# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from typing import Optional, Dict



class TokenInfo(TypedDict):
    token_id: str
    user_id: str  # or service_id
    issued_at: float  # timestamp
    expires_at: float  # timestamp
    status: str  # active, expired, revoked

class EntityInfo(TypedDict):
    entity_id: str  # user_id or service_id
    name: str
    account_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Authentication token management system environment.
        """

        # Tokens: {token_id: TokenInfo}
        # Represents authentication tokens with issuance, expiration, status, and association.
        self.tokens: Dict[str, TokenInfo] = {}

        # Entities: {entity_id: EntityInfo}
        # Represents users or services associated with tokens.
        self.entities: Dict[str, EntityInfo] = {}

        # Constraints:
        # - A token is expired if current time > expires_at.
        # - A token is invalid if its status is "revoked" (regardless of expiration).
        # - Only tokens unexpired and not revoked are valid for authentication.
        # - Each token_id must be unique in the system.

    def _current_time(self) -> float:
        try:
            return float(getattr(self, "current_time", 1700000000.0))
        except (TypeError, ValueError):
            return 1700000000.0

    def get_token_by_id(self, token_id: str) -> dict:
        """
        Retrieve all metadata for a specific token given its token_id.

        Args:
            token_id (str): The unique identifier for the token.

        Returns:
            dict: {
                "success": True,
                "data": TokenInfo,  # token metadata if found
            }
            or
            {
                "success": False,
                "error": str  # "Token not found"
            }

        Constraints:
            - token_id must exist in the system.
        """
        token = self.tokens.get(token_id)
        if token is not None:
            return {"success": True, "data": token}
        else:
            return {"success": False, "error": "Token not found"}

    def list_tokens_for_entity(self, entity_id: str) -> dict:
        """
        List all token objects associated with a particular user or service (by entity_id).

        Args:
            entity_id (str): The user_id or service_id to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[TokenInfo]  # All tokens issued to this entity (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., 'Entity does not exist')
            }

        Constraints:
        - The entity_id must exist in the system.
        - Only tokens with user_id == entity_id will be returned.
        """

        if entity_id not in self.entities:
            return { "success": False, "error": "Entity does not exist" }

        result = [
            token for token in self.tokens.values()
            if token["user_id"] == entity_id
        ]
        return { "success": True, "data": result }


    def check_token_expiration(self, token_id: str) -> dict:
        """
        Check if the specified token is expired.

        Args:
            token_id (str): The unique identifier of the token.

        Returns:
            dict: 
            {
                "success": True,
                "expired": bool,   # True if expired, False otherwise
                "expires_at": float  # The expiration timestamp of the token
            }
            or
            {
                "success": False,
                "error": str  # Error description if token_id is invalid
            }
    
        Constraints:
            - Token must exist in the system.
            - A token is considered expired if the current time is greater than its `expires_at`.
        """
        token_info = self.tokens.get(token_id)
        if token_info is None:
            return { "success": False, "error": "Token does not exist" }
    
        current_time = self._current_time()
        expired = (current_time > token_info["expires_at"])
        return {
            "success": True,
            "expired": expired,
            "expires_at": token_info["expires_at"]
        }

    def check_token_revoked(self, token_id: str) -> dict:
        """
        Check if a given token (by token_id) is currently revoked, based on its status.

        Args:
            token_id (str): The unique identifier of the token to check.

        Returns:
            dict:
                - If token exists:
                    { "success": True, "data": True }   # if token is revoked
                    { "success": True, "data": False }  # if token is not revoked
                - If token does not exist:
                    { "success": False, "error": "Token not found" }

        Constraints:
            - Each token_id must be unique in the system.
            - Only token.status == "revoked" means revoked.
        """
        token = self.tokens.get(token_id)
        if token is None:
            return {"success": False, "error": "Token not found"}
        return {"success": True, "data": token["status"] == "revoked"}


    def check_token_validity(self, token_id: str) -> dict:
        """
        Check if a token is currently valid for authentication.
        A token is valid iff:
          - It exists in the system.
          - Its status is not "revoked".
          - The current time is not past its expires_at.

        Args:
            token_id (str): The unique identifier of the token.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if valid, else False
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        token = self.tokens.get(token_id)
        if not token:
            return { "success": False, "error": "Token not found" }
    
        if token["status"] == "revoked":
            return { "success": True, "data": False }
    
        current_time = self._current_time()
        if current_time > token["expires_at"]:
            return { "success": True, "data": False }
    
        return { "success": True, "data": True }

    def list_all_tokens(self) -> dict:
        """
        Retrieve all tokens currently present in the management system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TokenInfo],  # All tokens in the system (may be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.tokens.values())
        }

    def list_tokens_by_status(self, status: str) -> dict:
        """
        Retrieve all tokens in the system with the specified status.

        Args:
            status (str): The status to filter by. Must be "active", "expired", or "revoked".

        Returns:
            dict: {
                "success": True,
                "data": List[TokenInfo]  # All tokens with the desired status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Invalid status provided"
            }

        Constraints:
            - Only "active", "expired" or "revoked" are valid status values.
        """
        allowed_statuses = {"active", "expired", "revoked"}
        if status not in allowed_statuses:
            return { "success": False, "error": "Invalid status provided" }
        result = [
            token_info
            for token_info in self.tokens.values()
            if token_info["status"] == status
        ]
        return { "success": True, "data": result }

    def get_entity_by_id(self, entity_id: str) -> dict:
        """
        Retrieve information about a user or service by entity_id.

        Args:
            entity_id (str): Unique identifier of the user or service.

        Returns:
            dict: 
                If found: {
                    "success": True,
                    "data": EntityInfo
                }
                If not found: {
                    "success": False,
                    "error": "Entity not found"
                }

        Constraints:
            - The entity_id must exist in the entities database.
        """
        entity = self.entities.get(entity_id)
        if entity is None:
            return {
                "success": False,
                "error": "Entity not found"
            }
        return {
            "success": True,
            "data": entity
        }

    def list_all_entities(self) -> dict:
        """
        List all users and services (entities) registered with the token management system.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[EntityInfo],  # List may be empty if no entities are registered
                }
        Constraints:
            - Returns all entities present in the system.
            - Always succeeds (returns empty list if there are no entities).
        """
        entities_list = list(self.entities.values())
        return {
            "success": True,
            "data": entities_list
        }


    def issue_token(
        self,
        entity_id: str,
        expires_at: float,
        token_id: Optional[str] = None
    ) -> dict:
        """
        Create and register a new authentication token for a user or service, specifying validity period.

        Args:
            entity_id (str): The user_id or service_id the token is associated with. Must exist in entities.
            expires_at (float): Unix timestamp when the token will expire. Must be greater than current time.
            token_id (Optional[str]): Optionally specify the token_id (must be unique). If not given, generates a new unique token_id.

        Returns:
            dict: {
                "success": True,
                "message": "Token issued",
                "token_id": <token_id>,
                "data": <TokenInfo>
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The entity (user or service) must exist.
            - expires_at must be after current time.
            - token_id must be unique.
        """
        # Check that entity exists
        if entity_id not in self.entities:
            return {"success": False, "error": "Entity not found"}

        issued_at = self._current_time()
        if expires_at <= issued_at:
            return {"success": False, "error": "Expiration time must be in the future"}

        # Generate unique token_id if not provided
        if token_id is not None:
            if token_id in self.tokens:
                return {"success": False, "error": "Token ID already exists"}
        else:
            # Use uuid4 hex, retry if somehow collision (extremely unlikely)
            for _ in range(3):
                gen_token_id = uuid.uuid4().hex
                if gen_token_id not in self.tokens:
                    token_id = gen_token_id
                    break
            else:
                return {"success": False, "error": "Failed to generate unique token_id"}

        # Register token
        token_info: Dict = {
            "token_id": token_id,
            "user_id": entity_id,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "status": "active"
        }
        self.tokens[token_id] = token_info

        return {
            "success": True,
            "message": "Token issued",
            "token_id": token_id,
            "data": token_info
        }

    def revoke_token(self, token_id: str) -> dict:
        """
        Change the status of the token with the given token_id to "revoked",
        immediately rendering it invalid for authentication.

        Args:
            token_id (str): The unique identifier of the token to revoke.

        Returns:
            dict: {
                "success": True,
                "message": "Token revoked successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - token_id must exist in the system.
            - If the token is already revoked, report it accordingly.
            - Status must be set to "revoked".
            - Token becomes invalid for authentication immediately.
        """
        token = self.tokens.get(token_id)
        if token is None:
            return {"success": False, "error": "Token not found."}
        if token["status"] == "revoked":
            return {"success": False, "error": "Token is already revoked."}

        token["status"] = "revoked"
        self.tokens[token_id] = token  # Ensures state is updated

        return {"success": True, "message": "Token revoked successfully."}

    def update_token_expiration(self, token_id: str, new_expires_at: float) -> dict:
        """
        Change or extend the expires_at field of a given token.

        Args:
            token_id (str): The ID of the token to update.
            new_expires_at (float): The new expiration time (Unix timestamp).

        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "message": "Expiration updated for token <token_id>"
                }
                On failure: {
                    "success": False, 
                    "error": "<reason>"
                }

        Constraints:
            - token_id must exist in self.tokens.
            - Will adjust the expires_at field.
            - If token's status is "active" or "expired", and new_expires_at > now, will set status to "active".
            - If token's status is "active" and new_expires_at <= now, will set status to "expired".
            - If token's status is "revoked", status is not changed (remains revoked).
        """

        if token_id not in self.tokens:
            return {"success": False, "error": "Token does not exist"}

        token = self.tokens[token_id]
        now = self._current_time()

        # Basic semantic check: don't allow expiration before issued_at
        if new_expires_at < token["issued_at"]:
            return {"success": False, "error": "New expiration precedes token issuance"}

        token["expires_at"] = new_expires_at

        # Adjust status if not revoked
        if token["status"] != "revoked":
            if new_expires_at > now:
                token["status"] = "active"
            else:
                token["status"] = "expired"
        # If revoked: do not change status, but update expiration

        self.tokens[token_id] = token

        return {
            "success": True,
            "message": f"Expiration updated for token {token_id}"
        }

    def delete_token(self, token_id: str) -> dict:
        """
        Completely remove a token from the system, erasing all its metadata.

        Args:
            token_id (str): The unique ID of the token to delete.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Token <token_id> deleted successfully."}
                On failure:
                    {"success": False, "error": "Token not found."}

        Constraints:
            - The token_id must exist in the system to be deleted.
            - Deletion is permanent and allowed regardless of token status.
        """
        if token_id not in self.tokens:
            return {"success": False, "error": "Token not found."}
        del self.tokens[token_id]
        return {"success": True, "message": f"Token {token_id} deleted successfully."}

    def register_entity(self, entity_id: str, name: str, account_status: str) -> dict:
        """
        Add a new entity (user or service) into the system.

        Args:
            entity_id (str): Unique identifier for the user or service.
            name (str): Name of the user or service.
            account_status (str): Status of the account (e.g., active, suspended).

        Returns:
            dict: 
              - On success: {"success": True, "message": "Entity registered successfully"}
              - On failure: {"success": False, "error": <reason>}
          
        Constraints:
            - entity_id must be unique in the system (not already registered).
        """

        if not entity_id or not name or not account_status:
            return { "success": False, "error": "All fields (entity_id, name, account_status) are required" }

        if entity_id in self.entities:
            return { "success": False, "error": "Entity with this ID already exists" }

        entity_info = {
            "entity_id": entity_id,
            "name": name,
            "account_status": account_status
        }
        self.entities[entity_id] = entity_info

        return { "success": True, "message": "Entity registered successfully" }

    def update_entity_status(self, entity_id: str, new_status: str) -> dict:
        """
        Change the account status of a user or service.

        Args:
            entity_id (str): The unique identifier for the user or service whose status should be changed.
            new_status (str): The desired status string (e.g., 'active', 'suspended').

        Returns:
            dict:
                - On success: {"success": True, "message": "Entity account status updated."}
                - On failure: {"success": False, "error": "Entity not found."}

        Constraints:
            - Fails if the entity_id is not present in the system.
            - No restriction is placed on new_status value.
        """
        if entity_id not in self.entities:
            return {"success": False, "error": "Entity not found."}

        self.entities[entity_id]["account_status"] = new_status
        return {"success": True, "message": "Entity account status updated."}

    def bulk_revoke_tokens_for_entity(self, entity_id: str) -> dict:
        """
        Marks all tokens belonging to the specified user or service as revoked.

        Args:
            entity_id (str): The ID of the user or service whose tokens should be revoked.

        Returns:
            dict: {
                "success": True,
                "message": "Number of tokens revoked for entity <entity_id>: <count>"
            }
            or
            {
                "success": False,
                "error": "Entity not found"
            }

        Constraints:
            - If the entity_id does not exist, the operation fails.
            - All tokens for this entity are marked as 'revoked', including those already revoked.
            - The operation is idempotent.
        """
        if entity_id not in self.entities:
            return { "success": False, "error": "Entity not found" }

        count = 0
        for token in self.tokens.values():
            if token['user_id'] == entity_id:
                if token['status'] != "revoked":
                    token['status'] = "revoked"
                count += 1

        return {
            "success": True,
            "message": f"Number of tokens revoked for entity {entity_id}: {count}"
        }


class AuthenticationTokenManagementSystem(BaseEnv):
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

    def get_token_by_id(self, **kwargs):
        return self._call_inner_tool('get_token_by_id', kwargs)

    def list_tokens_for_entity(self, **kwargs):
        return self._call_inner_tool('list_tokens_for_entity', kwargs)

    def check_token_expiration(self, **kwargs):
        return self._call_inner_tool('check_token_expiration', kwargs)

    def check_token_revoked(self, **kwargs):
        return self._call_inner_tool('check_token_revoked', kwargs)

    def check_token_validity(self, **kwargs):
        return self._call_inner_tool('check_token_validity', kwargs)

    def list_all_tokens(self, **kwargs):
        return self._call_inner_tool('list_all_tokens', kwargs)

    def list_tokens_by_status(self, **kwargs):
        return self._call_inner_tool('list_tokens_by_status', kwargs)

    def get_entity_by_id(self, **kwargs):
        return self._call_inner_tool('get_entity_by_id', kwargs)

    def list_all_entities(self, **kwargs):
        return self._call_inner_tool('list_all_entities', kwargs)

    def issue_token(self, **kwargs):
        return self._call_inner_tool('issue_token', kwargs)

    def revoke_token(self, **kwargs):
        return self._call_inner_tool('revoke_token', kwargs)

    def update_token_expiration(self, **kwargs):
        return self._call_inner_tool('update_token_expiration', kwargs)

    def delete_token(self, **kwargs):
        return self._call_inner_tool('delete_token', kwargs)

    def register_entity(self, **kwargs):
        return self._call_inner_tool('register_entity', kwargs)

    def update_entity_status(self, **kwargs):
        return self._call_inner_tool('update_entity_status', kwargs)

    def bulk_revoke_tokens_for_entity(self, **kwargs):
        return self._call_inner_tool('bulk_revoke_tokens_for_entity', kwargs)
