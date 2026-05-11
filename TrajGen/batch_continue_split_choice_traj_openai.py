from __future__ import annotations

import argparse
import copy
import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.api_slots import ApiSlot, load_api_slots
from TrajGen.continue_split_choice_traj_openai import (
    ROOT_DIR,
    RUNS_ROOT,
    _find_trace_event,
    _is_split_text_and_tool_choices,
    _load_json,
    continue_from_split_choice,
)


def _case_sort_key(case_id: str) -> tuple[int, str]:
    stem = Path(case_id).stem
    if stem.startswith("case_"):
        try:
            return (int(stem.split("_", 1)[1]), stem)
        except Exception:
            pass
    return (10**9, stem)


def _normalize_case_id(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    stem = Path(text).stem
    if stem.endswith("_traj"):
        stem = stem[: -len("_traj")]
    return stem


def _iter_case_ids_from_file(path: Path) -> Iterable[str]:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        yield _normalize_case_id(line.split()[0])


def _iter_case_ids_from_cases_dir(path: Path) -> Iterable[str]:
    for case_path in sorted(path.rglob("*.json")):
        if case_path.name == "manifest.json":
            continue
        try:
            data = _load_json(case_path)
        except Exception:
            data = {}
        case_id = data.get("case_id") if isinstance(data, dict) else None
        yield _normalize_case_id(str(case_id or case_path.stem))


def _dedupe_case_ids(case_ids: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for case_id in case_ids:
        normalized = _normalize_case_id(case_id)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return sorted(out, key=_case_sort_key)


def _load_case_ids(args: argparse.Namespace) -> List[str]:
    values: List[str] = []
    values.extend(_normalize_case_id(item) for item in (args.case_ids or []))
    if args.case_ids_file:
        values.extend(_iter_case_ids_from_file(Path(args.case_ids_file).expanduser().resolve()))
    if args.cases_dir:
        values.extend(_iter_case_ids_from_cases_dir(Path(args.cases_dir).expanduser().resolve()))
    return _dedupe_case_ids(values)


def _case_state_path(source_run_name: str, case_id: str) -> Path:
    return RUNS_ROOT / source_run_name / "cases" / case_id / "state.json"


def _load_case_state(source_run_name: str, case_id: str) -> Dict[str, Any]:
    state_path = _case_state_path(source_run_name, case_id)
    if not state_path.exists():
        raise FileNotFoundError(f"case state not found: {state_path}")
    state = _load_json(state_path)
    if not isinstance(state, dict):
        raise ValueError(f"case state is not an object: {state_path}")
    return state


def _latest_error_raw(source_run_name: str, case_id: str) -> Dict[str, Any]:
    state = _load_case_state(source_run_name, case_id)
    attempt_dir = Path(str(state.get("last_attempt_dir") or "")).expanduser().resolve()
    if not attempt_dir.exists():
        raise FileNotFoundError(f"last_attempt_dir not found for {case_id}: {attempt_dir}")
    trace_dir = attempt_dir / "trace"
    event = _find_trace_event(trace_dir, category="tir_agent_openai", name="step_llm_error", latest=True)
    payload = event.get("payload") or {}
    response = payload.get("response") if isinstance(payload, dict) else None
    raw = response.get("raw") if isinstance(response, dict) else None
    if not isinstance(raw, dict):
        raise ValueError(f"raw failed response missing for {case_id}")
    return raw


def _is_strict_split_case(source_run_name: str, case_id: str) -> bool:
    raw = _latest_error_raw(source_run_name, case_id)
    _is_split_text_and_tool_choices(raw)
    return True


def _formal_output_path(source_run_name: str, case_id: str, output_root: Path) -> Path:
    state = _load_case_state(source_run_name, case_id)
    rel = str(state.get("relative_traj_path") or "").strip()
    if rel:
        return output_root / rel
    return output_root / f"{case_id}_traj.json"


def _write_case_result(output_run_dir: Path, case_id: str, result: Dict[str, Any]) -> None:
    case_dir = output_run_dir / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def _continue_one(
    *,
    source_run_name: str,
    case_id: str,
    slot: ApiSlot,
    scratch_output_root: Path,
    formal_output_root: Path,
    output_run_dir: Path,
    merge_subsequent_split_choices: bool,
    eval_model: Optional[str],
    skip_non_split: bool,
    skip_existing: bool,
) -> Dict[str, Any]:
    if skip_existing:
        formal_path = _formal_output_path(source_run_name, case_id, formal_output_root)
        if formal_path.exists():
            return {
                "case_id": case_id,
                "status": "skipped_existing",
                "slot_id": slot.slot_id,
                "slot_name": slot.name,
                "formal_output_path": str(formal_path),
                "promoted": False,
            }

    if skip_non_split:
        try:
            _is_strict_split_case(source_run_name, case_id)
        except Exception as exc:
            return {
                "case_id": case_id,
                "status": "skipped_non_split",
                "slot_id": slot.slot_id,
                "slot_name": slot.name,
                "error": str(exc),
                "promoted": False,
            }

    case_args = argparse.Namespace(
        run_name=source_run_name,
        case_id=case_id,
        attempt_dir=None,
        failed_traj_path=None,
        output_traj_root=str(scratch_output_root),
        merge_subsequent_split_choices=merge_subsequent_split_choices,
        eval_api_key=slot.api_key,
        eval_base_url=slot.base_url,
        eval_model=eval_model,
        slot_id=slot.slot_id,
        slot_name=slot.name,
    )
    try:
        repair_log = continue_from_split_choice(case_args)
        scratch_path = Path(str(repair_log["output_traj_path"]))
        continued = _load_json(scratch_path)
        status = str(continued.get("status") or repair_log.get("status") or "")
        formal_path = _formal_output_path(source_run_name, case_id, formal_output_root)
        promoted = False
        if status == "finished":
            formal_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(scratch_path, formal_path)
            promoted = True
        result = {
            "case_id": case_id,
            "status": status,
            "slot_id": slot.slot_id,
            "slot_name": slot.name,
            "scratch_output_path": str(scratch_path),
            "formal_output_path": str(formal_path),
            "repair_log": repair_log,
            "promoted": promoted,
        }
    except Exception as exc:
        result = {
            "case_id": case_id,
            "status": "exception",
            "slot_id": slot.slot_id,
            "slot_name": slot.name,
            "error": f"{type(exc).__name__}: {exc}",
            "promoted": False,
        }
    _write_case_result(output_run_dir, case_id, result)
    return result


def _build_plan(case_ids: List[str], slots: List[ApiSlot]) -> List[Dict[str, Any]]:
    return [
        {
            "case_id": case_id,
            "slot_id": slots[idx % len(slots)].slot_id,
            "slot_name": slots[idx % len(slots)].name,
        }
        for idx, case_id in enumerate(case_ids)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Batch continue split-choice OpenAI-tool trajectories by assigning cases to API slots "
            "and reusing the single-case merge+continue logic."
        )
    )
    parser.add_argument("--source_run_name", required=True, help="Failed source run under TrajGen/traj_batch_runs.")
    parser.add_argument(
        "--run_name",
        default=f"split_choice_continue_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="New batch-wrapper run name under TrajGen/traj_batch_runs.",
    )
    parser.add_argument("--api_slots_json", required=True, help="API slot config JSON.")
    parser.add_argument("--traj_output_dir_name", required=True, help="Formal trajectory output root.")
    parser.add_argument("--case_ids", nargs="*", default=[], help="Case ids to continue.")
    parser.add_argument("--case_ids_file", default=None, help="Optional newline-delimited case id list.")
    parser.add_argument("--cases_dir", default=None, help="Optional directory containing case_*.json files.")
    parser.add_argument("--eval_model", default=None, help="Optional model override. Defaults to source attempt model.")
    parser.add_argument("--max_workers", type=int, default=None, help="Default: number of loaded API slots.")
    parser.add_argument(
        "--merge_subsequent_split_choices",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also merge later strict text/tool split choices during continuation.",
    )
    parser.add_argument(
        "--skip_non_split",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip cases whose latest failed response is not a strict text-only + tool-only split.",
    )
    parser.add_argument("--skip_existing", action="store_true", help="Skip cases whose formal output already exists.")
    parser.add_argument("--dry_run", action="store_true", help="Only build the plan and validate inputs; do not call APIs.")
    args = parser.parse_args()

    case_ids = _load_case_ids(args)
    if not case_ids:
        raise ValueError("No case ids provided. Use --case_ids, --case_ids_file, or --cases_dir.")

    slots = load_api_slots(Path(args.api_slots_json).expanduser().resolve())
    if not slots:
        raise ValueError(f"No API slots loaded from {args.api_slots_json}")

    output_run_dir = RUNS_ROOT / args.run_name
    output_run_dir.mkdir(parents=True, exist_ok=True)
    scratch_output_root = output_run_dir / "continued_traj"
    scratch_output_root.mkdir(parents=True, exist_ok=True)
    formal_output_root = (ROOT_DIR / args.traj_output_dir_name).resolve()

    plan = _build_plan(case_ids, slots)
    plan_payload = {
        "source_run_name": args.source_run_name,
        "run_name": args.run_name,
        "api_slots_json": str(Path(args.api_slots_json).expanduser().resolve()),
        "traj_output_dir_name": str(formal_output_root),
        "case_count": len(case_ids),
        "slot_count": len(slots),
        "max_workers": min(args.max_workers or len(slots), len(case_ids)),
        "skip_non_split": args.skip_non_split,
        "skip_existing": args.skip_existing,
        "plan": plan,
    }
    (output_run_dir / "plan.json").write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dry_run:
        dry_run_cases: List[Dict[str, Any]] = []
        for item in plan:
            case_id = str(item["case_id"])
            case_report = dict(item)
            case_report["formal_output_exists"] = _formal_output_path(
                args.source_run_name,
                case_id,
                formal_output_root,
            ).exists()
            try:
                _is_strict_split_case(args.source_run_name, case_id)
                case_report["strict_split"] = True
            except Exception as exc:
                case_report["strict_split"] = False
                case_report["strict_split_error"] = str(exc)
            dry_run_cases.append(case_report)
        print(json.dumps({**plan_payload, "dry_run": True, "dry_run_cases": dry_run_cases}, ensure_ascii=False, indent=2))
        return 0

    worker_count = min(args.max_workers or len(slots), len(case_ids))
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = []
        for idx, case_id in enumerate(case_ids):
            slot = copy.copy(slots[idx % len(slots)])
            futures.append(
                executor.submit(
                    _continue_one,
                    source_run_name=args.source_run_name,
                    case_id=case_id,
                    slot=slot,
                    scratch_output_root=scratch_output_root,
                    formal_output_root=formal_output_root,
                    output_run_dir=output_run_dir,
                    merge_subsequent_split_choices=args.merge_subsequent_split_choices,
                    eval_model=args.eval_model,
                    skip_non_split=args.skip_non_split,
                    skip_existing=args.skip_existing,
                )
            )

        for fut in as_completed(futures):
            result = fut.result()
            results.append(result)
            print(
                "[SPLIT-CHOICE-BATCH] "
                f"slot={result.get('slot_name')} case={result.get('case_id')} "
                f"status={result.get('status')} promoted={result.get('promoted')}"
            )

    results.sort(key=lambda item: _case_sort_key(str(item.get("case_id") or "")))
    report = {
        **{k: v for k, v in plan_payload.items() if k != "plan"},
        "results": results,
        "finished_count": sum(1 for item in results if item.get("status") == "finished"),
        "promoted_count": sum(1 for item in results if item.get("promoted")),
        "exception_count": sum(1 for item in results if item.get("status") == "exception"),
        "skipped_non_split_count": sum(1 for item in results if item.get("status") == "skipped_non_split"),
        "skipped_existing_count": sum(1 for item in results if item.get("status") == "skipped_existing"),
        "max_steps_count": sum(1 for item in results if item.get("status") == "max_steps"),
        "error_count": sum(1 for item in results if item.get("status") == "error"),
    }
    (output_run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
