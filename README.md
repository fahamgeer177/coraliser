# Coraliser

## What is Coraliser?

Coraliser is a powerful tool that streamlines the integration of both MCP servers and standalone agents with the Coral Server. It automates the generation of Coral-compatible agents, eliminating the need for manual wiring or complex configurations.

Coraliser currently includes the following components:

**mcp-coraliser**
By simply providing a `coraliser_settings.json` file containing connection details for multiple MCP servers and executing `coraliser.py`, Coraliser automates the entire setup. It generates Coral-compatible agents that are immediately ready to operate within the Coral network.

**agent-coraliser**
By providing an input agent in .py format and executing coraliser.py, Coraliser first validates whether the file contains a valid agent. If it does, it generates a Coral-compatible version of that agent, ready to run within the Coral network.

## Why Coraliser?

Coraliser streamlines the adoption of Coral by automating the conversion of both MCP servers and standalone agents into Coral-compatible agents. Once integrated, these agents can seamlessly receive inputs from the Coral network and invoke their tools as needed. This makes your multi-agent system more efficient, scalable, and ready for production use without additional configuration.

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

## Setting Up and Running the MCP-Coraliser

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

## Setting Up and Running the MCP-Coraliser
Follow these steps to set up and run the Agent-Coraliser:

1. **Create the .env file**: Copy the .env_sample file to .env and update it with your specific environment variable values (e.g., OPENAI_API_KEY).

2. **Prepare the input agent**: Ensure you have a Python file (e.g., agent_coraliser_sample_input.py) that defines your standalone agent.

3. **Run the Coraliser**: 
   - Execute the following command to coralise the agent: 
      ```bash
      python utils/langchain/coraliser.py
      ```
   - It will ask the agent name as Input, ensure you add the agent name along with the file extension.

4. **Check the agent prompts**: Review the generated Python files to validate that the agents are configured as per your requirements.

5. **Run the agents**: To activate the agents within the Coral network (assuming your Coral Server is running), execute the generated scripts. For example:
   ```bash
   python <filename>.py
   ```

Once launched, these agents will be ready to receive and respond to queries from other agents within the Coral ecosystem.

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2025 [Coral Protocol]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

https://www.coralprotocol.org/
