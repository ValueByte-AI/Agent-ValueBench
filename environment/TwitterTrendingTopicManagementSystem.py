# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class HashtagInfo(TypedDict):
    hashtag_id: str
    text: str
    category: str
    language: str
    trend_score: float
    last_updated_timestamp: str

class RegionInfo(TypedDict):
    region_id: str
    name: str
    country_code: str
    timezone: str

class TrendInfo(TypedDict):
    hashtag_id: str
    region_id: str
    trend_score: float
    rank: int
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Hashtags/Topics: {hashtag_id: HashtagInfo}
        self.hashtags: Dict[str, HashtagInfo] = {}

        # Regions: {region_id: RegionInfo}
        self.regions: Dict[str, RegionInfo] = {}

        # Trends per region: {region_id: List[TrendInfo]}
        # Each TrendInfo links a hashtag to its trending status in a specific region and time.
        self.trends: Dict[str, List[TrendInfo]] = {}

        # Constraints:
        # - Trending hashtags must be updated periodically based on user activity and engagement.
        # - Hashtag can trend in multiple regions simultaneously.
        # - Filters by region, language, or category must only return currently trending hashtags in the specified context.
        # - Only the most recent trends per region are considered for "latest" trend queries.

    def get_region_by_name(self, region_name: str) -> dict:
        """
        Retrieve region information by region name.

        Args:
            region_name (str): The name of the region to retrieve (e.g., "Japan").

        Returns:
            dict:
                - success: True, data: RegionInfo for the first region matching the name
                - success: False, error: "Region not found" (if no match)
        Constraints:
            - Region name lookup is case-sensitive.
            - Only the first matching region (if more exist) is returned.
        """
        for region in self.regions.values():
            if region["name"] == region_name:
                return {"success": True, "data": region}
        return {"success": False, "error": "Region not found"}

    def get_region_by_country_code(self, country_code: str) -> dict:
        """
        Retrieve all region infos matching the given ISO country code.

        Args:
            country_code (str): ISO country code, e.g., 'JP', 'KR', 'AU'.

        Returns:
            dict: {
                "success": True,
                "data": List[RegionInfo]  # List of regions with the given country code (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., invalid input
            }

        Constraints:
            - country_code must be a non-empty string.
            - Matches are case-insensitive.
        """
        # Validate input
        if not isinstance(country_code, str) or not country_code.strip():
            return { "success": False, "error": "Invalid or empty country code." }

        normalized_code = country_code.strip().upper()

        matched_regions = [
            region for region in self.regions.values()
            if region["country_code"].upper() == normalized_code
        ]

        return { "success": True, "data": matched_regions }

    def list_all_regions(self) -> dict:
        """
        Retrieve all available regions being tracked in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[RegionInfo],  # List of all region metadata dictionaries (may be empty)
            }

        Constraints:
            - None (simply returns all RegionInfo entries in the system).
        """
        all_regions = list(self.regions.values())
        return { "success": True, "data": all_regions }

    def get_latest_trends_by_region(self, region_id: str, sort_by: str = "rank") -> dict:
        """
        Get the most recent trending hashtags for a specified region (by region_id),
        sorted by rank (ascending) or trend_score (descending).

        Args:
            region_id (str): ID of the region to query trends for.
            sort_by (str): Either "rank" or "trend_score" (optional, default "rank").

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[TrendInfo]  # Trends at latest timestamp, sorted per sort_by.
                }
                or
                {
                    "success": False,
                    "error": "Reason"
                }

        Constraints:
            - Only the most recent trends per region (by timestamp) are considered.
            - If region does not exist, operation fails.
            - If region has no trends, returns empty list as success.
            - If sort_by is invalid, defaults to "rank".
        """
        if region_id not in self.regions:
            return {"success": False, "error": "Region not found"}

        region_trends = self.trends.get(region_id, [])
        if not region_trends:
            return {"success": True, "data": []}

        # Find the latest timestamp for the region
        timestamps = [trend["timestamp"] for trend in region_trends]
        latest_timestamp = max(timestamps) if timestamps else None
        if latest_timestamp is None:
            return {"success": True, "data": []}

        # Get all trends with the latest timestamp
        latest_trends = [trend for trend in region_trends if trend["timestamp"] == latest_timestamp]

        # Determining sort key
        if sort_by not in {"rank", "trend_score"}:
            sort_by = "rank"

        if sort_by == "rank":
            latest_trends_sorted = sorted(latest_trends, key=lambda x: x["rank"])
        else:  # sort_by == "trend_score"
            latest_trends_sorted = sorted(latest_trends, key=lambda x: (-x["trend_score"], x["rank"]))

        return {"success": True, "data": latest_trends_sorted}

    def get_trending_hashtags_filtered(self, region_id: str = None, language: str = None, category: str = None) -> dict:
        """
        Retrieve currently trending hashtags filtered by one or more of: region, language, or category.
    
        Args:
            region_id (str, optional): Only include trends from this region (must exist if specified).
            language (str, optional): Only include hashtags of this language.
            category (str, optional): Only include hashtags of this category.
    
        Returns:
            dict:
                success (bool): Was the query successful?
                data (list[HashtagInfo]): List of currently trending hashtags matching all filters (possibly empty).
                error (str, optional): Description of the error on failure.
            
        Constraints:
            - If region_id is specified, it must exist.
            - Only currently trending hashtags are considered (latest trends per region).
            - Multiple filters combine as "AND".
        """
        # Step 1: Determine which trends to consider (by region)
        region_ids = []
        if region_id is not None:
            if region_id not in self.regions:
                return {"success": False, "error": f"Region ID '{region_id}' does not exist"}
            region_ids = [region_id]
        else:
            region_ids = list(self.regions.keys())
    
        trending_hashtag_ids = set()
    
        for rid in region_ids:
            region_trends = self.trends.get(rid, [])
            if not region_trends:
                continue
            # Find the latest timestamp among trends in this region
            latest_ts = max(t["timestamp"] for t in region_trends)
            # Take all trends from this region with exactly that timestamp
            current_trends = [t for t in region_trends if t["timestamp"] == latest_ts]
            trending_hashtag_ids.update([t["hashtag_id"] for t in current_trends])
    
        # Filter hashtag info
        result = []
        for hashtag_id in trending_hashtag_ids:
            hashtag = self.hashtags.get(hashtag_id)
            if not hashtag:
                continue  # Corrupted/missing state, skip
            if language is not None and hashtag["language"] != language:
                continue
            if category is not None and hashtag["category"] != category:
                continue
            result.append(hashtag)
    
        return {"success": True, "data": result}

    def get_hashtag_info(self, hashtag_id: str) -> dict:
        """
        Retrieve full metadata for a given hashtag/topic.

        Args:
            hashtag_id (str): The unique identifier of the hashtag/topic.

        Returns:
            dict: {
                "success": True,
                "data": HashtagInfo  # metadata of the hashtag
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Hashtag not found"
            }

        Constraints:
            - The hashtag_id must exist in the system.
        """
        if not hashtag_id or hashtag_id not in self.hashtags:
            return { "success": False, "error": "Hashtag not found" }

        return { "success": True, "data": self.hashtags[hashtag_id] }

    def list_trending_regions_for_hashtag(self, hashtag_id: str) -> dict:
        """
        Query all regions where a given hashtag is currently trending.

        Args:
            hashtag_id (str): The ID of the hashtag to query.

        Returns:
            dict:
              On success:
                {
                  "success": True,
                  "data": List[RegionInfo]  # List of region infos where hashtag is currently trending
                }
              On failure:
                {
                  "success": False,
                  "error": str  # Error description, e.g., hashtag not found
                }

        Constraints:
            - Only the most recent trends per region are considered for "currently trending".
            - The hashtag must exist in the system.
        """
        if hashtag_id not in self.hashtags:
            return { "success": False, "error": "Hashtag not found" }

        trending_regions = []
        for region_id, trend_list in self.trends.items():
            if not trend_list:
                continue
            latest_timestamp = max(trend["timestamp"] for trend in trend_list)
            latest_trends = [trend for trend in trend_list if trend["timestamp"] == latest_timestamp]
            if any(trend["hashtag_id"] == hashtag_id for trend in latest_trends):
                region_info = self.regions.get(region_id)
                if region_info:
                    trending_regions.append(region_info)

        return { "success": True, "data": trending_regions }

    def get_trend_history_for_region(self, region_id: str) -> dict:
        """
        Retrieve historical trending data (past rankings/scores) for a specified region.

        Args:
            region_id (str): The region's identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[TrendInfo]  # All historical trend records for the region (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure, e.g., region does not exist
            }

        Constraints:
            - The region must exist in self.regions.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region does not exist" }
    
        # return the trend history list (can be empty)
        history = self.trends.get(region_id, [])
        return { "success": True, "data": history }

    def get_trend_history_for_hashtag(self, hashtag_id: str) -> dict:
        """
        Retrieve historical trend information (when, where, score, rank) for the specified hashtag.

        Args:
            hashtag_id (str): Unique identifier for the hashtag/topic.

        Returns:
            dict: {
                "success": True,
                "data": List[TrendInfo]  # All TrendInfo records for this hashtag (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Explanation (e.g., 'Hashtag not found')
            }

        Constraints:
            - hashtag_id must exist in self.hashtags.
            - All records across all regions and timestamps must be included.
        """
        if hashtag_id not in self.hashtags:
            return {"success": False, "error": "Hashtag not found"}

        history = []
        for region_trends in self.trends.values():
            for trend in region_trends:
                if trend["hashtag_id"] == hashtag_id:
                    history.append(trend)

        return {"success": True, "data": history}

    def update_trending_hashtags_for_region(self, region_id: str, new_trends: list) -> dict:
        """
        Update the set of trending hashtags/topics and their ranks/scores for a given region.

        Args:
            region_id (str): ID of the region for which to update trending hashtags.
            new_trends (List[TrendInfo]): The latest list of trending hashtags/topics with
                                          their updated scores, ranks, and timestamps.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Trending hashtags for region <region_name> updated successfully."
                    }
                On error:
                    {
                        "success": False,
                        "error": <description>
                    }
    
        Constraints:
            - The region must exist.
            - All hashtag_ids in new_trends must exist in self.hashtags.
            - The existing list of trends for that region is completely replaced by new_trends.
        """
        # Check if region exists
        region_info = self.regions.get(region_id)
        if not region_info:
            return { "success": False, "error": "Region does not exist." }

        # Check that all hashtag_ids in new_trends exist
        missing_hashtags = [
            trend["hashtag_id"] for trend in new_trends if trend["hashtag_id"] not in self.hashtags
        ]
        if missing_hashtags:
            return {
                "success": False,
                "error": f"Hashtag(s) not found: {', '.join(missing_hashtags)}"
            }

        # Update the region's trending hashtags
        self.trends[region_id] = new_trends

        # Optionally update hashtag's trend_score and last_updated_timestamp (if wanted).
        # For now, only update if the hashtag's highest trend_score is increased.
        for trend in new_trends:
            hashtag_id = trend["hashtag_id"]
            # Update latest trend_score and last_updated_timestamp in hashtag info
            if hashtag_id in self.hashtags:
                hashtag = self.hashtags[hashtag_id]
                hashtag["trend_score"] = trend["trend_score"]
                hashtag["last_updated_timestamp"] = trend["timestamp"]

        return {
            "success": True,
            "message": f"Trending hashtags for region {region_info['name']} updated successfully."
        }

    def add_or_update_hashtag(
        self,
        hashtag_id: str,
        text: str = None,
        category: str = None,
        language: str = None,
        trend_score: float = None,
        last_updated_timestamp: str = None
    ) -> dict:
        """
        Add a new hashtag/topic to the system, or update its properties if it exists.

        Args:
            hashtag_id (str): The unique identifier for the hashtag/topic. (Required)
            text (str, optional): The hashtag text (e.g., "#ai").
            category (str, optional): Category of the hashtag.
            language (str, optional): ISO language code.
            trend_score (float, optional): The hashtag's current trend score.
            last_updated_timestamp (str, optional): Most recent update time (ISO8601 or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Added or updated hashtag <hashtag_id>"
              }
              or
              {
                "success": False,
                "error": "<reason>"
              }

        Constraints:
            - hashtag_id must not be empty.
            - For a new hashtag, at least text, category, language, trend_score, last_updated_timestamp must be provided.
            - For existing, at least one non-ID field must be provided.
        """
        if not hashtag_id or not isinstance(hashtag_id, str):
            return {"success": False, "error": "Invalid or empty hashtag_id"}

        is_new = hashtag_id not in self.hashtags

        if is_new:
            missing_fields = []
            if text is None:
                missing_fields.append('text')
            if category is None:
                missing_fields.append('category')
            if language is None:
                missing_fields.append('language')
            if trend_score is None:
                missing_fields.append('trend_score')
            if last_updated_timestamp is None:
                missing_fields.append('last_updated_timestamp')
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing fields for new hashtag: {', '.join(missing_fields)}"
                }
            self.hashtags[hashtag_id] = {
                "hashtag_id": hashtag_id,
                "text": text,
                "category": category,
                "language": language,
                "trend_score": trend_score,
                "last_updated_timestamp": last_updated_timestamp
            }
            return {
                "success": True,
                "message": f"Added new hashtag {hashtag_id}"
            }
        else:
            tag = self.hashtags[hashtag_id]
            fields_updated = 0
            if text is not None:
                tag['text'] = text
                fields_updated += 1
            if category is not None:
                tag['category'] = category
                fields_updated += 1
            if language is not None:
                tag['language'] = language
                fields_updated += 1
            if trend_score is not None:
                tag['trend_score'] = trend_score
                fields_updated += 1
            if last_updated_timestamp is not None:
                tag['last_updated_timestamp'] = last_updated_timestamp
                fields_updated += 1
            if fields_updated == 0:
                return {
                    "success": False,
                    "error": "No fields provided to update for existing hashtag"
                }
            self.hashtags[hashtag_id] = tag
            return {
                "success": True,
                "message": f"Updated hashtag {hashtag_id}"
            }

    def remove_hashtag_from_region_trending(self, hashtag_id: str, region_id: str) -> dict:
        """
        Remove a given hashtag from the current trending list of a specified region.

        Args:
            hashtag_id (str): The hashtag/topic id to remove from the region's trending list.
            region_id (str): The region id from which to remove the trending hashtag.

        Returns:
            dict: {
                "success": True,
                "message": "Hashtag {hashtag_id} removed from trending in region {region_id}."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - If specified region does not exist, operation fails.
            - If the hashtag is not trending in the region, operation fails.
            - All TrendInfo entries for the hashtag in that region will be removed.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region does not exist." }

        if region_id not in self.trends or not self.trends[region_id]:
            return { "success": False, "error": "No trending hashtags found for the specified region." }

        # Find and remove all TrendInfo entries matching the hashtag
        original_trend_count = len(self.trends[region_id])
        self.trends[region_id] = [
            trend for trend in self.trends[region_id] if trend["hashtag_id"] != hashtag_id
        ]
        new_trend_count = len(self.trends[region_id])

        if original_trend_count == new_trend_count:
            return { "success": False, "error": "Hashtag is not currently trending in the specified region." }

        return {
            "success": True,
            "message": f"Hashtag {hashtag_id} removed from trending in region {region_id}."
        }


    def set_hashtag_trend_score(self, hashtag_id: str, region_id: str, new_trend_score: float) -> dict:
        """
        Manually adjust the trend score for a hashtag in a specific region.

        Args:
            hashtag_id (str): The hashtag/topic ID to adjust.
            region_id (str): The target region ID.
            new_trend_score (float): The new trend score to set.

        Returns:
            dict: {
                "success": True,
                "message": str  # operation completed description
            } or {
                "success": False,
                "error": str  # error description
            }

        Constraints:
            - Both hashtag_id and region_id must exist.
            - The (hashtag_id, region_id) pair must exist in current trends.
            - Only the most recent/current TrendInfo for this hashtag+region is updated.
            - Hashtag metadata is kept in sync with the updated trend score.
        """
        if hashtag_id not in self.hashtags:
            return { "success": False, "error": f"Hashtag ID '{hashtag_id}' does not exist" }

        if region_id not in self.regions:
            return { "success": False, "error": f"Region ID '{region_id}' does not exist" }

        if region_id not in self.trends or not self.trends[region_id]:
            return { "success": False, "error": f"No trends available for region '{region_id}'" }

        # Locate the latest TrendInfo for this hashtag in the region
        trend_list = [trend for trend in self.trends[region_id] if trend["hashtag_id"] == hashtag_id]
        if not trend_list:
            return { "success": False, "error": f"Hashtag '{hashtag_id}' is not currently trending in region '{region_id}'" }

        # Find the most recent one (based on timestamp, assuming format is ISO or float seconds string)
        # If multiple, pick the one with the max timestamp
        latest_trend = max(trend_list, key=lambda t: t["timestamp"])
    
        # Update the trend score in-place while preserving the region's current snapshot timestamp.
        latest_trend["trend_score"] = float(new_trend_score)
        if hashtag_id in self.hashtags:
            self.hashtags[hashtag_id]["trend_score"] = float(new_trend_score)
            self.hashtags[hashtag_id]["last_updated_timestamp"] = latest_trend["timestamp"]

        return {
            "success": True,
            "message": f"Trend score for hashtag '{hashtag_id}' in region '{region_id}' updated successfully"
        }

    def purge_outdated_trends(self) -> dict:
        """
        Remove or archive trends that are no longer current or relevant per region.
        For each region, only the latest trends (those with the most recent timestamp) are kept;
        all older trends are removed from the trends list for that region.

        Returns:
            dict: {
                "success": True,
                "message": "Purged outdated trends from all regions."
            }
            If no trends existed, still returns success.
    
        Constraints:
            - Only the most recent trends per region (by timestamp) are kept after the purge.
            - If multiple trends have the identical latest timestamp in a region, all are retained.
        """
        for region_id, trend_list in self.trends.items():
            if not trend_list:
                continue  # Nothing to purge in this region
            # Find the maximum timestamp in this region
            max_timestamp = max(trend["timestamp"] for trend in trend_list)
            # Keep only trends with this max timestamp
            self.trends[region_id] = [
                trend for trend in trend_list if trend["timestamp"] == max_timestamp
            ]
        return {"success": True, "message": "Purged outdated trends from all regions."}


class TwitterTrendingTopicManagementSystem(BaseEnv):
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

    def get_region_by_name(self, **kwargs):
        return self._call_inner_tool('get_region_by_name', kwargs)

    def get_region_by_country_code(self, **kwargs):
        return self._call_inner_tool('get_region_by_country_code', kwargs)

    def list_all_regions(self, **kwargs):
        return self._call_inner_tool('list_all_regions', kwargs)

    def get_latest_trends_by_region(self, **kwargs):
        return self._call_inner_tool('get_latest_trends_by_region', kwargs)

    def get_trending_hashtags_filtered(self, **kwargs):
        return self._call_inner_tool('get_trending_hashtags_filtered', kwargs)

    def get_hashtag_info(self, **kwargs):
        return self._call_inner_tool('get_hashtag_info', kwargs)

    def list_trending_regions_for_hashtag(self, **kwargs):
        return self._call_inner_tool('list_trending_regions_for_hashtag', kwargs)

    def get_trend_history_for_region(self, **kwargs):
        return self._call_inner_tool('get_trend_history_for_region', kwargs)

    def get_trend_history_for_hashtag(self, **kwargs):
        return self._call_inner_tool('get_trend_history_for_hashtag', kwargs)

    def update_trending_hashtags_for_region(self, **kwargs):
        return self._call_inner_tool('update_trending_hashtags_for_region', kwargs)

    def add_or_update_hashtag(self, **kwargs):
        return self._call_inner_tool('add_or_update_hashtag', kwargs)

    def remove_hashtag_from_region_trending(self, **kwargs):
        return self._call_inner_tool('remove_hashtag_from_region_trending', kwargs)

    def set_hashtag_trend_score(self, **kwargs):
        return self._call_inner_tool('set_hashtag_trend_score', kwargs)

    def purge_outdated_trends(self, **kwargs):
        return self._call_inner_tool('purge_outdated_trends', kwargs)
