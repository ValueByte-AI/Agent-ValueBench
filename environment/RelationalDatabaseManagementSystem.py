# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, Any, TypedDict



class ColumnInfo(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Optional[Any]

class SchemaInfo(TypedDict):
    columns: List[ColumnInfo]
    primary_key: List[str]
    foreign_key: Dict[str, Dict[str, str]]  # column_name -> {referenced_table, referenced_column}

class ConstraintInfo(TypedDict):
    constraint_type: str
    columns: List[str]
    referenced_table: Optional[str]
    referenced_column: Optional[str]

class IndexInfo(TypedDict):
    index_name: str
    table_name: str
    columns: List[str]
    index_type: str

class TableInfo(TypedDict):
    table_name: str
    schema: SchemaInfo
    indexes: List[IndexInfo]
    constraints: List[ConstraintInfo]

class RecordInfo(TypedDict):
    table_name: str
    field_values: Dict[str, Any]  # mapping of column names to field values

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Relational Database Management System (RDBMS) stateful environment.
        """
        # Tables (metadata and definitions): {table_name: TableInfo}
        self.tables: Dict[str, TableInfo] = {}
        # Records (by table): {table_name: List[RecordInfo]}
        self.records: Dict[str, List[RecordInfo]] = {}

        # Entity mapping (for code clarity):
        # TableInfo   <-- Table entity (table_name, schema, indexes, constraints)
        # SchemaInfo  <-- Schema entity (columns, primary_key, foreign_key)
        # RecordInfo  <-- Record entity (table_name, field_values)
        # ConstraintInfo <-- Constraint entity (constraint_type, columns, referenced_table, referenced_column)
        # IndexInfo   <-- Index entity (index_name, table_name, columns, index_type)

        # Constraint Rules (documentation only, not enforced here):
        # - Cannot violate primary key, foreign key, or other integrity constraints when deleting records.
        # - All changes are performed within transactions to ensure atomicity.
        # - Data types for columns are enforced for all field_values.
        # - Referential integrity must be maintained during deletion (e.g., cascading deletes if specified).
        # - Indexes must reflect updates or deletions for efficient querying.

    @staticmethod
    def _coerce_transaction_flag(value: Any) -> bool:
        if isinstance(value, str):
            return value.strip().lower() == "true"
        return bool(value)

    @staticmethod
    def _is_foreign_key_constraint(constraint_type: Any) -> bool:
        normalized = str(constraint_type or "").strip().lower().replace("_", " ")
        return normalized.startswith("foreign key")

    @staticmethod
    def _constraint_has_cascade(constraint_type: Any) -> bool:
        normalized = str(constraint_type or "").strip().lower().replace("_", " ")
        return "cascade" in normalized

    @staticmethod
    def _normalize_foreign_key_target(target: Any) -> Dict[str, str]:
        if not isinstance(target, dict):
            return {}
        if "referenced_table" in target or "referenced_column" in target:
            referenced_table = target.get("referenced_table")
            referenced_column = target.get("referenced_column")
            if isinstance(referenced_table, str) and isinstance(referenced_column, str):
                return {
                    "referenced_table": referenced_table,
                    "referenced_column": referenced_column,
                }
            return {}
        if len(target) == 1:
            referenced_table, referenced_column = next(iter(target.items()))
            if isinstance(referenced_table, str) and isinstance(referenced_column, str):
                return {
                    "referenced_table": referenced_table,
                    "referenced_column": referenced_column,
                }
        return {}

    @staticmethod
    def _normalize_foreign_key_entry(column_name: Any, target: Any) -> tuple[str, Dict[str, str]]:
        child_column = str(column_name or "").strip()

        if isinstance(target, dict) and len(target) == 1:
            inner_column, reference = next(iter(target.items()))
            if isinstance(inner_column, str) and isinstance(reference, str) and "." in reference:
                referenced_table, referenced_column = reference.split(".", 1)
                if referenced_table and referenced_column:
                    return inner_column, {
                        "referenced_table": referenced_table,
                        "referenced_column": referenced_column,
                    }

        normalized_target = _GeneratedEnvImpl._normalize_foreign_key_target(target)
        if normalized_target:
            return child_column, normalized_target

        return child_column, {}

    def get_table_schema(self, table_name: str) -> dict:
        """
        Retrieve the schema for a given table.

        Args:
            table_name (str): Name of the table whose schema is requested.

        Returns:
            dict: {
                "success": True,
                "data": SchemaInfo  # The table schema information (columns, PK, FK)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. table does not exist
            }

        Constraints:
            - The specified table must exist in the database.
            - No constraints enforced for read-only schema retrieval.
        """
        table = self.tables.get(table_name)
        if not table:
            return { "success": False, "error": "Table does not exist" }

        schema = table["schema"]
        return { "success": True, "data": schema }

    def get_table_constraints(self, table_name: str) -> dict:
        """
        Get all integrity constraints (primary key, foreign key, unique, check, etc.) defined for the specified table.

        Args:
            table_name (str): The name of the table to query.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": List[ConstraintInfo],   # List of constraint definitions, may be empty
                  }
                - On failure: {
                      "success": False,
                      "error": str                    # Reason, e.g. table does not exist
                  }

        Constraints:
            - The specified table must exist in the database.
        """
        table = self.tables.get(table_name)
        if table is None:
            return { "success": False, "error": "Table does not exist." }

        constraints = table.get("constraints", [])
        return { "success": True, "data": constraints }

    def get_table_indexes(self, table_name: str) -> dict:
        """
        List all index metadata for a table (names, columns, type).

        Args:
            table_name (str): Name of the table for which to list indexes.

        Returns:
            dict: 
                - On success:
                    {
                      "success": True,
                      "data": List[IndexInfo]  # List of all index definitions for the table (may be empty)
                    }
                - On failure:
                    {
                      "success": False,
                      "error": str  # Error message, e.g., table not found.
                    }

        Constraints:
            - The table must exist in the RDBMS.
        """
        table = self.tables.get(table_name)
        if not table:
            return { "success": False, "error": f"Table '{table_name}' does not exist" }
        return { "success": True, "data": table.get("indexes", []) }

    def get_all_table_names(self) -> dict:
        """
        Retrieve a list of all table names present in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of table names (may be empty if no tables exist)
            }

        Constraints:
            - None (simple query, always succeeds)
        """
        table_names = list(self.tables.keys())
        return { "success": True, "data": table_names }

    def query_records(self, table_name: str, filters: Dict[str, Any]) -> dict:
        """
        Retrieve records from a specified table, applying filtering conditions to column values.

        Args:
            table_name (str): The name of the table to query.
            filters (dict): A dictionary mapping column names to desired values.
                            Only records matching all these pairs will be returned.

        Returns:
            dict: {
                "success": True,
                "data": List[RecordInfo],  # List may be empty if no records match
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure (e.g., table does not exist, invalid filter column)
            }

        Constraints:
            - The table must exist.
            - All filter keys must be valid column names in the table's schema.
        """
        if table_name not in self.tables:
            return { "success": False, "error": f"Table '{table_name}' does not exist" }

        schema_columns = {col['name'] for col in self.tables[table_name]['schema']['columns']}

        # Validate filter columns
        for col in filters.keys():
            if col not in schema_columns:
                return {
                    "success": False,
                    "error": f"Invalid filter column '{col}'; not found in table schema"
                }

        all_records = self.records.get(table_name, [])
        matching_records = []
        for record in all_records:
            match = True
            for key, value in filters.items():
                record_value = record['field_values'].get(key)
                if isinstance(value, (list, tuple, set)):
                    if record_value not in value:
                        match = False
                        break
                elif record_value != value:
                    match = False
                    break
            if match:
                matching_records.append(record)

        return { "success": True, "data": matching_records }

    def get_record_by_primary_key(self, table_name: str, primary_key_values: Dict[str, Any]) -> dict:
        """
        Fetch a unique record from the specified table by matching primary key column(s) to provided values.

        Args:
            table_name (str): Name of the table to search in.
            primary_key_values (Dict[str, Any]): Mapping from primary key column names to their desired values.
                                                 All primary key columns and no extraneous columns must be provided.

        Returns:
            dict:
              On success:
                {"success": True, "data": RecordInfo}  # The matching record
              On failure:
                {"success": False, "error": str}

        Constraints:
            - Table must exist.
            - Table must define a primary key.
            - All primary key columns must be provided in `primary_key_values`.
            - Exactly one record must match, or return error if none.
        """
        # Check if table exists
        table = self.tables.get(table_name)
        if table is None:
            return {"success": False, "error": f"Table '{table_name}' does not exist"}

        schema = table.get("schema")
        if schema is None or "primary_key" not in schema:
            return {"success": False, "error": f"Schema or primary key not defined for table '{table_name}'"}

        pk_cols = schema["primary_key"]
        if not pk_cols:
            return {"success": False, "error": f"No primary key defined for table '{table_name}'"}

        # Must provide all (and only) the PK columns
        if set(primary_key_values.keys()) != set(pk_cols):
            return {"success": False, "error": f"Primary key columns must match {pk_cols}"}

        # Search for a record in self.records[table_name] that matches all primary key values
        records = self.records.get(table_name, [])
        for record in records:
            field_values = record.get("field_values", {})
            if all(field_values.get(col) == primary_key_values[col] for col in pk_cols):
                return {"success": True, "data": record}

        return {"success": False, "error": "No record found with the given primary key(s)"}

    def get_related_records_by_foreign_key(self, table_name: str, primary_key_values: Dict[str, Any]) -> dict:
        """
        For a given record (by table and primary key values), retrieve all records in related
        (children or parent) tables via foreign key relationships.

        Args:
            table_name (str): Name of the table containing the record.
            primary_key_values (dict): Mapping from primary key column names to values.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "parent_records": List[dict],  # Each: { "table": table_name, "record": RecordInfo }
                    "child_records":  List[dict],  # Each: { "table": table_name, "record": RecordInfo }
                }
            }
            or
            { "success": False, "error": str }

        Constraints:
            - Table must exist.
            - Record with specified PK must exist.
            - Foreign key relationships as per schema/constraints.
        """
        # 1. Table exists?
        if table_name not in self.tables:
            return { "success": False, "error": f"Table '{table_name}' does not exist." }
        table_info = self.tables[table_name]
        pk_cols = table_info['schema']['primary_key']
        # 2. PK columns provided?
        if not all(col in primary_key_values for col in pk_cols):
            return { "success": False, "error": "Primary key values incomplete." }
        # 3. Locate the record
        candidates = [
            rec for rec in self.records.get(table_name, [])
            if all(rec['field_values'].get(pk) == primary_key_values[pk] for pk in pk_cols)
        ]
        if not candidates:
            return { "success": False, "error": "Record not found with provided primary key values." }
        record = candidates[0]

        # --- Find parent records (if this is a FK child) ---
        parent_records = []
        for fk_col, raw_target in table_info['schema'].get('foreign_key', {}).items():
            fk_target = self._normalize_foreign_key_target(raw_target)
            ref_table = fk_target.get('referenced_table')
            ref_col = fk_target.get('referenced_column')
            if not ref_table or not ref_col:
                continue
            fk_val = record['field_values'].get(fk_col)
            if fk_val is not None:
                parent_recs = [
                    r for r in self.records.get(ref_table, [])
                    if r['field_values'].get(ref_col) == fk_val
                ]
                for pr in parent_recs:
                    parent_records.append({ "table": ref_table, "record": pr })

        # --- Find child records in other tables referencing this (if any) ---
        child_records = []
        for other_table, other_info in self.tables.items():
            # For all other tables, see if any FK points to this table's PK
            schema_fk = other_info['schema'].get('foreign_key', {})
            for fk_col, raw_target in schema_fk.items():
                fk_target = self._normalize_foreign_key_target(raw_target)
                if (fk_target.get('referenced_table') == table_name and
                    fk_target.get('referenced_column') in pk_cols):
                    # look for records where the FK column matches the PK value
                    pk_val = primary_key_values[fk_target['referenced_column']]
                    child_recs = [
                        r for r in self.records.get(other_table, [])
                        if r['field_values'].get(fk_col) == pk_val
                    ]
                    for cr in child_recs:
                        child_records.append({ "table": other_table, "record": cr })

        return {
            "success": True,
            "data": {
                "parent_records": parent_records,
                "child_records": child_records
            }
        }

    def get_constraint_details(self, table_name: str, constraint_type: str, columns: list) -> dict:
        """
        Fetch detailed information about a given constraint on a table.

        Args:
            table_name (str): The name of the table to search.
            constraint_type (str): The type of the constraint (e.g. 'primary_key', 'foreign_key', 'unique', etc.).
            columns (List[str]): The list of column names that define the constraint (order-sensitive).

        Returns:
            dict:
                On success: { "success": True, "data": ConstraintInfo }
                On failure: { "success": False, "error": str }
    
        Constraints:
            - The table must exist and contain a matching constraint with the specified type and columns.
        """
        if table_name not in self.tables:
            return { "success": False, "error": "Table does not exist" }

        constraints = self.tables[table_name].get("constraints", [])

        # Compare columns as lists (order sensitive, as enforced by some DBMS)
        for constraint in constraints:
            if (
                str(constraint.get("constraint_type", "")).strip().lower().replace("_", " ") ==
                str(constraint_type).strip().lower().replace("_", " ") and
                constraint.get("columns") == columns
            ):
                return { "success": True, "data": constraint }

        return { "success": False, "error": "No matching constraint found for the given type and columns" }

    def delete_records_with_filter(self, table_name: str, filter_conditions: Dict[str, Any]) -> dict:
        """
        Delete records from a specified table that match given filter conditions,
        enforcing primary key, foreign key, and other integrity constraints.

        Args:
            table_name (str): Name of the table from which to delete records.
            filter_conditions (Dict[str, Any]): Mapping of column names to values; records
                where all specified columns equal given values will be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Deleted X records from table <table_name>."
            }
            or
            dict: {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Table must exist.
            - Cannot violate primary key, foreign key, or integrity constraints.
            - Referential integrity enforced (no orphaned foreign keys).
            - Changes are atomic.
            - Indexes updated.
        """
        # Check table existence
        if table_name not in self.tables:
            return {"success": False, "error": f"Table '{table_name}' does not exist."}

        records = self.records.get(table_name, [])
        table_info = self.tables[table_name]
        schema = table_info["schema"]
        constraints = table_info.get("constraints", [])

        # Helper: filter records by filter_conditions
        def matches(record: RecordInfo) -> bool:
            for col, val in filter_conditions.items():
                if col not in record["field_values"] or record["field_values"][col] != val:
                    return False
            return True

        # Find records to delete
        records_to_delete = [r for r in records if matches(r)]
        if not records_to_delete:
            return {"success": True, "message": f"Deleted 0 records from table '{table_name}'."}

        deleted_pk_values_list = [
            {
                pk: record["field_values"].get(pk)
                for pk in schema.get("primary_key", [])
                if pk in record.get("field_values", {})
            }
            for record in records_to_delete
        ]

        needs_cascade_delete = False

        # -- Integrity checking: foreign keys and referential integrity --
        # For each record to delete, check if it is referenced by another table (foreign key constraints)
        for constraint in constraints:
            if self._is_foreign_key_constraint(constraint["constraint_type"]):
                # This is an outbound FK (from table_name to referenced)
                continue  # We want inbound references only (other tables referencing this one)
        # Check if other tables reference this table via FK:
        for other_table, other_table_info in self.tables.items():
            other_schema = other_table_info["schema"]
            other_constraints = other_table_info.get("constraints", [])
            for c in other_constraints:
                if self._is_foreign_key_constraint(c["constraint_type"]) and \
                   c.get("referenced_table") == table_name:
                    # Foreign key in other_table points to this table
                    fk_col = c["columns"][0]
                    referenced_col = c["referenced_column"]
                    # Build set of PK or referenced values we're deleting
                    deleted_values = set(r["field_values"].get(referenced_col) for r in records_to_delete)
                    # Scan other_table records for references
                    for rec in self.records.get(other_table, []):
                        if rec["field_values"].get(fk_col) in deleted_values:
                            if self._constraint_has_cascade(c.get("constraint_type")):
                                needs_cascade_delete = True
                                continue
                            # Referential integrity violated: orphan
                            return {
                                "success": False,
                                "error": f"Deletion would violate referential integrity. Record in table '{other_table}' references '{table_name}'."
                            }

        if needs_cascade_delete and deleted_pk_values_list:
            cascade_result = self.cascade_delete_related_records(table_name, deleted_pk_values_list)
            if not cascade_result.get("success", False):
                return cascade_result

        # -- All checks passed: perform deletion atomically --
        # Remove from records list:
        remaining_records = [r for r in records if not matches(r)]
        num_deleted = len(records_to_delete)
        self.records[table_name] = remaining_records

        self.update_indexes_after_deletion(table_name)

        return {
            "success": True,
            "message": f"Deleted {num_deleted} records from table '{table_name}'."
        }

    def begin_transaction(self) -> dict:
        """
        Start a transactional context to batch multiple operations atomically.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction started."
            }
            or
            {
                "success": False,
                "error": "A transaction is already active."
            }

        Constraints:
            - If a transaction is already active, cannot begin a new one
              (nested transactions not supported).
        """
        active = self._coerce_transaction_flag(
            getattr(self, "_in_transaction", getattr(self, "in_transaction", False))
        )
        if active:
            return {
                "success": False,
                "error": "A transaction is already active."
            }
        self._transaction_backup = {
            "tables": copy.deepcopy(self.tables),
            "records": copy.deepcopy(self.records),
        }
        self._transaction_buffer = {}
        self._in_transaction = True
        self.in_transaction = True
        return {
            "success": True,
            "message": "Transaction started."
        }

    def commit_transaction(self) -> dict:
        """
        Finalize and persist all changes made during the current transaction.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction committed successfully."
            }
            or
            {
                "success": False,
                "error": "No active transaction to commit."
            }

        Constraints:
            - There must be an active transaction.
            - All changes are finalized and persisted.
            - Any transaction buffer/state should be cleared upon successful commit.
        """
        active = self._coerce_transaction_flag(
            getattr(self, "_in_transaction", getattr(self, "in_transaction", False))
        )
        if not active:
            return {"success": False, "error": "No active transaction to commit."}

        # Here we would apply the changes staged during the transaction.
        # For this simulation, we assume changes have been applied to the main state.

        # Clear transaction state
        self._in_transaction = False
        self.in_transaction = False
        self._transaction_buffer = {}
        self._transaction_backup = {}

        return {"success": True, "message": "Transaction committed successfully."}

    def rollback_transaction(self) -> dict:
        """
        Abort the current transaction and revert the database state (tables, records) 
        to what it was before the transaction began.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction rolled back. All changes reverted."
            }
            or
            {
                "success": False,
                "error": str  # e.g., "No active transaction to rollback."
            }

        Constraints:
            - There must be an active transaction.
            - All uncommitted changes (to tables and records) are undone.
            - Transactional atomicity is enforced.
        """
        active = self._coerce_transaction_flag(
            getattr(self, "_in_transaction", getattr(self, "in_transaction", False))
        )
        backup = getattr(self, "_transaction_backup", None)
        if isinstance(backup, str):
            try:
                backup = json.loads(backup)
            except Exception:
                backup = None
        if (not active) or not isinstance(backup, dict) or "tables" not in backup or "records" not in backup:
            return {"success": False, "error": "No active transaction to rollback."}

        # Restore the backup state
        self.tables = copy.deepcopy(backup['tables'])
        self.records = copy.deepcopy(backup['records'])
    
        # Clear the backup to mark transaction as closed
        self._transaction_backup = {}
        self._transaction_buffer = {}
        self._in_transaction = False
        self.in_transaction = False

        return {
            "success": True,
            "message": "Transaction rolled back. All changes reverted."
        }

    def cascade_delete_related_records(
        self, 
        parent_table: str, 
        deleted_pk_values_list: list
    ) -> dict:
        """
        Automatically delete dependent records in related tables if cascading is required by the schema/constraints.
    
        Args:
            parent_table (str): The name of the table whose records have been deleted.
            deleted_pk_values_list (List[Dict[str, Any]]): 
                A list of dicts, each representing the field_values of a deleted primary key in the parent_table.
                Example: [{'id': 1}, {'id': 2}]

        Returns:
            dict:
                Success => { "success": True, "message": "Cascade delete completed for dependent records." }
                Error => { "success": False, "error": <reason> }

        Constraints enforced:
            - Only constraints specifying ON DELETE CASCADE will trigger deletions.
            - Referential cascade deletion recurses as far as required.

        Notes:
            - This implementation assumes constraints with cascade have constraint_type containing the word "CASCADE" 
              (e.g., 'FOREIGN KEY CASCADE').
            - This is a simple logic: for a robust system, you'd want a specific field (e.g., 'on_delete').

        """

        # Check if parent table exists
        if parent_table not in self.tables:
            return { "success": False, "error": f"Parent table '{parent_table}' does not exist." }
    
        # Fetch the list of primary key column names
        pk_cols = self.tables[parent_table]['schema']['primary_key']
        if not pk_cols:
            return { "success": False, "error": f"Parent table '{parent_table}' has no primary key." }

        # For each table, check for foreign key constraints that reference this table AND have CASCADE
        for child_table, table_info in self.tables.items():
            # Search for each constraint in child table
            for constr in table_info.get('constraints', []):
                if (
                    constr['constraint_type'].startswith('FOREIGN KEY') and 
                    constr.get('referenced_table', '') == parent_table and
                    'CASCADE' in constr['constraint_type']
                ):
                    child_fk_cols = constr['columns']        # columns in child table
                    referenced_cols = [constr['referenced_column']] if constr['referenced_column'] else []
                    if not referenced_cols or not child_fk_cols:
                        continue  # skip invalid constraint specs

                    # For each deleted parent PK, find and delete referencing child records
                    remaining_child_records = []
                    deleted_child_records = []
                    for rec in self.records.get(child_table, []):
                        match = False
                        for pk_values in deleted_pk_values_list:
                            # Map child FK columns to parent PK columns
                            all_match = True
                            for fk_col, ref_col in zip(child_fk_cols, referenced_cols):
                                if fk_col not in rec['field_values'] or ref_col not in pk_values:
                                    all_match = False
                                    break
                                if rec['field_values'][fk_col] != pk_values[ref_col]:
                                    all_match = False
                                    break
                            if all_match:
                                match = True
                                break
                        if match:
                            deleted_child_records.append(rec)
                        else:
                            remaining_child_records.append(rec)
                    # Update child table records
                    self.records[child_table] = remaining_child_records
                    self.update_indexes_after_deletion(child_table)

                    # RECURSIVELY apply cascade for each deleted child record
                    if deleted_child_records:
                        child_pk_cols = self.tables[child_table]['schema']['primary_key']
                        if child_pk_cols:
                            deleted_child_pks = [
                                {col: rec['field_values'][col] for col in child_pk_cols if col in rec['field_values']}
                                for rec in deleted_child_records
                            ]
                            self.cascade_delete_related_records(child_table, deleted_child_pks)
        return { "success": True, "message": "Cascade delete completed for dependent records." }

    def update_indexes_after_deletion(self, table_name: str) -> dict:
        """
        Update all affected indexes for the specified table after records have been deleted, to maintain 
        efficient querying and data integrity.

        Args:
            table_name (str): Name of the table whose indexes need to be updated.

        Returns:
            dict: {
                "success": True,
                "message": "Indexes updated after deletion."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The table must exist.
            - All index definitions for the table should be updated to reflect deletion.
            - Indexes must remain consistent with the actual records.
        """
        table = self.tables.get(table_name)
        if not table:
            return {"success": False, "error": f"Table '{table_name}' does not exist."}
        indexes = table.get("indexes", [])
        if not indexes:
            # No indexes to update, but operation is still considered successful
            return {"success": True, "message": f"No indexes to update for table '{table_name}'."}

        # In a real RDBMS we would now rebuild or update the physical index structures.
        # Here, as an environment simulation, we'll assume indexes are marked as updated.
        for idx in indexes:
            # For simulation, mark index as "up-to-date" after deletion
            # Optionally, you might add e.g. idx['last_updated'] = time.time()
            idx["last_updated"] = "after_deletion"  # Placeholder flag

        return {"success": True, "message": f"Indexes updated after deletion for table '{table_name}'."}

    def enforce_constraint_on_delete(self, table_name: str, filter_conditions: dict) -> dict:
        """
        Perform integrity checks to block or permit deletion based on constraints.

        Args:
            table_name (str): Name of the table where deletion is intended.
            filter_conditions (dict): Column-value pairs for identifying target records.
    
        Returns:
            dict: {
                "success": bool,
                "message"/"error": str
            }

        Constraints:
            - Blocks deletion if it would violate foreign key constraints (i.e., if other tables reference PK values being deleted and CASCADE is not defined).
            - If the table or relevant constraints do not exist, deletion is blocked or permitted accordingly.
            - No-Op (permit) if no matching records.
        """
        # 1. Table exists?
        if table_name not in self.tables:
            return {"success": False, "error": "Table does not exist"}

        table_info = self.tables[table_name]
        schema = table_info["schema"]
        pk_columns = schema.get("primary_key", [])
        constraints = table_info.get("constraints", [])

        # 2. Find records matching filter_conditions
        records = self.records.get(table_name, [])
        def record_matches_filter(record):
            return all(record["field_values"].get(k) == v for k, v in filter_conditions.items())

        records_to_delete = [r for r in records if record_matches_filter(r)]
        if not records_to_delete:
            return {"success": True, "message": "No matching records; deletion would have no effect."}

        # 3. For each constraint (especially FK), check safety
        # a) Find if any other table refers to these records
        for other_table, other_table_info in self.tables.items():
            if other_table == table_name:
                continue
            other_schema = other_table_info["schema"]
            other_constraints = other_table_info.get("constraints", [])
            for constraint in other_constraints:
                if self._is_foreign_key_constraint(constraint["constraint_type"]) and \
                   constraint.get("referenced_table") == table_name:
                    ref_col = constraint.get("referenced_column")
                    fk_cols = constraint.get("columns", [])
                    # Collect PK values being deleted
                    pk_values_to_delete = [
                        tuple(r["field_values"][col] for col in pk_columns)
                        for r in records_to_delete
                    ]
                    # For all records in other_table:
                    for other_record in self.records.get(other_table, []):
                        # If FK in other_record matches any PK being deleted, block unless CASCADE (not modeled here)
                        fk_val = tuple(other_record["field_values"].get(col) for col in fk_cols)
                        # ref_col could be more than one col, handle as tuple
                        # (For now, assume 1-column PK/FK for simplicity)
                        for pk_value in pk_values_to_delete:
                            # Compare only the columns count that exist
                            if fk_val == pk_value:
                                if self._constraint_has_cascade(constraint.get("constraint_type")):
                                    continue
                                # Violation found: deletion blocked
                                msg = (f"Deletion blocked: record in table '{table_name}' is referenced by table "
                                       f"'{other_table}' via foreign key {fk_cols}.")
                                return {"success": False, "error": msg}

        # 4. If all constraints pass:
        return {"success": True, "message": "Deletion permitted by all constraints."}


class RelationalDatabaseManagementSystem(BaseEnv):
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
            if key == "tables" and isinstance(value, dict):
                normalized_tables = copy.deepcopy(value)
                for table_info in normalized_tables.values():
                    if not isinstance(table_info, dict):
                        continue
                    schema = table_info.get("schema")
                    if not isinstance(schema, dict):
                        continue
                    foreign_key = schema.get("foreign_key")
                    if isinstance(foreign_key, dict):
                        normalized_foreign_key = {}
                        for column_name, target in foreign_key.items():
                            child_column, normalized_target = _GeneratedEnvImpl._normalize_foreign_key_entry(
                                column_name,
                                target,
                            )
                            if child_column and normalized_target:
                                normalized_foreign_key[child_column] = normalized_target
                        schema["foreign_key"] = normalized_foreign_key
                value = normalized_tables
            if key in {"in_transaction", "_in_transaction"}:
                normalized = _GeneratedEnvImpl._coerce_transaction_flag(value)
                setattr(env, "in_transaction", normalized)
                setattr(env, "_in_transaction", normalized)
                continue
            if key in {"_transaction_buffer", "_transaction_backup"} and isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    value = {}
                else:
                    try:
                        parsed = json.loads(stripped)
                    except Exception:
                        parsed = {}
                    value = parsed if isinstance(parsed, dict) else {}
            if key == "cascade_delete_related_records" and callable(getattr(env, key, None)):
                continue
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

    def get_table_schema(self, **kwargs):
        return self._call_inner_tool('get_table_schema', kwargs)

    def get_table_constraints(self, **kwargs):
        return self._call_inner_tool('get_table_constraints', kwargs)

    def get_table_indexes(self, **kwargs):
        return self._call_inner_tool('get_table_indexes', kwargs)

    def get_all_table_names(self, **kwargs):
        return self._call_inner_tool('get_all_table_names', kwargs)

    def query_records(self, **kwargs):
        return self._call_inner_tool('query_records', kwargs)

    def get_record_by_primary_key(self, **kwargs):
        return self._call_inner_tool('get_record_by_primary_key', kwargs)

    def get_related_records_by_foreign_key(self, **kwargs):
        return self._call_inner_tool('get_related_records_by_foreign_key', kwargs)

    def get_constraint_details(self, **kwargs):
        return self._call_inner_tool('get_constraint_details', kwargs)

    def delete_records_with_filter(self, **kwargs):
        return self._call_inner_tool('delete_records_with_filter', kwargs)

    def begin_transaction(self, **kwargs):
        return self._call_inner_tool('begin_transaction', kwargs)

    def commit_transaction(self, **kwargs):
        return self._call_inner_tool('commit_transaction', kwargs)

    def rollback_transaction(self, **kwargs):
        return self._call_inner_tool('rollback_transaction', kwargs)

    def cascade_delete_related_records(self, **kwargs):
        return self._call_inner_tool('cascade_delete_related_records', kwargs)

    def update_indexes_after_deletion(self, **kwargs):
        return self._call_inner_tool('update_indexes_after_deletion', kwargs)

    def enforce_constraint_on_delete(self, **kwargs):
        return self._call_inner_tool('enforce_constraint_on_delete', kwargs)
