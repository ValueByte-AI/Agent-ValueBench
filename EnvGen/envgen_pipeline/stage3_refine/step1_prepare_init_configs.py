"""Stage3-REFINE Step1: prepare eval init config (no best-config selection)."""

import argparse
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage3_refine.test_config_generation import process_env_item as gen_init_configs_for_env
from stage3_refine.refine_utils import ensure_eval_init_config
from utils.process_file import read_file, save_file
from utils.recovery import RecoverableStepError
from utils.resumable import run_sequential_step


def _maybe_pad_init_configs(env_item, target_num: int):
    init_list = deepcopy(env_item.get("init_config_list", []))
    if len(init_list) >= target_num:
        env_item["init_config_list"] = init_list
        return env_item
    if not init_list:
        init_list.append({})
    while len(init_list) < target_num:
        init_list.append(deepcopy(init_list[0]))
    env_item["init_config_list"] = init_list
    return env_item


def process_item(
    env_item,
    gen_config_num: int,
    model: str,
    temperature: float,
    skip_llm_init: bool,
    reuse_existing_init_config: bool,
):
    new_item = deepcopy(env_item)
    existing_num = len(new_item.get("init_config_list", []))

    if reuse_existing_init_config and existing_num >= gen_config_num:
        pass
    elif skip_llm_init:
        new_item = _maybe_pad_init_configs(new_item, gen_config_num)
    else:
        try:
            new_item = gen_init_configs_for_env(
                env_item=new_item,
                gen_config_num=gen_config_num,
                model=model,
                temperature=temperature,
            )
        except RecoverableStepError as exc:
            raise RecoverableStepError(
                step_label="Stage3-Refine-Step1",
                error=exc.error,
                partial_item=exc.partial_item,
            ) from exc
        if not new_item.get("init_config_list"):
            new_item["init_config_list"] = [{}]
        if len(new_item["init_config_list"]) < gen_config_num:
            new_item = _maybe_pad_init_configs(new_item, gen_config_num)

    new_item = ensure_eval_init_config(new_item)
    return new_item


def main(args):
    data = read_file(args.read_file_path)
    run_sequential_step(
        items=data,
        output_path=args.save_file_path,
        key_fn=lambda item: item.get("__dispatch_index__", item.get("task", item.get("environment_summary", ""))),
        is_complete_fn=lambda item: (
            isinstance(item, dict)
            and isinstance(item.get("init_config_list"), list)
            and len(item.get("init_config_list", [])) >= args.gen_config_num
            and "eval_init_config" in item
        ),
        process_fn=lambda item: process_item(
            env_item=item,
            gen_config_num=args.gen_config_num,
            model=args.model,
            temperature=args.temperature,
            skip_llm_init=args.skip_llm_init,
            reuse_existing_init_config=args.reuse_existing_init_config,
        ),
        save_every=args.save_every,
        step_label="Stage3-Refine-Step1",
        progress_desc=getattr(args, "progress_desc", None),
        progress_position=getattr(args, "progress_position", None),
    )
    print(f"[Step1] saved: {args.save_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--read_file_path",
        type=str,
        default="stage2_env_synthesis/final_result/synthesized_environments.json",
    )
    parser.add_argument(
        "--save_file_path",
        type=str,
        default="stage3_refine/temp_result/step1_prepared_init_configs.json",
    )
    parser.add_argument("--gen_config_num", type=int, default=1)
    parser.add_argument("--model", type=str, default="gpt-4.1")
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--save_every", type=int, default=1)
    parser.add_argument("--skip_llm_init", action="store_true")
    parser.add_argument("--reuse_existing_init_config", action="store_true")
    args = parser.parse_args()
    main(args)
