# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict
import uuid
from datetime import datetime, timezone
from typing import List, Dict
from datetime import datetime



class AccountInfo(TypedDict):
    account_id: str
    organization_name: str
    contact_info: str
    credit_balance: int
    account_status: str  # (active, suspended, etc.)

class BatchJobInfo(TypedDict):
    job_id: str
    account_id: str
    submitted_at: str  # timestamp (ISO format)
    status: str  # (pending, processing, completed, failed)
    total_emails: int
    processed_count: int
    result_location: str  # URL or file/path

class EmailVerificationRecordInfo(TypedDict):
    verification_id: str
    job_id: Optional[str]  # nullable: can be None for single verifications
    account_id: str
    email_address: str
    status: str  # (pending, processing, completed, failed)
    result: str  # e.g., "valid", "invalid", "catch-all"
    requested_at: str  # timestamp (ISO format)
    completed_at: Optional[str]  # timestamp (ISO format), or None if not completed

class _GeneratedEnvImpl:
    """
    Email Verification Platform State

    Constraints:
    - An account must have sufficient credits to submit verification requests (batch or single).
    - A batch job’s processed_count cannot exceed total_emails.
    - Email verification records must correspond to a valid account and, if part of a batch, to an existing batch job.
    - Credits are decremented when a verification is requested (and not refunded unless the request fails per platform policy).
    - Email verification status transitions from "pending" to "processing" to "completed" or "failed".
    """

    def __init__(self):
        # Accounts: {account_id: AccountInfo}
        self.accounts: Dict[str, AccountInfo] = {}

        # Batch jobs: {job_id: BatchJobInfo}
        self.batch_jobs: Dict[str, BatchJobInfo] = {}

        # Email verification records: {verification_id: EmailVerificationRecordInfo}
        self.verification_records: Dict[str, EmailVerificationRecordInfo] = {}

    def get_account_info(self, account_id: str) -> dict:
        """
        Retrieve general information of an account, including status and organization details.

        Args:
            account_id (str): ID of the account to be queried.

        Returns:
            dict:
                - success: True, data: AccountInfo dict (on found)
                - success: False, error: reason (if not found)

        Constraints:
            - The account must exist.
        """
        account_info = self.accounts.get(account_id)
        if not account_info:
            return {"success": False, "error": "Account not found"}
        return {"success": True, "data": account_info}

    def get_account_credit_balance(self, account_id: str) -> dict:
        """
        Query the available credit balance for a given account.

        Args:
            account_id (str): The unique identifier for the account.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "account_id": str,
                    "credit_balance": int
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Account not found"
            }

        Constraints:
            - The specified account must exist.
        """
        account = self.accounts.get(account_id)
        if account is None:
            return { "success": False, "error": "Account not found" }
    
        return {
            "success": True,
            "data": {
                "account_id": account_id,
                "credit_balance": account["credit_balance"]
            }
        }

    def get_batch_job_status(self, job_id: str) -> dict:
        """
        Retrieve the current status and details of a batch verification job by job_id.

        Args:
            job_id (str): The unique identifier of the batch verification job.

        Returns:
            dict: {
                "success": True,
                "data": BatchJobInfo  # Batch job details if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if job ID does not exist
            }
        """
        job = self.batch_jobs.get(job_id)
        if not job:
            return { "success": False, "error": "Batch job ID does not exist." }
        return { "success": True, "data": job }

    def get_verification_record_status(self, verification_id: str) -> dict:
        """
        Retrieve the status and result of a specific email verification record.

        Args:
            verification_id (str): The unique verification record identifier.

        Returns:
            dict: 
              - If successful:
                  {
                    "success": True,
                    "data": {
                      "verification_id": str,
                      "status": str,
                      "result": str
                    }
                  }
              - If not found:
                  { "success": False, "error": "Verification record not found" }

        Constraints:
            - verification_id must exist in platform records.
        """
        record = self.verification_records.get(verification_id)
        if not record:
            return { "success": False, "error": "Verification record not found" }
        return {
            "success": True,
            "data": {
                "verification_id": record["verification_id"],
                "status": record["status"],
                "result": record["result"]
            }
        }

    def get_batch_job_verification_records(self, job_id: str) -> dict:
        """
        List all email verification records (as EmailVerificationRecordInfo) associated with a given batch job.

        Args:
            job_id (str): The unique identifier of the batch job.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[EmailVerificationRecordInfo],  # may be empty if no records
                }
                or
                {
                    "success": False,
                    "error": str  # Reason job_id not found
                }

        Constraints:
            - job_id must refer to an existing batch job.
            - Only records whose job_id field == job_id are returned.
        """
        if not isinstance(job_id, str) or job_id not in self.batch_jobs:
            return {"success": False, "error": "Batch job not found."}

        records = [
            record for record in self.verification_records.values()
            if record.get("job_id") == job_id
        ]
        return {"success": True, "data": records}

    def list_account_batch_jobs(self, account_id: str) -> dict:
        """
        Retrieve all batch jobs submitted by a specific account.

        Args:
            account_id (str): The ID of the account.

        Returns:
            dict: {
                "success": True,
                "data": List[BatchJobInfo]  # List of batch job info dicts (may be empty).
            }
            or
            {
                "success": False,
                "error": str  # If the account does not exist.
            }

        Constraints:
            - Provided account_id must exist in the platform.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }

        jobs = [
            job_info for job_info in self.batch_jobs.values()
            if job_info["account_id"] == account_id
        ]

        return { "success": True, "data": jobs }

    def get_account_verification_history(self, account_id: str) -> dict:
        """
        Retrieve the history (list and statuses) of all email verifications for a given account.

        Args:
            account_id (str): The account identifier.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[EmailVerificationRecordInfo]
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - account_id must exist in the platform.
            - Only records where email_verification.account_id == account_id are returned.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account does not exist" }
    
        result = [
            record for record in self.verification_records.values()
            if record["account_id"] == account_id
        ]
    
        return { "success": True, "data": result }

    def list_accounts(self) -> dict:
        """
        Return all registered accounts on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AccountInfo],  # List of all accounts (may be empty)
            }

        Constraints:
            - None
        """
        account_list = list(self.accounts.values())
        return {"success": True, "data": account_list}

    def submit_single_email_verification(self, account_id: str, email_address: str) -> dict:
        """
        Start a single email verification request for an account.
        Decrements credits if sufficient, creates and returns a new verification record.

        Args:
            account_id (str): The ID of the account requesting verification.
            email_address (str): The email address to be verified.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Verification record created",
                        "verification_id": str
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - Account must exist and have status "active".
            - Account must have at least 1 credit.
            - Credits are decremented when a request is made.
            - The created EmailVerificationRecord will have:
                - unique verification_id
                - job_id=None
                - account_id, email_address set
                - status="pending"
                - result=""
                - requested_at=<now>
                - completed_at=None
        """

        # Check account exists
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist"}

        if account.get("account_status") != "active":
            return {"success": False, "error": "Account is not active"}

        # Check sufficient credits
        if account.get("credit_balance", 0) < 1:
            return {"success": False, "error": "Insufficient credits"}

        # All checks passed, decrement credits
        self.accounts[account_id]["credit_balance"] -= 1

        # Generate a unique verification_id
        while True:
            verification_id = str(uuid.uuid4())
            if verification_id not in self.verification_records:
                break

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        verification_record = {
            "verification_id": verification_id,
            "job_id": None,
            "account_id": account_id,
            "email_address": email_address,
            "status": "pending",
            "result": "",
            "requested_at": now_iso,
            "completed_at": None
        }

        self.verification_records[verification_id] = verification_record

        return {
            "success": True,
            "message": "Verification record created",
            "verification_id": verification_id
        }


    def submit_batch_email_verification(self, account_id: str, emails: List[str]) -> dict:
        """
        Start a batch email verification job for an account, decrementing credits and creating batch job plus associated verification records.
    
        Args:
            account_id (str): The ID of the account requesting the verification.
            emails (List[str]): List of email addresses to verify.
        Returns:
            dict: {
                "success": True,
                "job_id": str,
                "verification_record_ids": List[str],
                "message": str,
            }
            OR
            {
                "success": False,
                "error": str,
            }
        Constraints:
            - Account must exist and be active.
            - Sufficient credits must be available (len(emails) <= credit_balance).
            - Minimum one email required.
            - Credits are decremented by number of emails.
            - BatchJob and verification records refer to valid entities.
        """
        # Check for valid account
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist."}
        if str(account.get("account_status", "")).lower() != "active":
            return {"success": False, "error": "Account is not active."}
    
        # Validate emails
        if not emails or not isinstance(emails, list) or not all(isinstance(e, str) and e for e in emails):
            return {"success": False, "error": "Email list is empty or invalid."}
    
        num_emails = len(emails)
        if account["credit_balance"] < num_emails:
            return {"success": False, "error": "Insufficient credits."}
    
        # Decrement credits
        account["credit_balance"] -= num_emails
    
        # Create BatchJob
        job_id = str(uuid.uuid4())
        submitted_at = datetime.utcnow().isoformat() + "Z"
        batch_job = {
            "job_id": job_id,
            "account_id": account_id,
            "submitted_at": submitted_at,
            "status": "pending",
            "total_emails": num_emails,
            "processed_count": 0,
            "result_location": "",  # Placeholder, can be updated when results are ready
        }
        self.batch_jobs[job_id] = batch_job
    
        # Create verification records
        verification_record_ids = []
        for email in emails:
            verification_id = str(uuid.uuid4())
            record = {
                "verification_id": verification_id,
                "job_id": job_id,
                "account_id": account_id,
                "email_address": email,
                "status": "pending",
                "result": "",
                "requested_at": submitted_at,
                "completed_at": None,
            }
            self.verification_records[verification_id] = record
            verification_record_ids.append(verification_id)
    
        return {
            "success": True,
            "job_id": job_id,
            "verification_record_ids": verification_record_ids,
            "message": f"Batch job created with {num_emails} verification(s)."
        }

    def update_batch_job_status(self, job_id: str, new_status: str) -> dict:
        """
        Update the status of a batch job (e.g., from "pending" to "processing", or to "completed"/"failed").

        Args:
            job_id (str): The ID of the batch job to update.
            new_status (str): The target status (must be one of: "pending", "processing", "completed", "failed").

        Returns:
            dict: {
                "success": True,
                "message": "Batch job status updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
        - job_id must correspond to an existing batch job.
        - new_status must be a valid status value (pending, processing, completed, failed).
        - (Optional) Status transitions should respect platform's FSM. Minimal transition logic is enforced here matching constraints description.
        """
        valid_statuses = {"pending", "processing", "completed", "failed"}

        # Check batch job exists
        job = self.batch_jobs.get(job_id)
        if job is None:
            return {"success": False, "error": "Batch job not found."}

        # Check if new_status is valid
        if new_status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'."}

        current_status = job["status"]

        # Optional: FSM status transitions, restrict backward/illegal transitions
        legal_transitions = {
            "pending": {"processing", "failed"},
            "processing": {"completed", "failed"},
            "completed": set(),
            "failed": set(),
        }
        if new_status != current_status:
            allowed = legal_transitions.get(current_status, set())
            if new_status not in allowed:
                return {
                    "success": False,
                    "error": (
                        f"Cannot transition from '{current_status}' to '{new_status}'."
                    ),
                }

        # Update status
        job["status"] = new_status
        self.batch_jobs[job_id] = job  # Redundant if referencing original, for clarity

        return {"success": True, "message": "Batch job status updated."}

    def update_verification_record_status(
        self,
        verification_id: str,
        new_status: str,
        result: str = "",
        completed_at: str = ""
    ) -> dict:
        """
        Update the status and result of an email verification record. If new_status is 'failed',
        refunds credit to the associated account (per platform policy). Valid transitions:
        'pending' -> 'processing' -> 'completed'/'failed'. No revert from 'completed'/'failed'.

        Args:
            verification_id (str): The verification record to update.
            new_status (str): New status: 'processing', 'completed', or 'failed'.
            result (str, optional): Result of verification ('valid', 'invalid', etc.).
                                    Required for 'completed' or 'failed'.
            completed_at (str, optional): Completion timestamp (ISO format).
                                          Required for 'completed' or 'failed'.

        Returns:
            dict:
                - On success: {"success": True, "message": "Verification record updated."}
                - On failure: {"success": False, "error": "reason"}
        Constraints:
            - Status transitions must be forward, not to previous states.
            - If failed, refund one credit to the associated account (if not already refunded).
            - Verification record and account must exist.
            - result and completed_at must be provided for 'completed'/'failed' status.
        """
        # Valid statuses
        valid_statuses = ["pending", "processing", "completed", "failed"]

        # Check existence
        record = self.verification_records.get(verification_id)
        if not record:
            return {"success": False, "error": "Verification record does not exist."}

        if new_status not in valid_statuses[1:]:  # can't directly set to "pending"
            return {"success": False, "error": "Invalid new status."}

        old_status = record["status"]
        # Enforce legal status transitions
        allowed_transitions = {
            "pending": ["processing", "failed"],
            "processing": ["completed", "failed"],
        }
        if old_status in ["completed", "failed"]:
            return {"success": False, "error": "Cannot change status of a completed/failed record."}
        if new_status not in allowed_transitions.get(old_status, []):
            return {"success": False, "error": f"Invalid status transition from '{old_status}' to '{new_status}'."}

        # result and completed_at must be provided for completed/failed
        if new_status in ["completed", "failed"]:
            if not result or not completed_at:
                return {"success": False, "error": "Must provide result and completed_at for completed/failed status."}

        # Find and validate account
        account_id = record["account_id"]
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Associated account does not exist."}

        # --- Update fields ---
        record["status"] = new_status
        if new_status in ["completed", "failed"]:
            record["result"] = result
            record["completed_at"] = completed_at

        # --- Credit refund if "failed" ---
        if new_status == "failed":
            # Refund _one_ credit if policy applies (only refund once)
            # Check if already refunded (using a marker in the record)
            if not record.get("_credit_refunded"):  # pseudo-marker, only for internal state
                account["credit_balance"] += 1
                record["_credit_refunded"] = True  # Mark as refunded

        self.verification_records[verification_id] = record
        self.accounts[account_id] = account
        return {"success": True, "message": "Verification record updated."}

    def increment_batch_processed_count(self, job_id: str) -> dict:
        """
        Increment the processed_count for a batch job as verifications are completed.

        Args:
            job_id (str): The unique identifier of the batch job.

        Returns:
            dict: 
                - If successful: {
                      "success": True,
                      "message": "Processed count incremented for batch job <job_id>."
                  }
                - If failed: {
                      "success": False,
                      "error": <reason string>
                  }

        Constraints:
            - Batch job must exist.
            - processed_count cannot exceed total_emails.
        """
        job = self.batch_jobs.get(job_id)
        if not job:
            return {"success": False, "error": "Batch job does not exist"}

        if job["processed_count"] >= job["total_emails"]:
            return {
                "success": False, 
                "error": "Processed count cannot exceed total_emails for this batch job"
            }

        job["processed_count"] += 1
        return {
            "success": True,
            "message": f"Processed count incremented for batch job {job_id}."
        }

    def refund_credits_for_failed_verification(self, verification_id: str) -> dict:
        """
        Refund credits to an account if a verification request fails.
        Args:
            verification_id (str): The ID of the failed verification record.
        Returns:
            dict: {
                "success": True,
                "message": "Refunded 1 credit for failed verification."
            }
            or
            {
                "success": False,
                "error": "<description of failure>"
            }
        Constraints:
            - The verification record must exist.
            - The verification's status must be "failed".
            - The record must correspond to an existing account.
            - Credits are refunded (1 credit) only once per failed verification per policy.
        """
        vrec = self.verification_records.get(verification_id)
        if vrec is None:
            return {"success": False, "error": "Verification record not found."}
        if vrec["status"] != "failed":
            return {
                "success": False,
                "error": f"Verification status is not 'failed' (current: '{vrec['status']}'). Cannot refund."
            }

        # Prevent multiple refunds, including failures already refunded when the
        # record was transitioned to failed through update_verification_record_status.
        if vrec.get("_credit_refunded") or vrec.get("_refunded"):
            return {"success": False, "error": "Credits already refunded for this verification."}

        account_id = vrec["account_id"]
        account = self.accounts.get(account_id)
        if account is None:
            return {"success": False, "error": "Associated account not found."}

        # Refund 1 credit
        account["credit_balance"] += 1

        # Mark as refunded (in practice, such a field would be needed in a real system)
        vrec["_credit_refunded"] = True
        vrec["_refunded"] = True

        return {"success": True, "message": "Refunded 1 credit for failed verification."}

    def suspend_or_restore_account(self, account_id: str, action: str) -> dict:
        """
        Change the standing/status of an account: suspend or restore/reactivate.

        Args:
            account_id (str): The unique account identifier for the target account.
            action (str): "suspend" to suspend the account, "restore"/"reactivate" to make it active.

        Returns:
            dict:
                - On success: {"success": True, "message": "Account <account_id> suspended/restored."}
                - On failure: {"success": False, "error": "reason"}

        Constraints:
            - Account must exist.
            - 'suspend' is valid only if not already suspended.
            - 'restore'/'reactivate' is valid only if account is currently suspended.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": f"Account '{account_id}' does not exist."}

        valid_actions = {"suspend", "restore", "reactivate"}
        action_lower = action.lower()
        if action_lower not in valid_actions:
            return {"success": False, "error": f"Invalid action '{action}'. Must be one of: suspend, restore, reactivate."}

        account_status = self.accounts[account_id]["account_status"]

        if action_lower == "suspend":
            if account_status == "suspended":
                return {"success": False, "error": f"Account '{account_id}' is already suspended."}
            self.accounts[account_id]["account_status"] = "suspended"
            return {"success": True, "message": f"Account '{account_id}' suspended."}
        else:  # restore or reactivate
            if account_status == "active":
                return {"success": False, "error": f"Account '{account_id}' is already active."}
            self.accounts[account_id]["account_status"] = "active"
            return {"success": True, "message": f"Account '{account_id}' restored."}


class EmailVerificationPlatform(BaseEnv):
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

    def get_account_info(self, **kwargs):
        return self._call_inner_tool('get_account_info', kwargs)

    def get_account_credit_balance(self, **kwargs):
        return self._call_inner_tool('get_account_credit_balance', kwargs)

    def get_batch_job_status(self, **kwargs):
        return self._call_inner_tool('get_batch_job_status', kwargs)

    def get_verification_record_status(self, **kwargs):
        return self._call_inner_tool('get_verification_record_status', kwargs)

    def get_batch_job_verification_records(self, **kwargs):
        return self._call_inner_tool('get_batch_job_verification_records', kwargs)

    def list_account_batch_jobs(self, **kwargs):
        return self._call_inner_tool('list_account_batch_jobs', kwargs)

    def get_account_verification_history(self, **kwargs):
        return self._call_inner_tool('get_account_verification_history', kwargs)

    def list_accounts(self, **kwargs):
        return self._call_inner_tool('list_accounts', kwargs)

    def submit_single_email_verification(self, **kwargs):
        return self._call_inner_tool('submit_single_email_verification', kwargs)

    def submit_batch_email_verification(self, **kwargs):
        return self._call_inner_tool('submit_batch_email_verification', kwargs)

    def update_batch_job_status(self, **kwargs):
        return self._call_inner_tool('update_batch_job_status', kwargs)

    def update_verification_record_status(self, **kwargs):
        return self._call_inner_tool('update_verification_record_status', kwargs)

    def increment_batch_processed_count(self, **kwargs):
        return self._call_inner_tool('increment_batch_processed_count', kwargs)

    def refund_credits_for_failed_verification(self, **kwargs):
        return self._call_inner_tool('refund_credits_for_failed_verification', kwargs)

    def suspend_or_restore_account(self, **kwargs):
        return self._call_inner_tool('suspend_or_restore_account', kwargs)
