# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class RowInfo(TypedDict):
    row_id: str  # Represents the unique id of the row
    data: Dict[str, Any]  # Maps column name to cell value

class DatasetInfo(TypedDict):
    name: str  # Name of the dataset (must be unique)
    columns: List[str]  # List of column names (must be unique within dataset)
    rows: List[RowInfo]  # Ordered list of rows
    schema: Dict[str, str]  # column name -> data type (as string)
    row_ord: List[str]  # Preserves order of row_ids

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing multiple tabular datasets with schema and row order preservation.
        """

        # Datasets: mapping from dataset name to its info structure
        # Each dataset:
        #   - name: str
        #   - columns: List[str]
        #   - rows: List[RowInfo]
        #   - schema: Dict[str, str]
        #   - row_ord: List[str]
        self.datasets: Dict[str, DatasetInfo] = {}

        # Constraints:
        # - Each dataset's name must be unique within the environment.
        # - Row order is preserved unless an operation (such as deduplication) changes it.
        # - Deduplication operations compare specified columns and retain either the first or last occurrence as requested.
        # - Column names within a dataset must be unique.
        # - The schema of each dataset determines the allowed data types for each column.
        # - Operations must not introduce or remove columns unless explicitly specified.

    def list_datasets(self) -> dict:
        """
        Return a list of all dataset names present in the environment.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of all dataset names (may be empty)
            }
        """
        dataset_names = list(self.datasets.keys())
        return {"success": True, "data": dataset_names}

    def get_dataset_info(self, dataset_name: str) -> dict:
        """
        Retrieve metadata (columns, schema, row count, and row order) for a given dataset by name.

        Args:
            dataset_name (str): The unique name of the dataset.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": {
                        "columns": List[str],
                        "schema": Dict[str, str],
                        "row_count": int,
                        "row_ord": List[str]
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Description of the error
                }

        Constraints:
            - Dataset name must exist in the environment.
        """
        dataset = self.datasets.get(dataset_name)
        if dataset is None:
            return { "success": False, "error": "Dataset not found" }

        info = {
            "columns": dataset["columns"],
            "schema": dataset["schema"],
            "row_count": len(dataset["rows"]),
            "row_ord": dataset["row_ord"]
        }
        return { "success": True, "data": info }

    def get_dataset_columns(self, dataset_name: str) -> dict:
        """
        Get the list of column names and their types for a given dataset.

        Args:
            dataset_name (str): The unique name of the dataset.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "columns": List[str],
                    "schema": Dict[str, str]
                }
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - Dataset with the given name must exist.
        """
        dataset = self.datasets.get(dataset_name)
        if dataset is None:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist"}

        return {
            "success": True,
            "data": {
                "columns": dataset["columns"],
                "schema": dataset["schema"]
            }
        }

    def get_dataset_rows(self, dataset_name: str) -> dict:
        """
        Retrieve all rows (row_id and data) for the specified dataset.

        Args:
            dataset_name (str): The unique name of the dataset to query.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[RowInfo]  # List of {'row_id': str, 'data': Dict[column_name, value]}
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "Dataset does not exist"
                    }

        Constraints:
            - Dataset name must exist in the environment.
            - Does not alter the state or contents of the dataset.
        """
        if dataset_name not in self.datasets:
            return {"success": False, "error": "Dataset does not exist"}
        rows = self.datasets[dataset_name]["rows"]
        return {"success": True, "data": rows.copy()}

    def get_row_by_id(self, dataset_name: str, row_id: str) -> dict:
        """
        Retrieve the full data of a specific row from a dataset by its row_id.

        Args:
            dataset_name (str): Name of the dataset to search.
            row_id (str): Unique identifier of the row to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": RowInfo,  # If the row is found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (dataset or row does not exist)
            }

        Constraints:
            - No changes allowed to the structure/content of the dataset.
            - Dataset and row_id must exist.
        """
        # Check if dataset exists
        if dataset_name not in self.datasets:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist"}

        dataset = self.datasets[dataset_name]
        # Find row by id
        for row in dataset["rows"]:
            if row["row_id"] == row_id:
                return {"success": True, "data": row}

        return {"success": False, "error": f"Row with id '{row_id}' does not exist in dataset '{dataset_name}'"}

    def get_row_order(self, dataset_name: str) -> dict:
        """
        Get the current row order for a dataset as a list of row_ids.

        Args:
            dataset_name (str): The name of the dataset whose row order is to be retrieved.

        Returns:
            dict: 
              - On success: { "success": True, "data": List[str] }
              - On failure: { "success": False, "error": "Dataset not found" }

        Constraints:
            - The dataset_name must exist in self.datasets.
        """
        if dataset_name not in self.datasets:
            return { "success": False, "error": "Dataset not found" }

        row_order = self.datasets[dataset_name]["row_ord"]
        return { "success": True, "data": list(row_order) }

    def verify_columns_exist(self, dataset_name: str, columns: list) -> dict:
        """
        Check if all given columns exist (and are unique in the input list) within the specified dataset.

        Args:
            dataset_name (str): The name of the dataset to check.
            columns (List[str]): List of column names to verify existence.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": { "all_exist": True }
                }
                On error: {
                    "success": False,
                    "error": str  # Error reason
                }
        Constraints:
            - Dataset name must exist.
            - Input column names must be unique (no duplicates in input).
            - Each input column must exist in the dataset's column list.
            - No columns are added or removed.
        """
        # Check if dataset exists
        if dataset_name not in self.datasets:
            return { "success": False, "error": "Dataset does not exist" }
        # Check that input columns are unique
        if len(set(columns)) != len(columns):
            return { "success": False, "error": "Duplicate columns specified in input" }
        # Dataset columns
        dataset_columns = set(self.datasets[dataset_name]["columns"])
        missing = [col for col in columns if col not in dataset_columns]
        if missing:
            return { "success": False, "error": f"The following columns are missing: {missing}" }
        return { "success": True, "data": { "all_exist": True } }

    def deduplicate_rows(
        self, 
        dataset_name: str, 
        columns: List[str], 
        keep: str
    ) -> dict:
        """
        Remove duplicate rows from a dataset using specified columns, retaining either the "first" or "last" occurrence as requested.
        Row order is updated to reflect the kept rows.

        Args:
            dataset_name (str): Target dataset name.
            columns (List[str]): List of column names to compare for duplicates.
            keep (str): "first" to keep first occurrence, "last" for last occurrence.

        Returns:
            dict: 
                On success: {"success": True, "message": "Deduplication operation completed for <dataset_name> using columns ..."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Dataset must exist.
            - All columns must exist within the dataset.
            - Only "first" or "last" allowed for keep.
            - No new columns introduced or removed.
            - Row order preserved as per deduplication rules.

        """
        # Validate dataset exists
        ds = self.datasets.get(dataset_name)
        if ds is None:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist"}

        ds_columns = set(ds["columns"])
        for col in columns:
            if col not in ds_columns:
                return {"success": False, "error": f"Column '{col}' does not exist in dataset '{dataset_name}'"}

        if keep not in {"first", "last"}:
            return {"success": False, "error": "Parameter 'keep' must be either 'first' or 'last'"}

        seen = {}
        keep_indices = []
        row_ord = ds["row_ord"]
        # Map row_id to row for fast lookup
        rowid_to_row = {row["row_id"]: row for row in ds["rows"]}
        if keep == "first":
            # Iterate from start, keep first unique group
            for rid in row_ord:
                row = rowid_to_row[rid]
                key = tuple(row["data"].get(col) for col in columns)
                if key not in seen:
                    seen[key] = rid
                    keep_indices.append(rid)
        else:  # keep == "last"
            # Iterate from end, then reverse at the end to restore order
            temp_seen = {}
            for rid in reversed(row_ord):
                row = rowid_to_row[rid]
                key = tuple(row["data"].get(col) for col in columns)
                if key not in temp_seen:
                    temp_seen[key] = rid
            # The "last" occurrence is the one seen with last row_id
            # We must reconstruct row order in original dataset order
            filtered_last_ids = set(temp_seen.values())
            keep_indices = [rid for rid in row_ord if rid in filtered_last_ids]

        # Rebuild rows and row_ord to keep only deduplicated rows, preserving desired order
        new_rows = [rowid_to_row[rid] for rid in keep_indices]
        ds["rows"] = new_rows
        ds["row_ord"] = keep_indices

        return {
            "success": True,
            "message": (f"Deduplication operation completed for dataset '{dataset_name}' using columns {columns}, keeping '{keep}' occurrence")
        }

    def reorder_rows(self, dataset_name: str, new_row_order: list) -> dict:
        """
        Recompute and set a new row order for a dataset (if needed after certain operations).

        Args:
            dataset_name (str): The name of the dataset to reorder.
            new_row_order (List[str]): A list of row_id strings representing the new row order. Must be a permutation of the current set of row_ids for the dataset.

        Returns:
            dict:
                On success: { "success": True, "message": "Row order updated successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Dataset must exist.
            - new_row_order must be a permutation of existing row_ids (no duplicates, no missing, no extras).
            - No rows are added or removed, only the order is changed.
        """
        # Check dataset existence
        if dataset_name not in self.datasets:
            return { "success": False, "error": "Dataset does not exist." }
        dataset = self.datasets[dataset_name]

        current_ids = [row["row_id"] for row in dataset["rows"]]
        current_set = set(current_ids)
        new_set = set(new_row_order)

        # Check that new order is a permutation of current
        if current_set != new_set or len(new_row_order) != len(current_ids):
            return { "success": False, "error": "new_row_order must be a permutation of existing row_ids (no duplicates or missing rows)." }

        # Update row_ord
        dataset["row_ord"] = list(new_row_order)

        # Reorder the rows themselves to match row_ord
        id_to_row = {row["row_id"]: row for row in dataset["rows"]}
        dataset["rows"] = [id_to_row[row_id] for row_id in dataset["row_ord"]]

        return { "success": True, "message": "Row order updated successfully." }

    def add_dataset(
        self,
        name: str,
        columns: list,
        schema: dict,
        rows: list,
        row_ord: list
    ) -> dict:
        """
        Add a new dataset with the specified name, columns, schema, rows, and row order.

        Args:
            name (str): The dataset's unique name.
            columns (List[str]): List of unique column names.
            schema (Dict[str, str]): Mapping of column name to data type (columns and schema keys must match exactly).
            rows (List[RowInfo]): List of row dictionaries. Each must have unique 'row_id', and its 'data' keys must match the columns.
            row_ord (List[str]): Specifies the order of the row_ids. Must contain all and only the row_ids from rows.

        Returns:
            dict: {
                'success': True,
                'message': ...,
            }
            or
            {
                'success': False,
                'error': ...,
            }

        Constraints:
            - Dataset name must be unique in environment.
            - Columns must be unique.
            - All columns in schema, columns list, and all rows' data must match exactly.
            - row_ord must be a permutation of row_ids in rows (no extras, no missing, no duplicates).
            - No new columns may be introduced/removed by this operation.
        """
        # Check unique name
        if name in self.datasets:
            return { "success": False, "error": f"Dataset with name '{name}' already exists." }

        # Columns must be unique
        if len(columns) != len(set(columns)):
            return { "success": False, "error": "Columns must be unique." }

        # Schema keys must exactly match columns and vice versa
        if set(schema.keys()) != set(columns):
            return {
                "success": False,
                "error": "Schema keys and columns must match exactly."
            }

        # Row ids must be unique and match row_ord
        row_ids = [row["row_id"] for row in rows]
        if len(row_ids) != len(set(row_ids)):
            return { "success": False, "error": "Row IDs must be unique." }

        if set(row_ids) != set(row_ord):
            return {
                "success": False,
                "error": "row_ord must contain all and only the row_ids from the provided rows."
            }

        if len(row_ord) != len(row_ids):
            return {
                "success": False,
                "error": "row_ord must contain the same number of IDs as provided rows."
            }

        # Each row: data keys exactly match columns
        for idx, row in enumerate(rows):
            data_keys = set(row["data"].keys())
            if data_keys != set(columns):
                return {
                    "success": False,
                    "error": f"Row at index {idx} data keys do not match columns."
                }

        # Ready to add dataset
        self.datasets[name] = {
            "name": name,
            "columns": list(columns),
            "rows": list(rows),
            "schema": dict(schema),
            "row_ord": list(row_ord)
        }
        return { "success": True, "message": f"Dataset '{name}' added successfully." }

    def delete_dataset(self, dataset_name: str) -> dict:
        """
        Remove a dataset (including all its rows, columns, and schema) from the environment by its unique name.

        Args:
            dataset_name (str): The name of the dataset to be deleted.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Dataset '<dataset_name>' deleted successfully."
                    }
                On failure (dataset does not exist):
                    {
                        "success": False,
                        "error": "Dataset '<dataset_name>' does not exist."
                    }

        Constraints:
            - Dataset name must exist in the environment.
            - The operation fully removes the dataset and all its metadata.
        """
        if dataset_name not in self.datasets:
            return {
                "success": False,
                "error": f"Dataset '{dataset_name}' does not exist."
            }

        del self.datasets[dataset_name]
        return {
            "success": True,
            "message": f"Dataset '{dataset_name}' deleted successfully."
        }

    def add_row(self, dataset_name: str, row_id: str, data: Dict[str, Any]) -> dict:
        """
        Add a new row to the specified dataset, respecting dataset schema and row uniqueness.

        Args:
            dataset_name (str): The name of the dataset to add the row to.
            row_id (str): The unique identifier for the new row.
            data (Dict[str, Any]): Mapping of column name to value for the new row. Keys must match dataset's columns.

        Returns:
            dict: {
                "success": True,
                "message": "Row added to dataset <dataset_name>."
            } on success,
            or {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - Dataset must exist.
            - Row id must be unique in the dataset.
            - Data keys must exactly match dataset columns.
            - Data types must match the schema.
        """
        # Dataset existence check
        ds = self.datasets.get(dataset_name)
        if ds is None:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist."}

        # Unique row id check
        if any(row['row_id'] == row_id for row in ds['rows']):
            return {"success": False, "error": f"Row id '{row_id}' already exists in dataset '{dataset_name}'."}

        # Column key check
        columns = ds['columns']
        data_columns = set(data.keys())
        expected_columns = set(columns)
        if data_columns != expected_columns:
            missing = expected_columns - data_columns
            extra = data_columns - expected_columns
            msg = []
            if missing:
                msg.append(f"missing columns: {', '.join(missing)}")
            if extra:
                msg.append(f"unexpected columns: {', '.join(extra)}")
            return {"success": False, "error": f"Column mismatch: {'; '.join(msg)}."}

        # Schema & type check
        schema = ds['schema']
        for col in columns:
            expected_type = schema.get(col)
            val = data[col]
            # Check type as string (simple type match: str, int, float, bool)
            if expected_type == 'int':
                if not isinstance(val, int):
                    return {"success": False, "error": f"Column '{col}': expected int, got {type(val).__name__}."}
            elif expected_type == 'float':
                if not (isinstance(val, float) or isinstance(val, int)):  # allow int for float
                    return {"success": False, "error": f"Column '{col}': expected float, got {type(val).__name__}."}
            elif expected_type == 'str':
                if not isinstance(val, str):
                    return {"success": False, "error": f"Column '{col}': expected str, got {type(val).__name__}."}
            elif expected_type == 'bool':
                if not isinstance(val, bool):
                    return {"success": False, "error": f"Column '{col}': expected bool, got {type(val).__name__}."}
            else:
                return {"success": False, "error": f"Unsupported type '{expected_type}' for column '{col}'."}

        # All checks passed; add row
        new_row: RowInfo = {
            "row_id": row_id,
            "data": data.copy()
        }
        ds['rows'].append(new_row)
        ds['row_ord'].append(row_id)

        return {"success": True, "message": f"Row added to dataset '{dataset_name}'."}

    def delete_row(self, dataset_name: str, row_id: str) -> dict:
        """
        Removes a specific row from the given dataset by row_id.

        Args:
            dataset_name (str): The name of the dataset from which to delete the row.
            row_id (str): The unique id of the row to delete.

        Returns:
            dict: On success:
                {"success": True, "message": "Row <row_id> deleted from dataset <dataset_name>."}
            On failure:
                {"success": False, "error": "<reason>"}

        Constraints:
            - The dataset must exist in the environment.
            - The row_id must exist in the dataset.
            - Row order (row_ord) must be updated accordingly.
            - Must not add or remove columns.
        """
        if dataset_name not in self.datasets:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist."}

        dataset = self.datasets[dataset_name]

        # Find row index
        row_idx = None
        for idx, row in enumerate(dataset["rows"]):
            if row["row_id"] == row_id:
                row_idx = idx
                break
        if row_idx is None:
            return {"success": False, "error": f"Row with id '{row_id}' does not exist in dataset '{dataset_name}'."}

        # Remove from rows
        del dataset["rows"][row_idx]
        # Remove from row_ord
        if row_id in dataset["row_ord"]:
            dataset["row_ord"].remove(row_id)
        # No column changes needed

        return {"success": True, "message": f"Row {row_id} deleted from dataset {dataset_name}."}

    def update_row_data(self, dataset_name: str, row_id: str, new_data: Dict[str, Any]) -> dict:
        """
        Modify the data of a specific row within a dataset, ensuring all schema and type constraints.

        Args:
            dataset_name (str): Name of the dataset to update.
            row_id (str): The unique identifier for the row to update.
            new_data (dict): Mapping of column names to new values (partial updates allowed).

        Returns:
            dict: {
                "success": True,
                "message": "Row data updated."
            } or {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - The dataset must exist.
            - The row must exist in the dataset.
            - Only columns present in the dataset's schema may be updated.
            - The updated values must match the expected types in the schema (strict, e.g. int, float, str).
            - No new columns may be introduced by this method.
        """
        # 1. Check dataset exists
        dataset = self.datasets.get(dataset_name)
        if dataset is None:
            return { "success": False, "error": "Dataset not found." }

        # 2. Find the row
        row = None
        for r in dataset['rows']:
            if r['row_id'] == row_id:
                row = r
                break
        if row is None:
            return { "success": False, "error": "Row not found in the specified dataset." }

        # 3. Schema check
        schema = dataset['schema']
        for col, val in new_data.items():
            if col not in schema:
                return { "success": False, "error": f"Column '{col}' not in dataset schema." }
            # Type check
            expected_type = schema[col]
            type_ok = False
            if expected_type == "int":
                type_ok = isinstance(val, int)
            elif expected_type == "float":
                type_ok = isinstance(val, float) or isinstance(val, int)
            elif expected_type == "str":
                type_ok = isinstance(val, str)
            elif expected_type == "bool":
                type_ok = isinstance(val, bool)
            # You may expand for other types as needed
            else:
                # For unsupported/unknown types, skip type check
                type_ok = True
            if not type_ok:
                return { "success": False, "error": f"Column '{col}' expects type {expected_type}." }

        # 4. Update the row (partial or full)
        row['data'].update(new_data)

        return { "success": True, "message": "Row data updated." }

    def add_column(self, dataset_name: str, column_name: str, data_type: str) -> dict:
        """
        Explicitly add a new column to a dataset, specifying its name and data type.

        Args:
            dataset_name (str): Name of the target dataset (must exist).
            column_name (str): Name of the new column (must be unique within dataset).
            data_type (str): Data type of the new column (as string, e.g. 'str', 'int').

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Column '<column_name>' added to dataset '<dataset_name>'"}
                On failure:
                    {"success": False, "error": "<error reason>"}
    
        Constraints:
            - Dataset must exist.
            - Column name must be unique within the dataset.
            - Schema must be updated; existing rows must have None as default for new column.
        """
        ds = self.datasets.get(dataset_name)
        if ds is None:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist"}
        if column_name in ds["columns"]:
            return {"success": False, "error": f"Column '{column_name}' already exists in dataset '{dataset_name}'"}
        # Update columns
        ds["columns"].append(column_name)
        # Update schema
        ds["schema"][column_name] = data_type
        # Update all rows: add default None for this column
        for row in ds["rows"]:
            row["data"][column_name] = None
        return {"success": True, "message": f"Column '{column_name}' added to dataset '{dataset_name}'"}

    def remove_column(self, dataset_name: str, column_name: str) -> dict:
        """
        Explicitly remove a column from a dataset.

        Args:
            dataset_name (str): Name of dataset from which to remove the column.
            column_name (str): Name of the column to remove.

        Returns:
            dict:
                On success:
                  {"success": True, "message": "Column '<column_name>' removed from dataset '<dataset_name>'."}
                On failure:
                  {"success": False, "error": <reason>}

        Constraints:
            - Dataset must exist.
            - Column must exist in the dataset.
            - Must not remove all columns (at least one column must remain).
            - Operation must remove column from: columns, schema, and from data in all rows.
            - Row order must remain unchanged.
        """
        if dataset_name not in self.datasets:
            return {"success": False, "error": f"Dataset '{dataset_name}' does not exist."}
        dataset = self.datasets[dataset_name]
        if column_name not in dataset["columns"]:
            return {"success": False, "error": f"Column '{column_name}' does not exist in dataset '{dataset_name}'."}
        if len(dataset["columns"]) == 1:
            return {"success": False, "error": "Cannot remove the last remaining column from a dataset."}

        # Remove from columns list
        dataset["columns"] = [col for col in dataset["columns"] if col != column_name]
        # Remove from schema
        if column_name in dataset["schema"]:
            del dataset["schema"][column_name]
        # Remove column from all rows' data
        for row in dataset["rows"]:
            if column_name in row["data"]:
                del row["data"][column_name]

        return {"success": True, "message": f"Column '{column_name}' removed from dataset '{dataset_name}'."}


class TabularDataProcessingEnvironment(BaseEnv):
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

    def list_datasets(self, **kwargs):
        return self._call_inner_tool('list_datasets', kwargs)

    def get_dataset_info(self, **kwargs):
        return self._call_inner_tool('get_dataset_info', kwargs)

    def get_dataset_columns(self, **kwargs):
        return self._call_inner_tool('get_dataset_columns', kwargs)

    def get_dataset_rows(self, **kwargs):
        return self._call_inner_tool('get_dataset_rows', kwargs)

    def get_row_by_id(self, **kwargs):
        return self._call_inner_tool('get_row_by_id', kwargs)

    def get_row_order(self, **kwargs):
        return self._call_inner_tool('get_row_order', kwargs)

    def verify_columns_exist(self, **kwargs):
        return self._call_inner_tool('verify_columns_exist', kwargs)

    def deduplicate_rows(self, **kwargs):
        return self._call_inner_tool('deduplicate_rows', kwargs)

    def reorder_rows(self, **kwargs):
        return self._call_inner_tool('reorder_rows', kwargs)

    def add_dataset(self, **kwargs):
        return self._call_inner_tool('add_dataset', kwargs)

    def delete_dataset(self, **kwargs):
        return self._call_inner_tool('delete_dataset', kwargs)

    def add_row(self, **kwargs):
        return self._call_inner_tool('add_row', kwargs)

    def delete_row(self, **kwargs):
        return self._call_inner_tool('delete_row', kwargs)

    def update_row_data(self, **kwargs):
        return self._call_inner_tool('update_row_data', kwargs)

    def add_column(self, **kwargs):
        return self._call_inner_tool('add_column', kwargs)

    def remove_column(self, **kwargs):
        return self._call_inner_tool('remove_column', kwargs)

