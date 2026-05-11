# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Tuple, TypedDict



class FinancialInstrumentInfo(TypedDict):
    instrument_id: str
    ticker_symbol: str
    type: str
    name: str
    exchange: str

class PriceDataInfo(TypedDict):
    instrument_id: str
    timestamp: str  # ISO formatted date-time string
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float

class TechnicalIndicatorInfo(TypedDict):
    indicator_type: str
    instrument_id: str
    timestamp: str  # ISO formatted date-time string
    value: float
    param: str  # parameterization, e.g. period/window

class _GeneratedEnvImpl:
    @staticmethod
    def _normalize_supported_indicator_names(raw_value):
        if isinstance(raw_value, str):
            return {item.strip() for item in raw_value.split(",") if item.strip()}
        if isinstance(raw_value, (list, tuple, set)):
            return {str(item).strip() for item in raw_value if str(item).strip()}
        return set()

    @staticmethod
    def _normalize_supported_params(raw_value):
        if isinstance(raw_value, Mapping):
            normalized = {}
            for indicator_type, params in raw_value.items():
                normalized[str(indicator_type)] = _GeneratedEnvImpl._normalize_supported_indicator_names(params)
            return normalized
        if isinstance(raw_value, str):
            params = _GeneratedEnvImpl._normalize_supported_indicator_names(raw_value)
            if params:
                return {
                    "EMA": set(params),
                    "MA": set(params),
                }
        return {}

    def __init__(self):
        """
        The environment for storing and analyzing financial market time-series data, instruments, and indicators.
        """

        # Financial Instruments: {instrument_id: FinancialInstrumentInfo}
        self.instruments: Dict[str, FinancialInstrumentInfo] = {}

        # Price Data: {instrument_id: {timestamp: PriceDataInfo}}
        self.price_data: Dict[str, Dict[str, PriceDataInfo]] = {}

        # Technical Indicators: {(indicator_type, instrument_id, timestamp, param): TechnicalIndicatorInfo}
        self.technical_indicators: Dict[
            Tuple[str, str, str, str], TechnicalIndicatorInfo
        ] = {}

        # Constraints:
        # - Each PriceData entry must reference a valid FinancialInstrument.
        # - TechnicalIndicator values must match underlying PriceData accuracy.
        # - Timestamps must be unique per instrument (no duplicate entries).
        # - Only supported indicator types/parameterizations are allowed.

    def get_instrument_by_ticker(self, ticker_symbol: str) -> dict:
        """
        Retrieve the FinancialInstrumentInfo for a given ticker symbol.

        Args:
            ticker_symbol (str): The ticker to search for.

        Returns:
            dict:
                - { "success": True, "data": FinancialInstrumentInfo }
                - { "success": False, "error": <reason> }

        Constraints:
            - Ticker symbol must exist among registered instruments.
            - At most one instrument is associated with a ticker symbol.
        """
        for instrument in self.instruments.values():
            if instrument["ticker_symbol"] == ticker_symbol:
                return { "success": True, "data": instrument }
        return { "success": False, "error": f"Instrument with ticker '{ticker_symbol}' not found." }

    def list_instruments(self) -> dict:
        """
        List all available financial instruments in the system with their metadata.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FinancialInstrumentInfo],  # May be empty if no instruments
            }
            or
            {
                "success": False,
                "error": str  # Unexpected environment or data structure failure
            }

        Constraints:
            - None (listing operation; always succeeds with empty list if no data)
        """
        if not hasattr(self, "instruments") or not isinstance(self.instruments, dict):
            return { "success": False, "error": "Instrument data is uninitialized or invalid." }

        data = list(self.instruments.values())
        return { "success": True, "data": data }

    def get_price_data_for_instrument(
        self,
        instrument_id: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """
        Retrieve price data (OHLCV) for a given instrument over a specified ISO date/time range.

        Args:
            instrument_id (str): The instrument to fetch data for.
            start_time (str): ISO-formatted string for range start (inclusive).
            end_time (str): ISO-formatted string for range end (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[PriceDataInfo],  # Chronologically sorted (by timestamp) price data
            }
            or
            {
                "success": False,
                "error": str  # error description
            }

        Constraints:
            - Instrument must exist in system.
            - start_time must be <= end_time.
        """
        if instrument_id not in self.instruments:
            return { "success": False, "error": "Instrument does not exist" }

        if start_time > end_time:
            return { "success": False, "error": "start_time must be <= end_time" }

        instrument_price_data = self.price_data.get(instrument_id, {})
        # ISO format allows lexical string comparison for ordering
        filtered_data = [
            pdi for ts, pdi in instrument_price_data.items()
            if start_time <= ts <= end_time
        ]
        # Sort chronologically (ascending by timestamp)
        filtered_data.sort(key=lambda x: x['timestamp'])

        return { "success": True, "data": filtered_data }

    def get_supported_indicators(self) -> dict:
        """
        List the supported technical indicator types and their accepted parameterizations.

        Returns:
            dict:
            {
                "success": True,
                "data": Dict[str, List[str]]
                    # Mapping from indicator type (e.g. "EMA") to list of accepted parameterization names (e.g. ["period"])
            }
            or
            {
                "success": False,
                "error": str  # Error message if unavailable
            }

        Constraints:
            - Supported indicators and parameterizations are environment-defined and static.
        """

        # For demonstration, we'll define a static mapping (could also be class/member variable).
        supported_indicators = {
            "EMA": ["period"],
            "MA": ["window"],
        }

        if not supported_indicators:
            return {"success": False, "error": "Supported indicator information unavailable."}

        return {"success": True, "data": supported_indicators}

    def get_technical_indicators(
        self,
        instrument_id: str,
        indicator_type: str,
        param: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> dict:
        """
        Retrieve stored technical indicator values for an instrument, indicator type, parameterization, and date/time range.

        Args:
            instrument_id (str): The instrument ID to query indicators for.
            indicator_type (str): The technical indicator type (e.g., "EMA", "MA").
            param (str): Parameterization for the indicator (e.g., period/window).
            start_timestamp (str): ISO datetime string (inclusive, lower bound).
            end_timestamp (str): ISO datetime string (inclusive, upper bound).

        Returns:
            dict: {
                "success": True,
                "data": List[TechnicalIndicatorInfo],  # Sorted by timestamp ascending, possibly empty.
            }
            or
            {
                "success": False,
                "error": str,  # Only on missing instrument.
            }

        Constraints:
            - The instrument_id must exist.
            - Technical indicators outside the date range (start, end) are not included.
            - If no indicators match, returns a success with empty data list.
        """
        # Check instrument existence
        if instrument_id not in self.instruments:
            return {"success": False, "error": "Instrument does not exist."}

        result = []
        for (ind_type, instr_id, ts, indicator_param), info in self.technical_indicators.items():
            if (
                ind_type == indicator_type
                and instr_id == instrument_id
                and indicator_param == param
                and start_timestamp <= ts <= end_timestamp
            ):
                result.append(info)

        # Sort by timestamp ascending
        result.sort(key=lambda info: info["timestamp"])

        return {"success": True, "data": result}

    def get_latest_technical_indicator(
        self,
        indicator_type: str,
        instrument_id: str,
        param: str
    ) -> dict:
        """
        Retrieve the latest (most recent) stored technical indicator value for a given instrument and indicator configuration.

        Args:
            indicator_type (str): The type of technical indicator (e.g., 'EMA', 'SMA').
            instrument_id (str): The instrument ID to retrieve the indicator for.
            param (str): Parameterization string (e.g., window/period).

        Returns:
            dict:
                - success: True, and 'data' contains the most recent TechnicalIndicatorInfo if found.
                - success: False, and 'error' describes why not found.

        Constraints:
            - If no technical indicator entry exists for this configuration, return an error.
        """
        candidates = [
            ti for (it, iid, ts, p), ti in self.technical_indicators.items()
            if it == indicator_type and iid == instrument_id and p == param
        ]
        if not candidates:
            return {
                "success": False,
                "error": "No technical indicator found for the specified configuration."
            }

        # Find the entry with the latest (max) timestamp (ISO string can be compared)
        latest_indicator = max(
            candidates,
            key=lambda ti: ti["timestamp"]
        )

        return {
            "success": True,
            "data": latest_indicator
        }

    def get_instrument_type(self, instrument_id: str) -> dict:
        """
        Query the instrument’s type (e.g., 'stock', 'bond', etc.) for the specified instrument_id.

        Args:
            instrument_id (str): The unique identifier for the financial instrument.

        Returns:
            dict:
                - On success: { "success": True, "data": str }
                    where data is the instrument type (e.g., 'stock').
                - On failure: { "success": False, "error": str }
                    where error explains the problem (e.g., instrument not found).

        Constraints:
            - instrument_id must reference a valid FinancialInstrument.
        """
        instrument = self.instruments.get(instrument_id)
        if not instrument:
            return {"success": False, "error": "Instrument not found"}
        return {"success": True, "data": instrument.get("type")}

    def check_price_data_consistency(self) -> dict:
        """
        Verify that for every stored technical indicator, the referenced price data (by instrument_id and timestamp) exists.

        Returns:
            dict: {
                "success": True,
                "data": List[
                    {
                        "indicator": TechnicalIndicatorInfo,
                        "consistent": bool,
                        "reason": Optional[str]
                    }
                ]
            }
            Always succeeds; returns a report of consistency for each indicator.

        Constraints:
            - Checks only existence of referenced price data for each indicator. 
            - Returns inconsistency if price data is missing, or instrument is missing.
        """
        results = []
        for indicator_key, indicator in self.technical_indicators.items():
            instrument_id = indicator["instrument_id"]
            timestamp = indicator["timestamp"]
            # First, check that instrument exists
            if instrument_id not in self.instruments:
                results.append({
                    "indicator": indicator,
                    "consistent": False,
                    "reason": "Instrument does not exist"
                })
                continue
            # Then, check that price data exists for that instrument and timestamp
            instrument_prices = self.price_data.get(instrument_id, None)
            if not instrument_prices or timestamp not in instrument_prices:
                results.append({
                    "indicator": indicator,
                    "consistent": False,
                    "reason": "Missing price data for instrument/timestamp"
                })
            else:
                results.append({
                    "indicator": indicator,
                    "consistent": True,
                    "reason": ""
                })
        return { "success": True, "data": results }

    def add_price_data(
        self,
        instrument_id: str,
        timestamp: str,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float
    ) -> dict:
        """
        Insert a new OHLCV (Open, High, Low, Close, Volume) entry for a given
        instrument at the specified timestamp.

        Args:
            instrument_id (str): The financial instrument's unique identifier.
            timestamp (str): ISO date-time string (must be unique per instrument).
            open_price (float): Opening price.
            high_price (float): Highest price.
            low_price (float): Lowest price.
            close_price (float): Closing price.
            volume (float): Traded volume.

        Returns:
            dict: {
                "success": True,
                "message": "Price data added for instrument <id> at <timestamp>."
            }
            or
            {
                "success": False,
                "error": "<Reason for failure>"
            }

        Constraints:
            - instrument_id must reference an existing financial instrument.
            - (instrument_id, timestamp) combination must not already exist.
            - Prices and volume must be non-negative (>= 0).
            - high_price >= max(open, close, low)
            - low_price <= min(open, close, high)
        """
        # Existence check
        if instrument_id not in self.instruments:
            return {"success": False, "error": f"Instrument '{instrument_id}' does not exist."}
    
        if instrument_id not in self.price_data:
            self.price_data[instrument_id] = {}

        if timestamp in self.price_data[instrument_id]:
            return {"success": False, "error": f"Price data for instrument '{instrument_id}' at timestamp '{timestamp}' already exists."}
    
        # Validity checks
        for value, name in [
            (open_price, "open_price"),
            (high_price, "high_price"),
            (low_price, "low_price"),
            (close_price, "close_price"),
            (volume, "volume")
        ]:
            if not (isinstance(value, (int, float))):
                return {"success": False, "error": f"{name} must be a number."}
            if value < 0:
                return {"success": False, "error": f"{name} must be non-negative."}
    
        # Plausibility of high/low/open/close consistency
        max_price = max(open_price, close_price, low_price)
        min_price = min(open_price, close_price, high_price)
        if high_price < max_price:
            return {"success": False, "error": "high_price must be >= max(open_price, close_price, low_price)."}
        if low_price > min_price:
            return {"success": False, "error": "low_price must be <= min(open_price, close_price, high_price)."}

        price_entry = {
            "instrument_id": instrument_id,
            "timestamp": timestamp,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "close_price": close_price,
            "volume": volume
        }

        self.price_data[instrument_id][timestamp] = price_entry
        return {
            "success": True,
            "message": f"Price data added for instrument '{instrument_id}' at timestamp '{timestamp}'."
        }

    def update_price_data(
        self,
        instrument_id: str,
        timestamp: str,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float
    ) -> dict:
        """
        Update an existing OHLCV (open, high, low, close, volume) PriceData entry for a given instrument and timestamp.

        Args:
            instrument_id (str): The instrument whose data to update (must exist).
            timestamp (str): ISO timestamp for the entry to update (must already exist).
            open_price (float): Updated open price.
            high_price (float): Updated high price.
            low_price (float): Updated low price.
            close_price (float): Updated close price.
            volume (float): Updated volume.

        Returns:
            dict: { "success": True, "message": "..." } on success;
                  { "success": False, "error": "..." } on failure.

        Constraints:
            - instrument_id must exist in the instruments DB.
            - PriceData for (instrument_id, timestamp) must already exist.
            - Does NOT create new price data.
            - (Optional) Prices and volume should be non-negative.
        """

        # Validate instrument
        if instrument_id not in self.instruments:
            return { "success": False, "error": "Instrument does not exist." }

        # Validate PriceData presence
        if instrument_id not in self.price_data or timestamp not in self.price_data[instrument_id]:
            return { "success": False, "error": "Price data entry does not exist for this instrument and timestamp." }

        if any(val < 0 for val in [open_price, high_price, low_price, close_price, volume]):
            return { "success": False, "error": "OHLCV prices and volume must be non-negative." }

        # Update the entry
        price_entry = self.price_data[instrument_id][timestamp]
        price_entry["open_price"] = open_price
        price_entry["high_price"] = high_price
        price_entry["low_price"] = low_price
        price_entry["close_price"] = close_price
        price_entry["volume"] = volume

        # Optionally, recalculate technical indicators here (TBD by another operation)

        return {
            "success": True,
            "message": f"Price data updated for instrument {instrument_id} at timestamp {timestamp}."
        }

    def delete_price_data_entry(self, instrument_id: str, timestamp: str) -> dict:
        """
        Remove an OHLCV price data entry for a given instrument and timestamp.

        Args:
            instrument_id (str): Unique identifier for the financial instrument.
            timestamp (str): ISO-formatted date-time string for the target entry.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Price data entry deleted for instrument {instrument_id} at {timestamp}"
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - The instrument_id must exist in price_data dictionary.
            - The timestamp must exist for this instrument's data dictionary.
            - No exception is raised; errors are returned in result dictionary.
        """
        if instrument_id not in self.price_data:
            return { "success": False, "error": f"Instrument {instrument_id} has no price data records." }
        if timestamp not in self.price_data[instrument_id]:
            return { "success": False, "error": f"No price data for instrument {instrument_id} at timestamp {timestamp}." }
        del self.price_data[instrument_id][timestamp]
        # Optionally, cleanup empty subdict
        if not self.price_data[instrument_id]:
            del self.price_data[instrument_id]
        return {
            "success": True,
            "message": f"Price data entry deleted for instrument {instrument_id} at {timestamp}"
        }

    def calculate_and_store_technical_indicator(
        self,
        indicator_type: str,
        instrument_id: str,
        timestamp: str,
        param: str,
    ) -> dict:
        """
        Compute and store a technical indicator (e.g., EMA, MA) for the given instrument, timestamp, and parameterization.
        Ensures consistency with underlying price data and system constraints.

        Args:
            indicator_type (str): The type of indicator to compute ('EMA' or 'MA' supported).
            instrument_id (str): The instrument ID to operate on.
            timestamp (str): The reference timestamp (ISO string) for the computed value.
            param (str): String parameterization (must be an integer window size, e.g., '10' for 10-period).

        Returns:
            dict: {
                "success": True,
                "message": "Calculated and stored ..."
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only 'EMA' and 'MA' indicator types are supported.
            - The instrument and required price data must exist.
            - The parameter must be a positive integer window size.
            - Timestamps must reference actual price data entries.
            - Indicator value must be consistent with price data.
            - If indicator already exists for (indicator_type, instrument_id, timestamp, param), it is overwritten.
        """
        # Supported indicators
        supported_indicators = {'EMA', 'MA'}
        if indicator_type not in supported_indicators:
            return {"success": False, "error": f"Unsupported indicator_type '{indicator_type}'"}

        # Validate instrument
        if instrument_id not in self.instruments:
            return {"success": False, "error": f"Instrument '{instrument_id}' does not exist"}

        # Validate param as integer window size
        try:
            window = int(param)
            if window <= 0:
                return {"success": False, "error": "Parameter 'param' (window) must be a positive integer"}
        except Exception:
            return {"success": False, "error": "Parameter 'param' must be a positive integer string"}

        # Validate price data for instrument
        if instrument_id not in self.price_data or not self.price_data[instrument_id]:
            return {"success": False, "error": f"No price data found for instrument '{instrument_id}'"}

        instrument_prices = self.price_data[instrument_id]

        if timestamp not in instrument_prices:
            return {"success": False, "error": f"Price data for timestamp '{timestamp}' not found for instrument '{instrument_id}'"}

        # Get all timestamps <= provided timestamp, sorted ascending
        sorted_timestamps = sorted(t for t in instrument_prices if t <= timestamp)
        if len(sorted_timestamps) < window:
            return {"success": False, "error": f"Insufficient price history (need {window} data points)"}

        # Restrict to the last 'window' timestamps up to and including 'timestamp'
        price_points = [instrument_prices[t]['close_price'] for t in sorted(sorted_timestamps)[-window:]]

        # Calculate value
        if indicator_type == 'MA':
            value = sum(price_points) / window

        elif indicator_type == 'EMA':
            # Simple EMA computation:
            # EMA_today = (Close_today * k) + (EMA_yesterday * (1-k)), k=2/(N+1)
            k = 2 / (window + 1)
            ema = price_points[0]
            for price in price_points[1:]:
                ema = (price * k) + (ema * (1 - k))
            value = ema

        else:
            # Should not reach here, for completeness
            return {"success": False, "error": "Indicator not implemented"}

        # Store the computed value (overwrite if exists)
        ti_key = (indicator_type, instrument_id, timestamp, param)
        ti_info = {
            "indicator_type": indicator_type,
            "instrument_id": instrument_id,
            "timestamp": timestamp,
            "value": value,
            "param": param
        }
        self.technical_indicators[ti_key] = ti_info

        return {
            "success": True,
            "message": f"Calculated and stored {indicator_type} for {instrument_id} at {timestamp} with param {param}."
        }

    def recalculate_all_indicators_for_instrument(self, instrument_id: str) -> dict:
        """
        Recalculate all stored technical indicators for a given instrument, ensuring they
        match the up-to-date price data. Updates internal technical_indicators storage in-place.

        Args:
            instrument_id (str): The ID of the financial instrument to update indicators for.

        Returns:
            dict:
              - On success: { "success": True, "message": "All technical indicators for instrument {instrument_id} have been recalculated." }
              - On error: { "success": False, "error": <reason> }

        Constraints:
            - Instrument must exist.
            - Only recalculates already-stored indicators for this instrument.
            - Skips updating an indicator if required price data is missing.
        """
        if instrument_id not in self.instruments:
            return { "success": False, "error": "Instrument does not exist." }

        updated_count = 0

        # Find all indicators for the instrument
        for key, indicator in list(self.technical_indicators.items()):
            ind_type, ind_inst_id, ind_timestamp, ind_param = key
            if ind_inst_id != instrument_id:
                continue

            # Get corresponding price data needed
            pdict = self.price_data.get(instrument_id, {})
            # For demonstration: just require that price data for the timestamp exists
            data = pdict.get(ind_timestamp)
            if not data:
                continue  # Cannot update indicator with missing price data

            # Recompute indicator value (mock formulas)
            if ind_type.lower() in ["moving_average", "ma"]:
                try:
                    period = int(ind_param)
                except:
                    continue

                # Collect close prices up to and including ind_timestamp
                timestamps_sorted = sorted(
                    [ts for ts in pdict if ts <= ind_timestamp],
                    reverse=True
                )
                closes = [
                    pdict[ts]["close_price"]
                    for ts in timestamps_sorted[:period]
                ]
                if len(closes) < period:
                    continue
                new_value = sum(closes) / period

            elif ind_type.lower() in ["ema", "exponential_moving_average"]:
                try:
                    period = int(ind_param)
                except:
                    continue

                # Simple EMA calculation (not exact; for demonstration)
                timestamps_sorted = sorted(
                    [ts for ts in pdict if ts <= ind_timestamp]
                )
                closes = [pdict[ts]["close_price"] for ts in timestamps_sorted]
                if not closes or len(closes) < period:
                    continue
                k = 2 / (period + 1)
                ema = closes[0]
                for price in closes[1:]:
                    ema = (price - ema) * k + ema
                new_value = ema
            else:
                # Other indicator types not supported; skip
                continue

            # Update the indicator value
            self.technical_indicators[key]["value"] = new_value
            updated_count += 1

        return {
            "success": True,
            "message": f"All technical indicators for instrument {instrument_id} have been recalculated ({updated_count} updated)."
        }

    def add_instrument(
        self,
        instrument_id: str,
        ticker_symbol: str,
        type: str,
        name: str,
        exchange: str
    ) -> dict:
        """
        Register a new financial instrument in the system.

        Args:
            instrument_id (str): Unique ID for the financial instrument.
            ticker_symbol (str): The instrument's ticker symbol.
            type (str): Instrument type (e.g., 'stock', 'bond', 'index').
            name (str): Formal name of the instrument.
            exchange (str): Which exchange it's traded on.

        Returns:
            dict: On success,
                { "success": True, "message": "Financial instrument <instrument_id> added." }
            On failure (duplicate or missing fields),
                { "success": False, "error": "<reason>" }

        Constraints:
            - Instrument ID must be unique.
            - All fields are required (non-empty strings).
        """
        # Validate required fields
        fields = {
            "instrument_id": instrument_id,
            "ticker_symbol": ticker_symbol,
            "type": type,
            "name": name,
            "exchange": exchange,
        }
        for fieldname, val in fields.items():
            if not isinstance(val, str) or not val.strip():
                return {"success": False, "error": f"Missing or empty field: {fieldname}"}

        if instrument_id in self.instruments:
            return {"success": False, "error": "Instrument already exists."}

        # Compose and add instrument info
        self.instruments[instrument_id] = {
            "instrument_id": instrument_id,
            "ticker_symbol": ticker_symbol,
            "type": type,
            "name": name,
            "exchange": exchange,
        }

        return {"success": True, "message": f"Financial instrument {instrument_id} added."}

    def remove_instrument(self, instrument_id: str) -> dict:
        """
        Permanently delete a FinancialInstrument and all related price data and technical indicators from the system.

        Args:
            instrument_id (str): Unique identifier for the financial instrument.

        Returns:
            dict:
                Success: { "success": True, "message": "Instrument <instrument_id> and all associated data removed." }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - Instrument must exist.
            - All related PriceData and TechnicalIndicator entries must also be deleted.
        """
        if instrument_id not in self.instruments:
            return { "success": False, "error": f"Instrument {instrument_id} does not exist." }

        # Delete instrument
        del self.instruments[instrument_id]

        # Delete associated price data (if any)
        if instrument_id in self.price_data:
            del self.price_data[instrument_id]

        # Delete associated technical indicators (may be multiple keys per instrument)
        to_delete = [
            key for key in self.technical_indicators
            if key[1] == instrument_id
        ]
        for key in to_delete:
            del self.technical_indicators[key]

        return {
            "success": True,
            "message": f"Instrument {instrument_id} and all associated data removed."
        }

    def delete_technical_indicator_entry(
        self, 
        indicator_type: str, 
        instrument_id: str, 
        timestamp: str,
        param: str
    ) -> dict:
        """
        Delete a stored technical indicator value for the specified configuration.

        Args:
            indicator_type (str): The type of technical indicator (e.g., "EMA", "SMA").
            instrument_id (str): The ID of the instrument.
            timestamp (str): The ISO formatted timestamp for the indicator value.
            param (str): The parameterization (e.g., period/window) for the indicator.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Technical indicator entry deleted." }
                - On failure: { "success": False, "error": "Technical indicator entry not found." }

        Constraints:
            - The technical indicator entry must exist to be deleted.
            - The combination (indicator_type, instrument_id, timestamp, param) uniquely identifies the entry.
        """
        key = (indicator_type, instrument_id, timestamp, param)
        if key not in self.technical_indicators:
            return {
                "success": False,
                "error": "Technical indicator entry not found."
            }
        del self.technical_indicators[key]
        return {
            "success": True,
            "message": "Technical indicator entry deleted."
        }

    def update_technical_indicator_entry(
        self,
        indicator_type: str,
        instrument_id: str,
        timestamp: str,
        param: str,
        value: float = None,
        new_param: str = None,
    ) -> dict:
        """
        Amend the value or configuration (param) of a stored technical indicator, maintaining system constraints.

        Args:
            indicator_type (str): The type of the indicator (e.g., 'EMA').
            instrument_id (str): The ID of the financial instrument.
            timestamp (str): The ISO-format timestamp for the indicator.
            param (str): The current parameterization (e.g., period/window).
            value (float, optional): New value for the indicator.
            new_param (str, optional): New parameterization (changes configuration window).

        Returns:
            dict: {
                "success": True,
                "message": "Technical indicator updated successfully"
            }
            or {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - The targeted indicator must exist.
            - If changing param, no duplicate (indicator_type, instrument_id, timestamp, new_param) may exist.
            - Only supported indicator types/param combinations may be set.
            - Underlying price data consistency must be maintained.
            - indicator_type, instrument_id, and timestamp are immutable for this operation.
        """

        key = (indicator_type, instrument_id, timestamp, param)
        if key not in self.technical_indicators:
            return {"success": False, "error": "Technical indicator entry does not exist."}

        # If changing param (i.e., the config/window), ensure new key uniqueness
        target_param = new_param if new_param is not None else param
        new_key = (indicator_type, instrument_id, timestamp, target_param)
        if new_key != key and new_key in self.technical_indicators:
            return {
                "success": False,
                "error": "Target configuration already exists for this indicator entry."
            }

        # (Optional) Supported indicator/param check -- here, we'll assume only types are checked.
        # If there is a supported indicator registry, add check here, e.g.:
        if hasattr(self, "_SUPPORTED_INDICATORS"):
            supported_indicator_names = self._normalize_supported_indicator_names(self._SUPPORTED_INDICATORS)
            if supported_indicator_names and indicator_type not in supported_indicator_names:
                return {
                    "success": False,
                    "error": f"Indicator type '{indicator_type}' is not supported."
                }
            if hasattr(self, "_SUPPORTED_PARAMS"):
                params_for_type = self._normalize_supported_params(self._SUPPORTED_PARAMS).get(indicator_type, set())
                if target_param not in params_for_type:
                    return {
                        "success": False,
                        "error": f"Parameter '{target_param}' is not supported for indicator '{indicator_type}'."
                    }

        # (Optional) Price data consistency check: instrument_id and timestamp must be valid price data
        if indicator_type != "custom":  # For standard indicators
            price_records = self.price_data.get(instrument_id, {})
            if timestamp not in price_records:
                return {
                    "success": False,
                    "error": "No price data available for the specified instrument and timestamp."
                }

        # Amend the technical indicator value/param
        indicator_info = self.technical_indicators.pop(key)
        if value is not None:
            indicator_info["value"] = value
        if new_param is not None:
            indicator_info["param"] = new_param

        # Insert with possibly new key
        self.technical_indicators[new_key] = indicator_info

        return {"success": True, "message": "Technical indicator updated successfully"}


class FinancialMarketDataAnalyticsSystem(BaseEnv):
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
            if key == "technical_indicators" and isinstance(value, dict):
                normalized = {}
                for indicator in value.values():
                    if not isinstance(indicator, dict):
                        continue
                    indicator_type = indicator.get("indicator_type")
                    instrument_id = indicator.get("instrument_id")
                    timestamp = indicator.get("timestamp")
                    param = indicator.get("param")
                    if all(isinstance(part, str) for part in (indicator_type, instrument_id, timestamp, param)):
                        normalized[(indicator_type, instrument_id, timestamp, param)] = copy.deepcopy(indicator)
                value = normalized
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

    def get_instrument_by_ticker(self, **kwargs):
        return self._call_inner_tool('get_instrument_by_ticker', kwargs)

    def list_instruments(self, **kwargs):
        return self._call_inner_tool('list_instruments', kwargs)

    def get_price_data_for_instrument(self, **kwargs):
        return self._call_inner_tool('get_price_data_for_instrument', kwargs)

    def get_supported_indicators(self, **kwargs):
        return self._call_inner_tool('get_supported_indicators', kwargs)

    def get_technical_indicators(self, **kwargs):
        return self._call_inner_tool('get_technical_indicators', kwargs)

    def get_latest_technical_indicator(self, **kwargs):
        return self._call_inner_tool('get_latest_technical_indicator', kwargs)

    def get_instrument_type(self, **kwargs):
        return self._call_inner_tool('get_instrument_type', kwargs)

    def check_price_data_consistency(self, **kwargs):
        return self._call_inner_tool('check_price_data_consistency', kwargs)

    def add_price_data(self, **kwargs):
        return self._call_inner_tool('add_price_data', kwargs)

    def update_price_data(self, **kwargs):
        return self._call_inner_tool('update_price_data', kwargs)

    def delete_price_data_entry(self, **kwargs):
        return self._call_inner_tool('delete_price_data_entry', kwargs)

    def calculate_and_store_technical_indicator(self, **kwargs):
        return self._call_inner_tool('calculate_and_store_technical_indicator', kwargs)

    def recalculate_all_indicators_for_instrument(self, **kwargs):
        return self._call_inner_tool('recalculate_all_indicators_for_instrument', kwargs)

    def add_instrument(self, **kwargs):
        return self._call_inner_tool('add_instrument', kwargs)

    def remove_instrument(self, **kwargs):
        return self._call_inner_tool('remove_instrument', kwargs)

    def delete_technical_indicator_entry(self, **kwargs):
        return self._call_inner_tool('delete_technical_indicator_entry', kwargs)

    def update_technical_indicator_entry(self, **kwargs):
        return self._call_inner_tool('update_technical_indicator_entry', kwargs)
