"""
Digital Genome Architecture Demo Script.

This script demonstrates the key functionalities of the Digital Genome Architecture:
1. Dual Knowledge Architecture
2. Event Tracking and Processing
3. Associative Memory
4. Knowledge Synchronization

Usage:
    python demo_digital_genome.py [--shared]
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime, timedelta
import threading
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)

logger = logging.getLogger("digital_genome_demo")

# Import Digital Genome components
from infrastructure.knowledge_fabric.digital_genome_manager import DigitalGenomeManager
from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType


class DigitalGenomeDemo:
    """Demo class for the Digital Genome Architecture."""
    
    def __init__(self, use_shared=False):
        """
        Initialize the Digital Genome Demo.
        
        Args:
            use_shared: Whether to use a shared knowledge graph
        """
        self.use_shared = use_shared
        self.genome_managers = {}
        self.stop_event = threading.Event()
        
        logger.info(f"Initializing Digital Genome Demo (Shared Graph: {use_shared})")
        
        # Load Neo4j configuration
        self.neo4j_config = self._load_neo4j_config()
        
        # Initialize genome managers for demo agents
        self._init_genome_managers()
    
    def _load_neo4j_config(self):
        """Load Neo4j configuration from environment variables."""
        # Load configuration from environment variables
        config = {
            "individual": {
                "uri": os.getenv("NEO4J_URI"),
                "username": os.getenv("NEO4J_USERNAME"),
                "password": os.getenv("NEO4J_PASSWORD"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j")
            },
            "shared": None
        }
        
        # Add shared config if enabled
        if self.use_shared:
            config["shared"] = {
                "uri": os.getenv("NEO4J_SHARED_URI", os.getenv("NEO4J_URI")),
                "username": os.getenv("NEO4J_SHARED_USERNAME", os.getenv("NEO4J_USERNAME")),
                "password": os.getenv("NEO4J_SHARED_PASSWORD", os.getenv("NEO4J_PASSWORD")),
                "database": os.getenv("NEO4J_SHARED_DATABASE", os.getenv("NEO4J_DATABASE", "neo4j"))
            }
        
        return config
    
    def _init_genome_managers(self):
        """Initialize Digital Genome Managers for demo agents."""
        # Define demo agents
        agents = [
            {
                "id": "agent_1",
                "name": "OrchestratorAgent",
                "layer": "orchestration"
            },
            {
                "id": "agent_2",
                "name": "ArchitectAgent",
                "layer": "planning"
            },
            {
                "id": "agent_3",
                "name": "DeveloperAgent",
                "layer": "development"
            }
        ]
        
        # Create genome manager for each agent
        for agent in agents:
            shared_config = self.neo4j_config["shared"] if self.use_shared else None
            
            genome_manager = DigitalGenomeManager(
                agent_id=agent["id"],
                individual_connection_config=self.neo4j_config["individual"],
                shared_connection_config=shared_config,
                enable_events=True,
                enable_associative_memory=True,
                auto_sync=self.use_shared,
                sync_interval_minutes=1  # Short interval for demo
            )
            
            # Register demo event handlers
            genome_manager.register_event_handler("agent_action", self._handle_agent_action)
            genome_manager.register_event_handler("system_event", self._handle_system_event)
            
            # Store manager
            self.genome_managers[agent["id"]] = {
                "manager": genome_manager,
                "info": agent
            }
        
        logger.info(f"Initialized {len(self.genome_managers)} Digital Genome Managers")
    
    def _handle_agent_action(self, event, event_id):
        """Handle agent action events."""
        agent_id = event["metadata"].get("agent_id", "unknown")
        action_type = event["metadata"].get("action_type", "unknown")
        success = event["metadata"].get("success", False)
        
        logger.info(f"Agent Action: {agent_id} performed {action_type} (Success: {success})")
    
    def _handle_system_event(self, event, event_id):
        """Handle system events."""
        component = event["metadata"].get("component", "unknown")
        event_type = event["metadata"].get("event_type", "unknown")
        severity = event["metadata"].get("severity", "info")
        
        logger.info(f"System Event: {component} - {event_type} [{severity}]")
    
    def start(self):
        """Start the demo."""
        logger.info("Starting Digital Genome Demo")
        
        # Start all genome managers
        for agent_id, data in self.genome_managers.items():
            data["manager"].start()
        
        # Start demo activity
        self.demo_thread = threading.Thread(target=self._run_demo)
        self.demo_thread.daemon = True
        self.demo_thread.start()
        
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
    
    def stop(self):
        """Stop the demo."""
        logger.info("Stopping Digital Genome Demo")
        
        # Signal demo thread to stop
        self.stop_event.set()
        
        # Stop all genome managers
        for agent_id, data in self.genome_managers.items():
            data["manager"].stop()
        
        logger.info("Digital Genome Demo stopped")
    
    def _run_demo(self):
        """Run the demo activities."""
        logger.info("Starting demo activities")
        
        # Demo sequence
        demo_steps = [
            self._demo_emit_events,
            self._demo_store_memories,
            self._demo_associative_memory,
        ]
        
        if self.use_shared:
            demo_steps.append(self._demo_knowledge_sync)
        
        # Run each demo step
        for step in demo_steps:
            if self.stop_event.is_set():
                break
                
            try:
                step()
                time.sleep(2)  # Pause between demo steps
            except Exception as e:
                logger.error(f"Error in demo step {step.__name__}: {str(e)}")
        
        logger.info("Demo activities completed")
    
    def _demo_emit_events(self):
        """Demonstrate event emission and processing."""
        logger.info("=== DEMO: Event Emission and Processing ===")
        
        # Sample agent actions
        actions = [
            {"action": "code_generation", "success": True},
            {"action": "code_review", "success": True},
            {"action": "deployment", "success": False},
            {"action": "testing", "success": True},
            {"action": "documentation", "success": True}
        ]
        
        # Emit events from each agent
        for agent_id, data in self.genome_managers.items():
            genome_manager = data["manager"]
            agent_info = data["info"]
            
            # Emit agent action events
            for action in actions:
                event_metadata = {
                    "agent_id": agent_id,
                    "agent_name": agent_info["name"],
                    "agent_layer": agent_info["layer"],
                    "action_type": action["action"],
                    "success": action["success"],
                    "inputs": {"sample": "input data"},
                    "outputs": {"sample": "output data"}
                }
                
                event_id = genome_manager.emit_event(
                    event_type="agent_action",
                    metadata=event_metadata,
                    context={"demo": True, "timestamp": datetime.now().isoformat()}
                )
                
                logger.info(f"Emitted event: {agent_id} - {action['action']} (ID: {event_id})")
                time.sleep(0.5)  # Small delay between events
        
        logger.info("Completed event emission demo")
    
    def _demo_store_memories(self):
        """Demonstrate memory storage."""
        logger.info("=== DEMO: Memory Storage ===")
        
        # Sample memories
        memories = [
            {
                "content": {"code_pattern": "Factory Method", "language": "Python"},
                "context": {"project": "Digital Genome", "component": "Agent Design"},
                "memory_type": "code_pattern",
                "importance": 0.8
            },
            {
                "content": {"decision": "Use Neo4j for knowledge storage", "rationale": "Graph database fits the knowledge model"},
                "context": {"project": "Digital Genome", "component": "Infrastructure"},
                "memory_type": "decision",
                "importance": 0.9
            },
            {
                "content": {"dependency": "pandas", "version": "1.3.0", "purpose": "Data manipulation"},
                "context": {"project": "Digital Genome", "component": "Data Processing"},
                "memory_type": "dependency",
                "importance": 0.6
            }
        ]
        
        # Store memories in each agent
        memory_ids = {}
        for agent_id, data in self.genome_managers.items():
            genome_manager = data["manager"]
            agent_memory_ids = []
            
            # Store memories
            for memory in memories:
                memory_id = genome_manager.store_memory(
                    content=memory["content"],
                    context=memory["context"],
                    memory_type=memory["memory_type"],
                    importance=memory["importance"]
                )
                
                agent_memory_ids.append(memory_id)
                logger.info(f"Stored memory: {agent_id} - {memory['memory_type']} (ID: {memory_id})")
                time.sleep(0.5)  # Small delay between memory storage
            
            memory_ids[agent_id] = agent_memory_ids
        
        # Store as instance variable for other demos
        self.memory_ids = memory_ids
        logger.info("Completed memory storage demo")
    
    def _demo_associative_memory(self):
        """Demonstrate associative memory capabilities."""
        logger.info("=== DEMO: Associative Memory ===")
        
        # Skip if no memories stored
        if not hasattr(self, 'memory_ids'):
            logger.warning("No memories available for associative memory demo")
            return
        
        # For each agent, demonstrate memory operations
        for agent_id, data in self.genome_managers.items():
            genome_manager = data["manager"]
            agent_memory_ids = self.memory_ids.get(agent_id, [])
            
            if not agent_memory_ids:
                continue
            
            # 1. Recall specific memory
            memory_id = agent_memory_ids[0]
            memory = genome_manager.recall_memory(memory_id=memory_id)
            
            if memory:
                logger.info(f"Recalled memory: {agent_id} - {memory_id}")
                logger.info(f"  Content: {memory.get('content', 'N/A')}")
            
            # 2. Recall by context
            memories = genome_manager.recall_memory(
                query_context={"project": "Digital Genome"}
            )
            
            logger.info(f"Found {len(memories)} memories by context for {agent_id}")
            
            # 3. Create associations between memories
            if len(agent_memory_ids) >= 2:
                source_id = agent_memory_ids[0]
                target_id = agent_memory_ids[1]
                
                success = genome_manager.create_memory_association(
                    source_id=source_id,
                    target_id=target_id,
                    strength=0.7
                )
                
                if success:
                    logger.info(f"Created memory association: {source_id} -> {target_id}")
            
            time.sleep(1)  # Pause between agents
        
        logger.info("Completed associative memory demo")
    
    def _demo_knowledge_sync(self):
        """Demonstrate knowledge synchronization (only if shared graph enabled)."""
        if not self.use_shared:
            return
            
        logger.info("=== DEMO: Knowledge Synchronization ===")
        
        # For demonstration, manually trigger sync for each agent
        for agent_id, data in self.genome_managers.items():
            genome_manager = data["manager"]
            
            # Get sync status before
            before_status = genome_manager.get_sync_status()
            logger.info(f"Sync status before for {agent_id}: {before_status}")
            
            # Trigger manual sync
            sync_result = genome_manager.sync_knowledge()
            
            logger.info(f"Manual sync for {agent_id}:")
            logger.info(f"  To shared: {sync_result.get('to_shared', {}).get('nodes_synced', 0)} nodes")
            logger.info(f"  From shared: {sync_result.get('from_shared', {}).get('nodes_synced', 0)} nodes")
            
            # Pause to allow scheduled sync to run
            time.sleep(3)
            
            # Get sync status after
            after_status = genome_manager.get_sync_status()
            logger.info(f"Sync status after for {agent_id}: {after_status}")
            
            time.sleep(1)  # Pause between agents
        
        logger.info("Completed knowledge synchronization demo")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Digital Genome Architecture Demo")
    parser.add_argument("--shared", action="store_true", help="Enable shared knowledge graph")
    args = parser.parse_args()
    
    # Create and run demo
    demo = DigitalGenomeDemo(use_shared=args.shared)
    
    try:
        demo.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        demo.stop()
