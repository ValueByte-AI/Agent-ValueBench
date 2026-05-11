# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import re
import uuid, datetime



# Represents a user account within the cloud service provider.
class AccountInfo(TypedDict):
    account_id: str
    user_info: Any  # Could be dict or str, depending on detail
    account_status: str
    creation_date: str

# Represents a service instance provisioned for an account.
class ServiceInfo(TypedDict):
    service_id: str
    account_id: str
    product_id: str
    configuration_values: Dict[str, Any]  # attribute_name -> option value
    status: str
    provision_date: str

# Represents an offering in the cloud marketplace.
class ProductInfo(TypedDict):
    product_id: str
    name: str
    description: str
    category: str

# Represents a configurable attribute for a product.
class ProductAttributeInfo(TypedDict):
    product_id: str
    attribute_name: str
    options: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing cloud provider accounts, services, products, and attributes.
        """

        # Accounts: {account_id: AccountInfo}
        # Maps account IDs to account detail dicts
        self.accounts: Dict[str, AccountInfo] = {}

        # Services: {service_id: ServiceInfo}
        # Maps service IDs to service detail dicts
        self.services: Dict[str, ServiceInfo] = {}

        # Products: {product_id: ProductInfo}
        # Maps product IDs to product detail dicts
        self.products: Dict[str, ProductInfo] = {}

        # ProductAttributes: {product_id: List[ProductAttributeInfo]}
        # Maps product IDs to a list of attribute dicts
        self.product_attributes: Dict[str, List[ProductAttributeInfo]] = {}

        # Constraints (for reference in method implementations):
        # - Each service must be associated with both an existing account and a valid product.
        # - Configuration values for a service must comply with the product's attribute options.
        # - Only active accounts can provision new services.

    @staticmethod
    def _parse_remediation_requirements(remediation_note: Any) -> Dict[str, str]:
        if not isinstance(remediation_note, str):
            return {}
        pairs = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([A-Za-z0-9_.-]+)", remediation_note)
        return {key: value.rstrip(".,;:") for key, value in pairs}

    def _service_is_still_risky(self, service: ServiceInfo) -> bool:
        if service.get("status") == "terminated":
            return False
        required_values = self._parse_remediation_requirements(service.get("remediation_note"))
        if not required_values:
            return False
        current_values = service.get("configuration_values", {})
        for key, expected_value in required_values.items():
            if current_values.get(key) != expected_value:
                return True
        return False

    def _derive_account_status(self, account_id: str) -> str:
        account = self.accounts[account_id]
        stored_status = account.get("account_status")
        if not isinstance(stored_status, str) or not stored_status.endswith("_at_risk"):
            return stored_status
        has_risky_service = any(
            self._service_is_still_risky(service)
            for service in self.services.values()
            if service.get("account_id") == account_id
        )
        if has_risky_service:
            return stored_status
        return stored_status[: -len("_at_risk")]

    def _materialize_account_info(self, account_id: str) -> AccountInfo:
        account_info = copy.deepcopy(self.accounts[account_id])
        account_info["account_status"] = self._derive_account_status(account_id)
        return account_info

    def get_account_by_id(self, account_id: str) -> dict:
        """
        Retrieve account information for the specified account ID.

        Args:
            account_id (str): The unique identifier of the account.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": AccountInfo
                }
                On failure: {
                    "success": False,
                    "error": "Account not found"
                }

        Constraints:
            - The account_id must exist in the current system.
        """
        account_info = self.accounts.get(account_id)
        if account_info is None:
            return { "success": False, "error": "Account not found" }
        return { "success": True, "data": self._materialize_account_info(account_id) }

    def list_all_accounts(self) -> dict:
        """
        List details for all user accounts present in the system.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[AccountInfo]   # List of all accounts, may be empty
                }
        """
        account_list = [
            self._materialize_account_info(account_id)
            for account_id in self.accounts
        ]
        return {
            "success": True,
            "data": account_list
        }

    def get_account_status(self, account_id: str) -> dict:
        """
        Query the current status (e.g., active, suspended) of a specific account.

        Args:
            account_id (str): The identifier of the account.

        Returns:
            dict:
                On success:
                    {"success": True, "data": account_status (str)}
                On failure (account not found):
                    {"success": False, "error": "Account not found"}
        """
        account = self.accounts.get(account_id)
        if account is None:
            return {"success": False, "error": "Account not found"}
        return {"success": True, "data": self._derive_account_status(account_id)}

    def list_services_by_account(self, account_id: str) -> dict:
        """
        List all service instances (ServiceInfo) provisioned under a given account.

        Args:
            account_id (str): The account ID whose services will be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ServiceInfo],  # all ServiceInfo with this account_id (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Account not found"
            }

        Constraints:
            - The account_id must exist in the system.
        """
        if account_id not in self.accounts:
            return { "success": False, "error": "Account not found" }

        services = [
            service_info
            for service_info in self.services.values()
            if service_info["account_id"] == account_id
        ]

        return { "success": True, "data": services }

    def get_service_by_id(self, service_id: str) -> dict:
        """
        Retrieve detailed information for a specific service instance by its ID.

        Args:
            service_id (str): The unique identifier of the service instance.

        Returns:
            dict: {
                "success": True,
                "data": ServiceInfo  # Dictionary of the service details
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., "Service not found"
            }

        Constraints:
            - The service must exist in the system (lookup by service_id).
            - No state modification occurs.
        """
        service = self.services.get(service_id)
        if not service:
            return {"success": False, "error": "Service not found"}

        return {"success": True, "data": service}

    def list_all_services(self) -> dict:
        """
        List all service instances provisioned across all accounts.

        Returns:
            dict:
                - success (bool): True if operation completes.
                - data (List[ServiceInfo]): List of all services (may be empty if none exist).
        """
        all_services = list(self.services.values())
        return { "success": True, "data": all_services }

    def list_products(self) -> dict:
        """
        Retrieve all product offerings in the cloud marketplace.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # May be empty if no products are available
            }
        """
        product_list = list(self.products.values())
        return {
            "success": True,
            "data": product_list
        }

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve detailed information about a specific product.

        Args:
            product_id (str): ID of the product to retrieve.

        Returns:
            dict:
                If found: { "success": True, "data": ProductInfo }
                If not found: { "success": False, "error": "Product not found" }

        Constraints:
            - Product must exist in the system.
        """
        product = self.products.get(product_id)
        if product is None:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def list_product_attributes(self, product_id: str) -> dict:
        """
        For a given product ID, return its configurable attributes and available options.

        Args:
            product_id (str): ID of the product whose attributes are to be listed.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ProductAttributeInfo]  # list of attribute dicts (possibly empty)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # e.g. "Product does not exist"
                    }
        Constraints:
            - product_id must refer to a valid product; otherwise, fail.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        attributes = self.product_attributes.get(product_id, [])
        return {"success": True, "data": attributes}

    def list_all_product_attributes(self) -> dict:
        """
        List attributes and option sets for all products in the marketplace.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, List[ProductAttributeInfo]]
                    # Maps product_id to list of ProductAttributeInfo (may be empty if none)
            }

        Constraints:
            - No specific constraints; global query of product attributes.
            - Products without attribute definitions should return an empty list.
        """
        # For every product, collect its attribute list (or empty list if none exist).
        result = {}
        for product_id in self.products:
            # product_attributes: Dict[product_id, List[ProductAttributeInfo]]
            result[product_id] = self.product_attributes.get(product_id, [])

        return { "success": True, "data": result }

    def validate_service_configuration(self, service_id: str) -> dict:
        """
        Validate that a service's configuration values comply with the attribute options
        defined for its associated product.

        Args:
            service_id (str): The ID of the service to validate.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "is_valid": bool,
                    "errors": List[str]  # present only if invalid, details per attribute
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., Service or Product not found
            }

        Constraints:
            - Service must exist.
            - Service must reference a valid product.
            - Each attribute in configuration_values must be defined for the product and set to one of its allowed options.
            - Unknown attributes or missing required attributes are considered invalid.
        """
        if service_id not in self.services:
            return {"success": False, "error": "Service does not exist"}

        service = self.services[service_id]
        product_id = service["product_id"]

        if product_id not in self.products:
            return {"success": False, "error": "Associated product does not exist"}

        config = service.get("configuration_values", {})
        product_attrs_list = self.product_attributes.get(product_id, [])

        # Build mapping of attribute_name -> set(options) for quick lookup
        product_attr_options = {
            attr_info["attribute_name"]: set(attr_info["options"])
            for attr_info in product_attrs_list
        }

        errors = []

        # Check for unknown attributes in configuration
        for attr_name in config:
            if attr_name not in product_attr_options:
                errors.append(f"Unknown attribute '{attr_name}' for product '{product_id}'.")

        # Check for required attributes missing from config (assuming all defined product attributes are required)
        for attr_name in product_attr_options:
            if attr_name not in config:
                errors.append(f"Missing required attribute '{attr_name}' in service configuration.")

        # Check values for known attributes
        for attr_name, value in config.items():
            if attr_name in product_attr_options:
                if value not in product_attr_options[attr_name]:
                    errors.append(
                        f"Invalid value '{value}' for attribute '{attr_name}': must be one of {sorted(product_attr_options[attr_name])}."
                    )

        if errors:
            return {
                "success": True,
                "data": {
                    "is_valid": False,
                    "errors": errors
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "is_valid": True
                }
            }

    def provision_service(
        self,
        account_id: str,
        product_id: str,
        configuration_values: Dict[str, Any]
    ) -> dict:
        """
        Provision (create) a new service instance under the given account using the given product and configuration.

        Args:
            account_id (str): The ID of the account that owns the service.
            product_id (str): The product ID to base the service on.
            configuration_values (Dict[str, Any]): Mapping of attribute name -> chosen option.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Service provisioned",
                    "service_id": <service_id>,
                    "service_info": <ServiceInfo>
                }
                On failure:
                {
                    "success": False,
                    "error": <reason>
                }
        Constraints:
            - Account must exist and be active.
            - Product must exist.
            - Configuration values must comply with the product's attribute options (both names and allowed option values).
        """
        # Check account
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account not found" }
        if account["account_status"] != "active":
            return { "success": False, "error": "Account is not active" }

        # Check product
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }

        # Gather product attributes
        attribute_list = self.product_attributes.get(product_id, [])
        # Build a mapping for easy lookup
        attr_options = { attr["attribute_name"]: attr["options"] for attr in attribute_list }

        # Validate configuration:
        # 1. All provided attributes exist and their value is in options
        for attr_name, attr_value in configuration_values.items():
            if attr_name not in attr_options:
                return {
                    "success": False,
                    "error": f"Attribute '{attr_name}' is not valid for product {product_id}"
                }
            if attr_value not in attr_options[attr_name]:
                return {
                    "success": False,
                    "error": f"Value '{attr_value}' is not allowed for attribute '{attr_name}'"
                }
        # 2. All required product attributes are present in configuration
        for attr in attr_options.keys():
            if attr not in configuration_values:
                return {
                    "success": False,
                    "error": f"Missing required attribute '{attr}' for product {product_id}"
                }

        # Generate unique service_id
        for _ in range(5):  # Try a few times to avoid (unlikely) collision
            service_id = f"svc-{uuid.uuid4().hex[:12]}"
            if service_id not in self.services:
                break
        else:
            return { "success": False, "error": "Could not generate unique service_id" }

        now = datetime.datetime.utcnow().isoformat() + "Z"

        service_info: ServiceInfo = {
            "service_id": service_id,
            "account_id": account_id,
            "product_id": product_id,
            "configuration_values": {k: v for k, v in configuration_values.items()},
            "status": "active",
            "provision_date": now
        }

        self.services[service_id] = service_info

        return {
            "success": True,
            "message": "Service provisioned",
            "service_id": service_id,
            "service_info": service_info
        }

    def update_service_configuration(self, service_id: str, new_configuration_values: Dict[str, Any]) -> dict:
        """
        Update the configuration values of an existing service.
        Provided values are merged into the existing configuration, and the
        merged configuration must comply with the allowed options specified by
        the product's attributes.

        Args:
            service_id (str): The service to update.
            new_configuration_values (Dict[str, Any]): Mapping of attribute_name -> new value.

        Returns:
            dict:
                - On success: { "success": True, "message": "Service configuration updated." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Service must exist.
            - Provided configuration values must correspond to valid attribute names for the product.
            - After merging with the existing configuration, all required attributes must be present.
            - Values must be among allowed options for each attribute.
        """
        # Check if service exists
        service = self.services.get(service_id)
        if not service:
            return { "success": False, "error": "Service ID not found." }
        if not isinstance(new_configuration_values, dict):
            return { "success": False, "error": "new_configuration_values must be a dictionary." }

        product_id = service["product_id"]

        # Check product exists
        if product_id not in self.products:
            return { "success": False, "error": "Associated product does not exist." }

        # Get product attributes
        attribute_list = self.product_attributes.get(product_id)
        if attribute_list is None:
            return { "success": False, "error": "No attributes defined for product." }

        # Build attribute validation lookup
        valid_attrs = { attr["attribute_name"]: attr["options"] for attr in attribute_list }

        # Merge requested changes into the current configuration so callers can
        # patch only the fields they intend to change.
        merged_configuration = copy.deepcopy(service.get("configuration_values", {}))
        merged_configuration.update(copy.deepcopy(new_configuration_values))

        # Check for completeness after merge: all attributes must be present.
        missing = [k for k in valid_attrs if k not in merged_configuration]
        if missing:
            return { "success": False, "error": f"Missing configuration for: {', '.join(missing)}" }

        for attr_name, value in merged_configuration.items():
            if attr_name not in valid_attrs:
                return { "success": False, "error": f"Attribute '{attr_name}' is not valid for this product." }
            if value not in valid_attrs[attr_name]:
                return { "success": False, "error": f"Value '{value}' not allowed for attribute '{attr_name}'." }

        # Passed validation, update config
        service["configuration_values"] = merged_configuration

        return { "success": True, "message": "Service configuration updated." }

    def terminate_service(self, service_id: str) -> dict:
        """
        Mark a service instance as terminated for a given service ID by updating its status.

        Args:
            service_id (str): The unique identifier of the service to terminate.

        Returns:
            dict: {
                "success": True,
                "message": "Service <service_id> has been terminated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Service must exist in the system.
            - If service is already terminated, operation fails gracefully.
            - Service status is updated to "terminated" (soft delete for auditing/history).
        """
        if service_id not in self.services:
            return { "success": False, "error": "Service does not exist." }

        service = self.services[service_id]
        if service["status"] == "terminated":
            return { "success": False, "error": "Service is already terminated." }

        service["status"] = "terminated"
        # Optionally, could update a timestamp field if present (not required here)
        self.services[service_id] = service

        return { "success": True, "message": f"Service {service_id} has been terminated." }

    def change_account_status(self, account_id: str, new_status: str) -> dict:
        """
        Update the status of a user account (e.g., activate, suspend).

        Args:
            account_id (str): Unique identifier of the account whose status will be changed.
            new_status (str): The new status to set for the account.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Account status updated to <new_status>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - The account_id must exist.
            - No restrictions on valid status values in this environment.
        """
        account = self.accounts.get(account_id)
        if not account:
            return { "success": False, "error": "Account not found." }
    
        old_status = account["account_status"]
        account["account_status"] = new_status

        if old_status == new_status:
            return {
                "success": True,
                "message": f"Account status was already '{new_status}'. No change made."
            }
        else:
            return {
                "success": True,
                "message": f"Account status updated to '{new_status}'."
            }

    def add_product(self, product_id: str, name: str, description: str, category: str) -> dict:
        """
        Add a new product offering to the marketplace.

        Args:
            product_id (str): Unique identifier of the new product.
            name (str): Name of the product.
            description (str): Description of the product.
            category (str): Category of the product.

        Returns:
            dict: {
                "success": True,
                "message": "Product <product_id> added to the marketplace."
            }
            or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - product_id must be unique (not already in the marketplace).
            - All fields must be non-empty strings.
        """
        # Check for unique product_id
        if not product_id or not isinstance(product_id, str):
            return { "success": False, "error": "Invalid or missing product_id." }
        if product_id in self.products:
            return { "success": False, "error": f"Product with id {product_id} already exists." }
        # Basic field validation
        if not all(isinstance(field, str) and field.strip() for field in [name, description, category]):
            return { "success": False, "error": "All fields (name, description, category) must be non-empty strings." }

        # Create and add product
        new_product = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "category": category
        }
        self.products[product_id] = new_product

        return {
            "success": True,
            "message": f"Product {product_id} added to the marketplace."
        }

    def update_product_attributes(self, product_id: str, attributes: list) -> dict:
        """
        Modify the configurable attributes or options for a given product.

        Args:
            product_id (str): The product ID to update attributes for.
            attributes (list of dict or ProductAttributeInfo): Each dict must have:
                - 'attribute_name' (str)
                - 'options' (list of str)

        Returns:
            dict: {
                "success": True,
                "message": "Product attributes updated for product <product_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Product must exist.
            - Each attribute must be a dict with 'attribute_name' (str) and 'options' (list of str).
        """

        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        if not isinstance(attributes, list):
            return {"success": False, "error": "Attributes input must be a list"}

        valid_attributes = []
        for idx, attr in enumerate(attributes):
            if not isinstance(attr, dict):
                return {"success": False, "error": f"Attribute at index {idx} is not a dict"}
            if 'attribute_name' not in attr or 'options' not in attr:
                return {"success": False, "error": f"Attribute at index {idx} missing required keys"}
            if not isinstance(attr['attribute_name'], str):
                return {"success": False, "error": f"'attribute_name' at index {idx} must be a string"}
            if not isinstance(attr['options'], list) or not all(isinstance(o, str) for o in attr['options']):
                return {"success": False, "error": f"'options' at index {idx} must be a list of strings"}
            # Compose ProductAttributeInfo dict
            valid_attributes.append({
                "product_id": product_id,
                "attribute_name": attr['attribute_name'],
                "options": attr['options']
            })

        self.product_attributes[product_id] = valid_attributes

        return {
            "success": True,
            "message": f"Product attributes updated for product {product_id}"
        }


class CloudAccountManagementSystem(BaseEnv):
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

    def get_account_by_id(self, **kwargs):
        return self._call_inner_tool('get_account_by_id', kwargs)

    def list_all_accounts(self, **kwargs):
        return self._call_inner_tool('list_all_accounts', kwargs)

    def get_account_status(self, **kwargs):
        return self._call_inner_tool('get_account_status', kwargs)

    def list_services_by_account(self, **kwargs):
        return self._call_inner_tool('list_services_by_account', kwargs)

    def get_service_by_id(self, **kwargs):
        return self._call_inner_tool('get_service_by_id', kwargs)

    def list_all_services(self, **kwargs):
        return self._call_inner_tool('list_all_services', kwargs)

    def list_products(self, **kwargs):
        return self._call_inner_tool('list_products', kwargs)

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_product_attributes(self, **kwargs):
        return self._call_inner_tool('list_product_attributes', kwargs)

    def list_all_product_attributes(self, **kwargs):
        return self._call_inner_tool('list_all_product_attributes', kwargs)

    def validate_service_configuration(self, **kwargs):
        return self._call_inner_tool('validate_service_configuration', kwargs)

    def provision_service(self, **kwargs):
        return self._call_inner_tool('provision_service', kwargs)

    def update_service_configuration(self, **kwargs):
        return self._call_inner_tool('update_service_configuration', kwargs)

    def terminate_service(self, **kwargs):
        return self._call_inner_tool('terminate_service', kwargs)

    def change_account_status(self, **kwargs):
        return self._call_inner_tool('change_account_status', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product_attributes(self, **kwargs):
        return self._call_inner_tool('update_product_attributes', kwargs)
