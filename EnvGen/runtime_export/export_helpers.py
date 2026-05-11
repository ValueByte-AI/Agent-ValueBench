"""Deterministic helpers for EnvGen runtime export.

This module contains only the non-LLM utilities used by the current
``run_adapt.py`` pipeline: source loading, schema normalization, static
adapter checks, and runtime smoke execution.
"""

from __future__ import annotations

import ast
import copy
import json
import re
import subprocess
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.json_utils import parse_json_with_fallback


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_TYPE_HINT_RECURSION_DEPTH = 32


@dataclass
class AdaptResult:
    env_name: str
    source_env_id: str
    py_path: Path
    json_path: Path
    tool_count: int
    success: bool
    signal: str
    repair_rounds: int
    report_path: Path
    message: str
    adapt_attempts_used: int = 1


@dataclass
class _TypedDictField:
    annotation: ast.expr
    required: bool = True


@dataclass
class _EnvTypeContext:
    typed_dicts: Dict[str, Dict[str, _TypedDictField]] = field(default_factory=dict)
    state_annotations: Dict[str, ast.expr] = field(default_factory=dict)


def _adapt_result_to_json_dict(result: AdaptResult) -> Dict[str, Any]:
    d = asdict(result)
    d["py_path"] = str(result.py_path)
    d["json_path"] = str(result.json_path)
    d["report_path"] = str(result.report_path)
    return d


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _log_progress(
    stage: str,
    status: str,
    message: str = "",
    *,
    round_idx: Optional[int] = None,
    round_total: Optional[int] = None,
) -> None:
    parts = ["[ADAPT]"]
    if round_idx is not None:
        if round_total is not None:
            parts.append(f"[R{round_idx}/{round_total}]")
        else:
            parts.append(f"[R{round_idx}]")
    parts.append(f"[{stage}]")
    parts.append(f"[{status}]")
    text = " ".join(parts)
    if message:
        text = f"{text} {message}"
    print(text, flush=True)


def _safe_env_name(text: str) -> str:
    name = re.sub(r"[^0-9A-Za-z_]", "", str(text or "").strip())
    if not name:
        name = "AdaptedEnv"
    if name[0].isdigit():
        name = f"Env{name}"
    return name


def _load_items(path: Path) -> List[Dict[str, Any]]:
    raw = _read_json(path)
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]

    if isinstance(raw, dict):
        if "env_class_code" in raw:
            return [raw]

        items: List[Dict[str, Any]] = []
        for key, value in raw.items():
            if not isinstance(value, dict):
                continue
            item = copy.deepcopy(value)
            item.setdefault("env_id", str(key))
            items.append(item)
        if items:
            return items

    raise ValueError(f"Unsupported source json format: {path}")


def _pick_item(items: List[Dict[str, Any]], env_id: Optional[str], index: int) -> Dict[str, Any]:
    if env_id:
        for item in items:
            if str(item.get("env_id", "")) == env_id:
                return item
        raise ValueError(f"env_id not found: {env_id}")

    if index < 0 or index >= len(items):
        raise IndexError(f"index out of range: {index}, total={len(items)}")
    return items[index]


def _schema_type_from_hint(type_hint: str) -> str:
    t = str(type_hint or "").lower()
    if "list" in t or "array" in t:
        return "array"
    if "dict" in t or "typedict" in t or "mapping" in t:
        return "object"
    if "int" in t:
        return "integer"
    if "float" in t or "double" in t or "number" in t:
        return "number"
    if "bool" in t:
        return "boolean"
    return "string"


def _annotation_name(annotation: Any) -> str:
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    if isinstance(annotation, ast.Subscript):
        return _annotation_name(annotation.value)
    return ""


def _annotation_to_source(annotation: Any) -> str:
    try:
        return ast.unparse(annotation)
    except Exception:
        return ""


def _parse_annotation_text(annotation_text: str) -> Optional[ast.expr]:
    text = str(annotation_text or "").strip()
    if not text:
        return None
    try:
        parsed = ast.parse(text, mode="eval")
    except SyntaxError:
        return None
    return parsed.body


def _normalize_annotation_expr(annotation: Any) -> Any:
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        parsed = _parse_annotation_text(annotation.value)
        if parsed is not None:
            return parsed
    return annotation


def _annotation_args(annotation: Any) -> List[ast.expr]:
    if not isinstance(annotation, ast.Subscript):
        return []
    slice_node = annotation.slice
    if isinstance(slice_node, ast.Tuple):
        return list(slice_node.elts)
    return [slice_node]


def _is_typed_dict_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if _annotation_name(base) == "TypedDict":
            return True
    return False


def _typed_dict_total(node: ast.ClassDef) -> bool:
    for kw in node.keywords:
        if kw.arg == "total" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, bool):
            return bool(kw.value.value)
    return True


def _collect_env_type_context(env_class_code: str) -> _EnvTypeContext:
    source = str(env_class_code or "").strip()
    if not source:
        return _EnvTypeContext()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _EnvTypeContext()

    ctx = _EnvTypeContext()

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not _is_typed_dict_class(node):
            continue
        total = _typed_dict_total(node)
        fields: Dict[str, _TypedDictField] = {}
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            field_name = str(stmt.target.id)
            annotation = _normalize_annotation_expr(stmt.annotation)
            required = total
            wrapper_name = _annotation_name(annotation)
            args = _annotation_args(annotation)
            if wrapper_name == "Required" and args:
                annotation = _normalize_annotation_expr(args[0])
                required = True
            elif wrapper_name == "NotRequired" and args:
                annotation = _normalize_annotation_expr(args[0])
                required = False
            fields[field_name] = _TypedDictField(annotation=annotation, required=required)
        if fields:
            ctx.typed_dicts[node.name] = fields

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or _is_typed_dict_class(node):
            continue
        init_func = None
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                init_func = stmt
                break
        scope = init_func.body if init_func is not None else node.body
        for stmt in ast.walk(ast.Module(body=scope, type_ignores=[])):
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Attribute):
                continue
            target = stmt.target
            if not isinstance(target.value, ast.Name) or target.value.id != "self":
                continue
            ctx.state_annotations[str(target.attr)] = _normalize_annotation_expr(stmt.annotation)

    return ctx


def _is_none_annotation(annotation: Any) -> bool:
    annotation = _normalize_annotation_expr(annotation)
    if isinstance(annotation, ast.Constant) and annotation.value is None:
        return True
    name = _annotation_name(annotation)
    return name in {"None", "NoneType"}


def _flatten_union_members(annotation: Any) -> List[ast.expr]:
    annotation = _normalize_annotation_expr(annotation)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _flatten_union_members(annotation.left) + _flatten_union_members(annotation.right)

    name = _annotation_name(annotation)
    args = _annotation_args(annotation)
    if name == "Optional" and args:
        members = [args[0], ast.Constant(value=None)]
        return [m for member in members for m in _flatten_union_members(member)]
    if name == "Union" and args:
        return [m for member in args for m in _flatten_union_members(member)]
    return [annotation]


def _schema_fallback_from_annotation(annotation: Any) -> Dict[str, Any]:
    text = _annotation_to_source(annotation)
    guessed = _schema_type_from_hint(text)
    if guessed == "string":
        base_name = _annotation_name(annotation)
        if base_name and re.match(r"^[A-Z_][A-Za-z0-9_]*$", base_name):
            guessed = "object"
    return {"type": guessed}


def _schema_is_unconstrained(schema: Any) -> bool:
    return isinstance(schema, dict) and not schema


def _collapse_union_schema_candidates(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    if any(_schema_is_unconstrained(item) for item in candidates):
        return {}

    types = [str(item.get("type", "")).strip() for item in candidates if isinstance(item, dict) and str(item.get("type", "")).strip()]
    if not types:
        return {}
    unique = set(types)
    if len(unique) == 1:
        return copy.deepcopy(candidates[0])
    if unique <= {"integer", "number"}:
        return {"type": "number"}
    if "object" in unique:
        return {"type": "object"}
    if "array" in unique:
        return {"type": "array", "items": {"type": "string"}}
    return {"type": "string"}


def _annotation_to_schema(
    annotation: Any,
    ctx: _EnvTypeContext,
    *,
    _active_typed_dicts: Optional[set] = None,
    _depth: int = 0,
) -> Dict[str, Any]:
    if _active_typed_dicts is None:
        _active_typed_dicts = set()

    annotation = _normalize_annotation_expr(annotation)
    if annotation is None:
        return {"type": "string"}

    if _depth > MAX_TYPE_HINT_RECURSION_DEPTH:
        return _schema_fallback_from_annotation(annotation)

    union_members = _flatten_union_members(annotation)
    if len(union_members) > 1:
        non_null_members = [member for member in union_members if not _is_none_annotation(member)]
        if len(non_null_members) == 1:
            return _annotation_to_schema(
                non_null_members[0],
                ctx,
                _active_typed_dicts=_active_typed_dicts,
                _depth=_depth + 1,
            )
        return _collapse_union_schema_candidates(
            [
                _annotation_to_schema(
                    member,
                    ctx,
                    _active_typed_dicts=_active_typed_dicts,
                    _depth=_depth + 1,
                )
                for member in non_null_members
            ]
        )

    name = _annotation_name(annotation)
    args = _annotation_args(annotation)

    if name in ctx.typed_dicts:
        if name in _active_typed_dicts:
            return {"type": "object"}
        _active_typed_dicts.add(name)
        fields = ctx.typed_dicts.get(name, {})
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for field_name, field_info in fields.items():
            properties[field_name] = _annotation_to_schema(
                field_info.annotation,
                ctx,
                _active_typed_dicts=_active_typed_dicts,
                _depth=_depth + 1,
            )
            if field_info.required:
                required.append(field_name)
        _active_typed_dicts.discard(name)
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    if name in {"Required", "NotRequired", "Annotated", "ReadOnly"} and args:
        return _annotation_to_schema(
            args[0],
            ctx,
            _active_typed_dicts=_active_typed_dicts,
            _depth=_depth + 1,
        )

    if name in {"list", "List", "Sequence", "MutableSequence", "Iterable", "set", "Set", "frozenset", "FrozenSet"}:
        if not args:
            return {"type": "array"}
        item_schema = _annotation_to_schema(
            args[0],
            ctx,
            _active_typed_dicts=_active_typed_dicts,
            _depth=_depth + 1,
        )
        if _schema_is_unconstrained(item_schema):
            return {"type": "array"}
        return {"type": "array", "items": item_schema}

    if name in {"tuple", "Tuple"}:
        if len(args) == 2 and isinstance(args[1], ast.Constant) and args[1].value is Ellipsis:
            item_schema = _annotation_to_schema(
                args[0],
                ctx,
                _active_typed_dicts=_active_typed_dicts,
                _depth=_depth + 1,
            )
            if _schema_is_unconstrained(item_schema):
                return {"type": "array"}
            return {"type": "array", "items": item_schema}
        if args:
            item_candidates = [
                _annotation_to_schema(
                    arg,
                    ctx,
                    _active_typed_dicts=_active_typed_dicts,
                    _depth=_depth + 1,
                )
                for arg in args
            ]
            item_schema = _collapse_union_schema_candidates(item_candidates)
            if _schema_is_unconstrained(item_schema):
                return {"type": "array"}
            return {"type": "array", "items": item_schema}
        return {"type": "array"}

    if name in {"dict", "Dict", "Mapping", "MutableMapping", "DefaultDict"}:
        value_annotation = args[1] if len(args) >= 2 else None
        if value_annotation is None:
            return {"type": "object"}
        value_schema = _annotation_to_schema(
            value_annotation,
            ctx,
            _active_typed_dicts=_active_typed_dicts,
            _depth=_depth + 1,
        )
        if _schema_is_unconstrained(value_schema):
            return {"type": "object"}
        return {
            "type": "object",
            "additionalProperties": value_schema,
        }

    if name == "Literal" and args:
        literal_types = []
        for arg in args:
            if isinstance(arg, ast.Constant):
                literal_types.append(type(arg.value).__name__)
        if literal_types:
            sample_type = literal_types[0]
            if sample_type == "str":
                return {"type": "string"}
            if sample_type == "int":
                return {"type": "integer"}
            if sample_type == "float":
                return {"type": "number"}
            if sample_type == "bool":
                return {"type": "boolean"}

    primitive_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "None": "null",
        "NoneType": "null",
    }
    if name in primitive_map:
        return {"type": primitive_map[name]}
    if name in {"Any", "object"}:
        return {}

    return _schema_fallback_from_annotation(annotation)


def _infer_schema_from_value(value: Any) -> Dict[str, Any]:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, list):
        schema: Dict[str, Any] = {"type": "array"}
        if value:
            schema["items"] = _infer_schema_from_value(value[0])
        return schema
    if isinstance(value, dict):
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for key, item in value.items():
            k = str(key)
            properties[k] = _infer_schema_from_value(item)
            required.append(k)
        return {"type": "object", "properties": properties, "required": required}
    return {"type": "string"}


def _build_initial_parameters(item: Dict[str, Any]) -> Dict[str, Any]:
    initial_parameters = item.get("initial_parameters")
    if isinstance(initial_parameters, dict) and initial_parameters:
        return copy.deepcopy(initial_parameters)

    eval_init_config = item.get("eval_init_config")
    if isinstance(eval_init_config, dict) and eval_init_config:
        return copy.deepcopy(eval_init_config)

    init_list = item.get("init_config_list", [])
    if isinstance(init_list, list) and init_list and isinstance(init_list[0], dict):
        return copy.deepcopy(init_list[0])

    if isinstance(initial_parameters, dict):
        return copy.deepcopy(initial_parameters)
    return {}


def _build_initial_parameter_schema(item: Dict[str, Any]) -> Dict[str, Any]:
    raw = item.get("initial_parameter_schema")
    if isinstance(raw, dict) and raw:
        return copy.deepcopy(raw)

    schema: Dict[str, Any] = {}
    states = ((item.get("env_structure") or {}).get("states") or {})
    ctx = _collect_env_type_context(str(item.get("env_class_code", "") or ""))
    if isinstance(states, dict):
        for state_name, state_info in states.items():
            name = str(state_name).strip()
            if not name or name == "init_config":
                continue
            type_hint = ""
            if isinstance(state_info, dict):
                type_hint = str(state_info.get("type", ""))
            annotation = ctx.state_annotations.get(name)
            if annotation is None and type_hint:
                annotation = _parse_annotation_text(type_hint)

            if annotation is not None:
                schema[name] = _annotation_to_schema(annotation, ctx)
            else:
                schema[name] = {"type": _schema_type_from_hint(type_hint)}

    if schema:
        return schema

    defaults = _build_initial_parameters(item)
    inferred: Dict[str, Any] = {}
    if isinstance(defaults, dict):
        for key, value in defaults.items():
            k = str(key)
            inferred[k] = _infer_schema_from_value(value)
    return inferred


def _convert_tools(tools_raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(tools_raw, list):
        return out

    for t in tools_raw:
        if not isinstance(t, dict):
            continue

        if "function" in t and isinstance(t.get("function"), dict):
            fn = t["function"]
            name = str(fn.get("name", "")).strip()
            if not name:
                continue
            params = fn.get("parameters", {})
            if not isinstance(params, dict):
                params = {"type": "object", "properties": {}, "required": []}
            params.setdefault("type", "object")
            if not isinstance(params.get("properties"), dict):
                params["properties"] = {}
            if not isinstance(params.get("required"), list):
                params["required"] = []
            out.append(
                {
                    "name": name,
                    "description": str(fn.get("description", "")),
                    "parameters": params,
                }
            )
            continue

        name = str(t.get("name", "")).strip()
        if not name:
            continue
        params = t.get("parameters", {})
        if not isinstance(params, dict):
            params = {"type": "object", "properties": {}, "required": []}
        params.setdefault("type", "object")
        if not isinstance(params.get("properties"), dict):
            params["properties"] = {}
        if not isinstance(params.get("required"), list):
            params["required"] = []
        out.append(
            {
                "name": name,
                "description": str(t.get("description", "")),
                "parameters": params,
            }
        )

    dedup: List[Dict[str, Any]] = []
    seen = set()
    for t in out:
        n = t["name"]
        if n in seen:
            continue
        seen.add(n)
        dedup.append(t)
    return dedup


def _build_tool_state_dependencies(item: Dict[str, Any], tools: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    methods = ((item.get("env_structure") or {}).get("methods") or {})
    deps: Dict[str, List[str]] = {}
    if not isinstance(methods, dict):
        methods = {}

    for tool in tools:
        name = tool.get("name", "")
        info = methods.get(name, {}) if isinstance(methods, dict) else {}
        if not isinstance(info, dict):
            info = {}

        reads = info.get("reads", []) if isinstance(info.get("reads", []), list) else []
        writes = info.get("writes", []) if isinstance(info.get("writes", []), list) else []
        merged: List[str] = []
        for x in reads + writes:
            sx = str(x).strip()
            if not sx or sx == "init_config" or sx in merged:
                continue
            merged.append(sx)
        deps[name] = merged
    return deps


def _build_base_json_candidate(item: Dict[str, Any], target_name: str) -> Dict[str, Any]:
    tools = _convert_tools(item.get("tools", []))
    env_json = {
        "env_name": target_name,
        "description": str(item.get("environment_introduction", item.get("description", ""))),
        "initial_parameter_schema": _build_initial_parameter_schema(item),
        "tool_state_dependencies": _build_tool_state_dependencies(item, tools),
        "tools": tools,
    }
    return env_json


def _normalize_json_candidate(candidate: Any, item: Dict[str, Any], target_name: str) -> Dict[str, Any]:
    base = _build_base_json_candidate(item, target_name)
    if not isinstance(candidate, dict):
        return base

    out = copy.deepcopy(base)
    out["env_name"] = target_name
    if isinstance(candidate.get("description"), str):
        out["description"] = candidate.get("description", "")

    ips = candidate.get("initial_parameter_schema")
    if isinstance(ips, dict) and ips:
        out["initial_parameter_schema"] = copy.deepcopy(ips)

    tools = _convert_tools(candidate.get("tools", []))
    if tools:
        out["tools"] = tools

    deps = candidate.get("tool_state_dependencies")
    if isinstance(deps, dict):
        clean_deps: Dict[str, List[str]] = {}
        for k, v in deps.items():
            if not isinstance(v, list):
                continue
            clean_deps[str(k)] = [str(x) for x in v if isinstance(x, (str, int, float))]
        out["tool_state_dependencies"] = clean_deps

    if not isinstance(out.get("tool_state_dependencies"), dict):
        out["tool_state_dependencies"] = {}

    for tool in out.get("tools", []):
        name = tool.get("name", "")
        out["tool_state_dependencies"].setdefault(name, [])

    if not isinstance(out.get("initial_parameter_schema"), dict):
        out["initial_parameter_schema"] = {}

    return out


def _validate_json_candidate(env_json: Dict[str, Any], target_name: str) -> List[str]:
    issues: List[str] = []

    required_keys = [
        "env_name",
        "description",
        "initial_parameter_schema",
        "tool_state_dependencies",
        "tools",
    ]
    for key in required_keys:
        if key not in env_json:
            issues.append(f"Missing top-level key: {key}")

    if str(env_json.get("env_name", "")) != target_name:
        issues.append(f"env_name must be '{target_name}'")

    if not isinstance(env_json.get("description", ""), str):
        issues.append("description must be string")
    if not isinstance(env_json.get("initial_parameter_schema", {}), dict):
        issues.append("initial_parameter_schema must be object")
    if not isinstance(env_json.get("tool_state_dependencies", {}), dict):
        issues.append("tool_state_dependencies must be object")

    tools = env_json.get("tools", [])
    if not isinstance(tools, list) or not tools:
        issues.append("tools must be non-empty list")
        return issues

    tool_names: List[str] = []
    for idx, tool in enumerate(tools):
        if not isinstance(tool, dict):
            issues.append(f"tools[{idx}] must be object")
            continue
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            issues.append(f"tools[{idx}].name must be non-empty string")
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            issues.append(f"Tool name not valid python identifier: {name}")
        if name in tool_names:
            issues.append(f"Duplicated tool name: {name}")
        tool_names.append(name)

        params = tool.get("parameters")
        if not isinstance(params, dict):
            issues.append(f"tools[{idx}].parameters must be object")
            continue
        if params.get("type") != "object":
            issues.append(f"tools[{idx}].parameters.type must be 'object'")
        if not isinstance(params.get("properties", {}), dict):
            issues.append(f"tools[{idx}].parameters.properties must be object")
        if not isinstance(params.get("required", []), list):
            issues.append(f"tools[{idx}].parameters.required must be list")

    deps = env_json.get("tool_state_dependencies", {})
    for name in tool_names:
        if name not in deps:
            issues.append(f"tool_state_dependencies missing key for tool: {name}")
        elif not isinstance(deps[name], list):
            issues.append(f"tool_state_dependencies['{name}'] must be list")

    return issues


def _strip_future_imports(code: str) -> str:
    out_lines: List[str] = []
    for ln in str(code).splitlines():
        if ln.strip().startswith("from __future__ import"):
            continue
        out_lines.append(ln)
    return "\n".join(out_lines).strip() + "\n"


def _apply_deterministic_py_fixes(py_code: str) -> str:
    return str(py_code or "")


def _validate_python_static(py_code: str, env_name: str, tool_names: List[str]) -> List[str]:
    issues: List[str] = []

    source = str(py_code or "")
    if not source.strip():
        return ["python_code_empty"]

    try:
        tree = ast.parse(source)
    except Exception as exc:
        return [f"ast_parse_failed: {exc}"]

    class_nodes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    cls_node = None
    for node in class_nodes:
        if node.name == env_name:
            cls_node = node
            break
    if cls_node is None:
        issues.append(f"class '{env_name}' not found")
        return issues

    has_base_import = "from .BaseEnv import BaseEnv" in source
    if not has_base_import:
        issues.append("missing relative import: from .BaseEnv import BaseEnv")

    method_names = {n.name for n in cls_node.body if isinstance(n, ast.FunctionDef)}
    for tool_name in tool_names:
        if tool_name not in method_names:
            issues.append(f"tool method missing in adapter class: {tool_name}")

    if "_GeneratedEnvImpl" not in source:
        issues.append("missing _GeneratedEnvImpl class in module")

    try:
        compile(source, filename=f"{env_name}.py", mode="exec")
    except Exception as exc:
        issues.append(f"compile_failed: {exc}")

    return issues


def _sample_value_from_schema(schema: Dict[str, Any], key_hint: str = "") -> Any:
    if not isinstance(schema, dict):
        return None

    stype = str(schema.get("type", "string")).lower()
    if stype == "string":
        return f"{key_hint or 'value'}_sample"
    if stype == "integer":
        return 1
    if stype == "number":
        return 1.0
    if stype == "boolean":
        return True
    if stype == "array":
        items = schema.get("items", {}) if isinstance(schema.get("items", {}), dict) else {}
        return [_sample_value_from_schema(items, key_hint=key_hint)]
    if stype == "object":
        props = schema.get("properties", {}) if isinstance(schema.get("properties", {}), dict) else {}
        required = schema.get("required", []) if isinstance(schema.get("required", []), list) else []
        additional = schema.get("additionalProperties") if isinstance(schema.get("additionalProperties"), dict) else {}

        if props:
            keys = required if required else list(props.keys())[:3]
            obj: Dict[str, Any] = {}
            for k in keys:
                if k in props:
                    obj[k] = _sample_value_from_schema(props[k], key_hint=str(k))
            return obj

        if additional:
            singular = key_hint[:-1] if key_hint.endswith("s") else key_hint or "item"
            return {
                f"{singular}_001": _sample_value_from_schema(additional, key_hint=singular)
            }

        singular = key_hint[:-1] if key_hint.endswith("s") else key_hint or "item"
        return {
            f"{singular}_001": {
                "_id": f"{singular}_001",
                "name": f"{singular}_name",
            }
        }

    return None


def _build_sample_initial_parameters(env_json: Dict[str, Any]) -> Dict[str, Any]:
    defaults = env_json.get("initial_parameters", {})
    if not isinstance(defaults, dict):
        defaults = {}
    out = copy.deepcopy(defaults)

    schema = env_json.get("initial_parameter_schema", {})
    if not isinstance(schema, dict):
        return out

    for key, sdef in schema.items():
        if key not in out:
            out[key] = _sample_value_from_schema(sdef if isinstance(sdef, dict) else {}, key_hint=str(key))
    return out


def _collect_values_by_key(obj: Any, target_key: str, out: List[Any]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) == target_key:
                out.append(v)
            _collect_values_by_key(v, target_key, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_values_by_key(item, target_key, out)


def _pick_argument_value(param_name: str, param_schema: Dict[str, Any], init_params: Dict[str, Any]) -> Any:
    values: List[Any] = []
    _collect_values_by_key(init_params, param_name, values)
    for v in values:
        if isinstance(v, (str, int, float, bool)):
            return v
        if isinstance(v, list) and v and isinstance(v[0], (str, int, float, bool)):
            return v[0]

    return _sample_value_from_schema(param_schema if isinstance(param_schema, dict) else {}, key_hint=param_name)


def _build_tool_call_plan(env_json: Dict[str, Any], init_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []
    tools = env_json.get("tools", [])
    if not isinstance(tools, list):
        return plan

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name", "")).strip()
        if not name:
            continue
        params = tool.get("parameters", {}) if isinstance(tool.get("parameters", {}), dict) else {}
        props = params.get("properties", {}) if isinstance(params.get("properties", {}), dict) else {}
        required = params.get("required", []) if isinstance(params.get("required", []), list) else []

        call_args: Dict[str, Any] = {}
        for req in required:
            req_name = str(req)
            call_args[req_name] = _pick_argument_value(req_name, props.get(req_name, {}), init_params)

        plan.append({"tool_name": name, "arguments": call_args})

    return plan


def _normalize_call_plan(
    plan_candidate: Any,
    env_json: Dict[str, Any],
    fallback_plan: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    tools = env_json.get("tools", [])
    if not isinstance(tools, list):
        return fallback_plan

    valid_tools: Dict[str, Dict[str, Any]] = {}
    for tool in tools:
        if isinstance(tool, dict):
            name = str(tool.get("name", "")).strip()
            if name:
                valid_tools[name] = tool

    if not isinstance(plan_candidate, list):
        return fallback_plan

    out: List[Dict[str, Any]] = []
    used = set()
    for row in plan_candidate:
        if not isinstance(row, dict):
            continue
        name = str(row.get("tool_name", "")).strip()
        if not name or name not in valid_tools or name in used:
            continue
        args = row.get("arguments", {})
        if not isinstance(args, dict):
            args = {}
        out.append({"tool_name": name, "arguments": args})
        used.add(name)

    if not out:
        return fallback_plan

    by_name = {x.get("tool_name"): x for x in fallback_plan if isinstance(x, dict)}
    for name in valid_tools:
        if name not in used and name in by_name:
            out.append(copy.deepcopy(by_name[name]))

    return out


def _run_runtime_smoke(
    project_root: Path,
    env_name: str,
    init_params: Dict[str, Any],
    call_plan: List[Dict[str, Any]],
    timeout_seconds: int,
) -> Dict[str, Any]:
    payload = {
        "project_root": str(project_root),
        "env_name": env_name,
        "init_params": init_params,
        "call_plan": call_plan,
    }

    script = textwrap.dedent(
        """
        import copy
        import json
        import sys

        data = json.load(sys.stdin)
        project_root = data["project_root"]
        env_name = data["env_name"]
        init_params = data.get("init_params", {})
        call_plan = data.get("call_plan", [])

        sys.path.insert(0, project_root)

        try:
            from environment import EnvManager
            manager = EnvManager()
            env = manager.init_env(env_name, init_params)
            if env is None:
                print(json.dumps({"ok": False, "error": f"init_env returned None for {env_name}", "calls": []}, ensure_ascii=False))
                sys.exit(0)

            calls = []
            for row in call_plan:
                name = row.get("tool_name")
                args = row.get("arguments", {}) or {}
                if not env.has_tool(name):
                    calls.append({
                        "tool_name": name,
                        "arguments": args,
                        "result": {"success": False, "message": f"tool missing: {name}"},
                        "ok": False,
                    })
                    continue

                try:
                    result = env.call_tool(name, copy.deepcopy(args))
                    calls.append({
                        "tool_name": name,
                        "arguments": args,
                        "result": result,
                        "ok": bool(isinstance(result, dict) and result.get("success", False)),
                    })
                except Exception as exc:
                    calls.append({
                        "tool_name": name,
                        "arguments": args,
                        "result": {"success": False, "message": f"runtime exception: {exc}"},
                        "ok": False,
                    })

            print(json.dumps({"ok": True, "error": None, "calls": calls}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc), "calls": []}, ensure_ascii=False))
        """
    ).strip()

    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=int(timeout_seconds),
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": f"subprocess_failed: {exc}", "calls": []}

    stdout = (proc.stdout or "").strip()
    if not stdout:
        return {"ok": False, "error": f"empty_subprocess_output: {proc.stderr}", "calls": []}

    parsed = parse_json_with_fallback(stdout, {"ok": False, "error": "parse_failed", "calls": []})
    if not isinstance(parsed, dict):
        return {"ok": False, "error": "invalid_runtime_response", "calls": []}
    parsed.setdefault("calls", [])
    parsed.setdefault("ok", False)
    parsed.setdefault("error", None)
    if proc.returncode != 0 and not parsed.get("error"):
        parsed["error"] = f"subprocess_returncode={proc.returncode}, stderr={proc.stderr}"
    return parsed
