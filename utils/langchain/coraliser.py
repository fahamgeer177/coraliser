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
            f"The description must always start with `I am an {self.agent_name} agent capable of...`"
            "{\"description\": \"<insert your concise summary here>\"}"
        )

        llm_helper = init_chat_model(
            model=os.getenv('llm_model_name'),
            model_provider=os.getenv('llm_model_provider'),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,
            max_tokens=16000,
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
        
        base_code = base_code.replace('"agentId": "",', f'"agentId": "{self.agent_name}",')
        base_code = base_code.replace('"agentDescription": ""', f'"agentDescription": "{agent_description}"')
        base_code = base_code.replace('"mcp": ""', mcp_dict_code)
        base_code = base_code.replace("agent_tools = multi_connection_client.server_name_to_tools['mcp']",
                                      f"agent_tools = multi_connection_client.server_name_to_tools['{self.agent_name}']")

        filename = f"{self.agent_name.lower()}_coral_agent.py"
        
        with open(filename, "w") as f:
            f.write(base_code)
        print(f"File '{filename}' created successfully.")



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
