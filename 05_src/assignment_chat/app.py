from main import get_graph
from langchain_core.messages import HumanMessage, AIMessage
import gradio as gr
from dotenv import load_dotenv
import os
import threading

from tools_bbcnews import initialize_search_service


#from utils.logger import get_logger

#_logs = get_logger(__name__)

load_dotenv("../../05_src/.secrets")

llm = get_graph()

# ── Background search index init ───────────────────────────────────────────────
 
_search_status = {"ready": False, "message": "⏳ Loading search index…"}
 
 
def _init_search_background():
    msg = initialize_search_service()
    _search_status["ready"] = True
    _search_status["message"] = msg
    print(f"[app] {msg}")
 
 
threading.Thread(target=_init_search_background, daemon=True).start()
 
 
# ── Chat function ──────────────────────────────────────────────────────────────
 
def chat(message: str, history: list[dict]) -> str:
    """
    Gradio chat callback.
 
    Args:
        message: The latest user message string.
        history: List of {"role": "user"|"assistant", "content": "..."} dicts.
 
    Returns:
        The assistant's response as a string.
    """
    langchain_messages = []
 
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
 
    langchain_messages.append(HumanMessage(content=message))
 
    response = llm.invoke({"messages": langchain_messages})
    return response["messages"][-1].content
 
 
# ── Gradio UI
 
chat_ui = gr.ChatInterface(
    fn=chat,
    type="messages",
    title="🤖 Multi-Service AI Chatbot",
    description=(
        "Ask me about **NHL teams**, search **BBC news articles**, "
        "or ask any **general web question**. Routing is automatic."
    ),
    examples=[
        "Tell me about the Toronto Maple Leafs",
        "Find BBC news articles about artificial intelligence",
        "What is machine learning?",
    ],
    cache_examples=False,
)
 
 
# ── Launch ─────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    print(f"[app] Search index status: {_search_status['message']}")
    chat_ui.launch()