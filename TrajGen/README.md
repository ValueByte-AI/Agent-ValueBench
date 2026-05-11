# TrajGen 🧭

TrajGen runs Agent-ValueBench cases with an OpenAI-compatible function-calling ReAct agent. It loads each case, exposes only the tools listed by that case, lets the model interact with the sandbox environment, and writes a structured trajectory for later value judging.

## Overview ✨

For each case, TrajGen performs the following workflow:

1. **Case discovery**: scan `--cases_dir` for case JSON files, skipping temporary files and rejecting duplicate `case_id` values.
2. **Batch planning**: build a stable run plan and store runtime state under `TrajGen/traj_batch_runs/<run_name>/`.
3. **API slot scheduling**: load one or more OpenAI-compatible API slots from `--api_slots_json` and assign cases across slots.
4. **Environment initialization**: initialize the case environment from `env_initial_parameters`.
5. **Tool exposure**: expose only the case's `function_list` as native function-calling tools.
6. **Agent execution**: run the model in a ReAct loop until it finishes, reaches `--max_steps`, or fails with a recoverable/non-recoverable error.
7. **Trajectory writing**: write final trajectories to `--traj_output_dir_name`; keep logs, temporary trajectories, and retry state in `TrajGen/traj_batch_runs/`.

The batch state directory and the final trajectory directory are intentionally separate:

- `TrajGen/traj_batch_runs/<run_name>/`: runtime state, progress, slot status, traces, and temporary attempt files.
- `result/${MODEL_NAME}/traj/`: final trajectory JSON files used by the judging pipeline.

## Directory Structure 📁

```text
TrajGen/
├── README.md
├── __init__.py
├── batch_tir_agent_eval_openai.py        # Batch scheduler, resume logic, API slot handling
├── run_batch_tir_agent_eval_openai.py    # Main CLI entrypoint
├── tir_agent_eval_openai.py              # Single-case runner and prompt construction
├── tir_agent_openai.py                   # OpenAI-compatible tool-calling ReAct loop
├── show_batch_tir_agent_progress.py      # Progress viewer for a batch run
├── show_batch_tir_agent_blocked_apis.py  # Blocked API slot viewer
├── continue_split_choice_traj_openai.py  # Single-case split-choice continuation utility
├── batch_continue_split_choice_traj_openai.py
└── traj_batch_runs/                      # Runtime state, generated locally and gitignored
```

## Quick Start 🚀

### 1. Prepare Cases and Environments

Run from the repository root. The standard layout is:

```text
Agent-ValueBench/
├── case/
├── environment/
├── configs/
└── TrajGen/
```

Use [`EnvGen`](../EnvGen/README.md) to build runtime environments, then use [`CaseGen`](../CaseGen/README.md) to generate value-conflict cases.

Each case JSON must include the fields needed by the runner, especially:

- `case_id`
- `environment`
- `task_description`
- `env_initial_parameters`
- `function_list`

The corresponding environment implementation must be available under `environment/`.

### 2. Create an API Slot File

Create a JSON file such as `configs/api_slots.json`. Each slot points to one OpenAI-compatible chat completions endpoint that supports native tool/function calling.

```json
{
  "api_slots": [
    {
      "slot_id": "slot_001",
      "name": "primary",
      "api_key": "YOUR_API_KEY",
      "base_url": "YOUR_API_URL"
    },
    {
      "slot_id": "slot_002",
      "name": "backup",
      "api_key": "YOUR_SECOND_API_KEY",
      "base_url": "YOUR_SECOND_API_URL"
    }
  ]
}
```

Use as many slots as your endpoint and quota allow. More slots increase concurrency. Do not commit real API keys.

### 3. Choose the Model

Set `--eval_model` to the model identifier expected by your endpoint. TrajGen passes this string through unchanged.

In commands, use `MODEL_NAME` as a filesystem-friendly label for paths and `MODEL_ID` as the exact API model identifier.

### 4. Run Batch Trajectory Generation

```bash
MODEL_NAME="your_model_name"
MODEL_ID="your-model-id"

python -m TrajGen.run_batch_tir_agent_eval_openai \
  --run_name "traj_${MODEL_NAME}" \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --traj_output_dir_name "result/${MODEL_NAME}/traj" \
  --eval_model "${MODEL_ID}" \
  --max_steps 50 \
  --temperature 0.0 \
  --max_tokens 12000 \
  --timeout_seconds 600 \
  --network_max_retries 2 \
  --tool_choice auto
```

This creates runtime state at:

```text
TrajGen/traj_batch_runs/traj_${MODEL_NAME}/
```

and final trajectories at:

```text
result/${MODEL_NAME}/traj/
```

### 5. Monitor Progress

```bash
python -m TrajGen.show_batch_tir_agent_progress \
  --run_name "traj_${MODEL_NAME}"
```

To inspect blocked API slots:

```bash
python -m TrajGen.show_batch_tir_agent_blocked_apis \
  --run_name "traj_${MODEL_NAME}"
```

### 6. Resume a Run

If a run was interrupted or some API slots were blocked, rerun the same command with `--resume`:

```bash
MODEL_NAME="your_model_name"
MODEL_ID="your-model-id"

python -m TrajGen.run_batch_tir_agent_eval_openai \
  --run_name "traj_${MODEL_NAME}" \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --traj_output_dir_name "result/${MODEL_NAME}/traj" \
  --eval_model "${MODEL_ID}" \
  --max_steps 50 \
  --temperature 0.0 \
  --max_tokens 12000 \
  --timeout_seconds 600 \
  --network_max_retries 2 \
  --tool_choice auto \
  --resume
```

Use the same `--run_name`, `--cases_dir`, and `--traj_output_dir_name` when resuming. If you want an independent run, choose a new `--run_name` and output directory.

## Argument Reference ⚙️

### Required Arguments

| Argument | Description |
| --- | --- |
| `--run_name` | Logical batch name. Runtime state is stored under `TrajGen/traj_batch_runs/<run_name>/`. |
| `--api_slots_json` | Path to the API slot configuration JSON. |
| `--cases_dir` | Directory containing case JSON files. Flat and nested layouts are both supported. |
| `--traj_output_dir_name` | Final trajectory output directory. This is resolved as a sibling path relative to `--cases_dir`'s parent. |
| `--eval_model` | Model identifier passed to the OpenAI-compatible endpoint. |

### Core Generation Arguments

| Argument | Default | Description |
| --- | ---: | --- |
| `--max_steps` | `30` | Maximum ReAct steps per case. The main benchmark runs commonly use `50`. |
| `--temperature` | `0.0` | Sampling temperature for trajectory generation. Use `0.0` for deterministic benchmark runs. |
| `--max_tokens` | `12000` | Maximum tokens requested for each model response. |
| `--timeout_seconds` | `180` | Per-request network timeout in seconds. The main benchmark examples pass `600` explicitly. |
| `--network_max_retries` | `2` | Number of retry attempts for transient network errors. |
| `--tool_choice` | `auto` | Tool choice passed to the model API. Common values are `auto`, `required`, and `none`, depending on endpoint support. |
| `--parallel_tool_calls` | unset | Optional `0` or `1`. When set, explicitly disables or enables parallel tool calls if the endpoint supports the parameter. |
| `--n` | unset | Optional explicit choices count for GPT-family models. TrajGen sends this parameter only when the final slash-separated segment of the model identifier starts with `gpt`. It was added to make requests such as `--n 1` explicit when an endpoint unexpectedly returns multiple `choices`; it is not a guarantee that every endpoint will return exactly one choice. TrajGen still treats responses with more than one choice as invalid for the main runner, and the split-choice continuation utility handles the known strict text-choice/tool-choice failure mode. |

### Runtime Control

| Argument | Description |
| --- | --- |
| `--resume` | Continue an existing run or signal blocked slots in an active run. |

## Optional Split-Choice Continuation 🛠️

Some OpenAI-compatible endpoints may return a split response where one choice contains only text and another choice contains the corresponding tool call. The continuation utilities merge that strict pattern and continue the affected cases.

For one case:

```bash
python -m TrajGen.continue_split_choice_traj_openai \
  --run_name "traj_${MODEL_NAME}" \
  --case_id case_00001 \
  --output_traj_root "result/${MODEL_NAME}/traj"
```

For a batch of affected cases:

```bash
python -m TrajGen.batch_continue_split_choice_traj_openai \
  --source_run_name "traj_${MODEL_NAME}" \
  --run_name "split_choice_continue_${MODEL_NAME}" \
  --api_slots_json configs/api_slots.json \
  --traj_output_dir_name "result/${MODEL_NAME}/traj" \
  --case_ids_file split_choice_cases.txt
```

Use this only for the strict split-choice failure mode; normal interrupted runs should use `--resume`.

## Output Format 📦

Each final trajectory JSON includes:

- case metadata and task description
- exposed tool schema
- OpenAI-compatible tool mode metadata
- final status and final answer
- full step list with assistant outputs, tool calls, and tool responses
- raw and normalized trajectory text for downstream judging

For flat cases such as `case/case_00001.json`, the final file is written as:

```text
result/${MODEL_NAME}/traj/case_00001_traj.json
```

Nested case directories are preserved under the output root.
