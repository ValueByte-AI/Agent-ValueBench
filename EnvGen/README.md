# EnvGen

EnvGen is the environment-generation pipeline used by **Agent-ValueBench**. It turns tool-use task corpora into executable, stateful sandbox environments that can later be paired with value-conflict cases and agent trajectories.

At a high level, EnvGen follows a three-stage workflow:

1. 🔎 **Env Discovery** collects source tasks, keeps tasks that require
   tool-mediated state, and abstracts them into candidate environment themes.
2. 🧩 **Env Synthesis** converts each theme into a structured environment
   specification, tool interface, and executable Python implementation.
3. 🛠️ **Env Evolution** stress-tests each synthesized environment with
   diagnostic rollouts, identifies implementation failures, repairs the code
   when enabled, and exports validated environments.

After evolution, EnvGen can export accepted metadata into the runtime format used by Agent-ValueBench: one readable `<EnvName>.json` schema file and one executable `<EnvName>.py` file per environment.

The pipeline is designed for OpenAI-compatible APIs. It supports both a single API profile and sharded multi-profile execution for higher-throughput runs.

---

## 📁 Directory Structure

```text
EnvGen/
├── run_env_generation.py                  # Unified runner for all stages
├── configs/
│   ├── multi_api_profiles.json            # Local multi-API profile template
│   └── multi_api_profiles.example.json    # Example profile structure
├── runtime_export/
│   ├── run_adapt.py                       # Export stage-3 metadata to runtime files
│   ├── exporter.py                        # JSON export, LLM review, Python wrapping
│   └── export_helpers.py                  # Deterministic helpers and runtime smoke
├── envgen_pipeline/
│   ├── stage1_env_discovery/
│   │   ├── step1_source_corpus_aggregation.py
│   │   ├── step2_environment_theme_pool_construction.py
│   │   ├── step3_clustering_deduplication.py
│   │   └── source_data/                   # Local source task corpora
│   ├── stage2_env_synthesis/
│   │   ├── step1_state_deduction.py
│   │   ├── step2_interface_design.py
│   │   ├── step3_program_synthesis.py
│   │   └── analysis_env_src/              # Program parsing utilities
│   ├── stage3_refine/
│   │   ├── step1_prepare_init_configs.py
│   │   ├── step2_baseline_roll_check.py
│   │   ├── step3_build_bug_ledger.py
│   │   ├── step4_repair_loop.py
│   │   ├── step5_finalize_outputs.py
│   │   ├── refine_agents.py
│   │   ├── refine_utils.py
│   │   └── run_stage3_refine.py
│   └── utils/                             # LLM calls, sharding, recovery
└── README.md
```

Generated files are written to each stage's `temp_result/` and `final_result/` directories.

---

## 🧭 Pipeline Overview

### Stage 1: Env Discovery

**Goal:** identify environment themes from raw source tasks.

Stage 1 runs in three steps:

1. **Source corpus aggregation**
   - Loads tasks from local corpora, a custom JSON file, or one inline task.
   - Optionally deduplicates tasks within each corpus and across corpora.
   - Writes a normalized list of `{task, task_from}` records.

2. **Environment theme pool construction**
   - Uses an LLM judge to filter for tasks that require stateful tool use.
   - Uses an LLM topic model to infer an environment theme, summary, and
     introduction from each retained task.

3. **Clustering and deduplication**
   - Optionally embeds environment summaries.
   - Filters themes by modelability and usefulness scores.
   - Optionally clusters themes and keeps representative candidates.
   - Exports the final discovered environment theme list.

Default dataset mode aggregates these six corpora from `envgen_pipeline/stage1_env_discovery/source_data/`:

- API-Bank
- ToolACE
- ToolBench-5000
- ToolAlpaca
- AgentHarm
- Agent-SafetyBench

### Stage 2: Env Synthesis

**Goal:** synthesize executable environment implementations from discovered themes.

Stage 2 runs in three steps:

1. **State deduction**
   - Infers the environment state schema from each discovered theme.
   - Builds a Python state scaffold for the inferred schema.

2. **Interface design**
   - Designs tool/function interfaces that expose controlled operations over
     the state.
   - Produces function names, descriptions, arguments, and return conventions.

3. **Program synthesis**
   - Synthesizes operation code for the designed interfaces.
   - Assembles state scaffolds and operation code into complete programs.
   - Runs lightweight program analysis before writing the synthesized
     environment list.

### Stage 3: Env Evolution

**Goal:** validate and improve synthesized environments through execution.

Stage 3 is implemented under `envgen_pipeline/stage3_refine/` and contains:

1. **Initialization config preparation**
   - Generates environment initialization configurations for rollout tests.

2. **Baseline rollout check**
   - Executes diagnostic rollouts and records pass/fail information.

3. **Bug ledger construction**
   - Aggregates failures and identifies high-impact functions to repair.

4. **Repair loop**
   - Applies surgical LLM patches when `--evolution_enable_llm_patch` is set.
   - Re-runs checks after each repair round.

5. **Finalization**
   - Keeps environments whose pass rate meets the configured threshold.
   - Writes accepted environments, repair queues, and repair reports.

---

## 🚀 Quick Start

### 1. Create a Python 3.11 environment

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

If you use Conda:

```bash
conda create -n agent-valuebench python=3.11
conda activate agent-valuebench
python -m pip install --upgrade pip
```

Then install the root dependencies:

```bash
pip install -r requirements.txt
```

Then enter the EnvGen module directory for the remaining commands in this README:

```bash
cd EnvGen
```

### 2. Check source corpora

For the default dataset mode, source files should already be present under:

```text
envgen_pipeline/stage1_env_discovery/source_data/
```

You can also bypass the bundled corpora with `--task_source file` or `--task_source inline`.

### 3. Configure API credentials

EnvGen uses OpenAI-compatible chat and embedding APIs.

First set the default single-API profile. Some EnvGen steps run outside the sharded multi-profile dispatcher, including early Env Discovery filtering, so they read `VALUEBENCH_API_KEY` / `VALUEBENCH_BASE_URL` or `OPENAI_API_KEY` / `OPENAI_BASE_URL` directly. Runtime export also uses this single-API profile for narrow JSON schema type completion and final JSON review.

```bash
export VALUEBENCH_API_KEY="YOUR_API_KEY"
export VALUEBENCH_BASE_URL="YOUR_API_URL"
```

`OPENAI_API_KEY` and `OPENAI_BASE_URL` are also accepted. If these default variables are missing, EnvGen may fail during early discovery with an error such as `Missing API key. Set OPENAI_API_KEY, VALUEBENCH_API_KEY, or provide api_key_env in the multi-API profile config.`

For multi-profile execution, also use `configs/multi_api_profiles.json`. The default file contains five profiles that read credentials from environment variables:

```bash
export ENVGEN_API_KEY_1="YOUR_API_KEY_1"
export ENVGEN_BASE_URL_1="YOUR_API_URL_1"

export ENVGEN_API_KEY_2="YOUR_API_KEY_2"
export ENVGEN_BASE_URL_2="YOUR_API_URL_2"

export ENVGEN_API_KEY_3="YOUR_API_KEY_3"
export ENVGEN_BASE_URL_3="YOUR_API_URL_3"

export ENVGEN_API_KEY_4="YOUR_API_KEY_4"
export ENVGEN_BASE_URL_4="YOUR_API_URL_4"

export ENVGEN_API_KEY_5="YOUR_API_KEY_5"
export ENVGEN_BASE_URL_5="YOUR_API_URL_5"
```

If you run with `--multi_api_count 5`, all five profile environment variables must be set. If you run with `--multi_api_count 3`, only profiles 1-3 are loaded and checked.

The default single-API variables and the selected `ENVGEN_API_KEY_*` / `ENVGEN_BASE_URL_*` variables may point to the same endpoint and key. They still need to be set separately because different EnvGen stages read them through different configuration paths.

### 4. Run a dry check

Use `--dry_run` to verify argument parsing without calling APIs:

```bash
python run_env_generation.py \
  --run_env_discovery --run_env_synthesis --run_env_evolution \
  --task_source dataset \
  --enable_theme_embedding \
  --enable_theme_clustering \
  --theme_cluster_count 800 \
  --evolution_init_config_count 1 \
  --evolution_eval_steps 30 \
  --evolution_max_repair_rounds 3 \
  --evolution_top_n 5 \
  --evolution_threshold 1 \
  --evolution_agent_mode dual \
  --evolution_enable_llm_patch \
  --multi_api_count 5 \
  --multi_api_config configs/multi_api_profiles.json \
  --dry_run
```

### 5. Run the full pipeline

```bash
python run_env_generation.py \
  --run_env_discovery --run_env_synthesis --run_env_evolution \
  --task_source dataset \
  --enable_theme_embedding \
  --enable_theme_clustering \
  --theme_cluster_count 800 \
  --evolution_init_config_count 1 \
  --evolution_eval_steps 30 \
  --evolution_max_repair_rounds 3 \
  --evolution_top_n 5 \
  --evolution_threshold 1 \
  --evolution_agent_mode dual \
  --evolution_enable_llm_patch \
  --multi_api_count 5 \
  --multi_api_config configs/multi_api_profiles.json
```

This is the recommended full generation command for Agent-ValueBench-style environment construction.

### 6. Export runtime environment files

After Env Evolution has produced `EnvGen/envgen_pipeline/stage3_refine/final_result/filtered_env_metadata.json`, return to the repository root and run:

```bash
cd ..

python EnvGen/runtime_export/run_adapt.py \
  --source_json EnvGen/envgen_pipeline/stage3_refine/final_result/filtered_env_metadata.json \
  --all_envs \
  --output_env_dir environment \
  --reasoner_model <reasoner-model-id> \
  --reasoner_max_calls 4 \
  --report_dir EnvGen/runtime_export/full_batch_reports \
  --max_adapt_attempts 1
```

This writes paired runtime files to:

```text
environment/<EnvName>.json
environment/<EnvName>.py
```

### 7. Resume interrupted runs

Long runs may pause because of network or provider errors. To reuse existing step outputs and continue from resumable checkpoints, re-run the same command with:

```bash
--resume
```

For small smoke tests, add `--max_tasks`, for example:

```bash
--max_tasks 70 --theme_cluster_count 10
```

---

## 📦 Main Outputs

By default, EnvGen writes:

| Stage | Output |
| --- | --- |
| Env Discovery | `EnvGen/envgen_pipeline/stage1_env_discovery/final_result/discovered_environment_themes.json` |
| Env Synthesis | `EnvGen/envgen_pipeline/stage2_env_synthesis/final_result/synthesized_environments.json` |
| Env Evolution | `EnvGen/envgen_pipeline/stage3_refine/final_result/filtered_env_metadata.json` |
| Env Evolution repair queue | `EnvGen/envgen_pipeline/stage3_refine/final_result/repair_queue_env_metadata.json` |
| Env Evolution report | `EnvGen/envgen_pipeline/stage3_refine/final_result/repair_report.json` |
| Env Evolution full metadata | `EnvGen/envgen_pipeline/stage3_refine/final_result/refined_env_items_full.json` |
| Runtime environment JSON | `environment/<EnvName>.json` |
| Runtime environment Python | `environment/<EnvName>.py` |

Generation-stage outputs are written under `EnvGen/envgen_pipeline/`. The runtime export command above is run from the repository root so that `--output_env_dir environment` writes into the root runtime environment directory.

---

## ⚙️ CLI Reference

### General controls

| Argument | Default | Description |
| --- | ---: | --- |
| `--random_seed` | `42` | Random seed used by deterministic sampling utilities. |
| `--max_tasks` | `0` | Limit the number of source tasks after aggregation and deduplication. `<=0` means no limit. |
| `--dry_run` | off | Print resolved arguments and exit without running the pipeline. |
| `--resume` | off | Reuse existing outputs and resume resumable shard checkpoints. |
| `--resume_poll_interval` | `2` | Seconds between status checks while waiting for active or blocked shards. |
| `--run_env_discovery` | off | Run Stage 1. If no stage flag is given, Stage 1 and Stage 2 run by default. |
| `--run_env_synthesis` | off | Run Stage 2. |
| `--run_env_evolution` | off | Run Stage 3. |
| `--multi_api_count` | `1` | Number of API profiles to use. Multi-profile execution shards Stage 2, Stage 3, and optional theme embedding work. |
| `--multi_api_config` | `""` | JSON profile file. Required when `--multi_api_count > 1`. |

### Task source controls

| Argument | Default | Description |
| --- | ---: | --- |
| `--task_source` | `dataset` | Source mode: `dataset`, `file`, or `inline`. |
| `--task_file` | `""` | JSON list file used when `--task_source file`. Items may be strings or objects. |
| `--task_file_task_key` | `task` | Object key containing the task text in `--task_file`. |
| `--task_file_task_from_key` | `task_from` | Object key containing the source label in `--task_file`. |
| `--task_file_default_from` | `custom_file` | Source label used when a file item has no source label. |
| `--inline_task` | `""` | Single task text used when `--task_source inline`. |
| `--inline_task_from` | `inline` | Source label for the inline task. |
| `--include_api_bank` / `--exclude_api_bank` | include | Include or exclude API-Bank in dataset mode. |
| `--include_toolace` / `--exclude_toolace` | include | Include or exclude ToolACE in dataset mode. |
| `--include_toolbench_5000` / `--exclude_toolbench_5000` | include | Include or exclude ToolBench-5000 in dataset mode. |
| `--include_toolalpaca` / `--exclude_toolalpaca` | include | Include or exclude ToolAlpaca in dataset mode. |
| `--include_agentharm` / `--exclude_agentharm` | include | Include or exclude AgentHarm in dataset mode. |
| `--include_agent_safetybench` / `--exclude_agent_safetybench` | include | Include or exclude Agent-SafetyBench in dataset mode. |
| `--deduplicate_within_corpus` / `--no_deduplicate_within_corpus` | deduplicate | Deduplicate tasks inside each corpus before merging. |
| `--deduplicate_across_corpora` / `--no_deduplicate_across_corpora` | deduplicate | Deduplicate tasks globally after merging corpora. |

### Stage 1: Env Discovery

| Argument | Default | Description |
| --- | ---: | --- |
| `--discovery_source_tasks_output` | `stage1_env_discovery/temp_result/step1_source_corpus_aggregation.json` | Normalized source task output. |
| `--discovery_task_filter_output` | `stage1_env_discovery/temp_result/step2_environment_theme_pool_construction.judge.json` | Stateful-task filtering output. |
| `--discovery_theme_pool_output` | `stage1_env_discovery/temp_result/step2_environment_theme_pool_construction.json` | Inferred environment theme pool. |
| `--discovery_theme_embedding_output` | `stage1_env_discovery/temp_result/step3_clustering_deduplication.embeddings.json` | Optional embedding output for theme summaries. |
| `--discovery_selected_theme_output` | `stage1_env_discovery/temp_result/step3_clustering_deduplication.selected.json` | Optional selected themes after filtering and clustering. |
| `--discovery_final_output` | `stage1_env_discovery/final_result/discovered_environment_themes.json` | Final Stage 1 environment theme list. |
| `--judge_model` | `gpt-4.1` | Model used to judge whether tasks require stateful tool use. |
| `--judge_max_workers` | `3` | Worker count for the stateful-task judge. |
| `--topic_model` | `gpt-4.1` | Model used to infer environment themes. |
| `--topic_num_workers` | `3` | Worker count for theme inference. |
| `--enable_theme_embedding` | off | Generate embeddings for environment theme summaries. |
| `--embedding_model` | `text-embedding-3-large` | Embedding model for theme clustering. |
| `--embedding_batch_size` | `2` | Batch size for embedding requests. |
| `--embedding_timeout` | `60` | Embedding request timeout in seconds. |
| `--enable_theme_clustering` | off | Filter and cluster environment themes. Requires `--enable_theme_embedding`. |
| `--theme_modelability_threshold` | `7` | Minimum modelability score retained before clustering. |
| `--theme_usefulness_threshold` | `7` | Minimum usefulness score retained before clustering. |
| `--theme_cluster_count` | `50` | Target number of clusters. The actual value is capped by the number of retained themes. |

### Stage 2: Env Synthesis

| Argument | Default | Description |
| --- | ---: | --- |
| `--synthesis_input_themes` | `stage1_env_discovery/final_result/discovered_environment_themes.json` | Input themes when Stage 2 is run without Stage 1 in the same command. |
| `--state_deduction_model` | `gpt-4.1` | Model used to infer environment state schemas. |
| `--state_scaffold_model` | `gpt-4.1` | Model used to build state scaffolds. |
| `--interface_design_model` | `gpt-4.1` | Model used to design tool interfaces. |
| `--program_synthesis_model` | `gpt-4.1` | Model used to synthesize function implementations. |
| `--program_synthesis_max_workers` | `2` | Worker count for operation-code synthesis. |
| `--state_deduction_save_every` | `10` | Save interval during state deduction. |
| `--state_schema_output` | `stage2_env_synthesis/temp_result/step1_state_deduction.schema.json` | State schema output. |
| `--state_scaffold_output` | `stage2_env_synthesis/temp_result/step1_state_deduction.scaffold.json` | State scaffold output. |
| `--interface_design_output` | `stage2_env_synthesis/temp_result/step2_interface_design.json` | Tool interface design output. |
| `--operation_code_output` | `stage2_env_synthesis/temp_result/step3_program_synthesis.functions.json` | Synthesized function code output. |
| `--assembled_program_output` | `stage2_env_synthesis/temp_result/step3_program_synthesis.programs.json` | Assembled environment program output. |
| `--verified_program_output` | `stage2_env_synthesis/temp_result/step3_program_synthesis.verified.json` | Program-analysis output. |
| `--synthesis_final_output` | `stage2_env_synthesis/final_result/synthesized_environments.json` | Final Stage 2 synthesized environments. |

### Stage 3: Env Evolution

| Argument | Default | Description |
| --- | ---: | --- |
| `--evolution_input_envs` | `stage2_env_synthesis/final_result/synthesized_environments.json` | Input environments when Stage 3 is run without Stage 2 in the same command. |
| `--evolution_temp_dir` | `stage3_refine/temp_result` | Intermediate Stage 3 output directory. |
| `--evolution_final_dir` | `stage3_refine/final_result` | Final Stage 3 output directory. |
| `--evolution_threshold` | `0.85` | Minimum pass rate required for an environment to be accepted. |
| `--evolution_positive_pass_threshold` | `0.5` | Positive-case pass threshold used during finalization. |
| `--evolution_init_config_count` | `1` | Number of initialization configurations generated per environment. |
| `--evolution_eval_steps` | `100` | Number of diagnostic rollout steps/cases used during evaluation. |
| `--evolution_max_repair_rounds` | `3` | Maximum repair rounds per environment. |
| `--evolution_top_n` | `5` | Number of high-impact failed functions selected for the repair ledger. |
| `--evolution_max_cases_per_function` | `5` | Maximum failure cases retained per function for repair. |
| `--evolution_init_model` | `gpt-4.1` | Model used to generate initialization configs. |
| `--evolution_init_temperature` | `0.5` | Temperature for initialization-config generation. |
| `--evolution_eval_model` | `gpt-4.1-mini` | Model used by the rollout evaluator. |
| `--evolution_eval_temperature` | `0.5` | Temperature for rollout evaluation. |
| `--evolution_agent_mode` | `dual` | Rollout mode: `dual` or `local`. |
| `--evolution_enable_llm_patch` | off | Enable LLM-based surgical repair in the repair loop. |
| `--evolution_llm_patch_model` | `gpt-4.1` | Model used for LLM code patches. |
| `--evolution_llm_patch_temperature` | `0.1` | Temperature for LLM code patches. |
| `--evolution_skip_llm_init` | off | Skip LLM initialization-config generation. Useful only when reusing existing configs. |
| `--evolution_reuse_existing_init_config` | off | Reuse previously generated initialization configs when present. |

### Runtime export

Runtime export is launched with `python EnvGen/runtime_export/run_adapt.py` from the repository root.

| Argument | Default | Description |
| --- | ---: | --- |
| `--source_json` | `EnvGen/envgen_pipeline/stage3_refine/final_result/filtered_env_metadata.json` | EnvGen metadata file to export. |
| `--all_envs` | off | Required by this entrypoint. Exports every environment item in `--source_json`. |
| `--output_env_dir` | `environment` | Directory for final `<EnvName>.json` and `<EnvName>.py` files. Existing same-name files are overwritten. |
| `--report_dir` | `EnvGen/runtime_export/output` | Directory for JSON-stage reports, runtime reports, and `batch_adapt_summary.json`. |
| `--max_adapt_attempts` | `1` | Number of full JSON+Python export attempts per environment. |
| `--runtime_timeout_seconds` | `120` | Timeout for the local runtime smoke subprocess. |
| `--reasoner_model` | `deepseek-reasoner` | Model used for JSON type completion and final JSON review. |
| `--reasoner_temperature` | `0.0` | Sampling temperature for reasoner calls. |
| `--reasoner_max_tokens` | `4096` | Maximum tokens for each reasoner response. |
| `--reasoner_max_calls` | `4` | Maximum retries per reasoner call, hard-capped at 4 internally. |

Runtime export uses the same single-API environment variables described in Quick Start: `VALUEBENCH_API_KEY` / `VALUEBENCH_BASE_URL` or `OPENAI_API_KEY` / `OPENAI_BASE_URL`.

---

## 🧪 Example: Custom Task File

Create a JSON list:

```json
[
  {
    "task": "Book a meeting room, check conflicts, and update the calendar.",
    "task_from": "custom_demo"
  }
]
```

Then run:

```bash
python run_env_generation.py \
  --run_env_discovery --run_env_synthesis --run_env_evolution \
  --task_source file \
  --task_file path/to/tasks.json \
  --enable_theme_embedding \
  --enable_theme_clustering \
  --theme_cluster_count 10 \
  --evolution_enable_llm_patch
```

---

## ✅ Notes for Reproducibility

- Keep API keys out of version control. Prefer environment variables.
- Use the same model names, thresholds, clustering settings, and random seed
  when comparing generated outputs across runs.
- `--resume` is intended for recovering interrupted long runs, not for changing
  pipeline settings mid-run.
- Multi-profile execution preserves item order when shards are merged.

## 🙏 Acknowledgement

This codebase is built upon [EnvScaler](https://github.com/RUC-NLPIR/EnvScaler), and we sincerely appreciate their efforts.
