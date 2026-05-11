# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import uuid



class BuildArtifactInfo(TypedDict):
    artifact_id: str
    version: str
    creation_time: str
    checksum: str
    status: str  # "sta" is interpreted as "status"

class DeploymentEnvironmentInfo(TypedDict):
    environment_id: str
    name: str
    status: str
    configuration: str

class DeploymentRecordInfo(TypedDict):
    deployment_id: str
    artifact_id: str
    environment_id: str
    deployed_at: str
    status: str
    performed_by: str

class DeploymentLogInfo(TypedDict):
    deployment_id: str
    timestamp: str
    message: str
    level: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Build Artifacts: {artifact_id: BuildArtifactInfo}
        self.build_artifacts: Dict[str, BuildArtifactInfo] = {}

        # Deployment Environments: {environment_id: DeploymentEnvironmentInfo}
        self.deployment_environments: Dict[str, DeploymentEnvironmentInfo] = {}

        # Deployment Records: {deployment_id: DeploymentRecordInfo}
        self.deployment_records: Dict[str, DeploymentRecordInfo] = {}

        # Deployment Logs: {deployment_id: [DeploymentLogInfo]}
        self.deployment_logs: Dict[str, List[DeploymentLogInfo]] = {}

        # Constraints:
        # - Only build artifacts with status "ready" or "approved" can be deployed.
        # - Each deployment environment can have at most one active deployed version at a time.
        # - Deployments must be logged, and all deployment actions are auditable.
        # - Rollback operations must only target previously deployed build artifacts.

    @staticmethod
    def _parse_timestamp_value(value: Any):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except Exception:
                return None
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromtimestamp(float(text), tz=timezone.utc)
        except Exception:
            pass
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return None

    def _latest_known_timestamp(self) -> datetime:
        timestamps = []
        for artifact in self.build_artifacts.values():
            parsed = self._parse_timestamp_value(artifact.get("creation_time"))
            if parsed:
                timestamps.append(parsed)
        for record in self.deployment_records.values():
            parsed = self._parse_timestamp_value(record.get("deployed_at"))
            if parsed:
                timestamps.append(parsed)
        for logs in self.deployment_logs.values():
            for entry in logs:
                parsed = self._parse_timestamp_value(entry.get("timestamp"))
                if parsed:
                    timestamps.append(parsed)
        if timestamps:
            return max(timestamps)
        return datetime(2023, 1, 1, tzinfo=timezone.utc)

    def _next_controlled_timestamp(self) -> str:
        cursor = getattr(self, "_timestamp_cursor", None)
        latest_known = self._latest_known_timestamp()
        if cursor is None or cursor < latest_known:
            cursor = latest_known
        cursor = cursor + timedelta(minutes=1)
        self._timestamp_cursor = cursor
        return cursor.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _record_sort_key(self, record: Dict[str, Any]):
        parsed = self._parse_timestamp_value(record.get("deployed_at"))
        if parsed is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        return parsed

    def list_build_artifacts(self) -> dict:
        """
        Retrieve all build artifacts with their metadata.

        Args:
            None

        Returns:
            dict:
                - success (bool): True if retrieval is successful.
                - data (List[BuildArtifactInfo]): List of all build artifacts' info; may be empty if none exist.
        """
        artifacts = list(self.build_artifacts.values())
        return {
            "success": True,
            "data": artifacts
        }

    def get_build_artifact_by_id(self, artifact_id: str) -> dict:
        """
        Retrieve details for a specific build artifact via its artifact_id.

        Args:
            artifact_id (str): The unique identifier for the build artifact.

        Returns:
            dict: 
                - On success: {"success": True, "data": BuildArtifactInfo}
                - On failure: {"success": False, "error": "Build artifact not found"}

        Constraints:
            - The artifact_id must correspond to an existing build artifact in the system.
        """
        if artifact_id not in self.build_artifacts:
            return {"success": False, "error": "Build artifact not found"}
        return {"success": True, "data": self.build_artifacts[artifact_id]}

    def list_ready_or_approved_build_artifacts(self) -> dict:
        """
        Retrieve all build artifacts eligible for deployment (status: "ready" or "approved").

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[BuildArtifactInfo]  # List of artifacts with eligible status (may be empty)
                }
        Constraints:
            - Only artifacts with status "ready" or "approved" are included.
        """
        eligible_statuses = {"ready", "approved"}
        result = [
            artifact for artifact in self.build_artifacts.values()
            if artifact.get("status") in eligible_statuses
        ]
        return {"success": True, "data": result}

    def get_latest_build_artifact(self) -> dict:
        """
        Find the most recent eligible build artifact by creation_time.

        Eligibility: Only 'ready' or 'approved' artifacts are considered (per constraints).
        Among all eligible artifacts, the one with the latest (max) creation_time is selected.

        Returns:
            dict: {
                "success": True,
                "data": BuildArtifactInfo  # Info for the most recent eligible artifact
            }
            or
            {
                "success": False,
                "error": str  # If no eligible artifacts exist or other error
            }
        """
        eligible_status = {"ready", "approved"}
        eligible_artifacts = [
            art for art in self.build_artifacts.values()
            if art.get("status") in eligible_status
        ]
        if not eligible_artifacts:
            return { "success": False, "error": "No eligible build artifact found" }

        # Sort by creation_time descending, pick the first
        # Assume creation_time is ISO8601 or at least string-sortable
        latest_artifact = max(
            eligible_artifacts,
            key=lambda art: art.get("creation_time", "")
        )

        return { "success": True, "data": latest_artifact }

    def list_deployment_environments(self) -> dict:
        """
        Retrieve all defined deployment environments.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DeploymentEnvironmentInfo]  # List of environments (may be empty)
            }

        Constraints:
            - No constraints; this is a query operation.
            - Returns an empty list if no environments are defined.
        """
        environments = list(self.deployment_environments.values())
        return {
            "success": True,
            "data": environments
        }

    def get_environment_by_id(self, environment_id: str) -> dict:
        """
        Get details of a deployment environment using environment_id.

        Args:
            environment_id (str): The unique identifier of the deployment environment.

        Returns:
            dict:
                - On success: {"success": True, "data": DeploymentEnvironmentInfo}
                - On failure: {"success": False, "error": str}

        Constraints:
            - The specified environment_id must exist in the deployment_environments dictionary.
        """
        env = self.deployment_environments.get(environment_id)
        if env is None:
            return {"success": False, "error": "Environment not found"}
        return {"success": True, "data": env}

    def get_active_deployment_for_environment(self, environment_id: str) -> dict:
        """
        Retrieve the currently active deployed artifact in a particular environment.

        Args:
            environment_id (str): ID of the deployment environment.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": DeploymentRecordInfo or None   # The active deployment record, or None if none active.
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of error (e.g. environment not found)
                    }

        Constraints:
            - The environment must exist.
            - There should be at most one active deployed artifact per environment.
        """
        if environment_id not in self.deployment_environments:
            return {"success": False, "error": "Deployment environment does not exist"}

        # Assuming 'status' for active deployments is "active" or "deployed".
        # Let's consider { "active", "deployed", "success" } are synonyms for active.
        ACTIVE_STATUSES = {"active", "deployed", "success"}

        # Find all candidate records
        candidates = [
            rec for rec in self.deployment_records.values()
            if rec["environment_id"] == environment_id and rec["status"].lower() in ACTIVE_STATUSES
        ]

        if not candidates:
            return {"success": True, "data": None}

        # If multiple, pick the one with the latest deployed_at timestamp
        # (assuming ISO 8601 or comparable, so lex sort works)
        latest = max(candidates, key=self._record_sort_key)

        return {"success": True, "data": latest}

    def list_deployment_records(self) -> dict:
        """
        Retrieve all deployment records (deployment history) in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[DeploymentRecordInfo],  # May be an empty list if no records exist
            }
        """
        records = list(self.deployment_records.values())
        return {"success": True, "data": records}

    def get_deployment_record_by_id(self, deployment_id: str) -> dict:
        """
        Get details of a specific deployment record by its deployment_id.

        Args:
            deployment_id (str): The identifier for the deployment record.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": DeploymentRecordInfo  # details for the specified deployment_id
                    }
                On failure (deployment_id not found):
                    {
                        "success": False,
                        "error": "Deployment record not found"
                    }
        """
        record = self.deployment_records.get(deployment_id)
        if not record:
            return { "success": False, "error": "Deployment record not found" }
        return { "success": True, "data": record }

    def list_deployment_records_for_environment(self, environment_id: str) -> dict:
        """
        Get all deployment records related to a given environment.

        Args:
            environment_id (str): The ID of the deployment environment.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[DeploymentRecordInfo]  # All deployment records where environment_id matches
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., environment not found
                    }
        Constraints:
            - The specified environment_id must exist in the deployment_environments.
            - If there are no deployment records for the environment, returns empty list in "data".
        """
        if environment_id not in self.deployment_environments:
            return {"success": False, "error": "Deployment environment not found"}

        records = [
            record for record in self.deployment_records.values()
            if record["environment_id"] == environment_id
        ]

        return {"success": True, "data": records}

    def list_previous_deployments_for_environment(self, environment_id: str) -> dict:
        """
        Get the history of previously deployed artifacts for a deployment environment.
        Useful for rollback validation. Only considers environments that exist.

        Args:
            environment_id (str): The ID of the deployment environment to query.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[DeploymentRecordInfo], # List can be empty.
                  }
                - On error: {
                    "success": False,
                    "error": str, # Reason for failure, e.g., environment does not exist.
                  }

        Constraints:
            - The environment must exist.
        """
        if environment_id not in self.deployment_environments:
            return {"success": False, "error": "Deployment environment does not exist"}

        records = [
            record for record in self.deployment_records.values()
            if record["environment_id"] == environment_id
        ]
        # Optional: sort the records by deployed_at, most recent first
        records.sort(key=self._record_sort_key, reverse=True)

        return {"success": True, "data": records}

    def get_deployment_log(self, deployment_id: str) -> dict:
        """
        Get all log entries for a specific deployment action.

        Args:
            deployment_id (str): The unique identifier of the deployment to query logs for.

        Returns:
            dict: {
                "success": True,
                "data": List[DeploymentLogInfo],  # List of logs for the deployment; may be empty
            }
            or
            {
                "success": False,
                "error": str  # Explanation of error, e.g. "Deployment record does not exist"
            }

        Constraints:
            - The deployment_id must correspond to an existing deployment record.
            - Returns an empty list if no logs exist for the deployment but deployment is valid.
        """
        if deployment_id not in self.deployment_records:
            return { "success": False, "error": "Deployment record does not exist" }
    
        deployment_logs = self.deployment_logs.get(deployment_id, [])
        return { "success": True, "data": deployment_logs }

    def get_latest_deployment_record_for_environment(self, environment_id: str) -> dict:
        """
        Get the most recent deployment record for the specified environment.

        Args:
            environment_id (str): The unique identifier of the deployment environment.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": DeploymentRecordInfo or None  # The latest deployment record, or None if none exist.
                }
                or
                {
                    "success": False,
                    "error": str  # Error message if the environment does not exist
                }
    
        Constraints:
            - The environment_id must exist.
            - If no deployment records exist for the environment, "data" will be None.
        """
        if environment_id not in self.deployment_environments:
            return { "success": False, "error": "Environment does not exist" }
    
        records = [
            record for record in self.deployment_records.values()
            if record["environment_id"] == environment_id
        ]
        if not records:
            return { "success": True, "data": None }

        latest_record = max(records, key=self._record_sort_key)
        return { "success": True, "data": latest_record }

    def deploy_build_artifact(self, artifact_id: str, environment_id: str, performed_by: str) -> dict:
        """
        Deploy a specified build artifact to a deployment environment.
    
        Args:
            artifact_id (str): The ID of the build artifact to deploy. Must have status "ready" or "approved".
            environment_id (str): The ID of the deployment environment.
            performed_by (str): Actor performing the deployment.
    
        Returns:
            dict:
                On success: { "success": True, "message": "Artifact <artifact_id> deployed to environment <environment_id>" }
                On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Only build artifacts with status "ready" or "approved" can be deployed.
            - Each deployment environment can have at most one active deployed version at a time (the previous is marked "inactive").
            - Deployments must be logged (creates a DeploymentLogInfo entry).
        """

        # 1. Validate build artifact exists and is eligible
        artifact = self.build_artifacts.get(artifact_id)
        if not artifact:
            return {"success": False, "error": f"Build artifact {artifact_id} does not exist"}
        if artifact["status"] not in ("ready", "approved"):
            return {"success": False, "error": f"Build artifact {artifact_id} not deployable (status: {artifact['status']})"}

        # 2. Validate environment exists
        environment = self.deployment_environments.get(environment_id)
        if not environment:
            return {"success": False, "error": f"Deployment environment {environment_id} does not exist"}

        # 3. Find and deactivate current active deployment for this environment
        for rec in self.deployment_records.values():
            if rec["environment_id"] == environment_id and rec["status"] == "active":
                rec["status"] = "inactive"
                # Optionally, could log this deactivation
                log_rec_id = rec["deployment_id"]
                log_entry = {
                    "deployment_id": log_rec_id,
                    "timestamp": self._next_controlled_timestamp(),
                    "message": f"Deployment deactivated due to new deployment ({artifact_id}).",
                    "level": "info"
                }
                if log_rec_id not in self.deployment_logs:
                    self.deployment_logs[log_rec_id] = []
                self.deployment_logs[log_rec_id].append(log_entry)

        # 4. Create new DeploymentRecord (status "active")
        deployment_id = str(uuid4())
        timestamp = self._next_controlled_timestamp()
        deployment_record = {
            "deployment_id": deployment_id,
            "artifact_id": artifact_id,
            "environment_id": environment_id,
            "deployed_at": timestamp,
            "status": "active",
            "performed_by": performed_by
        }
        self.deployment_records[deployment_id] = deployment_record

        # 5. Log the deployment action
        log_entry = {
            "deployment_id": deployment_id,
            "timestamp": timestamp,
            "message": f"Deployed artifact {artifact_id} to environment {environment_id} by {performed_by}.",
            "level": "info"
        }
        if deployment_id not in self.deployment_logs:
            self.deployment_logs[deployment_id] = []
        self.deployment_logs[deployment_id].append(log_entry)

        return {
            "success": True,
            "message": f"Artifact {artifact_id} deployed to environment {environment_id}"
        }

    def rollback_deployment(self, environment_id: str, artifact_id: str, performed_by: str) -> dict:
        """
        Rolls back the deployment for the specified environment to a previously deployed build artifact.
        The rollback is only permitted if the artifact has previously been deployed in the environment.
        Logs the rollback action for auditing.

        Args:
            environment_id (str): The deployment environment to roll back.
            artifact_id (str): The artifact to roll back to.
            performed_by (str): The user performing the rollback.

        Returns:
            dict: {
                "success": True,
                "message": "Rollback of env <id> to artifact <id> completed."
            } on success;
            {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - Only previously deployed artifacts may be rolled back to.
            - All rollback actions must be logged.
        """
        # Check environment exists
        if environment_id not in self.deployment_environments:
            return { "success": False, "error": f"Environment '{environment_id}' does not exist." }
        # Check artifact exists
        if artifact_id not in self.build_artifacts:
            return { "success": False, "error": f"Artifact '{artifact_id}' does not exist." }

        # Find previous deployments for this environment with the target artifact
        previous_deployment_ids = [
            rec_id for rec_id, record in self.deployment_records.items()
            if record["environment_id"] == environment_id and record["artifact_id"] == artifact_id
        ]
        if not previous_deployment_ids:
            return {
                "success": False,
                "error": f"Artifact '{artifact_id}' was never previously deployed to environment '{environment_id}'."
            }

        # Determine if already current: find the latest deployment for the environment
        records_env = [
            record for record in self.deployment_records.values()
            if record["environment_id"] == environment_id
        ]
        latest_record = None
        if records_env:
            latest_record = max(records_env, key=self._record_sort_key)

        if latest_record and latest_record["artifact_id"] == artifact_id:
            # Already at the desired rollback state
            msg = f"Environment '{environment_id}' is already at artifact '{artifact_id}'. Rollback is not needed."
            # Still log this as an audit trail
        else:
            for record in self.deployment_records.values():
                if record["environment_id"] == environment_id and record["status"] == "active":
                    record["status"] = "inactive"
                    old_log = {
                        "deployment_id": record["deployment_id"],
                        "timestamp": self._next_controlled_timestamp(),
                        "message": f"Deployment deactivated due to rollback to '{artifact_id}'.",
                        "level": "INFO"
                    }
                    if record["deployment_id"] not in self.deployment_logs:
                        self.deployment_logs[record["deployment_id"]] = []
                    self.deployment_logs[record["deployment_id"]].append(old_log)
            # Create a new DeploymentRecord to log the rollback
            deployment_id = str(uuid.uuid4())
            timestamp = self._next_controlled_timestamp()
            rollback_record = {
                "deployment_id": deployment_id,
                "artifact_id": artifact_id,
                "environment_id": environment_id,
                "deployed_at": timestamp,
                "status": "active",
                "performed_by": performed_by,
            }
            self.deployment_records[deployment_id] = rollback_record

            # Log the rollback action
            log_entry = {
                "deployment_id": deployment_id,
                "timestamp": timestamp,
                "message": f"Rollback: Environment '{environment_id}' rolled back to artifact '{artifact_id}' by '{performed_by}'.",
                "level": "INFO"
            }
            if deployment_id not in self.deployment_logs:
                self.deployment_logs[deployment_id] = []
            self.deployment_logs[deployment_id].append(log_entry)
            msg = f"Rollback of environment '{environment_id}' to artifact '{artifact_id}' completed."

        return {
            "success": True,
            "message": msg
        }

    def update_build_artifact_status(self, artifact_id: str, new_status: str) -> dict:
        """
        Change the status of a build artifact.

        Args:
            artifact_id (str): The identifier of the build artifact to update.
            new_status (str): The new status value (e.g., "ready", "approved", "deprecated").

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Status of artifact <artifact_id> updated to <new_status>."
                }
                or
                {
                    "success": False,
                    "error": "Build artifact not found"
                }

        Constraints:
            - The artifact_id must exist in the build_artifacts dictionary.
            - No restriction on new_status value based on current specification.
        """
        if artifact_id not in self.build_artifacts:
            return { "success": False, "error": "Build artifact not found" }

        self.build_artifacts[artifact_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Status of artifact {artifact_id} updated to {new_status}."
        }

    def update_environment_status(
        self, 
        environment_id: str, 
        status: str = None, 
        configuration: str = None
    ) -> dict:
        """
        Update the status and/or configuration for a deployment environment.

        Args:
            environment_id (str): The unique identifier of the deployment environment.
            status (str, optional): New operational status (e.g., "enabled", "disabled").
            configuration (str, optional): Updated environment configuration.

        Returns:
            dict: {
                "success": True,
                "message": "Environment status/configuration updated"
            }
            or
            {
                "success": False,
                "error": str describing reason for failure
            }

        Constraints:
            - The specified environment_id must exist.
            - At least one of status or configuration must be provided.
        """
        env = self.deployment_environments.get(environment_id)
        if env is None:
            return {"success": False, "error": "Environment does not exist."}
        if status is None and configuration is None:
            return {"success": False, "error": "No status or configuration provided to update."}
        if status is not None:
            env["status"] = status
        if configuration is not None:
            env["configuration"] = configuration
        # Save update (dict is mutable)
        self.deployment_environments[environment_id] = env
        return {"success": True, "message": "Environment status and/or configuration updated."}

    def log_deployment_action(
        self,
        deployment_id: str,
        timestamp: str,
        message: str,
        level: str
    ) -> dict:
        """
        Add a log entry to a deployment record.

        Args:
            deployment_id (str): The deployment record to log to.
            timestamp (str): The time of the log entry (ISO8601 or similar).
            message (str): The log message content.
            level (str): Log severity/type, e.g. 'INFO', 'ERROR'

        Returns:
            dict:
              On success: { "success": True, "message": "Log entry added to deployment X." }
              On failure: { "success": False, "error": <reason> }

        Constraints:
            - The deployment_id must refer to a valid deployment record.
        """
        if deployment_id not in self.deployment_records:
            return {"success": False, "error": "Deployment record not found."}

        log_entry = {
            "deployment_id": deployment_id,
            "timestamp": timestamp,
            "message": message,
            "level": level
        }

        if deployment_id not in self.deployment_logs:
            self.deployment_logs[deployment_id] = []

        self.deployment_logs[deployment_id].append(log_entry)
        return {"success": True, "message": f"Log entry added to deployment {deployment_id}."}


class SoftwareDeploymentManagementSystem(BaseEnv):
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

    def list_build_artifacts(self, **kwargs):
        return self._call_inner_tool('list_build_artifacts', kwargs)

    def get_build_artifact_by_id(self, **kwargs):
        return self._call_inner_tool('get_build_artifact_by_id', kwargs)

    def list_ready_or_approved_build_artifacts(self, **kwargs):
        return self._call_inner_tool('list_ready_or_approved_build_artifacts', kwargs)

    def get_latest_build_artifact(self, **kwargs):
        return self._call_inner_tool('get_latest_build_artifact', kwargs)

    def list_deployment_environments(self, **kwargs):
        return self._call_inner_tool('list_deployment_environments', kwargs)

    def get_environment_by_id(self, **kwargs):
        return self._call_inner_tool('get_environment_by_id', kwargs)

    def get_active_deployment_for_environment(self, **kwargs):
        return self._call_inner_tool('get_active_deployment_for_environment', kwargs)

    def list_deployment_records(self, **kwargs):
        return self._call_inner_tool('list_deployment_records', kwargs)

    def get_deployment_record_by_id(self, **kwargs):
        return self._call_inner_tool('get_deployment_record_by_id', kwargs)

    def list_deployment_records_for_environment(self, **kwargs):
        return self._call_inner_tool('list_deployment_records_for_environment', kwargs)

    def list_previous_deployments_for_environment(self, **kwargs):
        return self._call_inner_tool('list_previous_deployments_for_environment', kwargs)

    def get_deployment_log(self, **kwargs):
        return self._call_inner_tool('get_deployment_log', kwargs)

    def get_latest_deployment_record_for_environment(self, **kwargs):
        return self._call_inner_tool('get_latest_deployment_record_for_environment', kwargs)

    def deploy_build_artifact(self, **kwargs):
        return self._call_inner_tool('deploy_build_artifact', kwargs)

    def rollback_deployment(self, **kwargs):
        return self._call_inner_tool('rollback_deployment', kwargs)

    def update_build_artifact_status(self, **kwargs):
        return self._call_inner_tool('update_build_artifact_status', kwargs)

    def update_environment_status(self, **kwargs):
        return self._call_inner_tool('update_environment_status', kwargs)

    def log_deployment_action(self, **kwargs):
        return self._call_inner_tool('log_deployment_action', kwargs)
