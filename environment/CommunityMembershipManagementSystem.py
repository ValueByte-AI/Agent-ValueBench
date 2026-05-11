# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any
from datetime import datetime
from typing import Dict, Any



class MemberInfo(TypedDict):
    member_id: str
    name: str
    contact_info: str
    join_date: str
    profile_metadata: Dict[str, Any]
    membership_sta: str  # Assuming this stands for "membership_status"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Community membership management environment state.
        """
        # Members: {member_id: MemberInfo}
        self.members: Dict[str, MemberInfo] = {}

        # Constraints:
        # - Each member must have a unique member_id.
        # - join_date is set at creation and should not be altered.
        # - Members should be retrievable and sortable by any attribute.
        # - Support limiting query results (paging/slicing).


    def get_member_by_id(self, member_id: str) -> dict:
        """
        Retrieve the full profile information for a specific member using their unique member_id.

        Args:
            member_id (str): The unique identifier for the member.

        Returns:
            dict: {
                "success": True,
                "data": MemberInfo    # full profile of the member
            }
            or
            {
                "success": False,
                "error": str         # Error description if not found
            }

        Constraints:
            - member_id must exist in the system.
        """
        if member_id not in self.members:
            return { "success": False, "error": "Member not found" }
        return { "success": True, "data": self.members[member_id] }

    def list_members(
        self,
        filter_by: Dict[str, Any] = None,
        sort_by: list = None,
        sort_order: str = "asc",
        limit: int = None
    ) -> dict:
        """
        Retrieve all member records with optional filtering, sorting, and result limiting.

        Args:
            filter_by (Dict[str, Any], optional): Filter dict where key is attribute name and value is the value to match.
            sort_by (list of str, optional): List of attribute names to sort by (priority order).
            sort_order (str, optional): 'asc' or 'desc', defaults to 'asc'.
            limit (int, optional): Maximum number of results to return. If None, returns all.

        Returns:
            dict: {
                "success": True,
                "data": List[MemberInfo],  # Possibly empty if no match.
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Can filter and sort by any top-level attribute in MemberInfo.
            - filter_by also supports nested profile_metadata lookups via dot notation
              such as 'profile_metadata.account_type'.
            - Non-existent filter/sort attribute will return an error.
            - Limit must be a positive integer if provided.
        """
        members = list(self.members.values())

        # Filtering
        if filter_by:
            for key in filter_by:
                if "." in key:
                    prefix, nested_key = key.split(".", 1)
                    if prefix != "profile_metadata" or not nested_key:
                        return {"success": False, "error": f"Invalid filter attribute: {key}"}
                    continue
                if key not in MemberInfo.__annotations__:
                    return {"success": False, "error": f"Invalid filter attribute: {key}"}

            def matches(member: MemberInfo) -> bool:
                for key, value in filter_by.items():
                    if "." in key:
                        prefix, nested_key = key.split(".", 1)
                        if prefix != "profile_metadata":
                            return False
                        if member.get("profile_metadata", {}).get(nested_key) != value:
                            return False
                    elif member.get(key) != value:
                        return False
                return True

            members = [m for m in members if matches(m)]

        # Sorting
        if sort_by:
            for key in sort_by:
                if key not in MemberInfo.__annotations__:
                    return {"success": False, "error": f"Invalid sort attribute: {key}"}
            reverse = (sort_order.lower() == "desc")
            try:
                members.sort(key=lambda m: tuple(m[k] for k in sort_by), reverse=reverse)
            except Exception as e:
                return {"success": False, "error": f"Error sorting members: {str(e)}"}

        # Limiting
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                return {"success": False, "error": "Limit must be a non-negative integer"}
            members = members[:limit]

        return {"success": True, "data": members}

    def search_members(
        self, 
        name_contains: str = "", 
        contact_info: str = "", 
        membership_sta: str = "", 
        sort_by: str = "", 
        ascending: bool = True, 
        limit: int = 0
    ) -> dict:
        """
        Retrieve members matching the given search criteria (partial name, contact_info, membership status),
        with optional sorting and result limiting.
    
        Args:
            name_contains (str): Case-insensitive substring for name (partial match).
            contact_info (str): Exact match for contact_info (empty to ignore).
            membership_sta (str): Exact match for membership_sta (empty to ignore).
            sort_by (str): Attribute name to sort by ('member_id', 'name', 'contact_info', 'join_date', 'membership_sta').
            ascending (bool): Sort order; True for ascending, False for descending.
            limit (int): Maximum number of results to return (0 or less means no limit).
    
        Returns:
            dict: 
            {
                "success": True,
                "data": List[MemberInfo],  # possibly empty
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Members can be filtered and sorted by any attribute.
            - Partial matching supported only on 'name'.
            - Limit is optional; <= 0 means no limit.
            - Sorting by unsupported field returns failure.
        """
        results = []
        for member in self.members.values():
            if name_contains and name_contains.lower() not in member["name"].lower():
                continue
            if contact_info and contact_info != member["contact_info"]:
                continue
            if membership_sta and membership_sta != member["membership_sta"]:
                continue
            results.append(member)

        if sort_by:
            valid_sort_fields = {"member_id", "name", "contact_info", "join_date", "membership_sta"}
            if sort_by not in valid_sort_fields:
                return {"success": False, "error": f"Invalid sort_by field: {sort_by}"}
            try:
                results = sorted(results, key=lambda m: m[sort_by], reverse=not ascending)
            except Exception:
                return {"success": False, "error": f"Failed to sort by field: {sort_by}"}

        if limit and isinstance(limit, int) and limit > 0:
            results = results[:limit]

        return {"success": True, "data": results}

    def count_members(self, criteria: dict = None) -> dict:
        """
        Return the total number of members in the community, or matching specific criteria.

        Args:
            criteria (dict, optional): A dictionary of attribute-value pairs to filter members.
                Example: {"membership_sta": "active", "profile_metadata.role": "admin"}
                Supports matching on top-level keys and nested 'profile_metadata' keys as dot notation.

        Returns:
            dict: {
                "success": True,
                "count": int  # Number of matching members
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If criteria includes attribute names not in MemberInfo or its subfields, returns error.
            - If no criteria is provided, count all members.
        """
        # Supported MemberInfo keys (including special handling for profile_metadata subkeys)
        allowed_keys = {"member_id", "name", "contact_info", "join_date", "profile_metadata", "membership_sta"}
    
        criteria = criteria or {}
        if not isinstance(criteria, dict):
            return {"success": False, "error": "Criteria must be a dictionary."}
    
        # Validate criteria keys
        for key in criteria.keys():
            if "." in key:
                k0, k1 = key.split(".", 1)
                if k0 != "profile_metadata":
                    return {"success": False, "error": f"Unsupported nested field: {key}"}
            elif key not in allowed_keys:
                return {"success": False, "error": f"Invalid member attribute: {key}"}

        def matches(member: MemberInfo) -> bool:
            for key, val in criteria.items():
                if "." in key:
                    k0, k1 = key.split(".", 1)
                    if k0 == "profile_metadata":
                        if member.get("profile_metadata", {}).get(k1) != val:
                            return False
                else:
                    if member.get(key) != val:
                        return False
            return True

        if criteria:
            total = sum(1 for m in self.members.values() if matches(m))
        else:
            total = len(self.members)
        return {"success": True, "count": total}


    def add_member(
        self,
        member_id: str,
        name: str,
        contact_info: str,
        profile_metadata: Dict[str, Any] = None,
        membership_sta: str = "active",
    ) -> dict:
        """
        Create a new member profile with a unique member_id.

        Args:
            member_id (str): Unique identifier for the member.
            name (str): Member's name.
            contact_info (str): Member's contact information.
            profile_metadata (dict, optional): Additional profile metadata.
            membership_sta (str, optional): Membership status string. Defaults to 'active'.

        Returns:
            dict: {
                "success": True,
                "message": "Member <member_id> added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - member_id must be unique.
            - join_date is assigned as the current time at creation (ISO string).
        """
        if member_id in self.members:
            return {"success": False, "error": f"Member with id '{member_id}' already exists."}
    
        if not name or not contact_info:
            return {"success": False, "error": "Name and contact_info are required fields."}

        if profile_metadata is None:
            profile_metadata = {}

        join_date = datetime.now().isoformat()

        self.members[member_id] = {
            "member_id": member_id,
            "name": name,
            "contact_info": contact_info,
            "join_date": join_date,
            "profile_metadata": profile_metadata,
            "membership_sta": membership_sta,
        }

        return {"success": True, "message": f"Member {member_id} added."}

    def update_member_profile(
        self,
        member_id: str,
        name: str = None,
        contact_info: str = None,
        profile_metadata: dict = None,
        membership_sta: str = None
    ) -> dict:
        """
        Update editable attributes of an existing member. Only the following fields are mutable:
        - name
        - contact_info
        - profile_metadata (merged: updates/overwrites provided keys)
        - membership_sta (membership_status)

        Args:
            member_id (str): Unique identifier for the member (required, immutable).
            name (str, optional): New name.
            contact_info (str, optional): New contact info.
            profile_metadata (dict, optional): Dict of metadata to update/merge.
            membership_sta (str, optional): New membership status value.

        Returns:
            dict:
                On success: {"success": True, "message": "..."}
                On failure: {"success": False, "error": "..."}
        Constraints:
            - member_id and join_date cannot be modified (immutable).
            - Nonexistent member_id is an error.
            - If no editable attribute provided, operation is a no-op and still succeeds.
        """
        member = self.members.get(member_id)
        if not member:
            return {"success": False, "error": "Member not found."}

        updated = False

        if name is not None:
            member["name"] = name
            updated = True
        if contact_info is not None:
            member["contact_info"] = contact_info
            updated = True
        if profile_metadata is not None and isinstance(profile_metadata, dict):
            # Merge/overwrite keys with the existing metadata
            member["profile_metadata"].update(profile_metadata)
            updated = True
        if membership_sta is not None:
            member["membership_sta"] = membership_sta
            updated = True

        # No forbidden fields are modified regardless of provided params

        return {
            "success": True,
            "message": "Member profile updated successfully." if updated else "No changes were made."
        }

    def remove_member(self, member_id: str) -> dict:
        """
        Remove a member from the system by their member_id.

        Args:
            member_id (str): The unique identifier of the member to remove.

        Returns:
            dict: 
                - If the member exists:
                    {"success": True, "message": "Member <member_id> removed successfully."}
                - If the member does not exist:
                    {"success": False, "error": "Member not found."}

        Constraints:
            - The member_id must exist in the system for removal.
        """
        if member_id not in self.members:
            return { "success": False, "error": "Member not found." }
    
        del self.members[member_id]
        return { "success": True, "message": f"Member {member_id} removed successfully." }

    def update_membership_status(self, member_id: str, new_status: str) -> dict:
        """
        Change the membership_sta (membership status) field of a member.

        Args:
            member_id (str): The unique identifier of the member.
            new_status (str): The new status to assign (e.g., 'active', 'suspended', 'expired').

        Returns:
            dict: {
                "success": True,
                "message": "Membership status updated."
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - Only updates the 'membership_sta' field for the member.
            - Fails if member_id does not exist.
            - join_date and other fields are not modified.
        """
        if member_id not in self.members:
            return { "success": False, "error": "Member not found." }
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid membership status." }
    
        self.members[member_id]["membership_sta"] = new_status.strip()
        return { "success": True, "message": "Membership status updated." }

    def update_profile_metadata(self, member_id: str, profile_metadata: Dict[str, Any]) -> dict:
        """
        Update only the profile_metadata attribute for the specified member.

        Args:
            member_id (str): The unique identifier of the member to update.
            profile_metadata (Dict[str, Any]): The new metadata dictionary to assign.

        Returns:
            dict:
                On success: { "success": True, "message": "Profile metadata updated for member <member_id>." }
                On failure: { "success": False, "error": "Member not found." }

        Constraints:
            - Only the profile_metadata attribute is modified.
            - No other member attributes (including join_date) are altered.
            - Member must exist.

        """
        if member_id not in self.members:
            return { "success": False, "error": "Member not found." }
        if not isinstance(profile_metadata, dict):
            return { "success": False, "error": "profile_metadata must be a dictionary." }

        member = self.members[member_id]
        member['profile_metadata'] = profile_metadata
        return { "success": True, "message": f"Profile metadata updated for member {member_id}." }

    def bulk_remove_members(
        self, 
        member_ids: list[str] = None, 
        filter_criteria: dict = None
    ) -> dict:
        """
        Remove multiple members from the system based on a list of member_ids and/or filter criteria.

        Args:
            member_ids (list[str], optional): List of member IDs to remove.
            filter_criteria (dict, optional): Dictionary of attribute-value pairs to filter members for removal.

        Returns:
            dict: {
                "success": True,
                "message": "X members removed"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - At least one of member_ids or filter_criteria must be provided.
            - Does nothing (but succeeds) if there are no matches.
        """
        if not member_ids and not filter_criteria:
            return {"success": False, "error": "No member_ids or filter criteria provided"}

        # Find members to remove
        to_remove = set()

        if member_ids:
            for mid in member_ids:
                if mid in self.members:
                    to_remove.add(mid)
        if filter_criteria:
            for mid, m in self.members.items():
                match = True
                for attr, value in filter_criteria.items():
                    # Support nested keys for profile_metadata, e.g. {"profile_metadata.age": 25}
                    if "." in attr:
                        fields = attr.split(".")
                        d = m
                        for f in fields:
                            if isinstance(d, dict) and f in d:
                                d = d[f]
                            else:
                                match = False
                                break
                        if not match or d != value:
                            match = False
                            break
                    else:
                        if m.get(attr) != value:
                            match = False
                            break
                if match:
                    to_remove.add(mid)

        for mid in to_remove:
            self.members.pop(mid, None)

        return {"success": True, "message": f"{len(to_remove)} members removed"}


class CommunityMembershipManagementSystem(BaseEnv):
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

    def get_member_by_id(self, **kwargs):
        return self._call_inner_tool('get_member_by_id', kwargs)

    def list_members(self, **kwargs):
        return self._call_inner_tool('list_members', kwargs)

    def search_members(self, **kwargs):
        return self._call_inner_tool('search_members', kwargs)

    def count_members(self, **kwargs):
        return self._call_inner_tool('count_members', kwargs)

    def add_member(self, **kwargs):
        return self._call_inner_tool('add_member', kwargs)

    def update_member_profile(self, **kwargs):
        return self._call_inner_tool('update_member_profile', kwargs)

    def remove_member(self, **kwargs):
        return self._call_inner_tool('remove_member', kwargs)

    def update_membership_status(self, **kwargs):
        return self._call_inner_tool('update_membership_status', kwargs)

    def update_profile_metadata(self, **kwargs):
        return self._call_inner_tool('update_profile_metadata', kwargs)

    def bulk_remove_members(self, **kwargs):
        return self._call_inner_tool('bulk_remove_members', kwargs)
