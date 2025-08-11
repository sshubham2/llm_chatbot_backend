import streamlit as st

chatbot = st.Page("streamlit_chat_ui_sc.py", title="LLM Chatbot (Simple)", icon="🤖")
chatbot2 = st.Page("streamlit_chat_ui_cp.py", title="LLM Chatbot (Context Processor)", icon="🤖")
model_registration = st.Page("register_model_ui.py", title="Configuration", icon="📋")

pg = st.navigation([chatbot, chatbot2, model_registration])

pg.run()