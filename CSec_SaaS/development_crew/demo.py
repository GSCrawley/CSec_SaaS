"""
demo.py

A demonstration of the Development Crew system with agent creation,
knowledge fabric initialization, and agent communication.
"""

import logging
import os
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import necessary components
from infrastructure.knowledge_fabric.init import initialize_knowledge_fabric, create_initial_domain
from infrastructure.communication.agent_communication import AgentCommunicationSystem
from agents.core.agent_factory import AgentFactory

def run_demo():
    """Run a demonstration of the Development Crew system."""
    logger.info("Starting Development Crew demonstration")
    
    # Step 1: Initialize the knowledge fabric
    logger.info("Step 1: Initializing knowledge fabric")
    knowledge_service = initialize_knowledge_fabric()
    
    # Create an initial domain for our demo project
    domain_id = create_initial_domain(knowledge_service, "DemoProject")
    logger.info(f"Created domain with ID: {domain_id}")
    
    # Step 2: Set up the communication system
    logger.info("Step 2: Setting up communication system")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    communication_system = AgentCommunicationSystem(redis_url)
    
    # Start listening for messages
    listen_thread = communication_system.start_listening()
    
    # Step 3: Create agents using the factory
    logger.info("Step 3: Creating agents")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY environment variable not set")
        return
    
    # Create the orchestration team
    agents = AgentFactory.create_orchestration_team(
        api_key=api_key,
        knowledge_service=knowledge_service,
        communication_system=communication_system
    )
    
    project_manager = agents["project_manager"]
    requirements_analyst = agents["requirements_analyst"]
    
    # Step 4: Create a project in the knowledge graph
    logger.info("Step 4: Creating a project")
    project = knowledge_service.create_project(
        name="Demo Application",
        domain_id=domain_id,
        description="A demonstration project for testing the Development Crew system"
    )
    logger.info(f"Created project with ID: {project.id}")
    
    # Step 5: Demonstrate agent communication
    logger.info("Step 5: Demonstrating agent communication")
    
    # Project Manager sends a request to Requirements Analyst
    request_id = project_manager.send_request_to_agent(
        requirements_analyst.config.agent_id,
        "gather_requirements",
        {
            "project_id": project.id,
            "description": "We need to gather requirements for the Demo Application",
            "priority": "high"
        }
    )
    logger.info(f"Project Manager sent request with ID: {request_id}")
    
    # Wait for communication to complete
    logger.info("Waiting for communication to complete...")
    time.sleep(5)
    
    # Step 6: Record a decision in the knowledge graph
    logger.info("Step 6: Recording a decision")
    decision_id = project_manager.record_decision(
        title="Initial project setup",
        description="Decided to use a microservices architecture for the Demo Application",
        context="Based on the requirements and scalability needs",
        confidence=0.85
    )
    logger.info(f"Recorded decision with ID: {decision_id}")
    
    # Wait for notification to be processed
    time.sleep(2)
    
    # Step 7: Create a component
    logger.info("Step 7: Creating a component")
    component = knowledge_service.create_component(
        name="API Gateway",
        component_type="service",
        project_id=project.id,
        description="API Gateway for the Demo Application"
    )
    logger.info(f"Created component with ID: {component.id}")
    
    # Step 8: Create a requirement
    logger.info("Step 8: Creating a requirement")
    requirement = knowledge_service.create_requirement(
        name="Secure Authentication",
        description="The system must implement OAuth 2.0 for secure authentication",
        requirement_type="security",
        priority="high",
        project_id=project.id
    )
    logger.info(f"Created requirement with ID: {requirement.id}")
    
    # Link component to requirement
    logger.info("Linking component to requirement")
    knowledge_service.link_component_to_requirement(
        component_id=component.id,
        requirement_id=requirement.id
    )
    
    # Step 9: Broadcast status update
    logger.info("Step 9: Broadcasting status update")
    project_manager.broadcast_notification(
        "project_status_update",
        {
            "project_id": project.id,
            "status": "in_progress",
            "completion_percentage": 15,
            "next_milestone": "Requirements gathering completion"
        }
    )
    
    # Wait for notification to be processed
    time.sleep(2)
    
    # Step 10: Shutdown the agents
    logger.info("Step 10: Shutting down agents")
    for agent_type, agent in agents.items():
        logger.info(f"Shutting down {agent_type} agent")
        agent.shutdown()
    
    # Stop the communication system
    communication_system.stop_listening()
    
    # Clean up
    knowledge_service.close()
    
    logger.info("Demonstration completed successfully")

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        logger.error(f"Error during demonstration: {e}", exc_info=True)