# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class HotelInfo(TypedDict):
    hotel_id: str
    name: str
    location: str
    property_type: str

class TransactionInfo(TypedDict):
    transaction_id: str
    hotel_id: str
    booking_id: str
    guest_id: str
    amount: float
    date: str
    payment_method: str
    transaction_type: str
    status: str

class BookingInfo(TypedDict):
    booking_id: str
    hotel_id: str
    guest_id: str
    room_number: str
    check_in_date: str
    check_out_date: str
    status: str
    total_amount: float

class GuestInfo(TypedDict):
    guest_id: str
    name: str
    contact_info: str
    loyalty_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Hotel Property Management System (PMS) stateful environment.
        - Maintains hotels, guests, bookings, and transactions.
        """

        # Hotels: {hotel_id: HotelInfo}
        # State space: Hotel(hotel_id, name, location, property_type)
        self.hotels: Dict[str, HotelInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        # State space: Transaction(transaction_id, hotel_id, booking_id, guest_id, amount, date, payment_method, transaction_type, status)
        self.transactions: Dict[str, TransactionInfo] = {}

        # Bookings: {booking_id: BookingInfo}
        # State space: Booking(booking_id, hotel_id, guest_id, room_number, check_in_date, check_out_date, status, total_amount)
        self.bookings: Dict[str, BookingInfo] = {}

        # Guests: {guest_id: GuestInfo}
        # State space: Guest(guest_id, name, contact_info, loyalty_status)
        self.guests: Dict[str, GuestInfo] = {}

        # Constraints:
        # - Each transaction must be associated with a valid hotel (hotel_id).
        # - Only transactions with status "completed" contribute to revenue calculations.
        # - Bookings must belong to an existing hotel and reference a valid guest.
        # - Revenue for a hotel is the sum of the amounts of completed transactions linked to that hotel.

    def get_hotel_by_id(self, hotel_id: str) -> dict:
        """
        Retrieve the information of a specific hotel by its hotel_id.

        Args:
            hotel_id (str): Unique identifier for the hotel.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": HotelInfo  # The hotel's information
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Hotel not found"
                    }

        Constraints:
            - The hotel_id must exist in the hotels dictionary.
        """
        hotel_info = self.hotels.get(hotel_id)
        if hotel_info is None:
            return {"success": False, "error": "Hotel not found"}
        return {"success": True, "data": hotel_info}

    def get_hotel_by_name(self, name: str) -> dict:
        """
        Search and retrieve hotel information using the hotel’s name.

        Args:
            name (str): The name of the hotel to search for.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[HotelInfo]  # All hotels matching the name, exact match
                }
            or
                {
                    "success": False,
                    "error": str  # Error message, e.g. missing or empty name
                }

        Constraints:
            - Returns all hotels whose `name` exactly matches the input.
            - Returns an empty list if no match found.
            - Returns failure if name is not provided or is empty.
        """
        if not isinstance(name, str) or not name.strip():
            return {
                "success": False,
                "error": "Hotel name must be provided and non-empty."
            }
        matches = [
            hotel_info for hotel_info in self.hotels.values()
            if hotel_info["name"] == name
        ]
        return {
            "success": True,
            "data": matches
        }

    def list_hotels(self) -> dict:
        """
        List all hotel properties managed in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[HotelInfo],  # List of hotel info (may be empty if no hotels)
            }
        """
        hotel_list = list(self.hotels.values())
        return { "success": True, "data": hotel_list }

    def list_transactions_by_hotel(self, hotel_id: str) -> dict:
        """
        Retrieve all transactions associated with a specific hotel.

        Args:
            hotel_id (str): Unique identifier for the hotel.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": List[TransactionInfo]}
                - On failure (hotel does not exist):
                    {"success": False, "error": "Hotel does not exist"}

        Constraints:
            - hotel_id must exist in the system.
            - Transactions are all those with hotel_id matching the provided value.
        """
        if hotel_id not in self.hotels:
            return { "success": False, "error": "Hotel does not exist" }

        transactions = [
            transaction_info for transaction_info in self.transactions.values()
            if transaction_info["hotel_id"] == hotel_id
        ]

        return { "success": True, "data": transactions }

    def list_transactions_by_hotel_and_status(self, hotel_id: str, status: str) -> dict:
        """
        Retrieve all transactions for a given hotel filtered by the provided transaction status.

        Args:
            hotel_id (str): The ID of the hotel whose transactions should be retrieved.
            status (str): The transaction status to filter by ("completed", "pending", etc.).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TransactionInfo],  # May be empty
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error description
                    }
        Constraints:
            - The hotel must exist.
        """
        if hotel_id not in self.hotels:
            return {"success": False, "error": "Hotel does not exist"}

        result = [
            tx for tx in self.transactions.values()
            if tx["hotel_id"] == hotel_id and tx["status"] == status
        ]

        return {"success": True, "data": result}

    def calculate_hotel_revenue(self, hotel_id: str) -> dict:
        """
        Sum the amounts of all completed transactions for the given hotel ID 
        to compute and return the hotel's revenue.

        Args:
            hotel_id (str): The unique identifier of the hotel.

        Returns:
            dict: 
                - On success: { "success": True, "data": <revenue_float> }
                - On error: { "success": False, "error": "Hotel ID does not exist" }

        Constraints:
            - The hotel_id must exist in the system.
            - Only transactions with status 'completed' are included in the revenue sum.
        """
        if hotel_id not in self.hotels:
            return { "success": False, "error": "Hotel ID does not exist" }

        revenue = 0.0
        for transaction in self.transactions.values():
            if transaction["hotel_id"] == hotel_id and transaction["status"] == "completed":
                revenue += transaction["amount"]

        return { "success": True, "data": revenue }

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Retrieve the details of a single transaction by its transaction_id.

        Args:
            transaction_id (str): The ID of the transaction to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": TransactionInfo
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. transaction not found
            }

        Constraints:
            - The transaction must exist in the system.
        """
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            return { "success": False, "error": "Transaction not found" }
        return { "success": True, "data": transaction }

    def list_bookings_by_hotel(self, hotel_id: str) -> dict:
        """
        List all bookings associated with a particular hotel.

        Args:
            hotel_id (str): The unique ID of the hotel.

        Returns:
            dict: {
                "success": True,
                "data": List[BookingInfo]  # List of bookings (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., hotel not found
            }

        Constraints:
            - The hotel_id must exist in the hotels database.
            - Returns all bookings referencing the hotel (no filtering by status).
        """
        if hotel_id not in self.hotels:
            return {
                "success": False,
                "error": "Hotel not found"
            }
    
        bookings = [
            booking for booking in self.bookings.values()
            if booking["hotel_id"] == hotel_id
        ]
        return {
            "success": True,
            "data": bookings
        }

    def get_booking_by_id(self, booking_id: str) -> dict:
        """
        Retrieve a specific booking's details.

        Args:
            booking_id (str): The unique booking identifier.

        Returns:
            dict: 
                {"success": True, "data": BookingInfo} if found
                {"success": False, "error": "Booking not found"} if not found

        Constraints:
            - The booking_id must exist in the PMS.
        """
        if booking_id not in self.bookings:
            return {"success": False, "error": "Booking not found"}
        return {"success": True, "data": self.bookings[booking_id]}

    def get_guest_by_id(self, guest_id: str) -> dict:
        """
        Retrieve guest information by guest_id.
    
        Args:
            guest_id (str): The unique identifier of the guest.
        
        Returns:
            dict:
                - success: True and data (GuestInfo) if found.
                - success: False and error message if guest_id not found.
        """
        guest = self.guests.get(guest_id)
        if guest is None:
            return {"success": False, "error": "Guest not found"}
        return {"success": True, "data": guest}

    def list_guests_by_hotel(self, hotel_id: str) -> dict:
        """
        List all unique guests (GuestInfo) who have bookings or transactions with the specified hotel.

        Args:
            hotel_id (str): The unique identifier of the hotel.

        Returns:
            dict:
                success: True
                data: list of GuestInfo dicts (may be empty if no guests related to hotel)
            OR
                success: False
                error: error message (if hotel does not exist)

        Constraints:
            - Only guests present in the 'guests' state are returned.
            - No duplicates: each guest appears only once in the list.
        """
        if hotel_id not in self.hotels:
            return {"success": False, "error": "Hotel does not exist"}

        guest_ids = set()

        # Collect guest_ids from bookings
        for booking in self.bookings.values():
            if booking.get("hotel_id") == hotel_id:
                guest_ids.add(booking.get("guest_id"))

        # Collect guest_ids from transactions
        for txn in self.transactions.values():
            if txn.get("hotel_id") == hotel_id:
                guest_ids.add(txn.get("guest_id"))

        # Prepare result, including only guests present in self.guests
        guests_list = [
            self.guests[g_id] for g_id in guest_ids
            if g_id in self.guests
        ]

        return {"success": True, "data": guests_list}

    def add_hotel(self, hotel_id: str, name: str, location: str, property_type: str) -> dict:
        """
        Add a new hotel to the system.

        Args:
            hotel_id (str): Unique identifier for the hotel (must not already exist).
            name (str): Hotel name.
            location (str): Hotel location.
            property_type (str): Hotel property type (e.g., resort, motel, etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Hotel added successfully."
            }
            OR
            {
                "success": False,
                "error": "...reason..."
            }

        Constraints:
            - hotel_id must be unique (not already present in the system).
        """
        if hotel_id in self.hotels:
            return {
                "success": False,
                "error": f"Hotel ID '{hotel_id}' already exists."
            }

        self.hotels[hotel_id] = {
            "hotel_id": hotel_id,
            "name": name,
            "location": location,
            "property_type": property_type
        }
        return {
            "success": True,
            "message": "Hotel added successfully."
        }

    def update_hotel_info(self, hotel_id: str, name: str = None, location: str = None, property_type: str = None) -> dict:
        """
        Update the attributes of an existing hotel (name, location, property_type).

        Args:
            hotel_id (str): The unique identifier of the hotel to update.
            name (str, optional): New name for the hotel.
            location (str, optional): New location for the hotel.
            property_type (str, optional): New property type for the hotel.

        Returns:
            dict: {
                "success": True,
                "message": "Hotel information updated."
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - hotel_id must exist.
            - At least one updatable attribute must be provided.
            - Unknown fields are ignored; if no fields to update are valid, operation does nothing and returns error.
        """
        if hotel_id not in self.hotels:
            return {"success": False, "error": "Hotel not found."}

        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if location is not None:
            update_fields["location"] = location
        if property_type is not None:
            update_fields["property_type"] = property_type

        if not update_fields:
            return {"success": False, "error": "No attributes provided to update."}

        # Update only the specified fields
        self.hotels[hotel_id].update(update_fields)

        return {"success": True, "message": "Hotel information updated."}

    def add_transaction(
        self,
        transaction_id: str,
        hotel_id: str,
        booking_id: str,
        guest_id: str,
        amount: float,
        date: str,
        payment_method: str,
        transaction_type: str,
        status: str
    ) -> dict:
        """
        Record a new transaction linked to a hotel, booking, and guest.
    
        Args:
            transaction_id (str): Unique identifier for the transaction.
            hotel_id (str): The hotel the transaction is associated with.
            booking_id (str): The booking the transaction is associated with.
            guest_id (str): The guest responsible for the transaction.
            amount (float): Transaction amount.
            date (str): Transaction date.
            payment_method (str): Method of payment.
            transaction_type (str): Type of transaction (e.g., charge/refund).
            status (str): Transaction status.
    
        Returns:
            dict: {
                "success": True,
                "message": "Transaction <transaction_id> added."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - transaction_id must be unique.
            - hotel_id, guest_id, booking_id must exist.
            - Booking must belong to hotel_id and reference guest_id.
        """
        # Check for unique transaction_id
        if transaction_id in self.transactions:
            return { "success": False, "error": "Transaction ID already exists." }
    
        # Check hotel exists
        if hotel_id not in self.hotels:
            return { "success": False, "error": "Hotel ID does not exist." }
    
        # Check guest exists
        if guest_id not in self.guests:
            return { "success": False, "error": "Guest ID does not exist." }
    
        # Check booking exists
        if booking_id not in self.bookings:
            return { "success": False, "error": "Booking ID does not exist." }
    
        booking = self.bookings[booking_id]

        # Booking links must match hotel and guest
        if booking["hotel_id"] != hotel_id:
            return { "success": False, "error": "Booking does not belong to the specified hotel." }
        if booking["guest_id"] != guest_id:
            return { "success": False, "error": "Booking does not reference the specified guest." }

        # Construct transaction
        txn: TransactionInfo = {
            "transaction_id": transaction_id,
            "hotel_id": hotel_id,
            "booking_id": booking_id,
            "guest_id": guest_id,
            "amount": amount,
            "date": date,
            "payment_method": payment_method,
            "transaction_type": transaction_type,
            "status": status
        }

        self.transactions[transaction_id] = txn

        return {
            "success": True,
            "message": f"Transaction {transaction_id} added."
        }

    def update_transaction_status(self, transaction_id: str, new_status: str) -> dict:
        """
        Change the status of a transaction to the specified new status.

        Args:
            transaction_id (str): The unique identifier of the transaction to update.
            new_status (str): The new status for the transaction (e.g., "completed", "pending", etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Transaction status updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., transaction does not exist)
            }

        Constraints:
            - Transaction with given transaction_id must exist.
            - No restrictions on permissible status values, as per current environment constraints.
        """
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            return { "success": False, "error": "Transaction does not exist" }

        transaction["status"] = new_status
        return { "success": True, "message": "Transaction status updated successfully" }

    def add_booking(
        self,
        hotel_id: str,
        guest_id: str,
        room_number: str,
        check_in_date: str,
        check_out_date: str,
        status: str,
        total_amount: float,
    ) -> dict:
        """
        Create a new booking, tying together hotel, guest, and room assignment.

        Args:
            hotel_id (str): ID of the hotel.
            guest_id (str): ID of the guest.
            room_number (str): Assigned room number.
            check_in_date (str): Check-in date (ISO format recommended).
            check_out_date (str): Check-out date (ISO format recommended).
            status (str): Status of the booking (e.g., 'reserved', 'checked_in').
            total_amount (float): Total amount for the stay.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Booking created",
                    "booking_id": <new_booking_id>
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - The hotel_id must reference an existing hotel.
            - The guest_id must reference an existing guest.
            - Booking ID must be unique.
        """
        # Check existence of hotel and guest
        if hotel_id not in self.hotels:
            return {"success": False, "error": "Hotel does not exist"}
        if guest_id not in self.guests:
            return {"success": False, "error": "Guest does not exist"}

        # Booking id auto-generation (simple increment or uuid-based)
        booking_id = str(uuid.uuid4())
        if booking_id in self.bookings:
            return {"success": False, "error": "Generated booking_id already exists (try again)"}

        # Create and store booking
        booking_info = {
            "booking_id": booking_id,
            "hotel_id": hotel_id,
            "guest_id": guest_id,
            "room_number": room_number,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "status": status,
            "total_amount": total_amount,
        }
        self.bookings[booking_id] = booking_info

        return {
            "success": True,
            "message": "Booking created",
            "booking_id": booking_id
        }

    def update_booking_status(self, booking_id: str, new_status: str) -> dict:
        """
        Change the reservation status of a booking.

        Args:
            booking_id (str): The unique identifier of the booking.
            new_status (str): The target status to set (e.g., "confirmed", "checked-in", "cancelled").

        Returns:
            dict: {
                "success": True,
                "message": "Booking status updated successfully."
            }
            or
            {
                "success": False,
                "error": "Booking not found."
            }

        Constraints:
            - Booking must exist in the system (booking_id in self.bookings).
            - No restrictions on new_status (unless otherwise specified).
        """
        if booking_id not in self.bookings:
            return { "success": False, "error": "Booking not found." }
        self.bookings[booking_id]["status"] = new_status
        return { "success": True, "message": "Booking status updated successfully." }

    def add_guest(self, guest_id: str, name: str, contact_info: str, loyalty_status: str) -> dict:
        """
        Add a new guest record to the PMS.

        Args:
            guest_id (str): Unique identifier for the guest.
            name (str): Guest's full name.
            contact_info (str): Contact information (phone/email).
            loyalty_status (str): Guest's loyalty status.

        Returns:
            dict: {
                "success": True,
                "message": "Guest added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - guest_id must be unique.
            - guest_id and name must not be empty.
        """
        if not guest_id or not name:
            return {"success": False, "error": "guest_id and name must be provided and non-empty."}

        if guest_id in self.guests:
            return {"success": False, "error": f"Guest with guest_id '{guest_id}' already exists."}

        guest_record = {
            "guest_id": guest_id,
            "name": name,
            "contact_info": contact_info,
            "loyalty_status": loyalty_status
        }
        self.guests[guest_id] = guest_record
        return {"success": True, "message": "Guest added successfully."}

    def update_guest_info(self, guest_id: str, name: str = None, contact_info: str = None, loyalty_status: str = None) -> dict:
        """
        Update guest details (name, contact info, loyalty status) for the given guest_id.

        Args:
            guest_id (str): Unique guest identifier.
            name (str, optional): New guest name.
            contact_info (str, optional): New contact information.
            loyalty_status (str, optional): New loyalty status.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Guest info updated."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - guest_id must exist in self.guests.
            - Only provided fields should be updated.
            - If no fields provided, operation is a no-op and returns an error message.
        """
        if guest_id not in self.guests:
            return {"success": False, "error": "Guest not found."}

        update_fields = {}
        if name is not None:
            update_fields['name'] = name
        if contact_info is not None:
            update_fields['contact_info'] = contact_info
        if loyalty_status is not None:
            update_fields['loyalty_status'] = loyalty_status

        if not update_fields:
            return {"success": False, "error": "No fields provided to update."}

        self.guests[guest_id].update(update_fields)

        return {"success": True, "message": "Guest info updated."}

    def delete_transaction(self, transaction_id: str) -> dict:
        """
        Remove a transaction from the system. 
        This operation is intended for admin use only (for data correction scenarios).
    
        Args:
            transaction_id (str): The unique identifier for the transaction.

        Returns:
            dict: 
                { "success": True, "message": "Transaction <transaction_id> deleted." }
                if the deletion is successful.
                { "success": False, "error": "Transaction not found." }
                if the transaction does not exist.

        Constraints:
            - Transaction must exist to be deleted.
            - Deletion removes the transaction from the system entirely.
        """
        if transaction_id not in self.transactions:
            return {"success": False, "error": "Transaction not found."}
        del self.transactions[transaction_id]
        return {"success": True, "message": f"Transaction {transaction_id} deleted."}

    def delete_booking(self, booking_id: str) -> dict:
        """
        Remove a booking from the system by its booking_id.

        Args:
            booking_id (str): Unique booking identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Booking deleted successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Booking must exist.
            - Booking cannot be deleted if any transactions reference it.
        """
        if booking_id not in self.bookings:
            return { "success": False, "error": "Booking does not exist" }

        # Check if any transaction references this booking
        for transaction in self.transactions.values():
            if transaction["booking_id"] == booking_id:
                return { "success": False, "error": "Cannot delete booking: referenced by a transaction" }

        del self.bookings[booking_id]
        return { "success": True, "message": "Booking deleted successfully" }


class HotelPropertyManagementSystem(BaseEnv):
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

    def get_hotel_by_id(self, **kwargs):
        return self._call_inner_tool('get_hotel_by_id', kwargs)

    def get_hotel_by_name(self, **kwargs):
        return self._call_inner_tool('get_hotel_by_name', kwargs)

    def list_hotels(self, **kwargs):
        return self._call_inner_tool('list_hotels', kwargs)

    def list_transactions_by_hotel(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_hotel', kwargs)

    def list_transactions_by_hotel_and_status(self, **kwargs):
        return self._call_inner_tool('list_transactions_by_hotel_and_status', kwargs)

    def calculate_hotel_revenue(self, **kwargs):
        return self._call_inner_tool('calculate_hotel_revenue', kwargs)

    def get_transaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_transaction_by_id', kwargs)

    def list_bookings_by_hotel(self, **kwargs):
        return self._call_inner_tool('list_bookings_by_hotel', kwargs)

    def get_booking_by_id(self, **kwargs):
        return self._call_inner_tool('get_booking_by_id', kwargs)

    def get_guest_by_id(self, **kwargs):
        return self._call_inner_tool('get_guest_by_id', kwargs)

    def list_guests_by_hotel(self, **kwargs):
        return self._call_inner_tool('list_guests_by_hotel', kwargs)

    def add_hotel(self, **kwargs):
        return self._call_inner_tool('add_hotel', kwargs)

    def update_hotel_info(self, **kwargs):
        return self._call_inner_tool('update_hotel_info', kwargs)

    def add_transaction(self, **kwargs):
        return self._call_inner_tool('add_transaction', kwargs)

    def update_transaction_status(self, **kwargs):
        return self._call_inner_tool('update_transaction_status', kwargs)

    def add_booking(self, **kwargs):
        return self._call_inner_tool('add_booking', kwargs)

    def update_booking_status(self, **kwargs):
        return self._call_inner_tool('update_booking_status', kwargs)

    def add_guest(self, **kwargs):
        return self._call_inner_tool('add_guest', kwargs)

    def update_guest_info(self, **kwargs):
        return self._call_inner_tool('update_guest_info', kwargs)

    def delete_transaction(self, **kwargs):
        return self._call_inner_tool('delete_transaction', kwargs)

    def delete_booking(self, **kwargs):
        return self._call_inner_tool('delete_booking', kwargs)

