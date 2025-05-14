"""
Requirements Analyst Agent Module.

This module implements the Requirements Analyst Agent responsible for translating business needs
into technical requirements, generating acceptance criteria, and validating requirements for completeness,
consistency, and clarity.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from .tools import (
    requirements_elicitation_tool,
    requirements_analysis_tool,
    requirements_validation_tool,
    traceability_matrix_tool,
    stakeholder_communication_tool
)

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.tools import Tool

class RequirementsAnalystAgent:
    """
    Requirements Analyst Agent implementation.
    Translates business needs into technical requirements, validates requirements, and ensures alignment with project goals.
    Integrates with MCP server for requirements engineering tasks.
    """
    def __init__(self,
                 api_key: str,
                 model: str = "mixtral-8x7b-32768",
                 tools_config: Optional[Dict[str, Any]] = None,
                 agent_id: Optional[str] = None):
        """Initialize Requirements Analyst Agent."""
        self.api_key = api_key
        self.model = model
        self.tools_config = tools_config or {}
        self.agent_id = agent_id

        # Initialize LLM
        self.llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.2,
            max_tokens=4000
        )

        # Initialize tools
        self.tools = self._initialize_tools()

        # Initialize agent
        self.agent_executor = self._initialize_agent()

    def _initialize_tools(self) -> List[Tool]:
        """Initialize agent tools."""
        return [
            requirements_elicitation_tool(self.tools_config.get("requirements_elicitation", {})),
            requirements_analysis_tool(self.tools_config.get("requirements_analysis", {})),
            requirements_validation_tool(self.tools_config.get("requirements_validation", {})),
            traceability_matrix_tool(self.tools_config.get("traceability_matrix", {})),
            stakeholder_communication_tool(self.tools_config.get("stakeholder_communication", {})),
        ]

    def _initialize_agent(self) -> AgentExecutor:
        """Initialize the agent executor."""
        prompt_template = """
        You are the Requirements Analyst Agent within the Development Crew. Your role is to translate business needs into actionable technical requirements, validate requirements, and ensure alignment with project objectives. You are skilled at requirements elicitation, analysis, validation, and stakeholder communication.

        As the Requirements Analyst, you are responsible for:
        1. Gathering requirements from stakeholders or prompts
        2. Analyzing, clustering, and clarifying requirements
        3. Validating requirements for completeness, ambiguity, and conflicts
        4. Generating traceability matrices
        5. Simulating stakeholder interviews to clarify requirements

        When responding, maintain a precise, analytical, and collaborative tone appropriate for a requirements analyst.

        Current date and time: {current_datetime}

        User request: {input}

        {agent_scratchpad}
        """
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={"current_datetime": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        )
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def process_request(self, request: str) -> Dict:
        """Process a user request."""
        response = self.agent_executor.invoke({"input": request})
        return {"status": "success", "response": response["output"]}

    def elicit_requirements(self, prompt: str) -> Dict:
        """Gather requirements from a prompt or stakeholder simulation."""
        response = self.process_request(f"Elicit requirements: {prompt}")
        return response

    def analyze_requirements(self, requirements: List[str]) -> Dict:
        """Analyze, cluster, and clarify requirements."""
        response = self.process_request(f"Analyze requirements: {requirements}")
        return response

    def validate_requirements(self, requirements: List[str]) -> Dict:
        """Validate requirements for completeness, ambiguity, and conflicts."""
        response = self.process_request(f"Validate requirements: {requirements}")
        return response

    def generate_traceability_matrix(self, requirements: List[str]) -> Dict:
        """Generate a traceability matrix for requirements."""
        response = self.process_request(f"Generate traceability matrix for: {requirements}")
        return response

    def simulate_stakeholder_communication(self, question: str) -> Dict:
        """Simulate stakeholder Q&A for requirements clarification."""
        response = self.process_request(f"Stakeholder question: {question}")
        return response
