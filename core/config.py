# -*- coding: utf-8 -*-
"""Shared LLM configuration.

All default credentials and endpoints are intentionally empty. Runtime callers
must provide credentials through environment variables or explicit config files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 120
    max_retries: int = 2
    extra_body: Optional[Dict[str, Any]] = None


DEFAULT_LLM_CONFIG = LLMConfig(
    api_key=os.getenv("VALUEBENCH_API_KEY", ""),
    base_url=os.getenv("VALUEBENCH_BASE_URL", ""),
    model=os.getenv("VALUEBENCH_MODEL", ""),
    timeout_seconds=int(os.getenv("VALUEBENCH_TIMEOUT_SECONDS", "120")),
    max_retries=int(os.getenv("VALUEBENCH_MAX_RETRIES", "2")),
)

DEFAULT_TEMPERATURE = float(os.getenv("VALUEBENCH_TEMPERATURE", "0.3"))
DEFAULT_MAX_TOKENS = int(os.getenv("VALUEBENCH_MAX_TOKENS", "12000"))


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


ENABLE_LEGACY_SCHEMA_INFERENCE = _env_bool("VALUEBENCH_ENABLE_LEGACY_SCHEMA_INFERENCE", False)

REACT_MAX_STEPS = int(os.getenv("VALUEBENCH_REACT_MAX_STEPS", "30"))
