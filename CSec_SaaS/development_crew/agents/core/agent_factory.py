"""
agents/core/agent_factory.py

This module provides a factory for creating specialized agent instances.
It centralizes agent creation logic and ensures consistent configuration.
"""

import logging
from typing import Any, Dict, Optional, Type

from infrastructure.communication.agent_communication import AgentCommunicationSystem
from infrastructure.knowledge_fabric.services.knowledge_service import KnowledgeService
from agents.core.base_agent import Agent, AgentConfig

# Import specialized agent classes as needed
# This will be expanded as we implement more agent types
from agents.orchestration.project_manager.agent import ProjectManagerAgent
from agents.orchestration.requirements_analyst.agent import RequirementsAnalystAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agent instances."""
    
    # Registry of agent types to classes
    _agent_registry: Dict[str, Type[Agent]] = {
        "project_manager": ProjectManagerAgent,
        "requirements_analyst": RequirementsAnalystAgent,
        # Add more as they are implemented
    }
    
    # Default layers for agent types if not specified
    _default_layers: Dict[str, str] = {
        "project_manager": "orchestration",
        "requirements_analyst": "orchestration",
        "quality_assurance": "orchestration",
        "architecture": "planning",
        "security_architect": "planning",
        "ux_designer": "planning",
        "data_architect": "planning",
        "backend_developer": "development",
        "frontend_developer": "development",
        "database_engineer": "development",
        "ml_engineer": "development",
        "framework_specialist": "development",
        "incident_response": "development",
        "devops": "operations",
        "security_operations": "operations",
        "documentation": "operations",
        "tester": "operations"
    }
    
    @classmethod
    def register_agent_class(cls, agent_type: str, agent_class: Type[Agent]) -> None:
        """Register a new agent class for a specific type.
        
        Args:
            agent_type: Agent type identifier.
            agent_class: Agent class to register.
        """
        cls._agent_registry[agent_type] = agent_class
        logger.info(f"Registered agent class for type: {agent_type}")
    
    @classmethod
    def create_agent(cls, 
                   agent_type: str,
                   agent_name: str,
                   api_key: str,
                   agent_layer: Optional[str] = None,
                   description: Optional[str] = None,
                   model: str = "mixtral-8x7b-32768",
                   knowledge_service: Optional[KnowledgeService] = None,
                   communication_system: Optional[AgentCommunicationSystem] = None,
                   tools_config: Optional[Dict[str, Any]] = None,
                   agent_id: Optional[str] = None) -> Agent:
        """Create a specialized agent instance.
        
        Args:
            agent_type: Type of agent to create.
            agent_name: Name for the agent.
            api_key: API key for the LLM.
            agent_layer: Optional layer the agent belongs to (defaults based on type).
            description: Optional agent description.
            model: LLM model to use.
            knowledge_service: Optional knowledge service to use.
            communication_system: Optional communication system to use.
            tools_config: Optional configuration for agent tools.
            agent_id: Optional existing agent ID in knowledge graph.
            
        Returns:
            Initialized agent instance.
            
        Raises:
            ValueError: If agent type is not registered.
        """
        if agent_type not in cls._agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Determine agent layer if not provided
        if agent_layer is None:
            agent_layer = cls._default_layers.get(agent_type, "unknown")
        
        # Create agent configuration
        config = AgentConfig(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            agent_layer=agent_layer,
            description=description or f"{agent_name} - {agent_type} agent",
            model=model,
            tools_config=tools_config or {},
            api_keys={"groq": api_key}  # Add more API keys as needed
        )
        
        # Get agent class and create instance
        agent_class = cls._agent_registry[agent_type]
        
        try:
            agent = agent_class(
                config=config,
                knowledge_service=knowledge_service,
                communication_system=communication_system
            )
            logger.info(f"Created agent: {agent_name} ({agent_type})")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent {agent_name} ({agent_type}): {e}", exc_info=True)
            raise
    
    @classmethod
    def get_available_agent_types(cls) -> Dict[str, str]:
        """Get a list of available agent types and their default layers.
        
        Returns:
            Dictionary mapping agent types to their default layers.
        """
        return {agent_type: cls._default_layers.get(agent_type, "unknown") 
                for agent_type in cls._agent_registry.keys()}
    
    @classmethod
    def create_orchestration_team(cls,
                                api_key: str,
                                knowledge_service: Optional[KnowledgeService] = None,
                                communication_system: Optional[AgentCommunicationSystem] = None,
                                model: str = "mixtral-8x7b-32768") -> Dict[str, Agent]:
        """Create the orchestration layer agent team.
        
        Args:
            api_key: API key for the LLM.
            knowledge_service: Optional knowledge service to use.
            communication_system: Optional communication system to use.
            model: LLM model to use.
            
        Returns:
            Dictionary mapping agent types to agent instances.
        """
        orchestration_agents = {}
        
        # Create Project Manager agent
        orchestration_agents["project_manager"] = cls.create_agent(
            agent_type="project_manager",
            agent_name="Project Manager Agent",
            api_key=api_key,
            description="Coordinates workflows, monitors progress, identifies bottlenecks",
            model=model,
            knowledge_service=knowledge_service,
            communication_system=communication_system
        )
        
        # Create Requirements Analyst agent
        orchestration_agents["requirements_analyst"] = cls.create_agent(
            agent_type="requirements_analyst",
            agent_name="Requirements Analyst Agent",
            api_key=api_key,
            description="Translates business needs into technical requirements",
            model=model,
            knowledge_service=knowledge_service,
            communication_system=communication_system
        )
        
        # Quality Assurance agent will be added when implemented
        
        logger.info(f"Created orchestration team with {len(orchestration_agents)} agents")
        return orchestration_agents