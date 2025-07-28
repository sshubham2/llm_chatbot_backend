from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama.chat_models import ChatOllama
import re
import os
from datetime import datetime
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

# Initialize the chat model
# llm = ChatOllama(model="deepseek-r1:14B", temperature=0)
llm = None  # Placeholder for the LLM, to be set later

def create_chatbot(system_content: str):
    def chatbot(state: State):
        if system_content:
            # Check if a system message is already present
            if not any(isinstance(m, SystemMessage) for m in state["messages"]):
                # If not, prepend the system message
                state["messages"].insert(0, SystemMessage(content=system_content))
        return {"messages": llm.invoke(state["messages"])}
    return chatbot



def build_chatbot_graph(system_message: str = None):
    """
    Builds the chatbot graph with a single node for the chatbot function.
    """
    graph_builder = StateGraph(State)
    chatbot_func = create_chatbot(system_message)
    graph_builder.add_node("chatbot", chatbot_func)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    return graph_builder.compile(checkpointer=InMemorySaver())
