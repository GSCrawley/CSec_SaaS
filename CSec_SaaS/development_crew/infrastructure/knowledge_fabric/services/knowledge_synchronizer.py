"""
Knowledge Synchronizer Module for Digital Genome Architecture.

This module provides automatic and scheduled synchronization between
individual agent knowledge graphs and the shared knowledge fabric.
"""

import logging
import time
import threading
import schedule
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta

from infrastructure.knowledge_fabric.core.dual_knowledge import DualKnowledgeManager
from infrastructure.knowledge_fabric.core.schema import NodeLabel
from infrastructure.knowledge_fabric.core.events_node import EventsNode

logger = logging.getLogger(__name__)

class KnowledgeSynchronizer:
    """
    Manages synchronization between individual and shared knowledge graphs.
    
    The KnowledgeSynchronizer is responsible for:
    1. Scheduling periodic synchronization of knowledge
    2. Detecting and resolving conflicts during synchronization
    3. Tracking synchronization events and history
    4. Providing real-time sync on critical updates
    """
    
    def __init__(self, dual_knowledge_manager: DualKnowledgeManager, events_node: Optional[EventsNode] = None):
        """
        Initialize the knowledge synchronizer.
        
        Args:
            dual_knowledge_manager: Manager for dual knowledge architecture
            events_node: Optional events node for logging sync events
        """
        self.dual_knowledge_manager = dual_knowledge_manager
        self.events_node = events_node
        self.agent_id = dual_knowledge_manager.agent_id
        self._sync_thread = None
        self._stop_sync = threading.Event()
        self.sync_schedule = {
            "interval_minutes": 15,
            "priority_node_types": [
                NodeLabel.EVENT.value,
                NodeLabel.RED_FLAG.value
            ]
        }
        self.last_sync = {
            "to_shared": {},
            "from_shared": {}
        }
        
    def start_scheduled_sync(self):
        """
        Start the scheduled synchronization thread.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self._sync_thread and self._sync_thread.is_alive():
            logger.warning(f"Sync thread for agent {self.agent_id} already running")
            return False
        
        self._stop_sync.clear()
        self._sync_thread = threading.Thread(target=self._run_sync_scheduler)
        self._sync_thread.daemon = True
        self._sync_thread.start()
        
        if self.events_node:
            self.events_node.log_system_event(
                component="KnowledgeSynchronizer",
                event_type="scheduler_started",
                details={
                    "agent_id": self.agent_id,
                    "interval_minutes": self.sync_schedule["interval_minutes"]
                }
            )
        
        logger.info(f"Started scheduled sync for agent {self.agent_id} every {self.sync_schedule['interval_minutes']} minutes")
        return True
    
    def stop_scheduled_sync(self):
        """
        Stop the scheduled synchronization thread.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self._sync_thread or not self._sync_thread.is_alive():
            logger.warning(f"No active sync thread for agent {self.agent_id}")
            return False
        
        self._stop_sync.set()
        self._sync_thread.join(timeout=5)
        
        if self.events_node:
            self.events_node.log_system_event(
                component="KnowledgeSynchronizer",
                event_type="scheduler_stopped",
                details={
                    "agent_id": self.agent_id
                }
            )
        
        logger.info(f"Stopped scheduled sync for agent {self.agent_id}")
        return True
    
    def _run_sync_scheduler(self):
        """Run the synchronization scheduler thread."""
        # Schedule regular sync
        interval_mins = self.sync_schedule["interval_minutes"]
        schedule.every(interval_mins).minutes.do(self.sync_all)
        
        # Schedule priority sync more frequently (1/3 of regular interval)
        priority_interval = max(1, interval_mins // 3)
        schedule.every(priority_interval).minutes.do(self.sync_priority_nodes)
        
        while not self._stop_sync.is_set():
            schedule.run_pending()
            time.sleep(1)
    
    def sync_all(self):
        """
        Synchronize all knowledge between individual and shared knowledge graphs.
        
        Returns:
            Dict: Summary of synchronization
        """
        try:
            # First sync from individual to shared
            to_shared_result = self.dual_knowledge_manager.sync_to_shared()
            
            # Then sync from shared to individual
            from_shared_result = self.dual_knowledge_manager.sync_from_shared()
            
            # Update last sync timestamps
            now = datetime.now()
            self.last_sync["to_shared"]["all"] = now
            self.last_sync["from_shared"]["all"] = now
            
            # Log sync event
            if self.events_node:
                self.events_node.log_system_event(
                    component="KnowledgeSynchronizer",
                    event_type="sync_completed",
                    details={
                        "agent_id": self.agent_id,
                        "to_shared": to_shared_result,
                        "from_shared": from_shared_result,
                        "timestamp": now.isoformat()
                    }
                )
            
            logger.info(f"Completed full sync for agent {self.agent_id}")
            
            combined_result = {
                "to_shared": to_shared_result,
                "from_shared": from_shared_result,
                "timestamp": now.isoformat()
            }
            
            return combined_result
            
        except Exception as e:
            error_msg = f"Sync error for agent {self.agent_id}: {str(e)}"
            logger.error(error_msg)
            
            # Log error event
            if self.events_node:
                self.events_node.log_system_event(
                    component="KnowledgeSynchronizer",
                    event_type="sync_error",
                    details={
                        "agent_id": self.agent_id,
                        "error": str(e)
                    },
                    severity="error"
                )
                
            return {"error": error_msg}
    
    def sync_priority_nodes(self):
        """
        Synchronize priority node types between individual and shared knowledge graphs.
        
        Returns:
            Dict: Summary of synchronization
        """
        try:
            priority_types = self.sync_schedule["priority_node_types"]
            
            # First sync priority nodes from individual to shared
            to_shared_result = self.dual_knowledge_manager.sync_to_shared(priority_types)
            
            # Then sync priority nodes from shared to individual
            from_shared_result = self.dual_knowledge_manager.sync_from_shared(priority_types)
            
            # Update last sync timestamps
            now = datetime.now()
            self.last_sync["to_shared"]["priority"] = now
            self.last_sync["from_shared"]["priority"] = now
            
            # Log sync event
            if self.events_node:
                self.events_node.log_system_event(
                    component="KnowledgeSynchronizer",
                    event_type="priority_sync_completed",
                    details={
                        "agent_id": self.agent_id,
                        "node_types": priority_types,
                        "to_shared": to_shared_result,
                        "from_shared": from_shared_result,
                        "timestamp": now.isoformat()
                    }
                )
            
            logger.info(f"Completed priority sync for agent {self.agent_id}")
            
            combined_result = {
                "node_types": priority_types,
                "to_shared": to_shared_result,
                "from_shared": from_shared_result,
                "timestamp": now.isoformat()
            }
            
            return combined_result
            
        except Exception as e:
            error_msg = f"Priority sync error for agent {self.agent_id}: {str(e)}"
            logger.error(error_msg)
            
            # Log error event
            if self.events_node:
                self.events_node.log_system_event(
                    component="KnowledgeSynchronizer",
                    event_type="sync_error",
                    details={
                        "agent_id": self.agent_id,
                        "error": str(e),
                        "node_types": self.sync_schedule["priority_node_types"]
                    },
                    severity="error"
                )
                
            return {"error": error_msg}
    
    def sync_specific_nodes(self, node_types: List[str]):
        """
        Synchronize specific node types between individual and shared knowledge graphs.
        
        Args:
            node_types: List of node types to synchronize
            
        Returns:
            Dict: Summary of synchronization
        """
        try:
            # First sync specific nodes from individual to shared
            to_shared_result = self.dual_knowledge_manager.sync_to_shared(node_types)
            
            # Then sync specific nodes from shared to individual
            from_shared_result = self.dual_knowledge_manager.sync_from_shared(node_types)
            
            # Update last sync timestamps
            now = datetime.now()
            for node_type in node_types:
                self.last_sync["to_shared"][node_type] = now
                self.last_sync["from_shared"][node_type] = now
            
            # Log sync event
            if self.events_node:
                self.events_node.log_system_event(
                    component="KnowledgeSynchronizer",
                    event_type="specific_sync_completed",
                    details={
                        "agent_id": self.agent_id,
                        "node_types": node_types,
                        "to_shared": to_shared_result,
                        "from_shared": from_shared_result,
                        "timestamp": now.isoformat()
                    }
                )
            
            logger.info(f"Completed specific sync for agent {self.agent_id}: {node_types}")
            
            combined_result = {
                "node_types": node_types,
                "to_shared": to_shared_result,
                "from_shared": from_shared_result,
                "timestamp": now.isoformat()
            }
            
            return combined_result
            
        except Exception as e:
            error_msg = f"Specific sync error for agent {self.agent_id}: {str(e)}"
            logger.error(error_msg)
            
            # Log error event
            if self.events_node:
                self.events_node.log_system_event(
                    component="KnowledgeSynchronizer",
                    event_type="sync_error",
                    details={
                        "agent_id": self.agent_id,
                        "error": str(e),
                        "node_types": node_types
                    },
                    severity="error"
                )
                
            return {"error": error_msg}
    
    def update_sync_schedule(self, interval_minutes: int = None, priority_node_types: List[str] = None):
        """
        Update the synchronization schedule.
        
        Args:
            interval_minutes: Minutes between synchronizations
            priority_node_types: List of node types to sync at higher frequency
            
        Returns:
            Dict: Updated schedule
        """
        # Update interval if provided
        if interval_minutes is not None:
            self.sync_schedule["interval_minutes"] = max(1, interval_minutes)
        
        # Update priority node types if provided
        if priority_node_types is not None:
            self.sync_schedule["priority_node_types"] = priority_node_types
        
        # Restart scheduler with new settings if running
        if self._sync_thread and self._sync_thread.is_alive():
            self.stop_scheduled_sync()
            self.start_scheduled_sync()
        
        # Log update event
        if self.events_node:
            self.events_node.log_system_event(
                component="KnowledgeSynchronizer",
                event_type="schedule_updated",
                details={
                    "agent_id": self.agent_id,
                    "new_schedule": self.sync_schedule
                }
            )
        
        logger.info(f"Updated sync schedule for agent {self.agent_id}: {self.sync_schedule}")
        
        return self.sync_schedule
    
    def get_sync_status(self):
        """
        Get the current synchronization status.
        
        Returns:
            Dict: Synchronization status information
        """
        is_running = self._sync_thread is not None and self._sync_thread.is_alive()
        
        return {
            "agent_id": self.agent_id,
            "scheduler_running": is_running,
            "schedule": self.sync_schedule,
            "last_sync": self.last_sync
        }
    
    def force_sync_now(self, specific_types: List[str] = None):
        """
        Force immediate synchronization.
        
        Args:
            specific_types: Optional list of specific node types to sync
            
        Returns:
            Dict: Synchronization results
        """
        if specific_types:
            return self.sync_specific_nodes(specific_types)
        else:
            return self.sync_all()
