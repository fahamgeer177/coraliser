import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

# ──────────────────────────── Tools ────────────────────────────
@tool
def add(numbers: str) -> str:
    """Add two numbers provided as a string separated by space or comma."""
    try:
        parts = numbers.replace(",", " ").split()
        if len(parts) != 2:
            return "Please provide exactly two numbers."
        a, b = float(parts[0]), float(parts[1])
        return str(a + b)
    except Exception:
        return "Invalid input. Please provide two valid numbers."

@tool
def subtract(numbers: str) -> str:
    """Subtract two numbers provided as a string separated by space or comma."""
    try:
        parts = numbers.replace(",", " ").split()
        if len(parts) != 2:
            return "Please provide exactly two numbers."
        a, b = float(parts[0]), float(parts[1])
        return str(a - b)
    except Exception:
        return "Invalid input. Please provide two valid numbers."

@tool
def multiply(numbers: str) -> str:
    """Multiply two numbers provided as a string separated by space or comma."""
    try:
        parts = numbers.replace(",", " ").split()
        if len(parts) != 2:
            return "Please provide exactly two numbers."
        a, b = float(parts[0]), float(parts[1])
        return str(a * b)
    except Exception:
        return "Invalid input. Please provide two valid numbers."

@tool
def divide(numbers: str) -> str:
    """Divide two numbers provided as a string separated by space or comma."""
    try:
        parts = numbers.replace(",", " ").split()
        if len(parts) != 2:
            return "Please provide exactly two numbers."
        a, b = float(parts[0]), float(parts[1])
        if b == 0:
            return "Division by zero is not allowed."
        return str(a / b)
    except Exception:
        return "Invalid input. Please provide two valid numbers."

# ──────────────────────────── Prompt ───────────────────────────
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful math assistant that can perform addition, subtraction, multiplication, and division.
            * Greet the user and offer help with these operations for two numbers.
            * Use the appropriate tool (add, subtract, multiply, divide) based on the user's request.
            * Continue assisting until the user says 'exit' or 'done'."""
        ),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "{input}"),
    ]
)

# ──────────────────────────── Agent / Executor ─────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3,
                 api_key=os.environ["OPENAI_API_KEY"])

tools = [add, subtract, multiply, divide]

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ──────────────────────────── Run ──────────────────────────────
async def main():
    chat_history = []
    print("🤖 Math assistant started. Type 'exit' or 'done' to stop.")

    while True:
        user_input = input("\n👤 Your math query: ")
        if user_input.lower() in ["exit", "done"]:
            print("🤖 Goodbye!")
            break

        result = await executor.ainvoke({
            "input": user_input,
            "chat_history": chat_history,
            "agent_scratchpad": []
        })

        print(f"\n🤖 {result['output']}")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=result['output']))

if __name__ == "__main__":
    asyncio.run(main())