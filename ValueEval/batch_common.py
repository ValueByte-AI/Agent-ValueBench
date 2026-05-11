from __future__ import annotations

import copy
import fcntl
import json
import os
import signal
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.api_slots import ApiSlot, load_api_slots
from core.file_utils import ensure_dir


MASTER_LOCK_NAME = "master.lock"
RUN_STATE_NAME = "run_state.json"
PLAN_NAME = "plan.json"
SLOTS_NAME = "api_slots_state.json"
MASTER_LOG_NAME = "master_events.jsonl"
DEFAULT_STAGE_POLL_SECONDS = 1.0

MANUAL_BLOCK_KINDS = {"quota_or_balance", "auth", "unknown"}
AUTO_RETRY_KINDS = {"network", "timeout"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask_secret(value: str) -> str:
    text = str(value or "")
    if len(text) <= 10:
        return "*" * len(text)
    return f"{text[:6]}...{text[-4:]}"


def _atomic_write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}.{threading.get_ident()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, data: Any) -> None:
    _atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _read_json_or(path: Path, default: Any) -> Any:
    if not path.exists():
        return copy.deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return copy.deepcopy(default)


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    line = json.dumps(payload, ensure_ascii=False, default=str) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _process_alive(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except Exception:
        return False
    if pid_int <= 0:
        return False
    try:
        os.kill(pid_int, 0)
    except OSError:
        return False
    return True


def _classify_llm_error(message: str) -> str:
    text = str(message or "").lower()
    if not text:
        return "unknown"
    if (
        "invalid api key" in text
        or "authentication" in text
        or "unauthorized" in text
        or "401" in text
    ):
        return "auth"
    if (
        "quota" in text
        or "insufficient" in text
        or "credit" in text
        or "balance" in text
        or "429" in text
        or "rate limit" in text
    ):
        return "quota_or_balance"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if (
        "proxyerror" in text
        or "connection" in text
        or "ssl" in text
        or "eof" in text
        or "network" in text
        or "dns" in text
        or "remote end closed" in text
    ):
        return "network"
    return "unknown"


class FileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._fh = None

    def acquire(self) -> bool:
        ensure_dir(self.path.parent)
        fh = self.path.open("a+")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            return False
        self._fh = fh
        return True

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None


def discover_case_files(case_root: Path) -> List[Path]:
    if not case_root.exists():
        raise FileNotFoundError(f"case directory not found: {case_root}")
    if not case_root.is_dir():
        raise NotADirectoryError(f"case directory is not a directory: {case_root}")

    files: List[Path] = []
    for path in case_root.rglob("*.json"):
        if not path.is_file():
            continue
        if path.name.endswith("_tmp.json"):
            continue
        files.append(path)
    files.sort(key=lambda item: item.relative_to(case_root).as_posix())
    if not files:
        raise ValueError(f"No case json files found under {case_root}")
    return files


class BatchRecoverableAPIError(RuntimeError):
    def __init__(self, *, kind: str, message: str, stage_name: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.stage_name = stage_name


class BatchCoordinatorBase:
    @property
    def run_state_path(self) -> Path:
        return self.run_dir / RUN_STATE_NAME

    @property
    def plan_path(self) -> Path:
        return self.run_dir / PLAN_NAME

    @property
    def slots_state_path(self) -> Path:
        return self.run_dir / SLOTS_NAME

    @property
    def master_log_path(self) -> Path:
        return self.run_dir / MASTER_LOG_NAME

    def _write_master_event(self, event: str, payload: Dict[str, Any]) -> None:
        _append_jsonl(
            self.master_log_path,
            {"timestamp": _now_iso(), "event": event, "payload": payload},
        )

    def _load_or_init_plan(self) -> None:
        if self.plan_path.exists():
            existing = _read_json_or(self.plan_path, {})
            if existing == self.plan_bundle:
                return
            if self.settings.resume:
                raise ValueError("Existing judge run plan does not match current case directory scan.")
        _atomic_write_json(self.plan_path, self.plan_bundle)

    def _case_root_dir(self, case_id: str) -> Path:
        return self.run_dir / "cases" / case_id

    def _case_state_path(self, case_id: str) -> Path:
        return self._case_root_dir(case_id) / "state.json"

    def _case_trace_dir(self, case_id: str) -> Path:
        return self._case_root_dir(case_id) / "trace"

    def _load_case_state(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        cached = self.case_states.get(str(spec["case_id"]))
        if isinstance(cached, dict) and cached:
            return copy.deepcopy(cached)
        path = self._case_state_path(spec["case_id"])
        existing = _read_json_or(path, {})
        if isinstance(existing, dict) and existing:
            state = existing
        else:
            state = self._case_state_default(spec)
        with self.state_lock:
            self.case_states[str(spec["case_id"])] = copy.deepcopy(state)
        return copy.deepcopy(state)

    def _save_case_state(self, case_state: Dict[str, Any]) -> None:
        saved = copy.deepcopy(case_state)
        saved["updated_at"] = _now_iso()
        with self.state_lock:
            self.case_states[str(saved["case_id"])] = saved
        _atomic_write_json(self._case_state_path(str(saved["case_id"])), saved)

    def _initialize_case_runtime_state(self) -> None:
        valid_slot_ids = set(self.slot_states.keys())
        assigned_by_slot: Dict[str, str] = {}
        pending = deque()

        for spec in self.plan:
            original_state = self._load_case_state(spec)
            state = copy.deepcopy(original_state)
            case_id = str(spec["case_id"])
            status = str(state.get("status") or "pending")
            assigned_slot = str(state.get("assigned_slot_id") or "").strip() or None
            changed = False

            if assigned_slot and assigned_slot not in valid_slot_ids:
                assigned_slot = None
                changed = True

            if status in {"succeeded", "failed"}:
                if assigned_slot is not None:
                    assigned_slot = None
                    changed = True
                if str(state.get("current_stage") or ""):
                    state["current_stage"] = ""
                    changed = True
            elif self.settings.resume and assigned_slot and status in {"running", "blocked", "retrying"}:
                if assigned_slot in assigned_by_slot:
                    status = "pending"
                    assigned_slot = None
                    state["current_stage"] = ""
                    changed = True
                else:
                    assigned_by_slot[assigned_slot] = case_id
            else:
                if status != "pending":
                    status = "pending"
                    changed = True
                if assigned_slot is not None:
                    assigned_slot = None
                    changed = True
                if str(state.get("current_stage") or ""):
                    state["current_stage"] = ""
                    changed = True

            state["status"] = status
            state["assigned_slot_id"] = assigned_slot
            self.case_states[case_id] = copy.deepcopy(state)
            if changed:
                self._save_case_state(state)
            if status == "pending" and assigned_slot is None:
                pending.append(case_id)

        with self.state_lock:
            for slot_id in self.slot_order:
                item = copy.deepcopy(self.slot_states.get(slot_id) or {})
                assigned_case_id = assigned_by_slot.get(slot_id)
                if assigned_case_id:
                    case_state = self.case_states.get(assigned_case_id, {})
                    case_status = str(case_state.get("status") or "running")
                    item.update(
                        {
                            "status": case_status if case_status in {"running", "blocked", "retrying"} else "running",
                            "assigned_case_id": assigned_case_id,
                            "current_stage": str(case_state.get("current_stage") or ""),
                            "blocked_kind": item.get("blocked_kind", "") if case_status == "blocked" else "",
                            "blocked_message": item.get("blocked_message", "") if case_status == "blocked" else "",
                            "blocked_at": item.get("blocked_at") if case_status == "blocked" else None,
                            "resume_requested": bool(item.get("resume_requested", False)),
                        }
                    )
                else:
                    item.update(
                        {
                            "status": "idle",
                            "assigned_case_id": None,
                            "current_stage": "",
                            "blocked_kind": "",
                            "blocked_message": "",
                            "blocked_at": None,
                            "resume_requested": False,
                            "retry_count": 0,
                            "next_retry_at": None,
                            "last_error": "",
                        }
                    )
                item["updated_at"] = _now_iso()
                self.slot_states[slot_id] = item

        for slot_id in self.slot_order:
            if not pending:
                break
            slot_state = self.slot_states.get(slot_id, {})
            if slot_state.get("assigned_case_id"):
                continue
            case_id = pending.popleft()
            case_state = self.case_states[case_id]
            case_state["assigned_slot_id"] = slot_id
            case_state["status"] = "running"
            case_state["current_stage"] = "queued"
            case_state["failure_reason"] = ""
            case_state["last_error"] = ""
            self._save_case_state(case_state)
            with self.state_lock:
                item = copy.deepcopy(self.slot_states[slot_id])
                item.update(
                    {
                        "status": "running",
                        "assigned_case_id": case_id,
                        "current_stage": "queued",
                        "blocked_kind": "",
                        "blocked_message": "",
                        "blocked_at": None,
                        "resume_requested": False,
                        "retry_count": 0,
                        "next_retry_at": None,
                        "last_error": "",
                        "updated_at": _now_iso(),
                    }
                )
                self.slot_states[slot_id] = item

        with self.state_lock:
            self.pending_case_ids = pending
            self._slot_states_dirty = True
        self._persist_slot_states(force=True)

    def _count_case_statuses(self) -> Dict[str, int]:
        if not self.case_states:
            success_count = 0
            failed_count = 0
            running_count = 0
            for spec in self.plan:
                path = self._case_state_path(spec["case_id"])
                state = _read_json_or(path, {})
                if not isinstance(state, dict) or not state:
                    state = self._case_state_default(spec)
                status = str(state.get("status", "pending"))
                if status == "succeeded":
                    success_count += 1
                elif status == "failed":
                    failed_count += 1
                elif status in {"running", "blocked", "retrying"}:
                    running_count += 1
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "running_count": running_count,
            }
        success_count = 0
        failed_count = 0
        running_count = 0
        for state in self.case_states.values():
            status = str(state.get("status", "pending"))
            if status == "succeeded":
                success_count += 1
            elif status == "failed":
                failed_count += 1
            elif status in {"running", "blocked", "retrying"}:
                running_count += 1
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "running_count": running_count,
        }

    def _all_cases_terminal(self) -> bool:
        counts = self._count_case_statuses()
        return counts["success_count"] + counts["failed_count"] >= len(self.plan)

    def _claim_next_case_for_slot(self, slot_id: str) -> Optional[Dict[str, Any]]:
        with self.state_lock:
            slot_state = copy.deepcopy(self.slot_states.get(slot_id) or {})
            assigned_case_id = str(slot_state.get("assigned_case_id") or "").strip()
            if assigned_case_id:
                case_state = self.case_states.get(assigned_case_id, {})
                if (
                    isinstance(case_state, dict)
                    and str(case_state.get("assigned_slot_id") or "") == slot_id
                    and str(case_state.get("status") or "") in {"running", "blocked", "retrying"}
                ):
                    return self.plan_by_case_id.get(assigned_case_id)

            while self.pending_case_ids:
                case_id = str(self.pending_case_ids.popleft())
                case_state = copy.deepcopy(self.case_states.get(case_id) or {})
                if not case_state:
                    continue
                if str(case_state.get("status") or "") != "pending":
                    continue
                if case_state.get("assigned_slot_id"):
                    continue
                case_state["assigned_slot_id"] = slot_id
                case_state["status"] = "running"
                case_state["current_stage"] = "queued"
                case_state["failure_reason"] = ""
                case_state["last_error"] = ""
                self._save_case_state(case_state)
                item = copy.deepcopy(self.slot_states.get(slot_id) or {})
                if item:
                    item.update(
                        {
                            "status": "running",
                            "assigned_case_id": case_id,
                            "current_stage": "queued",
                            "blocked_kind": "",
                            "blocked_message": "",
                            "blocked_at": None,
                            "resume_requested": False,
                            "retry_count": 0,
                            "next_retry_at": None,
                            "last_error": "",
                            "updated_at": _now_iso(),
                        }
                    )
                    self.slot_states[slot_id] = item
                    self._slot_states_dirty = True
                return self.plan_by_case_id.get(case_id)
            return None

    def _update_slot_state(self, slot_id: str, updater, *, flush: bool = False) -> Dict[str, Any]:
        with self.state_lock:
            item = copy.deepcopy(self.slot_states.get(slot_id) or {})
            if not item:
                return {}
            new_item = updater(item)
            new_item["updated_at"] = _now_iso()
            self.slot_states[slot_id] = new_item
            self._slot_states_dirty = True
            selected = copy.deepcopy(new_item)
        if flush:
            self._persist_slot_states(force=True)
        return selected

    def _slot_state(self, slot_id: str) -> Dict[str, Any]:
        with self.state_lock:
            return copy.deepcopy(self.slot_states.get(slot_id) or {})

    def _mark_slot_busy(self, slot_id: str, case_id: str, stage: str) -> None:
        self._update_slot_state(
            slot_id,
            lambda item: {
                **item,
                "status": "running",
                "assigned_case_id": case_id,
                "current_stage": stage,
                "resume_requested": False,
                "blocked_kind": "",
                "blocked_message": "",
                "blocked_at": None,
                "last_error": "",
            },
        )

    def _mark_slot_idle(self, slot_id: str) -> None:
        self._update_slot_state(
            slot_id,
            lambda item: {
                **item,
                "status": "idle",
                "assigned_case_id": None,
                "current_stage": "",
                "resume_requested": False,
                "blocked_kind": "",
                "blocked_message": "",
                "blocked_at": None,
                "retry_count": 0,
                "next_retry_at": None,
                "last_error": "",
            },
        )

    def _mark_slot_retrying(self, slot_id: str, case_id: str, stage: str, error: BatchRecoverableAPIError) -> None:
        def updater(item: Dict[str, Any]) -> Dict[str, Any]:
            retry_count = int(item.get("retry_count", 0) or 0) + 1
            delay_seconds = min(300, 10 * (2 ** max(0, retry_count - 1)))
            return {
                **item,
                "status": "retrying",
                "assigned_case_id": case_id,
                "current_stage": stage,
                "blocked_kind": error.kind,
                "blocked_message": error.message,
                "last_error": error.message,
                "retry_count": retry_count,
                "next_retry_at": datetime.fromtimestamp(time.time() + delay_seconds, tz=timezone.utc).isoformat(),
            }

        self._update_slot_state(slot_id, updater)

    def _mark_slot_blocked(self, slot_id: str, case_id: str, stage: str, error: BatchRecoverableAPIError) -> None:
        self._update_slot_state(
            slot_id,
            lambda item: {
                **item,
                "status": "blocked",
                "assigned_case_id": case_id,
                "current_stage": stage,
                "blocked_kind": error.kind,
                "blocked_message": error.message,
                "blocked_at": _now_iso(),
                "resume_requested": False,
                "last_error": error.message,
                "next_retry_at": None,
            },
        )

    def _maybe_signal_resume_only(self) -> bool:
        state = self._read_run_state()
        leader_pid = state.get("leader_pid")
        if self.settings.resume and _process_alive(leader_pid):
            latest_slots = {slot.slot_id: slot for slot in load_api_slots(self.settings.api_slots_json)}
            slot_states = _read_json_or(self.slots_state_path, [])
            updated = []
            out: List[Dict[str, Any]] = []
            for item in slot_states:
                if not isinstance(item, dict):
                    continue
                item = copy.deepcopy(item)
                slot_id = str(item.get("slot_id", "")).strip()
                latest = latest_slots.get(slot_id)
                if latest is not None:
                    item["api"] = {
                        "base_url": latest.gen_base_url,
                        "api_key_masked": _mask_secret(latest.gen_api_key),
                    }
                    item["config"] = {
                        "api_key": latest.gen_api_key,
                        "base_url": latest.gen_base_url,
                    }
                if str(item.get("status")) == "blocked":
                    item["resume_requested"] = True
                    item["updated_at"] = _now_iso()
                    updated.append(
                        {
                            "slot_id": item.get("slot_id"),
                            "name": item.get("name"),
                            "assigned_case_id": item.get("assigned_case_id"),
                            "blocked_kind": item.get("blocked_kind"),
                        }
                    )
                out.append(item)
            _atomic_write_json(self.slots_state_path, out)
            print(
                "[RUBRIC-BATCH][RESUME-SIGNAL] "
                + json.dumps({"leader_pid": leader_pid, "resumed_slots": updated}, ensure_ascii=False),
                flush=True,
            )
            return True
        return False

    def _install_signal_handlers(self) -> None:
        def _handle_signal(signum, _frame) -> None:
            self.stop_event.set()
            self._write_run_state({"state": "stopping", "leader_pid": os.getpid()})
            self._write_master_event("signal", {"signal": signum, "message": "shutdown requested"})

        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            try:
                signal.signal(sig, _handle_signal)
            except Exception:
                continue

    def _read_run_state(self) -> Dict[str, Any]:
        return _read_json_or(
            self.run_state_path,
            {
                "run_name": self.run_dir.name,
                "state": "idle",
                "leader_pid": None,
                "success_count": 0,
                "failed_count": 0,
                "total_cases": len(self.plan),
                "updated_at": _now_iso(),
            },
        )

    def _write_run_state(self, updates: Dict[str, Any]) -> None:
        state = self._read_run_state()
        state.update(updates)
        state["updated_at"] = _now_iso()
        _atomic_write_json(self.run_state_path, state)


def render_progress_bar(current: int, total: int, width: int = 32) -> str:
    if total <= 0:
        total = 1
    ratio = min(1.0, max(0.0, current / total))
    filled = int(width * ratio)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def watch_progress(run_dir: Path, poll_seconds: float = 1.0) -> None:
    while True:
        state = _read_json_or(run_dir / RUN_STATE_NAME, {})
        success_count = int(state.get("success_count", 0) or 0)
        total_cases = int(state.get("total_cases", 0) or 0)
        leader_alive = _process_alive(state.get("leader_pid"))
        run_state = str(state.get("state", "idle"))
        effective_state = run_state
        if not leader_alive and run_state not in {"completed", "paused", "idle"}:
            effective_state = "orphaned"
        bar = render_progress_bar(success_count, total_cases)
        blocked_items = state.get("blocked_api_resources")
        if not isinstance(blocked_items, list):
            blocked_items = state.get("blocked_slots", [])
        if not isinstance(blocked_items, list):
            blocked_items = []
        line = (
            f"\r{bar} {success_count}/{total_cases} "
            f"state={effective_state} failed={int(state.get('failed_count', 0) or 0)} "
            f"blocked={len(blocked_items)}"
        )
        print(line, end="", flush=True)
        if not leader_alive and effective_state in {"completed", "paused", "idle", "orphaned"}:
            print("", flush=True)
            return
        time.sleep(max(0.2, float(poll_seconds)))


def show_blocked_slots(run_dir: Path) -> int:
    state = _read_json_or(run_dir / RUN_STATE_NAME, {})
    blocked = state.get("blocked_api_resources")
    if not isinstance(blocked, list):
        blocked = state.get("blocked_slots", [])
    if not isinstance(blocked, list):
        blocked = []
    if not blocked:
        print("No blocked APIs.", flush=True)
        return 0
    for item in blocked:
        if not isinstance(item, dict):
            continue
        if "api_key_masked" in item or "resource_id" in item:
            payload = {
                "resource_id": item.get("resource_id"),
                "api_key_masked": item.get("api_key_masked"),
                "base_url": item.get("base_url"),
                "blocked_kind": item.get("blocked_kind"),
            }
        else:
            payload = {
                "slot_id": item.get("slot_id"),
                "name": item.get("name"),
                "assigned_case_id": item.get("assigned_case_id"),
                "blocked_kind": item.get("blocked_kind"),
            }
        print(json.dumps(payload, ensure_ascii=False), flush=True)
    return len(blocked)
