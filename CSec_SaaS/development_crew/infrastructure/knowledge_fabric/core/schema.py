"""
Knowledge Graph Schema Module.

This module defines the core schema for the knowledge graph,
including node types, relationships, and constraints.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union
from datetime import datetime

from pydantic import BaseModel, Field

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


class NodeLabel(str, Enum):
    """Core node labels in the knowledge graph."""
    # Original labels
    DOMAIN = "Domain"
    PROJECT = "Project"
    COMPONENT = "Component"
    REQUIREMENT = "Requirement"
    IMPLEMENTATION = "Implementation"
    PATTERN = "Pattern" 
    DECISION = "Decision"
    AGENT = "Agent"
    
    # Digital Genome Architecture labels
    EVENT = "Event"
    EVENT_SEQUENCE = "EventSequence"
    FUNCTIONAL_REQUIREMENT = "FunctionalRequirement"
    NON_FUNCTIONAL_REQUIREMENT = "NonFunctionalRequirement"
    POLICY = "Policy"
    WORKFLOW = "Workflow"
    WORKFLOW_STEP = "WorkflowStep"
    RED_FLAG = "RedFlag"
    GENOMIC_AGENT = "GenomicAgent"
    MEMORY = "Memory"
    
    # Dual Knowledge Manager labels
    DKM_MANAGED_KG = "DKM_ManagedKG"
    DKM_SYNCHRONIZATION_RULE = "DKM_SynchronizationRule"
    DKM_SCHEMA_MAPPING = "DKM_SchemaMapping"
    DKM_KNOWLEDGE_POLICY = "DKM_KnowledgePolicy"


class RelationshipType(str, Enum):
    """Core relationship types in the knowledge graph."""
    # Original types
    BELONGS_TO = "BELONGS_TO"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    USES_PATTERN = "USES_PATTERN"
    MADE_BY = "MADE_BY"
    SATISFIES = "SATISFIES"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"
    RELATED_TO = "RELATED_TO"
    
    # Digital Genome Architecture types
    TRIGGERS = "TRIGGERS"
    GOVERNED_BY = "GOVERNED_BY"
    NEXT_STEP = "NEXT_STEP"
    DETECTED_BY = "DETECTED_BY"
    CONTAINS = "CONTAINS"
    CREATED_BY = "CREATED_BY"
    SYNCHRONIZED_WITH = "SYNCHRONIZED_WITH"
    RESPONDS_TO = "RESPONDS_TO"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    
    # Dual Knowledge Manager relationship types
    SYNCS_WITH = "SYNCS_WITH"
    SYNCS_TO = "SYNCS_TO"
    APPLIES_TO = "APPLIES_TO"
    MAPS_BETWEEN = "MAPS_BETWEEN"
    GOVERNS = "GOVERNS"


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
        constraints=["CREATE CONSTRAINT domain_id_unique FOR (d:Domain) REQUIRE d.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT project_id_unique FOR (p:Project) REQUIRE p.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT component_id_unique FOR (c:Component) REQUIRE c.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT requirement_id_unique FOR (r:Requirement) REQUIRE r.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT implementation_id_unique FOR (i:Implementation) REQUIRE i.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT pattern_id_unique FOR (p:Pattern) REQUIRE p.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT decision_id_unique FOR (d:Decision) REQUIRE d.id IS UNIQUE"]
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
        constraints=["CREATE CONSTRAINT agent_id_unique FOR (a:Agent) REQUIRE a.id IS UNIQUE"]
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

# Add Digital Genome Architecture node schemas
GENOMIC_NODE_SCHEMAS = {
    NodeLabel.MEMORY: NodeSchema(
        label=NodeLabel.MEMORY,
        description="Stored memories in the associative memory system",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="content", data_type="string", required=True),
            SchemaProperty(name="context", data_type="string", required=True),
            SchemaProperty(name="memory_type", data_type="string", required=True),
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
            SchemaProperty(name="importance", data_type="float", required=True),
            SchemaProperty(name="last_accessed", data_type="datetime", required=True),
            SchemaProperty(name="access_count", data_type="integer", required=True),
            SchemaProperty(name="associations", data_type="string", required=False),
        ],
        constraints=["CREATE CONSTRAINT memory_id_unique FOR (m:Memory) REQUIRE m.id IS UNIQUE"]
    ),
    NodeLabel.EVENT: NodeSchema(
        label=NodeLabel.EVENT,
        description="System events with temporal and associative properties",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
            SchemaProperty(name="metadata", data_type="string", required=False),
            SchemaProperty(name="context", data_type="string", required=False),
        ],
        constraints=["CREATE CONSTRAINT event_id_unique FOR (e:Event) REQUIRE e.id IS UNIQUE"]
    ),
    
    NodeLabel.EVENT_SEQUENCE: NodeSchema(
        label=NodeLabel.EVENT_SEQUENCE,
        description="Ordered sequence of related events",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="event_count", data_type="integer", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="metadata", data_type="string", required=False),
        ],
        constraints=["CREATE CONSTRAINT event_sequence_id_unique FOR (es:EventSequence) REQUIRE es.id IS UNIQUE"]
    ),
    
    NodeLabel.FUNCTIONAL_REQUIREMENT: NodeSchema(
        label=NodeLabel.FUNCTIONAL_REQUIREMENT,
        description="System capabilities that must be implemented",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="priority", data_type="string", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT functional_req_id_unique FOR (fr:FunctionalRequirement) REQUIRE fr.id IS UNIQUE"]
    ),
    
    NodeLabel.NON_FUNCTIONAL_REQUIREMENT: NodeSchema(
        label=NodeLabel.NON_FUNCTIONAL_REQUIREMENT,
        description="Quality attributes and constraints",
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
        constraints=["CREATE CONSTRAINT non_functional_req_id_unique FOR (nfr:NonFunctionalRequirement) REQUIRE nfr.id IS UNIQUE"]
    ),
    
    NodeLabel.POLICY: NodeSchema(
        label=NodeLabel.POLICY,
        description="Best practices and governance rules",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="domain", data_type="string", required=True),
            SchemaProperty(name="enforcement", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT policy_id_unique FOR (p:Policy) REQUIRE p.id IS UNIQUE"]
    ),
    
    NodeLabel.WORKFLOW: NodeSchema(
        label=NodeLabel.WORKFLOW,
        description="End-to-end process definitions",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT workflow_id_unique FOR (w:Workflow) REQUIRE w.id IS UNIQUE"]
    ),
    
    NodeLabel.WORKFLOW_STEP: NodeSchema(
        label=NodeLabel.WORKFLOW_STEP,
        description="Individual steps in a workflow",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="order", data_type="integer", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT workflow_step_id_unique FOR (ws:WorkflowStep) REQUIRE ws.id IS UNIQUE"]
    ),
    
    NodeLabel.RED_FLAG: NodeSchema(
        label=NodeLabel.RED_FLAG,
        description="System anomalies and issues requiring attention",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=True),
            SchemaProperty(name="severity", data_type="string", required=True),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
            SchemaProperty(name="resolved_at", data_type="datetime", required=False),
        ],
        constraints=["CREATE CONSTRAINT red_flag_id_unique FOR (rf:RedFlag) REQUIRE rf.id IS UNIQUE"]
    ),
    
    NodeLabel.GENOMIC_AGENT: NodeSchema(
        label=NodeLabel.GENOMIC_AGENT,
        description="Self-regulating agent with enhanced cognitive capabilities",
        properties=[
            SchemaProperty(name="id", data_type="string", required=True),
            SchemaProperty(name="name", data_type="string", required=True),
            SchemaProperty(name="type", data_type="string", required=True),
            SchemaProperty(name="layer", data_type="string", required=True),
            SchemaProperty(name="description", data_type="string", required=False),
            SchemaProperty(name="status", data_type="string", required=True),
            SchemaProperty(name="policies", data_type="string", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=True),
        ],
        constraints=["CREATE CONSTRAINT genomic_agent_id_unique FOR (ga:GenomicAgent) REQUIRE ga.id IS UNIQUE"]
    ),
}

# Add Digital Genome Architecture relationship schemas
GENOMIC_RELATIONSHIP_SCHEMAS = {
    RelationshipType.ASSOCIATED_WITH: RelationshipSchema(
        type=RelationshipType.ASSOCIATED_WITH,
        description="Links memories that are associated with each other",
        source_labels=[
            NodeLabel.MEMORY.value
        ],
        target_labels=[
            NodeLabel.MEMORY.value
        ],
        properties=[
            SchemaProperty(name="strength", data_type="float", required=True),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
            SchemaProperty(name="updated_at", data_type="datetime", required=False),
        ]
    ),
    RelationshipType.TRIGGERS: RelationshipSchema(
        type=RelationshipType.TRIGGERS,
        description="Shows how events trigger other events or actions",
        source_labels=[
            NodeLabel.EVENT.value,
            NodeLabel.RED_FLAG.value
        ],
        target_labels=[
            NodeLabel.EVENT.value,
            NodeLabel.WORKFLOW.value,
            NodeLabel.WORKFLOW_STEP.value
        ],
        properties=[
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
            SchemaProperty(name="context", data_type="string", required=False),
        ]
    ),
    
    RelationshipType.GOVERNED_BY: RelationshipSchema(
        type=RelationshipType.GOVERNED_BY,
        description="Links entities to their governing policies",
        source_labels=[
            NodeLabel.GENOMIC_AGENT.value,
            NodeLabel.WORKFLOW.value,
            NodeLabel.FUNCTIONAL_REQUIREMENT.value,
            NodeLabel.NON_FUNCTIONAL_REQUIREMENT.value
        ],
        target_labels=[
            NodeLabel.POLICY.value
        ],
        properties=[
            SchemaProperty(name="compliance_level", data_type="float", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.NEXT_STEP: RelationshipSchema(
        type=RelationshipType.NEXT_STEP,
        description="Defines sequence of workflow steps",
        source_labels=[
            NodeLabel.WORKFLOW_STEP.value
        ],
        target_labels=[
            NodeLabel.WORKFLOW_STEP.value
        ],
        properties=[
            SchemaProperty(name="condition", data_type="string", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.DETECTED_BY: RelationshipSchema(
        type=RelationshipType.DETECTED_BY,
        description="Links red flags to detecting agent or mechanism",
        source_labels=[
            NodeLabel.RED_FLAG.value
        ],
        target_labels=[
            NodeLabel.GENOMIC_AGENT.value,
            NodeLabel.COMPONENT.value
        ],
        properties=[
            SchemaProperty(name="detection_method", data_type="string", required=False),
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.CONTAINS: RelationshipSchema(
        type=RelationshipType.CONTAINS,
        description="Shows containment relationships",
        source_labels=[
            NodeLabel.EVENT_SEQUENCE.value,
            NodeLabel.WORKFLOW.value
        ],
        target_labels=[
            NodeLabel.EVENT.value,
            NodeLabel.WORKFLOW_STEP.value
        ],
        properties=[
            SchemaProperty(name="order", data_type="integer", required=False),
            SchemaProperty(name="created_at", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.CREATED_BY: RelationshipSchema(
        type=RelationshipType.CREATED_BY,
        description="Links events to their originating agent",
        source_labels=[
            NodeLabel.EVENT.value
        ],
        target_labels=[
            NodeLabel.GENOMIC_AGENT.value,
            NodeLabel.AGENT.value
        ],
        properties=[
            SchemaProperty(name="context", data_type="string", required=False),
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
        ]
    ),
    
    RelationshipType.SYNCHRONIZED_WITH: RelationshipSchema(
        type=RelationshipType.SYNCHRONIZED_WITH,
        description="Links individual knowledge graphs with shared knowledge fabric",
        source_labels=[
            NodeLabel.GENOMIC_AGENT.value
        ],
        target_labels=[
            NodeLabel.DOMAIN.value
        ],
        properties=[
            SchemaProperty(name="last_sync", data_type="datetime", required=True),
            SchemaProperty(name="sync_status", data_type="string", required=True),
        ]
    ),
    
    RelationshipType.RESPONDS_TO: RelationshipSchema(
        type=RelationshipType.RESPONDS_TO,
        description="Links agents to events they respond to",
        source_labels=[
            NodeLabel.GENOMIC_AGENT.value,
            NodeLabel.AGENT.value
        ],
        target_labels=[
            NodeLabel.EVENT.value,
            NodeLabel.RED_FLAG.value
        ],
        properties=[
            SchemaProperty(name="response_type", data_type="string", required=False),
            SchemaProperty(name="timestamp", data_type="datetime", required=True),
        ]
    ),
}

# Merge original schemas with genomic schemas
ALL_NODE_SCHEMAS = {**CORE_NODE_SCHEMAS, **GENOMIC_NODE_SCHEMAS}
ALL_RELATIONSHIP_SCHEMAS = {**CORE_RELATIONSHIP_SCHEMAS, **GENOMIC_RELATIONSHIP_SCHEMAS}

# Create the core schema
CORE_SCHEMA = KnowledgeGraphSchema(
    nodes=ALL_NODE_SCHEMAS,
    relationships=ALL_RELATIONSHIP_SCHEMAS,
    description="Extended schema for the Development Crew Digital Genome Architecture"
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
                        # Update old constraint syntax if needed
                        if "ASSERT" in constraint_query:
                            # Extract label and property from old syntax
                            import re
                            match = re.search(r'ON \(([a-z]):([A-Za-z]+)\) ASSERT \1\.([a-z_]+) IS UNIQUE', constraint_query)
                            if match:
                                var, label, prop = match.groups()
                                # Form new constraint name
                                constraint_name = f"{label.lower()}_{prop}_unique"
                                # Create new constraint syntax
                                constraint_query = f"CREATE CONSTRAINT {constraint_name} FOR ({var}:{label}) REQUIRE {var}.{prop} IS UNIQUE"
                        self.connection.query(constraint_query)
                        logger.info(f"Created constraint: {constraint_query}")
                    except Exception as e:
                        logger.error(f"Failed to create constraint: {e}")
        
        index_queries = [
            # Original indices
            "CREATE INDEX domain_name_idx IF NOT EXISTS FOR (d:Domain) ON (d.name)",
            "CREATE INDEX project_name_idx IF NOT EXISTS FOR (p:Project) ON (p.name)",
            "CREATE INDEX component_name_idx IF NOT EXISTS FOR (c:Component) ON (c.name)",
            "CREATE INDEX requirement_name_idx IF NOT EXISTS FOR (r:Requirement) ON (r.name)",
            "CREATE INDEX pattern_name_idx IF NOT EXISTS FOR (p:Pattern) ON (p.name)",
            "CREATE INDEX agent_info_idx IF NOT EXISTS FOR (a:Agent) ON (a.name, a.type)",
            
            # Digital Genome Architecture indices
            "CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.type)",
            "CREATE INDEX event_timestamp_idx IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
            "CREATE INDEX workflow_status_idx IF NOT EXISTS FOR (w:Workflow) ON (w.status)",
            "CREATE INDEX red_flag_severity_idx IF NOT EXISTS FOR (rf:RedFlag) ON (rf.severity, rf.status)",
            "CREATE INDEX policy_domain_idx IF NOT EXISTS FOR (p:Policy) ON (p.domain)",
            "CREATE INDEX genomic_agent_info_idx IF NOT EXISTS FOR (ga:GenomicAgent) ON (ga.name, ga.type, ga.layer)",
            "CREATE INDEX memory_type_idx IF NOT EXISTS FOR (m:Memory) ON (m.memory_type)",
            "CREATE INDEX memory_importance_idx IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
            "CREATE INDEX memory_timestamp_idx IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)",
        ]
        
        for query in index_queries:
            try:
                # Update old index syntax if needed
                if "CREATE INDEX ON" in query:
                    # Extract label and properties from old syntax
                    import re
                    match = re.search(r'CREATE INDEX ON :([A-Za-z]+)\(([a-z_, ]+)\)', query)
                    if match:
                        label, props = match.groups()
                        # Form new index name
                        index_name = f"{label.lower()}_{props.replace(', ', '_')}_idx"
                        # Create new index syntax
                        var = label[0].lower()
                        query = f"CREATE INDEX {index_name} IF NOT EXISTS FOR ({var}:{label}) ON ({var}.{props.replace(', ', f', {var}.')})"
            
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
            constraint_query = f"CREATE CONSTRAINT {compound_label.lower()}_id_unique FOR (n:{compound_label}) REQUIRE n.id IS UNIQUE"
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
                elif prop_schema.data_type == "datetime" and not isinstance(value, (datetime, str)):
                    # Allow string representations of datetime
                    if isinstance(value, str):
                        try:
                            # Try to parse the string as datetime
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            errors.append(f"Property {name} should be a valid datetime string")
        
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
        "CREATE INDEX domain_name_idx FOR (d:Domain) ON (d.name);",
        "CREATE INDEX project_name_idx FOR (p:Project) ON (p.name);",
        "CREATE INDEX component_name_idx FOR (c:Component) ON (c.name);",
        "CREATE INDEX requirement_name_idx FOR (r:Requirement) ON (r.name);",
        "CREATE INDEX pattern_name_idx FOR (p:Pattern) ON (p.name);",
        "CREATE INDEX agent_info_idx FOR (a:Agent) ON (a.name, a.type);"
    ]
    script_lines.extend(index_queries)
    
    return "\n".join(script_lines)