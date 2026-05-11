# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import datetime



class VehicleInfo(TypedDict):
    registration_number: str
    VIN: str
    make: str
    model: str
    year: int
    color: str
    engine_number: str
    vehicle_type: str
    status: str

class OwnerInfo(TypedDict):
    owner_id: str
    name: str
    address: str
    date_of_birth: str
    license_number: str
    contact_information: str

class RegistrationInfo(TypedDict):
    registration_number: str
    vehicle_id: str
    owner_id: str
    registration_date: str
    expiration_date: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment: Motor vehicle registration database.
        """

        # Vehicles: {registration_number: VehicleInfo}
        self.vehicles: Dict[str, VehicleInfo] = {}

        # Owners: {owner_id: OwnerInfo}
        self.owners: Dict[str, OwnerInfo] = {}

        # Registrations: {registration_number: RegistrationInfo}
        self.registrations: Dict[str, RegistrationInfo] = {}

        # Constraints:
        # - Each registration_number must be unique across all vehicles.
        # - A vehicle can only have one active (current) registration at a time.
        # - Only authorized users can update, add, or transfer vehicle records.
        # - Expired or revoked registrations cannot be transferred.
        # - All vehicles must have a valid VIN and registration_number to be in the database.

    def _get_vehicle_and_vin(self, registration_number: str = None, VIN: str = None):
        vehicle = None
        vehicle_vin = None

        if registration_number:
            vehicle = self.vehicles.get(registration_number)
            if vehicle:
                vehicle_vin = vehicle.get("VIN")

        if VIN and vehicle is None:
            for candidate in self.vehicles.values():
                if candidate.get("VIN") == VIN:
                    vehicle = candidate
                    vehicle_vin = candidate.get("VIN")
                    break

        if vehicle is not None and VIN and vehicle_vin != VIN:
            return None, None
        return vehicle, vehicle_vin

    def get_vehicle_by_registration(self, registration_number: str) -> dict:
        """
        Retrieve all details of a vehicle by its registration number.

        Args:
            registration_number (str): The vehicle's unique registration identifier.

        Returns:
            dict: {
                "success": True,
                "data": VehicleInfo  # Vehicle's full details
            }
            or
            {
                "success": False,
                "error": str  # Error message such as not found
            }

        Constraints:
            - registration_number must exist in the database.
        """
        vehicle = self.vehicles.get(registration_number)
        if not vehicle:
            return {
                "success": False,
                "error": "Vehicle with this registration number does not exist"
            }
        return {
            "success": True,
            "data": vehicle
        }

    def get_vehicle_by_vin(self, vin: str) -> dict:
        """
        Retrieve vehicle details using the VIN (Vehicle Identification Number).

        Args:
            vin (str): The vehicle's VIN.

        Returns:
            dict: {
                "success": True,
                "data": VehicleInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - VIN must be present and valid for the vehicle.
            - If VIN is not found, operation fails.
        """
        for vehicle in self.vehicles.values():
            if vehicle.get('VIN') == vin:
                return {"success": True, "data": vehicle}

        return {"success": False, "error": "No vehicle found with the provided VIN."}

    def list_vehicles_by_owner(self, owner_id: str = None, name: str = None) -> dict:
        """
        Retrieves all vehicles associated with a specific owner, identified by owner_id or name.

        Args:
            owner_id (str, optional): The unique owner identifier.
            name (str, optional): The owner's name (may match multiple owners).

        Returns:
            dict: {
                "success": True,
                "data": List[VehicleInfo],  # List of matched vehicles (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message describing the issue
            }

        Constraints:
            - At least one of owner_id or name must be specified.
            - If name is used, and matches multiple owners, returns vehicles for all such owners.
        """
        # Input validation
        if not owner_id and not name:
            return {"success": False, "error": "Must provide either owner_id or name to search."}

        matching_owner_ids = set()
        if owner_id:
            if owner_id not in self.owners:
                return {"success": False, "error": f"Owner with id '{owner_id}' not found."}
            matching_owner_ids.add(owner_id)
        elif name:
            for oid, oinfo in self.owners.items():
                if oinfo["name"] == name:
                    matching_owner_ids.add(oid)
            if not matching_owner_ids:
                return {"success": False, "error": f"No owner found with name '{name}'."}

        # Gather all vehicles for each matching owner via registrations
        vehicles_set = set()
        for reg in self.registrations.values():
            if reg["owner_id"] in matching_owner_ids:
                vehicles_set.add(reg["registration_number"])

        vehicles_list = []
        for reg_num in vehicles_set:
            vinfo = self.vehicles.get(reg_num)
            if vinfo:
                vehicles_list.append(vinfo)

        return {"success": True, "data": vehicles_list}

    def get_owner_by_id(self, owner_id: str) -> dict:
        """
        Retrieve owner information using the specified owner_id.

        Args:
            owner_id (str): Unique identifier for the owner.

        Returns:
            dict: {
                "success": True,
                "data": OwnerInfo  # If the owner is found
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Owner not found"
            }

        Constraints:
            - owner_id must exist in the database.
        """
        owner = self.owners.get(owner_id)
        if owner is None:
            return { "success": False, "error": "Owner not found" }
        return { "success": True, "data": owner }

    def get_owner_by_license(self, license_number: str) -> dict:
        """
        Retrieve owner information given their driver's license number.

        Args:
            license_number (str): The driver's license number to look up.

        Returns:
            dict:
              - On success: {"success": True, "data": OwnerInfo}
              - On failure: {"success": False, "error": "Owner not found with given license number."}
        Constraints:
            - License number should be unique in the system.
        """

        for owner in self.owners.values():
            if owner.get("license_number") == license_number:
                return { "success": True, "data": owner }
        return { "success": False, "error": "Owner not found with given license number." }

    def get_registration_by_number(self, registration_number: str) -> dict:
        """
        Retrieve the full registration record for the given registration number.

        Args:
            registration_number (str): The unique registration number to look up.

        Returns:
            dict: {
                "success": True,
                "data": RegistrationInfo
            }
            or
            {
                "success": False,
                "error": "Registration number not found"
            }

        Constraints:
            - The registration_number must exist in the registrations database.
        """
        registration = self.registrations.get(registration_number)
        if registration is None:
            return {
                "success": False,
                "error": "Registration number not found"
            }
        return {
            "success": True,
            "data": registration
        }

    def list_active_registrations(self) -> dict:
        """
        Retrieve all registrations that have an 'active' status.

        Returns:
            dict: {
                "success": True,
                "data": List[RegistrationInfo]  # List of active registration info (may be empty)
            }
        """
        active_regs = [
            reg_info for reg_info in self.registrations.values()
            if reg_info.get("status", "").lower() == "active"
        ]
        return { "success": True, "data": active_regs }

    def get_registration_status(self, registration_number: str) -> dict:
        """
        Retrieve the current status of a registration (e.g., active, expired, revoked).
    
        Args:
            registration_number (str): The registration number to query.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": {
                        "registration_number": str,
                        "status": str
                    }
                }
                On failure: {
                    "success": False,
                    "error": "Registration number not found"
                }

        Constraints:
            - The registration_number must exist in the system.
        """
        reg = self.registrations.get(registration_number)
        if not reg:
            return { "success": False, "error": "Registration number not found" }
        return {
            "success": True,
            "data": {
                "registration_number": registration_number,
                "status": reg["status"]
            }
        }

    def get_vehicle_registration_history(self, registration_number: str = None, VIN: str = None) -> dict:
        """
        Retrieve all past and current registration records for a given vehicle, using either registration_number or VIN.

        Args:
            registration_number (str, optional): Vehicle's registration number.
            VIN (str, optional): Vehicle's VIN.

        Returns:
            dict:
                - If successful:
                    { "success": True, "data": List[RegistrationInfo] }
                - On error:
                    { "success": False, "error": str }

        Constraints:
            - At least one of registration_number or VIN must be provided.
            - If both are provided, they must correspond to the same vehicle.
            - Vehicle must exist.
        """
        # Input validation
        if not registration_number and not VIN:
            return { "success": False, "error": "At least registration_number or VIN must be provided." }

        vehicle, vehicle_vin = self._get_vehicle_and_vin(registration_number=registration_number, VIN=VIN)
        if registration_number and not vehicle:
            return { "success": False, "error": "Vehicle with the given registration_number not found." }
        if VIN and not vehicle:
            return { "success": False, "error": "Vehicle with the given VIN not found." }
        if vehicle is None or vehicle_vin is None:
            return { "success": False, "error": "Vehicle must exist." }

        registration_number = vehicle["registration_number"]
        records = [
            reg for reg in self.registrations.values()
            if reg.get("vehicle_id") == vehicle_vin
            or reg.get("registration_number") == registration_number
        ]
        return { "success": True, "data": records }

    def register_new_vehicle(self,
                            registration_number: str,
                            VIN: str,
                            make: str,
                            model: str,
                            year: int,
                            color: str,
                            engine_number: str,
                            vehicle_type: str,
                            owner_id: str,
                            registration_date: str,
                            expiration_date: str,
                            status: str = "active") -> dict:
        """
        Add a new vehicle and its initial registration to the system.

        Args:
            registration_number (str): Unique registration number for the vehicle.
            VIN (str): Unique vehicle identification number.
            make (str): Vehicle make (manufacturer).
            model (str): Vehicle model.
            year (int): Model year.
            color (str): Color of the vehicle.
            engine_number (str): Engine number.
            vehicle_type (str): Type/category of the vehicle.
            owner_id (str): Existing owner ID.
            registration_date (str): Registration start date.
            expiration_date (str): Registration expiration date.
            status (str): Registration status ('active' by default).

        Returns:
            dict: {
                "success": True,
                "message": "Vehicle and registration created."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - registration_number must be unique; not in vehicles or registrations.
            - VIN must be unique; not in vehicles.
            - owner_id must exist.
            - Registration status is usually 'active'.
            - All fields required and not empty/None.
        """

        required_vehicle_fields = [
            registration_number, VIN, make, model, year, color, engine_number, vehicle_type, owner_id
        ]
        required_registration_fields = [
            registration_date, expiration_date, status
        ]

        # Check presence of all required fields
        if any(x is None or (isinstance(x, str) and not x.strip()) for x in required_vehicle_fields + required_registration_fields):
            return { "success": False, "error": "All fields are required and must be non-empty." }

        # Check uniqueness of registration_number
        if registration_number in self.vehicles or registration_number in self.registrations:
            return { "success": False, "error": "Registration number already exists." }

        # Check uniqueness of VIN
        for vinfo in self.vehicles.values():
            if vinfo["VIN"] == VIN:
                return { "success": False, "error": "VIN already exists for another vehicle." }

        # Check owner exists
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner does not exist." }

        # Create VehicleInfo
        vehicle_info: VehicleInfo = {
            "registration_number": registration_number,
            "VIN": VIN,
            "make": make,
            "model": model,
            "year": year,
            "color": color,
            "engine_number": engine_number,
            "vehicle_type": vehicle_type,
            "status": status
        }

        self.vehicles[registration_number] = vehicle_info

        # Create RegistrationInfo (use VIN as vehicle_id to avoid ambiguity)
        registration_info: RegistrationInfo = {
            "registration_number": registration_number,
            "vehicle_id": VIN,
            "owner_id": owner_id,
            "registration_date": registration_date,
            "expiration_date": expiration_date,
            "status": status
        }

        self.registrations[registration_number] = registration_info

        return { "success": True, "message": "Vehicle and registration created." }

    def update_vehicle_details(self, registration_number: str, kwargs: dict = None, **extra_kwargs) -> dict:
        """
        Modify details for an existing vehicle (e.g., color, make, model).

        Args:
            registration_number (str): Vehicle's unique registration number.
            **kwargs: Fields and new values to update (e.g., color="Red", model="Accord")

        Returns:
            dict:
                {"success": True, "message": "Vehicle details updated successfully."}
                or
                {"success": False, "error": "reason"}

        Constraints:
            - Vehicle must exist.
            - Cannot modify registration_number or VIN.
            - Must update at least one allowed field.
            - Allowed mutable fields: make, model, year, color, engine_number, vehicle_type, status
        """
        # Check vehicle exists
        if registration_number not in self.vehicles:
            return {"success": False, "error": "Vehicle with registration_number does not exist."}

        # List of updatable fields
        mutable_fields = {"make", "model", "year", "color", "engine_number", "vehicle_type", "status"}

        # Remove attempts to update forbidden fields
        combined_updates = {}
        if isinstance(kwargs, dict):
            combined_updates.update(kwargs)
        combined_updates.update(extra_kwargs)
        update_fields = {k: v for k, v in combined_updates.items() if k in mutable_fields}

        if not update_fields:
            return {"success": False, "error": "No valid fields provided to update."}

        vehicle = self.vehicles[registration_number]

        # Perform updates
        changed = False
        for field, value in update_fields.items():
            if vehicle.get(field) != value:
                vehicle[field] = value
                changed = True

        if changed:
            self.vehicles[registration_number] = vehicle
            return {"success": True, "message": "Vehicle details updated successfully."}
        else:
            return {"success": False, "error": "No changes made (fields already have specified values)."}

    def transfer_registration(self, registration_number: str, new_owner_id: str) -> dict:
        """
        Transfer ownership/registration of a vehicle to a new owner (only if current registration is active).

        Args:
            registration_number (str): Registration to be transferred.
            new_owner_id (str): The owner_id of the new owner.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Success description
            }
            or
            {
                "success": False,
                "error": str,    # Reason for failure
            }
    
        Constraints:
          - Only registrations with status 'active' can be transferred.
          - Registration number and new_owner_id must exist.
          - Expired or revoked registrations cannot be transferred.
        """
        reg = self.registrations.get(registration_number)
        if not reg:
            return {"success": False, "error": "Registration number does not exist."}

        if reg["status"].lower() != "active":
            return {"success": False, "error": "Only active registrations can be transferred."}
    
        if new_owner_id not in self.owners:
            return {"success": False, "error": "New owner does not exist."}

        # Update registration record with new owner
        reg["owner_id"] = new_owner_id

        return {
            "success": True,
            "message": f"Registration {registration_number} successfully transferred to owner {new_owner_id}."
        }

    def expire_registration(self, registration_number: str) -> dict:
        """
        Mark a registration as expired (status='expired').

        Args:
            registration_number (str): The unique registration number to expire.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Registration <registration_number> marked as expired."
                }
                Failure: {
                    "success": False,
                    "error": <string describing the failure>
                }

        Constraints:
            - Registration must exist.
            - Cannot expire a registration that is already expired or revoked.
        """
        reg = self.registrations.get(registration_number)
        if not reg:
            return {
                "success": False,
                "error": "Registration not found."
            }
        if reg["status"].lower() == "expired":
            return {
                "success": False,
                "error": "Registration is already expired."
            }
        if reg["status"].lower() == "revoked":
            return {
                "success": False,
                "error": "Cannot expire a revoked registration."
            }
        reg["status"] = "expired"
        self.registrations[registration_number] = reg
        return {
            "success": True,
            "message": f"Registration {registration_number} marked as expired."
        }

    def revoke_registration(self, registration_number: str) -> dict:
        """
        Revoke a registration for legal or administrative reasons.

        Args:
            registration_number (str): The unique registration number to revoke.

        Returns:
            dict:
                - success (bool): True if the operation was successful, False otherwise.
                - message (str): Success message if revoked, otherwise empty.
                - error (str): Error message if any failure occurs.

        Constraints:
            - The registration must exist.
            - Only registrations that are neither already revoked nor expired can be revoked.
            - Status is updated to 'revoked' upon successful operation.
        """
        reg = self.registrations.get(registration_number)
        if not reg:
            return { "success": False, "error": f"Registration '{registration_number}' does not exist." }
        if reg["status"].lower() in ("revoked", "expired"):
            return { "success": False, "error": f"Registration '{registration_number}' is already {reg['status'].lower()} and cannot be revoked." }
        reg["status"] = "revoked"
        self.registrations[registration_number] = reg  # Defensive; actually not strictly needed with dict-of-mutable TypedDict
        return { "success": True, "message": f"Registration '{registration_number}' revoked successfully." }

    def renew_registration(
        self,
        registration_number: str,
        new_expiration_date: str = None,
        new_registration_date: str = None
    ) -> dict:
        """
        Reactivate or extend an existing (not revoked) vehicle registration for a new period.

        Args:
            registration_number (str): The registration number to be renewed.
            new_expiration_date (str, optional): The new expiration date in ISO/year-month-day format. If not provided, defaults to one year from today.
            new_registration_date (str, optional): The new registration date. If not provided, defaults to today.

        Returns:
            dict: {
                "success": True,
                "message": "Registration renewed; new expiration: ...",
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Registration must exist and must not be revoked.
            - Only one active registration per vehicle is allowed (renewal for the same registration is fine).
        """

        reg = self.registrations.get(registration_number)
        if not reg:
            return { "success": False, "error": "Registration number does not exist." }
        if reg.get("status", "").lower() == "revoked":
            return { "success": False, "error": "Registration has been revoked and cannot be renewed." }

        # Get today's date as string
        today_str = datetime.date.today().isoformat()

        # Default: 1 year extension from today
        if new_registration_date is None:
            new_registration_date = today_str
        if new_expiration_date is None:
            try:
                new_expiry = datetime.date.today() + datetime.timedelta(days=365)
                new_expiration_date = new_expiry.isoformat()
            except Exception:
                # Fallback, if datetime fails
                new_expiration_date = today_str

        reg["registration_date"] = new_registration_date
        reg["expiration_date"] = new_expiration_date
        reg["status"] = "active"  # Assume renewal also makes it active

        self.registrations[registration_number] = reg

        return {
            "success": True,
            "message": f"Registration {registration_number} renewed. New expiration date: {new_expiration_date}."
        }

    def delete_vehicle_record(self, registration_number: str) -> dict:
        """
        Remove a vehicle and all associated registration(s) from the system by registration_number.

        Args:
            registration_number (str): Unique registration number of the vehicle to remove.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Vehicle and associated registrations deleted."
                }
                On failure,
                {
                    "success": False,
                    "error": "Vehicle with registration_number ... does not exist."
                }

        Constraints:
            - Only removes record if vehicle exists.
            - Deletes both vehicle and its registration(s).
            - Assumes admin permissions (no explicit authorization check).
        """
        if registration_number not in self.vehicles:
            return {
                "success": False,
                "error": f"Vehicle with registration_number {registration_number} does not exist."
            }

        vehicle = self.vehicles[registration_number]
        vehicle_vin = vehicle.get("VIN")

        # Remove vehicle record
        del self.vehicles[registration_number]

        # Remove all associated registration(s), including historical entries keyed differently.
        registrations_to_delete = [
            reg_num
            for reg_num, reg in self.registrations.items()
            if reg_num == registration_number or reg.get("vehicle_id") == vehicle_vin
        ]
        for reg_num in registrations_to_delete:
            del self.registrations[reg_num]

        return {
            "success": True,
            "message": "Vehicle and associated registrations deleted."
        }

    def add_owner(
        self,
        owner_id: str,
        name: str,
        address: str,
        date_of_birth: str,
        license_number: str,
        contact_information: str
    ) -> dict:
        """
        Add a new owner to the owner records.

        Args:
            owner_id (str): Unique identifier for the owner.
            name (str): Name of the owner.
            address (str): Owner's address.
            date_of_birth (str): Owner's date of birth.
            license_number (str): Owner's driver's license number.
            contact_information (str): Contact information for the owner.

        Returns:
            dict: {
                "success": True,
                "message": "Owner <owner_id> added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - owner_id must be unique (not already present in self.owners)
            - All fields must be provided and non-empty
        """
        # Check if owner_id is unique
        if owner_id in self.owners:
            return {"success": False, "error": f"Owner with owner_id {owner_id} already exists."}

        # Basic validation (no empty strings)
        attrs = [owner_id, name, address, date_of_birth, license_number, contact_information]
        attr_names = ["owner_id", "name", "address", "date_of_birth", "license_number", "contact_information"]
        for val, field in zip(attrs, attr_names):
            if not val or not isinstance(val, str):
                return {"success": False, "error": f"Field '{field}' must be a non-empty string."}

        # Create and add owner record
        owner_info: OwnerInfo = {
            "owner_id": owner_id,
            "name": name,
            "address": address,
            "date_of_birth": date_of_birth,
            "license_number": license_number,
            "contact_information": contact_information
        }
        self.owners[owner_id] = owner_info

        return {"success": True, "message": f"Owner {owner_id} added successfully."}

    def update_owner_details(
        self,
        owner_id: str,
        name: str = None,
        address: str = None,
        date_of_birth: str = None,
        license_number: str = None,
        contact_information: str = None
    ) -> dict:
        """
        Modify the personal information for an existing owner.

        Args:
            owner_id (str): ID of the owner record to update.
            name (str, optional): New name for the owner.
            address (str, optional): New address for the owner.
            date_of_birth (str, optional): New date of birth for the owner.
            license_number (str, optional): New driving license number for the owner.
            contact_information (str, optional): New contact information.

        Returns:
            dict:
                If success:
                    { "success": True, "message": "Owner details updated." }
                If failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Only updates fields present in the OwnerInfo type.
            - Fails if owner_id does not exist.
            - Fails if no valid fields are given to update.
        """
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner ID does not exist." }

        owner_info = self.owners[owner_id]
        update_fields = {
            "name": name,
            "address": address,
            "date_of_birth": date_of_birth,
            "license_number": license_number,
            "contact_information": contact_information
        }
        # Only update fields that are not None
        fields_to_update = {k: v for k, v in update_fields.items() if v is not None}
        if not fields_to_update:
            return { "success": False, "error": "No valid fields to update." }

        for field, value in fields_to_update.items():
            owner_info[field] = value
        # Save back (dict is mutable, so this is not strictly necessary)
        self.owners[owner_id] = owner_info

        return { "success": True, "message": "Owner details updated." }


class MotorVehicleRegistrationDatabase(BaseEnv):
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

    def get_vehicle_by_registration(self, **kwargs):
        return self._call_inner_tool('get_vehicle_by_registration', kwargs)

    def get_vehicle_by_vin(self, **kwargs):
        return self._call_inner_tool('get_vehicle_by_vin', kwargs)

    def list_vehicles_by_owner(self, **kwargs):
        return self._call_inner_tool('list_vehicles_by_owner', kwargs)

    def get_owner_by_id(self, **kwargs):
        return self._call_inner_tool('get_owner_by_id', kwargs)

    def get_owner_by_license(self, **kwargs):
        return self._call_inner_tool('get_owner_by_license', kwargs)

    def get_registration_by_number(self, **kwargs):
        return self._call_inner_tool('get_registration_by_number', kwargs)

    def list_active_registrations(self, **kwargs):
        return self._call_inner_tool('list_active_registrations', kwargs)

    def get_registration_status(self, **kwargs):
        return self._call_inner_tool('get_registration_status', kwargs)

    def get_vehicle_registration_history(self, **kwargs):
        return self._call_inner_tool('get_vehicle_registration_history', kwargs)

    def register_new_vehicle(self, **kwargs):
        return self._call_inner_tool('register_new_vehicle', kwargs)

    def update_vehicle_details(self, **kwargs):
        return self._call_inner_tool('update_vehicle_details', kwargs)

    def transfer_registration(self, **kwargs):
        return self._call_inner_tool('transfer_registration', kwargs)

    def expire_registration(self, **kwargs):
        return self._call_inner_tool('expire_registration', kwargs)

    def revoke_registration(self, **kwargs):
        return self._call_inner_tool('revoke_registration', kwargs)

    def renew_registration(self, **kwargs):
        return self._call_inner_tool('renew_registration', kwargs)

    def delete_vehicle_record(self, **kwargs):
        return self._call_inner_tool('delete_vehicle_record', kwargs)

    def add_owner(self, **kwargs):
        return self._call_inner_tool('add_owner', kwargs)

    def update_owner_details(self, **kwargs):
        return self._call_inner_tool('update_owner_details', kwargs)
