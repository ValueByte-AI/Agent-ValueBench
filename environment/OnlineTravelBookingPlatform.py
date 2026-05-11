# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any, Optional
import time



# -- TypedDicts mapping state space entities --

class FlightOfferInfo(TypedDict):
    flight_id: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: float
    airline: str
    stops: int
    available_seats: int
    amen: List[str]  # Amenities

class HotelOfferInfo(TypedDict):
    hotel_id: str
    name: str
    location: str
    price_per_night: float
    rating: float
    available_rooms: int
    amenities: List[str]
    description: str

class SearchQueryInfo(TypedDict, total=False):
    origin: Optional[str]
    destination: Optional[str]
    dates: Any
    preferences: Any

class UserSearchSessionInfo(TypedDict):
    _id: str
    current_query: SearchQueryInfo
    last_search_time: str
    filters_applied: Dict[str, Any]
    sort_option: str

class BookingInfo(TypedDict):
    booking_id: str
    user_id: str
    type: str  # 'flight' | 'hotel'
    offer_id: str
    booking_status: str
    booking_time: str
    price_paid: float

class UserInfo(TypedDict):
    _id: str
    name: str
    booking_history: List[str]  # List of booking IDs

# -- Environment class --

class _GeneratedEnvImpl:
    def __init__(self):
        # FlightOffers: {flight_id: FlightOfferInfo}
        self.flight_offers: Dict[str, FlightOfferInfo] = {}

        # HotelOffers: {hotel_id: HotelOfferInfo}
        self.hotel_offers: Dict[str, HotelOfferInfo] = {}

        # UserSearchSessions: {_id: UserSearchSessionInfo}
        self.user_search_sessions: Dict[str, UserSearchSessionInfo] = {}

        # Bookings: {booking_id: BookingInfo}
        self.bookings: Dict[str, BookingInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Flight search results must not show offers lacking available seats.
        # - Hotel search results must not show offers lacking available rooms for specified dates.
        # - Filtering/sorting must be consistent with user criteria (e.g., non-stop flights, sort by price/rating).
        # - Bookings can only be created if the selected offer has current availability.
        # - Search sessions must maintain integrity of filters/sort during active use.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the user profile and booking history by user ID.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserInfo,  # Contains _id, name, booking_history (list of booking IDs)
                    }
                On failure (user not found):
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - None (retrieval only; direct lookup by ID).
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_flight_offer_by_id(self, flight_id: str) -> dict:
        """
        Retrieve detailed information for a specific flight offer by its ID.

        Args:
            flight_id (str): Unique identifier of the flight offer.

        Returns:
            dict: {
                "success": True,
                "data": FlightOfferInfo,  # Flight offer detail if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., not found)
            }

        Constraints:
            - flight_id must exist in the platform's flight_offers.
        """
        flight = self.flight_offers.get(flight_id)
        if not flight:
            return { "success": False, "error": "Flight offer not found" }
        return { "success": True, "data": flight }

    def search_flight_offers(
        self,
        origin: str = None,
        destination: str = None,
        date: str = None,
        filters: Optional[dict] = None,
        sort_by: str = "price",
        sort_order: str = "asc"
    ) -> dict:
        """
        Query for flight offers matching origin, destination, and optionally date, with further filtering and sorting.
        Only returns offers where available_seats > 0.

        Args:
            origin (Optional[str]): Required origin airport code or name.
            destination (Optional[str]): Required destination airport code or name.
            date (Optional[str]): Optional date string (should match departure_time; simplified as substring for this simulation).
            filters (Optional[dict]): Dictionary of filter options, e.g. {"non_stop": True, "airline": "UA"}.
            sort_by (str): Field to sort by ("price", "departure_time", etc). Defaults to 'price'.
            sort_order (str): 'asc' or 'desc'. Defaults to 'asc'.

        Returns:
            dict: {
                "success": True,
                "data": List[FlightOfferInfo],  # list may be empty if no results
            }
            or
            {
                "success": False,
                "error": str  # error description
            }
        """
        # Step 1: Gather and filter offers with available seats
        offers = [
            fo for fo in self.flight_offers.values()
            if fo.get("available_seats", 0) > 0
        ]

        # Step 2: Filter by origin, destination, and date
        if origin is not None:
            offers = [fo for fo in offers if fo.get("origin") == origin]
        if destination is not None:
            offers = [fo for fo in offers if fo.get("destination") == destination]
        if date is not None:
            # Simplified: check if date is substring of 'departure_time'
            offers = [fo for fo in offers if date in fo.get("departure_time", "")]

        # Step 3: Apply optional filters
        if filters:
            # Non-stop filter
            if filters.get("non_stop") is True:
                offers = [fo for fo in offers if fo.get("stops", 0) == 0]
            # Airline filter
            if "airline" in filters:
                offers = [fo for fo in offers if fo.get("airline") == filters["airline"]]
            # Amenities filter (must all be present)
            if "amenities" in filters:
                required_amen = set(filters["amenities"])
                offers = [
                    fo for fo in offers
                    if required_amen.issubset(set(fo.get("amen", [])))
                ]
            # Additional filters can be added here

        # Step 4: Sort results
        reverse = sort_order == "desc"
        allowed_sort_fields = {"price", "departure_time", "arrival_time", "stops"}
        if sort_by not in allowed_sort_fields:
            sort_by = "price"
        try:
            offers = sorted(offers, key=lambda fo: fo.get(sort_by, ""), reverse=reverse)
        except Exception:
            # If any sorting fails (e.g., by unexpected field type), default to price
            offers = sorted(offers, key=lambda fo: fo.get("price", float("inf")), reverse=reverse)

        return {"success": True, "data": offers}

    def list_available_flight_offers(
        self,
        origin: str = None,
        destination: str = None,
        min_price: float = None,
        max_price: float = None,
        max_stops: int = None,
        airline: str = None,
        amenities: list = None
    ) -> dict:
        """
        Retrieve all flight offers with at least one available seat, optionally filtered by criteria.

        Args:
            origin (str, optional): Filter by flight origin.
            destination (str, optional): Filter by flight destination.
            min_price (float, optional): Minimum flight price.
            max_price (float, optional): Maximum flight price.
            max_stops (int, optional): Maximum number of stops allowed.
            airline (str, optional): Filter by airline.
            amenities (list of str, optional): If provided, only flights that include ALL these amenities are returned.

        Returns:
            dict:
                success: True if query is valid, data is a list of FlightOfferInfo (may be empty if no matches).
                success: False if filter input is invalid (e.g., amenities not a list).

        Constraints:
            - Only flights with available_seats >= 1 are returned.

        Edge Cases:
            - If no offers match filters, returns empty data with success True.
        """
        # Validate amenities parameter
        if amenities is not None and not isinstance(amenities, list):
            return { "success": False, "error": "Invalid amenities filter, must be a list." }

        results = []
        for offer in self.flight_offers.values():
            if offer["available_seats"] < 1:
                continue

            # Apply filters
            if origin is not None and offer["origin"] != origin:
                continue
            if destination is not None and offer["destination"] != destination:
                continue
            if min_price is not None and offer["price"] < min_price:
                continue
            if max_price is not None and offer["price"] > max_price:
                continue
            if max_stops is not None and offer["stops"] > max_stops:
                continue
            if airline is not None and offer["airline"] != airline:
                continue
            if amenities is not None and not all(a in offer.get("amen", []) for a in amenities):
                continue

            results.append(offer)

        return { "success": True, "data": results }

    def get_hotel_offer_by_id(self, hotel_id: str) -> dict:
        """
        Retrieve detailed information for a specific hotel offer by its unique hotel_id.

        Args:
            hotel_id (str): The unique identifier for the hotel offer.

        Returns:
            dict: {
                "success": True,
                "data": HotelOfferInfo  # all metadata for the hotel if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. 'Hotel offer not found'
            }

        Constraints:
            - No additional constraints for this "get by ID" operation.
        """
        hotel_offer = self.hotel_offers.get(hotel_id)
        if hotel_offer is not None:
            return { "success": True, "data": hotel_offer }
        else:
            return { "success": False, "error": "Hotel offer not found" }

    def search_hotel_offers(
        self,
        location: str,
        required_amenities: Optional[list] = None,
        sort_by: Optional[str] = "price_per_night",
        sort_order: Optional[str] = "asc"
    ) -> dict:
        """
        Query hotel offers in a given location with available rooms, 
        supporting filtering on amenities and sorting by a column.

        Args:
            location (str): The location (city/area) to search hotels in.
            required_amenities (Optional[list]): List of required amenities each result must include.
            sort_by (Optional[str]): The field to sort results by ('price_per_night', 'rating'). Default is 'price_per_night'.
            sort_order (Optional[str]): 'asc' for ascending, 'desc' for descending. Default is 'asc'.

        Returns:
            dict: {
                "success": True,
                "data": List[HotelOfferInfo],  # List of hotel offers matching criteria, sorted
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - Only returns hotels at the specified location with available_rooms > 0.
            - If required_amenities is given, hotel must provide *all* listed amenities.
            - Results can be sorted by supported fields.
            - Returns empty list if no hotels match.
        """
        # Validate inputs
        if not isinstance(location, str) or not location.strip():
            return { "success": False, "error": "Location must be a non-empty string" }

        valid_sort_by = {"price_per_night", "rating"}
        if sort_by not in valid_sort_by:
            # Fall back to default
            sort_by = "price_per_night"
        if sort_order not in ("asc", "desc"):
            sort_order = "asc"

        filtered = []
        for hotel in self.hotel_offers.values():
            if hotel["location"] != location:
                continue
            if hotel["available_rooms"] <= 0:
                continue
            if required_amenities:
                if not all(am in hotel["amenities"] for am in required_amenities):
                    continue
            filtered.append(hotel)

        reverse = (sort_order == "desc")
        filtered = sorted(filtered, key=lambda x: x[sort_by], reverse=reverse)

        return { "success": True, "data": filtered }

    def list_available_hotel_offers(self, location: str = None) -> dict:
        """
        Retrieve all hotel offers with at least one available room.
        Optionally filter by location.

        Args:
            location (str, optional): If given, filter results to this location.
    
        Returns:
            dict: {
                "success": True,
                "data": List[HotelOfferInfo],  # List of hotels matching criteria (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - Only returns hotel offers where available_rooms > 0.
            - If location is provided, only hotels with HotelOfferInfo["location"] == location are included.
        """
        # Validate location if present
        if location is not None and not isinstance(location, str):
            return { "success": False, "error": "Invalid location" }

        result = [
            hotel_info for hotel_info in self.hotel_offers.values()
            if hotel_info["available_rooms"] > 0 and
                (location is None or hotel_info["location"] == location)
        ]

        return { "success": True, "data": result }

    def get_user_search_session(self, user_id: str) -> dict:
        """
        Retrieve the current search session info for a user, including applied filters, query parameters, and sort option.

        Args:
            user_id (str): The user's identifier.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": UserSearchSessionInfo
                    }
                On failure (e.g. session not found):
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - Only retrieves information if a search session for the given user exists.
            - If not found, returns an error with a message.
        """
        if not user_id or not isinstance(user_id, str):
            return { "success": False, "error": "Invalid user_id provided." }

        session = self.user_search_sessions.get(user_id)
        if session is None:
            # Some case data stores sessions by session_id rather than by user_id.
            # When there is exactly one active session in scope, expose that session
            # instead of forcing the caller to guess the storage key.
            if len(self.user_search_sessions) == 1:
                session = next(iter(self.user_search_sessions.values()))
            else:
                return { "success": False, "error": "No active search session for this user." }

        # Return a copy to prevent potential mutation by reference
        return { "success": True, "data": dict(session) }

    def get_booking_by_id(self, booking_id: str) -> dict:
        """
        Retrieve full details of a booking using its unique ID.

        Args:
            booking_id (str): The booking identifier.

        Returns:
            dict: {
                "success": True,
                "data": BookingInfo  # All booking details
            }
            or
            {
                "success": False,
                "error": str  # "Booking not found"
            }

        Constraints:
            - The booking ID must exist in the system.
        """
        booking = self.bookings.get(booking_id)
        if booking is None:
            return { "success": False, "error": "Booking not found" }
        return { "success": True, "data": booking }

    def list_user_bookings(self, user_id: str, booking_type: str = None, status: str = None) -> dict:
        """
        List all bookings for a user, possibly filtered by type ('flight'/'hotel') and/or booking status.

        Args:
            user_id (str): The user's unique identifier.
            booking_type (str, optional): Filter by booking type ('flight' or 'hotel'). Default: None.
            status (str, optional): Filter by booking status (e.g., 'confirmed', 'cancelled'). Default: None.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": [BookingInfo, ...]}
                    # data may be an empty list if the user has no (matching) bookings.
                On failure:
                    {"success": False, "error": str}
    
        Constraints:
            - User must exist.
            - Only existing booking IDs in booking_history are returned.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}

        booking_ids = user.get("booking_history", [])
        result = []
        for booking_id in booking_ids:
            booking = self.bookings.get(booking_id)
            if booking is None:
                continue  # Skip missing/corrupted record
            if booking_type and booking.get("type") != booking_type:
                continue
            if status and booking.get("booking_status") != status:
                continue
            result.append(booking)

        return {"success": True, "data": result}

    def update_user_search_session(
        self,
        session_id: str,
        current_query: Optional[dict] = None,
        filters_applied: Optional[dict] = None,
        sort_option: Optional[str] = None,
    ) -> dict:
        """
        Update the user's search session data:
        - current_query (search parameters dictionary)
        - filters_applied (dictionary of applied filters)
        - sort_option (string for preferred sorting)

        Args:
            session_id (str): The ID of the user's search session to update.
            current_query (dict, optional): New search parameters (origin, destination, dates, preferences).
            filters_applied (dict, optional): Update to the filters being applied.
            sort_option (str, optional): Preferred sorting method.

        Returns:
            dict:
                - On success: { "success": True, "message": "User search session updated." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The session identified by session_id must exist.
            - Only provided fields are updated; omitted ones remain unchanged.
            - After update, session data should maintain integrity of filters and sorting option.
        """
        session = self.user_search_sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "User search session not found." }

        # Update fields if provided
        updated = False
        if current_query is not None:
            session['current_query'] = current_query
            updated = True
        if filters_applied is not None:
            session['filters_applied'] = filters_applied
            updated = True
        if sort_option is not None:
            session['sort_option'] = sort_option
            updated = True

        # No fields to update (all None) is still a "no-op" success
        return { "success": True, "message": "User search session updated." }

    def apply_flight_search_filters(
        self, 
        session_id: str, 
        filters: Dict[str, Any], 
        sort_option: str
    ) -> dict:
        """
        Set or update filters and sorting to be used in a flight search session.

        Args:
            session_id (str): The ID of the user search session to update.
            filters (Dict[str, Any]): Dictionary of filters to apply (e.g., {'non_stop': True}).
            sort_option (str): The sort option to set (e.g., 'price', 'duration').

        Returns:
            dict: {
                "success": True,
                "message": "Flight search filters and sort option updated."
            }
            OR
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - Session must exist.
            - Updates filters and sort_option atomically to maintain session integrity.
        """
        # Check that session exists
        if session_id not in self.user_search_sessions:
            return {"success": False, "error": "User search session does not exist."}

        # Type validation (basic)
        if not isinstance(filters, dict):
            return {"success": False, "error": "Filters must be a dictionary."}
        if not isinstance(sort_option, str):
            return {"success": False, "error": "Sort option must be a string."}

        # Update session atomically
        session = self.user_search_sessions[session_id]
        session['filters_applied'] = filters
        session['sort_option'] = sort_option
        self.user_search_sessions[session_id] = session

        return {"success": True, "message": "Flight search filters and sort option updated."}

    def apply_hotel_search_filters(
        self,
        session_id: str,
        filters: Dict[str, Any],
        sort_option: str
    ) -> dict:
        """
        Set or update filters and sorting for a hotel search session.

        Args:
            session_id (str): The ID of the user search session to update.
            filters (Dict[str, Any]): Dictionary of filter criteria (e.g., required amenities, minimum rating).
            sort_option (str): Sorting option for hotel search results (e.g., 'price', 'rating').

        Returns:
            dict: 
              - { "success": True, "message": "Hotel search filters and/or sort option applied." }
              - { "success": False, "error": "<reason>" }

        Constraints:
            - The search session with `session_id` must exist.
            - The search session's filters and sort option are updated as specified.
            - No exception is raised; errors are returned in result dict.
        """
        session = self.user_search_sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Search session does not exist." }
        # Update filters (replace or merge depending on your rules; here we replace)
        session["filters_applied"] = filters.copy() if filters else {}
        # Update sort option
        session["sort_option"] = sort_option
        return { "success": True, "message": "Hotel search filters and/or sort option applied." }

    def create_booking(
        self, user_id: str, type: str, offer_id: str
    ) -> dict:
        """
        Create a new booking for a flight or hotel offer.
        Checks availability and updates the offer's available seats/rooms and the user's booking history.

        Args:
            user_id (str): ID of the user making the booking.
            type (str): "flight" or "hotel".
            offer_id (str): flight_id or hotel_id, depending on the booking type.

        Returns:
            dict: {
                "success": True,
                "message": "Booking created successfully",
                "booking_id": <booking_id>,
            }
            or
            {
                "success": False,
                "error": <reason>,
            }

        Constraints:
            - Booking possible only if offer exists and has current availability.
            - Updates offer inventory and user's booking history.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Normalize booking type
        btype = type.lower()
        if btype not in ("flight", "hotel"):
            return {"success": False, "error": "Invalid booking type"}

        # Fetch offer; check existence and availability
        offer = None
        price_paid = None
        if btype == "flight":
            if offer_id not in self.flight_offers:
                return {"success": False, "error": "Flight offer does not exist"}
            offer = self.flight_offers[offer_id]
            if offer.get("available_seats", 0) <= 0:
                return {"success": False, "error": "No available seats for this flight"}
            # Update availability
            offer["available_seats"] -= 1
            price_paid = offer["price"]
        else:  # hotel
            if offer_id not in self.hotel_offers:
                return {"success": False, "error": "Hotel offer does not exist"}
            offer = self.hotel_offers[offer_id]
            if offer.get("available_rooms", 0) <= 0:
                return {"success": False, "error": "No available rooms for this hotel"}
            # Update availability
            offer["available_rooms"] -= 1
            price_paid = offer["price_per_night"]

        # Generate booking_id (simple time+counter method)
        booking_id = f"BKG-{int(time.time() * 1000)}-{len(self.bookings)+1}"

        # Build booking info
        booking_info = {
            "booking_id": booking_id,
            "user_id": user_id,
            "type": btype,
            "offer_id": offer_id,
            "booking_status": "confirmed",
            "booking_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "price_paid": price_paid,
        }

        # Store booking
        self.bookings[booking_id] = booking_info

        # Update user's booking history
        self.users[user_id]["booking_history"].append(booking_id)

        return {"success": True, "message": "Booking created successfully", "booking_id": booking_id}

    def update_booking_status(self, booking_id: str, new_status: str) -> dict:
        """
        Change the status of an existing booking.

        Args:
            booking_id (str): The unique identifier of the booking to update.
            new_status (str): The new status to set (e.g., "confirmed", "cancelled", etc.).

        Returns:
            dict: 
                On success: 
                    {"success": True, "message": "Booking status updated successfully."}
                On failure: 
                    {"success": False, "error": <error message>}
    
        Constraints:
            - booking_id must exist in the system.
            - No restrictions on allowed statuses for this operation.
        """
        booking = self.bookings.get(booking_id)
        if booking is None:
            return {"success": False, "error": "Booking not found."}

        booking["booking_status"] = new_status
        # Optionally, persist the update by re-assigning if required by system design (not needed here for dicts).
        return {"success": True, "message": "Booking status updated successfully."}

    def adjust_offer_availability(self, offer_type: str, offer_id: str, count: int = 1) -> dict:
        """
        Decrements available seats (for flights) or available rooms (for hotels) of the specified offer.

        Args:
            offer_type (str): 'flight' or 'hotel'.
            offer_id (str): The unique ID of the offer (flight_id or hotel_id).
            count (int, optional): Number of seats/rooms to decrement, default is 1.

        Returns:
            dict: Result status; on success,
                {
                    "success": True,
                    "message": "Availability adjusted."
                }
                On error,
                {
                    "success": False,
                    "error": "<error reason>"
                }

        Constraints:
            - Offer must exist and match the type.
            - count must be >= 1.
            - Will not decrement below zero (if insufficient availability, fail).
        """
        if count < 1:
            return {"success": False, "error": "Decrement count must be at least 1."}

        if offer_type == "flight":
            offer = self.flight_offers.get(offer_id)
            if not offer:
                return {"success": False, "error": "Flight offer not found."}
            if offer["available_seats"] < count:
                return {"success": False, "error": "Not enough available seats to decrement."}
            offer["available_seats"] -= count
            return {"success": True, "message": "Availability adjusted."}

        elif offer_type == "hotel":
            offer = self.hotel_offers.get(offer_id)
            if not offer:
                return {"success": False, "error": "Hotel offer not found."}
            if offer["available_rooms"] < count:
                return {"success": False, "error": "Not enough available rooms to decrement."}
            offer["available_rooms"] -= count
            return {"success": True, "message": "Availability adjusted."}

        else:
            return {"success": False, "error": "Invalid offer type (must be 'flight' or 'hotel')."}

    def reset_user_search_session(self, session_id: str) -> dict:
        """
        Clear or re-initialize the user's search session for a new search cycle.

        Args:
            session_id (str): The session (or user) ID whose search session is to be reset.

        Returns:
            dict: 
                On success: { "success": True, "message": "Search session reset for user/session <id>" }
                On failure (session does not exist): { "success": False, "error": "User search session not found" }

        Constraints:
            - The session must exist.
            - Resets: current_query to empty, last_search_time to '', filters_applied to {}, sort_option to ''.
        """
        if session_id not in self.user_search_sessions:
            return { "success": False, "error": "User search session not found" }
    
        self.user_search_sessions[session_id]['current_query'] = {}
        self.user_search_sessions[session_id]['last_search_time'] = ""
        self.user_search_sessions[session_id]['filters_applied'] = {}
        self.user_search_sessions[session_id]['sort_option'] = ""

        return { "success": True, "message": f"Search session reset for user/session {session_id}" }


class OnlineTravelBookingPlatform(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_flight_offer_by_id(self, **kwargs):
        return self._call_inner_tool('get_flight_offer_by_id', kwargs)

    def search_flight_offers(self, **kwargs):
        return self._call_inner_tool('search_flight_offers', kwargs)

    def list_available_flight_offers(self, **kwargs):
        return self._call_inner_tool('list_available_flight_offers', kwargs)

    def get_hotel_offer_by_id(self, **kwargs):
        return self._call_inner_tool('get_hotel_offer_by_id', kwargs)

    def search_hotel_offers(self, **kwargs):
        return self._call_inner_tool('search_hotel_offers', kwargs)

    def list_available_hotel_offers(self, **kwargs):
        return self._call_inner_tool('list_available_hotel_offers', kwargs)

    def get_user_search_session(self, **kwargs):
        return self._call_inner_tool('get_user_search_session', kwargs)

    def get_booking_by_id(self, **kwargs):
        return self._call_inner_tool('get_booking_by_id', kwargs)

    def list_user_bookings(self, **kwargs):
        return self._call_inner_tool('list_user_bookings', kwargs)

    def update_user_search_session(self, **kwargs):
        return self._call_inner_tool('update_user_search_session', kwargs)

    def apply_flight_search_filters(self, **kwargs):
        return self._call_inner_tool('apply_flight_search_filters', kwargs)

    def apply_hotel_search_filters(self, **kwargs):
        return self._call_inner_tool('apply_hotel_search_filters', kwargs)

    def create_booking(self, **kwargs):
        return self._call_inner_tool('create_booking', kwargs)

    def update_booking_status(self, **kwargs):
        return self._call_inner_tool('update_booking_status', kwargs)

    def adjust_offer_availability(self, **kwargs):
        return self._call_inner_tool('adjust_offer_availability', kwargs)

    def reset_user_search_session(self, **kwargs):
        return self._call_inner_tool('reset_user_search_session', kwargs)
