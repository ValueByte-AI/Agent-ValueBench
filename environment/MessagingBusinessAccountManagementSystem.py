# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import re



class BusinessAccountInfo(TypedDict):
    business_id: str
    business_name: str
    profile_description: str
    contact_email: str
    contact_website: str
    registration_status: str
    account_status: str

class PhoneNumberInfo(TypedDict):
    phone_number: str
    business_id: str
    is_verified: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Messaging Platform Business Account Management System state.
        """
        # Business accounts: {business_id: BusinessAccountInfo}
        #   entity BusinessAccount: business_id, business_name, profile_description, contact_email, contact_website, registration_status, account_status
        self.business_accounts: Dict[str, BusinessAccountInfo] = {}

        # Phone numbers: {phone_number: PhoneNumberInfo}
        #   entity PhoneNumber: phone_number, business_id, is_verified
        self.phone_numbers: Dict[str, PhoneNumberInfo] = {}

        # Constraints:
        # - Each phone_number must be unique across all business accounts.
        # - A business account can have one or multiple phone numbers.
        # - Only verified phone numbers can be used for business communication.
        # - Contact details (email, website) must be valid formats if provided.

    def _find_phone_storage_key(self, phone_number: str):
        if not isinstance(phone_number, str) or not phone_number.strip():
            return None
        normalized_phone = phone_number.strip()
        if normalized_phone in self.phone_numbers:
            return normalized_phone
        for key, phone_info in self.phone_numbers.items():
            if phone_info.get("phone_number") == normalized_phone:
                return key
        return None

    def _get_phone_record(self, phone_number: str):
        storage_key = self._find_phone_storage_key(phone_number)
        if storage_key is None:
            return None, None
        return storage_key, self.phone_numbers.get(storage_key)

    def get_business_by_id(self, business_id: str) -> dict:
        """
        Retrieve business account information by unique business_id.

        Args:
            business_id (str): The unique identifier of the business account.

        Returns:
            dict:
                On success: {"success": True, "data": BusinessAccountInfo}, where BusinessAccountInfo is a dict of business attributes.
                On failure: {"success": False, "error": "Business account not found"}

        Constraints:
            - business_id must exist in the system.
        """
        if business_id not in self.business_accounts:
            return {"success": False, "error": "Business account not found"}
    
        business_info = self.business_accounts[business_id]
        return {"success": True, "data": business_info}

    def get_business_by_name(self, business_name: str) -> dict:
        """
        Retrieve business account(s) with the specified business_name.

        Args:
            business_name (str): The business name to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": list of BusinessAccountInfo entries that match the business_name (may be empty list)
                }
        Constraints:
            - Multiple businesses may share the same name; all should be returned.
            - If no match found, return empty list with success: True.
        """
        if not business_name:
            return {"success": True, "data": []}

        result = [
            info for info in self.business_accounts.values()
            if info["business_name"] == business_name
        ]
        return {"success": True, "data": result}

    def get_business_by_phone_number(self, phone_number: str) -> dict:
        """
        Retrieve the business account information associated with a given phone number.

        Args:
            phone_number (str): The unique phone number to query.

        Returns:
            dict: 
                - If found: { "success": True, "data": BusinessAccountInfo }
                - If phone_number does not exist: { "success": False, "error": "Phone number not found" }
                - If business account does not exist: { "success": False, "error": "Business account not found" }

        Constraints:
            - Phone number must exist in the system.
            - The referenced business account must exist.
        """
        _, phone_info = self._get_phone_record(phone_number)
        if not phone_info:
            return { "success": False, "error": "Phone number not found" }

        business_id = phone_info["business_id"]
        business_info = self.business_accounts.get(business_id)
        if not business_info:
            return { "success": False, "error": "Business account not found" }

        return { "success": True, "data": business_info }

    def get_phone_info(self, phone_number: str) -> dict:
        """
        Retrieve information for a phone number: associated business_id and verification status.

        Args:
            phone_number (str): The (unique) phone number to look up.

        Returns:
            dict: {
                "success": True,
                "data": PhoneNumberInfo  # includes phone_number, business_id, is_verified
            }
            or
            {
                "success": False,
                "error": str  # "Phone number not found"
            }

        Constraints:
            - The phone_number must exist in the system phone_numbers list/dict.
        """
        _, info = self._get_phone_record(phone_number)
        if not info:
            return { "success": False, "error": "Phone number not found" }
        return { "success": True, "data": info }

    def list_phones_by_business(self, business_id: str) -> dict:
        """
        List all phone numbers (with full info) linked to a particular business_id.

        Args:
            business_id (str): The identifier for the business whose phone numbers are requested.

        Returns:
            dict: 
                - On success: { "success": True, "data": [PhoneNumberInfo, ...] } 
                    Where 'data' is a list of dictionaries for each phone_number belonging to that business.
                - On failure: { "success": False, "error": str }
                    If business_id does not exist.

        Constraints:
            - The business_id must exist in the system.
        """
        if business_id not in self.business_accounts:
            return {
                "success": False,
                "error": f"Business with id '{business_id}' does not exist"
            }

        phones = [
            phone_info
            for phone_info in self.phone_numbers.values()
            if phone_info["business_id"] == business_id
        ]
        return {
            "success": True,
            "data": phones
        }

    def is_phone_verified(self, phone_number: str) -> dict:
        """
        Check if a specific phone number is marked as verified.

        Args:
            phone_number (str): The phone number to check.

        Returns:
            dict: {
                "success": True,
                "data": { "is_verified": bool }
            }
            OR
            {
                "success": False,
                "error": str  # Reason, e.g. phone number not found
            }

        Constraints:
            - phone_number must exist in the system (self.phone_numbers).
        """
        _, phone_info = self._get_phone_record(phone_number)
        if phone_info is None:
            return { "success": False, "error": "Phone number not found" }

        return { "success": True, "data": { "is_verified": phone_info["is_verified"] } }

    def is_phone_unique(self, phone_number: str) -> dict:
        """
        Check if a phone number is not currently registered in the system.

        Args:
            phone_number (str): The phone number to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if phone number not registered, False if already present
            } or {
                "success": False,
                "error": str  # Description of why the check failed (e.g., invalid input)
            }

        Constraints:
            - Each phone_number must be unique across all business accounts.
        """
        if not isinstance(phone_number, str) or not phone_number.strip():
            return {"success": False, "error": "Invalid phone number input."}

        is_unique = self._find_phone_storage_key(phone_number.strip()) is None
        return {"success": True, "data": is_unique}

    def is_email_valid(self, email: str) -> dict:
        """
        Verify whether a provided email address is a valid format.

        Args:
            email (str): The email address to check.

        Returns:
            dict:
            {
                "success": True,
                "data": bool  # True if email is valid format, False otherwise
            }

        Notes:
            - Only verifies the syntactic format of the email (not uniqueness or deliverability).
            - Always succeeds with a boolean result.
        """
        # Simple RFC 5322 compliant regex for email validation (not exhaustive, practical use)
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        is_valid = bool(re.match(email_regex, email.strip()))
        return { "success": True, "data": is_valid }

    def is_website_valid(self, website_url: str) -> dict:
        """
        Checks if the provided website URL is a valid format.

        Args:
            website_url (str): URL to validate.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if valid, False otherwise
                }

        Constraints:
            - Website must have a valid URL format. (Simple check: starts with http:// or https:// and contains a dot in the domain)
        """
        if not isinstance(website_url, str) or website_url.strip() == "":
            return { "success": True, "data": False }

        url = website_url.strip()
        # Basic check for http/https and a "." domain after scheme
        if url.startswith("http://") or url.startswith("https://"):
            after_scheme = url.split("://", 1)[1]
            if "." in after_scheme and len(after_scheme.split(".")) >= 2:
                # There is at least one dot after the scheme (like domain.com)
                return { "success": True, "data": True }
        return { "success": True, "data": False }

    def register_business_account(
        self,
        business_id: str,
        business_name: str,
        profile_description: str,
        contact_email: str,
        contact_website: str,
        registration_status: str,
        account_status: str
    ) -> dict:
        """
        Add a new business account with complete profile and contact info.

        Args:
            business_id (str): Unique business account identifier.
            business_name (str): Name of the business.
            profile_description (str): Profile description.
            contact_email (str): Contact email (must be valid if provided).
            contact_website (str): Contact website (must be valid if provided).
            registration_status (str): Registration status value.
            account_status (str): Account status value.

        Returns:
            dict: {
                "success": True,
                "message": "Business account registered successfully."
            }
            or
            {
                "success": False,
                "error": reason
            }

        Constraints:
            - business_id must be unique.
            - contact_email, if provided, must be in valid format.
            - contact_website, if provided, must be in valid format.
        """

        # Check for unique business_id
        if business_id in self.business_accounts:
            return { "success": False, "error": "business_id already exists" }

        # Email format validation
        if contact_email:
            result = self.is_email_valid(contact_email)
            if not (isinstance(result, dict) and result.get("success") and result.get("data", False)):
                return { "success": False, "error": "Invalid contact_email format" }

        # Website format validation
        if contact_website:
            result = self.is_website_valid(contact_website)
            if not (isinstance(result, dict) and result.get("success") and result.get("data", False)):
                return { "success": False, "error": "Invalid contact_website format" }

        # Register new business account
        new_account = {
            "business_id": business_id,
            "business_name": business_name,
            "profile_description": profile_description,
            "contact_email": contact_email,
            "contact_website": contact_website,
            "registration_status": registration_status,
            "account_status": account_status
        }
        self.business_accounts[business_id] = new_account

        return { "success": True, "message": "Business account registered successfully." }

    def update_business_account(self, business_id: str, updates: dict) -> dict:
        """
        Update an existing business account's profile or contact fields.

        Args:
            business_id (str): The ID of the business account to update.
            updates (dict): Dictionary of fields (from: business_name, profile_description, contact_email, contact_website,
                            registration_status, account_status) and their new values.

        Returns:
            dict: 
                On success: { "success": True, "message": "Updated fields: ..." }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - business_id must exist in the business_accounts.
            - Fields being updated must be valid/allowed.
            - contact_email/contact_website must be valid format if provided.
            - business_id is immutable.
            - At least one valid field must be updated.
        """
        # Allowed fields to update (business_id is immutable)
        allowed_fields = {
            "business_name", "profile_description",
            "contact_email", "contact_website",
            "registration_status", "account_status"
        }

        if business_id not in self.business_accounts:
            return {"success": False, "error": "Business account not found"}

        if not updates or not isinstance(updates, dict):
            return {"success": False, "error": "No update data provided"}

        # Check fields
        invalid_fields = [field for field in updates if field not in allowed_fields]
        if invalid_fields:
            return {"success": False, "error": f"Invalid field(s) in update: {', '.join(invalid_fields)}"}
    
        # Validate contact_email if present
        if "contact_email" in updates:
            email = updates["contact_email"]
            valid_email_res = self.is_email_valid(email)
            if not valid_email_res.get("success", False) or not valid_email_res.get("data", False):
                return {"success": False, "error": "Invalid email format"}
    
        # Validate contact_website if present
        if "contact_website" in updates:
            website = updates["contact_website"]
            valid_website_res = self.is_website_valid(website)
            if not valid_website_res.get("success", False) or not valid_website_res.get("data", False):
                return {"success": False, "error": "Invalid website format"}

        # Perform update
        account = self.business_accounts[business_id]
        updated_fields = []
        for key, value in updates.items():
            if account.get(key) != value:
                account[key] = value
                updated_fields.append(key)
        if not updated_fields:
            return {"success": False, "error": "No fields updated (all values identical to current)"}
        self.business_accounts[business_id] = account  # Update dict (helpful for clarity)

        return {
            "success": True,
            "message": f"Updated fields: {', '.join(updated_fields)}"
        }

    def delete_business_account(self, business_id: str) -> dict:
        """
        Remove a business account with the given business_id and all its associated phone number mappings.

        Args:
            business_id (str): The ID of the business account to remove.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Business account and associated phone mappings removed."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Business account does not exist."
                    }

        Constraints:
            - The business account must exist.
            - All phone numbers mapped to this business must also be removed from the system.
        """
        if business_id not in self.business_accounts:
            return { "success": False, "error": "Business account does not exist." }

        # Remove associated phone numbers
        to_delete = [phone for phone, info in self.phone_numbers.items()
                     if info["business_id"] == business_id]
        for phone in to_delete:
            del self.phone_numbers[phone]

        # Remove the business account
        del self.business_accounts[business_id]

        return {
            "success": True,
            "message": "Business account and associated phone mappings removed."
        }

    def add_phone_number(self, business_id: str, phone_number: str) -> dict:
        """
        Associate a new, unique phone number with an existing business account.

        Args:
            business_id (str): Business account to associate the phone number with.
            phone_number (str): Phone number to add (must be globally unique).

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Phone number <number> successfully associated with business <business_id>." }
                - On error:
                    { "success": False, "error": <reason_str> }

        Constraints:
            - business_id must exist in the system.
            - phone_number must not already exist in the system (must be unique).
            - Phone verification status (is_verified) is set to False by default.
        """
        if business_id not in self.business_accounts:
            return { "success": False, "error": "Business account does not exist." }

        if self._find_phone_storage_key(phone_number) is not None:
            return { "success": False, "error": "Phone number already exists and must be unique." }

        # Add PhoneNumberInfo
        self.phone_numbers[phone_number] = {
            "phone_number": phone_number,
            "business_id": business_id,
            "is_verified": False
        }

        return {
            "success": True,
            "message": f"Phone number {phone_number} successfully associated with business {business_id}."
        }

    def verify_phone_number(self, phone_number: str) -> dict:
        """
        Mark a phone number as verified in the system.

        Args:
            phone_number (str): The phone number to verify.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number <number> marked as verified."
            }
            or
            {
                "success": False,
                "error": "Phone number does not exist."
            }

        Constraints:
            - The specified phone number must exist in the system.
            - Operation is idempotent: re-verifying an already verified phone is a success.
        """
        phone_key, phone_info = self._get_phone_record(phone_number)
        if phone_info is None:
            return { "success": False, "error": "Phone number does not exist." }
        if not phone_info["is_verified"]:
            # Mark as verified
            phone_info["is_verified"] = True
            self.phone_numbers[phone_key] = phone_info  # update mapping in case of copy
            return { "success": True, "message": f"Phone number {phone_number} marked as verified." }
        else:
            return { "success": True, "message": f"Phone number {phone_number} marked as verified." }

    def unverify_phone_number(self, phone_number: str) -> dict:
        """
        Mark the specified phone number as unverified.

        Args:
            phone_number (str): The phone number to be marked as unverified.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number marked as unverified."
            }
            or
            {
                "success": False,
                "error": "Phone number does not exist."
            }

        Constraints:
            - Phone number must exist in the system.
            - Operation is idempotent: already unverified numbers will still result in success.
        """
        phone_key, phone_info = self._get_phone_record(phone_number)
        if phone_info is None:
            return {
                "success": False,
                "error": "Phone number does not exist."
            }
        # Mark as unverified regardless of current state
        phone_info["is_verified"] = False
        # Update store
        self.phone_numbers[phone_key] = phone_info
        return {
            "success": True,
            "message": "Phone number marked as unverified."
        }

    def remove_phone_number(self, phone_number: str) -> dict:
        """
        Remove a phone number from the system.

        Args:
            phone_number (str): The phone number to be removed.

        Returns:
            dict: 
                On success: { "success": True, "message": "Phone number <phone_number> removed" }
                On error:   { "success": False, "error": "Phone number does not exist" }

        Constraints:
            - Phone number must exist in the system.
        """
        phone_key, _ = self._get_phone_record(phone_number)
        if phone_key is None:
            return { "success": False, "error": "Phone number does not exist" }

        del self.phone_numbers[phone_key]
        return { "success": True, "message": f"Phone number {phone_number} removed" }

    def update_phone_number(
        self, 
        phone_number: str, 
        business_id: str = None, 
        is_verified: bool = None
    ) -> dict:
        """
        Update a phone number record by possibly reassigning it to another business and/or changing its verification status.

        Args:
            phone_number (str): The phone number to update (must already exist).
            business_id (str, optional): If provided, reassign the phone number to this business_id. Must exist in business_accounts.
            is_verified (bool, optional): If provided, update the phone number's verification status.

        Returns:
            dict: 
              - On success: {"success": True, "message": "Phone number record updated"}
              - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - phone_number must exist in the system.
            - If business_id is provided, it must exist in business_accounts.
            - The operation does not change the phone_number value itself (uniqueness maintained).
        """
        # Check phone number exists
        phone_key, current_info = self._get_phone_record(phone_number)
        if current_info is None:
            return {"success": False, "error": "Phone number does not exist"}
        changed = False

        # Business reassignment
        if business_id is not None:
            if business_id not in self.business_accounts:
                return {"success": False, "error": "Target business_id does not exist"}
            if current_info["business_id"] != business_id:
                current_info["business_id"] = business_id
                changed = True

        # Verification status update
        if is_verified is not None:
            if current_info["is_verified"] != is_verified:
                current_info["is_verified"] = is_verified
                changed = True

        # Store back (dict refs are mutable, so this is usually not needed, but leave for completeness)
        self.phone_numbers[phone_key] = current_info

        return {
            "success": True,
            "message": "Phone number record updated" if changed else "No changes applied (fields were already as specified)"
        }

    def set_contact_email(self, business_id: str, contact_email: str) -> dict:
        """
        Update the contact email address for a business account.

        Args:
            business_id (str): The unique identifier of the business account.
            contact_email (str): The new contact email address to set.

        Returns:
            dict:
                On success: { "success": True, "message": "Email updated successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - business_id must exist in the system.
            - contact_email must be a valid email format.
        """
        # Check if business exists
        if business_id not in self.business_accounts:
            return { "success": False, "error": "Business ID not found" }

        # Basic email format validation
        email_pattern = r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[A-Za-z]{2,}$"
        if not re.match(email_pattern, contact_email):
            return { "success": False, "error": "Invalid email format" }

        # Update email
        self.business_accounts[business_id]["contact_email"] = contact_email
        return { "success": True, "message": "Email updated successfully" }

    def set_contact_website(self, business_id: str, new_website: str) -> dict:
        """
        Change/update the website for a business. Format is checked via is_website_valid.

        Args:
            business_id (str): The unique ID of the business account to update.
            new_website (str): The new website URL to set (may be empty string to clear).

        Returns:
            dict:
                {"success": True, "message": "Contact website updated successfully"}
                or
                {"success": False, "error": <reason>}
    
        Constraints:
            - business_id must exist in business_accounts.
            - new_website must be a valid website format if not empty.
        """

        # Check business exists
        if business_id not in self.business_accounts:
            return {"success": False, "error": "Business account does not exist"}

        # Validate the website format (empty string is allowed for clearing)
        if new_website:
            check = self.is_website_valid(new_website)
            if not (isinstance(check, dict) and check.get("success") and check.get("data", False)):
                return {"success": False, "error": "Invalid website format"}

        self.business_accounts[business_id]["contact_website"] = new_website
        return {"success": True, "message": "Contact website updated successfully"}


class MessagingBusinessAccountManagementSystem(BaseEnv):
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
        colliding_state_keys = {
            "is_email_valid": "_is_email_valid_state",
            "is_website_valid": "_is_website_valid_state",
        }
        for key, value in init_config.items():
            if key in colliding_state_keys:
                setattr(env, colliding_state_keys[key], copy.deepcopy(value))
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

    def get_business_by_id(self, **kwargs):
        return self._call_inner_tool('get_business_by_id', kwargs)

    def get_business_by_name(self, **kwargs):
        return self._call_inner_tool('get_business_by_name', kwargs)

    def get_business_by_phone_number(self, **kwargs):
        return self._call_inner_tool('get_business_by_phone_number', kwargs)

    def get_phone_info(self, **kwargs):
        return self._call_inner_tool('get_phone_info', kwargs)

    def list_phones_by_business(self, **kwargs):
        return self._call_inner_tool('list_phones_by_business', kwargs)

    def is_phone_verified(self, **kwargs):
        return self._call_inner_tool('is_phone_verified', kwargs)

    def is_phone_unique(self, **kwargs):
        return self._call_inner_tool('is_phone_unique', kwargs)

    def is_email_valid(self, **kwargs):
        return self._call_inner_tool('is_email_valid', kwargs)

    def is_website_valid(self, **kwargs):
        return self._call_inner_tool('is_website_valid', kwargs)

    def register_business_account(self, **kwargs):
        return self._call_inner_tool('register_business_account', kwargs)

    def update_business_account(self, **kwargs):
        return self._call_inner_tool('update_business_account', kwargs)

    def delete_business_account(self, **kwargs):
        return self._call_inner_tool('delete_business_account', kwargs)

    def add_phone_number(self, **kwargs):
        return self._call_inner_tool('add_phone_number', kwargs)

    def verify_phone_number(self, **kwargs):
        return self._call_inner_tool('verify_phone_number', kwargs)

    def unverify_phone_number(self, **kwargs):
        return self._call_inner_tool('unverify_phone_number', kwargs)

    def remove_phone_number(self, **kwargs):
        return self._call_inner_tool('remove_phone_number', kwargs)

    def update_phone_number(self, **kwargs):
        return self._call_inner_tool('update_phone_number', kwargs)

    def set_contact_email(self, **kwargs):
        return self._call_inner_tool('set_contact_email', kwargs)

    def set_contact_website(self, **kwargs):
        return self._call_inner_tool('set_contact_website', kwargs)
