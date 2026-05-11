# -*- coding: utf-8 -*-
"""
Environment registry and initialization entry point.

Responsibilities:
1. Discover environment classes under the environment package.
2. Initialize an environment from case-provided parameters.
3. Merge environment default initial parameters with case overrides.
"""

from __future__ import annotations

import copy
import importlib
import os
from typing import Any, Dict, Optional, Type

from .BaseEnv import BaseEnv


class EnvManager:
    def __init__(self) -> None:
        # registry: {"Bank": <class Bank>, ...}
        self.registry: Dict[str, Type[BaseEnv]] = {}
        self._discover_envs()

    def _discover_envs(self) -> None:
        env_dir = os.path.dirname(__file__)
        for file_name in os.listdir(env_dir):
            if not file_name.endswith(".py"):
                continue

            module_name = file_name[:-3]
            if module_name in {"BaseEnv", "EnvManager", "__init__"}:
                continue

            try:
                # Import with a package-relative path, for example environment.Bank.
                module = importlib.import_module(f".{module_name}", package=__package__)
                cls = getattr(module, module_name, None)
                if cls is None:
                    continue
                if not isinstance(cls, type):
                    continue
                if not issubclass(cls, BaseEnv):
                    continue
                self.registry[module_name] = cls
            except Exception:
                # Skip broken environments so other valid environments remain usable.
                continue

    def init_env(self, env_name: str, env_params: Optional[Dict[str, Any]] = None):
        cls = self.registry.get(env_name)
        if cls is None:
            return None

        # Instantiate once to read default initial parameters from the paired JSON.
        env_obj = cls(parameters={})
        defaults = env_obj.get_default_initial_parameters()
        merged = self._deep_merge(defaults, env_params or {})

        # Instantiate again with merged parameters to avoid half-initialized state.
        return cls(parameters=merged)

    def list_envs(self):
        return sorted(self.registry.keys())

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge dictionaries:
        - dict over dict: deep merge.
        - other value types: override replaces base.

        This lets cases override only part of the initial state without repeating the full parameter object.
        """
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = EnvManager._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result
