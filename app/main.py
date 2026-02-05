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
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from auth import auth_manager, show_login_page
from frontend.html_ui import HTMLResearchAssistantUI
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
    """Load configuration from Streamlit secrets or environment variables"""
    try:
        # Elastic Cloud Configuration
        # Support both Serverless (endpoint + API key) and Hosted (cloud_id + username/password)
        # Try Streamlit secrets first, then fall back to environment variables
        def get_secret(key_path: str, env_var: str = None):
            """Get value from Streamlit secrets or environment variable"""
            try:
                keys = key_path.split(".")
                value = st.secrets
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, AttributeError):
                if env_var and env_var in os.environ:
                    return os.environ[env_var]
                return None
        
        elastic_cloud_id = get_secret("elasticsearch.cloud_id", "ELASTICSEARCH_CLOUD_ID")
        elastic_endpoint = get_secret("elasticsearch.endpoint", "ELASTICSEARCH_ENDPOINT")  # For Serverless
        elastic_username = get_secret("elasticsearch.username", "ELASTICSEARCH_USERNAME")
        elastic_password = get_secret("elasticsearch.password", "ELASTICSEARCH_PASSWORD")
        elastic_api_key = get_secret("elasticsearch.api_key", "ELASTICSEARCH_API_KEY")  # For Serverless
        
        # Prioritize Serverless if both are provided
        if elastic_endpoint and elastic_api_key:
            # Serverless configuration
            print("✓ Using Serverless Elasticsearch configuration")
            elastic_config = {
                'elastic_cloud_id': None,
                'elastic_hosts': [elastic_endpoint],
                'elastic_username': None,
                'elastic_password': None,
                'elastic_api_key': elastic_api_key
            }
        elif elastic_cloud_id and elastic_username and elastic_password:
            # Hosted configuration
            print("✓ Using Hosted Elasticsearch configuration")
            elastic_config = {
                'elastic_cloud_id': elastic_cloud_id,
                'elastic_hosts': None,
                'elastic_username': elastic_username,
                'elastic_password': elastic_password,
                'elastic_api_key': None
            }
        else:
            raise KeyError("elasticsearch configuration: Must provide either (endpoint + api_key) for Serverless or (cloud_id + username + password) for Hosted")

        # Vertex AI Configurations
        vertexai_project = get_secret("vertex_ai.VERTEXAI_PROJECT", "VERTEXAI_PROJECT")
        vertexai_location = get_secret("vertex_ai.VERTEXAI_LOCATION", "VERTEXAI_LOCATION")
        vertexai_model_id = get_secret("vertex_ai.VERTEXAI_MODEL_ID", "VERTEXAI_MODEL_ID") or "gemini-2.0-flash-001"
        
        vertexai_config = {
            'vertexai_project': vertexai_project,
            'vertexai_location': vertexai_location,
            'vertexai_model_id': vertexai_model_id
        }

        # GCS Configuration
        gcs_bucket_name = get_secret("app_config.gcs_bucket_name", "GCS_BUCKET_NAME")
        gcs_config = {
            'gcs_bucket_name': gcs_bucket_name
        }

        # Google Service Account Credentials
        # Try to get from secrets first, then from environment or file
        GOOGLE_CREDENTIALS_DICT = None
        try:
            gcp_service_account_secret = st.secrets["gcp_service_account"]
            GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
        except (KeyError, AttributeError):
            # Try to load from gcp_credentials.json file
            credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path and os.path.exists(credentials_path):
                with open(credentials_path, 'r') as f:
                    GOOGLE_CREDENTIALS_DICT = json.load(f)
            elif os.path.exists("gcp_credentials.json"):
                with open("gcp_credentials.json", 'r') as f:
                    GOOGLE_CREDENTIALS_DICT = json.load(f)
        
        if not GOOGLE_CREDENTIALS_DICT:
            raise KeyError("gcp_service_account: Must provide GCP credentials in secrets, environment variable, or gcp_credentials.json file")
        
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
    
    # Initialize HTML frontend UI
    ui = HTMLResearchAssistantUI(api)
    
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
    
    # Inject CSS styling
    ui.inject_css_and_js()
    
    # Initialize session state
    ui.initialize_session_state()
    
    # Handle form submissions first
    ui.handle_form_submissions()
    
    # Render the HTML application
    ui.render_main_interface()

if __name__ == "__main__":
    main()
