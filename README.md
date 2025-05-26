# Coraliser

## What is Coraliser?

Coraliser is a powerful tool that streamlines the integration of any MCP server with the Coral Server. By simply providing a `coraliser_settings.json` file containing connection details for multiple MCP servers and executing `coraliser.py`, Coraliser automates the entire setup. It generates Coral-compatible agents that are immediately ready to operate within the Coral network, eliminating the need for manual wiring or complex configurations.

In this repo, we are **coralising the Firecrawl and GitHub MCPs**, enabling them to operate as Coral agents. You can follow these instructions to coralise any MCP server by updating the `coraliser_settings.json` with the appropriate connection details for your desired MCP.

## Why Coraliser?

Coraliser streamlines the adoption of Coral in MCP-based projects. Once connected, your MCP agent can receive inputs from the Coral network and invoke its tools as needed. This makes your multi-agent system more efficient, scalable, and ready for production use without additional configuration.

## Prerequisites

### General Coraliser Prerequisites
- Python 3.12.10
- Setup required environment variables like: `llm_model_provider`, `llm_model_name`, and `coral_base_url` (e.g., 'http://localhost:5555/devmode/exampleApplication/privkey/session1/sse')
- Basic familiarity with terminal commands and Python virtual environments

### Repo-Specific Prerequisites (Firecrawl and GitHub MCPs)
- Access to an OpenAI API key (set as `OPENAI_API_KEY` in your environment variables)
- Access to a Firecrawl API key (set as `FIRECRAWL_API_KEY` in your environment variables)
- Access to a GitHub PAT key (set as `GITHUB_PERSONAL_ACCESS_TOKEN` in your environment variables)
- Node.js and npm installed (for running the Firecrawl MCP)

## Setting Up and Running the Coraliser

Follow these steps to set up and run the Coraliser:

1. **Create the .env file**: Copy the `.env_sample` file to `.env` and update it with your specific environment variable values (e.g., `OPENAI_API_KEY`, `FIRECRAWL_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `llm_model_provider`, `llm_model_name`, and `coral_base_url`).

2. **Update the coraliser_settings.json**: Modify the `coraliser_settings.json` file to include the connection details for your MCP server(s).

3. **Run the Coraliser**: Execute the following command to create the coralised agents:
   ```bash
   python utils/langchain/coraliser.py
   ```
   This will validate connections to all MCP servers specified in the `coraliser_settings.json` file and generate agent scripts tailored to integrate with the Coral Server.

4. **Check the agent prompts**: Review the generated Python files (e.g., `firecrawl_coral_agent.py` and `github_coral_agent.py`) to validate that the agents are configured as per your requirements.

5. **Run the agents**: To activate the agents within the Coral network (assuming your Coral Server is running), execute the generated scripts. For example:
   ```bash
   python firecrawl_coral_agent.py
   ```
   ```bash
   python github_coral_agent.py
   ```

Once launched, these agents will be ready to receive and respond to queries from other agents within the Coral ecosystem.