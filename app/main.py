# app/main.py
# main.py v2

import streamlit as st
import platform
import requests
import time
import json
import PyPDF2
import io
import yaml
import os
import sys
import base64
from typing import List, Dict, Any
import datetime
from dateutil import parser as date_parser
from collections import defaultdict

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
from google.api_core.exceptions import NotFound
from auth import get_auth_manager, show_login_page, show_logout_button


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from elasticsearch_utils import get_es_manager
except ImportError as e:
    st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
    st.stop()

# App Configuration & Constants
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    st.error("Configuration file 'config/config.yaml' not found.")
    st.stop()
except Exception as e:
    st.error(f"Error loading config.yaml: {e}")
    st.stop()

# Configuration from Streamlit Secrets
try:
    # Elastic Cloud Configuration
    ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
    ELASTIC_USER = st.secrets["elasticsearch"]["username"]
    ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

    # Vertex AI Configurations
    # Reading lowercase keys to match secrets.toml best practice
    VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
    VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
    VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

    # GCS Configuration
    GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

    # Google Service Account Credentials
    # 1. Read the secret, which is a Streamlit AttrDict object.
    gcp_service_account_secret = st.secrets["gcp_service_account"]
    
    # 2. Convert the AttrDict to a standard Python dictionary.
    GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
    # 3. Write the standard dictionary to a temporary file.
    with open("gcp_credentials.json", "w") as f:
        json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
    # 4. Set the environment variable for Google Cloud libraries to find the file.
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

except KeyError as e:
    st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
    st.stop()

# Interface Constants
GENETICS_KEYWORDS = [
    "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
]   
USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# API and Helper Functions
def post_message_vertexai(input_text: str) -> str | None:
    try:
        vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
        model = GenerativeModel(VERTEXAI_MODEL_ID)
        generation_config = {"temperature": 0.2, "max_output_tokens": 8192}
        response = model.generate_content([input_text], generation_config=generation_config)
        return response.text
    except Exception as e:
        st.error(f"An error occurred with the Vertex AI API: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

@st.cache_data
def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    except NotFound:
        st.warning(f"File not found in GCS: {blob_name}")
        return None
    except Exception as e:
        st.error(f"Failed to download from GCS: {e}")
        return None

def get_user_key(key):
    """Get user-specific session key"""
    current_user = st.session_state.get('username', 'default')
    return f"{key}_{current_user}"

def get_user_session(key, default=None):
    """Get user-specific session value"""
    user_key = get_user_key(key)
    return st.session_state.get(user_key, default)

def set_user_session(key, value):
    """Set user-specific session value"""
    user_key = get_user_key(key)
    st.session_state[user_key] = value

def save_user_data_to_cloud():
    """Save current user's data to storage (cloud or local)"""
    if st.session_state.get('authenticated', False) and 'username' in st.session_state:
        username = st.session_state.username
        
        # Collect all user-specific data
        user_data = {}
        for key, value in st.session_state.items():
            if key.endswith(f"_{username}"):
                # Extract the original key name
                original_key = key[:-len(f"_{username}")]
                user_data[original_key] = value
        
        # Save to storage (cloud or local)
        if user_data:
            auth_mgr = get_auth_manager()
            auth_mgr.save_user_data(username, user_data)

def restore_user_data_from_cloud(username: str, silent: bool = True):
    """Restore user data from cloud storage to session state"""
    try:
        auth_mgr = get_auth_manager()
        user_data = auth_mgr.load_user_data(username)
        
        if user_data:
            # Restore user-specific data to session state
            for key, value in user_data.items():
                user_key = get_user_key(key)
                st.session_state[user_key] = value
            
            # Only show messages if not in silent mode
            if not silent:
                conversation_count = len(user_data.get('conversations', {}))
                if conversation_count > 0:
                    st.success(f"✅ Restored {conversation_count} conversation(s)")
                else:
                    st.info("No conversation history found")
        else:
            # Try to load individual conversation files as fallback
            load_individual_conversations(username, show_progress=False, silent=silent)
            
    except Exception as e:
        if not silent:
            st.error("Unable to restore conversation history")

def load_individual_conversations(username: str, show_progress: bool = False, silent: bool = True):
    """Load individual conversation files from the conversations folder"""
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        conversations = {}
        conversation_count = 0
        
        # Try both path formats (prioritize the correct one)
        path_formats = [
            f"user-data/conversations/{username}/",
            f"user_data/conversations/{username}/"
        ]
        
        for conversations_folder in path_formats:
            if show_progress and not silent:
                st.write(f"🔍 Checking path: `{conversations_folder}`")
            blobs = bucket.list_blobs(prefix=conversations_folder)
            
            for blob in blobs:
                if blob.name.endswith('.json') and not blob.name.endswith('index.json'):
                    try:
                        # Download and parse the conversation file
                        content = blob.download_as_text()
                        conv_data = json.loads(content)
                        
                        # Extract conversation ID from filename
                        filename = blob.name.split('/')[-1]
                        if filename.startswith('conv_'):
                            conv_id = filename.replace('.json', '')
                            conversations[conv_id] = conv_data
                            conversation_count += 1
                            if show_progress and not silent:
                                st.write(f"✅ Loaded conversation: {conv_id}")
                            
                    except Exception as e:
                        if show_progress and not silent:
                            st.warning(f"Could not load conversation file {blob.name}: {e}")
                        continue
            
            # If we found conversations, break out of the loop
            if conversations:
                break
        
        if conversations:
            # Restore conversations to session state
            set_user_session('conversations', conversations)
            if show_progress and not silent:
                st.success(f"📂 Restored {conversation_count} conversation(s) from individual files")
            elif not silent:
                st.success(f"✅ Restored {conversation_count} conversation(s)")
        else:
            if show_progress and not silent:
                st.info("📂 No individual conversation files found in any path")
            elif not silent:
                st.info("No conversation history found")
            
    except Exception as e:
        if show_progress and not silent:
            st.error(f"Error loading individual conversations: {e}")
        elif not silent:
            st.error("Unable to load conversation history")

def debug_cloud_storage(username: str):
    """Debug function to show what's stored in cloud storage"""
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        st.write("🔍 **Cloud Storage Debug Info:**")
        
        # Check for consolidated user data file
        user_data_file = f"user-data/{username}_data.json"
        user_data_blob = bucket.blob(user_data_file)
        
        st.write(f"**1. Consolidated user data file:** `{user_data_file}`")
        if user_data_blob.exists():
            st.success(f"✅ Found consolidated user data file")
            try:
                content = user_data_blob.download_as_text()
                data = json.loads(content)
                conv_count = len(data.get('conversations', {}))
                st.write(f"   - Contains {conv_count} conversations")
            except Exception as e:
                st.error(f"   - Error reading file: {e}")
        else:
            st.warning(f"❌ Consolidated user data file not found")
        
        # Check for individual conversation files
        conversations_folder = f"user-data/conversations/{username}/"
        st.write(f"**2. Individual conversation files:** `{conversations_folder}`")
        
        blobs = list(bucket.list_blobs(prefix=conversations_folder))
        if blobs:
            st.success(f"✅ Found {len(blobs)} files in conversations folder:")
            for blob in blobs:
                st.write(f"   - `{blob.name}` ({blob.size} bytes)")
        else:
            st.warning(f"❌ No files found in conversations folder")
            
            # Try alternative path structure
            alt_folder = f"user-data/conversations/{username}/"
            st.write(f"**2b. Trying alternative path:** `{alt_folder}`")
            alt_blobs = list(bucket.list_blobs(prefix=alt_folder))
            if alt_blobs:
                st.success(f"✅ Found {len(alt_blobs)} files in alternative path:")
                for blob in alt_blobs:
                    st.write(f"   - `{blob.name}` ({blob.size} bytes)")
            else:
                st.warning(f"❌ No files found in alternative path either")
        
        # Check for any files with username
        st.write(f"**3. All files containing '{username}':**")
        all_blobs = list(bucket.list_blobs(prefix="user-data/"))
        matching_files = [blob for blob in all_blobs if username in blob.name]
        
        if matching_files:
            for blob in matching_files:
                st.write(f"   - `{blob.name}` ({blob.size} bytes)")
        else:
            st.warning(f"❌ No files found containing '{username}'")
            
    except Exception as e:
        st.error(f"Error debugging cloud storage: {e}")

def fix_corrupted_data(username: str):
    """Fix corrupted admin_data.json by deleting it and loading individual files"""
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # Delete the corrupted admin_data.json file
        user_data_file = f"user-data/{username}_data.json"
        user_data_blob = bucket.blob(user_data_file)
        
        if user_data_blob.exists():
            user_data_blob.delete()
            st.success("✅ Fixed data storage issue")
        
        # Now try to load individual conversation files
        with st.spinner("Loading your conversation history..."):
            load_individual_conversations(username, show_progress=False)
        
    except Exception as e:
        st.error(f"Error fixing corrupted data: {e}")

def initialize_session_state():
    # Get current username for user-specific data
    current_user = st.session_state.get('username', 'default')
    
    # Initialize user-specific session state
    if get_user_key('conversations') not in st.session_state:
        set_user_session('conversations', {})
    if get_user_key('active_conversation_id') not in st.session_state:
        set_user_session('active_conversation_id', None)
    if get_user_key('selected_keywords') not in st.session_state:
        set_user_session('selected_keywords', [])
    if get_user_key('search_mode') not in st.session_state:
        set_user_session('search_mode', "all_keywords")
    if get_user_key('uploaded_papers') not in st.session_state:
        set_user_session('uploaded_papers', [])
    if get_user_key('custom_summary_chat') not in st.session_state:
        set_user_session('custom_summary_chat', [])
    
    # Load user data from cloud storage if authenticated and no data loaded yet
    if (st.session_state.get('authenticated', False) and 
        current_user != 'default' and 
        not get_user_session('conversations')):
        # Load history silently in the background
        restore_user_data_from_cloud(current_user, silent=True)
    
    # Global session state (shared across users)
    if 'es_manager' not in st.session_state:
        st.session_state.es_manager = get_es_manager(cloud_id=ELASTIC_CLOUD_ID, username=ELASTIC_USER, password=ELASTIC_PASSWORD)
    if 'use_custom_search' not in st.session_state:
        st.session_state.use_custom_search = False
    if 'generate_custom_summary' not in st.session_state:
        st.session_state.generate_custom_summary = False
    if 'is_loading_analysis' not in st.session_state:
        st.session_state.is_loading_analysis = False
    if 'loading_message' not in st.session_state:
        st.session_state.loading_message = ""

def show_loading_overlay(message="Generating new analysis..."):
    """Show a loading overlay with message"""
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        color: white;
        font-size: 18px;
    ">
        <div style="text-align: center;">
            <div style="
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 2s linear infinite;
                margin: 0 auto 20px;
            "></div>
            <p>{message}</p>
        </div>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found. Using default styles.")

def read_pdf_content(pdf_file: io.BytesIO) -> str | None:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return "".join(page.extract_text() for page in pdf_reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def generate_conversation_title(conversation_history: str) -> str:
    prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
    title = post_message_vertexai(prompt)
    if title:
        return title.strip().replace('"', '')
    return "New Chat"

def get_paper_link(metadata: dict) -> str:
    """Safely retrieves a link from paper metadata, checking multiple keys."""
    if not isinstance(metadata, dict):
        return "Not available"
    # Prioritize specific link fields
    for key in ['url', 'link', 'doi_url']:
        link = metadata.get(key)
        if link and isinstance(link, str) and link.startswith('http'):
            return link
    return "Not available"

def filter_papers_by_gcs_dates(papers: list, time_filter_type: str) -> list:
    """
    Filter papers based on publication dates stored in GCS metadata.
    This bypasses Elasticsearch date filtering issues.
    """
    if not papers:
        return papers
    
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        filtered_papers = []
        for paper in papers:
            paper_id = paper.get('paper_id')
            if paper_id:
                # Try to find corresponding .metadata.json file
                json_filename = paper_id.rsplit('.', 1)[0] + '.metadata.json'
                json_blob = bucket.blob(json_filename)
                
                if json_blob.exists():
                    try:
                        json_content = json_blob.download_as_string()
                        json_metadata = json.loads(json_content)
                        publication_date = json_metadata.get('publication_date', '')
                        
                        # Check if this paper matches our time filter
                        if matches_time_filter(publication_date, time_filter_type):
                            filtered_papers.append(paper)
                    except Exception as e:
                        # If JSON loading fails, include the paper (better to include than exclude)
                        filtered_papers.append(paper)
                else:
                    # If no JSON file found, include the paper
                    filtered_papers.append(paper)
            else:
                filtered_papers.append(paper)
        
        return filtered_papers
    except Exception as e:
        # If any error occurs, return original papers
        return papers

def matches_time_filter(publication_date: str, time_filter_type: str) -> bool:
    """
    Check if a publication date matches the selected time filter.
    """
    if not publication_date:
        return False
    
    try:
        # Parse the date 
        from dateutil import parser as date_parser
        parsed_date = date_parser.parse(publication_date)
        
        if time_filter_type == "Current year":
            return parsed_date.year == 2025
        elif time_filter_type == "Last 3 months":
            # Check if paper is from recent months (simplified to 2025)
            return parsed_date.year == 2025
        elif time_filter_type == "Last 6 months":
            # Check if paper is from recent months (simplified to 2025)
            return parsed_date.year == 2025
        elif time_filter_type in ["January", "February", "March", "April", "May", "June", 
                                 "July", "August", "September", "October", "November", "December"]:
            month_map = {
                "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
            }
            target_month = month_map[time_filter_type]
            return parsed_date.year == 2025 and parsed_date.month == target_month
        
        return True  # For "All time" or unknown filters
    except Exception:
        return False  # If date parsing fails, exclude the paper

def sync_bucket_to_elasticsearch() -> dict:
    """
    Simple function to sync new papers from Google Cloud bucket to Elasticsearch.
    Returns a dictionary with sync results.
    """
    try:
        # Get all currently indexed papers
        es_manager = st.session_state.es_manager
        response = es_manager.es_client.search(
            index="papers",
            body={
                "query": {"match_all": {}},
                "_source": False,  # Only get IDs
                "size": 10000
            }
        )
        indexed_ids = {hit['_id'] for hit in response['hits']['hits']}
        
        # Get all papers from bucket
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blobs = bucket.list_blobs(prefix="pdf-metadata/")
        
        pdf_files = {}
        metadata_files = {}
        
        # Separate PDFs and metadata files
        for blob in blobs:
            filename = blob.name
            if filename.endswith('.pdf'):
                base_name = os.path.splitext(os.path.basename(filename))[0]
                pdf_files[base_name] = filename
            elif filename.endswith('.metadata.json'):
                base_name = os.path.splitext(os.path.basename(filename))[0]
                metadata_files[base_name] = filename
        
        # Find new papers to index
        new_papers = []
        skipped_count = 0
        
        for base_name, pdf_path in pdf_files.items():
            if base_name in metadata_files:
                if pdf_path in indexed_ids:
                    skipped_count += 1
                    continue
                
                metadata_path = metadata_files[base_name]
                
                # Download metadata
                metadata_blob = bucket.blob(metadata_path)
                metadata_content = metadata_blob.download_as_string()
                metadata = json.loads(metadata_content)
                
                # Download PDF content
                pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, pdf_path)
                if not pdf_bytes:
                    continue
                
                # Extract text content
                pdf_content = read_pdf_content(pdf_bytes)
                if not pdf_content:
                    continue
                
                # Index to Elasticsearch
                metadata['paper_id'] = pdf_path
                es_manager.index_paper(
                    paper_id=pdf_path,
                    metadata=metadata,
                    content=pdf_content,
                    index_name="papers"
                )
                
                new_papers.append(pdf_path)
        
        return {
            "success": len(new_papers),
            "errors": 0,
            "skipped": skipped_count
        }
        
    except Exception as e:
        return {
            "success": 0,
            "errors": 1,
            "skipped": 0,
            "error_message": str(e)
        }

def reload_paper_metadata(papers: list) -> list:
    """
    Reloads metadata from .metadata.json files to get the actual links.
    """
    if not papers:
        return papers
    
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        updated_papers = []
        for paper in papers:
            paper_id = paper.get('paper_id')
            if paper_id:
                # Try to find corresponding .metadata.json file
                json_filename = paper_id.rsplit('.', 1)[0] + '.metadata.json'
                json_blob = bucket.blob(json_filename)
                
                if json_blob.exists():
                    try:
                        json_content = json_blob.download_as_string()
                        json_metadata = json.loads(json_content)
                        
                        # Update the paper metadata with the JSON content
                        updated_metadata = paper.get('metadata', {}).copy()
                        updated_metadata.update(json_metadata)
                        updated_metadata['paper_id'] = paper_id
                        
                        # Create updated paper object
                        updated_paper = paper.copy()
                        updated_paper['metadata'] = updated_metadata
                        updated_papers.append(updated_paper)
                    except Exception as e:
                        # If JSON loading fails, keep original paper
                        updated_papers.append(paper)
                else:
                    # If no JSON file found, keep original paper
                    updated_papers.append(paper)
            else:
                updated_papers.append(paper)
        
        return updated_papers
    except Exception as e:
        # If any error occurs, return original papers
        return papers

def make_inline_citations_clickable(analysis_text: str, analysis_papers: list) -> str:
    """
    Make inline citations clickable by converting [1], [2][3] etc. to clickable links.
    Only citations that correspond to papers in analysis_papers will be made clickable.
    Limits citations to maximum 3 per sentence for better readability.
    """
    if not analysis_papers:
        return analysis_text
    
    import re
    
    # Create a mapping of citation numbers to paper links
    citation_links = {}
    for i, paper in enumerate(analysis_papers):
        meta = paper.get('metadata', {})
        link = get_paper_link(meta)
        if link != "Not available":
            citation_links[i + 1] = link
    
    # Function to replace citation numbers with clickable links
    def replace_citation(match):
        citation_text = match.group(0)  # e.g., "[1]" or "[2][3]"
        
        # Extract individual citation numbers
        citation_numbers = re.findall(r'\[(\d+)\]', citation_text)
        
        # Limit to maximum 3 citations per sentence
        if len(citation_numbers) > 3:
            citation_numbers = citation_numbers[:3]
        
        # Replace each citation number with a clickable link if it exists in our mapping
        result_parts = []
        for num_str in citation_numbers:
            num = int(num_str)
            if num in citation_links:
                # Create clickable link that opens in new tab
                result_parts.append(f'<a href="{citation_links[num]}" target="_blank" class="citation-link">[{num}]</a>')
            else:
                # Keep original citation if not in analysis papers
                result_parts.append(f'[{num}]')
        
        return ''.join(result_parts)
    
    # Find all citation patterns like [1], [2][3], [1][2][3], etc.
    citation_pattern = r'\[\d+\](?:\[\d+\])*'
    
    # Replace citations with clickable links
    clickable_text = re.sub(citation_pattern, replace_citation, analysis_text)
    
    return clickable_text

def display_citations_separately(analysis_text: str, papers: list, analysis_papers: list = None, search_mode: str = "all_keywords", include_references: bool = True) -> str:
    """
    Display citations separately at the end, with different sections for OR queries.
    """
    if not papers:
        return analysis_text
    
    # Make inline citations clickable for analysis papers
    if analysis_papers:
        analysis_text = make_inline_citations_clickable(analysis_text, analysis_papers)
    
    # Only add references section if requested
    if not include_references:
        return analysis_text
    
    citations_section = "\n\n---\n\n### References\n\n"
    
    if search_mode == "any_keyword" and analysis_papers:
        # For OR queries: Separate analysis papers from additional papers
        citations_section += "#### References Used in Analysis\n\n"
        
        # Show papers used in analysis (top 15)
        for i, paper in enumerate(analysis_papers):
            meta = paper.get('metadata', {})
            title = meta.get('title', 'N/A')
            link = get_paper_link(meta)
            
            if link != "Not available":
                citations_section += f"**[{i+1}]** [{title}]({link})\n\n"
            else:
                citations_section += f"**[{i+1}]** {title}\n\n"
        
        # Show additional papers found in search
        additional_papers = [p for p in papers if p not in analysis_papers]
        if additional_papers:
            citations_section += "#### Additional References Found\n\n"
            start_num = len(analysis_papers) + 1
            
            for i, paper in enumerate(additional_papers):
                meta = paper.get('metadata', {})
                title = meta.get('title', 'N/A')
                link = get_paper_link(meta)
                
                if link != "Not available":
                    citations_section += f"**[{start_num + i}]** [{title}]({link})\n\n"
                else:
                    citations_section += f"**[{start_num + i}]** {title}\n\n"
    else:
        # For AND queries or when no analysis_papers specified: Show all papers normally
        for i, paper in enumerate(papers):
            meta = paper.get('metadata', {})
            title = meta.get('title', 'N/A')
            link = get_paper_link(meta)
            
            if link != "Not available":
                citations_section += f"**[{i+1}]** [{title}]({link})\n\n"
            else:
                citations_section += f"**[{i+1}]** {title}\n\n"
    
    return analysis_text + citations_section


def perform_custom_search(keywords: list, uploaded_papers: list) -> tuple[list, int]:
    """
    Performs search only on uploaded papers using keyword matching.
    """
    if not uploaded_papers:
        return [], 0
    
    # Filter uploaded papers based on keywords
    matching_papers = []
    
    for paper in uploaded_papers:
        # Combine all searchable text
        searchable_text = ""
        if 'metadata' in paper:
            metadata = paper['metadata']
            searchable_text += metadata.get('title', '').lower() + " "
            searchable_text += metadata.get('abstract', '').lower() + " "
        
        if 'content' in paper:
            searchable_text += paper['content'].lower()
        
        # Check if any keyword matches
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in searchable_text:
                keyword_matches += 1
        
        # Include paper if it matches at least one keyword
        if keyword_matches > 0:
            paper['keyword_matches'] = keyword_matches
            paper['relevance_score'] = keyword_matches / len(keywords)  # Simple relevance score
            matching_papers.append(paper)
    
    # Sort by relevance score (keyword matches / total keywords)
    matching_papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return matching_papers, len(matching_papers)

def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 100, score_threshold: float = 0.005, max_final_results: int = 15, search_mode: str = "all_keywords") -> tuple[list, int]:
    """
    Performs a search with different strategies based on search_mode:
    1. "all_keywords": Elasticsearch AND search with relevance scoring
    2. "any_keyword": Single-stage search (Elasticsearch OR only, return ALL papers)
    Returns a tuple: (list of papers, total number of papers found).
    """
    # Determine the operator based on search mode
    operator = "AND" if search_mode == "all_keywords" else "OR"
    
    if search_mode == "all_keywords":
        # For AND queries: Use the original two-stage hybrid approach
        return perform_and_search(keywords, time_filter_dict, n_results, score_threshold, max_final_results)
    else:
        # For OR queries: Return ALL papers found, no filtering
        return perform_or_search(keywords, time_filter_dict, n_results)

def perform_and_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 100, score_threshold: float = 0.005, max_final_results: int = 15) -> tuple[list, int]:
    """
    Performs Elasticsearch AND search with relevance scoring for AND queries.
    """
    # Stage 1: The Hard Filter. This is the most important step.
    es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="AND")

    # Create a set of valid paper IDs from the Elasticsearch search for efficient lookup.
    valid_paper_ids = {hit['_id'] for hit in es_results}
    total_papers_found = len(valid_paper_ids)

    # If the search returns no results, we stop immediately.
    if not valid_paper_ids:
        return [], 0 # Return an empty list and a count of 0

    # Process Elasticsearch results and create relevance scores
    fused_scores = defaultdict(lambda: {'score': 0, 'doc': None})
    k = 60 # Relevance scoring constant

    # Process Elasticsearch results (all of these are guaranteed to be valid).
    for i, hit in enumerate(es_results):
        rank = i + 1
        paper_id = hit['_id']
        fused_scores[paper_id]['score'] += 1 / (k + rank)
        doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
        fused_scores[paper_id]['doc'] = doc_content

    # Filter out any entries that somehow didn't get a 'doc' object.
    valid_fused_results = [item for item in fused_scores.values() if item['doc'] is not None]

    # Sort the combined results by the fused relevance score.
    sorted_fused_results = sorted(valid_fused_results, key=lambda x: x['score'], reverse=True)
    
    # Create the final list, filtered by a minimum score and limited by the max_final_results parameter (now 15).
    final_paper_list = [
        item['doc'] for item in sorted_fused_results 
        if item['score'] >= score_threshold
    ][:max_final_results]

    return final_paper_list, total_papers_found

def perform_or_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 100) -> tuple[list, int]:
    """
    Performs an OR search returning ALL papers found, sorted by Elasticsearch relevance score.
    """
    # Get ALL papers that contain at least one keyword
    es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="OR")
    
    # Convert to the expected format and preserve relevance scores
    all_papers = []
    for hit in es_results:
        paper_id = hit['_id']
        relevance_score = hit.get('_score', 0.0)  # Get Elasticsearch relevance score
        doc_content = {
            'paper_id': paper_id, 
            'metadata': hit['_source'], 
            'content': hit['_source'].get('content', ''),
            'relevance_score': relevance_score  # Store the relevance score
        }
        all_papers.append(doc_content)
    
    # Sort papers by relevance score (highest first)
    all_papers.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
    
    total_papers_found = len(all_papers)
    
    # Return ALL papers found, sorted by relevance
    return all_papers, total_papers_found


# <<< MODIFICATION: Updated this function to handle the new return values from perform_hybrid_search >>>
def process_keyword_search(keywords: list, time_filter_type: str | None, search_mode: str = "all_keywords") -> tuple[str | None, list, int]:
    if not keywords:
        st.error("Please select at least one keyword.")
        return None, [], 0

    # Loading is now handled at the UI level
    time_filter_dict = None
    now = datetime.datetime.now()
    # Use 2025 since that's the year of your papers
    data_year = 2025
    
    if time_filter_type == "Current year":
        # Search for 2025 papers in the format "dd MMM yyyy" (e.g., "07 Aug 2025")
        time_filter_dict = {"gte": f"01 Jan {data_year}", "lte": f"31 Dec {data_year}"}
    elif time_filter_type == "Last 3 months":
        # For last 3 months, go back 90 days from current date but use 2025 year
        three_months_ago = now - datetime.timedelta(days=90)
        time_filter_dict = {"gte": f"01 Jan {data_year}"}  # From start of 2025
    elif time_filter_type == "Last 6 months":
        # For last 6 months, go back 180 days from current date but use 2025 year
        six_months_ago = now - datetime.timedelta(days=180)
        time_filter_dict = {"gte": f"01 Jan {data_year}"}  # From start of 2025
    elif time_filter_type in ["January", "February", "March", "April", "May", "June", 
                             "July", "August", "September", "October", "November", "December"]:
        # Map month names to abbreviations and create date range in "dd MMM yyyy" format
        month_map = {
            "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr", 
            "May": "May", "June": "Jun", "July": "Jul", "August": "Aug", 
            "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"
        }
        next_month_map = {
            "January": "Feb", "February": "Mar", "March": "Apr", "April": "May", 
            "May": "Jun", "June": "Jul", "July": "Aug", "August": "Sep", 
            "September": "Oct", "October": "Nov", "November": "Dec", "December": "Jan"
        }
        month_abbr = month_map[time_filter_type]
        next_month_abbr = next_month_map[time_filter_type]
        next_year = data_year + 1 if time_filter_type == "December" else data_year
        time_filter_dict = {"gte": f"01 {month_abbr} {data_year}", "lt": f"01 {next_month_abbr} {next_year}"}
    
    # Skip Elasticsearch time filtering - we'll use GCS instead
    # For OR searches, increase the result limit to capture more papers
    # For AND searches, keep the original limit as they're more restrictive
    n_results_limit = 1000 if search_mode == "any_keyword" else 100
    
    all_papers, total_found = perform_hybrid_search(
        keywords, 
        time_filter_dict=None,  # No ES time filtering
        n_results=n_results_limit, 
        max_final_results=15,
        search_mode=search_mode
    )
    
    # Apply GCS-based time filtering if needed
    if time_filter_type != "All time" and all_papers:
        all_papers = filter_papers_by_gcs_dates(all_papers, time_filter_type)
        total_found = len(all_papers)
    
    if not all_papers:
        search_mode_text = "ALL of the selected keywords" if search_mode == "all_keywords" else "AT LEAST ONE of the selected keywords"
        st.error(f"No papers found that contain {search_mode_text} within the specified time window. Please try a different combination of keywords.")
        return None, [], 0

    # For OR queries: Use top 15 for analysis, but keep ALL papers for references
    # For AND queries: Use the already filtered top papers
    if search_mode == "any_keyword":
        # Papers are already sorted by relevance score from perform_or_search
        top_papers_for_analysis = all_papers[:15]  # Use top 15 most relevant papers for analysis
        papers_for_references = all_papers  # Use ALL papers for references
    else:
        # For AND queries, use the same papers for both analysis and references
        top_papers_for_analysis = all_papers
        papers_for_references = all_papers

    context = "You are a world-class scientific analyst and expert research assistant. Your primary objective is to generate the most detailed and extensive report possible based on the following scientific paper excerpts.\n\n"
    # <<< MODIFICATION: Build the context for the LLM using only the top 15 papers >>>
    for i, result in enumerate(top_papers_for_analysis):
        meta = result.get('metadata', {})
        title = meta.get('title', 'N/A')
        link = get_paper_link(meta)
        content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
        context += f"SOURCE [{i+1}]:\n"
        context += f"Title: {title}\n"
        context += f"Link: {link}\n"
        context += f"Content: {content_preview}\n---\n\n"
    
    prompt = f"""{context}
---
**CRITICAL TASK:**

You are a world-class scientific analyst. Your task is to generate an exceptionally detailed and extensive multi-part report based *only* on the provided paper sources. The final report should be substantial in length, reflecting a deep synthesis of information from all provided papers.

# Part 1: Thematic Analysis
For the sections "Key Methodological Advances," "Emerging Trends," and "Overall Summary," your analysis **MUST** be exhaustive. Generate at least **three long and detailed paragraphs** or a comprehensive multi-level bulleted list for each of these sections. Do not just list findings; you must deeply synthesize information across multiple sources, explain the significance, compare and contrast approaches, and build a compelling narrative about the state of the research.

   ### Diseases: List the specific diseases, conditions, or traits studied.
   ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries mentioned across the papers.
   ### Key Methodological Advances: Provide an in-depth description of significant methods, pipelines, or statistical approaches. Explain *why* they are important advances, how they differ from previous methods, and what new possibilities they unlock.
   ### Emerging Trends: Identify future directions and new research areas. Synthesize recurring themes to explain what trends are emerging in the field. Discuss the implications of these trends for science and medicine.
   ### Overall Summary: Provide a comprehensive, multi-paragraph textual summary of the key findings and clinical implications. This should be a full executive summary, not a brief conclusion.

**CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].` **IMPORTANT:** Limit citations to a maximum of 3 per sentence. If more than 3 sources support a finding, choose the 3 most relevant or representative sources.

# Part 2: Key Paper Summaries
Identify the top 3-5 most impactful papers from the sources and provide a detailed, one-paragraph summary for each.

**IMPORTANT:** Do NOT create a "References" section. Focus only on the thematic analysis and key paper summaries.

**CRITICAL INSTRUCTION FOR CITATIONS:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].` **IMPORTANT:** Always separate multiple citations with individual brackets, like `[2][3][4]` NOT `[234]`. **CRUCIAL:** In the Key Paper Summaries section, do NOT add citation numbers to the paper titles - only add citations at the end of the summary paragraphs. **FORMATTING RULE:** All citations MUST be in square brackets [1], [2], [3], etc. - never use unbracketed numbers for citations. **CITATION LIMIT:** Maximum 3 citations per sentence. If more than 3 sources support a finding, choose the 3 most relevant or representative sources.
"""
    analysis = post_message_vertexai(prompt)
    
    # Make citations clickable
    if analysis:
        # First, reload metadata from .metadata.json files to get the links
        papers_for_references = reload_paper_metadata(papers_for_references)
        top_papers_for_analysis = reload_paper_metadata(top_papers_for_analysis)
        analysis = display_citations_separately(analysis, papers_for_references, top_papers_for_analysis, search_mode)
    
    # <<< MODIFICATION: Return all three pieces of information >>>
    return analysis, papers_for_references, total_found

def generate_custom_summary(uploaded_papers):
    """Generate a summary of uploaded papers"""
    if not uploaded_papers:
        return "No papers uploaded."
    
    # Combine all paper content
    all_content = ""
    paper_titles = []
    
    for paper in uploaded_papers:
        title = paper['metadata'].get('title', 'Unknown Title')
        content = paper.get('content', '')
        paper_titles.append(title)
        all_content += f"\n\n--- {title} ---\n{content}"
    
    # Create summary prompt
    prompt = f"""
    Please provide a comprehensive summary of the following {len(uploaded_papers)} research paper(s):
    
    Papers: {', '.join(paper_titles)}
    
    Content:
    {all_content}
    
    Please provide:
    1. A brief overview of each paper
    2. Key findings and methodologies
    3. Common themes across the papers
    4. Overall conclusions and implications
    
    Keep the summary concise but informative.
    """
    
    return post_message_vertexai(prompt)

def display_paper_management():
    st.subheader("Upload PDF Files")
    st.info("Upload PDF files to generate custom summary of your documents.")

    uploaded_pdfs = st.file_uploader("Choose PDF files", accept_multiple_files=True, type=['pdf'], key="pdf_uploader_v2")
    
    if uploaded_pdfs and st.button("Add PDFs", type="primary"):
        with st.spinner("Processing PDF files..."):
            for uploaded_file in uploaded_pdfs:
                # Get the base name without extension
                pdf_base_name = os.path.splitext(os.path.basename(uploaded_file.name))[0]
                
                # Create basic metadata
                metadata = {
                    'title': pdf_base_name,
                    'abstract': 'No abstract available',
                    'publication_date': '2024-01-01',
                    'authors': ['Unknown'],
                    'url': '',
                    'doi_url': '',
                    'link': ''
                }
                
                # Extract PDF content
                pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
                paper_content = read_pdf_content(pdf_content_bytes)
                
                if paper_content:
                    # Store in user-specific session state for custom search
                    paper_data = {
                        'paper_id': f"uploaded_{pdf_base_name}",
                        'metadata': metadata,
                        'content': paper_content
                    }
                    uploaded_papers = get_user_session('uploaded_papers', [])
                    uploaded_papers.append(paper_data)
                    set_user_session('uploaded_papers', uploaded_papers)
                    st.success(f"Successfully processed '{uploaded_file.name}' (Content length: {len(paper_content)} chars)")
                else:
                    st.error(f"Could not read content from '{uploaded_file.name}'. The PDF might be corrupted or password-protected.")
        st.rerun()
    


def display_chat_history():
    st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
    
    # Get user-specific conversations
    conversations = get_user_session('conversations', {})
    if not conversations:
        st.caption("No past analyses found.")
        return

    grouped_convs = defaultdict(list)
    
    # Sort conversations by last interaction time (most recent first)
    def get_last_interaction_time(conv_id, conv_data):
        # Use last_interaction_time if available, otherwise fall back to creation time
        if 'last_interaction_time' in conv_data:
            return conv_data['last_interaction_time']
        
        # Fallback to creation time from conversation ID
        try:
            if conv_id.startswith('custom_summary_'):
                timestamp_str = conv_id.split('_', 2)[2]
            else:
                timestamp_str = conv_id.split('_')[1]
            return float(timestamp_str)
        except (IndexError, ValueError):
            return 0
    
    sorted_conv_ids = sorted(
        conversations.keys(), 
        key=lambda conv_id: get_last_interaction_time(conv_id, conversations[conv_id]),
        reverse=True
    )
    
    for conv_id in sorted_conv_ids:
        try:
            # Get creation date for grouping by month
            if conv_id.startswith('custom_summary_'):
                timestamp_str = conv_id.split('_', 2)[2]
            else:
                timestamp_str = conv_id.split('_')[1]
            
            ts = float(timestamp_str)
            conv_date = datetime.datetime.fromtimestamp(ts)
            month_key = conv_date.strftime("%Y-%m")
            title = conversations[conv_id].get("title", "Chat...")
            grouped_convs[month_key].append((conv_id, title))
        except (IndexError, ValueError):
            continue
    
    now = datetime.datetime.now()
    current_month_key = now.strftime("%Y-%m")
    
    for month_key in sorted(grouped_convs.keys(), reverse=True):
        if month_key == current_month_key:
            st.markdown("<h5>Recent</h5>", unsafe_allow_html=True)
        else:
            display_date = datetime.datetime.strptime(month_key, "%Y-%m")
            st.markdown(f"<h5>{display_date.strftime('%B %Y')}</h5>", unsafe_allow_html=True)

        for conv_id, title in grouped_convs[month_key]:
            if st.button(title, key=f"btn_{conv_id}", use_container_width=True):
                if get_user_session('active_conversation_id') != conv_id:
                    set_user_session('active_conversation_id', conv_id)
                    # Update last interaction time for this conversation
                    conversations[conv_id]['last_interaction_time'] = time.time()
                    set_user_session('conversations', conversations)
                    st.rerun()

def main():
    # Check authentication first
    auth_mgr = get_auth_manager()
    
    # Check for session restoration from localStorage
    if hasattr(auth_mgr, 'restore_session_from_localStorage'):
        # This will be handled by JavaScript in the auth manager
        pass
    
    if not auth_mgr.require_auth():
        show_login_page()
        return
    
    st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant", page_icon="polo-ggb-logo.png")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(current_dir, "style.css")
    local_css(style_path)
    initialize_session_state()

    with st.sidebar:
        # Show user info for all users
        if st.session_state.get('authenticated', False):
            st.markdown("---")
            st.markdown(f"**Logged in as:** {st.session_state.username}")
            
            # Get user role from auth manager
            auth_mgr = get_auth_manager()
            users = auth_mgr.load_users()
            user_role = users.get(st.session_state.username, {}).get('role', 'user')
            st.markdown(f"**Role:** {user_role.title()}")
        
        if st.button("➕ New Analysis", use_container_width=True):
            set_user_session('active_conversation_id', None)
            set_user_session('selected_keywords', [])
            set_user_session('search_mode', "all_keywords")
            # Custom summaries are now in chat history
            set_user_session('custom_summary_chat', [])  # Clear custom summary chat
            st.rerun()
        
        # Only show technical buttons for admin users
        user_role = users.get(st.session_state.username, {}).get('role', 'user')
        if user_role == 'admin':
            with st.expander("🔧 Technical Tools (Admin Only)"):
                if st.button("🔍 Debug Cloud Storage", use_container_width=True, help="Check what's stored in cloud storage"):
                    username = st.session_state.get('username')
                    if username:
                        debug_cloud_storage(username)
                    else:
                        st.error("No username found in session")
                
                if st.button("🔧 Fix Corrupted Data", use_container_width=True, help="Delete corrupted admin_data.json to use individual files"):
                    username = st.session_state.get('username')
                    if username:
                        fix_corrupted_data(username)
                    else:
                        st.error("No username found in session")
                
                if st.button("🔄 Manual Restore", use_container_width=True, help="Manually restore conversation history"):
                    username = st.session_state.get('username')
                    if username:
                        restore_user_data_from_cloud(username, silent=False)
                    else:
                        st.error("No username found in session")
                
                if st.button("🔍 Check Auth Manager", use_container_width=True, help="Check which authentication manager is being used"):
                    auth_mgr = get_auth_manager()
                    auth_type = type(auth_mgr).__name__
                    if auth_type == "AuthenticationManager":
                        st.success(f"✅ Using {auth_type} (Cloud Storage Enabled)")
                    else:
                        st.error(f"❌ Using {auth_type} (Local Storage Only - Data NOT saved to cloud)")
                        st.warning("This is why your data isn't appearing in cloud storage!")

        display_chat_history()




        st.markdown("---")
        with st.form(key="new_analysis_form"):
            st.subheader("Start a New Analysis")
            
            # Add data availability note - simple static version
            st.info("**Data available until:** end of September 2025")
            
            selected_keywords = st.multiselect("Select keywords", GENETICS_KEYWORDS, default=get_user_session('selected_keywords', []))
            
            # Search mode selection
            search_mode_options = {
                "all_keywords": "Find papers containing ALL keywords",
                "any_keyword": "Find papers containing AT LEAST ONE keyword"
            }
            search_mode_display = st.selectbox(
                "Search Mode", 
                options=list(search_mode_options.keys()),
                format_func=lambda x: search_mode_options[x],
                index=0 if get_user_session('search_mode', 'all_keywords') == 'all_keywords' else 1
            )
            
            time_filter_type = st.selectbox("Filter by Time Window", [
                "Current year", 
                "Last 3 months", 
                "Last 6 months", 
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ])
            
            if st.form_submit_button("Search & Analyze"):
                # Store user-specific form data
                set_user_session('selected_keywords', selected_keywords)
                set_user_session('search_mode', search_mode_display)
                # Clear custom summary when starting new analysis
                set_user_session('custom_summary_chat', [])
                # Set loading state
                st.session_state.is_loading_analysis = True
                st.session_state.loading_message = "Searching for highly relevant papers and generating a comprehensive, in-depth report..."
                st.rerun()
        
        # Handle loading state and process analysis
        if st.session_state.get('is_loading_analysis', False):
            # Show loading overlay
            show_loading_overlay(st.session_state.loading_message)
            
            # Process the analysis
            analysis_result, retrieved_papers, total_found = process_keyword_search(get_user_session('selected_keywords', []), time_filter_type, get_user_session('search_mode', 'all_keywords'))
            
            # Clear loading state
            st.session_state.is_loading_analysis = False
            
            if analysis_result:
                conv_id = f"conv_{time.time()}"
                search_mode_display = get_user_session('search_mode', 'all_keywords')
                selected_keywords = get_user_session('selected_keywords', [])
                search_mode_text = "ALL keywords" if search_mode_display == "all_keywords" else "AT LEAST ONE keyword"
                initial_message = {"role": "assistant", "content": f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    <h2 style="color: white; margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">Analysis Report</h2>
    <div style="color: #f0f0f0; font-size: 16px; margin-bottom: 8px;">
        <strong>Keywords:</strong> {', '.join(selected_keywords)}
    </div>
    <div style="color: #e0e0e0; font-size: 14px;">
        <strong>Search Mode:</strong> {search_mode_text}
    </div>
</div>

{analysis_result}
"""}
                title = generate_conversation_title(analysis_result)
                
                # Get user-specific conversations and add new one
                conversations = get_user_session('conversations', {})
                conversations[conv_id] = {
                    "title": title, 
                    "messages": [initial_message], 
                    "keywords": selected_keywords,
                    "search_mode": search_mode_display,
                    "retrieved_papers": retrieved_papers,
                    "total_papers_found": total_found,
                    "created_at": time.time(),
                    "last_interaction_time": time.time()
                }
                set_user_session('conversations', conversations)
                # Clear any previous analysis and set new one
                set_user_session('active_conversation_id', conv_id)
                # Custom summaries are now in chat history
                set_user_session('custom_summary_chat', [])  # Clear custom summary chat
                # Save user data to cloud
                save_user_data_to_cloud()
                st.rerun()
            else:
                st.error("Failed to generate analysis. Please try again.")

        st.markdown("---")
        
        # Display uploaded papers count
        uploaded_papers = get_user_session('uploaded_papers', [])
        if uploaded_papers:
            st.info(f"{len(uploaded_papers)} papers uploaded")
            with st.expander("View uploaded papers"):
                for i, paper in enumerate(uploaded_papers):
                    title = paper['metadata'].get('title', 'Unknown title')
                    st.write(f"{i+1}. {title}")
            
            # Custom summary button in sidebar
            if st.button("Generate Custom Summary", use_container_width=True, type="primary"):
                # Clear any active analysis and set custom summary generation
                set_user_session('active_conversation_id', None)
                st.session_state.generate_custom_summary = True
                # Set loading state for custom summary
                st.session_state.is_loading_analysis = True
                st.session_state.loading_message = "Generating summary of your uploaded papers..."
                st.rerun()
            
            # Custom summaries are now in chat history - no clear button needed
            
            # Show chat history if exists
            custom_summary_chat = get_user_session('custom_summary_chat', [])
            if custom_summary_chat:
                st.markdown("---")
                st.markdown("**Chat History:**")
                for i, message in enumerate(custom_summary_chat[-3:]):  # Show last 3 messages
                    if message["role"] == "user":
                        st.caption(f"**You:** {message['content'][:50]}...")
                    else:
                        st.caption(f"**Assistant:** {message['content'][:50]}...")
                
                if len(custom_summary_chat) > 3:
                    st.caption(f"... and {len(custom_summary_chat) - 3} more messages")
            
            if st.button("Clear uploaded papers"):
                set_user_session('uploaded_papers', [])
                st.rerun()
        else:
            st.caption("No papers uploaded yet")
        
        with st.expander("Upload PDF Files"):
            display_paper_management()
        
        # Logout button at the bottom
        st.markdown("---")
        show_logout_button()

    # CSS and JavaScript for clickable citations
    st.markdown("""
    <style>
    .citation-link {
        color: #007bff;
        cursor: pointer;
        text-decoration: underline;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        transition: all 0.2s ease;
        display: inline-block;
    }
    .citation-link:hover {
        color: #0056b3;
        background-color: #e3f2fd;
        transform: scale(1.05);
    }
    
    /* Make sidebar wider */
    .css-1d391kg {
        width: 350px !important;
    }
    
    /* Adjust main content area */
    .css-1y0tads {
        margin-left: 350px !important;
    }
    
    /* Ensure sidebar content fits better */
    .css-1lcbmhc .css-1y0tads {
        padding-left: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1>🧬 POLO-GGB RESEARCH ASSISTANT</h1>", unsafe_allow_html=True)

    # Show loading overlay if analysis is in progress (but not for custom summary)
    if st.session_state.get('is_loading_analysis', False):
        show_loading_overlay(st.session_state.loading_message)
        return  # Don't render the rest of the page while loading

    # Handle custom summary generation
    if st.session_state.get('generate_custom_summary', False):
        st.session_state.generate_custom_summary = False  # Reset the flag
        
        # Generate the summary immediately
        summary = generate_custom_summary(get_user_session('uploaded_papers', []))
        
        if summary:
            # Summary is now stored in chat history
            
            # Add custom summary to chat history with better title and metadata
            conv_id = f"custom_summary_{time.time()}"
            
            # Generate a brief, descriptive title
            def generate_custom_summary_title(papers, summary_text):
                paper_count = len(papers)
                
                # Try to extract key topics from the summary
                summary_lower = summary_text.lower()
                topics = []
                
                # Common research topics
                if any(word in summary_lower for word in ['sustainability', 'sustainable', 'environment']):
                    topics.append('Sustainability')
                if any(word in summary_lower for word in ['machine learning', 'ai', 'artificial intelligence', 'ml']):
                    topics.append('AI/ML')
                if any(word in summary_lower for word in ['genetics', 'genetic', 'dna', 'genome']):
                    topics.append('Genetics')
                if any(word in summary_lower for word in ['disease', 'medical', 'health', 'clinical']):
                    topics.append('Medical')
                if any(word in summary_lower for word in ['prediction', 'predictive', 'modeling']):
                    topics.append('Prediction')
                if any(word in summary_lower for word in ['risk', 'risk assessment']):
                    topics.append('Risk Analysis')
                if any(word in summary_lower for word in ['leather', 'industry', 'manufacturing']):
                    topics.append('Industry')
                if any(word in summary_lower for word in ['reporting', 'disclosure', 'transparency']):
                    topics.append('Reporting')
                
                # Create title based on topics found
                if topics:
                    topic_str = ', '.join(topics[:2])  # Max 2 topics
                    return topic_str
                else:
                    # Fallback to first few words of summary
                    first_words = ' '.join(summary_text.split()[:4])
                    return f"{first_words}..."
            
            uploaded_papers = get_user_session('uploaded_papers', [])
            title = generate_custom_summary_title(uploaded_papers, summary)
            
            initial_message = {
                "role": "assistant", 
                "content": f"**Custom Summary of {len(uploaded_papers)} Uploaded Papers**\n\n{summary}"
            }
            
            # Get user-specific conversations and add new one
            conversations = get_user_session('conversations', {})
            conversations[conv_id] = {
                "title": title,
                "messages": [initial_message],
                "keywords": ["Custom Summary"],
                "search_mode": "custom",
                "retrieved_papers": uploaded_papers,
                "total_papers_found": len(uploaded_papers),
                "created_at": time.time(),
                "last_interaction_time": time.time(),
                "paper_count": len(uploaded_papers)
            }
            set_user_session('conversations', conversations)
            
            # Set this as the active conversation so user can immediately interact
            set_user_session('active_conversation_id', conv_id)
            
            # Save user data to cloud
            save_user_data_to_cloud()
            
            # Summary is now permanently stored in chat history
        else:
            st.error("Failed to generate summary. Please try again.")
        
        # Clear loading state and force rerun to show results immediately
        st.session_state.is_loading_analysis = False
        st.rerun()

    # Custom summaries are now handled through chat history - no separate display needed

    # Show default message only if no active conversation
    active_conversation_id = get_user_session('active_conversation_id')
    if active_conversation_id is None:
        st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
    elif active_conversation_id is not None:
        active_id = active_conversation_id
        conversations = get_user_session('conversations', {})
        active_conv = conversations[active_id]
        
        for message_index, message in enumerate(active_conv["messages"]):
            avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"], unsafe_allow_html=True)
                
                # Show papers section only for the first assistant message and regular analyses, not custom summaries
                if (message["role"] == "assistant" and message_index == 0 and 
                    "retrieved_papers" in active_conv and active_conv["retrieved_papers"] and 
                    active_conv.get("search_mode") != "custom"):
                    with st.expander("View and Download Retrieved Papers for this Analysis"):
                        # Display papers without the count message
                        
                        for paper_index, paper in enumerate(active_conv["retrieved_papers"]):
                            meta = paper.get('metadata', {})
                            title = meta.get('title', 'N/A')
                            paper_id = paper.get('paper_id')

                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**{paper_index+1}. {title}**")
                            with col2:
                                if paper_id:
                                    pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
                                    if pdf_bytes:
                                        st.download_button(
                                            label="Download PDF",
                                            data=pdf_bytes,
                                            file_name=paper_id,
                                            mime="application/pdf",
                                            key=f"download_{active_id}_{paper_id}"
                                        )




        if prompt := st.chat_input("Ask a follow-up question..."):
            active_conv["messages"].append({"role": "user", "content": prompt})
            # Update last interaction time for this conversation
            active_conv['last_interaction_time'] = time.time()
            # Save updated conversations
            set_user_session('conversations', conversations)
            st.rerun()

    active_conversation_id = get_user_session('active_conversation_id')
    conversations = get_user_session('conversations', {})
    if active_conversation_id and conversations[active_conversation_id]["messages"][-1]["role"] == "user":
        active_conv = conversations[active_conversation_id]
        with st.spinner("Thinking..."):
            chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in active_conv["messages"]])
            full_context = ""
            if active_conv.get("retrieved_papers"):
                full_context += "Here is the full context of every paper found in the initial analysis:\n\n"
                for i, paper in enumerate(active_conv["retrieved_papers"]):
                    meta = paper.get('metadata', {})
                    title = meta.get('title', 'N/A')
                    link = get_paper_link(meta)
                    content_preview = (meta.get('abstract') or paper.get('content') or '')[:4000]
                    full_context += f"SOURCE [{i+1}]:\nTitle: {title}\nLink: {link}\nContent: {content_preview}\n---\n\n"
            
            full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
Your task is to answer the user's last message based on the chat history and the full context from the paper sources provided below.

**CITATION INSTRUCTIONS:** When referencing sources, use citation markers in square brackets like [1], [2], [3], etc. Separate multiple citations with individual brackets like [2][3][4]. **IMPORTANT:** Limit citations to a maximum of 3 per sentence. If more than 3 sources support a finding, choose the 3 most relevant or representative sources.

--- CHAT HISTORY ---
{chat_history}
--- END CHAT HISTORY ---

--- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
{full_context}
--- END FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---

Assistant Response:"""
            
            response_text = post_message_vertexai(full_prompt)
            if response_text:
                # Make citations clickable in follow-up responses
                retrieved_papers = active_conv.get("retrieved_papers", [])
                search_mode = active_conv.get("search_mode", "all_keywords")
                
                # For follow-up responses, use all retrieved papers to make citations clickable but don't include references section
                response_text = display_citations_separately(response_text, retrieved_papers, retrieved_papers, search_mode, include_references=False)
                active_conv["messages"].append({"role": "assistant", "content": response_text})
                # Update last interaction time for this conversation
                active_conv['last_interaction_time'] = time.time()
                # Save updated conversations
                set_user_session('conversations', conversations)
                # Save user data immediately
                save_user_data_to_cloud()
                st.rerun()

if __name__ == "__main__":
    main()