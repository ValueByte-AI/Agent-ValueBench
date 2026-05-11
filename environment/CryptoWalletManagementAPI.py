# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
import uuid
from datetime import datetime



# State entity: Wallet
class WalletInfo(TypedDict):
    wallet_id: str
    wallet_type: str
    blockchain_address: str
    configuration: str
    status: str
    created_at: str
    updated_at: str

# State entity: WalletCollection
class WalletCollectionInfo(TypedDict):
    total_count: int
    wallet_ids: List[str]  # ordered list of wallet_ids

# State entity: BlockchainAddress
class BlockchainAddressInfo(TypedDict):
    address: str
    blockchain_type: str
    associated_wallet_id: str

# State entity: Transaction
class TransactionInfo(TypedDict):
    transaction_id: str
    wallet_id: str
    from_address: str
    to_address: str
    amount: float
    token_type: str
    timestamp: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing cryptocurrency wallets, addresses, and transactions.
        """

        # Wallet storage: {wallet_id: WalletInfo}
        self.wallets: Dict[str, WalletInfo] = {}

        # Blockchain addresses: {address: BlockchainAddressInfo}
        self.blockchain_addresses: Dict[str, BlockchainAddressInfo] = {}

        # Transactions: {transaction_id: TransactionInfo}
        self.transactions: Dict[str, TransactionInfo] = {}

        # Last wallet collection used for pagination/listing (maps to WalletCollection entity)
        self.last_wallet_collection: WalletCollectionInfo = {
            "total_count": 0,
            "wallet_ids": []
        }

        # --- Constraints rules ---
        # - The wallet list returned must respect the specified limit and offset for pagination.
        # - Only wallets of the requested type (e.g., "token forwarding") should be listed for that operation.
        # - Each wallet must have a unique blockchain address.
        # - Wallet status and configuration must be consistent with supported API operations.

    def list_wallets_paginated(self, limit: int, offset: int) -> dict:
        """
        Retrieve a paginated list of all wallets using the specified limit and offset.

        Args:
            limit (int): Maximum number of wallets to include in the result (must be >= 0).
            offset (int): Start index in the wallet list (must be >= 0).

        Returns:
            dict: {
                'success': True,
                'data': WalletCollectionInfo (total_count, wallet_ids as ordered list for this page)
            }
            or
            {
                'success': False,
                'error': str (error message)
            }

        Constraints:
            - The wallet list returned must respect the specified limit and offset for pagination.
            - No wallet type filtering.
        """
        # Validate input
        if not isinstance(limit, int) or not isinstance(offset, int):
            return {"success": False, "error": "Arguments 'limit' and 'offset' must be integers"}
        if limit < 0 or offset < 0:
            return {"success": False, "error": "Arguments 'limit' and 'offset' must be non-negative integers"}

        all_wallet_ids = list(self.wallets.keys())
        total_count = len(all_wallet_ids)

        # Apply pagination
        paginated_ids = all_wallet_ids[offset:offset + limit] if limit > 0 else []

        collection_info: WalletCollectionInfo = {
            "total_count": total_count,
            "wallet_ids": paginated_ids
        }
        self.last_wallet_collection = collection_info  # Track the last used collection if needed

        return {"success": True, "data": collection_info}

    def list_wallets_by_type_paginated(self, wallet_type: str, limit: int, offset: int) -> dict:
        """
        Retrieve a paginated list of wallets filtered by the specified wallet_type.

        Args:
            wallet_type (str): Filter wallets of this type (e.g., 'token forwarding').
            limit (int): Maximum number of results to return (must be >= 0).
            offset (int): Number of filtered (matching) results to skip (must be >= 0).

        Returns:
            dict:
            - On success:
              {
                  "success": True,
                  "data": {
                      "total_count": int,      # Number of wallets matching wallet_type (before pagination)
                      "wallets": List[WalletInfo]  # The paginated list of matching wallets (may be empty)
                  }
              }
            - On failure (invalid input):
              {
                  "success": False,
                  "error": str
              }

        Constraints:
            - Only wallets of the requested type are listed.
            - Results must respect the specified limit and offset for pagination.
            - Limit and offset must be non-negative integers.
        """
        if not isinstance(limit, int) or not isinstance(offset, int) or limit < 0 or offset < 0:
            return {
                "success": False,
                "error": "Limit and offset must be non-negative integers"
            }

        # Filter wallets by type
        wallets_of_type = [w for w in self.wallets.values() if w["wallet_type"] == wallet_type]
        total_count = len(wallets_of_type)

        # Paginate
        paginated_wallets = wallets_of_type[offset:offset + limit] if limit > 0 else []

        # Save wallet collection info for reference
        self.last_wallet_collection = {
            "total_count": total_count,
            "wallet_ids": [w["wallet_id"] for w in wallets_of_type]
        }

        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "wallets": paginated_wallets
            }
        }

    def get_wallet_by_id(self, wallet_id: str) -> dict:
        """
        Retrieve detailed information for a wallet given its unique wallet_id.

        Args:
            wallet_id (str): The unique identifier of the wallet.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": WalletInfo  # Wallet metadata info
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Wallet with specified wallet_id does not exist."
                    }

        Constraints:
            - wallet_id must exist in the wallet storage.
        """
        wallet = self.wallets.get(wallet_id)
        if wallet is None:
            return {
                "success": False,
                "error": "Wallet with specified wallet_id does not exist."
            }
        return {
            "success": True,
            "data": wallet
        }

    def get_wallets_by_type(self, wallet_type: str) -> dict:
        """
        Retrieve all wallets of a specified wallet_type (no pagination).

        Args:
            wallet_type (str): The type of wallet to retrieve (e.g., "token forwarding").

        Returns:
            dict: {
                "success": True,
                "data": List[WalletInfo]  # All wallets of given type (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # If wallet_type parameter is missing/invalid
            }

        Constraints:
            - Only wallets where wallet_info["wallet_type"] == wallet_type are included.
            - No pagination; result list can be large.
        """
        if not wallet_type or not isinstance(wallet_type, str):
            return {"success": False, "error": "wallet_type must be a non-empty string"}

        matching_wallets = [
            wallet_info for wallet_info in self.wallets.values()
            if wallet_info["wallet_type"] == wallet_type
        ]

        return {"success": True, "data": matching_wallets}

    def get_wallet_status(self, wallet_id: str) -> dict:
        """
        Query the current status and configuration of a wallet.

        Args:
            wallet_id (str): The unique identifier of the wallet.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "status": str,
                            "configuration": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message, e.g. wallet not found
                    }

        Constraints:
            - The specified wallet must exist in the system.
        """
        wallet = self.wallets.get(wallet_id)
        if not wallet:
            return {"success": False, "error": "Wallet not found"}

        return {
            "success": True,
            "data": {
                "status": wallet["status"],
                "configuration": wallet["configuration"]
            }
        }

    def get_blockchain_address_by_wallet(self, wallet_id: str) -> dict:
        """
        Retrieve the blockchain address information associated with a specific wallet.
    
        Args:
            wallet_id (str): The unique ID of the wallet to query.
        
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": BlockchainAddressInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": <str>  # Reason: Wallet not found, or association missing
                    }
        Constraints:
            - The wallet_id must correspond to an existing wallet.
            - Each wallet can have at most one associated blockchain address.
        """
        if wallet_id not in self.wallets:
            return {"success": False, "error": "Wallet not found"}

        for address, addr_info in self.blockchain_addresses.items():
            if addr_info.get("associated_wallet_id") == wallet_id:
                return {"success": True, "data": addr_info}

        return {"success": False, "error": "No blockchain address associated with this wallet"}

    def get_wallet_by_blockchain_address(self, blockchain_address: str) -> dict:
        """
        Find the wallet associated with a specified blockchain address.

        Args:
            blockchain_address (str): The blockchain address whose wallet should be retrieved.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": WalletInfo
                }
                or
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Each wallet must have a unique blockchain address.
            - Address must exist in the system.
            - The associated wallet_id must exist and point to a wallet.
        """
        addr_info = self.blockchain_addresses.get(blockchain_address)
        if not addr_info:
            return { "success": False, "error": "Blockchain address not found" }
    
        wallet_id = addr_info.get("associated_wallet_id")
        wallet_info = self.wallets.get(wallet_id)
        if not wallet_info:
            return { "success": False, "error": "Associated wallet not found for this address" }
    
        return { "success": True, "data": wallet_info }

    def get_transaction_history_by_wallet(self, wallet_id: str) -> dict:
        """
        Retrieve the list of transactions associated with the specified wallet.

        Args:
            wallet_id (str): The unique identifier of the wallet.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[TransactionInfo]  # Transactions (possibly empty)
                    }
                - On error (wallet does not exist):
                    {
                        "success": False,
                        "error": "Wallet not found"
                    }

        Constraints:
            - The wallet with the given wallet_id must exist.
        """
        if wallet_id not in self.wallets:
            return {"success": False, "error": "Wallet not found"}

        transactions = [
            tx for tx in self.transactions.values()
            if tx["wallet_id"] == wallet_id
        ]

        return {"success": True, "data": transactions}

    def get_wallet_collection_info(self) -> dict:
        """
        Return metadata about the last wallet collection used for pagination/listing.
    
        Returns:
            dict: {
                "success": True,
                "data": WalletCollectionInfo  # {"total_count": int, "wallet_ids": List[str]}
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }
    
        Constraints:
            - None specific; just returns metadata stored in-memory.
        """
        if not hasattr(self, "last_wallet_collection") or self.last_wallet_collection is None:
            return {
                "success": False,
                "error": "No wallet collection info available"
            }
        # Defensive: type check (optional)
        if not isinstance(self.last_wallet_collection, dict):
            return {
                "success": False,
                "error": "Corrupted wallet collection data"
            }
        return {
            "success": True,
            "data": self.last_wallet_collection
        }


    def create_wallet(
        self,
        wallet_type: str,
        blockchain_address: str,
        configuration: str
    ) -> dict:
        """
        Create a new wallet with the specified type, configuration, and unique blockchain address.

        Args:
            wallet_type (str): The type of the wallet (e.g., 'token forwarding', etc.)
            blockchain_address (str): The unique blockchain address to associate with this wallet.
            configuration (str): Configuration information for the wallet.

        Returns:
            dict: 
                Success:
                    {
                        "success": True,
                        "message": "Wallet created",
                        "wallet_id": <wallet_id>,
                        "wallet_info": <WalletInfo>
                    }
                Failure:
                    {
                        "success": False,
                        "error": <error_message>
                    }

        Constraints:
            - blockchain_address must be unique and not already used.
            - Required fields must not be empty.
            - Wallet status is set to 'active' by default.
            - Timestamps ('created_at', 'updated_at') are auto-set to current time (as ISO8601 string).
        """
        # Validate input
        if not wallet_type or not blockchain_address or not configuration:
            return {"success": False, "error": "wallet_type, blockchain_address, and configuration are required"}

        # Enforce blockchain_address uniqueness
        if blockchain_address in self.blockchain_addresses:
            return {"success": False, "error": "Blockchain address already assigned to another wallet"}
    
        # Generate unique wallet_id (UUID4)
        wallet_id = str(uuid.uuid4())

        # Timestamps
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Compose WalletInfo
        wallet_info = {
            "wallet_id": wallet_id,
            "wallet_type": wallet_type,
            "blockchain_address": blockchain_address,
            "configuration": configuration,
            "status": "active",
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        # Add to wallets dict
        self.wallets[wallet_id] = wallet_info

        # Map blockchain_address to wallet
        blockchain_addr_info = {
            "address": blockchain_address,
            "blockchain_type": "",  # Could be an input, but not specified
            "associated_wallet_id": wallet_id
        }
        self.blockchain_addresses[blockchain_address] = blockchain_addr_info

        # Update wallet collection (total_count, wallet_ids)
        self.last_wallet_collection["wallet_ids"].append(wallet_id)
        self.last_wallet_collection["total_count"] += 1

        return {
            "success": True,
            "message": "Wallet created",
            "wallet_id": wallet_id,
            "wallet_info": wallet_info
        }

    def update_wallet_status(self, wallet_id: str, status: str) -> dict:
        """
        Update the status of an existing wallet (e.g., active, enabled, disabled, archived).
    
        Args:
            wallet_id (str): The unique ID of the wallet whose status is to be updated.
            status (str): The new status value. Allowed: "active", "enabled", "disabled", "archived".
    
        Returns:
            dict: Success or failure message.
                - If success: {
                    "success": True,
                    "message": "Wallet status updated successfully."
                  }
                - If failure: {
                    "success": False,
                    "error": <error reason>
                  }
    
        Constraints:
            - Only allows status to be set to "active", "enabled", "disabled", or "archived".
            - The wallet identified by wallet_id must exist.
            - Updates the wallet's 'status' and 'updated_at' fields.
        """
        allowed_statuses = {"active", "enabled", "disabled", "archived"}
        if wallet_id not in self.wallets:
            return { "success": False, "error": "Wallet does not exist." }
        if status not in allowed_statuses:
            return {
                "success": False,
                "error": (
                    f"Invalid status '{status}'. Must be one of: "
                    "active, enabled, disabled, archived."
                ),
            }
    
        now = datetime.utcnow().isoformat() + "Z"
    
        self.wallets[wallet_id]["status"] = status
        self.wallets[wallet_id]["updated_at"] = now
    
        return { "success": True, "message": "Wallet status updated successfully." }


    def update_wallet_configuration(self, wallet_id: str, new_configuration: str) -> dict:
        """
        Update the configuration details for an existing wallet.

        Args:
            wallet_id (str): Unique identifier of the wallet to update.
            new_configuration (str): New configuration string to set.

        Returns:
            dict: {
                "success": True,
                "message": "Wallet configuration updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The wallet with wallet_id must exist.
            - updated_at is set to the current time in ISO format after change.
            - Wallet status and configuration must be consistent with supported API operations (not further specified).
        """
        if wallet_id not in self.wallets:
            return {"success": False, "error": "Wallet does not exist."}

        wallet = self.wallets[wallet_id]
        wallet["configuration"] = new_configuration
        wallet["updated_at"] = datetime.utcnow().isoformat()

        # If additional consistency checks on configuration & status are needed, insert here.

        self.wallets[wallet_id] = wallet
        return {"success": True, "message": "Wallet configuration updated."}

    def assign_blockchain_address(self, wallet_id: str, address: str, blockchain_type: str) -> dict:
        """
        Assign or update the blockchain address associated with a wallet, ensuring uniqueness.

        Args:
            wallet_id (str): The ID of the wallet to assign the address to.
            address (str): The blockchain address to assign.
            blockchain_type (str): The type of blockchain (e.g., "Ethereum").

        Returns:
            dict: Success or error message.
                - On success: { "success": True, "message": "Assigned blockchain address X to wallet Y." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The wallet must exist.
            - The address must not already be assigned to a different wallet.
            - Wallet <-> blockchain address association must be unique.
            - Properly update both wallet and blockchain address entities.
        """
        # Check wallet exists
        if wallet_id not in self.wallets:
            return { "success": False, "error": "Wallet not found" }

        # Check if the address is assigned to any wallet already
        if address in self.blockchain_addresses:
            existing_assoc = self.blockchain_addresses[address]["associated_wallet_id"]
            if existing_assoc != wallet_id:
                return { "success": False, "error": f"Address already assigned to another wallet ({existing_assoc})" }
            # Idempotent update: assigned to same wallet, just update blockchain_type if necessary
            self.blockchain_addresses[address]["blockchain_type"] = blockchain_type
        else:
            # If this wallet already has an address (possibly a different one), remove its entry
            old_address = self.wallets[wallet_id]["blockchain_address"]
            if old_address and old_address != address:
                # Remove the previous blockchain address mapping, if any
                if old_address in self.blockchain_addresses:
                    del self.blockchain_addresses[old_address]
            # Insert new association
            self.blockchain_addresses[address] = {
                "address": address,
                "blockchain_type": blockchain_type,
                "associated_wallet_id": wallet_id
            }

        # Update wallet's blockchain_address field
        self.wallets[wallet_id]["blockchain_address"] = address

        return { "success": True, "message": f"Blockchain address '{address}' assigned to wallet '{wallet_id}'." }

    def delete_wallet(self, wallet_id: str) -> dict:
        """
        Delete an existing wallet (admin level), removing it from collections and releasing associated blockchain address.

        Args:
            wallet_id (str): The ID of the wallet to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Wallet deleted and address released"
            }
            or
            {
                "success": False,
                "error": "Wallet does not exist"
            }

        Constraints:
            - The wallet must exist.
            - Remove wallet from wallets store, collections, and release associated address.
            - The 'admin level' requirement is assumed handled at API layer (not enforced here).
        """
        # 1. Check wallet exists
        if wallet_id not in self.wallets:
            return { "success": False, "error": "Wallet does not exist" }
    
        # 2. Remove wallet from wallet storage
        del self.wallets[wallet_id]
    
        # 3. Remove wallet from last_wallet_collection (if present)
        if wallet_id in self.last_wallet_collection["wallet_ids"]:
            self.last_wallet_collection["wallet_ids"].remove(wallet_id)
            self.last_wallet_collection["total_count"] = len(self.last_wallet_collection["wallet_ids"])
    
        # 4. Release associated blockchain address (if any)
        # Look for any address with associated_wallet_id == wallet_id
        addresses_to_remove = [
            address
            for address, addr_info in self.blockchain_addresses.items()
            if addr_info["associated_wallet_id"] == wallet_id
        ]
        for address in addresses_to_remove:
            del self.blockchain_addresses[address]
    
        return { "success": True, "message": "Wallet deleted and address released" }

    def add_transaction_record(
        self,
        transaction_id: str,
        wallet_id: str,
        from_address: str,
        to_address: str,
        amount: float,
        token_type: str,
        timestamp: str,
        status: str
    ) -> dict:
        """
        Add a new transaction to a wallet's transaction history.

        Args:
            transaction_id (str): Unique identifier for the transaction.
            wallet_id (str): Identifier of the wallet involved in the transaction.
            from_address (str): Source blockchain address.
            to_address (str): Destination blockchain address.
            amount (float): Amount to transfer.
            token_type (str): Kind of cryptocurrency/token.
            timestamp (str): Timestamp (preferably ISO8601) of transaction.
            status (str): Transaction status (e.g., "pending", "completed").

        Returns:
            dict: {
                "success": True,
                "message": "Transaction record added to wallet <wallet_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - wallet_id must exist in self.wallets.
            - transaction_id must be unique in self.transactions.
        """
        if wallet_id not in self.wallets:
            return { "success": False, "error": "Wallet ID does not exist." }
        if transaction_id in self.transactions:
            return { "success": False, "error": "Transaction ID already exists." }

        transaction: TransactionInfo = {
            "transaction_id": transaction_id,
            "wallet_id": wallet_id,
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
            "token_type": token_type,
            "timestamp": timestamp,
            "status": status
        }
        self.transactions[transaction_id] = transaction

        return {
            "success": True,
            "message": f"Transaction record added to wallet {wallet_id}."
        }

    def remove_transaction_record(self, transaction_id: str) -> dict:
        """
        Remove a transaction from the wallet's transaction history (admin/debug action).
    
        Args:
            transaction_id (str): The unique identifier of the transaction to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Transaction record removed successfully."
            }
            or
            {
                "success": False,
                "error": "Transaction record not found."
            }

        Constraints:
            - The transaction must exist; if not, the operation results in an error message.
            - No side-effects or additional consistency actions are specified for this operation.
        """
        if transaction_id not in self.transactions:
            return {"success": False, "error": "Transaction record not found."}

        del self.transactions[transaction_id]
        return {"success": True, "message": "Transaction record removed successfully."}


class CryptoWalletManagementAPI(BaseEnv):
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

    def list_wallets_paginated(self, **kwargs):
        return self._call_inner_tool('list_wallets_paginated', kwargs)

    def list_wallets_by_type_paginated(self, **kwargs):
        return self._call_inner_tool('list_wallets_by_type_paginated', kwargs)

    def get_wallet_by_id(self, **kwargs):
        return self._call_inner_tool('get_wallet_by_id', kwargs)

    def get_wallets_by_type(self, **kwargs):
        return self._call_inner_tool('get_wallets_by_type', kwargs)

    def get_wallet_status(self, **kwargs):
        return self._call_inner_tool('get_wallet_status', kwargs)

    def get_blockchain_address_by_wallet(self, **kwargs):
        return self._call_inner_tool('get_blockchain_address_by_wallet', kwargs)

    def get_wallet_by_blockchain_address(self, **kwargs):
        return self._call_inner_tool('get_wallet_by_blockchain_address', kwargs)

    def get_transaction_history_by_wallet(self, **kwargs):
        return self._call_inner_tool('get_transaction_history_by_wallet', kwargs)

    def get_wallet_collection_info(self, **kwargs):
        return self._call_inner_tool('get_wallet_collection_info', kwargs)

    def create_wallet(self, **kwargs):
        return self._call_inner_tool('create_wallet', kwargs)

    def update_wallet_status(self, **kwargs):
        return self._call_inner_tool('update_wallet_status', kwargs)

    def update_wallet_configuration(self, **kwargs):
        return self._call_inner_tool('update_wallet_configuration', kwargs)

    def assign_blockchain_address(self, **kwargs):
        return self._call_inner_tool('assign_blockchain_address', kwargs)

    def delete_wallet(self, **kwargs):
        return self._call_inner_tool('delete_wallet', kwargs)

    def add_transaction_record(self, **kwargs):
        return self._call_inner_tool('add_transaction_record', kwargs)

    def remove_transaction_record(self, **kwargs):
        return self._call_inner_tool('remove_transaction_record', kwargs)
