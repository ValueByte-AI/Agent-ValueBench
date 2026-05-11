from __future__ import annotations

import json
import re
import shlex
import threading
from collections import deque
from pathlib import Path
from typing import Any, Dict, List

from core.file_utils import ensure_dir

from .batch_common import (
    BatchRecoverableAPIError,
    FileLock,
    _atomic_write_json,
    _atomic_write_text,
    _classify_llm_error,
    _now_iso,
    _read_json_or,
    discover_case_files,
)
from .batch_rubric_judging import (
    RUNS_ROOT,
    BatchJudgeCoordinator,
    JudgeBatchSettings,
    PersistentJudgeExecutor,
    _discover_named_json_files,
    _parse_models,
    _result_is_newer_than_traj,
    build_run_parser,
)
from .rubric_trajectory_judge import ValueEvalSettings


def _safe_json_loads(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _extract_tool_harness_calls(command: str) -> List[Dict[str, Any]]:
    """Extract actual sandbox tool calls from shell commands used by harnesses."""

    try:
        tokens = shlex.split(str(command or ""))
    except ValueError:
        return []

    calls: List[Dict[str, Any]] = []
    for idx, token in enumerate(tokens):
        if not token.endswith("tool_harness.py"):
            continue
        if idx + 1 >= len(tokens):
            continue
        tool_name = tokens[idx + 1]
        if not tool_name or tool_name in {"&&", ";", "|"}:
            continue
        raw_args = "{}"
        if idx + 2 < len(tokens):
            candidate = tokens[idx + 2]
            if candidate not in {"&&", ";", "|"}:
                raw_args = candidate
        calls.append(
            {
                "name": tool_name,
                "arguments": _safe_json_loads(raw_args),
            }
        )
    return calls


def _compact_command_output(content: Any) -> Any:
    if not isinstance(content, str):
        return content
    marker = "\nOutput:\n"
    if marker in content:
        content = content.split(marker, 1)[1]
    stdout_marker = "\n[stdout]\n"
    if stdout_marker in content:
        content = content.split(stdout_marker, 1)[0]
    metadata_marker = "\n[metadata]"
    if metadata_marker in content:
        content = content.split(metadata_marker, 1)[0]
    return content


def _observation_content(step: Dict[str, Any]) -> Any:
    observation = step.get("observation")
    if not isinstance(observation, dict):
        return observation
    results = observation.get("results")
    if not isinstance(results, list):
        return observation
    contents = []
    for item in results:
        if isinstance(item, dict) and "content" in item:
            contents.append(_compact_command_output(item.get("content")))
        else:
            contents.append(item)
    if len(contents) == 1:
        return contents[0]
    return contents


def _split_observation_for_calls(observation: Any, count: int) -> List[Any]:
    if count <= 0:
        return []
    if count == 1:
        return [observation]
    if isinstance(observation, list) and len(observation) == count:
        return observation
    if isinstance(observation, str):
        parts = re.split(r"(?:^|\n)---(?:\n|$)", observation.strip())
        if len(parts) == count:
            return [part.strip() for part in parts]
    return []


def _normalize_atif_tool_calls(step: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    raw_tool_calls = step.get("tool_calls")
    if not isinstance(raw_tool_calls, list):
        return normalized

    for raw_call in raw_tool_calls:
        if not isinstance(raw_call, dict):
            continue
        call_id = str(raw_call.get("tool_call_id") or raw_call.get("id") or "")
        function_name = str(raw_call.get("function_name") or raw_call.get("name") or "")
        arguments = raw_call.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}

        command = arguments.get("cmd")
        if command is None:
            command = arguments.get("command")
        extracted_calls = _extract_tool_harness_calls(str(command or ""))

        if extracted_calls:
            for index, extracted in enumerate(extracted_calls, start=1):
                suffix = f":{index}" if len(extracted_calls) > 1 else ""
                normalized.append(
                    {
                        "id": f"{call_id}{suffix}" if call_id else f"extracted_tool_call_{index}",
                        "name": extracted["name"],
                        "arguments": extracted["arguments"],
                        "harness_wrapper_tool": function_name,
                        "harness_wrapper_arguments": arguments,
                    }
                )
            continue

        normalized.append(
            {
                "id": call_id,
                "name": function_name,
                "arguments": arguments,
            }
        )

    return normalized


def _normalize_atif_json_traj(source_path: Path) -> Dict[str, Any]:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    raw_steps = payload.get("steps", [])
    normalized_steps: List[Dict[str, Any]] = []
    final_answer = ""

    for idx, step in enumerate(raw_steps, start=1):
        if not isinstance(step, dict):
            continue
        source = str(step.get("source") or "").strip().lower()
        if source in {"system", "user"}:
            continue

        tool_calls = _normalize_atif_tool_calls(step)
        observation = _observation_content(step) if "observation" in step else None
        message = str(step.get("message") or "")
        reasoning_content = str(step.get("reasoning_content") or "")
        assistant_output = message
        if reasoning_content.strip():
            if assistant_output.strip():
                assistant_output = f"{assistant_output}\n\n[REASONING_CONTENT]\n{reasoning_content}"
            else:
                assistant_output = f"[REASONING_CONTENT]\n{reasoning_content}"
        step_id = step.get("step_id") or step.get("step") or f"s{idx}"

        if not assistant_output and not tool_calls and observation is None:
            continue

        normalized_step: Dict[str, Any] = {
            "step": step_id,
            "assistant_output": assistant_output,
        }

        if tool_calls:
            normalized_step["tool_calls"] = tool_calls
            response_contents = _split_observation_for_calls(observation, len(tool_calls))
            responses = []
            if len(response_contents) == len(tool_calls):
                for call, response_content in zip(tool_calls, response_contents):
                    responses.append(
                        {
                            "tool_call_id": call.get("id"),
                            "name": call.get("name"),
                            "content": response_content,
                        }
                    )
            else:
                responses.append(
                    {
                        "tool_call_id": ",".join(str(call.get("id") or "") for call in tool_calls),
                        "tool_call_ids": [call.get("id") for call in tool_calls],
                        "name": "combined_harness_output",
                        "content": observation,
                    }
                )
            normalized_step["tool_responses"] = responses
        elif observation is not None:
            normalized_step["tool_call"] = None
            normalized_step["tool_response"] = observation

        normalized_steps.append(normalized_step)
        if message.strip():
            final_answer = message.strip()

    return {
        "case_name": source_path.name.rsplit("_traj.", 1)[0],
        "status": "completed",
        "final_answer": final_answer,
        "trajectory_source_format": "atif_json",
        "trajectory_source_path": str(source_path),
        "steps": normalized_steps,
    }


def _normalize_jsonl_traj(source_path: Path) -> Dict[str, Any]:
    normalized_steps: List[Dict[str, Any]] = []
    for idx, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            continue
        tool_name = str(record.get("tool_name") or "")
        arguments = record.get("arguments")
        result = record.get("result")
        normalized_steps.append(
            {
                "step": f"jsonl_{idx:04d}",
                "assistant_output": "",
                "tool_calls": [
                    {
                        "id": f"jsonl_{idx:04d}",
                        "name": tool_name,
                        "arguments": arguments if isinstance(arguments, dict) else arguments,
                        "allowed": record.get("allowed"),
                        "timestamp": record.get("timestamp"),
                    }
                ],
                "tool_responses": [
                    {
                        "tool_call_id": f"jsonl_{idx:04d}",
                        "name": tool_name,
                        "content": result,
                    }
                ],
            }
        )

    return {
        "case_name": source_path.name.rsplit("_traj.", 1)[0],
        "status": "completed",
        "final_answer": "",
        "trajectory_source_format": "jsonl_tool_log",
        "trajectory_source_path": str(source_path),
        "steps": normalized_steps,
    }


def normalize_harness_traj(source_path: Path, output_path: Path) -> Path:
    if source_path.suffix == ".jsonl":
        normalized = _normalize_jsonl_traj(source_path)
    elif source_path.suffix == ".json":
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "schema_version" in payload and "steps" in payload:
            normalized = _normalize_atif_json_traj(source_path)
        else:
            normalized = payload
    else:
        raise ValueError(f"Unsupported trajectory file type: {source_path}")

    normalized["normalized_for"] = "ValueEval_judge"
    normalized["normalized_from"] = str(source_path.resolve())
    _atomic_write_json(output_path, normalized)
    return output_path


def _discover_harness_traj_files(root: Path) -> Dict[str, Path]:
    if not root.exists():
        raise FileNotFoundError(f"trajectory directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"trajectory path is not a directory: {root}")

    mapping: Dict[str, Path] = {}
    for path in sorted(root.rglob("*_traj.*")):
        if not path.is_file() or path.suffix not in {".json", ".jsonl"}:
            continue
        case_stem = path.name.rsplit("_traj.", 1)[0]
        previous = mapping.get(case_stem)
        if previous is not None:
            raise ValueError(f"Duplicate trajectory for {case_stem}: {previous} and {path}")
        mapping[case_stem] = path
    return mapping


def build_harness_judge_plan(
    *,
    case_root: Path,
    rubric_root: Path,
    traj_root: Path,
    result_output_dir_name: str,
) -> Dict[str, Any]:
    output_root = case_root.parent / str(result_output_dir_name).strip()
    case_files = discover_case_files(case_root)
    rubric_files = _discover_named_json_files(rubric_root)
    traj_files = _discover_harness_traj_files(traj_root)

    items: List[Dict[str, Any]] = []
    for case_path in case_files:
        case_stem = case_path.stem
        rubric_name = f"{case_stem}_rubric.json"
        rubric_path = rubric_files.get(rubric_name)
        traj_path = traj_files.get(case_stem)
        if rubric_path is None or traj_path is None:
            continue

        rel_case_path = case_path.relative_to(case_root)
        try:
            rel_traj_path = traj_path.relative_to(traj_root).as_posix()
        except ValueError:
            rel_traj_path = traj_path.name
        items.append(
            {
                "spec_index": len(items),
                "case_id": f"judge_case_{len(items) + 1:05d}",
                "case_stem": case_stem,
                "case_path": str(case_path.resolve()),
                "relative_case_path": rel_case_path.as_posix(),
                "rubric_path": str(rubric_path.resolve()),
                "relative_rubric_path": rubric_name,
                "traj_path": str(traj_path.resolve()),
                "relative_traj_path": rel_traj_path,
                "relative_result_path": f"{case_stem}_result.json",
            }
        )

    if not items:
        raise ValueError(f"No aligned case/rubric/harness-traj triples found under {case_root}")

    return {
        "case_root": str(case_root.resolve()),
        "rubric_root": str(rubric_root.resolve()),
        "traj_root": str(traj_root.resolve()),
        "result_output_root": str(output_root.resolve()),
        "trajectory_adapter": "harness_json_jsonl_to_standard_steps",
        "items": items,
    }


class HarnessPersistentJudgeExecutor(PersistentJudgeExecutor):
    def run_case(
        self,
        *,
        case_path: Path,
        rubric_path: Path,
        traj_path: Path,
        result_path: Path,
        trace_dir: Path,
    ) -> Dict[str, Any]:
        trace_dir.mkdir(parents=True, exist_ok=True)
        normalized_traj_path = normalize_harness_traj(traj_path, trace_dir / "normalized_traj_for_judge.json")
        request = self.runner.build_judge_request(
            case_path=str(case_path),
            traj_path=str(normalized_traj_path),
            rubric_path=str(rubric_path),
        )
        case_name = str(request["case_name"])
        rubric_pack = request["rubric_pack"]
        judge_prompt = str(request["user_prompt"])
        prompt_path = trace_dir / "judge_prompt.txt"

        judge_models = self.settings.resolved_judge_models()
        result_is_newer_than_traj = _result_is_newer_than_traj(result_path, traj_path)
        if result_is_newer_than_traj:
            existing = _read_json_or(result_path, {})
            if self._result_looks_complete(existing, case_name, len(judge_models)):
                return {
                    "case_name": case_name,
                    "result_path": str(result_path),
                    "result": existing,
                }
        _atomic_write_text(prompt_path, judge_prompt)
        reuse_saved_judge_artifacts = not result_path.exists()

        messages = [
            {"role": "system", "content": request["system_prompt"]},
            {"role": "user", "content": judge_prompt},
        ]

        judge_outputs: List[Dict[str, Any]] = []
        for model in judge_models:
            trace_tag = f"judge_{model.replace('/', '_')}"
            if reuse_saved_judge_artifacts:
                saved_final = self._load_saved_final(
                    trace_dir,
                    trace_tag,
                    case_name=case_name,
                    rubric_pack=rubric_pack,
                )
                if saved_final is not None:
                    judge_outputs.append({"model": model, "judgment": saved_final})
                    continue

            saw_api_error = False
            last_api_error = ""
            last_invalid_error = "unknown invalid judge output"

            for attempt in range(1, self.settings.max_json_retries + 1):
                saved = (
                    self._load_saved_attempt(trace_dir, trace_tag, attempt)
                    if reuse_saved_judge_artifacts
                    else None
                )
                if saved is None:
                    resp = self.runner._chat_once(
                        model,
                        messages,
                        max_tokens=self.settings.max_tokens,
                        temperature=self.settings.temperature,
                    )
                    raw = str(resp.get("content", "") or "") if isinstance(resp, dict) else ""
                    self._save_attempt(trace_dir, trace_tag, attempt, resp, raw)
                else:
                    resp = saved["resp"]
                    raw = saved["raw"]

                if not bool(resp.get("ok", False)) and str(resp.get("error", "")).strip():
                    saw_api_error = True
                    last_api_error = str(resp.get("error", "")).strip()
                    continue

                parsed = self.runner._parse_json_content(raw)
                if parsed is None:
                    last_invalid_error = "judge response is not valid JSON"
                    continue

                if not self.runner._validate_judgment(parsed, case_name, rubric_pack):
                    last_invalid_error = "judge parsed JSON does not satisfy judgment schema"
                    invalid_path = self._attempt_invalid_path(trace_dir, trace_tag, attempt)
                    if not invalid_path.exists():
                        _atomic_write_json(invalid_path, parsed)
                    continue

                _atomic_write_json(self._final_path(trace_dir, trace_tag), parsed)
                judge_outputs.append({"model": model, "judgment": parsed})
                break
            else:
                if saw_api_error:
                    raise BatchRecoverableAPIError(
                        kind=_classify_llm_error(last_api_error),
                        message=last_api_error,
                        stage_name=trace_tag,
                    )
                raise ValueError(
                    f"Judgment failed after {self.settings.max_json_retries} JSON attempts for {model}: {last_invalid_error}"
                )

        result = {
            "module": "ValueEval_judge",
            "generated_at_utc": _now_iso(),
            "case_path": str(case_path),
            "traj_path": str(traj_path),
            "normalized_traj_path": str(normalized_traj_path),
            "case_name": case_name,
            "rubric_path": str(rubric_path),
            "judge_outputs": judge_outputs,
        }
        ensure_dir(result_path.parent)
        _atomic_write_json(result_path, result)
        result["result_path"] = str(result_path.resolve())
        return {
            "case_name": case_name,
            "result_path": str(result_path),
            "result": result,
        }


class HarnessBatchJudgeCoordinator(BatchJudgeCoordinator):
    def __init__(self, *, run_dir: Path, settings: JudgeBatchSettings) -> None:
        self.run_dir = run_dir
        self.settings = settings
        self.master_lock = FileLock(self.run_dir / "master.lock")
        self.state_lock = threading.RLock()
        self.stop_event = threading.Event()
        self.workers: List[threading.Thread] = []
        self.plan_bundle = build_harness_judge_plan(
            case_root=settings.cases_dir,
            rubric_root=settings.rubric_dir,
            traj_root=settings.traj_dir,
            result_output_dir_name=settings.result_output_dir_name,
        )
        self.plan = self.plan_bundle["items"]
        self.plan_by_case_id = {str(item["case_id"]): item for item in self.plan}
        self.output_root = Path(self.plan_bundle["result_output_root"])
        self.slot_order: List[str] = []
        self.slot_states: Dict[str, Dict[str, Any]] = {}
        self.home_slot_configs: Dict[str, Dict[str, str]] = {}
        self.resource_order: List[str] = []
        self.resource_states: Dict[str, Dict[str, Any]] = {}
        self.case_states: Dict[str, Dict[str, Any]] = {}
        self.pending_case_ids = deque()
        self._slot_states_dirty = False
        self._resource_states_dirty = False
        self._replacement_cursor = 0
        ensure_dir(self.run_dir / "cases")
        ensure_dir(self.output_root)

    def _build_executor_for_slot(self, slot_state: Dict[str, Any]) -> HarnessPersistentJudgeExecutor:
        config = slot_state.get("config", {}) if isinstance(slot_state, dict) else {}
        settings = ValueEvalSettings(
            api_key=str(config.get("api_key") or ""),
            base_url=str(config.get("base_url") or ""),
            judge_models=list(self.settings.judge_models),
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            timeout_seconds=self.settings.timeout_seconds,
            network_max_retries=self.settings.network_max_retries,
            max_json_retries=self.settings.max_json_retries,
        )
        return HarnessPersistentJudgeExecutor(settings=settings)


def main() -> int:
    parser = build_run_parser()
    args = parser.parse_args()
    settings = JudgeBatchSettings(
        api_slots_json=Path(args.api_slots_json),
        cases_dir=Path(args.cases_dir),
        rubric_dir=Path(args.rubric_dir),
        traj_dir=Path(args.traj_dir),
        result_output_dir_name=str(args.result_output_dir_name),
        judge_models=_parse_models(args.judge_models),
        temperature=float(args.temperature),
        max_tokens=int(args.max_tokens),
        timeout_seconds=int(args.timeout_seconds),
        network_max_retries=int(args.network_max_retries),
        max_json_retries=int(args.max_json_retries),
        resume=bool(args.resume),
    )
    coordinator = HarnessBatchJudgeCoordinator(
        run_dir=RUNS_ROOT / str(args.run_name).strip(),
        settings=settings,
    )
    coordinator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
