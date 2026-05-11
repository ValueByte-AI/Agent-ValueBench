# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class DirectoryInfo(TypedDict):
    path: str
    parent_directory: str
    subdirectories: List[str]
    files: List[str]

class FileInfo(TypedDict):
    name: str
    path: str
    parent_directory: str
    extension: str
    associated_class: str  # fully qualified class name

class JavaClassInfo(TypedDict):
    fully_qualified_name: str
    package_name: str
    class_name: str
    file_path: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Directories in the project: {path: DirectoryInfo}
        self.directories: Dict[str, DirectoryInfo] = {}

        # Files in the project: {path: FileInfo}
        self.files: Dict[str, FileInfo] = {}

        # Java classes: {fully_qualified_name: JavaClassInfo}
        self.java_classes: Dict[str, JavaClassInfo] = {}

        # Constraints:
        # - Each JavaClass must correspond to exactly one File, and the File extension must be .java.
        # - Package hierarchies (com.example.utilities) map to nested directories (com/example/utilities).
        # - The file path to a Java class is constructed by joining the package path with the class file name.
        # - The directory structure must be consistent with the declared package names in the source files.

    @staticmethod
    def _package_to_relative_path(package_name: str) -> str:
        return package_name.replace('.', '/')

    @staticmethod
    def _strip_known_source_root(path: str) -> str:
        normalized = path.strip("/\\")
        for root in ("src/main/java", "src/test/java"):
            if normalized == root:
                return ""
            prefix = root + "/"
            if normalized.startswith(prefix):
                return normalized[len(prefix):]
        return normalized

    @staticmethod
    def _extract_source_prefix(directory_path: str, package_relative_path: str) -> str:
        normalized_dir = directory_path.replace("\\", "/").rstrip("/")
        normalized_pkg = package_relative_path.strip("/\\")
        if not normalized_pkg:
            return normalized_dir
        if normalized_dir == normalized_pkg:
            return ""
        suffix = "/" + normalized_pkg
        if normalized_dir.endswith(suffix):
            return normalized_dir[:-len(suffix)]
        return ""

    @staticmethod
    def _join_source_prefix(source_prefix: str, package_relative_path: str) -> str:
        normalized_prefix = source_prefix.replace("\\", "/").rstrip("/")
        normalized_relative = package_relative_path.strip("/\\")
        if not normalized_prefix:
            return normalized_relative
        if not normalized_relative:
            return normalized_prefix
        return normalized_prefix + "/" + normalized_relative

    @staticmethod
    def _path_prefixes(path: str) -> List[str]:
        normalized = path.replace("\\", "/").rstrip("/")
        if not normalized:
            return []
        is_absolute = normalized.startswith("/")
        parts = [part for part in normalized.strip("/").split("/") if part]
        prefixes: List[str] = []
        current = ""
        for part in parts:
            if not current:
                current = f"/{part}" if is_absolute else part
            else:
                current = f"{current}/{part}"
            prefixes.append(current)
        return prefixes

    def _directory_match_priority(self, directory_path: str):
        normalized = directory_path.strip("/\\")
        if normalized.startswith("src/main/java/") or normalized == "src/main/java":
            return (0, len(normalized))
        if normalized.startswith("src/test/java/") or normalized == "src/test/java":
            return (1, len(normalized))
        return (2, len(normalized))

    def _get_existing_directory_for_package(self, package_name: str):
        if not package_name:
            return None

        for class_info in self.java_classes.values():
            if class_info.get("package_name") != package_name:
                continue
            file_info = self.files.get(class_info.get("file_path"))
            if not file_info:
                continue
            parent_directory = file_info.get("parent_directory")
            if parent_directory in self.directories:
                return parent_directory

        package_relative_path = self._package_to_relative_path(package_name)
        matches = []
        for directory_path in self.directories:
            normalized = directory_path.strip("/\\")
            if normalized == package_relative_path or normalized.endswith("/" + package_relative_path):
                matches.append(directory_path)
        if not matches:
            return None
        matches.sort(key=self._directory_match_priority)
        return matches[0]

    def _infer_source_prefix_for_package(self, package_name: str):
        parent_package = package_name.rsplit(".", 1)[0] if "." in package_name else ""
        if parent_package:
            parent_directory = self._get_existing_directory_for_package(parent_package)
            if parent_directory:
                return self._extract_source_prefix(
                    parent_directory,
                    self._package_to_relative_path(parent_package),
                )

        for class_info in self.java_classes.values():
            file_info = self.files.get(class_info.get("file_path"))
            if not file_info:
                continue
            parent_directory = file_info.get("parent_directory", "")
            extracted = self._extract_source_prefix(
                parent_directory,
                self._package_to_relative_path(class_info.get("package_name", "")),
            )
            if extracted or parent_directory == self._package_to_relative_path(class_info.get("package_name", "")):
                return extracted
        return ""

    def _remove_file_from_directory_listing(self, directory_path: str, file_info: dict) -> None:
        directory = self.directories.get(directory_path)
        if not directory:
            return
        stale_refs = {file_info.get("name"), file_info.get("path")}
        directory["files"] = [entry for entry in directory["files"] if entry not in stale_refs]

    def _add_file_to_directory_listing(self, directory_path: str, file_info: dict) -> None:
        directory = self.directories.get(directory_path)
        if not directory:
            return
        preferred_ref = file_info.get("path") if any("/" in entry for entry in directory["files"]) else file_info.get("name")
        if preferred_ref and preferred_ref not in directory["files"]:
            directory["files"].append(preferred_ref)

    def _drop_stale_directory_file_refs(self, directory_path: str) -> None:
        directory = self.directories.get(directory_path)
        if not directory:
            return
        live_refs = set()
        for path, file_info in self.files.items():
            if file_info.get("parent_directory") == directory_path:
                live_refs.add(path)
                live_refs.add(file_info.get("name"))
        directory["files"] = [entry for entry in directory["files"] if entry in live_refs]

    def get_java_class_info(self, fully_qualified_name: str) -> dict:
        """
        Retrieve all metadata for a Java class by its fully qualified name.

        Args:
            fully_qualified_name (str): The canonical name of the Java class (e.g., 'com.example.MyClass').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": JavaClassInfo,  # All metadata about the class
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Java class not found"
                    }

        Constraints:
            - The Java class must exist in the environment.
            - If not found, returns an error.
        """
        class_info = self.java_classes.get(fully_qualified_name)
        if class_info is None:
            return { "success": False, "error": "Java class not found" }
        return { "success": True, "data": class_info }

    def get_file_info(self, file_path: str) -> dict:
        """
        Retrieve metadata for a file specified by its file path.

        Args:
            file_path (str): The absolute path of the file to retrieve metadata for.

        Returns:
            dict: {
                "success": True,
                "data": FileInfo,  # Metadata of the file, including associated class and extension
            }
            or
            {
                "success": False,
                "error": str  # "File does not exist"
            }

        Constraints:
            - The file path must exist in the source tree.
        """
        file_info = self.files.get(file_path)
        if not file_info:
            return { "success": False, "error": "File does not exist" }
        return { "success": True, "data": file_info }

    def get_directory_info(self, directory_path: str) -> dict:
        """
        Retrieve metadata (DirectoryInfo) for the given directory path.

        Args:
            directory_path (str): The path to the directory.

        Returns:
            dict: 
                - If directory exists: { "success": True, "data": DirectoryInfo }
                - If not found: { "success": False, "error": "Directory does not exist" }

        Constraints:
            - directory_path must exist in the project source tree.
        """
        if directory_path not in self.directories:
            return { "success": False, "error": "Directory does not exist" }
        info = self.directories[directory_path]
        return { "success": True, "data": info }

    def list_java_classes_in_package(self, package_name: str) -> dict:
        """
        List all Java classes defined within a specified package.
    
        Args:
            package_name (str): The fully qualified package name (e.g., 'com.example.util').
    
        Returns:
            dict:
                - success (bool)
                - data (List[JavaClassInfo]): List of JavaClassInfo for all matching classes.
    
        Constraints:
            - No error if package is missing; if no class found, return empty list.
            - Query only: does not mutate state.
        """
        matched_classes = [
            class_info
            for class_info in self.java_classes.values()
            if class_info['package_name'] == package_name
        ]
        return {"success": True, "data": matched_classes}

    def list_files_in_directory(self, directory_path: str) -> dict:
        """
        List all files (FileInfo) within the specified directory path.

        Args:
            directory_path (str): The directory whose files are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[FileInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Directory must exist.
            - Only include files whose 'parent_directory' matches 'directory_path'.
        """
        if directory_path not in self.directories:
            return { "success": False, "error": "Directory does not exist" }

        files_in_dir = [
            file_info
            for file_info in self.files.values()
            if file_info['parent_directory'] == directory_path
        ]
        return { "success": True, "data": files_in_dir }

    def get_classes_in_file(self, file_path: str) -> dict:
        """
        Given a `.java` file path, retrieve the fully qualified names of classes it defines.

        Args:
            file_path (str): Path to the .java file.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of fully qualified names of classes in the file (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., file not found or not a .java file
            }

        Constraints:
            - The file must exist.
            - The file extension must be '.java'.
            - All matching JavaClass entries corresponding to file_path are returned.
        """
        file_info = self.files.get(file_path)
        if not file_info:
            return { "success": False, "error": "File not found" }
        if file_info["extension"] != ".java":
            return { "success": False, "error": "Not a .java file" }

        class_fqns = [
            class_info["fully_qualified_name"]
            for class_info in self.java_classes.values()
            if class_info["file_path"] == file_path
        ]

        return { "success": True, "data": class_fqns }

    def get_directory_for_package(self, package_name: str) -> dict:
        """
        Given a Java package name, returns the corresponding directory path in the source tree,
        if it exists.

        Args:
            package_name (str): The fully qualified Java package name (e.g., "com.example.utils").

        Returns:
            dict: {
                "success": True,
                "data": str  # Directory path corresponding to the package
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., not found
            }

        Constraints:
            - The returned directory path must exist in the project directories.
        """
        if not package_name or not isinstance(package_name, str):
            return {"success": False, "error": "Invalid package name"}

        directory_path = self._get_existing_directory_for_package(package_name)
        if directory_path is not None:
            return {"success": True, "data": directory_path}
        return {"success": False, "error": "Directory for package does not exist"}

    def get_package_for_directory(self, directory_path: str) -> dict:
        """
        Infer the Java package name for a given directory path.

        Args:
            directory_path (str): absolute or project-relative directory path

        Returns:
            dict: {
                "success": True,
                "data": str   # The inferred Java package name ("" for default package)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Directory must exist in the project.
            - Package hierarchy maps nested directories to .-separated package names.
        """
        # Check that the directory exists
        if directory_path not in self.directories:
            return {"success": False, "error": "Directory does not exist"}

        normalized_path = self._strip_known_source_root(directory_path)
        if not normalized_path:
            return {"success": True, "data": ""}
        return {"success": True, "data": normalized_path.replace("/", ".").replace("\\", ".")}

    def get_fully_qualified_name_for_file(self, file_path: str) -> dict:
        """
        Given a file path, retrieve the fully qualified Java class name it defines (if any).

        Args:
            file_path (str): The absolute path of the Java source file.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": str}  # fully qualified class name
                - On failure:
                    {"success": False, "error": str}  # Reason for failure

        Constraints:
            - The file must exist in the project.
            - The file must have a '.java' extension.
            - The file must define exactly one Java class (associated_class must be non-empty).
        """
        file_info = self.files.get(file_path)
        if file_info is None:
            return { "success": False, "error": "File does not exist" }

        if file_info.get("extension") != ".java":
            return { "success": False, "error": "Not a Java source file" }

        fqcn = file_info.get("associated_class")
        if not fqcn or fqcn.strip() == "":
            return { "success": False, "error": "No Java class associated with this file" }

        return { "success": True, "data": fqcn }

    def get_file_path_for_class_name(self, fully_qualified_name: str) -> dict:
        """
        Given a fully qualified Java class name, return the file system path for its `.java` file.

        Args:
            fully_qualified_name (str): The full package and class name (e.g., 'com.example.utils.MathUtil').

        Returns:
            dict: {
                "success": True,
                "data": str,  # The file system path to the .java file
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., Java class not found)
            }

        Constraints:
            - Class must exist (present in self.java_classes).
            - Each Java class maps to one file and it must be a .java file.
        """
        class_info = self.java_classes.get(fully_qualified_name)
        if not class_info:
            return { "success": False, "error": "Java class not found" }
        file_path = class_info.get('file_path')
        if not file_path or not file_path.endswith('.java'):
            return { "success": False, "error": "Associated .java file not found or invalid" }
        return { "success": True, "data": file_path }

    def create_java_class_file(self, fully_qualified_name: str) -> dict:
        """
        Create a new Java class, its .java file, and the appropriate directory hierarchy as needed.
    
        Args:
            fully_qualified_name (str): The full Java class name, including package (e.g., com.example.MyClass)
    
        Returns:
            dict: {
                "success": True,
                "message": "Created Java class <class> at <file_path>",
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Must not already exist (as file or class).
            - Creates missing package directories hierarchically.
            - File name must be <ClassName>.java.
            - Directory structure must map to the package name.
        """
        # Input validation
        if not fully_qualified_name or "." not in fully_qualified_name:
            return {"success": False, "error": "Fully qualified name must include package and class name"}
    
        # Parse components
        *package_parts, class_name = fully_qualified_name.strip().split('.')
        if not class_name or not class_name[0].isalpha() or not class_name.isidentifier():
            return {"success": False, "error": "Invalid class name"}
        package_name = ".".join(package_parts)
        if not package_parts or any(not part or not part.isidentifier() for part in package_parts):
            return {"success": False, "error": "Invalid or missing package name"}
    
        package_relative_path = "/".join(package_parts)
        existing_dir_path = self._get_existing_directory_for_package(package_name)
        if existing_dir_path:
            dir_path = existing_dir_path
        else:
            source_prefix = self._infer_source_prefix_for_package(package_name)
            dir_path = self._join_source_prefix(source_prefix, package_relative_path)
        if not dir_path:
            dir_path = "."  # default package, root directory

        # Build file name and file path
        file_name = f"{class_name}.java"
        file_path = f"{dir_path}/{file_name}" if dir_path != "." else file_name
    
        # Check for existing class
        if fully_qualified_name in self.java_classes:
            return {"success": False, "error": f"Java class '{fully_qualified_name}' already exists"}
        # Check for file collision
        if file_path in self.files:
            return {"success": False, "error": f"File '{file_path}' already exists"}

        # Create directory hierarchy as needed
        parent_directory = ""
        dir_parts = self._path_prefixes(dir_path) if dir_path != "." else []
        for idx, built_path in enumerate(dir_parts):
            if built_path not in self.directories:
                # Create parent if necessary
                parent_dir = dir_parts[idx - 1] if idx > 0 else ""
                self.directories[built_path] = {
                    "path": built_path,
                    "parent_directory": parent_dir,
                    "subdirectories": [],
                    "files": []
                }
                # Register in parent's subdirectories
                if parent_dir in self.directories:
                    if built_path not in self.directories[parent_dir]["subdirectories"]:
                        self.directories[parent_dir]["subdirectories"].append(built_path)
            parent_directory = built_path

        # Ensure parent_directory now exists
        if dir_path not in self.directories:
            # (May be root "." for default package)
            self.directories[dir_path] = {
                "path": dir_path,
                "parent_directory": "",
                "subdirectories": [],
                "files": []
            }

        # Create FileInfo
        file_info = {
            "name": file_name,
            "path": file_path,
            "parent_directory": dir_path,
            "extension": ".java",
            "associated_class": fully_qualified_name
        }
        self.files[file_path] = file_info

        # Register file in directory
        if file_name not in self.directories[dir_path]["files"]:
            self.directories[dir_path]["files"].append(file_name)
        
        # Create JavaClassInfo
        java_class_info = {
            "fully_qualified_name": fully_qualified_name,
            "package_name": package_name,
            "class_name": class_name,
            "file_path": file_path,
        }
        self.java_classes[fully_qualified_name] = java_class_info

        return {"success": True, "message": f"Created Java class '{fully_qualified_name}' at '{file_path}'"}

    def rename_java_class(self, old_fully_qualified_name: str, new_class_name: str) -> dict:
        """
        Rename a Java class and update its file name and related mappings accordingly.

        Args:
            old_fully_qualified_name (str): The current fully qualified name (e.g., "com.example.OldName").
            new_class_name (str): The new Java class name as identifier (e.g., "NewName").

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of the renaming operation.
            }
            OR
            {
                "success": False,
                "error": str  # Description of the error.
            }

        Constraints:
            - The class must exist in the project.
            - The new class name must not cause duplicate fully qualified names or file path conflicts.
            - The file must be renamed to match the class, with .java extension.
            - Mappings (`java_classes`, `files`, directory lists) must be updated to remain consistent.
        """
        # 1. Check if the old class exists
        if old_fully_qualified_name not in self.java_classes:
            return { "success": False, "error": "JavaClass not found: " + old_fully_qualified_name }

        old_class_info = self.java_classes[old_fully_qualified_name]
        old_package = old_class_info["package_name"]
        old_class_name = old_class_info["class_name"]
        old_file_path = old_class_info["file_path"]

        # 2. Compose new fully qualified name and new file path
        if old_package:
            new_fully_qualified_name = f"{old_package}.{new_class_name}"
        else:
            new_fully_qualified_name = new_class_name
        if new_fully_qualified_name in self.java_classes:
            return { "success": False, "error": f"JavaClass with name '{new_fully_qualified_name}' already exists." }

        # File renaming logic:
        # Get file info
        if old_file_path not in self.files:
            return { "success": False, "error": "File for this class does not exist." }
        file_info = self.files[old_file_path]
        parent_directory = file_info["parent_directory"]
        new_file_name = f"{new_class_name}.java"
        new_file_path = '/'.join(old_file_path.split('/')[:-1] + [new_file_name])

        # Check if any file with this new name exists in the directory
        if new_file_path in self.files:
            return { "success": False, "error": f"File {new_file_path} already exists." }

        dir_info = self.directories.get(parent_directory)
        if dir_info is None:
            return { "success": False, "error": f"Parent directory {parent_directory} not found." }
        if new_file_name in dir_info["files"]:
            return { "success": False, "error": f"A file named '{new_file_name}' already exists in {parent_directory}." }

        # 3. Update JavaClassInfo
        new_class_info = {
            "fully_qualified_name": new_fully_qualified_name,
            "package_name": old_package,
            "class_name": new_class_name,
            "file_path": new_file_path
        }

        # 4. Update FileInfo
        new_file_info = file_info.copy()
        new_file_info["name"] = new_file_name
        new_file_info["path"] = new_file_path
        new_file_info["associated_class"] = new_fully_qualified_name

        # 5. Update parent's file list
        self._remove_file_from_directory_listing(parent_directory, file_info)
        self._add_file_to_directory_listing(parent_directory, new_file_info)

        # 6. Update internal mappings
        # Remove old entries
        del self.java_classes[old_fully_qualified_name]
        del self.files[old_file_path]

        # Add new entries
        self.java_classes[new_fully_qualified_name] = new_class_info
        self.files[new_file_path] = new_file_info

        return {
            "success": True,
            "message": f"Renamed Java class '{old_fully_qualified_name}' to '{new_fully_qualified_name}' and file '{old_file_path}' to '{new_file_path}'."
        }

    def move_java_class_to_package(self, fully_qualified_name: str, new_package_name: str) -> dict:
        """
        Move an existing Java class to a new package, updating directory, file path, and package name.

        Args:
            fully_qualified_name (str): The fully-qualified name (e.g. com.example.OldClass) of the Java class to move.
            new_package_name (str): The target package name (e.g. com.example.newpkg).

        Returns:
            dict:
                - On success: { "success": True, "message": "Moved class <old> to package <new>." }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - JavaClass must exist.
            - Directory structure must reflect the package structure, and must be created if missing.
            - No existing class with the same (class name, package) tuple should exist in the target package.
            - Update all relevant mappings.
        """
        # 1. Validate that the Java class exists
        jc = self.java_classes.get(fully_qualified_name)
        if not jc:
            return {"success": False, "error": "Java class not found"}
    
        old_package = jc["package_name"]
        class_name = jc["class_name"]
        old_file_path = jc["file_path"]

        if old_package == new_package_name:
            return {"success": False, "error": "Class is already in the specified package"}

        # 2. Build new fully-qualified name and new file path
        new_fqn = new_package_name + "." + class_name if new_package_name else class_name
        file_info = self.files.get(old_file_path)
        if not file_info:
            return {"success": False, "error": "Associated file for Java class not found"}
        # Directory path for new package
        existing_target_dir = self._get_existing_directory_for_package(new_package_name)
        if existing_target_dir:
            new_dir_path = existing_target_dir
        else:
            old_parent_dir = file_info["parent_directory"]
            source_prefix = self._extract_source_prefix(
                old_parent_dir,
                self._package_to_relative_path(old_package),
            )
            new_package_relative_path = self._package_to_relative_path(new_package_name)
            new_dir_path = self._join_source_prefix(source_prefix, new_package_relative_path)
        # Get file name and extension from FileInfo
        file_name = file_info["name"]
        if file_info["extension"] != ".java":
            return {"success": False, "error": "Associated file does not have a .java extension"}

        # New file path
        new_file_path = new_dir_path + '/' + file_name

        # 3. Check for name conflict in the new package
        if new_fqn in self.java_classes:
            return {"success": False, "error": "A class with this name already exists in the target package"}

        # Also, ensure no file with that name exists in the new directory
        if new_file_path in self.files:
            return {"success": False, "error": "A file with this name already exists in the target directory"}

        # 4. Ensure new directory exists (create if missing)
        if new_dir_path not in self.directories:
            # Attempt to create nested directories
            parts = self._path_prefixes(new_dir_path)
            parent_path = ""
            for current_path in parts:
                if current_path not in self.directories:
                    self.directories[current_path] = {
                        "path": current_path,
                        "parent_directory": parent_path if parent_path else "",
                        "subdirectories": [],
                        "files": []
                    }
                    # Add as subdirectory to parent
                    if parent_path and parent_path in self.directories:
                        if current_path not in self.directories[parent_path]["subdirectories"]:
                            self.directories[parent_path]["subdirectories"].append(current_path)
                parent_path = current_path

        # 5. Remove file from old directory's files list; add to new directory's files list
        old_parent_dir = file_info["parent_directory"]
        self._remove_file_from_directory_listing(old_parent_dir, file_info)
        # Add to new
        if new_dir_path in self.directories:
            moved_file_info = file_info.copy()
            moved_file_info["path"] = new_file_path
            moved_file_info["parent_directory"] = new_dir_path
            self._add_file_to_directory_listing(new_dir_path, moved_file_info)

        # 6. Update the file_info entry and files mapping
        new_file_info = file_info.copy()
        new_file_info["path"] = new_file_path
        new_file_info["parent_directory"] = new_dir_path
        new_file_info["associated_class"] = new_fqn
        self.files[new_file_path] = new_file_info
        del self.files[old_file_path]

        # 7. Update the JavaClassInfo and java_classes mapping
        new_jc_info = jc.copy()
        new_jc_info["fully_qualified_name"] = new_fqn
        new_jc_info["package_name"] = new_package_name
        new_jc_info["file_path"] = new_file_path
        self.java_classes[new_fqn] = new_jc_info
        del self.java_classes[fully_qualified_name]

        return {"success": True, "message": f"Moved class {fully_qualified_name} to package {new_package_name}."}

    def delete_java_class_file(self, fully_qualified_class_name: str) -> dict:
        """
        Delete a `.java` file and unregister the associated Java class from the project.

        Args:
            fully_qualified_class_name (str): The fully qualified name of the Java class to delete.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Java class and file successfully deleted"}
                - On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - The class must exist (be registered in self.java_classes).
            - The file must exist, be a `.java` file, and be associated with the given class.
            - Directory file list must be updated to remove file if all else succeeds.
        """
        # Step 1: Check class existence
        class_info = self.java_classes.get(fully_qualified_class_name)
        if not class_info:
            return {"success": False, "error": "Java class not found"}

        file_path = class_info["file_path"]

        # Step 2: Check file existence and association
        file_info = self.files.get(file_path)
        if not file_info:
            return {"success": False, "error": "Associated file not found"}

        if file_info["extension"] != ".java":
            return {"success": False, "error": "Associated file is not a .java file"}

        if file_info["associated_class"] != fully_qualified_class_name:
            return {"success": False, "error": "File is not associated with the specified class"}

        parent_dir = file_info.get("parent_directory")
        if parent_dir not in self.directories:
            return {"success": False, "error": "Parent directory record not found"}

        # Step 3: Remove class registration
        del self.java_classes[fully_qualified_class_name]

        # Step 4: Remove file registration
        del self.files[file_path]

        # Step 5: Remove file from directory's files list
        self._remove_file_from_directory_listing(parent_dir, file_info)

        return {"success": True, "message": "Java class and file successfully deleted"}

    def create_directory(self, path: str) -> dict:
        """
        Create a new package directory in the project source tree.

        Args:
            path (str): The path of the directory to create (e.g., "com/example/utilities").

        Returns:
            dict:
                - On success: { "success": True, "message": "Directory '<path>' created." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Directory names must not clash with existing directories.
            - Parent directory (unless root) must exist.
            - Updates parent directory's subdirectories list accordingly.
        """
        # Sanitize input (remove trailing slashes)
        normalized_path = path.rstrip("/")
        if not normalized_path:
            return {"success": False, "error": "Directory path must not be empty."}
        if normalized_path in self.directories:
            return {"success": False, "error": "Directory already exists."}

        # Determine parent directory
        if "/" in normalized_path:
            parent_directory = normalized_path.rsplit("/", 1)[0]
        else:
            parent_directory = ""  # Root or top-level directory; could also be None or some indicator

        # If not root, parent must exist
        if parent_directory and parent_directory not in self.directories:
            return {"success": False, "error": "Parent directory does not exist."}

        # Add new directory
        self.directories[normalized_path] = {
            "path": normalized_path,
            "parent_directory": parent_directory,
            "subdirectories": [],
            "files": []
        }

        # Update parent's subdirectories list, if applicable
        if parent_directory:
            if normalized_path not in self.directories[parent_directory]["subdirectories"]:
                self.directories[parent_directory]["subdirectories"].append(normalized_path)

        return {"success": True, "message": f"Directory '{normalized_path}' created."}

    def move_file(self, file_path: str, destination_directory_path: str) -> dict:
        """
        Move a file from one directory to another, adjusting all related metadata as necessary.

        Args:
            file_path (str): The full path to the file to move.
            destination_directory_path (str): The full path of the directory to move the file into.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "File moved successfully from <src> to <dst>"}
                On failure:
                    {"success": False, "error": str}

        Constraints:
            - File and destination directory must exist.
            - Destination directory must not already contain a file with the same name.
            - All metadata and class info must be updated accordingly.
        """
        # Check if file exists
        if file_path not in self.files:
            return { "success": False, "error": f"File {file_path} does not exist" }
        file_info = self.files[file_path]

        # Check if destination directory exists
        if destination_directory_path not in self.directories:
            return { "success": False, "error": f"Destination directory {destination_directory_path} does not exist" }

        file_name = file_info["name"]
        dest_dir_info = self.directories[destination_directory_path]
        # Check if the destination directory already has a file with this name
        for dest_file_ref in dest_dir_info["files"]:
            existing_name = dest_file_ref
            if dest_file_ref in self.files:
                existing_name = self.files[dest_file_ref]["name"]
            if existing_name == file_name:
                return { "success": False, "error": f"File with name {file_name} already exists in destination directory" }

        # Get old directory info
        old_dir_path = file_info["parent_directory"]
        old_dir_info = self.directories.get(old_dir_path)
        # Construct new file path
        new_file_path = destination_directory_path.rstrip('/') + '/' + file_name

        # Update file metadata
        updated_file_info = file_info.copy()
        updated_file_info["path"] = new_file_path
        updated_file_info["parent_directory"] = destination_directory_path

        # Update file mappings
        self.files.pop(file_path)
        self.files[new_file_path] = updated_file_info

        # Remove from old directory's file list
        if old_dir_info and file_name in old_dir_info["files"]:
            old_dir_info["files"].remove(file_name)
        # Add to new directory's file list
        dest_dir_info["files"].append(file_name)

        # Update JavaClass file_path if necessary
        associated_class_name = updated_file_info.get("associated_class")
        if associated_class_name and associated_class_name in self.java_classes:
            class_info = self.java_classes.pop(associated_class_name)
            new_package_name = destination_directory_path.replace("/", ".").replace("\\", ".")
            new_fully_qualified_name = (
                f"{new_package_name}.{class_info['class_name']}"
                if new_package_name else class_info["class_name"]
            )
            class_info["file_path"] = new_file_path
            class_info["package_name"] = new_package_name
            class_info["fully_qualified_name"] = new_fully_qualified_name
            updated_file_info["associated_class"] = new_fully_qualified_name
            self.files[new_file_path] = updated_file_info
            self.java_classes[new_fully_qualified_name] = class_info

        message = f"File moved successfully from {file_path} to {new_file_path}"
        return { "success": True, "message": message }

    def rename_directory(self, old_path: str, new_path: str) -> dict:
        """
        Rename a directory from old_path to new_path, updating all parent and subdirectory
        references, file paths, and affected Java class file paths accordingly.

        Args:
            old_path (str): Current path of the directory to rename.
            new_path (str): New path for the directory (should not exist).

        Returns:
            dict: 
                - On success: { "success": True, "message": "Directory renamed from <old_path> to <new_path>" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - old_path must exist in directories.
            - new_path must not exist in directories.
            - All subdirectories, files, Java classes under old_path must have their paths updated accordingly.
        """
        # Check existence and collisions
        if old_path not in self.directories:
            return { "success": False, "error": f"Directory '{old_path}' does not exist." }
        if new_path in self.directories:
            return { "success": False, "error": f"Directory '{new_path}' already exists." }
    
        # Prepare to update all affected directories and their files/classes
        # Step 1: Identify all directories to be updated (the whole subtree)
        affected_dirs = {}
        for dir_path, info in self.directories.items():
            if dir_path == old_path or dir_path.startswith(old_path + '/'):
                affected_dirs[dir_path] = info

        # Step 2: Calculate mapping from old to new directory paths
        dir_rename_map = {
            dir_path: dir_path.replace(old_path, new_path, 1)
            for dir_path in affected_dirs
        }

        # Step 3: Update directory structures
        # Remove old paths from self.directories and insert under new keys
        for old_dir_path, dir_info in list(affected_dirs.items()):
            new_dir_path = dir_rename_map[old_dir_path]
            # Update path and parent_directory in dir_info
            updated_info = dir_info.copy()
            updated_info['path'] = new_dir_path
            # If parent_directory is within the subtree, update it too
            parent_dir = updated_info['parent_directory']
            if parent_dir == old_path or parent_dir.startswith(old_path + '/'):
                updated_info['parent_directory'] = parent_dir.replace(old_path, new_path, 1)
            elif parent_dir == old_path:  # Direct parent
                updated_info['parent_directory'] = new_path
            # Rewrite subdirectories as well
            updated_subdirs = []
            for sub_path in updated_info['subdirectories']:
                if sub_path == old_path or sub_path.startswith(old_path + '/'):
                    updated_subdirs.append(sub_path.replace(old_path, new_path, 1))
                else:
                    updated_subdirs.append(sub_path)
            updated_info['subdirectories'] = updated_subdirs

            # The files list will be updated later, after file paths have changed
            self.directories[new_dir_path] = updated_info
            del self.directories[old_dir_path]

        # Step 4: Update parent directory's subdirectory reference
        old_parent = dir_info['parent_directory']
        if old_parent and old_parent in self.directories:
            parent = self.directories[old_parent]
            updated_subdirs = [
                new_path if s == old_path else s for s in parent['subdirectories']
            ]
            parent['subdirectories'] = updated_subdirs
            self.directories[old_parent] = parent

        # Step 5: Update file paths and their metadata
        affected_files = {}
        for file_path, file_info in self.files.items():
            if file_path.startswith(old_path + '/'):
                affected_files[file_path] = file_info

        file_rename_map = {
            file_path: file_path.replace(old_path, new_path, 1)
            for file_path in affected_files
        }

        for old_file_path, file_info in list(affected_files.items()):
            new_file_path = file_rename_map[old_file_path]
            updated_file_info = file_info.copy()
            updated_file_info['path'] = new_file_path
            # Update parent_directory if inside the subtree
            parent_dir = updated_file_info['parent_directory']
            if parent_dir == old_path or parent_dir.startswith(old_path + '/'):
                updated_file_info['parent_directory'] = parent_dir.replace(old_path, new_path, 1)
            elif parent_dir == old_path:
                updated_file_info['parent_directory'] = new_path
            self.files[new_file_path] = updated_file_info
            del self.files[old_file_path]

        # Step 6: Update files lists in the (now updated) directory infos
        for dir_info in self.directories.values():
            updated_files = []
            for file_path in dir_info['files']:
                if file_path in file_rename_map:
                    updated_files.append(file_rename_map[file_path])
                else:
                    updated_files.append(file_path)
            dir_info['files'] = updated_files

        # Step 7: Update JavaClass entries (file_path, and if needed package_name/fully_qualified_name)
        affected_classes = {}
        for fqcn, class_info in self.java_classes.items():
            if class_info['file_path'].startswith(old_path + '/'):
                affected_classes[fqcn] = class_info

        new_java_classes = {}
        fqcn_rename_map = {}
        for fqcn, class_info in affected_classes.items():
            new_file_path = class_info['file_path'].replace(old_path, new_path, 1)
            # Package name may change if it's path-derived, so update package_name if necessary
            new_package_name = class_info['package_name']
            old_package_path = old_path.strip('/').replace('/', '.')
            new_package_path = new_path.strip('/').replace('/', '.')
            if class_info['package_name'] and old_package_path and class_info['package_name'].startswith(old_package_path):
                new_package_name = class_info['package_name'].replace(old_package_path, new_package_path, 1)
            # Update fully qualified name
            old_fqcn_prefix = old_package_path + '.' if old_package_path else ''
            new_fqcn_prefix = new_package_path + '.' if new_package_path else ''
            new_fqcn = fqcn
            if fqcn.startswith(old_fqcn_prefix):
                new_fqcn = fqcn.replace(old_fqcn_prefix, new_fqcn_prefix, 1)
            updated_class_info = class_info.copy()
            updated_class_info['file_path'] = new_file_path
            updated_class_info['package_name'] = new_package_name
            updated_class_info['fully_qualified_name'] = new_fqcn
            # Remove old mapping and add new
            new_java_classes[new_fqcn] = updated_class_info
            fqcn_rename_map[fqcn] = new_fqcn

        for fqcn in affected_classes:
            del self.java_classes[fqcn]
        self.java_classes.update(new_java_classes)

        for file_info in self.files.values():
            associated_class = file_info.get("associated_class")
            if associated_class in fqcn_rename_map:
                file_info["associated_class"] = fqcn_rename_map[associated_class]

        return { "success": True, "message": f"Directory renamed from '{old_path}' to '{new_path}'" }

    def delete_directory(self, directory_path: str) -> dict:
        """
        Remove an empty directory from the Java project source tree.
    
        Args:
            directory_path (str): The path to the directory to delete.

        Returns:
            dict: {
                "success": True,
                "message": f"Directory {directory_path} deleted."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Directory must exist.
            - Directory must have no files and no subdirectories (empty).
            - Directory must be removed from its parent's subdirectories list.
            - No orphan FileInfo or JavaClassInfo will be left because all files must be removed prior.
        """
        dir_info = self.directories.get(directory_path)
        if not dir_info:
            return {"success": False, "error": "Directory does not exist."}

        self._drop_stale_directory_file_refs(directory_path)

        if dir_info["files"]:
            return {"success": False, "error": "Directory is not empty: contains files."}

        if dir_info["subdirectories"]:
            return {"success": False, "error": "Directory is not empty: contains subdirectories."}

        parent_path = dir_info["parent_directory"]
        # Remove from parent's subdirectories, if parent exists
        if parent_path in self.directories:
            parent_dir = self.directories[parent_path]
            if directory_path in parent_dir["subdirectories"]:
                parent_dir["subdirectories"].remove(directory_path)

        # Delete the directory itself
        del self.directories[directory_path]

        return {"success": True, "message": f"Directory {directory_path} deleted."}


class JavaProjectSourceTree(BaseEnv):
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

    def get_java_class_info(self, **kwargs):
        return self._call_inner_tool('get_java_class_info', kwargs)

    def get_file_info(self, **kwargs):
        return self._call_inner_tool('get_file_info', kwargs)

    def get_directory_info(self, **kwargs):
        return self._call_inner_tool('get_directory_info', kwargs)

    def list_java_classes_in_package(self, **kwargs):
        return self._call_inner_tool('list_java_classes_in_package', kwargs)

    def list_files_in_directory(self, **kwargs):
        return self._call_inner_tool('list_files_in_directory', kwargs)

    def get_classes_in_file(self, **kwargs):
        return self._call_inner_tool('get_classes_in_file', kwargs)

    def get_directory_for_package(self, **kwargs):
        return self._call_inner_tool('get_directory_for_package', kwargs)

    def get_package_for_directory(self, **kwargs):
        return self._call_inner_tool('get_package_for_directory', kwargs)

    def get_fully_qualified_name_for_file(self, **kwargs):
        return self._call_inner_tool('get_fully_qualified_name_for_file', kwargs)

    def get_file_path_for_class_name(self, **kwargs):
        return self._call_inner_tool('get_file_path_for_class_name', kwargs)

    def create_java_class_file(self, **kwargs):
        return self._call_inner_tool('create_java_class_file', kwargs)

    def rename_java_class(self, **kwargs):
        return self._call_inner_tool('rename_java_class', kwargs)

    def move_java_class_to_package(self, **kwargs):
        return self._call_inner_tool('move_java_class_to_package', kwargs)

    def delete_java_class_file(self, **kwargs):
        return self._call_inner_tool('delete_java_class_file', kwargs)

    def create_directory(self, **kwargs):
        return self._call_inner_tool('create_directory', kwargs)

    def move_file(self, **kwargs):
        return self._call_inner_tool('move_file', kwargs)

    def rename_directory(self, **kwargs):
        return self._call_inner_tool('rename_directory', kwargs)

    def delete_directory(self, **kwargs):
        return self._call_inner_tool('delete_directory', kwargs)
