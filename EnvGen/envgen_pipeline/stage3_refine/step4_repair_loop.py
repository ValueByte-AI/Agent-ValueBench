"""Stage3-REFINE Step4: simple LLM-centric repair loop.

Core loop:
1) Mine failure information from bug ledger.
2) Ask agentic LLM to patch top failing functions.
3) Apply AST-safe replacement.
4) Re-evaluate and keep best revision.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import textwrap
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage2_env_synthesis.step3_program_synthesis import (
    analyze_env_item,
    check_ast,
    check_returns,
)
from stage3_refine.refine_utils import (
    build_bug_ledger,
    calc_metrics_from_item,
    ensure_eval_init_config,
    extract_method_source,
    metrics_meet_thresholds,
    replace_class_methods,
    summarize_diff,
    to_pretty_json,
)
from stage3_refine.step2_baseline_roll_check import run_rollout_for_env_item
from utils.call_llm import llm_inference
from utils.process_file import read_file, save_file
from utils.recovery import RecoverableAPIError, RecoverableStepError
from utils.resumable import run_sequential_step


REPAIR_RESUME_FIELD = "__repair_resume_state__"


def _is_above_threshold(
    metrics: Dict[str, Any],
    threshold: float,
    positive_pass_threshold: float,
) -> bool:
    return metrics_meet_thresholds(metrics, threshold, positive_pass_threshold)


def _is_static_valid(env_class_code: str) -> Tuple[bool, str]:
    if not check_ast(env_class_code):
        return False, "AST parse failed"
    ret_checks = check_returns(env_class_code, strict=True)
    has_fail = any(status == "FAIL" for _, _, status, _ in ret_checks)
    if has_fail:
        return False, "check_returns(strict=True) has FAIL entries"
    return True, "ok"


def _extract_target_functions(env_item: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
    ledger = env_item.get("bug_ledger") or build_bug_ledger(env_item, top_n=top_n)
    targets = ledger.get("repair_targets", [])[:top_n]
    return [target for target in targets if int(target.get("fail_count", 0)) > 0]


def _parse_function_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    if "```python" in text:
        text = text.split("```python", 1)[1].split("```", 1)[0]
    code = text.strip()
    if not code:
        return None
    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return ast.unparse(node)
    except Exception:
        return None
    match = re.search(r"(def\s+[a-zA-Z_]\w*\s*\(.*)", code, flags=re.S)
    if match:
        return match.group(1).strip()
    return None


def _same_signature(old_func_src: str, new_func_src: str) -> bool:
    def _norm(src: str) -> str:
        return textwrap.dedent(src or "").strip()

    def _sig(src: str) -> Optional[Tuple[str, Tuple[str, ...]]]:
        try:
            node = ast.parse(_norm(src)).body[0]
            if not isinstance(node, ast.FunctionDef):
                return None
            args = [a.arg for a in node.args.args]
            return (node.name, tuple(args))
        except Exception:
            return None

    old_sig = _sig(old_func_src)
    new_sig = _sig(new_func_src)
    return old_sig is not None and old_sig == new_sig


def _build_fallback_safe_patch(old_func_src: str) -> Optional[str]:
    """Generic fallback patch when LLM output is unavailable.

    Wraps original body with try/except and returns controlled error dict.
    This is generic safety hardening, not case-specific hardcoding.
    """
    try:
        node = ast.parse(textwrap.dedent(old_func_src or "").strip()).body[0]
        if not isinstance(node, ast.FunctionDef):
            return None

        doc_stmt = None
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            doc_stmt = body[0]
            body = body[1:]

        except_stmt = ast.parse(
            f"return {{'success': False, 'error': 'Exception in {node.name}: ' + str(e)}}"
        ).body[0]

        wrapped = ast.Try(
            body=body if body else [ast.parse("return {'success': True, 'message': 'noop'}").body[0]],
            handlers=[ast.ExceptHandler(type=ast.Name(id='Exception', ctx=ast.Load()), name='e', body=[except_stmt])],
            orelse=[],
            finalbody=[],
        )
        node.body = [doc_stmt, wrapped] if doc_stmt is not None else [wrapped]
        ast.fix_missing_locations(node)
        return ast.unparse(node)
    except Exception:
        return None


def _llm_patch_function(
    env_item: Dict[str, Any],
    target: Dict[str, Any],
    model: str,
    temperature: float,
) -> Optional[str]:
    func_name = target.get("function_name")
    old_func_src = (
        env_item.get("env_func_details", {})
        .get(func_name, {})
        .get("source_code", "")
    )
    if not old_func_src:
        old_func_src = extract_method_source(
            env_item["env_class_code"],
            env_item["env_class_name"],
            func_name,
        )
    if not old_func_src:
        return None

    fail_cases = target.get("top_failing_cases", [])[:3]
    prompt = f"""
You are an agentic debugging engineer patching one Python class method.

Hard constraints:
1) Keep the exact same function signature.
2) Never raise exceptions to caller.
3) Query success uses {{ "success": True, "data": ... }}.
4) Modify success uses {{ "success": True, "message": ... }}.
5) Error path uses {{ "success": False, "error": ... }}.
6) Respect constraints_rules.
7) Fix based on provided failing cases.

Environment Introduction:
{env_item.get("environment_introduction", "")}

Constraints Rules:
{to_pretty_json(env_item.get("constraints_rules", []))}

Class Definition:
{env_item.get("env_class_def", "")}

Function Name:
{func_name}

Original Function Source:
```python
{old_func_src}
```

Top Failing Cases:
{to_pretty_json(fail_cases)}

Checker Suggestions:
{target.get("suggested_fix", "")}

Return only the fixed function in python markdown.
"""
    response = llm_inference(
        provider="openai",
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        raise_on_failure=True,
    )
    patched_func = _parse_function_from_text(response or "")
    if patched_func and _same_signature(old_func_src, patched_func):
        return patched_func

    # Fallback: generic safety patch to avoid raw runtime failures.
    fallback = _build_fallback_safe_patch(old_func_src)
    if fallback and _same_signature(old_func_src, fallback):
        return fallback
    return None


def _apply_llm_patches(
    env_item: Dict[str, Any],
    targets: List[Dict[str, Any]],
    enable_llm_patch: bool,
    llm_model: str,
    llm_temperature: float,
) -> Tuple[str, List[Dict[str, Any]]]:
    env_class_code = env_item["env_class_code"]
    class_name = env_item["env_class_name"]
    patch_actions: List[Dict[str, Any]] = []

    # C) optional LLM surgical patch
    if enable_llm_patch:
        replacements = {}
        for target in targets:
            patched_func = _llm_patch_function(
                env_item=env_item,
                target=target,
                model=llm_model,
                temperature=llm_temperature,
            )
            if patched_func:
                replacements[target["function_name"]] = patched_func
                patch_actions.append(
                    {
                        "type": "llm_surgical_patch",
                        "changed": True,
                        "functions": [target["function_name"]],
                    }
                )
            else:
                patch_actions.append(
                    {
                        "type": "llm_surgical_patch",
                        "changed": False,
                        "functions": [target["function_name"]],
                    }
                )
        if replacements:
            env_class_code = replace_class_methods(
                env_class_code=env_class_code,
                class_name=class_name,
                new_method_sources=replacements,
            )
    return env_class_code, patch_actions


def _merge_analysis_fields(base_item: Dict[str, Any], analyzed_item: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(analyzed_item)
    for field in ["init_config_list", "eval_init_config", "bug_ledger", "baseline_metrics"]:
        if field in base_item:
            merged[field] = deepcopy(base_item[field])
    return merged


def _is_better_metrics(new_metrics: Dict[str, Any], old_metrics: Dict[str, Any]) -> bool:
    n_not_fail = float(new_metrics.get("not_fail_acc", 0))
    o_not_fail = float(old_metrics.get("not_fail_acc", 0))
    if n_not_fail > o_not_fail:
        return True
    if n_not_fail < o_not_fail:
        return False
    n_positive_pass = float(new_metrics.get("positive_pass_acc", 0))
    o_positive_pass = float(old_metrics.get("positive_pass_acc", 0))
    if n_positive_pass > o_positive_pass:
        return True
    if n_positive_pass < o_positive_pass:
        return False
    n_pass = float(new_metrics.get("pass_acc", 0))
    o_pass = float(old_metrics.get("pass_acc", 0))
    return n_pass > o_pass


def _collect_changed_functions_from_actions(patch_actions: List[Dict[str, Any]]) -> List[str]:
    funcs: List[str] = []
    for action in patch_actions:
        if action.get("changed"):
            funcs.extend(action.get("functions", []))
    return sorted(set(funcs))


def repair_one_env(env_item: Dict[str, Any], args) -> Dict[str, Any]:
    env_item = ensure_eval_init_config(env_item)
    resume_state = env_item.get(REPAIR_RESUME_FIELD) if isinstance(env_item, dict) else None
    if isinstance(resume_state, dict):
        current_item = deepcopy(resume_state.get("current_item", env_item))
        best_item = deepcopy(resume_state.get("best_item", env_item))
        best_metrics = deepcopy(resume_state.get("best_metrics", calc_metrics_from_item(best_item)))
        repair_audit = deepcopy(resume_state.get("repair_audit", env_item.get("repair_audit", {})))
        if not repair_audit:
            original_metrics = calc_metrics_from_item(env_item)
            repair_audit = {
                "environment_summary": env_item.get("environment_summary", ""),
                "threshold": args.threshold,
                "positive_pass_threshold": args.positive_pass_threshold,
                "original_metrics": original_metrics,
                "iterations": [],
                "patched_functions": [],
                "final_metrics": original_metrics,
                "reached_threshold": False,
            }
        start_round = int(resume_state.get("next_round", 1))
    else:
        current_item = deepcopy(env_item)
        best_item = deepcopy(env_item)
        original_metrics = calc_metrics_from_item(env_item)
        best_metrics = deepcopy(original_metrics)
        repair_audit = {
            "environment_summary": env_item.get("environment_summary", ""),
            "threshold": args.threshold,
            "positive_pass_threshold": args.positive_pass_threshold,
            "original_metrics": original_metrics,
            "iterations": [],
            "patched_functions": [],
            "final_metrics": original_metrics,
            "reached_threshold": _is_above_threshold(
                original_metrics,
                args.threshold,
                args.positive_pass_threshold,
            ),
        }
        start_round = 1

    if repair_audit["reached_threshold"]:
        best_item["final_metrics"] = best_metrics
        best_item["repair_status"] = "accepted"
        best_item["repair_audit"] = repair_audit
        best_item.pop(REPAIR_RESUME_FIELD, None)
        return best_item

    for round_idx in range(start_round, args.max_repair_rounds + 1):
        current_item["bug_ledger"] = build_bug_ledger(current_item, top_n=args.top_n)
        targets = _extract_target_functions(current_item, top_n=args.top_n)
        if not targets:
            repair_audit["iterations"].append(
                {"round": round_idx, "status": "no_targets", "message": "No failing function targets found."}
            )
            break

        old_code = current_item["env_class_code"]
        try:
            patched_code, patch_actions = _apply_llm_patches(
                env_item=current_item,
                targets=targets,
                enable_llm_patch=args.enable_llm_patch,
                llm_model=args.llm_patch_model,
                llm_temperature=args.llm_patch_temperature,
            )
        except RecoverableAPIError as exc:
            raise _build_repair_pause(
                current_item=current_item,
                best_item=best_item,
                best_metrics=best_metrics,
                repair_audit=repair_audit,
                round_idx=round_idx,
                error=exc,
            ) from exc

        iteration = {
            "round": round_idx,
            "status": "patched",
            "targets": [t["function_name"] for t in targets],
            "patch_actions": patch_actions,
            "diff_summary": summarize_diff(old_code, patched_code, max_lines=140),
        }

        if patched_code == old_code:
            iteration["status"] = "no_code_change"
            repair_audit["iterations"].append(iteration)
            continue

        static_ok, static_msg = _is_static_valid(patched_code)
        iteration["static_check"] = {"ok": static_ok, "msg": static_msg}
        if not static_ok:
            iteration["status"] = "static_failed"
            repair_audit["iterations"].append(iteration)
            continue

        candidate = deepcopy(current_item)
        candidate["env_class_code"] = patched_code
        try:
            analyzed = analyze_env_item(candidate)
            candidate = _merge_analysis_fields(candidate, analyzed)
        except Exception as exc:
            iteration["status"] = "analyze_failed"
            iteration["analyze_error"] = str(exc)
            repair_audit["iterations"].append(iteration)
            continue

        try:
            full_eval = run_rollout_for_env_item(
                env_item=candidate,
                model=args.eval_model,
                temperature=args.eval_temperature,
                max_steps=args.eval_steps,
                agent_mode=args.agent_mode,
            )
        except RecoverableStepError as exc:
            raise _build_repair_pause(
                current_item=current_item,
                best_item=best_item,
                best_metrics=best_metrics,
                repair_audit=repair_audit,
                round_idx=round_idx,
                error=exc.error,
            ) from exc
        full_metrics = calc_metrics_from_item(full_eval)
        iteration["full_metrics"] = full_metrics

        if _is_better_metrics(full_metrics, best_metrics):
            iteration["status"] = "accepted_improvement"
            best_item = deepcopy(full_eval)
            best_metrics = deepcopy(full_metrics)
            best_item["bug_ledger"] = build_bug_ledger(best_item, top_n=args.top_n)
            current_item = deepcopy(best_item)
            repaired_funcs = _collect_changed_functions_from_actions(patch_actions)
            repair_audit["patched_functions"] = sorted(
                set(repair_audit["patched_functions"] + repaired_funcs)
            )
        else:
            iteration["status"] = "rejected_not_better"

        repair_audit["iterations"].append(iteration)
        if _is_above_threshold(best_metrics, args.threshold, args.positive_pass_threshold):
            break

    reached = _is_above_threshold(best_metrics, args.threshold, args.positive_pass_threshold)
    repair_audit["reached_threshold"] = reached
    repair_audit["final_metrics"] = best_metrics

    best_item["final_metrics"] = best_metrics
    best_item["repair_status"] = "accepted" if reached else "repair_queue"
    best_item["repair_audit"] = repair_audit
    best_item.pop(REPAIR_RESUME_FIELD, None)
    return best_item


def main(args):
    data = read_file(args.read_file_path)
    run_sequential_step(
        items=data,
        output_path=args.save_file_path,
        key_fn=lambda item: item.get("__dispatch_index__", item.get("task", item.get("environment_summary", ""))),
        is_complete_fn=lambda item: isinstance(item, dict) and "repair_status" in item and REPAIR_RESUME_FIELD not in item,
        process_fn=lambda item: repair_one_env(item, args),
        save_every=args.save_every,
        step_label="Stage3-Refine-Step4",
        progress_desc=getattr(args, "progress_desc", None),
        progress_position=getattr(args, "progress_position", None),
    )
    print(f"[Step4] saved: {args.save_file_path}")


def _build_repair_pause(
    *,
    current_item: Dict[str, Any],
    best_item: Dict[str, Any],
    best_metrics: Dict[str, Any],
    repair_audit: Dict[str, Any],
    round_idx: int,
    error: RecoverableAPIError,
) -> RecoverableStepError:
    partial_item = deepcopy(current_item)
    partial_item["repair_audit"] = deepcopy(repair_audit)
    partial_item[REPAIR_RESUME_FIELD] = {
        "current_item": deepcopy(current_item),
        "best_item": deepcopy(best_item),
        "best_metrics": deepcopy(best_metrics),
        "repair_audit": deepcopy(repair_audit),
        "next_round": round_idx,
    }
    return RecoverableStepError(
        step_label="Stage3-Refine-Step4",
        error=error,
        partial_item=partial_item,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--read_file_path",
        type=str,
        default="stage3_refine/temp_result/step3_bug_ledger.json",
    )
    parser.add_argument(
        "--save_file_path",
        type=str,
        default="stage3_refine/temp_result/step4_repaired_envs.json",
    )
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--positive_pass_threshold", type=float, default=0.5)
    parser.add_argument("--top_n", type=int, default=5)
    parser.add_argument("--max_repair_rounds", type=int, default=3)
    parser.add_argument("--eval_steps", type=int, default=100)
    parser.add_argument("--eval_model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--eval_temperature", type=float, default=0.5)
    parser.add_argument("--agent_mode", type=str, choices=["dual", "local"], default="dual")
    parser.add_argument("--enable_llm_patch", action="store_true")
    parser.add_argument("--llm_patch_model", type=str, default="gpt-4.1")
    parser.add_argument("--llm_patch_temperature", type=float, default=0.1)
    parser.add_argument("--save_every", type=int, default=1)
    args = parser.parse_args()
    main(args)
