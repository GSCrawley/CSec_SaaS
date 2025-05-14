"""
Knowledge Graph Schema Module.

This module defines the core schema for the knowledge graph,
including node types, relationships, and constraints.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


class NodeLabel(str, Enum):
    """Core node labels in the knowledge graph."""
    DOMAIN = "Domain"
    PROJECT = "Project"
    COMPONENT = "Component"
    REQUIREMENT = "Requirement"
    IMPLEMENTATION = "Implementation"
    PATTERN = "Pattern" 
    DECISION = "Decision"
    AGENT = "Agent"


class RelationshipType(str, Enum):
    """Core relationship types in the knowledge graph."""
    BELONGS_TO = "BELONGS_TO"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    USES_PATTERN = "USES_PATTERN"
    MADE_BY = "MADE_BY"
    SATISFIES = "SATISFIES"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"
    RELATED_TO = "RELATED_TO"


class SchemaProperty(BaseModel):
    """Definition of a property in the schema."""
    name: str
    data_type: str
    required: bool = False
    description: Optional[str] = None
    default_value: Optional[str] = None
    constraints: Optional[List[str]] = None


class NodeSchema(BaseModel):
    """Schema definition for a node type."""
    label: str
    properties: List[SchemaProperty]
    description: Optional[str] = None
    constraints: Optional[List[str]] = None


class RelationshipSchema(BaseModel):
    """Schema definition for a relationship type."""
    type: str
    source_labels: List[str]
    target_labels: List[str]
    properties: Optional[List[SchemaProperty]] = None
    description: Optional[str] = None
    constraints: Optional[List[str]] = None


class KnowledgeGraphSchema(BaseModel):
    """Complete knowledge graph schema definition."""
    nodes: Dict[str, NodeSchema]
    relationships: Dict[str, RelationshipSchema]
    description: Optional[str] = None


# Core Schema Definition

CORE_NODE_SCHEMAS = {
    NodeLabel.DOMAIN: NodeSchema(
        label=NodeLabel.DOMAIN,
        description="A knowledge or application domain (e.g., cybersecurity, healthcare)",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (d:Domain) ASSERT d.id IS UNIQUE"]
    ),
    
    NodeLabel.PROJECT: NodeSchema(
        label=NodeLabel.PROJECT,
        description="A development initiative with specific goals and requirements",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=False),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (p:Project) ASSERT p.id IS UNIQUE"]
    ),
    
    NodeLabel.COMPONENT: NodeSchema(
        label=NodeLabel.COMPONENT,
        description="Modular parts of the system being developed",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=False),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (c:Component) ASSERT c.id IS UNIQUE"]
    ),
    
    NodeLabel.REQUIREMENT: NodeSchema(
        label=NodeLabel.REQUIREMENT,
        description="Functional and non-functional specifications",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="priority", data_type="string", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (r:Requirement) ASSERT r.id IS UNIQUE"]
    ),
    
    NodeLabel.IMPLEMENTATION: NodeSchema(
        label=NodeLabel.IMPLEMENTATION,
        description="Actual code or configurations",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="path", data_type="string", required=True),
            SchemaProperty(name="language", data_type="string", required=False),
            SchemaProperty(name="version", data_type="string", required=False),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (i:Implementation) ASSERT i.id IS UNIQUE"]
    ),
    
    NodeLabel.PATTERN: NodeSchema(
        label=NodeLabel.PATTERN,
        description="Reusable design and architecture patterns",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (p:Pattern) ASSERT p.id IS UNIQUE"]
    ),
    
    NodeLabel.DECISION: NodeSchema(
        label=NodeLabel.DECISION,
        description="Key architectural or development decisions",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="title", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="context", data_type="string", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (d:Decision) ASSERT d.id IS UNIQUE"]
    ),
    
    NodeLabel.AGENT: NodeSchema(
        label=NodeLabel.AGENT,
        description="AI agents in the Development Crew",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="layer", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=False),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT ON (a:Agent) ASSERT a.id IS UNIQUE"]
    ),
}

CORE_RELATIONSHIP_SCHEMAS = {
    RelationshipType.BELONGS_TO: RelationshipSchema(
        type=RelationshipType.BELONGS_TO,
        description="Links entities to their parent domain or project",
        source_labels=[
            NodeLabel.COMPONENT,
            NodeLabel.REQUIREMENT,
            NodeLabel.IMPLEMENTATION,
            NodeLabel.PATTERN,
            NodeLabel.DECISION,
            NodeLabel.AGENT,
            NodeLabel.PROJECT
        ],
        target_labels=[
            NodeLabel.DOMAIN,
            NodeLabel.PROJECT
        ],
        properties=[
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.DEPENDS_ON: RelationshipSchema(
        type=RelationshipType.DEPENDS_ON,
        description="Captures dependencies between components",
        source_labels=[
            NodeLabel.COMPONENT,
            NodeLabel.IMPLEMENTATION,
            NodeLabel.REQUIREMENT
        ],
        target_labels=[
            NodeLabel.COMPONENT,
            NodeLabel.IMPLEMENTATION,
            NodeLabel.REQUIREMENT
        ],
        properties=[
            SchemaProperty(name="dependency_type", data_type="string", required=False),
            SchemaProperty(name="strength", data_type="float", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.IMPLEMENTS: RelationshipSchema(
        type=RelationshipType.IMPLEMENTS,
        description="Shows which components implement which requirements",
        source_labels=[
            NodeLabel.COMPONENT,
            NodeLabel.IMPLEMENTATION
        ],
        target_labels=[
            NodeLabel.REQUIREMENT
        ],
        properties=[
            SchemaProperty(name="status", data_type="string", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.USES_PATTERN: RelationshipSchema(
        type=RelationshipType.USES_PATTERN,
        description="Associates components with design patterns",
        source_labels=[
            NodeLabel.COMPONENT,
            NodeLabel.IMPLEMENTATION
        ],
        target_labels=[
            NodeLabel.PATTERN
        ],
        properties=[
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.MADE_BY: RelationshipSchema(
        type=RelationshipType.MADE_BY,
        description="Links decisions to agents who made them",
        source_labels=[
            NodeLabel.DECISION
        ],
        target_labels=[
            NodeLabel.AGENT
        ],
        properties=[
            SchemaProperty(name="context", data_type="string", required=False),
            SchemaProperty(name="confidence", data_type="float", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.SATISFIES: RelationshipSchema(
        type=RelationshipType.SATISFIES,
        description="Shows how implementations fulfill requirements",
        source_labels=[
            NodeLabel.IMPLEMENTATION
        ],
        target_labels=[
            NodeLabel.REQUIREMENT
        ],
        properties=[
            SchemaProperty(name="satisfaction_level", data_type="float", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.CONTRIBUTES_TO: RelationshipSchema(
        type=RelationshipType.CONTRIBUTES_TO,
        description="Shows how agents contribute to components",
        source_labels=[
            NodeLabel.AGENT
        ],
        target_labels=[
            NodeLabel.COMPONENT,
            NodeLabel.IMPLEMENTATION
        ],
        properties=[
            SchemaProperty(name="contribution_type", data_type="string", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.RELATED_TO: RelationshipSchema(
        type=RelationshipType.RELATED_TO,
        description="General relationship between entities",
        source_labels=[n.value for n in NodeLabel],
        target_labels=[n.value for n in NodeLabel],
        properties=[
            SchemaProperty(name="relationship_type", data_type="string", required=False),
            SchemaProperty(name="strength", data_type="float", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
}

# Create the core schema
CORE_SCHEMA = KnowledgeGraphSchema(
    nodes=CORE_NODE_SCHEMAS,
    relationships=CORE_RELATIONSHIP_SCHEMAS,
    description="Core schema for the Development Crew knowledge graph"
)


class SchemaManager:
    """Manages the knowledge graph schema."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize schema manager.
        
        Args:
            connection: Neo4j connection.
        """
        self.connection = connection
        
    def initialize_schema(self, schema: Optional[KnowledgeGraphSchema] = None):
        """Initialize the knowledge graph schema.
        
        Args:
            schema: Optional schema to initialize. If None, uses the core schema.
        """
        schema = schema or CORE_SCHEMA
        
        # Create constraints for node types
        for node_schema in schema.nodes.values():
            if node_schema.constraints:
                for constraint_query in node_schema.constraints:
                    try:
                        self.connection.query(constraint_query)
                        logger.info(f"Created constraint: {constraint_query}")
                    except Exception as e:
                        logger.error(f"Failed to create constraint: {e}")
        
        # Create indexes for common properties
        index_queries = [
            "CREATE INDEX ON :Domain(name)",
            "CREATE INDEX ON :Project(name)",
            "CREATE INDEX ON :Component(name)",
            "CREATE INDEX ON :Requirement(name)",
            "CREATE INDEX ON :Pattern(name)",
            "CREATE INDEX ON :Agent(name, type)",
        ]
        
        for query in index_queries:
            try:
                self.connection.query(query)
                logger.info(f"Created index: {query}")
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
    
    def extend_for_domain(self, domain_name: str, schema_extensions: Dict):
        """Extend the knowledge graph schema for a specific domain.
        
        Args:
            domain_name: Name of the domain.
            schema_extensions: Schema extensions for the domain.
        """
        # Create domain node if it doesn't exist
        domain_query = """
        MERGE (d:Domain {name: $domain_name})
        ON CREATE SET d.id = $domain_id,
                      d.description = $domain_name + ' domain',
                      d.created_at = datetime(),
                      d.updated_at = datetime()
        RETURN d
        """
        
        domain_id = domain_name.lower().replace(' ', '_')
        self.connection.query(
            domain_query, 
            {"domain_name": domain_name, "domain_id": domain_id}
        )
        logger.info(f"Created or ensured domain: {domain_name}")
        
        # Add domain-specific node labels and constraints
        for node_type, properties in schema_extensions.get("nodes", {}).items():
            # Create compound label for domain-specific nodes
            compound_label = f"{domain_name.replace(' ', '')}{node_type}"
            
            # Create constraint for the new node type
            constraint_query = f"CREATE CONSTRAINT ON (n:{compound_label}) ASSERT n.id IS UNIQUE"
            try:
                self.connection.query(constraint_query)
                logger.info(f"Created constraint for domain-specific node: {compound_label}")
            except Exception as e:
                logger.error(f"Failed to create constraint for {compound_label}: {e}")
        
        # Add domain-specific relationship types
        for rel_type in schema_extensions.get("relationships", {}):
            logger.info(f"Registered domain-specific relationship: {rel_type}")
    
    def validate_entity(self, label: str, properties: Dict) -> Tuple[bool, List[str]]:
        """Validate entity properties against schema.
        
        Args:
            label: Node label.
            properties: Entity properties.
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if label not in CORE_NODE_SCHEMAS:
            return False, [f"Unknown node label: {label}"]
        
        schema = CORE_NODE_SCHEMAS[label]
        errors = []
        
        # Check required properties
        for prop in schema.properties:
            if prop.required and prop.name not in properties:
                errors.append(f"Missing required property: {prop.name}")
        
        # Check property types (basic validation)
        for name, value in properties.items():
            prop_schema = next((p for p in schema.properties if p.name == name), None)
            if prop_schema:
                if prop_schema.data_type == "string" and not isinstance(value, str):
                    errors.append(f"Property {name} should be a string")
                elif prop_schema.data_type == "float" and not isinstance(value, (float, int)):
                    errors.append(f"Property {name} should be a number")
        
        return len(errors) == 0, errors


def create_schema_script() -> str:
    """Generate a Cypher script to create the schema.
    
    Returns:
        Cypher script as a string.
    """
    script_lines = [
        "// Knowledge Graph Schema Creation Script",
        "// Generated automatically by schema.py",
        "",
        "// Create constraints for node uniqueness"
    ]
    
    # Add node constraints
    for node_schema in CORE_NODE_SCHEMAS.values():
        if node_schema.constraints:
            for constraint in node_schema.constraints:
                script_lines.append(constraint + ";")
    
    script_lines.extend([
        "",
        "// Create indexes for performance"
    ])
    
    # Add indexes
    index_queries = [
        "CREATE INDEX ON :Domain(name);",
        "CREATE INDEX ON :Project(name);",
        "CREATE INDEX ON :Component(name);",
        "CREATE INDEX ON :Requirement(name);",
        "CREATE INDEX ON :Pattern(name);",
        "CREATE INDEX ON :Agent(name, type);"
    ]
    script_lines.extend(index_queries)
    
    return "\n".join(script_lines)