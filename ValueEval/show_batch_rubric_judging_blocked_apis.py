from __future__ import annotations

import argparse
from pathlib import Path

from .batch_common import show_blocked_slots
from .batch_rubric_judging import RUNS_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Show blocked API slots for batch ValueEval trajectory judging.")
    parser.add_argument("--run_name", type=str, required=True)
    args = parser.parse_args()
    raise SystemExit(show_blocked_slots(RUNS_ROOT / Path(str(args.run_name).strip())))


if __name__ == "__main__":
    main()
