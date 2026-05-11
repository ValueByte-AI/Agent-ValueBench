# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from datetime import datetime
from typing import Dict
import time



class CodeFileInfo(TypedDict):
    file_id: str
    file_name: str
    file_type: str
    content: str
    version: str
    timestamp: str

class ComparisonSessionInfo(TypedDict):
    session_id: str
    file1_id: str
    file2_id: str
    comparison_time: str
    diff_result: str  # diff_id

class DiffResultInfo(TypedDict):
    diff_id: str
    session_id: str
    diff_lines: List[str]  # list of diff_line ids
    summary: str

class DiffLineInfo(TypedDict):
    diff_id: str
    line_number: int
    change_type: str
    original_text: str
    changed_text: str

class ReportInfo(TypedDict):
    report_id: str
    session_id: str
    format: str
    file_path: str
    creation_time: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Code Files: {file_id: CodeFileInfo}
        self.code_files: Dict[str, CodeFileInfo] = {}
        
        # Comparison Sessions: {session_id: ComparisonSessionInfo}
        self.comparison_sessions: Dict[str, ComparisonSessionInfo] = {}
        
        # Diff Results: {diff_id: DiffResultInfo}
        self.diff_results: Dict[str, DiffResultInfo] = {}
        
        # Diff Lines: {diff_line_id: DiffLineInfo}
        self.diff_lines: Dict[str, DiffLineInfo] = {}
        
        # Reports: {report_id: ReportInfo}
        self.reports: Dict[str, ReportInfo] = {}
        
        # Constraints:
        # - Files being compared must be accessible and their specified versions exist.
        # - Diff results must reference valid comparison sessions and code file snapshots.
        # - Reports must be generated in one of the supported formats and saved to a valid/authorized file path.
        # - Reports reference a single comparison session and its associated diff result.

    def get_code_file_by_id(self, file_id: str) -> dict:
        """
        Retrieve details (metadata and content) for a specific code file given its file_id.

        Args:
            file_id (str): Unique identifier of the code file.

        Returns:
            dict: {
                "success": True,
                "data": CodeFileInfo  # All metadata and content for the file,
            }
            OR
            {
                "success": False,
                "error": str  # Explanation if file not found
            }

        Constraints:
            - The file_id must exist in the code_files dictionary.
        """
        file_info = self.code_files.get(file_id)
        if file_info is None:
            return { "success": False, "error": "Code file with the given ID does not exist" }
        return { "success": True, "data": file_info }

    def get_code_files_by_name_and_version(self, file_name: str, version: str) -> dict:
        """
        Retrieve all code file records matching the given file_name and version.

        Args:
            file_name (str): Name of the code file to search.
            version (str): Version string to search.

        Returns:
            dict: {
                "success": True,
                "data": List[CodeFileInfo],  # List of file records matching criteria, empty if none found.
            }

        Constraints:
            - No error is returned if no match; an empty list is returned instead.
            - Only exact matches on both file_name and version are considered.
        """
        matches = [
            file_info
            for file_info in self.code_files.values()
            if file_info["file_name"] == file_name and file_info["version"] == version
        ]
        return { "success": True, "data": matches }

    def list_code_files(self) -> dict:
        """
        List all tracked code files and their metadata.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[CodeFileInfo]  # all code files' metadata (empty list if none)
                }

        This operation does not take parameters and always succeeds, returning all code files tracked by the system.
        """
        files = list(self.code_files.values())
        return { "success": True, "data": files }

    def check_code_file_version_exists(
        self, 
        version: str, 
        file_id: str = None, 
        file_name: str = None
    ) -> dict:
        """
        Verify that a code file with a specific file_id (or file_name) and version exists.

        Args:
            version (str): The version string to search for (required)
            file_id (str, optional): The unique file ID (preferred)
            file_name (str, optional): The file's name (if file_id not provided)

        Returns:
            dict: {
                "success": True,
                "exists": bool  # Whether at least one matching code file exists
            }
            or
            {
                "success": False,
                "error": str  # Error message if input is insufficient/invalid
            }

        Constraints:
            - Either file_id or file_name must be provided (prefer file_id if both).
            - Version must be provided.
        """
        if not version:
            return { "success": False, "error": "Version must be specified." }
        if not file_id and not file_name:
            return { "success": False, "error": "Either file_id or file_name must be provided." }

        if file_id:
            # file_id is unique
            file_info = self.code_files.get(file_id)
            if file_info and file_info.get("version") == version:
                return { "success": True, "exists": True }
            else:
                return { "success": True, "exists": False }

        # file_id not provided, search by file_name (could be multiple versions)
        for file in self.code_files.values():
            if file.get("file_name") == file_name and file.get("version") == version:
                return { "success": True, "exists": True }

        return { "success": True, "exists": False }

    def get_comparison_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve metadata and details for a specific comparison session.

        Args:
            session_id (str): The ID of the comparison session to retrieve.

        Returns:
            dict: 
                - If found: {"success": True, "data": ComparisonSessionInfo}
                - If not found: {"success": False, "error": "Comparison session not found"}
    
        Constraints:
            - The session_id must exist in the system.
        """
        session = self.comparison_sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Comparison session not found"}
        return {"success": True, "data": session}

    def list_comparison_sessions_for_file(self, file_id: str) -> dict:
        """
        List all comparison sessions involving the specified file_id either as file1 or file2.

        Args:
            file_id (str): The id of the code file.

        Returns:
            dict: {
                "success": True,
                "data": List[ComparisonSessionInfo]  # May be empty if no sessions found
            }
            or
            {
                "success": False,
                "error": str  # Reason for the error (e.g., non-existent file_id)
            }

        Constraints:
            - The specified file_id must exist in the environment.
        """
        if file_id not in self.code_files:
            return {"success": False, "error": "File id does not exist"}

        sessions = [
            session_info
            for session_info in self.comparison_sessions.values()
            if session_info["file1_id"] == file_id or session_info["file2_id"] == file_id
        ]

        return {"success": True, "data": sessions}

    def get_diff_result_by_session_id(self, session_id: str) -> dict:
        """
        Retrieve the diff result associated with the given comparison session.
    
        Args:
            session_id (str): The unique identifier for the comparison session.
    
        Returns:
            dict: 
                On success:
                  {
                    "success": True,
                    "data": DiffResultInfo  # DiffResultInfo for the session
                  }
                On failure:
                  {
                    "success": False,
                    "error": str  # Reason for failure
                  }
    
        Constraints:
            - session_id must refer to an existing comparison session.
            - The referenced diff_result (diff_id) must exist.
        """
        # 1. Check comparison session existence
        session = self.comparison_sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Comparison session does not exist"}
    
        # 2. Get the diff_id from the session
        diff_id = session.get("diff_result")
        if not diff_id:
            return {"success": False, "error": "No diff result associated with this session"}

        # 3. Fetch the DiffResultInfo
        diff_result = self.diff_results.get(diff_id)
        if diff_result is None:
            return {"success": False, "error": "Diff result not found for this session"}
    
        return {"success": True, "data": diff_result}

    def get_diff_result_by_id(self, diff_id: str) -> dict:
        """
        Retrieve details of a specific diff result, including summary and all line changes.

        Args:
            diff_id (str): The unique identifier for the diff result.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "diff_id": str,
                    "session_id": str,
                    "summary": str,
                    "diff_lines": List[DiffLineInfo],  # Detailed line changes
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., diff result not found
            }
        """
        if diff_id not in self.diff_results:
            return {"success": False, "error": "Diff result not found"}
    
        diff_result = self.diff_results[diff_id]

        # Fetch the DiffLineInfo for each diff_line id
        diff_line_infos = [
            self.diff_lines[line_id]
            for line_id in diff_result.get("diff_lines", [])
            if line_id in self.diff_lines
        ]

        data = {
            "diff_id": diff_result["diff_id"],
            "session_id": diff_result["session_id"],
            "summary": diff_result["summary"],
            "diff_lines": diff_line_infos,
        }
        return {"success": True, "data": data}

    def list_diff_lines_for_diff(self, diff_id: str) -> dict:
        """
        Retrieves all line-level changes (DiffLineInfo) for the specified diff_id.

        Args:
            diff_id (str): The unique identifier of the diff result.

        Returns:
            dict: {
                "success": True,
                "data": List[DiffLineInfo], # may be empty if no lines
            }
            or
            {
                "success": False,
                "error": str # Reason, e.g. diff id doesn't exist
            }

        Constraints:
            - The given diff_id must exist in the diff results.
        """
        if diff_id not in self.diff_results:
            return { "success": False, "error": "Diff result does not exist" }

        diff_result = self.diff_results[diff_id]
        diff_line_ids = diff_result.get("diff_lines", [])
        result = []
        for line_id in diff_line_ids:
            if line_id in self.diff_lines:
                result.append(self.diff_lines[line_id])
            # else (unlikely), ignore silently as data may be corrupted

        return { "success": True, "data": result }

    def get_report_by_id(self, report_id: str) -> dict:
        """
        Retrieve details and metadata for a previously generated report.

        Args:
            report_id (str): Unique identifier for the report.

        Returns:
            dict:
              - On success: {"success": True, "data": ReportInfo}
              - On failure: {"success": False, "error": "Report not found"}

        Constraints:
            - The specified report_id must exist in the reports registry.
        """
        report = self.reports.get(report_id)
        if report is None:
            return { "success": False, "error": "Report not found" }
        return { "success": True, "data": report }

    def list_reports_for_session(self, session_id: str) -> dict:
        """
        List all reports generated for a specified comparison session.

        Args:
            session_id (str): The identifier for the comparison session whose reports are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ReportInfo]  # All reports for this session (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., session_id not found)
            }
    
        Constraints:
            - The comparison session must exist.
        """
        if session_id not in self.comparison_sessions:
            return { "success": False, "error": "Comparison session does not exist" }

        reports_for_session = [
            report for report in self.reports.values()
            if report["session_id"] == session_id
        ]

        return { "success": True, "data": reports_for_session }

    def create_comparison_session(self, file1_id: str, file1_version: str, file2_id: str, file2_version: str) -> dict:
        """
        Create a new comparison session between two specified code files (by file_id and version).
    
        Args:
            file1_id (str): The ID of the first code file.
            file1_version (str): The version of the first code file.
            file2_id (str): The ID of the second code file.
            file2_version (str): The version of the second code file.

        Returns:
            dict: 
                Success: 
                    {"success": True, "session_id": str, "message": "Comparison session created."}
                Failure (file not found or version mismatch): 
                    {"success": False, "error": "..."}
    
        Constraints:
            - Both files (file_id + version) must exist in code_files.
            - Session is created with a unique session_id and empty diff_result field.
        """

        # Helper to find the given file id+version
        def find_file_id_and_version(file_id: str, version: str):
            file_info = self.code_files.get(file_id)
            if file_info and file_info.get("version") == version:
                return True
            # In case code_files holds multiple versions under different file_ids (if versioning means new file_id, not reused)
            # Otherwise, need to scan for matching (file_name, version)
            return False

        if not find_file_id_and_version(file1_id, file1_version):
            return { "success": False, "error": f"File with id '{file1_id}' and version '{file1_version}' not found." }
        if not find_file_id_and_version(file2_id, file2_version):
            return { "success": False, "error": f"File with id '{file2_id}' and version '{file2_version}' not found." }

        session_id = str(uuid.uuid4())
        comparison_time = datetime.utcnow().isoformat() + "Z"
        session_info = {
            "session_id": session_id,
            "file1_id": file1_id,
            "file2_id": file2_id,
            "comparison_time": comparison_time,
            "diff_result": ""  # Initially empty
        }
        self.comparison_sessions[session_id] = session_info
        return {"success": True, "session_id": session_id, "message": "Comparison session created."}


    def generate_diff_result(self, session_id: str) -> dict:
        """
        Compute and store the line-by-line differences for a given comparison session,
        and produce a DiffResult entry and corresponding DiffLine entries.

        Args:
            session_id (str): The identifier of the comparison session.

        Returns:
            dict: {
                "success": True,
                "message": str,      # Description of the result.
                "diff_id": str,      # The generated diff result's identifier.
            }
            or
            {
                "success": False,
                "error": str         # Description of what went wrong.
            }

        Constraints:
            - The comparison session must exist.
            - The session must reference valid and existing code files.
            - Only one diff result per session is allowed.
        """
        # 1. Verify session exists
        session = self.comparison_sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Comparison session does not exist"}

        file1_id = session.get("file1_id")
        file2_id = session.get("file2_id")

        # 2. Verify referenced code files exist
        file1 = self.code_files.get(file1_id)
        file2 = self.code_files.get(file2_id)
        if (not file1) or (not file2):
            return {"success": False, "error": "One or both code files in session do not exist"}

        # 3. Ensure no existing diff result for this session
        for diff in self.diff_results.values():
            if diff["session_id"] == session_id:
                return {"success": False, "error": "Diff result for this session already exists"}

        # 4. Compute diff (line-by-line)
        content1 = file1["content"].splitlines()
        content2 = file2["content"].splitlines()
        max_lines = max(len(content1), len(content2))

        diff_line_ids = []
        changes_summary = {
            "added": 0, "removed": 0, "modified": 0
        }

        for idx in range(max_lines):
            orig_line = content1[idx] if idx < len(content1) else None
            new_line  = content2[idx] if idx < len(content2) else None

            if orig_line is None:
                # Line added in file2
                diff_line_id = str(uuid.uuid4())
                self.diff_lines[diff_line_id] = {
                    "diff_id": None,  # to be set below
                    "line_number": idx + 1,
                    "change_type": "added",
                    "original_text": "",
                    "changed_text": new_line,
                }
                diff_line_ids.append(diff_line_id)
                changes_summary["added"] += 1

            elif new_line is None:
                # Line removed from file1
                diff_line_id = str(uuid.uuid4())
                self.diff_lines[diff_line_id] = {
                    "diff_id": None,  # to be set below
                    "line_number": idx + 1,
                    "change_type": "removed",
                    "original_text": orig_line,
                    "changed_text": "",
                }
                diff_line_ids.append(diff_line_id)
                changes_summary["removed"] += 1

            elif orig_line != new_line:
                # Line modified
                diff_line_id = str(uuid.uuid4())
                self.diff_lines[diff_line_id] = {
                    "diff_id": None,  # to be set below
                    "line_number": idx + 1,
                    "change_type": "modified",
                    "original_text": orig_line,
                    "changed_text": new_line,
                }
                diff_line_ids.append(diff_line_id)
                changes_summary["modified"] += 1
            # else: lines are the same, no diff record

        # 5. Create DiffResultInfo entry
        diff_id = str(uuid.uuid4())
        summary = (
            f"Added {changes_summary['added']} lines, "
            f"removed {changes_summary['removed']} lines, "
            f"modified {changes_summary['modified']} lines."
        )
        self.diff_results[diff_id] = {
            "diff_id": diff_id,
            "session_id": session_id,
            "diff_lines": diff_line_ids,
            "summary": summary
        }

        # 6. Assign diff_id to all related diff_lines
        for diff_line_id in diff_line_ids:
            self.diff_lines[diff_line_id]["diff_id"] = diff_id

        # 7. Update session with diff_result (diff_id)
        self.comparison_sessions[session_id]["diff_result"] = diff_id

        return {
            "success": True,
            "message": "Diff result generated",
            "diff_id": diff_id
        }


    def add_diff_line(
        self,
        diff_id: str,
        line_number: int,
        change_type: str,
        original_text: str,
        changed_text: str
    ) -> dict:
        """
        Add a detailed diff line to an existing diff result.

        Args:
            diff_id (str): The ID of the diff result this line is part of.
            line_number (int): The line number in question (must be >= 1).
            change_type (str): The type of change ('added', 'removed', 'modified', etc.).
            original_text (str): Text from the original file.
            changed_text (str): Text from the changed file.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Added diff line to diff result <diff_id>." }
              - On failure: { "success": False, "error": "reason" }

        Constraints:
            - diff_id must reference an existing diff result.
            - line_number must be positive integer.
            - diff_line_id is generated unique.
            - New diff line is added to both diff_lines collection and the referenced diff result's diff_lines list.
        """
        # Validate diff result exists
        if diff_id not in self.diff_results:
            return { "success": False, "error": "Diff result not found" }

        # Validate line_number
        if not isinstance(line_number, int) or line_number < 1:
            return { "success": False, "error": "line_number must be a positive integer" }
    
        # Basic validation for other fields
        if not isinstance(change_type, str) or not isinstance(original_text, str) or not isinstance(changed_text, str):
            return { "success": False, "error": "Invalid argument types for change_type/original_text/changed_text" }

        # Generate a unique diff_line_id (UUID)
        diff_line_id = str(uuid.uuid4())

        # Compose the DiffLineInfo
        diff_line_info = {
            "diff_id": diff_id,
            "line_number": line_number,
            "change_type": change_type,
            "original_text": original_text,
            "changed_text": changed_text
        }

        # Add to diff_lines collection
        self.diff_lines[diff_line_id] = diff_line_info

        # Attach to diff_lines list of the target diff result
        self.diff_results[diff_id]["diff_lines"].append(diff_line_id)

        return { "success": True, "message": f"Added diff line to diff result {diff_id}." }

    def generate_report(
        self,
        session_id: str,
        diff_id: str,
        format: str,
        file_path: str,
    ) -> dict:
        """
        Generate a human-readable report for a given comparison session and diff result,
        storing report metadata.

        Args:
            session_id (str): The ID of the comparison session to report on.
            diff_id (str): The ID of the diff result to use for the report.
            format (str): The output report format (e.g., "PDF", "HTML").
            file_path (str): Where to store the generated report.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Report generated and stored at <file_path>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - session_id and diff_id must exist.
            - diff_id must reference the specified session.
            - format must be supported.
            - file_path must be unique (no existing report at this path) and non-empty.
        """

        # Supported formats
        supported_formats = {"PDF", "HTML", "Markdown"}

        if session_id not in self.comparison_sessions:
            return {"success": False, "error": "Comparison session does not exist"}
        if diff_id not in self.diff_results:
            return {"success": False, "error": "Diff result does not exist"}

        diff_result = self.diff_results[diff_id]
        if diff_result["session_id"] != session_id:
            return {"success": False, "error": "Diff result does not match the comparison session"}

        if not format or format.upper() not in supported_formats:
            return {"success": False, "error": f"Format '{format}' not supported"}

        if not file_path or not isinstance(file_path, str) or file_path.strip() == "":
            return {"success": False, "error": "A valid non-empty file_path must be provided"}

        # Check uniqueness of file_path
        for report in self.reports.values():
            if report["file_path"] == file_path:
                return {"success": False, "error": "A report at this file_path already exists"}

        # Generate a unique report_id
        report_id = str(uuid.uuid4())
        now = str(time.time())

        report_info = {
            "report_id": report_id,
            "session_id": session_id,
            "format": format.upper(),
            "file_path": file_path,
            "creation_time": now,
        }
        self.reports[report_id] = report_info

        return {
            "success": True,
            "message": f"Report generated and stored at {file_path}"
        }

    def delete_report(self, report_id: str) -> dict:
        """
        Permanently remove a previously generated report from the system.

        Args:
            report_id (str): The unique ID of the report to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "Report deleted successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The report ID must exist in the system.
        """
        if report_id not in self.reports:
            return { "success": False, "error": "Report not found." }
        del self.reports[report_id]
        return { "success": True, "message": "Report deleted successfully." }

    def update_report_file_path(self, report_id: str, new_file_path: str) -> dict:
        """
        Change the file path where a report is saved.

        Args:
            report_id (str): The unique identifier for the report to update.
            new_file_path (str): The new file path to assign to this report.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Report file path updated successfully."}
                - On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - The report must exist.
            - The new file path must be a non-empty string.
            - (Recommended) The file extension should match the report format.
            - (Recommended) The file path should not already be used by another report.
        """
        if report_id not in self.reports:
            return {"success": False, "error": "Report not found."}
        if not isinstance(new_file_path, str) or not new_file_path.strip():
            return {"success": False, "error": "New file path is empty or invalid."}
    
        # Optional: Check collision with other reports' file_path
        for rid, rep in self.reports.items():
            if rid != report_id and rep["file_path"] == new_file_path:
                return {"success": False, "error": "Another report already uses this file path."}
    
        # Optional: Enforce format/extension consistency
        report = self.reports[report_id]
        report_format = report["format"].lower()
        file_ext = new_file_path.split('.')[-1].lower() if '.' in new_file_path else ""
        expected_ext = {
            "pdf": "pdf",
            "txt": "txt",
            "html": "html",
            "md": "md"
        }.get(report_format)
        if expected_ext and file_ext and file_ext != expected_ext:
            return {
                "success": False,
                "error": f"The file extension '{file_ext}' does not match the report format '{report_format}'."
            }
        # Update file path
        self.reports[report_id]["file_path"] = new_file_path.strip()
        return {"success": True, "message": "Report file path updated successfully."}

    def remove_comparison_session(self, session_id: str) -> dict:
        """
        Delete a comparison session and all associated diff results, diff lines, and reports.

        Args:
            session_id (str): The ID of the comparison session to remove.

        Returns:
            dict:
                success (bool): True if operation succeeded, False otherwise.
                message (str): Success message on completion.
                error (str, optional): Present if operation fails due to invalid session_id.
    
        Constraints:
            - The session_id must exist.
            - Cascade deletes: all diff results, associated diff lines, and reports referencing this session must be removed as well.
        """
        # 1. Check if session exists
        if session_id not in self.comparison_sessions:
            return {"success": False, "error": "Comparison session does not exist."}
    
        # 2. Find and delete diff results + related diff lines
        diff_result_ids = [
            diff_id for diff_id, diff_result in self.diff_results.items()
            if diff_result["session_id"] == session_id
        ]
        for diff_id in diff_result_ids:
            # Remove diff lines associated with this diff result
            diff_line_ids = [
                diff_line_id for diff_line_id, diff_line in self.diff_lines.items()
                if diff_line["diff_id"] == diff_id
            ]
            for diff_line_id in diff_line_ids:
                del self.diff_lines[diff_line_id]
            del self.diff_results[diff_id]
    
        # 3. Find and delete reports for this session
        report_ids = [
            report_id for report_id, report in self.reports.items()
            if report["session_id"] == session_id
        ]
        for report_id in report_ids:
            del self.reports[report_id]
    
        # 4. Remove the comparison session record itself
        del self.comparison_sessions[session_id]

        return {
            "success": True,
            "message": f"Comparison session '{session_id}' and all associated diff results, diff lines, and reports have been removed."
        }

    def add_code_file_version(
        self,
        file_id: str,
        file_name: str,
        file_type: str,
        content: str,
        version: str,
        timestamp: str
    ) -> dict:
        """
        Adds a new code file snapshot/version to the system.
    
        Args:
            file_id (str): Unique identifier for this file version/snapshot.
            file_name (str): Logical name of the code file.
            file_type (str): Type/extension (e.g., 'py', 'cpp').
            content (str): File contents at this version.
            version (str): Version label/identifier.
            timestamp (str): Creation timestamp for the snapshot.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Code file version added.", "file_id": <file_id> }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - file_id must be unique (must not already exist in system).
            - All fields are required.
        """
        # Check for required fields
        required_params = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "content": content,
            "version": version,
            "timestamp": timestamp
        }
        for k, v in required_params.items():
            if v is None or (isinstance(v, str) and v.strip() == ""):
                return {"success": False, "error": f"Missing or empty required parameter: {k}"}
    
        # file_id uniqueness constraint
        if file_id in self.code_files:
            return {"success": False, "error": "File ID already exists."}
    
        # Add the new file version
        new_file_info = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "content": content,
            "version": version,
            "timestamp": timestamp
        }
        self.code_files[file_id] = new_file_info

        return {
            "success": True,
            "message": "Code file version added.",
            "file_id": file_id
        }


class SourceCodeComparisonTool(BaseEnv):
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

    def get_code_file_by_id(self, **kwargs):
        return self._call_inner_tool('get_code_file_by_id', kwargs)

    def get_code_files_by_name_and_version(self, **kwargs):
        return self._call_inner_tool('get_code_files_by_name_and_version', kwargs)

    def list_code_files(self, **kwargs):
        return self._call_inner_tool('list_code_files', kwargs)

    def check_code_file_version_exists(self, **kwargs):
        return self._call_inner_tool('check_code_file_version_exists', kwargs)

    def get_comparison_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_comparison_session_by_id', kwargs)

    def list_comparison_sessions_for_file(self, **kwargs):
        return self._call_inner_tool('list_comparison_sessions_for_file', kwargs)

    def get_diff_result_by_session_id(self, **kwargs):
        return self._call_inner_tool('get_diff_result_by_session_id', kwargs)

    def get_diff_result_by_id(self, **kwargs):
        return self._call_inner_tool('get_diff_result_by_id', kwargs)

    def list_diff_lines_for_diff(self, **kwargs):
        return self._call_inner_tool('list_diff_lines_for_diff', kwargs)

    def get_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_report_by_id', kwargs)

    def list_reports_for_session(self, **kwargs):
        return self._call_inner_tool('list_reports_for_session', kwargs)

    def create_comparison_session(self, **kwargs):
        return self._call_inner_tool('create_comparison_session', kwargs)

    def generate_diff_result(self, **kwargs):
        return self._call_inner_tool('generate_diff_result', kwargs)

    def add_diff_line(self, **kwargs):
        return self._call_inner_tool('add_diff_line', kwargs)

    def generate_report(self, **kwargs):
        return self._call_inner_tool('generate_report', kwargs)

    def delete_report(self, **kwargs):
        return self._call_inner_tool('delete_report', kwargs)

    def update_report_file_path(self, **kwargs):
        return self._call_inner_tool('update_report_file_path', kwargs)

    def remove_comparison_session(self, **kwargs):
        return self._call_inner_tool('remove_comparison_session', kwargs)

    def add_code_file_version(self, **kwargs):
        return self._call_inner_tool('add_code_file_version', kwargs)

