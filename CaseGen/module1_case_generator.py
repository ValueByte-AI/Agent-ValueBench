# -*- coding: utf-8 -*-
"""
Single-case CaseGen pipeline.

Current flow:
1) Sample a value pair and select an environment.
2) Run Stage 1 to draft the conflict scenario.
3) Run Stage 2 to realize the executable case.
4) Validate environment alignment.
5) Run the independent case quality gate with an LLM judge.
"""

from __future__ import annotations

import copy
import json
import random
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config import (
    DEFAULT_LLM_CONFIG,
    DEFAULT_MAX_TOKENS,
    ENABLE_LEGACY_SCHEMA_INFERENCE,
    LLMConfig,
)
from core.debug_trace import trace_event, trace_log
from core.file_utils import ensure_dir, read_json, write_json
from core.json_utils import extract_json_candidate
from core.llm_client import UnifiedLLMClient
from environment import EnvManager
from CaseGen.module2_case_validator import CaseTaskValidator
from CaseGen.prompts.stage1_case_prompt import build_stage1_prompt
from CaseGen.prompts.stage2_case_prompt import build_stage2_prompt


STAGE1_DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS
STAGE2_DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS
STAGE2_STREAM_DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS
STAGE2_STREAM_DEFAULT_TIMEOUT_SECONDS = 600
JSON_PARSE_MAX_ATTEMPTS = 3
CASEGEN_DEFAULT_API_KEY: Optional[str] = None
CASEGEN_DEFAULT_BASE_URL = ""
CASEGEN_DEFAULT_GEN_MODEL = ""
CASEGEN_DEFAULT_JUDGE_MODEL = ""


class CaseGeneratorPipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.config_path = self.project_root / "configs" / "value_systems.json"
        self.env_dir = self.project_root / "environment"
        self.case_dir = self.project_root / "case"
        self.traj_dir = self.project_root / "traj"

        ensure_dir(self.case_dir)

        self.llm = UnifiedLLMClient()
        self.llm_gen = self.llm
        self.case_validator = CaseTaskValidator()
        self.env_manager = EnvManager()
        self.eval_llm_overrides: Dict[str, Optional[str]] = {
            "api_key": None,
            "base_url": None,
            "model": None,
        }

        self.value_systems = self._load_value_systems()
        self.env_defs = self._load_env_definitions()

    def _load_value_systems(self) -> Dict[str, Dict[str, Any]]:
        data = read_json(self.config_path)
        if not isinstance(data, dict):
            raise ValueError(f"value_systems.json must contain a JSON object: {self.config_path}")
        return data

    def _load_env_definitions(self) -> Dict[str, Dict[str, Any]]:
        env_defs: Dict[str, Dict[str, Any]] = {}
        for env_name in self.env_manager.list_envs():
            env_obj = self.env_manager.init_env(env_name, {})
            if env_obj is None:
                continue

            try:
                runtime_tools = env_obj.get_tool_descs(list(env_obj.tool_list))
            except Exception:
                runtime_tools = []

            if not isinstance(runtime_tools, list):
                runtime_tools = []
            runtime_tools = [copy.deepcopy(t) for t in runtime_tools if isinstance(t, dict)]
            if not runtime_tools:
                continue

            json_path = self.env_dir / f"{env_name}.json"
            raw_json: Dict[str, Any] = {}
            if json_path.exists():
                loaded = read_json(json_path)
                if isinstance(loaded, dict):
                    raw_json = loaded

            description = raw_json.get("description", "")
            if not isinstance(description, str) or not description.strip():
                description = str(getattr(env_obj, "env_description", "") or "")

            tool_state_dependencies = raw_json.get("tool_state_dependencies", {})
            if not isinstance(tool_state_dependencies, dict):
                tool_state_dependencies = {}

            initial_parameter_schema = env_obj.get_initial_parameter_schema()
            if not isinstance(initial_parameter_schema, dict):
                initial_parameter_schema = {}

            env_defs[env_name] = {
                "env_name": env_name,
                "description": description,
                "initial_parameter_schema": copy.deepcopy(initial_parameter_schema),
                "tool_state_dependencies": copy.deepcopy(tool_state_dependencies),
                "tools": runtime_tools,
            }
        if not env_defs:
            raise ValueError(f"No usable environment definitions were loaded from: {self.env_dir}")
        return env_defs

    def list_environments(self) -> List[str]:
        return sorted(self.env_defs.keys())

    @staticmethod
    def _preview_failure_payload(payload: Any, max_chars: int = 1200) -> str:
        try:
            text = json.dumps(payload, ensure_ascii=False)
        except Exception:
            text = repr(payload)
        if len(text) > max_chars:
            text = text[:max_chars] + "...(truncated)"
        return text

    def _log_case_gate_failure(
        self,
        *,
        env_name: str,
        attempt_idx: int,
        max_attempts: int,
        case_name: str,
        stage: str,
        payload: Dict[str, Any],
    ) -> None:
        reason = str(payload.get("reason", "")).strip() if isinstance(payload, dict) else ""
        details = payload.get("details", {}) if isinstance(payload, dict) else {}
        blocked_at = payload.get("blocked_at", {}) if isinstance(payload, dict) else {}
        failed_criteria = payload.get("failed_criteria", []) if isinstance(payload, dict) else []
        if not reason and isinstance(payload, dict):
            judge_result = payload.get("judge_result", {})
            if isinstance(judge_result, dict):
                reason = str(judge_result.get("reason", "")).strip()
                if not failed_criteria:
                    failed_criteria = judge_result.get("failed_criteria", [])
                if not blocked_at:
                    blocked_at = judge_result.get("blocked_at", {})
            if not reason:
                pipeline_blockers = payload.get("pipeline_blockers", [])
                if isinstance(pipeline_blockers, list) and pipeline_blockers:
                    first_blocker = pipeline_blockers[0]
                    if isinstance(first_blocker, dict):
                        reason = str(first_blocker.get("reason", "")).strip()
                        if not blocked_at:
                            blocked_at = first_blocker.get("blocked_at", {})
        print(
            "[CaseGen][CASE-FAIL] "
            f"env={env_name} attempt={attempt_idx}/{max_attempts} case={case_name} "
            f"stage={stage} reason={reason or '<none>'} "
            f"blocked_at={self._preview_failure_payload(blocked_at)} "
            f"failed_criteria={self._preview_failure_payload(failed_criteria)} "
            f"details={self._preview_failure_payload(details)}",
            flush=True,
        )

    def generate_cases(
        self,
        num_cases: int = 1,
        env_name: Optional[str] = None,
        value_system: Optional[str] = None,
        auto_compare: bool = True,
        baseline_only_compare: bool = False,
        baseline_only_skip_checkpoint_coverage_judges: bool = False,
        # generation: CaseGen Stage 1 / Stage 2
        gen_api_key: Optional[str] = CASEGEN_DEFAULT_API_KEY,
        gen_base_url: Optional[str] = None,
        gen_model: Optional[str] = None,
        # check: CaseGen quality gate
        check_api_key: Optional[str] = CASEGEN_DEFAULT_API_KEY,
        check_base_url: Optional[str] = None,
        check_model: Optional[str] = None,
        # reserved eval client override
        eval_api_key: Optional[str] = None,
        eval_base_url: Optional[str] = None,
        eval_model: Optional[str] = None,
        coverage_prompt_mode: str = "strict",
        stage1_max_tokens: Optional[int] = None,
        stage2_stream_collect: bool = False,
        stage2_max_tokens: Optional[int] = None,
        stage2_timeout_seconds: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        self._configure_llm_clients(
            gen_api_key=gen_api_key,
            gen_base_url=gen_base_url,
            gen_model=gen_model,
            check_api_key=check_api_key,
            check_base_url=check_base_url,
            check_model=check_model,
            eval_api_key=eval_api_key,
            eval_base_url=eval_base_url,
            eval_model=eval_model,
        )
        results: List[Dict[str, Any]] = []

        for _ in range(num_cases):
            selected_env = self._pick_environment(env_name)
            env_def = self.env_defs[selected_env]

            selected_vs, value_a, value_b, value_a_definition, value_b_definition = self._pick_value_pair(value_system)
            case_env_dir = self.case_dir / selected_env
            ensure_dir(case_env_dir)

            stage1: Dict[str, Any] = {}
            stage2: Dict[str, Any] = {}
            tmp_path: Optional[Path] = None
            final_path: Optional[Path] = None
            compare_result: Optional[Dict[str, Any]] = None
            alignment_report: Dict[str, Any] = {}
            consistency_before: Dict[str, Any] = {}
            consistency_after: Dict[str, Any] = {}
            case_validation: Dict[str, Any] = {}
            last_cleanup: Dict[str, Any] = {"removed": [], "errors": []}
            last_failure_stage: str = "unknown"
            attempt_count = 0
            success = False

            # Validation failures clean up case artifacts and retry:
            # environment alignment -> case quality gate.
            max_attempts = 3
            for attempt_idx in range(max_attempts):
                attempt_count = attempt_idx + 1
                trace_log(
                    f"[CaseGen][RUN] env={selected_env} attempt={attempt_count}/{max_attempts} step=stage1"
                )
                trace_event(
                    "casegen",
                    "attempt_start",
                    {
                        "environment": selected_env,
                        "attempt": attempt_count,
                        "max_attempts": max_attempts,
                        "value_system": selected_vs,
                        "value_items": [value_a, value_b],
                    },
                )
                stage1 = self._run_stage1(
                    env_name=selected_env,
                    env_def=env_def,
                    value_system_name=selected_vs,
                    value_a=value_a,
                    value_b=value_b,
                    value_a_definition=value_a_definition,
                    value_b_definition=value_b_definition,
                    stage1_max_tokens=stage1_max_tokens,
                )

                tmp_path = case_env_dir / f"{stage1['case_name']}_tmp.json"
                write_json(tmp_path, stage1)
                trace_event(
                    "casegen",
                    "stage1_output_written",
                    {
                        "case_name": stage1.get("case_name"),
                        "tmp_path": str(tmp_path),
                        "stage1": stage1,
                    },
                )

                trace_log(
                    f"[CaseGen][RUN] env={selected_env} attempt={attempt_count}/{max_attempts} step=stage2 case={stage1.get('case_name')}"
                )
                try:
                    stage2 = self._run_stage2(
                        tmp_case=stage1,
                        env_def=env_def,
                        selected_env=selected_env,
                        value_system_name=selected_vs,
                        value_a=value_a,
                        value_b=value_b,
                        value_a_definition=value_a_definition,
                        value_b_definition=value_b_definition,
                        stage2_stream_collect=stage2_stream_collect,
                        stage2_max_tokens=stage2_max_tokens,
                        stage2_timeout_seconds=stage2_timeout_seconds,
                    )
                except Exception as exc:
                    self._log_case_gate_failure(
                        env_name=selected_env,
                        attempt_idx=attempt_count,
                        max_attempts=max_attempts,
                        case_name=str(stage1.get("case_name", "case_unnamed")),
                        stage="stage2_generation_or_parse",
                        payload={
                            "reason": str(exc),
                            "blocked_at": {
                                "component": "stage2_output",
                                "location": "stage2_json_parse",
                                "why": str(exc),
                            },
                            "details": {},
                        },
                    )
                    trace_event(
                        "casegen_stage2",
                        "failed",
                        {
                            "environment": selected_env,
                            "case_name": stage1.get("case_name"),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        },
                    )
                    last_failure_stage = "stage2_generation_or_parse"
                    last_cleanup = self._cleanup_case_artifacts(
                        env_name=selected_env,
                        case_name=stage1.get("case_name", "case_unnamed"),
                    )
                    raise RuntimeError(f"[CaseGen][{selected_env}] stage2_generation_or_parse failed: {exc}") from exc

                consistency_before = self._validate_case_against_env(
                    case_data=stage2,
                    env_name=selected_env,
                    env_def=env_def,
                )
                if int(consistency_before.get("keep", 0)) != 1:
                    self._log_case_gate_failure(
                        env_name=selected_env,
                        attempt_idx=attempt_count,
                        max_attempts=max_attempts,
                        case_name=str(stage2.get("case_name", stage1.get("case_name", "case_unnamed"))),
                        stage="env_alignment_validation_before",
                        payload=consistency_before,
                    )
                    last_failure_stage = "env_alignment_validation_before"
                    last_cleanup = self._cleanup_case_artifacts(
                        env_name=selected_env,
                        case_name=stage2.get("case_name", stage1.get("case_name", "case_unnamed")),
                    )
                    raise RuntimeError(
                        f"[CaseGen][{selected_env}] env_alignment_validation_before failed: "
                        f"{consistency_before.get('reason', '')}"
                    )

                alignment_report = {
                    "mode": "disabled",
                    "reason": "runtime auto-alignment removed; no auto drop/fill on tools or state keys",
                }
                consistency_after = copy.deepcopy(consistency_before)

                judge_case = copy.deepcopy(stage2)
                judge_case["value_item_definitions"] = {
                    str(value_a): str(value_a_definition),
                    str(value_b): str(value_b_definition),
                }
                case_validation = self.case_validator.validate_case(judge_case)
                if int(case_validation.get("keep", 0)) != 1:
                    self._log_case_gate_failure(
                        env_name=selected_env,
                        attempt_idx=attempt_count,
                        max_attempts=max_attempts,
                        case_name=str(stage2.get("case_name", stage1["case_name"])),
                        stage="case_validation",
                        payload=case_validation,
                    )
                    last_failure_stage = "case_validation"
                    last_cleanup = self._cleanup_case_artifacts(
                        env_name=selected_env,
                        case_name=stage2.get("case_name", stage1["case_name"]),
                    )
                    raise RuntimeError(
                        f"[CaseGen][{selected_env}] case_validation failed: "
                        f"{case_validation.get('reason', '')}"
                    )

                final_case = copy.deepcopy(stage2)
                final_case.pop("finite_state", None)
                final_path = case_env_dir / f"{stage2['case_name']}.json"
                write_json(final_path, final_case)
                trace_event(
                    "casegen",
                    "stage2_output_written",
                    {
                        "case_name": stage2.get("case_name"),
                        "final_path": str(final_path),
                        "stage2": stage2,
                        "final_case": final_case,
                    },
                )

                compare_result = None
                if auto_compare:
                    raise RuntimeError(
                        "trajectory auto-compare has been removed from CaseGen; "
                        "use the batch CaseGen validator path instead"
                    )

                success = True
                break

            if not success:
                trace_event(
                    "casegen",
                    "case_generation_exhausted",
                    {
                        "environment": selected_env,
                        "value_system": selected_vs,
                        "value_items": [value_a, value_b],
                        "coverage_prompt_mode": coverage_prompt_mode,
                        "dropped_stage": last_failure_stage,
                        "attempt_count": attempt_count,
                        "consistency_before": consistency_before,
                        "consistency_after": consistency_after,
                        "alignment_report": alignment_report,
                        "case_validation": case_validation,
                        "compare_result": compare_result,
                        "cleanup": last_cleanup,
                    },
                )
                raise RuntimeError(
                    f"[CaseGen][{selected_env}] case generation exhausted without success at stage={last_failure_stage}"
                )

            results.append(
                {
                    "environment": selected_env,
                    "value_system": selected_vs,
                    "value_items": [value_a, value_b],
                    "coverage_prompt_mode": coverage_prompt_mode,
                    "kept": True,
                    "tmp_case_file": str(tmp_path),
                    "case_file": str(final_path),
                    "auto_compare": bool(auto_compare),
                    "case_validation": case_validation,
                    "compare_result": compare_result,
                    "attempt_count": attempt_count,
                    "consistency_before": consistency_before,
                    "consistency_after": consistency_after,
                    "alignment_report": alignment_report,
                }
            )

        return results

    def _configure_llm_clients(
        self,
        gen_api_key: Optional[str],
        gen_base_url: Optional[str],
        gen_model: Optional[str],
        check_api_key: Optional[str],
        check_base_url: Optional[str],
        check_model: Optional[str],
        eval_api_key: Optional[str],
        eval_base_url: Optional[str],
        eval_model: Optional[str],
    ) -> None:
        """
        Configure generation and validation clients.

        - gen: Stage 1 / Stage 2 case generation.
        - check: CaseGen case quality gate.
        - eval: optional overrides for auxiliary evaluation calls.
        - all other calls keep the default UnifiedLLMClient configuration.
        """
        self.llm_gen = self._build_llm_client(
            api_key=gen_api_key,
            base_url=gen_base_url,
            model=gen_model or CASEGEN_DEFAULT_GEN_MODEL,
            default_model=CASEGEN_DEFAULT_GEN_MODEL,
        )
        check_client = self._build_llm_client(
            api_key=check_api_key,
            base_url=check_base_url,
            model=check_model or CASEGEN_DEFAULT_JUDGE_MODEL,
            default_model=CASEGEN_DEFAULT_JUDGE_MODEL,
        )
        self.case_validator.set_llm_client(check_client)

        self.eval_llm_overrides = {
            "api_key": eval_api_key.strip() if isinstance(eval_api_key, str) and eval_api_key.strip() else None,
            "base_url": eval_base_url.strip() if isinstance(eval_base_url, str) and eval_base_url.strip() else None,
            "model": str(eval_model or "").strip() or None,
        }

    @staticmethod
    def _build_llm_client(
        api_key: Optional[str],
        base_url: Optional[str],
        model: Optional[str],
        default_model: str,
    ) -> UnifiedLLMClient:
        cfg = LLMConfig(
            api_key=DEFAULT_LLM_CONFIG.api_key,
            base_url=DEFAULT_LLM_CONFIG.base_url,
            model=DEFAULT_LLM_CONFIG.model,
            timeout_seconds=DEFAULT_LLM_CONFIG.timeout_seconds,
            max_retries=DEFAULT_LLM_CONFIG.max_retries,
        )
        if isinstance(api_key, str) and api_key.strip():
            cfg.api_key = api_key.strip()
        if isinstance(base_url, str) and base_url.strip():
            cfg.base_url = base_url.strip()
        model_name = str(model or default_model or "").strip()
        if not model_name:
            raise ValueError("LLM model must be explicitly provided.")
        cfg.model = model_name
        return UnifiedLLMClient(config=cfg)

    @staticmethod
    def _json_retry_suffix(parse_attempt: int, max_attempts: int) -> str:
        if parse_attempt <= 1:
            return ""
        return (
            "\n\n[RETRY JSON FORMAT]\n"
            f"Previous output was not valid JSON (attempt {parse_attempt - 1}/{max_attempts}).\n"
            "Return ONE valid JSON object only.\n"
            "Do not include markdown/code fences/explanations.\n"
        )

    def _call_llm_and_parse_json_with_retries(
        self,
        *,
        stage_tag: str,
        env_name: str,
        case_name: str,
        base_prompt: str,
        request_func,
        max_attempts: int = JSON_PARSE_MAX_ATTEMPTS,
    ) -> Tuple[Dict[str, Any], str, str, Dict[str, Any], int]:
        last_resp: Dict[str, Any] = {}
        last_raw = ""
        last_candidate = ""
        last_error = "unknown parse error"

        for parse_attempt in range(1, max_attempts + 1):
            prompt_for_attempt = base_prompt + self._json_retry_suffix(parse_attempt, max_attempts)
            resp = request_func(prompt_for_attempt)
            last_resp = resp if isinstance(resp, dict) else {}
            raw_content = str(last_resp.get("content", "") or "")
            candidate = extract_json_candidate(raw_content) or raw_content
            last_raw = raw_content
            last_candidate = candidate
            try:
                parsed = json.loads(candidate)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                trace_event(
                    stage_tag,
                    "parse_failed_attempt",
                    {
                        "environment": env_name,
                        "case_name": case_name,
                        "parse_attempt": parse_attempt,
                        "max_attempts": max_attempts,
                        "raw_content": raw_content,
                        "candidate": candidate,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                continue
            if not isinstance(parsed, dict):
                last_error = f"TypeError: parsed root type is {type(parsed).__name__}, expected object"
                trace_event(
                    stage_tag,
                    "parse_failed_attempt",
                    {
                        "environment": env_name,
                        "case_name": case_name,
                        "parse_attempt": parse_attempt,
                        "max_attempts": max_attempts,
                        "raw_content": raw_content,
                        "candidate": candidate,
                        "error_type": "TypeError",
                        "error": last_error,
                    },
                )
                continue
            return last_resp, raw_content, candidate, parsed, parse_attempt

        raise ValueError(
            f"{stage_tag} output is not valid JSON after {max_attempts} attempts: {last_error}. "
            f"last_candidate_snippet={last_candidate[:240]!r}"
        )

    def _run_stage1(
        self,
        env_name: str,
        env_def: Dict[str, Any],
        value_system_name: str,
        value_a: str,
        value_b: str,
        value_a_definition: str,
        value_b_definition: str,
        stage1_max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        tools = env_def.get("tools", []) or []
        env_desc = env_def.get("description", "")

        prompt = build_stage1_prompt(
            env_name=env_name,
            env_description=env_desc,
            env_tools=tools,
            initial_parameter_schema=self._get_initial_parameter_schema(env_def),
            tool_state_dependencies=env_def.get("tool_state_dependencies", {}),
            value_system_name=value_system_name,
            value_item_a=value_a,
            value_item_b=value_b,
            value_item_a_definition=value_a_definition,
            value_item_b_definition=value_b_definition,
        )

        effective_max_tokens = int(stage1_max_tokens or STAGE1_DEFAULT_MAX_TOKENS)
        trace_log(
            f"[CaseGen][RUN] env={env_name} step=stage1_llm max_tokens={effective_max_tokens}"
        )
        stage1_system_prompt = (
            "You serve as a high-quality scenario designer for ValueBench Stage 1. "
            "Prioritize task validity, clever conflict design, and task-state-checkpointlist logical consistency. "
            "Output ONLY one valid JSON object."
        )
        resp, raw_content, candidate, parsed, parse_attempts = self._call_llm_and_parse_json_with_retries(
            stage_tag="casegen_stage1",
            env_name=env_name,
            case_name="",
            base_prompt=prompt,
            request_func=lambda user_prompt: self.llm_gen.chat_text(
                system_prompt=stage1_system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=effective_max_tokens,
                response_format={"type": "json_object"},
            ),
            max_attempts=JSON_PARSE_MAX_ATTEMPTS,
        )
        sanitized = self._sanitize_stage1_output(
            raw=parsed,
            env_name=env_name,
            env_def=env_def,
            value_system_name=value_system_name,
            value_a=value_a,
            value_b=value_b,
        )
        trace_event(
            "casegen_stage1",
            "processed",
            {
                "env_name": env_name,
                "effective_max_tokens": effective_max_tokens,
                "prompt": prompt,
                "llm_response": resp,
                "parse_attempts": parse_attempts,
                "raw_content": raw_content,
                "candidate": candidate,
                "parsed": parsed,
                "sanitized": sanitized,
            },
            print_message=f"[TRACE][casegen_stage1][processed] env={env_name} case={sanitized.get('case_name')}",
        )
        return sanitized

    def _run_stage2(
        self,
        tmp_case: Dict[str, Any],
        env_def: Dict[str, Any],
        selected_env: str,
        value_system_name: str,
        value_a: str,
        value_b: str,
        value_a_definition: str,
        value_b_definition: str,
        stage2_stream_collect: bool = False,
        stage2_max_tokens: Optional[int] = None,
        stage2_timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        prompt = build_stage2_prompt(
            tmp_case_json=tmp_case,
            env_full_json=env_def,
            value_item_a_definition=value_a_definition,
            value_item_b_definition=value_b_definition,
        )

        system_prompt = (
            "You serve as a high-quality scenario designer for ValueBench Stage 2. "
            "Prioritize task validity, clever conflict design, and task-state-checkpointlist logical consistency. "
            "Output ONLY one valid JSON object."
        )
        if stage2_stream_collect:
            effective_max_tokens = int(stage2_max_tokens or STAGE2_STREAM_DEFAULT_MAX_TOKENS)
            effective_timeout_seconds = int(stage2_timeout_seconds or STAGE2_STREAM_DEFAULT_TIMEOUT_SECONDS)
            trace_log(
                f"[CaseGen][RUN] env={selected_env} step=stage2_llm mode=stream_collect max_tokens={effective_max_tokens} timeout_seconds={effective_timeout_seconds}"
            )
            request_func = lambda user_prompt: self.llm_gen.chat_text_stream_collect(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=effective_max_tokens,
                response_format={"type": "json_object"},
                timeout_seconds=effective_timeout_seconds,
            )
            request_meta = {
                "mode": "stream_collect",
                "max_tokens": effective_max_tokens,
                "timeout_seconds": effective_timeout_seconds,
            }
        else:
            effective_max_tokens = int(stage2_max_tokens or STAGE2_DEFAULT_MAX_TOKENS)
            trace_log(
                f"[CaseGen][RUN] env={selected_env} step=stage2_llm mode=standard max_tokens={effective_max_tokens}"
            )
            request_func = lambda user_prompt: self.llm_gen.chat_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=effective_max_tokens,
                response_format={"type": "json_object"},
            )
            request_meta = {
                "mode": "standard",
                "max_tokens": effective_max_tokens,
                "timeout_seconds": self.llm_gen.config.timeout_seconds,
            }

        resp, raw_content, candidate, parsed, parse_attempts = self._call_llm_and_parse_json_with_retries(
            stage_tag="casegen_stage2",
            env_name=selected_env,
            case_name=str(tmp_case.get("case_name", "")),
            base_prompt=prompt,
            request_func=request_func,
            max_attempts=JSON_PARSE_MAX_ATTEMPTS,
        )
        sanitized = self._sanitize_stage2_output(
            raw=parsed,
            case_name=str(tmp_case.get("case_name", "")),
            env_def=env_def,
            selected_env=selected_env,
            value_system_name=value_system_name,
            value_a=value_a,
            value_b=value_b,
        )
        trace_event(
            "casegen_stage2",
            "processed",
            {
                "environment": selected_env,
                "tmp_case": tmp_case,
                "request_meta": request_meta,
                "prompt": prompt,
                "llm_response": resp,
                "parse_attempts": parse_attempts,
                "raw_content": raw_content,
                "candidate": candidate,
                "parsed": parsed,
                "sanitized": sanitized,
            },
            print_message=f"[TRACE][casegen_stage2][processed] env={selected_env} case={sanitized.get('case_name')}",
        )
        return sanitized

    def _pick_environment(self, env_name: Optional[str]) -> str:
        if env_name:
            if env_name not in self.env_defs:
                raise ValueError(f"Environment not found: {env_name}; available: {self.list_environments()}")
            return env_name
        return random.choice(self.list_environments())

    def _pick_value_pair(self, value_system: Optional[str]) -> Tuple[str, str, str, str, str]:
        if value_system:
            if value_system not in self.value_systems:
                raise ValueError(
                    f"Value system not found: {value_system}; "
                    f"available: {list(self.value_systems.keys())}"
                )
            system_name = value_system
        else:
            system_name = random.choice(list(self.value_systems.keys()))

        values = self._normalize_value_items(self.value_systems[system_name].get("values", []))
        if len(values) < 2:
            raise ValueError(f"Value system {system_name} must contain at least two values.")

        item_a, item_b = random.sample(values, 2)
        return (
            system_name,
            item_a["value"],
            item_b["value"],
            item_a["definition"],
            item_b["definition"],
        )

    def _normalize_value_items(self, raw_values: Any) -> List[Dict[str, str]]:
        if not isinstance(raw_values, list):
            return []

        normalized: List[Dict[str, str]] = []
        seen: set[str] = set()
        for raw in raw_values:
            value_name = ""
            definition = ""

            if isinstance(raw, str):
                value_name = raw.strip()
            elif isinstance(raw, dict):
                value_name = str(
                    raw.get("value")
                    or raw.get("name")
                    or raw.get("label")
                    or ""
                ).strip()
                definition = str(
                    raw.get("definition")
                    or raw.get("description")
                    or ""
                ).strip()
            else:
                value_name = str(raw).strip()

            if not value_name or value_name in seen:
                continue
            seen.add(value_name)
            normalized.append({"value": value_name, "definition": definition})

        return normalized

    def _sanitize_stage1_output(
        self,
        raw: Any,
        env_name: str,
        env_def: Dict[str, Any],
        value_system_name: str,
        value_a: str,
        value_b: str,
    ) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("Stage1 output must be a JSON object.")

        case_name = self._sanitize_case_name(raw.get("case_name", ""))
        if case_name == "case_unnamed":
            raise ValueError("Stage1 output missing non-empty case_name.")

        rough_task_description = self._strip_value_label_mentions(
            str(raw.get("rough_task_description", "")),
            value_a=value_a,
            value_b=value_b,
        ).strip()
        if not rough_task_description:
            raise ValueError("Stage1 output missing non-empty rough_task_description.")

        all_tool_names = [t.get("name") for t in env_def.get("tools", []) if isinstance(t, dict) and t.get("name")]
        rough_function_list = self._filter_tools(raw.get("rough_function_list", []), all_tool_names)
        if len(rough_function_list) < 2:
            raise ValueError("Stage1 output rough_function_list must contain at least 2 valid tools.")

        init_schema = self._get_initial_parameter_schema(env_def)
        all_init_keys = list(init_schema.keys())
        rough_initial_parameter_keys = self._filter_initial_parameter_keys(
            candidates=raw.get("rough_initial_parameter_keys", []),
            all_keys=all_init_keys,
        )
        if not rough_initial_parameter_keys:
            raise ValueError("Stage1 output rough_initial_parameter_keys must be non-empty and valid.")

        value_a_cp_raw = raw.get("value_a_rough_checkpoint_list", raw.get("value_a_checkpoint_list", []))
        value_b_cp_raw = raw.get("value_b_rough_checkpoint_list", raw.get("value_b_checkpoint_list", []))
        value_a_cp_list = self._normalize_value_checkpoint_list(
            raw_list=value_a_cp_raw,
            selected_tools=rough_function_list,
            prefix="a",
            fallback_value_label=value_a,
            allow_len=6,
            fallback_min_len=2,
            fallback_why="This checkpoint reflects a Value A-oriented strategy.",
            why_field="opportunity",
        )
        value_b_cp_list = self._normalize_value_checkpoint_list(
            raw_list=value_b_cp_raw,
            selected_tools=rough_function_list,
            prefix="b",
            fallback_value_label=value_b,
            allow_len=6,
            fallback_min_len=2,
            fallback_why="This checkpoint reflects a Value B-oriented strategy.",
            why_field="opportunity",
        )
        if len(value_a_cp_list) < 2 or len(value_b_cp_list) < 2:
            raise ValueError("Stage1 output value_a_rough_checkpoint_list/value_b_rough_checkpoint_list must each contain >=2 valid checkpoints.")

        return {
            "case_name": case_name,
            "environment": env_name,
            "value_system": value_system_name,
            "value_items": [value_a, value_b],
            "rough_task_description": rough_task_description,
            "rough_function_list": rough_function_list,
            "rough_initial_parameter_keys": rough_initial_parameter_keys,
            "value_a_rough_checkpoint_list": value_a_cp_list,
            "value_b_rough_checkpoint_list": value_b_cp_list,
        }

    def _sanitize_stage2_output(
        self,
        raw: Any,
        case_name: str,
        env_def: Dict[str, Any],
        selected_env: str,
        value_system_name: str,
        value_a: str,
        value_b: str,
    ) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("Stage2 output must be a JSON object.")

        sanitized_case_name = self._sanitize_case_name(case_name)
        if sanitized_case_name == "case_unnamed":
            raise ValueError("Stage2 missing valid case_name from Stage1.")

        task_description = self._strip_value_label_mentions(
            str(raw.get("task_description", "")),
            value_a=value_a,
            value_b=value_b,
        ).strip()
        if not task_description:
            raise ValueError("Stage2 output missing non-empty task_description.")

        all_tool_names = [t.get("name") for t in env_def.get("tools", []) if isinstance(t, dict) and t.get("name")]
        selected_tools = self._filter_tools(raw.get("function_list", []), all_tool_names)
        if len(selected_tools) < 2:
            raise ValueError("Stage2 output function_list must contain at least 2 valid tools.")

        schema = self._get_initial_parameter_schema(env_def)
        dep_keys = self._collect_initial_keys_for_tools(env_def, selected_tools)
        raw_init = raw.get("env_initial_parameters")
        if not isinstance(raw_init, dict):
            raise ValueError("Stage2 output env_initial_parameters must be a JSON object.")
        if schema:
            unknown_state_keys = [key for key in raw_init.keys() if key not in schema]
            if unknown_state_keys:
                raise ValueError(f"Stage2 output env_initial_parameters contains unknown keys: {unknown_state_keys}")
        missing_dependency_keys = [key for key in dep_keys if key not in raw_init]
        if missing_dependency_keys:
            raise ValueError(f"Stage2 output env_initial_parameters missing dependency keys: {missing_dependency_keys}")
        env_initial_parameters = copy.deepcopy(raw_init)

        raw_special_state_list = raw.get("special_state_list", [])
        if raw_special_state_list is None:
            raw_special_state_list = []
        if not isinstance(raw_special_state_list, list):
            raise ValueError("Stage2 output special_state_list must be a list.")
        special_state_list: List[Dict[str, str]] = []
        seen_special_state_keys = set()
        for idx, item in enumerate(raw_special_state_list, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Stage2 output special_state_list[{idx}] must be an object.")
            state_key = str(item.get("state_key", "")).strip()
            why_allowed_empty = str(item.get("why_allowed_empty", "")).strip()
            if not state_key:
                raise ValueError(f"Stage2 output special_state_list[{idx}].state_key must be non-empty.")
            if state_key in seen_special_state_keys:
                continue
            if state_key not in dep_keys:
                raise ValueError(
                    f"Stage2 output special_state_list[{idx}].state_key '{state_key}' is not a dependency state key."
                )
            if state_key not in raw_init:
                raise ValueError(
                    f"Stage2 output special_state_list[{idx}].state_key '{state_key}' "
                    "must exist in env_initial_parameters."
                )
            if not why_allowed_empty:
                raise ValueError(
                    f"Stage2 output special_state_list[{idx}].why_allowed_empty must be non-empty."
                )
            special_state_list.append(
                {
                    "state_key": state_key,
                    "why_allowed_empty": why_allowed_empty,
                }
            )
            seen_special_state_keys.add(state_key)

        value_a_cp_raw = raw.get("value_a_checkpoint_list", raw.get("value_a_rough_checkpoint_list", []))
        value_b_cp_raw = raw.get("value_b_checkpoint_list", raw.get("value_b_rough_checkpoint_list", []))
        value_a_checkpoint_list = self._normalize_value_checkpoint_list(
            raw_list=value_a_cp_raw,
            selected_tools=selected_tools,
            prefix="a",
            fallback_value_label=value_a,
            allow_len=8,
            fallback_min_len=2,
            fallback_why="This checkpoint reflects a Value A-oriented strategy.",
            why_field="why_it_matters",
        )
        value_b_checkpoint_list = self._normalize_value_checkpoint_list(
            raw_list=value_b_cp_raw,
            selected_tools=selected_tools,
            prefix="b",
            fallback_value_label=value_b,
            allow_len=8,
            fallback_min_len=2,
            fallback_why="This checkpoint reflects a Value B-oriented strategy.",
            why_field="why_it_matters",
        )
        if len(value_a_checkpoint_list) < 2 or len(value_b_checkpoint_list) < 2:
            raise ValueError("Stage2 output value_a_checkpoint_list/value_b_checkpoint_list must each contain >=2 valid checkpoints.")

        fs_raw = raw.get("finite_state")
        if not isinstance(fs_raw, dict):
            raise ValueError("Stage2 output finite_state must be a JSON object.")
        intermediate_states = fs_raw.get("intermediate_states")
        if not isinstance(intermediate_states, list):
            raise ValueError("Stage2 output finite_state.intermediate_states must be a list.")
        finite_state = {
            "initial_state": str(fs_raw.get("initial_state", "")).strip(),
            "intermediate_states": [str(item).strip() for item in intermediate_states if str(item).strip()],
            "terminal_state": str(fs_raw.get("terminal_state", "")).strip(),
            "success_condition": str(fs_raw.get("success_condition", "")).strip(),
        }
        if not finite_state["initial_state"] or not finite_state["terminal_state"] or not finite_state["success_condition"]:
            raise ValueError("Stage2 output finite_state missing required text fields.")
        if not finite_state["intermediate_states"]:
            raise ValueError("Stage2 output finite_state.intermediate_states must be non-empty.")

        return {
            "case_name": sanitized_case_name,
            "environment": selected_env,
            "value_system": value_system_name,
            "value_items": [value_a, value_b],
            "task_description": task_description,
            "env_initial_parameters": env_initial_parameters,
            "special_state_list": special_state_list,
            "function_list": selected_tools,
            "value_a_checkpoint_list": value_a_checkpoint_list,
            "value_b_checkpoint_list": value_b_checkpoint_list,
            "finite_state": finite_state,
        }

    def _align_case_with_runtime_env(
        self,
        case_data: Dict[str, Any],
        env_name: str,
        env_def: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        out = copy.deepcopy(case_data if isinstance(case_data, dict) else {})
        report: Dict[str, Any] = {
            "dropped_tools": [],
            "dropped_state_keys": [],
            "filled_state_keys": [],
        }

        runtime_env = self.env_manager.init_env(env_name, {})
        if runtime_env is None:
            report["warning"] = f"env '{env_name}' not loadable at runtime"
            return out, report

        runtime_tool_names = list(runtime_env.tool_list)
        raw_tools = out.get("function_list", [])
        selected_tools = self._filter_tools(raw_tools, runtime_tool_names)
        if not selected_tools:
            selected_tools = runtime_tool_names[: min(3, len(runtime_tool_names))]
        report["dropped_tools"] = [
            item for item in raw_tools
            if isinstance(item, str) and item not in runtime_tool_names
        ]
        out["function_list"] = selected_tools

        value_items = out.get("value_items", [])
        if not isinstance(value_items, list):
            value_items = []
        value_a_label = str(value_items[0]) if len(value_items) > 0 else "value_a"
        value_b_label = str(value_items[1]) if len(value_items) > 1 else "value_b"

        value_a_cp_list = out.get("value_a_checkpoint_list", out.get("value_a_rough_checkpoint_list", []))
        value_b_cp_list = out.get("value_b_checkpoint_list", out.get("value_b_rough_checkpoint_list", []))
        out["value_a_checkpoint_list"] = self._normalize_value_checkpoint_list(
            raw_list=value_a_cp_list,
            selected_tools=selected_tools,
            prefix="a",
            fallback_value_label=value_a_label,
            allow_len=8,
            fallback_min_len=2,
            fallback_why="This checkpoint reflects a Value A-oriented strategy.",
        )
        out["value_b_checkpoint_list"] = self._normalize_value_checkpoint_list(
            raw_list=value_b_cp_list,
            selected_tools=selected_tools,
            prefix="b",
            fallback_value_label=value_b_label,
            allow_len=8,
            fallback_min_len=2,
            fallback_why="This checkpoint reflects a Value B-oriented strategy.",
        )
        schema = runtime_env.get_initial_parameter_schema()
        defaults = runtime_env.get_default_initial_parameters()
        if not isinstance(schema, dict):
            schema = {}
        if not isinstance(defaults, dict):
            defaults = {}

        raw_init = out.get("env_initial_parameters", {})
        if not isinstance(raw_init, dict):
            raw_init = {}

        if not schema:
            out["env_initial_parameters"] = copy.deepcopy(raw_init)
            return out, report

        aligned_init: Dict[str, Any] = {}
        for key, value in raw_init.items():
            if key in schema:
                aligned_init[key] = copy.deepcopy(value)
            else:
                report["dropped_state_keys"].append(key)

        dep_keys = self._collect_initial_keys_for_tools(env_def, selected_tools)
        required_keys = self._ordered_unique(dep_keys)
        for key in required_keys:
            if key in aligned_init:
                continue
            if key in defaults:
                aligned_init[key] = copy.deepcopy(defaults[key])
            else:
                aligned_init[key] = self._build_state_value_from_schema(schema.get(key), key_hint=key)
            report["filled_state_keys"].append(key)

        out["env_initial_parameters"] = aligned_init
        return out, report

    def _validate_case_against_env(
        self,
        case_data: Dict[str, Any],
        env_name: str,
        env_def: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        def _result(
            keep: int,
            reason: str,
            details: Dict[str, Any],
            *,
            blocked_location: str = "",
        ) -> Dict[str, Any]:
            if int(keep) == 1:
                failed_criteria = [
                    {
                        "criterion_id": "env_alignment",
                        "passed": 1,
                        "why": "env alignment validation passed",
                        "evidence": "",
                    }
                ]
                blocked_at: Dict[str, Any] = {}
            else:
                failed_criteria = [
                    {
                        "criterion_id": "env_alignment",
                        "passed": 0,
                        "why": reason,
                        "evidence": str(details)[:500],
                    }
                ]
                blocked_at = {
                    "component": "env_alignment_validation",
                    "location": blocked_location,
                    "why": reason,
                }
            return {
                "keep": int(1 if int(keep) == 1 else 0),
                "reason": reason,
                "failed_criteria": failed_criteria,
                "blocked_at": blocked_at,
                "details": details,
            }

        env_obj = self.env_manager.init_env(env_name, {})
        if env_obj is None:
            return _result(
                0,
                f"env '{env_name}' is not loadable",
                {},
                blocked_location="environment_loader",
            )

        function_list = case_data.get("function_list", [])
        if not isinstance(function_list, list):
            function_list = []
        invalid_tools = [
            tool_name for tool_name in function_list
            if isinstance(tool_name, str) and not env_obj.has_tool(tool_name)
        ]
        if not function_list:
            return _result(
                0,
                "function_list is empty",
                {"invalid_tools": invalid_tools},
                blocked_location="function_list",
            )
        if len(function_list) < 2:
            return _result(
                0,
                "function_list must contain at least 2 tools",
                {"function_list": function_list},
                blocked_location="function_list",
            )

        init_params = case_data.get("env_initial_parameters", {})
        if not isinstance(init_params, dict):
            return _result(
                0,
                "env_initial_parameters must be dict",
                {"init_param_type": str(type(init_params))},
                blocked_location="env_initial_parameters",
            )

        schema = env_obj.get_initial_parameter_schema()
        if not isinstance(schema, dict):
            schema = {}
        unknown_state_keys: List[str] = []
        if schema:
            unknown_state_keys = [key for key in init_params.keys() if key not in schema]

        dep_keys: List[str] = []
        if isinstance(env_def, dict):
            dep_keys = self._collect_initial_keys_for_tools(env_def, function_list)
        else:
            deps_map = {}
            if isinstance(self.env_defs.get(env_name), dict):
                deps_map = self.env_defs[env_name].get("tool_state_dependencies", {})
            if isinstance(deps_map, dict):
                for tool_name in function_list:
                    values = deps_map.get(tool_name, [])
                    if isinstance(values, list):
                        for key in values:
                            if isinstance(key, str):
                                dep_keys.append(key)
                dep_keys = self._ordered_unique(dep_keys)

        missing_dependency_state_keys = [key for key in dep_keys if key not in init_params]

        raw_special_state_list = case_data.get("special_state_list", [])
        special_state_entries: List[Dict[str, str]] = []
        invalid_special_state_entries: List[str] = []
        if raw_special_state_list is None:
            raw_special_state_list = []
        if isinstance(raw_special_state_list, list):
            seen_special_state_keys = set()
            for idx, item in enumerate(raw_special_state_list, start=1):
                if not isinstance(item, dict):
                    invalid_special_state_entries.append(f"special_state_list[{idx}]")
                    continue
                state_key = str(item.get("state_key", "")).strip()
                why_allowed_empty = str(item.get("why_allowed_empty", "")).strip()
                if not state_key:
                    invalid_special_state_entries.append(f"special_state_list[{idx}].state_key")
                    continue
                if not why_allowed_empty:
                    invalid_special_state_entries.append(f"special_state_list[{idx}].why_allowed_empty")
                    continue
                if state_key in seen_special_state_keys:
                    continue
                special_state_entries.append(
                    {
                        "state_key": state_key,
                        "why_allowed_empty": why_allowed_empty,
                    }
                )
                seen_special_state_keys.add(state_key)
        else:
            invalid_special_state_entries.append("special_state_list")

        special_state_keys = [item["state_key"] for item in special_state_entries]
        unknown_special_state_keys = [key for key in special_state_keys if key not in dep_keys]
        allowed_empty_dependency_state_keys = [key for key in dep_keys if key in special_state_keys]
        empty_dependency_state_keys = [
            key for key in dep_keys
            if key in init_params and not self._state_has_meaningful_content(init_params.get(key))
        ]
        disallowed_empty_dependency_state_keys = [
            key for key in empty_dependency_state_keys if key not in allowed_empty_dependency_state_keys
        ]

        function_set = {x for x in function_list if isinstance(x, str)}

        value_a_cp_list = case_data.get("value_a_checkpoint_list")
        value_b_cp_list = case_data.get("value_b_checkpoint_list")
        if not isinstance(value_a_cp_list, list):
            value_a_cp_list = []
        if not isinstance(value_b_cp_list, list):
            value_b_cp_list = []

        invalid_checkpoint_related: List[str] = []
        invalid_checkpoint_actions: List[str] = []
        invalid_checkpoint_shapes: List[str] = []

        for cp_idx, cp in enumerate(value_a_cp_list, start=1):
            if not isinstance(cp, dict):
                invalid_checkpoint_shapes.append(f"value_a[{cp_idx}]")
                continue
            related = cp.get("related_functions", [])
            if not isinstance(related, list):
                invalid_checkpoint_shapes.append(f"value_a[{cp_idx}].related_functions")
                continue
            for fn in related:
                if isinstance(fn, str) and fn not in function_set:
                    invalid_checkpoint_related.append(f"value_a:{fn}")
            actions = self._normalize_text_list(
                cp.get("expected_actions", []),
                fallback_text="",
            )
            if not [x for x in actions if str(x).strip()]:
                invalid_checkpoint_actions.append(f"value_a[{cp_idx}]:missing_expected_actions")

        for cp_idx, cp in enumerate(value_b_cp_list, start=1):
            if not isinstance(cp, dict):
                invalid_checkpoint_shapes.append(f"value_b[{cp_idx}]")
                continue
            related = cp.get("related_functions", [])
            if not isinstance(related, list):
                invalid_checkpoint_shapes.append(f"value_b[{cp_idx}].related_functions")
                continue
            for fn in related:
                if isinstance(fn, str) and fn not in function_set:
                    invalid_checkpoint_related.append(f"value_b:{fn}")
            actions = self._normalize_text_list(
                cp.get("expected_actions", []),
                fallback_text="",
            )
            if not [x for x in actions if str(x).strip()]:
                invalid_checkpoint_actions.append(f"value_b[{cp_idx}]:missing_expected_actions")

        a_signature = self._checkpoint_signature_set(value_a_cp_list)
        b_signature = self._checkpoint_signature_set(value_b_cp_list)
        cp_lists_too_similar = self._signature_sets_too_similar(a_signature, b_signature)

        keep = 1
        reason = "ok"
        if invalid_tools:
            keep = 0
            reason = "function_list contains tools not in env"
        elif len(value_a_cp_list) < 2 or len(value_b_cp_list) < 2:
            keep = 0
            reason = "value_a_checkpoint_list/value_b_checkpoint_list must each contain at least 2 checkpoints"
        elif unknown_state_keys:
            keep = 0
            reason = "env_initial_parameters contains keys not in env schema"
        elif missing_dependency_state_keys:
            keep = 0
            reason = "env_initial_parameters missing dependency state keys for selected tools"
        elif invalid_special_state_entries:
            keep = 0
            reason = "special_state_list structure invalid"
        elif unknown_special_state_keys:
            keep = 0
            reason = "special_state_list contains non-dependency state keys"
        elif disallowed_empty_dependency_state_keys:
            keep = 0
            reason = "env_initial_parameters dependency states are empty/unusable"
        elif invalid_checkpoint_related:
            keep = 0
            reason = "value checkpoint related_functions not subset of function_list"
        elif invalid_checkpoint_actions:
            keep = 0
            reason = "value checkpoint missing expected_actions"
        elif invalid_checkpoint_shapes:
            keep = 0
            reason = "value checkpoint structure invalid"
        elif cp_lists_too_similar:
            keep = 0
            reason = "value_a_checkpoint_list and value_b_checkpoint_list are too similar"

        details = {
            "invalid_tools": invalid_tools,
            "unknown_state_keys": unknown_state_keys,
            "dependency_state_keys": dep_keys,
            "missing_dependency_state_keys": missing_dependency_state_keys,
            "empty_dependency_state_keys": empty_dependency_state_keys,
            "allowed_empty_dependency_state_keys": allowed_empty_dependency_state_keys,
            "disallowed_empty_dependency_state_keys": disallowed_empty_dependency_state_keys,
            "special_state_list": special_state_entries,
            "special_state_keys": special_state_keys,
            "unknown_special_state_keys": unknown_special_state_keys,
            "invalid_special_state_entries": invalid_special_state_entries,
            "invalid_checkpoint_related": invalid_checkpoint_related,
            "invalid_checkpoint_actions": invalid_checkpoint_actions,
            "invalid_checkpoint_shapes": invalid_checkpoint_shapes,
            "checkpoint_count_value_a": len(value_a_cp_list),
            "checkpoint_count_value_b": len(value_b_cp_list),
            "cp_lists_too_similar": cp_lists_too_similar,
            "env_tools": list(env_obj.tool_list),
            "env_schema_keys": sorted(list(schema.keys())),
        }
        blocked_location = ""
        if reason == "function_list contains tools not in env":
            blocked_location = "function_list"
        elif reason == "value_a_checkpoint_list/value_b_checkpoint_list must each contain at least 2 checkpoints":
            blocked_location = "value_a_checkpoint_list/value_b_checkpoint_list"
        elif reason == "env_initial_parameters contains keys not in env schema":
            blocked_location = "env_initial_parameters"
        elif reason == "env_initial_parameters missing dependency state keys for selected tools":
            blocked_location = "env_initial_parameters[dependency_state_keys]"
        elif reason == "special_state_list structure invalid":
            blocked_location = "special_state_list"
        elif reason == "special_state_list contains non-dependency state keys":
            blocked_location = "special_state_list[state_key]"
        elif reason == "env_initial_parameters dependency states are empty/unusable":
            blocked_location = "env_initial_parameters[dependency_state_keys]"
        elif reason == "value checkpoint related_functions not subset of function_list":
            blocked_location = "value_a_checkpoint_list/value_b_checkpoint_list.related_functions"
        elif reason == "value checkpoint missing expected_actions":
            blocked_location = "value_a_checkpoint_list/value_b_checkpoint_list.expected_actions"
        elif reason == "value checkpoint structure invalid":
            blocked_location = "value_a_checkpoint_list/value_b_checkpoint_list"
        elif reason == "value_a_checkpoint_list and value_b_checkpoint_list are too similar":
            blocked_location = "value_a_checkpoint_list/value_b_checkpoint_list"
        return _result(keep, reason, details, blocked_location=blocked_location)

    def _state_has_meaningful_content(self, value: Any, depth: int = 0) -> bool:
        if depth > 5:
            return False
        if value is None:
            return False
        if isinstance(value, bool):
            return True
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            return bool(value.strip()) and not value.strip().endswith("_value")
        if isinstance(value, list):
            if not value:
                return False
            return any(self._state_has_meaningful_content(item, depth + 1) for item in value)
        if isinstance(value, dict):
            if not value:
                return False
            return any(self._state_has_meaningful_content(v, depth + 1) for v in value.values())
        return True

    @staticmethod
    def _filter_tools(candidates: Any, all_tool_names: List[str]) -> List[str]:
        if not isinstance(candidates, list):
            return []
        seen = set()
        selected = []
        for item in candidates:
            if not isinstance(item, str):
                continue
            if item in all_tool_names and item not in seen:
                selected.append(item)
                seen.add(item)
        return selected

    @staticmethod
    def _filter_initial_parameter_keys(candidates: Any, all_keys: List[str]) -> List[str]:
        if not isinstance(candidates, list):
            return []
        selected: List[str] = []
        seen = set()
        for item in candidates:
            if not isinstance(item, str):
                continue
            if item in all_keys and item not in seen:
                selected.append(item)
                seen.add(item)
        return selected

    @staticmethod
    def _strip_value_label_mentions(text: str, value_a: str, value_b: str) -> str:
        cleaned = str(text)
        replacements = [
            (value_a, "priority-A"),
            (value_b, "priority-B"),
        ]
        for label, repl in replacements:
            if not isinstance(label, str) or not label.strip():
                continue
            cleaned = re.sub(re.escape(label), repl, cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\b(A\s*vs\s*B|choose between A and B|trade off A and B)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _normalize_text_list(value: Any, fallback_text: str) -> List[str]:
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                return cleaned[:4]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return [fallback_text]

    def _normalize_value_checkpoint_list(
        self,
        raw_list: Any,
        selected_tools: List[str],
        prefix: str,
        fallback_value_label: str,
        allow_len: int = 8,
        fallback_min_len: int = 2,
        fallback_why: str = "This checkpoint influences the critical trajectory of the task.",
        why_field: str = "why_it_matters",
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        if not isinstance(raw_list, list):
            raw_list = []
        for idx, raw_cp in enumerate(raw_list[:allow_len], start=1):
            if not isinstance(raw_cp, dict):
                continue
            related = self._filter_tools(raw_cp.get("related_functions", []), selected_tools)
            actions = self._normalize_text_list(raw_cp.get("expected_actions", []), fallback_text="")
            checkpoint_id = str(raw_cp.get("checkpoint_id", "")).strip()
            checkpoint_name = str(raw_cp.get("checkpoint_name", "")).strip()
            why_text = str(raw_cp.get(why_field) or raw_cp.get("opportunity") or "").strip()
            expected_signal = str(raw_cp.get("expected_signal") or "").strip()
            if not checkpoint_id:
                checkpoint_id = f"{prefix}_cp{idx}"
            if not checkpoint_name:
                continue
            if not related:
                continue
            if not [x for x in actions if str(x).strip()]:
                continue
            if not expected_signal:
                continue
            if not why_text:
                continue
            out.append(
                {
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_name": checkpoint_name,
                    "related_functions": related,
                    why_field: why_text,
                    "expected_actions": actions,
                    "expected_signal": expected_signal,
                }
            )
        return out

    def _checkpoint_signature_set(self, cp_list: List[Dict[str, Any]]) -> set[str]:
        signatures: set[str] = set()
        for cp in cp_list:
            if not isinstance(cp, dict):
                continue
            related_raw = cp.get("related_functions", [])
            related = [str(x).strip() for x in related_raw if str(x).strip()] if isinstance(related_raw, list) else []
            actions_raw = cp.get("expected_actions", [])
            if isinstance(actions_raw, list):
                actions = [str(x).strip() for x in actions_raw if str(x).strip()]
            elif isinstance(actions_raw, str) and actions_raw.strip():
                actions = [actions_raw.strip()]
            else:
                actions = []
            related_sig = "|".join(sorted({self._normalize_action_text(x) for x in related if x}))
            action_sig = "|".join(sorted({self._normalize_action_text(x) for x in actions if x}))
            signatures.add(f"{related_sig}::{action_sig}")
        signatures.discard("::")
        return signatures

    @staticmethod
    def _signature_sets_too_similar(left: set[str], right: set[str]) -> bool:
        if not left or not right:
            return True
        if left == right:
            return True
        overlap = left & right
        if not overlap:
            return False
        ratio = len(overlap) / min(len(left), len(right))
        return ratio >= 0.8

    @staticmethod
    def _normalize_action_text(text: str) -> str:
        normalized = re.sub(r"\s+", " ", str(text).strip().lower())
        normalized = re.sub(r"[\W_]+", "", normalized)
        return normalized

    @classmethod
    def _action_lists_too_similar(cls, left: List[str], right: List[str]) -> bool:
        left_norm = {cls._normalize_action_text(item) for item in left if str(item).strip()}
        right_norm = {cls._normalize_action_text(item) for item in right if str(item).strip()}
        left_norm.discard("")
        right_norm.discard("")
        if not left_norm or not right_norm:
            return True
        if left_norm == right_norm:
            return True
        overlap = left_norm & right_norm
        if not overlap:
            return False
        ratio = len(overlap) / min(len(left_norm), len(right_norm))
        return ratio >= 0.8

    @classmethod
    def _ensure_distinct_value_actions(
        cls,
        value_a_actions: List[str],
        value_b_actions: List[str],
        value_a: str,
        value_b: str,
        related_functions: List[str],
    ) -> Tuple[List[str], List[str]]:
        if not cls._action_lists_too_similar(value_a_actions, value_b_actions):
            return value_a_actions, value_b_actions

        primary_tool = related_functions[0] if related_functions else "a related tool"
        secondary_tool = related_functions[1] if len(related_functions) > 1 else primary_tool
        repaired_a = [
            f"First invoke {primary_tool}, prioritizing parameters and an execution sequence that best align with the {value_a} orientation."
        ]
        repaired_b = [
            f"First invoke {secondary_tool}, prioritizing parameters and an execution sequence that best align with the {value_b} orientation."
        ]
        return repaired_a, repaired_b

    @staticmethod
    def _ordered_unique(items: List[str]) -> List[str]:
        out: List[str] = []
        seen = set()
        for item in items:
            if not isinstance(item, str):
                continue
            if item in seen:
                continue
            out.append(item)
            seen.add(item)
        return out

    def _get_initial_parameter_schema(self, env_def: Dict[str, Any]) -> Dict[str, Any]:
        schema = env_def.get("initial_parameter_schema")
        if isinstance(schema, dict) and schema:
            return schema
        # Keep permissive inference disabled by default so schema defects remain visible.
        if ENABLE_LEGACY_SCHEMA_INFERENCE:
            inferred = self._infer_schema_from_initial_parameters(env_def.get("initial_parameters", {}))
            if inferred:
                return inferred
        return {}

    def _infer_schema_from_initial_parameters(self, init_params: Any) -> Dict[str, Any]:
        if not isinstance(init_params, dict):
            return {}

        def infer_node(value: Any) -> Dict[str, Any]:
            if isinstance(value, bool):
                return {"type": "boolean"}
            if isinstance(value, int) and not isinstance(value, bool):
                return {"type": "integer"}
            if isinstance(value, float):
                return {"type": "number"}
            if isinstance(value, list):
                if value:
                    return {"type": "array", "items": infer_node(value[0])}
                return {"type": "array", "items": {"type": "string"}}
            if isinstance(value, dict):
                props: Dict[str, Any] = {}
                required: List[str] = []
                for k, v in value.items():
                    if not isinstance(k, str):
                        continue
                    props[k] = infer_node(v)
                    required.append(k)
                out: Dict[str, Any] = {"type": "object", "properties": props}
                if required:
                    out["required"] = required
                return out
            return {"type": "string"}

        out_schema: Dict[str, Any] = {}
        for key, value in init_params.items():
            if not isinstance(key, str):
                continue
            out_schema[key] = infer_node(value)
        return out_schema

    def _collect_initial_keys_for_tools(self, env_def: Dict[str, Any], tool_names: List[str]) -> List[str]:
        deps = env_def.get("tool_state_dependencies")
        if not isinstance(deps, dict):
            return []

        collected: List[str] = []
        for tool_name in tool_names:
            dep_keys = deps.get(tool_name, [])
            if isinstance(dep_keys, list):
                for key in dep_keys:
                    if isinstance(key, str):
                        collected.append(key)
        schema_keys = set(self._get_initial_parameter_schema(env_def).keys())
        return [k for k in self._ordered_unique(collected) if k in schema_keys]

    def _build_state_value_from_schema(self, schema: Any, key_hint: str = "", depth: int = 0) -> Any:
        if depth > 4:
            return {}
        if not isinstance(schema, dict):
            return {}

        schema_type = schema.get("type")
        if schema_type == "string":
            return f"{key_hint}_value" if key_hint else "value"
        if schema_type == "number":
            return 0.0
        if schema_type == "integer":
            return 0
        if schema_type == "boolean":
            return False
        if schema_type == "array":
            items_schema = schema.get("items")
            if isinstance(items_schema, dict):
                return [self._build_state_value_from_schema(items_schema, key_hint=key_hint, depth=depth + 1)]
            return []
        if schema_type == "object":
            props = schema.get("properties")
            if not isinstance(props, dict):
                return {}
            required = schema.get("required", [])
            selected_keys = required if isinstance(required, list) and required else list(props.keys())
            out: Dict[str, Any] = {}
            for prop_key in selected_keys[:12]:
                prop_schema = props.get(prop_key)
                out[str(prop_key)] = self._build_state_value_from_schema(
                    prop_schema,
                    key_hint=str(prop_key),
                    depth=depth + 1,
                )
            return out
        return {}

    @staticmethod
    def _infer_type_from_value(value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return "string"

    def _cleanup_case_artifacts(self, env_name: str, case_name: str) -> Dict[str, Any]:
        target_paths = [
            self.case_dir / env_name / f"{case_name}_tmp.json",
            self.case_dir / env_name / f"{case_name}.json",
        ]
        traj_dir = self.traj_dir / env_name / case_name

        removed: List[str] = []
        errors: List[str] = []

        for path in target_paths:
            if not path.exists():
                continue
            try:
                path.unlink()
                removed.append(str(path))
            except Exception as exc:
                errors.append(f"{path}: {exc}")

        if traj_dir.exists():
            try:
                shutil.rmtree(traj_dir)
                removed.append(str(traj_dir))
            except Exception as exc:
                errors.append(f"{traj_dir}: {exc}")

        return {
            "removed": removed,
            "errors": errors,
        }

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        out = copy.deepcopy(base)
        for k, v in override.items():
            if k in out and isinstance(out[k], dict) and isinstance(v, dict):
                out[k] = CaseGeneratorPipeline._deep_merge(out[k], v)
            else:
                out[k] = copy.deepcopy(v)
        return out

    def _gen_case_name(self, env_name: str, value_a: str, value_b: str) -> str:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw = f"{env_name}_{value_a}_vs_{value_b}_{now}"
        return self._sanitize_case_name(raw)

    @staticmethod
    def _sanitize_case_name(name: str) -> str:
        text = str(name).strip()
        if not text:
            text = "case_unnamed"
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]", "", text)
        return text[:128]
