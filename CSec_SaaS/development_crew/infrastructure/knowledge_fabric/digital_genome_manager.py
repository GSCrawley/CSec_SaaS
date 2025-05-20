"""
Digital Genome Manager Module.

This module serves as the main facade for the Digital Genome Architecture,
integrating the dual knowledge architecture, events system, and
associative memory components.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Set

from infrastructure.knowledge_fabric.core.dual_knowledge import DualKnowledgeManager
from infrastructure.knowledge_fabric.core.events_node import EventsNode
from infrastructure.knowledge_fabric.core.associative_memory import AssociativeMemory
from infrastructure.knowledge_fabric.services.event_processor import EventProcessor
from infrastructure.knowledge_fabric.services.knowledge_synchronizer import KnowledgeSynchronizer
from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType
from infrastructure.knowledge_fabric.core.connection import Neo4jConnection
from infrastructure.knowledge_fabric.core.repository import NodeRepository

logger = logging.getLogger(__name__)


class DigitalGenomeManager:
    """
    Main facade for the Digital Genome Architecture.
    
    The DigitalGenomeManager integrates all components of the Digital Genome Architecture:
    1. Dual Knowledge Architecture - individual and shared knowledge graphs
    2. Events System - event logging, processing, and correlation
    3. Associative Memory - context-aware memory system with decay and recall
    
    It provides a unified interface for agents to interact with the genome system.
    """
    
    def __init__(
        self,
        agent_id: str,
        individual_connection_config: Dict[str, Any],
        shared_connection_config: Optional[Dict[str, Any]] = None,
        enable_events: bool = True,
        enable_associative_memory: bool = True,
        auto_sync: bool = True,
        sync_interval_minutes: int = 15
    ):
        """
        Initialize the Digital Genome Manager.
        
        Args:
            agent_id: Unique identifier for the agent
            individual_connection_config: Neo4j connection config for individual graph
            shared_connection_config: Neo4j connection config for shared graph
            enable_events: Whether to enable the events system
            enable_associative_memory: Whether to enable associative memory
            auto_sync: Whether to enable automatic knowledge synchronization
            sync_interval_minutes: Minutes between synchronizations
        """
        self.agent_id = agent_id
        
        # Initialize connections
        self.individual_connection = Neo4jConnection(individual_connection_config)
        self.shared_connection = None
        
        if shared_connection_config:
            self.shared_connection = Neo4jConnection(shared_connection_config)
        
        # Initialize dual knowledge manager
        self.dual_knowledge_manager = None
        if self.shared_connection:
            self.dual_knowledge_manager = DualKnowledgeManager(
                self.shared_connection,
                self.agent_id
            )
        
        # Initialize components based on configuration
        self.events_node = None
        self.associative_memory = None
        self.event_processor = None
        self.knowledge_synchronizer = None
        
        # Initialize repository for nodes
        self.node_repository = NodeRepository(self.individual_connection, NodeLabel.EVENT, None)
        
        # Initialize events system if enabled
        if enable_events:
            self.events_node = EventsNode(self.node_repository)
            
            # Initialize associative memory if enabled
            if enable_associative_memory:
                self.associative_memory = AssociativeMemory(
                    self.node_repository,
                    self.events_node
                )
                
                # Initialize event processor
                self.event_processor = EventProcessor(
                    self.events_node,
                    self.associative_memory
                )
            else:
                # Initialize event processor without associative memory
                self.event_processor = EventProcessor(self.events_node)
        
        # Initialize knowledge synchronizer if shared connection is available
        if self.dual_knowledge_manager and auto_sync:
            self.knowledge_synchronizer = KnowledgeSynchronizer(
                self.dual_knowledge_manager,
                self.events_node
            )
            
            # Configure synchronization interval
            self.knowledge_synchronizer.update_sync_schedule(
                interval_minutes=sync_interval_minutes
            )
        
        logger.info(f"Initialized Digital Genome Manager for agent {agent_id}")
    
    def start(self):
        """
        Start all system components.
        
        Returns:
            bool: True if started successfully
        """
        success = True
        
        # Start event processor
        if self.event_processor:
            processor_started = self.event_processor.start()
            if not processor_started:
                logger.error("Failed to start event processor")
                success = False
            else:
                logger.info("Event processor started")
        
        # Start knowledge synchronizer
        if self.knowledge_synchronizer:
            sync_started = self.knowledge_synchronizer.start_scheduled_sync()
            if not sync_started:
                logger.error("Failed to start knowledge synchronizer")
                success = False
            else:
                logger.info("Knowledge synchronizer started")
        
        if success:
            # Log system startup event
            if self.events_node:
                self.events_node.log_system_event(
                    component="DigitalGenomeManager",
                    event_type="system_started",
                    details={
                        "agent_id": self.agent_id,
                        "event_processor_enabled": self.event_processor is not None,
                        "knowledge_sync_enabled": self.knowledge_synchronizer is not None,
                        "associative_memory_enabled": self.associative_memory is not None
                    }
                )
            
            logger.info(f"Digital Genome Manager started for agent {self.agent_id}")
        
        return success
    
    def stop(self):
        """
        Stop all system components.
        
        Returns:
            bool: True if stopped successfully
        """
        success = True
        
        # Stop event processor
        if self.event_processor:
            processor_stopped = self.event_processor.stop()
            if not processor_stopped:
                logger.error("Failed to stop event processor")
                success = False
            else:
                logger.info("Event processor stopped")
        
        # Stop knowledge synchronizer
        if self.knowledge_synchronizer:
            sync_stopped = self.knowledge_synchronizer.stop_scheduled_sync()
            if not sync_stopped:
                logger.error("Failed to stop knowledge synchronizer")
                success = False
            else:
                logger.info("Knowledge synchronizer stopped")
        
        if success:
            # Log system shutdown event
            if self.events_node:
                self.events_node.log_system_event(
                    component="DigitalGenomeManager",
                    event_type="system_stopped",
                    details={
                        "agent_id": self.agent_id
                    }
                )
            
            logger.info(f"Digital Genome Manager stopped for agent {self.agent_id}")
        
        return success
    
    # Event System Methods
    
    def emit_event(
        self, 
        event_type: str, 
        metadata: Dict[str, Any],
        related_nodes: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        urgent: bool = False
    ) -> Optional[str]:
        """
        Emit an event into the system.
        
        Args:
            event_type: Type of the event
            metadata: Additional data about the event
            related_nodes: Optional list of nodes related to this event
            context: Optional execution context information
            urgent: Whether to process event immediately
            
        Returns:
            str: ID of the created event or None if queued/unavailable
        """
        if not self.event_processor:
            logger.warning("Event processor not available")
            return None
        
        return self.event_processor.emit_event(
            event_type=event_type,
            metadata=metadata,
            related_nodes=related_nodes,
            context=context,
            urgent=urgent
        )
    
    def register_event_handler(self, event_type: str, handler):
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
            
        Returns:
            bool: True if registered successfully
        """
        if not self.event_processor:
            logger.warning("Event processor not available")
            return False
        
        return self.event_processor.register_handler(event_type, handler)
    
    def register_event_correlation(self, pattern: List[str], timeframe: int, action):
        """
        Register a correlation rule for events.
        
        Args:
            pattern: List of event types to match
            timeframe: Time window in seconds
            action: Function to call when pattern is matched
            
        Returns:
            bool: True if registered successfully
        """
        if not self.event_processor:
            logger.warning("Event processor not available")
            return False
        
        rule = {
            "pattern": pattern,
            "timeframe": timeframe,
            "action": action
        }
        
        return self.event_processor.register_correlation_rule(rule)
    
    # Memory System Methods
    
    def store_memory(
        self, 
        content: Dict[str, Any],
        context: Dict[str, Any],
        memory_type: str,
        importance: float = 0.5,
        associations: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Store a memory in the associative memory system.
        
        Args:
            content: The actual content of the memory
            context: Contextual information about the memory
            memory_type: Type of memory
            importance: Initial importance score (0.0 to 1.0)
            associations: IDs of other related memories
            
        Returns:
            str: ID of the created memory or None if unavailable
        """
        if not self.associative_memory:
            logger.warning("Associative memory not available")
            return None
        
        return self.associative_memory.store_memory(
            content=content,
            context=context,
            memory_type=memory_type,
            importance=importance,
            associations=associations
        )
    
    def recall_memory(
        self,
        memory_id: Optional[str] = None,
        query_content: Optional[Dict[str, Any]] = None,
        query_context: Optional[Dict[str, Any]] = None,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> Union[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Recall memories from the associative memory system.
        
        Args:
            memory_id: Optional specific memory ID to recall
            query_content: Optional content to search for
            query_context: Optional context to search for
            memory_type: Optional type of memories to retrieve
            limit: Maximum number of memories to return
            
        Returns:
            Dict or List: Memory data or list of memories
        """
        if not self.associative_memory:
            logger.warning("Associative memory not available")
            return [] if memory_id is None else None
        
        # Recall by specific ID
        if memory_id:
            memory = self.associative_memory.recall_by_id(memory_id)
            return memory.to_dict() if memory else None
        
        # Recall by content
        if query_content:
            memories = self.associative_memory.recall_by_content(query_content, limit)
            return [m.to_dict() for m in memories]
        
        # Recall by context
        if query_context:
            memories = self.associative_memory.recall_by_context(query_context, limit)
            return [m.to_dict() for m in memories]
        
        # Recall by type
        if memory_type:
            memories = self.associative_memory.recall_by_type(memory_type, limit)
            return [m.to_dict() for m in memories]
        
        # Default: return empty list
        return []
    
    def create_memory_association(self, source_id: str, target_id: str, strength: float = 0.5) -> bool:
        """
        Create an association between two memories.
        
        Args:
            source_id: ID of the source memory
            target_id: ID of the target memory
            strength: Association strength (0.0 to 1.0)
            
        Returns:
            bool: True if successful
        """
        if not self.associative_memory:
            logger.warning("Associative memory not available")
            return False
        
        return self.associative_memory.create_association(source_id, target_id, strength)
    
    # Knowledge Synchronization Methods
    
    def sync_knowledge(self, node_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Manually synchronize knowledge between individual and shared graphs.
        
        Args:
            node_types: Optional list of node types to synchronize
            
        Returns:
            Dict: Synchronization results
        """
        if not self.knowledge_synchronizer:
            logger.warning("Knowledge synchronizer not available")
            return {"error": "Knowledge synchronizer not available"}
        
        if node_types:
            return self.knowledge_synchronizer.sync_specific_nodes(node_types)
        else:
            return self.knowledge_synchronizer.sync_all()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get the current knowledge synchronization status.
        
        Returns:
            Dict: Synchronization status
        """
        if not self.knowledge_synchronizer:
            logger.warning("Knowledge synchronizer not available")
            return {"status": "unavailable"}
        
        return self.knowledge_synchronizer.get_sync_status()
    
    # System Status Methods
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of all system components.
        
        Returns:
            Dict: System status information
        """
        status = {
            "agent_id": self.agent_id,
            "components": {
                "dual_knowledge": self.dual_knowledge_manager is not None,
                "events_node": self.events_node is not None,
                "associative_memory": self.associative_memory is not None,
                "event_processor": self.event_processor is not None,
                "knowledge_synchronizer": self.knowledge_synchronizer is not None
            }
        }
        
        # Add event processor status if available
        if self.event_processor:
            status["event_processor"] = {
                "running": self.event_processor.running,
                "queue": self.event_processor.get_queue_stats(),
                "handlers": self.event_processor.get_active_handlers(),
                "correlation_rules": self.event_processor.get_correlation_rules()
            }
        
        # Add synchronizer status if available
        if self.knowledge_synchronizer:
            status["knowledge_synchronizer"] = self.knowledge_synchronizer.get_sync_status()
        
        # Add associative memory stats if available
        if self.associative_memory:
            status["associative_memory"] = self.associative_memory.get_memory_stats()
        
        return status
