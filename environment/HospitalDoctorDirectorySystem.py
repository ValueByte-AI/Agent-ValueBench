# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict



class ContactInformation(TypedDict):
    phone: str
    email: str
    # Extend with more fields if needed (e.g., address)

class DoctorInfo(TypedDict):
    doctor_id: str
    name: str
    specialty: List[str]  # At least one specialty required
    contact_information: ContactInformation
    department_id: Optional[str]  # Zero or one department
    office_location: str
    sta: str  # Included as in provided attributes

class DepartmentInfo(TypedDict):
    department_id: str
    name: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Doctors: {doctor_id: DoctorInfo}
        self.doctors: Dict[str, DoctorInfo] = {}

        # Departments: {department_id: DepartmentInfo}
        self.departments: Dict[str, DepartmentInfo] = {}

        # Constraints:
        # - Each doctor must be associated with zero or one department (department_id may be None).
        # - Each doctor must have at least one specialty listed.
        # - Contact information for each doctor must be maintained and accurate.
        # - Searches/queries can be filtered by specialty, department, or location.

    def get_doctor_by_id(self, doctor_id: str) -> dict:
        """
        Retrieve the complete profile (DoctorInfo) of a doctor given their doctor_id.

        Args:
            doctor_id (str): Unique identifier of the doctor.

        Returns:
            dict:
                - If found: { "success": True, "data": DoctorInfo }
                - If not found: { "success": False, "error": "Doctor not found" }
        """
        doctor = self.doctors.get(doctor_id)
        if doctor is None:
            return { "success": False, "error": "Doctor not found" }
        return { "success": True, "data": doctor }

    def list_all_doctors(self) -> dict:
        """
        Retrieve a list of all doctors (with their complete profiles) in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[DoctorInfo]  # May be empty if no doctors exist
            }

        Constraints:
            - None for this operation; lists all doctors regardless of their profile content.
        """
        doctors_list = list(self.doctors.values())
        return {"success": True, "data": doctors_list}

    def filter_doctors_by_specialty(self, specialty: str) -> dict:
        """
        Return a list of doctors (DoctorInfo) matching a given specialty.

        Args:
            specialty (str): The specialty to filter doctors by.

        Returns:
            dict: {
                "success": True,
                "data": List[DoctorInfo],  # Possibly empty if no matches
            }
            or
            {
                "success": False,
                "error": str  # If input is invalid
            }

        Constraints:
            - specialty must be a non-empty string.
            - Each doctor entry is checked case-insensitively against their specialties list.
        """
        if not isinstance(specialty, str) or not specialty.strip():
            return { "success": False, "error": "Specialty must be a non-empty string." }

        target = specialty.strip().lower()
        result = [
            doctor_info for doctor_info in self.doctors.values()
            if any(s.lower() == target for s in doctor_info["specialty"])
        ]

        return { "success": True, "data": result }

    def filter_doctors_by_department(self, department_id: str) -> dict:
        """
        Returns all doctors belonging to the specified department.

        Args:
            department_id (str): The identifier of the department.

        Returns:
            dict: {
                "success": True,
                "data": List[DoctorInfo],  # May be empty if no doctors found
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Department does not exist"
            }

        Constraints:
            - department_id must correspond to an existing department.
            - Only doctors whose department_id equals the specified value are returned.
        """
        if department_id not in self.departments:
            return { "success": False, "error": "Department does not exist" }

        results = [
            doctor_info for doctor_info in self.doctors.values()
            if doctor_info.get("department_id") == department_id
        ]

        return { "success": True, "data": results }

    def filter_doctors_by_office_location(self, office_location: str) -> dict:
        """
        Return a list of doctors (DoctorInfo) whose office_location matches the specified office_location.

        Args:
            office_location (str): The office location value to filter the doctors by.

        Returns:
            dict: {
                "success": True,
                "data": List[DoctorInfo],  # All matching doctors (empty if none)
            }

        Notes:
            - Exact match is used for office_location.
            - No error if the office_location is not present for any doctor; result will be an empty list.
        """
        result = [
            doctor for doctor in self.doctors.values()
            if doctor.get("office_location") == office_location
        ]
        return { "success": True, "data": result }

    def get_department_by_id(self, department_id: str) -> dict:
        """
        Retrieve details about a department, given its department_id.

        Args:
            department_id (str): The unique identifier of the department.

        Returns:
            dict: {
                "success": True,
                "data": DepartmentInfo
            }
            or
            {
                "success": False,
                "error": "Department not found"
            }

        Constraints:
            - The provided department_id must exist in the hospital directory system.
        """
        if department_id not in self.departments:
            return {"success": False, "error": "Department not found"}
        return {"success": True, "data": self.departments[department_id]}

    def list_all_departments(self) -> dict:
        """
        Retrieve a list of all departments in the hospital.

        Returns:
            dict: {
                "success": True,
                "data": List[DepartmentInfo],  # All department profiles, may be empty
            }

        Constraints:
            - Returns all existing departments with their information.
            - No parameters or filtering.
            - Safe if there are zero departments (returns empty list).
        """
        departments_list = list(self.departments.values())
        return { "success": True, "data": departments_list }

    def add_doctor(
        self,
        doctor_id: str,
        name: str,
        specialty: list,
        contact_information: dict,
        office_location: str,
        sta: str,
        department_id: str = None
    ) -> dict:
        """
        Add a new doctor to the directory. All fields required except department_id, which may be None.

        Args:
            doctor_id (str): Unique doctor identifier.
            name (str): Full name.
            specialty (list of str): At least one specialty required.
            contact_information (dict): Must contain at least 'phone' and 'email'.
            office_location (str): Office location string.
            sta (str): Status/attribute string.
            department_id (str or None): Optional department; must exist if provided.

        Returns:
            dict: { "success": True, "message": "Doctor added successfully" }
                  or { "success": False, "error": <str> }

        Constraints:
            - doctor_id must be unique.
            - specialty must be a nonempty list of strings.
            - contact_information must have 'phone' and 'email'.
            - department_id (if provided) must exist in departments.
        """
        # Check doctor_id validity
        if not doctor_id or not isinstance(doctor_id, str):
            return { "success": False, "error": "doctor_id is required and must be a string" }
        if doctor_id in self.doctors:
            return { "success": False, "error": "doctor_id already exists" }

        # Check name
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Doctor name is required" }

        # Check specialty
        if not isinstance(specialty, list) or not specialty or not all(isinstance(s, str) and s for s in specialty):
            return { "success": False, "error": "At least one valid specialty is required" }

        # Check contact_information
        if not isinstance(contact_information, dict):
            return { "success": False, "error": "Contact information is required" }
        if 'phone' not in contact_information or 'email' not in contact_information:
            return { "success": False, "error": "Contact information must include phone and email" }
        if not contact_information['phone'] or not contact_information['email']:
            return { "success": False, "error": "Contact information must have non-empty phone and email" }

        # Check office_location
        if not office_location or not isinstance(office_location, str):
            return { "success": False, "error": "Office location is required" }

        # Check sta
        if not sta or not isinstance(sta, str):
            return { "success": False, "error": "sta is required" }

        # Check department_id if provided
        if department_id is not None:
            if department_id not in self.departments:
                return { "success": False, "error": "Given department_id does not exist" }

        # Add doctor
        self.doctors[doctor_id] = {
            "doctor_id": doctor_id,
            "name": name,
            "specialty": specialty,
            "contact_information": contact_information,
            "department_id": department_id,
            "office_location": office_location,
            "sta": sta
        }
        return { "success": True, "message": "Doctor added successfully" }

    def update_doctor_profile(
        self,
        doctor_id: str,
        updates: dict
    ) -> dict:
        """
        Edit an existing doctor's details (name, specialties, contact info, department, office location, etc.),
        enforcing constraints.

        Args:
            doctor_id (str): Unique identifier of the doctor to update.
            updates (dict): Fields and their new values (can include: name, specialty, contact_information,
                            department_id, office_location, sta).

        Returns:
            dict:
                On success: {"success": True, "message": "Doctor profile updated."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Doctor must exist (doctor_id present).
            - If 'specialty' is updated, must be a non-empty list.
            - If 'department_id' is updated, must be None or valid department_id.
            - contact_information, if provided, should include required fields ("phone", "email").
        """
        # Check doctor exists
        if doctor_id not in self.doctors:
            return {"success": False, "error": "Doctor not found."}
    
        allowed_fields = {"name", "specialty", "contact_information", "department_id", "office_location", "sta"}
        for key in updates:
            if key not in allowed_fields:
                return {"success": False, "error": f"Unknown field: {key}"}

        doc = self.doctors[doctor_id]

        # Validate specialty update
        if "specialty" in updates:
            specialty = updates["specialty"]
            if not isinstance(specialty, list) or not specialty or not all(isinstance(x, str) and x.strip() for x in specialty):
                return {"success": False, "error": "Specialty must be a non-empty list of strings."}

        # Validate department_id update
        if "department_id" in updates:
            dep = updates["department_id"]
            if dep is not None and dep not in self.departments:
                return {"success": False, "error": f"Department ID '{dep}' does not exist."}

        # Validate contact_information update
        if "contact_information" in updates:
            contact_info = updates["contact_information"]
            if not isinstance(contact_info, dict) or \
               "phone" not in contact_info or "email" not in contact_info or \
               not isinstance(contact_info["phone"], str) or \
               not isinstance(contact_info["email"], str):
                return {"success": False, "error": "Contact information must be a dict with 'phone' and 'email' fields."}

        # All checks passed; perform update
        for key, value in updates.items():
            doc[key] = value

        # Enforce that specialty remains non-empty
        if not doc["specialty"]:
            return {"success": False, "error": "Doctor must have at least one specialty."}

        return {"success": True, "message": "Doctor profile updated."}

    def remove_doctor(self, doctor_id: str) -> dict:
        """
        Remove a doctor's entry from the directory.

        Args:
            doctor_id (str): The unique identifier of the doctor to remove.

        Returns:
            dict:
                { "success": True, "message": "Doctor <doctor_id> removed from directory." }
                or
                { "success": False, "error": "Doctor not found." }

        Constraints:
            - doctor_id must exist in self.doctors to be removed.
        """
        if not doctor_id or doctor_id not in self.doctors:
            return { "success": False, "error": "Doctor not found." }

        del self.doctors[doctor_id]
        return { "success": True, "message": f"Doctor {doctor_id} removed from directory." }

    def add_department(self, department_id: str, name: str, description: str) -> dict:
        """
        Add a new department to the system.

        Args:
            department_id (str): Unique identifier for the department.
            name (str): Name of the department.
            description (str): Description of the department.

        Returns:
            dict: 
                On success: { "success": True, "message": "Department added successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - department_id must be unique (not already present in self.departments)
        """
        if department_id in self.departments:
            return { "success": False, "error": "Department ID already exists" }

        self.departments[department_id] = {
            "department_id": department_id,
            "name": name,
            "description": description
        }
        return { "success": True, "message": "Department added successfully" }

    def update_department(
        self,
        department_id: str,
        name: str = None,
        description: str = None
    ) -> dict:
        """
        Edit the attributes (name and/or description) of an existing department.

        Args:
            department_id (str): Unique identifier for the department to update (must exist).
            name (str, optional): New name for the department.
            description (str, optional): New description for the department.

        Returns:
            dict:
                {"success": True, "message": "Department updated successfully"}
                or
                {"success": False, "error": "<reason>"}

        Constraints:
            - department_id must exist in the system.
            - At least one updatable field (name or description) must be provided.
            - department_id itself cannot be changed.
        """
        if department_id not in self.departments:
            return {"success": False, "error": "Department ID does not exist"}

        if name is None and description is None:
            return {"success": False, "error": "No fields provided to update"}

        dept = self.departments[department_id]

        if name is not None:
            dept["name"] = name
        if description is not None:
            dept["description"] = description

        # Save the updated dept (dict is mutable, so this is sufficient)
        self.departments[department_id] = dept

        return {"success": True, "message": "Department updated successfully"}

    def remove_department(self, department_id: str) -> dict:
        """
        Remove a department from the system by its ID.
        Any doctors associated with this department will have their department reference cleared (set to None).
    
        Args:
            department_id (str): The unique identifier for the department to remove.

        Returns:
            dict: 
                - On success: {"success": True, "message": f"Department {department_id} removed."}
                - On failure: {"success": False, "error": "Department not found."}
    
        Constraints:
            - Doctors can have zero or one department; on removal, any doctor's department_id matching the removed one is set to None.
        """
        if department_id not in self.departments:
            return {"success": False, "error": "Department not found."}
    
        # Remove department
        del self.departments[department_id]
    
        # Disassociate any doctors assigned to this department
        for doctor in self.doctors.values():
            if doctor.get("department_id") == department_id:
                doctor["department_id"] = None

        return {"success": True, "message": f"Department {department_id} removed."}

    def assign_doctor_to_department(self, doctor_id: str, department_id: Optional[str]) -> dict:
        """
        Assign a doctor to a department (or unassign if department_id is None), ensuring only zero or one department is assigned.

        Args:
            doctor_id (str): The unique identifier of the doctor to update.
            department_id (Optional[str]): The department's unique identifier to assign, or None to unassign.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of successful assignment/unassignment.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (not found, etc.)
            }

        Constraints:
            - doctor_id must exist in the system.
            - department_id must exist in the system if not None.
            - Each doctor may only be assigned zero or one department.
        """
        if doctor_id not in self.doctors:
            return {"success": False, "error": "Doctor does not exist."}
        if department_id is not None and department_id not in self.departments:
            return {"success": False, "error": "Department does not exist."}

        self.doctors[doctor_id]["department_id"] = department_id

        if department_id is None:
            message = f"Doctor '{doctor_id}' unassigned from any department."
        else:
            dept_name = self.departments[department_id]["name"]
            message = f"Doctor '{doctor_id}' assigned to department '{dept_name}' (ID: {department_id})."
        return {"success": True, "message": message}

    def update_doctor_specialties(self, doctor_id: str, new_specialties: list[str]) -> dict:
        """
        Update the list of a doctor's specialties, ensuring at least one specialty remains.
    
        Args:
            doctor_id (str): The unique identifier for the doctor.
            new_specialties (list[str]): The new list of specialties to assign (must not be empty).
        
        Returns:
            dict: {
                "success": True,
                "message": "Doctor specialties updated successfully."
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }
        
        Constraints:
            - The specified doctor must exist.
            - The new list must contain at least one specialty (non-empty strings).
        """
        if doctor_id not in self.doctors:
            return {"success": False, "error": "Doctor ID does not exist."}
    
        # Check new_specialties is a non-empty list of non-empty strings
        if not isinstance(new_specialties, list) or not new_specialties:
            return {"success": False, "error": "At least one specialty must be provided."}
        for specialty in new_specialties:
            if not isinstance(specialty, str) or not specialty.strip():
                return {"success": False, "error": "Each specialty must be a non-empty string."}
    
        self.doctors[doctor_id]['specialty'] = new_specialties
        return {
            "success": True,
            "message": "Doctor specialties updated successfully."
        }

    def update_doctor_contact_information(self, doctor_id: str, contact_information: dict) -> dict:
        """
        Update a doctor's contact information, ensuring data is complete and accurate.

        Args:
            doctor_id (str): Unique identifier for the doctor.
            contact_information (dict): Dictionary with keys 'phone', 'email' (and possibly more).

        Returns:
            dict:
              - Success: { "success": True, "message": "Contact information updated for doctor <doctor_id>" }
              - Failure: { "success": False, "error": str (reason for failure) }

        Constraints:
            - Doctor must exist.
            - contact_information must contain non-empty 'phone' and 'email' fields.
        """
        # Check doctor exists
        if doctor_id not in self.doctors:
            return { "success": False, "error": "Doctor not found" }

        # Basic field validation
        phone = contact_information.get("phone", "")
        email = contact_information.get("email", "")
        if not isinstance(phone, str) or not phone.strip() or not isinstance(email, str) or not email.strip():
            return { "success": False, "error": "Contact information must include non-empty 'phone' and 'email'" }

        # Optionally: update only allowed fields, ignore extras
        self.doctors[doctor_id]["contact_information"] = {
            "phone": phone.strip(),
            "email": email.strip()
            # Could extend with additional allowed fields.
        }
        # If there are more allowed contact fields, merge/preserve as needed.

        return {
            "success": True,
            "message": f"Contact information updated for doctor {doctor_id}"
        }


class HospitalDoctorDirectorySystem(BaseEnv):
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

    def get_doctor_by_id(self, **kwargs):
        return self._call_inner_tool('get_doctor_by_id', kwargs)

    def list_all_doctors(self, **kwargs):
        return self._call_inner_tool('list_all_doctors', kwargs)

    def filter_doctors_by_specialty(self, **kwargs):
        return self._call_inner_tool('filter_doctors_by_specialty', kwargs)

    def filter_doctors_by_department(self, **kwargs):
        return self._call_inner_tool('filter_doctors_by_department', kwargs)

    def filter_doctors_by_office_location(self, **kwargs):
        return self._call_inner_tool('filter_doctors_by_office_location', kwargs)

    def get_department_by_id(self, **kwargs):
        return self._call_inner_tool('get_department_by_id', kwargs)

    def list_all_departments(self, **kwargs):
        return self._call_inner_tool('list_all_departments', kwargs)

    def add_doctor(self, **kwargs):
        return self._call_inner_tool('add_doctor', kwargs)

    def update_doctor_profile(self, **kwargs):
        return self._call_inner_tool('update_doctor_profile', kwargs)

    def remove_doctor(self, **kwargs):
        return self._call_inner_tool('remove_doctor', kwargs)

    def add_department(self, **kwargs):
        return self._call_inner_tool('add_department', kwargs)

    def update_department(self, **kwargs):
        return self._call_inner_tool('update_department', kwargs)

    def remove_department(self, **kwargs):
        return self._call_inner_tool('remove_department', kwargs)

    def assign_doctor_to_department(self, **kwargs):
        return self._call_inner_tool('assign_doctor_to_department', kwargs)

    def update_doctor_specialties(self, **kwargs):
        return self._call_inner_tool('update_doctor_specialties', kwargs)

    def update_doctor_contact_information(self, **kwargs):
        return self._call_inner_tool('update_doctor_contact_information', kwargs)

