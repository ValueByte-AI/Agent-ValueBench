# -*- coding: utf-8 -*-
"""JSON parsing helpers with fallback extraction."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from .debug_trace import is_enabled, trace_event

def extract_json_candidate(text: str) -> Optional[str]:
    """
    Extract a likely JSON fragment from model output text.

    Supported cases:
    1. fenced JSON block;
    2. direct JSON output;
    3. mixed text with the first {...} or [...] fragment.
    """
    if not text:
        return None

    text = text.strip()

    fence_pattern = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
    m = fence_pattern.search(text)
    if m:
        return m.group(1).strip()

    # Try object first, then array, so {"a":[...]} is not truncated to [...].
    for left, right in [("{", "}"), ("[", "]")]:
        start = text.find(left)
        end = text.rfind(right)
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()

    return None


def parse_json_with_fallback(text: str, fallback: Any) -> Any:
    """
    Parse JSON and return fallback when parsing fails.

    This is the shared fallback path for JSON-only model outputs.
    """
    raw_text = text or ""
    try:
        result = json.loads(raw_text)
        if is_enabled():
            trace_event(
                "json_parse",
                "direct_success",
                {
                    "raw_text": raw_text,
                    "fallback": fallback,
                    "result": result,
                },
            )
        return result
    except Exception:
        pass

    candidate = extract_json_candidate(raw_text) or raw_text
    try:
        result = json.loads(candidate)
        if is_enabled():
            trace_event(
                "json_parse",
                "candidate_success",
                {
                    "raw_text": raw_text,
                    "candidate": candidate,
                    "fallback": fallback,
                    "result": result,
                },
            )
        return result
    except Exception:
        if is_enabled():
            trace_event(
                "json_parse",
                "fallback",
                {
                    "raw_text": raw_text,
                    "candidate": candidate,
                    "fallback": fallback,
                },
            )
        return fallback
