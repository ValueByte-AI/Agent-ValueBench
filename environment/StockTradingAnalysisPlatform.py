# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List, Dict



class StockInfo(TypedDict):
    stock_id: str
    symbol: str
    name: str
    exchange: str

class PriceDataInfo(TypedDict):
    stock_id: str
    timestamp: str  # ISO format or UNIX epoch as string
    open: float
    close: float
    high: float
    low: float
    volume: int

class TechnicalSignalInfo(TypedDict):
    stock_id: str
    signal_type: str
    signal_time: str  # ISO format or UNIX epoch as string
    signal_a: float  # can be confidence, measurement, etc.

class PaginationStateInfo(TypedDict):
    query_id: str
    current_page: int
    page_size: int
    total_result: int

class _GeneratedEnvImpl:
    def __init__(self):
        # Stocks mapped by stock_id: {stock_id: StockInfo}
        self.stocks: Dict[str, StockInfo] = {}

        # Historical/real-time price data mapped by stock_id: {stock_id: List[PriceDataInfo]}
        self.price_data: Dict[str, List[PriceDataInfo]] = {}

        # Technical signals mapped by stock_id: {stock_id: List[TechnicalSignalInfo]}
        self.technical_signals: Dict[str, List[TechnicalSignalInfo]] = {}

        # Pagination state mapped by query_id: {query_id: PaginationStateInfo}
        self.pagination_states: Dict[str, PaginationStateInfo] = {}

        # Constraint notes:
        # - Technical signals must be derived from valid historical price sequences.
        # - Pagination must present non-overlapping, ordered results.
        # - Stock and signal records must be linked and consistent (e.g., signals reference existing stocks).

    def get_stocks_by_signal_type(self, signal_type: str) -> dict:
        """
        Retrieve a list of StockInfo objects for stocks that have at least one technical signal of the specified type.

        Args:
            signal_type (str): The technical signal type to search for (e.g. "Bullish Hammer").

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[StockInfo],  # Possibly empty list if no matches
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g., missing/invalid input
                }

        Constraints:
            - Only stocks recognized in self.stocks are considered.
            - No duplicates in result.
            - Results reflect only valid (referenced) stock_ids from technical signals.
        """
        if not signal_type or not isinstance(signal_type, str):
            return { "success": False, "error": "Signal type must be specified as a non-empty string" }
    
        matching_stock_ids = set()
        for stock_id, signals in self.technical_signals.items():
            for signal in signals:
                if signal.get("signal_type") == signal_type:
                    if stock_id in self.stocks:
                        matching_stock_ids.add(stock_id)
                    break  # Once found, no need to check more signals for this stock
    
        # Gather StockInfo for each matched stock_id
        result = [self.stocks[stock_id] for stock_id in matching_stock_ids]

        return {"success": True, "data": result}

    def get_technical_signals_by_stock(self, stock_id: str) -> dict:
        """
        Fetch all technical signals for a given stock_id.

        Args:
            stock_id (str): The unique identifier of the stock.

        Returns:
            dict: {
                "success": True,
                "data": List[TechnicalSignalInfo]  # all technical signals for the stock, possibly empty
            }
            OR
            {
                "success": False,
                "error": str  # reason of failure, e.g. stock_id does not exist
            }

        Constraints:
            - stock_id must refer to an existing stock.
            - Signal records must reference existing stocks.
        """
        if stock_id not in self.stocks:
            return { "success": False, "error": "Stock ID does not exist" }
        signals = self.technical_signals.get(stock_id, [])
        return { "success": True, "data": signals }

    def get_signal_details(
        self, 
        stock_id: str,
        signal_type: str,
        signal_time: str
    ) -> dict:
        """
        Retrieve detailed information for a specified technical signal.

        Args:
            stock_id (str): The stock ID to which the signal belongs.
            signal_type (str): Type of technical signal (e.g., 'Bullish Hammer').
            signal_time (str): Time the signal was generated (ISO format).

        Returns:
            dict:
                success: True and data with the TechnicalSignalInfo on success;
                otherwise success: False and a descriptive error.

        Constraints:
            - The stock must exist.
            - The signal must exist for the provided stock, type, and time.
        """
        # Check stock exists
        if stock_id not in self.stocks:
            return { "success": False, "error": "Stock ID does not exist." }

        # Check signals exist for stock
        signals = self.technical_signals.get(stock_id, [])
        # Find technical signal with given type and time
        for signal in signals:
            if signal["signal_type"] == signal_type and signal["signal_time"] == signal_time:
                return { "success": True, "data": signal }

        return { "success": False, "error": "Technical signal not found for specified parameters." }

    def get_stock_info_by_id(self, stock_id: str) -> dict:
        """
        Retrieve the full StockInfo dictionary for a given stock_id.

        Args:
            stock_id (str): The unique identifier of the stock.

        Returns:
            dict:
                - On success: { "success": True, "data": StockInfo }
                - On failure (not found): { "success": False, "error": "Stock not found" }

        Constraints:
            - The stock_id must exist in the platform's records.
        """
        stock_info = self.stocks.get(stock_id)
        if stock_info is None:
            return { "success": False, "error": "Stock not found" }
        return { "success": True, "data": stock_info }

    def get_stock_info_by_symbol(self, symbol: str) -> dict:
        """
        Retrieve StockInfo for a given stock symbol.

        Args:
            symbol (str): The ticker symbol to search for.

        Returns:
            dict:
                { "success": True, "data": StockInfo } if found,
                { "success": False, "error": "Stock symbol not found" } otherwise.

        Constraints:
            - Symbol matching is case-insensitive.
            - Symbol must match a loaded stock.
        """
        if not symbol or not isinstance(symbol, str):
            return { "success": False, "error": "Invalid symbol" }

        for stock_info in self.stocks.values():
            if stock_info["symbol"].upper() == symbol.upper():
                return { "success": True, "data": stock_info }

        return { "success": False, "error": "Stock symbol not found" }

    def list_all_stocks(self) -> dict:
        """
        Return the complete list of all supported stocks.

        Returns:
            dict: {
                "success": True,
                "data": List[StockInfo]  # List of all stocks, empty if none
            }

        Constraints:
            - No input or selection constraint.
            - Returns all supported stocks currently loaded in the platform.
        """
        stock_list = list(self.stocks.values())
        return { "success": True, "data": stock_list }


    def get_price_data(
        self,
        stock_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> dict:
        """
        Fetch price data (historical/real-time) for a specified stock, optionally within a given time window.

        Args:
            stock_id (str): The ID of the stock for which to fetch price data.
            start_time (Optional[str]): Inclusive lower bound for timestamp (ISO8601 or UNIX string). If None, no lower bound.
            end_time (Optional[str]): Inclusive upper bound for timestamp. If None, no upper bound.

        Returns:
            dict: {
                "success": True,
                "data": List[PriceDataInfo]   # List of matching price data entries (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - stock_id must exist in the stocks dictionary.
            - If both start_time and end_time are provided and start_time > end_time, returns error.
        """
        # Check that the stock_id exists
        if stock_id not in self.stocks:
            return {"success": False, "error": "Stock not found"}

        # Get all price data for this stock
        all_data: List[PriceDataInfo] = self.price_data.get(stock_id, [])

        # Validate time range
        if start_time and end_time and start_time > end_time:
            return {"success": False, "error": "Invalid time window: start_time > end_time"}

        # Filter based on time window if provided
        if start_time or end_time:
            def within_time_window(entry: Dict) -> bool:
                ts = entry["timestamp"]
                if start_time and ts < start_time:
                    return False
                if end_time and ts > end_time:
                    return False
                return True
            filtered_data = [entry for entry in all_data if within_time_window(entry)]
        else:
            filtered_data = all_data

        return {"success": True, "data": filtered_data}

    def get_pagination_state(self, query_id: str) -> dict:
        """
        Retrieve the current pagination state for a given query.

        Args:
            query_id (str): The identifier for the paginated result set.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PaginationStateInfo,  # Pagination info (page number, size, total results, etc.)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g. "Query ID not found"
                    }

        Constraints:
            - query_id must exist in the pagination_states mapping to be valid.
        """
        state = self.pagination_states.get(query_id)
        if state is None:
            return { "success": False, "error": "Query ID not found" }
        return { "success": True, "data": state }

    def initialize_pagination(self, query_id: str, page_size: int, total_result: int) -> dict:
        """
        Initialize a new paginated result set for the specific query, tracked by query_id.
    
        Args:
            query_id (str): Unique identifier for pagination context/query.
            page_size (int): Number of results per page (must be > 0).
            total_result (int): Total results available for this query (must be >= 0).
        
        Returns:
            dict: 
                On success: {"success": True, "message": "Pagination initialized for query_id <query_id>"}
                On failure: {"success": False, "error": "<reason>"}
            
        Constraints:
            - query_id must not already exist in pagination_states.
            - page_size must be a positive integer.
            - total_result must be a non-negative integer.
        """
        if not isinstance(page_size, int) or page_size <= 0:
            return { "success": False, "error": "page_size must be a positive integer" }
        if not isinstance(total_result, int) or total_result < 0:
            return { "success": False, "error": "total_result must be a non-negative integer" }
        if query_id in self.pagination_states:
            return { "success": False, "error": "Pagination for query_id already exists" }
    
        self.pagination_states[query_id] = {
            "query_id": query_id,
            "current_page": 1,    # start at first page
            "page_size": page_size,
            "total_result": total_result
        }
        return {
            "success": True,
            "message": f"Pagination initialized for query_id {query_id}"
        }

    def go_to_next_page(self, query_id: str) -> dict:
        """
        Advance to the next page for the given paginated query.

        Args:
            query_id (str): Unique identifier for the paginated query.

        Returns:
            dict: {
                "success": True,
                "message": "Current page advanced to N"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Cannot advance past the last page.
            - Pagination state for the query_id must exist.
        """
        pag_state = self.pagination_states.get(query_id)
        if not pag_state:
            return {"success": False, "error": "Pagination state not found for query_id."}

        page_size = pag_state["page_size"]
        total_result = pag_state["total_result"]
        current_page = pag_state["current_page"]

        # Calculate total number of pages (minimum 1 if any results, 0 otherwise)
        total_pages = (total_result + page_size - 1) // page_size if page_size > 0 else 0

        if total_pages == 0:
            return {"success": False, "error": "No results to paginate."}

        if current_page >= total_pages:
            return {"success": False, "error": "Already at last page."}

        pag_state["current_page"] = current_page + 1
        self.pagination_states[query_id] = pag_state

        return {"success": True, "message": f"Current page advanced to {pag_state['current_page']}"}

    def go_to_previous_page(self, query_id: str) -> dict:
        """
        Move to the previous page for the given paginated query.

        Args:
            query_id (str): The unique identifier for the paginated query session.

        Returns:
            dict: 
                - On success:
                    {"success": True, "message": "Moved to previous page", "current_page": int}
                - On failure:
                    {"success": False, "error": str}
        Constraints:
            - If already at the first page (current_page == 1), stay at page 1 (do not decrement below 1).
            - query_id must exist in pagination_states.
        """
        pagination = self.pagination_states.get(query_id)
        if not pagination:
            return { "success": False, "error": "Query ID does not exist." }

        original_page = pagination["current_page"]
        if original_page <= 1:
            pagination["current_page"] = 1  # Always stay at page 1
            return {
                "success": True,
                "message": "Already at the first page.",
                "current_page": pagination["current_page"]
            }
        else:
            pagination["current_page"] -= 1
            return {
                "success": True,
                "message": "Moved to previous page.",
                "current_page": pagination["current_page"]
            }

    def set_page_size(self, query_id: str, page_size: int) -> dict:
        """
        Adjust the number of results returned per page for a given paginated query.

        Args:
            query_id (str): The identifier for the paginated query.
            page_size (int): The new page size (must be positive integer).

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - query_id must exist in self.pagination_states.
            - page_size must be a positive integer (> 0).
            - If current_page is now out of range given new page_size and total_result,
              adjust current_page to the maximum valid page.
        """

        if query_id not in self.pagination_states:
            return { "success": False, "error": "Invalid query_id" }

        if not isinstance(page_size, int) or page_size <= 0:
            return { "success": False, "error": "Page size must be a positive integer" }

        info = self.pagination_states[query_id]
        total_result = info["total_result"]

        # Calculate new max page index (1-based page numbers assumed)
        max_page = max(1, ((total_result - 1) // page_size) + 1)
        current_page = info["current_page"]

        # If current_page now exceeds max_page, adjust it to max_page
        if current_page > max_page:
            current_page = max_page

        # Update the info
        info["page_size"] = page_size
        info["current_page"] = current_page
        self.pagination_states[query_id] = info

        return {
            "success": True,
            "message": f"Page size updated for query_id {query_id} (page_size={page_size}, current_page={current_page})"
        }

    def reset_pagination(self, query_id: str) -> dict:
        """
        Reset pagination state to the first page (current_page = 1) for a given query.

        Args:
            query_id (str): The identifier of the pagination state to reset.

        Returns:
            dict: {
                "success": True,
                "message": "Pagination reset to first page for query <query_id>"
            }
            or
            {
                "success": False,
                "error": "Pagination state with query_id ... does not exist."
            }
        Constraints:
            - The pagination state for the given query_id must exist.
            - Only current_page is updated to 1; other fields remain unchanged.
        """
        pagination = self.pagination_states.get(query_id)
        if not pagination:
            return {"success": False, "error": f"Pagination state with query_id '{query_id}' does not exist."}

        pagination["current_page"] = 1
        return {"success": True, "message": f"Pagination reset to first page for query '{query_id}'"}

    def update_pagination_state(
        self,
        query_id: str,
        current_page: int = None,
        page_size: int = None
    ) -> dict:
        """
        Manually update page number or navigation parameters for a paginated result set.

        Args:
            query_id (str): Identifier for the paginated result set.
            current_page (int, optional): The new page number to set (must be >=1 and <= max page).
            page_size (int, optional): The new page size to set (must be >=1).

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message.
            }
            or
            {
                "success": False,
                "error": str  # Error reason.
            }

        Constraints:
            - Pagination state must exist for the given query_id.
            - current_page >= 1 and page_size >= 1.
            - After update, current_page cannot exceed total number of pages.
        """
        if query_id not in self.pagination_states:
            return { "success": False, "error": f"Pagination state for query_id {query_id} does not exist." }

        state = self.pagination_states[query_id]
        total_result = state["total_result"]
        updated = False

        # Page size update
        if page_size is not None:
            if page_size < 1:
                return { "success": False, "error": "page_size must be at least 1." }
            state["page_size"] = page_size
            updated = True

        # Determine the effective number of pages
        effective_page_size = state["page_size"]
        total_pages = ((total_result - 1) // effective_page_size + 1) if total_result > 0 else 1

        # Current page update
        if current_page is not None:
            if current_page < 1:
                return { "success": False, "error": "current_page must be at least 1." }
            if current_page > total_pages:
                return { "success": False, "error": f"current_page exceeds total_pages ({total_pages})." }
            state["current_page"] = current_page
            updated = True
        else:
            # After potential page_size update, if current_page would now be out of range, cap it
            if state["current_page"] > total_pages:
                state["current_page"] = total_pages

        if not updated:
            return { "success": False, "error": "No valid parameters to update were provided." }

        self.pagination_states[query_id] = state
        return {
            "success": True,
            "message": f"Updated pagination state for query_id {query_id}."
        }


class StockTradingAnalysisPlatform(BaseEnv):
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

    def get_stocks_by_signal_type(self, **kwargs):
        return self._call_inner_tool('get_stocks_by_signal_type', kwargs)

    def get_technical_signals_by_stock(self, **kwargs):
        return self._call_inner_tool('get_technical_signals_by_stock', kwargs)

    def get_signal_details(self, **kwargs):
        return self._call_inner_tool('get_signal_details', kwargs)

    def get_stock_info_by_id(self, **kwargs):
        return self._call_inner_tool('get_stock_info_by_id', kwargs)

    def get_stock_info_by_symbol(self, **kwargs):
        return self._call_inner_tool('get_stock_info_by_symbol', kwargs)

    def list_all_stocks(self, **kwargs):
        return self._call_inner_tool('list_all_stocks', kwargs)

    def get_price_data(self, **kwargs):
        return self._call_inner_tool('get_price_data', kwargs)

    def get_pagination_state(self, **kwargs):
        return self._call_inner_tool('get_pagination_state', kwargs)

    def initialize_pagination(self, **kwargs):
        return self._call_inner_tool('initialize_pagination', kwargs)

    def go_to_next_page(self, **kwargs):
        return self._call_inner_tool('go_to_next_page', kwargs)

    def go_to_previous_page(self, **kwargs):
        return self._call_inner_tool('go_to_previous_page', kwargs)

    def set_page_size(self, **kwargs):
        return self._call_inner_tool('set_page_size', kwargs)

    def reset_pagination(self, **kwargs):
        return self._call_inner_tool('reset_pagination', kwargs)

    def update_pagination_state(self, **kwargs):
        return self._call_inner_tool('update_pagination_state', kwargs)

