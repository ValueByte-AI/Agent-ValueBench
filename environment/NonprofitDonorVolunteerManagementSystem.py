# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict

_UNSET = object()



class OrganizationInfo(TypedDict):
    organization_id: str
    name: str
    mission_statement: str
    profile_info: str
    contact_info: str

class DonorInfo(TypedDict):
    donor_id: str
    name: str
    contact_info: str
    donation_history: List[str]      # List of donation_ids
    volunteer_history: List[str]     # List of engagement_ids

class DonationInfo(TypedDict):
    donation_id: str
    donor_id: str
    organization_id: str
    donation_date: str
    amount: float
    impact_report: Optional[str]     # May be None if no report available

class VolunteerEngagementInfo(TypedDict):
    engagement_id: str
    volunteer_id: str
    organization_id: str
    event_id: Optional[str]          # May be None if not linked to a specific event
    role: str
    participation_date: str
    hours_served: float

class EventInfo(TypedDict):
    event_id: str
    organization_id: str
    name: str
    description: str
    date: str
    volunteer_role: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Nonprofit donor and volunteer management system environment state.
        """

        # Organizations: {organization_id: OrganizationInfo}
        self.organizations: Dict[str, OrganizationInfo] = {}

        # Donors: {donor_id: DonorInfo}
        self.donors: Dict[str, DonorInfo] = {}

        # Donations: {donation_id: DonationInfo}
        self.donations: Dict[str, DonationInfo] = {}

        # Volunteer Engagements: {engagement_id: VolunteerEngagementInfo}
        self.volunteer_engagements: Dict[str, VolunteerEngagementInfo] = {}

        # Events: {event_id: EventInfo}
        self.events: Dict[str, EventInfo] = {}

        # ---------------------------------------------
        # Constraints:
        # - Each donation must be linked to a valid donor and organization.
        # - Each volunteer engagement must reference a valid volunteer and organization (and, if applicable, a valid event).
        # - Impact reports, if requested, must exist for donations or indicate if none is available.
        # - Organization missions and profiles must be accessible and retrievable for communication and reporting purposes.
        # ---------------------------------------------

    def get_organization_by_name(self, name: str) -> dict:
        """
        Retrieve complete organization information (including mission statement)
        given the organization's name.

        Args:
            name (str): The name of the organization to look up.

        Returns:
            dict: {
                "success": True,
                "data": OrganizationInfo
            }
            or
            {
                "success": False,
                "error": str  # "Organization not found" if no match
            }

        Constraints:
            - The organization name must match exactly.
            - If multiple organizations have the same name, returns the first found.
        """
        for org in self.organizations.values():
            if org["name"] == name:
                return { "success": True, "data": org }
        return { "success": False, "error": "Organization not found" }

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Retrieve complete organization information by organization_id.

        Args:
            organization_id (str): The unique identifier of the organization.

        Returns:
            dict: 
                - On success: { "success": True, "data": OrganizationInfo }
                - On failure: { "success": False, "error": "Organization not found." }

        Constraints:
            - organization_id must exist in the environment's organizations.
        """
        org = self.organizations.get(organization_id)
        if org is None:
            return { "success": False, "error": "Organization not found." }
        return { "success": True, "data": org }

    def list_organizations(self) -> dict:
        """
        List all registered organizations with their summary information.

        Returns:
            dict: {
                "success": True,
                "data": List[OrganizationInfo],  # May be empty if no organizations are present
            }
        """
        result = list(self.organizations.values())
        return {
            "success": True,
            "data": result
        }

    def get_organization_mission(self, organization_id: str = None, organization_name: str = None) -> dict:
        """
        Retrieve the mission statement of a nonprofit organization by its ID or name.

        Args:
            organization_id (str, optional): Unique identifier of the organization.
            organization_name (str, optional): Name of the organization.

        Returns:
            dict: {
                "success": True,
                "data": str  # The mission statement
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - At least one identifier (id or name) must be provided.
            - Returns the organization's mission statement if found; else, returns an error.
        """
        # Prioritize organization_id if both provided
        org_info = None

        if organization_id:
            org_info = self.organizations.get(organization_id)
            if not org_info:
                return {"success": False, "error": "Organization with specified id not found"}
        elif organization_name:
            for org in self.organizations.values():
                if org["name"] == organization_name:
                    org_info = org
                    break
            if not org_info:
                return {"success": False, "error": "Organization with specified name not found"}
        else:
            return {"success": False, "error": "Must provide organization_id or organization_name"}

        return {"success": True, "data": org_info["mission_statement"]}

    def get_organization_profile(self, organization_id: str) -> dict:
        """
        Retrieve the full profile for a specified organization, including mission statement,
        profile info, name, and contact info.

        Args:
            organization_id (str): Unique identifier for the organization.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": OrganizationInfo  # Full organization profile
                    }
                On failure (organization_id not found):
                    {
                        "success": False,
                        "error": "Organization not found"
                    }

        Constraints:
            - organization_id must exist in the system.
        """
        org = self.organizations.get(organization_id)
        if org is None:
            return { "success": False, "error": "Organization not found" }
        # Return full OrganizationInfo structure
        return { "success": True, "data": org }

    def get_donor_by_id(self, donor_id: str) -> dict:
        """
        Retrieve detailed donor information by donor_id.
    
        Args:
            donor_id (str): The unique identifier of the donor.
        
        Returns:
            dict: {
                "success": True,
                "data": DonorInfo  # Detailed donor info including contact and histories.
            }
            or
            {
                "success": False,
                "error": str  # Error message if donor not found.
            }
        
        Constraints:
            - donor_id must exist in the system.
        """
        donor_info = self.donors.get(donor_id)
        if donor_info is None:
            return { "success": False, "error": "Donor not found" }
        return { "success": True, "data": donor_info }

    def get_donor_by_name(self, name: str) -> dict:
        """
        Retrieve donor information by donor's name.

        Args:
            name (str): The exact name of the donor to query.

        Returns:
            dict: {
                "success": True,
                "data": List[DonorInfo]  # List of matching donors (may be empty if no matches)
            }

        Constraints:
            - Returns all donors whose 'name' exactly matches the given input (case-sensitive).
            - No error is returned if no donor is found; 'data' will simply be an empty list.
        """
        result = [
            donor for donor in self.donors.values()
            if donor["name"] == name
        ]
        return {"success": True, "data": result}

    def get_donation_by_id(self, donation_id: str) -> dict:
        """
        Retrieve donation details, including donor, organization, amount, date, and impact report, by donation_id.

        Args:
            donation_id (str): The unique identifier of the donation.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": DonationInfo,  # Details about the donation.
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": str  # Description of the error.
                    }

        Notes:
            - If impact_report is not available for the donation, it will be None in the result.
            - Only retrieves the donation if the donation_id exists in the system.
        """
        donation = self.donations.get(donation_id)
        if donation is None:
            return {"success": False, "error": "Donation not found"}

        return {"success": True, "data": donation}

    def get_donor_donation_history(self, donor_id: str) -> dict:
        """
        Retrieve all donation IDs and summary info for a given donor.

        Args:
            donor_id (str): The unique ID of the donor.

        Returns:
            dict: {
                "success": True,
                "data": [  # List of donation summaries (may be empty)
                    {
                        "donation_id": str,
                        "organization_id": str,
                        "donation_date": str,
                        "amount": float
                    },
                    ...
                ]
            }
            or
            {
                "success": False,
                "error": str  # "Donor not found"
            }

        Constraints:
            - Donor with given donor_id must exist.
            - Only donations actually present in the donation registry are returned.
        """
        donor_info = self.donors.get(donor_id)
        if donor_info is None:
            return { "success": False, "error": "Donor not found" }

        summaries = []
        for donation_id in donor_info.get("donation_history", []):
            donation = self.donations.get(donation_id)
            if donation:
                summaries.append({
                    "donation_id": donation["donation_id"],
                    "organization_id": donation["organization_id"],
                    "donation_date": donation["donation_date"],
                    "amount": donation["amount"]
                })

        return { "success": True, "data": summaries }

    def get_donation_impact_report(self, donation_id: str) -> dict:
        """
        Retrieve the impact report for a specific donation, if it exists.

        Args:
            donation_id (str): The unique identifier for the donation.

        Returns:
            dict:
                - If donation exists and report present:
                    { "success": True, "data": <impact_report (str)> }
                - If donation exists but no report:
                    { "success": True, "data": None, "message": "No impact report available for this donation." }
                - If donation does not exist:
                    { "success": False, "error": "Donation does not exist." }

        Constraints:
            - The donation must exist in self.donations.
            - Indicate explicitly if no impact report is available for a valid donation.
        """
        donation = self.donations.get(donation_id)
        if donation is None:
            return {"success": False, "error": "Donation does not exist."}
        impact_report = donation.get("impact_report")
        if impact_report is None:
            return {"success": True, "data": None, "message": "No impact report available for this donation."}
        return {"success": True, "data": impact_report}

    def list_volunteer_engagements_by_donor(self, donor_id: str) -> dict:
        """
        List all volunteer engagement records for the given donor/volunteer.

        Args:
            donor_id (str): Unique identifier for the donor/volunteer.

        Returns:
            dict: {
                "success": True,
                "data": List[VolunteerEngagementInfo]  # List of engagements (can be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Error message if donor_id is invalid
            }

        Constraints:
            - donor_id must exist in the donors data.
            - Only valid engagement_ids in volunteer_history are included in the result.
        """
        if donor_id not in self.donors:
            return { "success": False, "error": "Donor/volunteer not found" }

        donor_info = self.donors[donor_id]
        engagement_ids = donor_info.get("volunteer_history", [])
        engagements = [
            self.volunteer_engagements[engagement_id]
            for engagement_id in engagement_ids
            if engagement_id in self.volunteer_engagements
        ]
        return { "success": True, "data": engagements }

    def get_volunteer_engagement_by_id(self, engagement_id: str) -> dict:
        """
        Retrieve the full VolunteerEngagementInfo record for a given volunteer engagement ID.
    
        Args:
            engagement_id (str): The unique ID of the volunteer engagement record.
    
        Returns:
            dict: 
                - {"success": True, "data": VolunteerEngagementInfo} if found
                - {"success": False, "error": "Volunteer engagement not found"} if the ID does not exist
        """
        engagement = self.volunteer_engagements.get(engagement_id)
        if engagement is None:
            return {"success": False, "error": "Volunteer engagement not found"}
        return {"success": True, "data": engagement}

    def list_events_by_organization(self, organization_id: str) -> dict:
        """
        List all events held by the specified organization.

        Args:
            organization_id (str): The unique ID of the organization.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[EventInfo]  # List of events for the organization (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "Organization does not exist"
                    }

        Constraints:
            - organization_id must exist in the organizations.
        """
        if organization_id not in self.organizations:
            return { "success": False, "error": "Organization does not exist" }
    
        events = [
            event for event in self.events.values()
            if event["organization_id"] == organization_id
        ]
        return { "success": True, "data": events }

    def get_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve full information for a specific event.

        Args:
            event_id (str): The unique identifier for the event.

        Returns:
            dict: {
                "success": True,
                "data": EventInfo  # Detailed info for the found event
            }
            or
            {
                "success": False,
                "error": "Event not found"
            }

        Constraints:
            - The event_id must exist in the environment.
        """
        event = self.events.get(event_id)
        if event is None:
            return {"success": False, "error": "Event not found"}
        return {"success": True, "data": event}

    def validate_donation_entity_links(self, donation_id: str) -> dict:
        """
        Check that a donation properly references a valid donor and organization.

        Args:
            donation_id (str): The ID of the donation to validate.

        Returns:
            dict: 
                - If the donation does not exist:
                  { "success": False, "error": "Donation does not exist" }
                - If the donation exists:
                  {
                      "success": True,
                      "data": {
                          "donation_id": str,
                          "donor_valid": bool,
                          "organization_valid": bool
                      }
                  }

        Constraints:
            - Each donation must be linked to an existing donor and organization in the system.
        """
        donation = self.donations.get(donation_id)
        if donation is None:
            return { "success": False, "error": "Donation does not exist" }

        donor_id = donation["donor_id"]
        organization_id = donation["organization_id"]

        donor_valid = donor_id in self.donors
        organization_valid = organization_id in self.organizations

        return {
            "success": True,
            "data": {
                "donation_id": donation_id,
                "donor_valid": donor_valid,
                "organization_valid": organization_valid
            }
        }

    def validate_volunteer_engagement_links(self, engagement_id: str = None) -> dict:
        """
        Check that each (or a specific) volunteer engagement references valid volunteer (donor),
        organization, and event (if event_id is specified).

        Args:
            engagement_id (str, optional): If specified, only validate this engagement; otherwise, validate all.

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "engagement_id": str,
                    "is_valid_volunteer": bool,
                    "is_valid_organization": bool,
                    "is_valid_event": Optional[bool]  # None if no event_id given for the engagement
                }]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Each volunteer engagement must reference a valid volunteer (donor), organization, and, if applicable, event.
            - If engagement_id is specified, it must exist or return an error.
        """
        engagements_to_check = []
        if engagement_id:
            engagement = self.volunteer_engagements.get(engagement_id)
            if not engagement:
                return {"success": False, "error": f"Volunteer engagement '{engagement_id}' does not exist."}
            engagements_to_check = [engagement]
        else:
            engagements_to_check = list(self.volunteer_engagements.values())

        data = []
        for eng in engagements_to_check:
            is_valid_volunteer = eng["volunteer_id"] in self.donors
            is_valid_organization = eng["organization_id"] in self.organizations
            # Only check event if event_id is not None
            if eng["event_id"] is not None:
                is_valid_event = eng["event_id"] in self.events
            else:
                is_valid_event = None
            data.append({
                "engagement_id": eng["engagement_id"],
                "is_valid_volunteer": is_valid_volunteer,
                "is_valid_organization": is_valid_organization,
                "is_valid_event": is_valid_event
            })

        return {"success": True, "data": data}

    def add_donation(
        self,
        donation_id: str,
        donor_id: str,
        organization_id: str,
        donation_date: str,
        amount: float,
        impact_report: Optional[str] = None
    ) -> dict:
        """
        Record a new donation, validate references, and update donor record.

        Args:
            donation_id (str): Unique ID for the donation.
            donor_id (str): Existing donor's ID.
            organization_id (str): Existing organization's ID.
            donation_date (str): Date of donation.
            amount (float): Donation amount.
            impact_report (Optional[str]): Impact report text or None.

        Returns:
            dict: {
                "success": True,
                "message": "Donation added successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - donation_id must be unique
            - donor_id and organization_id must exist in the system
            - Updates donor's donation_history on success
        """
        # Check for duplicate donation_id
        if donation_id in self.donations:
            return {"success": False, "error": "Donation ID already exists."}

        # Validate donor
        if donor_id not in self.donors:
            return {"success": False, "error": "Donor ID does not exist."}

        # Validate organization
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization ID does not exist."}

        # Create donation record
        donation_info: DonationInfo = {
            "donation_id": donation_id,
            "donor_id": donor_id,
            "organization_id": organization_id,
            "donation_date": donation_date,
            "amount": amount,
            "impact_report": impact_report
        }

        self.donations[donation_id] = donation_info

        # Update donor's donation_history
        self.donors[donor_id]["donation_history"].append(donation_id)

        return {"success": True, "message": "Donation added successfully"}

    def update_impact_report(self, donation_id: str, impact_report: str) -> dict:
        """
        Amend or add the impact report for a given donation.

        Args:
            donation_id (str): The ID of the donation to update.
            impact_report (str): The new or amended impact report text; can be empty to clear the report.

        Returns:
            dict: {
                "success": True,
                "message": "Impact report updated for donation <donation_id>"
            }
            or
            {
                "success": False,
                "error": "Donation not found"
            }

        Constraints:
            - The donation_id must exist in the system.
        """
        if donation_id not in self.donations:
            return { "success": False, "error": "Donation not found" }
        self.donations[donation_id]['impact_report'] = impact_report
        return {
            "success": True,
            "message": f"Impact report updated for donation {donation_id}"
        }

    def add_volunteer_engagement(
        self,
        engagement_id: str,
        volunteer_id: str,
        organization_id: str,
        event_id: Optional[str],
        role: str,
        participation_date: str,
        hours_served: float
    ) -> dict:
        """
        Record a new volunteer engagement in the system.

        Args:
            engagement_id (str): Unique identifier for the volunteer engagement.
            volunteer_id (str): ID of the volunteer (must exist in donors).
            organization_id (str): ID of the organization (must exist).
            event_id (Optional[str]): Event ID if linked, else None.
            role (str): Volunteer role in the engagement.
            participation_date (str): Date of participation (human-readable or ISO format).
            hours_served (float): Number of service hours for this engagement.

        Returns:
            dict: On success: { "success": True, "message": ... }
                  On failure: { "success": False, "error": <reason> }

        Constraints:
            - engagement_id must not already exist.
            - volunteer_id must correspond to existing donor/volunteer.
            - organization_id must exist.
            - If event_id is provided, it must exist in events.
            - engagement_id is linked in the volunteer's volunteer_history.
        """
        # Check for duplicate engagement
        if engagement_id in self.volunteer_engagements:
            return { "success": False, "error": "Engagement ID already exists." }

        if volunteer_id not in self.donors:
            return { "success": False, "error": f"Volunteer (donor) ID {volunteer_id} does not exist." }

        if organization_id not in self.organizations:
            return { "success": False, "error": f"Organization ID {organization_id} does not exist." }

        if event_id is not None and event_id not in self.events:
            return { "success": False, "error": f"Event ID {event_id} does not exist." }

        # Prepare engagement info
        engagement_info: VolunteerEngagementInfo = {
            "engagement_id": engagement_id,
            "volunteer_id": volunteer_id,
            "organization_id": organization_id,
            "event_id": event_id,
            "role": role,
            "participation_date": participation_date,
            "hours_served": hours_served
        }
        # Add to main engagement registry
        self.volunteer_engagements[engagement_id] = engagement_info

        # Update volunteer's history
        self.donors[volunteer_id]["volunteer_history"].append(engagement_id)

        return {
            "success": True,
            "message": f"Volunteer engagement {engagement_id} added for volunteer {volunteer_id} at organization {organization_id}."
        }

    def update_organization_profile(
        self,
        organization_id: str,
        mission_statement: Optional[str] = None,
        profile_info: Optional[str] = None,
        contact_info: Optional[str] = None
    ) -> dict:
        """
        Modify the mission statement, profile information, or contact info for the specified organization.

        Args:
            organization_id (str): Unique ID of the organization to update.
            mission_statement (Optional[str]): New mission statement to set (if provided).
            profile_info (Optional[str]): New profile information to set (if provided).
            contact_info (Optional[str]): New contact info to set (if provided).

        Returns:
            dict: {
                "success": True,
                "message": "Organization profile updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Organization must exist.
            - Only provided fields are updated; others remain unchanged.
        """
        if organization_id not in self.organizations:
            return {"success": False, "error": "Organization does not exist."}
    
        org = self.organizations[organization_id]
        updated = False

        if mission_statement is not None:
            org["mission_statement"] = mission_statement
            updated = True
        if profile_info is not None:
            org["profile_info"] = profile_info
            updated = True
        if contact_info is not None:
            org["contact_info"] = contact_info
            updated = True

        if not updated:
            return {
                "success": False,
                "error": "No updatable fields provided."
            }

        return {"success": True, "message": "Organization profile updated."}

    def correct_donation_links(
        self,
        donation_id: str,
        new_donor_id: str = None,
        new_organization_id: str = None
    ) -> dict:
        """
        Update or correct the donor and/or organization reference for a donation.
    
        Args:
            donation_id (str): The donation to correct.
            new_donor_id (str, optional): The new donor id to associate (must exist).
            new_organization_id (str, optional): The new organization id to associate (must exist).
        
        Returns:
            dict: {
                "success": True,
                "message": str  # Description of correction
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - donation_id must exist in donations.
            - If new_donor_id is provided, must exist in donors.
            - If new_organization_id is provided, must exist in organizations.
            - donation_history must be updated for donor changes (remove from old, add to new).
            - No update if nothing to change or no update params provided.
        """
        # Validate donation exists
        if donation_id not in self.donations:
            return {"success": False, "error": "Donation does not exist."}
    
        donation = self.donations[donation_id]
        current_donor_id = donation["donor_id"]
        current_org_id = donation["organization_id"]
        changed = False

        # Prepare for changes
        # Validate new donor
        if new_donor_id is not None:
            if new_donor_id not in self.donors:
                return {"success": False, "error": "New donor does not exist."}
            if new_donor_id == current_donor_id:
                pass  # no actual change
            else:
                changed = True
        # Validate new organization
        if new_organization_id is not None:
            if new_organization_id not in self.organizations:
                return {"success": False, "error": "New organization does not exist."}
            if new_organization_id == current_org_id:
                pass
            else:
                changed = True

        if not changed:
            return {"success": False, "error": "Nothing to update; parameters not provided or links unchanged."}

        # If donor needs to change
        if new_donor_id is not None and new_donor_id != current_donor_id:
            # Remove from old donor's history
            if current_donor_id in self.donors:
                if donation_id in self.donors[current_donor_id]["donation_history"]:
                    self.donors[current_donor_id]["donation_history"].remove(donation_id)
            # Add to new donor's history if not already present
            if donation_id not in self.donors[new_donor_id]["donation_history"]:
                self.donors[new_donor_id]["donation_history"].append(donation_id)
            # Set new donor id
            donation["donor_id"] = new_donor_id

        # If organization needs to change
        if new_organization_id is not None and new_organization_id != current_org_id:
            donation["organization_id"] = new_organization_id

        return {
            "success": True,
            "message": "Donation links updated successfully"
        }

    def correct_engagement_links(
        self,
        engagement_id: str,
        volunteer_id: str = None,
        organization_id: str = None,
        event_id: Any = _UNSET
    ) -> dict:
        """
        Update or fix the references (volunteer_id, organization_id, event_id) for a given volunteer engagement.

        Args:
            engagement_id (str): The engagement to be corrected.
            volunteer_id (str, optional): New volunteer_id to set (must exist if provided).
            organization_id (str, optional): New organization_id to set (must exist if provided).
            event_id (str, optional): New event_id to set (must exist if provided, or None to clear).

        Returns:
            dict: {
                "success": True,
                "message": "Volunteer engagement links corrected."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Each volunteer engagement must reference a valid volunteer and organization (and, if provided, a valid event).
            - Donor and volunteer_history references are kept consistent if volunteer_id is changed.
        """
        # Check that the engagement exists
        engagement = self.volunteer_engagements.get(engagement_id)
        if engagement is None:
            return { "success": False, "error": "Engagement not found." }

        changes = []
        # Handle volunteer_id change
        if volunteer_id is not None and volunteer_id != engagement["volunteer_id"]:
            if volunteer_id not in self.donors:
                return { "success": False, "error": "Provided volunteer_id does not exist." }
            # Remove from old donor's volunteer_history
            old_volunteer_id = engagement["volunteer_id"]
            if old_volunteer_id in self.donors:
                old_hist = self.donors[old_volunteer_id].get("volunteer_history", [])
                if engagement_id in old_hist:
                    old_hist.remove(engagement_id)
            # Add to new donor's volunteer_history
            new_hist = self.donors[volunteer_id].setdefault("volunteer_history", [])
            if engagement_id not in new_hist:
                new_hist.append(engagement_id)
            engagement["volunteer_id"] = volunteer_id
            changes.append("volunteer_id")

        # Handle organization_id change
        if organization_id is not None and organization_id != engagement["organization_id"]:
            if organization_id not in self.organizations:
                return { "success": False, "error": "Provided organization_id does not exist." }
            engagement["organization_id"] = organization_id
            changes.append("organization_id")

        # Handle event_id change (allow clearing with None)
        if event_id is not _UNSET and event_id != engagement["event_id"]:
            if event_id not in ("", None) and event_id not in self.events:
                return { "success": False, "error": "Provided event_id does not exist." }
            engagement["event_id"] = None if event_id == "" else event_id
            changes.append("event_id")

        if not changes:
            return { "success": False, "error": "No changes provided." }

        return {
            "success": True,
            "message": f"Volunteer engagement {engagement_id} links corrected: {', '.join(changes)}."
        }

    def delete_donation(self, donation_id: str, is_admin: bool) -> dict:
        """
        Remove a donation record by donation_id. Only admins may perform this action.

        Args:
            donation_id (str): The unique ID of the donation to be deleted.
            is_admin (bool): Whether the requester is an admin.

        Returns:
            dict: Success or error description:
              - If permission denied: { "success": False, "error": "Permission denied: admin access required" }
              - If donation not found: { "success": False, "error": "Donation not found" }
              - On success: { "success": True, "message": "Donation <donation_id> has been deleted." }

        Constraints:
            - Only admin users may delete a donation.
            - Donation must exist.
            - Donation must be removed from donor's donation_history.
        """
        if not is_admin:
            return { "success": False, "error": "Permission denied: admin access required" }

        donation = self.donations.get(donation_id)
        if not donation:
            return { "success": False, "error": "Donation not found" }

        donor_id = donation["donor_id"]
        # Remove from the donor's donation_history if donor exists
        if donor_id in self.donors:
            try:
                if donation_id in self.donors[donor_id]["donation_history"]:
                    self.donors[donor_id]["donation_history"].remove(donation_id)
            except Exception:
                # Defensive; should not occur if data is valid
                pass

        # Delete the donation record
        del self.donations[donation_id]

        return { "success": True, "message": f"Donation {donation_id} has been deleted." }

    def delete_volunteer_engagement(self, engagement_id: str) -> dict:
        """
        Remove (delete) a volunteer engagement by its ID. (Admin only)

        Args:
            engagement_id (str): The unique engagement ID to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Volunteer engagement <id> deleted."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - The engagement must exist.
            - Will also remove the engagement ID from the linked donor's volunteer_history (if available).
        """
        engagement = self.volunteer_engagements.get(engagement_id)
        if not engagement:
            return {"success": False, "error": "Volunteer engagement does not exist."}

        volunteer_id = engagement["volunteer_id"]

        # Remove from donor's volunteer_history, if donor exists
        donor_info = self.donors.get(volunteer_id)
        if donor_info and engagement_id in donor_info["volunteer_history"]:
            donor_info["volunteer_history"].remove(engagement_id)
            # No need to update self.donors since donor_info is a reference

        # Remove from the volunteer_engagements dictionary
        del self.volunteer_engagements[engagement_id]

        return {
            "success": True,
            "message": f"Volunteer engagement {engagement_id} deleted."
        }


class NonprofitDonorVolunteerManagementSystem(BaseEnv):
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

    def get_organization_by_name(self, **kwargs):
        return self._call_inner_tool('get_organization_by_name', kwargs)

    def get_organization_by_id(self, **kwargs):
        return self._call_inner_tool('get_organization_by_id', kwargs)

    def list_organizations(self, **kwargs):
        return self._call_inner_tool('list_organizations', kwargs)

    def get_organization_mission(self, **kwargs):
        return self._call_inner_tool('get_organization_mission', kwargs)

    def get_organization_profile(self, **kwargs):
        return self._call_inner_tool('get_organization_profile', kwargs)

    def get_donor_by_id(self, **kwargs):
        return self._call_inner_tool('get_donor_by_id', kwargs)

    def get_donor_by_name(self, **kwargs):
        return self._call_inner_tool('get_donor_by_name', kwargs)

    def get_donation_by_id(self, **kwargs):
        return self._call_inner_tool('get_donation_by_id', kwargs)

    def get_donor_donation_history(self, **kwargs):
        return self._call_inner_tool('get_donor_donation_history', kwargs)

    def get_donation_impact_report(self, **kwargs):
        return self._call_inner_tool('get_donation_impact_report', kwargs)

    def list_volunteer_engagements_by_donor(self, **kwargs):
        return self._call_inner_tool('list_volunteer_engagements_by_donor', kwargs)

    def get_volunteer_engagement_by_id(self, **kwargs):
        return self._call_inner_tool('get_volunteer_engagement_by_id', kwargs)

    def list_events_by_organization(self, **kwargs):
        return self._call_inner_tool('list_events_by_organization', kwargs)

    def get_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_id', kwargs)

    def validate_donation_entity_links(self, **kwargs):
        return self._call_inner_tool('validate_donation_entity_links', kwargs)

    def validate_volunteer_engagement_links(self, **kwargs):
        return self._call_inner_tool('validate_volunteer_engagement_links', kwargs)

    def add_donation(self, **kwargs):
        return self._call_inner_tool('add_donation', kwargs)

    def update_impact_report(self, **kwargs):
        return self._call_inner_tool('update_impact_report', kwargs)

    def add_volunteer_engagement(self, **kwargs):
        return self._call_inner_tool('add_volunteer_engagement', kwargs)

    def update_organization_profile(self, **kwargs):
        return self._call_inner_tool('update_organization_profile', kwargs)

    def correct_donation_links(self, **kwargs):
        return self._call_inner_tool('correct_donation_links', kwargs)

    def correct_engagement_links(self, **kwargs):
        return self._call_inner_tool('correct_engagement_links', kwargs)

    def delete_donation(self, **kwargs):
        return self._call_inner_tool('delete_donation', kwargs)

    def delete_volunteer_engagement(self, **kwargs):
        return self._call_inner_tool('delete_volunteer_engagement', kwargs)
