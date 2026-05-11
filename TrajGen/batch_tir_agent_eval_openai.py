from __future__ import annotations

import argparse
import contextlib
import copy
from collections import deque
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.batch_api_resources import (
    api_config_equal,
    blocked_resource_payload,
    collect_unique_resource_configs,
    is_confirmed_balance_exhaustion,
    normalize_api_config,
    resource_id_from_config,
    resource_state_default,
)
from core.file_utils import ensure_dir
import core.debug_trace as debug_trace_module
from core.api_slots import ApiSlot, load_api_slots
from TrajGen.tir_agent_eval_openai import run_case_file_openai


RUNS_ROOT = ROOT_DIR / "TrajGen" / "traj_batch_runs"
MASTER_LOCK_NAME = "master.lock"
RUN_STATE_NAME = "run_state.json"
PLAN_NAME = "plan.json"
SLOTS_NAME = "api_slots_state.json"
RESOURCES_NAME = "api_resources_state.json"
MASTER_LOG_NAME = "master_events.jsonl"
DEFAULT_STAGE_POLL_SECONDS = 1.0

MANUAL_BLOCK_KINDS = {"quota_or_balance"}
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
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


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
        or "403" in text
        or "access_denied" in text
        or "no permission" in text
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
        or "connection aborted" in text
        or "bad gateway" in text
        or "gateway timeout" in text
        or "service unavailable" in text
        or "502" in text
        or "503" in text
        or "504" in text
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


def build_traj_plan(
    *,
    case_root: Path,
    traj_output_dir_name: str,
) -> Dict[str, Any]:
    output_root = case_root.parent / str(traj_output_dir_name).strip()
    files = discover_case_files(case_root)
    seen_case_ids: Dict[str, str] = {}
    plan: List[Dict[str, Any]] = []
    for path in files:
        payload = _read_json_or(path, None)
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid case JSON object: {path}")
        case_id = str(payload.get("case_id") or path.stem).strip() or path.stem
        environment = str(payload.get("environment") or "").strip()
        case_name = str(payload.get("case_name") or path.stem).strip() or path.stem
        previous = seen_case_ids.get(case_id)
        if previous is not None:
            raise ValueError(f"Duplicate case_id discovered under case root: {case_id} ({previous}, {path})")
        seen_case_ids[case_id] = str(path)
        rel_case_path = path.relative_to(case_root)
        rel_traj_path = rel_case_path.with_name(f"{rel_case_path.stem}_traj.json")
        plan.append(
            {
                "spec_index": len(plan),
                "case_id": case_id,
                "case_name": case_name,
                "environment": environment,
                "case_path": str(path.resolve()),
                "relative_case_path": rel_case_path.as_posix(),
                "relative_traj_path": rel_traj_path.as_posix(),
            }
        )
    return {
        "case_root": str(case_root.resolve()),
        "traj_output_root": str(output_root.resolve()),
        "items": plan,
    }


class BatchRecoverableAPIError(RuntimeError):
    def __init__(self, *, kind: str, message: str, stage_name: str) -> None:
        super().__init__(message)
        self.kind = str(kind or "unknown")
        self.message = str(message or "")
        self.stage_name = str(stage_name or "traj")


@dataclass
class TrajectoryBatchSettings:
    api_slots_json: Path
    cases_dir: Path
    traj_output_dir_name: str
    eval_model: str
    max_steps: int
    temperature: float
    max_tokens: int
    timeout_seconds: int
    network_max_retries: int
    parallel_tool_calls: Optional[bool] = None
    n: Optional[int] = None
    tool_choice: str = "auto"
    resume: bool = False


class TrajectoryBatchExecutor:
    def __init__(self, settings: TrajectoryBatchSettings) -> None:
        self.settings = settings

    def _output_temp_path(self, *, spec: Dict[str, Any], temp_traj_root: Path) -> Path:
        return temp_traj_root / str(spec["environment"]) / str(spec["case_name"]) / f"{spec['case_name']}_traj.json"

    @staticmethod
    def _extract_traj_error(traj_data: Any) -> str:
        if not isinstance(traj_data, dict):
            return ""
        steps = traj_data.get("steps")
        if isinstance(steps, list):
            for step in reversed(steps):
                if not isinstance(step, dict):
                    continue
                error = str(step.get("error") or "").strip()
                if error:
                    return error
        final_answer = str(traj_data.get("final_answer") or "").strip()
        if final_answer:
            return final_answer
        return ""

    def _finalize_attempt(
        self,
        *,
        spec: Dict[str, Any],
        output_traj_path: Path,
        temp_traj_path: Path,
        traj_data: Any,
        stdout_text: str,
        stderr_text: str,
        returncode: int,
    ) -> Dict[str, Any]:
        if isinstance(traj_data, dict):
            status = str(traj_data.get("status") or "")
            if status == "finished":
                ensure_dir(output_traj_path.parent)
                _atomic_write_json(output_traj_path, traj_data)
                return {
                    "case_name": str(traj_data.get("case_name") or spec["case_name"]),
                    "traj_path": str(output_traj_path),
                    "temp_traj_path": str(temp_traj_path),
                    "traj_data": traj_data,
                }

            error_message = self._extract_traj_error(traj_data)
            if error_message:
                kind = _classify_llm_error(error_message)
                if kind in AUTO_RETRY_KINDS or kind in MANUAL_BLOCK_KINDS:
                    raise BatchRecoverableAPIError(kind=kind, message=error_message, stage_name="traj")
                raise RuntimeError(error_message)

            raise RuntimeError(f"trajectory ended with status={status or 'unknown'}")

        error_message = ""
        if not error_message:
            if stderr_text.strip():
                error_message = stderr_text.strip().splitlines()[-1]
            elif stdout_text.strip():
                error_message = stdout_text.strip().splitlines()[-1]
            elif returncode != 0:
                error_message = f"subprocess exited with code {returncode}"
            else:
                error_message = "trajectory generation failed without a structured error"

        kind = _classify_llm_error(error_message)
        if kind in AUTO_RETRY_KINDS or kind in MANUAL_BLOCK_KINDS:
            raise BatchRecoverableAPIError(kind=kind, message=error_message, stage_name="traj")
        raise RuntimeError(error_message)


@contextlib.contextmanager
def _temporary_trace_env(trace_dir: Path) -> Any:
    ensure_dir(trace_dir)
    old_dir = os.environ.get("VALUEBENCH_DEBUG_TRACE_DIR")
    old_stdout = os.environ.get("VALUEBENCH_DEBUG_TRACE_STDOUT")
    old_state = dict(debug_trace_module._STATE)
    os.environ["VALUEBENCH_DEBUG_TRACE_DIR"] = str(trace_dir)
    os.environ["VALUEBENCH_DEBUG_TRACE_STDOUT"] = "0"
    debug_trace_module._STATE["dir"] = None
    debug_trace_module._STATE["stdout"] = False
    debug_trace_module._STATE["counter"] = 0
    debug_trace_module._STATE["session_started"] = False
    try:
        yield
    finally:
        debug_trace_module._STATE.clear()
        debug_trace_module._STATE.update(old_state)
        if old_dir is None:
            os.environ.pop("VALUEBENCH_DEBUG_TRACE_DIR", None)
        else:
            os.environ["VALUEBENCH_DEBUG_TRACE_DIR"] = old_dir
        if old_stdout is None:
            os.environ.pop("VALUEBENCH_DEBUG_TRACE_STDOUT", None)
        else:
            os.environ["VALUEBENCH_DEBUG_TRACE_STDOUT"] = old_stdout


class InProcessTrajectoryBatchExecutor(TrajectoryBatchExecutor):
    def run_case(
        self,
        *,
        spec: Dict[str, Any],
        slot_state: Dict[str, Any],
        output_traj_path: Path,
        attempt_dir: Path,
    ) -> Dict[str, Any]:
        del slot_state
        temp_traj_root = attempt_dir / "temp_traj_root"
        trace_dir = attempt_dir / "trace"
        ensure_dir(temp_traj_root)
        ensure_dir(trace_dir)
        with _temporary_trace_env(trace_dir):
            traj_data, temp_traj_path = run_case_file_openai(
                case_file=Path(spec["case_path"]),
                traj_root=temp_traj_root,
                max_steps=self.settings.max_steps,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
                eval_api_key="test-key",
                eval_base_url="https://example.com/v1",
                eval_model=self.settings.eval_model,
                timeout_seconds=self.settings.timeout_seconds,
                network_max_retries=self.settings.network_max_retries,
                parallel_tool_calls=self.settings.parallel_tool_calls,
                n=self.settings.n,
                tool_choice=self.settings.tool_choice,
            )
        _atomic_write_text(attempt_dir / "stdout.txt", "")
        _atomic_write_text(attempt_dir / "stderr.txt", "")
        _atomic_write_json(
            attempt_dir / "attempt_summary.json",
            {
                "mode": "inprocess",
                "case_path": spec["case_path"],
                "temp_traj_path": str(temp_traj_path),
            },
        )
        return self._finalize_attempt(
            spec=spec,
            output_traj_path=output_traj_path,
            temp_traj_path=temp_traj_path,
            traj_data=traj_data,
            stdout_text="",
            stderr_text="",
            returncode=0,
        )


class SubprocessTrajectoryBatchExecutor(TrajectoryBatchExecutor):
    def _build_command(self, *, spec: Dict[str, Any], slot_state: Dict[str, Any], temp_traj_root: Path) -> List[str]:
        config = slot_state.get("config", {}) if isinstance(slot_state, dict) else {}
        cmd = [
            sys.executable,
            "-m",
            "TrajGen.tir_agent_eval_openai",
            "--case_file",
            str(spec["case_path"]),
            "--traj_root",
            str(temp_traj_root),
            "--max_steps",
            str(int(self.settings.max_steps)),
            "--temperature",
            str(float(self.settings.temperature)),
            "--max_tokens",
            str(int(self.settings.max_tokens)),
            "--eval_api_key",
            str(config.get("api_key") or ""),
            "--eval_base_url",
            str(config.get("base_url") or ""),
            "--eval_model",
            str(self.settings.eval_model),
            "--timeout_seconds",
            str(int(self.settings.timeout_seconds)),
            "--network_max_retries",
            str(int(self.settings.network_max_retries)),
            "--tool_choice",
            str(self.settings.tool_choice),
        ]
        if self.settings.parallel_tool_calls is not None:
            cmd.extend(
                [
                    "--parallel_tool_calls",
                    "1" if self.settings.parallel_tool_calls else "0",
                ]
            )
        if self.settings.n is not None:
            cmd.extend(["--n", str(int(self.settings.n))])
        return cmd

    def run_case(
        self,
        *,
        spec: Dict[str, Any],
        slot_state: Dict[str, Any],
        output_traj_path: Path,
        attempt_dir: Path,
    ) -> Dict[str, Any]:
        temp_traj_root = attempt_dir / "temp_traj_root"
        trace_dir = attempt_dir / "trace"
        ensure_dir(temp_traj_root)
        ensure_dir(trace_dir)

        cmd = self._build_command(spec=spec, slot_state=slot_state, temp_traj_root=temp_traj_root)
        env = os.environ.copy()
        env["VALUEBENCH_DEBUG_TRACE_DIR"] = str(trace_dir)
        env["VALUEBENCH_DEBUG_TRACE_STDOUT"] = "0"
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT_DIR),
            env=env,
            capture_output=True,
            text=True,
        )
        stdout_text = str(proc.stdout or "")
        stderr_text = str(proc.stderr or "")
        _atomic_write_text(attempt_dir / "stdout.txt", stdout_text)
        _atomic_write_text(attempt_dir / "stderr.txt", stderr_text)
        _atomic_write_json(
            attempt_dir / "attempt_summary.json",
            {
                "mode": "subprocess",
                "command": cmd,
                "returncode": int(proc.returncode),
                "case_path": spec["case_path"],
                "slot_id": slot_state.get("slot_id"),
                "slot_name": slot_state.get("name"),
                "api": slot_state.get("api"),
            },
        )

        temp_traj_path = self._output_temp_path(spec=spec, temp_traj_root=temp_traj_root)
        traj_data = _read_json_or(temp_traj_path, None) if temp_traj_path.exists() else None
        return self._finalize_attempt(
            spec=spec,
            output_traj_path=output_traj_path,
            temp_traj_path=temp_traj_path,
            traj_data=traj_data,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            returncode=int(proc.returncode),
        )


class BatchTrajectoryCoordinator:
    def __init__(
        self,
        *,
        run_dir: Path,
        settings: TrajectoryBatchSettings,
        executor_cls=SubprocessTrajectoryBatchExecutor,
    ) -> None:
        self.run_dir = run_dir
        self.settings = settings
        self.executor_cls = executor_cls
        self.master_lock = FileLock(self.run_dir / MASTER_LOCK_NAME)
        self.state_lock = threading.RLock()
        self.stop_event = threading.Event()
        self.workers: List[threading.Thread] = []
        self.plan_bundle = build_traj_plan(
            case_root=settings.cases_dir,
            traj_output_dir_name=settings.traj_output_dir_name,
        )
        self.plan = self.plan_bundle["items"]
        self.plan_by_case_id = {str(item["case_id"]): item for item in self.plan}
        self.output_root = Path(self.plan_bundle["traj_output_root"])
        self.slot_order: List[str] = []
        self.slot_states: Dict[str, Dict[str, Any]] = {}
        self.home_slot_configs: Dict[str, Dict[str, str]] = {}
        self.resource_order: List[str] = []
        self.resource_states: Dict[str, Dict[str, Any]] = {}
        self.case_states: Dict[str, Dict[str, Any]] = {}
        self.pending_case_ids = deque()
        self._slot_states_dirty = False
        self._resource_states_dirty = False
        self._replacement_cursor = 0
        ensure_dir(self.run_dir / "cases")
        ensure_dir(self.output_root)

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
    def resources_state_path(self) -> Path:
        return self.run_dir / RESOURCES_NAME

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
                raise ValueError("Existing trajectory batch plan does not match current case directory scan.")
        _atomic_write_json(self.plan_path, self.plan_bundle)

    def _slot_state_default(self, slot: ApiSlot) -> Dict[str, Any]:
        config = {
            "api_key": slot.api_key,
            "base_url": slot.base_url,
        }
        return {
            "slot_id": slot.slot_id,
            "name": slot.name,
            "status": "idle",
            "assigned_case_id": None,
            "resource_id": resource_id_from_config(config),
            "uses_override": False,
            "current_stage": "",
            "blocked_kind": "",
            "blocked_message": "",
            "blocked_at": None,
            "resume_requested": False,
            "retry_count": 0,
            "next_retry_at": None,
            "last_error": "",
            "updated_at": _now_iso(),
            "api": {
                "base_url": config["base_url"],
                "api_key_masked": _mask_secret(config["api_key"]),
            },
            "config": config,
        }

    def _load_slots(self, slots: List[ApiSlot]) -> None:
        existing = _read_json_or(self.slots_state_path, [])
        existing_by_id = {
            str(item.get("slot_id")): item
            for item in existing
            if isinstance(item, dict) and str(item.get("slot_id", "")).strip()
        }
        merged: List[Dict[str, Any]] = []
        self.home_slot_configs = {}
        for slot in slots:
            base = self._slot_state_default(slot)
            self.home_slot_configs[slot.slot_id] = copy.deepcopy(base["config"])
            old = existing_by_id.get(slot.slot_id)
            if isinstance(old, dict):
                old_config = normalize_api_config(old.get("config"))
                preserve_override = bool(old.get("uses_override", False))
                if old_config is not None and not api_config_equal(old_config, base["config"]):
                    preserve_override = True
                base.update(
                    {
                        "status": old.get("status", base["status"]),
                        "assigned_case_id": old.get("assigned_case_id"),
                        "resource_id": str(old.get("resource_id") or base["resource_id"]),
                        "uses_override": preserve_override,
                        "current_stage": old.get("current_stage", ""),
                        "blocked_kind": old.get("blocked_kind", ""),
                        "blocked_message": old.get("blocked_message", ""),
                        "blocked_at": old.get("blocked_at"),
                        "resume_requested": bool(old.get("resume_requested", False)),
                        "retry_count": int(old.get("retry_count", 0) or 0),
                        "next_retry_at": old.get("next_retry_at"),
                        "last_error": old.get("last_error", ""),
                    }
                )
                if preserve_override and old_config is not None:
                    base["config"] = old_config
                    base["resource_id"] = resource_id_from_config(old_config)
                    base["api"] = {
                        "base_url": old_config["base_url"],
                        "api_key_masked": _mask_secret(old_config["api_key"]),
                    }
            merged.append(base)
        with self.state_lock:
            self.slot_order = [str(item["slot_id"]) for item in merged]
            self.slot_states = {str(item["slot_id"]): item for item in merged}
            self._slot_states_dirty = True
        self._persist_slot_states(force=True)
        self._load_resource_states(slots)

    def _persist_slot_states(self, *, force: bool = False) -> None:
        with self.state_lock:
            if not self.slot_states:
                return
            if not force and not self._slot_states_dirty:
                return
            payload = [copy.deepcopy(self.slot_states[slot_id]) for slot_id in self.slot_order if slot_id in self.slot_states]
            self._slot_states_dirty = False
        _atomic_write_json(self.slots_state_path, payload)

    def _load_resource_states(self, slots: List[ApiSlot]) -> None:
        existing = _read_json_or(self.resources_state_path, [])
        existing_by_id = {
            str(item.get("resource_id")): item
            for item in existing
            if isinstance(item, dict) and str(item.get("resource_id", "")).strip()
        }
        candidate_configs = collect_unique_resource_configs(
            list(self.home_slot_configs.values())
            + [item.get("config") for item in self.slot_states.values()]
            + [{"api_key": slot.api_key, "base_url": slot.base_url} for slot in slots]
        )
        merged: List[Dict[str, Any]] = []
        for config in candidate_configs:
            base = resource_state_default(config=config, mask_secret=_mask_secret, now_iso=_now_iso)
            old = existing_by_id.get(base["resource_id"])
            if isinstance(old, dict):
                base.update(
                    {
                        "status": old.get("status", base["status"]),
                        "blocked_kind": old.get("blocked_kind", ""),
                        "blocked_message": old.get("blocked_message", ""),
                        "blocked_at": old.get("blocked_at"),
                    }
                )
            merged.append(base)
        with self.state_lock:
            self.resource_order = [str(item["resource_id"]) for item in merged]
            self.resource_states = {str(item["resource_id"]): item for item in merged}
            self._resource_states_dirty = True
        self._persist_resource_states(force=True)

    def _persist_resource_states(self, *, force: bool = False) -> None:
        with self.state_lock:
            if not self.resource_states:
                return
            if not force and not self._resource_states_dirty:
                return
            payload = [
                copy.deepcopy(self.resource_states[resource_id])
                for resource_id in self.resource_order
                if resource_id in self.resource_states
            ]
            self._resource_states_dirty = False
        _atomic_write_json(self.resources_state_path, payload)

    def _case_root_dir(self, case_id: str) -> Path:
        return self.run_dir / "cases" / case_id

    def _case_state_path(self, case_id: str) -> Path:
        return self._case_root_dir(case_id) / "state.json"

    def _case_state_default(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        default = {
            "case_id": spec["case_id"],
            "spec_index": spec["spec_index"],
            "case_name": spec["case_name"],
            "environment": spec["environment"],
            "case_path": spec["case_path"],
            "relative_case_path": spec["relative_case_path"],
            "relative_traj_path": spec["relative_traj_path"],
            "status": "pending",
            "assigned_slot_id": None,
            "current_stage": "",
            "attempt_count": 0,
            "last_attempt_dir": "",
            "output_traj_path": "",
            "failure_reason": "",
            "last_error": "",
            "success_at": None,
            "updated_at": _now_iso(),
        }
        output_traj_path = self.output_root / spec["relative_traj_path"]
        if output_traj_path.exists():
            traj_data = _read_json_or(output_traj_path, {})
            if isinstance(traj_data, dict) and str(traj_data.get("status") or "") == "finished":
                default["status"] = "succeeded"
                default["output_traj_path"] = str(output_traj_path)
                default["success_at"] = _now_iso()
        return default

    def _next_attempt_dir(self, case_id: str) -> Path:
        root = self._case_root_dir(case_id) / "attempts"
        ensure_dir(root)
        existing = sorted(
            [
                path
                for path in root.iterdir()
                if path.is_dir() and path.name.startswith("attempt_") and path.name[8:].isdigit()
            ]
        )
        next_idx = len(existing) + 1
        return root / f"attempt_{next_idx:02d}"

    def _load_case_state(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        cached = self.case_states.get(str(spec["case_id"]))
        if isinstance(cached, dict) and cached:
            return copy.deepcopy(cached)
        path = self._case_state_path(spec["case_id"])
        existing = _read_json_or(path, {})
        if isinstance(existing, dict) and existing:
            output_traj_path = self.output_root / spec["relative_traj_path"]
            if str(existing.get("status")) != "succeeded" and output_traj_path.exists():
                traj_data = _read_json_or(output_traj_path, {})
                if isinstance(traj_data, dict) and str(traj_data.get("status") or "") == "finished":
                    existing["status"] = "succeeded"
                    existing["assigned_slot_id"] = None
                    existing["output_traj_path"] = str(output_traj_path)
                    existing["success_at"] = existing.get("success_at") or _now_iso()
                    self._save_case_state(existing)
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

    def _update_resource_state(self, resource_id: str, updater, *, flush: bool = False) -> Dict[str, Any]:
        with self.state_lock:
            item = copy.deepcopy(self.resource_states.get(resource_id) or {})
            if not item:
                return {}
            new_item = updater(item)
            new_item["updated_at"] = _now_iso()
            self.resource_states[resource_id] = new_item
            self._resource_states_dirty = True
            selected = copy.deepcopy(new_item)
        if flush:
            self._persist_resource_states(force=True)
        return selected

    def _blocked_resource_items(self) -> List[Dict[str, Any]]:
        with self.state_lock:
            items = [
                blocked_resource_payload(item)
                for item in self.resource_states.values()
            ]
        return [item for item in items if item is not None]

    def _clear_blocked_resources(self) -> None:
        with self.state_lock:
            for resource_id, item in list(self.resource_states.items()):
                updated = copy.deepcopy(item)
                updated.update(
                    {
                        "status": "available",
                        "blocked_kind": "",
                        "blocked_message": "",
                        "blocked_at": None,
                        "updated_at": _now_iso(),
                    }
                )
                self.resource_states[resource_id] = updated
            self._resource_states_dirty = True
        self._persist_resource_states(force=True)

    def _mark_resource_blocked(self, config: Dict[str, str], error: BatchRecoverableAPIError) -> str:
        resource_id = resource_id_from_config(config)
        if not resource_id:
            return ""
        self._update_resource_state(
            resource_id,
            lambda item: {
                **item,
                "status": "blocked",
                "blocked_kind": error.kind,
                "blocked_message": error.message,
                "blocked_at": _now_iso(),
            },
            flush=True,
        )
        return resource_id

    def _select_replacement_resource(self, *, exclude: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        excluded = {str(item) for item in (exclude or []) if str(item)}
        with self.state_lock:
            if not self.resource_order:
                return None
            total = len(self.resource_order)
            start = self._replacement_cursor % total
            for offset in range(total):
                idx = (start + offset) % total
                resource_id = self.resource_order[idx]
                if resource_id in excluded:
                    continue
                item = self.resource_states.get(resource_id)
                if not isinstance(item, dict):
                    continue
                if str(item.get("status") or "") == "blocked":
                    continue
                self._replacement_cursor = idx + 1
                return copy.deepcopy(item)
        return None

    def _assign_slot_resource(self, slot_id: str, *, case_id: str, stage: str, resource: Dict[str, Any]) -> Dict[str, Any]:
        config = normalize_api_config(resource.get("config"))
        if config is None:
            return {}
        home_config = self.home_slot_configs.get(slot_id) or {}
        uses_override = not api_config_equal(config, home_config)
        return self._update_slot_state(
            slot_id,
            lambda item: {
                **item,
                "status": "running",
                "assigned_case_id": case_id,
                "current_stage": stage,
                "resource_id": str(resource.get("resource_id") or resource_id_from_config(config)),
                "uses_override": uses_override,
                "config": copy.deepcopy(config),
                "api": {
                    "base_url": config["base_url"],
                    "api_key_masked": _mask_secret(config["api_key"]),
                },
                "resume_requested": False,
                "blocked_kind": "",
                "blocked_message": "",
                "blocked_at": None,
                "retry_count": 0,
                "next_retry_at": None,
                "last_error": "",
            },
            flush=True,
        )

    def _replace_exhausted_slot_resource(
        self,
        *,
        slot_id: str,
        case_id: str,
        stage: str,
        error: BatchRecoverableAPIError,
    ) -> Optional[Dict[str, Any]]:
        slot_state = self._slot_state(slot_id)
        current_config = normalize_api_config(slot_state.get("config"))
        if current_config is None:
            return None
        exhausted_resource_id = self._mark_resource_blocked(current_config, error)
        replacement = self._select_replacement_resource(exclude=[exhausted_resource_id])
        if replacement is None:
            return None
        updated_slot = self._assign_slot_resource(slot_id, case_id=case_id, stage=stage, resource=replacement)
        return {
            "exhausted_resource_id": exhausted_resource_id,
            "replacement_resource_id": str(replacement.get("resource_id") or ""),
            "updated_slot": updated_slot,
        }

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
                if latest is not None and not bool(item.get("uses_override", False)):
                    item["api"] = {
                        "base_url": latest.base_url,
                        "api_key_masked": _mask_secret(latest.api_key),
                    }
                    item["config"] = {
                        "api_key": latest.api_key,
                        "base_url": latest.base_url,
                    }
                    item["resource_id"] = resource_id_from_config(item["config"])
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
            resources = _read_json_or(self.resources_state_path, [])
            if isinstance(resources, list):
                cleared = []
                for item in resources:
                    if not isinstance(item, dict):
                        continue
                    updated_item = copy.deepcopy(item)
                    updated_item.update(
                        {
                            "status": "available",
                            "blocked_kind": "",
                            "blocked_message": "",
                            "blocked_at": None,
                            "updated_at": _now_iso(),
                        }
                    )
                    cleared.append(updated_item)
                _atomic_write_json(self.resources_state_path, cleared)
            print(
                "[TRAJ-BATCH][RESUME-SIGNAL] "
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

    def _build_executor_for_slot(self) -> TrajectoryBatchExecutor:
        return self.executor_cls(self.settings)

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

    def _refresh_run_state(self, *, state: str) -> None:
        self._persist_slot_states(force=True)
        self._persist_resource_states(force=True)
        counts = self._count_case_statuses()
        with self.state_lock:
            blocked_slots = [
                {
                    "slot_id": item.get("slot_id"),
                    "name": item.get("name"),
                    "assigned_case_id": item.get("assigned_case_id"),
                    "blocked_kind": item.get("blocked_kind"),
                }
                for item in self.slot_states.values()
                if isinstance(item, dict) and str(item.get("status")) == "blocked"
            ]
            blocked_api_resources = self._blocked_resource_items()
        self._write_run_state(
            {
                "run_name": self.run_dir.name,
                "state": state,
                "leader_pid": os.getpid(),
                "success_count": counts["success_count"],
                "failed_count": counts["failed_count"],
                "running_count": counts["running_count"],
                "total_cases": len(self.plan),
                "blocked_slots": blocked_slots,
                "blocked_api_resources": blocked_api_resources,
            }
        )

    def _slot_worker(self, slot_id: str) -> None:
        executor = self._build_executor_for_slot()
        while not self.stop_event.is_set():
            if self._all_cases_terminal():
                self._mark_slot_idle(slot_id)
                return

            slot_state = self._slot_state(slot_id)
            if not slot_state:
                return

            status = str(slot_state.get("status", "idle"))
            assigned_case_id = slot_state.get("assigned_case_id")
            if status == "blocked":
                if bool(slot_state.get("resume_requested")):
                    self._update_slot_state(
                        slot_id,
                        lambda item: {
                            **item,
                            "status": "running",
                            "resume_requested": False,
                            "blocked_kind": "",
                            "blocked_message": "",
                            "blocked_at": None,
                            "next_retry_at": None,
                        },
                    )
                    continue
                time.sleep(DEFAULT_STAGE_POLL_SECONDS)
                continue

            if status == "retrying":
                next_retry_at = str(slot_state.get("next_retry_at") or "")
                retry_allowed = True
                if next_retry_at:
                    try:
                        retry_allowed = datetime.fromisoformat(next_retry_at) <= datetime.now(timezone.utc)
                    except Exception:
                        retry_allowed = True
                if not retry_allowed:
                    time.sleep(DEFAULT_STAGE_POLL_SECONDS)
                    continue
                self._update_slot_state(
                    slot_id,
                    lambda item: {**item, "status": "running", "next_retry_at": None},
                )
                continue

            spec = None
            if assigned_case_id:
                for item in self.plan:
                    if item["case_id"] == assigned_case_id:
                        spec = item
                        break
            if spec is None:
                spec = self._claim_next_case_for_slot(slot_id)
            if spec is None:
                if self._all_cases_terminal():
                    self._mark_slot_idle(slot_id)
                    return
                time.sleep(DEFAULT_STAGE_POLL_SECONDS)
                continue

            output_traj_path = self.output_root / spec["relative_traj_path"]
            case_state = self._load_case_state(spec)
            if output_traj_path.exists() and str(case_state.get("status")) != "succeeded":
                traj_data = _read_json_or(output_traj_path, {})
                if isinstance(traj_data, dict) and str(traj_data.get("status") or "") == "finished":
                    case_state["status"] = "succeeded"
                    case_state["assigned_slot_id"] = None
                    case_state["output_traj_path"] = str(output_traj_path)
                    case_state["success_at"] = case_state.get("success_at") or _now_iso()
                    self._save_case_state(case_state)
                    self._mark_slot_idle(slot_id)
                    continue

            case_state["assigned_slot_id"] = slot_id
            case_state["status"] = "running"
            case_state["current_stage"] = "traj"
            case_state["failure_reason"] = ""
            self._save_case_state(case_state)
            self._mark_slot_busy(slot_id, spec["case_id"], "traj")

            attempt_dir = self._next_attempt_dir(spec["case_id"])
            ensure_dir(attempt_dir)
            case_state["attempt_count"] = int(case_state.get("attempt_count", 0) or 0) + 1
            case_state["last_attempt_dir"] = str(attempt_dir)
            self._save_case_state(case_state)

            try:
                payload = executor.run_case(
                    spec=spec,
                    slot_state=self._slot_state(slot_id),
                    output_traj_path=output_traj_path,
                    attempt_dir=attempt_dir,
                )
            except BatchRecoverableAPIError as exc:
                if self.stop_event.is_set():
                    case_state["status"] = "running"
                    case_state["current_stage"] = exc.stage_name
                    case_state["last_error"] = exc.message
                    self._save_case_state(case_state)
                    return
                slot_state = self._slot_state(slot_id)
                if exc.kind in AUTO_RETRY_KINDS:
                    case_state["status"] = "running"
                    case_state["current_stage"] = exc.stage_name
                    case_state["last_error"] = exc.message
                    self._save_case_state(case_state)
                    self._mark_slot_retrying(slot_id, spec["case_id"], exc.stage_name, exc)
                    print(
                        "[TRAJ-BATCH][API-RETRY] "
                        f"slot={slot_state.get('name')} case={spec['relative_case_path']} "
                        f"stage={exc.stage_name} kind={exc.kind} error={exc.message}",
                        flush=True,
                    )
                else:
                    failover = None
                    if exc.kind in MANUAL_BLOCK_KINDS and is_confirmed_balance_exhaustion(exc.message):
                        failover = self._replace_exhausted_slot_resource(
                            slot_id=slot_id,
                            case_id=spec["case_id"],
                            stage=exc.stage_name,
                            error=exc,
                        )
                    if failover is not None:
                        case_state["status"] = "running"
                        case_state["current_stage"] = exc.stage_name
                        case_state["last_error"] = exc.message
                        self._save_case_state(case_state)
                        replaced_slot = self._slot_state(slot_id)
                        print(
                            "[TRAJ-BATCH][API-FAILOVER] "
                            f"slot={replaced_slot.get('name')} case={spec['relative_case_path']} "
                            f"stage={exc.stage_name} kind={exc.kind} "
                            f"retired_resource={failover['exhausted_resource_id']} "
                            f"replacement_resource={failover['replacement_resource_id']}",
                            flush=True,
                        )
                        continue
                    case_state["status"] = "blocked" if exc.kind in MANUAL_BLOCK_KINDS else "running"
                    case_state["current_stage"] = exc.stage_name
                    case_state["last_error"] = exc.message
                    self._save_case_state(case_state)
                    self._mark_slot_blocked(slot_id, spec["case_id"], exc.stage_name, exc)
                    print(
                        "[TRAJ-BATCH][API-BLOCKED] "
                        f"slot={slot_state.get('name')} case={spec['relative_case_path']} "
                        f"stage={exc.stage_name} kind={exc.kind} error={exc.message}",
                        flush=True,
                    )
                continue
            except Exception as exc:
                if self.stop_event.is_set():
                    case_state["status"] = "running"
                    case_state["current_stage"] = "traj"
                    case_state["last_error"] = str(exc)
                    self._save_case_state(case_state)
                    return
                case_state["status"] = "failed"
                case_state["failure_reason"] = str(exc)
                case_state["assigned_slot_id"] = None
                case_state["current_stage"] = "traj"
                case_state["last_error"] = str(exc)
                self._save_case_state(case_state)
                slot_state = self._slot_state(slot_id)
                self._mark_slot_idle(slot_id)
                print(
                    "[TRAJ-BATCH][CASE-FAILED] "
                    f"slot={slot_state.get('name')} case={spec['relative_case_path']} reason={exc}",
                    flush=True,
                )
                continue

            case_state["status"] = "succeeded"
            case_state["assigned_slot_id"] = None
            case_state["output_traj_path"] = str(output_traj_path)
            case_state["success_at"] = _now_iso()
            case_state["current_stage"] = ""
            case_state["last_error"] = ""
            self._save_case_state(case_state)
            self._mark_slot_idle(slot_id)

    def run(self) -> None:
        if self.settings.resume and self._maybe_signal_resume_only():
            return

        existing_state = self._read_run_state()
        existing_counts = self._count_case_statuses()
        if (
            not self.settings.resume
            and (
                int(existing_counts["success_count"]) > 0
                or int(existing_counts["failed_count"]) > 0
                or int(existing_state.get("running_count", 0) or 0) > 0
            )
        ):
            raise RuntimeError(
                f"Run directory {self.run_dir} already has progress. Use --resume to continue from checkpoints."
            )

        if not self.master_lock.acquire():
            leader_pid = self._read_run_state().get("leader_pid")
            raise RuntimeError(
                f"Batch trajectory master is already running for {self.run_dir} (pid={leader_pid}). "
                "Use --resume to signal blocked APIs."
            )

        try:
            self._install_signal_handlers()
            self._load_or_init_plan()
            slots = load_api_slots(self.settings.api_slots_json)
            self._load_slots(slots)
            self._initialize_case_runtime_state()

            if self.settings.resume:
                self._clear_blocked_resources()
                with self.state_lock:
                    for slot_id, item in list(self.slot_states.items()):
                        if str(item.get("status")) == "blocked":
                            updated = copy.deepcopy(item)
                            updated["resume_requested"] = True
                            updated["updated_at"] = _now_iso()
                            self.slot_states[slot_id] = updated
                    self._slot_states_dirty = True
                self._persist_slot_states(force=True)

            self._refresh_run_state(state="running")
            self._write_master_event(
                "start",
                {
                    "resume": self.settings.resume,
                    "slot_count": len(slots),
                    "cases_dir": str(self.settings.cases_dir),
                    "traj_output_root": str(self.output_root),
                    "eval_model": self.settings.eval_model,
                    "total_cases": len(self.plan),
                },
            )

            self.workers = []
            for slot in slots:
                thread = threading.Thread(
                    target=self._slot_worker,
                    name=f"traj-batch-{slot.slot_id}",
                    args=(slot.slot_id,),
                    daemon=True,
                )
                thread.start()
                self.workers.append(thread)

            while not self.stop_event.is_set():
                self._refresh_run_state(state="running")
                if self._all_cases_terminal():
                    break
                alive = [t for t in self.workers if t.is_alive()]
                if not alive:
                    break
                time.sleep(DEFAULT_STAGE_POLL_SECONDS)

            for thread in self.workers:
                if thread.is_alive():
                    thread.join(timeout=0.1)

            final_counts = self._count_case_statuses()
            final_state = "completed" if self._all_cases_terminal() else "paused"
            if self.stop_event.is_set() and final_state != "completed":
                final_state = "paused"
            self._refresh_run_state(state=final_state)
            self._write_master_event(
                "finish",
                {
                    "final_state": final_state,
                    "success_count": final_counts["success_count"],
                    "failed_count": final_counts["failed_count"],
                },
            )
        finally:
            self.master_lock.release()


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


def build_run_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch trajectory generation in OpenAI-compatible tool-calling mode.")
    parser.add_argument("--run_name", type=str, required=True, help="Logical batch run name")
    parser.add_argument("--api_slots_json", type=str, required=True, help="JSON file containing API slots")
    parser.add_argument("--cases_dir", type=str, required=True, help="Root directory containing case json files")
    parser.add_argument(
        "--traj_output_dir_name",
        type=str,
        required=True,
        help="Sibling directory name for generated trajectory files",
    )
    parser.add_argument("--eval_model", type=str, required=True, help="Trajectory generation model")
    parser.add_argument("--max_steps", type=int, default=30)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max_tokens", type=int, default=12000)
    parser.add_argument("--timeout_seconds", type=int, default=180)
    parser.add_argument("--network_max_retries", type=int, default=2)
    parser.add_argument("--parallel_tool_calls", type=int, choices=[0, 1], default=None)
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help=(
            "Optional explicit choices count for GPT-family models. "
            "For example, --n 1 requests one choice, but some endpoints may still return multiple choices."
        ),
    )
    parser.add_argument("--tool_choice", type=str, default="auto")
    parser.add_argument("--resume", action="store_true", help="Resume existing run or signal blocked APIs")
    return parser
