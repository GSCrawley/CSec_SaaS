# Repository Structure

## Overview

This repository now contains two distinct products:

- **development_crew/**: The general-purpose agentic platform (all platform code, infra, docs)
- **csec_saas/**: The customizable Cybersecurity Incident Response SaaS application (all app-specific code, docs)

## Top-Level Layout

```text
CSec_SaaS/
├── development_crew/   # General-purpose agentic platform
├── csec_saas/          # Cybersecurity SaaS application
├── Comprehensive Integration Plan for Combining Cybersecurity Projects.pdf
├── Integrated Cybersecurity Platform - AI Agent Deployment Kickoff Checklist.md
├── README.md           # (top-level overview)
```

## development_crew/
- `agents/` — Specialized agent implementations
- `infrastructure/` — Core platform infrastructure (knowledge fabric, MCP servers, orchestration)
- `docs/` — Architecture, integration, and planning docs
- `repo-structure.md` — (this file)
- `requirements.txt` — Platform dependencies

## csec_saas/
- `docs/` — Cybersecurity SaaS documentation
- `src/` — Application source code
- `tests/` — Application tests
- `requirements.txt` — App-specific dependencies

## Boundaries & Integration

- All platform code and documentation lives in `development_crew/`.
- All application-specific code and documentation lives in `csec_saas/`.
- Applications in `csec_saas/` (or other future apps) should import and extend the platform from `development_crew/`.
- Shared resources or integration logic should be clearly documented in each product's README.

---

For further details, see the `README.md` files in each major directory.

## Key Components

### 1. Agent Architecture

The Development Crew follows a hierarchical structure with specialized agents handling different aspects of the development process:

- **Orchestration Layer**: Coordinates workflows and agent interactions
- **Planning Layer**: Handles system design, architecture, and requirements
- **Development Layer**: Implements code and application components
- **Operations Layer**: Manages deployment, testing, and documentation

### 2. MCP Servers

Each agent is powered by a dedicated Model Context Protocol (MCP) server that provides specialized tools and capabilities:

- Role-specific functions and utilities
- Knowledge base connections
- Specialized tool access
- Communication protocols
- State management system
- Reasoning and decision-making components

### 3. Knowledge Fabric

A unified knowledge system using Neo4j knowledge graphs to:

- Maintain relationships between entities
- Track development decisions and rationales
- Store contextual information for cross-agent collaboration
- Enable reasoning across domains through connected knowledge

### 4. Tool Integrations

The Development Crew connects with external tools through dedicated interfaces:

- **Jira**: For project management and issue tracking
- **Notion**: For documentation and knowledge management
- **Figma**: For design and user experience creation
- **Neo4j**: For knowledge graph implementation and querying

### 5. Domain Adaptability

The system is designed to be domain-agnostic with:

- Pluggable knowledge sources for domain-specific information
- Adaptable agent configurations for different types of applications
- Template-based project structures for new domains