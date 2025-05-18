"""
knowledge_fabric_init.py

This script initializes the knowledge fabric for the Development Crew.
It sets up the Neo4j schema, creates necessary indexes, and establishes
the core entity types needed for agent collaboration.
"""

import logging
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from infrastructure.knowledge_fabric.core.connection import Neo4jConnection, Neo4jConfig
from infrastructure.knowledge_fabric.core.schema import SchemaManager, CORE_SCHEMA
from infrastructure.knowledge_fabric.services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_knowledge_fabric(config: Optional[Dict[str, Any]] = None) -> KnowledgeService:
    """Initialize the knowledge fabric with the core schema.
    
    Args:
        config: Optional Neo4j configuration. If None, uses environment variables.
        
    Returns:
        Initialized Knowledge Service instance.
    """
    logger.info("Initializing knowledge fabric...")
    
    # Load environment variables if no config provided
    if not config:
        load_dotenv()
        config = {
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "username": os.getenv("NEO4J_USERNAME", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", "password"),
            "database": os.getenv("NEO4J_DATABASE", "neo4j")
        }
    
    # Create Neo4j connection
    neo4j_config = Neo4jConfig(**config)
    connection = Neo4jConnection(neo4j_config)
    
    # Verify connectivity
    if not connection.verify_connectivity():
        logger.error("Failed to connect to Neo4j database. Check your configuration.")
        raise ConnectionError("Neo4j connection failed")
    
    logger.info("Successfully connected to Neo4j database.")
    
    # Get some database info to confirm it's working
    try:
        result = connection.query("CALL dbms.components() YIELD name, versions RETURN name, versions")
        if result:
            version_info = f"{result[0]['name']} {result[0]['versions'][0]}"
            logger.info(f"Connected to Neo4j version: {version_info}")
    except Exception as e:
        logger.warning(f"Connected but couldn't get version info: {e}")
    
    # Initialize schema
    schema_manager = SchemaManager(connection)
    schema_manager.initialize_schema(CORE_SCHEMA)
    logger.info("Core schema initialized.")
    
    # Create knowledge service
    knowledge_service = KnowledgeService(connection)
    logger.info("Knowledge service created.")
    
    return knowledge_service

def create_initial_domain(knowledge_service: KnowledgeService, domain_name: str) -> str:
    """Create an initial domain in the knowledge graph.
    
    Args:
        knowledge_service: Knowledge service instance.
        domain_name: Name of the domain to create.
        
    Returns:
        ID of the created domain.
    """
    logger.info(f"Creating initial domain: {domain_name}")
    domain = knowledge_service.create_domain(domain_name, f"The {domain_name} domain for Development Crew")
    logger.info(f"Domain created with ID: {domain.id}")
    return domain.id

def create_agent_team(knowledge_service: KnowledgeService) -> Dict[str, str]:
    """Create the initial agent team in the knowledge graph.
    
    Args:
        knowledge_service: Knowledge service instance.
        
    Returns:
        Dictionary mapping agent types to their IDs.
    """
    logger.info("Creating agent team...")
    
    agents = {
        # Orchestration Layer
        "project_manager": knowledge_service.create_agent(
            "Project Manager Agent", 
            "project_manager", 
            "orchestration",
            "Coordinates workflows, monitors progress, identifies bottlenecks"
        ),
        "requirements_analyst": knowledge_service.create_agent(
            "Requirements Analyst Agent", 
            "requirements_analyst", 
            "orchestration",
            "Translates business needs into technical requirements"
        ),
        "quality_assurance": knowledge_service.create_agent(
            "Quality Assurance Agent", 
            "quality_assurance", 
            "orchestration",
            "Verifies outputs against requirements and standards"
        )
    }
    
    logger.info(f"Created {len(agents)} initial agents")
    
    return {agent_type: agent.id for agent_type, agent in agents.items()}

if __name__ == "__main__":
    try:
        # Initialize knowledge fabric
        knowledge_service = initialize_knowledge_fabric()
        
        # Create initial domain
        domain_id = create_initial_domain(knowledge_service, "Development")
        
        # Create agent team
        agent_ids = create_agent_team(knowledge_service)
        
        logger.info("Knowledge fabric initialization complete!")
        logger.info(f"Domain ID: {domain_id}")
        logger.info(f"Agent IDs: {agent_ids}")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
    finally:
        # Close connections
        if 'knowledge_service' in locals():
            knowledge_service.close()