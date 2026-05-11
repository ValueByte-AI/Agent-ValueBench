"""Shard runtime state helpers for multi-API stage coordination."""

from __future__ import annotations

import datetime as dt
import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List

from utils.process_file import path_exists, read_file, save_file


STATUS_FILE = "status.json"
MANIFEST_FILE = "manifest.json"
INPUT_FILE = "input_items.json"
LOCK_FILE = "run.lock"
STAGE_LOCK_FILE = "stage.lock"
STAGE_STATUS_FILE = "stage_status.json"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_shard_runtime(
    *,
    work_dir: Path,
    stage_label: str,
    shard_id: int,
    profile_name: str,
    items: List[Dict[str, Any]],
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    save_file(
        str(work_dir / MANIFEST_FILE),
        {
            "stage_label": stage_label,
            "shard_id": shard_id,
            "profile_name": profile_name,
            "items_total": len(items),
            "updated_at": _now_iso(),
        },
    )
    save_file(str(work_dir / INPUT_FILE), items)
    if not path_exists(str(work_dir / STATUS_FILE)):
        update_shard_status(
            work_dir=work_dir,
            state="pending",
            current_step="pending",
            profile_name=profile_name,
            shard_id=shard_id,
        )


def read_shard_status(work_dir: Path) -> Dict[str, Any]:
    status_path = work_dir / STATUS_FILE
    if not path_exists(str(status_path)):
        return {
            "state": "pending",
            "current_step": "pending",
            "updated_at": _now_iso(),
        }
    data = read_file(str(status_path))
    if isinstance(data, dict):
        return data
    return {
        "state": "pending",
        "current_step": "pending",
        "updated_at": _now_iso(),
    }


def read_stage_status(stage_dir: Path) -> Dict[str, Any]:
    status_path = stage_dir / STAGE_STATUS_FILE
    if not path_exists(str(status_path)):
        return {
            "state": "idle",
            "updated_at": _now_iso(),
        }
    data = read_file(str(status_path))
    if isinstance(data, dict):
        return data
    return {
        "state": "idle",
        "updated_at": _now_iso(),
    }


def update_stage_status(
    *,
    stage_dir: Path,
    stage_label: str,
    state: str,
    leader_pid: int | None = None,
    extra: Dict[str, Any] | None = None,
) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    status = read_stage_status(stage_dir)
    status.update(
        {
            "stage_label": stage_label,
            "state": state,
            "updated_at": _now_iso(),
        }
    )
    if leader_pid is not None:
        status["leader_pid"] = leader_pid
    if extra:
        status.update(extra)
    save_file(str(stage_dir / STAGE_STATUS_FILE), status)


def update_shard_status(
    *,
    work_dir: Path,
    state: str,
    current_step: str,
    profile_name: str | None = None,
    shard_id: int | None = None,
    error: Dict[str, Any] | None = None,
    extra: Dict[str, Any] | None = None,
) -> None:
    status = read_shard_status(work_dir)
    status.update(
        {
            "state": state,
            "current_step": current_step,
            "updated_at": _now_iso(),
        }
    )
    if profile_name is not None:
        status["profile_name"] = profile_name
    if shard_id is not None:
        status["shard_id"] = shard_id
    if error is not None:
        status["error"] = error
    elif state != "blocked":
        status.pop("error", None)
    if extra:
        status.update(extra)
    save_file(str(work_dir / STATUS_FILE), status)


@contextmanager
def _try_lock_file(lock_path: Path) -> Iterator[bool]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = lock_path.open("a+")
    locked = False
    try:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except BlockingIOError:
            locked = False
        yield locked
    finally:
        if locked:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


@contextmanager
def try_shard_lock(work_dir: Path) -> Iterator[bool]:
    with _try_lock_file(work_dir / LOCK_FILE) as locked:
        yield locked


@contextmanager
def try_stage_lock(stage_dir: Path) -> Iterator[bool]:
    with _try_lock_file(stage_dir / STAGE_LOCK_FILE) as locked:
        yield locked


def list_shard_work_dirs(stage_dir: Path) -> List[Path]:
    if not stage_dir.exists():
        return []
    return sorted(
        [
            path
            for path in stage_dir.iterdir()
            if path.is_dir() and path.name[:2].isdigit()
        ],
        key=lambda path: path.name,
    )


def request_resume_for_blocked_shards(stage_dir: Path) -> List[Dict[str, Any]]:
    resumed: List[Dict[str, Any]] = []
    for work_dir in list_shard_work_dirs(stage_dir):
        status = read_shard_status(work_dir)
        if status.get("state") != "blocked":
            continue
        update_shard_status(
            work_dir=work_dir,
            state="blocked",
            current_step=str(status.get("current_step", "blocked")),
            profile_name=status.get("profile_name"),
            shard_id=status.get("shard_id"),
            error=status.get("error"),
            extra={
                "resume_requested": True,
                "resume_requested_at": _now_iso(),
            },
        )
        resumed.append(read_shard_status(work_dir))
    return resumed
