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
from typing import List, Dict, Any
import datetime
from dateutil import parser as date_parser
from collections import defaultdict

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
from google.api_core.exceptions import NotFound


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(_file_))))

try:
    from elasticsearch_utils import get_es_manager
except ImportError as e:
    st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
    st.stop()

# --- App Configuration & Constants ---
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(_file_)), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    st.error("Configuration file 'config/config.yaml' not found.")
    st.stop()
except Exception as e:
    st.error(f"Error loading config.yaml: {e}")
    st.stop()

# --- Configuration from Streamlit Secrets ---
try:
    # --- Elastic Cloud Configuration ---
    ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
    ELASTIC_USER = st.secrets["elasticsearch"]["username"]
    ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

    # --- Vertex AI Configurations ---
    # Reading lowercase keys to match secrets.toml best practice
    VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
    VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
    VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

    # --- GCS Configuration ---
    GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

    # --- Google Service Account Credentials ---
    # 1. Read the secret, which is a Streamlit AttrDict object.
    gcp_service_account_secret = st.secrets["gcp_service_account"]
    
    # 2. Convert the AttrDict to a standard Python dictionary.
    #    THIS IS THE FIX for the "not JSON serializable" error.
    GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
    # 3. Write the standard dictionary to a temporary file.
    with open("gcp_credentials.json", "w") as f:
        json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
    # 4. Set the environment variable for Google Cloud libraries to find the file.
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

except KeyError as e:
    st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
    st.stop()

# --- Interface Constants ---
GENETICS_KEYWORDS = [
    "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
]
USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# --- API and Helper Functions ---
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

def initialize_session_state():
    if 'es_manager' not in st.session_state:
        st.session_state.es_manager = get_es_manager(cloud_id=ELASTIC_CLOUD_ID, username=ELASTIC_USER, password=ELASTIC_PASSWORD)
    if 'conversations' not in st.session_state:
        st.session_state.conversations = {}
    if 'active_conversation_id' not in st.session_state:
        st.session_state.active_conversation_id = None
    if 'selected_keywords' not in st.session_state:
        st.session_state.selected_keywords = []
    if 'search_mode' not in st.session_state:
        st.session_state.search_mode = "all_keywords"

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
        # Parse the date "07 Aug 2025"
        from dateutil import parser as date_parser
        parsed_date = date_parser.parse(publication_date)
        
        if time_filter_type == "All year":
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

def display_citations_separately(analysis_text: str, papers: list, analysis_papers: list = None, search_mode: str = "all_keywords") -> str:
    """
    Display citations separately at the end, with different sections for OR queries.
    """
    if not papers:
        return analysis_text
    
    # Make inline citations clickable for analysis papers
    if analysis_papers:
        analysis_text = make_inline_citations_clickable(analysis_text, analysis_papers)
    
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
                citations_section += f"*[{i+1}]* [{title}]({link})\n\n"
            else:
                citations_section += f"*[{i+1}]* {title}\n\n"
        
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
                    citations_section += f"*[{start_num + i}]* [{title}]({link})\n\n"
                else:
                    citations_section += f"*[{start_num + i}]* {title}\n\n"
    else:
        # For AND queries or when no analysis_papers specified: Show all papers normally
        for i, paper in enumerate(papers):
            meta = paper.get('metadata', {})
            title = meta.get('title', 'N/A')
            link = get_paper_link(meta)
            
            if link != "Not available":
                citations_section += f"*[{i+1}]* [{title}]({link})\n\n"
            else:
                citations_section += f"*[{i+1}]* {title}\n\n"
    
    return analysis_text + citations_section


# <<< MODIFICATION: The entire search function is redesigned for accuracy >>>
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
    Performs a simple OR search returning ALL papers found.
    """
    # Get ALL papers that contain at least one keyword
    es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="OR")
    
    # Convert to the expected format
    all_papers = []
    for hit in es_results:
        paper_id = hit['_id']
        doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
        all_papers.append(doc_content)
    
    total_papers_found = len(all_papers)
    
    # Return ALL papers found (no filtering)
    return all_papers, total_papers_found


# <<< MODIFICATION: Updated this function to handle the new return values from perform_hybrid_search >>>
def process_keyword_search(keywords: list, time_filter_type: str | None, search_mode: str = "all_keywords") -> tuple[str | None, list, int]:
    if not keywords:
        st.error("Please select at least one keyword.")
        return None, [], 0

    with st.spinner("Searching for highly relevant papers and generating a comprehensive, in-depth report..."):
        time_filter_dict = None
        now = datetime.datetime.now()
        # Use 2025 since that's the year of your papers
        data_year = 2025
        
        if time_filter_type == "All time":
            time_filter_dict = None  # No time filter
        elif time_filter_type == "All year":
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
        all_papers, total_found = perform_hybrid_search(
            keywords, 
            time_filter_dict=None,  # No ES time filtering
            n_results=100, 
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
            # Sort all papers by relevance (simple sort by title for now, could be improved)
            sorted_papers = sorted(all_papers, key=lambda x: x.get('metadata', {}).get('title', ''))
            top_papers_for_analysis = sorted_papers[:15]  # Use top 15 for analysis
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
*CRITICAL TASK:*

You are a world-class scientific analyst. Your task is to generate an exceptionally detailed and extensive multi-part report based only on the provided paper sources. The final report should be substantial in length, reflecting a deep synthesis of information from all provided papers.

*Part 1: Thematic Analysis*
For the sections "Key Methodological Advances," "Emerging Trends," and "Overall Summary," your analysis *MUST* be exhaustive. Generate at least *three long and detailed paragraphs* or a comprehensive multi-level bulleted list for each of these sections. Do not just list findings; you must deeply synthesize information across multiple sources, explain the significance, compare and contrast approaches, and build a compelling narrative about the state of the research.

   ### Diseases: List the specific diseases, conditions, or traits studied.
   ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries mentioned across the papers.
   ### Key Methodological Advances: Provide an in-depth description of significant methods, pipelines, or statistical approaches. Explain why they are important advances, how they differ from previous methods, and what new possibilities they unlock.
   ### Emerging Trends: Identify future directions and new research areas. Synthesize recurring themes to explain what trends are emerging in the field. Discuss the implications of these trends for science and medicine.
   ### Overall Summary: Provide a comprehensive, multi-paragraph textual summary of the key findings and clinical implications. This should be a full executive summary, not a brief conclusion.

*CRITICAL INSTRUCTION FOR PART 1:* At the end of every sentence or key finding that you derive from a source, you *MUST* include a citation marker referencing the source's number in brackets. For example: This new method improves risk prediction [1]. Multiple sources can be cited like This was observed in several cohorts [2][3].

*Part 2: Key Paper Summaries*
Create a new section titled ### Key Paper Summaries. Under this heading, identify the top 3-5 most impactful papers from the sources and provide a detailed, one-paragraph summary for each.

*IMPORTANT:* Do NOT create a "References" section. Focus only on the thematic analysis and key paper summaries.

*CRITICAL INSTRUCTION FOR CITATIONS:* At the end of every sentence or key finding that you derive from a source, you *MUST* include a citation marker referencing the source's number in brackets. For example: This new method improves risk prediction [1]. Multiple sources can be cited like This was observed in several cohorts [2][3]. *IMPORTANT:* Always separate multiple citations with individual brackets, like [2][3][4] NOT [234]. *CRUCIAL:* In the Key Paper Summaries section, do NOT add citation numbers to the paper titles - only add citations at the end of the summary paragraphs. *FORMATTING RULE:* All citations MUST be in square brackets [1], [2], [3], etc. - never use unbracketed numbers for citations.
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

def display_paper_management():
    st.subheader("Add Papers to Database")
    st.info("Ensure every uploaded PDF has a corresponding JSON file with the exact same name (before the extension), even if they are in different subfolders.")

    uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
    uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
    
    if uploaded_pdfs and st.button("Add to Database"):
        # Create a dictionary of available JSON metadata, keyed by their base filename (without path)
        json_map = {os.path.splitext(os.path.basename(json_file.name))[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
        
        with st.spinner("Adding papers to databases..."):
            for uploaded_file in uploaded_pdfs:
                # <<< FIX: Get the base name WITHOUT the directory path to ensure a match >>>
                # Example: "pdf-metadata/paper1.pdf" -> "paper1"
                pdf_base_name = os.path.splitext(os.path.basename(uploaded_file.name))[0]
                
                # Use the clean base name to look up the metadata
                metadata = json_map.get(pdf_base_name)

                if metadata:
                    # If metadata is found, proceed with adding the paper
                    metadata['paper_id'] = uploaded_file.name
                    pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
                    paper_content = read_pdf_content(pdf_content_bytes)
                    if paper_content:
                        # Vector database is disabled - papers are only stored in Elasticsearch
                        st.success(f"✅ Successfully processed '{uploaded_file.name}' with full metadata.")
                    else:
                        st.error(f"❌ Could not read content from '{uploaded_file.name}'.")
                else:
                    # If no matching JSON is found, skip this PDF and warn the user
                    st.warning(f"⚠️ Skipped '{uploaded_file.name}' because a matching JSON metadata file was not found.")
        st.rerun()


def display_chat_history():
    st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
    if not st.session_state.conversations:
        st.caption("No past analyses found.")
        return

    grouped_convs = defaultdict(list)
    sorted_conv_ids = sorted(st.session_state.conversations.keys(), reverse=True)
    for conv_id in sorted_conv_ids:
        try:
            timestamp_str = conv_id.split('_')[1]
            ts = float(timestamp_str)
            conv_date = datetime.datetime.fromtimestamp(ts)
            month_key = conv_date.strftime("%Y-%m")
            title = st.session_state.conversations[conv_id].get("title", "Chat...")
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
                if st.session_state.active_conversation_id != conv_id:
                    st.session_state.active_conversation_id = conv_id
                    st.rerun()

def main():
    st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
    current_dir = os.path.dirname(os.path.abspath(_file_))
    style_path = os.path.join(current_dir, "style.css")
    local_css(style_path)
    initialize_session_state()

    with st.sidebar:
        if st.button("➕ New Analysis", use_container_width=True):
            st.session_state.active_conversation_id = None
            st.session_state.selected_keywords = []
            st.session_state.search_mode = "all_keywords"
            st.rerun()

        display_chat_history()




        st.markdown("---")
        with st.form(key="new_analysis_form"):
            st.subheader("Start a New Analysis")
            selected_keywords = st.multiselect("Select keywords", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []))
            
            # Search mode selection
            search_mode_options = {
                "all_keywords": "Find papers containing ALL keywords",
                "any_keyword": "Find papers containing AT LEAST ONE keyword"
            }
            search_mode_display = st.selectbox(
                "Search Mode", 
                options=list(search_mode_options.keys()),
                format_func=lambda x: search_mode_options[x],
                index=0 if st.session_state.get('search_mode', 'all_keywords') == 'all_keywords' else 1
            )
            
            time_filter_type = st.selectbox("Filter by Time Window", [
                "All time", 
                "All year", 
                "Last 3 months", 
                "Last 6 months", 
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ])
            
            if st.form_submit_button("Search & Analyze"):
                # Store the selected search mode in session state
                st.session_state.search_mode = search_mode_display
                
                # <<< MODIFICATION: Handle the new three-part return from the processing function >>>
                analysis_result, retrieved_papers, total_found = process_keyword_search(selected_keywords, time_filter_type, search_mode_display)
                if analysis_result:
                    conv_id = f"conv_{time.time()}"
                    search_mode_text = "ALL keywords" if search_mode_display == "all_keywords" else "AT LEAST ONE keyword"
                    initial_message = {"role": "assistant", "content": f"*Analysis for: {', '.join(selected_keywords)} (Search Mode: {search_mode_text})*\n\n{analysis_result}"}
                    title = generate_conversation_title(analysis_result)
                    st.session_state.conversations[conv_id] = {
                        "title": title, 
                        "messages": [initial_message], 
                        "keywords": selected_keywords,
                        "search_mode": search_mode_display,
                        "retrieved_papers": retrieved_papers,
                        "total_papers_found": total_found # <<< MODIFICATION: Store the total count
                    }
                    st.session_state.active_conversation_id = conv_id
                    st.rerun()

        st.markdown("---")
        with st.expander("Paper Management"):
            display_paper_management()

    # Add CSS and JavaScript for clickable citations
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
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

    if st.session_state.active_conversation_id is None:
        st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
    else:
        active_id = st.session_state.active_conversation_id
        active_conv = st.session_state.conversations[active_id]
        
        for message in active_conv["messages"]:
            avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"], unsafe_allow_html=True)

        if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
            with st.expander("View and Download Retrieved Papers for this Analysis"):
                # Display papers without the count message
                
                for paper_index, paper in enumerate(active_conv["retrieved_papers"]):
                    meta = paper.get('metadata', {})
                    title = meta.get('title', 'N/A')
                    paper_id = paper.get('paper_id')

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"*{paper_index+1}. {title}*")
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
            st.rerun()

    if st.session_state.active_conversation_id and st.session_state.conversations[st.session_state.active_conversation_id]["messages"][-1]["role"] == "user":
        active_conv = st.session_state.conversations[st.session_state.active_conversation_id]
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
                
                # For follow-up responses, we don't have separate analysis papers, so use all papers
                response_text = display_citations_separately(response_text, retrieved_papers, None, search_mode)
                active_conv["messages"].append({"role": "assistant", "content": response_text})
                st.rerun()

if _name_ == "_main_":
    main()