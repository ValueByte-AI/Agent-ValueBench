# -*- coding: utf-8 -*-
"""
Shared LLM API client.

Notes:
- Uses OpenAI-compatible Chat Completions requests.
- Centralizes timeout, retry, and error handling.
- Construction, trajectory, and evaluation modules route API calls through this layer for consistent configuration.
"""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import requests

from .config import DEFAULT_LLM_CONFIG, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, LLMConfig
from .debug_trace import is_enabled, trace_event


_API_LOG_LOCK = threading.Lock()
_API_LOG_DIR: Optional[Path] = None


def _now_utc_text() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _resolve_api_log_dir() -> Optional[Path]:
    global _API_LOG_DIR
    if isinstance(_API_LOG_DIR, Path):
        return _API_LOG_DIR

    enabled_raw = str(os.getenv("VALUEBENCH_API_CALL_LOG_ENABLED", "0")).strip().lower()
    if enabled_raw in {"0", "false", "no"}:
        return None

    raw_dir = str(os.getenv("VALUEBENCH_API_CALL_LOG_DIR", "") or "").strip()
    if raw_dir:
        log_dir = Path(raw_dir).expanduser().resolve()
    else:
        repo_root = Path(__file__).resolve().parents[1]
        log_dir = repo_root / "Debug_Doc" / "api_call_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    _API_LOG_DIR = log_dir
    return log_dir


def _record_api_event(
    event_name: str,
    payload: Dict[str, Any],
    *,
    raw_text: Optional[str] = None,
) -> None:
    try:
        log_dir = _resolve_api_log_dir()
        if log_dir is None:
            return

        with _API_LOG_LOCK:
            event_key = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

        event_file = log_dir / f"{event_key}_{event_name}.json"
        record: Dict[str, Any] = {
            "event_key": event_key,
            "event_name": event_name,
            "timestamp_utc": _now_utc_text(),
            "payload": payload,
        }

        if isinstance(raw_text, str):
            raw_file = log_dir / f"{event_key}_{event_name}_raw.txt"
            raw_file.write_text(raw_text, encoding="utf-8", errors="replace")
            record["raw_text_file"] = str(raw_file)
            record["raw_text_length"] = len(raw_text)

        event_file.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception:
        # never break the main pipeline because of debug logging
        return


def _retry_delay_seconds(attempt: int) -> float:
    # exponential backoff + jitter, capped to keep runtime bounded
    base = min(15.0, 1.2 * (2 ** attempt))
    return base + random.uniform(0.0, 0.35)


def _coerce_stream_text(value: Any) -> str:
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


def _is_gemini_model_name(model: Any) -> bool:
    return "gemini" in str(model or "").strip().lower()


def _should_use_gemini_native_protocol(model: Any, base_url: Any) -> bool:
    if not _is_gemini_model_name(model):
        return False

    base = str(base_url or "").strip()
    if not base:
        return True

    parsed = urlparse(base)
    path = (parsed.path or "").rstrip("/")

    if path.endswith("/chat/completions"):
        return False
    if path.endswith("/v1"):
        return False
    if path.endswith("/v1beta") or not path:
        return True

    return True


def _resolve_gemini_native_base_url(base_url: str) -> str:
    base = str(base_url or "").strip().rstrip("/")
    if not base:
        return "https://generativelanguage.googleapis.com"
    if base.endswith("/v1beta"):
        return base[: -len("/v1beta")]
    return base


def _extract_gemini_parts_text(parts: Any) -> tuple[str, str]:
    content_parts: List[str] = []
    reasoning_parts: List[str] = []

    if isinstance(parts, dict):
        parts = [parts]
    if not isinstance(parts, list):
        return "", ""

    for part in parts:
        if not isinstance(part, dict):
            continue
        text = part.get("text")
        if not isinstance(text, str) or not text:
            continue
        if part.get("thought") is True:
            reasoning_parts.append(text)
        else:
            content_parts.append(text)

    return "".join(content_parts), "".join(reasoning_parts)


def _extract_gemini_candidate_text(candidate: Dict[str, Any]) -> tuple[str, str]:
    if not isinstance(candidate, dict):
        return "", ""
    content = candidate.get("content")
    if not isinstance(content, dict):
        return "", ""
    return _extract_gemini_parts_text(content.get("parts"))


def _extract_stream_choice_text(choice: Dict[str, Any], key: str) -> str:
    if not isinstance(choice, dict):
        return ""

    delta = choice.get("delta")
    if isinstance(delta, dict):
        text = _coerce_stream_text(delta.get(key))
        if text:
            return text

    if key == "content":
        message = choice.get("message")
        if isinstance(message, dict):
            text = _coerce_stream_text(message.get("content"))
            if text:
                return text
        text = _coerce_stream_text(choice.get("text"))
        if text:
            return text

    return ""


def parse_sse_text_stream(lines: List[str]) -> Dict[str, Any]:
    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    parsed_events: List[Dict[str, Any]] = []
    parse_errors: List[Dict[str, str]] = []
    ignored_lines: List[str] = []
    saw_done = False

    for raw_line in lines:
        line = str(raw_line or "")
        if not line.strip():
            continue
        if not line.startswith("data:"):
            ignored_lines.append(line)
            continue

        payload_text = line[len("data:"):].strip()
        if payload_text == "[DONE]":
            saw_done = True
            continue

        try:
            event = json.loads(payload_text)
        except Exception as exc:
            parse_errors.append(
                {
                    "line": line,
                    "payload": payload_text,
                    "error": str(exc),
                }
            )
            continue

        if isinstance(event, dict):
            parsed_events.append(event)
            choices = event.get("choices", [])
            if isinstance(choices, list):
                for choice in choices:
                    if not isinstance(choice, dict):
                        continue
                    content_text = _extract_stream_choice_text(choice, "content")
                    if content_text:
                        content_parts.append(content_text)
                    reasoning_text = _extract_stream_choice_text(choice, "reasoning_content")
                    if reasoning_text:
                        reasoning_parts.append(reasoning_text)
            candidates = event.get("candidates", [])
            if isinstance(candidates, list):
                for candidate in candidates:
                    content_text, reasoning_text = _extract_gemini_candidate_text(candidate)
                    if content_text:
                        content_parts.append(content_text)
                    if reasoning_text:
                        reasoning_parts.append(reasoning_text)

    return {
        "content": "".join(content_parts),
        "reasoning_content": "".join(reasoning_parts),
        "parsed_events": parsed_events,
        "parse_errors": parse_errors,
        "ignored_lines": ignored_lines,
        "saw_done": saw_done,
    }


class UnifiedLLMClient:
    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        self.config = config or DEFAULT_LLM_CONFIG
        disable_proxy_raw = str(os.getenv("VALUEBENCH_DISABLE_SYSTEM_PROXY", "0")).strip().lower()
        self.disable_system_proxy = disable_proxy_raw in {"1", "true", "yes"}
        self.proxies_override: Optional[Dict[str, str]] = (
            {"http": "", "https": ""} if self.disable_system_proxy else None
        )

    def _use_gemini_native_protocol(self) -> bool:
        return _should_use_gemini_native_protocol(self.config.model, self.config.base_url)

    @staticmethod
    def _normalize_message_content(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        return str(content)

    def _build_gemini_native_contents(
        self,
        messages: List[Dict[str, str]],
    ) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        system_chunks: List[str] = []
        contents: List[Dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "user") or "user").strip().lower()
            text = self._normalize_message_content(message.get("content"))
            if not text:
                continue
            if role == "system":
                system_chunks.append(text)
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(
                {
                    "role": gemini_role,
                    "parts": [{"text": text}],
                }
            )

        if not contents:
            contents = [{"role": "user", "parts": [{"text": ""}]}]

        system_instruction: Optional[Dict[str, Any]] = None
        if system_chunks:
            system_instruction = {
                "parts": [{"text": "\n\n".join(system_chunks)}],
            }
        return system_instruction, contents

    def _build_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]],
        *,
        stream: bool = False,
    ) -> tuple[str, Dict[str, str], Dict[str, Any]]:
        api_key = str(self.config.api_key or "").strip()
        model = str(self.config.model or "").strip()
        base_url = str(self.config.base_url or "").strip()
        if not api_key:
            raise ValueError("Missing API key. Set VALUEBENCH_API_KEY or provide api_key in the API configuration.")
        if not model:
            raise ValueError("Missing model. Set VALUEBENCH_MODEL or pass a model through the caller configuration.")

        use_gemini_native = _should_use_gemini_native_protocol(model, base_url)
        if use_gemini_native:
            native_base_url = _resolve_gemini_native_base_url(base_url)
            model_name = quote(model, safe="")
            action = "streamGenerateContent?alt=sse" if stream else "generateContent"
            url = f"{native_base_url}/v1beta/models/{model_name}:{action}"
            headers = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
                "Connection": "close",
            }
            system_instruction, contents = self._build_gemini_native_contents(messages)
            generation_config: Dict[str, Any] = {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
            if isinstance(response_format, dict) and response_format.get("type") == "json_object":
                generation_config["responseMimeType"] = "application/json"

            payload = {
                "contents": contents,
                "generationConfig": generation_config,
            }
            if system_instruction is not None:
                payload["system_instruction"] = system_instruction
            return url, headers, payload

        if not base_url:
            raise ValueError("Missing base_url for OpenAI-compatible chat completions.")
        url = base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Connection": "close",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if isinstance(self.config.extra_body, dict) and self.config.extra_body:
            payload.update(self.config.extra_body)
        if response_format is not None:
            payload["response_format"] = response_format
        if stream:
            payload["stream"] = True
        return url, headers, payload

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call the chat endpoint and return a structured result.

        Return format:
        {
          "ok": bool,
          "content": str,
          "raw": dict|None,
          "error": str|None
        }
        """
        use_gemini_native = self._use_gemini_native_protocol()
        url, headers, payload = self._build_request(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
        call_id = f"chat_{uuid.uuid4().hex[:12]}"

        last_error = ""
        _record_api_event(
            "request_prepare",
            {
                "call_id": call_id,
                "stream": False,
                "config": {
                    "base_url": self.config.base_url,
                    "model": self.config.model,
                    "timeout_seconds": self.config.timeout_seconds,
                    "max_retries": self.config.max_retries,
                    "disable_system_proxy": self.disable_system_proxy,
                },
                "request": {
                    "url": url,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": response_format,
                    "extra_body": self.config.extra_body,
                    "messages": messages,
                },
            },
        )
        if is_enabled():
            trace_event(
                "llm",
                "request_prepare",
                {
                    "config": {
                        "base_url": self.config.base_url,
                        "model": self.config.model,
                        "timeout_seconds": self.config.timeout_seconds,
                        "max_retries": self.config.max_retries,
                        "disable_system_proxy": self.disable_system_proxy,
                    },
                    "request": {
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "response_format": response_format,
                        "extra_body": self.config.extra_body,
                        "url": url,
                    },
                },
                print_message=f"[TRACE][llm][request_prepare] model={self.config.model} messages={len(messages)}",
            )
        for attempt in range(self.config.max_retries + 1):
            try:
                if is_enabled():
                    trace_event(
                        "llm",
                        "request_attempt_start",
                        {
                            "attempt": attempt + 1,
                            "max_attempts": self.config.max_retries + 1,
                            "url": url,
                            "model": self.config.model,
                        },
                        print_message=f"[TRACE][llm][request_attempt_start] model={self.config.model} attempt={attempt + 1}/{self.config.max_retries + 1}",
                    )
                _record_api_event(
                    "request_attempt_start",
                    {
                        "call_id": call_id,
                        "stream": False,
                        "attempt": attempt + 1,
                        "max_attempts": self.config.max_retries + 1,
                        "url": url,
                        "model": self.config.model,
                    },
                )
                request_kwargs: Dict[str, Any] = {
                    "timeout": self.config.timeout_seconds,
                }
                if self.proxies_override is not None:
                    request_kwargs["proxies"] = self.proxies_override
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    **request_kwargs,
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
                if is_enabled():
                    trace_event(
                        "llm",
                        "request_attempt_response",
                        {
                            "attempt": attempt + 1,
                            "status_code": resp.status_code,
                            "text": resp.text,
                        },
                        print_message=f"[TRACE][llm][request_attempt_response] model={self.config.model} attempt={attempt + 1} status={resp.status_code}",
                    )
                if resp.status_code >= 400:
                    last_error = f"HTTP {resp.status_code}: {resp.text}"
                    if attempt < self.config.max_retries:
                        time.sleep(_retry_delay_seconds(attempt))
                        continue
                    result = {"ok": False, "content": "", "raw": None, "error": last_error}
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
                    if is_enabled():
                        trace_event("llm", "request_result", result, print_message=f"[TRACE][llm][request_result] ok=0 error={last_error}")
                    return result

                data = resp.json()
                if use_gemini_native:
                    candidates = data.get("candidates", [])
                    if not candidates:
                        result = {"ok": False, "content": "", "raw": data, "error": "No candidates in response"}
                        _record_api_event(
                            "request_result",
                            {
                                "call_id": call_id,
                                "stream": False,
                                "ok": False,
                                "error": "No candidates in response",
                                "content": "",
                                "raw": data,
                            },
                        )
                        if is_enabled():
                            trace_event("llm", "request_result", result, print_message="[TRACE][llm][request_result] ok=0 error=No candidates in response")
                        return result
                    content, reasoning = _extract_gemini_candidate_text(candidates[0])
                    if reasoning and not content:
                        content = reasoning
                else:
                    choices = data.get("choices", [])
                    if not choices:
                        result = {"ok": False, "content": "", "raw": data, "error": "No choices in response"}
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
                        if is_enabled():
                            trace_event("llm", "request_result", result, print_message="[TRACE][llm][request_result] ok=0 error=No choices in response")
                        return result

                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    if content is None:
                        content = ""
                result = {"ok": True, "content": str(content), "raw": data, "error": None}
                _record_api_event(
                    "request_result",
                    {
                        "call_id": call_id,
                        "stream": False,
                        "ok": True,
                        "error": None,
                        "content": str(content),
                        "raw": data,
                    },
                )
                if is_enabled():
                    trace_event(
                        "llm",
                        "request_result",
                        result,
                        print_message=f"[TRACE][llm][request_result] ok=1 model={self.config.model}",
                    )
                return result
            except Exception as exc:
                last_error = str(exc)
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
                if is_enabled():
                    trace_event(
                        "llm",
                        "request_attempt_exception",
                        {
                            "attempt": attempt + 1,
                            "error": last_error,
                            "error_type": type(exc).__name__,
                        },
                        print_message=f"[TRACE][llm][request_attempt_exception] model={self.config.model} attempt={attempt + 1} error={last_error}",
                    )
                if attempt < self.config.max_retries:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue

        result = {"ok": False, "content": "", "raw": None, "error": last_error}
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
        if is_enabled():
            trace_event("llm", "request_result", result, print_message=f"[TRACE][llm][request_result] ok=0 error={last_error}")
        return result

    def chat_stream_collect(
        self,
        messages: List[Dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        use_gemini_native = self._use_gemini_native_protocol()
        url, headers, payload = self._build_request(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            stream=True,
        )
        call_id = f"stream_{uuid.uuid4().hex[:12]}"
        effective_timeout = int(timeout_seconds or self.config.timeout_seconds)

        last_error = ""
        _record_api_event(
            "stream_request_prepare",
            {
                "call_id": call_id,
                "stream": True,
                "config": {
                    "base_url": self.config.base_url,
                    "model": self.config.model,
                    "timeout_seconds": self.config.timeout_seconds,
                    "max_retries": self.config.max_retries,
                },
                "request": {
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": response_format,
                    "timeout_seconds": effective_timeout,
                    "url": url,
                    "stream": True,
                },
            },
        )
        if is_enabled():
            trace_event(
                "llm",
                "stream_request_prepare",
                {
                    "config": {
                        "base_url": self.config.base_url,
                        "model": self.config.model,
                        "timeout_seconds": self.config.timeout_seconds,
                        "max_retries": self.config.max_retries,
                    },
                    "request": {
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "response_format": response_format,
                        "timeout_seconds": effective_timeout,
                        "url": url,
                        "stream": True,
                    },
                },
                print_message=f"[TRACE][llm][stream_request_prepare] model={self.config.model} messages={len(messages)}",
            )

        for attempt in range(self.config.max_retries + 1):
            try:
                if is_enabled():
                    trace_event(
                        "llm",
                        "stream_request_attempt_start",
                        {
                            "attempt": attempt + 1,
                            "max_attempts": self.config.max_retries + 1,
                            "url": url,
                            "model": self.config.model,
                            "timeout_seconds": effective_timeout,
                        },
                        print_message=f"[TRACE][llm][stream_request_attempt_start] model={self.config.model} attempt={attempt + 1}/{self.config.max_retries + 1}",
                    )
                _record_api_event(
                    "stream_request_attempt_start",
                    {
                        "call_id": call_id,
                        "stream": True,
                        "attempt": attempt + 1,
                        "max_attempts": self.config.max_retries + 1,
                        "url": url,
                        "model": self.config.model,
                        "timeout_seconds": effective_timeout,
                    },
                )

                started = time.monotonic()
                request_kwargs: Dict[str, Any] = {
                    "timeout": effective_timeout,
                    "stream": True,
                }
                if self.proxies_override is not None:
                    request_kwargs["proxies"] = self.proxies_override
                with requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    **request_kwargs,
                ) as resp:
                    if resp.status_code >= 400:
                        error_text = resp.text
                        elapsed_sec = round(time.monotonic() - started, 4)
                        _record_api_event(
                            "stream_request_attempt_response",
                            {
                                "call_id": call_id,
                                "stream": True,
                                "attempt": attempt + 1,
                                "status_code": resp.status_code,
                                "elapsed_sec": elapsed_sec,
                                "headers": dict(resp.headers),
                            },
                            raw_text=error_text,
                        )
                        if is_enabled():
                            trace_event(
                                "llm",
                                "stream_request_attempt_response",
                                {
                                    "attempt": attempt + 1,
                                    "status_code": resp.status_code,
                                    "elapsed_sec": elapsed_sec,
                                    "error_text": error_text,
                                },
                                print_message=f"[TRACE][llm][stream_request_attempt_response] model={self.config.model} attempt={attempt + 1} status={resp.status_code}",
                            )
                        last_error = f"HTTP {resp.status_code}: {error_text}"
                        if attempt < self.config.max_retries:
                            time.sleep(_retry_delay_seconds(attempt))
                            continue
                        result = {"ok": False, "content": "", "raw": None, "error": last_error}
                        _record_api_event(
                            "stream_request_result",
                            {
                                "call_id": call_id,
                                "stream": True,
                                "ok": False,
                                "error": last_error,
                                "content": "",
                                "raw": None,
                            },
                        )
                        if is_enabled():
                            trace_event(
                                "llm",
                                "stream_request_result",
                                result,
                                print_message=f"[TRACE][llm][stream_request_result] ok=0 error={last_error}",
                            )
                        return result

                    raw_lines: List[str] = []
                    for raw_line in resp.iter_lines(decode_unicode=True):
                        if raw_line is None:
                            continue
                        raw_lines.append(str(raw_line))

                elapsed_sec = round(time.monotonic() - started, 4)
                stream_payload = parse_sse_text_stream(raw_lines)
                raw = {
                    "status_code": 200,
                    "elapsed_sec": elapsed_sec,
                    "sse_line_count": len(raw_lines),
                    "sse_lines": raw_lines,
                    "stream_payload": stream_payload,
                }
                _record_api_event(
                    "stream_request_attempt_response",
                    {
                        "call_id": call_id,
                        "stream": True,
                        "attempt": attempt + 1,
                        "status_code": 200,
                        "elapsed_sec": elapsed_sec,
                        "sse_line_count": len(raw_lines),
                        "content_length": len(stream_payload.get("content", "")),
                        "reasoning_length": len(stream_payload.get("reasoning_content", "")),
                        "saw_done": bool(stream_payload.get("saw_done", False)),
                        "parse_error_count": len(stream_payload.get("parse_errors", [])),
                    },
                    raw_text="\n".join(raw_lines),
                )
                if is_enabled():
                    trace_event(
                        "llm",
                        "stream_request_attempt_response",
                        {
                            "attempt": attempt + 1,
                            "status_code": 200,
                            "elapsed_sec": elapsed_sec,
                            "sse_line_count": len(raw_lines),
                            "content_length": len(stream_payload.get("content", "")),
                            "reasoning_length": len(stream_payload.get("reasoning_content", "")),
                            "saw_done": bool(stream_payload.get("saw_done", False)),
                            "parse_error_count": len(stream_payload.get("parse_errors", [])),
                            "sse_lines": raw_lines,
                        },
                        print_message=f"[TRACE][llm][stream_request_attempt_response] model={self.config.model} attempt={attempt + 1} status=200 stream_lines={len(raw_lines)}",
                    )
                result = {
                    "ok": True,
                    "content": str(stream_payload.get("content", "")),
                    "raw": raw,
                    "error": None,
                }
                _record_api_event(
                    "stream_request_result",
                    {
                        "call_id": call_id,
                        "stream": True,
                        "ok": True,
                        "error": None,
                        "content": str(stream_payload.get("content", "")),
                        "raw": raw,
                    },
                )
                if is_enabled():
                    trace_event(
                        "llm",
                        "stream_request_result",
                        result,
                        print_message=f"[TRACE][llm][stream_request_result] ok=1 model={self.config.model}",
                    )
                return result
            except Exception as exc:
                last_error = str(exc)
                _record_api_event(
                    "stream_request_attempt_exception",
                    {
                        "call_id": call_id,
                        "stream": True,
                        "attempt": attempt + 1,
                        "error": last_error,
                        "error_type": type(exc).__name__,
                    },
                )
                if is_enabled():
                    trace_event(
                        "llm",
                        "stream_request_attempt_exception",
                        {
                            "attempt": attempt + 1,
                            "error": last_error,
                            "error_type": type(exc).__name__,
                        },
                        print_message=f"[TRACE][llm][stream_request_attempt_exception] model={self.config.model} attempt={attempt + 1} error={last_error}",
                    )
                if attempt < self.config.max_retries:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue

        result = {"ok": False, "content": "", "raw": None, "error": last_error}
        _record_api_event(
            "stream_request_result",
            {
                "call_id": call_id,
                "stream": True,
                "ok": False,
                "error": last_error,
                "content": "",
                "raw": None,
            },
        )
        if is_enabled():
            trace_event(
                "llm",
                "stream_request_result",
                result,
                print_message=f"[TRACE][llm][stream_request_result] ok=0 error={last_error}",
            )
        return result

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    def chat_text_stream_collect(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat_stream_collect(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            timeout_seconds=timeout_seconds,
        )
