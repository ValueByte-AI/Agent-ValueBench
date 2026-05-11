"""Stage3-REFINE Step3: failure mining and root-cause bug ledger."""

import argparse
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage3_refine.refine_utils import build_bug_ledger, calc_metrics_from_item
from utils.process_file import read_file, save_file
from utils.resumable import run_sequential_step


def main(args):
    data = read_file(args.read_file_path)
    run_sequential_step(
        items=data,
        output_path=args.save_file_path,
        key_fn=lambda item: item.get("__dispatch_index__", item.get("task", item.get("environment_summary", ""))),
        is_complete_fn=lambda item: isinstance(item, dict) and isinstance(item.get("bug_ledger"), dict),
        process_fn=lambda item: _process_one_item(
            item=item,
            top_n=args.top_n,
            max_cases_per_func=args.max_cases_per_func,
        ),
        save_every=args.save_every,
        step_label="Stage3-Refine-Step3",
        progress_desc=getattr(args, "progress_desc", None),
        progress_position=getattr(args, "progress_position", None),
    )
    print(f"[Step3] saved: {args.save_file_path}")


def _process_one_item(item, top_n, max_cases_per_func):
    new_item = deepcopy(item)
    new_item["baseline_metrics"] = calc_metrics_from_item(new_item)
    new_item["bug_ledger"] = build_bug_ledger(
        env_item=new_item,
        top_n=top_n,
        max_cases_per_func=max_cases_per_func,
    )
    return new_item


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--read_file_path",
        type=str,
        default="stage3_refine/temp_result/step2_baseline_roll_check.json",
    )
    parser.add_argument(
        "--save_file_path",
        type=str,
        default="stage3_refine/temp_result/step3_bug_ledger.json",
    )
    parser.add_argument("--top_n", type=int, default=5)
    parser.add_argument("--max_cases_per_func", type=int, default=5)
    parser.add_argument("--save_every", type=int, default=1)
    args = parser.parse_args()
    main(args)
