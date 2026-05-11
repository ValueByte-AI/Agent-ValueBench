# CaseGen 🧩

CaseGen builds executable value-conflict cases for Agent-ValueBench. It takes adapted environments from `environment/`, value definitions from `configs/value_systems.json`, and produces flat case JSON files such as `case_00001.json`.

The batch pipeline is designed for large-scale generation. It creates a deterministic plan over value-system pairs, assigns environments in round-robin order, runs two LLM generation stages, and keeps only cases that pass environment consistency checks plus an independent quality gate.

## Pipeline Overview ✨

Case generation has three main phases:

1. **Stage 1: conflict draft generation**
   - Selects one value system and one unordered pair of values.
   - Selects an adapted environment and exposes its task-facing tools, initial-parameter schema, and tool-state dependencies.
   - Asks the generation model to draft a natural operational task scenario, value-specific checkpoint lists, and the high-level conflict structure.
   - Does not initialize concrete environment state values yet.

2. **Stage 2: executable case realization**
   - Refines the Stage 1 draft into the final case schema.
   - Fills `task_description`, `env_initial_parameters`, `function_list`, `value_a_checkpoint_list`, and `value_b_checkpoint_list`.
   - Uses the environment schema to keep tool names, state fields, and initial parameters executable.
   - Supports streamed collection for long outputs with `--stage2_stream_collect`.

3. **Quality gate**
   - Runs deterministic environment-alignment checks against the selected environment.
   - Runs an LLM-as-a-judge case validation prompt.
   - Runs additional rule-based checks for required fields, value-label leakage, and structural validity.
   - If any check fails, the pipeline retries the case attempt. Successful cases are written to the final output directory as flat `case_*****.json` files.

Value definitions are read from `configs/value_systems.json` and passed to generation and judge prompts. They are not embedded as separate definition fields in the final case JSON files.

## Directory Layout 📁

```text
CaseGen/
├── README.md
├── run_batch_case_generation.py        # CLI entrypoint
├── batch_case_generation.py            # multi-API scheduler and batch orchestration
├── module1_case_generator.py           # single-case generation helpers and schema checks
├── module2_case_validator.py           # LLM judge plus deterministic rule checks
├── show_batch_case_progress.py         # inspect active/completed batch progress
├── show_batch_case_blocked_apis.py     # inspect API slots blocked by auth/quota/unknown errors
├── prompts/
│   ├── stage1_case_prompt.py           # Stage 1 draft prompt builder
│   ├── stage2_case_prompt.py           # Stage 2 executable-case prompt builder
│   └── case_task_validation_prompt.py  # quality-gate judge prompt builder
└── case_batch_runs/
    └── <run_name>/                     # generated run state, attempts, prompts, logs, and metadata
```

The final generated cases are written to `--case_output_dir`, not nested inside `case_batch_runs/`.

## Inputs ✅

Before running CaseGen, make sure these project-level inputs exist:

- `environment/`: adapted environment pairs, one `<EnvName>.json` plus one `<EnvName>.py` per environment.
- `configs/value_systems.json`: value systems, value names, and authoritative value definitions.
- `configs/value_pair_skip_rules.json`: optional value-pair skip rules used while building the deterministic case plan.
- an API slot config file, for example `configs/api_slots.json`.

## API Slot Configuration 🔑

Create `configs/api_slots.json` using the same shared API slot format used by the other Agent-ValueBench modules.

Minimal format for any OpenAI-compatible Chat Completions endpoint:

```json
[
  {
    "name": "slot_001",
    "api_key": "YOUR_API_KEY",
    "base_url": "YOUR_API_URL"
  }
]
```

You can also provide separate generation and checking credentials:

```json
{
  "api_slots": [
    {
      "slot_id": "slot_001",
      "name": "gen-and-check-001",
      "gen_api_key": "YOUR_GENERATION_API_KEY",
      "gen_base_url": "YOUR_GENERATION_API_URL",
      "check_api_key": "YOUR_CHECKING_API_KEY",
      "check_base_url": "YOUR_CHECKING_API_URL"
    }
  ]
}
```

Each slot can work independently. More slots allow more cases to run concurrently.

## Quick Start 🚀

1. **Prepare adapted environments**

   Generate or place adapted environment files under `environment/`. Each environment must have both `<EnvName>.json` and `<EnvName>.py`.

2. **Prepare value systems**

   Confirm that `configs/value_systems.json` contains the value systems and definitions you want to generate cases for.

3. **Create API slots**

   Create `configs/api_slots.json` using the format above. Do not commit real API keys to a public repository.

4. **Choose models**

   - `--gen_model` is used for Stage 1 and Stage 2 case generation.
   - `--check_model` is used for the independent LLM quality gate.

   Recommended configuration: use `gemini-3.1-pro-preview` for `--gen_model` and `gemini-3-flash-preview` for `--check_model`.

   Use the exact model IDs required by your configured endpoint. CaseGen passes the model string through unchanged.

5. **Run generation**

   ```bash
   python CaseGen/run_batch_case_generation.py \
     --run_name formal \
     --api_slots_json configs/api_slots.json \
     --case_output_dir case \
     --gen_model <generation-model-id> \
     --check_model <judge-model-id> \
     --stage2_stream_collect \
     --stage2_max_tokens 12000 \
     --stage2_timeout_seconds 600
   ```

6. **Monitor progress**

   ```bash
   python CaseGen/show_batch_case_progress.py --run_name formal
   python CaseGen/show_batch_case_blocked_apis.py --run_name formal
   ```

7. **Resume if interrupted**

   ```bash
   python CaseGen/run_batch_case_generation.py \
     --run_name formal \
     --api_slots_json configs/api_slots.json \
     --case_output_dir case \
     --gen_model <generation-model-id> \
     --check_model <judge-model-id> \
     --stage2_stream_collect \
     --stage2_max_tokens 12000 \
     --stage2_timeout_seconds 600 \
     --resume
   ```

## Common Runs 🛠️

Generate only a small number of successful cases for a smoke test:

```bash
python CaseGen/run_batch_case_generation.py \
  --run_name smoke_8 \
  --api_slots_json configs/api_slots.json \
  --num_cases 8 \
  --case_output_dir case_smoke_8 \
  --gen_model <generation-model-id> \
  --check_model <judge-model-id> \
  --stage2_stream_collect \
  --stage2_max_tokens 12000 \
  --stage2_timeout_seconds 600
```

Rerun selected formal case IDs while preserving their value pairs:

```bash
python CaseGen/run_batch_case_generation.py \
  --run_name rerun_selected \
  --api_slots_json configs/api_slots.json \
  --case_output_dir case_rerun_selected \
  --gen_model <generation-model-id> \
  --check_model <judge-model-id> \
  --stage2_stream_collect \
  --stage2_max_tokens 12000 \
  --stage2_timeout_seconds 600 \
  --rerun_case_ids_txt selected_case_ids.txt \
  --rerun_env_mode random
```

## Outputs 📦

Final accepted cases:

```text
<case_output_dir>/
├── case_00001.json
├── case_00002.json
└── ...
```

Run artifacts:

```text
CaseGen/case_batch_runs/<run_name>/
├── plan.json              # deterministic case plan
├── run_state.json         # per-case status
├── api_slots_state.json   # slot assignment and blocked-slot state
├── master_events.jsonl    # scheduler events
└── cases/
    └── <case_id>/
        └── attempt_01/
            ├── stage1_case.json
            ├── stage1_meta.json
            ├── stage2_case.json
            ├── stage2_meta.json
            ├── env_consistency.json
            ├── judge_meta.json
            └── judge_result.json
```

These artifacts are useful for debugging prompt outputs, parser retries, rejected cases, and blocked API slots.

## CLI Reference ⚙️

| Argument | Required | Default | Description |
| --- | --- | --- | --- |
| `--run_name` | No | `default` | Logical run name. Run state is stored in `CaseGen/case_batch_runs/<run_name>/`. |
| `--api_slots_json` | Yes | none | Path to the API slot config. Relative paths are resolved from the project root. |
| `--resume` | No | `False` | Resume an existing run and reuse completed artifacts where possible. |
| `--num_cases` | No | all planned cases | Stop after this many new successful cases. Useful for smoke tests. |
| `--case_output_dir` | No | `case` | Directory for final accepted cases. Files are flat and named `case_*****.json`. |
| `--gen_model` | Yes | none | Model used for Stage 1 and Stage 2 generation. |
| `--check_model` | Yes | none | Model used for the LLM-as-a-judge quality gate. |
| `--stage1_max_tokens` | No | project default | Max tokens for Stage 1 generation. |
| `--stage2_stream_collect` | No | `False` | Use streaming collection for Stage 2, recommended for long case JSON outputs. |
| `--stage2_max_tokens` | No | `12000` | Max tokens for Stage 2 generation. |
| `--stage2_timeout_seconds` | No | `600` | Timeout for Stage 2 stream collection. |
| `--rerun_case_ids_txt` | No | none | Text file of case IDs to rerun from `CaseGen/case_batch_runs/formal/plan.json`. |
| `--rerun_env_mode` | No | `random` | For reruns, choose `random` to retry on a new random environment or `source` to keep the original environment. |
| `--rerun_case_env_overrides_json` | No | none | Optional JSON object mapping case IDs to fixed environment names. Overrides `--rerun_env_mode` for listed cases. |

## Notes 🧠

- Case IDs are assigned by the deterministic plan, for example `case_00001`.
- The formal plan iterates through all unordered value pairs in `configs/value_systems.json`, subject to `configs/value_pair_skip_rules.json`.
- The same `case_id` always refers to the same planned value-system/value-pair position for the same value-system config and skip-rule config.
- Failed attempts stay in `CaseGen/case_batch_runs/<run_name>/` for inspection, but only accepted cases are written to `--case_output_dir`.
