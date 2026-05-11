# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from statistics import mean, median
import statistics



# Maps to entity: LiquidationEvent (attributes: event_id, coin, exchange, side, quantity, size, price, time)
class LiquidationEventInfo(TypedDict):
    event_id: str
    coin: str
    exchange: str
    side: str  # Allowed values: "long", "short", "buy", "sell" (see constraints)
    quantity: float
    size: float
    price: float
    time: float  # Unix timestamp for precise ordering

# Maps to entity: Exchange (attributes: exchange_id, name, status)
class ExchangeInfo(TypedDict):
    exchange_id: str
    name: str
    status: str

# Maps to entity: Coin (attributes: coin_symbol, coin_name, asset_type)
class CoinInfo(TypedDict):
    coin_symbol: str
    coin_name: str
    asset_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Liquidation events: {event_id: LiquidationEventInfo}
        self.liquidation_events: Dict[str, LiquidationEventInfo] = {}

        # Exchanges: {exchange_id: ExchangeInfo}
        self.exchanges: Dict[str, ExchangeInfo] = {}

        # Coins/assets: {coin_symbol: CoinInfo}
        self.coins: Dict[str, CoinInfo] = {}

        # Constraints:
        # - Each LiquidationEvent is tied to one Coin and one Exchange.
        # - LiquidationEvent 'time' must be recorded and is used for ordering/latest logic.
        # - 'side' for events must be one of: "long", "short", "buy", "sell".
        # - All statistical reporting must use currently stored liquidation event data, possibly filtered by coin or exchange.

    def list_all_coins(self) -> dict:
        """
        Retrieve the list of all tradeable coins/assets being monitored.

        Returns:
            dict: {
                "success": True,
                "data": List[CoinInfo]  # list of CoinInfo dictionaries (may be empty if none tracked)
            }
        Constraints:
            - No constraints; all coins in self.coins are considered.
            - Always succeeds, even if no coins present.
        """
        return {
            "success": True,
            "data": list(self.coins.values())
        }

    def list_all_exchanges(self) -> dict:
        """
        Retrieve all exchanges currently tracked in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ExchangeInfo],  # List of all exchange info dicts (may be empty)
            }

        Constraints:
            - No parameters required.
            - Always succeeds, returns all exchanges tracked.
        """
        all_exchanges = list(self.exchanges.values())
        return { "success": True, "data": all_exchanges }

    def get_exchange_by_name(self, name: str) -> dict:
        """
        Retrieve the exchange_id and full information for the exchange with the given human-readable name.

        Args:
            name (str): The human-readable name of the exchange (e.g., "Binance").

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": {
                          "exchange_id": str,
                          "exchange_info": ExchangeInfo
                      }
                  }
                - On failure: {
                      "success": False,
                      "error": "Exchange not found"
                  }

        Constraints:
            - Exchange name comparison is case-sensitive.
            - If multiple exchanges have the same name (unexpected), the first found is returned.
        """
        for exchange_id, exchange_info in self.exchanges.items():
            if exchange_info["name"] == name:
                return {
                    "success": True,
                    "data": {
                        "exchange_id": exchange_id,
                        "exchange_info": exchange_info
                    }
                }
        return {
            "success": False,
            "error": "Exchange not found"
        }

    def get_coin_info(self, coin_symbol: str) -> dict:
        """
        Retrieve metadata for a coin given its symbol.

        Args:
            coin_symbol (str): The coin's symbol (e.g., "BTC", "ETH").

        Returns:
            dict: {
                "success": True,
                "data": CoinInfo  # Metadata for the coin
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., coin not found)
            }

        Constraints:
            - The coin symbol must exist in the module.
        """
        coin = self.coins.get(coin_symbol)
        if coin is None:
            return { "success": False, "error": "Coin not found" }
        return { "success": True, "data": coin }

    def list_all_liquidation_events(self) -> dict:
        """
        Retrieve all liquidation events currently stored in the monitoring module.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[LiquidationEventInfo]  # (may be empty if no events)
            }
        """
        all_events = list(self.liquidation_events.values())
        return {
            "success": True,
            "data": all_events
        }

    def list_liquidation_events_by_coin(self, coin_symbol: str) -> dict:
        """
        Retrieve all liquidation events for a specified coin.

        Args:
            coin_symbol (str): Symbol of the coin to filter events by (e.g., "BTC").

        Returns:
            dict: {
                "success": True,
                "data": List[LiquidationEventInfo],  # All event records for this coin (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason, e.g. "Coin not found"
            }

        Constraints:
            - Only returns events for coins present in self.coins.
        """
        if coin_symbol not in self.coins:
            return { "success": False, "error": "Coin not found" }

        matched_events = [
            event for event in self.liquidation_events.values()
            if event["coin"] == coin_symbol
        ]
        return { "success": True, "data": matched_events }

    def list_liquidation_events_by_exchange(self, exchange_id: str) -> dict:
        """
        Retrieve all liquidation events for the specified exchange.

        Args:
            exchange_id (str): The unique identifier of the exchange.

        Returns:
            dict: {
                "success": True,
                "data": List[LiquidationEventInfo],  # All events for the exchange (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If the exchange does not exist
            }

        Constraints:
            - The exchange must exist in the system.
        """
        if exchange_id not in self.exchanges:
            return { "success": False, "error": "Exchange does not exist." }

        exchange_name = self.exchanges[exchange_id]["name"]
        result = [
            event for event in self.liquidation_events.values()
            if event["exchange"] == exchange_id or event["exchange"] == exchange_name
        ]
        return { "success": True, "data": result }

    def list_liquidation_events_by_side(self, side: str) -> dict:
        """
        Retrieve all liquidation events filtered by side/direction.

        Args:
            side (str): The direction to filter events by. Allowed values: "long", "short", "buy", "sell".

        Returns:
            dict: 
                - On success: { "success": True, "data": [LiquidationEventInfo, ...] }
                - On failure: { "success": False, "error": str }
        Constraints:
            - 'side' value must be one of the allowed values ("long", "short", "buy", "sell").
        """
        ALLOWED_SIDES = {"long", "short", "buy", "sell"}
        if side not in ALLOWED_SIDES:
            return { "success": False, "error": "Invalid side: must be one of 'long', 'short', 'buy', 'sell'." }

        results = [
            event for event in self.liquidation_events.values()
            if event["side"] == side
        ]
        return { "success": True, "data": results }

    def get_latest_liquidation_event_for_exchange(self, exchange_name: str) -> dict:
        """
        Retrieve the most recent liquidation event for a specified exchange.

        Args:
            exchange_name (str): The name of the exchange to search for.

        Returns:
            dict: {
                "success": True,
                "data": LiquidationEventInfo | None  # Most recent event info or None if no events
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., exchange not found
            }

        Constraints:
            - The exchange must exist in the system.
            - If there are no liquidation events for the exchange, return data=None.
        """
        # Find exchange_id(s) matching the given exchange name
        matched_exchange_ids = [
            eid for eid, einfo in self.exchanges.items()
            if einfo["name"] == exchange_name
        ]
        if not matched_exchange_ids:
            return { "success": False, "error": "Exchange not found" }

        # Now, aggregate all events with exchange matching the given name
        events = [
            event for event in self.liquidation_events.values()
            if event["exchange"] == exchange_name
        ]
        if not events:
            return { "success": True, "data": None }

        # Find the one with the highest 'time'
        latest_event = max(events, key=lambda e: e["time"])

        return {
            "success": True,
            "data": latest_event
        }

    def get_latest_liquidation_event_for_coin(self, coin_symbol: str) -> dict:
        """
        Retrieve the most recent liquidation event for the specified coin.

        Args:
            coin_symbol (str): The symbol of the coin (e.g., "BTC", "ETH").

        Returns:
            dict: 
                Success case:
                    {
                        "success": True,
                        "data": LiquidationEventInfo  # The latest liquidation event for the given coin
                    }
                Failure cases:
                    {
                        "success": False,
                        "error": str  # "Coin not found" or "No liquidation events for coin"
                    }

        Constraints:
            - The coin must exist in the module.
            - The result is the liquidation event for this coin with the greatest 'time' value.
        """
        if coin_symbol not in self.coins:
            return { "success": False, "error": "Coin not found" }

        # Filter events by coin
        filtered_events = [
            event for event in self.liquidation_events.values()
            if event["coin"] == coin_symbol
        ]

        if not filtered_events:
            return { "success": False, "error": "No liquidation events for coin" }

        # Find event with the largest 'time'
        latest_event = max(filtered_events, key=lambda e: e["time"])

        return {
            "success": True,
            "data": latest_event
        }

    def summarize_liquidation_statistics_by_coin(self) -> dict:
        """
        For all coins, provide total liquidation value, total amount, mean value, and median value.

        Returns:
            dict: {
                "success": True,
                "data": List[Dict[str, <...>]], # Per-coin statistics:
                    [
                        {
                            'coin_symbol': str,
                            'coin_name': str,
                            'total_value': float,
                            'total_amount': float,
                            'mean_value': float,
                            'median_value': float,
                        },
                        ...
                    ]
            }
        Constraints:
            - All statistics are computed over current liquidation events grouped by coin.
            - Coins with no liquidation events will have zero in all fields.
        """

        stats_result = []

        for coin_symbol, coin_info in self.coins.items():
            # Gather all event sizes/quantities for this coin
            event_sizes = []
            event_quantities = []
            for event in self.liquidation_events.values():
                if event["coin"] == coin_symbol:
                    event_sizes.append(event["size"])
                    event_quantities.append(event["quantity"])
            total_value = sum(event_sizes) if event_sizes else 0.0
            total_amount = sum(event_quantities) if event_quantities else 0.0
            mean_value = mean(event_sizes) if event_sizes else 0.0
            # For median, statistics.median([]) raises an error - guard for empty
            if event_sizes:
                median_value = median(event_sizes)
            else:
                median_value = 0.0
            stats_result.append({
                "coin_symbol": coin_symbol,
                "coin_name": coin_info["coin_name"],
                "total_value": total_value,
                "total_amount": total_amount,
                "mean_value": mean_value,
                "median_value": median_value
            })

        return {"success": True, "data": stats_result}

    def summarize_liquidation_statistics_by_exchange(self) -> dict:
        """
        For each exchange, provide statistics (total, mean, median) of liquidation event size and quantity.
        Returns:
            dict: {
                "success": True,
                "data": {
                    exchange_id: {
                        "exchange_name": str,
                        "count": int,
                        "total_size": float,
                        "mean_size": float or None,
                        "median_size": float or None,
                        "total_quantity": float,
                        "mean_quantity": float or None,
                        "median_quantity": float or None
                    },
                    ...
                }
            }
            or
            {"success": False, "error": str}
        Constraints:
            - Aggregates only for exchanges present in liquidation events and existing in exchanges list.
            - For exchanges with no liquidation events, fields will use 0 or None as appropriate.
        """

        exchange_name_to_id = {
            exchange_info["name"]: exchange_id
            for exchange_id, exchange_info in self.exchanges.items()
        }

        # Build mapping from exchange_id to list of liquidation events
        exchange_events = {}
        for event in self.liquidation_events.values():
            exchange_ref = event["exchange"]
            exch_id = exchange_ref if exchange_ref in self.exchanges else exchange_name_to_id.get(exchange_ref)
            if exch_id is None:
                continue  # skip events for unknown exchanges (defensively)
            if exch_id not in exchange_events:
                exchange_events[exch_id] = []
            exchange_events[exch_id].append(event)

        result = {}
        for exch_id, exch_info in self.exchanges.items():
            events = exchange_events.get(exch_id, [])
            sizes = [e["size"] for e in events]
            quantities = [e["quantity"] for e in events]
            stats = {
                "exchange_name": exch_info["name"],
                "count": len(events),
                "total_size": sum(sizes) if sizes else 0.0,
                "mean_size": statistics.mean(sizes) if sizes else None,
                "median_size": statistics.median(sizes) if sizes else None,
                "total_quantity": sum(quantities) if quantities else 0.0,
                "mean_quantity": statistics.mean(quantities) if quantities else None,
                "median_quantity": statistics.median(quantities) if quantities else None,
            }
            result[exch_id] = stats

        return {"success": True, "data": result}

    def get_liquidation_event_details(self, event_id: str) -> dict:
        """
        Retrieve full details for a specific liquidation event by event_id.

        Args:
            event_id (str): The unique identifier for the liquidation event.

        Returns:
            dict: 
                - If found: { "success": True, "data": LiquidationEventInfo }
                - If not found: { "success": False, "error": "Liquidation event not found" }

        Constraints:
            - The event_id must exist in the stored liquidation events.
        """
        if not event_id or event_id not in self.liquidation_events:
            return {"success": False, "error": "Liquidation event not found"}

        return {
            "success": True,
            "data": self.liquidation_events[event_id]
        }

    def add_liquidation_event(
        self,
        event_id: str,
        coin: str,
        exchange: str,
        side: str,
        quantity: float,
        size: float,
        price: float,
        time: float
    ) -> dict:
        """
        Adds a new liquidation event to the platform.

        Args:
            event_id (str): Unique identifier for the event.
            coin (str): Coin symbol (must exist in tracked coins).
            exchange (str): Exchange name (must exist in tracked exchanges).
            side (str): Direction ("long", "short", "buy", "sell").
            quantity (float): Quantity involved.
            size (float): Size/value of the liquidation.
            price (float): Price at liquidation.
            time (float): Unix timestamp when the event occurred.

        Returns:
            dict: { "success": True, "message": ... } on success,
                  { "success": False, "error": ... } on error.

        Constraints:
            - event_id must be unique.
            - coin must refer to an existing coin (by symbol).
            - exchange must refer to an existing exchange (by name).
            - side must be one of: "long", "short", "buy", "sell".
        """
        # Unique event_id
        if event_id in self.liquidation_events:
            return { "success": False, "error": "Event ID already exists" }

        # Coin existence
        if coin not in self.coins:
            return { "success": False, "error": "Referenced coin does not exist" }

        # Exchange existence (lookup by name)
        exchange_obj = None
        for ex in self.exchanges.values():
            if ex["name"] == exchange:
                exchange_obj = ex
                break
        if not exchange_obj:
            return { "success": False, "error": "Referenced exchange does not exist" }

        # Side validity
        allowed_sides = {"long", "short", "buy", "sell"}
        if side not in allowed_sides:
            return { "success": False, "error": "Invalid side value" }

        # Basic type checking (not raising, just checking)
        try:
            quantity = float(quantity)
            size = float(size)
            price = float(price)
            time = float(time)
        except Exception:
            return { "success": False, "error": "quantity, size, price, and time must be numbers" }

        event = {
            "event_id": event_id,
            "coin": coin,
            "exchange": exchange,
            "side": side,
            "quantity": quantity,
            "size": size,
            "price": price,
            "time": time,
        }
        self.liquidation_events[event_id] = event
        return { "success": True, "message": f"Liquidation event {event_id} added successfully" }

    def update_liquidation_event(self, event_id: str, updates: dict) -> dict:
        """
        Modify the data for an existing liquidation event.

        Args:
            event_id (str): The unique identifier of the liquidation event to update.
            updates (dict): Dictionary of fields (as keys) to update with their new values.
                            Allowed fields: coin, exchange, side, quantity, size, price, time.

        Returns:
            dict:
                On success: { "success": True, "message": "Liquidation event updated" }
                On failure: { "success": False, "error": <description> }

        Constraints:
            - event_id must exist in self.liquidation_events
            - Only allowed fields can be updated; event_id cannot be changed
            - When updating coin, value must exist in self.coins
            - When updating exchange, value must exist in self.exchanges (by name)
            - When updating side, the value must be in {"long", "short", "buy", "sell"}
            - When updating quantity, size, price, value must be valid float
            - When updating time, value must be valid float (unix timestamp)
        """

        allowed_fields = {"coin", "exchange", "side", "quantity", "size", "price", "time"}
        allowed_sides = {"long", "short", "buy", "sell"}

        if event_id not in self.liquidation_events:
            return { "success": False, "error": "Liquidation event not found" }

        event = self.liquidation_events[event_id]

        # Validate updates
        for key, value in updates.items():
            if key == "event_id":
                return { "success": False, "error": "event_id cannot be changed" }
            if key not in allowed_fields:
                return { "success": False, "error": f"Field '{key}' cannot be updated" }

            # Field-specific validation
            if key == "coin":
                if not isinstance(value, str) or value not in self.coins:
                    return { "success": False, "error": "Invalid coin symbol: must exist in coins list" }

            elif key == "exchange":
                if not isinstance(value, str):
                    return { "success": False, "error": "Exchange value must be a string" }
                if not any(einfo["name"] == value for einfo in self.exchanges.values()):
                    return { "success": False, "error": "Invalid exchange: must exist in exchanges list by name" }

            elif key == "side":
                if value not in allowed_sides:
                    return { "success": False, "error": "Invalid side; must be one of long, short, buy, sell" }

            elif key in {"quantity", "size", "price", "time"}:
                try:
                    valfloat = float(value)
                except Exception:
                    return { "success": False, "error": f"{key} must be a number" }
                if key in {"quantity", "size", "price"} and valfloat < 0:
                    return { "success": False, "error": f"{key} must not be negative" }

        # Apply validated updates
        for key, value in updates.items():
            event[key] = value

        self.liquidation_events[event_id] = event
        return { "success": True, "message": "Liquidation event updated" }

    def delete_liquidation_event(self, event_id: str) -> dict:
        """
        Remove a liquidation event from the system.

        Args:
            event_id (str): The unique identifier of the liquidation event to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Liquidation event <event_id> deleted."
                    }
                On failure (nonexistent event):
                    {
                        "success": False,
                        "error": "Liquidation event <event_id> does not exist."
                    }

        Constraints:
            - The event_id must exist in the system.
            - All statistics and queries immediately reflect this deletion.
        """
        if event_id not in self.liquidation_events:
            return {
                "success": False,
                "error": f"Liquidation event {event_id} does not exist."
            }

        del self.liquidation_events[event_id]
        return {
            "success": True,
            "message": f"Liquidation event {event_id} deleted."
        }

    def add_exchange(self, exchange_id: str, name: str, status: str) -> dict:
        """
        Register a new exchange to be monitored.

        Args:
            exchange_id (str): Unique identifier for the exchange.
            name (str): Name of the exchange (e.g., "Binance").
            status (str): Current status of exchange (e.g., "active", "inactive").

        Returns:
            dict: On success:
                      { "success": True, "message": "Exchange <name> (<exchange_id>) added successfully." }
                  On error:
                      { "success": False, "error": "<error message>" }

        Constraints:
            - The exchange_id must be unique (not already present).
            - exchange_id and name must be non-empty strings.
        """
        if not exchange_id or not isinstance(exchange_id, str):
            return { "success": False, "error": "exchange_id must be a non-empty string." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "name must be a non-empty string." }

        if exchange_id in self.exchanges:
            return { "success": False, "error": f"Exchange ID '{exchange_id}' already exists." }

        # Construct the ExchangeInfo dict
        new_exchange = {
            "exchange_id": exchange_id,
            "name": name,
            "status": status if status else "unknown"
        }
        self.exchanges[exchange_id] = new_exchange

        return {
            "success": True,
            "message": f"Exchange {name} ({exchange_id}) added successfully."
        }

    def update_exchange_status(self, exchange_id: str, status: str) -> dict:
        """
        Update the status (e.g., active/inactive) of an exchange.

        Args:
            exchange_id (str): The unique identifier of the exchange to update.
            status (str): The new status to set for the exchange.

        Returns:
            dict: 
                - If successful: { "success": True, "message": "Exchange status updated." }
                - If exchange_id does not exist: { "success": False, "error": "Exchange does not exist." }

        Constraints:
            - The exchange_id must refer to an existing exchange.
            - No restriction on status values is specified; sets to given value verbatim.
        """
        if exchange_id not in self.exchanges:
            return { "success": False, "error": "Exchange does not exist." }

        self.exchanges[exchange_id]['status'] = status
        return { "success": True, "message": "Exchange status updated." }

    def add_coin(self, coin_symbol: str, coin_name: str, asset_type: str) -> dict:
        """
        Add a new coin/asset to the monitored coin list.

        Args:
            coin_symbol (str): The unique short symbol for the coin (e.g., "BTC").
            coin_name (str): The full name of the coin (e.g., "Bitcoin").
            asset_type (str): The type of asset (e.g., "crypto").

        Returns:
            dict: 
                - If success: { "success": True, "message": "Coin <coin_symbol> added." }
                - If failure: { "success": False, "error": <reason> }

        Constraints:
            - coin_symbol must be unique (cannot already exist in self.coins)
            - None of the fields can be empty
        """
        # Basic validation
        if not coin_symbol or not coin_name or not asset_type:
            return { "success": False, "error": "coin_symbol, coin_name, and asset_type must all be provided and non-empty." }

        if coin_symbol in self.coins:
            return { "success": False, "error": f"Coin with symbol '{coin_symbol}' already exists." }
    
        # Insert new coin
        self.coins[coin_symbol] = {
            "coin_symbol": coin_symbol,
            "coin_name": coin_name,
            "asset_type": asset_type
        }
        return { "success": True, "message": f"Coin '{coin_symbol}' added." }

    def update_coin_info(self, coin_symbol: str, coin_name: str = None, asset_type: str = None) -> dict:
        """
        Update the information of a tracked coin/asset.

        Args:
            coin_symbol (str): The symbol of the coin/asset to update.
            coin_name (Optional[str]): The new display name (if updating).
            asset_type (Optional[str]): The new asset type (if updating).

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Coin info for <coin_symbol> updated."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - coin_symbol must exist in the coins database.
            - At least one of coin_name or asset_type must be provided for update.
            - Only coin_name and asset_type fields are updatable.
        """
        if coin_symbol not in self.coins:
            return { "success": False, "error": "Coin not found." }

        if coin_name is None and asset_type is None:
            return { "success": False, "error": "No update fields specified." }

        coin = self.coins[coin_symbol]
        updated = False

        if coin_name is not None:
            coin['coin_name'] = coin_name
            updated = True

        if asset_type is not None:
            coin['asset_type'] = asset_type
            updated = True

        # No need to reassign in self.coins as dict is mutable

        if updated:
            return { "success": True, "message": f"Coin info for {coin_symbol} updated." }
        else:
            return { "success": False, "error": "No valid update performed." }


class LiquidationMonitoringModule(BaseEnv):
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

    def list_all_coins(self, **kwargs):
        return self._call_inner_tool('list_all_coins', kwargs)

    def list_all_exchanges(self, **kwargs):
        return self._call_inner_tool('list_all_exchanges', kwargs)

    def get_exchange_by_name(self, **kwargs):
        return self._call_inner_tool('get_exchange_by_name', kwargs)

    def get_coin_info(self, **kwargs):
        return self._call_inner_tool('get_coin_info', kwargs)

    def list_all_liquidation_events(self, **kwargs):
        return self._call_inner_tool('list_all_liquidation_events', kwargs)

    def list_liquidation_events_by_coin(self, **kwargs):
        return self._call_inner_tool('list_liquidation_events_by_coin', kwargs)

    def list_liquidation_events_by_exchange(self, **kwargs):
        return self._call_inner_tool('list_liquidation_events_by_exchange', kwargs)

    def list_liquidation_events_by_side(self, **kwargs):
        return self._call_inner_tool('list_liquidation_events_by_side', kwargs)

    def get_latest_liquidation_event_for_exchange(self, **kwargs):
        return self._call_inner_tool('get_latest_liquidation_event_for_exchange', kwargs)

    def get_latest_liquidation_event_for_coin(self, **kwargs):
        return self._call_inner_tool('get_latest_liquidation_event_for_coin', kwargs)

    def summarize_liquidation_statistics_by_coin(self, **kwargs):
        return self._call_inner_tool('summarize_liquidation_statistics_by_coin', kwargs)

    def summarize_liquidation_statistics_by_exchange(self, **kwargs):
        return self._call_inner_tool('summarize_liquidation_statistics_by_exchange', kwargs)

    def get_liquidation_event_details(self, **kwargs):
        return self._call_inner_tool('get_liquidation_event_details', kwargs)

    def add_liquidation_event(self, **kwargs):
        return self._call_inner_tool('add_liquidation_event', kwargs)

    def update_liquidation_event(self, **kwargs):
        return self._call_inner_tool('update_liquidation_event', kwargs)

    def delete_liquidation_event(self, **kwargs):
        return self._call_inner_tool('delete_liquidation_event', kwargs)

    def add_exchange(self, **kwargs):
        return self._call_inner_tool('add_exchange', kwargs)

    def update_exchange_status(self, **kwargs):
        return self._call_inner_tool('update_exchange_status', kwargs)

    def add_coin(self, **kwargs):
        return self._call_inner_tool('add_coin', kwargs)

    def update_coin_info(self, **kwargs):
        return self._call_inner_tool('update_coin_info', kwargs)
