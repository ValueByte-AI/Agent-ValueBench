# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime



class MedicalProfessionalInfo(TypedDict):
    professional_id: str
    name: str
    date_of_birth: str
    specialty: str
    contact_info: str

class MedicalLicenseInfo(TypedDict):
    license_number: str
    professional_id: str
    issue_date: str
    expiry_date: str
    status: str  # Should be one of {"active", "expired", "suspended"}

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Medical professional licensing registry environment.
        """

        # Medical professionals: {professional_id: MedicalProfessionalInfo}
        self.professionals: Dict[str, MedicalProfessionalInfo] = {}

        # Medical licenses: {license_number: MedicalLicenseInfo}
        self.licenses: Dict[str, MedicalLicenseInfo] = {}

        # Constraints:
        # - Each license_number must be unique (enforced by dict structure).
        # - Each medical professional can only have one active license at a time.
        # - License status must be one of {'active', 'expired', 'suspended'}.
        # - Licenses are valid only if status == "active" and the current date is between issue_date and expiry_date.

    def get_professional_by_name(self, name: str) -> dict:
        """
        Retrieve all medical professionals' information matching the specified name.

        Args:
            name (str): The name of the medical professional to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalProfessionalInfo],  # List of professional info dicts (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. missing name
            }

        Notes:
            - The match is exact and case-sensitive.
            - Multiple professionals may share the same name.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Name must be provided"}
    
        results = [
            prof_info for prof_info in self.professionals.values()
            if prof_info["name"] == name
        ]
        return {"success": True, "data": results}

    def get_professional_by_id(self, professional_id: str) -> dict:
        """
        Retrieve a medical professional's info given their professional_id.

        Args:
            professional_id (str): The unique identifier for the medical professional.

        Returns:
            dict: 
                On success: {"success": True, "data": MedicalProfessionalInfo}
                On failure: {"success": False, "error": "Professional not found"}

        Constraints:
            - The professional_id must exist in the registry.
        """
        if professional_id not in self.professionals:
            return {"success": False, "error": "Professional not found"}

        return {"success": True, "data": self.professionals[professional_id]}

    def list_all_professionals(self) -> dict:
        """
        List all registered medical professionals in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalProfessionalInfo]  # All professionals (may be empty if none registered)
            }
        """
        all_professionals = list(self.professionals.values())
        return { "success": True, "data": all_professionals }

    def list_licenses_for_professional(self, professional_id: str) -> dict:
        """
        Get all license records associated with a given professional_id.

        Args:
            professional_id (str): Unique identifier of the medical professional.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalLicenseInfo]  # All licenses for this professional (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g., professional not found.
            }

        Constraints:
            - professional_id must exist in the registry (self.professionals).
        """
        if professional_id not in self.professionals:
            return {"success": False, "error": "Professional not found"}

        licenses = [
            license_info for license_info in self.licenses.values()
            if license_info["professional_id"] == professional_id
        ]
        return {"success": True, "data": licenses}

    def get_license_by_number(self, license_number: str) -> dict:
        """
        Retrieve full license information for a given license_number.

        Args:
            license_number (str): The unique identifier of the medical license.

        Returns:
            dict:
              - Success: { "success": True, "data": MedicalLicenseInfo }
              - Failure: { "success": False, "error": "License not found" }

        Constraints:
            - license_number must exist in the registry.
        """
        license_info = self.licenses.get(license_number)
        if not license_info:
            return { "success": False, "error": "License not found" }
        return { "success": True, "data": license_info }

    def list_licenses_by_status(self, status: str) -> dict:
        """
        List all license records filtered by their status.

        Args:
            status (str): License status to filter by. Must be one of {"active", "expired", "suspended"}.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalLicenseInfo],  # Matching license records (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
        Constraints:
            - Only the statuses {"active", "expired", "suspended"} are allowed.
        """
        allowed_statuses = {"active", "expired", "suspended"}
        if status not in allowed_statuses:
            return {"success": False, "error": "Invalid status value"}
    
        filtered = [
            license_info for license_info in self.licenses.values()
            if license_info["status"] == status
        ]
        return {"success": True, "data": filtered}

    def check_license_status(self, license_number: str) -> dict:
        """
        Query the status field ("active", "expired", "suspended") of a medical license.

        Args:
            license_number (str): The unique identifier for the license to query.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": {
                        "license_number": str,
                        "status": str
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - license_number must exist in the registry.
        """
        license_info = self.licenses.get(license_number)
        if not license_info:
            return { "success": False, "error": "License not found" }
    
        return {
            "success": True,
            "data": {
                "license_number": license_number,
                "status": license_info.get("status", None)
            }
        }


    def check_if_professional_has_active_license(self, professional_id: str) -> dict:
        """
        Determine if the specified professional currently has a valid (active) license.
    
        Args:
            professional_id (str): The professional's unique identifier.
    
        Returns:
            dict: {
                "success": True,
                "data": bool  # True if professional has an active and currently valid license, else False
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. not found
            }
        
        Constraints:
            - License considered valid if:
                - status == "active"
                - current date is >= issue_date and <= expiry_date (inclusive)
            - Each medical professional can have at most one active license at a time.
        """
        if professional_id not in self.professionals:
            return { "success": False, "error": "Professional not found" }
    
        current_date = datetime.now().date()
        has_active = False
        for license_info in self.licenses.values():
            if license_info["professional_id"] == professional_id and license_info["status"] == "active":
                try:
                    issue = datetime.strptime(license_info["issue_date"], "%Y-%m-%d").date()
                    expiry = datetime.strptime(license_info["expiry_date"], "%Y-%m-%d").date()
                except Exception:
                    # Malformed date
                    continue
                if issue <= current_date <= expiry:
                    has_active = True
                    break

        return { "success": True, "data": has_active }


    def check_license_validity(self, license_number: str) -> dict:
        """
        Evaluate if the given license is currently valid.

        Args:
            license_number (str): The medical license number to check.

        Returns:
            dict: 
                {
                  "success": True,
                  "data": { "license_number": ..., "valid": True/False }
                }
                or
                {
                  "success": False,
                  "error": <reason>
                }

        Validity logic:
            - License status must be "active"
            - Current date must be >= issue_date and <= expiry_date (inclusive)
            - Dates are assumed to be in 'YYYY-MM-DD' or ISO format
        """
        license_info = self.licenses.get(license_number)
        if not license_info:
            return { "success": False, "error": "License not found" }
    
        status = license_info.get("status")
        issue_date_str = license_info.get("issue_date")
        expiry_date_str = license_info.get("expiry_date")

        try:
            issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
        except Exception:
            return { "success": False, "error": "Invalid date format in license record" }

        is_active = (status == "active")
        in_range = (issue_date <= today <= expiry_date)

        valid = is_active and in_range

        return {
            "success": True,
            "data": {
                "license_number": license_number,
                "valid": valid
            }
        }

    def create_license(
        self,
        license_number: str,
        professional_id: str,
        issue_date: str,
        expiry_date: str,
        status: str
    ) -> dict:
        """
        Create a new MedicalLicense record associated with a medical professional.
    
        Args:
            license_number (str): Unique license number.
            professional_id (str): ID of the medical professional (must exist).
            issue_date (str): License issue date (ISO formatted string).
            expiry_date (str): License expiry date (ISO formatted string).
            status (str): Initial status ("active", "expired", or "suspended").
    
        Returns:
            dict: {
                "success": True,
                "message": "License created successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        Constraints:
            - license_number must be unique.
            - professional_id must refer to an existing professional.
            - status must be in {"active", "expired", "suspended"}.
            - Only one active license per professional at a time.
        """
        # Check license_number uniqueness
        if license_number in self.licenses:
            return {"success": False, "error": "License number already exists."}
    
        # Validate professional_id
        if professional_id not in self.professionals:
            return {"success": False, "error": "Professional ID does not exist."}
    
        # Validate status
        if status not in {"active", "expired", "suspended"}:
            return {"success": False, "error": "Invalid license status."}
    
        # Only one active license per professional at a time
        if status == "active":
            for lic in self.licenses.values():
                if lic["professional_id"] == professional_id and lic["status"] == "active":
                    return {
                        "success": False,
                        "error": "Professional already has an active license."
                    }
    
        # Create the license
        self.licenses[license_number] = {
            "license_number": license_number,
            "professional_id": professional_id,
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "status": status
        }
    
        return {"success": True, "message": "License created successfully"}

    def update_license_status(self, license_number: str, new_status: str) -> dict:
        """
        Change the status of a medical license (must be one of allowed values).

        Args:
            license_number (str): The license to update.
            new_status (str): The new status ('active', 'expired', or 'suspended').

        Returns:
            dict: { "success": True, "message": str } on success,
                  { "success": False, "error": str } on error.

        Constraints:
            - new_status must be in {'active', 'expired', 'suspended'}
            - License must exist.
            - Only one 'active' license per medical professional is allowed.
        """
        allowed_statuses = {'active', 'expired', 'suspended'}
        if license_number not in self.licenses:
            return {"success": False, "error": f"License number '{license_number}' does not exist."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Status '{new_status}' is not allowed. Allowed: {allowed_statuses}."}

        license_info = self.licenses[license_number]
        professional_id = license_info["professional_id"]

        if new_status == "active":
            # Check if this professional has another active license (not this one!)
            for lic in self.licenses.values():
                if (
                    lic["professional_id"] == professional_id
                    and lic["license_number"] != license_number
                    and lic["status"] == "active"
                ):
                    return {
                        "success": False,
                        "error": "Professional already has another active license. Only one active license allowed per professional."
                    }

        self.licenses[license_number]["status"] = new_status
        return {
            "success": True,
            "message": f"License status updated to '{new_status}'."
        }

    def update_license_expiry_date(self, license_number: str, new_expiry_date: str) -> dict:
        """
        Modifies the expiry date of an existing medical license.

        Args:
            license_number (str): The unique identifier for the license to update.
            new_expiry_date (str): The new expiry date to set (should follow standard format, e.g., "YYYY-MM-DD").

        Returns:
            dict: 
            - On success: { "success": True, "message": "Expiry date updated successfully." }
            - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The license_number must exist in the system.
            - Does not enforce date format or ordering with issue_date (unless specified elsewhere).
        """
        if license_number not in self.licenses:
            return { "success": False, "error": "License number does not exist." }

        self.licenses[license_number]["expiry_date"] = new_expiry_date
        return { "success": True, "message": "Expiry date updated successfully." }

    def expire_all_licenses_for_professional(self, professional_id: str) -> dict:
        """
        Set all licenses for a specific medical professional to status "expired".

        Args:
            professional_id (str): The unique ID for the medical professional.

        Returns:
            dict: 
                - On success: { "success": True, "message": "..."}
                - On error (professional does not exist): { "success": False, "error": "Professional not found" }

        Constraints:
            - Status must only be set to "expired".
            - Status must be one of {"active", "expired", "suspended"}.
            - No-op if the professional has no licenses (still success).
        """
        if professional_id not in self.professionals:
            return { "success": False, "error": "Professional not found" }

        licenses_modified = 0
        for license_info in self.licenses.values():
            if license_info["professional_id"] == professional_id:
                if license_info["status"] != "expired":
                    license_info["status"] = "expired"
                licenses_modified += 1

        return {
            "success": True,
            "message": f"All licenses for professional {professional_id} set to expired."
        }

    def assign_active_license(self, license_number: str) -> dict:
        """
        Assign the specified license as active for its professional. Expire all other
        licenses for that professional as per registry constraints.

        Args:
            license_number (str): The license number to activate.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The license must exist.
            - Only one active license per professional.
            - Other licenses for the professional will be set to 'expired'.
            - License status must be one of {"active", "expired", "suspended"}.
        """
        if license_number not in self.licenses:
            return { "success": False, "error": "License does not exist" }

        target_license = self.licenses[license_number]
        professional_id = target_license["professional_id"]

        for lic in self.licenses.values():
            if lic["professional_id"] == professional_id:
                if lic["license_number"] == license_number:
                    if lic["status"] != "active":
                        lic["status"] = "active"
                else:
                    if lic["status"] == "active":
                        lic["status"] = "expired"
                    elif lic["status"] not in {"expired", "suspended"}:
                        lic["status"] = "expired"

        return {
            "success": True,
            "message": f"License {license_number} assigned as active for professional {professional_id}. Other licenses set to expired."
        }


class MedicalProfessionalLicensingRegistry(BaseEnv):
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

    def get_professional_by_name(self, **kwargs):
        return self._call_inner_tool('get_professional_by_name', kwargs)

    def get_professional_by_id(self, **kwargs):
        return self._call_inner_tool('get_professional_by_id', kwargs)

    def list_all_professionals(self, **kwargs):
        return self._call_inner_tool('list_all_professionals', kwargs)

    def list_licenses_for_professional(self, **kwargs):
        return self._call_inner_tool('list_licenses_for_professional', kwargs)

    def get_license_by_number(self, **kwargs):
        return self._call_inner_tool('get_license_by_number', kwargs)

    def list_licenses_by_status(self, **kwargs):
        return self._call_inner_tool('list_licenses_by_status', kwargs)

    def check_license_status(self, **kwargs):
        return self._call_inner_tool('check_license_status', kwargs)

    def check_if_professional_has_active_license(self, **kwargs):
        return self._call_inner_tool('check_if_professional_has_active_license', kwargs)

    def check_license_validity(self, **kwargs):
        return self._call_inner_tool('check_license_validity', kwargs)

    def create_license(self, **kwargs):
        return self._call_inner_tool('create_license', kwargs)

    def update_license_status(self, **kwargs):
        return self._call_inner_tool('update_license_status', kwargs)

    def update_license_expiry_date(self, **kwargs):
        return self._call_inner_tool('update_license_expiry_date', kwargs)

    def expire_all_licenses_for_professional(self, **kwargs):
        return self._call_inner_tool('expire_all_licenses_for_professional', kwargs)

    def assign_active_license(self, **kwargs):
        return self._call_inner_tool('assign_active_license', kwargs)

