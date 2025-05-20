"""
Events Node for the Digital Genome Architecture.

This module implements real-time event tracking, capturing mechanisms,
and associative memory structures as part of the Digital Genome Architecture.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType


class NodeRepositoryAdapter:
    """
    Adapter for NodeRepository to provide the interface expected by EventsNode.
    """
    
    def __init__(self, repository):
        """
        Initialize the adapter.
        
        Args:
            repository: NodeRepository instance
        """
        self.repository = repository
    
    def create_node(self, label, properties):
        """
        Create a node using the repository.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            ID of the created node
        """
        # Convert label enum to string if needed
        if hasattr(label, 'value'):
            label = label.value
            
        # Add required timestamp properties if not present
        if 'created_at' not in properties:
            properties['created_at'] = datetime.now()
        if 'updated_at' not in properties:
            properties['updated_at'] = datetime.now()
            
        # Use the repository's run_query method as it accepts raw queries
        query = f"""
        CREATE (n:{label} $props)
        RETURN ID(n) as id
        """
        
        result = self.repository.connection.query(query, {"props": properties})
        return result[0]['id'] if result else None
    
    def create_relationship(self, source_id, target_id, relationship_type, properties=None):
        """
        Create a relationship between nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship_type: Relationship type
            properties: Relationship properties
            
        Returns:
            True if successful, False otherwise
        """
        # Convert type enum to string if needed
        if hasattr(relationship_type, 'value'):
            relationship_type = relationship_type.value
            
        if properties is None:
            properties = {}
            
        query = f"""
        MATCH (a), (b)
        WHERE ID(a) = $source_id AND ID(b) = $target_id
        CREATE (a)-[r:{relationship_type} $props]->(b)
        RETURN ID(r) as id
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "props": properties
        }
        
        result = self.repository.connection.query(query, params)
        return True if result else False
        

class EventsNode:
    """
    Manages the event tracking and associative memory in the knowledge graph.
    
    The EventsNode is responsible for:
    1. Logging all system events in the knowledge graph
    2. Creating associative links between related events
    3. Providing temporal analysis of event sequences
    4. Supporting event-based triggers for system actions
    """
    
    def __init__(self, repository):
        """
        Initialize the events node.
        
        Args:
            repository: Repository for graph operations
        """
        # Create an adapter if repository is not already an adapter
        if not hasattr(repository, 'create_node'):
            self.knowledge_manager = NodeRepositoryAdapter(repository)
        else:
            self.knowledge_manager = repository
        
    def log_event(self, event_type: str, metadata: Dict[str, Any], 
                  related_nodes: Optional[List[Dict[str, Any]]] = None,
                  context: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an event in the knowledge graph.
        
        Args:
            event_type: Type of the event (e.g., "agent_action", "system_error")
            metadata: Additional data about the event
            related_nodes: Optional list of nodes related to this event
            context: Optional execution context information
            
        Returns:
            str: ID of the created event node
        """
        event_node = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": json.dumps(metadata)
        }
        
        # Add contextual information if provided
        if context:
            event_node["context"] = json.dumps(context)
        
        # Create event node
        event_id = self.knowledge_manager.create_node(
            NodeLabel.EVENT, 
            properties=event_node
        )
        
        # Link to related nodes
        if related_nodes:
            for node in related_nodes:
                self.knowledge_manager.create_relationship(
                    event_id, 
                    node["id"], 
                    RelationshipType.RELATED_TO
                )
                
        return event_id
    
    def log_agent_action(self, agent_id: str, action_type: str, 
                         inputs: Dict[str, Any], outputs: Dict[str, Any],
                         success: bool, related_nodes: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Log an agent action as an event.
        
        Args:
            agent_id: ID of the agent performing the action
            action_type: Type of action performed
            inputs: Input data for the action
            outputs: Output data from the action
            success: Whether the action was successful
            related_nodes: Optional list of nodes related to this event
            
        Returns:
            str: ID of the created event node
        """
        metadata = {
            "agent_id": agent_id,
            "action_type": action_type,
            "inputs": inputs,
            "outputs": outputs,
            "success": success
        }
        
        return self.log_event("agent_action", metadata, related_nodes)
    
    def log_system_event(self, component: str, event_type: str, 
                        details: Dict[str, Any], 
                        severity: str = "info",
                        related_nodes: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Log a system event.
        
        Args:
            component: System component generating the event
            event_type: Type of system event
            details: Details about the event
            severity: Severity level (info, warning, error, critical)
            related_nodes: Optional list of nodes related to this event
            
        Returns:
            str: ID of the created event node
        """
        metadata = {
            "component": component,
            "event_type": event_type,
            "details": details,
            "severity": severity
        }
        
        return self.log_event("system_event", metadata, related_nodes)
    
    def log_workflow_step(self, workflow_id: str, step_id: str, 
                         status: str, data: Dict[str, Any],
                         related_nodes: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Log a workflow step execution.
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the workflow step
            status: Status of the step (started, completed, failed)
            data: Data associated with the step
            related_nodes: Optional list of nodes related to this event
            
        Returns:
            str: ID of the created event node
        """
        metadata = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "status": status,
            "data": data
        }
        
        return self.log_event("workflow_step", metadata, related_nodes)
    
    def create_event_sequence(self, event_ids: List[str], sequence_name: str, 
                             metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a sequence from multiple events.
        
        Args:
            event_ids: List of event IDs to include in the sequence
            sequence_name: Name of the sequence
            metadata: Optional metadata for the sequence
            
        Returns:
            str: ID of the created sequence node
        """
        sequence_properties = {
            "name": sequence_name,
            "event_count": len(event_ids),
            "created_at": datetime.now().isoformat()
        }
        
        if metadata:
            sequence_properties["metadata"] = json.dumps(metadata)
        
        # Create sequence node
        sequence_id = self.knowledge_manager.create_node(
            "EventSequence", 
            properties=sequence_properties
        )
        
        # Link events to sequence in order
        for index, event_id in enumerate(event_ids):
            self.knowledge_manager.create_relationship(
                sequence_id, 
                event_id, 
                RelationshipType.CONTAINS,
                properties={"order": index}
            )
        
        return sequence_id
    
    def find_related_events(self, node_id: str, event_types: Optional[List[str]] = None,
                           time_range: Optional[Dict[str, str]] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find events related to a specific node.
        
        Args:
            node_id: ID of the node to find related events
            event_types: Optional list of event types to filter
            time_range: Optional time range for filtering
            limit: Maximum number of events to return
            
        Returns:
            List[Dict]: List of related events
        """
        # Create query with filters
        query = f"""
        MATCH (e:{NodeLabel.EVENT.value})-[r:{RelationshipType.RELATED_TO.value}]-(n)
        WHERE ID(n) = {node_id}
        """
        
        # Add event type filter
        if event_types:
            event_type_condition = " OR ".join([f"e.type = '{t}'" for t in event_types])
            query += f" AND ({event_type_condition})"
        
        # Add time range filter
        if time_range:
            if "start" in time_range:
                query += f" AND e.timestamp >= '{time_range['start']}'"
            if "end" in time_range:
                query += f" AND e.timestamp <= '{time_range['end']}'"
        
        # Add order and limit
        query += f"""
        ORDER BY e.timestamp DESC
        LIMIT {limit}
        RETURN e
        """
        
        return self.knowledge_manager.query(query)
    
    def find_event_patterns(self, pattern_template: List[Dict[str, Any]], 
                           time_window: Optional[int] = None) -> List[List[Dict[str, Any]]]:
        """
        Find instances of event patterns in the knowledge graph.
        
        Args:
            pattern_template: Template describing the pattern to find
            time_window: Optional time window (in seconds) for pattern matching
            
        Returns:
            List[List[Dict]]: List of event sequences matching the pattern
        """
        # Implementation would depend on pattern complexity
        # This is a placeholder for the pattern matching algorithm
        
        # Example implementation for simple sequence pattern
        if len(pattern_template) <= 1:
            return []
        
        # Build query based on pattern template
        query_parts = []
        
        for i, event_spec in enumerate(pattern_template):
            node_var = f"e{i}"
            
            # Create node pattern
            query_parts.append(f"MATCH ({node_var}:{NodeLabel.EVENT.value})")
            
            # Add constraints for this event
            constraints = []
            
            if "type" in event_spec:
                constraints.append(f"{node_var}.type = '{event_spec['type']}'")
            
            if "metadata" in event_spec:
                for key, value in event_spec["metadata"].items():
                    # Note: This is a simplification. In practice, we'd need to parse the JSON
                    constraints.append(f"{node_var}.metadata CONTAINS '{key}' AND {node_var}.metadata CONTAINS '{value}'")
            
            if constraints:
                query_parts.append("WHERE " + " AND ".join(constraints))
            
            # Add temporal constraints between events
            if i > 0:
                prev_node = f"e{i-1}"
                
                query_parts.append(f"WITH {', '.join([f'e{j}' for j in range(i+1)])}")
                
                # Add time constraint if window specified
                if time_window:
                    # Calculate time difference in seconds
                    query_parts.append(
                        f"WHERE duration.inSeconds(datetime({prev_node}.timestamp), "
                        f"datetime({node_var}.timestamp)) <= {time_window} "
                        f"AND {node_var}.timestamp > {prev_node}.timestamp"
                    )
                else:
                    # Just ensure correct order
                    query_parts.append(f"WHERE {node_var}.timestamp > {prev_node}.timestamp")
        
        # Complete the query
        query_parts.append(f"RETURN {', '.join([f'e{j}' for j in range(len(pattern_template))])}")
        
        # Execute query
        query = "\n".join(query_parts)
        result = self.knowledge_manager.query(query)
        
        # Format results as sequences
        sequences = []
        for row in result:
            sequence = [row[f"e{i}"] for i in range(len(pattern_template))]
            sequences.append(sequence)
        
        return sequences
    
    def get_event_statistics(self, event_type: Optional[str] = None, 
                            time_range: Optional[Dict[str, str]] = None,
                            group_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about events in the system.
        
        Args:
            event_type: Optional event type to filter
            time_range: Optional time range for filtering
            group_by: Optional field to group by (e.g., "metadata.agent_id")
            
        Returns:
            Dict: Statistics about events
        """
        # Build base query
        query = f"MATCH (e:{NodeLabel.EVENT.value})"
        
        conditions = []
        
        # Add event type filter
        if event_type:
            conditions.append(f"e.type = '{event_type}'")
        
        # Add time range filter
        if time_range:
            if "start" in time_range:
                conditions.append(f"e.timestamp >= '{time_range['start']}'")
            if "end" in time_range:
                conditions.append(f"e.timestamp <= '{time_range['end']}'")
        
        # Add conditions to query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Define what to return based on grouping
        if group_by:
            # Example for grouping by a field in metadata (simplified)
            # In practice, would need to parse JSON
            if group_by.startswith("metadata."):
                field = group_by.split(".", 1)[1]
                query += f"""
                WITH e.type as type, e.metadata as metadata
                RETURN type, metadata, count(*) as count
                ORDER BY count DESC
                """
            else:
                # Group by regular property
                query += f"""
                WITH e.{group_by} as {group_by}, count(*) as count
                RETURN {group_by}, count
                ORDER BY count DESC
                """
        else:
            # No grouping, just get counts
            query += """
            RETURN e.type as type, count(*) as count
            ORDER BY count DESC
            """
        
        result = self.knowledge_manager.query(query)
        
        # Format result as statistics
        stats = {
            "total_count": sum(r.get("count", 0) for r in result),
            "breakdown": result
        }
        
        return stats
