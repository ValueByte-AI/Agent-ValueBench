# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import time



class CardInfo(TypedDict):
    card_id: str
    card_number: str
    expiration_date: str
    cardholder_id: str
    status: str
    BIN: str
    issue_date: str
    card_type: str
    card_art_url: str

class CardholderInfo(TypedDict):
    cardholder_id: str
    name: str
    address: str
    contact_info: str
    account_sta: str  # Possible typo; assumed to be "account_status"

class BINInfo(TypedDict):
    n_number: str
    brand: str
    card_art_url: str
    issuer_name: str
    card_typ: str  # Possible typo; assumed to be "card_type"

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for Payment Card Management System.
        """

        # Cards: {card_id: CardInfo}
        # Entity: Card (card_id, card_number, expiration_date, cardholder_id, status, BIN, issue_date, card_type, card_art_url)
        self.cards: Dict[str, CardInfo] = {}

        # Cardholders: {cardholder_id: CardholderInfo}
        # Entity: Cardholder (cardholder_id, name, address, contact_info, account_sta)
        self.cardholders: Dict[str, CardholderInfo] = {}

        # BINs: {n_number: BINInfo}
        # Entity: BIN (n_number, brand, card_art_url, issuer_name, card_typ)
        self.bins: Dict[str, BINInfo] = {}

        # Constraints:
        # - A card must reference a valid cardholder and BIN.
        # - Only authorized users (e.g., business owner, admin) can access full card details.
        # - Each BIN maps to a unique brand and card art URL.
        # - Card status must reflect current validity (e.g., active, revoked, expired).
        # - Card data must comply with security and regulatory requirements (e.g., masking card number on retrieval).

    def get_card_info(self, card_id: str) -> dict:
        """
        Retrieve the details of a specified card by card_id with masked card number.

        Args:
            card_id (str): The ID of the card to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CardInfo (with card_number masked)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
    
        Constraints:
            - The card must exist.
            - The card_number in the response must be masked for security (all but last 4 digits replaced by '*').
        """
        card = self.cards.get(card_id)
        if not card:
            return {"success": False, "error": "Card not found"}

        masked_number = '*' * (len(card["card_number"]) - 4) + card["card_number"][-4:]
        masked_card = dict(card)
        masked_card["card_number"] = masked_number

        return {"success": True, "data": masked_card}

    def get_card_full_info_admin(self, card_id: str, user_role: str) -> dict:
        """
        Retrieve full (unmasked) card details for the specified card_id.
        Only accessible to admin users.

        Args:
            card_id (str): The ID of the card whose details are to be retrieved.
            user_role (str): The role of the requester (must be 'admin').

        Returns:
            dict: {
                "success": True,
                "data": CardInfo  # Full card info, unmasked card_number
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found, permission denied)
            }

        Constraints:
            - Only users with admin privileges can retrieve unmasked card info.
            - If card_id is invalid or not found, return error.
        """
        if user_role != "admin":
            return { "success": False, "error": "Permission denied: admin only" }
        if card_id not in self.cards:
            return { "success": False, "error": "Card not found" }
        return { "success": True, "data": self.cards[card_id] }

    def get_cards_by_cardholder(self, cardholder_id: str) -> dict:
        """
        Retrieve all cards (with masked card numbers) belonging to a given cardholder.

        Args:
            cardholder_id (str): The identifier of the cardholder to retrieve cards for.

        Returns:
            dict: {
                "success": True,
                "data": List[CardInfo] (with card_number masked)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - cardholder_id must exist in system.
            - Returned card_number fields are masked (e.g., "************1234").
        """
        if cardholder_id not in self.cardholders:
            return { "success": False, "error": "Cardholder does not exist" }

        def mask_card_number(card_number: str) -> str:
            # Mask all but last 4 digits
            if len(card_number) <= 4:
                return "*" * len(card_number)
            return "*" * (len(card_number) - 4) + card_number[-4:]

        result = []
        for card in self.cards.values():
            if card["cardholder_id"] == cardholder_id:
                masked_card = dict(card)
                masked_card["card_number"] = mask_card_number(card["card_number"])
                result.append(masked_card)

        return { "success": True, "data": result }

    def get_cardholder_info(self, cardholder_id: str) -> dict:
        """
        Retrieve KYC and contact info for a specified cardholder by cardholder_id.

        Args:
            cardholder_id (str): The unique identifier for the cardholder.

        Returns:
            dict: {
                "success": True,
                "data": CardholderInfo  # Cardholder's full KYC and contact info
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. cardholder does not exist
            }

        Constraints:
            - cardholder_id must exist in the system.
            - Operation returns all KYC and contact info fields.
        """
        cardholder = self.cardholders.get(cardholder_id)
        if not cardholder:
            return {"success": False, "error": "Cardholder does not exist"}
        return {"success": True, "data": cardholder}

    def get_bin_info(self, n_number: str) -> dict:
        """
        Retrieve complete BIN details for a given BIN number.

        Args:
            n_number (str): The BIN (Bank Identification Number) to look up.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": BINInfo  # Complete BIN details for the given n_number
                    }
                On failure (e.g., not found):
                    {
                        "success": False,
                        "error": "BIN not found"
                    }

        Constraints:
            - The BIN number must exist in the system.
            - Each BIN uniquely maps to its info.
        """
        bin_info = self.bins.get(n_number)
        if not bin_info:
            return { "success": False, "error": "BIN not found" }

        return { "success": True, "data": bin_info }

    def get_card_art_url_by_bin(self, n_number: str) -> dict:
        """
        Retrieve the card art URL for a specific BIN.

        Args:
            n_number (str): The BIN number to query.

        Returns:
            dict: 
                - If BIN exists: { "success": True, "data": str (card_art_url) }
                - If not found:  { "success": False, "error": "BIN not found" }

        Constraints:
            - n_number must exist in the BINs database.
        """
        bin_info = self.bins.get(n_number)
        if not bin_info:
            return { "success": False, "error": "BIN not found" }

        return {
            "success": True,
            "data": bin_info["card_art_url"]
        }

    def list_active_cards(self) -> dict:
        """
        List all cards with status "active".

        Returns:
            dict:
                success (bool): True if query is successful.
                data (List[CardInfo]): A list of masked CardInfo for cards where status == "active".
            If no active cards exist, returns success with an empty list.
            Card numbers will be masked according to security requirements
            (e.g., format: "**** **** **** 1234").

        Constraints:
        - Only cards with status "active" are listed.
        - Card numbers in the listing are always masked for security compliance.
        """
        def mask_card_number(card_number: str) -> str:
            # Example: Keep last 4 digits, mask rest with '*' (grouped as in "**** **** **** 1234")
            if len(card_number) <= 4:
                return "****"
            masked = "*" * (len(card_number) - 4) + card_number[-4:]
            # For display grouping if 16-digit: "**** **** **** 1234"
            if len(card_number) == 16:
                return " ".join([
                    "****", "****", "****", card_number[-4:]
                ])
            return masked

        results = []
        for card in self.cards.values():
            if card.get("status") == "active":
                # Copy card info and mask card_number
                masked_card = dict(card)
                masked_card["card_number"] = mask_card_number(card["card_number"])
                results.append(masked_card)
        return {
            "success": True,
            "data": results
        }

    def list_cards_by_status(self, status: str) -> dict:
        """
        List all cards filtered by the given status (e.g., 'active', 'revoked', 'expired').

        Args:
            status (str): The card status to filter by.

        Returns:
            dict:
                success (bool): True if query succeeds.
                data (List[CardInfo]): List of CardInfo dictionaries matching the input status. Empty list if none found.
        Constraints:
            - No permissions check.
            - The 'status' field is matched exactly.
        """
        if not isinstance(status, str):
            return {"success": False, "error": "Invalid status parameter; must be a string."}

        filtered_cards = [
            card_info
            for card_info in self.cards.values()
            if card_info.get("status") == status
        ]
        return {"success": True, "data": filtered_cards}

    def list_bins(self) -> dict:
        """
        Retrieve the list of all registered BINs in the system.

        Args:
            None.

        Returns:
            dict: {
                "success": True,
                "data": List[BINInfo],  # List may be empty if no BINs are present.
            }
        Constraints:
            - No input required.
            - Returns all BINs present in the system.
        """
        bin_list = list(self.bins.values())
        return {
            "success": True,
            "data": bin_list
        }

    def list_brands(self) -> dict:
        """
        List all unique brands from the BIN definitions in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of unique brand names (may be empty if no BINs)
            }
        """
        brands = {bin_info["brand"] for bin_info in self.bins.values()}
        return { "success": True, "data": list(brands) }

    def validate_card_status(self, card_id: str) -> dict:
        """
        Check if a specific card is currently valid ('active'), or provide the reason for its invalidity.

        Args:
            card_id (str): The unique identifier of the card to check.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "status": str,        # The status of the card (e.g., "active", "revoked", "expired")
                            "is_valid": bool,     # True if status == "active", else False
                            "reason": str|null    # If not valid, reason (same as status), else None
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str    # Reason for failure, e.g. card not found
                    }

        Constraints:
            - The card must exist in the system.
        """
        card = self.cards.get(card_id)
        if not card:
            return { "success": False, "error": "Card not found" }
        status = card.get("status")
        if status == "active":
            return {
                "success": True,
                "data": {
                    "status": "active",
                    "is_valid": True,
                    "reason": None
                }
            }
        else:
            # Handle missing or abnormal status as not valid
            reason = status if status else "unknown status"
            return {
                "success": True,
                "data": {
                    "status": status if status else "unknown",
                    "is_valid": False,
                    "reason": reason
                }
            }

    def issue_card(
        self,
        card_id: str,
        card_number: str,
        expiration_date: str,
        cardholder_id: str,
        BIN: str,
        issue_date: str,
        card_type: str,
        card_art_url: str
    ) -> dict:
        """
        Issue (create) a new card for a cardholder.

        Args:
            card_id (str): Unique identifier for the card (must be unique).
            card_number (str): Primary account number (must be unique).
            expiration_date (str): Expiry date for the card.
            cardholder_id (str): Cardholder entity id (must exist).
            BIN (str): Bank Identification Number (must exist).
            issue_date (str): Date of card issuance.
            card_type (str): Card type (e.g., debit, credit).
            card_art_url (str): URL for card image/art.

        Returns:
            dict: {
                "success": True,
                "message": "Card issued successfully",
                "card_id": card_id
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - card_id and card_number must be globally unique.
            - cardholder_id must exist.
            - BIN must exist.
            - Required fields must not be empty.
        """
        # Check for required fields
        if not all([card_id, card_number, expiration_date, cardholder_id, BIN, issue_date, card_type, card_art_url]):
            return {"success": False, "error": "All fields are required"}

        # Uniqueness checks
        if card_id in self.cards:
            return {"success": False, "error": "Card ID already exists"}

        for c in self.cards.values():
            if c["card_number"] == card_number:
                return {"success": False, "error": "Card number already exists"}

        # Cardholder and BIN checks
        if cardholder_id not in self.cardholders:
            return {"success": False, "error": "Cardholder does not exist"}
        if BIN not in self.bins:
            return {"success": False, "error": "BIN does not exist"}

        # Status must start as "active" for a new card
        card_info: CardInfo = {
            "card_id": card_id,
            "card_number": card_number,
            "expiration_date": expiration_date,
            "cardholder_id": cardholder_id,
            "status": "active",
            "BIN": BIN,
            "issue_date": issue_date,
            "card_type": card_type,
            "card_art_url": card_art_url
        }
        self.cards[card_id] = card_info

        return {
            "success": True,
            "message": "Card issued successfully",
            "card_id": card_id
        }

    def update_card_status(self, card_id: str, new_status: str) -> dict:
        """
        Change the status of a card to "active," "revoked," or "expired."

        Args:
            card_id (str): The identifier of the card to update.
            new_status (str): The new status to set; must be one of ["active", "revoked", "expired"].

        Returns:
            dict: {
                "success": True,
                "message": "Card status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<error_reason>"
            }

        Constraints:
            - card_id must exist in the system.
            - new_status must be "active", "revoked", or "expired".
            - Card status must accurately reflect current validity.
        """
        allowed_statuses = {"active", "revoked", "expired"}
        if card_id not in self.cards:
            return {"success": False, "error": "Card ID does not exist."}
        if new_status not in allowed_statuses:
            return {"success": False, "error": "Invalid status value. Must be 'active', 'revoked', or 'expired'."}

        self.cards[card_id]["status"] = new_status
        return {"success": True, "message": f"Card status updated to {new_status}."}

    def revoke_card(self, card_id: str) -> dict:
        """
        Set a card's status to "revoked", making it invalid for further transactions.

        Args:
            card_id (str): The unique identifier of the card to revoke.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Card <card_id> status updated to revoked."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error_reason>
                    }

        Constraints:
            - The card must exist.
            - Sets status to "revoked" (idempotent if already revoked).
        """
        card = self.cards.get(card_id)
        if not card:
            return {"success": False, "error": "Card not found"}
    
        if card["status"].lower() == "revoked":
            # Already revoked, idempotent
            return {
                "success": True,
                "message": f"Card {card_id} status is already revoked."
            }

        card["status"] = "revoked"
        # Optionally, in real implementation, update status timestamp if tracked

        return {
            "success": True,
            "message": f"Card {card_id} status updated to revoked."
        }

    def expire_card(self, card_id: str) -> dict:
        """
        Mark a card as 'expired' by updating its status and/or expiration date.

        Args:
            card_id (str): The ID of the card to be expired.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Card <card_id> expired successfully" }
                - On failure: { "success": False, "error": "<error-message>" }

        Constraints:
            - Card must exist.
            - Card status will be updated to 'expired'.
            - Optionally, expiration_date can be set to current date.
        """

        if card_id not in self.cards:
            return {"success": False, "error": f"Card ID '{card_id}' does not exist"}

        # Update status to 'expired'
        self.cards[card_id]['status'] = 'expired'
    
        # Optional: update expiration_date to now, for audit (ISO format)
        now_iso = time.strftime("%Y-%m-%d")
        self.cards[card_id]['expiration_date'] = now_iso

        return { "success": True, "message": f"Card {card_id} expired successfully" }

    def update_cardholder_info(
        self,
        cardholder_id: str,
        name: str = None,
        address: str = None,
        contact_info: str = None,
        account_sta: str = None
    ) -> dict:
        """
        Edit the KYC/contact details for a given cardholder.

        Args:
            cardholder_id (str): The ID of the cardholder to update.
            name (str, optional): Updated name.
            address (str, optional): Updated address.
            contact_info (str, optional): Updated contact info.
            account_sta (str, optional): Updated account status.

        Returns:
            dict: {
                "success": True,
                "message": "Cardholder info updated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only updates to allowed fields are performed.
            - Cardholder must exist.
            - At least one updatable field must be provided.
        """
        cardholder = self.cardholders.get(cardholder_id)
        if cardholder is None:
            return { "success": False, "error": "Cardholder does not exist." }

        updatable_fields = ["name", "address", "contact_info", "account_sta"]
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if address is not None:
            update_data["address"] = address
        if contact_info is not None:
            update_data["contact_info"] = contact_info
        if account_sta is not None:
            update_data["account_sta"] = account_sta

        if not update_data:
            return { "success": False, "error": "No update fields provided." }

        for key, value in update_data.items():
            cardholder[key] = value

        # Optionally: self.cardholders[cardholder_id] = cardholder

        return { "success": True, "message": "Cardholder info updated." }

    def add_bin_entry(
        self, 
        n_number: str, 
        brand: str, 
        card_art_url: str, 
        issuer_name: str, 
        card_type: str
    ) -> dict:
        """
        Add a new BIN entry and its associated metadata.

        Args:
            n_number (str): The BIN (Bank Identification Number, must be unique).
            brand (str): Brand for the BIN (e.g., VISA, Mastercard).
            card_art_url (str): URL to the card art resource for this BIN.
            issuer_name (str): Name of the issuing bank.
            card_type (str): Type of card (e.g., credit, debit).

        Returns:
            dict: 
                { "success": True, "message": "BIN entry added successfully." }
                OR
                { "success": False, "error": "BIN already exists." }
        Constraints:
            - BIN numbers must be unique (cannot overwrite existing entry).
            - All required fields must be provided (not empty).
        """
        if not all([n_number, brand, card_art_url, issuer_name, card_type]):
            return { "success": False, "error": "All fields are required." }

        if n_number in self.bins:
            return { "success": False, "error": "BIN already exists." }

        self.bins[n_number] = {
            "n_number": n_number,
            "brand": brand,
            "card_art_url": card_art_url,
            "issuer_name": issuer_name,
            "card_typ": card_type  # Using field name as in TypedDict
        }
        return { "success": True, "message": "BIN entry added successfully." }

    def update_bin_info(
        self, 
        n_number: str, 
        brand: str = None, 
        card_art_url: str = None, 
        issuer_name: str = None,
        card_typ: str = None
    ) -> dict:
        """
        Edit details (brand, card_art_url, issuer_name, optionally card_typ) for an existing BIN.

        Args:
            n_number (str): The BIN identifier (must exist).
            brand (Optional[str]): New brand (if to be updated).
            card_art_url (Optional[str]): New card art URL (if to be updated).
            issuer_name (Optional[str]): New issuer name (if to be updated).
            card_typ (Optional[str]): New card type (if to be updated).

        Returns:
            dict: 
                On success: { "success": True, "message": "BIN info updated." }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - The BIN must already exist.
            - Only supplied, valid fields will be updated.
            - Each BIN maps to a unique brand and card art URL (not enforced across all BINs here).
        """
        if n_number not in self.bins:
            return {"success": False, "error": "BIN does not exist."}

        bin_info = self.bins[n_number]
        updated = False
        allowed_fields = ["brand", "card_art_url", "issuer_name", "card_typ"]
        update_map = {
            "brand": brand,
            "card_art_url": card_art_url,
            "issuer_name": issuer_name,
            "card_typ": card_typ,
        }

        for key, value in update_map.items():
            if value is not None and key in bin_info and bin_info[key] != value:
                bin_info[key] = value
                updated = True

        if not updated:
            return {"success": False, "error": "No valid attributes to update."}

        self.bins[n_number] = bin_info
        return {"success": True, "message": "BIN info updated."}

    def remove_card(self, card_id: str, is_admin: bool) -> dict:
        """
        Admin action to delete (deactivate) a card.
        Ensures regulatory compliance by retaining card information, but marks card as inactive.

        Args:
            card_id (str): ID of the card to remove/deactivate.
            is_admin (bool): Must be True; only admins are allowed to perform this operation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Card <card_id> deactivated (data retained for compliance)"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <error reason>
                    }

        Constraints:
            - Only admin users may remove a card.
            - Card data must be retained (not deleted) for compliance; card status is set to 'deactivated'.
            - If already deactivated/revoked/expired, just confirm current status but do not error.
        """
        if not is_admin:
            return {"success": False, "error": "Permission denied: operation allowed only for admin users"}
        if card_id not in self.cards:
            return {"success": False, "error": f"Card {card_id} does not exist"}
        # Regulatory data retention: do NOT delete, just deactivate
        card = self.cards[card_id]
        if card['status'] in ('deactivated', 'revoked', 'expired'):
            return {"success": True, "message": f"Card {card_id} is already {card['status']} (data retained for compliance)"}
        card['status'] = 'deactivated'
        return {"success": True, "message": f"Card {card_id} deactivated (data retained for compliance)"}


class PaymentCardManagementSystem(BaseEnv):
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

    def get_card_info(self, **kwargs):
        return self._call_inner_tool('get_card_info', kwargs)

    def get_card_full_info_admin(self, **kwargs):
        return self._call_inner_tool('get_card_full_info_admin', kwargs)

    def get_cards_by_cardholder(self, **kwargs):
        return self._call_inner_tool('get_cards_by_cardholder', kwargs)

    def get_cardholder_info(self, **kwargs):
        return self._call_inner_tool('get_cardholder_info', kwargs)

    def get_bin_info(self, **kwargs):
        return self._call_inner_tool('get_bin_info', kwargs)

    def get_card_art_url_by_bin(self, **kwargs):
        return self._call_inner_tool('get_card_art_url_by_bin', kwargs)

    def list_active_cards(self, **kwargs):
        return self._call_inner_tool('list_active_cards', kwargs)

    def list_cards_by_status(self, **kwargs):
        return self._call_inner_tool('list_cards_by_status', kwargs)

    def list_bins(self, **kwargs):
        return self._call_inner_tool('list_bins', kwargs)

    def list_brands(self, **kwargs):
        return self._call_inner_tool('list_brands', kwargs)

    def validate_card_status(self, **kwargs):
        return self._call_inner_tool('validate_card_status', kwargs)

    def issue_card(self, **kwargs):
        return self._call_inner_tool('issue_card', kwargs)

    def update_card_status(self, **kwargs):
        return self._call_inner_tool('update_card_status', kwargs)

    def revoke_card(self, **kwargs):
        return self._call_inner_tool('revoke_card', kwargs)

    def expire_card(self, **kwargs):
        return self._call_inner_tool('expire_card', kwargs)

    def update_cardholder_info(self, **kwargs):
        return self._call_inner_tool('update_cardholder_info', kwargs)

    def add_bin_entry(self, **kwargs):
        return self._call_inner_tool('add_bin_entry', kwargs)

    def update_bin_info(self, **kwargs):
        return self._call_inner_tool('update_bin_info', kwargs)

    def remove_card(self, **kwargs):
        return self._call_inner_tool('remove_card', kwargs)
