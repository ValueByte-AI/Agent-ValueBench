# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class ProductLaunchInfo(TypedDict):
    product_id: str
    name: str
    description: str
    product_type: str
    price: float
    target_market: str
    launch_date: str
    launch_stage: str
    status: str

class MarketEvaluationReportInfo(TypedDict):
    report_id: str
    product_id: str
    demand_level: str
    evaluation_date: str
    report_data: str

class _GeneratedEnvImpl:
    def __init__(self):
        # ProductLaunches: {product_id: ProductLaunchInfo}
        # Represents a launch plan for a product
        self.product_launches: Dict[str, ProductLaunchInfo] = {}
        # MarketEvaluationReports: {report_id: MarketEvaluationReportInfo}
        # Captures analytics and reports about each launch
        self.evaluation_reports: Dict[str, MarketEvaluationReportInfo] = {}

        # --- Constraints ---
        # - Each ProductLaunch must have a unique product_id.
        # - ProductLaunch entries can be created, read, updated, or deleted.
        # - ProductLaunch price must be non-negative.
        # - Only products with sufficient market demand (per MarketEvaluationReport)
        #   should proceed to final launch stages.
        # - Deleting a ProductLaunch may require verifying that it has not yet been launched
        #   or has dependencies (e.g., linked reports).

    def get_product_launch_by_id(self, product_id: str) -> dict:
        """
        Retrieve all details of a specific ProductLaunch given its product_id.

        Args:
            product_id (str): The unique identifier for the product launch.

        Returns:
            dict: {
                "success": True,
                "data": ProductLaunchInfo  # All attributes of the product launch
            }
            or
            {
                "success": False,
                "error": str  # Reason why retrieval failed, e.g. not found
            }

        Constraints:
            - The product_id must exist in the system.
        """
        product_launch = self.product_launches.get(product_id)
        if product_launch is None:
            return { "success": False, "error": "ProductLaunch not found" }

        return { "success": True, "data": product_launch }

    def list_product_launches(self) -> dict:
        """
        List all ProductLaunch entries in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductLaunchInfo],  # list of all product launch info (may be empty if none)
            }
        """
        result = list(self.product_launches.values())
        return { "success": True, "data": result }

    def get_product_launch_by_name(self, name: str) -> dict:
        """
        Retrieve a ProductLaunch entry by its product name.

        Args:
            name (str): The name of the product to search for.

        Returns:
            dict:
                On success:
                  {
                    "success": True,
                    "data": ProductLaunchInfo  # the info for the matching product
                  }
                On failure (not found):
                  {
                    "success": False,
                    "error": "ProductLaunch with the given name does not exist"
                  }

        Constraints:
            - Names are matched exactly (case-sensitive).
        """
        for launch_info in self.product_launches.values():
            if launch_info["name"] == name:
                return { "success": True, "data": launch_info }
        return { "success": False, "error": "ProductLaunch with the given name does not exist" }

    def list_product_launches_by_status(self, status: str) -> dict:
        """
        List all ProductLaunch entries filtered by their status 
        (e.g., active, cancelled, deleted).

        Args:
            status (str): The status value to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductLaunchInfo],
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - No restrictions, except status must be a non-empty string.
        """
        if not isinstance(status, str) or not status.strip():
            return {"success": False, "error": "Invalid status parameter"}

        result = [
            pli for pli in self.product_launches.values()
            if pli.get("status") == status
        ]
        return {"success": True, "data": result}

    def get_market_evaluation_reports_for_product(self, product_id: str) -> dict:
        """
        Retrieve all MarketEvaluationReports linked to a specific product_id.

        Args:
            product_id (str): The product's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[MarketEvaluationReportInfo],  # List of matched reports (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # e.g., "ProductLaunch not found for the given product_id"
            }

        Constraints:
            - The given product_id must exist in product_launches.
        """
        if product_id not in self.product_launches:
            return {"success": False, "error": "ProductLaunch not found for the given product_id"}

        reports = [
            report for report in self.evaluation_reports.values()
            if report["product_id"] == product_id
        ]
        return {"success": True, "data": reports}

    def get_latest_market_evaluation_report(self, product_id: str) -> dict:
        """
        Retrieve the most recent MarketEvaluationReport for the specified product.

        Args:
            product_id (str): The id of the product for which to retrieve the latest report.

        Returns:
            dict: {
                "success": True,
                "data": MarketEvaluationReportInfo  # The most recent report
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. no reports for product
            }

        Constraints:
            - The product must have at least one MarketEvaluationReport.
        """
        # Filter all reports for this product_id
        reports = [
            report for report in self.evaluation_reports.values()
            if report["product_id"] == product_id
        ]
        if not reports:
            return { "success": False, "error": "No evaluation reports found for product" }

        # Find the report with the latest evaluation_date
        # Assume ISO8601 string comparison is valid (lex order)
        latest_report = max(reports, key=lambda r: r["evaluation_date"])

        return { "success": True, "data": latest_report }

    def get_market_demand_level(self, product_id: str) -> dict:
        """
        Get the market demand_level from the latest MarketEvaluationReport for the given product.

        Args:
            product_id (str): The ID of the product whose demand level is to be queried.

        Returns:
            dict: 
              - On success: { "success": True, "data": <demand_level (str)> }
              - On failure: { "success": False, "error": <reason> }

        Notes:
            - If there are multiple reports for the product, selects the one with the most recent evaluation_date.
            - If there are no reports for the product, returns an appropriate error message.
            - Assumes evaluation_date can be sorted as ISO8601 strings for recency.
        """
        # Filter all reports for the given product_id
        reports = [
            report for report in self.evaluation_reports.values()
            if report["product_id"] == product_id
        ]
        if not reports:
            return { "success": False, "error": "No market evaluation report found for this product" }
    
        # Find latest report by evaluation_date (string compare should suffice if ISO8601)
        latest_report = max(reports, key=lambda r: r["evaluation_date"])
        demand_level = latest_report.get("demand_level")
    
        return { "success": True, "data": demand_level }

    def check_product_launch_deletable(self, product_id: str) -> dict:
        """
        Determine if a ProductLaunch with the given product_id is eligible for deletion.
        Reasons a product launch would NOT be deletable:
          - It is already launched (based on launch_stage: e.g. 'launched', 'completed', etc.)
          - There are linked MarketEvaluationReports (i.e., reports referencing this product_id)
    
        Args:
            product_id (str): The ID of the ProductLaunch to check.
    
        Returns:
            dict: 
                On success (deletable):
                    { "success": True, "data": True }
                On success (not deletable):
                    { "success": True, "data": False, "reason": <reason> }
                On error (not found):
                    { "success": False, "error": "ProductLaunch not found" }
        """
        launch = self.product_launches.get(product_id)
        if not launch:
            return {"success": False, "error": "ProductLaunch not found"}
    
        # Define which stages mean "already launched"
        non_deletable_stages = {"launched", "completed", "final"}
        if launch.get("launch_stage", "").lower() in non_deletable_stages:
            return {
                "success": True,
                "data": False,
                "reason": "Product has already launched and cannot be deleted"
            }

        # Check for presence of any linked MarketEvaluationReports
        for report in self.evaluation_reports.values():
            if report.get("product_id") == product_id:
                return {
                    "success": True,
                    "data": False,
                    "reason": "Product has linked MarketEvaluationReports and cannot be deleted"
                }
    
        # If all checks passed, it's deletable
        return {"success": True, "data": True}

    def check_product_id_unique(self, product_id: str) -> dict:
        """
        Check if the given product_id is unique and unused in the system.

        Args:
            product_id (str): Product ID to be validated for uniqueness.

        Returns:
            dict: {
                "success": True,
                "data": {"unique": bool}
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. missing product_id
            }

        Constraints:
            - product_id must be a non-empty string.
            - Checks only for existence of product_id in self.product_launches.
        """
        if not isinstance(product_id, str) or not product_id.strip():
            return { "success": False, "error": "No product_id provided" }

        unique = product_id not in self.product_launches
        return { "success": True, "data": { "unique": unique } }

    def check_price_valid(self, price: float) -> dict:
        """
        Confirm that a price is non-negative.

        Args:
            price (float): The price to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if valid (>=0), False if negative
            }
            - If price is not a number, success is False with error message.

        Constraints:
            - Price must be >= 0.
        """
        # Basic type validation
        if not isinstance(price, (int, float)):
            return { "success": False, "error": "Price must be a numeric value." }
        # Non-negative check
        is_valid = price >= 0
        return { "success": True, "data": is_valid }

    def check_market_demand_sufficient(self, product_id: str) -> dict:
        """
        Determine if the given product's market demand (latest MarketEvaluationReport) is sufficient to
        proceed to next launch stages.

        Args:
            product_id (str): The product's unique identifier.

        Returns:
            dict: {
                "success": True,
                "sufficient": bool,     # Whether market demand is sufficient
                "demand_level": str,    # The demand level from the latest report
                "criteria": str,        # Textual description of sufficiency criteria
                "latest_report_id": str # Which report this is based on
            }
            or
            {
                "success": False,
                "error": str            # Description of the error (e.g., product not found or no report)
            }

        Constraints:
            - Must match existing product_id.
            - Market demand is deemed sufficient if demand_level is 'HIGH' or 'SUFFICIENT' (by default).
            - Uses latest (by evaluation_date) MarketEvaluationReport for that product.
        """
        # Check for valid product
        if product_id not in self.product_launches:
            return {"success": False, "error": "ProductLaunch with this ID does not exist"}

        # Collect all reports for product
        reports = [
            report for report in self.evaluation_reports.values()
            if report.get("product_id") == product_id
        ]
        if not reports:
            return {"success": False, "error": "No MarketEvaluationReport found for this product"}

        # Select latest report (assuming ISO date string)
        latest_report = max(reports, key=lambda r: r["evaluation_date"])
        demand_level = latest_report.get("demand_level", "").upper()

        # Setting criteria
        sufficient_levels = {"HIGH", "SUFFICIENT"}
        criteria = "Demand is sufficient if demand_level is 'HIGH' or 'SUFFICIENT'."

        is_sufficient = demand_level in sufficient_levels

        return {
            "success": True,
            "sufficient": is_sufficient,
            "demand_level": latest_report.get("demand_level", ""),
            "criteria": criteria,
            "latest_report_id": latest_report.get("report_id")
        }

    def create_product_launch(
        self,
        product_id: str,
        name: str,
        description: str,
        product_type: str,
        price: float,
        target_market: str,
        launch_date: str,
        launch_stage: str,
        status: str
    ) -> dict:
        """
        Create a new ProductLaunch entry.

        Args:
            product_id (str): Unique identifier for the product launch.
            name (str): Product name.
            description (str): Product description.
            product_type (str): Product type/category.
            price (float): Product price (must be non-negative).
            target_market (str): Target market for launch.
            launch_date (str): Scheduled launch date (string format).
            launch_stage (str): Current stage of launch.
            status (str): Status (e.g., active, cancelled, deleted).

        Returns:
            dict:
                {"success": True, "message": "ProductLaunch entry created successfully."}
                or
                {"success": False, "error": "<reason>"}

        Constraints:
            - product_id must be unique.
            - price must be non-negative.
        """
        # Check if product_id is unique
        if product_id in self.product_launches:
            return {"success": False, "error": "Product ID already exists."}

        # Validate price
        try:
            p_val = float(price)
        except (TypeError, ValueError):
            return {"success": False, "error": "Invalid price value."}
        if p_val < 0:
            return {"success": False, "error": "Price must be non-negative."}

        # Build launch info
        info: ProductLaunchInfo = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "product_type": product_type,
            "price": p_val,
            "target_market": target_market,
            "launch_date": launch_date,
            "launch_stage": launch_stage,
            "status": status,
        }
        self.product_launches[product_id] = info
        return {"success": True, "message": "ProductLaunch entry created successfully."}

    def update_product_launch(self, product_id: str, **kwargs) -> dict:
        """
        Update fields of an existing ProductLaunch.

        Args:
            product_id (str): Unique identifier of the ProductLaunch to update.
            kwargs: Field-value pairs for fields to update. Allowed fields: 
                name, description, product_type, price, target_market, launch_date, launch_stage, status

        Returns:
            dict:
                Success: { "success": True, "message": "Updated fields: ..." }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - product_id must exist.
            - price (if provided) must be non-negative.
            - If launch_stage is updated to a 'final' stage, this may require sufficient demand (optional, if business logic specifies).
            - Only listed fields can be updated. Unrecognized fields will be ignored.
        """
        if product_id not in self.product_launches:
            return { "success": False, "error": "ProductLaunch with given product_id does not exist." }

        allowed_fields = {
            "name", "description", "product_type", "price", 
            "target_market", "launch_date", "launch_stage", "status"
        }
        update_fields = {}
        for k, v in kwargs.items():
            if k in allowed_fields:
                update_fields[k] = v

        if not update_fields:
            return { "success": False, "error": "No valid fields to update." }

        # Constraint: price >= 0
        if 'price' in update_fields:
            try:
                p = float(update_fields['price'])
            except (TypeError, ValueError):
                return { "success": False, "error": "Invalid price value." }
            if p < 0:
                return { "success": False, "error": "Price must be non-negative." }

        # Optional: launch_stage constraint
        # (Let's assume 'launched' and 'finalized' are final stages for this example)
        final_stages = {"launched", "finalized"}
        if 'launch_stage' in update_fields and update_fields['launch_stage'].lower() in final_stages:
            # Check if demand is sufficient
            demand_ok = False
            # Find the latest relevant market evaluation report
            product_reports = [
                rpt for rpt in self.evaluation_reports.values()
                if rpt["product_id"] == product_id
            ]
            # "sufficient" is assumed to be 'high' demand (business logic may differ)
            if product_reports:
                latest_report = max(product_reports, key=lambda r: r["evaluation_date"])
                if latest_report.get("demand_level", "").lower() == "high":
                    demand_ok = True
            if not demand_ok:
                return { 
                    "success": False, 
                    "error": "Cannot proceed to final launch stage: insufficient market demand." 
                }

        # Apply updates
        for k, v in update_fields.items():
            self.product_launches[product_id][k] = v

        # Compose message
        updated = ", ".join(update_fields.keys())
        return { "success": True, "message": f"Updated fields: {updated}" }

    def update_product_price(self, product_id: str, new_price: float) -> dict:
        """
        Update the price of a ProductLaunch, enforcing the non-negative price constraint.

        Args:
            product_id (str): The unique ID of the product launch to update.
            new_price (float): The new price to set. Must be non-negative.

        Returns:
            dict: {
              "success": True,
              "message": "Price updated for product_id <id>"
            } on success,
            or {
              "success": False,
              "error": "<reason>"
            } if not found or invalid price.

        Constraints:
            - product_id must exist in the product_launches.
            - new_price must be non-negative.
        """
        if product_id not in self.product_launches:
            return {"success": False, "error": f"ProductLaunch with product_id '{product_id}' not found."}
        if not isinstance(new_price, (int, float)) or new_price < 0:
            return {"success": False, "error": "Price must be a non-negative number."}

        self.product_launches[product_id]["price"] = float(new_price)
        return {"success": True, "message": f"Price updated for product_id {product_id}"}

    def update_product_target_market(self, product_id: str, new_target_market: str) -> dict:
        """
        Change the target_market field for a ProductLaunch.

        Args:
            product_id (str): The ID of the product launch to update.
            new_target_market (str): The new target market description.

        Returns:
            dict:
                If successful:
                    { "success": True, "message": "Product target market updated." }
                If product_id not found:
                    { "success": False, "error": "ProductLaunch with specified product_id does not exist." }

        Constraints:
            - product_id must exist in product_launches.
        """
        if product_id not in self.product_launches:
            return { "success": False, "error": "ProductLaunch with specified product_id does not exist." }

        self.product_launches[product_id]["target_market"] = new_target_market
        return { "success": True, "message": "Product target market updated." }

    def update_product_launch_stage(self, product_id: str, new_launch_stage: str) -> dict:
        """
        Advance or regress the launch_stage field of a ProductLaunch.
        If proceeding into a final launch stage, require market demand sufficiency per latest MarketEvaluationReport.

        Args:
            product_id (str): The id of the product launch to update.
            new_launch_stage (str): The new stage to set for the product launch.

        Returns:
            dict:
                On success: { "success": True, "message": "Launch stage updated to <stage>." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - product_id must exist.
            - If advancing to a final stage (stage contains 'final', 'approved', or 'ready'), must have a MarketEvaluationReport for this product_id with demand_level indicating "sufficiency" (i.e., "sufficient" or "high").
        """
        # Stage names indicating "final" (this could be parameterized or made more robust)
        final_stage_keywords = {"final", "approved", "ready"}

        if product_id not in self.product_launches:
            return { "success": False, "error": "ProductLaunch with this product_id does not exist." }

        # Determine if the new stage is a "final" stage (case-insensitive match)
        is_final_stage = any(kw in new_launch_stage.lower() for kw in final_stage_keywords)

        if is_final_stage:
            # Find all reports for this product, get the latest (by date)
            reports = [
                rpt for rpt in self.evaluation_reports.values()
                if rpt["product_id"] == product_id
            ]
            if not reports:
                return { "success": False, "error": "Cannot advance to final stage: no market evaluation report for this product." }

            # Parse evaluation_date, assume ISO format, latest means max string
            latest_report = max(reports, key=lambda r: r["evaluation_date"])
            demand_level = latest_report.get("demand_level", "").lower()
            if demand_level not in ("sufficient", "high"):
                return { "success": False, "error": "Cannot advance to final stage: market demand is insufficient according to the latest evaluation report." }

        # Update the stage
        self.product_launches[product_id]["launch_stage"] = new_launch_stage

        return {
            "success": True,
            "message": f"Launch stage updated to {new_launch_stage}."
        }

    def delete_product_launch(self, product_id: str) -> dict:
        """
        Delete a ProductLaunch after verifying it is eligible for deletion:
        - ProductLaunch must exist.
        - Product must not be in a final launch stage (e.g., 'launched', 'released').
        - No dependent MarketEvaluationReport entries should reference it.

        Args:
            product_id (str): Unique identifier of the product launch to delete.

        Returns:
            dict: {
                "success": True,
                "message": "ProductLaunch <product_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Each ProductLaunch must have a unique product_id.
            - Product cannot be deleted if already launched ('launched', 'released', etc.).
            - Cannot delete if dependent MarketEvaluationReports exist.
        """

        # 1. Existence check
        if product_id not in self.product_launches:
            return { "success": False, "error": "ProductLaunch not found." }

        deletable_check = self.check_product_launch_deletable(product_id)
        if not deletable_check.get("success", False):
            return {"success": False, "error": deletable_check.get("error", "ProductLaunch not found.")}
        if not deletable_check.get("data", False):
            return {"success": False, "error": deletable_check.get("reason", "ProductLaunch cannot be deleted.")}

        # 4. Perform deletion
        del self.product_launches[product_id]
        # Success
        return { "success": True, "message": f"ProductLaunch {product_id} deleted successfully." }

    def create_market_evaluation_report(
        self, 
        report_id: str,
        product_id: str,
        demand_level: str,
        evaluation_date: str,
        report_data: str
    ) -> dict:
        """
        Create a new MarketEvaluationReport for a product.

        Args:
            report_id (str): Unique identifier for the report.
            product_id (str): Identifier of the product being evaluated (must exist).
            demand_level (str): Demand evaluation (e.g., 'high', 'medium', 'low').
            evaluation_date (str): Date of evaluation (e.g., 'YYYY-MM-DD').
            report_data (str): Additional report details.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "MarketEvaluationReport <report_id> created for product <product_id>"}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - report_id must be unique.
            - product_id must refer to an existing ProductLaunch.
            - All fields required.

        """
        if not all([report_id, product_id, demand_level, evaluation_date, report_data]):
            return {"success": False, "error": "All fields are required."}
    
        if report_id in self.evaluation_reports:
            return {"success": False, "error": f"Report with report_id '{report_id}' already exists."}
    
        if product_id not in self.product_launches:
            return {"success": False, "error": f"ProductLaunch with product_id '{product_id}' does not exist."}
    
        report_info = {
            "report_id": report_id,
            "product_id": product_id,
            "demand_level": demand_level,
            "evaluation_date": evaluation_date,
            "report_data": report_data,
        }
        self.evaluation_reports[report_id] = report_info
        return {"success": True, "message": f"MarketEvaluationReport {report_id} created for product {product_id}"}

    def update_market_evaluation_report(
        self, 
        report_id: str, 
        demand_level: str = None, 
        evaluation_date: str = None, 
        report_data: str = None
    ) -> dict:
        """
        Modify fields within an existing MarketEvaluationReport for a product.

        Args:
            report_id (str): Unique identifier of the MarketEvaluationReport to update.
            demand_level (str, optional): New demand level value.
            evaluation_date (str, optional): New evaluation date.
            report_data (str, optional): New report data content.

        Returns:
            dict:
              - On success: { "success": True, "message": "MarketEvaluationReport updated successfully." }
              - On failure: { "success": False, "error": "<reason>" }

        Constraints:
          - report_id must refer to an existing MarketEvaluationReport.
          - At least one field should be provided to update (otherwise operation is a no-op but will still succeed quietly).
        """
        if report_id not in self.evaluation_reports:
            return {"success": False, "error": "MarketEvaluationReport with given report_id does not exist."}

        report = self.evaluation_reports[report_id]

        # Track whether any actual update is performed (not strictly necessary, but good for feedback)
        updated = False
        if demand_level is not None:
            report["demand_level"] = demand_level
            updated = True
        if evaluation_date is not None:
            report["evaluation_date"] = evaluation_date
            updated = True
        if report_data is not None:
            report["report_data"] = report_data
            updated = True

        # If no updates actually performed, still count as success
        return {"success": True, "message": "MarketEvaluationReport updated successfully."}


class ProductLaunchManagementSystem(BaseEnv):
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

    def get_product_launch_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_launch_by_id', kwargs)

    def list_product_launches(self, **kwargs):
        return self._call_inner_tool('list_product_launches', kwargs)

    def get_product_launch_by_name(self, **kwargs):
        return self._call_inner_tool('get_product_launch_by_name', kwargs)

    def list_product_launches_by_status(self, **kwargs):
        return self._call_inner_tool('list_product_launches_by_status', kwargs)

    def get_market_evaluation_reports_for_product(self, **kwargs):
        return self._call_inner_tool('get_market_evaluation_reports_for_product', kwargs)

    def get_latest_market_evaluation_report(self, **kwargs):
        return self._call_inner_tool('get_latest_market_evaluation_report', kwargs)

    def get_market_demand_level(self, **kwargs):
        return self._call_inner_tool('get_market_demand_level', kwargs)

    def check_product_launch_deletable(self, **kwargs):
        return self._call_inner_tool('check_product_launch_deletable', kwargs)

    def check_product_id_unique(self, **kwargs):
        return self._call_inner_tool('check_product_id_unique', kwargs)

    def check_price_valid(self, **kwargs):
        return self._call_inner_tool('check_price_valid', kwargs)

    def check_market_demand_sufficient(self, **kwargs):
        return self._call_inner_tool('check_market_demand_sufficient', kwargs)

    def create_product_launch(self, **kwargs):
        return self._call_inner_tool('create_product_launch', kwargs)

    def update_product_launch(self, **kwargs):
        return self._call_inner_tool('update_product_launch', kwargs)

    def update_product_price(self, **kwargs):
        return self._call_inner_tool('update_product_price', kwargs)

    def update_product_target_market(self, **kwargs):
        return self._call_inner_tool('update_product_target_market', kwargs)

    def update_product_launch_stage(self, **kwargs):
        return self._call_inner_tool('update_product_launch_stage', kwargs)

    def delete_product_launch(self, **kwargs):
        return self._call_inner_tool('delete_product_launch', kwargs)

    def create_market_evaluation_report(self, **kwargs):
        return self._call_inner_tool('create_market_evaluation_report', kwargs)

    def update_market_evaluation_report(self, **kwargs):
        return self._call_inner_tool('update_market_evaluation_report', kwargs)
