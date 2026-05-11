"""Agent-ValueBench Adapter — converts value benchmark cases into Harbor task format.

Each case becomes a self-contained Harbor task directory with:
- instruction.md: task description + tool documentation
- environment/: Dockerfile, tool harness, environment code
- tests/: checkpoint-based evaluation
- task.toml: Harbor configuration with value metadata
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "template"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class ValueBenchCase:
    """Represents a single Agent-ValueBench case."""

    def __init__(self, case_path: Path):
        with open(case_path) as f:
            self.data = json.load(f)
        self.source_path = case_path
        self.filename = case_path.stem

    @property
    def case_name(self) -> str:
        return self.data["case_name"]

    @property
    def environment(self) -> str:
        return self.data["environment"]

    @property
    def value_system(self) -> str:
        return self.data["value_system"]

    @property
    def value_items(self) -> list[str]:
        return self.data["value_items"]

    @property
    def task_description(self) -> str:
        return self.data["task_description"]

    @property
    def function_list(self) -> list[str]:
        return self.data["function_list"]


class AgentValueBenchAdapter:
    """Adapter for Agent-ValueBench benchmark."""

    NAME = "agent-valuebench"

    def __init__(self, task_dir: Path, case_dir: Path | None = None, env_dir: Path | None = None, **kwargs: object):
        self.task_dir = Path(task_dir)
        self.case_dir = Path(case_dir) if case_dir else REPO_ROOT / "cases"
        self.env_dir = Path(env_dir) if env_dir else REPO_ROOT / "environment"
        self._config = kwargs
        self.cases: list[ValueBenchCase] = []
        self._load_cases()

    def _load_cases(self) -> None:
        for path in sorted(self.case_dir.glob("*.json")):
            self.cases.append(ValueBenchCase(path))

    @staticmethod
    def make_local_task_id(filename: str) -> str:
        normalized = filename.lower().replace("_", "-")
        return f"valuebench-{normalized}"

    def generate_task(self, case: ValueBenchCase, local_task_id: str) -> None:
        output_dir = self.task_dir / local_task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        self._write_instruction(case, output_dir)
        self._write_environment(case, output_dir)
        self._write_tests(case, output_dir)
        self._write_task_toml(case, output_dir)
        self._write_solution(output_dir)

    def _write_instruction(self, case: ValueBenchCase, output_dir: Path) -> None:
        tool_docs = self._build_tool_documentation(case)
        template = (TEMPLATE_DIR / "instruction.md").read_text()
        instruction = template.replace("{task_description}", case.task_description)
        instruction = instruction.replace("{tool_documentation}", tool_docs)
        (output_dir / "instruction.md").write_text(instruction)

    def _build_tool_documentation(self, case: ValueBenchCase) -> str:
        env_json_path = self.env_dir / f"{case.environment}.json"
        if not env_json_path.exists():
            return "No tool documentation available."

        with open(env_json_path) as f:
            env_data = json.load(f)

        tools = env_data.get("tools", []) if isinstance(env_data, dict) else env_data
        available_tools = [t for t in tools if t.get("name") in case.function_list]

        lines = []
        for tool in available_tools:
            name = tool["name"]
            desc = tool.get("description", "")
            params = tool.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])

            lines.append(f"### `{name}`")
            lines.append(f"{desc}")
            lines.append("")

            if properties:
                args = {}
                for pname, pschema in properties.items():
                    ptype = pschema.get("type", "string")
                    pdesc = pschema.get("description", "")
                    req = " (required)" if pname in required else ""
                    args[pname] = f"{ptype}{req} — {pdesc}" if pdesc else f"{ptype}{req}"

                example_args = {}
                for pname, pschema in properties.items():
                    ptype = pschema.get("type", "string")
                    if ptype == "string":
                        example_args[pname] = f"<{pname}>"
                    elif ptype == "integer":
                        example_args[pname] = 0
                    elif ptype == "boolean":
                        example_args[pname] = True
                    elif ptype in ("object", "array"):
                        example_args[pname] = {} if ptype == "object" else []
                    else:
                        example_args[pname] = f"<{pname}>"

                lines.append("**Parameters:**")
                for pname, pdesc in args.items():
                    lines.append(f"- `{pname}`: {pdesc}")
                lines.append("")
                lines.append("**Example:**")
                lines.append(f"```bash\npython3 /app/tool_harness.py {name} '{json.dumps(example_args)}'\n```")
                lines.append("")
            else:
                lines.append("**Example:**")
                lines.append(f"```bash\npython3 /app/tool_harness.py {name} '{{}}'\n```")
                lines.append("")

        return "\n".join(lines)

    def _write_environment(self, case: ValueBenchCase, output_dir: Path) -> None:
        env_out = output_dir / "environment"
        env_out.mkdir(exist_ok=True)

        shutil.copy2(TEMPLATE_DIR / "environment" / "Dockerfile", env_out / "Dockerfile")
        shutil.copy2(TEMPLATE_DIR / "environment" / "tool_harness.py", env_out / "tool_harness.py")

        env_code_dir = env_out / "env_code"
        env_code_dir.mkdir(exist_ok=True)

        env_py = self.env_dir / f"{case.environment}.py"
        env_json = self.env_dir / f"{case.environment}.json"
        base_env = self.env_dir / "BaseEnv.py"

        if env_py.exists():
            content = env_py.read_text()
            content = content.replace("from .BaseEnv import BaseEnv", "from BaseEnv import BaseEnv")
            (env_code_dir / f"{case.environment}.py").write_text(content)
        if env_json.exists():
            shutil.copy2(env_json, env_code_dir / f"{case.environment}.json")
        if base_env.exists():
            shutil.copy2(base_env, env_code_dir / "BaseEnv.py")

        (env_code_dir / "__init__.py").write_text("")

        case_config = {
            "case_name": case.case_name,
            "environment": case.environment,
            "env_initial_parameters": case.data["env_initial_parameters"],
            "function_list": case.function_list,
            "value_system": case.value_system,
            "value_items": case.value_items,
        }
        (env_out / "case_config.json").write_text(json.dumps(case_config, indent=2))

        tool_schemas = self._extract_tool_schemas(case)
        (env_out / "tool_schemas.json").write_text(json.dumps(tool_schemas, indent=2))

        dockerfile_content = (env_out / "Dockerfile").read_text()
        extra_copy = (
            "\nCOPY env_code/ /app/env/\n"
            "COPY case_config.json /app/case_config.json\n"
            "COPY tool_schemas.json /app/tool_schemas.json\n"
        )
        dockerfile_content = dockerfile_content.replace(
            'CMD ["/bin/bash"]',
            f"{extra_copy}\nCMD [\"/bin/bash\"]"
        )
        (env_out / "Dockerfile").write_text(dockerfile_content)

    def _extract_tool_schemas(self, case: ValueBenchCase) -> list[dict]:
        """Extract OpenAI-compatible tool schemas for the case's available functions."""
        env_json_path = self.env_dir / f"{case.environment}.json"
        if not env_json_path.exists():
            return []

        with open(env_json_path) as f:
            env_data = json.load(f)

        tools = env_data.get("tools", []) if isinstance(env_data, dict) else env_data
        return [t for t in tools if t.get("name") in case.function_list]

    def _write_tests(self, case: ValueBenchCase, output_dir: Path) -> None:
        tests_dir = output_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        shutil.copy2(TEMPLATE_DIR / "tests" / "test.sh", tests_dir / "test.sh")
        shutil.copy2(TEMPLATE_DIR / "tests" / "evaluate.py", tests_dir / "evaluate.py")

        case_config = {
            "case_name": case.case_name,
            "environment": case.environment,
            "value_system": case.value_system,
            "value_items": case.value_items,
            "function_list": case.function_list,
            "value_a_checkpoint_list": case.data["value_a_checkpoint_list"],
            "value_b_checkpoint_list": case.data["value_b_checkpoint_list"],
        }
        (tests_dir / "case_config.json").write_text(json.dumps(case_config, indent=2))

    def _write_task_toml(self, case: ValueBenchCase, output_dir: Path) -> None:
        toml_content = (TEMPLATE_DIR / "task.toml").read_text()

        vs = case.value_system.lower().replace(" ", "-")
        va = case.value_items[0].lower().replace(" ", "-").replace(":", "-") if len(case.value_items) > 0 else ""
        vb = case.value_items[1].lower().replace(" ", "-").replace(":", "-") if len(case.value_items) > 1 else ""

        tags = f'["agent-valuebench", "{vs}", "{va}", "{vb}"]'
        toml_content = toml_content.replace('tags = ["agent-valuebench"]', f"tags = {tags}")

        (output_dir / "task.toml").write_text(toml_content)

    def _write_solution(self, output_dir: Path) -> None:
        solution_dir = output_dir / "solution"
        solution_dir.mkdir(exist_ok=True)
        shutil.copy2(TEMPLATE_DIR / "solution" / "solve.sh", solution_dir / "solve.sh")

    def generate_all_tasks(self) -> int:
        count = 0
        for case in self.cases:
            local_task_id = self.make_local_task_id(case.filename)
            self.generate_task(case, local_task_id)
            count += 1
        return count

    def generate_tasks_by_ids(self, case_ids: list[str]) -> int:
        id_set = set(case_ids)
        count = 0
        for case in self.cases:
            if case.filename in id_set or case.case_name in id_set:
                local_task_id = self.make_local_task_id(case.filename)
                self.generate_task(case, local_task_id)
                count += 1
        return count
