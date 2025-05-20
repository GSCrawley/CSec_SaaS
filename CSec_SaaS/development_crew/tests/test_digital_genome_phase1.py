"""
Test script for Digital Genome Architecture Phase 1 components.

This script tests the core components implemented in Phase 1:
1. Dual Knowledge Manager
2. Events Node
3. Associative Memory
4. Event Processor
5. Knowledge Synchronizer
6. Digital Genome Manager (integration)
"""

import os
import sys
import time
import unittest
import logging
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.knowledge_fabric.core.dual_knowledge import DualKnowledgeManager
from infrastructure.knowledge_fabric.core.events_node import EventsNode
from infrastructure.knowledge_fabric.core.associative_memory import AssociativeMemory, MemoryRecord
from infrastructure.knowledge_fabric.services.event_processor import EventProcessor
from infrastructure.knowledge_fabric.services.knowledge_synchronizer import KnowledgeSynchronizer
from infrastructure.knowledge_fabric.digital_genome_manager import DigitalGenomeManager
from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType


class TestDualKnowledge(unittest.TestCase):
    """Test cases for DualKnowledgeManager."""
    
    def setUp(self):
        # Create mock Neo4j connections
        self.shared_connection = MagicMock()
        self.individual_connection = MagicMock()
        
        # Mock connection creation
        with patch.object(DualKnowledgeManager, '_create_individual_connection') as mock_create:
            mock_create.return_value = self.individual_connection
            self.dual_knowledge = DualKnowledgeManager(self.shared_connection, "test_agent")
    
    def test_init(self):
        """Test initialization of DualKnowledgeManager."""
        self.assertEqual(self.dual_knowledge.agent_id, "test_agent")
        self.assertEqual(self.dual_knowledge.shared_connection, self.shared_connection)
        self.assertEqual(self.dual_knowledge.individual_connection, self.individual_connection)
    
    def test_sync_to_shared(self):
        """Test synchronization from individual to shared graph."""
        # Mock individual nodes
        mock_nodes = [
            {"id": "1", "type": "TestNode", "properties": {"name": "Test", "updated_at": datetime.now().isoformat()}}
        ]
        self.individual_connection.query.return_value = mock_nodes
        
        # Mock find matching node - no match
        self.dual_knowledge._find_matching_node = MagicMock(return_value=None)
        
        # Mock create node
        self.dual_knowledge._create_shared_node = MagicMock()
        
        # Mock get relationships - empty
        self.dual_knowledge._get_node_relationships = MagicMock(return_value=[])
        
        # Call sync
        result = self.dual_knowledge.sync_to_shared()
        
        # Verify query was called
        self.individual_connection.query.assert_called_once()
        
        # Verify node creation was attempted
        self.dual_knowledge._create_shared_node.assert_called_once()
        
        # Verify result
        self.assertEqual(result["nodes_synced"], 1)
        self.assertEqual(result["relationships_synced"], 0)
    
    def test_sync_from_shared(self):
        """Test synchronization from shared to individual graph."""
        # Mock shared nodes
        mock_nodes = [
            {"id": "1", "type": "TestNode", "properties": {"name": "Test", "updated_at": datetime.now().isoformat()}}
        ]
        self.shared_connection.query.return_value = mock_nodes
        
        # Mock find matching node - no match
        self.dual_knowledge._find_matching_individual_node = MagicMock(return_value=None)
        
        # Mock create node
        self.dual_knowledge._create_individual_node = MagicMock()
        
        # Mock get relationships - empty
        self.dual_knowledge._get_shared_node_relationships = MagicMock(return_value=[])
        
        # Call sync
        result = self.dual_knowledge.sync_from_shared()
        
        # Verify query was called
        self.shared_connection.query.assert_called_once()
        
        # Verify node creation was attempted
        self.dual_knowledge._create_individual_node.assert_called_once()
        
        # Verify result
        self.assertEqual(result["nodes_synced"], 1)
        self.assertEqual(result["relationships_synced"], 0)


class TestEventsNode(unittest.TestCase):
    """Test cases for EventsNode."""
    
    def setUp(self):
        self.knowledge_manager = MagicMock()
        self.events_node = EventsNode(self.knowledge_manager)
    
    def test_log_event(self):
        """Test logging an event."""
        # Setup mock
        self.knowledge_manager.create_node.return_value = "event_id_123"
        
        # Log event
        event_type = "test_event"
        metadata = {"test_key": "test_value"}
        result = self.events_node.log_event(event_type, metadata)
        
        # Verify node was created
        self.knowledge_manager.create_node.assert_called_once()
        self.assertEqual(result, "event_id_123")
    
    def test_log_agent_action(self):
        """Test logging an agent action event."""
        # Setup mock
        self.knowledge_manager.create_node.return_value = "event_id_456"
        
        # Log action
        agent_id = "test_agent"
        action_type = "test_action"
        inputs = {"input_key": "input_value"}
        outputs = {"output_key": "output_value"}
        
        result = self.events_node.log_agent_action(
            agent_id, action_type, inputs, outputs, True
        )
        
        # Verify event was logged
        self.knowledge_manager.create_node.assert_called_once()
        self.assertEqual(result, "event_id_456")
    
    def test_find_related_events(self):
        """Test finding events related to a node."""
        # Setup mock response
        mock_events = [{"id": "event1", "type": "test_event"}]
        self.knowledge_manager.query.return_value = mock_events
        
        # Find related events
        node_id = "test_node_id"
        result = self.events_node.find_related_events(node_id)
        
        # Verify query was called
        self.knowledge_manager.query.assert_called_once()
        
        # Verify result
        self.assertEqual(result, mock_events)


class TestAssociativeMemory(unittest.TestCase):
    """Test cases for AssociativeMemory."""
    
    def setUp(self):
        self.knowledge_manager = MagicMock()
        self.events_node = MagicMock()
        self.associative_memory = AssociativeMemory(self.knowledge_manager, self.events_node)
    
    def test_store_memory(self):
        """Test storing a memory."""
        # Setup mock
        self.knowledge_manager.create_node.return_value = "memory_id_123"
        
        # Store memory
        content = {"content_key": "content_value"}
        context = {"context_key": "context_value"}
        memory_type = "test_memory"
        
        result = self.associative_memory.store_memory(content, context, memory_type)
        
        # Verify node was created
        self.knowledge_manager.create_node.assert_called_once()
        self.assertEqual(result, "memory_id_123")
    
    def test_memory_record(self):
        """Test MemoryRecord class."""
        # Create memory record
        memory = MemoryRecord(
            id="mem_123",
            content={"test": "content"},
            context={"test": "context"},
            memory_type="test",
            timestamp=datetime.now(),
            importance=0.75
        )
        
        # Test to_dict
        memory_dict = memory.to_dict()
        self.assertEqual(memory_dict["id"], "mem_123")
        self.assertEqual(memory_dict["importance"], 0.75)
        
        # Test from_dict
        reconstructed = MemoryRecord.from_dict(memory_dict)
        self.assertEqual(reconstructed.id, memory.id)
        self.assertEqual(reconstructed.importance, memory.importance)
        
        # Test access
        old_access_count = memory.access_count
        memory.access()
        self.assertEqual(memory.access_count, old_access_count + 1)


class TestEventProcessor(unittest.TestCase):
    """Test cases for EventProcessor."""
    
    def setUp(self):
        self.events_node = MagicMock()
        self.associative_memory = MagicMock()
        self.event_processor = EventProcessor(
            self.events_node,
            self.associative_memory,
            max_queue_size=10,
            worker_threads=1
        )
    
    def test_emit_event_urgent(self):
        """Test emitting an urgent event."""
        # Setup mocks
        self.events_node.log_event.return_value = "event_id_789"
        
        # Emit urgent event
        event_type = "urgent_event"
        metadata = {"urgent": True}
        
        result = self.event_processor.emit_event(
            event_type, metadata, urgent=True
        )
        
        # Verify event was logged immediately
        self.events_node.log_event.assert_called_once()
        self.assertEqual(result, "event_id_789")
    
    def test_register_handler(self):
        """Test registering an event handler."""
        # Create mock handler
        handler = MagicMock()
        
        # Register handler
        event_type = "test_event"
        result = self.event_processor.register_handler(event_type, handler)
        
        # Verify registration
        self.assertTrue(result)
        self.assertIn(event_type, self.event_processor.event_handlers)
        self.assertEqual(len(self.event_processor.event_handlers[event_type]), 1)
    
    def test_start_stop(self):
        """Test starting and stopping the event processor."""
        # Start processor
        start_result = self.event_processor.start()
        
        # Verify started
        self.assertTrue(start_result)
        self.assertTrue(self.event_processor.running)
        
        # Stop processor
        stop_result = self.event_processor.stop()
        
        # Verify stopped
        self.assertTrue(stop_result)
        self.assertFalse(self.event_processor.running)


class TestKnowledgeSynchronizer(unittest.TestCase):
    """Test cases for KnowledgeSynchronizer."""
    
    def setUp(self):
        self.dual_knowledge_manager = MagicMock()
        self.dual_knowledge_manager.agent_id = "test_agent"
        self.events_node = MagicMock()
        self.synchronizer = KnowledgeSynchronizer(
            self.dual_knowledge_manager,
            self.events_node
        )
    
    def test_update_sync_schedule(self):
        """Test updating the sync schedule."""
        # Update schedule
        interval = 30
        priority_types = ["Event", "RedFlag"]
        
        result = self.synchronizer.update_sync_schedule(
            interval_minutes=interval,
            priority_node_types=priority_types
        )
        
        # Verify update
        self.assertEqual(result["interval_minutes"], interval)
        self.assertEqual(result["priority_node_types"], priority_types)
    
    def test_sync_priority_nodes(self):
        """Test synchronizing priority nodes."""
        # Setup mocks
        self.dual_knowledge_manager.sync_to_shared.return_value = {"nodes_synced": 5}
        self.dual_knowledge_manager.sync_from_shared.return_value = {"nodes_synced": 3}
        
        # Sync priority nodes
        result = self.synchronizer.sync_priority_nodes()
        
        # Verify sync calls
        self.dual_knowledge_manager.sync_to_shared.assert_called_once()
        self.dual_knowledge_manager.sync_from_shared.assert_called_once()
        
        # Verify results
        self.assertEqual(result["to_shared"]["nodes_synced"], 5)
        self.assertEqual(result["from_shared"]["nodes_synced"], 3)


class TestDigitalGenomeManager(unittest.TestCase):
    """Test cases for DigitalGenomeManager."""
    
    def setUp(self):
        # Setup mocks for components
        self.individual_connection = MagicMock()
        self.shared_connection = MagicMock()
        self.dual_knowledge = MagicMock()
        self.events_node = MagicMock()
        self.associative_memory = MagicMock()
        self.event_processor = MagicMock()
        self.knowledge_synchronizer = MagicMock()
        
        # Setup connection patches
        with patch('infrastructure.knowledge_fabric.digital_genome_manager.Neo4jConnection') as mock_neo4j, \
             patch('infrastructure.knowledge_fabric.digital_genome_manager.DualKnowledgeManager') as mock_dual, \
             patch('infrastructure.knowledge_fabric.digital_genome_manager.EventsNode') as mock_events, \
             patch('infrastructure.knowledge_fabric.digital_genome_manager.AssociativeMemory') as mock_memory, \
             patch('infrastructure.knowledge_fabric.digital_genome_manager.EventProcessor') as mock_processor, \
             patch('infrastructure.knowledge_fabric.digital_genome_manager.KnowledgeSynchronizer') as mock_sync:
            
            # Configure mocks
            mock_neo4j.side_effect = [self.individual_connection, self.shared_connection]
            mock_dual.return_value = self.dual_knowledge
            mock_events.return_value = self.events_node
            mock_memory.return_value = self.associative_memory
            mock_processor.return_value = self.event_processor
            mock_sync.return_value = self.knowledge_synchronizer
            
            # Create manager
            self.genome_manager = DigitalGenomeManager(
                agent_id="test_agent",
                individual_connection_config={"uri": "neo4j://localhost:7687"},
                shared_connection_config={"uri": "neo4j://shared:7687"}
            )
    
    def test_initialization(self):
        """Test initialization of DigitalGenomeManager."""
        self.assertEqual(self.genome_manager.agent_id, "test_agent")
        self.assertIsNotNone(self.genome_manager.events_node)
        self.assertIsNotNone(self.genome_manager.associative_memory)
        self.assertIsNotNone(self.genome_manager.event_processor)
        self.assertIsNotNone(self.genome_manager.knowledge_synchronizer)
    
    def test_start_stop(self):
        """Test starting and stopping the genome manager."""
        # Configure mocks
        self.event_processor.start.return_value = True
        self.event_processor.stop.return_value = True
        self.knowledge_synchronizer.start_scheduled_sync.return_value = True
        self.knowledge_synchronizer.stop_scheduled_sync.return_value = True
        
        # Start manager
        start_result = self.genome_manager.start()
        
        # Verify components started
        self.assertTrue(start_result)
        self.event_processor.start.assert_called_once()
        self.knowledge_synchronizer.start_scheduled_sync.assert_called_once()
        
        # Stop manager
        stop_result = self.genome_manager.stop()
        
        # Verify components stopped
        self.assertTrue(stop_result)
        self.event_processor.stop.assert_called_once()
        self.knowledge_synchronizer.stop_scheduled_sync.assert_called_once()
    
    def test_emit_event(self):
        """Test emitting an event through the manager."""
        # Configure mock
        self.event_processor.emit_event.return_value = "event_id_999"
        
        # Emit event
        event_type = "test_event"
        metadata = {"test": "data"}
        
        result = self.genome_manager.emit_event(event_type, metadata)
        
        # Verify event emitted
        self.assertEqual(result, "event_id_999")
        self.event_processor.emit_event.assert_called_once_with(
            event_type=event_type,
            metadata=metadata,
            related_nodes=None,
            context=None,
            urgent=False
        )
    
    def test_store_recall_memory(self):
        """Test storing and recalling memory through the manager."""
        # Configure mocks
        self.associative_memory.store_memory.return_value = "memory_id_123"
        self.associative_memory.recall_by_id.return_value = MagicMock(to_dict=lambda: {"id": "memory_id_123"})
        
        # Store memory
        content = {"test": "content"}
        context = {"test": "context"}
        
        memory_id = self.genome_manager.store_memory(
            content=content,
            context=context,
            memory_type="test"
        )
        
        # Verify memory stored
        self.assertEqual(memory_id, "memory_id_123")
        
        # Recall memory
        memory = self.genome_manager.recall_memory(memory_id=memory_id)
        
        # Verify memory recalled
        self.assertEqual(memory["id"], memory_id)
    
    def test_sync_knowledge(self):
        """Test knowledge synchronization through the manager."""
        # Configure mock
        self.knowledge_synchronizer.sync_all.return_value = {
            "to_shared": {"nodes_synced": 10},
            "from_shared": {"nodes_synced": 5}
        }
        
        # Sync knowledge
        result = self.genome_manager.sync_knowledge()
        
        # Verify sync performed
        self.knowledge_synchronizer.sync_all.assert_called_once()
        self.assertEqual(result["to_shared"]["nodes_synced"], 10)
        self.assertEqual(result["from_shared"]["nodes_synced"], 5)
    
    def test_get_system_status(self):
        """Test getting system status from the manager."""
        # Configure mocks
        self.event_processor.get_queue_stats.return_value = {"queue_size": 0}
        self.event_processor.get_active_handlers.return_value = {"test_event": 1}
        self.event_processor.get_correlation_rules.return_value = [{"pattern": ["a", "b"]}]
        self.knowledge_synchronizer.get_sync_status.return_value = {"scheduler_running": True}
        self.associative_memory.get_memory_stats.return_value = {"total_memories": 50}
        
        # Get status
        status = self.genome_manager.get_system_status()
        
        # Verify components status included
        self.assertEqual(status["agent_id"], "test_agent")
        self.assertTrue(status["components"]["dual_knowledge"])
        self.assertTrue(status["components"]["events_node"])
        self.assertTrue(status["components"]["associative_memory"])
        self.assertEqual(status["event_processor"]["queue"]["queue_size"], 0)
        self.assertEqual(status["knowledge_synchronizer"]["scheduler_running"], True)
        self.assertEqual(status["associative_memory"]["total_memories"], 50)


if __name__ == '__main__':
    unittest.main()
