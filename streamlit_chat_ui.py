import streamlit as st
import test2
import re
import os
from datetime import datetime

# Set the page configuration for Streamlit
st.set_page_config(page_title="LLM Chatbot", page_icon=":robot_face:",
                   layout="wide", initial_sidebar_state="expanded")

if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
if "seleted_temperature" not in st.session_state:
    st.session_state.selected_temperature = 0.5

with st.sidebar:
    st.session_state.selected_model = st.selectbox("Select Model",
                                                    ["deepseek-r1",
                                                      "other-model"],
                                                        index=0, key="model_select")
    st.session_state.selected_temperature = st.slider("Temperature", 0.0, 1.0, 0.5, key="temperature")


# Set the model and temperature in the ChatOllama instance
test2.llm = test2.ChatOllama(model=st.session_state.selected_model,
                             temperature=st.session_state.selected_temperature)

# Cache the graph so it's not rebuilt on every run.
# This preserves the conversation history in the graph's memory.
@st.cache_resource
def get_graph():
    return test2.build_chatbot_graph()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = os.getlogin() + datetime.now().strftime("_%H_%M_%S")

# Set the configuration for the graph
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Display the entire chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        graph = get_graph()
        
        # The checkpointer in the graph will load the previous messages for the given thread_id
        events = graph.stream(
            {"messages": [("user", prompt)]},
            config=config,
            stream_mode="messages"
        )

        # First, stream the raw response to a placeholder to show progress
        placeholder = st.empty()
        full_response = ""
        for chunk in events:
            # The stream yields lists of message chunks. We get the content from the first one.
            content = chunk[0].content if chunk else ""
            full_response += content
            placeholder.markdown(full_response + "▌")

        # Clear the placeholder and render the final, formatted response
        placeholder.empty()

        # Use regex to split the response by <think> tags
        # parts = re.split(r"(<think>.*?</think>)", full_response, flags=re.DOTALL)

        thinking_part = re.findall(r"<think>(.*?)</think>", full_response, flags=re.DOTALL)
        if thinking_part:
            # If there's a thinking part, display it in an expander
            with st.expander("Thinking..."):
                st.markdown(thinking_part[0].strip())

        actual_response = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()
        st.markdown(actual_response)
        st.empty()
        st.session_state.messages.append({"role": "assistant", "content": actual_response})

with st.sidebar:
    st.write("Thread ID:", st.session_state.thread_id)
    st.write("Messages in this thread:", len(st.session_state.messages))
    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.rerun()  # Rerun the app to clear the chat display