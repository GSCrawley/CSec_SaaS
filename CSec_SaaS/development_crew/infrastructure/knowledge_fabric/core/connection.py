"""
Neo4j knowledge graph connection module.

This module provides the base connection and session management
for interacting with the Neo4j knowledge graph database.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from neo4j import GraphDatabase, Session
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Neo4jConfig(BaseModel):
    """Configuration for Neo4j connection."""
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    max_transaction_retry_time: float = 30.0

class Neo4jConnection:
    """Manages connection to Neo4j database."""
    
    def __init__(self, config: Union[Neo4jConfig, Dict[str, Any]]):
        """Initialize Neo4j connection.
        
        Args:
            config: Neo4j connection configuration.
        """
        if isinstance(config, dict):
            config = Neo4jConfig(**config)
        
        self.config = config
        self._driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password),
            max_connection_pool_size=config.max_connection_pool_size,
            max_transaction_retry_time=config.max_transaction_retry_time
        )
        logger.info(f"Initialized Neo4j connection to {config.uri}")
        
    def close(self):
        """Close the driver connection."""
        if self._driver:
            self._driver.close()
            logger.info("Closed Neo4j connection")
            
    def verify_connectivity(self) -> bool:
        """Verify connectivity to Neo4j database.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 AS result")
                return result.single()["result"] == 1
        except Neo4jError as e:
            logger.error(f"Neo4j connection verification failed: {e}")
            return False
            
    def session(self) -> Session:
        """Get a new Neo4j session.
        
        Returns:
            Session: A new Neo4j session.
        """
        return self._driver.session(database=self.config.database)
    
    def query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string.
            parameters: Query parameters.
            
        Returns:
            List of dictionaries containing query results.
        """
        parameters = parameters or {}
        try:
            with self.session() as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        except Neo4jError as e:
            logger.error(f"Neo4j query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise

class Neo4jConnectionPool:
    """A connection pool for Neo4j database connections."""
    
    def __init__(self, config: Union[Neo4jConfig, Dict[str, Any]], pool_size: int = 5):
        """Initialize Neo4j connection pool.
        
        Args:
            config: Neo4j connection configuration.
            pool_size: Size of the connection pool.
        """
        self.config = config if isinstance(config, Neo4jConfig) else Neo4jConfig(**config)
        self.pool_size = pool_size
        self.available_connections = []
        self.used_connections = set()
        
        # Initialize pool with connections
        for _ in range(pool_size):
            self.available_connections.append(Neo4jConnection(self.config))
            
        logger.info(f"Initialized Neo4j connection pool with {pool_size} connections")
    
    def get_connection(self) -> Neo4jConnection:
        """Get a connection from the pool.
        
        Returns:
            A Neo4j connection from the pool.
            
        Raises:
            RuntimeError: If no connections are available.
        """
        if not self.available_connections:
            if len(self.used_connections) < self.pool_size:
                # Create a new connection if we haven't reached pool_size
                connection = Neo4jConnection(self.config)
            else:
                raise RuntimeError("No available connections in the pool")
        else:
            connection = self.available_connections.pop()
            
        self.used_connections.add(connection)
        return connection
    
    def release_connection(self, connection: Neo4jConnection):
        """Release a connection back to the pool.
        
        Args:
            connection: The connection to release.
        """
        if connection in self.used_connections:
            self.used_connections.remove(connection)
            self.available_connections.append(connection)
        else:
            # If connection wasn't from our pool, close it
            connection.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        for connection in self.available_connections:
            connection.close()
            
        for connection in self.used_connections:
            connection.close()
            
        self.available_connections = []
        self.used_connections = set()
        logger.info("Closed all connections in Neo4j connection pool")


# Singleton connection pool
_connection_pool = None

def get_connection_pool(config: Optional[Union[Neo4jConfig, Dict[str, Any]]] = None, 
                        pool_size: int = 5) -> Neo4jConnectionPool:
    """Get or create the singleton connection pool.
    
    Args:
        config: Optional Neo4j configuration. If None, will use environment variables.
        pool_size: Size of the connection pool.
        
    Returns:
        Neo4jConnectionPool: The connection pool.
    """
    global _connection_pool
    
    if _connection_pool is None:
        if config is None:
            # If no config provided, use environment variables
            config = Neo4jConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                username=os.getenv("NEO4J_USERNAME", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "password"),
                database=os.getenv("NEO4J_DATABASE", "neo4j")
            )
        
        _connection_pool = Neo4jConnectionPool(config, pool_size)
        
    return _connection_pool