# -*- coding: utf-8 -*-
"""Single-case trajectory generation with OpenAI-compatible tool calling."""

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

from core.config import DEFAULT_LLM_CONFIG, DEFAULT_MAX_TOKENS, LLMConfig, REACT_MAX_STEPS
from core.debug_trace import trace_event, trace_log
from core.file_utils import read_json, write_json
from environment import EnvManager
from TrajGen.tir_agent_openai import OpenAIToolCallAgent
from TrajGen.tir_agent_openai import _is_gpt_model


def _build_overridden_llm_config(
    api_key: Optional[str],
    base_url: Optional[str],
    model: Optional[str],
    timeout_seconds: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> LLMConfig:
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
    model_name = str(model or cfg.model).strip()
    cfg.model = model_name if model_name else cfg.model
    if timeout_seconds is not None:
        cfg.timeout_seconds = int(timeout_seconds)
    if max_retries is not None:
        cfg.max_retries = int(max_retries)
    return cfg


def _resolve_task_description(case_data: Dict[str, Any]) -> str:
    for key in ("task_description", "rough_task_description"):
        value = case_data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolve_function_list(case_data: Dict[str, Any]) -> List[str]:
    for key in ("function_list", "rough_function_list"):
        value = case_data.get(key)
        if isinstance(value, list) and value:
            return [str(x).strip() for x in value if isinstance(x, str) and str(x).strip()]
    return []


def _model_requires_root_combinator_cleanup(model_name: Optional[str]) -> bool:
    model_id = str(model_name or "").strip().rsplit("/", 1)[-1].lower()
    return model_id.startswith(("gpt", "claude", "kimi"))


def _sanitize_tool_parameters_for_model(parameters: Any, model_name: Optional[str]) -> Any:
    if not isinstance(parameters, dict):
        return parameters
    if not _model_requires_root_combinator_cleanup(model_name):
        return copy.deepcopy(parameters)

    sanitized = copy.deepcopy(parameters)
    for key in ("anyOf", "oneOf", "allOf"):
        sanitized.pop(key, None)
    return sanitized


def _build_openai_tools_payload(
    tool_schema: List[Dict[str, Any]],
    *,
    model_name: Optional[str],
) -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "parameters": _sanitize_tool_parameters_for_model(
                    t.get("parameters", {"type": "object", "properties": {}, "required": []}),
                    model_name,
                ),
            },
        }
        for t in tool_schema
    ]


def build_react_system_prompt_openai(tool_schema: List[Dict[str, Any]]) -> str:
    tool_names = [str(t.get("name", "")).strip() for t in tool_schema if isinstance(t, dict)]
    tool_names = [x for x in tool_names if x]

    return (
        "You are an autonomous tool-using agent working in an interactive environment.\n"
        "You must solve the task using only the provided tools and tool results.\n"
        "Execution rules:\n"
        "1) Use OpenAI function-calling style via provided tools; do not invent non-existent tools.\n"
        "2) Prefer evidence-driven actions; do not claim facts that are not observed from tool outputs.\n"
        "3) If IDs/keys are required, discover them via available tools rather than guessing.\n"
        "4) Avoid redundant repeated calls with identical arguments unless needed after a state-changing action.\n"
        "5) When sufficient evidence is collected and task objective is reached, provide a concise final answer.\n"
        "6) If completion is impossible, explain objective blockers based on observed tool evidence.\n"
        f"Available tool names: {tool_names}\n"
        "\nProtocol guard:\n"
        "- Do not output XML-like tool tags.\n"
        "- Use native tool calls through the API tools interface only.\n"
    )


def build_task_prompt_openai(case_data: Dict[str, Any]) -> str:
    task = _resolve_task_description(case_data)
    env = str(case_data.get("environment", "") or "")

    return (
        "You will execute a task inside an interactive environment using available tools.\n"
        f"Environment: {env}\n"
        "Task:\n"
        f"{task}\n"
        "Constraints:\n"
        "- Act autonomously; do not ask user follow-up questions.\n"
        "- Use tool evidence only; avoid unsupported assumptions.\n"
    )


def evaluate_case_data_openai(
    case_data: Dict[str, Any],
    max_steps: int = REACT_MAX_STEPS,
    temperature: float = 0.2,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    eval_api_key: Optional[str] = None,
    eval_base_url: Optional[str] = None,
    eval_model: Optional[str] = None,
    parallel_tool_calls: Optional[bool] = None,
    n: Optional[int] = None,
    tool_choice: str = "auto",
    timeout_seconds: Optional[int] = None,
    network_max_retries: Optional[int] = None,
) -> Dict[str, Any]:
    trace_log(
        f"[TRAJGEN][RUN] case={case_data.get('case_name', '')} env={case_data.get('environment', '')} "
        f"max_steps={max_steps}"
    )

    env_name = case_data.get("environment", "")
    env_init_params = case_data.get("env_initial_parameters", {}) or {}
    function_list = _resolve_function_list(case_data)

    env_manager = EnvManager()
    env = env_manager.init_env(env_name, env_init_params)
    if env is None:
        raise ValueError(f"Failed to init environment: {env_name}")

    if not function_list:
        raise ValueError("case.function_list (or rough_function_list) must be non-empty")

    invalid_tools = [fn for fn in function_list if (not isinstance(fn, str)) or (not env.has_tool(fn))]
    if invalid_tools:
        raise ValueError(f"case.function_list has invalid tools: {invalid_tools}")
    valid_function_list = [fn for fn in function_list if isinstance(fn, str)]
    resolved_model_name = str(eval_model or DEFAULT_LLM_CONFIG.model).strip()

    env_tool_desc = env.get_tool_descs(valid_function_list)
    tool_schema: List[Dict[str, Any]] = [
        {
            "name": d.get("name"),
            "description": d.get("description", ""),
            "parameters": d.get("parameters", {"type": "object", "properties": {}, "required": []}),
        }
        for d in env_tool_desc
    ]

    # OpenAI-standard tools payload
    openai_tools = _build_openai_tools_payload(
        tool_schema,
        model_name=resolved_model_name,
    )

    base_system_prompt = build_react_system_prompt_openai(tool_schema=tool_schema)
    resolved_task_description = _resolve_task_description(case_data)
    if not resolved_task_description:
        raise ValueError("case.task_description (or rough_task_description) must be non-empty")
    case_for_prompt = dict(case_data)
    case_for_prompt["task_description"] = resolved_task_description
    system_prompt = base_system_prompt
    task_prompt = build_task_prompt_openai(case_data=case_for_prompt)

    llm_cfg = _build_overridden_llm_config(
        api_key=eval_api_key,
        base_url=eval_base_url,
        model=resolved_model_name,
        timeout_seconds=timeout_seconds,
        max_retries=network_max_retries,
    )

    def tool_executor(tool_name: str, arguments: Dict[str, Any], _last_round_trace: str) -> Dict[str, Any]:
        if env.has_tool(tool_name):
            return env.call_tool(tool_name, arguments)
        raise ValueError(f"Unknown tool call: {tool_name}")

    agent_inputs_payload = {
        "case_name": case_data.get("case_name", ""),
        "environment": env_name,
        "env_initial_parameters": env_init_params,
        "function_list": valid_function_list,
        "tool_schema": tool_schema,
        "openai_tools": openai_tools,
        "system_prompt": system_prompt,
        "task_prompt": task_prompt,
        "tool_choice": tool_choice,
        "llm_config": {
            "base_url": llm_cfg.base_url,
            "model": llm_cfg.model,
            "timeout_seconds": llm_cfg.timeout_seconds,
            "max_retries": llm_cfg.max_retries,
        },
    }
    if parallel_tool_calls is not None:
        agent_inputs_payload["parallel_tool_calls"] = bool(parallel_tool_calls)
    if n is not None and _is_gpt_model(llm_cfg.model):
        agent_inputs_payload["n"] = int(n)
    trace_event("trajgen", "agent_inputs", agent_inputs_payload)

    agent = OpenAIToolCallAgent(
        llm_config=llm_cfg,
        system_prompt=system_prompt,
        task_prompt=task_prompt,
        tools=openai_tools,
        tool_executor=tool_executor,
        max_steps=max_steps,
        temperature=temperature,
        max_tokens=max_tokens,
        parallel_tool_calls=None if parallel_tool_calls is None else bool(parallel_tool_calls),
        n=n,
        tool_choice=tool_choice,
    )
    run_res = agent.run()

    result = {
        "case_name": case_data.get("case_name", ""),
        "environment": env_name,
        "task_description": resolved_task_description,
        "function_list": valid_function_list,
        "tool_schema": tool_schema,
        "tool_mode": "openai_function_call",
        "tool_choice": tool_choice,
        "status": run_res.get("status"),
        "final_answer": run_res.get("final_answer", ""),
        "trajectory_text": run_res.get("trajectory_text", ""),
        "trajectory_text_raw": run_res.get("trajectory_text_raw", ""),
        "steps": run_res.get("steps", []),
    }
    if parallel_tool_calls is not None:
        result["parallel_tool_calls"] = bool(parallel_tool_calls)
    trace_event(
        "trajgen",
        "agent_result",
        {
            "case_name": case_data.get("case_name", ""),
            "run_result": run_res,
            "result": result,
        },
        print_message=f"[TRACE][trajgen][agent_result] case={case_data.get('case_name', '')} status={result.get('status')}",
    )
    return result


def run_case_file_openai(
    case_file: Path,
    traj_root: Path,
    max_steps: int = REACT_MAX_STEPS,
    temperature: float = 0.2,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    eval_api_key: Optional[str] = None,
    eval_base_url: Optional[str] = None,
    eval_model: Optional[str] = None,
    parallel_tool_calls: Optional[bool] = None,
    n: Optional[int] = None,
    tool_choice: str = "auto",
    timeout_seconds: Optional[int] = None,
    network_max_retries: Optional[int] = None,
) -> Tuple[Dict[str, Any], Path]:
    case_data = read_json(case_file)
    traj_data = evaluate_case_data_openai(
        case_data=case_data,
        max_steps=max_steps,
        temperature=temperature,
        max_tokens=max_tokens,
        eval_api_key=eval_api_key,
        eval_base_url=eval_base_url,
        eval_model=eval_model,
        parallel_tool_calls=parallel_tool_calls,
        n=n,
        tool_choice=tool_choice,
        timeout_seconds=timeout_seconds,
        network_max_retries=network_max_retries,
    )

    env_name = traj_data.get("environment", "unknown_env")
    case_name = traj_data.get("case_name", case_file.stem)

    out_dir = traj_root / env_name / case_name
    out_path = out_dir / f"{case_name}_traj.json"
    write_json(out_path, traj_data)
    trace_event(
        "trajgen",
        "traj_written",
        {
            "case_file": str(case_file),
            "traj_path": str(out_path),
            "traj_data": traj_data,
        },
        print_message=f"[TRACE][trajgen][traj_written] path={out_path}",
    )
    return traj_data, out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one case in OpenAI-compatible tool-calling mode")
    parser.add_argument("--case_file", type=str, required=True, help="case JSON path")
    parser.add_argument("--traj_root", type=str, default="traj", help="trajectory output root")
    parser.add_argument("--max_steps", type=int, default=REACT_MAX_STEPS)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max_tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--eval_api_key", type=str, default=None)
    parser.add_argument("--eval_base_url", type=str, default=None)
    parser.add_argument("--eval_model", type=str, required=True)
    parser.add_argument("--timeout_seconds", type=int, default=None)
    parser.add_argument("--network_max_retries", type=int, default=None)
    parser.add_argument("--parallel_tool_calls", type=int, choices=[0, 1], default=None, help="Optional: 0=off, 1=on")
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help=(
            "Optional explicit choices count for GPT-family models. "
            "For example, --n 1 requests one choice, but some endpoints may still return multiple choices."
        ),
    )
    parser.add_argument("--tool_choice", type=str, default="auto", help="auto|required|none")
    args = parser.parse_args()

    case_file = Path(args.case_file)
    traj_root = Path(args.traj_root)

    traj_data, out_path = run_case_file_openai(
        case_file=case_file,
        traj_root=traj_root,
        max_steps=args.max_steps,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        eval_api_key=args.eval_api_key,
        eval_base_url=args.eval_base_url,
        eval_model=args.eval_model,
        timeout_seconds=args.timeout_seconds,
        network_max_retries=args.network_max_retries,
        parallel_tool_calls=None if args.parallel_tool_calls is None else bool(args.parallel_tool_calls),
        n=args.n,
        tool_choice=args.tool_choice,
    )

    summary = {
        "case": str(case_file),
        "traj_path": str(out_path),
        "status": traj_data.get("status"),
        "tool_mode": traj_data.get("tool_mode"),
    }
    if "parallel_tool_calls" in traj_data:
        summary["parallel_tool_calls"] = traj_data.get("parallel_tool_calls")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
