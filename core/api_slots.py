from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List


@dataclass(frozen=True)
class ApiSlot:
    slot_id: str
    name: str
    api_key: str
    base_url: str
    gen_api_key: str
    gen_base_url: str
    check_api_key: str
    check_base_url: str


def _read_json_or(path: Path, default: Any) -> Any:
    if not path.exists():
        return copy.deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return copy.deepcopy(default)


def load_api_slots(config_path: Path) -> List[ApiSlot]:
    config_path = Path(config_path)
    data = _read_json_or(config_path, {})
    if isinstance(data, list):
        raw_slots = data
    elif isinstance(data, dict):
        raw_slots = data.get("api_slots") or data.get("profiles") or []
    else:
        raw_slots = []
    if not isinstance(raw_slots, list) or not raw_slots:
        raise ValueError(f"Invalid api slot config: {config_path}")

    slots: List[ApiSlot] = []
    for idx, raw in enumerate(raw_slots, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"api slot #{idx} must be object")
        slot_id = str(raw.get("slot_id") or f"slot_{idx:03d}")
        name = str(raw.get("name") or slot_id)
        common_key = str(raw.get("api_key") or "").strip()
        common_base = str(raw.get("base_url") or "").strip()
        gen_key = str(raw.get("gen_api_key") or common_key).strip()
        gen_base = str(raw.get("gen_base_url") or common_base).strip() or common_base
        check_key = str(raw.get("check_api_key") or common_key).strip()
        check_base = str(raw.get("check_base_url") or common_base).strip() or common_base
        if not gen_key or not check_key:
            raise ValueError(f"api slot #{idx} missing api_key/check_api_key")
        if not gen_base or not check_base:
            raise ValueError(f"api slot #{idx} missing base_url/check_base_url")
        slots.append(
            ApiSlot(
                slot_id=slot_id,
                name=name,
                api_key=common_key or gen_key,
                base_url=common_base,
                gen_api_key=gen_key,
                gen_base_url=gen_base,
                check_api_key=check_key,
                check_base_url=check_base,
            )
        )
    return slots
