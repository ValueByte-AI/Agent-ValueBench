# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime, timedelta, timezone
from typing import Optional
from typing import List, Dict, Any



class CountryInfo(TypedDict):
    country_id: str
    country_code: str
    country_nam: str  # Original spelling retained for fidelity

class ProvinceInfo(TypedDict):
    province_id: str
    province_code: str
    province_name: str
    country_id: str
    last_updated: str  # ISO datetime string

class DistrictInfo(TypedDict):
    district_id: str
    district_code: str
    district_name: str
    province_id: str
    last_updated: str  # ISO datetime string

class _GeneratedEnvImpl:
    def __init__(self):
        # Countries: {country_id: CountryInfo}
        self.countries: Dict[str, CountryInfo] = {}

        # Provinces: {province_id: ProvinceInfo}
        self.provinces: Dict[str, ProvinceInfo] = {}

        # Districts: {district_id: DistrictInfo}
        self.districts: Dict[str, DistrictInfo] = {}

        # State space mapping:
        # - countries → Country: country_id, country_code, country_nam
        # - provinces → Province: province_id, province_code, province_name, country_id, last_updated
        # - districts → District: district_id, district_code, district_name, province_id, last_updated

        # Constraints:
        # - Each province must be associated with exactly one country via country_id.
        # - Each district must be associated with exactly one province via province_id.
        # - Province and district codes and IDs must be unique within their parent scope.
        # - Updates to provinces or districts must update the last_updated field for synchronization.
        self._benchmark_clock: Optional[datetime] = None

    @staticmethod
    def _parse_timestamp(raw: Any) -> Optional[datetime]:
        if not isinstance(raw, str) or not raw.strip():
            return None
        text = raw.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except Exception:
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    @staticmethod
    def _format_timestamp(ts: datetime) -> str:
        return ts.replace(microsecond=0).isoformat() + "Z"

    def _ensure_benchmark_clock(self) -> None:
        if self._benchmark_clock is not None:
            return
        candidates = []
        for collection_name in ("provinces", "districts"):
            collection = getattr(self, collection_name, {})
            if not isinstance(collection, dict):
                continue
            for item in collection.values():
                if isinstance(item, dict):
                    parsed = self._parse_timestamp(item.get("last_updated"))
                    if parsed is not None:
                        candidates.append(parsed)
        self._benchmark_clock = max(candidates) if candidates else datetime(2023, 1, 1, 0, 0, 0)

    def _next_benchmark_timestamp(self) -> str:
        self._ensure_benchmark_clock()
        self._benchmark_clock = self._benchmark_clock + timedelta(seconds=1)
        return self._format_timestamp(self._benchmark_clock)

    def get_country_by_name(self, country_nam: str) -> dict:
        """
        Retrieve information about a country using its country_nam.

        Args:
            country_nam (str): The exact name of the country to look up (case-sensitive match).

        Returns:
            dict: {
                "success": True,
                "data": CountryInfo  # The complete country information record
            }
            or
            {
                "success": False,
                "error": str  # Reason why the country could not be found
            }
        """
        for country in self.countries.values():
            if country["country_nam"] == country_nam:
                return {"success": True, "data": country}
        return {"success": False, "error": f'Country with name "{country_nam}" not found'}

    def get_country_by_code(self, country_code: str) -> dict:
        """
        Retrieve information about a country using its country_code.

        Args:
            country_code (str): The unique country code to search for.

        Returns:
            dict: {
                "success": True,
                "data": CountryInfo
            }
            or
            {
                "success": False,
                "error": str  # reason ("Country code not found")
            }

        Constraints:
            - country_code must uniquely identify a country.
            - If country code does not exist, return an error.
        """
        for country in self.countries.values():
            if country["country_code"] == country_code:
                return { "success": True, "data": country }
        return { "success": False, "error": "Country code not found" }

    def get_provinces_by_country_id(self, country_id: str) -> dict:
        """
        List all provinces associated with a given country_id.

        Args:
            country_id (str): The unique identifier for the country.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ProvinceInfo]  # List may be empty if no provinces
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Error reason, e.g. "Country does not exist"
                    }

        Constraints:
            - Province.country_id must match the argument.
            - country_id must exist in the system.
        """
        if country_id not in self.countries:
            return { "success": False, "error": "Country does not exist" }

        provinces = [
            province for province in self.provinces.values()
            if province["country_id"] == country_id
        ]
        return { "success": True, "data": provinces }

    def get_province_by_id(self, province_id: str) -> dict:
        """
        Retrieve province details by province_id.

        Args:
            province_id (str): Unique identifier for the province.

        Returns:
            dict: {
                "success": True,
                "data": ProvinceInfo  # Province metadata if found
            }
            or
            {
                "success": False,
                "error": str  # If not found, returns descriptive error message
            }
    
        Constraints:
            - province_id must exist in the system.
        """
        province = self.provinces.get(province_id)
        if province is None:
            return {"success": False, "error": "Province with given province_id does not exist"}
        return {"success": True, "data": province}

    def get_province_by_code(self, province_code: str) -> dict:
        """
        Retrieve province details using the specified province_code.

        Args:
            province_code (str): The code of the province to retrieve.

        Returns:
            dict:
              - If found: {"success": True, "data": ProvinceInfo}
              - If not found: {"success": False, "error": "Province with the given code does not exist"}

        Constraints:
            - province_code is assumed to be unique among all provinces.
        """
        for province in self.provinces.values():
            if province["province_code"] == province_code:
                return {"success": True, "data": province}
        return {"success": False, "error": "Province with the given code does not exist"}

    def get_districts_by_province_id(self, province_id: str) -> dict:
        """
        Retrieve all districts belonging to the specified province_id.

        Args:
            province_id (str): The province's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[DistrictInfo]  # List of DistrictInfo dicts (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
        - The provided province_id must exist in the system.
        """
        if province_id not in self.provinces:
            return {"success": False, "error": "Province not found"}
    
        districts = [
            d for d in self.districts.values()
            if d["province_id"] == province_id
        ]
        return {"success": True, "data": districts}

    def get_district_by_id(self, district_id: str) -> dict:
        """
        Retrieve details for a district specified by its unique district_id.

        Args:
            district_id (str): The unique identifier of the district.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": DistrictInfo  # The dictionary of district details
                }
            On failure:
                {
                    "success": False,
                    "error": str  # Reason, e.g. 'District not found'
                }

        Constraints:
            - The district_id must exist in the system.
        """
        if district_id not in self.districts:
            return { "success": False, "error": "District not found" }

        return { "success": True, "data": self.districts[district_id] }

    def get_district_by_code(self, district_code: str) -> dict:
        """
        Retrieve district details by district_code.

        Args:
            district_code (str): The unique code of the district.

        Returns:
            dict: {
                "success": True,
                "data": DistrictInfo,  # All info for the found district
            }
            or
            {
                "success": False,
                "error": "District code not found"
            }

        Constraints:
            - Assumes district_code is unique within the dataset.
        """
        for district in self.districts.values():
            if district["district_code"] == district_code:
                return { "success": True, "data": district }
        return { "success": False, "error": "District code not found" }

    def list_all_countries(self) -> dict:
        """
        Retrieve the list of all countries in the GIS system.

        Returns:
            dict: {
                "success": True,
                "data": List[CountryInfo]  # List of all countries (may be empty)
            }

        Constraints:
            - None (read-only operation).
        """
        result = list(self.countries.values())
        return { "success": True, "data": result }

    def list_provinces(self) -> dict:
        """
        Retrieve the list of all provinces in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProvinceInfo],  # List of all ProvinceInfo dicts, or empty list if none
            }

        Constraints:
            - None specific for listing; all provinces should be returned.
        """
        provinces_list = list(self.provinces.values())
        return {"success": True, "data": provinces_list}

    def list_districts(self) -> dict:
        """
        Retrieve the list of all districts present in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[DistrictInfo]  # All district records (possibly empty)
            }

        Constraints:
            - No constraints/validation needed; all present districts are returned.
        """
        data = list(self.districts.values())
        return { "success": True, "data": data }

    def add_country(self, country_id: str, country_code: str, country_nam: str) -> dict:
        """
        Add a new country to the system.

        Args:
            country_id (str): Unique identifier for the new country.
            country_code (str): Unique code for the new country.
            country_nam (str): Name for the new country (spelling as per spec).

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Country <country_nam> added with ID <country_id>."
                }
                  On failure,
                {
                    "success": False,
                    "error": str  # Description of the error (e.g. duplicate id or code)
                }
        Constraints:
            - country_id must be globally unique.
            - country_code must be globally unique.
        """
        # Uniqueness check: ID
        if country_id in self.countries:
            return {"success": False, "error": f"country_id '{country_id}' already exists."}

        # Uniqueness check: Code
        for cinfo in self.countries.values():
            if cinfo["country_code"] == country_code:
                return {"success": False, "error": f"country_code '{country_code}' already exists."}

        # Add country
        country_info = {
            "country_id": country_id,
            "country_code": country_code,
            "country_nam": country_nam
        }
        self.countries[country_id] = country_info

        return {
            "success": True,
            "message": f"Country {country_nam} added with ID {country_id}."
        }

    def update_country(
        self, 
        country_id: str, 
        country_code: str = None, 
        country_nam: str = None
    ) -> dict:
        """
        Update details of an existing country.
    
        Args:
            country_id (str): The unique ID of the country to update (required).
            country_code (str, optional): New country code, must be unique if provided.
            country_nam (str, optional): New country name if provided.
    
        Returns:
            dict: 
                On success: { "success": True, "message": "Country updated successfully." }
                On failure: { "success": False, "error": "reason" }
    
        Constraints:
            - country_id must exist in self.countries.
            - If country_code is provided, it must be unique among all countries.
            - At least one field (country_code or country_nam) must be provided.
        """
        if country_id not in self.countries:
            return { "success": False, "error": "Country not found." }

        if country_code is None and country_nam is None:
            return { "success": False, "error": "No update data provided." }

        # Uniqueness check for code if updating
        if country_code is not None:
            for cid, cinfo in self.countries.items():
                if cid != country_id and cinfo["country_code"] == country_code:
                    return { "success": False, "error": "Country code must be unique." }

        updated = False
        if country_code is not None:
            self.countries[country_id]["country_code"] = country_code
            updated = True
        if country_nam is not None:
            self.countries[country_id]["country_nam"] = country_nam
            updated = True

        if updated:
            return { "success": True, "message": "Country updated successfully." }
        else:
            return { "success": False, "error": "Nothing was updated." }

    def delete_country(self, country_id: str) -> dict:
        """
        Remove a country by its country_id, ensuring all associated provinces and districts
        are also removed for referential integrity.

        Args:
            country_id (str): The unique identifier of the country to delete.

        Returns:
            dict: Success or failure information.
                On success:
                {
                    "success": True,
                    "message": "Country (<country_id>) and all associated provinces and districts deleted."
                }
                On failure:
                {
                    "success": False,
                    "error": "Country not found."
                }

        Constraints:
            - All provinces with this country_id and all their districts are removed.
            - No references are left dangling.
        """
        if country_id not in self.countries:
            return { "success": False, "error": "Country not found." }
    
        # Find all provinces of this country
        provinces_to_delete = [prov_id for prov_id, prov in self.provinces.items() if prov['country_id'] == country_id]
        districts_deleted = 0
        provinces_deleted = 0
        # For each such province, remove its districts first
        for province_id in provinces_to_delete:
            districts_to_delete = [dist_id for dist_id, dist in self.districts.items() if dist['province_id'] == province_id]
            for district_id in districts_to_delete:
                del self.districts[district_id]
                districts_deleted += 1
            # Remove the province
            del self.provinces[province_id]
            provinces_deleted += 1

        # Remove the country itself
        del self.countries[country_id]

        return {
            "success": True,
            "message": f"Country ({country_id}) and all its {provinces_deleted} provinces and {districts_deleted} districts deleted."
        }


    def add_province(self, province_id: str, province_code: str, province_name: str, country_id: str) -> dict:
        """
        Add a new province under a specific country.

        Args:
            province_id (str): Unique identifier for the new province.
            province_code (str): Province code (unique under the country).
            province_name (str): Name of the province.
            country_id (str): ID of the country this province belongs to.

        Returns:
            dict: {
                "success": True,
                "message": "Province added successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - country_id must refer to an existing country.
            - province_id and province_code must be unique within the specified country.
            - last_updated set to the next controlled benchmark timestamp.
        """
        # Input validation
        if not (province_id and province_code and province_name and country_id):
            return {"success": False, "error": "All fields must be provided and non-empty"}

        # 1. Check if country exists
        if country_id not in self.countries:
            return {"success": False, "error": "Specified country does not exist"}

        # 2. Prevent overwriting an existing province keyed by province_id
        if province_id in self.provinces:
            return {"success": False, "error": "province_id already exists"}

        # 3. Check uniqueness of province_code under the country
        for p in self.provinces.values():
            if p["country_id"] == country_id:
                if p["province_code"] == province_code:
                    return {"success": False, "error": "province_code already exists under this country"}

        # 4. Add province
        now_iso = self._next_benchmark_timestamp()
        province_info = {
            "province_id": province_id,
            "province_code": province_code,
            "province_name": province_name,
            "country_id": country_id,
            "last_updated": now_iso,
        }
        self.provinces[province_id] = province_info

        return {"success": True, "message": "Province added successfully"}


    def update_province(
        self,
        province_id: str,
        province_name: Optional[str] = None,
        province_code: Optional[str] = None,
        country_id: Optional[str] = None
    ) -> dict:
        """
        Update details of a province: name, code, and/or country association.
        Enforces uniqueness of province_code, existence of province and referenced country,
        and ensures last_updated is set to the operation timestamp (ISO format).
    
        Args:
            province_id (str): The unique identifier for the province to update.
            province_name (str, optional): The new name for the province.
            province_code (str, optional): The new code for the province (must be unique).
            country_id (str, optional): The new country association (must reference existing country).
        
        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Province updated successfully." }
                On failure:
                    { "success": False, "error": <str describing reason> }
        """
        # 1. Province existence
        if province_id not in self.provinces:
            return {"success": False, "error": "Province not found"}

        province = self.provinces[province_id]

        # 2. Uniqueness of province_code, if updating
        if province_code is not None:
            for pid, pinfo in self.provinces.items():
                if (
                    pid != province_id
                    and pinfo["province_code"] == province_code
                ):
                    return {"success": False, "error": "Province code must be unique"}

        # 3. country_id must exist if changing
        if country_id is not None:
            if country_id not in self.countries:
                return {"success": False, "error": "Referenced country does not exist"}

        # 4. Update fields
        if province_name is not None:
            province["province_name"] = province_name
        if province_code is not None:
            province["province_code"] = province_code
        if country_id is not None:
            province["country_id"] = country_id

        # 5. Update last_updated using the controlled benchmark clock
        province["last_updated"] = self._next_benchmark_timestamp()

        # 6. Save back (not strictly necessary for dict references, but explicit)
        self.provinces[province_id] = province

        return {"success": True, "message": "Province updated successfully."}

    def delete_province(self, province_id: str) -> dict:
        """
        Delete a province and all its districts, maintaining a valid administrative hierarchy.

        Args:
            province_id (str): The unique identifier of the province to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Province <province_id> and all its districts deleted"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - If the province does not exist, no action is taken and failure is returned.
            - Deleting a province removes all districts whose province_id matches.
        """
        if province_id not in self.provinces:
            return {"success": False, "error": "Province not found"}

        # Remove all districts with this province_id
        district_ids_to_delete = [
            district_id
            for district_id, district in self.districts.items()
            if district["province_id"] == province_id
        ]
        for district_id in district_ids_to_delete:
            del self.districts[district_id]

        # Remove the province itself
        del self.provinces[province_id]

        return {
            "success": True,
            "message": f"Province {province_id} and all its districts deleted"
        }


    def add_district(
        self,
        district_id: str,
        district_code: str,
        district_name: str,
        province_id: str
    ) -> dict:
        """
        Add a new district under the given province.
    
        Args:
            district_id (str): Unique identifier for the district.
            district_code (str): Unique district code (must be unique within its province).
            district_name (str): Name of the district.
            province_id (str): ID of the province to associate with.

        Returns:
            dict: {
                "success": True,
                "message": "District added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Province must exist.
            - district_id must be unique among all districts.
            - district_code must be unique within the given province (among districts in that province).
            - Sets last_updated to the next controlled benchmark timestamp.
        """
        # Check if parent province exists
        if province_id not in self.provinces:
            return { "success": False, "error": "Province does not exist." }
    
        # Check for duplicate district_id
        if district_id in self.districts:
            return { "success": False, "error": "district_id already exists." }
    
        # Check for duplicate district_code within this province
        for d in self.districts.values():
            if d["province_id"] == province_id and d["district_code"] == district_code:
                return { "success": False, "error": "district_code already exists in this province." }
    
        # Prepare new district info
        now_iso = self._next_benchmark_timestamp()
        new_district = {
            "district_id": district_id,
            "district_code": district_code,
            "district_name": district_name,
            "province_id": province_id,
            "last_updated": now_iso,
        }

        # Add to districts
        self.districts[district_id] = new_district

        return { "success": True, "message": "District added successfully." }


    def update_district(
        self,
        district_id: str,
        district_name: Optional[str] = None,
        district_code: Optional[str] = None,
        province_id: Optional[str] = None
    ) -> dict:
        """
        Update details of a district (name, code, association to province), enforcing code/ID uniqueness within the 
        new parent province and integrity of associations; also updates 'last_updated' synchronization timestamp.

        Args:
            district_id (str): The unique identifier of the district to update.
            district_name (Optional[str]): New name for the district (optional).
            district_code (Optional[str]): New code for the district (optional; must be unique within new province).
            province_id (Optional[str]): New province association for the district (optional; must exist).

        Returns:
            dict: 
              - On success: { "success": True, "message": "District updated successfully." }
              - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The district must exist.
            - If province_id changes, the new province_id must exist.
            - district_code must be unique within the target province.
            - On any update, 'last_updated' is updated to the next controlled benchmark timestamp.
        """
        # Check the district exists
        district = self.districts.get(district_id)
        if not district:
            return {"success": False, "error": "District does not exist."}
    
        # Determine target province for validation
        target_province_id = province_id if province_id is not None else district["province_id"]

        # If province is changed, check new province exists
        if target_province_id not in self.provinces:
            return {"success": False, "error": "Target province does not exist."}
    
        # If district_code is changing or province_id is changing, enforce new district_code uniqueness
        code_to_check = district_code if district_code is not None else district["district_code"]
        # Uniqueness means: no other district with same code in the target province (excluding self)
        for other in self.districts.values():
            if (
                other["district_id"] != district_id and
                other["province_id"] == target_province_id and
                other["district_code"] == code_to_check
            ):
                return {
                    "success": False, 
                    "error": "District code already exists in the target province."
                }
    
        # Apply updates
        if district_name is not None:
            district["district_name"] = district_name
        if district_code is not None:
            district["district_code"] = district_code
        if province_id is not None:
            district["province_id"] = province_id
        # Always update last_updated using the controlled benchmark clock
        district["last_updated"] = self._next_benchmark_timestamp()

        self.districts[district_id] = district  # Redundant for mutable dict, but ensures state is synchronized

        return {
            "success": True,
            "message": "District updated successfully."
        }

    def delete_district(self, district_id: str) -> dict:
        """
        Removes a district from the system.

        Args:
            district_id (str): The unique identifier of the district to be deleted.

        Returns:
            dict:
                Success: { "success": True, "message": "District {district_id} deleted successfully" }
                Failure: { "success": False, "error": "District not found" }

        Constraints:
            - The district_id must exist in the system for deletion.
            - Deletion is immediate and permanent.
            - This operation does not affect provinces or countries.
        """
        if district_id not in self.districts:
            return { "success": False, "error": "District not found" }

        del self.districts[district_id]
        return { "success": True, "message": f"District {district_id} deleted successfully" }


    def synchronize_last_updated(self, entity_type: str, ids: List[str]) -> Dict[str, Any]:
        """
        Manually refresh the 'last_updated' field for provinces or districts using the controlled benchmark clock.

        Args:
            entity_type (str): Type of the entity to update, either 'province' or 'district'.
            ids (List[str]): List of province_ids or district_ids to synchronize.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "last_updated successfully synchronized for N {entity_type}s."
                }
                or
                {
                    "success": False,
                    "error": "reason"
                }
    
        Constraints:
            - entity_type must be 'province' or 'district'.
            - IDs must exist in the corresponding collection.
            - If an ID is not found, it will be ignored and the count will be for actually-updated rows.
            - On empty ID input list, returns success with count 0.
        """
        if entity_type not in {"province", "district"}:
            return {
                "success": False,
                "error": "Invalid entity_type. Must be 'province' or 'district'."
            }
        if not isinstance(ids, list):
            return {
                "success": False,
                "error": "ids must be a list of strings."
            }
        now = self._next_benchmark_timestamp()
        updated_count = 0
        ids_seen = set()
        for id_ in ids:
            if id_ in ids_seen:
                continue  # Prevent double updates
            ids_seen.add(id_)
            if entity_type == "province":
                if id_ in self.provinces:
                    self.provinces[id_]["last_updated"] = now
                    updated_count += 1
            elif entity_type == "district":
                if id_ in self.districts:
                    self.districts[id_]["last_updated"] = now
                    updated_count += 1

        return {
            "success": True,
            "message": f"last_updated successfully synchronized for {updated_count} {entity_type}{'s' if updated_count != 1 else ''}."
        }


class AdministrativeGIS(BaseEnv):
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

    def get_country_by_name(self, **kwargs):
        return self._call_inner_tool('get_country_by_name', kwargs)

    def get_country_by_code(self, **kwargs):
        return self._call_inner_tool('get_country_by_code', kwargs)

    def get_provinces_by_country_id(self, **kwargs):
        return self._call_inner_tool('get_provinces_by_country_id', kwargs)

    def get_province_by_id(self, **kwargs):
        return self._call_inner_tool('get_province_by_id', kwargs)

    def get_province_by_code(self, **kwargs):
        return self._call_inner_tool('get_province_by_code', kwargs)

    def get_districts_by_province_id(self, **kwargs):
        return self._call_inner_tool('get_districts_by_province_id', kwargs)

    def get_district_by_id(self, **kwargs):
        return self._call_inner_tool('get_district_by_id', kwargs)

    def get_district_by_code(self, **kwargs):
        return self._call_inner_tool('get_district_by_code', kwargs)

    def list_all_countries(self, **kwargs):
        return self._call_inner_tool('list_all_countries', kwargs)

    def list_provinces(self, **kwargs):
        return self._call_inner_tool('list_provinces', kwargs)

    def list_districts(self, **kwargs):
        return self._call_inner_tool('list_districts', kwargs)

    def add_country(self, **kwargs):
        return self._call_inner_tool('add_country', kwargs)

    def update_country(self, **kwargs):
        return self._call_inner_tool('update_country', kwargs)

    def delete_country(self, **kwargs):
        return self._call_inner_tool('delete_country', kwargs)

    def add_province(self, **kwargs):
        return self._call_inner_tool('add_province', kwargs)

    def update_province(self, **kwargs):
        return self._call_inner_tool('update_province', kwargs)

    def delete_province(self, **kwargs):
        return self._call_inner_tool('delete_province', kwargs)

    def add_district(self, **kwargs):
        return self._call_inner_tool('add_district', kwargs)

    def update_district(self, **kwargs):
        return self._call_inner_tool('update_district', kwargs)

    def delete_district(self, **kwargs):
        return self._call_inner_tool('delete_district', kwargs)

    def synchronize_last_updated(self, **kwargs):
        return self._call_inner_tool('synchronize_last_updated', kwargs)
