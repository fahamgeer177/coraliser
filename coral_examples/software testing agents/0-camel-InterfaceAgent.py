import asyncio
import os
import json
from camel.toolkits.mcp_toolkit import MCPClient
from camel.toolkits import HumanToolkit, MCPToolkit 
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.agents import ChatAgent
import urllib.parse

async def get_tools_description(tools):
    descriptions = []
    for tool in tools:
        tool_name = getattr(tool.func, '__name__', 'unknown_tool')
        schema = tool.get_openai_function_schema() or {}
        arg_names = list(schema.get('parameters', {}).get('properties', {}).keys()) if schema else []
        description = tool.get_function_description() or 'No description'
        schema_str = json.dumps(schema, default=str).replace('{', '{{').replace('}', '}}')
        descriptions.append(
            f"Tool: {tool_name}, Args: {arg_names}, Description: {description}, Schema: {schema_str}"
        )
    return "\n".join(descriptions)

async def main():
    # Connect to Coral Server
    base_url_1 = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
    params_1 = {
        "waitForAgents": 1,
        "agentId": "user_interface_agent",
        "agentDescription": "You are user_interaction_agent, responsible for engaging with users, processing instructions, and coordinating with other agents"
    }
    query_string = urllib.parse.urlencode(params_1)
    MCP_SERVER_URL_1 = f"{base_url_1}?{query_string}"

    coral_server = MCPClient(
        command_or_url=MCP_SERVER_URL_1,
        timeout=300.0
    )

    await coral_server.__aenter__()
    try:
        print(f"Connected to MCP server as user_interface_agent at {MCP_SERVER_URL_1}")

        # Initialize ChatAgent
        mcp_toolkit = MCPToolkit([coral_server])
        tools = mcp_toolkit.get_tools()
        tools_description = await get_tools_description(tools)

        sys_msg = (
            f"""You are user_interaction_agent, handling user instructions and coordinating testing tasks across agents.

            **Initialization**:
            1. Call list_agents (includeDetails: True) to check registration of 'user_interaction_agent'.  
            If not registered, call:  
            register_agent(agentId: 'user_interaction_agent', agentName: 'User Interaction Agent', description: 'Handles user instructions and coordinates testing tasks.')  
            Retry once on failure. If it fails again, send a message to the thread: 'Error checking agent registration.'

            2. Create a thread using create_thread (threadName: 'User Interaction Thread', creatorId: 'user_interaction_agent', participantIds: ['user_interaction_agent']).  
            Store threadId. Retry once on failure. If it fails again, stop and report: 'Error creating thread.'

            3. Send message: 'I am ready to receive testing instructions.' Retry once. If failed again, send: 'Error sending readiness message.'

            ---

            **Loop (STRICTLY follow each step, NEVER skip any step)**:

            1. Use ask_human to ask:  
            'Please tell me the GitHub repo (e.g., owner/repo) and the PR number to test.'

            2. After receiving the human reply, extract:
            - `repo_name` (e.g., 'octocat/calculator')
            - `pr_number` (e.g., 42)

            3. Check and add the following agents if needed:
            - 'gitclone_agent' → call add_participant. On failure, send: 'Error adding Git Clone Agent.'
            - 'codediff_review_agent' → call add_participant. On failure, send: 'Error adding Code Diff Review Agent.'
            - 'unit_test_runner_agent' → call add_participant. On failure, send: 'Error adding Unit Test Runner Agent.'

            4. Send message to `gitclone_agent`:  
            "Checkout PR #[pr_number] from '[repo_name]'".  
            Use send_message (senderId: 'user_interaction_agent', mentions: ['gitclone_agent']).

            5. KEEP calling wait_for_mentions (agentId: 'user_interaction_agent', timeoutMs: 30000) until messages are received.  
            - If no messages after 3 attempts, send: 'No response from gitclone_agent.'  
            - Extract the `Local path: [repo_path]` from the response. Store as `project_root`.

            6. Send message to `codediff_review_agent`:  
            "Analyze PR #[pr_number] from '[repo_name]'".  
            Use send_message (senderId: 'user_interaction_agent', mentions: ['codediff_review_agent']).

            7. KEEP calling wait_for_mentions (agentId: 'user_interaction_agent', timeoutMs: 30000) until messages are received.  
            - If no messages after 3 attempts, send: 'No response from codediff_review_agent.'  
            - Extract a list of (filename, patch snippet) pairs, e.g.:
                ```
                File: calculator.py
                +def multiply(x, y): return x * y

                File: utils/math.py
                +def square(x): return x ** 2
                ```

            8. Send message to `unit_test_runner_agent`:  
            "Please run relevant tests for the following code diffs under project root '[project_root]':

            File: [filename_1]
            [patch_1]

            File: [filename_2]
            [patch_2]
            "  
            Use send_message (senderId: 'user_interaction_agent', mentions: ['unit_test_runner_agent']).

            9. KEEP calling wait_for_mentions (agentId: 'user_interaction_agent', timeoutMs: 30000) until messages are received.  
            - If no messages after 3 attempts, send: 'No response from unit_test_runner_agent.'  
            - Extract full structured test report:
                - Which test functions were run, their pass/fail status and outputs;
                - Which test functions were skipped and not covered.

            10. Format the result using this structure:
            ````

            Test results summary:

            * File: \[test\_file\_1]
            ✔ Run: test\_func\_1 → PASSED
            Output:
            \[pytest stdout]

            ✘ Skipped: test\_func\_2, test\_func\_3 (Not triggered by current code changes)

            * File: \[test\_file\_2]
            ✔ Run: test\_func\_x → FAILED
            Output:
            \[pytest stdout]

            ```

            11. Send the result to the thread using send_message (content: [formatted results], mentions: []).  
            Retry once. If it fails again, send: 'Error sending test results.'

            12. Send a confirmation message using send_message (content: 'Task completed.', mentions: []).  
            Retry once. If it fails again, send: 'Error sending task completion message.'

            13. Return to step 1.

            ---

            **For any other instruction**:
            - If message is 'list agents' or similar, call list_agents and report results.
            - If message is 'close thread', close the current thread and re-create a new one. Continue interaction in the new thread.
            - If input is empty or invalid, reply: 'No valid instructions received.'

            ---

            **Notes**:
            - Cache agent list after list_agents and reuse across loop iterations.
            - Track threadId persistently.
            Use only listed tools: {tools_description}"""
        )

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4_1,
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.3, "max_tokens": 16000},
        )

        camel_agent = ChatAgent(
            system_message=sys_msg,
            model=model,
            tools=tools,
        )
        print("ChatAgent initialized successfully!")

        # Get agent reply
        prompt = "As the user_interaction_agent on the Coral Server, initiate your workflow by listing all connected agents and asking the user how you can assist them."
        response = await camel_agent.astep(prompt)
        print("Agent Reply:")
        print(response.msgs[0].content)

    finally:
        await coral_server.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())