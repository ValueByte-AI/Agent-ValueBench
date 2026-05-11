"""Utilities for shard-based multi-API execution."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from utils.call_llm import LLMApiProfile
from utils.process_file import read_file


DISPATCH_INDEX_FIELD = "__dispatch_index__"


def _resolve_profile_value(raw_profile: Dict[str, Any], key: str) -> str:
    value = str(raw_profile.get(key, "") or "").strip()
    return value


def _resolve_profile_env(raw_profile: Dict[str, Any], key: str) -> str:
    env_name = _resolve_profile_value(raw_profile, key)
    if not env_name:
        return ""
    return str(os.getenv(env_name, "") or "").strip()


def _resolve_profile_setting(
    raw_profile: Dict[str, Any],
    direct_key: str,
    env_key: str,
    *,
    required: bool = False,
) -> str | None:
    value = _resolve_profile_value(raw_profile, direct_key)
    if not value:
        value = _resolve_profile_env(raw_profile, env_key)
    if required and not value:
        raise ValueError(
            f"Profile '{raw_profile.get('name', '') or 'unnamed'}' is missing "
            f"'{direct_key}' or '{env_key}'."
        )
    return value or None


def load_multi_api_profiles(config_path: str | Path, profile_count: int) -> List[LLMApiProfile]:
    """Load and validate multi-API profiles from JSON config."""
    if profile_count <= 0:
        return []

    config = read_file(str(config_path))
    if not isinstance(config, dict):
        raise ValueError(f"Invalid multi-api config: {config_path}")

    raw_profiles = config.get("profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ValueError(
            f"Invalid multi-api config {config_path}: 'profiles' must be a non-empty list."
        )

    if profile_count > len(raw_profiles):
        raise ValueError(
            f"Requested --multi_api_count={profile_count}, but only {len(raw_profiles)} "
            f"profiles are available in {config_path}."
        )

    profiles: List[LLMApiProfile] = []
    for idx, raw_profile in enumerate(raw_profiles[:profile_count]):
        if not isinstance(raw_profile, dict):
            raise ValueError(f"Invalid multi-api profile at index {idx}: must be a dict.")
        name = str(raw_profile.get("name") or f"profile_{idx}").strip() or f"profile_{idx}"
        api_key = _resolve_profile_setting(raw_profile, "api_key", "api_key_env", required=True)
        base_url = _resolve_profile_setting(raw_profile, "base_url", "base_url_env")
        default_model = _resolve_profile_setting(
            raw_profile,
            "default_model",
            "default_model_env",
        )
        profiles.append(
            LLMApiProfile(
                name=name,
                api_key=api_key or "",
                base_url=base_url,
                default_model=default_model,
            )
        )

    return profiles


def attach_dispatch_indices(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach stable indices used to shard and merge results safely."""
    indexed: List[Dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError("Multi-API dispatch requires list items to be dict objects.")
        if DISPATCH_INDEX_FIELD in item:
            raise ValueError(f"Input item already contains reserved field {DISPATCH_INDEX_FIELD}.")
        new_item = dict(item)
        new_item[DISPATCH_INDEX_FIELD] = idx
        indexed.append(new_item)
    return indexed


def split_round_robin(items: Sequence[Dict[str, Any]], shard_count: int) -> List[List[Dict[str, Any]]]:
    """Split items into deterministic round-robin shards."""
    if shard_count <= 0:
        raise ValueError("shard_count must be positive.")
    shards: List[List[Dict[str, Any]]] = [[] for _ in range(shard_count)]
    for idx, item in enumerate(items):
        shards[idx % shard_count].append(item)
    return shards


def strip_dispatch_index(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove internal dispatch metadata from items."""
    stripped: List[Dict[str, Any]] = []
    for item in items:
        new_item = dict(item)
        new_item.pop(DISPATCH_INDEX_FIELD, None)
        stripped.append(new_item)
    return stripped


def merge_dispatched_items(
    shard_outputs: Sequence[Sequence[Dict[str, Any]]],
    *,
    expected_count: int | None = None,
    strip_internal: bool = True,
) -> List[Dict[str, Any]]:
    """Merge shard outputs by dispatch index and reject duplicate results."""
    merged: Dict[int, Dict[str, Any]] = {}
    for shard_output in shard_outputs:
        for item in shard_output:
            if not isinstance(item, dict):
                raise ValueError("Merged shard output must contain dict items.")
            dispatch_idx = item.get(DISPATCH_INDEX_FIELD)
            if not isinstance(dispatch_idx, int):
                raise ValueError(
                    f"Merged shard item is missing valid {DISPATCH_INDEX_FIELD}: {item}"
                )
            if dispatch_idx in merged:
                raise ValueError(
                    f"Duplicate dispatched result detected for index {dispatch_idx}."
                )
            merged_item = dict(item)
            if strip_internal:
                merged_item.pop(DISPATCH_INDEX_FIELD, None)
            merged[dispatch_idx] = merged_item

    if expected_count is not None and len(merged) != expected_count:
        raise ValueError(
            f"Merged shard output count mismatch: expected {expected_count}, got {len(merged)}."
        )

    return [merged[idx] for idx in sorted(merged)]


def make_profile_work_dir(base_dir: str | Path, stage_name: str, shard_id: int, profile_name: str) -> Path:
    """Build a stable work directory for one profile shard."""
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", profile_name).strip("._") or f"profile_{shard_id}"
    return Path(base_dir) / "multi_api" / stage_name / f"{shard_id:02d}_{safe_name}"
