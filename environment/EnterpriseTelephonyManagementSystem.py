# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict



# TypedDicts map the entity attributes.
class DepartmentInfo(TypedDict):
    department_id: str
    name: str
    allocated_num: List[str]  # List of telephone number strings

class TelephoneNumberInfo(TypedDict):
    number: str
    allocation_status: str  # e.g. 'allocated', 'unallocated'
    allocated_to: Optional[str]  # department_id or user_id or None
    endpoint_id: Optional[str]  # endpoint_id or None

class EndpointInfo(TypedDict):
    endpoint_id: str
    type: str  # e.g., 'SIP', 'PSTN'
    address: str  # e.g., SIP URI, MAC address
    device_id: Optional[str]  # device_id or None

class DeviceInfo(TypedDict):
    device_id: str
    model: str
    location: str
    assigned_to: Optional[str]  # user_id or None

class UserInfo(TypedDict):
    user_id: str
    name: str
    department_id: str
    assigned_device: Optional[str]  # device_id or None

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Enterprise telephony management system state.
        """

        # Departments: {department_id: DepartmentInfo}
        self.departments: Dict[str, DepartmentInfo] = {}

        # Telephone numbers: {number: TelephoneNumberInfo}
        self.telephone_numbers: Dict[str, TelephoneNumberInfo] = {}

        # Endpoints: {endpoint_id: EndpointInfo}
        self.endpoints: Dict[str, EndpointInfo] = {}

        # Devices: {device_id: DeviceInfo}
        self.devices: Dict[str, DeviceInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each telephone number can be allocated to at most one department or user at a time.
        # - An endpoint must exist before a number can be routed to it.
        # - Allocated numbers must be unique and not assigned to multiple entities.
        # - Device assignment must be to valid users within the system.

    def list_allocated_numbers(self) -> dict:
        """
        Retrieve all telephone numbers currently allocated to departments or users.

        Returns:
            dict:
                - success (bool): True if the query is successful
                - data (List[TelephoneNumberInfo]): List of allocated telephone numbers' info (could be empty)

        Constraints:
            - Only numbers with 'allocation_status' == 'allocated' are returned.
        """
        allocated_numbers = [
            tn_info for tn_info in self.telephone_numbers.values()
            if tn_info["allocation_status"] == "allocated"
        ]
        return {
            "success": True,
            "data": allocated_numbers
        }

    def list_unallocated_numbers(self) -> dict:
        """
        Retrieve all telephone numbers that are currently unallocated (available for assignment).

        Returns:
            dict: {
                "success": True,
                "data": List[TelephoneNumberInfo]
            }
            or
            {
                "success": False,
                "error": str  # Failure reason (should not happen for normal queries)
            }

        Constraints:
            - Only numbers where allocation_status == 'unallocated' should be included.
        """
        try:
            result = [
                number_info
                for number_info in self.telephone_numbers.values()
                if number_info["allocation_status"] == "unallocated"
            ]

            return { "success": True, "data": result }
        except Exception as e:
            return { "success": False, "error": f"Unexpected error: {str(e)}" }

    def get_allocated_numbers_for_department(self, department_id: str) -> dict:
        """
        Retrieve the list of telephone numbers allocated specifically to the given department.

        Args:
            department_id (str): The unique identifier for the department.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of allocated telephone number strings
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Department must exist.
            - Only numbers with allocation_status == 'allocated' and allocated_to == department_id are included.
        """
        if department_id not in self.departments:
            return {"success": False, "error": "Department does not exist"}

        allocated_numbers = [
            num_info["number"]
            for num_info in self.telephone_numbers.values()
            if num_info["allocation_status"] == "allocated"
            and num_info["allocated_to"] == department_id
        ]
        return {"success": True, "data": allocated_numbers}

    def get_allocated_numbers_for_user(self, user_id: str) -> dict:
        """
        Retrieve all numbers specifically allocated to a given user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TelephoneNumberInfo]  # List may be empty if user has no numbers
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # E.g., "User does not exist"
                    }

        Constraints:
            - The user must exist in the system.
            - Only numbers with allocation_status == 'allocated' and allocated_to == user_id are returned.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        allocated_numbers = [
            tn_info for tn_info in self.telephone_numbers.values()
            if tn_info["allocation_status"] == "allocated" and tn_info["allocated_to"] == user_id
        ]

        return { "success": True, "data": allocated_numbers }

    def get_endpoint_for_number(self, number: str) -> dict:
        """
        Given a telephone number, retrieve its associated endpoint information (if routed).

        Args:
            number (str): The telephone number to look up.

        Returns:
            dict:
                {
                    "success": True,
                    "data": <EndpointInfo dict>,   # the endpoint info, if routed
                }
                or
                {
                    "success": True,
                    "data": None                   # if not routed to any endpoint
                }
                or
                {
                    "success": False,
                    "error": str                   # error description
                }

        Constraints:
            - The telephone number must exist in the system.
            - If the number is not routed (endpoint_id is None), data is None.
            - If the endpoint_id is set but not present in endpoints, return error.
        """
        if number not in self.telephone_numbers:
            return {"success": False, "error": "Telephone number does not exist"}

        telnum_info = self.telephone_numbers[number]
        endpoint_id = telnum_info.get("endpoint_id")
        if not endpoint_id:
            return {"success": True, "data": None}

        endpoint_info = self.endpoints.get(endpoint_id)
        if not endpoint_info:
            return {"success": False, "error": "Associated endpoint does not exist in system"}

        return {"success": True, "data": endpoint_info}

    def get_number_info(self, number: str) -> dict:
        """
        Retrieve full allocation and endpoint assignment details for a telephone number.

        Args:
            number (str): The telephone number to look up.

        Returns:
            dict:
                - success: True and data is the TelephoneNumberInfo dict if found
                - success: False and an error message if the number does not exist

        Constraints:
            - The specified telephone number must exist in the system.
        """
        tn_info = self.telephone_numbers.get(number)
        if tn_info is None:
            return { "success": False, "error": "Telephone number does not exist" }
        return { "success": True, "data": tn_info }

    def get_department_info(self, department_id: str) -> dict:
        """
        Retrieve complete information for a specified department.

        Args:
            department_id (str): The unique identifier of the department.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": DepartmentInfo}  # Department details
                On failure:
                    {"success": False, "error": str}  # Error message if not found

        Constraints:
            - The department_id must exist in the system.
        """
        department_info = self.departments.get(department_id)
        if department_info is None:
            return { "success": False, "error": "Department not found" }
        return { "success": True, "data": department_info }

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve information about a specific user.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. user does not exist
            }

        Constraints:
            - The specified user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}

        return {"success": True, "data": user_info}

    def get_device_info(self, device_id: str) -> dict:
        """
        Retrieve information/details for a specific device.

        Args:
            device_id (str): The unique identifier for the device.

        Returns:
            dict: {
                "success": True,
                "data": DeviceInfo
            }
            or
            {
                "success": False,
                "error": str  # If device_id does not exist
            }

        Constraints:
            - The device_id must exist in the system.
        """
        device_info = self.devices.get(device_id)
        if device_info is not None:
            return { "success": True, "data": device_info }
        else:
            return { "success": False, "error": "Device not found" }

    def get_endpoint_info(self, endpoint_id: str) -> dict:
        """
        Retrieve information about a specific endpoint.

        Args:
            endpoint_id (str): Unique identifier for the endpoint.

        Returns:
            dict: {
                "success": True,
                "data": EndpointInfo,  # contains endpoint_id, type, address, device_id (may be None)
            }
            or
            {
                "success": False,
                "error": str  # 'Endpoint not found' if not found in system
            }

        Constraints:
            - Endpoint must exist in the system.
        """
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return { "success": False, "error": "Endpoint not found" }
        return { "success": True, "data": endpoint }

    def list_departments(self) -> dict:
        """
        Get a list of all departments in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DepartmentInfo]  # Each department's information as a dict
            }
            or
            {
                "success": False,
                "error": str
            }

        If no departments exist, the data list will be empty.
        """
        # Since self.departments is always a dict, casting to list will always succeed
        return {
            "success": True,
            "data": list(self.departments.values())
        }

    def list_users(self) -> dict:
        """
        Get a list of all users in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of user information dicts (may be empty if no users)
            }

        Constraints:
            - None.
        """
        users_list = list(self.users.values())
        return { "success": True, "data": users_list }

    def list_devices(self) -> dict:
        """
        Retrieve all devices registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DeviceInfo]  # List of all devices in the system; empty list if none exist
            }
        """
        device_list = list(self.devices.values())
        return {
            "success": True,
            "data": device_list
        }

    def list_endpoints(self) -> dict:
        """
        Retrieve all endpoint entries in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[EndpointInfo],  # May be empty if no endpoints exist
            }

        Constraints:
            - None; this operation lists all endpoints unconditionally.
        """
        endpoints_list = list(self.endpoints.values())
        return { "success": True, "data": endpoints_list }

    def allocate_number_to_department(self, number: str, department_id: str) -> dict:
        """
        Allocate a telephone number to a department, enforcing uniqueness and updating state.

        Args:
            number (str): The telephone number to allocate.
            department_id (str): The department's unique id.

        Returns:
            dict: 
                If success:
                    {"success": True, "message": "Number <number> allocated to department <department_id>"}
                If failure:
                    {"success": False, "error": "<reason>"}
    
        Constraints:
            - The number and department must exist.
            - The number must not be already allocated (to any department/user).
            - Allocated numbers must be unique.
        """
        # Check department exists
        if department_id not in self.departments:
            return {"success": False, "error": "Department does not exist"}

        # Check telephone number exists
        if number not in self.telephone_numbers:
            return {"success": False, "error": "Telephone number does not exist"}

        tn_info = self.telephone_numbers[number]

        # Check allocation status
        if tn_info["allocation_status"] == "allocated" and tn_info["allocated_to"] is not None:
            return {
                "success": False,
                "error": f"Number {number} is already allocated to {tn_info['allocated_to']}"
            }

        # Update TelephoneNumberInfo
        tn_info["allocation_status"] = "allocated"
        tn_info["allocated_to"] = department_id
        self.telephone_numbers[number] = tn_info

        # Update DepartmentInfo
        dept_info = self.departments[department_id]
        if number not in dept_info["allocated_num"]:
            dept_info["allocated_num"].append(number)
        self.departments[department_id] = dept_info

        return {
            "success": True, 
            "message": f"Number {number} allocated to department {department_id}"
        }

    def allocate_number_to_user(self, number: str, user_id: str) -> dict:
        """
        Allocate a telephone number to a specific user, enforcing uniqueness.
        Prior assignment (to department or another user) is removed.
    
        Args:
            number (str): The telephone number to allocate.
            user_id (str): The user ID to allocate the number to.
    
        Returns:
            dict: {
                "success": True,
                "message": "Number {number} successfully allocated to user {user_id}."
            }
            or 
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Number must exist in the system.
            - User must exist in the system.
            - Number is allocated to at most one department or user at a time.
            - If previously allocated to department, remove from department's allocated_num.
        """
        # Validate number exists
        if number not in self.telephone_numbers:
            return {"success": False, "error": "Telephone number does not exist"}
        # Validate user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        tnum = self.telephone_numbers[number]
        curr_alloc = tnum['allocated_to']

        # If already allocated to this user, do nothing (idempotent)
        if tnum['allocation_status'] == 'allocated' and curr_alloc == user_id:
            return {
                "success": True,
                "message": f"Number {number} already allocated to user {user_id}."
            }

        # Remove number from previous assignee (if any)
        if curr_alloc is not None:
            # Check if it was a department
            if curr_alloc in self.departments:
                dept = self.departments[curr_alloc]
                if 'allocated_num' in dept and number in dept['allocated_num']:
                    dept['allocated_num'].remove(number)
            # Check if it was a user
            elif curr_alloc in self.users:
                # No need to update user info based on problem description (unless you keep a number list in user)
                pass
            # Else, allocated_to is an invalid reference, just clear it

        # Set new allocation
        tnum['allocation_status'] = 'allocated'
        tnum['allocated_to'] = user_id

        return {
            "success": True,
            "message": f"Number {number} successfully allocated to user {user_id}."
        }

    def deallocate_number(self, number: str) -> dict:
        """
        Remove the allocation of a telephone number from any department or user, making it available.

        Args:
            number (str): The telephone number to deallocate.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Number <number> deallocated successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The number must exist in the system.
            - The number must currently be allocated to a department or user.
            - Department's allocated_num list must be updated if relevant.
        """
        tn_info = self.telephone_numbers.get(number)
        if tn_info is None:
            return { "success": False, "error": "Telephone number does not exist." }
    
        if tn_info["allocation_status"] != "allocated" or tn_info["allocated_to"] is None:
            return { "success": False, "error": "Telephone number is not currently allocated." }
    
        old_allocated_to = tn_info["allocated_to"]

        # Remove from department's allocated_num list if applicable
        if old_allocated_to in self.departments:
            dept = self.departments[old_allocated_to]
            if number in dept["allocated_num"]:
                dept["allocated_num"].remove(number)
            # (Not strictly necessary, as only department tracks allocated_num.)

        # Update telephone number info
        tn_info["allocation_status"] = "unallocated"
        tn_info["allocated_to"] = None

        return { "success": True, "message": f"Number {number} deallocated successfully." }

    def route_number_to_endpoint(self, number: str, endpoint_id: str) -> dict:
        """
        Assign (route) a telephone number to a routing endpoint.
    
        Args:
            number (str): The telephone number to route.
            endpoint_id (str): The endpoint to which the number should be routed.

        Returns:
            dict, on success:
                {
                    "success": True,
                    "message": "Number <number> routed to endpoint <endpoint_id>"
                }
            On error:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The endpoint must exist in the system before a number can be routed to it.
        """
        # Check if the number exists
        if number not in self.telephone_numbers:
            return {"success": False, "error": "Telephone number does not exist"}

        # Check if the endpoint exists
        if endpoint_id not in self.endpoints:
            return {"success": False, "error": "Endpoint does not exist"}

        # Route the number to the endpoint (assignment)
        self.telephone_numbers[number]['endpoint_id'] = endpoint_id

        return {
            "success": True,
            "message": f"Number {number} routed to endpoint {endpoint_id}"
        }

    def unroute_number(self, number: str) -> dict:
        """
        Remove the routing assignment from a telephone number by clearing its endpoint reference.

        Args:
            number (str): The telephone number to unroute.

        Returns:
            dict: {
                "success": True,
                "message": "Routing for number <number> has been removed."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The telephone number must exist within the system.
            - If the number is already unrouted (endpoint_id is None), this operation is idempotent and succeeds.
        """
        if number not in self.telephone_numbers:
            return {"success": False, "error": "Telephone number does not exist."}

        tn_info = self.telephone_numbers[number]
        tn_info["endpoint_id"] = None  # Unroute the number (even if it was already None)
        self.telephone_numbers[number] = tn_info  # Not strictly necessary for dict reference, but for clarity

        return {
            "success": True,
            "message": f"Routing for number {number} has been removed."
        }

    def assign_device_to_user(self, user_id: str, device_id: str) -> dict:
        """
        Assign a device to a specified user, updating both the user and device states.

        Args:
            user_id (str): The ID of the user to assign the device to.
            device_id (str): The ID of the device to be assigned.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Device <device_id> assigned to user <user_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Both user and device must exist.
            - The device may only be assigned to one user at a time.
            - If the user already has a different device assigned, unassign it first.
        """

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if device_id not in self.devices:
            return {"success": False, "error": "Device does not exist"}

        user_info = self.users[user_id]
        device_info = self.devices[device_id]

        current_assigned_to = device_info.get("assigned_to") or None
        if current_assigned_to is not None and current_assigned_to != user_id:
            return {"success": False, "error": f"Device {device_id} is already assigned to another user"}

        # If user already has this device assigned, it's a no-op
        if user_info.get("assigned_device") == device_id and device_info.get("assigned_to") == user_id:
            return {"success": True, "message": f"Device {device_id} assigned to user {user_id}"}

        # If user currently has a different device assigned, unassign it
        prev_device_id = user_info.get("assigned_device") or None
        if prev_device_id and prev_device_id != device_id:
            prev_device_info = self.devices.get(prev_device_id)
            if prev_device_info and prev_device_info.get("assigned_to") == user_id:
                prev_device_info["assigned_to"] = None

        # Update device's assigned_to
        device_info["assigned_to"] = user_id
        # Update user's assigned_device
        user_info["assigned_device"] = device_id

        return {"success": True, "message": f"Device {device_id} assigned to user {user_id}"}

    def unassign_device_from_user(self, user_id: str) -> dict:
        """
        Remove device assignment from a user, making that device available for reassignment.

        Args:
            user_id (str): The ID of the user whose device assignment is to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Device {device_id} unassigned from user {user_id}."
            }
            or
            {
                "success": False,
                "error": "Description of the problem."
            }

        Constraints:
            - The user must exist in the system.
            - The user must have an assigned device.
            - Update both the user and device state to reflect the unassignment.
        """
        if user_id not in self.users:
            return {"success": False, "error": f"User {user_id} does not exist."}
    
        user_info = self.users[user_id]
        device_id = user_info.get("assigned_device")

        if not device_id:
            return {"success": False, "error": f"User {user_id} does not have an assigned device."}

        # Set user's assigned_device to None
        self.users[user_id]["assigned_device"] = None

        # Set device's assigned_to to None if device exists
        if device_id in self.devices:
            self.devices[device_id]["assigned_to"] = None
        # If device does not exist, proceed but mention in message
        else:
            return {
                "success": False,
                "error": f"Device {device_id} assigned to user {user_id} not found in devices."
            }

        return {
            "success": True,
            "message": f"Device {device_id} unassigned from user {user_id}."
        }

    def add_telephone_number(self, number: str) -> dict:
        """
        Add a new telephone number entry to the system, unallocated by default.

        Args:
            number (str): The telephone number (as a string) to add.

        Returns:
            dict: 
                { "success": True, "message": "Telephone number <number> added (unallocated)." }
                OR
                { "success": False, "error": <reason> }
    
        Constraints:
            - The number must not already exist in the system (unique).
            - The number must be a non-empty string.
            - On addition: allocation_status is 'unallocated', allocated_to and endpoint_id are None.
        """
        if not isinstance(number, str) or not number.strip():
            return { "success": False, "error": "Invalid or empty number provided." }
    
        if number in self.telephone_numbers:
            return { "success": False, "error": f"Telephone number {number} already exists." }

        self.telephone_numbers[number] = {
            "number": number,
            "allocation_status": "unallocated",
            "allocated_to": None,
            "endpoint_id": None
        }
        return { "success": True, "message": f"Telephone number {number} added (unallocated)." }

    def remove_telephone_number(self, number: str) -> dict:
        """
        Remove a telephone number record from the system, deallocating any assignment.

        Args:
            number (str): The telephone number string to remove.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Telephone number <number> removed from the system." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - If allocated to a department, remove it from their allocated_num list.
            - If allocated_to refers to a user/department, remove those links as relevant.
            - If routed to an endpoint, no special cleanup required (unless references must be dropped).
            - Number must exist in the system.
        """
        tn_info = self.telephone_numbers.get(number)
        if tn_info is None:
            return { "success": False, "error": f"Telephone number {number} does not exist in the system." }

        # If allocated to a department, update their allocated_num list.
        allocated_to = tn_info.get("allocated_to")
        if allocated_to is not None:
            # Check if allocated_to matches a department or a user
            if allocated_to in self.departments:
                dept = self.departments[allocated_to]
                if number in dept.get("allocated_num", []):
                    dept["allocated_num"].remove(number)
            elif allocated_to in self.users:
                # No explicit tracking of allocated numbers in UserInfo
                pass  # No action, since user info doesn't store number

        # Remove from the numbers dictionary
        del self.telephone_numbers[number]

        return {
            "success": True,
            "message": f"Telephone number {number} removed from the system."
        }

    def add_endpoint(self, endpoint_id: str, type: str, address: str, device_id: Optional[str] = None) -> dict:
        """
        Add a new endpoint to the telephony system.

        Args:
            endpoint_id (str): Unique identifier for the endpoint.
            type (str): Endpoint type (e.g., 'SIP', 'PSTN').
            address (str): Endpoint address (e.g., SIP URI or MAC address).
            device_id (Optional[str]): Device associated with this endpoint (must exist if provided, otherwise None).

        Returns:
            dict:
                - {"success": True, "message": "Endpoint <endpoint_id> added." }
                - {"success": False, "error": "reason"}

        Constraints:
            - endpoint_id must not already exist in the system.
            - If device_id is provided, it must exist in self.devices.
        """
        if endpoint_id in self.endpoints:
            return {"success": False, "error": f"Endpoint '{endpoint_id}' already exists"}

        if device_id is not None:
            if device_id not in self.devices:
                return {"success": False, "error": f"Device '{device_id}' does not exist"}
        else:
            device_id = None

        endpoint_info: EndpointInfo = {
            "endpoint_id": endpoint_id,
            "type": type,
            "address": address,
            "device_id": device_id
        }
        self.endpoints[endpoint_id] = endpoint_info

        return {"success": True, "message": f"Endpoint '{endpoint_id}' added."}

    def remove_endpoint(self, endpoint_id: str) -> dict:
        """
        Remove an endpoint from the system if and only if no telephone number is routed to it.

        Args:
            endpoint_id (str): The ID of the endpoint to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Endpoint removed successfully"
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Endpoint must exist.
            - No telephone number may have its endpoint_id set to the endpoint being removed.
        """
        # Check existence
        if endpoint_id not in self.endpoints:
            return { "success": False, "error": "Endpoint does not exist" }

        # Check that no telephone number is routed to this endpoint
        numbers_routed = [
            number for number, info in self.telephone_numbers.items()
            if info.get('endpoint_id') == endpoint_id
        ]
        if numbers_routed:
            return {
                "success": False,
                "error": "Cannot remove endpoint: routed numbers exist (%s)" % ', '.join(numbers_routed)
            }

        # Remove the endpoint
        del self.endpoints[endpoint_id]
        return { "success": True, "message": "Endpoint removed successfully" }

    def add_device(self, device_id: str, model: str, location: str, assigned_to: Optional[str] = None) -> dict:
        """
        Register a new device in the system.
    
        Args:
            device_id (str): Unique identifier for the device.
            model (str): Model name/number of the device.
            location (str): Location (physical or logical) of the device.
            assigned_to (Optional[str]): user_id this device is assigned to, or None.
        
        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Device <device_id> added."
                }
                or
                {
                    "success": False,
                    "error": <reason>
                }
    
        Constraints:
            - device_id must be unique within the system.
            - If assigned_to is not None, corresponding user_id must exist.
            - Device assignment must be to valid users within the system.
        """
        # Validate device_id
        if not device_id or not isinstance(device_id, str):
            return {"success": False, "error": "Device ID must be a non-empty string."}
        if device_id in self.devices:
            return {"success": False, "error": "Device ID already exists."}
        if not model or not isinstance(model, str):
            return {"success": False, "error": "Model must be a non-empty string."}
        if not location or not isinstance(location, str):
            return {"success": False, "error": "Location must be a non-empty string."}

        if assigned_to is not None:
            if assigned_to not in self.users:
                return {"success": False, "error": f"Assigned user '{assigned_to}' does not exist."}
            current_device = self.users[assigned_to].get("assigned_device")
            if current_device not in (None, device_id):
                return {"success": False, "error": f"User '{assigned_to}' already has an assigned device."}

        device_info: DeviceInfo = {
            "device_id": device_id,
            "model": model,
            "location": location,
            "assigned_to": assigned_to
        }
        self.devices[device_id] = device_info
        if assigned_to is not None:
            self.users[assigned_to]["assigned_device"] = device_id
        return {"success": True, "message": f"Device {device_id} added."}

    def remove_device(self, device_id: str) -> dict:
        """
        Remove a device from the system, updating or warning about any user assignment.

        Args:
            device_id (str): The unique ID of the device to remove.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Description of the operation, including if users were updated
            }
            or
            {
                "success": False,
                "error": str,  # Reason for failure (e.g., device does not exist)
            }

        Constraints:
            - Device must exist to be removed.
            - Any user assigned to this device should have `assigned_device` set to None upon removal.
        """
        if device_id not in self.devices:
            return {"success": False, "error": "Device does not exist"}

        # Track which users, if any, were assigned to this device (for reporting)
        users_updated = []
        for user_info in self.users.values():
            if user_info.get("assigned_device") == device_id:
                user_info["assigned_device"] = None
                users_updated.append(user_info["user_id"])

        # Actually remove the device from the system
        del self.devices[device_id]

        if users_updated:
            return {
                "success": True,
                "message": (
                    f"Device {device_id} removed from system. "
                    f"Unassigned from users: {', '.join(users_updated)}."
                )
            }
        else:
            return {
                "success": True,
                "message": f"Device {device_id} removed from system."
            }

    def add_user(
        self,
        user_id: str,
        name: str,
        department_id: str,
        assigned_device: Optional[str] = None
    ) -> dict:
        """
        Register a new user in the system, specifying department and optionally assigning a device.

        Args:
            user_id (str): Unique identifier for the new user.
            name (str): User's name.
            department_id (str): Department ID the user belongs to (must exist).
            assigned_device (Optional[str]): Device ID to assign to the user (must be unassigned, if provided).

        Returns:
            dict: 
                On success: { "success": True, "message": "User <user_id> added successfully" }
                On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - user_id must be unique.
            - department_id must exist.
            - assigned_device, if provided, must exist and be unassigned.
        """
        # Check for unique user_id
        if user_id in self.users:
            return { "success": False, "error": f"User ID '{user_id}' already exists." }

        # Check department existence
        if department_id not in self.departments:
            return { "success": False, "error": f"Department ID '{department_id}' does not exist." }

        # If device assigned, validate device existence and assignment
        if assigned_device is not None:
            if assigned_device not in self.devices:
                return { "success": False, "error": f"Assigned device '{assigned_device}' does not exist." }
            if self.devices[assigned_device].get("assigned_to") is not None:
                return { "success": False, "error": f"Device '{assigned_device}' is already assigned to a user." }

        # Create user entry
        self.users[user_id] = {
            "user_id": user_id,
            "name": name,
            "department_id": department_id,
            "assigned_device": assigned_device
        }

        # Assign device if requested
        if assigned_device is not None:
            self.devices[assigned_device]["assigned_to"] = user_id

        return { "success": True, "message": f"User '{user_id}' added successfully" }

    def remove_user(self, user_id: str) -> dict:
        """
        Remove a user from the system, unassigning any devices and telephone numbers.

        Args:
            user_id (str): The ID of the user to remove.

        Returns:
            dict: {
                "success": True,
                "message": "User <user_id> removed and all devices/numbers unassigned."
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - User must exist.
            - All devices assigned to this user are unassigned (assigned_to set to None).
            - All telephone numbers where allocated_to == user_id are made unallocated/None.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Unassign all devices from this user
        for device in self.devices.values():
            if device.get("assigned_to") == user_id:
                device["assigned_to"] = None

        # Unassign all numbers from this user
        for number_info in self.telephone_numbers.values():
            if number_info.get("allocated_to") == user_id:
                number_info["allocated_to"] = None
                number_info["allocation_status"] = "unallocated"

        # Remove the user
        del self.users[user_id]

        return {
            "success": True,
            "message": f"User {user_id} removed and all devices/numbers unassigned."
        }

    def add_department(self, department_id: str, name: str) -> dict:
        """
        Create/register a new department entry in the system.

        Args:
            department_id (str): Unique identifier for the department.
            name (str): Human-readable name of the department.

        Returns:
            dict: {
                "success": True,
                "message": "Department <department_id> added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - department_id must be unique in the system.
            - name and department_id must not be empty.
        """
        # Input validation
        if not department_id or not isinstance(department_id, str):
            return { "success": False, "error": "Invalid or missing department_id." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid or missing department name." }
        if department_id in self.departments:
            return { "success": False, "error": "Department already exists." }

        # Register new department
        self.departments[department_id] = {
            "department_id": department_id,
            "name": name,
            "allocated_num": []
        }
        return { "success": True, "message": f"Department {department_id} added." }

    def remove_department(self, department_id: str) -> dict:
        """
        Remove a department by department_id.

        This operation:
          - Deallocates all telephone numbers allocated to this department,
            by setting their allocation_status to 'unallocated' and allocated_to to None.
          - Removes the department from self.departments.
          - Sets department_id to None for any users who belonged to this department ("orphaned users").

        Args:
            department_id (str): The identifier of the department to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Department <department_id> removed, numbers deallocated, orphaned users handled."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The department must exist.
            - All associated numbers must be deallocated.
            - Orphaned users must not reference the deleted department.
        """
        if department_id not in self.departments:
            return { "success": False, "error": "Department does not exist." }

        # Deallocate all numbers allocated to this department
        dept_info = self.departments[department_id]
        for num in dept_info.get("allocated_num", []):
            if num in self.telephone_numbers:
                self.telephone_numbers[num]["allocation_status"] = "unallocated"
                self.telephone_numbers[num]["allocated_to"] = None

        # Remove department entry
        del self.departments[department_id]

        # Set department_id = None for all orphaned users
        for user in self.users.values():
            if user.get("department_id") == department_id:
                user["department_id"] = None

        return {
            "success": True,
            "message": f"Department {department_id} removed, numbers deallocated, orphaned users handled."
        }


class EnterpriseTelephonyManagementSystem(BaseEnv):
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

    def list_allocated_numbers(self, **kwargs):
        return self._call_inner_tool('list_allocated_numbers', kwargs)

    def list_unallocated_numbers(self, **kwargs):
        return self._call_inner_tool('list_unallocated_numbers', kwargs)

    def get_allocated_numbers_for_department(self, **kwargs):
        return self._call_inner_tool('get_allocated_numbers_for_department', kwargs)

    def get_allocated_numbers_for_user(self, **kwargs):
        return self._call_inner_tool('get_allocated_numbers_for_user', kwargs)

    def get_endpoint_for_number(self, **kwargs):
        return self._call_inner_tool('get_endpoint_for_number', kwargs)

    def get_number_info(self, **kwargs):
        return self._call_inner_tool('get_number_info', kwargs)

    def get_department_info(self, **kwargs):
        return self._call_inner_tool('get_department_info', kwargs)

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def get_device_info(self, **kwargs):
        return self._call_inner_tool('get_device_info', kwargs)

    def get_endpoint_info(self, **kwargs):
        return self._call_inner_tool('get_endpoint_info', kwargs)

    def list_departments(self, **kwargs):
        return self._call_inner_tool('list_departments', kwargs)

    def list_users(self, **kwargs):
        return self._call_inner_tool('list_users', kwargs)

    def list_devices(self, **kwargs):
        return self._call_inner_tool('list_devices', kwargs)

    def list_endpoints(self, **kwargs):
        return self._call_inner_tool('list_endpoints', kwargs)

    def allocate_number_to_department(self, **kwargs):
        return self._call_inner_tool('allocate_number_to_department', kwargs)

    def allocate_number_to_user(self, **kwargs):
        return self._call_inner_tool('allocate_number_to_user', kwargs)

    def deallocate_number(self, **kwargs):
        return self._call_inner_tool('deallocate_number', kwargs)

    def route_number_to_endpoint(self, **kwargs):
        return self._call_inner_tool('route_number_to_endpoint', kwargs)

    def unroute_number(self, **kwargs):
        return self._call_inner_tool('unroute_number', kwargs)

    def assign_device_to_user(self, **kwargs):
        return self._call_inner_tool('assign_device_to_user', kwargs)

    def unassign_device_from_user(self, **kwargs):
        return self._call_inner_tool('unassign_device_from_user', kwargs)

    def add_telephone_number(self, **kwargs):
        return self._call_inner_tool('add_telephone_number', kwargs)

    def remove_telephone_number(self, **kwargs):
        return self._call_inner_tool('remove_telephone_number', kwargs)

    def add_endpoint(self, **kwargs):
        return self._call_inner_tool('add_endpoint', kwargs)

    def remove_endpoint(self, **kwargs):
        return self._call_inner_tool('remove_endpoint', kwargs)

    def add_device(self, **kwargs):
        return self._call_inner_tool('add_device', kwargs)

    def remove_device(self, **kwargs):
        return self._call_inner_tool('remove_device', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def remove_user(self, **kwargs):
        return self._call_inner_tool('remove_user', kwargs)

    def add_department(self, **kwargs):
        return self._call_inner_tool('add_department', kwargs)

    def remove_department(self, **kwargs):
        return self._call_inner_tool('remove_department', kwargs)
