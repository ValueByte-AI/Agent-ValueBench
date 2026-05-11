# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class EventInfo(TypedDict):
    event_id: str
    name: str
    date: str
    location: str
    description: str

class TicketInfo(TypedDict):
    ticket_id: str
    event_id: str
    price: float
    seat_location: str
    availability_status: str
    ticket_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Stateful environment for event ticketing management.
        """

        # Events: {event_id: EventInfo}
        # Each entity in EventInfo: event_id, name, date, location, description
        self.events: Dict[str, EventInfo] = {}

        # Tickets: {ticket_id: TicketInfo}
        # Each entity in TicketInfo: ticket_id, event_id, price, seat_location, availability_status, ticket_type
        self.tickets: Dict[str, TicketInfo] = {}

        # Constraints:
        # - Each ticket must be associated with exactly one event (event_id is foreign key in TicketInfo)
        # - availability_status determines if a ticket can be sold or reserved (available, reserved, sold, etc.)
        # - No two tickets for the same event can have the same seat_location if seat assignments are unique

    def get_event_info(self, event_id: str) -> dict:
        """
        Retrieve core details (name, date, location, description) for a specific event by event_id.

        Args:
            event_id (str): The ID of the event to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": EventInfo     # event_id, name, date, location, description
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The specified event_id must exist in the system.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }
        return { "success": True, "data": self.events[event_id] }

    def list_tickets_by_event(self, event_id: str) -> dict:
        """
        Retrieve all tickets (TicketInfo) associated with a specified event.

        Args:
            event_id (str): The ID of the event for which tickets should be retrieved.

        Returns:
            dict: {
                'success': True,
                'data': List[TicketInfo]  # All tickets for this event (may be empty)
            }
            or
            {
                'success': False,
                'error': str  # Error description, e.g. event does not exist
            }

        Constraints:
            - The provided event_id must exist in the system.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        tickets = [
            ticket_info for ticket_info in self.tickets.values()
            if ticket_info["event_id"] == event_id
        ]
        return { "success": True, "data": tickets }

    def list_available_tickets_by_event(self, event_id: str) -> dict:
        """
        Retrieve all tickets that are currently available (availability_status="available")
        for a given event_id.

        Args:
            event_id (str): The identifier for the event.

        Returns:
            dict: {
                "success": True,
                "data": List[TicketInfo]  # List of ticket info dicts with availability_status == "available"
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Event does not exist"
            }

        Constraints:
            - The provided event_id must exist in the events table.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        available_tickets = [
            ticket for ticket in self.tickets.values()
            if ticket["event_id"] == event_id and ticket["availability_status"] == "available"
        ]

        return {"success": True, "data": available_tickets}

    def get_ticket_info(self, ticket_id: str) -> dict:
        """
        Retrieve details for a specific ticket by its ticket_id.

        Args:
            ticket_id (str): The unique identifier of the ticket.

        Returns:
            dict:
                - On success: {"success": True, "data": TicketInfo}
                - On failure: {"success": False, "error": "Ticket not found"}
        """
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            return {"success": False, "error": "Ticket not found"}
        return {"success": True, "data": ticket}

    def list_tickets_by_availability_status(self, event_id: str, availability_status: str) -> dict:
        """
        Retrieve all tickets for the specified event_id that match the given availability_status.

        Args:
            event_id (str): The unique ID of the event for which to search tickets.
            availability_status (str): The availability status to filter by (e.g., 'available', 'sold', 'reserved').

        Returns:
            dict: {
                "success": True,
                "data": List[TicketInfo],  # All tickets matching event_id and availability_status (may be [])
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., event does not exist.
            }

        Constraints:
            - event_id must exist in the system.
            - Only tickets with ticket.event_id == event_id and ticket.availability_status == availability_status are returned.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        result = [
            ticket_info for ticket_info in self.tickets.values()
            if ticket_info["event_id"] == event_id and ticket_info["availability_status"] == availability_status
        ]

        return { "success": True, "data": result }

    def get_event_by_ticket_id(self, ticket_id: str) -> dict:
        """
        Given a ticket_id, retrieve the event information for the event
        associated with that ticket via its event_id.

        Args:
            ticket_id (str): The ID of the ticket whose event is requested.

        Returns:
            dict:
                - On success: {"success": True, "data": EventInfo}
                - On failure: {"success": False, "error": <reason>}
        Constraints:
            - ticket_id must exist in the system.
            - The corresponding event_id must exist in the events list.
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return {"success": False, "error": "Ticket does not exist."}

        event_id = ticket.get("event_id")
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Associated event does not exist."}

        return {"success": True, "data": event}

    def check_seat_location_uniqueness(self, event_id: str, seat_location: str) -> dict:
        """
        Verify that the given seat_location is unique among all tickets for a specific event.

        Args:
            event_id (str): The ID of the event.
            seat_location (str): The seat location string to validate for uniqueness.

        Returns:
            dict:
                If event exists:
                    {
                        "success": True,
                        "unique": bool  # True if seat_location is not used for event, else False
                    }
                If event does not exist:
                    {
                        "success": False,
                        "error": "Event does not exist"
                    }
        Constraints:
            - event_id must exist
            - Returns True if no existing ticket for this event uses seat_location
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        for ticket in self.tickets.values():
            if ticket["event_id"] == event_id and ticket["seat_location"] == seat_location:
                return {"success": True, "unique": False}

        return {"success": True, "unique": True}

    def create_event(
        self,
        event_id: str,
        name: str,
        date: str,
        location: str,
        description: str
    ) -> dict:
        """
        Add a new event to the system with specified details.

        Args:
            event_id (str): Unique identifier for the event.
            name (str): Name of the event.
            date (str): Date string for the event.
            location (str): Location of the event.
            description (str): Description of the event.

        Returns:
            dict: {
                "success": True,
                "message": "Event <event_id> created successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., duplicate event_id, invalid input)
            }

        Constraints:
            - event_id must be unique in the system.
            - All fields must be provided and non-empty.
        """
        # Basic validation: non-empty fields
        if not all([event_id, name, date, location, description]):
            return {
                "success": False,
                "error": "All event fields (event_id, name, date, location, description) must be provided and non-empty."
            }

        # Constraint: event_id uniqueness
        if event_id in self.events:
            return {
                "success": False,
                "error": f"Event with id '{event_id}' already exists."
            }

        event_info: EventInfo = {
            "event_id": event_id,
            "name": name,
            "date": date,
            "location": location,
            "description": description
        }

        self.events[event_id] = event_info

        return {
            "success": True,
            "message": f"Event '{event_id}' created successfully."
        }

    def edit_event(
        self,
        event_id: str,
        name: str = None,
        date: str = None,
        location: str = None,
        description: str = None
    ) -> dict:
        """
        Update the details of an existing event.

        Args:
            event_id (str): The unique ID of the event to update (required).
            name (str, optional): New event name.
            date (str, optional): New event date.
            location (str, optional): New event location.
            description (str, optional): New event description.

        Returns:
            dict: On success:
                { "success": True, "message": "Event updated successfully." }
            On error:
                { "success": False, "error": "Event does not exist." }

        Constraints:
            - Only updates events that exist.
            - event_id itself may not be modified.
            - Attributes not provided are kept unchanged.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist." }

        updated = False
        event = self.events[event_id]
        if name is not None:
            event["name"] = name
            updated = True
        if date is not None:
            event["date"] = date
            updated = True
        if location is not None:
            event["location"] = location
            updated = True
        if description is not None:
            event["description"] = description
            updated = True

        # Save back (not really necessary as dict is mutable, but for explicitness)
        self.events[event_id] = event

        return { "success": True, "message": "Event updated successfully." }

    def create_ticket(
        self,
        ticket_id: str,
        event_id: str,
        price: float,
        seat_location: str,
        availability_status: str,
        ticket_type: str
    ) -> dict:
        """
        Add a new ticket for a specific event.

        Args:
            ticket_id (str): Unique identifier for the new ticket (must not already exist).
            event_id (str): Identifier of the associated event (must exist).
            price (float): Ticket price.
            seat_location (str): Location/seat identifier (must be unique per event if non-empty).
            availability_status (str): Current status ('available', 'reserved', 'sold', etc.).
            ticket_type (str): The type of the ticket, e.g., 'VIP', 'Regular'.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Ticket <ticket_id> created for event <event_id>." }
                On error:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - ticket_id must be unique.
            - event_id must refer to an existing event.
            - seat_location must be unique per event if seat assignments are in use (non-empty).
        """
        # Check event existence
        if event_id not in self.events:
            return {"success": False, "error": f"Event {event_id} does not exist."}

        # Check ticket_id uniqueness
        if ticket_id in self.tickets:
            return {"success": False, "error": f"Ticket ID {ticket_id} already exists."}

        # Check seat_location uniqueness for this event if seat_location is not empty
        if seat_location:
            for ticket in self.tickets.values():
                if ticket["event_id"] == event_id and ticket["seat_location"] == seat_location:
                    return {
                        "success": False,
                        "error": f"Seat location '{seat_location}' is already taken for event {event_id}."
                    }

        # All checks passed — create ticket
        self.tickets[ticket_id] = {
            "ticket_id": ticket_id,
            "event_id": event_id,
            "price": price,
            "seat_location": seat_location,
            "availability_status": availability_status,
            "ticket_type": ticket_type,
        }

        return {
            "success": True,
            "message": f"Ticket {ticket_id} created for event {event_id}."
        }

    def update_ticket_status(self, ticket_id: str, new_status: str) -> dict:
        """
        Change the availability_status of a ticket to a new status.

        Args:
            ticket_id (str): The unique identifier of the ticket whose status is to be updated.
            new_status (str): The new availability status to be assigned (e.g., "reserved", "sold", "available", etc.).

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "message": "Ticket <ticket_id> status updated to <new_status>"
                  }
                - On error: {
                      "success": False,
                      "error": "Ticket not found"
                  }
        Constraints:
            - The specified ticket must exist.
            - No restrictions on valid status values unless specified elsewhere.
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return { "success": False, "error": "Ticket not found" }

        ticket["availability_status"] = new_status
        return {
            "success": True,
            "message": f"Ticket {ticket_id} status updated to {new_status}"
        }

    def update_ticket_info(
        self,
        ticket_id: str,
        seat_location: str = None,
        price: float = None,
        ticket_type: str = None
    ) -> dict:
        """
        Edit ticket details such as seat_location, price, or type.

        Args:
            ticket_id (str): The ID of the ticket to modify.
            seat_location (str, optional): New seat location for the ticket.
            price (float, optional): New price for the ticket (must be >=0).
            ticket_type (str, optional): New ticket type.

        Returns:
            dict:
                Success: { "success": True, "message": "Ticket <ticket_id> updated successfully." }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - Ticket must exist.
            - If seat_location is being updated and seat assignments are unique for the event,
              ensure no other ticket for the same event has the same seat_location.
            - Price must be non-negative if specified.
        """
        if ticket_id not in self.tickets:
            return { "success": False, "error": "Ticket does not exist." }

        ticket = self.tickets[ticket_id]
        event_id = ticket["event_id"]

        # Validate seat_location (if updating)
        if seat_location is not None:
            seat_conflict = any(
                t["seat_location"] == seat_location
                and t["event_id"] == event_id
                and t["ticket_id"] != ticket_id
                for t in self.tickets.values()
            )
            if seat_conflict:
                return {
                    "success": False,
                    "error": f"Seat location '{seat_location}' is already assigned for this event."
                }
            ticket["seat_location"] = seat_location

        # Validate price (if updating)
        if price is not None:
            if not isinstance(price, (int, float)) or price < 0:
                return { "success": False, "error": "Ticket price must be non-negative." }
            ticket["price"] = price

        # Update ticket_type (if updating)
        if ticket_type is not None:
            ticket["ticket_type"] = ticket_type

        # Save back (dict is mutable; already reflects changes)
        self.tickets[ticket_id] = ticket

        return { "success": True, "message": f"Ticket {ticket_id} updated successfully." }

    def delete_ticket(self, ticket_id: str) -> dict:
        """
        Remove a ticket from the system by its ticket_id.

        Args:
            ticket_id (str): The unique identifier of the ticket to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Ticket <ticket_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Ticket not found."
            }

        Constraints:
            - Ticket must exist in the system.
            - Deletion simply removes the ticket; no extra cleanup is necessary as no reverse references.
        """
        if ticket_id not in self.tickets:
            return { "success": False, "error": "Ticket not found." }
    
        del self.tickets[ticket_id]
        return { "success": True, "message": f"Ticket {ticket_id} deleted." }

    def delete_event(self, event_id: str) -> dict:
        """
        Remove an event and all associated tickets from the system.

        Args:
            event_id (str): The ID of the event to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Event and associated tickets deleted"
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - The event must exist in the system.
            - All tickets associated with the event will be deleted.
        """
        if event_id not in self.events:
            return { "success": False, "error": "Event does not exist" }

        # Remove associated tickets
        to_delete = [ticket_id for ticket_id, ticket in self.tickets.items()
                     if ticket["event_id"] == event_id]
        for ticket_id in to_delete:
            del self.tickets[ticket_id]

        # Remove the event
        del self.events[event_id]

        return { "success": True, "message": "Event and associated tickets deleted" }

    def bulk_update_ticket_status_by_event(
        self,
        event_id: str,
        ticket_ids: list,
        new_status: str
    ) -> dict:
        """
        Update availability status for multiple tickets of a given event at once.

        Args:
            event_id (str): The event whose tickets are to be updated.
            ticket_ids (List[str]): List of ticket IDs to update.
            new_status (str): The new availability_status value to assign (e.g., 'reserved', 'available', 'sold').

        Returns:
            dict: {
                "success": True,
                "message": "Updated X tickets' status to '<new_status>' for event <event_id>."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - event_id must exist in the system.
            - All ticket_ids must exist, belong to the event_id, and support status update.
        """
        if event_id not in self.events:
            return {"success": False, "error": "Event does not exist"}

        # Validate ticket IDs
        invalid_ticket_ids = [tid for tid in ticket_ids if tid not in self.tickets]
        if invalid_ticket_ids:
            return {
                "success": False,
                "error": "These ticket_ids do not exist: {}".format(", ".join(invalid_ticket_ids))
            }

        # Validate event association
        wrong_event_tickets = [tid for tid in ticket_ids if self.tickets[tid]['event_id'] != event_id]
        if wrong_event_tickets:
            return {
                "success": False,
                "error": "These tickets do not belong to event {}: {}".format(event_id, ", ".join(wrong_event_tickets))
            }

        # Perform the status update
        for tid in ticket_ids:
            self.tickets[tid]['availability_status'] = new_status

        return {
            "success": True,
            "message": "Updated {} tickets' status to '{}' for event {}.".format(len(ticket_ids), new_status, event_id)
        }

    def validate_and_assign_seat_location(self, ticket_id: str, new_seat_location: str) -> dict:
        """
        Ensure the new seat_location for the ticket is unique within its event,
        and assign the seat location if valid.

        Args:
            ticket_id (str): The ID of the ticket to update.
            new_seat_location (str): The new seat location to assign.

        Returns:
            dict: 
                { "success": True, "message": "Seat location assigned successfully." }
                OR
                { "success": False, "error": <reason str> }

        Constraints:
            - ticket_id must exist.
            - The ticket's associated event must exist.
            - No other ticket for the same event can have the same seat_location.
        """
        if ticket_id not in self.tickets:
            return { "success": False, "error": "Ticket ID does not exist." }

        ticket = self.tickets[ticket_id]
        event_id = ticket["event_id"]

        if event_id not in self.events:
            return { "success": False, "error": "Associated event does not exist." }

        # Check for uniqueness of seat_location within the event (excluding this ticket)
        for t in self.tickets.values():
            if (
                t["event_id"] == event_id and
                t["ticket_id"] != ticket_id and
                t["seat_location"] == new_seat_location
            ):
                return { "success": False, "error": "Seat location already assigned to another ticket in this event." }

        # Assign new seat_location
        self.tickets[ticket_id]["seat_location"] = new_seat_location

        return { "success": True, "message": "Seat location assigned successfully." }


class EventTicketingManagementSystem(BaseEnv):
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

    def get_event_info(self, **kwargs):
        return self._call_inner_tool('get_event_info', kwargs)

    def list_tickets_by_event(self, **kwargs):
        return self._call_inner_tool('list_tickets_by_event', kwargs)

    def list_available_tickets_by_event(self, **kwargs):
        return self._call_inner_tool('list_available_tickets_by_event', kwargs)

    def get_ticket_info(self, **kwargs):
        return self._call_inner_tool('get_ticket_info', kwargs)

    def list_tickets_by_availability_status(self, **kwargs):
        return self._call_inner_tool('list_tickets_by_availability_status', kwargs)

    def get_event_by_ticket_id(self, **kwargs):
        return self._call_inner_tool('get_event_by_ticket_id', kwargs)

    def check_seat_location_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_seat_location_uniqueness', kwargs)

    def create_event(self, **kwargs):
        return self._call_inner_tool('create_event', kwargs)

    def edit_event(self, **kwargs):
        return self._call_inner_tool('edit_event', kwargs)

    def create_ticket(self, **kwargs):
        return self._call_inner_tool('create_ticket', kwargs)

    def update_ticket_status(self, **kwargs):
        return self._call_inner_tool('update_ticket_status', kwargs)

    def update_ticket_info(self, **kwargs):
        return self._call_inner_tool('update_ticket_info', kwargs)

    def delete_ticket(self, **kwargs):
        return self._call_inner_tool('delete_ticket', kwargs)

    def delete_event(self, **kwargs):
        return self._call_inner_tool('delete_event', kwargs)

    def bulk_update_ticket_status_by_event(self, **kwargs):
        return self._call_inner_tool('bulk_update_ticket_status_by_event', kwargs)

    def validate_and_assign_seat_location(self, **kwargs):
        return self._call_inner_tool('validate_and_assign_seat_location', kwargs)

