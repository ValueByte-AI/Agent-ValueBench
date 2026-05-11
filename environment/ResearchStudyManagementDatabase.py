# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import time
from typing import Any, Dict
from typing import Dict, Any



class StudyInfo(TypedDict, total=False):
    # Represents an individual research study.
    study_id: str         # (dy_id)
    title: str
    authors: List[str]
    year: int
    methodology: str
    sample_size: int
    outcomes: str
    status: str
    no: Optional[str]

class UserInfo(TypedDict):
    # Represents a user in the system
    _id: str
    name: str
    role: str
    permission: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing research studies and user access.
        """

        # Studies: {study_id: StudyInfo}
        self.studies: Dict[str, StudyInfo] = {}
        #   State space entity: Study
        #   Attributes: study_id, title, authors, year, methodology, sample_size, outcomes, status, no

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        #   State space entity: User
        #   Attributes: _id, name, role, permission

        # Constraints:
        # - Each study must have a unique study_id.
        # - Required fields for each study: methodology and sample_size.
        # - Only users with the appropriate permissions can update study metadata.
        # - Updates to studies should be timestamped/audited for provenance.
        # - Queries must return the current (latest) information for each requested field.

    def get_study_by_id(self, study_id: str) -> dict:
        """
        Retrieve all metadata fields for a study specified by its study_id.

        Args:
            study_id (str): Unique identifier of the study.

        Returns:
            dict: {
                "success": True,
                "data": StudyInfo,  # All available metadata for the study
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. study not found
            }

        Constraints:
            - study_id must be unique and exist in the database.
        """
        study = self.studies.get(study_id)
        if not study:
            return { "success": False, "error": "Study not found" }

        return { "success": True, "data": study }

    def get_study_field(self, study_id: str, field_name: str) -> dict:
        """
        Get the value of a specific field (e.g., methodology, sample_size) for a study.

        Args:
            study_id (str): The unique identifier of the study.
            field_name (str): The field name to query (e.g., 'methodology', 'sample_size').

        Returns:
            dict: {
                "success": True,
                "data": <field_value>  # Value for the requested field, may be None if field not present
            }
            or
            {
                "success": False,
                "error": str  # Error description (study not found, invalid field name)
            }

        Constraints:
            - study_id must refer to an existing study.
            - field_name must be a valid field for StudyInfo.
        """
        if study_id not in self.studies:
            return { "success": False, "error": "Study not found" }

        valid_fields = {
            "study_id", "title", "authors", "year", "methodology", "sample_size",
            "outcomes", "status", "no"
        }

        if field_name not in valid_fields:
            return { "success": False, "error": "Invalid field name" }

        field_value = self.studies[study_id].get(field_name, None)
        return { "success": True, "data": field_value }

    def list_all_studies(self) -> dict:
        """
        Return metadata for all research studies in the database.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[StudyInfo] # metadata of all studies (empty if none exist)
                }
        Constraints:
            - All returned data must be current.
        """
        all_studies = list(self.studies.values())
        return {"success": True, "data": all_studies}

    def search_studies(
        self,
        year: int = None,
        author: str = None,
        methodology: str = None,
        status: str = None
    ) -> dict:
        """
        Search studies by optional filters: year, author, methodology, and/or status.

        Args:
            year (int, optional): Publication year.
            author (str, optional): Author name (study returned if author listed is among authors).
            methodology (str, optional): Methodology string (exact match).
            status (str, optional): Status string (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[StudyInfo],  # List of matching studies, empty if none
            }

        Notes:
            - Filters use AND logic (all provided filters must match).
            - If no filters provided, all studies are returned.
            - For authors, the search is case-sensitive exact substring match within the authors list.
        """
        results = []
        for study in self.studies.values():
            if year is not None and ("year" not in study or study["year"] != year):
                continue
            if author is not None:
                if "authors" not in study or not isinstance(study["authors"], list):
                    continue
                if author not in study["authors"]:
                    continue
            if methodology is not None and ("methodology" not in study or study["methodology"] != methodology):
                continue
            if status is not None and ("status" not in study or study["status"] != status):
                continue
            results.append(study)
        return {"success": True, "data": results}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # user record { "_id", "name", "role", "permission" }
            }
            or
            {
                "success": False,
                "error": str  # "User not found"
            }
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_permissions(self, user_id: str) -> dict:
        """
        Return the set of permissions associated with a given user.

        Args:
            user_id (str): The unique identifier (_id) of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of permission strings
            }
            or
            {
                "success": False,
                "error": str  # Description (e.g., user not found)
            }

        Constraints:
            - The user must exist in the database.
            - If the user is found but has no permissions field, treat as empty list.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        permissions = user.get("permission", [])
        if not isinstance(permissions, list):
            # If permissions is somehow corrupt, treat as empty list
            permissions = []
        return { "success": True, "data": permissions }

    def get_study_update_history(self, study_id: str) -> dict:
        """
        Retrieve the audit/provenance log (timestamps, updater) for a study.

        Args:
            study_id (str): The unique identifier of the study whose audit log is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict contains at least "timestamp" and "updater" fields. Empty list if no updates.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. study does not exist.
            }

        Constraints:
            - Only studies that exist in the database can return an audit log.
            - If no log exists, returns empty data list with success.
        """
        # Check if study exists
        if study_id not in self.studies:
            return { "success": False, "error": "Study does not exist." }

        log_source = None
        if hasattr(self, "study_update_audits"):
            log_source = self.study_update_audits
        elif hasattr(self, "study_update_history"):
            log_source = self.study_update_history
        else:
            return { "success": True, "data": [] }

        if isinstance(log_source, dict):
            return { "success": True, "data": log_source.get(study_id, []) }

        if isinstance(log_source, list):
            filtered = []
            for entry in log_source:
                if not isinstance(entry, dict):
                    continue
                entry_study_id = entry.get("study_id")
                if entry_study_id is None or entry_study_id == study_id:
                    filtered.append(entry)
            return { "success": True, "data": filtered }

        return { "success": True, "data": [] }

    def add_study(
        self,
        study_id: str,
        methodology: str,
        sample_size: int,
        title: str = "",
        authors: Optional[list] = None,
        year: Optional[int] = None,
        outcomes: str = "",
        status: str = "",
        no: Optional[str] = None
    ) -> dict:
        """
        Add a new study to the database, enforcing unique study_id and required fields.

        Args:
            study_id (str): Unique identifier for the study (required).
            methodology (str): Study methodology description (required).
            sample_size (int): Sample size (required).
            title (str, optional): Study title.
            authors (list[str], optional): List of author names.
            year (int, optional): Year of publication/conduct.
            outcomes (str, optional): Study outcomes.
            status (str, optional): Current status of the study.
            no (str, optional): Optional extra study number.

        Returns:
            dict: {
                "success": True, "message": "Study added successfully."
            }
            or
            {
                "success": False, "error": <reason>
            }

        Constraints:
            - study_id must be unique (not already present).
            - methodology and sample_size are required.
        """
        # Check for required fields
        missing_fields = []
        if not study_id:
            missing_fields.append("study_id")
        if not methodology:
            missing_fields.append("methodology")
        if sample_size is None:
            missing_fields.append("sample_size")
        if missing_fields:
            return {"success": False, "error": f"Missing required fields: {', '.join(missing_fields)}"}

        # Enforce unique study_id
        if study_id in self.studies:
            return {"success": False, "error": "Study ID already exists."}

        if authors is None:
            authors = []

        study_entry: StudyInfo = {
            "study_id": study_id,
            "title": title,
            "authors": authors,
            "year": year if year is not None else 0,
            "methodology": methodology,
            "sample_size": sample_size,
            "outcomes": outcomes,
            "status": status,
        }
        if no is not None:
            study_entry["no"] = no

        self.studies[study_id] = study_entry

        return {"success": True, "message": "Study added successfully."}


    def update_study_field(self, user_id: str, study_id: str, field: str, value: Any) -> dict:
        """
        Update a specific metadata field for a study, with permission checking and audit/timestamp.

        Args:
            user_id (str): The ID of the user requesting the update.
            study_id (str): ID of the study to update.
            field (str): Name of the metadata field of the study to update.
            value (Any): The new value to set.

        Returns:
            dict: {
                "success": True,
                "message": "Field updated successfully"
            }
            or
            {
                "success": False,
                "error": "Error description"
            }

        Constraints:
            - Only users with permission ("update_study") can update study metadata.
            - Required fields ("methodology", "sample_size") cannot be emptied/null.
            - Audit/timestamp the update (calls record_study_update_audit, if exists).
            - Only valid fields in StudyInfo can be updated.
        """
        # Check user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check permissions
        if "update_study" not in user.get("permission", []):
            return { "success": False, "error": "Permission denied" }

        # Check study existence
        study = self.studies.get(study_id)
        if not study:
            return { "success": False, "error": "Study does not exist" }

        # Validate field
        study_fields = {
            "study_id", "title", "authors", "year", "methodology", "sample_size",
            "outcomes", "status", "no"
        }
        if field not in study_fields:
            return { "success": False, "error": f"Invalid field '{field}'" }

        # Required fields must not be empty/null
        if field in ("methodology", "sample_size"):
            if value is None or (field == "methodology" and str(value).strip() == ""):
                return { "success": False, "error": f"Field '{field}' is required and cannot be empty/null" }

        # Perform update
        study[field] = value

        timestamp = time.time()
        audit_entry = {
            "timestamp": timestamp,
            "updater": user_id,
            "field": field,
            "new_value": value,
            "study_id": study_id,
        }

        if not isinstance(getattr(self, "study_update_audits", None), dict):
            self.study_update_audits = {}
        self.study_update_audits.setdefault(study_id, []).append(copy.deepcopy(audit_entry))

        if not isinstance(getattr(self, "study_update_history", None), dict):
            self.study_update_history = {}
        self.study_update_history.setdefault(study_id, []).append(copy.deepcopy(audit_entry))

        audit_method = getattr(self, "record_study_update_audit", None)
        if callable(audit_method):
            audit_method(
                study_id=study_id,
                user_id=user_id,
                change_details={
                    "field": field,
                    "new_value": value,
                    "timestamp": timestamp,
                },
            )

        return { "success": True, "message": f"Field '{field}' updated successfully" }

    def batch_update_studies(
        self,
        study_ids: List[str],
        field_name: str,
        new_value,
        user_id: str
    ) -> dict:
        """
        Modify a metadata field across multiple studies, enforcing permissions and tracking provenance.

        Args:
            study_ids (List[str]): List of study_id values to update.
            field_name (str): Name of the StudyInfo field to modify.
            new_value: The new value to assign to the field across studies.
            user_id (str): The _id of the user performing the update (for permission and audit).

        Returns:
            dict: {
                "success": True,
                "message": str,                # Summary of update
                "results": List[dict],         # Per-study success/error report
            }
            or
            {
                "success": False,
                "error": str                   # Description of overarching error (e.g., user/permissions)
            }

        Constraints:
            - User must exist and have 'update' permission.
            - Only valid fields can be updated.
            - Studies must exist.
            - Required fields ('methodology', 'sample_size') must not be set to None/empty.
            - Update actions must be timestamped/audited.
        """


        # Permission validation
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "Updating user not found"}
        if "update" not in user_info.get("permission", []):
            return {"success": False, "error": "User lacks permission to update studies"}

        valid_fields = set([
            "study_id", "title", "authors", "year", "methodology", "sample_size", "outcomes", "status", "no"
        ])

        if field_name not in valid_fields or field_name == "study_id":
            return {"success": False, "error": f"Invalid or non-editable field: {field_name}"}

        # Required fields protection
        if field_name in ("methodology", "sample_size"):
            # Do not allow None or empty string (for methodology) or None/invalid value for sample_size
            if new_value is None or (field_name == "methodology" and str(new_value).strip() == "") \
                    or (field_name == "sample_size" and (not isinstance(new_value, int) or new_value <= 0)):
                return {"success": False, "error": f"Cannot set required field '{field_name}' to an invalid value"}

        results = []
        update_time = time.time()

        for study_id in study_ids:
            result = {"study_id": study_id}
            study_info = self.studies.get(study_id)
            if not study_info:
                result["success"] = False
                result["error"] = "Study not found"
                results.append(result)
                continue

            # Apply update
            study_info[field_name] = new_value
            # Audit/provenance (simple recording)
            if "update_history" not in study_info:
                study_info["update_history"] = []
            audit_entry = {
                "field": field_name,
                "new_value": new_value,
                "updated_by": user_id,
                "timestamp": update_time
            }
            study_info["update_history"].append(audit_entry)

            if not isinstance(getattr(self, "study_update_audits", None), dict):
                self.study_update_audits = {}
            self.study_update_audits.setdefault(study_id, []).append({
                "timestamp": update_time,
                "updater": user_id,
                "field": field_name,
                "new_value": new_value,
                "study_id": study_id,
            })

            if not isinstance(getattr(self, "study_update_history", None), dict):
                self.study_update_history = {}
            self.study_update_history.setdefault(study_id, []).append({
                "timestamp": update_time,
                "updater": user_id,
                "field": field_name,
                "new_value": new_value,
                "study_id": study_id,
            })

            audit_method = getattr(self, "record_study_update_audit", None)
            if callable(audit_method):
                audit_method(
                    study_id=study_id,
                    user_id=user_id,
                    change_details={
                        "field": field_name,
                        "new_value": new_value,
                        "timestamp": update_time,
                    },
                )

            result["success"] = True
            result["message"] = f"Updated {field_name} of study {study_id}"
            results.append(result)

        return {
            "success": True,
            "message": f"Batch update completed for field '{field_name}' across specified studies.",
            "results": results
        }

    def update_user_permissions(self, user_id: str, new_permissions: list, operator_id: str) -> dict:
        """
        Modify a user's permission set (admin/manager-only).

        Args:
            user_id (str): The user whose permissions to change.
            new_permissions (list of str): The new list of permissions.
            operator_id (str): The user performing this operation (for permissions checking).

        Returns:
            dict: {
                "success": True,
                "message": "Permissions updated for user <user_id>.",
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Only users with role 'admin' or 'manager', or 'manage_users' in permission, can modify user permissions.
            - Both target user and operator must exist.
            - new_permissions must be a non-empty list of strings.
            - Users cannot modify their own permissions unless they are admin.
        """
        # Check operator exists
        if operator_id not in self.users:
            return { "success": False, "error": "Operator user does not exist" }
        operator = self.users[operator_id]

        # Check target user exists
        if user_id not in self.users:
            return { "success": False, "error": "Target user does not exist" }
        if not isinstance(new_permissions, list) or not all(isinstance(p, str) for p in new_permissions):
            return { "success": False, "error": "new_permissions must be a list of strings" }

        # Permission check (role or possess 'manage_users' right)
        allowed_roles = {'admin', 'manager'}
        has_manage_right = bool(set(operator.get('permission', [])) & {'manage_users'})

        if operator['role'] not in allowed_roles and not has_manage_right:
            return { "success": False, "error": "Permission denied: operator lacks sufficient rights" }

        # Prevent non-admins from modifying their own permissions
        if operator_id == user_id and operator['role'] != 'admin':
            return { "success": False, "error": "You cannot modify your own permissions unless you are an admin" }

        # Apply the update
        self.users[user_id]['permission'] = new_permissions

        return {
            "success": True,
            "message": f"Permissions updated for user {user_id}."
        }

    def delete_study(self, study_id: str, user_id: str) -> dict:
        """
        Remove a study from the database and record audit logging of this operation.

        Args:
            study_id (str): Unique identifier for the study to be deleted.
            user_id (str): Unique identifier for the user performing the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Study deleted and audit logged"
            }
            or
            {
                "success": False,
                "error": str # Error description
            }

        Constraints:
            - Only users with 'delete_study' permission can perform deletion.
            - The study must exist.
            - Audit log is updated to record who, when, and what was deleted.
        """

        # Check that user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_info = self.users[user_id]
        if "delete_study" not in user_info["permission"]:
            return {"success": False, "error": "User lacks delete_study permission"}

        # Check that study exists
        if study_id not in self.studies:
            return {"success": False, "error": "Study not found"}

        # Delete study
        deleted_study = self.studies.pop(study_id)

        # Audit log (record who+when+what)
        audit_record = {
            "action": "delete_study",
            "study_id": study_id,
            "user_id": user_id,
            "timestamp": time.time(),
            "details": {
                "deleted_study": deleted_study
            }
        }
        # Attach audit log. Add audit log storage if not present.
        if not hasattr(self, "audit_log"):
            self.audit_log = []
        self.audit_log.append(audit_record)

        return {"success": True, "message": "Study deleted and audit logged"}


    def record_study_update_audit(self, study_id: str, user_id: str, change_details: Any) -> dict:
        """
        Log an audit entry whenever study metadata is changed.

        Args:
            study_id (str): The unique identifier of the updated study.
            user_id (str): The unique identifier of the user performing the update.
            change_details (Any): Description of what was updated (e.g., fields changed, values before/after).

        Returns:
            dict: {
                "success": True,
                "message": "Audit log entry recorded."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - study_id must exist in the database.
            - user_id must exist in the database.
            - change_details must be present and non-empty.
            - Audit entry records timestamp, user, study, and change details.
        """
        # Ensure audit_logs attribute exists
        if not hasattr(self, 'audit_logs'):
            self.audit_logs = []

        if study_id not in self.studies:
            return { "success": False, "error": "Invalid study_id: study does not exist." }
        if user_id not in self.users:
            return { "success": False, "error": "Invalid user_id: user does not exist." }
        if change_details is None or (isinstance(change_details, str) and change_details.strip() == ""):
            return { "success": False, "error": "Missing or empty change_details." }

        audit_entry = {
            "timestamp": time.time(),
            "study_id": study_id,
            "user_id": user_id,
            "change_details": change_details
        }
        self.audit_logs.append(audit_entry)

        return { "success": True, "message": "Audit log entry recorded." }


class ResearchStudyManagementDatabase(BaseEnv):
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
        def _parse_jsonish(raw, default):
            if isinstance(raw, type(default)):
                return copy.deepcopy(raw)
            if isinstance(raw, str):
                stripped = raw.strip()
                if not stripped:
                    return copy.deepcopy(default)
                try:
                    parsed = json.loads(stripped)
                except Exception:
                    return copy.deepcopy(default)
                if isinstance(parsed, type(default)):
                    return parsed
            return copy.deepcopy(default)
        for key, value in init_config.items():
            if key == "record_study_update_audit":
                setattr(env, "_record_study_update_audit_state", copy.deepcopy(value))
                continue
            if key in {"study_update_audits", "study_update_history"}:
                parsed = _parse_jsonish(value, {})
                if isinstance(parsed, list):
                    setattr(env, key, copy.deepcopy(parsed))
                else:
                    setattr(env, key, parsed)
                continue
            if key in {"audit_log", "audit_logs"}:
                setattr(env, key, _parse_jsonish(value, []))
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

    def get_study_by_id(self, **kwargs):
        return self._call_inner_tool('get_study_by_id', kwargs)

    def get_study_field(self, **kwargs):
        return self._call_inner_tool('get_study_field', kwargs)

    def list_all_studies(self, **kwargs):
        return self._call_inner_tool('list_all_studies', kwargs)

    def search_studies(self, **kwargs):
        return self._call_inner_tool('search_studies', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_permissions(self, **kwargs):
        return self._call_inner_tool('get_user_permissions', kwargs)

    def get_study_update_history(self, **kwargs):
        return self._call_inner_tool('get_study_update_history', kwargs)

    def add_study(self, **kwargs):
        return self._call_inner_tool('add_study', kwargs)

    def update_study_field(self, **kwargs):
        return self._call_inner_tool('update_study_field', kwargs)

    def batch_update_studies(self, **kwargs):
        return self._call_inner_tool('batch_update_studies', kwargs)

    def update_user_permissions(self, **kwargs):
        return self._call_inner_tool('update_user_permissions', kwargs)

    def delete_study(self, **kwargs):
        return self._call_inner_tool('delete_study', kwargs)

    def record_study_update_audit(self, **kwargs):
        return self._call_inner_tool('record_study_update_audit', kwargs)
