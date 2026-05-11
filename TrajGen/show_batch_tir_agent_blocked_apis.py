from __future__ import annotations

import argparse
from pathlib import Path

from .batch_tir_agent_eval_openai import RUNS_ROOT, show_blocked_slots


def main() -> None:
    parser = argparse.ArgumentParser(description="Show blocked API slots for batch trajectory generation.")
    parser.add_argument("--run_name", type=str, required=True)
    args = parser.parse_args()
    show_blocked_slots(RUNS_ROOT / Path(str(args.run_name).strip()))


if __name__ == "__main__":
    main()
