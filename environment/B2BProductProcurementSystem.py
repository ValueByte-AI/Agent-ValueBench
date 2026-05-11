# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from uuid import uuid4



# Represents an item that can be purchased through the platform.
class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str
    description: str
    unit_price: float
    sku: str  # corrected from 'sk'

# Tracks the real-time stock available for each product, possibly across warehouses.
class InventoryInfo(TypedDict):
    product_id: str
    available_quantity: int
    location: str

# Represents a B2B (business) customer.
class CompanyInfo(TypedDict):
    company_id: str
    company_name: str
    account_status: str
    contact_info: str

# Represents a product and terms within a specific quotation.
class QuotedItemInfo(TypedDict):
    quotation_id: str
    product_id: str
    quantity: int
    unit_price: float
    line_total: float

# Stores generated quotations for companies.
class QuotationInfo(TypedDict):
    quotation_id: str
    company_id: str
    date_issued: str
    quoted_items: List[QuotedItemInfo]
    status: str
    valid_until: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        B2B Product Procurement System environment state.
        """
        # Products catalog: {product_id: ProductInfo}
        self.products: Dict[str, ProductInfo] = {}

        # Product inventories: {product_id: InventoryInfo}
        self.inventories: Dict[str, InventoryInfo] = {}

        # Companies: {company_id: CompanyInfo}
        self.companies: Dict[str, CompanyInfo] = {}

        # Quotations: {quotation_id: QuotationInfo}
        self.quotations: Dict[str, QuotationInfo] = {}

        # Constraints:
        # - Only products with available_quantity > 0 are included in availability lists and quotations.
        # - Quotation unit_price may differ from Product unit_price (B2B/negotiated terms).
        # - Quotations are specific to the requesting company and have a defined validity period.
        # - Each quotation must reference valid, existing products and company records.

    def get_company_by_name(self, company_name: str) -> dict:
        """
        Retrieve company details using company name.

        Args:
            company_name (str): The name of the company to search for.

        Returns:
            dict: {
                "success": True,
                "data": CompanyInfo  # Matching company's details
            }
            or
            {
                "success": False,
                "error": str  # Error message if no company is found
            }

        Constraints:
            - If multiple companies share the same name, returns the first match.
            - Company search is case-sensitive.
        """
        for company in self.companies.values():
            if company["company_name"] == company_name:
                return {"success": True, "data": company}

        return {"success": False, "error": "No company found with the specified name"}

    def list_available_products(self) -> dict:
        """
        Retrieve all products for which the associated inventory available_quantity > 0.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # Product info dicts (empty if none available)
            }

        Constraints:
            - Product must have an entry in inventory with available_quantity > 0.
        """
        result = []
        for product_id, inventory in self.inventories.items():
            if inventory.get("available_quantity", 0) > 0:
                # Only include product if it exists in the products catalog
                product_info = self.products.get(product_id)
                if product_info:
                    result.append(product_info)
        return {"success": True, "data": result}

    def get_product_details(self, product_id: str) -> dict:
        """
        Retrieve all attributes of a product given its product_id.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict: 
                If found: {
                    "success": True,
                    "data": ProductInfo
                }
                If not found: {
                    "success": False,
                    "error": "Product not found"
                }
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def get_inventory_by_product(self, product_id: str) -> dict:
        """
        Retrieve inventory information (including available_quantity and location) for a given product.

        Args:
            product_id (str): The product's unique identifier.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": InventoryInfo  # includes product_id, available_quantity, location
                  }
                - On failure: {
                      "success": False,
                      "error": "No inventory info for product_id"
                  }

        Constraints:
            - product_id must exist in inventories.
        """
        inventory = self.inventories.get(product_id)
        if inventory is None:
            return { "success": False, "error": "No inventory info for product_id" }

        return { "success": True, "data": inventory }

    def list_company_quotations(self, company_id: str) -> dict:
        """
        Retrieve all quotations previously generated for a particular company.

        Args:
            company_id (str): The company's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[QuotationInfo]  # List of QuotationInfo dicts for the company
            }
            or
            {
                "success": False,
                "error": str  # If the company does not exist in the records
            }

        Constraints:
            - The company_id must exist in the system.
            - If no quotations are found for this company, returns an empty list with success.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist" }

        matching_quotations = [
            quotation
            for quotation in self.quotations.values()
            if quotation["company_id"] == company_id
        ]

        return { "success": True, "data": matching_quotations }

    def get_quotation_details(self, quotation_id: str) -> dict:
        """
        Retrieve complete details for a specific quotation by its ID.

        Args:
            quotation_id (str): The identifier of the quotation to look up.

        Returns:
            dict: {
                "success": True,
                "data": QuotationInfo,  # All fields, including quoted_items[]
            }
            or
            {
                "success": False,
                "error": str  # Reason why details could not be retrieved
            }

        Constraints:
            - The quotation must exist (quotation_id in self.quotations).
        """
        if quotation_id not in self.quotations:
            return {"success": False, "error": "Quotation with provided ID does not exist."}
    
        return {
            "success": True,
            "data": self.quotations[quotation_id]
        }

    def check_company_account_status(self, company_id: str) -> dict:
        """
        Query and return the current account status for a given company.

        Args:
            company_id (str): The unique identifier of the company.

        Returns:
            dict: 
                If found: {"success": True, "data": {"company_id": str, "account_status": str}}
                If not found: {"success": False, "error": "Company not found"}
        Constraints:
            - The company_id must refer to an existing company.
        """
        company = self.companies.get(company_id)
        if not company:
            return {"success": False, "error": "Company not found"}
        return {
            "success": True,
            "data": {
                "company_id": company_id,
                "account_status": company["account_status"]
            }
        }

    def generate_quotation(
        self,
        company_id: str,
        items: list,
        date_issued: str,
        valid_until: str,
    ) -> dict:
        """
        Create a new quotation for one or more products for a specific company.

        Args:
            company_id (str): ID of the company requesting the quotation.
            items (list): List of dicts, each with keys:
                - product_id (str)
                - quantity (int)
                - unit_price (float)
            date_issued (str): Date when the quotation is issued.
            valid_until (str): Validity period end date (as str).

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": "Quotation generated",
                    "quotation_id": str,
                    "quotation": QuotationInfo
                }
                On failure,
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Company must exist.
            - Each product must exist and have available_quantity > 0 in inventory.
            - Each quantity must be >0 and <= available_quantity.
            - Unit price must be non-negative.
            - Quotation must fully reference existing products and company.
        """
        # Check company exists
        if company_id not in self.companies:
            return {"success": False, "error": f"Company {company_id} does not exist"}
        if not isinstance(items, list) or len(items) == 0:
            return {"success": False, "error": "Quotation must contain at least one quoted item"}

        quoted_items = []
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            unit_price = item.get("unit_price")

            # Check product exists
            if product_id not in self.products:
                return {"success": False, "error": f"Product {product_id} does not exist"}

            # Check inventory exists and is available
            inventory = self.inventories.get(product_id)
            if (
                inventory is None
                or inventory["available_quantity"] <= 0
            ):
                return {
                    "success": False,
                    "error": f"Product {product_id} is not available in inventory"
                }

            # Check quantity
            if not isinstance(quantity, int) or quantity <= 0:
                return {
                    "success": False,
                    "error": f"Invalid quantity for product {product_id}"
                }
            if quantity > inventory["available_quantity"]:
                return {
                    "success": False,
                    "error": f"Requested quantity ({quantity}) for product {product_id} exceeds available stock ({inventory['available_quantity']})"
                }

            # Check unit price
            if not isinstance(unit_price, (int, float)) or unit_price < 0:
                return {
                    "success": False,
                    "error": f"Invalid unit price for product {product_id}"
                }

            # Prepare quoted item (line)
            line_total = quantity * unit_price
            # We'll generate the quotation_id below, temporarily leave as ''
            quoted_items.append({
                "quotation_id": "",  # To be set later
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        # Generate unique quotation_id
        quotation_id = str(uuid4())

        # Assign correct quotation_id to each quoted item
        for qi in quoted_items:
            qi["quotation_id"] = quotation_id

        # Create quotation info
        quotation_info = {
            "quotation_id": quotation_id,
            "company_id": company_id,
            "date_issued": date_issued,
            "quoted_items": quoted_items,
            "status": "pending",  # default status
            "valid_until": valid_until,
        }

        self.quotations[quotation_id] = quotation_info

        return {
            "success": True,
            "message": "Quotation generated",
            "quotation_id": quotation_id,
            "quotation": quotation_info,
        }

    def add_quoted_item_to_quotation(
        self, 
        quotation_id: str, 
        product_id: str, 
        quantity: int, 
        unit_price: float
    ) -> dict:
        """
        Add a new quoted item (product and terms) to an existing quotation.

        Args:
            quotation_id (str): The ID of the quotation to be updated.
            product_id (str): The ID of the product to add as a quoted item.
            quantity (int): Number of units to quote.
            unit_price (float): Price per unit for this quote line.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Quoted item added to quotation." }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Quotation must exist.
            - Product must exist.
            - Product inventory must exist with available_quantity > 0.
            - Quantity must be positive and should not exceed available_quantity.
            - Quotation must reference valid products.
            - Quotation and product values cannot be negative or zero as appropriate.
        """
        # Check quotation exists
        if quotation_id not in self.quotations:
            return { "success": False, "error": "Quotation does not exist." }
        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }
        # Check inventory exists for product
        if product_id not in self.inventories:
            return { "success": False, "error": "Inventory data not found for product." }
        inventory = self.inventories[product_id]
        available_quantity = inventory.get("available_quantity", 0)
        # Only allow quoting products that are in stock
        if available_quantity <= 0:
            return { "success": False, "error": "Product has no available stock for quoting." }
        # Quantity check
        if not isinstance(quantity, int) or quantity <= 0:
            return { "success": False, "error": "Quoted quantity must be a positive integer." }
        if quantity > available_quantity:
            return { "success": False, "error": f"Requested quantity ({quantity}) exceeds available stock ({available_quantity})." }
        # Unit price check
        if not isinstance(unit_price, (float, int)) or unit_price < 0:
            return { "success": False, "error": "Unit price must be a non-negative number." }

        # Prepare quoted item
        line_total = round(quantity * unit_price, 2)
        quoted_item = {
            "quotation_id": quotation_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": float(unit_price),
            "line_total": line_total
        }
        # Append to quotation's quoted_items
        quotation = self.quotations[quotation_id]
        if "quoted_items" not in quotation or quotation["quoted_items"] is None:
            quotation["quoted_items"] = []
        quotation["quoted_items"].append(quoted_item)
        # Persist change
        self.quotations[quotation_id] = quotation

        return { "success": True, "message": "Quoted item added to quotation." }

    def set_quotation_validity(self, quotation_id: str, valid_until: str) -> dict:
        """
        Update or set the 'valid_until' field for a specific quotation.

        Args:
            quotation_id (str): The identifier for the quotation to update.
            valid_until (str): The new validity date/time (ISO or other string format).

        Returns:
            dict: {
                "success": True,
                "message": "Quotation validity updated"
            } 
            or
            {
                "success": False,
                "error": "Quotation not found"
            }
        
        Constraints:
            - The quotation with given quotation_id must exist in self.quotations.
            - No checks/validation on the valid_until format (assumed as string by spec).
        """
        if quotation_id not in self.quotations:
            return { "success": False, "error": "Quotation not found" }
    
        self.quotations[quotation_id]["valid_until"] = valid_until
        return { "success": True, "message": "Quotation validity updated" }

    def update_quotation_status(self, quotation_id: str, new_status: str) -> dict:
        """
        Change the status of a specific quotation.

        Args:
            quotation_id (str): The ID of the quotation whose status should be updated.
            new_status (str): New status value (e.g., 'issued', 'expired').

        Returns:
            dict: {
                "success": True,
                "message": "Status for quotation <quotation_id> updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": "Quotation does not exist"
            }

        Constraints:
            - Quotation must exist.
            - No restriction on status values specified by environment.
        """
        if quotation_id not in self.quotations:
            return {"success": False, "error": "Quotation does not exist"}

        self.quotations[quotation_id]['status'] = new_status
        return {
            "success": True,
            "message": f"Status for quotation {quotation_id} updated to {new_status}"
        }

    def modify_quoted_item(
        self,
        quotation_id: str,
        product_id: str,
        quantity: int = None,
        unit_price: float = None,
        line_total: float = None
    ) -> dict:
        """
        Change the quantity, unit_price, or line_total of an item within a quotation.

        Args:
            quotation_id (str): The ID of the quotation containing the item.
            product_id (str): The product ID of the quoted item to be modified.
            quantity (int, optional): New quantity. Must be >= 1 and <= available stock.
            unit_price (float, optional): New unit price. Must be >= 0.
            line_total (float, optional): New line total. If not provided, recalculated as quantity * unit_price.

        Returns:
            dict: {
                "success": True,
                "message": "Quoted item modified successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Quotation and cited product must exist.
            - The quoted item must be present in the quotation.
            - Only positive quantity (>=1) permitted and must not exceed available stock.
            - Unit price must be non-negative.
            - Quotation and references must remain valid.
        """
        # Check quotation exists
        if quotation_id not in self.quotations:
            return {"success": False, "error": "Quotation does not exist."}
        quotation = self.quotations[quotation_id]
        # Find quoted item
        quoted_items = quotation["quoted_items"]
        quoted_item = None
        for item in quoted_items:
            if item["product_id"] == product_id:
                quoted_item = item
                break
        if quoted_item is None:
            return {"success": False, "error": "Quoted item for product not found in quotation."}
        # Validate product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist."}
        # Validate inventory exists and get current stock
        if product_id not in self.inventories:
            return {"success": False, "error": "No inventory record for this product."}
        available_quantity = self.inventories[product_id]["available_quantity"]
        if quantity is None and unit_price is None and line_total is None:
            return {"success": False, "error": "At least one quoted item field must be updated."}

        # Update logic
        new_quantity = quoted_item["quantity"]
        new_unit_price = quoted_item["unit_price"]

        # Quantity
        if quantity is not None:
            if quantity < 1:
                return {"success": False, "error": "Quantity must be at least 1."}
            if quantity > available_quantity:
                return {"success": False, "error": "Quantity exceeds available stock."}
            new_quantity = quantity

        # Unit price
        if unit_price is not None:
            if unit_price < 0:
                return {"success": False, "error": "Unit price cannot be negative."}
            new_unit_price = unit_price

        # Line total
        if line_total is not None:
            if line_total < 0:
                return {"success": False, "error": "Line total cannot be negative."}
            new_line_total = line_total
        else:
            # Recalculate from possibly-updated values
            new_line_total = new_quantity * new_unit_price

        # Update the quoted item
        quoted_item["quantity"] = new_quantity
        quoted_item["unit_price"] = new_unit_price
        quoted_item["line_total"] = new_line_total

        return {"success": True, "message": "Quoted item modified successfully."}

    def remove_quoted_item(self, quotation_id: str, product_id: str) -> dict:
        """
        Remove an item (product line) identified by product_id from a quotation.

        Args:
            quotation_id (str): The ID of the quotation to be modified.
            product_id (str): The product ID to be removed from the quotation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Removed product <product_id> from quotation <quotation_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
          - Quotation must exist.
          - Quoted item (specified by product_id) must exist in the quotation.
          - After removal, the quotation still only references valid products (enforced by original construction, not an issue here).
        """
        # Check if quotation exists
        if quotation_id not in self.quotations:
            return {"success": False, "error": f"Quotation {quotation_id} does not exist."}
    
        quotation = self.quotations[quotation_id]

        # Defensive: quoted_items must be a list
        quoted_items = quotation.get('quoted_items', None)
        if not isinstance(quoted_items, list):
            return {"success": False, "error": "Malformed quotation data (quoted_items not a list)."}

        # Find item index to remove
        idx_to_remove = None
        for idx, item in enumerate(quoted_items):
            if item.get("product_id") == product_id:
                idx_to_remove = idx
                break
    
        if idx_to_remove is None:
            return {"success": False, "error": f"Quoted item with product_id {product_id} not found in quotation {quotation_id}."}

        # Remove the item
        del quoted_items[idx_to_remove]
        quotation['quoted_items'] = quoted_items  # assign back, in case

        # Update (not strictly necessary, as dict is a reference, but for clarity)
        self.quotations[quotation_id] = quotation

        return {"success": True,
                "message": f"Removed product {product_id} from quotation {quotation_id}."}


class B2BProductProcurementSystem(BaseEnv):
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
            if key == "inventories" and isinstance(value, dict):
                normalized_inventories = {}
                for inventory_key, inventory_info in value.items():
                    if isinstance(inventory_info, dict):
                        product_id = inventory_info.get("product_id")
                        normalized_key = (
                            product_id
                            if isinstance(product_id, str) and product_id
                            else inventory_key
                        )
                    else:
                        normalized_key = inventory_key
                    normalized_inventories[normalized_key] = copy.deepcopy(inventory_info)
                setattr(env, key, normalized_inventories)
                continue
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

    def get_company_by_name(self, **kwargs):
        return self._call_inner_tool('get_company_by_name', kwargs)

    def list_available_products(self, **kwargs):
        return self._call_inner_tool('list_available_products', kwargs)

    def get_product_details(self, **kwargs):
        return self._call_inner_tool('get_product_details', kwargs)

    def get_inventory_by_product(self, **kwargs):
        return self._call_inner_tool('get_inventory_by_product', kwargs)

    def list_company_quotations(self, **kwargs):
        return self._call_inner_tool('list_company_quotations', kwargs)

    def get_quotation_details(self, **kwargs):
        return self._call_inner_tool('get_quotation_details', kwargs)

    def check_company_account_status(self, **kwargs):
        return self._call_inner_tool('check_company_account_status', kwargs)

    def generate_quotation(self, **kwargs):
        return self._call_inner_tool('generate_quotation', kwargs)

    def add_quoted_item_to_quotation(self, **kwargs):
        return self._call_inner_tool('add_quoted_item_to_quotation', kwargs)

    def set_quotation_validity(self, **kwargs):
        return self._call_inner_tool('set_quotation_validity', kwargs)

    def update_quotation_status(self, **kwargs):
        return self._call_inner_tool('update_quotation_status', kwargs)

    def modify_quoted_item(self, **kwargs):
        return self._call_inner_tool('modify_quoted_item', kwargs)

    def remove_quoted_item(self, **kwargs):
        return self._call_inner_tool('remove_quoted_item', kwargs)
