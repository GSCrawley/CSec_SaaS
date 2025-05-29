"""
Dual Knowledge Manager for the Digital Genome Architecture.

This module implements the dual-layer knowledge graph structure that allows agents
to maintain both individual knowledge graphs for domain-specific expertise and
synchronize with a shared knowledge fabric for team-wide context.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Union, Tuple

from .schema import NodeLabel, RelationshipType
from .connection import Neo4jConnection

logger = logging.getLogger(__name__)

class DualKnowledgeManager:
    """
    Manages the dual knowledge architecture with individual and shared knowledge graphs.
    
    The DualKnowledgeManager is responsible for:
    1. Knowledge Graph Management: Creating, updating, and deleting knowledge graphs
    2. Synchronization: Implementing the rules for knowledge transfer between graphs
    3. Schema Translation: Applying mappings to translate between different knowledge representations
    4. Policy Enforcement: Ensuring that knowledge sharing and access adhere to defined policies
    """
    
    def __init__(self, connection: Neo4jConnection, agent_id: Optional[str] = None):
        """
        Initialize the dual knowledge manager.
        
        Args:
            connection: Connection to the Neo4j database
            agent_id: Optional unique identifier for the agent
        """
        self.connection = connection
        self.agent_id = agent_id
        
        # Verify that the blueprint knowledge graph exists
        self._verify_blueprint_exists()
        
    def _verify_blueprint_exists(self) -> None:
        """
        Verify that the blueprint knowledge graph exists in the database.
        If not, create the basic blueprint structure.
        """
        # Check if Global_Knowledge_Fabric exists
        query = """
        MATCH (kg:DKM_ManagedKG {name: "Global_Knowledge_Fabric"}) 
        RETURN kg
        """
        result = self.connection.query(query)
        
        if not result:
            logger.info("Blueprint knowledge graph not found. Creating basic blueprint structure.")
            self._create_blueprint_structure()
        else:
            logger.info("Blueprint knowledge graph found.")
    
    def _create_blueprint_structure(self) -> None:
        """
        Create the basic blueprint structure for the Dual Knowledge Manager.
        This includes the Global_Knowledge_Fabric and basic synchronization rules.
        """
        # Create Global Knowledge Fabric
        self.create_knowledge_graph(
            "Global_Knowledge_Fabric", 
            "Global", 
            "The central, shared knowledge graph for the Development Crew."
        )
        
        # Create an example Local Knowledge Graph
        self.create_knowledge_graph(
            "Local_Agent_KG_Example", 
            "Local", 
            "An example local knowledge graph for an individual agent."
        )
        
        # Create Synchronization Rules
        self.create_sync_rule(
            "Bidirectional_Sync", 
            "Bidirectional", 
            "Synchronizes entities in both directions between local and global KGs."
        )
        
        self.create_sync_rule(
            "LocalToGlobal_Sync", 
            "Unidirectional", 
            "Pushes selected entities from local KGs to the global fabric."
        )
        
        self.create_sync_rule(
            "GlobalToLocal_Sync", 
            "Unidirectional", 
            "Pulls selected entities from the global fabric to local KGs."
        )
        
        # Create Schema Mappings
        self.create_schema_mapping(
            "Entity_Mapping", 
            "Entity", 
            "Maps entity structures between local and global schemas."
        )
        
        self.create_schema_mapping(
            "Relation_Mapping", 
            "Relation", 
            "Maps relationship structures between local and global schemas."
        )
        
        # Create Knowledge Policies
        self.create_knowledge_policy(
            "Sharing_Policy", 
            "Sharing", 
            "Defines what knowledge can be shared between KGs and under what conditions."
        )
        
        self.create_knowledge_policy(
            "Access_Policy", 
            "Access", 
            "Defines which agents can access what knowledge and with what permissions."
        )
        
        # Create relationships between nodes
        self._create_blueprint_relationships()
        
        logger.info("Created basic blueprint structure for Dual Knowledge Manager.")
    
    def _create_blueprint_relationships(self) -> None:
        """
        Create the relationships between blueprint nodes.
        """
        # Connect Global KG to Local KG with SynchronizationRules
        query = """
        MATCH (gkf:DKM_ManagedKG {name: "Global_Knowledge_Fabric"})
        MATCH (lakg:DKM_ManagedKG {name: "Local_Agent_KG_Example"})
        MATCH (bidirectional:DKM_SynchronizationRule {name: "Bidirectional_Sync"})
        MATCH (localToGlobal:DKM_SynchronizationRule {name: "LocalToGlobal_Sync"})
        MATCH (globalToLocal:DKM_SynchronizationRule {name: "GlobalToLocal_Sync"})

        MERGE (lakg)-[:SYNCS_WITH {rule: "bidirectional"}]->(gkf)
        MERGE (lakg)-[:SYNCS_TO {rule: "push"}]->(gkf)
        MERGE (gkf)-[:SYNCS_TO {rule: "pull"}]->(lakg)

        MERGE (bidirectional)-[:APPLIES_TO]->(lakg)
        MERGE (bidirectional)-[:APPLIES_TO]->(gkf)
        MERGE (localToGlobal)-[:APPLIES_TO]->(lakg)
        MERGE (globalToLocal)-[:APPLIES_TO]->(gkf)
        """
        self.connection.query(query)
        
        # Connect Schema Mappings to KGs
        query = """
        MATCH (gkf:DKM_ManagedKG {name: "Global_Knowledge_Fabric"})
        MATCH (lakg:DKM_ManagedKG {name: "Local_Agent_KG_Example"})
        MATCH (entityMapping:DKM_SchemaMapping {name: "Entity_Mapping"})
        MATCH (relationMapping:DKM_SchemaMapping {name: "Relation_Mapping"})

        MERGE (entityMapping)-[:MAPS_BETWEEN]->(gkf)
        MERGE (entityMapping)-[:MAPS_BETWEEN]->(lakg)
        MERGE (relationMapping)-[:MAPS_BETWEEN]->(gkf)
        MERGE (relationMapping)-[:MAPS_BETWEEN]->(lakg)
        """
        self.connection.query(query)
        
        # Connect Knowledge Policies
        query = """
        MATCH (gkf:DKM_ManagedKG {name: "Global_Knowledge_Fabric"})
        MATCH (lakg:DKM_ManagedKG {name: "Local_Agent_KG_Example"})
        MATCH (sharingPolicy:DKM_KnowledgePolicy {name: "Sharing_Policy"})
        MATCH (accessPolicy:DKM_KnowledgePolicy {name: "Access_Policy"})

        MERGE (sharingPolicy)-[:GOVERNS]->(gkf)
        MERGE (sharingPolicy)-[:GOVERNS]->(lakg)
        MERGE (accessPolicy)-[:GOVERNS]->(gkf)
        MERGE (accessPolicy)-[:GOVERNS]->(lakg)
        """
        self.connection.query(query)
    
    def create_knowledge_graph(self, name: str, kg_type: str, description: str) -> Dict[str, Any]:
        """
        Create a new managed knowledge graph.
        
        Args:
            name: Name of the knowledge graph
            kg_type: Type of knowledge graph (Global or Local)
            description: Description of the knowledge graph
            
        Returns:
            Dict: Created knowledge graph node properties
        """
        # Generate a unique ID if not provided
        node_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        
        query = """
        MERGE (kg:DKM_ManagedKG {name: $name}) 
        ON CREATE SET 
            kg.id = $id,
            kg.type = $type,
            kg.description = $description,
            kg.created_at = $timestamp
        RETURN kg
        """
        
        params = {
            "name": name,
            "id": node_id,
            "type": kg_type,
            "description": description,
            "timestamp": timestamp
        }
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Created knowledge graph: {name} ({kg_type})")
            return result[0]["kg"]
        else:
            logger.error(f"Failed to create knowledge graph: {name}")
            return {}
    
    def get_knowledge_graph(self, name: str) -> Dict[str, Any]:
        """
        Get a managed knowledge graph by name.
        
        Args:
            name: Name of the knowledge graph
            
        Returns:
            Dict: Knowledge graph node properties or empty dict if not found
        """
        query = """
        MATCH (kg:DKM_ManagedKG {name: $name}) 
        RETURN kg
        """
        
        params = {"name": name}
        result = self.connection.query(query, params)
        
        if result:
            return result[0]["kg"]
        else:
            logger.warning(f"Knowledge graph not found: {name}")
            return {}
    
    def update_knowledge_graph(self, name: str, properties: Dict[str, Any]) -> bool:
        """
        Update a managed knowledge graph.
        
        Args:
            name: Name of the knowledge graph
            properties: Properties to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Build the SET clause for each property
        set_clauses = [f"kg.{key} = ${key}" for key in properties.keys()]
        set_statement = ", ".join(set_clauses)
        
        query = f"""
        MATCH (kg:DKM_ManagedKG {{name: $name}}) 
        SET {set_statement}
        RETURN kg
        """
        
        # Add name to parameters
        params = {**properties, "name": name}
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Updated knowledge graph: {name}")
            return True
        else:
            logger.error(f"Failed to update knowledge graph: {name}")
            return False
    
    def delete_knowledge_graph(self, name: str) -> bool:
        """
        Delete a managed knowledge graph.
        
        Args:
            name: Name of the knowledge graph
            
        Returns:
            bool: True if successful, False otherwise
        """
        # First, delete all relationships involving this knowledge graph
        query = """
        MATCH (kg:DKM_ManagedKG {name: $name})-[r]-() 
        DELETE r
        """
        
        params = {"name": name}
        self.connection.query(query, params)
        
        # Then delete the node itself
        query = """
        MATCH (kg:DKM_ManagedKG {name: $name}) 
        DELETE kg
        """
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Deleted knowledge graph: {name}")
            return True
        else:
            logger.error(f"Failed to delete knowledge graph: {name}")
            return False
    
    # Synchronization Rule Methods
    
    def create_sync_rule(self, name: str, rule_type: str, description: str) -> Dict[str, Any]:
        """
        Create a new synchronization rule.
        
        Args:
            name: Name of the synchronization rule
            rule_type: Type of rule (Bidirectional or Unidirectional)
            description: Description of the rule
            
        Returns:
            Dict: Created synchronization rule node properties
        """
        # Generate a unique ID if not provided
        node_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        
        query = """
        MERGE (rule:DKM_SynchronizationRule {name: $name}) 
        ON CREATE SET 
            rule.id = $id,
            rule.type = $type,
            rule.description = $description,
            rule.created_at = $timestamp
        RETURN rule
        """
        
        params = {
            "name": name,
            "id": node_id,
            "type": rule_type,
            "description": description,
            "timestamp": timestamp
        }
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Created synchronization rule: {name} ({rule_type})")
            return result[0]["rule"]
        else:
            logger.error(f"Failed to create synchronization rule: {name}")
            return {}
    
    def get_sync_rule(self, name: str) -> Dict[str, Any]:
        """
        Get a synchronization rule by name.
        
        Args:
            name: Name of the synchronization rule
            
        Returns:
            Dict: Synchronization rule node properties or empty dict if not found
        """
        query = """
        MATCH (rule:DKM_SynchronizationRule {name: $name}) 
        RETURN rule
        """
        
        params = {"name": name}
        result = self.connection.query(query, params)
        
        if result:
            return result[0]["rule"]
        else:
            logger.warning(f"Synchronization rule not found: {name}")
            return {}
    
    def apply_sync_rule(self, rule_name: str, source_kg: str, target_kg: str) -> bool:
        """
        Apply a synchronization rule between two knowledge graphs.
        
        Args:
            rule_name: Name of the synchronization rule to apply
            source_kg: Name of the source knowledge graph
            target_kg: Name of the target knowledge graph
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get the rule type
        rule = self.get_sync_rule(rule_name)
        if not rule:
            logger.error(f"Synchronization rule not found: {rule_name}")
            return False
            
        rule_type = rule.get("type")
        
        # Create appropriate relationships based on rule type
        if rule_type == "Bidirectional":
            # Create bidirectional sync relationship
            query = """
            MATCH (source:DKM_ManagedKG {name: $source_kg})
            MATCH (target:DKM_ManagedKG {name: $target_kg})
            MATCH (rule:DKM_SynchronizationRule {name: $rule_name})
            
            MERGE (source)-[:SYNCS_WITH {rule: "bidirectional"}]->(target)
            MERGE (rule)-[:APPLIES_TO]->(source)
            MERGE (rule)-[:APPLIES_TO]->(target)
            
            RETURN source, target, rule
            """
        else:  # Unidirectional
            # Create unidirectional sync relationship
            query = """
            MATCH (source:DKM_ManagedKG {name: $source_kg})
            MATCH (target:DKM_ManagedKG {name: $target_kg})
            MATCH (rule:DKM_SynchronizationRule {name: $rule_name})
            
            MERGE (source)-[:SYNCS_TO {rule: "push"}]->(target)
            MERGE (rule)-[:APPLIES_TO]->(source)
            
            RETURN source, target, rule
            """
            
        params = {
            "source_kg": source_kg,
            "target_kg": target_kg,
            "rule_name": rule_name
        }
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Applied synchronization rule {rule_name} from {source_kg} to {target_kg}")
            return True
        else:
            logger.error(f"Failed to apply synchronization rule {rule_name}")
            return False
    
    def synchronize(self, source_kg: str, target_kg: str, sync_rule: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronize knowledge between two knowledge graphs.
        
        Args:
            source_kg: Name of the source knowledge graph
            target_kg: Name of the target knowledge graph
            sync_rule: Optional name of the synchronization rule to use
                       If not provided, will use any applicable rule
                       
        Returns:
            Dict: Summary of synchronized nodes and relationships
        """
        # Initialize sync summary
        sync_summary = {
            "nodes_synced": 0,
            "relationships_synced": 0,
            "conflicts_resolved": 0,
            "errors": 0
        }
        
        # Find applicable synchronization rule if not specified
        if not sync_rule:
            query = """
            MATCH (source:DKM_ManagedKG {name: $source_kg})
            MATCH (target:DKM_ManagedKG {name: $target_kg})
            MATCH (source)-[r:SYNCS_WITH|SYNCS_TO]->(target)
            MATCH (rule:DKM_SynchronizationRule)-[:APPLIES_TO]->(source)
            RETURN rule.name as rule_name, r.rule as direction
            LIMIT 1
            """
            
            params = {
                "source_kg": source_kg,
                "target_kg": target_kg
            }
            
            result = self.connection.query(query, params)
            
            if result:
                sync_rule = result[0]["rule_name"]
                direction = result[0]["direction"]
                logger.info(f"Found applicable sync rule: {sync_rule} ({direction})")
            else:
                logger.error(f"No applicable synchronization rule found between {source_kg} and {target_kg}")
                sync_summary["errors"] += 1
                return sync_summary
        
        # Get nodes from source knowledge graph
        query = """
        MATCH (kg:DKM_ManagedKG {name: $source_kg})
        MATCH (n)
        WHERE NOT n:DKM_ManagedKG AND NOT n:DKM_SynchronizationRule 
              AND NOT n:DKM_SchemaMapping AND NOT n:DKM_KnowledgePolicy
        RETURN n
        """
        
        params = {"source_kg": source_kg}
        source_nodes = self.connection.query(query, params)
        
        # Process each node for synchronization
        for node_record in source_nodes:
            node = node_record["n"]
            
            # Apply schema mapping if needed
            mapped_node = self.apply_schema_mapping(node, source_kg, target_kg)
            
            # Check policy compliance
            if not self.check_policy_compliance(mapped_node, "Sharing"):
                logger.warning(f"Node {node.get('id')} does not comply with sharing policy. Skipping.")
                continue
                
            # Create or update node in target knowledge graph
            self._sync_node(mapped_node, target_kg)
            sync_summary["nodes_synced"] += 1
            
            # Sync relationships for this node
            rel_count = self._sync_node_relationships(node, mapped_node, target_kg)
            sync_summary["relationships_synced"] += rel_count
        
        logger.info(f"Synchronized {sync_summary['nodes_synced']} nodes and {sync_summary['relationships_synced']} relationships")
        return sync_summary
        
    def _sync_node(self, node: Dict[str, Any], target_kg: str) -> bool:
        """
        Synchronize a node to the target knowledge graph.
        
        Args:
            node: Node to synchronize
            target_kg: Name of the target knowledge graph
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if node already exists in target
        node_id = node.get("id")
        if not node_id:
            logger.error("Cannot sync node without id")
            return False
            
        query = """
        MATCH (n {id: $node_id}) 
        RETURN n
        """
        
        params = {"node_id": node_id}
        result = self.connection.query(query, params)
        
        if result:
            # Update existing node
            existing_node = result[0]["n"]
            
            # Build properties to update
            update_props = {}
            for key, value in node.items():
                if key != "id":  # Don't update id
                    update_props[key] = value
                    
            # Add sync metadata
            update_props["last_synced"] = datetime.now().timestamp()
            update_props["sync_source"] = target_kg
            
            # Build the SET clause
            set_clauses = [f"n.{key} = ${key}" for key in update_props.keys()]
            set_statement = ", ".join(set_clauses)
            
            query = f"""
            MATCH (n {{id: $node_id}}) 
            SET {set_statement}
            RETURN n
            """
            
            # Add node_id to parameters
            params = {**update_props, "node_id": node_id}
            
            self.connection.query(query, params)
            logger.debug(f"Updated node {node_id} in target knowledge graph")
            
        else:
            # Create new node
            # Get node labels
            labels = node.get("labels", [])
            if not labels:
                logger.error(f"Cannot create node {node_id} without labels")
                return False
                
            # Build label string
            label_string = ":".join(labels)
            
            # Build properties
            props = {key: value for key, value in node.items() if key != "labels"}
            
            # Add sync metadata
            props["last_synced"] = datetime.now().timestamp()
            props["sync_source"] = target_kg
            
            query = f"""
            CREATE (n:{label_string} $props)
            RETURN n
            """
            
            params = {"props": props}
            
            self.connection.query(query, params)
            logger.debug(f"Created node {node_id} in target knowledge graph")
            
        return True
        
    def _sync_node_relationships(self, source_node: Dict[str, Any], target_node: Dict[str, Any], target_kg: str) -> int:
        """
        Synchronize relationships for a node to the target knowledge graph.
        
        Args:
            source_node: Source node
            target_node: Target node (may have different properties due to schema mapping)
            target_kg: Name of the target knowledge graph
            
        Returns:
            int: Number of relationships synchronized
        """
        # Get relationships for the source node
        node_id = source_node.get("id")
        if not node_id:
            logger.error("Cannot sync relationships for node without id")
            return 0
            
        query = """
        MATCH (n {id: $node_id})-[r]->(m)
        RETURN type(r) as rel_type, properties(r) as props, m.id as target_id
        """
        
        params = {"node_id": node_id}
        relationships = self.connection.query(query, params)
        
        rel_count = 0
        for rel in relationships:
            rel_type = rel["rel_type"]
            props = rel["props"]
            target_id = rel["target_id"]
            
            # Skip if target node doesn't exist in target knowledge graph
            query = """
            MATCH (m {id: $target_id}) 
            RETURN m
            """
            
            params = {"target_id": target_id}
            target_exists = self.connection.query(query, params)
            
            if not target_exists:
                logger.warning(f"Target node {target_id} not found in target knowledge graph. Skipping relationship.")
                continue
                
            # Create relationship in target knowledge graph
            query = f"""
            MATCH (n {{id: $source_id}})
            MATCH (m {{id: $target_id}})
            MERGE (n)-[r:{rel_type}]->(m)
            ON CREATE SET r = $props
            RETURN r
            """
            
            params = {
                "source_id": node_id,
                "target_id": target_id,
                "props": props
            }
            
            self.connection.query(query, params)
            rel_count += 1
            
        return rel_count
    
    # Schema Mapping Methods
    
    def create_schema_mapping(self, name: str, mapping_type: str, description: str, mapping_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new schema mapping.
        
        Args:
            name: Name of the schema mapping
            mapping_type: Type of mapping (Entity or Relation)
            description: Description of the mapping
            mapping_rules: Optional dictionary of mapping rules
            
        Returns:
            Dict: Created schema mapping node properties
        """
        # Generate a unique ID if not provided
        node_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        
        # Convert mapping rules to JSON string if provided
        mapping_rules_json = None
        if mapping_rules:
            mapping_rules_json = json.dumps(mapping_rules)
        
        query = """
        MERGE (mapping:DKM_SchemaMapping {name: $name}) 
        ON CREATE SET 
            mapping.id = $id,
            mapping.type = $type,
            mapping.description = $description,
            mapping.created_at = $timestamp
        """
        
        # Add mapping rules if provided
        if mapping_rules_json:
            query += ", mapping.rules = $rules"
            
        query += " RETURN mapping"
        
        params = {
            "name": name,
            "id": node_id,
            "type": mapping_type,
            "description": description,
            "timestamp": timestamp
        }
        
        if mapping_rules_json:
            params["rules"] = mapping_rules_json
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Created schema mapping: {name} ({mapping_type})")
            return result[0]["mapping"]
        else:
            logger.error(f"Failed to create schema mapping: {name}")
            return {}
    
    def get_schema_mapping(self, name: str) -> Dict[str, Any]:
        """
        Get a schema mapping by name.
        
        Args:
            name: Name of the schema mapping
            
        Returns:
            Dict: Schema mapping node properties or empty dict if not found
        """
        query = """
        MATCH (mapping:DKM_SchemaMapping {name: $name}) 
        RETURN mapping
        """
        
        params = {"name": name}
        result = self.connection.query(query, params)
        
        if result:
            mapping = result[0]["mapping"]
            
            # Parse mapping rules if present
            if "rules" in mapping and mapping["rules"]:
                try:
                    mapping["rules"] = json.loads(mapping["rules"])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse mapping rules for {name}")
                    
            return mapping
        else:
            logger.warning(f"Schema mapping not found: {name}")
            return {}
    
    def apply_schema_mapping(self, entity: Dict[str, Any], source_kg: str, target_kg: str) -> Dict[str, Any]:
        """
        Apply a schema mapping to translate an entity between schemas.
        
        Args:
            entity: Entity to translate
            source_kg: Name of the source knowledge graph
            target_kg: Name of the target knowledge graph
            
        Returns:
            Dict: Translated entity
        """
        # Find applicable schema mappings
        query = """
        MATCH (source:DKM_ManagedKG {name: $source_kg})
        MATCH (target:DKM_ManagedKG {name: $target_kg})
        MATCH (mapping:DKM_SchemaMapping)-[:MAPS_BETWEEN]->(source)
        MATCH (mapping)-[:MAPS_BETWEEN]->(target)
        RETURN mapping
        """
        
        params = {
            "source_kg": source_kg,
            "target_kg": target_kg
        }
        
        mappings = self.connection.query(query, params)
        
        if not mappings:
            logger.warning(f"No schema mappings found between {source_kg} and {target_kg}. Using entity as is.")
            return entity
        
        # Make a copy of the entity to avoid modifying the original
        translated_entity = dict(entity)
        
        # Apply each applicable mapping
        for mapping_record in mappings:
            mapping = mapping_record["mapping"]
            
            # Get mapping rules
            rules = {}
            if "rules" in mapping and mapping["rules"]:
                try:
                    rules = json.loads(mapping["rules"]) if isinstance(mapping["rules"], str) else mapping["rules"]
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse mapping rules for {mapping.get('name')}")
                    continue
            
            # If no explicit rules, use identity mapping (no changes)
            if not rules:
                continue
                
            # Apply property mappings
            if "properties" in rules:
                for source_prop, target_prop in rules["properties"].items():
                    if source_prop in entity:
                        translated_entity[target_prop] = entity[source_prop]
                        
                        # Remove source property if different from target
                        if source_prop != target_prop:
                            translated_entity.pop(source_prop, None)
            
            # Apply label mappings
            if "labels" in rules and "labels" in entity:
                new_labels = []
                for label in entity["labels"]:
                    if label in rules["labels"]:
                        new_labels.append(rules["labels"][label])
                    else:
                        new_labels.append(label)
                        
                translated_entity["labels"] = new_labels
                
            # Apply value transformations
            if "transformations" in rules:
                for prop, transform in rules["transformations"].items():
                    if prop in translated_entity:
                        value = translated_entity[prop]
                        
                        # Apply transformation based on type
                        if transform["type"] == "prefix" and "value" in transform:
                            translated_entity[prop] = f"{transform['value']}{value}"
                        elif transform["type"] == "suffix" and "value" in transform:
                            translated_entity[prop] = f"{value}{transform['value']}"
                        elif transform["type"] == "replace" and "from" in transform and "to" in transform:
                            if isinstance(value, str):
                                translated_entity[prop] = value.replace(transform["from"], transform["to"])
        
        return translated_entity
    
    # Knowledge Policy Methods
    
    def create_knowledge_policy(self, name: str, policy_type: str, description: str, rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new knowledge policy.
        
        Args:
            name: Name of the knowledge policy
            policy_type: Type of policy (Sharing or Access)
            description: Description of the policy
            rules: Optional dictionary of policy rules
            
        Returns:
            Dict: Created knowledge policy node properties
        """
        # Generate a unique ID if not provided
        node_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        
        # Convert rules to JSON string if provided
        rules_json = None
        if rules:
            rules_json = json.dumps(rules)
        
        query = """
        MERGE (policy:DKM_KnowledgePolicy {name: $name}) 
        ON CREATE SET 
            policy.id = $id,
            policy.type = $type,
            policy.description = $description,
            policy.created_at = $timestamp
        """
        
        # Add rules if provided
        if rules_json:
            query += ", policy.rules = $rules"
            
        query += " RETURN policy"
        
        params = {
            "name": name,
            "id": node_id,
            "type": policy_type,
            "description": description,
            "timestamp": timestamp
        }
        
        if rules_json:
            params["rules"] = rules_json
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Created knowledge policy: {name} ({policy_type})")
            return result[0]["policy"]
        else:
            logger.error(f"Failed to create knowledge policy: {name}")
            return {}
    
    def get_knowledge_policy(self, name: str) -> Dict[str, Any]:
        """
        Get a knowledge policy by name.
        
        Args:
            name: Name of the knowledge policy
            
        Returns:
            Dict: Knowledge policy node properties or empty dict if not found
        """
        query = """
        MATCH (policy:DKM_KnowledgePolicy {name: $name}) 
        RETURN policy
        """
        
        params = {"name": name}
        result = self.connection.query(query, params)
        
        if result:
            policy = result[0]["policy"]
            
            # Parse rules if present
            if "rules" in policy and policy["rules"]:
                try:
                    policy["rules"] = json.loads(policy["rules"])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse policy rules for {name}")
                    
            return policy
        else:
            logger.warning(f"Knowledge policy not found: {name}")
            return {}
    
    def apply_policy(self, policy_name: str, kg_name: str) -> bool:
        """
        Apply a policy to a knowledge graph.
        
        Args:
            policy_name: Name of the knowledge policy to apply
            kg_name: Name of the knowledge graph
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        MATCH (policy:DKM_KnowledgePolicy {name: $policy_name})
        MATCH (kg:DKM_ManagedKG {name: $kg_name})
        MERGE (policy)-[:GOVERNS]->(kg)
        RETURN policy, kg
        """
        
        params = {
            "policy_name": policy_name,
            "kg_name": kg_name
        }
        
        result = self.connection.query(query, params)
        
        if result:
            logger.info(f"Applied policy {policy_name} to knowledge graph {kg_name}")
            return True
        else:
            logger.error(f"Failed to apply policy {policy_name} to knowledge graph {kg_name}")
            return False
    
    def check_policy_compliance(self, entity: Dict[str, Any], policy_type: str) -> bool:
        """
        Check if an entity complies with a specific policy type.
        
        Args:
            entity: Entity to check
            policy_type: Type of policy to check (Sharing or Access)
            
        Returns:
            bool: True if entity complies with policy, False otherwise
        """
        # For now, implement a simple policy check
        # In a real implementation, this would be more sophisticated
        
        # Default to allowing if no specific rules are defined
        if policy_type == "Sharing":
            # Check if entity has explicit sharing restrictions
            if "sharing_restricted" in entity and entity["sharing_restricted"] == True:
                logger.info(f"Entity {entity.get('id')} has sharing restrictions. Blocked by policy.")
                return False
                
            # Check for sensitive data flags
            if "sensitive" in entity and entity["sensitive"] == True:
                logger.info(f"Entity {entity.get('id')} contains sensitive data. Blocked by policy.")
                return False
                
        elif policy_type == "Access":
            # Check if entity has access restrictions
            if "access_restricted" in entity and entity["access_restricted"] == True:
                # If agent_id is specified, check if it's in the allowed list
                if self.agent_id and "allowed_agents" in entity and isinstance(entity["allowed_agents"], list):
                    if self.agent_id not in entity["allowed_agents"]:
                        logger.info(f"Agent {self.agent_id} does not have access to entity {entity.get('id')}")
                        return False
                else:
                    logger.info(f"Entity {entity.get('id')} has access restrictions. Blocked by policy.")
                    return False
        
        # If no restrictions found, entity complies with policy
        return True
    
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
