# -*- coding: utf-8 -*-
"""
Base environment class for runtime Agent-ValueBench environments.

Design goals:
1. Load a paired single-file environment JSON containing description,
   initial_parameter_schema, optional initial parameters, and tools.
2. Keep compatibility with older JSON files whose top level is directly a tool list.
3. Provide shared parameter validation, type conversion, and tool-call dispatch.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Optional


class BaseEnv:
    def __init__(self) -> None:
        # Tool names only, used for quick availability checks.
        self.tool_list: List[str] = []
        # Human-readable environment description from JSON.
        self.env_description: str = ""
        # Initial-parameter schema from JSON.
        self.initial_parameter_schema: Dict[str, Any] = {}
        # Optional default initial parameters from JSON.
        self.default_initial_parameters: Dict[str, Any] = {}
        # Full tool schema list, one item per tool.
        self.tool_descs: List[Dict[str, Any]] = []

        class_name = self.__class__.__name__
        dir_path = os.path.dirname(__file__)
        json_path = os.path.join(dir_path, f"{class_name}.json")

        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Environment {class_name} is missing its paired JSON file: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Current JSON format:
        # {
        #   "env_name": "Bank",
        #   "description": "...",
        #   "initial_parameter_schema": {...},
        #   "initial_parameters": {...},  # optional
        #   "tools": [ ... ]
        # }
        if isinstance(raw, dict):
            self.env_description = raw.get("description", "")
            self.initial_parameter_schema = raw.get("initial_parameter_schema", {}) or {}
            self.default_initial_parameters = (
                raw.get("initial_parameters", {})
                or raw.get("default_initial_parameters", {})
                or {}
            )
            self.tool_descs = raw.get("tools", []) or []
        # Older JSON format: top-level tool list.
        elif isinstance(raw, list):
            self.tool_descs = raw
        else:
            raise ValueError(f"Invalid environment JSON structure: {json_path}")

        for tool_desc in self.tool_descs:
            name = tool_desc.get("name")
            if isinstance(name, str) and name:
                self.tool_list.append(name)

    def get_default_initial_parameters(self) -> Dict[str, Any]:
        """Return a deep copy of default initial parameters so callers cannot mutate shared defaults."""
        return copy.deepcopy(self.default_initial_parameters)

    def get_initial_parameter_schema(self) -> Dict[str, Any]:
        """Return a deep copy of the initial-parameter schema without instance values."""
        return copy.deepcopy(self.initial_parameter_schema)

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Shared tool-call entry point.

        Argument handling:
        1. Validate tool name.
        2. Validate required fields.
        3. Drop schema-undeclared extra fields to avoid failures from hallucinated arguments.
        4. Apply lightweight conversion based on JSON Schema type.
        5. Call the actual tool method and return its result.
        """
        arguments = arguments or {}

        if not hasattr(self, tool_name):
            return {"success": False, "message": f"Invalid tool name: {tool_name}"}

        try:
            tool_desc = self.get_tool_descs([tool_name])[0]
        except Exception as exc:
            return {"success": False, "message": str(exc)}

        parameters_schema = tool_desc.get("parameters", {}) or {}
        properties = parameters_schema.get("properties", {}) or {}
        required = parameters_schema.get("required", []) or []

        for req in required:
            if req not in arguments:
                return {
                    "success": False,
                    "message": f"Missing required parameter '{req}' for tool '{tool_name}'",
                }

        # Drop schema-undeclared fields.
        sanitized: Dict[str, Any] = {k: v for k, v in arguments.items() if k in properties}

        # Apply lightweight type conversion.
        for key, value in list(sanitized.items()):
            param_type = properties.get(key, {}).get("type")
            try:
                sanitized[key] = self._convert_type(value, param_type)
            except Exception:
                return {
                    "success": False,
                    "message": f"Parameter '{key}' should be '{param_type}'",
                }

        func = getattr(self, tool_name)
        try:
            result = func(**sanitized)
        except TypeError as exc:
            # Return a clear error when the Python signature and tool schema disagree.
            return {
                "success": False,
                "message": f"Tool '{tool_name}' parameter mismatch: {exc}",
            }
        except Exception as exc:
            return {
                "success": False,
                "message": f"Tool '{tool_name}' execution error: {exc}",
            }

        # Wrap non-dict tool outputs to keep upstream serialization stable.
        if not isinstance(result, dict):
            return {
                "success": True,
                "data": result,
                "message": "Tool returned non-dict result; wrapped by BaseEnv.",
            }
        return result

    def get_tool_descs(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        if not self.tool_descs:
            raise Exception(f"Environment {self.__class__.__name__} does not have tool descriptions")

        selected: List[Dict[str, Any]] = []
        for tool_name in tool_names:
            found = None
            for desc in self.tool_descs:
                if desc.get("name") == tool_name:
                    found = desc
                    break
            if found is None:
                raise Exception(f"Tool {tool_name} not found in Environment {self.__class__.__name__}")
            selected.append(found)
        return selected

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self.tool_list

    @staticmethod
    def _convert_type(value: Any, param_type: Optional[str]) -> Any:
        """
        Apply lightweight conversion based on the JSON Schema type.

        Notes:
        - This is not full JSON Schema validation for constructs such as oneOf/allOf.
        - Strict validation can be added here later with pydantic or jsonschema if needed.
        """
        if param_type is None:
            return value
        if param_type == "integer":
            return int(value)
        if param_type == "number":
            return float(value)
        if param_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)
        if param_type == "object":
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                return json.loads(value)
        if param_type == "array":
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return json.loads(value)
        # Return strings and unknown types unchanged.
        return value
