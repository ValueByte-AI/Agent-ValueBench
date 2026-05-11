# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import uuid
from datetime import datetime
from datetime import datetime, timezone
from typing import Optional, Dict
import secrets
from typing import Dict
import re



class UserInfo(TypedDict):
    _id: str
    name: str
    credentials: List[str]  # List of api_key strings
    contact_info: str
    permission: str

class MessageTemplateInfo(TypedDict):
    template_id: str
    owner_id: str  # user_id
    name: str
    content: str
    creation_time: str
    variables: List[str]

class MessageInfo(TypedDict, total=False):
    message_id: str
    sender_id: str  # user_id
    recipient_phone: str
    content: str
    template_id: Optional[str]  # Can be empty for non-templated content
    status: str  # pending, sent, delivered, failed
    sent_time: Optional[str]
    scheduled_time: Optional[str]
    delivery_report: Optional[str]
    parameters_used: Optional[Dict[str, str]]  # template variable assignment

class APIKeyInfo(TypedDict):
    api_key: str
    user_id: str
    status: str
    allowed_operation: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        SMS Gateway Platform Environment
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Message Templates: {template_id: MessageTemplateInfo}
        self.templates: Dict[str, MessageTemplateInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # API Keys: {api_key: APIKeyInfo}
        self.api_keys: Dict[str, APIKeyInfo] = {}

        # Constraints (to be enforced in logic):
        # - Messages can only be sent using API keys that are active and authorized for the requesting user.
        # - Message templates are only accessible by their respective owners or with proper permissions.
        # - Template variables must be provided or assigned when sending a message with variable content.
        # - Each message delivery record must record status (pending, sent, delivered, failed).
        # - Phone numbers must be validated before message submission/queuing.
        # - Scheduled messages must not be sent before their scheduled_time.

    @staticmethod
    def _looks_like_regex_validator(pattern: str) -> bool:
        if not isinstance(pattern, str):
            return False
        regex_markers = ("\\d", "\\w", "\\s", "^", "$", "[", "]", "(", ")", "{", "}", "|", "+", "*", "?")
        return any(marker in pattern for marker in regex_markers)

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _get_platform_current_time(self) -> Optional[datetime]:
        explicit_now = self._parse_timestamp(getattr(self, "current_time", None))
        return explicit_now

    def _can_use_template(self, user_id: str, template: MessageTemplateInfo) -> bool:
        if user_id == template["owner_id"]:
            return True

        requester = self.users.get(user_id)
        if not requester:
            return False
        if requester.get("permission") == "admin":
            return True

        owner = self.users.get(template["owner_id"])
        if requester.get("permission") == "operator" and owner and owner.get("permission") == "admin":
            return True

        return False

    def _is_phone_number_valid(self, phone_number: str) -> dict:
        pattern = getattr(self, "_validate_phone_number_state", None)
        if isinstance(pattern, str) and pattern:
            stripped = pattern.strip()
            if stripped.startswith("def validate_phone_number"):
                local_ns = {}
                try:
                    exec(stripped, {}, local_ns)
                    validator = local_ns.get("validate_phone_number")
                    if callable(validator):
                        result = validator(phone_number)
                        if isinstance(result, dict):
                            return {
                                "success": True,
                                "data": {
                                    "valid": bool(result.get("valid", False)),
                                    "reason": str(result.get("reason", "")),
                                },
                            }
                except Exception:
                    pass
            if self._looks_like_regex_validator(stripped):
                if not isinstance(phone_number, str):
                    return {
                        "success": True,
                        "data": {"valid": False, "reason": "Phone number must be a string."},
                    }
                try:
                    matched = re.fullmatch(stripped, phone_number) is not None
                except re.error:
                    matched = False
                return {
                    "success": True,
                    "data": {
                        "valid": matched,
                        "reason": "Valid phone number." if matched else "Phone number does not match platform policy.",
                    },
                }
        if not isinstance(phone_number, str):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Phone number must be a string."
                }
            }
        if not phone_number:
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Phone number is empty."
                }
            }
        if not phone_number.startswith("+"):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Phone number must start with '+' and country code."
                }
            }
        digits = phone_number[1:]
        if not digits.isdigit():
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Phone number must contain only digits after '+'."
                }
            }
        if not (8 <= len(digits) <= 15):
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Phone number must contain 8 to 15 digits after '+'."
                }
            }
        return {
            "success": True,
            "data": {
                "valid": True,
                "reason": "Valid phone number."
            }
        }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user info (ID, permissions, contact, API keys) by exact username.

        Args:
            name (str): The username (case-sensitive) to look up.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }
        """
        for user in self.users.values():
            if user["name"] == name:
                return {"success": True, "data": user}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by unique user ID.

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str  # If user is not found.
            }

        Constraints:
            - The user must exist in the platform.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def list_user_api_keys(self, user_id: str) -> dict:
        """
        Get all API keys and their statuses for a specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[APIKeyInfo],  # List of APIKeyInfo dicts for the user (may be empty if none)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message, e.g. user does not exist
                    }

        Constraints:
            - The user must exist.
            - Only API keys owned by the user are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        api_keys_list = [
            api_key_info
            for api_key_info in self.api_keys.values()
            if api_key_info["user_id"] == user_id
        ]

        return { "success": True, "data": api_keys_list }

    def get_api_key_info(self, api_key: str) -> dict:
        """
        Retrieve details of the given API key, including its bound user, status, and allowed operations.

        Args:
            api_key (str): The API key to look up.

        Returns:
            dict:
                - success: True, data: APIKeyInfo dictionary if found.
                - success: False, error: error message if not found.

        Constraints:
            - The input api_key must exist in the system.
        """
        info = self.api_keys.get(api_key)
        if info is None:
            return { "success": False, "error": "API key does not exist" }
        return { "success": True, "data": info }

    def list_templates_by_user(self, user_id: str) -> dict:
        """
        List all message templates owned or accessible by a specific user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageTemplateInfo],  # All templates owned by or accessible to this user
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. user does not exist
            }

        Constraints:
            - User must exist.
            - By default, user can access templates where owner_id == user_id.
            - (Extension point: If user has elevated/global permissions, could access more templates.)
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # By default, return templates owned by user
        result = [
            template
            for template in self.templates.values()
            if template["owner_id"] == user_id
        ]
    
        # Optionally expand for permissions (not specified in base env)
        # Example for global permission (uncomment if logic is desired)
        # if self.users[user_id].get("permission", "") == "admin":
        #     result = list(self.templates.values())
    
        return { "success": True, "data": result }

    def get_template_by_name(self, template_name: str, user_id: str) -> dict:
        """
        Retrieve template details (content, variables) by template name and user ID.

        Args:
            template_name (str): The name of the template to retrieve.
            user_id (str): The user ID of the template's owner.

        Returns:
            dict: {
                "success": True,
                "data": MessageTemplateInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only templates owned by `user_id` (owner_id) may be retrieved.
            - If no matching template is found, returns success False with error.
        """
        for template in self.templates.values():
            if template["owner_id"] == user_id and template["name"] == template_name:
                return {
                    "success": True,
                    "data": template
                }
        return {
            "success": False,
            "error": "Template not found"
        }

    def get_template_by_id(self, template_id: str) -> dict:
        """
        Retrieve the details of a message template given its template ID.

        Args:
            template_id (str): The unique identifier of the message template.

        Returns:
            dict: {
                "success": True,
                "data": MessageTemplateInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason: e.g., "Template not found"
            }

        Constraints:
            - The given template_id must exist in the platform.
            - No permission/access control is enforced in this method; raw lookup only.
        """
        template = self.templates.get(template_id)
        if template is None:
            return { "success": False, "error": "Template not found" }
        return { "success": True, "data": template }

    def list_template_variables(self, template_id: str) -> dict:
        """
        List the variable placeholders required for a given template.

        Args:
            template_id (str): The ID of the message template.

        Returns:
            dict: {
                "success": True,
                "data": List[str]   # list of template variable placeholders
            }
            or
            {
                "success": False,
                "error": str        # Reason for failure (e.g., template not found)
            }

        Constraints:
            - The template must exist.
        """
        template = self.templates.get(template_id)
        if not template:
            return { "success": False, "error": "Template not found" }
        variables = template.get("variables", [])
        return { "success": True, "data": variables }

    def validate_template_access(
        self,
        template_id: str,
        user_id: str = None,
        api_key: str = None
    ) -> dict:
        """
        Check if a user (via user_id or API key) is allowed to access a given template.

        Args:
            template_id (str): The ID of the template.
            user_id (str, optional): User id of the requestor.
            api_key (str, optional): API key for authentication (if given, user_id is ignored).

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if allowed to access, False otherwise
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Message templates are only accessible by their respective owners or with proper permissions.
            - API key (if given) must be active and valid.
            - Template must exist.
            - At least one of user_id or api_key must be provided.
        """
        # At least user_id or api_key
        if not user_id and not api_key:
            return {"success": False, "error": "Either user_id or api_key must be provided."}

        # Template existence
        template = self.templates.get(template_id)
        if not template:
            return {"success": False, "error": "Template not found."}

        # Resolve user_id from api_key if provided
        if api_key:
            api_info = self.api_keys.get(api_key)
            if not api_info:
                return {"success": False, "error": "API key not found."}
            if api_info["status"] != "active":
                return {"success": False, "error": "API key inactive or revoked."}
            # Optionally validate allowed_operation, if template access is more granular
            user_id = api_info["user_id"]

        # User existence
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        return {"success": True, "data": self._can_use_template(user_id, template)}

    def validate_api_key_permissions(self, api_key: str, operation: str) -> dict:
        """
        Validate if the given API key is active and permits the requested operation.

        Args:
            api_key (str): The API key string to check.
            operation (str): Operation name to validate permission for (e.g., "send_sms").

        Returns:
            dict: 
              - On success:
                {"success": True, "message": "API key is active and authorized for operation."}
              - On failure:
                {"success": False, "error": "<reason>"}

        Constraints:
            - API key must exist in platform.
            - Must have status=="active".
            - allowed_operation must include the requested operation.
        """
        api_info = self.api_keys.get(api_key)
        if not api_info:
            return {"success": False, "error": "API key not found."}
        if api_info.get("status") != "active":
            return {"success": False, "error": "API key is not active."}
        allowed_ops = api_info.get("allowed_operation", [])
        if operation not in allowed_ops:
            return {"success": False, "error": "Permission denied for operation."}
        return {"success": True, "message": "API key is active and authorized for operation."}

    def validate_phone_number(self, phone_number: str) -> dict:
        """
        Check if a given phone number meets platform and regulatory requirements.

        Args:
            phone_number (str): The phone number string to validate.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "valid": bool,
                    "reason": str
                }
            }

        Validation rules (platform typical):
            - Must be a non-empty string.
            - Must start with '+' (E.164 international format).
            - Must be followed by 8-15 digits (country code + subscriber).
            - No embedded spaces, letters, or symbols (besides leading '+').
        """
        return self._is_phone_number_valid(phone_number)

    def list_user_messages(self, user_id: str, status: Optional[str] = None) -> dict:
        """
        List all messages sent by a user, optionally filter by message status.

        Args:
            user_id (str): The user ID of the sender.
            status (Optional[str]): Filter messages by status ("pending", "sent", "delivered", "failed").
                                    If None, do not filter by status.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],  # List of messages sent by the user (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist.
            - If status is provided, must be one of the allowed message statuses.
        """

        # Validate user existence
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        allowed_statuses = {"pending", "sent", "delivered", "failed"}
        if status is not None and status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status: {status}" }

        filtered_messages = [
            msg for msg in self.messages.values()
            if msg.get("sender_id") == user_id and (status is None or msg.get("status") == status)
        ]

        return { "success": True, "data": filtered_messages }

    def get_message_by_id(self, message_id: str) -> dict:
        """
        Retrieve the full details and delivery status of a specific message event.

        Args:
            message_id (str): The unique identifier of the message event to query.

        Returns:
            dict: 
                {"success": True, "data": MessageInfo}  # if found
                {"success": False, "error": "Message not found"}  # if not found

        Constraints:
            - message_id must exist in the messages registry.
        """
        message = self.messages.get(message_id)
        if message is None:
            return {"success": False, "error": "Message not found"}
    
        return {"success": True, "data": message}

    def get_message_status(self, message_id: str) -> dict:
        """
        Get the current status ("pending", "sent", "delivered", or "failed") for a message.

        Args:
            message_id (str): The unique ID of the message.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "message_id": str,
                            "status": str
                        }
                    }
                On error:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The message must exist.
        """
        msg = self.messages.get(message_id)
        if not msg:
            return { "success": False, "error": "Message not found" }
        status = msg.get("status")
        if status is None:
            return { "success": False, "error": "Message status not found" }
        return { "success": True, "data": {"message_id": message_id, "status": status} }

    def list_messages_by_recipient(self, recipient_phone: str, user_id: str = None) -> dict:
        """
        List all messages sent to a specific phone number.
        If user_id is provided, only include messages sent by that user.

        Args:
            recipient_phone (str): The recipient phone number to filter messages for.
            user_id (str, optional): Restrict to messages sent by this user.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo]
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The recipient phone number must be valid per platform policy.
            - If user_id is specified but does not exist, returns empty result.
        """
        # Phone validation (assuming we have a validate_phone_number method that returns {success: True/False})
        phone_check = self.validate_phone_number(recipient_phone)
        if not phone_check.get("success", False) or not phone_check.get("data", {}).get("valid", False):
            return {"success": False, "error": "Invalid recipient phone number"}

        if user_id is not None and user_id not in self.users:
            # Could return an error, but better to just return empty in case it's used for search
            return {"success": True, "data": []}

        results = []
        for msg in self.messages.values():
            if msg.get("recipient_phone") != recipient_phone:
                continue
            if user_id is not None and msg.get("sender_id") != user_id:
                continue
            results.append(msg)

        return {"success": True, "data": results}

    def send_message_using_template(
        self,
        api_key: str,
        template_id: str,
        recipient_phone: str,
        parameters: Dict[str, str]
    ) -> dict:
        """
        Create and submit a new message for sending using a template and filled variables.

        Args:
            api_key (str): The API key of the sending user (must be active and allowed to send).
            template_id (str): The template to use (must be owned by user or permitted).
            recipient_phone (str): The phone number to send the message to (must be valid).
            parameters (Dict[str, str]): Variable assignments for the template (must exactly match required variables).

        Returns:
            dict: {
              "success": True,
              "message": "Submitted message <id> for delivery"
            }
            or {
              "success": False,
              "error": <reason>
            }

        Constraints:
            - API key must be valid, active, belong to sender, and allowed to send.
            - Template must exist and accessible to sender.
            - All template variables must be filled (no missing/extra).
            - Phone must be valid.
            - Message is recorded with status "pending".
        """

        # 1. API key validation
        api_key_info = self.api_keys.get(api_key)
        if not api_key_info:
            return {"success": False, "error": "Invalid API key"}
        if api_key_info["status"] != "active":
            return {"success": False, "error": "API key is not active"}
        allowed_ops = api_key_info.get("allowed_operation", [])
        if "send_message_using_template" not in allowed_ops and "send" not in allowed_ops:
            return {"success": False, "error": "API key not authorized to send messages"}
        user_id = api_key_info["user_id"]
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User not found for API key"}

        # 2. Template validation & access
        template = self.templates.get(template_id)
        if not template:
            return {"success": False, "error": "Template does not exist"}
        if not self._can_use_template(user_id, template):
            return {"success": False, "error": "Template access denied"}

        # 3. Template variable checks
        template_vars = template.get("variables", [])
        if set(parameters.keys()) != set(template_vars):
            missing = [v for v in template_vars if v not in parameters]
            extra = [k for k in parameters if k not in template_vars]
            parts = []
            if missing:
                parts.append(f"Missing variables: {', '.join(missing)}")
            if extra:
                parts.append(f"Unexpected variables: {', '.join(extra)}")
            return {"success": False, "error": "; ".join(parts)}

        # 4. Phone number validation (stub – real checker would be more complex)
        phone_check = self.validate_phone_number(recipient_phone)
        if not phone_check.get("success", False) or not phone_check.get("data", {}).get("valid", False):
            return {"success": False, "error": "Invalid recipient phone number"}

        # 5. Fill template
        content = template["content"]
        # Simple placeholder replacement: assume content uses {var} syntax
        try:
            content_filled = content.format(**parameters)
        except Exception as e:
            return {"success": False, "error": f"Template filling error: {str(e)}"}

        # 6. Message ID and record
        message_id = str(uuid.uuid4())
        msg_info = {
            "message_id": message_id,
            "sender_id": user_id,
            "recipient_phone": recipient_phone,
            "content": content_filled,
            "template_id": template_id,
            "status": "pending",    # initial state
            "sent_time": None,
            "scheduled_time": None,
            "delivery_report": None,
            "parameters_used": parameters.copy()
        }

        self.messages[message_id] = msg_info

        return {
            "success": True,
            "message": f"Submitted message {message_id} for delivery"
        }

    def send_custom_message(
        self, 
        api_key: str, 
        recipient_phone: str, 
        content: str,
        scheduled_time: str = None
    ) -> dict:
        """
        Submit and queue a one-off custom SMS (not using a template) using a validated API key.

        Args:
            api_key (str): The API key used for authentication and authorization.
            recipient_phone (str): The target phone number.
            content (str): The message content to send.
            scheduled_time (str, optional): Time to schedule the message (ISO8601). If None, send ASAP.

        Returns:
            dict: {
                "success": True,
                "message": "Message queued for sending",
                "message_id": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - API key must exist, active, and authorized for 'send_custom_message'.
            - Phone number must be valid.
            - Content must not be empty.
            - Sender is the user associated to the API key.
            - Message status will be 'pending' if scheduled_time is in future or sending is pending.
        """
        # Check API key exists and active
        api_info = self.api_keys.get(api_key)
        if not api_info:
            return { "success": False, "error": "Invalid API key" }
        if api_info["status"] != "active":
            return { "success": False, "error": "API key not active" }
        if "send_custom_message" not in api_info.get("allowed_operation", []):
            return { "success": False, "error": "API key not authorized for custom message sending" }

        user_id = api_info["user_id"]
        if user_id not in self.users:
            return { "success": False, "error": "Associated user not found" }

        # Validate phone number
        phone_check = self.validate_phone_number(recipient_phone)
        if not (isinstance(phone_check, dict) and phone_check.get("success") and phone_check.get("data", {}).get("valid", False)):
            error_msg = phone_check.get("data", {}).get("reason", phone_check.get("error", "Invalid phone number"))
            return { "success": False, "error": error_msg }

        # Content should not be empty
        if not content or not content.strip():
            return { "success": False, "error": "Message content cannot be empty" }

        # Prepare message record

        message_id = str(uuid.uuid4())
        now_iso = datetime.utcnow().isoformat() + 'Z'

        status = "pending"
        message_info = {
            "message_id": message_id,
            "sender_id": user_id,
            "recipient_phone": recipient_phone,
            "content": content,
            "template_id": None,
            "status": status,
            "sent_time": None,
            "scheduled_time": scheduled_time,
            "delivery_report": None,
            "parameters_used": None
        }

        # If scheduled_time is None or in the past, set as pending. 
        # Platform respects scheduling rule elsewhere (not sending before scheduled_time).

        self.messages[message_id] = message_info

        return {
            "success": True,
            "message": "Message queued for sending",
            "message_id": message_id
        }


    def schedule_message(
        self,
        api_key: str,
        recipient_phone: str,
        scheduled_time: str,
        content: Optional[str] = None,
        template_id: Optional[str] = None,
        parameters_used: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Schedule a message to be sent at a specified future time. The message can be custom
        (content) or use a template (template_id and parameters_used). Creation only: delivery
        occurs later when scheduled_time is reached.

        Args:
            api_key (str): API key to authenticate the sender.
            recipient_phone (str): Recipient's phone number.
            scheduled_time (str): Time (ISO8601 string) the message should be sent.
            content (Optional[str]): Message text if not using template.
            template_id (Optional[str]): If using a template, its id.
            parameters_used (Optional[Dict[str, str]]): Values for template variables.

        Returns:
            dict:
                On success:
                  {
                    "success": True,
                    "message": "Message scheduled successfully",
                    "message_id": <new_message_id>
                  }
                On failure:
                  {
                    "success": False,
                    "error": "reason"
                  }

        Constraints:
            - API key must be active and authorized for scheduling.
            - If template is used, only accessible by sender & all variables required.
            - Phone number must be valid.
            - scheduled_time must be in the future.
        """
        # 1. Validate API key
        api_info = self.api_keys.get(api_key)
        if not api_info:
            return {"success": False, "error": "Invalid API key"}
        if api_info["status"] != "active":
            return {"success": False, "error": "API key inactive"}
        if "schedule_message" not in api_info.get("allowed_operation", []):
            return {"success": False, "error": "API key not permitted to schedule message"}
        user_id = api_info["user_id"]
        if user_id not in self.users:
            return {"success": False, "error": "Associated user not found"}

        # 2. Validate recipient phone
        valid_phone = self.validate_phone_number(recipient_phone)
        if not valid_phone.get("success") or not valid_phone.get("data", {}).get("valid", False):
            return {"success": False, "error": f"Invalid recipient phone: {valid_phone.get('data', {}).get('reason', valid_phone.get('error', ''))}"}

        # 3. Check scheduled_time is in the future
        try:
            t_sched = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
        except Exception:
            return {"success": False, "error": "Invalid scheduled_time format (must be ISO8601)"}
        now = self._get_platform_current_time()
        if now is not None and t_sched <= now:
            return {"success": False, "error": "Scheduled time must be in the future"}

        # 4. Message body construction: template or custom
        if template_id:
            template = self.templates.get(template_id)
            if not template:
                return {"success": False, "error": "Template not found"}
            if not self._can_use_template(user_id, template):
                return {"success": False, "error": "You do not have access to this template"}
            required_vars = set(template.get("variables", []))
            provided_vars = set(parameters_used.keys() if parameters_used else [])
            missing = required_vars - provided_vars
            if missing:
                return {"success": False, "error": f"Missing template variable(s): {', '.join(missing)}"}
            # Compose content by substituting params (simple implementation)
            body = template["content"]
            try:
                body = body.format(**(parameters_used or {}))
            except Exception as e:
                return {"success": False, "error": f"Template filling error: {str(e)}"}
        else:
            if not content:
                return {"success": False, "error": "No message content or template provided"}
            body = content

        # 5. Generate a unique message_id
        message_id = str(uuid.uuid4())

        # 6. Insert record as 'pending'
        msg_info = {
            "message_id": message_id,
            "sender_id": user_id,
            "recipient_phone": recipient_phone,
            "content": body,
            "template_id": template_id,
            "status": "pending",
            "sent_time": None,
            "scheduled_time": t_sched.isoformat(),
            "delivery_report": None,
            "parameters_used": parameters_used if parameters_used else None
        }
        self.messages[message_id] = msg_info

        return {
            "success": True,
            "message": "Message scheduled successfully",
            "message_id": message_id
        }

    def update_message_status(
        self,
        message_id: str,
        new_status: str,
        delivery_report: str = None
    ) -> dict:
        """
        Update the delivery status and/or the delivery report of a specific message.

        Args:
            message_id (str): The unique message identifier to update.
            new_status (str): The new delivery status. Must be one of "pending", "sent", "delivered", "failed".
            delivery_report (str, optional): The delivery report to record (if any).

        Returns:
            dict:
                { "success": True, "message": "Message status updated to <status>." }
                or
                { "success": False, "error": <reason> }

        Constraints:
            - Only allows status values: "pending", "sent", "delivered", "failed".
            - Fails if the message_id does not exist.
            - Updates message status and delivery_report accordingly.
        """
        allowed_status = {"pending", "sent", "delivered", "failed"}
        if message_id not in self.messages:
            return {"success": False, "error": "Message not found."}

        if new_status not in allowed_status:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed: pending, sent, delivered, failed."}

        message = self.messages[message_id]
        message["status"] = new_status
        if delivery_report is not None:
            message["delivery_report"] = delivery_report

        return {"success": True, "message": f"Message status updated to {new_status}."}

    def record_delivery_report(self, message_id: str, delivery_report: str) -> dict:
        """
        Attach or update a delivery report/info for a message.

        Args:
            message_id (str): The unique ID of the message to update.
            delivery_report (str): The delivery report information to attach (may be any string).

        Returns:
            dict: {
                "success": True,
                "message": "Delivery report updated for message <message_id>"
            }
            or
            {
                "success": False,
                "error": "Message not found"
            }

        Constraints:
            - The message must exist in the platform.
            - The delivery report can be set or overwritten without restriction.
        """
        msg = self.messages.get(message_id)
        if not msg:
            return {"success": False, "error": "Message not found"}

        msg["delivery_report"] = delivery_report
        self.messages[message_id] = msg  # Save changes (for TypedDict mutation semantics)

        return {"success": True, "message": f"Delivery report updated for message {message_id}"}

    def create_template(
        self,
        owner_id: str,
        name: str,
        content: str,
        variables: list,
        creation_time: str = ""
    ) -> dict:
        """
        Add a new message template for a user.

        Args:
            owner_id (str): User ID of the template creator/owner.
            name (str): Name of the template (must be unique for the user).
            content (str): Template body text. May contain placeholders.
            variables (List[str]): List of variable names used in the template.
            creation_time (str, optional): Creation timestamp. If empty, leave as "".

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Template created",
                        "template_id": <generated_id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - owner_id must exist.
            - Template name must be unique for the user.
            - Template_id must be unique (generated).
            - Variable names must be non-empty strings.
        """
        # Check user exists
        if owner_id not in self.users:
            return {"success": False, "error": "owner_id (user) does not exist"}

        # Check uniqueness of name for this user
        for tmpl in self.templates.values():
            if tmpl["owner_id"] == owner_id and tmpl["name"] == name:
                return {"success": False, "error": "Template name already used by this user"}

        # Validate variable names
        if not isinstance(variables, list):
            return {"success": False, "error": "variables must be a list of non-empty strings"}
        for var in variables:
            if not isinstance(var, str) or var.strip() == "":
                return {"success": False, "error": "Variables must be non-empty strings"}

        # Generate a unique template_id
        base_id = f"{owner_id}_{name}"
        i = 1
        template_id = f"{base_id}"
        while template_id in self.templates:
            template_id = f"{base_id}_{i}"
            i += 1

        if not creation_time:
            creation_time = ""  # Placeholder, would normally use datetime.now()

        # Create template info
        template_info = {
            "template_id": template_id,
            "owner_id": owner_id,
            "name": name,
            "content": content,
            "creation_time": creation_time,
            "variables": variables
        }

        self.templates[template_id] = template_info

        return {"success": True, "message": "Template created", "template_id": template_id}

    def update_template(
        self,
        template_id: str,
        user_id: str,
        new_content: str = None,
        new_variables: list = None
    ) -> dict:
        """
        Edit the content or variable set of an existing message template.

        Args:
            template_id (str): The ID of the template to update.
            user_id (str): The ID of the user performing the update (must be owner).
            new_content (str, optional): The new message content (leave unchanged if None).
            new_variables (List[str], optional): The new list of template variables (leave unchanged if None).

        Returns:
            dict: {
                "success": True,
                "message": "Template updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        Constraints:
            - Only the owner of the template (user_id == owner_id) may update.
            - Template must exist.
            - If updating variables, must be a list of strings.
        """
        # Check existence
        template = self.templates.get(template_id)
        if template is None:
            return {"success": False, "error": "Template not found."}

        # Check owner permission
        if template["owner_id"] != user_id:
            return {"success": False, "error": "Permission denied."}

        # Validate and apply changes
        updated = False
        if new_content is not None:
            if not isinstance(new_content, str):
                return {"success": False, "error": "Content must be a string."}
            template["content"] = new_content
            updated = True
        if new_variables is not None:
            if not (isinstance(new_variables, list) and all(isinstance(v, str) for v in new_variables)):
                return {"success": False, "error": "Invalid variables list."}
            template["variables"] = new_variables
            updated = True

        if not updated:
            return {"success": False, "error": "No updates specified."}

        # If you want to add a last_modified field, do it here (not defined by schema)
        # template["last_modified"] = current_time()

        # Store back (not needed for mutable dict)
        self.templates[template_id] = template

        return {"success": True, "message": "Template updated."}

    def revoke_api_key(self, api_key: str) -> dict:
        """
        Disable (revoke) an API key so it is no longer usable for API operations.

        Args:
            api_key (str): The API key to be revoked.

        Returns:
            dict: 
                - success: True, message if operation succeeded (or already revoked)
                - success: False, error if api_key not found

        Constraints:
            - The API key must exist in the system.
            - Revocation is idempotent and will mark the status as "revoked".
        """
        if api_key not in self.api_keys:
            return { "success": False, "error": "API key not found" }
    
        # Already revoked?
        if self.api_keys[api_key]["status"] == "revoked":
            return { "success": True, "message": f"API key {api_key} is already revoked." }

        self.api_keys[api_key]["status"] = "revoked"
        return { "success": True, "message": f"API key {api_key} revoked successfully." }


    def rotate_api_key(self, user_id: str, old_api_key: str) -> Dict:
        """
        Generate and assign a new API key for a user, disabling an old one.

        Args:
            user_id (str): The user ID whose API key will be rotated.
            old_api_key (str): The API key to be replaced/disabled.

        Returns:
            dict: Success structure is
                {
                    "success": True,
                    "message": <description>,
                    "new_api_key": <the newly generated API key string>
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - The user with user_id must exist.
            - The old_api_key must exist, be active, and belong to the user.
            - The new API key must be unique.
        """

        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": f"User {user_id} does not exist." }

        # Check old_api_key exists
        if old_api_key not in self.api_keys:
            return { "success": False, "error": f"API key {old_api_key} does not exist." }

        api_key_info = self.api_keys[old_api_key]
        if api_key_info["user_id"] != user_id:
            return { "success": False, "error": "API key does not belong to the specified user." }

        # Generate a new unique API key string
        for _ in range(10):
            new_api_key = secrets.token_urlsafe(24)
            if new_api_key not in self.api_keys:
                break
        else:
            return { "success": False, "error": "Failed to generate a unique API key." }

        # Add the new key to api_keys
        self.api_keys[new_api_key] = {
            "api_key": new_api_key,
            "user_id": user_id,
            "status": "active",
            "allowed_operation": list(api_key_info.get("allowed_operation", []))
        }

        # Add the new key to user's credentials list
        if new_api_key not in self.users[user_id]["credentials"]:
            self.users[user_id]["credentials"].append(new_api_key)

        # Disable an active key; preserve already-nonactive statuses such as revoked/suspended.
        old_status = self.api_keys[old_api_key]["status"]
        if old_status == "active":
            self.api_keys[old_api_key]["status"] = "disabled"
            old_key_result = "disabled"
        else:
            old_key_result = f"left in {old_status} status"

        return {
            "success": True,
            "message": f"New API key {new_api_key} assigned to user {user_id}, old key {old_api_key} {old_key_result}.",
            "new_api_key": new_api_key
        }

    def delete_message(self, message_id: str) -> dict:
        """
        Remove a message event record by its unique message_id.
        (Assumed to be invoked by admin or per retention policy, no permission check.)

        Args:
            message_id (str): Unique identifier of the message to delete.

        Returns:
            dict:
                - success: True and informational message if deletion succeeds.
                - success: False and error reason if message is not found.
        Constraints:
            - The specified message_id must exist.
            - No exception will be raised; returns a result dictionary on any outcome.
        """
        if message_id not in self.messages:
            return { "success": False, "error": "Message not found." }

        del self.messages[message_id]
        return { "success": True, "message": f"Message {message_id} deleted." }


class SMSGatewayPlatform(BaseEnv):
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
            if key == "validate_phone_number":
                setattr(env, "_validate_phone_number_state", copy.deepcopy(value))
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_user_api_keys(self, **kwargs):
        return self._call_inner_tool('list_user_api_keys', kwargs)

    def get_api_key_info(self, **kwargs):
        return self._call_inner_tool('get_api_key_info', kwargs)

    def list_templates_by_user(self, **kwargs):
        return self._call_inner_tool('list_templates_by_user', kwargs)

    def get_template_by_name(self, **kwargs):
        return self._call_inner_tool('get_template_by_name', kwargs)

    def get_template_by_id(self, **kwargs):
        return self._call_inner_tool('get_template_by_id', kwargs)

    def list_template_variables(self, **kwargs):
        return self._call_inner_tool('list_template_variables', kwargs)

    def validate_template_access(self, **kwargs):
        return self._call_inner_tool('validate_template_access', kwargs)

    def validate_api_key_permissions(self, **kwargs):
        return self._call_inner_tool('validate_api_key_permissions', kwargs)

    def validate_phone_number(self, **kwargs):
        return self._call_inner_tool('validate_phone_number', kwargs)

    def list_user_messages(self, **kwargs):
        return self._call_inner_tool('list_user_messages', kwargs)

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def get_message_status(self, **kwargs):
        return self._call_inner_tool('get_message_status', kwargs)

    def list_messages_by_recipient(self, **kwargs):
        return self._call_inner_tool('list_messages_by_recipient', kwargs)

    def send_message_using_template(self, **kwargs):
        return self._call_inner_tool('send_message_using_template', kwargs)

    def send_custom_message(self, **kwargs):
        return self._call_inner_tool('send_custom_message', kwargs)

    def schedule_message(self, **kwargs):
        return self._call_inner_tool('schedule_message', kwargs)

    def update_message_status(self, **kwargs):
        return self._call_inner_tool('update_message_status', kwargs)

    def record_delivery_report(self, **kwargs):
        return self._call_inner_tool('record_delivery_report', kwargs)

    def create_template(self, **kwargs):
        return self._call_inner_tool('create_template', kwargs)

    def update_template(self, **kwargs):
        return self._call_inner_tool('update_template', kwargs)

    def revoke_api_key(self, **kwargs):
        return self._call_inner_tool('revoke_api_key', kwargs)

    def rotate_api_key(self, **kwargs):
        return self._call_inner_tool('rotate_api_key', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)
