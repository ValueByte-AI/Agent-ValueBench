from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from CaseGen.batch_case_generation import RUNS_ROOT, BatchCaseCoordinator, build_run_parser


def main() -> None:
    parser = build_run_parser()
    args = parser.parse_args()
    run_dir = RUNS_ROOT / str(args.run_name).strip()
    coordinator = BatchCaseCoordinator(
        run_dir=run_dir,
        api_slots_path=(ROOT_DIR / args.api_slots_json).resolve() if not Path(args.api_slots_json).is_absolute() else Path(args.api_slots_json),
        case_output_dir=(
            (ROOT_DIR / args.case_output_dir).resolve()
            if not Path(args.case_output_dir).is_absolute()
            else Path(args.case_output_dir)
        ),
        resume=bool(args.resume),
        num_cases=args.num_cases,
        gen_model=args.gen_model,
        check_model=args.check_model,
        stage1_max_tokens=args.stage1_max_tokens,
        stage2_stream_collect=bool(args.stage2_stream_collect),
        stage2_max_tokens=args.stage2_max_tokens,
        stage2_timeout_seconds=args.stage2_timeout_seconds,
        rerun_case_ids_path=(
            (ROOT_DIR / args.rerun_case_ids_txt).resolve()
            if args.rerun_case_ids_txt and not Path(args.rerun_case_ids_txt).is_absolute()
            else (Path(args.rerun_case_ids_txt) if args.rerun_case_ids_txt else None)
        ),
        rerun_env_mode=args.rerun_env_mode,
        rerun_case_env_overrides_path=(
            (ROOT_DIR / args.rerun_case_env_overrides_json).resolve()
            if args.rerun_case_env_overrides_json and not Path(args.rerun_case_env_overrides_json).is_absolute()
            else (Path(args.rerun_case_env_overrides_json) if args.rerun_case_env_overrides_json else None)
        ),
    )
    coordinator.run()


if __name__ == "__main__":
    main()
