"""
agents/core/base_agent.py

This module defines the base Agent class that all specialized agents will inherit from.
It provides common functionality for agent operations, communication, and interaction
with the knowledge fabric.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from infrastructure.communication.agent_communication import (
    AgentCommunicator, AgentCommunicationSystem, Message, MessageType
)
from infrastructure.knowledge_fabric.services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for agents."""
    agent_id: Optional[str] = None
    agent_name: str
    agent_type: str
    agent_layer: str
    description: Optional[str] = None
    model: str = "mixtral-8x7b-32768"
    max_tokens: int = 4000
    temperature: float = 0.2
    tools_config: Dict[str, Any] = Field(default_factory=dict)
    api_keys: Dict[str, str] = Field(default_factory=dict)


class AgentState(BaseModel):
    """Agent state information."""
    status: str = "idle"  # idle, busy, error
    current_task: Optional[str] = None
    last_activity: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class Agent(ABC):
    """Base class for all agents in the Development Crew."""
    
    def __init__(self, 
                 config: AgentConfig,
                 knowledge_service: Optional[KnowledgeService] = None,
                 communication_system: Optional[AgentCommunicationSystem] = None):
        """Initialize agent.
        
        Args:
            config: Agent configuration.
            knowledge_service: Optional knowledge service. If None, creates a new one.
            communication_system: Optional communication system. If None, creates a new one.
        """
        self.config = config
        self.state = AgentState()
        
        # Initialize knowledge service
        if knowledge_service:
            self.knowledge_service = knowledge_service
            self._owns_knowledge_service = False
        else:
            from infrastructure.knowledge_fabric.core.connection import get_connection_pool
            connection = get_connection_pool().get_connection()
            self.knowledge_service = KnowledgeService(connection)
            self._owns_knowledge_service = True
        
        # Register agent in knowledge graph if not already registered
        if not self.config.agent_id:
            agent = self.knowledge_service.create_agent(
                name=self.config.agent_name,
                agent_type=self.config.agent_type,
                layer=self.config.agent_layer,
                description=self.config.description
            )
            self.config.agent_id = agent.id
            logger.info(f"Registered agent in knowledge graph with ID: {self.config.agent_id}")
        
        # Initialize communication system
        if communication_system:
            self.communication_system = communication_system
            self._owns_communication_system = False
        else:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.communication_system = AgentCommunicationSystem(redis_url)
            self._owns_communication_system = True
        
        # Create communicator
        self.communicator = AgentCommunicator(self.config.agent_id, self.communication_system)
        
        # Register message handlers
        self._register_message_handlers()
        
        logger.info(f"Initialized agent: {self.config.agent_name} ({self.config.agent_type})")
    
    def _register_message_handlers(self) -> None:
        """Register message handlers for different message types."""
        # Register handlers for different message types
        self.communicator.register_handler(MessageType.REQUEST, "*", self._handle_request)
        self.communicator.register_handler(MessageType.COMMAND, "*", self._handle_command)
        self.communicator.register_handler(MessageType.NOTIFICATION, "*", self._handle_notification)
        self.communicator.register_handler(MessageType.STATUS, "*", self._handle_status)
    
    def _handle_request(self, message: Message) -> None:
        """Handle request messages.
        
        Args:
            message: Request message.
        """
        logger.info(f"Agent {self.config.agent_id} received request: {message.subject}")
        
        # Update agent state
        self.state.status = "busy"
        self.state.current_task = f"Processing request: {message.subject}"
        
        try:
            # Process the request
            response_content = self.process_request(message.subject, message.content)
            
            # Send response
            self.communicator.send_response(message, response_content)
            
            # Update agent state
            self.state.status = "idle"
            self.state.current_task = None
            self.state.last_activity = f"Processed request: {message.subject}"
            
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            
            # Send error response
            error_content = {"error": str(e)}
            self.communicator.send_response(message, error_content)
            
            # Update agent state
            self.state.status = "error"
            self.state.error_message = str(e)
    
    def _handle_command(self, message: Message) -> None:
        """Handle command messages.
        
        Args:
            message: Command message.
        """
        logger.info(f"Agent {self.config.agent_id} received command: {message.subject}")
        
        # Update agent state
        self.state.status = "busy"
        self.state.current_task = f"Executing command: {message.subject}"
        
        try:
            # Execute the command
            result = self.execute_command(message.subject, message.content)
            
            # Send response with command result
            response_content = {"result": result}
            self.communicator.send_response(message, response_content)
            
            # Update agent state
            self.state.status = "idle"
            self.state.current_task = None
            self.state.last_activity = f"Executed command: {message.subject}"
            
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            
            # Send error response
            error_content = {"error": str(e)}
            self.communicator.send_response(message, error_content)
            
            # Update agent state
            self.state.status = "error"
            self.state.error_message = str(e)
    
    def _handle_notification(self, message: Message) -> None:
        """Handle notification messages.
        
        Args:
            message: Notification message.
        """
        logger.info(f"Agent {self.config.agent_id} received notification: {message.subject}")
        self.process_notification(message.subject, message.content)
    
    def _handle_status(self, message: Message) -> None:
        """Handle status messages.
        
        Args:
            message: Status message.
        """
        logger.debug(f"Agent {self.config.agent_id} received status update: {message.subject}")
        self.process_status_update(message.subject, message.content)
    
    @abstractmethod
    def process_request(self, subject: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request from another agent.
        
        Args:
            subject: Request subject.
            content: Request content.
            
        Returns:
            Response content.
        """
        pass
    
    @abstractmethod
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> Any:
        """Execute a command.
        
        Args:
            command: Command to execute.
            parameters: Command parameters.
            
        Returns:
            Command result.
        """
        pass
    
    def process_notification(self, subject: str, content: Dict[str, Any]) -> None:
        """Process a notification.
        
        Args:
            subject: Notification subject.
            content: Notification content.
        """
        # Default implementation logs the notification
        logger.info(f"Notification {subject}: {content}")
    
    def process_status_update(self, subject: str, content: Dict[str, Any]) -> None:
        """Process a status update.
        
        Args:
            subject: Status subject.
            content: Status content.
        """
        # Default implementation logs the status update
        logger.debug(f"Status update {subject}: {content}")
    
    def send_request_to_agent(self, agent_id: str, subject: str, 
                            content: Dict[str, Any]) -> str:
        """Send a request to another agent.
        
        Args:
            agent_id: Target agent ID.
            subject: Request subject.
            content: Request content.
            
        Returns:
            Message ID.
        """
        return self.communicator.send_request(agent_id, subject, content)
    
    def broadcast_notification(self, subject: str, content: Dict[str, Any]) -> str:
        """Broadcast a notification to all agents.
        
        Args:
            subject: Notification subject.
            content: Notification content.
            
        Returns:
            Message ID.
        """
        return self.communicator.send_notification(subject, content)
    
    def record_decision(self, title: str, description: str, context: str, 
                       component_ids: Optional[List[str]] = None,
                       confidence: Optional[float] = None) -> str:
        """Record a decision in the knowledge graph.
        
        Args:
            title: Decision title.
            description: Decision description.
            context: Decision context.
            component_ids: Optional list of related component IDs.
            confidence: Optional confidence level (0.0-1.0).
            
        Returns:
            Decision ID.
        """
        decision = self.knowledge_service.record_decision(
            title=title,
            description=description,
            context=context,
            agent_id=self.config.agent_id,
            related_component_ids=component_ids,
            confidence=confidence
        )
        
        # Broadcast decision notification
        self.broadcast_notification(
            "decision_made",
            {
                "decision_id": decision.id,
                "title": title,
                "agent_id": self.config.agent_id,
                "agent_name": self.config.agent_name
            }
        )
        
        return decision.id
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state.
        
        Returns:
            Agent state as dictionary.
        """
        return self.state.dict()
    
    def shutdown(self) -> None:
        """Shutdown the agent, releasing resources."""
        # Broadcast shutdown notification
        self.broadcast_notification(
            "agent_shutdown",
            {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.agent_name,
                "reason": "Normal shutdown"
            }
        )
        
        # Release resources
        if self._owns_knowledge_service:
            self.knowledge_service.close()
        
        if self._owns_communication_system:
            self.communication_system.stop_listening()
        
        logger.info(f"Agent {self.config.agent_name} ({self.config.agent_id}) shutdown complete")