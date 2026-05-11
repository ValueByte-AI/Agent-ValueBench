# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import datetime
import uuid
from datetime import datetime



class AppInfo(TypedDict):
    app_id: str
    name: str
    install_status: str
    permissions_granted: List[str]
    is_running: bool
    last_opened_time: str
    app_setting: Dict[str, Any]

class DeviceSettingInfo(TypedDict):
    setting_name: str
    value: str

class PermissionInfo(TypedDict):
    permission_id: str
    app_id: str
    status: str  # e.g., "granted", "denied", "prompt"

class NotificationInfo(TypedDict):
    notification_id: str
    app_id: str
    content: str
    timestamp: str
    is_read: bool

class UserAccountInfo(TypedDict):
    user_id: str
    username: str
    preferences: Dict[str, Any]
    logged_in_status: bool

class SystemServiceInfo(TypedDict):
    service_id: str
    service_type: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Apps: {app_id: AppInfo}
        self.apps: Dict[str, AppInfo] = {}

        # Device Settings: {setting_name: DeviceSettingInfo}
        self.device_settings: Dict[str, DeviceSettingInfo] = {}

        # Permissions: {permission_id: PermissionInfo}
        self.permissions: Dict[str, PermissionInfo] = {}

        # Notifications: {notification_id: NotificationInfo}
        self.notifications: Dict[str, NotificationInfo] = {}

        # User Accounts: {user_id: UserAccountInfo}
        self.user_accounts: Dict[str, UserAccountInfo] = {}

        # System Services: {service_id: SystemServiceInfo}
        self.system_services: Dict[str, SystemServiceInfo] = {}

        # Constraints (see also methods to be implemented):
        # - Only apps with 'install_status' = "installed" can be opened.
        # - Required permissions (such as location for map apps) must be granted, or the system must prompt the user.
        # - System services required by apps (e.g., location) must be enabled for full functionality.
        # - Only one active user session may exist at a time (per user account).
        # - DeviceSettings can only be changed according to user permissions or system policy.

    def _find_permission_entry(self, app_id: str, permission_id: str):
        """
        Resolve a permission entry for an app using either the internal dict key or
        the externally exposed PermissionInfo.permission_id field.
        """
        permission = self.permissions.get(permission_id)
        if permission is not None and permission.get("app_id") == app_id:
            return permission_id, permission

        for internal_key, candidate in self.permissions.items():
            if candidate.get("app_id") == app_id and candidate.get("permission_id") == permission_id:
                return internal_key, candidate

        return None, None

    def get_app_by_name(self, name: str) -> dict:
        """
        Retrieve all app infos where the app's name exactly matches the given name.

        Args:
            name (str): Name of the app to query.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[AppInfo]  # List of apps with this name (may be empty if no matches found)
                }
                or
                {
                    "success": False,
                    "error": str  # If input is invalid
                }

        Constraints:
            - Name must not be empty.
            - Returns all matches; app names need not be unique.
        """
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid app name input." }

        results = [
            app_info for app_info in self.apps.values()
            if app_info["name"] == name
        ]

        return { "success": True, "data": results }

    def get_app_by_id(self, app_id: str) -> dict:
        """
        Retrieve app information by its app_id.

        Args:
            app_id (str): The unique identifier of the app.

        Returns:
            dict: {
                "success": True,
                "data": AppInfo  # App metadata for the given app_id
            }
            or
            {
                "success": False,
                "error": str  # Error message (e.g., "App not found")
            }

        Constraints:
            - No installation state or user permission checks are required for this query.
            - App must exist in self.apps.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App not found" }
        return { "success": True, "data": self.apps[app_id] }

    def list_installed_apps(self) -> dict:
        """
        List all installed applications.

        Returns:
            dict: {
                "success": True,
                "data": List[AppInfo]  # List of installed applications (could be empty)
            }
        """
        installed_apps = [
            app_info for app_info in self.apps.values()
            if app_info.get("install_status") == "installed"
        ]
        return { "success": True, "data": installed_apps }

    def get_app_install_status(self, app_id: str) -> dict:
        """
        Get the current install status of an app.

        Args:
            app_id (str): The unique identifier of the app.

        Returns:
            dict: {
                "success": True,
                "data": str  # The install_status of the app (e.g., "installed", "not_installed")
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., app not found)
            }

        Constraints:
            - The app must exist in the system.
        """
        app_info = self.apps.get(app_id)
        if not app_info:
            return { "success": False, "error": "App not found" }
        return { "success": True, "data": app_info["install_status"] }

    def get_app_permissions(self, app_id: str) -> dict:
        """
        List all granted and required permissions for an app.

        Args:
            app_id (str): Unique application identifier.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "granted": List[PermissionInfo],   # All permissions for this app with status == 'granted'
                    "required": List[PermissionInfo],  # All registered permissions for this app (any status)
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., 'App does not exist'
            }

        Constraints:
            - Fails if the app does not exist.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App does not exist" }
    
        # Get all permission objects associated with this app
        app_permissions = [
            permission for permission in self.permissions.values()
            if permission["app_id"] == app_id
        ]
        # Subset with status == 'granted'
        granted_permissions = [
            permission for permission in app_permissions
            if permission["status"] == "granted"
        ]
        return {
            "success": True,
            "data": {
                "granted": granted_permissions,
                "required": app_permissions
            }
        }

    def get_permission_status(self, app_id: str, permission_id: str) -> dict:
        """
        Query the current status ("granted", "denied", "prompt") for a specific permission on a given app.

        Args:
            app_id (str): The unique identifier for the app.
            permission_id (str): The unique identifier for the permission.

        Returns:
            dict:
                On success:
                    { "success": True, "data": "<status>" }
                On failure:
                    { "success": False, "error": "Permission not found for given app" }

        Constraints:
            - The (app_id, permission_id) must correspond to an entry in self.permissions.
        """
        for perm in self.permissions.values():
            if perm["app_id"] == app_id and perm["permission_id"] == permission_id:
                return {"success": True, "data": perm["status"]}
        return {"success": False, "error": "Permission not found for given app"}

    def get_app_running_status(self, app_id: str) -> dict:
        """
        Check if the app with the given app_id is currently running.

        Args:
            app_id (str): The ID of the app to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if the app is running, else False
            }
            or {
                "success": False,
                "error": str  # Reason for failure (e.g., app does not exist)
            }

        Constraints:
            - app_id must correspond to an app in the system.
        """
        app = self.apps.get(app_id)
        if not app:
            return {
                "success": False,
                "error": "App with given app_id does not exist"
            }
        return {
            "success": True,
            "data": app["is_running"]
        }

    def get_app_setting(self, app_id: str) -> dict:
        """
        Retrieve the configurable settings for the specified app.

        Args:
            app_id (str): The unique identifier of the app to query.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": Dict[str, Any]  # The app's settings dictionary.
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g., app not found)
                  }

        Constraints:
            - The given app_id must exist in the apps registry.
        """
        app_info = self.apps.get(app_id)
        if not app_info:
            return {"success": False, "error": "App not found"}

        return {"success": True, "data": app_info.get("app_setting", {})}

    def get_device_setting(self, setting_name: str) -> dict:
        """
        Query the current value of a device/system setting.

        Args:
            setting_name (str): The name of the device/system setting to query.

        Returns:
            dict: 
                - On success: 
                    { "success": True, "data": DeviceSettingInfo }
                - On failure (setting does not exist): 
                    { "success": False, "error": "Setting not found" }
        Constraints:
            - The setting must exist in the device_settings.
        """
        setting = self.device_settings.get(setting_name)
        if setting is None:
            return { "success": False, "error": "Setting not found" }
        return { "success": True, "data": setting }

    def get_system_service_status(self, service_id: str) -> dict:
        """
        Query the current status (enabled/disabled/running/etc.) of a specific system service.

        Args:
            service_id (str): Unique identifier for the system service.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": SystemServiceInfo }
                - On failure:
                    { "success": False, "error": "System service does not exist" }

        Constraints:
            - The specified service_id must exist in the system services.
        """
        service_info = self.system_services.get(service_id)
        if not service_info:
            return { "success": False, "error": "System service does not exist" }
        return { "success": True, "data": service_info }

    def get_notifications_for_app(self, app_id: str) -> dict:
        """
        Retrieve all notifications (read and unread) associated with the specified app.

        Args:
            app_id (str): The unique identifier of the app.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[NotificationInfo]  # Empty if no notifications exist for the app
                    }
                On failure:
                    {
                        "success": False,
                        "error": "App does not exist"
                    }

        Constraints:
            - The app_id must correspond to an existing app.
            - No filtering on notification status; both read and unread are included.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App does not exist" }

        notifications = [
            notif for notif in self.notifications.values()
            if notif["app_id"] == app_id
        ]
        return { "success": True, "data": notifications }

    def get_unread_notifications(self) -> dict:
        """
        List all unread notifications in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[NotificationInfo]  # List of unread notifications, empty if none
            }

        Constraints:
            - None (no permissions, session, or input is required).
        """
        unread = [
            notif for notif in self.notifications.values()
            if not notif.get("is_read", False)
        ]
        return { "success": True, "data": unread }

    def get_user_account_status(self, user_id: str) -> dict:
        """
        Query whether a user account is logged in and its preferences.

        Args:
            user_id (str): The unique identifier for the user account.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "user_id": str,
                            "logged_in_status": bool,
                            "preferences": Dict[str, Any]
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The user_id must exist in the system.
        """
        user = self.user_accounts.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        return {
            "success": True,
            "data": {
                "user_id": user["user_id"],
                "logged_in_status": user["logged_in_status"],
                "preferences": user["preferences"]
            }
        }

    def get_active_user_session(self) -> dict:
        """
        Find and return the currently active/logged-in user session on the device.

        Returns:
            dict: {
                "success": True,
                "data": UserAccountInfo | None
                    # User information if an active session exists, else None
            }
            (Never returns error unless internal bug arises.)

        Constraints:
            - Only one active user session may exist at a time (i.e., only one user should have logged_in_status == True).
        """
        for user in self.user_accounts.values():
            if user.get("logged_in_status", False):
                return {"success": True, "data": user}
        return {"success": True, "data": None}

    def list_all_permissions(self) -> dict:
        """
        List all defined permission types (unique permission IDs) in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Sorted list of unique permission IDs/types in the system
            }
            or
            {
                "success": False,
                "error": str
            }
        Notes:
            - Returns an empty list if there are no defined permissions.
            - No input parameters or constraints.
        """
        permission_types = sorted(set(
            perm_info["permission_id"] for perm_info in self.permissions.values()
        ))
        return { "success": True, "data": permission_types }

    def install_app(self, app_id: str) -> dict:
        """
        Change the installation status of an app to "installed".

        Args:
            app_id (str): The ID of the app to be installed.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "App <app_id> successfully installed."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (not found, already installed, etc.)
                    }

        Constraints:
            - The specified app_id must exist.
            - If the app is already installed, the operation is not performed and an error is returned.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App not found." }

        app_info = self.apps[app_id]

        if app_info.get("install_status", "").lower() == "installed":
            return { "success": False, "error": "App is already installed." }

        app_info["install_status"] = "installed"
        self.apps[app_id] = app_info  # Persist change

        return { "success": True, "message": f"App {app_id} successfully installed." }

    def uninstall_app(self, app_id: str) -> dict:
        """
        Remove an app by setting its install status to "uninstalled".

        Args:
            app_id (str): The unique identifier of the app to uninstall.

        Returns:
            dict:
                - On success: { "success": True, "message": "App '<app_id>' uninstalled successfully." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - App must exist in the system.
            - Only apps currently installed (install_status == "installed") can be uninstalled.
        """
        app = self.apps.get(app_id)
        if not app:
            return { "success": False, "error": f"App '{app_id}' does not exist." }
        if app["install_status"] != "installed":
            return { "success": False, "error": f"App '{app_id}' is not currently installed." }
        # Perform the uninstallation
        app["install_status"] = "uninstalled"
        # (Optional: could also set is_running = False or clean related permissions/notifications)
        return { "success": True, "message": f"App '{app_id}' uninstalled successfully." }

    def open_app(self, app_id: str) -> dict:
        """
        Launch an installed app: sets its is_running to True and updates last_opened_time.
    
        Args:
            app_id (str): The application ID to be launched.

        Returns:
            dict:
                - On success: { "success": True, "message": "App <app_id> launched." }
                - On error: { "success": False, "error": "Error message" }

        Constraints:
            - App must exist.
            - App's install_status must be "installed".
            - Updates is_running and last_opened_time fields.
        """

        app = self.apps.get(app_id)
        if app is None:
            return { "success": False, "error": "App does not exist." }
        if app.get("install_status") != "installed":
            return { "success": False, "error": "App is not installed." }

        app["is_running"] = True
        app["last_opened_time"] = datetime.now().isoformat()

        return { "success": True, "message": f"App {app_id} launched." }

    def close_app(self, app_id: str) -> dict:
        """
        Close a running app by setting its 'is_running' property to False.

        Args:
            app_id (str): The unique identifier for the app to close.

        Returns:
            dict: {
                "success": True,
                "message": "App <app_id> closed."
            }
            or
            {
                "success": False,
                "error": str  # Error message (app not found, not running)
            }

        Constraints:
            - The app must exist.
            - The app must currently be running to be closed.
        """
        app = self.apps.get(app_id)
        if app is None:
            return { "success": False, "error": "App not found" }
        if not app.get("is_running", False):
            return { "success": False, "error": "App is not currently running" }
        app["is_running"] = False
        return { "success": True, "message": f"App {app_id} closed." }

    def grant_permission(self, app_id: str, permission_id: str) -> dict:
        """
        Grant a permission for a specified app.

        Args:
            app_id (str): The ID of the app to grant permission to.
            permission_id (str): The ID of the permission to grant.

        Returns:
            dict:
                - Success: { "success": True, "message": "Permission granted to app." }
                - Failure: { "success": False, "error": "reason" }

        Constraints:
            - The app must exist.
            - The permission entry must exist and be associated with the specified app.
            - Operation is idempotent (already-granted is treated as success).
        """
        # Check app existence
        if app_id not in self.apps:
            return {"success": False, "error": "App not found."}
    
        internal_key, perm = self._find_permission_entry(app_id, permission_id)
        if perm is None:
            return {"success": False, "error": "Permission not found."}
    
        # Update status if not already granted
        updated = False
        if perm["status"] != "granted":
            perm["status"] = "granted"
            updated = True
            self.permissions[internal_key] = perm

        # Update app's permissions_granted if needed
        if permission_id not in self.apps[app_id]["permissions_granted"]:
            self.apps[app_id]["permissions_granted"].append(permission_id)
            updated = True

        return {"success": True, "message": "Permission granted to app."}

    def revoke_permission(self, app_id: str, permission_id: str) -> dict:
        """
        Revoke a previously granted permission for a specified app.

        Args:
            app_id (str): The ID of the app for which the permission is to be revoked.
            permission_id (str): The ID of the permission to revoke.

        Returns:
            dict: {
                "success": True,
                "message": "Permission '<permission_id>' revoked for app '<app_id>'."
            }
            OR
            {
                "success": False,
                "error": "reason: app/permission not found or not granted, etc."
            }

        Constraints:
            - Both app and permission must exist.
            - Permission must be associated with the specified app.
            - Permission must currently be "granted".
            - Upon success, the permission status is set to "denied", and it is removed from app's permissions_granted list if present.
        """
        # Check that app exists
        if app_id not in self.apps:
            return {"success": False, "error": f"App '{app_id}' does not exist."}
        internal_key, perm = self._find_permission_entry(app_id, permission_id)
        if perm is None:
            return {"success": False, "error": f"Permission '{permission_id}' does not exist."}
        # Check it is currently granted
        if perm["status"] != "granted":
            return {"success": False, "error": f"Permission '{permission_id}' is not currently granted."}
        # Mark as denied
        perm["status"] = "denied"
        self.permissions[internal_key] = perm
        # Remove from app's grants list if present
        if permission_id in self.apps[app_id]["permissions_granted"]:
            self.apps[app_id]["permissions_granted"].remove(permission_id)
        return {
            "success": True,
            "message": f"Permission '{permission_id}' revoked for app '{app_id}'."
        }

    def prompt_permission_request(self, app_id: str, permission_id: str) -> dict:
        """
        Trigger a simulated prompt to the user for the specified permission for an app.
    
        Args:
            app_id (str): ID of the app requesting permission.
            permission_id (str): ID of the permission to be prompted.
    
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Prompted user for permission <permission_id> for app <app_id>"
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - app_id must refer to an existing app.
            - permission_id must refer to an existing permission entry and must belong to app_id.
            - Sets permission status to "prompt" unless already "granted".
        """
        # Check app exists
        if app_id not in self.apps:
            return {"success": False, "error": f"App with id '{app_id}' does not exist"}

        internal_key, permission = self._find_permission_entry(app_id, permission_id)
        if not permission:
            return {"success": False, "error": f"Permission with id '{permission_id}' does not exist"}

        # Check status
        if permission["status"] == "granted":
            return {"success": True, "message": f"Permission '{permission_id}' for app '{app_id}' is already granted"}

        # Set permission status to "prompt"
        permission["status"] = "prompt"
        self.permissions[internal_key] = permission

        return {
            "success": True,
            "message": f"Prompted user for permission '{permission_id}' for app '{app_id}'"
        }

    def enable_system_service(self, service_id: str) -> dict:
        """
        Enable/start a system service (e.g., LocationService) so it is available to apps.

        Args:
            service_id (str): The unique identifier of the system service to enable.

        Returns:
            dict:
                - On success: {"success": True, "message": "System service '<service_id>' enabled."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The service_id must exist in the system.
            - If already enabled, the operation is idempotent and still returns success.
        """
        service = self.system_services.get(service_id)
        if service is None:
            return { "success": False, "error": f"System service '{service_id}' does not exist." }

        # Assuming "enabled" or "running" denotes an enabled service.
        # Treat already-enabled as success so callers can safely request a desired target state.
        if service["status"].lower() in ("enabled", "running"):
            return { "success": True, "message": f"System service '{service_id}' already enabled." }

        service["status"] = "enabled"
        return { "success": True, "message": f"System service '{service_id}' enabled." }

    def disable_system_service(self, service_id: str) -> dict:
        """
        Stop/disable a system service.

        Args:
            service_id (str): The unique ID of the system service to disable.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "System service <service_id> disabled."
                }
                OR
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - The system service must exist.
            - If the service is already disabled, the operation is idempotent and still returns success.
        """
        service = self.system_services.get(service_id)
        if not service:
            return {"success": False, "error": "System service not found"}

        if service["status"] == "disabled":
            return {"success": True, "message": f"System service {service_id} already disabled."}

        service["status"] = "disabled"
        self.system_services[service_id] = service

        return {"success": True, "message": f"System service {service_id} disabled."}

    def set_device_setting(self, setting_name: str, value: str) -> dict:
        """
        Change a device/system setting to a new value.

        Args:
            setting_name (str): The setting identifier (e.g., 'airplane_mode').
            value (str): The new value for the setting.
    
        Returns:
            dict: {
                "success": True,
                "message": "Device setting '<setting_name>' updated to '<value>'."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - The setting must exist in the device.
            - (Advanced, not implemented) Changing certain settings may be forbidden by system policy or user permissions.
        """
        if setting_name not in self.device_settings:
            return {"success": False, "error": f"Setting '{setting_name}' does not exist."}

        # In a richer environment, check user/system policy here

        # Update the setting value
        self.device_settings[setting_name]["value"] = value

        return {
            "success": True,
            "message": f"Device setting '{setting_name}' updated to '{value}'."
        }

    def update_app_setting(self, app_id: str, setting_key: str, setting_value: Any) -> dict:
        """
        Change an app-specific setting (e.g., theme, notification preference).

        Args:
            app_id (str): Unique identifier of the app.
            setting_key (str): The setting key to update for the app.
            setting_value (Any): The new value for the given setting key.

        Returns:
            dict: {
                "success": True,
                "message": "Setting '<key>' updated for app '<app_id>'"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The app must exist (app_id in self.apps).
            - It is allowed to add new keys to app_setting if not present.
            - No constraints regarding app installation state or setting key existence.
        """
        app = self.apps.get(app_id)
        if app is None:
            return { "success": False, "error": f"App with id '{app_id}' does not exist" }

        if not isinstance(app.get('app_setting'), dict):
            app['app_setting'] = {}

        app['app_setting'][setting_key] = setting_value
        return { "success": True, "message": f"Setting '{setting_key}' updated for app '{app_id}'" }

    def mark_notification_as_read(self, notification_id: str) -> dict:
        """
        Mark a notification as read by setting its 'is_read' status to True.

        Args:
            notification_id (str): The ID of the notification to mark as read.

        Returns:
            dict: {
                "success": True,
                "message": "Notification marked as read."
            }
            OR
            {
                "success": False,
                "error": "Notification not found."
            }

        Constraints:
            - The notification_id must exist in the notification store.
            - If already marked as read, the operation is idempotent and still returns success.
        """
        notification = self.notifications.get(notification_id)
        if not notification:
            return { "success": False, "error": "Notification not found." }
        notification['is_read'] = True
        self.notifications[notification_id] = notification  # Save back in case of mutable/immutable object.
        return { "success": True, "message": "Notification marked as read." }

    def send_notification(self, app_id: str, content: str, timestamp: str = None) -> dict:
        """
        Generate and display a system or app notification.

        Args:
            app_id (str): The app sending the notification (use "system" for a system notification).
            content (str): The notification message content.
            timestamp (str, optional): Timestamp string; if None, uses current time (ISO format).

        Returns:
            dict: {
                "success": True,
                "message": "Notification sent, id: <notification_id>"
            }
            or
            {
                "success": False,
                "error": <error string>
            }

        Constraints:
            - If app_id != "system", must exist in self.apps.
            - Notification content must not be empty.
            - Notification_id is auto-generated (unique).
        """

        if not content or not content.strip():
            return {"success": False, "error": "Notification content cannot be empty"}

        # System notification is allowed, otherwise app_id must exist
        if app_id != "system" and app_id not in self.apps:
            return {"success": False, "error": f"App id '{app_id}' does not exist"}
    
        notification_id = str(uuid.uuid4())
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()

        notification_info = {
            "notification_id": notification_id,
            "app_id": app_id,
            "content": content,
            "timestamp": timestamp,
            "is_read": False
        }

        self.notifications[notification_id] = notification_info

        return {
            "success": True,
            "message": f"Notification sent, id: {notification_id}"
        }

    def start_user_session(self, user_id: str) -> dict:
        """
        Log in or activate a user session for the specified user if not already active.

        Args:
            user_id (str): The unique identifier of the user account to activate.

        Returns:
            dict: {
                "success": True,
                "message": "User session started for <username>."
            }
            or
            {
                "success": False,
                "error": str  # Reason: user not found or session already active
            }

        Constraints:
            - Only one active user session may exist at a time for any user account.
        """
        user_info = self.user_accounts.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found." }

        if user_info.get("logged_in_status", False):
            return { "success": False, "error": "Session already active for user." }

        existing_active = [
            user for uid, user in self.user_accounts.items()
            if uid != user_id and user.get("logged_in_status", False)
        ]
        if existing_active:
            return {
                "success": False,
                "error": "Another user session is already active."
            }

        user_info["logged_in_status"] = True
        self.user_accounts[user_id] = user_info  # update state

        return { 
            "success": True, 
            "message": f"User session started for {user_info.get('username', user_id)}."
        }

    def end_user_session(self) -> dict:
        """
        Log out/end the current user session.

        Returns:
            dict: {
                "success": True,
                "message": "User session ended for <username/user_id>[, ...]"
            }
            or
            {
                "success": False,
                "error": "No active user session"
            }

        Constraints:
            - Only one active user session may exist at a time (per user account),
              but we end ALL currently active sessions for robustness.
        """
        active_users = [
            user_info for user_info in self.user_accounts.values()
            if user_info.get("logged_in_status", False)
        ]

        if not active_users:
            return { "success": False, "error": "No active user session" }

        ended_users = []
        for user_info in active_users:
            user_info["logged_in_status"] = False
            ended_users.append(user_info.get("username", user_info.get("user_id", "<unknown>")))

        ended_users_str = ", ".join(ended_users)
        return {
            "success": True,
            "message": f"User session ended for {ended_users_str}"
        }


class MobileOperatingSystemEnvironment(BaseEnv):
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

    def get_app_by_name(self, **kwargs):
        return self._call_inner_tool('get_app_by_name', kwargs)

    def get_app_by_id(self, **kwargs):
        return self._call_inner_tool('get_app_by_id', kwargs)

    def list_installed_apps(self, **kwargs):
        return self._call_inner_tool('list_installed_apps', kwargs)

    def get_app_install_status(self, **kwargs):
        return self._call_inner_tool('get_app_install_status', kwargs)

    def get_app_permissions(self, **kwargs):
        return self._call_inner_tool('get_app_permissions', kwargs)

    def get_permission_status(self, **kwargs):
        return self._call_inner_tool('get_permission_status', kwargs)

    def get_app_running_status(self, **kwargs):
        return self._call_inner_tool('get_app_running_status', kwargs)

    def get_app_setting(self, **kwargs):
        return self._call_inner_tool('get_app_setting', kwargs)

    def get_device_setting(self, **kwargs):
        return self._call_inner_tool('get_device_setting', kwargs)

    def get_system_service_status(self, **kwargs):
        return self._call_inner_tool('get_system_service_status', kwargs)

    def get_notifications_for_app(self, **kwargs):
        return self._call_inner_tool('get_notifications_for_app', kwargs)

    def get_unread_notifications(self, **kwargs):
        return self._call_inner_tool('get_unread_notifications', kwargs)

    def get_user_account_status(self, **kwargs):
        return self._call_inner_tool('get_user_account_status', kwargs)

    def get_active_user_session(self, **kwargs):
        return self._call_inner_tool('get_active_user_session', kwargs)

    def list_all_permissions(self, **kwargs):
        return self._call_inner_tool('list_all_permissions', kwargs)

    def install_app(self, **kwargs):
        return self._call_inner_tool('install_app', kwargs)

    def uninstall_app(self, **kwargs):
        return self._call_inner_tool('uninstall_app', kwargs)

    def open_app(self, **kwargs):
        return self._call_inner_tool('open_app', kwargs)

    def close_app(self, **kwargs):
        return self._call_inner_tool('close_app', kwargs)

    def grant_permission(self, **kwargs):
        return self._call_inner_tool('grant_permission', kwargs)

    def revoke_permission(self, **kwargs):
        return self._call_inner_tool('revoke_permission', kwargs)

    def prompt_permission_request(self, **kwargs):
        return self._call_inner_tool('prompt_permission_request', kwargs)

    def enable_system_service(self, **kwargs):
        return self._call_inner_tool('enable_system_service', kwargs)

    def disable_system_service(self, **kwargs):
        return self._call_inner_tool('disable_system_service', kwargs)

    def set_device_setting(self, **kwargs):
        return self._call_inner_tool('set_device_setting', kwargs)

    def update_app_setting(self, **kwargs):
        return self._call_inner_tool('update_app_setting', kwargs)

    def mark_notification_as_read(self, **kwargs):
        return self._call_inner_tool('mark_notification_as_read', kwargs)

    def send_notification(self, **kwargs):
        return self._call_inner_tool('send_notification', kwargs)

    def start_user_session(self, **kwargs):
        return self._call_inner_tool('start_user_session', kwargs)

    def end_user_session(self, **kwargs):
        return self._call_inner_tool('end_user_session', kwargs)
