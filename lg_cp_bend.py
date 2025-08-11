from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
import register_model as rm

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    reformulated_question: str = ""  # Add field to store reformulated question

# Initialize the chat models
response_llm = None  # Model for generating responses
reformulate_llm = None  # Model for reformulating questions

def create_context_processor():
    """
    Creates a node that processes chat history and reformulates the user question with context.
    """
    def context_processor(state: State):
        messages = state["messages"]
        
        if not messages:
            return {"reformulated_question": ""}
        
        # Get the last user message
        last_message = messages[-1] if messages else None
        if not last_message or not isinstance(last_message, HumanMessage):
            return {"reformulated_question": ""}
        
        # If there's no history (first message), pass through as is
        if len(messages) <= 1:
            return {"reformulated_question": last_message.content}
        
        # Create a system prompt for context processing
        context_prompt = """You are a context processor. Your job is to:
1. Read the chat history
2. Reformulate the user's latest question to be self-contained and clear
3. Add relevant context from the conversation history
4. Remove unnecessary tokens and redundant information
5. Return only the reformulated question with context - make it complete so no history is needed
6. If there is any decimal number e.g. 9.8 MAKE SURE to treat it like 9.80

Chat history:
{history}

Latest user question: {question}

Provide a clear, self-contained reformulated question with necessary context:"""
        
        # Build chat history (excluding the last message)
        history_text = ""
        for i, msg in enumerate(messages[:-1]):
            if isinstance(msg, SystemMessage):
                continue
            elif isinstance(msg, HumanMessage):
                history_text += f"User: {msg.content}\n"
            else:
                history_text += f"Assistant: {msg.content}\n"
        
        # Create the context processing message
        context_message = HumanMessage(
            content=context_prompt.format(
                history=history_text.strip() if history_text else "No previous conversation.",
                question=last_message.content
            )
        )
        
        # Get the reformulated question from the reformulate LLM
        if reformulate_llm:
            reformulated_response = reformulate_llm.invoke([context_message])
            # Return only the reformulated_question, NO messages update
            return {"reformulated_question": reformulated_response.content}
        
        return {"reformulated_question": last_message.content}
    
    return context_processor

def create_chatbot(system_content: str):
    def chatbot(state: State):
        # Get the reformulated question from the previous node
        reformulated_question = state.get("reformulated_question", "")
        
        if not reformulated_question:
            return {}
        
        # Create fresh messages with only system message and reformulated question
        chatbot_messages = []
        if system_content:
            chatbot_messages.append(SystemMessage(content=system_content))
        
        chatbot_messages.append(HumanMessage(content=reformulated_question))
        
        # Get the response from the response LLM
        if response_llm:
            response = response_llm.invoke(chatbot_messages)
            # Only return the assistant response, not the reformulated question
            return {"messages": [response]}
        
        return {}
    return chatbot

def build_chatbot_graph(personality_name: str = None, response_model=None, reformulate_model=None):
    """
    Builds the chatbot graph with two separate nodes: context processor and chatbot.
    """
    
    system_message = None
    
    # Get the actual system message content from the personality
    if personality_name:
        registry = rm.ModelRegistry()
        system_message = registry.get_personality_description(personality_name)
    
    global response_llm, reformulate_llm
    
    # Set the models
    if response_model:
        response_llm = response_model
    if reformulate_model:
        reformulate_llm = reformulate_model
    
    graph_builder = StateGraph(State)
    
    # Add the context processing node
    context_processor = create_context_processor()
    graph_builder.add_node("context_processor", context_processor)
    
    # Add the chatbot node
    chatbot_func = create_chatbot(system_message)
    graph_builder.add_node("chatbot", chatbot_func)
    
    # Define the flow: START -> context_processor -> chatbot -> END
    graph_builder.add_edge(START, "context_processor")
    graph_builder.add_edge("context_processor", "chatbot")
    graph_builder.add_edge("chatbot", END)
    
    return graph_builder.compile(checkpointer=InMemorySaver())