# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict
from datetime import datetime
from typing import Optional, Dict



class CompanyInfo(TypedDict):
    company_id: str
    name: str
    ticker: str
    sector: str
    industry: str

class FinancialStatementInfo(TypedDict):
    statement_id: str
    company_id: str
    statement_type: str  # e.g., balance sheet, income statement, cash flow statement
    period_start_date: str
    period_end_date: str
    filing_date: str
    data: Any  # Could be a dict or other structure

class PerformanceMetricInfo(TypedDict):
    metric_id: str
    company_id: str
    metric_type: str  # e.g., EPS, ROE
    period_end_date: str
    val: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Companies: {company_id: CompanyInfo}
        self.companies: Dict[str, CompanyInfo] = {}
        # FinancialStatements: {statement_id: FinancialStatementInfo}
        self.financial_statements: Dict[str, FinancialStatementInfo] = {}
        # PerformanceMetrics: {metric_id: PerformanceMetricInfo}
        self.performance_metrics: Dict[str, PerformanceMetricInfo] = {}

        # Constraints:
        # - Each financial statement must be linked to a valid company.
        # - Only one statement of a given type per company per unique reporting period is allowed.
        # - "Latest" statements are determined by the most recent period_end_date or filing_date for a statement type.
        # - Company identifiers must be unique.

    def get_company_by_id(self, company_id: str) -> dict:
        """
        Retrieve full information about a company using its unique company_id.

        Args:
            company_id (str): Unique identifier for the company.

        Returns:
            dict:
              - On success: {"success": True, "data": CompanyInfo}
              - On failure: {"success": False, "error": <reason>}
          
        Constraints:
            - The given company_id must exist in the repository.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company ID does not exist" }

        return { "success": True, "data": self.companies[company_id] }

    def get_company_by_ticker(self, ticker: str) -> dict:
        """
        Retrieve company details via its ticker symbol.

        Args:
            ticker (str): The ticker symbol of the company (case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": CompanyInfo
            }
            or
            {
                "success": False,
                "error": "Ticker not found"
            }

        Constraints:
            - Ticker symbols are unique across companies.
            - Match ticker case-insensitively for robustness.
        """
        ticker = ticker.upper()
        for company in self.companies.values():
            if company["ticker"].upper() == ticker:
                return {"success": True, "data": company}
        return {"success": False, "error": "Ticker not found"}

    def list_companies(self) -> dict:
        """
        List all companies in the repository.

        Returns:
            dict: {
                "success": True,
                "data": List[CompanyInfo]  # May be an empty list if no companies exist
            }
        """
        result = list(self.companies.values())
        return { "success": True, "data": result }

    def get_financial_statements_by_company(self, company_id: str) -> dict:
        """
        Retrieve all financial statements associated with the specified company_id.

        Args:
            company_id (str): Unique company identifier.

        Returns:
            dict:
                - If success:
                    {
                        "success": True,
                        "data": List[FinancialStatementInfo]  # List of all financial statements (possibly empty) for this company
                    }
                - If company_id does not exist:
                    {
                        "success": False,
                        "error": "Company not found"
                    }

        Constraints:
            - The company_id must exist in the repository.
        """
        if company_id not in self.companies:
            return {"success": False, "error": "Company not found"}

        statements = [
            statement for statement in self.financial_statements.values()
            if statement["company_id"] == company_id
        ]
        return {"success": True, "data": statements}

    def get_financial_statements_by_type(self, company_id: str, statement_type: str) -> dict:
        """
        Retrieve all financial statements of a specific type for a given company.

        Args:
            company_id (str): The unique identifier of the company.
            statement_type (str): The financial statement type (e.g., 'balance sheet', 'income statement', 'cash flow statement').

        Returns:
            dict: {
                "success": True,
                "data": List[FinancialStatementInfo]  # May be empty if no statements exist.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., company does not exist.
            }

        Constraints:
            - The specified company must exist.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }

        result = [
            stmt for stmt in self.financial_statements.values()
            if stmt["company_id"] == company_id and stmt["statement_type"] == statement_type
        ]
        return { "success": True, "data": result }

    def get_financial_statement_by_id(self, statement_id: str) -> dict:
        """
        Retrieve a specific financial statement by its statement_id.

        Args:
            statement_id (str): Unique identifier for the financial statement.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": FinancialStatementInfo  # Full statement information
                }
                or
                {
                    "success": False,
                    "error": str  # Reason, e.g. not found
                }
        Constraints:
            - statement_id must exist in the repository.
        """
        statement = self.financial_statements.get(statement_id)
        if statement is None:
            return { "success": False, "error": "Financial statement not found" }
        return { "success": True, "data": statement }


    def get_latest_financial_statement_by_type(self, company_id: str, statement_type: str) -> Dict[str, Optional[dict]]:
        """
        For a company and statement type, retrieve the statement with the latest period_end_date (and, as a tiebreaker, filing_date).

        Args:
            company_id (str): The unique identifier of the company.
            statement_type (str): Statement type (e.g., 'balance sheet', 'income statement').

        Returns:
            dict: {
                "success": True,
                "data": FinancialStatementInfo or None,  # None if no statement for criteria
            }
            or
            {
                "success": False,
                "error": str,  # Error message
            }

        Constraints:
            - company_id must exist in the repository.
            - If multiple statements have the same (latest) period_end_date, use latest filing_date.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }

        statements = [
            s for s in self.financial_statements.values()
            if s["company_id"] == company_id and s["statement_type"] == statement_type
        ]

        if not statements:
            return { "success": True, "data": None }

        # Helper to get date for comparison, fallback to minimal
        def parse_date(d: str) -> datetime:
            try:
                return datetime.fromisoformat(d)
            except Exception:
                return datetime.min

        # Sort by period_end_date, then filing_date descending
        statements.sort(
            key=lambda s: (
                parse_date(s["period_end_date"]),
                parse_date(s["filing_date"])
            ),
            reverse=True
        )

        latest_statement = statements[0]
        return { "success": True, "data": latest_statement }

    def get_performance_metrics_by_company(self, company_id: str) -> dict:
        """
        Retrieve all performance metrics calculated for a given company.

        Args:
            company_id (str): The unique identifier of the company.

        Returns:
            dict: {
                "success": True,
                "data": List[PerformanceMetricInfo],
            }
            or
            {
                "success": False,
                "error": str  # Error reason (e.g., company does not exist)
            }

        Constraints:
            - The specified company must exist in the repository.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }

        metrics = [
            metric_info
            for metric_info in self.performance_metrics.values()
            if metric_info["company_id"] == company_id
        ]

        return { "success": True, "data": metrics }

    def get_performance_metrics_by_type(self, company_id: str, metric_type: str) -> dict:
        """
        Retrieve all performance metrics of a given type for a specific company.

        Args:
            company_id (str): The unique identifier for the company.
            metric_type (str): Type of the metric to retrieve (e.g., "EPS", "ROE").

        Returns:
            dict: {
                "success": True,
                "data": List[PerformanceMetricInfo]  # all matching metrics (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g. if company not found
            }

        Constraints:
            - The company_id must exist in the repository.
            - Returns empty list if no metrics of this type for the company.
        """
        if company_id not in self.companies:
            return {"success": False, "error": "Company not found"}

        result = [
            metric_info for metric_info in self.performance_metrics.values()
            if metric_info['company_id'] == company_id and metric_info['metric_type'] == metric_type
        ]

        return {"success": True, "data": result}

    def get_performance_metric_by_id(self, metric_id: str) -> dict:
        """
        Retrieve a specific performance metric using its metric_id.

        Args:
            metric_id (str): The unique identifier for the performance metric.

        Returns:
            dict: {
                "success": True,
                "data": PerformanceMetricInfo  # The matching performance metric info
            }
            or
            {
                "success": False,
                "error": str  # If the metric_id does not exist
            }

        Constraints:
            - The metric_id must exist in the repository.
        """
        if metric_id not in self.performance_metrics:
            return { "success": False, "error": "Performance metric not found" }
    
        metric_info = self.performance_metrics[metric_id]
        return { "success": True, "data": metric_info }

    def add_company(self, company_id: str, name: str, ticker: str, sector: str, industry: str) -> dict:
        """
        Add a new company record.

        Args:
            company_id (str): Unique identifier for the company.
            name (str): Name of the company.
            ticker (str): Ticker symbol.
            sector (str): Business sector.
            industry (str): Industry group.

        Returns:
            dict: 
                Success: { "success": True, "message": "Company added successfully." }
                Failure: { "success": False, "error": "reason" }

        Constraints:
            - company_id must be unique (not already in the repository).
            - All fields must be provided and non-empty strings.
        """
        required_fields = {
            "company_id": company_id,
            "name": name,
            "ticker": ticker,
            "sector": sector,
            "industry": industry,
        }
        for field, value in required_fields.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return { "success": False, "error": f"Missing or empty required field: {field}" }

        if company_id in self.companies:
            return { "success": False, "error": "Company ID already exists." }

        self.companies[company_id] = {
            "company_id": company_id,
            "name": name,
            "ticker": ticker,
            "sector": sector,
            "industry": industry,
        }

        return { "success": True, "message": "Company added successfully." }

    def update_company(self, company_id: str, update_fields: dict) -> dict:
        """
        Update the descriptive attributes (name, ticker, sector, industry) of an existing company.

        Args:
            company_id (str): Unique ID of the company to update.
            update_fields (dict): Dictionary of attribute names (name, ticker, sector, industry) and their new values.

        Returns:
            dict: {
                "success": True,
                "message": "Company updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - company_id must exist.
            - Only allowed attributes (name, ticker, sector, industry) can be updated.
            - company_id itself cannot be updated.
            - At least one valid attribute must be provided for update.
        """
        allowed_fields = {"name", "ticker", "sector", "industry"}
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }

        # Filter for valid fields only
        valid_updates = {k: v for k, v in update_fields.items() if k in allowed_fields}

        if not valid_updates:
            return { "success": False, "error": "No valid fields provided for update" }

        for attr, value in valid_updates.items():
            self.companies[company_id][attr] = value

        return { "success": True, "message": "Company updated successfully" }

    def add_financial_statement(
        self,
        statement_id: str,
        company_id: str,
        statement_type: str,
        period_start_date: str,
        period_end_date: str,
        filing_date: str,
        data: Any
    ) -> dict:
        """
        Add a new financial statement to the repository.

        Args:
            statement_id (str): Unique identifier for the financial statement.
            company_id (str): Identifier of the company the statement is linked to.
            statement_type (str): Type of statement (e.g., balance sheet, income statement, cash flow statement).
            period_start_date (str): Start date of the reported period.
            period_end_date (str): End date of the reported period.
            filing_date (str): Filing date of the statement.
            data (Any): Statement data, usually a dict or similar structure.

        Returns:
            dict: {
                "success": True,
                "message": "Financial statement added"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - company_id must exist in the repository.
            - Only one statement of each type per company per (period_start_date, period_end_date) is allowed.
            - statement_id must be unique.
        """
        # Constraint 1: company_id must exist
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }

        # Constraint 2: statement_id must be unique
        if statement_id in self.financial_statements:
            return { "success": False, "error": "Statement ID already exists" }

        # Constraint 3: Only one statement of this type per company per period
        for stmt in self.financial_statements.values():
            if (
                stmt["company_id"] == company_id and
                stmt["statement_type"] == statement_type and
                stmt["period_start_date"] == period_start_date and
                stmt["period_end_date"] == period_end_date
            ):
                return {
                    "success": False,
                    "error": "Statement for this type and period already exists for this company"
                }

        # Add new statement
        self.financial_statements[statement_id] = {
            "statement_id": statement_id,
            "company_id": company_id,
            "statement_type": statement_type,
            "period_start_date": period_start_date,
            "period_end_date": period_end_date,
            "filing_date": filing_date,
            "data": data
        }
        return { "success": True, "message": "Financial statement added" }

    def update_financial_statement(self, statement_id: str, updates: dict) -> dict:
        """
        Modify the fields or data contents of an existing financial statement.

        Args:
            statement_id (str): ID of the financial statement to update.
            updates (dict): Dictionary of fields to update (e.g., statement_type, company_id,
                            period_start_date, period_end_date, filing_date, data).

        Returns:
            dict: {
                "success": True,
                "message": "Financial statement <statement_id> updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - statement_id must exist.
            - If company_id is modified, new company_id must exist.
            - Cannot create a duplicate (company_id, statement_type, period_start_date, period_end_date)
              for the same company and statement_type in the same reporting period.
        """
        if statement_id not in self.financial_statements:
            return { "success": False, "error": "Financial statement does not exist." }

        fs = self.financial_statements[statement_id]
        # Copy original values (for comparison and to handle partial updates)
        current_company_id = fs["company_id"]
        current_statement_type = fs["statement_type"]
        current_period_start_date = fs["period_start_date"]
        current_period_end_date = fs["period_end_date"]

        # Determine what the new identity tuple would be:
        new_company_id = updates.get("company_id", current_company_id)
        new_statement_type = updates.get("statement_type", current_statement_type)
        new_period_start_date = updates.get("period_start_date", current_period_start_date)
        new_period_end_date = updates.get("period_end_date", current_period_end_date)
        # If company_id is being changed, check existence
        if new_company_id != current_company_id:
            if new_company_id not in self.companies:
                return { "success": False, "error": "Target company does not exist." }
        # Constraint: only one (company_id, statement_type, period_start_date, period_end_date)
        for other_id, other_fs in self.financial_statements.items():
            if other_id == statement_id:
                continue
            if (other_fs["company_id"] == new_company_id and
                other_fs["statement_type"] == new_statement_type and
                other_fs["period_start_date"] == new_period_start_date and
                other_fs["period_end_date"] == new_period_end_date):
                return { "success": False, "error": "Duplicate statement for this company, type, and reporting period already exists." }
        # Valid, so update allowed fields
        mutable_keys = {"company_id", "statement_type", "period_start_date", "period_end_date", "filing_date", "data"}
        for k, v in updates.items():
            if k in mutable_keys:
                fs[k] = v
        self.financial_statements[statement_id] = fs
        return { "success": True, "message": f"Financial statement {statement_id} updated successfully." }

    def add_performance_metric(
        self,
        metric_id: str,
        company_id: str,
        metric_type: str,
        period_end_date: str,
        val: float
    ) -> dict:
        """
        Add a new computed performance metric for a company.

        Args:
            metric_id (str): Unique identifier for this performance metric.
            company_id (str): Identifier of the company this metric relates to.
            metric_type (str): Type of metric (e.g., EPS, ROE, etc.).
            period_end_date (str): Period end date this metric covers (ISO string).
            val (float): The computed value of the metric.

        Returns:
            dict: 
                {"success": True, "message": "Performance metric added for company <company_id>."}
                or
                {"success": False, "error": <error_message>}
        Constraints:
            - metric_id must be unique.
            - company_id must exist.
        """
        if metric_id in self.performance_metrics:
            return {"success": False, "error": "metric_id already exists."}
        if company_id not in self.companies:
            return {"success": False, "error": "company_id does not exist."}
        metric_info: PerformanceMetricInfo = {
            "metric_id": metric_id,
            "company_id": company_id,
            "metric_type": metric_type,
            "period_end_date": period_end_date,
            "val": val
        }
        self.performance_metrics[metric_id] = metric_info
        return {"success": True, "message": f"Performance metric added for company {company_id}."}

    def update_performance_metric(
        self,
        metric_id: str,
        company_id: str = None,
        metric_type: str = None,
        period_end_date: str = None,
        val: float = None
    ) -> dict:
        """
        Modify an existing performance metric record.

        Args:
            metric_id (str): ID of the performance metric to update.
            company_id (str, optional): New company_id. If set, must refer to a valid company.
            metric_type (str, optional): New metric_type.
            period_end_date (str, optional): New period_end_date.
            val (float, optional): New value.

        Returns:
            dict: {
                "success": True,
                "message": "Performance metric <metric_id> updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - metric_id must exist.
            - If updating company_id, the company must exist.
        """
        if metric_id not in self.performance_metrics:
            return {"success": False, "error": "Performance metric does not exist."}
    
        metric = self.performance_metrics[metric_id]
        updated_fields = []

        if company_id is not None:
            if company_id not in self.companies:
                return {"success": False, "error": "New company_id does not exist."}
            metric["company_id"] = company_id
            updated_fields.append("company_id")
        if metric_type is not None:
            metric["metric_type"] = metric_type
            updated_fields.append("metric_type")
        if period_end_date is not None:
            metric["period_end_date"] = period_end_date
            updated_fields.append("period_end_date")
        if val is not None:
            metric["val"] = val
            updated_fields.append("val")

        if not updated_fields:
            return {"success": False, "error": "No fields provided to update."}

        self.performance_metrics[metric_id] = metric

        return {
            "success": True,
            "message": f"Performance metric {metric_id} updated: {', '.join(updated_fields)}."
        }

    def delete_company(self, company_id: str) -> dict:
        """
        Remove a company and all associated financial statements and performance metrics.

        Args:
            company_id (str): The unique ID of the company to be removed.

        Returns:
            dict: 
                - On success: 
                    {"success": True, "message": "Company <company_id> and all associated records have been deleted."}
                - On failure (company not found): 
                    {"success": False, "error": "Company not found."}

        Constraints:
            - All FinancialStatements and PerformanceMetrics linked to company_id are deleted.
            - Company must exist.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company not found." }

        # Remove associated financial statements
        statements_to_delete = [
            sid for sid, s in self.financial_statements.items()
            if s["company_id"] == company_id
        ]
        for sid in statements_to_delete:
            del self.financial_statements[sid]

        # Remove associated performance metrics
        metrics_to_delete = [
            mid for mid, m in self.performance_metrics.items()
            if m["company_id"] == company_id
        ]
        for mid in metrics_to_delete:
            del self.performance_metrics[mid]

        # Remove the company itself
        del self.companies[company_id]

        return {
            "success": True, 
            "message": f"Company {company_id} and all associated records have been deleted."
        }

    def delete_financial_statement(self, statement_id: str) -> dict:
        """
        Remove a specific financial statement by its unique identifier.

        Args:
            statement_id (str): The unique ID of the financial statement to delete.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Financial statement <statement_id> deleted." }
                - On failure: { "success": False, "error": "Financial statement does not exist." }

        Constraints:
            - The financial statement with the given ID must exist to be deleted.
        """
        if statement_id not in self.financial_statements:
            return { "success": False, "error": "Financial statement does not exist." }
        del self.financial_statements[statement_id]
        return { "success": True, "message": f"Financial statement {statement_id} deleted." }

    def delete_performance_metric(self, metric_id: str) -> dict:
        """
        Remove a specific performance metric from the repository by its metric_id.

        Args:
            metric_id (str): Identifier of the performance metric to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "Performance metric <metric_id> deleted." }
                On failure: { "success": False, "error": "Performance metric not found." }

        Constraints:
            - metric_id must exist in the performance_metrics store.
        """
        if metric_id not in self.performance_metrics:
            return { "success": False, "error": "Performance metric not found." }
        del self.performance_metrics[metric_id]
        return { "success": True, "message": f"Performance metric {metric_id} deleted." }


class FinancialDataRepository(BaseEnv):
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

    def get_company_by_id(self, **kwargs):
        return self._call_inner_tool('get_company_by_id', kwargs)

    def get_company_by_ticker(self, **kwargs):
        return self._call_inner_tool('get_company_by_ticker', kwargs)

    def list_companies(self, **kwargs):
        return self._call_inner_tool('list_companies', kwargs)

    def get_financial_statements_by_company(self, **kwargs):
        return self._call_inner_tool('get_financial_statements_by_company', kwargs)

    def get_financial_statements_by_type(self, **kwargs):
        return self._call_inner_tool('get_financial_statements_by_type', kwargs)

    def get_financial_statement_by_id(self, **kwargs):
        return self._call_inner_tool('get_financial_statement_by_id', kwargs)

    def get_latest_financial_statement_by_type(self, **kwargs):
        return self._call_inner_tool('get_latest_financial_statement_by_type', kwargs)

    def get_performance_metrics_by_company(self, **kwargs):
        return self._call_inner_tool('get_performance_metrics_by_company', kwargs)

    def get_performance_metrics_by_type(self, **kwargs):
        return self._call_inner_tool('get_performance_metrics_by_type', kwargs)

    def get_performance_metric_by_id(self, **kwargs):
        return self._call_inner_tool('get_performance_metric_by_id', kwargs)

    def add_company(self, **kwargs):
        return self._call_inner_tool('add_company', kwargs)

    def update_company(self, **kwargs):
        return self._call_inner_tool('update_company', kwargs)

    def add_financial_statement(self, **kwargs):
        return self._call_inner_tool('add_financial_statement', kwargs)

    def update_financial_statement(self, **kwargs):
        return self._call_inner_tool('update_financial_statement', kwargs)

    def add_performance_metric(self, **kwargs):
        return self._call_inner_tool('add_performance_metric', kwargs)

    def update_performance_metric(self, **kwargs):
        return self._call_inner_tool('update_performance_metric', kwargs)

    def delete_company(self, **kwargs):
        return self._call_inner_tool('delete_company', kwargs)

    def delete_financial_statement(self, **kwargs):
        return self._call_inner_tool('delete_financial_statement', kwargs)

    def delete_performance_metric(self, **kwargs):
        return self._call_inner_tool('delete_performance_metric', kwargs)

