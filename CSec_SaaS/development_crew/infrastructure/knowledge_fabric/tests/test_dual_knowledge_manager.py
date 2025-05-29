"""
Test script for the DualKnowledgeManager.

This script tests the basic functionality of the DualKnowledgeManager class
by connecting to the Neo4j database and performing some operations.
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.connection import Neo4jConnection, Neo4jConfig
from core.dual_knowledge import DualKnowledgeManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dual_knowledge_manager():
    """Test the DualKnowledgeManager class."""
    logger.info("Testing DualKnowledgeManager...")
    
    # Create a Neo4j connection
    config = Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "DKMdbms!"),
        database=os.getenv("NEO4J_DATABASE", "master-graph")
    )
    
    connection = Neo4jConnection(config)
    
    # Verify connection
    if not connection.verify_connectivity():
        logger.error("Failed to connect to Neo4j database. Check your connection settings.")
        return False
    
    logger.info("Connected to Neo4j database.")
    
    # Create a DualKnowledgeManager instance
    dkm = DualKnowledgeManager(connection, agent_id="test_agent")
    
    # Test knowledge graph operations
    logger.info("Testing knowledge graph operations...")
    
    # Get the Global Knowledge Fabric
    global_kg = dkm.get_knowledge_graph("Global_Knowledge_Fabric")
    logger.info(f"Global Knowledge Fabric: {global_kg}")
    
    # Create a test knowledge graph
    test_kg = dkm.create_knowledge_graph(
        "Test_Agent_KG",
        "Local",
        "A test knowledge graph for the test agent."
    )
    logger.info(f"Created test knowledge graph: {test_kg}")
    
    # Apply a synchronization rule
    logger.info("Testing synchronization rule operations...")
    result = dkm.apply_sync_rule("Bidirectional_Sync", "Test_Agent_KG", "Global_Knowledge_Fabric")
    logger.info(f"Applied synchronization rule: {result}")
    
    # Create a test entity in the test knowledge graph
    logger.info("Creating test entity...")
    query = """
    CREATE (e:TestEntity {
        id: $id,
        name: $name,
        description: $description,
        created_at: $timestamp
    })
    RETURN e
    """
    
    params = {
        "id": "test-entity-1",
        "name": "Test Entity",
        "description": "A test entity for synchronization",
        "timestamp": datetime.now().timestamp()
    }
    
    connection.query(query, params)
    
    # Test synchronization
    logger.info("Testing synchronization...")
    sync_result = dkm.synchronize("Test_Agent_KG", "Global_Knowledge_Fabric")
    logger.info(f"Synchronization result: {sync_result}")
    
    # Clean up
    logger.info("Cleaning up...")
    
    # Delete the test entity
    query = """
    MATCH (e:TestEntity {id: $id})
    DETACH DELETE e
    """
    
    params = {"id": "test-entity-1"}
    connection.query(query, params)
    
    # Delete the test knowledge graph
    dkm.delete_knowledge_graph("Test_Agent_KG")
    
    logger.info("Test completed successfully.")
    return True

if __name__ == "__main__":
    test_dual_knowledge_manager()
