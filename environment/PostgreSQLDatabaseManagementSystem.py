# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class DatabaseInfo(TypedDict):
    database_id: str
    database_name: str
    owner: str
    creation_date: str  # Could be datetime, using str for simplicity

class SchemaInfo(TypedDict):
    schema_id: str
    schema_name: str
    owner: str
    creation_date: str  # Could be datetime, using str for simplicity
    parent_database_id: str

class ObjectInfo(TypedDict):
    object_id: str
    object_name: str
    object_type: str
    schema_id: str
    definition: str
    dependencies: List[str]  # List of object_id's this object depends on

class UserInfo(TypedDict):
    user_id: str
    username: str
    roles: List[str]
    privileges: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        PostgreSQL database management system environment.
        """

        # Databases: {database_id: DatabaseInfo}
        self.databases: Dict[str, DatabaseInfo] = {}

        # Schemas: {schema_id: SchemaInfo}
        self.schemas: Dict[str, SchemaInfo] = {}

        # Objects: {object_id: ObjectInfo}
        self.objects: Dict[str, ObjectInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints (see rules):
        # - Schemas can only be deleted if no objects (in/outside) depend on their contained objects, unless CASCADE.
        # - Only users with appropriate privileges (schema owner, superuser) may delete a schema.
        # - Deleting a schema removes all its contained objects.
        # - Schema names must be unique within a given database.
        # - The database must exist and be accessible for operations.

    def _resolve_user_identifier(self, user_identifier: str):
        user = self.users.get(user_identifier)
        if user:
            return user_identifier, user
        for stored_user_id, user_info in self.users.items():
            if user_info.get("username") == user_identifier:
                return stored_user_id, user_info
        return None, None

    def _is_schema_owner(self, resolved_user_id: str, user_info: dict, schema_info: dict) -> bool:
        owner = schema_info.get("owner")
        return owner in {
            resolved_user_id,
            user_info.get("user_id"),
            user_info.get("username"),
        }

    def _has_schema_management_privilege(
        self,
        resolved_user_id: str,
        user_info: dict,
        schema_info: dict,
    ) -> bool:
        if self._is_schema_owner(resolved_user_id, user_info, schema_info):
            return True
        return "superuser" in user_info.get("roles", []) or "superuser" in user_info.get("privileges", [])

    def _schema_privilege_matches(self, privilege: str, schema_info: dict) -> bool:
        schema_id = schema_info["schema_id"]
        schema_name = schema_info["schema_name"]
        normalized_candidates = {schema_id, schema_name}

        if privilege in normalized_candidates:
            return True

        for candidate in normalized_candidates:
            if privilege.startswith(f"{candidate}_") or privilege.startswith(f"{candidate}:"):
                return True
            if privilege.startswith(f"schema:{candidate}:"):
                return True

        return False

    def get_database_by_name(self, database_name: str) -> dict:
        """
        Retrieve information about a database by its name.

        Args:
            database_name (str): The name of the database to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": DatabaseInfo  # Info dictionary for the database
            }
            or
            {
                "success": False,
                "error": str  # "Database not found"
            }

        Constraints:
            - Database names are unique.
            - The database must exist.
        """
        for db_info in self.databases.values():
            if db_info["database_name"] == database_name:
                return {"success": True, "data": db_info}
        return {"success": False, "error": "Database not found"}

    def get_database_by_id(self, database_id: str) -> dict:
        """
        Retrieve database info by its unique id.

        Args:
            database_id (str): The unique identifier of the database.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": DatabaseInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Database ID not found"
                    }
        """
        db_info = self.databases.get(database_id)
        if db_info is None:
            return {
                "success": False,
                "error": "Database ID not found"
            }
        return {
            "success": True,
            "data": db_info
        }

    def check_database_exists(self, database_id: str = None, database_name: str = None) -> dict:
        """
        Check if a database (by name or id) exists and is accessible.

        Args:
            database_id (str, optional): The database's unique id.
            database_name (str, optional): The database's name.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "database_id": str,
                            "database_name": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - At least one of database_id or database_name must be specified.
            - If both are specified, they must refer to the same database.
            - Only considers in-memory 'accessible' databases (those present in self.databases).
        """
        if not database_id and not database_name:
            return { "success": False, "error": "At least one of database_id or database_name must be provided" }

        # Try by ID first if provided
        if database_id:
            db_info = self.databases.get(database_id)
            if not db_info:
                return { "success": False, "error": "Database does not exist" }
            if database_name and db_info["database_name"] != database_name:
                return { "success": False, "error": "database_id and database_name do not match" }
            # Found by id
            return {
                "success": True,
                "data": {
                    "database_id": db_info["database_id"],
                    "database_name": db_info["database_name"]
                }
            }

        # Fallback: Try by name
        for db in self.databases.values():
            if db["database_name"] == database_name:
                return {
                    "success": True,
                    "data": {
                        "database_id": db["database_id"],
                        "database_name": db["database_name"]
                    }
                }

        return { "success": False, "error": "Database does not exist" }

    def list_schemas_in_database(self, database_id: str) -> dict:
        """
        List all schemas contained within the specified database.

        Args:
            database_id (str): The unique ID of the database.

        Returns:
            dict: {
                "success": True,
                "data": List[SchemaInfo],  # All schemas within the database, empty list if none
            }
            or
            {
                "success": False,
                "error": str  # If the database does not exist
            }

        Constraints:
            - The database with database_id must exist.
        """
        if database_id not in self.databases:
            return { "success": False, "error": "Database does not exist" }

        schemas = [
            schema for schema in self.schemas.values()
            if schema["parent_database_id"] == database_id
        ]
        return { "success": True, "data": schemas }

    def get_schema_by_name(self, database_name: str, schema_name: str) -> dict:
        """
        Retrieve schema information by name within the specified database.

        Args:
            database_name (str): Name of the database containing the schema.
            schema_name (str): Name of the schema to retrieve.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": SchemaInfo
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - The database must exist by the given name.
            - The schema name must exist and be unique within that database.
        """
        # Find the database_id for the given database_name
        matching_db_id = None
        for db_id, db_info in self.databases.items():
            if db_info["database_name"] == database_name:
                matching_db_id = db_id
                break

        if not matching_db_id:
            return { "success": False, "error": "Database does not exist" }

        # Search for schema with the given name and matching parent_database_id
        for schema in self.schemas.values():
            if schema["schema_name"] == schema_name and schema["parent_database_id"] == matching_db_id:
                return { "success": True, "data": schema }
    
        return { "success": False, "error": "Schema not found in specified database" }

    def get_schema_by_id(self, schema_id: str) -> dict:
        """
        Retrieve schema metadata by its unique schema_id.

        Args:
            schema_id (str): The unique identifier of the schema to query.

        Returns:
            dict:
                - { "success": True, "data": SchemaInfo } if found.
                - { "success": False, "error": "Schema not found" } if not present.
        
        Constraints:
            - No privilege or dependency checks; this is purely informational.
            - schema_id must be present in self.schemas.
        """
        if schema_id not in self.schemas:
            return {"success": False, "error": "Schema not found"}
        return {"success": True, "data": self.schemas[schema_id]}

    def get_schema_objects(self, schema_id: str) -> dict:
        """
        List all objects (tables, views, etc.) contained in a schema.

        Args:
            schema_id (str): The ID of the schema whose objects are to be listed.

        Returns:
            dict:
                - Success: { "success": True, "data": List[ObjectInfo] }
                - Failure: { "success": False, "error": "Schema does not exist" }

        Constraints:
            - The provided schema_id must exist in self.schemas.
        """
        if schema_id not in self.schemas:
            return { "success": False, "error": "Schema does not exist" }

        result = [
            obj_info
            for obj_info in self.objects.values()
            if obj_info["schema_id"] == schema_id
        ]

        return { "success": True, "data": result }

    def get_object_dependencies(self, object_ids: list[str]) -> dict:
        """
        For a given object or set of object IDs, list all other objects (including outside the schema) that depend on them.

        Args:
            object_ids (List[str]): List of object_id(s) to check for dependencies.

        Returns:
            dict: {
                "success": True,
                "data": {
                    <object_id>: [ObjectInfo, ...],  # Objects that depend on given object_id
                    ...
                }
            }
            If no such object is found for an object_id, the value is an empty list.

            Example:
                {
                    "success": True,
                    "data": {
                        "obj1": [<ObjectInfo1>, <ObjectInfo2>], 
                        "obj2": []
                    }
                }
        Constraints:
            - No permissions or existence requirements (missing object_ids return empty dependent lists).
        """
        # Collect results per input object_id
        result: dict = {}
        for object_id in object_ids:
            dependents = [
                obj for obj in self.objects.values() if object_id in obj.get("dependencies", [])
            ]
            result[object_id] = dependents

        return {"success": True, "data": result}

    def check_user_privileges_on_schema(self, user_id: str, schema_id: str) -> dict:
        """
        Check whether a specific user has the privilege (schema owner or superuser) 
        to delete a given schema.

        Args:
            user_id (str): The user ID to check.
            schema_id (str): The schema ID to check privileges for.

        Returns:
            dict: {
                "success": True,
                "has_privilege": bool
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only the schema owner or a user with "superuser" privileges may delete the schema.
            - Both user and schema must exist.
        """
        # Check if schema exists
        schema = self.schemas.get(schema_id)
        if not schema:
            return {"success": False, "error": "Schema does not exist"}

        # Check if user exists
        resolved_user_id, user = self._resolve_user_identifier(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        return {
            "success": True,
            "has_privilege": self._has_schema_management_privilege(resolved_user_id, user, schema),
        }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information by username.

        Args:
            username (str): The username to look up.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": UserInfo    # User's full information.
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str        # "User not found"
                    }

        Constraints:
            - Username is assumed to be unique.
            - Returns error if user does not exist.
        """
        for user_info in self.users.values():
            if user_info["username"] == username:
                return { "success": True, "data": user_info }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # Full info dict for the user
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. if user is not found
            }

        Constraints:
            - The user_id must exist in the environment's users.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def delete_schema(
        self, 
        schema_id: str, 
        user_id: str
    ) -> dict:
        """
        Delete a schema if no dependent objects outside the schema exist.
        All objects contained in the schema are also deleted.

        Args:
            schema_id (str): The unique identifier of the schema to be deleted.
            user_id (str): The ID of the user requesting this operation.

        Returns:
            dict:
                success: True and a message if deletion was successful.
                success: False and an error message otherwise.

        Constraints:
            - The database and schema must exist.
            - Only the schema owner or a user with 'superuser' role may delete the schema.
            - The schema can be deleted ONLY if no objects outside the schema have dependencies on its contained objects.
            - All objects within the schema are deleted.
        """
        # Check if the schema exists
        schema_info = self.schemas.get(schema_id)
        if not schema_info:
            return {"success": False, "error": "Schema does not exist"}

        # Check if the parent database exists
        parent_db_id = schema_info['parent_database_id']
        if parent_db_id not in self.databases:
            return {"success": False, "error": "Parent database does not exist or inaccessible"}

        # Check if the user exists
        resolved_user_id, user_info = self._resolve_user_identifier(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}

        # Check user privileges: must be schema owner or superuser
        if not self._has_schema_management_privilege(resolved_user_id, user_info, schema_info):
            return {"success": False, "error": "Permission denied: only the schema owner or superuser can delete schema"}

        # Collect all objects within the schema
        schema_object_ids = [
            obj_id for obj_id, obj_info in self.objects.items()
            if obj_info['schema_id'] == schema_id
        ]
        # Check for external dependencies
        for obj_id, obj_info in self.objects.items():
            # Only examine objects outside the schema
            if obj_info['schema_id'] != schema_id:
                # If this object depends on any object in our set, that's a violation
                for dep_id in obj_info.get('dependencies', []):
                    if dep_id in schema_object_ids:
                        return {
                            "success": False,
                            "error": (
                                "Cannot delete schema: "
                                "external object '{}' depends on schema object '{}'".format(obj_info['object_name'], dep_id)
                            )
                        }

        # Delete all objects in the schema
        for obj_id in schema_object_ids:
            del self.objects[obj_id]

        # Remove the schema itself
        schema_name = schema_info['schema_name']
        del self.schemas[schema_id]

        return {
            "success": True,
            "message": f"Schema '{schema_name}' and all its contained objects were deleted successfully."
        }

    def delete_schema_with_cascade(self, schema_id: str, user_id: str) -> dict:
        """
        Force-delete a schema and all its contained objects, ignoring their dependencies (CASCADE behavior).

        Args:
            schema_id (str): ID of the schema to delete.
            user_id (str): ID of the user requesting the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Schema and all contained objects deleted (CASCADE)."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The schema and parent database must exist.
            - Only the schema owner or a user with the 'superuser' role may delete the schema.
            - All objects in the schema are deleted, regardless of dependencies.
        """

        # Schema existence check
        schema = self.schemas.get(schema_id)
        if not schema:
            return {"success": False, "error": "Schema does not exist."}

        db_id = schema["parent_database_id"]
        db = self.databases.get(db_id)
        if not db:
            return {"success": False, "error": "Parent database does not exist."}

        # User existence and privilege check
        resolved_user_id, user = self._resolve_user_identifier(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        if not self._has_schema_management_privilege(resolved_user_id, user, schema):
            return {"success": False, "error": "Insufficient privileges to delete this schema."}

        # CASCADE semantics: delete contained objects and any external objects that depend on them.
        objects_to_delete = {
            oid for oid, obj in self.objects.items() if obj["schema_id"] == schema_id
        }
        changed = True
        while changed:
            changed = False
            for oid, obj in self.objects.items():
                if oid in objects_to_delete:
                    continue
                if any(dep_id in objects_to_delete for dep_id in obj.get("dependencies", [])):
                    objects_to_delete.add(oid)
                    changed = True

        for oid in objects_to_delete:
            if oid in self.objects:
                del self.objects[oid]

        # Delete the schema itself
        del self.schemas[schema_id]

        return {"success": True, "message": "Schema and all contained objects deleted (CASCADE)." }

    def clear_schema_contents(self, schema_id: str, user_id: str) -> dict:
        """
        Remove every object contained in a schema while keeping the schema itself in place.
        External dependent objects are preserved; any dependency references they hold to
        deleted schema objects are detached as part of the operation.

        Args:
            schema_id (str): ID of the schema whose contents should be cleared.
            user_id (str): ID or username of the user requesting the operation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": str,
                        "details": {
                            "objects_removed": int,
                            "external_objects_detached": int
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The schema and parent database must exist.
            - Only the schema owner or a user with the 'superuser' role may clear it.
            - The schema itself is preserved.
            - External objects are not deleted; dependency references to removed schema objects
              are detached so the schema can be emptied safely in this simplified environment.
        """
        schema = self.schemas.get(schema_id)
        if not schema:
            return {"success": False, "error": "Schema does not exist."}

        db_id = schema["parent_database_id"]
        if db_id not in self.databases:
            return {"success": False, "error": "Parent database does not exist."}

        resolved_user_id, user = self._resolve_user_identifier(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        if not self._has_schema_management_privilege(resolved_user_id, user, schema):
            return {"success": False, "error": "Insufficient privileges to clear this schema."}

        schema_object_ids = {
            object_id
            for object_id, object_info in self.objects.items()
            if object_info["schema_id"] == schema_id
        }
        if not schema_object_ids:
            return {
                "success": True,
                "message": f"Schema '{schema['schema_name']}' is already empty.",
                "details": {"objects_removed": 0, "external_objects_detached": 0},
            }

        external_objects_detached = 0
        for object_info in self.objects.values():
            if object_info["schema_id"] == schema_id:
                continue
            original_dependencies = list(object_info.get("dependencies", []))
            pruned_dependencies = [
                dependency_id
                for dependency_id in original_dependencies
                if dependency_id not in schema_object_ids
            ]
            if pruned_dependencies != original_dependencies:
                object_info["dependencies"] = pruned_dependencies
                external_objects_detached += 1

        for object_id in list(schema_object_ids):
            if object_id in self.objects:
                del self.objects[object_id]

        return {
            "success": True,
            "message": (
                f"Cleared {len(schema_object_ids)} object(s) from schema "
                f"'{schema['schema_name']}' while preserving the schema."
            ),
            "details": {
                "objects_removed": len(schema_object_ids),
                "external_objects_detached": external_objects_detached,
            },
        }

    def remove_object(self, object_id: str) -> dict:
        """
        Delete a specific object (table, view, etc.) from a schema.

        Args:
            object_id (str): The unique identifier of the object to delete.

        Returns:
            dict: 
                { "success": True, "message": "Object <object_name> deleted from schema <schema_name>." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - The object must exist.
            - No other object may depend on this object (i.e., this object's ID is not in any ObjectInfo.dependencies).
            - If some object depends on this object, deletion is not permitted.
        """
        obj = self.objects.get(object_id)
        if obj is None:
            return {"success": False, "error": "Object does not exist."}

        # Check if any other object depends on this object
        for other_obj in self.objects.values():
            if object_id in other_obj.get("dependencies", []):
                return {
                    "success": False,
                    "error": f"Cannot delete object '{obj['object_name']}' because other objects depend on it."
                }

        # Save needed info for message before deletion
        object_name = obj["object_name"]
        schema_id = obj["schema_id"]
        schema = self.schemas.get(schema_id)
        schema_name = schema["schema_name"] if schema else "<unknown schema>"

        # Perform the deletion
        del self.objects[object_id]

        return {
            "success": True,
            "message": f"Object '{object_name}' deleted from schema '{schema_name}'."
        }

    def revoke_schema_privileges_from_user(self, schema_id: str, user_id: str) -> dict:
        """
        Revoke all of a user's privileges on a specific schema.

        Args:
            schema_id (str): The ID of the schema whose privileges are to be revoked.
            user_id (str): The ID of the user from whom to revoke privileges.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Revoked N privileges from user <username> on schema <schema_name>."
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
        - The schema and user must exist.
        - Only privileges referring to this schema will be removed from the user.
        - If there are no privileges to revoke, this is still considered success.
        """
        # Check schema exists
        if schema_id not in self.schemas:
            return { "success": False, "error": "Schema does not exist" }
        # Check user exists
        resolved_user_id, resolved_user = self._resolve_user_identifier(user_id)
        if not resolved_user:
            return { "success": False, "error": "User does not exist" }

        username = resolved_user["username"]
        schema_name = self.schemas[schema_id]["schema_name"]

        original_privileges = resolved_user.get("privileges", [])
        schema_info = self.schemas[schema_id]
        # Privileges are assumed to be in the form "schema:<schema_id>:<privilege>"
        remaining_privileges = []
        revoked = []
        for priv in original_privileges:
            if self._schema_privilege_matches(priv, schema_info):
                revoked.append(priv)
            else:
                remaining_privileges.append(priv)
        self.users[resolved_user_id]["privileges"] = remaining_privileges

        return {
            "success": True,
            "message": f"Revoked {len(revoked)} privilege(s) from user {username} on schema {schema_name}."
        }

    def cleanup_orphaned_dependencies(self) -> dict:
        """
        Remove/correct dependency references from objects that depended on deleted objects.
        For each object, remove from its dependencies any object_id that no longer exists in self.objects.

        Returns:
            dict: {
                "success": True,
                "message": "Orphaned dependencies cleaned up from N objects."
            }

        Constraints:
            - This operation is idempotent and non-failing.
            - Only dependencies on missing (deleted) objects are removed.
            - No additional privilege checks are needed.
        """
        existing_object_ids = set(self.objects.keys())
        updated_count = 0
        for obj in self.objects.values():
            orig_dependencies = set(obj.get("dependencies", []))
            pruned_dependencies = [dep_id for dep_id in orig_dependencies if dep_id in existing_object_ids]
            if pruned_dependencies != obj.get("dependencies", []):
                obj["dependencies"] = pruned_dependencies
                updated_count += 1
        return {
            "success": True,
            "message": f"Orphaned dependencies cleaned up from {updated_count} objects."
        }


class PostgreSQLDatabaseManagementSystem(BaseEnv):
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

    def get_database_by_name(self, **kwargs):
        return self._call_inner_tool('get_database_by_name', kwargs)

    def get_database_by_id(self, **kwargs):
        return self._call_inner_tool('get_database_by_id', kwargs)

    def check_database_exists(self, **kwargs):
        return self._call_inner_tool('check_database_exists', kwargs)

    def list_schemas_in_database(self, **kwargs):
        return self._call_inner_tool('list_schemas_in_database', kwargs)

    def get_schema_by_name(self, **kwargs):
        return self._call_inner_tool('get_schema_by_name', kwargs)

    def get_schema_by_id(self, **kwargs):
        return self._call_inner_tool('get_schema_by_id', kwargs)

    def get_schema_objects(self, **kwargs):
        return self._call_inner_tool('get_schema_objects', kwargs)

    def get_object_dependencies(self, **kwargs):
        return self._call_inner_tool('get_object_dependencies', kwargs)

    def check_user_privileges_on_schema(self, **kwargs):
        return self._call_inner_tool('check_user_privileges_on_schema', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def delete_schema(self, **kwargs):
        return self._call_inner_tool('delete_schema', kwargs)

    def delete_schema_with_cascade(self, **kwargs):
        return self._call_inner_tool('delete_schema_with_cascade', kwargs)

    def clear_schema_contents(self, **kwargs):
        return self._call_inner_tool('clear_schema_contents', kwargs)

    def remove_object(self, **kwargs):
        return self._call_inner_tool('remove_object', kwargs)

    def revoke_schema_privileges_from_user(self, **kwargs):
        return self._call_inner_tool('revoke_schema_privileges_from_user', kwargs)

    def cleanup_orphaned_dependencies(self, **kwargs):
        return self._call_inner_tool('cleanup_orphaned_dependencies', kwargs)
