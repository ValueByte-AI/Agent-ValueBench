# -*- coding: utf-8 -*-
"""Lightweight debug trace utilities for local run instrumentation."""

from __future__ import annotations

import inspect
import json
import os
import re
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {
    "dir": None,
    "stdout": True,
    "counter": 0,
    "session_started": False,
}


def _utc_now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _slug(text: str, default: str = "event") -> str:
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "_", str(text or "").strip())
    normalized = normalized.strip("._-")
    return normalized[:80] if normalized else default


def _ensure_state_from_env() -> Optional[Path]:
    if isinstance(_STATE.get("dir"), Path):
        return _STATE["dir"]

    raw_dir = str(os.getenv("VALUEBENCH_DEBUG_TRACE_DIR", "") or "").strip()
    if not raw_dir:
        return None

    trace_dir = Path(raw_dir).expanduser().resolve()
    trace_dir.mkdir(parents=True, exist_ok=True)
    _STATE["dir"] = trace_dir
    _STATE["stdout"] = str(os.getenv("VALUEBENCH_DEBUG_TRACE_STDOUT", "1")).strip() not in {"0", "false", "False"}
    return trace_dir


def is_enabled() -> bool:
    return _ensure_state_from_env() is not None


def get_trace_dir() -> Optional[Path]:
    return _ensure_state_from_env()


def _append_index(record: Dict[str, Any]) -> None:
    trace_dir = _ensure_state_from_env()
    if trace_dir is None:
        return
    index_path = trace_dir / "trace_index.jsonl"
    with index_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _caller_info() -> Dict[str, Any]:
    internal_suffixes = (
        "core/debug_trace.py",
        "core/llm_client.py",
        "core/json_utils.py",
    )
    try:
        for frame in inspect.stack()[2:]:
            filename = str(frame.filename)
            if any(filename.endswith(suffix) for suffix in internal_suffixes):
                continue
            return {
                "file": filename,
                "line": int(frame.lineno),
                "function": str(frame.function),
            }
    except Exception:
        pass
    return {}


def enable_trace(trace_dir: Path, *, metadata: Optional[Dict[str, Any]] = None, stdout: bool = True) -> Path:
    resolved = trace_dir.expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    os.environ["VALUEBENCH_DEBUG_TRACE_DIR"] = str(resolved)
    os.environ["VALUEBENCH_DEBUG_TRACE_STDOUT"] = "1" if stdout else "0"
    _STATE["dir"] = resolved
    _STATE["stdout"] = bool(stdout)

    if not _STATE.get("session_started", False):
        _STATE["session_started"] = True
        trace_event(
            "session",
            "start",
            {
                "metadata": metadata or {},
            },
            print_message=f"[TRACE][session][start] dir={resolved}",
        )
    elif metadata:
        trace_event("session", "metadata", {"metadata": metadata})
    return resolved


def trace_log(message: str) -> None:
    if not is_enabled():
        return
    if bool(_STATE.get("stdout", True)):
        print(message, flush=True)


def trace_event(
    category: str,
    name: str,
    payload: Any,
    *,
    print_message: Optional[str] = None,
) -> Optional[str]:
    trace_dir = _ensure_state_from_env()
    if trace_dir is None:
        return None

    with _LOCK:
        _STATE["counter"] = int(_STATE.get("counter", 0)) + 1
        event_id = int(_STATE["counter"])

    filename = f"{event_id:05d}_{_slug(category)}_{_slug(name)}.json"
    path = trace_dir / filename
    record = {
        "event_id": event_id,
        "category": str(category),
        "name": str(name),
        "timestamp": _utc_now_text(),
        "caller": _caller_info(),
        "payload": payload,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _append_index(
        {
            "event_id": event_id,
            "category": str(category),
            "name": str(name),
            "timestamp": record["timestamp"],
            "file": str(path),
        }
    )

    if bool(_STATE.get("stdout", True)):
        print(print_message or f"[TRACE][{category}][{name}] file={path}", flush=True)
    return str(path)


def trace_exception(
    category: str,
    name: str,
    exc: BaseException,
    *,
    context: Optional[Dict[str, Any]] = None,
    print_message: Optional[str] = None,
) -> Optional[str]:
    payload = {
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "context": context or {},
    }
    return trace_event(
        category,
        name,
        payload,
        print_message=print_message or f"[TRACE][{category}][{name}] error={type(exc).__name__}: {exc}",
    )
