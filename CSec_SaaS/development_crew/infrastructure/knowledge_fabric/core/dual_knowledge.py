"""
Dual Knowledge Manager for the Digital Genome Architecture.

This module implements the dual-layer knowledge graph structure that allows agents
to maintain both individual knowledge graphs for domain-specific expertise and
synchronize with a shared knowledge fabric for team-wide context.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Union

from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType
from infrastructure.knowledge_fabric.core.connection import Neo4jConnection


class DualKnowledgeManager:
    """
    Manages the dual knowledge architecture with individual and shared knowledge graphs.
    
    The DualKnowledgeManager is responsible for:
    1. Maintaining connections to both individual and shared knowledge graphs
    2. Synchronizing knowledge between individual and shared graphs
    3. Managing access control for knowledge sharing
    4. Versioning knowledge updates to track changes
    """
    
    def __init__(self, shared_connection, agent_id: str):
        """
        Initialize the dual knowledge manager.
        
        Args:
            shared_connection: Connection to the shared knowledge graph
            agent_id: Unique identifier for the agent
        """
        self.shared_connection = shared_connection
        self.agent_id = agent_id
        self.individual_connection = self._create_individual_connection()
        
    def _create_individual_connection(self) -> Neo4jConnection:
        """
        Create a connection to the individual agent's knowledge graph.
        
        Returns:
            Neo4jConnection: A connection to the individual knowledge graph
        """
        # Could be a separate Neo4j database, collection, or namespace
        return Neo4jConnection({
            "uri": f"{os.getenv('NEO4J_URI')}_{self.agent_id}",
            "username": os.getenv("NEO4J_USERNAME"),
            "password": os.getenv("NEO4J_PASSWORD")
        })
    
    def sync_to_shared(self, node_types: Optional[List[NodeLabel]] = None):
        """
        Synchronize knowledge from individual to shared knowledge graph.
        
        Args:
            node_types: Optional list of node types to synchronize. If None, synchronizes all.
        
        Returns:
            Dict: Summary of synchronized nodes and relationships
        """
        # Get nodes from individual graph that need synchronization
        # Filter by node types if specified
        query = self._build_sync_query(node_types)
        
        # Get nodes from individual graph
        individual_nodes = self.individual_connection.query(query)
        
        # Sync nodes to shared graph
        sync_summary = {
            "nodes_synced": 0,
            "relationships_synced": 0,
            "conflicts_resolved": 0
        }
        
        for node in individual_nodes:
            # Add agent_id attribute to track source
            node["properties"]["source_agent"] = self.agent_id
            node["properties"]["last_synced"] = datetime.now().isoformat()
            
            # Check if node already exists in shared graph
            existing_node = self._find_matching_node(node)
            
            if existing_node:
                # Update existing node
                self._update_shared_node(node, existing_node)
                sync_summary["nodes_synced"] += 1
            else:
                # Create new node
                self._create_shared_node(node)
                sync_summary["nodes_synced"] += 1
            
            # Sync relationships
            relationships = self._get_node_relationships(node["id"])
            for rel in relationships:
                self._sync_relationship(rel)
                sync_summary["relationships_synced"] += 1
        
        return sync_summary
    
    def sync_from_shared(self, node_types: Optional[List[NodeLabel]] = None):
        """
        Synchronize knowledge from shared to individual knowledge graph.
        
        Args:
            node_types: Optional list of node types to synchronize. If None, synchronizes all.
        
        Returns:
            Dict: Summary of synchronized nodes and relationships
        """
        # Get nodes from shared graph that need synchronization
        # Filter by node types if specified and relevance to agent
        query = self._build_shared_sync_query(node_types)
        
        # Get nodes from shared graph
        shared_nodes = self.shared_connection.query(query)
        
        # Sync nodes to individual graph
        sync_summary = {
            "nodes_synced": 0,
            "relationships_synced": 0,
            "conflicts_resolved": 0
        }
        
        for node in shared_nodes:
            # Check if node already exists in individual graph
            existing_node = self._find_matching_individual_node(node)
            
            if existing_node:
                # Update existing node
                self._update_individual_node(node, existing_node)
                sync_summary["nodes_synced"] += 1
            else:
                # Create new node
                self._create_individual_node(node)
                sync_summary["nodes_synced"] += 1
            
            # Sync relationships
            relationships = self._get_shared_node_relationships(node["id"])
            for rel in relationships:
                self._sync_individual_relationship(rel)
                sync_summary["relationships_synced"] += 1
        
        return sync_summary
    
    def _build_sync_query(self, node_types: Optional[List[NodeLabel]]) -> str:
        """
        Build a query to get nodes for synchronization.
        
        Args:
            node_types: Optional list of node types to include in the query
            
        Returns:
            str: Cypher query for retrieving nodes
        """
        if node_types:
            # Create query for specific node types
            labels = " OR ".join([f"n:{node_type.value}" for node_type in node_types])
            return f"MATCH (n) WHERE {labels} RETURN n"
        else:
            # Query for all nodes
            return "MATCH (n) RETURN n"
    
    def _build_shared_sync_query(self, node_types: Optional[List[NodeLabel]]) -> str:
        """
        Build a query to get nodes from shared graph for synchronization.
        
        Args:
            node_types: Optional list of node types to include in the query
            
        Returns:
            str: Cypher query for retrieving nodes
        """
        # Base query to find relevant nodes
        query = "MATCH (n) WHERE "
        
        # Add conditions for node types if specified
        if node_types:
            type_conditions = " OR ".join([f"n:{node_type.value}" for node_type in node_types])
            query += f"({type_conditions}) AND "
        
        # Add relevance conditions
        # Either created by this agent or marked as shared
        query += f"(n.source_agent = '{self.agent_id}' OR n.shared = true)"
        
        # Return nodes
        query += " RETURN n"
        
        return query
    
    def _find_matching_node(self, node: Dict) -> Optional[Dict]:
        """
        Find a matching node in the shared graph.
        
        Args:
            node: Node from individual graph
            
        Returns:
            Dict or None: Matching node in shared graph if found
        """
        node_type = node["type"]
        node_props = node["properties"]
        
        # Create query to find matching node
        # Match based on type and key properties
        query = f"MATCH (n:{node_type}) WHERE "
        
        # Add key property matches
        key_props = self._get_key_properties(node_type)
        conditions = []
        
        for key in key_props:
            if key in node_props:
                conditions.append(f"n.{key} = '{node_props[key]}'")
        
        query += " AND ".join(conditions)
        query += " RETURN n"
        
        result = self.shared_connection.query(query)
        
        if result and len(result) > 0:
            return result[0]
        
        return None
    
    def _find_matching_individual_node(self, node: Dict) -> Optional[Dict]:
        """
        Find a matching node in the individual graph.
        
        Args:
            node: Node from shared graph
            
        Returns:
            Dict or None: Matching node in individual graph if found
        """
        node_type = node["type"]
        node_props = node["properties"]
        
        # Create query to find matching node
        # Match based on type and key properties
        query = f"MATCH (n:{node_type}) WHERE "
        
        # Add key property matches
        key_props = self._get_key_properties(node_type)
        conditions = []
        
        for key in key_props:
            if key in node_props:
                conditions.append(f"n.{key} = '{node_props[key]}'")
        
        query += " AND ".join(conditions)
        query += " RETURN n"
        
        result = self.individual_connection.query(query)
        
        if result and len(result) > 0:
            return result[0]
        
        return None
    
    def _get_key_properties(self, node_type: str) -> List[str]:
        """
        Get key properties for a node type used for matching.
        
        Args:
            node_type: Type of node
            
        Returns:
            List[str]: List of key property names
        """
        # Define key properties for each node type
        # These are used to identify matching nodes across graphs
        key_properties = {
            NodeLabel.EVENT.value: ["type", "timestamp"],
            NodeLabel.FUNCTIONAL_REQUIREMENT.value: ["id", "name"],
            NodeLabel.NON_FUNCTIONAL_REQUIREMENT.value: ["id", "name"],
            NodeLabel.POLICY.value: ["id", "name"],
            NodeLabel.WORKFLOW.value: ["id", "name"],
            NodeLabel.WORKFLOW_STEP.value: ["id", "name"],
            NodeLabel.RED_FLAG.value: ["id", "timestamp"],
            # Default keys for other node types
            "default": ["id", "name"]
        }
        
        # Return key properties for node type or default
        return key_properties.get(node_type, key_properties["default"])
    
    def _update_shared_node(self, individual_node: Dict, shared_node: Dict):
        """
        Update a shared node with data from an individual node.
        
        Args:
            individual_node: Node from individual graph
            shared_node: Matching node in shared graph
        """
        node_id = shared_node["id"]
        update_props = {}
        
        # Merge properties with conflict resolution
        for key, value in individual_node["properties"].items():
            # Skip key properties (used for matching)
            if key in self._get_key_properties(individual_node["type"]):
                continue
            
            # Handle conflicts
            if key in shared_node["properties"]:
                # Use most recent update
                if "last_updated" in individual_node["properties"] and "last_updated" in shared_node["properties"]:
                    ind_time = datetime.fromisoformat(individual_node["properties"]["last_updated"])
                    shared_time = datetime.fromisoformat(shared_node["properties"]["last_updated"])
                    
                    if ind_time > shared_time:
                        update_props[key] = value
                else:
                    # Default to individual node value
                    update_props[key] = value
            else:
                # No conflict, add property
                update_props[key] = value
        
        # Update shared node with new properties
        update_props["last_synced"] = datetime.now().isoformat()
        
        self.shared_connection.update_node(node_id, update_props)
    
    def _create_shared_node(self, node: Dict):
        """
        Create a new node in the shared graph.
        
        Args:
            node: Node to create
        
        Returns:
            str: ID of created node
        """
        # Create node with properties
        properties = node["properties"].copy()
        properties["last_synced"] = datetime.now().isoformat()
        
        return self.shared_connection.create_node(
            node["type"],
            properties=properties
        )
    
    def _get_node_relationships(self, node_id: str) -> List[Dict]:
        """
        Get relationships for a node in the individual graph.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List[Dict]: List of relationships
        """
        query = f"""
        MATCH (n)-[r]->(m)
        WHERE ID(n) = {node_id}
        RETURN ID(n) as source, TYPE(r) as type, ID(m) as target, properties(r) as properties
        """
        
        return self.individual_connection.query(query)
    
    def _get_shared_node_relationships(self, node_id: str) -> List[Dict]:
        """
        Get relationships for a node in the shared graph.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List[Dict]: List of relationships
        """
        query = f"""
        MATCH (n)-[r]->(m)
        WHERE ID(n) = {node_id}
        RETURN ID(n) as source, TYPE(r) as type, ID(m) as target, properties(r) as properties
        """
        
        return self.shared_connection.query(query)
    
    def _sync_relationship(self, relationship: Dict):
        """
        Synchronize a relationship to the shared graph.
        
        Args:
            relationship: Relationship to synchronize
        """
        # Find matching nodes in shared graph
        source_node = self._find_node_by_id(relationship["source"])
        target_node = self._find_node_by_id(relationship["target"])
        
        if source_node and target_node:
            # Create relationship in shared graph
            self.shared_connection.create_relationship(
                source_node["id"],
                target_node["id"],
                relationship["type"],
                properties=relationship.get("properties", {})
            )
    
    def _sync_individual_relationship(self, relationship: Dict):
        """
        Synchronize a relationship to the individual graph.
        
        Args:
            relationship: Relationship to synchronize
        """
        # Find matching nodes in individual graph
        source_node = self._find_individual_node_by_id(relationship["source"])
        target_node = self._find_individual_node_by_id(relationship["target"])
        
        if source_node and target_node:
            # Create relationship in individual graph
            self.individual_connection.create_relationship(
                source_node["id"],
                target_node["id"],
                relationship["type"],
                properties=relationship.get("properties", {})
            )
    
    def _find_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        Find a node in the shared graph by its individual graph ID.
        
        Args:
            node_id: ID of the node in individual graph
            
        Returns:
            Dict or None: Matching node in shared graph if found
        """
        # Implementation would depend on how node IDs are mapped between graphs
        # This is a placeholder implementation
        
        # Get node from individual graph
        individual_node = self.individual_connection.get_node(node_id)
        
        if individual_node:
            # Find matching node in shared graph
            return self._find_matching_node(individual_node)
        
        return None
    
    def _find_individual_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        Find a node in the individual graph by its shared graph ID.
        
        Args:
            node_id: ID of the node in shared graph
            
        Returns:
            Dict or None: Matching node in individual graph if found
        """
        # Implementation would depend on how node IDs are mapped between graphs
        # This is a placeholder implementation
        
        # Get node from shared graph
        shared_node = self.shared_connection.get_node(node_id)
        
        if shared_node:
            # Find matching node in individual graph
            return self._find_matching_individual_node(shared_node)
        
        return None
    
    def _update_individual_node(self, shared_node: Dict, individual_node: Dict):
        """
        Update an individual node with data from a shared node.
        
        Args:
            shared_node: Node from shared graph
            individual_node: Matching node in individual graph
        """
        node_id = individual_node["id"]
        update_props = {}
        
        # Merge properties with conflict resolution
        for key, value in shared_node["properties"].items():
            # Skip key properties and agent-specific properties
            if key in self._get_key_properties(shared_node["type"]) or key == "source_agent":
                continue
            
            # Handle conflicts
            if key in individual_node["properties"]:
                # Use most recent update
                if "last_updated" in shared_node["properties"] and "last_updated" in individual_node["properties"]:
                    shared_time = datetime.fromisoformat(shared_node["properties"]["last_updated"])
                    ind_time = datetime.fromisoformat(individual_node["properties"]["last_updated"])
                    
                    if shared_time > ind_time:
                        update_props[key] = value
                else:
                    # Default to shared node value for synchronization
                    update_props[key] = value
            else:
                # No conflict, add property
                update_props[key] = value
        
        # Update individual node with new properties
        update_props["last_synced"] = datetime.now().isoformat()
        
        self.individual_connection.update_node(node_id, update_props)
    
    def _create_individual_node(self, node: Dict):
        """
        Create a new node in the individual graph.
        
        Args:
            node: Node to create
        
        Returns:
            str: ID of created node
        """
        # Create node with properties
        properties = node["properties"].copy()
        properties["last_synced"] = datetime.now().isoformat()
        
        # Remove source_agent if it's not this agent
        if properties.get("source_agent") != self.agent_id:
            properties["original_source"] = properties.get("source_agent")
            properties["source_agent"] = self.agent_id
        
        return self.individual_connection.create_node(
            node["type"],
            properties=properties
        )
