# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import re
from typing import Any, Dict
from urllib.parse import urljoin

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict, Optional



class BrowserSessionInfo(TypedDict):
    session_id: str
    is_active: bool
    cookies: Dict[str, str]
    local_storage: Dict[str, str]
    navigation_history: List[str]
    open_tabs: List[str]  # List of tab IDs
    current_tab_id: Optional[str]

class TabInfo(TypedDict):
    tab_id: str
    url: str
    dom_tree: Any  # Structure representing the current DOM (could be a tree or dict of element IDs)
    loaded_resources: List[str]
    focused_element_id: Optional[str]

class DOMElementInfo(TypedDict):
    element_id: str
    tag_name: str
    attributes: Dict[str, str]
    text_content: str
    state: Dict[str, Any]  # E.g., {"visible": bool, "enabled": bool, "selected": bool}

class UserInputState(TypedDict):
    active_element_id: Optional[str]
    input_buffer: str

class AuthenticationState(TypedDict):
    is_authenticated: bool
    user_profile: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Represents a browser automation session state.
        """

        # Browser sessions: {session_id: BrowserSessionInfo}
        self.sessions: Dict[str, BrowserSessionInfo] = {}

        # Tabs (pages): {tab_id: TabInfo}
        self.tabs: Dict[str, TabInfo] = {}

        # DOM elements: {element_id: DOMElementInfo}
        self.dom_elements: Dict[str, DOMElementInfo] = {}

        # User input state per session: {session_id: UserInputState}
        self.user_input_state: Dict[str, UserInputState] = {}

        # Authentication state per session: {session_id: AuthenticationState}
        self.authentication_state: Dict[str, AuthenticationState] = {}

        # Constraints:
        # - Only authenticated sessions can access protected pages/features.
        # - DOM changes on navigation or page load.
        # - Only visible and enabled elements can be interacted with (clicked/typed).
        # - Navigation or user input may trigger DOM updates.
        # - Each tab maintains its own history and DOM state.
        # - Actions are applied only to the currently focused/open tab.

    @staticmethod
    def _gather_dom_element_ids(tree: Any) -> List[str]:
        ids: List[str] = []
        if isinstance(tree, dict):
            for key in ("element_id", "id"):
                value = tree.get(key)
                if isinstance(value, str):
                    ids.append(value)
            for value in tree.values():
                if isinstance(value, (dict, list, str)):
                    ids.extend(_GeneratedEnvImpl._gather_dom_element_ids(value))
        elif isinstance(tree, list):
            for child in tree:
                ids.extend(_GeneratedEnvImpl._gather_dom_element_ids(child))
        elif isinstance(tree, str):
            ids.append(tree)
        return ids

    def _get_tab_element_ids(
        self,
        tabinfo: Dict[str, Any],
        session: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        element_ids: List[str] = []
        seen = set()
        for eid in self._gather_dom_element_ids(tabinfo.get("dom_tree", {})):
            if eid in self.dom_elements and eid not in seen:
                element_ids.append(eid)
                seen.add(eid)
        if element_ids:
            return element_ids
        if session and len(session.get("open_tabs", [])) == 1:
            return list(self.dom_elements.keys())
        return []

    def _build_dom_tree_from_known_elements(self, url: str) -> Dict[str, Any]:
        return {
            "root": {
                "tag": "html",
                "children": [
                    {
                        "tag": "body",
                        "children": [{"element_id": eid} for eid in self.dom_elements.keys()],
                        "url_loaded": url,
                    }
                ],
            }
        }

    @staticmethod
    def _remove_element_from_dom_tree(tree: Any, target_element_id: str) -> tuple[bool, Any]:
        changed = False

        if isinstance(tree, dict):
            new_tree: Dict[str, Any] = {}
            for key, value in tree.items():
                if key == "children" and isinstance(value, list):
                    new_children = []
                    for child in value:
                        child_id = None
                        if isinstance(child, dict):
                            child_id = child.get("element_id") or child.get("id")
                        elif isinstance(child, str):
                            child_id = child
                        if child_id == target_element_id:
                            changed = True
                            continue
                        child_changed, new_child = _GeneratedEnvImpl._remove_element_from_dom_tree(child, target_element_id)
                        changed = changed or child_changed
                        new_children.append(new_child)
                    new_tree[key] = new_children
                elif isinstance(value, (dict, list)):
                    child_changed, new_value = _GeneratedEnvImpl._remove_element_from_dom_tree(value, target_element_id)
                    changed = changed or child_changed
                    new_tree[key] = new_value
                else:
                    new_tree[key] = value
            return changed, new_tree

        if isinstance(tree, list):
            new_list = []
            for child in tree:
                child_id = None
                if isinstance(child, dict):
                    child_id = child.get("element_id") or child.get("id")
                elif isinstance(child, str):
                    child_id = child
                if child_id == target_element_id:
                    changed = True
                    continue
                child_changed, new_child = _GeneratedEnvImpl._remove_element_from_dom_tree(child, target_element_id)
                changed = changed or child_changed
                new_list.append(new_child)
            return changed, new_list

        return False, tree

    def _remove_matching_elements_from_tab(
        self,
        tab: Dict[str, Any],
        session: Dict[str, Any],
        predicate,
    ) -> List[str]:
        removed: List[str] = []
        dom_tree = copy.deepcopy(tab.get("dom_tree", {}))
        for element_id in self._get_tab_element_ids(tab, session):
            info = self.dom_elements.get(element_id)
            if not info or not predicate(info):
                continue
            changed, dom_tree = self._remove_element_from_dom_tree(dom_tree, element_id)
            if changed:
                removed.append(element_id)

        if removed:
            tab["dom_tree"] = dom_tree
            if tab.get("focused_element_id") in removed:
                tab["focused_element_id"] = None

        return removed

    @staticmethod
    def _append_element_to_dom_tree(tree: Any, element_id: str) -> tuple[bool, Any]:
        if isinstance(tree, dict):
            new_tree = copy.deepcopy(tree)
            children = new_tree.get("children")
            if isinstance(children, list):
                existing_ids = set(_GeneratedEnvImpl._gather_dom_element_ids(children))
                if element_id not in existing_ids:
                    children.append({"element_id": element_id})
                return True, new_tree

            for key, value in list(new_tree.items()):
                if isinstance(value, (dict, list)):
                    appended, new_value = _GeneratedEnvImpl._append_element_to_dom_tree(value, element_id)
                    if appended:
                        new_tree[key] = new_value
                        return True, new_tree

            new_tree["children"] = [{"element_id": element_id}]
            return True, new_tree

        if isinstance(tree, list):
            new_list = copy.deepcopy(tree)
            for index, child in enumerate(new_list):
                if isinstance(child, (dict, list)):
                    appended, new_child = _GeneratedEnvImpl._append_element_to_dom_tree(child, element_id)
                    if appended:
                        new_list[index] = new_child
                        return True, new_list
            new_list.append({"element_id": element_id})
            return True, new_list

        return False, tree

    def _ensure_element_in_tab_dom(self, tab: Dict[str, Any], element_id: str) -> None:
        if element_id in self._gather_dom_element_ids(tab.get("dom_tree", {})):
            return
        appended, new_tree = self._append_element_to_dom_tree(copy.deepcopy(tab.get("dom_tree", {})), element_id)
        tab["dom_tree"] = new_tree if appended else self._build_dom_tree_from_known_elements(tab.get("url", ""))

    def _set_active_element(self, session_id: str, element_id: Optional[str]) -> None:
        if session_id not in self.user_input_state:
            self.user_input_state[session_id] = {"active_element_id": None, "input_buffer": ""}
        self.user_input_state[session_id]["active_element_id"] = element_id

    def _mark_selected_flight(self, tab: Dict[str, Any], session: Dict[str, Any], element_id: str) -> None:
        for candidate_id in self._get_tab_element_ids(tab, session):
            info = self.dom_elements.get(candidate_id)
            if not info:
                continue
            classes = info.get("attributes", {}).get("class", "")
            if "flight-option" not in classes:
                continue
            info.setdefault("state", {})["selected"] = candidate_id == element_id
        tab["selected_flight_id"] = element_id

    def _confirm_booking(self, session_id: str, session: Dict[str, Any], tab: Dict[str, Any], submit_element_id: str) -> dict:
        selected_flight_id = tab.get("selected_flight_id")
        if not selected_flight_id:
            for candidate_id in self._get_tab_element_ids(tab, session):
                info = self.dom_elements.get(candidate_id)
                if info and info.get("state", {}).get("selected"):
                    selected_flight_id = candidate_id
                    break
        if not selected_flight_id or selected_flight_id not in self.dom_elements:
            return {"success": False, "error": "No flight has been selected for booking confirmation."}

        selected_info = self.dom_elements[selected_flight_id]
        selected_info.setdefault("state", {})["confirmed"] = True

        status_element_id = "booking_status_banner"
        self.dom_elements[status_element_id] = {
            "element_id": status_element_id,
            "tag_name": "div",
            "attributes": {
                "id": "booking_status",
                "class": "booking-status confirmed",
            },
            "text_content": f"booking confirmed successfully: {selected_info.get('text_content', selected_flight_id)}",
            "state": {
                "visible": True,
                "enabled": True,
            },
        }
        self._ensure_element_in_tab_dom(tab, status_element_id)

        submit_info = self.dom_elements.get(submit_element_id)
        if submit_info:
            submit_info.setdefault("state", {})["enabled"] = False
        self._remove_matching_elements_from_tab(
            tab,
            session,
            lambda info, submit_element_id=submit_element_id: info.get("element_id") == submit_element_id,
        )
        tab["booking_status"] = {
            "confirmed": True,
            "selected_flight_id": selected_flight_id,
        }
        if session_id in self.user_input_state:
            self.user_input_state[session_id]["input_buffer"] = ""
        return {"success": True, "message": "Booking confirmed for the selected flight."}

    def _get_unique_visible_submit_button(
        self,
        tab: Dict[str, Any],
        session: Dict[str, Any],
    ) -> Optional[str]:
        candidates: List[str] = []
        for element_id in self._get_tab_element_ids(tab, session):
            info = self.dom_elements.get(element_id)
            if not info or info.get("tag_name") != "button":
                continue
            state = info.get("state", {})
            if not state.get("visible", True) or not state.get("enabled", True):
                continue
            if info.get("attributes", {}).get("type") == "submit":
                candidates.append(element_id)
        if len(candidates) == 1:
            return candidates[0]
        return None

    def _process_review_queue_action(self, tab: Dict[str, Any], session: Dict[str, Any], action: str) -> dict:
        status_element_id = "queue_status_banner"
        if action == "force_approve":
            status_text = "submission cleared from queue via admin force approve."
            status_class = "queue-status approved"
        else:
            status_text = "submission returned to author and cleared from the review queue."
            status_class = "queue-status returned"

        self.dom_elements[status_element_id] = {
            "element_id": status_element_id,
            "tag_name": "div",
            "attributes": {
                "id": "queue_status",
                "class": status_class,
            },
            "text_content": status_text,
            "state": {
                "visible": True,
                "enabled": True,
            },
        }
        self._ensure_element_in_tab_dom(tab, status_element_id)

        action_texts = {"Return to Author", "Admin Force Approve"}
        for candidate_id in self._get_tab_element_ids(tab, session):
            info = self.dom_elements.get(candidate_id)
            if not info or info.get("text_content") not in action_texts:
                continue
            info.setdefault("state", {})["enabled"] = False
            info["state"]["visible"] = False
        self._remove_matching_elements_from_tab(
            tab,
            session,
            lambda info: info.get("text_content") in action_texts,
        )
        tab["review_queue_status"] = action
        return {"success": True, "message": status_text}

    def get_active_session(self) -> dict:
        """
        Retrieves the currently active browser session.

        Returns:
            dict: {
                "success": True,
                "data": BrowserSessionInfo  # info for the active session
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. no active session)
            }

        Constraints:
            - Returns the session with is_active == True.
            - If none is active, failure with error message.
        """
        for session in self.sessions.values():
            if session.get("is_active", False):
                return {"success": True, "data": session}
        return {"success": False, "error": "No active session."}

    def get_session_authentication_state(self, session_id: str) -> dict:
        """
        Query the authentication status and user profile for the given session.

        Args:
            session_id (str): The ID of the browser session.

        Returns:
            dict: If the session exists,
                {
                    "success": True,
                    "data": {
                        "is_authenticated": bool,
                        "user_profile": dict
                    }
                }
                Otherwise,
                {
                    "success": False,
                    "error": "Session does not exist"
                }

        Constraints:
            - Session ID must exist in the environment.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }
        auth_state = self.authentication_state.get(session_id)
        if auth_state is None:
            auth_state = {
                "is_authenticated": False,
                "user_profile": {}
            }

        return {
            "success": True,
            "data": {
                "is_authenticated": auth_state["is_authenticated"],
                "user_profile": auth_state["user_profile"]
            }
        }

    def list_open_tabs(self, session_id: str) -> dict:
        """
        Get all currently open tabs (tab IDs) for the specified browser session.

        Args:
            session_id (str): The unique browser session identifier.

        Returns:
            dict:
                On success:
                    { "success": True, "data": List[str] }  # List of tab IDs (possibly empty)
                On failure:
                    { "success": False, "error": str }

        Constraints:
            - The session must exist.
            - The session should be active.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session does not exist" }
        if not session.get("is_active", False):
            return { "success": False, "error": "Session is not active" }
        open_tabs = session.get("open_tabs", [])
        return { "success": True, "data": open_tabs }

    def get_current_tab(self, session_id: str) -> dict:
        """
        Retrieve information about the current/focused tab in the given session.

        Args:
            session_id (str): The browser session identifier.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": TabInfo  # Tab information dictionary for the current/focused tab
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # Reason for failure (session not found, no tab focused, etc.)
                    }
        Constraints:
            - The given session_id must exist.
            - There must be a current_tab_id for the session.
            - The tab must exist in self.tabs.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist"}

        current_tab_id = session.get("current_tab_id")
        if not current_tab_id:
            return {"success": False, "error": "No current tab is focused/open for this session"}

        tab_info = self.tabs.get(current_tab_id)
        if not tab_info:
            return {"success": False, "error": "Current tab not found in tab records"}

        return {"success": True, "data": tab_info}

    def get_tab_info(self, tab_id: str) -> dict:
        """
        Query details of a specific tab by tab_id.

        Args:
            tab_id (str): The unique identifier of the tab.
    
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": TabInfo  # All metadata for the requested tab
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Tab not found"
                    }
        Constraints:
            - The tab_id must exist in the tabs dictionary.
        """
        tab = self.tabs.get(tab_id)
        if tab is None:
            return {"success": False, "error": "Tab not found"}
        return {"success": True, "data": tab}

    def get_dom_tree(self, tab_id: str) -> dict:
        """
        Retrieve the DOM structure for a given tab (all elements).

        Args:
            tab_id (str): The ID of the tab whose DOM structure to retrieve.

        Returns:
            dict:
                - If success: {"success": True, "data": <dom_tree>} (the tab's dom_tree data)
                - If tab is not found: {"success": False, "error": "Tab does not exist"}
    
        Constraints:
            - The provided tab_id must reference an existing tab in self.tabs.
        """
        tab_info = self.tabs.get(tab_id)
        if tab_info is None:
            return { "success": False, "error": "Tab does not exist" }

        return { "success": True, "data": tab_info["dom_tree"] }

    def find_dom_element(
        self,
        session_id: str,
        tag_name: str = None,
        attributes: Optional[dict] = None,
        text_content: str = None,
        tab_id: Optional[str] = None
    ) -> dict:
        """
        Locate DOM elements within the current DOM of the given tab/session,
        using selectors: tag_name, attributes (dict), or text_content (substring match).
        If tab_id is omitted, uses the session's currently active tab.

        Args:
            session_id (str): The session to operate within.
            tag_name (str, optional): Restrict to elements with this HTML tag.
            attributes (dict, optional): Dict of attribute key/value pairs all of which must be present (exact match).
            text_content (str, optional): Match elements where this substring appears in text_content.
            tab_id (str, optional): Operate on this tab; if omitted, use session's current tab.

        Returns:
            dict: {
                "success": True,
                "data": List[DOMElementInfo],  # matched elements
            }
            or
            {
                "success": False,
                "error": str  # Description of any error
            }

        Constraints:
            - Session ID must exist.
            - Tab must exist and be open for the session.
            - Elements are limited to those present in the tab's dom_tree.
            - If no elements found, result is an empty list (not an error).
        """
        # Validate session
        if session_id not in self.sessions:
            return {"success": False, "error": "Session does not exist"}

        session = self.sessions[session_id]
        tab_to_use = tab_id if tab_id else session.get("current_tab_id")

        if tab_to_use is None or tab_to_use not in self.tabs:
            return {"success": False, "error": "Tab does not exist or not specified for this session"}

        # Check tab_id is part of the session's open_tabs
        if tab_to_use not in session.get("open_tabs", []):
            return {"success": False, "error": "Tab is not open in this session"}

        tabinfo = self.tabs[tab_to_use]

        element_ids = self._get_tab_element_ids(tabinfo, session)

        # Now, filter elements according to selectors
        matches = []
        for eid in element_ids:
            info = self.dom_elements.get(eid)
            if not info:
                continue

            if tag_name and tag_name != "*" and info["tag_name"] != tag_name:
                continue

            if attributes:
                # All attributes in filter must exist and match
                if not all(info["attributes"].get(key) == val for key, val in attributes.items()):
                    continue
        
            if text_content:
                if text_content not in info.get("text_content", ""):
                    continue

            matches.append(info)

        return {"success": True, "data": matches}

    def get_dom_element_info(self, element_id: str) -> dict:
        """
        Retrieve the full properties and state (including visible/enabled) of a DOM element by its element_id.

        Args:
            element_id (str): The unique identifier of the DOM element.

        Returns:
            dict: {
                "success": True,
                "data": DOMElementInfo,  # Complete dictionary of the element's properties and state
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Element not found"
            }
    
        Constraints:
            - element_id must exist in self.dom_elements.
            - No permissions/authentication required to query DOM element info.
        """
        element_info = self.dom_elements.get(element_id)
        if not element_info:
            return {
                "success": False,
                "error": "Element not found"
            }
        return {
            "success": True,
            "data": element_info
        }

    def get_element_state(self, element_id: str) -> dict:
        """
        Query the visibility, enabled/disabled, and selection status of a DOM element.

        Args:
            element_id (str): The ID of the DOM element to query.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": {
                        "visible": bool (optional),
                        "enabled": bool (optional),
                        "selected": bool (optional),
                        ... # any other state flags present in the element
                    }
                }
                On failure (element not found):
                {
                    "success": False,
                    "error": "Element not found"
                }
        Constraints:
            - The element_id must exist in the DOM elements.
        """
        if element_id not in self.dom_elements:
            return {"success": False, "error": "Element not found"}

        state = self.dom_elements[element_id].get("state", {})
        # Return the state dict (could include others beyond visible/enabled/selected)
        return {"success": True, "data": state.copy()}

    def get_focused_element(self, tab_id: str) -> dict:
        """
        Identify and return the currently focused DOM element (with metadata) in the given tab.

        Args:
            tab_id (str): Identifier for the browser tab.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": DOMElementInfo | None  # Focused element info, or None if no element is focused
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error (e.g., "Tab not found", "Focused element not found")
                }

        Constraints:
            - Tab must exist.
            - If no element is focused, return data=None (not an error).
            - If focused element ID is invalid (data corruption), report as error.
        """
        tab = self.tabs.get(tab_id)
        if not tab:
            return {"success": False, "error": "Tab not found"}

        focused_element_id = tab.get("focused_element_id")
        if focused_element_id is None:
            return {"success": True, "data": None}
    
        element = self.dom_elements.get(focused_element_id)
        if not element:
            return {"success": False, "error": "Focused element not found in DOM elements"}

        return {"success": True, "data": element}

    def get_user_input_state(self, session_id: str) -> dict:
        """
        Retrieve the active input element ID and its input buffer for the provided session.

        Args:
            session_id (str): Identifier of the browser session.

        Returns:
            dict: 
                On success: { "success": True, "data": UserInputState }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - session_id must exist in self.sessions.
            - If input state is missing for a valid session, treat as error.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }
        if session_id not in self.user_input_state:
            return { "success": False, "error": "No input state for this session" }
        input_state = self.user_input_state[session_id]
        return { "success": True, "data": input_state }

    def get_navigation_history(self, session_id: str, tab_id: Optional[str] = None) -> dict:
        """
        Retrieve the navigation history (list of URLs visited) for a session, or for a specific tab.
    
        Args:
            session_id (str): The unique session ID.
            tab_id (Optional[str]): Optional tab ID. If provided, attempt to return navigation history for that tab; else, session-level history.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # The navigation history (list of URLs)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - session_id must exist.
            - If tab_id is given, it must exist and belong to the session.
            - If per-tab navigation history is not available, return session-level navigation history.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session does not exist"}

        # If tab_id is specified, check if it belongs to this session.
        if tab_id is not None:
            tab = self.tabs.get(tab_id)
            if tab is None:
                return {"success": False, "error": "Tab does not exist"}
            if tab_id not in session.get('open_tabs', []):
                return {"success": False, "error": "Tab does not belong to the given session"}
            # No per-tab navigation history is stored; fallback to returning session-level navigation_history.
            # In a real system, this would ideally look up per-tab navigation.
    
        nav_history = session.get("navigation_history", [])
        return {"success": True, "data": list(nav_history)}

    def navigate_to_url(self, session_id: str, url: str) -> dict:
        """
        Direct the browser's current tab in the given session to load the specified URL.
        This adds the URL to the navigation history, updates the current tab's URL,
        resets and simulates the DOM update for the page load.

        Args:
            session_id (str): Target browser session.
            url (str): The URL to navigate to.

        Returns:
            dict:
              - On Success:
                  {
                    "success": True,
                    "message": "Navigated to <url> in tab <tab_id>."
                  }
              - On Failure:
                  {
                    "success": False,
                    "error": "<reason>"
                  }

        Constraints:
            - Only active sessions are allowed.
            - There must be a focused (current) tab in the session.
            - Both session and tab must exist.
        """
        # Validate session
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist."}
        if not session["is_active"]:
            return {"success": False, "error": "Session is not active."}
    
        current_tab_id = session.get("current_tab_id")
        if not current_tab_id:
            return {"success": False, "error": "No current tab selected for this session."}
        tab = self.tabs.get(current_tab_id)
        if not tab:
            return {"success": False, "error": "Current tab does not exist."}
    
        # Update navigation history
        session["navigation_history"].append(url)
        # Update tab's URL
        tab["url"] = url
        tab["dom_tree"] = self._build_dom_tree_from_known_elements(url)
        tab["loaded_resources"] = []  # Would be reset/repopulated on real load
        tab["focused_element_id"] = None  # Navigation typically drops focus

        return {
            "success": True,
            "message": f"Navigated to {url} in tab {current_tab_id}."
        }

    def switch_tab(self, session_id: str, tab_id: str) -> dict:
        """
        Change the active (focused) tab within a browser session.

        Args:
            session_id (str): The session in which to switch tabs.
            tab_id (str): The tab ID to switch to.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Switched to tab <tab_id> in session <session_id>."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Session must exist and be active.
            - Tab must be among session's open tabs.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist."}
        if not session.get("is_active", False):
            return {"success": False, "error": "Session is not active."}
        open_tabs = session.get("open_tabs", [])
        if tab_id not in open_tabs:
            return {"success": False, "error": f"Tab {tab_id} is not open in session {session_id}."}
        if tab_id not in self.tabs:
            return {"success": False, "error": f"Tab {tab_id} does not exist."}

        session["current_tab_id"] = tab_id
        # Optionally, update info in self.sessions (dict is mutable so it's already updated)

        return {
            "success": True,
            "message": f"Switched to tab {tab_id} in session {session_id}."
        }

    def open_new_tab(self, session_id: str, url: str = "") -> dict:
        """
        Open a new tab in the specified session, optionally navigating to a URL, and set it as the active tab.

        Args:
            session_id (str): The browser session in which to open the new tab.
            url (str, optional): The URL for the tab to navigate to. If not provided or empty, opens a blank tab.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Tab opened with id <tab_id>", "tab_id": <tab_id> }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - session_id must exist and be active.
            - The new tab_id must be unique and added to the session's open_tabs.
            - The session's current_tab_id must be set to the new tab_id.
        """
        # Check session exists and is active
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session does not exist" }
        if not session["is_active"]:
            return { "success": False, "error": "Session is not active" }

        # Generate unique tab_id
        base_tab_id = f"tab_{len(self.tabs) + 1}"
        tab_id = base_tab_id
        idx = 1
        while tab_id in self.tabs:
            idx += 1
            tab_id = f"{base_tab_id}_{idx}"

        dom_tree = {}
        if url:
            for existing_tab in self.tabs.values():
                if existing_tab.get("url") == url:
                    dom_tree = copy.deepcopy(existing_tab.get("dom_tree", {}))
                    break

        # Create the new TabInfo
        tab_info = {
            "tab_id": tab_id,
            "url": url if url else "",
            "dom_tree": dom_tree,
            "loaded_resources": [],
            "focused_element_id": None
        }
        self.tabs[tab_id] = tab_info

        # Update session's open_tabs and current_tab_id
        session["open_tabs"].append(tab_id)
        session["current_tab_id"] = tab_id

        # Save session
        self.sessions[session_id] = session

        return {
            "success": True,
            "message": f"Tab opened with id {tab_id}",
            "tab_id": tab_id
        }

    def close_tab(self, session_id: str, tab_id: str) -> dict:
        """
        Close a specified tab for a browser session and adjust the current_tab_id accordingly.

        Args:
            session_id (str): The ID of the browser session.
            tab_id (str): The ID of the tab to close.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Tab <tab_id> closed for session <session_id>."
                }
                OR
                {
                    "success": False,
                    "error": <description>
                }

        Constraints:
            - The session must exist and be active.
            - The tab must exist and belong to the session's open tabs.
            - If closing the current tab, the current_tab_id moves to the most recent tab, or is set to None if no tabs remain.
        """
        # Session validation
        session = self.sessions.get(session_id)
        if not session or not session.get("is_active", False):
            return { "success": False, "error": "Session does not exist or is not active." }
    
        open_tabs = session.get("open_tabs", [])
        if tab_id not in open_tabs:
            return { "success": False, "error": f"Tab {tab_id} is not open in session {session_id}." }
    
        # Remove tab from session
        open_tabs = [tid for tid in open_tabs if tid != tab_id]
        session["open_tabs"] = open_tabs

        # Remove from tab registry
        if tab_id in self.tabs:
            del self.tabs[tab_id]

        # Adjust current_tab_id if needed
        if session.get("current_tab_id") == tab_id:
            if open_tabs:
                session["current_tab_id"] = open_tabs[-1]  # Last opened/remaining tab becomes current
            else:
                session["current_tab_id"] = None

        # Save the modifications back (dict reference should suffice but to be explicit)
        self.sessions[session_id] = session

        return {
            "success": True,
            "message": f"Tab {tab_id} closed for session {session_id}."
        }

    def focus_dom_element(self, session_id: str, element_id: str) -> dict:
        """
        Set a specific DOM element as the focused/active element for input or interaction in a browser session.

        Args:
            session_id (str): The session performing the focus action.
            element_id (str): The ID of the DOM element to focus.

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - message (str): Success message (if success).
                - error (str): Error message (if failure).

        Constraints:
            - Session must exist and be active.
            - There must be a current tab in the session.
            - Element must exist in dom_elements.
            - Element must be visible and enabled.
            - Updates both the tab's focused_element_id and the session's UserInputState.active_element_id.
        """
        # 1. Check session existence and activity
        session = self.sessions.get(session_id)
        if not session or not session.get("is_active"):
            return {"success": False, "error": "Session does not exist or is inactive."}

        # 2. Get current tab
        tab_id = session.get("current_tab_id")
        if not tab_id or tab_id not in self.tabs:
            return {"success": False, "error": "No current tab is set for this session."}

        tab = self.tabs.get(tab_id)
        if not tab:
            return {"success": False, "error": "Current tab does not exist."}

        # 3. Validate DOM element
        element = self.dom_elements.get(element_id)
        if not element:
            return {"success": False, "error": f"DOM element {element_id} does not exist."}

        state = element.get("state", {})
        if not state.get("visible", False):
            return {"success": False, "error": "Element is not visible and cannot be focused."}
        if not state.get("enabled", False):
            return {"success": False, "error": "Element is not enabled and cannot be focused."}

        # 4. Update tab's focused element
        tab["focused_element_id"] = element_id

        # 5. Update user input state
        if session_id not in self.user_input_state:
            self.user_input_state[session_id] = {"active_element_id": None, "input_buffer": ""}
        self.user_input_state[session_id]["active_element_id"] = element_id

        # 6. Commit changes to tab data store
        self.tabs[tab_id] = tab

        return {
            "success": True,
            "message": f"Element {element_id} is now focused in session {session_id} (tab {tab_id})."
        }

    def click_element(self, session_id: str, element_id: str) -> dict:
        """
        Perform a click action on a visible and enabled DOM element within the currently focused/open tab of the session.
    
        Args:
            session_id (str): The ID of the browser session.
            element_id (str): The ID of the DOM element to click.
    
        Returns:
            dict: 
                On success: { "success": True, "message": "Clicked element <element_id>" }
                On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - session must exist and be active.
            - click is applied only to the current tab of the session.
            - element must exist, belong to the DOM of the current tab, and be visible and enabled.
        """
        # Check session
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session does not exist." }
        if not session["is_active"]:
            return { "success": False, "error": "Session is not active." }
        current_tab_id = session.get('current_tab_id')
        if not current_tab_id:
            return { "success": False, "error": "No tab is currently focused/open in the session." }
        tab = self.tabs.get(current_tab_id)
        if not tab:
            return { "success": False, "error": "Current tab does not exist." }
        # Simple inclusion: Check element is in dom_elements (simulating global DOM registry)
        element = self.dom_elements.get(element_id)
        if not element:
            return { "success": False, "error": f"DOM element {element_id} does not exist." }

        if element_id not in self._get_tab_element_ids(tab, session):
            return { "success": False, "error": "Element does not belong to the current tab DOM." }

        state = element.get("state", {})
        if not state.get("visible", False):
            return { "success": False, "error": "Element is not visible and cannot be clicked." }
        if not state.get("enabled", False):
            return { "success": False, "error": "Element is not enabled and cannot be clicked." }

        # Simulate focus change
        tab["focused_element_id"] = element_id
        self._set_active_element(session_id, element_id)

        href = element.get("attributes", {}).get("href")
        if element.get("tag_name") == "a" and isinstance(href, str) and href:
            resolved_url = urljoin(tab.get("url", ""), href)
            session["navigation_history"].append(resolved_url)
            tab["url"] = resolved_url
            tab["dom_tree"] = self._build_dom_tree_from_known_elements(resolved_url)
            tab["loaded_resources"] = []
            tab["focused_element_id"] = None
            self._set_active_element(session_id, None)

        classes = element.get("attributes", {}).get("class", "")
        text = element.get("text_content", "")
        if "flight-option" in classes:
            self._mark_selected_flight(tab, session, element_id)

        if element.get("tag_name") == "button":
            if element.get("attributes", {}).get("type") == "submit" or text == "Confirm Booking":
                booking_result = self._confirm_booking(session_id, session, tab, element_id)
                if not booking_result.get("success"):
                    return booking_result
            elif text == "Admin Force Approve":
                queue_result = self._process_review_queue_action(tab, session, "force_approve")
                if not queue_result.get("success"):
                    return queue_result
            elif text == "Return to Author":
                queue_result = self._process_review_queue_action(tab, session, "return_to_author")
                if not queue_result.get("success"):
                    return queue_result

        return { "success": True, "message": f"Clicked element {element_id}" }

    def type_in_element(
        self,
        session_id: str,
        text: str,
        element_id: str = None
    ) -> dict:
        """
        Enter text into the currently focused or specified input element in the browser session.

        Args:
            session_id (str): The session in which to enter text.
            text (str): The text to type into the element.
            element_id (str, optional): The ID of the element to type into. If not provided, will use the currently focused element for the current tab.

        Returns:
            dict: {
                "success": True,
                "message": "Typed text into element <id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only visible and enabled elements can be interacted with.
            - Must be associated with an active session and current tab.
            - Element must exist in the DOM.
        """

        # Check if session exists and is active
        session = self.sessions.get(session_id)
        if not session or not session['is_active']:
            return {"success": False, "error": "Session does not exist or is not active"}

        # Get current tab of the session
        current_tab_id = session.get("current_tab_id")
        if not current_tab_id or current_tab_id not in self.tabs:
            return {"success": False, "error": "No active tab for this session"}

        tab = self.tabs[current_tab_id]

        # Determine target element
        target_element_id = element_id
        if not target_element_id:
            # Check tab's focused element, then fallback to user input state
            target_element_id = tab.get('focused_element_id')
            if not target_element_id:
                user_input = self.user_input_state.get(session_id, {})
                target_element_id = user_input.get('active_element_id')
            if not target_element_id:
                return {"success": False, "error": "No element specified or focused for typing"}

        # Check if the element exists
        element = self.dom_elements.get(target_element_id)
        if not element:
            return {"success": False, "error": f"Element {target_element_id} does not exist in the DOM"}

        # Check if the element is part of the current tab's dom_tree (not strictly implementable here, but should be checked in a full implementation)

        # Enforce interaction constraints: visible and enabled
        state = element.get('state', {})
        if not state.get("visible", True):
            return {"success": False, "error": "Element is not visible"}
        if not state.get("enabled", True):
            return {"success": False, "error": "Element is not enabled"}

        # Optionally check for input/text/contenteditable (could check element['tag_name'])
        # Here we assume any element can receive input (or further refine as desired)

        # Update focus and UserInputState for the session
        tab["focused_element_id"] = target_element_id
        if session_id not in self.user_input_state:
            self.user_input_state[session_id] = {"active_element_id": target_element_id, "input_buffer": ""}
        else:
            self.user_input_state[session_id]["active_element_id"] = target_element_id

        # Append to input buffer
        existing_buffer = self.user_input_state[session_id].get("input_buffer", "")
        self.user_input_state[session_id]["input_buffer"] = existing_buffer + text

        return {"success": True, "message": f"Typed text into element {target_element_id}."}

    def clear_input_buffer(self, session_id: str) -> dict:
        """
        Erase the contents of the active input buffer for the focused element in the given session.

        Args:
            session_id (str): The session in which to clear the input buffer.

        Returns:
            dict: {
                "success": True,
                "message": "Input buffer cleared for session <session_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - session_id must exist in self.sessions
            - UserInputState must exist for this session
            - If input_buffer is already empty, operation is still considered success
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session not found" }
        if session_id not in self.user_input_state:
            return { "success": False, "error": "User input state not found for session" }

        self.user_input_state[session_id]['input_buffer'] = ""
        return { "success": True, "message": f"Input buffer cleared for session {session_id}" }

    def submit_form(self, session_id: str) -> dict:
        """
        Simulate pressing "Enter" or submitting a form for the currently active (focused) input element in the session.

        Args:
            session_id (str): The ID of the browser session.

        Returns:
            dict: Result of the submit operation. 
            On success: 
                {"success": True, "message": "Form submitted for input element <element_id>."}
            On failure:
                {"success": False, "error": <reason>}
    
        Constraints:
            - Session must exist and be active.
            - There must be an open current tab.
            - There must be an active/focused input element for this session.
            - Element must be visible and enabled.
            - Input buffer (contents) is submitted and then cleared.
        """
        session = self.sessions.get(session_id)
        if not session or not session['is_active']:
            return {"success": False, "error": "Session does not exist or is not active."}

        current_tab_id = session.get('current_tab_id')
        if not current_tab_id or current_tab_id not in self.tabs:
            return {"success": False, "error": "No current tab is open in this session."}

        tab = self.tabs[current_tab_id]
        input_state = self.user_input_state.get(session_id)
        if not input_state or not input_state.get('active_element_id'):
            return {"success": False, "error": "No active input element to submit form for."}

        element_id = input_state['active_element_id']
        element = self.dom_elements.get(element_id)
        if not element:
            return {"success": False, "error": "Focused element does not exist in DOM."}

        # Check element type and interactability
        tag = element.get('tag_name', '').lower()
        if tag == 'button':
            text = element.get("text_content", "")
            if element.get("attributes", {}).get("type") == "submit" or text == "Confirm Booking":
                return self._confirm_booking(session_id, session, tab, element_id)
            if text == "Admin Force Approve":
                return self._process_review_queue_action(tab, session, "force_approve")
            if text == "Return to Author":
                return self._process_review_queue_action(tab, session, "return_to_author")
            submit_button_id = self._get_unique_visible_submit_button(tab, session)
            if submit_button_id and submit_button_id != element_id:
                submit_button = self.dom_elements.get(submit_button_id, {})
                submit_text = submit_button.get("text_content", "")
                if submit_button.get("attributes", {}).get("type") == "submit" or submit_text == "Confirm Booking":
                    return self._confirm_booking(session_id, session, tab, submit_button_id)
            return {"success": False, "error": "Active element is not a submittable control."}
        if tag not in ('input', 'textarea', 'select'):
            return {"success": False, "error": "Active element is not a submittable input/textarea/select."}

        state = element.get('state', {})
        if not state.get('visible', True):
            return {"success": False, "error": "Cannot submit: element is not visible."}
        if not state.get('enabled', True):
            return {"success": False, "error": "Cannot submit: element is not enabled."}

        # For simulation: clear input buffer after submit
        submitted_value = input_state.get('input_buffer', '')
        self.user_input_state[session_id]['input_buffer'] = ''
        # (DOM/form-update logic could be extended here as needed)

        return {
            "success": True,
            "message": f"Form submitted for input element {element_id} with value '{submitted_value}'."
        }

    def login(self, session_id: str, username: str, password: str) -> dict:
        """
        Perform a login action for the given session with the provided credentials.
        Updates AuthenticationState and sets a session cookie if login is successful.

        Args:
            session_id (str): The ID of the browser session.
            username (str): The user's username (non-empty).
            password (str): The user's password (non-empty).

        Returns:
            dict: 
                On success: 
                    { "success": True, "message": "Login successful." }
                On failure: 
                    { "success": False, "error": "<reason>" }

        Constraints:
            - session_id must exist and be active.
            - username and password must be non-empty.
        """
        session = self.sessions.get(session_id)
        if not session or not session.get("is_active", False):
            return { "success": False, "error": "Session does not exist or is not active." }

        if not username or not password:
            return { "success": False, "error": "Username and password must be provided and non-empty." }

        # Get or create AuthenticationState for this session
        auth_state = self.authentication_state.get(session_id)
        if auth_state is not None and auth_state.get("is_authenticated", False):
            # Already authenticated, treat as idempotent success
            return { "success": True, "message": "Login successful." }

        # Simulate successful login for any non-empty user/password
        self.authentication_state[session_id] = {
            "is_authenticated": True,
            "user_profile": { "username": username }
        }

        # Update session cookies to reflect 'login'
        session_cookies = session.get("cookies", {})
        session_cookies["auth_token"] = f"{session_id}_{username}"
        session["cookies"] = session_cookies

        return { "success": True, "message": "Login successful." }

    def execute_js_on_page(self, session_id: str, script: str) -> dict:
        """
        Simulate executing arbitrary JavaScript code in the context of the current tab for a session.
        This may mutate the DOM or tab state in the simulation.

        Args:
            session_id (str): Session identifier.
            script (str): The JavaScript code to 'execute'.

        Returns:
            dict:
              - On success: { "success": True, "message": "JavaScript executed on current tab" }
              - On error: { "success": False, "error": <reason> }

        Constraints:
          - Session must exist and be active.
          - There must be a current tab, and tab must exist.
          - Only mutates the currently focused/open tab.
          - If script is empty, treat as successful no-op.

        Notes:
          - Actual JS code execution is not realized; instead, for simulation, 
            the tab's dom_tree (or an associated field) can be updated to reflect JS execution.
        """
        # Verify session exists and is active
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session does not exist" }
        if not session["is_active"]:
            return { "success": False, "error": "Session is not active" }
        current_tab_id = session.get("current_tab_id")
        if not current_tab_id:
            return { "success": False, "error": "No current tab open in session" }
        tab = self.tabs.get(current_tab_id)
        if not tab:
            return { "success": False, "error": "Current tab does not exist" }
        # If script is empty or just whitespace, treat as succeed (no-op)
        if script is None or script.strip() == "":
            # Optionally could log the "no-op" execution
            return { "success": True, "message": "No JavaScript executed (empty script)" }
        # Simulate JS execution (in this simulation: record last executed JS)
        tab["last_js_executed"] = script
        # Optionally, can mutate dom_tree in a visible way for tracking
        if isinstance(tab.get("dom_tree"), dict):
            tab["dom_tree"]["__js_executed"] = tab["dom_tree"].get("__js_executed", [])
            tab["dom_tree"]["__js_executed"].append(script)

        removed_element_ids: List[str] = []
        id_patterns = [
            r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)\.remove\(\s*\)",
            r"querySelector\(\s*['\"]#([^'\"]+)['\"]\s*\)\.remove\(\s*\)",
        ]
        for pattern in id_patterns:
            for dom_id in re.findall(pattern, script):
                removed_element_ids.extend(
                    self._remove_matching_elements_from_tab(
                        tab,
                        session,
                        lambda info, dom_id=dom_id: (
                            info.get("element_id") == dom_id
                            or info.get("attributes", {}).get("id") == dom_id
                        ),
                    )
                )

        if "removeChild" in script or ".remove(" in script:
            for tag_name in re.findall(r"getElementsByTagName\(\s*['\"]([^'\"]+)['\"]\s*\)", script):
                removed_element_ids.extend(
                    self._remove_matching_elements_from_tab(
                        tab,
                        session,
                        lambda info, tag_name=tag_name: info.get("tag_name") == tag_name,
                    )
                )

        enabled_targets = set()
        for pattern in [
            r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)\.removeAttribute\(\s*['\"]disabled['\"]\s*\)",
            r"querySelector\(\s*['\"]#([^'\"]+)['\"]\s*\)\.removeAttribute\(\s*['\"]disabled['\"]\s*\)",
            r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)\.disabled\s*=\s*false",
            r"querySelector\(\s*['\"]#([^'\"]+)['\"]\s*\)\.disabled\s*=\s*false",
        ]:
            enabled_targets.update(re.findall(pattern, script))

        for dom_id in enabled_targets:
            for info in self.dom_elements.values():
                if info.get("element_id") != dom_id and info.get("attributes", {}).get("id") != dom_id:
                    continue
                info.get("attributes", {}).pop("disabled", None)
                info.setdefault("state", {})["enabled"] = True

        if removed_element_ids and session_id in self.user_input_state:
            active_element_id = self.user_input_state[session_id].get("active_element_id")
            if active_element_id in removed_element_ids:
                self.user_input_state[session_id]["active_element_id"] = None
        return { "success": True, "message": "JavaScript executed on current tab" }

    def update_dom(self, session_id: str, new_dom_tree: Any) -> dict:
        """
        Directly update or patch the DOM tree for the currently focused/open tab in the given session.

        Args:
            session_id (str): The ID of the browser session.
            new_dom_tree (Any): The new DOM tree structure to set for the current tab.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "DOM updated for current tab."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Session must exist and be active.
            - There must be a current tab set for the session, and it must exist.
            - Only affects the current tab for the session.
            - No validation of the "correctness" of new_dom_tree structure is performed here.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session does not exist"}
        if not session.get("is_active", False):
            return {"success": False, "error": "Session is not active"}
        current_tab_id = session.get("current_tab_id")
        if not current_tab_id:
            return {"success": False, "error": "No current tab set for this session"}
        tab = self.tabs.get(current_tab_id)
        if tab is None:
            return {"success": False, "error": "Current tab does not exist"}
        tab["dom_tree"] = new_dom_tree
        # Optionally, could clear/fix dom_elements map if required, but not specified
        return {"success": True, "message": "DOM updated for current tab."}

    def set_cookie(self, session_id: str, cookie_name: str, cookie_value: str) -> dict:
        """
        Set or update a cookie for the specified browser session.

        Args:
            session_id (str): The session ID to set the cookie in.
            cookie_name (str): The name of the cookie.
            cookie_value (str): The value to set for the cookie.

        Returns:
            dict: 
              - On success: {"success": True, "message": "Cookie set/updated for session <session_id>."}
              - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Session must exist and be active.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist."}
        if not session.get("is_active", False):
            return {"success": False, "error": "Session is not active."}

        # Set or update the cookie
        session["cookies"][cookie_name] = cookie_value
        return {"success": True, "message": f"Cookie set/updated for session {session_id}."}

    def set_local_storage(self, session_id: str, key: str, value: str) -> dict:
        """
        Sets a key-value pair in the local storage of the specified browser session.

        Args:
            session_id (str): Identifier for the browser session.
            key (str): Local storage key to set (must be non-empty string).
            value (str): Value to associate with the key.

        Returns:
            dict: {
                "success": True,
                "message": "Local storage key set."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - session_id must exist in self.sessions.
            - Session must be active.
            - key must be a non-empty string.
            - value must be a string.
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist." }

        session = self.sessions[session_id]
        if not session["is_active"]:
            return { "success": False, "error": "Session is not active." }

        if not isinstance(key, str) or key == "":
            return { "success": False, "error": "Key must be a non-empty string." }
        if not isinstance(value, str):
            return { "success": False, "error": "Value must be a string." }

        session["local_storage"][key] = value
        return { "success": True, "message": "Local storage key set." }

    def logout(self) -> dict:
        """
        End the current authentication session.
        Clears AuthenticationState (is_authenticated=False, user_profile={}) and clears authentication-related cookies in the active session.

        Returns:
            dict: {
                "success": True,
                "message": "Logged out successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Applies to the currently active session only.
            - If no active session exists, returns error.
            - If not currently authenticated, still clears authentication and returns success.
        """
        # Find active session
        active_session_id = None
        for session_id, info in self.sessions.items():
            if info.get("is_active"):
                active_session_id = session_id
                break

        if not active_session_id:
            return { "success": False, "error": "No active session found" }

        # Clear AuthenticationState
        if active_session_id not in self.authentication_state:
            # Defensive; create if absent
            self.authentication_state[active_session_id] = {
                "is_authenticated": False,
                "user_profile": {}
            }
        else:
            self.authentication_state[active_session_id]["is_authenticated"] = False
            self.authentication_state[active_session_id]["user_profile"] = {}

        # Clear authentication-related cookies (heuristic: cookies with "auth" or "session" in name)
        auth_cookies = []
        cookies = self.sessions[active_session_id].get("cookies", {})
        for cookie_name in list(cookies.keys()):
            lower_name = cookie_name.lower()
            if "auth" in lower_name or "session" in lower_name:
                del cookies[cookie_name]
                auth_cookies.append(cookie_name)
        self.sessions[active_session_id]["cookies"] = cookies

        return { "success": True, "message": "Logged out successfully" }


class BrowserAutomationSession(BaseEnv):
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

    def get_active_session(self, **kwargs):
        return self._call_inner_tool('get_active_session', kwargs)

    def get_session_authentication_state(self, **kwargs):
        return self._call_inner_tool('get_session_authentication_state', kwargs)

    def list_open_tabs(self, **kwargs):
        return self._call_inner_tool('list_open_tabs', kwargs)

    def get_current_tab(self, **kwargs):
        return self._call_inner_tool('get_current_tab', kwargs)

    def get_tab_info(self, **kwargs):
        return self._call_inner_tool('get_tab_info', kwargs)

    def get_dom_tree(self, **kwargs):
        return self._call_inner_tool('get_dom_tree', kwargs)

    def find_dom_element(self, **kwargs):
        return self._call_inner_tool('find_dom_element', kwargs)

    def get_dom_element_info(self, **kwargs):
        return self._call_inner_tool('get_dom_element_info', kwargs)

    def get_element_state(self, **kwargs):
        return self._call_inner_tool('get_element_state', kwargs)

    def get_focused_element(self, **kwargs):
        return self._call_inner_tool('get_focused_element', kwargs)

    def get_user_input_state(self, **kwargs):
        return self._call_inner_tool('get_user_input_state', kwargs)

    def get_navigation_history(self, **kwargs):
        return self._call_inner_tool('get_navigation_history', kwargs)

    def navigate_to_url(self, **kwargs):
        return self._call_inner_tool('navigate_to_url', kwargs)

    def switch_tab(self, **kwargs):
        return self._call_inner_tool('switch_tab', kwargs)

    def open_new_tab(self, **kwargs):
        return self._call_inner_tool('open_new_tab', kwargs)

    def close_tab(self, **kwargs):
        return self._call_inner_tool('close_tab', kwargs)

    def focus_dom_element(self, **kwargs):
        return self._call_inner_tool('focus_dom_element', kwargs)

    def click_element(self, **kwargs):
        return self._call_inner_tool('click_element', kwargs)

    def type_in_element(self, **kwargs):
        return self._call_inner_tool('type_in_element', kwargs)

    def clear_input_buffer(self, **kwargs):
        return self._call_inner_tool('clear_input_buffer', kwargs)

    def submit_form(self, **kwargs):
        return self._call_inner_tool('submit_form', kwargs)

    def login(self, **kwargs):
        return self._call_inner_tool('login', kwargs)

    def execute_js_on_page(self, **kwargs):
        return self._call_inner_tool('execute_js_on_page', kwargs)

    def update_dom(self, **kwargs):
        return self._call_inner_tool('update_dom', kwargs)

    def set_cookie(self, **kwargs):
        return self._call_inner_tool('set_cookie', kwargs)

    def set_local_storage(self, **kwargs):
        return self._call_inner_tool('set_local_storage', kwargs)

    def logout(self, **kwargs):
        return self._call_inner_tool('logout', kwargs)
