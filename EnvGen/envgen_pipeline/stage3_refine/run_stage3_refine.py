"""Run the full Stage3-REFINE diagnose-repair-recheck pipeline."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage3_refine.step1_prepare_init_configs import main as step1_main
from stage3_refine.step2_baseline_roll_check import main as step2_main
from stage3_refine.step3_build_bug_ledger import main as step3_main
from stage3_refine.step4_repair_loop import main as step4_main
from stage3_refine.step5_finalize_outputs import main as step5_main


def _ns(**kwargs):
    return argparse.Namespace(**kwargs)


def main(args):
    temp_dir = args.temp_dir
    final_dir = args.final_dir
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    Path(final_dir).mkdir(parents=True, exist_ok=True)

    step1_path = f"{temp_dir}/step1_prepared_init_configs.json"
    step2_path = f"{temp_dir}/step2_baseline_roll_check.json"
    step3_path = f"{temp_dir}/step3_bug_ledger.json"
    step4_path = f"{temp_dir}/step4_repaired_envs.json"

    step1_main(
        _ns(
            read_file_path=args.read_file_path,
            save_file_path=step1_path,
            gen_config_num=args.gen_config_num,
            model=args.init_model,
            temperature=args.init_temperature,
            skip_llm_init=args.skip_llm_init,
            reuse_existing_init_config=args.reuse_existing_init_config,
            save_every=1,
            progress_desc="Stage3-Refine-Step1",
        )
    )
    step2_main(
        _ns(
            read_file_path=step1_path,
            save_file_path=step2_path,
            model=args.eval_model,
            temperature=args.eval_temperature,
            max_steps=args.eval_steps,
            agent_mode=args.agent_mode,
            save_every=1,
            progress_desc="Stage3-Refine-Step2",
        )
    )
    step3_main(
        _ns(
            read_file_path=step2_path,
            save_file_path=step3_path,
            top_n=args.top_n,
            max_cases_per_func=args.max_cases_per_func,
            save_every=1,
            progress_desc="Stage3-Refine-Step3",
        )
    )
    step4_main(
        _ns(
            read_file_path=step3_path,
            save_file_path=step4_path,
            threshold=args.threshold,
            positive_pass_threshold=args.positive_pass_threshold,
            top_n=args.top_n,
            max_repair_rounds=args.max_repair_rounds,
            eval_steps=args.eval_steps,
            eval_model=args.eval_model,
            eval_temperature=args.eval_temperature,
            agent_mode=args.agent_mode,
            enable_llm_patch=args.enable_llm_patch,
            llm_patch_model=args.llm_patch_model,
            llm_patch_temperature=args.llm_patch_temperature,
            save_every=1,
            progress_desc="Stage3-Refine-Step4",
        )
    )
    step5_main(
        _ns(
            read_file_path=step4_path,
            threshold=args.threshold,
            positive_pass_threshold=args.positive_pass_threshold,
            filtered_output_path=f"{final_dir}/filtered_env_metadata.json",
            repair_queue_output_path=f"{final_dir}/repair_queue_env_metadata.json",
            repair_report_output_path=f"{final_dir}/repair_report.json",
            full_output_path=f"{final_dir}/refined_env_items_full.json",
        )
    )
    print("[Stage3-REFINE] pipeline done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--read_file_path",
        type=str,
        default="stage2_env_synthesis/final_result/synthesized_environments.json",
    )
    parser.add_argument("--temp_dir", type=str, default="stage3_refine/temp_result")
    parser.add_argument("--final_dir", type=str, default="stage3_refine/final_result")

    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--positive_pass_threshold", type=float, default=0.5)
    parser.add_argument("--gen_config_num", type=int, default=1)
    parser.add_argument("--eval_steps", type=int, default=100)
    parser.add_argument("--max_repair_rounds", type=int, default=3)
    parser.add_argument("--top_n", type=int, default=5)
    parser.add_argument("--max_cases_per_func", type=int, default=5)

    parser.add_argument("--init_model", type=str, default="gpt-4.1")
    parser.add_argument("--init_temperature", type=float, default=0.5)
    parser.add_argument("--eval_model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--eval_temperature", type=float, default=0.5)
    parser.add_argument("--agent_mode", type=str, choices=["dual", "local"], default="dual")

    parser.add_argument("--enable_llm_patch", action="store_true")
    parser.add_argument("--llm_patch_model", type=str, default="gpt-4.1")
    parser.add_argument("--llm_patch_temperature", type=float, default=0.1)

    parser.add_argument("--skip_llm_init", action="store_true")
    parser.add_argument("--reuse_existing_init_config", action="store_true")
    args = parser.parse_args()
    main(args)
