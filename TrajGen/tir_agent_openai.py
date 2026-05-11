# -*- coding: utf-8 -*-
"""Core agent loop for OpenAI-compatible tool-calling trajectories."""

from __future__ import annotations

import copy
import json
import random
import re
import sys
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

import requests

from core.config import DEFAULT_MAX_TOKENS, REACT_MAX_STEPS, LLMConfig
from core.debug_trace import trace_event, trace_log
from core.json_utils import parse_json_with_fallback
from core.llm_client import _record_api_event


_CJK_CHAR_RE = re.compile(
    "["
    "\u3400-\u4DBF"
    "\u4E00-\u9FFF"
    "\uF900-\uFAFF"
    "\U00020000-\U0002A6DF"
    "\U0002A700-\U0002B73F"
    "\U0002B740-\U0002B81F"
    "\U0002B820-\U0002CEAF"
    "\U0002CEB0-\U0002EBEF"
    "\U00030000-\U0003134F"
    "]"
)


def _snapshot_tool_payload(payload: Any) -> Any:
    try:
        return copy.deepcopy(payload)
    except Exception:
        return json.loads(json.dumps(payload, ensure_ascii=False, default=str))


def _retry_delay_seconds(attempt: int) -> float:
    base = min(12.0, 1.2 * (2 ** attempt))
    return base + random.uniform(0.0, 0.35)


def _coerce_message_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""

    parts: List[str] = []
    for item in value:
        if isinstance(item, str):
            parts.append(item)
            continue
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str):
            parts.append(text)
            continue
        nested = item.get("content")
        if isinstance(nested, str):
            parts.append(nested)
    return "".join(parts)


def _extract_reasoning_text(message: Dict[str, Any]) -> Optional[str]:
    if not isinstance(message, dict):
        return None

    direct_reasoning = _coerce_message_text(message.get("reasoning"))
    if direct_reasoning:
        return direct_reasoning

    reasoning_details = message.get("reasoning_details")
    if isinstance(reasoning_details, dict):
        reasoning_details = [reasoning_details]
    if not isinstance(reasoning_details, list):
        return None

    parts: List[str] = []
    for item in reasoning_details:
        if not isinstance(item, dict):
            continue
        text = _coerce_message_text(item.get("text"))
        if not text:
            text = _coerce_message_text(item.get("summary"))
        if text:
            parts.append(text)
    if not parts:
        return None
    return "\n".join(parts)


def _extract_recorded_assistant_output(message: Dict[str, Any]) -> Optional[str]:
    content = _coerce_message_text(message.get("content"))
    if content:
        return content
    return _extract_reasoning_text(message)


def _assistant_message_for_replay(message: Dict[str, Any]) -> Dict[str, Any]:
    replay = _snapshot_tool_payload(message)
    if not isinstance(replay, dict):
        replay = {"role": "assistant", "content": ""}
    role = str(replay.get("role") or "").strip()
    if not role:
        replay["role"] = "assistant"
    return replay


def _assistant_message_for_record(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    recorded = _snapshot_tool_payload(message)
    if not isinstance(recorded, dict):
        return None
    recorded.pop("tool_calls", None)
    role = str(recorded.get("role") or "").strip()
    if not role:
        recorded["role"] = "assistant"
    return recorded


def _repair_tool_call_arguments_string(raw_args: Any) -> Any:
    if not isinstance(raw_args, str):
        return raw_args
    try:
        json.loads(raw_args)
        return raw_args
    except Exception:
        repaired = raw_args + "}"
        try:
            json.loads(repaired)
            return repaired
        except Exception:
            return raw_args


def _strip_cjk_chars(value: Any) -> Any:
    if isinstance(value, str):
        return _CJK_CHAR_RE.sub("", value)
    if isinstance(value, list):
        return [_strip_cjk_chars(item) for item in value]
    if isinstance(value, dict):
        sanitized: Dict[str, Any] = {}
        for key, item in value.items():
            sanitized_key = _strip_cjk_chars(key) if isinstance(key, str) else key
            sanitized[sanitized_key] = _strip_cjk_chars(item)
        return sanitized
    return value


def _contains_cjk_chars(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_CJK_CHAR_RE.search(value))
    if isinstance(value, list):
        return any(_contains_cjk_chars(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_cjk_chars(key) if isinstance(key, str) else False
            for key in value.keys()
        ) or any(_contains_cjk_chars(item) for item in value.values())
    return False


def _strip_string_edges(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_strip_string_edges(item) for item in value]
    if isinstance(value, dict):
        stripped: Dict[str, Any] = {}
        for key, item in value.items():
            stripped_key = key.strip() if isinstance(key, str) else key
            stripped[stripped_key] = _strip_string_edges(item)
        return stripped
    return value


def _model_id_for_family_checks(model_name: Optional[str]) -> str:
    raw = str(model_name or "").strip()
    return raw.rsplit("/", 1)[-1].lower()


def _should_apply_cjk_tool_arg_sanitization(model_name: Optional[str]) -> bool:
    return _model_id_for_family_checks(model_name) == "gemini-3-flash-preview"


def _is_gpt_model(model_name: Optional[str]) -> bool:
    return _model_id_for_family_checks(model_name).startswith("gpt")


def _prepare_tool_call_arguments_for_execution(
    raw_args: Any,
    *,
    enable_cjk_sanitization: bool = False,
) -> Any:
    if isinstance(raw_args, str):
        had_cjk = enable_cjk_sanitization and _contains_cjk_chars(raw_args)
        sanitized = _strip_cjk_chars(raw_args) if enable_cjk_sanitization else raw_args
        repaired = _repair_tool_call_arguments_string(sanitized)
        if had_cjk and isinstance(repaired, str):
            try:
                parsed = json.loads(repaired)
            except Exception:
                return repaired
            return json.dumps(_strip_string_edges(parsed), ensure_ascii=False)
        return repaired

    if not enable_cjk_sanitization:
        return raw_args

    sanitized = _strip_cjk_chars(raw_args)
    if _contains_cjk_chars(raw_args):
        return _strip_string_edges(sanitized)
    return sanitized


def _normalize_message_tool_calls_for_execution(
    message: Dict[str, Any],
    *,
    enable_cjk_sanitization: bool = False,
) -> Dict[str, Any]:
    normalized = _snapshot_tool_payload(message)
    if not isinstance(normalized, dict):
        return {"role": "assistant", "content": ""}

    tool_calls = normalized.get("tool_calls")
    if not isinstance(tool_calls, list):
        return normalized

    repaired_calls: List[Dict[str, Any]] = []
    for tc in tool_calls:
        repaired_tc = _snapshot_tool_payload(tc)
        if not isinstance(repaired_tc, dict):
            repaired_calls.append(tc)
            continue
        fn = repaired_tc.get("function")
        if isinstance(fn, dict):
            fn = _snapshot_tool_payload(fn)
            fn["arguments"] = _prepare_tool_call_arguments_for_execution(
                fn.get("arguments"),
                enable_cjk_sanitization=enable_cjk_sanitization,
            )
            repaired_tc["function"] = fn
        repaired_calls.append(repaired_tc)
    normalized["tool_calls"] = repaired_calls
    return normalized


def _extract_step_assistant_text(step: Dict[str, Any]) -> str:
    message = step.get("assistant_message")
    if isinstance(message, dict):
        text = _extract_recorded_assistant_output(message)
        if text:
            return text
    return str(step.get("assistant_output", "") or "")


def _build_plain_trajectory_text(
    steps: List[Dict[str, Any]],
    final_answer: str,
    status: str,
) -> str:
    lines: List[str] = []
    for step in steps:
        idx = step.get("step")
        lines.append(f"Step {idx}:")
        assistant_output = _extract_step_assistant_text(step).strip()
        if assistant_output:
            lines.append(f"assistant_output: {assistant_output}")
        for call in step.get("tool_calls", []) or []:
            name = str(call.get("name", "") or "")
            arguments = call.get("arguments", {})
            lines.append(f"tool_call: name={name} | arguments={json.dumps(arguments, ensure_ascii=False)}")
        for obs in step.get("tool_responses", []) or []:
            name = str(obs.get("name", "") or "")
            content = obs.get("content")
            lines.append(f"tool_response: name={name} | result={json.dumps(content, ensure_ascii=False)}")
        if isinstance(step.get("error"), str) and step.get("error"):
            lines.append(f"Error: {step.get('error')}")
        lines.append("")

    if final_answer:
        lines.append(f"final_answer: {final_answer}")
    lines.append(f"status: {status}")
    return "\n".join(lines).strip()


class OpenAIToolCallAgent:
    def __init__(
        self,
        llm_config: LLMConfig,
        system_prompt: str,
        task_prompt: str,
        tools: List[Dict[str, Any]],
        tool_executor: Callable[[str, Dict[str, Any], str], Dict[str, Any]],
        max_steps: int = REACT_MAX_STEPS,
        temperature: float = 0.2,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        parallel_tool_calls: Optional[bool] = None,
        n: Optional[int] = None,
        tool_choice: str = "auto",
    ) -> None:
        self.llm_config = llm_config
        self.system_prompt = system_prompt
        self.task_prompt = task_prompt
        self.tools = tools
        self.tool_executor = tool_executor
        self.max_steps = int(max_steps)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.parallel_tool_calls = None if parallel_tool_calls is None else bool(parallel_tool_calls)
        self.n = None if n is None else int(n)
        self.tool_choice = str(tool_choice or "auto").strip() or "auto"

    def _chat_once(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = self.llm_config.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.llm_config.api_key}",
            "Content-Type": "application/json",
            "Connection": "close",
        }
        payload: Dict[str, Any] = {
            "model": self.llm_config.model,
            "messages": messages,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        effective_parallel_tool_calls = self.parallel_tool_calls
        if _model_id_for_family_checks(self.llm_config.model) == "qwen3-30b-a3b":
            effective_parallel_tool_calls = False
        if effective_parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = effective_parallel_tool_calls
        if self.n is not None and _is_gpt_model(self.llm_config.model):
            payload["n"] = self.n

        call_id = uuid.uuid4().hex
        request_trace_payload = {
            "url": url,
            "messages": messages,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "parallel_tool_calls": effective_parallel_tool_calls,
        }
        if "n" in payload:
            request_trace_payload["n"] = payload["n"]
        _record_api_event(
            "request_prepare",
            {
                "call_id": call_id,
                "stream": False,
                "config": {
                    "base_url": self.llm_config.base_url,
                    "model": self.llm_config.model,
                    "timeout_seconds": self.llm_config.timeout_seconds,
                    "max_retries": self.llm_config.max_retries,
                },
                "request": request_trace_payload,
            },
        )

        last_error = ""
        for attempt in range(self.llm_config.max_retries + 1):
            try:
                _record_api_event(
                    "request_attempt_start",
                    {
                        "call_id": call_id,
                        "stream": False,
                        "attempt": attempt + 1,
                        "max_attempts": self.llm_config.max_retries + 1,
                        "url": url,
                        "model": self.llm_config.model,
                    },
                )
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.llm_config.timeout_seconds,
                )
                _record_api_event(
                    "request_attempt_response",
                    {
                        "call_id": call_id,
                        "stream": False,
                        "attempt": attempt + 1,
                        "status_code": resp.status_code,
                        "headers": dict(resp.headers),
                    },
                    raw_text=resp.text,
                )
                if resp.status_code >= 400:
                    last_error = f"HTTP {resp.status_code}: {resp.text}"
                    if attempt < self.llm_config.max_retries:
                        time.sleep(_retry_delay_seconds(attempt))
                        continue
                    result = {"ok": False, "error": last_error, "raw": None, "message": None}
                    _record_api_event(
                        "request_result",
                        {
                            "call_id": call_id,
                            "stream": False,
                            "ok": False,
                            "error": last_error,
                            "content": "",
                            "raw": None,
                        },
                    )
                    return result

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    result = {"ok": False, "error": "No choices in response", "raw": data, "message": None}
                    _record_api_event(
                        "request_result",
                        {
                            "call_id": call_id,
                            "stream": False,
                            "ok": False,
                            "error": "No choices in response",
                            "content": "",
                            "raw": data,
                        },
                    )
                    return result
                if len(choices) > 1:
                    error_message = f"Multiple choices in response: {len(choices)}"
                    result = {"ok": False, "error": error_message, "raw": data, "message": None}
                    _record_api_event(
                        "request_result",
                        {
                            "call_id": call_id,
                            "stream": False,
                            "ok": False,
                            "error": error_message,
                            "content": "",
                            "raw": data,
                        },
                    )
                    return result
                message = choices[0].get("message", {})
                result = {"ok": True, "error": None, "raw": data, "message": message}
                _record_api_event(
                    "request_result",
                    {
                        "call_id": call_id,
                        "stream": False,
                        "ok": True,
                        "error": None,
                        "content": _coerce_message_text(message.get("content")),
                        "raw": data,
                    },
                )
                return result
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                _record_api_event(
                    "request_attempt_exception",
                    {
                        "call_id": call_id,
                        "stream": False,
                        "attempt": attempt + 1,
                        "error": last_error,
                        "error_type": type(exc).__name__,
                    },
                )
                if attempt < self.llm_config.max_retries:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue

        result = {"ok": False, "error": last_error, "raw": None, "message": None}
        _record_api_event(
            "request_result",
            {
                "call_id": call_id,
                "stream": False,
                "ok": False,
                "error": last_error,
                "content": "",
                "raw": None,
            },
        )
        return result

    def _parse_tool_args(self, raw_args: Any) -> Dict[str, Any]:
        enable_cjk_sanitization = _should_apply_cjk_tool_arg_sanitization(self.llm_config.model)
        prepared_args = _prepare_tool_call_arguments_for_execution(
            raw_args,
            enable_cjk_sanitization=enable_cjk_sanitization,
        )
        if isinstance(prepared_args, dict):
            return prepared_args
        if isinstance(prepared_args, str):
            parsed = parse_json_with_fallback(prepared_args, {})
            if isinstance(parsed, dict):
                if enable_cjk_sanitization:
                    return _strip_cjk_chars(parsed)
                return parsed
        return {}

    def run(self) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.task_prompt},
        ]

        run_start_payload = {
            "system_prompt": self.system_prompt,
            "task_prompt": self.task_prompt,
            "tools": self.tools,
            "max_steps": self.max_steps,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tool_choice": self.tool_choice,
            "model": self.llm_config.model,
            "base_url": self.llm_config.base_url,
        }
        if self.n is not None and _is_gpt_model(self.llm_config.model):
            run_start_payload["n"] = self.n
        trace_event(
            "tir_agent_openai",
            "run_start",
            run_start_payload,
            print_message=f"[TRACE][tir_agent_openai][run_start] max_steps={self.max_steps}",
        )
        if self.parallel_tool_calls is not None:
            trace_event(
                "tir_agent_openai",
                "parallel_tool_calls_config",
                {"parallel_tool_calls": self.parallel_tool_calls},
            )

        steps: List[Dict[str, Any]] = []
        trajectory_chunks: List[str] = []
        status = "max_steps"
        final_answer = ""

        last_completed_round_trace = ""
        enable_cjk_sanitization = _should_apply_cjk_tool_arg_sanitization(self.llm_config.model)
        attempt_idx = 0
        while len(steps) < self.max_steps:
            attempt_idx += 1
            step_idx = len(steps) + 1
            trace_log(
                f"[TRAJGEN][STEP] step={step_idx}/{self.max_steps} attempt={attempt_idx} sending_messages={len(messages)}"
            )
            trace_event(
                "tir_agent_openai",
                "step_messages",
                {"step": step_idx, "attempt": attempt_idx, "messages": messages},
                print_message=f"[TRACE][tir_agent_openai][step_messages] step={step_idx} attempt={attempt_idx} messages={len(messages)}",
            )

            resp = self._chat_once(messages)
            if not resp.get("ok"):
                status = "error"
                step_record = {
                    "step": step_idx,
                    "assistant_message": None,
                    "tool_calls": [],
                    "tool_responses": [],
                    "error": resp.get("error", "LLM call failed"),
                }
                steps.append(step_record)
                trace_event(
                    "tir_agent_openai",
                    "step_llm_error",
                    {
                        "step": step_idx,
                        "attempt": attempt_idx,
                        "error": resp.get("error"),
                        "response": resp,
                        "steps_so_far": steps,
                    },
                    print_message=f"[TRACE][tir_agent_openai][step_llm_error] step={step_idx} attempt={attempt_idx} error={resp.get('error')}",
                )
                break

            raw_msg = _snapshot_tool_payload(resp.get("message") or {})
            msg = _normalize_message_tool_calls_for_execution(
                raw_msg,
                enable_cjk_sanitization=enable_cjk_sanitization,
            )
            assistant_content = _coerce_message_text(raw_msg.get("content"))
            recorded_assistant_output = _extract_recorded_assistant_output(raw_msg)
            raw_tool_calls = raw_msg.get("tool_calls") or []
            if not isinstance(raw_tool_calls, list):
                raw_tool_calls = []
            tool_calls = msg.get("tool_calls") or []
            if not isinstance(tool_calls, list):
                tool_calls = []

            has_tool_calls = bool(tool_calls)
            has_visible_content = bool(assistant_content.strip())
            is_empty_round = (not has_tool_calls) and (not has_visible_content)
            assistant_text = assistant_content if has_visible_content else "(empty response)"

            trace_event(
                "tir_agent_openai",
                "step_llm_response",
                {
                    "step": step_idx,
                    "attempt": attempt_idx,
                    "assistant_content": assistant_content,
                    "assistant_message": _assistant_message_for_record(raw_msg),
                    "tool_calls": raw_tool_calls,
                    "raw": resp.get("raw"),
                },
                print_message=f"[TRACE][tir_agent_openai][step_llm_response] step={step_idx} attempt={attempt_idx} tool_calls={len(tool_calls)}",
            )

            if is_empty_round:
                status = "error"
                error_message = "LLM returned an empty response without tool calls or visible content."
                step_record = {
                    "step": step_idx,
                    "assistant_message": _assistant_message_for_record(raw_msg),
                    "tool_calls": [],
                    "tool_responses": [],
                    "error": error_message,
                }
                steps.append(step_record)
                print(f"[TRAJGEN][ERROR] {error_message}", file=sys.stderr, flush=True)
                trace_log(f"[TRAJGEN][ERROR] {error_message}")
                trace_event(
                    "tir_agent_openai",
                    "step_empty_response",
                    {
                        "step": step_idx,
                        "attempt": attempt_idx,
                        "assistant_content": assistant_content,
                        "assistant_message": _assistant_message_for_record(raw_msg),
                        "response": resp,
                        "error": error_message,
                        "steps_so_far": steps,
                    },
                    print_message=f"[TRACE][tir_agent_openai][step_empty_response] step={step_idx} attempt={attempt_idx}",
                )
                break

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
                    tool_args = self._parse_tool_args(fn.get("arguments", {}))

                    step_record["tool_calls"].append(
                        {
                            "id": tc_id,
                            "name": tool_name,
                            "arguments": tool_args,
                        }
                    )

                    try:
                        tool_result = self.tool_executor(tool_name, tool_args, last_completed_round_trace)
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

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": tool_name,
                        "content": json.dumps(tool_result_snapshot, ensure_ascii=False),
                    }
                    messages.append(tool_msg)

                    # Keep trajectory_text compatible with downstream readers.
                    trajectory_chunks.append(
                        f"<tool_call>{json.dumps({'name': tool_name, 'arguments': tool_args}, ensure_ascii=False)}</tool_call>"
                    )
                    trajectory_chunks.append(
                        f"<tool_response>{json.dumps(tool_result_snapshot, ensure_ascii=False)}</tool_response>"
                    )

                    trace_event(
                        "tir_agent_openai",
                        "step_tool_result",
                        {
                            "step": step_idx,
                            "attempt": attempt_idx,
                            "tool_call": {"id": tc_id, "name": tool_name, "arguments": tool_args},
                            "tool_response": tool_result_snapshot,
                        },
                        print_message=f"[TRACE][tir_agent_openai][step_tool_result] step={step_idx} attempt={attempt_idx} tool={tool_name}",
                    )

                steps.append(step_record)
                last_completed_round_trace = recorded_assistant_output
                continue

            # No tool calls => treat as final answer turn.
            messages.append(_assistant_message_for_replay(msg))
            steps.append(step_record)
            final_answer = recorded_assistant_output
            if recorded_assistant_output:
                trajectory_chunks.append(recorded_assistant_output)
            status = "finished"

            trace_event(
                "tir_agent_openai",
                "step_final_answer",
                {
                    "step": step_idx,
                    "attempt": attempt_idx,
                    "assistant_content": assistant_content,
                    "step_record": step_record,
                },
                print_message=f"[TRACE][tir_agent_openai][step_final_answer] step={step_idx} attempt={attempt_idx}",
            )
            break

        result = {
            "status": status,
            "final_answer": final_answer,
            "steps": steps,
            # Keep an explicit plain-text trajectory as the primary output.
            "trajectory_text": _build_plain_trajectory_text(
                steps=steps,
                final_answer=final_answer,
                status=status,
            ),
            # Preserve the raw tag-like running trace for debugging.
            "trajectory_text_raw": "\n".join([x for x in trajectory_chunks if isinstance(x, str) and x != ""]),
        }
        trace_event(
            "tir_agent_openai",
            "run_result",
            result,
            print_message=f"[TRACE][tir_agent_openai][run_result] status={status} step_count={len(steps)}",
        )
        return result
