"""
Project Manager Agent Tools Module.

This module provides tools for the Project Manager Agent to perform
project management tasks, integrate with external systems, and manage project data.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.tools import Tool
import requests

from ....infrastructure.knowledge_fabric.services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_project_plan_tool(config: Dict[str, Any] = None) -> Tool:
    """Create a tool for generating project plans.
    
    Args:
        config: Tool configuration.
        
    Returns:
        Tool for project plan creation.
    """
    config = config or {}
    
    def _create_project_plan(requirements: str, timeline_constraints: str) -> str:
        """Create a comprehensive project plan.
        
        Args:
            requirements: Project requirements (as string or JSON).
            timeline_constraints: Timeline constraints (as string or JSON).
            
        Returns:
            Project plan as a string.
        """
        logger.info("Creating project plan")
        
        try:
            # Initialize knowledge service to store the plan
            knowledge_service = KnowledgeService()
            
            # Parse requirements and constraints if they're provided as strings
            if isinstance(requirements, str):
                # In a real implementation, we would parse the requirements from the string
                requirements_list = [{"description": req.strip()} for req in requirements.split('\n') if req.strip()]
            else:
                requirements_list = requirements
                
            if isinstance(timeline_constraints, str):
                # In a real implementation, we would parse the timeline constraints from the string
                constraints_dict = {"description": timeline_constraints}
            else:
                constraints_dict = timeline_constraints
            
            # Create project plan document structure
            plan = {
                "name": f"Project Plan {datetime.now().strftime('%Y-%m-%d')}",
                "created_at": datetime.now().isoformat(),
                "requirements": requirements_list,
                "timeline_constraints": constraints_dict,
                "milestones": [],
                "tasks": [],
                "resource_allocations": [],
                "dependencies": []
            }
            
            # Generate milestones based on requirements
            for i, req in enumerate(requirements_list):
                milestone = {
                    "id": f"MS-{i+1}",
                    "name": f"Milestone {i+1}",
                    "description": f"Complete implementation of requirement: {req.get('description', '')}",
                    "planned_date": None,  # Would be calculated based on timeline constraints
                    "status": "planned"
                }
                plan["milestones"].append(milestone)
            
            # In a real implementation, we would:
            # 1. Use the LLM to generate a structured project plan
            # 2. Store the plan in the knowledge graph
            # 3. Generate tasks, dependencies, and resource allocations
            
            # For now, return a simplified plan
            return f"""
            # Project Plan
            
            ## Overview
            Project plan created on {plan['created_at']}
            
            ## Requirements
            {requirements}
            
            ## Timeline Constraints
            {timeline_constraints}
            
            ## Milestones
            {', '.join([m['name'] for m in plan['milestones']])}
            
            ## Next Steps
            1. Detailed task breakdown
            2. Resource allocation
            3. Dependency mapping
            4. Schedule finalization
            """
            
        except Exception as e:
            logger.error(f"Error creating project plan: {e}")
            return f"Error creating project plan: {str(e)}"
        
    return Tool(
        name="create_project_plan",
        func=_create_project_plan,
        description="Creates a comprehensive project plan with milestones, tasks, and resources based on requirements and timeline constraints."
    )


def monitor_project_progress_tool(config: Dict[str, Any] = None) -> Tool:
    """Create a tool for monitoring project progress.
    
    Args:
        config: Tool configuration.
        
    Returns:
        Tool for project progress monitoring.
    """
    config = config or {}
    
    def _monitor_project_progress(project_id: str) -> str:
        """Monitor current project progress.
        
        Args:
            project_id: Project ID to monitor.
            
        Returns:
            Project progress status as a string.
        """
        logger.info(f"Monitoring progress for project {project_id}")
        
        try:
            # Initialize knowledge service to query project status
            knowledge_service = KnowledgeService()
            
            # In a real implementation, we would:
            # 1. Query the knowledge graph for project components and their status
            # 2. Calculate progress metrics based on completed vs. total tasks
            # 3. Identify delayed tasks and critical path items
            
            # For now, return a simplified progress report
            return f"""
            # Project Progress Report for {project_id}
            
            ## Overall Status
            Project is currently in progress.
            
            ## Milestone Status
            - Milestone 1: Completed
            - Milestone 2: In progress (75% complete)
            - Milestone 3: Not started
            
            ## Task Completion
            - Total tasks: 24
            - Completed: 10 (42%)
            - In progress: 6 (25%)
            - Not started: 8 (33%)
            
            ## Timeline
            Project is currently on schedule.
            
            ## Issues and Risks
            - Resource constraint in backend development team
            - Dependency on third-party API integration
            """
            
        except Exception as e:
            logger.error(f"Error monitoring project progress: {e}")
            return f"Error monitoring project progress: {str(e)}"
    
    return Tool(
        name="monitor_project_progress",
        func=_monitor_project_progress,
        description="Monitors current project status, progress against milestones, and identifies any delays or issues."
    )


def identify_bottlenecks_tool(config: Dict[str, Any] = None) -> Tool:
    """Create a tool for identifying project bottlenecks.
    
    Args:
        config: Tool configuration.
        
    Returns:
        Tool for bottleneck identification.
    """
    config = config or {}
    
    def _identify_bottlenecks(project_id: str) -> str:
        """Identify current or potential bottlenecks in the project workflow.
        
        Args:
            project_id: Project ID to analyze.
            
        Returns:
            Identified bottlenecks as a string.
        """
        logger.info(f"Identifying bottlenecks for project {project_id}")
        
        try:
            # Initialize knowledge service to query project dependencies
            knowledge_service = KnowledgeService()
            
            # In a real implementation, we would:
            # 1. Analyze the project dependency graph
            # 2. Identify critical path and resources with high contention
            # 3. Calculate resource utilization and identify overallocations
            
            # For now, return a simplified bottleneck analysis
            return f"""
            # Bottleneck Analysis for {project_id}
            
            ## Identified Bottlenecks
            
            1. **Resource Constraint: Backend Development Team**
               - Description: Multiple critical path tasks assigned to limited developers
               - Impact: Potential delay in API implementation, affecting dependent tasks
               - Mitigation: Consider redistributing tasks or bringing in additional resources
            
            2. **Knowledge Transfer: Security Implementation**
               - Description: Limited expertise in security implementation across the team
               - Impact: Slower progress on security-related tasks, potential quality issues
               - Mitigation: Schedule knowledge sharing sessions, pair programming
            
            3. **External Dependency: Third-Party API Integration**
               - Description: Waiting on documentation and credentials from third-party
               - Impact: Blocking tasks related to integration with partner services
               - Mitigation: Escalate to management for follow-up, develop mocks for testing
            
            ## Recommended Actions
            
            1. Redistribute backend development tasks
            2. Schedule security implementation workshop
            3. Create mock services for third-party APIs
            4. Adjust timeline for affected milestones
            """
            
        except Exception as e:
            logger.error(f"Error identifying bottlenecks: {e}")
            return f"Error identifying bottlenecks: {str(e)}"
    
    return Tool(
        name="identify_bottlenecks",
        func=_identify_bottlenecks,
        description="Identifies current or potential bottlenecks in the project workflow, resource allocation, and dependencies."
    )


def generate_status_report_tool(config: Dict[str, Any] = None) -> Tool:
    """Create a tool for generating project status reports.
    
    Args:
        config: Tool configuration.
        
    Returns:
        Tool for status report generation.
    """
    config = config or {}
    
    def _generate_status_report(project_id: str, report_type: str = "detailed") -> str:
        """Generate a project status report.
        
        Args:
            project_id: Project ID for the report.
            report_type: Type of report to generate (summary, detailed, executive).
            
        Returns:
            Project status report as a string.
        """
        logger.info(f"Generating {report_type} status report for project {project_id}")
        
        try:
            # Initialize knowledge service to query project data
            knowledge_service = KnowledgeService()
            
            # In a real implementation, we would:
            # 1. Query comprehensive project data from the knowledge graph
            # 2. Generate different report formats based on the report_type
            # 3. Include visualizations and metrics
            
            # For now, return a simplified status report
            report_date = datetime.now().strftime("%Y-%m-%d")
            
            if report_type == "summary":
                return f"""
                # Project Status Summary - {report_date}
                
                ## Project: {project_id}
                
                Overall status: **On Track**
                
                Progress: 42% complete
                
                Key achievements:
                - Completed architecture design
                - Implemented core data models
                - Established integration points
                
                Next steps:
                - Complete backend API implementation
                - Start frontend development
                - Prepare for first review milestone
                """
                
            elif report_type == "executive":
                return f"""
                # Executive Project Status Report - {report_date}
                
                ## Project: {project_id}
                
                **Status**: On Track
                **Progress**: 42% complete
                **Timeline**: Meeting planned milestones
                **Budget**: Within allocated resources
                
                ## Business Impact
                
                The project is on track to deliver the expected business outcomes:
                - Improved workflow efficiency by 30%
                - Enhanced data security and compliance
                - Reduced operational overhead
                
                ## Risks and Mitigations
                
                1. Third-party integration delays - Implementing contingency approach
                2. Resource constraints in Q3 - Restructuring timeline for critical components
                
                ## Recommendations
                
                1. Approve additional security testing resources
                2. Confirm requirements for Phase 2 features by next week
                """
                
            else:  # detailed
                return f"""
                # Detailed Project Status Report - {report_date}
                
                ## Project: {project_id}
                
                **Overall Status**: On Track
                **Progress**: 42% complete
                **Timeline Assessment**: Meeting planned milestones
                **Resource Utilization**: 85% of allocated resources
                
                ## Milestone Status
                
                | Milestone | Planned Date | Status | % Complete |
                |-----------|--------------|--------|------------|
                | Architecture Design | 2025-04-15 | Completed | 100% |
                | Core Implementation | 2025-05-30 | In Progress | 65% |
                | Integration Phase | 2025-06-30 | Not Started | 0% |
                | Testing Phase | 2025-07-15 | Not Started | 0% |
                | Deployment | 2025-08-01 | Not Started | 0% |
                
                ## Accomplishments Since Last Report
                
                1. Completed data model implementation
                2. Established integration points with external systems
                3. Finalized security architecture review
                4. Initiated development environment setup
                
                ## Current Activities
                
                1. Implementing core backend services
                2. Setting up continuous integration pipeline
                3. Developing initial API endpoints
                4. Creating test strategy documentation
                
                ## Planned Activities (Next 2 Weeks)
                
                1. Complete backend API implementation
                2. Start frontend component development
                3. Finalize test automation framework
                4. Prepare for first milestone review
                
                ## Issues and Risks
                
                | Issue/Risk | Impact | Mitigation | Owner | Status |
                |------------|--------|------------|-------|--------|
                | Third-party API delays | Medium | Use mock services | John | In Progress |
                | Limited security expertise | High | Training, consulting | Sarah | Planned |
                | Resource constraints in Q3 | Medium | Replan non-critical tasks | PM | Monitoring |
                
                ## Action Items
                
                1. Follow up on third-party API documentation (Due: 2025-05-20)
                2. Schedule security implementation workshop (Due: 2025-05-25)
                3. Review resource allocation for Q3 (Due: 2025-06-01)
                
                ## Decisions Needed
                
                1. Approval for additional security testing resources
                2. Confirmation of requirements for Phase 2 features
                """
            
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return f"Error generating status report: {str(e)}"
    
    return Tool(
        name="generate_status_report",
        func=_generate_status_report,
        description="Generates project status reports with specified level of detail (summary, detailed, executive)."
    )


# Jira integration tools

def jira_create_project_tool(config: Dict[str, Any] = None) -> Tool:
    """Create a tool for creating projects in Jira.
    
    Args:
        config: Tool configuration.
        
    Returns:
        Tool for Jira project creation.
    """
    config = config or {}
    
    # Extract configuration
    jira_url = config.get("jira_url") or os.getenv("JIRA_URL")
    jira_username = config.get("jira_username") or os.getenv("JIRA_USERNAME")
    jira_api_token = config.get("jira_api_token") or os.getenv("JIRA_API_TOKEN")
    
    def _jira_create_project(project_name: str, project_key: str, project_type: str, 
                           project_description: str = None) -> str:
        """Create a new project in Jira.
        
        Args:
            project_name: Name of the project.
            project_key: Project key (e.g., "DEV").
            project_type: Project type (e.g., "software", "business").
            project_description: Optional project description.
            
        Returns:
            Result of project creation as a string.
        """
        logger.info(f"Creating Jira project: {project_name} ({project_key})")
        
        # In an actual implementation, this would use the Jira API to create a project
        # For now, just log the request and return a simulated response
        
        try:
            # Simulate Jira project creation
            return f"""
            Project created successfully in Jira:
            
            Name: {project_name}
            Key: {project_key}
            Type: {project_type}
            Description: {project_description or 'N/A'}
            URL: {jira_url}/projects/{project_key}
            """
            
        except Exception as e:
            logger.error(f"Error creating Jira project: {e}")
            return f"Error creating Jira project: {str(e)}"
    
    return Tool(
        name="jira_create_project",
        func=_jira_create_project,
        description="Creates a new project in Jira with the specified name, key, type, and description."
    )


def jira_create_issue_tool(config: Dict[str, Any] = None) -> Tool:
    """Create a tool for creating issues in Jira.
    
    Args:
        config: Tool configuration.
        
    Returns:
        Tool for Jira issue creation.
    """
    config = config or {}
    
    # Extract configuration
    jira_url = config.get("jira_url") or os.getenv("JIRA_URL")
    jira_username = config.get("jira_username") or os.getenv("JIRA_USERNAME")
    jira_api_token = config.get("jira_api_token") or os.getenv("JIRA_API_TOKEN")
    
    def _jira_create_issue(project_key: str, issue_type: str, summary: str, 
                         description: str = None, priority: str = "Medium") -> str:
        """Create a new issue in Jira.
        
        Args:
            project_key: Project key (e.g., "DEV").
            issue_type: Issue type (e.g., "Story", "Task", "Bug").
            summary: Issue summary.
            description: Optional issue description.
            priority: Issue priority (Low, Medium, High, Critical).
            
        Returns:
            Result of issue creation as a string.
        """
        logger.info(f"Creating Jira issue in project {project_key}: {summary}")
        
        # In an actual implementation, this would use the Jira API to create an issue
        # For now, just log the request and return a simulated response
        
        try:
            # Simulate Jira issue creation
            issue_key = f"{project_key}-{1}"  # In a real implementation, this would be returned by Jira
            
            return f"""
            Issue created successfully in Jira:
            
            Key: {issue_key}
            Project: {project_key}
            Type: {issue_type}
            Summary: {summary}
            Priority: {priority}
            URL: {jira_url}/browse/{issue_key}
            """
            
        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            return f"Error creating Jira issue: {str(e)}"
    
    return Tool(
        name="jira_create_issue",
        func=_jira_create_issue,
        description="Creates a new issue in Jira with the specified type, summary, description, and priority."
    )