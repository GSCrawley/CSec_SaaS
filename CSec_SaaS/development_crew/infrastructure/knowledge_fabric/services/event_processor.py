"""
Event Processor Module for the Digital Genome Architecture.

This module implements real-time event processing capabilities, 
including event capture, filtering, analysis, and response.
"""

import logging
import uuid
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union, Callable

from infrastructure.knowledge_fabric.core.events_node import EventsNode
from infrastructure.knowledge_fabric.core.associative_memory import AssociativeMemory
from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType

logger = logging.getLogger(__name__)

class EventProcessor:
    """
    Handles real-time processing of events in the Digital Genome Architecture.
    
    The EventProcessor is responsible for:
    1. Capturing events from various sources
    2. Processing events based on registered handlers
    3. Triggering appropriate responses to events
    4. Maintaining event history and relationships
    """
    
    def __init__(
        self, 
        events_node: EventsNode,
        associative_memory: Optional[AssociativeMemory] = None,
        max_queue_size: int = 1000,
        worker_threads: int = 2
    ):
        """
        Initialize the event processor.
        
        Args:
            events_node: The events node for storing events
            associative_memory: Optional associative memory for event context
            max_queue_size: Maximum size of the event queue
            worker_threads: Number of worker threads to process events
        """
        self.events_node = events_node
        self.associative_memory = associative_memory
        self.event_handlers = {}  # type: Dict[str, List[Callable]]
        self.event_queue = queue.Queue(maxsize=max_queue_size)
        self.worker_threads = worker_threads
        self.workers = []
        self.running = False
        self.event_filters = {}  # type: Dict[str, Callable]
        self.event_history = {}  # type: Dict[str, List[str]]  # event_type -> [event_ids]
        self.correlation_rules = []  # type: List[Dict[str, Any]]
        
    def start(self):
        """
        Start the event processing system.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Event processor already running")
            return False
        
        self.running = True
        
        # Start worker threads
        for i in range(self.worker_threads):
            worker = threading.Thread(
                target=self._event_worker,
                name=f"EventWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started event processor with {self.worker_threads} workers")
        return True
    
    def stop(self):
        """
        Stop the event processing system.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Event processor not running")
            return False
        
        self.running = False
        
        # Put None in the queue for each worker to signal shutdown
        for _ in range(self.worker_threads):
            self.event_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers = []
        logger.info("Stopped event processor")
        return True
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register a handler function for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
            
        Returns:
            bool: True if registered successfully
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
        return True
    
    def register_filter(self, filter_name: str, filter_func: Callable):
        """
        Register a filter function for events.
        
        Args:
            filter_name: Name of the filter
            filter_func: Function that returns True if event should be processed
            
        Returns:
            bool: True if registered successfully
        """
        self.event_filters[filter_name] = filter_func
        logger.info(f"Registered event filter: {filter_name}")
        return True
    
    def register_correlation_rule(self, rule: Dict[str, Any]):
        """
        Register a rule for correlating events.
        
        Args:
            rule: Dictionary with rule parameters
            
        Returns:
            bool: True if registered successfully
        """
        # Rule should contain:
        # - pattern: List of event types to match
        # - timeframe: Time window for correlation (in seconds)
        # - action: Function to call when pattern is matched
        
        if not all(key in rule for key in ["pattern", "timeframe", "action"]):
            logger.error("Invalid correlation rule format")
            return False
        
        self.correlation_rules.append(rule)
        logger.info(f"Registered correlation rule for pattern: {rule['pattern']}")
        return True
    
    def emit_event(
        self, 
        event_type: str, 
        metadata: Dict[str, Any],
        related_nodes: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        urgent: bool = False
    ):
        """
        Emit an event into the processing system.
        
        Args:
            event_type: Type of the event
            metadata: Additional data about the event
            related_nodes: Optional list of nodes related to this event
            context: Optional execution context information
            urgent: Whether to process event immediately
            
        Returns:
            str: ID of the created event or None if queued
        """
        # Create event object
        event = {
            "event_type": event_type,
            "metadata": metadata,
            "related_nodes": related_nodes,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        # Handle urgent events immediately
        if urgent:
            return self._process_event(event)
        
        # Queue regular events
        try:
            self.event_queue.put(event, block=False)
            return None
        except queue.Full:
            logger.warning("Event queue full, processing event immediately")
            return self._process_event(event)
    
    def _event_worker(self):
        """Worker thread for processing events from the queue."""
        while self.running:
            try:
                # Get event from queue
                event = self.event_queue.get(timeout=1)
                
                # Check for shutdown signal
                if event is None:
                    break
                
                # Process the event
                self._process_event(event)
                
                # Mark as done
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in event worker: {str(e)}")
    
    def _process_event(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Process a single event.
        
        Args:
            event: Event to process
            
        Returns:
            str: ID of the created event or None on failure
        """
        event_type = event["event_type"]
        
        # Apply filters
        for filter_name, filter_func in self.event_filters.items():
            try:
                if not filter_func(event):
                    logger.debug(f"Event filtered out by {filter_name}: {event_type}")
                    return None
            except Exception as e:
                logger.error(f"Error in filter {filter_name}: {str(e)}")
        
        # Create event in the knowledge graph
        try:
            event_id = self.events_node.log_event(
                event_type=event_type,
                metadata=event["metadata"],
                related_nodes=event.get("related_nodes"),
                context=event.get("context")
            )
            
            # Store in event history
            if event_type not in self.event_history:
                self.event_history[event_type] = []
            
            # Keep history limited to recent events
            history = self.event_history[event_type]
            history.append(event_id)
            if len(history) > 100:  # Limit history size
                history = history[-100:]
                self.event_history[event_type] = history
            
            # Store in associative memory
            if self.associative_memory:
                self.associative_memory.store_memory(
                    content=event["metadata"],
                    context={
                        "event_type": event_type,
                        "event_id": event_id,
                        "timestamp": event["timestamp"]
                    },
                    memory_type="event",
                    importance=0.5  # Default importance
                )
            
            # Check for correlations
            self._check_correlations(event_type, event_id, event)
            
            # Dispatch to handlers
            self._dispatch_to_handlers(event_type, event, event_id)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {str(e)}")
            return None
    
    def _dispatch_to_handlers(self, event_type: str, event: Dict[str, Any], event_id: str):
        """Dispatch an event to registered handlers."""
        # Call specific handlers for this event type
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event, event_id)
                except Exception as e:
                    logger.error(f"Error in handler for {event_type}: {str(e)}")
        
        # Call wildcard handlers
        if "*" in self.event_handlers:
            for handler in self.event_handlers["*"]:
                try:
                    handler(event, event_id)
                except Exception as e:
                    logger.error(f"Error in wildcard handler: {str(e)}")
    
    def _check_correlations(self, event_type: str, event_id: str, event: Dict[str, Any]):
        """Check for event correlations based on registered rules."""
        now = datetime.now()
        
        for rule in self.correlation_rules:
            pattern = rule["pattern"]
            timeframe = rule["timeframe"]
            
            # Skip if this event doesn't match the pattern
            if event_type not in pattern:
                continue
            
            # Find position of this event in the pattern
            event_index = pattern.index(event_type)
            
            # Check if we can find all events in the pattern
            # within the specified timeframe
            match = True
            matched_events = [None] * len(pattern)
            matched_events[event_index] = event_id
            
            # Get timestamp for this event
            event_time = datetime.fromisoformat(event["timestamp"])
            
            # Look for other events in the pattern
            for i, pattern_event_type in enumerate(pattern):
                if i == event_index:
                    continue  # Skip current event
                
                if pattern_event_type not in self.event_history:
                    match = False
                    break
                
                # Find events of the correct type within the timeframe
                found_match = False
                for other_event_id in reversed(self.event_history[pattern_event_type]):
                    # Get the other event
                    other_event = self._get_event_by_id(other_event_id)
                    if not other_event:
                        continue
                    
                    # Check if within timeframe
                    other_time = datetime.fromisoformat(other_event["timestamp"])
                    time_diff = abs((event_time - other_time).total_seconds())
                    
                    if time_diff <= timeframe:
                        matched_events[i] = other_event_id
                        found_match = True
                        break
                
                if not found_match:
                    match = False
                    break
            
            # If we found a match for the pattern, call the action
            if match:
                try:
                    rule["action"](matched_events, pattern)
                except Exception as e:
                    logger.error(f"Error in correlation rule action: {str(e)}")
    
    def _get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an event by its ID.
        
        Args:
            event_id: ID of the event
            
        Returns:
            Dict or None: Event data or None if not found
        """
        # Query the knowledge graph for the event
        query = f"""
        MATCH (e:{NodeLabel.EVENT.value})
        WHERE ID(e) = {event_id}
        RETURN e
        """
        
        result = self.events_node.knowledge_manager.query(query)
        
        if not result or not result[0].get("e"):
            return None
        
        event_data = result[0]["e"]
        return event_data
    
    def get_active_handlers(self) -> Dict[str, int]:
        """
        Get a count of active handlers by event type.
        
        Returns:
            Dict: Event types and their handler counts
        """
        return {event_type: len(handlers) for event_type, handlers in self.event_handlers.items()}
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the event queue.
        
        Returns:
            Dict: Queue statistics
        """
        return {
            "queue_size": self.event_queue.qsize(),
            "max_queue_size": self.event_queue.maxsize,
            "queue_full": self.event_queue.full(),
            "queue_empty": self.event_queue.empty(),
            "workers": self.worker_threads,
            "active_workers": len([w for w in self.workers if w.is_alive()])
        }
    
    def get_correlation_rules(self) -> List[Dict[str, Any]]:
        """
        Get a list of active correlation rules.
        
        Returns:
            List: Correlation rules
        """
        # Return a simplified version without the action function
        return [
            {
                "pattern": rule["pattern"],
                "timeframe": rule["timeframe"]
            }
            for rule in self.correlation_rules
        ]
    
    def add_event_relationship(self, source_id: str, target_id: str, relationship_type: str) -> bool:
        """
        Create a relationship between two events.
        
        Args:
            source_id: ID of the source event
            target_id: ID of the target event
            relationship_type: Type of relationship
            
        Returns:
            bool: True if created successfully
        """
        # Create relationship in the knowledge graph
        try:
            self.events_node.knowledge_manager.create_relationship(
                source_id,
                target_id,
                relationship_type,
                properties={
                    "created_at": datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error creating event relationship: {str(e)}")
            return False
