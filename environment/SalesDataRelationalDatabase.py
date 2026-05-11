# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import numbers



# TypedDict for Product
class ProductInfo(TypedDict):
    ProductID: str
    ProductName: str
    Category: str
    Price: float

# TypedDict for Customer
class CustomerInfo(TypedDict):
    CustomerID: str
    CustomerName: str
    ContactInfo: str

# TypedDict for Salesperson
class SalespersonInfo(TypedDict):
    SalespersonID: str
    Name: str

# TypedDict for SalesRecord
class SalesRecordInfo(TypedDict):
    SaleID: str
    ProductID: str
    ProductName: str
    Timestamp: str
    QuantitySold: int
    CustomerID: str
    SaleAmount: float
    SalespersonID: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Mapping ProductID -> ProductInfo
        self.products: Dict[str, ProductInfo] = {}
        # Mapping CustomerID -> CustomerInfo
        self.customers: Dict[str, CustomerInfo] = {}
        # Mapping SalespersonID -> SalespersonInfo
        self.salespersons: Dict[str, SalespersonInfo] = {}
        # Mapping SaleID -> SalesRecordInfo
        self.sales_records: Dict[str, SalesRecordInfo] = {}

        # --- Constraints & Data integrity rules ---
        # - SaleID is unique for each sales record.
        # - Timestamp must be stored in a consistent and queryable format.
        # - ProductID in SalesRecord must reference a valid Product entry (foreign key).
        # - QuantitySold must be a non-negative integer.
        # - Queries may request subsets of columns (to be handled in query logic).
        # - Data integrity is enforced via primary and foreign keys.

    def query_sales_records(
        self, 
        filters: dict = None, 
        columns: list = None
    ) -> dict:
        """
        Retrieve sales records filtered by arbitrary criteria and optionally select a subset of columns.

        Args:
            filters (dict, optional): key-value pairs to filter by. 
                For 'Timestamp', you may supply a range as a tuple ('start', 'end').
            columns (list of str, optional): If given, only the listed columns will be returned per sales record.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # Each dict contains the desired columns for a matching sales record
            }
            or
            {
                "success": False,
                "error": str
            }

        Edge/error cases:
            - Invalid filter fields or invalid column names will result in failure.
            - Returns empty list if no records match.
        """
        base_fields = {
            "SaleID", "ProductID", "ProductName", "Timestamp", 
            "QuantitySold", "CustomerID", "SaleAmount", "SalespersonID"
        }
        valid_fields = set(base_fields)
        for record in self.sales_records.values():
            valid_fields.update(record.keys())

        # Validate columns
        if columns is not None:
            for col in columns:
                if col not in valid_fields:
                    return {"success": False, "error": f"Invalid column name '{col}'."}

        # Validate filters
        applied_filters = filters or {}
        for key, val in applied_filters.items():
            if key not in valid_fields:
                return {"success": False, "error": f"Invalid filter field '{key}'."}
            if key == "Timestamp" and isinstance(val, tuple) and len(val) != 2:
                return {"success": False, "error": "Timestamp range filters must contain exactly two values."}

        # Start with all sales records
        records = list(self.sales_records.values())

        # Apply filters
        filtered = []
        for rec in records:
            matched = True
            for key, val in applied_filters.items():
                if key == "Timestamp":
                    # Range filter
                    if isinstance(val, tuple):
                        start, end = val
                        # Assume ISO string comparison is valid (YYYY-MM-DD ...)
                        if not (start <= rec["Timestamp"] <= end):
                            matched = False
                            break
                    elif isinstance(val, (list, set)):
                        if rec.get(key) not in val:
                            matched = False
                            break
                    else:
                        if rec.get("Timestamp") != val:
                            matched = False
                            break
                else:
                    if isinstance(val, (list, tuple, set)):
                        if rec.get(key) not in val:
                            matched = False
                            break
                    elif rec.get(key) != val:
                        matched = False
                        break
            if matched:
                filtered.append(rec)

        # Select columns
        result = []
        for rec in filtered:
            if columns is None:
                result.append(dict(rec))
            else:
                result.append({col: rec.get(col) for col in columns})

        return {"success": True, "data": result}

    def get_sales_record_by_id(self, sale_id: str) -> dict:
        """
        Retrieve a specific sales record by its unique SaleID.

        Args:
            sale_id (str): The unique SaleID of the sales record to retrieve.

        Returns:
            dict:
                - If found: { "success": True, "data": SalesRecordInfo }
                - If not found: { "success": False, "error": "Sales record not found" }

        Constraints:
            - SaleID must exist in the sales_records table.
        """
        record = self.sales_records.get(sale_id)
        if record is None:
            return {"success": False, "error": "Sales record not found"}
        return {"success": True, "data": record}

    def list_all_products(self) -> dict:
        """
        Retrieve the list of all products and their metadata.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of all products (may be empty if no products exist)
            }
        """
        products_list = list(self.products.values())
        return {
            "success": True,
            "data": products_list
        }

    def get_product_by_id(self, ProductID: str) -> dict:
        """
        Retrieve product details by ProductID.

        Args:
            ProductID (str): The unique identifier of the product.

        Returns:
            dict: 
            - On success: {"success": True, "data": ProductInfo}
            - On failure: {"success": False, "error": "Product not found"}
    
        Constraints:
            - ProductID must reference a valid Product entry.
        """
        if ProductID not in self.products:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "data": self.products[ProductID]}

    def list_all_customers(self) -> dict:
        """
        Retrieve all customers in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[CustomerInfo]  # All customer entries (may be empty if none exist)
            }
        """
        result = list(self.customers.values())
        return {"success": True, "data": result}

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve customer information by CustomerID.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict:
                - success: True and 'data' with CustomerInfo if found,
                - success: False and 'error' if not found.
        Constraints:
            - CustomerID must exist in the database.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": f"CustomerID '{customer_id}' does not exist" }

        customer_info = self.customers[customer_id]
        return { "success": True, "data": customer_info }

    def list_all_salespersons(self) -> dict:
        """
        Retrieve all salespersons (employees) recorded in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SalespersonInfo],  # list of salespersons (may be empty if none)
            }

        Constraints:
            - No constraints for this read operation.
        """
        salespersons_list = list(self.salespersons.values())
        return { "success": True, "data": salespersons_list }

    def get_salesperson_by_id(self, SalespersonID: str) -> dict:
        """
        Retrieve info about a specific salesperson by their SalespersonID.

        Args:
            SalespersonID (str): The unique identifier of the salesperson to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": SalespersonInfo
            }
            or
            {
                "success": False,
                "error": "Salesperson not found"
            }
        Constraints:
            - SalespersonID must exist in the database.
        """
        if SalespersonID in self.salespersons:
            return {
                "success": True,
                "data": self.salespersons[SalespersonID]
            }
        else:
            return {
                "success": False,
                "error": "Salesperson not found"
            }

    def aggregate_sales_data(
        self, 
        aggregations: Dict[str, str], 
        group_by: list = None
    ) -> dict:
        """
        Compute aggregates (e.g., total sales, quantities, revenue) over sales records,
        optionally grouped by fields (product, customer, date, etc.).

        Args:
            aggregations (Dict[str, str]): Dictionary mapping aggregation name to field.
                Supported aggregations: "sum", "count", "avg", "min", "max".
                E.g., { "sum": "SaleAmount", "count": "SaleID" }
            group_by (list, optional): List of SalesRecordInfo field names by which to group results.
                If None or empty, aggregates over all records.

        Returns:
            dict: 
            {
                "success": True,
                "data": List[dict],  # Each dict has group_by fields and aggregate results
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - All fields in aggregations and group_by must exist in SalesRecordInfo.
            - Only numeric aggregations (sum/avg/min/max) supported on numeric fields.
            - "count" is always supported; it counts the number of records per group.
        """

        # Define valid fields
        valid_fields = {
            'SaleID', 'ProductID', 'ProductName', 'Timestamp',
            'QuantitySold', 'CustomerID', 'SaleAmount', 'SalespersonID'
        }
        # Define numeric fields for sum/avg/min/max
        numeric_fields = {'QuantitySold', 'SaleAmount'}

        if not isinstance(aggregations, dict) or not aggregations:
            return {"success": False, "error": "Aggregations must be a non-empty dict"}

        if group_by is None:
            group_by = []
        if not isinstance(group_by, list):
            return {"success": False, "error": "group_by must be a list of field names"}
        for field in group_by:
            if field not in valid_fields:
                return {"success": False, "error": f"Invalid group_by field: '{field}'"}

        for agg, field in aggregations.items():
            if agg not in {"sum", "count", "avg", "min", "max"}:
                return {"success": False, "error": f"Unsupported aggregation: '{agg}'"}
            if agg != "count":
                if field not in numeric_fields:
                    return {"success": False, "error": f"Aggregation '{agg}' requires a numeric field, got '{field}'"}
            else:
                if field not in valid_fields:
                    return {"success": False, "error": f"Invalid field for count aggregation: '{field}'"}

        # Prepare grouping
        grouped = {}
        for record in self.sales_records.values():
            # Compose group key
            key = tuple(record[field] for field in group_by) if group_by else ('__all__',)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
    
        result = []
        for group_key, records in grouped.items():
            entry = {}
            # Add group_by keys to result entry
            if group_by:
                for idx, field in enumerate(group_by):
                    entry[field] = group_key[idx]
            # Compute requested aggregates
            for agg, field in aggregations.items():
                values = [r[field] for r in records if field in r]
                if agg == "count":
                    # count the number of records (not the number of non-null field values)
                    entry[f"{agg}_{field}"] = len(records)
                elif len(values) == 0:
                    entry[f"{agg}_{field}"] = None
                elif agg == "sum":
                    entry[f"{agg}_{field}"] = sum(values)
                elif agg == "avg":
                    entry[f"{agg}_{field}"] = sum(values) / len(values) if values else 0
                elif agg == "min":
                    entry[f"{agg}_{field}"] = min(values)
                elif agg == "max":
                    entry[f"{agg}_{field}"] = max(values)
            result.append(entry)
        return {"success": True, "data": result}

    def filter_products(
        self,
        category: str = None,
        min_price: float = None,
        max_price: float = None
    ) -> dict:
        """
        Retrieve products that match the specified filter criteria.
    
        Args:
            category (str, optional): Only include products in this category.
            min_price (float, optional): Only include products with Price >= min_price.
            max_price (float, optional): Only include products with Price <= max_price.
    
        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo] # List of matching products
            }
            or
            {
                "success": False,
                "error": str # Description of the error
            }
    
        Constraints:
            - If min_price and max_price are both provided, min_price must be <= max_price.
            - All filter fields are optional; no filter means all products.
        """

        # Input validation
        if min_price is not None and max_price is not None:
            try:
                if float(min_price) > float(max_price):
                    return { "success": False, "error": "min_price cannot be greater than max_price" }
            except Exception:
                return { "success": False, "error": "Invalid values for min_price or max_price" }

        results = []
        for p in self.products.values():
            # Filter by category if specified and non-empty
            if category is not None and category != "" and p.get("Category") != category:
                continue
            # Filter by min_price if specified
            if min_price is not None:
                try:
                    if float(p.get("Price", 0)) < float(min_price):
                        continue
                except Exception:
                    continue  # Skip product if Price is bad (should not happen in clean DB)
            # Filter by max_price if specified
            if max_price is not None:
                try:
                    if float(p.get("Price", 0)) > float(max_price):
                        continue
                except Exception:
                    continue
            results.append(p)

        return { "success": True, "data": results }

    def get_product_sales_history(
        self,
        product_id: str,
        start_date: str = None,
        end_date: str = None,
        customer_id: str = None,
        salesperson_id: str = None,
    ) -> dict:
        """
        Retrieve the sales history for a specific product, with optional filters.
    
        Args:
            product_id (str): ProductID whose sales history will be retrieved.
            start_date (str, optional): Filter for lower bound of Timestamp (inclusive), ISO 8601 format.
            end_date (str, optional): Filter for upper bound of Timestamp (inclusive), ISO 8601 format.
            customer_id (str, optional): Only retrieve sales for this customer.
            salesperson_id (str, optional): Only retrieve sales by this salesperson.
    
        Returns:
            dict: {
                "success": True,
                "data": List[SalesRecordInfo]  # All matching sale records
            }
            or
            {
                "success": False,
                "error": "<error message>"
            }
        
        Constraints:
            - product_id must exist in products table.
            - If no matching records, data is an empty list.
            - start_date and end_date must be the same format as stored Timestamps (ISO 8601), if provided.
        """
        if product_id not in self.products:
            return { "success": False, "error": "ProductID does not exist" }

        # Filtering function
        def record_matches(sr: SalesRecordInfo) -> bool:
            if sr["ProductID"] != product_id:
                return False
            if start_date is not None and sr["Timestamp"] < start_date:
                return False
            if end_date is not None and sr["Timestamp"] > end_date:
                return False
            if customer_id is not None and sr["CustomerID"] != customer_id:
                return False
            if salesperson_id is not None and sr["SalespersonID"] != salesperson_id:
                return False
            return True

        # Run filter
        result = [
            sr for sr in self.sales_records.values()
            if record_matches(sr)
        ]

        return { "success": True, "data": result }

    def get_customer_purchase_history(self, customer_id: str) -> dict:
        """
        Retrieve all sales records made to a particular customer.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: {
                "success": True,
                "data": List[SalesRecordInfo],  # All sales records for this customer (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # "Customer not found" if invalid ID
            }

        Constraints:
            - The customer_id must exist in the database.
        """
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        sales_list = [
            record for record in self.sales_records.values()
            if record["CustomerID"] == customer_id
        ]

        return {"success": True, "data": sales_list}

    def get_sales_by_salesperson(self, SalespersonID: str) -> dict:
        """
        Retrieve all sales records associated with the given SalespersonID.

        Args:
            SalespersonID (str): The unique identifier of the salesperson to filter sales records.

        Returns:
            dict: {
                "success": True,
                "data": List[SalesRecordInfo]  # Sales records for this salesperson (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Salesperson does not exist"
            }

        Constraints:
            - SalespersonID must exist in self.salespersons.
            - Only sales records directly matching this SalespersonID are included.
        """
        if SalespersonID not in self.salespersons:
            return {"success": False, "error": "Salesperson does not exist"}

        records = [
            record for record in self.sales_records.values()
            if record["SalespersonID"] == SalespersonID
        ]

        return {"success": True, "data": records}

    def insert_sales_record(
        self, 
        SaleID: str, 
        ProductID: str, 
        ProductName: str, 
        Timestamp: str, 
        QuantitySold: int, 
        CustomerID: str, 
        SaleAmount: float, 
        SalespersonID: str
    ) -> dict:
        """
        Add a new sales record to the database, ensuring:
          - SaleID is unique.
          - ProductID, CustomerID, and SalespersonID reference valid existing entries.
          - QuantitySold is a non-negative integer.

        Args:
            SaleID (str): Unique identifier for the sale.
            ProductID (str): Foreign key referencing a Product.
            ProductName (str): Name of the product sold.
            Timestamp (str): Timestamp of sale (assumed properly formatted).
            QuantitySold (int): Number of units sold (must be >= 0).
            CustomerID (str): Foreign key referencing a Customer.
            SaleAmount (float): Amount of the sale.
            SalespersonID (str): Foreign key referencing a Salesperson.

        Returns:
            dict:
              { "success": True, "message": "Sales record inserted successfully." }
            or
              { "success": False, "error": "Error message describing why insert failed." }
        """
        # Check SaleID uniqueness
        if SaleID in self.sales_records:
            return { "success": False, "error": "SaleID already exists." }
        # Check foreign keys: ProductID, CustomerID, SalespersonID
        if ProductID not in self.products:
            return { "success": False, "error": "ProductID does not exist." }
        if CustomerID not in self.customers:
            return { "success": False, "error": "CustomerID does not exist." }
        if SalespersonID not in self.salespersons:
            return { "success": False, "error": "SalespersonID does not exist." }
        # Check QuantitySold non-negative integer
        if not isinstance(QuantitySold, int) or QuantitySold < 0:
            return { "success": False, "error": "QuantitySold must be a non-negative integer." }
        # (Optional) Check Timestamp format/validity if necessary

        # Build record
        record: SalesRecordInfo = {
            "SaleID": SaleID,
            "ProductID": ProductID,
            "ProductName": ProductName,
            "Timestamp": Timestamp,
            "QuantitySold": QuantitySold,
            "CustomerID": CustomerID,
            "SaleAmount": SaleAmount,
            "SalespersonID": SalespersonID
        }
        self.sales_records[SaleID] = record
        return { "success": True, "message": "Sales record inserted successfully." }

    def update_sales_record(self, SaleID: str, updates: dict) -> dict:
        """
        Modify fields of an existing sales record (SaleID).

        Args:
            SaleID (str): The SaleID of the record to update.
            updates (dict): Dictionary of fields to update and their new values.
                            Allowed fields: ProductID, ProductName, Timestamp, QuantitySold,
                            CustomerID, SaleAmount, SalespersonID

        Returns:
            dict: {
                "success": True,
                "message": "Sales record updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - SaleID must exist.
            - Cannot update SaleID field itself.
            - ProductID, CustomerID, SalespersonID must reference existing entities if updated.
            - QuantitySold must be a non-negative integer if updated.
            - All updates must respect data integrity and allowed fields.
        """
        if SaleID not in self.sales_records:
            return { "success": False, "error": "SaleID does not exist." }

        # Prevent SaleID update and get valid field keys
        allowed_fields = {"ProductID", "ProductName", "Timestamp", "QuantitySold", "CustomerID", "SaleAmount", "SalespersonID"}
        for key in updates.keys():
            if key == "SaleID":
                return { "success": False, "error": "Cannot update SaleID." }
            if key not in allowed_fields:
                return { "success": False, "error": f"Invalid field: {key}." }

        # Data integrity checks
        if "ProductID" in updates:
            new_pid = updates["ProductID"]
            if new_pid not in self.products:
                return { "success": False, "error": "ProductID does not reference an existing product." }
            # If ProductName not also given, auto-update it to match product reference
            if "ProductName" not in updates:
                updates["ProductName"] = self.products[new_pid]["ProductName"]
        if "CustomerID" in updates:
            if updates["CustomerID"] not in self.customers:
                return { "success": False, "error": "CustomerID does not reference an existing customer." }
        if "SalespersonID" in updates:
            if updates["SalespersonID"] not in self.salespersons:
                return { "success": False, "error": "SalespersonID does not reference an existing salesperson." }
        if "QuantitySold" in updates:
            qs = updates["QuantitySold"]
            if not isinstance(qs, int) or qs < 0:
                return { "success": False, "error": "QuantitySold must be a non-negative integer." }

        # Perform the update
        record = self.sales_records[SaleID]
        for key, value in updates.items():
            record[key] = value

        return { "success": True, "message": "Sales record updated successfully." }

    def delete_sales_record(self, sale_id: str) -> dict:
        """
        Remove a sales record from the database by its unique SaleID.

        Args:
            sale_id (str): The SaleID of the record to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Sales record with SaleID <sale_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Sales record with SaleID <sale_id> does not exist."
            }

        Constraints:
            - SaleID must exist in the database (primary key).
            - Data integrity remains preserved after deletion.
        """
        if sale_id not in self.sales_records:
            return {
                "success": False,
                "error": f"Sales record with SaleID {sale_id} does not exist."
            }

        del self.sales_records[sale_id]
        return {
            "success": True,
            "message": f"Sales record with SaleID {sale_id} deleted."
        }

    def insert_product(
        self,
        ProductID: str,
        ProductName: str,
        Category: str,
        Price: float
    ) -> dict:
        """
        Add a new product to the products table.

        Args:
            ProductID (str): Unique identifier for the product.
            ProductName (str): Name of the product.
            Category (str): The product's category.
            Price (float): Product price (should be non-negative).

        Returns:
            dict:
                On success: { "success": True, "message": "Product inserted successfully." }
                On failure: { "success": False, "error": "Reason for failure" }

        Constraints:
            - ProductID must be unique (not already present).
            - All fields must be present and valid.
            - Price must be non-negative.
        """
        # Check for existing ProductID
        if not ProductID or ProductID in self.products:
            return { "success": False, "error": "ProductID is missing or already exists." }

        # Validate required fields
        if not isinstance(ProductName, str) or not ProductName.strip():
            return { "success": False, "error": "ProductName must be a non-empty string." }
        if not isinstance(Category, str) or not Category.strip():
            return { "success": False, "error": "Category must be a non-empty string." }
        if not isinstance(Price, (int, float)):
            return { "success": False, "error": "Price must be a number." }
        if Price < 0:
            return { "success": False, "error": "Price must be non-negative." }

        # Insert product
        self.products[ProductID] = {
            "ProductID": ProductID,
            "ProductName": ProductName,
            "Category": Category,
            "Price": float(Price)
        }
        return { "success": True, "message": "Product inserted successfully." }

    def update_product(
        self,
        ProductID: str,
        ProductName: str = None,
        Category: str = None,
        Price: float = None
    ) -> dict:
        """
        Modify details of an existing product.
    
        Args:
            ProductID (str): ID of the product to update (must exist).
            ProductName (str, optional): New product name.
            Category (str, optional): New category.
            Price (float, optional): New price (must be non-negative).

        Returns:
            dict: 
                - { "success": True, "message": "Product updated successfully." }
                - { "success": False, "error": <error reason> }

        Constraints:
            - ProductID must exist in products.
            - Only ProductName, Category, and Price can be updated.
            - Price (if provided) must be >= 0.
            - At least one updatable field must be provided.
        """
        if ProductID not in self.products:
            return { "success": False, "error": "ProductID does not exist." }
    
        update_fields = {}
        if ProductName is not None:
            update_fields["ProductName"] = ProductName
        if Category is not None:
            update_fields["Category"] = Category
        if Price is not None:
            if not isinstance(Price, (int, float)):  # Defensive type check
                return { "success": False, "error": "Price must be a number." }
            if Price < 0:
                return { "success": False, "error": "Price cannot be negative." }
            update_fields["Price"] = float(Price)
    
        if not update_fields:
            return { "success": False, "error": "No fields to update provided." }
    
        # Update the fields
        product = self.products[ProductID]
        for k, v in update_fields.items():
            product[k] = v

        self.products[ProductID] = product  # Not strictly necessary (dict mutability), but explicit

        return { "success": True, "message": "Product updated successfully." }

    def delete_product(self, product_id: str) -> dict:
        """
        Remove a product by ProductID, with checks for references in sales records.

        Args:
            product_id (str): The ProductID of the product to remove.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Product <ProductID> deleted."}
                On failure:
                    {"success": False, "error": "Product not found."}
                    {"success": False, "error": "Product is referenced in sales records and cannot be deleted."}

        Constraints:
            - ProductID must exist in the products table.
            - Product must not be referenced in any sales record (foreign key constraint).
        """
        # Check if the product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product not found."}

        # Check if the product is referenced by any sales record
        for record in self.sales_records.values():
            if record["ProductID"] == product_id:
                return {
                    "success": False, 
                    "error": "Product is referenced in sales records and cannot be deleted."
                }

        # Passed checks: safe to delete
        del self.products[product_id]
        return {"success": True, "message": f"Product {product_id} deleted."}

    def insert_customer(self, CustomerID: str, CustomerName: str, ContactInfo: str) -> dict:
        """
        Add a new customer to the relational database.

        Args:
            CustomerID (str): Unique identifier for the customer.
            CustomerName (str): Name of the customer.
            ContactInfo (str): Contact information for the customer.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Customer inserted successfully" }
                - On failure (duplicate): { "success": False, "error": "CustomerID already exists" }
                - On failure (invalid input): { "success": False, "error": "Missing or invalid customer data" }

        Constraints:
            - CustomerID must be unique within the system.
            - All attributes must be present and non-empty.
        """
        # Basic validation
        if not CustomerID or not isinstance(CustomerID, str):
            return { "success": False, "error": "Missing or invalid CustomerID" }
        if not CustomerName or not isinstance(CustomerName, str):
            return { "success": False, "error": "Missing or invalid CustomerName" }
        if not ContactInfo or not isinstance(ContactInfo, str):
            return { "success": False, "error": "Missing or invalid ContactInfo" }

        # Enforce CustomerID uniqueness
        if CustomerID in self.customers:
            return { "success": False, "error": "CustomerID already exists" }

        # Add new customer
        self.customers[CustomerID] = {
            "CustomerID": CustomerID,
            "CustomerName": CustomerName,
            "ContactInfo": ContactInfo
        }

        return { "success": True, "message": "Customer inserted successfully" }

    def update_customer(
        self, 
        CustomerID: str, 
        update_fields: dict
    ) -> dict:
        """
        Update information for an existing customer.

        Args:
            CustomerID (str): The unique ID of the customer to update.
            update_fields (dict): Dictionary with keys as updatable customer fields
                                  ('CustomerName', 'ContactInfo') and their new values.

        Returns:
            dict: 
                If success: { "success": True, "message": "Customer information updated." }
                If failure: { "success": False, "error": <reason> }

        Constraints:
            - CustomerID must exist in the customers table.
            - Only 'CustomerName' and 'ContactInfo' are allowed to be updated.
        """
        if CustomerID not in self.customers:
            return { "success": False, "error": "CustomerID does not exist." }
    
        valid_fields = {'CustomerName', 'ContactInfo'}
        # Intersect and filter only valid fields
        fields_to_update = {k: v for k, v in update_fields.items() if k in valid_fields}
        if not fields_to_update:
            return { "success": False, "error": "No valid fields provided to update." }
    
        # Update allowed fields
        for k, v in fields_to_update.items():
            self.customers[CustomerID][k] = v

        return { "success": True, "message": "Customer information updated." }

    def delete_customer(self, customer_id: str) -> dict:
        """
        Remove a customer from the database.

        Args:
            customer_id (str): The ID of the customer to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Customer <customer_id> deleted"
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (non-existence or foreign key constraint)
            }

        Constraints:
            - Cannot delete if the customer is referenced by any sales record (foreign key).
            - Customer must exist.
        """
        # Check if customer exists
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist" }

        # Check for foreign key references in sales records
        for record in self.sales_records.values():
            if record["CustomerID"] == customer_id:
                return {
                    "success": False,
                    "error": "Customer cannot be deleted as there are associated sales records"
                }

        # Passed checks: safe to delete
        del self.customers[customer_id]
        return {
            "success": True,
            "message": f"Customer {customer_id} deleted"
        }

    def insert_salesperson(self, SalespersonID: str, Name: str) -> dict:
        """
        Add a new salesperson to the system.

        Args:
            SalespersonID (str): Unique identifier for the salesperson.
            Name (str): Name of the salesperson.

        Returns:
            dict:
                - On success: {"success": True, "message": "Salesperson inserted successfully."}
                - On failure: {"success": False, "error": "<error description>"}

        Constraints:
            - SalespersonID must be unique (no duplicate IDs).
            - SalespersonID and Name must be non-empty strings.
        """
        if not SalespersonID or not isinstance(SalespersonID, str):
            return {"success": False, "error": "SalespersonID must be a non-empty string."}

        if not Name or not isinstance(Name, str):
            return {"success": False, "error": "Name must be a non-empty string."}

        if SalespersonID in self.salespersons:
            return {"success": False, "error": "SalespersonID already exists."}

        self.salespersons[SalespersonID] = {
            "SalespersonID": SalespersonID,
            "Name": Name
        }
        return {"success": True, "message": "Salesperson inserted successfully."}

    def update_salesperson(self, SalespersonID: str, updates: dict) -> dict:
        """
        Update the information of an existing salesperson.

        Args:
            SalespersonID (str): Identifier of the salesperson to update.
            updates (dict): Fields and new values to update. Allowed: 'Name'.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Salesperson <ID> updated successfully" }
                - On error: { "success": False, "error": str }
    
        Constraints:
            - SalespersonID must exist.
            - Only updatable fields are those in SalespersonInfo except 'SalespersonID' (in this schema, only 'Name').
        """

        if SalespersonID not in self.salespersons:
            return { "success": False, "error": "SalespersonID does not exist" }

        allowed_fields = {"Name"}
        updated = False

        for key, value in updates.items():
            if key in allowed_fields:
                self.salespersons[SalespersonID][key] = value
                updated = True

        if not updated:
            return { "success": False, "error": "No updatable fields provided" }

        return { "success": True, "message": f"Salesperson {SalespersonID} updated successfully" }

    def delete_salesperson(self, SalespersonID: str) -> dict:
        """
        Remove a salesperson from the system.

        Args:
            SalespersonID (str): The unique identifier for the salesperson to be removed.

        Returns:
            dict:
                - On success:
                      { "success": True, "message": "Salesperson <SalespersonID> removed." }
                - On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - SalespersonID must exist.
            - Cannot delete if referenced in any SalesRecord (foreign key constraint).
        """
        # Check existence
        if SalespersonID not in self.salespersons:
            return { "success": False, "error": "Salesperson not found." }
    
        # Check for foreign key references in sales records
        for sale in self.sales_records.values():
            if sale["SalespersonID"] == SalespersonID:
                return {
                    "success": False,
                    "error": "Cannot delete salesperson; referenced in sales records."
                }

        # Safely remove
        del self.salespersons[SalespersonID]
        return {
            "success": True,
            "message": f"Salesperson {SalespersonID} removed."
        }

    @staticmethod
    def _normalize_optional_filter(value):
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    def bulk_delete_sales_records(
        self,
        before_date: str = None,
        customer_id: str = None,
        product_id: str = None,
        salesperson_id: str = None,
    ) -> dict:
        """
        Delete multiple sales records matching given filter criteria.

        Args:
            before_date (str, optional): Delete sales records with Timestamp before this date (inclusive).
            customer_id (str, optional): Delete sales records from this customer.
            product_id (str, optional): Delete sales records for this product.
            salesperson_id (str, optional): Delete sales records for this salesperson.

        Returns:
            dict: {
                "success": True,
                "message": "<N> sales records deleted."
            }
            or
            {
                "success": False,
                "error": "<description of reason>"
            }

        Constraints:
            - All filters are optional; at least one filter must be provided to prevent accidental mass deletion.
            - Timestamps are compared as strings (expecting ISO format).
        """
        before_date = self._normalize_optional_filter(before_date)
        customer_id = self._normalize_optional_filter(customer_id)
        product_id = self._normalize_optional_filter(product_id)
        salesperson_id = self._normalize_optional_filter(salesperson_id)

        # Ensure at least one meaningful filter is specified
        if not any([before_date, customer_id, product_id, salesperson_id]):
            return {"success": False, "error": "At least one filter must be specified."}
    
        to_delete = []
        for sale_id, record in self.sales_records.items():
            if before_date is not None and not (record["Timestamp"] < before_date):
                continue
            if customer_id is not None and record["CustomerID"] != customer_id:
                continue
            if product_id is not None and record["ProductID"] != product_id:
                continue
            if salesperson_id is not None and record["SalespersonID"] != salesperson_id:
                continue
            to_delete.append(sale_id)
    
        for sale_id in to_delete:
            del self.sales_records[sale_id]
    
        return {
            "success": True,
            "message": f"{len(to_delete)} sales record(s) deleted."
        }

    def correct_sales_record_foreign_keys(
        self,
        foreign_key_field: str,
        old_id: str,
        new_id: str,
        sale_ids: list = None,
    ) -> dict:
        """
        Update the foreign key field in all sales records that reference old_id
        to new_id. Ensures data integrity by requiring that new_id exists in
        the corresponding referenced table.

        Args:
            foreign_key_field (str): The foreign key field to update ("ProductID", "CustomerID", or "SalespersonID")
            old_id (str): The old ID value to replace.
            new_id (str): The new ID value to set.

        Returns:
            dict: 
                On success: { "success": True, "message": "<n> sales records updated with new <field>." }
                On error: { "success": False, "error": str }

        Constraints:
            - Only "ProductID", "CustomerID", or "SalespersonID" fields may be updated.
            - new_id must exist in the corresponding referenced table.
            - Updates all matching records; if sale_ids is provided, only matching SaleIDs are updated.
            - If none exist, still a successful no-op.
            - If foreign key is "ProductID" and ProductName denormalized, update ProductName to match.
        """

        # Map field to referenced table
        valid_fk_fields = {
            "ProductID": ("products", "ProductID"),
            "CustomerID": ("customers", "CustomerID"),
            "SalespersonID": ("salespersons", "SalespersonID"),
        }
        if foreign_key_field not in valid_fk_fields:
            return {
                "success": False,
                "error": f"Unsupported foreign key field: {foreign_key_field}"
            }
    
        if old_id == new_id:
            return {
                "success": False,
                "error": "old_id and new_id are the same; no update necessary"
            }

        referenced_table_name, referenced_id_field = valid_fk_fields[foreign_key_field]
        referenced_table = getattr(self, referenced_table_name)

        # Check that new_id exists in referenced table
        if new_id not in referenced_table:
            return {
                "success": False,
                "error": f"new_id '{new_id}' does not exist in referenced table '{referenced_table_name}'"
            }

        targeted_sale_ids = None
        if sale_ids is not None:
            if not isinstance(sale_ids, list) or not sale_ids:
                return {
                    "success": False,
                    "error": "sale_ids must be a non-empty list when provided"
                }
            missing_sale_ids = [sale_id for sale_id in sale_ids if sale_id not in self.sales_records]
            if missing_sale_ids:
                return {
                    "success": False,
                    "error": f"Unknown SaleID(s): {', '.join(missing_sale_ids)}"
                }
            targeted_sale_ids = set(sale_ids)

        updated_count = 0

        # If ProductID is being updated, new ProductName must be updated from products table
        new_product_name = None
        if foreign_key_field == "ProductID":
            new_product_name = self.products[new_id]["ProductName"]

        for sale_id, record in self.sales_records.items():
            if targeted_sale_ids is not None and sale_id not in targeted_sale_ids:
                continue
            if record.get(foreign_key_field) == old_id:
                record[foreign_key_field] = new_id
                updated_count += 1
                if foreign_key_field == "ProductID":
                    record["ProductName"] = new_product_name

        return {
            "success": True,
            "message": f"{updated_count} sales records updated with new {foreign_key_field}."
        }

    def adjust_quantity_sold_in_record(self, sale_id: str, quantity_sold: int) -> dict:
        """
        Set or adjust the QuantitySold field of a sales record.

        Args:
            sale_id (str): The unique identifier for the sales record to update.
            quantity_sold (int): The non-negative integer to set as QuantitySold.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Quantity sold updated for sale record <sale_id>" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - sale_id must match an existing record.
            - quantity_sold must be a non-negative integer.
        """
        if sale_id not in self.sales_records:
            return { "success": False, "error": "SaleID not found" }
        if not isinstance(quantity_sold, int) or quantity_sold < 0:
            return { "success": False, "error": "QuantitySold must be a non-negative integer" }
    
        self.sales_records[sale_id]["QuantitySold"] = quantity_sold
        return { "success": True, "message": f"Quantity sold updated for sale record {sale_id}" }

    def update_sale_amount(self, sale_id: str, new_sale_amount: float) -> dict:
        """
        Change the SaleAmount of a specific sales record.

        Args:
            sale_id (str): Unique identifier of the sales record to update.
            new_sale_amount (float): The new sale amount to set. Must be non-negative.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "message": "SaleAmount for SaleID <sale_id> updated to <new_sale_amount>."
                    }
                - On failure (record not found or invalid input):
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - SaleID must exist in the database.
            - SaleAmount must be a non-negative float.
        """
        if sale_id not in self.sales_records:
            return {"success": False, "error": "Sales record not found."}

        if not isinstance(new_sale_amount, (float, int)):
            return {"success": False, "error": "SaleAmount must be a numeric value."}

        if new_sale_amount < 0:
            return {"success": False, "error": "SaleAmount must be non-negative."}

        self.sales_records[sale_id]["SaleAmount"] = float(new_sale_amount)

        return {
            "success": True,
            "message": f"SaleAmount for SaleID {sale_id} updated to {float(new_sale_amount)}."
        }


class SalesDataRelationalDatabase(BaseEnv):
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

    def query_sales_records(self, **kwargs):
        return self._call_inner_tool('query_sales_records', kwargs)

    def get_sales_record_by_id(self, **kwargs):
        return self._call_inner_tool('get_sales_record_by_id', kwargs)

    def list_all_products(self, **kwargs):
        return self._call_inner_tool('list_all_products', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_all_customers(self, **kwargs):
        return self._call_inner_tool('list_all_customers', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_all_salespersons(self, **kwargs):
        return self._call_inner_tool('list_all_salespersons', kwargs)

    def get_salesperson_by_id(self, **kwargs):
        return self._call_inner_tool('get_salesperson_by_id', kwargs)

    def aggregate_sales_data(self, **kwargs):
        return self._call_inner_tool('aggregate_sales_data', kwargs)

    def filter_products(self, **kwargs):
        return self._call_inner_tool('filter_products', kwargs)

    def get_product_sales_history(self, **kwargs):
        return self._call_inner_tool('get_product_sales_history', kwargs)

    def get_customer_purchase_history(self, **kwargs):
        return self._call_inner_tool('get_customer_purchase_history', kwargs)

    def get_sales_by_salesperson(self, **kwargs):
        return self._call_inner_tool('get_sales_by_salesperson', kwargs)

    def insert_sales_record(self, **kwargs):
        return self._call_inner_tool('insert_sales_record', kwargs)

    def update_sales_record(self, **kwargs):
        return self._call_inner_tool('update_sales_record', kwargs)

    def delete_sales_record(self, **kwargs):
        return self._call_inner_tool('delete_sales_record', kwargs)

    def insert_product(self, **kwargs):
        return self._call_inner_tool('insert_product', kwargs)

    def update_product(self, **kwargs):
        return self._call_inner_tool('update_product', kwargs)

    def delete_product(self, **kwargs):
        return self._call_inner_tool('delete_product', kwargs)

    def insert_customer(self, **kwargs):
        return self._call_inner_tool('insert_customer', kwargs)

    def update_customer(self, **kwargs):
        return self._call_inner_tool('update_customer', kwargs)

    def delete_customer(self, **kwargs):
        return self._call_inner_tool('delete_customer', kwargs)

    def insert_salesperson(self, **kwargs):
        return self._call_inner_tool('insert_salesperson', kwargs)

    def update_salesperson(self, **kwargs):
        return self._call_inner_tool('update_salesperson', kwargs)

    def delete_salesperson(self, **kwargs):
        return self._call_inner_tool('delete_salesperson', kwargs)

    def bulk_delete_sales_records(self, **kwargs):
        return self._call_inner_tool('bulk_delete_sales_records', kwargs)

    def correct_sales_record_foreign_keys(self, **kwargs):
        return self._call_inner_tool('correct_sales_record_foreign_keys', kwargs)

    def adjust_quantity_sold_in_record(self, **kwargs):
        return self._call_inner_tool('adjust_quantity_sold_in_record', kwargs)

    def update_sale_amount(self, **kwargs):
        return self._call_inner_tool('update_sale_amount', kwargs)
