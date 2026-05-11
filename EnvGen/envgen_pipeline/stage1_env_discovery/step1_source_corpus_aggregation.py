"""
Step 1: aggregate source tasks from existing instruction-following datasets.
Supported corpora:
- API-Bank
- ToolAce
- ToolBench-5000
- ToolAlpaca
- AgentHarm
- Agent-SafetyBench
"""
# Add the EnvGen pipeline directory to sys.path.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
from typing import Iterable, List
from utils.process_file import read_file, save_file


def contains_non_english(s):
    """Check if task contains non-English characters."""
    # English letters + numbers + common English punctuation + whitespace
    allowed_pattern = r'^[A-Za-z0-9\s\.\,\?\!\;\:\'\"\(\)\[\]\{\}\-\_\*/\\@#\$%\^&\+\=<>\|~`]*$'
    return not re.match(allowed_pattern, s)


def is_multimodal_task(task_str):
    """Check if task string contains multimodal keywords."""
    keywords = ["image", "photo", "picture", "video", "audio", "sound", "speech", "clip"]
    return any(kw.lower() in task_str.lower() for kw in keywords)



def extract_task(item, dataset_name):
    """Extract task from a single sample based on dataset format."""
    if dataset_name == 'toolace':
        assert item['conversations'][0]['from'] == 'user'
        task = item['conversations'][0]['value']
    elif dataset_name == "api-bank":
        task = item["input"].split("User:")[1].split("\nGenerate API Request: ")[0].split("\nAPI-Request: ")[0].split("TIME: ")[0].strip()
        if '\nAI: ' in task:
            task = task.split('\nAI: ')[0]
    elif dataset_name == "toolbench-5000":
        task = str(item.get("query", "")).strip()
    elif dataset_name == "toolalpaca":
        task = str(item.get("input", "")).strip()
    elif dataset_name == "agentharm":
        task = str(item.get("prompt", "")).strip()
    elif dataset_name == "agent-safetybench":
        task = str(item.get("instruction", "")).strip()
    else:
        return False, None

    if not isinstance(task, str):
        return False, None
    task = task.strip()
    if not task:
        return False, None
    # Filter non-English tasks
    if contains_non_english(task):
        return False, None
    # Filter multimodal tasks
    if is_multimodal_task(task):
        return False, None
    # Filter tasks with special characters/keywords
    if "Role definition:" in task or 'USD' in task or 'ETH' in task or 'Bitcoin' in task or 'Ethereum' in task or '@' in task or '.com' in task or 'http:' in task or 'https:' in task:
        return False, None

    return True, task


def _to_task_records(tasks: Iterable[str], source_name: str, deduplicate: bool = True) -> List[dict]:
    cleaned_tasks = [task.strip() for task in tasks if isinstance(task, str) and task.strip()]
    if deduplicate:
        cleaned_tasks = sorted(set(cleaned_tasks))
    return [{"task": task, "task_from": source_name} for task in cleaned_tasks]


def extract_api_bank(deduplicate: bool = True):
    """Extract tasks from API-Bank dataset."""
    data = []
    data.extend(read_file("stage1_env_discovery/source_data/api-bank/lv1-train.json"))
    data.extend(read_file("stage1_env_discovery/source_data/api-bank/lv2-train.json"))
    data.extend(read_file("stage1_env_discovery/source_data/api-bank/lv3-train.json"))
    tasks = []
    for item in data:
        success, task = extract_task(item, dataset_name='api-bank')
        if success:
            tasks.append(task)
    return _to_task_records(tasks, "api-bank", deduplicate=deduplicate)


def extract_toolace(deduplicate: bool = True):
    """Extract tasks from ToolAce dataset."""
    data = read_file('stage1_env_discovery/source_data/toolace/data.json')
    tasks = []
    for item in data:
        success, task = extract_task(item, dataset_name='toolace')
        if success:
            tasks.append(task)
    return _to_task_records(tasks, "toolace", deduplicate=deduplicate)


def extract_toolbench_5000(deduplicate: bool = True):
    """Extract tasks from the local ToolBench 5000 subset corpus."""
    data = read_file("stage1_env_discovery/source_data/toolbench-5000/toolbench_5000.json")
    tasks = []
    for item in data:
        if isinstance(item, dict):
            task = str(item.get("task", "")).strip()
        elif isinstance(item, str):
            task = item.strip()
        else:
            continue
        success, task = extract_task({"query": task}, dataset_name="toolbench-5000")
        if success:
            tasks.append(task)
    return _to_task_records(tasks, "toolbench-5000", deduplicate=deduplicate)


def extract_toolalpaca(deduplicate: bool = True):
    """Extract tasks from ToolAlpaca dataset."""
    data = read_file("stage1_env_discovery/source_data/toolalpaca/train_data.json")
    tasks = []
    for item in data:
        instances = item.get("Instances", [])
        if not isinstance(instances, list):
            continue
        for inst in instances:
            if not isinstance(inst, dict):
                continue
            success, task = extract_task(inst, dataset_name="toolalpaca")
            if success:
                tasks.append(task)
    return _to_task_records(tasks, "toolalpaca", deduplicate=deduplicate)


def extract_agentharm(deduplicate: bool = True):
    """Extract tasks from AgentHarm benchmark files."""
    tasks = []
    base_dir = Path("stage1_env_discovery/source_data/agentharm/benchmark")
    json_paths = sorted(
        {
            *base_dir.glob("harmful_behaviors*.json"),
            *base_dir.glob("benign_behaviors*.json"),
            *base_dir.glob("chat_*.json"),
        }
    )

    for path in json_paths:
        data = read_file(str(path))
        if not isinstance(data, dict):
            continue
        behaviors = data.get("behaviors", [])
        if not isinstance(behaviors, list):
            continue
        for item in behaviors:
            if not isinstance(item, dict):
                continue
            success, task = extract_task(item, dataset_name="agentharm")
            if success:
                tasks.append(task)
    return _to_task_records(tasks, "agentharm", deduplicate=deduplicate)


def extract_agent_safetybench(deduplicate: bool = True):
    """Extract tasks from Agent-SafetyBench released data."""
    data = read_file("stage1_env_discovery/source_data/agent-safetybench/released_data.json")
    tasks = []
    for item in data:
        if not isinstance(item, dict):
            continue
        success, task = extract_task(item, dataset_name="agent-safetybench")
        if success:
            tasks.append(task)
    return _to_task_records(tasks, "agent-safetybench", deduplicate=deduplicate)
    

if __name__ == "__main__":
    task_data_1 = extract_api_bank()
    print("api-bank:", len(task_data_1))
    task_data_2 = extract_toolace()
    print("toolace:", len(task_data_2))
    task_data_3 = extract_toolbench_5000()
    print("toolbench-5000:", len(task_data_3))
    task_data_4 = extract_toolalpaca()
    print("toolalpaca:", len(task_data_4))
    task_data_5 = extract_agentharm()
    print("agentharm:", len(task_data_5))
    task_data_6 = extract_agent_safetybench()
    print("agent-safetybench:", len(task_data_6))

    task_data = (
        task_data_1
        + task_data_2
        + task_data_3
        + task_data_4
        + task_data_5
        + task_data_6
    )
    print("total:", len(task_data))
    save_file("stage1_env_discovery/temp_result/step1_source_corpus_aggregation.json", task_data)
