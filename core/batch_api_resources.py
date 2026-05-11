from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional


def normalize_api_config(config: Any) -> Optional[Dict[str, str]]:
    if not isinstance(config, dict):
        return None
    api_key = str(config.get("api_key") or "").strip()
    base_url = str(config.get("base_url") or "").strip()
    if not api_key or not base_url:
        return None
    return {
        "api_key": api_key,
        "base_url": base_url,
    }


def api_config_equal(left: Any, right: Any) -> bool:
    return normalize_api_config(left) == normalize_api_config(right)


def resource_id_from_config(config: Any) -> str:
    normalized = normalize_api_config(config)
    if normalized is None:
        return ""
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def resource_state_default(
    *,
    config: Dict[str, str],
    mask_secret,
    now_iso,
) -> Dict[str, Any]:
    resource_id = resource_id_from_config(config)
    return {
        "resource_id": resource_id,
        "status": "available",
        "blocked_kind": "",
        "blocked_message": "",
        "blocked_at": None,
        "updated_at": now_iso(),
        "api": {
            "base_url": str(config["base_url"]),
            "api_key_masked": mask_secret(str(config["api_key"])),
        },
        "config": {
            "api_key": str(config["api_key"]),
            "base_url": str(config["base_url"]),
        },
    }


def blocked_resource_payload(resource_state: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(resource_state, dict):
        return None
    if str(resource_state.get("status") or "") != "blocked":
        return None
    api = resource_state.get("api")
    if not isinstance(api, dict):
        api = {}
    return {
        "resource_id": str(resource_state.get("resource_id") or ""),
        "api_key_masked": str(api.get("api_key_masked") or ""),
        "base_url": str(api.get("base_url") or ""),
        "blocked_kind": str(resource_state.get("blocked_kind") or ""),
    }


def collect_unique_resource_configs(configs: Iterable[Any]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for raw in configs:
        normalized = normalize_api_config(raw)
        if normalized is None:
            continue
        resource_id = resource_id_from_config(normalized)
        if not resource_id or resource_id in seen:
            continue
        seen.add(resource_id)
        out.append(normalized)
    return out


def is_confirmed_balance_exhaustion(message: str) -> bool:
    text = str(message or "").lower()
    if not text:
        return False
    patterns = [
        "reject_no_credit",
        "credit required",
        "no credit",
        "insufficient balance",
        "insufficient credit",
        "insufficient quota",
        "quota exceeded",
        "out of credit",
        "out of quota",
        "balance exhausted",
        "balance is not enough",
        "余额不足",
        "欠费",
        "充值",
    ]
    return any(pattern in text for pattern in patterns)
