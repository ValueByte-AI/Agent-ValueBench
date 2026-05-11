# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Union
from typing import Optional, List, Dict, Any
from datetime import datetime



class ServerClockInfo(TypedDict):
    current_time: Union[float, str]  # timestamp
    timezone: str

class AccountInfo(TypedDict):
    account_id: str
    balance: float
    currency: str
    status: str

class TradeInfo(TypedDict):
    trade_id: str
    account_id: str
    instrument_id: str
    quantity: float
    price: float
    trade_time: Union[float, str]  # timestamp
    status: str

class MarketInfo(TypedDict):
    market_id: str
    status: str
    open_time: Union[float, str]  # timestamp
    close_time: Union[float, str]  # timestamp

class SystemLogInfo(TypedDict):
    log_id: str
    timestamp: Union[float, str]  # timestamp
    event_type: str
    message: str
    severity: str

class OperationalMetricInfo(TypedDict):
    metric_id: str
    value: float
    timestamp: Union[float, str]  # timestamp
    metric_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Backend state for a financial trading platform.

        Constraints:
        - ServerClock must be synchronized with authoritative time sources.
        - Trades and account updates must use ServerClock for all time-stamping.
        - Market status changes (open, closed, paused) must be recorded with timestamps.
        - All logged events must include a timestamp.
        - Account balances cannot become negative (unless margin trading allowed).
        - Each trade must reference valid account and instrument identifiers.
        """

        # ServerClock: The authoritative clock for all time-stamping
        self.server_clock: ServerClockInfo = {"current_time": 0.0, "timezone": "UTC"}

        # Accounts: {account_id: AccountInfo}
        self.accounts: Dict[str, AccountInfo] = {}

        # Trades: {trade_id: TradeInfo}
        self.trades: Dict[str, TradeInfo] = {}

        # Markets: {market_id: MarketInfo}
        self.markets: Dict[str, MarketInfo] = {}

        # System logs: {log_id: SystemLogInfo}
        self.system_logs: Dict[str, SystemLogInfo] = {}

        # Operational Metrics: {metric_id: OperationalMetricInfo}
        self.operational_metrics: Dict[str, OperationalMetricInfo] = {}

    def get_current_server_time(self) -> dict:
        """
        Retrieve the authoritative current platform time and timezone from ServerClock.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": ServerClockInfo  # Dict with 'current_time' and 'timezone'
            }
            or
            {
                "success": False,
                "error": str  # Error description if ServerClock is not properly set up
            }
        """
        if not self.server_clock or "current_time" not in self.server_clock or "timezone" not in self.server_clock:
            return { "success": False, "error": "ServerClock is not properly initialized" }
        return { "success": True, "data": self.server_clock }

    def get_account_info(self, account_id: str) -> dict:
        """
        Retrieve account details (status, balance, currency) given an account_id.

        Args:
            account_id (str): The account's unique identifier.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": AccountInfo  # Dictionary of account details
                }
                On failure:
                {
                    "success": False,
                    "error": "Account not found"
                }

        Constraints:
            - The account_id must exist in the platform.
            - No exceptions raised; errors returned as dict.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account not found" }
        return { "success": True, "data": self.accounts[account_id] }

    def list_all_accounts(self) -> dict:
        """
        List all existing trading accounts with their current balances and statuses.

        Returns:
            dict: {
                "success": True,
                "data": List[AccountInfo],  # May be empty if no accounts exist
            }

        Constraints:
            - No constraints directly apply for query operation.
            - Returns an empty list if no accounts are present.
        """
        account_list = list(self.accounts.values())
        return {
            "success": True,
            "data": account_list
        }

    def get_account_balance(self, account_id: str) -> dict:
        """
        Obtain the current balance and currency of a specific account.

        Args:
            account_id (str): The unique identifier for the account.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": {
                        "balance": float,
                        "currency": str
                    }
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The account_id must exist in the platform's accounts.
        """
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account does not exist" }
        return {
            "success": True,
            "data": {
                "balance": account["balance"],
                "currency": account["currency"]
            }
        }

    def list_trades_by_account(self, account_id: str) -> dict:
        """
        List all executed trades for the given account_id.

        Args:
            account_id (str): The account identifier to retrieve trades for.

        Returns:
            dict: {
                "success": True,
                "data": List[TradeInfo],  # A list of matching trade dicts, or empty if no trades found.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error when account not found.
            }

        Constraints:
            - The account_id must exist in the accounts dictionary.
            - Only trades where trade_info["account_id"] == account_id are included.
        """
        if account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist"}

        result = [
            trade_info for trade_info in self.trades.values()
            if trade_info["account_id"] == account_id
        ]

        return {"success": True, "data": result}

    def get_trade_info(self, trade_id: str) -> dict:
        """
        Retrieve comprehensive details of a trade by trade_id.

        Args:
            trade_id (str): The unique identifier of the trade.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": TradeInfo  # details of the trade
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Trade not found"
                    }

        Constraints:
            - trade_id must exist in the self.trades dictionary.
        """
        trade = self.trades.get(trade_id)
        if trade is None:
            return { "success": False, "error": "Trade not found" }
        return { "success": True, "data": trade }

    def list_open_trades(self, status: str = "open") -> dict:
        """
        List all trades that have the specified status (default: "open") in the system.

        Args:
            status (str): Trade status to filter by (e.g., "open", "active", "filled", etc.).
                          Defaults to "open".

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[TradeInfo]  # List of trades matching the status (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error message
                    }

        Constraints:
            - No state change; only trade status is filtered.
        """
        if not isinstance(status, str) or not status:
            return { "success": False, "error": "Status filter must be a non-empty string." }

        matching_trades = [
            trade for trade in self.trades.values()
            if trade.get("status", "").lower() == status.lower()
        ]

        return { "success": True, "data": matching_trades }

    def list_markets(self) -> dict:
        """
        Retrieve basic information about all configured markets.

        Returns:
            dict: {
                "success": True,
                "data": List[MarketInfo],  # List of all market info (can be empty)
            }

        Constraints:
            - No parameters needed.
            - Always succeeds (even with zero markets).
        """
        market_list = list(self.markets.values())
        return {
            "success": True,
            "data": market_list
        }

    def get_market_status(self, market_id: str) -> dict:
        """
        Query the current status and scheduled open/close hours for a specified market.

        Args:
            market_id (str): The unique identifier of the market.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "market_id": str,
                            "status": str,
                            "open_time": float|str,
                            "close_time": float|str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "Market not found"
                    }

        Constraints:
            - The specified market_id must exist in the system.
        """
        market = self.markets.get(market_id)
        if market is None:
            return {"success": False, "error": "Market not found"}

        # Prepare result with required fields only
        data = {
            "market_id": market["market_id"],
            "status": market["status"],
            "open_time": market["open_time"],
            "close_time": market["close_time"]
        }
        return {"success": True, "data": data}

    def get_system_log_by_id(self, log_id: str) -> dict:
        """
        Retrieve details of a specific system log entry by its unique log_id.

        Args:
            log_id (str): The unique identifier of the system log entry.

        Returns:
            dict: {
                "success": True,
                "data": SystemLogInfo   # The log entry data
            }
            or
            {
                "success": False,
                "error": str   # Description of error, e.g., "Log entry not found"
            }

        Constraints:
            - The log_id must exist in self.system_logs.
        """
        log_entry = self.system_logs.get(log_id)
        if log_entry is None:
            return {"success": False, "error": "Log entry not found"}
        return {"success": True, "data": log_entry}


    def list_system_logs(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> dict:
        """
        Fetch system logs with optional filters.

        Args:
            event_type (Optional[str]): Only return logs with this event_type if provided.
            severity (Optional[str]): Only return logs with this severity if provided.
            start_time (Optional[float]): Only logs with timestamp >= start_time (if provided).
            end_time (Optional[float]): Only logs with timestamp <= end_time (if provided).

        Returns:
            dict:
                success: bool
                data: List[SystemLogInfo] (may be empty if no logs match)
                error: str  (only on parameter type failure)

        Constraints:
            - All logs have timestamps.
        """

        def _coerce_timestamp(value):
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
                try:
                    return float(value)
                except ValueError:
                    pass
                try:
                    iso_value = value.replace("Z", "+00:00")
                    return datetime.fromisoformat(iso_value).timestamp()
                except ValueError:
                    return None
            return None

        logs = list(self.system_logs.values())

        # Filtering
        filtered_logs = []
        for log in logs:
            if event_type is not None and log.get("event_type") != event_type:
                continue
            if severity is not None and log.get("severity") != severity:
                continue

            if start_time is not None or end_time is not None:
                log_ts = _coerce_timestamp(log.get("timestamp"))
                if log_ts is None:
                    continue
                if start_time is not None and log_ts < start_time:
                    continue
                if end_time is not None and log_ts > end_time:
                    continue
            filtered_logs.append(log)

        return { "success": True, "data": filtered_logs }

    def get_operational_metrics(self, metric_type: str = None) -> dict:
        """
        Retrieve recent or aggregated operational statistics (operational metrics),
        optionally filtered by metric_type.

        Args:
            metric_type (str, optional): If provided, only metrics of this type are returned.

        Returns:
            dict: {
                "success": True,
                "data": List[OperationalMetricInfo]  # List of metrics matching the filter (possibly empty)
            }

        Constraints:
            - No modification; purely informational.
            - Returns all metrics if metric_type is None.
        """
        if metric_type is None:
            result = list(self.operational_metrics.values())
        else:
            result = [
                metric for metric in self.operational_metrics.values()
                if metric["metric_type"] == metric_type
            ]
        return { "success": True, "data": result }

    def synchronize_server_clock(self, current_time: 'Union[float, str]', timezone: str) -> dict:
        """
        Update ServerClock to align with an external authoritative time source.

        Args:
            current_time (float|str): The new current time for the authoritative clock. Should be non-negative float (UNIX ts) or valid ISO string.
            timezone (str): The timezone of the authoritative clock (e.g. 'UTC').

        Returns:
            dict: 
              - On success: { "success": True, "message": "ServerClock synchronized to new time." }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - ServerClock must reflect the new authoritative time and timezone.
            - current_time must be valid (not negative if numeric, non-empty if string).
            - timezone must be a non-empty string.
        """
        # Validate timezone
        if not isinstance(timezone, str) or not timezone.strip():
            return { "success": False, "error": "Invalid timezone." }

        # Validate current_time
        if isinstance(current_time, (int, float)):
            if current_time < 0:
                return { "success": False, "error": "current_time must be non-negative." }
        elif isinstance(current_time, str):
            if not current_time.strip():
                return { "success": False, "error": "current_time cannot be empty string." }
            # Optionally: Add more ISO8601 validation if needed.
        else:
            return { "success": False, "error": "Invalid type for current_time." }

        # Update server clock
        self.server_clock["current_time"] = current_time
        self.server_clock["timezone"] = timezone.strip()

        return { "success": True, "message": "ServerClock synchronized to new time." }

    def record_trade(
        self,
        trade_id: str,
        account_id: str,
        instrument_id: str,
        quantity: float,
        price: float,
        status: str
    ) -> dict:
        """
        Add a new executed trade to the platform, updating account balances and time-stamping via ServerClock.

        Args:
            trade_id (str): Unique identifier for the trade (must not duplicate).
            account_id (str): The ID of the trading account (must exist).
            instrument_id (str): Financial instrument's identifier (str, required, assumed valid if non-empty).
            quantity (float): Amount of asset being traded (>0 for buy, <0 for sell).
            price (float): Trade execution price (must be >0).
            status (str): Status of the trade (executed, pending, etc.).

        Returns:
            dict: 
                On success: { "success": True, "message": "Trade recorded and account balance updated." }
                On failure: { "success": False, "error": "Description of the problem" }

        Constraints:
            - trade_id must be unique.
            - account_id must exist.
            - instrument_id must be non-empty.
            - Account balance cannot become negative (unless margin trading enabled, which we assume False).
            - Trades must use ServerClock for time-stamping.
        """
        # Validate input
        if not trade_id:
            return {"success": False, "error": "Trade ID is required."}
        if trade_id in self.trades:
            return {"success": False, "error": "Trade ID already exists."}
        if not account_id or account_id not in self.accounts:
            return {"success": False, "error": "Account does not exist."}
        if not instrument_id:
            return {"success": False, "error": "Instrument ID is required."}
        if not isinstance(quantity, (int, float)):
            return {"success": False, "error": "Quantity must be a number."}
        if not isinstance(price, (int, float)) or price <= 0:
            return {"success": False, "error": "Price must be a positive number."}

        # Get the account
        account = self.accounts[account_id]

        # Calculate the impact on account balance
        # Buy: quantity > 0 -> spend money; Sell: quantity < 0 -> receive money
        cash_flow = -quantity * price  # Buy (quantity>0): negative, Sell (quantity<0): positive

        new_balance = account["balance"] + cash_flow

        if new_balance < 0:
            return {"success": False, "error": "Account balance would become negative."}

        # Prepare trade_time from server clock
        trade_time = self.server_clock["current_time"]

        # Add the trade
        self.trades[trade_id] = {
            "trade_id": trade_id,
            "account_id": account_id,
            "instrument_id": instrument_id,
            "quantity": quantity,
            "price": price,
            "trade_time": trade_time,
            "status": status
        }

        # Update account balance
        account["balance"] = new_balance
        self.accounts[account_id] = account  # Not strictly necessary (dict is mutable), but explicit

        return {"success": True, "message": "Trade recorded and account balance updated."}

    def update_account_balance(self, account_id: str, amount: float) -> dict:
        """
        Adjusts the balance of the specified account by a given amount,
        enforcing the constraint that balances cannot become negative.

        Args:
            account_id (str): The account whose balance is to be updated.
            amount (float): The amount to adjust (positive for deposit/increase, negative for withdrawal/decrease).

        Returns:
            dict: 
                On success: { "success": True, "message": "Balance updated for account <id>: new balance is <value>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Account must exist.
            - The resulting balance must not be negative.
        """
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account does not exist" }
    
        new_balance = account["balance"] + amount
        if new_balance < 0:
            return {
                "success": False,
                "error": "Insufficient funds: negative balance not allowed"
            }

        account["balance"] = new_balance
        self.accounts[account_id] = account

        return {
            "success": True,
            "message": f"Balance updated for account {account_id}: new balance is {new_balance}"
        }

    def update_market_status(self, market_id: str, new_status: str) -> dict:
        """
        Change the operational status of a market (open/close/pause), recording the transition time.
    
        Args:
            market_id (str): The identifier of the market to update.
            new_status (str): The new status ("open", "closed", or "paused").
    
        Returns:
            dict: { "success": True, "message": "Market status updated for <id> to <status>" }
                  or { "success": False, "error": <reason> }
    
        Constraints:
            - Market must exist.
            - Status must be one of "open", "closed", "paused".
            - Status transition timestamp must be recorded with server clock.
        """
        allowed_statuses = {"open", "closed", "paused"}
        if market_id not in self.markets:
            return { "success": False, "error": "Market does not exist" }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Must be one of {allowed_statuses}" }
    
        market = self.markets[market_id]
        market["status"] = new_status

        current_time = self.server_clock["current_time"]
    
        if new_status == "open":
            market["open_time"] = current_time
        elif new_status == "closed":
            market["close_time"] = current_time
        # "paused": No explicit "pause_time" in spec, so do not record new field, just update status
    
        self.markets[market_id] = market
    
        return { "success": True, "message": f"Market status updated for {market_id} to {new_status}" }

    def log_system_event(
        self,
        log_id: str,
        event_type: str,
        message: str,
        severity: str
    ) -> dict:
        """
        Create a new entry in the system log with a timestamp for auditing/debugging.

        Args:
            log_id (str): Unique identifier for this log entry.
            event_type (str): Category/type of the event (e.g., 'trade', 'error').
            message (str): Informative message about the event.
            severity (str): Severity level (e.g., 'info', 'warning', 'error').

        Returns:
            dict: 
              - If successful: { "success": True, "message": "System event logged" }
              - If failed (duplicate log_id): { "success": False, "error": "Log ID already exists" }

        Constraints:
            - log_id must be unique in current logs.
            - All log entries are timestamped with the current ServerClock time.
        """
        if log_id in self.system_logs:
            return { "success": False, "error": "Log ID already exists" }
        timestamp = self.server_clock["current_time"]

        log_entry = {
            "log_id": log_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "severity": severity
        }
        self.system_logs[log_id] = log_entry

        return { "success": True, "message": "System event logged" }

    def update_operational_metric(
        self,
        metric_id: str,
        value: float,
        metric_type: str
    ) -> dict:
        """
        Modify or add a new operational metric at the current server time.
        Always records the update with the up-to-date server clock timestamp.

        Args:
            metric_id (str): Unique identifier of the metric.
            value (float): The value to assign to the metric.
            metric_type (str): Type/category of the metric (e.g., 'latency', 'throughput').

        Returns:
            dict: 
                {"success": True, "message": "..."}
                or
                {"success": False, "error": "<error description>"}
    
        Constraints:
            - metric_id must be a non-empty string.
            - metric_type must be a non-empty string.
            - value must be a float.
            - timestamp must be set to the current server time.
        """
        # Validate inputs
        if not metric_id or not isinstance(metric_id, str):
            return {"success": False, "error": "Invalid or empty metric_id"}
        if not isinstance(value, (float, int)):
            return {"success": False, "error": "Metric value must be a number"}
        if not metric_type or not isinstance(metric_type, str):
            return {"success": False, "error": "Invalid or empty metric_type"}
        if "current_time" not in self.server_clock:
            return {"success": False, "error": "Server clock not initialized"}

        # Stamp with current server time
        ts = self.server_clock["current_time"]

        metric_info = {
            "metric_id": metric_id,
            "value": float(value),
            "timestamp": ts,
            "metric_type": metric_type,
        }
        self.operational_metrics[metric_id] = metric_info

        return {"success": True, "message": "Operational metric updated/added successfully"}

    def update_trade_status(self, trade_id: str, new_status: str) -> dict:
        """
        Alter the status of an executed trade to the specified new status.

        Args:
            trade_id (str): Unique identifier of the trade to update.
            new_status (str): The new status to assign to the trade.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Trade status updated." }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The trade must exist (trade_id must be in self.trades).
            - Status can be changed to any string (no restriction unless specified).
            - Does not log the status update or record its time unless this is required elsewhere.
        """
        trade = self.trades.get(trade_id)
        if trade is None:
            return { "success": False, "error": "Trade not found." }
        if not isinstance(new_status, str) or not new_status:
            return { "success": False, "error": "New status must be a non-empty string." }

        trade["status"] = new_status
        # Optionally: could log this event or update a modified timestamp
        return { "success": True, "message": "Trade status updated." }

    def create_account(self, account_id: str, balance: float, currency: str, status: str) -> dict:
        """
        Add a new account to the platform with an initial balance and status.

        Args:
            account_id (str): Unique identifier for the new account.
            balance (float): Initial balance (must be non-negative unless margin trading is enabled).
            currency (str): Currency code, e.g., 'USD'.
            status (str): Initial status of the account, e.g., 'active'.

        Returns:
            dict: {
                "success": True,
                "message": "Account <account_id> created successfully."
            }
            or {
                "success": False,
                "error": "Reason why account was not created."
            }

        Constraints:
            - Account_id must be unique.
            - Initial balance must not be negative (assuming no margin trading support).
        """

        if account_id in self.accounts:
            return { "success": False, "error": "Account already exists." }

        if balance < 0:
            return { "success": False, "error": "Initial balance cannot be negative." }

        # Create and insert AccountInfo
        new_account: AccountInfo = {
            "account_id": account_id,
            "balance": balance,
            "currency": currency,
            "status": status
        }
        self.accounts[account_id] = new_account

        return {
            "success": True,
            "message": f"Account {account_id} created successfully."
        }

    def close_account(self, account_id: str) -> dict:
        """
        Close an account by setting its status to 'closed'.

        Args:
            account_id (str): The identifier of the account to close.

        Returns:
            dict: {
                "success": True,
                "message": "Account {account_id} status set to closed."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The account must exist.
            - Sets status to 'closed' regardless of current balance.
        """
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "error": "Account does not exist."}

        if account["status"] == "closed":
            return {"success": False, "error": f"Account {account_id} is already closed."}

        account["status"] = "closed"
        self.accounts[account_id] = account

        return {
            "success": True,
            "message": f"Account {account_id} status set to closed."
        }


class FinancialTradingPlatformBackend(BaseEnv):
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

    def get_current_server_time(self, **kwargs):
        return self._call_inner_tool('get_current_server_time', kwargs)

    def get_account_info(self, **kwargs):
        return self._call_inner_tool('get_account_info', kwargs)

    def list_all_accounts(self, **kwargs):
        return self._call_inner_tool('list_all_accounts', kwargs)

    def get_account_balance(self, **kwargs):
        return self._call_inner_tool('get_account_balance', kwargs)

    def list_trades_by_account(self, **kwargs):
        return self._call_inner_tool('list_trades_by_account', kwargs)

    def get_trade_info(self, **kwargs):
        return self._call_inner_tool('get_trade_info', kwargs)

    def list_open_trades(self, **kwargs):
        return self._call_inner_tool('list_open_trades', kwargs)

    def list_markets(self, **kwargs):
        return self._call_inner_tool('list_markets', kwargs)

    def get_market_status(self, **kwargs):
        return self._call_inner_tool('get_market_status', kwargs)

    def get_system_log_by_id(self, **kwargs):
        return self._call_inner_tool('get_system_log_by_id', kwargs)

    def list_system_logs(self, **kwargs):
        return self._call_inner_tool('list_system_logs', kwargs)

    def get_operational_metrics(self, **kwargs):
        return self._call_inner_tool('get_operational_metrics', kwargs)

    def synchronize_server_clock(self, **kwargs):
        return self._call_inner_tool('synchronize_server_clock', kwargs)

    def record_trade(self, **kwargs):
        return self._call_inner_tool('record_trade', kwargs)

    def update_account_balance(self, **kwargs):
        return self._call_inner_tool('update_account_balance', kwargs)

    def update_market_status(self, **kwargs):
        return self._call_inner_tool('update_market_status', kwargs)

    def log_system_event(self, **kwargs):
        return self._call_inner_tool('log_system_event', kwargs)

    def update_operational_metric(self, **kwargs):
        return self._call_inner_tool('update_operational_metric', kwargs)

    def update_trade_status(self, **kwargs):
        return self._call_inner_tool('update_trade_status', kwargs)

    def create_account(self, **kwargs):
        return self._call_inner_tool('create_account', kwargs)

    def close_account(self, **kwargs):
        return self._call_inner_tool('close_account', kwargs)
