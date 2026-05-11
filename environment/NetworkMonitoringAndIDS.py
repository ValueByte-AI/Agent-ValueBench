# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any



class NetworkSegmentInfo(TypedDict):
    network_id: str
    name: str
    description: str

class ObservedTrafficInfo(TypedDict):
    network_id: str
    timestamp: str
    src_ip: str
    dest_ip: str
    bytes_transferred: int

class AlertRuleInfo(TypedDict):
    rule_id: str
    network_id: str
    traffic_threshold: int
    ip_list: List[str]
    time_window_start: str
    time_window_end: str
    status: str

class SecurityPolicyInfo(TypedDict):
    policy_id: str
    network_id: str
    policy_type: str
    parameters: str
    enabled: str

class AlertInstanceInfo(TypedDict):
    alert_instance_id: str
    rule_id: str
    timestamp_triggered: str
    observed_ip: str
    observed_volume: int
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for Network Monitoring and Intrusion Detection System.
        """

        # Network Segments: {network_id: NetworkSegmentInfo}
        self.network_segments: Dict[str, NetworkSegmentInfo] = {}

        # Observed Traffic: {network_id: List[ObservedTrafficInfo]}
        self.observed_traffic: Dict[str, List[ObservedTrafficInfo]] = {}

        # Alert Rules: {rule_id: AlertRuleInfo}
        self.alert_rules: Dict[str, AlertRuleInfo] = {}

        # Security Policies: {policy_id: SecurityPolicyInfo}
        self.security_policies: Dict[str, SecurityPolicyInfo] = {}

        # Alert Instances: {alert_instance_id: AlertInstanceInfo}
        self.alert_instances: Dict[str, AlertInstanceInfo] = {}

        # Constraints:
        # - AlertRules must reference existing NetworkSegments.
        # - AlertRules cannot overlap with conflicting time windows for same network_id, ip_list, and threshold.
        # - ObservedTraffic records must be available in real time to compare against AlertRules.
        # - AlertInstances are created if and only if observed traffic exceeds thresholds in the rule's window for monitored IPs.
        # - SecurityPolicy enforcement may override or influence AlertRule activations.

    def _parse_iso_timestamp(self, value: str) -> datetime:
        """
        Parse ISO timestamps used by observed traffic and filters.

        Accepts both timezone-aware strings (including trailing 'Z') and naive
        ISO strings. Naive inputs are interpreted as UTC so comparisons remain
        stable instead of failing on naive/aware mismatches.
        """
        if not isinstance(value, str):
            raise ValueError("Timestamp must be a string")
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def get_network_segment(self, network_id: str) -> dict:
        """
        Retrieve details (metadata) of a network segment by network_id.

        Args:
            network_id (str): The unique network identifier.

        Returns:
            dict: {
                "success": True,
                "data": NetworkSegmentInfo
            }
            or
            {
                "success": False,
                "error": str  # If no such network segment exists
            }

        Constraints:
            - The network_id must reference an existing network segment.
        """
        segment = self.network_segments.get(network_id)
        if segment is None:
            return { "success": False, "error": "Network segment not found" }
        return { "success": True, "data": segment }

    def list_network_segments(self) -> dict:
        """
        List all available network segments being monitored.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[NetworkSegmentInfo]
            }
            - On success, returns the list of all NetworkSegmentInfo objects. If no segments, the list is empty.
        """
        segments = list(self.network_segments.values())
        return {"success": True, "data": segments}

    def get_alert_rule(self, rule_id: str) -> dict:
        """
        Retrieve the details of an alert rule given its unique rule_id.

        Args:
            rule_id (str): The unique identifier for the alert rule.

        Returns:
            dict:
                - success: True, data: AlertRuleInfo (if found)
                - success: False, error: "Alert rule not found" (if rule_id does not exist)

        Constraints:
            - rule_id must exist in the alert_rules dictionary.
        """
        alert_rule = self.alert_rules.get(rule_id)
        if alert_rule is None:
            return { "success": False, "error": "Alert rule not found" }
        return { "success": True, "data": alert_rule }

    def list_alert_rules_for_network(self, network_id: str) -> dict:
        """
        List all alert rules configured for the given network segment.

        Args:
            network_id (str): The ID of the network segment.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[AlertRuleInfo],  # a list of the alert rules (empty if none)
                }
                OR
                {
                    "success": False,
                    "error": str  # descriptive error message
                }

        Constraints:
            - The specified network_id must reference an existing network segment.
        """
        if network_id not in self.network_segments:
            return { "success": False, "error": "Network segment does not exist" }

        rules = [rule_info for rule_info in self.alert_rules.values() if rule_info["network_id"] == network_id]

        return { "success": True, "data": rules }

    def check_alert_rule_time_conflict(
        self,
        network_id: str,
        ip_list: list,
        traffic_threshold: int,
        time_window_start: str,
        time_window_end: str
    ) -> dict:
        """
        Determine if a proposed alert rule would overlap/conflict with existing alert rules.

        Args:
            network_id (str): The network segment's ID the rule would reference.
            ip_list (List[str]): The list of IPs this rule monitors.
            traffic_threshold (int): The traffic threshold condition of the proposed rule.
            time_window_start (str): Start time for monitoring window (e.g., "08:00").
            time_window_end (str): End time for monitoring window (e.g., "16:00").

        Returns:
            dict: {
                "success": True,
                "data": {
                    "conflict": Bool,
                    "conflicting_rules": List[AlertRuleInfo] (only if conflict True)
                }
            }
            or
            {
                "success": False,
                "error": str  # error description
            }

        Constraints:
            - AlertRules cannot overlap on (network_id, ip_list intersection, threshold) with time window overlap.
            - network_id must exist.
            - Input validation for parameter types.
        """
        # Validate network_id
        if network_id not in self.network_segments:
            return { "success": False, "error": "Specified network_id does not exist." }

        # Validate ip_list
        if not isinstance(ip_list, list) or not all(isinstance(ip, str) for ip in ip_list):
            return { "success": False, "error": "ip_list must be a list of IP address strings." }

        # Validate time window is well-formed
        if not isinstance(time_window_start, str) or not isinstance(time_window_end, str):
            return { "success": False, "error": "Invalid time_window_start or time_window_end format." }
        if time_window_start >= time_window_end:
            return { "success": False, "error": "time_window_start must be before time_window_end." }

        # Lookup for conflicting rules
        input_ip_set = set(ip_list)
        conflicts = []
        for rule in self.alert_rules.values():
            if rule["network_id"] != network_id:
                continue
            if rule["traffic_threshold"] != traffic_threshold:
                continue
            existing_ip_set = set(rule["ip_list"])
            if not input_ip_set & existing_ip_set:
                continue  # No intersecting IPs
            # Check time window overlap
            existing_start = rule["time_window_start"]
            existing_end = rule["time_window_end"]

            # Windows overlap if start < other_end and end > other_start
            if (time_window_start < existing_end) and (time_window_end > existing_start):
                conflicts.append(rule)

        if conflicts:
            return {
                "success": True,
                "data": {
                    "conflict": True,
                    "conflicting_rules": conflicts
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "conflict": False
                }
            }



    def get_observed_traffic(
        self,
        network_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        ip_list: Optional[List[str]] = None
    ) -> Dict:
        """
        Retrieve observed traffic records for a given network_id, optionally filtered by time window and/or IPs.

        Args:
            network_id (str): The target network segment's ID.
            start_time (str, optional): Lower bound (inclusive) for timestamp, ISO format.
            end_time (str, optional): Upper bound (inclusive) for timestamp, ISO format.
            ip_list (List[str], optional): Matches records where src_ip or dest_ip is any of these IPs.

        Returns:
            dict: {
                "success": True,
                "data": List[ObservedTrafficInfo]  # May be empty if no matches
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - network_id must refer to an existing network segment.
            - If filtering by time, timestamps are compared inclusively.
            - IP filtering matches src_ip OR dest_ip.
        """
        if network_id not in self.network_segments:
            return {"success": False, "error": "Network segment not found"}

        records = self.observed_traffic.get(network_id, [])
        filtered = []

        # Preparse time filters
        try:
            start_dt = self._parse_iso_timestamp(start_time) if start_time else None
            end_dt = self._parse_iso_timestamp(end_time) if end_time else None
        except Exception:
            return {"success": False, "error": "Invalid time window format"}

        for rec in records:
            # Filter by time window if specified
            try:
                rec_time = self._parse_iso_timestamp(rec["timestamp"])
            except Exception:
                return {"success": False, "error": "Invalid time window format"}
            if start_time and rec_time < start_dt:
                continue
            if end_time and rec_time > end_dt:
                continue
            # Filter by IP list if specified
            if ip_list is not None and len(ip_list) > 0:
                if rec["src_ip"] not in ip_list and rec["dest_ip"] not in ip_list:
                    continue
            filtered.append(rec)

        return {"success": True, "data": filtered}

    def list_security_policies_for_network(self, network_id: str) -> dict:
        """
        List all security policies for a given network segment.

        Args:
            network_id (str): The network segment identifier.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[SecurityPolicyInfo],  # List of security policies (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Error message if network not found
                }

        Constraints:
            - network_id must refer to an existing network segment.
        """
        if network_id not in self.network_segments:
            return {"success": False, "error": "Network segment not found"}

        policies = [
            policy for policy in self.security_policies.values()
            if policy["network_id"] == network_id
        ]
        return {"success": True, "data": policies}

    def get_security_policy(self, policy_id: str) -> dict:
        """
        Retrieve the details of a security policy using its unique policy_id.

        Args:
            policy_id (str): The unique identifier of the security policy to retrieve.

        Returns:
            dict:
                - On success: {"success": True, "data": SecurityPolicyInfo}
                - On error:   {"success": False, "error": "Security policy not found"}

        Constraints:
            - The policy_id must exist within the environment's configured security policies.
        """
        policy = self.security_policies.get(policy_id)
        if policy is None:
            return { "success": False, "error": "Security policy not found" }
        return { "success": True, "data": policy }

    def get_alert_instance(self, alert_instance_id: str) -> dict:
        """
        Fetch alert instance details by alert_instance_id.

        Args:
            alert_instance_id (str): Unique identifier for the alert instance.

        Returns:
            dict: {
                "success": True,
                "data": AlertInstanceInfo   # Alert instance details
            }
            or
            {
                "success": False,
                "error": str                # Reason, e.g. alert instance not found
            }

        Constraints:
            - alert_instance_id must exist in self.alert_instances.
        """
        instance = self.alert_instances.get(alert_instance_id)
        if instance is None:
            return { "success": False, "error": "Alert instance not found" }
        return { "success": True, "data": instance }

    def list_alert_instances_for_network(self, network_id: str) -> dict:
        """
        List all alert instances triggered in a given network segment.

        Args:
            network_id (str): Unique identifier for the network segment.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[AlertInstanceInfo]  # May be empty if no alerts
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g. invalid network_id
                    }

        Constraints:
            - network_id must exist in self.network_segments.
            - Only include alert instances where the associated rule's network_id matches the input.
            - Gracefully skip alert instances referencing invalid rule_ids.
        """
        if network_id not in self.network_segments:
            return { "success": False, "error": "Network segment does not exist" }

        result = []
        for alert_instance in self.alert_instances.values():
            rule_id = alert_instance.get("rule_id")
            rule_info = self.alert_rules.get(rule_id)
            if rule_info and rule_info.get("network_id") == network_id:
                result.append(alert_instance)

        return { "success": True, "data": result }


    def create_alert_rule(
        self,
        network_id: str,
        traffic_threshold: int,
        ip_list: List[str],
        time_window_start: str,
        time_window_end: str,
        status: str = "enabled"
    ) -> dict:
        """
        Create a new alert rule for the specified network segment.

        Args:
            network_id (str): The network segment to tie the rule to.
            traffic_threshold (int): The byte threshold for triggering the alert.
            ip_list (List[str]): List of IPs (as strings) this rule monitors.
            time_window_start (str): ISO 8601 datetime for start of rule activity.
            time_window_end (str): ISO 8601 datetime for end of rule activity.
            status (str): (Optional) Status of rule ('enabled' or 'disabled'), defaults to 'enabled'.

        Returns:
            dict:
                On success: {"success": True, "message": "Alert rule created", "rule_id": <str>}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - The network_id must exist.
            - The rule must not conflict (overlap in time window) with an existing rule on this network with the same ip_list and threshold.
            - The time window must be valid (start < end).
        """
        # Check network_id validity
        if network_id not in self.network_segments:
            return {"success": False, "error": "Network segment does not exist"}

        # Validate ip_list
        if not isinstance(ip_list, list) or not ip_list:
            return {"success": False, "error": "IP list must be a non-empty list"}

        # Validate time window
        if time_window_start >= time_window_end:
            return {"success": False, "error": "Invalid time window: start must be before end"}

        # Check for conflicts with existing rules
        for rule in self.alert_rules.values():
            if (
                rule["network_id"] == network_id and
                rule["traffic_threshold"] == traffic_threshold and
                set(rule["ip_list"]) == set(ip_list)
            ):
                # Time window overlap: (start1 < end2) and (start2 < end1)
                if (time_window_start < rule["time_window_end"] and
                    rule["time_window_start"] < time_window_end):
                    return {"success": False, "error": "Conflicting alert rule time window for these parameters"}

        # Generate unique rule_id
        rule_id = str(uuid.uuid4())

        self.alert_rules[rule_id] = {
            "rule_id": rule_id,
            "network_id": network_id,
            "traffic_threshold": traffic_threshold,
            "ip_list": list(ip_list),
            "time_window_start": time_window_start,
            "time_window_end": time_window_end,
            "status": status
        }

        return {
            "success": True,
            "message": f"Alert rule created with id {rule_id}",
            "rule_id": rule_id
        }

    def update_alert_rule(
        self,
        rule_id: str,
        traffic_threshold: int = None,
        ip_list: List[str] = None,
        time_window_start: str = None,
        time_window_end: str = None,
        status: str = None,
        network_id: str = None
    ) -> dict:
        """
        Modify an existing alert rule configuration.

        Args:
            rule_id (str): The alert rule to update.
            traffic_threshold (int, optional): New threshold for triggering alert.
            ip_list (List[str], optional): New monitored IPs.
            time_window_start (str, optional): New time window start (format: e.g., "HH:MM").
            time_window_end (str, optional): New time window end (format: e.g., "HH:MM").
            status (str, optional): New rule status.
            network_id (str, optional): New network segment id.

        Returns:
            dict:
                - On success: {"success": True, "message": "Alert rule updated successfully."}
                - On failure: {"success": False, "error": "reason"}
    
        Constraints:
            - rule_id must exist.
            - If network_id is updated, it must exist in the system.
            - Cannot introduce time window/IP/threshold conflicts for same network.
        """
        # Check if rule exists
        if rule_id not in self.alert_rules:
            return {"success": False, "error": "Alert rule does not exist."}

        rule = self.alert_rules[rule_id]
        changed = False

        # Validate network_id if updating
        if network_id is not None and network_id != rule["network_id"]:
            if network_id not in self.network_segments:
                return {"success": False, "error": "Referenced network_id does not exist."}
            rule["network_id"] = network_id
            changed = True

        # Update fields if provided
        if traffic_threshold is not None and traffic_threshold != rule["traffic_threshold"]:
            rule["traffic_threshold"] = traffic_threshold
            changed = True

        if ip_list is not None and ip_list != rule["ip_list"]:
            rule["ip_list"] = ip_list
            changed = True

        if time_window_start is not None and time_window_start != rule["time_window_start"]:
            rule["time_window_start"] = time_window_start
            changed = True

        if time_window_end is not None and time_window_end != rule["time_window_end"]:
            rule["time_window_end"] = time_window_end
            changed = True

        if status is not None and status != rule["status"]:
            rule["status"] = status
            changed = True

        # Constraint: Check for time window/IP/threshold conflicts in same network
        if changed:
            for other_rule_id, other_rule in self.alert_rules.items():
                if other_rule_id == rule_id:
                    continue
                if rule["network_id"] == other_rule["network_id"]:
                    # If IP lists intersect, AND time windows overlap, AND threshold possibly same/conflicting:
                    ip_intersection = set(rule["ip_list"]) & set(other_rule["ip_list"])
                    threshold_match = rule["traffic_threshold"] == other_rule["traffic_threshold"]

                    # Time window overlap: assume windows strip format "HH:MM" or ISO date/time.
                    def window_overlap(start1, end1, start2, end2):
                        return not (end1 <= start2 or start1 >= end2)

                    try:
                        s1 = rule["time_window_start"]
                        e1 = rule["time_window_end"]
                        s2 = other_rule["time_window_start"]
                        e2 = other_rule["time_window_end"]
                    except Exception:
                        return {"success": False, "error": "Invalid time window format."}

                    if ip_intersection and threshold_match and window_overlap(s1, e1, s2, e2):
                        return {
                            "success": False,
                            "error": (
                                "Conflicting alert rule found (IP/time window/threshold overlap) "
                                f"with rule_id {other_rule_id}."
                            )
                        }

            # Apply the update
            self.alert_rules[rule_id] = rule

            return {"success": True, "message": "Alert rule updated successfully."}

        return {"success": True, "message": "No changes applied; alert rule unchanged."}

    def delete_alert_rule(self, rule_id: str) -> dict:
        """
        Remove an existing alert rule from the system.

        Args:
            rule_id (str): The unique identifier of the alert rule to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Alert rule <rule_id> deleted" }
                - On failure: { "success": False, "error": "Alert rule <rule_id> does not exist" }

        Constraints:
            - The alert rule must exist in self.alert_rules to be deleted.
            - Related AlertInstance objects (if any) are not deleted or modified.
        """
        if rule_id not in self.alert_rules:
            return { "success": False, "error": f"Alert rule {rule_id} does not exist" }

        del self.alert_rules[rule_id]
        # Note: Related alert instances, if any, are not removed.

        return { "success": True, "message": f"Alert rule {rule_id} deleted" }

    def enable_alert_rule(self, rule_id: str) -> dict:
        """
        Enable (activate) a currently disabled alert rule.

        Args:
            rule_id (str): The ID of the alert rule to enable.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., rule not found, conflicting, network segment missing)
            }

        Constraints:
            - Rule must exist.
            - Rule's referenced network_id must exist in network segments.
            - Rule status will be set to "enabled".
            - If already enabled, return success with a message.

        """
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return {"success": False, "error": f"Alert rule {rule_id} does not exist."}

        network_id = rule["network_id"]
        if network_id not in self.network_segments:
            return {"success": False, "error": f"Network segment {network_id} does not exist for this rule."}

        if rule["status"] == "enabled":
            return {"success": True, "message": f"Alert rule {rule_id} is already enabled."}

        rule["status"] = "enabled"
        self.alert_rules[rule_id] = rule  # Update the rule in storage
        return {"success": True, "message": f"Alert rule {rule_id} enabled."}

    def disable_alert_rule(self, rule_id: str) -> dict:
        """
        Disable (deactivate) a currently enabled alert rule.

        Args:
            rule_id (str): The ID of the alert rule to disable.

        Returns:
            dict: 
                - { "success": True, "message": "Alert rule <rule_id> disabled." }
                - { "success": False, "error": <error reason> }
    
        Constraints:
            - The alert rule must exist.
            - The rule must currently be enabled.
        """
        rule = self.alert_rules.get(rule_id)
        if rule is None:
            return { "success": False, "error": f"Alert rule '{rule_id}' does not exist." }
        if rule["status"].lower() in ("disabled", "inactive"):
            return { "success": False, "error": f"Alert rule '{rule_id}' is already disabled." }
    
        rule["status"] = "disabled"
        self.alert_rules[rule_id] = rule
        return { "success": True, "message": f"Alert rule '{rule_id}' disabled." }

    def create_security_policy(
        self, 
        policy_id: str,
        network_id: str,
        policy_type: str,
        parameters: str,
        enabled: str
    ) -> dict:
        """
        Add a new security policy for a network segment.

        Args:
            policy_id (str): Unique identifier for the new policy.
            network_id (str): The ID of the network segment this policy applies to.
            policy_type (str): The type/category of this policy (e.g., firewall, access).
            parameters (str): Policy configuration or parameters.
            enabled (str): Activation status ("true"/"false" or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Security policy created for network segment <network_id>."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The `policy_id` must not already be present (unique).
            - The `network_id` must refer to an existing segment.
        """
        if policy_id in self.security_policies:
            return { "success": False, "error": "Policy ID already exists." }

        if network_id not in self.network_segments:
            return { "success": False, "error": "Network segment does not exist." }

        new_policy = {
            "policy_id": policy_id,
            "network_id": network_id,
            "policy_type": policy_type,
            "parameters": parameters,
            "enabled": enabled
        }

        self.security_policies[policy_id] = new_policy

        return {
            "success": True,
            "message": f"Security policy created for network segment {network_id}."
        }

    def update_security_policy(
        self,
        policy_id: str,
        policy_type: str = None,
        parameters: str = None,
        enabled: str = None
    ) -> dict:
        """
        Modify parameters or status of an existing security policy. Only supplied fields are updated.

        Args:
            policy_id (str): The unique ID of the security policy to update.
            policy_type (str, optional): New policy type (e.g., 'firewall', 'anomaly_detection'). If None, not changed.
            parameters (str, optional): New parameters string. If None, not changed.
            enabled (str, optional): New enabled status ('true'/'false' or similar). If None, not changed.

        Returns:
            dict:
                - On success: { "success": True, "message": "Security policy updated successfully." }
                - On failure (not found): { "success": False, "error": "Security policy not found." }
                - On failure (no update fields): { "success": False, "error": "No update parameters provided." }

        Constraints:
            - Only updates existing policies.
            - At least one field to update must be provided.
        """
        if policy_id not in self.security_policies:
            return {"success": False, "error": "Security policy not found."}

        update_fields = {}
        if policy_type is not None:
            update_fields["policy_type"] = policy_type
        if parameters is not None:
            update_fields["parameters"] = parameters
        if enabled is not None:
            update_fields["enabled"] = enabled

        if not update_fields:
            return {"success": False, "error": "No update parameters provided."}

        for k, v in update_fields.items():
            self.security_policies[policy_id][k] = v

        return {"success": True, "message": "Security policy updated successfully."}

    def delete_security_policy(self, policy_id: str) -> dict:
        """
        Remove a security policy from the system.

        Args:
            policy_id (str): The unique identifier for the policy to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Security policy <policy_id> deleted." }
                - On failure: { "success": False, "error": "Policy does not exist." }

        Constraints:
            - Policy must exist in the system to be deleted.
        """
        if policy_id not in self.security_policies:
            return { "success": False, "error": "Policy does not exist." }
    
        del self.security_policies[policy_id]
        return { "success": True, "message": f"Security policy {policy_id} deleted." }

    def add_network_segment(self, network_id: str, name: str, description: str) -> dict:
        """
        Add a new network segment to the monitored environment.

        Args:
            network_id (str): Unique identifier for the new segment.
            name (str): Human-readable name for the network segment.
            description (str): Description of the network segment.

        Returns:
            dict: {
                "success": True,
                "message": "Network segment <network_id> added."
            }
            or
            {
                "success": False,
                "error": <error description>
            }

        Constraints:
            - network_id must be unique.
            - name and description must not be empty.
        """
        # Check input validity
        if not network_id or not name:
            return {"success": False, "error": "Network ID and name are required."}
        if network_id in self.network_segments:
            return {"success": False, "error": "Network segment with this ID already exists."}
    
        # Add the network segment
        self.network_segments[network_id] = {
            "network_id": network_id,
            "name": name,
            "description": description
        }

        return {"success": True, "message": f"Network segment {network_id} added."}

    def edit_network_segment(self, network_id: str, name: str = None, description: str = None) -> dict:
        """
        Update details of an existing network segment.

        Args:
            network_id (str): Identifier of the network segment to update.
            name (str, optional): New name for the network segment.
            description (str, optional): New description for the network segment.

        Returns:
            dict:
                - {"success": True, "message": "Network segment updated successfully."}
                - {"success": False, "error": "...reason..."}

        Constraints:
            - The network_id must exist.
            - At least one of 'name' or 'description' must be provided to update.
            - Only 'name' and 'description' fields are updatable.
        """
        if network_id not in self.network_segments:
            return {"success": False, "error": "Network segment does not exist."}
        if name is None and description is None:
            return {"success": False, "error": "No update fields provided. Specify 'name' and/or 'description'."}

        current_info = self.network_segments[network_id].copy()  # type: ignore

        if name is not None:
            current_info["name"] = name
        if description is not None:
            current_info["description"] = description

        self.network_segments[network_id] = current_info

        return {"success": True, "message": "Network segment updated successfully."}

    def remove_network_segment(self, network_id: str) -> dict:
        """
        Remove a network segment from monitoring, including cleanup of:
            - All associated alert rules (and their alert instances)
            - All associated security policies
            - Observed traffic records for the segment

        Args:
            network_id (str): The ID of the network segment to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Network segment <id> and related rules/policies removed",
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The network segment must exist.
            - All related AlertRules and SecurityPolicies must be deleted.
            - AlertInstances linked to removed rules must be deleted.
            - All ObservedTraffic records for the segment must be deleted.
        """
        if network_id not in self.network_segments:
            return { "success": False, "error": "Network segment does not exist" }

        # Remove related alert rules and their alert instances
        removed_rule_ids = [rule_id for rule_id, rule in self.alert_rules.items() if rule['network_id'] == network_id]
        for rule_id in removed_rule_ids:
            # Remove related alert instances for this rule
            to_remove_alert_instance_ids = [
                aid for aid, ai in self.alert_instances.items()
                if ai['rule_id'] == rule_id
            ]
            for aid in to_remove_alert_instance_ids:
                del self.alert_instances[aid]
            # Remove the rule
            del self.alert_rules[rule_id]

        # Remove related security policies
        removed_policy_ids = [policy_id for policy_id, policy in self.security_policies.items() if policy['network_id'] == network_id]
        for policy_id in removed_policy_ids:
            del self.security_policies[policy_id]

        # Remove observed traffic records
        if network_id in self.observed_traffic:
            del self.observed_traffic[network_id]

        # Remove the network segment itself
        del self.network_segments[network_id]

        return {
            "success": True,
            "message": f"Network segment {network_id} and related rules/policies removed"
        }


class NetworkMonitoringAndIDS(BaseEnv):
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

    def get_network_segment(self, **kwargs):
        return self._call_inner_tool('get_network_segment', kwargs)

    def list_network_segments(self, **kwargs):
        return self._call_inner_tool('list_network_segments', kwargs)

    def get_alert_rule(self, **kwargs):
        return self._call_inner_tool('get_alert_rule', kwargs)

    def list_alert_rules_for_network(self, **kwargs):
        return self._call_inner_tool('list_alert_rules_for_network', kwargs)

    def check_alert_rule_time_conflict(self, **kwargs):
        return self._call_inner_tool('check_alert_rule_time_conflict', kwargs)

    def get_observed_traffic(self, **kwargs):
        return self._call_inner_tool('get_observed_traffic', kwargs)

    def list_security_policies_for_network(self, **kwargs):
        return self._call_inner_tool('list_security_policies_for_network', kwargs)

    def get_security_policy(self, **kwargs):
        return self._call_inner_tool('get_security_policy', kwargs)

    def get_alert_instance(self, **kwargs):
        return self._call_inner_tool('get_alert_instance', kwargs)

    def list_alert_instances_for_network(self, **kwargs):
        return self._call_inner_tool('list_alert_instances_for_network', kwargs)

    def create_alert_rule(self, **kwargs):
        return self._call_inner_tool('create_alert_rule', kwargs)

    def update_alert_rule(self, **kwargs):
        return self._call_inner_tool('update_alert_rule', kwargs)

    def delete_alert_rule(self, **kwargs):
        return self._call_inner_tool('delete_alert_rule', kwargs)

    def enable_alert_rule(self, **kwargs):
        return self._call_inner_tool('enable_alert_rule', kwargs)

    def disable_alert_rule(self, **kwargs):
        return self._call_inner_tool('disable_alert_rule', kwargs)

    def create_security_policy(self, **kwargs):
        return self._call_inner_tool('create_security_policy', kwargs)

    def update_security_policy(self, **kwargs):
        return self._call_inner_tool('update_security_policy', kwargs)

    def delete_security_policy(self, **kwargs):
        return self._call_inner_tool('delete_security_policy', kwargs)

    def add_network_segment(self, **kwargs):
        return self._call_inner_tool('add_network_segment', kwargs)

    def edit_network_segment(self, **kwargs):
        return self._call_inner_tool('edit_network_segment', kwargs)

    def remove_network_segment(self, **kwargs):
        return self._call_inner_tool('remove_network_segment', kwargs)
