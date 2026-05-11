# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Tuple, TypedDict

from .BaseEnv import BaseEnv



# TypedDicts for each entity

class UserInfo(TypedDict):
    _id: str
    username: str
    account_sta: str  # Watch for original naming ("account_status")

class AccountBalanceInfo(TypedDict):
    _id: str
    asset_symbol: str
    balance_available: float
    balance_reserved: float

class OrderInfo(TypedDict):
    order_id: str
    user_id: str
    order_type: str   # e.g., 'limit', 'market'
    side: str         # 'buy' or 'sell'
    asset_symbol: str
    quote_symbol: str
    quantity: float
    price: float
    quantity_remaining: float
    status: str
    timestamp: float

class OrderBookInfo(TypedDict):
    asset_symbol: str
    quote_symbol: str
    bids: List[OrderInfo]
    asks: List[OrderInfo]

class TradeInfo(TypedDict):
    trade_id: str
    buy_order_id: str
    sell_order_id: str
    asset_symbol: str
    quote_symbol: str
    quantity: float
    price: float
    timestamp: float

class TransactionHistoryInfo(TypedDict):
    _id: str
    transaction_id: str
    asset_symbol: str
    type: str  # 'deposit', 'withdrawal', 'trade', 'fee'
    amount: float
    timestamp: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Cryptocurrency exchange trading environment state structure.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Account balances: {(user_id, asset_symbol): AccountBalanceInfo}
        self.balances: Dict[Tuple[str, str], AccountBalanceInfo] = {}

        # Orders: {order_id: OrderInfo}
        self.orders: Dict[str, OrderInfo] = {}

        # Order books: {(asset_symbol, quote_symbol): OrderBookInfo}
        # Each book contains 'bids' (buy order list) and 'asks' (sell order list).
        self.order_books: Dict[Tuple[str, str], OrderBookInfo] = {}

        # Trades: {trade_id: TradeInfo}
        self.trades: Dict[str, TradeInfo] = {}

        # Transaction histories: {user_id: [TransactionHistoryInfo]}
        self.transaction_histories: Dict[str, List[TransactionHistoryInfo]] = {}

        # --- Constraints ---
        # - Users must have sufficient available balance to place buy and sell orders (reserve funds on order placement).
        # - Order book must remain sorted by price and timestamp for correct matching.
        # - Orders can only be matched according to order type and best price logic.
        # - Only valid trading pairs can have order books and trades.
        # - Balance and order state updates must be atomic to prevent inconsistent states.

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user details by username.

        Args:
            username (str): The username to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # User information dictionary
            }
            or
            {
                "success": False,
                "error": str,  # Error message if no such user
            }

        Constraints:
            - Username must match exactly (case-sensitive).
        """
        for user_info in self.users.values():
            if user_info.get("username") == username:
                return {"success": True, "data": user_info}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details for the given internal _id.

        Args:
            user_id (str): The internal unique user identifier.

        Returns:
            dict: 
                { "success": True, "data": UserInfo } if user exists,
                { "success": False, "error": "User not found" } otherwise.

        Constraints:
            - user_id must exist in the exchange system.
            - No permission or authentication checks are performed at this layer.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_account_balance(self, user_id: str, asset_symbol: str) -> dict:
        """
        Check a user's available and reserved balance for a given asset.

        Args:
            user_id (str): The user's unique identifier.
            asset_symbol (str): The asset code, e.g. 'BTC', 'USD'.

        Returns:
            dict: {
                "success": True,
                "data": AccountBalanceInfo,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Account balance must exist for the given (user_id, asset_symbol).
        """
        key = (user_id, asset_symbol)
        if key not in self.balances:
            return { "success": False, "error": "Balance entry not found for user or asset" }
        return {
            "success": True,
            "data": self.balances[key]
        }

    def get_all_balances_for_user(self, user_id: str) -> dict:
        """
        Retrieve all asset balances for a given user.

        Args:
            user_id (str): The user ID to query balances for.

        Returns:
            dict: {
                "success": True,
                "data": List[AccountBalanceInfo],  # All balances for user (may be empty if no balances)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user does not exist)
            }

        Constraints:
            - User must exist.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        balances = [
            balance_info for (uid, _), balance_info in self.balances.items()
            if uid == user_id
        ]
        return { "success": True, "data": balances }

    def get_order_by_id(self, order_id: str) -> dict:
        """
        Fetch full data for a given order by its unique order_id.

        Args:
            order_id (str): The unique identifier of the order.

        Returns:
            dict: {
                "success": True,
                "data": OrderInfo  # Full order information
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. order not found
            }

        Constraints:
            - order_id must exist in the system.
        """
        if order_id not in self.orders:
            return {"success": False, "error": "Order not found"}

        order_info = self.orders[order_id]

        return {"success": True, "data": order_info}

    def list_open_orders_for_user(self, user_id: str) -> dict:
        """
        List all currently open orders for the specified user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[OrderInfo]  # List of the user's open orders (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # "User does not exist"
                    }
        Constraints:
            - user_id must reference an existing user.
            - Only orders with status 'open' (and/or 'active') are included.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Assuming 'open' status defines open orders (adapt as needed for other status values)
        open_statuses = {'open', 'active'}
        open_orders = [
            order for order in self.orders.values()
            if order["user_id"] == user_id and order["status"] in open_statuses
        ]

        return { "success": True, "data": open_orders }

    def list_orders_by_status(
        self,
        status: str,
        user_id: str = None,
        asset_symbol: str = None,
        quote_symbol: str = None
    ) -> dict:
        """
        List orders filtered by status, with optional user or trading pair constraint.

        Args:
            status (str): Order status to filter (e.g., 'open', 'filled').
            user_id (str, optional): User ID to filter orders for. If None, all users included.
            asset_symbol (str, optional): Base asset symbol for trading pair. Must be provided together with quote_symbol.
            quote_symbol (str, optional): Quote asset symbol for trading pair.

        Returns:
            dict: {
                "success": True,
                "data": List[OrderInfo]  # All orders matching the given filters.
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If filtering by user, user_id must exist.
            - If filtering by trading pair, asset_symbol and quote_symbol must both be provided and be a valid trading pair.
        """
        # Validate input
        if not status:
            return {"success": False, "error": "Missing required parameter: status"}

        # Check user existence if user_id provided
        if user_id is not None and user_id not in self.users:
            return {"success": False, "error": "User not found"}

        # Check trading pair existence if asset_symbol and quote_symbol provided
        if (asset_symbol is not None or quote_symbol is not None):
            if asset_symbol is None or quote_symbol is None:
                return {"success": False, "error": "Both asset_symbol and quote_symbol must be provided for trading pair filter"}
            pair = (asset_symbol, quote_symbol)
            if pair not in self.order_books:
                return {"success": False, "error": "Trading pair does not exist"}

        # Gather filtered orders
        result = []
        for order in self.orders.values():
            if order['status'] != status:
                continue
            if user_id is not None and order['user_id'] != user_id:
                continue
            if asset_symbol is not None and quote_symbol is not None:
                if order['asset_symbol'] != asset_symbol or order['quote_symbol'] != quote_symbol:
                    continue
            result.append(order)

        return {"success": True, "data": result}

    def get_order_book(self, asset_symbol: str, quote_symbol: str) -> dict:
        """
        Retrieve the order book for a specific trading pair (asset_symbol, quote_symbol).

        Args:
            asset_symbol (str): The base asset symbol (e.g., 'BTC').
            quote_symbol (str): The quote/counter asset symbol (e.g., 'USD').

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": OrderBookInfo  # Includes sorted 'bids' and 'asks'
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Trading pair does not exist"
                    }

        Constraints:
            - Only valid trading pairs may have order books and trades.
            - Order book should present 'bids' and 'asks' lists sorted by price then timestamp.
        """
        key = (asset_symbol, quote_symbol)
        if key not in self.order_books:
            return { "success": False, "error": "Trading pair does not exist" }
    
        order_book = self.order_books[key]
        # Defensive: Re-sort just in case (should already be sorted by constraints)
        order_book_sorted = {
            'asset_symbol': order_book['asset_symbol'],
            'quote_symbol': order_book['quote_symbol'],
            'bids': sorted(
                order_book['bids'],
                key=lambda o: (-o['price'], o['timestamp'])
            ),
            'asks': sorted(
                order_book['asks'],
                key=lambda o: (o['price'], o['timestamp'])
            ),
        }
        return { "success": True, "data": order_book_sorted }

    def get_order_book_top_n(self, asset_symbol: str, quote_symbol: str, n: int) -> dict:
        """
        Retrieve the top N bids and asks for a specified trading pair's order book.

        Args:
            asset_symbol (str): The asset symbol (e.g., 'BTC').
            quote_symbol (str): The quote symbol (e.g., 'USD').
            n (int): The number of top bids and asks to fetch.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "bids": List[OrderInfo],
                    "asks": List[OrderInfo],
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Trading pair must exist.
            - n must be a positive integer.
        """
        if not isinstance(n, int) or n <= 0:
            return {"success": False, "error": "N must be a positive integer"}

        key = (asset_symbol, quote_symbol)
        order_book = self.order_books.get(key)
        if not order_book:
            return {"success": False, "error": "Trading pair does not exist"}

        bids = order_book.get("bids", [])[:n]
        asks = order_book.get("asks", [])[:n]

        return {"success": True, "data": {"bids": bids, "asks": asks}}

    def get_trade_by_id(self, trade_id: str) -> dict:
        """
        Retrieve details of a trade by its trade_id.

        Args:
            trade_id (str): Unique identifier of the trade.

        Returns:
            dict:
                - success (bool): True if trade is found, else False.
                - data (TradeInfo): Trade details (if found).
                - error (str): If not found, reason for failure.

        Constraints:
            - The trade_id must exist in the system's self.trades dict.
        """
        trade = self.trades.get(trade_id)
        if trade is None:
            return { "success": False, "error": "Trade not found" }
        return { "success": True, "data": trade }

    def list_trades_for_user(self, user_id: str) -> dict:
        """
        List all trades in which the user (by user_id) was either the buyer or seller.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                - success: True if retrieval succeeded, with 'data' containing a list of TradeInfo,
                          or False with 'error' set if user does not exist.

        Constraints:
            - Returns trades where the user participated as buyer or seller.
            - If user does not exist, returns error.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        result = []
        for trade in self.trades.values():
            buy_order_id = trade.get("buy_order_id")
            sell_order_id = trade.get("sell_order_id")
            buy_order = self.orders.get(buy_order_id)
            sell_order = self.orders.get(sell_order_id)
            # Defensive: if order info was deleted somehow, skip that trade
            if buy_order and buy_order.get("user_id") == user_id:
                result.append(trade)
            elif sell_order and sell_order.get("user_id") == user_id:
                result.append(trade)
            # no else — skip if neither
        return { "success": True, "data": result }

    def get_transaction_history(self, user_id: str) -> dict:
        """
        Fetch the complete transaction history for the specified user, including deposits,
        withdrawals, trades, fees, etc.

        Args:
            user_id (str): The user ID whose transaction history to fetch.

        Returns:
            dict: {
                "success": True,
                "data": List[TransactionHistoryInfo],  # Maybe empty if no transactions
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - user_id must correspond to an existing user in the system.
            - If the user exists but has no transactions, return an empty data list (success).
        """
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        txns = self.transaction_histories.get(user_id, [])
        return { "success": True, "data": txns }

    def verify_trading_pair(self, asset_symbol: str, quote_symbol: str) -> dict:
        """
        Check whether the specified asset/quote symbol trading pair is supported
        (i.e., has an order book, hence trading is enabled).

        Args:
            asset_symbol (str): The base asset symbol (e.g., 'BTC').
            quote_symbol (str): The quote currency symbol (e.g., 'USD').

        Returns:
            dict:
                {
                    "success": True,
                    "supported": bool  # True if the trading pair exists/supported.
                }
        Constraints:
            - No permission checking.
            - Just checks for existence in self.order_books as the indicator for support.
        """
        supported = (asset_symbol, quote_symbol) in self.order_books
        return { "success": True, "supported": supported }

    def place_limit_order(
        self,
        user_id: str,
        side: str,
        asset_symbol: str,
        quote_symbol: str,
        quantity: float,
        price: float
    ) -> dict:
        """
        Places a new limit order (buy or sell), reserves necessary funds, inserts the order
        into the order book, and updates account balances atomically.

        Args:
            user_id (str): ID of the user placing the order.
            side (str): 'buy' or 'sell'.
            asset_symbol (str): Symbol of asset being traded (e.g., 'BTC').
            quote_symbol (str): Symbol of quote currency (e.g., 'USDT').
            quantity (float): Amount of asset to buy/sell.
            price (float): Limit price.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Limit order placed.",
                    "order": <OrderInfo>
                }
                OR
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - User/account/trading pair must exist and be active.
            - quantity and price must be > 0.
            - User must have sufficient available funds (buy: quote, sell: asset).
            - The operation is atomic: on failure, no state is changed.
            - Funds must be reserved.
            - Order is placed in correct sorted book.
        """

        # Validate user
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }
        if user.get("account_sta", "active") != "active":
            return { "success": False, "error": "User account not active" }

        # Validate symbols and trading pair
        book_key = (asset_symbol, quote_symbol)
        order_book = self.order_books.get(book_key)
        if order_book is None:
            return { "success": False, "error": "Invalid or unsupported trading pair" }

        # Validate order parameters
        if side not in ("buy", "sell"):
            return { "success": False, "error": "Side must be 'buy' or 'sell'" }
        if (not isinstance(quantity, (float,int))) or quantity <= 0:
            return { "success": False, "error": "Quantity must be positive" }
        if (not isinstance(price, (float,int))) or price <= 0:
            return { "success": False, "error": "Price must be positive" }

        # Sufficient balance check and reservation
        if side == "buy":
            reserve_asset = quote_symbol
            required = price * quantity
        else:  # sell
            reserve_asset = asset_symbol
            required = quantity

        bal_key = (user_id, reserve_asset)
        balance = self.balances.get(bal_key)
        if balance is None:
            return { "success": False, "error": f"No balance entry for {reserve_asset}" }
        if balance["balance_available"] < required:
            return { "success": False, "error": f"Insufficient balance in {reserve_asset}" }

        # --- ATOMIC begin: update balances and insert order ---
        # Reserve funds
        new_bal_avail = balance["balance_available"] - required
        new_bal_reserved = balance["balance_reserved"] + required

        # Generate unique order_id
        order_id = str(uuid.uuid4())
        ts = time.time()

        order = {
            "order_id": order_id,
            "user_id": user_id,
            "order_type": "limit",
            "side": side,
            "asset_symbol": asset_symbol,
            "quote_symbol": quote_symbol,
            "quantity": quantity,
            "price": price,
            "quantity_remaining": quantity,
            "status": "open",
            "timestamp": ts
        }

        # Update the balance atomically
        balance["balance_available"] = new_bal_avail
        balance["balance_reserved"] = new_bal_reserved

        # Place in order book
        if side == "buy":
            order_book["bids"].append(order)
            # sort: highest price, then earliest time
            order_book["bids"].sort(key=lambda o: (-o["price"], o["timestamp"]))
        else:
            order_book["asks"].append(order)
            # sort: lowest price, then earliest time
            order_book["asks"].sort(key=lambda o: (o["price"], o["timestamp"]))

        # Add to system-wide order registry
        self.orders[order_id] = order

        return {
            "success": True,
            "message": "Limit order placed.",
            "order": order
        }

    def place_market_order(
        self,
        user_id: str,
        side: str,
        asset_symbol: str,
        quote_symbol: str,
        quantity: float
    ) -> dict:
        """
        Place a market order for the given user and attempt to immediately match it against the order book.
        All affected balances, order statuses, and records are updated atomically.

        Args:
            user_id (str): ID of the user placing the order.
            side (str): 'buy' or 'sell'.
            asset_symbol (str): Symbol of asset to buy or sell.
            quote_symbol (str): Symbol of quote asset (currency to pay/receive).
            quantity (float): Quantity to buy/sell (must be positive).

        Returns:
            dict: {
                "success": True,
                "message": "Market order executed and matched",
                "order_id": str,
                "trades": List[TradeInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Trading pair must exist.
            - Quantity must be positive.
            - User must have sufficient available balance (quote for buy; asset for sell).
            - Order matching, balance updates and trade records are atomic.
        """

        # 1. Validation
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}

        trading_pair = (asset_symbol, quote_symbol)
        if trading_pair not in self.order_books:
            return {"success": False, "error": "Trading pair not supported"}

        order_book = self.order_books[trading_pair]
        now = time.time()
        trades = []
        order_id = f"order_{str(len(self.orders)+1)}_{int(now*1000)}"

        # 2. Check balance sufficiency
        if side == 'buy':
            # We'll need to estimate how much quote asset will be spent for up to 'quantity' asset
            asks = sorted(order_book['asks'], key=lambda o: (o['price'], o['timestamp']))  # Lowest price first
            remaining_qty = quantity
            total_cost = 0.0
            for ask in asks:
                fill_qty = min(remaining_qty, ask['quantity_remaining'])
                total_cost += fill_qty * ask['price']
                remaining_qty -= fill_qty
                if remaining_qty <= 1e-12:  # Floating-point margin
                    break
            if remaining_qty > 1e-12:  # Not enough liquidity
                return {"success": False, "error": "Insufficient order book liquidity to fulfill buy order"}
            balance_key = (user_id, quote_symbol)
            user_balance = self.balances.get(balance_key)
            if not user_balance or user_balance['balance_available'] < total_cost - 1e-8:
                return {"success": False, "error": "Insufficient quote asset balance"}
        elif side == 'sell':
            bids = sorted(order_book['bids'], key=lambda o: (-o['price'], o['timestamp']))  # Highest price first
            remaining_qty = quantity
            total_to_receive = 0.0
            for bid in bids:
                fill_qty = min(remaining_qty, bid['quantity_remaining'])
                total_to_receive += fill_qty * bid['price']
                remaining_qty -= fill_qty
                if remaining_qty <= 1e-12:
                    break
            if remaining_qty > 1e-12:
                return {"success": False, "error": "Insufficient order book liquidity to fulfill sell order"}
            balance_key = (user_id, asset_symbol)
            user_balance = self.balances.get(balance_key)
            if not user_balance or user_balance['balance_available'] < quantity - 1e-8:
                return {"success": False, "error": "Insufficient asset balance for sell order"}
        else:
            return {"success": False, "error": "Order side must be 'buy' or 'sell'"}

        # --- Begin atomic update (simulate with deepcopy as transaction) ---
        original_orders = deepcopy(self.orders)
        original_balances = deepcopy(self.balances)
        original_order_books = deepcopy(self.order_books)
        original_trades = deepcopy(self.trades)
        original_histories = deepcopy(self.transaction_histories)

        try:
            new_order = {
                "order_id": order_id,
                "user_id": user_id,
                "order_type": "market",
                "side": side,
                "asset_symbol": asset_symbol,
                "quote_symbol": quote_symbol,
                "quantity": quantity,
                "price": 0.0,  # Market price is set per match.
                "quantity_remaining": quantity,
                "status": "open",
                "timestamp": now
            }
            self.orders[order_id] = new_order

            matched_qty = 0.0
            if side == 'buy':
                # Buyer consuming lowest ask(s)
                asks = sorted(order_book['asks'], key=lambda o: (o['price'], o['timestamp']))
                remaining_qty = quantity
                for ask in asks:
                    if remaining_qty <= 1e-12:
                        break
                    match_qty = min(remaining_qty, ask['quantity_remaining'])
                    trade_price = ask['price']
                    ask_user_id = ask['user_id']
                    # Update balances
                    cost = match_qty * trade_price
                    # Buyer's quote goes down, buyer's asset goes up
                    self.balances[(user_id, quote_symbol)]['balance_available'] -= cost
                    self.balances[(user_id, asset_symbol)] = self.balances.get((user_id, asset_symbol),
                        {
                            "_id": user_id + '_' + asset_symbol,
                            "asset_symbol": asset_symbol,
                            "balance_available": 0.0,
                            "balance_reserved": 0.0
                        }
                    )
                    self.balances[(user_id, asset_symbol)]['balance_available'] += match_qty
                    # Seller's asset reserved goes down, seller's quote goes up
                    self.balances[(ask_user_id, asset_symbol)]['balance_reserved'] -= match_qty
                    self.balances[(ask_user_id, quote_symbol)] = self.balances.get((ask_user_id, quote_symbol),
                        {
                            "_id": ask_user_id + '_' + quote_symbol,
                            "asset_symbol": quote_symbol,
                            "balance_available": 0.0,
                            "balance_reserved": 0.0
                        }
                    )
                    self.balances[(ask_user_id, quote_symbol)]['balance_available'] += cost

                    # Update orders/books
                    ask['quantity_remaining'] -= match_qty
                    new_order['quantity_remaining'] -= match_qty
                    remaining_qty -= match_qty
                    if abs(ask['quantity_remaining']) < 1e-10:
                        ask['status'] = 'filled'
                    else:
                        ask['status'] = 'partially_filled'
                    matched_qty += match_qty

                    # Trade record
                    trade_id = f"trade_{str(len(self.trades)+1)}_{int(time.time()*1000)}"
                    trade_info = {
                        "trade_id": trade_id,
                        "buy_order_id": order_id,
                        "sell_order_id": ask['order_id'],
                        "asset_symbol": asset_symbol,
                        "quote_symbol": quote_symbol,
                        "quantity": match_qty,
                        "price": trade_price,
                        "timestamp": time.time()
                    }
                    self.trades[trade_id] = trade_info
                    trades.append(trade_info)
                    # Transaction history for both users
                    for uid, symbol, amount, ttype in [
                            (user_id, quote_symbol, -cost, "trade"),
                            (user_id, asset_symbol, match_qty, "trade"),
                            (ask_user_id, asset_symbol, -match_qty, "trade"),
                            (ask_user_id, quote_symbol, cost, "trade")]:
                        hist = {
                            "_id": uid + '_' + trade_id + '_' + symbol,
                            "transaction_id": trade_id,
                            "asset_symbol": symbol,
                            "type": ttype,
                            "amount": amount,
                            "timestamp": time.time()
                        }
                        self.transaction_histories.setdefault(uid, []).append(hist)
                    if abs(new_order['quantity_remaining']) < 1e-10:
                        new_order['status'] = 'filled'
                        break
                # Remove fully filled asks from orderbook
                self.order_books[trading_pair]['asks'] = [
                    o for o in self.order_books[trading_pair]['asks'] if o['quantity_remaining'] > 1e-10
                ]
            else:  # side == 'sell'
                bids = sorted(order_book['bids'], key=lambda o: (-o['price'], o['timestamp']))
                remaining_qty = quantity
                for bid in bids:
                    if remaining_qty <= 1e-12:
                        break
                    match_qty = min(remaining_qty, bid['quantity_remaining'])
                    trade_price = bid['price']
                    bid_user_id = bid['user_id']
                    proceeds = match_qty * trade_price
                    # Seller's asset goes down, seller's quote goes up
                    self.balances[(user_id, asset_symbol)]['balance_available'] -= match_qty
                    self.balances[(user_id, quote_symbol)] = self.balances.get((user_id, quote_symbol),
                        {
                            "_id": user_id + '_' + quote_symbol,
                            "asset_symbol": quote_symbol,
                            "balance_available": 0.0,
                            "balance_reserved": 0.0
                        }
                    )
                    self.balances[(user_id, quote_symbol)]['balance_available'] += proceeds
                    # Buyer's quote reserved goes down, buyer's asset goes up
                    self.balances[(bid_user_id, quote_symbol)]['balance_reserved'] -= proceeds
                    self.balances[(bid_user_id, asset_symbol)] = self.balances.get((bid_user_id, asset_symbol),
                        {
                            "_id": bid_user_id + '_' + asset_symbol,
                            "asset_symbol": asset_symbol,
                            "balance_available": 0.0,
                            "balance_reserved": 0.0
                        }
                    )
                    self.balances[(bid_user_id, asset_symbol)]['balance_available'] += match_qty

                    bid['quantity_remaining'] -= match_qty
                    new_order['quantity_remaining'] -= match_qty
                    remaining_qty -= match_qty
                    if abs(bid['quantity_remaining']) < 1e-10:
                        bid['status'] = 'filled'
                    else:
                        bid['status'] = 'partially_filled'
                    matched_qty += match_qty

                    # Trade record
                    trade_id = f"trade_{str(len(self.trades)+1)}_{int(time.time()*1000)}"
                    trade_info = {
                        "trade_id": trade_id,
                        "buy_order_id": bid['order_id'],
                        "sell_order_id": order_id,
                        "asset_symbol": asset_symbol,
                        "quote_symbol": quote_symbol,
                        "quantity": match_qty,
                        "price": trade_price,
                        "timestamp": time.time()
                    }
                    self.trades[trade_id] = trade_info
                    trades.append(trade_info)
                    for uid, symbol, amount, ttype in [
                            (user_id, asset_symbol, -match_qty, "trade"),
                            (user_id, quote_symbol, proceeds, "trade"),
                            (bid_user_id, quote_symbol, -proceeds, "trade"),
                            (bid_user_id, asset_symbol, match_qty, "trade")]:
                        hist = {
                            "_id": uid + '_' + trade_id + '_' + symbol,
                            "transaction_id": trade_id,
                            "asset_symbol": symbol,
                            "type": ttype,
                            "amount": amount,
                            "timestamp": time.time()
                        }
                        self.transaction_histories.setdefault(uid, []).append(hist)
                    if abs(new_order['quantity_remaining']) < 1e-10:
                        new_order['status'] = 'filled'
                        break
                # Remove fully filled bids from orderbook
                self.order_books[trading_pair]['bids'] = [
                    o for o in self.order_books[trading_pair]['bids'] if o['quantity_remaining'] > 1e-10
                ]

            if abs(new_order['quantity_remaining']) < 1e-10:
                new_order['status'] = 'filled'
            else:
                new_order['status'] = 'cancelled'  # Market order unfilled portion is cancelled

            # Update in main order table
            self.orders[order_id] = new_order

            return {
                "success": True,
                "message": "Market order executed and matched",
                "order_id": order_id,
                "trades": trades
            }
        except Exception as e:
            # Rollback to atomicity
            self.orders = original_orders
            self.balances = original_balances
            self.order_books = original_order_books
            self.trades = original_trades
            self.transaction_histories = original_histories
            return {"success": False, "error": "Internal error: " + str(e)}

    def cancel_order(self, order_id: str) -> dict:
        """
        Attempt to cancel a user's open order by order_id if eligible.
        Releases any reserved funds back to the user's available balance.

        Args:
            order_id (str): The unique identifier of the order to cancel.

        Returns:
            dict:
                - If successful:
                    { "success": True, "message": "Order <order_id> cancelled and funds released." }
                - If error:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Only 'open' or 'partially_filled' orders can be cancelled.
            - Funds or assets reserved for the order must be atomically released.
            - Order is removed from the order book.
            - Proper state is preserved if order not eligible for cancellation.
        """

        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order not found." }

        if order["status"] not in ["open", "partially_filled"]:
            return { "success": False, "error": f"Order cannot be cancelled in its current status: {order['status']}" }

        user_id = order["user_id"]
        side = order["side"]
        asset_symbol = order["asset_symbol"]
        quote_symbol = order["quote_symbol"]
        quantity_remaining = order["quantity_remaining"]
        price = order["price"]
        pair_key = (asset_symbol, quote_symbol)

        # Remove order from order book
        order_book = self.order_books.get(pair_key)
        if not order_book:
            return { "success": False, "error": "Order book for this trading pair does not exist." }

        removed = False
        if side == "buy":
            new_bids = [o for o in order_book["bids"] if o["order_id"] != order_id]
            if len(new_bids) != len(order_book["bids"]):
                order_book["bids"] = new_bids
                removed = True
        elif side == "sell":
            new_asks = [o for o in order_book["asks"] if o["order_id"] != order_id]
            if len(new_asks) != len(order_book["asks"]):
                order_book["asks"] = new_asks
                removed = True
        else:
            return { "success": False, "error": f"Unknown order side '{side}'" }

        if not removed:
            return { "success": False, "error": "Order not found in order book (may already be cancelled or filled)." }

        # Release reserved funds/assets
        if side == "buy":
            # For buy: reserved quote currency for remaining amount
            reserved_key = (user_id, quote_symbol)
            reserved_info = self.balances.get(reserved_key)
            reserved_amount = quantity_remaining * price
            if reserved_info:
                reserved_released = min(reserved_info["balance_reserved"], reserved_amount)
                reserved_info["balance_reserved"] -= reserved_released
                reserved_info["balance_available"] += reserved_released
            # If balance does not exist, do nothing (should not happen)
        elif side == "sell":
            # For sell: reserved asset being sold
            reserved_key = (user_id, asset_symbol)
            reserved_info = self.balances.get(reserved_key)
            reserved_amount = quantity_remaining
            if reserved_info:
                reserved_released = min(reserved_info["balance_reserved"], reserved_amount)
                reserved_info["balance_reserved"] -= reserved_released
                reserved_info["balance_available"] += reserved_released
            # If balance does not exist, do nothing (should not happen)

        # Update order status
        order["status"] = "cancelled"
        # Optionally, update order["timestamp"] here with new time if desired

        return { "success": True, "message": f"Order {order_id} cancelled and funds released." }

    def reserve_funds_for_order(self, order_id: str) -> dict:
        """
        Atomically reserve the necessary funds for the given pending order.
        Moves funds from available to reserved in user's account balance.

        Args:
            order_id (str): The ID of the order for which funds should be reserved.

        Returns:
            dict: {
                "success": True,
                "message": "Funds reserved for order <id>"
            }
            or
            {
                "success": False,
                "error": "Description of the error"
            }

        Constraints:
            - Order must exist and be in a fund-reservable status.
            - User must have sufficient available balance.
            - Should not double-reserve for already reserved orders.
            - Reservation is atomic: both available and reserved updated together.
        """

        order = self.orders.get(order_id)
        if not order:
            return { "success": False, "error": "Order does not exist" }

        user_id = order["user_id"]
        side = order["side"]
        asset_symbol = order["asset_symbol"]
        quote_symbol = order["quote_symbol"]
        quantity = order["quantity"]
        price = order["price"]
        status = order["status"]

        # Allow only for orders that are NEW/PENDING and not already reserved/cancelled/filled
        if status not in ("pending", "new"):
            return {"success": False, "error": f"Order status is '{status}': cannot reserve funds."}

        # Check if already reserved by seeing if corresponding reserved funds were already moved
        # [Note: Real implementation may require a flag in the Order entity; here we use status]
        # Determine amount and which asset to reserve
        if side == "buy":
            reserve_asset = quote_symbol
            reserve_amount = quantity * price
        elif side == "sell":
            reserve_asset = asset_symbol
            reserve_amount = quantity
        else:
            return {"success": False, "error": f"Invalid order side: {side}" }

        balance_key = (user_id, reserve_asset)
        balance = self.balances.get(balance_key)
        if not balance:
            return {"success": False, "error": f"No balance record found for user and asset {reserve_asset}" }

        if balance["balance_available"] < reserve_amount:
            return {
                "success": False,
                "error": f"Insufficient available balance ({balance['balance_available']}) for reservation ({reserve_amount})"
            }

        # Make atomic reservation (subtract from available, add to reserved)
        balance["balance_available"] -= reserve_amount
        balance["balance_reserved"] += reserve_amount

        # Save the updated balance back
        self.balances[balance_key] = balance

        # Optionally, mark order as "reserved" (out of scope if such a status does not exist)
        # order["status"] = "reserved"

        return {
            "success": True,
            "message": f"Funds reserved for order {order_id}"
        }

    def release_reserved_funds(self, order_id: str) -> dict:
        """
        Release reserved funds (move from reserved back to available) for an order, 
        typically due to cancellation or failure.

        Args:
            order_id (str): The ID of the order to release funds for.

        Returns:
            dict: 
                On success: { "success": True, "message": "Reserved funds released for order <order_id>." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Order must exist.
            - User/account must exist.
            - Cannot release more than is currently reserved.
            - Only applies for non-fully filled/cancelled/failed orders with reserved funds.
            - Balance update must be atomic.
        """
        # Step 1: Validate order existence
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order does not exist"}

        user_id = order["user_id"]
        side = order["side"]
        asset_symbol = order["asset_symbol"]
        quote_symbol = order["quote_symbol"]
        qty_remaining = order["quantity_remaining"]
        price = order["price"]

        # Only pending/open-type orders should have reserved funds
        # If the order is already "filled", "cancelled", "failed" (typically no reserved funds remain)
        if order["status"] not in ("open", "pending", "partially_filled"):
            return {"success": False, "error": f"Order status '{order['status']}' does not have reserved funds to release"}

        # Step 2: Determine which asset/funds to release and its amount
        if side == "buy":
            # For limit buy: reserved in quote currency (qty_remaining × price)
            asset_to_release = quote_symbol
            amount = qty_remaining * price
        elif side == "sell":
            # For limit sell: reserved in base currency (qty_remaining)
            asset_to_release = asset_symbol
            amount = qty_remaining
        else:
            return {"success": False, "error": f"Unsupported order side: {side}"}

        key = (user_id, asset_to_release)
        balance_info = self.balances.get(key)
        if not balance_info:
            return {"success": False, "error": f"Account balance not found for user {user_id} asset {asset_to_release}"}

        # Step 3: Cannot release more than reserved
        reserved = balance_info["balance_reserved"]
        if reserved < amount - 1e-9:
            return {"success": False, 
                    "error": f"Insufficient reserved funds to release. Reserved: {reserved}, Required: {amount}"}

        # Step 4: Update balances atomically
        balance_info["balance_reserved"] -= amount
        balance_info["balance_available"] += amount

        # Step 5: Optionally, set order status to "cancelled" if this is a result of cancellation
        # (Not specified - only funds are released here.)

        return {"success": True, "message": f"Reserved funds released for order {order_id}."}

    def execute_trade(
        self,
        buy_order_id: str,
        sell_order_id: str,
        quantity: float,
        price: float
    ) -> dict:
        """
        Atomically match the specified buy and sell orders, update balances, order status,
        record the trade, and update transaction history for both participants.

        Args:
            buy_order_id (str): The order_id of the buy order to match.
            sell_order_id (str): The order_id of the sell order to match.
            quantity (float): The quantity of asset_symbol to be traded.
            price (float): The trade execution price (per unit asset_symbol).

        Returns:
            dict: {
                "success": True,
                "message": "Trade executed between ... for ... at ...",
            }
            or
            {
                "success": False,
                "error": "Reason for failure",
            }

        Constraints:
            - Orders must exist, be open, and be for the same trading pair and compatible sides.
            - Orders must have sufficient unfilled quantity (quantity_remaining >= quantity).
            - Users must have sufficient reserved balances for the trade.
            - Balances, orders, trades, and transaction histories must be updated atomically.
        """
        # --- Validation ---
        if buy_order_id not in self.orders:
            return {"success": False, "error": "Buy order not found."}
        if sell_order_id not in self.orders:
            return {"success": False, "error": "Sell order not found."}

        buy_order = self.orders[buy_order_id]
        sell_order = self.orders[sell_order_id]

        # Check sides
        if buy_order['side'] != 'buy' or sell_order['side'] != 'sell':
            return {"success": False, "error": "Order sides do not match (buy/sell)."}

        # Trading pair match
        if (buy_order['asset_symbol'], buy_order['quote_symbol']) != (sell_order['asset_symbol'], sell_order['quote_symbol']):
            return {"success": False, "error": "Orders are for different trading pairs."}

        asset_symbol = buy_order['asset_symbol']
        quote_symbol = buy_order['quote_symbol']

        if (asset_symbol, quote_symbol) not in self.order_books:
            return {"success": False, "error": "Invalid trading pair."}

        # Order status
        if buy_order['status'] != 'open' or sell_order['status'] != 'open':
            return {"success": False, "error": "One or both orders are not open."}

        # Quantity checks
        if buy_order['quantity_remaining'] < quantity:
            return {"success": False, "error": "Buy order does not have enough unfilled quantity."}
        if sell_order['quantity_remaining'] < quantity:
            return {"success": False, "error": "Sell order does not have enough unfilled quantity."}

        buy_user_id = buy_order['user_id']
        sell_user_id = sell_order['user_id']

        # Check balances: buy-side (reserved quote), sell-side (reserved asset)
        buy_balance_key = (buy_user_id, quote_symbol)
        sell_balance_key = (sell_user_id, asset_symbol)

        if buy_balance_key not in self.balances or sell_balance_key not in self.balances:
            return {"success": False, "error": "Insufficient user balances or accounts not found."}

        buy_user_balance = self.balances[buy_balance_key]
        sell_user_balance = self.balances[sell_balance_key]

        total_quote_needed = quantity * price

        # Check that buy user has enough reserved quote to pay
        if buy_user_balance['balance_reserved'] < total_quote_needed:
            return {"success": False, "error": "Buy user does not have enough reserved quote for this trade."}

        # Check that sell user has enough reserved asset to deliver
        if sell_user_balance['balance_reserved'] < quantity:
            return {"success": False, "error": "Sell user does not have enough reserved asset for this trade."}

        # --- All validation passed, snapshot state for atomic update ---
        # Deep copies for rollback if needed (not shown, but atomic ops should be enforced in real systems)
        # Update buyer: reduce reserved, increase available asset
        buy_user_balance['balance_reserved'] -= total_quote_needed
        asset_balance_key = (buy_user_id, asset_symbol)
        if asset_balance_key not in self.balances:
            # Initialize asset balance record if not present
            self.balances[asset_balance_key] = {
                '_id': asset_balance_key[0] + '_' + asset_balance_key[1],
                'asset_symbol': asset_symbol,
                'balance_available': 0.0,
                'balance_reserved': 0.0
            }
        self.balances[asset_balance_key]['balance_available'] += quantity

        # Update seller: reduce reserved asset, increase available quote
        sell_user_balance['balance_reserved'] -= quantity
        quote_balance_key = (sell_user_id, quote_symbol)
        if quote_balance_key not in self.balances:
            self.balances[quote_balance_key] = {
                '_id': quote_balance_key[0] + '_' + quote_balance_key[1],
                'asset_symbol': quote_symbol,
                'balance_available': 0.0,
                'balance_reserved': 0.0
            }
        self.balances[quote_balance_key]['balance_available'] += total_quote_needed

        # Update order quantities and status
        buy_order['quantity_remaining'] -= quantity
        sell_order['quantity_remaining'] -= quantity

        if buy_order['quantity_remaining'] <= 0:
            buy_order['status'] = 'filled'
        elif buy_order['quantity_remaining'] < buy_order['quantity']:
            buy_order['status'] = 'partially_filled'

        if sell_order['quantity_remaining'] <= 0:
            sell_order['status'] = 'filled'
        elif sell_order['quantity_remaining'] < sell_order['quantity']:
            sell_order['status'] = 'partially_filled'

        # Generate trade record
        trade_id = str(uuid.uuid4())
        new_trade = {
            'trade_id': trade_id,
            'buy_order_id': buy_order_id,
            'sell_order_id': sell_order_id,
            'asset_symbol': asset_symbol,
            'quote_symbol': quote_symbol,
            'quantity': quantity,
            'price': price,
            'timestamp': time.time()
        }
        self.trades[trade_id] = new_trade

        # Update transaction history for both users
        now = new_trade['timestamp']
        buy_txn = {
            '_id': buy_user_id + '_' + str(uuid.uuid4()),
            'transaction_id': trade_id,
            'asset_symbol': asset_symbol,
            'type': 'trade',
            'amount': quantity,
            'timestamp': now
        }
        quote_txn = {
            '_id': sell_user_id + '_' + str(uuid.uuid4()),
            'transaction_id': trade_id,
            'asset_symbol': quote_symbol,
            'type': 'trade',
            'amount': total_quote_needed,
            'timestamp': now
        }
        # Buyer's transaction: asset increase
        self.transaction_histories.setdefault(buy_user_id, []).append(buy_txn)
        # Seller's transaction: quote increase
        self.transaction_histories.setdefault(sell_user_id, []).append(quote_txn)

        # Update order book entries to mirror the updated order state, then remove filled orders.
        ob_key = (asset_symbol, quote_symbol)
        order_book = self.order_books[ob_key]
        for entry in order_book['bids']:
            if entry['order_id'] == buy_order_id:
                entry['quantity_remaining'] = buy_order['quantity_remaining']
                entry['status'] = buy_order['status']
        for entry in order_book['asks']:
            if entry['order_id'] == sell_order_id:
                entry['quantity_remaining'] = sell_order['quantity_remaining']
                entry['status'] = sell_order['status']

        order_book['bids'] = [o for o in order_book['bids'] if o['quantity_remaining'] > 0]
        order_book['asks'] = [o for o in order_book['asks'] if o['quantity_remaining'] > 0]

        return {
            "success": True,
            "message": f"Trade executed between {buy_order_id}(buy) and {sell_order_id}(sell) for {quantity} {asset_symbol} at {price} {quote_symbol} per unit."
        }

    def update_order_status(self, order_id: str, new_status: str) -> dict:
        """
        Change the status of a specific order (e.g., open → filled/cancelled).
        If status changes to 'cancelled', reserved funds are released.
        If status changes to 'filled', order should be removed from order book.

        Args:
            order_id (str): ID of the order to update.
            new_status (str): Status to set ('open', 'filled', 'cancelled', ...).

        Returns:
            dict: {
                "success": True,
                "message": "Order status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Order must exist.
            - new_status must be a valid value.
            - On 'cancelled', reserved funds are released.
            - On 'filled', order is removed from order book.
            - No status change for already filled/cancelled orders.
        """
        valid_statuses = {"open", "filled", "cancelled"}
        if order_id not in self.orders:
            return { "success": False, "error": "Order does not exist." }

        if new_status not in valid_statuses:
            return { "success": False, "error": "Invalid status." }

        order = self.orders[order_id]
        current_status = order["status"]

        if current_status in ("filled", "cancelled"):
            return { "success": False, "error": f"Cannot change status of an order that is already {current_status}." }

        # Update the status
        order["status"] = new_status
        self.orders[order_id] = order

        # Handle reserved funds and order book updates
        # Find order book location
        order_book_key = (order["asset_symbol"], order["quote_symbol"])
        user_id = order["user_id"]

        if new_status == "cancelled":
            # Release reserved funds for the portion not filled
            if order["side"] == "sell":
                bal = self.balances.get((user_id, order["asset_symbol"]))
                if bal:
                    to_release = order["quantity_remaining"]
                    bal["balance_available"] += to_release
                    bal["balance_reserved"] -= to_release
                    if bal["balance_reserved"] < 0:
                        bal["balance_reserved"] = 0
                    self.balances[(user_id, order["asset_symbol"])] = bal
            else:  # buy
                quote_symbol = order["quote_symbol"]
                bal = self.balances.get((user_id, quote_symbol))
                if bal:
                    to_release = order["quantity_remaining"] * order["price"]
                    bal["balance_available"] += to_release
                    bal["balance_reserved"] -= to_release
                    if bal["balance_reserved"] < 0:
                        bal["balance_reserved"] = 0
                    self.balances[(user_id, quote_symbol)] = bal
            # Remove from order book
            if order_book_key in self.order_books:
                book = self.order_books[order_book_key]
                order_list = book["bids"] if order["side"] == "buy" else book["asks"]
                order_list = [o for o in order_list if o["order_id"] != order_id]
                if order["side"] == "buy":
                    book["bids"] = order_list
                else:
                    book["asks"] = order_list
                self.order_books[order_book_key] = book

        if new_status == "filled":
            # Remove from order book
            if order_book_key in self.order_books:
                book = self.order_books[order_book_key]
                order_list = book["bids"] if order["side"] == "buy" else book["asks"]
                order_list = [o for o in order_list if o["order_id"] != order_id]
                if order["side"] == "buy":
                    book["bids"] = order_list
                else:
                    book["asks"] = order_list
                self.order_books[order_book_key] = book
            # Reserved funds have been dealt with during trade execution, so nothing to release here

        return { "success": True, "message": f"Order status updated to {new_status}." }

    def deposit_funds(self, user_id: str, asset_symbol: str, amount: float) -> dict:
        """
        Increase a user's available balance for a given asset due to a deposit.

        Args:
            user_id (str): The user's ID who receives the deposit.
            asset_symbol (str): The asset symbol (e.g., 'USD', 'BTC').
            amount (float): The amount to deposit (must be > 0).

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
            - `user_id` must exist.
            - `amount` must be positive.
            - Balance is created if missing.
            - A transaction history entry for the deposit is created.
        """
        # User must exist
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
        if amount <= 0:
            return { "success": False, "error": "Deposit amount must be positive." }
    
        key = (user_id, asset_symbol)
        now_ts = time.time()
        # If balance record exists, increase; else create.
        if key in self.balances:
            self.balances[key]["balance_available"] += amount
        else:
            self.balances[key] = {
                "_id": f"{user_id}:{asset_symbol}",
                "asset_symbol": asset_symbol,
                "balance_available": amount,
                "balance_reserved": 0.0
            }

        # Log the deposit in transaction history
        transaction_entry = {
            "_id": f"tx_{user_id}_{asset_symbol}_{now_ts}",
            "transaction_id": f"deposit_{user_id}_{asset_symbol}_{now_ts}",
            "asset_symbol": asset_symbol,
            "type": "deposit",
            "amount": amount,
            "timestamp": now_ts,
        }
        if user_id not in self.transaction_histories:
            self.transaction_histories[user_id] = []
        self.transaction_histories[user_id].append(transaction_entry)

        return {
            "success": True,
            "message": f"Deposited {amount} {asset_symbol} to user {user_id}."
        }

    def withdraw_funds(self, user_id: str, asset_symbol: str, amount: float) -> dict:
        """
        Deducts available balance for a specified user and asset upon withdrawal,
        and records the transaction in the transaction history.

        Args:
            user_id (str): The unique identifier of the user.
            asset_symbol (str): The symbol of the asset to withdraw (e.g., 'BTC').
            amount (float): The amount to withdraw (must be > 0).

        Returns:
            dict: {
                "success": True,
                "message": "Withdrawal completed."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - Asset balance must exist and be sufficient for withdrawal.
            - Amount must be positive.
            - Withdrawal must be logged in transaction history atomically with balance update.
        """
        # Input validation
        if amount <= 0:
            return {"success": False, "error": "Withdrawal amount must be positive."}
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        key = (user_id, asset_symbol)
        balance_info = self.balances.get(key)
        if not balance_info:
            return {"success": False, "error": "Asset balance entry does not exist for user."}
        if balance_info["balance_available"] < amount:
            return {"success": False, "error": "Insufficient available balance."}

        # Deduct the funds
        new_available = balance_info["balance_available"] - amount
        self.balances[key]["balance_available"] = new_available
        # Note: reserved balance is unaffected

        # Prepare and record transaction history
        tx = {
            "_id": str(uuid.uuid4()),
            "transaction_id": str(uuid.uuid4()),
            "asset_symbol": asset_symbol,
            "type": "withdrawal",
            "amount": amount,
            "timestamp": time.time()
        }
        if user_id not in self.transaction_histories:
            self.transaction_histories[user_id] = []
        self.transaction_histories[user_id].append(tx)

        return {"success": True, "message": "Withdrawal completed."}

    def add_trading_pair(self, asset_symbol: str, quote_symbol: str) -> dict:
        """
        Admin operation to create a new trading pair and corresponding (empty) order book.

        Args:
            asset_symbol (str): The base asset for the trading pair (e.g., 'BTC').
            quote_symbol (str): The quote asset for the trading pair (e.g., 'USD').

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message if pair is created
            }
            or
            {
                "success": False,
                "error": str    # Description of the error
            }

        Constraints:
        - A trading pair must not already exist.
        - asset_symbol and quote_symbol must be non-empty and not identical.
        """

        if not asset_symbol or not quote_symbol:
            return {"success": False, "error": "Asset and quote symbols must be non-empty."}
        if asset_symbol == quote_symbol:
            return {"success": False, "error": "Asset symbol and quote symbol must be different."}
        if (asset_symbol, quote_symbol) in self.order_books:
            return {"success": False, "error": "Trading pair already exists."}

        order_book: OrderBookInfo = {
            "asset_symbol": asset_symbol,
            "quote_symbol": quote_symbol,
            "bids": [],
            "asks": []
        }
        self.order_books[(asset_symbol, quote_symbol)] = order_book

        return {
            "success": True,
            "message": f"Trading pair {asset_symbol}/{quote_symbol} added."
        }

    def remove_trading_pair(self, asset_symbol: str, quote_symbol: str) -> dict:
        """
        Admin operation to remove a trading pair (order book) from the exchange.

        Args:
            asset_symbol (str): The base asset of the pair (e.g., 'BTC').
            quote_symbol (str): The quote asset of the pair (e.g., 'USD').

        Returns:
            dict: {
                "success": True,
                "message": "Trading pair {asset_symbol}/{quote_symbol} removed successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - The trading pair must exist in order_books.
            - Any open orders for this pair will be canceled and their reserved balances released.
        """
        pair_key = (asset_symbol, quote_symbol)
        if pair_key not in self.order_books:
            return {"success": False, "error": "Trading pair does not exist."}

        order_book = self.order_books[pair_key]
        canceled_order_ids = []

        # Cancel and cleanup all open orders
        for order_list in (order_book.get("bids", []), order_book.get("asks", [])):
            for order in order_list:
                order_id = order["order_id"]
                user_id = order["user_id"]
                side = order["side"]
                quantity_remaining = order["quantity_remaining"]
                price = order["price"]
                asset = order["asset_symbol"]
                quote = order["quote_symbol"]
                # Release reserved funds
                if side == "buy":
                    # For a buy order, reserved balance is in quote currency: price * quantity_remaining
                    reserve_asset = quote
                    amount_to_release = price * quantity_remaining
                else:  # "sell"
                    # For a sell order, reserved balance is in base currency: quantity_remaining
                    reserve_asset = asset
                    amount_to_release = quantity_remaining
                balance_key = (user_id, reserve_asset)
                bal = self.balances.get(balance_key)
                if bal:
                    bal["balance_reserved"] = max(bal["balance_reserved"] - amount_to_release, 0)
                    bal["balance_available"] += amount_to_release  # Release back to available
                # Mark order as cancelled
                if order_id in self.orders:
                    self.orders[order_id]["status"] = "cancelled"
                canceled_order_ids.append(order_id)
        # Remove the order book
        del self.order_books[pair_key]
        return {
            "success": True,
            "message": f"Trading pair {asset_symbol}/{quote_symbol} removed successfully. "
                       f"{len(canceled_order_ids)} open orders canceled."
        }

    def modify_order(self, order_id: str, new_quantity: float = None, new_price: float = None) -> dict:
        """
        Modify permitted parameters (quantity and/or price) of an existing order,
        enforcing atomicity and all validation constraints.

        Args:
            order_id (str): The ID of the order to be modified.
            new_quantity (float|None): The new desired quantity (optional).
            new_price (float|None): The new desired price (optional; only for limit orders).

        Returns:
            dict: {
                "success": True,
                "message": "Order modified successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only allow changing price (for limit orders) and/or quantity.
            - Cannot increase quantity unless sufficient balance is available and reserve can be updated.
            - Cannot change fields like side, asset_symbol, quote_symbol, user_id, or order_type.
            - Order must be in a modifiable state (e.g., 'open', not filled or canceled).
            - Updates to balances and order book must be atomic.
            - Order book's sorting (by price, timestamp) must be maintained after modifications.
        """
        # Locate the order
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}

        # Check modifiable state
        if order["status"] not in ("open", "partially_filled"):
            return {"success": False, "error": "Order may not be modified in its current state"}

        # Validate inputs
        # For market orders, price cannot be changed/should not be provided
        if order["order_type"] == "market" and new_price is not None:
            return {"success": False, "error": "Cannot change price of a market order"}

        if new_quantity is None and (new_price is None or order["order_type"] == "market"):
            return {"success": False, "error": "Nothing to modify"}

        # Get user's balance for asset (for sells) or quote (for buys)
        user_id = order["user_id"]
        side = order["side"]
        asset = order["asset_symbol"]
        quote = order["quote_symbol"]

        # Current order quantity remaining
        orig_quantity = order["quantity_remaining"]
        orig_price = order["price"]

        # Handle quantity modification
        # For limit orders, price and quantity both may be changed
        # For market orders, only quantity may be reduced (since market price is not user-provided)

        # Save old values for possible rollback/atomic logic
        changes = {}

        # Check and process quantity
        if new_quantity is not None:
            if new_quantity <= 0.0:
                return {"success": False, "error": "Quantity must be positive"}
            if new_quantity < (order["quantity"] - order["quantity_remaining"]):
                return {"success": False, "error": "New quantity less than already filled amount"}
            # Calculate change in required reservation (increase/decrease)
            # For partially filled: only remaining part is modifiable
            change_in_quantity = new_quantity - order["quantity"]
        else:
            new_quantity = order["quantity"]
            change_in_quantity = 0.0

        # Check and process price (only for limit orders)
        if new_price is not None:
            if order["order_type"] != "limit":
                return {"success": False, "error": "Only limit orders can change price"}
            if new_price <= 0.0:
                return {"success": False, "error": "Price must be positive"}
        else:
            new_price = order["price"]

        # Funds checking (atomicity: verify prior to any state modification)
        if side == "buy":
            # Reservation in quote asset
            old_total, new_total = order["quantity"] * order["price"], new_quantity * new_price
            # Find user's reserved and available
            key = (user_id, quote)
        else:  # sell
            # Reservation in asset_asset
            old_total, new_total = order["quantity"], new_quantity
            key = (user_id, asset)

        bal = self.balances.get(key)
        if not bal:
            return {"success": False, "error": "Balance record not found"}

        # Calculate change in reservation
        diff = new_total - old_total
        # If increasing reservation, check available funds
        if diff > 0.0:
            if bal["balance_available"] < diff:
                return {"success": False, "error": "Insufficient available funds/asset to increase order"}
        # All checks pass: apply changes atomically

        # Reserve/release funds accordingly
        if diff != 0.0:
            if diff > 0:
                bal["balance_available"] -= diff
                bal["balance_reserved"] += diff
            else:
                # Release reservation
                bal["balance_available"] += -diff
                bal["balance_reserved"] -= -diff
            # store back
            self.balances[key] = bal

        # Update order
        order["quantity"] = new_quantity
        order["quantity_remaining"] += change_in_quantity  # If quantity increased, add to remaining; if decreased, reduce appropriately.
        if order["quantity_remaining"] > new_quantity:
            order["quantity_remaining"] = new_quantity  # can't be more than total
        if order["order_type"] == "limit":
            order["price"] = new_price
        # store back
        self.orders[order_id] = order

        # Update order book: remove then re-insert order to re-sort
        book_key = (asset, quote)
        ob = self.order_books.get(book_key)
        if not ob:
            return {"success": False, "error": "Order book for trading pair not found"}

        # Locate and remove order from bids/asks, then re-insert
        order_list = ob["bids"] if side == "buy" else ob["asks"]
        # remove current order
        order_list = [o for o in order_list if o["order_id"] != order_id]
        # re-insert and maintain sortedness
        order_list.append(order.copy())
        # sort:
        if side == "buy":
            # highest price priority, then earliest timestamp
            order_list.sort(key=lambda x: (-x["price"], x["timestamp"]))
            ob["bids"] = order_list
        else:  # sell (asks): lowest price priority
            order_list.sort(key=lambda x: (x["price"], x["timestamp"]))
            ob["asks"] = order_list
        self.order_books[book_key] = ob

        return {"success": True, "message": "Order modified successfully"}


class CryptoExchangeTradingSystem(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {})
        self._sync_from_inner()

    @staticmethod
    def _normalize_token(value: Any) -> str:
        return "".join(ch for ch in str(value).lower() if ch.isalnum())

    @classmethod
    def _token_variants(cls, value: Any) -> set[str]:
        token = cls._normalize_token(value)
        variants = {token} if token else set()
        if token.startswith("user") and len(token) > 4:
            variants.add(token[4:])
        if token.startswith("u") and len(token) > 1:
            variants.add(token[1:])
        if token.startswith("balance") and len(token) > 7:
            variants.add(token[7:])
        if token.startswith("bal") and len(token) > 3:
            variants.add(token[3:])
        if token.startswith("b") and len(token) > 1:
            variants.add(token[1:])
        return {v for v in variants if v}

    @classmethod
    def _score_user_match(
        cls,
        raw_key: Any,
        record_id: Any,
        asset_symbol: Any,
        aliases: set[str],
    ) -> int:
        score = 0
        search_texts = [str(raw_key or ""), str(record_id or "")]
        asset_token = cls._normalize_token(asset_symbol)
        for text in search_texts:
            token = cls._normalize_token(text)
            reduced = token
            if asset_token and reduced.endswith(asset_token):
                reduced = reduced[: -len(asset_token)]
            for prefix in ("balance", "bal", "b"):
                if reduced.startswith(prefix):
                    reduced = reduced[len(prefix):]
            candidates = {token, reduced}
            for candidate in list(candidates):
                candidates.update(cls._token_variants(candidate))
            if aliases & candidates:
                score = max(score, 100 if token in aliases else 80)
            if any(alias and alias in token for alias in aliases):
                score = max(score, 60)
        return score

    @classmethod
    def _normalize_users(cls, raw_users: Any) -> dict[str, UserInfo]:
        if not isinstance(raw_users, dict):
            return {}
        normalized: dict[str, UserInfo] = {}
        for raw_key, user_info in raw_users.items():
            if not isinstance(user_info, dict):
                continue
            canonical_id = str(user_info.get("_id") or raw_key)
            normalized[canonical_id] = copy.deepcopy(user_info)
        return normalized

    @classmethod
    def _collect_unique_orders(
        cls,
        raw_orders: Any = None,
        raw_order_books: Any = None,
    ) -> list[dict]:
        collected: dict[str, dict] = {}

        if isinstance(raw_orders, dict):
            for raw_key, order in raw_orders.items():
                if not isinstance(order, dict):
                    continue
                order_id = str(order.get("order_id") or raw_key)
                collected.setdefault(order_id, copy.deepcopy(order))

        if isinstance(raw_order_books, dict):
            for _, order_book in raw_order_books.items():
                if not isinstance(order_book, dict):
                    continue
                for side in ("bids", "asks"):
                    for order in order_book.get(side, []) or []:
                        if not isinstance(order, dict):
                            continue
                        order_id = str(order.get("order_id") or f"{side}_{len(collected)}")
                        collected.setdefault(order_id, copy.deepcopy(order))

        return list(collected.values())

    @classmethod
    def _resolve_user_id(
        cls,
        candidate: Any,
        users: dict[str, UserInfo],
        user_aliases: dict[str, set[str]],
    ) -> str | None:
        if candidate is None:
            return None
        candidate_str = str(candidate)
        if candidate_str in users:
            return candidate_str
        candidate_token = cls._normalize_token(candidate_str)
        if not candidate_token:
            return None
        matches = [
            user_id
            for user_id, aliases in user_aliases.items()
            if candidate_token in aliases
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    @classmethod
    def _normalize_balances(
        cls,
        raw_balances: Any,
        users: dict[str, UserInfo],
        raw_orders: Any = None,
        raw_order_books: Any = None,
        raw_transaction_histories: Any = None,
    ) -> dict[Tuple[str, str], AccountBalanceInfo]:
        if not isinstance(raw_balances, dict):
            return {}

        user_aliases: dict[str, set[str]] = {}
        for user_id, user_info in users.items():
            aliases = set()
            aliases.update(cls._token_variants(user_id))
            aliases.update(cls._token_variants(user_info.get("_id", "")))
            aliases.update(cls._token_variants(user_info.get("username", "")))
            user_aliases[user_id] = aliases

        unique_orders = cls._collect_unique_orders(raw_orders, raw_order_books)
        normalized: dict[Tuple[str, str], AccountBalanceInfo] = {}
        unresolved: list[tuple[Any, dict]] = []

        for raw_key, balance_info in raw_balances.items():
            if not isinstance(balance_info, dict):
                continue
            asset_symbol = balance_info.get("asset_symbol")
            if not asset_symbol:
                continue

            explicit_user_id = None
            for user_field in (
                "user_id",
                "owner_user_id",
                "owner_id",
                "account_owner_id",
                "account_id",
            ):
                explicit_user_id = cls._resolve_user_id(balance_info.get(user_field), users, user_aliases)
                if explicit_user_id:
                    break
            if explicit_user_id:
                normalized[(explicit_user_id, str(asset_symbol))] = copy.deepcopy(balance_info)
                continue

            scored = sorted(
                (
                    (
                        cls._score_user_match(raw_key, balance_info.get("_id"), asset_symbol, aliases),
                        user_id,
                    )
                    for user_id, aliases in user_aliases.items()
                ),
                reverse=True,
            )
            if scored and scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
                normalized[(scored[0][1], str(asset_symbol))] = copy.deepcopy(balance_info)
            else:
                unresolved.append((raw_key, balance_info))

        if unresolved:
            reserve_hints: dict[tuple[str, str], list[float]] = {}
            reserve_totals: dict[tuple[str, str], float] = {}
            for order in unique_orders:
                if not isinstance(order, dict):
                    continue
                user_id = str(order.get("user_id") or "")
                side = order.get("side")
                asset_symbol = str(order.get("asset_symbol") or "")
                quote_symbol = str(order.get("quote_symbol") or "")
                quantity_remaining = float(order.get("quantity_remaining", order.get("quantity", 0)) or 0)
                price = float(order.get("price", 0) or 0)
                if side == "buy" and quote_symbol:
                    reserved_amount = quantity_remaining * price
                    reserve_hints.setdefault((user_id, quote_symbol), []).append(reserved_amount)
                    reserve_totals[(user_id, quote_symbol)] = reserve_totals.get((user_id, quote_symbol), 0.0) + reserved_amount
                elif side == "sell" and asset_symbol:
                    reserve_hints.setdefault((user_id, asset_symbol), []).append(quantity_remaining)
                    reserve_totals[(user_id, asset_symbol)] = reserve_totals.get((user_id, asset_symbol), 0.0) + quantity_remaining

            still_unresolved: list[tuple[Any, dict]] = []
            for raw_key, balance_info in unresolved:
                asset_symbol = str(balance_info.get("asset_symbol") or "")
                reserved = float(balance_info.get("balance_reserved", 0) or 0)
                matching_users = [
                    user_id
                    for (user_id, reserve_asset), amounts in reserve_hints.items()
                    if reserve_asset == asset_symbol and (
                        any(abs(amount - reserved) < 1e-9 for amount in amounts)
                        or abs(reserve_totals.get((user_id, reserve_asset), 0.0) - reserved) < 1e-9
                    )
                ]
                if reserved > 0 and len(matching_users) == 1:
                    normalized[(matching_users[0], asset_symbol)] = copy.deepcopy(balance_info)
                else:
                    still_unresolved.append((raw_key, balance_info))
            unresolved = still_unresolved

        asset_participants: dict[str, set[str]] = {}
        if unresolved:
            for order in unique_orders:
                user_id = str(order.get("user_id") or "")
                if user_id:
                    for symbol_field in ("asset_symbol", "quote_symbol"):
                        symbol = order.get(symbol_field)
                        if symbol:
                            asset_participants.setdefault(str(symbol), set()).add(user_id)
            for raw_user_key, history_entries in (raw_transaction_histories or {}).items() if isinstance(raw_transaction_histories, dict) else []:
                raw_user_token = cls._normalize_token(raw_user_key)
                matched_users = [
                    user_id
                    for user_id, aliases in user_aliases.items()
                    if raw_user_token in aliases
                ]
                if len(matched_users) != 1:
                    continue
                canonical_user_id = matched_users[0]
                for entry in history_entries or []:
                    if isinstance(entry, dict) and entry.get("asset_symbol"):
                        asset_participants.setdefault(str(entry["asset_symbol"]), set()).add(canonical_user_id)

            still_unresolved = []
            for raw_key, balance_info in unresolved:
                asset_symbol = str(balance_info.get("asset_symbol") or "")
                participants = asset_participants.get(asset_symbol, set())
                if len(participants) == 1:
                    normalized[(next(iter(participants)), asset_symbol)] = copy.deepcopy(balance_info)
                else:
                    still_unresolved.append((raw_key, balance_info))
            unresolved = still_unresolved

        if unresolved:
            still_unresolved = []
            for raw_key, balance_info in unresolved:
                asset_symbol = str(balance_info.get("asset_symbol") or "")
                candidate_users = asset_participants.get(asset_symbol, set()) or set(users.keys())
                remaining_users = [
                    user_id
                    for user_id in candidate_users
                    if (user_id, asset_symbol) not in normalized
                ]
                if len(remaining_users) == 1:
                    normalized[(remaining_users[0], asset_symbol)] = copy.deepcopy(balance_info)
                else:
                    still_unresolved.append((raw_key, balance_info))
            unresolved = still_unresolved

        if len(users) == 1:
            sole_user_id = next(iter(users))
            for _, balance_info in unresolved:
                asset_symbol = balance_info.get("asset_symbol")
                if asset_symbol:
                    normalized[(sole_user_id, str(asset_symbol))] = copy.deepcopy(balance_info)

        return normalized

    @classmethod
    def _reconcile_balances_with_open_orders(cls, env) -> None:
        required_reserved: dict[Tuple[str, str], float] = {}
        unique_orders = cls._collect_unique_orders(getattr(env, "orders", None), getattr(env, "order_books", None))
        for order in unique_orders:
            if not isinstance(order, dict):
                continue
            if order.get("status") not in {"open", "partially_filled", "active"}:
                continue
            user_id = str(order.get("user_id") or "")
            side = order.get("side")
            asset_symbol = str(order.get("asset_symbol") or "")
            quote_symbol = str(order.get("quote_symbol") or "")
            quantity_remaining = float(order.get("quantity_remaining", order.get("quantity", 0)) or 0)
            price = float(order.get("price", 0) or 0)
            if not user_id or quantity_remaining <= 0:
                continue
            if side == "buy" and quote_symbol:
                reserve_key = (user_id, quote_symbol)
                reserve_amount = quantity_remaining * price
            elif side == "sell" and asset_symbol:
                reserve_key = (user_id, asset_symbol)
                reserve_amount = quantity_remaining
            else:
                continue
            required_reserved[reserve_key] = required_reserved.get(reserve_key, 0.0) + reserve_amount

        for balance_key, required_amount in required_reserved.items():
            if required_amount <= 0:
                continue
            balance = env.balances.get(balance_key)
            if balance is None:
                user_id, asset_symbol = balance_key
                env.balances[balance_key] = {
                    "_id": f"{user_id}_{asset_symbol}",
                    "asset_symbol": asset_symbol,
                    "balance_available": 0.0,
                    "balance_reserved": required_amount,
                }
                continue

            current_reserved = float(balance.get("balance_reserved", 0) or 0)
            if current_reserved + 1e-9 >= required_amount:
                continue

            current_available = float(balance.get("balance_available", 0) or 0)
            needed = required_amount - current_reserved
            movable = min(current_available, needed)
            balance["balance_available"] = current_available - movable
            balance["balance_reserved"] = current_reserved + movable
            remaining_needed = needed - movable
            if remaining_needed > 1e-9:
                balance["balance_reserved"] += remaining_needed

    @classmethod
    def _normalize_order_books(cls, raw_order_books: Any) -> dict[Tuple[str, str], OrderBookInfo]:
        if not isinstance(raw_order_books, dict):
            return {}
        normalized: dict[Tuple[str, str], OrderBookInfo] = {}
        for _, order_book in raw_order_books.items():
            if not isinstance(order_book, dict):
                continue
            asset_symbol = order_book.get("asset_symbol")
            quote_symbol = order_book.get("quote_symbol")
            if not asset_symbol or not quote_symbol:
                continue
            normalized[(str(asset_symbol), str(quote_symbol))] = copy.deepcopy(order_book)
        return normalized

    @classmethod
    def _normalize_transaction_histories(
        cls,
        raw_histories: Any,
        users: dict[str, UserInfo],
    ) -> dict[str, List[TransactionHistoryInfo]]:
        if not isinstance(raw_histories, dict):
            return {}
        normalized: dict[str, List[TransactionHistoryInfo]] = {}
        reverse_alias: dict[str, str] = {}
        for user_id, user_info in users.items():
            for alias in cls._token_variants(user_id) | cls._token_variants(user_info.get("_id", "")) | cls._token_variants(user_info.get("username", "")):
                reverse_alias.setdefault(alias, user_id)
        for raw_key, history_entries in raw_histories.items():
            key_token = cls._normalize_token(raw_key)
            canonical_user_id = reverse_alias.get(key_token, str(raw_key))
            normalized[canonical_user_id] = copy.deepcopy(history_entries)
        return normalized

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
        raw_users = init_config.get("users")
        normalized_users = CryptoExchangeTradingSystem._normalize_users(raw_users)
        if normalized_users:
            env.users = normalized_users

        raw_balances = init_config.get("balances")
        normalized_balances = CryptoExchangeTradingSystem._normalize_balances(
            raw_balances,
            env.users,
            init_config.get("orders"),
            init_config.get("order_books"),
            init_config.get("transaction_histories"),
        )
        if normalized_balances:
            env.balances = normalized_balances

        raw_order_books = init_config.get("order_books")
        normalized_order_books = CryptoExchangeTradingSystem._normalize_order_books(raw_order_books)
        if normalized_order_books:
            env.order_books = normalized_order_books

        raw_histories = init_config.get("transaction_histories")
        normalized_histories = CryptoExchangeTradingSystem._normalize_transaction_histories(raw_histories, env.users)
        if normalized_histories:
            env.transaction_histories = normalized_histories

        for key, value in init_config.items():
            if key in {"users", "balances", "order_books", "transaction_histories"}:
                continue
            setattr(env, key, copy.deepcopy(value))

        CryptoExchangeTradingSystem._reconcile_balances_with_open_orders(env)

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

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_account_balance(self, **kwargs):
        return self._call_inner_tool('get_account_balance', kwargs)

    def get_all_balances_for_user(self, **kwargs):
        return self._call_inner_tool('get_all_balances_for_user', kwargs)

    def get_order_by_id(self, **kwargs):
        return self._call_inner_tool('get_order_by_id', kwargs)

    def list_open_orders_for_user(self, **kwargs):
        return self._call_inner_tool('list_open_orders_for_user', kwargs)

    def list_orders_by_status(self, **kwargs):
        return self._call_inner_tool('list_orders_by_status', kwargs)

    def get_order_book(self, **kwargs):
        return self._call_inner_tool('get_order_book', kwargs)

    def get_order_book_top_n(self, **kwargs):
        return self._call_inner_tool('get_order_book_top_n', kwargs)

    def get_trade_by_id(self, **kwargs):
        return self._call_inner_tool('get_trade_by_id', kwargs)

    def list_trades_for_user(self, **kwargs):
        return self._call_inner_tool('list_trades_for_user', kwargs)

    def get_transaction_history(self, **kwargs):
        return self._call_inner_tool('get_transaction_history', kwargs)

    def verify_trading_pair(self, **kwargs):
        return self._call_inner_tool('verify_trading_pair', kwargs)

    def place_limit_order(self, **kwargs):
        return self._call_inner_tool('place_limit_order', kwargs)

    def place_market_order(self, **kwargs):
        return self._call_inner_tool('place_market_order', kwargs)

    def cancel_order(self, **kwargs):
        return self._call_inner_tool('cancel_order', kwargs)

    def reserve_funds_for_order(self, **kwargs):
        return self._call_inner_tool('reserve_funds_for_order', kwargs)

    def release_reserved_funds(self, **kwargs):
        return self._call_inner_tool('release_reserved_funds', kwargs)

    def execute_trade(self, **kwargs):
        return self._call_inner_tool('execute_trade', kwargs)

    def update_order_status(self, **kwargs):
        return self._call_inner_tool('update_order_status', kwargs)

    def deposit_funds(self, **kwargs):
        return self._call_inner_tool('deposit_funds', kwargs)

    def withdraw_funds(self, **kwargs):
        return self._call_inner_tool('withdraw_funds', kwargs)

    def add_trading_pair(self, **kwargs):
        return self._call_inner_tool('add_trading_pair', kwargs)

    def remove_trading_pair(self, **kwargs):
        return self._call_inner_tool('remove_trading_pair', kwargs)

    def modify_order(self, **kwargs):
        return self._call_inner_tool('modify_order', kwargs)
