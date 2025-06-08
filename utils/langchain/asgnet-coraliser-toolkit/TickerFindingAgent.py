import os
from dotenv import load_dotenv

from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun, tool

@tool
def search_ticker(company_name: str) -> str:
    """
    Searches for the stock ticker symbol of a given company using DuckDuckGo.
    It parses search results specifically checking for entries from MarketWatch.
    """
    search = DuckDuckGoSearchRun()
    search_results = search.run(company_name)
    # Assue search_results is string instead of list
    return search_results

load_dotenv()

llm = ChatOpenAI(temperature=0.0)
tools = [search_ticker]  # can used load_tool since 'search_ticker' is not the pre-defined tool in langchain
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
output = agent.run("what is the stock ticker of apple?")
print(output)
