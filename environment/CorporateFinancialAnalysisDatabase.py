# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class CompanyInfo(TypedDict, total=False):
    # "etc." fields are allowed as optional
    company_id: str
    name: str
    sector: str

class FinancialPeriodInfo(TypedDict):
    period_id: str
    company_id: str
    year: int
    start_date: str
    end_date: str

class FinancialMetricInfo(TypedDict):
    metric_id: str
    company_id: str
    period_id: str
    metric_name: str
    metric_val: float

class FinancialStatementEntryInfo(TypedDict):
    entry_id: str
    company_id: str
    period_id: str
    entry_type: str
    val: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Corporate financial analysis database environment.
        """

        # Companies: {company_id: CompanyInfo}
        self.companies: Dict[str, CompanyInfo] = {}

        # Financial Periods: {period_id: FinancialPeriodInfo}
        self.financial_periods: Dict[str, FinancialPeriodInfo] = {}

        # Financial Metrics: {metric_id: FinancialMetricInfo}
        self.financial_metrics: Dict[str, FinancialMetricInfo] = {}

        # Financial Statement Entries: {entry_id: FinancialStatementEntryInfo}
        self.financial_statement_entries: Dict[str, FinancialStatementEntryInfo] = {}

        # Constraints:
        # - Each FinancialMetric and FinancialStatementEntry must reference a valid company and financial period.
        # - Metric values must align with the correct financial period as defined in FinancialPeriod.
        # - Derived ratios must be calculated from corresponding FinancialStatementEntries as per standards.

    def get_company_by_id(self, company_id: str) -> dict:
        """
        Retrieve detailed company information using the company_id.

        Args:
            company_id (str): The unique identifier for the target company.

        Returns:
            dict: {
                "success": True,
                "data": CompanyInfo  # Detailed info dictionary for the company
            }
            or
            {
                "success": False,
                "error": str  # Description if not found
            }

        Constraints:
            - company_id must exist in the database.
        """
        company = self.companies.get(company_id)
        if not company:
            return {"success": False, "error": "Company not found"}
        return {"success": True, "data": company}

    def list_company_periods(self, company_id: str) -> dict:
        """
        List all financial periods (with ids and dates) for a given company.

        Args:
            company_id (str): Unique company identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[FinancialPeriodInfo],  # possibly empty if no periods
            }
            or
            {
                "success": False,
                "error": str  # "Company does not exist"
            }

        Constraints:
            - The company_id must exist in the database.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }
    
        periods = [
            period_info for period_info in self.financial_periods.values()
            if period_info["company_id"] == company_id
        ]
        return { "success": True, "data": periods }

    def get_latest_period_for_company(self, company_id: str) -> dict:
        """
        Identify and return the most recent (latest) financial period for a given company.

        Args:
            company_id (str): Unique identifier of the company.

        Returns:
            dict: 
                On success:
                  {
                    "success": True, 
                    "data": FinancialPeriodInfo  # Info for latest period
                  }
                On failure:
                  {
                    "success": False, 
                    "error": str  # Reason for failure, e.g., company/period not found
                  }

        Constraints:
            - The company must exist in the database.
            - The latest period is determined by the greatest 'year', and if there are duplicates, the latest 'end_date'.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company not found" }

        periods = [
            p for p in self.financial_periods.values()
            if p["company_id"] == company_id
        ]

        if not periods:
            return { "success": False, "error": "No financial periods found for company" }

        # Sort periods by year descending, then by end_date descending
        periods_sorted = sorted(
            periods, 
            key=lambda p: (p["year"], p["end_date"]), 
            reverse=True
        )
        latest_period = periods_sorted[0]

        return { "success": True, "data": latest_period }

    def list_metrics_for_company_period(self, company_id: str, period_id: str) -> dict:
        """
        List all financial metrics for a company in a specific financial period.

        Args:
            company_id (str): Unique identifier of the company.
            period_id (str): Unique identifier of the financial period (must match the company_id).

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[FinancialMetricInfo],  # possibly empty if no metrics exist
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # reason (e.g. company or period invalid)
                    }

        Constraints:
            - The company_id must exist in the companies dictionary.
            - The period_id must exist and must belong to the specified company.
        """
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist."}
        period = self.financial_periods.get(period_id)
        if period is None:
            return {"success": False, "error": "Financial period does not exist."}
        if period["company_id"] != company_id:
            return {"success": False, "error": "Period does not belong to the given company."}
    
        results = [
            metric for metric in self.financial_metrics.values()
            if metric["company_id"] == company_id and metric["period_id"] == period_id
        ]
        return {"success": True, "data": results}

    def get_metric_by_name(self, company_id: str, period_id: str, metric_name: str) -> dict:
        """
        Retrieve the value and metadata for a specific metric (e.g., ROA) assigned to a given company and financial period.

        Args:
            company_id (str): Unique identifier of the company.
            period_id (str): Unique identifier of the financial period.
            metric_name (str): The name of the requested metric (case-sensitive).

        Returns:
            dict:
                { "success": True, "data": FinancialMetricInfo } if metric exists,
                or { "success": False, "error": <reason> } if not found or parameters invalid.

        Constraints:
            - Only returns metrics where company_id and period_id are registered and metric_name matches.
            - Enforces referential integrity.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company ID does not exist" }

        if period_id not in self.financial_periods:
            return { "success": False, "error": "Period ID does not exist" }

        # The metric_name match is case-sensitive, as commonly used in such systems.
        for metric in self.financial_metrics.values():
            if (metric['company_id'] == company_id and
                metric['period_id'] == period_id and
                metric['metric_name'] == metric_name):
                return { "success": True, "data": metric }

        return { "success": False, "error": "Metric not found" }

    def list_statement_entries_for_company_period(self, company_id: str, period_id: str) -> dict:
        """
        List all financial statement entries (entry_type and value) for the given company and period.

        Args:
            company_id (str): The unique identifier of the company.
            period_id (str): The unique identifier of the financial period.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": [
                            {"entry_type": str, "val": float},
                            ...
                        ]
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - Both company_id and period_id must exist.
            - The period_id must correspond to the given company_id.
        """
        # Check company existence
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist"}

        # Check period existence
        period = self.financial_periods.get(period_id)
        if not period:
            return {"success": False, "error": "Financial period does not exist"}
        if period['company_id'] != company_id:
            return {"success": False, "error": "Financial period does not belong to the specified company"}

        # Filter and collect statement entries
        entries = [
            {"entry_type": entry['entry_type'], "val": entry['val']}
            for entry in self.financial_statement_entries.values()
            if entry['company_id'] == company_id and entry['period_id'] == period_id
        ]

        return {"success": True, "data": entries}

    def get_statement_entry_by_type(self, company_id: str, period_id: str, entry_type: str) -> dict:
        """
        Retrieve a specific financial statement entry (e.g., net income, total assets)
        for a company and a period by entry type.

        Args:
            company_id (str): The unique identifier of the company.
            period_id (str): The identifier of the financial period.
            entry_type (str): The financial statement entry type to retrieve.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": FinancialStatementEntryInfo }
                - If not found:
                    { "success": False, "error": "No such financial statement entry for the given company, period, and entry_type" }

        Constraints:
            - The returned entry must match all of: company_id, period_id, and entry_type.
        """
        for entry in self.financial_statement_entries.values():
            if (
                entry.get("company_id") == company_id and
                entry.get("period_id") == period_id and
                entry.get("entry_type") == entry_type
            ):
                return { "success": True, "data": entry }
        return {
            "success": False,
            "error": "No such financial statement entry for the given company, period, and entry_type"
        }

    def check_metric_exists(self, company_id: str, period_id: str, metric_name: str) -> dict:
        """
        Check if a particular financial metric (by name) exists for a company and period.

        Args:
            company_id (str): The company's unique identifier.
            period_id (str): The financial period's unique identifier.
            metric_name (str): The name of the financial metric.

        Returns:
            dict: 
                {
                    "success": True,
                    "exists": bool  # True if matching metric exists, else False
                }
                OR
                {
                    "success": False,
                    "error": str    # Reason for error (company/period not found)
                }

        Constraints:
            - The given company_id and period_id must exist in the database.
        """
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist"}
        if period_id not in self.financial_periods:
            return {"success": False, "error": "Financial period does not exist"}

        for metric in self.financial_metrics.values():
            if (
                metric["company_id"] == company_id and
                metric["period_id"] == period_id and
                metric["metric_name"] == metric_name
            ):
                return {"success": True, "exists": True}

        return {"success": True, "exists": False}

    def add_or_update_financial_metric(
        self,
        company_id: str,
        period_id: str,
        metric_name: str,
        metric_val: float
    ) -> dict:
        """
        Add a new or update an existing financial metric for the specified company and period.

        Args:
            company_id (str): The company's unique ID.
            period_id (str): The financial period's unique ID.
            metric_name (str): Name of the financial metric (e.g., ROA).
            metric_val (float): Value to set for the metric.

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
            - company_id must refer to an existing company
            - period_id must refer to an existing period, and that period must belong to company_id.
            - Only one metric per (company_id, period_id, metric_name); update if exists, otherwise add as new.
        """

        # Validate company existence
        if company_id not in self.companies:
            return { "success": False, "error": f"Company ID '{company_id}' does not exist." }

        # Validate period existence
        if period_id not in self.financial_periods:
            return { "success": False, "error": f"Financial period ID '{period_id}' does not exist." }

        period_info = self.financial_periods[period_id]
        # Check if the period actually belongs to the company
        if period_info.get("company_id") != company_id:
            return { "success": False, "error": "Financial period does not belong to specified company." }

        # Search for existing metric
        existing_metric_id = None
        for metric_id, metric_info in self.financial_metrics.items():
            if (
                metric_info.get("company_id") == company_id and
                metric_info.get("period_id") == period_id and
                metric_info.get("metric_name") == metric_name
            ):
                existing_metric_id = metric_id
                break

        if existing_metric_id:
            # Update
            self.financial_metrics[existing_metric_id]["metric_val"] = metric_val
            message = (
                f"Updated financial metric '{metric_name}' for company '{company_id}' "
                f"period '{period_id}'."
            )
            return { "success": True, "message": message }
        else:
            # Add new metric
            new_metric_id = str(uuid.uuid4())
            new_metric: FinancialMetricInfo = {
                "metric_id": new_metric_id,
                "company_id": company_id,
                "period_id": period_id,
                "metric_name": metric_name,
                "metric_val": metric_val
            }
            self.financial_metrics[new_metric_id] = new_metric
            message = (
                f"Added financial metric '{metric_name}' for company '{company_id}' "
                f"period '{period_id}'."
            )
            return { "success": True, "message": message }

    def remove_financial_metric(self, company_id: str, period_id: str, metric_name: str) -> dict:
        """
        Remove a financial metric for a given company and period, identified by metric_name.

        Args:
            company_id (str): The company identifier.
            period_id (str): The financial period identifier.
            metric_name (str): The metric name to remove (e.g., "ROA", "ROE").

        Returns:
            dict: {
              "success": True,
              "message": str  # Confirmation with details
            }
            or
            {
              "success": False,
              "error": str    # Error message
            }

        Constraints:
            - The specified company_id and period_id must exist.
            - The metric to remove must exactly match company_id, period_id, and metric_name.
        """

        if company_id not in self.companies:
            return { "success": False, "error": "Invalid company_id." }
        if period_id not in self.financial_periods:
            return { "success": False, "error": "Invalid period_id." }

        found_metric_id = None
        for metric_id, metric in self.financial_metrics.items():
            if (metric["company_id"] == company_id and
                metric["period_id"] == period_id and
                metric["metric_name"] == metric_name):
                found_metric_id = metric_id
                break

        if not found_metric_id:
            return { "success": False, "error": "Metric not found." }

        del self.financial_metrics[found_metric_id]

        return {
            "success": True,
            "message": f"Financial metric '{metric_name}' removed for company '{company_id}' in period '{period_id}'."
        }

    def add_financial_statement_entry(
        self,
        entry_id: str,
        company_id: str,
        period_id: str,
        entry_type: str,
        val: float
    ) -> dict:
        """
        Insert a new financial statement entry for a company and period.

        Args:
            entry_id (str): Unique identifier for the statement entry.
            company_id (str): The associated company's unique ID.
            period_id (str): The financial period's unique ID.
            entry_type (str): The type/category of the financial statement entry (e.g., 'net_income').
            val (float): The value of the entry.

        Returns:
            dict: {
                'success': True,
                'message': 'Financial statement entry added.'
            }
            or
            {
                'success': False,
                'error': str
            }

        Constraints:
            - entry_id must be unique.
            - company_id and period_id must refer to existing records.
            - period_id must belong to the given company_id.
        """
        # Ensure entry_id is unique
        if entry_id in self.financial_statement_entries:
            return {"success": False, "error": "Entry ID already exists."}

        # Verify company exists
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist."}

        # Verify financial period exists and is for this company
        period_info = self.financial_periods.get(period_id)
        if not period_info:
            return {"success": False, "error": "Financial period does not exist."}
        if period_info["company_id"] != company_id:
            return {"success": False, "error": "Financial period does not belong to specified company."}

        # Logical duplicate entry check for (company_id, period_id, entry_type)
        for existing in self.financial_statement_entries.values():
            if (
                existing["company_id"] == company_id and
                existing["period_id"] == period_id and
                existing["entry_type"] == entry_type
            ):
                return {"success": False, "error": "Duplicate statement entry type for this company and period."}

        # Insert new entry
        self.financial_statement_entries[entry_id] = {
            "entry_id": entry_id,
            "company_id": company_id,
            "period_id": period_id,
            "entry_type": entry_type,
            "val": val
        }
        return {"success": True, "message": "Financial statement entry added."}

    def update_financial_statement_entry(
        self,
        company_id: str,
        period_id: str,
        entry_type: str,
        new_val: float
    ) -> dict:
        """
        Update the value of an existing financial statement entry for a company and period.

        Args:
            company_id (str): The company's unique identifier.
            period_id (str): The period's unique identifier.
            entry_type (str): The type of statement entry (e.g., 'net_income').
            new_val (float): The new value to set for the entry.

        Returns:
            dict: {
                "success": True,
                "message": "Financial statement entry updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - The referenced company_id and period_id must be valid (exist in their respective tables).
            - The entry must exist; only updating existing entries is allowed.
        """
        # Verify company and period exist (defensive, constraints state these must be valid)
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist."}
        if period_id not in self.financial_periods:
            return {"success": False, "error": "Financial period does not exist."}

        # Find the entry
        for entry in self.financial_statement_entries.values():
            if (entry['company_id'] == company_id and
                entry['period_id'] == period_id and
                entry['entry_type'] == entry_type):
                entry['val'] = new_val
                return {
                    "success": True,
                    "message": "Financial statement entry updated successfully."
                }

        return {
            "success": False,
            "error": "Financial statement entry not found for the specified company, period, and entry type."
        }


class CorporateFinancialAnalysisDatabase(BaseEnv):
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

    def list_company_periods(self, **kwargs):
        return self._call_inner_tool('list_company_periods', kwargs)

    def get_latest_period_for_company(self, **kwargs):
        return self._call_inner_tool('get_latest_period_for_company', kwargs)

    def list_metrics_for_company_period(self, **kwargs):
        return self._call_inner_tool('list_metrics_for_company_period', kwargs)

    def get_metric_by_name(self, **kwargs):
        return self._call_inner_tool('get_metric_by_name', kwargs)

    def list_statement_entries_for_company_period(self, **kwargs):
        return self._call_inner_tool('list_statement_entries_for_company_period', kwargs)

    def get_statement_entry_by_type(self, **kwargs):
        return self._call_inner_tool('get_statement_entry_by_type', kwargs)

    def check_metric_exists(self, **kwargs):
        return self._call_inner_tool('check_metric_exists', kwargs)

    def add_or_update_financial_metric(self, **kwargs):
        return self._call_inner_tool('add_or_update_financial_metric', kwargs)

    def remove_financial_metric(self, **kwargs):
        return self._call_inner_tool('remove_financial_metric', kwargs)

    def add_financial_statement_entry(self, **kwargs):
        return self._call_inner_tool('add_financial_statement_entry', kwargs)

    def update_financial_statement_entry(self, **kwargs):
        return self._call_inner_tool('update_financial_statement_entry', kwargs)

