"""
Knowledge Graph Repository Module.

This module provides repository classes for interacting with the knowledge graph,
implementing the repository pattern for each core entity type.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from .connection import Neo4jConnection
from .schema import NodeLabel, RelationshipType, SchemaManager

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


class NodeRepository(BaseRepository):
    """Base repository for node operations."""
    
    def __init__(self, connection: Neo4jConnection, label: str, model_class: Type[T]):
        """Initialize node repository.
        
        Args:
            connection: Neo4j connection.
            label: Node label.
            model_class: Pydantic model class for the node.
        """
        super().__init__(connection)
        self.label = label
        self.model_class = model_class
    
    def create(self, data: Union[Dict[str, Any], T]) -> T:
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
        
        # Validate data against schema
        is_valid, errors = self.schema_manager.validate_entity(self.label, data_dict)
        if not is_valid:
            error_msg = f"Invalid data for {self.label}: {', '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Add ID and timestamps if not present
        if 'id' not in data_dict:
            data_dict['id'] = self._generate_id()
        
        now = self._timestamp()
        if 'created_at' not in data_dict:
            data_dict['created_at'] = now
        if 'updated_at' not in data_dict:
            data_dict['updated_at'] = now
        
        # Create node in database
        query = f"""
        CREATE (n:{self.label} $props)
        RETURN n
        """
        result = self.connection.query(query, {"props": data_dict})
        
        if result and result[0].get('n'):
            created_node = result[0]['n']
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
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        RETURN n
        """
        result = self.connection.query(query, {"id": node_id})
        
        if result and result[0].get('n'):
            return self.model_class(**result[0]['n'])
        else:
            return None
    
    def find_by_property(self, property_name: str, property_value: Any) -> List[T]:
        """Find nodes by property value.
        
        Args:
            property_name: Property name.
            property_value: Property value.
            
        Returns:
            List of nodes as model instances.
        """
        query = f"""
        MATCH (n:{self.label})
        WHERE n.{property_name} = $value
        RETURN n
        """
        result = self.connection.query(query, {"value": property_value})
        
        return [self.model_class(**record['n']) for record in result if 'n' in record]
    
    def update(self, node_id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update a node.
        
        Args:
            node_id: Node ID.
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
        
        params = {"id": node_id, **data}
        result = self.connection.query(query, params)
        
        if result and result[0].get('n'):
            return self.model_class(**result[0]['n'])
        else:
            return None
    
    def delete(self, node_id: str) -> bool:
        """Delete a node.
        
        Args:
            node_id: Node ID.
            
        Returns:
            True if deleted, False if not found.
        """
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        result = self.connection.query(query, {"id": node_id})
        
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
        
        return [self.model_class(**record['n']) for record in result if 'n' in record]
    
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
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize relationship repository.
        
        Args:
            connection: Neo4j connection.
        """
        super().__init__(connection)
    
    def create_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Create a relationship between two nodes.
        
        Args:
            source_id: Source node ID.
            source_label: Source node label.
            target_id: Target node ID.
            target_label: Target node label.
            relationship_type: Relationship type.
            properties: Optional relationship properties.
            
        Returns:
            Dictionary with relationship information.
            
        Raises:
            ValueError: If source or target node not found.
        """
        # Add created_at timestamp if not present
        properties = properties or {}
        if 'created_at' not in properties:
            properties['created_at'] = self._timestamp()
        
        query = f"""
        MATCH (source:{source_label} {{id: $source_id}})
        MATCH (target:{target_label} {{id: $target_id}})
        CREATE (source)-[r:{relationship_type} $props]->(target)
        RETURN source, target, r
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
        
        return {
            "source": result[0]['source'],
            "target": result[0]['target'],
            "relationship": result[0]['r'],
            "type": relationship_type
        }
    
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
        query = f"""
        MATCH (p:{NodeLabel.PROJECT})-[:{RelationshipType.BELONGS_TO}]->(d:{NodeLabel.DOMAIN} {{id: $domain_id}})
        RETURN p
        """
        result = self.connection.query(query, {"domain_id": domain_id})
        
        return [ProjectModel(**record['p']) for record in result if 'p' in record]


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
        query = f"""
        MATCH (c:{NodeLabel.COMPONENT})-[:{RelationshipType.BELONGS_TO}]->(p:{NodeLabel.PROJECT} {{id: $project_id}})
        RETURN c
        """
        result = self.connection.query(query, {"project_id": project_id})
        
        return [ComponentModel(**record['c']) for record in result if 'c' in record]
    
    def find_dependent_components(self, component_id: str) -> List[ComponentModel]:
        """Find components that depend on the specified component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of dependent components.
        """
        query = f"""
        MATCH (c:{NodeLabel.COMPONENT})-[:{RelationshipType.DEPENDS_ON}]->(target:{NodeLabel.COMPONENT} {{id: $component_id}})
        RETURN c
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [ComponentModel(**record['c']) for record in result if 'c' in record]
    
    def find_dependencies(self, component_id: str) -> List[ComponentModel]:
        """Find components that the specified component depends on.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of dependency components.
        """
        query = f"""
        MATCH (source:{NodeLabel.COMPONENT} {{id: $component_id}})-[:{RelationshipType.DEPENDS_ON}]->(c:{NodeLabel.COMPONENT})
        RETURN c
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [ComponentModel(**record['c']) for record in result if 'c' in record]


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
        query = f"""
        MATCH (r:{NodeLabel.REQUIREMENT})-[:{RelationshipType.BELONGS_TO}]->(p:{NodeLabel.PROJECT} {{id: $project_id}})
        RETURN r
        """
        result = self.connection.query(query, {"project_id": project_id})
        
        return [RequirementModel(**record['r']) for record in result if 'r' in record]
    
    def find_requirements_for_component(self, component_id: str) -> List[RequirementModel]:
        """Find requirements implemented by a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of requirements.
        """
        query = f"""
        MATCH (c:{NodeLabel.COMPONENT} {{id: $component_id}})-[:{RelationshipType.IMPLEMENTS}]->(r:{NodeLabel.REQUIREMENT})
        RETURN r
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [RequirementModel(**record['r']) for record in result if 'r' in record]


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
        query = f"""
        MATCH (i:{NodeLabel.IMPLEMENTATION})-[:{RelationshipType.BELONGS_TO}]->(c:{NodeLabel.COMPONENT} {{id: $component_id}})
        RETURN i
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [ImplementationModel(**record['i']) for record in result if 'i' in record]
    
    def find_implementations_for_requirement(self, requirement_id: str) -> List[ImplementationModel]:
        """Find implementations that satisfy a requirement.
        
        Args:
            requirement_id: Requirement ID.
            
        Returns:
            List of implementations.
        """
        query = f"""
        MATCH (i:{NodeLabel.IMPLEMENTATION})-[:{RelationshipType.SATISFIES}]->(r:{NodeLabel.REQUIREMENT} {{id: $requirement_id}})
        RETURN i
        """
        result = self.connection.query(query, {"requirement_id": requirement_id})
        
        return [ImplementationModel(**record['i']) for record in result if 'i' in record]


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
        """Find patterns used by a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of patterns.
        """
        query = f"""
        MATCH (c:{NodeLabel.COMPONENT} {{id: $component_id}})-[:{RelationshipType.USES_PATTERN}]->(p:{NodeLabel.PATTERN})
        RETURN p
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [PatternModel(**record['p']) for record in result if 'p' in record]


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
        query = f"""
        MATCH (d:{NodeLabel.DECISION})-[:{RelationshipType.MADE_BY}]->(a:{NodeLabel.AGENT} {{id: $agent_id}})
        RETURN d
        """
        result = self.connection.query(query, {"agent_id": agent_id})
        
        return [DecisionModel(**record['d']) for record in result if 'd' in record]
    
    def find_decisions_for_component(self, component_id: str) -> List[DecisionModel]:
        """Find decisions related to a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of decisions.
        """
        query = f"""
        MATCH (d:{NodeLabel.DECISION})-[:{RelationshipType.RELATED_TO}]->(c:{NodeLabel.COMPONENT} {{id: $component_id}})
        RETURN d
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [DecisionModel(**record['d']) for record in result if 'd' in record]


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
        """Find agents contributing to a component.
        
        Args:
            component_id: Component ID.
            
        Returns:
            List of agents.
        """
        query = f"""
        MATCH (a:{NodeLabel.AGENT})-[:{RelationshipType.CONTRIBUTES_TO}]->(c:{NodeLabel.COMPONENT} {{id: $component_id}})
        RETURN a
        """
        result = self.connection.query(query, {"component_id": component_id})
        
        return [AgentModel(**record['a']) for record in result if 'a' in record]