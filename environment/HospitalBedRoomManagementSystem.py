# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict



# Represents a hospital room
class RoomInfo(TypedDict):
    room_id: str  # corrected from 'oom_id'
    room_type: str
    capacity: int
    status: str   # corrected from 'sta'

# Represents a bed within a room
class BedInfo(TypedDict):
    bed_id: str   # corrected from 'd_id'
    room_id: str
    status: str  # e.g., 'available', 'occupied', 'out-of-service'
    assigned_patient_id: Optional[str]  # patient_id or None if no assignment

# Represents a patient
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    admission_status: str
    assigned_bed_id: Optional[str]  # bed_id or None if not assigned

class _GeneratedEnvImpl:
    def __init__(self):
        # Rooms: {room_id: RoomInfo}
        self.rooms: Dict[str, RoomInfo] = {}
        # Beds: {bed_id: BedInfo}
        self.beds: Dict[str, BedInfo] = {}
        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # === Constraints ===
        # - Each bed can have at most one patient assigned at any time.
        # - Beds can only be assigned to patients if their status is "available".
        # - The number of occupied beds in a room cannot exceed the room's capacity.
        # - Assignments cannot proceed if there are fewer available beds than patients to admit.

    def list_rooms(self) -> dict:
        """
        Retrieve all rooms with their types, capacities, and operational statuses.

        Returns:
            dict: {
                "success": True,
                "data": List[RoomInfo],  # List of all room information; may be empty if none exist
            }
        """
        rooms_list = list(self.rooms.values())
        return { "success": True, "data": rooms_list }

    def get_room_by_id(self, room_id: str) -> dict:
        """
        Retrieve detailed information about a specific room by its room_id.

        Args:
            room_id (str): The identifier of the room.

        Returns:
            dict: {
                "success": True,
                "data": RoomInfo,  # Room's metadata if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. room not found
            }

        Constraints:
            - The room_id must exist in the system.
        """
        room = self.rooms.get(room_id)
        if room is None:
            return {"success": False, "error": "Room not found"}
        return {"success": True, "data": room}

    def list_beds_in_room(self, room_id: str) -> dict:
        """
        List all beds and their statuses assigned to a given room.

        Args:
            room_id (str): The unique identifier of the room.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": List[BedInfo]   # all beds in the room (may be empty)
                }
                On failure (room not found):
                {
                    "success": False,
                    "error": str  # "Room does not exist"
                }

        Constraints:
            - Room must exist in the system (room_id in self.rooms).
        """
        if room_id not in self.rooms:
            return { "success": False, "error": "Room does not exist" }

        beds_in_room = [
            bed_info for bed_info in self.beds.values()
            if bed_info["room_id"] == room_id
        ]

        return { "success": True, "data": beds_in_room }

    def list_all_beds(self) -> dict:
        """
        Retrieve all beds in the system, with their status and assigned_patient_id.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BedInfo],  # list of all beds in the system
            }

        Edge Cases:
            - If there are no beds, returns an empty list in "data".
        """
        all_beds = list(self.beds.values())
        return { "success": True, "data": all_beds }

    def list_available_beds(self) -> dict:
        """
        List all beds across the hospital whose status is "available".

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BedInfo],  # List of all available beds (may be empty)
            }

        Notes:
            - If there are no available beds, an empty list is returned, still with success = True.
            - No permission, assignment, or capacity constraints are considered in this query.
        """
        available_beds = [
            bed_info for bed_info in self.beds.values()
            if bed_info["status"] == "available"
        ]
        return { "success": True, "data": available_beds }

    def list_occupied_beds(self) -> dict:
        """
        List all beds whose status is 'occupied'.

        Returns:
            dict: {
                "success": True,
                "data": List[BedInfo]   # List may be empty if no beds are occupied.
            }

        Constraints:
            - No special constraints (read-only, info query).
            - If there are no occupied beds, returns empty list with success.
        """
        occupied_beds = [
            bed_info for bed_info in self.beds.values()
            if bed_info["status"] == "occupied"
        ]
        return {
            "success": True,
            "data": occupied_beds
        }

    def get_bed_by_id(self, bed_id: str) -> dict:
        """
        Retrieve the full details of a bed given its bed_id.

        Args:
            bed_id (str): The unique identifier for the bed.

        Returns:
            dict: {
                "success": True,
                "data": BedInfo  # Bed information including room_id, status, assigned_patient_id
            }
            OR
            {
                "success": False,
                "error": str  # If no such bed exists
            }
        """
        bed = self.beds.get(bed_id)
        if bed is None:
            return { "success": False, "error": "Bed not found" }
        return { "success": True, "data": bed }

    def count_available_beds(self, room_id: Optional[str] = None) -> dict:
        """
        Count the number of available beds in the hospital, or in a specific room.

        Args:
            room_id (Optional[str]): If specified, restrict the count to beds in the given room.

        Returns:
            dict: {
                "success": True,
                "data": int,  # Number of available beds
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g. room not found
            }

        Constraints:
            - If room_id is provided, the room must exist.
        """
        if room_id is not None:
            if room_id not in self.rooms:
                return { "success": False, "error": "Room not found" }
            count = sum(
                1 for bed in self.beds.values()
                if bed["room_id"] == room_id and bed["status"] == "available"
            )
        else:
            count = sum(
                1 for bed in self.beds.values()
                if bed["status"] == "available"
            )
        return { "success": True, "data": count }

    def list_patients(self) -> dict:
        """
        Retrieve all patients and their admission/bed assignment status.

        Returns:
            dict:
              {
                "success": True,
                "data": List[PatientInfo]  # All PatientInfo objects in the system (may be empty if no patients)
              }

        Constraints:
            - Always succeeds; returns empty list if no patients are present.
        """
        result = list(self.patients.values())
        return { "success": True, "data": result }

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve all patient records matching the given name.

        Args:
            name (str): The patient's name to search for.

        Returns:
            dict: 
                {
                  "success": True,
                  "data": List[PatientInfo], # List of patient records matching the name (may be empty list)
                }
              or
                {
                  "success": False,
                  "error": str # If name is not provided
                }

        Constraints:
            - If multiple patients share the same name, returns all matches.
            - Name search is case-sensitive.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Patient name must be provided"}

        matches = [
            patient for patient in self.patients.values()
            if patient["name"] == name
        ]

        return {"success": True, "data": matches}

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve a patient's full record by patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo,  # Patient record if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if patient not found
            }

        Constraints:
            - patient_id must exist in the system.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return {"success": False, "error": "Patient not found"}
        return {"success": True, "data": patient}

    def list_unassigned_patients(self) -> dict:
        """
        List all patients in the system who are not currently assigned to any bed.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # List of patients with assigned_bed_id == None (possibly empty)
            }
        """
        unassigned = [
            patient for patient in self.patients.values()
            if patient["assigned_bed_id"] is None
        ]
        return { "success": True, "data": unassigned }

    def get_room_occupancy(self, room_id: str) -> dict:
        """
        Obtain the current occupancy (number of occupied beds) for a specific room.

        Args:
            room_id (str): The unique identifier of the room.

        Returns:
            dict:
                {"success": True, "data": occupied_count}
                or
                {"success": False, "error": "<reason>"}
        Constraints:
            - Room must exist in the system.
            - "Occupied" means bed status is "occupied" and assigned_patient_id is not None.
        """
        if room_id not in self.rooms:
            return {"success": False, "error": "Room not found"}

        occupied_count = 0
        for bed in self.beds.values():
            if bed["room_id"] == room_id and bed["status"] == "occupied" and bed["assigned_patient_id"] is not None:
                occupied_count += 1

        return {"success": True, "data": occupied_count}

    def check_room_capacity_constraint(self, room_id: str) -> dict:
        """
        Verify if a room has fewer occupied beds than its defined capacity.

        Args:
            room_id (str): The room identifier to check.

        Returns:
            dict:
                success: True if operation successful; False if error.
                data: {
                    constraint_satisfied: bool,  # True if occupied beds < capacity
                    occupied_beds: int,          # The count of occupied beds in the room
                    capacity: int                # The room's defined bed capacity
                }
                error: Reason for failure if not successful.

        Constraints:
            - Room must exist in the system.
            - Occupied beds (with status "occupied") must be strictly less than capacity.
        """
        room = self.rooms.get(room_id)
        if room is None:
            return {"success": False, "error": "Room not found"}

        capacity = room.get("capacity", 0)
        occupied_beds = sum(
            1 for bed in self.beds.values()
            if bed["room_id"] == room_id and bed["status"] == "occupied"
        )
        constraint_satisfied = occupied_beds < capacity

        return {
            "success": True,
            "data": {
                "constraint_satisfied": constraint_satisfied,
                "occupied_beds": occupied_beds,
                "capacity": capacity,
            }
        }

    def check_available_bed_count(self, patient_count: int) -> dict:
        """
        Check whether the number of available beds can accommodate a given number of patients.

        Args:
            patient_count (int): The number of patients to check for available beds.
    
        Returns:
            dict: {
                "success": True,
                "data": {
                    "sufficient": bool,  # True if available bed count >= patient_count
                    "available_bed_count": int
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of input error, e.g., invalid patient_count
            }

        Constraints:
            - patient_count must be a non-negative integer.
        """
        if not isinstance(patient_count, int) or patient_count < 0:
            return {"success": False, "error": "patient_count must be a non-negative integer"}

        available_beds = [bed for bed in self.beds.values() if bed["status"] == "available"]
        available_count = len(available_beds)
        sufficient = available_count >= patient_count

        return {
            "success": True,
            "data": {
                "sufficient": sufficient,
                "available_bed_count": available_count
            }
        }

    def assign_bed_to_patient(self, bed_id: str, patient_id: str) -> dict:
        """
        Assign an available bed to a patient and update relevant status fields.

        Args:
            bed_id (str): The ID of the bed to assign.
            patient_id (str): The ID of the patient to assign.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Patient <patient_id> assigned to bed <bed_id>."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Bed must exist and be 'available'.
            - Patient must exist and not already have a bed assigned.
            - Bed must not be already assigned (redundant with 'available' check).
            - The room of the bed must not be at or over capacity.
            - Room must be 'available'.
        """
        bed = self.beds.get(bed_id)
        if not bed:
            return {"success": False, "error": "Bed does not exist."}

        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient does not exist."}

        room = self.rooms.get(bed['room_id'])
        if not room:
            return {"success": False, "error": f"Room for bed {bed_id} does not exist."}

        if room['status'] not in {'available', 'open'}:
            return {"success": False, "error": f"Room {room['room_id']} is not available."}

        if bed['status'] != 'available':
            return {"success": False, "error": f"Bed {bed_id} is not available."}

        if bed['assigned_patient_id'] is not None:
            return {"success": False, "error": f"Bed {bed_id} is already assigned to a patient."}

        if patient.get('assigned_bed_id'):
            return {"success": False, "error": f"Patient {patient_id} is already assigned to a bed."}

        # Enforce room capacity constraint
        room_beds = [
            b for b in self.beds.values() if b['room_id'] == room['room_id']
        ]
        occupied_beds = [
            b for b in room_beds if b['status'] == 'occupied'
        ]
        if len(occupied_beds) >= room['capacity']:
            return {"success": False, "error": f"Room {room['room_id']} is at full capacity."}

        # Assign the patient to the bed
        bed['status'] = 'occupied'
        bed['assigned_patient_id'] = patient_id

        patient['admission_status'] = 'admitted'
        patient['assigned_bed_id'] = bed_id

        return {
            "success": True,
            "message": f"Patient {patient_id} assigned to bed {bed_id}."
        }

    def unassign_patient_from_bed(self, bed_id: str) -> dict:
        """
        Unassign the patient currently assigned to the given bed.
        This marks the bed as 'available' and updates the patient record (if any).

        Args:
            bed_id (str): The bed identifier from which to remove the patient assignment.

        Returns:
            dict: 
              Success: { "success": True, "message": "Patient unassigned from bed and bed marked as available." }
              Failure: { "success": False, "error": <reason> }

        Constraints:
            - The bed must exist.
            - A patient must be currently assigned to the bed.
            - Updates bed and patient state accordingly.
        """
        if bed_id not in self.beds:
            return { "success": False, "error": "Bed does not exist." }

        bed = self.beds[bed_id]
        if bed["assigned_patient_id"] is None:
            return { "success": False, "error": "No patient is currently assigned to this bed." }

        patient_id = bed["assigned_patient_id"]

        # Unassign patient from bed
        bed["assigned_patient_id"] = None
        bed["status"] = "available"

        # Unassign bed from patient record if patient exists
        if patient_id in self.patients:
            self.patients[patient_id]["assigned_bed_id"] = None

        return { "success": True, "message": "Patient unassigned from bed and bed marked as available." }

    def admit_new_patient(self, patient_id: str, name: str) -> dict:
        """
        Add a new patient to the system.

        Args:
            patient_id (str): Unique identifier for the new patient.
            name (str): Patient's name.

        Returns:
            dict: {
                "success": True,
                "message": "Patient <name> admitted with ID <patient_id>."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - patient_id must be unique (not already present).
            - name must be non-empty.
            - New patient admission_status is set to 'admitted'.
            - assigned_bed_id is None initially.
        """
        if not patient_id or not isinstance(patient_id, str):
            return { "success": False, "error": "Invalid or missing patient_id." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid or missing patient name." }
        if patient_id in self.patients:
            return { "success": False, "error": f"Patient ID {patient_id} already exists." }
    
        new_patient: PatientInfo = {
            "patient_id": patient_id,
            "name": name,
            "admission_status": "admitted",
            "assigned_bed_id": None
        }
        self.patients[patient_id] = new_patient

        return { "success": True, "message": f"Patient {name} admitted with ID {patient_id}." }

    def set_bed_status(self, bed_id: str, status: str) -> dict:
        """
        Change the status of a bed to 'available', 'occupied', or 'out-of-service'.

        Args:
            bed_id (str): The bed to modify.
            status (str): New status. Must be one of 'available', 'occupied', or 'out-of-service'.

        Returns:
            dict: {
                "success": True,
                "message": "Bed status updated to <status> for bed <bed_id>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Bed must exist.
            - Status must be valid.
            - If setting to 'available' or 'out-of-service', and a patient is assigned, unassign the patient from the bed and update patient assignment.
            - If setting to 'occupied', bed must have a patient assigned, otherwise it's an error.
        """
        valid_statuses = {'available', 'occupied', 'out-of-service'}
        if bed_id not in self.beds:
            return { "success": False, "error": "Bed not found" }

        if status not in valid_statuses:
            return { "success": False, "error": f"Invalid status '{status}'. Must be one of {valid_statuses}" }

        bed = self.beds[bed_id]

        # If setting to 'occupied', ensure a patient is assigned
        if status == 'occupied':
            if bed["assigned_patient_id"] is None:
                return { "success": False, "error": "Cannot set bed to 'occupied' as no patient is assigned to this bed." }

        # If setting to 'available' or 'out-of-service', and a patient is assigned, unassign
        if status in {'available', 'out-of-service'}:
            assigned_patient_id = bed["assigned_patient_id"]
            if assigned_patient_id is not None:
                # Unassign bed from patient also
                if assigned_patient_id in self.patients:
                    self.patients[assigned_patient_id]["assigned_bed_id"] = None
                bed["assigned_patient_id"] = None

        bed["status"] = status

        return {
            "success": True,
            "message": f"Bed status updated to {status} for bed {bed_id}"
        }

    def set_room_status(self, room_id: str, new_status: str) -> dict:
        """
        Change the status of a specified room.

        Args:
            room_id (str): The unique identifier of the room to update.
            new_status (str): The status to set, e.g., 'open', 'closed', 'closed to admissions'.
        
        Returns:
            dict: 
                On success: { "success": True, "message": "Room <room_id> status updated to <new_status>." }
                On error:   { "success": False, "error": "Room not found." }
    
        Constraints:
            - Room must exist to change its status.
            - No restriction on accepted status values unless enforced in business logic.
        """
        room = self.rooms.get(room_id)
        if room is None:
            return { "success": False, "error": "Room not found." }

        room['status'] = new_status
        return { "success": True, "message": f"Room {room_id} status updated to {new_status}." }

    def move_patient_to_bed(self, patient_id: str, new_bed_id: str) -> dict:
        """
        Re-assign a patient from their current bed to another bed, updating all relevant fields
        (beds' statuses and assigned_patient_id; patient's assigned_bed_id).

        Args:
            patient_id (str): The ID of the patient to move.
            new_bed_id (str): The ID of the bed to assign the patient to.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Patient moved to new bed." }
                - On failure: { "success": False, "error": "Description" }

        Constraints:
            - Patient must exist and currently be assigned to a bed.
            - New bed must exist and be 'available'.
            - Update involved bed and patient records atomically.
            - Cannot move to the same bed (no-op or error).
        """
        # Check patient existence
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient does not exist." }

        current_bed_id = patient.get("assigned_bed_id")
        if not current_bed_id:
            return { "success": False, "error": "Patient is not currently assigned to any bed." }

        # Check new bed
        new_bed = self.beds.get(new_bed_id)
        if not new_bed:
            return { "success": False, "error": "Target bed does not exist." }

        if new_bed["status"] != "available":
            return { "success": False, "error": "Target bed is not available." }
    
        if new_bed_id == current_bed_id:
            return { "success": False, "error": "Patient is already assigned to the specified bed." }

        # All checks pass, proceed to move
        # 1. Update current bed: set status to available, assigned_patient_id to None
        current_bed = self.beds.get(current_bed_id)
        if current_bed:
            current_bed["status"] = "available"
            current_bed["assigned_patient_id"] = None

        # 2. Update new bed: set status to occupied, assigned_patient_id to patient_id
        new_bed["status"] = "occupied"
        new_bed["assigned_patient_id"] = patient_id

        # 3. Update patient's assigned_bed_id
        patient["assigned_bed_id"] = new_bed_id

        return { "success": True, "message": "Patient moved to new bed." }

    def discharge_patient(self, patient_id: str) -> dict:
        """
        Discharge a patient from the hospital: mark admission ended and release their bed.

        Args:
            patient_id (str): The unique identifier for the patient to discharge.

        Returns:
            dict: {
                "success": True,
                "message": "Patient <name> (<patient_id>) discharged and bed <bed_id> released.",
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
          - Patient must exist.
          - Patient must be admitted and have a bed assigned.
          - Bed must exist and be assigned to this patient.
          - Bed is released (status set to "available", assigned_patient_id is None).
          - Patient admission_status set to "discharged", assigned_bed_id set to None.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": f"Patient {patient_id} does not exist."}

        if patient["admission_status"] != "admitted":
            return {"success": False, "error": f"Patient {patient['name']} ({patient_id}) is not currently admitted."}

        bed_id = patient.get("assigned_bed_id")
        if not bed_id:
            return {"success": False, "error": f"Patient {patient['name']} ({patient_id}) is not assigned to any bed."}

        bed = self.beds.get(bed_id)
        if not bed:
            return {"success": False, "error": f"Assigned bed {bed_id} does not exist for patient {patient['name']} ({patient_id})."}

        if bed.get("assigned_patient_id") != patient_id:
            return {"success": False, "error": f"Bed {bed_id} is not assigned to patient {patient['name']} ({patient_id}), data inconsistency."}

        # Perform discharge
        patient["admission_status"] = "discharged"
        patient["assigned_bed_id"] = None
        bed["status"] = "available"
        bed["assigned_patient_id"] = None

        return {
            "success": True,
            "message": f"Patient {patient['name']} ({patient_id}) discharged and bed {bed_id} released."
        }


class HospitalBedRoomManagementSystem(BaseEnv):
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
        def _normalize_optional_ref(value):
            if value is None:
                return None
            if isinstance(value, str) and value.strip().lower() in {"", "none", "null"}:
                return None
            return value
        for key, value in init_config.items():
            copied_value = copy.deepcopy(value)
            if key == "beds" and isinstance(copied_value, dict):
                for bed in copied_value.values():
                    if isinstance(bed, dict):
                        bed["assigned_patient_id"] = _normalize_optional_ref(bed.get("assigned_patient_id"))
            if key == "patients" and isinstance(copied_value, dict):
                for patient in copied_value.values():
                    if isinstance(patient, dict):
                        patient["assigned_bed_id"] = _normalize_optional_ref(patient.get("assigned_bed_id"))
            setattr(env, key, copied_value)

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

    def list_rooms(self, **kwargs):
        return self._call_inner_tool('list_rooms', kwargs)

    def get_room_by_id(self, **kwargs):
        return self._call_inner_tool('get_room_by_id', kwargs)

    def list_beds_in_room(self, **kwargs):
        return self._call_inner_tool('list_beds_in_room', kwargs)

    def list_all_beds(self, **kwargs):
        return self._call_inner_tool('list_all_beds', kwargs)

    def list_available_beds(self, **kwargs):
        return self._call_inner_tool('list_available_beds', kwargs)

    def list_occupied_beds(self, **kwargs):
        return self._call_inner_tool('list_occupied_beds', kwargs)

    def get_bed_by_id(self, **kwargs):
        return self._call_inner_tool('get_bed_by_id', kwargs)

    def count_available_beds(self, **kwargs):
        return self._call_inner_tool('count_available_beds', kwargs)

    def list_patients(self, **kwargs):
        return self._call_inner_tool('list_patients', kwargs)

    def get_patient_by_name(self, **kwargs):
        return self._call_inner_tool('get_patient_by_name', kwargs)

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def list_unassigned_patients(self, **kwargs):
        return self._call_inner_tool('list_unassigned_patients', kwargs)

    def get_room_occupancy(self, **kwargs):
        return self._call_inner_tool('get_room_occupancy', kwargs)

    def check_room_capacity_constraint(self, **kwargs):
        return self._call_inner_tool('check_room_capacity_constraint', kwargs)

    def check_available_bed_count(self, **kwargs):
        return self._call_inner_tool('check_available_bed_count', kwargs)

    def assign_bed_to_patient(self, **kwargs):
        return self._call_inner_tool('assign_bed_to_patient', kwargs)

    def unassign_patient_from_bed(self, **kwargs):
        return self._call_inner_tool('unassign_patient_from_bed', kwargs)

    def admit_new_patient(self, **kwargs):
        return self._call_inner_tool('admit_new_patient', kwargs)

    def set_bed_status(self, **kwargs):
        return self._call_inner_tool('set_bed_status', kwargs)

    def set_room_status(self, **kwargs):
        return self._call_inner_tool('set_room_status', kwargs)

    def move_patient_to_bed(self, **kwargs):
        return self._call_inner_tool('move_patient_to_bed', kwargs)

    def discharge_patient(self, **kwargs):
        return self._call_inner_tool('discharge_patient', kwargs)
