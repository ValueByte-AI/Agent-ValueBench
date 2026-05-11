"""Fallback/local and safe dual-LLM agents for Stage3-REFINE."""

from __future__ import annotations

from typing import Any, Dict, List

from stage3_refine.verification.func_call_agent import (
    get_brief_tool_info,
    get_tool_info,
    input_template as dual_fc_input_template,
    parse_response as dual_fc_parse_response,
    system_prompt as dual_fc_system_prompt,
)
from stage3_refine.verification.check_agent import input_template as dual_check_input_template
from utils.call_llm import llm_inference


def _default_positive_value(type_name: str) -> Any:
    t = (type_name or "").lower()
    if "int" in t:
        return 1
    if "float" in t or "double" in t or "number" in t:
        return 1.0
    if "bool" in t:
        return True
    if "list" in t or "array" in t:
        return []
    if "dict" in t or "object" in t or "map" in t:
        return {}
    return "demo_value"


def _default_negative_value(type_name: str) -> Any:
    t = (type_name or "").lower()
    if "int" in t or "float" in t or "number" in t:
        return "not_a_number"
    if "bool" in t:
        return "not_bool"
    if "list" in t or "array" in t:
        return "not_a_list"
    if "dict" in t or "object" in t or "map" in t:
        return "not_a_dict"
    return None


class LocalFuncCallAgent:
    """A deterministic local replacement for FuncCallAgent."""

    def __init__(self, env_item: Dict[str, Any]):
        self.env_item = env_item
        self.tool_names = list(env_item.get("env_func_details", {}).keys())
        self._cursor = 0
        self._round = 0
        self.stats = {
            name: {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "pass": 0,
                "warning": 0,
                "fail": 0,
            }
            for name in self.tool_names
        }

    def _build_params(self, tool_name: str, case_type: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        detail = self.env_item.get("env_func_details", {}).get(tool_name, {})
        signature = detail.get("signature", {})
        fields: List[Dict[str, Any]] = signature.get("parameters", [])
        for field in fields:
            name = field.get("name")
            field_type = field.get("type", "")
            if case_type == "negative":
                params[name] = _default_negative_value(field_type)
            else:
                params[name] = _default_positive_value(field_type)
        return params

    def gen_func_call_request(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        del current_state
        if not self.tool_names:
            return {"tool_name": "__missing_tool__", "parameters": {}, "case_type": "negative"}
        tool_name = self.tool_names[self._cursor % len(self.tool_names)]
        self._cursor += 1
        case_type = "positive" if self._round % 2 == 0 else "negative"
        self._round += 1
        params = self._build_params(tool_name, case_type)
        return {"tool_name": tool_name, "parameters": params, "case_type": case_type}

    def update_stats(self, tool_name: str, case_type: str, check_result: str) -> None:
        entry = self.stats.setdefault(
            tool_name,
            {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "pass": 0,
                "warning": 0,
                "fail": 0,
            },
        )
        entry["total"] += 1
        if case_type == "positive":
            entry["positive"] += 1
        elif case_type == "negative":
            entry["negative"] += 1
        if check_result in ("pass", "warning", "fail"):
            entry[check_result] += 1

    def get_stats_table_str(self) -> str:
        lines = ["Tool | Total | Negative | Positive | Pass | Warning | Fail"]
        for tool, stats in self.stats.items():
            lines.append(
                f"{tool} | {stats['total']} | {stats['negative']} | {stats['positive']} | "
                f"{stats['pass']} | {stats['warning']} | {stats['fail']}"
            )
        return "\n".join(lines)


class LocalCheckAgent:
    """A deterministic local replacement for CheckAgent."""

    def __init__(self) -> None:
        pass

    def check_func_call(
        self,
        func_name: str,
        state_before_call: Dict[str, Any],
        func_params: Dict[str, Any],
        func_return: Any,
        state_after_call: Dict[str, Any],
        state_diff: Dict[str, Any],
    ) -> Dict[str, str]:
        del func_name, state_before_call, func_params, state_after_call, state_diff

        if isinstance(func_return, dict):
            err = str(func_return.get("error", ""))
            if "<Exception>" in err or "Traceback" in err:
                return {
                    "analysis": "Environment call raised runtime exception in wrapper.",
                    "result": "Fail",
                    "error_reason": err or "Runtime exception.",
                }
            if "success" in func_return:
                if func_return.get("success") is True:
                    return {
                        "analysis": "Return protocol is valid and success=True.",
                        "result": "Pass",
                        "error_reason": "No error",
                    }
                return {
                    "analysis": "Return protocol is valid with success=False.",
                    "result": "Warning",
                    "error_reason": "Method returned controlled error path.",
                }
            return {
                "analysis": "Return is dict but missing success field.",
                "result": "Warning",
                "error_reason": "Return protocol instability: missing success.",
            }

        return {
            "analysis": "Return is non-dict and violates expected contract.",
            "result": "Fail",
            "error_reason": "Return value must be dict with success field.",
        }


class SafeDualFuncCallAgent:
    """LLM-based function-call generator with bounded retries."""

    def __init__(self, model: str, temperature: float, env_item: Dict[str, Any]):
        self.model = model
        self.temperature = temperature
        self.env_item = env_item
        self.tool_info = get_tool_info(env_item)
        self.brief_tool_info = get_brief_tool_info(env_item)
        self.tool_names = list(env_item.get("env_func_details", {}).keys())
        self.stats = {
            tool_name: {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "pass": 0,
                "warning": 0,
                "fail": 0,
            }
            for tool_name in self.tool_names
        }
        self.system_prompt = dual_fc_system_prompt.format(
            env_introduction=env_item.get("environment_introduction", ""),
            tool_info=self.tool_info,
        )

    def update_stats(self, tool_name: str, case_type: str, check_result: str) -> None:
        entry = self.stats.setdefault(
            tool_name,
            {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "pass": 0,
                "warning": 0,
                "fail": 0,
            },
        )
        entry["total"] += 1
        if case_type == "positive":
            entry["positive"] += 1
        elif case_type == "negative":
            entry["negative"] += 1
        if check_result in ("pass", "warning", "fail"):
            entry[check_result] += 1

    def get_stats_table_str(self) -> str:
        lines = ["Tool | Total | Negative | Positive | Pass | Warning | Fail"]
        for tool, d in self.stats.items():
            lines.append(
                f"{tool} | {d.get('total', 0)} | {d.get('negative', 0)} | {d.get('positive', 0)}"
                f" | {d.get('pass', 0)} | {d.get('warning', 0)} | {d.get('fail', 0)}"
            )
        return "\n".join(lines)

    def _build_input(self, current_state: Dict[str, Any]) -> str:
        return dual_fc_input_template.format(
            test_summary=self.get_stats_table_str(),
            current_state=current_state,
            tool_brief_info=self.brief_tool_info,
        )

    def _fallback_request(self) -> Dict[str, Any]:
        tool_name = self.tool_names[0] if self.tool_names else "__missing_tool__"
        return {"tool_name": tool_name, "parameters": {}, "case_type": "positive"}

    def gen_func_call_request(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        input_content = self._build_input(current_state)
        input_message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_content},
        ]
        max_try = 3
        for _ in range(max_try):
            response = llm_inference(
                provider="openai",
                model=self.model,
                temperature=self.temperature,
                messages=input_message,
                raise_on_failure=True,
            )
            parsed_success, func_call_request = dual_fc_parse_response(response)
            if parsed_success and isinstance(func_call_request, dict):
                tool_name = func_call_request.get("tool_name", "")
                if tool_name in self.tool_names:
                    return func_call_request
        return self._fallback_request()


class SafeDualCheckAgent:
    """LLM-based checker with bounded retries and robust parser."""

    def __init__(self, model: str, temperature: float, env_item: Dict[str, Any]):
        self.model = model
        self.temperature = temperature
        self.env_info = {
            "env_introduction": env_item.get("environment_introduction", ""),
            "env_rules": "\n".join([f"- {r}" for r in env_item.get("constraints_rules", [])]),
            "env_class_def": env_item.get("env_class_def", ""),
        }
        self.func_source_map = {
            fn: detail.get("source_code", "")
            for fn, detail in env_item.get("env_func_details", {}).items()
        }

    def _format_input(
        self,
        func_name: str,
        state_before_call: Dict[str, Any],
        func_params: Dict[str, Any],
        func_return: Any,
        state_after_call: Dict[str, Any],
        state_diff: Dict[str, Any],
    ) -> str:
        return dual_check_input_template.format(
            env_introduction=self.env_info["env_introduction"],
            env_rules=self.env_info["env_rules"],
            env_class_def=self.env_info["env_class_def"],
            func_name=func_name,
            func_source=self.func_source_map.get(func_name, ""),
            func_params=func_params,
            func_return=func_return,
            state_before_call=state_before_call,
            state_after_call=state_after_call,
            state_diff=state_diff,
        )

    @staticmethod
    def _parse_response(response: str) -> Dict[str, str]:
        text = response or ""
        analysis = ""
        result = ""
        error_reason = ""

        if "[Analysis]" in text and "[Result]" in text:
            analysis = text.split("[Analysis]", 1)[1].split("[Result]", 1)[0].strip()
        if "[Result]" in text:
            tmp = text.split("[Result]", 1)[1]
            if "[Error Reason]" in tmp:
                result = tmp.split("[Error Reason]", 1)[0].strip()
                error_reason = tmp.split("[Error Reason]", 1)[1].strip()
            else:
                result = tmp.strip()
        result_lower = result.lower().strip()
        if "pass" == result_lower:
            result = "Pass"
        elif "warning" == result_lower:
            result = "Warning"
        elif "fail" == result_lower:
            result = "Fail"
        else:
            result = "Fail"
            if not error_reason:
                error_reason = "Unparseable check result."
        if not analysis:
            analysis = "No analysis parsed."
        if not error_reason and result == "Pass":
            error_reason = "No error"
        return {"analysis": analysis, "result": result, "error_reason": error_reason}

    def check_func_call(
        self,
        func_name: str,
        state_before_call: Dict[str, Any],
        func_params: Dict[str, Any],
        func_return: Any,
        state_after_call: Dict[str, Any],
        state_diff: Dict[str, Any],
    ) -> Dict[str, str]:
        input_content = self._format_input(
            func_name=func_name,
            state_before_call=state_before_call,
            func_params=func_params,
            func_return=func_return,
            state_after_call=state_after_call,
            state_diff=state_diff,
        )
        input_message = [{"role": "user", "content": input_content}]
        max_try = 5
        for _ in range(max_try):
            response = llm_inference(
                provider="openai",
                model=self.model,
                messages=input_message,
                temperature=self.temperature,
                raise_on_failure=True,
            )
            parsed = self._parse_response(response)
            if parsed.get("result", "").lower() in ("pass", "warning", "fail"):
                return parsed
        return {
            "analysis": "Check agent retries exhausted.",
            "result": "Fail",
            "error_reason": "Unable to parse valid checker response.",
        }
