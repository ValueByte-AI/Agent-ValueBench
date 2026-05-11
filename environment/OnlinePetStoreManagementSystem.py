# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import time
import uuid



class PetInfo(TypedDict):
    pet_id: str
    species: str
    breed: str
    age: float  # Can be int if only integer ages are needed
    gender: str
    price: float
    status: str  # available/sold/reserved
    description: str
    arrival_date: str

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_details: str
    account_type: str  # individual/company
    authentication_credential: str

class OrderInfo(TypedDict):
    order_id: str
    customer_id: str
    pet_id: str
    order_date: str
    status: str  # placed/completed/cancelled
    payment_status: str

class SessionInfo(TypedDict):
    session_id: str
    customer_id: str
    login_time: str
    expiration_time: str
    is_active: bool

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment simulating an online pet store management system.

        Constraints:
        - A pet with status "sold" or "reserved" cannot be ordered again.
        - Each customer can have only one active session at a time.
        - Creating an order for a pet automatically updates its status to "sold" or "reserved".
        - Customers (including companies) must be authenticated and have an active session to place orders.
        - Logging out ends the session and invalidates authentication for that user.
        """

        # Pets: {pet_id: PetInfo}
        self.pets: Dict[str, PetInfo] = {}

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}

        # Sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}


    def get_customer_by_name(self, name: str) -> dict:
        """
        Retrieve customer details using the given name.
        Returns all customers (individuals or companies) whose name exactly matches the input.

        Args:
            name (str): The name of the customer to search for.

        Returns:
            dict:
                {"success": True, "data": [CustomerInfo, ...]}
                    - List will be all customers matching the name (may be empty if none).
                {"success": False, "error": str}
                    - For invalid input.

        Constraints:
            - Name match is case-sensitive and exact.
            - Matches both individuals and companies.
        """
        if not isinstance(name, str) or len(name.strip()) == 0:
            return {"success": False, "error": "Customer name must be a non-empty string"}

        matched_customers = [
            customer for customer in self.customers.values()
            if customer["name"] == name
        ]

        return {"success": True, "data": matched_customers}

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer details (CustomerInfo) by unique customer_id.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": CustomerInfo
                  }
                - On failure: {
                    "success": False,
                    "error": str
                  }

        Constraints:
            - Customer must exist in the system. 
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": f"Customer with id '{customer_id}' does not exist" }

        return { "success": True, "data": customer }

    def list_all_customers(self) -> dict:
        """
        Retrieve all registered customers in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo]  # List of customers (possibly empty)
            }
    
        Constraints:
            - None; public query operation.
            - If no customers exist, returns an empty list in 'data'.
        """
        customers_list = list(self.customers.values())
        return { "success": True, "data": customers_list }

    def get_pet_by_id(self, pet_id: str) -> dict:
        """
        Retrieve detailed information for a specified pet by pet_id.

        Args:
            pet_id (str): The unique identifier of the pet.

        Returns:
            dict:
                {
                    "success": True,
                    "data": PetInfo  # All details of the pet
                }
                or
                {
                    "success": False,
                    "error": str  # Reason why the retrieval failed
                }

        Constraints:
            - The pet must exist in the system (by pet_id).
        """
        pet_info = self.pets.get(pet_id)
        if pet_info is None:
            return {
                "success": False,
                "error": "Pet not found"
            }

        return {
            "success": True,
            "data": pet_info
        }

    def list_pets_by_status(self, status: str) -> dict:
        """
        List all pets filtered by their status.

        Args:
            status (str): The inventory status to filter by. One of: "available", "sold", "reserved".

        Returns:
            dict:
                On success: 
                    {
                        "success": True,
                        "data": List[PetInfo]  # List of all pets matching the given status, may be empty.
                    }
                On failure (invalid status): 
                    {
                        "success": False,
                        "error": str  # Error message
                    }

        Constraints:
            - Status must be one of "available", "sold", or "reserved".
        """
        allowed_statuses = {"available", "sold", "reserved"}
        if status not in allowed_statuses:
            return {"success": False, "error": "Invalid status. Allowed values: available, sold, reserved."}

        pets = [pet for pet in self.pets.values() if pet["status"] == status]
        return {"success": True, "data": pets}

    def list_pets_by_species(self, species: str) -> dict:
        """
        List all pets of the specified species.

        Args:
            species (str): The species to filter for. (e.g., 'dog', 'cat')

        Returns:
            dict:
                { "success": True, "data": List[PetInfo] }
                or
                { "success": False, "error": error_msg }

        Constraints:
            - Species must be a non-empty string.
            - If no pets are found matching the species, returns an empty list (success).
        """
        if not species or not isinstance(species, str):
            return { "success": False, "error": "Species parameter must be a non-empty string." }

        result = [
            pet_info for pet_info in self.pets.values()
            if pet_info["species"] == species
        ]
        return { "success": True, "data": result }

    def check_pet_availability(self, pet_id: str) -> dict:
        """
        Check if a pet is available (status = "available") for order.

        Args:
            pet_id (str): The unique ID of the pet.

        Returns:
            dict: 
                If found: {
                    "success": True,
                    "data": bool  # True if available, False if not
                }
                If not found: {
                    "success": False,
                    "error": "Pet not found"
                }

        Constraints:
            - Pet must exist in the system.
            - Pet status must be "available" to be considered available for order.
        """
        pet_info = self.pets.get(pet_id)
        if pet_info is None:
            return { "success": False, "error": "Pet not found" }
    
        is_available = pet_info["status"] == "available"
        return { "success": True, "data": is_available }

    def get_orders_by_customer(self, customer_id: str) -> dict:
        """
        Retrieve all orders placed by a given customer.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: {
                "success": True,
                "data": List[OrderInfo]  # All orders placed by the customer (can be empty if none).
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "Customer not found"
            }

        Constraints:
            - The given customer_id must exist in the system.
        """
        # Check if customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        orders = [
            order_info
            for order_info in self.orders.values()
            if order_info["customer_id"] == customer_id
        ]

        return {"success": True, "data": orders}

    def get_order_by_id(self, order_id: str) -> dict:
        """
        Retrieve details of a specific order by its order_id.

        Args:
            order_id (str): Unique identifier for the order.

        Returns:
            dict:
                - If found: {"success": True, "data": OrderInfo}
                - If not found: {"success": False, "error": "Order not found"}

        Constraints:
            - No authentication is required since this is an information query.
        """
        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found" }
        return { "success": True, "data": order }

    def list_orders_by_status(self, status: str = None, payment_status: str = None) -> dict:
        """
        List orders filtered by order status and/or payment status.

        Args:
            status (str, optional): Filter orders with this status ('placed', 'completed', 'cancelled').
            payment_status (str, optional): Filter orders with this payment status ('paid', 'unpaid', etc).

        Returns:
            dict: {
                "success": True,
                "data": List[OrderInfo],           # List of matching orders (OrderInfo)
            }

        Constraints:
            - If both 'status' and 'payment_status' are provided, order must match both.
            - If neither provided, returns all orders.
            - Always returns successfully, empty data if no matches.
        """
        filtered_orders = [
            order for order in self.orders.values()
            if (status is None or order["status"] == status)
            and (payment_status is None or order["payment_status"] == payment_status)
        ]
        return { "success": True, "data": filtered_orders }

    def get_active_session_by_customer(self, customer_id: str) -> dict:
        """
        Retrieve the active session for a customer, if it exists.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: {
                "success": True,
                "data": SessionInfo  # Active session info
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - The customer must exist in the system.
            - Each customer can have at most one active session.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist."}

        active_sessions = [
            session for session in self.sessions.values()
            if session["customer_id"] == customer_id and session["is_active"]
        ]

        if len(active_sessions) == 0:
            return {"success": False, "error": "No active session for this customer."}
        if len(active_sessions) > 1:
            return {"success": False, "error": "Data integrity error: Multiple active sessions found for this customer."}

        return {"success": True, "data": active_sessions[0]}

    def check_customer_authentication(self, customer_id: str, authentication_credential: str) -> dict:
        """
        Verify authentication state for a customer.

        Args:
            customer_id (str): Unique identifier for the customer.
            authentication_credential (str): Credential for authentication (e.g., password or token).

        Returns:
            dict: {
                "success": True,
                "data": {
                    "is_authenticated": bool,
                    "reason": str
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Customer must exist.
            - Credential must match the stored credential.
            - The customer must have one active session (is_active == True).
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer not found" }

        if customer.get("authentication_credential") != authentication_credential:
            return {
                "success": True,
                "data": {
                    "is_authenticated": False,
                    "reason": "Invalid credentials"
                }
            }

        # Find active session for customer
        active_sessions = [
            sess for sess in self.sessions.values()
            if sess["customer_id"] == customer_id and sess["is_active"]
        ]

        if not active_sessions:
            return {
                "success": True,
                "data": {
                    "is_authenticated": False,
                    "reason": "No active session"
                }
            }
        elif len(active_sessions) > 1:
            return {
                "success": True,
                "data": {
                    "is_authenticated": False,
                    "reason": "Multiple active sessions found for customer (data inconsistency)"
                }
            }

        return {
            "success": True,
            "data": {
                "is_authenticated": True,
                "reason": "Credentials valid and active session found"
            }
        }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Retrieve details of a session with the given session_id.

        Args:
            session_id (str): The unique identifier for the session.

        Returns:
            dict:
              - On success:
                  { "success": True, "data": SessionInfo (dict) }
              - On failure:
                  { "success": False, "error": "Session not found" }

        Constraints:
            - session_id must exist in the system.
        """
        session_info = self.sessions.get(session_id)
        if not session_info:
            return {"success": False, "error": "Session not found"}
        return {"success": True, "data": session_info}


    def login_customer(self, customer_id: str, authentication_credential: str) -> dict:
        """
        Authenticate a customer and create a new session if no active session exists.

        Args:
            customer_id (str): The customer's unique identifier.
            authentication_credential (str): Credential used for authentication.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "message": "Customer logged in successfully.",
                        "session": SessionInfo
                    }
                Failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Customer must exist.
            - Credential must match.
            - Only one active session per customer.
            - On successful login, a new session is created and stored.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return { "success": False, "error": "Customer does not exist." }

        # Authentication check
        if customer["authentication_credential"] != authentication_credential:
            return { "success": False, "error": "Invalid authentication credentials." }

        # Check for active session for this customer
        for session in self.sessions.values():
            if session["customer_id"] == customer_id and session["is_active"]:
                return { "success": False, "error": "Customer already has an active session." }

        # Create new session
        session_id = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        # In a real system, expiration might be set to 1 hour later; here, we simulate with string + 1 hour
        expiration_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 3600))
        session_info = {
            "session_id": session_id,
            "customer_id": customer_id,
            "login_time": now,
            "expiration_time": expiration_time,
            "is_active": True
        }
        self.sessions[session_id] = session_info

        return {
            "success": True,
            "message": "Customer logged in successfully.",
            "session": session_info
        }

    def logout_customer(self, customer_id: str) -> dict:
        """
        Invalidate and end the current session for a customer.

        Args:
            customer_id (str): The unique identifier of the customer to log out.

        Returns:
            dict:
                - success: True, message indicating logout completed.
                - success: False, error explaining why logout failed (customer does not exist, no active session).

        Constraints:
            - The customer must exist.
            - A customer can have only one active session at a time.
            - Logging out ends the session and invalidates authentication for that user.
        """
        # Validate customer exists
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist."}

        # Find active session for customer
        active_session = None
        for session in self.sessions.values():
            if session["customer_id"] == customer_id and session["is_active"]:
                active_session = session
                break

        if not active_session:
            return {"success": False, "error": "Customer has no active session."}

        # Invalidate session
        active_session["is_active"] = False

        return {"success": True, "message": "Customer session has been logged out and invalidated."}


    def place_order(self, customer_id: str, pet_id: str) -> dict:
        """
        Create an order for a pet by a customer, subject to pet status and session constraints.
        Also updates pet status appropriately.
    
        Args:
            customer_id (str): The ID of the customer placing the order.
            pet_id (str): The ID of the pet to order.
    
        Returns:
            dict: {
                "success": True,
                "message": "Order placed successfully",
                "order_id": str,
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - Customer must exist and have an active session.
            - Pet must exist and have status "available".
            - Pet status is updated atomically when placing an order.
            - Pet with status 'sold' or 'reserved' cannot be ordered.
        """
        # Check customer existence
        customer = self.customers.get(customer_id)
        if not customer:
            return {"success": False, "error": "Customer does not exist"}

        # Check active session
        active_session = None
        for session in self.sessions.values():
            if session['customer_id'] == customer_id and session['is_active']:
                active_session = session
                break
        if not active_session:
            return {"success": False, "error": "Customer is not authenticated or has no active session"}

        # Check pet existence
        pet = self.pets.get(pet_id)
        if not pet:
            return {"success": False, "error": "Pet does not exist"}

        # Pet must be available
        if pet['status'] != 'available':
            return {"success": False, "error": f"Pet is not available for order (current status: {pet['status']})"}

        # Generate new unique order_id
        order_id = str(uuid.uuid4())
        order_date = time.strftime('%Y-%m-%d %H:%M:%S')

        order_info = {
            "order_id": order_id,
            "customer_id": customer_id,
            "pet_id": pet_id,
            "order_date": order_date,
            "status": "placed",
            "payment_status": "pending",
        }

        # Place the order (atomic update)
        self.orders[order_id] = order_info
        pet['status'] = 'sold'
        self.pets[pet_id] = pet

        return {
            "success": True,
            "message": "Order placed successfully",
            "order_id": order_id,
        }

    def update_pet_status(self, pet_id: str, new_status: str) -> dict:
        """
        Change the status of a pet directly to one of ["available", "sold", "reserved"].
        Typically used by administrators to correct status manually.

        Args:
            pet_id (str): The ID of the pet whose status is to be updated.
            new_status (str): The new status to set ("available", "sold", or "reserved").

        Returns:
            dict: 
                On success: { "success": True, "message": "Pet status updated successfully" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - pet_id must exist in self.pets.
            - new_status must be one of ["available", "sold", "reserved"].
        """
        allowed_statuses = {"available", "sold", "reserved"}
        if pet_id not in self.pets:
            return { "success": False, "error": "Pet with the given pet_id does not exist" }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed: available, sold, reserved" }
    
        self.pets[pet_id]["status"] = new_status
        return { "success": True, "message": "Pet status updated successfully" }

    def update_order_status(self, order_id: str, new_status: str) -> dict:
        """
        Update the status of an order. The status can be 'placed', 'completed', or 'cancelled'.

        Args:
            order_id (str): The ID of the order to update.
            new_status (str): The new status to assign to the order ('placed', 'completed', 'cancelled').

        Returns:
            dict: {
                "success": True,
                "message": "Order status updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The order must exist.
            - The new_status must be one of {'placed', 'completed', 'cancelled'}.
            - (No authentication/session enforcement in this operation.)
        """
        allowed_statuses = {"placed", "completed", "cancelled"}
        if order_id not in self.orders:
            return { "success": False, "error": "Order does not exist." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed values: placed, completed, cancelled." }

        self.orders[order_id]['status'] = new_status
        return { "success": True, "message": "Order status updated successfully." }

    def cancel_order(self, order_id: str) -> dict:
        """
        Cancel an existing order, subject to valid order status.

        Args:
            order_id (str): The ID of the order to cancel.

        Returns:
            dict:
                success: True and message if the cancellation is successful.
                success: False and error if failed.

        Constraints:
            - Order must exist.
            - Only orders with status 'placed' can be cancelled (not 'completed' or 'cancelled').
            - Cancelling an order updates its status to 'cancelled'.
            - Associated pet's status is reverted to 'available' if possible.
        """
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order does not exist"}

        if order["status"] in ["cancelled", "completed"]:
            return {"success": False, "error": f"Order cannot be cancelled (status is '{order['status']}')"}

        pet_id = order["pet_id"]
        pet = self.pets.get(pet_id)
        if not pet:
            return {"success": False, "error": "Associated pet does not exist"}

        # Cancel the order
        order["status"] = "cancelled"
        self.orders[order_id] = order

        # Revert pet status if it was sold or reserved
        if pet["status"] in ["sold", "reserved"]:
            pet["status"] = "available"
            self.pets[pet_id] = pet

        return {
            "success": True,
            "message": f"Order {order_id} cancelled"
        }

    def delete_session(self, session_id: str) -> dict:
        """
        Force-remove a session from the system (for admin/error recovery purposes).

        Args:
            session_id (str): The unique identifier of the session to delete.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Session deleted successfully."
                }
                OR
                {
                    "success": False,
                    "error": "Session not found."
                }

        Constraints:
            - The session is removed even if it was active.
            - If the session does not exist, returns an error.
            - No authentication required for this operation.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session not found." }

        del self.sessions[session_id]
        return { "success": True, "message": "Session deleted successfully." }

    def register_new_customer(
        self,
        customer_id: str,
        name: str,
        contact_details: str,
        account_type: str,
        authentication_credential: str
    ) -> dict:
        """
        Adds/registers a new customer to the store.

        Args:
            customer_id (str): Unique ID for the customer.
            name (str): Customer's name.
            contact_details (str): Customer's contact information.
            account_type (str): Must be 'individual' or 'company'.
            authentication_credential (str): Credential for authentication.

        Returns:
            dict: {
                "success": True,
                "message": "Customer registered successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - customer_id must be unique in the store.
            - account_type must be 'individual' or 'company'.
            - No input can be empty.
        """
        # Validate all fields
        if not all([customer_id, name, contact_details, account_type, authentication_credential]):
            return { "success": False, "error": "All fields must be provided and non-empty." }

        # Check uniqueness
        if customer_id in self.customers:
            return { "success": False, "error": "Customer ID already exists." }

        # Check valid account type
        if account_type not in ("individual", "company"):
            return { "success": False, "error": "Account type must be 'individual' or 'company'." }

        # Add customer
        customer_info = {
            "customer_id": customer_id,
            "name": name,
            "contact_details": contact_details,
            "account_type": account_type,
            "authentication_credential": authentication_credential
        }
        self.customers[customer_id] = customer_info

        return { "success": True, "message": "Customer registered successfully." }

    def add_new_pet(
        self,
        pet_id: str,
        species: str,
        breed: str,
        age: float,
        gender: str,
        price: float,
        status: str,
        description: str,
        arrival_date: str
    ) -> dict:
        """
        Add a new pet (with metadata) to the store's inventory.

        Args:
            pet_id (str): Unique identifier for the pet.
            species (str): Species of the pet.
            breed (str): Breed of the pet.
            age (float): Age of the pet.
            gender (str): Gender of the pet.
            price (float): Sale price for the pet.
            status (str): Inventory status (should be 'available' for new).
            description (str): Description details of the pet.
            arrival_date (str): Arrival date in the store (format YYYY-MM-DD or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Pet added to inventory."
            } on success,
            or
            {
                "success": False,
                "error": <reason>
            } on error.

        Constraints:
            - pet_id must be unique (not already present in inventory)
            - status should usually be 'available' for a newly added pet
        """
        if not pet_id or not isinstance(pet_id, str):
            return {"success": False, "error": "pet_id must be a non-empty string."}
        if pet_id in self.pets:
            return {"success": False, "error": "Pet ID already exists."}
        if status not in {"available", "sold", "reserved"}:
            return {"success": False, "error": "Invalid status for pet. Must be 'available', 'sold', or 'reserved'."}
        # Minimal validation
        if (
            not isinstance(species, str) or not species.strip()
            or not isinstance(breed, str) or not breed.strip()
            or not isinstance(gender, str) or not gender.strip()
            or not isinstance(arrival_date, str) or not arrival_date.strip()
        ):
            return {"success": False, "error": "Missing or invalid required fields."}
        try:
            age_val = float(age)
            price_val = float(price)
        except Exception:
            return {"success": False, "error": "Age and price must be numeric."}

        info: PetInfo = {
            "pet_id": pet_id,
            "species": species,
            "breed": breed,
            "age": age_val,
            "gender": gender,
            "price": price_val,
            "status": status,
            "description": description,
            "arrival_date": arrival_date
        }
        self.pets[pet_id] = info
        return {"success": True, "message": "Pet added to inventory."}


class OnlinePetStoreManagementSystem(BaseEnv):
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

    def get_customer_by_name(self, **kwargs):
        return self._call_inner_tool('get_customer_by_name', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_all_customers(self, **kwargs):
        return self._call_inner_tool('list_all_customers', kwargs)

    def get_pet_by_id(self, **kwargs):
        return self._call_inner_tool('get_pet_by_id', kwargs)

    def list_pets_by_status(self, **kwargs):
        return self._call_inner_tool('list_pets_by_status', kwargs)

    def list_pets_by_species(self, **kwargs):
        return self._call_inner_tool('list_pets_by_species', kwargs)

    def check_pet_availability(self, **kwargs):
        return self._call_inner_tool('check_pet_availability', kwargs)

    def get_orders_by_customer(self, **kwargs):
        return self._call_inner_tool('get_orders_by_customer', kwargs)

    def get_order_by_id(self, **kwargs):
        return self._call_inner_tool('get_order_by_id', kwargs)

    def list_orders_by_status(self, **kwargs):
        return self._call_inner_tool('list_orders_by_status', kwargs)

    def get_active_session_by_customer(self, **kwargs):
        return self._call_inner_tool('get_active_session_by_customer', kwargs)

    def check_customer_authentication(self, **kwargs):
        return self._call_inner_tool('check_customer_authentication', kwargs)

    def get_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_session_by_id', kwargs)

    def login_customer(self, **kwargs):
        return self._call_inner_tool('login_customer', kwargs)

    def logout_customer(self, **kwargs):
        return self._call_inner_tool('logout_customer', kwargs)

    def place_order(self, **kwargs):
        return self._call_inner_tool('place_order', kwargs)

    def update_pet_status(self, **kwargs):
        return self._call_inner_tool('update_pet_status', kwargs)

    def update_order_status(self, **kwargs):
        return self._call_inner_tool('update_order_status', kwargs)

    def cancel_order(self, **kwargs):
        return self._call_inner_tool('cancel_order', kwargs)

    def delete_session(self, **kwargs):
        return self._call_inner_tool('delete_session', kwargs)

    def register_new_customer(self, **kwargs):
        return self._call_inner_tool('register_new_customer', kwargs)

    def add_new_pet(self, **kwargs):
        return self._call_inner_tool('add_new_pet', kwargs)
