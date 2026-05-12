# Agent-ValueBench 🧭

📄 This is the official repository for our paper *Agent-ValueBench: A Comprehensive Benchmark for Evaluating Agent Values*, containing our complete dataset and codebase.

**Agent-ValueBench** is the first comprehensive benchmark for evaluating agent values in tool-using language model agents. It spans 28 value systems, 332 system-scoped value dimensions, 394 executable sandbox environments, and 4,335 value-conflict tasks. Each benchmark case defines a value-conflict task, a sandbox environment, the available tools, and rubric items used to evaluate whether an agent's trajectory supports either side of the value conflict.

The benchmark is designed around a central question:

> What values do agents exhibit?

The released benchmark assets include executable environments, value-conflict cases, and rubrics. The codebase also contains the pipeline used to construct and evaluate those assets.

---

## ✨ What This Repository Contains

Agent-ValueBench is organized as a chronological pipeline:

1. 🔎 **Environment generation and runtime export** with [`EnvGen/`](EnvGen/README.md)  
   Discover environment themes from source tasks, synthesize stateful tool
   environments, validate / repair them through execution, and export
   runtime-ready paired files: `environment/<EnvName>.json` and
   `environment/<EnvName>.py`.

2. 🧩 **Case generation** with [`CaseGen/`](CaseGen/README.md)  
   Generate executable value-conflict cases from adapted environments and
   authoritative value definitions.

3. 🤖 **Agent trajectory generation** with [`TrajGen/`](TrajGen/README.md)  
   Run OpenAI-compatible function-calling ReAct agents on each case and record
   structured trajectories.

4. ⚖️ **Trajectory judging and aggregation** with
   [`ValueEval/`](ValueEval/README.md)  
   Judge trajectories with saved rubrics, compute value adherence, and estimate
   value priority with Bradley-Terry ranking.

5. 🧪 **Optional LLM forced-choice comparison** with
   [`LLMChoice/`](LLMChoice/README.md)  
   Present selected cases as direct two-option LLM decisions and convert those
   choices into the same value-priority format.

6. 🧰 **Optional alternative harness evaluation** with
   [`HarnessEval/`](HarnessEval/README.md)  
   Run selected cases through OpenClaw, Codex, and Claude Code style harnesses,
   including skill-injection experiments.

---

## 📁 Repository Structure

```text
Agent-ValueBench/
├── README.md
├── requirements.txt                    # Root Python 3.11 dependencies, except HarnessEval
├── configs/
│   └── value_systems.json              # Authoritative value systems and value definitions
├── core/                               # Shared API, JSON, file, and debug utilities
├── EnvGen/                             # Environment discovery, synthesis, evolution, and runtime export
├── CaseGen/                            # Value-conflict case generation
├── TrajGen/                            # Main function-calling ReAct trajectory generation
├── LLMChoice/                          # Forced-choice LLM comparison experiment
├── HarnessEval/                        # Alternative harness and skill-injection experiments
├── ValueEval/                          # Trajectory judging and value aggregation
├── environment/                        # Released runtime environments: <EnvName>.json + <EnvName>.py
├── case/                               # Released value-conflict cases
└── rubric/                             # Released scoring rubrics
```

Generated run artifacts are intentionally written to module-specific run directories or `result*/` directories. They are not required to understand the released benchmark assets.

---

## 🚀 Quick Setup

### 1. Clone the repository

```bash
git clone https://github.com/ValueByte-AI/Agent-ValueBench.git
cd Agent-ValueBench
```

### 2. Create a Python 3.11 environment

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

### 3. Install root dependencies

The root `requirements.txt` covers the main construction, trajectory generation, forced-choice LLM, and value-evaluation pipeline:

```bash
pip install -r requirements.txt
```

`HarnessEval` is separate and uses `uv` inside [`HarnessEval/`](HarnessEval/README.md), so its dependencies are not included in the root requirements file.

### 4. Prepare API credentials

Agent-ValueBench has two API configuration formats.

**CaseGen, TrajGen, LLMChoice, and ValueEval** use API slot files such as `configs/api_slots.json`. Each slot is one OpenAI-compatible endpoint profile. The number of slots controls how much parallel API work these modules can schedule, so add as many slots as you want to use for concurrent requests:

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
      "name": "secondary",
      "api_key": "YOUR_API_KEY",
      "base_url": "YOUR_API_URL"
    }
  ]
}
```

Use the exact model identifiers required by your endpoint. Do not commit real API keys.

**EnvGen** uses a single-API profile through environment variables. It also needs a separate multi-API profile file for sharded generation runs.

Set the default single-API profile first. EnvGen uses it for steps that run outside the sharded multi-profile dispatcher, and its runtime export utility uses it for reasoner calls during JSON type completion and final JSON review. Use `VALUEBENCH_API_KEY` / `VALUEBENCH_BASE_URL` for this shared single-API profile:

```bash
export VALUEBENCH_API_KEY="YOUR_API_KEY"
export VALUEBENCH_BASE_URL="YOUR_API_URL"
```

EnvGen also accepts `OPENAI_API_KEY` / `OPENAI_BASE_URL` for its own default single-API profile.

Then configure multi-profile execution with `EnvGen/configs/multi_api_profiles.json`. This is not the same format as `configs/api_slots.json`: EnvGen reads a list named `profiles`, then uses `--multi_api_count` to select the first N profiles for its own sharded environment-generation stages. Both formats support concurrent API use; they are separate only because EnvGen has a different internal sharding pipeline.

The recommended EnvGen pattern is to keep secrets in environment variables and let the JSON file point to those variable names:

```json
{
  "profiles": [
    {
      "name": "api_1",
      "api_key_env": "ENVGEN_API_KEY_1",
      "base_url_env": "ENVGEN_BASE_URL_1"
    },
    {
      "name": "api_2",
      "api_key_env": "ENVGEN_API_KEY_2",
      "base_url_env": "ENVGEN_BASE_URL_2"
    }
  ]
}
```

Then set the corresponding environment variables before running EnvGen:

```bash
export ENVGEN_API_KEY_1="YOUR_API_KEY_1"
export ENVGEN_BASE_URL_1="YOUR_API_URL_1"

export ENVGEN_API_KEY_2="YOUR_API_KEY_2"
export ENVGEN_BASE_URL_2="YOUR_API_URL_2"
```

Set as many `ENVGEN_API_KEY_*` / `ENVGEN_BASE_URL_*` pairs as your `--multi_api_count` uses. For example, `--multi_api_count 5` requires five usable profiles in `EnvGen/configs/multi_api_profiles.json`, and the default profile file expects `ENVGEN_API_KEY_1` through `ENVGEN_API_KEY_5`. If you run with `--multi_api_count 3`, only profiles 1-3 are loaded and checked.

If you use the same endpoint for the default profile and the sharded profiles, it is fine for these variables to point to the same API key and base URL. The important point is that the default profile variables and the selected `ENVGEN_API_KEY_*` / `ENVGEN_BASE_URL_*` variables must both be set.

EnvGen also supports direct local profile values:

```json
{
  "profiles": [
    {
      "name": "api_1",
      "api_key": "YOUR_API_KEY",
      "base_url": "YOUR_API_URL"
    }
  ]
}
```

This is convenient for private local runs, but do not commit real API keys. For single-profile EnvGen runs without a profile file, `OPENAI_API_KEY` / `OPENAI_BASE_URL` or `VALUEBENCH_API_KEY` / `VALUEBENCH_BASE_URL` are accepted.

---

## 🧭 Main Pipeline Commands

The commands below follow the intended time order of the benchmark pipeline. Each module README contains the full argument reference and operational notes.

### 1. Generate Environments with EnvGen 🔎

Before running this stage, configure EnvGen API profiles as described in the Quick Setup section above.

```bash
cd EnvGen

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

cd ..
```

This writes generated environment metadata under EnvGen's stage output directories. See [`EnvGen/README.md`](EnvGen/README.md) for all generation arguments.

### 2. Export Environments to Runtime Format 🧱

```bash
python EnvGen/runtime_export/run_adapt.py \
  --source_json EnvGen/envgen_pipeline/stage3_refine/final_result/filtered_env_metadata.json \
  --all_envs \
  --output_env_dir environment \
  --reasoner_model <reasoner-model-id> \
  --reasoner_max_calls 4 \
  --report_dir EnvGen/runtime_export/full_batch_reports \
  --max_adapt_attempts 1
```

This writes paired runtime files:

```text
environment/<EnvName>.json
environment/<EnvName>.py
```

See [`EnvGen/README.md`](EnvGen/README.md) for runtime export arguments, JSON schema review, Python wrapping, and runtime smoke-test behavior.

### 3. Generate Value-Conflict Cases 🧩

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

Monitor the run in another terminal with the same run name:

```bash
python CaseGen/show_batch_case_progress.py --run_name formal
```

Accepted cases are written as flat JSON files:

```text
case/case_00001.json
case/case_00002.json
...
```

See [`CaseGen/README.md`](CaseGen/README.md) for case planning, retry, validation, and resume behavior.

### 4. Run Main Agent Trajectories 🤖

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

Monitor the trajectory run in another terminal with the same run name:

```bash
python -m TrajGen.show_batch_tir_agent_progress \
  --run_name "traj_${MODEL_NAME}"
```

Final trajectories are written to:

```text
result/<model_name>/traj/
```

If you pass `--n`, TrajGen sends it only for GPT-family models: the final slash-separated segment of the model identifier must start with `gpt`.

See [`TrajGen/README.md`](TrajGen/README.md) for resume, progress monitoring, and split-choice continuation.

### 5. Judge Trajectories and Compute Value Reports ⚖️

See [`ValueEval/README.md`](ValueEval/README.md) for the full argument reference and additional judging examples.

Judge standard TrajGen trajectories:

```bash
python -m ValueEval.run_batch_rubric_judging \
  --run_name "judge_${MODEL_NAME}" \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir "result/${MODEL_NAME}/traj" \
  --result_output_dir_name "result/${MODEL_NAME}/judge_result" \
  --judge_models <judge-model-id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4
```

Monitor the judging run in another terminal with the same run name:

```bash
python -m ValueEval.show_batch_rubric_judging_progress \
  --run_name "judge_${MODEL_NAME}"
```

Compute value adherence:

```bash
python -m ValueEval.compute_value_adherence \
  --cases_dir case \
  --rubric_dir rubric \
  --judge_result_dir "result/${MODEL_NAME}/judge_result" \
  --max_score 10 \
  --output_dir "result/${MODEL_NAME}"
```

Compute value priority:

```bash
python ValueEval/compute_value_priority.py \
  --model-dir "result/${MODEL_NAME}"
```

Render a markdown summary table:

```bash
python ValueEval/render_value_results_markdown.py \
  --result-root result \
  --output result/all_model_results.md
```

---

## 🧪 Optional Experiments

### LLM Forced-Choice Comparison

This experiment tests whether the same model exhibits different value preferences when it answers as a direct LLM versus when it acts as a tool-using agent in the main trajectory pipeline.

Run the direct LLM two-option experiment:

```bash
python LLMChoice/run_batch_choice_llm_eval_openai.py \
  --run_name "choice_${MODEL_NAME}" \
  --api_slots_json configs/api_slots.json \
  --cases_dir LLMChoice/cases \
  --output_dir "result/${MODEL_NAME}/choice_llm" \
  --eval_model "${MODEL_ID}" \
  --temperature 0.0 \
  --max_tokens 12000 \
  --timeout_seconds 600 \
  --network_max_retries 2
```

Convert choices into Bradley-Terry-ready input:

```bash
python LLMChoice/convert_choice_llm_to_priority_input.py \
  --choice_cases_dir LLMChoice/cases \
  --choice_result_dir "result/${MODEL_NAME}/choice_llm" \
  --project_root . \
  --max_score 10
```

Then compute priority:

```bash
python ValueEval/compute_value_priority.py \
  --model-dir "result/${MODEL_NAME}/choice_llm"
```

See [`LLMChoice/README.md`](LLMChoice/README.md) for the case format and conversion checks.

### Alternative Harness Evaluation

This experiment tests whether an agent's value preferences change under different harnesses, and whether skill injection can steer those preferences.

Set up the harness environment:

```bash
cd HarnessEval
uv sync
git clone https://github.com/harbor-framework/harbor.git harbor
git -C harbor checkout 0533a59c41ce435d9e59ff8c82da67f6e5b6edc7
uv tool install ./harbor
docker pull python:3.12-alpine
```

Prepare the HarnessEval case subset and harness-compatible environment copy from the root dataset:

```bash
uv run python scripts/prepare_harness_assets.py
```

Generate Harbor tasks:

```bash
uv run python adapters/agent_valuebench/run_adapter.py \
  --output-dir datasets/agent_valuebench
```

Then run OpenClaw, Codex, or Claude Code as described in [`HarnessEval/README.md`](HarnessEval/README.md). The resulting trajectories can be judged from the repository root with:

```bash
cd ..

python -m ValueEval.run_batch_harness_rubric_judging \
  --run_name judge_harness_<model_name>_<harness_name> \
  --api_slots_json configs/api_slots.json \
  --cases_dir case \
  --rubric_dir rubric \
  --traj_dir result_harness/<model_name>/<harness_name> \
  --result_output_dir_name result_harness/<model_name>/<harness_name>/judge_result \
  --judge_models <judge-model-id> \
  --temperature 0.0 \
  --max-tokens 18000 \
  --timeout-seconds 600 \
  --network-max-retries 2 \
  --max-json-retries 4
```

Monitor the harness judging run with the same ValueEval progress watcher:

```bash
python -m ValueEval.show_batch_rubric_judging_progress \
  --run_name judge_harness_<model_name>_<harness_name>
```

---

## 📦 Released Benchmark Assets

The released dataset portion of the repository is centered on:

- `environment/`: executable sandbox environments, each as a paired JSON schema
  and Python implementation.
- `case/`: value-conflict tasks that initialize and use those environments.
- `rubric/`: saved case-specific rubrics used by ValueEval to score model
  trajectories.
- `configs/value_systems.json`: value-system definitions used to construct and
  interpret cases.

These assets are sufficient to run models, judge trajectories, and reproduce value adherence / value priority reports without regenerating the benchmark from scratch.

---

## 📚 Third-Party Components

`HarnessEval/` can run optional Codex / Claude Code harness experiments through Harbor. Harbor is not vendored in this repository; follow the [`HarnessEval/README.md`](HarnessEval/README.md) setup steps to clone the upstream Harbor repository locally before running Harbor-based experiments.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for the full third-party notice and citation information.

---

## 🔐 API Key Hygiene

Do not commit real API keys. Keep credentials in local files such as `configs/api_slots.json` or environment variables, and exclude private config files from public commits.

---

## 📚 Module Documentation

- [`EnvGen/README.md`](EnvGen/README.md): environment generation and runtime export
- [`CaseGen/README.md`](CaseGen/README.md): case generation
- [`TrajGen/README.md`](TrajGen/README.md): main trajectory generation
- [`LLMChoice/README.md`](LLMChoice/README.md): forced-choice LLM experiment
- [`HarnessEval/README.md`](HarnessEval/README.md): alternative harness runs
- [`ValueEval/README.md`](ValueEval/README.md): judging and aggregation

---

## 📝 Citation

If Agent-ValueBench is useful for your research, please consider citing our paper. We sincerely appreciate your support.

```bibtex
@misc{dong2026agentvaluebenchcomprehensivebenchmarkevaluating,
      title={Agent-ValueBench: A Comprehensive Benchmark for Evaluating Agent Values}, 
      author={Haonan Dong and Qiguan Feng and Kehan Jiang and Haoran Ye and Xin Zhang and Guojie Song},
      year={2026},
      eprint={2605.10365},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.10365}, 
}
```
