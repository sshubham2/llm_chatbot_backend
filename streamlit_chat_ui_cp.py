import streamlit as st
import lg_cp_bend
import re
import os
from datetime import datetime
from langchain.chat_models import init_chat_model
import uuid
import register_model as rm
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io


registry = rm.ModelRegistry()

def save_conversation(messages, thread_id, title=None):
    """Save conversation to a JSON file"""
    if not os.path.exists("saved_conversations"):
        os.makedirs("saved_conversations")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not title:
        title = f"Conversation_{timestamp}"
    
    conversation_data = {
        "title": title,
        "thread_id": thread_id,
        "timestamp": timestamp,
        "messages": messages,
        "model": st.session_state.selected_model,
        "provider": st.session_state.selected_provider,
        "temperature": st.session_state.selected_temperature,
        "personality": st.session_state.selected_personality
    }
    
    filename = f"saved_conversations/{title}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)
    
    return filename

def load_conversation(filename):
    """Load conversation from a JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error loading conversation: {e}")
        return None

def get_saved_conversations():
    """Get list of saved conversations"""
    if not os.path.exists("saved_conversations"):
        return []
    
    conversations = []
    for filename in os.listdir("saved_conversations"):
        if filename.endswith('.json'):
            try:
                with open(f"saved_conversations/{filename}", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                conversations.append({
                    "filename": f"saved_conversations/{filename}",
                    "title": data.get("title", "Untitled"),
                    "timestamp": data.get("timestamp", ""),
                    "message_count": len(data.get("messages", []))
                })
            except:
                continue
    
    # Sort by timestamp (newest first)
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return conversations

def export_to_pdf(messages, thread_id, title=None):
    """Export conversation to PDF"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor='#333333'
    )
    
    user_style = ParagraphStyle(
        'UserMessage',
        parent=styles['Normal'],
        fontSize=12,
        leftIndent=0,
        rightIndent=20,
        spaceAfter=10,
        textColor='#0066cc'
    )
    
    assistant_style = ParagraphStyle(
        'AssistantMessage',
        parent=styles['Normal'],
        fontSize=12,
        leftIndent=20,
        rightIndent=0,
        spaceAfter=10,
        textColor='#333333'
    )
    
    # Build PDF content
    story = []
    
    # Title
    if not title:
        title = f"Chat Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(title, title_style))
    
    # Metadata
    story.append(Paragraph(f"<b>Thread ID:</b> {thread_id}", styles['Normal']))
    story.append(Paragraph(f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"<b>Model:</b> {st.session_state.selected_model}", styles['Normal']))
    story.append(Paragraph(f"<b>Provider:</b> {st.session_state.selected_provider}", styles['Normal']))
    if st.session_state.selected_personality:
        story.append(Paragraph(f"<b>Personality:</b> {st.session_state.selected_personality}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Messages
    for i, message in enumerate(messages):
        role = message['role']
        content = message['content']
        
        # Clean content for PDF (remove HTML tags, escape special characters)
        content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        if role == 'user':
            story.append(Paragraph(f"<b>👤 User:</b>", styles['Normal']))
            story.append(Paragraph(content, user_style))
        else:
            story.append(Paragraph(f"<b>🤖 Assistant:</b>", styles['Normal']))
            story.append(Paragraph(content, assistant_style))
        
        story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Set the page configuration for Streamlit
st.set_page_config(page_title="LLM Chatbot", page_icon=":robot_face:",
                   layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main chat container styling */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Sidebar styling - adaptive to theme */
    .css-1d391kg {
        background-color: var(--background-color);
    }
    
    /* Model info header styling - improved for dark mode */
    .model-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
        color: #ffffff;
        padding: 0.10rem 0.30rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 0.25rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Make h2 in model header smaller */
    .model-header h2 {
        margin: 0;
        font-size: 1.5rem;      /* Reduced font size */
        line-height: 1.2;       /* Tighter line height */
    }
    
    /* Make paragraph in model header smaller */
    .model-header p {
        margin: 0.15rem 0 0 0;  /* Reduced top margin */
        font-size: 0.9rem;      /* Slightly smaller font */
    }
    
    /* Alternative darker gradient for better contrast */
    .model-header-alt {
        background: linear-gradient(135deg, #1e40af 0%, #7c2d12 50%, #be185d 100%);
        color: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Chat message styling */
    .stChatMessage {
        margin-bottom: 1rem;
    }
    
    /* Thinking expander styling - theme adaptive */
    .thinking-content {
        background-color: rgba(255, 193, 7, 0.15);  /* Light amber background */
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        color: #856404;  /* Dark amber text for light mode */
    }
    
    /* Sidebar section headers - improved contrast */
    .sidebar-section {
        background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
        color: #f9fafb;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-weight: bold;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
     /* Thread info styling - better visibility */
    .thread-info {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: #e0e7ff;
        padding: 0.75rem;
        border-radius: 8px;
        font-size: 0.75rem;  /* Slightly smaller font to fit more text */
        word-break: break-all;  /* Break long words */
        word-wrap: break-word;  /* Wrap long words */
        overflow-wrap: break-word;  /* Modern word wrapping */
        border: 1px solid rgba(255,255,255,0.1);
        line-height: 1.3;  /* Better line spacing for readability */
    }
    
    /* Dark mode media query */
    @media (prefers-color-scheme: dark) {
        .sidebar-section {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            color: #f3f4f6;
        }
        
        .thread-info {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #cbd5e1;
        }
        
        .thinking-content {
            background-color: rgba(59, 130, 246, 0.15);  /* Blue background for dark mode */
            border-left-color: #3b82f6;
            color: #bfdbfe;  /* Light blue text for dark mode */
        }
    }
</style>
""", unsafe_allow_html=True)

if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "Ollama"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "deepseek-r1"
if "selected_temperature" not in st.session_state:
    st.session_state.selected_temperature = 0.5
if "selected_personality" not in st.session_state:
    st.session_state.selected_personality = None
if "previous_model" not in st.session_state:
    st.session_state.previous_model = st.session_state.selected_model
if "previous_provider" not in st.session_state:
    st.session_state.previous_provider = st.session_state.selected_provider
if "reformulate_provider" not in st.session_state:
    st.session_state.reformulate_provider = "Ollama"
if "reformulate_model" not in st.session_state:
    st.session_state.reformulate_model = "deepseek-r1"
if "previous_reformulate_model" not in st.session_state:
    st.session_state.previous_reformulate_model = st.session_state.reformulate_model
if "previous_reformulate_provider" not in st.session_state:
    st.session_state.previous_reformulate_provider = st.session_state.reformulate_provider
if "previous_personality" not in st.session_state:
    st.session_state.previous_personality = st.session_state.selected_personality

with st.sidebar:
    st.markdown('<div class="sidebar-section">🎭 Personality</div>', unsafe_allow_html=True)
    # Get list of all personalities
    personalities = registry.get_all_personalities()
    if personalities:
        selected_personality = st.selectbox("Choose AI Personality", 
                                           [p[0] for p in personalities],
                                           index=None, key="personality_select",
                                           help="Select a personality to customize the AI's behavior")
        st.session_state.selected_personality = selected_personality
    
    st.markdown('<div class="sidebar-section">🔄 Context Processing Model</div>', unsafe_allow_html=True)
    providers = registry.get_all_providers()
    if not providers:
        st.error("No providers registered. Please register a model first.")
    
    reformulate_provider = st.selectbox("🏢 Context Provider", [p[0] for p in providers],
                                       index=0, key="reformulate_provider_select")
    st.session_state.reformulate_provider = reformulate_provider
    
    if reformulate_provider:
        reformulate_models = registry.get_models_by_provider(reformulate_provider)
        reformulate_model = st.selectbox("🧠 Context Model", [m[0] for m in reformulate_models],
                                        index=0, key="reformulate_model_select",
                                        help="Model used for reformulating questions with context")
        st.session_state.reformulate_model = reformulate_model
    
    st.markdown('<div class="sidebar-section">🤖 Response Generation Model</div>', unsafe_allow_html=True)
    selected_provider = st.selectbox("🏢 Response Provider", [p[0] for p in providers],
                                    index=0, key="provider_select")
    st.session_state.selected_provider = selected_provider
    
    if selected_provider:
        models = registry.get_models_by_provider(selected_provider)
        selected_model = st.selectbox("🧠 Response Model", [m[0] for m in models],
                                     index=0, key="model_select",
                                     help="Model used for generating the final response")
        st.session_state.selected_model = selected_model
        
        if selected_model:
            try:
                # Set up API keys for both providers
                for provider in [selected_provider, reformulate_provider]:
                    api_key = registry.get_api_key(provider)
                    env_var_name = registry.get_api_env_name(provider)
                    if api_key and env_var_name:
                        api_key = os.environ[f'{env_var_name}'] = f"{api_key}"
            except Exception as e:
                st.error(f"Configuration error: {e}")
                st.stop()
            
            selected_temperature = st.slider("🌡️ Response Temperature", 0.0, 1.0, 0.5, key="temperature",
                                            help="Temperature for response generation (lower = more focused, higher = more creative)")
            st.session_state.selected_temperature = selected_temperature
        else:
            st.error("Unable to initialize the model. Please check the log.")

# Cache the graph so it's not rebuilt on every run.
# This preserves the conversation history in the graph's memory.
@st.cache_resource
def get_graph(response_model, response_provider, response_temp, reformulate_model, reformulate_provider):
    # Update both models inside the cached function
    response_llm = init_chat_model(response_model,
                                 model_provider=response_provider,
                                 temperature=response_temp)
    
    reformulate_llm = init_chat_model(reformulate_model,
                                    model_provider=reformulate_provider,
                                    temperature=1)
    
    return lg_cp_bend.build_chatbot_graph(st.session_state.selected_personality, response_llm, reformulate_llm)

# Clear the cached graph when any model changes
if (st.session_state.selected_model != st.session_state.previous_model or 
    st.session_state.selected_provider != st.session_state.previous_provider or
    st.session_state.reformulate_model != st.session_state.previous_reformulate_model or
    st.session_state.reformulate_provider != st.session_state.previous_reformulate_provider or
     st.session_state.selected_personality != st.session_state.previous_personality):
    get_graph.clear()  # Clear the cached graph
    st.session_state.previous_model = st.session_state.selected_model
    st.session_state.previous_provider = st.session_state.selected_provider
    st.session_state.previous_reformulate_model = st.session_state.reformulate_model
    st.session_state.previous_reformulate_provider = st.session_state.reformulate_provider
    
# Display the selected models and providers at the top of the page
response_model_display = registry.get_model_display_name(st.session_state.selected_provider, st.session_state.selected_model)
context_model_display = registry.get_model_display_name(st.session_state.reformulate_provider, st.session_state.reformulate_model)

if st.session_state.selected_personality:
    st.markdown(f'''
    <div class="model-header">
        <h2>🎭 {st.session_state.selected_personality}</h2>
        <p style="margin: 0; opacity: 0.8;">Response: {response_model_display} | Context: {context_model_display}</p>
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown(f'''
    <div class="model-header">
        <h2>🤖 Dual Model Chat</h2>
        <p style="margin: 0; opacity: 0.8;">Response: {response_model_display} | Context: {context_model_display}</p>
    </div>
    ''', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Set the configuration for the graph
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Display the entire chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("💬 Ask me anything..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        graph = get_graph(st.session_state.selected_model, 
                st.session_state.selected_provider,
                st.session_state.selected_temperature,
                st.session_state.reformulate_model,
                st.session_state.reformulate_provider)
        
        # The checkpointer in the graph will load the previous messages for the given thread_id
        try:
            events = graph.stream(
                {"messages": [("user", prompt)]},
                config=config,
                stream_mode="updates"
            )
        except Exception as e:
            st.error(f"Error invoking the model: {e}")
            st.stop()

        # First, stream the raw response to a placeholder to show progress
        if events:
            placeholder = st.empty()
            full_response = ""
            
            for chunk in events:
                # Only process updates from the chatbot node
                if "chatbot" in chunk and "messages" in chunk["chatbot"]:
                    messages = chunk["chatbot"]["messages"]
                    if messages:
                        # Get the last message content
                        message = messages[-1]
                        if hasattr(message, 'content'):
                            content = message.content
                            full_response = content  # Replace, don't concatenate
                            placeholder.markdown(full_response + "▌")

            # Clear the placeholder and render the final, formatted response
            placeholder.empty()
            
        if not full_response:
            st.error("No response received from the model.")
            st.stop()
        
        if full_response:
            # Check if response starts with thinking tags (more reliable for thinking models)
            thinking_match = re.match(r'^<(think|reasoning|thought|analysis|internal)>(.*?)</\1>(.*)', 
                                    full_response, flags=re.DOTALL)
            
            if thinking_match:
                # Extract thinking content and actual response
                thinking_content = thinking_match.group(2).strip()
                actual_response = thinking_match.group(3).strip()
            
            # Display thinking part in expander
                with st.expander("🧠 AI's Thought Process", expanded=False):
                    st.markdown(f'<div class="thinking-content">{thinking_content}</div>', unsafe_allow_html=True)
                
                # Display actual response
                st.markdown(actual_response)
            else:
                # No thinking tags at start, display full response
                st.markdown(full_response)
                actual_response = full_response
            
            st.session_state.messages.append({"role": "assistant", "content": actual_response})

with st.sidebar:
    st.markdown('<div class="sidebar-section">💬 Conversation</div>', unsafe_allow_html=True)
    # Enhanced thread info with full Thread ID
    st.markdown(f'''
    <div class="thread-info">
        <strong>Thread ID:</strong><br>
        <code style="font-size: 0.7rem; line-height: 1.2;">{st.session_state.thread_id}</code>
    </div>
    ''', unsafe_allow_html=True)
    
    # Conversation management buttons
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced new conversation button
        if st.button("🔄 New", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.success("✅ New conversation started!")
            st.rerun()
    
    with col2:
        # Save conversation button
        if st.button("💾 Save", use_container_width=True, disabled=len(st.session_state.messages) == 0):
            # Create a text input for conversation title
            if "show_save_input" not in st.session_state:
                st.session_state.show_save_input = True
            else:
                st.session_state.show_save_input = not st.session_state.show_save_input
    
    # Save conversation input (shown when save button is clicked)
    if st.session_state.get("show_save_input", False) and len(st.session_state.messages) > 0:
        title = st.text_input("💬 Conversation Title:", 
                             placeholder="Enter a title for this conversation...",
                             key="save_title")
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("✅ Save", key="confirm_save"):
                filename = save_conversation(st.session_state.messages, 
                                           st.session_state.thread_id, 
                                           title if title else None)
                st.success(f"💾 Conversation saved!")
                st.session_state.show_save_input = False
                st.rerun()
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_save"):
                st.session_state.show_save_input = False
                st.rerun()
    
    # Export to PDF button
    if st.button("📄 Export PDF", use_container_width=True, disabled=len(st.session_state.messages) == 0):
        try:
            pdf_buffer = export_to_pdf(st.session_state.messages, st.session_state.thread_id)
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error creating PDF: {e}")
    
    # Load saved conversations section
    st.markdown('<div class="sidebar-section">📂 Saved Conversations</div>', unsafe_allow_html=True)
    
    saved_conversations = get_saved_conversations()
    if saved_conversations:
        selected_conversation = st.selectbox(
            "Select a conversation to load:",
            options=[""] + [f"{conv['title']} ({conv['message_count']} messages)" for conv in saved_conversations],
            key="conversation_select"
        )
        
        if selected_conversation and selected_conversation != "":
            # Find the selected conversation
            conv_index = [f"{conv['title']} ({conv['message_count']} messages)" for conv in saved_conversations].index(selected_conversation)
            selected_conv = saved_conversations[conv_index]
            
            col_load, col_delete = st.columns(2)
            with col_load:
                if st.button("📂 Load", key="load_conv"):
                    conversation_data = load_conversation(selected_conv["filename"])
                    if conversation_data:
                        st.session_state.messages = conversation_data["messages"]
                        st.session_state.thread_id = conversation_data["thread_id"]
                        # Optionally restore model settings
                        if "model" in conversation_data:
                            st.session_state.selected_model = conversation_data["model"]
                        if "provider" in conversation_data:
                            st.session_state.selected_provider = conversation_data["provider"]
                        if "temperature" in conversation_data:
                            st.session_state.selected_temperature = conversation_data["temperature"]
                        if "personality" in conversation_data:
                            st.session_state.selected_personality = conversation_data["personality"]
                        st.success("📂 Conversation loaded!")
                        st.rerun()
            
            with col_delete:
                if st.button("🗑️ Delete", key="delete_conv"):
                    try:
                        os.remove(selected_conv["filename"])
                        st.success("🗑️ Conversation deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting conversation: {e}")
    else:
        st.info("No saved conversations found.")