"""Step 3: synthesize executable environment programs and tool schemas."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import ast
import re
from copy import deepcopy
from typing import List, Optional

from utils.call_llm import llm_inference
from utils.process_file import read_file, save_file
from utils.recovery import RecoverableAPIError, RecoverableStepError
from utils.resumable import run_parallel_step
from stage2_env_synthesis.analysis_env_src.get_env_class_def import parse_env_class_name, parse_env_class_def
from stage2_env_synthesis.analysis_env_src.build_env_structure import build_class_tree_form_str
from stage2_env_synthesis.analysis_env_src.get_func_details_from_src import extract_class_methods_from_source
from stage2_env_synthesis.analysis_env_src.get_tool_schema import get_tool_info, convert_tool_schema

_OPERATION_CODE_SYSTEM_PROMPT = "You are a code generation assistant.\nGiven an Agent's environment, including the environment's summary and introduction, the environment's state space definition, the environment's constraint rules, key base class definitions, and the list of operations supported by the environment.\nOperations include two types: one is information querying of the environment, and the other is state modification of the environment.\nGiven one of the operations in the operation list (Target Operation),\n\nYou must:  \n1. In **# Analysis**, reason about:  \n   - What entities/attributes are involved.  \n   - Parameters needed.  \n   - Expected outputs (queries return structured results, state modifications return success messages).  \n   - Error/edge cases (e.g., invalid input, permission denied).  \n   - Does it involve environmental constraints or rules.  \n2. In **# Code**, implement the Python method:  \n   - Method name: `def <operation_name>(self, ...)`.  Note: Cannot be an independent function, but rather a method function within an already implemented environment class.\n   - Add clear type hints.  \n   - Add docstring describing inputs, outputs, constraints.  \n   - **Error handling**: do **not raise exceptions** — return a dict like `{ \"success\": False, \"error\": \"reason\" }`.  \n   - For information-query operations, if successful return `{ \"success\": True, \"data\": <result> }`.  \n   - For state-modifying operations, if successful return `{ \"success\": True, \"message\": \"operation description\" }`. \n\nIn each subsequent round, the input format is:\n### Environment Summary\n<environment_summary_here>\n\n### Environment Introduction\n<environment_introduction_here>\n\n### State Space Definition\n<state_space_definition_here>\n\n### Constraints Rules\n<constraints_rules_here>\n\n### Class Definition\n```python\n<class_definition_here>\n```\n\n### Operation List\n{operation_list}\n\n### Target Operation\n{\n  \"operation_name\": \"<operation_name>\",\n  \"operation_description\": \"<operation_description>\",\n  \"operation_type\": \"<query_or_state_change>\"\n}\n\n\nYour output format must be:\n# Analysis\n[Explain reasoning: inputs, outputs, related entities/attributes, constraints logic, success/failure cases]\n\n# Code\n```python\ndef <operation_name>(self, ...):\n    \"\"\"\n    <docstring explaining inputs, outputs and constraints>\n    \"\"\"\n    # Implementation\n```"

_OPERATION_CODE_INPUT_CASE_1 = "Based on the following environment specification, generate the function code for the target operation.\n\n### Environment Summary\nLinux filesystem\n\n### Environment Introduction\nThis environment is a Linux filesystem, where hierarchical directories and files are managed with associated metadata such as permissions, ownership, and timestamps. The `/var/tmp/` directory is commonly used for temporary files that need to persist across reboots, and utilities are available to manipulate and query file properties. This stateful environment is ideal for tasks that require combining filename pattern matching, attribute checking, and file compression operations.\n\n### State Space Definition\n[{'entity': 'Directory', 'attributes': 'directory_path, permissions, owner, group, timestamps (created, modified, accessed)', 'description': 'Represents a directory in the filesystem, including its location in the hierarchy and metadata.'}, {'entity': 'File', 'attributes': 'file_path, name, extension, size, permissions, owner, group, timestamps (created, modified, accessed), parent_directory', 'description': 'Represents a file, with metadata and association to its parent directory.'}]\n\n### Constraints Rules\n['Each file must have a unique path within the filesystem.', 'Permissions and ownership determine the allowed operations on files and directories.', 'Timestamps must be automatically updated according to standard filesystem operations.', 'Directory hierarchy is strictly tree', 'structured (no cycles).', 'File names within the same directory must be unique.']\n\n### Class Definition\n```python\n\nfrom typing import Dict, TypedDict\n\nclass TimestampsInfo(TypedDict):\n    created: float  # Unix timestamp\n    modified: float\n    accessed: float\n\nclass DirectoryInfo(TypedDict):\n    directory_path: str\n    permissions: str\n    owner: str\n    group: str\n    timestamps: TimestampsInfo  # created, modified, accessed\n\nclass FileInfo(TypedDict):\n    file_path: str\n    name: str\n    extension: str\n    size: int  # In bytes\n    permissions: str\n    owner: str\n    group: str\n    timestamps: TimestampsInfo  # created, modified, accessed\n    parent_directory: str\n\nclass LinuxFileSystem:\n    def __init__(self, init_config: dict):\n        \"\"\"\n        Linux filesystem environment simulation.\n        init_config: configuration for initialization (not implemented here).\n        \"\"\"\n\n        # Directories: {directory_path: DirectoryInfo}\n        # Represents all directories in the filesystem with metadata.\n        self.directories: Dict[str, DirectoryInfo] = {}\n\n        # Files: {file_path: FileInfo}\n        # Represents all files in the filesystem with metadata.\n        self.files: Dict[str, FileInfo] = {}\n\n        # --- Constraints (to be enforced in methods, not here) ---\n        # 1. Each file must have a unique path within the filesystem.\n        # 2. Permissions and ownership determine allowed operations on files/directories.\n        # 3. Timestamps (created, modified, accessed) must be updated per FS operations.\n        # 4. Directory hierarchy is strictly tree-structured (no cycles).\n        # 5. File names within the same directory must be unique.\n\n        self.init_config = init_config\n\n```\n\n### Operation List\n['list_files_in_directory', 'filter_files_by_extension', 'get_file_info', 'get_file_last_modified_time', 'check_file_permissions', 'get_directory_info', 'compress_file', 'update_file_timestamp', 'delete_file', 'create_file', 'change_file_permissions', 'change_file_owner']\n\n### Target Operation\n\"operation_name\": \"list_files_in_directory\"\n\"operation_description\": \"Retrieve all files within a specified directory path.\"\n\"operation_type\": \"query\""

_OPERATION_CODE_OUTPUT_CASE_1 = "# Analysis\nThe operation `list_files_in_directory` is an information query operation which retrieves all files that reside within a given directory path.\n\n**Entities/Attributes:**\n- Entity: File\n- Relevant attributes: file_path, parent_directory\n\n**Parameters Needed:**\n- `directory_path` (str): the absolute path to the target directory.\n\n**Operation Logic:**\n- Verify that the given `directory_path` exists in `self.directories`. If not, return failure.\n- For each file in `self.files`, check if the `parent_directory` equals the given `directory_path`.\n- Collect information on such files and return a list (likely their FileInfo dictionaries).\n\n**Constraints:**\n- Ensure that the provided directory exists (directory path is valid).\n- Tree structure of directories is implicit, but not directly relevant for a flat fetch.\n\n**Expected Output:**\n- On success: `{ \"success\": True, \"data\": <list of FileInfo for each file where parent_directory == directory_path> }`\n- On error: If directory does not exist, `{ \"success\": False, \"error\": \"Directory does not exist\" }`.\n\n**Edge/Error Cases:**\n- Directory does not exist.\n- Directory exists but contains no files: return empty list (this is still a successful call).\n\nNo permission checking is required (unless explicitly asked in the operation).\n\n# Code\n```python\ndef list_files_in_directory(self, directory_path: str) -> dict:\n    \"\"\"\n    Retrieve all files (with metadata) within the specified directory path.\n\n    Args:\n        directory_path (str): The absolute path to the directory to query.\n\n    Returns:\n        dict: {\n            \"success\": True,\n            \"data\": List[FileInfo],  # List of matching files' info (may be empty if no files)\n        }\n        or\n        {\n            \"success\": False,\n            \"error\": str  # Description of the error, e.g. directory does not exist\n        }\n\n    Constraints:\n        - The given directory must exist in the filesystem.\n    \"\"\"\n    if directory_path not in self.directories:\n        return { \"success\": False, \"error\": \"Directory does not exist\" }\n\n    result = [\n        file_info for file_info in self.files.values()\n        if file_info[\"parent_directory\"] == directory_path\n    ]\n\n    return { \"success\": True, \"data\": result }\n```"

_OPERATION_CODE_INPUT_TEMPLATE = \
"""
Based on the following environment specification, generate the function code for the target operation.

### Environment Summary
{env_summary}

### Environment Introduction
{env_intro}

### State Space Definition
{state_space_definition}

### Constraints Rules
{constraints_rules}

### Class Definition
```python
{class_definition}
```

### Operation List
{operation_name_list}

### Target Operation
"operation_name": "{operation_name}"
"operation_description": "{operation_description}"
"operation_type": "{operation_type}"
"""

def _parse_operation_code_response(response):
    """Parse the response from the LLM"""
    if "# Analysis" in response and "# Code" in response:
        try:
            analysis = response.split("# Analysis")[1].split("# Code")[0].strip()
            code = response.split("# Code")[1].strip().lstrip("```python").rstrip("```").strip()
            return analysis, code
        except Exception as e:
            print(f"Error parsing response: {e}")
            return "Error parsing response: {e}"+ response, None
    else:
        print(f"Error parsing response: {response}")
        return "Error parsing response: "+ response, None
    
def _construct_operation_code_messages(env_item, operation_item):
    """Construct the messages for the LLM"""
    # env info
    env_summary = env_item["environment_summary"]
    env_intro = env_item["environment_introduction"]
    state_space_definition = env_item["state_space_definition"]
    constraints_rules = env_item["constraints_rules"]
    class_definition = env_item["class_definition"]
    operation_name_list = [operation["operation_name"] for operation in env_item["operation_list"]]
    # operation info
    operation_name = operation_item["operation_name"]
    operation_description = operation_item["operation_description"]
    operation_type = operation_item["operation_type"]
    # format
    input_content = _OPERATION_CODE_INPUT_TEMPLATE.format(
        env_summary=env_summary, 
        env_intro=env_intro, 
        state_space_definition=state_space_definition, 
        constraints_rules=constraints_rules, 
        class_definition=class_definition, 
        operation_name_list=operation_name_list, 
        operation_name=operation_name, 
        operation_description=operation_description, 
        operation_type=operation_type)
    # print(f"Input content: \n{input_content}")
    messages = [
        {"role": "system", "content": _OPERATION_CODE_SYSTEM_PROMPT}, 
        {"role": "user", "content": _OPERATION_CODE_INPUT_CASE_1},
        {"role": "assistant", "content": _OPERATION_CODE_OUTPUT_CASE_1},
        {"role": "user", "content": input_content}
    ]
    return messages

def _infer_operation_code(messages, model):
    """LLM inference"""
    cur_try = 0
    max_try = 5
    parse_success = False
    func_code = ""
    while cur_try < max_try:
        response = llm_inference(
            provider="openai",
            model=model,
            messages=messages,
            raise_on_failure=True,
        )
        parse_success, func_code = _parse_operation_code_response(response)
        if parse_success:
            break
        cur_try += 1
    return func_code

def _synthesize_operation_code_for_item(env_item, model):
    """Process the environment item"""
    new_env_item = deepcopy(env_item)
    operation_items = deepcopy(env_item["operation_list"])
    for i in range(len(operation_items)):
        if str(operation_items[i].get("code", "")).strip():
            continue
        messages = _construct_operation_code_messages(env_item, operation_items[i])
        try:
            func_code = _infer_operation_code(messages, model)
            operation_items[i]["code"] = func_code
        except RecoverableAPIError as exc:
            partial_item = deepcopy(new_env_item)
            partial_item["operation_list"] = operation_items
            raise RecoverableStepError(
                step_label="EnvSynthesis-ProgramSynthesis",
                error=exc,
                partial_item=partial_item,
            ) from exc
    new_env_item["operation_list"] = operation_items
    return new_env_item


def synthesize_operation_code(read_file_path, save_file_path, model, max_workers, progress_desc=None, progress_position=None):
    raw_data = read_file(read_file_path)
    sorted_data = run_parallel_step(
        items=raw_data,
        output_path=save_file_path,
        key_fn=lambda item: item.get("__dispatch_index__", item.get("task", "")),
        is_complete_fn=lambda item: (
            isinstance(item, dict)
            and isinstance(item.get("operation_list"), list)
            and bool(item.get("operation_list"))
            and all(bool(str(op.get("code", "")).strip()) for op in item["operation_list"])
        ),
        process_fn=lambda item: _synthesize_operation_code_for_item(item, model),
        save_every=5,
        max_workers=max_workers,
        step_label="EnvSynthesis-ProgramSynthesis",
        progress_desc=progress_desc,
        progress_position=progress_position,
    )
    print("Save to file: {}".format(save_file_path))
    save_file(save_file_path, sorted_data)

def assemble_env_class(class_def: str, methods: List[str]) -> str:
    """
    Assemble a class definition string and a list of method definitions into one complete Python class code.
    
    Args:
        class_def (str): Python code string defining the class and __init__.
        methods (List[str]): A list of Python method code strings (should start with "def ...").
        output_path (Optional[str]): If given, the result will also be written to this file.
    
    Returns:
        str: The assembled full Python code.
    """
    lines = class_def.splitlines()
    
    # Find insertion point (after __init__ method)
    insertion_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def __init__"):
            insertion_index = i
    if insertion_index is None:
        raise ValueError("No __init__ method found in class_def")

    # Determine indentation level (usually 4 spaces inside class)
    base_indent = " " * 4
    
    # Prepare indented methods
    indented_methods = []
    for method in methods:
        method_lines = method.strip().splitlines()
        indented_methods.extend([base_indent + l if l.strip() else l for l in method_lines])
        indented_methods.append("")  # blank line between methods
    
    # Find end of __init__ method (detect next method definition or end of class)
    end_init_idx = insertion_index
    for i in range(insertion_index + 1, len(lines)):
        if lines[i].startswith("    def ") and not lines[i].lstrip().startswith("__init__"):
            end_init_idx = i - 1
            break
    else:
        end_init_idx = len(lines) - 1

    assembled = []
    assembled.extend(lines[:end_init_idx+1])
    assembled.append("")  # ensure one blank line
    assembled.extend(indented_methods)
    assembled.extend(lines[end_init_idx+1:])

    result = "\n".join(assembled)

    return result



def process_import(result: str) -> str:
    """
    Post-process assembled Python code:
    - Extract all import statements (both `import ...` and `from ... import ...`),
      even if they appear indented inside class/methods.
    - Move them to the file top.
    - Deduplicate and sort.
    - Remove duplicates from original places.
    
    Args:
        result (str): Python code string.
    
    Returns:
        str: Cleaned Python code with all imports at the top.
    """
    lines = result.splitlines()

    import_lines = []
    cleaned_lines = []

    # Regex patterns for import detection
    import_pattern = re.compile(r'^\s*(import .+|from .+ import .+)')

    for line in lines:
        if import_pattern.match(line.strip()):
            # Normalize by stripping leading/trailing spaces
            stmt = line.strip()
            import_lines.append(stmt)
            # remove from inline position
            continue
        cleaned_lines.append(line)

    # Deduplicate + preserve relative order (use dict.fromkeys)
    unique_imports = list(dict.fromkeys(import_lines))

    # Compose new file content
    final_lines = []
    if unique_imports:
        final_lines.extend(unique_imports)
        final_lines.append("")  # blank line after imports

    # Add back the rest (cleaned)
    final_lines.extend(cleaned_lines)

    return "\n".join(final_lines).strip() + "\n"


def check_ast(source: str) -> bool:
    """
    Check whether a Python source code string is syntactically valid.
    
    Args:
        source (str): Python source code as a string.
    
    Returns:
        bool: True if syntax is valid, False otherwise.
    
    Raises:
        SyntaxError: with detailed info if invalid.
    """
    try:
        ast.parse(source)
        return True
    except SyntaxError as e:
        print("❌ Syntax error detected:")
        print(f"  Line {e.lineno}, Offset {e.offset}: {e.text.strip() if e.text else ''}")
        print(f"  Details: {e.msg}")
        return False

def check_returns(source: str, strict: bool = False) -> list:
    """
    Check all function return statements for dictionary style output.
    
    Args:
        source (str): Python source code string.
        strict (bool): 
            If True, enforce that return dict must contain "success" and at least one of ("data","message","error").
    
    Returns:
        list of (function_name, lineno, status, message)
    """
    results = []
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    ret = child.value
                    # Check return dictionary structure
                    if isinstance(ret, ast.Dict):
                        keys = []
                        for k in ret.keys:
                            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                keys.append(k.value)
                        if "success" not in keys:
                            results.append((func_name, child.lineno, "FAIL", "Missing 'success' key in return dict"))
                        elif strict and not (("data" in keys) or ("message" in keys) or ("error" in keys)):
                            results.append((func_name, child.lineno, "WARN", "Return dict has 'success' but missing data/message/error"))
                        else:
                            results.append((func_name, child.lineno, "PASS", "Return dict keys: " + ",".join(keys)))
                    elif isinstance(ret, ast.Name):
                        # Variable return - cannot check statically
                        results.append((func_name, child.lineno, "WARN", f"Returns variable '{ret.id}', cannot check keys statically"))
                    elif isinstance(ret, ast.Constant) and ret.value is None:
                        results.append((func_name, child.lineno, "FAIL", "Return None detected"))
                    elif isinstance(ret, ast.Constant):
                        results.append((func_name, child.lineno, "WARN", f"Return constant {ret.value!r}, not directly checkable"))
                    else:
                        # Other return types
                        results.append((func_name, child.lineno, "WARN", f"Return type {type(ret).__name__}, not directly checkable"))
    return results


def write_py_code(py_code: str, output_path: str):
    """Write Python code to file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(py_code)

def _assemble_program_for_item(env_item):
    """Assemble class code from definition and methods, validate syntax and returns."""
    class_def = env_item["class_definition"]
    methods = [operation["code"] for operation in env_item["operation_list"]]
    passed = True
    try:
        py_code = assemble_env_class(class_def, methods)
        py_code = process_import(py_code)
    except Exception as e:
        print(f"❌ Error assembling class: {e}")
        passed = False
    if check_ast(py_code):
        print("✅ Syntax is valid")
    else:
        print("❌ Syntax is invalid")
        passed = False
    # Check return statements for proper dictionary structure
    ret_checks = check_returns(py_code)
    has_fail = any(status == "FAIL" for _, _, status, _ in ret_checks)
    if ret_checks and not has_fail:
        warn_count = sum(1 for _, _, status, _ in ret_checks if status == "WARN")
        print(f"✅ Returns are valid (warnings={warn_count})")
    else:
        print("❌ Returns are invalid")
        if not ret_checks:
            print("  Details: no return statements detected")
        else:
            for func_name, lineno, status, message in ret_checks:
                if status == "FAIL":
                    print(f"  FAIL {func_name}:{lineno} - {message}")
        passed = False
    new_item = deepcopy(env_item)
    new_item["env_class_code"] = py_code
    return passed, new_item
        
        
def assemble_programs(read_file_path, save_file_path):
    """Process all environment items, assemble code, validate, and save valid ones."""
    raw_data = read_file(read_file_path)
    new_data = []
    for env_item in raw_data:
        print(f"Processing env item: {env_item['environment_summary']}")
        try:
            passed, env_item = _assemble_program_for_item(env_item)
        except Exception as e:
            print(f"❌ Error processing env item: {e}")
            continue
        # Only keep items that passed all validations
        if passed:
            new_data.append(env_item)
    save_file(save_file_path, new_data)


def analyze_env_item(env_item):
    """Extract class name, definition, structure, methods, and tools from environment class code."""
    env_class_code = env_item["env_class_code"]
    env_class_name = parse_env_class_name(env_class_code)
    env_class_def = parse_env_class_def(env_class_code, env_class_name)
    env_structure = build_class_tree_form_str(src = env_class_code, class_name = env_class_name)
    env_func_details = extract_class_methods_from_source(source_str=env_class_code, class_name=env_class_name, include_self=False)
    new_item = deepcopy(env_item)
    print("env_class_name: ", env_class_name)
    new_item["env_class_name"] = env_class_name
    new_item["env_class_def"] = env_class_def
    new_item["env_structure"] = env_structure
    new_item["env_func_details"] = env_func_details
    # Convert tools to schema format
    new_item["tools"] = [convert_tool_schema(tool) for tool in get_tool_info(new_item)]
    return new_item

def analyze_programs(read_file_path, save_file_path):
    """Process all environment items and save analyzed results."""
    raw_data = read_file(read_file_path)
    new_data = []
    for env_item in raw_data:
        new_item = analyze_env_item(env_item)
        new_data.append(new_item)
    save_file(save_file_path, new_data)
