# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class SongInfo(TypedDict):
    song_id: str
    title: str
    release_date: str
    artist_ids: List[str]
    genre: str

class ArtistInfo(TypedDict):
    artist_id: str
    name: str
    country_of_origin: str
    active_date: str  # Could be changed to List[str] if representing a range

class ChartInfo(TypedDict):
    chart_id: str
    name: str
    region: str   # region_code
    chart_type: str

class ChartEntryInfo(TypedDict):
    chart_id: str
    song_id: str
    week_start_date: str
    position: int

class RegionInfo(TypedDict):
    region_code: str
    region_name: str

class WeekInfo(TypedDict):
    week_start_date: str
    week_end_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Music chart tracking database environment state.
        """

        # Songs: {song_id: SongInfo}
        self.songs: Dict[str, SongInfo] = {}  # Song: song_id, title, release_date, artist_ids, genre

        # Artists: {artist_id: ArtistInfo}
        self.artists: Dict[str, ArtistInfo] = {}  # Artist: artist_id, name, country_of_origin, active_date

        # Charts: {chart_id: ChartInfo}
        self.charts: Dict[str, ChartInfo] = {}  # Chart: chart_id, name, region, chart_type

        # ChartEntries: List of ChartEntryInfo
        self.chart_entries: List[ChartEntryInfo] = []  # ChartEntry: chart_id, song_id, week_start_date, position

        # Regions: {region_code: RegionInfo}
        self.regions: Dict[str, RegionInfo] = {}  # Region: region_code, region_name

        # Weeks: {week_start_date: WeekInfo}
        self.weeks: Dict[str, WeekInfo] = {}  # Week: week_start_date, week_end_date

        # Constraints (to be enforced in logic, noted here for clarity):
        # - Each ChartEntry must have a valid corresponding Song, Chart, and Week.
        # - A song can appear at most once per chart per week.
        # - Ranking positions (position) are unique within a chart and week.
        # - Regions must be valid ISO country/region codes.
        # - Charts are associated with only one region at a time.
        # - Chart data for a requested period must reference finalized (not provisional) results.
        self._chart_entry_finalized_default = None
        self._finalized_chart_weeks = set()

    def get_chart_by_name_and_region(self, name: str, region_code: str) -> dict:
        """
        Retrieve chart(s) having the specified name in the given region code.

        Args:
            name (str): Name of the chart.
            region_code (str): ISO code of the region.

        Returns:
            dict: {
                "success": True,
                "data": List[ChartInfo]  # All charts matching (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # error message if region is invalid
            }

        Constraints:
            - region_code must exist in self.regions (i.e., be a valid region).
        """
        if region_code not in self.regions:
            return { "success": False, "error": "Region code does not exist" }

        result = [
            chart_info
            for chart_info in self.charts.values()
            if chart_info["name"] == name and chart_info["region"] == region_code
        ]

        return { "success": True, "data": result }

    def get_charts_by_region(self, region_code: str) -> dict:
        """
        List all chart definitions (ChartInfo) associated with a specified region.

        Args:
            region_code (str): ISO region code to filter charts by.

        Returns:
            dict: {
                "success": True,
                "data": List[ChartInfo]  # List of charts for this region (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. "Region not found"
            }

        Constraints:
            - region_code must exist in self.regions.
            - Returns all charts linked to region_code; empty list if region valid but has no charts.
        """
        if region_code not in self.regions:
            return { "success": False, "error": "Region not found" }

        charts = [
            chart_info
            for chart_info in self.charts.values()
            if chart_info["region"] == region_code
        ]
        return { "success": True, "data": charts }

    def get_region_by_name(self, region_name: str) -> dict:
        """
        Retrieves the region_code associated with a given human-readable region name.

        Args:
            region_name (str): The region name to search for.

        Returns:
            dict: {
                "success": True,
                "data": str    # region_code of matching region
            }
            or
            {
                "success": False,
                "error": str   # Reason, e.g. region not found
            }

        Constraints:
            - region_name must exist in the regions dictionary values.
            - Returns the first matching region_code if multiple found (duplicate names are unlikely).
        """
        for region in self.regions.values():
            if region["region_name"] == region_name:
                return { "success": True, "data": region["region_code"] }
        return { "success": False, "error": "Region not found" }

    def get_weeks_by_start_dates(self, week_start_dates: list) -> dict:
        """
        Retrieve week objects for a list of week_start_dates.

        Args:
            week_start_dates (list of str): List of week_start_date strings to fetch info for.

        Returns:
            dict: {
                "success": True,
                "data": List[WeekInfo],  # List of existing week info objects (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason ("Input must be a list of week_start_dates")
            }

        Constraints:
            - Returns only weeks that exist in the database.
            - Accepts empty lists and returns empty result.
        """
        if not isinstance(week_start_dates, list):
            return {
                "success": False,
                "error": "Input must be a list of week_start_dates"
            }

        result = [
            self.weeks[week_start_date]
            for week_start_date in week_start_dates
            if week_start_date in self.weeks
        ]

        return {
            "success": True,
            "data": result
        }

    def get_chart_entries_for_chart_and_week(self, chart_id: str, week_start_date: str) -> dict:
        """
        Retrieves all chart entries for the specified chart_id and week_start_date.

        Args:
            chart_id (str): The ID of the chart.
            week_start_date (str): The start date of the week (YYYY-MM-DD format).

        Returns:
            dict: {
                "success": True,
                "data": List[ChartEntryInfo]  # May be empty if no entries exist
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., chart or week does not exist)
            }

        Constraints:
            - chart_id must exist in the database.
            - week_start_date must be a known, valid week.
            - Only include entries that match both.
            - Only finalized data is included (assumed all data is finalized unless provisional handling is implemented).
        """
        if chart_id not in self.charts:
            return {"success": False, "error": "Chart does not exist"}
        if week_start_date not in self.weeks:
            return {"success": False, "error": "Week does not exist"}

        # Filter for entries matching both chart_id and week_start_date
        entries = [
            entry for entry in self.chart_entries
            if entry["chart_id"] == chart_id and entry["week_start_date"] == week_start_date
        ]
        return {"success": True, "data": entries}

    def get_song_info(self, song_id: str) -> dict:
        """
        Retrieve metadata for a song given its song_id.

        Args:
            song_id (str): The unique identifier for the song.

        Returns:
            dict: {
                "success": True,
                "data": SongInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g. song_id not found)
            }

        Constraints:
            - song_id must exist in the database.
        """
        if song_id not in self.songs:
            return { "success": False, "error": "Song ID not found" }

        return { "success": True, "data": self.songs[song_id] }

    def get_artist_info(self, artist_id: str) -> dict:
        """
        Retrieve metadata (name, country_of_origin, active_date) about a given artist_id.

        Args:
            artist_id (str): The unique identifier for the artist.

        Returns:
            dict: {
                "success": True,
                "data": ArtistInfo  # All metadata about the artist
            }
            or
            {
                "success": False,
                "error": str  # Error message if artist_id is not found
            }

        Constraints:
            - artist_id must exist in the environment's artists dict.
        """
        artist = self.artists.get(artist_id)
        if artist is None:
            return { "success": False, "error": "Artist not found" }
        return { "success": True, "data": artist }

    def get_chart_entry(self, chart_id: str, song_id: str, week_start_date: str) -> dict:
        """
        Retrieve a specific chart entry uniquely identified by chart_id, song_id, and week_start_date.

        Args:
            chart_id (str): The unique identifier of the chart.
            song_id (str): The unique identifier of the song.
            week_start_date (str): The start date of the chart week (YYYY-MM-DD).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": ChartEntryInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "No chart entry found for the specified parameters."
                    }

        Constraints:
            - Returns the matching chart entry whether or not that chart/week has already been finalized.
            - Result uniquely determined by the tuple (chart_id, song_id, week_start_date).
        """
        for entry in self.chart_entries:
            if (
                entry["chart_id"] == chart_id and
                entry["song_id"] == song_id and
                entry["week_start_date"] == week_start_date
            ):
                # Optionally, could check if entry is finalized, but by default assumed so as per database constraints
                return {"success": True, "data": entry}

        return {
            "success": False,
            "error": "No chart entry found for the specified parameters."
        }

    def list_songs_on_chart_for_week(self, chart_id: str, week_start_date: str) -> dict:
        """
        List all songs and their positions for a given chart and week.

        Args:
            chart_id (str): The ID of the chart.
            week_start_date (str): The starting date of the week (YYYY-MM-DD).

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[dict],  # Each dict: {"song_id", "title", "position"}
                }
                - On error: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - ChartEntry must reference valid song, chart, and week in the system.
            - If chart_id or week_start_date not found, report error.
        """
        if chart_id not in self.charts:
            return { "success": False, "error": "Chart does not exist" }
        if week_start_date not in self.weeks:
            return { "success": False, "error": "Week does not exist" }

        # Gather chart entries for this chart and week
        entries = [
            entry for entry in self.chart_entries
            if entry["chart_id"] == chart_id and entry["week_start_date"] == week_start_date
        ]

        # Build response list: songs (with metadata)
        result = []
        for entry in entries:
            song_id = entry["song_id"]
            # Per constraints, should always exist, but be defensive
            song_info = self.songs.get(song_id)
            if not song_info:
                continue  # Or could skip/report error
            result.append({
                "song_id": song_id,
                "title": song_info["title"],
                "position": entry["position"]
            })

        # Optionally, sort by position (ascending)
        result.sort(key=lambda x: x["position"])

        return { "success": True, "data": result }

    def is_chart_entry_finalized(self, chart_id: str, week_start_date: str) -> dict:
        """
        Check if the chart data for a specified chart and week is finalized (historically accurate).

        Args:
            chart_id (str): The unique ID for the chart.
            week_start_date (str): The start date of the week to check, in string format.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if finalized, False if not finalized
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., chart or week not found)
            }

        Constraints:
            - The chart_id and week_start_date must both be valid and present in self.charts and self.weeks.
            - Finalization state is assumed to be tracked in self.weeks[week_start_date]['finalized'] (bool).
        """
        # Check for chart existence
        if chart_id not in self.charts:
            return {"success": False, "error": "Chart not found."}
        # Check for week existence
        week_info = self.weeks.get(week_start_date)
        if week_info is None:
            return {"success": False, "error": "Week not found."}

        if (chart_id, week_start_date) in self._finalized_chart_weeks:
            is_finalized = True
        elif isinstance(week_info.get("finalized_by_chart"), dict):
            is_finalized = bool(week_info["finalized_by_chart"].get(chart_id, False))
        elif "finalized" in week_info:
            is_finalized = bool(week_info.get("finalized"))
        elif isinstance(self._chart_entry_finalized_default, bool):
            is_finalized = self._chart_entry_finalized_default
        else:
            is_finalized = False
        return {"success": True, "data": is_finalized}

    def get_all_weeks(self) -> dict:
        """
        Retrieve all week periods from the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[WeekInfo]  # List of all weeks' information (may be empty)
            }

        Notes:
            - No parameters: retrieves all weeks as-is. Does not sort or filter.
            - If needed, sorting/filtering parameters could be added later.
            - Returns empty list if no weeks are found.
        """
        all_weeks = list(self.weeks.values())
        return {"success": True, "data": all_weeks}

    def get_charts_by_type(self, chart_type: str) -> dict:
        """
        List all charts that match a specified chart_type.

        Args:
            chart_type (str): The chart type (e.g., "Songs", "Albums", etc.) to filter charts by.

        Returns:
            dict: {
                "success": True,
                "data": List[ChartInfo]  # List of charts matching the chart_type (may be empty)
            }

        Notes:
            - Returns an empty list if no charts have the specified chart_type.
        """
        if not isinstance(chart_type, str) or not chart_type:
            return { "success": False, "error": "Invalid chart_type parameter" }

        result = [
            chart_info for chart_info in self.charts.values()
            if chart_info.get("chart_type") == chart_type
        ]
        return { "success": True, "data": result }

    def add_chart_entry(
        self, 
        chart_id: str, 
        song_id: str, 
        week_start_date: str, 
        position: int
    ) -> dict:
        """
        Insert a new chart entry for a specific chart_id, song_id, and week_start_date with the given position.

        Args:
            chart_id (str): ID of the chart
            song_id (str): ID of the song
            week_start_date (str): Start date of the week for entry (must exist and not yet be finalized for this chart)
            position (int): Desired ranking position (must be unique within chart/week)

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Chart entry added for song <song_id> to chart <chart_id> at position <position> for week <week_start_date>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <Error description>
                    }

        Constraints enforced:
            - chart_id, song_id, week_start_date must all be valid and exist.
            - week must not already be finalized for the specified chart.
            - Only one entry for (chart_id, song_id, week_start_date)
            - Only one entry per position within (chart_id, week_start_date)
        """
        # Check Chart exists
        if chart_id not in self.charts:
            return { "success": False, "error": "Chart does not exist" }
        # Check Song exists
        if song_id not in self.songs:
            return { "success": False, "error": "Song does not exist" }
        # Check Week exists
        if week_start_date not in self.weeks:
            return { "success": False, "error": "Week does not exist" }
        # Chart entries may only be edited before the chart/week is finalized.
        is_finalized_result = self.is_chart_entry_finalized(chart_id, week_start_date)
        if not is_finalized_result.get("success", False):
            return {"success": False, "error": is_finalized_result.get("error", "Finalization check failed")}
        if is_finalized_result.get("data", False):
            return { "success": False, "error": "Week data for this chart is already finalized" }
        # Check song not already present in this chart/week
        for entry in self.chart_entries:
            if (
                entry["chart_id"] == chart_id and
                entry["week_start_date"] == week_start_date
            ):
                if entry["song_id"] == song_id:
                    return { "success": False, "error": "Song is already present on this chart for this week" }
                if entry["position"] == position:
                    return { "success": False, "error": f"Position {position} already taken for this chart and week" }
        # Passed: Add entry
        new_entry = {
            "chart_id": chart_id,
            "song_id": song_id,
            "week_start_date": week_start_date,
            "position": position
        }
        self.chart_entries.append(new_entry)
        return {
            "success": True,
            "message": f"Chart entry added for song {song_id} to chart {chart_id} at position {position} for week {week_start_date}"
        }

    def remove_chart_entry(self, chart_id: str, song_id: str, week_start_date: str) -> dict:
        """
        Delete an existing chart entry from the system.

        Args:
            chart_id (str): The ID of the chart.
            song_id (str): The ID of the song.
            week_start_date (str): The start date of the chart week.

        Returns:
            dict: {
                "success": True,
                "message": "Chart entry removed successfully."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }
        
        Constraints:
            - ChartEntry must exist (matching all three fields).
            - No effect if linked Song, Chart, or Week missing after deletion.
        """
        found = False
        is_finalized_result = self.is_chart_entry_finalized(chart_id, week_start_date)
        if not is_finalized_result.get("success", False):
            return {"success": False, "error": is_finalized_result.get("error", "Finalization check failed")}
        if is_finalized_result.get("data", False):
            return {"success": False, "error": "Cannot remove chart entry after this chart week has been finalized."}
        for idx, entry in enumerate(self.chart_entries):
            if (
                entry["chart_id"] == chart_id and
                entry["song_id"] == song_id and
                entry["week_start_date"] == week_start_date
            ):
                found = True
                del self.chart_entries[idx]
                return { "success": True, "message": "Chart entry removed successfully." }
        return { "success": False, "error": "Chart entry not found." }

    def update_chart_entry_position(self, chart_id: str, song_id: str, week_start_date: str, new_position: int) -> dict:
        """
        Change the chart position (ranking) of a specific song on a chart for a specific week.

        Args:
            chart_id (str): The chart identifier.
            song_id (str): The song identifier.
            week_start_date (str): The start date of the week (e.g., '2023-03-13').
            new_position (int): The new ranking position to assign.

        Returns:
            dict:
                - On success: { "success": True, "message": "Chart entry position updated." }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Entry (chart_id, song_id, week_start_date) must exist.
            - New position must not already be taken within (chart_id, week_start_date).
            - Positions must be unique within each chart and week.
            - Each song can appear at most once on each chart/week.
        """
        # Find the target chart entry
        is_finalized_result = self.is_chart_entry_finalized(chart_id, week_start_date)
        if not is_finalized_result.get("success", False):
            return {"success": False, "error": is_finalized_result.get("error", "Finalization check failed")}
        if is_finalized_result.get("data", False):
            return {"success": False, "error": "Cannot update positions after this chart week has been finalized."}

        found = False
        for entry in self.chart_entries:
            if (entry["chart_id"] == chart_id and
                entry["song_id"] == song_id and
                entry["week_start_date"] == week_start_date):
                found = True
                target_entry = entry
                break
        if not found:
            return { "success": False, "error": "Chart entry not found for the given chart, song, and week." }
    
        # Check uniqueness of position (within same chart and week, excluding the current entry)
        for entry in self.chart_entries:
            if (entry["chart_id"] == chart_id and
                entry["week_start_date"] == week_start_date and
                entry["position"] == new_position and
                not (entry["song_id"] == song_id)):
                return { "success": False, "error": f"Position {new_position} is already occupied on this chart and week." }
    
        # Optionally, check that the song, chart, and week exist (not strictly necessary if chart entry exists, but extra validation)
        if chart_id not in self.charts:
            return { "success": False, "error": "Chart does not exist." }
        if song_id not in self.songs:
            return { "success": False, "error": "Song does not exist." }
        if week_start_date not in self.weeks:
            return { "success": False, "error": "Week does not exist." }
    
        # Update the position
        target_entry["position"] = new_position
    
        return { "success": True, "message": "Chart entry position updated." }

    def finalize_chart_entries_for_week(self, chart_id: str, week_start_date: str) -> dict:
        """
        Mark all chart entries for a specific chart and week as finalized.

        Args:
            chart_id (str): The ID of the chart.
            week_start_date (str): The start date string of the week.

        Returns:
            dict: {
                "success": True,
                "message": "Chart entries for chart <chart_id> in week <week_start_date> finalized.",
            }
            or
            {
                "success": False,
                "error": "<reason>",
            }

        Constraints:
            - chart_id must refer to an existing chart.
            - week_start_date must refer to an existing week.
            - Finalization is tracked per chart/week pair.
            - After finalization, add/remove/update operations for that chart/week are no longer allowed.
        """
        if chart_id not in self.charts:
            return {"success": False, "error": f"Chart with id '{chart_id}' does not exist."}
        if week_start_date not in self.weeks:
            return {"success": False, "error": f"Week with start date '{week_start_date}' does not exist."}

        entries_found = False
        for entry in self.chart_entries:
            if entry["chart_id"] == chart_id and entry["week_start_date"] == week_start_date:
                entry["finalized"] = True
                entries_found = True
        self._finalized_chart_weeks.add((chart_id, week_start_date))
        finalized_by_chart = self.weeks[week_start_date].setdefault("finalized_by_chart", {})
        if isinstance(finalized_by_chart, dict):
            finalized_by_chart[chart_id] = True

        # Note: Even if none found, return success ("0 entries finalized") as it's not an error.
        return {
            "success": True,
            "message": f"Chart entries for chart '{chart_id}' in week '{week_start_date}' finalized."
        }

    def add_song(
        self,
        song_id: str,
        title: str,
        release_date: str,
        artist_ids: list,
        genre: str
    ) -> dict:
        """
        Insert a new song and its metadata into the system.

        Args:
            song_id (str): Unique identifier for the song.
            title (str): Song title.
            release_date (str): The song's release date (string format).
            artist_ids (List[str]): List of associated artist IDs (must all exist).
            genre (str): Genre of the song.

        Returns:
            dict: 
                {"success": True, "message": "<song_id> added successfully"} on success, OR
                {"success": False, "error": "<reason>"} on failure.

        Constraints:
            - song_id must be unique.
            - All artist_ids must exist in the artists database.
        """
        if song_id in self.songs:
            return { "success": False, "error": "Song ID already exists" }

        missing_artists = [aid for aid in artist_ids if aid not in self.artists]
        if missing_artists:
            return { "success": False, "error": f"Artist IDs do not exist: {missing_artists}" }

        self.songs[song_id] = {
            "song_id": song_id,
            "title": title,
            "release_date": release_date,
            "artist_ids": artist_ids,
            "genre": genre,
        }

        return { "success": True, "message": f"Song '{song_id}' added successfully" }

    def remove_song(self, song_id: str) -> dict:
        """
        Delete a song by song_id and all related ChartEntry records.
    
        Args:
            song_id (str): Unique identifier of the song to remove.
    
        Returns:
            dict:
                - On success: { "success": True, "message": "Deleted song <song_id> and <N> related chart entries." }
                - On error: { "success": False, "error": "Song does not exist" }
    
        Constraints:
            - Song must exist to be removed.
            - All ChartEntry records referencing the song should also be removed for referential integrity.
        """
        if song_id not in self.songs:
            return { "success": False, "error": "Song does not exist" }
    
        # Remove the song
        del self.songs[song_id]

        # Remove all related chart entries
        original_entry_count = len(self.chart_entries)
        self.chart_entries = [
            entry for entry in self.chart_entries if entry["song_id"] != song_id
        ]
        removed_entries = original_entry_count - len(self.chart_entries)

        return {
            "success": True,
            "message": f"Deleted song {song_id} and {removed_entries} related chart entries."
        }

    def add_artist(
        self, 
        artist_id: str, 
        name: str, 
        country_of_origin: str, 
        active_date: str
    ) -> dict:
        """
        Insert a new artist into the database.

        Args:
            artist_id (str): Unique identifier for the artist (must not already exist).
            name (str): Name of the artist.
            country_of_origin (str): ISO region code where the artist originates (must exist in regions).
            active_date (str): Activity date or range for the artist.

        Returns:
            dict: {
                "success": True,
                "message": "Artist <artist_id> added."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - artist_id must be unique.
            - country_of_origin must be a valid region_code (present in self.regions).
            - All arguments are required (not empty).
        """
        # Check required fields are present/non-empty
        missing_params = []
        if not artist_id:
            missing_params.append("artist_id")
        if not name:
            missing_params.append("name")
        if not country_of_origin:
            missing_params.append("country_of_origin")
        if not active_date:
            missing_params.append("active_date")
        if missing_params:
            return {"success": False, "error": f"Missing required parameter(s): {', '.join(missing_params)}"}

        # Check artist_id uniqueness
        if artist_id in self.artists:
            return {"success": False, "error": "Artist ID already exists."}

        # Validate country_of_origin
        if country_of_origin not in self.regions:
            return {"success": False, "error": "Invalid country_of_origin."}
    
        # Add artist
        self.artists[artist_id] = {
            "artist_id": artist_id,
            "name": name,
            "country_of_origin": country_of_origin,
            "active_date": active_date
        }
        return {"success": True, "message": f"Artist {artist_id} added."}

    def add_chart(self, name: str, region: str, chart_type: str) -> dict:
        """
        Add a new chart definition to the system.

        Args:
            name (str): Name of the chart.
            region (str): Valid ISO region code for the chart (must exist in self.regions).
            chart_type (str): The chart type (e.g., "singles", "albums").

        Returns:
            dict: 
                - On success:
                    { "success": True, "message": "Chart <chart_id> added successfully" }
                - On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Region code must exist in self.regions.
            - Chart ID must be unique (no duplicate charts for same name, region, and type).
            - Charts are associated with only one region at a time.
        """
        # Validate region existence
        if region not in self.regions:
            return { "success": False, "error": "Region code does not exist" }

        # Generate a deterministic and unique chart_id
        chart_id = f"chart:{name}:{region}:{chart_type}"

        # Check uniqueness
        if chart_id in self.charts:
            return { "success": False, "error": "Chart with the same name, region, and type already exists" }

        chart_info: ChartInfo = {
            "chart_id": chart_id,
            "name": name,
            "region": region,
            "chart_type": chart_type
        }
        self.charts[chart_id] = chart_info

        return { "success": True, "message": f"Chart {chart_id} added successfully" }

    def add_region(self, region_code: str, region_name: str) -> dict:
        """
        Add a new region to the system.

        Args:
            region_code (str): The ISO country/region code for the region (must be unique and non-empty).
            region_name (str): The human-readable name for the region (must be non-empty).

        Returns:
            dict: 
                - On success: { "success": True, "message": "Region <code> added successfully." }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Region code must be unique (not already present in self.regions).
            - Both region_code and region_name must be non-empty.
        """
        if not region_code or not region_name:
            return { "success": False, "error": "Region code and name are required." }
        if region_code in self.regions:
            return { "success": False, "error": "Region code already exists." }

        self.regions[region_code] = {
            "region_code": region_code,
            "region_name": region_name,
        }
        return { "success": True, "message": f"Region {region_code} added successfully." }

    def add_week(self, week_start_date: str, week_end_date: str) -> dict:
        """
        Add a new week record to the system.

        Args:
            week_start_date (str): The ISO-formatted start date for the week (unique).
            week_end_date (str): The ISO-formatted end date for the week.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Week <start> - <end> added successfully."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - week_start_date must be unique (not already present in self.weeks).
            - week_start_date and week_end_date must not be empty.
            - Optionally, week_start_date should not be after week_end_date.
        """
        if not week_start_date or not week_end_date:
            return { "success": False, "error": "Week start and end date must not be empty." }
        if week_start_date in self.weeks:
            return { "success": False, "error": "Week with this start date already exists." }
        # Optional: Basic check for ordering (assuming string ISO dates for lex order)
        if week_start_date > week_end_date:
            return { "success": False, "error": "Week start date cannot be after end date." }
        self.weeks[week_start_date] = {
            "week_start_date": week_start_date,
            "week_end_date": week_end_date,
        }
        return {
            "success": True,
            "message": f"Week {week_start_date} - {week_end_date} added successfully."
        }

    def update_song_metadata(
        self,
        song_id: str,
        title: str = None,
        artist_ids: list = None,
        genre: str = None,
        release_date: str = None
    ) -> dict:
        """
        Edit metadata of an existing song.

        Args:
            song_id (str): The unique ID of the song to update.
            title (str, optional): New song title.
            artist_ids (List[str], optional): New list of artist IDs (all must exist).
            genre (str, optional): New genre string.
            release_date (str, optional): New release date string.

        Returns:
            dict: {
                "success": True,
                "message": "Song metadata updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The song must exist.
            - If artist_ids is provided, all must correspond to an existing artist.
            - At least one field to update must be provided.
            - Only valid SongInfo fields are updated.
        """
        if song_id not in self.songs:
            return { "success": False, "error": "Song not found" }

        if (
            title is None
            and artist_ids is None
            and genre is None
            and release_date is None
        ):
            return {"success": False, "error": "No metadata fields to update provided"}

        song = self.songs[song_id]
        updates = []

        if title is not None:
            song["title"] = title
            updates.append("title")

        if artist_ids is not None:
            if not isinstance(artist_ids, list):
                return {"success": False, "error": "artist_ids must be a list"}
            invalid_artists = [aid for aid in artist_ids if aid not in self.artists]
            if invalid_artists:
                return {
                    "success": False,
                    "error": f"Invalid artist id(s): {', '.join(invalid_artists)}"
                }
            song["artist_ids"] = artist_ids
            updates.append("artist_ids")

        if genre is not None:
            song["genre"] = genre
            updates.append("genre")

        if release_date is not None:
            song["release_date"] = release_date
            updates.append("release_date")

        self.songs[song_id] = song

        return {
            "success": True,
            "message": f"Song metadata updated: {', '.join(updates)}"
        }

    def update_artist_metadata(
        self,
        artist_id: str,
        name: str = None,
        country_of_origin: str = None,
        active_date: str = None
    ) -> dict:
        """
        Edit metadata fields (name, country_of_origin, active_date) of an existing artist.

        Args:
            artist_id (str): Unique identifier of the artist to update.
            name (str, optional): New name for the artist.
            country_of_origin (str, optional): New country of origin.
            active_date (str, optional): New active date or period.

        Returns:
            dict: {
                "success": True,
                "message": "Artist metadata updated successfully."
            } 
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The artist with the given artist_id must exist.
            - At least one valid field must be provided for update.
            - Cannot update artist_id itself.
        """
        if artist_id not in self.artists:
            return { "success": False, "error": "Artist ID does not exist." }

        updatable_fields = ["name", "country_of_origin", "active_date"]
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if country_of_origin is not None:
            update_data["country_of_origin"] = country_of_origin
        if active_date is not None:
            update_data["active_date"] = active_date

        if not update_data:
            return { "success": False, "error": "No metadata fields provided for update." }

        # Perform the update
        artist_info = self.artists[artist_id]
        for field, value in update_data.items():
            artist_info[field] = value

        return { "success": True, "message": "Artist metadata updated successfully." }


class MusicChartTrackingDatabase(BaseEnv):
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
            if key == "is_chart_entry_finalized":
                normalized = None
                if isinstance(value, bool):
                    normalized = value
                elif isinstance(value, str):
                    lowered = value.strip().lower()
                    if lowered == "true":
                        normalized = True
                    elif lowered == "false":
                        normalized = False
                env._chart_entry_finalized_default = normalized
                continue
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

    def get_chart_by_name_and_region(self, **kwargs):
        return self._call_inner_tool('get_chart_by_name_and_region', kwargs)

    def get_charts_by_region(self, **kwargs):
        return self._call_inner_tool('get_charts_by_region', kwargs)

    def get_region_by_name(self, **kwargs):
        return self._call_inner_tool('get_region_by_name', kwargs)

    def get_weeks_by_start_dates(self, **kwargs):
        return self._call_inner_tool('get_weeks_by_start_dates', kwargs)

    def get_chart_entries_for_chart_and_week(self, **kwargs):
        return self._call_inner_tool('get_chart_entries_for_chart_and_week', kwargs)

    def get_song_info(self, **kwargs):
        return self._call_inner_tool('get_song_info', kwargs)

    def get_artist_info(self, **kwargs):
        return self._call_inner_tool('get_artist_info', kwargs)

    def get_chart_entry(self, **kwargs):
        return self._call_inner_tool('get_chart_entry', kwargs)

    def list_songs_on_chart_for_week(self, **kwargs):
        return self._call_inner_tool('list_songs_on_chart_for_week', kwargs)

    def is_chart_entry_finalized(self, **kwargs):
        return self._call_inner_tool('is_chart_entry_finalized', kwargs)

    def get_all_weeks(self, **kwargs):
        return self._call_inner_tool('get_all_weeks', kwargs)

    def get_charts_by_type(self, **kwargs):
        return self._call_inner_tool('get_charts_by_type', kwargs)

    def add_chart_entry(self, **kwargs):
        return self._call_inner_tool('add_chart_entry', kwargs)

    def remove_chart_entry(self, **kwargs):
        return self._call_inner_tool('remove_chart_entry', kwargs)

    def update_chart_entry_position(self, **kwargs):
        return self._call_inner_tool('update_chart_entry_position', kwargs)

    def finalize_chart_entries_for_week(self, **kwargs):
        return self._call_inner_tool('finalize_chart_entries_for_week', kwargs)

    def add_song(self, **kwargs):
        return self._call_inner_tool('add_song', kwargs)

    def remove_song(self, **kwargs):
        return self._call_inner_tool('remove_song', kwargs)

    def add_artist(self, **kwargs):
        return self._call_inner_tool('add_artist', kwargs)

    def add_chart(self, **kwargs):
        return self._call_inner_tool('add_chart', kwargs)

    def add_region(self, **kwargs):
        return self._call_inner_tool('add_region', kwargs)

    def add_week(self, **kwargs):
        return self._call_inner_tool('add_week', kwargs)

    def update_song_metadata(self, **kwargs):
        return self._call_inner_tool('update_song_metadata', kwargs)

    def update_artist_metadata(self, **kwargs):
        return self._call_inner_tool('update_artist_metadata', kwargs)
