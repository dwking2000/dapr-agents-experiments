# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dapr Agents is a Python framework for building production-grade agentic AI systems using the Dapr runtime. It provides a developer-friendly API for creating AI agents that can reason, act, and collaborate using LLMs, with built-in observability and stateful workflow execution.

## Key Architecture Components

### Core Package Structure (`dapr_agents/`)
- **agent/**: Base agent classes and patterns (ReAct, ToolCall, OpenAPI)
- **llm/**: LLM client abstractions supporting OpenAI, Azure OpenAI, HuggingFace, NVIDIA, ElevenLabs
- **workflow/**: Dapr workflow integration for stateful, resilient agent orchestration
- **tool/**: Tool system including MCP client, HTTP tools, and function calling utilities
- **storage/**: Persistence layer with vectorstores (Chroma, Postgres), graphstores (Neo4j), and Dapr state stores
- **memory/**: Context management and memory systems for agents
- **types/**: Shared type definitions and schemas

### Agent Patterns
- **ReActAgent**: Reasoning and Acting pattern for problem-solving
- **ToolCallAgent**: Function calling with custom tools
- **OpenAPIReActAgent**: Integration with OpenAPI specifications
- **AssistantAgent**: High-level assistant with conversation capabilities

### Workflow System
- **AgenticWorkflow**: Base workflow class for agent orchestration
- **Orchestrators**: LLM-based, Random, and RoundRobin agent selection strategies
- **WorkflowApp**: Dapr workflow runtime integration

## Development Commands

### Setup with UV
```bash
# Install with development dependencies
uv sync --extra dev --extra test

# Or install specific dependency groups
uv sync --extra test  # Test dependencies only
uv sync --extra dev   # Development dependencies only

# Install in editable mode for development
uv pip install -e ".[dev,test]"
```

### Testing
```bash
# Run all tests
uv run tox -e pytest

# Run specific test file
uv run tox -e pytest tests/test_random_orchestrator.py

# Run tests with coverage
uv run tox -e pytest --cov=dapr_agents

# Run tests directly with uv
uv run pytest tests/
```

### Code Quality
```bash
# Run linting
uv run tox -e flake8

# Run code formatting
uv run tox -e ruff

# Run type checking
uv run tox -e type

# Or run tools directly with uv
uv run ruff format
uv run mypy --config-file mypy.ini
```

### Quickstart Validation
```bash
# Validate all quickstarts (creates separate venvs)
make validate-quickstarts

# Validate quickstarts using current environment
make validate-quickstarts-local
```

## Important Patterns

### Agent Creation
Agents are typically created using factory methods or direct instantiation:
```python
from dapr_agents import Agent, ReActAgent, ToolCallAgent

# Factory method (recommended)
agent = Agent(name="my_agent", llm_client=llm_client)

# Direct pattern instantiation
react_agent = ReActAgent(name="reasoner", llm_client=llm_client)
```

### Workflow Integration
Workflows use Dapr's durable execution engine for resilience:
```python
from dapr_agents.workflow import WorkflowApp, AgenticWorkflow

app = WorkflowApp()

@app.workflow
def my_workflow(context, input_data):
    # Stateful, resilient workflow execution
    pass
```

### Tool Definition
Tools use the `@tool` decorator for function calling:
```python
from dapr_agents.tool import tool

@tool
def my_custom_tool(param: str) -> str:
    """Tool description for LLM"""
    return "result"
```

## Configuration Files

- **pyproject.toml**: Main project configuration, dependencies, and build settings
- **uv.lock**: UV lockfile for reproducible dependency resolution
- **tox.ini**: Testing and quality assurance environments
- **mypy.ini**: Type checking configuration (currently ignores most modules during development)
- **Makefile**: Quickstart validation automation

## Working with Quickstarts

The `quickstarts/` directory contains progressive examples from basic LLM calls to multi-agent workflows. Each quickstart is self-contained with its own `requirements.txt` and README. The quickstarts serve as both documentation and integration tests.

## Dapr Integration

This framework heavily leverages Dapr's building blocks:
- **Actors**: For stateful agent instances
- **Workflows**: For resilient multi-step processes
- **State Management**: For agent memory and context
- **Pub/Sub**: For agent-to-agent communication
- **Service Invocation**: For distributed agent systems

Components are configured via YAML files in `components/` directories within quickstarts and examples.

## Testing Philosophy

- Unit tests focus on core framework functionality
- Quickstarts serve as integration tests and documentation
- Tox environments ensure compatibility across Python versions
- Type checking is gradually being introduced (many modules currently ignored in mypy.ini)

## UV Package Management

This project uses UV for fast, reliable Python package management. UV provides:
- Fast dependency resolution and installation
- Reproducible builds via `uv.lock`
- Virtual environment management
- Better performance than traditional pip/virtualenv workflows