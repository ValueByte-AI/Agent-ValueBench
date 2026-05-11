"""CLI entrypoint for exporting EnvGen metadata to runtime environments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENVGEN_ROOT = Path(__file__).resolve().parents[1]
for path in (PROJECT_ROOT, ENVGEN_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from runtime_export.exporter import run_batch_adapt_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export EnvGen metadata with code-first JSON+PY conversion and runtime smoke"
    )
    parser.add_argument(
        "--source_json",
        type=str,
        default="EnvGen/envgen_pipeline/stage3_refine/final_result/filtered_env_metadata.json",
        help="Source env json path from EnvGen outputs",
    )
    parser.add_argument("--output_env_dir", type=str, default="environment", help="Target environment directory")
    parser.add_argument(
        "--all_envs",
        action="store_true",
        help="Export every env item in the source_json sequentially",
    )
    parser.add_argument("--runtime_timeout_seconds", type=int, default=120, help="Runtime smoke timeout seconds")
    parser.add_argument(
        "--max_adapt_attempts",
        type=int,
        default=1,
        help="Max attempts for each environment export (JSON+PY full pipeline)",
    )
    parser.add_argument(
        "--report_dir",
        type=str,
        default="EnvGen/runtime_export/output",
        help="Where runtime export report json will be saved",
    )

    # Reasoner options: JSON type completion/judge only.
    parser.add_argument(
        "--reasoner_model",
        type=str,
        default="deepseek-reasoner",
        help="Model for type completion + final JSON judge",
    )
    parser.add_argument("--reasoner_temperature", type=float, default=0.0, help="Temperature for reasoner calls")
    parser.add_argument("--reasoner_max_tokens", type=int, default=4096, help="Max tokens for reasoner calls")
    parser.add_argument("--reasoner_max_calls", type=int, default=4, help="Max retries per reasoner call (hard capped at 4)")

    args = parser.parse_args()

    if not args.all_envs:
        parser.error("--all_envs is required; this entrypoint only supports batch export")
    print(
        f"[RUN_ADAPT][BATCH] source_json={args.source_json}, max_adapt_attempts={args.max_adapt_attempts}",
        flush=True,
    )
    summary = run_batch_adapt_pipeline(
        source_json_path=Path(args.source_json),
        output_env_dir=Path(args.output_env_dir),
        runtime_timeout_seconds=args.runtime_timeout_seconds,
        report_dir=Path(args.report_dir),
        max_adapt_attempts=args.max_adapt_attempts,
        reasoner_model=args.reasoner_model,
        reasoner_temperature=args.reasoner_temperature,
        reasoner_max_tokens=args.reasoner_max_tokens,
        reasoner_max_calls=args.reasoner_max_calls,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not bool(summary.get("ok", False)):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
