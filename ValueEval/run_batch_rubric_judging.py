from __future__ import annotations

from pathlib import Path

from .batch_rubric_judging import BatchJudgeCoordinator, JudgeBatchSettings, RUNS_ROOT, _parse_models, build_run_parser


def main() -> int:
    parser = build_run_parser()
    args = parser.parse_args()
    settings = JudgeBatchSettings(
        api_slots_json=Path(args.api_slots_json),
        cases_dir=Path(args.cases_dir),
        rubric_dir=Path(args.rubric_dir),
        traj_dir=Path(args.traj_dir),
        result_output_dir_name=str(args.result_output_dir_name),
        judge_models=_parse_models(args.judge_models),
        temperature=float(args.temperature),
        max_tokens=int(args.max_tokens),
        timeout_seconds=int(args.timeout_seconds),
        network_max_retries=int(args.network_max_retries),
        max_json_retries=int(args.max_json_retries),
        resume=bool(args.resume),
    )
    coordinator = BatchJudgeCoordinator(
        run_dir=RUNS_ROOT / str(args.run_name).strip(),
        settings=settings,
    )
    coordinator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
