# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict, Any
import datetime

ALLOWED_REGISTRATION_STATUSES = {
    "active",
    "dissolved",
    "pending",
    "suspended",
    "pending_verification",
}


def _parse_iso8601_date_like(value: str) -> datetime.date:
    if not isinstance(value, str) or not value:
        raise ValueError("date value must be a non-empty string")

    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        return datetime.datetime.fromisoformat(normalized).date()



class CompanyInfo(TypedDict):
    company_id: str
    name: str
    legal_form: str
    registration_date: str  # Expected format: ISO8601 date
    registration_status: str  # Must be one of: "active", "dissolved", "pending", etc.
    address: str
    jurisdiction: str
    dissolution_date: Optional[str]  # None if not dissolved, else date string
    metadata: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing a company registry management system.
        """

        # Companies: {company_id: CompanyInfo}
        # Maps company_id to full company registration details.
        self.companies: Dict[str, CompanyInfo] = {}

        # Constraints:
        # - company_id must be unique for each company (enforced by dict key).
        # - registration_status must be one of a predefined set ("active", "dissolved", "pending", etc.).
        # - Only companies where registration_status == "active" are considered currently registered.
        # - registration_date must be a valid date (in the past or present).
        # - dissolution_date (if present) must not precede registration_date and implies registration_status != "active".

    def list_currently_registered_companies(self) -> dict:
        """
        Retrieve all companies with registration_status == "active".

        Returns:
            dict: {
                "success": True,
                "data": List[CompanyInfo]  # List of active companies; may be empty
            }

        Constraints:
            - Only companies with registration_status == "active" are returned.
        """
        active_companies = [
            company for company in self.companies.values()
            if company.get("registration_status") == "active"
        ]
        return { "success": True, "data": active_companies }

    def get_company_by_id(self, company_id: str) -> dict:
        """
        Retrieve the full record details for a single company by its unique company_id.

        Args:
            company_id (str): The unique identifier for the company.

        Returns:
            dict:
                On success:
                    { "success": True, "data": CompanyInfo }
                On failure (company not found):
                    { "success": False, "error": "Company not found" }

        Constraints:
            - company_id must be unique for each company.
        """
        company = self.companies.get(company_id)
        if company is None:
            return { "success": False, "error": "Company not found" }
        return { "success": True, "data": company }

    def list_companies_by_status(self, registration_status: str) -> dict:
        """
        List companies filtered by a specified registration_status.

        Args:
            registration_status (str): The registration status to filter by (e.g., "active", "pending", "dissolved").

        Returns:
            dict: {
                "success": True,
                "data": List[CompanyInfo]  # List of matching companies (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Invalid status or other error message.
            }

        Constraints:
            - Only valid registration_status values are accepted (e.g., "active", "dissolved", "pending").
            - Matching is case-sensitive.
            - Returns empty list if no companies match but input is valid.
        """
        valid_statuses = ALLOWED_REGISTRATION_STATUSES
    
        if registration_status not in valid_statuses:
            return { "success": False, "error": f"Invalid registration_status: {registration_status}" }

        filtered_companies = [
            company for company in self.companies.values()
            if company["registration_status"] == registration_status
        ]
        return { "success": True, "data": filtered_companies }

    def search_companies_by_name(
        self, 
        query: str, 
        match_type: str = "substring"
    ) -> dict:
        """
        Search for companies by name.

        Args:
            query (str): The search string for the company name.
            match_type (str): "exact" for full match, "substring" for substring (case-insensitive).
                              Defaults to "substring".

        Returns:
            dict: {
                "success": True,
                "data": List[CompanyInfo],  # List of matching company records
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - 'query' must be a non-empty string.
            - Both 'exact' and 'substring' matching are supported (case-insensitive).
        """
        if not isinstance(query, str) or query.strip() == "":
            return {"success": False, "error": "Query string must be a non-empty string"}

        normalized_query = query.strip().lower()
        match_type = match_type.lower().strip()
        results = []

        for company in self.companies.values():
            name = company["name"]
            if match_type == "exact":
                if name.lower() == normalized_query:
                    results.append(company)
            elif match_type == "substring":
                if normalized_query in name.lower():
                    results.append(company)
            else:
                return {"success": False, "error": "Invalid match_type. Must be 'exact' or 'substring'."}

        return {"success": True, "data": results}

    def get_company_registration_history(self, company_id: str) -> dict:
        """
        Retrieve the registration and dissolution dates and known status history for a specified company.

        Args:
            company_id (str): Unique company identifier.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "company_id": str,
                    "name": str,
                    "registration_date": str,
                    "dissolution_date": Optional[str],
                    "registration_status": str,
                    "status_history": list  # Status change history if tracked, or [] if not available
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - company_id must exist in the registry.
            - Only registration_date/current status and dissolution_date/status are available; no full status change history is tracked.
        """
        company = self.companies.get(company_id)
        if not company:
            return {"success": False, "error": "Company ID does not exist."}
    
        # Since status changes are not tracked, provide only what's available.
        history = []

        # Include registration and possible dissolution.
        reg_date = company["registration_date"]
        reg_status = company["registration_status"]
        diss_date = company.get("dissolution_date")

        # Add registration event
        history.append({
            "date": reg_date,
            "status": "registered"
        })
        # Add dissolution event, if present
        if diss_date:
            history.append({
                "date": diss_date,
                "status": "dissolved"
            })
    
        # Prepare result
        result = {
            "company_id": company["company_id"],
            "name": company["name"],
            "registration_date": reg_date,
            "dissolution_date": diss_date,
            "registration_status": reg_status,
            "status_history": history
        }

        return {"success": True, "data": result}

    def list_all_companies(self) -> dict:
        """
        Returns the full list of all companies in the registry, regardless of their current status.

        Args:
            None

        Returns:
            dict:
                - success: True if operation completes successfully
                - data: List[CompanyInfo], a possibly empty list of all companies

        Constraints:
            - No constraints: all companies should be returned, regardless of status.
        """
        all_companies = list(self.companies.values())
        return {
            "success": True,
            "data": all_companies
        }

    def register_new_company(
        self,
        company_id: str,
        name: str,
        legal_form: str,
        registration_date: str,
        registration_status: str,
        address: str,
        jurisdiction: str,
        dissolution_date: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Registers a new company in the registry.

        Args:
            company_id (str): Unique company identifier.
            name (str): Company name.
            legal_form (str): Legal form.
            registration_date (str): ISO8601 date string. Must be in past/present.
            registration_status (str): Must be one of predefined set.
            address (str): Registered address.
            jurisdiction (str): Jurisdiction of registration.
            dissolution_date (Optional[str]): If present, must not precede registration_date.
            metadata (Optional[dict]): Extra associated metadata.

        Returns:
            dict: { "success": True, "message": str } on success,
                  { "success": False, "error": str } on error.

        Constraints:
            - company_id must be unique.
            - registration_date must be in the past or today.
            - registration_status in allowed set.
            - if dissolution_date present: must not precede registration_date; registration_status != "active".
        """

        # Company ID uniqueness
        if company_id in self.companies:
            return {"success": False, "error": "Company ID already exists."}

        # registration_status validity
        if registration_status not in ALLOWED_REGISTRATION_STATUSES:
            return {
                "success": False,
                "error": (
                    "registration_status must be one of: "
                    f"{', '.join(sorted(ALLOWED_REGISTRATION_STATUSES))}."
                ),
            }

        # Parse registration_date
        try:
            reg_date_obj = _parse_iso8601_date_like(registration_date)
        except Exception:
            return {"success": False, "error": "registration_date must be a valid ISO8601 date string."}

        now = datetime.date.today()
        if reg_date_obj > now:
            return {"success": False, "error": "registration_date must not be in the future."}

        # Handle dissolution_date if provided
        diss_date_obj = None
        if dissolution_date is not None:
            try:
                diss_date_obj = _parse_iso8601_date_like(dissolution_date)
            except Exception:
                return {"success": False, "error": "dissolution_date must be a valid ISO8601 date string."}
            if diss_date_obj < reg_date_obj:
                return {"success": False, "error": "dissolution_date cannot precede registration_date."}
            if registration_status == "active":
                return {
                    "success": False,
                    "error": "registration_status cannot be 'active' if dissolution_date is present."
                }

        company_info: CompanyInfo = {
            "company_id": company_id,
            "name": name,
            "legal_form": legal_form,
            "registration_date": registration_date,
            "registration_status": registration_status,
            "address": address,
            "jurisdiction": jurisdiction,
            "dissolution_date": dissolution_date,
            "metadata": metadata if metadata is not None else {}
        }

        self.companies[company_id] = company_info

        return {"success": True, "message": "Company registered successfully."}

    def update_company_record(self, company_id: str, updates: dict) -> dict:
        """
        Modify mutable attributes (such as address, legal_form, metadata, etc.) of an existing company record.

        Args:
            company_id (str): Unique identifier of the target company.
            updates (dict): Dictionary of attributes and their new values to update. 
                            Keys can include: name, legal_form, address, jurisdiction, dissolution_date,
                            registration_status, metadata.

        Returns:
            dict: {
                "success": True,
                "message": str   # Description of the update
            }
            OR
            {
                "success": False,
                "error": str     # Reason for failure
            }

        Constraints:
            - company_id must exist.
            - Cannot update company_id or registration_date.
            - registration_status must be one of allowed set.
            - dissolution_date (if present) must not precede registration_date and implies registration_status != "active".
        """
        allowed_statuses = ALLOWED_REGISTRATION_STATUSES
        immutable_fields = {"company_id", "registration_date"}
        if company_id not in self.companies:
            return {"success": False, "error": "Company with the given ID does not exist."}

        company = self.companies[company_id]
        update_keys = set(updates.keys())

        # Check for attempt to update immutable fields
        if update_keys & immutable_fields:
            return {"success": False, "error": "Cannot update immutable fields: company_id or registration_date."}

        modified_fields = []
        # Enforce field rules & perform updates
        for key, value in updates.items():
            if key in immutable_fields:
                continue  # Already error checked; extra protection

            if key == "registration_status":
                if value not in allowed_statuses:
                    return {"success": False, "error": f"Invalid registration_status: {value}."}
                company["registration_status"] = value
                modified_fields.append(key)
            elif key == "dissolution_date":
                reg_date = company["registration_date"]
                # Accept value=None (undissolve; albeit in real system, this may not be allowed)
                if value is not None:
                    if value < reg_date:
                        return {"success": False, "error": "Dissolution date cannot precede registration date."}
                    # If dissolution_date set, registration_status cannot stay "active"
                    if company["registration_status"] == "active":
                        company["registration_status"] = "dissolved"
                        modified_fields.append("registration_status")
                company["dissolution_date"] = value
                modified_fields.append(key)
            elif key == "metadata":
                # Merge metadata dict
                if not isinstance(value, dict):
                    return {"success": False, "error": "metadata must be a dictionary."}
                company["metadata"].update(value)
                modified_fields.append(key)
            elif key in company:
                company[key] = value
                modified_fields.append(key)
            else:
                return {"success": False, "error": f"Unknown field: {key}."}

        self.companies[company_id] = company
        if modified_fields:
            return {"success": True, "message": f"Updated fields: {', '.join(modified_fields)}."}
        else:
            return {"success": False, "error": "No valid fields updated."}

    def change_company_status(
        self,
        company_id: str,
        new_status: str,
        dissolution_date: Optional[str] = None
    ) -> dict:
        """
        Change a company's registration_status with all necessary date/validity checks.

        Args:
            company_id (str): The ID of the company to update.
            new_status (str): The new registration_status value (e.g., "active", "dissolved", "pending").
            dissolution_date (Optional[str]): Date of dissolution (ISO8601 string), required if status is "dissolved".

        Returns:
            dict: {
                "success": True,
                "message": "Company status updated from X to Y."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - company_id must exist.
            - new_status must be a valid status.
            - If changing to "dissolved", dissolution_date is required, must not precede registration_date, and company should not remain active.
            - If changing to "active", dissolution_date must be cleared.
        """
        allowed_statuses = ALLOWED_REGISTRATION_STATUSES
        if company_id not in self.companies:
            return {"success": False, "error": "Company ID does not exist"}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status. Allowed: {', '.join(allowed_statuses)}"}

        company = self.companies[company_id]
        old_status = company["registration_status"]
        reg_date = company["registration_date"]

        # Helper to compare dates (assumes format YYYY-MM-DD or ISO8601)
        def is_before(date1: str, date2: str) -> bool:
            return date1 < date2  # Lexicographic works for ISO8601 dates

        # If dissolving
        if new_status == "dissolved":
            if dissolution_date is None:
                return {"success": False, "error": "Dissolution date required when dissolving a company"}
            if is_before(dissolution_date, reg_date):
                return {"success": False, "error": "Dissolution date cannot be before registration date"}
            company["registration_status"] = "dissolved"
            company["dissolution_date"] = dissolution_date

        elif new_status == "active":
            company["registration_status"] = "active"
            company["dissolution_date"] = None

        else:
            # Other allowed statuses
            company["registration_status"] = new_status
            # If status is not dissolved, ensure dissolution_date is None
            if company["dissolution_date"]:
                company["dissolution_date"] = None

        return {
            "success": True,
            "message": f"Company status updated from {old_status} to {new_status}."
        }

    def dissolve_company(self, company_id: str, dissolution_date: str) -> dict:
        """
        Mark a company as dissolved:
          - Sets dissolution_date (ISO8601 string)
          - Updates registration_status to "dissolved"
          - Ensures dissolution_date is not before registration_date

        Args:
            company_id (str): Unique identifier of the company to dissolve.
            dissolution_date (str): Date of dissolution (ISO8601 format; must not precede registration_date).

        Returns:
            dict: 
                success (bool), 
                message (on success) or error (on failure)

        Constraints:
            - company_id must exist.
            - dissolution_date >= registration_date.
            - Cannot dissolve company already dissolved.
        """

        company = self.companies.get(company_id)
        if not company:
            return { "success": False, "error": "Company does not exist." }

        reg_date_str = company.get("registration_date")
        try:
            reg_date = _parse_iso8601_date_like(reg_date_str)
            dissolve_date = _parse_iso8601_date_like(dissolution_date)
        except Exception:
            return { "success": False, "error": "Invalid date format. Use ISO8601 (YYYY-MM-DD)." }

        if dissolve_date < reg_date:
            return { "success": False, "error": "Dissolution date cannot be before registration date." }

        if company.get("registration_status") == "dissolved":
            return { "success": False, "error": "Company is already dissolved." }

        company["dissolution_date"] = dissolution_date
        company["registration_status"] = "dissolved"
        self.companies[company_id] = company
        return { "success": True, "message": f"Company {company_id} marked as dissolved as of {dissolution_date}." }

    def reactivate_company(self, company_id: str) -> dict:
        """
        Revert a company with registration_status not "active" to "active".
        Clears dissolution_date if necessary and ensures consistency with registry constraints.

        Args:
            company_id (str): The unique identifier for the target company.

        Returns:
            dict: 
            - On success: {
                "success": True,
                "message": "Company <company_id> reactivated and dissolution_date cleared."
              }
            - On failure: {
                "success": False,
                "error": "<reason>"
              }

        Constraints:
            - Company must exist in the registry.
            - Company must not already be "active".
            - After operation, registration_status is set to "active", dissolution_date set to None.
        """
        if not company_id or not isinstance(company_id, str):
            return { "success": False, "error": "Invalid or missing company_id." }

        company = self.companies.get(company_id)
        if company is None:
            return { "success": False, "error": f"Company with id '{company_id}' not found." }

        if company['registration_status'] == "active":
            return { "success": False, "error": "Company is already active." }

        # Reactivate company
        company['registration_status'] = "active"
        company['dissolution_date'] = None

        # Update the entry in the registry
        self.companies[company_id] = company

        return {
            "success": True,
            "message": f"Company {company_id} reactivated and dissolution_date cleared."
        }

    def delete_company(self, company_id: str) -> dict:
        """
        Permanently remove a company from the registry.

        Args:
            company_id (str): The unique identifier of the company to be deleted.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Company <company_id> deleted from registry."
                    }
                - On failure (company not found):
                    {
                        "success": False,
                        "error": "Company with id <company_id> does not exist."
                    }

        Constraints:
            - Only delete if company_id exists in the registry.
        """
        if company_id not in self.companies:
            return {
                "success": False,
                "error": f"Company with id {company_id} does not exist."
            }
        del self.companies[company_id]
        return {
            "success": True,
            "message": f"Company {company_id} deleted from registry."
        }


class CompanyRegistryManagementSystem(BaseEnv):
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

    def list_currently_registered_companies(self, **kwargs):
        return self._call_inner_tool('list_currently_registered_companies', kwargs)

    def get_company_by_id(self, **kwargs):
        return self._call_inner_tool('get_company_by_id', kwargs)

    def list_companies_by_status(self, **kwargs):
        return self._call_inner_tool('list_companies_by_status', kwargs)

    def search_companies_by_name(self, **kwargs):
        return self._call_inner_tool('search_companies_by_name', kwargs)

    def get_company_registration_history(self, **kwargs):
        return self._call_inner_tool('get_company_registration_history', kwargs)

    def list_all_companies(self, **kwargs):
        return self._call_inner_tool('list_all_companies', kwargs)

    def register_new_company(self, **kwargs):
        return self._call_inner_tool('register_new_company', kwargs)

    def update_company_record(self, **kwargs):
        return self._call_inner_tool('update_company_record', kwargs)

    def change_company_status(self, **kwargs):
        return self._call_inner_tool('change_company_status', kwargs)

    def dissolve_company(self, **kwargs):
        return self._call_inner_tool('dissolve_company', kwargs)

    def reactivate_company(self, **kwargs):
        return self._call_inner_tool('reactivate_company', kwargs)

    def delete_company(self, **kwargs):
        return self._call_inner_tool('delete_company', kwargs)
