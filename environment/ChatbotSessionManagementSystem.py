# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
import uuid
from datetime import datetime



# Client entity / attributes
class ClientInfo(TypedDict):
    client_id: str
    client_slug: str
    display_name: str
    account_status: str

# ChatbotAgent entity / attributes
class ChatbotAgentInfo(TypedDict):
    agent_id: str
    agent_name: str
    version: str
    is_active: bool

# ChatSession entity / attributes
class ChatSessionInfo(TypedDict):
    session_id: str
    client_id: str
    agent_id: str
    status: str
    created_at: str
    closed_at: Optional[str]

# Message entity / attributes
class MessageInfo(TypedDict):
    message_id: str
    session_id: str
    sender_type: str      # e.g., 'client' or 'agent'
    sender_id: str
    timestamp: str
    content: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Clients: {client_id: ClientInfo}
        self.clients: Dict[str, ClientInfo] = {}

        # Agents: {agent_id: ChatbotAgentInfo}
        self.agents: Dict[str, ChatbotAgentInfo] = {}

        # Chat Sessions: {session_id: ChatSessionInfo}
        self.sessions: Dict[str, ChatSessionInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # Constraints:
        # - A chat session must be associated with exactly one client and one chatbot agent.
        # - Only sessions with status = "active" are considered ongoing.
        # - Messages are always linked to an existing chat session.
        # - Agents and clients must exist before sessions can be created.

    def get_client_by_slug(self, client_slug: str) -> dict:
        """
        Retrieve client information using the unique client_slug.

        Args:
            client_slug (str): The unique, human-friendly identifier for the client.

        Returns:
            dict:
                - If found: {"success": True, "data": ClientInfo}
                - If not found: {"success": False, "error": "Client not found"}

        Constraints:
            - client_slug must uniquely identify a client in the system.
        """
        for client_info in self.clients.values():
            if client_info["client_slug"] == client_slug:
                return {"success": True, "data": client_info}
        return {"success": False, "error": "Client not found"}

    def get_client_by_id(self, client_id: str) -> dict:
        """
        Retrieve client information using client_id.

        Args:
            client_id (str): The unique identifier of the client.

        Returns:
            dict: {
                "success": True,
                "data": ClientInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - client_id must exist in the system.
        """
        client = self.clients.get(client_id)
        if client is None:
            return {"success": False, "error": "Client does not exist"}
        return {"success": True, "data": client}

    def list_all_clients(self) -> dict:
        """
        List all registered client entries.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ClientInfo]  # May be an empty list if there are no registered clients.
            }

        Constraints:
            - No constraints; returns all clients found in the system.
        """
        data = list(self.clients.values())
        return {"success": True, "data": data}

    def get_agent_by_name(self, agent_name: str) -> dict:
        """
        Retrieve chatbot agent information(s) matching the provided agent_name.

        Args:
            agent_name (str): Name of the chatbot agent to search for.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": List[ChatbotAgentInfo],  # List of matching agents (could be empty if no match)
                    }
                - On failure (no agent found):
                    {
                        "success": False,
                        "error": "No agent with that name"
                    }
        Constraints:
            - The system may contain multiple agents with the same agent_name but different IDs or versions.
            - Returns all matching agents in a list.
        """
        matches = [agent for agent in self.agents.values() if agent["agent_name"] == agent_name]
        if matches:
            return { "success": True, "data": matches }
        else:
            return { "success": False, "error": "No agent with that name" }

    def get_agent_by_id(self, agent_id: str) -> dict:
        """
        Retrieve chatbot agent information given an agent_id.

        Args:
            agent_id (str): Unique identifier for the chatbot agent.

        Returns:
            dict: {
                "success": True,
                "data": ChatbotAgentInfo  # Chatbot agent's information
            }
            or
            {
                "success": False,
                "error": str  # Reason why lookup failed (not found)
            }

        Constraints:
            - agent_id must correspond to an existing agent.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            return { "success": False, "error": "Agent with the given agent_id does not exist" }
        return { "success": True, "data": agent }

    def list_active_agents(self) -> dict:
        """
        Returns all currently active chatbot agent entries.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ChatbotAgentInfo]  # a list of all active agents (can be empty)
            }

        Constraints:
            - Only agents with 'is_active' set to True are returned.
        """
        active_agents = [
            agent_info for agent_info in self.agents.values() if agent_info.get("is_active", False)
        ]
        return {"success": True, "data": active_agents}

    def list_sessions_by_client(self, client_id: str) -> dict:
        """
        Retrieve all chat sessions associated with the given client_id.

        Args:
            client_id (str): Unique identifier for the client.

        Returns:
            dict with:
                - success: True if retrieval succeeds, False if client does not exist.
                - data: List[ChatSessionInfo] if success (may be empty).
                - error: error description if not successful.

        Constraints:
            - client_id must exist in the system (self.clients).
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist" }

        sessions = [
            session_info for session_info in self.sessions.values()
            if session_info["client_id"] == client_id
        ]
        return { "success": True, "data": sessions }

    def list_sessions_by_agent(self, agent_id: str) -> dict:
        """
        Retrieve all chat sessions (with metadata) associated with a specific agent_id.

        Args:
            agent_id (str): The identifier of the chatbot agent.

        Returns:
            dict:
                success: True and data: List[ChatSessionInfo] if successful (possibly empty).
                Or success: False and error: str reason if agent_id is not known.

        Constraints:
            - agent_id must exist as a key in self.agents.
            - All sessions where session.agent_id == agent_id are included, regardless of status.
        """
        if agent_id not in self.agents:
            return { "success": False, "error": "Agent with the specified agent_id does not exist" }
    
        sessions = [
            session_info for session_info in self.sessions.values()
            if session_info["agent_id"] == agent_id
        ]
        return { "success": True, "data": sessions }

    def list_active_sessions_for_client(self, client_id: str) -> dict:
        """
        List all active chat sessions for the specified client.

        Args:
            client_id (str): Unique identifier of the client.
        
        Returns:
            dict:
                - On success:
                    {"success": True, "data": List[ChatSessionInfo]} 
                      # List is empty if no active sessions
                - On failure:
                    {"success": False, "error": str}

        Constraints:
            - The given client_id must exist in the system.
            - Only sessions with status == 'active' are returned.
        """
        if client_id not in self.clients:
            return {"success": False, "error": "Client does not exist"}

        active_sessions = [
            session for session in self.sessions.values()
            if session["client_id"] == client_id and session["status"] == "active"
        ]

        return {"success": True, "data": active_sessions}

    def list_active_sessions_by_client_and_agents(self, client_id: str, agent_ids: list[str]) -> dict:
        """
        Lists all active chat sessions for a given client that involve any of the specified agent_ids.

        Args:
            client_id (str): The ID of the client whose sessions are to be listed.
            agent_ids (List[str]): A list of agent IDs. Only sessions involving agents in this list will be considered.

        Returns:
            dict: {
                "success": True,
                "data": List[ChatSessionInfo],  # All matching active sessions (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # E.g., client does not exist
            }

        Constraints:
            - Client must exist in the system.
            - Only returns sessions with status == "active" involving given agent_ids.
        """
        if client_id not in self.clients:
            return {"success": False, "error": "Client does not exist"}

        # agent_ids may include non existent, but that's fine - we just don't find those sessions

        result = [
            session for session in self.sessions.values()
            if session["client_id"] == client_id
                and session["agent_id"] in agent_ids
                and session["status"] == "active"
        ]

        return {"success": True, "data": result}

    def get_session_details(self, session_id: str) -> dict:
        """
        Retrieve full information for a chat session by session_id.

        Args:
            session_id (str): The unique identifier of the chat session.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": ChatSessionInfo}
                - If not found:
                    {"success": False, "error": "Session does not exist"}

        Constraints:
            - The provided session_id must exist in the system.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session does not exist"}
        return {"success": True, "data": session}

    def list_messages_for_session(self, session_id: str) -> dict:
        """
        Retrieve all messages exchanged within a specific chat session.

        Args:
            session_id (str): The unique identifier of the chat session.

        Returns:
            dict: {
                "success": True,
                "data": List[MessageInfo],   # List of all messages for the session (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # "Session does not exist"
            }

        Constraints:
            - The session must exist in the system.
            - All returned messages are linked to the provided session_id.
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session does not exist"}

        result = [
            msg for msg in self.messages.values()
            if msg["session_id"] == session_id
        ]
        return {"success": True, "data": result}

    def list_all_messages_by_client(self, client_id: str) -> dict:
        """
        Retrieve all messages sent by a particular client (across all sessions).

        Args:
            client_id (str): The unique identifier of the target client.

        Returns:
            dict:
                Success: { "success": True, "data": List[MessageInfo] }
                Failure: { "success": False, "error": str }

        Constraints:
            - The client_id must exist in the system.
            - Messages are filtered based on sender_type == "client" and sender_id == client_id.
        """
        if client_id not in self.clients:
            return { "success": False, "error": "Client does not exist" }

        matched_messages = [
            message_info for message_info in self.messages.values()
            if message_info["sender_type"] == "client" and message_info["sender_id"] == client_id
        ]

        return { "success": True, "data": matched_messages }

    def create_client(
        self, 
        client_id: str, 
        client_slug: str,
        display_name: str,
        account_status: str
    ) -> dict:
        """
        Register a new client in the system.

        Args:
            client_id (str): Unique identifier for the client.
            client_slug (str): Unique, human-readable string for the client.
            display_name (str): Name to display for the client.
            account_status (str): Status of the client account (e.g., 'active').

        Returns:
            dict:
                On success: { "success": True, "message": "Client created successfully" }
                On failure: { "success": False, "error": str }

        Constraints:
            - client_id must not already exist.
            - client_slug must be unique across all clients.
        """
        # Check required fields
        if not all([client_id, client_slug, display_name, account_status]):
            return {"success": False, "error": "All client fields must be provided and non-empty"}

        # Check uniqueness of client_id
        if client_id in self.clients:
            return {"success": False, "error": "client_id already exists"}

        # Check uniqueness of client_slug
        for client in self.clients.values():
            if client["client_slug"] == client_slug:
                return {"success": False, "error": "client_slug already exists"}

        # Create and store new client
        client_info: ClientInfo = {
            "client_id": client_id,
            "client_slug": client_slug,
            "display_name": display_name,
            "account_status": account_status
        }
        self.clients[client_id] = client_info

        return {"success": True, "message": "Client created successfully"}

    def create_chatbot_agent(
        self, 
        agent_id: str, 
        agent_name: str, 
        version: str, 
        is_active: bool
    ) -> dict:
        """
        Register a new chatbot agent.

        Args:
            agent_id (str): Unique identifier for the agent.
            agent_name (str): The display name of the chatbot agent.
            version (str): The version string of the agent.
            is_active (bool): Indicates if agent is active.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Chatbot agent created successfully." }
                - On error:   { "success": False, "error": "<reason>" }

        Constraints:
            - agent_id must be unique across the system.
        """
        if not agent_id or not agent_name or not version:
            return { "success": False, "error": "Missing required fields." }
    
        if agent_id in self.agents:
            return { "success": False, "error": "Agent ID already exists." }

        agent_info = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "version": version,
            "is_active": is_active
        }
        self.agents[agent_id] = agent_info
        return { "success": True, "message": "Chatbot agent created successfully." }

    def create_chat_session(self, client_id: str, agent_id: str) -> dict:
        """
        Create a new chat session between an existing client and agent.

        Args:
            client_id (str): The unique identifier of the client.
            agent_id (str): The unique identifier of the chatbot agent.

        Returns:
            dict: {
                "success": True,
                "message": "Chat session created",
                "session_id": str,
                "session_info": ChatSessionInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Both client and agent must exist before the chat session is created.
            - Creates a new session with status="active", sets created_at to now, and closed_at=None.
        """

        # Check client exists
        if client_id not in self.clients:
            return {"success": False, "error": "Client does not exist"}

        # Check agent exists
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent does not exist"}

        # Generate unique session_id
        session_id = str(uuid.uuid4())
        now_iso = datetime.utcnow().isoformat() + "Z"

        session_info: ChatSessionInfo = {
            "session_id": session_id,
            "client_id": client_id,
            "agent_id": agent_id,
            "status": "active",
            "created_at": now_iso,
            "closed_at": None,
        }

        self.sessions[session_id] = session_info

        return {
            "success": True,
            "message": "Chat session created",
            "session_id": session_id,
            "session_info": session_info
        }


    def close_chat_session(self, session_id: str) -> dict:
        """
        Mark a chat session as closed and record the closed_at timestamp.

        Args:
            session_id (str): The unique identifier of the chat session.

        Returns:
            dict: {
                "success": True,
                "message": "Session closed successfully"
            }
            or
            {
                "success": False,
                "error": str  # error message: e.g., 'Session does not exist', 'Session already closed'
            }

        Constraints:
            - The session must exist.
            - Only non-closed sessions may be closed.
            - closed_at timestamp is set to current time (ISO 8601).
        """
        if session_id not in self.sessions:
            return { "success": False, "error": "Session does not exist" }
    
        session = self.sessions[session_id]
        if session.get("status") == "closed":
            return { "success": False, "error": "Session already closed" }
    
        # Mark as closed and add timestamp
        session["status"] = "closed"
        session["closed_at"] = datetime.utcnow().isoformat() + "Z"
        self.sessions[session_id] = session

        return { "success": True, "message": "Session closed successfully" }

    def reopen_chat_session(self, session_id: str) -> dict:
        """
        Reopen a closed chat session (change status to 'active' and clear closed_at).

        Args:
            session_id (str): The ID of the chat session to reopen.

        Returns:
            dict: 
                On success: { "success": True, "message": "Session <session_id> reopened." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Session must exist.
            - Session must not already be active.
        """
        session = self.sessions.get(session_id)
        if not session:
            return { "success": False, "error": "Session not found." }
        if session["status"] == "active":
            return { "success": False, "error": "Session is already active." }

        session["status"] = "active"
        session["closed_at"] = None

        return { "success": True, "message": f"Session {session_id} reopened." }


    def send_message_in_session(
        self,
        session_id: str,
        sender_type: str,
        sender_id: str,
        content: str,
        timestamp: str = None
    ) -> dict:
        """
        Add a message to an existing chat session. Sender must be either the client or agent associated
        with the session, and the session must be active.

        Args:
            session_id (str): Target chat session.
            sender_type (str): 'client' or 'agent'.
            sender_id (str): ID of the sender (client_id or agent_id).
            content (str): Message content (non-empty).
            timestamp (str, optional): ISO8601 timestamp string. If not supplied, uses current time.

        Returns:
            dict: { "success": True, "message": "Message sent in session <session_id>" }
                  or
                  { "success": False, "error": "reason" }

        Constraints:
            - Session must exist and be active.
            - Sender must exist and be associated with the session.
            - Content must not be empty.
        """
        # Check session existence
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session does not exist"}

        # Check session status
        if session["status"] != "active":
            return {"success": False, "error": "Session is not active"}

        # Sender Type
        if sender_type not in ("client", "agent"):
            return {"success": False, "error": "sender_type must be 'client' or 'agent'"}

        # Check sender association and existence
        if sender_type == "client":
            if sender_id != session["client_id"]:
                return {"success": False, "error": "Sender_id does not match session's client_id"}
            if sender_id not in self.clients:
                return {"success": False, "error": "Client does not exist"}
        else:  # sender_type == "agent"
            if sender_id != session["agent_id"]:
                return {"success": False, "error": "Sender_id does not match session's agent_id"}
            if sender_id not in self.agents:
                return {"success": False, "error": "Agent does not exist"}

        # Validate content
        if content is None or not str(content).strip():
            return {"success": False, "error": "Content must not be empty"}

        # Timestamp
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        # Generate new message_id (UUID)
        message_id = str(uuid.uuid4())

        # Create message entry
        message: MessageInfo = {
            "message_id": message_id,
            "session_id": session_id,
            "sender_type": sender_type,
            "sender_id": sender_id,
            "timestamp": timestamp,
            "content": content,
        }

        self.messages[message_id] = message

        return {"success": True, "message": f"Message sent in session {session_id}"}

    def update_client_status(self, client_id: str, new_status: str) -> dict:
        """
        Change the account status of a client.

        Args:
            client_id (str): The unique identifier for the client to update.
            new_status (str): The new status value to assign to the client.

        Returns:
            dict: {
                "success": True,
                "message": "Client account status updated."
            }
            or
            {
                "success": False,
                "error": "Client not found."
            }

        Constraints:
            - client_id must refer to an existing client.
            - new_status can be any string (no constraints specified).
        """
        client = self.clients.get(client_id)
        if not client:
            return {"success": False, "error": "Client not found."}

        client["account_status"] = new_status
        return {"success": True, "message": "Client account status updated."}

    def update_agent_status(self, agent_id: str, is_active: bool) -> dict:
        """
        Activate or deactivate a chatbot agent.

        Args:
            agent_id (str): The unique identifier of the agent to update.
            is_active (bool): True to activate, False to deactivate the agent.

        Returns:
            dict: 
                - On success: 
                    {
                        "success": True,
                        "message": "Agent status updated to active." | "Agent status updated to deactivated."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Agent not found."
                    }
        Constraints:
            - The agent must exist in the system.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found."}

        agent["is_active"] = is_active
        status_str = "active" if is_active else "deactivated"
        return {"success": True, "message": f"Agent status updated to {status_str}."}

    def delete_chat_session(self, session_id: str) -> dict:
        """
        Remove a chat session and all its associated messages, if permitted.

        Args:
            session_id (str): The ID of the session to delete.

        Returns:
            dict:
                - If successful:
                    { "success": True, "message": "Chat session <session_id> deleted." }
                - If failure (session does not exist or deletion not permitted):
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The session must exist.
            - Only non-active (status != 'active') sessions can be deleted.
            - All messages associated with the session are deleted as well.
        """
        session = self.sessions.get(session_id)
        if session is None:
            return {"success": False, "error": "Session does not exist"}

        if session["status"] == "active":
            return {"success": False, "error": "Cannot delete an active session"}

        # Delete all messages linked to this session
        message_ids_to_delete = [msg_id for msg_id, msg in self.messages.items() if msg["session_id"] == session_id]
        for msg_id in message_ids_to_delete:
            del self.messages[msg_id]

        del self.sessions[session_id]

        return {
            "success": True,
            "message": f"Chat session {session_id} deleted."
        }

    def delete_message(self, message_id: str) -> dict:
        """
        Remove a specific message from the system.

        Args:
            message_id (str): The unique identifier of the message to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Message <message_id> deleted."
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The message must exist in the system.
            - The message must be linked to an existing chat session (extra check for consistency, though the environment should maintain this).
        """
        if message_id not in self.messages:
            return {"success": False, "error": "Message does not exist"}

        msg = self.messages[message_id]
        session_id = msg.get("session_id")
        if session_id not in self.sessions:
            return {"success": False, "error": "Session associated with message does not exist"}

        del self.messages[message_id]
        return {"success": True, "message": f"Message {message_id} deleted."}


class ChatbotSessionManagementSystem(BaseEnv):
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

    def get_client_by_slug(self, **kwargs):
        return self._call_inner_tool('get_client_by_slug', kwargs)

    def get_client_by_id(self, **kwargs):
        return self._call_inner_tool('get_client_by_id', kwargs)

    def list_all_clients(self, **kwargs):
        return self._call_inner_tool('list_all_clients', kwargs)

    def get_agent_by_name(self, **kwargs):
        return self._call_inner_tool('get_agent_by_name', kwargs)

    def get_agent_by_id(self, **kwargs):
        return self._call_inner_tool('get_agent_by_id', kwargs)

    def list_active_agents(self, **kwargs):
        return self._call_inner_tool('list_active_agents', kwargs)

    def list_sessions_by_client(self, **kwargs):
        return self._call_inner_tool('list_sessions_by_client', kwargs)

    def list_sessions_by_agent(self, **kwargs):
        return self._call_inner_tool('list_sessions_by_agent', kwargs)

    def list_active_sessions_for_client(self, **kwargs):
        return self._call_inner_tool('list_active_sessions_for_client', kwargs)

    def list_active_sessions_by_client_and_agents(self, **kwargs):
        return self._call_inner_tool('list_active_sessions_by_client_and_agents', kwargs)

    def get_session_details(self, **kwargs):
        return self._call_inner_tool('get_session_details', kwargs)

    def list_messages_for_session(self, **kwargs):
        return self._call_inner_tool('list_messages_for_session', kwargs)

    def list_all_messages_by_client(self, **kwargs):
        return self._call_inner_tool('list_all_messages_by_client', kwargs)

    def create_client(self, **kwargs):
        return self._call_inner_tool('create_client', kwargs)

    def create_chatbot_agent(self, **kwargs):
        return self._call_inner_tool('create_chatbot_agent', kwargs)

    def create_chat_session(self, **kwargs):
        return self._call_inner_tool('create_chat_session', kwargs)

    def close_chat_session(self, **kwargs):
        return self._call_inner_tool('close_chat_session', kwargs)

    def reopen_chat_session(self, **kwargs):
        return self._call_inner_tool('reopen_chat_session', kwargs)

    def send_message_in_session(self, **kwargs):
        return self._call_inner_tool('send_message_in_session', kwargs)

    def update_client_status(self, **kwargs):
        return self._call_inner_tool('update_client_status', kwargs)

    def update_agent_status(self, **kwargs):
        return self._call_inner_tool('update_agent_status', kwargs)

    def delete_chat_session(self, **kwargs):
        return self._call_inner_tool('delete_chat_session', kwargs)

    def delete_message(self, **kwargs):
        return self._call_inner_tool('delete_message', kwargs)

