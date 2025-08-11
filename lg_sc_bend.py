from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage
import register_model as rm

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
        messages = state["messages"][:]  # Create a copy of messages
        
        if system_content:
            # Remove any existing system messages
            messages = [m for m in messages if not isinstance(m, SystemMessage)]
            # Add the new system message at the beginning
            messages.insert(0, SystemMessage(content=system_content))
        
        return {"messages": llm.invoke(messages)}
    return chatbot

def build_chatbot_graph(personality_name: str = None):
    """
    Builds the chatbot graph with a single node for the chatbot function.
    """
    
    system_message = None
    
    # Get the actual system message content from the personality
    if personality_name:
        registry = rm.ModelRegistry()
        system_message = registry.get_personality_description(personality_name)
        
    graph_builder = StateGraph(State)
    chatbot_func = create_chatbot(system_message)
    graph_builder.add_node("chatbot", chatbot_func)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    return graph_builder.compile(checkpointer=InMemorySaver())
