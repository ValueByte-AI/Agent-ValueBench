#!/usr/bin/env python3
"""Batch-run agent-valuebench cases through OpenClaw in Docker.

Invokes scripts/run_openclaw.py per case, capturing per-case result JSON to
the chosen results directory. Uses a bounded process pool so cases run in
parallel within Docker.

Usage:
    uv run python scripts/run_openclaw_batch.py --case-ids-file /tmp/target_case_ids.txt
    uv run python scripts/run_openclaw_batch.py --case-ids case_00014 case_00015
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.run_openclaw import (  # noqa: E402
    OPENCLAW_TOOLUSE_CONTINUE_PATCH,
    build_instruction,
    ensure_base_image,
    evaluate_checkpoints,
    load_case,
    prepare_build_context,
)

BASE_IMAGE = "valuebench-openclaw-base"
CASE_DOCKERFILE = f"""\
FROM {BASE_IMAGE}
{OPENCLAW_TOOLUSE_CONTINUE_PATCH}
COPY tool_harness.py /app/tool_harness.py
COPY env_code/ /opt/valuebench/env/
COPY case_config.json /opt/valuebench/case_config.json
COPY .openclaw/ /root/.openclaw/
ENV VALUEBENCH_CONFIG=/opt/valuebench/case_config.json
ENV VALUEBENCH_ENV_DIR=/opt/valuebench/env
"""


def run_case(case_id: str, timeout: int, results_dir: Path, api_base: str, api_key: str, model_id: str) -> dict:
    case_out = results_dir / case_id
    case_out.mkdir(parents=True, exist_ok=True)
    summary_path = case_out / "result.json"

    if summary_path.exists():
        return {"case_id": case_id, "status": "skipped", "reason": "already exists"}

    start = time.time()
    try:
        case = load_case(case_id)
    except Exception as exc:
        return {"case_id": case_id, "status": "error", "error": f"load_case failed: {exc}"}

    try:
        instruction = build_instruction(case)
        ctx = prepare_build_context(case, api_base, api_key, model_id)
    except Exception as exc:
        return {"case_id": case_id, "status": "error", "error": f"prepare failed: {exc}"}

    tag = f"valuebench-openclaw:{case_id.lower().replace('_', '-')}-{os.getpid()}"
    (ctx / "Dockerfile").write_text(CASE_DOCKERFILE)

    tool_log_text = None
    container_name = f"valuebench-oc-{case_id.lower().replace('_', '-')}-{os.getpid()}"

    try:
        build = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            cwd=ctx, capture_output=True, text=True, timeout=180,
        )
        if build.returncode != 0:
            err = build.stderr[-2000:] if build.stderr else ""
            (case_out / "build.err").write_text(err)
            return {
                "case_id": case_id, "status": "error",
                "error": "docker build failed", "stderr_tail": err[-500:],
            }

        logs_dir = ctx / "logs" / "agent"
        logs_dir.mkdir(parents=True, exist_ok=True)

        escaped = instruction.replace("'", "'\\''")
        cmd = f"openclaw agent --local --agent main --message '{escaped}' --json"

        run = subprocess.run(
            ["docker", "run", "--rm", "--name", container_name,
             "-v", f"{ctx}/logs:/logs",
             tag, "bash", "-c", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        (case_out / "agent.stdout").write_text(run.stdout[-20000:] if run.stdout else "")
        (case_out / "agent.stderr").write_text(run.stderr[-20000:] if run.stderr else "")

        log_path = ctx / "logs" / "agent" / "tool_calls.jsonl"
        if log_path.exists():
            tool_log_text = log_path.read_text()
            (case_out / "tool_calls.jsonl").write_text(tool_log_text)

    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        (case_out / "agent.stderr").write_text(f"timeout after {timeout}s")
    except Exception as exc:
        (case_out / "agent.stderr").write_text(f"exception: {exc}")
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
        shutil.rmtree(ctx, ignore_errors=True)

    elapsed = time.time() - start

    try:
        result = evaluate_checkpoints(case, tool_log_text)
    except Exception as exc:
        result = {"error": f"evaluation failed: {exc}"}

    summary = {
        "case_id": case_id,
        "case_name": case.get("case_name"),
        "environment": case.get("environment"),
        "value_system": case.get("value_system"),
        "value_items": case.get("value_items"),
        "elapsed_sec": round(elapsed, 1),
        "result": result,
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    return {"case_id": case_id, "status": "ok", "elapsed_sec": summary["elapsed_sec"]}


def load_case_ids(args) -> list[str]:
    if args.case_ids_file:
        return [ln.strip() for ln in Path(args.case_ids_file).read_text().splitlines() if ln.strip()]
    if args.case_ids:
        return list(args.case_ids)
    raise SystemExit("need --case-ids-file or --case-ids")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-ids-file", type=Path)
    p.add_argument("--case-ids", nargs="+")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--n-concurrent", type=int, default=4)
    p.add_argument("--results-dir", type=Path, default=REPO_ROOT / "results" / "openclaw")
    p.add_argument("--job-name", type=str, default="targets-447")
    args = p.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    api_base = os.environ.get("OPENAI_API_BASE", "")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model_id = os.environ.get("MODEL_ID", "")

    if not (api_base and api_key and model_id):
        raise SystemExit("missing one of OPENAI_API_BASE/OPENAI_API_KEY/MODEL_ID in .env")

    if not ensure_base_image():
        raise SystemExit("base image unavailable")

    case_ids = load_case_ids(args)
    jobs_dir: Path = args.results_dir / args.job_name
    jobs_dir.mkdir(parents=True, exist_ok=True)
    print(f"[batch] running {len(case_ids)} cases, n_concurrent={args.n_concurrent}, timeout={args.timeout}s")
    print(f"[batch] results -> {jobs_dir}")

    started = time.time()
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.n_concurrent) as pool:
        futures = {
            pool.submit(run_case, cid, args.timeout, jobs_dir, api_base, api_key, model_id): cid
            for cid in case_ids
        }
        for fut in concurrent.futures.as_completed(futures):
            cid = futures[fut]
            try:
                info = fut.result()
            except Exception as exc:
                info = {"case_id": cid, "status": "error", "error": str(exc)}
            completed += 1
            elapsed_total = time.time() - started
            print(f"[{completed}/{len(case_ids)}] {cid}: {info.get('status')} "
                  f"(case elapsed {info.get('elapsed_sec','?')}s, total {elapsed_total:.0f}s)",
                  flush=True)

    # Final aggregation
    agg_path = jobs_dir / "aggregate.jsonl"
    summaries = []
    for cid in case_ids:
        r = jobs_dir / cid / "result.json"
        if r.exists():
            try:
                summaries.append(json.loads(r.read_text()))
            except Exception:
                pass
    agg_path.write_text("\n".join(json.dumps(s) for s in summaries) + ("\n" if summaries else ""))
    print(f"[batch] wrote aggregate with {len(summaries)} results to {agg_path}")


if __name__ == "__main__":
    main()
