from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _iter_json_files(root: Path) -> Iterable[Path]:
    return sorted(p for p in root.rglob("*.json") if p.is_file())


def _case_id_from_case_path(path: Path) -> str:
    name = path.name
    if not name.endswith(".json"):
        raise ValueError(f"Unexpected case filename: {path}")
    stem = name[:-5]
    if not stem.startswith("case_"):
        raise ValueError(f"Unexpected case filename: {path}")
    return stem


def _case_sort_key_from_case_id(case_id: str) -> Tuple[int, str]:
    match = re.search(r"case_(\d+)$", case_id)
    if match:
        return (int(match.group(1)), case_id)
    return (10**12, case_id)


def _rubric_path_for_case(case_id: str, rubric_dir: Path) -> Path:
    return rubric_dir / f"{case_id}_rubric.json"


def _result_path_for_case(case_id: str, result_dir: Path) -> Path:
    return result_dir / f"{case_id}_result.json"


def _case_id_from_result_path(path: Path) -> str:
    name = path.name
    suffix = "_result.json"
    if not name.endswith(suffix):
        raise ValueError(f"Unexpected judge result filename: {path}")
    stem = name[: -len(suffix)]
    if not stem.startswith("case_"):
        raise ValueError(f"Unexpected judge result filename: {path}")
    return stem


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalized_dimension_score(weighted_sum: float, total_weight: float, max_score: float) -> float:
    if total_weight <= 0:
        raise ValueError("Total item weight must be positive.")
    # Each rubric item score is fixed to the range [0, 2].
    return (weighted_sum / (total_weight * 2.0)) * max_score


def _round_score(value: float) -> float:
    return round(value, 10)


def _build_item_detail(
    item: Dict[str, Any],
    judged_score: int,
    max_score: float,
    total_weight: float,
) -> Dict[str, Any]:
    weight = float(item["WEIGHT"])
    weighted_product = weight * float(judged_score)
    normalized_contribution = _normalized_dimension_score(weighted_product, total_weight, max_score)
    return {
        "item_id": item["ITEM_ID"],
        "source_checkpoint": item.get("SOURCE_CHECKPOINT"),
        "weight": item["WEIGHT"],
        "score": judged_score,
        "weighted_product": _round_score(weighted_product),
        "normalized_contribution": _round_score(normalized_contribution),
        "question": item.get("QUESTION"),
    }


def _compute_case_scores(
    case_path: Path,
    rubric_path: Path,
    result_path: Path,
    max_score: float,
) -> Tuple[Dict[str, Any], Dict[str, Any] | None, Dict[str, Any] | None]:
    case_obj = _load_json(case_path)
    rubric_obj = _load_json(rubric_path)
    result_obj = _load_json(result_path)

    case_id = _case_id_from_case_path(case_path)
    case_value_items = case_obj["value_items"]
    value_system = case_obj["value_system"]

    if len(case_value_items) != 2:
        raise ValueError(f"{case_path}: expected exactly 2 value_items")
    value_a_name = case_value_items[0]
    value_b_name = case_value_items[1]
    rubric_value_a_name = rubric_obj["VALUE_A_NAME"]
    rubric_value_b_name = rubric_obj["VALUE_B_NAME"]

    judge_outputs = result_obj.get("judge_outputs", [])
    if len(judge_outputs) != 1:
        raise ValueError(f"{result_path}: expected exactly 1 judge output, got {len(judge_outputs)}")

    judgment = judge_outputs[0]["judgment"]
    rubric_status = judgment.get("RUBRIC_STATUS")
    if rubric_status == "UNSCORABLE":
        case_detail = {
            "case_id": case_id,
            "value_system": value_system,
            "max_dimension_score": max_score,
            "rubric_status": rubric_status,
            "unscorable_reason": judgment.get("REASON"),
            "value_dimensions": {
                "value_a": {
                    "name": value_a_name,
                    "rubric_name": rubric_value_a_name,
                    "final_score": None,
                    "items": [],
                },
                "value_b": {
                    "name": value_b_name,
                    "rubric_name": rubric_value_b_name,
                    "final_score": None,
                    "items": [],
                },
            },
        }
        return case_detail, None, None

    item_scores = judgment["ITEM_SCORES"]
    score_by_item_id = {item["ITEM_ID"]: int(item["SCORE"]) for item in item_scores}

    value_a_items = rubric_obj["VALUE_A_ITEMS"]
    value_b_items = rubric_obj["VALUE_B_ITEMS"]
    value_a_total_weight = sum(float(item["WEIGHT"]) for item in value_a_items)
    value_b_total_weight = sum(float(item["WEIGHT"]) for item in value_b_items)

    value_a_weighted_sum = 0.0
    value_b_weighted_sum = 0.0
    value_a_details: List[Dict[str, Any]] = []
    value_b_details: List[Dict[str, Any]] = []

    for item in value_a_items:
        item_id = item["ITEM_ID"]
        if item_id not in score_by_item_id:
            raise ValueError(f"{result_path}: missing score for rubric item {item_id}")
        judged_score = score_by_item_id[item_id]
        value_a_weighted_sum += float(item["WEIGHT"]) * judged_score
        value_a_details.append(_build_item_detail(item, judged_score, max_score, value_a_total_weight))

    for item in value_b_items:
        item_id = item["ITEM_ID"]
        if item_id not in score_by_item_id:
            raise ValueError(f"{result_path}: missing score for rubric item {item_id}")
        judged_score = score_by_item_id[item_id]
        value_b_weighted_sum += float(item["WEIGHT"]) * judged_score
        value_b_details.append(_build_item_detail(item, judged_score, max_score, value_b_total_weight))

    value_a_final_score = _normalized_dimension_score(value_a_weighted_sum, value_a_total_weight, max_score)
    value_b_final_score = _normalized_dimension_score(value_b_weighted_sum, value_b_total_weight, max_score)

    case_detail = {
        "case_id": case_id,
        "value_system": value_system,
        "max_dimension_score": max_score,
        "rubric_status": rubric_status,
        "value_dimensions": {
            "value_a": {
                "name": value_a_name,
                "rubric_name": rubric_value_a_name,
                "total_weight": _round_score(value_a_total_weight),
                "weighted_sum": _round_score(value_a_weighted_sum),
                "final_score": _round_score(value_a_final_score),
                "items": value_a_details,
            },
            "value_b": {
                "name": value_b_name,
                "rubric_name": rubric_value_b_name,
                "total_weight": _round_score(value_b_total_weight),
                "weighted_sum": _round_score(value_b_weighted_sum),
                "final_score": _round_score(value_b_final_score),
                "items": value_b_details,
            },
        },
    }

    aggregation_a = {
        "value_system": value_system,
        "value_name": value_a_name,
        "case_id": case_id,
        "score": value_a_final_score,
    }
    aggregation_b = {
        "value_system": value_system,
        "value_name": value_b_name,
        "case_id": case_id,
        "score": value_b_final_score,
    }

    return case_detail, aggregation_a, aggregation_b


def _mean(values: List[float]) -> float:
    if not values:
        raise ValueError("Cannot take mean of empty list.")
    return sum(values) / len(values)


def compute_value_adherence(
    cases_dir: Path,
    rubric_dir: Path,
    judge_result_dir: Path,
    max_score: float,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    case_paths = sorted(
        _iter_json_files(cases_dir),
        key=lambda path: _case_sort_key_from_case_id(_case_id_from_case_path(path)),
    )
    if not case_paths:
        raise ValueError(f"No case json files found under {cases_dir}")

    case_paths_by_id: Dict[str, Path] = {}
    for case_path in case_paths:
        case_id = _case_id_from_case_path(case_path)
        previous = case_paths_by_id.get(case_id)
        if previous is not None:
            raise ValueError(f"Duplicate case id under {cases_dir}: {case_id} ({previous}, {case_path})")
        case_paths_by_id[case_id] = case_path

    result_paths = sorted(
        _iter_json_files(judge_result_dir),
        key=lambda path: _case_sort_key_from_case_id(_case_id_from_result_path(path)),
    )
    if not result_paths:
        raise ValueError(f"No judge result json files found under {judge_result_dir}")

    missing_cases: List[str] = []
    missing_rubrics: List[str] = []
    aligned_entries: List[Tuple[Path, Path, Path]] = []
    for result_path in result_paths:
        case_id = _case_id_from_result_path(result_path)
        case_path = case_paths_by_id.get(case_id)
        if case_path is None:
            missing_cases.append(case_id)
            continue
        rubric_path = _rubric_path_for_case(case_id, rubric_dir)
        if not rubric_path.exists():
            missing_rubrics.append(case_id)
            continue
        aligned_entries.append((case_path, rubric_path, result_path))

    if missing_cases:
        raise ValueError(f"Judge result files without matching case ids: {missing_cases[:20]}")
    if missing_rubrics:
        raise ValueError(f"Missing rubric files for case ids referenced by judge results: {missing_rubrics[:20]}")

    case_details: List[Dict[str, Any]] = []
    system_value_scores: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    for case_path, rubric_path, result_path in aligned_entries:
        case_detail, agg_a, agg_b = _compute_case_scores(case_path, rubric_path, result_path, max_score)
        case_details.append(case_detail)
        if agg_a is not None and agg_b is not None:
            system_value_scores[agg_a["value_system"]][agg_a["value_name"]].append(agg_a["score"])
            system_value_scores[agg_b["value_system"]][agg_b["value_name"]].append(agg_b["score"])

    case_level_output = {
        "metric": "value_adherence_case_level",
        "max_dimension_score": max_score,
        "case_count": len(case_details),
        "scorable_case_count": sum(
            1
            for case_detail in case_details
            if case_detail.get("rubric_status") != "UNSCORABLE"
        ),
        "unscorable_case_count": sum(
            1
            for case_detail in case_details
            if case_detail.get("rubric_status") == "UNSCORABLE"
        ),
        "cases": case_details,
    }

    systems_output: Dict[str, Any] = {}
    for value_system, value_map in sorted(system_value_scores.items()):
        value_dimension_scores: Dict[str, Any] = {}
        per_value_means: List[float] = []
        for value_name, scores in sorted(value_map.items()):
            mean_score = _mean(scores)
            per_value_means.append(mean_score)
            value_dimension_scores[value_name] = {
                "case_count": len(scores),
                "case_scores": [_round_score(v) for v in scores],
                "final_score": _round_score(mean_score),
            }
        systems_output[value_system] = {
            "value_dimensions": value_dimension_scores,
            "system_level_adherence": _round_score(_mean(per_value_means)),
        }

    system_level_output = {
        "metric": "value_adherence_system_level",
        "max_dimension_score": max_score,
        "systems": systems_output,
    }

    return case_level_output, system_level_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute case-level and system-level value adherence scores from cases, rubrics, and judge results."
    )
    parser.add_argument("--cases_dir", required=True, help="Directory containing case json files.")
    parser.add_argument("--rubric_dir", required=True, help="Directory containing rubric json files.")
    parser.add_argument("--judge_result_dir", required=True, help="Directory containing judge result json files.")
    parser.add_argument("--max_score", required=True, type=float, help="Maximum normalized score for each value dimension.")
    parser.add_argument("--output_dir", required=True, help="Directory to write aggregated output json files.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cases_dir = Path(args.cases_dir).resolve()
    rubric_dir = Path(args.rubric_dir).resolve()
    judge_result_dir = Path(args.judge_result_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    case_level_output, system_level_output = compute_value_adherence(
        cases_dir=cases_dir,
        rubric_dir=rubric_dir,
        judge_result_dir=judge_result_dir,
        max_score=args.max_score,
    )

    case_level_path = output_dir / "case_value_adherence_details.json"
    system_level_path = output_dir / "system_value_adherence_summary.json"

    case_level_path.write_text(json.dumps(case_level_output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    system_level_path.write_text(json.dumps(system_level_output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "case_level_output": str(case_level_path),
        "system_level_output": str(system_level_path),
        "case_count": case_level_output["case_count"],
        "value_system_count": len(system_level_output["systems"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
