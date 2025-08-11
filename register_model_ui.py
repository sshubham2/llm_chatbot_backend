import streamlit as st
from register_model import ModelRegistry

# Initialize the model registry
registry = ModelRegistry()

st.set_page_config(page_title="Register Model", page_icon=":robot_face:",
                   layout="wide")

st.title("Model Configuration and Registration")

tab1, tab2, tab3, tab4  = st.tabs(["Registered Models", "Register Model", "Delete Models", "System Prompts"])
   
with tab1:
    # Display registered models in tabular format
    st.markdown("#### Registered Models")
    # fetch all providers and their models
    model_info = registry.get_provider_model_names()
    # This will give provider, model and display name from the registry
    # Convert to a DataFrame for better display
    if model_info:
        import pandas as pd
        df = pd.DataFrame(model_info, columns=["Provider", "Display Name", "Model"])
        df = df.set_index("Provider")
        df = df.sort_index()
        st.dataframe(df, use_container_width=False)
        
    config_info = registry.get_provider_configurations()
    if config_info:
        st.markdown("#### Registered Configurations")
        config_df = pd.DataFrame(config_info, columns=["Provider", "Environment Variable"])
        config_df = config_df.set_index("Provider")
        config_df = config_df.sort_index()
        st.dataframe(config_df,use_container_width=False)
        
    # Refresh the page to see the latest registered models
    if st.button("Refresh"):
        st.rerun()


with tab2:
    register_form_1 = st.form("Register Model Details", clear_on_submit=True)
    with register_form_1:
        st.subheader("Model Details")
        display_name = st.text_input("Model Display Name", placeholder="Enter model display name")
        model_name = st.text_input("Model Name", placeholder="Enter model name")
        provider = st.text_input("Provider", placeholder="Enter provider name")
        submit_button = st.form_submit_button("Register Model")
        if submit_button:
            if display_name and model_name and provider:
                try:
                    from register_model import ModelRegistry
                    register_model = ModelRegistry()
                    register_model.register_model(display_name, model_name, provider)
                    st.success("Model registered successfully!")
                except Exception as e:
                    st.error(f"Error registering model: {e}")
            else:
                st.warning("Please fill in all fields.")
    
    register_form_2 = st.form("Register provider configurations", clear_on_submit=True)
    with register_form_2:
        st.subheader("Configuration Details")
        provider = st.text_input("Provider", placeholder="Enter provider name for configuration")
        api_key = st.text_input("API Key", placeholder="Enter API key for configuration", type="password")
        api_env_name = st.text_input("Environment Variable Name", placeholder="Enter environment variable name for configuration")
        config_button = st.form_submit_button("Register Configuration")
        
        if config_button:
            if provider and api_key and api_env_name:
                try:
                    registry.register_config(provider, api_key, api_env_name)
                    st.success("Configuration registered successfully!")
                except Exception as e:
                    st.error(f"Error registering configuration: {e}")
            else:
                st.warning("Please fill in all fields.")

with tab3:                
    # Delelte existing model
    st.subheader("Delete Existing Model")
    delete_form_1 = st.form("Delete Model", clear_on_submit=True)
    with delete_form_1:
        delete_provider = st.selectbox("Select Provider", [p[0] for p in registry.get_all_providers()], key="delete_provider")
        delete_model = st.selectbox("Select Model", [m[0] for m in registry.get_models_by_provider(delete_provider)], key="delete_model")
        delete_button = st.form_submit_button("Delete Model")
        
        if delete_button:
            try:
                registry.delete_model(delete_provider, delete_model)
                st.success("Model deleted successfully!")
            except Exception as e:
                st.error(f"Error deleting model: {e}")
                
    # Delelte existing model
    st.subheader("Delete Existing Configuration")
    delete_form_1 = st.form("Delete Configuration", clear_on_submit=True)
    with delete_form_1:
        delete_provider = st.selectbox("Select Provider", [p[0] for p in registry.get_all_providers()], key="delete_provider_config")
        delete_button = st.form_submit_button("Delete Configuration")
        
        if delete_button:
            try:
                registry.delete_config(delete_provider)
                st.success("Configuration deleted successfully!")
            except Exception as e:
                st.error(f"Error deleting Configuration: {e}")
                
with tab4:
    st.subheader("System Prompts")
    st.markdown("#### Add or Edit System Prompts")
    prompt_form = st.form("System Prompt Form", clear_on_submit=True)
    with prompt_form:
        prompt_name = st.text_input("Prompt Name", placeholder="Enter prompt name")
        prompt_description = st.text_area("Prompt Description", placeholder="Enter prompt description", height=700)
        save_prompt_button = st.form_submit_button("Save Prompt")
        
        if save_prompt_button:
            if prompt_name and prompt_description:
                try:
                    registry.register_personality(prompt_name, prompt_description)
                    st.success("System prompt saved successfully!")
                except Exception as e:
                    st.error(f"Error saving system prompt: {e}")
            else:
                st.warning("Please fill in all fields.")
                
    #Edit existing system prompts
    st.markdown("#### Edit Existing System Prompts")
    
    # Move the selectbox outside the form to allow for dynamic updates
    personalities = registry.get_all_personalities()
    if personalities:
        selected_prompt = st.selectbox("Select Prompt to Edit", [p[0] for p in personalities], key="edit_prompt_select")
        
        # Get the description for the selected prompt
        system_prompt = registry.get_personality_description(selected_prompt)
        
        edit_prompt_form = st.form("Edit System Prompt Form", clear_on_submit=False)
        with edit_prompt_form:
            if system_prompt:
                edit_prompt_description = st.text_area("Current Prompt Description", value=system_prompt, height=700, key="edit_prompt_textarea")
            else:
                edit_prompt_description = st.text_area("Current Prompt Description", height=700, key="edit_prompt_textarea")
            update_prompt_button = st.form_submit_button("Update Prompt")
            
            if update_prompt_button:
                if selected_prompt and edit_prompt_description:
                    try:
                        registry.edit_personality_description(selected_prompt, edit_prompt_description)
                        st.success("System prompt updated successfully!")
                        st.rerun()  # Refresh to show updated content
                    except Exception as e:
                        st.error(f"Error updating system prompt: {e}")
                else:
                    st.warning("Please fill in all fields.")
    else:
        st.info("No system prompts available to edit.")
                
    # Delete existing system prompts
    st.markdown("#### Delete Existing System Prompts")
    delete_prompt_form = st.form("Delete System Prompt Form", clear_on_submit=True)
    with delete_prompt_form:
        prompt_name = st.selectbox("Select Prompt to Delete", [p[0] for p in registry.get_all_personalities()], key="delete_prompt_select")
        delete_prompt_button = st.form_submit_button("Delete Prompt")
        
        if delete_prompt_button:
            try:
                registry.delete_personality(prompt_name)
                st.success("System prompt deleted successfully!")
            except Exception as e:
                st.error(f"Error deleting system prompt: {e}")