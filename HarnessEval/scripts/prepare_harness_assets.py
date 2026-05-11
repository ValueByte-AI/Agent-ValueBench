#!/usr/bin/env python3
"""Prepare the HarnessEval case subset and environment copy from root assets."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path
from typing import Any


SELECTED_VALUE_SYSTEMS = {"mft08", "vsm13", "nfcc2000"}
PVQ40_CORE_VALUES = {
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
}
ROOT_TOOL_COMBINATORS = ("anyOf", "oneOf", "allOf")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _harness_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _is_selected_case(case_data: dict[str, Any]) -> bool:
    value_system = case_data.get("value_system")
    value_items = case_data.get("value_items") or []

    if value_system in SELECTED_VALUE_SYSTEMS:
        return True

    if value_system != "pvq40":
        return False
    if not isinstance(value_items, list) or len(value_items) != 2:
        return False
    return set(value_items).issubset(PVQ40_CORE_VALUES)


def _reset_dir(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise NotADirectoryError(path)
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_selected_cases(source_dir: Path, output_dir: Path) -> list[str]:
    _reset_dir(output_dir)
    copied: list[str] = []

    for case_path in sorted(source_dir.glob("case_*.json")):
        case_data = _load_json(case_path)
        if not _is_selected_case(case_data):
            continue
        shutil.copy2(case_path, output_dir / case_path.name)
        copied.append(case_path.name)

    if len(copied) != 111:
        raise RuntimeError(f"Expected 111 HarnessEval cases, copied {len(copied)}")
    return copied


def _sanitize_tool_parameter_roots(env_data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    cleaned = copy.deepcopy(env_data)
    changed = False
    tools = cleaned.get("tools")

    if isinstance(tools, list):
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            parameters = tool.get("parameters")
            if not isinstance(parameters, dict):
                continue
            for key in ROOT_TOOL_COMBINATORS:
                if key in parameters:
                    parameters.pop(key, None)
                    changed = True

    return cleaned, changed


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _copy_sanitized_environment(source_dir: Path, output_dir: Path) -> list[str]:
    _reset_dir(output_dir)
    changed_json_files: list[str] = []

    for source_path in sorted(p for p in source_dir.iterdir() if p.is_file()):
        target_path = output_dir / source_path.name

        if source_path.suffix != ".json":
            shutil.copy2(source_path, target_path)
            continue

        env_data = _load_json(source_path)
        cleaned, changed = _sanitize_tool_parameter_roots(env_data)
        if changed:
            _write_json(target_path, cleaned)
            changed_json_files.append(source_path.name)
        else:
            shutil.copy2(source_path, target_path)

    return changed_json_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare HarnessEval cases and environments from root assets.")
    parser.add_argument("--case-source-dir", type=Path, default=_repo_root() / "case")
    parser.add_argument("--environment-source-dir", type=Path, default=_repo_root() / "environment")
    parser.add_argument("--case-output-dir", type=Path, default=_harness_root() / "cases")
    parser.add_argument("--environment-output-dir", type=Path, default=_harness_root() / "environment")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    copied_cases = _copy_selected_cases(args.case_source_dir, args.case_output_dir)
    changed_env_json = _copy_sanitized_environment(args.environment_source_dir, args.environment_output_dir)

    print(f"Prepared {len(copied_cases)} cases -> {args.case_output_dir}")
    print(f"Prepared environment files -> {args.environment_output_dir}")
    print(f"Sanitized root tool schema combinators in {len(changed_env_json)} JSON files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
