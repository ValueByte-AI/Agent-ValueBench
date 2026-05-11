from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from CaseGen.batch_case_generation import RUNS_ROOT, watch_progress


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch deterministic batch CaseGen case generation progress.")
    parser.add_argument("--run_name", type=str, default="default")
    parser.add_argument("--poll_seconds", type=float, default=1.0)
    args = parser.parse_args()
    watch_progress(RUNS_ROOT / str(args.run_name).strip(), poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
