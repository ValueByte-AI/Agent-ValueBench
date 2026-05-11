# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
import datetime
from dateutil.parser import parse as dateparse



# --- Entity Definitions ---

class CityInfo(TypedDict):
    city_id: str
    city_name: str

class OperatorInfo(TypedDict):
    operator_id: str
    name: str
    contact_info: str

class RouteInfo(TypedDict):
    route_id: str
    origin_city_id: str
    destination_city_id: str
    operator_id: str
    distance: float

class ScheduleInfo(TypedDict):
    schedule_id: str
    route_id: str
    departure_time: str  # ISO 8601 time
    arrival_time: str    # ISO 8601 time
    operating_day: str   # e.g., "Monday", "Tue", or "2024-01-01"

class TripInfo(TypedDict):
    trip_id: str
    schedule_id: str
    departure_date: str  # ISO date
    bus_id: str
    status: str          # scheduled, departed, cancelled, etc.

class BusInfo(TypedDict):
    bus_id: str
    operator_id: str
    seat_capacity: int
    bus_type: str

class SeatInfo(TypedDict):
    seat_id: str
    bus_id: str
    seat_number: str
    seat_class: str      # e.g., standard, premium

class BookingInfo(TypedDict):
    booking_id: str
    trip_id: str
    customer_id: str
    booking_status: str  # reserved, confirmed, cancelled, etc.
    total_price: float
    booking_time: str    # ISO 8601 timestamp

class BookingSeatInfo(TypedDict):
    booking_id: str
    seat_id: str
    seat_status: str       # reserved, confirmed, cancelled, etc.
    passenger_name: str

class FareInfo(TypedDict):
    fare_id: str
    route_id: str
    base_price: float
    fare_rules: str
    effective_date: str    # ISO date

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str
    company_affiliation: str

# --- Environment Class ---

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Intercity bus booking system stateful environment

        Constraints:
        - A seat on a specific trip can be assigned to only one booking at a time.
        - Trip status can affect booking availability (e.g., cannot book on cancelled or departed trips).
        - Fare rules and effective dates determine pricing on a per-trip basis.
        - Bookings may have status (e.g., reserved, confirmed, cancelled), impacting seat occupancy.
        - The number of available seats for a trip is equal to total bus seat capacity minus the number of booked seats (excluding cancelled bookings).
        - Only available seats can be booked; overbooking is not permitted.
        - Schedule and trip timings must be valid with respect to time zones and route distances.
        """

        # Cities {city_id: CityInfo}
        self.cities: Dict[str, CityInfo] = {}
        # Operators {operator_id: OperatorInfo}
        self.operators: Dict[str, OperatorInfo] = {}
        # Routes {route_id: RouteInfo}
        self.routes: Dict[str, RouteInfo] = {}
        # Schedules {schedule_id: ScheduleInfo}
        self.schedules: Dict[str, ScheduleInfo] = {}
        # Trips {trip_id: TripInfo}
        self.trips: Dict[str, TripInfo] = {}
        # Buses {bus_id: BusInfo}
        self.buses: Dict[str, BusInfo] = {}
        # Seats {seat_id: SeatInfo}
        self.seats: Dict[str, SeatInfo] = {}
        # Bookings {booking_id: BookingInfo}
        self.bookings: Dict[str, BookingInfo] = {}
        # BookingSeats {booking_id: List[BookingSeatInfo]}
        self.booking_seats: Dict[str, List[BookingSeatInfo]] = {}
        # Fares {fare_id: FareInfo}
        self.fares: Dict[str, FareInfo] = {}
        # Customers {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # -- Entity mapping comments (from State Space) --
        # self.cities         ← C: city_id, city_name
        # self.operators      ← Operator: operator_id, name, contact_info
        # self.routes         ← Route: route_id, origin_city_id, destination_city_id, operator_id, distance
        # self.schedules      ← Schedule: schedule_id, route_id, departure_time, arrival_time, operating_day
        # self.trips          ← Trip: trip_id, schedule_id, departure_date, bus_id, status
        # self.buses          ← Bus: bus_id, operator_id, seat_capacity, bus_type
        # self.seats          ← Seat: seat_id, bus_id, seat_number, seat_class
        # self.bookings       ← Booking: booking_id, trip_id, customer_id, booking_status, total_price, booking_time
        # self.booking_seats  ← BookingSeat: booking_id, seat_id, seat_status, passenger_name
        # self.fares          ← Fare: fare_id, route_id, base_price, fare_rules, effective_date
        # self.customers      ← Customer: customer_id, name, contact_info, company_affiliation


    def get_city_by_name(self, city_name: str) -> dict:
        """
        Retrieve city info (including city_id) given a city name.

        Args:
            city_name (str): The name of the city to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CityInfo,  # city_id, city_name
                    }
                On failure:
                    {
                        "success": False,
                        "error": "City not found"
                    }

        Constraints:
            - Returns the first city matching the city_name. City names may not be unique.
        """

        for city in self.cities.values():
            if city["city_name"] == city_name:
                return { "success": True, "data": city }
        return { "success": False, "error": "City not found" }

    def get_operator_by_name(self, name: str) -> dict:
        """
        Retrieve operator information using the exact operator company name.

        Args:
            name (str): The exact name of the operator to search for.

        Returns:
            dict: 
                On success: {"success": True, "data": OperatorInfo}
                On failure: {"success": False, "error": "Operator not found"}

        Constraints:
            - The search is case-sensitive and matches the operator's name exactly.
            - If multiple operators have the same name, returns the first found.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing name"}

        for operator_info in self.operators.values():
            if operator_info["name"] == name:
                return {"success": True, "data": operator_info}
        return {"success": False, "error": "Operator not found"}

    def list_routes_by_origin_and_destination(
        self,
        origin_city_id: str,
        destination_city_id: str,
        operator_id: str = None
    ) -> dict:
        """
        Retrieve all routes between the given origin and destination city IDs,
        optionally filtered by operator ID.

        Args:
            origin_city_id (str): ID of the origin city.
            destination_city_id (str): ID of the destination city.
            operator_id (str, optional): If provided, filter only routes operated by this operator.

        Returns:
            dict: {
                "success": True,
                "data": List[RouteInfo],  # List of route info dicts, empty if no match
            }
            OR
            {
                "success": False,
                "error": str,  # Description of error
            }

        Constraints:
            - Both origin and destination city IDs must exist.
            - If operator_id is specified, it must exist.
        """
        if origin_city_id not in self.cities:
            return {"success": False, "error": "Origin city does not exist"}
        if destination_city_id not in self.cities:
            return {"success": False, "error": "Destination city does not exist"}
        if operator_id is not None and operator_id not in self.operators:
            return {"success": False, "error": "Operator does not exist"}

        routes = [
            route for route in self.routes.values()
            if route['origin_city_id'] == origin_city_id
               and route['destination_city_id'] == destination_city_id
               and (operator_id is None or route['operator_id'] == operator_id)
        ]

        return {"success": True, "data": routes}

    def list_schedules_for_route(self, route_id: str) -> dict:
        """
        Retrieve all schedules for the specified route_id. Each schedule includes departure/arrival times and operating days.

        Args:
            route_id (str): The unique identifier for the route.

        Returns:
            dict:
                - If the route exists:
                    {
                        "success": True,
                        "data": List[ScheduleInfo]  # All schedules for the route (may be empty if none found)
                    }
                - If the route does not exist:
                    {
                        "success": False,
                        "error": "Route does not exist"
                    }
        Constraints:
            - The route_id must exist in the system.
        """
        if route_id not in self.routes:
            return { "success": False, "error": "Route does not exist" }

        schedules = [
            schedule for schedule in self.schedules.values()
            if schedule["route_id"] == route_id
        ]
        return { "success": True, "data": schedules }

    def list_trips_by_route_and_date(self, route_id: str, departure_date: str, operator_id: str = None) -> dict:
        """
        Retrieve all trips for a route and given departure date, optionally filtered by operator.

        Args:
            route_id (str): Identifier of the route to search trips for.
            departure_date (str): Departure date in ISO format (YYYY-MM-DD).
            operator_id (str, optional): Limit to trips operated by this operator. Default: None.

        Returns:
            dict:
                - success: True, data: List[TripInfo] (empty if none)
                - success: False, error: str (with error description)

        Constraints:
            - route_id must exist.
            - If operator_id provided, must be valid.
            - Only trips whose associated schedule's route matches route_id, 
              and whose departure_date matches, should be returned.
            - If operator_id provided, only return trips for routes with this operator.
        """
        # Check route exists
        if route_id not in self.routes:
            return {"success": False, "error": "Route does not exist"}

        # If operator_id provided, check it exists
        if operator_id and operator_id not in self.operators:
            return {"success": False, "error": "Operator does not exist"}

        # Find schedules for this route_id
        schedules_for_route = [
            sched_id for sched_id, sched in self.schedules.items()
            if sched["route_id"] == route_id
        ]
        if not schedules_for_route:
            # Route exists but no scheduled journeys
            return {"success": True, "data": []}

        # Trips whose schedule_id is among those, and departure_date matches
        trips_list = []
        for trip in self.trips.values():
            if trip["schedule_id"] in schedules_for_route and trip["departure_date"] == departure_date:
                # Must check operator filter if provided
                # Operator is determined by the route (all schedules for this route_id have same operator)
                if operator_id:
                    route = self.routes[route_id]
                    if route["operator_id"] != operator_id:
                        continue  # skip, operator mismatch
                trips_list.append(trip)

        return {"success": True, "data": trips_list}

    def get_trip_info(self, trip_id: str) -> dict:
        """
        Retrieve detailed info about a trip (status, bus_id, etc.).

        Args:
            trip_id (str): Unique identifier for the trip.

        Returns:
            dict: 
                {"success": True, "data": TripInfo} if found,
                else {"success": False, "error": "Trip does not exist"}.

        Constraints:
            - trip_id must exist in the system.
            - Returns all attributes for the trip.
        """
        if trip_id not in self.trips:
            return {"success": False, "error": "Trip does not exist"}
        return {"success": True, "data": self.trips[trip_id]}

    def get_bus_info(self, bus_id: str) -> dict:
        """
        Retrieve info about a bus (capacity, type, etc.) given a bus_id.

        Args:
            bus_id (str): The identifier of the bus.

        Returns:
            dict: {
                "success": True,
                "data": BusInfo  # Information about the bus (seat_capacity, bus_type, operator_id, etc.)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "Bus not found"
            }

        Constraints:
            - The bus_id must exist in the system.
        """
        bus_info = self.buses.get(bus_id)
        if not bus_info:
            return { "success": False, "error": "Bus not found" }
        return { "success": True, "data": bus_info }

    def get_seats_of_bus(self, trip_id: str) -> dict:
        """
        Return all seat definitions (seat_id, seat_number, seat_class) for the bus assigned to the given trip.

        Args:
            trip_id (str): The identifier of the trip.

        Returns:
            dict:
                success: True, data: list of seat dictionaries, e.g.,
                    [
                        {"seat_id": ..., "seat_number": ..., "seat_class": ...},
                        ...
                    ]
                OR
                success: False, error: reason string

        Constraints:
            - Fails if trip_id not found.
            - Fails if bus assigned to trip does not exist.
            - Returns empty list if bus exists but has no seats defined.
        """
        # Check trip exists
        trip_info = self.trips.get(trip_id)
        if not trip_info:
            return {"success": False, "error": "Trip not found"}

        bus_id = trip_info.get("bus_id")
        if not bus_id or bus_id not in self.buses:
            return {"success": False, "error": "Bus assigned to trip not found"}

        seats = [
            {
                "seat_id": seat_info["seat_id"],
                "seat_number": seat_info["seat_number"],
                "seat_class": seat_info["seat_class"]
            }
            for seat_info in self.seats.values()
            if seat_info["bus_id"] == bus_id
        ]

        return {
            "success": True,
            "data": seats
        }

    def list_booked_seats_for_trip(self, trip_id: str) -> dict:
        """
        Return all seat_ids for a trip that are booked (excluding cancelled bookings and cancelled seats).

        Args:
            trip_id (str): The identifier of the trip.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of booked seat_ids (may be empty)
            }
            or
            {
                "success": False,
                "error": str       # Description, e.g., trip not found
            }

        Constraints:
            - Only bookings for the given trip_id with non-cancelled status are considered.
            - Only booking seats with non-cancelled seat_status are included.
        """
        if trip_id not in self.trips:
            return { "success": False, "error": "Trip does not exist" }

        booked_seat_ids = []

        for booking in self.bookings.values():
            if booking["trip_id"] == trip_id and booking["booking_status"] != "cancelled":
                booking_id = booking["booking_id"]
                seat_infos = self.booking_seats.get(booking_id, [])
                for seat_info in seat_infos:
                    if seat_info["seat_status"] != "cancelled":
                        booked_seat_ids.append(seat_info["seat_id"])

        return { "success": True, "data": booked_seat_ids }

    def get_available_seats_for_trip(self, trip_id: str) -> dict:
        """
        Returns a list of available seat_ids for the specified trip, based on the bus capacity
        and current bookings (excluding cancelled bookings and seats).

        Args:
            trip_id (str): The trip ID for which available seats are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of available seat_ids (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - Only seats not already assigned in non-cancelled bookings are available.
            - Trip status must allow bookings (not departed or cancelled).
        """
        trip = self.trips.get(trip_id)
        if not trip:
            return {"success": False, "error": "Trip does not exist"}
    
        if trip["status"] in ["cancelled", "departed"]:
            # Booking not permitted, seats are not available
            return {"success": True, "data": []}
    
        bus_id = trip.get("bus_id")
        if not bus_id or bus_id not in self.buses:
            return {"success": False, "error": "Associated bus for trip not found"}
    
        # Find all seats for this bus
        seats_for_bus = [seat for seat in self.seats.values() if seat["bus_id"] == bus_id]
        all_seat_ids = [seat["seat_id"] for seat in seats_for_bus]
    
        # Collect booked seats for this trip (in bookings that are not cancelled)
        booked_seat_ids = set()
        for booking in self.bookings.values():
            if booking["trip_id"] != trip_id or booking["booking_status"] == "cancelled":
                continue
            for seat_info in self.booking_seats.get(booking["booking_id"], []):
                if seat_info["seat_status"] == "cancelled":
                    continue
                booked_seat_ids.add(seat_info["seat_id"])
    
        available_seat_ids = [
            seat_id for seat_id in all_seat_ids
            if seat_id not in booked_seat_ids
        ]
        return {"success": True, "data": available_seat_ids}

    def get_fare_for_trip(self, trip_id: str) -> dict:
        """
        Retrieve the fare (base_price, fare_rules) applicable to a given trip, determined by its route and the effective date.

        Args:
            trip_id (str): Unique ID of the trip.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        "fare_id": str,
                        "base_price": float,
                        "fare_rules": str
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Fare must be effective on the trip's departure_date (i.e., latest effective_date <= departure_date for the same route).
        """
        # Lookup trip
        trip = self.trips.get(trip_id)
        if not trip:
            return {"success": False, "error": "Trip not found."}

        schedule_id = trip.get("schedule_id")
        departure_date = trip.get("departure_date")
        if not schedule_id or not departure_date:
            return {"success": False, "error": "Trip missing schedule_id or departure_date."}

        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule not found for trip."}

        route_id = schedule.get("route_id")
        if not route_id:
            return {"success": False, "error": "Schedule missing route_id."}

        # Find applicable fares for this route
        fares_for_route = [
            fare for fare in self.fares.values()
            if fare.get("route_id") == route_id
        ]

        # Only consider fares with effective_date on/before departure_date
        applicable_fares = []
        for fare in fares_for_route:
            effective_date = fare.get("effective_date")
            if not effective_date:
                continue
            # Only effective on/before departure date
            if effective_date <= departure_date:
                applicable_fares.append(fare)

        if not applicable_fares:
            return {"success": False, "error": "No fare found for the route/trip date."}

        # Pick the fare with the latest (max) effective_date <= departure_date
        applicable_fares.sort(key=lambda x: x["effective_date"], reverse=True)
        chosen_fare = applicable_fares[0]

        return {
            "success": True,
            "data": {
                "fare_id": chosen_fare["fare_id"],
                "base_price": chosen_fare["base_price"],
                "fare_rules": chosen_fare["fare_rules"]
            }
        }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Query customer info for user-facing applications.

        Args:
            customer_id (str): The unique identifier of the customer to retrieve.

        Returns:
            dict:
                success: True and data (CustomerInfo) if found,
                success: False and error message otherwise.

        Constraints:
            - The customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def create_booking(self, trip_id: str, customer_id: str, seat_ids: List[str], passenger_names: List[str]) -> dict:
        """
        Reserve seat(s) and create a booking for a specific trip and customer.

        Args:
            trip_id (str): The trip to book seats on.
            customer_id (str): Customer making the booking.
            seat_ids (List[str]): List of seat IDs to reserve (must be available).
            passenger_names (List[str]): List of passenger names for each seat (must match seat_ids length).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Booking created",
                    "booking_id": str,
                    "booking_info": BookingInfo,
                    "seats": List[BookingSeatInfo]
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Booking only allowed for scheduled (not cancelled/departed) trips.
            - Seats must exist, be available, and belong to the bus for this trip.
            - No seat can be double-booked on a trip; only one active booking per seat per trip.
            - Number of passenger_names must match seat_ids.
            - Customer must exist.
            - Fare must exist for the route.
        """

        # 1. Validate trip exists and is bookable
        trip = self.trips.get(trip_id)
        if not trip:
            return {"success": False, "error": "Trip does not exist"}
        if trip["status"] not in ["scheduled"]:
            return {"success": False, "error": f"Trip status is '{trip['status']}', bookings not allowed"}

        bus_id = trip.get("bus_id")
        bus = self.buses.get(bus_id)
        if not bus:
            return {"success": False, "error": "Bus not found for trip"}
    
        # 2. Validate customer
        customer = self.customers.get(customer_id)
        if not customer:
            return {"success": False, "error": "Customer does not exist"}

        # 3. Validate input array sizes
        if not seat_ids or not passenger_names or len(seat_ids) != len(passenger_names):
            return {"success": False, "error": "seat_ids and passenger_names must be non-empty and of same length"}

        # 4. Validate seats: exist, belong to bus, and are available for this trip
        for seat_id in seat_ids:
            seat = self.seats.get(seat_id)
            if not seat:
                return {"success": False, "error": f"Seat {seat_id} does not exist"}
            if seat["bus_id"] != bus_id:
                return {"success": False, "error": f"Seat {seat_id} does not belong to bus for this trip"}

        # 5. Check seat availability
        # For this trip, iterate bookings and booking_seats, and check that none of these seats are reserved/confirmed (exclude cancelled)
        seat_booked = set()
        for booking in self.bookings.values():
            if booking["trip_id"] != trip_id or booking["booking_status"] == "cancelled":
                continue
            b_id = booking["booking_id"]
            for bs in self.booking_seats.get(b_id, []):
                if bs["seat_id"] in seat_ids and bs["seat_status"] not in ["cancelled"]:
                    seat_booked.add(bs["seat_id"])
        if seat_booked:
            return {"success": False, "error": f"Seat(s) already booked: {list(seat_booked)}"}

        # 6. Compute fare/price
        schedule = self.schedules.get(trip["schedule_id"])
        if not schedule:
            return {"success": False, "error": "Schedule not found for trip"}
        route = self.routes.get(schedule["route_id"])
        if not route:
            return {"success": False, "error": "Route not found for schedule"}

        # Find matching fare for route
        # The most recent effective date before departure_date is used (simplified for demo)
        fare_candidates = [
            fare for fare in self.fares.values()
            if fare["route_id"] == route["route_id"]
        ]
        if not fare_candidates:
            return {"success": False, "error": "No fare found for route"}
        # Sort by effective_date and take last before trip departure_date
        dep_date = dateparse(trip["departure_date"])
        fare_candidates = sorted(fare_candidates, key=lambda x: dateparse(x["effective_date"]))
        fare = None
        for f in fare_candidates:
            if dateparse(f["effective_date"]) <= dep_date:
                fare = f
        if fare is None:
            return {"success": False, "error": "No fare found for route/trip date"}
        price = fare["base_price"] * len(seat_ids)  # No fare_rules/discounts applied in demo

        # 7. Create booking record
        booking_seed = "|".join([
            trip_id,
            customer_id,
            ",".join(seat_ids),
            ",".join(passenger_names),
            str(len(self.bookings)),
        ])
        booking_id = str(uuid.uuid5(uuid.NAMESPACE_URL, booking_seed))
        departure_time = "00:00"
        if schedule.get("departure_time"):
            departure_time = schedule["departure_time"]
        try:
            departure_dt = datetime.datetime.strptime(
                f"{trip['departure_date']}T{departure_time}:00",
                "%Y-%m-%dT%H:%M:%S"
            )
            booking_time = (departure_dt - datetime.timedelta(days=1)).replace(microsecond=0).isoformat()
        except Exception:
            booking_time = f"{trip['departure_date']}T00:00:00"
        booking_info = {
            "booking_id": booking_id,
            "trip_id": trip_id,
            "customer_id": customer_id,
            "booking_status": "reserved",
            "total_price": price,
            "booking_time": booking_time
        }
        self.bookings[booking_id] = booking_info

        # 8. Create booking_seat records
        seat_records = []
        for i, seat_id in enumerate(seat_ids):
            bs = {
                "booking_id": booking_id,
                "seat_id": seat_id,
                "seat_status": "reserved",
                "passenger_name": passenger_names[i]
            }
            seat_records.append(bs)
        self.booking_seats[booking_id] = seat_records

        return {
            "success": True,
            "message": "Booking created",
            "booking_id": booking_id,
            "booking_info": booking_info,
            "seats": seat_records
        }

    def cancel_booking(self, booking_id: str) -> dict:
        """
        Cancels a booking and updates its seat allocations to 'cancelled'.

        Args:
            booking_id (str): The unique identifier for the booking to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Booking and seat allocations cancelled."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Booking must exist.
            - Only non-cancelled bookings can be cancelled.
            - All associated seat allocations for the booking are set to 'cancelled'.
        """
        if booking_id not in self.bookings:
            return {"success": False, "error": "Booking not found."}
    
        booking = self.bookings[booking_id]
        current_status = booking.get("booking_status", "").lower()
        if current_status == "cancelled":
            return {"success": False, "error": "Booking is already cancelled."}
    
        # Set booking status to cancelled
        booking["booking_status"] = "cancelled"
        self.bookings[booking_id] = booking  # (Redundant, but for clarity)
    
        # Update seat allocations to cancelled
        if booking_id in self.booking_seats:
            for seat_info in self.booking_seats[booking_id]:
                seat_info["seat_status"] = "cancelled"
    
        return {"success": True, "message": "Booking and seat allocations cancelled."}

    def update_trip_status(self, trip_id: str, new_status: str) -> dict:
        """
        Change the status of a trip (e.g., scheduled, departed, cancelled).

        Args:
            trip_id (str): The ID of the trip to be updated.
            new_status (str): The new status to set for this trip (e.g., 'scheduled', 'departed', 'cancelled').

        Returns:
            dict: 
                On success: { "success": True, "message": "Trip status updated to <new_status> for trip_id <trip_id>" }
                On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - The trip must exist in the system.
            - Status strings can be any, but it's typical to use domain values like 'scheduled', 'departed', 'cancelled', etc.

        Notes:
            - This operation only updates the trip status; logic enforcing side effects (e.g., cascade to bookings) must be handled elsewhere.
        """
        trip = self.trips.get(trip_id)
        if not trip:
            return {"success": False, "error": f"Trip with id '{trip_id}' does not exist."}
    
        # Accept any status; if a validation list is later required, add here.
        previous_status = trip["status"]
        trip["status"] = new_status

        return {
            "success": True,
            "message": f"Trip status updated to '{new_status}' for trip_id '{trip_id}'."
        }

    def add_trip(
        self,
        trip_id: str,
        schedule_id: str,
        departure_date: str,
        bus_id: str,
        status: str = "scheduled"
    ) -> dict:
        """
        Admin operation to create a new trip instance.
    
        Args:
            trip_id (str): Unique trip ID for the new trip.
            schedule_id (str): Existing schedule ID to base the trip on.
            departure_date (str): Date of departure (ISO format 'YYYY-MM-DD').
            bus_id (str): Existing bus ID to assign to this trip.
            status (str): Trip status (default is "scheduled").
    
        Returns:
            dict: {
                "success": True,
                "message": "Trip added successfully"
            } on success,
            or {
                "success": False,
                "error": "Explanation"
            } on failure.
    
        Constraints:
            - trip_id must be unique.
            - schedule_id and bus_id must already exist.
            - departure_date should be a valid date string.
        """

        if trip_id in self.trips:
            return {"success": False, "error": "Trip ID already exists"}

        if schedule_id not in self.schedules:
            return {"success": False, "error": "Schedule ID does not exist"}

        if bus_id not in self.buses:
            return {"success": False, "error": "Bus ID does not exist"}

        # (Optional simple ISO date validation)
        try:
            datetime.datetime.strptime(departure_date, "%Y-%m-%d")
        except Exception:
            return {"success": False, "error": "Invalid departure_date format, expected YYYY-MM-DD"}

        self.trips[trip_id] = {
            "trip_id": trip_id,
            "schedule_id": schedule_id,
            "departure_date": departure_date,
            "bus_id": bus_id,
            "status": status
        }

        return {"success": True, "message": "Trip added successfully"}

    def update_fare(
        self,
        fare_id: str,
        base_price: float = None,
        fare_rules: str = None,
        effective_date: str = None
    ) -> dict:
        """
        Update the fare (base price, rules, or effective date) for a given fare entry by fare_id.

        Args:
            fare_id (str): The unique identifier of the fare to update.
            base_price (float, optional): New base price to set.
            fare_rules (str, optional): New fare rules to set.
            effective_date (str, optional): New effective date (ISO date).

        Returns:
            dict:
                On success: { "success": True, "message": "Fare updated successfully" }
                On error:   { "success": False, "error": "<reason>" }

        Constraints:
            - fare_id must exist in the system.
            - Only provided (non-None) fields are updated.
        """
        if fare_id not in self.fares:
            return { "success": False, "error": "Fare not found" }

        fare = self.fares[fare_id]
        updated = False

        if base_price is not None:
            fare["base_price"] = base_price
            updated = True
        if fare_rules is not None:
            fare["fare_rules"] = fare_rules
            updated = True
        if effective_date is not None:
            fare["effective_date"] = effective_date
            updated = True

        # Field values updated in-place in self.fares
        return { "success": True, "message": "Fare updated successfully" }

    def assign_seat_to_booking(self, booking_id: str, seat_id: str, passenger_name: str) -> dict:
        """
        Assign a specific seat to a booking, checking seat and trip availability.

        Args:
            booking_id (str): The booking to assign the seat to.
            seat_id (str): The seat to be assigned.
            passenger_name (str): Name of the passenger for this seat.

        Returns:
            dict: {
                "success": True,
                "message": "Seat assigned to booking successfully"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. booking not found, seat unavailable, etc.
            }

        Constraints:
            - The booking must exist and not be cancelled.
            - The seat must exist and not already be booked for the same trip.
            - The seat must belong to the bus for the trip.
            - The trip status must allow booking (not departed or cancelled).
            - Overbooking not permitted.
        """
        # Check booking exists
        if booking_id not in self.bookings:
            return { "success": False, "error": "Booking not found" }
        booking_info = self.bookings[booking_id]
        trip_id = booking_info.get("trip_id")

        # Check trip exists and status
        if trip_id not in self.trips:
            return { "success": False, "error": "Associated trip not found" }
        trip_info = self.trips[trip_id]
        trip_status = trip_info.get("status", "").lower()
        if trip_status in ["cancelled", "departed"]:
            return { "success": False, "error": f"Trip status '{trip_status}' does not allow seat assignment" }

        # Check booking status
        booking_status = booking_info.get("booking_status", "").lower()
        if booking_status == "cancelled":
            return { "success": False, "error": "Booking is cancelled; cannot assign seat" }

        # Check seat exists
        if seat_id not in self.seats:
            return { "success": False, "error": "Seat not found" }
        seat_info = self.seats[seat_id]
        bus_id_of_seat = seat_info.get("bus_id")
        bus_id_of_trip = trip_info.get("bus_id")
        # Check seat belongs to bus for this trip
        if bus_id_of_seat != bus_id_of_trip:
            return { "success": False, "error": "Seat does not belong to bus for this trip" }

        # Check seat availability for this trip (not booked by any booking with status not cancelled)
        for b_id, b_info in self.bookings.items():
            if b_info.get("trip_id") == trip_id and b_info.get("booking_status", "").lower() != "cancelled":
                for bs in self.booking_seats.get(b_id, []):
                    if bs["seat_id"] == seat_id and bs["seat_status"].lower() != "cancelled":
                        return { "success": False, "error": "Seat is already assigned/booked for this trip" }

        # Assign seat to booking
        # Add to self.booking_seats
        seat_assignment = {
            "booking_id": booking_id,
            "seat_id": seat_id,
            "seat_status": "reserved",  # or "confirmed" depending on status, here default to reserved
            "passenger_name": passenger_name
        }
        if booking_id not in self.booking_seats:
            self.booking_seats[booking_id] = []
        self.booking_seats[booking_id].append(seat_assignment)

        return { "success": True, "message": "Seat assigned to booking successfully" }


class IntercityBusBookingSystem(BaseEnv):
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

    def get_city_by_name(self, **kwargs):
        return self._call_inner_tool('get_city_by_name', kwargs)

    def get_operator_by_name(self, **kwargs):
        return self._call_inner_tool('get_operator_by_name', kwargs)

    def list_routes_by_origin_and_destination(self, **kwargs):
        return self._call_inner_tool('list_routes_by_origin_and_destination', kwargs)

    def list_schedules_for_route(self, **kwargs):
        return self._call_inner_tool('list_schedules_for_route', kwargs)

    def list_trips_by_route_and_date(self, **kwargs):
        return self._call_inner_tool('list_trips_by_route_and_date', kwargs)

    def get_trip_info(self, **kwargs):
        return self._call_inner_tool('get_trip_info', kwargs)

    def get_bus_info(self, **kwargs):
        return self._call_inner_tool('get_bus_info', kwargs)

    def get_seats_of_bus(self, **kwargs):
        return self._call_inner_tool('get_seats_of_bus', kwargs)

    def list_booked_seats_for_trip(self, **kwargs):
        return self._call_inner_tool('list_booked_seats_for_trip', kwargs)

    def get_available_seats_for_trip(self, **kwargs):
        return self._call_inner_tool('get_available_seats_for_trip', kwargs)

    def get_fare_for_trip(self, **kwargs):
        return self._call_inner_tool('get_fare_for_trip', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def create_booking(self, **kwargs):
        return self._call_inner_tool('create_booking', kwargs)

    def cancel_booking(self, **kwargs):
        return self._call_inner_tool('cancel_booking', kwargs)

    def update_trip_status(self, **kwargs):
        return self._call_inner_tool('update_trip_status', kwargs)

    def add_trip(self, **kwargs):
        return self._call_inner_tool('add_trip', kwargs)

    def update_fare(self, **kwargs):
        return self._call_inner_tool('update_fare', kwargs)

    def assign_seat_to_booking(self, **kwargs):
        return self._call_inner_tool('assign_seat_to_booking', kwargs)
