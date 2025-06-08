import asyncio
import os
import json
import logging
from typing import List
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from dotenv import load_dotenv
from anyio import ClosedResourceError
import urllib.parse


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
params = {
    "waitForAgents": 1,
    "agentId": "livekit_agent",
    "agentDescription": "I am a livekit_agent agent capable of initializing a voice AI assistant session using LiveKit and OpenAI's real-time model to provide real-time interaction with users, including greeting them and offering assistance, with enhanced noise cancellation features."
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

def get_tools_description(tools):
    return "\n".join(f"Tool: {t.name}, Schema: {json.dumps(t.args).replace('{', '{{').replace('}', '}}')}" for t in tools)
    

@tool
def livekit_toolkit() -> None:
    """
    LiveKit Toolkit: A voice AI assistant using LiveKit and OpenAI for real-time interaction.

    This toolkit initializes a voice AI assistant session using LiveKit and OpenAI's real-time model.
    It sets up noise cancellation and connects to a room, allowing the assistant to greet users and offer assistance.

    Args:
        ctx (agents.JobContext): The job context containing room information for the session.

    Returns:
        None

    Raises:
        Exception: If there is an error during session start or reply generation.
    """
    # === Begin original logic, fully adapted ===
    from dotenv import load_dotenv
    from livekit import agents
    from livekit.agents import AgentSession, Agent, RoomInputOptions
    from livekit.plugins import (
        openai,
        noise_cancellation,
    )

    load_dotenv()

    class Assistant(Agent):
        def __init__(self) -> None:
            super().__init__(instructions="You are a helpful voice AI assistant.")

    async def entrypoint(ctx: agents.JobContext):
        session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                voice="coral"
            )
        )

        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                # LiveKit Cloud enhanced noise cancellation
                # - If self-hosting, omit this parameter
                # - For telephony applications, use `BVCTelephony` for best results
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        await ctx.connect()

        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )

    import sys

    if __name__ == "__main__":
        sys.argv = [sys.argv[0], "console"]
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    # === End original logic ===
    return None


async def create_agent(client, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an agent interacting with the tools from Coral Server and having your own tools. Your task is to perform any instructions coming from any agent. 
        
        **Never end up the chain**  

        Follow these steps in order:
        1. Call wait_for_mentions from coral tools (timeoutMs: 30000) to receive mentions from other agents.
        2. When you receive a mention, keep the thread ID and the sender ID.
        3. Take 2 seconds to think about the content (instruction) of the message and check only from the list of your tools available for you to action.
        4. Check the tool schema and make a plan in steps for the task you want to perform.
        5. Only call the tools you need to perform for each step of the plan to complete the instruction in the content.
        6. Take 3 seconds and think about the content and see if you have executed the instruction to the best of your ability and the tools. Make this your response as "answer".
        7. Use `send_message(senderId=..., mentions=[senderId], threadId=..., content=...)` to reply to the sender with your analysis.
        8. If any error occurs, use `send_message` to send a message in the same thread ID to the sender Id you received the mention from, with content: "error".
        9. Always respond back to the sender agent even if you have no answer or error.
        9. Wait for 2 seconds and repeat the process from step 1.
         
        **Never end up the chain** 
        
        Tools: {get_tools_description(tools)}"""),
        ("placeholder", "{history}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    model = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=32768
    )


    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, max_iterations=100 ,verbose=True)

async def main():
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            async with MultiServerMCPClient(
                connections = {
                    "coral": {
                        "transport": "sse", 
                        "url": MCP_SERVER_URL, 
                        "timeout": 600, 
                        "sse_read_timeout": 600
                    }
                }
            ) as client:
                logger.info(f"Connected to MCP server at {MCP_SERVER_URL}")
                coral_tool_names = [
                    "list_agents",
                    "create_thread",
                    "add_participant",
                    "remove_participant",
                    "close_thread",
                    "send_message",
                    "wait_for_mentions",
                ]

                tools = client.get_tools()

                tools = [
                    tool for tool in tools
                    if tool.name in coral_tool_names
                ]

                tools += [livekit_toolkit]

                logger.info(f"Tools Description:\n{get_tools_description(tools)}")

                agent_executor = await create_agent(client, tools)
                await agent_executor.ainvoke({})
            
        except ClosedResourceError as e:
            logger.error(f"ClosedResourceError on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                raise
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                raise

if __name__ == "__main__":
    asyncio.run(main())
