"""Generate Harbor tasks from Agent-ValueBench cases."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapter import AgentValueBenchAdapter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Harbor tasks for Agent-ValueBench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "datasets" / "agent_valuebench",
        help="Directory to write generated tasks (defaults to datasets/agent_valuebench)",
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=None,
        help="Path to case JSON directory (defaults to cases/)",
    )
    parser.add_argument(
        "--env-dir",
        type=Path,
        default=None,
        help="Path to environment directory (defaults to environment/)",
    )
    parser.add_argument(
        "--case-ids",
        nargs="+",
        default=None,
        help="Specific case IDs to generate (e.g., case_00014 case_00015)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of tasks to generate",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== Agent-ValueBench Adapter ===")
    logger.info(f"Output directory: {output_dir.resolve()}")

    adapter = AgentValueBenchAdapter(
        task_dir=output_dir,
        case_dir=args.case_dir,
        env_dir=args.env_dir,
    )
    logger.info(f"Loaded {len(adapter.cases)} cases")

    if args.case_ids:
        count = adapter.generate_tasks_by_ids(args.case_ids)
        logger.info(f"Generated {count} tasks for specified case IDs")
    else:
        cases = adapter.cases
        if args.limit:
            cases = cases[: args.limit]

        count = 0
        for i, case in enumerate(cases):
            local_task_id = adapter.make_local_task_id(case.filename)
            if (i + 1) % 100 == 0 or i == 0:
                logger.info(f"Progress: {i + 1}/{len(cases)} — {local_task_id}")
            adapter.generate_task(case, local_task_id)
            count += 1

        logger.info(f"Generated {count} tasks in: {output_dir}")


if __name__ == "__main__":
    main()
