"""Stage3-REFINE Step2: baseline rollout check with eval init_config."""

import argparse
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage3_refine.verification.auto_env import build_env_from_str, get_state_diff
from stage3_refine.refine_agents import (
    LocalCheckAgent,
    LocalFuncCallAgent,
    SafeDualCheckAgent,
    SafeDualFuncCallAgent,
)
from stage3_refine.refine_utils import calc_metrics_from_item, ensure_eval_init_config
from utils.process_file import read_file, save_file
from utils.recovery import RecoverableAPIError, RecoverableStepError
from utils.resumable import run_sequential_step


RESUME_ROLLOUT_FIELD = "__resume_rollout_steps_log"


def build_func_test_cases(steps_log):
    """Convert flat step logs into function-grouped summary/details."""
    def normalize_status(case):
        status = (case.get("status") or "").strip().lower()
        if status in ("pass", "warning", "fail"):
            return status
        if case.get("passed") is True:
            return "pass"
        if case.get("passed") is False:
            return "fail"
        return "fail"

    log_data = {
        "func_test_cases": {
            "summary": {
                "total_count": 0,
                "pass_count": 0,
                "warning_count": 0,
                "fail_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "positive_pass_count": 0,
                "positive_warning_count": 0,
                "positive_fail_count": 0,
                "negative_pass_count": 0,
                "negative_warning_count": 0,
                "negative_fail_count": 0,
            },
            "details": {},
        }
    }

    summary_all = log_data["func_test_cases"]["summary"]
    details = log_data["func_test_cases"]["details"]

    for case in steps_log:
        func_name = case.get("tool_name", "UNKNOWN")
        case_type = (case.get("case_type") or "").strip().lower()
        status = normalize_status(case)
        passed_bool = status == "pass"
        check_reason = None
        if isinstance(case.get("check_result"), dict):
            check_reason = (
                case["check_result"].get("analysis")
                or case["check_result"].get("reason")
                or None
            )

        summary_all["total_count"] += 1
        if status == "pass":
            summary_all["pass_count"] += 1
        elif status == "warning":
            summary_all["warning_count"] += 1
        else:
            summary_all["fail_count"] += 1

        if case_type == "positive":
            summary_all["positive_count"] += 1
            if status == "pass":
                summary_all["positive_pass_count"] += 1
            elif status == "warning":
                summary_all["positive_warning_count"] += 1
            else:
                summary_all["positive_fail_count"] += 1
        elif case_type == "negative":
            summary_all["negative_count"] += 1
            if status == "pass":
                summary_all["negative_pass_count"] += 1
            elif status == "warning":
                summary_all["negative_warning_count"] += 1
            else:
                summary_all["negative_fail_count"] += 1

        if func_name not in details:
            details[func_name] = {
                "summary": {
                    "total_count": 0,
                    "pass_count": 0,
                    "warning_count": 0,
                    "fail_count": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "positive_pass_count": 0,
                    "positive_warning_count": 0,
                    "positive_fail_count": 0,
                    "negative_pass_count": 0,
                    "negative_warning_count": 0,
                    "negative_fail_count": 0,
                },
                "cases": [],
            }
        summary_func = details[func_name]["summary"]
        summary_func["total_count"] += 1
        if status == "pass":
            summary_func["pass_count"] += 1
        elif status == "warning":
            summary_func["warning_count"] += 1
        else:
            summary_func["fail_count"] += 1

        if case_type == "positive":
            summary_func["positive_count"] += 1
            if status == "pass":
                summary_func["positive_pass_count"] += 1
            elif status == "warning":
                summary_func["positive_warning_count"] += 1
            else:
                summary_func["positive_fail_count"] += 1
        elif case_type == "negative":
            summary_func["negative_count"] += 1
            if status == "pass":
                summary_func["negative_pass_count"] += 1
            elif status == "warning":
                summary_func["negative_warning_count"] += 1
            else:
                summary_func["negative_fail_count"] += 1

        details[func_name]["cases"].append(
            {
                "step": case.get("step"),
                "case_type": case_type,
                "status": status,
                "passed": passed_bool,
                "thought": case.get("thought", ""),
                "parameters": case.get("parameters", {}),
                "state_before_call": case.get("state_before_call", {}),
                "state_after_call": case.get("state_after_call", {}),
                "state_diff": case.get("state_diff", {}),
                "observation": case.get("observation", {}),
                "check_result": case.get("check_result", {}),
                "check_reason": check_reason,
            }
        )
    return log_data


def _build_agents(env_item, agent_mode: str, model: str, temperature: float):
    if agent_mode == "dual":
        func_call_agent = SafeDualFuncCallAgent(model=model, temperature=temperature, env_item=env_item)
        check_agent = SafeDualCheckAgent(model=model, temperature=0, env_item=env_item)
    else:
        func_call_agent = LocalFuncCallAgent(env_item=env_item)
        check_agent = LocalCheckAgent()
    return func_call_agent, check_agent


def _run_one_step(step_idx, env, func_call_agent, check_agent):
    state_before_call = deepcopy(env.get_state_info())
    func_call_request = func_call_agent.gen_func_call_request(current_state=state_before_call)
    func_name = func_call_request.get("tool_name")
    func_params = func_call_request.get("parameters", {})
    case_type = func_call_request.get("case_type", "positive")

    observation, reward, terminated, truncated, info = env.env_step(
        action={"name": func_name, "params": func_params}
    )
    state_after_call = deepcopy(env.get_state_info())
    state_diff = deepcopy(get_state_diff(state_before_call, state_after_call))
    check_result = deepcopy(
        check_agent.check_func_call(
            func_name=func_name,
            state_before_call=state_before_call,
            func_params=func_params,
            func_return=observation,
            state_after_call=state_after_call,
            state_diff=state_diff,
        )
    )
    check_status = str(check_result.get("result", "fail")).lower().strip()
    if check_status not in ("pass", "warning", "fail"):
        check_status = "fail"
    func_call_agent.update_stats(func_name, case_type=case_type, check_result=check_status)

    return {
        "step": step_idx,
        "tool_name": func_name,
        "case_type": case_type,
        "parameters": func_params,
        "state_before_call": state_before_call,
        "state_after_call": state_after_call,
        "state_diff": state_diff,
        "observation": observation,
        "reward": reward,
        "terminated": terminated,
        "truncated": truncated,
        "info": info,
        "check_result": check_result,
        "status": check_status,
        "stats_summary": func_call_agent.get_stats_table_str(),
    }


def run_rollout_for_env_item(
    env_item,
    model: str,
    temperature: float,
    max_steps: int,
    agent_mode: str,
):
    env_item = ensure_eval_init_config(env_item)
    new_item = deepcopy(env_item)

    try:
        env = build_env_from_str(
            env_str=new_item["env_class_code"],
            class_name=new_item["env_class_name"],
            max_steps=max_steps + 10,
        )
        env.env_init(init_config=new_item.get("eval_init_config", {}))
    except Exception as exc:
        new_item["func_test_result"] = {
            "func_test_cases": {
                "summary": {
                    "total_count": 1,
                    "pass_count": 0,
                    "warning_count": 0,
                    "fail_count": 1,
                    "positive_count": 0,
                    "negative_count": 0,
                    "positive_pass_count": 0,
                    "positive_warning_count": 0,
                    "positive_fail_count": 0,
                    "negative_pass_count": 0,
                    "negative_warning_count": 0,
                    "negative_fail_count": 0,
                },
                "details": {
                    "__env_init__": {
                        "summary": {"total_count": 1, "pass_count": 0, "warning_count": 0, "fail_count": 1},
                        "cases": [
                            {
                                "step": 0,
                                "status": "fail",
                                "case_type": "positive",
                                "parameters": {},
                                "observation": {"error": f"env init error: {exc}"},
                                "check_reason": f"Environment initialization failed: {exc}",
                            }
                        ],
                    }
                },
            }
        }
        new_item["baseline_metrics"] = calc_metrics_from_item(new_item)
        return new_item

    func_call_agent, check_agent = _build_agents(
        env_item=new_item,
        agent_mode=agent_mode,
        model=model,
        temperature=temperature,
    )

    steps_log = deepcopy(new_item.get(RESUME_ROLLOUT_FIELD, []))
    _restore_rollout_progress(env, func_call_agent, steps_log)
    for step_idx in range(len(steps_log), max_steps):
        try:
            step_log = _run_one_step(step_idx, env, func_call_agent, check_agent)
            steps_log.append(step_log)
        except RecoverableAPIError as exc:
            partial_item = deepcopy(new_item)
            partial_item[RESUME_ROLLOUT_FIELD] = steps_log
            partial_item["func_test_result"] = build_func_test_cases(steps_log)
            partial_item["baseline_metrics"] = calc_metrics_from_item(partial_item)
            raise RecoverableStepError(
                step_label="Stage3-Refine-Step2",
                error=exc,
                partial_item=partial_item,
            ) from exc
        except Exception as exc:
            steps_log.append(
                {
                    "step": step_idx,
                    "tool_name": "__rollout_error__",
                    "case_type": "negative",
                    "status": "fail",
                    "parameters": {},
                    "observation": {"error": f"rollout step error: {exc}"},
                    "check_result": {"analysis": "rollout exception", "result": "Fail", "error_reason": str(exc)},
                }
            )

    new_item["func_test_result"] = build_func_test_cases(steps_log)
    new_item["baseline_metrics"] = calc_metrics_from_item(new_item)
    new_item.pop(RESUME_ROLLOUT_FIELD, None)
    return new_item


def _restore_rollout_progress(env, func_call_agent, steps_log):
    for step_log in steps_log:
        tool_name = step_log.get("tool_name")
        params = step_log.get("parameters", {})
        if tool_name and not str(tool_name).startswith("__"):
            try:
                env.env_step(action={"name": tool_name, "params": params})
            except Exception:
                pass
            func_call_agent.update_stats(
                tool_name,
                case_type=step_log.get("case_type", "positive"),
                check_result=step_log.get("status", "fail"),
            )


def main(args):
    data = read_file(args.read_file_path)
    run_sequential_step(
        items=data,
        output_path=args.save_file_path,
        key_fn=lambda item: item.get("__dispatch_index__", item.get("task", item.get("environment_summary", ""))),
        is_complete_fn=lambda item: (
            isinstance(item, dict)
            and "func_test_result" in item
            and RESUME_ROLLOUT_FIELD not in item
            and "baseline_metrics" in item
        ),
        process_fn=lambda item: run_rollout_for_env_item(
            env_item=item,
            model=args.model,
            temperature=args.temperature,
            max_steps=args.max_steps,
            agent_mode=args.agent_mode,
        ),
        save_every=args.save_every,
        step_label="Stage3-Refine-Step2",
        progress_desc=getattr(args, "progress_desc", None),
        progress_position=getattr(args, "progress_position", None),
    )
    print(f"[Step2] saved: {args.save_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--read_file_path",
        type=str,
        default="stage3_refine/temp_result/step1_prepared_init_configs.json",
    )
    parser.add_argument(
        "--save_file_path",
        type=str,
        default="stage3_refine/temp_result/step2_baseline_roll_check.json",
    )
    parser.add_argument("--model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--max_steps", type=int, default=100)
    parser.add_argument("--agent_mode", type=str, choices=["dual", "local"], default="dual")
    parser.add_argument("--save_every", type=int, default=1)
    args = parser.parse_args()
    main(args)
