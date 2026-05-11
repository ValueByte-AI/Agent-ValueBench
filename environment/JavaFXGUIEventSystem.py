# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid



class UIComponentInfo(TypedDict):
    component_id: str
    component_type: str
    properties: Dict[str, Any]
    # Map event_type to a list of event_listener IDs registered for this component.
    event_listeners: Dict[str, List[str]]

class EventListenerInfo(TypedDict):
    event_type: str
    handler_reference: str  # could be a callable reference, using str for this static representation
    registered_component_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for a JavaFX-style GUI event management system.
        """

        # UI Components: {component_id: UIComponentInfo}
        # Attributes: component_id, component_type, properties, event_listeners
        self.ui_components: Dict[str, UIComponentInfo] = {}

        # Event Listeners: {event_listener_id: EventListenerInfo}
        # Attributes: event_type, handler_reference, registered_component_id
        self.event_listeners: Dict[str, EventListenerInfo] = {}

        # Constraints:
        # - Each UIComponent must have a unique component_id.
        # - EventListeners can only be registered on existing UIComponents.
        # - Only the event types supported by a UIComponent can have listeners registered or be triggered.
        # - Triggering an event will invoke all listeners associated with that event type for the affected UIComponent.

    def get_ui_component_by_id(self, component_id: str) -> dict:
        """
        Retrieve all information about a UI component (type, properties, registered event listeners)
        given its component_id.

        Args:
            component_id (str): The unique identifier of the UI component.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": UIComponentInfo  # All fields for the component
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # error description, e.g., "Component not found"
                    }

        Constraints:
            - The component_id must correspond to an existing UI component in the system.
        """
        component = self.ui_components.get(component_id)
        if component is None:
            return {"success": False, "error": "Component not found"}
        return {"success": True, "data": component}

    def list_ui_components(self) -> dict:
        """
        Retrieve a list of all UI components currently in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UIComponentInfo]  # List of all UI component dictionaries (may be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.ui_components.values())
        }

    def get_supported_event_types(self, component_id: str) -> dict:
        """
        Query which event types are supported by a given UI component.

        Args:
            component_id (str): Unique identifier of the UI component.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[str]  # Supported event types (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason, e.g., component does not exist
                    }

        Constraints:
            - Component must exist.
            - Supported event types are listed in properties["supported_event_types"] (list of str), or [] if missing.
        """
        component = self.ui_components.get(component_id)
        if not component:
            return { "success": False, "error": "Component does not exist" }

        # Convention: supported event types are listed in properties["supported_event_types"] as a list of strings
        supported_event_types = component["properties"].get("supported_event_types", [])
        if not isinstance(supported_event_types, list):
            # Defensive: property is present but not a list, so treat as none.
            supported_event_types = []

        return { "success": True, "data": supported_event_types }

    def list_event_listeners_for_component(self, component_id: str, event_type: str = None) -> dict:
        """
        List all event listeners registered for a specific UI component.
        Optionally filter by event_type.

        Args:
            component_id (str): The unique identifier of the UI component.
            event_type (str, optional): The type of event to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # each item includes event_listener_id plus EventListenerInfo fields
            }
            or
            {
                "success": False,
                "error": str  # reason for failure
            }

        Constraints:
            - component_id must correspond to an existing UI component.
            - Only listeners actually registered to this component (and optionally this event type) are listed.
        """
        # Check component existence
        component = self.ui_components.get(component_id)
        if not component:
            return { "success": False, "error": "UI component does not exist" }

        # Get the mapping of event_type to listener IDs for this component
        event_listeners_map = component.get("event_listeners", {})

        listener_ids = []
        if event_type is None:
            # All event types: accumulate all listener IDs
            for ids in event_listeners_map.values():
                listener_ids.extend(ids)
        else:
            ids = event_listeners_map.get(event_type, [])
            listener_ids.extend(ids)

        # Gather EventListenerInfo from self.event_listeners
        listeners_info = []
        for listener_id in listener_ids:
            listener_info = self.event_listeners.get(listener_id)
            if listener_info is None:
                continue
            listener_with_id = dict(listener_info)
            listener_with_id["event_listener_id"] = listener_id
            listeners_info.append(listener_with_id)

        return { "success": True, "data": listeners_info }

    def get_event_listener_by_id(self, event_listener_id: str) -> dict:
        """
        Retrieve details for a specific event listener given its ID.

        Args:
            event_listener_id (str): The unique identifier of the event listener.

        Returns:
            dict: {
                "success": True,
                "data": EventListenerInfo
            }
            or
            {
                "success": False,
                "error": "Event listener not found"
            }
        Constraints:
            - The event_listener_id must exist in the system.
        """
        listener = self.event_listeners.get(event_listener_id)
        if listener is None:
            return { "success": False, "error": "Event listener not found" }
        return { "success": True, "data": listener }

    def add_ui_component(self, component_id: str, component_type: str, properties: dict) -> dict:
        """
        Add a new UI component to the environment, ensuring a unique component_id.

        Args:
            component_id (str): Unique identifier for the new component.
            component_type (str): Type of the UI component (e.g., 'Button', 'Label').
            properties (dict): Initial properties for the component.

        Returns:
            dict: {
                "success": True,
                "message": "UI component <component_id> added."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - component_id must be unique.
            - component_type and properties must be provided and must be valid types.
        """
        # Check types
        if not isinstance(component_id, str) or not isinstance(component_type, str) or not isinstance(properties, dict):
            return { "success": False, "error": "Invalid argument types." }

        # Constraint: Unique component_id
        if component_id in self.ui_components:
            return { "success": False, "error": "Component ID already exists." }

        # Create the UIComponentInfo
        new_component: UIComponentInfo = {
            "component_id": component_id,
            "component_type": component_type,
            "properties": properties,
            "event_listeners": {}  # Start with no handlers.
        }

        self.ui_components[component_id] = new_component

        return { "success": True, "message": f"UI component {component_id} added." }

    def remove_ui_component(self, component_id: str) -> dict:
        """
        Remove an existing UI component and all its registered event listeners from the system.

        Args:
            component_id (str): The unique identifier of the UI component to remove.

        Returns:
            dict: 
                { "success": True, "message": "UI component and associated listeners removed." }
                or
                { "success": False, "error": "UI component does not exist." }

        Constraints:
            - If the UI component does not exist, the operation fails.
            - All event listeners registered to this component are also removed.
        """
        if component_id not in self.ui_components:
            return { "success": False, "error": "UI component does not exist." }

        # Remove associated event listeners
        to_remove = [
            listener_id for listener_id, listener_info in self.event_listeners.items()
            if listener_info["registered_component_id"] == component_id
        ]
        for listener_id in to_remove:
            del self.event_listeners[listener_id]

        # Remove the component itself
        del self.ui_components[component_id]

        return { "success": True, "message": "UI component and associated listeners removed." }

    def update_ui_component_properties(self, component_id: str, updated_properties: Dict[str, Any]) -> dict:
        """
        Modify the properties of a given UI component.

        Args:
            component_id (str): The ID of the target UI component.
            updated_properties (Dict[str, Any]): Dictionary of properties to update (key-value pairs).

        Returns:
            dict: {
                "success": True,
                "message": "Properties updated for component <id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The UI component must exist.
            - Properties are replaced/updated per the provided keys.
        """
        if component_id not in self.ui_components:
            return {"success": False, "error": "UIComponent does not exist"}

        # Update properties
        self.ui_components[component_id]['properties'].update(updated_properties)

        return {
            "success": True,
            "message": f"Properties updated for component {component_id}"
        }


    def register_event_listener(self, component_id: str, event_type: str, handler_reference: str) -> dict:
        """
        Register a new event listener (with a handler reference) on a specific event type
        for an existing UI component.

        Args:
            component_id (str): The ID of the UIComponent to attach the listener to.
            event_type (str): The type of event (e.g., "click") to listen for.
            handler_reference (str): A reference to the handler/callback.

        Returns:
            dict: 
                On success:
                    {
                        "success": True, 
                        "message": "Event listener registered",
                        "event_listener_id": <the new ID>
                    }
                On failure:
                    {
                        "success": False, 
                        "error": <reason>
                    }

        Constraints:
            - Must register on an existing UIComponent.
            - Only the UIComponent's supported event types may have listeners registered.
        """
        if component_id not in self.ui_components:
            return { "success": False, "error": "UI component not found" }

        comp = self.ui_components[component_id]

        supported_event_types = set(comp.get("properties", {}).get("supported_event_types", []))
        if event_type not in supported_event_types:
            return { "success": False, "error": f"Event type '{event_type}' not supported by this component" }

        # Generate unique event_listener_id
        event_listener_id = str(uuid.uuid4())

        # Register the listener info
        self.event_listeners[event_listener_id] = {
            "event_type": event_type,
            "handler_reference": handler_reference,
            "registered_component_id": component_id
        }

        # Add the listener to the component's event_listeners mapping
        comp["event_listeners"].setdefault(event_type, []).append(event_listener_id)

        return {
            "success": True,
            "message": "Event listener registered",
            "event_listener_id": event_listener_id
        }

    def remove_event_listener(
        self,
        event_listener_id: str = None,
        component_id: str = None,
        event_type: str = None
    ) -> dict:
        """
        Remove an event listener, either:
          - by its unique event_listener_id, or
          - by all listeners for a (component_id, event_type) pair.

        Args:
            event_listener_id (str, optional): Unique identifier for the event listener.
            component_id (str, optional): UI component identifier (required if removing by event_type).
            event_type (str, optional): Event type string (required if removing by event type).

        Returns:
            dict: {
                "success": True,
                "message": "Event listener(s) removed."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - If removing by id, id must exist.
            - If removing by component/event_type, component and event type must exist; removes all listeners for that type.
            - Only one method allowed per call (id or component/type), not both; both or neither yields error.
        """

        # Check proper input: only one removal mechanism allowed
        if event_listener_id is not None:
            # Removal by event_listener_id takes precedence, ignore others if given.
            if event_listener_id not in self.event_listeners:
                return {"success": False, "error": "Event listener id does not exist."}
            # Find the associated component and event_type
            listener_info = self.event_listeners[event_listener_id]
            comp_id = listener_info["registered_component_id"]
            ev_type = listener_info["event_type"]
            if comp_id not in self.ui_components:
                return {"success": False, "error": "Registered component for listener does not exist."}
            comp_info = self.ui_components[comp_id]
            # Remove from component's event_listeners registry
            if ev_type in comp_info["event_listeners"]:
                try:
                    comp_info["event_listeners"][ev_type].remove(event_listener_id)
                except ValueError:
                    pass  # Already missing, ignore
            # Remove from global event_listeners dict
            del self.event_listeners[event_listener_id]
            return {"success": True, "message": f"Event listener {event_listener_id} removed."}
        else:
            # Removal by component_id and event_type
            if (component_id is None) or (event_type is None):
                return {"success": False, "error": "Must provide either event_listener_id or (component_id and event_type)."}
            if component_id not in self.ui_components:
                return {"success": False, "error": "Component does not exist."}
            comp_info = self.ui_components[component_id]
            if event_type not in comp_info["event_listeners"] or not comp_info["event_listeners"][event_type]:
                return {"success": False, "error": "No listeners for that event type on this component."}
            # Remove all listeners for this event_type
            listener_ids = list(comp_info["event_listeners"][event_type])
            for lid in listener_ids:
                if lid in self.event_listeners:
                    del self.event_listeners[lid]
            comp_info["event_listeners"][event_type] = []
            return {
                "success": True,
                "message": f"All listeners for event type '{event_type}' on component '{component_id}' removed."
            }

    def trigger_event(self, component_id: str, event_type: str) -> dict:
        """
        Programmatically trigger a specific event type on a component, causing all registered
        listeners for that event to be invoked.

        Args:
            component_id (str): Unique identifier of the target UI component.
            event_type (str): The event type to trigger (e.g., "click").

        Returns:
            dict:
              Success: {
                "success": True,
                "message": (str),
                "invoked_handlers": List[str]  # handler_reference values for invoked listeners
              }
              Failure: {
                "success": False,
                "error": str
              }

        Constraints:
            - Component must exist.
            - Only event types supported/registered by the component can be triggered.
            - Triggering invokes all listeners for that event type (handlers listed).
        """
        if component_id not in self.ui_components:
            return {"success": False, "error": "Component does not exist"}
        component = self.ui_components[component_id]

        supported_event_types = set(component.get("properties", {}).get("supported_event_types", []))
        if event_type not in supported_event_types:
            return {"success": False, "error": f"Event type '{event_type}' is not supported by the component"}

        invoked_handlers = []
        listener_ids = component["event_listeners"].get(event_type, [])
        for listener_id in listener_ids:
            listener_info = self.event_listeners.get(listener_id)
            if listener_info is not None:
                invoked_handlers.append(listener_info["handler_reference"])

        return {
            "success": True,
            "message": f"Triggered event '{event_type}' on component '{component_id}'",
            "invoked_handlers": invoked_handlers
        }


class JavaFXGUIEventSystem(BaseEnv):
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

    def get_ui_component_by_id(self, **kwargs):
        return self._call_inner_tool('get_ui_component_by_id', kwargs)

    def list_ui_components(self, **kwargs):
        return self._call_inner_tool('list_ui_components', kwargs)

    def get_supported_event_types(self, **kwargs):
        return self._call_inner_tool('get_supported_event_types', kwargs)

    def list_event_listeners_for_component(self, **kwargs):
        return self._call_inner_tool('list_event_listeners_for_component', kwargs)

    def get_event_listener_by_id(self, **kwargs):
        return self._call_inner_tool('get_event_listener_by_id', kwargs)

    def add_ui_component(self, **kwargs):
        return self._call_inner_tool('add_ui_component', kwargs)

    def remove_ui_component(self, **kwargs):
        return self._call_inner_tool('remove_ui_component', kwargs)

    def update_ui_component_properties(self, **kwargs):
        return self._call_inner_tool('update_ui_component_properties', kwargs)

    def register_event_listener(self, **kwargs):
        return self._call_inner_tool('register_event_listener', kwargs)

    def remove_event_listener(self, **kwargs):
        return self._call_inner_tool('remove_event_listener', kwargs)

    def trigger_event(self, **kwargs):
        return self._call_inner_tool('trigger_event', kwargs)
