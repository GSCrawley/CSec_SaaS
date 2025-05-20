# Development Crew Platform

## Overview

The `development_crew/` directory contains all code, infrastructure, and documentation for the Development Crew: a general-purpose, modular AI agent platform.

- **Purpose:** Build agentic applications across any domain (not limited to cybersecurity)
- **Architecture:** Orchestration, Planning, Development, Operations agent layers
- **Integrations:** MCP servers, Neo4j knowledge fabric, project management tools (Jira, Notion, Figma)

## Directory Structure
- `agents/` — Specialized agent implementations
- `infrastructure/` — Core platform infrastructure (knowledge fabric, MCP servers, orchestration)
  - `infrastructure/knowledge_fabric/` — Digital Genome Architecture implementation
  - `infrastructure/knowledge_fabric/core/` — Core components (events, schema, repository, etc.)
  - `infrastructure/knowledge_fabric/services/` — Service components (event processing, synchronization)
- `docs/` — Architecture, integration, and planning docs
- `repo-structure.md` — Detailed breakdown of the repo organization
- `requirements.txt` — Platform dependencies

## Integration with Applications
- This platform is designed to be reused for any agentic app.
- For example, the `../csec_saas/` directory contains a customizable Cybersecurity Incident Response SaaS app built using this platform.
- Application-specific code and documentation should reside outside `development_crew/` to preserve modularity.

## Key Features

- **Domain-Agnostic Architecture**: Adaptable to various industry domains beyond cybersecurity
- **Four-Layer Agent Structure**: Specialized agents for orchestration, planning, development, and operations
- **Digital Genome Architecture**: Neo4j-based system for agent memory, event tracking, and knowledge representation
- **Knowledge Graph Foundation**: Neo4j-based knowledge sharing system to maintain project context
- **MCP Server Enhancement**: Each agent equipped with dedicated tools and capabilities
- **External Tool Integration**: Seamless connections with Figma, Jira, GitHub, and other development tools

## Project Status

### Completed

1. **Foundation Setup**
   - ✅ Configured the development environment with deployment kickoff checklist
   - ✅ Set up repository structure for the Development Crew project
   - ✅ Created initial documentation and project management resources
   - ✅ Implemented environment configuration with .env file and dependency management

2. **Knowledge Fabric - Digital Genome Architecture (Phase 1)**
   - ✅ Implemented Neo4j knowledge graph with domain-agnostic schema
   - ✅ Created comprehensive event logging system connected to Neo4j
   - ✅ Built associative memory system for context-aware agent memory
   - ✅ Developed repository pattern for simplified database operations
   - ✅ Added adapter patterns for flexible component integration
   - ✅ Implemented event processor service for real-time event handling
   - ✅ Created demo application for testing and verification
   - ✅ Built support for both individual and shared knowledge graphs

## Next Steps

1. **Knowledge Fabric - Digital Genome Architecture (Phase 2)**
   - Implement advanced query capabilities for complex knowledge retrieval
   - Add vector embeddings for semantic memory search
   - Develop cognitive architecture patterns for agent reasoning
   - Implement automatic knowledge synchronization between agents

2. **Orchestration Layer Implementation**
   - Deploy Project Manager Agent to coordinate workflows
   - Implement Requirements Analyst Agent for parsing requirements
   - Configure Quality Assurance Agent for output validation

3. **Planning Layer Implementation**
   - Deploy Architecture Agent for system design
   - Configure Security Architect Agent for security considerations
   - Implement UX Designer Agent for interface specifications
   - Set up Data Architect Agent for data modeling

4. **Development Layer Implementation**
   - Create Backend and Frontend Developer Agents
   - Implement Database Engineer Agent
   - Add Framework Specialist Agent
   - Configure ML Engineer Agent

5. **Operations Layer Implementation**
   - Configure DevOps Agent for CI/CD and infrastructure
   - Implement Security Operations Agent
   - Set up Documentation and Testing Agents

6. **Integration and Testing**
   - Verify cross-agent collaboration
   - Test end-to-end workflows across domains
   - Validate output quality and system performance

## Digital Genome Demo

The project includes a demo application that demonstrates the functionality of the Digital Genome Architecture:

```bash
cd development_crew
python demo_digital_genome.py
```

This demo showcases:
- Event emission and processing
- Memory storage in Neo4j
- Associative memory retrieval by context
- Memory associations between related concepts
- (Optional) Knowledge synchronization between individual and shared graphs

## References

- Architectural Implementation Plan: See `AI Project Development Crew_ Architecture and Implementation Plan.md`
- Repository Structure: See `repo-structure.md`
- Original Approach: Based on the Emerging Cybersecurity Threat Finder methodology

## Neo4j Integration

### Environment Configuration

The Digital Genome Architecture uses Neo4j for storing events, memories, and relationships. Connection settings are configured in the `.env` file:


### Testing the Neo4j Connection

To verify your Neo4j connection:

```bash
cd development_crew
python test_connection.py
```

This will attempt to connect to Neo4j and report success or failure. If successful, it will show the Neo4j version and the number of nodes in the database.

### Verifying in Neo4j Browser

After running the demo, you can verify the created nodes directly in Neo4j Browser:

1. In Neo4j Desktop, click on "Open" next to your database
2. In the Neo4j Browser, enter these queries:

```cypher
# View all nodes (limit 100)
MATCH (n) RETURN n LIMIT 100

# View events
MATCH (e:Event) RETURN e LIMIT 25

# View memories
MATCH (m:Memory) RETURN m LIMIT 25

# View relationships
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100

# View memories by type
MATCH (m:Memory) RETURN m.memory_type, count(*) as count
```

### Troubleshooting Connection Issues

If you encounter connection problems:

1. Ensure Neo4j Desktop has a database running
2. Verify your connection details in the `.env` file match those in Neo4j Desktop
3. Check for any firewall issues blocking the connection
4. Make sure you have installed all dependencies with `pip install -r requirements.txt`