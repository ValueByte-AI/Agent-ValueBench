"""Rubric-based trajectory judgment for Agent-ValueBench."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config import LLMConfig
from core.json_utils import extract_json_candidate
from core.llm_client import UnifiedLLMClient

from .prompts import TRAJECTORY_JUDGE_PROMPT


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class ValueEvalSettings:
    api_key: str = ""
    base_url: str = ""

    # Judge model list
    judge_models: Optional[List[str]] = None

    temperature: float = 0.0
    max_tokens: int = 8000
    timeout_seconds: int = 180
    network_max_retries: int = 2

    # JSON parse retry limit
    max_json_retries: int = 4

    def resolved_judge_models(self) -> List[str]:
        if self.judge_models:
            return self.judge_models
        raise ValueError("At least one judge model must be provided.")


class RubricTrajectoryJudge:
    def __init__(
        self,
        settings: Optional[ValueEvalSettings] = None,
        chat_override: Optional[Callable[[str, List[Dict[str, str]], int, float], Dict[str, Any]]] = None,
    ) -> None:
        self.settings = settings or ValueEvalSettings()
        self._chat_override = chat_override
        self.repo_root = Path(__file__).resolve().parents[1]
        self.module_dir = Path(__file__).resolve().parent

    # ---------------------------
    # LLM / JSON helpers
    # ---------------------------
    def _chat_once(
        self,
        model: str,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        if self._chat_override is not None:
            return self._chat_override(model, messages, max_tokens, temperature)

        cfg = LLMConfig(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            model=model,
            timeout_seconds=self.settings.timeout_seconds,
            max_retries=self.settings.network_max_retries,
        )
        client = UnifiedLLMClient(cfg)
        return client.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

    @staticmethod
    def _parse_json_content(raw_content: str) -> Optional[Dict[str, Any]]:
        content = (raw_content or "").strip()
        if not content:
            return None

        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        candidate = extract_json_candidate(content)
        if not candidate:
            return None

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

        return None

    def _call_json_with_retry(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        validator: Callable[[Dict[str, Any]], bool],
        output_trace_dir: Optional[Path],
        trace_tag: str,
    ) -> Optional[Dict[str, Any]]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if output_trace_dir is not None:
            output_trace_dir.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.settings.max_json_retries + 1):
            res = self._chat_once(
                model,
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            raw = ""
            if isinstance(res, dict):
                raw = str(res.get("content", "") or "")

            if output_trace_dir is not None:
                (output_trace_dir / f"{trace_tag}_attempt_{attempt}_raw.txt").write_text(raw, encoding="utf-8")
                (output_trace_dir / f"{trace_tag}_attempt_{attempt}_resp.json").write_text(
                    json.dumps(res, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

            if not res.get("ok", False):
                continue

            parsed = self._parse_json_content(raw)
            if parsed is None:
                continue

            if not validator(parsed):
                if output_trace_dir is not None:
                    (output_trace_dir / f"{trace_tag}_attempt_{attempt}_parsed_invalid.json").write_text(
                        json.dumps(parsed, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                continue

            if output_trace_dir is not None:
                (output_trace_dir / f"{trace_tag}_final.json").write_text(
                    json.dumps(parsed, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return parsed

        return None

    # ---------------------------
    # Validators
    # ---------------------------
    @staticmethod
    def _validate_judgment(
        payload: Dict[str, Any],
        expected_case_name: str,
        rubric_pack: Dict[str, Any],
    ) -> bool:
        if str(payload.get("CASE_NAME", "")).strip() != expected_case_name:
            return False

        rubric_status = str(payload.get("RUBRIC_STATUS", "")).strip().upper()
        if rubric_status not in {"OK", "UNSCORABLE"}:
            return False

        rubric_pack_status = str(rubric_pack.get("STATUS", "")).strip().upper()
        if rubric_status != rubric_pack_status:
            return False

        if rubric_status == "UNSCORABLE":
            return isinstance(payload.get("REASON"), str) and bool(payload.get("REASON").strip())

        item_scores = payload.get("ITEM_SCORES")
        if not isinstance(item_scores, list):
            return False

        expected_items: List[Dict[str, Any]] = []
        expected_items.extend(rubric_pack.get("VALUE_A_ITEMS", []))
        expected_items.extend(rubric_pack.get("VALUE_B_ITEMS", []))

        if len(item_scores) != len(expected_items):
            return False

        for judged, expected in zip(item_scores, expected_items):
            if not isinstance(judged, dict):
                return False
            if str(judged.get("ITEM_ID", "")).strip() != str(expected.get("ITEM_ID", "")).strip():
                return False
            if str(judged.get("SOURCE_CHECKPOINT", "")).strip() != str(expected.get("SOURCE_CHECKPOINT", "")).strip():
                return False
            score = str(judged.get("SCORE", "")).strip()
            if score not in {"0", "1", "2"}:
                return False
            if not isinstance(judged.get("EVIDENCE_STEPS"), list):
                return False
            if not isinstance(judged.get("RATIONALE"), str) or not judged.get("RATIONALE").strip():
                return False

        for key in [
            "VALUE_A_TRACK_SUMMARY",
            "VALUE_B_TRACK_SUMMARY",
            "QUALITATIVE_OVERALL_LEANING",
            "OVERALL_CONFIDENCE",
        ]:
            if not isinstance(payload.get(key), str) or not payload.get(key).strip():
                return False

        if payload["QUALITATIVE_OVERALL_LEANING"] not in {
            "VALUE_A_LEANING",
            "VALUE_B_LEANING",
            "MIXED",
            "INSUFFICIENT_EVIDENCE",
        }:
            return False

        if payload["OVERALL_CONFIDENCE"] not in {"HIGH", "MEDIUM", "LOW"}:
            return False

        return True

    # ---------------------------
    # Data preparation
    # ---------------------------
    def _load_case(self, case_path: Path) -> Dict[str, Any]:
        return json.loads(case_path.read_text(encoding="utf-8"))

    def _load_traj(self, traj_path: Path) -> Dict[str, Any]:
        return json.loads(traj_path.read_text(encoding="utf-8"))

    def _load_env_json(self, env_name: str) -> Dict[str, Any]:
        env_path = self.repo_root / "environment" / f"{env_name}.json"
        if not env_path.exists():
            raise FileNotFoundError(f"Environment json not found: {env_path}")
        return json.loads(env_path.read_text(encoding="utf-8"))

    def _load_value_definitions(self, value_system: str) -> Dict[str, str]:
        cfg_path = self.repo_root / "configs" / "value_systems.json"
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        if value_system not in data:
            raise KeyError(f"value_system not found in definitions file: {value_system}")

        values = data[value_system].get("values", [])
        mapping: Dict[str, str] = {}
        for item in values:
            if isinstance(item, dict) and "value" in item and "definition" in item:
                mapping[str(item["value"])] = str(item["definition"])
        return mapping

    @staticmethod
    def _format_available_tools(case: Dict[str, Any], env_json: Dict[str, Any]) -> str:
        chosen_tools = [str(x) for x in case.get("function_list", [])]
        tool_map: Dict[str, Dict[str, Any]] = {
            str(t.get("name")): t for t in env_json.get("tools", []) if isinstance(t, dict)
        }
        lines: List[str] = []
        for name in chosen_tools:
            info = tool_map.get(name, {})
            desc = str(info.get("description", "")).strip()
            if not desc:
                lines.append(f"{name}: <missing description>")
                continue
            lines.append(f"{name}: {desc}")
        return "\n".join(lines)

    @staticmethod
    def _format_checkpoints(checkpoints: List[Dict[str, Any]]) -> str:
        chunks: List[str] = []
        for cp in checkpoints:
            cp_id = str(cp.get("checkpoint_id", ""))
            cp_name = str(cp.get("checkpoint_name", ""))
            funcs = ", ".join(str(x) for x in cp.get("related_functions", []))
            why = str(cp.get("why_it_matters", ""))
            actions = cp.get("expected_actions", [])
            signal = str(cp.get("expected_signal", ""))
            action_lines = " | ".join(str(a) for a in actions)
            chunks.append(
                "\n".join(
                    [
                        f"- checkpoint_id: {cp_id}",
                        f"  checkpoint_name: {cp_name}",
                        f"  related_functions: {funcs}",
                        f"  why_it_matters: {why}",
                        f"  expected_actions: {action_lines}",
                        f"  expected_signal: {signal}",
                    ]
                )
            )
        return "\n".join(chunks)

    @staticmethod
    def _assistant_message_for_judge(assistant_message: Any) -> Any:
        if not isinstance(assistant_message, dict):
            return assistant_message
        return {k: v for k, v in assistant_message.items() if k != "reasoning_details"}

    @staticmethod
    def _format_full_trajectory(traj: Dict[str, Any]) -> str:
        steps = traj.get("steps", [])
        lines: List[str] = []
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            step_id = step.get("step")
            if step_id is None:
                step_id = step.get("step_id")
            if step_id is None:
                step_id = f"s{idx}"

            lines.append(f"STEP_ID: {step_id}")
            if "assistant_message" in step:
                assistant_message = RubricTrajectoryJudge._assistant_message_for_judge(step.get("assistant_message", None))
                lines.append(f"ASSISTANT_MESSAGE: {json.dumps(assistant_message, ensure_ascii=False)}")
            else:
                lines.append(f"ASSISTANT_OUTPUT: {json.dumps(step.get('assistant_output', ''), ensure_ascii=False)}")
            tool_calls = step.get("tool_calls")
            tool_responses = step.get("tool_responses")
            has_native_tool_fields = ("tool_calls" in step) or ("tool_responses" in step)
            if isinstance(tool_calls, list) and tool_calls:
                lines.append(f"TOOL_CALLS: {json.dumps(tool_calls, ensure_ascii=False)}")
                lines.append(
                    f"TOOL_RESPONSES: {json.dumps(tool_responses if isinstance(tool_responses, list) else [], ensure_ascii=False)}"
                )
            elif not has_native_tool_fields:
                lines.append(f"TOOL_CALL: {json.dumps(step.get('tool_call', None), ensure_ascii=False)}")
                lines.append(f"TOOL_RESPONSE: {json.dumps(step.get('tool_response', None), ensure_ascii=False)}")
            lines.append("---")

        if not lines:
            trajectory_text = str(traj.get("trajectory_text", ""))
            if trajectory_text:
                return trajectory_text
        return "\n".join(lines)

    def _build_case_context(self, case_path: str) -> Dict[str, Any]:
        case_fp = Path(case_path)
        case = self._load_case(case_fp)

        case_name = str(case.get("case_name", "")).strip()
        if not case_name:
            raise ValueError("case_name is required")

        value_items = case.get("value_items", [])
        if not isinstance(value_items, list) or len(value_items) != 2:
            raise ValueError("case.value_items must contain exactly 2 values")

        value_a_name = str(value_items[0])
        value_b_name = str(value_items[1])
        value_system_name = str(case.get("value_system", "")).strip()
        if not value_system_name:
            raise ValueError("case.value_system is required")

        value_defs = self._load_value_definitions(value_system_name)
        value_a_def = value_defs.get(value_a_name)
        value_b_def = value_defs.get(value_b_name)
        if not value_a_def or not value_b_def:
            raise KeyError("Value definition missing in configs/value_systems.json")

        env_name = str(case.get("environment", "")).strip()
        if not env_name:
            raise ValueError("case.environment is required")

        env_json = self._load_env_json(env_name)

        task_description = str(case.get("task_description", "")).strip()
        if not task_description:
            raise ValueError("case.task_description is required")

        value_a_cps = case.get("value_a_checkpoint_list", [])
        value_b_cps = case.get("value_b_checkpoint_list", [])
        if not isinstance(value_a_cps, list) or not isinstance(value_b_cps, list):
            raise ValueError("value_a_checkpoint_list and value_b_checkpoint_list must be lists")

        return {
            "case_path": str(case_fp),
            "case": case,
            "case_name": case_name,
            "value_system_name": value_system_name,
            "value_a_name": value_a_name,
            "value_b_name": value_b_name,
            "value_a_definition": value_a_def,
            "value_b_definition": value_b_def,
            "task_description": task_description,
            "tools_text": self._format_available_tools(case, env_json),
            "value_a_checkpoints_text": self._format_checkpoints(value_a_cps),
            "value_b_checkpoints_text": self._format_checkpoints(value_b_cps),
        }

    @staticmethod
    def _judge_system_prompt() -> str:
        return "You are a strict JSON generator. Output only valid JSON."

    def build_judge_request(
        self,
        *,
        case_path: str,
        traj_path: str,
        rubric_path: Optional[str] = None,
        rubric_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self._build_case_context(case_path)
        case_name = context["case_name"]

        resolved_rubric_path: Path
        if rubric_path:
            resolved_rubric_path = Path(rubric_path)
        else:
            rubric_root = Path(rubric_dir) if rubric_dir else (self.module_dir / "rubric")
            resolved_rubric_path = rubric_root / f"{case_name}_rubric.json"

        if not resolved_rubric_path.exists():
            raise FileNotFoundError(f"Rubric json not found: {resolved_rubric_path}")

        rubric_pack = json.loads(resolved_rubric_path.read_text(encoding="utf-8"))
        if str(rubric_pack.get("CASE_NAME", "")).strip() != case_name:
            raise ValueError("Rubric CASE_NAME does not match case_name")

        traj_fp = Path(traj_path)
        traj = self._load_traj(traj_fp)
        trajectory_text = self._format_full_trajectory(traj)

        judge_prompt = TRAJECTORY_JUDGE_PROMPT.format(
            case_name=case_name,
            frozen_rubric_pack_json=json.dumps(rubric_pack, ensure_ascii=False, indent=2),
            full_trajectory_text=trajectory_text,
        )
        return {
            "context": context,
            "case_name": case_name,
            "traj_path": str(traj_fp),
            "resolved_rubric_path": str(resolved_rubric_path),
            "rubric_pack": rubric_pack,
            "system_prompt": self._judge_system_prompt(),
            "user_prompt": judge_prompt,
        }

    # ---------------------------
    # Judgment API
    # ---------------------------
    def judge_with_saved_rubric(
        self,
        *,
        case_path: str,
        traj_path: str,
        rubric_path: Optional[str] = None,
        rubric_dir: Optional[str] = None,
        result_dir: Optional[str] = None,
        trace_dir: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        request = self.build_judge_request(
            case_path=case_path,
            traj_path=traj_path,
            rubric_path=rubric_path,
            rubric_dir=rubric_dir,
        )
        context = request["context"]
        case_name = request["case_name"]
        traj_fp = Path(request["traj_path"])
        resolved_rubric_path = Path(request["resolved_rubric_path"])
        rubric_pack = request["rubric_pack"]
        judge_prompt = request["user_prompt"]

        trace_path: Optional[Path] = Path(trace_dir) if trace_dir else None
        if trace_path is not None:
            trace_path.mkdir(parents=True, exist_ok=True)
            (trace_path / "judge_prompt.txt").write_text(judge_prompt, encoding="utf-8")

        judge_outputs: List[Dict[str, Any]] = []
        for model in self.settings.resolved_judge_models():
            judgment = self._call_json_with_retry(
                model=model,
                system_prompt=request["system_prompt"],
                user_prompt=judge_prompt,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                validator=lambda payload, _case=case_name, _rubric=rubric_pack: self._validate_judgment(
                    payload, _case, _rubric
                ),
                output_trace_dir=trace_path,
                trace_tag=f"judge_{model.replace('/', '_')}",
            )
            if judgment is None:
                return None
            judge_outputs.append({"model": model, "judgment": judgment})

        result: Dict[str, Any] = {
            "module": "ValueEval_judge",
            "generated_at_utc": _utc_now(),
            "case_path": context["case_path"],
            "traj_path": str(traj_fp),
            "case_name": case_name,
            "rubric_path": str(resolved_rubric_path.resolve()),
            "judge_outputs": judge_outputs,
        }

        result_root = Path(result_dir) if result_dir else (self.module_dir / "result")
        result_root.mkdir(parents=True, exist_ok=True)
        result_path = result_root / f"{case_name}.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["result_path"] = str(result_path.resolve())
        return result
