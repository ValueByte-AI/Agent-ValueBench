"""Call LLM with unified API settings."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from utils.recovery import RecoverableAPIError

load_dotenv()

# Default single-API settings used when no environment override is set.
DEFAULT_API_KEY = ""
DEFAULT_BASE_URL = ""
DEFAULT_MODEL = ""


@dataclass(frozen=True)
class LLMApiProfile:
    """One OpenAI-compatible API profile."""

    name: str
    api_key: str
    base_url: str | None = None
    default_model: str | None = None


_CURRENT_API_PROFILE: ContextVar[LLMApiProfile | None] = ContextVar(
    "valuebench_current_api_profile",
    default=None,
)


def get_current_api_profile() -> LLMApiProfile | None:
    """Return the API profile bound to the current execution context."""
    return _CURRENT_API_PROFILE.get()


@contextmanager
def use_api_profile(profile: LLMApiProfile | None) -> Iterator[None]:
    """Temporarily bind an API profile to the current execution context."""
    token = _CURRENT_API_PROFILE.set(profile)
    try:
        yield
    finally:
        _CURRENT_API_PROFILE.reset(token)


def _resolve_api_key(profile: LLMApiProfile | None = None) -> str:
    if profile and profile.api_key:
        return profile.api_key
    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("VALUEBENCH_API_KEY")
        or DEFAULT_API_KEY
    )
    if not api_key:
        raise ValueError(
            "Missing API key. Set OPENAI_API_KEY, VALUEBENCH_API_KEY, or "
            "provide api_key_env in the multi-API profile config."
        )
    return api_key


def _resolve_base_url(profile: LLMApiProfile | None = None) -> str:
    if profile and profile.base_url:
        return profile.base_url
    return (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("VALUEBENCH_BASE_URL")
        or DEFAULT_BASE_URL
    )


def _resolve_model(model: str, profile: LLMApiProfile | None = None) -> str:
    if isinstance(model, str) and model.strip():
        return model
    if profile and isinstance(profile.default_model, str) and profile.default_model.strip():
        return profile.default_model
    resolved = os.getenv("VALUEBENCH_MODEL", DEFAULT_MODEL).strip()
    if resolved:
        return resolved
    raise ValueError(
        "Missing model. Pass a model argument, set profile.default_model, "
        "or set VALUEBENCH_MODEL."
    )


@lru_cache(maxsize=32)
def _get_openai_client(api_key: str, base_url: str) -> OpenAI:
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def llm_inference(
    provider: str,
    model: str,
    messages: List[dict],
    temperature: float = None,
    stop_strs: Optional[List[str]] = None,
    max_tokens: int = None,
    raise_on_failure: bool = False,
):
    """Call LLM with different providers."""
    if provider == "openai":
        return openai_llm_inference(
            model,
            messages,
            temperature,
            stop_strs,
            max_tokens,
            raise_on_failure=raise_on_failure,
        )
    raise ValueError(f"Invalid provider: {provider}")


def openai_llm_inference(
    model: str,
    messages: List[dict],
    temperature: float = None,
    stop_strs: Optional[List[str]] = None,
    max_tokens: int = None,
    raise_on_failure: bool = False,
):
    """Call OpenAI-compatible LLM API with retry mechanism."""
    profile = get_current_api_profile()
    api_key = _resolve_api_key(profile)
    base_url = _resolve_base_url(profile)
    client = _get_openai_client(
        api_key,
        base_url,
    )
    model = _resolve_model(model, profile)
    profile_name = profile.name if profile else "default"

    retries = 0
    max_retries = 5
    last_exc: Exception | None = None
    while retries < max_retries:
        try:
            _maybe_inject_test_failure(
                operation="chat",
                provider="openai",
                model=model,
                profile_name=profile_name,
                base_url=base_url,
            )
            if "gpt-5" in model:
                response = client.responses.create(
                    model=model,
                    input=messages,
                )
                return response.output_text
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stop=stop_strs,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as exc:
            last_exc = exc
            wait_seconds = retries * 10 + 10
            if isinstance(exc, RecoverableAPIError) and exc.original_type == "SimulatedFailure":
                wait_seconds = 0
            print(
                f"[LLM Retry] profile={profile_name} model={model} "
                f"retry={retries + 1}/{max_retries} error={exc} "
                f"wait_seconds={wait_seconds}"
            )
            time.sleep(wait_seconds)
            retries += 1

    recoverable = _build_recoverable_api_error(
        provider="openai",
        model=model,
        profile_name=profile_name,
        base_url=base_url,
        exc=last_exc,
    )
    print(
        f"[LLM Blocked] profile={profile_name} model={model} "
        f"kind={recoverable.kind} message={recoverable.message}"
    )
    if raise_on_failure:
        raise recoverable
    print(f"Failed to get response after {max_retries} retries, return empty string")
    return ""


def openai_single_embedding_inference(
    model: str,
    text: str,
    *,
    raise_on_failure: bool = False,
) -> List[float]:
    """Get embedding for a single text using OpenAI-compatible API."""
    profile = get_current_api_profile()
    api_key = _resolve_api_key(profile)
    base_url = _resolve_base_url(profile)
    client = _get_openai_client(
        api_key,
        base_url,
    )
    model = _resolve_model(model, profile)
    profile_name = profile.name if profile else "default"

    retries = 0
    max_retries = 5
    last_exc: Exception | None = None
    while retries < max_retries:
        try:
            _maybe_inject_test_failure(
                operation="embedding_single",
                provider="openai",
                model=model,
                profile_name=profile_name,
                base_url=base_url,
            )
            response = client.embeddings.create(
                model=model,
                input=text,
            )
            return response.data[0].embedding
        except KeyboardInterrupt:
            print("Operation canceled by user.")
            break
        except Exception as exc:
            last_exc = exc
            wait_seconds = retries * 10 + 10
            if isinstance(exc, RecoverableAPIError) and exc.original_type == "SimulatedFailure":
                wait_seconds = 0
            print(
                f"[Embedding Retry] profile={profile_name} model={model} "
                f"retry={retries + 1}/{max_retries} error={exc} "
                f"wait_seconds={wait_seconds}"
            )
            time.sleep(wait_seconds)
            retries += 1
    recoverable = _build_recoverable_api_error(
        provider="openai",
        model=model,
        profile_name=profile_name,
        base_url=base_url,
        exc=last_exc,
    )
    print(
        f"[Embedding Blocked] profile={profile_name} model={model} "
        f"kind={recoverable.kind} message={recoverable.message}"
    )
    if raise_on_failure:
        raise recoverable
    print(f"Failed to get embedding after {max_retries} retries, return empty list")
    return []


def openai_batch_embedding_inference(
    model: str,
    texts: List[str],
    *,
    raise_on_failure: bool = False,
) -> List[List[float]]:
    """Get embeddings for multiple texts using OpenAI-compatible API."""
    profile = get_current_api_profile()
    api_key = _resolve_api_key(profile)
    base_url = _resolve_base_url(profile)
    client = _get_openai_client(
        api_key,
        base_url,
    )
    model = _resolve_model(model, profile)
    profile_name = profile.name if profile else "default"

    retries = 0
    max_retries = 5
    last_exc: Exception | None = None
    while retries < max_retries:
        try:
            _maybe_inject_test_failure(
                operation="embedding_batch",
                provider="openai",
                model=model,
                profile_name=profile_name,
                base_url=base_url,
            )
            response = client.embeddings.create(
                model=model,
                input=texts,
            )
            return [d.embedding for d in response.data]
        except Exception as exc:
            last_exc = exc
            wait_seconds = retries * 10 + 10
            if isinstance(exc, RecoverableAPIError) and exc.original_type == "SimulatedFailure":
                wait_seconds = 0
            print(
                f"[Embedding Retry] profile={profile_name} model={model} "
                f"retry={retries + 1}/{max_retries} error={exc} "
                f"wait_seconds={wait_seconds}"
            )
            time.sleep(wait_seconds)
            retries += 1
    recoverable = _build_recoverable_api_error(
        provider="openai",
        model=model,
        profile_name=profile_name,
        base_url=base_url,
        exc=last_exc,
    )
    print(
        f"[Embedding Blocked] profile={profile_name} model={model} "
        f"kind={recoverable.kind} message={recoverable.message}"
    )
    if raise_on_failure:
        raise recoverable
    print(f"Failed to get embeddings after {max_retries} retries, return empty list")
    return []


_FAILURE_COUNTS: Dict[str, int] = {}
_FAILURE_MATCH_COUNTS: Dict[str, int] = {}


def _resolve_failure_rules_file(rules_file: str) -> Path:
    path = Path(rules_file).expanduser()
    if path.is_absolute():
        return path

    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return cwd_candidate

    envscaler_root = Path(__file__).resolve().parents[2]
    root_candidate = envscaler_root / path
    if root_candidate.exists():
        return root_candidate

    return cwd_candidate


def _load_failure_rules() -> List[Dict[str, Any]]:
    rules_text = os.getenv("VALUEBENCH_SIMULATED_API_FAILURES", "").strip()
    rules_file = os.getenv("VALUEBENCH_SIMULATED_API_FAILURES_FILE", "").strip()
    if rules_file:
        try:
            resolved_path = _resolve_failure_rules_file(rules_file)
            with open(resolved_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return []
    if not rules_text:
        return []
    try:
        return json.loads(rules_text)
    except Exception:
        return []


def _maybe_inject_test_failure(
    *,
    operation: str,
    provider: str,
    model: str,
    profile_name: str,
    base_url: str,
) -> None:
    rules = _load_failure_rules()
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        if str(rule.get("profile_name", "") or "").strip() not in ("", profile_name):
            continue
        if str(rule.get("operation", "") or "").strip() not in ("", operation):
            continue
        model_contains = str(rule.get("model_contains", "") or "").strip()
        if model_contains and model_contains not in model:
            continue
        remaining = int(rule.get("times", 1))
        start_after = max(0, int(rule.get("start_after", 0) or 0))
        hit_key = f"{idx}:{profile_name}:{operation}:{model}"
        matched = _FAILURE_MATCH_COUNTS.get(hit_key, 0) + 1
        _FAILURE_MATCH_COUNTS[hit_key] = matched
        if matched <= start_after:
            continue
        used = _FAILURE_COUNTS.get(hit_key, 0)
        if used >= remaining:
            continue
        _FAILURE_COUNTS[hit_key] = used + 1
        raise RecoverableAPIError(
            provider=provider,
            model=model,
            profile_name=profile_name,
            base_url=base_url,
            kind=str(rule.get("kind", "quota_or_balance") or "quota_or_balance"),
            message=str(rule.get("message", "Simulated API failure") or "Simulated API failure"),
            original_type="SimulatedFailure",
        )


def _classify_exception(exc: Exception | None) -> str:
    if exc is None:
        return "unknown"
    exc_type = type(exc).__name__.lower()
    message = str(exc).lower()
    if "authentication" in exc_type or "auth" in message or "invalid api key" in message:
        return "auth"
    if "timeout" in exc_type or "timed out" in message:
        return "timeout"
    if "connection" in exc_type or "network" in message or "dns" in message:
        return "network"
    if "rate" in exc_type or "quota" in message or "insufficient" in message or "credit" in message or "balance" in message or "429" in message:
        return "quota_or_balance"
    return "unknown"


def _build_recoverable_api_error(
    *,
    provider: str,
    model: str,
    profile_name: str,
    base_url: str,
    exc: Exception | None,
) -> RecoverableAPIError:
    return RecoverableAPIError(
        provider=provider,
        model=model,
        profile_name=profile_name,
        base_url=base_url,
        kind=_classify_exception(exc),
        message=str(exc or "Unknown API failure"),
        original_type=type(exc).__name__ if exc is not None else "",
    )
