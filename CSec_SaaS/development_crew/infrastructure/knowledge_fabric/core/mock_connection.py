"""
Mock Neo4j connection for testing and demo purposes.

This module provides an in-memory implementation of the Neo4j connection
interface, allowing tests and demos to run without a live database.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import uuid

logger = logging.getLogger(__name__)

class MockNeo4jConnection:
    """Mock implementation of Neo4jConnection for testing and demos."""
    
    def __init__(self, config=None):
        """
        Initialize mock connection.
        
        Args:
            config: Connection configuration (ignored in mock)
        """
        self.nodes = {}  # id -> {labels: [], properties: {}}
        self.relationships = {}  # id -> {start_node: id, end_node: id, type: str, properties: {}}
        self.next_node_id = 1
        self.next_rel_id = 1
        
        logger.info("Initialized Mock Neo4j connection")
    
    def close(self):
        """Close the mock connection."""
        logger.info("Closed Mock Neo4j connection")
    
    def verify_connectivity(self) -> bool:
        """
        Verify connectivity (always returns True for mock).
        
        Returns:
            bool: Always True for mock connection
        """
        return True
    
    def query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query against the mock database.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        if parameters is None:
            parameters = {}
            
        # Very basic CREATE node support
        if "CREATE (n:" in query and "RETURN ID(n)" in query:
            # Extract label
            label_start = query.find("CREATE (n:") + 10
            label_end = query.find(")", label_start)
            if label_end == -1:
                label_end = query.find(" ", label_start)
            label = query[label_start:label_end].strip()
            
            # Create node
            node_id = self._create_node(label, parameters.get("props", {}))
            return [{"id": node_id}]
            
        # Basic CREATE relationship support
        elif "CREATE (a)-[r:" in query and "RETURN ID(r)" in query:
            source_id = parameters.get("source_id")
            target_id = parameters.get("target_id")
            props = parameters.get("props", {})
            
            # Extract relationship type
            rel_type_start = query.find("CREATE (a)-[r:") + 14
            rel_type_end = query.find("]", rel_type_start)
            rel_type = query[rel_type_start:rel_type_end].strip()
            
            # Create relationship
            rel_id = self._create_relationship(source_id, target_id, rel_type, props)
            return [{"id": rel_id}]
            
        # Default: return empty result
        logger.info(f"Mock query executed: {query[:50]}... (params: {parameters})")
        return []
    
    def run_transaction(self, work, access_mode=None, metadata=None, timeout=None, 
                        bookmarks=None, **kwargs):
        """
        Run a transaction function (simplified for mock).
        
        Args:
            work: Transaction function
            
        Returns:
            Result of transaction function
        """
        # Very simplified - just call the work function with self as a dummy transaction
        return work(self)
    
    def _create_node(self, label: str, properties: Dict[str, Any]) -> int:
        """
        Create a node in the mock database.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            ID of the created node
        """
        node_id = self.next_node_id
        self.next_node_id += 1
        
        # Ensure required properties
        if 'id' not in properties:
            properties['id'] = str(uuid.uuid4())
        if 'created_at' not in properties:
            properties['created_at'] = datetime.now()
        if 'updated_at' not in properties:
            properties['updated_at'] = datetime.now()
            
        self.nodes[node_id] = {
            "labels": [label],
            "properties": properties
        }
        
        logger.info(f"Created mock node with ID {node_id} and label {label}")
        return node_id
    
    def _create_relationship(self, source_id: int, target_id: int, 
                            rel_type: str, properties: Dict[str, Any]) -> int:
        """
        Create a relationship in the mock database.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            
        Returns:
            ID of the created relationship
        """
        # Check if source and target nodes exist
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot create relationship: nodes {source_id} or {target_id} not found")
            return None
            
        rel_id = self.next_rel_id
        self.next_rel_id += 1
        
        self.relationships[rel_id] = {
            "start_node": source_id,
            "end_node": target_id,
            "type": rel_type,
            "properties": properties
        }
        
        logger.info(f"Created mock relationship with ID {rel_id} of type {rel_type}")
        return rel_id
