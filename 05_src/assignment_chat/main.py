from langgraph.graph import StateGraph, MessagesState, START
from langchain.chat_models import init_chat_model
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage,  HumanMessage

from dotenv import load_dotenv

load_dotenv("../../05_src/.secrets")

import json
import requests
import os

from prompts import return_instructions
from tools_sports import get_nhl_team_facts
from tools_bbcnews import handle_semantic_search
from tools_websearch import handle_web_search

#from course_chat.tools_music import recommend_albums

#from utils.logger import get_logger


#_logs = get_logger(__name__)

#load_dotenv(".env")

load_dotenv("../../05_src/.secrets")


chat_agent = init_chat_model(
    "openai:gpt-4o-mini",
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_key="any-value",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY", "")},
)

tools = [get_nhl_team_facts, handle_semantic_search, handle_web_search]

instructions = return_instructions()


# @traceable(run_type="llm")
def call_model(state: MessagesState):
    """LLM decides whether to call a tool or respond directly."""
    response = (
        chat_agent
        .bind_tools(tools)
        .invoke([SystemMessage(content=instructions)] + state["messages"])
    )
    return {"messages": [response]}
 

def get_graph():
    
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
    )
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    return graph

