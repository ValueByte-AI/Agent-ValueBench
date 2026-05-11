# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Dict, Any
from datetime import datetime



class ClientInfo(TypedDict):
    client_id: str
    client_name: str
    client_type: str
    status: str

class SurveyInfo(TypedDict):
    survey_id: str
    target_metric: str
    creation_date: str
    question: str

class SurveyResponseInfo(TypedDict):
    response_id: str
    client_id: str
    respondent_id: str
    timestamp: str
    survey_id: str
    channel: str

class MetricInfo(TypedDict):
    metric_id: str
    response_id: str
    type: str   # e.g., 'NPS', 'CSAT'
    value: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Clients: {client_id: ClientInfo}
        self.clients: Dict[str, ClientInfo] = {}
        # Surveys: {survey_id: SurveyInfo}
        self.surveys: Dict[str, SurveyInfo] = {}
        # Survey Responses: {response_id: SurveyResponseInfo}
        self.survey_responses: Dict[str, SurveyResponseInfo] = {}
        # Metrics: {metric_id: MetricInfo}
        self.metrics: Dict[str, MetricInfo] = {}
        # Optional explicit supported metric types injected from case state.
        self._supported_metric_types_state: List[str] = []

        # Constraints:
        # - Every SurveyResponse must be linked to a valid Client and Survey
        # - Each Metric must be linked to a single SurveyResponse
        # - The metric's type must correspond to a supported/known metric (e.g., NPS)
        # - Timestamps must allow queries by time period (e.g., date ranges)
        # - Data access may be constrained by client-level permissions

    def get_client_by_id(self, client_id: str) -> dict:
        """
        Retrieve client information based on client_id.

        Args:
            client_id (str): The unique identifier of the client.

        Returns:
            dict:
                - On success: { "success": True, "data": ClientInfo }
                - On failure: { "success": False, "error": "Client not found" }

        Constraints:
            - client_id must exist in the client registry (self.clients).
        """
        client = self.clients.get(client_id)
        if client is None:
            return {"success": False, "error": "Client not found"}
        return {"success": True, "data": client}

    def get_client_by_name(self, client_name: str) -> dict:
        """
        Retrieve client information by client_name.

        Args:
            client_name (str): The name of the client to search for.

        Returns:
            dict:
                Success: { "success": True, "data": ClientInfo }
                Failure: { "success": False, "error": str }
        Constraints:
            - Returns the first client whose 'client_name' matches the argument exactly.
            - Returns an error if no such client exists.
        """
        if not client_name or not isinstance(client_name, str):
            return { "success": False, "error": "Invalid client name provided" }

        for client in self.clients.values():
            if client["client_name"] == client_name:
                return { "success": True, "data": client }
        return { "success": False, "error": "No client found with the specified name" }

    def list_all_clients(self) -> dict:
        """
        List all clients registered in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ClientInfo],  # List of all clients, possibly empty
            }
        """
        result = list(self.clients.values())
        return {"success": True, "data": result}

    def list_surveys_by_client(self, client_id: str) -> dict:
        """
        Get all survey definitions (SurveyInfo) associated with the specified client.

        Args:
            client_id (str): The client ID to find associated surveys for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[SurveyInfo]  # List may be empty if client has no surveys.
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g. client does not exist.
                }

        Constraints:
            - client_id must exist in the system.
            - Returns unique surveys for which there is at least one SurveyResponse linked to this client.
        """
        if client_id not in self.clients:
            return {"success": False, "error": "Client does not exist"}

        # Collect survey_ids from survey_responses belonging to the client
        survey_ids = set(
            resp_info["survey_id"]
            for resp_info in self.survey_responses.values()
            if resp_info["client_id"] == client_id
        )

        result = []
        for survey_id in survey_ids:
            survey_info = self.surveys.get(survey_id)
            if survey_info is not None:
                result.append(survey_info)

        return {"success": True, "data": result}

    def get_survey_by_id(self, survey_id: str) -> dict:
        """
        Fetch details of a specific survey given its unique survey_id.

        Args:
            survey_id (str): The unique identifier of the survey.

        Returns:
            dict: {
                "success": True,
                "data": SurveyInfo,   # Survey details if found
            }
            or
            {
                "success": False,
                "error": str         # "Survey not found" if not present
            }

        Constraints:
            - The survey with the given survey_id must exist.
        """
        survey_info = self.surveys.get(survey_id)
        if survey_info is None:
            return { "success": False, "error": "Survey not found" }
        return { "success": True, "data": survey_info }

    def list_survey_responses_by_client(self, client_id: str) -> dict:
        """
        Retrieve all survey responses for the specified client.

        Args:
            client_id (str): The ID of the client whose survey responses are to be retrieved.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[SurveyResponseInfo]  # Empty if none.
                  }
                - On failure: {
                    "success": False,
                    "error": "Client not found"
                  }
        Constraints:
            - client_id must exist in the clients database.
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client not found" }

        responses = [
            sresp for sresp in self.survey_responses.values()
            if sresp["client_id"] == client_id
        ]

        return { "success": True, "data": responses }


    def filter_survey_responses_by_client_and_time(
        self, 
        client_id: str, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """
        Retrieve all survey responses for a client within a specific date/time range.

        Args:
            client_id (str): The unique identifier of the client.
            start_time (str): ISO 8601 datetime string for start (inclusive).
            end_time (str): ISO 8601 datetime string for end (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[SurveyResponseInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - client_id must exist.
            - start_time and end_time must be valid ISO 8601 strings.
            - start_time <= end_time.
        """
        # Check that the client exists
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist" }

        # Parse times
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except Exception:
            return { "success": False, "error": "Invalid date/time format. Must be ISO 8601." }

        if start_dt > end_dt:
            return { "success": False, "error": "start_time must be before or equal to end_time" }

        # Filter responses
        result: List[Dict[str, Any]] = []

        for resp in self.survey_responses.values():
            if resp["client_id"] != client_id:
                continue
            try:
                resp_dt = datetime.fromisoformat(resp["timestamp"].replace('Z', '+00:00'))
            except Exception:
                continue  # skip malformed timestamps
            if start_dt <= resp_dt <= end_dt:
                result.append(resp)

        return { "success": True, "data": result }

    def get_survey_response_by_id(self, response_id: str) -> dict:
        """
        Retrieve details of a survey response given its unique response_id.

        Args:
            response_id (str): The ID of the survey response to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SurveyResponseInfo  # All fields for the response
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Survey response with response_id <id> does not exist."
                    }

        Constraints:
            - response_id must exist in the system.
            - No permission checks are required in this operation.
        """
        response = self.survey_responses.get(response_id)
        if response is None:
            return {
                "success": False,
                "error": f"Survey response with response_id {response_id} does not exist."
            }
        return {"success": True, "data": response}

    def get_metrics_by_response_id(self, response_id: str) -> dict:
        """
        Retrieve all metric records (MetricInfo) linked to a particular survey response.

        Args:
            response_id (str): The ID of the survey response to fetch metrics for.

        Returns:
            dict: 
              If found: {
                  "success": True,
                  "data": List[MetricInfo]  # May be empty list if no metrics for this response
              }
              If the survey response ID is not found: {
                  "success": False,
                  "error": "Survey response not found"
              }

        Constraints:
            - The survey response must exist in the system.
        """
        if response_id not in self.survey_responses:
            return {"success": False, "error": "Survey response not found"}

        data = [
            metric for metric in self.metrics.values()
            if metric["response_id"] == response_id
        ]

        return {"success": True, "data": data}

    def get_metrics_by_type_and_client_and_time(
        self,
        metric_type: str,
        client_id: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """
        Retrieve all metrics of a given type for a specific client within a time range.

        Args:
            metric_type (str): The metric type to filter (e.g., 'NPS').
            client_id (str): The client ID whose metrics to search.
            start_time (str): ISO8601 datetime string, inclusive.
            end_time (str): ISO8601 datetime string, inclusive.

        Returns:
            dict: {
              "success": True,
              "data": List[MetricInfo] (may be empty)
            }
            or
            {
              "success": False,
              "error": str
            }

        Constraints:
            - The client must exist.
            - The metric_type must be a supported metric.
            - Filters by client_id via associated SurveyResponse.
            - Timestamps are filtered as ISO8601 string comparisons.
        """

        # Check that client exists
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist" }

        # Check that metric_type is supported
        supported_types = {metric["type"] for metric in self.metrics.values()}
        if metric_type not in supported_types:
            return { "success": False, "error": f"Metric type '{metric_type}' is not supported" }

        try:
            ts_start = datetime.fromisoformat(start_time)
            ts_end = datetime.fromisoformat(end_time)
        except Exception:
            return { "success": False, "error": "Invalid time format. Use ISO8601 strings." }

        # First, get all survey responses for this client in time range
        # Assume timestamp is also ISO8601 (string comparison would also suffice, but safer to use datetime for inclusivity)
        matched_response_ids = []
        for sr in self.survey_responses.values():
            if sr["client_id"] == client_id:
                try:
                    sr_ts = datetime.fromisoformat(sr["timestamp"])
                except Exception:
                    continue
                if ts_start <= sr_ts <= ts_end:
                    matched_response_ids.append(sr["response_id"])

        # Now, get all metrics matching type and one of these responses
        result = [
            metric for metric in self.metrics.values()
            if metric["type"] == metric_type and metric["response_id"] in matched_response_ids
        ]

        return { "success": True, "data": result }

    def list_supported_metric_types(self) -> dict:
        """
        Returns the list of all currently supported metric types (e.g., NPS, CSAT) found in the system.
    
        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Unique metric type strings, possibly empty if no metrics exist.
            }
        """
        if self._supported_metric_types_state:
            return {
                "success": True,
                "data": sorted(set(self._supported_metric_types_state))
            }

        metric_types = set()
        for metric in self.metrics.values():
            metric_type = metric.get("type")
            if isinstance(metric_type, str):
                metric_types.add(metric_type)
        return {
            "success": True,
            "data": sorted(metric_types)
        }

    def summarize_metrics_by_type_and_client_and_time(
        self,
        client_id: str,
        metric_type: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """
        Aggregate and summarize (average, count) a feedback metric (e.g., NPS) for a specific client
        within a given time range. Only considers metrics linked to the client's survey responses and
        matching the specified metric type. Time comparisons are based on ISO8601 strings.

        Args:
            client_id (str): The client to summarize metrics for.
            metric_type (str): e.g., "NPS", "CSAT" (case-sensitive, must appear in data).
            start_time (str): Start UTC time (inclusive), ISO8601 string.
            end_time (str): End UTC time (inclusive), ISO8601 string.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "client_id": str,
                    "metric_type": str,
                    "count": int,
                    "average": float or None,
                }
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - client_id must exist.
            - metric_type must be a known metric (appear in at least one metric record).
        """

        # Check client existence
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist." }

        # Find if metric_type is known
        metric_types_present = set(m["type"] for m in self.metrics.values())
        if metric_type not in metric_types_present:
            return { "success": False, "error": f"Metric type '{metric_type}' not found." }

        # Find all SurveyResponses for this client in the time window
        responses_in_time = []
        try:
            for resp in self.survey_responses.values():
                if resp["client_id"] != client_id:
                    continue
                if resp["timestamp"] >= start_time and resp["timestamp"] <= end_time:
                    responses_in_time.append(resp["response_id"])
        except Exception:
            return { "success": False, "error": "Error parsing response timestamps." }

        if not responses_in_time:
            return {
                "success": True,
                "data": {
                    "client_id": client_id,
                    "metric_type": metric_type,
                    "count": 0,
                    "average": None
                }
            }

        # For each metric of correct type & on these responses, compute average
        values = [
            m["value"]
            for m in self.metrics.values()
            if m["type"] == metric_type and m["response_id"] in responses_in_time
        ]

        count = len(values)
        avg = sum(values)/count if count > 0 else None

        return {
            "success": True,
            "data": {
                "client_id": client_id,
                "metric_type": metric_type,
                "count": count,
                "average": avg
            }
        }

    def check_client_permissions(self, client_id: str) -> dict:
        """
        Check the permissions and data access rights for a given client.
        Currently, only status is checked, as there is no explicit permissions apparatus modeled.

        Args:
            client_id (str): The ID of the client to check.

        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "data": {
                        "client_id": str,
                        "client_name": str,
                        "client_type": str,
                        "status": str,
                        "permissions_info": str  # Human-readable description
                    }
                }
                On failure: {
                    "success": False,
                    "error": "Client not found"
                }
        Constraints:
            - Client must exist.
            - Permissions modeled only as "status" in this implementation.
        """
        client = self.clients.get(client_id)
        if not client:
            return { "success": False, "error": "Client not found" }

        # Interpret status as permission info if that is all that is available
        status = client.get("status", "unknown")
        if status.lower() == "active":
            permissions_info = "Full access to data and surveys."
        elif status.lower() == "inactive":
            permissions_info = "No data access (inactive client)."
        else:
            permissions_info = f"Access rights depend on client status: {status}."

        return {
            "success": True,
            "data": {
                "client_id": client["client_id"],
                "client_name": client.get("client_name", ""),
                "client_type": client.get("client_type", ""),
                "status": status,
                "permissions_info": permissions_info
            }
        }

    def add_client(
        self,
        client_id: str,
        client_name: str,
        client_type: str,
        status: str
    ) -> dict:
        """
        Create a new client record in the system.

        Args:
            client_id (str): Unique identifier for the client.
            client_name (str): Name of the client.
            client_type (str): Type/category of the client.
            status (str): Status value ('active', 'inactive', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Client <client_id> added."
            }
            or
            dict: {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - client_id must be unique (must not already exist in the system).
            - All fields must be provided and non-empty.
        """
        # Check if client_id is already present
        if not all([client_id, client_name, client_type, status]):
            return {"success": False, "error": "All client fields are required and must be non-empty."}

        if client_id in self.clients:
            return {"success": False, "error": f"Client with id '{client_id}' already exists."}

        client_info: ClientInfo = {
            "client_id": client_id,
            "client_name": client_name,
            "client_type": client_type,
            "status": status
        }
        self.clients[client_id] = client_info

        return {"success": True, "message": f"Client {client_id} added."}

    def update_client_info(
        self,
        client_id: str,
        client_name: str = None,
        client_type: str = None,
        status: str = None
    ) -> dict:
        """
        Modify the details of an existing client (client_name, client_type, status).

        Args:
            client_id (str): Unique identifier for the client to update.
            client_name (str, optional): New client name (if updating).
            client_type (str, optional): New client type (if updating).
            status (str, optional): New status (if updating).

        Returns:
            dict:
                On success: { "success": True, "message": "Client info updated successfully" }
                On failure: { "success": False, "error": <error_message> }

        Constraints:
            - client_id must exist in the system.
            - At least one of client_name, client_type, or status must be provided.
        """
        # Check if client_id exists
        if client_id not in self.clients:
            return { "success": False, "error": "Client not found" }

        # Collect which fields are to be updated
        update_fields = {}
        if client_name is not None:
            update_fields["client_name"] = client_name
        if client_type is not None:
            update_fields["client_type"] = client_type
        if status is not None:
            update_fields["status"] = status

        if not update_fields:
            return { "success": False, "error": "No update fields provided" }

        # Update the client info fields
        for key, value in update_fields.items():
            self.clients[client_id][key] = value

        return { "success": True, "message": "Client info updated successfully" }

    def delete_client(self, client_id: str) -> dict:
        """
        Remove a client record by client_id.

        Args:
            client_id (str): The unique identifier of the client to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str   # Success message
            }
            or
            {
                "success": False,
                "error": str     # Reason for failure
            }

        Constraints:
            - Cannot delete a client if there are associated survey responses (referential integrity).
            - Client must exist.
        """
        # Check if client exists
        if client_id not in self.clients:
            return {"success": False, "error": "Client does not exist"}

        # Check for associated survey responses
        for sr in self.survey_responses.values():
            if sr["client_id"] == client_id:
                return {
                    "success": False,
                    "error": "Client has associated survey responses and cannot be deleted"
                }

        # All checks passed; safe to delete client
        del self.clients[client_id]
        return {"success": True, "message": f"Client {client_id} deleted"}

    def add_survey(self, survey_id: str, target_metric: str, creation_date: str, question: str) -> dict:
        """
        Create a new survey definition.

        Args:
            survey_id (str): Unique identifier for the survey.
            target_metric (str): The feedback metric this survey targets (e.g., 'NPS').
            creation_date (str): ISO-format date string of survey creation.
            question (str): The survey's question.

        Returns:
            dict: {
                "success": True,
                "message": "Survey <survey_id> created."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - survey_id must be unique (not already present in self.surveys)
            - target_metric must be in the supported metric types list
            - All fields are required and must not be empty
        """
        # Check for required fields
        if not all([survey_id, target_metric, creation_date, question]):
            return {"success": False, "error": "All survey fields must be provided and non-empty."}

        # Check survey_id uniqueness
        if survey_id in self.surveys:
            return {"success": False, "error": f"Survey with id '{survey_id}' already exists."}

        # Check supported metric types
        if hasattr(self, "list_supported_metric_types"):
            supported = self.list_supported_metric_types()
            if supported.get("success") and target_metric not in supported["data"]:
                return {"success": False, "error": f"Metric type '{target_metric}' is not supported."}

        # Create and add survey
        survey: SurveyInfo = {
            "survey_id": survey_id,
            "target_metric": target_metric,
            "creation_date": creation_date,
            "question": question,
        }
        self.surveys[survey_id] = survey
        return {"success": True, "message": f"Survey '{survey_id}' created."}

    def update_survey(
        self,
        survey_id: str,
        target_metric: str = None,
        creation_date: str = None,
        question: str = None,
    ) -> dict:
        """
        Modify an existing survey definition. Only provided fields are updated.

        Args:
            survey_id (str): Unique identifier of the survey to update.
            target_metric (str, optional): New target metric (must be supported).
            creation_date (str, optional): New creation date.
            question (str, optional): New survey question.

        Returns:
            dict: {
                "success": True,
                "message": "Survey updated"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - survey_id must exist in the system.
            - If updating target_metric, its type must be among supported metric types.
        """
        if survey_id not in self.surveys:
            return { "success": False, "error": "Survey not found" }

        survey = self.surveys[survey_id]

        # Update fields only if provided
        if target_metric is not None:
            # Check against supported metric types
            supported_types = set(self.list_supported_metric_types().get("data", []))
            if target_metric not in supported_types:
                return { "success": False, "error": "Unsupported target_metric type" }
            survey["target_metric"] = target_metric

        if creation_date is not None:
            survey["creation_date"] = creation_date

        if question is not None:
            survey["question"] = question

        self.surveys[survey_id] = survey  # update the record

        return { "success": True, "message": "Survey updated" }

    def delete_survey(self, survey_id: str) -> dict:
        """
        Remove a survey from the system.

        Args:
            survey_id (str): The ID of the survey to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Survey <survey_id> deleted."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Survey must exist.
            - Survey cannot be deleted if it is referenced by any SurveyResponse (referential integrity).
        """
        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey does not exist"}

        # Check if any SurveyResponse is linked to this survey
        is_referenced = any(
            resp_info["survey_id"] == survey_id
            for resp_info in self.survey_responses.values()
        )
        if is_referenced:
            return {
                "success": False,
                "error": "Survey cannot be deleted: it is referenced by existing survey responses"
            }

        del self.surveys[survey_id]
        return {
            "success": True,
            "message": f"Survey {survey_id} deleted."
        }

    def add_survey_response(
        self,
        response_id: str,
        client_id: str,
        respondent_id: str,
        timestamp: str,
        survey_id: str,
        channel: str
    ) -> dict:
        """
        Add a new survey response, ensuring it links to a valid client and survey.

        Args:
            response_id (str): Unique survey response identifier.
            client_id (str): The client to whom the response belongs; must exist.
            respondent_id (str): Identifier of the responding customer.
            timestamp (str): ISO8601 string when the survey was answered.
            survey_id (str): The survey being answered; must exist.
            channel (str): The channel/context of the response (email, web, phone, etc).

        Returns:
            dict: {
                "success": True,
                "message": "Survey response added successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - response_id must be unique.
            - client_id must exist in self.clients.
            - survey_id must exist in self.surveys.
        """
        if response_id in self.survey_responses:
            return {"success": False, "error": "Survey response ID already exists"}

        if client_id not in self.clients:
            return {"success": False, "error": "Client does not exist"}

        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey does not exist"}

        # Build SurveyResponseInfo
        new_survey_response = {
            "response_id": response_id,
            "client_id": client_id,
            "respondent_id": respondent_id,
            "timestamp": timestamp,
            "survey_id": survey_id,
            "channel": channel
        }
        self.survey_responses[response_id] = new_survey_response

        return {"success": True, "message": "Survey response added successfully"}

    def update_survey_response(
        self,
        response_id: str,
        updates: dict
    ) -> dict:
        """
        Modify details of an existing survey response.

        Args:
            response_id (str): The ID of the survey response to update.
            updates (dict): Dict of fields and their new values. Allowed fields:
                - client_id: str (must exist in clients)
                - respondent_id: str
                - timestamp: str
                - survey_id: str (must exist in surveys)
                - channel: str

        Returns:
            dict: {
                "success": True,
                "message": "Survey response updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - response_id must exist.
            - If client_id is being changed, it must be a valid client.
            - If survey_id is being changed, it must be a valid survey.
            - Only the allowed fields can be updated.
            - Cannot update response_id.
        """
        allowed_fields = {"client_id", "respondent_id", "timestamp", "survey_id", "channel"}
        if response_id not in self.survey_responses:
            return {"success": False, "error": "Survey response does not exist."}
        if not updates:
            return {"success": False, "error": "No fields specified to update."}

        # Check for invalid fields
        invalid_fields = [k for k in updates if k not in allowed_fields]
        if invalid_fields:
            return {"success": False, "error": f"Cannot update fields: {', '.join(invalid_fields)}"}

        # Client ID constraint
        if "client_id" in updates:
            new_client_id = updates["client_id"]
            if new_client_id not in self.clients:
                return {"success": False, "error": "New client_id does not exist."}

        # Survey ID constraint
        if "survey_id" in updates:
            new_survey_id = updates["survey_id"]
            if new_survey_id not in self.surveys:
                return {"success": False, "error": "New survey_id does not exist."}

        # All checks passed; update fields
        for key, value in updates.items():
            self.survey_responses[response_id][key] = value

        return {"success": True, "message": "Survey response updated."}

    def delete_survey_response(self, response_id: str) -> dict:
        """
        Remove a survey response record and all associated metrics.

        Args:
            response_id (str): The ID of the survey response to delete.
    
        Returns:
            dict:
                - On success: {"success": True, "message": "Survey response deleted successfully."}
                - On failure: {"success": False, "error": "Survey response not found."}

        Constraints:
            - Only delete if the survey response exists.
            - Remove all metrics linked to this survey response to maintain database integrity.
        """
        if response_id not in self.survey_responses:
            return {"success": False, "error": "Survey response not found."}
    
        # Delete associated metrics
        metrics_to_delete = [metric_id for metric_id, metric_info in self.metrics.items()
                             if metric_info["response_id"] == response_id]
        for metric_id in metrics_to_delete:
            del self.metrics[metric_id]
    
        # Delete the survey response
        del self.survey_responses[response_id]

        return {"success": True, "message": "Survey response deleted successfully."}

    def add_metric(self, metric_id: str, response_id: str, type: str, value: float) -> dict:
        """
        Add a new metric record to the system, linked to a valid survey response and known/supported metric type.

        Args:
            metric_id (str): Unique identifier for the metric (must be unused).
            response_id (str): The survey response to which this metric belongs (must exist).
            type (str): Type of the metric (e.g., 'NPS', 'CSAT'); must be supported.
            value (float): Value of the metric.

        Returns:
            dict:
              - On success: { "success": True, "message": "Metric added successfully." }
              - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Each metric_id must be unique.
            - response_id must exist.
            - type must be in the supported metric types.
        """

        # Check uniqueness of metric_id
        if metric_id in self.metrics:
            return { "success": False, "error": "Metric ID already exists." }

        # Check that response_id is valid
        if response_id not in self.survey_responses:
            return { "success": False, "error": "Invalid survey response ID." }

        # Determine supported metric types
        # Strategy: gather all unique types from existing metrics, or from surveys' `target_metric`
        supported_types = set()
        for m in self.metrics.values():
            supported_types.add(m["type"])
        for s in self.surveys.values():
            if "target_metric" in s:
                supported_types.add(s["target_metric"])

        # For robustness: if no prior metrics/surveys, assume NPS and CSAT as examples
        if not supported_types:
            supported_types = {"NPS", "CSAT"}

        if type not in supported_types:
            return { "success": False, "error": f"Metric type '{type}' is not supported." }

        # Add metric
        metric_info = {
            "metric_id": metric_id,
            "response_id": response_id,
            "type": type,
            "value": value,
        }
        self.metrics[metric_id] = metric_info

        return { "success": True, "message": "Metric added successfully." }

    def update_metric(
        self,
        metric_id: str,
        type: str = None,
        value: float = None
    ) -> dict:
        """
        Modify a metric's value or type.

        Args:
            metric_id (str): The ID of the metric to update.
            type (str, optional): The new metric type (e.g., "NPS", "CSAT"). 
                If None, type is not changed.
            value (float, optional): The new metric value. 
                If None, value is not changed.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Metric updated." }
              - On failure: { "success": False, "error": "<error message>" }

        Constraints:
            - metric_id must exist in self.metrics.
            - If 'type' is provided, it must be a supported metric type.
            - If 'value' is provided, it must be a float (or convertible to float).
            - At least one of 'type' or 'value' must be provided.
        """
    
        if metric_id not in self.metrics:
            return {"success": False, "error": "Metric does not exist."}

        if type is None and value is None:
            return {"success": False, "error": "No update parameters provided (type and value are both None)."}

        supported_types = set()
        # Try to extract supported types from self.surveys
        for survey in self.surveys.values():
            if "target_metric" in survey:
                supported_types.add(survey["target_metric"])
        # Add hardcoded common types if not present
        if not supported_types:
            supported_types = {"NPS", "CSAT", "CES"}

        metric_info = self.metrics[metric_id]
        updated_fields = []

        if type is not None:
            if type not in supported_types:
                return {"success": False, "error": f"Unsupported metric type '{type}'."}
            metric_info["type"] = type
            updated_fields.append(f"type='{type}'")

        if value is not None:
            try:
                float_value = float(value)
            except (ValueError, TypeError):
                return {"success": False, "error": "Value must be a float."}
            metric_info["value"] = float_value
            updated_fields.append(f"value={float_value}")

        self.metrics[metric_id] = metric_info

        update_desc = ", ".join(updated_fields)
        return {
            "success": True,
            "message": f"Metric '{metric_id}' updated: {update_desc}."
        }

    def delete_metric(self, metric_id: str) -> dict:
        """
        Remove a metric record from the system.

        Args:
            metric_id (str): The unique ID of the metric to remove.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Metric <metric_id> deleted" }
              - On failure: { "success": False, "error": "Metric not found" }

        Constraints:
            - The metric must exist in the system.
            - No cascading deletion; only the metric is removed.
        """
        if not isinstance(metric_id, str) or metric_id not in self.metrics:
            return { "success": False, "error": "Metric not found" }
    
        del self.metrics[metric_id]
        return { "success": True, "message": f"Metric {metric_id} deleted" }


class CustomerExperienceManagementSystem(BaseEnv):
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
            if key == "list_supported_metric_types":
                if isinstance(value, str):
                    env._supported_metric_types_state = [
                        item.strip() for item in value.split(",") if item.strip()
                    ]
                elif isinstance(value, list):
                    env._supported_metric_types_state = [
                        str(item).strip() for item in value if str(item).strip()
                    ]
                else:
                    env._supported_metric_types_state = []
                continue
            if key in {"clients", "survey_responses", "metrics"} and isinstance(value, dict):
                id_field = {
                    "clients": "client_id",
                    "survey_responses": "response_id",
                    "metrics": "metric_id",
                }[key]
                normalized = {}
                for original_key, item in value.items():
                    if isinstance(item, dict):
                        record_id = item.get(id_field)
                        normalized_key = (
                            record_id
                            if isinstance(record_id, str) and record_id
                            else original_key
                        )
                    else:
                        normalized_key = original_key
                    normalized[normalized_key] = copy.deepcopy(item)
                setattr(env, key, normalized)
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

    def get_client_by_id(self, **kwargs):
        return self._call_inner_tool('get_client_by_id', kwargs)

    def get_client_by_name(self, **kwargs):
        return self._call_inner_tool('get_client_by_name', kwargs)

    def list_all_clients(self, **kwargs):
        return self._call_inner_tool('list_all_clients', kwargs)

    def list_surveys_by_client(self, **kwargs):
        return self._call_inner_tool('list_surveys_by_client', kwargs)

    def get_survey_by_id(self, **kwargs):
        return self._call_inner_tool('get_survey_by_id', kwargs)

    def list_survey_responses_by_client(self, **kwargs):
        return self._call_inner_tool('list_survey_responses_by_client', kwargs)

    def filter_survey_responses_by_client_and_time(self, **kwargs):
        return self._call_inner_tool('filter_survey_responses_by_client_and_time', kwargs)

    def get_survey_response_by_id(self, **kwargs):
        return self._call_inner_tool('get_survey_response_by_id', kwargs)

    def get_metrics_by_response_id(self, **kwargs):
        return self._call_inner_tool('get_metrics_by_response_id', kwargs)

    def get_metrics_by_type_and_client_and_time(self, **kwargs):
        return self._call_inner_tool('get_metrics_by_type_and_client_and_time', kwargs)

    def list_supported_metric_types(self, **kwargs):
        return self._call_inner_tool('list_supported_metric_types', kwargs)

    def summarize_metrics_by_type_and_client_and_time(self, **kwargs):
        return self._call_inner_tool('summarize_metrics_by_type_and_client_and_time', kwargs)

    def check_client_permissions(self, **kwargs):
        return self._call_inner_tool('check_client_permissions', kwargs)

    def add_client(self, **kwargs):
        return self._call_inner_tool('add_client', kwargs)

    def update_client_info(self, **kwargs):
        return self._call_inner_tool('update_client_info', kwargs)

    def delete_client(self, **kwargs):
        return self._call_inner_tool('delete_client', kwargs)

    def add_survey(self, **kwargs):
        return self._call_inner_tool('add_survey', kwargs)

    def update_survey(self, **kwargs):
        return self._call_inner_tool('update_survey', kwargs)

    def delete_survey(self, **kwargs):
        return self._call_inner_tool('delete_survey', kwargs)

    def add_survey_response(self, **kwargs):
        return self._call_inner_tool('add_survey_response', kwargs)

    def update_survey_response(self, **kwargs):
        return self._call_inner_tool('update_survey_response', kwargs)

    def delete_survey_response(self, **kwargs):
        return self._call_inner_tool('delete_survey_response', kwargs)

    def add_metric(self, **kwargs):
        return self._call_inner_tool('add_metric', kwargs)

    def update_metric(self, **kwargs):
        return self._call_inner_tool('update_metric', kwargs)

    def delete_metric(self, **kwargs):
        return self._call_inner_tool('delete_metric', kwargs)
