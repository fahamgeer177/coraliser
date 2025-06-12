import os
import json
from typing import List
from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain.memory import ConversationSummaryMemory
from langchain_core.memory import BaseMemory
from langchain_core.messages import HumanMessage, AIMessage
import subprocess
import re
import requests
from typing import Optional

# --------- URL 2 repo, file_name, and file_content ---------
def extract_repo_branch_filename_content(github_url):
    """
    Given a GitHub file URL, return (repository name, branch name, file name, file content).
    Supports the format owner/repo.
    """
    # Extract repo, branch, and file path
    pattern = r"github\.com/([^/]+/[^/]+)/blob/([^/]+)/(.*)"
    match = re.search(pattern, github_url)
    if not match:
        raise ValueError("Invalid URL format or not a valid GitHub file link.")
    repo = match.group(1)
    branch = match.group(2)
    file_path = match.group(3)
    file_name = file_path.split('/')[-1]

    # Construct the raw content URL
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"

    # Request the file content
    response = requests.get(raw_url)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch file content: {response.status_code} {raw_url}")
    content = response.text

    return repo, branch, file_name, content

# --------- Tool Functions and Classes ---------
def get_tools_description(tools):
    # Returns a string description of available tools and their argument schemas
    return "\n".join(
        f"Tool: {t.name}, Schema: {json.dumps(t.args).replace('{', '{{').replace('}', '}}')}"
        for t in tools
    )

@tool
def save_content_to_file_tool(content: str, file_ext: str = ".txt", filename: Optional[str] = None) -> str:
    """
    Save the given content to a new file with the specified file extension.

    Args:
        content (str): The content to be saved.
        file_ext (str): File extension, e.g. '.py', '.md', default is '.txt'.
        filename (str, optional): The filename without extension. If not provided, use 'output_<timestamp>'.

    Returns:
        str: Absolute path of the saved file or error message.
    """
    import time

    # Ensure the file_ext starts with a dot
    if not file_ext.startswith("."):
        file_ext = "." + file_ext

    # Generate filename if not provided
    if filename is None:
        filename = f"output_{int(time.time())}"
    file_name = filename + file_ext

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)
        return os.path.abspath(file_name)
    except Exception as e:
        return f"Error saving file: {e}"

@tool
def get_all_github_files(repo_name: str, branch: str = "main") -> List[str]:
    """
    Recursively retrieve all file paths from a specific branch of a GitHub repository.

    Args:
        repo_name (str): Full repository name in the format "owner/repo".
        branch (str): Branch name to retrieve files from. Defaults to "main".

    Returns:
        List[str]: A list of all file paths in the specified branch of the repository.

    Raises:
        ValueError: If GITHUB_ACCESS_TOKEN is not set.
        GithubException: On repository access or API failure.
    """
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITHUB_ACCESS_TOKEN environment variable is not set.")

    gh = Github(token)

    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        raise GithubException(f"Failed to access repository '{repo_name}': {e.data}")

    def get_all_file_paths(path: str = "") -> List[str]:
        files: List[str] = []
        try:
            contents = repo.get_contents(path, ref=branch)
        except GithubException as e:
            raise GithubException(f"Failed to get contents of path '{path}' in branch '{branch}': {e.data}")

        if isinstance(contents, ContentFile):
            files.append(contents.path)
        else:
            for content in contents:
                if content.type == "dir":
                    files.extend(get_all_file_paths(content.path))
                else:
                    files.append(content.path)
        return files

    return get_all_file_paths()


@tool
def retrieve_github_file_content_tool(repo_name: str, file_path: str, branch: str = "main") -> str:
    """
    Call the local retrieve_github_file_content.py script and return the file content or error.

    Args:
        repo_name (str): Full repository name in the format "owner/repo".
        file_path (str): Path to the file in the repository.
        branch (str): Branch name to retrieve the file from.

    Returns:
        str: Script output (file content or error message).
    """
    # Get the absolute path of the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    script_path = os.path.join(current_dir, "retrieve_github_file_content.py")

    result = subprocess.run(
        [
            "python",
            script_path,
            "--repo_name", repo_name,
            "--file_path", file_path,
            "--branch", branch
        ],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout
    else:
        return f"exit_code={result.returncode}\nstderr={result.stderr}"

class HeadSummaryMemory(BaseMemory):
    def __init__(self, llm, head_n=3):
        super().__init__()
        self.head_n = head_n
        self._messages = []
        self.summary_memory = ConversationSummaryMemory(llm=llm)

    def save_context(self, inputs, outputs):
        user_msg = inputs.get("input") or next(iter(inputs.values()), "")
        ai_msg = outputs.get("output") or next(iter(outputs.values()), "")
        self._messages.append({"input": user_msg, "output": ai_msg})
        if len(self._messages) > self.head_n:
            self.summary_memory.save_context(inputs, outputs)

    def load_memory_variables(self, inputs):
        messages = []
        
        for i in range(min(self._head_n, len(self._messages))):
            msg = self._messages[i]
            messages.append(HumanMessage(content=msg['input']))
            messages.append(AIMessage(content=msg['output']))
        # summary
        if len(self._messages) > self._head_n:
            summary_var = self.summary_memory.load_memory_variables(inputs).get("history", [])
            if summary_var:
                
                if isinstance(summary_var, str):
                    messages.append(HumanMessage(content="[Earlier Summary]\n" + summary_var))
                elif isinstance(summary_var, list):
                    messages.extend(summary_var)
        return {"history": messages}

    def clear(self):
        self._messages.clear()
        self.summary_memory.clear()

    @property
    def memory_variables(self):
        return {"history"}
    
    @property
    def head_n(self):
        return self._head_n

    @head_n.setter
    def head_n(self, value):
        self._head_n = value

    @property
    def summary_memory(self):
        return self._summary_memory

    @summary_memory.setter
    def summary_memory(self, value):
        self._summary_memory = value

# ---------- Agent/Prompt Main Workflow ----------
def create_repo_understanding_agent(tools):
    """
    Create a synchronous agent for GitHub repository understanding.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a GitHub repository analysis agent. Your job is to analyze any given GitHub repository and answer user's question using the provided tools.

        No matter what user's requierement is, you need to do these two things first:
         
        1. Use `get_all_github_files` to list all files in the target repo and branch.
        2. Go through all files that help you understand this repo using `retrieve_github_file_content_tool`.
         
        Then answer user's question also using the provided tools.
    

        Tools: {get_tools_description(tools)}
        """),
        ("user", "{input}"),
        ("placeholder", "{history}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    model = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=16384
    )
    memory = HeadSummaryMemory(llm=model, head_n=4)
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, max_iterations=30, verbose=True)

def create_file_saving_agent(tools):
    """
    Create a synchronous agent for GitHub repository understanding.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a file saving agent. Your job is to save the given content into specific format using provided tools.
    

        Tools: {get_tools_description(tools)}
        """),
        ("user", "{input}"),
        ("placeholder", "{history}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    model = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=16384
    )
    memory = HeadSummaryMemory(llm=model, head_n=4)
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, max_iterations=30, verbose=True)

def main():
    url = "https://github.com/livekit/agents/blob/main/examples/voice_agents/restaurant_agent.py"
    repo, branch, filename, content = extract_repo_branch_filename_content(url)

    # Main synchronous entry point for repository analysis
    github_token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_ACCESS_TOKEN environment variable is required")

    # Prepare the tool list for the agent
    tools_repo = [get_all_github_files, retrieve_github_file_content_tool]
    agent_executor_repo = create_repo_understanding_agent(tools_repo)

    tools_file = [save_content_to_file_tool]
    agent_executor_file = create_file_saving_agent(tools_file)

    result = agent_executor_repo.invoke({
        "input": f"""
        First, fully go through files in the repo {repo} repo on {branch} branch, to fully understand this repo first (inlcuding docs),
        
        Second,read {filename} and its related file, and make these two modifications:**

            1. Locate a place to replace the agent's prompt as "You are the central interface agent that connects users with specialized agents to fulfill their queries.

            Your workflow:
            1. List available agents using `list_agents` to understand capabilities
            2. Analyze user queries and select the most appropriate agent
            3. For Coral Server information requests, handle directly using available tools
            4. For other requests: create a thread with `create_thread`, send clear instructions via `send_message`, and wait for responses with `wait_for_mentions`
            5. Present agent responses back to the user in a helpful format
            6. Continue assisting with follow-up queries

            Always act as the central coordinator - you receive user requests, delegate to specialist agents when needed, and deliver comprehensive responses back to users."

            2. Locate a the place to add Coral server MCP connection

            ```
            base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
            params = {{
                "waitForAgents": 1,
                "agentId": "voice_assistant",
                "agentDescription": "You are a helpful voice AI assistant."
            }}
            query_string = urllib.parse.urlencode(params)
            MCP_SERVER_URL = f"{{base_url}}?{{query_string}}"
        ```

        Thrid, your output should include into 2 part, **an completed and workable modified file, nothing should be omitted, summarized, or left for the user to fill in. The result must be ready to use as-is.**, and **a readme including dependencies installation, API configuration, and Running command (for the modified agent file's name, you don't need to mention its path).**
    """
    })

    print(result["output"])
    result = result["output"]

    print("Files are saving...")

    agent_executor_file.invoke({
        "input": f"""
        For this file {result}
        Retrieve the entire python and save it as .py file, for naming, you should look at the command from the readme.
        Retrieve the readme and save it as Generated_README.md.
    """
    })

    print("Files are saved!")

if __name__ == "__main__":
    main()
