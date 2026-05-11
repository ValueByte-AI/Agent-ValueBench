# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import time
from typing import List, Dict, Union
import datetime



# Represents an individual publicly traded asset.
class SecurityInfo(TypedDict):
    symbol: str
    name: str
    isin: str
    cusip: str
    exchange: str

# Represents a financial regulation applicable to securities.
class RegulationInfo(TypedDict):
    regulation_id: str
    name: str
    description: str
    effective_date: str

# Represents a list mandated under a regulation (e.g., threshold list).
class ComplianceListInfo(TypedDict):
    list_id: str
    regulation_id: str
    name: str
    last_updated: str

# Represents security status on compliance lists, including membership and dates.
class ComplianceListSecurityInfo(TypedDict):
    list_id: str
    symbol: str
    added_date: str
    removed_date: str
    status: str  # e.g., 'active' or 'inactive'

class _GeneratedEnvImpl:
    def __init__(self):
        # Securities: {symbol: SecurityInfo}
        self.securities: Dict[str, SecurityInfo] = {}

        # Regulations: {regulation_id: RegulationInfo}
        self.regulations: Dict[str, RegulationInfo] = {}

        # Compliance Lists: {list_id: ComplianceListInfo}
        self.compliance_lists: Dict[str, ComplianceListInfo] = {}

        # Compliance List Securities: {list_id: {symbol: ComplianceListSecurityInfo}}
        self.compliance_list_securities: Dict[str, Dict[str, ComplianceListSecurityInfo]] = {}

        # Constraints:
        # - Each security can belong to zero or more compliance lists.
        # - Each compliance list must be linked to one regulation.
        # - Compliance lists must be periodically synchronized with regulatory sources;
        #   last_updated must always reflect most recent update.
        # - Only symbols present and marked active on a compliance list at the time of query
        #   should be considered included.
        # - Regulatory references must be maintained for reporting and audit purposes.

    def get_compliance_list_by_name(self, name: str) -> dict:
        """
        Retrieve compliance list metadata and ID for the specified list name.

        Args:
            name (str): The name of the compliance list to retrieve (e.g., "Regulation SHO threshold securities list").

        Returns:
            dict: {
                "success": True,
                "data": ComplianceListInfo,  # Metadata for the matching compliance list
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g., list not found)
            }

        Constraints:
            - List name must match exactly (case-sensitive).
            - List names are assumed unique. If not, returns first found.
        """
        for compliance_list in self.compliance_lists.values():
            if compliance_list["name"] == name:
                return {"success": True, "data": compliance_list}

        return {"success": False, "error": "No compliance list found with that name"}

    def get_regulation_by_id(self, regulation_id: str) -> dict:
        """
        Retrieve regulation information for a provided regulation_id.

        Args:
            regulation_id (str): The unique identifier of the regulation.

        Returns:
            dict: 
                - On success: { "success": True, "data": RegulationInfo }
                - On failure: { "success": False, "error": str }
    
        Constraints:
            - regulation_id must exist in the system's regulations.
            - Regulatory references must be maintained accurately.
        """
        regulation = self.regulations.get(regulation_id)
        if regulation is None:
            return { "success": False, "error": "Regulation not found" }
        return { "success": True, "data": regulation }

    def get_regulation_by_name(self, regulation_name: str) -> dict:
        """
        Retrieve regulation information by its name.

        Args:
            regulation_name (str): The name of the regulation to find.

        Returns:
            dict: {
                "success": True,
                "data": RegulationInfo  # Regulation details for the first found match
            }
            or
            {
                "success": False,
                "error": str  # Description if regulation name not found
            }

        Constraints:
            - If multiple regulations match the provided name, the first match is returned.
            - Regulation names are compared case-sensitively.
        """
        for regulation in self.regulations.values():
            if regulation["name"] == regulation_name:
                return { "success": True, "data": regulation }
        return { "success": False, "error": "No regulation found with the given name" }

    def get_security_info_by_symbol(self, symbol: str) -> dict:
        """
        Retrieve details for a given security symbol (name, ISIN, CUSIP, exchange).

        Args:
            symbol (str): The security symbol to look up.

        Returns:
            dict: {
                "success": True,
                "data": SecurityInfo  # Metadata dictionary for the security symbol
            }
            or
            {
                "success": False,
                "error": str  # If security symbol is not found in the system
            }

        Constraints:
            - Each symbol is unique.
            - No list membership or regulatory relationships are checked.
        """
        security = self.securities.get(symbol)
        if security is None:
            return { "success": False, "error": "Security symbol not found" }
        return { "success": True, "data": security }

    def check_symbol_in_compliance_list(self, list_id: str, symbol: str) -> dict:
        """
        Determine if a given symbol is currently actively included ('active' status) in a specific compliance list.
        Returns membership status and membership dates.
    
        Args:
            list_id (str): ID of the compliance list.
            symbol (str): Security symbol to check.
    
        Returns:
            dict: {
                "success": True,
                "data": {
                    "active": bool,
                    "membership_info": ComplianceListSecurityInfo or None  # Details if present, else None
                }
            }
            Or:
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only symbols present and marked 'active' in the compliance list at query time are considered as included.
            - list_id and symbol must exist.
            - If symbol is not present in compliance_list_securities[list_id], membership_info is None.
        """
        if list_id not in self.compliance_lists:
            return {"success": False, "error": "Compliance list does not exist"}
        if symbol not in self.securities:
            return {"success": False, "error": "Security symbol does not exist"}
        if list_id not in self.compliance_list_securities:
            return {"success": True, "data": {"active": False, "membership_info": None}}
    
        list_symbols = self.compliance_list_securities[list_id]
        symbol_info = list_symbols.get(symbol)
        if not symbol_info:
            # Symbol not present in compliance list
            return {"success": True, "data": {"active": False, "membership_info": None}}
        else:
            # Present: check status
            is_active = (symbol_info.get("status") == "active")
            return {"success": True, "data": {"active": is_active, "membership_info": symbol_info}}

    def list_active_symbols_in_compliance_list(self, list_id: str) -> dict:
        """
        Return all symbols currently marked 'active' on a specific compliance list.

        Args:
            list_id (str): The identifier of the compliance list.

        Returns:
            dict: {
                "success": True,
                "data": List[str], # List of symbol strings marked 'active'
            }
            or
            {
                "success": False,
                "error": str # Description of the error
            }

        Constraints:
            - Only symbols present and marked 'active' on the compliance list at the time of query should be included.
            - The specified compliance list must exist.
        """

        if list_id not in self.compliance_lists:
            return { "success": False, "error": "Compliance list does not exist" }

        # Get all compliance list security mappings for this list
        symbol_map = self.compliance_list_securities.get(list_id, {})
        result = [
            symbol for symbol, info in symbol_map.items()
            if info.get("status") == "active"
        ]

        return { "success": True, "data": result }

    def get_compliance_list_last_updated(self, list_id: str) -> dict:
        """
        Get the last synchronization date for a given compliance list.

        Args:
            list_id (str): Unique identifier for the compliance list.

        Returns:
            dict:
                - success: True and data containing the last_updated string if the list exists.
                - success: False and error message if the compliance list does not exist.

        Constraints:
            - The specified compliance list must exist.
        """
        compliance_list = self.compliance_lists.get(list_id)
        if compliance_list is None:
            return {
                "success": False,
                "error": "Compliance list does not exist"
            }
        return {
            "success": True,
            "data": compliance_list["last_updated"]
        }

    def get_regulation_for_compliance_list(self, list_id: str) -> dict:
        """
        Retrieve the regulation metadata associated with a given compliance list.

        Args:
            list_id (str): Identifier for the compliance list.

        Returns:
            dict: {
                "success": True,
                "data": RegulationInfo  # Regulation metadata for given compliance list
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. compliance list or regulation not found)
            }

        Constraints:
            - The compliance list must exist.
            - The regulation linked to the compliance list must exist.
        """
        compliance_list = self.compliance_lists.get(list_id)
        if not compliance_list:
            return {
                "success": False,
                "error": "Compliance list not found"
            }

        regulation_id = compliance_list.get("regulation_id")
        regulation = self.regulations.get(regulation_id)
        if not regulation:
            return {
                "success": False,
                "error": f"Regulation with id '{regulation_id}' not found"
            }
    
        return {
            "success": True,
            "data": regulation
        }

    def get_compliance_lists_for_symbol(self, symbol: str) -> dict:
        """
        List all compliance lists where a particular symbol is currently active.

        Args:
            symbol (str): The security symbol to query.

        Returns:
            dict: {
                "success": True,
                "data": List[ComplianceListInfo],  # Info for each compliance list where 'symbol' is active
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Symbol does not exist"
            }

        Constraints:
            - Only lists where symbol is marked 'active' at query time are included.
            - Symbol must exist in the securities dataset.
        """
        if symbol not in self.securities:
            return {"success": False, "error": "Symbol does not exist"}

        active_lists = []
        for list_id, symbol_map in self.compliance_list_securities.items():
            sec_info = symbol_map.get(symbol)
            if sec_info and sec_info.get("status") == "active":
                # Get ComplianceListInfo for list_id (may not exist, but assumed consistent by system design)
                list_info = self.compliance_lists.get(list_id)
                if list_info:
                    active_lists.append(list_info)

        return {"success": True, "data": active_lists}

    def get_compliance_list_audit_trail(self, list_id: str) -> dict:
        """
        Returns the complete membership history (add/remove/status changes)
        for a given compliance list, including regulatory linkage details.

        Args:
            list_id (str): The identifier of the compliance list.

        Returns:
            dict: {
                'success': True,
                'data': {
                    'compliance_list_info': ComplianceListInfo,
                    'regulation_info': RegulationInfo,
                    'membership_history': List[ComplianceListSecurityInfo]
                }
            }
            or
            {
                'success': False,
                'error': str
            }

        Constraints:
            - The compliance list must exist.
            - Returns all current and historical (active/inactive) symbol memberships for the list.
            - Includes full compliance list info and regulatory linkage.
        """
        # Check compliance list existence
        compliance_list = self.compliance_lists.get(list_id)
        if not compliance_list:
            return {'success': False, 'error': 'Compliance list does not exist'}

        # Get regulation info
        regulation_id = compliance_list.get('regulation_id')
        regulation_info = self.regulations.get(regulation_id)
        if not regulation_info:
            # Should not happen but possible if state corrupt, handle gracefully
            return {'success': False, 'error': 'Regulation linked to compliance list does not exist'}

        # Gather membership history
        symbol_history = self.compliance_list_securities.get(list_id, {})
        membership_history = list(symbol_history.values()) if symbol_history else []

        return {
            'success': True,
            'data': {
                'compliance_list_info': compliance_list,
                'regulation_info': regulation_info,
                'membership_history': membership_history
            }
        }


    def synchronize_compliance_list(self, list_id: str, latest_symbols: Union[List[str], set]) -> dict:
        """
        Update a compliance list's membership and last_updated field based on the latest regulatory data feed.

        Args:
            list_id (str): ID of the compliance list to synchronize.
            latest_symbols (List[str] or set): Iterable of active symbol strings from the latest regulatory feed.

        Returns:
            dict:
                If successful: { "success": True, "message": "Compliance list synchronized successfully." }
                If error: { "success": False, "error": <error message> }

        Constraints:
            - list_id must exist in self.compliance_lists.
            - Compliance list must have a valid regulation_id.
            - Only active symbols from regulatory feed are to be recorded as active.
            - Removed symbols should have their status set to 'inactive' and removed_date updated.
            - last_updated must be refreshed to now.
        """
        if list_id not in self.compliance_lists:
            return { "success": False, "error": "Compliance list does not exist." }

        compliance_list_info = self.compliance_lists[list_id]

        regulation_id = compliance_list_info.get("regulation_id")
        if not regulation_id or regulation_id not in self.regulations:
            return { "success": False, "error": "Compliance list is not linked to a valid regulation." }

        # Validate latest_symbols
        if not isinstance(latest_symbols, (list, set)):
            return { "success": False, "error": "latest_symbols must be a list or set of symbols." }

        # Ensure all symbols in feed are string
        latest_symbols_set = set()
        for symbol in latest_symbols:
            if not isinstance(symbol, str):
                return { "success": False, "error": f"Invalid symbol in latest_symbols: {symbol!r}" }
            latest_symbols_set.add(symbol)

        # Gather existing symbols mapping for this compliance list (symbol -> ComplianceListSecurityInfo)
        cls_map: Dict[str, ComplianceListSecurityInfo] = self.compliance_list_securities.get(list_id, {})
        current_active_symbols = {symbol for symbol, info in cls_map.items() if info.get("status") == "active"}

        # To add (new active): in latest but not current
        symbols_to_add = latest_symbols_set - current_active_symbols
        # To remove (was active, not in latest): in current but not in latest
        symbols_to_remove = current_active_symbols - latest_symbols_set

        now_str = str(int(time.time()))

        # Add or update symbols that are active in the new feed
        for symbol in latest_symbols_set:
            # If new, add new ComplianceListSecurityInfo; else, set status active & clear removed_date
            if symbol not in cls_map:
                cls_map[symbol] = {
                    "list_id": list_id,
                    "symbol": symbol,
                    "added_date": now_str,
                    "removed_date": "",
                    "status": "active"
                }
            else:
                cls_map[symbol]["status"] = "active"
                cls_map[symbol]["removed_date"] = ""
                if not cls_map[symbol].get("added_date"):
                    cls_map[symbol]["added_date"] = now_str

        # Mark as inactive and update removed_date for removed symbols
        for symbol in symbols_to_remove:
            cls_map[symbol]["status"] = "inactive"
            cls_map[symbol]["removed_date"] = now_str

        # Save back changes
        self.compliance_list_securities[list_id] = cls_map

        # Update last_updated for the compliance list
        self.compliance_lists[list_id]["last_updated"] = now_str

        return { "success": True, "message": "Compliance list synchronized successfully." }


    def add_symbol_to_compliance_list(self, list_id: str, symbol: str) -> dict:
        """
        Add a security (symbol) to a compliance list, marking as 'active' with current date.

        Args:
            list_id (str): The compliance list ID to add the symbol to.
            symbol (str): The security symbol to add.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": f"Symbol '{symbol}' added to compliance list '{list_id}' as active."
                  }
                - On error: {
                    "success": False,
                    "error": str  # Error description
                  }

        Constraints:
            - Compliance list (list_id) must exist.
            - Security (symbol) must exist.
            - Symbol must not already be 'active' in the compliance list.
        """
        if list_id not in self.compliance_lists:
            return { "success": False, "error": f"Compliance list '{list_id}' does not exist." }
        if symbol not in self.securities:
            return { "success": False, "error": f"Security symbol '{symbol}' does not exist." }

        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if list_id not in self.compliance_list_securities:
            self.compliance_list_securities[list_id] = {}

        clsec = self.compliance_list_securities[list_id].get(symbol)

        if clsec:
            if clsec["status"] == "active":
                return { "success": False, "error": f"Symbol '{symbol}' is already active in compliance list '{list_id}'." }
            # Was previously inactive, reactivate
            clsec["status"] = "active"
            clsec["added_date"] = now_date
            clsec["removed_date"] = ""
            self.compliance_list_securities[list_id][symbol] = clsec
            return { "success": True, "message": f"Symbol '{symbol}' reactivated as active in compliance list '{list_id}'." }
        else:
            # New entry
            self.compliance_list_securities[list_id][symbol] = {
                "list_id": list_id,
                "symbol": symbol,
                "added_date": now_date,
                "removed_date": "",
                "status": "active"
            }
            return { "success": True, "message": f"Symbol '{symbol}' added to compliance list '{list_id}' as active." }

    def remove_symbol_from_compliance_list(self, list_id: str, symbol: str, removed_date: str) -> dict:
        """
        Mark a symbol as 'inactive' on a compliance list, updating the removed_date and status.
    
        Args:
            list_id (str): The identifier of the compliance list.
            symbol (str): The security symbol to mark inactive.
            removed_date (str): The date when the symbol is marked inactive (in YYYY-MM-DD or similar format).
    
        Returns:
            dict: 
                - On success: 
                    { "success": True, "message": "Symbol {symbol} marked as inactive on compliance list {list_id}." }
                - On failure: 
                    { "success": False, "error": "Reason for failure" }
    
        Constraints:
            - The compliance list and symbol must exist.
            - Status and removed_date are updated (even if already inactive).
            - Audit trail is maintained via removed_date and status history.
        """
        if list_id not in self.compliance_list_securities:
            return { "success": False, "error": f"Compliance list {list_id} does not exist." }
    
        if symbol not in self.compliance_list_securities[list_id]:
            return { "success": False, "error": f"Symbol {symbol} is not present in compliance list {list_id}." }
    
        info = self.compliance_list_securities[list_id][symbol]
        info["status"] = "inactive"
        info["removed_date"] = removed_date
        # Optionally: log info/status change for audit purposes, if required elsewhere
    
        return { 
            "success": True, 
            "message": f"Symbol {symbol} marked as inactive on compliance list {list_id}." 
        }

    def update_symbol_status_in_compliance_list(
        self,
        list_id: str,
        symbol: str,
        status: str,
        current_date: str = None
    ) -> dict:
        """
        Change the status of a symbol in a compliance list (e.g., re-activate or deactivate).

        Args:
            list_id (str): ID of the compliance list.
            symbol (str): Symbol of the security.
            status (str): New status ('active' or 'inactive').
            current_date (str, optional): Date-time string for status update (used for added/removed date). If None, no change to added_date unless status is 'active' and previously inactive, or removed_date if status is 'inactive'.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Status for symbol updated in compliance list."
                }
                OR
                {
                    "success": False,
                    "error": "Reason why update failed."
                }

        Constraints:
            - Only updates mapping if it exists.
            - Only known statuses ('active', 'inactive') are allowed.
            - Updates appropriate date fields on status change.
        """
        # Validate list existence
        if list_id not in self.compliance_lists:
            return {"success": False, "error": "Compliance list not found."}

        # Validate symbol existence
        if symbol not in self.securities:
            return {"success": False, "error": "Symbol not found in security master."}

        # Validate mapping exists
        if list_id not in self.compliance_list_securities or \
           symbol not in self.compliance_list_securities[list_id]:
            return {"success": False, "error": "Symbol not present in specified compliance list."}

        # Validate status value
        if status not in ("active", "inactive"):
            return {"success": False, "error": "Unknown status value: must be 'active' or 'inactive'."}

        info = self.compliance_list_securities[list_id][symbol]

        # Update status and dates accordingly
        # If activating:
        if status == "active":
            if info["status"] != "active":
                info["status"] = "active"
                # Set added_date to now if becoming active
                if current_date:
                    info["added_date"] = current_date
                info["removed_date"] = ""
            else:
                # Already active, update only if needed
                pass
        else:  # status == "inactive"
            if info["status"] != "inactive":
                info["status"] = "inactive"
                if current_date:
                    info["removed_date"] = current_date
            else:
                # Already inactive, update only if needed
                pass

        return {"success": True, "message": "Status for symbol updated in compliance list."}

    def create_compliance_list(
        self, 
        list_id: str, 
        regulation_id: str, 
        name: str, 
        last_updated: str
    ) -> dict:
        """
        Create a new compliance list linked to an existing regulation.

        Args:
            list_id (str): Unique identifier for the compliance list.
            regulation_id (str): Regulation to which this list is linked. Must exist.
            name (str): Name of the compliance list.
            last_updated (str): Timestamp when the compliance list was last updated (ISO format).

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "message": "Compliance list <list_id> successfully created and linked to regulation <regulation_id>."
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Error message
                  }
        Constraints:
            - regulation_id must reference an existing regulation.
            - list_id must be unique and not already exist in compliance_lists.
            - Regulatory references are maintained for audit/reporting.
        """
        if regulation_id not in self.regulations:
            return {"success": False, "error": f"Regulation {regulation_id} does not exist."}
        if list_id in self.compliance_lists:
            return {"success": False, "error": f"Compliance list {list_id} already exists."}

        compliance_list_info = {
            "list_id": list_id,
            "regulation_id": regulation_id,
            "name": name,
            "last_updated": last_updated
        }
        self.compliance_lists[list_id] = compliance_list_info
        self.compliance_list_securities[list_id] = {}  # Initialize empty mapping

        return {
            "success": True,
            "message": f"Compliance list {list_id} successfully created and linked to regulation {regulation_id}."
        }

    def delete_compliance_list(self, list_id: str) -> dict:
        """
        Remove an existing compliance list and its associated symbol entries.
        Admin/audit log is assumed external or not implemented here.

        Args:
            list_id (str): The ID of the compliance list to delete.

        Returns:
            dict: 
              { "success": True, "message": "Compliance list <list_id> deleted." }
              or
              { "success": False, "error": <reason> }

        Constraints:
            - The compliance list must exist.
            - All symbol associations (compliance_list_securities) for this list are removed.
            - Regulation and audit trails are not affected.
        """
        if list_id not in self.compliance_lists:
            return { "success": False, "error": f"Compliance list '{list_id}' does not exist." }

        # Remove the compliance list
        del self.compliance_lists[list_id]

        # Remove associated securities mapping if any
        if list_id in self.compliance_list_securities:
            del self.compliance_list_securities[list_id]

        return { "success": True, "message": f"Compliance list '{list_id}' deleted." }

    def update_regulation_info(
        self, 
        regulation_id: str, 
        name: str = None, 
        description: str = None, 
        effective_date: str = None
    ) -> dict:
        """
        Modify details of a regulation (description, name, effective_date).

        Args:
            regulation_id (str): ID of the regulation to update. (Required)
            name (str, optional): New name. (If not provided, do not update)
            description (str, optional): New description.
            effective_date (str, optional): New effective date (format: yyyy-mm-dd or per RegulationInfo spec).

        Returns:
            dict: {
                "success": True,
                "message": "Regulation info updated successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - regulation_id must exist.
            - At least one field must be provided for update.
            - Field names must match RegulationInfo.
        """
        if regulation_id not in self.regulations:
            return { "success": False, "error": "Regulation ID does not exist." }

        updates = {}
        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if effective_date is not None:
            updates['effective_date'] = effective_date

        if not updates:
            return { "success": False, "error": "No fields provided to update." }

        # Validate fields
        valid_fields = {"name", "description", "effective_date"}
        for k in updates:
            if k not in self.regulations[regulation_id]:
                return { "success": False, "error": f"Invalid field for regulation: {k}" }

        # Apply updates
        for k, v in updates.items():
            self.regulations[regulation_id][k] = v

        return { "success": True, "message": "Regulation info updated successfully" }

    def add_security(
        self,
        symbol: str,
        name: str,
        isin: str,
        cusip: str,
        exchange: str
    ) -> dict:
        """
        Add a new publicly traded security record to the system.

        Args:
            symbol (str): Unique ticker symbol for the security.
            name (str): Full name of the security.
            isin (str): International Securities Identification Number.
            cusip (str): Committee on Uniform Securities Identification Procedures ID.
            exchange (str): The exchange where the security is traded.

        Returns:
            dict: {
                "success": True,
                "message": "Security with symbol <symbol> added successfully."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The symbol must not already exist (must be unique).
            - All fields are required and must not be empty.
        """
        required_fields = {
            "symbol": symbol,
            "name": name,
            "isin": isin,
            "cusip": cusip,
            "exchange": exchange
        }
        # Check for missing/empty fields
        for field, value in required_fields.items():
            if not isinstance(value, str) or not value.strip():
                return {
                    "success": False,
                    "error": f"Field '{field}' is required and must be a non-empty string."
                }
        # Check uniqueness
        if symbol in self.securities:
            return {
                "success": False,
                "error": f"Security with symbol '{symbol}' already exists."
            }
        # Add to system
        self.securities[symbol] = {
            "symbol": symbol,
            "name": name,
            "isin": isin,
            "cusip": cusip,
            "exchange": exchange
        }
        return {
            "success": True,
            "message": f"Security with symbol '{symbol}' added successfully."
        }

    def remove_security(self, symbol: str) -> dict:
        """
        Soft delete a security from the system for audit compliance.

        Args:
            symbol (str): The security's symbol to remove.

        Returns:
            dict: Success and message if removed (soft deleted), or error reason.
                {
                    "success": True,
                    "message": "Security soft-deleted (audit log retained)."
                }
                or
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Remove (soft delete) the security from active securities.
            - Do NOT remove audit trails or compliance list mappings; all data is preserved for audit.
            - If already deleted or does not exist, return failure.
            - Audit-enabled: soft-deleted securities should be stored for retention.
        """
        # Initialize deleted_securities dict if not already present
        if not hasattr(self, "deleted_securities") or not isinstance(self.deleted_securities, dict):
            self.deleted_securities = {}

        # Check if security is present and not already deleted
        if symbol not in self.securities:
            # If it's in deleted_securities, consider already deleted
            if hasattr(self, "deleted_securities") and symbol in self.deleted_securities:
                return {
                    "success": False,
                    "error": "Security does not exist or already deleted."
                }
            else:
                return {
                    "success": False,
                    "error": "Security does not exist."
                }
        # Soft delete
        self.deleted_securities[symbol] = self.securities[symbol]
        del self.securities[symbol]
        return {
            "success": True,
            "message": "Security soft-deleted (audit log retained)."
        }


class FinancialComplianceMonitoringSystem(BaseEnv):
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
            if key == "deleted_securities" and not isinstance(value, dict):
                value = {}
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

    def get_compliance_list_by_name(self, **kwargs):
        return self._call_inner_tool('get_compliance_list_by_name', kwargs)

    def get_regulation_by_id(self, **kwargs):
        return self._call_inner_tool('get_regulation_by_id', kwargs)

    def get_regulation_by_name(self, **kwargs):
        return self._call_inner_tool('get_regulation_by_name', kwargs)

    def get_security_info_by_symbol(self, **kwargs):
        return self._call_inner_tool('get_security_info_by_symbol', kwargs)

    def check_symbol_in_compliance_list(self, **kwargs):
        return self._call_inner_tool('check_symbol_in_compliance_list', kwargs)

    def list_active_symbols_in_compliance_list(self, **kwargs):
        return self._call_inner_tool('list_active_symbols_in_compliance_list', kwargs)

    def get_compliance_list_last_updated(self, **kwargs):
        return self._call_inner_tool('get_compliance_list_last_updated', kwargs)

    def get_regulation_for_compliance_list(self, **kwargs):
        return self._call_inner_tool('get_regulation_for_compliance_list', kwargs)

    def get_compliance_lists_for_symbol(self, **kwargs):
        return self._call_inner_tool('get_compliance_lists_for_symbol', kwargs)

    def get_compliance_list_audit_trail(self, **kwargs):
        return self._call_inner_tool('get_compliance_list_audit_trail', kwargs)

    def synchronize_compliance_list(self, **kwargs):
        return self._call_inner_tool('synchronize_compliance_list', kwargs)

    def add_symbol_to_compliance_list(self, **kwargs):
        return self._call_inner_tool('add_symbol_to_compliance_list', kwargs)

    def remove_symbol_from_compliance_list(self, **kwargs):
        return self._call_inner_tool('remove_symbol_from_compliance_list', kwargs)

    def update_symbol_status_in_compliance_list(self, **kwargs):
        return self._call_inner_tool('update_symbol_status_in_compliance_list', kwargs)

    def create_compliance_list(self, **kwargs):
        return self._call_inner_tool('create_compliance_list', kwargs)

    def delete_compliance_list(self, **kwargs):
        return self._call_inner_tool('delete_compliance_list', kwargs)

    def update_regulation_info(self, **kwargs):
        return self._call_inner_tool('update_regulation_info', kwargs)

    def add_security(self, **kwargs):
        return self._call_inner_tool('add_security', kwargs)

    def remove_security(self, **kwargs):
        return self._call_inner_tool('remove_security', kwargs)
