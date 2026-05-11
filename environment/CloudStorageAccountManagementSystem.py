# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict
from collections import defaultdict
import uuid
import datetime
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    username: str
    email: str
    storage_quota: float  # Maximum allowed storage (MB/GB)
    storage_used: float   # Current storage used

class FolderInfo(TypedDict, total=False):
    folder_id: str
    user_id: str              # Owner of the folder
    name: str                 # Folder name (unique within parent for user)
    parent_folder_id: Optional[str]  # None means root
    path: str                 # Full path

class FileInfo(TypedDict):
    file_id: str
    user_id: str              # Owner of the file
    folder_id: str            # Folder containing this file
    name: str                 # File name (unique within parent for user)
    size: float               # File size
    type: str                 # File type/extension
    created_at: str           # Timestamp string
    modified_at: str          # Timestamp string
    path: str                 # Full path

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {user_id (str): UserInfo}
        # From entity: User (_id, username, email, storage_quota, storage_used)
        self.users: Dict[str, UserInfo] = {}

        # Folders: {folder_id (str): FolderInfo}
        # From entity: Folder (folder_id, user_id, name, parent_folder_id, path)
        self.folders: Dict[str, FolderInfo] = {}

        # Files: {file_id (str): FileInfo}
        # From entity: File (file_id, user_id, folder_id, name, size, type, created_at, modified_at, path)
        self.files: Dict[str, FileInfo] = {}

        # Constraints:
        # - Each user can only access their own files and folders.
        # - storage_used for a user is the sum of sizes of all their files and must not exceed storage_quota.
        # - Folder and file names must be unique within the same parent folder for a user.
        # - Folders can be nested using parent_folder_id; root folders have parent_folder_id = None.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user data (id, email, storage quota, used space) by username.

        Args:
            username (str): The username to lookup.

        Returns:
            dict:
                {"success": True,
                 "data": {
                     "_id": str,
                     "username": str,
                     "email": str,
                     "storage_quota": float,
                     "storage_used": float
                 }
                }
                or
                {"success": False, "error": "User not found"}
        Constraints:
            - Usernames are unique.
        """
        for user in self.users.values():
            if user["username"] == username:
                # Copy only the requested fields
                result = {
                    "_id": user["_id"],
                    "username": user["username"],
                    "email": user["email"],
                    "storage_quota": user["storage_quota"],
                    "storage_used": user["storage_used"]
                }
                return {"success": True, "data": result}
        return {"success": False, "error": "User not found"}

    def get_user_storage_usage(self, user_id: str) -> dict:
        """
        Query the current storage_used and storage_quota for the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "storage_used": float,
                            "storage_quota": float
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g. user not found
                    }

        Constraints:
            - User must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }

        return {
            "success": True,
            "data": {
                "storage_used": user_info["storage_used"],
                "storage_quota": user_info["storage_quota"]
            }
        }

    def recalculate_user_storage_usage(self, user_id: str) -> dict:
        """
        Recomputes storage_used for the given user by summing the size of all files owned by them.

        Args:
            user_id (str): The ID of the user whose storage usage should be recalculated.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "user_id": <user_id>,
                    "calculated_storage_used": <sum of file sizes (float)>
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user not found
            }

        Constraints:
            - The user must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        total_size = sum(
            file_info["size"]
            for file_info in self.files.values()
            if file_info["user_id"] == user_id
        )

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "calculated_storage_used": total_size
            }
        }

    def list_user_folders(self, user_id: str, parent_folder_id: Optional[str] = None) -> dict:
        """
        List all folders owned by a user.
    
        Args:
            user_id (str): The target user's ID.
            parent_folder_id (Optional[str], default=None): If provided, filter returned folders to those whose parent_folder_id matches this value.
    
        Returns:
            dict: {
                "success": True,
                "data": List[FolderInfo],  # All matching folders (possibly empty list)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }
    
        Constraints:
            - Only list folders owned by the user (user_id).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Filter folders by user_id, and if parent_folder_id is specified, also filter by it
        folders = [
            folder for folder in self.folders.values()
            if folder.get("user_id") == user_id and 
               (parent_folder_id is None or folder.get("parent_folder_id") == parent_folder_id)
        ]

        return {"success": True, "data": folders}

    def get_folder_by_path(self, user_id: str, path: str) -> dict:
        """
        Retrieve a folder's metadata and folder_id for a user, by full folder path.

        Args:
            user_id (str): ID of the user who owns the folder.
            path (str): Full path of the folder.

        Returns:
            dict: 
              - Success: { "success": True, "data": FolderInfo }
              - Failure: { "success": False, "error": "Folder not found" }

        Constraints:
            - Only folders owned by the user are accessible.
            - Folder paths must uniquely identify the folder for a user.
        """
        for folder in self.folders.values():
            if folder.get("user_id") == user_id and folder.get("path") == path:
                return { "success": True, "data": folder }
        return { "success": False, "error": "Folder not found" }

    def get_folder_by_id(self, folder_id: str) -> dict:
        """
        Retrieve the metadata for a folder given its unique folder_id.

        Args:
            folder_id (str): The unique identifier for the folder.

        Returns:
            dict: {
                "success": True,
                "data": FolderInfo  # Folder metadata
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. "Folder not found"
            }

        Constraints:
            - folder_id must exist in the system.
        """
        folder = self.folders.get(folder_id)
        if not folder:
            return { "success": False, "error": "Folder not found" }

        return { "success": True, "data": folder }

    def list_files_in_folder(self, user_id: str, folder_id: str = None, path: str = None) -> dict:
        """
        List all files owned by a user within a specified folder.

        Args:
            user_id (str): The ID of the user.
            folder_id (str, optional): The ID of the folder (preferred for lookup).
            path (str, optional): The full path of the folder (used if folder_id is not given).

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[FileInfo],  # List of files
                }
            or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only the folder owner can list files.
            - Folder must exist.
            - Only files owned by the user in that folder are returned.
        """
        # Step 1: Lookup folder by folder_id or path, and check user ownership
        target_folder = None

        if folder_id:
            folder = self.folders.get(folder_id)
            if not folder:
                return {"success": False, "error": "Folder not found"}
            if folder["user_id"] != user_id:
                return {"success": False, "error": "Access denied: user does not own the folder"}
            target_folder = folder
        elif path:
            # Search for folder matching path and owned by user
            for fol in self.folders.values():
                if fol["path"] == path and fol["user_id"] == user_id:
                    target_folder = fol
                    break
            if not target_folder:
                return {"success": False, "error": "Folder not found for user"}
        else:
            return {"success": False, "error": "Either folder_id or path must be provided"}

        # Step 2: Gather files in folder (must match both folder_id and user_id)
        results = [
            file_info for file_info in self.files.values()
            if file_info["user_id"] == user_id and file_info["folder_id"] == target_folder["folder_id"]
        ]
        return {"success": True, "data": results}

    def get_file_by_id(self, file_id: str) -> dict:
        """
        Retrieve the complete metadata for a file by its unique file_id.

        Args:
            file_id (str): The unique identifier of the file.

        Returns:
            dict: {
                "success": True,
                "data": FileInfo  # Full metadata for the file if found
            }
            OR
            {
                "success": False,
                "error": str  # "File not found"
            }

        Constraints:
            - file_id must exist in the system.
        """
        file_info = self.files.get(file_id)
        if not file_info:
            return { "success": False, "error": "File not found" }
        return { "success": True, "data": file_info }

    def get_file_by_name_in_folder(self, user_id: str, folder_id: str, file_name: str) -> dict:
        """
        Retrieve file metadata for a file by its name within a given parent folder for a specified user.

        Args:
            user_id (str): ID of the user requesting/accessing the file.
            folder_id (str): ID of the parent folder.
            file_name (str): Name of the file to search for.

        Returns:
            dict:
            - On success: {
                  "success": True,
                  "data": FileInfo  # The file metadata dictionary
              }
            - On failure: {
                  "success": False,
                  "error": str  # Description of error
              }

        Constraints:
            - The folder must exist and belong to the specified user.
            - There must be a file with the given name in that folder for that user.
            - The user can only access their own folders/files.
            - File names are unique within a folder for a user.
        """
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder does not exist"}

        if folder["user_id"] != user_id:
            return {"success": False, "error": "User does not have access to this folder"}

        # Search for unique file in the given folder, for this user, with the given name
        for file in self.files.values():
            if (
                file["user_id"] == user_id and
                file["folder_id"] == folder_id and
                file["name"] == file_name
            ):
                return {"success": True, "data": file}

        return {"success": False, "error": "File not found in the specified folder"}

    def get_folder_structure(self, user_id: str, start_folder_id: Optional[str] = None) -> dict:
        """
        Retrieve the folder hierarchy/tree structure for a user starting from a specified folder or root.

        Args:
            user_id (str): The user whose folder structure to retrieve.
            start_folder_id (Optional[str]): The folder_id to start from.
                If None, retrieves structure from all root folders.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # List of folder tree(s) (each a dict with 'children')
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only includes folders for the specified user.
            - Folders must be structured as a hierarchy using parent_folder_id.
            - If start_folder_id is provided, it must exist and belong to the user.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Build a map of {parent_folder_id: [folder, ...]} for this user
        parent_map = defaultdict(list)
        user_folders = [f for f in self.folders.values() if f["user_id"] == user_id]
        for folder in user_folders:
            parent_map[folder.get("parent_folder_id")].append(folder)

        def build_tree(current_folder: FolderInfo) -> dict:
            # Recursively build a dictionary for this folder and its children
            folder_dict = dict(current_folder)
            children = [build_tree(child) for child in parent_map.get(current_folder["folder_id"], [])]
            folder_dict["children"] = children
            return folder_dict

        # Determine starting point(s)
        if start_folder_id:
            # Validate folder ownership and existence
            start_folder = self.folders.get(start_folder_id)
            if not start_folder or start_folder["user_id"] != user_id:
                return {"success": False, "error": "Start folder does not exist or does not belong to user"}
            tree = build_tree(start_folder)
            return {"success": True, "data": tree}
        else:
            roots = parent_map.get(None, [])
            tree = [build_tree(root) for root in roots]
            return {"success": True, "data": tree}

    def upload_file(
        self, 
        user_id: str,
        folder_id: str,
        name: str,
        size: float,
        file_type: str,
        created_at: str,
        modified_at: str,
        file_id: str = None
    ) -> dict:
        """
        Add a new file into a specified folder for a user.

        Args:
            user_id (str): ID of user uploading the file.
            folder_id (str): ID of the destination folder.
            name (str): File name (must be unique for this user in the folder).
            size (float): File size to be added.
            file_type (str): File extension/type.
            created_at (str): Creation timestamp.
            modified_at (str): Modified timestamp.
            file_id (str, optional): File ID. If None, it will be auto-generated.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "File uploaded successfully" }
                On failure:
                    { "success": False, "error": "Reason for failure" }

        Constraints:
            - Folder and file names must be unique within the same parent folder for a user.
            - User's storage_used + size must not exceed storage_quota.
            - User can only upload to their own folders.
        """
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        # Check if folder exists
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder does not exist"}

        # Check folder belongs to user
        if folder["user_id"] != user_id:
            return {"success": False, "error": "User does not own the folder"}

        # Check for file name uniqueness in folder for user
        for f in self.files.values():
            if f["user_id"] == user_id and f["folder_id"] == folder_id and f["name"] == name:
                return {"success": False, "error": "File name already exists in the folder"}

        # Check quota
        if user["storage_used"] + size > user["storage_quota"]:
            return {"success": False, "error": "Storage quota exceeded"}

        # Construct path
        folder_path = folder.get("path", "")
        if folder_path.endswith("/"):
            file_path = folder_path + name
        else:
            file_path = folder_path + "/" + name

        # Generate file_id if not provided
        new_file_id = file_id if file_id else str(uuid.uuid4())
    
        # Add the file
        file_info = {
            "file_id": new_file_id,
            "user_id": user_id,
            "folder_id": folder_id,
            "name": name,
            "size": size,
            "type": file_type,
            "created_at": created_at,
            "modified_at": modified_at,
            "path": file_path
        }
        self.files[new_file_id] = file_info

        # Update user storage_used
        user["storage_used"] += size
        self.users[user_id] = user  # in case the dict is not updated in-place

        return {"success": True, "message": "File uploaded successfully"}

    def delete_file(self, user_id: str, file_id: str) -> dict:
        """
        Remove a file specified by file_id (must belong to user_id) and update the user's storage_used.

        Args:
            user_id (str): The _id of the user requesting deletion.
            file_id (str): The file_id of the file to remove.

        Returns:
            dict: 
                - success: True and a descriptive message if deletion and update succeed.
                - success: False and an error message if file does not exist, permission denied, or user not found.

        Constraints:
            - Only the owner (user_id) can delete the file.
            - User's storage_used must be updated accordingly after file deletion.
        """
        file_info = self.files.get(file_id)
        if not file_info:
            return { "success": False, "error": "File not found." }
        if file_info['user_id'] != user_id:
            return { "success": False, "error": "Permission denied." }
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User not found." }
    
        # Deduct file size from user's storage_used
        file_size = file_info.get('size', 0.0)
        storage_used = user_info.get('storage_used', 0.0)
        try:
            # Remove file entry
            del self.files[file_id]
            # Update user's storage_used (avoid negative values)
            new_storage_used = max(0.0, storage_used - file_size)
            user_info['storage_used'] = new_storage_used
            self.users[user_id] = user_info
            return { "success": True, "message": "File deleted and user storage updated." }
        except Exception:
            return { "success": False, "error": "Unexpected failure during file deletion." }

    def move_file(self, file_id: str, target_folder_id: str) -> dict:
        """
        Move a file to another folder for the same user, ensuring target name uniqueness.

        Args:
            file_id (str): The ID of the file to move.
            target_folder_id (str): The ID of the folder to move the file into.

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
            - File must exist.
            - Target folder must exist and belong to the same user.
            - The file's name must not conflict with an existing file in the target folder for this user.
            - Updates file's folder_id, path, and modified_at. Storage usage is unaffected.
        """

        # Check file exists
        file_info = self.files.get(file_id)
        if not file_info:
            return { "success": False, "error": "File does not exist." }

        user_id = file_info["user_id"]

        # Check target folder exists
        target_folder = self.folders.get(target_folder_id)
        if not target_folder:
            return { "success": False, "error": "Target folder does not exist." }

        # Check target folder belongs to the same user
        if target_folder["user_id"] != user_id:
            return { "success": False, "error": "Cannot move file to a folder owned by another user." }

        # Check if file is already in the target folder
        if file_info["folder_id"] == target_folder_id:
            return { "success": False, "error": "File is already in the target folder." }

        # Check file name uniqueness in target folder for this user
        file_name = file_info["name"]
        for other_file in self.files.values():
            if (
                other_file["user_id"] == user_id and
                other_file["folder_id"] == target_folder_id and
                other_file["name"] == file_name and
                other_file["file_id"] != file_id
            ):
                return { "success": False, "error": "A file with the same name already exists in the target folder." }

        # Move file: update folder_id and path
        old_folder_id = file_info["folder_id"]
        target_folder_path = target_folder.get("path", "")  # should always exist
        # New path: target_folder_path + "/" + file_name (avoid "//" if already has "/")
        if target_folder_path.endswith('/'):
            new_path = target_folder_path + file_name
        else:
            new_path = target_folder_path + "/" + file_name

        self.files[file_id]["folder_id"] = target_folder_id
        self.files[file_id]["path"] = new_path
        self.files[file_id]["modified_at"] = datetime.utcnow().isoformat() + "Z"

        return {
            "success": True,
            "message": f"File moved to folder '{target_folder.get('name', target_folder_id)}' successfully."
        }

    def rename_file(self, user_id: str, file_id: str, new_name: str) -> dict:
        """
        Rename a file within its parent folder, enforcing uniqueness of names within the same folder for the user.

        Args:
            user_id (str): The ID of the user requesting the rename.
            file_id (str): The unique identifier of the file to be renamed.
            new_name (str): The new file name.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "File renamed successfully" }
                On failure:
                    { "success": False, "error": str }
                
        Constraints:
            - Only the owner can rename their file.
            - File names must be unique within the parent folder for the user.
            - File must exist.
            - File path and modified_at fields are updated accordingly.
        """
        # Check if file exists
        file_info = self.files.get(file_id)
        if not file_info:
            return { "success": False, "error": "File does not exist" }

        # Check that this file is owned by user
        if file_info["user_id"] != user_id:
            return { "success": False, "error": "User does not have permission to rename this file" }

        # Validate new_name is a nonempty string
        if not isinstance(new_name, str) or new_name.strip() == "":
            return { "success": False, "error": "Invalid (empty) new file name" }

        parent_folder_id = file_info["folder_id"]

        # Check for uniqueness: no other file with new_name in the same folder
        for f in self.files.values():
            if (
                f["user_id"] == user_id and 
                f["folder_id"] == parent_folder_id and
                f["name"] == new_name and
                f["file_id"] != file_id
            ):
                return { "success": False, "error": "A file with this name already exists in the folder" }

        # Compose new path (assume folder's path is correct)
        folder_info = self.folders.get(parent_folder_id)
        if not folder_info:
            return { "success": False, "error": "Parent folder does not exist" }
        folder_path = folder_info["path"].rstrip('/')

        # Extract extension if any, rebuild path
        ext = ''
        if '.' in new_name:
            ext = '.' + new_name.split('.')[-1]
        # Remove old extension from name in path if desired, or set as-is
        new_path = folder_path + '/' + new_name

        now = datetime.utcnow().isoformat()

        # Update file info
        file_info["name"] = new_name
        file_info["path"] = new_path
        file_info["modified_at"] = now

        # Write back
        self.files[file_id] = file_info

        return { "success": True, "message": "File renamed successfully" }


    def create_folder(self, user_id: str, name: str, parent_folder_id: Optional[str] = None) -> dict:
        """
        Create a new folder for a user under the specified parent folder, ensuring name uniqueness.

        Args:
            user_id (str): The ID of the user who owns the folder.
            name (str): The name of the new folder (must be unique within the parent for this user).
            parent_folder_id (Optional[str]): The folder_id of the parent folder. None indicates root.

        Returns:
            dict: {
                "success": True,
                "message": "Folder created",
                "folder_id": <new_folder_id>
            }
            or
            {
                "success": False,
                "error": "Reason"
            }
        Constraints:
            - user_id must exist
            - If parent_folder_id is not None, must exist and belong to user
            - Folder name must be unique under the same parent_folder_id for user
        """
        # Check that user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Validate folder name
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Invalid folder name" }
        name = name.strip()

        # Check parent folder if not root
        if parent_folder_id is not None:
            parent_folder = self.folders.get(parent_folder_id)
            if not parent_folder:
                return { "success": False, "error": "Parent folder does not exist" }
            if parent_folder["user_id"] != user_id:
                return { "success": False, "error": "Parent folder does not belong to user" }
            parent_path = parent_folder["path"]
        else:
            parent_path = "/" + self.users[user_id]["username"]  # e.g. root path for user

        # Check uniqueness of name within parent
        for folder in self.folders.values():
            if (
                folder["user_id"] == user_id and
                folder.get("parent_folder_id") == parent_folder_id and
                folder["name"] == name
            ):
                return { "success": False, "error": "Folder name already exists in parent for user" }

        # Generate new folder id
        new_folder_id = str(uuid.uuid4())

        # Construct path: parent's path plus name, ensure single slash between
        if parent_path.endswith("/"):
            path = parent_path + name
        else:
            path = parent_path + "/" + name

        new_folder: FolderInfo = {
            "folder_id": new_folder_id,
            "user_id": user_id,
            "name": name,
            "parent_folder_id": parent_folder_id,
            "path": path
        }
        self.folders[new_folder_id] = new_folder

        return {
            "success": True,
            "message": "Folder created",
            "folder_id": new_folder_id
        }

    def delete_folder(self, user_id: str, folder_id: str) -> dict:
        """
        Remove a folder and all its contents (files and subfolders), updating storage_used accordingly.

        Args:
            user_id (str): ID of the user performing the deletion (must own the folder).
            folder_id (str): ID of the folder to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Folder and all its contents deleted successfully"
            }
            or
            {
                "success": False,
                "error": str  # Explanation of failure
            }

        Constraints:
          - Only the folder's owner can delete the folder.
          - All files and subfolders (recursively) must be deleted.
          - User's storage_used updated by subtracting sizes of deleted files.
        """
        # Check folder exists
        folder = self.folders.get(folder_id)
        if not folder:
            return {"success": False, "error": "Folder not found"}

        # Check ownership
        if folder["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: cannot delete another user's folder"}

        # Helper: recursively get all descendant folder_ids
        def get_descendant_folder_ids(fid: str) -> list:
            descendants = []
            child_folders = [f for f in self.folders.values() if f.get("parent_folder_id") == fid and f["user_id"] == user_id]
            for cf in child_folders:
                descendants.append(cf["folder_id"])
                descendants.extend(get_descendant_folder_ids(cf["folder_id"]))
            return descendants

        # 1. Build set of all folders to delete (beginning with the target)
        folders_to_delete = [folder_id] + get_descendant_folder_ids(folder_id)

        # 2. Find all files in those folders
        files_to_delete = [file for file in self.files.values() if file["user_id"] == user_id and file["folder_id"] in folders_to_delete]
        total_bytes_freed = sum(file["size"] for file in files_to_delete)

        # 3. Delete files
        for file in files_to_delete:
            del self.files[file["file_id"]]

        # 4. Delete folders
        for fid in folders_to_delete:
            if fid in self.folders:
                del self.folders[fid]

        # 5. Update storage_used
        user = self.users.get(user_id)
        if user:
            user["storage_used"] = max(0.0, user["storage_used"] - total_bytes_freed)

        return {"success": True, "message": "Folder and all its contents deleted successfully"}

    def rename_folder(self, folder_id: str, new_name: str, user_id: str) -> dict:
        """
        Rename a folder within its parent, enforcing name uniqueness among siblings.

        Args:
            folder_id (str): The ID of the folder to rename.
            new_name (str): The new name to assign to the folder.
            user_id (str): The ID of the user making the request.

        Returns:
            dict: {
                "success": True,
                "message": "Folder renamed successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - User can only rename their own folders.
            - Folder name must be unique among sibling folders and files for the same user and parent.
            - All descendant folder/file 'path' attributes must be updated accordingly.
        """
        # 1. Folder existence
        folder = self.folders.get(folder_id)
        if not folder:
            return { "success": False, "error": "Folder not found." }

        # 2. Ownership check
        if folder['user_id'] != user_id:
            return { "success": False, "error": "Permission denied: not the folder owner." }

        # 3. Redundant rename (idempotent)
        if folder['name'] == new_name:
            return { "success": True, "message": "Folder renamed successfully." }

        # 4. Empty new_name
        if not isinstance(new_name, str) or not new_name.strip():
            return { "success": False, "error": "New folder name cannot be empty." }
        new_name = new_name.strip()

        parent_folder_id = folder.get('parent_folder_id')
        # 5. Uniqueness check for sibling folders
        for sibling in self.folders.values():
            if (
                sibling['user_id'] == user_id and
                sibling.get('parent_folder_id') == parent_folder_id and
                sibling['name'] == new_name and
                sibling['folder_id'] != folder_id
            ):
                return { "success": False, "error": "A sibling folder with the same name already exists." }
        # Uniqueness check for files in the same parent folder
        for file in self.files.values():
            if (
                file['user_id'] == user_id and
                file['folder_id'] == parent_folder_id and
                file['name'] == new_name
            ):
                return { "success": False, "error": "A file with the same name already exists in the parent folder." }

        # 6. Perform rename and update paths
        old_path = folder['path']
        # update folder name
        folder['name'] = new_name
        # build new path
        if parent_folder_id is not None:
            parent_folder = self.folders.get(parent_folder_id)
            if not parent_folder:
                return { "success": False, "error": "Parent folder not found." }
            parent_path = parent_folder['path']
            new_path = parent_path.rstrip('/') + '/' + new_name
        else:
            # Root folder
            new_path = '/' + new_name

        folder['path'] = new_path

        # Update paths of all descendant folders/files recursively
        old_path_prefix = old_path.rstrip('/')
        new_path_prefix = new_path.rstrip('/')

        # Descendant folders
        for desc_folder in self.folders.values():
            if (
                desc_folder['user_id'] == user_id and
                desc_folder['folder_id'] != folder_id and
                desc_folder['path'].startswith(old_path_prefix + '/')
            ):
                desc_folder['path'] = desc_folder['path'].replace(old_path_prefix + '/', new_path_prefix + '/', 1)
        # Descendant files
        for file in self.files.values():
            if (
                file['user_id'] == user_id and
                file['path'].startswith(old_path_prefix + '/')
            ):
                file['path'] = file['path'].replace(old_path_prefix + '/', new_path_prefix + '/', 1)

        return { "success": True, "message": "Folder renamed successfully." }

    def move_folder(self, user_id: str, folder_id: str, new_parent_folder_id: Optional[str]) -> dict:
        """
        Move a folder (and all its descendants) to a new parent folder for the same user,
        ensuring no name conflict within the target parent and preventing cycles.

        Args:
            user_id (str): ID of the user performing the action (must own the folder).
            folder_id (str): ID of the folder to move.
            new_parent_folder_id (Optional[str]): The folder ID of the target parent. None means user's root.

        Returns:
            dict: {
                "success": True,
                "message": "Folder moved successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Folder must exist and belong to the user.
            - Parent folder (if provided) must exist and belong to the user.
            - No name conflict within target parent folder.
            - Cannot move folder into itself or its descendants.
        """
        folder = self.folders.get(folder_id)
        if not folder or folder["user_id"] != user_id:
            return {"success": False, "error": "Folder not found or permission denied."}

        # Allow moving to root (None)
        if new_parent_folder_id is not None:
            new_parent = self.folders.get(new_parent_folder_id)
            if not new_parent or new_parent["user_id"] != user_id:
                return {"success": False, "error": "New parent folder does not exist or permission denied."}
        else:
            new_parent = None

        # Prevent moving folder into itself or its descendants
        descendant_ids = set()
        def collect_descendants(fid):
            for f in self.folders.values():
                if f.get("parent_folder_id") == fid and f["user_id"] == user_id:
                    descendant_ids.add(f["folder_id"])
                    collect_descendants(f["folder_id"])
        collect_descendants(folder_id)
        if new_parent_folder_id == folder_id or (new_parent_folder_id in descendant_ids):
            return {"success": False, "error": "Cannot move folder into itself or its descendants."}

        # Name conflict check in the new parent
        for f in self.folders.values():
            if f["user_id"] == user_id \
                and f.get("parent_folder_id") == new_parent_folder_id \
                and f["name"] == folder["name"] \
                and f["folder_id"] != folder_id:
                return {"success": False, "error": "A folder with the same name already exists in the target location."}

        # Compute new path
        if new_parent is None:
            new_path = "/" + folder["name"]
        else:
            # Ensure new_parent["path"] doesn't double slash
            parent_path = new_parent["path"].rstrip("/")
            new_path = parent_path + "/" + folder["name"]

        # Record old path to support updating descendants
        old_path_prefix = folder["path"]

        # Update folder
        folder["parent_folder_id"] = new_parent_folder_id
        folder["path"] = new_path
        self.folders[folder_id] = folder

        # Update paths of descendant folders and files
        for f in self.folders.values():
            if f["user_id"] == user_id and f["path"].startswith(old_path_prefix + "/"):
                # Compute new descendant path
                f["path"] = new_path + f["path"][len(old_path_prefix):]
        for file in self.files.values():
            if file["user_id"] == user_id and file["path"].startswith(old_path_prefix + "/"):
                # Compute new file path
                file["path"] = new_path + file["path"][len(old_path_prefix):]

        return {"success": True, "message": "Folder moved successfully"}

    def update_user_storage_quota(self, user_id: str, new_quota: float) -> dict:
        """
        Change a user's storage_quota (admin operation).

        Args:
            user_id (str): The ID of the user whose quota is to be set.
            new_quota (float): The new storage quota value to set (must be positive, and at least as large as storage_used).

        Returns:
            dict: {
                "success": True,
                "message": Description of the successful quota update
            }
            or
            {
                "success": False,
                "error": Error message describing the reason (invalid user, invalid quota etc.)
            }

        Constraints:
          - User must exist.
          - New quota must be > 0.
          - New quota must be >= current storage_used.
        """
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        storage_used = user["storage_used"]
        if new_quota <= 0:
            return {"success": False, "error": "New quota must be positive"}

        if new_quota < storage_used:
            return {"success": False, "error": f"New quota ({new_quota}) is less than current used storage ({storage_used})"}

        user["storage_quota"] = new_quota
        self.users[user_id] = user
        return {
            "success": True,
            "message": f"Updated storage quota for user {user_id} to {new_quota}"
        }

    def set_user_storage_used(self, user_id: str, storage_used: float) -> dict:
        """
        Directly update the storage_used value for the specified user.
        Intended for internal/admin use (e.g., after recalculation or bulk updates).

        Args:
            user_id (str): The user ID whose storage_used value is to be updated.
            storage_used (float): The new storage used value to set (should be non-negative).

        Returns:
            dict:
                - On success: { "success": True, "message": "Storage used for user <user_id> updated to <storage_used>." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - user_id must exist.
            - storage_used must be non-negative.
            - It is strongly recommended (though not always strictly required for admin/internal ops) that storage_used does not exceed storage_quota.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": f"User {user_id} does not exist" }

        if not isinstance(storage_used, (int, float)):
            return { "success": False, "error": "storage_used must be a number" }

        if storage_used < 0:
            return { "success": False, "error": "storage_used must be non-negative" }

        if storage_used > user["storage_quota"]:
            return { 
                "success": False, 
                "error": "storage_used exceeds storage_quota; operation denied for safety"
            }

        user["storage_used"] = storage_used

        return {
            "success": True,
            "message": f"Storage used for user {user_id} updated to {storage_used}."
        }


class CloudStorageAccountManagementSystem(BaseEnv):
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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_storage_usage(self, **kwargs):
        return self._call_inner_tool('get_user_storage_usage', kwargs)

    def recalculate_user_storage_usage(self, **kwargs):
        return self._call_inner_tool('recalculate_user_storage_usage', kwargs)

    def list_user_folders(self, **kwargs):
        return self._call_inner_tool('list_user_folders', kwargs)

    def get_folder_by_path(self, **kwargs):
        return self._call_inner_tool('get_folder_by_path', kwargs)

    def get_folder_by_id(self, **kwargs):
        return self._call_inner_tool('get_folder_by_id', kwargs)

    def list_files_in_folder(self, **kwargs):
        return self._call_inner_tool('list_files_in_folder', kwargs)

    def get_file_by_id(self, **kwargs):
        return self._call_inner_tool('get_file_by_id', kwargs)

    def get_file_by_name_in_folder(self, **kwargs):
        return self._call_inner_tool('get_file_by_name_in_folder', kwargs)

    def get_folder_structure(self, **kwargs):
        return self._call_inner_tool('get_folder_structure', kwargs)

    def upload_file(self, **kwargs):
        return self._call_inner_tool('upload_file', kwargs)

    def delete_file(self, **kwargs):
        return self._call_inner_tool('delete_file', kwargs)

    def move_file(self, **kwargs):
        return self._call_inner_tool('move_file', kwargs)

    def rename_file(self, **kwargs):
        return self._call_inner_tool('rename_file', kwargs)

    def create_folder(self, **kwargs):
        return self._call_inner_tool('create_folder', kwargs)

    def delete_folder(self, **kwargs):
        return self._call_inner_tool('delete_folder', kwargs)

    def rename_folder(self, **kwargs):
        return self._call_inner_tool('rename_folder', kwargs)

    def move_folder(self, **kwargs):
        return self._call_inner_tool('move_folder', kwargs)

    def update_user_storage_quota(self, **kwargs):
        return self._call_inner_tool('update_user_storage_quota', kwargs)

    def set_user_storage_used(self, **kwargs):
        return self._call_inner_tool('set_user_storage_used', kwargs)
