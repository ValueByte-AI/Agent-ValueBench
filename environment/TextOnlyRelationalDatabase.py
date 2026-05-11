# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ColumnInfo(TypedDict):
    column_name: str  # maps to the Column entity/attributes

class RecordInfo(TypedDict):
    field_values: Dict[str, str]  # maps to the Record entity/attributes

class TableInfo(TypedDict):
    table_name: str
    columns: List[ColumnInfo]      # list of columns in schema
    records: List[RecordInfo]      # list of records (rows)

class _GeneratedEnvImpl:
    def __init__(self):
        # Tables: {table_name: TableInfo}
        self.tables: Dict[str, TableInfo] = {}
        # --- Mapping from State Space:
        # Table: table_name, columns, records

        # Constraints:
        # - All record field values must be text (str)
        # - Each table_name in self.tables must be unique
        # - Each column_name in TableInfo['columns'] must be unique within the table
        # - Each record must supply a value (can be '') for each column in the table schema

    def list_tables(self) -> dict:
        """
        Retrieve the names of all tables in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of all table names (empty if no tables exist)
            }
        Constraints:
            - None.
        """
        table_names = list(self.tables.keys())
        return { "success": True, "data": table_names }

    def get_table_schema(self, table_name: str) -> dict:
        """
        Retrieve the schema (list of column names) of the specified table.

        Args:
            table_name (str): The name of the table to query.

        Returns:
            dict: {
                "success": True,
                "data": List[str]   # List of column names in the table (may be empty)
            } on success,
            or
            {
                "success": False,
                "error": str        # Error message if table doesn't exist
            } on failure.

        Constraints:
            - The table must exist (table_name must be present in self.tables).
        """
        table = self.tables.get(table_name)
        if not table:
            return { "success": False, "error": "Table does not exist" }

        column_names = [col['column_name'] for col in table['columns']]
        return { "success": True, "data": column_names }

    def list_table_records(self, table_name: str) -> dict:
        """
        Retrieve all records (rows) from the specified table, with each record's field values as text.

        Args:
            table_name (str): The name of the table from which to fetch records.

        Returns:
            dict:
                - On success: {"success": True, "data": List[Dict[str, str]]}
                  (Where each dict is a record mapping column names to text values)
                - On failure: {"success": False, "error": str}

        Constraints:
            - The specified table must exist.
            - All field values are strings.
        """
        table = self.tables.get(table_name)
        if table is None:
            return {"success": False, "error": "Table does not exist"}

        # Extract all records as list of field_values dicts
        records = [record["field_values"] for record in table["records"]]

        return {"success": True, "data": records}

    def get_table_record_count(self, table_name: str) -> dict:
        """
        Return the number of records in a specific table.

        Args:
            table_name (str): Name of the table to count records for.

        Returns:
            dict: {
                "success": True,
                "data": int  # The number of records in the table
            }
            or
            {
                "success": False,
                "error": str  # If table does not exist
            }

        Constraints:
            - The table must exist.
        """
        table = self.tables.get(table_name)
        if table is None:
            return {"success": False, "error": "Table does not exist"}
        record_count = len(table["records"])
        return {"success": True, "data": record_count}

    def get_table_column_names(self, table_name: str) -> dict:
        """
        List all column names for a specified table.

        Args:
            table_name (str): Name of the table.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": [column_name1, column_name2, ...]}
                On failure: 
                    {"success": False, "error": "Table does not exist"}

        Constraints:
            - Table must exist.
            - Column names are text, unique within the table.
        """
        table = self.tables.get(table_name)
        if not table:
            return {"success": False, "error": "Table does not exist"}
    
        column_names = [col["column_name"] for col in table["columns"]]
        return {"success": True, "data": column_names}

    def find_records_by_value(self, table_name: str, column_name: str, value: str) -> dict:
        """
        Query for records in a table where a specific column matches a given text value.

        Args:
            table_name (str): The target table to search.
            column_name (str): The column on which to match the value.
            value (str): The text value that must exactly match in the given column.

        Returns:
            dict: 
                On success: { "success": True, "data": List[RecordInfo] }
                On error:   { "success": False, "error": "..." }

        Constraints:
            - Table must exist.
            - column_name must exist within the table's schema.
            - All matchings are for exact text value.
        """
        table = self.tables.get(table_name)
        if table is None:
            return { "success": False, "error": f"Table '{table_name}' does not exist" }

        colnames = {col["column_name"] for col in table["columns"]}
        if column_name not in colnames:
            return { "success": False, "error": f"Column '{column_name}' does not exist in table '{table_name}'" }

        matching_records = [
            record for record in table["records"]
            if record["field_values"].get(column_name, "") == value
        ]
        return { "success": True, "data": matching_records }

    def search_records(self, table_name: str, columns: List[str], pattern: str) -> dict:
        """
        Query and filter records in a table based on substring or pattern match in specified columns.

        Args:
            table_name (str): The name of the table to search within.
            columns (List[str]): A list of column names to search in. All columns must exist on the table.
            pattern (str): The substring or pattern to match (plain substring search).

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "data": List[RecordInfo]  # records where any of the specified columns contains the pattern as a substring
                    }
                - On failure:
                    {
                      "success": False,
                      "error": str  # error message (table or column not found, etc.)
                    }

        Constraints:
            - The table must exist.
            - All columns must exist in the table's schema.
        """
        if table_name not in self.tables:
            return {"success": False, "error": f"Table '{table_name}' does not exist"}

        table = self.tables[table_name]
        table_column_names = {col["column_name"] for col in table["columns"]}

        if not columns:
            return {"success": False, "error": "No columns specified for searching"}

        missing_columns = [col for col in columns if col not in table_column_names]
        if missing_columns:
            return {
                "success": False,
                "error": f"Column(s) not found in table '{table_name}': {', '.join(missing_columns)}"
            }

        # Filter records
        matching_records = []
        for record in table["records"]:
            for col in columns:
                # Defensive: missing key should not occur if schema/constraints are respected,
                # but just in case, treat as non-match
                value = record["field_values"].get(col, "")
                if pattern in value:
                    matching_records.append(record)
                    break  # One match in any specified column is enough

        return {"success": True, "data": matching_records}

    def join_tables_on_column(
        self,
        left_table_name: str,
        right_table_name: str,
        column_name: str
    ) -> dict:
        """
        Perform a text-based (inner) join between two tables using a shared column name.

        Args:
            left_table_name (str): The name of the first table.
            right_table_name (str): The name of the second table.
            column_name (str): The column name to join on (must exist in both tables).

        Returns:
            dict:
                If success:
                    {
                        "success": True,
                        "data": List[Dict[str, str]]  # Each dict is a joined record:
                        # Keys are:
                        #   - All columns of left table, with 'left.' prefix (except join column: plain name)
                        #   - All columns of right table, with 'right.' prefix (except join column: plain name)
                        #   - The join column is included once (plain name)
                    }
                If error:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - Both tables must exist.
            - Both tables must have the join column.
            - Output dict keys for columns besides join column should be prefixed for disambiguation if duplicated.
        """
        # Existence checks
        if left_table_name not in self.tables:
            return { "success": False, "error": f"Table '{left_table_name}' does not exist" }
        if right_table_name not in self.tables:
            return { "success": False, "error": f"Table '{right_table_name}' does not exist" }

        left_table = self.tables[left_table_name]
        right_table = self.tables[right_table_name]

        left_columns = [col['column_name'] for col in left_table['columns']]
        right_columns = [col['column_name'] for col in right_table['columns']]

        if column_name not in left_columns:
            return { "success": False, "error": f"Column '{column_name}' does not exist in table '{left_table_name}'" }
        if column_name not in right_columns:
            return { "success": False, "error": f"Column '{column_name}' does not exist in table '{right_table_name}'" }

        # Prepare sets for fast lookup
        left_nonjoin = [col for col in left_columns if col != column_name]
        right_nonjoin = [col for col in right_columns if col != column_name]

        # Build index for right table: value of join column -> list of records
        right_index = {}
        for record in right_table['records']:
            val = record['field_values'].get(column_name, "")
            right_index.setdefault(val, []).append(record)

        joined_results = []

        for lrecord in left_table['records']:
            lval = lrecord['field_values'].get(column_name, "")
            if lval in right_index:
                for rrecord in right_index[lval]:
                    # Build joined record:
                    joined = {}
                    # Join column: as-is
                    joined[column_name] = lval
                    # Left table columns (except join): prefix left.
                    for col in left_nonjoin:
                        joined[f"{left_table_name}.{col}"] = lrecord['field_values'].get(col, "")
                    # Right table columns (except join): prefix right.
                    for col in right_nonjoin:
                        joined[f"{right_table_name}.{col}"] = rrecord['field_values'].get(col, "")
                    joined_results.append(joined)

        return { "success": True, "data": joined_results }

    def get_all_text_entries(self) -> dict:
        """
        Retrieve all text field values from all tables (table-wise full record scan).

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, List[str]],  # Mapping table_name -> flat list of all text values in all records (row scan order).
            }

        Notes:
            - If there are no tables, returns empty data dict.
            - If a table has no records, the value is an empty list for that table.
            - Each list is a flat list of all string field values, row by row, field order follows the table's column schema.
        """
        result = {}

        for table_name, table in self.tables.items():
            values = []
            col_names = [col["column_name"] for col in table["columns"]]
            for record in table["records"]:
                for col in col_names:
                    # All values are str as per constraints
                    values.append(record["field_values"].get(col, ""))  # Should always exist, but default for safety
            result[table_name] = values

        return { "success": True, "data": result }

    def create_table(self, table_name: str, column_names: List[str]) -> dict:
        """
        Define and add a new table with the given name and schema.

        Args:
            table_name (str): The name for the new table (must be unique).
            column_names (List[str]): List of text column names (must be unique, non-empty).

        Returns:
            dict: { "success": True, "message": "..." }
                  or { "success": False, "error": "..." }

        Constraints:
            - Table name must be unique (not already present).
            - Each column name must be non-empty and unique within the list.
        """
        # Check table_name is valid and unique
        if not isinstance(table_name, str) or table_name.strip() == "":
            return { "success": False, "error": "Table name must be a non-empty string." }
        if table_name in self.tables:
            return { "success": False, "error": f"Table '{table_name}' already exists." }

        # Check columns
        if not isinstance(column_names, list) or len(column_names) == 0:
            return { "success": False, "error": "At least one column name must be specified." }
        column_set = set()
        for col in column_names:
            if not isinstance(col, str) or col.strip() == "":
                return { "success": False, "error": "All column names must be non-empty strings." }
            col_normalized = col.strip()
            if col_normalized in column_set:
                return { "success": False, "error": f"Duplicate column name '{col_normalized}' in schema." }
            column_set.add(col_normalized)

        # Construct TableInfo
        columns_list = [ { "column_name": col.strip() } for col in column_names ]
        self.tables[table_name] = {
            "table_name": table_name,
            "columns": columns_list,
            "records": []
        }
        return { "success": True, "message": f"Table '{table_name}' created with columns {column_names}." }

    def drop_table(self, table_name: str) -> dict:
        """
        Removes the specified table and all its records from the database.

        Args:
            table_name (str): The name of the table to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Table '<table_name>' dropped." }
                - On failure: { "success": False, "error": "Table does not exist." }

        Constraints:
            - Table must exist in the database for deletion.
            - Operation is irreversible and removes all associated records and schema.
        """
        if table_name not in self.tables:
            return { "success": False, "error": "Table does not exist." }

        del self.tables[table_name]
        return { "success": True, "message": f"Table '{table_name}' dropped." }

    def add_column_to_table(self, table_name: str, column_name: str) -> dict:
        """
        Adds a new column to an existing table. The column name must be unique within the table.
        For all existing records in the table, the value for the new column is set to the empty string.
    
        Args:
            table_name (str): The name of the table to add the column to.
            column_name (str): The name of the new column to add.
    
        Returns:
            dict: On success:
                    {"success": True, "message": "Column '<column_name>' added to table '<table_name>'."}
                  On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - Table must exist.
            - Column name must be unique within the table.
            - All existing records get the new column with value ''.
        """
        # Check table existence
        if table_name not in self.tables:
            return {"success": False, "error": "Table does not exist."}

        table = self.tables[table_name]

        # Check column uniqueness
        for col in table["columns"]:
            if col["column_name"] == column_name:
                return {"success": False, "error": f"Column '{column_name}' already exists in table '{table_name}'."}

        # Add the new column to the schema
        table["columns"].append({"column_name": column_name})

        # Ensure each record now has this column with empty string value
        for record in table["records"]:
            record["field_values"][column_name] = ""

        return {
            "success": True,
            "message": f"Column '{column_name}' added to table '{table_name}'."
        }

    def remove_column_from_table(self, table_name: str, column_name: str) -> dict:
        """
        Remove a column from a table schema and update all records by deleting the corresponding field.
    
        Args:
            table_name (str): The name of the table from which to remove the column.
            column_name (str): The column to be removed.
        
        Returns:
            dict: {
                "success": True,
                "message": "Column '<column_name>' removed from table '<table_name>' and all records updated."
            }
            or
            {
                "success": False,
                "error": str (reason for failure)
            }
        
        Constraints:
            - table_name must exist in the database.
            - column_name must exist in the table schema.
            - All records' field_values must have the column removed.
        """
        if table_name not in self.tables:
            return {"success": False, "error": f"Table '{table_name}' does not exist."}
        
        table = self.tables[table_name]
        old_columns = table['columns']
        # Find the column in the schema
        matching_col = None
        for col in old_columns:
            if col['column_name'] == column_name:
                matching_col = col
                break
        if not matching_col:
            return {"success": False, "error": f"Column '{column_name}' does not exist in table '{table_name}'."}

        # Remove the column from schema
        new_columns = [col for col in old_columns if col['column_name'] != column_name]
        table['columns'] = new_columns

        # Remove the column from each record's field_values
        for record in table['records']:
            if column_name in record['field_values']:
                del record['field_values'][column_name]

        return {
            "success": True,
            "message": f"Column '{column_name}' removed from table '{table_name}' and all records updated."
        }

    def insert_record(self, table_name: str, field_values: Dict[str, str]) -> dict:
        """
        Add a new record to the specified table with string values for every schema column.

        Args:
            table_name (str): The target table's name.
            field_values (Dict[str, str]): Mapping from column name to value (all must be strings).

        Returns:
            dict with:
              - success: True/False
              - message: Success message if successful
              - error: String explaining the error if failed

        Constraints:
          - Table must exist.
          - Each column in the table schema must be supplied with a value (can be '').
          - No extra keys allowed besides schema columns.
          - All values in field_values must be str.
        """
        # Table existence check
        table = self.tables.get(table_name)
        if not table:
            return { "success": False, "error": f"Table '{table_name}' does not exist." }

        schema_cols = [col["column_name"] for col in table["columns"]]
        supplied_cols = list(field_values.keys())

        # Check for missing or extra columns
        missing_cols = [c for c in schema_cols if c not in field_values]
        extra_cols = [c for c in field_values if c not in schema_cols]
        if missing_cols:
            return { "success": False, "error": f"Missing values for columns: {missing_cols}" }
        if extra_cols:
            return { "success": False, "error": f"Extra non-schema columns in input: {extra_cols}" }

        # Check all values are text
        for column_name, value in field_values.items():
            if not isinstance(value, str):
                return { "success": False, "error": f"Field '{column_name}' value must be a string." }

        # All validations passed: insert record
        new_record: RecordInfo = {"field_values": field_values.copy()}
        table["records"].append(new_record)

        return { "success": True, "message": f"Record inserted into table '{table_name}'." }

    def update_record(self, table_name: str, record_index: int, new_values: Dict[str, str]) -> dict:
        """
        Change the text value(s) of fields in an existing record in a table.

        Args:
            table_name (str): Name of the table to update record in.
            record_index (int): Index (0-based) of the target record within the table's record list.
            new_values (Dict[str, str]): Mapping of column name(s) to the new text value(s) to set. Only these columns will be updated.

        Returns:
            dict:
                - On success: { "success": True, "message": "Record updated successfully" }
                - On error: { "success": False, "error": "<error message>" }

        Constraints:
            - Table must exist.
            - Record index must be valid.
            - Columns in new_values must exist in the table's schema.
            - All new_values must be strings.
        """
        # Check if table exists
        if table_name not in self.tables:
            return { "success": False, "error": "Table does not exist" }
        table = self.tables[table_name]
        # Check record index validity
        if not (0 <= record_index < len(table["records"])):
            return { "success": False, "error": "Record index out of range" }
        # Valid columns
        valid_columns = set(col["column_name"] for col in table["columns"])
        # Validate inputs
        for col, val in new_values.items():
            if col not in valid_columns:
                return { "success": False, "error": f"Column '{col}' does not exist in table schema" }
            if not isinstance(val, str):
                return { "success": False, "error": f"Value for column '{col}' is not a string" }
        # Update record in place
        record = table["records"][record_index]
        for col, val in new_values.items():
            record["field_values"][col] = val
        return { "success": True, "message": "Record updated successfully" }

    def delete_record(self, table_name: str, record: Dict[str, str]) -> dict:
        """
        Remove a specific record from a table.

        Args:
            table_name (str): The name of the table.
            record (Dict[str, str]): The record to delete, as a mapping of column names to string values.

        Returns:
            dict:
                - On success: { "success": True, "message": "Record deleted from table <table_name>" }
                - If table does not exist: { "success": False, "error": "Table does not exist" }
                - If record does not exist: { "success": False, "error": "Record not found in table" }

        Constraints:
            - Table must exist.
            - Record is identified by full match of all field values.
        """
        if table_name not in self.tables:
            return {"success": False, "error": "Table does not exist"}

        table = self.tables[table_name]
        records = table["records"]

        for i, rec in enumerate(records):
            if rec["field_values"] == record:
                del records[i]
                return {"success": True, "message": f"Record deleted from table {table_name}"}

        return {"success": False, "error": "Record not found in table"}

    def bulk_insert_records(self, table_name: str, records: list) -> dict:
        """
        Insert multiple records into the specified table, ensuring all field values are text (str) and
        each record matches the table schema exactly.

        Args:
            table_name (str): Name of table to insert records into.
            records (List[Dict[str, str]]): List of dicts, each representing a record ("column_name": str value).

        Returns:
            dict: {
                "success": True,
                "message": "X records inserted into table 'table_name'"
            } or (on error)
            {
                "success": False,
                "error": "Descriptive error message"
            }

        Constraints:
            - The table must exist.
            - All keys in each record must be exactly the same as the columns in the table schema
              (no missing or extra columns).
            - All values must be strings.
            - All-or-nothing: if any record is invalid, no records are inserted.
        """
        if table_name not in self.tables:
            return { "success": False, "error": f"Table '{table_name}' does not exist" }

        table = self.tables[table_name]
        schema_columns = [col['column_name'] for col in table['columns']]
        schema_set = set(schema_columns)

        # Check each record for compliance
        for idx, record in enumerate(records):
            if not isinstance(record, dict):
                return { "success": False, "error": f"Record at position {idx} is not a dict" }
            record_keys = set(record.keys())
            if record_keys != schema_set:
                missing = schema_set - record_keys
                extra = record_keys - schema_set
                if missing and extra:
                    return { "success": False, "error": f"Record {idx} missing columns {sorted(missing)} and has extra columns {sorted(extra)}" }
                elif missing:
                    return { "success": False, "error": f"Record {idx} missing columns {sorted(missing)}" }
                else:
                    return { "success": False, "error": f"Record {idx} has extra columns {sorted(extra)}" }
            # Ensure all values are strings
            for k, v in record.items():
                if not isinstance(v, str):
                    return { "success": False, "error": f"Value for column '{k}' in record {idx} is not a string" }

        # All records valid, perform insertion
        for record in records:
            table['records'].append({"field_values": dict(record)})

        return {
            "success": True,
            "message": f"{len(records)} record(s) inserted into table '{table_name}'"
        }

    def truncate_table(self, table_name: str) -> dict:
        """
        Remove all records from the specified table, but keep the table schema (columns) intact.

        Args:
            table_name (str): The name of the table to truncate.

        Returns:
            dict: {
                "success": True,
                "message": "All records removed from table '<table_name>'."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The table must exist (table_name in self.tables).
            - Does NOT delete the table or its columns; only empties the records.
        """
        if table_name not in self.tables:
            return {
                "success": False,
                "error": f"Table '{table_name}' does not exist."
            }

        # Remove all records, preserve columns
        self.tables[table_name]['records'] = []

        return {
            "success": True,
            "message": f"All records removed from table '{table_name}'."
        }


class TextOnlyRelationalDatabase(BaseEnv):
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

    def list_tables(self, **kwargs):
        return self._call_inner_tool('list_tables', kwargs)

    def get_table_schema(self, **kwargs):
        return self._call_inner_tool('get_table_schema', kwargs)

    def list_table_records(self, **kwargs):
        return self._call_inner_tool('list_table_records', kwargs)

    def get_table_record_count(self, **kwargs):
        return self._call_inner_tool('get_table_record_count', kwargs)

    def get_table_column_names(self, **kwargs):
        return self._call_inner_tool('get_table_column_names', kwargs)

    def find_records_by_value(self, **kwargs):
        return self._call_inner_tool('find_records_by_value', kwargs)

    def search_records(self, **kwargs):
        return self._call_inner_tool('search_records', kwargs)

    def join_tables_on_column(self, **kwargs):
        return self._call_inner_tool('join_tables_on_column', kwargs)

    def get_all_text_entries(self, **kwargs):
        return self._call_inner_tool('get_all_text_entries', kwargs)

    def create_table(self, **kwargs):
        return self._call_inner_tool('create_table', kwargs)

    def drop_table(self, **kwargs):
        return self._call_inner_tool('drop_table', kwargs)

    def add_column_to_table(self, **kwargs):
        return self._call_inner_tool('add_column_to_table', kwargs)

    def remove_column_from_table(self, **kwargs):
        return self._call_inner_tool('remove_column_from_table', kwargs)

    def insert_record(self, **kwargs):
        return self._call_inner_tool('insert_record', kwargs)

    def update_record(self, **kwargs):
        return self._call_inner_tool('update_record', kwargs)

    def delete_record(self, **kwargs):
        return self._call_inner_tool('delete_record', kwargs)

    def bulk_insert_records(self, **kwargs):
        return self._call_inner_tool('bulk_insert_records', kwargs)

    def truncate_table(self, **kwargs):
        return self._call_inner_tool('truncate_table', kwargs)

