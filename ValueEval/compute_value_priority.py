from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SMOOTHING = 0.01
DEFAULT_TOLERANCE = 1e-12
DEFAULT_MAX_ITERATIONS = 10_000


@dataclass
class DimensionAggregate:
    case_count: int = 0
    raw_wins: int = 0
    raw_losses: int = 0
    raw_ties: int = 0
    effective_wins: float = 0.0
    effective_losses: float = 0.0


@dataclass
class PairwiseAggregate:
    first: str
    second: str
    case_count: int = 0
    raw_wins_for_first: int = 0
    raw_wins_for_second: int = 0
    ties: int = 0
    effective_wins_for_first: float = 0.0
    effective_wins_for_second: float = 0.0


@dataclass
class SystemAggregate:
    case_count: int = 0
    dimensions: dict[str, DimensionAggregate] = field(default_factory=lambda: defaultdict(DimensionAggregate))
    pairwise: dict[tuple[str, str], PairwiseAggregate] = field(default_factory=dict)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute per-value-system Value Priority rankings from case_value_adherence_details.json "
            "with a Bradley-Terry model."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--model-dir",
        type=Path,
        help=(
            "Model result directory. The script reads <model-dir>/case_value_adherence_details.json "
            "and writes <model-dir>/value_priority_bradley_terry.json by default."
        ),
    )
    source_group.add_argument(
        "--input",
        type=Path,
        help="Explicit path to case_value_adherence_details.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Explicit output JSON path. Defaults next to the input file.",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=DEFAULT_SMOOTHING,
        help=(
            "Weak symmetric pseudo-count added to both directions of every observed value pair "
            f"(default: {DEFAULT_SMOOTHING})."
        ),
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
        help=f"MM solver convergence tolerance on centered log-strengths (default: {DEFAULT_TOLERANCE}).",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum MM iterations per value system (default: {DEFAULT_MAX_ITERATIONS}).",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level for the output file (default: 2).",
    )
    return parser.parse_args(argv)


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.model_dir is not None:
        input_path = args.model_dir / "case_value_adherence_details.json"
        output_path = args.output or (args.model_dir / "value_priority_bradley_terry.json")
    else:
        input_path = args.input
        output_path = args.output or args.input.with_name("value_priority_bradley_terry.json")

    return input_path.resolve(), output_path.resolve()


def _get_pair_record(system: SystemAggregate, first: str, second: str) -> PairwiseAggregate:
    key = (first, second)
    if key not in system.pairwise:
        system.pairwise[key] = PairwiseAggregate(first=first, second=second)
    return system.pairwise[key]


def _add_case_to_aggregate(system: SystemAggregate, value_a_name: str, value_b_name: str, score_a: float, score_b: float) -> None:
    system.case_count += 1

    dim_a = system.dimensions[value_a_name]
    dim_b = system.dimensions[value_b_name]
    dim_a.case_count += 1
    dim_b.case_count += 1

    first, second = sorted((value_a_name, value_b_name))
    pair_record = _get_pair_record(system, first, second)
    pair_record.case_count += 1

    if score_a > score_b:
        winner_name = value_a_name
        loser_name = value_b_name
        system.dimensions[winner_name].raw_wins += 1
        system.dimensions[winner_name].effective_wins += 1.0
        system.dimensions[loser_name].raw_losses += 1
        system.dimensions[loser_name].effective_losses += 1.0
        if winner_name == first:
            pair_record.raw_wins_for_first += 1
            pair_record.effective_wins_for_first += 1.0
        else:
            pair_record.raw_wins_for_second += 1
            pair_record.effective_wins_for_second += 1.0
        return

    if score_b > score_a:
        winner_name = value_b_name
        loser_name = value_a_name
        system.dimensions[winner_name].raw_wins += 1
        system.dimensions[winner_name].effective_wins += 1.0
        system.dimensions[loser_name].raw_losses += 1
        system.dimensions[loser_name].effective_losses += 1.0
        if winner_name == first:
            pair_record.raw_wins_for_first += 1
            pair_record.effective_wins_for_first += 1.0
        else:
            pair_record.raw_wins_for_second += 1
            pair_record.effective_wins_for_second += 1.0
        return

    dim_a.raw_ties += 1
    dim_b.raw_ties += 1
    dim_a.effective_wins += 0.5
    dim_b.effective_wins += 0.5
    dim_a.effective_losses += 0.5
    dim_b.effective_losses += 0.5
    pair_record.ties += 1
    pair_record.effective_wins_for_first += 0.5
    pair_record.effective_wins_for_second += 0.5


def aggregate_case_value_adherence(cases: list[dict[str, Any]]) -> tuple[dict[str, SystemAggregate], Counter[str]]:
    systems: dict[str, SystemAggregate] = {}
    skipped_reasons: Counter[str] = Counter()

    for case in cases:
        if case.get("rubric_status") != "OK":
            skipped_reasons["rubric_status_not_ok"] += 1
            continue

        value_system = case.get("value_system")
        value_dimensions = case.get("value_dimensions")
        if not value_system or not isinstance(value_dimensions, dict):
            skipped_reasons["missing_value_system_or_dimensions"] += 1
            continue

        value_a = value_dimensions.get("value_a")
        value_b = value_dimensions.get("value_b")
        if not isinstance(value_a, dict) or not isinstance(value_b, dict):
            skipped_reasons["missing_value_a_or_value_b"] += 1
            continue

        value_a_name = value_a.get("name")
        value_b_name = value_b.get("name")
        value_a_score = value_a.get("final_score")
        value_b_score = value_b.get("final_score")
        if not value_a_name or not value_b_name:
            skipped_reasons["missing_value_dimension_name"] += 1
            continue

        try:
            score_a = float(value_a_score)
            score_b = float(value_b_score)
        except (TypeError, ValueError):
            skipped_reasons["missing_or_invalid_final_score"] += 1
            continue

        system = systems.setdefault(value_system, SystemAggregate())
        _add_case_to_aggregate(system, value_a_name, value_b_name, score_a, score_b)

    return systems, skipped_reasons


def _reachable_nodes(graph: list[set[int]], start: int) -> set[int]:
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _build_graph_flags(pairwise_records: list[PairwiseAggregate], index_by_name: dict[str, int], dimension_count: int) -> tuple[bool, bool]:
    undirected = [set() for _ in range(dimension_count)]
    directed = [set() for _ in range(dimension_count)]
    reverse = [set() for _ in range(dimension_count)]

    for record in pairwise_records:
        first_idx = index_by_name[record.first]
        second_idx = index_by_name[record.second]
        undirected[first_idx].add(second_idx)
        undirected[second_idx].add(first_idx)
        if record.effective_wins_for_first > 0:
            directed[first_idx].add(second_idx)
            reverse[second_idx].add(first_idx)
        if record.effective_wins_for_second > 0:
            directed[second_idx].add(first_idx)
            reverse[first_idx].add(second_idx)

    if dimension_count == 0:
        return True, True

    connected = len(_reachable_nodes(undirected, 0)) == dimension_count
    strongly_connected = connected
    if connected:
        strongly_connected = (
            len(_reachable_nodes(directed, 0)) == dimension_count
            and len(_reachable_nodes(reverse, 0)) == dimension_count
        )
    return connected, strongly_connected


def _center_strengths(strengths: list[float]) -> list[float]:
    mean_log_strength = sum(math.log(value) for value in strengths) / len(strengths)
    scale = math.exp(mean_log_strength)
    return [value / scale for value in strengths]


def fit_bradley_terry_mm(
    effective_wins: list[list[float]],
    contests: list[list[float]],
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> tuple[list[float], int, bool]:
    item_count = len(effective_wins)
    strengths = [1.0] * item_count

    for iteration in range(1, max_iterations + 1):
        next_strengths = [0.0] * item_count
        for item_idx in range(item_count):
            total_wins = sum(effective_wins[item_idx][other_idx] for other_idx in range(item_count) if other_idx != item_idx)
            denominator = 0.0
            for other_idx in range(item_count):
                if other_idx == item_idx or contests[item_idx][other_idx] <= 0:
                    continue
                denominator += contests[item_idx][other_idx] / (strengths[item_idx] + strengths[other_idx])

            if total_wins <= 0 or denominator <= 0:
                raise ValueError(
                    "Bradley-Terry MM update received a non-positive numerator or denominator. "
                    "Check the comparison graph and smoothing configuration."
                )

            next_strengths[item_idx] = total_wins / denominator

        next_strengths = _center_strengths(next_strengths)
        max_delta = max(
            abs(math.log(next_strengths[item_idx]) - math.log(strengths[item_idx]))
            for item_idx in range(item_count)
        )
        strengths = next_strengths
        if max_delta < tolerance:
            return strengths, iteration, True

    return strengths, max_iterations, False


def compute_system_priority(
    value_system: str,
    aggregate: SystemAggregate,
    *,
    smoothing: float,
    tolerance: float,
    max_iterations: int,
) -> dict[str, Any]:
    if smoothing < 0:
        raise ValueError("Smoothing must be non-negative.")

    dimension_names = sorted(aggregate.dimensions.keys())
    if len(dimension_names) < 2:
        raise ValueError(f"Value system {value_system!r} needs at least two value dimensions.")

    index_by_name = {name: idx for idx, name in enumerate(dimension_names)}
    pairwise_records = [aggregate.pairwise[key] for key in sorted(aggregate.pairwise)]
    connected, strongly_connected = _build_graph_flags(pairwise_records, index_by_name, len(dimension_names))
    if not connected:
        raise ValueError(
            f"Value system {value_system!r} is not connected in the observed comparison graph, "
            "so a single Bradley-Terry ranking is not identifiable."
        )
    if smoothing == 0.0 and not strongly_connected:
        raise ValueError(
            f"Value system {value_system!r} is not strongly connected. "
            "Use positive smoothing to obtain finite Bradley-Terry estimates."
        )

    dimension_count = len(dimension_names)
    effective_wins = [[0.0 for _ in range(dimension_count)] for _ in range(dimension_count)]
    contests = [[0.0 for _ in range(dimension_count)] for _ in range(dimension_count)]
    for record in pairwise_records:
        first_idx = index_by_name[record.first]
        second_idx = index_by_name[record.second]
        effective_wins[first_idx][second_idx] = record.effective_wins_for_first + smoothing
        effective_wins[second_idx][first_idx] = record.effective_wins_for_second + smoothing
        contests[first_idx][second_idx] = record.case_count + (2 * smoothing)
        contests[second_idx][first_idx] = record.case_count + (2 * smoothing)

    strengths, iterations, converged = fit_bradley_terry_mm(
        effective_wins,
        contests,
        tolerance=tolerance,
        max_iterations=max_iterations,
    )
    centered_log_strengths = [math.log(strength) for strength in strengths]
    mean_log_strength = sum(centered_log_strengths) / len(centered_log_strengths)
    centered_log_strengths = [value - mean_log_strength for value in centered_log_strengths]
    strengths = [math.exp(value) for value in centered_log_strengths]

    rankings = []
    for name in dimension_names:
        dimension = aggregate.dimensions[name]
        idx = index_by_name[name]
        rankings.append(
            {
                "value_dimension": name,
                "strength_parameter": strengths[idx],
                "log_strength_parameter": centered_log_strengths[idx],
                "case_count": dimension.case_count,
                "raw_wins": dimension.raw_wins,
                "raw_losses": dimension.raw_losses,
                "raw_ties": dimension.raw_ties,
                "effective_wins": dimension.effective_wins,
                "effective_losses": dimension.effective_losses,
            }
        )

    rankings.sort(key=lambda item: (-item["log_strength_parameter"], item["value_dimension"]))
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank

    pairwise_summary = []
    for record in pairwise_records:
        pairwise_summary.append(
            {
                "value_dimension_1": record.first,
                "value_dimension_2": record.second,
                "case_count": record.case_count,
                "raw_wins_for_dimension_1": record.raw_wins_for_first,
                "raw_wins_for_dimension_2": record.raw_wins_for_second,
                "ties": record.ties,
                "effective_wins_for_dimension_1": record.effective_wins_for_first,
                "effective_wins_for_dimension_2": record.effective_wins_for_second,
            }
        )

    return {
        "case_count": aggregate.case_count,
        "dimension_count": dimension_count,
        "comparison_graph": {
            "connected_without_smoothing": connected,
            "strongly_connected_without_smoothing": strongly_connected,
        },
        "solver": {
            "method": "Bradley-Terry MM",
            "converged": converged,
            "iterations": iterations,
            "tolerance": tolerance,
            "smoothing": smoothing,
            "smoothing_scope": "observed_pairs_only",
        },
        "rankings": rankings,
        "pairwise_records": pairwise_summary,
    }


def compute_value_priority_report(
    input_payload: dict[str, Any],
    *,
    input_path: Path | None = None,
    smoothing: float = DEFAULT_SMOOTHING,
    tolerance: float = DEFAULT_TOLERANCE,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> dict[str, Any]:
    cases = input_payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Input JSON must contain a list under the 'cases' key.")

    systems, skipped_reasons = aggregate_case_value_adherence(cases)

    value_systems: dict[str, Any] = {}
    processed_case_count = 0
    for value_system in sorted(systems.keys()):
        system_output = compute_system_priority(
            value_system,
            systems[value_system],
            smoothing=smoothing,
            tolerance=tolerance,
            max_iterations=max_iterations,
        )
        processed_case_count += system_output["case_count"]
        value_systems[value_system] = system_output

    return {
        "metric": "value_priority",
        "source_metric": input_payload.get("metric"),
        "input_file": str(input_path) if input_path is not None else None,
        "input_summary": {
            "case_count": input_payload.get("case_count"),
            "scorable_case_count": input_payload.get("scorable_case_count"),
            "unscorable_case_count": input_payload.get("unscorable_case_count"),
            "max_dimension_score": input_payload.get("max_dimension_score"),
        },
        "estimation": {
            "model": "Bradley-Terry",
            "tie_handling": "each tie counts as 0.5 win for each value dimension",
            "normalization": "log strengths are centered to mean 0 within each value system",
            "smoothing": smoothing,
            "smoothing_scope": "observed_pairs_only",
            "tolerance": tolerance,
            "max_iterations": max_iterations,
        },
        "processed_case_count": processed_case_count,
        "skipped_case_count": sum(skipped_reasons.values()),
        "skipped_case_reasons": dict(sorted(skipped_reasons.items())),
        "value_system_count": len(value_systems),
        "value_systems": value_systems,
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any], *, indent: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=indent)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path, output_path = resolve_paths(args)
    payload = load_json(input_path)
    report = compute_value_priority_report(
        payload,
        input_path=input_path,
        smoothing=args.smoothing,
        tolerance=args.tolerance,
        max_iterations=args.max_iterations,
    )
    write_json(output_path, report, indent=args.indent)
    print(f"Wrote Bradley-Terry value priority report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
