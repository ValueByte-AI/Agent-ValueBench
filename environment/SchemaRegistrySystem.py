# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict
from typing import List, Dict, Any
import uuid
from datetime import datetime
import time
from typing import Optional, Dict



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    created_a: str

class SchemaInfo(TypedDict):
    schema_id: str
    name: str
    creator_user_id: str
    version: int
    metadata: Dict[str, Any]
    created_a: str

class FieldInfo(TypedDict):
    field_id: str
    schema_id: str
    field_name: str
    field_type: str
    a: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for a schema registry system.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # (entity: User, attributes: _id, username, email, created_a)

        # Schemas: {schema_id: SchemaInfo}
        self.schemas: Dict[str, SchemaInfo] = {}
        # (entity: Schema, attributes: schema_id, name, creator_user_id, version, metadata, created_a)

        # Fields: {field_id: FieldInfo}
        self.fields: Dict[str, FieldInfo] = {}
        # (entity: Field, attributes: field_id, schema_id, field_name, field_type, a)

        # Constraints:
        # - Each schema must have a unique schema_id.
        # - A schema must be associated with a valid user as its creator.
        # - Field names must be unique within a schema.
        # - Schemas can have multiple versions, and schemas with the same name but different versions must be distinguishable.
        # - Deleting a schema should also remove (or logically disassociate) its fields.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve UserInfo (including _id) for the user with the specified username.

        Args:
            username (str): The username to look up.

        Returns:
            dict:
                - If user is found:
                    {"success": True, "data": UserInfo}
                - If not found:
                    {"success": False, "error": "User not found"}
        Constraints:
            - Usernames are assumed to be unique in the registry.
        """
        for user in self.users.values():
            if user["username"] == username:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user information (UserInfo) by user _id.

        Args:
            _id (str): The unique user identifier.

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - The user _id must exist in the registry.
        """
        if _id in self.users:
            return { "success": True, "data": self.users[_id] }
        else:
            return { "success": False, "error": "User not found" }

    def list_schemas_by_creator(self, user_id: str) -> dict:
        """
        List all schemas created by a specific user id.

        Args:
            user_id (str): The _id field of the user.

        Returns:
            dict: {
                "success": True,
                "data": [
                    {
                        "schema_id": str,
                        "name": str,
                        "version": int,
                        "metadata": dict
                    },
                    ...
                ]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist in the registry.
            - Returns all schemas whose creator_user_id matches the input user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        result = []
        for schema in self.schemas.values():
            if schema.get("creator_user_id") == user_id:
                result.append({
                    "schema_id": schema["schema_id"],
                    "name": schema["name"],
                    "version": schema["version"],
                    "metadata": schema["metadata"]
                })
        return { "success": True, "data": result }

    def get_schema_by_id(self, schema_id: str) -> dict:
        """
        Retrieve the SchemaInfo for a given schema_id.

        Args:
            schema_id (str): Unique identifier of the schema to retrieve.

        Returns:
            dict:
                - If found: {"success": True, "data": SchemaInfo}
                - If not found: {"success": False, "error": "Schema ID not found"}

        Constraints:
            - schema_id must exist in self.schemas.
        """
        schema_info = self.schemas.get(schema_id)
        if schema_info is None:
            return { "success": False, "error": "Schema ID not found" }
        return { "success": True, "data": schema_info }

    def list_fields_by_schema_id(self, schema_id: str) -> dict:
        """
        List all fields (FieldInfo) for a given schema_id.

        Args:
            schema_id (str): The schema's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[FieldInfo],  # List of fields belonging to the schema (may be empty)
            }
            or
            {
                "success": False,
                "error": "Schema not found"
            }

        Constraints:
            - The schema_id must exist in the registry. If not, error.
            - Field names are unique within a schema (not directly relevant for listing).
        """
        if schema_id not in self.schemas:
            return {"success": False, "error": "Schema not found"}
    
        result = [
            field_info for field_info in self.fields.values()
            if field_info["schema_id"] == schema_id
        ]
        return {"success": True, "data": result}

    def get_field_by_id(self, field_id: str) -> dict:
        """
        Retrieve the FieldInfo for the specified field_id.

        Args:
            field_id (str): The unique identifier of the field.

        Returns:
            dict: {
                "success": True,
                "data": FieldInfo  # The field's information
            }
            or
            {
                "success": False,
                "error": str  # If not found, an error description
            }
        """
        field_info = self.fields.get(field_id)
        if field_info is None:
            return {"success": False, "error": "Field not found"}
        return {"success": True, "data": field_info}

    def list_schema_versions_by_name(self, schema_name: str) -> dict:
        """
        Retrieve all SchemaInfo records with the same schema name, corresponding to all versions of the specified schema.

        Args:
            schema_name (str): The name of the schema to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[SchemaInfo]  # All schemas with this name (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. invalid schema name
            }

        Constraints:
            - schema_name must not be empty.
        """
        if not schema_name or not isinstance(schema_name, str):
            return { "success": False, "error": "Invalid schema name" }

        result = [
            schema_info for schema_info in self.schemas.values()
            if schema_info["name"] == schema_name
        ]

        return { "success": True, "data": result }

    def list_all_users(self) -> dict:
        """
        Retrieve all registered users.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[UserInfo]  # List of all users, possibly empty
                }

        Constraints:
            - No input parameters required.
            - Returns all users present in the system.
            - If no users exist, returns an empty list.
        """
        user_list = list(self.users.values())
        return {
            "success": True,
            "data": user_list
        }


    def create_schema(
        self, 
        schema_id: str, 
        name: str, 
        creator_user_id: str, 
        version: int,
        metadata: Dict[str, Any], 
        created_a: str, 
        fields: List[Dict[str, Any]]
    ) -> dict:
        """
        Registers a new schema for a user, with its fields.
    
        Args:
            schema_id (str): Unique schema identifier.
            name (str): Schema name.
            creator_user_id (str): User ID of the creator (must exist).
            version (int): Initial version.
            metadata (dict): Additional metadata.
            created_a (str): Timestamp of creation.
            fields (list of dict): Each dict should include at least 'field_name', 'field_type', 'a'.
        
        Returns:
            dict: {
                "success": True,
                "message": "...",
            }
            or
            {
                "success": False,
                "error": "...",
            }
        
        Constraints:
            - schema_id must be unique.
            - creator_user_id must exist.
            - Field names must be unique within this schema.
        """
        # Check schema_id uniqueness
        if schema_id in self.schemas:
            return { "success": False, "error": "Schema ID already exists." }
    
        # Check user existence
        if creator_user_id not in self.users:
            return { "success": False, "error": "Creator user does not exist." }
    
        # Check field name uniqueness within supplied fields
        field_names = [f['field_name'] for f in fields]
        if len(field_names) != len(set(field_names)):
            return { "success": False, "error": "Duplicate field names provided in fields list." }
    
        # Add schema
        schema_info = {
            "schema_id": schema_id,
            "name": name,
            "creator_user_id": creator_user_id,
            "version": version,
            "metadata": metadata,
            "created_a": created_a,
        }
        self.schemas[schema_id] = schema_info
    
        # Add fields
        field_count = 0
        for idx, field in enumerate(fields):
            # Generate a unique field_id (could concatenate schema_id and index)
            field_id = f"{schema_id}:{field['field_name']}"
            # Even though schema is new, double check field_id uniqueness
            if field_id in self.fields:
                return { "success": False, "error": f"Field ID collision: {field_id}" }
            field_info = {
                "field_id": field_id,
                "schema_id": schema_id,
                "field_name": field["field_name"],
                "field_type": field.get("field_type", ""),
                "a": field.get("a", ""),
            }
            self.fields[field_id] = field_info
            field_count += 1
    
        return { "success": True, "message": f"Schema created with {field_count} fields." }

    def update_schema_metadata(self, schema_id: str, metadata: dict = None, version: int = None) -> dict:
        """
        Modify the metadata and/or version of an existing schema.

        Args:
            schema_id (str): The schema's unique identifier.
            metadata (dict, optional): New metadata to set for the schema (replaces the old).
            version (int, optional): New version number for the schema.

        Returns:
            dict: {
                "success": True,
                "message": "Schema metadata (and/or version) updated."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The schema with the given schema_id must exist.
            - If updating version: for this schema's name, there must be no other schema
              with the same name and the proposed new version.
            - Version must be a positive integer, if supplied.
        """

        schema = self.schemas.get(schema_id)
        if not schema:
            return {"success": False, "error": "Schema not found"}

        # Handle version update with conflict check
        if version is not None:
            if not isinstance(version, int) or version <= 0:
                return {"success": False, "error": "Version must be a positive integer"}
            # Find if another schema with same name and this version exists
            for s_id, s_info in self.schemas.items():
                if (
                    s_id != schema_id
                    and s_info["name"] == schema["name"]
                    and s_info["version"] == version
                ):
                    return {"success": False, "error": f"Schema version {version} for name '{schema['name']}' already exists."}
            schema["version"] = version

        # Handle metadata update (replace old metadata)
        if metadata is not None:
            if not isinstance(metadata, dict):
                return {"success": False, "error": "Metadata must be a dictionary"}
            schema["metadata"] = metadata

        return {"success": True, "message": "Schema metadata (and/or version) updated."}

    def delete_schema(self, schema_id: str) -> dict:
        """
        Delete a schema identified by schema_id and also remove all fields belonging to it.

        Args:
            schema_id (str): Unique identifier of the schema to be deleted.

        Returns:
            dict:
                - success (bool): Operation result.
                - message (str): Success description if successful.
                - error (str): Reason if failed.

        Constraints:
            - The schema must exist.
            - All fields with schema_id == <schema_id> are removed from the registry.
        """

        if schema_id not in self.schemas:
            return { "success": False, "error": "Schema does not exist." }

        # Remove the schema
        del self.schemas[schema_id]

        # Find all fields to delete (by matching schema_id)
        fields_to_remove = [field_id for field_id, field in self.fields.items() if field["schema_id"] == schema_id]
        for field_id in fields_to_remove:
            del self.fields[field_id]

        return { "success": True, "message": f"Schema {schema_id} deleted with its fields." }

    def add_field_to_schema(
        self,
        field_id: str,
        schema_id: str,
        field_name: str,
        field_type: str,
        a: str,
    ) -> dict:
        """
        Add a new field to a given schema. Enforces that the field_name is unique within the schema,
        the schema exists, and the field_id is globally unique.

        Args:
            field_id (str): Unique identifier for the new field.
            schema_id (str): Existing schema's ID to which the field will be added.
            field_name (str): Name of the new field (must be unique within the schema).
            field_type (str): Type of the field.
            a (str): Extra attribute for the field.

        Returns:
            dict:
                - On success: { "success": True, "message": "Field added to schema." }
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - Field names must be unique within a schema.
            - field_id must be globally unique.
            - schema_id must exist.
        """
        # Check schema existence
        if schema_id not in self.schemas:
            return { "success": False, "error": "Schema does not exist." }

        # Check for globally unique field_id
        if field_id in self.fields:
            return { "success": False, "error": "Field ID already exists." }

        # Check for field_name uniqueness within the schema
        for field in self.fields.values():
            if field["schema_id"] == schema_id and field["field_name"] == field_name:
                return { "success": False, "error": "Field name already exists in this schema." }

        # Add the field
        self.fields[field_id] = {
            "field_id": field_id,
            "schema_id": schema_id,
            "field_name": field_name,
            "field_type": field_type,
            "a": a
        }
        return { "success": True, "message": "Field added to schema." }

    def update_field(
        self,
        field_id: str,
        field_name: str = None,
        field_type: str = None,
        a: str = None
    ) -> dict:
        """
        Modify field attributes (e.g., name, type, metadata) for a given field_id,
        enforcing per-schema field name uniqueness.

        Args:
            field_id (str): The unique identifier of the field to update.
            field_name (str, optional): New name for the field (must be unique in its schema).
            field_type (str, optional): New type for the field.
            a (str, optional): New metadata or auxiliary value for the field.

        Returns:
            dict: {
                "success": True,
                "message": "Field <field_id> updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - If field_name is updated, it must be unique for the schema.
            - field_id must exist.
        """
        if field_id not in self.fields:
            return {"success": False, "error": f"Field {field_id} does not exist."}

        field = self.fields[field_id]
        schema_id = field["schema_id"]

        # Check for uniqueness if field_name is to be changed
        if field_name is not None:
            # Look for name conflict in the same schema
            for f in self.fields.values():
                if (
                    f["schema_id"] == schema_id
                    and f["field_name"] == field_name
                    and f["field_id"] != field_id
                ):
                    return {
                        "success": False,
                        "error": f"Field name '{field_name}' already exists in schema {schema_id}."
                    }
            field["field_name"] = field_name

        if field_type is not None:
            field["field_type"] = field_type

        if a is not None:
            field["a"] = a

        # Save the changes back (redundant due to mutability, but explicit)
        self.fields[field_id] = field

        return {
            "success": True,
            "message": f"Field {field_id} updated."
        }

    def delete_field(self, field_id: str) -> dict:
        """
        Remove (delete) the field with the specified field_id from the registry.

        Args:
            field_id (str): The unique identifier for the field to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Field deleted successfully."
            }
            OR
            {
                "success": False,
                "error": "Field not found."
            }

        Constraints:
            - field_id must exist in the field registry (self.fields).
        """
        if field_id not in self.fields:
            return { "success": False, "error": "Field not found." }

        del self.fields[field_id]
        return { "success": True, "message": "Field deleted successfully." }


    def create_user(self, username: str, email: str) -> dict:
        """
        Register a new user in the registry.

        Args:
            username (str): Desired username for the user. Must be unique.
            email (str): User's contact email. Should be unique.

        Returns:
            dict: 
                - On success: 
                  {"success": True, "message": "User created successfully", "user_id": <user_id>}
                - On failure: 
                  {"success": False, "error": <reason>}
        Constraints:
            - Username must be unique across users.
            - Email must be unique across users.
            - _id is generated as a new unique identifier.
            - created_a captured as timestamp at user creation.
        """
        # Basic input validation
        if not username or not isinstance(username, str):
            return {"success": False, "error": "Username is required and must be a string"}
        if not email or not isinstance(email, str):
            return {"success": False, "error": "Email is required and must be a string"}
    
        # Check for unique username and email
        for user in self.users.values():
            if user["username"] == username:
                return {"success": False, "error": "Username already exists"}
            if user["email"] == email:
                return {"success": False, "error": "Email already exists"}

        user_id = str(uuid.uuid4())
        created_a = datetime.utcnow().isoformat()

        user_info = {
            "_id": user_id,
            "username": username,
            "email": email,
            "created_a": created_a
        }
        self.users[user_id] = user_info
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id
        }

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user from the registry system by user_id.

        Args:
            user_id (str): Unique identifier of the user to delete.

        Returns:
            dict: {
                "success": True,
                "message": str   # Confirmation message of deletion,
            }
            or
            {
                "success": False,
                "error": str     # Reason for failure, e.g. user does not exist
            }

        Constraints:
            - If the user does not exist, fail gracefully.
            - Deletion does not cascade to schemas or fields; those objects remain,
              but their creator_user_id will now point to a non-existent user.
        """
        if user_id not in self.users:
            return { "success": False, "error": f"User {user_id} does not exist" }

        del self.users[user_id]

        return {
            "success": True,
            "message": f"User {user_id} deleted (schemas created by this user may now have invalid ownership)."
        }


    def increment_schema_version(self, schema_id: str) -> dict:
        """
        Create a new version of an existing schema, ensuring (name, version) uniqueness.

        Args:
            schema_id (str): The ID of the schema whose version is to be incremented.

        Returns:
            dict: 
              - On success:
                  {
                    "success": True,
                    "message": "New schema version created.",
                    "data": SchemaInfo  # Newly created schema info
                  }
              - On error:
                  {
                    "success": False,
                    "error": str  # Reason, e.g. schema not found or version conflict
                  }

        Constraints:
            - Schema with the provided schema_id must exist.
            - Resulting (name, version) combination cannot already exist.
            - New schema_id must be unique.
            - Metadata is copied from the original schema.
        """

        orig_schema = self.schemas.get(schema_id)
        if not orig_schema:
            return { "success": False, "error": "Schema not found" }

        schema_name = orig_schema["name"]
        # Find all schemas with this name, get their versions
        versions = [
            s["version"]
            for s in self.schemas.values()
            if s["name"] == schema_name
        ]
        if not versions:
            # Shouldn't be possible, since we just found the original
            return { "success": False, "error": "Internal error determining schema versions" }

        new_version = max(versions) + 1

        # Double-check that no schema with same name and the new_version exists
        for s in self.schemas.values():
            if s["name"] == schema_name and s["version"] == new_version:
                return { "success": False, "error": "Schema with same name and version already exists" }

        # Generate unique schema_id
        while True:
            new_schema_id = str(uuid.uuid4())
            if new_schema_id not in self.schemas:
                break

        # Timestamp for created_a
        created_a = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        # Compose new SchemaInfo
        new_schema_info = {
            "schema_id": new_schema_id,
            "name": schema_name,
            "creator_user_id": orig_schema["creator_user_id"],
            "version": new_version,
            "metadata": dict(orig_schema["metadata"]),  # deep copy
            "created_a": created_a
        }

        self.schemas[new_schema_id] = new_schema_info

        # Clone the original schema's fields into the new version so versioning
        # preserves structure instead of creating an empty schema shell.
        orig_fields = [
            field_info
            for field_info in self.fields.values()
            if field_info["schema_id"] == schema_id
        ]
        for field_info in orig_fields:
            new_field_id = f"{new_schema_id}:{field_info['field_name']}"
            self.fields[new_field_id] = {
                "field_id": new_field_id,
                "schema_id": new_schema_id,
                "field_name": field_info["field_name"],
                "field_type": field_info["field_type"],
                "a": field_info["a"],
            }

        return {
            "success": True,
            "message": f"New schema version created: name={schema_name}, version={new_version}, schema_id={new_schema_id}",
            "data": new_schema_info
        }


class SchemaRegistrySystem(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_schemas_by_creator(self, **kwargs):
        return self._call_inner_tool('list_schemas_by_creator', kwargs)

    def get_schema_by_id(self, **kwargs):
        return self._call_inner_tool('get_schema_by_id', kwargs)

    def list_fields_by_schema_id(self, **kwargs):
        return self._call_inner_tool('list_fields_by_schema_id', kwargs)

    def get_field_by_id(self, **kwargs):
        return self._call_inner_tool('get_field_by_id', kwargs)

    def list_schema_versions_by_name(self, **kwargs):
        return self._call_inner_tool('list_schema_versions_by_name', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def create_schema(self, **kwargs):
        return self._call_inner_tool('create_schema', kwargs)

    def update_schema_metadata(self, **kwargs):
        return self._call_inner_tool('update_schema_metadata', kwargs)

    def delete_schema(self, **kwargs):
        return self._call_inner_tool('delete_schema', kwargs)

    def add_field_to_schema(self, **kwargs):
        return self._call_inner_tool('add_field_to_schema', kwargs)

    def update_field(self, **kwargs):
        return self._call_inner_tool('update_field', kwargs)

    def delete_field(self, **kwargs):
        return self._call_inner_tool('delete_field', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

    def increment_schema_version(self, **kwargs):
        return self._call_inner_tool('increment_schema_version', kwargs)
