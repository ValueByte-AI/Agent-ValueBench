# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class FileInfo(TypedDict):
    file_uid: str
    owner_user_id: str
    filename: str
    resource_url: str
    upload_timestamp: str
    access_permissions: List[str]  # List of user IDs with access (owner, shared-with, etc.)
    file_size: float
    file_typ: str

class UserInfo(TypedDict):
    _id: str
    username: str
    account_status: str
    email: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for a content sharing platform's file management.
        """
        # Files: {file_uid: FileInfo}
        # Maps each file UID to its file metadata and owner.
        self.files: Dict[str, FileInfo] = {}

        # Users: {_id: UserInfo}
        # Maps each user ID to the account information.
        self.users: Dict[str, UserInfo] = {}
        
        # --- Constraints (see rules above) ---
        # - Only a user with appropriate access permissions (e.g., owner or shared-with) can retrieve the download link for a file.
        # - File UIDs must be unique across the platform.
        # - Each file must be associated with exactly one owner user.
        # - Users can only list files they are authorized to view (typically files they own or that are shared with them).

    def get_file_by_uid(self, file_uid: str) -> dict:
        """
        Retrieve complete metadata for a file given its unique UID.

        Args:
            file_uid (str): The unique identifier for the file.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": FileInfo  # Complete metadata for the file
                    }
                On failure:
                    {
                        "success": False,
                        "error": "File UID does not exist"
                    }

        Constraints:
            - The file_uid must exist in the system.
        """
        file_info = self.files.get(file_uid)
        if file_info is None:
            return {"success": False, "error": "File UID does not exist"}
        return {"success": True, "data": file_info}

    def get_file_resource_url(self, file_uid: str, requesting_user_id: str) -> dict:
        """
        Retrieve the resource URL (download link) for a file if and only if the requesting user has access permissions.

        Args:
            file_uid (str): The unique identifier of the target file.
            requesting_user_id (str): The user ID making the request.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": <resource_url>}
                - On error:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - File must exist.
            - Requesting user must exist.
            - Requesting user must be present in the file's access_permissions.
        """
        file_info = self.files.get(file_uid)
        if not file_info:
            return {"success": False, "error": "File does not exist"}
    
        if requesting_user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if requesting_user_id not in file_info["access_permissions"]:
            return {"success": False, "error": "Access denied: user lacks permissions for this file"}

        return {"success": True, "data": file_info["resource_url"]}

    def list_files_by_owner(self, owner_user_id: str) -> dict:
        """
        List all files owned by a specified user.

        Args:
            owner_user_id (str): The user ID to lookup file ownership.

        Returns:
            dict: 
                - If the user exists: 
                    {"success": True, "data": List[FileInfo]}
                    (list of files belonging to that user, may be empty)
                - If the user does not exist:
                    {"success": False, "error": "User does not exist"}

        Constraints:
            - The user must exist in the system.
            - Each file must be associated with exactly one owner user.
        """
        if owner_user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        result = [
            file_info for file_info in self.files.values()
            if file_info["owner_user_id"] == owner_user_id
        ]
        return {"success": True, "data": result}

    def list_files_shared_with_user(self, user_id: str) -> dict:
        """
        List all files that are explicitly shared with a specified user (user_id), i.e.,
        files that the user does NOT own but appear in access_permissions.

        Args:
            user_id (str): The user ID to search for shared files.

        Returns:
            dict: {
                "success": True,
                "data": List[FileInfo],  # List of FileInfo objects (may be empty if no files shared)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "User does not exist"
            }

        Constraints:
            - The user must exist on the platform.
            - Only files where user_id is in access_permissions and user is NOT the owner are listed.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        shared_files = [
            file_info
            for file_info in self.files.values()
            if (user_id in file_info["access_permissions"] and file_info["owner_user_id"] != user_id)
        ]

        return { "success": True, "data": shared_files }

    def list_accessible_files_for_user(self, user_id: str) -> dict:
        """
        List all files a user is authorized to view, whether they own them or have been given access.

        Args:
            user_id (str): The ID of the user for whom to list accessible files.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": List[FileInfo]  # List of FileInfo dicts accessible to the user (may be empty)
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., user does not exist)
                }

        Constraints:
            - Only files where the user is the owner or is listed in access_permissions are included.
            - The user must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        accessible_files = [
            file_info for file_info in self.files.values()
            if file_info["owner_user_id"] == user_id or user_id in file_info.get("access_permissions", [])
        ]
        return {"success": True, "data": accessible_files}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user account information by user ID.

        Args:
            user_id (str): The user ID to look up.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "data": UserInfo
                }
                Failure: {
                    "success": False,
                    "error": "User does not exist"
                }

        Constraints:
            - The given user ID must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {"success": False, "error": "User does not exist"}
        return {"success": True, "data": user_info}

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user account information by username.

        Args:
            username (str): The username to look for.

        Returns:
            dict: 
                - On success: {"success": True, "data": UserInfo}
                - On failure: {"success": False, "error": "User not found"}

        Constraints:
            - Usernames are assumed to be unique in this context.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def check_file_access_permission(self, file_uid: str, user_id: str) -> dict:
        """
        Check if a specific user has permission to access (view or download) a given file.

        Args:
            file_uid (str): Unique identifier for the file.
            user_id (str): Unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "permitted": bool  # True if user has permission, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Error message if file or user not found
            }

        Constraints:
            - Only a user in access_permissions can access a file.
            - Both file and user IDs must exist.
        """
        if file_uid not in self.files:
            return { "success": False, "error": "File does not exist" }
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        file_info = self.files[file_uid]
        permitted = user_id in file_info["access_permissions"]
        return { "success": True, "permitted": permitted }

    def file_uid_exists(self, file_uid: str) -> dict:
        """
        Checks whether a given file UID is already present in the platform.

        Args:
            file_uid (str): The file UID to check for uniqueness.

        Returns:
            dict: {
                "success": True,
                "exists": bool  # True if the file UID is present, False otherwise
            }
        """
        exists = file_uid in self.files
        return { "success": True, "exists": exists }

    def upload_file(
        self,
        file_uid: str,
        owner_user_id: str,
        filename: str,
        resource_url: str,
        upload_timestamp: str,
        access_permissions: list,
        file_size: float,
        file_typ: str
    ) -> dict:
        """
        Create a new file entry with unique UID, assign ownership, metadata, and initial access_permissions.
    
        Args:
            file_uid (str): Unique file identifier (must not already exist).
            owner_user_id (str): User ID of the file owner (must exist).
            filename (str): File name string.
            resource_url (str): Download/resource URL for this file.
            upload_timestamp (str): Timestamp string when uploaded.
            access_permissions (list of str): User IDs that can access this file (must exist in users).
            file_size (float): Size of file, in bytes or megabytes.
            file_typ (str): Type of the file.
    
        Returns:
            dict: {
                "success": True,
                "message": "File uploaded successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - file_uid must be unique and not present in self.files
            - owner_user_id must exist in self.users
            - All IDs in access_permissions must exist in self.users
            - Each file must be associated with exactly one owner user
        """
        # Check for unique file_uid
        if file_uid in self.files:
            return {"success": False, "error": "File UID already exists"}

        # Check that owner exists
        if owner_user_id not in self.users:
            return {"success": False, "error": "Owner user does not exist"}

        # Check all access_permission users exist
        for user_id in access_permissions:
            if user_id not in self.users:
                return {"success": False, "error": f"User in access_permissions does not exist: {user_id}"}

        # Ensure owner is at least in access_permissions (append if not present)
        if owner_user_id not in access_permissions:
            access_permissions = access_permissions + [owner_user_id]

        # File metadata init
        new_file: FileInfo = {
            "file_uid": file_uid,
            "owner_user_id": owner_user_id,
            "filename": filename,
            "resource_url": resource_url,
            "upload_timestamp": upload_timestamp,
            "access_permissions": access_permissions,
            "file_size": file_size,
            "file_typ": file_typ
        }

        self.files[file_uid] = new_file

        return {"success": True, "message": "File uploaded successfully"}

    def delete_file(self, file_uid: str, user_id: str) -> dict:
        """
        Permanently remove a file from the system. Only allowed for the file's owner.

        Args:
            file_uid (str): Unique identifier of the file to delete.
            user_id (str): User ID of the user requesting deletion.

        Returns:
            dict: On success:
                { "success": True, "message": "File <file_uid> deleted successfully." }
            On failure:
                { "success": False, "error": <reason str> }

        Constraints:
            - file_uid must exist in the system.
            - Only the owner (owner_user_id) of the file can delete it.
            - user_id must be a valid user.
        """
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
    
        # Check file exists
        if file_uid not in self.files:
            return { "success": False, "error": "File not found" }
    
        file_info = self.files[file_uid]
    
        # Check ownership
        if file_info['owner_user_id'] != user_id:
            return { "success": False, "error": "Permission denied: Only the owner can delete this file" }
    
        # Delete the file
        del self.files[file_uid]
    
        return { "success": True, "message": f"File {file_uid} deleted successfully." }

    def update_file_permissions(
        self,
        requesting_user_id: str,
        file_uid: str,
        add_user_ids: list = None,
        remove_user_ids: list = None
    ) -> dict:
        """
        Modify the access_permissions list for a specific file (to share or revoke access).

        Args:
            requesting_user_id (str): The user ID attempting to change the permissions.
            file_uid (str): The unique ID of the file whose permissions will be updated.
            add_user_ids (List[str], optional): User IDs to grant access (share file with). If None, no users added.
            remove_user_ids (List[str], optional): User IDs to revoke access from. If None, no users removed.

        Returns:
            dict: {
                "success": True,
                "message": "File permissions updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only the file's owner may update file permissions.
            - Cannot remove owner from access_permissions.
            - Ignores add/remove requests for non-existent users.
            - File must exist.
        """
        if file_uid not in self.files:
            return {"success": False, "error": "File does not exist."}

        file_info = self.files[file_uid]
        owner_id = file_info["owner_user_id"]

        if requesting_user_id != owner_id:
            return {"success": False, "error": "Permission denied: only the file owner can modify access permissions."}

        if add_user_ids is None:
            add_user_ids = []
        if remove_user_ids is None:
            remove_user_ids = []

        current_permissions = set(file_info["access_permissions"])

        # Only allow adding IDs that correspond to real users (ignore others)
        add_user_ids = [uid for uid in add_user_ids if uid in self.users]
        remove_user_ids = [uid for uid in remove_user_ids if uid in self.users]

        # Owner should always remain in permissions
        if owner_id not in current_permissions:
            current_permissions.add(owner_id)
        if owner_id in remove_user_ids:
            remove_user_ids.remove(owner_id)

        # Apply additions
        for uid in add_user_ids:
            current_permissions.add(uid)

        # Apply removals (except for owner)
        for uid in remove_user_ids:
            if uid != owner_id:
                current_permissions.discard(uid)

        # Save changes
        file_info["access_permissions"] = list(current_permissions)
        self.files[file_uid] = file_info

        return {"success": True, "message": "File permissions updated successfully."}

    def transfer_file_owner(self, file_uid: str, new_owner_user_id: str) -> dict:
        """
        Change the ownership of a file to another registered user.

        Args:
            file_uid (str): The unique identifier of the file to transfer.
            new_owner_user_id (str): The user ID of the new owner.

        Returns:
            dict: {
                "success": True,
                "message": "Ownership of file <file_uid> transferred to user <new_owner_user_id>."
            }
            OR
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - The file must exist.
            - The new owner must be an existing registered user.
            - After transfer, the file must have exactly one owner (field: owner_user_id).
            - Best-effort: ensure the new owner is in access_permissions (if not, add).
        """
        # Check file existence
        if file_uid not in self.files:
            return {"success": False, "error": "File does not exist."}

        # Check user existence
        if new_owner_user_id not in self.users:
            return {"success": False, "error": "New owner user does not exist."}

        file_info = self.files[file_uid]
        current_owner = file_info["owner_user_id"]

        # If ownership is already with the new owner, treat as success
        if current_owner == new_owner_user_id:
            return {
                "success": True,
                "message": f"Ownership already set to user {new_owner_user_id} for file {file_uid}."
            }

        # Update owner
        file_info["owner_user_id"] = new_owner_user_id

        # Update access_permissions so the new owner is in the list
        if new_owner_user_id not in file_info["access_permissions"]:
            file_info["access_permissions"].append(new_owner_user_id)

        self.files[file_uid] = file_info

        return {
            "success": True,
            "message": f"Ownership of file {file_uid} transferred to user {new_owner_user_id}."
        }

    def update_file_metadata(self, user_id: str, file_uid: str, new_metadata: dict) -> dict:
        """
        Edit metadata attributes of a file (e.g., filename, file_typ), if permitted.

        Args:
            user_id (str): The ID of the user requesting the update (must be the file's owner).
            file_uid (str): The unique identifier for the file to modify.
            new_metadata (dict): Dict of fields to update (allowed: 'filename', 'file_typ').

        Returns:
            dict: { "success": True, "message": "File metadata updated." }
                  or
                  { "success": False, "error": <reason> }

        Constraints:
            - Only owner (user_id == owner_user_id) may edit file metadata.
            - The file and user must both exist.
            - Only allowed fields ('filename', 'file_typ') are updatable.
        """
        # Check if file exists
        file_info = self.files.get(file_uid)
        if not file_info:
            return {"success": False, "error": "File not found."}

        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check permission: only owner can update
        if file_info["owner_user_id"] != user_id:
            return {"success": False, "error": "Permission denied. Only the file owner can update metadata."}

        # Only allow updating certain attributes
        allowed_fields = {"filename", "file_typ"}
        changes_made = []
        for key, value in new_metadata.items():
            if key in allowed_fields:
                if file_info[key] != value:
                    file_info[key] = value
                    changes_made.append(key)
            else:
                return {"success": False, "error": f"Cannot update field '{key}'. Only {allowed_fields} allowed."}

        if not changes_made:
            return {"success": True, "message": "No changes made (metadata identical or empty update)."}

        # Update reflected in self.files[file_uid], as file_info is a reference
        return {"success": True, "message": f"File metadata updated: {', '.join(changes_made)}."}

    def restore_deleted_file(self, file_uid: str) -> dict:
        """
        Restore a previously deleted file from the archive, returning it to active files.

        Args:
            file_uid (str): The unique identifier of the file to restore.

        Returns:
            dict: {
                "success": True,
                "message": "File restored: <filename>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - File UIDs must remain unique in the active files list.
            - File must exist in deleted/archived files (self.deleted_files) to be restored.
            - On restoration, file is removed from archive and added to active files.
            - Each file must remain associated with a valid owner user.
        """

        # Check if the deleted files archive exists
        if not hasattr(self, "deleted_files"):
            return { "success": False, "error": "System does not support file archival/undo." }

        # Check if the file is in the deleted archive
        if file_uid not in self.deleted_files:
            return { "success": False, "error": "File UID not found in deleted files archive." }

        # Ensure the file UID does not exist in the active files
        if file_uid in self.files:
            return { "success": False, "error": "File UID already active in the system." }

        file_info = self.deleted_files[file_uid]

        # Validate owner exists
        owner_user_id = file_info.get("owner_user_id")
        if owner_user_id not in self.users:
            return { "success": False, "error": "Owner user does not exist; cannot restore file." }

        # Restore the file
        self.files[file_uid] = file_info
        del self.deleted_files[file_uid]

        filename = file_info.get("filename", file_uid)
        return { "success": True, "message": f"File restored: {filename}" }

    def bulk_share_files(
        self,
        acting_user_id: str,
        file_uids: list,
        target_user_ids: list
    ) -> dict:
        """
        Share multiple files (those to which the acting user has access) with multiple target users by updating access_permissions.

        Args:
            acting_user_id (str): The user ID performing the share operation. Must have access to the files.
            file_uids (List[str]): A list of file UIDs to share.
            target_user_ids (List[str]): A list of user IDs with whom to share the files.

        Returns:
            dict: {
                "success": True,
                "message": "Successfully shared X files with Y users"
            }
            or
            {
                "success": False,
                "error": <error message>
            }
        Constraints:
            - Each file UID must exist in the system.
            - Each user ID in target_user_ids must exist.
            - Acting user must have access permission for each specified file.
            - Access permissions are extended, not removed.
            - No duplicate user IDs within the file's access_permissions.
        """
        # Validate non-empty (for both lists, allow empty as harmless/success)
        if not file_uids or not target_user_ids:
            return {
                "success": True,
                "message": "No files or users provided; nothing to share"
            }

        # Check all files exist
        not_found_files = [fid for fid in file_uids if fid not in self.files]
        if not_found_files:
            return {
                "success": False,
                "error": f"File(s) not found: {', '.join(not_found_files)}"
            }

        # Check all users exist
        not_found_users = [uid for uid in target_user_ids if uid not in self.users]
        if not_found_users:
            return {
                "success": False,
                "error": f"Target user(s) not found: {', '.join(not_found_users)}"
            }

        # Check acting_user has access to EACH file
        inaccessible_files = [
            fid for fid in file_uids
            if acting_user_id not in self.files[fid]['access_permissions']
        ]
        if inaccessible_files:
            return {
                "success": False,
                "error": f"Acting user does not have permission to share files: {', '.join(inaccessible_files)}"
            }

        # Perform the sharing
        for fid in file_uids:
            cur_permissions = set(self.files[fid]['access_permissions'])
            cur_permissions.update(target_user_ids)
            self.files[fid]['access_permissions'] = list(cur_permissions)

        return {
            "success": True,
            "message": f"Successfully shared {len(file_uids)} files with {len(target_user_ids)} users"
        }

    def bulk_delete_files(self, user_id: str, file_uids: list) -> dict:
        """
        Delete multiple files in a single operation, subject to permission and ownership.

        Args:
            user_id (str): The user requesting the deletions. Must be the owner of each file.
            file_uids (list): List of file UIDs (str) to attempt deletion.

        Returns:
            dict: 
                {
                    "success": True,
                    "results": [
                        { "file_uid": <str>, "status": "deleted" },
                        { "file_uid": <str>, "status": "failure", "reason": <str> },
                        ...
                    ]
                }
            or
                { "success": False, "error": <str> } for general/early error (e.g. user not found, input error)
    
        Constraints:
            - Only the file owner may delete a file.
            - Each file must exist.
        """
        if not isinstance(file_uids, list):
            return {"success": False, "error": "file_uids must be a list."}
        if user_id not in self.users:
            return {"success": False, "error": "Requesting user does not exist."}

        results = []
        for uid in file_uids:
            if uid not in self.files:
                results.append({
                    "file_uid": uid,
                    "status": "failure",
                    "reason": "File does not exist."
                })
                continue
            file_info = self.files[uid]
            if file_info.get("owner_user_id") != user_id:
                results.append({
                    "file_uid": uid,
                    "status": "failure",
                    "reason": "User does not have permission to delete this file."
                })
                continue
            # All checks pass, perform deletion
            del self.files[uid]
            results.append({
                "file_uid": uid,
                "status": "deleted"
            })

        return {"success": True, "results": results}


class ContentSharingFileManagementSystem(BaseEnv):
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
            if key == "deleted_files":
                normalized_deleted_files = {}
                raw_value = copy.deepcopy(value)
                if isinstance(raw_value, str):
                    try:
                        raw_value = json.loads(raw_value)
                    except Exception:
                        raw_value = {}
                if isinstance(raw_value, list):
                    for item in raw_value:
                        if isinstance(item, dict) and item.get("file_uid"):
                            normalized_deleted_files[item["file_uid"]] = copy.deepcopy(item)
                    setattr(env, key, normalized_deleted_files)
                    continue
                if isinstance(raw_value, dict):
                    for archive_key, archive_value in raw_value.items():
                        if isinstance(archive_value, dict):
                            normalized_deleted_files[archive_value.get("file_uid", archive_key)] = copy.deepcopy(archive_value)
                    setattr(env, key, normalized_deleted_files)
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

    def get_file_by_uid(self, **kwargs):
        return self._call_inner_tool('get_file_by_uid', kwargs)

    def get_file_resource_url(self, **kwargs):
        return self._call_inner_tool('get_file_resource_url', kwargs)

    def list_files_by_owner(self, **kwargs):
        return self._call_inner_tool('list_files_by_owner', kwargs)

    def list_files_shared_with_user(self, **kwargs):
        return self._call_inner_tool('list_files_shared_with_user', kwargs)

    def list_accessible_files_for_user(self, **kwargs):
        return self._call_inner_tool('list_accessible_files_for_user', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def check_file_access_permission(self, **kwargs):
        return self._call_inner_tool('check_file_access_permission', kwargs)

    def file_uid_exists(self, **kwargs):
        return self._call_inner_tool('file_uid_exists', kwargs)

    def upload_file(self, **kwargs):
        return self._call_inner_tool('upload_file', kwargs)

    def delete_file(self, **kwargs):
        return self._call_inner_tool('delete_file', kwargs)

    def update_file_permissions(self, **kwargs):
        return self._call_inner_tool('update_file_permissions', kwargs)

    def transfer_file_owner(self, **kwargs):
        return self._call_inner_tool('transfer_file_owner', kwargs)

    def update_file_metadata(self, **kwargs):
        return self._call_inner_tool('update_file_metadata', kwargs)

    def restore_deleted_file(self, **kwargs):
        return self._call_inner_tool('restore_deleted_file', kwargs)

    def bulk_share_files(self, **kwargs):
        return self._call_inner_tool('bulk_share_files', kwargs)

    def bulk_delete_files(self, **kwargs):
        return self._call_inner_tool('bulk_delete_files', kwargs)
