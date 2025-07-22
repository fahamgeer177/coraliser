import asyncio
import traceback, json, copy, os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

class AgentGenerator:

    def __init__(self, agent_name, mcp_json):
        self.agent_name = agent_name
        self.mcp_json = mcp_json
        self.client = None
    
    def get_tools_description(self):
        tools = self.client.get_tools()
        return "\n".join(
            f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
            for tool in tools
        )
    
    def get_agent_config(self):
        return copy.deepcopy(self.mcp_json[self.agent_name])
    
    def get_mcp_description(self):
        print('Creating MCP description for coral')
        formatted_tools = self.get_tools_description()
        system_prompt = (
            "You are an AI system tasked with summarizing the purpose and capabilities of an agent, "
            "based solely on the tools it has access to. "
            "Below is a list of tools available to the agent:\n"
            f"{formatted_tools}\n\n"
            "Using this information, write a concise 1-2 sentence description of what this agent is capable of doing. "
            "Focus on the agent's core functionality as inferred from the tools. "
            "Your response must be a valid JSON object in the following format:\n"
            f"The description must always start with `{self.agent_name} agent capable of...`"
            "{\"description\": \"<insert your concise summary here>\"}"
        )

        llm_helper = init_chat_model(
            model=os.getenv("MODEL_NAME", "gpt-4.1-mini"),
            model_provider=os.getenv("MODEL_PROVIDER", "openai"),
            api_key=os.getenv("API_KEY"),
            temperature=os.getenv("MODEL_TEMPERATURE", "0.1"),
            max_tokens=os.getenv("MODEL_TOKEN", "8000"),
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        response = llm_helper.invoke(system_prompt)
        response = response.content
        description = json.loads(response)["description"]
        print(f"Generated description: {description}")

        return description

    def get_env_or_raise(self, key):
        val = os.getenv(key)
        if not val:
            raise EnvironmentError(f'Missing required environment variable: {key}')
        return val

    async def check_connection(self):
        try:
            mcp_object = self.get_agent_config()
            if "env" in mcp_object:
                mcp_object['env'] = {key: self.get_env_or_raise(key) for key in mcp_object['env']}
            print(f"Checking connection with the MCP: {self.agent_name}")
            async with MultiServerMCPClient(connections={self.agent_name: mcp_object}) as client:
                self.client = client
                session = self.client.sessions
                return True
        except Exception as e:
            print(f"Failed to establish connection: {e}")
            print(traceback.format_exc())
            return False    
    
    def create_agent(self, agent_description):
        items = []
        env_code_str = None
        mcp_object = self.get_agent_config()

        for key, val in mcp_object.items():
            if key == "env":
                env_code_str = "{" + ", ".join(
                    f'"{k}": os.getenv("{k}")' for k in val
                ) + "}"
                val_str = env_code_str
            else:
                val_str = repr(val)
            items.append(f'"{key}": {val_str}')

        mcp_dict_code = f'"{self.agent_name}": {{' + ", ".join(items) + "}"

        base_dir = os.path.dirname(__file__)
        coraliser_path = os.path.join(base_dir, 'base_coraliser.py')
        with open(coraliser_path, 'r') as py_file:
                base_code = py_file.read()
        
        base_code = base_code.replace('"agentId": "",', f'"agentId": agentID,')
        base_code = base_code.replace('"agentDescription": ""', f'"agentDescription": "{agent_description}"')
        base_code = base_code.replace('"mcp": ""', mcp_dict_code)
        base_code = base_code.replace("agent_tools = await client.get_tools(server_name='mcp')",
                                      f"agent_tools = await client.get_tools(server_name='{self.agent_name}')")

        # Create the directory agent/<agent_name> if it doesn't exist
        output_dir = os.path.join("coralised_agents", self.agent_name.lower())
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"main.py")
        
        with open(filename, "w") as f:
            f.write(base_code)
        print(f"File '{filename}' created successfully.")

        # Create the .env file with specified keys
        env_filename = os.path.join(output_dir, ".env_sample")
        env_vars = {}
        
        # Add environment variables from mcp_object["env"] if it exists
        if "env" in mcp_object:
            for key in mcp_object["env"]:
                env_vars[key] = ""
        
        # Add hardcoded environment variables
        env_vars.update({
            "MODEL_NAME": "gpt-4.1-mini",
            "MODEL_PROVIDER": "openai",
            "MODEL_TOKEN": "16000",
            "MODEL_TEMPERATURE": "0.0",
            "API_KEY": "",
            "CORAL_AGENT_ID": self.agent_name.lower(),
            "CORAL_SSE_URL": "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
        })

        # Format environment variables for .env file
        env_content = "\n".join(
            f"{key}={value}" for key, value in env_vars.items()
        )
        with open(env_filename, "w") as f:
            f.write(env_content)
        print(f"File '{env_filename}' created successfully.")

         # Create the pyproject.toml file
        pyproject_filename = os.path.join(output_dir, "pyproject.toml")
        pyproject_content = f"""[project]
name = "{self.agent_name.lower()}"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "langchain==0.3.25",
    "langchain-community==0.3.24",
    "langchain-experimental==0.3.4",
    "langchain-groq==0.3.4",
    "langchain-mcp-adapters==0.1.7",
    "langchain-openai==0.3.26",
    "pandas==2.3.0",
    "tabulate>=0.9.0",
    "uv>=0.7.17",
]
"""
        with open(pyproject_filename, "w") as f:
            f.write(pyproject_content)
        print(f"File '{pyproject_filename}' created successfully.")

        # Create the run_agent.sh file
        run_agent_filename = os.path.join(output_dir, "run_agent.sh")
        run_agent_content = """#!/bin/bash

# Check for exactly one argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <python_script_path>" >&2
  exit 1
fi
PYTHON_SCRIPT="$1"

# Determine script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")

# Ensure write permissions for script directory
chmod u+w "$SCRIPT_DIR" || {
  echo "Error: Could not set write permissions for $SCRIPT_DIR" >&2
  exit 1
}

PROJECT_DIR="$SCRIPT_DIR"
echo "Project directory: $PROJECT_DIR"
echo "Python script to run: $PYTHON_SCRIPT"

# Change to project directory
cd "$PROJECT_DIR" || {
  echo "Error: Could not change to directory $PROJECT_DIR" >&2
  exit 1
}

# Set and activate virtual environment
echo "Activating virtual environment..."
VENV_ACTIVATE="$([[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]] && echo "$PROJECT_DIR/.venv/Scripts/activate" || echo "$PROJECT_DIR/.venv/bin/activate")"
[ ! -f "$VENV_ACTIVATE" ] && { echo "Error: Virtual environment activation script $VENV_ACTIVATE not found" >&2; exit 1; }
source "$VENV_ACTIVATE" || { echo "Error: Failed to activate virtual environment" >&2; exit 1; }
 
# Run Python script
echo "Running $PYTHON_SCRIPT..."
uv run "$PYTHON_SCRIPT" || { echo "Error: Failed to run $PYTHON_SCRIPT" >&2; exit 1; }
"""
        with open(run_agent_filename, "w") as f:
            f.write(run_agent_content)
        # Set executable permissions for the shell script
        os.chmod(run_agent_filename, 0o755)
        print(f"File '{run_agent_filename}' created successfully.")

async def main():
    with open(r'coraliser_settings.json', 'r') as f:
        config = f.read()
    
    mcp_json = json.loads(config)
    agent_list = list(mcp_json['mcpServers'].keys())
    print(f"List of available agents: {agent_list}")
    mcp_json = mcp_json['mcpServers']
    
    for agent_name in agent_list:
        try:
            agent_generator = AgentGenerator(agent_name, mcp_json)
            if await agent_generator.check_connection():
                description = agent_generator.get_mcp_description()
                agent_generator.create_agent(description)
        except Exception as e:
            print(f"Failed creating coralised agent: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())