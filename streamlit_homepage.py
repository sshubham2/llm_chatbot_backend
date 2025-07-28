import streamlit as st

chatbot = st.Page("streamlit_chat_ui.py", title="LLM Chatbot", icon="🤖")
model_registration = st.Page("register_model_ui.py", title="Configuration", icon="📋")

pg = st.navigation([chatbot, model_registration])

pg.run()