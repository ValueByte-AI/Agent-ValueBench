from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_SCORE_DECIMALS = 4
DEFAULT_STRENGTH_DECIMALS = 6

TARGET_DIMENSIONS_BY_SYSTEM: list[tuple[str, list[str]]] = [
    ("mft08", ["Authority", "Care", "Fairness", "Loyalty", "Purity"]),
    (
        "nfcc2000",
        [
            "Closed-Mindedness",
            "Decisiveness",
            "Discomfort with Ambiguity",
            "Need for Cognitive Closure",
            "Preference for Order and Structure",
            "Preference for Predictability",
        ],
    ),
    (
        "pvq40",
        [
            "Achievement",
            "Benevolence",
            "Conformity",
            "Hedonism",
            "Power",
            "Security",
            "Self-Direction",
            "Stimulation",
            "Tradition",
            "Universalism",
        ],
    ),
    (
        "vsm13",
        [
            "Collectivism",
            "Femininity",
            "Individualism",
            "Indulgence",
            "Long Term Orientation",
            "Masculinity",
            "Power Distance",
            "Restraint",
            "Short Term Orientation",
            "Uncertainty Avoidance",
        ],
    ),
]

TARGET_MODEL_HARNESS_DIRS: list[tuple[str, str, str]] = [
    ("claude-sonnet-4.6/openclaw", "claude-sonnet-4.6", "openclaw"),
    ("claude-sonnet-4.6/claudecode", "claude-sonnet-4.6", "claudecode"),
    ("gpt-5.4/openclaw", "gpt-5.4", "openclaw"),
    ("gpt-5.4/codex", "gpt-5.4", "codex"),
    ("kimi-k2.5/openclaw", "kimi-k2.5", "openclaw"),
    ("kimi-k2.5/claudecode", "kimi-k2.5", "claudecode"),
    ("kimi-k2.5/codex", "kimi-k2.5", "codex"),
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a harness-only markdown summary matching result/all_model_results.md, "
            "restricted to selected value systems and model/harness runs."
        )
    )
    parser.add_argument(
        "--result-root",
        type=Path,
        default=Path("result_harness"),
        help="Root directory containing result_harness/<model>/<harness>/ folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("result_harness/all_harness_model_results.md"),
        help="Markdown output path.",
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


def _html_escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _format_adherence_cell(value: float | None, decimals: int) -> str:
    if value is None:
        return "-"
    return f"{value:.{decimals}f}"


def _format_priority_cell(payload: dict[str, Any] | None, *, strength_decimals: int) -> str:
    if payload is None:
        return "-"
    strength = float(payload["strength_parameter"])
    rank = int(payload["rank"])
    return f"{strength:.{strength_decimals}f} / #{rank}"


def _load_adherence_map(path: Path) -> dict[tuple[str, str], float]:
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
        for value_dimension, dimension_payload in dimensions.items():
            if not isinstance(dimension_payload, dict):
                continue
            final_score = dimension_payload.get("final_score")
            if final_score is None:
                continue
            out[(str(value_system), str(value_dimension))] = float(final_score)
    return out


def _load_priority_map(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
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


def _build_table_header() -> str:
    parts: list[str] = []
    parts.append("  <thead>")
    parts.append("    <tr>")
    parts.append('      <th rowspan="2">Model</th>')
    for value_system, dimensions in TARGET_DIMENSIONS_BY_SYSTEM:
        parts.append(f'      <th colspan="{len(dimensions)}">{_html_escape(value_system)}</th>')
    parts.append("    </tr>")
    parts.append("    <tr>")
    for _, dimensions in TARGET_DIMENSIONS_BY_SYSTEM:
        for value_dimension in dimensions:
            parts.append(f"      <th>{_html_escape(value_dimension)}</th>")
    parts.append("    </tr>")
    parts.append("  </thead>")
    return "\n".join(parts)


def _build_adherence_table(
    *,
    model_names: list[str],
    adherence_by_model: dict[str, dict[tuple[str, str], float]],
    score_decimals: int,
) -> str:
    parts: list[str] = []
    parts.append("## Value Adherence")
    parts.append("")
    parts.append("Cell format: `final_score`.")
    parts.append("")
    parts.append("<table>")
    parts.append(_build_table_header())
    parts.append("  <tbody>")
    for model_name in model_names:
        parts.append("    <tr>")
        parts.append(f"      <td>{_html_escape(model_name)}</td>")
        adherence_map = adherence_by_model.get(model_name, {})
        for value_system, dimensions in TARGET_DIMENSIONS_BY_SYSTEM:
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
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    strength_decimals: int,
) -> str:
    parts: list[str] = []
    parts.append("## Value Priority")
    parts.append("")
    parts.append("Cell format: `strength_parameter / rank`.")
    parts.append("")
    parts.append("<table>")
    parts.append(_build_table_header())
    parts.append("  <tbody>")
    for model_name in model_names:
        parts.append("    <tr>")
        parts.append(f"      <td>{_html_escape(model_name)}</td>")
        priority_map = priority_by_model.get(model_name, {})
        for value_system, dimensions in TARGET_DIMENSIONS_BY_SYSTEM:
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


def _target_keys() -> set[tuple[str, str]]:
    return {
        (value_system, value_dimension)
        for value_system, dimensions in TARGET_DIMENSIONS_BY_SYSTEM
        for value_dimension in dimensions
    }


def _validate_required_inputs(
    *,
    result_root: Path,
    adherence_by_model: dict[str, dict[tuple[str, str], float]],
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
) -> None:
    target_keys = _target_keys()
    errors: list[str] = []
    for model_name, model_dir_name, harness_name in TARGET_MODEL_HARNESS_DIRS:
        run_dir = result_root / model_dir_name / harness_name
        if not run_dir.is_dir():
            errors.append(f"missing run directory for {model_name}: {run_dir}")
            continue
        for filename in ("system_value_adherence_summary.json", "value_priority_bradley_terry.json"):
            if not (run_dir / filename).is_file():
                errors.append(f"missing {filename} for {model_name}: {run_dir / filename}")
        missing_adherence = sorted(target_keys - set(adherence_by_model.get(model_name, {})))
        missing_priority = sorted(target_keys - set(priority_by_model.get(model_name, {})))
        if missing_adherence:
            errors.append(f"{model_name}: missing adherence cells: {missing_adherence[:8]}")
        if missing_priority:
            errors.append(f"{model_name}: missing priority cells: {missing_priority[:8]}")
    if errors:
        raise ValueError("Input validation failed:\n- " + "\n- ".join(errors))


def build_markdown_document(
    *,
    model_names: list[str],
    adherence_by_model: dict[str, dict[tuple[str, str], float]],
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    score_decimals: int,
    strength_decimals: int,
) -> str:
    lines: list[str] = []
    lines.append("# Value Results Summary")
    lines.append("")
    lines.append(
        _build_adherence_table(
            model_names=model_names,
            adherence_by_model=adherence_by_model,
            score_decimals=score_decimals,
        ).rstrip()
    )
    lines.append("")
    lines.append(
        _build_priority_table(
            model_names=model_names,
            priority_by_model=priority_by_model,
            strength_decimals=strength_decimals,
        ).rstrip()
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result_root = args.result_root.resolve()
    if not result_root.is_dir():
        raise ValueError(f"Result root does not exist or is not a directory: {result_root}")

    model_names: list[str] = []
    adherence_by_model: dict[str, dict[tuple[str, str], float]] = {}
    priority_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}

    for model_name, model_dir_name, harness_name in TARGET_MODEL_HARNESS_DIRS:
        run_dir = result_root / model_dir_name / harness_name
        model_names.append(model_name)
        adherence_path = run_dir / "system_value_adherence_summary.json"
        priority_path = run_dir / "value_priority_bradley_terry.json"
        adherence_by_model[model_name] = _load_adherence_map(adherence_path) if adherence_path.exists() else {}
        priority_by_model[model_name] = _load_priority_map(priority_path) if priority_path.exists() else {}

    _validate_required_inputs(
        result_root=result_root,
        adherence_by_model=adherence_by_model,
        priority_by_model=priority_by_model,
    )

    markdown = build_markdown_document(
        model_names=model_names,
        adherence_by_model=adherence_by_model,
        priority_by_model=priority_by_model,
        score_decimals=args.score_decimals,
        strength_decimals=args.strength_decimals,
    )

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
