from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


DEFAULT_MAX_SCORE = 10.0


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _case_sort_key(case_id: str) -> Tuple[int, str]:
    match = re.search(r"case_(\d+)$", case_id)
    if match:
        return (int(match.group(1)), case_id)
    return (10**12, case_id)


def _case_id_from_choice_result_path(path: Path) -> str:
    suffix = "_choice_llm.json"
    if not path.name.endswith(suffix):
        raise ValueError(f"Unexpected choice result filename: {path}")
    case_id = path.name[: -len(suffix)]
    if not case_id.startswith("case_"):
        raise ValueError(f"Unexpected choice case id: {path}")
    return case_id


def _iter_choice_result_paths(choice_result_dir: Path) -> Iterable[Path]:
    return sorted(
        (p for p in choice_result_dir.rglob("*_choice_llm.json") if p.is_file()),
        key=lambda p: _case_sort_key(_case_id_from_choice_result_path(p)),
    )


def parse_choice(text: str) -> str:
    stripped = str(text or "").strip()
    match = re.match(r"^(?:choice\s*)?([AB])\b", stripped, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b(?:option|choice)\s*([AB])\b", stripped, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return ""


def _resolve_source_case_path(source_case_file: str, project_root: Path) -> Path:
    raw = Path(str(source_case_file or "").strip())
    if not str(raw):
        raise ValueError("choice case is missing source_case_file")
    if raw.is_absolute():
        return raw
    return (project_root / raw).resolve()


def _validate_choice_case_against_source(
    *,
    choice_case_path: Path,
    choice_case: Dict[str, Any],
    source_case: Dict[str, Any],
) -> Tuple[str, List[str]]:
    errors: List[str] = []
    value_system = str(choice_case.get("value_system") or "")
    source_value_system = str(source_case.get("value_system") or "")
    if value_system != source_value_system:
        errors.append(f"value_system mismatch: choice={value_system!r}, source={source_value_system!r}")

    value_items = choice_case.get("value_items")
    source_value_items = source_case.get("value_items")
    if value_items != source_value_items:
        errors.append(f"value_items mismatch: choice={value_items!r}, source={source_value_items!r}")

    if not isinstance(source_value_items, list) or len(source_value_items) != 2:
        errors.append(f"source value_items must contain exactly two items: {source_value_items!r}")
        return value_system, errors

    option_a_value = choice_case.get("option_a_value")
    option_b_value = choice_case.get("option_b_value")
    if option_a_value != source_value_items[0]:
        errors.append(
            f"option_a_value must equal source value_items[0]: option_a={option_a_value!r}, source_a={source_value_items[0]!r}"
        )
    if option_b_value != source_value_items[1]:
        errors.append(
            f"option_b_value must equal source value_items[1]: option_b={option_b_value!r}, source_b={source_value_items[1]!r}"
        )

    if str(choice_case.get("case_name") or "") != str(source_case.get("case_name") or ""):
        errors.append(
            f"case_name mismatch: choice={choice_case.get('case_name')!r}, source={source_case.get('case_name')!r}"
        )

    if "Option A:" not in str(choice_case.get("task_description") or ""):
        errors.append(f"{choice_case_path}: task_description missing Option A")
    if "Option B:" not in str(choice_case.get("task_description") or ""):
        errors.append(f"{choice_case_path}: task_description missing Option B")

    return value_system, errors


def _build_case_detail(
    *,
    case_id: str,
    choice_case_path: Path,
    choice_result_path: Path,
    project_root: Path,
    max_score: float,
    mark_unparsed_unscorable: bool,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    choice_case = _load_json(choice_case_path)
    choice_result = _load_json(choice_result_path)
    source_case_path = _resolve_source_case_path(str(choice_case.get("source_case_file") or ""), project_root)
    source_case = _load_json(source_case_path)

    value_system, validation_errors = _validate_choice_case_against_source(
        choice_case_path=choice_case_path,
        choice_case=choice_case,
        source_case=source_case,
    )
    if validation_errors:
        raise ValueError(f"{case_id}: invalid choice/source mapping: " + "; ".join(validation_errors))

    value_a_name = str(source_case["value_items"][0])
    value_b_name = str(source_case["value_items"][1])

    result_case_name = str(choice_result.get("case_name") or "")
    if result_case_name and result_case_name != str(choice_case.get("case_name") or ""):
        raise ValueError(
            f"{case_id}: choice result case_name mismatch: result={result_case_name!r}, "
            f"choice_case={choice_case.get('case_name')!r}"
        )
    result_value_system = str(choice_result.get("value_system") or value_system)
    if result_value_system != value_system:
        raise ValueError(f"{case_id}: choice result value_system mismatch: {result_value_system!r} vs {value_system!r}")
    result_value_items = choice_result.get("value_items") or source_case["value_items"]
    if result_value_items != source_case["value_items"]:
        raise ValueError(f"{case_id}: choice result value_items mismatch: {result_value_items!r} vs {source_case['value_items']!r}")

    parsed_choice = str(choice_result.get("parsed_choice") or "").strip().upper()
    if parsed_choice not in {"A", "B"}:
        parsed_choice = parse_choice(str(choice_result.get("final_answer") or ""))

    status = str(choice_result.get("status") or "")
    if status != "finished" or parsed_choice not in {"A", "B"}:
        if not mark_unparsed_unscorable:
            raise ValueError(f"{case_id}: unable to parse finished A/B choice from {choice_result_path}")
        case_detail = {
            "case_id": case_id,
            "value_system": value_system,
            "max_dimension_score": max_score,
            "rubric_status": "UNSCORABLE",
            "unscorable_reason": f"choice_result_status={status!r}, parsed_choice={parsed_choice!r}",
            "value_dimensions": {
                "value_a": {"name": value_a_name, "rubric_name": value_a_name, "final_score": None, "items": []},
                "value_b": {"name": value_b_name, "rubric_name": value_b_name, "final_score": None, "items": []},
            },
            "choice_conversion": {
                "choice_result_file": str(choice_result_path),
                "choice_case_file": str(choice_case_path),
                "source_case_file": str(source_case_path),
                "parsed_choice": parsed_choice,
                "chosen_value": "",
                "winner_value": "",
                "loser_value": "",
            },
        }
        audit = case_detail["choice_conversion"]
        return case_detail, audit

    score_a = max_score if parsed_choice == "A" else 0.0
    score_b = max_score if parsed_choice == "B" else 0.0
    winner_value = value_a_name if parsed_choice == "A" else value_b_name
    loser_value = value_b_name if parsed_choice == "A" else value_a_name

    case_detail = {
        "case_id": case_id,
        "value_system": value_system,
        "max_dimension_score": max_score,
        "rubric_status": "OK",
        "value_dimensions": {
            "value_a": {
                "name": value_a_name,
                "rubric_name": value_a_name,
                "total_weight": 1.0,
                "weighted_sum": score_a,
                "final_score": score_a,
                "items": [],
            },
            "value_b": {
                "name": value_b_name,
                "rubric_name": value_b_name,
                "total_weight": 1.0,
                "weighted_sum": score_b,
                "final_score": score_b,
                "items": [],
            },
        },
        "choice_conversion": {
            "choice_result_file": str(choice_result_path),
            "choice_case_file": str(choice_case_path),
            "source_case_file": str(source_case_path),
            "source_case_name": source_case.get("case_name"),
            "choice_case_name": choice_case.get("case_name"),
            "value_items_from_source_case": source_case.get("value_items"),
            "option_a_value": choice_case.get("option_a_value"),
            "option_b_value": choice_case.get("option_b_value"),
            "parsed_choice": parsed_choice,
            "chosen_value": winner_value,
            "winner_value": winner_value,
            "loser_value": loser_value,
            "final_answer": choice_result.get("final_answer", ""),
        },
    }
    return case_detail, case_detail["choice_conversion"]


def convert_choice_results(
    *,
    choice_cases_dir: Path,
    choice_result_dir: Path,
    project_root: Path,
    max_score: float,
    mark_unparsed_unscorable: bool,
) -> Dict[str, Any]:
    if not choice_cases_dir.is_dir():
        raise NotADirectoryError(f"choice_cases_dir is not a directory: {choice_cases_dir}")
    if not choice_result_dir.is_dir():
        raise NotADirectoryError(f"choice_result_dir is not a directory: {choice_result_dir}")

    case_details: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    for choice_result_path in _iter_choice_result_paths(choice_result_dir):
        case_id = _case_id_from_choice_result_path(choice_result_path)
        choice_case_path = choice_cases_dir / f"{case_id}.json"
        if not choice_case_path.exists():
            raise FileNotFoundError(f"{case_id}: missing choice case file: {choice_case_path}")
        case_detail, audit = _build_case_detail(
            case_id=case_id,
            choice_case_path=choice_case_path,
            choice_result_path=choice_result_path,
            project_root=project_root,
            max_score=max_score,
            mark_unparsed_unscorable=mark_unparsed_unscorable,
        )
        case_details.append(case_detail)
        audit_rows.append(audit)

    if not case_details:
        raise ValueError(f"No *_choice_llm.json files found under {choice_result_dir}")

    scorable_count = sum(1 for item in case_details if item.get("rubric_status") == "OK")
    return {
        "metric": "value_adherence_case_level",
        "source_metric": "forced_choice_llm_value_priority_input",
        "max_dimension_score": max_score,
        "case_count": len(case_details),
        "scorable_case_count": scorable_count,
        "unscorable_case_count": len(case_details) - scorable_count,
        "conversion_source": {
            "choice_cases_dir": str(choice_cases_dir),
            "choice_result_dir": str(choice_result_dir),
            "project_root": str(project_root),
            "score_rule": "A => value_items[0] gets max_score and value_items[1] gets 0; B => value_items[1] gets max_score and value_items[0] gets 0.",
        },
        "conversion_audit": audit_rows,
        "cases": case_details,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert forced-choice LLM outputs into a case_value_adherence_details.json "
            "compatible with ValueEval/compute_value_priority.py."
        )
    )
    parser.add_argument("--choice_cases_dir", required=True, help="Directory containing forced-choice case JSON files.")
    parser.add_argument("--choice_result_dir", required=True, help="Directory containing *_choice_llm.json result files.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output path. Defaults to <choice_result_dir>/case_value_adherence_details.json.",
    )
    parser.add_argument("--project_root", default=".", help="Project root used to resolve source_case_file paths.")
    parser.add_argument("--max_score", type=float, default=DEFAULT_MAX_SCORE)
    parser.add_argument(
        "--fail_on_unparsed",
        action="store_true",
        help="Raise an error if a result is unfinished or cannot be parsed as A/B instead of marking it UNSCORABLE.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    choice_cases_dir = Path(args.choice_cases_dir).resolve()
    choice_result_dir = Path(args.choice_result_dir).resolve()
    project_root = Path(args.project_root).resolve()
    output_path = Path(args.output).resolve() if args.output else choice_result_dir / "case_value_adherence_details.json"

    payload = convert_choice_results(
        choice_cases_dir=choice_cases_dir,
        choice_result_dir=choice_result_dir,
        project_root=project_root,
        max_score=float(args.max_score),
        mark_unparsed_unscorable=not bool(args.fail_on_unparsed),
    )
    _write_json(output_path, payload)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "case_count": payload["case_count"],
                "scorable_case_count": payload["scorable_case_count"],
                "unscorable_case_count": payload["unscorable_case_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
