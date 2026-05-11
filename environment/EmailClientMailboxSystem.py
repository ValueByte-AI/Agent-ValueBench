# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import datetime
import time
import uuid



class UserInfo(TypedDict):
    _id: str
    name: str
    email_add: str

class MailboxInfo(TypedDict):
    mailbox_id: str
    name: str
    user_id: str

class MailInfo(TypedDict):
    mail_id: str
    sender: str
    receiver: str
    subject: str
    body: str
    timestamp: str
    mailbox_id: str
    read_sta: bool  # read status: True if read, False if unread

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Mailboxes: {mailbox_id: MailboxInfo}
        self.mailboxes: Dict[str, MailboxInfo] = {}
        # Mails: {mail_id: MailInfo}
        self.mails: Dict[str, MailInfo] = {}
        self._generated_mail_seq: int = 0

        # ==== Constraints and notes ====
        # - Each email is assigned to exactly one mailbox for a given user (MailInfo.mailbox_id; mailbox's user_id).
        # - Mailboxes must belong to a single user (MailboxInfo.user_id).
        # - Only emails in the Inbox mailbox are counted for this task.
        # - Deleted emails may be moved to the Trash mailbox, not permanently erased until further action.

    @staticmethod
    def _parse_mail_timestamp(value: str):
        if not isinstance(value, str):
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _next_generated_timestamp(self) -> str:
        latest = None
        for mail in self.mails.values():
            parsed = self._parse_mail_timestamp(mail.get("timestamp"))
            if parsed is not None and (latest is None or parsed > latest):
                latest = parsed
        if latest is None:
            latest = datetime.datetime(2023, 1, 1, 0, 0, 0)
        return (latest + datetime.timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _next_generated_mail_ids(self, sender_id: str, receiver_id: str):
        seq = self._generated_mail_seq + 1
        while True:
            sender_candidate = f"{sender_id}_sent_{seq:06d}"
            receiver_candidate = f"{receiver_id}_inbox_{seq:06d}"
            if sender_candidate not in self.mails and receiver_candidate not in self.mails:
                self._generated_mail_seq = seq
                return sender_candidate, receiver_candidate
            seq += 1

    def get_user_by_name(self, name: str) -> dict:
        """
        Get user information dictionary by user name.

        Args:
            name (str): The exact name of the user to search for.

        Returns:
            dict: 
            - success True: {"success": True, "data": UserInfo}, if a user is found with the given name
            - success False: {"success": False, "error": "User not found"}, if no such user exists

        Notes:
            - If multiple users have the same name, returns the first one found.
        """
        for user_info in self.users.values():
            if user_info["name"] == name:
                return { "success": True, "data": user_info }
        return { "success": False, "error": "User not found" }

    def get_user_by_email(self, email_address: str) -> dict:
        """
        Retrieve user info by email address.

        Args:
            email_address (str): The email address to search for.

        Returns:
            dict:
                - On success: {"success": True, "data": UserInfo}
                - On failure: {"success": False, "error": "User with that email not found"}

        Constraints:
            - Email addresses are unique to each user.
        """
        for user in self.users.values():
            if user["email_add"] == email_address:
                return {"success": True, "data": user}
        return {"success": False, "error": "User with that email not found"}

    def list_user_mailboxes(self, user_id: str) -> dict:
        """
        List all mailboxes (folders) belonging to a specific user.

        Args:
            user_id (str): The unique user identifier.

        Returns:
            dict: 
                { "success": True, "data": List[MailboxInfo] }
                or
                { "success": False, "error": str }
        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_mailboxes = [
            mailbox_info for mailbox_info in self.mailboxes.values()
            if mailbox_info["user_id"] == user_id
        ]

        return {"success": True, "data": user_mailboxes}

    def get_mailbox_by_name(self, user_id: str, mailbox_name: str) -> dict:
        """
        Retrieve a mailbox (folder) for a given user by its name.

        Args:
            user_id (str): The user identifier.
            mailbox_name (str): The name of the mailbox/folder (e.g., 'Inbox', 'Sent', 'Trash').

        Returns:
            dict: 
                - On success:
                    {"success": True, "data": MailboxInfo}
                - On failure:
                    {"success": False, "error": str}

        Constraints:
            - Mailboxes must belong to a single user (MailboxInfo.user_id = user_id).
            - Mailbox name must match exactly.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        for mailbox in self.mailboxes.values():
            if mailbox["user_id"] == user_id and mailbox["name"] == mailbox_name:
                return {"success": True, "data": mailbox}

        return {"success": False, "error": "Mailbox not found for user"}

    def list_emails_in_mailbox(self, mailbox_id: str) -> dict:
        """
        List all emails assigned to a specific mailbox.

        Args:
            mailbox_id (str): The ID of the mailbox/folder.

        Returns:
            dict: {
                "success": True,
                "data": List[MailInfo]  # List of mails in this mailbox (empty list if none)
            }
            or
            {
                "success": False,
                "error": str  # If mailbox does not exist
            }

        Constraints:
            - Mailbox with the given ID must exist.
            - All emails listed will have MailInfo.mailbox_id == mailbox_id.
        """
        if mailbox_id not in self.mailboxes:
            return {"success": False, "error": "Mailbox does not exist"}

        emails = [
            mail_info for mail_info in self.mails.values()
            if mail_info["mailbox_id"] == mailbox_id
        ]
        return {"success": True, "data": emails}

    def count_emails_in_mailbox(self, mailbox_id: str) -> dict:
        """
        Return the total number of emails in a given mailbox.

        Args:
            mailbox_id (str): The unique identifier of the mailbox folder.

        Returns:
            dict:
                { "success": True, "data": int }             # On success, count of emails in the mailbox
                { "success": False, "error": str }           # If mailbox does not exist

        Constraints:
            - The mailbox_id must exist in the system.
            - Counts all emails where mail.mailbox_id == mailbox_id.
        """
        if mailbox_id not in self.mailboxes:
            return { "success": False, "error": "Mailbox does not exist" }
        count = sum(1 for mail in self.mails.values() if mail["mailbox_id"] == mailbox_id)
        return { "success": True, "data": count }

    def list_unread_emails_in_mailbox(self, mailbox_id: str) -> dict:
        """
        List all unread emails in the specified mailbox.

        Args:
            mailbox_id (str): The ID of the mailbox to search in.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[MailInfo],  # List of all unread emails in the mailbox
                }
                On failure: {
                    "success": False,
                    "error": str,  # Error message, e.g., mailbox does not exist
                }

        Constraints:
            - The mailbox must exist.
            - Only mails with mail_info.read_sta == False are included.
        """
        if mailbox_id not in self.mailboxes:
            return { "success": False, "error": "Mailbox not found" }
    
        unread_mails = [
            mail_info
            for mail_info in self.mails.values()
            if mail_info["mailbox_id"] == mailbox_id and not mail_info["read_sta"]
        ]
        return { "success": True, "data": unread_mails }

    def count_unread_emails_in_mailbox(self, mailbox_id: str) -> dict:
        """
        Count the number of unread emails in the specified mailbox.

        Args:
            mailbox_id (str): The identifier for the mailbox.

        Returns:
            dict: {
                "success": True,
                "data": int    # The count of unread emails
            }
            or
            {
                "success": False,
                "error": str   # Description, e.g. mailbox does not exist
            }

        Constraints:
            - The specified mailbox must exist.
            - Only mails with read_sta == False (unread) are counted.
        """
        if mailbox_id not in self.mailboxes:
            return { "success": False, "error": "Mailbox does not exist" }

        unread_count = sum(
            1 for mail in self.mails.values() 
            if mail["mailbox_id"] == mailbox_id and not mail["read_sta"]
        )

        return { "success": True, "data": unread_count }

    def get_email_metadata(self, mail_id: str) -> dict:
        """
        Retrieve metadata (subject, sender, timestamp, read status) for a given email.

        Args:
            mail_id (str): The unique identifier of the email.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": {
                        "subject": str,
                        "sender": str,
                        "timestamp": str,
                        "read_sta": bool
                    }
                }
                On error,
                {
                    "success": False,
                    "error": str  # e.g. "Email not found."
                }

        Constraints:
            - The email with the given mail_id must exist.
        """
        mail = self.mails.get(mail_id)
        if mail is None:
            return {"success": False, "error": "Email not found."}

        metadata = {
            "subject": mail["subject"],
            "sender": mail["sender"],
            "timestamp": mail["timestamp"],
            "read_sta": mail["read_sta"]
        }
        return {"success": True, "data": metadata}

    def get_email_by_id(self, mail_id: str) -> dict:
        """
        Retrieve full detail of an email by its mail_id.

        Args:
            mail_id (str): The unique ID of the email to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": MailInfo
            } on success, or
            {
                "success": False,
                "error": str  # Reason (e.g. 'Email not found')
            } on error.

        Constraints:
            - The mail must exist in the system.
        """
        if mail_id not in self.mails:
            return { "success": False, "error": "Email not found" }

        return { "success": True, "data": self.mails[mail_id] }

    def move_email_to_mailbox(self, mail_id: str, target_mailbox_id: str) -> dict:
        """
        Move an email to a different mailbox (e.g., Inbox → Trash for delete).

        Args:
            mail_id (str): The unique identifier of the email to be moved.
            target_mailbox_id (str): The target mailbox's identifier.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Email moved to mailbox 'NAME'." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - mail_id must exist.
            - target_mailbox_id must exist.
            - Both the current and target mailbox must belong to the same user.
        """
        # Check that the email exists
        if mail_id not in self.mails:
            return { "success": False, "error": "Email does not exist" }
        mail = self.mails[mail_id]
    
        # Check that the target mailbox exists
        if target_mailbox_id not in self.mailboxes:
            return { "success": False, "error": "Target mailbox does not exist" }
        target_mailbox = self.mailboxes[target_mailbox_id]
    
        # Check that the mail's current mailbox exists (data integrity)
        current_mailbox_id = mail["mailbox_id"]
        if current_mailbox_id not in self.mailboxes:
            return { "success": False, "error": "Email's current mailbox does not exist (data error)" }
        current_mailbox = self.mailboxes[current_mailbox_id]
    
        # Ensure both mailboxes belong to the same user
        if current_mailbox["user_id"] != target_mailbox["user_id"]:
            return { "success": False, "error": "Cannot move email to a mailbox owned by a different user" }
    
        # If already in the target mailbox, do not move
        if mail["mailbox_id"] == target_mailbox_id:
            return { "success": True, "message": f"Email already in mailbox '{target_mailbox['name']}'." }
    
        # Move the email
        mail["mailbox_id"] = target_mailbox_id
        self.mails[mail_id] = mail  # Update in storage (not strictly needed for dict ref)
    
        return { "success": True, "message": f"Email moved to mailbox '{target_mailbox['name']}'." }

    def mark_email_as_read(self, mail_id: str) -> dict:
        """
        Set the read status of a specific email to True.

        Args:
            mail_id (str): The unique identifier of the email to be marked as read.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Email marked as read"}
                On failure:
                    {"success": False, "error": <reason string>}

        Constraints:
            - The provided mail_id must exist in the system.
        """
        mail = self.mails.get(mail_id)
        if mail is None:
            return {"success": False, "error": "Email not found"}

        mail["read_sta"] = True
        return {"success": True, "message": "Email marked as read"}

    def mark_email_as_unread(self, mail_id: str) -> dict:
        """
        Set the read status of a specific email (by mail_id) to False.

        Args:
            mail_id (str): The unique ID of the email to update.

        Returns:
            dict: {
                "success": True,
                "message": "Email marked as unread."
            }
            or
            {
                "success": False,
                "error": "Email not found"
            }

        Constraints:
            - The mail_id must correspond to an existing email.
            - Operation is idempotent (multiple calls have same effect).
        """
        mail = self.mails.get(mail_id)
        if mail is None:
            return { "success": False, "error": "Email not found" }
        mail["read_sta"] = False
        return { "success": True, "message": "Email marked as unread." }

    def compose_and_send_email(
        self,
        sender_email: str,
        receiver_email: str,
        subject: str,
        body: str
    ) -> dict:
        """
        Create and send an email from sender to receiver.

        Args:
            sender_email (str): The sender's email address.
            receiver_email (str): The recipient's email address.
            subject (str): The email subject text.
            body (str): The email message body.

        Returns:
            dict: 
              - On success: {
                  "success": True,
                  "message": "Email sent successfully",
                  "mail_id": <mail_id>  # Mail ID of sent email object (sender's copy)
              }
              - On failure: {
                  "success": False,
                  "error": <reason>
              }

        Constraints:
            - Sender and receiver must exist in the system.
            - Sender must have a "Sent" mailbox; receiver must have an "Inbox" mailbox.
            - An email is stored as two separate objects (one in each user's mailbox).
            - Sent copy is 'read', inbox copy is 'unread'.
        """
        # --- Look up sender ---
        sender = None
        for user in self.users.values():
            if user["email_add"] == sender_email:
                sender = user
                break
        if not sender:
            return {"success": False, "error": "Sender not found"}

        # --- Look up receiver ---
        receiver = None
        for user in self.users.values():
            if user["email_add"] == receiver_email:
                receiver = user
                break
        if not receiver:
            return {"success": False, "error": "Receiver not found"}

        sender_id = sender["_id"]
        receiver_id = receiver["_id"]

        # --- Locate 'Sent' mailbox for sender ---
        sent_mailbox = None
        for mailbox in self.mailboxes.values():
            if mailbox["user_id"] == sender_id and mailbox["name"].lower() == "sent":
                sent_mailbox = mailbox
                break
        if not sent_mailbox:
            return {"success": False, "error": "Sender does not have a 'Sent' mailbox"}

        # --- Locate 'Inbox' mailbox for receiver ---
        inbox_mailbox = None
        for mailbox in self.mailboxes.values():
            if mailbox["user_id"] == receiver_id and mailbox["name"].lower() == "inbox":
                inbox_mailbox = mailbox
                break
        if not inbox_mailbox:
            return {"success": False, "error": "Receiver does not have an 'Inbox' mailbox"}

        # --- Generate deterministic, scenario-local mail IDs and timestamps ---
        mail_id_sender, mail_id_receiver = self._next_generated_mail_ids(sender_id, receiver_id)
        timestamp = self._next_generated_timestamp()

        # --- Create sender's sent mail object (read) ---
        mail_info_sent: MailInfo = {
            "mail_id": mail_id_sender,
            "sender": sender_email,
            "receiver": receiver_email,
            "subject": subject,
            "body": body,
            "timestamp": timestamp,
            "mailbox_id": sent_mailbox["mailbox_id"],
            "read_sta": True
        }
        self.mails[mail_id_sender] = mail_info_sent

        # --- Create receiver's inbox mail object (unread) ---
        mail_info_inbox: MailInfo = {
            "mail_id": mail_id_receiver,
            "sender": sender_email,
            "receiver": receiver_email,
            "subject": subject,
            "body": body,
            "timestamp": timestamp,
            "mailbox_id": inbox_mailbox["mailbox_id"],
            "read_sta": False
        }
        self.mails[mail_id_receiver] = mail_info_inbox

        return {
            "success": True,
            "message": "Email sent successfully",
            "mail_id": mail_id_sender
        }

    def permanently_delete_email(self, mail_id: str) -> dict:
        """
        Permanently deletes an email from the system, but only if it is currently in a mailbox named "Trash".
    
        Args:
            mail_id (str): The unique identifier of the email to be permanently deleted.
    
        Returns:
            dict: {
                "success": True,
                "message": "Email permanently deleted."
            }
            or
            {
                "success": False,
                "error": Error message describing what failed.
            }
    
        Constraints:
            - Email must exist.
            - Associated mailbox must exist and must be named "Trash".
            - Only then will the email be deleted from storage.
        """
        mail = self.mails.get(mail_id)
        if not mail:
            return { "success": False, "error": "Email does not exist." }
    
        mailbox_id = mail["mailbox_id"]
        mailbox = self.mailboxes.get(mailbox_id)
        if not mailbox:
            return { "success": False, "error": "Mailbox does not exist for this email." }
    
        if mailbox["name"].lower() != "trash":
            return { 
                "success": False, 
                "error": "Email must be in Trash before permanent deletion." 
            }
    
        del self.mails[mail_id]
        return { "success": True, "message": "Email permanently deleted." }

    def create_mailbox(self, user_id: str, mailbox_name: str) -> dict:
        """
        Add a new mailbox (folder) for a user.

        Args:
            user_id (str): User identifier to own the mailbox.
            mailbox_name (str): Name of the mailbox/folder.

        Returns:
            dict: {
                "success": True,
                "message": "Mailbox created for user."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must exist.
            - mailbox_name must not be empty.
            - mailbox_name must be unique for this user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not mailbox_name or not mailbox_name.strip():
            return { "success": False, "error": "Mailbox name cannot be empty" }
        # Check uniqueness of mailbox name for the user
        for mb in self.mailboxes.values():
            if mb["user_id"] == user_id and mb["name"].lower() == mailbox_name.lower():
                return { "success": False, "error": f"Mailbox '{mailbox_name}' already exists for user" }
        # Generate mailbox_id (ensure uniqueness)
        mailbox_id = str(uuid.uuid4())
        self.mailboxes[mailbox_id] = {
            "mailbox_id": mailbox_id,
            "name": mailbox_name,
            "user_id": user_id
        }
        return { "success": True, "message": f"Mailbox '{mailbox_name}' created for user." }

    def delete_mailbox(self, mailbox_id: str) -> dict:
        """
        Remove an existing mailbox identified by mailbox_id, if allowed.

        Args:
            mailbox_id (str): The identifier of the mailbox to delete.

        Returns:
            dict: 
                - { "success": True,  "message": "Mailbox deleted." }
                - { "success": False, "error": "<reason>" }

        Constraints / Rules:
            - System mailboxes (Inbox, Sent, Trash) cannot be deleted.
            - Mailbox must exist.
            - Mailbox must be empty (no mails assigned to it).
        """
        mailbox = self.mailboxes.get(mailbox_id)
        if not mailbox:
            return { "success": False, "error": "Mailbox does not exist." }

        if mailbox["name"] in ["Inbox", "Sent", "Trash"]:
            return { "success": False, "error": f"Cannot delete system mailbox '{mailbox['name']}'." }

        # Check if mailbox contains any email
        for mail in self.mails.values():
            if mail["mailbox_id"] == mailbox_id:
                return { "success": False, "error": "Cannot delete mailbox: mailbox is not empty." }

        del self.mailboxes[mailbox_id]
        return { "success": True, "message": "Mailbox deleted." }


class EmailClientMailboxSystem(BaseEnv):
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
        init_config = copy.deepcopy(init_config)
        for state_key, id_field in (
            ("users", "_id"),
            ("mailboxes", "mailbox_id"),
            ("mails", "mail_id"),
        ):
            records = init_config.get(state_key)
            if isinstance(records, dict):
                init_config[state_key] = {
                    (record.get(id_field) if isinstance(record, dict) and record.get(id_field) else key): record
                    for key, record in records.items()
                }
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

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_email(self, **kwargs):
        return self._call_inner_tool('get_user_by_email', kwargs)

    def list_user_mailboxes(self, **kwargs):
        return self._call_inner_tool('list_user_mailboxes', kwargs)

    def get_mailbox_by_name(self, **kwargs):
        return self._call_inner_tool('get_mailbox_by_name', kwargs)

    def list_emails_in_mailbox(self, **kwargs):
        return self._call_inner_tool('list_emails_in_mailbox', kwargs)

    def count_emails_in_mailbox(self, **kwargs):
        return self._call_inner_tool('count_emails_in_mailbox', kwargs)

    def list_unread_emails_in_mailbox(self, **kwargs):
        return self._call_inner_tool('list_unread_emails_in_mailbox', kwargs)

    def count_unread_emails_in_mailbox(self, **kwargs):
        return self._call_inner_tool('count_unread_emails_in_mailbox', kwargs)

    def get_email_metadata(self, **kwargs):
        return self._call_inner_tool('get_email_metadata', kwargs)

    def get_email_by_id(self, **kwargs):
        return self._call_inner_tool('get_email_by_id', kwargs)

    def move_email_to_mailbox(self, **kwargs):
        return self._call_inner_tool('move_email_to_mailbox', kwargs)

    def mark_email_as_read(self, **kwargs):
        return self._call_inner_tool('mark_email_as_read', kwargs)

    def mark_email_as_unread(self, **kwargs):
        return self._call_inner_tool('mark_email_as_unread', kwargs)

    def compose_and_send_email(self, **kwargs):
        return self._call_inner_tool('compose_and_send_email', kwargs)

    def permanently_delete_email(self, **kwargs):
        return self._call_inner_tool('permanently_delete_email', kwargs)

    def create_mailbox(self, **kwargs):
        return self._call_inner_tool('create_mailbox', kwargs)

    def delete_mailbox(self, **kwargs):
        return self._call_inner_tool('delete_mailbox', kwargs)
