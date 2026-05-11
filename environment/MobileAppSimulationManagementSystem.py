# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, Any, TypedDict
import uuid
from typing import Dict, Any, Optional



class ApplicationInfo(TypedDict):
    application_id: str
    name: str
    version: str
    platform: str

class SimulationInfo(TypedDict):
    simulation_id: str
    application_id: str
    scenario_type: str
    scenario_parameters: Dict[str, Any]  # e.g. {'geolocation': (lat, lon)}
    status: str
    group_id: Optional[str]  # None if not part of a group

class GroupInfo(TypedDict):
    group_id: str
    name: str
    description: str
    created_by: str
    created_at: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Mobile app simulation management system environment class.
        """

        # Applications: {application_id: ApplicationInfo}
        self.applications: Dict[str, ApplicationInfo] = {}

        # Simulations: {simulation_id: SimulationInfo}
        self.simulations: Dict[str, SimulationInfo] = {}

        # Groups: {group_id: GroupInfo}
        self.groups: Dict[str, GroupInfo] = {}

        # Constraints:
        # - Each simulation must be associated with exactly one application.
        # - A simulation can belong to zero or one group.
        # - Each group can contain zero or more simulations.
        # - Simulations may only be started for registered applications.
        # - Only authorized users may create, view, or manage groups and simulations.

    def get_application_by_id(self, application_id: str) -> dict:
        """
        Retrieve details for a specific application using its application_id.

        Args:
            application_id (str): The unique identifier for the application.

        Returns:
            dict: {
                "success": True,
                "data": ApplicationInfo  # Application info dict
            }
            OR
            {
                "success": False,
                "error": str  # Error message, e.g., "Application does not exist"
            }

        Constraints:
            - The provided application_id must exist in the system.
        """
        app = self.applications.get(application_id)
        if app is None:
            return { "success": False, "error": "Application does not exist" }
        return { "success": True, "data": app }

    def list_applications(self) -> dict:
        """
        Retrieve a list of all registered applications.

        Returns:
            dict: {
                "success": True,
                "data": List[ApplicationInfo]  # List of apps, may be empty if none are registered
            }

        Constraints:
            - No parameters.
            - Returns all applications present in the system.
        """
        return {
            "success": True,
            "data": list(self.applications.values())
        }

    def get_group_by_id(self, group_id: str) -> dict:
        """
        Retrieve details for a specific group by its group_id.

        Args:
            group_id (str): The ID of the group to retrieve.

        Returns:
            dict:
              - If successful:
                { "success": True, "data": GroupInfo }
              - If group not found:
                { "success": False, "error": "Group not found" }
        """
        group = self.groups.get(group_id)
        if group is None:
            return {"success": False, "error": "Group not found"}
        return {"success": True, "data": group}

    def list_groups(self) -> dict:
        """
        Retrieve a list of all groups in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[GroupInfo],  # All groups' metadata, may be empty if no groups exist.
            }

        Constraints:
            - No input parameters or authorization enforced by this method.
        """
        return {
            "success": True,
            "data": list(self.groups.values())
        }

    def list_simulations_by_group(self, group_id: str) -> dict:
        """
        Retrieve all simulations associated with the specified group_id.

        Args:
            group_id (str): The identifier of the group.

        Returns:
            dict: {
                "success": True,
                "data": List[SimulationInfo],  # List of matching simulations (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Group does not exist
            }

        Constraints:
            - The group with group_id must exist.
        """
        if group_id not in self.groups:
            return { "success": False, "error": "Group does not exist" }

        result = [
            sim_info for sim_info in self.simulations.values()
            if sim_info.get("group_id") == group_id
        ]
        return { "success": True, "data": result }

    def list_simulations_by_application(self, application_id: str) -> dict:
        """
        List all simulations tied to a specified application_id.

        Args:
            application_id (str): The unique identifier of the application.

        Returns:
            dict: {
                "success": True,
                "data": List[SimulationInfo]  # List of simulation info dicts (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if the application does not exist
            }

        Constraints:
            - The application_id must be present in self.applications.
            - Only simulations exactly matching the application_id are returned.
        """
        if application_id not in self.applications:
            return {"success": False, "error": "Application does not exist"}

        simulations = [
            simulation for simulation in self.simulations.values()
            if simulation["application_id"] == application_id
        ]

        return {"success": True, "data": simulations}

    def get_simulation_by_id(self, simulation_id: str) -> dict:
        """
        Retrieve full details for a given simulation_id.

        Args:
            simulation_id (str): The unique identifier of the simulation.

        Returns:
            dict: {
                "success": True,
                "data": SimulationInfo,  # The simulation info dictionary
            }
            or
            {
                "success": False,
                "error": str  # If simulation_id not found
            }

        Constraints:
            - simulation_id must exist in the system.
        """
        sim = self.simulations.get(simulation_id)
        if sim is None:
            return { "success": False, "error": "Simulation not found" }
        return { "success": True, "data": sim }

    def get_simulation_status(self, simulation_id: str) -> dict:
        """
        Return the current status of a simulation by its id.

        Args:
            simulation_id (str): The unique identifier of the simulation.

        Returns:
            dict: {
                "success": True,
                "data": str,  # The current status of the simulation
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., simulation does not exist
            }

        Constraints:
            - The simulation with the given id must exist in the system.
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return { "success": False, "error": "Simulation does not exist" }
        return { "success": True, "data": simulation["status"] }

    def list_simulations_by_status(self, status: str) -> dict:
        """
        Retrieve all simulations filtered by their status.

        Args:
            status (str): The simulation status to filter by (e.g., "running", "completed").

        Returns:
            dict: {
                "success": True,
                "data": List[SimulationInfo],  # List of matching simulations (empty if none match)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. invalid input type
            }

        Constraints:
            - status must be a non-empty string.
        """
        if not isinstance(status, str) or not status:
            return { "success": False, "error": "Status must be a non-empty string" }

        data = [sim for sim in self.simulations.values() if sim["status"] == status]
        return { "success": True, "data": data }


    def create_simulation(
        self,
        application_id: str,
        scenario_type: str,
        scenario_parameters: Dict[str, Any]
    ) -> dict:
        """
        Instantiate (start) a new simulation for a registered application with specific scenario parameters.

        Args:
            application_id (str): ID of the application for which the simulation is created. Must exist.
            scenario_type (str): The type/category of the simulation scenario.
            scenario_parameters (Dict[str, Any]): The parameters (e.g., geolocation dict) for the simulation.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "simulation_id": <str>,
                    "message": "Simulation created successfully."
                }
            On failure:
                {
                    "success": False,
                    "error": <str>
                }

        Constraints:
            - The application_id must exist in self.applications.
            - The simulation will have status 'initialized' and no group association by default.
        """
        # Check if application exists
        if application_id not in self.applications:
            return { "success": False, "error": "Application does not exist." }

        simulation_id = str(uuid.uuid4())
        new_simulation = {
            "simulation_id": simulation_id,
            "application_id": application_id,
            "scenario_type": scenario_type,
            "scenario_parameters": scenario_parameters,
            "status": "initialized",
            "group_id": None
        }

        self.simulations[simulation_id] = new_simulation

        return {
            "success": True,
            "simulation_id": simulation_id,
            "message": "Simulation created successfully."
        }

    def associate_simulation_with_group(self, simulation_id: str, group_id: str) -> dict:
        """
        Assigns or updates a simulation's association to a group.

        Args:
            simulation_id (str): The identifier for the simulation to modify.
            group_id (str): The identifier for the group to associate with.

        Returns:
            dict: {
                "success": True,
                "message": "Simulation <simulation_id> associated with group <group_id>."
            }
            or
            {
                "success": False,
                "error": <reason: simulation or group does not exist>
            }

        Constraints:
            - Both the simulation and group must exist.
            - Simulation can belong to at most one group; this will overwrite previous association.
        """
        if simulation_id not in self.simulations:
            return {"success": False, "error": "Simulation does not exist."}

        if group_id not in self.groups:
            return {"success": False, "error": "Group does not exist."}

        self.simulations[simulation_id]['group_id'] = group_id
        return {
            "success": True,
            "message": f"Simulation {simulation_id} associated with group {group_id}."
        }

    def create_group(self, name: str, description: str, created_by: str, created_at: str) -> dict:
        """
        Create a new group for organizing simulations.

        Args:
            name (str): Name for the new group.
            description (str): Description of the group.
            created_by (str): User ID or username creating the group (authorization required).
            created_at (str): Timestamp string for group creation.

        Returns:
            dict: {
                "success": True,
                "message": "Group created",
                "group_id": <new_group_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only authorized users may create groups.
            - group_id must be unique.
        """
        # Basic authorization check
        if not created_by or created_by.strip() == "":
            return {"success": False, "error": "Authorization required: created_by missing"}

        if not name or name.strip() == "":
            return {"success": False, "error": "Group name required"}
    
        # Generate unique group_id (simple incremental or uuid-based)
        new_group_id = str(uuid.uuid4())
        while new_group_id in self.groups:
            new_group_id = str(uuid.uuid4())  # Very unlikely to loop, but ensure uniqueness

        # (Optional) Check for duplicate group name, if required
        for g in self.groups.values():
            if g['name'] == name:
                # If name uniqueness is required; if not, remove this.
                return {"success": False, "error": "Group name already exists"}

        group_info = {
            "group_id": new_group_id,
            "name": name,
            "description": description,
            "created_by": created_by,
            "created_at": created_at,
        }
        self.groups[new_group_id] = group_info

        return {
            "success": True,
            "message": "Group created",
            "group_id": new_group_id
        }

    def update_simulation_status(self, simulation_id: str, new_status: str) -> dict:
        """
        Change the status of a simulation (e.g., start, stop, complete).

        Args:
            simulation_id (str): The unique identifier of the simulation to update.
            new_status (str): The new status to set for the simulation.

        Returns:
            dict: On success:
                      { "success": True, "message": "Simulation status updated to <new_status>" }
                  On failure:
                      { "success": False, "error": "<reason>" }

        Constraints:
            - The simulation with simulation_id must exist.
            - (Not enforced) No restriction on allowed statuses unless predefined elsewhere.
        """
        if simulation_id not in self.simulations:
            return { "success": False, "error": "Simulation not found" }

        self.simulations[simulation_id]['status'] = new_status
        return {
            "success": True,
            "message": f"Simulation status updated to {new_status}"
        }

    def remove_simulation_from_group(self, simulation_id: str) -> dict:
        """
        Remove a simulation’s group association by setting group_id to None.

        Args:
            simulation_id (str): Unique identifier of the simulation to modify.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Simulation removed from group."}
                - On failure: {"success": False, "error": "Simulation not found."}

        Constraints:
            - The simulation must exist.
            - Each simulation can belong to zero or one group.
        """
        sim = self.simulations.get(simulation_id)
        if sim is None:
            return { "success": False, "error": "Simulation not found." }

        sim["group_id"] = None
        return { "success": True, "message": "Simulation removed from group." }

    def update_simulation_parameters(self, simulation_id: str, parameters: dict) -> dict:
        """
        Change the scenario parameters for an existing simulation.

        Args:
            simulation_id (str): The ID of the simulation to update.
            parameters (dict): The new scenario parameters to assign (overwriting the previous set).

        Returns:
            dict:
                On success: {"success": True, "message": "Simulation parameters updated successfully."}
                On failure: {"success": False, "error": "Simulation not found" or "Invalid parameters"}

        Constraints:
            - The simulation must exist.
            - Scenario parameters must be a dictionary.
            - Authorization is assumed/omitted (no user/session in environment).
        """
        if simulation_id not in self.simulations:
            return {"success": False, "error": "Simulation not found"}

        if not isinstance(parameters, dict):
            return {"success": False, "error": "Invalid parameters: must be a dictionary"}

        self.simulations[simulation_id]["scenario_parameters"] = parameters

        return {
            "success": True,
            "message": "Simulation parameters updated successfully."
        }

    def delete_simulation(self, simulation_id: str, user: str) -> dict:
        """
        Permanently remove a simulation from the system.

        Args:
            simulation_id (str): The unique ID of the simulation to remove.
            user (str): The identifier of the user performing the deletion.

        Returns:
            dict: {
                "success": True,
                "message": "Simulation <simulation_id> has been deleted"
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }

        Constraints:
            - Only authorized users may delete simulations.
            - Simulation must exist; otherwise, deletion fails.
        """
        # Simulated authorization check (assume 'admin' is always authorized)
        if user != "admin":
            return { "success": False, "error": "User not authorized to delete simulations." }
    
        if simulation_id not in self.simulations:
            return { "success": False, "error": "Simulation does not exist." }
    
        # Remove the simulation from the storage
        del self.simulations[simulation_id]

        return { "success": True, "message": f"Simulation {simulation_id} has been deleted" }

    def delete_group(self, group_id: str) -> dict:
        """
        Delete a group and update associated simulations to remove their group association.

        Args:
            group_id (str): The unique identifier of the group to delete.

        Returns:
            dict:
                - On success: 
                    {
                        "success": True,
                        "message": "Group <group_id> deleted. <N> simulations orphaned."
                    }
                - On error:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The group must exist.
            - Simulations referencing this group must have their `group_id` set to None (become orphaned).
            - State must remain consistent; no simulations reference deleted group.
        """
        if group_id not in self.groups:
            return { "success": False, "error": "Group does not exist" }

        # Orphan simulations referencing this group
        orphaned_count = 0
        for simulation in self.simulations.values():
            if simulation.get('group_id') == group_id:
                simulation['group_id'] = None
                orphaned_count += 1

        # Delete the group
        del self.groups[group_id]

        return { 
            "success": True, 
            "message": f"Group {group_id} deleted. {orphaned_count} simulations orphaned."
        }


class MobileAppSimulationManagementSystem(BaseEnv):
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

    def get_application_by_id(self, **kwargs):
        return self._call_inner_tool('get_application_by_id', kwargs)

    def list_applications(self, **kwargs):
        return self._call_inner_tool('list_applications', kwargs)

    def get_group_by_id(self, **kwargs):
        return self._call_inner_tool('get_group_by_id', kwargs)

    def list_groups(self, **kwargs):
        return self._call_inner_tool('list_groups', kwargs)

    def list_simulations_by_group(self, **kwargs):
        return self._call_inner_tool('list_simulations_by_group', kwargs)

    def list_simulations_by_application(self, **kwargs):
        return self._call_inner_tool('list_simulations_by_application', kwargs)

    def get_simulation_by_id(self, **kwargs):
        return self._call_inner_tool('get_simulation_by_id', kwargs)

    def get_simulation_status(self, **kwargs):
        return self._call_inner_tool('get_simulation_status', kwargs)

    def list_simulations_by_status(self, **kwargs):
        return self._call_inner_tool('list_simulations_by_status', kwargs)

    def create_simulation(self, **kwargs):
        return self._call_inner_tool('create_simulation', kwargs)

    def associate_simulation_with_group(self, **kwargs):
        return self._call_inner_tool('associate_simulation_with_group', kwargs)

    def create_group(self, **kwargs):
        return self._call_inner_tool('create_group', kwargs)

    def update_simulation_status(self, **kwargs):
        return self._call_inner_tool('update_simulation_status', kwargs)

    def remove_simulation_from_group(self, **kwargs):
        return self._call_inner_tool('remove_simulation_from_group', kwargs)

    def update_simulation_parameters(self, **kwargs):
        return self._call_inner_tool('update_simulation_parameters', kwargs)

    def delete_simulation(self, **kwargs):
        return self._call_inner_tool('delete_simulation', kwargs)

    def delete_group(self, **kwargs):
        return self._call_inner_tool('delete_group', kwargs)

