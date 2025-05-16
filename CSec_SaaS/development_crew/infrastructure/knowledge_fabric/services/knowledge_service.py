"""
Knowledge Fabric Service Module.

This module provides high-level services for agents to interact with the knowledge graph,
coordinating operations across multiple repositories and providing domain-specific functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ..core.connection import Neo4jConnection, get_connection_pool
from ..core.repository import (AgentModel, AgentRepository, ComponentModel,
                              ComponentRepository, DecisionModel,
                              DecisionRepository, DomainModel,
                              DomainRepository, ImplementationModel,
                              ImplementationRepository, PatternModel,
                              PatternRepository, ProjectModel,
                              ProjectRepository, RelationshipRepository,
                              RequirementModel, RequirementRepository)
from ..core.schema import NodeLabel, RelationshipType

logger = logging.getLogger(__name__)


class KnowledgeService:
    """High-level service for interacting with the knowledge graph."""
    
    def __init__(self, connection: Optional[Neo4jConnection] = None):
        """Initialize knowledge service.
        
        Args:
            connection: Optional Neo4j connection. If None, uses connection pool.
        """
        self.connection = connection or get_connection_pool().get_connection()
        
        # Initialize repositories
        self.domain_repo = DomainRepository(self.connection)
        self.project_repo = ProjectRepository(self.connection)
        self.component_repo = ComponentRepository(self.connection)
        self.requirement_repo = RequirementRepository(self.connection)
        self.implementation_repo = ImplementationRepository(self.connection)
        self.pattern_repo = PatternRepository(self.connection)
        self.decision_repo = DecisionRepository(self.connection)
        self.agent_repo = AgentRepository(self.connection)
        self.relationship_repo = RelationshipRepository(self.connection)
    
    def close(self):
        """Close the connection if it was created by this service."""
        if hasattr(self, 'connection') and self.connection:
            get_connection_pool().release_connection(self.connection)
            self.connection = None
    
    # Domain operations
    
    def create_domain(self, name: str, description: Optional[str] = None) -> DomainModel:
        """Create a new domain.
        
        Args:
            name: Domain name.
            description: Optional domain description.
            
        Returns:
            Created domain.
        """
        domain_data = {
            "name": name,
            "description": description or f"{name} domain"
        }
        return self.domain_repo.create(domain_data)
    
    def get_domain(self, domain_id: str) -> Optional[DomainModel]:
        """Get domain by ID.
        
        Args:
            domain_id: Domain ID.
            
        Returns:
            Domain or None if not found.
        """
        return self.domain_repo.find_by_id(domain_id)
    
    def get_domain_by_name(self, name: str) -> Optional[DomainModel]:
        """Get domain by name.
        
        Args:
            name: Domain name.
            
        Returns:
            Domain or None if not found.
        """
        domains = self.domain_repo.find_by_property("name", name)
        return domains[0] if domains else None
    
    # Project operations
    
    def create_project(
        self, 
        name: str, 
        domain_id: str, 
        description: Optional[str] = None
    ) -> ProjectModel:
        """Create a new project in a domain.
        
        Args:
            name: Project name.
            domain_id: Domain ID.
            description: Optional project description.
            
        Returns:
            Created project.
            
        Raises:
            ValueError: If domain not found.
        """
        # Verify domain exists
        domain = self.domain_repo.find_by_id(domain_id)
        if not domain:
            raise ValueError(f"Domain with ID {domain_id} not found")
        
        # Create project
        project_data = {
            "name": name,
            "description": description or f"{name} project",
            "status": "active"
        }
        project = self.project_repo.create(project_data)
        
        # Link project to domain
        self.relationship_repo.create_relationship(
            project.id,
            NodeLabel.PROJECT,
            domain_id,
            NodeLabel.DOMAIN,
            RelationshipType.BELONGS_TO
        )
        
        return project
    
    def get_project(self, project_id: str) -> Optional[ProjectModel]:
        """Get project by ID.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Project or None if not found.
        """
        return self.project_repo.find_by_id(project_id)
    
    def get_projects_by_domain(self, domain_id: str) -> List[ProjectModel]:
        """Get projects in a domain.
        
        Args:
            domain_id: Domain ID.
            
        Returns:
            List of projects.
        """
        return self.project_repo.find_projects_by_domain(domain_id)
    
    # Component operations
    
    def create_component(
        self, 
        name: str, 
        component_type: str, 
        project_id: str, 
        description: Optional[str] = None
    ) -> ComponentModel:
        """Create a new component in a project.
        
        Args:
            name: Component name.
            component_type: Component type.
            project_id: Project ID.
            description: Optional component description.
            
        Returns:
            Created component.
            
        Raises:
            ValueError: If project not found.
        """
        # Verify project exists
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Create component
        component_data = {
            "name": name,
            "description": description or f"{name} component",
            "type": component_type,
            "status": "planning"
        }
        component = self.component_repo.create(component_data)
        
        # Link component to project
        self.relationship_repo.create_relationship(
            component.id,
            NodeLabel.COMPONENT,
            project_id,
            NodeLabel.PROJECT,
            RelationshipType.BELONGS_TO
        )
        
        return component
    
    def get_component(self, component_id: str) -> Optional[ComponentModel]:
        """Get component by ID.
        
        Args:
            component_id: Component ID.
            
        Returns:
            Component or None if not found.
        """
        return self.component_repo.find_by_id(component_id)
    
    def get_components_by_project(self, project_id: str) -> List[ComponentModel]:
        """Get components in a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            List of components.
        """
        return self.component_repo.find_components_by_project(project_id)
    
    def add_component_dependency(
        self, 
        component_id: str, 
        dependency_id: str, 
        dependency_type: Optional[str] = None
    ) -> Dict:
        """Add a dependency between components.
        
        Args:
            component_id: ID of the dependent component.
            dependency_id: ID of the component being depended on.
            dependency_type: Optional type of dependency.
            
        Returns:
            Relationship information.
            
        Raises:
            ValueError: If either component not found.
        """
        # Verify components exist
        component = self.component_repo.find_by_id(component_id)
        dependency = self.component_repo.find_by_id(dependency_id)
        
        if not component:
            raise ValueError(f"Component with ID {component_id} not found")
        if not dependency:
            raise ValueError(f"Component with ID {dependency_id} not found")
        
        # Create dependency relationship
        properties = {"created_at": datetime.now()}
        if dependency_type:
            properties["dependency_type"] = dependency_type
        
        return self.relationship_repo.create_relationship(
            component_id,
            NodeLabel.COMPONENT,
            dependency_id,
            NodeLabel.COMPONENT,
            RelationshipType.DEPENDS_ON,
            properties
        )
    
    # Requirement operations
    
    def create_requirement(
        self,
        name: str,
        description: str,
        requirement_type: str,
        priority: str,
        project_id: str
    ) -> RequirementModel:
        """Create a new requirement in a project.
        
        Args:
            name: Requirement name.
            description: Requirement description.
            requirement_type: Requirement type.
            priority: Requirement priority.
            project_id: Project ID.
            
        Returns:
            Created requirement.
            
        Raises:
            ValueError: If project not found.
        """
        # Verify project exists
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Create requirement
        requirement_data = {
            "name": name,
            "description": description,
            "type": requirement_type,
            "priority": priority,
            "status": "defined"
        }
        requirement = self.requirement_repo.create(requirement_data)
        
        # Link requirement to project
        self.relationship_repo.create_relationship(
            requirement.id,
            NodeLabel.REQUIREMENT,
            project_id,
            NodeLabel.PROJECT,
            RelationshipType.BELONGS_TO
        )
        
        return requirement
    
    def get_requirement(self, requirement_id: str) -> Optional[RequirementModel]:
        """Get requirement by ID.
        
        Args:
            requirement_id: Requirement ID.
            
        Returns:
            Requirement or None if not found.
        """
        return self.requirement_repo.find_by_id(requirement_id)
    
    def get_requirements_by_project(self, project_id: str) -> List[RequirementModel]:
        """Get requirements in a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            List of requirements.
        """
        return self.requirement_repo.find_requirements_by_project(project_id)
    
    def link_component_to_requirement(
        self, 
        component_id: str, 
        requirement_id: str, 
        status: Optional[str] = "in_progress"
    ) -> Dict:
        """Link a component to a requirement it implements.
        
        Args:
            component_id: Component ID.
            requirement_id: Requirement ID.
            status: Implementation status.
            
        Returns:
            Relationship information.
            
        Raises:
            ValueError: If component or requirement not found.
        """
        # Verify entities exist
        component = self.component_repo.find_by_id(component_id)
        requirement = self.requirement_repo.find_by_id(requirement_id)
        
        if not component:
            raise ValueError(f"Component with ID {component_id} not found")
        if not requirement:
            raise ValueError(f"Requirement with ID {requirement_id} not found")
        
        # Create implements relationship
        now = datetime.now()
        properties = {
            "status": status,
            "created_at": now,
            "updated_at": now
        }
        
        return self.relationship_repo.create_relationship(
            component_id,
            NodeLabel.COMPONENT,
            requirement_id,
            NodeLabel.REQUIREMENT,
            RelationshipType.IMPLEMENTS,
            properties
        )
    
    # Implementation operations
    
    def create_implementation(
        self,
        name: str,
        path: str,
        component_id: str,
        language: Optional[str] = None,
        version: Optional[str] = None
    ) -> ImplementationModel:
        """Create a new implementation for a component.
        
        Args:
            name: Implementation name.
            path: File path or location.
            component_id: Component ID.
            language: Optional programming language.
            version: Optional version.
            
        Returns:
            Created implementation.
            
        Raises:
            ValueError: If component not found.
        """
        # Verify component exists
        component = self.component_repo.find_by_id(component_id)
        if not component:
            raise ValueError(f"Component with ID {component_id} not found")
        
        # Create implementation
        impl_data = {
            "name": name,
            "path": path,
            "language": language,
            "version": version,
            "status": "development"
        }
        implementation = self.implementation_repo.create(impl_data)
        
        # Link implementation to component
        self.relationship_repo.create_relationship(
            implementation.id,
            NodeLabel.IMPLEMENTATION,
            component_id,
            NodeLabel.COMPONENT,
            RelationshipType.BELONGS_TO
        )
        
        return implementation
    
    def link_implementation_to_requirement(
        self, 
        implementation_id: str, 
        requirement_id: str, 
        satisfaction_level: Optional[float] = None
    ) -> Dict:
        """Link an implementation to a requirement it satisfies.
        
        Args:
            implementation_id: Implementation ID.
            requirement_id: Requirement ID.
            satisfaction_level: Optional level of satisfaction (0.0-1.0).
            
        Returns:
            Relationship information.
            
        Raises:
            ValueError: If implementation or requirement not found.
        """
        # Verify entities exist
        implementation = self.implementation_repo.find_by_id(implementation_id)
        requirement = self.requirement_repo.find_by_id(requirement_id)
        
        if not implementation:
            raise ValueError(f"Implementation with ID {implementation_id} not found")
        if not requirement:
            raise ValueError(f"Requirement with ID {requirement_id} not found")
        
        # Create satisfies relationship
        now = datetime.now()
        properties = {
            "created_at": now,
            "updated_at": now
        }
        if satisfaction_level is not None:
            properties["satisfaction_level"] = max(0.0, min(1.0, satisfaction_level))
        
        return self.relationship_repo.create_relationship(
            implementation_id,
            NodeLabel.IMPLEMENTATION,
            requirement_id,
            NodeLabel.REQUIREMENT,
            RelationshipType.SATISFIES,
            properties
        )
    
    # Pattern operations
    
    def create_pattern(
        self,
        name: str,
        description: str,
        pattern_type: str
    ) -> PatternModel:
        """Create a new design pattern.
        
        Args:
            name: Pattern name.
            description: Pattern description.
            pattern_type: Pattern type.
            
        Returns:
            Created pattern.
        """
        pattern_data = {
            "name": name,
            "description": description,
            "type": pattern_type
        }
        return self.pattern_repo.create(pattern_data)
    
    def link_component_to_pattern(self, component_id: str, pattern_id: str) -> Dict:
        """Link a component to a design pattern it uses.
        
        Args:
            component_id: Component ID.
            pattern_id: Pattern ID.
            
        Returns:
            Relationship information.
            
        Raises:
            ValueError: If component or pattern not found.
        """
        # Verify entities exist
        component = self.component_repo.find_by_id(component_id)
        pattern = self.pattern_repo.find_by_id(pattern_id)
        
        if not component:
            raise ValueError(f"Component with ID {component_id} not found")
        if not pattern:
            raise ValueError(f"Pattern with ID {pattern_id} not found")
        
        # Create uses_pattern relationship
        properties = {"created_at": datetime.now()}
        
        return self.relationship_repo.create_relationship(
            component_id,
            NodeLabel.COMPONENT,
            pattern_id,
            NodeLabel.PATTERN,
            RelationshipType.USES_PATTERN,
            properties
        )
    
    # Agent operations
    
    def create_agent(
        self,
        name: str,
        agent_type: str,
        layer: str,
        description: Optional[str] = None
    ) -> AgentModel:
        """Create a new agent.
        
        Args:
            name: Agent name.
            agent_type: Agent type.
            layer: Agent layer.
            description: Optional agent description.
            
        Returns:
            Created agent.
        """
        agent_data = {
            "name": name,
            "type": agent_type,
            "layer": layer,
            "description": description or f"{name} agent",
            "status": "active"
        }
        return self.agent_repo.create(agent_data)
    
    def record_agent_contribution(
        self,
        agent_id: str,
        component_id: str,
        contribution_type: Optional[str] = None
    ) -> Dict:
        """Record an agent's contribution to a component.
        
        Args:
            agent_id: Agent ID.
            component_id: Component ID.
            contribution_type: Optional type of contribution.
            
        Returns:
            Relationship information.
            
        Raises:
            ValueError: If agent or component not found.
        """
        # Verify entities exist
        agent = self.agent_repo.find_by_id(agent_id)
        component = self.component_repo.find_by_id(component_id)
        
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")
        if not component:
            raise ValueError(f"Component with ID {component_id} not found")
        
        # Create contributes_to relationship
        properties = {"created_at": datetime.now()}
        if contribution_type:
            properties["contribution_type"] = contribution_type
        
        return self.relationship_repo.create_relationship(
            agent_id,
            NodeLabel.AGENT,
            component_id,
            NodeLabel.COMPONENT,
            RelationshipType.CONTRIBUTES_TO,
            properties
        )
    
    # Decision operations
    
    def record_decision(
        self,
        title: str,
        description: str,
        context: str,
        agent_id: str,
        related_component_ids: Optional[List[str]] = None,
        confidence: Optional[float] = None
    ) -> DecisionModel:
        """Record a decision made by an agent.
        
        Args:
            title: Decision title.
            description: Decision description.
            context: Decision context.
            agent_id: ID of the agent making the decision.
            related_component_ids: Optional IDs of related components.
            confidence: Optional confidence level (0.0-1.0).
            
        Returns:
            Created decision.
            
        Raises:
            ValueError: If agent not found.
        """
        # Verify agent exists
        agent = self.agent_repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")
        
        # Create decision
        decision_data = {
            "title": title,
            "description": description,
            "context": context,
            "status": "made"
        }
        decision = self.decision_repo.create(decision_data)
        
        # Link decision to agent
        properties = {"created_at": datetime.now()}
        if confidence is not None:
            properties["confidence"] = max(0.0, min(1.0, confidence))
        
        self.relationship_repo.create_relationship(
            decision.id,
            NodeLabel.DECISION,
            agent_id,
            NodeLabel.AGENT,
            RelationshipType.MADE_BY,
            properties
        )
        
        # Link decision to related components
        if related_component_ids:
            for component_id in related_component_ids:
                # Verify component exists
                component = self.component_repo.find_by_id(component_id)
                if not component:
                    logger.warning(f"Component with ID {component_id} not found, skipping relationship")
                    continue
                
                self.relationship_repo.create_relationship(
                    decision.id,
                    NodeLabel.DECISION,
                    component_id,
                    NodeLabel.COMPONENT,
                    RelationshipType.RELATED_TO,
                    {"created_at": datetime.now()}
                )
        
        return decision
    
    # Graph queries
    
    def find_path_between_components(
        self, 
        source_id: str, 
        target_id: str, 
        max_depth: int = 5
    ) -> List[Dict]:
        """Find paths between two components.
        
        Args:
            source_id: Source component ID.
            target_id: Target component ID.
            max_depth: Maximum path depth.
            
        Returns:
            List of paths with component information.
        """
        query = f"""
        MATCH path = (source:{NodeLabel.COMPONENT} {{id: $source_id}})-[:{RelationshipType.DEPENDS_ON}*1..{max_depth}]->(target:{NodeLabel.COMPONENT} {{id: $target_id}})
        RETURN path
        LIMIT 10
        """
        
        result = self.connection.query(query, {
            "source_id": source_id,
            "target_id": target_id
        })
        
        paths = []
        for record in result:
            if 'path' in record:
                path_nodes = []
                # Extract nodes and their properties
                # Implementation depends on how Neo4j returns path data
                # This is a simplified representation
                paths.append(path_nodes)
        
        return paths
    
    def find_component_dependencies_tree(
        self, 
        component_id: str, 
        max_depth: int = 3
    ) -> Dict:
        """Find the dependency tree for a component.
        
        Args:
            component_id: Component ID.
            max_depth: Maximum tree depth.
            
        Returns:
            Component dependency tree.
        """
        query = f"""
        MATCH path = (c:{NodeLabel.COMPONENT} {{id: $component_id}})-[:{RelationshipType.DEPENDS_ON}*0..{max_depth}]->(dep:{NodeLabel.COMPONENT})
        RETURN c, collect(distinct dep) as dependencies
        """
        
        result = self.connection.query(query, {"component_id": component_id})
        
        if not result:
            return {"component": None, "dependencies": []}
        
        component = result[0].get('c')
        dependencies = result[0].get('dependencies', [])
        
        return {
            "component": component,
            "dependencies": dependencies
        }
    
    def find_implementations_by_pattern(self, pattern_id: str) -> List[Dict]:
        """Find implementations using a specific pattern.
        
        Args:
            pattern_id: Pattern ID.
            
        Returns:
            List of implementations with component info.
        """
        query = f"""
        MATCH (c:{NodeLabel.COMPONENT})-[:{RelationshipType.USES_PATTERN}]->(p:{NodeLabel.PATTERN} {{id: $pattern_id}})
        MATCH (i:{NodeLabel.IMPLEMENTATION})-[:{RelationshipType.BELONGS_TO}]->(c)
        RETURN i, c
        """
        
        result = self.connection.query(query, {"pattern_id": pattern_id})
        
        return [
            {
                "implementation": record.get('i'),
                "component": record.get('c')
            }
            for record in result if 'i' in record and 'c' in record
        ]
    
    def get_agent_activity(self, agent_id: str) -> Dict:
        """Get an agent's activity summary.
        
        Args:
            agent_id: Agent ID.
            
        Returns:
            Agent activity summary.
        """
        # Get decisions made by the agent
        decisions = self.decision_repo.find_decisions_by_agent(agent_id)
        
        # Get components the agent contributed to
        query = f"""
        MATCH (a:{NodeLabel.AGENT} {{id: $agent_id}})-[r:{RelationshipType.CONTRIBUTES_TO}]->(c:{NodeLabel.COMPONENT})
        RETURN c, r.contribution_type as contribution_type
        """
        
        contributions_result = self.connection.query(query, {"agent_id": agent_id})
        
        contributions = [
            {
                "component": record.get('c'),
                "contribution_type": record.get('contribution_type')
            }
            for record in contributions_result if 'c' in record
        ]
        
        return {
            "agent_id": agent_id,
            "decisions_count": len(decisions),
            "decisions": [decision.dict() for decision in decisions],
            "contributions_count": len(contributions),
            "contributions": contributions
        }


class ProjectInsightService:
    """Service for generating project insights from the knowledge graph."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        """Initialize project insight service.
        
        Args:
            knowledge_service: Knowledge service.
        """
        self.knowledge_service = knowledge_service
    
    def get_project_overview(self, project_id: str) -> Dict:
        """Get an overview of a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Project overview.
        """
        project = self.knowledge_service.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        components = self.knowledge_service.get_components_by_project(project_id)
        requirements = self.knowledge_service.get_requirements_by_project(project_id)
        
        # Get requirement implementation status
        implementation_status = {}
        for req in requirements:
            query = f"""
            MATCH (c:{NodeLabel.COMPONENT})-[r:{RelationshipType.IMPLEMENTS}]->(req:{NodeLabel.REQUIREMENT} {{id: $req_id}})
            RETURN req.id as req_id, count(c) as implementing_components, collect(r.status) as statuses
            """
            
            result = self.knowledge_service.connection.query(query, {"req_id": req.id})
            
            if result:
                implementation_status[req.id] = {
                    "implementing_components": result[0].get('implementing_components', 0),
                    "statuses": result[0].get('statuses', [])
                }
        
        # Get components by status
        components_by_status = {}
        for comp in components:
            if comp.status not in components_by_status:
                components_by_status[comp.status] = 0
            components_by_status[comp.status] += 1
        
        # Get requirements by status
        requirements_by_status = {}
        for req in requirements:
            if req.status not in requirements_by_status:
                requirements_by_status[req.status] = 0
            requirements_by_status[req.status] += 1
        
        return {
            "project": project.dict(),
            "components_count": len(components),
            "requirements_count": len(requirements),
            "components_by_status": components_by_status,
            "requirements_by_status": requirements_by_status,
            "implementation_status": implementation_status
        }
    
    def get_component_dependencies_graph(self, project_id: str) -> Dict:
        """Get a graph of component dependencies in a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Component dependency graph.
        """
        components = self.knowledge_service.get_components_by_project(project_id)
        
        nodes = []
        edges = []
        
        # Add components as nodes
        for comp in components:
            nodes.append({
                "id": comp.id,
                "label": comp.name,
                "type": comp.type,
                "status": comp.status
            })
        
        # Add dependencies as edges
        for comp in components:
            query = f"""
            MATCH (source:{NodeLabel.COMPONENT} {{id: $source_id}})-[r:{RelationshipType.DEPENDS_ON}]->(target:{NodeLabel.COMPONENT})
            WHERE target.id in $target_ids
            RETURN source.id as source_id, target.id as target_id, r.dependency_type as dependency_type
            """
            
            result = self.knowledge_service.connection.query(query, {
                "source_id": comp.id,
                "target_ids": [c.id for c in components]
            })
            
            for record in result:
                if 'source_id' in record and 'target_id' in record:
                    edges.append({
                        "source": record['source_id'],
                        "target": record['target_id'],
                        "type": record.get('dependency_type', 'depends_on')
                    })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def get_agent_contributions_summary(self, project_id: str) -> Dict:
        """Get a summary of agent contributions to a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Agent contributions summary.
        """
        query = f"""
        MATCH (c:{NodeLabel.COMPONENT})-[:{RelationshipType.BELONGS_TO}]->(p:{NodeLabel.PROJECT} {{id: $project_id}})
        MATCH (a:{NodeLabel.AGENT})-[r:{RelationshipType.CONTRIBUTES_TO}]->(c)
        RETURN a.id as agent_id, a.name as agent_name, a.type as agent_type, a.layer as agent_layer,
               count(distinct c) as component_count,
               collect(distinct c.id) as component_ids,
               collect(distinct r.contribution_type) as contribution_types
        """
        
        result = self.knowledge_service.connection.query(query, {"project_id": project_id})
        
        contributions = []
        for record in result:
            if 'agent_id' in record:
                contributions.append({
                    "agent_id": record['agent_id'],
                    "agent_name": record['agent_name'],
                    "agent_type": record['agent_type'],
                    "agent_layer": record['agent_layer'],
                    "component_count": record['component_count'],
                    "component_ids": record['component_ids'],
                    "contribution_types": record['contribution_types']
                })
        
        return {
            "project_id": project_id,
            "agent_count": len(contributions),
            "contributions": contributions
        }