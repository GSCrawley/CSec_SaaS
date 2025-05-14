"""
Project Manager Agent Module.

This module implements the Project Manager Agent responsible for coordinating workflows,
monitoring progress, identifying bottlenecks, and generating status reports.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from .tools import (create_project_plan_tool, generate_status_report_tool,
                   identify_bottlenecks_tool, monitor_project_progress_tool)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectManagerAgent:
    """Project Manager Agent implementation."""
    
    def __init__(self, 
                 api_key: str, 
                 model: str = "mixtral-8x7b-32768",
                 tools_config: Optional[Dict[str, Any]] = None,
                 agent_id: Optional[str] = None):
        """Initialize Project Manager Agent.
        
        Args:
            api_key: Groq API key for LLM access.
            model: LLM model to use.
            tools_config: Configuration for agent tools.
            agent_id: Optional agent ID for knowledge graph.
        """
        self.api_key = api_key
        self.model = model
        self.tools_config = tools_config or {}
        self.agent_id = agent_id
        
        # Initialize LLM
        self.llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.2,  # Low temperature for more focused responses
            max_tokens=4000
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent_executor = self._initialize_agent()
        
        logger.info(f"Project Manager Agent initialized with model {model}")
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize agent tools.
        
        Returns:
            List of tools for the agent.
        """
        return [
            create_project_plan_tool(self.tools_config.get("create_project_plan", {})),
            monitor_project_progress_tool(self.tools_config.get("monitor_project_progress", {})),
            identify_bottlenecks_tool(self.tools_config.get("identify_bottlenecks", {})),
            generate_status_report_tool(self.tools_config.get("generate_status_report", {}))
        ]
    
    def _initialize_agent(self) -> AgentExecutor:
        """Initialize the agent executor.
        
        Returns:
            AgentExecutor instance.
        """
        # Define agent prompt
        prompt_template = """
        You are the Project Manager Agent within the Development Crew. Your role is to coordinate workflows,
        monitor progress, identify bottlenecks, and generate status reports. You have deep expertise in
        project management methodologies and practices.
        
        As the Project Manager, you are responsible for:
        1. Creating and maintaining comprehensive project plans
        2. Tracking progress against milestones and deadlines
        3. Identifying and resolving bottlenecks and issues
        4. Generating detailed status reports for stakeholders
        5. Ensuring effective communication across the agent team
        
        When responding, maintain a professional, organized, and precise tone appropriate for a project manager.
        
        Current date and time: {current_datetime}
        
        User request: {input}
        
        {agent_scratchpad}
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={"current_datetime": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        )
        
        # Create the agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """Process a user request.
        
        Args:
            request: User request string.
            
        Returns:
            Agent response dictionary.
        """
        logger.info(f"Processing request: {request}")
        
        start_time = time.time()
        
        try:
            # Run the agent executor to generate a response
            response = self.agent_executor.invoke({"input": request})
            
            # Process and format the response
            output = {
                "status": "success",
                "response": response.get("output", ""),
                "processing_time": time.time() - start_time
            }
            
            logger.info(f"Request processed successfully in {output['processing_time']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            output = {
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
        
        return output
    
    def create_project_plan(self, requirements: List[Dict], timeline_constraints: Dict) -> Dict:
        """Create a comprehensive project plan.
        
        Args:
            requirements: List of project requirements.
            timeline_constraints: Timeline constraints for the project.
            
        Returns:
            Project plan dictionary.
        """
        logger.info("Creating project plan")
        
        request = f"""
        Create a comprehensive project plan based on the following requirements and timeline constraints:
        
        Requirements:
        {requirements}
        
        Timeline Constraints:
        {timeline_constraints}
        
        Please provide a detailed plan with milestones, tasks, dependencies, and resource allocations.
        """
        
        response = self.process_request(request)
        
        # If successful, parse the response to extract structured project plan
        if response["status"] == "success":
            # This would typically involve more complex parsing of the LLM response
            # to extract a structured project plan
            return {
                "plan": response["response"],
                "generated_at": datetime.now().isoformat()
            }
        else:
            return {
                "error": response.get("error", "Unknown error creating project plan")
            }
    
    def monitor_project_progress(self, project_id: str) -> Dict:
        """Monitor project progress.
        
        Args:
            project_id: Project ID to monitor.
            
        Returns:
            Project progress status.
        """
        logger.info(f"Monitoring progress for project {project_id}")
        
        request = f"""
        Monitor the current progress of project {project_id}. 
        Please analyze the current status of all tasks, milestones, and deliverables.
        Identify any delays or issues that need attention.
        """
        
        response = self.process_request(request)
        
        if response["status"] == "success":
            return {
                "project_id": project_id,
                "status_report": response["response"],
                "generated_at": datetime.now().isoformat()
            }
        else:
            return {
                "project_id": project_id,
                "error": response.get("error", "Unknown error monitoring project progress")
            }
    
    def identify_bottlenecks(self, project_id: str) -> List[Dict]:
        """Identify bottlenecks in the project workflow.
        
        Args:
            project_id: Project ID to analyze.
            
        Returns:
            List of identified bottlenecks.
        """
        logger.info(f"Identifying bottlenecks for project {project_id}")
        
        request = f"""
        Identify current and potential bottlenecks in project {project_id}.
        Please analyze the workflow, resource allocation, dependencies, and critical paths.
        For each bottleneck, provide a description, impact assessment, and potential mitigation strategies.
        """
        
        response = self.process_request(request)
        
        if response["status"] == "success":
            # This would typically involve more complex parsing of the LLM response
            # to extract structured bottleneck information
            return [{
                "project_id": project_id,
                "bottlenecks": response["response"],
                "identified_at": datetime.now().isoformat()
            }]
        else:
            return [{
                "project_id": project_id,
                "error": response.get("error", "Unknown error identifying bottlenecks")
            }]
    
    def generate_status_report(self, project_id: str, report_type: str = "detailed") -> Dict:
        """Generate a project status report.
        
        Args:
            project_id: Project ID for the report.
            report_type: Type of report to generate (summary, detailed, executive).
            
        Returns:
            Project status report.
        """
        logger.info(f"Generating {report_type} status report for project {project_id}")
        
        request = f"""
        Generate a {report_type} status report for project {project_id}.
        Include information on overall progress, milestone status, key achievements,
        current challenges, risk assessment, and next steps.
        """
        
        response = self.process_request(request)
        
        if response["status"] == "success":
            return {
                "project_id": project_id,
                "report_type": report_type,
                "report_content": response["response"],
                "generated_at": datetime.now().isoformat()
            }
        else:
            return {
                "project_id": project_id,
                "report_type": report_type,
                "error": response.get("error", "Unknown error generating status report")
            }