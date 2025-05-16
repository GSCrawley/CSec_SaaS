"""
infrastructure/communication/agent_communication.py

This module provides the communication system for agents to interact with each other.
It implements message passing, event notifications, and coordination patterns for 
efficient agent collaboration.
"""

import logging
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

import redis
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """Types of messages that can be exchanged between agents."""
    REQUEST = "request"            # Request for information or action
    RESPONSE = "response"          # Response to a request
    NOTIFICATION = "notification"  # Notification of an event
    COMMAND = "command"            # Command to perform an action
    STATUS = "status"              # Status update


class Message(BaseModel):
    """Message exchanged between agents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    sender_id: str
    receiver_id: Optional[str] = None  # None for broadcast messages
    subject: str
    content: Dict[str, Any]
    correlation_id: Optional[str] = None  # For linking related messages
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "subject": self.subject,
            "content": self.content,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        if isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["type"] = MessageType(data["type"])
        return cls(**data)


class AgentCommunicationSystem:
    """System for agent communication using Redis pub/sub."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize agent communication system.
        
        Args:
            redis_url: Redis connection URL.
        """
        self.redis_client = redis.Redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        self.subscribers: Dict[str, List[Callable[[Message], None]]] = {}
        logger.info(f"Initialized AgentCommunicationSystem with Redis at {redis_url}")
    
    def send_message(self, message: Message) -> bool:
        """Send message to another agent.
        
        Args:
            message: Message to send.
            
        Returns:
            True if message was sent successfully, False otherwise.
        """
        try:
            channel = f"agent:{message.receiver_id}" if message.receiver_id else "agent:broadcast"
            message_data = json.dumps(message.to_dict())
            self.redis_client.publish(channel, message_data)
            logger.debug(f"Sent message {message.id} to channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def subscribe(self, agent_id: str, callback: Callable[[Message], None]) -> None:
        """Subscribe to messages directed to this agent.
        
        Args:
            agent_id: Agent ID.
            callback: Callback function to handle received messages.
        """
        channels = [f"agent:{agent_id}", "agent:broadcast"]
        
        for channel in channels:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            self.pubsub.subscribe(**{channel: self._message_handler})
        
        logger.info(f"Agent {agent_id} subscribed to channels: {channels}")
    
    def _message_handler(self, message: Dict[str, Any]) -> None:
        """Handle received messages from Redis pub/sub.
        
        Args:
            message: Raw message from Redis.
        """
        if message["type"] != "message":
            return
        
        try:
            channel = message["channel"].decode("utf-8")
            data = json.loads(message["data"].decode("utf-8"))
            parsed_message = Message.from_dict(data)
            
            # Call all callbacks for this channel
            if channel in self.subscribers:
                for callback in self.subscribers[channel]:
                    callback(parsed_message)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def start_listening(self) -> None:
        """Start listening for messages in a separate thread."""
        thread = self.pubsub.run_in_thread(sleep_time=0.01)
        logger.info("Started listening for messages")
        return thread
    
    def stop_listening(self) -> None:
        """Stop listening for messages."""
        self.pubsub.close()
        logger.info("Stopped listening for messages")


class AgentCommunicator:
    """Handles communication for a specific agent."""
    
    def __init__(self, agent_id: str, comm_system: AgentCommunicationSystem):
        """Initialize agent communicator.
        
        Args:
            agent_id: Agent ID.
            comm_system: Communication system.
        """
        self.agent_id = agent_id
        self.comm_system = comm_system
        self.message_handlers: Dict[str, Callable[[Message], None]] = {}
        
        # Subscribe to messages
        self.comm_system.subscribe(agent_id, self._handle_message)
        logger.info(f"Initialized communicator for agent {agent_id}")
    
    def send_request(self, receiver_id: str, subject: str, content: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a request message to another agent.
        
        Args:
            receiver_id: Receiver agent ID.
            subject: Message subject.
            content: Message content.
            metadata: Optional message metadata.
            
        Returns:
            Message ID.
        """
        message = Message(
            type=MessageType.REQUEST,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content,
            metadata=metadata or {}
        )
        self.comm_system.send_message(message)
        return message.id
    
    def send_response(self, request_message: Message, content: Dict[str, Any], 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a response message to a request.
        
        Args:
            request_message: Original request message.
            content: Response content.
            metadata: Optional message metadata.
            
        Returns:
            Message ID.
        """
        message = Message(
            type=MessageType.RESPONSE,
            sender_id=self.agent_id,
            receiver_id=request_message.sender_id,
            subject=f"Re: {request_message.subject}",
            content=content,
            correlation_id=request_message.id,
            metadata=metadata or {}
        )
        self.comm_system.send_message(message)
        return message.id
    
    def send_notification(self, subject: str, content: Dict[str, Any], 
                         receiver_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a notification message.
        
        Args:
            subject: Message subject.
            content: Message content.
            receiver_id: Optional receiver agent ID. If None, broadcast to all agents.
            metadata: Optional message metadata.
            
        Returns:
            Message ID.
        """
        message = Message(
            type=MessageType.NOTIFICATION,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content,
            metadata=metadata or {}
        )
        self.comm_system.send_message(message)
        return message.id
    
    def send_command(self, receiver_id: str, subject: str, content: Dict[str, Any],
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a command message to another agent.
        
        Args:
            receiver_id: Receiver agent ID.
            subject: Command subject.
            content: Command content.
            metadata: Optional message metadata.
            
        Returns:
            Message ID.
        """
        message = Message(
            type=MessageType.COMMAND,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content,
            metadata=metadata or {}
        )
        self.comm_system.send_message(message)
        return message.id
    
    def send_status(self, subject: str, content: Dict[str, Any],
                   receiver_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a status update message.
        
        Args:
            subject: Status subject.
            content: Status content.
            receiver_id: Optional receiver agent ID. If None, broadcast to all agents.
            metadata: Optional message metadata.
            
        Returns:
            Message ID.
        """
        message = Message(
            type=MessageType.STATUS,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            subject=subject,
            content=content,
            metadata=metadata or {}
        )
        self.comm_system.send_message(message)
        return message.id
    
    def register_handler(self, message_type: MessageType, subject: str, 
                        handler: Callable[[Message], None]) -> None:
        """Register a handler for specific message types and subjects.
        
        Args:
            message_type: Type of message to handle.
            subject: Subject to match (can use * as wildcard).
            handler: Handler function to call when message is received.
        """
        key = f"{message_type.value}:{subject}"
        self.message_handlers[key] = handler
        logger.info(f"Agent {self.agent_id} registered handler for {key}")
    
    def _handle_message(self, message: Message) -> None:
        """Handle a received message.
        
        Args:
            message: Received message.
        """
        # Check for exact match
        key = f"{message.type.value}:{message.subject}"
        if key in self.message_handlers:
            self.message_handlers[key](message)
            return
        
        # Check for wildcard match
        wildcard_key = f"{message.type.value}:*"
        if wildcard_key in self.message_handlers:
            self.message_handlers[wildcard_key](message)
            return
        
        # If no specific handler, log the message
        logger.debug(f"Agent {self.agent_id} received unhandled message: {message.subject}")