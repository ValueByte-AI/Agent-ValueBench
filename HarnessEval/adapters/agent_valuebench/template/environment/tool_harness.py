#!/usr/bin/env python3
"""Tool execution harness for Agent-ValueBench.

Initializes the environment from case config, executes tool calls, and logs
every call to /logs/agent/tool_calls.jsonl for checkpoint evaluation.

Usage:
    python3 /app/tool_harness.py <tool_name> '<json_arguments>'

Example:
    python3 /app/tool_harness.py get_project_by_title '{"title": "Titan Fall"}'
"""

import importlib
import json
import os
import sys
import time


LOG_PATH = "/logs/agent/tool_calls.jsonl"
CONFIG_PATH = os.environ.get("VALUEBENCH_CONFIG", "/app/case_config.json")
ENV_MODULE_DIR = os.environ.get("VALUEBENCH_ENV_DIR", "/app/env")


def load_environment():
    sys.path.insert(0, ENV_MODULE_DIR)
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    env_name = config["environment"]
    params = config["env_initial_parameters"]
    allowed_tools = config["function_list"]

    mod = importlib.import_module(env_name)
    env_cls = getattr(mod, env_name)
    env = env_cls(parameters=params)

    state_path = "/app/env_state.json"
    if os.path.exists(state_path):
        with open(state_path) as f:
            saved = json.load(f)
        for key, value in saved.items():
            if hasattr(env._inner, key):
                setattr(env._inner, key, value)
        env._sync_from_inner()

    return env, allowed_tools


def save_state(env):
    state = {}
    for key, value in vars(env._inner).items():
        if key.startswith("__") and key.endswith("__"):
            continue
        try:
            json.dumps(value)
            state[key] = value
        except (TypeError, ValueError):
            pass
    with open("/app/env_state.json", "w") as f:
        json.dump(state, f)


def log_tool_call(tool_name, arguments, result, allowed):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": time.time(),
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
        "allowed": allowed,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: tool_harness.py <tool_name> [json_arguments]"}))
        sys.exit(1)

    tool_name = sys.argv[1]
    arguments = {}
    if len(sys.argv) >= 3:
        try:
            arguments = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            result = {"success": False, "error": f"Invalid JSON arguments: {e}"}
            log_tool_call(tool_name, sys.argv[2], result, False)
            print(json.dumps(result))
            sys.exit(1)

    env, allowed_tools = load_environment()

    if tool_name not in allowed_tools:
        result = {"success": False, "error": f"Tool '{tool_name}' is not available. Available tools: {allowed_tools}"}
        log_tool_call(tool_name, arguments, result, False)
        print(json.dumps(result))
        sys.exit(1)

    result = env.call_tool(tool_name, arguments)
    log_tool_call(tool_name, arguments, result, True)
    save_state(env)
    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
