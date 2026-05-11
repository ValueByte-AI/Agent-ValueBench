# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class OrganizationInfo(TypedDict):
    organization_id: str
    name: str
    business_un: str

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    organization_id: str
    email: str

class SurveyInfo(TypedDict):
    survey_id: str
    title: str
    question_set: List[Any]
    active_period: str  # could be more structured
    associated_organization_id: str

class SurveyResponseInfo(TypedDict):
    response_id: str
    customer_id: str
    organization_id: str
    survey_date: str
    answers: Any  # Could be Dict[str, Any] or List[Any], left generic here
    nps_score: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for Customer Feedback Management System.
        """

        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Surveys: {survey_id: SurveyInfo}
        self.surveys: Dict[str, SurveyInfo] = {}

        # SurveyResponses: {response_id: SurveyResponseInfo}
        self.survey_responses: Dict[str, SurveyResponseInfo] = {}

        # Constraints:
        # - Each SurveyResponse must be associated with a valid customer and organization.
        # - NPS calculation uses the standardized methodology (promoters, detractors, passives per organization/survey).
        # - Customers can have multiple SurveyResponses (possibly for different surveys).
        # - Organizations can aggregate survey responses from all their customers.

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve organization info (name, business unit, etc) for the specified organization_id.

        Args:
            organization_id (str): The unique organization identifier.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": OrganizationInfo  # Includes organization_id, name, business_un
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason such as "Organization not found"
                }

        Constraints:
            - organization_id must exist in the organizations registry.
        """
        org = self.organizations.get(organization_id)
        if org is None:
            return {"success": False, "error": "Organization not found"}
        return {"success": True, "data": org}

    def list_customers_by_organization(self, organization_id: str) -> dict:
        """
        Return a list of all CustomerInfo objects associated with a given organization_id.

        Args:
            organization_id (str): The ID of the organization whose customers you want to fetch.

        Returns:
            dict:
              - On success:
                  {
                    "success": True,
                    "data": List[CustomerInfo]  # List may be empty
                  }
              - On failure (organization does not exist):
                  {
                    "success": False,
                    "error": "Organization does not exist"
                  }

        Constraints:
            - The organization_id must exist.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        customer_list = [
            customer_info for customer_info in self.customers.values()
            if customer_info["organization_id"] == organization_id
        ]

        return { "success": True, "data": customer_list }

    def list_surveys_by_organization(self, organization_id: str) -> dict:
        """
        Return all SurveyInfo records for surveys sent to or associated with the organization.

        Args:
            organization_id (str): The organization identifier.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": List[SurveyInfo]   # List of matching surveys (possibly empty)
                }
                On failure,
                {
                    "success": False,
                    "error": str  # Reason, e.g., organization not found
                }

        Constraints:
            - The organization must exist.
            - Only surveys where associated_organization_id == organization_id are returned.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization not found" }
    
        surveys = [
            survey_info
            for survey_info in self.surveys.values()
            if survey_info["associated_organization_id"] == organization_id
        ]
        return { "success": True, "data": surveys }

    def list_survey_responses_by_organization(self, organization_id: str) -> dict:
        """
        Retrieve all SurveyResponseInfo entries where organization_id matches the given value.

        Args:
            organization_id (str): The ID of the organization whose responses are to be listed.

        Returns:
            dict:
                - success: True and data (List[SurveyResponseInfo]) if organization is found.
                - success: False and error (str) if organization does not exist.

        Constraints:
            - The organization_id must refer to an existing organization.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        result = [
            response for response in self.survey_responses.values()
            if response["organization_id"] == organization_id
        ]

        return { "success": True, "data": result }

    def list_survey_responses_by_customer(self, customer_id: str) -> dict:
        """
        Retrieve all SurveyResponseInfo records submitted by the specified customer.

        Args:
            customer_id (str): The ID of the customer.

        Returns:
            dict: {
                "success": True,
                "data": List[SurveyResponseInfo]  # List of survey responses by the customer, could be empty
            }
            or
            {
                "success": False,
                "error": str  # If the customer does not exist
            }

        Constraints:
            - The customer_id must exist in the system.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist" }
    
        responses = [
            response for response in self.survey_responses.values()
            if response["customer_id"] == customer_id
        ]
        return { "success": True, "data": responses }

    def get_survey_response_by_id(self, response_id: str) -> dict:
        """
        Retrieve details of a survey response by its response_id.

        Args:
            response_id (str): The unique ID of the survey response to fetch.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SurveyResponseInfo  # All fields for the response
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # error message if not found
                    }
        Constraints:
            - The response_id must exist in the system.
        """
        if response_id not in self.survey_responses:
            return { "success": False, "error": "Survey response not found" }
        return { "success": True, "data": self.survey_responses[response_id] }

    def calculate_nps_for_organization(self, organization_id: str) -> dict:
        """
        Aggregate all survey responses for the specified organization and compute the NPS
        (Net Promoter Score) using the standard methodology:
          - Promoters: nps_score >= 9
          - Detractors: nps_score <= 6
          - Passives: nps_score in [7, 8]

        NPS = (% Promoters - % Detractors), percentages are of total responses.

        Args:
            organization_id (str): The ID of the organization to aggregate responses for.

        Returns:
            dict: Success: {
                      "success": True,
                      "data": {
                          "organization_id": ...,
                          "nps": float or None,
                          "counts": {"promoters": int, "detractors": int, "passives": int, "total": int}
                      }
                  }
                  Failure: {
                      "success": False,
                      "error": "Organization does not exist"
                  }

        Constraints:
            - Organization must exist.
            - If no responses exist for the organization, "nps" will be None and counts will be zero.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist"}

        responses = [
            resp for resp in self.survey_responses.values()
            if resp["organization_id"] == organization_id
        ]
        total = len(responses)
        promoters = detractors = passives = 0

        for resp in responses:
            score = resp.get("nps_score", None)
            if score is None:
                continue
            if score >= 9:
                promoters += 1
            elif score <= 6:
                detractors += 1
            elif score in (7, 8):
                passives += 1

        if total == 0:
            nps = None
        else:
            promoters_pct = (promoters / total) * 100
            detractors_pct = (detractors / total) * 100
            nps = promoters_pct - detractors_pct

        result = {
            "organization_id": organization_id,
            "nps": nps,
            "counts": {
                "promoters": promoters,
                "detractors": detractors,
                "passives": passives,
                "total": total
            }
        }
        return {"success": True, "data": result}

    def calculate_nps_for_organization_by_survey(self, organization_id: str) -> dict:
        """
        Computes the Net Promoter Score (NPS) for the given organization, broken down by each survey.
        For each survey sent by the organization, computes NPS using the following:
          - Promoters: nps_score >= 9
          - Passives: nps_score in [7, 8]
          - Detractors: nps_score <= 6
        NPS = 100*(Promoters-Detractors)/Total respondents

        Args:
            organization_id (str): Target organization.

        Returns:
            dict:
                {
                    "success": True,
                    "data": {
                        survey_id: {
                            "survey_title": str,
                            "num_promoters": int,
                            "num_passives": int,
                            "num_detractors": int,
                            "nps": float or None,  # None if no responses
                            "num_responses": int
                        },
                        ...
                    }
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Organization must exist.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist." }

        # Collect all surveys for the organization
        org_surveys = {
            survey_id: survey for survey_id, survey in self.surveys.items()
            if survey["associated_organization_id"] == organization_id
        }

        result = {}

        # For each survey, collect responses and calculate NPS
        for survey_id, survey in org_surveys.items():
            responses = [
                resp for resp in self.survey_responses.values()
                if resp["organization_id"] == organization_id 
                and resp.get("survey_id") == survey_id
            ]

            num_promoters = sum(1 for r in responses if r["nps_score"] >= 9)
            num_passives  = sum(1 for r in responses if 7 <= r["nps_score"] <= 8)
            num_detractors= sum(1 for r in responses if r["nps_score"] <= 6)
            num_responses = len(responses)

            if num_responses == 0:
                nps = None
            else:
                nps = 100.0 * (num_promoters - num_detractors) / num_responses

            result[survey_id] = {
                "survey_title": survey["title"],
                "num_promoters": num_promoters,
                "num_passives": num_passives,
                "num_detractors": num_detractors,
                "nps": nps,
                "num_responses": num_responses
            }

        return { "success": True, "data": result }

    def get_survey_by_id(self, survey_id: str) -> dict:
        """
        Retrieve SurveyInfo for the given survey_id.

        Args:
            survey_id (str): Unique identifier of the survey.

        Returns:
            dict: {
                "success": True,
                "data": SurveyInfo
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - survey_id must exist in the system.
        """
        if survey_id not in self.surveys:
            return { "success": False, "error": "Survey not found" }

        return { "success": True, "data": self.surveys[survey_id] }

    def add_survey_response(self, survey_response: SurveyResponseInfo) -> dict:
        """
        Store a new SurveyResponseInfo object after validating customer and organization linkage.

        Args:
            survey_response (SurveyResponseInfo): The survey response data to add.

        Returns:
            dict: {
                "success": True,
                "message": "Survey response added"
            }
            or
            {
                "success": False,
                "error": Reason for failure
            }

        Constraints:
            - response_id must be unique.
            - customer_id must exist.
            - organization_id must exist.
            - The customer’s organization_id must match the response’s organization_id.
        """
        required_fields = [
            "response_id", "customer_id", "organization_id",
            "survey_date", "answers", "nps_score"
        ]
        # Check for missing fields
        for field in required_fields:
            if field not in survey_response:
                return {"success": False, "error": f"Missing field: {field}"}

        response_id = survey_response["response_id"]
        customer_id = survey_response["customer_id"]
        organization_id = survey_response["organization_id"]

        # Check duplicate response_id
        if response_id in self.survey_responses:
            return { "success": False, "error": "response_id already exists" }

        # Check organization exists
        if organization_id not in self.organizations:
            return { "success": False, "error": "organization_id does not exist" }

        # Check customer exists
        if customer_id not in self.customers:
            return { "success": False, "error": "customer_id does not exist" }

        # Check customer's organization_id matches
        customer_info = self.customers[customer_id]
        if customer_info["organization_id"] != organization_id:
            return { "success": False, "error": "customer does not belong to the given organization" }

        # All checks passed, add the survey response
        self.survey_responses[response_id] = survey_response

        return { "success": True, "message": "Survey response added" }

    def update_survey_response(
        self,
        response_id: str,
        answers: Any = None,
        nps_score: float = None,
        survey_date: str = None,
        customer_id: str = None,
        organization_id: str = None
    ) -> dict:
        """
        Modify answers, NPS score, or metadata for an existing SurveyResponseInfo entry.

        Args:
            response_id (str): The ID of the survey response to update.
            answers (Any, optional): The new answers.
            nps_score (float, optional): The new NPS score.
            survey_date (str, optional): The new survey date.
            customer_id (str, optional): The (possibly new) customer ID (must exist).
            organization_id (str, optional): The (possibly new) org ID (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "SurveyResponse updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - response_id must exist.
            - New customer_id/org_id must refer to existing entries if updated.
            - Each SurveyResponse must be associated with a valid customer and org.
        """
        # Check if the survey response exists
        if response_id not in self.survey_responses:
            return {"success": False, "error": "Survey response does not exist"}

        sr = self.survey_responses[response_id]
        # Validate if updating customer_id
        if customer_id is not None:
            if customer_id not in self.customers:
                return {"success": False, "error": "Customer does not exist"}
            sr["customer_id"] = customer_id
        # Validate if updating organization_id
        if organization_id is not None:
            if organization_id not in self.organizations:
                return {"success": False, "error": "Organization does not exist"}
            sr["organization_id"] = organization_id
        # Update other fields if provided
        if answers is not None:
            sr["answers"] = answers
        if nps_score is not None:
            sr["nps_score"] = nps_score
        if survey_date is not None:
            sr["survey_date"] = survey_date

        # Final constraint: still has valid customer/org after changes
        if sr["customer_id"] not in self.customers:
            return {"success": False, "error": "SurveyResponse has invalid customer after update"}
        if sr["organization_id"] not in self.organizations:
            return {"success": False, "error": "SurveyResponse has invalid organization after update"}

        # Update done
        return {"success": True, "message": "SurveyResponse updated successfully"}

    def delete_survey_response(self, response_id: str) -> dict:
        """
        Remove a survey response record from the system (administrative action).

        Args:
            response_id (str): The identifier of the survey response to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Survey response <response_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Survey response not found."
            }

        Constraints:
            - The response_id must exist in self.survey_responses.
            - This is an administrative operation; no permission checks are modeled.
        """
        if response_id not in self.survey_responses:
            return { "success": False, "error": "Survey response not found." }
    
        del self.survey_responses[response_id]
        return { "success": True, "message": f"Survey response {response_id} deleted." }

    def add_customer(
        self,
        customer_id: str,
        name: str,
        organization_id: str,
        email: str
    ) -> dict:
        """
        Create a new customer record for association with organizations and survey participation.

        Args:
            customer_id (str): Unique identifier for the customer.
            name (str): Name of the customer.
            organization_id (str): ID of the organization with which the customer is associated.
            email (str): Email address of the customer.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Customer <customer_id> added successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error message>
                    }

        Constraints:
            - The organization specified by organization_id must exist.
            - The customer_id must be unique within the system.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist."}

        if customer_id in self.customers:
            return {"success": False, "error": "Customer ID already exists."}

        customer_info: CustomerInfo = {
            "customer_id": customer_id,
            "name": name,
            "organization_id": organization_id,
            "email": email
        }
        self.customers[customer_id] = customer_info

        return {
            "success": True,
            "message": f"Customer {customer_id} added successfully."
        }

    def update_customer(
        self,
        customer_id: str,
        name: str = None,
        email: str = None,
        organization_id: str = None
    ) -> dict:
        """
        Update customer attributes (name, email, organization_id).

        Args:
            customer_id (str): The ID of the customer to update.
            name (str, optional): New name for the customer.
            email (str, optional): New email address.
            organization_id (str, optional): New organization ID (must exist).

        Returns:
            dict: Success or failure message, e.g.:
                { "success": True, "message": "Customer updated successfully" }
                { "success": False, "error": "<reason>" }

        Constraints:
            - customer_id must exist in the system.
            - If organization_id is given, it must exist.
            - At least one updatable attribute must be provided.
            - Only name/email/organization_id can be updated.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer not found" }

        update_fields = {}
    
        if name is not None:
            update_fields['name'] = name
        if email is not None:
            update_fields['email'] = email
        if organization_id is not None:
            if organization_id not in self.organizations:
                return { "success": False, "error": "Organization does not exist" }
            update_fields['organization_id'] = organization_id

        if not update_fields:
            return { "success": False, "error": "No update attributes provided" }

        # Perform update
        for key, value in update_fields.items():
            customer[key] = value

        self.customers[customer_id] = customer
        return { "success": True, "message": "Customer updated successfully" }

    def add_survey(
        self,
        survey_id: str,
        title: str,
        question_set: list,
        active_period: str,
        associated_organization_id: str
    ) -> dict:
        """
        Add a new survey definition for an organization.

        Args:
            survey_id (str): Unique identifier for the survey.
            title (str): Survey title.
            question_set (list): List of survey questions.
            active_period (str): Active period of survey (e.g., date range string).
            associated_organization_id (str): ID of the organization to which the survey is linked.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Survey <survey_id> added successfully"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - survey_id must be unique.
            - associated_organization_id must exist.
        """
        if survey_id in self.surveys:
            return {"success": False, "error": f"Survey with id '{survey_id}' already exists."}

        if associated_organization_id not in self.organizations:
            return {"success": False, "error": "Associated organization does not exist."}

        self.surveys[survey_id] = {
            "survey_id": survey_id,
            "title": title,
            "question_set": question_set,
            "active_period": active_period,
            "associated_organization_id": associated_organization_id
        }

        return {"success": True, "message": f"Survey {survey_id} added successfully"}

    def update_survey(
        self,
        survey_id: str,
        question_set: List[Any] = None,
        active_period: str = None,
        associated_organization_id: str = None
    ) -> dict:
        """
        Edit survey questions, active period, or associated organization.

        Args:
            survey_id (str): ID of the survey to update.
            question_set (Optional[List[Any]]): New set of survey questions.
            active_period (Optional[str]): New active period.
            associated_organization_id (Optional[str]): New associated organization ID.

        Returns:
            dict: 
                On success: { "success": True, "message": "Survey updated successfully." }
                On failure: { "success": False, "error": str }

        Constraints:
            - survey_id must exist in self.surveys.
            - If associated_organization_id is provided, it must be valid in self.organizations.
            - At least one field must be provided to update.
        """
        survey = self.surveys.get(survey_id)
        if not survey:
            return { "success": False, "error": "Survey not found." }

        fields_updated = False

        if question_set is not None:
            survey["question_set"] = question_set
            fields_updated = True

        if active_period is not None:
            survey["active_period"] = active_period
            fields_updated = True

        if associated_organization_id is not None:
            if associated_organization_id not in self.organizations:
                return { "success": False, "error": "Organization not found for associated_organization_id." }
            survey["associated_organization_id"] = associated_organization_id
            fields_updated = True

        if not fields_updated:
            return { "success": False, "error": "No fields provided for update." }

        # Write back update
        self.surveys[survey_id] = survey

        return { "success": True, "message": "Survey updated successfully." }

    def add_organization(self, organization_id: str, name: str, business_un: str) -> dict:
        """
        Adds a new organization entry to the system.

        Args:
            organization_id (str): Unique identifier for the organization.
            name (str): Name of the organization.
            business_un (str): Business unit of the organization.

        Returns:
            dict: {
                "success": True,
                "message": "Organization added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - organization_id must be unique (not already present).
            - All fields should be non-empty strings.
        """
        if not organization_id or not name or not business_un:
            return {
                "success": False,
                "error": "All fields (organization_id, name, business_un) must be provided and non-empty."
            }

        if organization_id in self.organizations:
            return {
                "success": False,
                "error": "Organization ID already exists."
            }

        org_info: OrganizationInfo = {
            "organization_id": organization_id,
            "name": name,
            "business_un": business_un
        }
        self.organizations[organization_id] = org_info

        return {
            "success": True,
            "message": "Organization added successfully."
        }

    def update_organization(
        self,
        organization_id: str,
        name: str = None,
        business_un: str = None
    ) -> dict:
        """
        Update attributes of an organization (name, business unit).

        Args:
            organization_id (str): ID of the organization to update.
            name (Optional[str]): New name of the organization (if updating).
            business_un (Optional[str]): New business unit (if updating).

        Returns:
            dict:
                - success: True and a message if updated successfully.
                - success: False and error message if failed.

        Constraints:
            - Organization must exist.
            - At least one field to update must be provided.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }

        # No-op if neither field is provided
        if name is None and business_un is None:
            return { "success": False, "error": "No update fields provided" }

        org_info = self.organizations[organization_id]

        updated = False
        if name is not None:
            org_info["name"] = name
            updated = True
        if business_un is not None:
            org_info["business_un"] = business_un
            updated = True

        self.organizations[organization_id] = org_info

        if updated:
            return { "success": True, "message": "Organization updated successfully." }
        else:
            return { "success": False, "error": "No valid fields were updated." }

    def delete_customer(self, customer_id: str) -> dict:
        """
        Remove a customer from the system if no associated survey responses exist.

        Args:
            customer_id (str): Unique customer identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Customer X deleted."
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Cannot delete a customer if any SurveyResponse is linked to them (referential integrity).
            - Customer must exist.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": f"Customer {customer_id} does not exist." }

        # Check for any survey responses linked to this customer
        responses_linked = [
            resp for resp in self.survey_responses.values()
            if resp["customer_id"] == customer_id
        ]
        if responses_linked:
            return {
                "success": False,
                "error": f"Cannot delete customer {customer_id}: Linked survey responses exist."
            }

        # Safe to delete
        del self.customers[customer_id]
        return {
            "success": True,
            "message": f"Customer {customer_id} deleted."
        }


class CustomerFeedbackManagementSystem(BaseEnv):
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

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def list_customers_by_organization(self, **kwargs):
        return self._call_inner_tool('list_customers_by_organization', kwargs)

    def list_surveys_by_organization(self, **kwargs):
        return self._call_inner_tool('list_surveys_by_organization', kwargs)

    def list_survey_responses_by_organization(self, **kwargs):
        return self._call_inner_tool('list_survey_responses_by_organization', kwargs)

    def list_survey_responses_by_customer(self, **kwargs):
        return self._call_inner_tool('list_survey_responses_by_customer', kwargs)

    def get_survey_response_by_id(self, **kwargs):
        return self._call_inner_tool('get_survey_response_by_id', kwargs)

    def calculate_nps_for_organization(self, **kwargs):
        return self._call_inner_tool('calculate_nps_for_organization', kwargs)

    def calculate_nps_for_organization_by_survey(self, **kwargs):
        return self._call_inner_tool('calculate_nps_for_organization_by_survey', kwargs)

    def get_survey_by_id(self, **kwargs):
        return self._call_inner_tool('get_survey_by_id', kwargs)

    def add_survey_response(self, **kwargs):
        return self._call_inner_tool('add_survey_response', kwargs)

    def update_survey_response(self, **kwargs):
        return self._call_inner_tool('update_survey_response', kwargs)

    def delete_survey_response(self, **kwargs):
        return self._call_inner_tool('delete_survey_response', kwargs)

    def add_customer(self, **kwargs):
        return self._call_inner_tool('add_customer', kwargs)

    def update_customer(self, **kwargs):
        return self._call_inner_tool('update_customer', kwargs)

    def add_survey(self, **kwargs):
        return self._call_inner_tool('add_survey', kwargs)

    def update_survey(self, **kwargs):
        return self._call_inner_tool('update_survey', kwargs)

    def add_organization(self, **kwargs):
        return self._call_inner_tool('add_organization', kwargs)

    def update_organization(self, **kwargs):
        return self._call_inner_tool('update_organization', kwargs)

    def delete_customer(self, **kwargs):
        return self._call_inner_tool('delete_customer', kwargs)

