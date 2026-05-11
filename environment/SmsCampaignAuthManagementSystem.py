# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import time
from typing import Dict, Any
from datetime import datetime
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
import random



class CampaignInfo(TypedDict):
    campaign_id: str
    name: str
    created_at: str
    scheduled_time: str
    content: str
    status: str
    tool_used: str
    sender_id: str

class RecipientInfo(TypedDict):
    recipient_id: str
    phone_number: str
    recipient_name: str
    subscription_status: str

class CampaignRecipientInfo(TypedDict):
    campaign_id: str
    recipient_id: str
    delivery_status: str
    delivery_timestamp: str

class MessageLogInfo(TypedDict):
    message_id: str
    campaign_id: str
    recipient_id: str
    content: str
    sent_at: str
    delivery_status: str
    response_code: str

class OtpInfo(TypedDict):
    otp_id: str
    code: str
    recipient_id: str
    issued_at: str
    expires_at: str
    status: str
    validated_at: Optional[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing SMS campaigns and OTP authentication.
        """

        # Campaigns: {campaign_id: CampaignInfo}
        self.campaigns: Dict[str, CampaignInfo] = {}

        # Recipients: {recipient_id: RecipientInfo}
        self.recipients: Dict[str, RecipientInfo] = {}

        # CampaignRecipient delivery tracking:
        # {campaign_id: {recipient_id: CampaignRecipientInfo}}
        self.campaign_recipients: Dict[str, Dict[str, CampaignRecipientInfo]] = {}

        # Message logs: {message_id: MessageLogInfo}
        self.message_logs: Dict[str, MessageLogInfo] = {}

        # OTPs: {otp_id: OtpInfo}
        self.otps: Dict[str, OtpInfo] = {}

        # --- Constraint reminders ---
        # - OTPs have a validity period: not valid after expires_at
        # - OTP status transitions: pending → used/expired; can only validate if status is 'pending' and still valid
        # - Only campaigns with status "completed" or "sent" appear in campaign history
        # - Each campaign may only be sent to recipients with valid subscription_status
        # - No duplicate campaign messages to the same phone number within a campaign

    @staticmethod
    def _is_deliverable_subscription_status(status: str) -> bool:
        normalized = str(status or "").strip().lower().replace("_", "-")
        return normalized in {"active", "subscribed", "opt-in"}

    def get_campaign_by_id(self, campaign_id: str) -> dict:
        """
        Retrieve the full details of a campaign given its campaign_id.

        Args:
            campaign_id (str): The unique ID of the campaign to query.

        Returns:
            dict: 
                - { "success": True, "data": CampaignInfo }
                - { "success": False, "error": "Campaign not found" }

        Constraints:
            - campaign_id must exist in the system.
        """
        campaign = self.campaigns.get(campaign_id)
        if campaign is None:
            return { "success": False, "error": "Campaign not found" }
        return { "success": True, "data": campaign }

    def list_campaigns_by_tool(self, tool_used: str, status: Optional[str]=None) -> dict:
        """
        List all campaigns executed with a specified tool, optionally filtered by status.

        Args:
            tool_used (str): The name of the tool used to execute campaigns (e.g., "SMSto").
            status (Optional[str]): Optional campaign status to filter by (e.g., "sent", "completed").

        Returns:
            dict
            - On success: {
                "success": True,
                "data": List[CampaignInfo]  # campaigns matching tool_used (and status, if given)
              }
            - On failure: {
                "success": False,
                "error": str  # e.g., missing or empty tool_used
              }

        Constraints:
            - tool_used is required (cannot be None or empty)
        """
        if not tool_used or not isinstance(tool_used, str):
            return {"success": False, "error": "tool_used parameter must be a non-empty string"}

        # filter campaigns by tool_used, and optionally status
        result = [
            campaign for campaign in self.campaigns.values()
            if campaign["tool_used"] == tool_used and (status is None or campaign["status"] == status)
        ]

        return {"success": True, "data": result}

    def get_most_recent_campaign_by_tool(self, tool_used: str) -> dict:
        """
        Find the most recent campaign that used the specified tool.

        Args:
            tool_used (str): The tool name to filter campaigns (e.g., "SMSto").

        Returns:
            dict: {
                "success": True,
                "data": CampaignInfo  # The campaign with the newest created_at or scheduled_time
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, such as no campaign found for this tool
            }

        Notes:
            - Both created_at and scheduled_time are used for recency; the operation picks the latest of the two for each campaign,
              then among all matching campaigns, returns the one with the single latest timestamp.
            - Date-time strings should be directly comparable if ISO8601 (recommended).
        """

        # Accumulate relevant campaigns with this tool_used
        candidates = [
            campaign for campaign in self.campaigns.values()
            if campaign['tool_used'] == tool_used
        ]

        if not candidates:
            return {"success": False, "error": f"No campaigns found for tool: {tool_used}"}
    
        # Find the most recent by created_at or scheduled_time (use the max of both fields for each campaign)
        def get_latest_time(c):
            # NOTE: Assumes ISO8601 string (lexically sortable). For real applications, parse to datetime.
            return max(c['created_at'], c['scheduled_time'])

        most_recent_campaign = max(candidates, key=get_latest_time)
    
        return {"success": True, "data": most_recent_campaign}

    def list_campaign_history(self) -> dict:
        """
        Returns all campaigns whose status is "sent" or "completed", i.e., campaigns eligible to appear in campaign history.
    
        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # campaigns with status "sent" or "completed"
            }
            If no such campaigns, the list is empty.
        """
        result = [
            campaign_info
            for campaign_info in self.campaigns.values()
            if campaign_info.get("status") in ("sent", "completed")
        ]
        return {"success": True, "data": result}

    def get_campaign_recipients(self, campaign_id: str) -> dict:
        """
        List all recipients for a given campaign, along with their delivery statuses and timestamps.

        Args:
            campaign_id (str): The campaign identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": [
                            {
                                "recipient_id": str,
                                "phone_number": str,
                                "recipient_name": str,
                                "subscription_status": str,
                                "delivery_status": str,
                                "delivery_timestamp": str
                            },
                            ...
                        ]
                    }
                On error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The campaign_id must exist in the system.
            - Recipients are derived from campaign_recipients mapping.
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign does not exist"}

        recipients_data = []
        campaign_recips = self.campaign_recipients.get(campaign_id, {})
        for recipient_id, delivery_info in campaign_recips.items():
            recipient = self.recipients.get(recipient_id)
            if recipient is None:
                # Inconsistent state, skip this recipient
                continue
            recipients_data.append({
                "recipient_id": recipient["recipient_id"],
                "phone_number": recipient["phone_number"],
                "recipient_name": recipient["recipient_name"],
                "subscription_status": recipient["subscription_status"],
                "delivery_status": delivery_info["delivery_status"],
                "delivery_timestamp": delivery_info["delivery_timestamp"]
            })

        return {"success": True, "data": recipients_data}

    def get_message_log_by_id(self, message_id: str) -> dict:
        """
        Retrieve details of a particular message send record by message_id.

        Args:
            message_id (str): The unique identifier of the message log to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": MessageLogInfo
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Message log not found"
                    }
        Constraints:
            - The message_id must exist in message_logs to return a result.
        """
        if message_id not in self.message_logs:
            return { "success": False, "error": "Message log not found" }

        return { "success": True, "data": self.message_logs[message_id] }

    def list_messages_for_campaign(self, campaign_id: str) -> dict:
        """
        List all message logs associated with a specified campaign.

        Args:
            campaign_id (str): The campaign ID for which to fetch message logs.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": List[MessageLogInfo]}
                - On failure:
                    {"success": False, "error": str}

        Constraints:
            - The provided campaign_id must exist in the system.
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found"}

        logs = [
            log for log in self.message_logs.values()
            if log["campaign_id"] == campaign_id
        ]
        return {"success": True, "data": logs}

    def get_recipient_by_id(self, recipient_id: str) -> dict:
        """
        Retrieve recipient details using the given recipient_id.

        Args:
            recipient_id (str): The unique identifier of the recipient.

        Returns:
            dict: 
                - On success: { "success": True, "data": RecipientInfo }
                - On failure: { "success": False, "error": "Recipient not found" }

        Constraints:
            - The specified recipient_id must exist in the recipient records.
        """
        recipient = self.recipients.get(recipient_id)
        if not recipient:
            return {"success": False, "error": "Recipient not found"}
        return {"success": True, "data": recipient}

    def get_recipient_by_phone(self, phone_number: str) -> dict:
        """
        Find and return recipient information using the provided phone number.

        Args:
            phone_number (str): The recipient's phone number.

        Returns:
            dict:
                - {"success": True, "data": RecipientInfo} if found,
                - {"success": False, "error": "Recipient not found"} if not found.

        Constraints:
            - Phone number is matched exactly (string comparison).
        """
        for recipient in self.recipients.values():
            if recipient.get("phone_number") == phone_number:
                return { "success": True, "data": recipient }
        return { "success": False, "error": "Recipient not found" }

    def get_campaign_delivery_report(self, campaign_id: str) -> dict:
        """
        Retrieve aggregated delivery statistics (counts of each delivery_status) for a specified campaign.

        Args:
            campaign_id (str): The ID of the campaign to report on.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "<delivery_status>": int,    # e.g., "delivered": 120, "failed": 8, ...
                    ...
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The campaign must exist.
        """
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found"}

        recipients_info = self.campaign_recipients.get(campaign_id, {})
        if not recipients_info:
            # No recipients, all counts zero
            return {"success": True, "data": {}}

        status_counts = {}
        for recip in recipients_info.values():
            status = recip.get("delivery_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {"success": True, "data": status_counts}


    def get_otp_by_id(self, otp_id: str) -> Dict[str, Any]:
        """
        Retrieve OTP details by otp_id, including current status and computed validity.
    
        Args:
            otp_id (str): The unique identifier of the OTP.
    
        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        ...OtpInfo fields...,
                        "is_valid": bool  # Whether the OTP is currently valid for use
                    }
                }
                On error:
                {
                    "success": False,
                    "error": str  # e.g., OTP not found
                }

        Constraints:
            - Validity is True if current time < expires_at and status is "pending".
            - Validity is False if expired or status != "pending".
        """
        otp = self.otps.get(otp_id)
        if otp is None:
            return {"success": False, "error": "OTP not found"}

        expires_at_raw = otp.get("expires_at")
        if expires_at_raw is None:
            return {"success": False, "error": "Malformed expires_at timestamp"}

        expires_dt = None
        expires_ts = None
        try:
            expires_ts = float(expires_at_raw)
        except (TypeError, ValueError):
            try:
                expires_dt = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
            except Exception:
                return {"success": False, "error": "Malformed expires_at timestamp"}

        status = otp.get("status", "")
        if expires_dt is not None:
            now_dt = datetime.now(expires_dt.tzinfo) if expires_dt.tzinfo else datetime.utcnow()
            is_valid = (now_dt < expires_dt) and (status == "pending")
        else:
            now = time.time()
            is_valid = (now < expires_ts) and (status == "pending")

        # Return details, with computed validity
        otp_data = dict(otp)  # Make a copy
        otp_data["is_valid"] = is_valid

        return {"success": True, "data": otp_data}

    def get_otp_status(self, otp_id: str) -> dict:
        """
        Get the current status ('pending', 'used', 'expired') for the specified otp_id.

        Args:
            otp_id (str): The unique identifier of the OTP.

        Returns:
            dict: {
                "success": True,
                "data": str  # The status ("pending", "used", "expired") of the OTP
            }
            or
            {
                "success": False,
                "error": str  # If the OTP is not found
            }

        Constraints:
            - otp_id must exist in the OTP database.
        """
        otp_info = self.otps.get(otp_id)
        if not otp_info:
            return { "success": False, "error": "OTP not found" }

        return { "success": True, "data": otp_info["status"] }

    def list_otps_for_recipient(self, recipient_id: str) -> dict:
        """
        Show all OTPs issued to a particular recipient (by recipient_id).

        Args:
            recipient_id (str): The recipient's unique identifier.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": List[OtpInfo]  # All OTPs for the recipient, empty if none
                }
                On failure,
                {
                    "success": False,
                    "error": str  # Description of failure (e.g., recipient not found)
                }

        Constraints:
            - The recipient must exist (recipient_id in self.recipients).
            - No other constraints; all issued OTPs for this recipient are returned.
        """
        if recipient_id not in self.recipients:
            return {
                "success": False,
                "error": "Recipient does not exist"
            }
        otp_list = [
            otp_info for otp_info in self.otps.values()
            if otp_info["recipient_id"] == recipient_id
        ]
        return {
            "success": True,
            "data": otp_list
        }

    def create_campaign(
        self,
        campaign_id: str,
        name: str,
        created_at: str,
        scheduled_time: str,
        content: str,
        status: str,
        tool_used: str,
        sender_id: str
    ) -> dict:
        """
        Initialize and register a new SMS campaign in the system.

        Args:
            campaign_id (str): Unique identifier for the campaign.
            name (str): Campaign name.
            created_at (str): Timestamp of creation (ISO 8601).
            scheduled_time (str): Scheduled send time (ISO 8601).
            content (str): SMS message body.
            status (str): Initial status (e.g., 'draft', 'scheduled', 'sent').
            tool_used (str): Tool/service used for this campaign.
            sender_id (str): Campaign sender ID.

        Returns:
            dict: Success or failure information.
                On success:
                    { "success": True, "message": "Campaign <campaign_id> created successfully." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - campaign_id must be unique (not already in system).
        """
        if campaign_id in self.campaigns:
            return { "success": False, "error": "Campaign ID already exists." }

        # Minimal required field check (optional: you can comment out or adjust as needed)
        required_fields = [campaign_id, name, created_at, scheduled_time, content, status, tool_used, sender_id]
        if any(not x for x in required_fields):
            return { "success": False, "error": "All campaign fields are required and must be non-empty." }

        self.campaigns[campaign_id] = {
            "campaign_id": campaign_id,
            "name": name,
            "created_at": created_at,
            "scheduled_time": scheduled_time,
            "content": content,
            "status": status,
            "tool_used": tool_used,
            "sender_id": sender_id
        }

        return { "success": True, "message": f"Campaign {campaign_id} created successfully." }

    def update_campaign_status(self, campaign_id: str, new_status: str) -> dict:
        """
        Change the status of a campaign (e.g., from scheduled to sent/completed/cancelled).

        Args:
            campaign_id (str): The unique identifier of the campaign to update.
            new_status (str): The new status to set ("scheduled", "sent", "completed", "cancelled", etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Campaign status updated to <new_status> for campaign <campaign_id>"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - campaign_id must exist in the campaigns dictionary.
            - Optionally can check for valid status strings.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign not found" }

        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid status: status must be a non-empty string" }

        self.campaigns[campaign_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Campaign status updated to {new_status} for campaign {campaign_id}"
        }

    def add_recipient_to_campaign(self, campaign_id: str, recipient_id: str) -> dict:
        """
        Add a recipient to a campaign, ensuring:
          - Campaign exists
          - Recipient exists
          - Recipient's subscription_status is deliverable ("active", "subscribed", or "opt-in")
          - No duplicate phone number in same campaign
        Args:
            campaign_id (str): ID of the campaign
            recipient_id (str): ID of the recipient

        Returns:
            dict: {
                "success": True,
                "message": "Recipient added to campaign"
            }
            OR
            {
                "success": False,
                "error": <reason>
            }
        """
        # Check campaign existence
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign not found." }
    
        # Check recipient existence
        if recipient_id not in self.recipients:
            return { "success": False, "error": "Recipient not found." }
    
        recipient_info = self.recipients[recipient_id]
    
        if not self._is_deliverable_subscription_status(recipient_info.get("subscription_status", "")):
            return { "success": False, "error": "Recipient subscription status not valid for campaign." }
    
        # Prepare campaign recipient structure if not present
        if campaign_id not in self.campaign_recipients:
            self.campaign_recipients[campaign_id] = {}
    
        campaign_recips = self.campaign_recipients[campaign_id]
    
        # Prevent duplicate recipient_id in campaign
        if recipient_id in campaign_recips:
            return { "success": False, "error": "Recipient already added to this campaign." }
    
        # Prevent duplicate phone number in same campaign (check all recipient_ids already present)
        recipient_phone = recipient_info["phone_number"]
        for existing_recipient_id in campaign_recips:
            ex_info = self.recipients.get(existing_recipient_id)
            if ex_info and ex_info["phone_number"] == recipient_phone:
                return { "success": False, "error": "A recipient with this phone number is already in this campaign." }
    
        # Add CampaignRecipientInfo with initial blank delivery_status/timestamp
        self.campaign_recipients[campaign_id][recipient_id] = {
            "campaign_id": campaign_id,
            "recipient_id": recipient_id,
            "delivery_status": "",
            "delivery_timestamp": ""
        }
    
        return { "success": True, "message": "Recipient added to campaign" }

    def send_campaign_messages(self, campaign_id: str) -> dict:
        """
        Triggers the sending of messages for a campaign to all valid, non-duplicate recipients.
        Only sends to recipients who:
            - Have a deliverable subscription_status ("subscribed", "active", or "opt-in")
            - Have not already received the message within this campaign (by phone_number)

        Args:
            campaign_id (str): The ID of the campaign to send.

        Returns:
            dict: {
                "success": True,
                "message": str,
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Do not send to recipients without valid subscription_status.
            - Do not send duplicate messages to the same phone_number within the campaign.
            - If campaign is already sent/completed, do not allow sending again.
            - For each sent message:
                - Add to MessageLog.
                - Update CampaignRecipientInfo with delivery_status "sent" and delivery_timestamp.
            - Campaign status should be updated to "sent" after this operation.
        """

        # 1. Check campaign existence
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found."}

        campaign = self.campaigns[campaign_id]

        # 2. Check status: block resending if already sent/completed
        if campaign["status"] in ["sent", "completed"]:
            return {"success": False, "error": f"Campaign status is '{campaign['status']}', cannot send messages again."}

        # 3. Get assigned recipients
        campaign_recipient_map = self.campaign_recipients.get(campaign_id, {})
        if not campaign_recipient_map:
            return {"success": False, "error": "No recipients assigned to this campaign."}

        # 4. Deduplicate by phone number and filter by subscription status
        valid_recipients = []
        seen_phone_numbers = set()
        for recipient_id, camp_recv_info in campaign_recipient_map.items():
            recipient = self.recipients.get(recipient_id)
            if not recipient:
                continue  # skip if recipient info missing

            phone = recipient.get("phone_number")
            if not self._is_deliverable_subscription_status(recipient.get("subscription_status", "")):
                continue
            # No duplicate messages to same phone number in this campaign
            if phone in seen_phone_numbers:
                continue
            # Check if already sent by delivery_status in CampaignRecipientInfo or by MessageLog
            if camp_recv_info.get("delivery_status") == "sent":
                continue  # message already sent to this recipient for this campaign

            valid_recipients.append((recipient_id, recipient, camp_recv_info))
            seen_phone_numbers.add(phone)

        if not valid_recipients:
            return {"success": False, "error": "No valid recipients to send campaign messages to."}

        # 5. Send message to each valid recipient
        now_str = datetime.utcnow().isoformat() + "Z"
        sent_count = 0
        for recipient_id, recipient, camp_recv_info in valid_recipients:
            # Generate unique message_id (use time and IDs for simplification)
            message_id = f"{campaign_id}-{recipient_id}-{int(time.time() * 1000)}"

            # Create MessageLog
            msg_log: MessageLogInfo = {
                "message_id": message_id,
                "campaign_id": campaign_id,
                "recipient_id": recipient_id,
                "content": campaign["content"],
                "sent_at": now_str,
                "delivery_status": "sent",
                "response_code": "0"  # Assuming "0" as success placeholder
            }
            self.message_logs[message_id] = msg_log

            # Update CampaignRecipientInfo delivery
            camp_recv_info["delivery_status"] = "sent"
            camp_recv_info["delivery_timestamp"] = now_str

            # Sync update in campaign_recipients
            self.campaign_recipients[campaign_id][recipient_id] = camp_recv_info

            sent_count += 1

        # 6. Update campaign status to "sent"
        self.campaigns[campaign_id]["status"] = "sent"

        return {
            "success": True,
            "message": f"Sent campaign '{campaign['name']}' to {sent_count} recipients."
        }

    def log_message_delivery(
        self,
        message_id: str,
        campaign_id: str,
        recipient_id: str,
        content: str,
        sent_at: str,
        delivery_status: str,
        response_code: str
    ) -> dict:
        """
        Create a new message log record for SMS delivery results.

        Args:
            message_id (str): Unique message log identifier.
            campaign_id (str): Associated campaign ID (must exist).
            recipient_id (str): Associated recipient ID (must exist).
            content (str): Message content.
            sent_at (str): Time the message was sent (timestamp string).
            delivery_status (str): Delivery result/status.
            response_code (str): Response code/result of delivery.

        Returns:
            dict: {
                "success": True,
                "message": "Message log added."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - message_id must be unique.
            - campaign_id and recipient_id must exist in the system.
        """
        if message_id in self.message_logs:
            return {"success": False, "error": "Message ID already exists."}
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign does not exist."}
        if recipient_id not in self.recipients:
            return {"success": False, "error": "Recipient does not exist."}

        log_info: MessageLogInfo = {
            "message_id": message_id,
            "campaign_id": campaign_id,
            "recipient_id": recipient_id,
            "content": content,
            "sent_at": sent_at,
            "delivery_status": delivery_status,
            "response_code": response_code,
        }
        self.message_logs[message_id] = log_info

        return {"success": True, "message": "Message log added."}


    def issue_otp(
        self,
        recipient_id: str,
        code: Optional[str] = None,
        validity_seconds: int = 300,
        otp_id: Optional[str] = None,
        issued_at: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> dict:
        """
        Generate and assign a new OTP to a recipient.

        Args:
            recipient_id (str): The recipient's identifier.
            code (str, optional): The OTP code to use. If None, generates a random 6-digit code.
            validity_seconds (int): Validity period in seconds for the OTP (default: 300).
            otp_id (str, optional): Optionally provide an OTP ID. If None, a UUID will be generated.
            issued_at (str, optional): Optionally provide ISO timestamp for issuance time.
            expires_at (str, optional): Optionally provide expiration ISO timestamp. If None, calculated.
    
        Returns:
            dict: {
               "success": True,
               "message": "OTP issued successfully",
               "otp_id": str,
            }
            or
            {
               "success": False,
               "error": str,
            }
    
        Constraints:
            - Recipient must exist.
            - OTP ID must be unique.
            - Status is set to 'pending'.
            - OTP validity period enforced via expires_at.
        """
        # Check recipient existence
        if recipient_id not in self.recipients:
            return {"success": False, "error": "Recipient does not exist"}
    
        # OTP ID generation/check
        if otp_id is None:
            otp_id = str(uuid.uuid4())
        if otp_id in self.otps:
            return {"success": False, "error": "OTP ID already exists"}
    
        # OTP code generation (6-digit random if not provided)
        if code is None:
            code = f"{random.randint(100000, 999999)}"

        # Time handling (ISO strings)
        if issued_at is None:
            issued_dt = datetime.utcnow()
            issued_at = issued_dt.isoformat()
        else:
            try:
                issued_dt = datetime.fromisoformat(issued_at)
            except Exception:
                return {"success": False, "error": "Invalid issued_at format, must be ISO8601"}
    
        if expires_at is None:
            expires_dt = issued_dt + timedelta(seconds=validity_seconds)
            expires_at = expires_dt.isoformat()
        else:
            try:
                expires_dt = datetime.fromisoformat(expires_at)
            except Exception:
                return {"success": False, "error": "Invalid expires_at format, must be ISO8601"}
    
        # Compose OTP info
        otp_info = {
            "otp_id": otp_id,
            "code": code,
            "recipient_id": recipient_id,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "status": "pending",
            "validated_at": None
        }
        self.otps[otp_id] = otp_info

        return {
            "success": True,
            "message": "OTP issued successfully",
            "otp_id": otp_id
        }

    def validate_otp(self, otp_id: str, code: str, current_time: str) -> dict:
        """
        Attempt to validate a user's OTP by otp_id and code.
        OTP may only be validated if:
          - status is 'pending'
          - current_time <= expires_at
          - code matches

        If successful:
            - status is updated to 'used'
            - validated_at is set to current_time

        If OTP is expired (current_time > expires_at) and still pending:
            - status is set to 'expired'
            - cannot be validated

        Args:
            otp_id (str): OTP identifier.
            code (str): The OTP code submitted for validation.
            current_time (str): Current timestamp (ISO 8601 or comparable to expires_at).

        Returns:
            dict: { "success": True, "message": "OTP validated successfully" }
                  { "success": False, "error": "<reason>" }
        """
        otp = self.otps.get(otp_id)
        if not otp:
            return { "success": False, "error": "OTP not found" }

        if otp["status"] == "used":
            return { "success": False, "error": "OTP has already been used" }
        if otp["status"] == "expired":
            return { "success": False, "error": "OTP has expired" }

        # Compare current time with expires_at
        try:
            fmt = "%Y-%m-%dT%H:%M:%S" if "T" in otp["expires_at"] else "%Y-%m-%d %H:%M:%S"
            expires_at_dt = datetime.strptime(otp["expires_at"], fmt)
            current_dt = datetime.strptime(current_time, fmt)
        except Exception:
            # fallback to string comparison if parse fails
            if current_time > otp["expires_at"]:
                current_later = True
            else:
                current_later = False
        else:
            current_later = current_dt > expires_at_dt

        if current_later:
            if otp["status"] == "pending":
                otp["status"] = "expired"
                otp["validated_at"] = None  # Not validated
            return { "success": False, "error": "OTP has expired" }

        if code != otp["code"]:
            return { "success": False, "error": "Invalid OTP code" }

        # Valid OTP
        otp["status"] = "used"
        otp["validated_at"] = current_time
        return { "success": True, "message": "OTP validated successfully" }


    def expire_otp(self, otp_id: str, now: str = None) -> dict:
        """
        Mark an OTP as 'expired' if the current time is past its 'expires_at' time.

        Args:
            otp_id (str): The ID of the OTP to check/expire.
            now (str, optional): Current time in ISO8601 format. If not provided, uses UTC now.

        Returns:
            dict: {
                "success": True,
                "message": "OTP expired." | "OTP not yet expired." | "OTP is already expired/used."
            }
            or
            {
                "success": False,
                "error": "...reason..."
            }
        Constraints:
            - Only OTPs with status 'pending' can be marked 'expired'.
            - OTP must exist.
            - Must check that expires_at < current time (use provided `now` or UTC now).
            - Idempotent: re-expiring an already expired OTP is still a "success".
        """
        if otp_id not in self.otps:
            return { "success": False, "error": "OTP does not exist." }
    
        otp = self.otps[otp_id]
        current_status = otp.get("status")
        expires_at = otp.get("expires_at")
        try:
            expires_dt = datetime.fromisoformat(expires_at)
        except Exception:
            return { "success": False, "error": "Invalid expires_at time format." }
    
        # Get the "now" time
        if now is not None:
            try:
                now_dt = datetime.fromisoformat(now)
            except Exception:
                return { "success": False, "error": "Invalid now time format." }
        else:
            now_dt = datetime.utcnow()

        if current_status == "expired":
            return { "success": True, "message": "OTP is already expired." }
        if current_status == "used":
            return { "success": True, "message": "OTP is already used." }

        if now_dt >= expires_dt:
            if current_status == "pending":
                otp['status'] = "expired"
                return { "success": True, "message": "OTP expired." }
            else:
                return { "success": True, "message": f"OTP is already {current_status}." }
        else:
            return { "success": True, "message": "OTP not yet expired." }

    def update_recipient_subscription_status(self, recipient_id: str, new_status: str) -> dict:
        """
        Change the subscription_status of a recipient (e.g., opt-in/opt-out).

        Args:
            recipient_id (str): The unique identifier of the recipient to update.
            new_status (str): The new subscription status (e.g., 'opt-in', 'opt-out').

        Returns:
            dict: {
                "success": True,
                "message": "Recipient subscription_status updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - recipient_id must exist in the system.
            - No restrictions on new_status values (as per state space/constraints).
        """
        recipient = self.recipients.get(recipient_id)
        if recipient is None:
            return {"success": False, "error": "Recipient not found"}

        recipient["subscription_status"] = new_status
        return {"success": True, "message": "Recipient subscription_status updated."}

    def remove_recipient_from_campaign(self, campaign_id: str, recipient_id: str) -> dict:
        """
        Removes a given recipient from a specific campaign.

        Args:
            campaign_id (str): The ID of the campaign.
            recipient_id (str): The ID of the recipient to be removed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Recipient <recipient_id> removed from campaign <campaign_id>."
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Both campaign and recipient must exist.
            - Recipient must be in the campaign's recipient list.
            - Only removes from the campaign's recipient mapping (not logs or OTPs).
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign does not exist." }

        if recipient_id not in self.recipients:
            return { "success": False, "error": "Recipient does not exist." }

        if campaign_id not in self.campaign_recipients:
            return { "success": False, "error": "Campaign has no recipients." }

        if recipient_id not in self.campaign_recipients[campaign_id]:
            return { "success": False, "error": "Recipient is not part of this campaign." }

        del self.campaign_recipients[campaign_id][recipient_id]

        # Optionally, if all recipients removed from a campaign, remove the empty dict
        if not self.campaign_recipients[campaign_id]:
            del self.campaign_recipients[campaign_id]

        return {
            "success": True,
            "message": f"Recipient {recipient_id} removed from campaign {campaign_id}."
        }

    def clean_duplicate_campaign_recipients(self) -> dict:
        """
        Verify and remove duplicate recipient entries (by phone number) within the same campaign.

        For each campaign, ensures each phone number is only present once in the recipient list.
        Keeps the first occurrence and removes subsequent duplicates for a phone number.
        Recipients whose recipient_id cannot be resolved to a valid phone number are ignored.

        Returns:
            dict: {
                "success": True,
                "message": "Duplicate recipients removed from campaigns."
            }

        Constraints:
            - No duplicate campaign messages to the same phone number within a campaign.
        """
        for campaign_id, recipients_map in self.campaign_recipients.items():
            seen_numbers = set()
            to_remove = []
            # To preserve insertion order, get a list
            for recipient_id, rec_info in list(recipients_map.items()):
                recipient = self.recipients.get(recipient_id)
                if not recipient:
                    continue  # Skip if recipient not found
                phone = recipient.get("phone_number")
                if not phone:
                    continue  # Skip if phone_number missing
                if phone in seen_numbers:
                    to_remove.append(recipient_id)
                else:
                    seen_numbers.add(phone)
            # Remove duplicate recipient entries
            for rid in to_remove:
                del recipients_map[rid]
        return {"success": True, "message": "Duplicate recipients removed from campaigns."}


class SmsCampaignAuthManagementSystem(BaseEnv):
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

    def get_campaign_by_id(self, **kwargs):
        return self._call_inner_tool('get_campaign_by_id', kwargs)

    def list_campaigns_by_tool(self, **kwargs):
        return self._call_inner_tool('list_campaigns_by_tool', kwargs)

    def get_most_recent_campaign_by_tool(self, **kwargs):
        return self._call_inner_tool('get_most_recent_campaign_by_tool', kwargs)

    def list_campaign_history(self, **kwargs):
        return self._call_inner_tool('list_campaign_history', kwargs)

    def get_campaign_recipients(self, **kwargs):
        return self._call_inner_tool('get_campaign_recipients', kwargs)

    def get_message_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_log_by_id', kwargs)

    def list_messages_for_campaign(self, **kwargs):
        return self._call_inner_tool('list_messages_for_campaign', kwargs)

    def get_recipient_by_id(self, **kwargs):
        return self._call_inner_tool('get_recipient_by_id', kwargs)

    def get_recipient_by_phone(self, **kwargs):
        return self._call_inner_tool('get_recipient_by_phone', kwargs)

    def get_campaign_delivery_report(self, **kwargs):
        return self._call_inner_tool('get_campaign_delivery_report', kwargs)

    def get_otp_by_id(self, **kwargs):
        return self._call_inner_tool('get_otp_by_id', kwargs)

    def get_otp_status(self, **kwargs):
        return self._call_inner_tool('get_otp_status', kwargs)

    def list_otps_for_recipient(self, **kwargs):
        return self._call_inner_tool('list_otps_for_recipient', kwargs)

    def create_campaign(self, **kwargs):
        return self._call_inner_tool('create_campaign', kwargs)

    def update_campaign_status(self, **kwargs):
        return self._call_inner_tool('update_campaign_status', kwargs)

    def add_recipient_to_campaign(self, **kwargs):
        return self._call_inner_tool('add_recipient_to_campaign', kwargs)

    def send_campaign_messages(self, **kwargs):
        return self._call_inner_tool('send_campaign_messages', kwargs)

    def log_message_delivery(self, **kwargs):
        return self._call_inner_tool('log_message_delivery', kwargs)

    def issue_otp(self, **kwargs):
        return self._call_inner_tool('issue_otp', kwargs)

    def validate_otp(self, **kwargs):
        return self._call_inner_tool('validate_otp', kwargs)

    def expire_otp(self, **kwargs):
        return self._call_inner_tool('expire_otp', kwargs)

    def update_recipient_subscription_status(self, **kwargs):
        return self._call_inner_tool('update_recipient_subscription_status', kwargs)

    def remove_recipient_from_campaign(self, **kwargs):
        return self._call_inner_tool('remove_recipient_from_campaign', kwargs)

    def clean_duplicate_campaign_recipients(self, **kwargs):
        return self._call_inner_tool('clean_duplicate_campaign_recipients', kwargs)
