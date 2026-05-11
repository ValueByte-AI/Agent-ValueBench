from __future__ import annotations

from pathlib import Path

from .batch_tir_agent_eval_openai import BatchTrajectoryCoordinator, RUNS_ROOT, TrajectoryBatchSettings, build_run_parser


def main() -> int:
    parser = build_run_parser()
    args = parser.parse_args()
    settings = TrajectoryBatchSettings(
        api_slots_json=Path(args.api_slots_json),
        cases_dir=Path(args.cases_dir),
        traj_output_dir_name=str(args.traj_output_dir_name),
        eval_model=str(args.eval_model),
        max_steps=int(args.max_steps),
        temperature=float(args.temperature),
        max_tokens=int(args.max_tokens),
        timeout_seconds=int(args.timeout_seconds),
        network_max_retries=int(args.network_max_retries),
        parallel_tool_calls=None if args.parallel_tool_calls is None else bool(args.parallel_tool_calls),
        n=None if args.n is None else int(args.n),
        tool_choice=str(args.tool_choice),
        resume=bool(args.resume),
    )
    coordinator = BatchTrajectoryCoordinator(
        run_dir=RUNS_ROOT / str(args.run_name).strip(),
        settings=settings,
    )
    coordinator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
