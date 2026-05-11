# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class SkillInfo(TypedDict):
    skill_id: str
    name: str
    description: str
    category_id: str         # Must reference an existing category
    related_files: List[str] # List of file_ids

class CategoryInfo(TypedDict):
    category_id: str
    name: str
    description: str

class FileInfo(TypedDict):
    file_id: str
    file_name: str
    file_type: str
    url: str
    associated_skill_ids: List[str] # List of skill_ids

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for skill, category, and resource management.
        """

        # Skills: {skill_id: SkillInfo}
        self.skills: Dict[str, SkillInfo] = {}

        # Categories: {category_id: CategoryInfo}
        self.categories: Dict[str, CategoryInfo] = {}

        # Files/Resources: {file_id: FileInfo}
        self.files: Dict[str, FileInfo] = {}

        # Constraints:
        # - Each skill is linked to one category (skill.category_id must be in categories)
        # - A skill can be associated with zero or more files/resources (skill.related_files: List[file_id])
        # - Categories must exist before skills can reference them
        # - Each file/resource can be associated with one or more skills (file.associated_skill_ids: List[skill_id])

    def get_category_by_name(self, name: str) -> dict:
        """
        Retrieve details of a category given its name.

        Args:
            name (str): The name of the category to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CategoryInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Category not found"
                    }

        Constraints:
            - Returns the first exact match for category name.
            - Category names must be matched exactly (case-sensitive).
        """
        for category in self.categories.values():
            if category["name"] == name:
                return {"success": True, "data": category}
        return {"success": False, "error": "Category not found"}

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Retrieve a category’s details using the category_id.

        Args:
            category_id (str): The unique ID of the category.

        Returns:
            dict: {
                "success": True,
                "data": CategoryInfo,  # Details of the category
            }
            or
            {
                "success": False,
                "error": "Category not found"
            }

        Constraints:
            - The category_id must exist in the platform.
        """
        category = self.categories.get(category_id)
        if not category:
            return { "success": False, "error": "Category not found" }
        return { "success": True, "data": category }

    def list_all_categories(self) -> dict:
        """
        Get a list of all skill categories in the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo]  # List of category information, possibly empty if none present
            }
        Constraints:
            None
        """
        categories_list = list(self.categories.values())
        return { "success": True, "data": categories_list }

    def list_skills_by_category(self, category_id: str) -> dict:
        """
        Retrieve all skills belonging to the specified category_id.

        Args:
            category_id (str): The identifier of the category.

        Returns:
            dict:
                success: True and a list of SkillInfo for matching skills
                OR
                success: False and an error message if the category does not exist

        Constraints:
            - The given category_id must exist in the categories.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        result = [
            skill_info for skill_info in self.skills.values()
            if skill_info["category_id"] == category_id
        ]

        return { "success": True, "data": result }

    def get_skill_by_id(self, skill_id: str) -> dict:
        """
        Retrieve the full detail of a specific skill by its skill_id.

        Args:
            skill_id (str): The unique ID of the skill to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": SkillInfo  # If found
            }
            or
            {
                "success": False,
                "error": "Skill ID not found"  # If the skill_id is not present
            }

        Constraints:
            - None for query; the method will simply check presence.
        """
        skill = self.skills.get(skill_id)
        if skill is None:
            return { "success": False, "error": "Skill ID not found" }    
        return { "success": True, "data": skill }

    def get_skill_by_name(self, name: str) -> dict:
        """
        Retrieve detailed information for a specific skill by its name.

        Args:
            name (str): The name of the skill to look up (case-sensitive).

        Returns:
            dict: {
                "success": True,
                "data": SkillInfo
            }
            or
            {
                "success": False,
                "error": "Skill not found"
            }

        Constraints:
            - Skill name must exactly match (case-sensitive).
            - If multiple skills share a name, the first match is returned.
        """
        for skill in self.skills.values():
            if skill["name"] == name:
                return { "success": True, "data": skill }
        return { "success": False, "error": "Skill not found" }

    def list_all_skills(self) -> dict:
        """
        List all skills currently present in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SkillInfo]  # List of all skills (can be empty)
            }
        """
        all_skills = list(self.skills.values())
        return { "success": True, "data": all_skills }

    def list_files_by_skill(self, skill_id: str) -> dict:
        """
        Retrieve all files/resources (with metadata) associated with the given skill_id.

        Args:
            skill_id (str): The identifier of the skill.

        Returns:
            dict: {
                "success": True,
                "data": List[FileInfo],  # All files/resources linked to this skill (may be empty).
            }
            OR
            {
                "success": False,
                "error": str  # Error message if skill does not exist.
            }

        Constraints:
            - Skill must exist in the platform.
        """
        if skill_id not in self.skills:
            return { "success": False, "error": "Skill does not exist" }

        # Collect files where the skill_id appears in file's associated_skill_ids
        result = [
            file_info for file_info in self.files.values()
            if skill_id in file_info.get("associated_skill_ids", [])
        ]
        return { "success": True, "data": result }

    def get_file_by_id(self, file_id: str) -> dict:
        """
        Retrieve details (metadata) of a file/resource by its unique file_id.

        Args:
            file_id (str): The unique identifier of the file/resource.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": FileInfo (the metadata dictionary of the file/resource)
                  }
                - On failure: {
                      "success": False,
                      "error": "File/resource with specified file_id does not exist"
                  }

        Constraints:
            - file_id must correspond to an existing file/resource in the environment.
        """
        file_info = self.files.get(file_id)
        if not file_info:
            return {
                "success": False,
                "error": "File/resource with specified file_id does not exist"
            }
        return {
            "success": True,
            "data": file_info
        }

    def get_files_by_name(self, file_name: str) -> dict:
        """
        Search for files/resources whose file_name contains the given substring (case-insensitive).
    
        Args:
            file_name (str): The (partial) file/resource name to search for.
    
        Returns:
            dict: {
                "success": True,
                "data": List[FileInfo],  # List of matching file/resource info (may be empty if none match)
            }
            or
            {
                "success": False,
                "error": str  # Error message if input invalid
            }
    
        Constraints:
            - file_name must be a non-empty string.
        """
        if not isinstance(file_name, str) or not file_name.strip():
            return { "success": False, "error": "Invalid file_name: must be a non-empty string." }

        search = file_name.strip().lower()
        result = [
            file_info
            for file_info in self.files.values()
            if search in file_info["file_name"].lower()
        ]

        return { "success": True, "data": result }

    def list_skills_by_file(self, file_id: str) -> dict:
        """
        Return the list of skill_ids associated with the file identified by file_id.

        Args:
            file_id (str): The unique ID of the file/resource.

        Returns:
            dict: {
                "success": True,
                "data": List[str],   # The skill_ids associated with this file (may be empty)
            }
            OR
            {
                "success": False,
                "error": "File does not exist"
            }

        Constraints:
            - The file_id must refer to an existing file/resource.
        """
        file_info = self.files.get(file_id)
        if not file_info:
            return {"success": False, "error": "File does not exist"}

        return {"success": True, "data": file_info["associated_skill_ids"].copy()}

    def list_files_by_category(self, category_id: str) -> dict:
        """
        Retrieve all files/resources (FileInfo) associated with any skill in a given category.

        Args:
            category_id (str): The ID of the target category.

        Returns:
            dict:
                - success: True, data: List[FileInfo] of unique files linked to any skill in the category.
                - success: False, error: If the category does not exist.

        Constraints:
            - Category with the given ID must exist.
            - Files may be linked to multiple skills; output is deduplicated by file_id.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        # Collect all skill_ids under this category
        skill_ids = [skill_id for skill_id, skill in self.skills.items()
                     if skill["category_id"] == category_id]

        # Aggregate all related file_ids for these skills
        file_ids_set = set()
        for skill_id in skill_ids:
            related_files = self.skills[skill_id].get("related_files", [])
            file_ids_set.update(related_files)

        # Retrieve FileInfo for each file_id (only if actually present in self.files)
        files_info = [self.files[file_id] for file_id in file_ids_set if file_id in self.files]

        return { "success": True, "data": files_info }

    def add_category(self, category_id: str, name: str, description: str) -> dict:
        """
        Add a new category to the platform. The category_id must be unique.

        Args:
            category_id (str): Unique identifier for the category.
            name (str): Name of the category.
            description (str): Description of the category.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "<category_id> created" }
                On failure:
                    { "success": False, "error": "Category ID already exists" }
                    or
                    { "success": False, "error": "Invalid input - category_id, name, and description required" }

        Constraints:
            - category_id must be unique within categories.
        """
        if not category_id or not name or not description:
            return {
                "success": False,
                "error": "Invalid input - category_id, name, and description required"
            }

        if category_id in self.categories:
            return {
                "success": False,
                "error": "Category ID already exists"
            }
    
        new_category: CategoryInfo = {
            "category_id": category_id,
            "name": name,
            "description": description
        }
    
        self.categories[category_id] = new_category
        return {
            "success": True,
            "message": f"Category '{category_id}' created"
        }

    def update_category(self, category_id: str, name: str = None, description: str = None) -> dict:
        """
        Edit the details (name, description) of an existing category.

        Args:
            category_id (str): ID of the category to update (must exist).
            name (str, optional): New name for the category.
            description (str, optional): New description for the category.

        Returns:
            dict: {
                "success": True,
                "message": "Category updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - category_id must reference an existing category.
            - At least one of name or description should be provided to update.
            - Unspecified fields are left unchanged.
        """
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist."}
    
        if name is None and description is None:
            return {"success": False, "error": "No update fields provided."}
    
        cat = self.categories[category_id]
        if name is not None:
            cat["name"] = name
        if description is not None:
            cat["description"] = description
    
        self.categories[category_id] = cat
        return {"success": True, "message": "Category updated successfully."}

    def delete_category(self, category_id: str) -> dict:
        """
        Remove a category by its ID. Deletion is only allowed if no skills are currently assigned to the category.

        Args:
            category_id (str): Unique identifier of the category to delete.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Category deleted: <category_id>"
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason: non-existent, or skills still linked.
                }
        Constraints:
            - The category must exist.
            - No skill can reference the category (category must not be used by any skill).
        """
        # Check existence
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        # Check if any skill is linked to this category
        for skill in self.skills.values():
            if skill["category_id"] == category_id:
                return { "success": False, "error": "Category cannot be deleted: skills are linked to it" }

        # Proceed to delete
        del self.categories[category_id]
        return { "success": True, "message": f"Category deleted: {category_id}" }

    def add_skill(
        self, 
        skill_id: str, 
        name: str, 
        description: str, 
        category_id: str, 
        related_files: List[str] = None
    ) -> dict:
        """
        Add a new skill.

        Args:
            skill_id (str): Unique identifier for the skill.
            name (str): Skill name.
            description (str): Description of the skill.
            category_id (str): ID of the category the skill belongs to (must exist).
            related_files (List[str], optional): List of file_ids to associate with this skill (must all exist).

        Returns:
            dict: 
                - On success: {"success": True, "message": "Skill '<skill_id>' added."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - skill_id must not duplicate existing skill.
            - category_id must exist in the platform.
            - All related file_ids must exist.
            - If files are linked to this skill, update each file's associated_skill_ids.
        """

        if skill_id in self.skills:
            return { "success": False, "error": f"Skill ID '{skill_id}' already exists." }
        if category_id not in self.categories:
            return { "success": False, "error": f"Category ID '{category_id}' does not exist." }
        if related_files is None:
            related_files = []
        for fid in related_files:
            if fid not in self.files:
                return { "success": False, "error": f"Related file ID '{fid}' does not exist." }

        # Create and add the skill
        new_skill = {
            "skill_id": skill_id,
            "name": name,
            "description": description,
            "category_id": category_id,
            "related_files": list(related_files),
        }
        self.skills[skill_id] = new_skill

        # Update each FileInfo's associated_skill_ids if skill is linked to it
        for fid in related_files:
            if skill_id not in self.files[fid]['associated_skill_ids']:
                self.files[fid]['associated_skill_ids'].append(skill_id)

        return { "success": True, "message": f"Skill '{skill_id}' added." }

    def update_skill(
        self, 
        skill_id: str, 
        name: str = None, 
        description: str = None, 
        category_id: str = None, 
        related_files: list = None
    ) -> dict:
        """
        Edit metadata of a skill (name, description, category, linked files).
    
        Args:
            skill_id (str): The ID of the skill to update.
            name (str, optional): New skill name.
            description (str, optional): New skill description.
            category_id (str, optional): New category ID (must exist).
            related_files (list of str, optional): New list of related file IDs (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Skill updated successfully."
            }
            or
            {
                "success": False,
                "error": <error message>
            }
    
        Constraints:
            - skill_id must refer to an existing skill.
            - If category_id is provided, it must exist.
            - If related_files is provided, all files must exist.
            - Adjust associations in both Skill and File/Resource accordingly.
        """
        # Validate skill existence
        skill = self.skills.get(skill_id)
        if not skill:
            return { "success": False, "error": "Skill not found." }

        # Validate category if changed
        if category_id is not None:
            if category_id not in self.categories:
                return { "success": False, "error": "Category does not exist." }

        # Validate related_files if changed
        if related_files is not None:
            for file_id in related_files:
                if file_id not in self.files:
                    return { "success": False, "error": f"File {file_id} does not exist." }

        # Update name/description/category_id
        if name is not None:
            skill["name"] = name
        if description is not None:
            skill["description"] = description
        if category_id is not None:
            skill["category_id"] = category_id

        # Handle related_files and cross-reference with FileInfo objects
        if related_files is not None:
            old_files = set(skill["related_files"])
            new_files = set(related_files)

            # Remove skill_id from files no longer linked
            for file_id in old_files - new_files:
                file_info = self.files.get(file_id)
                if file_info and skill_id in file_info["associated_skill_ids"]:
                    file_info["associated_skill_ids"].remove(skill_id)
        
            # Add skill_id to newly linked files
            for file_id in new_files - old_files:
                file_info = self.files.get(file_id)
                if file_info and skill_id not in file_info["associated_skill_ids"]:
                    file_info["associated_skill_ids"].append(skill_id)

            # Update the skill's related_files
            skill["related_files"] = related_files

        return { "success": True, "message": "Skill updated successfully." }

    def delete_skill(self, skill_id: str) -> dict:
        """
        Remove a skill from the platform, and unlink it from all associated files/resources.

        Args:
            skill_id (str): The unique identifier of the skill to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Skill <skill_id> deleted successfully." }
                - On failure: { "success": False, "error": "Skill <skill_id> does not exist." }

        Constraints:
            - The skill must already exist in the platform.
            - After deletion, any files/resources that were linked to this skill must have the reference removed from their 'associated_skill_ids'.
            - The category and files themselves are not deleted.
        """
        if skill_id not in self.skills:
            return { "success": False, "error": f"Skill {skill_id} does not exist." }
    
        # Remove this skill_id from all associated files/resources
        for file_info in self.files.values():
            if skill_id in file_info['associated_skill_ids']:
                file_info['associated_skill_ids'] = [
                    sid for sid in file_info['associated_skill_ids'] if sid != skill_id
                ]
    
        # Remove the skill from the skills dictionary
        del self.skills[skill_id]

        return { "success": True, "message": f"Skill {skill_id} deleted successfully." }

    def add_file(self, file_id: str, file_name: str, file_type: str, url: str, associated_skill_ids: list) -> dict:
        """
        Add a new file/resource to the platform.

        Args:
            file_id (str): Unique identifier for the file/resource.
            file_name (str): Name/title of the file/resource.
            file_type (str): File/resource type (e.g., 'pdf', 'link', etc.).
            url (str): URL or path for the file/resource.
            associated_skill_ids (list of str): List of skill_ids to link this file to (can be empty).

        Returns:
            dict: {
                "success": True,
                "message": "File added successfully"
            }
            or
            {
                "success": False,
                "error": <error description>
            }
        Constraints:
            - file_id must be unique (not already in self.files).
            - Each skill_id in associated_skill_ids must exist in self.skills.
            - File will be linked to skills by updating file.associated_skill_ids,
              but does not update skill.related_files; that is handled separately.
        """
        # Check uniqueness of file_id
        if file_id in self.files:
            return {"success": False, "error": "File ID already exists."}

        # Validate skills (if any)
        for sid in associated_skill_ids:
            if sid not in self.skills:
                return {"success": False, "error": f"Associated skill_id '{sid}' does not exist."}

        # Create FileInfo record
        file_info = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "url": url,
            "associated_skill_ids": list(associated_skill_ids) if associated_skill_ids else []
        }

        # Add to files
        self.files[file_id] = file_info

        return {"success": True, "message": "File added successfully"}

    def update_file(
        self,
        file_id: str,
        file_name: str = None,
        file_type: str = None,
        url: str = None,
        associated_skill_ids: list = None,
    ) -> dict:
        """
        Edit metadata of a file/resource, including linkage to skills.

        Args:
            file_id (str): The ID of the file/resource to edit.
            file_name (str, optional): New file name.
            file_type (str, optional): New file type.
            url (str, optional): New URL.
            associated_skill_ids (list, optional): New list of skill_ids to associate with.

        Returns:
            dict: 
                On success: {"success": True, "message": "File metadata updated." }
                On failure: {"success": False, "error": <reason> }

        Constraints:
            - File must exist.
            - All skills in associated_skill_ids must exist.
            - Ensure backlinks between file and skills are consistent.
        """
        if file_id not in self.files:
            return {"success": False, "error": "File not found."}

        file_info = self.files[file_id]

        # Update fields if provided
        if file_name is not None:
            file_info["file_name"] = file_name
        if file_type is not None:
            file_info["file_type"] = file_type
        if url is not None:
            file_info["url"] = url

        if associated_skill_ids is not None:
            # Check all skill IDs exist
            for skill_id in associated_skill_ids:
                if skill_id not in self.skills:
                    return {"success": False, "error": f"Skill ID '{skill_id}' does not exist."}

            # Find which skills need to be unlinked
            old_skill_ids = set(file_info["associated_skill_ids"])
            new_skill_ids = set(associated_skill_ids)
            to_unlink = old_skill_ids - new_skill_ids
            to_link = new_skill_ids - old_skill_ids

            # Unlink this file from skills no longer associated
            for skill_id in to_unlink:
                skill = self.skills[skill_id]
                if file_id in skill["related_files"]:
                    skill["related_files"].remove(file_id)

            # Link this file to newly associated skills
            for skill_id in to_link:
                skill = self.skills[skill_id]
                if file_id not in skill["related_files"]:
                    skill["related_files"].append(file_id)

            # Update the file's backlinks
            file_info["associated_skill_ids"] = associated_skill_ids

        self.files[file_id] = file_info
        return {"success": True, "message": "File metadata updated."}

    def delete_file(self, file_id: str) -> dict:
        """
        Remove a file/resource from the platform.

        Args:
            file_id (str): The ID of the file/resource to delete.

        Returns:
            dict: {
                "success": True,
                "message": "File <file_id> deleted."
            }
            or
            {
                "success": False,
                "error": "File not found."
            }

        Constraints:
            - File must exist.
            - When deleting a file, remove its file_id from related_files in all skills.
            - No skill.related_files should reference the deleted file after the operation.
        """
        if file_id not in self.files:
            return { "success": False, "error": "File not found." }

        # Remove file_id from all skills' related_files
        for skill in self.skills.values():
            if file_id in skill["related_files"]:
                skill["related_files"].remove(file_id)

        # Remove file from platform
        del self.files[file_id]

        return { "success": True, "message": f"File {file_id} deleted." }

    def link_file_to_skill(self, file_id: str, skill_id: str) -> dict:
        """
        Associate an existing file with a skill.

        Args:
            file_id (str): The ID of the file to associate.
            skill_id (str): The ID of the skill to associate the file with.

        Returns:
            dict:
                - On success: { "success": True, "message": "File linked to skill." }
                - On error:
                    { "success": False, "error": "File does not exist." }
                    { "success": False, "error": "Skill does not exist." }
                    { "success": False, "error": "File is already linked to skill." }

        Constraints:
            - File and skill must both exist.
            - Association must not already exist.
            - Maintains many-to-many relation: adds skill_id to file, file_id to skill.
        """
        # Check skill exists
        if skill_id not in self.skills:
            return { "success": False, "error": "Skill does not exist." }
        # Check file exists
        if file_id not in self.files:
            return { "success": False, "error": "File does not exist." }
        # Check if already linked
        if file_id in self.skills[skill_id]["related_files"]:
            return { "success": False, "error": "File is already linked to skill." }
        # Perform association
        self.skills[skill_id]["related_files"].append(file_id)
        if skill_id not in self.files[file_id]["associated_skill_ids"]:
            self.files[file_id]["associated_skill_ids"].append(skill_id)
        return { "success": True, "message": "File linked to skill." }

    def unlink_file_from_skill(self, file_id: str, skill_id: str) -> dict:
        """
        Remove the association between a file/resource and a skill.

        Args:
            file_id (str): ID of the file to unlink.
            skill_id (str): ID of the skill to unlink from.

        Returns:
            dict: 
                - On success: {"success": True, "message": "File unlinked from skill successfully."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
          - Both file_id and skill_id must exist.
          - The association is removed from both sides (SkillInfo.related_files and FileInfo.associated_skill_ids).
          - Idempotent: if already unlinked, still considered success.
        """
        # Check existence
        if skill_id not in self.skills:
            return {"success": False, "error": "Skill does not exist."}
        if file_id not in self.files:
            return {"success": False, "error": "File does not exist."}

        skill = self.skills[skill_id]
        file = self.files[file_id]

        # Remove file_id from skill's related_files if present
        if file_id in skill['related_files']:
            skill['related_files'].remove(file_id)

        # Remove skill_id from file's associated_skill_ids if present
        if skill_id in file['associated_skill_ids']:
            file['associated_skill_ids'].remove(skill_id)

        return {"success": True, "message": "File unlinked from skill successfully."}

    def bulk_link_files_to_skill(self, skill_id: str, file_ids: list) -> dict:
        """
        Associate multiple files with a single skill.

        Args:
            skill_id (str): The skill to associate files with.
            file_ids (list): List of file IDs (str) to link to the skill.

        Returns:
            dict: {
                "success": True,
                "message": "N files linked to skill <skill_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - skill_id must exist in self.skills.
            - Each file_id in file_ids must exist in self.files.
            - Linking is idempotent: files already linked are ignored.
            - Both skill.related_files and file.associated_skill_ids must be updated symmetrically.
        """
        # Check that skill exists
        if skill_id not in self.skills:
            return { "success": False, "error": f"Skill '{skill_id}' does not exist." }

        # Check that all file_ids exist
        for file_id in file_ids:
            if file_id not in self.files:
                return { "success": False, "error": f"File '{file_id}' does not exist." }

        skill = self.skills[skill_id]
        files_linked = 0

        for file_id in file_ids:
            # Add file_id to skill.related_files if not present
            if file_id not in skill["related_files"]:
                skill["related_files"].append(file_id)
            # Add skill_id to file.associated_skill_ids if not present
            if skill_id not in self.files[file_id]["associated_skill_ids"]:
                self.files[file_id]["associated_skill_ids"].append(skill_id)
            files_linked += 1

        return {
            "success": True,
            "message": f"{files_linked} files linked to skill '{skill_id}'."
        }

    def bulk_unlink_files_from_skill(self, skill_id: str, file_ids: list) -> dict:
        """
        Remove multiple file associations from a single skill.

        Args:
            skill_id (str): ID of the skill whose file associations are to be removed.
            file_ids (List[str]): List of file_ids to unlink from the skill.

        Returns:
            dict:
                - success: True/False
                - message: On success, summary of unlink results.
                - error: On failure, reason.

        Constraints:
            - Skill must exist.
            - Files must exist to be unlinked; invalid file_ids are skipped with notice.
            - Unlinking an already-unlinked file is ignored.
            - Updates both skill.related_files and file.associated_skill_ids.
        """
        if skill_id not in self.skills:
            return { "success": False, "error": "Skill not found" }
    
        skill = self.skills[skill_id]
        successfully_unlinked = []
        skipped_not_found = []
        skipped_not_linked = []
    
        for fid in file_ids:
            if fid not in self.files:
                skipped_not_found.append(fid)
                continue

            # Remove file from skill's related_files if present
            if fid in skill["related_files"]:
                skill["related_files"].remove(fid)
                unlinked = True
            else:
                unlinked = False

            # Remove skill from file's associated_skill_ids if present
            file_info = self.files[fid]
            if skill_id in file_info["associated_skill_ids"]:
                file_info["associated_skill_ids"].remove(skill_id)
                unlinked = True or unlinked  # If one/unlinked, mark as unlinked

            if unlinked:
                successfully_unlinked.append(fid)
            else:
                skipped_not_linked.append(fid)
    
        msg_parts = []
        if successfully_unlinked:
            msg_parts.append(f"Successfully unlinked: {successfully_unlinked}")
        if skipped_not_found:
            msg_parts.append(f"Skipped (file(s) not found): {skipped_not_found}")
        if skipped_not_linked:
            msg_parts.append(f"Skipped (file(s) not linked to skill): {skipped_not_linked}")
        if not msg_parts:
            msg_parts.append("No action taken.")
    
        return {
            "success": True,
            "message": "; ".join(msg_parts)
        }


class SkillManagementPlatform(BaseEnv):
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

    def get_category_by_name(self, **kwargs):
        return self._call_inner_tool('get_category_by_name', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def list_all_categories(self, **kwargs):
        return self._call_inner_tool('list_all_categories', kwargs)

    def list_skills_by_category(self, **kwargs):
        return self._call_inner_tool('list_skills_by_category', kwargs)

    def get_skill_by_id(self, **kwargs):
        return self._call_inner_tool('get_skill_by_id', kwargs)

    def get_skill_by_name(self, **kwargs):
        return self._call_inner_tool('get_skill_by_name', kwargs)

    def list_all_skills(self, **kwargs):
        return self._call_inner_tool('list_all_skills', kwargs)

    def list_files_by_skill(self, **kwargs):
        return self._call_inner_tool('list_files_by_skill', kwargs)

    def get_file_by_id(self, **kwargs):
        return self._call_inner_tool('get_file_by_id', kwargs)

    def get_files_by_name(self, **kwargs):
        return self._call_inner_tool('get_files_by_name', kwargs)

    def list_skills_by_file(self, **kwargs):
        return self._call_inner_tool('list_skills_by_file', kwargs)

    def list_files_by_category(self, **kwargs):
        return self._call_inner_tool('list_files_by_category', kwargs)

    def add_category(self, **kwargs):
        return self._call_inner_tool('add_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def delete_category(self, **kwargs):
        return self._call_inner_tool('delete_category', kwargs)

    def add_skill(self, **kwargs):
        return self._call_inner_tool('add_skill', kwargs)

    def update_skill(self, **kwargs):
        return self._call_inner_tool('update_skill', kwargs)

    def delete_skill(self, **kwargs):
        return self._call_inner_tool('delete_skill', kwargs)

    def add_file(self, **kwargs):
        return self._call_inner_tool('add_file', kwargs)

    def update_file(self, **kwargs):
        return self._call_inner_tool('update_file', kwargs)

    def delete_file(self, **kwargs):
        return self._call_inner_tool('delete_file', kwargs)

    def link_file_to_skill(self, **kwargs):
        return self._call_inner_tool('link_file_to_skill', kwargs)

    def unlink_file_from_skill(self, **kwargs):
        return self._call_inner_tool('unlink_file_from_skill', kwargs)

    def bulk_link_files_to_skill(self, **kwargs):
        return self._call_inner_tool('bulk_link_files_to_skill', kwargs)

    def bulk_unlink_files_from_skill(self, **kwargs):
        return self._call_inner_tool('bulk_unlink_files_from_skill', kwargs)
