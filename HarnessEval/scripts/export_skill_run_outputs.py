#!/usr/bin/env python3
"""Export skill experiment trajectories into Agent-ValueBench result layout."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

HARBOR_CASE_RE = re.compile(r"valuebench-(case-\d{5}|xs-case-\d{5})__")


def normalize_case_id(text: str) -> str:
    return text.replace("valuebench-", "").replace("-", "_")


def export_harbor(job_dir: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for traj_path in sorted(job_dir.glob("*/agent/trajectory.json")):
        match = HARBOR_CASE_RE.match(traj_path.parents[1].name)
        if not match:
            continue
        case_id = normalize_case_id(match.group(1))
        shutil.copy2(traj_path, output_dir / f"{case_id}_traj.json")
        count += 1
    return count


def export_openclaw(result_dir: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for tool_log_path in sorted(result_dir.glob("*/tool_calls.jsonl")):
        case_id = tool_log_path.parent.name
        shutil.copy2(tool_log_path, output_dir / f"{case_id}_traj.jsonl")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["harbor", "openclaw"], required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.kind == "harbor":
        count = export_harbor(args.input_dir, args.output_dir)
    else:
        count = export_openclaw(args.input_dir, args.output_dir)

    print(f"Exported {count} trajectories to {args.output_dir}")


if __name__ == "__main__":
    main()
