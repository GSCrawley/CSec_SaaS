"""
test_connection.py

A simple script to test the Neo4j connection.
"""

import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """Test the Neo4j connection."""
    # Load environment variables
    load_dotenv()
    
    # Import Neo4j connection
    from infrastructure.knowledge_fabric.core.connection import Neo4jConnection, Neo4jConfig
    
    # Get connection details from environment
    config = {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "username": os.getenv("NEO4J_USERNAME", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password"),
        "database": os.getenv("NEO4J_DATABASE", "neo4j")
    }
    
    # Show connection details (redact password)
    connection_info = dict(config)
    if "password" in connection_info:
        connection_info["password"] = "********"  # Redact password for logging
    logger.info(f"Connecting to Neo4j with settings: {connection_info}")
    
    try:
        # Create connection
        neo4j_config = Neo4jConfig(**config)
        connection = Neo4jConnection(neo4j_config)
        
        # Test connection
        if connection.verify_connectivity():
            logger.info("✅ Successfully connected to Neo4j!")
            
            # Get database version
            result = connection.query("CALL dbms.components() YIELD name, versions RETURN name, versions")
            if result:
                version_info = f"{result[0]['name']} {result[0]['versions'][0]}"
                logger.info(f"Connected to Neo4j version: {version_info}")
            
            # Count nodes to verify database access
            count_result = connection.query("MATCH (n) RETURN count(n) as node_count")
            node_count = count_result[0]["node_count"] if count_result else 0
            logger.info(f"Database has {node_count} nodes")
            
            return True
        else:
            logger.error("❌ Failed to connect to Neo4j database")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
            logger.info("Connection closed")

if __name__ == "__main__":
    test_neo4j_connection()