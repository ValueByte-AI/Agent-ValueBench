# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from typing import Dict
import datetime



# Represents a unique interaction/session and its metadata
class SessionInfo(TypedDict):
    session_id: str
    client_ip: str
    start_time: str
    end_time: str
    connection_metadata: str
    tls_ssl_version: str
    request_count: int
    associated_rule_id: str

# Represents a WAF firewall rule
class WAFRuleInfo(TypedDict):
    rule_id: str
    rule_type: str
    rule_pattern: str
    action: str
    status: str
    priority: int

# Represents a security report (audit/snapshot)
class SecurityReportInfo(TypedDict):
    report_id: str
    generated_time: str
    target_scope: str
    summary: str
    detail: str

# Represents an API user or system account
class APIUserInfo(TypedDict):
    user_id: str
    api_key: str
    permissions: str
    last_accessed: str

# Represents an event/request logged by the WAF
class LogEntryInfo(TypedDict):
    log_id: str
    session_id: str
    timestamp: str
    event_type: str
    detail: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}
        # WAFRules: {rule_id: WAFRuleInfo}
        self.waf_rules: Dict[str, WAFRuleInfo] = {}
        # SecurityReports: {report_id: SecurityReportInfo}
        self.security_reports: Dict[str, SecurityReportInfo] = {}
        # APIUsers: {user_id: APIUserInfo}
        self.api_users: Dict[str, APIUserInfo] = {}
        # LogEntries: {log_id: LogEntryInfo}
        self.log_entries: Dict[str, LogEntryInfo] = {}

        # Constraints:
        # - Multiple sessions can exist per client IP; session_id is the unique identifier.
        # - Only authorized API users may retrieve/modify session and rule information.
        # - TLS/SSL version must be recorded for all secure sessions.
        # - WAF rules are applied by priority; changes affect active/future sessions as specified.
        # - Logging must be consistent and immutable for audit purposes.

    def get_sessions_by_client_ip(self, client_ip: str) -> dict:
        """
        Retrieve all session records associated with a given client_ip.

        Args:
            client_ip (str): The client IP address to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[SessionInfo],  # List of sessions for the given IP (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (invalid input)
            }

        Constraints:
            - Multiple sessions can exist per client IP.
            - Only authorized API users may retrieve session information, but no context is provided here.
        """
        if not isinstance(client_ip, str) or not client_ip.strip():
            return { "success": False, "error": "Invalid client_ip parameter." }

        result = [
            session_info
            for session_info in self.sessions.values()
            if session_info.get("client_ip") == client_ip
        ]

        return { "success": True, "data": result }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve the complete session details for a given session_id.

        Args:
            session_id (str): The unique identifier for the desired session.

        Returns:
            dict: 
                - If found: { "success": True, "data": SessionInfo }
                - If not found: { "success": False, "error": "Session not found" }

        Constraints:
            - session_id must exist in self.sessions.
            - No modification of state.
            - No authorization check unless specified.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session not found" }
        return { "success": True, "data": session }

    def get_tls_ssl_version_for_session(self, session_id: str) -> dict:
        """
        Query the TLS/SSL version used in a particular session.

        Args:
            session_id (str): The unique session identifier to look up.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": str }  # TLS/SSL version string (may be empty if data issue)
                - On failure:
                    { "success": False, "error": "Session not found" }

        Constraints:
            - Session must exist (identified by session_id).
            - For secure sessions, TLS/SSL version should be recorded; here, the method returns what is stored.
        """
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session not found" }

        return { "success": True, "data": session.get("tls_ssl_version", "") }

    def get_tls_ssl_versions_by_client_ip(self, client_ip: str) -> dict:
        """
        Aggregate and return the TLS/SSL versions for all sessions associated with a client IP.

        Args:
            client_ip (str): The IP address of the client whose sessions' TLS/SSL versions are to be returned.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of tls_ssl_version strings associated with the given client_ip
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Each session must record a TLS/SSL version if it is secure.
            - No permissions are checked in this method.
        """
        if not isinstance(client_ip, str) or not client_ip.strip():
            return {"success": False, "error": "Invalid or missing client_ip parameter"}

        # Collect TLS/SSL versions from all sessions for this client_ip
        tls_versions = [
            session["tls_ssl_version"]
            for session in self.sessions.values()
            if session["client_ip"] == client_ip and session["tls_ssl_version"]
        ]

        return {"success": True, "data": tls_versions}

    def list_api_users(self) -> dict:
        """
        Retrieve the list of all API users registered in the WAF management system.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[APIUserInfo]  # List of API user info dicts (may be empty)
                }
            or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - No parameters required.
            - Returns all API users in the system.
        """
        users = list(self.api_users.values())
        return {
            "success": True,
            "data": users
        }

    def get_api_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve full details of an API user by their user_id.

        Args:
            user_id (str): The identifier of the API user.

        Returns:
            dict: {
                "success": True,
                "data": APIUserInfo  # User information if found
            }
            or
            {
                "success": False,
                "error": str  # If user is not found
            }

        Constraints:
            - The user_id must exist in the system.
        """
        api_user = self.api_users.get(user_id)
        if api_user is None:
            return { "success": False, "error": "API user not found" }

        return { "success": True, "data": api_user }

    def get_waf_rule_by_id(self, rule_id: str) -> dict:
        """
        Retrieve the configuration (WAFRuleInfo) for a specific WAF rule.

        Args:
            rule_id (str): The unique identifier of the WAF rule.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": WAFRuleInfo
                  }
                - On failure: {
                      "success": False,
                      "error": "WAF rule not found"
                  }

        Constraints:
            - WAF rule identified by rule_id must exist.
            - No permission or mutation enforced in this query operation.
        """
        rule = self.waf_rules.get(rule_id)
        if rule is None:
            return { "success": False, "error": "WAF rule not found" }
        return { "success": True, "data": rule }

    def list_waf_rules(self, sort_by_priority: bool = False) -> dict:
        """
        Return all configured WAF rules, optionally sorted by priority.

        Args:
            sort_by_priority (bool, optional): If True, return list sorted by WAFRuleInfo['priority'] ascending.

        Returns:
            dict: {
                "success": True,
                "data": List[WAFRuleInfo]  # List (possibly empty) of all WAF rules
            }
        """
        rules = list(self.waf_rules.values())
        if sort_by_priority:
            rules.sort(key=lambda rule: rule["priority"])
        return {"success": True, "data": rules}

    def get_security_report_by_id(self, report_id: str) -> dict:
        """
        Retrieve the full security report corresponding to the provided report_id.

        Args:
            report_id (str): The unique identifier of the security report to fetch.

        Returns:
            dict: 
                - { "success": True, "data": SecurityReportInfo } if the report exists.
                - { "success": False, "error": str } if the report_id does not exist.

        Constraints:
            - The report_id must exist within the system's security_reports.
            - No permission checks are enforced for this query.
        """
        report = self.security_reports.get(report_id)
        if report is None:
            return { "success": False, "error": "Security report with provided report_id does not exist." }
        return { "success": True, "data": report }

    def list_security_reports(self) -> dict:
        """
        List all generated security reports in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SecurityReportInfo],  # List may be empty if no reports exist
            }

        Constraints:
            - No input arguments.
            - Returns all security reports (read-only; reports are immutable).
        """
        # Retrieve all security reports as a list
        reports = list(self.security_reports.values())
        return { "success": True, "data": reports }

    def get_log_entries_by_session_id(self, session_id: str) -> dict:
        """
        Retrieve all log entries associated with a particular session.

        Args:
            session_id (str): The unique identifier for the session.

        Returns:
            dict: {
                "success": True,
                "data": List[LogEntryInfo],  # List (possibly empty) of log entries for the session
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., session does not exist)
            }

        Constraints:
            - session_id must reference an existing session.
            - Log entry data is immutable (query only).
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }

        log_entries = [
            log_info for log_info in self.log_entries.values()
            if log_info["session_id"] == session_id
        ]
        return { "success": True, "data": log_entries }

    def get_log_entry_by_id(self, log_id: str) -> dict:
        """
        Retrieve details for a specific log entry given its log_id.

        Args:
            log_id (str): The unique identifier of the log entry.

        Returns:
            dict: {
                "success": True,
                "data": LogEntryInfo  # the dictionary for the found log entry
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., log entry not found)
            }

        Constraints:
            - No user authorization is required to perform this lookup.
            - Log entry with matching log_id must exist in the system.
        """
        log_entry = self.log_entries.get(log_id)
        if log_entry is None:
            return {"success": False, "error": "Log entry not found"}
        return {"success": True, "data": log_entry}

    def list_log_entries_by_event_type(self, event_type: str) -> dict:
        """
        Retrieve all WAF log entries filtered by a specific event_type (e.g., 'alert', 'block').

        Args:
            event_type (str): The event type to filter log entries by.

        Returns:
            dict: 
                - { "success": True, "data": List[LogEntryInfo] }
                  (List may be empty if no log entries match)
                - { "success": False, "error": str }
                  (If the filter is not provided or is invalid)

        Constraints:
            - event_type must be a non-empty string.
            - Logging entries are immutable and fully accessible for querying.
        """
        if not isinstance(event_type, str) or not event_type.strip():
            return { "success": False, "error": "event_type must be provided and non-empty" }

        filtered_logs = [
            log for log in self.log_entries.values()
            if log.get("event_type") == event_type
        ]
        return { "success": True, "data": filtered_logs }

    def create_waf_rule(
        self,
        user_id: str,
        rule_id: str,
        rule_type: str,
        rule_pattern: str,
        action: str,
        status: str,
        priority: int
    ) -> dict:
        """
        Add a new WAF rule to the system (requires authorization).

        Args:
            user_id (str): ID of the API user making the request.
            rule_id (str): Unique identifier for the new WAF rule.
            rule_type (str): Type/category of the rule.
            rule_pattern (str): Pattern to be matched (string/regex).
            action (str): Action to be taken (e.g., 'allow', 'block').
            status (str): Rule status ('active', 'inactive', etc.).
            priority (int): Rule priority (lower is higher priority).

        Returns:
            dict: {
                "success": True,
                "message": "WAF rule <rule_id> created successfully"
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only authorized API users with proper permissions can create rules.
            - `rule_id` must be unique.
            - Rule parameters must be provided.
        """
        # Check user exists & is authorized
        user = self.api_users.get(user_id)
        if not user:
            return { "success": False, "error": "API user not found" }
    
        # Check permissions (assuming 'manage_rules' or 'admin' required)
        perms = user.get("permissions", "")
        permitted = ("manage_rules" in perms) or ("admin" in perms)
        if not permitted:
            return { "success": False, "error": "Permission denied: insufficient privileges" }
    
        # Ensure unique rule_id
        if rule_id in self.waf_rules:
            return { "success": False, "error": f"WAF rule with rule_id '{rule_id}' already exists" }
    
        # Basic validation of parameters (simplified)
        if not all([rule_id, rule_type, rule_pattern, action, status]) or not isinstance(priority, int):
            return { "success": False, "error": "Missing or invalid WAF rule fields" }
    
        new_rule: WAFRuleInfo = {
            "rule_id": rule_id,
            "rule_type": rule_type,
            "rule_pattern": rule_pattern,
            "action": action,
            "status": status,
            "priority": priority
        }
        self.waf_rules[rule_id] = new_rule
    
        return { "success": True, "message": f"WAF rule '{rule_id}' created successfully" }

    def update_waf_rule(
        self, 
        api_user_id: str,
        rule_id: str,
        action: str = None, 
        status: str = None, 
        rule_pattern: str = None, 
        priority: int = None
    ) -> dict:
        """
        Modify properties (action, status, pattern, priority) of an existing WAF rule.

        Args:
            api_user_id (str): The API user performing the update. Used for permission check.
            rule_id (str): The ID of the rule to update.
            action (Optional[str]): New action for the rule, if updating.
            status (Optional[str]): New status for the rule, if updating.
            rule_pattern (Optional[str]): New pattern for the rule, if updating.
            priority (Optional[int]): New priority for the rule, if updating.

        Returns:
            dict: 
                { "success": True, "message": "WAF rule updated successfully." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - Only authorized API users (permissions 'admin' or including 'waf_rule_write') may modify rules.
            - Specified rule_id must exist.
            - Only provided properties are updated.
            - Priority, if set, must be an integer >= 0.
        """

        # Check user exists
        user = self.api_users.get(api_user_id)
        if not user:
            return { "success": False, "error": "API user not found." }

        # Simple permission check (example: 'admin' or permission includes 'waf_rule_write')
        perms = user.get('permissions', '')
        if not ('admin' in perms or 'waf_rule_write' in perms):
            return { "success": False, "error": "Permission denied." }

        # Check that rule exists
        rule = self.waf_rules.get(rule_id)
        if not rule:
            return { "success": False, "error": "WAF rule not found." }

        # Build update map
        updates = {}
        if action is not None:
            updates['action'] = action
        if status is not None:
            updates['status'] = status
        if rule_pattern is not None:
            updates['rule_pattern'] = rule_pattern
        if priority is not None:
            if not isinstance(priority, int) or priority < 0:
                return { "success": False, "error": "Invalid value for 'priority': must be non-negative integer." }
            updates['priority'] = priority

        if not updates:
            return { "success": False, "error": "No properties specified for update." }

        # Apply updates
        for key, value in updates.items():
            rule[key] = value

        return { "success": True, "message": "WAF rule updated successfully." }

    def delete_waf_rule(self, rule_id: str, api_key: str) -> dict:
        """
        Remove a WAF rule from the system.

        Args:
            rule_id (str): The unique identifier of the WAF rule to be deleted.
            api_key (str): The API key of the user performing the deletion; must have sufficient permissions.

        Returns:
            dict:
                - On success: { "success": True, "message": "WAF rule <rule_id> deleted." }
                - On failure: { "success": False, "error": <error reason> }

        Constraints:
            - Only authorized API users (with appropriate permissions) may delete WAF rules.
            - The rule must exist in the system.
        """
        # Check if API key is provided and valid
        user_info = None
        for user in self.api_users.values():
            if user.get("api_key") == api_key:
                user_info = user
                break
        if user_info is None:
            return { "success": False, "error": "Invalid or unauthorized API key." }
    
        # Check if user has sufficient permissions (assume 'write' or 'admin' privileges required)
        if user_info.get("permissions") not in ["write", "admin"]:
            return { "success": False, "error": "Insufficient permissions to delete WAF rule." }
    
        # Check if rule exists
        if rule_id not in self.waf_rules:
            return { "success": False, "error": "WAF rule does not exist." }
    
        # Delete the rule
        del self.waf_rules[rule_id]
        return { "success": True, "message": f"WAF rule {rule_id} deleted." }

    def create_security_report(
        self, 
        api_user_id: str, 
        generated_time: str, 
        target_scope: str, 
        summary: str, 
        detail: str
    ) -> dict:
        """
        Generate and save a new security report for auditing.

        Args:
            api_user_id (str): The ID of the API user performing the operation (must be authorized).
            generated_time (str): Timestamp of report generation (ISO8601).
            target_scope (str): The scope or target of the security report.
            summary (str): High-level summary of report findings.
            detail (str): Detailed report content.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Security report created with id <report_id>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Only authorized API users may create a report.
            - report_id is auto-generated and unique.
        """
        # Permission check
        user = self.api_users.get(api_user_id)
        if not user:
            return {"success": False, "error": "API user does not exist"}
        permissions = user.get("permissions", "")
        if "admin" not in permissions and "write_report" not in permissions:
            return {"success": False, "error": "Permission denied"}

        # Basic parameter validation
        if not (generated_time and target_scope and summary and detail):
            return {"success": False, "error": "Missing required report fields"}

        # Generate a unique report_id (simple incremental, or UUID)
        report_id = str(uuid.uuid4())
        if report_id in self.security_reports:
            # Extremely unlikely; regenerate if collision
            report_id = str(uuid.uuid4())

        report_info = {
            "report_id": report_id,
            "generated_time": generated_time,
            "target_scope": target_scope,
            "summary": summary,
            "detail": detail
        }

        self.security_reports[report_id] = report_info

        return {
            "success": True,
            "message": f"Security report created with id {report_id}"
        }

    def create_api_user(self, user_id: str, api_key: str, permissions: str, last_accessed: str = "") -> dict:
        """
        Register a new API user (system or human).

        Args:
            user_id (str): Unique user identifier
            api_key (str): Unique API key/token
            permissions (str): Permissions string/level for this user
            last_accessed (str, optional): Timestamp when last used (default: "")

        Returns:
            dict: {
                "success": True,
                "message": "API user created."
            }
            or
            {
                "success": False,
                "error": "user_id/api_key already exists."
            }

        Constraints:
            - user_id must not already exist in self.api_users
            - api_key must be unique among all users
        """
        # Enforce uniqueness of user_id
        if user_id in self.api_users:
            return { "success": False, "error": "user_id already exists." }

        # Enforce uniqueness of api_key
        for user in self.api_users.values():
            if user["api_key"] == api_key:
                return { "success": False, "error": "api_key already exists." }

        # Create the new user
        self.api_users[user_id] = {
            "user_id": user_id,
            "api_key": api_key,
            "permissions": permissions,
            "last_accessed": last_accessed
        }

        return { "success": True, "message": "API user created." }

    def update_api_user_permissions(self, user_id: str, new_permissions: str) -> dict:
        """
        Modify the permissions associated with an API user.

        Args:
            user_id (str): The unique identifier of the API user to update.
            new_permissions (str): The new permissions string to assign.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Permissions updated for API user <user_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Only existing API users can have their permissions modified.
            - The new_permissions argument must be a non-empty string.
        """
        if user_id not in self.api_users:
            return { "success": False, "error": "API user not found." }

        if not isinstance(new_permissions, str) or not new_permissions.strip():
            return { "success": False, "error": "Invalid permissions value." }

        self.api_users[user_id]['permissions'] = new_permissions.strip()
        return { "success": True, "message": f"Permissions updated for API user {user_id}." }

    def deactivate_api_user(self, user_id: str) -> dict:
        """
        Disable (but do not delete) an API user account.

        Args:
            user_id (str): The unique ID of the API user to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "API user <user_id> deactivated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The target user must exist in the system.
            - API user entry must not be deleted. Only their permissions should be changed to indicate deactivation.
            - Repeated deactivation is a no-op (but still returns success).
        """
        if user_id not in self.api_users:
            return {"success": False, "error": f"API user {user_id} does not exist"}

        user_info = self.api_users[user_id]
        if user_info.get("permissions", "") == "deactivated":
            # Already deactivated
            return {"success": True, "message": f"API user {user_id} already deactivated"}

        user_info["permissions"] = "deactivated"
        self.api_users[user_id] = user_info  # update in case not mutable

        return {"success": True, "message": f"API user {user_id} deactivated"}

    def create_session(
        self,
        session_id: str,
        client_ip: str,
        start_time: str,
        end_time: str,
        connection_metadata: str,
        tls_ssl_version: str,
        request_count: int,
        associated_rule_id: str
    ) -> dict:
        """
        Manually add a session with all required fields (typically for simulation/testing/admin use).
        Must record TLS/SSL version if secure.

        Args:
            session_id (str): Unique session identifier.
            client_ip (str): The IP address of the client.
            start_time (str): Session start time (string, e.g., ISO 8601).
            end_time (str): Session end time (string, e.g., ISO 8601).
            connection_metadata (str): Metadata about the connection.
            tls_ssl_version (str): TLS/SSL version used for the session (must not be empty for secure sessions).
            request_count (int): Number of requests in this session.
            associated_rule_id (str): Associated WAF rule ID (should exist in waf_rules).

        Returns:
            dict: {
                "success": True,
                "message": "Session created successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - session_id must be unique.
            - TLS/SSL version must be recorded (not empty).
            - associated_rule_id must exist in waf_rules (if not, return error).
        """
        # Check if the session_id is unique
        if session_id in self.sessions:
            return {"success": False, "error": "Session ID already exists."}

        # Check that associated_rule_id exists
        if associated_rule_id not in self.waf_rules:
            return {
                "success": False,
                "error": f"Associated rule ID '{associated_rule_id}' does not exist."
            }

        # Check that TLS/SSL version is not empty
        if not tls_ssl_version or not isinstance(tls_ssl_version, str):
            return {
                "success": False,
                "error": "TLS/SSL version must be provided and non-empty."
            }

        # Check that required fields are non-empty (client_ip, connection_metadata)
        if not client_ip or not connection_metadata:
            return {"success": False, "error": "Client IP and connection metadata must be provided."}

        try:
            # Build session info
            session: SessionInfo = {
                "session_id": session_id,
                "client_ip": client_ip,
                "start_time": start_time,
                "end_time": end_time,
                "connection_metadata": connection_metadata,
                "tls_ssl_version": tls_ssl_version,
                "request_count": int(request_count),
                "associated_rule_id": associated_rule_id
            }
            self.sessions[session_id] = session
            return {"success": True, "message": "Session created successfully."}
        except Exception as e:
            return {"success": False, "error": f"Internal error: {str(e)}"}


    def end_session(self, session_id: str) -> dict:
        """
        Mark the end_time of a session as the current UTC timestamp (closing the session).
    
        Args:
            session_id (str): The unique identifier of the session to end.
        
        Returns:
            dict: {
                "success": True,
                "message": "Session <session_id> successfully ended"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        
        Constraints:
            - The session_id must exist in the system.
            - The operation is idempotent: multiple calls simply update end_time to latest closure.
            - No log entries are deleted or updated by this operation.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session not found" }
    
        # Set end_time to current UTC time in ISO format
        now = datetime.datetime.utcnow().isoformat() + "Z"
        self.sessions[session_id]['end_time'] = now

        return {
            "success": True,
            "message": f"Session {session_id} successfully ended"
        }


class WAFManagementSystem(BaseEnv):
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

    def get_sessions_by_client_ip(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_client_ip', kwargs)

    def get_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_session_by_id', kwargs)

    def get_tls_ssl_version_for_session(self, **kwargs):
        return self._call_inner_tool('get_tls_ssl_version_for_session', kwargs)

    def get_tls_ssl_versions_by_client_ip(self, **kwargs):
        return self._call_inner_tool('get_tls_ssl_versions_by_client_ip', kwargs)

    def list_api_users(self, **kwargs):
        return self._call_inner_tool('list_api_users', kwargs)

    def get_api_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_api_user_by_id', kwargs)

    def get_waf_rule_by_id(self, **kwargs):
        return self._call_inner_tool('get_waf_rule_by_id', kwargs)

    def list_waf_rules(self, **kwargs):
        return self._call_inner_tool('list_waf_rules', kwargs)

    def get_security_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_security_report_by_id', kwargs)

    def list_security_reports(self, **kwargs):
        return self._call_inner_tool('list_security_reports', kwargs)

    def get_log_entries_by_session_id(self, **kwargs):
        return self._call_inner_tool('get_log_entries_by_session_id', kwargs)

    def get_log_entry_by_id(self, **kwargs):
        return self._call_inner_tool('get_log_entry_by_id', kwargs)

    def list_log_entries_by_event_type(self, **kwargs):
        return self._call_inner_tool('list_log_entries_by_event_type', kwargs)

    def create_waf_rule(self, **kwargs):
        return self._call_inner_tool('create_waf_rule', kwargs)

    def update_waf_rule(self, **kwargs):
        return self._call_inner_tool('update_waf_rule', kwargs)

    def delete_waf_rule(self, **kwargs):
        return self._call_inner_tool('delete_waf_rule', kwargs)

    def create_security_report(self, **kwargs):
        return self._call_inner_tool('create_security_report', kwargs)

    def create_api_user(self, **kwargs):
        return self._call_inner_tool('create_api_user', kwargs)

    def update_api_user_permissions(self, **kwargs):
        return self._call_inner_tool('update_api_user_permissions', kwargs)

    def deactivate_api_user(self, **kwargs):
        return self._call_inner_tool('deactivate_api_user', kwargs)

    def create_session(self, **kwargs):
        return self._call_inner_tool('create_session', kwargs)

    def end_session(self, **kwargs):
        return self._call_inner_tool('end_session', kwargs)
