# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import time
import uuid
from typing import List, Dict, Any
import copy



class CompilerInfo(TypedDict):
    compiler_id: str
    language: str
    version: str
    path: str
    is_default: bool
    install_status: str

class ToolchainConfigInfo(TypedDict):
    toolchain_id: str
    list_of_compilers: List[str]  # compiler_ids
    default_compiler_per_language: Dict[str, str]  # language -> compiler_id
    environment_variables: Dict[str, str]

class PerformanceMetricInfo(TypedDict):
    metric_id: str
    type: str  # e.g., 'cpu', 'memory', 'network', 'bottleneck'
    timestamp: float
    value: float

class PerfMonitorAPIInfo(TypedDict):
    api_status: str
    supported_metrics: List[str]
    access_level: str

class WorkstationInfo(TypedDict):
    os_version: str
    hardware_specs: Dict[str, str]
    network_configuration: Dict[str, str]
    installed_tools: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        # Compilers installed on the workstation: {compiler_id: CompilerInfo}
        self.compilers: Dict[str, CompilerInfo] = {}
        # Toolchain configurations: {toolchain_id: ToolchainConfigInfo}
        self.toolchain_configurations: Dict[str, ToolchainConfigInfo] = {}
        # Performance metrics collected: {metric_id: PerformanceMetricInfo}
        self.performance_metrics: Dict[str, PerformanceMetricInfo] = {}
        # Performance monitor API and its state (singleton-like)
        self.perf_monitor_api: Optional[PerfMonitorAPIInfo] = None
        # Workstation properties (singleton-like)
        self.workstation: Optional[WorkstationInfo] = None

        # Constraints:
        # - Only compilers with install_status = "installed" are available for use.
        # - Each language can only have one default/latest compiler set in toolchain configuration.
        # - Performance metrics are collected at regular intervals and available for querying via API.
        # - Only supported metric types (cpu, memory, network, bottleneck) can be queried through PerfMonitorAPI.

    def _find_compiler_record(self, compiler_id: str):
        for dict_key, compiler in self.compilers.items():
            if dict_key == compiler_id or compiler.get("compiler_id") == compiler_id:
                return dict_key, compiler
        return None, None

    def _find_toolchain_record(self, toolchain_id: str):
        for dict_key, toolchain in self.toolchain_configurations.items():
            if dict_key == toolchain_id or toolchain.get("toolchain_id") == toolchain_id:
                return dict_key, toolchain
        return None, None

    def _is_perf_api_operational(self):
        if self.perf_monitor_api is None:
            return False
        return self.perf_monitor_api.get("api_status") in {"active", "operational", "active_peak_hours"}

    def _next_metric_timestamp(self):
        if not self.performance_metrics:
            return 1.0
        return max(metric.get("timestamp", 0) for metric in self.performance_metrics.values()) + 1.0

    def _generate_metric_id(self, metric_type: str):
        existing = sum(1 for metric in self.performance_metrics.values() if metric.get("type") == metric_type)
        return f"{metric_type}_metric_{existing + 1:04d}"

    def _deterministic_metric_value(self, metric_type: str):
        history = [
            metric for metric in self.performance_metrics.values()
            if metric.get("type") == metric_type
        ]
        if history:
            latest = max(history, key=lambda metric: metric.get("timestamp", 0))
            return latest.get("value", 0.0)
        defaults = {
            "cpu": 25.0,
            "memory": 4096.0,
            "network": 250.0,
            "bottleneck": 0.0,
            "build_time": 60.0,
        }
        return defaults.get(metric_type, 0.0)

    def list_installed_compilers(self) -> dict:
        """
        Get all compilers whose install_status is 'installed' across all languages.

        Returns:
            dict:
            - success (bool): True if the query was performed.
            - data (List[CompilerInfo]): List of installed compiler info dicts (can be empty if none installed).
        Constraints:
            - Only compilers with install_status == 'installed' are included in the result.
        """
        installed_compilers = [
            compiler for compiler in self.compilers.values()
            if compiler['install_status'] == 'installed'
        ]
        return {
            "success": True,
            "data": installed_compilers
        }

    def list_installed_compilers_by_language(self, language: str) -> dict:
        """
        Retrieve all compilers for the specified programming language that are currently installed.

        Args:
            language (str): The programming language to filter compilers by.

        Returns:
            dict: {
                "success": True,
                "data": List[CompilerInfo]
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only compilers where install_status == "installed" are returned.
            - Filters by exact match of the language attribute.
            - If language is empty or not a string, returns an error.
        """
        if not isinstance(language, str) or not language:
            return {"success": False, "error": "Invalid language parameter"}

        result = [
            compiler for compiler in self.compilers.values()
            if compiler["language"] == language and compiler["install_status"] == "installed"
        ]
        return {"success": True, "data": result}

    def get_compiler_versions_by_language(self, language: str) -> dict:
        """
        Retrieve all available versions of installed compilers for a specified programming language.

        Args:
            language (str): The programming language to query (e.g., 'C++', 'Python', 'Go').

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of compiler versions for the language (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Only compilers with install_status == "installed" are considered.
            - 'language' must be provided as a non-empty string.
        """
        if not isinstance(language, str) or not language.strip():
            return { "success": False, "error": "Invalid language parameter" }

        versions = [
            compiler_info["version"]
            for compiler_info in self.compilers.values()
            if compiler_info["install_status"] == "installed"
               and compiler_info["language"] == language
        ]
        return { "success": True, "data": versions }

    def get_default_compiler_for_language(self, language: str) -> dict:
        """
        Retrieve detailed info of the default compiler for a given language as set in the toolchain configuration.

        Args:
            language (str): Programming language name.

        Returns:
            dict:
                If found:
                    { "success": True, "data": CompilerInfo }
                If not found or any error (no config, language, or compiler not installed):
                    { "success": False, "error": str }
        Constraints:
            - Only compilers with install_status == "installed" are valid.
            - Each language can only have one default in toolchain config.
        """
        if not self.toolchain_configurations:
            return {"success": False, "error": "No toolchain configuration present"}

        for config in self.toolchain_configurations.values():
            defaults = config.get("default_compiler_per_language", {})
            compiler_id = defaults.get(language)
            if not compiler_id:
                continue  # Try next config

            _compiler_key, compiler_info = self._find_compiler_record(compiler_id)
            if not compiler_info:
                return {
                    "success": False,
                    "error": f"Default compiler '{compiler_id}' for language '{language}' not found in registry"
                }
            if compiler_info.get("install_status") != "installed":
                return {
                    "success": False,
                    "error": f"Default compiler for language '{language}' is not installed"
                }
            return {"success": True, "data": compiler_info}

        return {
            "success": False,
            "error": f"No default compiler set for language '{language}' in toolchain configuration"
        }

    def get_toolchain_configuration(self) -> dict:
        """
        Get the details of the current toolchain configuration(s), including environment variables and default compilers.

        Returns:
            dict: {
                "success": True,
                "data": List[ToolchainConfigInfo],  # All toolchain configurations (may be one or many)
            }
            or
            {
                "success": False,
                "error": str  # "No toolchain configuration available"
            }

        Constraints:
            - There must be at least one toolchain configuration present.
        """
        if not self.toolchain_configurations:
            return { "success": False, "error": "No toolchain configuration available" }

        data = list(self.toolchain_configurations.values())
        return { "success": True, "data": data }

    def get_perf_monitor_api_status(self) -> dict:
        """
        Return the operational status and settings of the PerfMonitorAPI, including supported metrics.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": PerfMonitorAPIInfo  # Full status/settings dict
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., PerfMonitorAPI status unavailable)
            }

        Constraints:
            - Returns status information only if PerfMonitorAPI is initialized.
        """
        if self.perf_monitor_api is None:
            return { "success": False, "error": "PerfMonitorAPI status unavailable" }
        return { "success": True, "data": self.perf_monitor_api }

    def list_supported_performance_metrics(self) -> dict:
        """
        List metric types currently supported by PerfMonitorAPI.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[str],  # Supported metric types (e.g., ['cpu', 'memory', ...])
                }
                - On failure: {
                    "success": False,
                    "error": str  # Description, e.g. PerfMonitorAPI is unavailable
                }

        Constraints:
            - PerfMonitorAPI must be initialized (not None).
            - Only returns the supported_metrics claimed by the API.
        """
        if self.perf_monitor_api is None:
            return {"success": False, "error": "PerfMonitorAPI status is not initialized"}

        supported_metrics = self.perf_monitor_api.get("supported_metrics", [])
        return {"success": True, "data": supported_metrics}

    def get_recent_performance_metric(self, metric_type: str) -> dict:
        """
        Retrieve the most recent performance metric of a given type (e.g., 'cpu', 'memory', 'network', 'bottleneck').

        Args:
            metric_type (str): The type of performance metric to retrieve.

        Returns:
            dict:
                success: True, with 'data' as the most recent PerformanceMetricInfo of the given type, or None if none exist.
                success: False, with 'error' message if API is not available, not operational, or metric type is unsupported.

        Constraints:
            - Only supported metric types (according to self.perf_monitor_api) can be queried.
            - PerfMonitorAPI must be present and operational.
        """
        if self.perf_monitor_api is None:
            return {"success": False, "error": "Performance Monitor API is not configured"}
        if not self._is_perf_api_operational():
            return {"success": False, "error": "Performance Monitor API is not operational"}
        if metric_type not in self.perf_monitor_api["supported_metrics"]:
            return {"success": False, "error": f"Metric type '{metric_type}' is not supported by PerfMonitorAPI"}

        filtered_metrics = [
            metric for metric in self.performance_metrics.values()
            if metric["type"] == metric_type
        ]

        if not filtered_metrics:
            return {"success": True, "data": None}

        most_recent_metric = max(filtered_metrics, key=lambda m: m["timestamp"])
        return {"success": True, "data": most_recent_metric}

    def get_performance_metric_history(self, metric_type: str) -> dict:
        """
        Retrieve the historical performance metric values for a given metric type (e.g., 'cpu', 'memory').

        Args:
            metric_type (str): The type of performance metric to query. Must be among supported metrics
                in the PerfMonitorAPI (e.g., 'cpu', 'memory', 'network', 'bottleneck').

        Returns:
            dict: 
                - On success:
                    {
                      "success": True,
                      "data": List[PerformanceMetricInfo],  # Sorted chronologically (by timestamp, asc)
                    }
                - On failure:
                    {
                      "success": False,
                      "error": str  # Reason for failure.
                    }

        Constraints:
            - PerfMonitorAPI must be present and operational.
            - Only metric types listed in PerfMonitorAPI['supported_metrics'] can be queried.
        """
        if not self.perf_monitor_api:
            return {"success": False, "error": "Performance monitor API not initialized"}

        if not self._is_perf_api_operational():
            return {"success": False, "error": "Performance monitor API is not active"}

        supported_metrics = self.perf_monitor_api.get('supported_metrics', [])
        if metric_type not in supported_metrics:
            return {"success": False, "error": f"Metric type '{metric_type}' is not supported"}

        metrics = [
            metric for metric in self.performance_metrics.values()
            if metric.get('type') == metric_type
        ]

        metrics.sort(key=lambda m: m.get('timestamp', 0))

        return {"success": True, "data": metrics}

    def get_workstation_info(self) -> dict:
        """
        Retrieve the current workstation's properties (OS version, hardware specs, network configuration, installed tools).

        Args:
            None

        Returns:
            dict:
              - success: True and data is a WorkstationInfo dict if available.
              - success: False and error message if workstation info is not available.

        Constraints:
            - No permission enforcement or constraints on this query.
            - Returns failure if workstation info is uninitialized.
        """
        if self.workstation is None:
            return { "success": False, "error": "Workstation info not available" }

        return { "success": True, "data": self.workstation }

    def set_default_compiler_for_language(
        self,
        toolchain_id: str,
        language: str,
        compiler_id: str
    ) -> dict:
        """
        Update the default compiler for a specific language in a toolchain configuration.

        Args:
            toolchain_id (str): The identifier for the toolchain configuration to update.
            language (str): The programming language (e.g. 'C++', 'Python', etc).
            compiler_id (str): The compiler to set as default for this language.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Default compiler for language <language> set to <compiler_id> in toolchain <toolchain_id>"
                  }
                - On failure: {
                    "success": False,
                    "error": <reason>
                  }

        Constraints:
            - Compiler must exist and have install_status == "installed".
            - Compiler must support the requested language.
            - Enforces one-default-per-language (just overwrite).
        """
        # Check toolchain exists
        toolchain_key, toolchain = self._find_toolchain_record(toolchain_id)
        if toolchain is None:
            return { "success": False, "error": f"Toolchain '{toolchain_id}' does not exist." }
    
        # Check compiler exists
        compiler_key, compiler = self._find_compiler_record(compiler_id)
        if compiler is None:
            return { "success": False, "error": f"Compiler '{compiler_id}' does not exist." }
    
        # Check that compiler is installed
        if compiler['install_status'] != "installed":
            return { "success": False, "error": f"Compiler '{compiler_id}' is not installed." }
    
        # Check that compiler supports this language
        if compiler['language'] != language:
            return { "success": False, "error": f"Compiler '{compiler_id}' does not support language '{language}'." }

        if compiler_id not in toolchain['list_of_compilers'] and compiler_key not in toolchain['list_of_compilers']:
            toolchain['list_of_compilers'].append(compiler_id)

        # Set default compiler for language
        toolchain['default_compiler_per_language'][language] = compiler_id
        self.toolchain_configurations[toolchain_key] = toolchain

        return {
            "success": True,
            "message": f"Default compiler for language '{language}' set to '{compiler_id}' in toolchain '{toolchain_id}'."
        }

    def install_compiler(
        self,
        compiler_id: str,
        language: str,
        version: str,
        path: str,
        is_default: bool = False
    ) -> dict:
        """
        Add a new compiler to the system and mark it as 'installed'.

        Args:
            compiler_id (str): Unique identifier for the compiler.
            language (str): Programming language this compiler supports.
            version (str): Version string of the compiler.
            path (str): Filesystem path to the compiler binary.
            is_default (bool, optional): Whether this compiler should be the default for its language. Defaults to False.

        Returns:
            dict: 
                On success: { "success": True, "message": "Compiler <compiler_id> installed successfully" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - compiler_id must be unique (cannot already exist).
            - install_status will be forcibly set to "installed".
            - All required fields must be present.
        """
        if compiler_id in self.compilers:
            return { "success": False, "error": f"Compiler with id '{compiler_id}' already exists." }

        new_compiler = {
            "compiler_id": compiler_id,
            "language": language,
            "version": version,
            "path": path,
            "is_default": is_default,
            "install_status": "installed"
        }
        self.compilers[compiler_id] = new_compiler

        return { "success": True, "message": f"Compiler '{compiler_id}' installed successfully" }

    def uninstall_compiler(self, compiler_id: str) -> dict:
        """
        Uninstall (deactivate) a compiler by marking its install_status as not 'installed'.

        Args:
            compiler_id (str): The ID of the compiler to uninstall.

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - message (str): On success, the operation message.
                - error (str): On failure, the error message.

        Constraints:
            - Only compilers with install_status = "installed" are available for use.
            - If the compiler does not exist, returns error.
            - If the compiler is already uninstalled (install_status != "installed"), returns error.
        """
        compiler_key, compiler_info = self._find_compiler_record(compiler_id)
        if compiler_info is None:
            return {"success": False, "error": "Compiler not found"}

        if compiler_info["install_status"] != "installed":
            return {"success": False, "error": "Compiler already uninstalled"}

        compiler_info["install_status"] = "uninstalled"
        self.compilers[compiler_key] = compiler_info

        canonical_id = compiler_info.get("compiler_id", compiler_id)
        for toolchain in self.toolchain_configurations.values():
            toolchain["list_of_compilers"] = [
                existing_id for existing_id in toolchain.get("list_of_compilers", [])
                if existing_id not in {compiler_key, canonical_id}
            ]
            defaults = toolchain.get("default_compiler_per_language", {})
            for language, default_id in list(defaults.items()):
                if default_id in {compiler_key, canonical_id}:
                    del defaults[language]

        return {"success": True, "message": f"Compiler {canonical_id} uninstalled"}

    def modify_toolchain_environment_variable(
        self,
        toolchain_id: str,
        variable_name: str,
        variable_value: str = None
    ) -> dict:
        """
        Add, update, or remove an environment variable in a toolchain configuration.

        Args:
            toolchain_id (str): ID of the toolchain configuration to modify.
            variable_name (str): The environment variable key to add/update/remove.
            variable_value (str|None): The new value for the variable. If None (or empty string), remove the variable.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": str  # description of the operation performed
                }
                - On failure: {
                    "success": False,
                    "error": str  # error description
                }

        Constraints:
            - toolchain_id must exist in toolchain_configurations.
            - variable_name must be a non-empty string.
            - If variable_value is None or "", interpret as removal.
            - If removal requested and variable does not exist, operation succeeds (no-op).
        """
        # Check if the toolchain exists
        toolchain_key, config = self._find_toolchain_record(toolchain_id)
        if config is None:
            return {"success": False, "error": "toolchain_id does not exist"}

        if not isinstance(variable_name, str) or not variable_name.strip():
            return {"success": False, "error": "variable_name must be a non-empty string"}

        env_vars = config.get("environment_variables", {})

        # Remove variable if variable_value is None or empty string
        if variable_value is None or variable_value == "":
            if variable_name in env_vars:
                del env_vars[variable_name]
                config["environment_variables"] = env_vars
                self.toolchain_configurations[toolchain_key] = config
                return {
                    "success": True,
                    "message": f'Environment variable "{variable_name}" removed from toolchain {toolchain_id}.'
                }
            else:
                # Idempotent: removing non-existent variable is still a success
                return {
                    "success": True,
                    "message": f'Environment variable "{variable_name}" did not exist in toolchain {toolchain_id} (no action needed).'
                }
        else:
            old_value = env_vars.get(variable_name)
            env_vars[variable_name] = variable_value
            config["environment_variables"] = env_vars
            self.toolchain_configurations[toolchain_key] = config
            if old_value is None:
                return {
                    "success": True,
                    "message": f'Environment variable "{variable_name}" added to toolchain {toolchain_id}.'
                }
            else:
                return {
                    "success": True,
                    "message": f'Environment variable "{variable_name}" updated in toolchain {toolchain_id}.'
                }

    def refresh_perf_monitor_api(self) -> dict:
        """
        Force the PerfMonitorAPI to re-initialize and update its status and supported metric types.

        Returns:
            dict: {
                "success": True,
                "message": "PerfMonitorAPI successfully refreshed and updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only supported metric types (cpu, memory, network, bottleneck) may be included in supported_metrics.
            - Re-initialization sets API status to 'active' and resets supported metrics to default supported types.
        """
        SUPPORTED_TYPES = ['cpu', 'memory', 'network', 'bottleneck']
        refreshed_api: PerfMonitorAPIInfo = {
            "api_status": "active",
            "supported_metrics": SUPPORTED_TYPES.copy(),
            "access_level": "full"  # Default to 'full' (could be changed if policy/versioning required).
        }
        self.perf_monitor_api = refreshed_api
        return {
            "success": True,
            "message": "PerfMonitorAPI successfully refreshed and updated."
        }


    def trigger_performance_metric_collection(self, metric_types: List[str]) -> dict:
        """
        Instantly collect a new data point for one or more specified metric types using the PerfMonitorAPI.

        Args:
            metric_types (List[str]): List of metric type strings to collect (e.g., ['cpu', 'memory']).

        Returns:
            dict: On success:
                  {
                      "success": True,
                      "message": "Collected new performance metrics: ...",
                      "collected_metrics": List[PerformanceMetricInfo]
                  }
                  On error:
                  {
                      "success": False,
                      "error": "<reason>"
                  }
        Constraints:
            - PerfMonitorAPI must be initialized and operational.
            - Only supported metric types can be collected.
            - At least one valid (supported) metric type must be provided.
        """
        if not self._is_perf_api_operational():
            return {
                "success": False,
                "error": "Performance Monitor API is not initialized or not operational."
            }
        if not metric_types or not isinstance(metric_types, list):
            return {
                "success": False,
                "error": "No metric types specified to collect."
            }
        supported = set(self.perf_monitor_api.get("supported_metrics", []))
        invalid = [m for m in metric_types if m not in supported]
        if invalid:
            return {
                "success": False,
                "error": f"Metric types not supported: {', '.join(invalid)}"
            }

        timestamp = self._next_metric_timestamp()
        collected = []
        for mtype in metric_types:
            metric_id = self._generate_metric_id(mtype)
            value = self._deterministic_metric_value(mtype)

            metric_info = {
                "metric_id": metric_id,
                "type": mtype,
                "timestamp": timestamp,
                "value": value,
            }
            self.performance_metrics[metric_id] = metric_info
            collected.append(metric_info)

        return {
            "success": True,
            "message": f"Collected new performance metrics: {', '.join(metric_types)}.",
            "collected_metrics": collected
        }

    def update_workstation_info(self, info_updates: dict) -> dict:
        """
        Update workstation information fields.
        Only updates fields present in WorkstationInfo; ignores non-existent fields.

        Args:
            info_updates (dict): Dictionary of workstation attributes to be updated
                (os_version, hardware_specs, network_configuration, installed_tools).

        Returns:
            dict:
                On success: { "success": True, "message": "Workstation info updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only recognized WorkstationInfo fields are updated.
            - Types must match: hardware_specs/network_configuration (dict), installed_tools (list), os_version (str).
            - If workstation info does not yet exist, initialize first.
        """
        # Define allowed fields and types
        WorkstationFields = {
            "os_version": str,
            "hardware_specs": dict,
            "network_configuration": dict,
            "installed_tools": list,
        }

        # Initialize if not already set
        if self.workstation is None:
            self.workstation = {
                "os_version": "",
                "hardware_specs": {},
                "network_configuration": {},
                "installed_tools": []
            }

        for key, value in info_updates.items():
            if key not in WorkstationFields:
                # Ignore unexpected keys
                continue
            expected_type = WorkstationFields[key]
            if not isinstance(value, expected_type):
                return {"success": False, "error": f"Field '{key}' must be of type {expected_type.__name__}."}
            self.workstation[key] = copy.deepcopy(value)

        return {"success": True, "message": "Workstation info updated"}


class DeveloperWorkstationEnvironment(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {})
        self._sync_from_inner()

    @staticmethod
    def _build_inner_env():
        try:
            return _GeneratedEnvImpl({})
        except Exception:
            return _GeneratedEnvImpl()

    @staticmethod
    def _apply_init_config(env, init_config):
        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            setattr(env, key, copy.deepcopy(value))

    def _sync_from_inner(self):
        reserved = {
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "tool_list",
            "env_description",
            "initial_parameter_schema",
            "default_initial_parameters",
            "tool_descs",
        }
        current = set()
        for key, value in vars(self._inner).items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if key in reserved:
                continue
            setattr(self, key, copy.deepcopy(value))
            current.add(key)
        stale = getattr(self, "_mirrored_state_keys", set()) - current
        for key in stale:
            if hasattr(self, key):
                delattr(self, key)
        self._mirrored_state_keys = current

    def _call_inner_tool(self, tool_name: str, kwargs: Dict[str, Any]):
        func = getattr(self._inner, tool_name)
        result = func(**copy.deepcopy(kwargs or {}))
        self._sync_from_inner()
        return result

    def list_installed_compilers(self, **kwargs):
        return self._call_inner_tool('list_installed_compilers', kwargs)

    def list_installed_compilers_by_language(self, **kwargs):
        return self._call_inner_tool('list_installed_compilers_by_language', kwargs)

    def get_compiler_versions_by_language(self, **kwargs):
        return self._call_inner_tool('get_compiler_versions_by_language', kwargs)

    def get_default_compiler_for_language(self, **kwargs):
        return self._call_inner_tool('get_default_compiler_for_language', kwargs)

    def get_toolchain_configuration(self, **kwargs):
        return self._call_inner_tool('get_toolchain_configuration', kwargs)

    def get_perf_monitor_api_status(self, **kwargs):
        return self._call_inner_tool('get_perf_monitor_api_status', kwargs)

    def list_supported_performance_metrics(self, **kwargs):
        return self._call_inner_tool('list_supported_performance_metrics', kwargs)

    def get_recent_performance_metric(self, **kwargs):
        return self._call_inner_tool('get_recent_performance_metric', kwargs)

    def get_performance_metric_history(self, **kwargs):
        return self._call_inner_tool('get_performance_metric_history', kwargs)

    def get_workstation_info(self, **kwargs):
        return self._call_inner_tool('get_workstation_info', kwargs)

    def set_default_compiler_for_language(self, **kwargs):
        return self._call_inner_tool('set_default_compiler_for_language', kwargs)

    def install_compiler(self, **kwargs):
        return self._call_inner_tool('install_compiler', kwargs)

    def uninstall_compiler(self, **kwargs):
        return self._call_inner_tool('uninstall_compiler', kwargs)

    def modify_toolchain_environment_variable(self, **kwargs):
        return self._call_inner_tool('modify_toolchain_environment_variable', kwargs)

    def refresh_perf_monitor_api(self, **kwargs):
        return self._call_inner_tool('refresh_perf_monitor_api', kwargs)

    def trigger_performance_metric_collection(self, **kwargs):
        return self._call_inner_tool('trigger_performance_metric_collection', kwargs)

    def update_workstation_info(self, **kwargs):
        return self._call_inner_tool('update_workstation_info', kwargs)
