# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class MailInfo(TypedDict):
    mail_id: str
    sender: str
    recipient: str
    subject: str
    timestamp: str
    body: str
    state: str  # "new" or "read"
    fold: str

class UserInfo(TypedDict):
    _id: str
    name: str
    email_add: str

class InboxInfo(TypedDict):
    _id: str
    list_of_emails: List[str]
    current_view: str  # e.g., "inbox", "sent", "archive"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Email Inbox Management System environment.

        Constraints:
        - Only emails with state = "new" are shown in the new email listing.
        - Accessing an email body may change its state from "new" to "read".
        - Each email must have a unique email_id.
        - Email must be associated with a valid recipient (user).
        """
        # Mails: {mail_id: MailInfo}
        self.mails: Dict[str, MailInfo] = {}
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Inboxes: {_id: InboxInfo}
        self.inboxes: Dict[str, InboxInfo] = {}

    @staticmethod
    def _mail_listing_view(mail: MailInfo) -> dict:
        return {
            "mail_id": mail["mail_id"],
            "sender": mail["sender"],
            "recipient": mail["recipient"],
            "subject": mail["subject"],
            "timestamp": mail["timestamp"],
            "state": mail["state"],
            "fold": mail["fold"],
        }

    def _find_inbox_id_for_recipient(self, recipient_user_id: str, recipient_email: str) -> str | None:
        if recipient_user_id in self.inboxes:
            return recipient_user_id

        for inbox_id, inbox in self.inboxes.items():
            if inbox.get("_id") == recipient_user_id:
                return inbox_id

        candidate_inbox_ids: List[str] = []
        for inbox_id, inbox in self.inboxes.items():
            for existing_mail_id in inbox.get("list_of_emails", []):
                existing_mail = self.mails.get(existing_mail_id)
                if existing_mail and existing_mail.get("recipient") == recipient_email:
                    candidate_inbox_ids.append(inbox_id)
                    break

        unique_candidates = list(dict.fromkeys(candidate_inbox_ids))
        if len(unique_candidates) == 1:
            return unique_candidates[0]

        return None

    def get_user_by_email(self, email_add: str) -> dict:
        """
        Retrieve UserInfo for a given email address.

        Args:
            email_add (str): The email address to search for.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # The user's info if found
            }
            or
            {
                "success": False,
                "error": str,  # If no user matches the email address
            }

        Constraints:
            - The email address is assumed unique per user.
        """
        for user in self.users.values():
            if user["email_add"] == email_add:
                return { "success": True, "data": user }

        return { "success": False, "error": "User with the given email address does not exist." }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve UserInfo by the user's unique _id.

        Args:
            _id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # User information if found
            }
            or
            {
                "success": False,
                "error": str  # If user is not found
            }

        Constraints:
            - The _id must exist in the user registry (self.users).
        """
        user = self.users.get(_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def get_inbox_for_user(self, user_id: str) -> dict:
        """
        Retrieve the InboxInfo for a given user _id.

        Args:
            user_id (str): The _id of the user.

        Returns:
            dict: 
                { "success": True, "data": InboxInfo }
                or
                { "success": False, "error": <reason> }

        Constraints:
            - The user must exist.
            - The inbox for that user must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if user_id not in self.inboxes:
            return {"success": False, "error": "Inbox for user does not exist"}

        return {"success": True, "data": self.inboxes[user_id]}

    def list_inbox_emails(self, inbox_id: str) -> dict:
        """
        Get a list of all email metadata currently in an inbox.

        Args:
            inbox_id (str): The unique identifier of the inbox.

        Returns:
            dict: {
                "success": True,
                "data": List[MailInfo],  # List of mail metadata found in the inbox.
            }
            OR
            {
                "success": False,
                "error": str,  # Error description (e.g., inbox not found).
            }

        Constraints:
            - Only valid mail_ids present in the system are returned (missing/corrupt references ignored).
        """
        inbox = self.inboxes.get(inbox_id)
        if not inbox:
            return {"success": False, "error": "Inbox not found"}

        email_metadata = []
        for mail_id in inbox["list_of_emails"]:
            mail = self.mails.get(mail_id)
            if mail:
                email_metadata.append(mail)

        return {"success": True, "data": email_metadata}

    def list_new_emails(self, inbox_id: str) -> dict:
        """
        List unread emails in the given inbox using safe listing metadata only.

        Args:
            inbox_id (str): The ID of the inbox.

        Returns:
            dict:
                - On success: { "success": True, "data": List[dict] }
                - On failure: { "success": False, "error": str }
    
        Constraints:
            - Only return emails with state == "new".
            - The inbox must exist.
            - Email IDs referenced in the inbox must exist in the mail store.
            - Returned entries include mail_id, sender, recipient, subject, timestamp, state, and fold.
            - Returned entries do not include the email body and do not change read state.
        """
        if inbox_id not in self.inboxes:
            return { "success": False, "error": "Inbox not found" }
    
        inbox = self.inboxes[inbox_id]
        result = [
            self._mail_listing_view(self.mails[mail_id])
            for mail_id in inbox["list_of_emails"]
            if mail_id in self.mails and self.mails[mail_id]["state"] == "new"
        ]
        return { "success": True, "data": result }

    def get_email_metadata(self, mail_id: str) -> dict:
        """
        Retrieve metadata (sender, subject, timestamp, state) for the email with the given mail_id.
        Does NOT return the body of the email.

        Args:
            mail_id (str): The unique identifier for the email.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "sender": str,
                    "subject": str,
                    "timestamp": str,
                    "state": str,
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason email not found
            }

        Constraints:
            - mail_id must exist in the system.
            - No email body is returned.
        """
        mail = self.mails.get(mail_id)
        if not mail:
            return { "success": False, "error": "Email does not exist" }

        metadata = {
            "sender": mail["sender"],
            "subject": mail["subject"],
            "timestamp": mail["timestamp"],
            "state": mail["state"],
        }

        return { "success": True, "data": metadata }

    def get_email_by_id(self, mail_id: str) -> dict:
        """
        Retrieve the full MailInfo (including body and metadata) for a given mail_id.
        If the mail is in 'new' state, its state is changed to 'read' as a side-effect.

        Args:
            mail_id (str): The unique identifier for the email.

        Returns:
            dict:
                - On success: {"success": True, "data": MailInfo}
                - On failure: {"success": False, "error": <str>}

        Constraints:
            - mail_id must exist.
            - If mail state is 'new', update to 'read'.
        """
        mail = self.mails.get(mail_id)
        if not mail:
            return { "success": False, "error": "Email does not exist" }

        # If state is 'new', mark as 'read' (in-place update)
        if mail["state"] == "new":
            mail["state"] = "read"
            self.mails[mail_id] = mail

        return { "success": True, "data": mail }

    def list_emails_by_fold(self, user_id: str, fold: str) -> dict:
        """
        List all emails in a specified folder (e.g., "inbox", "sent", "archive") for the user.

        Args:
            user_id (str): The unique identifier for the user (Inbox _id).
            fold (str): The target folder name.

        Returns:
            dict: {
                "success": True,
                "data": List[MailInfo],  # may be empty if no emails found
            }
            or {
                "success": False,
                "error": str  # User or inbox not found
            }

        Constraints:
            - User and inbox must exist.
            - Only emails found in the user's inbox and with the specified fold are included.
        """

        if user_id not in self.inboxes:
            return {"success": False, "error": "Inbox for specified user does not exist"}

        inbox = self.inboxes[user_id]
        email_ids = inbox["list_of_emails"]

        result = []
        for mail_id in email_ids:
            mail = self.mails.get(mail_id)
            if mail is not None and mail["fold"] == fold:
                result.append(mail)

        return {"success": True, "data": result}

    def mark_email_as_read(self, mail_id: str) -> dict:
        """
        Updates the state of a mail from "new" to "read".
        Args:
            mail_id (str): The unique identifier for the mail.
        Returns:
            dict: {
                "success": True, "message": "Mail marked as read."
            }
            or
            {
                "success": False, "error": "Mail not found."
            }
        Constraints:
            - The mail must exist.
            - Idempotent: If mail is already "read", returns success.
        """
        mail = self.mails.get(mail_id)
        if not mail:
            return {"success": False, "error": "Mail not found."}

        if mail["state"] == "new":
            mail["state"] = "read"

        return {"success": True, "message": "Mail marked as read."}

    def change_email_fold(self, mail_id: str, new_fold: str) -> dict:
        """
        Move an email to a different folder by updating its 'fold' attribute.

        Args:
            mail_id (str): The unique identifier of the email to move.
            new_fold (str): The name of the target folder (e.g., 'archive', 'inbox', etc.).

        Returns:
            dict: {
                "success": True,
                "message": str  # Operation success message
            }
            or
            {
                "success": False,
                "error": str  # Explanation of failure, e.g., email not found
            }

        Constraints:
            - The mail_id must correspond to an existing email.
            - Folder name is a free string; no enforced set in current environment.
        """
        if mail_id not in self.mails:
            return {"success": False, "error": "Email not found"}

        self.mails[mail_id]['fold'] = new_fold
        return {
            "success": True,
            "message": f"Email '{mail_id}' moved to folder '{new_fold}'."
        }

    def delete_email(self, mail_id: str) -> dict:
        """
        Remove an email from all inboxes and from the system.

        Args:
            mail_id (str): Unique identifier of the email to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Email deleted successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Email must exist.
            - Remove email from all inboxes' list_of_emails.
            - Email must be fully deleted from the system.
        """
        if mail_id not in self.mails:
            return { "success": False, "error": "Email not found." }

        # Remove from all inboxes
        for inbox in self.inboxes.values():
            if mail_id in inbox["list_of_emails"]:
                inbox["list_of_emails"].remove(mail_id)

        # Remove from the main mail store
        del self.mails[mail_id]

        return { "success": True, "message": "Email deleted successfully." }

    def add_email_to_inbox(self, mail_info: dict) -> dict:
        """
        Insert a new email into a user's inbox, enforcing:
            - mail_id is unique
            - recipient is a valid user
            - inbox for recipient exists and is updated
            - all required fields are present

        Args:
            mail_info (dict): Dictionary containing mail attributes. Expected keys:
                'mail_id', 'sender', 'recipient', 'subject', 'timestamp', 'body', 'state', 'fold'

        Returns:
            dict: {
                "success": True,
                "message": "Email successfully added to inbox."
            }
            or
            {
                "success": False,
                "error": "...reason..."
            }
        """
        required_fields = ["mail_id", "sender", "recipient", "subject", "timestamp", "body", "state", "fold"]
        missing = [field for field in required_fields if field not in mail_info]
        if missing:
            return {"success": False, "error": f"Missing required fields: {', '.join(missing)}"}

        mail_id = mail_info["mail_id"]
        recipient = mail_info["recipient"]

        # Check mail_id uniqueness
        if mail_id in self.mails:
            return {"success": False, "error": "mail_id already exists"}

        # Check recipient user exists
        recipient_user_id = None
        for uid, user in self.users.items():
            if user["email_add"] == recipient:
                recipient_user_id = uid
                break
        if not recipient_user_id:
            return {"success": False, "error": "Recipient user does not exist"}

        # Check inbox for recipient exists
        recipient_inbox_id = self._find_inbox_id_for_recipient(recipient_user_id, recipient)
        if not recipient_inbox_id:
            return {"success": False, "error": "Inbox for recipient does not exist"}

        # Insert mail record
        self.mails[mail_id] = mail_info.copy()

        # Insert mail_id into inbox
        if mail_id not in self.inboxes[recipient_inbox_id]["list_of_emails"]:
            self.inboxes[recipient_inbox_id]["list_of_emails"].append(mail_id)

        return {"success": True, "message": "Email successfully added to inbox."}

    def set_inbox_view(self, inbox_id: str, new_view: str) -> dict:
        """
        Change the user's inbox current_view to a specified value ("inbox", "sent", "archive").

        Args:
            inbox_id (str): The identifier of the inbox to modify.
            new_view (str): The target view value. Expected: "inbox", "sent", "archive".

        Returns:
            dict: {
                "success": True,
                "message": "Inbox view updated to <new_view>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Inbox with given id must exist.
            - new_view should be one of "inbox", "sent", "archive".
        """
        allowed_views = {"inbox", "sent", "archive"}
        if inbox_id not in self.inboxes:
            return {"success": False, "error": "Inbox not found."}
        if new_view not in allowed_views:
            return {"success": False, "error": f"Invalid view. Allowed views: {', '.join(allowed_views)}."}
        self.inboxes[inbox_id]["current_view"] = new_view
        return {"success": True, "message": f"Inbox view updated to {new_view}."}


class EmailInboxManagementSystem(BaseEnv):
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

    def get_user_by_email(self, **kwargs):
        return self._call_inner_tool('get_user_by_email', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_inbox_for_user(self, **kwargs):
        return self._call_inner_tool('get_inbox_for_user', kwargs)

    def list_inbox_emails(self, **kwargs):
        return self._call_inner_tool('list_inbox_emails', kwargs)

    def list_new_emails(self, **kwargs):
        return self._call_inner_tool('list_new_emails', kwargs)

    def get_email_metadata(self, **kwargs):
        return self._call_inner_tool('get_email_metadata', kwargs)

    def get_email_by_id(self, **kwargs):
        return self._call_inner_tool('get_email_by_id', kwargs)

    def list_emails_by_fold(self, **kwargs):
        return self._call_inner_tool('list_emails_by_fold', kwargs)

    def mark_email_as_read(self, **kwargs):
        return self._call_inner_tool('mark_email_as_read', kwargs)

    def change_email_fold(self, **kwargs):
        return self._call_inner_tool('change_email_fold', kwargs)

    def delete_email(self, **kwargs):
        return self._call_inner_tool('delete_email', kwargs)

    def add_email_to_inbox(self, **kwargs):
        return self._call_inner_tool('add_email_to_inbox', kwargs)

    def set_inbox_view(self, **kwargs):
        return self._call_inner_tool('set_inbox_view', kwargs)
