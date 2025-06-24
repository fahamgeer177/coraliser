
# Coraliser

Coraliser streamlines the adoption of Coral by automating the conversion of both MCP servers and standalone agents into Coral-compatible agents. Once integrated, these agents can seamlessly receive inputs from the Coral Server and invoke their tools as needed. This makes your multi-agent system more efficient, scalable, and ready for production use without additional configuration.

## What is Coraliser?

Coraliser is a powerful tool that streamlines the integration of both MCP servers and standalone agents with the Coral Server. It automates the generation of Coral-compatible agents, eliminating the need for manual wiring or complex configurations.

Coraliser currently includes the following components:

- **mcp-coraliser**: Run coraliser.py with a c`oraliser_settings.json` file that includes connection details for multiple MCP servers. The Coraliser attempts to connect to each MCP adaptor listed and automatically generates Coral-compatible agents for the ones that are reachable. If a connection fails for any MCP adaptor, it flags the issue and proceeds to the next available MCP, ensuring uninterrupted agent generation for all valid connections.

- **agent-coraliser**: By providing an input agent in `.py` format and executing `coraliser.py`, Coraliser first validates whether the file contains a valid agent using a Language model. If it does, it generates a Coral-compatible version of that agent, ready to run within the Coral Server.

## Get Started

### 1. Clone & Install Dependencies
<details>

```bash
# Clone the Repository
git clone https://github.com/Coral-Protocol/Coraliser.git

# Navigate to the Project Directory
cd Coraliser

# Install uv
pip install uv

# Sync dependencies from pyproject.toml
uv sync
```
</details>

### 2. Configure Environment Variables
<details>

```bash
# Create .env file in project root
cp -r .env_sample .env
```
</details> 

### 3. Setting Up and Running the MCP-Coraliser
<details>

1. **Update `coraliser_settings.json`**:  
   Provide the connection details for your MCP server(s).

2. **Run the MCP Coraliser**:

```bash
   uv run utils/langchain/mcp-coraliser/coraliser.py
```

This script validates connections and generates Coral-compatible agent scripts.

4. **Review the Generated Agents**:  
   Check files like `firecrawl_coral_agent.py`, `github_coral_agent.py` to confirm they are configured correctly.

5. **Run the Agents** (assuming your Coral Server is running):

```bash
   uv run firecrawl_coral_agent.py
```

```bash
   uv run github_coral_agent.py
```
</details> 

### 4. Setting Up and Running the Agent-Coraliser
<details>

1. **Prepare the Input Agent**:  
   Ensure you have a valid agent Python file (e.g., `agent_coraliser_sample_input.py`).

2. **Run the Agent Coraliser**:

```bash
   uv run utils/langchain/agent-coraliser/coraliser.py
```

   (You’ll be prompted to enter the agent file name (including `.py` extension).)

3. **Review the Generated Agent File**:  
   Confirm the generated script matches your expectations.

4. **Run the Agent**:

```bash
uv run <generated_filename>.py
```
</details>

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2025 Coral Protocol

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

For more information, visit:  
https://www.coralprotocol.org/
