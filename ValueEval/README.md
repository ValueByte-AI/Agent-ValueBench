# ValueEval ⚖️

ValueEval is the scoring and aggregation module for Agent-ValueBench. It takes completed agent trajectories, applies the saved case-specific rubric for each case, and produces the two final value reports used by the benchmark:

- **Value Adherence**: how strongly the model implements each value dimension overall.
- **Value Priority**: which value dimension the model tends to prioritize when two values conflict, estimated with a Bradley-Terry model.

ValueEval does not generate rubrics. It assumes that one rubric file already exists for each case that should be judged.

## What ValueEval Does 🧭

For each model run, the module follows this workflow:

1. **Match files by case id**: align `case_XXXXX.json`, `case_XXXXX_rubric.json`, and `case_XXXXX_traj.json`.
2. **Build a judging prompt**: combine the frozen rubric and the full model trajectory.
3. **Call judge model(s)**: request strict JSON judgments for every rubric item.
4. **Write judge results**: save one result JSON per case.
5. **Compute adherence**: normalize rubric item scores into value-level and system-level scores.
6. **Compute priority**: convert pairwise value wins into Bradley-Terry strength rankings.
7. **Render summaries**: optionally produce markdown tables for reporting.

There are two judging entrypoints:

- **Standard trajectory judging** for trajectories produced by [`TrajGen`](../TrajGen/README.md), the OpenAI-compatible function-calling ReAct runner.
- **Harness trajectory judging** for trajectories exported from [`HarnessEval`](../HarnessEval/README.md), including newer `.json` and `.jsonl` formats.

## Directory Layout 📁

```text
ValueEval/
├── README.md
├── __init__.py
├── run_batch_rubric_judging.py             # Batch judging for standard TrajGen trajectories
├── run_batch_harness_rubric_judging.py     # Batch judging for HarnessEval JSON/JSONL trajectories
├── run_single_judgment.py                  # One-case debugging entrypoint
├── batch_rubric_judging.py                 # Scheduler, resume state, API-slot coordination
├── batch_common.py                         # Shared batch utilities and API error handling
├── rubric_trajectory_judge.py              # Prompt construction, trajectory formatting, validation
├── prompts.py                              # Frozen trajectory-judging prompt template
├── compute_value_adherence.py              # Case/value/system adherence aggregation
├── compute_value_priority.py               # Bradley-Terry value-priority estimation
├── show_batch_rubric_judging_progress.py   # Progress watcher
├── show_batch_rubric_judging_blocked_apis.py # Blocked API-slot inspection
├── render_value_results_markdown.py        # All-model result table renderer
└── render_harness_value_results_markdown.py # Fixed harness experiment table renderer
```

Batch run state is written under:

```text
ValueEval/judge_batch_runs/<run_name>/
```

Final judge result files are written to the directory passed through `--result_output_dir_name`.

## Inputs and File Naming 🔎

ValueEval aligns files by the case stem.

For standard [`TrajGen`](../TrajGen/README.md) trajectories:

```text
case/case_00001.json
rubric/case_00001_rubric.json
result/<model_name>/traj/case_00001_traj.json
```

For [`HarnessEval`](../HarnessEval/README.md) trajectories, the trajectory directory may contain:

```text
result_harness/<model_name>/<harness_name>/case_00001_traj.json
result_harness/<model_name>/<harness_name>/case_00001_traj.jsonl
```

The harness judging entrypoint automatically normalizes supported harness formats into the same internal `steps/tool_calls/tool_responses` structure used by the standard judge.

## Setup 🚀

### 1. Prepare Completed Trajectories

Run one of the trajectory generators first:

- [`TrajGen`](../TrajGen/README.md) for the main OpenAI-compatible function-calling ReAct trajectories.
- [`HarnessEval`](../HarnessEval/README.md) for OpenClaw, Codex, or Claude Code trajectories.

### 2. Prepare Rubrics

Place saved rubric files under a rubric directory:

```text
rubric/case_00001_rubric.json
rubric/case_00002_rubric.json
...
```

Each rubric must correspond to the same case stem as the case file.

### 3. Create an API Slot File

Create a JSON file such as `configs/api_slots.json`. Each slot points to one OpenAI-compatible chat-completions endpoint for the judge model.

```json
{
  "api_slots": [
    {
      "slot_id": "slot_001",
      "name": "judge_slot_001",
      "api_key": "<api_key>",
      "base_url": "<api_url>"
    }
  ]
}
```

You can provide multiple slots to run judging concurrently:

```json
{
  "api_slots": [
    {
      "slot_id": "slot_001",
      "api_key": "<api_key_1>",
      "base_url": "<api_url_1>"
    },
    {
      "slot_id": "slot_002",
      "api_key": "<api_key_2>",
      "base_url": "<api_url_2>"
    }
  ]
}
```

Use the exact model id expected by your endpoint in `--judge_models`.

### 4. Choose Judge Model(s)

`--judge_models` accepts one model id or a comma-separated list:

```text
deepseek-reasoner
model_a,model_b
```

Each listed judge model produces one independent judgment for each case. For the benchmark runs, use deterministic settings such as `--temperature 0.0` and a sufficiently large `--max-tokens` value so the judge can return the full JSON object.

## Standard Trajectory Judging 🧪

Use this for trajectories produced by [`TrajGen`](../TrajGen/README.md):

```bash
python -m TrajGen.run_batch_tir_agent_eval_openai ...
```

Example:

```bash
python -m ValueEval.run_batch_rubric_judging \
  --run_name judge_<model_name> \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir result/<model_name>/traj \
  --result_output_dir_name result/<model_name>/judge_result \
  --judge_models <judge_model_id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4
```

This is the current equivalent of the standard trajectory judging commands used after the main function-calling ReAct runs.

## Harness Trajectory Judging 🧩

Use this for trajectories exported from OpenClaw, Codex, or Claude Code runs through [`HarnessEval`](../HarnessEval/README.md).

Example:

```bash
python -m ValueEval.run_batch_harness_rubric_judging \
  --run_name judge_harness_<model_name>_<harness_name> \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir result_harness/<model_name>/<harness_name> \
  --result_output_dir_name result_harness/<model_name>/<harness_name>/judge_result \
  --judge_models <judge_model_id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4
```

This is the current equivalent of the harness judging commands used for OpenClaw, Codex, Claude Code, and skill-injection harness results.

## Monitor and Resume 📡

Watch progress:

```bash
python -m ValueEval.show_batch_rubric_judging_progress \
  --run_name judge_<model_name>
```

Inspect blocked API slots:

```bash
python -m ValueEval.show_batch_rubric_judging_blocked_apis \
  --run_name judge_<model_name>
```

Resume an interrupted or partially blocked run by rerunning the same judging command with `--resume`:

```bash
python -m ValueEval.run_batch_rubric_judging \
  --run_name judge_<model_name> \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir result/<model_name>/traj \
  --result_output_dir_name result/<model_name>/judge_result \
  --judge_models <judge_model_id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4 \
  --resume
```

Use the same `--run_name`, input directories, and output directory when resuming.

## Compute Value Adherence 📊

After judging completes, compute adherence:

```bash
python -m ValueEval.compute_value_adherence \
  --cases_dir case \
  --rubric_dir rubric \
  --judge_result_dir result/<model_name>/judge_result \
  --max_score 10 \
  --output_dir result/<model_name>
```

Outputs:

```text
result/<model_name>/case_value_adherence_details.json
result/<model_name>/system_value_adherence_summary.json
```

For harness runs, point to the corresponding harness directory:

```bash
python -m ValueEval.compute_value_adherence \
  --cases_dir case \
  --rubric_dir rubric \
  --judge_result_dir result_harness/<model_name>/<harness_name>/judge_result \
  --max_score 10 \
  --output_dir result_harness/<model_name>/<harness_name>
```

## Compute Value Priority 🏆

Compute Bradley-Terry value priority from `case_value_adherence_details.json`:

```bash
python ValueEval/compute_value_priority.py \
  --model-dir result/<model_name>
```

Output:

```text
result/<model_name>/value_priority_bradley_terry.json
```

For harness runs:

```bash
python ValueEval/compute_value_priority.py \
  --model-dir result_harness/<model_name>/<harness_name>
```

## Common Command Recipes 🍱

### Main Function-Calling ReAct Results

```bash
python -m ValueEval.run_batch_rubric_judging \
  --run_name judge_<model_name> \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir result/<model_name>/traj \
  --result_output_dir_name result/<model_name>/judge_result \
  --judge_models <judge_model_id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4

python -m ValueEval.compute_value_adherence \
  --cases_dir case \
  --rubric_dir rubric \
  --judge_result_dir result/<model_name>/judge_result \
  --max_score 10 \
  --output_dir result/<model_name>

python ValueEval/compute_value_priority.py \
  --model-dir result/<model_name>
```

### Harness and Skill-Injection Results

```bash
python -m ValueEval.run_batch_harness_rubric_judging \
  --run_name judge_harness_<model_name>_<harness_name> \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir result_harness/<model_name>/<harness_name> \
  --result_output_dir_name result_harness/<model_name>/<harness_name>/judge_result \
  --judge_models <judge_model_id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4

python -m ValueEval.compute_value_adherence \
  --cases_dir case \
  --rubric_dir rubric \
  --judge_result_dir result_harness/<model_name>/<harness_name>/judge_result \
  --max_score 10 \
  --output_dir result_harness/<model_name>/<harness_name>

python ValueEval/compute_value_priority.py \
  --model-dir result_harness/<model_name>/<harness_name>
```

Use the same recipe for skill-injection results by changing paths, for example:

```text
result_harness_skill_mft08/<model_name>/<harness_name>
result_harness_skill_pvq40_10dims/<model_name>/<harness_name>
```

## Single-Case Debugging 🔬

Use `run_single_judgment.py` when debugging one case:

```bash
python -m ValueEval.run_single_judgment \
  --case-path case/case_00001.json \
  --traj-path result/<model_name>/traj/case_00001_traj.json \
  --rubric-dir rubric \
  --result-dir ValueEval/result \
  --trace-dir ValueEval/result/case_00001_trace \
  --api-key <api_key> \
  --base-url <api_url> \
  --judge-models <judge_model_id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4
```

## Render Markdown Tables 📝

Render all-model results:

```bash
python ValueEval/render_value_results_markdown.py \
  --result-root result \
  --output result/all_model_results.md \
  --score-decimals 4 \
  --strength-decimals 6
```

Render the fixed harness experiment table. This script is intentionally tied to the seven model/harness runs and selected value dimensions used by the HarnessEval comparison:

```bash
python ValueEval/render_harness_value_results_markdown.py \
  --result-root result_harness \
  --output result_harness/all_harness_model_results.md \
  --score-decimals 4 \
  --strength-decimals 6
```

## Argument Reference ⚙️

### Batch Judging Arguments

Used by both `run_batch_rubric_judging.py` and `run_batch_harness_rubric_judging.py`.

| Argument | Required | Description |
| --- | --- | --- |
| `--run_name` | yes | Logical batch name. Runtime state is stored under `ValueEval/judge_batch_runs/<run_name>/`. |
| `--api_slots_json` | yes | JSON file containing one or more API slots. |
| `--cases_dir` | yes | Directory containing case JSON files. |
| `--rubric_dir` | yes | Directory containing saved rubric files named `<case_stem>_rubric.json`. |
| `--traj_dir` | yes | Directory containing trajectory files. |
| `--result_output_dir_name` | yes | Output directory for judge result JSON files. Relative paths are resolved from the parent of `--cases_dir`. |
| `--judge_models` | yes | Comma-separated judge model ids. Each model produces one judgment per case. |
| `--temperature` | no | Judge model sampling temperature. Default: `0.0`. |
| `--max_tokens`, `--max-tokens` | no | Maximum judge-model output tokens. Default: `8000`. |
| `--timeout_seconds`, `--timeout-seconds` | no | Per-request timeout in seconds. Default: `180`. |
| `--network_max_retries`, `--network-max-retries` | no | Network retry count for judge API calls. Default: `2`. |
| `--max_json_retries`, `--max-json-retries` | no | Number of JSON-output repair/retry attempts. Default: `4`. |
| `--resume` | no | Resume an existing run or signal blocked API slots in an active run. |

### Value Adherence Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--cases_dir` | yes | Directory containing the case JSON files used for the judged trajectories. |
| `--rubric_dir` | yes | Directory containing the rubric JSON files. |
| `--judge_result_dir` | yes | Directory containing `case_XXXXX_result.json` judge outputs. |
| `--max_score` | yes | Maximum normalized score for each value dimension, commonly `10`. |
| `--output_dir` | yes | Directory where adherence summary JSON files are written. |

### Value Priority Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--model-dir` | one of `--model-dir` or `--input` | Reads `<model-dir>/case_value_adherence_details.json` and writes `<model-dir>/value_priority_bradley_terry.json`. |
| `--input` | one of `--model-dir` or `--input` | Explicit path to `case_value_adherence_details.json`. |
| `--output` | no | Explicit output JSON path. Defaults next to the input file. |
| `--smoothing` | no | Symmetric pseudo-count for observed value pairs. Default: `0.01`. |
| `--tolerance` | no | Bradley-Terry MM solver convergence tolerance. Default: `1e-12`. |
| `--max-iterations` | no | Maximum solver iterations per value system. Default: `10000`. |
| `--indent` | no | JSON indentation level. Default: `2`. |

### Progress Utility Arguments

| Command | Arguments |
| --- | --- |
| `show_batch_rubric_judging_progress.py` | `--run_name`, optional `--poll_seconds` |
| `show_batch_rubric_judging_blocked_apis.py` | `--run_name` |

### Single-Case Judging Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--case-path` | yes | Path to one case JSON file. |
| `--traj-path` | yes | Path to one standard trajectory JSON file. |
| `--rubric-path` | one of `--rubric-path` or `--rubric-dir` | Explicit rubric JSON path. |
| `--rubric-dir` | one of `--rubric-path` or `--rubric-dir` | Rubric directory used to resolve `<case_stem>_rubric.json`. |
| `--result-dir` | no | Output directory for the single-case result. Default: `ValueEval/result`. |
| `--trace-dir` | no | Optional directory for prompt and raw judge-response traces. |
| `--api-key` | yes | API key for the judge endpoint. |
| `--base-url` | yes | Base URL for the judge endpoint. |
| `--judge-models` | yes | Comma-separated judge model ids. |
| `--temperature` | no | Judge model temperature. Default: `0.0`. |
| `--max-tokens` | no | Maximum judge-model output tokens. Default: `8000`. |
| `--timeout-seconds` | no | Per-request timeout in seconds. Default: `180`. |
| `--network-max-retries` | no | Network retry count. Default: `2`. |
| `--max-json-retries` | no | JSON-output retry count. Default: `4`. |

### Markdown Renderer Arguments

| Renderer | Key arguments |
| --- | --- |
| `render_value_results_markdown.py` | `--result-root`, `--exclude-models`, `--output`, `--score-decimals`, `--strength-decimals` |
| `render_harness_value_results_markdown.py` | `--result-root`, `--output`, `--score-decimals`, `--strength-decimals`; fixed to the HarnessEval comparison model/harness set |

## Notes ✅

- Use `run_batch_rubric_judging.py` for standard [`TrajGen`](../TrajGen/README.md) trajectories.
- Use `run_batch_harness_rubric_judging.py` for [`HarnessEval`](../HarnessEval/README.md) `.json` / `.jsonl` trajectories.
- `--temperature` and `--max-tokens` are the public judging controls.
- Missing case/rubric/trajectory triples are skipped during batch planning rather than stopping the whole run.
- Keep API keys in local config files that are not committed.
