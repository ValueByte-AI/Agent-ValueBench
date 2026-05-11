"""Stage3-REFINE Step5: finalize accepted pool + repair report (with audit trace)."""

import argparse
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage3_refine.refine_utils import calc_metrics_from_item, metrics_meet_thresholds
from utils.process_file import read_file, save_file


def _brief_metadata_dict(env_item):
    item = deepcopy(env_item)
    if "env_func_details" in item:
        del item["env_func_details"]
    if "func_test_result" in item:
        details = item["func_test_result"].get("func_test_cases", {}).get("details")
        if details is not None:
            del item["func_test_result"]["func_test_cases"]["details"]
    if "bug_ledger" in item:
        del item["bug_ledger"]
    return item


def _build_env_metadata(item, env_id):
    return {
        "env_id": env_id,
        "environment_summary": item["environment_summary"],
        "environment_introduction": item["environment_introduction"],
        "state_space_definition": item["state_space_definition"],
        "constraints_rules": item["constraints_rules"],
        "operation_list": item["operation_list"],
        "env_class_name": item["env_class_name"],
        "env_class_code": item["env_class_code"],
        "env_class_def": item["env_class_def"],
        "env_structure": item["env_structure"],
        "tools": item["tools"],
        "final_metrics": item.get("final_metrics") or calc_metrics_from_item(item),
    }


def _build_repair_report_entry(item, env_key, threshold, positive_pass_threshold):
    audit = item.get("repair_audit", {})
    final_metrics = item.get("final_metrics") or calc_metrics_from_item(item)
    original_metrics = audit.get("original_metrics") or item.get("baseline_metrics") or {}
    status = item.get("repair_status", "repair_queue")

    failure_type_summary = {}
    if item.get("bug_ledger"):
        for target in item["bug_ledger"].get("function_rankings", []):
            for k, v in target.get("failure_type_counts", {}).items():
                failure_type_summary[k] = failure_type_summary.get(k, 0) + int(v)

    patched_functions = audit.get("patched_functions", [])
    return {
        "env_key": env_key,
        "environment_summary": item.get("environment_summary", ""),
        "status": status,
        "threshold": threshold,
        "positive_pass_threshold": positive_pass_threshold,
        "original_metrics": original_metrics,
        "final_metrics": final_metrics,
        "patched_functions": patched_functions,
        "failure_type_summary": failure_type_summary,
        "iterations": audit.get("iterations", []),
    }


def main(args):
    data = read_file(args.read_file_path)

    accepted_items = []
    queue_items = []
    for item in data:
        metrics = item.get("final_metrics") or calc_metrics_from_item(item)
        if metrics_meet_thresholds(metrics, args.threshold, args.positive_pass_threshold):
            accepted_items.append(item)
        else:
            queue_items.append(item)

    accepted_metadata = {}
    repair_queue_metadata = {}
    repair_report = []

    for idx, item in enumerate(accepted_items, start=1):
        env_id = f"env_{idx}"
        meta = _build_env_metadata(item, env_id)
        accepted_metadata[env_id] = _brief_metadata_dict(meta)
        repair_report.append(
            _build_repair_report_entry(
                item,
                env_id,
                args.threshold,
                args.positive_pass_threshold,
            )
        )

    for idx, item in enumerate(queue_items, start=1):
        env_id = f"repair_queue_env_{idx}"
        meta = _build_env_metadata(item, env_id)
        repair_queue_metadata[env_id] = _brief_metadata_dict(meta)
        repair_report.append(
            _build_repair_report_entry(
                item,
                env_id,
                args.threshold,
                args.positive_pass_threshold,
            )
        )

    save_file(args.filtered_output_path, accepted_metadata)
    save_file(args.repair_queue_output_path, repair_queue_metadata)
    save_file(args.repair_report_output_path, repair_report)
    save_file(args.full_output_path, data)

    print(f"[Step5] accepted: {len(accepted_items)}")
    print(f"[Step5] repair_queue: {len(queue_items)}")
    print(f"[Step5] saved filtered metadata: {args.filtered_output_path}")
    print(f"[Step5] saved repair queue metadata: {args.repair_queue_output_path}")
    print(f"[Step5] saved repair report: {args.repair_report_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--read_file_path",
        type=str,
        default="stage3_refine/temp_result/step4_repaired_envs.json",
    )
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--positive_pass_threshold", type=float, default=0.5)
    parser.add_argument(
        "--filtered_output_path",
        type=str,
        default="stage3_refine/final_result/filtered_env_metadata.json",
    )
    parser.add_argument(
        "--repair_queue_output_path",
        type=str,
        default="stage3_refine/final_result/repair_queue_env_metadata.json",
    )
    parser.add_argument(
        "--repair_report_output_path",
        type=str,
        default="stage3_refine/final_result/repair_report.json",
    )
    parser.add_argument(
        "--full_output_path",
        type=str,
        default="stage3_refine/final_result/refined_env_items_full.json",
    )
    args = parser.parse_args()
    main(args)
