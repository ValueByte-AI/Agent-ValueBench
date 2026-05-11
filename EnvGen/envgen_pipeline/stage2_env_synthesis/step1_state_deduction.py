"""Step 1: deduce environment state and build the base state scaffold."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from copy import deepcopy

from utils.call_llm import llm_inference
from utils.process_file import read_file
from utils.resumable import run_sequential_step



# System prompt for state space inference
_STATE_SCHEMA_SYSTEM_PROMPT = \
"""You are an expert task and environment analyst.  
Given an environment description and a example task in this environment, infer the set of state variables (state space) that the environment maintained.  

The state should not be too broad (e.g. "all possible data in an e-commerce system"), nor too narrow (only for this single task).  Instead, reasonably design it to support this task and similar tasks in the same environment.  

The input format is:

# Environment Summary
[Environment summary]

# Environment Introduction
[Environment introduction]

# A Example Task in This Environment
[Example task]


Your output must follow the format below (do not include any other text):

# Analysis
[Your thought process: What states are involved in the environment? What entities/attributes need to be tracked? What constraints or rules exist in the environment? ……]

# State Space Definition
- Entity: EntityName1  
  - Attributes: Attribute1, Attribute2, ...
  - Description: The role of this entity in the environment

- Entity: EntityName2
  - Attributes: ...
  - Description: ...

# Constraints & Rules
- Constraint 1
- Constraint 2
...
"""


# Example cases for few-shot learning
_STATE_SCHEMA_INPUT_CASE_1 = \
"""Analyze the following task and environment, and infer the set of state variables (state space) that the environment maintained.  

# Environment Summary
E-commerce order management system

# Environment Introduction
This environment consists of a stateful backend for an e-commerce platform, managing products, orders, inventory, and order statuses.  
It keeps records of which products have been purchased in each order, tracks real-time stock quantities for all products, and stores fulfillment information for each order.  
These features make it the natural setting for inventory adjustments and order status updates in response to customer purchases.

# A Example Task in This Environment
Reduce stock quantity by 1 for every product purchased in order #58291 and mark the order as fulfilled.
"""

_STATE_SCHEMA_OUTPUT_CASE_1 = \
"""# Analysis
This task requires knowing which products belong to a given order, the quantity of each product, and their current stock levels.  
It also requires an order to have a modifiable status.  
Therefore, the environment must maintain entities for orders, products, and inventory, along with attributes like stock quantity and order state.  

# State Space Definition
- Entity: Product  
  - Attributes: product_id, name, category, price, stock_quantity  
  - Description: Represents a product sold on the platform, with inventory tracking via stock_quantity.

- Entity: Order  
  - Attributes: order_id, customer_id, status, order_items  
  - Description: Represents a purchase order placed by a customer. Includes current order status and the list of items purchased.

- Entity: OrderItem 
  - Attributes: order_id, product_id, quantity  
  - Description: Represents the many-to-many relationship between orders and products, with quantities ordered.

- Entity: Customer 
  - Attributes: customer_id, name, account_status  
  - Description: Represents the user placing the order, useful for related tasks.

# Constraints & Rules
- Stock quantity cannot drop below 0.  
- Only orders with status = "pending" can be marked as "fulfilled".  
- Each product in an order must exist in the product inventory."""


# Input template for state space inference
_STATE_SCHEMA_INPUT_TEMPLATE = \
"""Analyze the following task and environment, and infer the set of state variables (state space) that the environment maintained.  

# Environment Summary
{env_summary}

# Environment Introduction
{env_introduction}

# A Example Task in This Environment
{task}
"""


def parse_state_space_definition(state_space_definition):
    """Parse state space definition into list of dictionaries with entity, attributes, description."""
    if "- Entity: " not in state_space_definition:
        print(f"Error parsing state space definition: {state_space_definition}")
        return []
    state_space_definition = state_space_definition.split("- Entity: ")[1:]
    state_space_definition = [entity.split("\n") for entity in state_space_definition]
    if len(state_space_definition) == 0:
        print(f"Error parsing state space definition: {state_space_definition}")
        return []
    state_space_definition = [{
        "entity": entity[0].strip().strip("- Entity: "),
        "attributes": entity[1].strip().strip("- Attributes: "),
        "description": entity[2].strip().strip("- Description: ")
    } for entity in state_space_definition]
    return state_space_definition


def parse_constraints_rules(constraints_rules):
    """Parse constraints and rules by splitting on '- ' pattern."""
    if "- " not in constraints_rules:
        print(f"Error parsing constraints rules: {constraints_rules}")
        return []
    constraints_rules = constraints_rules.split("- ")[1:]
    constraints_rules = [constraint.strip() for constraint in constraints_rules]
    return constraints_rules


def _parse_state_schema_response(response):
    """Parse LLM response to extract analysis, state space definition, and constraints."""
    if "# Analysis" in response and "# State Space Definition" in response and "# Constraints & Rules" in response:
        try:
            analysis = response.split("# Analysis")[1].split("# State Space Definition")[0].strip()
            state_space_definition = response.split("# State Space Definition")[1].split("# Constraints & Rules")[0].strip()
            constraints_rules = response.split("# Constraints & Rules")[1].strip()
            return analysis, parse_state_space_definition(state_space_definition), parse_constraints_rules(constraints_rules)
        except Exception as e:
            print(f"Error parsing response: {e}")
            return response, None, None
    else:
        print(f"Error parsing response: {response}")
        return response, None, None

def deduce_state_schema(env_item, model):
    """Process a single environment item to infer state space."""
    new_env_item = deepcopy(env_item)
    input_content = _STATE_SCHEMA_INPUT_TEMPLATE.format(
        env_summary=env_item["environment_summary"],
        env_introduction=env_item["environment_introduction"],
        task=env_item["task"]
    )
    cur_try = 0
    max_try = 3
    while cur_try < max_try:
        cur_try += 1
        response = llm_inference(
            provider="openai",
            model=model, 
            messages=[
                {"role": "system", "content": _STATE_SCHEMA_SYSTEM_PROMPT}, 
                {"role": "user", "content": _STATE_SCHEMA_INPUT_CASE_1},
                {"role": "assistant", "content": _STATE_SCHEMA_OUTPUT_CASE_1},
                {"role": "user", "content": input_content}
            ],
            raise_on_failure=True,
        )
        analysis, state_space_definition, constraints_rules = _parse_state_schema_response(response)
        if analysis and state_space_definition and constraints_rules:
            break
    new_env_item["state_space_definition"] = state_space_definition
    new_env_item["constraints_rules"] = constraints_rules
    return new_env_item


def is_state_schema_complete(env_item):
    return (
        isinstance(env_item, dict)
        and isinstance(env_item.get("state_space_definition"), list)
        and len(env_item.get("state_space_definition", [])) > 0
        and isinstance(env_item.get("constraints_rules"), list)
        and len(env_item.get("constraints_rules", [])) > 0
    )

# System prompt for converting environment spec to Python class
_STATE_SCAFFOLD_SYSTEM_PROMPT = \
"""You are an AI coding assistant.  
Your job is to translate an environment specification into a Python environment class definition.  
The class should simulate the stateful environment structure (without methods yet).  

You should analyze first and then generate code.

You should follow the rules of Analysis and Code to generate the code.

Rules of Analysis
- Determine the environment class name. It should be EnvironmentSummary or an appropriate adaptation (e.g., `LinuxFileSystem`, `EcommerceOrderSystem`).  
- Extract attribute names (comma-separated) from each entity in `state_space_definition`.
- If needed, generate a corresponding `TypedDict` using the extracted attributes, with attribute name → key and attribute value type → inferred from the appropriate Python primitive type (e.g., `id`=str, `name`=str, `category`=str, `price`/`size`=float/int, `quantity`=int, `status`=str, `timestamps`=str/float).
- `constraints_rules` is left as a comment.

Rules of Code
- Generates each `TypedDict` definition if needed.
- Generates the environment class (with only `__init__` and attributes), with attributes of type `Dict[ID, TypedDict]`.
- Add comments mapping each attribute back to the state space entity/attributes.
- Annotates the constraints in the code comments.
- Do not implement any business logic or methods yet.  

The input format is:
# Environment Summary
<short label, e.g. Linux filesystem, E-commerce order system>"

# Environment Introduction
<paragraph intro>

# State Space Definition
[
    {
      "entity": "EntityName",
      "attributes": "attr1, attr2, ...",
      "description": "short description"
    },
    ...
]

# constraints_rules
constraint 1 ...
constraint 2 ...
}

Your output must follow the format below (do not include any other text):

# Analysis
[Explains how to design Python environment classes based on tasks and state spaces (including class name selection, mapping entities to data structures, which fields are stored as dict/list, and how constraints are expressed through annotations)]

# Class Definition
```python
[Python environment class definition]
```"""


# Example cases for few-shot learning
_STATE_SCAFFOLD_INPUT_CASE_1 = \
"""Given the following Environment, State Space, and Constraints, generate a Python environment class definition accordingly.

# Environment Summary
E-commerce order management system

# Environment Introduction
This environment represents an e-commerce order management system, where users can place orders, view products, and manage their accounts.

# State Space Definition
[
    {
      "entity": "Product",
      "attributes": "product_id, name, category, price, stock_quantity",
      "description": "Represents a product sold on the platform."
    },
    {
      "entity": "Order",
      "attributes": "order_id, customer_id, status, order_items",
      "description": "Represents a purchase order placed by a customer."
    },
    {
      "entity": "OrderItem",
      "attributes": "order_id, product_id, quantity",
      "description": "Intermediate entity linking products to orders."
    }
]

# constraints_rules
- tock quantity cannot drop below 0.
- Only orders with status = 'pending' can be marked as 'fulfilled'."""

_STATE_SCAFFOLD_OUTPUT_CASE_1 = "# Analysis\nThe task involves updating inventory and order status. The environment is summarized as an \"e-commerce order management system,\" so the class is named `EcommerceOrderManagementSystem`.\n\nBased on the state space:\n- The Product entity needs to store a dict with key = product_id and value = metadata (including stock_quantity).\n- The Order entity needs to store a dict with key = order_id and value = metadata (including customer_id, status, and order_items).\n- The OrderItem entity represents a many-to-many relationship between Order and Product, ideally stored as {order_id: [{product_id, quantity}, ...]}.\n \nExtract Entity：  \n  • Product → {product_id: str, name: str, category: str, price: float, stock_quantity: int}  \n  • Order → {order_id: str, customer_id: str, status: str, order_items: List[OrderItemInfo]}  \n  • OrderItem → {order_id: str, product_id: str, quantity: int}  \n\nUse TypedDict to define these structures\n- In the environment：  \n  self.products: Dict[str, ProductInfo]  \n  self.orders: Dict[str, OrderInfo] \n \nConstraints such as \"stock ≥ 0\" and \"order status can only transition from pending to fulfilled\" are initially documented in the class as comments and later implemented in method implementations.\n\n# Class Definition\n```python\nfrom typing import Dict, List, TypedDict\n\nclass ProductInfo(TypedDict):\n    product_id: str\n    name: str\n    category: str\n    price: float\n    stock_quantity: int\n\nclass OrderItemInfo(TypedDict):\n    order_id: str\n    product_id: str\n    quantity: int\n\nclass OrderInfo(TypedDict):\n    order_id: str\n    customer_id: str\n    status: str\n    order_items: List[OrderItemInfo]\n\nclass EcommerceOrderManagementSystem:\n    def __init__(self):\n        \"\"\"\n        The environment for e-commerce order management.\n        \"\"\"\n\n        # Products: {product_id: ProductInfo}\n        self.products: Dict[str, ProductInfo] = {}\n\n        # Orders: {order_id: OrderInfo}\n        self.orders: Dict[str, OrderInfo] = {}\n\n        # Constraints reminder:\n        # - Stock quantity cannot drop below 0\n        # - Only orders with status = 'pending' can be marked as 'fulfilled'\n\n        self.current_user: dict = {}\n```"


# Input template for environment class generation
_STATE_SCAFFOLD_INPUT_TEMPLATE = """Given the following Environment, State Space, and Constraints, generate a Python environment class definition accordingly.

# Environment Summary
{env_summary}

# Environment Introduction
{env_introduction}

# State Space Definition
{state_space_definition}

# constraints_rules
{constraints_rules}
"""  


def _parse_state_scaffold_response(response):
    """Parse LLM response to extract class definition."""
    if "# Analysis" in response and "# Class Definition" in response:
        try:
            analysis = response.split("# Analysis")[1].split("# Class Definition")[0].strip()
            class_definition = response.split("# Class Definition")[1].strip().lstrip("```python").rstrip("```")
            return True, class_definition
        except Exception as e:
            print(f"Error parsing response: {e}")
            return False, response
    else:
        print(f"Error parsing response: {response}")
        return False, response


def _construct_state_scaffold_messages(env_item):
    """Construct messages for LLM inference based on environment item."""
    state_space_definition_str = json.dumps(env_item["state_space_definition"], indent=4, ensure_ascii=False)
    constraint_str = ""
    for constraint in env_item["constraints_rules"]:
        constraint_str += f"- {constraint}\n"
    input_content = _STATE_SCAFFOLD_INPUT_TEMPLATE.format(
        env_summary=env_item["environment_summary"], 
        env_introduction=env_item["environment_introduction"], 
        state_space_definition=state_space_definition_str,
        constraints_rules=constraint_str)
    messages = [
        {"role": "system", "content": _STATE_SCAFFOLD_SYSTEM_PROMPT}, 
        {"role": "user", "content": _STATE_SCAFFOLD_INPUT_CASE_1},
        {"role": "assistant", "content": _STATE_SCAFFOLD_OUTPUT_CASE_1},
        {"role": "user", "content": input_content}
    ]
    return messages


def _infer_state_scaffold(messages, model):
    """Generate class definition using LLM with retry mechanism."""
    cur_try = 0
    max_try = 5
    parse_success = False
    class_definition = ""
    while cur_try < max_try:
        response = llm_inference(
            provider="openai",
            model=model,
            messages=messages,
            raise_on_failure=True,
        )
        parse_success, class_definition = _parse_state_scaffold_response(response)
        if parse_success:
            break
        cur_try += 1
    return class_definition


def _build_state_scaffold_for_item(env_item, model):
    """Process a single environment item to generate class definition."""
    new_env_item = deepcopy(env_item)
    messages = _construct_state_scaffold_messages(env_item)
    class_definition = _infer_state_scaffold(messages, model)
    new_env_item["class_definition"] = class_definition
    return new_env_item


def _is_state_scaffold_complete(env_item):
    return isinstance(env_item, dict) and bool(str(env_item.get("class_definition", "")).strip())


def build_state_scaffolds(read_file_path, save_file_path, model, progress_desc=None, progress_position=None):
    """Main function: generate class definitions for all environments."""
    raw_data = read_file(read_file_path)
    run_sequential_step(
        items=raw_data,
        output_path=save_file_path,
        key_fn=lambda item: item.get("__dispatch_index__", item.get("task", "")),
        is_complete_fn=_is_state_scaffold_complete,
        process_fn=lambda item: _build_state_scaffold_for_item(item, model),
        save_every=10,
        step_label="EnvSynthesis-StateScaffold",
        progress_desc=progress_desc,
        progress_position=progress_position,
    )
    print("Save to file: {}".format(save_file_path))
