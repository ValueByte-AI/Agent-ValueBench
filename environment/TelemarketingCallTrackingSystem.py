# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class AccountInfo(TypedDict):
    account_id: str
    account_name: str
    contact_info: str
    status: str

class PhoneNumberInfo(TypedDict):
    phone_number: str
    account_id: str
    campaign_id: str
    status: str

class CampaignInfo(TypedDict):
    campaign_id: str
    account_id: str
    name: str
    active_period: str
    status: str

class CallInfo(TypedDict):
    call_id: str
    phone_number: str
    campaign_id: str
    account_id: str
    timestamp: str
    duration: float
    caller_id: str
    call_status: str
    recording_url: str
    outcome: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Telemarketing Call Tracking System environment.
        """

        # Accounts: account_id → AccountInfo
        self.accounts: Dict[str, AccountInfo] = {}

        # Phone Numbers: phone_number → PhoneNumberInfo
        self.phone_numbers: Dict[str, PhoneNumberInfo] = {}

        # Campaigns: campaign_id → CampaignInfo
        self.campaigns: Dict[str, CampaignInfo] = {}

        # Calls: call_id → CallInfo (append-only)
        self.calls: Dict[str, CallInfo] = {}

        # Constraints:
        # - Each phone number must be uniquely assigned to a single account at any time.
        # - Calls must be uniquely associated with a valid phone number and account.
        # - Only active (non-archived) accounts and campaigns can have performance analyzed or new calls logged.
        # - Call logs cannot be modified, only appended.

    def get_call_by_id(self, call_id: str) -> dict:
        """
        Retrieve complete details for a call given its `call_id`.

        Args:
            call_id (str): The unique identifier for the call.

        Returns:
            dict: 
            {
                "success": True,
                "data": CallInfo  # Call info dictionary
            }
            or
            {
                "success": False,
                "error": str  # If the call_id is not found
            }

        Constraints:
            - No modifications, read-only operation.
            - No account/campaign status or permission restrictions for querying.
        """
        call_info = self.calls.get(call_id)
        if call_info is None:
            return { "success": False, "error": "Call ID not found" }
        return { "success": True, "data": call_info }

    def list_phone_numbers_by_account(self, account_id: str) -> dict:
        """
        Retrieve all phone numbers (with metadata) assigned to the specified account.

        Args:
            account_id (str): The ID of the account.

        Returns:
            dict: {
                "success": True,
                "data": List[PhoneNumberInfo],  # Phones assigned (can be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. "Account does not exist"
            }

        Constraints:
            - The account_id must exist in the system.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        result = [
            phone_info for phone_info in self.phone_numbers.values()
            if phone_info["account_id"] == account_id
        ]

        return { "success": True, "data": result }

    def list_recent_calls_by_account(self, account_id: str) -> dict:
        """
        Retrieve a list of all calls for a specified account, sorted by most recent (timestamp descending).
    
        Args:
            account_id (str): The identifier of the account.
    
        Returns:
            dict: {
                "success": True,
                "data": List[CallInfo],   # List of CallInfo dicts sorted most recent first.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., Account does not exist)
            }
    
        Constraints:
            - The specified account must exist.
            - Calls are simply listed; archived/active status does not affect result.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist"}
    
        # Gather calls belonging to the given account
        account_calls = [
            call for call in self.calls.values()
            if call["account_id"] == account_id
        ]

        # Sort by timestamp descending; assume ISO8601 or sortable string, else try float
        try:
            account_calls.sort(key=lambda call: call["timestamp"], reverse=True)
        except Exception:
            # Fallback: sort using float cast if possible
            try:
                account_calls.sort(key=lambda call: float(call["timestamp"]), reverse=True)
            except Exception:
                # Leave unsorted if unknown format
                pass

        return {"success": True, "data": account_calls}

    def get_account_info(self, account_id: str) -> dict:
        """
        Retrieve details for a specific account by its account_id.

        Args:
            account_id (str): The unique identifier of the account.

        Returns:
            dict: {
                "success": True,
                "data": AccountInfo  # The account's information if found
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., account not found
            }

        Constraints:
            - The account must exist in the system.
            - All account statuses (including archived/inactive) can be queried.
        """
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account not found" }
        return { "success": True, "data": account }

    def list_campaigns_by_account(self, account_id: str) -> dict:
        """
        List all campaigns associated with a particular account.

        Args:
            account_id (str): The account identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # (possibly empty if no campaigns)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - account_id must exist in the system.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account not found"}

        campaigns = [
            campaign_info for campaign_info in self.campaigns.values()
            if campaign_info["account_id"] == account_id
        ]

        return {"success": True, "data": campaigns}

    def get_campaign_info(self, campaign_id: str) -> dict:
        """
        Retrieve full campaign details for a given campaign_id.

        Args:
            campaign_id (str): The unique identifier of the campaign.

        Returns:
            dict: {
                "success": True,
                "data": CampaignInfo  # The campaign information, if found.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., campaign not found).
            }

        Constraints:
            - No status restriction; any campaign_id is queryable.
        """
        campaign = self.campaigns.get(campaign_id)
        if campaign is None:
            return { "success": False, "error": "Campaign not found" }
        return { "success": True, "data": campaign }

    def list_calls_by_campaign(self, campaign_id: str) -> dict:
        """
        List all calls associated with a specified campaign.

        Args:
            campaign_id (str): The campaign ID to fetch calls for.

        Returns:
            dict: 
                - On success: {"success": True, "data": List[CallInfo]} (possibly empty if no calls)
                - On failure: {"success": False, "error": str}

        Constraints:
            - The campaign_id must exist in the system.
            - Does not require campaign to be active (read-only history operation).
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign does not exist"}

        calls = [
            call_info for call_info in self.calls.values()
            if call_info["campaign_id"] == campaign_id
        ]

        return {"success": True, "data": calls}

    def list_calls_by_phone_number(self, phone_number: str) -> dict:
        """
        List all calls associated with a particular phone number.

        Args:
            phone_number (str): The phone number for which to retrieve call logs.

        Returns:
            dict: {
                "success": True,
                "data": List[CallInfo],  # List of call logs for the phone number (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Phone number does not exist"
            }

        Constraints:
            - The given phone number must exist in the system for calls to be listed.
        """
        if phone_number not in self.phone_numbers:
            return { "success": False, "error": "Phone number does not exist" }

        calls = [
            call_info for call_info in self.calls.values()
            if call_info["phone_number"] == phone_number
        ]
        return { "success": True, "data": calls }

    def get_phone_number_info(self, phone_number: str) -> dict:
        """
        Retrieve status and assignment details for a given phone number.

        Args:
            phone_number (str): The phone number to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PhoneNumberInfo   # Assignment details for the phone number
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason why retrieval failed (e.g., not found)
                    }

        Constraints:
            - The phone number must exist in the system records.
            - No modifications are performed (read-only).
        """
        info = self.phone_numbers.get(phone_number)
        if not info:
            return {"success": False, "error": "Phone number not found"}
        return {"success": True, "data": info}

    def list_active_accounts(self) -> dict:
        """
        List all accounts that are currently active (status == 'active').

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": List[AccountInfo],  # List may be empty if no active accounts
                  }
        """
        active_accounts = [
            account_info
            for account_info in self.accounts.values()
            if account_info.get("status") == "active"
        ]
        return {"success": True, "data": active_accounts}

    def list_active_campaigns(self) -> dict:
        """
        List all campaigns that are currently active (not archived).

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[CampaignInfo],  # All campaigns whose status != 'archived'.
                }
        Notes:
            - Returns an empty list if no campaigns or no active campaigns exist.
        """
        active_campaigns = [
            campaign_info
            for campaign_info in self.campaigns.values()
            if campaign_info.get("status", "").lower() != "archived"
        ]
        return { "success": True, "data": active_campaigns }

    def get_call_performance_metrics(
        self,
        account_id: str = None,
        campaign_id: str = None,
        phone_number: str = None
    ) -> dict:
        """
        Provide call performance analytics (total calls, success rate, average duration) filtered by account, campaign, and/or phone number.

        Inputs:
            account_id (str, optional): ID of the account to analyze. Must exist and be active if used.
            campaign_id (str, optional): ID of the campaign to analyze. Must exist and be active if used.
            phone_number (str, optional): Phone number to analyze. Must exist if used.

        Returns:
            dict: 
                On success:
                    {
                      "success": True,
                      "data": {
                          "filter": {key: value},
                          "total_calls": int,
                          "successful_calls": int,
                          "success_rate": float,        # 0.0 if no calls
                          "average_duration": float,    # In seconds, 0.0 if no calls
                      }
                    }
                On failure:
                    { "success": False, "error": str }
    
        Constraints:
            - At least one non-empty filter (account_id, campaign_id, or phone_number) must be provided.
            - If filtering by account_id or campaign_id, entity must exist and be active.
            - If filtering by phone_number, must exist in system.
            - If multiple filters are provided, only calls matching all provided filters are included.
            - If a call has an outcome value, only outcome=="success" counts as successful.
            - If a call has no outcome value, call_status=="completed" counts as successful.
        """

        def _normalize_filter(value: str):
            if isinstance(value, str):
                value = value.strip()
                return value or None
            return value

        normalized_account_id = _normalize_filter(account_id)
        normalized_campaign_id = _normalize_filter(campaign_id)
        normalized_phone_number = _normalize_filter(phone_number)

        filter_info = {}

        if normalized_account_id is not None:
            account = self.accounts.get(normalized_account_id)
            if not account:
                return { "success": False, "error": "Account not found" }
            if account.get("status", "").lower() != "active":
                return { "success": False, "error": "Account is not active" }
            filter_info["account_id"] = normalized_account_id

        if normalized_campaign_id is not None:
            campaign = self.campaigns.get(normalized_campaign_id)
            if not campaign:
                return { "success": False, "error": "Campaign not found" }
            if campaign.get("status", "").lower() != "active":
                return { "success": False, "error": "Campaign is not active" }
            filter_info["campaign_id"] = normalized_campaign_id

        if normalized_phone_number is not None:
            number_info = self.phone_numbers.get(normalized_phone_number)
            if not number_info:
                return { "success": False, "error": "Phone number not found" }
            filter_info["phone_number"] = normalized_phone_number

        if not filter_info:
            return { "success": False, "error": "At least one filter (account_id, campaign_id, phone_number) must be provided" }

        calls = [
            call for call in self.calls.values()
            if all(call.get(key) == value for key, value in filter_info.items())
        ]
    
        total_calls = len(calls)
        if total_calls == 0:
            return {
                "success": True,
                "data": {
                    "filter": filter_info,
                    "total_calls": 0,
                    "successful_calls": 0,
                    "success_rate": 0.0,
                    "average_duration": 0.0
                }
            }
    
        def _is_successful(call: Dict[str, Any]) -> bool:
            outcome = call.get("outcome")
            if isinstance(outcome, str) and outcome.strip():
                return outcome.strip().lower() in {"success", "successful"}
            return call.get("call_status", "").lower() == "completed"

        successful_calls = [c for c in calls if _is_successful(c)]
        num_successful = len(successful_calls)
        total_duration = sum(float(c.get("duration", 0)) for c in calls)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0.0
        success_rate = num_successful / total_calls if total_calls > 0 else 0.0

        return {
            "success": True,
            "data": {
                "filter": filter_info,
                "total_calls": total_calls,
                "successful_calls": num_successful,
                "success_rate": round(success_rate, 3),
                "average_duration": round(avg_duration, 2),
            }
        }

    def add_call_log(
        self,
        call_id: str,
        phone_number: str,
        campaign_id: str,
        account_id: str,
        timestamp: str,
        duration: float,
        caller_id: str,
        call_status: str,
        recording_url: str,
        outcome: str
    ) -> dict:
        """
        Append a new call record to the call log (append-only).
    
        Args:
            call_id (str): Unique identifier for the call.
            phone_number (str): The phone number used for the call.
            campaign_id (str): The campaign this call belongs to.
            account_id (str): The account associated with this call.
            timestamp (str): When the call occurred.
            duration (float): Duration of call in seconds.
            caller_id (str): Originating caller ID.
            call_status (str): Status of the call (answered, missed, etc.).
            recording_url (str): URL to the call recording.
            outcome (str): Outcome of the call.

        Returns:
            dict: 
                {"success": True, "message": "Call log added for call_id <call_id>"}
                or
                {"success": False, "error": <reason>}
    
        Constraints:
            - `call_id` must be unique in the call log.
            - `phone_number` must exist and be assigned to the account and campaign.
            - Both account and campaign must exist and be 'active'.
            - Log is strictly append-only (no overwrites).
        """
        # Check for uniqueness of call_id
        if call_id in self.calls:
            return {"success": False, "error": "Call ID already exists"}

        # Validate phone number
        pni = self.phone_numbers.get(phone_number)
        if not pni:
            return {"success": False, "error": "Phone number does not exist"}

        # Validate account and campaign assignment for the phone number
        if pni["account_id"] != account_id:
            return {"success": False, "error": "Phone number not assigned to provided account"}
        if pni["campaign_id"] != campaign_id:
            return {"success": False, "error": "Phone number not assigned to provided campaign"}

        # Validate account
        acct = self.accounts.get(account_id)
        if not acct:
            return {"success": False, "error": "Account does not exist"}
        if acct["status"] != "active":
            return {"success": False, "error": "Account is not active"}

        # Validate campaign
        camp = self.campaigns.get(campaign_id)
        if not camp:
            return {"success": False, "error": "Campaign does not exist"}
        if camp["status"] != "active":
            return {"success": False, "error": "Campaign is not active"}

        # Construct the call info record
        call_info: CallInfo = {
            "call_id": call_id,
            "phone_number": phone_number,
            "campaign_id": campaign_id,
            "account_id": account_id,
            "timestamp": timestamp,
            "duration": duration,
            "caller_id": caller_id,
            "call_status": call_status,
            "recording_url": recording_url,
            "outcome": outcome
        }

        # Append (insert) to calls log
        self.calls[call_id] = call_info

        return {"success": True, "message": f"Call log added for call_id {call_id}"}

    def assign_phone_number_to_account(self, phone_number: str, account_id: str) -> dict:
        """
        Assign a phone number to a single account, ensuring uniqueness of assignment.

        Args:
            phone_number (str): The phone number to assign.
            account_id (str): The account ID to assign the phone number to.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Phone number X assigned to account Y" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Phone number must exist.
            - Account must exist and be active.
            - The phone number must not already be assigned to another account.
            - Successfully assigning an unassigned phone number activates it for operational use.
        """
        # Check phone number existence
        if phone_number not in self.phone_numbers:
            return { "success": False, "error": "Phone number does not exist" }

        # Check account existence
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        # Check account is active (assume 'active' status; update as per real statuses if needed)
        account = self.accounts[account_id]
        if account["status"].lower() != "active":
            return { "success": False, "error": "Account is not active" }

        # Check phone number current assignment
        current_info = self.phone_numbers[phone_number]
        current_account_id = current_info["account_id"]

        if current_account_id == account_id:
            return { "success": True, "message": f"Phone number {phone_number} is already assigned to account {account_id}" }

        if current_account_id and current_account_id != account_id:
            # Check if the previous account is still active; regardless, assignment must be unique at a time
            return { "success": False, "error": f"Phone number is already assigned to another account ({current_account_id})" }

        # Assign phone number and make it operational for downstream campaign use.
        self.phone_numbers[phone_number]["account_id"] = account_id
        self.phone_numbers[phone_number]["status"] = "active"

        return { "success": True, "message": f"Phone number {phone_number} assigned to account {account_id}" }

    def assign_phone_number_to_campaign(self, phone_number: str, campaign_id: str) -> dict:
        """
        Assign a phone number to a campaign for tracking during the campaign's active period.

        Args:
            phone_number (str): The phone number to assign.
            campaign_id (str): The campaign ID to assign the phone number to.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number <phone_number> assigned to campaign <campaign_id>."
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - Both phone number and campaign must exist and be active (not archived).
            - Both must belong to the same account.
            - Assignment is idempotent if already assigned to this campaign.
        """
        pn = self.phone_numbers.get(phone_number)
        campaign = self.campaigns.get(campaign_id)

        if pn is None:
            return { "success": False, "error": f"Phone number {phone_number} does not exist." }
        if campaign is None:
            return { "success": False, "error": f"Campaign {campaign_id} does not exist." }
    
        if pn["status"] != "active":
            return { "success": False, "error": f"Phone number {phone_number} is not active." }
        if campaign["status"] != "active":
            return { "success": False, "error": f"Campaign {campaign_id} is not active." }

        if pn["account_id"] != campaign["account_id"]:
            return { "success": False, "error": "Phone number and campaign belong to different accounts." }

        # Idempotency: already assigned
        if pn["campaign_id"] == campaign_id:
            return {
                "success": True,
                "message": f"Phone number {phone_number} is already assigned to campaign {campaign_id}."
            }
    
        # Perform assignment
        pn["campaign_id"] = campaign_id
        self.phone_numbers[phone_number] = pn

        return {
            "success": True,
            "message": f"Phone number {phone_number} assigned to campaign {campaign_id}."
        }

    def change_account_status(self, account_id: str, new_status: str) -> dict:
        """
        Change the status of an account (e.g., activate, archive, suspend).

        Args:
            account_id (str): ID of the account to update.
            new_status (str): Status to set for the account (e.g., 'active', 'archived', 'suspended').

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Account status updated to <new_status>" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Account must exist.
            - Status is overwritten regardless of previous state.
        """
        account = self.accounts.get(account_id)
        if account is None:
            return { "success": False, "error": "Account does not exist" }
    
        account['status'] = new_status
        self.accounts[account_id] = account  # Not strictly needed since dict is mutable, but explicit

        return { "success": True, "message": f"Account status updated to {new_status}" }

    def change_campaign_status(self, campaign_id: str, new_status: str) -> dict:
        """
        Change the status of a campaign.

        Args:
            campaign_id (str): The unique identifier for the campaign to update.
            new_status (str): The new status to assign ('active', 'archived', 'suspended', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Status of campaign <campaign_id> changed to <new_status>."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., campaign not found)
            }

        Constraints:
            - Campaign must exist to be updated.
            - Allowed status values may be limited (if such limits are system-defined).
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": f"Campaign {campaign_id} does not exist."}

        # Optional: Validate new_status.
        allowed_statuses = {'active', 'archived', 'suspended'}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed statuses: {', '.join(allowed_statuses)}."}

        self.campaigns[campaign_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Status of campaign {campaign_id} changed to {new_status}."
        }

    def reassign_phone_number(self, phone_number: str, new_account_id: str) -> dict:
        """
        Move a phone number from one account to another (must be unassigned first).

        Args:
            phone_number (str): The phone number to reassign.
            new_account_id (str): The account ID to assign the phone number to.

        Returns:
            dict: {
                "success": True,
                "message": "Phone number {phone_number} assigned to account {new_account_id}"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The phone number must exist in the system.
            - The new account must exist and be active (status != "archived").
            - The phone number may be moved directly from its current account to the new active account.
            - Reassignment clears any existing campaign assignment on that number.
        """
        pn_info = self.phone_numbers.get(phone_number)
        if not pn_info:
            return {"success": False, "error": "Phone number does not exist"}

        new_account = self.accounts.get(new_account_id)
        if not new_account:
            return {"success": False, "error": "Target account does not exist"}

        if new_account.get("status", "").lower() == "archived":
            return {"success": False, "error": "Target account is archived and cannot be assigned phone numbers"}

        current_account_id = pn_info.get("account_id", "")
        if current_account_id == new_account_id:
            return {
                "success": True,
                "message": f"Phone number {phone_number} assigned to account {new_account_id}"
            }

        # Perform reassignment
        pn_info["account_id"] = new_account_id
        pn_info["campaign_id"] = ""
        pn_info["status"] = "active"

        self.phone_numbers[phone_number] = pn_info

        return {
            "success": True,
            "message": f"Phone number {phone_number} assigned to account {new_account_id}"
        }

    def archive_call_log(self, call_ids: list[str]) -> dict:
        """
        Mark calls as archived for non-active records - for data retention, not log modification. 
    
        Args:
            call_ids (List[str]): List of call_id strings to consider for archiving.
        Returns:
            dict: 
              - success (bool): True if operation is processed (even partially)
              - message (str): How many calls were archived
              - Optionally, details of skipped call_ids (not found, related active account/campaign).
        Constraints:
            - No changes are made to call log data ("append-only"); archiving is tracked via a separate set.
            - Only calls associated with inactive (non-active/archived) accounts OR campaigns are eligible for archiving.
            - Nonexistent calls or those already archived are skipped.
        """
        # Initialize archived_calls tracking set if not present.
        if not hasattr(self, "archived_calls"):
            self.archived_calls = set()

        if not call_ids or not isinstance(call_ids, list):
            return { "success": False, "error": "Input must be a non-empty list of call_id strings." }

        archived_count = 0
        skipped_calls = []
        for cid in call_ids:
            if cid in self.archived_calls:
                skipped_calls.append((cid, "already archived"))
                continue
            call = self.calls.get(cid)
            if not call:
                skipped_calls.append((cid, "call not found"))
                continue
            # Check account and campaign status
            account_info = self.accounts.get(call["account_id"])
            campaign_info = self.campaigns.get(call["campaign_id"])
            if not account_info or not campaign_info:
                skipped_calls.append((cid, "related account or campaign missing"))
                continue
            if account_info["status"] == "active" and campaign_info["status"] == "active":
                skipped_calls.append((cid, "account and campaign are both active"))
                continue
            # Archive call (append to set)
            self.archived_calls.add(cid)
            archived_count += 1

        msg = f"{archived_count} call(s) marked as archived."
        if skipped_calls:
            msg += f" Skipped: {', '.join([f'{c}[{r}]' for c,r in skipped_calls])}"

        return { "success": True, "message": msg }


class TelemarketingCallTrackingSystem(BaseEnv):
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
            if key == "phone_numbers" and isinstance(value, dict):
                normalized_phone_numbers = {}
                for fallback_key, info in value.items():
                    if isinstance(info, dict):
                        actual_phone_number = info.get("phone_number") or fallback_key
                        normalized_info = copy.deepcopy(info)
                        normalized_info["phone_number"] = actual_phone_number
                        normalized_phone_numbers[actual_phone_number] = normalized_info
                    else:
                        normalized_phone_numbers[fallback_key] = copy.deepcopy(info)
                setattr(env, key, normalized_phone_numbers)
                continue
            if key == "archived_calls":
                normalized_archived_calls = set()
                if isinstance(value, str):
                    stripped = value.strip()
                    if stripped:
                        try:
                            parsed = json.loads(stripped)
                            if isinstance(parsed, list):
                                normalized_archived_calls = {
                                    item for item in parsed if isinstance(item, str) and item
                                }
                            else:
                                normalized_archived_calls = {
                                    token.strip()
                                    for token in stripped.split(",")
                                    if token.strip()
                                }
                        except Exception:
                            normalized_archived_calls = {
                                token.strip()
                                for token in stripped.split(",")
                                if token.strip()
                            }
                elif isinstance(value, (list, tuple, set)):
                    normalized_archived_calls = {
                        item for item in value if isinstance(item, str) and item
                    }
                setattr(env, key, normalized_archived_calls)
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

    def get_call_by_id(self, **kwargs):
        return self._call_inner_tool('get_call_by_id', kwargs)

    def list_phone_numbers_by_account(self, **kwargs):
        return self._call_inner_tool('list_phone_numbers_by_account', kwargs)

    def list_recent_calls_by_account(self, **kwargs):
        return self._call_inner_tool('list_recent_calls_by_account', kwargs)

    def get_account_info(self, **kwargs):
        return self._call_inner_tool('get_account_info', kwargs)

    def list_campaigns_by_account(self, **kwargs):
        return self._call_inner_tool('list_campaigns_by_account', kwargs)

    def get_campaign_info(self, **kwargs):
        return self._call_inner_tool('get_campaign_info', kwargs)

    def list_calls_by_campaign(self, **kwargs):
        return self._call_inner_tool('list_calls_by_campaign', kwargs)

    def list_calls_by_phone_number(self, **kwargs):
        return self._call_inner_tool('list_calls_by_phone_number', kwargs)

    def get_phone_number_info(self, **kwargs):
        return self._call_inner_tool('get_phone_number_info', kwargs)

    def list_active_accounts(self, **kwargs):
        return self._call_inner_tool('list_active_accounts', kwargs)

    def list_active_campaigns(self, **kwargs):
        return self._call_inner_tool('list_active_campaigns', kwargs)

    def get_call_performance_metrics(self, **kwargs):
        return self._call_inner_tool('get_call_performance_metrics', kwargs)

    def add_call_log(self, **kwargs):
        return self._call_inner_tool('add_call_log', kwargs)

    def assign_phone_number_to_account(self, **kwargs):
        return self._call_inner_tool('assign_phone_number_to_account', kwargs)

    def assign_phone_number_to_campaign(self, **kwargs):
        return self._call_inner_tool('assign_phone_number_to_campaign', kwargs)

    def change_account_status(self, **kwargs):
        return self._call_inner_tool('change_account_status', kwargs)

    def change_campaign_status(self, **kwargs):
        return self._call_inner_tool('change_campaign_status', kwargs)

    def reassign_phone_number(self, **kwargs):
        return self._call_inner_tool('reassign_phone_number', kwargs)

    def archive_call_log(self, **kwargs):
        return self._call_inner_tool('archive_call_log', kwargs)
