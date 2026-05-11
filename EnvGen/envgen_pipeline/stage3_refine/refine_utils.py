"""Utility functions for the simplified Stage3-REFINE pipeline.

The pipeline keeps only core helpers for:
- metric calculation
- baseline failure mining (bug ledger)
- AST-safe function replacement
- compact diff rendering
"""

from __future__ import annotations

import ast
import difflib
import json
import textwrap
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from utils.process_file import convert_for_save


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def calc_metrics_from_summary(summary: Dict[str, Any]) -> Dict[str, float]:
    """Calculate quality metrics from rollout summary."""
    total = _safe_float(summary.get("total_count", 0))
    if total <= 0:
        return {
            "total_count": 0,
            "pass_count": 0,
            "warning_count": 0,
            "fail_count": 0,
            "pass_acc": 0.0,
            "not_fail_acc": 0.0,
            "positive_pass_acc": 0.0,
            "positive_not_fail_acc": 0.0,
            "negative_pass_acc": 0.0,
            "negative_not_fail_acc": 0.0,
        }

    pass_count = _safe_float(summary.get("pass_count", 0))
    warning_count = _safe_float(summary.get("warning_count", 0))
    fail_count = _safe_float(summary.get("fail_count", 0))

    positive_total = _safe_float(summary.get("positive_count", 0))
    positive_pass = _safe_float(summary.get("positive_pass_count", 0))
    positive_not_fail = _safe_float(summary.get("positive_pass_count", 0)) + _safe_float(
        summary.get("positive_warning_count", 0)
    )

    negative_total = _safe_float(summary.get("negative_count", 0))
    negative_pass = _safe_float(summary.get("negative_pass_count", 0))
    negative_not_fail = _safe_float(summary.get("negative_pass_count", 0)) + _safe_float(
        summary.get("negative_warning_count", 0)
    )

    return {
        "total_count": int(total),
        "pass_count": int(pass_count),
        "warning_count": int(warning_count),
        "fail_count": int(fail_count),
        "pass_acc": round(pass_count / total, 4),
        "not_fail_acc": round((pass_count + warning_count) / total, 4),
        "positive_pass_acc": round(positive_pass / positive_total, 4) if positive_total > 0 else 0.0,
        "positive_not_fail_acc": round(positive_not_fail / positive_total, 4) if positive_total > 0 else 0.0,
        "negative_pass_acc": round(negative_pass / negative_total, 4) if negative_total > 0 else 0.0,
        "negative_not_fail_acc": round(negative_not_fail / negative_total, 4) if negative_total > 0 else 0.0,
    }


def calc_metrics_from_item(env_item: Dict[str, Any]) -> Dict[str, float]:
    """Calculate metrics from env item with func_test_result."""
    summary = env_item.get("func_test_result", {}).get("func_test_cases", {}).get("summary", {})
    return calc_metrics_from_summary(summary)


def metrics_meet_thresholds(
    metrics: Dict[str, Any],
    threshold: float,
    positive_pass_threshold: float,
) -> bool:
    """Check whether an env meets both robustness and positive-path thresholds."""
    return (
        float(metrics.get("not_fail_acc", 0.0)) >= threshold
        and float(metrics.get("positive_pass_acc", 0.0)) >= positive_pass_threshold
    )


def ensure_eval_init_config(env_item: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure env item has deterministic eval_init_config."""
    new_item = deepcopy(env_item)
    init_config_list = new_item.get("init_config_list", [])
    if not init_config_list:
        init_config_list = [{}]
    new_item["init_config_list"] = init_config_list
    if "eval_init_config" not in new_item:
        new_item["eval_init_config"] = init_config_list[0]
    return new_item


def _collect_case_text(case: Dict[str, Any]) -> str:
    observation = case.get("observation", {})
    check_reason = str(case.get("check_reason", ""))
    check_result = case.get("check_result", {})
    if isinstance(check_result, dict):
        check_reason = check_reason or str(check_result.get("error_reason", ""))

    err = ""
    if isinstance(observation, dict):
        err = str(observation.get("error", ""))

    return f"{err} {check_reason}".strip().lower()


def classify_failure_case(case: Dict[str, Any]) -> List[str]:
    """Classify one failure case into coarse root-cause categories."""
    text = _collect_case_text(case)
    types: List[str] = []

    if "<exception>" in text or "traceback" in text or "exception" in text:
        types.append("runtime_exception")

    if any(k in text for k in ["import", "module", "cannot import", "has no attribute", "dependency"]):
        types.append("import_or_dependency_conflict")

    if any(
        k in text
        for k in [
            "missing validation",
            "invalid id",
            "not found",
            "invalid parameter",
            "wrong type",
            "type mismatch",
            "boundary",
            "parameter",
        ]
    ):
        types.append("parameter_validation_or_boundary_gap")

    if any(k in text for k in ["state", "state_diff", "not updated", "unexpected change", "inconsistent"]):
        types.append("state_update_inconsistency")

    if any(k in text for k in ["constraint", "rule", "violate", "invariant"]):
        types.append("constraint_violation")

    if any(k in text for k in ["missing success", "return protocol", "return value must be dict"]):
        types.append("return_protocol_instability")

    case_type = str(case.get("case_type", "")).lower().strip()
    if case_type == "negative" and any(k in text for k in ["not found", "missing", "id"]):
        types.append("init_config_induced_failure")

    if not types:
        types.append("unknown_logic_error")
    return sorted(set(types))


def _extract_case_snapshot(case: Dict[str, Any], idx: int, failure_types: List[str]) -> Dict[str, Any]:
    return {
        "case_idx": idx,
        "step": case.get("step"),
        "case_type": case.get("case_type"),
        "status": case.get("status"),
        "failure_types": failure_types,
        "parameters": case.get("parameters", {}),
        "observation": case.get("observation", {}),
        "state_before_call": case.get("state_before_call", {}),
        "state_after_call": case.get("state_after_call", {}),
        "state_diff": case.get("state_diff", {}),
        "check_reason": case.get("check_reason", ""),
        "check_result": case.get("check_result", {}),
    }


def _default_fix_suggestion(failure_type: str) -> str:
    mapping = {
        "runtime_exception": "Wrap risky branches with safe error return and avoid raising exceptions.",
        "import_or_dependency_conflict": "Resolve import alias conflicts and dependency usage mismatch.",
        "parameter_validation_or_boundary_gap": "Add strict input validation and boundary checks before state access.",
        "state_update_inconsistency": "Align state write paths with constraints and expected state_diff.",
        "constraint_violation": "Enforce constraints_rules before and after state modifications.",
        "return_protocol_instability": "Always return dict with success and data/message/error fields.",
        "init_config_induced_failure": "Repair entity/reference coverage in init_config or add defensive existence checks.",
        "unknown_logic_error": "Inspect failing cases and add guarded logic for uncovered paths.",
    }
    return mapping.get(failure_type, "Review failed cases and apply minimal safe patch.")


def build_bug_ledger(
    env_item: Dict[str, Any],
    top_n: int = 5,
    max_cases_per_func: int = 5,
) -> Dict[str, Any]:
    """Mine rollout results and build root-cause bug ledger."""
    details = env_item.get("func_test_result", {}).get("func_test_cases", {}).get("details", {})
    if not isinstance(details, dict):
        details = {}

    rankings: List[Dict[str, Any]] = []
    for func_name, info in details.items():
        if not isinstance(info, dict):
            continue

        summary = info.get("summary", {}) if isinstance(info.get("summary", {}), dict) else {}
        total = int(summary.get("total_count", 0) or 0)
        fail_count = int(summary.get("fail_count", 0) or 0)
        warning_count = int(summary.get("warning_count", 0) or 0)
        fail_rate = round((fail_count / total), 4) if total > 0 else 0.0

        cases = info.get("cases", []) if isinstance(info.get("cases", []), list) else []
        failing_cases = [c for c in cases if str(c.get("status", "")).lower().strip() in ("fail", "warning")]

        failure_type_counts: Dict[str, int] = {}
        case_snapshots: List[Dict[str, Any]] = []
        suggested_fix = ""

        for idx, case in enumerate(failing_cases):
            if not isinstance(case, dict):
                continue
            failure_types = classify_failure_case(case)
            for ftype in failure_types:
                failure_type_counts[ftype] = failure_type_counts.get(ftype, 0) + 1

            if len(case_snapshots) < max_cases_per_func:
                case_snapshots.append(_extract_case_snapshot(case, idx, failure_types))

            if not suggested_fix:
                suggested_fix = str(case.get("check_reason") or "").strip()

        if not suggested_fix and failure_type_counts:
            major_type = sorted(failure_type_counts.items(), key=lambda kv: kv[1], reverse=True)[0][0]
            suggested_fix = _default_fix_suggestion(major_type)
        if not suggested_fix:
            suggested_fix = "No explicit failures found for this function."

        severity = 0
        if failure_type_counts.get("runtime_exception", 0) > 0:
            severity = 3
        elif fail_count > 0:
            severity = 2
        elif warning_count > 0:
            severity = 1

        impact = fail_count
        rank_score = round(impact * 10 + severity * 5 + fail_rate * 100, 4)
        rankings.append(
            {
                "function_name": func_name,
                "total_count": total,
                "fail_count": fail_count,
                "warning_count": warning_count,
                "fail_rate": fail_rate,
                "impact": impact,
                "severity": severity,
                "rank_score": rank_score,
                "failure_type_counts": failure_type_counts,
                "top_failing_cases": case_snapshots,
                "suggested_fix": suggested_fix,
            }
        )

    rankings.sort(key=lambda x: (x["rank_score"], x["impact"], x["severity"]), reverse=True)
    repair_targets = [item for item in rankings if int(item.get("fail_count", 0)) > 0][:top_n]
    return {
        "top_n": top_n,
        "function_rankings": rankings,
        "repair_targets": repair_targets,
    }


def extract_method_source(
    env_class_code: str,
    class_name: str,
    method_name: str,
) -> str:
    """Extract method source from class code."""
    try:
        tree = ast.parse(env_class_code)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == method_name:
                        return ast.unparse(item)
    except Exception:
        return ""
    return ""


def _parse_function_def(func_source: str) -> Optional[ast.FunctionDef]:
    try:
        code = textwrap.dedent(func_source or "").strip()
        if not code:
            return None
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node
    except Exception:
        return None
    return None


def replace_class_methods(
    env_class_code: str,
    class_name: str,
    new_method_sources: Dict[str, str],
) -> str:
    """Replace selected methods in target class using AST-safe replacement."""
    try:
        tree = ast.parse(env_class_code)
    except Exception:
        return env_class_code

    parsed_methods: Dict[str, ast.FunctionDef] = {}
    for name, src in new_method_sources.items():
        fn = _parse_function_def(src)
        if fn:
            parsed_methods[name] = fn

    if not parsed_methods:
        return env_class_code

    changed = False
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for i, child in enumerate(node.body):
                if isinstance(child, ast.FunctionDef) and child.name in parsed_methods:
                    node.body[i] = parsed_methods[child.name]
                    changed = True

    if not changed:
        return env_class_code

    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def summarize_diff(old_text: str, new_text: str, max_lines: int = 160) -> str:
    """Build compact unified diff summary."""
    diff = list(
        difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile="before.py",
            tofile="after.py",
            lineterm="",
        )
    )
    if not diff:
        return ""
    if len(diff) > max_lines:
        diff = diff[:max_lines] + ["... (truncated)"]
    return "\n".join(diff)


def to_pretty_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except TypeError:
        return json.dumps(convert_for_save(data), ensure_ascii=False, indent=2)
