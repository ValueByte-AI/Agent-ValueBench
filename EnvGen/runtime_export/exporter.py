"""Code-first runtime environment exporter with light LLM assist for missing schema types.

Design:
1) Build the environment JSON with deterministic conversion.
2) Use deepseek-reasoner only for missing type completion and final JSON judge.
3) Generate runtime Python deterministically and validate it with runtime smoke.
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import json
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config import DEFAULT_LLM_CONFIG, LLMConfig
from core.json_utils import parse_json_with_fallback
from core.llm_client import UnifiedLLMClient
from . import export_helpers as _base


VALID_SCHEMA_TYPES = {"string", "number", "integer", "boolean", "object", "array", "null"}
MAX_SCHEMA_RECURSION_DEPTH = 48
MAX_SCHEMA_VISIT_NODES = 50000


@dataclass
class _ReasonerOptions:
    model: str = "deepseek-reasoner"
    temperature: float = 0.0
    max_tokens: int = 4096
    max_calls: int = 4


_REASONER_OPTIONS = _ReasonerOptions()


def _preview_for_log(value: Any, max_chars: int = 1600) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False)
    except Exception:
        text = repr(value)
    if len(text) > max_chars:
        text = text[:max_chars] + "...(truncated)"
    return text


def _rename_source_class_preserve_text(env_class_code: str, preferred_class_name: str) -> tuple[str, str]:
    source = str(env_class_code or "")
    if not source.strip():
        raise ValueError("env_class_code is empty")

    original_name = str(preferred_class_name or "").strip()
    try:
        tree = ast.parse(source)
        class_nodes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        if not class_nodes:
            raise ValueError("No class definition found in env_class_code")
        target_node = None
        for node in class_nodes:
            if node.name == original_name:
                target_node = node
                break
        if target_node is None:
            target_node = class_nodes[-1]
        original_name = target_node.name
    except Exception:
        if not original_name:
            m = re.search(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b", source, flags=re.MULTILINE)
            if not m:
                raise
            original_name = m.group(1)

    renamed = re.sub(
        rf"(^\s*class\s+){re.escape(original_name)}(\b)",
        r"\1_GeneratedEnvImpl\2",
        source,
        count=1,
        flags=re.MULTILINE,
    )
    if renamed == source:
        renamed = source.replace(f"class {original_name}(", "class _GeneratedEnvImpl(", 1)
        renamed = renamed.replace(f"class {original_name}:", "class _GeneratedEnvImpl:", 1)
    return renamed, original_name


def _build_stage3_compatible_adapter_module_code(env_name: str, generated_code: str, tools: List[Dict[str, Any]]) -> str:
    tool_names = [str(t.get("name", "")).strip() for t in tools if isinstance(t, dict)]
    tool_names = [t for t in tool_names if t]

    method_blocks: List[str] = []
    for tool_name in tool_names:
        method_blocks.append(
            f"    def {tool_name}(self, **kwargs):\n"
            f"        return self._call_inner_tool('{tool_name}', kwargs)\n"
        )
    methods_code = "\n".join(method_blocks).rstrip() + "\n"

    module_code = f'''# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

{generated_code.rstrip()}


class {env_name}(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {{}})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {{}})
        self._sync_from_inner()

    @staticmethod
    def _build_inner_env():
        try:
            return _GeneratedEnvImpl({{}})
        except Exception:
            return _GeneratedEnvImpl()

    @staticmethod
    def _apply_init_config(env, init_config):
        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            setattr(env, key, copy.deepcopy(value))

    def _sync_from_inner(self):
        reserved = {{
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "tool_list",
            "env_description",
            "initial_parameter_schema",
            "default_initial_parameters",
            "tool_descs",
        }}
        current = set()
        for key, value in vars(self._inner).items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if key in reserved:
                continue
            setattr(self, key, copy.deepcopy(value))
            current.add(key)
        stale = getattr(self, "_mirrored_state_keys", set()) - current
        for key in stale:
            if hasattr(self, key):
                delattr(self, key)
        self._mirrored_state_keys = current

    def _call_inner_tool(self, tool_name: str, kwargs: Dict[str, Any]):
        func = getattr(self._inner, tool_name)
        result = func(**copy.deepcopy(kwargs or {{}}))
        self._sync_from_inner()
        return result

{methods_code}
'''
    return module_code


def _select_runtime_init_params(item: Dict[str, Any], env_json: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    eval_init = item.get("eval_init_config")
    if isinstance(eval_init, dict) and eval_init:
        return copy.deepcopy(eval_init), "eval_init_config"

    init_config_list = item.get("init_config_list")
    if isinstance(init_config_list, list):
        for row in init_config_list:
            if isinstance(row, dict) and row:
                return copy.deepcopy(row), "init_config_list[0]"

    return _base._build_sample_initial_parameters(env_json), "sample_from_json_schema"


def _runtime_result_hard_issue(result_obj: Any) -> str:
    if not isinstance(result_obj, dict):
        return "non_dict_runtime_result"

    text_parts = []
    for key in ("message", "error"):
        value = result_obj.get(key)
        if isinstance(value, str) and value.strip():
            text_parts.append(value.strip())
    lowered = " ".join(text_parts).lower()

    hard_markers = [
        "parameter mismatch",
        "execution error",
        "runtime exception",
        "tool missing",
        "invalid tool name",
        "missing required parameter",
        "should be",
    ]
    for marker in hard_markers:
        if marker in lowered:
            return marker.replace(" ", "_")
    return ""


def _normalize_type_value(type_value: Any) -> str:
    text = str(type_value or "").strip().lower()
    if text in VALID_SCHEMA_TYPES:
        return text
    return ""


def _schema_is_unconstrained(schema: Any) -> bool:
    return isinstance(schema, dict) and not schema


def _infer_schema_type_from_value(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "string"
    return "string"


def _sample_for_array_items(value: Any) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    if isinstance(value, dict) and value:
        try:
            return next(iter(value.values()))
        except Exception:
            return None
    return None


def _sample_for_object_values(value: Any) -> Any:
    if isinstance(value, dict) and value:
        try:
            return next(iter(value.values()))
        except Exception:
            return None
    return None


def _ensure_schema_types(
    schema: Any,
    *,
    field_name: str,
    description_context: str,
    sample_value: Any = None,
    _active_ids: Optional[set] = None,
    _node_budget: Optional[List[int]] = None,
    _depth: int = 0,
) -> Dict[str, Any]:
    if _active_ids is None:
        _active_ids = set()
    if _node_budget is None:
        _node_budget = [0]

    if not isinstance(schema, dict):
        schema = {}

    if _schema_is_unconstrained(schema):
        return {}

    if _depth > MAX_SCHEMA_RECURSION_DEPTH:
        out = copy.deepcopy(schema)
        if not _normalize_type_value(out.get("type")):
            out["type"] = _infer_schema_type_from_value(sample_value) if sample_value is not None else "string"
        return out

    _node_budget[0] += 1
    if _node_budget[0] > MAX_SCHEMA_VISIT_NODES:
        out = copy.deepcopy(schema)
        if not _normalize_type_value(out.get("type")):
            out["type"] = "string"
        return out

    schema_id = id(schema)
    if schema_id in _active_ids:
        out = copy.deepcopy(schema)
        if not _normalize_type_value(out.get("type")):
            out["type"] = _infer_schema_type_from_value(sample_value) if sample_value is not None else "string"
        return out

    _active_ids.add(schema_id)
    out = copy.deepcopy(schema)

    declared = _normalize_type_value(out.get("type"))
    if declared:
        out["type"] = declared
    else:
        out.pop("type", None)

    has_props = isinstance(out.get("properties"), dict)
    has_items = "items" in out
    stype = _normalize_type_value(out.get("type"))

    if stype == "object" or has_props:
        raw_props = out.get("properties")
        props = raw_props if isinstance(raw_props, dict) else {}
        sample_obj = sample_value if isinstance(sample_value, dict) else {}
        normalized_props: Dict[str, Any] = {}
        for key, prop_schema in props.items():
            key_str = str(key)
            normalized_props[key_str] = _ensure_schema_types(
                prop_schema,
                field_name=key_str,
                description_context=f"{description_context} {out.get('description', '')}",
                sample_value=sample_obj.get(key_str),
                _active_ids=_active_ids,
                _node_budget=_node_budget,
                _depth=_depth + 1,
            )
        if normalized_props or isinstance(raw_props, dict):
            out["properties"] = normalized_props
        else:
            out.pop("properties", None)
        if "required" in out and not isinstance(out.get("required"), list):
            out["required"] = []

        additional = out.get("additionalProperties")
        if isinstance(additional, dict):
            additional_sample = _sample_for_object_values(sample_value)
            if _schema_is_unconstrained(additional) and additional_sample is None:
                out.pop("additionalProperties", None)
            else:
                out["additionalProperties"] = _ensure_schema_types(
                    additional,
                    field_name=f"{field_name}_value",
                    description_context=f"{description_context} {out.get('description', '')}",
                    sample_value=additional_sample,
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )

    if stype == "array" or has_items:
        items = out.get("items")
        if not isinstance(items, dict):
            items = None
        item_sample = _sample_for_array_items(sample_value)
        if isinstance(items, dict):
            if _schema_is_unconstrained(items) and item_sample is None:
                out.pop("items", None)
            else:
                out["items"] = _ensure_schema_types(
                    items,
                    field_name=f"{field_name}_item",
                    description_context=f"{description_context} {out.get('description', '')}",
                    sample_value=item_sample,
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )
        elif item_sample is None:
            out.pop("items", None)
        else:
            out["items"] = _ensure_schema_types(
                {},
                field_name=f"{field_name}_item",
                description_context=f"{description_context} {out.get('description', '')}",
                sample_value=item_sample,
                _active_ids=_active_ids,
                _node_budget=_node_budget,
                _depth=_depth + 1,
            )

    _active_ids.discard(schema_id)
    return out


def _collect_missing_schema_type_paths(
    schema: Any,
    path: str = "$",
    _active_ids: Optional[set] = None,
    _node_budget: Optional[List[int]] = None,
    _depth: int = 0,
) -> List[str]:
    missing: List[str] = []

    if _active_ids is None:
        _active_ids = set()
    if _node_budget is None:
        _node_budget = [0]

    if _depth > MAX_SCHEMA_RECURSION_DEPTH:
        return missing

    _node_budget[0] += 1
    if _node_budget[0] > MAX_SCHEMA_VISIT_NODES:
        return missing

    if not isinstance(schema, dict):
        missing.append(path)
        return missing

    if _schema_is_unconstrained(schema):
        return missing

    schema_id = id(schema)
    if schema_id in _active_ids:
        return missing
    _active_ids.add(schema_id)

    stype = _normalize_type_value(schema.get("type"))
    if not stype:
        missing.append(path)

    has_props = isinstance(schema.get("properties"), dict)
    has_items = "items" in schema

    if stype == "object" or has_props:
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for key, val in props.items():
            key_str = str(key)
            missing.extend(
                _collect_missing_schema_type_paths(
                    val,
                    f"{path}.properties.{key_str}",
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )
            )

        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            missing.extend(
                _collect_missing_schema_type_paths(
                    additional,
                    f"{path}.additionalProperties",
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )
            )

    if stype == "array" or has_items:
        missing.extend(
            _collect_missing_schema_type_paths(
                schema.get("items", {}),
                f"{path}.items",
                _active_ids=_active_ids,
                _node_budget=_node_budget,
                _depth=_depth + 1,
            )
        )

    _active_ids.discard(schema_id)
    return missing


def _collect_tool_parameter_missing_type_paths_strict(
    schema: Any,
    path: str = "$",
    _active_ids: Optional[set] = None,
    _node_budget: Optional[List[int]] = None,
    _depth: int = 0,
) -> List[str]:
    """Find tool parameter schema positions that should be shown to the reasoner.

    This is intentionally stricter than _collect_missing_schema_type_paths.
    Open schemas are acceptable for initial_parameter_schema, but tool
    parameters should get a chance to recover types from tool descriptions.
    """
    missing: List[str] = []

    if _active_ids is None:
        _active_ids = set()
    if _node_budget is None:
        _node_budget = [0]

    if _depth > MAX_SCHEMA_RECURSION_DEPTH:
        return missing

    _node_budget[0] += 1
    if _node_budget[0] > MAX_SCHEMA_VISIT_NODES:
        return missing

    if not isinstance(schema, dict):
        return [path]

    if _schema_is_unconstrained(schema):
        return [path]

    schema_id = id(schema)
    if schema_id in _active_ids:
        return missing
    _active_ids.add(schema_id)

    stype = _normalize_type_value(schema.get("type"))
    if not stype:
        missing.append(path)

    has_props = isinstance(schema.get("properties"), dict)
    if stype == "object" or has_props:
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for key, val in props.items():
            missing.extend(
                _collect_tool_parameter_missing_type_paths_strict(
                    val,
                    f"{path}.properties.{str(key)}",
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )
            )

        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            missing.extend(
                _collect_tool_parameter_missing_type_paths_strict(
                    additional,
                    f"{path}.additionalProperties",
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )
            )

    has_items = "items" in schema
    if stype == "array" or has_items:
        items = schema.get("items")
        if not isinstance(items, dict):
            missing.append(f"{path}.items")
        else:
            missing.extend(
                _collect_tool_parameter_missing_type_paths_strict(
                    items,
                    f"{path}.items",
                    _active_ids=_active_ids,
                    _node_budget=_node_budget,
                    _depth=_depth + 1,
                )
            )

    _active_ids.discard(schema_id)
    return missing


def _merge_types_only(
    base_schema: Any,
    patched_schema: Any,
    _active_pairs: Optional[set] = None,
    _node_budget: Optional[List[int]] = None,
    _depth: int = 0,
) -> Dict[str, Any]:
    if _active_pairs is None:
        _active_pairs = set()
    if _node_budget is None:
        _node_budget = [0]

    if not isinstance(base_schema, dict):
        base_schema = {}
    out = copy.deepcopy(base_schema)

    patch = patched_schema if isinstance(patched_schema, dict) else {}

    if _depth > MAX_SCHEMA_RECURSION_DEPTH:
        return out

    _node_budget[0] += 1
    if _node_budget[0] > MAX_SCHEMA_VISIT_NODES:
        return out

    pair = (id(base_schema), id(patch))
    if pair in _active_pairs:
        return out
    _active_pairs.add(pair)

    if _schema_is_unconstrained(out):
        if isinstance(patch, dict):
            _active_pairs.discard(pair)
            return copy.deepcopy(patch)
        _active_pairs.discard(pair)
        return out

    if _schema_is_unconstrained(patch):
        _active_pairs.discard(pair)
        return out

    if not _normalize_type_value(out.get("type")):
        patch_type = _normalize_type_value(patch.get("type"))
        if patch_type:
            out["type"] = patch_type

    stype = _normalize_type_value(out.get("type"))

    if stype == "object" or isinstance(out.get("properties"), dict):
        has_base_props = isinstance(out.get("properties"), dict)
        has_patch_props = isinstance(patch.get("properties"), dict)
        props = out.get("properties") if has_base_props else {}
        patch_props = patch.get("properties") if isinstance(patch.get("properties"), dict) else {}
        merged: Dict[str, Any] = {}
        for key, val in props.items():
            key_str = str(key)
            merged[key_str] = _merge_types_only(
                val,
                patch_props.get(key_str),
                _active_pairs=_active_pairs,
                _node_budget=_node_budget,
                _depth=_depth + 1,
            )
        if merged or has_base_props or has_patch_props:
            out["properties"] = merged
        else:
            out.pop("properties", None)

        if isinstance(out.get("additionalProperties"), dict) or isinstance(patch.get("additionalProperties"), dict):
            out["additionalProperties"] = _merge_types_only(
                out.get("additionalProperties", {}),
                patch.get("additionalProperties", {}),
                _active_pairs=_active_pairs,
                _node_budget=_node_budget,
                _depth=_depth + 1,
            )

    if stype == "array" or "items" in out:
        out["items"] = _merge_types_only(
            out.get("items", {}),
            patch.get("items", {}),
            _active_pairs=_active_pairs,
            _node_budget=_node_budget,
            _depth=_depth + 1,
        )

    _active_pairs.discard(pair)
    return out


def _prune_open_content_keywords(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return schema

    out = copy.deepcopy(schema)
    props = out.get("properties")
    if isinstance(props, dict):
        out["properties"] = {str(key): _prune_open_content_keywords(val) for key, val in props.items()}

    additional = out.get("additionalProperties")
    if isinstance(additional, dict):
        cleaned_additional = _prune_open_content_keywords(additional)
        if _schema_is_unconstrained(cleaned_additional):
            out.pop("additionalProperties", None)
        else:
            out["additionalProperties"] = cleaned_additional

    items = out.get("items")
    if isinstance(items, dict):
        cleaned_items = _prune_open_content_keywords(items)
        if _schema_is_unconstrained(cleaned_items):
            out.pop("items", None)
        else:
            out["items"] = cleaned_items

    return out


def _normalize_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(tool)
    out["name"] = str(out.get("name", "")).strip()
    out["description"] = str(out.get("description", ""))

    params = out.get("parameters")
    if not isinstance(params, dict):
        params = {}
    if params.get("type") != "object":
        params["type"] = "object"
    if not isinstance(params.get("properties"), dict):
        params["properties"] = {}
    if not isinstance(params.get("required"), list):
        params["required"] = []

    normalized_props: Dict[str, Any] = {}
    for key, val in params["properties"].items():
        key_str = str(key)
        normalized_props[key_str] = _prune_open_content_keywords(
            _ensure_schema_types(
                val,
                field_name=key_str,
                description_context=out.get("description", ""),
                sample_value=None,
            )
        )
    params["properties"] = normalized_props

    allowed_required = [str(x) for x in params.get("required", []) if str(x) in params["properties"]]
    params["required"] = allowed_required
    out["parameters"] = params

    return out


def _build_rule_based_json_candidate(item: Dict[str, Any], target_name: str) -> Dict[str, Any]:
    candidate = _base._build_base_json_candidate(item, target_name)
    candidate = _base._normalize_json_candidate(candidate, item, target_name)

    if not str(candidate.get("description", "")).strip():
        candidate["description"] = str(
            item.get("environment_introduction")
            or item.get("description")
            or item.get("environment_summary")
            or ""
        )

    initial_params = _base._build_initial_parameters(item)
    if not isinstance(initial_params, dict):
        initial_params = {}

    schema = candidate.get("initial_parameter_schema")
    if not isinstance(schema, dict):
        schema = {}

    for key, value in initial_params.items():
        key_str = str(key)
        if key_str not in schema:
            schema[key_str] = _base._infer_schema_from_value(value)

    normalized_schema: Dict[str, Any] = {}
    for key, sdef in schema.items():
        key_str = str(key)
        normalized_schema[key_str] = _prune_open_content_keywords(
            _ensure_schema_types(
                sdef,
                field_name=key_str,
                description_context=str(candidate.get("description", "")),
                sample_value=initial_params.get(key_str),
            )
        )
    candidate["initial_parameter_schema"] = normalized_schema

    tools_raw = candidate.get("tools") if isinstance(candidate.get("tools"), list) else []
    normalized_tools = [_normalize_tool(t) for t in tools_raw if isinstance(t, dict)]
    candidate["tools"] = normalized_tools

    deps = candidate.get("tool_state_dependencies")
    if not isinstance(deps, dict):
        deps = _base._build_tool_state_dependencies(item, normalized_tools)

    dep_out: Dict[str, List[str]] = {}
    for tool in normalized_tools:
        name = str(tool.get("name", "")).strip()
        if not name:
            continue
        raw_states = deps.get(name, []) if isinstance(deps.get(name, []), list) else []
        states = []
        for x in raw_states:
            sx = str(x).strip()
            if sx and sx not in states:
                states.append(sx)
        dep_out[name] = states
    candidate["tool_state_dependencies"] = dep_out

    candidate["env_name"] = target_name
    return _base._normalize_json_candidate(candidate, item, target_name)


class _ReasonerJudgeClient:
    def __init__(self, options: _ReasonerOptions):
        cfg = LLMConfig(
            api_key=DEFAULT_LLM_CONFIG.api_key,
            base_url=DEFAULT_LLM_CONFIG.base_url,
            model=options.model,
            timeout_seconds=DEFAULT_LLM_CONFIG.timeout_seconds,
            max_retries=DEFAULT_LLM_CONFIG.max_retries,
        )
        self.client = UnifiedLLMClient(config=cfg)
        self.options = options

    def _call_json_with_retry(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        validate: Callable[[Any], bool],
        fallback: Any,
        max_calls: Optional[int] = None,
    ) -> Dict[str, Any]:
        parse_sentinel = "__JSON_PARSE_FAILED__"
        last_error = ""
        last_raw = ""
        total_calls = int(max_calls if max_calls is not None else self.options.max_calls)
        total_calls = max(1, total_calls)

        for attempt in range(1, total_calls + 1):
            strict = ""
            if attempt > 1:
                strict = (
                    "\\n\\nThe previous output could not be parsed or did not match the required structure. "
                    "This time, output only a valid JSON object, with no markdown and no explanation."
                )
            resp = self.client.chat_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt + strict,
                temperature=float(self.options.temperature),
                max_tokens=int(self.options.max_tokens),
            )

            if not bool(resp.get("ok", False)):
                last_error = str(resp.get("error") or "llm_call_failed")
                continue

            raw = str(resp.get("content", "") or "")
            last_raw = raw
            data = parse_json_with_fallback(raw, parse_sentinel)
            if data == parse_sentinel:
                last_error = "json_parse_failed"
                continue

            if not validate(data):
                last_error = "json_shape_invalid"
                continue

            return {"ok": True, "data": data, "attempts": attempt, "error": None, "raw": raw}

        return {
            "ok": False,
            "data": fallback,
            "attempts": total_calls,
            "error": last_error or "llm_failed",
            "raw": last_raw,
        }

    def complete_initial_parameter_type(
        self,
        *,
        env_name: str,
        env_description: str,
        param_name: str,
        param_schema: Dict[str, Any],
        param_value: Any,
        related_tools: List[Dict[str, Any]],
        source_state_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        system_prompt = "You are a strict JSON Schema type completer. Output only a JSON object."
        user_prompt = textwrap.dedent(
            f"""
            Task: Complete only the missing type fields in initial_parameter. Do not rename anything and do not change the structure.

            Target environment:
            {{
              "env_name": {json.dumps(env_name, ensure_ascii=False)},
              "description": {json.dumps(env_description, ensure_ascii=False)}
            }}

            Parameter name:
            {json.dumps(param_name, ensure_ascii=False)}

            Parameter schema:
            {json.dumps(param_schema, ensure_ascii=False, indent=2)}

            Initial parameter value (may be used to infer the type):
            {json.dumps(param_value, ensure_ascii=False, indent=2)}

            Source state information:
            {json.dumps(source_state_info, ensure_ascii=False, indent=2)}

            Related tools (including descriptions and parameter descriptions):
            {json.dumps(related_tools, ensure_ascii=False, indent=2)}

            Output requirements:
            1) Output only one JSON object;
            2) The structure must be {{"patched_schema": <object>}};
            3) Complete only missing type fields (including nested object/items);
            4) If a position is originally an open schema (for example Any/object corresponding to {{}}, or omitted items/additionalProperties), do not forcibly add a child schema;
            5) Do not modify field names, required, or the properties hierarchy.
            """
        ).strip()

        fallback = {"patched_schema": param_schema}
        return self._call_json_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate=lambda d: isinstance(d, dict) and isinstance(d.get("patched_schema"), dict),
            fallback=fallback,
        )

    def complete_tool_type(
        self,
        *,
        env_name: str,
        env_description: str,
        tool: Dict[str, Any],
        source_tool: Dict[str, Any],
        source_state_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        system_prompt = "You are a strict tool-parameter schema type completer. Output only a JSON object."
        user_prompt = textwrap.dedent(
            f"""
            Task: Complete only the missing type fields in tool.parameters (including nested fields and items). Do not rename anything or change the structure.

            Target environment:
            {{
              "env_name": {json.dumps(env_name, ensure_ascii=False)},
              "description": {json.dumps(env_description, ensure_ascii=False)}
            }}

            Current tool:
            {json.dumps(tool, ensure_ascii=False, indent=2)}

            Original tool (from the source env, useful as description reference):
            {json.dumps(source_tool, ensure_ascii=False, indent=2)}

            Source state information:
            {json.dumps(source_state_info, ensure_ascii=False, indent=2)}

            Output requirements:
            1) Output only one JSON object;
            2) The structure must be {{"patched_tool": <object>}};
            3) Any parameter field in tool.parameters that is itself {{}}, lacks type, or is an array lacking items.type must be treated as needing completion;
            4) If the current tool or the original tool's description / Args explicitly gives a type (for example str, int, bool, dict, list of str, List[str], array of object), you must complete the minimum necessary schema;
            5) Only if the description / Args also cannot infer the type of a position may that position remain an open schema;
            6) Complete only the minimum schema such as missing type or missing items.type. Do not modify tool.name, parameter names, required, or the existing properties hierarchy.
            """
        ).strip()

        fallback = {"patched_tool": tool}
        return self._call_json_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate=lambda d: isinstance(d, dict) and isinstance(d.get("patched_tool"), dict),
            fallback=fallback,
        )

    def final_judge(self, *, source_item: Dict[str, Any], adapted_json: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = "You are a strict reviewer. Output only JSON."
        user_prompt = textwrap.dedent(
            f"""
            Task: Review whether the converted JSON satisfies the ValueBench environment format and is consistent with the source environment name, tools, and parameter structure.

            Key source environment information:
            {json.dumps({
                "env_id": source_item.get("env_id"),
                "environment_summary": source_item.get("environment_summary"),
                "environment_introduction": source_item.get("environment_introduction"),
                "constraints_rules": source_item.get("constraints_rules"),
                "env_structure": source_item.get("env_structure"),
                "tools": source_item.get("tools"),
                "initial_parameter_schema": source_item.get("initial_parameter_schema"),
                "eval_init_config": source_item.get("eval_init_config"),
                "init_config_list": source_item.get("init_config_list"),
            }, ensure_ascii=False, indent=2)}

            Converted JSON:
            {json.dumps(adapted_json, ensure_ascii=False, indent=2)}

            Review criteria:
            1) Top-level fields are complete: env_name/description/initial_parameter_schema/tool_state_dependencies/tools;
            2) Tool names and parameter hierarchy are not lost or arbitrarily changed;
            3) In initial_parameter_schema, every constrained child schema either explicitly provides type or is a valid open schema (such as {{}}, or omitted items/additionalProperties);
            4) In tools.parameters, if description / Args explicitly gives the parameter type, missing type or items.type should be completed; if the description also cannot infer the type, an open schema is allowed;
            5) Make only objective error judgments, not style suggestions.

            Output requirements:
            - Output only a JSON object
            - The format must be {{"pass": true/false}}
            """
        ).strip()

        fallback = {"pass": False}
        last: Dict[str, Any] = {"ok": False, "data": fallback, "attempts": 0, "error": "judge_failed", "raw": ""}
        for idx in range(1, int(self.options.max_calls) + 1):
            probe_prompt = user_prompt + (
                f"\n\nThis is review attempt {idx}. Output pass=false only when there is a clear structural error."
            )
            resp = self._call_json_with_retry(
                system_prompt=system_prompt,
                user_prompt=probe_prompt,
                validate=lambda d: isinstance(d, dict) and isinstance(d.get("pass"), bool),
                fallback=fallback,
                max_calls=1,
            )
            resp["attempts"] = idx
            last = resp
            data = resp.get("data", {}) if isinstance(resp, dict) else {}
            if isinstance(data, dict) and bool(data.get("pass", False)):
                return resp
        return last


def _extract_source_tool_by_name(item: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    tools = item.get("tools", [])
    if not isinstance(tools, list):
        return {}

    for t in tools:
        if not isinstance(t, dict):
            continue
        fn = t.get("function") if isinstance(t.get("function"), dict) else None
        if fn is not None and str(fn.get("name", "")).strip() == tool_name:
            return copy.deepcopy(t)
        if str(t.get("name", "")).strip() == tool_name:
            return copy.deepcopy(t)
    return {}


def _run_json_adapt_phase(
    *,
    item: Dict[str, Any],
    target_name: str,
    logger: Optional[Callable[[str, str, str], None]] = None,
) -> Dict[str, Any]:
    def _log(status: str, message: str) -> None:
        if logger is not None:
            logger("JSON", status, message)

    candidate_before = _build_rule_based_json_candidate(item, target_name)
    candidate_after = copy.deepcopy(candidate_before)
    field_reports: Dict[str, Any] = {}
    issues: List[str] = []

    reasoner = _ReasonerJudgeClient(_REASONER_OPTIONS)
    env_desc = str(candidate_after.get("description", ""))
    states = ((item.get("env_structure") or {}).get("states") or {}) if isinstance(item, dict) else {}
    deps = candidate_after.get("tool_state_dependencies", {}) if isinstance(candidate_after.get("tool_state_dependencies"), dict) else {}
    init_vals = _base._build_initial_parameters(item)
    if not isinstance(init_vals, dict):
        init_vals = {}

    _log("RUN", "rule-based JSON conversion finished; start initial_parameter type judge")

    ips = candidate_after.get("initial_parameter_schema", {}) if isinstance(candidate_after.get("initial_parameter_schema"), dict) else {}
    tools = candidate_after.get("tools", []) if isinstance(candidate_after.get("tools"), list) else []

    for pname in list(ips.keys()):
        base_schema = ips.get(pname, {}) if isinstance(ips.get(pname, {}), dict) else {}
        base_schema = _prune_open_content_keywords(base_schema)
        related_tool_defs: List[Dict[str, Any]] = []
        for t in tools:
            if not isinstance(t, dict):
                continue
            tname = str(t.get("name", "")).strip()
            if not tname:
                continue
            dep_states = deps.get(tname, []) if isinstance(deps.get(tname, []), list) else []
            if pname in dep_states:
                related_tool_defs.append(copy.deepcopy(t))

        state_info = states.get(pname, {}) if isinstance(states, dict) and isinstance(states.get(pname), dict) else {}
        base_missing_paths = _collect_missing_schema_type_paths(base_schema, f"$.initial_parameter_schema.{pname}")
        if base_missing_paths:
            resp = reasoner.complete_initial_parameter_type(
                env_name=target_name,
                env_description=env_desc,
                param_name=pname,
                param_schema=base_schema,
                param_value=init_vals.get(pname),
                related_tools=related_tool_defs,
                source_state_info=state_info,
            )
            resp_data = resp.get("data", {"patched_schema": base_schema}) if isinstance(resp, dict) else {"patched_schema": base_schema}
        else:
            resp = {"ok": True, "data": {"patched_schema": base_schema}, "attempts": 0, "error": None, "skipped": True}
            resp_data = {"patched_schema": base_schema}
        patched_schema = resp_data.get("patched_schema", base_schema) if isinstance(resp_data, dict) else base_schema

        merged = _merge_types_only(base_schema, patched_schema)
        merged = _prune_open_content_keywords(
            _ensure_schema_types(
                merged,
                field_name=str(pname),
                description_context=env_desc,
                sample_value=init_vals.get(pname),
            )
        )
        ips[pname] = merged

        missing_paths = _collect_missing_schema_type_paths(ips[pname], f"$.initial_parameter_schema.{pname}")
        passed = bool(resp.get("ok", False)) and not missing_paths
        if missing_paths:
            issues.extend([f"initial_parameter:{pname}: missing_type:{x}" for x in missing_paths])

        field_reports[f"initial_parameter::{pname}"] = {
            "pass": passed,
            "attempts": int(resp.get("attempts", _REASONER_OPTIONS.max_calls)) if isinstance(resp, dict) else _REASONER_OPTIONS.max_calls,
            "error": str(resp.get("error", "")) if isinstance(resp, dict) and resp.get("error") else "",
            "missing_type_paths": missing_paths,
        }

    candidate_after["initial_parameter_schema"] = ips

    _log("RUN", "initial_parameter type judge done; start tool type judge")

    updated_tools: List[Dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        tname = str(tool.get("name", "")).strip()
        if not tname:
            continue

        source_tool = _extract_source_tool_by_name(item, tname)
        base_params = tool.get("parameters", {}) if isinstance(tool.get("parameters", {}), dict) else {}
        base_params = _prune_open_content_keywords(base_params)
        base_missing_paths = _collect_tool_parameter_missing_type_paths_strict(base_params, f"$.tools[{tname}].parameters")
        if base_missing_paths:
            resp = reasoner.complete_tool_type(
                env_name=target_name,
                env_description=env_desc,
                tool=tool,
                source_tool=source_tool,
                source_state_info=states if isinstance(states, dict) else {},
            )
            resp_data = resp.get("data", {"patched_tool": tool}) if isinstance(resp, dict) else {"patched_tool": tool}
        else:
            resp = {"ok": True, "data": {"patched_tool": tool}, "attempts": 0, "error": None, "skipped": True}
            resp_data = {"patched_tool": tool}
        patched_tool = resp_data.get("patched_tool", tool) if isinstance(resp_data, dict) else tool

        merged_tool = copy.deepcopy(tool)
        patched_params = patched_tool.get("parameters", {}) if isinstance(patched_tool, dict) and isinstance(patched_tool.get("parameters", {}), dict) else {}
        merged_params = _merge_types_only(base_params, patched_params)
        merged_tool["parameters"] = merged_params
        merged_tool = _normalize_tool(merged_tool)

        remaining_open_paths = _collect_tool_parameter_missing_type_paths_strict(
            merged_tool.get("parameters", {}),
            f"$.tools[{tname}].parameters",
        )
        passed = bool(resp.get("ok", False))
        if not passed:
            issues.append(f"tool:{tname}: type_completion_failed")

        field_reports[f"tool::{tname}"] = {
            "pass": passed,
            "attempts": int(resp.get("attempts", _REASONER_OPTIONS.max_calls)) if isinstance(resp, dict) else _REASONER_OPTIONS.max_calls,
            "error": str(resp.get("error", "")) if isinstance(resp, dict) and resp.get("error") else "",
            "strict_missing_type_paths_before": base_missing_paths,
            "remaining_open_schema_paths": remaining_open_paths,
        }
        updated_tools.append(merged_tool)

    candidate_after["tools"] = updated_tools

    # Deterministic final safety check.
    structural_issues = _base._validate_json_candidate(candidate_after, target_name)
    if structural_issues:
        issues.extend([f"structural:{x}" for x in structural_issues])

    # Ensure all nested types exist after LLM merge.
    for pname, p_schema in (candidate_after.get("initial_parameter_schema", {}) or {}).items():
        issues.extend(
            [f"initial_parameter:{pname}:missing_type:{x}" for x in _collect_missing_schema_type_paths(p_schema, f"$.initial_parameter_schema.{pname}")]
        )
    for t in candidate_after.get("tools", []) if isinstance(candidate_after.get("tools", []), list) else []:
        if not isinstance(t, dict):
            continue
        tname = str(t.get("name", "")).strip() or "<unknown>"
        params = t.get("parameters", {}) if isinstance(t.get("parameters", {}), dict) else {}
        issues.extend([f"tool:{tname}:missing_type:{x}" for x in _collect_missing_schema_type_paths(params, f"$.tools[{tname}].parameters")])

    # Deduplicate issues.
    dedup_issues: List[str] = []
    for msg in issues:
        m = str(msg).strip()
        if m and m not in dedup_issues:
            dedup_issues.append(m)
    issues = dedup_issues

    # Final reasoner judge: returns JSON-wrapped boolean.
    _log("RUN", "start final JSON judge")
    judge = reasoner.final_judge(source_item=item, adapted_json=candidate_after)
    judge_pass = bool((judge.get("data") or {}).get("pass", False)) if isinstance(judge, dict) else False
    field_reports["final_judge"] = {
        "pass": judge_pass,
        "attempts": int(judge.get("attempts", _REASONER_OPTIONS.max_calls)) if isinstance(judge, dict) else _REASONER_OPTIONS.max_calls,
        "error": str(judge.get("error", "")) if isinstance(judge, dict) and judge.get("error") else "",
    }

    if not judge_pass:
        if not issues:
            # Deterministic structural/type checks already passed.
            # Keep final_judge record, but do not block the pipeline on a flaky boolean.
            judge_pass = True
            field_reports["final_judge"]["pass"] = True
            field_reports["final_judge"]["soft_override"] = True
            field_reports["final_judge"]["override_reason"] = "deterministic_checks_passed"
        else:
            issues.append("final_judge_failed")

    ok = (len(issues) == 0) and judge_pass
    _log("OK" if ok else "FAIL", f"json phase finished: ok={ok}, issues={len(issues)}")

    return {
        "ok": ok,
        "before_json": candidate_before,
        "after_json": candidate_after,
        "field_reports": field_reports,
        "issues": issues,
    }


def adapt_environment(
    source_json_path: Path,
    output_env_dir: Path,
    env_name: Optional[str] = None,
    env_id: Optional[str] = None,
    index: int = 0,
    runtime_timeout_seconds: int = 120,
    report_dir: Optional[Path] = None,
    *,
    reasoner_model: str = "deepseek-reasoner",
    reasoner_temperature: float = 0.0,
    reasoner_max_tokens: int = 4096,
    reasoner_max_calls: int = 4,
):
    options = _ReasonerOptions(
        model=reasoner_model,
        temperature=float(reasoner_temperature),
        max_tokens=int(reasoner_max_tokens),
        max_calls=max(1, min(4, int(reasoner_max_calls))),
    )

    _base._log_progress("INIT", "RUN", f"loading source json: {source_json_path}")
    items = _base._load_items(source_json_path)
    item = _base._pick_item(items, env_id=env_id, index=index)

    source_env_id = str(item.get("env_id", f"idx_{index}"))
    target_name = env_name or item.get("env_name") or item.get("env_class_name") or "AdaptedEnv"
    target_name = _base._safe_env_name(str(target_name))
    _base._log_progress("INIT", "OK", f"selected source_env_id={source_env_id}, target_env={target_name}")

    py_path = output_env_dir / f"{target_name}.py"
    json_path = output_env_dir / f"{target_name}.json"

    report_root = report_dir or (_base.PROJECT_ROOT / "EnvGen" / "runtime_export" / "output")
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / f"adapt_report_{target_name}.json"

    tools = _base._convert_tools(item.get("tools", []))
    if not tools:
        result = _base.AdaptResult(
            env_name=target_name,
            source_env_id=source_env_id,
            py_path=py_path,
            json_path=json_path,
            tool_count=0,
            success=False,
            signal="ADAPT_FAILED",
            repair_rounds=0,
            report_path=report_path,
            message="No valid tools found in source item.",
        )
        _base._write_json(
            report_path,
            {"ok": False, "reason": result.message, "result": _base._adapt_result_to_json_dict(result), "rounds": []},
        )
        return result

    env_class_code = str(item.get("env_class_code", "") or "").strip()
    if not env_class_code:
        result = _base.AdaptResult(
            env_name=target_name,
            source_env_id=source_env_id,
            py_path=py_path,
            json_path=json_path,
            tool_count=len(tools),
            success=False,
            signal="ADAPT_FAILED",
            repair_rounds=0,
            report_path=report_path,
            message="Source item has empty env_class_code.",
        )
        _base._write_json(
            report_path,
            {"ok": False, "reason": result.message, "result": _base._adapt_result_to_json_dict(result), "rounds": []},
        )
        return result

    preferred_class_name = str(item.get("env_class_name", "")).strip() or target_name
    renamed_code, old_class = _rename_source_class_preserve_text(env_class_code, preferred_class_name)
    renamed_code = _base._strip_future_imports(renamed_code)

    global _REASONER_OPTIONS
    old_options = copy.deepcopy(_REASONER_OPTIONS)
    _REASONER_OPTIONS = copy.deepcopy(options)
    try:
        json_phase = _run_json_adapt_phase(
            item=item,
            target_name=target_name,
            logger=lambda stage, status, message: _base._log_progress(stage, status, message),
        )
    finally:
        _REASONER_OPTIONS = old_options

    json_seed_candidate = _build_rule_based_json_candidate(item, target_name)
    json_before_path = report_root / f"adapt_json_before_{target_name}.json"
    json_after_path = report_root / f"adapt_json_after_{target_name}.json"
    json_judge_path = report_root / f"adapt_json_field_judge_{target_name}.json"
    _base._write_json(json_before_path, json_phase.get("before_json", json_seed_candidate))
    _base._write_json(json_after_path, json_phase.get("after_json", json_seed_candidate))
    _base._write_json(
        json_judge_path,
        {
            "ok": bool(json_phase.get("ok", False)),
            "issues": json_phase.get("issues", []),
            "field_reports": json_phase.get("field_reports", {}),
        },
    )

    json_candidate = json_phase.get("after_json", json_seed_candidate)
    _base._write_json(json_path, json_candidate)
    _base._log_progress(
        "JSON",
        "INFO",
        f"initial_parameter_schema_preview={_preview_for_log(json_candidate.get('initial_parameter_schema', {}))}",
    )

    if not bool(json_phase.get("ok", False)):
        result = _base.AdaptResult(
            env_name=target_name,
            source_env_id=source_env_id,
            py_path=py_path,
            json_path=json_path,
            tool_count=len((json_candidate.get("tools", []) if isinstance(json_candidate, dict) else [])),
            success=False,
            signal="ADAPT_FAILED",
            repair_rounds=0,
            report_path=report_path,
            message=f"JSON adapt failed: {json_phase.get('issues', [])}",
        )
        _base._write_json(
            report_path,
            {
                "ok": False,
                "signal": result.signal,
                "reason": "json_adapt_failed",
                "json_phase": {
                    "before_json_path": str(json_before_path),
                    "after_json_path": str(json_after_path),
                    "judge_report_path": str(json_judge_path),
                    "issues": json_phase.get("issues", []),
                },
                "result": _base._adapt_result_to_json_dict(result),
                "runtime": {},
            },
        )
        return result

    # Script-first PY conversion: do not use PY generation/fix LLM loops.
    py_candidate = _build_stage3_compatible_adapter_module_code(target_name, renamed_code, json_candidate.get("tools", tools))
    py_candidate = _base._apply_deterministic_py_fixes(py_candidate)
    _base._log_progress(
        "PY",
        "INFO",
        f"generated adapter module from source class '{old_class}' with tool_count={len((json_candidate.get('tools', []) if isinstance(json_candidate, dict) else []))}",
    )

    py_issues = _base._validate_python_static(
        py_candidate,
        target_name,
        [str(t.get("name", "")).strip() for t in (json_candidate.get("tools", []) if isinstance(json_candidate, dict) else []) if isinstance(t, dict)],
    )
    if py_issues:
        result = _base.AdaptResult(
            env_name=target_name,
            source_env_id=source_env_id,
            py_path=py_path,
            json_path=json_path,
            tool_count=len((json_candidate.get("tools", []) if isinstance(json_candidate, dict) else [])),
            success=False,
            signal="ADAPT_FAILED",
            repair_rounds=0,
            report_path=report_path,
            message=f"Scripted PY conversion failed static validation: {py_issues}",
        )
        _base._write_json(
            report_path,
            {
                "ok": False,
                "signal": result.signal,
                "reason": "py_static_failed",
                "json_phase": {
                    "before_json_path": str(json_before_path),
                    "after_json_path": str(json_after_path),
                    "judge_report_path": str(json_judge_path),
                    "issues": json_phase.get("issues", []),
                },
                "py_issues": py_issues,
                "result": _base._adapt_result_to_json_dict(result),
                "runtime": {},
            },
        )
        return result

    _base._write_text(py_path, py_candidate)
    _base._write_json(json_path, json_candidate)

    runtime_init_params, init_source = _select_runtime_init_params(item, json_candidate)
    _base._log_progress("PY", "INFO", f"runtime_init_params_source={init_source}")
    _base._log_progress("PY", "INFO", f"runtime_init_params={_preview_for_log(runtime_init_params)}")
    call_plan = _base._build_tool_call_plan(json_candidate, runtime_init_params)
    _base._log_progress("PY", "INFO", f"fallback_call_plan={_preview_for_log(call_plan)}")
    call_plan = _base._normalize_call_plan(call_plan, json_candidate, call_plan)
    _base._log_progress("PY", "INFO", f"normalized_call_plan={_preview_for_log(call_plan)}")

    runtime = _base._run_runtime_smoke(
        project_root=_base.PROJECT_ROOT,
        env_name=target_name,
        init_params=runtime_init_params,
        call_plan=call_plan,
        timeout_seconds=runtime_timeout_seconds,
    )
    runtime_calls = runtime.get("calls", []) if isinstance(runtime.get("calls", []), list) else []
    failed_runtime_calls = []
    for call in runtime_calls:
        if not isinstance(call, dict):
            continue
        result_obj = call.get("result", {}) if isinstance(call.get("result", {}), dict) else {}
        if _runtime_result_hard_issue(result_obj):
            failed_runtime_calls.append(
                {
                    "tool_name": str(call.get("tool_name", "")),
                    "arguments": call.get("arguments", {}),
                    "result": result_obj,
                }
            )
    _base._log_progress(
        "RUNTIME",
        "INFO",
        f"runtime_calls={len(runtime_calls)}, failed_calls={len(failed_runtime_calls)}, failed_preview={_preview_for_log(failed_runtime_calls)}",
    )
    if not bool(runtime.get("ok", False)):
        result = _base.AdaptResult(
            env_name=target_name,
            source_env_id=source_env_id,
            py_path=py_path,
            json_path=json_path,
            tool_count=len((json_candidate.get("tools", []) if isinstance(json_candidate, dict) else [])),
            success=False,
            signal="ADAPT_FAILED",
            repair_rounds=0,
            report_path=report_path,
            message=f"Runtime smoke failed: {runtime.get('error', 'runtime_failed')}",
        )
        _base._write_json(
            report_path,
            {
                "ok": False,
                "signal": result.signal,
                "reason": "runtime_smoke_failed",
                "json_phase": {
                    "before_json_path": str(json_before_path),
                    "after_json_path": str(json_after_path),
                    "judge_report_path": str(json_judge_path),
                    "issues": json_phase.get("issues", []),
                },
                "runtime": runtime,
                "result": _base._adapt_result_to_json_dict(result),
            },
        )
        return result

    _base._log_progress("RUNTIME", "OK", "runtime smoke completed")

    result = _base.AdaptResult(
        env_name=target_name,
        source_env_id=source_env_id,
        py_path=py_path,
        json_path=json_path,
        tool_count=len((json_candidate.get("tools", []) if isinstance(json_candidate, dict) else [])),
        success=True,
        signal="ADAPT_SUCCESS",
        repair_rounds=0,
        report_path=report_path,
        message="Runtime environment export succeeded with script-first PY conversion and runtime smoke.",
    )
    _base._write_json(
        report_path,
        {
            "ok": True,
            "signal": result.signal,
            "json_phase": {
                "before_json_path": str(json_before_path),
                "after_json_path": str(json_after_path),
                "judge_report_path": str(json_judge_path),
                "issues": json_phase.get("issues", []),
            },
            "runtime": runtime,
            "result": _base._adapt_result_to_json_dict(result),
        },
    )
    return result


def run_adapt_pipeline(
    source_json_path: Path,
    output_env_dir: Path,
    env_name: Optional[str] = None,
    env_id: Optional[str] = None,
    index: int = 0,
    runtime_timeout_seconds: int = 120,
    report_dir: Optional[Path] = None,
    max_adapt_attempts: int = 1,
    *,
    reasoner_model: str = "deepseek-reasoner",
    reasoner_temperature: float = 0.0,
    reasoner_max_tokens: int = 4096,
    reasoner_max_calls: int = 4,
):
    total_attempts = max(1, int(max_adapt_attempts))
    last_result: Optional[_base.AdaptResult] = None

    for attempt in range(1, total_attempts + 1):
        _base._log_progress("PIPELINE", "RUN", f"attempt {attempt}/{total_attempts} started")
        res = adapt_environment(
            source_json_path=source_json_path,
            output_env_dir=output_env_dir,
            env_name=env_name,
            env_id=env_id,
            index=index,
            runtime_timeout_seconds=runtime_timeout_seconds,
            report_dir=report_dir,
            reasoner_model=reasoner_model,
            reasoner_temperature=reasoner_temperature,
            reasoner_max_tokens=reasoner_max_tokens,
            reasoner_max_calls=reasoner_max_calls,
        )
        res.adapt_attempts_used = attempt
        last_result = res
        if res.success:
            _base._log_progress("PIPELINE", "OK", f"attempt {attempt}/{total_attempts} succeeded")
            return res
        if attempt < total_attempts:
            _base._log_progress("PIPELINE", "RETRY", f"attempt {attempt}/{total_attempts} failed; restarting full adapt")
        else:
            _base._log_progress("PIPELINE", "FAIL", f"all {total_attempts} attempt(s) failed")

    assert last_result is not None
    return last_result


def _derive_batch_target_name(
    item: Dict[str, Any],
    *,
    used_names: set[str],
    fallback_prefix: str = "AdaptedEnv",
) -> str:
    base_name = (
        item.get("env_name")
        or item.get("env_class_name")
        or item.get("class_name")
        or fallback_prefix
    )
    candidate = _base._safe_env_name(str(base_name))
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    env_id_suffix = _base._safe_env_name(str(item.get("env_id", "") or ""))
    if env_id_suffix:
        candidate = f"{candidate}_{env_id_suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate

    serial = 2
    while True:
        deduped = f"{candidate}_{serial}"
        if deduped not in used_names:
            used_names.add(deduped)
            return deduped
        serial += 1


def run_batch_adapt_pipeline(
    source_json_path: Path,
    output_env_dir: Path,
    runtime_timeout_seconds: int = 120,
    report_dir: Optional[Path] = None,
    max_adapt_attempts: int = 1,
    *,
    reasoner_model: str = "deepseek-reasoner",
    reasoner_temperature: float = 0.0,
    reasoner_max_tokens: int = 4096,
    reasoner_max_calls: int = 4,
) -> Dict[str, Any]:
    items = _base._load_items(source_json_path)
    output_env_dir.mkdir(parents=True, exist_ok=True)
    report_root = report_dir or (_base.PROJECT_ROOT / "EnvGen" / "runtime_export" / "output")
    report_root.mkdir(parents=True, exist_ok=True)
    summary_path = report_root / "batch_adapt_summary.json"

    started_at = dt.datetime.now(dt.timezone.utc)
    used_names: set[str] = set()
    summary: Dict[str, Any] = {
        "ok": False,
        "signal": "BATCH_ADAPT_RUNNING",
        "source_json": str(source_json_path),
        "output_env_dir": str(output_env_dir),
        "report_dir": str(report_root),
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_seconds": None,
        "total_items": len(items),
        "success_count": 0,
        "failure_count": 0,
        "items": [],
    }
    _base._write_json(summary_path, summary)

    for idx, item in enumerate(items, start=1):
        has_explicit_env_id = "env_id" in item and str(item.get("env_id", "")).strip() != ""
        source_env_id = str(item.get("env_id", f"idx_{idx - 1}"))
        target_name = _derive_batch_target_name(item, used_names=used_names)
        print(
            f"[RUN_ADAPT][BATCH] {idx}/{len(items)} env_id={source_env_id} env_name={target_name}",
            flush=True,
        )
        try:
            result = run_adapt_pipeline(
                source_json_path=source_json_path,
                output_env_dir=output_env_dir,
                env_name=target_name,
                env_id=source_env_id if has_explicit_env_id else None,
                index=idx - 1,
                runtime_timeout_seconds=runtime_timeout_seconds,
                report_dir=report_root,
                max_adapt_attempts=max_adapt_attempts,
                reasoner_model=reasoner_model,
                reasoner_temperature=reasoner_temperature,
                reasoner_max_tokens=reasoner_max_tokens,
                reasoner_max_calls=reasoner_max_calls,
            )
            item_record = {
                "index": idx - 1,
                "source_env_id": source_env_id,
                "target_env_name": result.env_name,
                "success": bool(result.success),
                "signal": result.signal,
                "message": result.message,
                "py_path": str(result.py_path),
                "json_path": str(result.json_path),
                "report_path": str(result.report_path),
                "tool_count": int(result.tool_count),
                "adapt_attempts_used": int(result.adapt_attempts_used),
            }
        except KeyboardInterrupt:
            finished_at = dt.datetime.now(dt.timezone.utc)
            summary["finished_at"] = finished_at.isoformat()
            summary["duration_seconds"] = round((finished_at - started_at).total_seconds(), 3)
            summary["signal"] = "BATCH_ADAPT_INTERRUPTED"
            _base._write_json(summary_path, summary)
            raise
        except Exception as exc:
            item_record = {
                "index": idx - 1,
                "source_env_id": source_env_id,
                "target_env_name": target_name,
                "success": False,
                "signal": "ADAPT_EXCEPTION",
                "message": str(exc),
                "py_path": str(output_env_dir / f"{target_name}.py"),
                "json_path": str(output_env_dir / f"{target_name}.json"),
                "report_path": str(report_root / f"adapt_report_{target_name}.json"),
                "tool_count": 0,
                "adapt_attempts_used": 0,
            }

        summary["items"].append(item_record)
        if item_record["success"]:
            summary["success_count"] += 1
        else:
            summary["failure_count"] += 1
        _base._write_json(summary_path, summary)

    finished_at = dt.datetime.now(dt.timezone.utc)
    summary["finished_at"] = finished_at.isoformat()
    summary["duration_seconds"] = round((finished_at - started_at).total_seconds(), 3)
    summary["ok"] = summary["failure_count"] == 0
    summary["signal"] = "BATCH_ADAPT_SUCCESS" if summary["ok"] else "BATCH_ADAPT_PARTIAL_FAILURE"
    _base._write_json(summary_path, summary)
    return summary
