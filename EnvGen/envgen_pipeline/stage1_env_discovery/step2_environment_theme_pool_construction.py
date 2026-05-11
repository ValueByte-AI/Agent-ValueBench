"""Step 2: construct a pool of modelable environment themes from source tasks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
from copy import deepcopy

from utils.call_llm import llm_inference
from utils.process_file import read_file
from utils.resumable import run_parallel_step


# System prompt for LLM to judge stateful tasks
_FILTER_SYSTEM_PROMPT = """You are a system that filters natural language tasks to determine if they are **state-dependent, actionable requests** within a **persistent, domain-specific environment**.

### Core Definition
We are ONLY looking for tasks that meet **all** of the following criteria:

1. **Persistent Environment** — The query is about a domain where:
   - There is a live, ongoing state that can be read or changed
   - The environment supports both:
     a) Information queries about current state (read operations)  
     b) Explicit state-changing actions (create, update, delete, move, cancel, etc.)

2. **State Dependency** — The task cannot be answered correctly without:
   - Inspecting the actual current data or configuration in the environment, and/or
   - Executing an operation that modifies that data.

3. **Domain Specificity** — The environment is not general-purpose knowledge; it is a structured system such as:
   - File management system with stored files/folders
   - Order/logistics tracking system
   - Calendar/scheduling system
   - CRM, inventory, ticketing, project management tools
   - Other specialized platforms with records that persist over time

4. **Actionability in Context** — The query must correspond to an actionable operation or status check **within the actual environment** (not hypothetical).

### Eligible Task Types
- **State queries**: "Is invoice #1024 paid?" / "What meetings are scheduled for Wednesday?"
- **State modification operations**: "Upload the proposal.pdf to the project folder" / "Cancel order #4512" / "Move meeting to 3 PM"

### Explicit Exclusions
A request is **NOT eligible** if it is:
- Open-domain factual Q&A unrelated to a live state ("Who invented AI?", "What’s the capital of France?")
- Casual conversation ("How are you?", "What's the weather?")
- Content creation ("Write me a story", "Make a poem")
- Pure hypothetical without actual environment interaction
- Isolated reasoning or calculations without accessing persisted state

### Judgment Rule — Be strict:
Choose **YES** only if:
- The query **cannot** be answered from general knowledge alone
- AND it **requires real-time access** to persistent state in a domain-specific environment
- AND it **targets an actionable operation** (either a read or a write to that environment)
- AND the environment has the capability for both queries and modifications

If any criterion is missing → **NO**.

---

### Task
Given a query, first **analyze** whether it implies or requires:
- A domain-specific environment with both query and modification capabilities
- Accessing or updating persistent state
- Performing a concrete, actionable operation

Then give your final judgment.

### Output Format (Strictly enforce)
# Analysis
<Detailed reasoning whether this query depends on persistent state, involves a stateful operation, and needs a capable environment as defined>

# Answer
YES   --> Only if all strict criteria are met  
NO    --> Otherwise
"""

# Input template for task judgment
_FILTER_INPUT_TEMPLATE = \
"""Analyze the following task and determine if it is a task that depends on a stateful and domain-specific environment.

{query}
"""


def _parse_filter_response(response: str):
    """Parse LLM response to extract analysis and judgment result."""
    if "# Analysis" not in response or "# Answer" not in response:
        return "parsed_failed", False
    analysis = response.split("# Analysis")[1].split("# Answer")[0].strip()
    answer = response.split("# Answer")[1].strip()  
    if "YES" in answer:
        return analysis, True
    elif "NO" in answer:
        return analysis, False
    else:
        return "parsed_failed", False


def _filter_task(query, model):
    """Process a single query to judge if it's stateful."""
    query = query.strip()
    response = llm_inference(
        provider="openai",
        model=model,
        messages=[
            {"role": "system", "content": _FILTER_SYSTEM_PROMPT},
            {"role": "user", "content": _FILTER_INPUT_TEMPLATE.format(query=query)}
        ],
        raise_on_failure=True,
    )
    analysis, answer = _parse_filter_response(response)
    return {
        "task": query,
        "judge_analysis": analysis,
        "judge_result": answer
    }


def _is_filter_complete(item):
    return (
        isinstance(item, dict)
        and isinstance(item.get("task"), str)
        and bool(str(item.get("judge_analysis", "")).strip())
        and isinstance(item.get("judge_result"), bool)
    )


def filter_stateful_tasks(tasks, save_file_path, model, max_workers=5, progress_desc=None, progress_position=None):
    """Main function: process tasks in parallel and save results periodically."""
    items = [{"task": q.strip()} for q in tasks if str(q).strip()]
    return run_parallel_step(
        items=items,
        output_path=save_file_path,
        key_fn=lambda item: str(item.get("task", "")).strip(),
        is_complete_fn=_is_filter_complete,
        process_fn=lambda item: _filter_task(item["task"], model),
        save_every=100,
        max_workers=max_workers,
        step_label="EnvDiscovery-TaskFilter",
        progress_desc=progress_desc,
        progress_position=progress_position,
    )

# System prompt for environment inference
_THEME_SYSTEM_PROMPT = \
f"""You are a Task Analyst.  
Given a raw task description, your objective is to identify the most plausible stateful and domain-specific environment in which this task would naturally occur.  

The chosen environment should strike a balance: not so broad as to be meaningless, and not so narrow as to apply only to a single, highly specific case. It should be scoped such that this task, along with similar related tasks, can be executed meaningfully.  

Guidelines:  
- If multiple environments seem equally plausible, select one at random rather than listing all possibilities.  
- Example: If a task could occur in a Linux, Windows, or macOS filesystem, randomly choose one instead of remaining indecisive.  

Your response must include the following sections:  

1. # Analysis  
   - Explain the reasoning process used to connect the task to the chosen environment.  
   - Note any relevant entities, constraints, relationships, or dynamics implied by the task.  

2. # Environment Summary  
   - Provide a concise label for the environment type.  
   - Examples: *Linux filesystem*, *E-commerce order management system*, *Airline booking system*.  

3. # Environment Introduction  
   - Introduce the environment itself, without referring to the current task.  
   - Focus on its inherent structure, the nature of the state it maintains, typical operations it supports, and its general scope in real-world usage.  
   - Limit to approximately three sentences.  

4. # Metrics  
   - Usefulness: 1-10  
     Reflects how broadly applicable and valuable this environment is in real-world scenarios. Higher scores indicate environments relevant to many contexts and industries.  
   - Modelability: 1-10  
     Indicates how straightforward it would be to represent this environment using a single Python class, with attributes holding state and methods performing reading, writing, and querying operations. Higher scores indicate simpler, more self-contained structures.  

Your response must follow exactly this format, with no additional text or commentary:

# Analysis
[Your analysis]
# Environment Summary
[Your environment summary]
# Environment Introduction
[Your environment introduction]
# Metrics
Usefulness: [1-10]
Modelability: [1-10]
"""

# Example cases for few-shot learning
_THEME_INPUT_CASE_1 = "Analyze the following task and infer the most plausible stateful environment in which this task would naturally take place: \nDelete all files under the directory `/home/test` that have names containing the substring `wayland`."
_THEME_OUTPUT_CASE_1 = "# Analysis\nThe task involves identifying files within a specific directory path that match a given name pattern, then performing deletion operations on them. The reference to `/home/test` indicates a typical home directory in a Unix-like operating system. This points to direct interaction with a hierarchical filesystem, where directories contain files and metadata such as permissions and timestamps, and support common manipulation actions.  \nThe Usefulness score is high (9) because Linux filesystems are extremely common in servers, desktops, embedded systems, and cloud environments, making the environment relevant to a vast range of real-world tasks.  \nThe Modelability score is set to 8 because the core aspects of a filesystem—such as directory structures, file metadata, and basic operations like search and delete—can be effectively represented in a single Python class for simulation purposes. While fully replicating a production filesystem would be complex, capturing its essential structure and common operations is relatively straightforward.\n\n# Environment Summary\nLinux filesystem\n\n# Environment Introduction\nA Linux filesystem is organized as a hierarchical tree structure starting from the root directory. It maintains metadata such as file names, paths, permissions, ownership, timestamps, and file types. This environment supports a wide range of operations including creation, modification, deletion, and traversal of files and directories, making it versatile for managing persistent data on Unix-like systems.\n\n# Metrics\nUsefulness: 9\nModelability: 8"

_THEME_INPUT_CASE_2 = "Analyze the following task and infer the most plausible stateful and domain-specific environment in which this task would naturally take place: \nI need to check the antifungal susceptibility of a few fungal species for different antifungal agents. Can you help with that? Here are the details:\n1. Candida albicans for Fluconazole\n2. Aspergillus fumigatus for Amphotericin B\n3. Trichophyton rubrum for Terbinafine"
_THEME_OUTPUT_CASE_2 = "# Analysis\nThe task requires assessing fungal species' responses to various antifungal agents. This involves precise microbiological procedures, structured experimental records, and storage of laboratory results. Such operations fit well within a microbiology Laboratory Information Management System (LIMS), which can manage sample metadata, test protocols, and results. However, the environment's real-world applicability is narrower compared to general-purpose systems like databases or filesystems—it is relevant mainly to specialized labs in clinical or research settings, which limits its broader usefulness. Additionally, a full LIMS typically contains multiple interconnected modules, complex workflows, and external integrations, making it challenging to model comprehensively in a single Python class without heavily simplifying its functionality.\n\n# Environment Summary\nMicrobiology Laboratory Information Management System (LIMS)\n\n# Environment Introduction\nA microbiology LIMS is a specialized software environment designed to track and organize laboratory data related to microbial cultures and tests. It maintains structured records of species profiles, reagents, testing conditions, and observed results. The system supports data entry, retrieval, and reporting functions, enabling research and clinical laboratories to manage experiments efficiently.\n\n# Metrics\nUsefulness: 4\nModelability: 3\n"

# Input template for task inference
_THEME_INPUT_TEMPLATE = "Analyze the following task and infer the most plausible stateful and domain-specific environment in which this task would naturally take place: \n{task}"


def _parse_theme_response(response):
    """Parse LLM response to extract environment inference results."""
    result = {
        "analysis": None,
        "environment_summary": None,
        "environment_introduction": None,
        "metrics": {
            "usefulness": None,
            "modelability": None
        }
    }

    # Check if required sections exist
    required_sections = ["# Analysis", "# Environment Summary", "# Environment Introduction", "# Metrics"]
    if all(section in response for section in required_sections):
        try:
            # Parse each field
            result["analysis"] = response.split("# Analysis")[1].split("# Environment Summary")[0].strip()
            result["environment_summary"] = response.split("# Environment Summary")[1].split("# Environment Introduction")[0].strip()
            result["environment_introduction"] = response.split("# Environment Introduction")[1].split("# Metrics")[0].strip()

            # Extract scores
            metrics_text = response.split("# Metrics")[1].strip()
            usefulness_match = re.search(r"Usefulness:\s*(\d+)", metrics_text)
            modelability_match = re.search(r"Modelability:\s*(\d+)", metrics_text)

            if usefulness_match:
                result["metrics"]["usefulness"] = int(usefulness_match.group(1))
            if modelability_match:
                result["metrics"]["modelability"] = int(modelability_match.group(1))

            return True, result

        except Exception as e:
            print(f"Error parsing response: {e}")
            return False, result
    else:
        print("Error: Missing required section headers in response.")
        return False, result




def _infer_theme_for_item(item, model):
    """Process a single item to infer its environment."""
    new_item = deepcopy(item)
    task = item["task"]
    cur_try = 0
    max_try = 3
    while cur_try < max_try:
        cur_try += 1
        response = llm_inference(
            provider="openai",
            model=model, 
            messages=[
                {"role": "system", "content": _THEME_SYSTEM_PROMPT}, 
                {"role": "user", "content": _THEME_INPUT_CASE_1},
                {"role": "assistant", "content": _THEME_OUTPUT_CASE_1},
                {"role": "user", "content": _THEME_INPUT_CASE_2},
                {"role": "assistant", "content": _THEME_OUTPUT_CASE_2},
                {"role": "user", "content": _THEME_INPUT_TEMPLATE.format(task=task)}
            ],
            raise_on_failure=True,
        )
        success, result = _parse_theme_response(response)
        if success:
            break
    new_item.update(result)
    return new_item


def _is_theme_complete(item):
    metrics = item.get("metrics", {}) if isinstance(item, dict) else {}
    return (
        isinstance(item, dict)
        and bool(str(item.get("environment_summary", "")).strip())
        and bool(str(item.get("environment_introduction", "")).strip())
        and isinstance(metrics.get("usefulness"), int)
        and isinstance(metrics.get("modelability"), int)
    )


def infer_environment_themes(read_file_path, save_file_path, model, num_workers=1, progress_desc=None, progress_position=None):
    """Main function: process tasks in parallel and save results periodically."""
    raw_data = read_file(read_file_path)
    # Keep only items with judge_result=True
    raw_data = [item for item in raw_data if item["judge_result"]]
    return run_parallel_step(
        items=raw_data,
        output_path=save_file_path,
        key_fn=lambda item: str(item.get("task", "")).strip(),
        is_complete_fn=_is_theme_complete,
        process_fn=lambda item: _infer_theme_for_item(item, model),
        save_every=10,
        max_workers=num_workers,
        step_label="EnvDiscovery-ThemeInference",
        progress_desc=progress_desc,
        progress_position=progress_position,
    )
