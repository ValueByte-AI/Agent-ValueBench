# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import re
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict



class ContactInfo(TypedDict):
    contact_id: str
    name: str
    email_addresses: List[str]
    phone_number: str
    tags: List[str]
    no: str  # Assumed to be 'notes' or additional info

class MailInfo(TypedDict):
    mail_id: str
    sender: str
    to_recipients: List[str]
    cc_recipients: List[str]
    bcc_recipients: List[str]
    subject: str
    body: str
    attachments: List[str]  # list of attachment_ids
    timestamp: str
    folder: str
    status: str  # e.g., 'read', 'unread', 'archived', etc.

class AttachmentInfo(TypedDict):
    attachment_id: str
    filename: str
    file_path: str
    mime_type: str
    email_id: str

class FolderInfo(TypedDict):
    folder_id: str
    folder_name: str
    parent_folder_id: Optional[str]
    email_id: str  # email belonging to folder

class UserSettingsInfo(TypedDict):
    display_preferences: str
    signature: str
    default_account: str
    smtp_settings: str
    search_history: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        # Contacts: {contact_id: ContactInfo}
        self.contacts: Dict[str, ContactInfo] = {}

        # Mails: {mail_id: MailInfo}
        self.mails: Dict[str, MailInfo] = {}

        # Attachments: {attachment_id: AttachmentInfo}
        self.attachments: Dict[str, AttachmentInfo] = {}

        # Available files injected by the case. Keys are file paths.
        self.available_files: Dict[str, Dict[str, str]] = {}

        # Folders: {folder_id: FolderInfo}
        self.folders: Dict[str, FolderInfo] = {}

        # User Settings (single entity)
        self.user_settings: Optional[UserSettingsInfo] = None

        # Constraints:
        # - Email addresses in recipient fields must be valid (well-formed).
        # - Attachments must reference existing, accessible files at time of sending.
        # - Contacts and emails can be searched by name or email address.
        # - Emails cannot be sent without at least one valid recipient.
        # - Email status transitions (sent/draft/archived/etc.) according to user/system actions.

    def search_contacts_by_name(self, name_query: str) -> dict:
        """
        Lookup contacts based on (partial or full) case-insensitive name match.

        Args:
            name_query (str): Substring to search for in contact names.
                - If empty, all contacts are returned.

        Returns:
            dict:
                - success (bool): True if search performed.
                - data (List[ContactInfo]): List of matching contacts (may be empty).
        """
        # Normalize query for case-insensitive comparison
        query = name_query.strip().lower()
        if query == "":
            # If empty, return all contacts
            matches = list(self.contacts.values())
        else:
            matches = [
                contact
                for contact in self.contacts.values()
                if query in contact['name'].lower()
            ]
        return { "success": True, "data": matches }

    def search_contacts_by_email(self, email_address: str) -> dict:
        """
        Find all contacts in the address book that have the specified email address.

        Args:
            email_address (str): The email address to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ContactInfo],  # May be empty if no contacts found
                }
        Constraints:
            - Matches must be exact (case-sensitive).
            - Returns all contacts for which the email is present in their email_addresses list.
        """
        if not isinstance(email_address, str) or not email_address:
            return { "success": False, "error": "Invalid or missing email_address argument" }

        result = [
            contact for contact in self.contacts.values()
            if email_address in contact["email_addresses"]
        ]
        return { "success": True, "data": result }

    def search_contacts_by_tag(self, tag: str) -> dict:
        """
        Find all contacts that have the specified tag in their tags list.

        Args:
            tag (str): The tag to search for (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[ContactInfo]
            }
            (Empty list if no contacts have the tag.)
        """
        if not isinstance(tag, str) or tag == "":
            return {"success": True, "data": []}

        results = [
            contact for contact in self.contacts.values()
            if tag in contact.get("tags", [])
        ]
        return {"success": True, "data": results}

    def get_contact_by_id(self, contact_id: str) -> dict:
        """
        Retrieve full information for a specific contact by its contact_id.

        Args:
            contact_id (str): Unique identifier of the contact to retrieve.

        Returns:
            dict: On success:
                      {"success": True, "data": ContactInfo}
                  If not found:
                      {"success": False, "error": "Contact not found"}

        Constraints:
            - contact_id must exist in self.contacts.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return {"success": False, "error": "Contact not found"}
        return {"success": True, "data": contact}

    def get_contact_email_addresses(self, contact_id: str) -> dict:
        """
        Get all email addresses associated with a particular contact.

        Args:
            contact_id (str): The unique identifier of the contact.

        Returns:
            dict:
                If found:
                    {
                        "success": True,
                        "data": List[str]  # All email addresses for the contact (may be empty)
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Contact not found"
                    }

        Constraints:
            - contact_id must reference an existing contact in the address book.
        """
        contact = self.contacts.get(contact_id)
        if not contact:
            return { "success": False, "error": "Contact not found" }
        return { "success": True, "data": contact.get("email_addresses", []) }

    def get_contact_phone_number(self, contact_id: str) -> dict:
        """
        Retrieve the phone number for the specified contact.

        Args:
            contact_id (str): Unique identifier of the contact.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": str  # phone number (may be empty string if not provided)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Contact not found"
                    }

        Constraints:
            - The contact_id must exist in the address book.
        """
        contact = self.contacts.get(contact_id)
        if contact is None:
            return {"success": False, "error": "Contact not found"}

        # Phone number may be empty or None, but that's not an error.
        return {"success": True, "data": contact.get("phone_number", "")}


    def validate_email_address(self, email_address: str) -> dict:
        """
        Check if the provided string is a well-formed email address.

        Args:
            email_address (str): The email address to validate.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if email is well-formed, False otherwise
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Email must be non-empty string and conform to a standard pattern.
        """
        if not isinstance(email_address, str) or not email_address.strip():
            return {"success": False, "error": "Invalid or missing email address"}

        # Approximate RFC 5322 official regex for email validation (simplified for practicality)
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        is_valid = re.match(email_regex, email_address) is not None

        return {"success": True, "data": is_valid}


    def check_attachment_file_exists(self, file_path: str) -> dict:
        """
        Verify that a given file path (for attachments) exists and is accessible (readable).

        Args:
            file_path (str): The full file path to check for existence and readability.

        Returns:
            dict:
                If valid input:
                    { "success": True, "exists": bool }
                If invalid input:
                    { "success": False, "error": <str> }

        Constraints:
            - Only checks if file exists on the file system and is readable.
            - Does not modify state.
        """
        if not isinstance(file_path, str) or not file_path:
            return {"success": False, "error": "Invalid file_path argument"}
        exists_and_accessible = self._file_exists(file_path)
        return {"success": True, "exists": exists_and_accessible}

    def _file_exists(self, file_path: str) -> bool:
        if not isinstance(file_path, str) or not file_path:
            return False
        if file_path in self.available_files:
            return True
        for attachment in self.attachments.values():
            if attachment.get("file_path") == file_path:
                return True
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)

    def get_folder_by_name(self, folder_name: str) -> dict:
        """
        Fetches one or more folder(s) info objects by their folder name.

        Args:
            folder_name (str): The human-readable name of a folder (e.g. 'Sent', 'Inbox', etc.)

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[FolderInfo]  # List of folders matching the name (may contain just one)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "No folder found with the given name"
                    }
        Constraints:
            - If multiple folders share the name, all are returned.
            - If no folder is found, "success": False.
        """
        if not folder_name or not isinstance(folder_name, str):
            return {"success": False, "error": "Invalid folder name"}

        matched_folders = [
            folder
            for folder in self.folders.values()
            if folder.get("folder_name") == folder_name
        ]

        if not matched_folders:
            return {"success": False, "error": "No folder found with the given name"}

        return {"success": True, "data": matched_folders}

    def list_folders(self) -> dict:
        """
        Retrieve all existing email folders.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FolderInfo],  # List of folder information
            }
            If no folders exist, the data list will be empty.
        """
        folders_list = list(self.folders.values())
        return { "success": True, "data": folders_list }

    def get_mail_by_id(self, mail_id: str) -> dict:
        """
        Retrieve an email’s full contents by its mail_id.

        Args:
            mail_id (str): The unique identifier for the email.

        Returns:
            dict: {
                "success": True,
                "data": MailInfo  # Email's content and metadata
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Mail not found"
            }

        Constraints:
            - The specified mail_id must exist in the environment's mails dictionary.
        """
        if mail_id not in self.mails:
            return { "success": False, "error": "Mail not found" }

        return { "success": True, "data": self.mails[mail_id] }

    def list_mails_in_folder(self, folder_name: str) -> dict:
        """
        List all emails in a specified folder by folder name.

        Args:
            folder_name (str): The name of the folder (e.g., 'Inbox', 'Sent', 'Drafts', custom name).

        Returns:
            dict: {
                "success": True,
                "data": List[MailInfo],  # list of mails in the folder (empty if none)
            }
            or
            {
                "success": False,
                "error": str,  # folder not found
            }

        Constraints:
            - The folder with specified name must exist in self.folders.
            - All emails with MailInfo['folder'] == folder_name are included.
        """
        matching_folder_ids = {
            folder_info["folder_id"]
            for folder_info in self.folders.values()
            if folder_info["folder_name"] == folder_name
        }
        folder_exists = bool(matching_folder_ids)
        if not folder_exists:
            return {"success": False, "error": "Folder not found"}

        result = [
            mail_info for mail_info in self.mails.values()
            if mail_info["folder"] == folder_name or mail_info["folder"] in matching_folder_ids
        ]

        return {"success": True, "data": result}

    def get_user_settings(self) -> dict:
        """
        Retrieve the current user's email client settings.

        Returns:
            dict: 
                - { "success": True, "data": UserSettingsInfo } if user settings exist
                - { "success": False, "error": "User settings not configured" } if none are set

        Constraints:
            - No special constraints; only returns the user_settings entity if present.
        """
        if self.user_settings is None:
            return { "success": False, "error": "User settings not configured" }
        return { "success": True, "data": self.user_settings }


    def _is_valid_email(self, email: str) -> bool:
        # Simple regex (not exhaustive RFC spec)
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        return bool(re.match(pattern, email))

    def create_email_draft(
        self,
        sender: str,
        to_recipients: List[str],
        cc_recipients: List[str],
        bcc_recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> dict:
        """
        Create a new draft email with the specified fields.
        - Sender and any recipients must be valid email addresses (basic validation).
        - Attachments (if provided) must reference existing attachment_ids in self.attachments.
        - Email will be created with status 'draft' and placed in the 'Drafts' folder.

        Args:
            sender (str): Sender's email address.
            to_recipients (List[str]): To recipient email addresses.
            cc_recipients (List[str]): CC recipient email addresses.
            bcc_recipients (List[str]): BCC recipient email addresses.
            subject (str): Subject text.
            body (str): Email body.
            attachments (Optional[List[str]]): List of attachment IDs.

        Returns:
            dict:
                success: True/False
                message: On success, creation message.
                mail_id: Created mail_id (on success).
                error: Error reason (on failure).
        """
        if not sender or not self._is_valid_email(sender):
            return {"success": False, "error": "Invalid or missing sender email address"}

        for field, recipient_list in [
            ("to", to_recipients), ("cc", cc_recipients), ("bcc", bcc_recipients)
        ]:
            for addr in recipient_list:
                if not self._is_valid_email(addr):
                    return {"success": False, "error": f"Invalid email address in {field} recipients: {addr}"}

        # Attachments validation
        attach_ids = attachments if attachments is not None else []
        for attach_id in attach_ids:
            if attach_id not in self.attachments:
                return {"success": False, "error": f"Attachment '{attach_id}' does not exist"}

        # Generate unique mail_id
        mail_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Place in "Drafts" folder (find by name, or just use string "Drafts")
        folder_name = "Drafts"
        folder_found = None
        for f in self.folders.values():
            if f["folder_name"] == folder_name:
                folder_found = f["folder_id"]
                break
        folder_to_use = folder_found if folder_found else folder_name  # tolerate missing 'Drafts' folder record

        mail: MailInfo = {
            "mail_id": mail_id,
            "sender": sender,
            "to_recipients": to_recipients,
            "cc_recipients": cc_recipients,
            "bcc_recipients": bcc_recipients,
            "subject": subject,
            "body": body,
            "attachments": attach_ids,
            "timestamp": timestamp,
            "folder": folder_to_use,
            "status": "draft"
        }
        self.mails[mail_id] = mail

        return {"success": True, "message": "Draft email created", "mail_id": mail_id}

    def attach_file_to_email(
        self,
        mail_id: str,
        filename: str,
        file_path: str,
        mime_type: str,
    ) -> dict:
        """
        Add a specific file attachment to an existing draft email.

        Args:
            mail_id (str): ID of the draft email to which the attachment will be added.
            filename (str): Name of the file as it appears in the attachment list.
            file_path (str): Path to the file to attach; must exist and be accessible.
            mime_type (str): MIME type for the attachment.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Attachment added to draft email <mail_id>"}
                On error:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The email must exist and be in "draft" status.
            - The file must exist at the specified file_path at the time of attachment.
        """
        # Check if the mail exists
        mail = self.mails.get(mail_id)
        if not mail:
            return {"success": False, "error": "Email draft not found"}

        # Allow only attaching to drafts
        if mail.get("status") != "draft":
            return {"success": False, "error": "Can only attach files to draft emails"}

        # Ensure the file exists at the specified file_path
        if not self._file_exists(file_path):
            return {"success": False, "error": "Attachment file does not exist at specified path"}

        # Generate a unique attachment ID (simple implementation: count + 1)
        attachment_id = str(uuid.uuid4())
    
        # Create and store the attachment info
        attachment_info = {
            "attachment_id": attachment_id,
            "filename": filename,
            "file_path": file_path,
            "mime_type": mime_type,
            "email_id": mail_id,
        }
        self.attachments[attachment_id] = attachment_info

        # Update mail's attachment list
        mail["attachments"].append(attachment_id)
        self.mails[mail_id] = mail

        return {
            "success": True,
            "message": f"Attachment added to draft email {mail_id}"
        }

    def send_email(self, mail_id: str) -> dict:
        """
        Attempt to send a composed email, validating recipients and attachments.
        Updates the email's status to 'sent' and moves it to the Sent folder.

        Args:
            mail_id (str): The ID of the email to send.

        Returns:
            dict: {
                "success": True,
                "message": "Email sent successfully and moved to Sent folder."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - At least one of to/cc/bcc must have a valid email address.
            - Each recipient's email address must be well-formed.
            - Each attachment must reference an existing AttachmentInfo and file_path.
            - Sets status='sent', moves mail to Sent folder.
        """

        # Helper for simple RFC 5322-compliant email validation
        def is_valid_email(email: str) -> bool:
            # Simple check; replace with robust check if needed.
            return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

        # 1. Fetch email
        mail = self.mails.get(mail_id)
        if not mail:
            return { "success": False, "error": "Mail with given ID does not exist." }

        # 2. Collect all recipients
        recipients = (mail.get("to_recipients", []) or []) + \
                     (mail.get("cc_recipients", []) or []) + \
                     (mail.get("bcc_recipients", []) or [])

        if not recipients or all(not addr.strip() for addr in recipients):
            return { "success": False, "error": "No recipients specified - cannot send email without recipients." }

        # 3. Validate all recipient addresses
        for addr in recipients:
            addr = addr.strip()
            if not addr:
                continue
            if not is_valid_email(addr):
                return { "success": False, "error": f"Invalid email address in recipients: {addr}" }

        # 4. Validate all attachments exist and have file_path
        for att_id in mail.get("attachments", []):
            att = self.attachments.get(att_id)
            if (
                not att or
                not att.get("file_path") or
                not self._file_exists(att["file_path"])
            ):
                return { "success": False, "error": f"Attachment missing or inaccessible: attachment_id={att_id}" }

        # 5. Find or create the Sent folder
        sent_folder_id = None
        for folder_id, folder in self.folders.items():
            if folder["folder_name"].lower() == "sent":
                sent_folder_id = folder_id
                break

        if sent_folder_id is None:
            # Create a new Sent folder if not found
            sent_folder_id = f"folder_{uuid.uuid4().hex}"
            self.folders[sent_folder_id] = {
                "folder_id": sent_folder_id,
                "folder_name": "Sent",
                "parent_folder_id": None,
                "email_id": mail_id  # Only for this initial mail; would otherwise be a set/list in real system
            }
        else:
            # Folder exists, update its email_id field to cover this email as well (by appending for sim)
            folder = self.folders[sent_folder_id]
            # Simulate folder holding multiple mails in real client
            # (here folder['email_id'] is a single mail_id, so just assign last added one for this model)

            # -- Nothing to do for simple model

            pass

        # 6. Set status to 'sent', move to Sent
        mail["status"] = "sent"
        mail["folder"] = self.folders[sent_folder_id]["folder_name"]

        # 7. Record success
        return {
            "success": True,
            "message": "Email sent successfully and moved to Sent folder."
        }

    def update_email_status(self, mail_id: str, new_status: str) -> dict:
        """
        Manually change the status of an email, e.g., from unread to archived or draft to sent.

        Args:
            mail_id (str): The unique ID of the email to update.
            new_status (str): The new status to set for the email (e.g., 'read', 'unread', 'archived', 'sent', 'draft').

        Returns:
            dict: {
                "success": True,
                "message": "Email status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The mail_id must exist.
            - Status is set as provided. Further status transition rules can be implemented if required.
        """
        if mail_id not in self.mails:
            return {"success": False, "error": "Email with the specified mail_id does not exist."}
        self.mails[mail_id]['status'] = new_status
        return {"success": True, "message": f"Email status updated to {new_status}."}

    def move_email_to_folder(self, mail_id: str, target_folder_id: str) -> dict:
        """
        Move an email message to a specified folder.

        Args:
            mail_id (str): The unique identifier of the email to move.
            target_folder_id (str): The unique identifier of the target folder.

        Returns:
            dict:
                success (bool): True if operation succeeded, False otherwise.
                message (str): Success message, present if success=True.
                error (str): Error message, present if success=False.

        Constraints:
            - Email and target folder must both exist.
            - Email's 'folder' field is updated to match the target folder id.
            - Folder's email mapping (FolderInfo -> email_id): 
                If relevant, update FolderInfo so `email_id` fields reflect emails currently in that folder.
        """
        # Check mail existence
        if mail_id not in self.mails:
            return {"success": False, "error": "Email not found."}
    
        # Check folder existence
        if target_folder_id not in self.folders:
            return {"success": False, "error": "Target folder does not exist."}

        mail_info = self.mails[mail_id]
        current_folder_id = mail_info["folder"]
    
        # Update mail's folder
        mail_info["folder"] = target_folder_id

        # If needed, update FolderInfo's email_id
        # Remove from old folder's email list (if maintained)
        if current_folder_id in self.folders:
            old_folder_info = self.folders[current_folder_id]
            if old_folder_info.get("email_id") == mail_id:
                old_folder_info["email_id"] = ""  # or set to None/empty if only one email per FolderInfo

        # Add to new folder's email list (if maintained)
        # (This structure only has one email per FolderInfo; may need link list externally in reality)
        new_folder_info = self.folders[target_folder_id]
        new_folder_info["email_id"] = mail_id

        return {
            "success": True,
            "message": f"Email moved to folder {target_folder_id}"
        }

    def delete_email(self, mail_id: str) -> dict:
        """
        Remove an email and its associated records from the mailbox system.

        Args:
            mail_id (str): The unique identifier of the email to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Email deleted: <mail_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - If the email does not exist, returns a failure.
            - Deletes associated attachments and email-folder associations.
            - No exceptions are raised; all errors are returned in structured dicts.
        """
        # Check if the mail exists
        if mail_id not in self.mails:
            return { "success": False, "error": "Email does not exist" }

        # Remove the email itself
        del self.mails[mail_id]

        # Remove associated attachments
        attachments_to_delete = [aid for aid, attach in self.attachments.items() if attach['email_id'] == mail_id]
        for aid in attachments_to_delete:
            del self.attachments[aid]

        # Remove any folder associations with this email without deleting the folder itself.
        for folder in self.folders.values():
            if folder.get('email_id') == mail_id:
                folder['email_id'] = ""

        return { "success": True, "message": f"Email deleted: {mail_id}" }

    def update_contact_info(
        self,
        contact_id: str,
        name: str = None,
        email_addresses: Optional[List[str]] = None,
        phone_number: str = None,
        tags: Optional[List[str]] = None,
        no: str = None
    ) -> dict:
        """
        Edit the information of an existing contact.
    
        Args:
            contact_id (str): ID of the contact to update (required).
            name (str, optional): New name.
            email_addresses (List[str], optional): New list of email addresses (must be well-formed).
            phone_number (str, optional): New phone number.
            tags (List[str], optional): New list of tags.
            no (str, optional): New note or info.

        Returns:
            dict:
              On success: { "success": True, "message": "Contact info updated." }
              On failure: { "success": False, "error": "<Reason>" }
    
        Constraints:
            - Contact must exist.
            - If email_addresses is updated, all must be well-formed.
            - Only specified fields are updated (partial update supported).
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact not found." }

        contact = self.contacts[contact_id]

        def _is_valid_email(addr: str) -> bool:
            # Very simple validation; for demo
            return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', addr))

        if email_addresses is not None:
            if not isinstance(email_addresses, list) or not all(isinstance(e, str) for e in email_addresses):
                return { "success": False, "error": "email_addresses must be a list of strings." }
            invalids = [e for e in email_addresses if not _is_valid_email(e)]
            if invalids:
                return { "success": False, "error": f"Invalid email address(es): {', '.join(invalids)}" }
            contact['email_addresses'] = email_addresses

        if name is not None:
            if not isinstance(name, str):
                return { "success": False, "error": "Name must be a string." }
            contact['name'] = name

        if phone_number is not None:
            if not isinstance(phone_number, str):
                return { "success": False, "error": "Phone number must be a string." }
            contact['phone_number'] = phone_number

        if tags is not None:
            if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                return { "success": False, "error": "Tags must be a list of strings." }
            contact['tags'] = tags

        if no is not None:
            if not isinstance(no, str):
                return { "success": False, "error": "Note (no) must be a string." }
            contact['no'] = no

        self.contacts[contact_id] = contact
        return { "success": True, "message": "Contact info updated." }

    def add_contact(
        self,
        contact_id: str,
        name: str,
        email_addresses: list,
        phone_number: str,
        tags: list,
        no: str
    ) -> dict:
        """
        Create a new contact in the address book.

        Args:
            contact_id (str): Unique identifier for the contact.
            name (str): Name of the contact (non-empty).
            email_addresses (List[str]): One or more valid email addresses.
            phone_number (str): Contact's phone number.
            tags (List[str]): Tags for categorization.
            no (str): Additional notes/info.

        Returns:
            dict: {
                'success': True, 'message': 'Contact added successfully'
            }
            Or error dict:
            {
                'success': False, 'error': <reason>
            }

        Constraints:
            - contact_id must be unique (not already in address book)
            - At least one valid, well-formed email address required
            - Name must not be empty
        """
        # Check uniqueness
        if contact_id in self.contacts:
            return {"success": False, "error": "Contact ID already exists"}
    
        # Check name
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Name cannot be empty"}
    
        # Check email_addresses field
        if not isinstance(email_addresses, list) or len(email_addresses) == 0:
            return {"success": False, "error": "At least one email address required"}

        # Validate emails (use validate_email_address if method exists, else basic)
        def is_valid_email(email: str) -> bool:
            # Basic well-formed check
            # Simple regex for demonstration
            return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

        for email in email_addresses:
            if not is_valid_email(email):
                return {"success": False, "error": f"Invalid email address: {email}"}

        # Create ContactInfo entry
        new_contact: ContactInfo = {
            'contact_id': contact_id,
            'name': name,
            'email_addresses': email_addresses,
            'phone_number': phone_number,
            'tags': tags,
            'no': no
        }
        self.contacts[contact_id] = new_contact
        return {"success": True, "message": "Contact added successfully"}

    def remove_contact(self, contact_id: str) -> dict:
        """
        Delete an existing contact from the address book.

        Args:
            contact_id (str): The unique identifier of the contact to remove.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Contact <contact_id> removed successfully." }
                - On failure: { "success": False, "error": "Contact does not exist." }

        Constraints:
            - The contact must exist in the address book.
            - Removal does not affect related emails or other entities.
        """
        if contact_id not in self.contacts:
            return { "success": False, "error": "Contact does not exist." }

        del self.contacts[contact_id]
        return { "success": True, "message": f"Contact {contact_id} removed successfully." }

    def update_user_settings(
        self,
        display_preferences: Optional[str] = None,
        signature: Optional[str] = None,
        default_account: Optional[str] = None,
        smtp_settings: Optional[str] = None,
        search_history: Optional[List[str]] = None
    ) -> dict:
        """
        Change user preferences such as display, signature, or default account.

        Args:
            display_preferences (Optional[str]): New display preferences.
            signature (Optional[str]): New email signature.
            default_account (Optional[str]): New default sending account.
            smtp_settings (Optional[str]): New SMTP configuration/settings.
            search_history (Optional[List[str]]): New search history list.

        Returns:
            dict: {
                "success": True,
                "message": "User settings updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If no settings record exists, it will be created.
            - Only provided (non-None) fields are updated.
        """
        if (
            display_preferences is None and
            signature is None and
            default_account is None and
            smtp_settings is None and
            search_history is None
        ):
            return {"success": False, "error": "No user settings fields provided for update"}

        # Create default settings if not present
        if self.user_settings is None:
            self.user_settings = {
                "display_preferences": "",
                "signature": "",
                "default_account": "",
                "smtp_settings": "",
                "search_history": []
            }

        # Type checking for search_history
        if search_history is not None:
            if not isinstance(search_history, list) or not all(isinstance(x, str) for x in search_history):
                return {"success": False, "error": "search_history must be a list of strings"}

        # Update only the provided fields
        if display_preferences is not None:
            self.user_settings["display_preferences"] = display_preferences
        if signature is not None:
            self.user_settings["signature"] = signature
        if default_account is not None:
            self.user_settings["default_account"] = default_account
        if smtp_settings is not None:
            self.user_settings["smtp_settings"] = smtp_settings
        if search_history is not None:
            self.user_settings["search_history"] = search_history

        return {"success": True, "message": "User settings updated"}


class EmailClientWithAddressBook(BaseEnv):
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
            if key == "_is_valid_email":
                setattr(env, "_is_valid_email_state", copy.deepcopy(value))
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

    def search_contacts_by_name(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_name', kwargs)

    def search_contacts_by_email(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_email', kwargs)

    def search_contacts_by_tag(self, **kwargs):
        return self._call_inner_tool('search_contacts_by_tag', kwargs)

    def get_contact_by_id(self, **kwargs):
        return self._call_inner_tool('get_contact_by_id', kwargs)

    def get_contact_email_addresses(self, **kwargs):
        return self._call_inner_tool('get_contact_email_addresses', kwargs)

    def get_contact_phone_number(self, **kwargs):
        return self._call_inner_tool('get_contact_phone_number', kwargs)

    def validate_email_address(self, **kwargs):
        return self._call_inner_tool('validate_email_address', kwargs)

    def check_attachment_file_exists(self, **kwargs):
        return self._call_inner_tool('check_attachment_file_exists', kwargs)

    def get_folder_by_name(self, **kwargs):
        return self._call_inner_tool('get_folder_by_name', kwargs)

    def list_folders(self, **kwargs):
        return self._call_inner_tool('list_folders', kwargs)

    def get_mail_by_id(self, **kwargs):
        return self._call_inner_tool('get_mail_by_id', kwargs)

    def list_mails_in_folder(self, **kwargs):
        return self._call_inner_tool('list_mails_in_folder', kwargs)

    def get_user_settings(self, **kwargs):
        return self._call_inner_tool('get_user_settings', kwargs)

    def _is_valid_email(self, **kwargs):
        return self._call_inner_tool('_is_valid_email', kwargs)

    def create_email_draft(self, **kwargs):
        return self._call_inner_tool('create_email_draft', kwargs)

    def attach_file_to_email(self, **kwargs):
        return self._call_inner_tool('attach_file_to_email', kwargs)

    def send_email(self, **kwargs):
        return self._call_inner_tool('send_email', kwargs)

    def update_email_status(self, **kwargs):
        return self._call_inner_tool('update_email_status', kwargs)

    def move_email_to_folder(self, **kwargs):
        return self._call_inner_tool('move_email_to_folder', kwargs)

    def delete_email(self, **kwargs):
        return self._call_inner_tool('delete_email', kwargs)

    def update_contact_info(self, **kwargs):
        return self._call_inner_tool('update_contact_info', kwargs)

    def add_contact(self, **kwargs):
        return self._call_inner_tool('add_contact', kwargs)

    def remove_contact(self, **kwargs):
        return self._call_inner_tool('remove_contact', kwargs)

    def update_user_settings(self, **kwargs):
        return self._call_inner_tool('update_user_settings', kwargs)
