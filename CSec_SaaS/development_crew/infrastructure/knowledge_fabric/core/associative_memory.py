"""
Associative Memory Module for the Digital Genome Architecture.

This module implements an associative memory system that can:
1. Store and retrieve memories based on content and context
2. Establish associations between related memories
3. Support temporal and semantic queries for memory recall
4. Decay less relevant memories over time
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union, Tuple
import math

from infrastructure.knowledge_fabric.core.schema import NodeLabel, RelationshipType
from infrastructure.knowledge_fabric.core.events_node import EventsNode

logger = logging.getLogger(__name__)

class MemoryRecord:
    """Represents a single memory record in the associative memory system."""
    
    def __init__(
        self, 
        id: str,
        content: Dict[str, Any],
        context: Dict[str, Any],
        memory_type: str,
        timestamp: datetime,
        importance: float = 0.5,
        last_accessed: Optional[datetime] = None,
        access_count: int = 0,
        associations: Optional[List[str]] = None
    ):
        """
        Initialize a memory record.
        
        Args:
            id: Unique identifier for the memory
            content: The actual content of the memory
            context: Contextual information about the memory
            memory_type: Type of memory (event, knowledge, decision, etc.)
            timestamp: When the memory was created
            importance: Initial importance score (0.0 to 1.0)
            last_accessed: When the memory was last accessed
            access_count: How many times the memory has been accessed
            associations: IDs of other related memories
        """
        self.id = id
        self.content = content
        self.context = context
        self.memory_type = memory_type
        self.timestamp = timestamp
        self.importance = importance
        self.last_accessed = last_accessed or timestamp
        self.access_count = access_count
        self.associations = associations or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "content": json.dumps(self.content),
            "context": json.dumps(self.context),
            "memory_type": self.memory_type,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "associations": self.associations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=json.loads(data["content"]),
            context=json.loads(data["context"]),
            memory_type=data["memory_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data["importance"],
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            associations=data["associations"]
        )
    
    def access(self):
        """Record an access to this memory."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self


class AssociativeMemory:
    """
    Implements an associative memory system using the knowledge graph.
    
    The associative memory system is responsible for:
    1. Storing and retrieving memories based on content and context
    2. Establishing associations between related memories
    3. Managing memory importance and decay over time
    4. Supporting temporal and semantic queries for memory recall
    """
    
    def __init__(self, knowledge_manager, events_node: Optional[EventsNode] = None):
        """
        Initialize the associative memory system.
        
        Args:
            knowledge_manager: Manager for knowledge graph operations
            events_node: Optional events node for logging memory operations
        """
        self.knowledge_manager = knowledge_manager
        self.events_node = events_node
        self.memory_decay_factor = 0.85  # Controls how quickly memories decay (0.0-1.0)
        self.time_weight = 0.4  # Weight for time in relevance calculation
        self.semantic_weight = 0.6  # Weight for semantic similarity in relevance
        self.importance_threshold = 0.3  # Threshold for memory importance to be maintained
        
    def store_memory(
        self, 
        content: Dict[str, Any],
        context: Dict[str, Any],
        memory_type: str,
        importance: float = 0.5,
        associations: Optional[List[str]] = None
    ) -> str:
        """
        Store a new memory in the associative memory system.
        
        Args:
            content: The actual content of the memory
            context: Contextual information about the memory
            memory_type: Type of memory (event, knowledge, decision, etc.)
            importance: Initial importance score (0.0 to 1.0)
            associations: IDs of other related memories
            
        Returns:
            str: ID of the created memory node
        """
        # Create memory record
        now = datetime.now()
        memory = MemoryRecord(
            id=f"mem_{now.timestamp()}",
            content=content,
            context=context,
            memory_type=memory_type,
            timestamp=now,
            importance=importance,
            associations=associations or []
        )
        
        # Create node properties
        properties = memory.to_dict()
        
        # Create memory node in the knowledge graph
        memory_id = self.knowledge_manager.create_node(
            NodeLabel.MEMORY,
            properties=properties
        )
        
        # Create associations to other memories
        if associations:
            for assoc_id in associations:
                self.knowledge_manager.create_relationship(
                    memory_id,
                    assoc_id,
                    RelationshipType.ASSOCIATED_WITH,
                    properties={
                        "created_at": now.isoformat(),
                        "strength": 0.5  # Initial association strength
                    }
                )
        
        # Log memory creation event
        if self.events_node:
            self.events_node.log_system_event(
                component="AssociativeMemory",
                event_type="memory_created",
                details={
                    "memory_id": memory_id,
                    "memory_type": memory_type,
                    "importance": importance
                }
            )
        
        return memory_id
    
    def recall_by_id(self, memory_id: str) -> Optional[MemoryRecord]:
        """
        Retrieve a specific memory by its ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            MemoryRecord or None: The retrieved memory or None if not found
        """
        # Query the knowledge graph for the memory node
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        WHERE m.id = $memory_id
        RETURN m
        """
        
        result = self.knowledge_manager.query(query, {"memory_id": memory_id})
        
        if not result or not result[0].get("m"):
            return None
        
        # Convert to memory record
        memory_data = result[0]["m"]
        memory = MemoryRecord.from_dict(memory_data)
        
        # Update access information
        memory.access()
        self._update_memory_access(memory_id, memory.last_accessed, memory.access_count)
        
        return memory
    
    def recall_by_content(self, query_content: Dict[str, Any], limit: int = 5) -> List[MemoryRecord]:
        """
        Retrieve memories related to specific content.
        
        Args:
            query_content: Content to search for
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryRecord]: List of matching memories
        """
        # Convert query content to string for comparison
        query_str = json.dumps(query_content)
        
        # Query the knowledge graph for similar memories
        # This is a simplified implementation; a real system would use
        # vector embeddings or more sophisticated similarity measures
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        WHERE m.content CONTAINS $query_str
        RETURN m
        ORDER BY m.importance DESC
        LIMIT $limit
        """
        
        result = self.knowledge_manager.query(query, {
            "query_str": query_str,
            "limit": limit
        })
        
        memories = []
        for record in result:
            if record.get("m"):
                memory = MemoryRecord.from_dict(record["m"])
                # Update access information
                memory.access()
                self._update_memory_access(memory.id, memory.last_accessed, memory.access_count)
                memories.append(memory)
        
        return memories
    
    def recall_by_context(self, query_context: Dict[str, Any], limit: int = 5) -> List[MemoryRecord]:
        """
        Retrieve memories related to specific context.
        
        Args:
            query_context: Context to search for
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryRecord]: List of matching memories
        """
        # Create parameters for the query
        params = {"limit": limit}
        
        # Build a JSON pattern matching query
        # This uses apoc.json.path to search within the JSON string
        # which is more reliable than basic string containment
        where_clauses = []
        
        for i, (key, value) in enumerate(query_context.items()):
            param_key = f"key_{i}"
            param_val = f"val_{i}"
            
            # Store parameters
            params[param_key] = key
            
            if isinstance(value, (dict, list)):
                params[param_val] = json.dumps(value)
            else:
                params[param_val] = str(value)
            
            # Create a clause that checks if the key exists and has the right value
            # Use string pattern matching for Neo4j context queries
            where_clauses.append(f"(m.context CONTAINS ${param_key} AND m.context CONTAINS ${param_val})")

        
        # Join all conditions with OR
        where_clause = " OR ".join(where_clauses) if where_clauses else "TRUE"
        
        # Query the knowledge graph for contextually similar memories
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        WHERE {where_clause}
        RETURN m
        ORDER BY m.importance DESC
        LIMIT $limit
        """
        
        try:
            result = self.knowledge_manager.query(query, params)
            
            memories = []
            for record in result:
                if record.get("m"):
                    memory = MemoryRecord.from_dict(record["m"])
                    # Update access information
                    memory.access()
                    self._update_memory_access(memory.id, memory.last_accessed, memory.access_count)
                    memories.append(memory)
            
            return memories
        except Exception as e:
            logger.error(f"Error executing recall_by_context query: {str(e)}")
            # Return empty list in case of error
            return []
    
    def recall_by_time(self, start_time: datetime, end_time: datetime, limit: int = 10) -> List[MemoryRecord]:
        """
        Retrieve memories from a specific time period.
        
        Args:
            start_time: Start of time period
            end_time: End of time period
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryRecord]: List of matching memories
        """
        # Query the knowledge graph for memories in the time range
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        WHERE datetime(m.timestamp) >= datetime($start_time)
        AND datetime(m.timestamp) <= datetime($end_time)
        RETURN m
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        
        result = self.knowledge_manager.query(query, {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "limit": limit
        })
        
        memories = []
        for record in result:
            if record.get("m"):
                memory = MemoryRecord.from_dict(record["m"])
                # Update access information
                memory.access()
                self._update_memory_access(memory.id, memory.last_accessed, memory.access_count)
                memories.append(memory)
        
        return memories
    
    def recall_by_type(self, memory_type: str, limit: int = 10) -> List[MemoryRecord]:
        """
        Retrieve memories of a specific type.
        
        Args:
            memory_type: Type of memories to retrieve
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryRecord]: List of matching memories
        """
        # Query the knowledge graph for memories of the specified type
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        WHERE m.memory_type = $memory_type
        RETURN m
        ORDER BY m.importance DESC
        LIMIT $limit
        """
        
        result = self.knowledge_manager.query(query, {
            "memory_type": memory_type,
            "limit": limit
        })
        
        memories = []
        for record in result:
            if record.get("m"):
                memory = MemoryRecord.from_dict(record["m"])
                # Update access information
                memory.access()
                self._update_memory_access(memory.id, memory.last_accessed, memory.access_count)
                memories.append(memory)
        
        return memories
    
    def recall_associations(self, memory_id: str, depth: int = 1) -> List[MemoryRecord]:
        """
        Retrieve memories associated with a specific memory.
        
        Args:
            memory_id: ID of the source memory
            depth: How many levels of associations to traverse
            
        Returns:
            List[MemoryRecord]: List of associated memories
        """
        # Query the knowledge graph for associated memories
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value} {{id: $memory_id}})-[r:{RelationshipType.ASSOCIATED_WITH.value}*1..{depth}]->(a:{NodeLabel.MEMORY.value})
        RETURN a, min(length(r)) as distance
        ORDER BY distance, a.importance DESC
        """
        
        result = self.knowledge_manager.query(query, {"memory_id": memory_id})
        
        memories = []
        for record in result:
            if record.get("a"):
                memory = MemoryRecord.from_dict(record["a"])
                # Update access information
                memory.access()
                self._update_memory_access(memory.id, memory.last_accessed, memory.access_count)
                memories.append(memory)
        
        return memories
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> Optional[MemoryRecord]:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of the memory to update
            updates: Dictionary of fields to update
            
        Returns:
            MemoryRecord or None: The updated memory or None if not found
        """
        # First retrieve the existing memory
        memory = self.recall_by_id(memory_id)
        if not memory:
            return None
        
        # Apply updates
        if "content" in updates:
            memory.content = updates["content"]
        if "context" in updates:
            memory.context = updates["context"]
        if "importance" in updates:
            memory.importance = updates["importance"]
        
        # Convert updated memory to dictionary
        properties = memory.to_dict()
        
        # Update the memory node in the knowledge graph
        self.knowledge_manager.update_node(
            memory_id,
            properties
        )
        
        # Log memory update event
        if self.events_node:
            self.events_node.log_system_event(
                component="AssociativeMemory",
                event_type="memory_updated",
                details={
                    "memory_id": memory_id,
                    "updated_fields": list(updates.keys())
                }
            )
        
        return memory
    
    def create_association(self, source_id: str, target_id: str, strength: float = 0.5) -> bool:
        """
        Create or strengthen an association between two memories.
        
        Args:
            source_id: ID of the source memory
            target_id: ID of the target memory
            strength: Association strength (0.0 to 1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if both memories exist
        source = self.recall_by_id(source_id)
        target = self.recall_by_id(target_id)
        
        if not source or not target:
            return False
        
        # Check if association already exists
        query = f"""
        MATCH (s:{NodeLabel.MEMORY.value} {{id: $source_id}})-[r:{RelationshipType.ASSOCIATED_WITH.value}]->(t:{NodeLabel.MEMORY.value} {{id: $target_id}})
        RETURN r
        """
        
        result = self.knowledge_manager.query(query, {
            "source_id": source_id,
            "target_id": target_id
        })
        
        now = datetime.now()
        
        if result and result[0].get("r"):
            # Update existing association
            rel_id = result[0]["r"].id
            self.knowledge_manager.update_relationship(
                rel_id,
                {
                    "strength": strength,
                    "updated_at": now.isoformat()
                }
            )
        else:
            # Create new association
            self.knowledge_manager.create_relationship(
                source_id,
                target_id,
                RelationshipType.ASSOCIATED_WITH,
                properties={
                    "strength": strength,
                    "created_at": now.isoformat()
                }
            )
            
            # Add to associations list for both memories
            if target_id not in source.associations:
                source.associations.append(target_id)
                self.update_memory(source_id, {"associations": source.associations})
            
            if source_id not in target.associations:
                target.associations.append(source_id)
                self.update_memory(target_id, {"associations": target.associations})
        
        # Log association event
        if self.events_node:
            self.events_node.log_system_event(
                component="AssociativeMemory",
                event_type="association_created",
                details={
                    "source_id": source_id,
                    "target_id": target_id,
                    "strength": strength
                }
            )
        
        return True
    
    def decay_memories(self, older_than: Optional[timedelta] = None):
        """
        Decay memory importance based on time and usage.
        
        Args:
            older_than: Only decay memories older than this time delta
            
        Returns:
            int: Number of memories decayed
        """
        time_limit = datetime.now()
        if older_than:
            time_limit = time_limit - older_than
        
        # Find memories older than the time limit
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        WHERE datetime(m.timestamp) < datetime($time_limit)
        RETURN m
        """
        
        result = self.knowledge_manager.query(query, {
            "time_limit": time_limit.isoformat()
        })
        
        count = 0
        for record in result:
            if record.get("m"):
                memory = MemoryRecord.from_dict(record["m"])
                
                # Calculate decay based on time since last access and importance
                time_since_access = (datetime.now() - memory.last_accessed).total_seconds()
                decay_factor = math.exp(-time_since_access / (86400 * self.memory_decay_factor))  # 86400 = seconds in a day
                
                # Apply decay but increase value for frequently accessed memories
                access_bonus = min(0.2, memory.access_count / 100)  # Max bonus of 0.2
                new_importance = memory.importance * decay_factor + access_bonus
                
                # Limit to range [0.0, 1.0]
                new_importance = max(0.0, min(1.0, new_importance))
                
                # Update memory importance
                if abs(new_importance - memory.importance) > 0.01:  # Only update if significant change
                    memory.importance = new_importance
                    self.update_memory(memory.id, {"importance": new_importance})
                    count += 1
                    
                    # Prune if below threshold
                    if new_importance < self.importance_threshold:
                        self.prune_memory(memory.id)
        
        # Log decay event
        if self.events_node and count > 0:
            self.events_node.log_system_event(
                component="AssociativeMemory",
                event_type="memories_decayed",
                details={
                    "count": count,
                    "time_threshold": time_limit.isoformat()
                }
            )
        
        return count
    
    def prune_memory(self, memory_id: str) -> bool:
        """
        Remove a memory from the system.
        
        Args:
            memory_id: ID of the memory to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Delete the memory node and all its relationships
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value} {{id: $memory_id}})
        DETACH DELETE m
        """
        
        self.knowledge_manager.query(query, {"memory_id": memory_id})
        
        # Log prune event
        if self.events_node:
            self.events_node.log_system_event(
                component="AssociativeMemory",
                event_type="memory_pruned",
                details={
                    "memory_id": memory_id
                }
            )
        
        return True
    
    def _update_memory_access(self, memory_id: str, last_accessed: datetime, access_count: int):
        """Update the access information for a memory."""
        self.knowledge_manager.update_node(
            memory_id,
            {
                "last_accessed": last_accessed.isoformat(),
                "access_count": access_count
            }
        )
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            Dict: Memory statistics
        """
        # Query for memory stats
        query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        RETURN 
            count(m) as total_memories,
            avg(m.importance) as avg_importance,
            avg(m.access_count) as avg_access_count,
            min(datetime(m.timestamp)) as oldest_memory,
            max(datetime(m.timestamp)) as newest_memory,
            count(CASE WHEN m.importance < {self.importance_threshold} THEN 1 END) as low_importance_count
        """
        
        result = self.knowledge_manager.query(query)
        
        if not result:
            return {
                "total_memories": 0,
                "avg_importance": 0,
                "avg_access_count": 0,
                "oldest_memory": None,
                "newest_memory": None,
                "low_importance_count": 0,
                "memory_types": {}
            }
        
        stats = {
            "total_memories": result[0].get("total_memories", 0),
            "avg_importance": result[0].get("avg_importance", 0),
            "avg_access_count": result[0].get("avg_access_count", 0),
            "oldest_memory": result[0].get("oldest_memory"),
            "newest_memory": result[0].get("newest_memory"),
            "low_importance_count": result[0].get("low_importance_count", 0)
        }
        
        # Query for memory type distribution
        type_query = f"""
        MATCH (m:{NodeLabel.MEMORY.value})
        RETURN m.memory_type as type, count(*) as count
        ORDER BY count DESC
        """
        
        type_result = self.knowledge_manager.query(type_query)
        
        memory_types = {}
        for record in type_result:
            if record.get("type") and record.get("count"):
                memory_types[record["type"]] = record["count"]
        
        stats["memory_types"] = memory_types
        
        return stats
