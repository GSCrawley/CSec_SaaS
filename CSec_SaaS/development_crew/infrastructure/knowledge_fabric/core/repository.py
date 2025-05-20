"""
Knowledge Graph Repository Module.

This module provides repository classes for interacting with the knowledge graph,
implementing the repository pattern for each core entity type.
"""

import logging
import uuid
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Set

from pydantic import BaseModel, Field

from ..utils import convert_neo4j_to_python

from .connection import Neo4jConnection
from .schema import NodeLabel, RelationshipType, SchemaManager
from .dual_knowledge import DualKnowledgeManager

logger = logging.getLogger(__name__)

# Generic type for entity models
T = TypeVar('T', bound=BaseModel)


class EntityModel(BaseModel):
    """Base model for all knowledge graph entities."""
    id: str
    created_at: datetime
    updated_at: datetime


class DomainModel(EntityModel):
    """Model for Domain nodes."""
    name: str
    description: Optional[str] = None


class ProjectModel(EntityModel):
    """Model for Project nodes."""
    name: str
    description: Optional[str] = None
    status: str


class ComponentModel(EntityModel):
    """Model for Component nodes."""
    name: str
    description: Optional[str] = None
    type: str
    status: str


class RequirementModel(EntityModel):
    """Model for Requirement nodes."""
    name: str
    description: str
    type: str
    priority: str
    status: str


class ImplementationModel(EntityModel):
    """Model for Implementation nodes."""
    name: str
    path: str
    language: Optional[str] = None
    version: Optional[str] = None
    status: str


class PatternModel(EntityModel):
    """Model for Pattern nodes."""
    name: str
    description: str
    type: str


class DecisionModel(EntityModel):
    """Model for Decision nodes."""
    title: str
    description: str
    context: str
    status: str


class AgentModel(EntityModel):
    """Model for Agent nodes."""
    name: str
    type: str
    layer: str
    description: Optional[str] = None
    status: str


class EventModel(EntityModel):
    """Model for Event nodes in the Digital Genome Architecture."""
    type: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class EventSequenceModel(EntityModel):
    """Model for EventSequence nodes in the Digital Genome Architecture."""
    name: str
    event_count: int
    metadata: Optional[Dict[str, Any]] = None


class FunctionalRequirementModel(EntityModel):
    """Model for FunctionalRequirement nodes in the Digital Genome Architecture."""
    name: str
    description: str
    priority: str
    status: str


class NonFunctionalRequirementModel(EntityModel):
    """Model for NonFunctionalRequirement nodes in the Digital Genome Architecture."""
    name: str
    description: str
    type: str
    priority: str
    status: str


class PolicyModel(EntityModel):
    """Model for Policy nodes in the Digital Genome Architecture."""
    name: str
    description: str
    domain: str
    enforcement: str


class WorkflowModel(EntityModel):
    """Model for Workflow nodes in the Digital Genome Architecture."""
    name: str
    description: str
    status: str


class WorkflowStepModel(EntityModel):
    """Model for WorkflowStep nodes in the Digital Genome Architecture."""
    name: str
    description: str
    order: int
    status: str


class RedFlagModel(EntityModel):
    """Model for RedFlag nodes in the Digital Genome Architecture."""
    type: str
    description: str
    severity: str
    status: str
    timestamp: datetime
    resolved_at: Optional[datetime] = None


class GenomicAgentModel(EntityModel):
    """Model for GenomicAgent nodes in the Digital Genome Architecture."""
    name: str
    type: str
    layer: str
    description: Optional[str] = None
    status: str
    policies: Optional[List[str]] = None


class RelationshipModel(BaseModel):
    """Model for relationships in the knowledge graph."""
    source_id: str
    target_id: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class BaseRepository:
    """Base repository class for knowledge graph operations."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize repository.
        
        Args:
            connection: Neo4j connection.
        """
        self.connection = connection
        self.schema_manager = SchemaManager(connection)
    
    def _timestamp(self) -> datetime:
        """Get current timestamp.
        
        Returns:
            Current datetime.
        """
        return datetime.now()
    
    def _generate_id(self) -> str:
        """Generate a unique ID.
        
        Returns:
            Unique ID string.
        """
        return str(uuid.uuid4())
        
    def _convert_neo4j_types(self, data: Dict) -> Dict:
        """Convert Neo4j types to Python types.
        
        Args:
            data: Dictionary with Neo4j values.
            
        Returns:
            Dictionary with Python values.
        """
        result = {}
        for key, value in data.items():
            # Convert Neo4j DateTime to Python datetime
            if hasattr(value, '__class__') and value.__class__.__name__ == 'DateTime':
                result[key] = datetime(
                    year=value.year, 
                    month=value.month, 
                    day=value.day,
                    hour=value.hour,
                    minute=value.minute, 
                    second=value.second,
                    microsecond=value.nanosecond // 1000  # Convert nanoseconds to microseconds
                )
            else:
                result[key] = value
                
        return result


class NodeRepository(BaseRepository):
    """Base repository for node operations."""
    
    def __init__(self, connection: Neo4jConnection, label: str, model_class: Type[T], dual_knowledge_manager: Optional[DualKnowledgeManager] = None):
        """Initialize node repository.
        
        Args:
            connection: Neo4j connection.
            label: Node label.
            model_class: Pydantic model class for the node.
        """
        super().__init__(connection)
        self.label = label
        self.model_class = model_class
        self.dual_knowledge_manager = dual_knowledge_manager
        
    def create_node(self, label, properties):
        """Create a node in the graph (adapter for EventsNode compatibility).
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            ID of created node
        """
        # Convert label enum to string if needed
        if hasattr(label, 'value'):
            label = label.value
            
        # Add required timestamp properties if not present
        if 'created_at' not in properties:
            properties['created_at'] = datetime.now()
        if 'updated_at' not in properties:
            properties['updated_at'] = datetime.now()
        if 'id' not in properties:
            properties['id'] = self._generate_id()
            
        # Use the connection's query method as it accepts raw queries
        query = f"""
        CREATE (n:{label} $props)
        RETURN ID(n) as id
        """
        
        result = self.connection.query(query, {"props": properties})
        return result[0]['id'] if result else None
        
    def create_relationship(self, source_id, target_id, relationship_type, properties=None):
        """Create a relationship between nodes (adapter for EventsNode compatibility).
        
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
        
        result = self.connection.query(query, params)
        return True if result else False
        
    def query(self, query, parameters=None):
        """Execute a query against the Neo4j database (adapter for AssociativeMemory compatibility).
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of query results
        """
        return self.connection.query(query, parameters)
        
    def update_node(self, node_id, properties):
        """Update a node with new properties (adapter for AssociativeMemory compatibility).
        
        Args:
            node_id: ID of the node to update
            properties: Properties to update
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure we have the updated_at property set
        if 'updated_at' not in properties:
            properties['updated_at'] = datetime.now().isoformat()
            
        # Build the SET clause for each property
        set_clauses = [f"n.{key} = ${key}" for key in properties.keys()]
        set_statement = ", ".join(set_clauses)
        
        # Create and execute the query
        query = f"""
        MATCH (n)
        WHERE n.id = $node_id
        SET {set_statement}
        RETURN n
        """
        
        # Add node_id to parameters
        params = {**properties, "node_id": node_id}
        
        # Execute the query
        result = self.connection.query(query, params)
        return bool(result)
    
    def create(self, data: Union[Dict[str, Any], T], sync_to_shared: bool = False) -> T:
        """Create a new node.
        
        Args:
            data: Node data as dictionary or model instance.
            
        Returns:
            Created node as model instance.
            
        Raises:
            ValueError: If data validation fails.
        """
        # Convert model to dict if needed
        if isinstance(data, BaseModel):
            data_dict = data.dict()
        else:
            data_dict = dict(data)
        
        # Add ID and timestamps if not present
        now = self._timestamp()
        
        if 'id' not in data_dict:
            data_dict['id'] = self._generate_id()
        
        if 'created_at' not in data_dict:
            data_dict['created_at'] = now
            
        # Convert Dict metadata/context to JSON strings if present
        if 'metadata' in data_dict and isinstance(data_dict['metadata'], dict):
            data_dict['metadata'] = json.dumps(data_dict['metadata'])
            
        if 'context' in data_dict and isinstance(data_dict['context'], dict):
            data_dict['context'] = json.dumps(data_dict['context'])
        
        if 'updated_at' not in data_dict:
            data_dict['updated_at'] = now
        
        # Validate data against schema
        is_valid, errors = self.schema_manager.validate_entity(self.label, data_dict)
        if not is_valid:
            error_msg = f"Invalid data for {self.label}: {', '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create node in database
        # Extract the string value from the Enum if necessary
        label_str = self.label.value if isinstance(self.label, Enum) else self.label
        query = f"""
            CREATE (n:{label_str} $props)
            RETURN n
            """
        result = self.connection.query(query, {"props": data_dict})
        
        if result and len(result) > 0 and 'n' in result[0]:
            # Neo4j returns a Node object which we need to convert to a dictionary
            created_node = dict(result[0]['n'])
            
            # Convert Neo4j DateTime objects to Python datetime objects
            for key, value in created_node.items():
                if hasattr(value, '__class__') and value.__class__.__name__ == 'DateTime':
                    created_node[key] = datetime(
                        year=value.year, 
                        month=value.month, 
                        day=value.day,
                        hour=value.hour,
                        minute=value.minute, 
                        second=value.second,
                        microsecond=value.nanosecond // 1000  # Convert nanoseconds to microseconds
                    )
            
            # Create and return model instance
            return self.model_class(**created_node)
        else:
            error_msg = f"Failed to create {self.label} node"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def find_by_id(self, node_id: str) -> Optional[T]:
        """Find node by ID.
        
        Args:
            node_id: Node ID.
            
        Returns:
            Node as model instance, or None if not found.
        """
        label_str = self.label.value if isinstance(self.label, Enum) else self.label
        query = f"""
        MATCH (n:{label_str} {{id: $id}})
        RETURN n
        """
        result = self.connection.query(query, {"id": node_id})
        
        if result and result[0].get('n'):
            # Convert Neo4j node to dictionary and convert Neo4j types to Python types
            node_data = convert_neo4j_to_python(result[0]['n'])
            return self.model_class(**node_data)
        else:
            return None
    
    def find_by_property(self, property_name: str, property_value: Any) -> List[T]:
        """Find nodes by a property value.
        
        Args:
            property_name: Property name.
            property_value: Property value.
            
        Returns:
            List of nodes as model instances.
        """
        # Convert Enum value to string if needed
        label_str = self.label.value if hasattr(self.label, 'value') else self.label
        
        query = f"""
        MATCH (n:{label_str})
        WHERE n.{property_name} = $value
        RETURN n
        """
        result = self.connection.query(query, {"value": property_value})
        
        return [self.model_class(**convert_neo4j_to_python(record['n'])) for record in result if 'n' in record]
    
    def update(self, entity_id: str, data: Union[Dict[str, Any], T], sync_to_shared: bool = False) -> Optional[T]:
        """Update a node.
        
        Args:
            entity_id: Node ID.
            data: New node data.
            
        Returns:
            Updated node as model instance, or None if not found.
        """
        # Never update the ID
        if 'id' in data:
            del data['id']
        
        # Always update the updated_at timestamp
        data['updated_at'] = self._timestamp()
        
        properties_set = ", ".join([f"n.{key} = ${key}" for key in data.keys()])
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        SET {properties_set}
        RETURN n
        """
        
        params = {"id": entity_id, **data}
        result = self.connection.query(query, params)
        
        if result and result[0].get('n'):
            # Convert Neo4j node to dictionary and convert Neo4j types to Python types
            node_data = convert_neo4j_to_python(result[0]['n'])
            return self.model_class(**node_data)
        else:
            return None
    
    def delete(self, entity_id: str, sync_to_shared: bool = False) -> bool:
        """Delete a node.
        
        Args:
            entity_id: Node ID.
            
        Returns:
            True if deleted, False if not found.
        """
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        result = self.connection.query(query, {"id": entity_id})
        
        return result[0]['deleted_count'] > 0 if result else False
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all nodes of this type.
        
        Args:
            limit: Maximum number of nodes to return.
            offset: Number of nodes to skip.
            
        Returns:
            List of nodes as model instances.
        """
        query = f"""
        MATCH (n:{self.label})
        RETURN n
        SKIP {offset}
        LIMIT {limit}
        """
        result = self.connection.query(query)
        
        return [self.model_class(**convert_neo4j_to_python(record['n'])) for record in result if 'n' in record]
    
    def count(self) -> int:
        """Count nodes of this type.
        
        Returns:
            Number of nodes.
        """
        query = f"""
        MATCH (n:{self.label})
        RETURN count(n) as count
        """
        result = self.connection.query(query)
        
        return result[0]['count'] if result else 0


class RelationshipRepository(BaseRepository):
    """Repository for relationship operations."""
    
    def __init__(self, connection: Neo4jConnection, dual_knowledge_manager: Optional[DualKnowledgeManager] = None):
        """Initialize relationship repository.
        
        Args:
            connection: Neo4j connection.
        """
        super().__init__(connection)
        self.dual_knowledge_manager = dual_knowledge_manager
    
    def create_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
        sync_to_shared: bool = False
    ) -> str:
        """Create a relationship between two nodes.
        
        Args:
            source_id: Source node ID.
            source_label: Source node label.
            target_id: Target node ID.
            target_label: Target node label.
            relationship_type: Relationship type.
            properties: Optional relationship properties.
            
        Returns:
            Relationship ID.
            
        Raises:
            ValueError: If source or target node not found.
        """
        # Add created_at timestamp if not present
        properties = properties or {}
        if 'created_at' not in properties:
            properties['created_at'] = self._timestamp()
        
        # Convert Enum objects to string values if needed
        source_label_str = source_label.value if hasattr(source_label, 'value') else source_label
        target_label_str = target_label.value if hasattr(target_label, 'value') else target_label
        relationship_type_str = relationship_type.value if hasattr(relationship_type, 'value') else relationship_type
        
        query = f"""
        MATCH (source:{source_label_str} {{id: $source_id}})
        MATCH (target:{target_label_str} {{id: $target_id}})
        CREATE (source)-[r:{relationship_type_str} $props]->(target)
        RETURN id(r) as relationship_id
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "props": properties
        }
        
        result = self.connection.query(query, params)
        
        if not result:
            error_msg = (f"Failed to create relationship {relationship_type} from "
                        f"{source_label}:{source_id} to {target_label}:{target_id}")
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return result[0]['relationship_id']
    
    def find_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        source_label: Optional[str] = None,
        target_label: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Find relationships matching criteria.
        
        Args:
            source_id: Optional source node ID.
            target_id: Optional target node ID.
            relationship_type: Optional relationship type.
            source_label: Optional source node label.
            target_label: Optional target node label.
            limit: Maximum number of relationships to return.
            
        Returns:
            List of dictionaries with relationship information.
        """
        # Build match clause based on provided filters
        match_clause = "MATCH (source)"
        if source_label:
            match_clause = f"MATCH (source:{source_label})"
        
        rel_clause = "-[r]->"
        if relationship_type:
            rel_clause = f"-[r:{relationship_type}]->"
        
        target_clause = "(target)"
        if target_label:
            target_clause = f"(target:{target_label})"
        
        where_clauses = []
        params = {}
        
        if source_id:
            where_clauses.append("source.id = $source_id")
            params["source_id"] = source_id
        
        if target_id:
            where_clauses.append("target.id = $target_id")
            params["target_id"] = target_id
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        query = f"""
        {match_clause}{rel_clause}{target_clause}
        {where_clause}
        RETURN source, target, r
        LIMIT {limit}
        """
        
        result = self.connection.query(query, params)
        
        return [
            {
                "source": record['source'],
                "target": record['target'],
                "relationship": record['r'],
                "type": record['r'].type
            }
            for record in result if 'source' in record and 'target' in record and 'r' in record
        ]
    
    def delete_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: Optional[str] = None
    ) -> bool:
        """Delete relationship(s) between two nodes.
        
        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            relationship_type: Optional relationship type. If None, deletes all relationships.
            
        Returns:
            True if any relationships deleted, False otherwise.
        """
        rel_clause = "-[r]->"
        if relationship_type:
            rel_clause = f"-[r:{relationship_type}]->"
        
        query = f"""
        MATCH (source {{id: $source_id}}){rel_clause}(target {{id: $target_id}})
        DELETE r
        RETURN count(r) as deleted_count
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id
        }
        
        result = self.connection.query(query, params)
        
        return result[0]['deleted_count'] > 0 if result else False


# Concrete repositories for each node type

class DomainRepository(NodeRepository):
    """Repository for Domain nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize domain repository."""
        super().__init__(connection, NodeLabel.DOMAIN, DomainModel)


class ProjectRepository(NodeRepository):
    """Repository for Project nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize project repository."""
        super().__init__(connection, NodeLabel.PROJECT, ProjectModel)
    
    def find_projects_by_domain(self, domain_id: str) -> List[ProjectModel]:
        """Find projects belonging to a domain.
        
        Args:
            domain_id: Domain ID.
            
        Returns:
            List of projects.
        """
        # Convert Enum values to strings
        project_label = NodeLabel.PROJECT.value if hasattr(NodeLabel.PROJECT, 'value') else NodeLabel.PROJECT
        belongs_to_rel = RelationshipType.BELONGS_TO.value if hasattr(RelationshipType.BELONGS_TO, 'value') else RelationshipType.BELONGS_TO
        domain_label = NodeLabel.DOMAIN.value if hasattr(NodeLabel.DOMAIN, 'value') else NodeLabel.DOMAIN
        
        query = f"""
        MATCH (p:{project_label})-[:{belongs_to_rel}]->(d:{domain_label} {{id: $domain_id}})
        RETURN p
        """
        result = self.connection.query(query, {"domain_id": domain_id})
        
        return [ProjectModel(**convert_neo4j_to_python(record['p'])) for record in result if 'p' in record]


class ComponentRepository(NodeRepository):
    """Repository for Component nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize component repository."""
        super().__init__(connection, NodeLabel.COMPONENT, ComponentModel)
    
    def find_components_by_project(self, project_id: str) -> List[ComponentModel]:
        """Find components belonging to a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            List of components.
        """
        # Convert Enum values to strings
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        belongs_to_rel = RelationshipType.BELONGS_TO.value if hasattr(RelationshipType.BELONGS_TO, 'value') else RelationshipType.BELONGS_TO
        project_label = NodeLabel.PROJECT.value if hasattr(NodeLabel.PROJECT, 'value') else NodeLabel.PROJECT
        
        query = f"""
        MATCH (c:{component_label})-[:{belongs_to_rel}]->(p:{project_label} {{id: $project_id}})
        RETURN c
        """
        result = self.connection.query(query, {"project_id": project_id})
        
        return [ComponentModel(**convert_neo4j_to_python(record['c'])) for record in result if 'c' in record]
    
    def find_dependent_components(self, component_id: str) -> List[ComponentModel]:
        """Find components that depend on the specified component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of dependent components.
        """
        # Convert Enum values to strings
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        depends_on_rel = RelationshipType.DEPENDS_ON.value if hasattr(RelationshipType.DEPENDS_ON, 'value') else RelationshipType.DEPENDS_ON
        
        query = f"""
        MATCH (c:{component_label})-[:{depends_on_rel}]->(target:{component_label} {{id: $component_id}})
        RETURN c
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [ComponentModel(**convert_neo4j_to_python(record['c'])) for record in result if 'c' in record]
    
    def find_dependencies(self, component_id: str) -> List[ComponentModel]:
        """Find dependencies of the specified component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of dependencies.
        """
        # Convert Enum values to strings
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        depends_on_rel = RelationshipType.DEPENDS_ON.value if hasattr(RelationshipType.DEPENDS_ON, 'value') else RelationshipType.DEPENDS_ON
        
        query = f"""
        MATCH (source:{component_label} {{id: $component_id}})-[:{depends_on_rel}]->(c:{component_label})
        RETURN c
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [ComponentModel(**convert_neo4j_to_python(record['c'])) for record in result if 'c' in record]


class RequirementRepository(NodeRepository):
    """Repository for Requirement nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize requirement repository."""
        super().__init__(connection, NodeLabel.REQUIREMENT, RequirementModel)
    
    def find_requirements_by_project(self, project_id: str) -> List[RequirementModel]:
        """Find requirements belonging to a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            List of requirements.
        """
        # Convert Enum values to strings
        requirement_label = NodeLabel.REQUIREMENT.value if hasattr(NodeLabel.REQUIREMENT, 'value') else NodeLabel.REQUIREMENT
        belongs_to_rel = RelationshipType.BELONGS_TO.value if hasattr(RelationshipType.BELONGS_TO, 'value') else RelationshipType.BELONGS_TO
        project_label = NodeLabel.PROJECT.value if hasattr(NodeLabel.PROJECT, 'value') else NodeLabel.PROJECT
        
        query = f"""
        MATCH (r:{requirement_label})-[:{belongs_to_rel}]->(p:{project_label} {{id: $project_id}})
        RETURN r
        """
        result = self.connection.query(query, {"project_id": project_id})
        
        return [RequirementModel(**convert_neo4j_to_python(record['r'])) for record in result if 'r' in record]
    
    def find_requirements_for_component(self, component_id: str) -> List[RequirementModel]:
        """Find requirements implemented by the specified component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of requirements.
        """
        # Convert Enum values to strings
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        implements_rel = RelationshipType.IMPLEMENTS.value if hasattr(RelationshipType.IMPLEMENTS, 'value') else RelationshipType.IMPLEMENTS
        requirement_label = NodeLabel.REQUIREMENT.value if hasattr(NodeLabel.REQUIREMENT, 'value') else NodeLabel.REQUIREMENT
        
        query = f"""
        MATCH (c:{component_label} {{id: $component_id}})-[:{implements_rel}]->(r:{requirement_label})
        RETURN r
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [RequirementModel(**convert_neo4j_to_python(record['r'])) for record in result if 'r' in record]


class ImplementationRepository(NodeRepository):
    """Repository for Implementation nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize implementation repository."""
        super().__init__(connection, NodeLabel.IMPLEMENTATION, ImplementationModel)
    
    def find_implementations_by_component(self, component_id: str) -> List[ImplementationModel]:
        """Find implementations belonging to a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of implementations.
        """
        # Convert Enum values to strings
        implementation_label = NodeLabel.IMPLEMENTATION.value if hasattr(NodeLabel.IMPLEMENTATION, 'value') else NodeLabel.IMPLEMENTATION
        belongs_to_rel = RelationshipType.BELONGS_TO.value if hasattr(RelationshipType.BELONGS_TO, 'value') else RelationshipType.BELONGS_TO
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        
        query = f"""
        MATCH (i:{implementation_label})-[:{belongs_to_rel}]->(c:{component_label} {{id: $component_id}})
        RETURN i
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [ImplementationModel(**convert_neo4j_to_python(record['i'])) for record in result if 'i' in record]
    
    def find_implementations_for_requirement(self, requirement_id: str) -> List[ImplementationModel]:
        """Find implementations that satisfy a requirement.
        
        Args:
            requirement_id: Requirement ID.
            
        Returns:
            List of implementations.
        """
        # Convert Enum values to strings
        implementation_label = NodeLabel.IMPLEMENTATION.value if hasattr(NodeLabel.IMPLEMENTATION, 'value') else NodeLabel.IMPLEMENTATION
        satisfies_rel = RelationshipType.SATISFIES.value if hasattr(RelationshipType.SATISFIES, 'value') else RelationshipType.SATISFIES
        requirement_label = NodeLabel.REQUIREMENT.value if hasattr(NodeLabel.REQUIREMENT, 'value') else NodeLabel.REQUIREMENT
        
        query = f"""
        MATCH (i:{implementation_label})-[:{satisfies_rel}]->(r:{requirement_label} {{id: $requirement_id}})
        RETURN i
        """
        result = self.connection.query(query, {"requirement_id": requirement_id})
        
        return [ImplementationModel(**convert_neo4j_to_python(record['i'])) for record in result if 'i' in record]


class PatternRepository(NodeRepository):
    """Repository for Pattern nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize pattern repository."""
        super().__init__(connection, NodeLabel.PATTERN, PatternModel)
    
    def find_patterns_by_type(self, pattern_type: str) -> List[PatternModel]:
        """Find patterns by type.
        
        Args:
            pattern_type: Pattern type.
            
        Returns:
            List of patterns.
        """
        return self.find_by_property("type", pattern_type)
    
    def find_patterns_used_by_component(self, component_id: str) -> List[PatternModel]:
        """Find design patterns used by a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of patterns.
        """
        # Convert Enum values to strings
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        uses_pattern_rel = RelationshipType.USES_PATTERN.value if hasattr(RelationshipType.USES_PATTERN, 'value') else RelationshipType.USES_PATTERN
        pattern_label = NodeLabel.PATTERN.value if hasattr(NodeLabel.PATTERN, 'value') else NodeLabel.PATTERN
        
        query = f"""
        MATCH (c:{component_label} {{id: $component_id}})-[:{uses_pattern_rel}]->(p:{pattern_label})
        RETURN p
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [PatternModel(**convert_neo4j_to_python(record['p'])) for record in result if 'p' in record]


class DecisionRepository(NodeRepository):
    """Repository for Decision nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize decision repository."""
        super().__init__(connection, NodeLabel.DECISION, DecisionModel)
    
    def find_decisions_by_agent(self, agent_id: str) -> List[DecisionModel]:
        """Find decisions made by an agent.
        
        Args:
            agent_id: Agent ID.
            
        Returns:
            List of decisions.
        """
        # Convert Enum values to strings
        decision_label = NodeLabel.DECISION.value if hasattr(NodeLabel.DECISION, 'value') else NodeLabel.DECISION
        made_by_rel = RelationshipType.MADE_BY.value if hasattr(RelationshipType.MADE_BY, 'value') else RelationshipType.MADE_BY
        agent_label = NodeLabel.AGENT.value if hasattr(NodeLabel.AGENT, 'value') else NodeLabel.AGENT
        
        query = f"""
        MATCH (d:{decision_label})-[:{made_by_rel}]->(a:{agent_label} {{id: $agent_id}})
        RETURN d
        """
        result = self.connection.query(query, {"agent_id": agent_id})
        
        return [DecisionModel(**convert_neo4j_to_python(record['d'])) for record in result if 'd' in record]
    
    def find_decisions_for_component(self, component_id: str) -> List[DecisionModel]:
        """Find decisions related to a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of decisions.
        """
        # Convert Enum values to strings
        decision_label = NodeLabel.DECISION.value if hasattr(NodeLabel.DECISION, 'value') else NodeLabel.DECISION
        related_to_rel = RelationshipType.RELATED_TO.value if hasattr(RelationshipType.RELATED_TO, 'value') else RelationshipType.RELATED_TO
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        
        query = f"""
        MATCH (d:{decision_label})-[:{related_to_rel}]->(c:{component_label} {{id: $component_id}})
        RETURN d
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [DecisionModel(**convert_neo4j_to_python(record['d'])) for record in result if 'd' in record]


class AgentRepository(NodeRepository):
    """Repository for Agent nodes."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize agent repository."""
        super().__init__(connection, NodeLabel.AGENT, AgentModel)
    
    def find_agents_by_layer(self, layer: str) -> List[AgentModel]:
        """Find agents by layer.
        
        Args:
            layer: Agent layer.
            
        Returns:
            List of agents.
        """
        return self.find_by_property("layer", layer)
    
    def find_agents_by_type(self, agent_type: str) -> List[AgentModel]:
        """Find agents by type.
        
        Args:
            agent_type: Agent type.
            
        Returns:
            List of agents.
        """
        return self.find_by_property("type", agent_type)
    
    def find_agents_contributing_to_component(self, component_id: str) -> List[AgentModel]:
        """Find agents that contribute to a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of agents.
        """
        # Convert Enum values to strings
        agent_label = NodeLabel.AGENT.value if hasattr(NodeLabel.AGENT, 'value') else NodeLabel.AGENT
        contributes_to_rel = RelationshipType.CONTRIBUTES_TO.value if hasattr(RelationshipType.CONTRIBUTES_TO, 'value') else RelationshipType.CONTRIBUTES_TO
        component_label = NodeLabel.COMPONENT.value if hasattr(NodeLabel.COMPONENT, 'value') else NodeLabel.COMPONENT
        
        query = f"""
        MATCH (a:{agent_label})-[:{contributes_to_rel}]->(c:{component_label} {{id: $component_id}})
        RETURN a
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [AgentModel(**convert_neo4j_to_python(record['a'])) for record in result if 'a' in record]