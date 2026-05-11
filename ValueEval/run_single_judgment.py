"""Single-case rubric-based judging CLI."""

from __future__ import annotations

import argparse
import json
from typing import List

from .rubric_trajectory_judge import ValueEvalSettings, RubricTrajectoryJudge


def _parse_models(raw: str) -> List[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Judge one trajectory with a saved rubric")
    parser.add_argument("--case-path", required=True, help="Path to case json")
    parser.add_argument("--traj-path", required=True, help="Path to trajectory json")
    parser.add_argument("--rubric-path", default="", help="Specific rubric file path")
    parser.add_argument("--rubric-dir", default="", help="Rubric dir when --rubric-path is not given")
    parser.add_argument("--result-dir", default="", help="Result output dir (default: ValueEval/result)")
    parser.add_argument("--trace-dir", default="", help="Optional judge trace dir")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--judge-models", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=8000)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--network-max-retries", type=int, default=2)
    parser.add_argument("--max-json-retries", type=int, default=4)

    args = parser.parse_args()
    runner = RubricTrajectoryJudge(
        settings=ValueEvalSettings(
            api_key=args.api_key,
            base_url=args.base_url,
            judge_models=_parse_models(args.judge_models),
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout_seconds=args.timeout_seconds,
            network_max_retries=args.network_max_retries,
            max_json_retries=args.max_json_retries,
        )
    )
    out = runner.judge_with_saved_rubric(
        case_path=args.case_path,
        traj_path=args.traj_path,
        rubric_path=args.rubric_path or None,
        rubric_dir=args.rubric_dir or None,
        result_dir=args.result_dir or None,
        trace_dir=args.trace_dir or None,
    )
    if out is None:
        print("null")
        return 1
    print(json.dumps({"ok": True, "result_path": out["result_path"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
