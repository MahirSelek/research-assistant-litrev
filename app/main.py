# app/main.py
"""
Main Application Entry Point - Clean Architecture
This file orchestrates the frontend UI and backend API layers
"""

import streamlit as st
import os
import yaml
import json
from typing import Dict, Any

# Add current directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import auth_manager, show_login_page
from frontend.ui import ResearchAssistantUI
from backend.api import ResearchAssistantAPI

def load_configuration() -> Dict[str, Any]:
    """Load application configuration"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        st.error("Configuration file 'config/config.yaml' not found.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading config.yaml: {e}")
        st.stop()

def load_streamlit_secrets() -> Dict[str, Any]:
    """Load configuration from Streamlit secrets"""
    try:
        # Elastic Cloud Configuration
        elastic_config = {
            'elastic_cloud_id': st.secrets["elasticsearch"]["cloud_id"],
            'elastic_username': st.secrets["elasticsearch"]["username"],
            'elastic_password': st.secrets["elasticsearch"]["password"]
        }

        # Vertex AI Configurations
        vertexai_config = {
            'vertexai_project': st.secrets["vertex_ai"]["VERTEXAI_PROJECT"],
            'vertexai_location': st.secrets["vertex_ai"]["VERTEXAI_LOCATION"],
            'vertexai_model_id': "gemini-2.0-flash-001"
        }

        # GCS Configuration
        gcs_config = {
            'gcs_bucket_name': st.secrets["app_config"]["gcs_bucket_name"]
        }

        # Google Service Account Credentials
        gcp_service_account_secret = st.secrets["gcp_service_account"]
        GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
        
        # Write credentials to temporary file
        with open("gcp_credentials.json", "w") as f:
            json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
        # Set environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"
        
        return {
            **elastic_config,
            **vertexai_config,
            **gcs_config
        }

    except KeyError as e:
        st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
        st.stop()

def initialize_application():
    """Initialize the application with proper configuration"""
    # Load configuration
    config = load_configuration()
    secrets = load_streamlit_secrets()
    
    # Combine configurations
    full_config = {**config, **secrets}
    
    # Initialize backend API
    api = ResearchAssistantAPI(full_config)
    
    # Initialize frontend UI
    ui = ResearchAssistantUI(api)
    
    return api, ui

def main():
    """Main application entry point"""
    # Set page configuration FIRST (must be before any other Streamlit calls)
    st.set_page_config(
        layout="wide", 
        page_title="Polo GGB Research Assistant", 
        page_icon="polo-ggb-logo.png",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "Polo GGB Research Assistant - AI-powered literature review tool"
        }
    )
    
    # Check authentication
    if not auth_manager.require_auth():
        show_login_page()
        return
    
    # Initialize application
    try:
        api, ui = initialize_application()
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        return

    # Load CSS
    current_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(current_dir, "style.css")
    ui.local_css(style_path)
    
    # Initialize session state
    ui.initialize_session_state()
    
    # Render the application with responsive design
    ui.render_sidebar()
    ui.render_main_interface()

if __name__ == "__main__":
    main()