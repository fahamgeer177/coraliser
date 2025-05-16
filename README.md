
# Coraliser

## What is Coraliser?

Coraliser is a powerful tool that streamlines the integration of any MCP server with the Coral Server. By simply providing a `coraliser_settings.json` file containing connection details for multiple MCP servers and executing `coraliser.py`, Coraliser automates the entire setup. It generates Coral-compatible agents that are immediately ready to operate within the Coral network, eliminating the need for manual wiring or complex configurations.

In this demo, we are **coralising the Firecrawl and GitHub MCPs**, enabling them to operate as Coral agents.

## Why Coraliser?

Coraliser streamlines the adoption of Coral in MCP-based projects. Once connected, your MCP agent can receive inputs from the Coral network and invoke its tools as needed. This makes your multi-agent system more efficient, scalable, and ready for production use without additional configuration.

## Prerequisites

- Python 3.12.10
- Access to an OpenAI API key (set as `OPENAI_API_KEY` in your environment variables)
- Access to a Firecrawl API key (set as `FIRECRAWL_API_KEY` in your environment variables)
- Access to a GitHub PAT key (set as `GITHUB_PERSONAL_ACCESS_TOKEN` in your environment variables)
- Setup other required environment variables like: `llm_model_provider`, `llm_model_name` and the `coral_base_url` which in this case is 'http://localhost:5555/devmode/exampleApplication/privkey/session1/sse'
- Node.js and npm installed (for running the Firecrawl MCP)
- Basic familiarity with terminal commands and Python virtual environments

## Setting Up and Running the Coraliser

### 1. Set Up the Virtual Environment

Create and activate a Python virtual environment to isolate dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### 2. Install Dependencies

Install the required Python packages for the Coraliser:

```bash
pip install pydantic
pip install langchain_openai
pip install langchain_mcp_adapters
```

### 3. Run Coraliser

```bash
python utils/langchain/coraliser.py
```

Running Coraliser will validate connections to all MCP servers specified in the `coraliser_settings.json` file. If the connections are successful, it will generate agent scripts, each tailored to integrate with the Coral Server.

In this case, a successful run will produce two py files, `firecrawl_coral_agent.py` and `github_coral_agent.py`. To activate these agents within the Coral network (assuming your Coral Server is running), simply execute the generated scripts.

```bash
python firecrawl_coral_agent.py
```

```bash
python github_coral_agent.py
```

Once launched, these agents will be ready to receive and respond to queries from other agents within the Coral ecosystem.
