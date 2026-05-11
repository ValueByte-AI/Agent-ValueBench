from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from CaseGen.batch_case_generation import RUNS_ROOT, show_blocked_slots


def main() -> None:
    parser = argparse.ArgumentParser(description="Show blocked API slots for deterministic batch CaseGen case generation.")
    parser.add_argument("--run_name", type=str, default="default")
    args = parser.parse_args()
    show_blocked_slots(RUNS_ROOT / str(args.run_name).strip())


if __name__ == "__main__":
    main()
