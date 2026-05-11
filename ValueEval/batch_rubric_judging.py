from __future__ import annotations

import argparse
import copy
import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
from core.api_slots import ApiSlot, load_api_slots

from .batch_common import (
    AUTO_RETRY_KINDS,
    DEFAULT_STAGE_POLL_SECONDS,
    MANUAL_BLOCK_KINDS,
    BatchRecoverableAPIError,
    BatchCoordinatorBase,
    FileLock,
    _append_jsonl,
    _atomic_write_json,
    _atomic_write_text,
    _classify_llm_error,
    _mask_secret,
    _now_iso,
    _process_alive,
    _read_json_or,
    discover_case_files,
    render_progress_bar,
    show_blocked_slots,
    watch_progress,
)
from .rubric_trajectory_judge import ValueEvalSettings, RubricTrajectoryJudge


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT_DIR / "ValueEval" / "judge_batch_runs"
MASTER_LOCK_NAME = "master.lock"
RUN_STATE_NAME = "run_state.json"
PLAN_NAME = "plan.json"
SLOTS_NAME = "api_slots_state.json"
RESOURCES_NAME = "api_resources_state.json"
MASTER_LOG_NAME = "master_events.jsonl"


def _parse_models(raw: str) -> List[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


def _discover_named_json_files(root: Path) -> Dict[str, Path]:
    files = discover_case_files(root)
    mapping: Dict[str, Path] = {}
    for path in files:
        name = path.name
        previous = mapping.get(name)
        if previous is not None:
            raise ValueError(f"Duplicate file name under {root}: {name} ({previous}, {path})")
        mapping[name] = path
    return mapping


def _file_mtime_ns(path: Path) -> Optional[int]:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def _result_is_newer_than_traj(result_path: Path, traj_path: Path) -> bool:
    result_mtime = _file_mtime_ns(result_path)
    traj_mtime = _file_mtime_ns(traj_path)
    if result_mtime is None or traj_mtime is None:
        return False
    return result_mtime > traj_mtime


def build_judge_plan(
    *,
    case_root: Path,
    rubric_root: Path,
    traj_root: Path,
    result_output_dir_name: str,
) -> Dict[str, Any]:
    output_root = case_root.parent / str(result_output_dir_name).strip()
    case_files = discover_case_files(case_root)
    rubric_files = _discover_named_json_files(rubric_root)
    traj_files = _discover_named_json_files(traj_root)

    items: List[Dict[str, Any]] = []
    for idx, case_path in enumerate(case_files, start=1):
        case_stem = case_path.stem
        rubric_name = f"{case_stem}_rubric.json"
        traj_name = f"{case_stem}_traj.json"
        rubric_path = rubric_files.get(rubric_name)
        traj_path = traj_files.get(traj_name)
        # Judge only aligned case/rubric/traj triples. Missing trajectories should not
        # block the whole batch; they are skipped here so that every available traj can
        # still be judged against its correctly matched rubric.
        if rubric_path is None or traj_path is None:
            continue

        rel_case_path = case_path.relative_to(case_root)
        items.append(
            {
                "spec_index": len(items),
                "case_id": f"judge_case_{len(items) + 1:05d}",
                "case_stem": case_stem,
                "case_path": str(case_path.resolve()),
                "relative_case_path": rel_case_path.as_posix(),
                "rubric_path": str(rubric_path.resolve()),
                "relative_rubric_path": rubric_name,
                "traj_path": str(traj_path.resolve()),
                "relative_traj_path": traj_name,
                "relative_result_path": f"{case_stem}_result.json",
            }
        )

    if not items:
        raise ValueError(f"No aligned case/rubric/traj triples found under {case_root}")

    return {
        "case_root": str(case_root.resolve()),
        "rubric_root": str(rubric_root.resolve()),
        "traj_root": str(traj_root.resolve()),
        "result_output_root": str(output_root.resolve()),
        "items": items,
    }


@dataclass
class JudgeBatchSettings:
    api_slots_json: Path
    cases_dir: Path
    rubric_dir: Path
    traj_dir: Path
    result_output_dir_name: str
    judge_models: List[str]
    temperature: float
    max_tokens: int
    timeout_seconds: int
    network_max_retries: int
    max_json_retries: int
    resume: bool = False


class PersistentJudgeExecutor:
    def __init__(self, settings: ValueEvalSettings) -> None:
        self.settings = settings
        self.runner = RubricTrajectoryJudge(settings=settings)

    @staticmethod
    def _attempt_raw_path(trace_dir: Path, trace_tag: str, attempt: int) -> Path:
        return trace_dir / f"{trace_tag}_attempt_{attempt}_raw.txt"

    @staticmethod
    def _attempt_resp_path(trace_dir: Path, trace_tag: str, attempt: int) -> Path:
        return trace_dir / f"{trace_tag}_attempt_{attempt}_resp.json"

    @staticmethod
    def _attempt_invalid_path(trace_dir: Path, trace_tag: str, attempt: int) -> Path:
        return trace_dir / f"{trace_tag}_attempt_{attempt}_parsed_invalid.json"

    @staticmethod
    def _final_path(trace_dir: Path, trace_tag: str) -> Path:
        return trace_dir / f"{trace_tag}_final.json"

    @staticmethod
    def _result_looks_complete(payload: Any, expected_case_name: str, expected_models: int) -> bool:
        if not isinstance(payload, dict):
            return False
        if str(payload.get("case_name", "")).strip() != expected_case_name:
            return False
        judge_outputs = payload.get("judge_outputs")
        return isinstance(judge_outputs, list) and len(judge_outputs) == expected_models

    def _load_saved_attempt(self, trace_dir: Path, trace_tag: str, attempt: int) -> Optional[Dict[str, Any]]:
        resp_path = self._attempt_resp_path(trace_dir, trace_tag, attempt)
        raw_path = self._attempt_raw_path(trace_dir, trace_tag, attempt)
        if not resp_path.exists():
            return None
        resp = _read_json_or(resp_path, {})
        if not isinstance(resp, dict):
            return None
        if not bool(resp.get("ok", False)) and str(resp.get("error", "")).strip():
            return None
        if raw_path.exists():
            raw = raw_path.read_text(encoding="utf-8")
        else:
            raw = str(resp.get("content", "") or "")
            _atomic_write_text(raw_path, raw)
        return {"resp": resp, "raw": raw}

    def _save_attempt(self, trace_dir: Path, trace_tag: str, attempt: int, resp: Dict[str, Any], raw: str) -> None:
        _atomic_write_text(self._attempt_raw_path(trace_dir, trace_tag, attempt), raw)
        _atomic_write_json(self._attempt_resp_path(trace_dir, trace_tag, attempt), resp)

    def _load_saved_final(
        self,
        trace_dir: Path,
        trace_tag: str,
        *,
        case_name: str,
        rubric_pack: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        final_path = self._final_path(trace_dir, trace_tag)
        if not final_path.exists():
            return None
        payload = _read_json_or(final_path, {})
        if not isinstance(payload, dict):
            return None
        if not self.runner._validate_judgment(payload, case_name, rubric_pack):
            return None
        return payload

    def run_case(
        self,
        *,
        case_path: Path,
        rubric_path: Path,
        traj_path: Path,
        result_path: Path,
        trace_dir: Path,
    ) -> Dict[str, Any]:
        request = self.runner.build_judge_request(
            case_path=str(case_path),
            traj_path=str(traj_path),
            rubric_path=str(rubric_path),
        )
        case_name = str(request["case_name"])
        rubric_pack = request["rubric_pack"]
        judge_prompt = str(request["user_prompt"])
        trace_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = trace_dir / "judge_prompt.txt"

        judge_models = self.settings.resolved_judge_models()
        result_is_newer_than_traj = _result_is_newer_than_traj(result_path, traj_path)
        if result_is_newer_than_traj:
            existing = _read_json_or(result_path, {})
            if self._result_looks_complete(existing, case_name, len(judge_models)):
                return {
                    "case_name": case_name,
                    "result_path": str(result_path),
                    "result": existing,
                }
        _atomic_write_text(prompt_path, judge_prompt)
        reuse_saved_judge_artifacts = not result_path.exists()

        messages = [
            {"role": "system", "content": request["system_prompt"]},
            {"role": "user", "content": judge_prompt},
        ]

        judge_outputs: List[Dict[str, Any]] = []
        for model in judge_models:
            trace_tag = f"judge_{model.replace('/', '_')}"
            if reuse_saved_judge_artifacts:
                saved_final = self._load_saved_final(
                    trace_dir,
                    trace_tag,
                    case_name=case_name,
                    rubric_pack=rubric_pack,
                )
                if saved_final is not None:
                    judge_outputs.append({"model": model, "judgment": saved_final})
                    continue

            saw_api_error = False
            last_api_error = ""
            last_invalid_error = "unknown invalid judge output"

            for attempt in range(1, self.settings.max_json_retries + 1):
                saved = (
                    self._load_saved_attempt(trace_dir, trace_tag, attempt)
                    if reuse_saved_judge_artifacts
                    else None
                )
                if saved is None:
                    resp = self.runner._chat_once(
                        model,
                        messages,
                        max_tokens=self.settings.max_tokens,
                        temperature=self.settings.temperature,
                    )
                    raw = str(resp.get("content", "") or "") if isinstance(resp, dict) else ""
                    self._save_attempt(trace_dir, trace_tag, attempt, resp, raw)
                else:
                    resp = saved["resp"]
                    raw = saved["raw"]

                if not bool(resp.get("ok", False)) and str(resp.get("error", "")).strip():
                    saw_api_error = True
                    last_api_error = str(resp.get("error", "")).strip()
                    continue

                parsed = self.runner._parse_json_content(raw)
                if parsed is None:
                    last_invalid_error = "judge response is not valid JSON"
                    continue

                if not self.runner._validate_judgment(parsed, case_name, rubric_pack):
                    last_invalid_error = "judge parsed JSON does not satisfy judgment schema"
                    invalid_path = self._attempt_invalid_path(trace_dir, trace_tag, attempt)
                    if not invalid_path.exists():
                        _atomic_write_json(invalid_path, parsed)
                    continue

                _atomic_write_json(self._final_path(trace_dir, trace_tag), parsed)
                judge_outputs.append({"model": model, "judgment": parsed})
                break
            else:
                if saw_api_error:
                    raise BatchRecoverableAPIError(
                        kind=_classify_llm_error(last_api_error),
                        message=last_api_error,
                        stage_name=trace_tag,
                    )
                raise ValueError(
                    f"Judgment failed after {self.settings.max_json_retries} JSON attempts for {model}: {last_invalid_error}"
                )

        result = {
            "module": "ValueEval_judge",
            "generated_at_utc": _now_iso(),
            "case_path": str(case_path),
            "traj_path": str(traj_path),
            "case_name": case_name,
            "rubric_path": str(rubric_path),
            "judge_outputs": judge_outputs,
        }
        ensure_dir(result_path.parent)
        _atomic_write_json(result_path, result)
        result["result_path"] = str(result_path.resolve())
        return {
            "case_name": case_name,
            "result_path": str(result_path),
            "result": result,
        }


class BatchJudgeCoordinator(BatchCoordinatorBase):
    def __init__(self, *, run_dir: Path, settings: JudgeBatchSettings) -> None:
        self.run_dir = run_dir
        self.settings = settings
        self.master_lock = FileLock(self.run_dir / MASTER_LOCK_NAME)
        self.state_lock = threading.RLock()
        self.stop_event = threading.Event()
        self.workers: List[threading.Thread] = []
        self.plan_bundle = build_judge_plan(
            case_root=settings.cases_dir,
            rubric_root=settings.rubric_dir,
            traj_root=settings.traj_dir,
            result_output_dir_name=settings.result_output_dir_name,
        )
        self.plan = self.plan_bundle["items"]
        self.plan_by_case_id = {str(item["case_id"]): item for item in self.plan}
        self.output_root = Path(self.plan_bundle["result_output_root"])
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

    def _slot_state_default(self, slot: ApiSlot) -> Dict[str, Any]:
        config = {
            "api_key": slot.gen_api_key,
            "base_url": slot.gen_base_url,
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
            payload = [
                copy.deepcopy(self.slot_states[slot_id])
                for slot_id in self.slot_order
                if slot_id in self.slot_states
            ]
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
            + [{"api_key": slot.gen_api_key, "base_url": slot.gen_base_url} for slot in slots]
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

    def _case_trace_dir(self, case_id: str) -> Path:
        return self._case_root_dir(case_id) / "trace_judge"

    def _case_state_default(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        default = {
            "case_id": spec["case_id"],
            "spec_index": spec["spec_index"],
            "case_stem": spec["case_stem"],
            "case_path": spec["case_path"],
            "relative_case_path": spec["relative_case_path"],
            "rubric_path": spec["rubric_path"],
            "relative_rubric_path": spec["relative_rubric_path"],
            "traj_path": spec["traj_path"],
            "relative_traj_path": spec["relative_traj_path"],
            "relative_result_path": spec["relative_result_path"],
            "status": "pending",
            "assigned_slot_id": None,
            "current_stage": "",
            "case_name": "",
            "result_path": "",
            "failure_reason": "",
            "last_error": "",
            "success_at": None,
            "updated_at": _now_iso(),
        }
        output_result_path = self.output_root / spec["relative_result_path"]
        if self._case_result_is_reusable(spec):
            result = _read_json_or(output_result_path, {})
            default["status"] = "succeeded"
            default["result_path"] = str(output_result_path)
            default["case_name"] = str(result.get("case_name") or spec["case_stem"])
            default["success_at"] = _now_iso()
        return default

    def _case_result_is_reusable(self, spec: Dict[str, Any]) -> bool:
        output_result_path = self.output_root / spec["relative_result_path"]
        if not _result_is_newer_than_traj(output_result_path, Path(spec["traj_path"])):
            return False
        result = _read_json_or(output_result_path, {})
        case_payload = _read_json_or(Path(spec["case_path"]), {})
        expected_case_name = (
            str(case_payload.get("case_name") or spec["case_stem"])
            if isinstance(case_payload, dict)
            else str(spec["case_stem"])
        )
        return PersistentJudgeExecutor._result_looks_complete(
            result,
            expected_case_name,
            len(self.settings.judge_models),
        )

    def _load_case_state(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        state = super()._load_case_state(spec)
        reusable_result = self._case_result_is_reusable(spec)
        output_result_path = self.output_root / spec["relative_result_path"]
        changed = False

        if reusable_result:
            if str(state.get("status") or "") != "succeeded":
                state["status"] = "succeeded"
                changed = True
            if str(state.get("result_path") or "") != str(output_result_path):
                state["result_path"] = str(output_result_path)
                changed = True
            if not state.get("success_at"):
                state["success_at"] = _now_iso()
                changed = True
        elif str(state.get("status") or "") == "succeeded":
            state["status"] = "pending"
            state["assigned_slot_id"] = None
            state["current_stage"] = ""
            state["result_path"] = ""
            state["success_at"] = None
            changed = True

        with self.state_lock:
            self.case_states[str(spec["case_id"])] = copy.deepcopy(state)
        if changed:
            self._save_case_state(state)
        return copy.deepcopy(state)

    def _run_dir_has_progress(self) -> bool:
        state = self._read_run_state()
        if isinstance(state, dict) and state:
            for key in ["success_count", "failed_count", "running_count"]:
                try:
                    if int(state.get(key, 0) or 0) > 0:
                        return True
                except Exception:
                    continue

        slots_state = _read_json_or(self.slots_state_path, [])
        if isinstance(slots_state, list) and slots_state:
            return True

        for spec in self.plan:
            case_state_path = self._case_state_path(str(spec["case_id"]))
            if case_state_path.exists():
                return True
        return False

    def _build_executor_for_slot(self, slot_state: Dict[str, Any]) -> PersistentJudgeExecutor:
        config = slot_state.get("config", {}) if isinstance(slot_state, dict) else {}
        settings = ValueEvalSettings(
            api_key=str(config.get("api_key") or ""),
            base_url=str(config.get("base_url") or ""),
            judge_models=list(self.settings.judge_models),
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            timeout_seconds=self.settings.timeout_seconds,
            network_max_retries=self.settings.network_max_retries,
            max_json_retries=self.settings.max_json_retries,
        )
        return PersistentJudgeExecutor(settings=settings)

    def _sync_slot_state_from_disk(self, slot_id: str) -> Dict[str, Any]:
        payload = _read_json_or(self.slots_state_path, [])
        if not isinstance(payload, list):
            return self._slot_state(slot_id)
        for item in payload:
            if not isinstance(item, dict):
                continue
            if str(item.get("slot_id", "")).strip() != slot_id:
                continue
            synced = copy.deepcopy(item)
            with self.state_lock:
                self.slot_states[slot_id] = copy.deepcopy(synced)
            return synced
        return self._slot_state(slot_id)

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
            flush=True,
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
                        "base_url": latest.gen_base_url,
                        "api_key_masked": _mask_secret(latest.gen_api_key),
                    }
                    item["config"] = {
                        "api_key": latest.gen_api_key,
                        "base_url": latest.gen_base_url,
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
                "[JUDGE-BATCH][RESUME-SIGNAL] "
                + json.dumps({"leader_pid": leader_pid, "resumed_slots": updated}, ensure_ascii=False),
                flush=True,
            )
            return True
        return False

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
                slot_state = self._sync_slot_state_from_disk(slot_id)
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
                self._update_slot_state(slot_id, lambda item: {**item, "status": "running", "next_retry_at": None})
                continue

            spec = None
            if assigned_case_id:
                spec = self.plan_by_case_id.get(str(assigned_case_id))
            if spec is None:
                spec = self._claim_next_case_for_slot(slot_id)
            if spec is None:
                if self._all_cases_terminal():
                    self._mark_slot_idle(slot_id)
                    return
                time.sleep(DEFAULT_STAGE_POLL_SECONDS)
                continue

            case_state = self._load_case_state(spec)
            case_state["assigned_slot_id"] = slot_id
            case_state["status"] = "running"
            case_state["current_stage"] = "judge"
            self._save_case_state(case_state)
            self._mark_slot_busy(slot_id, spec["case_id"], "judge")

            executor = self._build_executor_for_slot(self._slot_state(slot_id))
            trace_dir = self._case_trace_dir(spec["case_id"])
            result_path = self.output_root / spec["relative_result_path"]
            case_path = Path(spec["case_path"])
            rubric_path = Path(spec["rubric_path"])
            traj_path = Path(spec["traj_path"])
            try:
                payload = executor.run_case(
                    case_path=case_path,
                    rubric_path=rubric_path,
                    traj_path=traj_path,
                    result_path=result_path,
                    trace_dir=trace_dir,
                )
            except BatchRecoverableAPIError as exc:
                if self.stop_event.is_set():
                    case_state["status"] = "running"
                    case_state["current_stage"] = exc.stage_name
                    case_state["last_error"] = exc.message
                    self._save_case_state(case_state)
                    return
                if exc.kind in AUTO_RETRY_KINDS:
                    case_state["status"] = "running"
                    case_state["current_stage"] = exc.stage_name
                    case_state["last_error"] = exc.message
                    self._save_case_state(case_state)
                    self._mark_slot_retrying(slot_id, spec["case_id"], exc.stage_name, exc)
                    print(
                        "[JUDGE-BATCH][API-RETRY] "
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
                            "[JUDGE-BATCH][API-FAILOVER] "
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
                        "[JUDGE-BATCH][API-BLOCKED] "
                        f"slot={slot_state.get('name')} case={spec['relative_case_path']} "
                        f"stage={exc.stage_name} kind={exc.kind} error={exc.message}",
                        flush=True,
                    )
                continue
            except Exception as exc:
                if self.stop_event.is_set():
                    case_state["status"] = "running"
                    case_state["current_stage"] = "judge"
                    case_state["last_error"] = str(exc)
                    self._save_case_state(case_state)
                    return
                case_state["status"] = "failed"
                case_state["failure_reason"] = str(exc)
                case_state["assigned_slot_id"] = None
                case_state["current_stage"] = "judge"
                case_state["last_error"] = str(exc)
                self._save_case_state(case_state)
                self._mark_slot_idle(slot_id)
                print(
                    "[JUDGE-BATCH][CASE-FAILED] "
                    f"slot={slot_state.get('name')} case={spec['relative_case_path']} reason={exc}",
                    flush=True,
                )
                continue

            case_state["status"] = "succeeded"
            case_state["assigned_slot_id"] = None
            case_state["case_name"] = str(payload.get("case_name") or spec["case_stem"])
            case_state["result_path"] = str(result_path)
            case_state["success_at"] = _now_iso()
            case_state["current_stage"] = ""
            case_state["last_error"] = ""
            self._save_case_state(case_state)
            self._mark_slot_idle(slot_id)

    def run(self) -> None:
        if self.settings.resume and self._maybe_signal_resume_only():
            return

        if not self.settings.resume and self._run_dir_has_progress():
            raise RuntimeError(
                f"Run directory {self.run_dir} already has progress. Use --resume to continue from checkpoints."
            )

        if not self.master_lock.acquire():
            leader_pid = self._read_run_state().get("leader_pid")
            raise RuntimeError(
                f"Batch judge master is already running for {self.run_dir} (pid={leader_pid}). "
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
                    "rubric_dir": str(self.settings.rubric_dir),
                    "traj_dir": str(self.settings.traj_dir),
                    "result_output_root": str(self.output_root),
                    "judge_models": list(self.settings.judge_models),
                    "total_cases": len(self.plan),
                },
            )

            self.workers = []
            for slot in slots:
                thread = threading.Thread(
                    target=self._slot_worker,
                    name=f"judge-batch-{slot.slot_id}",
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


def build_run_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch ValueEval trajectory judging with multi-slot resume support.")
    parser.add_argument("--run_name", type=str, required=True)
    parser.add_argument("--api_slots_json", type=str, required=True)
    parser.add_argument("--cases_dir", type=str, required=True)
    parser.add_argument("--rubric_dir", type=str, required=True)
    parser.add_argument("--traj_dir", type=str, required=True)
    parser.add_argument("--result_output_dir_name", type=str, required=True)
    parser.add_argument("--judge_models", type=str, required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max_tokens", "--max-tokens", dest="max_tokens", type=int, default=8000)
    parser.add_argument("--timeout_seconds", "--timeout-seconds", dest="timeout_seconds", type=int, default=180)
    parser.add_argument(
        "--network_max_retries",
        "--network-max-retries",
        dest="network_max_retries",
        type=int,
        default=2,
    )
    parser.add_argument("--max_json_retries", "--max-json-retries", dest="max_json_retries", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    return parser
