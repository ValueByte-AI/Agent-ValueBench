# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class BotInfo(TypedDict):
    bot_id: str
    name: str
    metadata: dict
    configuration: dict

class ClientInfo(TypedDict):
    client_id: str
    name: str
    organization: str
    contact_info: str

class ChatSessionInfo(TypedDict):
    session_id: str
    bot_id: str
    client_id: str
    start_time: str
    end_time: str
    transcript: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Persistent environment for managing chatbots, client accounts, and chat sessions.
        """

        # Bots: {bot_id: BotInfo}
        self.bots: Dict[str, BotInfo] = {}

        # Clients: {client_id: ClientInfo}
        self.clients: Dict[str, ClientInfo] = {}

        # Chat Sessions: {session_id: ChatSessionInfo}
        self.sessions: Dict[str, ChatSessionInfo] = {}

        # Constraints:
        # - Every ChatSession must be associated with a valid bot_id and client_id.
        # - Bot profiles (bot_id) are unique; bot names may not be unique.
        # - Client identifiers are unique; a client may interact with multiple bots.
        # - Chat transcripts must be retained for historical and auditing purposes.
        # - Session filtering supports queries by both bot and client.

    def get_bot_by_id(self, bot_id: str) -> dict:
        """
        Retrieve complete details (metadata, configuration, and identity fields) for a bot using its unique bot_id.

        Args:
            bot_id (str): The unique identifier for the bot.

        Returns:
            dict: {
                "success": True,
                "data": BotInfo,  # Complete information for the bot
            }
            or
            {
                "success": False,
                "error": str  # If the bot_id does not exist
            }
        Constraints:
            - bot_id must be unique and present in the system.
        """
        bot = self.bots.get(bot_id)
        if not bot:
            return { "success": False, "error": "Bot not found" }
        return { "success": True, "data": bot }

    def get_bots_by_name(self, name: str) -> dict:
        """
        Retrieve all bot metadata whose names exactly match a given string.

        Args:
            name (str): The bot name to match (case-sensitive, exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[BotInfo]   # List of bots with the matching name; may be empty if no matches
            }
            or
            {
                "success": False,
                "error": str            # Description of the error (e.g., invalid input)
            }

        Constraints:
            - Bot names are not unique; may return multiple bots.
            - Input `name` must be a non-empty string.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Invalid 'name' parameter; must be a non-empty string."}

        matching_bots = [
            bot_info for bot_info in self.bots.values()
            if bot_info["name"] == name
        ]
        return {"success": True, "data": matching_bots}

    def list_all_bots(self) -> dict:
        """
        List all chatbot profiles and their metadata on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BotInfo],  # List of all bots (may be empty if none exist)
            }
        Constraints:
            - None. All bots in the system are included.
        """
        bots_list = list(self.bots.values())
        return { "success": True, "data": bots_list }

    def get_client_by_id(self, client_id: str) -> dict:
        """
        Retrieve complete client details by client_id.

        Args:
            client_id (str): The unique identifier for the client.

        Returns:
            dict: {
                "success": True,
                "data": ClientInfo  # Client information dictionary
            }
            or
            {
                "success": False,
                "error": str  # Description if client not found
            }

        Constraints:
            - The provided client_id must exist in the platform's clients.
        """
        client_info = self.clients.get(client_id)
        if client_info is None:
            return {"success": False, "error": "Client with given client_id does not exist."}
        return {"success": True, "data": client_info}

    def get_clients_by_name(self, name: str) -> dict:
        """
        Retrieve all client(s) whose name exactly matches the provided string.
    
        Args:
            name (str): The name of the client(s) to match (exact).
    
        Returns:
            dict: {
                "success": True,
                "data": List[ClientInfo]  # List of all clients with the matching name, can be empty
            }
        """
        result = [
            client_info for client_info in self.clients.values()
            if client_info["name"] == name
        ]
        return { "success": True, "data": result }

    def get_clients_by_organization(self, organization: str) -> dict:
        """
        Fetch all clients whose 'organization' attribute matches the specified string.

        Args:
            organization (str): The organization name to filter clients by.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[ClientInfo],  # All clients with matching organization (may be empty)
                }
    
        Notes:
            - This is a filter; no error is reported if there are no matches.
            - Client 'organization' matching is case-sensitive (exact match).
        """
        matching_clients = [
            client for client in self.clients.values()
            if client["organization"] == organization
        ]
        return {"success": True, "data": matching_clients}

    def list_all_clients(self) -> dict:
        """
        List all client accounts and their associated details.

        Returns:
            dict: {
                "success": True,
                "data": List[ClientInfo]  # All client profiles (may be empty if none registered)
            }
        """
        client_list = list(self.clients.values())
        return { "success": True, "data": client_list }

    def get_session_by_id(self, session_id: str) -> dict:
        """
        Fetch full information (including transcript) for a chat session given its session_id.

        Args:
            session_id (str): The unique identifier of the chat session.

        Returns:
            dict:
                On success: { "success": True, "data": ChatSessionInfo }
                On failure: { "success": False, "error": "Session not found" }

        Constraints:
            - session_id must exist in the platform.
        """
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session not found" }
        return { "success": True, "data": session }

    def get_sessions_by_bot_id(self, bot_id: str) -> dict:
        """
        Retrieve all chat sessions associated with a particular bot (by bot_id).

        Args:
            bot_id (str): The unique identifier of the bot.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[ChatSessionInfo],  # List of sessions (may be empty)
                }
                On failure: {
                    "success": False,
                    "error": str  # e.g., "Bot not found"
                }

        Constraints:
            - bot_id must exist in self.bots.
        """
        if bot_id not in self.bots:
            return { "success": False, "error": "Bot not found" }

        sessions = [
            session_info for session_info in self.sessions.values()
            if session_info["bot_id"] == bot_id
        ]
        return { "success": True, "data": sessions }

    def get_sessions_by_client_id(self, client_id: str) -> dict:
        """
        Retrieve all chat sessions involving a particular client (by client_id).

        Args:
            client_id (str): The unique identifier for the client.

        Returns:
            dict: {
                "success": True,
                "data": List[ChatSessionInfo],  # May be empty if no sessions for this client.
            }
            or
            {
                "success": False,
                "error": str  # Error message if client_id not found.
            }
    
        Constraints:
            - client_id must exist on the platform.
            - Every ChatSession returned is guaranteed to have a valid client_id.
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client not found" }

        sessions = [
            session_info for session_info in self.sessions.values()
            if session_info["client_id"] == client_id
        ]
        return { "success": True, "data": sessions }

    def get_sessions_by_bot_and_client(self, bot_id: str, client_id: str) -> dict:
        """
        Retrieve all chat sessions involving a specific bot and client.

        Args:
            bot_id (str): Unique identifier of the bot.
            client_id (str): Unique identifier of the client.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ChatSessionInfo]  # All chat sessions where both IDs match.
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure: missing bot or client.
                }

        Constraints:
            - `bot_id` must exist in the platform.
            - `client_id` must exist in the platform.
            - Returns all matching sessions (may be an empty list).
        """
        if bot_id not in self.bots:
            return {"success": False, "error": "Bot not found"}
        if client_id not in self.clients:
            return {"success": False, "error": "Client not found"}

        result = [
            session for session in self.sessions.values()
            if session['bot_id'] == bot_id and session['client_id'] == client_id
        ]
        return {"success": True, "data": result}

    def get_sessions_by_bot_name_and_client_name(self, bot_name: str, client_name: str) -> dict:
        """
        Retrieve all chat sessions involving bots with the given name and clients with the given name.
        If names are not unique, sessions involving any matching bot and any matching client are included.

        Args:
            bot_name (str): Name of the bot(s)
            client_name (str): Name of the client(s)

        Returns:
            dict: {
                "success": True,
                "data": List[ChatSessionInfo],  # May be empty if no matched sessions
            }

        Notes:
            - Bot and client names are not unique; matches all bots/clients with the given names.
            - No error if no such bot/client is found (returns empty list).
        """
        # Find all bot_ids for bots whose name equals bot_name
        matching_bot_ids = {bot["bot_id"] for bot in self.bots.values() if bot["name"] == bot_name}
        # Find all client_ids for clients whose name equals client_name
        matching_client_ids = {client["client_id"] for client in self.clients.values() if client["name"] == client_name}

        # Find all sessions where both bot_id and client_id match
        result = [
            session for session in self.sessions.values()
            if session["bot_id"] in matching_bot_ids and session["client_id"] in matching_client_ids
        ]

        return {
            "success": True,
            "data": result
        }

    def get_session_transcript(self, session_id: str) -> dict:
        """
        Retrieve the chat transcript for a given session_id.

        Args:
            session_id (str): The unique identifier of the chat session.

        Returns:
            dict: {
                "success": True,
                "data": str  # The transcript of the session (possibly empty if no messages)
            }
            or
            {
                "success": False,
                "error": str  # Description of why retrieval failed (e.g. session_id not found)
            }

        Constraints:
            - session_id must refer to an existing ChatSession.
            - Chat transcripts are always present for a valid session (may be empty).
        """
        session = self.sessions.get(session_id)
        if session is None:
            return { "success": False, "error": "Session ID does not exist" }
        return { "success": True, "data": session["transcript"] }

    def filter_sessions_by_time_range(
        self,
        start_time: str,
        end_time: str,
        bot_id: str = None,
        client_id: str = None
    ) -> dict:
        """
        List chat sessions that occurred within (overlapping) the specified time interval.
        Optionally filter by bot_id and/or client_id.

        Args:
            start_time (str): Lower bound (inclusive) for session times (ISO format string).
            end_time (str): Upper bound (inclusive) for session times (ISO format string).
            bot_id (str, optional): If set, only sessions for this bot.
            client_id (str, optional): If set, only sessions for this client.

        Returns:
            dict: {
                "success": True,
                "data": List[ChatSessionInfo]  # Matching chat sessions
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - start_time must not be greater than end_time.
            - If specified, bot_id/client_id must exist.
            - Sessions are returned if their [start_time, end_time] overlap with the query interval.
        """
        # Check that start_time <= end_time
        if start_time > end_time:
            return { "success": False, "error": "start_time cannot be after end_time" }

        # Validate bot_id and client_id if given
        if bot_id is not None and bot_id not in self.bots:
            return { "success": False, "error": f"bot_id '{bot_id}' does not exist" }
        if client_id is not None and client_id not in self.clients:
            return { "success": False, "error": f"client_id '{client_id}' does not exist" }

        result = []
        for session in self.sessions.values():
            sess_start = session["start_time"]
            sess_end = session["end_time"]
            # Overlap if: sess_start <= end_time and sess_end >= start_time
            if sess_start <= end_time and sess_end >= start_time:
                if bot_id is not None and session["bot_id"] != bot_id:
                    continue
                if client_id is not None and session["client_id"] != client_id:
                    continue
                result.append(session)

        return { "success": True, "data": result }

    def get_session_count_by_bot_or_client(self, bot_id: str = None, client_id: str = None) -> dict:
        """
        Return a count of chat sessions filtered by bot_id and/or client_id.

        Args:
            bot_id (str, optional): If provided, count only sessions for this bot.
            client_id (str, optional): If provided, count only sessions associated with this client.

        Returns:
            dict: {
                "success": True,
                "data": {"count": int}  # Count of matching sessions
            }
            or
            dict: {
                "success": False,
                "error": str
            }

        Constraints:
            - If bot_id is provided, it must exist in the system.
            - If client_id is provided, it must exist in the system.
            - If both are None, count all sessions.
        """
        # Validate bot_id if given
        if bot_id is not None and bot_id not in self.bots:
            return { "success": False, "error": f"bot_id '{bot_id}' does not exist" }

        # Validate client_id if given
        if client_id is not None and client_id not in self.clients:
            return { "success": False, "error": f"client_id '{client_id}' does not exist" }

        # Filtering logic
        filtered_sessions = self.sessions.values()
        if bot_id is not None:
            filtered_sessions = [s for s in filtered_sessions if s["bot_id"] == bot_id]
        if client_id is not None:
            filtered_sessions = [s for s in filtered_sessions if s["client_id"] == client_id]

        count = len(filtered_sessions)

        return { "success": True, "data": {"count": count} }

    def add_bot(self, bot_id: str, name: str, metadata: dict, configuration: dict) -> dict:
        """
        Register a new bot with given bot_id, name, metadata, and configuration.

        Args:
            bot_id (str): Unique identifier for the bot (must not duplicate existing bot_id).
            name (str): Bot name (not required to be unique).
            metadata (dict): Metadata for the bot.
            configuration (dict): Configuration for the bot.

        Returns:
            dict: {
                "success": True,
                "message": "Bot added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (duplicate bot_id)
            }

        Constraints:
            - `bot_id` must be unique across all bots in the platform.
            - Names do not need to be unique.
        """
        if bot_id in self.bots:
            return { "success": False, "error": "Bot with this bot_id already exists." }

        self.bots[bot_id] = {
            "bot_id": bot_id,
            "name": name,
            "metadata": metadata,
            "configuration": configuration
        }

        return { "success": True, "message": "Bot added successfully." }

    def update_bot_metadata(self, bot_id: str, metadata: dict = None, configuration: dict = None) -> dict:
        """
        Update the metadata and/or configuration of an existing bot profile.

        Args:
            bot_id (str): Unique identifier of the bot to update.
            metadata (dict, optional): New metadata dict to assign to the bot. If not provided, metadata is unchanged.
            configuration (dict, optional): New configuration dict to assign. If not provided, configuration is unchanged.

        Returns:
            dict: 
                - {"success": True, "message": "Bot metadata/configuration updated."} on success.
                - {"success": False, "error": "..."} on failure (e.g., bot not found, invalid input).

        Constraints:
            - bot_id must exist (must be a valid bot).
            - At least one of metadata or configuration must be provided.
            - Provided metadata/configuration must be dicts if provided.
        """
        if bot_id not in self.bots:
            return {"success": False, "error": "Bot not found."}

        if metadata is None and configuration is None:
            return {"success": False, "error": "No update parameters provided."}

        if metadata is not None:
            if not isinstance(metadata, dict):
                return {"success": False, "error": "Provided metadata is not a dictionary."}
            self.bots[bot_id]["metadata"] = metadata

        if configuration is not None:
            if not isinstance(configuration, dict):
                return {"success": False, "error": "Provided configuration is not a dictionary."}
            self.bots[bot_id]["configuration"] = configuration

        return {"success": True, "message": "Bot metadata/configuration updated."}

    def register_new_client(
        self,
        client_id: str,
        name: str,
        organization: str,
        contact_info: str
    ) -> dict:
        """
        Add a new client account with organizational and contact info.

        Args:
            client_id (str): Unique client identifier. Must not already exist.
            name (str): Client's name.
            organization (str): Client's organization.
            contact_info (str): Contact details for the client.

        Returns:
            dict:
                - success: True and message on successful registration.
                - success: False and error message on failure (e.g., duplicate client_id).

        Constraints:
            - client_id must be unique in the platform.
            - All fields are required.
        """
        if not all([client_id, name, organization, contact_info]):
            return {
                "success": False,
                "error": "All fields (client_id, name, organization, contact_info) are required"
            }

        if client_id in self.clients:
            return {
                "success": False,
                "error": f"Client with client_id '{client_id}' already exists"
            }
    
        self.clients[client_id] = {
            "client_id": client_id,
            "name": name,
            "organization": organization,
            "contact_info": contact_info
        }

        return {
            "success": True,
            "message": f"Client '{client_id}' registered successfully"
        }

    def update_client_info(
        self, 
        client_id: str, 
        name: str = None, 
        organization: str = None, 
        contact_info: str = None
    ) -> dict:
        """
        Modify existing client details. Only fields provided (not None) will be updated.

        Args:
            client_id (str): Unique client identifier.
            name (str, optional): New name for the client.
            organization (str, optional): New organization for the client.
            contact_info (str, optional): New contact info for the client.

        Returns:
            dict: {
                "success": True,
                "message": "Client info updated."
            }
            or
            {
                "success": False,
                "error": "Client not found." or other error string
            }

        Constraints:
            - client_id must exist.
            - Only provided (non-None) fields are updated.

        """
        client = self.clients.get(client_id)
        if not client:
            return { "success": False, "error": "Client not found." }

        fields_updated = False
        if name is not None:
            client['name'] = name
            fields_updated = True
        if organization is not None:
            client['organization'] = organization
            fields_updated = True
        if contact_info is not None:
            client['contact_info'] = contact_info
            fields_updated = True

        if not fields_updated:
            return { "success": False, "error": "No update fields provided." }

        self.clients[client_id] = client  # Not strictly necessary, but explicit.

        return { "success": True, "message": "Client info updated." }

    def create_chat_session(
        self,
        session_id: str,
        bot_id: str,
        client_id: str,
        start_time: str,
        end_time: str,
        transcript: str
    ) -> dict:
        """
        Log a new chat session, associating it with a valid bot and client, and storing transcript.

        Args:
            session_id (str): Unique identifier for this session.
            bot_id (str): ID of the bot for this session (must exist).
            client_id (str): ID of the client for this session (must exist).
            start_time (str): Session start time (e.g., ISO format).
            end_time (str): Session end time (e.g., ISO format).
            transcript (str): The text of the conversation.

        Returns:
            dict: 
                Success: {"success": True, "message": "Chat session logged successfully"}
                Failure: {"success": False, "error": <reason>}

        Constraints:
            - session_id must be unique.
            - bot_id and client_id must exist.
            - Deletion of chat sessions is not permitted.
        """
        if session_id in self.sessions:
            return {"success": False, "error": "Session ID already exists"}
        if bot_id not in self.bots:
            return {"success": False, "error": "Bot ID does not exist"}
        if client_id not in self.clients:
            return {"success": False, "error": "Client ID does not exist"}

        self.sessions[session_id] = {
            "session_id": session_id,
            "bot_id": bot_id,
            "client_id": client_id,
            "start_time": start_time,
            "end_time": end_time,
            "transcript": transcript
        }

        return {"success": True, "message": "Chat session logged successfully"}


class ChatbotManagementPlatform(BaseEnv):
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

    def get_bot_by_id(self, **kwargs):
        return self._call_inner_tool('get_bot_by_id', kwargs)

    def get_bots_by_name(self, **kwargs):
        return self._call_inner_tool('get_bots_by_name', kwargs)

    def list_all_bots(self, **kwargs):
        return self._call_inner_tool('list_all_bots', kwargs)

    def get_client_by_id(self, **kwargs):
        return self._call_inner_tool('get_client_by_id', kwargs)

    def get_clients_by_name(self, **kwargs):
        return self._call_inner_tool('get_clients_by_name', kwargs)

    def get_clients_by_organization(self, **kwargs):
        return self._call_inner_tool('get_clients_by_organization', kwargs)

    def list_all_clients(self, **kwargs):
        return self._call_inner_tool('list_all_clients', kwargs)

    def get_session_by_id(self, **kwargs):
        return self._call_inner_tool('get_session_by_id', kwargs)

    def get_sessions_by_bot_id(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_bot_id', kwargs)

    def get_sessions_by_client_id(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_client_id', kwargs)

    def get_sessions_by_bot_and_client(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_bot_and_client', kwargs)

    def get_sessions_by_bot_name_and_client_name(self, **kwargs):
        return self._call_inner_tool('get_sessions_by_bot_name_and_client_name', kwargs)

    def get_session_transcript(self, **kwargs):
        return self._call_inner_tool('get_session_transcript', kwargs)

    def filter_sessions_by_time_range(self, **kwargs):
        return self._call_inner_tool('filter_sessions_by_time_range', kwargs)

    def get_session_count_by_bot_or_client(self, **kwargs):
        return self._call_inner_tool('get_session_count_by_bot_or_client', kwargs)

    def add_bot(self, **kwargs):
        return self._call_inner_tool('add_bot', kwargs)

    def update_bot_metadata(self, **kwargs):
        return self._call_inner_tool('update_bot_metadata', kwargs)

    def register_new_client(self, **kwargs):
        return self._call_inner_tool('register_new_client', kwargs)

    def update_client_info(self, **kwargs):
        return self._call_inner_tool('update_client_info', kwargs)

    def create_chat_session(self, **kwargs):
        return self._call_inner_tool('create_chat_session', kwargs)

