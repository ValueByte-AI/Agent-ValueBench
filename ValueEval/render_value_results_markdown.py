from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDE_MODELS: tuple[str, ...] = ()
DEFAULT_SCORE_DECIMALS = 4
DEFAULT_STRENGTH_DECIMALS = 6


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render markdown (with embedded HTML tables) that aggregates final value adherence "
            "and value priority results from result/<model_name>/."
        )
    )
    parser.add_argument(
        "--result-root",
        type=Path,
        default=Path("result"),
        help="Root directory containing result/<model_name>/ folders (default: result).",
    )
    parser.add_argument(
        "--exclude-models",
        type=str,
        default=",".join(DEFAULT_EXCLUDE_MODELS),
        help=f"Comma-separated model directory names to exclude (default: {','.join(DEFAULT_EXCLUDE_MODELS)}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional markdown output file path. If omitted, only stdout is used.",
    )
    parser.add_argument(
        "--score-decimals",
        type=int,
        default=DEFAULT_SCORE_DECIMALS,
        help=f"Number of decimals for adherence scores (default: {DEFAULT_SCORE_DECIMALS}).",
    )
    parser.add_argument(
        "--strength-decimals",
        type=int,
        default=DEFAULT_STRENGTH_DECIMALS,
        help=f"Number of decimals for priority strength_parameter (default: {DEFAULT_STRENGTH_DECIMALS}).",
    )
    return parser.parse_args(argv)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_exclude_models(raw: str) -> set[str]:
    return {item.strip() for item in str(raw or "").split(",") if item.strip()}


def _discover_model_dirs(result_root: Path, exclude_models: set[str]) -> list[Path]:
    return sorted(
        path
        for path in result_root.iterdir()
        if path.is_dir() and path.name not in exclude_models
    )


def _load_adherence_map(path: Path) -> dict[tuple[str, str], float]:
    if not path.exists():
        return {}
    payload = _load_json(path)
    out: dict[tuple[str, str], float] = {}
    systems = payload.get("systems", {})
    if not isinstance(systems, dict):
        return out
    for value_system, system_payload in systems.items():
        if not isinstance(system_payload, dict):
            continue
        dimensions = system_payload.get("value_dimensions", {})
        if not isinstance(dimensions, dict):
            continue
        for value_dimension, dim_payload in dimensions.items():
            if not isinstance(dim_payload, dict):
                continue
            final_score = dim_payload.get("final_score")
            if final_score is None:
                continue
            out[(str(value_system), str(value_dimension))] = float(final_score)
    return out


def _load_priority_map(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    payload = _load_json(path)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    systems = payload.get("value_systems", {})
    if not isinstance(systems, dict):
        return out
    for value_system, system_payload in systems.items():
        if not isinstance(system_payload, dict):
            continue
        rankings = system_payload.get("rankings", [])
        if not isinstance(rankings, list):
            continue
        for item in rankings:
            if not isinstance(item, dict):
                continue
            value_dimension = item.get("value_dimension")
            rank = item.get("rank")
            strength_parameter = item.get("strength_parameter")
            if value_dimension is None or rank is None or strength_parameter is None:
                continue
            out[(str(value_system), str(value_dimension))] = {
                "rank": int(rank),
                "strength_parameter": float(strength_parameter),
            }
    return out


def _html_escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _key_sort(value_system_and_dimension: tuple[str, str]) -> tuple[str, str]:
    return value_system_and_dimension


def _ordered_dimensions_by_system(
    adherence_by_model: dict[str, dict[tuple[str, str], float]],
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
) -> list[tuple[str, list[str]]]:
    keys = (
        {
            key
            for payload in adherence_by_model.values()
            for key in payload.keys()
        }
        | {
            key
            for payload in priority_by_model.values()
            for key in payload.keys()
        }
    )
    grouped: dict[str, set[str]] = {}
    for value_system, value_dimension in keys:
        grouped.setdefault(value_system, set()).add(value_dimension)
    return [
        (value_system, sorted(value_dimensions))
        for value_system, value_dimensions in sorted(grouped.items())
    ]


def _format_adherence_cell(value: float | None, decimals: int) -> str:
    if value is None:
        return "-"
    return f"{value:.{decimals}f}"


def _format_priority_cell(
    payload: dict[str, Any] | None,
    *,
    strength_decimals: int,
) -> str:
    if payload is None:
        return "-"
    strength = float(payload["strength_parameter"])
    rank = int(payload["rank"])
    return f"{strength:.{strength_decimals}f} / #{rank}"


def _build_table_header(dimensions_by_system: list[tuple[str, list[str]]]) -> str:
    parts: list[str] = []
    parts.append("  <thead>")
    parts.append("    <tr>")
    parts.append('      <th rowspan="2">Model</th>')
    for value_system, dimensions in dimensions_by_system:
        parts.append(f'      <th colspan="{len(dimensions)}">{_html_escape(value_system)}</th>')
    parts.append("    </tr>")
    parts.append("    <tr>")
    for _, dimensions in dimensions_by_system:
        for value_dimension in dimensions:
            parts.append(f"      <th>{_html_escape(value_dimension)}</th>")
    parts.append("    </tr>")
    parts.append("  </thead>")
    return "\n".join(parts)


def _build_adherence_table(
    *,
    model_names: list[str],
    dimensions_by_system: list[tuple[str, list[str]]],
    adherence_by_model: dict[str, dict[tuple[str, str], float]],
    score_decimals: int,
) -> str:
    parts: list[str] = []
    parts.append("## Value Adherence")
    parts.append("")
    parts.append("Cell format: `final_score`.")
    parts.append("")
    parts.append("<table>")
    parts.append(_build_table_header(dimensions_by_system))
    parts.append("  <tbody>")
    for model_name in model_names:
        parts.append("    <tr>")
        parts.append(f"      <td>{_html_escape(model_name)}</td>")
        adherence_map = adherence_by_model.get(model_name, {})
        for value_system, dimensions in dimensions_by_system:
            for value_dimension in dimensions:
                cell = _format_adherence_cell(
                    adherence_map.get((value_system, value_dimension)),
                    score_decimals,
                )
                parts.append(f"      <td>{_html_escape(cell)}</td>")
        parts.append("    </tr>")
    parts.append("  </tbody>")
    parts.append("</table>")
    parts.append("")
    return "\n".join(parts)


def _build_priority_table(
    *,
    model_names: list[str],
    dimensions_by_system: list[tuple[str, list[str]]],
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    strength_decimals: int,
) -> str:
    parts: list[str] = []
    parts.append("## Value Priority")
    parts.append("")
    parts.append("Cell format: `strength_parameter / rank`.")
    parts.append("")
    parts.append("<table>")
    parts.append(_build_table_header(dimensions_by_system))
    parts.append("  <tbody>")
    for model_name in model_names:
        parts.append("    <tr>")
        parts.append(f"      <td>{_html_escape(model_name)}</td>")
        priority_map = priority_by_model.get(model_name, {})
        for value_system, dimensions in dimensions_by_system:
            for value_dimension in dimensions:
                cell = _format_priority_cell(
                    priority_map.get((value_system, value_dimension)),
                    strength_decimals=strength_decimals,
                )
                parts.append(f"      <td>{_html_escape(cell)}</td>")
        parts.append("    </tr>")
    parts.append("  </tbody>")
    parts.append("</table>")
    parts.append("")
    return "\n".join(parts)


def build_markdown_document(
    *,
    model_names: list[str],
    adherence_by_model: dict[str, dict[tuple[str, str], float]],
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    score_decimals: int,
    strength_decimals: int,
) -> str:
    dimensions_by_system = _ordered_dimensions_by_system(adherence_by_model, priority_by_model)
    lines: list[str] = []
    lines.append("# Value Results Summary")
    lines.append("")
    lines.append(
        _build_adherence_table(
            model_names=model_names,
            dimensions_by_system=dimensions_by_system,
            adherence_by_model=adherence_by_model,
            score_decimals=score_decimals,
        ).rstrip()
    )
    lines.append("")
    lines.append(
        _build_priority_table(
            model_names=model_names,
            dimensions_by_system=dimensions_by_system,
            priority_by_model=priority_by_model,
            strength_decimals=strength_decimals,
        ).rstrip()
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result_root = args.result_root.resolve()
    exclude_models = _parse_exclude_models(args.exclude_models)

    if not result_root.is_dir():
        raise ValueError(f"Result root does not exist or is not a directory: {result_root}")

    model_dirs = _discover_model_dirs(result_root, exclude_models)
    if not model_dirs:
        raise ValueError(f"No model directories found under {result_root} after exclusions: {sorted(exclude_models)}")

    model_names = [path.name for path in model_dirs]
    adherence_by_model: dict[str, dict[tuple[str, str], float]] = {}
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}

    for model_dir in model_dirs:
        model_name = model_dir.name
        adherence_by_model[model_name] = _load_adherence_map(model_dir / "system_value_adherence_summary.json")
        priority_by_model[model_name] = _load_priority_map(model_dir / "value_priority_bradley_terry.json")

    markdown = build_markdown_document(
        model_names=model_names,
        adherence_by_model=adherence_by_model,
        priority_by_model=priority_by_model,
        score_decimals=args.score_decimals,
        strength_decimals=args.strength_decimals,
    )

    if args.output is not None:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

    try:
        sys.stdout.write(markdown)
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
