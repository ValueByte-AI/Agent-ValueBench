# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Dict
from datetime import datetime



# --- TypedDicts mapping the state space entities ---

class TenderInfo(TypedDict):
    tender_id: str
    title: str
    description: str
    submission_deadline: str
    budget: float
    status: str
    created_date: str
    published_date: str
    closing_date: str
    organization_id: str

class OrganizationInfo(TypedDict):
    organization_id: str
    name: str
    contact_info: str

class UserInfo(TypedDict):
    user_id: str  # mapped from "_id"
    name: str
    user_role: str
    organization_id: str

class BidInfo(TypedDict):
    bid_id: str  # mapped from "d_id"
    tender_id: str
    user_id: str
    submission_date: str
    bid_amount: float
    status: str  # mapped from "sta"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment: E-Procurement Tender Management System

        # Constraints:
        # - Each tender must have a unique tender_id
        # - Tender status should reflect submission deadline phase ("open"/"closed")
        # - Only tenders with status "open" can accept new bids
        # - Organization and user data are linked to tenders and bids for accountability
        # - Budgets must be non-negative numbers
        """
        # Tenders: {tender_id: TenderInfo}
        self.tenders: Dict[str, TenderInfo] = {}

        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Bids: {bid_id: BidInfo}
        self.bids: Dict[str, BidInfo] = {}

        # Optional benchmark time injected by a case. This env must not depend
        # on host time when evaluating tender windows.
        self.current_time: str | None = None

    @staticmethod
    def _parse_datetime(value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid datetime string")
        value = value.strip()
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")

    def _get_current_time(self) -> datetime:
        current_time = getattr(self, "current_time", None)
        if isinstance(current_time, str) and current_time.strip():
            return self._parse_datetime(current_time)

        candidate_values = []
        for tender in self.tenders.values():
            for key in ("created_date", "published_date"):
                value = tender.get(key)
                if isinstance(value, str) and value.strip():
                    candidate_values.append(value)
        for bid in self.bids.values():
            value = bid.get("submission_date")
            if isinstance(value, str) and value.strip():
                candidate_values.append(value)

        parsed_candidates = []
        for value in candidate_values:
            try:
                parsed_candidates.append(self._parse_datetime(value))
            except Exception:
                continue

        if parsed_candidates:
            return max(parsed_candidates)

        raise ValueError("Environment current time is unavailable")

    def get_tender_by_id(self, tender_id: str) -> dict:
        """
        Retrieve the details of a specific tender by its unique tender_id.

        Args:
            tender_id (str): The unique identifier of the tender.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": TenderInfo  # The tender's structured metadata
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Tender not found"
                    }

        Constraints:
            - tender_id must exist in the system.
        """
        tender = self.tenders.get(tender_id)
        if not tender:
            return { "success": False, "error": "Tender not found" }
        return { "success": True, "data": tender }

    def get_tender_status(self, tender_id: str) -> dict:
        """
        Return the current status of a tender (e.g., "open", "closed").

        Args:
            tender_id (str): The unique identifier of the tender.

        Returns:
            dict: {
                "success": True,
                "data": str  # The current status of the tender
            }
            OR
            {
                "success": False,
                "error": str  # An error message if tender_id does not exist
            }

        Constraints:
            - The tender must exist (tender_id must be present in the system).
        """
        tender = self.tenders.get(tender_id)
        if not tender:
            return {"success": False, "error": "Tender does not exist"}

        return {"success": True, "data": tender["status"]}

    def get_tender_deadlines(self, tender_id: str) -> dict:
        """
        Retrieve the submission_deadline, published_date, and closing_date for the specified tender.

        Args:
            tender_id (str): The unique identifier of the tender.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "submission_deadline": str,
                            "published_date": str,
                            "closing_date": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Tender not found"
                    }

        Constraints:
            - Specified tender_id must exist.
        """
        tender = self.tenders.get(tender_id)
        if not tender:
            return { "success": False, "error": "Tender not found" }

        deadlines = {
            "submission_deadline": tender.get("submission_deadline"),
            "published_date": tender.get("published_date"),
            "closing_date": tender.get("closing_date")
        }
        return { "success": True, "data": deadlines }

    def get_tender_budget(self, tender_id: str) -> dict:
        """
        Return the budget value for a given tender.

        Args:
            tender_id (str): The unique identifier of the tender.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": float  # budget value (non-negative)
                }
            or
                {
                    "success": False,
                    "error": str  # e.g. "Tender not found"
                }

        Constraints:
            - Budget must be a non-negative number (enforced elsewhere).
            - Returns error if tender_id does not exist.
        """
        tender = self.tenders.get(tender_id)
        if not tender:
            return { "success": False, "error": "Tender not found" }
        return { "success": True, "data": tender["budget"] }

    def list_all_tenders(self) -> dict:
        """
        Retrieve a list of all tenders in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TenderInfo],  # list of all tender info (possibly empty)
            }
        Constraints:
            - None; simply returns all tenders as stored.
        """
        tender_list = list(self.tenders.values())
        return { "success": True, "data": tender_list }

    def list_tenders_by_status(self, status: str) -> dict:
        """
        List all tenders filtered by a given status (e.g., "open", "closed").

        Args:
            status (str): The status to filter tenders by.

        Returns:
            dict: {
                "success": True,
                "data": List[TenderInfo],  # All matching tenders (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # On invalid input type or internal error
            }

        Constraints:
            - None directly, status value is matched as-is to tenders' status attribute.
        """
        if not isinstance(status, str):
            return { "success": False, "error": "Status must be a string." }
        result = [
            tender for tender in self.tenders.values()
            if tender["status"] == status
        ]
        return { "success": True, "data": result }

    def list_tenders_by_organization(self, organization_id: str) -> dict:
        """
        List all tenders associated with a specific organization.

        Args:
            organization_id (str): The ID of the organization whose tenders to fetch.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TenderInfo]  # May be empty if no tenders found
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of reason (e.g., organization does not exist)
                    }

        Constraints:
            - The organization must exist in the system.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        tenders = [
            tender for tender in self.tenders.values()
            if tender["organization_id"] == organization_id
        ]
        return { "success": True, "data": tenders }

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve organization details by organization_id.

        Args:
            organization_id (str): The unique identifier for the organization.

        Returns:
            dict:
                success: True and data: OrganizationInfo if found,
                otherwise, success: False and error message.

        Constraints:
            - The organization_id must exist in the system.
        """
        if not organization_id or organization_id not in self.organizations:
            return {"success": False, "error": "Organization not found"}
        return {"success": True, "data": self.organizations[organization_id]}

    def list_all_organizations(self) -> dict:
        """
        Retrieve the complete list of organizations registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[OrganizationInfo]  # List of all organizations (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Only if an internal issue occurs (should not happen here)
            }
        """
        organizations = list(self.organizations.values())
        return { "success": True, "data": organizations }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,   # User details if user exists
            }
            or {
                "success": False,
                "error": str        # Error message if user not found
            }

        Constraints:
            - The user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def list_all_users(self) -> dict:
        """
        List all users registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],  # List of all users (empty if none exist)
            }
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def list_bids_by_tender(self, tender_id: str) -> dict:
        """
        Fetch all bids submitted for a particular tender.

        Args:
            tender_id (str): Tender ID whose bids will be retrieved.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[BidInfo]  # List of bids for the tender, may be empty
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g., tender not found)
                }

        Constraints:
            - tender_id must exist in the system (must reference a Tender).
        """
        if tender_id not in self.tenders:
            return { "success": False, "error": "Tender not found" }

        result = [
            bid_info for bid_info in self.bids.values()
            if bid_info["tender_id"] == tender_id
        ]
        return { "success": True, "data": result }

    def list_bids_by_user(self, user_id: str) -> dict:
        """
        List all bids submitted by a particular user.

        Args:
            user_id (str): Unique identifier of the user whose bids are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[BidInfo]  # List of bid info submitted by this user (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g. "User does not exist"
            }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        bids_by_user = [
            bid_info for bid_info in self.bids.values()
            if bid_info["user_id"] == user_id
        ]

        return { "success": True, "data": bids_by_user }

    def get_bid_by_id(self, bid_id: str) -> dict:
        """
        Retrieve detailed information about a bid, given its bid_id.

        Args:
            bid_id (str): Unique identifier for the bid.

        Returns:
            dict: {
                "success": True,
                "data": BidInfo
            }
            or
            {
                "success": False,
                "error": str  # Bid does not exist
            }

        Constraints:
            - The bid_id must exist in the system.
        """
        bid = self.bids.get(bid_id)
        if not bid:
            return { "success": False, "error": "Bid does not exist" }
        return { "success": True, "data": bid }

    def get_bid_status(self, bid_id: str) -> dict:
        """
        Return the status of a given bid.

        Args:
            bid_id (str): The unique identifier of the bid.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": { "status": <str> }
                    }
                On error:
                    {
                        "success": False,
                        "error": "Bid not found"
                    }
        Constraints:
            - bid_id must exist in the system.
        """
        bid = self.bids.get(bid_id)
        if not bid:
            return { "success": False, "error": "Bid not found" }
        return { "success": True, "data": { "status": bid["status"] } }


    def can_tender_accept_bids(self, tender_id: str) -> dict:
        """
        Check if a tender is 'open' and currently eligible to receive new bids
        (i.e., status is 'open' and current time is before its submission_deadline).

        Args:
            tender_id (str): The unique identifier for the tender.

        Returns:
            dict: {
                'success': True,
                'data': bool  # True if eligible, False otherwise
            }
            or
            {
                'success': False,
                'error': str  # Reason for failure (e.g., tender not found)
            }

        Constraints:
            - Tender must exist.
            - Status must be 'open'.
            - Current time must be before submission_deadline.
        """
        tender = self.tenders.get(tender_id)
        if not tender:
            return {"success": False, "error": "Tender not found"}

        status = tender.get("status")
        deadline_str = tender.get("submission_deadline")

        if not status or not deadline_str:
            return {"success": True, "data": False}

        try:
            deadline = self._parse_datetime(deadline_str)
            now = self._get_current_time()
        except Exception:
            return {"success": True, "data": False}

        eligible = (status == "open") and (now < deadline)
        return {"success": True, "data": eligible}

    def submit_bid(
        self,
        bid_id: str,
        tender_id: str,
        user_id: str,
        bid_amount: float,
        submission_date: str
    ) -> dict:
        """
        Create and submit a new bid for a tender on behalf of a user, if the tender is open.

        Args:
            bid_id (str): Unique identifier for the bid.
            tender_id (str): Identifier of the tender to bid for.
            user_id (str): Identifier of the user submitting the bid.
            bid_amount (float): The bid financial value (must be non-negative).
            submission_date (str): Submission date/time as ISO string.

        Returns:
            dict: On success, { "success": True, "message": "Bid submitted successfully." }
                  On failure, { "success": False, "error": <reason> }

        Constraints:
          - Tender must exist and be "open".
          - User must exist.
          - Bid ID must be unique.
          - Bid amount >= 0.
          - Registers association: bid links user and tender.
        """

        # Tender existence
        tender = self.tenders.get(tender_id)
        if tender is None:
            return {"success": False, "error": "Tender does not exist."}

        acceptance = self.can_tender_accept_bids(tender_id)
        if not acceptance.get("success"):
            return {"success": False, "error": acceptance["error"]}
        if not acceptance.get("data"):
            return {"success": False, "error": "Tender is not open for bids."}

        # User existence
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist."}

        # Bid ID uniqueness
        if bid_id in self.bids:
            return {"success": False, "error": "Bid ID already exists."}

        # Bid amount check
        if not isinstance(bid_amount, (int, float)) or bid_amount < 0:
            return {"success": False, "error": "Bid amount must be a non-negative number."}

        # Create bid info
        bid_info = {
            "bid_id": bid_id,
            "tender_id": tender_id,
            "user_id": user_id,
            "submission_date": submission_date,
            "bid_amount": bid_amount,
            "status": "submitted"
        }

        self.bids[bid_id] = bid_info

        return {"success": True, "message": "Bid submitted successfully."}


    def close_tender(self, tender_id: str) -> dict:
        """
        Mark a tender as 'closed'.

        Args:
            tender_id (str): The identifier of the tender to close.

        Returns:
            dict: {
                "success": True,
                "message": "Tender <tender_id> marked as closed."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The tender must exist.
            - If already closed, do not update and return failure.
            - Sets status to 'closed'.
            - Optionally updates 'closing_date' to current UTC time (ISO format string).
        """
        tender = self.tenders.get(tender_id)
        if not tender:
            return {"success": False, "error": "Tender does not exist."}

        if tender["status"] == "closed":
            return {"success": False, "error": "Tender is already closed."}

        tender["status"] = "closed"
        try:
            tender["closing_date"] = self._format_datetime(self._get_current_time())
        except Exception:
            pass

        self.tenders[tender_id] = tender

        return {"success": True, "message": f"Tender {tender_id} marked as closed."}


    def update_tender_status(self, tender_id: str, new_status: str) -> dict:
        """
        Update the status of a tender, enforcing consistency with its submission deadline.

        Args:
            tender_id (str): The ID of the tender to update.
            new_status (str): The new status to set ('open' or 'closed').

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of the operation
            }
            or
            {
                "success": False,
                "error": str  # Reason why update failed
            }

        Constraints:
            - Tender status should reflect the current phase based on submission_deadline:
                - "open" only if deadline is in the future
                - "closed" only if deadline is in the past
            - Tender must exist
            - Only "open" or "closed" are allowed as statuses
        """
        tender = self.tenders.get(tender_id)
        if tender is None:
            return { "success": False, "error": "Tender not found." }

        if new_status not in ("open", "closed"):
            return { "success": False, "error": "Invalid status. Only 'open' or 'closed' allowed." }

        try:
            deadline_dt = self._parse_datetime(tender["submission_deadline"])
        except Exception:
            return { "success": False, "error": "Submission deadline format invalid." }

        try:
            now = self._get_current_time()
        except Exception:
            return { "success": False, "error": "Environment current time unavailable." }
        if now < deadline_dt:
            # Only open is allowed before deadline
            if new_status != "open":
                return { "success": False, "error": "Tender can only be 'open' before submission deadline." }
        else:
            # Only closed is allowed after deadline
            if new_status != "closed":
                return { "success": False, "error": "Tender can only be 'closed' after submission deadline." }

        tender["status"] = new_status
        self.tenders[tender_id] = tender
        return { "success": True, "message": f"Tender status updated to {new_status}." }

    def create_tender(
        self,
        tender_id: str,
        title: str,
        description: str,
        submission_deadline: str,
        budget: float,
        status: str,
        created_date: str,
        published_date: str,
        closing_date: str,
        organization_id: str
    ) -> dict:
        """
        Add a new tender to the system.
        Args:
            tender_id (str): Unique identifier for the tender.
            title (str): Title of the tender.
            description (str): Description of the tender.
            submission_deadline (str): Submission deadline (ISO string).
            budget (float): Budget amount (must be non-negative).
            status (str): Initial status for the tender.
            created_date (str): Date of creation (ISO string).
            published_date (str): When the tender is/will be published (ISO string).
            closing_date (str): Date the tender will be closed (ISO string).
            organization_id (str): Organization ID creating the tender (must exist).

        Returns:
            dict: 
              - success: True and message on creation
              - success: False and error if constraints fail

        Constraints:
            - tender_id must be unique.
            - budget must be non-negative.
            - organization_id must reference an existing organization.
        """
        if tender_id in self.tenders:
            return { "success": False, "error": "Tender ID already exists." }
        if not isinstance(budget, (int, float)) or budget < 0:
            return { "success": False, "error": "Budget must be a non-negative number." }
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }
        # Minimal/naive: check required fields not empty
        required_fields = [tender_id, title, description, submission_deadline, status, created_date, published_date]
        if any(field is None or (isinstance(field, str) and not field.strip()) for field in required_fields):
            return { "success": False, "error": "Missing required tender fields." }
        # Add the tender
        self.tenders[tender_id] = {
            "tender_id": tender_id,
            "title": title,
            "description": description,
            "submission_deadline": submission_deadline,
            "budget": budget,
            "status": status,
            "created_date": created_date,
            "published_date": published_date,
            "closing_date": closing_date,
            "organization_id": organization_id
        }
        return { "success": True, "message": "Tender created successfully" }

    def update_tender_budget(self, tender_id: str, new_budget: float) -> dict:
        """
        Update the budget of the specified tender.

        Args:
            tender_id (str): The unique ID of the tender to update.
            new_budget (float): The new budget value (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Tender budget updated successfully."
            }
            or
            dict: {
                "success": False,
                "error": str  # Description of the error (e.g. tender not found, budget negative)
            }

        Constraints:
            - The tender_id must exist.
            - The new_budget must be a non-negative number.
        """
        if tender_id not in self.tenders:
            return { "success": False, "error": "Tender does not exist." }

        # Defensive check for numeric budget
        if not isinstance(new_budget, (int, float)):
            return { "success": False, "error": "Budget must be a numeric value." }
        if new_budget < 0:
            return { "success": False, "error": "Budget must be non-negative." }

        self.tenders[tender_id]["budget"] = float(new_budget)
        return { "success": True, "message": "Tender budget updated successfully." }

    def update_bid_status(self, bid_id: str, new_status: str) -> dict:
        """
        Change the status of a bid (e.g., from "submitted" to "accepted" or "rejected").

        Args:
            bid_id (str): The unique identifier for the bid.
            new_status (str): The new status to assign to the bid.

        Returns:
            dict: {
                "success": True,
                "message": "Bid status updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Bid must exist.
            - The referenced tender must exist.
            - Status must be a non-empty string.
        """
        if not isinstance(new_status, str) or not new_status.strip():
            return {"success": False, "error": "Invalid new status."}

        bid = self.bids.get(bid_id)
        if not bid:
            return {"success": False, "error": "Bid does not exist."}

        tender_id = bid.get('tender_id')
        if not tender_id or tender_id not in self.tenders:
            return {"success": False, "error": "Referenced tender does not exist."}

        bid["status"] = new_status
        self.bids[bid_id] = bid  # Not strictly necessary, but explicit.

        return {"success": True, "message": "Bid status updated successfully."}

    def update_tender_deadlines(
        self,
        tender_id: str,
        submission_deadline: str = None,
        published_date: str = None,
        closing_date: str = None
    ) -> dict:
        """
        Modify the submission_deadline, published_date, or closing_date for a given tender.

        Args:
            tender_id (str): The unique ID of the tender to update.
            submission_deadline (str, optional): The new submission deadline (ISO 8601 format encouraged).
            published_date (str, optional): The new published date (ISO 8601 format encouraged).
            closing_date (str, optional): The new closing date (ISO 8601 format encouraged).

        Returns:
            dict: {
                "success": True,
                "message": "Tender deadlines updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The tender_id must exist.
            - At least one deadline field must be provided to update.
        """
        if tender_id not in self.tenders:
            return { "success": False, "error": "Tender not found." }

        if not any([submission_deadline, published_date, closing_date]):
            return { "success": False, "error": "No new deadline values provided." }

        tender = self.tenders[tender_id]
        updated = False

        if submission_deadline is not None:
            tender["submission_deadline"] = submission_deadline
            updated = True

        if published_date is not None:
            tender["published_date"] = published_date
            updated = True

        if closing_date is not None:
            tender["closing_date"] = closing_date
            updated = True

        if updated:
            return { "success": True, "message": "Tender deadlines updated successfully." }
        else:
            return { "success": False, "error": "No deadline fields updated." }

    def delete_bid(self, bid_id: str) -> dict:
        """
        Remove a bid from the system.

        Args:
            bid_id (str): The unique identifier of the bid to be removed.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Bid deleted successfully."
                    }
                On failure (bid not found):
                    {
                        "success": False,
                        "error": "Bid with the given ID does not exist."
                    }

        Constraints:
            - The bid must exist in the system.
        """
        if bid_id not in self.bids:
            return {
                "success": False,
                "error": "Bid with the given ID does not exist."
            }
        del self.bids[bid_id]
        return {
            "success": True,
            "message": "Bid deleted successfully."
        }

    def delete_tender(self, tender_id: str) -> dict:
        """
        Remove a tender by its ID, along with all associated bids.

        Args:
            tender_id (str): Unique identifier of the tender to remove.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Tender and its associated bids have been deleted."
                    }
                On error:
                    {
                        "success": False,
                        "error": "Tender not found."
                    }

        Constraints:
        - The tender must exist; otherwise, an error is returned.
        - All bids associated with the tender must also be deleted.
        """
        if tender_id not in self.tenders:
            return {"success": False, "error": "Tender not found."}

        # Delete all bids associated with this tender
        associated_bid_ids = [bid_id for bid_id, bid in self.bids.items() if bid["tender_id"] == tender_id]
        for bid_id in associated_bid_ids:
            del self.bids[bid_id]

        # Delete the tender itself
        del self.tenders[tender_id]

        return {
            "success": True,
            "message": "Tender and its associated bids have been deleted."
        }

    def register_user(self, user_id: str, name: str, user_role: str, organization_id: str) -> dict:
        """
        Add a new user to the system.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): The user's name.
            user_role (str): Role/type of the user (e.g., "bidder", "official").
            organization_id (str): Identifier of the user's organization (must already exist).

        Returns:
            dict: {
                "success": True,
                "message": "User registered successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }
        
        Constraints:
            - user_id must be unique (not already in the system).
            - organization_id must refer to an existing organization.
            - All fields are required (non-empty).
        """
        if not all([user_id, name, user_role, organization_id]):
            return {"success": False, "error": "All user fields must be provided"}

        if user_id in self.users:
            return {"success": False, "error": "User ID already exists"}

        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist"}

        user_info = {
            "user_id": user_id,
            "name": name,
            "user_role": user_role,
            "organization_id": organization_id,
        }

        self.users[user_id] = user_info

        return {"success": True, "message": "User registered successfully"}

    def register_organization(self, organization_id: str, name: str, contact_info: str) -> dict:
        """
        Add a new organization to the system.

        Args:
            organization_id (str): The unique identifier for the organization.
            name (str): The organization's name.
            contact_info (str): The organization's contact details.

        Returns:
            dict: {
                "success": True,
                "message": "Organization registered successfully."
            }
            OR
            {
                "success": False,
                "error": str  # Reason why registration failed (e.g., ID already exists)
            }

        Constraints:
            - organization_id must be unique.
            - All fields must be non-empty.
        """
        if not organization_id or not isinstance(organization_id, str):
            return {"success": False, "error": "organization_id must be a non-empty string."}
        if organization_id in self.organizations:
            return {"success": False, "error": f"Organization with id '{organization_id}' already exists."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Organization name must be a non-empty string."}
        if not contact_info or not isinstance(contact_info, str):
            return {"success": False, "error": "Contact info must be a non-empty string."}

        org_info: OrganizationInfo = {
            "organization_id": organization_id,
            "name": name,
            "contact_info": contact_info
        }
        self.organizations[organization_id] = org_info

        return {"success": True, "message": "Organization registered successfully."}


class EProcurementTenderManagementSystem(BaseEnv):
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

    def get_tender_by_id(self, **kwargs):
        return self._call_inner_tool('get_tender_by_id', kwargs)

    def get_tender_status(self, **kwargs):
        return self._call_inner_tool('get_tender_status', kwargs)

    def get_tender_deadlines(self, **kwargs):
        return self._call_inner_tool('get_tender_deadlines', kwargs)

    def get_tender_budget(self, **kwargs):
        return self._call_inner_tool('get_tender_budget', kwargs)

    def list_all_tenders(self, **kwargs):
        return self._call_inner_tool('list_all_tenders', kwargs)

    def list_tenders_by_status(self, **kwargs):
        return self._call_inner_tool('list_tenders_by_status', kwargs)

    def list_tenders_by_organization(self, **kwargs):
        return self._call_inner_tool('list_tenders_by_organization', kwargs)

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def list_all_organizations(self, **kwargs):
        return self._call_inner_tool('list_all_organizations', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def list_bids_by_tender(self, **kwargs):
        return self._call_inner_tool('list_bids_by_tender', kwargs)

    def list_bids_by_user(self, **kwargs):
        return self._call_inner_tool('list_bids_by_user', kwargs)

    def get_bid_by_id(self, **kwargs):
        return self._call_inner_tool('get_bid_by_id', kwargs)

    def get_bid_status(self, **kwargs):
        return self._call_inner_tool('get_bid_status', kwargs)

    def can_tender_accept_bids(self, **kwargs):
        return self._call_inner_tool('can_tender_accept_bids', kwargs)

    def submit_bid(self, **kwargs):
        return self._call_inner_tool('submit_bid', kwargs)

    def close_tender(self, **kwargs):
        return self._call_inner_tool('close_tender', kwargs)

    def update_tender_status(self, **kwargs):
        return self._call_inner_tool('update_tender_status', kwargs)

    def create_tender(self, **kwargs):
        return self._call_inner_tool('create_tender', kwargs)

    def update_tender_budget(self, **kwargs):
        return self._call_inner_tool('update_tender_budget', kwargs)

    def update_bid_status(self, **kwargs):
        return self._call_inner_tool('update_bid_status', kwargs)

    def update_tender_deadlines(self, **kwargs):
        return self._call_inner_tool('update_tender_deadlines', kwargs)

    def delete_bid(self, **kwargs):
        return self._call_inner_tool('delete_bid', kwargs)

    def delete_tender(self, **kwargs):
        return self._call_inner_tool('delete_tender', kwargs)

    def register_user(self, **kwargs):
        return self._call_inner_tool('register_user', kwargs)

    def register_organization(self, **kwargs):
        return self._call_inner_tool('register_organization', kwargs)
