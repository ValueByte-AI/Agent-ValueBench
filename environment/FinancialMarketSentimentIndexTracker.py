# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Tuple, Any, TypedDict



# Entity: SentimentIndex
class SentimentIndexInfo(TypedDict):
    index_id: str
    name: str
    description: str

# Entity: SentimentIndexValue
class SentimentIndexValueInfo(TypedDict):
    sentiment_index_id: str
    date: str  # ISO format
    score: float
    rating: str
    additional_metrics: Dict[str, float]

# Entity: MarketDataSource
class MarketDataSourceInfo(TypedDict):
    source_id: str
    name: str
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Sentiment indices: {index_id: SentimentIndexInfo}
        self.sentiment_indices: Dict[str, SentimentIndexInfo] = {}
        # Sentiment index values: {(sentiment_index_id, date): SentimentIndexValueInfo}
        self.sentiment_index_values: Dict[Tuple[str, str], SentimentIndexValueInfo] = {}
        # Market data sources: {source_id: MarketDataSourceInfo}
        self.data_sources: Dict[str, MarketDataSourceInfo] = {}

        # Constraints:
        # - Each (sentiment_index_id, date) pair must be unique in SentimentIndexValue.
        # - Only the latest date entry per index is considered "current."
        # - Ratings and scores must conform to an allowed set of values/formats for each index type.
        # - Data queries must return accurate historical records without retrospective modification.

    def get_sentiment_index_by_name(self, name: str) -> dict:
        """
        Retrieve SentimentIndex information (index_id, description) for the given name.

        Args:
            name (str): The sentiment index name (e.g., "Fear and Greed").

        Returns:
            dict: 
                - If found: {"success": True, "data": {index_id, name, description}}
                - If not found: {"success": False, "error": "Sentiment index not found"}

        Constraints:
            - Search is case-sensitive on the name attribute.
            - Only one index with a given name may exist.
        """
        for idx_info in self.sentiment_indices.values():
            if idx_info["name"] == name:
                return { "success": True, "data": {
                    "index_id": idx_info["index_id"],
                    "name": idx_info["name"],
                    "description": idx_info["description"]
                } }
        return { "success": False, "error": "Sentiment index not found" }

    def get_sentiment_indices(self) -> dict:
        """
        List all available sentiment indices.

        Returns:
            dict:
                success (bool): True if the operation is successful.
                data (List[SentimentIndexInfo]): List of all sentiment indices; may be empty if none exist.
        """
        indices = list(self.sentiment_indices.values())
        return { "success": True, "data": indices }

    def get_current_sentiment_index_value(self, sentiment_index_id: str) -> dict:
        """
        Obtain the latest (current) value, score, and rating for a given sentiment index.

        Args:
            sentiment_index_id (str): The unique identifier of the sentiment index.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": SentimentIndexValueInfo  # The current/latest value for the index
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., index does not exist or has no values
                    }

        Constraints:
            - Sentiment index must exist.
            - Only the latest entry by date is considered "current" per index.
        """
        if sentiment_index_id not in self.sentiment_indices:
            return { "success": False, "error": "Sentiment index does not exist." }

        # Find all values for this sentiment index
        values = [v for (idx, _), v in self.sentiment_index_values.items() if idx == sentiment_index_id]
        if not values:
            return { "success": False, "error": "No sentiment values found for this index." }

        # Select the entry with the greatest date (ISO format sortable)
        current_value = max(values, key=lambda v: v["date"])

        return { "success": True, "data": current_value }

    def get_sentiment_index_value_by_date(self, sentiment_index_id: str, date: str) -> dict:
        """
        Retrieve the sentiment index value (score, rating, and metrics) for a given index on a specific date.

        Args:
            sentiment_index_id (str): The ID of the sentiment index to query.
            date (str): The date (ISO format, e.g., "2023-06-01") for which to retrieve the value.

        Returns:
            dict: 
                Success: {"success": True, "data": SentimentIndexValueInfo}
                Failure: {"success": False, "error": str}
    
        Constraints:
            - sentiment_index_id must exist.
            - (sentiment_index_id, date) must reference a recorded value.
        """
        if sentiment_index_id not in self.sentiment_indices:
            return {"success": False, "error": "Sentiment index not found"}
        key = (sentiment_index_id, date)
        if key not in self.sentiment_index_values:
            return {"success": False, "error": "No sentiment value for specified date"}
        return {"success": True, "data": self.sentiment_index_values[key]}

    def get_sentiment_index_history(self, sentiment_index_id: str) -> dict:
        """
        Retrieve the full historical time series for a sentiment index: all date-value records.

        Args:
            sentiment_index_id (str): The ID of the sentiment index to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[SentimentIndexValueInfo],  # List of historical records (sorted by date ascending)
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # Reason, e.g. index does not exist
                    }

        Constraints:
            - Sentiment index must exist in the system.
            - History includes all SentimentIndexValue entries with matching sentiment_index_id.
        """
        if sentiment_index_id not in self.sentiment_indices:
            return { "success": False, "error": "Sentiment index does not exist" }

        # Filter all records with matching index_id
        values = [
            v for (idx, _), v in self.sentiment_index_values.items()
            if idx == sentiment_index_id
        ]
        # Optional: sort by date (ISO format so string sort works)
        values_sorted = sorted(values, key=lambda x: x["date"])

        return { "success": True, "data": values_sorted }

    def get_market_data_sources(self) -> dict:
        """
        List all available external market data sources integrated into the system.

        Returns:
            dict: {
                "success": True,
                "data": List[MarketDataSourceInfo]  # List of all registered market data sources (may be empty)
            }

        This operation has no input parameters and cannot fail unless the system is in an inconsistent state.
        """
        data_sources_list = list(self.data_sources.values())
        return { "success": True, "data": data_sources_list }

    def get_sentiment_index_value_metrics(self, sentiment_index_id: str, date: str) -> dict:
        """
        Retrieve all additional metrics for the specified sentiment index value.

        Args:
            sentiment_index_id (str): The unique ID of the sentiment index.
            date (str): The date of the sentiment index value (ISO format, e.g. "2024-06-13").

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, float],  # Additional metrics mapping
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - (sentiment_index_id, date) must exist in the sentiment_index_values mapping.
            - No modifications to the data; only retrieval.
        """
        key = (sentiment_index_id, date)
        if key not in self.sentiment_index_values:
            return {
                "success": False,
                "error": "No sentiment index value found for the specified index_id and date."
            }
        value_info = self.sentiment_index_values[key]
        metrics = value_info.get("additional_metrics", {})
        return {
            "success": True,
            "data": metrics
        }

    def add_sentiment_index(self, index_id: str, name: str, description: str) -> dict:
        """
        Add a new sentiment index type to the system.

        Args:
            index_id (str): Unique identifier for the sentiment index.
            name (str): Human-readable name of the index.
            description (str): Description of the index.

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "Sentiment index added successfully." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - index_id must be unique.
            - All arguments should be non-empty strings.
        """
        if not index_id or not isinstance(index_id, str):
            return { "success": False, "error": "index_id must be a non-empty string." }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "name must be a non-empty string." }
        if not description or not isinstance(description, str):
            return { "success": False, "error": "description must be a non-empty string." }

        if index_id in self.sentiment_indices:
            return { "success": False, "error": "index_id already exists." }

        self.sentiment_indices[index_id] = {
            "index_id": index_id,
            "name": name,
            "description": description
        }
        return { "success": True, "message": "Sentiment index added successfully." }

    def add_sentiment_index_value(
        self,
        sentiment_index_id: str,
        date: str,
        score: float,
        rating: str,
        additional_metrics: Dict[str, float]
    ) -> dict:
        """
        Insert a new value (score, rating, metrics) for a sentiment index for a specific date.

        Args:
            sentiment_index_id (str): The index to which this value belongs (must exist).
            date (str): Date in ISO format (YYYY-MM-DD, must be unique for the index).
            score (float): Numeric score for the index value.
            rating (str): Qualitative rating (must be non-empty).
            additional_metrics (Dict[str, float]): Optional additional numeric metrics.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Sentiment index value added." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - sentiment_index_id must refer to an existing SentimentIndex.
            - (sentiment_index_id, date) pair must be unique (not already present).
            - rating must be non-empty.
            - score must be a float.
        """

        # Check that index exists
        if sentiment_index_id not in self.sentiment_indices:
            return { "success": False, "error": "Sentiment index does not exist." }

        # Check uniqueness
        if (sentiment_index_id, date) in self.sentiment_index_values:
            return { "success": False, "error": "Sentiment index value for this date already exists." }

        # Validate rating
        if not isinstance(rating, str) or rating.strip() == "":
            return { "success": False, "error": "Rating must be a non-empty string." }

        # Validate score
        try:
            score_val = float(score)  # accept floats and ints
        except (ValueError, TypeError):
            return { "success": False, "error": "Score must be a float." }

        # Validate additional_metrics type
        if not isinstance(additional_metrics, dict):
            return { "success": False, "error": "additional_metrics must be a dictionary." }
        for k, v in additional_metrics.items():
            try:
                float(v)
            except (ValueError, TypeError):
                return { "success": False, "error": f"Metric '{k}' value must be a float." }

        # All checks passed, insert
        value_info = {
            "sentiment_index_id": sentiment_index_id,
            "date": date,
            "score": score_val,
            "rating": rating,
            "additional_metrics": dict(additional_metrics)
        }
        self.sentiment_index_values[(sentiment_index_id, date)] = value_info

        return { "success": True, "message": "Sentiment index value added." }

    def add_market_data_source(self, source_id: str, name: str, description: str) -> dict:
        """
        Add a new external market data source to the registry.

        Args:
            source_id (str): Unique identifier for the market data source.
            name (str): Name of the market data source.
            description (str): Description of the data source.

        Returns:
            dict:
            - If successful:
                {
                    "success": True,
                    "message": "Market data source '<name>' added successfully."
                }
            - If failed:
                {
                    "success": False,
                    "error": str  # Description of why adding failed
                }

        Constraints:
            - The source_id must be unique.
            - Name and description must be non-empty.
        """
        if not source_id or not isinstance(source_id, str):
            return { "success": False, "error": "source_id must be a non-empty string" }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "name must be a non-empty string" }
        if not description or not isinstance(description, str):
            return { "success": False, "error": "description must be a non-empty string" }
        if source_id in self.data_sources:
            return { "success": False, "error": f"Market data source with id '{source_id}' already exists" }

        self.data_sources[source_id] = {
            "source_id": source_id,
            "name": name,
            "description": description,
        }
        return { "success": True, "message": f"Market data source '{name}' added successfully." }

    def remove_sentiment_index(self, index_id: str) -> dict:
        """
        Remove a sentiment index by its index_id from the system.
        Constraints:
          - The sentiment index must exist.
          - It must not have any associated SentimentIndexValue records (i.e., (index_id, date) entries).
        Args:
            index_id (str): The index id of the SentimentIndex to remove.
        Returns:
            dict: 
              {"success": True, "message": "Sentiment index removed successfully."}
              or
              {"success": False, "error": "reason"}
        """
        if index_id not in self.sentiment_indices:
            return { "success": False, "error": "Sentiment index not found." }

        # Check referential integrity: no SentimentIndexValue can reference this index_id
        for key in self.sentiment_index_values:
            if key[0] == index_id:
                return {
                    "success": False,
                    "error": "Sentiment index has associated values and cannot be removed."
                }

        del self.sentiment_indices[index_id]
        return { "success": True, "message": "Sentiment index removed successfully." }

    def remove_market_data_source(self, source_id: str, is_admin: bool = False) -> dict:
        """
        Delete (remove) a market data source from the system.

        Args:
            source_id (str): The unique identifier for the data source.
            is_admin (bool, optional): Whether the requester is an admin (must be True to proceed).

        Returns:
            dict: {
                "success": True,
                "message": "Market data source <source_id> removed."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only admin users (is_admin=True) can perform this operation.
            - The data source must exist.
            - Does not affect any historical sentiment index values.
        """
        if not is_admin:
            return { "success": False, "error": "Admin privileges required to remove market data source." }

        if source_id not in self.data_sources:
            return { "success": False, "error": f"Market data source '{source_id}' does not exist." }

        del self.data_sources[source_id]
        return { "success": True, "message": f"Market data source '{source_id}' removed." }


class FinancialMarketSentimentIndexTracker(BaseEnv):
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
            if key == "sentiment_index_values" and isinstance(value, dict):
                normalized = {}
                for entry in value.values():
                    if not isinstance(entry, dict):
                        continue
                    sentiment_index_id = entry.get("sentiment_index_id")
                    date = entry.get("date")
                    if isinstance(sentiment_index_id, str) and isinstance(date, str):
                        normalized[(sentiment_index_id, date)] = copy.deepcopy(entry)
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

    def get_sentiment_index_by_name(self, **kwargs):
        return self._call_inner_tool('get_sentiment_index_by_name', kwargs)

    def get_sentiment_indices(self, **kwargs):
        return self._call_inner_tool('get_sentiment_indices', kwargs)

    def get_current_sentiment_index_value(self, **kwargs):
        return self._call_inner_tool('get_current_sentiment_index_value', kwargs)

    def get_sentiment_index_value_by_date(self, **kwargs):
        return self._call_inner_tool('get_sentiment_index_value_by_date', kwargs)

    def get_sentiment_index_history(self, **kwargs):
        return self._call_inner_tool('get_sentiment_index_history', kwargs)

    def get_market_data_sources(self, **kwargs):
        return self._call_inner_tool('get_market_data_sources', kwargs)

    def get_sentiment_index_value_metrics(self, **kwargs):
        return self._call_inner_tool('get_sentiment_index_value_metrics', kwargs)

    def add_sentiment_index(self, **kwargs):
        return self._call_inner_tool('add_sentiment_index', kwargs)

    def add_sentiment_index_value(self, **kwargs):
        return self._call_inner_tool('add_sentiment_index_value', kwargs)

    def add_market_data_source(self, **kwargs):
        return self._call_inner_tool('add_market_data_source', kwargs)

    def remove_sentiment_index(self, **kwargs):
        return self._call_inner_tool('remove_sentiment_index', kwargs)

    def remove_market_data_source(self, **kwargs):
        return self._call_inner_tool('remove_market_data_source', kwargs)
