#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified environment generation runner for EnvGen.

This script orchestrates:
1) Stage I: Env Discovery
2) Stage II: Env Synthesis
3) Stage III: Env Evolution
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = ROOT_DIR / "envgen_pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from stage1_env_discovery.step1_source_corpus_aggregation import (
    extract_agentharm,
    extract_agent_safetybench,
    extract_api_bank,
    extract_toolace,
    extract_toolalpaca,
    extract_toolbench_5000,
)
from stage1_env_discovery.step2_environment_theme_pool_construction import (
    filter_stateful_tasks,
    infer_environment_themes,
)
from stage1_env_discovery.step3_clustering_deduplication import (
    batch_add_embeddings as theme_embedding_main,
    cluster_deduplicate,
    deduplicate_environments,
    filter_environments,
)
from stage2_env_synthesis.step1_state_deduction import (
    build_state_scaffolds,
    deduce_state_schema,
)
from stage2_env_synthesis.step2_interface_design import main as design_interfaces
from stage2_env_synthesis.step3_program_synthesis import (
    analyze_programs,
    assemble_programs,
    synthesize_operation_code,
)
from stage3_refine.step1_prepare_init_configs import main as evolution_step1_main
from stage3_refine.step2_baseline_roll_check import main as evolution_step2_main
from stage3_refine.step3_build_bug_ledger import main as evolution_step3_main
from stage3_refine.step4_repair_loop import main as evolution_step4_main
from stage3_refine.step5_finalize_outputs import main as evolution_step5_main
from stage3_refine.run_stage3_refine import main as env_evolution_main
from utils.call_llm import LLMApiProfile, use_api_profile
from utils.multi_api import (
    attach_dispatch_indices,
    load_multi_api_profiles,
    make_profile_work_dir,
    merge_dispatched_items,
    split_round_robin,
)
from utils.process_file import path_exists, read_file, save_file
from utils.recovery import (
    RecoverableAPIError,
    RecoverableStepError,
    StageBlockedError,
    StageCoordinatorActiveError,
    StageResumeSignalHandled,
)
from utils.resumable import run_sequential_step
from utils.shard_runtime import (
    ensure_shard_runtime,
    read_stage_status,
    read_shard_status,
    request_resume_for_blocked_shards,
    try_stage_lock,
    try_shard_lock,
    update_stage_status,
    update_shard_status,
)


def _load_tasks_from_file(
    file_path: str,
    task_key: str,
    task_from_key: str,
    default_task_from: str,
) -> List[Dict[str, str]]:
    raw = read_file(file_path)
    if not isinstance(raw, list):
        raise ValueError(f"--task_file must contain a JSON list, got: {type(raw)}")
    records: List[Dict[str, str]] = []
    for idx, item in enumerate(raw):
        if isinstance(item, str):
            task = item.strip()
            if task:
                records.append({"task": task, "task_from": default_task_from})
            continue
        if not isinstance(item, dict):
            continue
        task = str(item.get(task_key, "")).strip()
        if not task:
            continue
        task_from = str(item.get(task_from_key, default_task_from)).strip() or default_task_from
        records.append({"task": task, "task_from": task_from})
    if not records:
        raise ValueError(f"No valid tasks loaded from --task_file: {file_path}")
    return records


def _deduplicate_task_records(records: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    seen = set()
    for item in records:
        task = str(item.get("task", "")).strip()
        if not task:
            continue
        if task in seen:
            continue
        seen.add(task)
        out.append(
            {
                "task": task,
                "task_from": str(item.get("task_from", "custom")).strip() or "custom",
            }
        )
    return out


def _maybe_limit(records: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    if limit <= 0:
        return records
    return records[:limit]


def _brief_env_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trim heavy fields from filtered metadata while preserving structure."""
    if not isinstance(data, dict):
        return data
    out: Dict[str, Any] = {}
    for env_id, item in data.items():
        if not isinstance(item, dict):
            out[env_id] = item
            continue
        new_item = dict(item)
        if "env_func_details" in new_item:
            del new_item["env_func_details"]
        if "func_test_result" in new_item and isinstance(new_item["func_test_result"], dict):
            fn_cases = new_item["func_test_result"].get("func_test_cases")
            if isinstance(fn_cases, dict) and "details" in fn_cases:
                del fn_cases["details"]
        out[env_id] = new_item
    return out


def _resolve_root_relative_path(path_str: str) -> Path:
    """Resolve a path against the repository root."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def _public_arg_dump(args: argparse.Namespace) -> Dict[str, Any]:
    """Return dry-run arguments using public EnvGen option names."""
    return vars(args).copy()


def _load_enabled_multi_api_profiles(args: argparse.Namespace) -> List[LLMApiProfile]:
    """Load multi-API profiles when the feature is enabled."""
    if getattr(args, "multi_api_count", 1) <= 1:
        return []
    if not getattr(args, "multi_api_config", ""):
        raise ValueError("--multi_api_count > 1 requires --multi_api_config")
    config_path = _resolve_root_relative_path(args.multi_api_config)
    return load_multi_api_profiles(config_path, args.multi_api_count)


def _item_resume_key(item: Dict[str, Any]) -> Any:
    return item.get("__dispatch_index__", item.get("task", item.get("environment_summary", "")))


def _read_optional_list(file_path: str) -> List[Dict[str, Any]]:
    if not path_exists(file_path):
        return []
    data = read_file(file_path)
    if isinstance(data, list):
        return data
    return []


def _print_blocked_shard(stage_label: str, status: Dict[str, Any]) -> None:
    error = status.get("error") or {}
    print(
        f"[{stage_label}] shard blocked: "
        f"shard={status.get('shard_id')} "
        f"profile={status.get('profile_name')} "
        f"step={status.get('current_step')} "
        f"kind={error.get('kind', 'unknown')} "
        f"message={error.get('message', '')}"
    )


_AUTO_RESUME_KINDS = {"network", "timeout"}


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_iso_datetime(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _auto_resume_delay_seconds(attempt: int) -> int:
    normalized = max(1, int(attempt))
    return min(300, 10 * (2 ** (normalized - 1)))


def _leader_pid_for_stage(stage_dir: Path) -> int | None:
    status = read_stage_status(stage_dir)
    leader_pid = status.get("leader_pid")
    if isinstance(leader_pid, int) and leader_pid > 0:
        return leader_pid
    return None


def _mark_shard_blocked(
    *,
    work_dir: Path,
    stage_label: str,
    shard_id: int,
    profile_name: str,
    exc: RecoverableStepError,
) -> None:
    previous = read_shard_status(work_dir)
    auto_retry_attempts = int(previous.get("auto_retry_attempts", 0) or 0)
    next_resume_at = None
    resume_mode = "manual"
    if exc.error.kind in _AUTO_RESUME_KINDS:
        auto_retry_attempts += 1
        next_resume_at = (
            _now_utc() + dt.timedelta(seconds=_auto_resume_delay_seconds(auto_retry_attempts))
        ).isoformat()
        resume_mode = "auto"
    update_shard_status(
        work_dir=work_dir,
        state="blocked",
        current_step=exc.step_label,
        profile_name=profile_name,
        shard_id=shard_id,
        error=exc.error.to_dict(),
        extra={
            "blocked_at": _now_utc().isoformat(),
            "resume_requested": False,
            "resume_requested_at": None,
            "resume_mode": resume_mode,
            "auto_retry_attempts": auto_retry_attempts,
            "next_resume_at": next_resume_at,
        },
    )
    _print_blocked_shard(stage_label, read_shard_status(work_dir))


def _should_resume_blocked_shard(status: Dict[str, Any]) -> tuple[bool, str | None]:
    if status.get("state") != "blocked":
        return False, None
    if status.get("resume_requested"):
        return True, "manual"
    error = status.get("error") or {}
    if error.get("kind") in _AUTO_RESUME_KINDS:
        next_resume_at = _parse_iso_datetime(status.get("next_resume_at"))
        if next_resume_at is None or next_resume_at <= _now_utc():
            return True, "auto"
    return False, None


def _format_waiting_blocked_shards(stage_label: str, statuses: List[Dict[str, Any]]) -> str:
    details = []
    for status in statuses:
        error = status.get("error") or {}
        details.append(
            f"shard={status.get('shard_id')} profile={status.get('profile_name')} "
            f"step={status.get('current_step')} kind={error.get('kind', 'unknown')}"
        )
    return f"[{stage_label}] waiting for blocked shards: " + "; ".join(details)


def _run_profile_shards(
    stage_label: str,
    stage_name: str,
    profiles: List[LLMApiProfile],
    shard_items: List[List[Dict[str, Any]]],
    stage_base_dir: Path,
    worker_fn,
    poll_interval: int = 2,
    resume_requested: bool = False,
) -> List[Path]:
    """Run shard workers with one stage coordinator and resumable shard restarts."""
    active_shards = [
        (shard_id, profile, items)
        for shard_id, (profile, items) in enumerate(zip(profiles, shard_items))
        if items
    ]
    if not active_shards:
        return []

    stage_dir = Path(stage_base_dir) / "multi_api" / stage_name
    print(f"[{stage_label}] Multi-API enabled with {len(active_shards)} active profiles.")
    shard_meta = []
    for shard_id, profile, items in active_shards:
        work_dir = make_profile_work_dir(stage_base_dir, stage_name, shard_id, profile.name)
        ensure_shard_runtime(
            work_dir=work_dir,
            stage_label=stage_label,
            shard_id=shard_id,
            profile_name=profile.name,
            items=items,
        )
        shard_meta.append(
            {
                "shard_id": shard_id,
                "profile": profile,
                "items": items,
                "work_dir": work_dir,
            }
        )

    def _worker(meta: Dict[str, Any]) -> None:
        shard_id = int(meta["shard_id"])
        profile = meta["profile"]
        items = meta["items"]
        work_dir = meta["work_dir"]
        with try_shard_lock(work_dir) as locked:
            if not locked:
                return
            update_shard_status(
                work_dir=work_dir,
                state="running",
                current_step="starting",
                profile_name=profile.name,
                shard_id=shard_id,
                extra={
                    "resume_requested": False,
                    "resume_requested_at": None,
                    "resume_mode": None,
                    "next_resume_at": None,
                    "last_started_at": _now_utc().isoformat(),
                },
            )
            try:
                with use_api_profile(profile):
                    worker_fn(shard_id, profile, items, work_dir)
            except RecoverableStepError as exc:
                _mark_shard_blocked(
                    work_dir=work_dir,
                    stage_label=stage_label,
                    shard_id=shard_id,
                    profile_name=profile.name,
                    exc=exc,
                )
                return
            update_shard_status(
                work_dir=work_dir,
                state="completed",
                current_step="completed",
                profile_name=profile.name,
                shard_id=shard_id,
                extra={
                    "resume_requested": False,
                    "resume_requested_at": None,
                    "resume_mode": None,
                    "next_resume_at": None,
                    "completed_at": _now_utc().isoformat(),
                },
            )

    with try_stage_lock(stage_dir) as is_leader:
        if not is_leader:
            leader_pid = _leader_pid_for_stage(stage_dir)
            if resume_requested:
                signaled = request_resume_for_blocked_shards(stage_dir)
                raise StageResumeSignalHandled(
                    stage_label,
                    signaled_shards=signaled,
                    leader_pid=leader_pid,
                )
            raise StageCoordinatorActiveError(stage_label, leader_pid=leader_pid)

        update_stage_status(
            stage_dir=stage_dir,
            stage_label=stage_label,
            state="running",
            leader_pid=os.getpid(),
            extra={
                "active_profiles": [profile.name for _, profile, _ in active_shards],
                "shard_count": len(active_shards),
            },
        )

        if resume_requested:
            request_resume_for_blocked_shards(stage_dir)

        with ThreadPoolExecutor(max_workers=len(active_shards)) as executor:
            future_to_meta: Dict[Any, Dict[str, Any]] = {}
            last_wait_message = ""
            last_wait_time = 0.0

            while True:
                for future in list(future_to_meta.keys()):
                    if not future.done():
                        continue
                    meta = future_to_meta.pop(future)
                    exc = future.exception()
                    if exc is not None:
                        update_stage_status(
                            stage_dir=stage_dir,
                            stage_label=stage_label,
                            state="failed",
                            leader_pid=os.getpid(),
                            extra={"last_exception": str(exc)},
                        )
                        raise RuntimeError(
                            f"[{stage_label}] shard #{meta['shard_id']} "
                            f"profile={meta['profile'].name} failed: {exc}"
                        ) from exc

                statuses = []
                for meta in shard_meta:
                    status = read_shard_status(meta["work_dir"])
                    status.setdefault("shard_id", meta["shard_id"])
                    status.setdefault("profile_name", meta["profile"].name)
                    statuses.append(status)

                if statuses and all(status.get("state") == "completed" for status in statuses):
                    update_stage_status(
                        stage_dir=stage_dir,
                        stage_label=stage_label,
                        state="completed",
                        leader_pid=os.getpid(),
                    )
                    return [meta["work_dir"] for meta in shard_meta]

                active_shard_ids = {
                    int(meta["shard_id"])
                    for meta in future_to_meta.values()
                }
                scheduled_count = 0
                for meta, status in zip(shard_meta, statuses):
                    shard_id = int(meta["shard_id"])
                    if shard_id in active_shard_ids:
                        continue
                    state = str(status.get("state", "pending"))
                    if state == "completed":
                        continue
                    resume_allowed, resume_reason = _should_resume_blocked_shard(status)
                    should_launch = state in {"pending", "running", "starting"} or resume_allowed
                    if not should_launch:
                        continue
                    if resume_reason == "manual":
                        print(
                            f"[{stage_label}] manual resume accepted: "
                            f"shard={shard_id} profile={status.get('profile_name')} "
                            f"step={status.get('current_step')}"
                        )
                    elif resume_reason == "auto":
                        print(
                            f"[{stage_label}] auto retrying shard: "
                            f"shard={shard_id} profile={status.get('profile_name')} "
                            f"step={status.get('current_step')}"
                        )
                    future = executor.submit(_worker, meta)
                    future_to_meta[future] = meta
                    scheduled_count += 1

                blocked = [status for status in statuses if status.get("state") == "blocked"]
                any_running = bool(future_to_meta) or any(
                    status.get("state") == "running" for status in statuses
                )
                if blocked and not any_running and scheduled_count == 0:
                    wait_message = _format_waiting_blocked_shards(stage_label, blocked)
                    now_monotonic = time.monotonic()
                    if (
                        wait_message != last_wait_message
                        or now_monotonic - last_wait_time >= max(5, int(poll_interval))
                    ):
                        print(wait_message)
                        print(
                            "[Paused] Fix the blocked API/profile and rerun the same "
                            "command with --resume to signal the active coordinator."
                        )
                        last_wait_message = wait_message
                        last_wait_time = now_monotonic
                    update_stage_status(
                        stage_dir=stage_dir,
                        stage_label=stage_label,
                        state="waiting_for_resume",
                        leader_pid=os.getpid(),
                        extra={"blocked_shard_count": len(blocked)},
                    )
                    time.sleep(max(1, int(poll_interval)))
                    continue

                update_stage_status(
                    stage_dir=stage_dir,
                    stage_label=stage_label,
                    state="running",
                    leader_pid=os.getpid(),
                    extra={
                        "blocked_shard_count": len(blocked),
                        "running_shard_count": len(future_to_meta),
                    },
                )
                time.sleep(max(1, int(poll_interval)))


def _run_state_deduction_local(
    raw_data: List[Dict[str, Any]],
    save_file_path: str,
    model: str,
    save_every: int,
    progress_desc: str | None = None,
    progress_position: int | None = None,
) -> List[Dict[str, Any]]:
    """Run Env Synthesis state deduction with periodic saves."""
    return run_sequential_step(
        items=raw_data,
        output_path=save_file_path,
        key_fn=_item_resume_key,
        is_complete_fn=lambda item: (
            isinstance(item, dict)
            and isinstance(item.get("state_space_definition"), list)
            and len(item.get("state_space_definition", [])) > 0
            and isinstance(item.get("constraints_rules"), list)
            and len(item.get("constraints_rules", [])) > 0
        ),
        process_fn=lambda item: deduce_state_schema(item, model),
        save_every=save_every,
        step_label="EnvSynthesis-StateDeduction",
        progress_desc=progress_desc,
        progress_position=progress_position,
    )


def _run_synthesis_llm_steps_for_items(
    items: List[Dict[str, Any]],
    args: argparse.Namespace,
    work_dir: Path,
    progress_position: int | None = None,
) -> None:
    """Run LLM-heavy Env Synthesis steps for a shard of items."""
    work_dir.mkdir(parents=True, exist_ok=True)
    step1_output = str(work_dir / "step1_state_deduction.schema.json")
    step2_output = str(work_dir / "step1_state_deduction.scaffold.json")
    step3_output = str(work_dir / "step2_interface_design.json")
    step4_output = str(work_dir / "step3_program_synthesis.functions.json")

    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvSynthesis-StateDeduction",
    )
    _run_state_deduction_local(
        raw_data=items,
        save_file_path=step1_output,
        model=args.state_deduction_model,
        save_every=args.state_deduction_save_every,
        progress_desc="EnvSynthesis-StateDeduction",
        progress_position=progress_position,
    )
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvSynthesis-StateScaffold",
    )
    build_state_scaffolds(
        step1_output,
        step2_output,
        args.state_scaffold_model,
        progress_desc="EnvSynthesis-StateScaffold",
        progress_position=progress_position,
    )
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvSynthesis-InterfaceDesign",
    )
    design_interfaces(
        step2_output,
        step3_output,
        args.interface_design_model,
        progress_desc="EnvSynthesis-InterfaceDesign",
        progress_position=progress_position,
    )
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvSynthesis-ProgramSynthesis",
    )
    synthesize_operation_code(
        step3_output,
        step4_output,
        args.program_synthesis_model,
        args.program_synthesis_max_workers,
        progress_desc="EnvSynthesis-ProgramSynthesis",
        progress_position=progress_position,
    )


def _run_evolution_steps_for_items(
    items: List[Dict[str, Any]],
    args: argparse.Namespace,
    work_dir: Path,
    progress_position: int | None = None,
) -> None:
    """Run Env Evolution steps for a shard of items."""
    work_dir.mkdir(parents=True, exist_ok=True)
    input_path = str(work_dir / "input_env_with_code.json")
    step1_output = str(work_dir / "step1_prepared_init_configs.json")
    step2_output = str(work_dir / "step2_baseline_roll_check.json")
    step3_output = str(work_dir / "step3_bug_ledger.json")
    step4_output = str(work_dir / "step4_repaired_envs.json")

    save_file(input_path, items)
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvEvolution-InitConfig",
    )
    evolution_step1_main(
        argparse.Namespace(
            read_file_path=input_path,
            save_file_path=step1_output,
            gen_config_num=args.evolution_init_config_count,
            model=args.evolution_init_model,
            temperature=args.evolution_init_temperature,
            skip_llm_init=args.evolution_skip_llm_init,
            reuse_existing_init_config=args.evolution_reuse_existing_init_config,
            save_every=1,
            progress_desc="EnvEvolution-InitConfig",
            progress_position=progress_position,
        )
    )
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvEvolution-BaselineRollout",
    )
    evolution_step2_main(
        argparse.Namespace(
            read_file_path=step1_output,
            save_file_path=step2_output,
            model=args.evolution_eval_model,
            temperature=args.evolution_eval_temperature,
            max_steps=args.evolution_eval_steps,
            agent_mode=args.evolution_agent_mode,
            save_every=1,
            progress_desc="EnvEvolution-BaselineRollout",
            progress_position=progress_position,
        )
    )
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvEvolution-BugLedger",
    )
    evolution_step3_main(
        argparse.Namespace(
            read_file_path=step2_output,
            save_file_path=step3_output,
            top_n=args.evolution_top_n,
            max_cases_per_func=args.evolution_max_cases_per_function,
            save_every=1,
            progress_desc="EnvEvolution-BugLedger",
            progress_position=progress_position,
        )
    )
    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvEvolution-RepairLoop",
    )
    evolution_step4_main(
        argparse.Namespace(
            read_file_path=step3_output,
            save_file_path=step4_output,
            threshold=args.evolution_threshold,
            positive_pass_threshold=args.evolution_positive_pass_threshold,
            top_n=args.evolution_top_n,
            max_repair_rounds=args.evolution_max_repair_rounds,
            eval_steps=args.evolution_eval_steps,
            eval_model=args.evolution_eval_model,
            eval_temperature=args.evolution_eval_temperature,
            agent_mode=args.evolution_agent_mode,
            enable_llm_patch=args.evolution_enable_llm_patch,
            llm_patch_model=args.evolution_llm_patch_model,
            llm_patch_temperature=args.evolution_llm_patch_temperature,
            save_every=1,
            progress_desc="EnvEvolution-RepairLoop",
            progress_position=progress_position,
        )
    )


def _merge_shard_output_files(
    *,
    work_dirs: List[Path],
    filename: str,
    expected_count: int,
) -> List[Dict[str, Any]]:
    return merge_dispatched_items(
        [_read_optional_list(str(work_dir / filename)) for work_dir in work_dirs],
        expected_count=expected_count,
    )


def _prepare_theme_embedding_samples(env_topic_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    for item in env_topic_items:
        if not isinstance(item, dict):
            continue
        new_item = dict(item)
        summary = str(new_item.get("environment_summary", "")).strip()
        intro = str(new_item.get("environment_introduction", "")).strip()
        new_item["env_summary_and_introduction"] = f"**{summary}**: {intro}"
        samples.append(new_item)
    return samples


def _merge_existing_theme_embeddings(
    samples: List[Dict[str, Any]],
    emb_output: str,
) -> List[Dict[str, Any]]:
    existing_items = _read_optional_list(emb_output)
    if not existing_items:
        return samples

    existing_by_task: Dict[str, Dict[str, Any]] = {}
    for item in existing_items:
        if not isinstance(item, dict):
            continue
        task = str(item.get("task", "")).strip()
        embedding = item.get("env_summary_and_introduction_embedding")
        if not task:
            continue
        if isinstance(embedding, list) and embedding:
            existing_by_task[task] = item

    if not existing_by_task:
        return samples

    merged: List[Dict[str, Any]] = []
    for item in samples:
        task = str(item.get("task", "")).strip()
        existing = existing_by_task.get(task)
        if existing is None:
            merged.append(item)
            continue
        new_item = dict(item)
        new_item["env_summary_and_introduction_embedding"] = existing.get(
            "env_summary_and_introduction_embedding"
        )
        merged.append(new_item)
    return merged


def _split_theme_embedding_batches(
    items: List[Dict[str, Any]],
    *,
    batch_size: int,
    shard_count: int,
) -> List[List[Dict[str, Any]]]:
    """Split items by stable original embedding batches, then round-robin batches to shards."""
    if shard_count <= 0:
        raise ValueError("shard_count must be positive for Env Discovery multi-API embedding.")
    normalized_batch_size = max(1, int(batch_size))
    shards: List[List[Dict[str, Any]]] = [[] for _ in range(shard_count)]
    for batch_idx, start in enumerate(range(0, len(items), normalized_batch_size)):
        shard_id = batch_idx % shard_count
        shards[shard_id].extend(items[start:start + normalized_batch_size])
    return shards


def _run_theme_embedding_for_items(
    *,
    items: List[Dict[str, Any]],
    args: argparse.Namespace,
    work_dir: Path,
    progress_position: int | None = None,
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    shard_output = str(work_dir / "step3_embedding.json")
    if not path_exists(shard_output):
        save_file(shard_output, items)

    update_shard_status(
        work_dir=work_dir,
        state="running",
        current_step="EnvDiscovery-ThemeEmbedding",
    )
    try:
        theme_embedding_main(
            data=items,
            field="env_summary_and_introduction",
            model=args.embedding_model,
            batch_size=args.embedding_batch_size,
            timeout=args.embedding_timeout,
            save_file_path=shard_output,
            progress_desc="EnvDiscovery-ThemeEmbedding",
            progress_position=progress_position,
        )
    except RecoverableAPIError as exc:
        raise RecoverableStepError(step_label="EnvDiscovery-ThemeEmbedding", error=exc) from exc


def _run_theme_embedding_multi_api(
    *,
    emb_samples: List[Dict[str, Any]],
    emb_output: str,
    args: argparse.Namespace,
    profiles: List[LLMApiProfile],
) -> List[Dict[str, Any]]:
    emb_samples = _merge_existing_theme_embeddings(emb_samples, emb_output)
    indexed_items = attach_dispatch_indices(emb_samples)
    shard_items = _split_theme_embedding_batches(
        indexed_items,
        batch_size=args.embedding_batch_size,
        shard_count=len(profiles),
    )
    stage_base_dir = Path(emb_output).parent

    def _theme_embedding_worker(
        shard_id: int,
        profile: LLMApiProfile,
        items: List[Dict[str, Any]],
        work_dir: Path,
    ) -> None:
        _run_theme_embedding_for_items(
            items=items,
            args=args,
            work_dir=work_dir,
            progress_position=shard_id,
        )

    work_dirs = _run_profile_shards(
        "EnvDiscovery-ThemeEmbedding",
        "env_discovery_embedding",
        profiles,
        shard_items,
        stage_base_dir,
        _theme_embedding_worker,
        poll_interval=args.resume_poll_interval,
        resume_requested=args.resume,
    )
    merged = _merge_shard_output_files(
        work_dirs=work_dirs,
        filename="step3_embedding.json",
        expected_count=len(indexed_items),
    )
    save_file(emb_output, merged)
    return merged


def run_env_discovery(args: argparse.Namespace) -> str:
    print("\n[Env Discovery] Start")
    step0_output = args.discovery_source_tasks_output
    step1_output = args.discovery_task_filter_output
    step2_output = args.discovery_theme_pool_output

    records: List[Dict[str, str]] | None = None
    if args.resume and path_exists(step0_output):
        existing_records = read_file(step0_output)
        if isinstance(existing_records, list) and existing_records:
            records = existing_records
            print(f"[EnvDiscovery-SourceCorpusAggregation] resume from existing -> {step0_output}")
    if records is None:
        if args.task_source == "dataset":
            records = []
            if args.include_api_bank:
                records.extend(extract_api_bank(deduplicate=args.deduplicate_within_corpus))
            if args.include_toolace:
                records.extend(extract_toolace(deduplicate=args.deduplicate_within_corpus))
            if args.include_toolbench_5000:
                records.extend(extract_toolbench_5000(deduplicate=args.deduplicate_within_corpus))
            if args.include_toolalpaca:
                records.extend(extract_toolalpaca(deduplicate=args.deduplicate_within_corpus))
            if args.include_agentharm:
                records.extend(extract_agentharm(deduplicate=args.deduplicate_within_corpus))
            if args.include_agent_safetybench:
                records.extend(extract_agent_safetybench(deduplicate=args.deduplicate_within_corpus))
            if not records:
                raise ValueError(
                    "No tasks loaded from dataset mode. Enable at least one corpus include flag."
                )
        elif args.task_source == "file":
            if not args.task_file:
                raise ValueError("--task_source=file requires --task_file")
            records = _load_tasks_from_file(
                file_path=args.task_file,
                task_key=args.task_file_task_key,
                task_from_key=args.task_file_task_from_key,
                default_task_from=args.task_file_default_from,
            )
        else:
            if not args.inline_task:
                raise ValueError("--task_source=inline requires --inline_task")
            records = [{"task": args.inline_task.strip(), "task_from": args.inline_task_from}]

        if args.deduplicate_across_corpora:
            records = _deduplicate_task_records(records)
        records = _maybe_limit(records, args.max_tasks)
        save_file(step0_output, records)
        print(f"[EnvDiscovery-SourceCorpusAggregation] saved {len(records)} tasks -> {step0_output}")

    try:
        filter_stateful_tasks(
            tasks=[item["task"] for item in records],
            save_file_path=step1_output,
            model=args.judge_model,
            max_workers=args.judge_max_workers,
            progress_desc="EnvDiscovery-TaskFilter",
        )
        print(f"[EnvDiscovery-TaskFilter] done -> {step1_output}")

        infer_environment_themes(
            read_file_path=step1_output,
            save_file_path=step2_output,
            model=args.topic_model,
            num_workers=args.topic_num_workers,
            progress_desc="EnvDiscovery-ThemeInference",
        )
        print(f"[EnvDiscovery-ThemeInference] done -> {step2_output}")
    except RecoverableStepError as exc:
        print(f"[Env Discovery] paused at {exc.step_label}: {exc}")
        raise

    final_env_desc = args.discovery_final_output
    env_topic_items = read_file(step2_output)
    if not isinstance(env_topic_items, list):
        raise ValueError(f"Invalid stage1 step2 output: {step2_output}")

    if args.enable_theme_embedding:
        emb_output = args.discovery_theme_embedding_output
        emb_samples = _prepare_theme_embedding_samples(env_topic_items)
        multi_api_profiles = _load_enabled_multi_api_profiles(args)
        try:
            if len(multi_api_profiles) > 1 and len(emb_samples) > 1:
                emb_samples = _run_theme_embedding_multi_api(
                    emb_samples=emb_samples,
                    emb_output=emb_output,
                    args=args,
                    profiles=multi_api_profiles,
                )
            else:
                emb_samples = theme_embedding_main(
                    data=_merge_existing_theme_embeddings(emb_samples, emb_output),
                    field="env_summary_and_introduction",
                    model=args.embedding_model,
                    batch_size=args.embedding_batch_size,
                    timeout=args.embedding_timeout,
                    save_file_path=emb_output,
                    progress_desc="EnvDiscovery-ThemeEmbedding",
                )
        except RecoverableAPIError as exc:
            print(f"[Env Discovery] paused at theme embedding: {exc}")
            raise
        save_file(emb_output, emb_samples)
        print(f"[EnvDiscovery-ThemeEmbedding] done -> {emb_output}")
        env_topic_items = emb_samples

    if args.enable_theme_clustering:
        if not args.enable_theme_embedding:
            raise ValueError("--enable_theme_clustering requires --enable_theme_embedding")
        if not isinstance(env_topic_items, list):
            raise ValueError("Embedding output is not a list.")
        selected = deduplicate_environments(env_topic_items)
        selected = filter_environments(
            selected,
            modelability_threshold=args.theme_modelability_threshold,
            usefulness_threshold=args.theme_usefulness_threshold,
        )
        if selected and args.theme_cluster_count > 0:
            n_clusters = min(args.theme_cluster_count, len(selected))
            selected = cluster_deduplicate(
                selected,
                embedding_field="env_summary_and_introduction_embedding",
                n_clusters=n_clusters,
            )
        save_file(args.discovery_selected_theme_output, selected)
        print(f"[EnvDiscovery-ClusteringDeduplication] done -> {args.discovery_selected_theme_output}")
        source_for_final = selected
    else:
        source_for_final = env_topic_items

    final_data = []
    for item in source_for_final:
        if not isinstance(item, dict):
            continue
        final_data.append(
            {
                "task": item.get("task", ""),
                "environment_summary": item.get("environment_summary", ""),
                "environment_introduction": item.get("environment_introduction", ""),
            }
        )
    save_file(final_env_desc, final_data)
    print(f"[EnvDiscovery-Final] saved {len(final_data)} environment themes -> {final_env_desc}")
    return final_env_desc


def run_env_synthesis(args: argparse.Namespace, discovery_output: str | None = None) -> str:
    print("\n[Env Synthesis] Start")
    input_path = args.synthesis_input_themes
    if discovery_output:
        input_path = discovery_output

    raw_data = read_file(input_path)
    if not isinstance(raw_data, list):
        raise ValueError(f"env synthesis input must be a list: {input_path}")

    multi_api_profiles = _load_enabled_multi_api_profiles(args)
    if len(multi_api_profiles) <= 1 or len(raw_data) <= 1:
        try:
            _run_state_deduction_local(
                raw_data=raw_data,
                save_file_path=args.state_schema_output,
                model=args.state_deduction_model,
                save_every=args.state_deduction_save_every,
                progress_desc="EnvSynthesis-StateDeduction",
            )
            print(f"[EnvSynthesis-StateDeduction] done -> {args.state_schema_output}")

            build_state_scaffolds(
                args.state_schema_output,
                args.state_scaffold_output,
                args.state_scaffold_model,
                progress_desc="EnvSynthesis-StateScaffold",
            )
            print(f"[EnvSynthesis-StateScaffold] done -> {args.state_scaffold_output}")

            design_interfaces(
                args.state_scaffold_output,
                args.interface_design_output,
                args.interface_design_model,
                progress_desc="EnvSynthesis-InterfaceDesign",
            )
            print(f"[EnvSynthesis-InterfaceDesign] done -> {args.interface_design_output}")

            synthesize_operation_code(
                args.interface_design_output,
                args.operation_code_output,
                args.program_synthesis_model,
                args.program_synthesis_max_workers,
                progress_desc="EnvSynthesis-ProgramSynthesis",
            )
            print(f"[EnvSynthesis-ProgramSynthesis] done -> {args.operation_code_output}")
        except RecoverableStepError as exc:
            print(f"[Env Synthesis] paused at {exc.step_label}: {exc}")
            raise
    else:
        indexed_items = attach_dispatch_indices(raw_data)
        shard_items = split_round_robin(indexed_items, len(multi_api_profiles))
        stage_base_dir = Path(args.state_schema_output).parent

        def _synthesis_worker(
            shard_id: int,
            profile: LLMApiProfile,
            items: List[Dict[str, Any]],
            work_dir: Path,
        ):
            _run_synthesis_llm_steps_for_items(
                items=items,
                args=args,
                work_dir=work_dir,
                progress_position=shard_id,
            )

        work_dirs = _run_profile_shards(
            "Env Synthesis",
            "env_synthesis",
            multi_api_profiles,
            shard_items,
            stage_base_dir,
            _synthesis_worker,
            poll_interval=args.resume_poll_interval,
            resume_requested=args.resume,
        )
        expected_count = len(raw_data)

        merged_step1 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step1_state_deduction.schema.json",
            expected_count=expected_count,
        )
        save_file(args.state_schema_output, merged_step1)
        print(f"[EnvSynthesis-StateDeduction] done -> {args.state_schema_output}")

        merged_step2 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step1_state_deduction.scaffold.json",
            expected_count=expected_count,
        )
        save_file(args.state_scaffold_output, merged_step2)
        print(f"[EnvSynthesis-StateScaffold] done -> {args.state_scaffold_output}")

        merged_step3 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step2_interface_design.json",
            expected_count=expected_count,
        )
        save_file(args.interface_design_output, merged_step3)
        print(f"[EnvSynthesis-InterfaceDesign] done -> {args.interface_design_output}")

        merged_step4 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step3_program_synthesis.functions.json",
            expected_count=expected_count,
        )
        save_file(args.operation_code_output, merged_step4)
        print(f"[EnvSynthesis-ProgramSynthesis] done -> {args.operation_code_output}")

    assemble_programs(args.operation_code_output, args.assembled_program_output)
    print(f"[EnvSynthesis-ProgramAssembly] done -> {args.assembled_program_output}")

    analyze_programs(args.assembled_program_output, args.verified_program_output)
    print(f"[EnvSynthesis-ProgramVerification] done -> {args.verified_program_output}")

    analyzed = read_file(args.verified_program_output)
    save_file(args.synthesis_final_output, analyzed)
    print(f"[EnvSynthesis-Final] synthesized environments saved -> {args.synthesis_final_output}")
    return args.synthesis_final_output


def run_env_evolution(args: argparse.Namespace, synthesis_output: str | None = None) -> str:
    print("\n[Env Evolution] Start")
    read_file_path = synthesis_output or args.evolution_input_envs
    raw_data = read_file(read_file_path)
    if not isinstance(raw_data, list):
        raise ValueError(f"env evolution input must be a list: {read_file_path}")

    multi_api_profiles = _load_enabled_multi_api_profiles(args)
    if len(multi_api_profiles) <= 1 or len(raw_data) <= 1:
        ns = argparse.Namespace(
            read_file_path=read_file_path,
            temp_dir=args.evolution_temp_dir,
            final_dir=args.evolution_final_dir,
            threshold=args.evolution_threshold,
            positive_pass_threshold=args.evolution_positive_pass_threshold,
            gen_config_num=args.evolution_init_config_count,
            eval_steps=args.evolution_eval_steps,
            max_repair_rounds=args.evolution_max_repair_rounds,
            top_n=args.evolution_top_n,
            max_cases_per_func=args.evolution_max_cases_per_function,
            init_model=args.evolution_init_model,
            init_temperature=args.evolution_init_temperature,
            eval_model=args.evolution_eval_model,
            eval_temperature=args.evolution_eval_temperature,
            agent_mode=args.evolution_agent_mode,
            enable_llm_patch=args.evolution_enable_llm_patch,
            llm_patch_model=args.evolution_llm_patch_model,
            llm_patch_temperature=args.evolution_llm_patch_temperature,
            skip_llm_init=args.evolution_skip_llm_init,
            reuse_existing_init_config=args.evolution_reuse_existing_init_config,
        )
        try:
            env_evolution_main(ns)
        except RecoverableStepError as exc:
            print(f"[Env Evolution] paused at {exc.step_label}: {exc}")
            raise
    else:
        temp_dir = Path(args.evolution_temp_dir)
        final_dir = Path(args.evolution_final_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)

        indexed_items = attach_dispatch_indices(raw_data)
        shard_items = split_round_robin(indexed_items, len(multi_api_profiles))

        def _evolution_worker(
            shard_id: int,
            profile: LLMApiProfile,
            items: List[Dict[str, Any]],
            work_dir: Path,
        ):
            _run_evolution_steps_for_items(
                items=items,
                args=args,
                work_dir=work_dir,
                progress_position=shard_id,
            )

        work_dirs = _run_profile_shards(
            "Env Evolution",
            "env_evolution",
            multi_api_profiles,
            shard_items,
            temp_dir,
            _evolution_worker,
            poll_interval=args.resume_poll_interval,
            resume_requested=args.resume,
        )
        expected_count = len(raw_data)

        step1_path = str(temp_dir / "step1_prepared_init_configs.json")
        merged_step1 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step1_prepared_init_configs.json",
            expected_count=expected_count,
        )
        save_file(step1_path, merged_step1)
        print(f"[EnvEvolution-InitConfig] done -> {step1_path}")

        step2_path = str(temp_dir / "step2_baseline_roll_check.json")
        merged_step2 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step2_baseline_roll_check.json",
            expected_count=expected_count,
        )
        save_file(step2_path, merged_step2)
        print(f"[EnvEvolution-BaselineRollout] done -> {step2_path}")

        step3_path = str(temp_dir / "step3_bug_ledger.json")
        merged_step3 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step3_bug_ledger.json",
            expected_count=expected_count,
        )
        save_file(step3_path, merged_step3)
        print(f"[EnvEvolution-BugLedger] done -> {step3_path}")

        step4_path = str(temp_dir / "step4_repaired_envs.json")
        merged_step4 = _merge_shard_output_files(
            work_dirs=work_dirs,
            filename="step4_repaired_envs.json",
            expected_count=expected_count,
        )
        save_file(step4_path, merged_step4)
        print(f"[EnvEvolution-RepairLoop] done -> {step4_path}")

        evolution_step5_main(
            argparse.Namespace(
                read_file_path=step4_path,
                threshold=args.evolution_threshold,
                positive_pass_threshold=args.evolution_positive_pass_threshold,
                filtered_output_path=str(final_dir / "filtered_env_metadata.json"),
                repair_queue_output_path=str(final_dir / "repair_queue_env_metadata.json"),
                repair_report_output_path=str(final_dir / "repair_report.json"),
                full_output_path=str(final_dir / "refined_env_items_full.json"),
            )
        )

    final_output = str(Path(args.evolution_final_dir) / "filtered_env_metadata.json")
    print(f"[Env Evolution] done -> {final_output}")
    return final_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EnvGen runner: Env Discovery, Env Synthesis, and Env Evolution."
    )

    parser.add_argument("--random_seed", type=int, default=42)
    parser.add_argument("--max_tasks", type=int, default=0, help="<=0 means no limit.")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume from existing step/shard checkpoints.")
    parser.add_argument("--resume_poll_interval", type=int, default=2, help="Polling interval in seconds while waiting for running/resumed shards.")

    parser.add_argument("--run_env_discovery", dest="run_env_discovery", action="store_true")
    parser.add_argument("--run_env_synthesis", dest="run_env_synthesis", action="store_true")
    parser.add_argument("--run_env_evolution", dest="run_env_evolution", action="store_true")

    parser.add_argument("--task_source", type=str, choices=["dataset", "file", "inline"], default="dataset")
    parser.add_argument("--task_file", type=str, default="")
    parser.add_argument("--task_file_task_key", type=str, default="task")
    parser.add_argument("--task_file_task_from_key", type=str, default="task_from")
    parser.add_argument("--task_file_default_from", type=str, default="custom_file")
    parser.add_argument("--inline_task", type=str, default="")
    parser.add_argument("--inline_task_from", type=str, default="inline")
    parser.add_argument("--include_api_bank", dest="include_api_bank", action="store_true")
    parser.add_argument("--exclude_api_bank", dest="include_api_bank", action="store_false")
    parser.add_argument("--include_toolace", dest="include_toolace", action="store_true")
    parser.add_argument("--exclude_toolace", dest="include_toolace", action="store_false")
    parser.add_argument("--include_toolbench_5000", dest="include_toolbench_5000", action="store_true")
    parser.add_argument("--exclude_toolbench_5000", dest="include_toolbench_5000", action="store_false")
    parser.add_argument("--include_toolalpaca", dest="include_toolalpaca", action="store_true")
    parser.add_argument("--exclude_toolalpaca", dest="include_toolalpaca", action="store_false")
    parser.add_argument("--include_agentharm", dest="include_agentharm", action="store_true")
    parser.add_argument("--exclude_agentharm", dest="include_agentharm", action="store_false")
    parser.add_argument("--include_agent_safetybench", dest="include_agent_safetybench", action="store_true")
    parser.add_argument("--exclude_agent_safetybench", dest="include_agent_safetybench", action="store_false")
    parser.add_argument(
        "--deduplicate_within_corpus",
        dest="deduplicate_within_corpus",
        action="store_true",
        help="Deduplicate tasks inside each corpus before merge.",
    )
    parser.add_argument(
        "--no_deduplicate_within_corpus",
        dest="deduplicate_within_corpus",
        action="store_false",
    )
    parser.add_argument(
        "--deduplicate_across_corpora",
        dest="deduplicate_across_corpora",
        action="store_true",
        help="Deduplicate tasks globally across all merged corpora.",
    )
    parser.add_argument(
        "--no_deduplicate_across_corpora",
        dest="deduplicate_across_corpora",
        action="store_false",
    )
    parser.set_defaults(
        run_env_discovery=False,
        run_env_synthesis=False,
        run_env_evolution=False,
        include_api_bank=True,
        include_toolace=True,
        include_toolbench_5000=True,
        include_toolalpaca=True,
        include_agentharm=True,
        include_agent_safetybench=True,
        deduplicate_within_corpus=True,
        deduplicate_across_corpora=True,
    )

    parser.add_argument(
        "--discovery_source_tasks_output",
        dest="discovery_source_tasks_output",
        type=str,
        default="stage1_env_discovery/temp_result/step1_source_corpus_aggregation.json",
    )
    parser.add_argument(
        "--discovery_task_filter_output",
        dest="discovery_task_filter_output",
        type=str,
        default="stage1_env_discovery/temp_result/step2_environment_theme_pool_construction.judge.json",
    )
    parser.add_argument(
        "--discovery_theme_pool_output",
        dest="discovery_theme_pool_output",
        type=str,
        default="stage1_env_discovery/temp_result/step2_environment_theme_pool_construction.json",
    )
    parser.add_argument(
        "--discovery_theme_embedding_output",
        dest="discovery_theme_embedding_output",
        type=str,
        default="stage1_env_discovery/temp_result/step3_clustering_deduplication.embeddings.json",
    )
    parser.add_argument(
        "--discovery_selected_theme_output",
        dest="discovery_selected_theme_output",
        type=str,
        default="stage1_env_discovery/temp_result/step3_clustering_deduplication.selected.json",
    )
    parser.add_argument(
        "--discovery_final_output",
        dest="discovery_final_output",
        type=str,
        default="stage1_env_discovery/final_result/discovered_environment_themes.json",
    )
    parser.add_argument("--judge_model", type=str, default="gpt-4.1")
    parser.add_argument("--judge_max_workers", type=int, default=3)
    parser.add_argument("--topic_model", type=str, default="gpt-4.1")
    parser.add_argument("--topic_num_workers", type=int, default=3)
    parser.add_argument("--enable_theme_embedding", dest="enable_theme_embedding", action="store_true")
    parser.add_argument("--embedding_model", type=str, default="text-embedding-3-large")
    parser.add_argument("--embedding_batch_size", type=int, default=2)
    parser.add_argument("--embedding_timeout", type=int, default=60)
    parser.add_argument("--enable_theme_clustering", dest="enable_theme_clustering", action="store_true")
    parser.add_argument("--theme_modelability_threshold", dest="theme_modelability_threshold", type=int, default=7)
    parser.add_argument("--theme_usefulness_threshold", dest="theme_usefulness_threshold", type=int, default=7)
    parser.add_argument("--theme_cluster_count", dest="theme_cluster_count", type=int, default=50)

    parser.add_argument(
        "--synthesis_input_themes",
        dest="synthesis_input_themes",
        type=str,
        default="stage1_env_discovery/final_result/discovered_environment_themes.json",
    )
    parser.add_argument("--state_deduction_model", dest="state_deduction_model", type=str, default="gpt-4.1")
    parser.add_argument("--state_scaffold_model", dest="state_scaffold_model", type=str, default="gpt-4.1")
    parser.add_argument("--interface_design_model", dest="interface_design_model", type=str, default="gpt-4.1")
    parser.add_argument("--program_synthesis_model", dest="program_synthesis_model", type=str, default="gpt-4.1")
    parser.add_argument("--program_synthesis_max_workers", dest="program_synthesis_max_workers", type=int, default=2)
    parser.add_argument("--state_deduction_save_every", dest="state_deduction_save_every", type=int, default=10)
    parser.add_argument("--state_schema_output", dest="state_schema_output", type=str, default="stage2_env_synthesis/temp_result/step1_state_deduction.schema.json")
    parser.add_argument("--state_scaffold_output", dest="state_scaffold_output", type=str, default="stage2_env_synthesis/temp_result/step1_state_deduction.scaffold.json")
    parser.add_argument("--interface_design_output", dest="interface_design_output", type=str, default="stage2_env_synthesis/temp_result/step2_interface_design.json")
    parser.add_argument("--operation_code_output", dest="operation_code_output", type=str, default="stage2_env_synthesis/temp_result/step3_program_synthesis.functions.json")
    parser.add_argument("--assembled_program_output", dest="assembled_program_output", type=str, default="stage2_env_synthesis/temp_result/step3_program_synthesis.programs.json")
    parser.add_argument("--verified_program_output", dest="verified_program_output", type=str, default="stage2_env_synthesis/temp_result/step3_program_synthesis.verified.json")
    parser.add_argument(
        "--synthesis_final_output",
        dest="synthesis_final_output",
        type=str,
        default="stage2_env_synthesis/final_result/synthesized_environments.json",
    )

    parser.add_argument(
        "--evolution_input_envs",
        dest="evolution_input_envs",
        type=str,
        default="stage2_env_synthesis/final_result/synthesized_environments.json",
    )
    parser.add_argument("--evolution_temp_dir", dest="evolution_temp_dir", type=str, default="stage3_refine/temp_result")
    parser.add_argument("--evolution_final_dir", dest="evolution_final_dir", type=str, default="stage3_refine/final_result")
    parser.add_argument("--evolution_threshold", dest="evolution_threshold", type=float, default=0.85)
    parser.add_argument("--evolution_positive_pass_threshold", dest="evolution_positive_pass_threshold", type=float, default=0.5)
    parser.add_argument("--evolution_init_config_count", dest="evolution_init_config_count", type=int, default=1)
    parser.add_argument("--evolution_eval_steps", dest="evolution_eval_steps", type=int, default=100)
    parser.add_argument("--evolution_max_repair_rounds", dest="evolution_max_repair_rounds", type=int, default=3)
    parser.add_argument("--evolution_top_n", dest="evolution_top_n", type=int, default=5)
    parser.add_argument("--evolution_max_cases_per_function", dest="evolution_max_cases_per_function", type=int, default=5)
    parser.add_argument("--evolution_init_model", dest="evolution_init_model", type=str, default="gpt-4.1")
    parser.add_argument("--evolution_init_temperature", dest="evolution_init_temperature", type=float, default=0.5)
    parser.add_argument("--evolution_eval_model", dest="evolution_eval_model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--evolution_eval_temperature", dest="evolution_eval_temperature", type=float, default=0.5)
    parser.add_argument("--evolution_agent_mode", dest="evolution_agent_mode", type=str, choices=["dual", "local"], default="dual")
    parser.add_argument("--evolution_enable_llm_patch", dest="evolution_enable_llm_patch", action="store_true")
    parser.add_argument("--evolution_llm_patch_model", dest="evolution_llm_patch_model", type=str, default="gpt-4.1")
    parser.add_argument("--evolution_llm_patch_temperature", dest="evolution_llm_patch_temperature", type=float, default=0.1)
    parser.add_argument("--evolution_skip_llm_init", dest="evolution_skip_llm_init", action="store_true")
    parser.add_argument("--evolution_reuse_existing_init_config", dest="evolution_reuse_existing_init_config", action="store_true")

    parser.add_argument(
        "--multi_api_count",
        type=int,
        default=1,
        help=(
            "Number of API profiles to use in parallel for Env Synthesis/Env Evolution. "
            "Env Discovery always stays on a single API."
        ),
    )
    parser.add_argument(
        "--multi_api_config",
        type=str,
        default="",
        help=(
            "JSON config containing per-API settings. "
            "Required when --multi_api_count > 1."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    random.seed(args.random_seed)
    os.chdir(PIPELINE_DIR)

    # If user does not specify stages, default to Env Discovery + Env Synthesis.
    if not any([args.run_env_discovery, args.run_env_synthesis, args.run_env_evolution]):
        args.run_env_discovery = True
        args.run_env_synthesis = True

    if args.dry_run:
        print(json.dumps(_public_arg_dump(args), ensure_ascii=False, indent=2))
        return

    discovery_output: str | None = None
    synthesis_output: str | None = None

    try:
        if args.run_env_discovery:
            discovery_output = run_env_discovery(args)

        if args.run_env_synthesis:
            synthesis_output = run_env_synthesis(args, discovery_output=discovery_output)

        if args.run_env_evolution:
            run_env_evolution(args, synthesis_output=synthesis_output)
    except StageBlockedError as exc:
        print(str(exc))
        print("[Paused] Fix the blocked API/profile and rerun the same command with --resume.")
        raise SystemExit(2) from exc
    except StageResumeSignalHandled as exc:
        print(str(exc))
        raise SystemExit(0) from exc
    except StageCoordinatorActiveError as exc:
        print(str(exc))
        raise SystemExit(2) from exc
    except (RecoverableAPIError, RecoverableStepError) as exc:
        print(f"[Paused] {exc}")
        print("[Paused] Fix the API/network issue and rerun the same command with --resume.")
        raise SystemExit(2) from exc

    print("\n[Done] All selected stages finished.")


if __name__ == "__main__":
    main()
