# app/main.py  as the main entry point for the Research Assistant application.
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
from streamlit_option_menu import option_menu
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
from google.api_core.exceptions import NotFound

# This code block must be at the absolute top of your script, before any other imports
# that might trigger a ChromaDB import.
if platform.system() == "Linux":
    try:
        # On Linux, default sqlite3 can be too old. We swap it with the pysqlite3-binary version.
        __import__("pysqlite3")
        import sys
        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    except ImportError:
        # This will be hit if pysqlite3-binary is not in requirements.txt
        st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

try:
    from elasticsearch_utils import get_es_manager
    from vector_db import get_vector_db
except ImportError as e:
    st.error(f"Failed to import a local module: {e}. Make sure elasticsearch_utils.py and vector_db.py are in the correct path.")
    st.stop()


# --- App Configuration & Constants ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Primary Application Configuration ---
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    st.error("Configuration file 'config/config.yaml' not found. Ensure it's in a 'config' directory one level above your app's directory.")
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


# Interface Constants
GENETICS_KEYWORDS = [
    "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
]
USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# Api call
def post_message_vertexai(input_text: str) -> str | None:
    try:
        vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
        model = GenerativeModel(VERTEXAI_MODEL_ID)
        generation_config = {"temperature": 0.2, "max_output_tokens": 4096}
        response = model.generate_content([input_text], generation_config=generation_config)
        return response.text
    except Exception as e:
        st.error(f"An error occurred with the Vertex AI API: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

# GCS download function
@st.cache_data
def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        file_bytes = blob.download_as_bytes()
        return file_bytes
    except NotFound:
        st.error(f"File not found in Google Cloud Storage: {blob_name}")
        return None
    except Exception as e:
        st.error(f"Failed to download from GCS: {e}")
        return None

# --- Core Application Functions ---
def initialize_session_state():
    if 'elasticsearch' not in st.session_state:
        # Pass the cloud credentials directly to the simplified manager
        st.session_state.es_manager = get_es_manager(
            cloud_id=ELASTIC_CLOUD_ID, 
            username=ELASTIC_USER, 
            password=ELASTIC_PASSWORD
        )
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = get_vector_db(_es_manager=st.session_state.es_manager)
    if 'conversations' not in st.session_state:
        st.session_state.conversations = {}
    if 'active_conversation_id' not in st.session_state:
        st.session_state.active_conversation_id = None
    if 'selected_keywords' not in st.session_state:
        st.session_state.selected_keywords = []

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

def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 10) -> list:
    vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
    es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results)
    fused_scores = {}
    k = 60
    for i, doc in enumerate(vector_results):
        rank = i + 1
        paper_id = doc.get('paper_id')
        if paper_id and paper_id not in fused_scores:
            fused_scores[paper_id] = {'score': 0, 'doc': doc}
            fused_scores[paper_id]['score'] += 1 / (k + rank)
    for i, hit in enumerate(es_results):
        rank = i + 1
        paper_id = hit['_id']
        if paper_id not in fused_scores:
            doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
            fused_scores[paper_id] = {'score': 0, 'doc': doc_content}
        if paper_id in fused_scores:
            fused_scores[paper_id]['score'] += 1 / (k + rank)
    sorted_fused_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
    return [item['doc'] for item in sorted_fused_results[:n_results]]

def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
    if not keywords:
        st.error("Please select at least one keyword.")
        return None, []
    with st.spinner("Searching papers and generating a structured report..."):
        time_filter_dict = None
        now = datetime.datetime.now()
        if time_filter_type == "Year" and selected_year:
            time_filter_dict = {"gte": f"{selected_year}-01-01", "lte": f"{selected_year}-12-31"}
        elif time_filter_type == "Month" and selected_month:
            year, month = map(int, selected_month.split('-'))
            time_filter_dict = {"gte": f"{year}-{month:02d}-01", "lt": f"{year}-{(month % 12) + 1:02d}-01" if month < 12 else f"{year+1}-01-01"}
        elif time_filter_type == "Last week":
            time_filter_dict = {"gte": (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}
        elif time_filter_type == "Last month":
            time_filter_dict = {"gte": (now - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}
        
        search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict)
        if not search_results:
            st.error("No papers found for the selected keywords and time window.")
            return None, []

        context = f"Based on a hybrid search for keywords: {', '.join(keywords)}\n\n"
        for result in search_results:
            meta = result.get('metadata', {})
            title = meta.get('title', 'N/A')
            pub_date = meta.get('publication_date', 'N/A')
            link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
            content_preview = (meta.get('abstract') or result.get('content') or '')[:1500]
            context += f"Title: {title}\nPublished: {pub_date}\nLink: {link}\nPreview: {content_preview}...\n---\n"
        
        prompt = f"""Polo-GGB Assistant. As the expert AI assistant of the Stat4Value, I need your help to perform a detailed analysis. Your task is to analyze the following excerpts from scientific papers and generate a structured report. Based *only* on the context provided below, please generate the report using the following markdown structure. If information for a specific section is not available in the provided excerpts, you MUST write 'Information not available in the provided excerpts.' for that section.
--- CONTEXT FROM PAPERS ---
{context}
--- END CONTEXT ---
### Diseases
List the specific diseases, conditions, or traits studied in these papers.
### Sample Size & Genetic Ancestry
Summarize the sample sizes (e.g., number of participants) and the genetic ancestries (e.g., European, African, East Asian) of the study populations mentioned.
### Key Methodological Advances
Describe any new or significant methods, PRS pipelines, tools, or statistical approaches discussed in the papers.
### Emerging Trends
Identify any future directions, new research areas, or repeated themes that suggest emerging trends in the field based on these papers.
### Chatbot Summary
Provide a concise, overall textual summary of the key findings and clinical implications from the provided excerpts. This should be a general overview."""

        analysis = post_message_vertexai(prompt)
        return analysis, search_results

def display_paper_management():
    st.subheader("Add Papers to Database")
    uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
    uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
    json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
    if uploaded_pdfs and st.button("Add to Database"):
        with st.spinner("Adding papers to databases... This may take a moment."):
            for uploaded_file in uploaded_pdfs:
                base_name = os.path.splitext(uploaded_file.name)[0]
                metadata = json_map.get(base_name, {'title': base_name})
                metadata['paper_id'] = uploaded_file.name
                pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
                paper_content = read_pdf_content(pdf_content_bytes)
                if paper_content:
                    st.session_state.vector_db.add_paper(paper_id=uploaded_file.name, content=paper_content, metadata=metadata)
                    st.success(f"Successfully added '{uploaded_file.name}' to the database.")
        st.rerun()

def main():
    st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
    local_css("style.css")
    initialize_session_state()

    with st.sidebar:
        st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
        conv_id_to_title_map = {conv_id: data.get("title", "Chat...") for conv_id, data in st.session_state.conversations.items()}
        title_to_conv_id_map = {v: k for k, v in conv_id_to_title_map.items()}
        ordered_titles = [conv_id_to_title_map[cid] for cid in reversed(list(st.session_state.conversations.keys()))]
        active_title = conv_id_to_title_map.get(st.session_state.active_conversation_id)
        try:
            default_index = ordered_titles.index(active_title) + 1 if active_title else 0
        except ValueError:
            default_index = 0
        selected_option = option_menu(
            menu_title=None, options=["➕ New Analysis"] + ordered_titles,
            icons=['plus-square-dotted'] + ['journals'] * len(ordered_titles),
            default_index=default_index,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#007bff", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e9ecef"},
                "nav-link-selected": {"background-color": "#cce5ff", "color": "#0056b3", "font-weight": "600"},
            })
        intended_conv_id = title_to_conv_id_map.get(selected_option) if selected_option != "➕ New Analysis" else None
        if st.session_state.active_conversation_id != intended_conv_id:
            st.session_state.active_conversation_id = intended_conv_id
            if intended_conv_id is None:
                st.session_state.selected_keywords = []
            st.rerun()
        st.markdown("---")
        with st.form(key="new_analysis_form"):
            st.subheader("Start a New Analysis")
            selected_keywords = st.multiselect("Select keywords (up to 3)", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []), max_selections=3)
            time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
            selected_year, selected_month = None, None
            if time_filter_type == "Year":
                import pandas as pd
                all_papers = st.session_state.vector_db.get_all_papers()
                dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
                years = pd.to_datetime(dates, errors='coerce').dropna().year.unique()
                selected_year = st.selectbox("Select year", sorted(years, reverse=True)) if len(years) > 0 else st.write("No papers with years found.")
            elif time_filter_type == "Month":
                import pandas as pd
                all_papers = st.session_state.vector_db.get_all_papers()
                dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
                months = pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique()
                selected_month = st.selectbox("Select month", sorted(months, reverse=True)) if len(months) > 0 else st.write("No papers with months found.")
            
            if st.form_submit_button("Search & Analyze"):
                analysis_result, retrieved_papers = process_keyword_search(selected_keywords, time_filter_type, selected_year, selected_month)
                if analysis_result:
                    conv_id = f"conv_{time.time()}"
                    initial_message = {"role": "assistant", "content": f"**Analysis for: {', '.join(selected_keywords)}**\n\n{analysis_result}"}
                    title = generate_conversation_title(analysis_result)
                    st.session_state.conversations[conv_id] = {
                        "title": title, 
                        "messages": [initial_message], 
                        "keywords": selected_keywords,
                        "retrieved_papers": retrieved_papers
                    }
                    st.session_state.active_conversation_id = conv_id
                    st.rerun()

        st.markdown("---")
        with st.expander("Paper Management"):
            display_paper_management()

    st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

    if st.session_state.active_conversation_id is None:
        st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
    else:
        active_id = st.session_state.active_conversation_id
        active_conv = st.session_state.conversations[active_id]
        
        for message in active_conv["messages"]:
            avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

        if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
            with st.expander("View Retrieved Papers for this Analysis"):
                for i, paper in enumerate(active_conv["retrieved_papers"]):
                    meta = paper.get('metadata', {})
                    title = meta.get('title', 'N/A')
                    link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'N/A')
                    paper_id = paper.get('paper_id')

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{i+1}. {title}**")
                        if link != 'N/A':
                            st.markdown(f"   - Link: [{link}]({link})")
                    with col2:
                        if paper_id:
                            pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
                            if pdf_bytes:
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_bytes,
                                    file_name=paper_id,
                                    mime="application/pdf",
                                    key=f"download_{paper_id}_{i}"
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
                for paper in active_conv["retrieved_papers"]:
                    meta = paper.get('metadata', {})
                    title = meta.get('title', 'N/A')
                    link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
                    content_preview = (meta.get('abstract') or paper.get('content') or '')[:1000]
                    full_context += f"Title: {title}\nLink: {link}\nPreview: {content_preview}...\n---\n"
            full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
Your task is to answer the user's follow-up question based on the chat history and the full context of the papers provided below.
When the user asks you to list the papers, you MUST list ALL papers provided in the context below. Do not omit, summarize, or change any.
Format the response as a numbered list. For each paper, provide its full title and a clickable markdown link if the link is available in the context.
--- CHAT HISTORY ---
{chat_history}
--- END CHAT HISTORY ---
--- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
{full_context}
--- END FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
Assistant Response:"""
            
            response_text = post_message_vertexai(full_prompt)
            if response_text:
                active_conv["messages"].append({"role": "assistant", "content": response_text})
                st.rerun()

if __name__ == "__main__":
    main()
