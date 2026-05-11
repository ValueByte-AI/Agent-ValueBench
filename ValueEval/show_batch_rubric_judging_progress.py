from __future__ import annotations

import argparse
from pathlib import Path

from .batch_common import watch_progress
from .batch_rubric_judging import RUNS_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch batch ValueEval trajectory judging progress.")
    parser.add_argument("--run_name", type=str, required=True)
    parser.add_argument("--poll_seconds", type=float, default=1.0)
    args = parser.parse_args()
    watch_progress(RUNS_ROOT / Path(str(args.run_name).strip()), poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
