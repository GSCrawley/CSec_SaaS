"""
simple_demo.py

A simplified demonstration of the Development Crew system focusing on the knowledge fabric.
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

def run_demo():
   """Run a demonstration of the Development Crew system focusing on the knowledge fabric."""
   logger.info("Starting Development Crew knowledge fabric demonstration")
   
   try:
       # Step 1: Initialize the knowledge fabric
       logger.info("Step 1: Initializing knowledge fabric")
       knowledge_service = initialize_knowledge_fabric()
       
       # Step 2: Create an initial domain
       logger.info("Step 2: Creating a domain")
       domain_id = create_initial_domain(knowledge_service, "CyberSecurity")
       logger.info(f"Created domain with ID: {domain_id}")
       
       # Step 3: Create a project
       logger.info("Step 3: Creating a project")
       project = knowledge_service.create_project(
           name="Integrated Security Platform",
           domain_id=domain_id,
           description="An integrated cybersecurity GRC and incident response platform"
       )
       logger.info(f"Created project with ID: {project.id}")
       
       # Step 4: Create components
       logger.info("Step 4: Creating components")
       components = {}
       
       components["api_gateway"] = knowledge_service.create_component(
           name="API Gateway",
           component_type="service",
           project_id=project.id,
           description="API Gateway for the platform"
       )
       
       components["auth_service"] = knowledge_service.create_component(
           name="Authentication Service",
           component_type="service",
           project_id=project.id,
           description="Authentication and authorization service"
       )
       
       components["incident_manager"] = knowledge_service.create_component(
           name="Incident Manager",
           component_type="service",
           project_id=project.id,
           description="Incident management and response service"
       )
       
       logger.info(f"Created {len(components)} components")
       
       # Step 5: Create component dependencies
       logger.info("Step 5: Creating component dependencies")
       
       # API Gateway depends on Auth Service
       knowledge_service.add_component_dependency(
           component_id=components["api_gateway"].id,
           dependency_id=components["auth_service"].id,
           dependency_type="authentication"
       )
       
       # Incident Manager depends on API Gateway
       knowledge_service.add_component_dependency(
           component_id=components["incident_manager"].id,
           dependency_id=components["api_gateway"].id,
           dependency_type="api_access"
       )
       
       logger.info("Component dependencies created")
       
       # Step 6: Create requirements
       logger.info("Step 6: Creating requirements")
       requirements = {}
       
       requirements["secure_auth"] = knowledge_service.create_requirement(
           name="Secure Authentication",
           description="The system must implement OAuth 2.0 and MFA for secure authentication",
           requirement_type="security",
           priority="high",
           project_id=project.id
       )
       
       requirements["incident_response"] = knowledge_service.create_requirement(
           name="Incident Response Workflow",
           description="The system must support configurable incident response workflows with escalation paths",
           requirement_type="functional",
           priority="high",
           project_id=project.id
       )
       
       requirements["compliance"] = knowledge_service.create_requirement(
           name="Compliance Reporting",
           description="The system must generate compliance reports for major regulatory frameworks",
           requirement_type="compliance",
           priority="medium",
           project_id=project.id
       )
       
       logger.info(f"Created {len(requirements)} requirements")
       
       # Step 7: Link components to requirements
       logger.info("Step 7: Linking components to requirements")
       
       # Auth Service implements Secure Authentication
       knowledge_service.link_component_to_requirement(
           component_id=components["auth_service"].id,
           requirement_id=requirements["secure_auth"].id
       )
       
       # Incident Manager implements Incident Response Workflow
       knowledge_service.link_component_to_requirement(
           component_id=components["incident_manager"].id,
           requirement_id=requirements["incident_response"].id
       )
       
       # Both components contribute to Compliance Reporting
       knowledge_service.link_component_to_requirement(
           component_id=components["auth_service"].id,
           requirement_id=requirements["compliance"].id
       )
       
       knowledge_service.link_component_to_requirement(
           component_id=components["incident_manager"].id,
           requirement_id=requirements["compliance"].id
       )
       
       logger.info("Components linked to requirements")
       
       # Step 8: Query the knowledge graph
       logger.info("Step 8: Querying the knowledge graph")
       
       # Get all components in the project
       project_components = knowledge_service.get_components_by_project(project.id)
       logger.info(f"Project has {len(project_components)} components")
       
       # Get all requirements for the project
       project_requirements = knowledge_service.get_requirements_by_project(project.id)
       logger.info(f"Project has {len(project_requirements)} requirements")
       
       # Get components implementing a specific requirement
       auth_requirement_id = requirements["secure_auth"].id
       implementing_components = knowledge_service.component_repo.find_by_property("id", components["auth_service"].id)
       logger.info(f"Requirement 'Secure Authentication' is implemented by {len(implementing_components)} component(s)")
       
       # Get requirements for a specific component
       auth_service_requirements = knowledge_service.requirement_repo.find_requirements_for_component(components["auth_service"].id)
       logger.info(f"Auth Service implements {len(auth_service_requirements)} requirement(s)")
       
       # Clean up resources
       knowledge_service.close()
       
       logger.info("Knowledge fabric demonstration completed successfully")
       
   except Exception as e:
       logger.error(f"Error during demonstration: {e}", exc_info=True)

if __name__ == "__main__":
   run_demo()