# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime



class LeadInfo(TypedDict):
    lead_id: str
    email: str
    name: str
    country: str
    region: str
    city: str
    created_at: str  # ISO 8601 timestamp as string
    campaign_id: str

class CampaignInfo(TypedDict):
    campaign_id: str
    campaign_name: str
    campaign_type: str
    start_date: str  # ISO 8601 date as string
    end_date: str    # ISO 8601 date as string
    status: str      # Assumed correction of 'sta' to 'status'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for Online Lead Management System.
        Stores leads and campaigns as dictionaries with their respective IDs as keys.
        
        Constraints:
        - Each lead must be associated with a valid campaign_id.
        - Email should be unique per lead or follow system-specific rules.
        - The 'created_at' timestamp must be captured when the lead is created.
        - Campaigns cannot be deleted if leads are associated with them.
        """
        # Leads: {lead_id: LeadInfo}
        self.leads: Dict[str, LeadInfo] = {}
        # Campaigns: {campaign_id: CampaignInfo}
        self.campaigns: Dict[str, CampaignInfo] = {}

    def get_campaign_by_id(self, campaign_id: str) -> dict:
        """
        Retrieve campaign information using campaign_id.

        Args:
            campaign_id (str): The ID of the campaign to retrieve.

        Returns:
            dict: 
                If found: {"success": True, "data": CampaignInfo}
                If not found: {"success": False, "error": "Campaign not found"}
        """
        if campaign_id in self.campaigns:
            return {"success": True, "data": self.campaigns[campaign_id]}
        else:
            return {"success": False, "error": "Campaign not found"}

    def list_all_campaigns(self) -> dict:
        """
        List all campaigns currently present in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # List of all campaign metadata (empty if none)
            }
        """
        campaigns = list(self.campaigns.values())
        return { "success": True, "data": campaigns }

    def get_leads_by_campaign(self, campaign_id: str) -> dict:
        """
        Retrieve all leads associated with the given campaign_id.

        Args:
            campaign_id (str): The campaign ID for which to retrieve associated leads.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[LeadInfo]  # List (possibly empty) of LeadInfo dicts
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g. "Campaign does not exist"
                    }

        Constraints:
            - Campaign ID must exist in the system.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign does not exist" }

        leads_list = [
            lead_info for lead_info in self.leads.values()
            if lead_info["campaign_id"] == campaign_id
        ]
        return { "success": True, "data": leads_list }

    def get_lead_by_id(self, lead_id: str) -> dict:
        """
        Retrieve a lead’s information using lead_id.

        Args:
            lead_id (str): The unique identifier of the lead.

        Returns:
            dict: {
                "success": True,
                "data": LeadInfo  # All information for the matching lead
            }
            or
            {
                "success": False,
                "error": "Lead not found"
            }
    
        Constraints:
            - lead_id must exist in the system.
        """
        lead = self.leads.get(lead_id)
        if lead is None:
            return { "success": False, "error": "Lead not found" }
        return { "success": True, "data": lead }

    def get_lead_by_email(self, email: str) -> dict:
        """
        Retrieve a lead's complete information using their unique email address.

        Args:
            email (str): The email address of the lead.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": LeadInfo   # Information for the matching lead
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Lead with provided email not found"
                    }

        Constraints:
            - Email should be unique per lead, but this function simply returns the first matching lead.
        """
        for lead in self.leads.values():
            if lead['email'] == email:
                return { "success": True, "data": lead }
        return { "success": False, "error": "Lead with provided email not found" }

    def list_all_leads(self) -> dict:
        """
        List all leads present in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[LeadInfo],  # List of LeadInfo dicts (empty list if no leads)
            }
        """
        result = list(self.leads.values())
        return {"success": True, "data": result}

    def extract_lead_details(self, lead_ids: list[str]) -> dict:
        """
        For a given list of lead IDs, extract selected fields (email, name, country, region, city, created_at) for each.

        Args:
            lead_ids (list[str]): List of lead IDs to extract details for.

        Returns:
            dict: 
                - If successful:
                    { "success": True, "data": [ { "lead_id": ..., "email": ..., "name": ..., "country": ..., "region": ..., "city": ..., "created_at": ... }, ... ] }
                - If all lead_ids invalid or input empty:
                    { "success": False, "error": "No valid leads found for given ID(s)" }

        Notes:
            - If some IDs are invalid, only valid ones are included in the output.
            - If no valid IDs, returns error.
        """
        if not lead_ids or not isinstance(lead_ids, list):
            return { "success": False, "error": "No valid leads found for given ID(s)" }

        selected_fields = ["lead_id", "email", "name", "country", "region", "city", "created_at"]
        result = []

        for lid in lead_ids:
            lead = self.leads.get(lid)
            if lead:
                short_lead = {field: lead[field] for field in selected_fields}
                result.append(short_lead)

        if not result:
            return { "success": False, "error": "No valid leads found for given ID(s)" }

        return { "success": True, "data": result }

    def count_leads_by_campaign(self, campaign_id: str) -> dict:
        """
        Get the number of leads associated with a specific campaign.

        Args:
            campaign_id (str): ID of the campaign to count leads for.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "campaign_id": str,
                    "lead_count": int
                }
            }
            OR
            {
                "success": False,
                "error": str  # e.g., campaign does not exist
            }

        Constraints:
            - campaign_id must exist in the campaigns data.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign does not exist" }

        count = sum(1 for lead in self.leads.values() if lead["campaign_id"] == campaign_id)
        return { "success": True, "data": { "campaign_id": campaign_id, "lead_count": count } }


    def create_lead(
        self,
        lead_id: str,
        email: str,
        name: str,
        country: str,
        region: str,
        city: str,
        campaign_id: str
    ) -> dict:
        """
        Add a new lead, ensuring valid campaign association and unique email.

        Args:
            lead_id (str): Unique identifier for the lead.
            email (str): Lead's email. Must be unique in the system.
            name (str): Name of the lead.
            country (str): Country for the lead.
            region (str): Region for the lead.
            city (str): City for the lead.
            campaign_id (str): Campaign to associate this lead with. Must exist.

        Returns:
            dict: {
                "success": True,
                "message": "Lead created successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The campaign must exist.
            - Email must be unique among all leads.
            - lead_id must be unique.
            - created_at is set at the time of creation (ISO8601).
        """
        # lead_id must be unique
        if lead_id in self.leads:
            return {"success": False, "error": "Lead ID already exists"}

        # campaign_id must exist
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Associated campaign_id does not exist"}

        # Email uniqueness check
        for lead in self.leads.values():
            if lead["email"] == email:
                return {"success": False, "error": "Email already exists"}

        created_at = datetime.utcnow().isoformat() + "Z"

        lead_info = {
            "lead_id": lead_id,
            "email": email,
            "name": name,
            "country": country,
            "region": region,
            "city": city,
            "created_at": created_at,
            "campaign_id": campaign_id
        }

        self.leads[lead_id] = lead_info

        return {"success": True, "message": "Lead created successfully"}

    def update_lead(self, lead_id: str, update_fields: dict) -> dict:
        """
        Update the information of an existing lead.
    
        Args:
            lead_id (str): The unique identifier of the lead to update.
            update_fields (dict): Dictionary of fields to update (cannot include 'lead_id' or 'created_at').

        Returns:
            dict: 
                On success: { "success": True, "message": "Lead updated" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The lead must exist in the system.
            - 'lead_id' and 'created_at' cannot be updated.
            - If 'email' is updated, it must remain unique among all leads.
            - If 'campaign_id' is updated, the new campaign must exist.
            - Each lead must always be associated with a valid campaign_id.
        """
        if lead_id not in self.leads:
            return { "success": False, "error": "Lead does not exist" }

        if not update_fields:
            return { "success": False, "error": "No fields provided to update" }

        lead_info = self.leads[lead_id]

        # Disallow changes to lead_id and created_at
        immutable_fields = {"lead_id", "created_at"}
        for key in update_fields:
            if key in immutable_fields:
                return { "success": False, "error": f"Cannot update field '{key}'" }

        # If email is being updated, check for uniqueness
        if "email" in update_fields:
            new_email = update_fields["email"]
            for other_lead_id, other_lead in self.leads.items():
                if other_lead_id != lead_id and other_lead["email"] == new_email:
                    return { "success": False, "error": "Email must be unique" }
    
        # If campaign_id is being updated, validate existence
        if "campaign_id" in update_fields:
            new_campaign_id = update_fields["campaign_id"]
            if new_campaign_id not in self.campaigns:
                return { "success": False, "error": "New campaign_id does not exist" }

        # Apply changes
        updated = False
        for key, value in update_fields.items():
            if key in lead_info and lead_info[key] != value:
                lead_info[key] = value
                updated = True

        self.leads[lead_id] = lead_info

        if not updated:
            return { "success": True, "message": "No changes were made (fields identical to current values)" }

        return { "success": True, "message": "Lead updated" }

    def delete_lead(self, lead_id: str) -> dict:
        """
        Remove a lead from the system by the given lead_id.

        Args:
            lead_id (str): Unique identifier of the lead to remove.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Lead <lead_id> successfully deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The lead identified by lead_id must exist.
            - No other explicit constraints are imposed for lead deletion.
        """
        if lead_id not in self.leads:
            return {"success": False, "error": f"Lead '{lead_id}' does not exist."}
    
        del self.leads[lead_id]
        return {"success": True, "message": f"Lead '{lead_id}' successfully deleted."}

    def create_campaign(
        self,
        campaign_id: str,
        campaign_name: str,
        campaign_type: str,
        start_date: str,
        end_date: str,
        status: str
    ) -> dict:
        """
        Add a new campaign to the system.

        Args:
            campaign_id (str): Unique identifier for the campaign.
            campaign_name (str): Name of the campaign.
            campaign_type (str): Type/category of the campaign.
            start_date (str): Campaign start date (ISO 8601 string).
            end_date (str): Campaign end date (ISO 8601 string).
            status (str): Status of the campaign.

        Returns:
            dict: {
                "success": True,
                "message": "Campaign created successfully."
            }
            or
            {
                "success": False,
                "error": "Campaign ID already exists." / "Missing required campaign field(s)."
            }

        Constraints:
            - campaign_id must be unique in the system.
            - All fields are required and must be non-empty.
        """
        # Check for required fields (none should be empty)
        required = [campaign_id, campaign_name, campaign_type, start_date, end_date, status]
        if any(field is None or str(field).strip() == "" for field in required):
            return {"success": False, "error": "Missing required campaign field(s)."}

        # Enforce uniqueness of campaign_id
        if campaign_id in self.campaigns:
            return {"success": False, "error": "Campaign ID already exists."}

        # Prepare campaign info dict
        campaign_info: CampaignInfo = {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "campaign_type": campaign_type,
            "start_date": start_date,
            "end_date": end_date,
            "status": status
        }

        self.campaigns[campaign_id] = campaign_info
        return {"success": True, "message": "Campaign created successfully."}

    def update_campaign(
        self,
        campaign_id: str,
        campaign_name: str = None,
        campaign_type: str = None,
        start_date: str = None,
        end_date: str = None,
        status: str = None
    ) -> dict:
        """
        Update details of an existing campaign.

        Args:
            campaign_id (str): The unique campaign identifier.
            campaign_name (str, optional): New name for the campaign.
            campaign_type (str, optional): New type for the campaign.
            start_date (str, optional): New start date (ISO 8601).
            end_date (str, optional): New end date (ISO 8601).
            status (str, optional): New status value.

        Returns:
            dict: 
                On success: { "success": True, "message": "Campaign updated successfully." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Campaign must exist.
            - At least one updatable field must be provided.
            - Only valid attributes are updated.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign does not exist." }

        update_fields = ["campaign_name", "campaign_type", "start_date", "end_date", "status"]
        new_values = {
            "campaign_name": campaign_name,
            "campaign_type": campaign_type,
            "start_date": start_date,
            "end_date": end_date,
            "status": status
        }

        if not any(new_values[field] is not None for field in update_fields):
            return { "success": False, "error": "No update parameters provided." }

        for field, value in new_values.items():
            if value is not None:
                self.campaigns[campaign_id][field] = value

        return { "success": True, "message": "Campaign updated successfully." }

    def delete_campaign(self, campaign_id: str) -> dict:
        """
        Remove the campaign with the given `campaign_id` from the system, ONLY if it has no leads associated.
    
        Args:
            campaign_id (str): The unique identifier of the campaign to be deleted.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Campaign <id> deleted successfully." }
                On failure (campaign not found or constraint violation):
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Campaigns cannot be deleted if leads are associated with them.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign does not exist." }

        for lead in self.leads.values():
            if lead.get("campaign_id") == campaign_id:
                return { 
                    "success": False, 
                    "error": "Cannot delete campaign: leads are still associated with this campaign." 
                }

        del self.campaigns[campaign_id]
        return { "success": True, "message": f"Campaign {campaign_id} deleted successfully." }

    def reassign_leads_to_campaign(self, leads_ids: list, new_campaign_id: str) -> dict:
        """
        Change the campaign assignment of multiple leads to another campaign.

        Args:
            leads_ids (list of str): List of lead_id values to be reassigned.
            new_campaign_id (str): campaign_id to assign to the leads.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message describing operation
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - All lead_ids must exist in the system.
            - new_campaign_id must exist.
            - Each lead's 'campaign_id' attribute will be updated to new_campaign_id.
        """

        # Check presence of new campaign
        if new_campaign_id not in self.campaigns:
            return {"success": False, "error": f"Target campaign_id '{new_campaign_id}' does not exist."}

        # Check all leads exist
        missing_leads = [lead_id for lead_id in leads_ids if lead_id not in self.leads]
        if missing_leads:
            return {"success": False, "error": f"The following lead_ids do not exist: {missing_leads}"}

        # Perform reassignment
        for lead_id in set(leads_ids):  # set() to avoid double-update
            self.leads[lead_id]["campaign_id"] = new_campaign_id

        return {
            "success": True,
            "message": f"Reassigned {len(set(leads_ids))} lead(s) to campaign '{new_campaign_id}'."
        }

    def validate_campaign_deletion(self, campaign_id: str) -> dict:
        """
        Check if a campaign has zero associated leads and can safely be deleted.

        Args:
            campaign_id (str): The ID of the campaign to validate.

        Returns:
            dict:
                - If campaign does not exist:
                  { "success": False, "error": "Campaign does not exist" }
                - If leads are still associated:
                  { "success": False, "error": "<n> leads are still associated with this campaign" }
                - If no leads are associated:
                  { "success": True, "message": "Campaign can be safely deleted" }

        Constraints:
            - Campaigns cannot be deleted if leads are still associated with them.
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign does not exist" }

        num_leads = sum(
            1 for lead in self.leads.values()
            if lead["campaign_id"] == campaign_id
        )

        if num_leads > 0:
            return {
                "success": False,
                "error": f"{num_leads} leads are still associated with this campaign"
            }

        return {
            "success": True,
            "message": "Campaign can be safely deleted"
        }

    def check_email_uniqueness(self, email: str) -> dict:
        """
        Validate that a provided lead email is not already used by another lead.
    
        Args:
            email (str): The email address to check for uniqueness.
        
        Returns:
            dict: 
                - { "success": True, "message": "Email is unique." }
                - { "success": False, "error": "Email is already associated with an existing lead." }
    
        Constraints:
            - Email must not already exist in self.leads values under the 'email' field.
        """
        for lead_info in self.leads.values():
            if lead_info["email"].lower() == email.lower():
                return { "success": False, "error": "Email is already associated with an existing lead." }
        return { "success": True, "message": "Email is unique." }


class OnlineLeadManagementSystem(BaseEnv):
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

    def get_campaign_by_id(self, **kwargs):
        return self._call_inner_tool('get_campaign_by_id', kwargs)

    def list_all_campaigns(self, **kwargs):
        return self._call_inner_tool('list_all_campaigns', kwargs)

    def get_leads_by_campaign(self, **kwargs):
        return self._call_inner_tool('get_leads_by_campaign', kwargs)

    def get_lead_by_id(self, **kwargs):
        return self._call_inner_tool('get_lead_by_id', kwargs)

    def get_lead_by_email(self, **kwargs):
        return self._call_inner_tool('get_lead_by_email', kwargs)

    def list_all_leads(self, **kwargs):
        return self._call_inner_tool('list_all_leads', kwargs)

    def extract_lead_details(self, **kwargs):
        return self._call_inner_tool('extract_lead_details', kwargs)

    def count_leads_by_campaign(self, **kwargs):
        return self._call_inner_tool('count_leads_by_campaign', kwargs)

    def create_lead(self, **kwargs):
        return self._call_inner_tool('create_lead', kwargs)

    def update_lead(self, **kwargs):
        return self._call_inner_tool('update_lead', kwargs)

    def delete_lead(self, **kwargs):
        return self._call_inner_tool('delete_lead', kwargs)

    def create_campaign(self, **kwargs):
        return self._call_inner_tool('create_campaign', kwargs)

    def update_campaign(self, **kwargs):
        return self._call_inner_tool('update_campaign', kwargs)

    def delete_campaign(self, **kwargs):
        return self._call_inner_tool('delete_campaign', kwargs)

    def reassign_leads_to_campaign(self, **kwargs):
        return self._call_inner_tool('reassign_leads_to_campaign', kwargs)

    def validate_campaign_deletion(self, **kwargs):
        return self._call_inner_tool('validate_campaign_deletion', kwargs)

    def check_email_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_email_uniqueness', kwargs)

