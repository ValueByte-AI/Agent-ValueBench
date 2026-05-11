# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class AssetInfo(TypedDict):
    ticker_symbol: str
    asset_type: str
    name: str
    exchange: str

class PriceRecordInfo(TypedDict):
    ticker_symbol: str
    timestamp: float   # Unix timestamp or other numeric representation
    open: float
    high: float
    low: float
    close: float
    volume: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Assets: {ticker_symbol: AssetInfo}
        # Maps each ticker symbol to its asset metadata.
        self.assets: Dict[str, AssetInfo] = {}

        # PriceRecords: {ticker_symbol: List[PriceRecordInfo]}
        # Maps each ticker to its time-series price and volume records.
        self.price_records: Dict[str, List[PriceRecordInfo]] = {}

        # Constraints:
        # - Each PriceRecord must reference an existing Asset via ticker_symbol.
        # - PriceRecord timestamps must be sequential and non-overlapping for a given ticker_symbol and time interval.
        # - Asset information (ticker_symbol, asset_type, name, exchange) must remain consistent over time for accurate historical referencing.

    def get_asset_info(self, ticker_symbol: str) -> dict:
        """
        Fetch asset metadata (asset_type, name, exchange) for a given ticker_symbol.

        Args:
            ticker_symbol (str): The asset's unique ticker symbol.

        Returns:
            dict:
                - On success: { "success": True, "data": AssetInfo }
                - On failure: { "success": False, "error": "Asset not found" }

        Constraints:
            - The ticker_symbol must exist in the system's registry of assets.
        """
        asset_info = self.assets.get(ticker_symbol)
        if not asset_info:
            return { "success": False, "error": "Asset not found" }
        return { "success": True, "data": asset_info }

    def list_all_assets(self) -> dict:
        """
        List all assets (tickers) being tracked in the system with their metadata.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of all assets' info, possibly empty
            }
        Constraints:
            - None. This operation reads all asset entries currently tracked.
        """
        result = list(self.assets.values())
        return { "success": True, "data": result }

    def get_price_history(self, ticker_symbol: str, start_time: float, end_time: float) -> dict:
        """
        Retrieve historical price and volume records for the given ticker within a specified time interval.

        Args:
            ticker_symbol (str): The ticker symbol of the asset.
            start_time (float): Start of the time interval (inclusive).
            end_time (float): End of the time interval (inclusive).

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[PriceRecordInfo]}
                On failure:
                    {"success": False, "error": str}

        Constraints:
          - Asset must exist.
          - start_time must be less than or equal to end_time.
          - Records must reference existing asset (enforced by lookup).
        """
        # Validate ticker_symbol exists as per constraint
        if ticker_symbol not in self.assets:
            return { "success": False, "error": "Asset does not exist" }
        # Validate time interval
        if start_time > end_time:
            return { "success": False, "error": "Invalid time interval" }
        # Retrieve records (empty list if ticker has no price records)
        records = self.price_records.get(ticker_symbol, [])
        filtered = [
            rec for rec in records
            if start_time <= rec["timestamp"] <= end_time
        ]
        return { "success": True, "data": filtered }

    def get_available_time_range(self, ticker_symbol: str) -> dict:
        """
        Obtain the available time span (earliest/latest timestamps) for a ticker’s data.

        Args:
            ticker_symbol (str): The ticker symbol of the asset to query.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "earliest": float,
                    "latest": float
                }
            } if records exist,
            {
                "success": True,
                "data": None
            } if the ticker has no price records,
            {
                "success": False,
                "error": str
            } if the ticker symbol does not exist.

        Constraints:
            - Ticker symbol must refer to an existing asset.
            - Will return None for data if the asset has no price records.
        """
        if ticker_symbol not in self.assets:
            return { "success": False, "error": "Ticker symbol does not exist" }

        records = self.price_records.get(ticker_symbol, [])
        if not records:
            return { "success": True, "data": None }

        timestamps = [record["timestamp"] for record in records]
        return {
            "success": True,
            "data": {
                "earliest": min(timestamps),
                "latest": max(timestamps)
            }
        }

    def list_price_records_for_tickers(
        self, 
        ticker_symbols: list, 
        start_time: float, 
        end_time: float
    ) -> dict:
        """
        Retrieve price records for a list of tickers over a specified [start_time, end_time] interval.

        Args:
            ticker_symbols (List[str]): List of ticker symbols for which to retrieve records.
            start_time (float): Start (inclusive) of the time interval (unix timestamp).
            end_time (float): End (inclusive) of the time interval (unix timestamp).

        Returns:
            dict: {
                "success": True,
                "data": {
                    <ticker>: List[PriceRecordInfo],  # filtered list for each ticker
                    ...
                }
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. tickers not found
            }

        Constraints:
            - All ticker_symbols must correspond to existing assets.
            - Results for each ticker will be empty if no records are found in interval.
        """
        if not isinstance(ticker_symbols, list) or not all(isinstance(t, str) for t in ticker_symbols):
            return {"success": False, "error": "ticker_symbols must be a list of strings"}
        if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
            return {"success": False, "error": "start_time and end_time must be numeric (float or int)"}
        if start_time > end_time:
            return {"success": False, "error": "start_time must be less than or equal to end_time"}

        # Validate provided ticker_symbols exist
        missing_tickers = [t for t in ticker_symbols if t not in self.assets]
        if missing_tickers:
            return {"success": False, "error": f"One or more ticker symbols not found: {missing_tickers}"}
    
        # Collect results per ticker
        output = {}
        for t in ticker_symbols:
            records = self.price_records.get(t, [])
            filtered = [
                rec for rec in records 
                if start_time <= rec["timestamp"] <= end_time
            ]
            output[t] = filtered

        return {"success": True, "data": output}

    def get_latest_price(self, ticker_symbol: str) -> dict:
        """
        Fetch the most recent price record for a specified ticker.

        Args:
            ticker_symbol (str): The symbol of the asset to fetch the latest price for.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": PriceRecordInfo  # The latest price record
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - Ticker symbol must exist in the assets dictionary.
            - Must have at least one price record for the ticker.
        """
        if ticker_symbol not in self.assets:
            return { "success": False, "error": "Ticker does not exist" }

        records = self.price_records.get(ticker_symbol, [])
        if not records:
            return { "success": False, "error": "No price records found for this ticker" }

        latest_record = max(records, key=lambda rec: rec["timestamp"])
        return { "success": True, "data": latest_record }

    def get_aggregated_statistics(
        self,
        ticker_symbol: str,
        start_time: float,
        end_time: float
    ) -> dict:
        """
        Compute aggregate statistics (average open, minimum low, maximum high,
        average close, total volume, count) for a ticker over a specified time window.

        Args:
            ticker_symbol (str): Asset ticker symbol to query.
            start_time (float): Start timestamp (inclusive).
            end_time (float): End timestamp (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": {
                    "average_open": float,
                    "min_low": float,
                    "max_high": float,
                    "average_close": float,
                    "total_volume": float,
                    "record_count": int
                }
            }
            OR
            { "success": False, "error": str }

        Notes/Constraints:
            - Returns empty aggregates (0/None) if no price records in window.
            - start_time must be <= end_time.
            - ticker_symbol must be valid.
        """
        # Validate ticker symbol
        if ticker_symbol not in self.assets:
            return {"success": False, "error": "Ticker symbol does not exist"}

        # Validate time window
        if start_time > end_time:
            return {"success": False, "error": "start_time must be <= end_time"}

        records = self.price_records.get(ticker_symbol, [])
        # Filter records in the time window (inclusive)
        filtered = [
            r for r in records
            if start_time <= r["timestamp"] <= end_time
        ]

        if not filtered:
            # Return empty aggregates for valid symbol and time window with no data
            return {
                "success": True,
                "data": {
                    "average_open": None,
                    "min_low": None,
                    "max_high": None,
                    "average_close": None,
                    "total_volume": 0.0,
                    "record_count": 0
                }
            }

        total_open = sum(r["open"] for r in filtered)
        total_close = sum(r["close"] for r in filtered)
        total_volume = sum(r["volume"] for r in filtered)
        min_low = min(r["low"] for r in filtered)
        max_high = max(r["high"] for r in filtered)
        count = len(filtered)

        return {
            "success": True,
            "data": {
                "average_open": total_open / count,
                "min_low": min_low,
                "max_high": max_high,
                "average_close": total_close / count,
                "total_volume": total_volume,
                "record_count": count
            }
        }

    def validate_ticker_symbol(self, ticker_symbol: str) -> dict:
        """
        Check whether a ticker symbol exists as an Asset in the system.

        Args:
            ticker_symbol (str): The asset's ticker symbol to validate.

        Returns:
            dict: {
                "success": True,
                "exists": bool  # True if the ticker exists in the assets, False otherwise
            }

        Constraints:
            - Accepts any string as ticker_symbol input.
            - Returns exists: False for missing/empty ticker, but does not raise errors.
        """
        if not isinstance(ticker_symbol, str) or not ticker_symbol:
            # Invalid symbol, treat as non-existent (do not error)
            return {"success": True, "exists": False}

        exists = ticker_symbol in self.assets
        return {"success": True, "exists": exists}

    def get_asset_price_record_count(self, ticker_symbol: str) -> dict:
        """
        Return the count of price records available for a given ticker symbol.

        Args:
            ticker_symbol (str): The ticker symbol for the asset to query.

        Returns:
            dict:
                success: True and data: int (count of price records) on success,
                         e.g., { "success": True, "data": 15 }
                success: False and error: str if ticker does not exist,
                         e.g., { "success": False, "error": "Ticker symbol does not exist" }
    
        Constraints:
            - The ticker_symbol must refer to an existing Asset.
        """
        if ticker_symbol not in self.assets:
            return { "success": False, "error": "Ticker symbol does not exist" }
    
        count = len(self.price_records.get(ticker_symbol, []))
        return { "success": True, "data": count }

    def add_asset(self, ticker_symbol: str, asset_type: str, name: str, exchange: str) -> dict:
        """
        Add a new asset (by ticker_symbol) and its metadata to the market data system.

        Args:
            ticker_symbol (str): Unique ticker symbol for the asset.
            asset_type (str): Type of the asset (e.g., equity, index, derivative).
            name (str): Human-readable asset name.
            exchange (str): Exchange where the asset is listed.

        Returns:
            dict: {
                "success": True,
                "message": "Asset <ticker_symbol> added successfully."
            } or {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - ticker_symbol must be unique in the system.
            - All input fields must be non-empty.
        """
        # Validate input presence and non-empty fields
        if not all([ticker_symbol, asset_type, name, exchange]):
            return {"success": False, "error": "All fields (ticker_symbol, asset_type, name, exchange) are required and must be non-empty."}
    
        # Ensure ticker_symbol is unique
        if ticker_symbol in self.assets:
            return {"success": False, "error": f"Asset with ticker_symbol '{ticker_symbol}' already exists."}
    
        # Construct and add the asset
        asset_info = {
            "ticker_symbol": ticker_symbol,
            "asset_type": asset_type,
            "name": name,
            "exchange": exchange
        }
        self.assets[ticker_symbol] = asset_info
        return {"success": True, "message": f"Asset '{ticker_symbol}' added successfully."}

    def update_asset_info(self, ticker_symbol: str, name: str = None, exchange: str = None) -> dict:
        """
        Modify metadata fields (name, exchange) for an existing asset.

        Args:
            ticker_symbol (str): The identifier of the asset to update. Must already exist.
            name (str, optional): New name for asset. If not specified, name is unchanged.
            exchange (str, optional): New exchange for asset. If not specified, exchange is unchanged.

        Returns:
            dict: 
                Success: { "success": True, "message": "Asset info updated for <ticker_symbol>" }
                Failure: { "success": False, "error": <error message> }

        Constraints:
            - Asset must exist.
            - Only 'name' and 'exchange' fields may be changed.
            - 'ticker_symbol' and 'asset_type' are immutable.
            - At least one field (name or exchange) must be provided to update.
        """
        asset = self.assets.get(ticker_symbol)
        if not asset:
            return {"success": False, "error": "Asset with given ticker_symbol does not exist."}

        updates = {}
        if name is not None and name != asset["name"]:
            updates["name"] = name
        if exchange is not None and exchange != asset["exchange"]:
            updates["exchange"] = exchange

        if not updates:
            return {"success": False, "error": "No update fields specified, or values are identical to current asset info."}

        # Only allowed fields are updated
        asset.update(updates)

        # If an audit log were implemented, it would be appended to here.

        return {
            "success": True,
            "message": f"Asset info updated for {ticker_symbol}"
        }

    def add_price_record(
        self, 
        ticker_symbol: str, 
        timestamp: float, 
        open: float, 
        high: float, 
        low: float, 
        close: float, 
        volume: float
    ) -> dict:
        """
        Insert a new price/volume record for a given ticker at a specific timestamp.
    
        Args:
            ticker_symbol (str): The asset's ticker symbol.
            timestamp (float): Unix timestamp for this record.
            open (float): Opening price.
            high (float): Highest price.
            low (float): Lowest price.
            close (float): Closing price.
            volume (float): Volume traded.
        
        Returns:
            dict: {
                "success": bool,
                "message": str  # on success,
                "error": str    # on failure
            }
        
        Constraints:
            - Asset with ticker_symbol must exist.
            - No duplicate or overlapping PriceRecord timestamps for this ticker_symbol allowed.
            - Time series for ticker_symbol must remain strictly sequential (no duplicate timestamps).
        """
        # Constraint: Asset must exist
        if ticker_symbol not in self.assets:
            return {"success": False, "error": f"Asset '{ticker_symbol}' does not exist."}
    
        # Fetch or initialize records list
        records = self.price_records.get(ticker_symbol, [])
    
        # Enforce unique and non-overlapping timestamp for this ticker
        if any(record["timestamp"] == timestamp for record in records):
            return {
                "success": False,
                "error": f"Timestamp {timestamp} already exists for asset '{ticker_symbol}'."
            }
    
        # Create new PriceRecordInfo
        new_record = {
            "ticker_symbol": ticker_symbol,
            "timestamp": timestamp,
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        records.append(new_record)
        # Sort by timestamp to keep the price series orderly
        records.sort(key=lambda rec: rec["timestamp"])
        self.price_records[ticker_symbol] = records

        return {
            "success": True, 
            "message": f"Price record added for '{ticker_symbol}' at timestamp {timestamp}."
        }

    def delete_asset(self, ticker_symbol: str) -> dict:
        """
        Remove an asset and all its associated price records.

        Args:
            ticker_symbol (str): The ticker symbol of the asset to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Asset and associated price records deleted for <ticker_symbol>"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The ticker symbol must reference an existing asset.
            - Removes both the asset and all its price records, if any.
        """
        if ticker_symbol not in self.assets:
            return {
                "success": False,
                "error": f"Ticker symbol '{ticker_symbol}' does not exist."
            }
        # Remove asset
        del self.assets[ticker_symbol]
        # Remove price records if present
        if ticker_symbol in self.price_records:
            del self.price_records[ticker_symbol]
        return {
            "success": True,
            "message": f"Asset and associated price records deleted for '{ticker_symbol}'."
        }

    def delete_price_record(self, ticker_symbol: str, timestamp: float) -> dict:
        """
        Remove a price record for a ticker at a specific timestamp.

        Args:
            ticker_symbol (str): The ticker symbol of the asset.
            timestamp (float): The timestamp of the record to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Price record for <ticker_symbol> at <timestamp> deleted"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Ticker symbol must exist and have price records.
            - Price record for the given timestamp must exist.
        """
        # Check if the ticker_symbol exists in assets and price_records
        if ticker_symbol not in self.assets:
            return {"success": False, "error": f"Ticker symbol '{ticker_symbol}' does not exist."}

        if ticker_symbol not in self.price_records or not self.price_records[ticker_symbol]:
            return {"success": False, "error": f"No price records found for ticker symbol '{ticker_symbol}'."}

        # Find the price record with the specified timestamp
        price_list = self.price_records[ticker_symbol]
        index_to_remove = None
        for i, record in enumerate(price_list):
            if record["timestamp"] == timestamp:
                index_to_remove = i
                break

        if index_to_remove is None:
            return {"success": False, "error": f"No price record found for ticker '{ticker_symbol}' at timestamp {timestamp}."}

        # Remove the price record
        del price_list[index_to_remove]
        # If the list is now empty, optionally remove the ticker from price_records
        if not price_list:
            del self.price_records[ticker_symbol]
        else:
            self.price_records[ticker_symbol] = price_list

        return {
            "success": True,
            "message": f"Price record for '{ticker_symbol}' at timestamp {timestamp} deleted"
        }

    def correct_price_record(
        self,
        ticker_symbol: str,
        timestamp: float,
        open: float = None,
        high: float = None,
        low: float = None,
        close: float = None,
        volume: float = None,
    ) -> dict:
        """
        Update an existing price record’s fields for the given ticker and timestamp.

        Args:
            ticker_symbol (str): Ticker symbol of the asset.
            timestamp (float): Unique timestamp of the price record.
            open (float, optional): New open price.
            high (float, optional): New high price.
            low (float, optional): New low price.
            close (float, optional): New close price.
            volume (float, optional): New volume.

        Returns:
            dict: Success or failure message.

        Constraints:
            - Ticker_symbol must exist in the assets database.
            - PriceRecord with exact ticker_symbol and timestamp must exist.
            - All fields, if provided, must be non-negative numbers.
            - Timestamps for a ticker remain in sequence after update (not affected unless timestamp changes, which is not the case here).
            - At least one field to update must be provided.
        """
        if ticker_symbol not in self.assets:
            return { "success": False, "error": "Asset (ticker_symbol) does not exist." }

        price_list = self.price_records.get(ticker_symbol)
        if not price_list:
            return { "success": False, "error": "No price records for provided ticker_symbol." }

        # Find price record for the given timestamp
        record_idx = None
        for idx, rec in enumerate(price_list):
            if rec["timestamp"] == timestamp:
                record_idx = idx
                break
        if record_idx is None:
            return { "success": False, "error": "Price record not found for ticker and timestamp." }

        if all(param is None for param in [open, high, low, close, volume]):
            return { "success": False, "error": "No fields provided for update." }

        # Validate fields if provided
        for field_name, value in [("open", open), ("high", high), ("low", low), ("close", close), ("volume", volume)]:
            if value is not None and value < 0:
                return { "success": False, "error": f"Field {field_name} must be non-negative." }

        # Update the fields
        if open is not None:
            price_list[record_idx]["open"] = open
        if high is not None:
            price_list[record_idx]["high"] = high
        if low is not None:
            price_list[record_idx]["low"] = low
        if close is not None:
            price_list[record_idx]["close"] = close
        if volume is not None:
            price_list[record_idx]["volume"] = volume

        # As only field values changed (not timestamp), timestamp sequence/interface invariant is preserved

        return {
            "success": True,
            "message": f"Price record updated for {ticker_symbol} at {timestamp}"
        }


class StockMarketDataManagementSystem(BaseEnv):
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

    def get_asset_info(self, **kwargs):
        return self._call_inner_tool('get_asset_info', kwargs)

    def list_all_assets(self, **kwargs):
        return self._call_inner_tool('list_all_assets', kwargs)

    def get_price_history(self, **kwargs):
        return self._call_inner_tool('get_price_history', kwargs)

    def get_available_time_range(self, **kwargs):
        return self._call_inner_tool('get_available_time_range', kwargs)

    def list_price_records_for_tickers(self, **kwargs):
        return self._call_inner_tool('list_price_records_for_tickers', kwargs)

    def get_latest_price(self, **kwargs):
        return self._call_inner_tool('get_latest_price', kwargs)

    def get_aggregated_statistics(self, **kwargs):
        return self._call_inner_tool('get_aggregated_statistics', kwargs)

    def validate_ticker_symbol(self, **kwargs):
        return self._call_inner_tool('validate_ticker_symbol', kwargs)

    def get_asset_price_record_count(self, **kwargs):
        return self._call_inner_tool('get_asset_price_record_count', kwargs)

    def add_asset(self, **kwargs):
        return self._call_inner_tool('add_asset', kwargs)

    def update_asset_info(self, **kwargs):
        return self._call_inner_tool('update_asset_info', kwargs)

    def add_price_record(self, **kwargs):
        return self._call_inner_tool('add_price_record', kwargs)

    def delete_asset(self, **kwargs):
        return self._call_inner_tool('delete_asset', kwargs)

    def delete_price_record(self, **kwargs):
        return self._call_inner_tool('delete_price_record', kwargs)

    def correct_price_record(self, **kwargs):
        return self._call_inner_tool('correct_price_record', kwargs)

