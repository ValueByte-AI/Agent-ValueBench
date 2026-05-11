# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ProjectInfo(TypedDict):
    project_id: str
    name: str
    description: str
    status: str  # 'sta' assumed as 'status'

class TestCaseInfo(TypedDict):
    test_case_id: str   # '_case_id' typo fixed
    project_id: str
    description: str
    expected_result: str  # 'expected_resul' typo fixed

class TestRunInfo(TypedDict):
    test_run_id: str    # '_run_id' typo fixed
    test_case_id: str
    scheduled_time: str  # Must be one of: 'Morning', 'Afternoon', 'Evening', 'Night'
    actual_result: str
    run_status: str
    executed_by: str

class RunSummaryInfo(TypedDict):
    project_id: str
    test_case_ids: List[str]
    summary_report: str
    run_times: List[str]
    status: str  # 'sta' assumed as 'status'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Software QA test management system environment state.
        """

        # Projects: {project_id: ProjectInfo}
        self.projects: Dict[str, ProjectInfo] = {}

        # Test cases: {test_case_id: TestCaseInfo}
        self.test_cases: Dict[str, TestCaseInfo] = {}
        # Note: Test case IDs must be unique within each project.

        # Test runs: {test_run_id: TestRunInfo}
        self.test_runs: Dict[str, TestRunInfo] = {}
        # Note: scheduled_time must be one of ['Morning', 'Afternoon', 'Evening', 'Night']

        # Run summaries: {project_id: RunSummaryInfo}
        self.run_summaries: Dict[str, RunSummaryInfo] = {}

        # Constraints:
        # - Test case IDs must be unique within each project.
        # - Test cases must be associated with a valid, existing project.
        # - Scheduled test runs must have valid time slots ('Morning', 'Afternoon', 'Evening', 'Night').
        # - Actual results must be recorded after test execution.
        # - Summaries can only be generated for projects and test cases with at least one completed run.

    @staticmethod
    def _is_completed_status(status: str) -> bool:
        if not isinstance(status, str):
            return False
        return status.strip().lower() in {"completed", "passed", "failed"}

    def get_project_by_id(self, project_id: str) -> dict:
        """
        Retrieve the details of a project by its project_id.

        Args:
            project_id (str): Unique identifier for the project.

        Returns:
            dict:
                - On success: { "success": True, "data": ProjectInfo }
                - On failure if project does not exist: { "success": False, "error": "Project not found" }

        Constraints:
            - project_id must match an existing project.
        """
        project = self.projects.get(project_id)
        if project:
            return { "success": True, "data": project }
        else:
            return { "success": False, "error": "Project not found" }

    def list_projects(self) -> dict:
        """
        List all projects currently in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProjectInfo]  # List of all projects (may be empty if none)
            }
        """
        return {
            "success": True,
            "data": list(self.projects.values())
        }

    def get_test_cases_by_project(self, project_id: str) -> dict:
        """
        List all test cases associated with a specific project.

        Args:
            project_id (str): The ID of the project for which test cases are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[TestCaseInfo]  # May be an empty list if the project has no test cases
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., project does not exist)
            }

        Constraints:
            - The project ID must refer to an existing project.
            - Returned test cases are only those whose project_id matches the provided one.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist"}

        result = [
            test_case for test_case in self.test_cases.values()
            if test_case["project_id"] == project_id
        ]

        return {"success": True, "data": result}

    def get_test_case_by_id(self, test_case_id: str) -> dict:
        """
        Retrieve details for a given test case by its test_case_id.

        Args:
            test_case_id (str): The unique identifier of the test case.

        Returns:
            dict: {
                "success": True,
                "data": TestCaseInfo  # Dict containing test case details.
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found.
            }

        Constraints:
            - test_case_id must exist in the system.
        """
        test_case = self.test_cases.get(test_case_id)
        if not test_case:
            return { "success": False, "error": "Test case not found" }
        return { "success": True, "data": test_case }

    def is_test_case_id_unique_within_project(self, test_case_id: str, project_id: str) -> dict:
        """
        Check if the given test_case_id is unique within the given project.

        Args:
            test_case_id (str): The candidate test case ID to check for uniqueness.
            project_id (str): The project identifier to check within.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if unique (not yet used in the project), False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. project does not exist
            }

        Constraints:
            - Project must exist.
            - Test case IDs must be unique within each project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }
    
        for tc in self.test_cases.values():
            if tc["project_id"] == project_id and tc["test_case_id"] == test_case_id:
                return { "success": True, "data": False }  # Not unique

        return { "success": True, "data": True }  # Unique

    def get_test_runs_by_test_case(self, test_case_id: str) -> dict:
        """
        Retrieve all test runs associated with a given test_case_id.

        Args:
            test_case_id (str): The ID of the test case.

        Returns:
            dict:
              - On success:
                    { "success": True, "data": List[TestRunInfo] }
                (If no runs, "data" is an empty list.)
              - On failure:
                    { "success": False, "error": str }
                      - "Test case does not exist" if not found.

        Constraints:
            - The test_case_id must exist in self.test_cases.
        """
        if test_case_id not in self.test_cases:
            return { "success": False, "error": "Test case does not exist" }

        test_runs = [
            run_info for run_info in self.test_runs.values()
            if run_info["test_case_id"] == test_case_id
        ]
        return { "success": True, "data": test_runs }

    def get_test_run_by_id(self, test_run_id: str) -> dict:
        """
        Retrieve details for a given test run by its test_run_id.

        Args:
            test_run_id (str): Unique identifier of the test run.

        Returns:
            dict: {
                "success": True,
                "data": TestRunInfo  # Details for the test run
            }
            or
            {
                "success": False,
                "error": str  # If test_run_id does not exist
            }

        Constraints:
            - The test_run_id must exist in the system.
        """
        if test_run_id not in self.test_runs:
            return { "success": False, "error": "Test run with the given ID does not exist" }

        return { "success": True, "data": self.test_runs[test_run_id] }

    def list_test_runs_for_project(self, project_id: str) -> dict:
        """
        List all test runs for all test cases under a given project.

        Args:
            project_id (str): The ID of the project whose test runs are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[TestRunInfo],  # May be an empty list if no runs
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., project does not exist)
            }

        Constraints:
            - The project_id must correspond to an existing project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        # Get all test case IDs under this project
        test_case_ids = [
            test_case["test_case_id"]
            for test_case in self.test_cases.values()
            if test_case["project_id"] == project_id
        ]

        # Gather test runs whose test_case_id is under this project
        test_runs = [
            test_run
            for test_run in self.test_runs.values()
            if test_run["test_case_id"] in test_case_ids
        ]

        return { "success": True, "data": test_runs }

    def get_run_summary_by_project(self, project_id: str) -> dict:
        """
        Retrieve the run summary for a given project.

        Args:
            project_id (str): The unique identifier for the project.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": RunSummaryInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Project does not exist" | "No run summary found for project"
                    }

        Constraints:
            - The project must exist.
            - The run summary for the project must exist (i.e., has been generated).
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        if project_id not in self.run_summaries:
            return { "success": False, "error": "No run summary found for project" }

        return { "success": True, "data": self.run_summaries[project_id] }

    def get_test_run_status(self, test_run_id: str) -> dict:
        """
        Obtain the current run_status of a specific test run.

        Args:
            test_run_id (str): The unique identifier of the test run to check.

        Returns:
            dict: {
                "success": True,
                "data": str  # The 'run_status' of the test run
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., test run not found)
            }

        Constraints:
            - The test_run_id must exist in the system.
        """
        test_run = self.test_runs.get(test_run_id)
        if test_run is None:
            return {"success": False, "error": "Test run not found"}
        return {"success": True, "data": test_run["run_status"]}

    def get_allowed_time_slots(self) -> dict:
        """
        Retrieve the valid allowed time slots for scheduling test runs.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # ['Morning', 'Afternoon', 'Evening', 'Night']
            }

        This operation is always successful and does not require any input.
        """
        allowed_slots = ['Morning', 'Afternoon', 'Evening', 'Night']
        return {"success": True, "data": allowed_slots}

    def has_completed_runs(self, project_id: str, test_case_ids: list) -> dict:
        """
        Determine if there is at least one completed run for the given test_case_ids under a specific project.

        Args:
            project_id (str): The ID of the project.
            test_case_ids (List[str]): List of test case IDs for which to check completed runs.

        Returns:
            dict:
            - On success:
                {
                    "success": True,
                    "data": {
                        "has_completed": bool,  # True if at least one of the test_case_ids has a completed run
                        "completed_test_cases": List[str]  # IDs which have at least one completed run
                    }
                }
            - On failure:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }
        Constraints:
            - Project must exist.
            - Test cases must exist and belong to the specified project.
            - Terminal execution statuses such as 'Completed', 'Passed', or 'Failed'
              are considered completed runs.
        """
        # 1. Check if project exists
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }

        # 2. Collect all test cases for this project and check test_case_ids
        valid_test_cases_for_project = {
            tc_id for tc_id, tc_info in self.test_cases.items()
            if tc_info["project_id"] == project_id
        }

        invalid_test_cases = [tc_id for tc_id in test_case_ids if tc_id not in valid_test_cases_for_project]
        if invalid_test_cases:
            return { "success": False, "error": f"Invalid test_case_id(s) for project: {invalid_test_cases}" }

        # 3. Check for completed runs for these test cases
        completed_test_cases = set()
        for test_run in self.test_runs.values():
            if (test_run["test_case_id"] in test_case_ids and
                self._is_completed_status(test_run["run_status"])):
                completed_test_cases.add(test_run["test_case_id"])

        return {
            "success": True,
            "data": {
                "has_completed": bool(completed_test_cases),
                "completed_test_cases": list(completed_test_cases)
            }
        }

    def add_test_case(
        self,
        project_id: str,
        test_case_id: str,
        description: str,
        expected_result: str
    ) -> dict:
        """
        Add a new test case to a project.

        Args:
            project_id (str): The ID of the project the test case is for. Must already exist.
            test_case_id (str): The new test case's ID. Must be unique within the project.
            description (str): Description of the test case.
            expected_result (str): Expected outcome of executing the test case.

        Returns:
            dict: {
                "success": True,
                "message": "Test case <id> added to project <project_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The project must exist.
            - The test_case_id must be unique within the project.
        """
        if project_id not in self.projects:
            return { "success": False, "error": "Project does not exist" }
    
        # Check for uniqueness of test_case_id within this project
        for tc in self.test_cases.values():
            if tc['project_id'] == project_id and tc['test_case_id'] == test_case_id:
                return { "success": False, "error": "Test case ID already exists in this project" }

        # Create and add the test case
        test_case_info: TestCaseInfo = {
            "test_case_id": test_case_id,
            "project_id": project_id,
            "description": description,
            "expected_result": expected_result
        }
        self.test_cases[test_case_id] = test_case_info

        return {
            "success": True,
            "message": f"Test case {test_case_id} added to project {project_id}"
        }

    def schedule_test_run(
        self,
        test_run_id: str,
        test_case_id: str,
        scheduled_time: str,
        executed_by: str
    ) -> dict:
        """
        Schedule a new test run for a given test case at a specified, valid time slot.

        Args:
            test_run_id (str): Unique identifier for the new test run.
            test_case_id (str): The ID of the test case to run. Must exist.
            scheduled_time (str): When the test run is scheduled. Must be one of {'Morning', 'Afternoon', 'Evening', 'Night'}.
            executed_by (str): User assigned to execute the run.

        Returns:
            dict: 
              On success:
                {
                    "success": True,
                    "message": "Test run scheduled successfully."
                }
              On error:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
          - test_run_id must be unique.
          - test_case_id must exist.
          - scheduled_time must be a valid slot.
        """
        allowed_slots = {'Morning', 'Afternoon', 'Evening', 'Night'}

        if test_run_id in self.test_runs:
            return { "success": False, "error": "Test run ID already exists." }
        if test_case_id not in self.test_cases:
            return { "success": False, "error": "Test case ID does not exist." }
        if scheduled_time not in allowed_slots:
            return { "success": False, "error": "Invalid scheduled_time slot." }

        self.test_runs[test_run_id] = {
            "test_run_id": test_run_id,
            "test_case_id": test_case_id,
            "scheduled_time": scheduled_time,
            "actual_result": "",
            "run_status": "Scheduled",
            "executed_by": executed_by
        }

        return { "success": True, "message": "Test run scheduled successfully." }

    def record_test_run_result(self, test_run_id: str, actual_result: str, run_status: str) -> dict:
        """
        Record the result and status update of a test run after it has been executed.

        Args:
            test_run_id (str): The ID of the test run to update.
            actual_result (str): The observed outcome/result of the test run.
            run_status (str): New status for the test run (e.g. 'Completed', 'Passed', 'Failed').

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Test run result recorded successfully"
                    }
                On failure (e.g. test_run_id not found, invalid input):
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The test_run_id must exist.
            - Both actual_result and run_status must be non-empty.
        """
        if test_run_id not in self.test_runs:
            return { "success": False, "error": "Test run ID not found" }
        if not actual_result or not isinstance(actual_result, str):
            return { "success": False, "error": "Actual result must be a non-empty string" }
        if not run_status or not isinstance(run_status, str):
            return { "success": False, "error": "Run status must be a non-empty string" }
    
        test_run = self.test_runs[test_run_id]
        test_run["actual_result"] = actual_result
        test_run["run_status"] = run_status

        return { "success": True, "message": "Test run result recorded successfully" }

    def generate_run_summary(self, project_id: str, test_case_ids: list) -> dict:
        """
        Produce a summary report for a project and selected test cases,
        only if at least one run is completed.

        Args:
            project_id (str): The ID of the project.
            test_case_ids (List[str]): List of test case IDs that belong to the project.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Run summary generated.",
                    "summary_report": str,
                    "run_summary": RunSummaryInfo
                }
                On error:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - project_id must exist.
            - All test_case_ids must exist and belong to the project.
            - At least one test run in a terminal execution status such as
              'Completed', 'Passed', or 'Failed' for these test cases must exist.
            - Updates or creates the run summary for this project.
        """
        # Validate project
        if project_id not in self.projects:
            return {"success": False, "error": "Project does not exist."}

        # Validate test case IDs and association to project
        for tcid in test_case_ids:
            tc_info = self.test_cases.get(tcid)
            if not tc_info or tc_info["project_id"] != project_id:
                return {"success": False, "error": f"Test case {tcid} does not exist or does not belong to project."}

        # Treat execution-complete statuses as terminal regardless of pass/fail outcome.
        completed_runs = [
            run for run in self.test_runs.values()
            if run["test_case_id"] in test_case_ids and self._is_completed_status(run["run_status"])
        ]
        if not completed_runs:
            return {"success": False, "error": "No completed runs for these test cases; cannot generate summary."}

        # Generate run summary (simple structure)
        run_times = [run["scheduled_time"] for run in completed_runs]
        summary_strs = []
        for run in completed_runs:
            case = self.test_cases.get(run["test_case_id"], {})
            summary_strs.append(
                f"Test Case {run['test_case_id']}: "
                f"Expected: {case.get('expected_result', 'N/A')}, "
                f"Actual: {run['actual_result']}, "
                f"Run by: {run.get('executed_by', 'Unknown')} at {run['scheduled_time']}, "
                f"Status: {run['run_status']}"
            )
        summary_report = "Run Summary:\n" + "\n".join(summary_strs)

        run_summary: RunSummaryInfo = {
            "project_id": project_id,
            "test_case_ids": test_case_ids,
            "summary_report": summary_report,
            "run_times": run_times,
            "status": "Completed",
        }
        self.run_summaries[project_id] = run_summary

        return {
            "success": True,
            "message": "Run summary generated.",
            "summary_report": summary_report,
            "run_summary": run_summary,
        }

    def update_test_run_status(self, test_run_id: str, new_status: str) -> dict:
        """
        Update the status of a test run.

        Args:
            test_run_id (str): Unique identifier of the test run to update.
            new_status (str): The new status to assign (e.g., 'scheduled', 'running', 'completed').

        Returns:
            dict:
                - On success: { "success": True, "message": "Test run status updated." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - test_run_id must exist.
            - Optionally (for data integrity), new_status should be one of: 'scheduled', 'running', 'completed'.

        """
        if test_run_id not in self.test_runs:
            return { "success": False, "error": "Test run ID does not exist." }

        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid status value." }

        # Update the status
        self.test_runs[test_run_id]["run_status"] = new_status.strip()
        return { "success": True, "message": "Test run status updated." }

    def update_project_status(self, project_id: str, new_status: str) -> dict:
        """
        Update the status value for a project.

        Args:
            project_id (str): The unique identifier for the project.
            new_status (str): The new status value to set for the project.

        Returns:
            dict:
                - Success: {"success": True, "message": "Project status updated."}
                - Failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The project must exist.
        """
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found."}
        if not isinstance(new_status, str) or not new_status.strip():
            return {"success": False, "error": "Invalid new status."}

        self.projects[project_id]["status"] = new_status.strip()
        return {"success": True, "message": "Project status updated."}

    def delete_test_case(self, test_case_id: str) -> dict:
        """
        Remove a test case from the system by its ID. Also removes all associated test runs.

        Args:
            test_case_id (str): The unique identifier of the test case to delete.

        Returns:
            dict: {
                "success": True,
                "message": str  # Summary of deletion
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. "Test case not found")
            }

        Constraints:
            - The test case must exist in the system.
            - All test runs associated with this test case will also be deleted.
        """
        if test_case_id not in self.test_cases:
            return { "success": False, "error": "Test case not found" }

        # Delete the test case
        del self.test_cases[test_case_id]

        # Delete associated test runs
        to_delete = [run_id for run_id, run_info in self.test_runs.items()
                     if run_info["test_case_id"] == test_case_id]
        for run_id in to_delete:
            del self.test_runs[run_id]

        return {
            "success": True,
            "message": f"Test case '{test_case_id}' and {len(to_delete)} associated test run(s) deleted."
        }

    def delete_test_run(self, test_run_id: str) -> dict:
        """
        Remove a specific test run from the system.

        Args:
            test_run_id (str): The ID of the test run to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Test run <id> deleted successfully."
            }
            OR
            {
                "success": False,
                "error": "Test run not found."
            }

        Constraints:
            - The specified test_run_id must exist in the system.
            - No effect if the test run does not exist.
        """
        if test_run_id not in self.test_runs:
            return { "success": False, "error": "Test run not found." }

        del self.test_runs[test_run_id]
        return { "success": True, "message": f"Test run {test_run_id} deleted successfully." }

    def add_project(self, project_id: str, name: str, description: str, status: str) -> dict:
        """
        Add a new project to the QA test management system.

        Args:
            project_id (str): Unique identifier for the project.
            name (str): Name of the project.
            description (str): Description of the project.
            status (str): Status of the project (e.g., 'Active', 'Inactive').

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Project added: <project_name>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - project_id must be unique and not already used.
            - All fields are required (not blank).
        """
        # Basic validation
        if not all([project_id, name, description, status]):
            return { "success": False, "error": "All fields (project_id, name, description, status) must be provided and non-empty." }

        if project_id in self.projects:
            return { "success": False, "error": f"Project ID '{project_id}' already exists." }

        self.projects[project_id] = {
            "project_id": project_id,
            "name": name,
            "description": description,
            "status": status
        }

        return { "success": True, "message": f"Project added: {name}" }


class SoftwareQATestManagementSystem(BaseEnv):
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

    def get_project_by_id(self, **kwargs):
        return self._call_inner_tool('get_project_by_id', kwargs)

    def list_projects(self, **kwargs):
        return self._call_inner_tool('list_projects', kwargs)

    def get_test_cases_by_project(self, **kwargs):
        return self._call_inner_tool('get_test_cases_by_project', kwargs)

    def get_test_case_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_case_by_id', kwargs)

    def is_test_case_id_unique_within_project(self, **kwargs):
        return self._call_inner_tool('is_test_case_id_unique_within_project', kwargs)

    def get_test_runs_by_test_case(self, **kwargs):
        return self._call_inner_tool('get_test_runs_by_test_case', kwargs)

    def get_test_run_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_run_by_id', kwargs)

    def list_test_runs_for_project(self, **kwargs):
        return self._call_inner_tool('list_test_runs_for_project', kwargs)

    def get_run_summary_by_project(self, **kwargs):
        return self._call_inner_tool('get_run_summary_by_project', kwargs)

    def get_test_run_status(self, **kwargs):
        return self._call_inner_tool('get_test_run_status', kwargs)

    def get_allowed_time_slots(self, **kwargs):
        return self._call_inner_tool('get_allowed_time_slots', kwargs)

    def has_completed_runs(self, **kwargs):
        return self._call_inner_tool('has_completed_runs', kwargs)

    def add_test_case(self, **kwargs):
        return self._call_inner_tool('add_test_case', kwargs)

    def schedule_test_run(self, **kwargs):
        return self._call_inner_tool('schedule_test_run', kwargs)

    def record_test_run_result(self, **kwargs):
        return self._call_inner_tool('record_test_run_result', kwargs)

    def generate_run_summary(self, **kwargs):
        return self._call_inner_tool('generate_run_summary', kwargs)

    def update_test_run_status(self, **kwargs):
        return self._call_inner_tool('update_test_run_status', kwargs)

    def update_project_status(self, **kwargs):
        return self._call_inner_tool('update_project_status', kwargs)

    def delete_test_case(self, **kwargs):
        return self._call_inner_tool('delete_test_case', kwargs)

    def delete_test_run(self, **kwargs):
        return self._call_inner_tool('delete_test_run', kwargs)

    def add_project(self, **kwargs):
        return self._call_inner_tool('add_project', kwargs)
