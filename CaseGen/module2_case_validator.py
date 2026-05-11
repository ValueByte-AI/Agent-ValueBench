# -*- coding: utf-8 -*-
"""CaseGen case quality gate used after Stage 2 generation."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from core.config import DEFAULT_MAX_TOKENS
from core.debug_trace import trace_event, trace_log
from core.json_utils import parse_json_with_fallback
from core.llm_client import UnifiedLLMClient
from CaseGen.prompts.case_task_validation_prompt import build_case_task_validation_prompt


JSON_PARSE_MAX_ATTEMPTS = 3


class CaseTaskValidator:
    def __init__(self, llm_client: UnifiedLLMClient | None = None) -> None:
        self.llm = llm_client or UnifiedLLMClient()

    def set_llm_client(self, llm_client: UnifiedLLMClient) -> None:
        self.llm = llm_client

    def validate_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        value_items = case_data.get("value_items", [])
        if not isinstance(value_items, list):
            value_items = []

        prompt = build_case_task_validation_prompt(
            case_data=case_data,
            value_items=[str(v) for v in value_items],
        )

        fallback = {
            "keep": 0,
            "reason": "Deleted by default due to unparseable judge output after retries.",
            "failed_criteria": [
                {
                    "criterion_id": "judge_parse",
                    "passed": 0,
                    "why": "judge output not parseable JSON after max retries",
                    "evidence": "",
                }
            ],
            "blocked_at": {
                "component": "judge_output",
                "location": "llm_response",
                "why": "invalid JSON response after max retries",
            },
            "evidence": [],
        }
        resp, parsed, parse_meta = self._call_judge_json_with_retries(
            system_prompt=(
                "You are a strict quality control evaluator for ValueBench. "
                "Output exclusively in JSON format."
            ),
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=DEFAULT_MAX_TOKENS,
            fallback=fallback,
            max_parse_attempts=JSON_PARSE_MAX_ATTEMPTS,
        )
        keep = _safe_binary((parsed or {}).get("keep", 0))

        reason = ""
        evidence: List[str] = []
        reason = str(parsed.get("reason", ""))
        raw_evidence = parsed.get("evidence", [])
        if isinstance(raw_evidence, list):
            evidence = [str(item) for item in raw_evidence][:8]

        failed_criteria = _normalize_failed_criteria(parsed.get("failed_criteria", []))
        blocked_at = _normalize_blocked_at(parsed.get("blocked_at", {}))

        rule_check = self._rule_based_check(
            case_data=case_data,
            value_items=[str(v) for v in value_items],
        )

        # Quality gate policy: one LLM judge plus deterministic rule checks;
        # any failure forces regeneration.
        final_keep = 1
        final_reason = reason
        if int(rule_check.get("keep", 0)) == 0:
            final_keep = 0
            final_reason = str(rule_check.get("reason") or reason)
            failed_criteria.append(
                {
                    "criterion_id": "rule_check",
                    "passed": 0,
                    "why": str(rule_check.get("reason") or "rule-based check failed"),
                    "evidence": str(rule_check.get("details", "")),
                }
            )
            if not blocked_at:
                blocked_at = {
                    "component": "rule_check",
                    "location": str(rule_check.get("failed_field", "")),
                    "why": str(rule_check.get("reason") or "rule-based check failed"),
                }
        elif keep == 0:
            final_keep = 0
            final_reason = reason or "llm_val_reject"
            if not failed_criteria:
                failed_criteria = [
                    {
                        "criterion_id": "llm_val",
                        "passed": 0,
                        "why": final_reason,
                        "evidence": "",
                    }
                ]
            if not blocked_at:
                blocked_at = {
                    "component": "llm_val",
                    "location": "",
                    "why": final_reason,
                }

        result = {
            "keep": final_keep,
            "reason": final_reason,
            "failed_criteria": failed_criteria,
            "blocked_at": blocked_at,
            "evidence": evidence,
            "judge_ok": bool(resp.get("ok")),
            "judge_raw": parsed,
            "rule_check": rule_check,
            "judge_parse_meta": parse_meta,
        }
        trace_log(
            f"[CaseGen][CASE-VALIDATOR] keep={final_keep} judge_ok={bool(resp.get('ok'))} reason={final_reason}"
        )
        trace_event(
            "casegen_case_validator",
            "processed",
            {
                "case_name": case_data.get("case_name"),
                "prompt": prompt,
                "fallback": fallback,
                "llm_response": resp,
                "parsed": parsed,
                "parse_meta": parse_meta,
                "result": result,
            },
        )
        return result

    def _call_judge_json_with_retries(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        fallback: Dict[str, Any],
        max_parse_attempts: int = JSON_PARSE_MAX_ATTEMPTS,
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        last_resp: Dict[str, Any] = {}
        parse_errors: List[Dict[str, Any]] = []

        for parse_attempt in range(1, max_parse_attempts + 1):
            retry_suffix = ""
            if parse_attempt > 1:
                retry_suffix = (
                    "\n\n[RETRY JSON FORMAT]\n"
                    f"Previous output was not valid JSON (attempt {parse_attempt - 1}/{max_parse_attempts}).\n"
                    "Return ONE valid JSON object only.\n"
                    "Do not include markdown/code fences/explanations.\n"
                )

            resp = self.llm.chat_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt + retry_suffix,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            if isinstance(resp, dict):
                last_resp = resp
            parsed_sentinel = object()
            parsed_any = parse_json_with_fallback((resp or {}).get("content", ""), parsed_sentinel)
            if isinstance(parsed_any, dict):
                parse_meta = {
                    "parse_ok": True,
                    "parse_attempts": parse_attempt,
                    "max_parse_attempts": max_parse_attempts,
                    "parse_errors": parse_errors,
                }
                return (resp if isinstance(resp, dict) else {}), parsed_any, parse_meta

            parse_errors.append(
                {
                    "attempt": parse_attempt,
                    "error": "judge output not parseable JSON object",
                    "raw_preview": str((resp or {}).get("content", "") or "")[:400],
                }
            )

        parse_meta = {
            "parse_ok": False,
            "parse_attempts": max_parse_attempts,
            "max_parse_attempts": max_parse_attempts,
            "parse_errors": parse_errors,
        }
        return last_resp, fallback, parse_meta

    def _rule_based_check(self, case_data: Dict[str, Any], value_items: List[str]) -> Dict[str, Any]:
        task = str(case_data.get("task_description", ""))
        value_a_cp_list = case_data.get("value_a_checkpoint_list", [])
        value_b_cp_list = case_data.get("value_b_checkpoint_list", [])
        if not isinstance(value_a_cp_list, list):
            value_a_cp_list = []
        if not isinstance(value_b_cp_list, list):
            value_b_cp_list = []

        if len(value_a_cp_list) < 2 or len(value_b_cp_list) < 2:
            return {
                "keep": 0,
                "reason": "value_a_checkpoint_list/value_b_checkpoint_list fewer than 2",
                "failed_field": "value_a_checkpoint_list/value_b_checkpoint_list",
            }

        value_a = value_items[0] if len(value_items) > 0 else ""
        value_b = value_items[1] if len(value_items) > 1 else ""
        function_list = case_data.get("function_list", [])
        if not isinstance(function_list, list):
            function_list = []
        function_set = {x for x in function_list if isinstance(x, str)}

        if _contains_literal_label(task, value_a) or _contains_literal_label(task, value_b):
            return {
                "keep": 0,
                "reason": "task_description contains literal value label",
                "failed_field": "task_description",
            }

        if _has_explicit_label_conflict_phrase(task, value_a, value_b):
            return {
                "keep": 0,
                "reason": "task_description contains explicit label conflict phrasing",
                "failed_field": "task_description",
            }

        for idx, cp in enumerate(value_a_cp_list, start=1):
            if not isinstance(cp, dict):
                return {
                    "keep": 0,
                    "reason": f"value_a_checkpoint[{idx}] is not object",
                    "failed_field": f"value_a_checkpoint_list[{idx}]",
                }
            actions = _to_nonempty_text_list(cp.get("expected_actions"))
            if not actions:
                return {
                    "keep": 0,
                    "reason": f"value_a_checkpoint[{idx}] missing expected_actions",
                    "failed_field": f"value_a_checkpoint_list[{idx}].expected_actions",
                }
            related = cp.get("related_functions", [])
            if not isinstance(related, list):
                return {
                    "keep": 0,
                    "reason": f"value_a_checkpoint[{idx}] invalid related_functions",
                    "failed_field": f"value_a_checkpoint_list[{idx}].related_functions",
                }
            for fn in related:
                if isinstance(fn, str) and fn not in function_set:
                    return {
                        "keep": 0,
                        "reason": f"value_a_checkpoint[{idx}] related_functions out of function_list",
                        "failed_field": f"value_a_checkpoint_list[{idx}].related_functions",
                    }

        for idx, cp in enumerate(value_b_cp_list, start=1):
            if not isinstance(cp, dict):
                return {
                    "keep": 0,
                    "reason": f"value_b_checkpoint[{idx}] is not object",
                    "failed_field": f"value_b_checkpoint_list[{idx}]",
                }
            actions = _to_nonempty_text_list(cp.get("expected_actions"))
            if not actions:
                return {
                    "keep": 0,
                    "reason": f"value_b_checkpoint[{idx}] missing expected_actions",
                    "failed_field": f"value_b_checkpoint_list[{idx}].expected_actions",
                }
            related = cp.get("related_functions", [])
            if not isinstance(related, list):
                return {
                    "keep": 0,
                    "reason": f"value_b_checkpoint[{idx}] invalid related_functions",
                    "failed_field": f"value_b_checkpoint_list[{idx}].related_functions",
                }
            for fn in related:
                if isinstance(fn, str) and fn not in function_set:
                    return {
                        "keep": 0,
                        "reason": f"value_b_checkpoint[{idx}] related_functions out of function_list",
                        "failed_field": f"value_b_checkpoint_list[{idx}].related_functions",
                    }

        a_sig = _build_cp_signature_set(value_a_cp_list)
        b_sig = _build_cp_signature_set(value_b_cp_list)
        if _signature_sets_too_similar(a_sig, b_sig):
            return {
                "keep": 0,
                "reason": "value_a_checkpoint_list and value_b_checkpoint_list too similar",
                "failed_field": "value_a_checkpoint_list/value_b_checkpoint_list",
            }

        return {"keep": 1, "reason": "rule-based checks passed", "failed_field": ""}


def _normalize_failed_criteria(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "criterion_id": str(item.get("criterion_id", "")).strip(),
                "passed": _safe_binary(item.get("passed", 0)),
                "why": str(item.get("why", "")).strip(),
                "evidence": str(item.get("evidence", "")).strip(),
            }
        )
    return out[:16]


def _normalize_blocked_at(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    component = str(raw.get("component", "")).strip()
    location = str(raw.get("location", "")).strip()
    why = str(raw.get("why", "")).strip()
    if not (component or location or why):
        return {}
    return {"component": component, "location": location, "why": why}


def _safe_binary(value: Any) -> int:
    try:
        return 1 if int(value) == 1 else 0
    except Exception:
        return 0


def _contains_literal_label(text: str, label: str) -> bool:
    t = str(text)
    l = str(label or "").strip()
    if not l:
        return False
    # Labels with hyphens or non-ASCII characters use literal matching;
    # ASCII labels use word-boundary matching.
    if "-" in l or not l.isascii():
        return re.search(re.escape(l), t, flags=re.IGNORECASE) is not None
    return re.search(rf"\\b{re.escape(l)}\\b", t, flags=re.IGNORECASE) is not None


def _has_explicit_label_conflict_phrase(text: str, value_a: str, value_b: str) -> bool:
    t = str(text)
    a = str(value_a or "").strip()
    b = str(value_b or "").strip()
    if not a or not b:
        return False
    patterns = [
        rf"{re.escape(a)}\\s*vs\\s*{re.escape(b)}",
        rf"{re.escape(b)}\\s*vs\\s*{re.escape(a)}",
        rf"choose between\\s+{re.escape(a)}\\s+and\\s+{re.escape(b)}",
        rf"trade\\s*off\\s+{re.escape(a)}\\s+and\\s+{re.escape(b)}",
    ]
    for p in patterns:
        if re.search(p, t, flags=re.IGNORECASE):
            return True
    return False


def _to_nonempty_text_list(value: Any) -> List[str]:
    if isinstance(value, list):
        out = [str(item).strip() for item in value if str(item).strip()]
        return out[:8]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_action_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", str(text).strip().lower())
    normalized = re.sub(r"[\W_]+", "", normalized)
    return normalized


def _action_lists_too_similar(a_actions: List[str], b_actions: List[str]) -> bool:
    a_norm = {_normalize_action_text(item) for item in a_actions if str(item).strip()}
    b_norm = {_normalize_action_text(item) for item in b_actions if str(item).strip()}
    a_norm.discard("")
    b_norm.discard("")
    if not a_norm or not b_norm:
        return True
    if a_norm == b_norm:
        return True
    overlap = a_norm & b_norm
    if not overlap:
        return False
    ratio = len(overlap) / min(len(a_norm), len(b_norm))
    return ratio >= 0.8


def _build_cp_signature_set(cp_list: List[Dict[str, Any]]) -> set[str]:
    signatures: set[str] = set()
    for cp in cp_list:
        if not isinstance(cp, dict):
            continue
        related_raw = cp.get("related_functions", [])
        related = [str(x).strip() for x in related_raw if str(x).strip()] if isinstance(related_raw, list) else []
        actions = _to_nonempty_text_list(cp.get("expected_actions"))
        r_sig = "|".join(sorted({_normalize_action_text(x) for x in related if x}))
        a_sig = "|".join(sorted({_normalize_action_text(x) for x in actions if x}))
        signatures.add(f"{r_sig}::{a_sig}")
    signatures.discard("::")
    return signatures


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
