from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import LLMConfig
from core.file_utils import ensure_dir, read_json, write_json
from environment import EnvManager
from TrajGen.tir_agent_openai import (
    OpenAIToolCallAgent,
    _assistant_message_for_record,
    _assistant_message_for_replay,
    _build_plain_trajectory_text,
    _coerce_message_text,
    _extract_recorded_assistant_output,
    _extract_step_assistant_text,
    _is_gpt_model,
    _normalize_message_tool_calls_for_execution,
    _should_apply_cjk_tool_arg_sanitization,
    _snapshot_tool_payload,
)


RUNS_ROOT = ROOT_DIR / "TrajGen" / "traj_batch_runs"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _arg_after(command: List[Any], name: str, default: Optional[str] = None) -> Optional[str]:
    tokens = [str(item) for item in command]
    for idx, token in enumerate(tokens):
        if token == name and idx + 1 < len(tokens):
            return tokens[idx + 1]
    return default


def _bool_arg_after(command: List[Any], name: str) -> Optional[bool]:
    value = _arg_after(command, name)
    if value is None:
        return None
    return str(value).strip() not in {"0", "false", "False"}


def _find_trace_event(trace_dir: Path, *, category: str, name: str, latest: bool = False) -> Dict[str, Any]:
    matches: List[Dict[str, Any]] = []
    for path in sorted(trace_dir.glob("*.json")):
        try:
            data = _load_json(path)
        except Exception:
            continue
        if data.get("category") == category and data.get("name") == name:
            data["_path"] = str(path)
            matches.append(data)
    if not matches:
        raise FileNotFoundError(f"trace event not found: category={category} name={name} in {trace_dir}")
    return matches[-1] if latest else matches[0]


def _find_step_messages(trace_dir: Path, *, step: int, attempt: int) -> Dict[str, Any]:
    for path in sorted(trace_dir.glob("*.json")):
        try:
            data = _load_json(path)
        except Exception:
            continue
        if data.get("category") != "tir_agent_openai" or data.get("name") != "step_messages":
            continue
        payload = data.get("payload") or {}
        if int(payload.get("step") or -1) == int(step) and int(payload.get("attempt") or -1) == int(attempt):
            data["_path"] = str(path)
            return data
    raise FileNotFoundError(f"step_messages trace not found: step={step} attempt={attempt} in {trace_dir}")


def _resolve_attempt_dir(run_name: Optional[str], case_id: Optional[str], attempt_dir: Optional[str]) -> Path:
    if attempt_dir:
        resolved = Path(attempt_dir).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"attempt_dir not found: {resolved}")
        return resolved
    if not run_name or not case_id:
        raise ValueError("Either --attempt_dir or both --run_name and --case_id are required.")
    state_path = RUNS_ROOT / run_name / "cases" / case_id / "state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"case state not found: {state_path}")
    state = _load_json(state_path)
    resolved = Path(str(state.get("last_attempt_dir") or "")).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"last_attempt_dir not found: {resolved}")
    return resolved


def _resolve_temp_traj_path(attempt_dir: Path, failed_traj_path: Optional[str]) -> Path:
    if failed_traj_path:
        path = Path(failed_traj_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"failed trajectory not found: {path}")
        return path
    matches = sorted((attempt_dir / "temp_traj_root").rglob("*_traj.json"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one temp trajectory under {attempt_dir}, found {len(matches)}")
    return matches[0].resolve()


def _extract_output_traj_root(args: argparse.Namespace, attempt_summary: Dict[str, Any]) -> Path:
    if args.output_traj_root:
        return Path(args.output_traj_root).expanduser().resolve()

    command = attempt_summary.get("command")
    if isinstance(command, list):
        case_file = _arg_after(command, "--case_file")
        if case_file:
            # This fallback mirrors the batch convention only when the caller
            # explicitly used --traj_output_dir_name. Keeping this path explicit
            # prevents accidental writes into an unexpected formal result dir.
            case_parent = Path(case_file).expanduser().resolve().parent
            fallback = case_parent.parent / "split_choice_continued_traj"
            return fallback.resolve()
    return (ROOT_DIR / "split_choice_continued_traj").resolve()


def _relative_output_path(args: argparse.Namespace, case_file: Path) -> Path:
    if args.run_name and args.case_id:
        state_path = RUNS_ROOT / str(args.run_name) / "cases" / str(args.case_id) / "state.json"
        if state_path.exists():
            state = _load_json(state_path)
            rel = str(state.get("relative_traj_path") or "").strip()
            if rel:
                return Path(rel)

    return Path(f"{case_file.stem}_traj.json")


def _is_split_text_and_tool_choices(raw: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    choices = raw.get("choices")
    if not isinstance(choices, list) or len(choices) != 2:
        raise ValueError(f"Expected exactly 2 choices, got {len(choices) if isinstance(choices, list) else 'non-list'}")

    text_choice: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        content = _coerce_message_text(message.get("content")).strip()
        tool_calls = message.get("tool_calls") or []
        if content and not tool_calls:
            if text_choice is not None:
                raise ValueError("More than one text-only choice found.")
            text_choice = choice
        elif tool_calls and not content:
            if tool_choice is not None:
                raise ValueError("More than one tool-only choice found.")
            tool_choice = choice

    if text_choice is None or tool_choice is None:
        raise ValueError("Multiple choices are not a strict text-only + tool-only split.")
    return text_choice, tool_choice


def _merge_split_choice_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    text_choice, tool_choice = _is_split_text_and_tool_choices(raw)
    text_message = text_choice.get("message") or {}
    tool_message = tool_choice.get("message") or {}

    merged_message = _snapshot_tool_payload(tool_message)
    if not isinstance(merged_message, dict):
        raise ValueError("Tool choice message is not an object.")
    merged_message["role"] = str(merged_message.get("role") or "assistant")
    merged_message["content"] = text_message.get("content")
    if "refusal" in text_message and "refusal" not in merged_message:
        merged_message["refusal"] = text_message.get("refusal")

    merged_choice = _snapshot_tool_payload(tool_choice)
    merged_choice["message"] = merged_message
    merged_choice["finish_reason"] = tool_choice.get("finish_reason") or "tool_calls"

    merged_raw = _snapshot_tool_payload(raw)
    merged_raw["choices"] = [merged_choice]
    return {"ok": True, "error": None, "raw": merged_raw, "message": merged_message}


def _build_llm_config_from_attempt(
    attempt_summary: Dict[str, Any],
    agent_inputs: Dict[str, Any],
    *,
    api_key_override: Optional[str] = None,
    base_url_override: Optional[str] = None,
    model_override: Optional[str] = None,
) -> LLMConfig:
    command = attempt_summary.get("command") if isinstance(attempt_summary.get("command"), list) else []
    llm_payload = agent_inputs.get("llm_config") if isinstance(agent_inputs.get("llm_config"), dict) else {}
    return LLMConfig(
        api_key=str(api_key_override if api_key_override is not None else (_arg_after(command, "--eval_api_key", "") or "")),
        base_url=str(
            base_url_override
            if base_url_override is not None
            else (_arg_after(command, "--eval_base_url", llm_payload.get("base_url", "")) or "")
        ),
        model=str(
            model_override
            if model_override is not None
            else (_arg_after(command, "--eval_model", llm_payload.get("model", "")) or "")
        ),
        timeout_seconds=int(_arg_after(command, "--timeout_seconds", llm_payload.get("timeout_seconds", 600)) or 600),
        max_retries=int(_arg_after(command, "--network_max_retries", llm_payload.get("max_retries", 0)) or 0),
    )


def _execution_args_from_attempt(attempt_summary: Dict[str, Any]) -> Dict[str, Any]:
    command = attempt_summary.get("command") if isinstance(attempt_summary.get("command"), list) else []
    return {
        "max_steps": int(_arg_after(command, "--max_steps", 50) or 50),
        "temperature": float(_arg_after(command, "--temperature", 0.2) or 0.2),
        "max_tokens": int(_arg_after(command, "--max_tokens", 12000) or 12000),
        "parallel_tool_calls": _bool_arg_after(command, "--parallel_tool_calls"),
        "n": None if _arg_after(command, "--n") is None else int(_arg_after(command, "--n") or 1),
        "tool_choice": str(_arg_after(command, "--tool_choice", "auto") or "auto"),
    }


def _replay_environment_state(case_data: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> Any:
    env_name = case_data.get("environment", "")
    env_init_params = case_data.get("env_initial_parameters", {}) or {}
    env_manager = EnvManager()
    env = env_manager.init_env(env_name, env_init_params)
    if env is None:
        raise ValueError(f"Failed to init environment: {env_name}")

    for step in previous_steps:
        for call in step.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            name = str(call.get("name") or "").strip()
            arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
            if not name:
                continue
            env.call_tool(name, arguments)
    return env


def _trajectory_chunks_from_steps(steps: List[Dict[str, Any]]) -> List[str]:
    chunks: List[str] = []
    for step in steps:
        text = _extract_step_assistant_text(step)
        if text:
            chunks.append(text)
        for call in step.get("tool_calls") or []:
            name = str(call.get("name") or "")
            args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
            chunks.append(f"<tool_call>{json.dumps({'name': name, 'arguments': args}, ensure_ascii=False)}</tool_call>")
        for obs in step.get("tool_responses") or []:
            content = obs.get("content")
            chunks.append(f"<tool_response>{json.dumps(content, ensure_ascii=False)}</tool_response>")
    return chunks


def _last_completed_round_trace(previous_steps: List[Dict[str, Any]]) -> str:
    value = ""
    for step in previous_steps:
        if step.get("tool_calls"):
            value = _extract_step_assistant_text(step)
    return value


def _process_response_turn(
    *,
    agent: OpenAIToolCallAgent,
    env: Any,
    response: Dict[str, Any],
    messages: List[Dict[str, Any]],
    steps: List[Dict[str, Any]],
    trajectory_chunks: List[str],
    step_idx: int,
    attempt_idx: int,
    last_completed_round_trace: str,
) -> Tuple[str, str, str]:
    raw_msg = _snapshot_tool_payload(response.get("message") or {})
    enable_cjk_sanitization = _should_apply_cjk_tool_arg_sanitization(agent.llm_config.model)
    msg = _normalize_message_tool_calls_for_execution(
        raw_msg,
        enable_cjk_sanitization=enable_cjk_sanitization,
    )

    assistant_content = _coerce_message_text(raw_msg.get("content"))
    recorded_assistant_output = _extract_recorded_assistant_output(raw_msg)
    tool_calls = msg.get("tool_calls") or []
    if not isinstance(tool_calls, list):
        tool_calls = []

    has_tool_calls = bool(tool_calls)
    has_visible_content = bool(assistant_content.strip())
    if not has_tool_calls and not has_visible_content:
        error_message = "LLM returned an empty response without tool calls or visible content."
        steps.append(
            {
                "step": step_idx,
                "assistant_message": _assistant_message_for_record(raw_msg),
                "tool_calls": [],
                "tool_responses": [],
                "error": error_message,
            }
        )
        return "error", "", last_completed_round_trace

    step_record: Dict[str, Any] = {
        "step": step_idx,
        "assistant_message": _assistant_message_for_record(raw_msg),
        "tool_calls": [],
        "tool_responses": [],
    }

    if tool_calls:
        messages.append(_assistant_message_for_replay(msg))
        if recorded_assistant_output:
            trajectory_chunks.append(recorded_assistant_output)

        for tc in tool_calls:
            tc_id = str((tc or {}).get("id", "") or "")
            fn = (tc or {}).get("function") or {}
            tool_name = str(fn.get("name", "") or "").strip()
            tool_args = agent._parse_tool_args(fn.get("arguments", {}))
            step_record["tool_calls"].append(
                {
                    "id": tc_id,
                    "name": tool_name,
                    "arguments": tool_args,
                }
            )

            try:
                tool_result = env.call_tool(tool_name, tool_args)
            except Exception as exc:
                tool_result = {"success": False, "error": f"{type(exc).__name__}: {exc}"}

            tool_result_snapshot = _snapshot_tool_payload(tool_result)
            step_record["tool_responses"].append(
                {
                    "tool_call_id": tc_id,
                    "name": tool_name,
                    "content": tool_result_snapshot,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": tool_name,
                    "content": json.dumps(tool_result_snapshot, ensure_ascii=False),
                }
            )
            trajectory_chunks.append(
                f"<tool_call>{json.dumps({'name': tool_name, 'arguments': tool_args}, ensure_ascii=False)}</tool_call>"
            )
            trajectory_chunks.append(f"<tool_response>{json.dumps(tool_result_snapshot, ensure_ascii=False)}</tool_response>")

        steps.append(step_record)
        return "continue", "", recorded_assistant_output or ""

    messages.append(_assistant_message_for_replay(msg))
    steps.append(step_record)
    final_answer = recorded_assistant_output or ""
    if final_answer:
        trajectory_chunks.append(final_answer)
    return "finished", final_answer, last_completed_round_trace


def continue_from_split_choice(args: argparse.Namespace) -> Dict[str, Any]:
    attempt_dir = _resolve_attempt_dir(args.run_name, args.case_id, args.attempt_dir)
    trace_dir = attempt_dir / "trace"
    if not trace_dir.exists():
        raise FileNotFoundError(f"trace directory not found: {trace_dir}")

    attempt_summary_path = attempt_dir / "attempt_summary.json"
    if not attempt_summary_path.exists():
        raise FileNotFoundError(f"attempt_summary.json not found: {attempt_summary_path}")
    attempt_summary = _load_json(attempt_summary_path)

    failed_traj_path = _resolve_temp_traj_path(attempt_dir, args.failed_traj_path)
    failed_traj = _load_json(failed_traj_path)
    failed_steps = failed_traj.get("steps") if isinstance(failed_traj.get("steps"), list) else []
    previous_steps = [copy.deepcopy(step) for step in failed_steps if isinstance(step, dict) and not step.get("error")]

    agent_inputs_event = _find_trace_event(trace_dir, category="trajgen", name="agent_inputs")
    agent_inputs = agent_inputs_event.get("payload") or {}
    error_event = _find_trace_event(trace_dir, category="tir_agent_openai", name="step_llm_error", latest=True)
    error_payload = error_event.get("payload") or {}
    step_idx = int(error_payload.get("step") or (len(previous_steps) + 1))
    attempt_idx = int(error_payload.get("attempt") or step_idx)
    step_messages_event = _find_step_messages(trace_dir, step=step_idx, attempt=attempt_idx)
    messages = _snapshot_tool_payload((step_messages_event.get("payload") or {}).get("messages") or [])
    if not isinstance(messages, list):
        raise ValueError("Recovered step messages are not a list.")

    response = error_payload.get("response") or {}
    raw = response.get("raw") if isinstance(response, dict) else None
    if not isinstance(raw, dict):
        raise ValueError("Failed response raw payload is missing.")
    merged_response = _merge_split_choice_response(raw)

    case_file = Path(str(attempt_summary.get("case_path") or _arg_after(attempt_summary.get("command") or [], "--case_file") or "")).expanduser().resolve()
    if not case_file.exists():
        raise FileNotFoundError(f"case file not found: {case_file}")
    case_data = read_json(case_file)
    env = _replay_environment_state(case_data, previous_steps)

    llm_config = _build_llm_config_from_attempt(
        attempt_summary,
        agent_inputs,
        api_key_override=getattr(args, "eval_api_key", None),
        base_url_override=getattr(args, "eval_base_url", None),
        model_override=getattr(args, "eval_model", None),
    )
    exec_args = _execution_args_from_attempt(attempt_summary)
    tools = agent_inputs.get("openai_tools")
    if not isinstance(tools, list):
        raise ValueError("openai_tools missing from trace agent_inputs.")

    agent = OpenAIToolCallAgent(
        llm_config=llm_config,
        system_prompt=str(agent_inputs.get("system_prompt") or ""),
        task_prompt=str(agent_inputs.get("task_prompt") or ""),
        tools=tools,
        tool_executor=lambda name, arguments, _trace: env.call_tool(name, arguments),
        max_steps=int(exec_args["max_steps"]),
        temperature=float(exec_args["temperature"]),
        max_tokens=int(exec_args["max_tokens"]),
        parallel_tool_calls=exec_args["parallel_tool_calls"],
        n=exec_args["n"],
        tool_choice=str(exec_args["tool_choice"]),
    )

    steps = previous_steps
    trajectory_chunks = _trajectory_chunks_from_steps(steps)
    last_round_trace = _last_completed_round_trace(steps)
    final_answer = ""
    status = "max_steps"
    merged_count = 0

    turn_status, final_answer, last_round_trace = _process_response_turn(
        agent=agent,
        env=env,
        response=merged_response,
        messages=messages,
        steps=steps,
        trajectory_chunks=trajectory_chunks,
        step_idx=step_idx,
        attempt_idx=attempt_idx,
        last_completed_round_trace=last_round_trace,
    )
    merged_count += 1
    if turn_status == "finished":
        status = "finished"
    elif turn_status == "error":
        status = "error"
    else:
        while len(steps) < int(exec_args["max_steps"]):
            next_step = len(steps) + 1
            resp = agent._chat_once(messages)
            if not resp.get("ok"):
                raw_payload = resp.get("raw")
                if (
                    args.merge_subsequent_split_choices
                    and isinstance(raw_payload, dict)
                    and str(resp.get("error") or "").startswith("Multiple choices in response:")
                ):
                    try:
                        resp = _merge_split_choice_response(raw_payload)
                        merged_count += 1
                    except Exception:
                        status = "error"
                        steps.append(
                            {
                                "step": next_step,
                                "assistant_message": None,
                                "tool_calls": [],
                                "tool_responses": [],
                                "error": resp.get("error", "LLM call failed"),
                            }
                        )
                        break
                else:
                    status = "error"
                    steps.append(
                        {
                            "step": next_step,
                            "assistant_message": None,
                            "tool_calls": [],
                            "tool_responses": [],
                            "error": resp.get("error", "LLM call failed"),
                        }
                    )
                    break

            turn_status, final_answer, last_round_trace = _process_response_turn(
                agent=agent,
                env=env,
                response=resp,
                messages=messages,
                steps=steps,
                trajectory_chunks=trajectory_chunks,
                step_idx=next_step,
                attempt_idx=next_step,
                last_completed_round_trace=last_round_trace,
            )
            if turn_status == "finished":
                status = "finished"
                break
            if turn_status == "error":
                status = "error"
                break
        else:
            status = "max_steps"

    result = copy.deepcopy(failed_traj)
    result["status"] = status
    result["final_answer"] = final_answer
    result["steps"] = steps
    result["trajectory_text"] = _build_plain_trajectory_text(
        steps=steps,
        final_answer=final_answer,
        status=status,
    )
    result["trajectory_text_raw"] = "\n".join([chunk for chunk in trajectory_chunks if isinstance(chunk, str) and chunk])

    output_root = _extract_output_traj_root(args, attempt_summary)
    out_path = output_root / _relative_output_path(args, case_file)
    write_json(out_path, result)

    repair_log = {
        "source_attempt_dir": str(attempt_dir),
        "source_failed_traj_path": str(failed_traj_path),
        "output_traj_path": str(out_path),
        "status": status,
        "merged_split_choice_count": merged_count,
        "initial_merged_step": step_idx,
        "model": llm_config.model,
        "base_url": llm_config.base_url,
        "n": exec_args["n"] if exec_args["n"] is not None and _is_gpt_model(llm_config.model) else None,
    }
    if getattr(args, "slot_id", None) is not None:
        repair_log["slot_id"] = getattr(args, "slot_id")
    if getattr(args, "slot_name", None) is not None:
        repair_log["slot_name"] = getattr(args, "slot_name")
    log_path = out_path.with_name(f"{out_path.stem}_split_choice_repair_log.json")
    write_json(log_path, repair_log)
    return repair_log


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Continue a failed OpenAI-tool trajectory by merging a strict split-choice response "
            "(one text-only choice + one tool-only choice) into one assistant message."
        )
    )
    parser.add_argument("--run_name", type=str, default=None, help="Batch run name under TrajGen/traj_batch_runs.")
    parser.add_argument("--case_id", type=str, default=None, help="Case id, e.g. case_00739.")
    parser.add_argument("--attempt_dir", type=str, default=None, help="Direct path to a failed attempt directory.")
    parser.add_argument("--failed_traj_path", type=str, default=None, help="Optional direct path to failed temp traj.")
    parser.add_argument(
        "--output_traj_root",
        type=str,
        required=True,
        help="Formal trajectory output root, e.g. result/gpt-5.4-mini/n_v9.",
    )
    parser.add_argument(
        "--merge_subsequent_split_choices",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also merge later strict text/tool split choices during continuation.",
    )
    args = parser.parse_args()
    repair_log = continue_from_split_choice(args)
    print(json.dumps(repair_log, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
