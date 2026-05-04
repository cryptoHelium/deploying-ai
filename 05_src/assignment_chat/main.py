#The main file that handles the LLM/Model calls. the UI will be depended on the graph and tools concept.
#the instructions are set in prompts.py
#As mentioned above we will use the defined tools. LLM will determine which tool to use.
#Everything will start with the app.py It will load the chat interface and call the model to use the available tools/services based on user input
#See the workflow below
#Code reused from sample and class

"""User message
     ↓
    call_model  →  LLM reads tool descriptions → decides which tool fits
     ↓
    tools_condition  →  tool call detected?
     ↓ yes
    ToolNode  →  runs the function, returns result
     ↓
    call_model  →  LLM reads result, writes final answer
     ↓
    User sees response"""

from langgraph.graph import StateGraph, MessagesState, START
from langchain.chat_models import init_chat_model
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage,  HumanMessage

from dotenv import load_dotenv

load_dotenv("../../05_src/.secrets")

import json
import requests
import os

#These are the tools, aka services that will be provided

from prompts import return_instructions
from tools_sports import get_nhl_team_facts
from tools_bbcnews import handle_semantic_search
from tools_websearch import handle_web_search


load_dotenv("../../05_src/.secrets")


chat_agent = init_chat_model(
    "openai:gpt-4o-mini",
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_key="any-value",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY", "")},
)

#use the tools available, depending on what is needed. Use the instructions from the prompts.py

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

