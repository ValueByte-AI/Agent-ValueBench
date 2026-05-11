# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



# Represents an ERC-20 token
class TokenInfo(TypedDict):
    token_address: str
    symbol: str
    name: str
    decimal: int

# Represents a token pair and pool
class PairInfo(TypedDict):
    pair_id: str
    token0_address: str
    token1_address: str
    pair_contract_address: str
    reserve0: float
    reserve1: float
    creation_block: int
    metadata: Any  # If more specifics are known, use a TypedDict or dict

# Tracks the enumeration of all pairs on the protocol
class PairRegistryInfo(TypedDict):
    total_pairs: int
    pairs_list: List[str]  # List of pair_contract_address
    last_indexed_block: int

class _GeneratedEnvImpl:
    def __init__(self):
        # Tokens: {token_address: TokenInfo}
        self.tokens: Dict[str, TokenInfo] = {}
        # Pairs: {pair_contract_address: PairInfo}
        self.pairs: Dict[str, PairInfo] = {}
        # Global pair registry (tracks all pairs)
        self.pair_registry: PairRegistryInfo = {
            "total_pairs": 0,
            "pairs_list": [],
            "last_indexed_block": 0
        }
        # Constraint notes:
        # - Each pair must contain two unique token addresses.
        # - No two pairs can exist with the same token0-token1 combination.
        # - PairRegistry must be updated atomically with pair modifications.
        # - Only ERC-20 tokens (must exist in self.tokens) can form a pair.
        # - Reserve values are non-negative (>= 0) and represent actual balances.

    def _find_pair_entry(self, pair_contract_address: str):
        if pair_contract_address in self.pairs:
            return pair_contract_address, self.pairs[pair_contract_address]
        for pair_key, pair_info in self.pairs.items():
            if pair_info.get("pair_contract_address") == pair_contract_address:
                return pair_key, pair_info
        return None, None

    def get_total_pairs(self) -> dict:
        """
        Retrieve the current total number of token pairs tracked in PairRegistry.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": int  # The total number of pairs.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (if PairRegistry is malformed)
            }

        Constraints:
            - Must reflect the current count in self.pair_registry['total_pairs'].
        """
        total_pairs = self.pair_registry.get("total_pairs")
        if not isinstance(total_pairs, int):
            return { "success": False, "error": "Invalid PairRegistry: total_pairs missing or not integer." }
        return { "success": True, "data": total_pairs }

    def list_all_pairs(self) -> dict:
        """
        Return all pair metadata (PairInfo) for every pair on the exchange.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PairInfo]  # List of PairInfo dicts for every pair (possibly empty)
            }

        Edge cases:
            - If no pairs exist, returns an empty list with success.
            - If a pair_contract_address in registry is missing in self.pairs, it is skipped.

        Constraints:
            - Only pairs listed in the pair_registry are returned.
        """
        result = []
        seen_pair_keys = set()
        for pair_address in self.pair_registry["pairs_list"]:
            pair_key, pair_info = self._find_pair_entry(pair_address)
            if pair_info is not None and pair_key not in seen_pair_keys:
                result.append(pair_info)
                seen_pair_keys.add(pair_key)
            # else, skip if inconsistency (should not happen in a correct registry)
        return {"success": True, "data": result}

    def get_pair_by_contract_address(self, pair_contract_address: str) -> dict:
        """
        Retrieve full details of a pair given its pair_contract_address.

        Args:
            pair_contract_address (str): The smart contract address of the pair.

        Returns:
            dict: {
                "success": True,
                "data": PairInfo  # Complete pair information if found
            }
            OR
            {
                "success": False,
                "error": str  # "Pair contract address not found"
            }

        Constraints:
            - Address must exist in current pair registry.
        """
        if pair_contract_address not in self.pair_registry.get("pairs_list", []):
            return { "success": False, "error": "Pair contract address not found" }
        _, pair_info = self._find_pair_entry(pair_contract_address)
        if pair_info is None:
            return { "success": False, "error": "Pair contract address not found" }
        return { "success": True, "data": pair_info }

    def get_pair_by_tokens(self, token0_address: str, token1_address: str) -> dict:
        """
        Retrieve a token pair's info given token0_address and token1_address.

        Args:
            token0_address (str): The first token's ERC-20 address.
            token1_address (str): The second token's ERC-20 address.

        Returns:
            dict:
                - success: True, data: PairInfo (if found)
                - success: False, error: str (if not found)

        Constraints:
            - Only one pair can exist with the given token0-token1 combination (uniqueness).
            - Pair will not exist if token0_address == token1_address, per environmental constraint.

        Note:
            - The match is strict (token0_address, token1_address), not token1-token0 reversed.
            - If no such pair is found, returns error.
        """
        for pair_info in self.pairs.values():
            if (pair_info["token0_address"] == token0_address and
                pair_info["token1_address"] == token1_address):
                return { "success": True, "data": pair_info }

        return { "success": False, "error": "Pair not found" }

    def get_token_info(self, token_address: str) -> dict:
        """
        Retrieve information for an ERC-20 token by its address.

        Args:
            token_address (str): The ERC-20 token address to query.

        Returns:
            dict: {
                "success": True,
                "data": TokenInfo  # Token metadata (symbol, name, decimal, etc.)
            }
            or
            {
                "success": False,
                "error": str  # Reason if not found
            }

        Constraints:
            - Token address must exist in tokens registry (self.tokens).
        """
        token_info = self.tokens.get(token_address)
        if token_info is None:
            return { "success": False, "error": "Token not found" }
        return { "success": True, "data": token_info }

    def list_all_tokens(self) -> dict:
        """
        List all ERC-20 tokens known to the system.

        Returns:
            dict: {
                "success": True,
                "data": List[TokenInfo],  # All known tokens (can be empty)
            }
        """
        tokens_list = list(self.tokens.values())
        return {
            "success": True,
            "data": tokens_list
        }

    def get_pair_reserves(self, pair_contract_address: str) -> dict:
        """
        Query the current reserves for a given pair.

        Args:
            pair_contract_address (str): The contract address of the target pair.

        Returns:
            dict: {
                "success": True,
                "data": { "reserve0": float, "reserve1": float }
            }
            or
            {
                "success": False,
                "error": str  # Reason why the operation failed (e.g., pair not found)
            }

        Constraints:
            - The pair_contract_address must exist in the pairs dictionary.
            - The reserve values will be non-negative and reflect the current pool balances.
        """
        _, pair_info = self._find_pair_entry(pair_contract_address)
        if pair_info is None:
            return { "success": False, "error": "Pair contract address not found" }

        return {
            "success": True,
            "data": {
                "reserve0": pair_info["reserve0"],
                "reserve1": pair_info["reserve1"],
            }
        }

    def get_pairs_by_token(self, token_address: str) -> dict:
        """
        Retrieve all pairs where the specified token address is one of the pair's tokens.

        Args:
            token_address (str): ERC-20 token address to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[PairInfo],  # List of pairs including this token (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # If input is invalid (e.g. blank, not a string)
            }

        Constraints:
            - The token address should be a valid (non-blank) string.
            - Pairs must include the token as token0 or token1 address.
        """
        if not isinstance(token_address, str) or token_address.strip() == "":
            return { "success": False, "error": "Invalid token address" }

        matching_pairs = [
            pair_info for pair_info in self.pairs.values()
            if pair_info["token0_address"] == token_address
            or pair_info["token1_address"] == token_address
        ]

        return { "success": True, "data": matching_pairs }

    def get_pair_registry_info(self) -> dict:
        """
        Retrieve the global PairRegistryInfo, which includes:
          - total_pairs: number of pairs currently registered
          - pairs_list: list of pair_contract_address
          - last_indexed_block: the last block number where the registry was updated

        Args:
            None

        Returns:
            dict:
              - success: True
              - data: PairRegistryInfo (dictionary with total_pairs, pairs_list, last_indexed_block)
            If an unexpected error occurs:
              - success: False
              - error: str
        """
        if not hasattr(self, "pair_registry") or self.pair_registry is None:
            return {"success": False, "error": "Pair registry not initialized."}
        return {"success": True, "data": self.pair_registry}

    def add_pair(
        self,
        token0_address: str,
        token1_address: str,
        pair_contract_address: str,
        creation_block: int,
        metadata: Any = None
    ) -> dict:
        """
        Create a new pair (pool) for two ERC-20 tokens, updating PairRegistry atomically,
        and ensuring uniqueness.

        Args:
            token0_address (str): ERC-20 address for token0.
            token1_address (str): ERC-20 address for token1.
            pair_contract_address (str): Unique contract address for the new pair.
            creation_block (int): Ethereum block number the pair is created at.
            metadata (Any, optional): Additional metadata for the pair.

        Returns:
            dict: 
                { "success": True, "message": "Pair created successfully" }
                or
                { "success": False, "error": "reason" }

        Constraints:
            - Both token addresses must exist in self.tokens.
            - Token addresses must be unique (not the same).
            - No pair with the same token0-token1 combination (regardless of order) may exist.
            - pair_contract_address must not already be used.
            - PairRegistry is updated atomically.
        """
        # Check both tokens exist
        if token0_address not in self.tokens:
            return { "success": False, "error": "token0_address not tracked as ERC-20 token" }
        if token1_address not in self.tokens:
            return { "success": False, "error": "token1_address not tracked as ERC-20 token" }
        # Check uniqueness of token addresses
        if token0_address == token1_address:
            return { "success": False, "error": "Both tokens must be unique addresses" }
        # Check pair_contract_address doesn't already exist
        existing_pair_key, _ = self._find_pair_entry(pair_contract_address)
        if existing_pair_key is not None:
            return { "success": False, "error": "pair_contract_address already exists" }

        # Check uniqueness of token0-token1 combination (regardless of order)
        for pair in self.pairs.values():
            # Compare unordered; Uniswap treats token0/token1 assignment, but no duplicate pairs with same tokens
            tokens_existing = {pair["token0_address"], pair["token1_address"]}
            tokens_new = {token0_address, token1_address}
            if tokens_existing == tokens_new:
                return { "success": False, "error": "A pair with this token combination already exists" }
    
        # Assemble PairInfo, initial reserves are 0
        pair_id = str(len(self.pairs) + 1)  # Simplified ID assignment
        if metadata is None:
            metadata = {}

        new_pair = {
            "pair_id": pair_id,
            "token0_address": token0_address,
            "token1_address": token1_address,
            "pair_contract_address": pair_contract_address,
            "reserve0": 0.0,
            "reserve1": 0.0,
            "creation_block": creation_block,
            "metadata": metadata
        }
        # Atomically update pairs AND pair_registry
        self.pairs[pair_contract_address] = new_pair
        self.pair_registry["pairs_list"].append(pair_contract_address)
        self.pair_registry["total_pairs"] += 1
        self.pair_registry["last_indexed_block"] = max(
            self.pair_registry.get("last_indexed_block", 0),
            creation_block
        )

        return { "success": True, "message": "Pair created successfully" }

    def remove_pair(self, pair_contract_address: str) -> dict:
        """
        Remove (deregister) a pair by its contract address, and update PairRegistry atomically.

        Args:
            pair_contract_address (str): The unique smart contract address identifying the pair to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Pair <address> removed and registry updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Pair must exist in self.pairs.
            - Registry update (removal from pairs_list, decrement total_pairs) is atomic.
            - It is not an error if pair_contract_address is missing from pairs_list (fix inconsistency).
        """
        # Check existence
        pair_key, _ = self._find_pair_entry(pair_contract_address)
        if pair_key is None:
            return { "success": False, "error": "Pair contract address does not exist." }

        # Remove pair
        del self.pairs[pair_key]

        # Atomically update pair registry
        existing_pairs = self.pair_registry["pairs_list"]
        if pair_contract_address in existing_pairs:
            self.pair_registry["pairs_list"] = [
                addr for addr in existing_pairs if addr != pair_contract_address
            ]
            self.pair_registry["total_pairs"] -= 1
        else:
            # Missing from registry -- fix: just ensure registry is correct
            self.pair_registry["pairs_list"] = [
                addr for addr in existing_pairs if addr != pair_contract_address
            ]
            # Don't decrement below zero
            if self.pair_registry["total_pairs"] > 0:
                self.pair_registry["total_pairs"] -= 1

        return {
            "success": True,
            "message": f"Pair {pair_contract_address} removed and registry updated."
        }

    def update_pair_reserves(
        self,
        pair_contract_address: str,
        reserve0: float,
        reserve1: float
    ) -> dict:
        """
        Modify the reserves (reserve0/reserve1) of a given pair.

        Args:
            pair_contract_address (str): The smart contract address identifier of the pair.
            reserve0 (float): New reserve amount for token0 (must be non-negative).
            reserve1 (float): New reserve amount for token1 (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Reserves updated successfully."
            } on success, or
            {
                "success": False,
                "error": "reason"
            } on error.

        Constraints:
            - The pair must exist (by contract address).
            - Both reserves must be non-negative.
            - State is updated atomically.
        """
        _, pair = self._find_pair_entry(pair_contract_address)
        if pair is None:
            return { "success": False, "error": "Pair does not exist." }
        if not (isinstance(reserve0, (int, float)) and isinstance(reserve1, (int, float))):
            return { "success": False, "error": "Reserve values must be numeric." }
        if reserve0 < 0 or reserve1 < 0:
            return { "success": False, "error": "Reserve values must be non-negative." }

        # Update reserves atomically
        pair["reserve0"] = float(reserve0)
        pair["reserve1"] = float(reserve1)
        # If additional state change events are tracked, they would be handled here.

        return { "success": True, "message": "Reserves updated successfully." }

    def add_token(self,
                  token_address: str,
                  symbol: str,
                  name: str,
                  decimal: int) -> dict:
        """
        Register a new ERC-20 token in the token list.

        Args:
            token_address (str): The unique address of the ERC-20 token.
            symbol (str): The token's symbol.
            name (str): The token's name.
            decimal (int): Number of decimals for the token. Must be positive.

        Returns:
            dict: {
                "success": True,
                "message": "Token <symbol> registered successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - token_address must be unique (not already present in self.tokens).
            - symbol, name, token_address must be non-empty strings.
            - decimal must be a positive integer.
        """
        if not token_address or not isinstance(token_address, str):
            return {"success": False, "error": "Invalid token address."}
        if token_address in self.tokens:
            return {"success": False, "error": "Token already exists."}
        if not symbol or not isinstance(symbol, str):
            return {"success": False, "error": "Invalid token symbol."}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid token name."}
        if not isinstance(decimal, int) or decimal <= 0:
            return {"success": False, "error": "Decimal must be a positive integer."}

        # Register the token
        self.tokens[token_address] = {
            "token_address": token_address,
            "symbol": symbol,
            "name": name,
            "decimal": decimal,
        }
        return {"success": True, "message": f"Token {symbol} registered successfully."}

    def update_pair_metadata(self, pair_contract_address: str, metadata: Any) -> dict:
        """
        Update the metadata field for the given pair.

        Args:
            pair_contract_address (str): The contract address (unique identifier) for the pair.
            metadata (Any): The new metadata object/value to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Pair metadata updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The specified pair must exist.
            - Metadata can have any valid value.
        """
        pair_key, pair = self._find_pair_entry(pair_contract_address)
        if pair_key is None:
            return { "success": False, "error": "Pair with provided contract address does not exist." }

        pair["metadata"] = metadata

        return { "success": True, "message": "Pair metadata updated." }

    def set_last_indexed_block(self, block_number: int) -> dict:
        """
        Update the last_indexed_block of the PairRegistry.
    
        Args:
            block_number (int): The new block number to be set.
    
        Returns:
            dict: {
                "success": True,
                "message": "last_indexed_block updated to <block_number>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - block_number must be an integer and non-negative.
            - block_number should not decrease (must be >= current last_indexed_block).
        """
        if not isinstance(block_number, int):
            return {"success": False, "error": "block_number must be an integer"}
        if block_number < 0:
            return {"success": False, "error": "block_number must be non-negative"}
        current_block = self.pair_registry.get("last_indexed_block", 0)
        if block_number < current_block:
            return {
                "success": False,
                "error": f"block_number {block_number} cannot be less than current last_indexed_block {current_block}"
            }
        self.pair_registry["last_indexed_block"] = block_number
        return {
            "success": True,
            "message": f"last_indexed_block updated to {block_number}"
        }


class UniswapV2Exchange(BaseEnv):
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

    def get_total_pairs(self, **kwargs):
        return self._call_inner_tool('get_total_pairs', kwargs)

    def list_all_pairs(self, **kwargs):
        return self._call_inner_tool('list_all_pairs', kwargs)

    def get_pair_by_contract_address(self, **kwargs):
        return self._call_inner_tool('get_pair_by_contract_address', kwargs)

    def get_pair_by_tokens(self, **kwargs):
        return self._call_inner_tool('get_pair_by_tokens', kwargs)

    def get_token_info(self, **kwargs):
        return self._call_inner_tool('get_token_info', kwargs)

    def list_all_tokens(self, **kwargs):
        return self._call_inner_tool('list_all_tokens', kwargs)

    def get_pair_reserves(self, **kwargs):
        return self._call_inner_tool('get_pair_reserves', kwargs)

    def get_pairs_by_token(self, **kwargs):
        return self._call_inner_tool('get_pairs_by_token', kwargs)

    def get_pair_registry_info(self, **kwargs):
        return self._call_inner_tool('get_pair_registry_info', kwargs)

    def add_pair(self, **kwargs):
        return self._call_inner_tool('add_pair', kwargs)

    def remove_pair(self, **kwargs):
        return self._call_inner_tool('remove_pair', kwargs)

    def update_pair_reserves(self, **kwargs):
        return self._call_inner_tool('update_pair_reserves', kwargs)

    def add_token(self, **kwargs):
        return self._call_inner_tool('add_token', kwargs)

    def update_pair_metadata(self, **kwargs):
        return self._call_inner_tool('update_pair_metadata', kwargs)

    def set_last_indexed_block(self, **kwargs):
        return self._call_inner_tool('set_last_indexed_block', kwargs)
