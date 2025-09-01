# # app/main.py  as the main entry point for the Research Assistant application.
# import streamlit as st
# import platform
# import requests
# import time
# import json
# import PyPDF2
# import io
# import yaml
# import os
# import sys
# from typing import List, Dict, Any
# import datetime
# from dateutil import parser as date_parser
# from streamlit_option_menu import option_menu
# import vertexai
# from vertexai.generative_models import GenerativeModel
# from google.cloud import storage
# from google.api_core.exceptions import NotFound

# # This code block must be at the absolute top of your script, before any other imports
# # that might trigger a ChromaDB import.
# if platform.system() == "Linux":
#     try:
#         # On Linux, default sqlite3 can be too old. We swap it with the pysqlite3-binary version.
#         __import__("pysqlite3")
#         import sys
#         sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
#     except ImportError:
#         # This will be hit if pysqlite3-binary is not in requirements.txt
#         st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

# try:
#     from elasticsearch_utils import get_es_manager
#     from vector_db import get_vector_db
# except ImportError as e:
#     st.error(f"Failed to import a local module: {e}. Make sure elasticsearch_utils.py and vector_db.py are in the correct path.")
#     st.stop()


# # --- App Configuration & Constants ---
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # --- Primary Application Configuration ---
# try:
#     config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
#     with open(config_path, 'r') as file:
#         config = yaml.safe_load(file)
# except FileNotFoundError:
#     st.error("Configuration file 'config/config.yaml' not found. Ensure it's in a 'config' directory one level above your app's directory.")
#     st.stop()
# except Exception as e:
#     st.error(f"Error loading config.yaml: {e}")
#     st.stop()

# # --- Configuration from Streamlit Secrets ---
# try:
#     # --- Elastic Cloud Configuration ---
#     ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
#     ELASTIC_USER = st.secrets["elasticsearch"]["username"]
#     ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

#     # --- Vertex AI Configurations ---
#     # Reading lowercase keys to match secrets.toml best practice
#     VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
#     VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
#     VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

#     # --- GCS Configuration ---
#     GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

#     # --- Google Service Account Credentials ---
#     # 1. Read the secret, which is a Streamlit AttrDict object.
#     gcp_service_account_secret = st.secrets["gcp_service_account"]
    
#     # 2. Convert the AttrDict to a standard Python dictionary.
#     #    THIS IS THE FIX for the "not JSON serializable" error.
#     GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
#     # 3. Write the standard dictionary to a temporary file.
#     with open("gcp_credentials.json", "w") as f:
#         json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
#     # 4. Set the environment variable for Google Cloud libraries to find the file.
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

# except KeyError as e:
#     st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
#     st.stop()


# # Interface Constants
# GENETICS_KEYWORDS = [
#     "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
# ]
# USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
# BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# # Api call
# def post_message_vertexai(input_text: str) -> str | None:
#     try:
#         vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
#         model = GenerativeModel(VERTEXAI_MODEL_ID)
#         generation_config = {"temperature": 0.2, "max_output_tokens": 4096}
#         response = model.generate_content([input_text], generation_config=generation_config)
#         return response.text
#     except Exception as e:
#         st.error(f"An error occurred with the Vertex AI API: {e}")
#         import traceback
#         st.error(f"Traceback: {traceback.format_exc()}")
#         return None

# # GCS download function
# @st.cache_data
# def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
#     try:
#         storage_client = storage.Client()
#         bucket = storage_client.bucket(bucket_name)
#         blob = bucket.blob(blob_name)
#         file_bytes = blob.download_as_bytes()
#         return file_bytes
#     except NotFound:
#         st.error(f"File not found in Google Cloud Storage: {blob_name}")
#         return None
#     except Exception as e:
#         st.error(f"Failed to download from GCS: {e}")
#         return None

# # --- Core Application Functions ---
# def initialize_session_state():
#     if 'elasticsearch' not in st.session_state:
#         # Pass the cloud credentials directly to the simplified manager
#         st.session_state.es_manager = get_es_manager(
#             cloud_id=ELASTIC_CLOUD_ID, 
#             username=ELASTIC_USER, 
#             password=ELASTIC_PASSWORD
#         )
#     if 'vector_db' not in st.session_state:
#         st.session_state.vector_db = get_vector_db(_es_manager=st.session_state.es_manager)
#     if 'conversations' not in st.session_state:
#         st.session_state.conversations = {}
#     if 'active_conversation_id' not in st.session_state:
#         st.session_state.active_conversation_id = None
#     if 'selected_keywords' not in st.session_state:
#         st.session_state.selected_keywords = []

# def local_css(file_name):
#     try:
#         with open(file_name) as f:
#             st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#     except FileNotFoundError:
#         st.warning(f"CSS file '{file_name}' not found. Using default styles.")

# def read_pdf_content(pdf_file: io.BytesIO) -> str | None:
#     try:
#         pdf_reader = PyPDF2.PdfReader(pdf_file)
#         return "".join(page.extract_text() for page in pdf_reader.pages)
#     except Exception as e:
#         st.error(f"Error reading PDF: {e}")
#         return None

# def generate_conversation_title(conversation_history: str) -> str:
#     prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
#     title = post_message_vertexai(prompt)
#     if title:
#         return title.strip().replace('"', '')
#     return "New Chat"

# def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 10) -> list:
#     vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
#     es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results)
#     fused_scores = {}
#     k = 60
#     for i, doc in enumerate(vector_results):
#         rank = i + 1
#         paper_id = doc.get('paper_id')
#         if paper_id and paper_id not in fused_scores:
#             fused_scores[paper_id] = {'score': 0, 'doc': doc}
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     for i, hit in enumerate(es_results):
#         rank = i + 1
#         paper_id = hit['_id']
#         if paper_id not in fused_scores:
#             doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
#             fused_scores[paper_id] = {'score': 0, 'doc': doc_content}
#         if paper_id in fused_scores:
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     sorted_fused_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
#     return [item['doc'] for item in sorted_fused_results[:n_results]]

# def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
#     if not keywords:
#         st.error("Please select at least one keyword.")
#         return None, []
#     with st.spinner("Searching papers and generating a structured report..."):
#         time_filter_dict = None
#         now = datetime.datetime.now()
#         if time_filter_type == "Year" and selected_year:
#             time_filter_dict = {"gte": f"{selected_year}-01-01", "lte": f"{selected_year}-12-31"}
#         elif time_filter_type == "Month" and selected_month:
#             year, month = map(int, selected_month.split('-'))
#             time_filter_dict = {"gte": f"{year}-{month:02d}-01", "lt": f"{year}-{(month % 12) + 1:02d}-01" if month < 12 else f"{year+1}-01-01"}
#         elif time_filter_type == "Last week":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}
#         elif time_filter_type == "Last month":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}
        
#         search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict)
#         if not search_results:
#             st.error("No papers found for the selected keywords and time window.")
#             return None, []

#         context = f"Based on a hybrid search for keywords: {', '.join(keywords)}\n\n"
#         for result in search_results:
#             meta = result.get('metadata', {})
#             title = meta.get('title', 'N/A')
#             pub_date = meta.get('publication_date', 'N/A')
#             link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#             content_preview = (meta.get('abstract') or result.get('content') or '')[:1500]
#             context += f"Title: {title}\nPublished: {pub_date}\nLink: {link}\nPreview: {content_preview}...\n---\n"
        
#         prompt = f"""Polo-GGB Assistant. As the expert AI assistant of the Stat4Value, I need your help to perform a detailed analysis. Your task is to analyze the following excerpts from scientific papers and generate a structured report. Based *only* on the context provided below, please generate the report using the following markdown structure. If information for a specific section is not available in the provided excerpts, you MUST write 'Information not available in the provided excerpts.' for that section.
# --- CONTEXT FROM PAPERS ---
# {context}
# --- END CONTEXT ---
# ### Diseases
# List the specific diseases, conditions, or traits studied in these papers.
# ### Sample Size & Genetic Ancestry
# Summarize the sample sizes (e.g., number of participants) and the genetic ancestries (e.g., European, African, East Asian) of the study populations mentioned.
# ### Key Methodological Advances
# Describe any new or significant methods, PRS pipelines, tools, or statistical approaches discussed in the papers.
# ### Emerging Trends
# Identify any future directions, new research areas, or repeated themes that suggest emerging trends in the field based on these papers.
# ### Chatbot Summary
# Provide a concise, overall textual summary of the key findings and clinical implications from the provided excerpts. This should be a general overview."""

#         analysis = post_message_vertexai(prompt)
#         return analysis, search_results

# def display_paper_management():
#     st.subheader("Add Papers to Database")
#     uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
#     uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
#     json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
#     if uploaded_pdfs and st.button("Add to Database"):
#         with st.spinner("Adding papers to databases... This may take a moment."):
#             for uploaded_file in uploaded_pdfs:
#                 base_name = os.path.splitext(uploaded_file.name)[0]
#                 metadata = json_map.get(base_name, {'title': base_name})
#                 metadata['paper_id'] = uploaded_file.name
#                 pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
#                 paper_content = read_pdf_content(pdf_content_bytes)
#                 if paper_content:
#                     st.session_state.vector_db.add_paper(paper_id=uploaded_file.name, content=paper_content, metadata=metadata)
#                     st.success(f"Successfully added '{uploaded_file.name}' to the database.")
#         st.rerun()

# # def main():
# #     st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
# #     local_css("style.css")
# #     initialize_session_state()

# def main():
#     st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")

#     # --- THIS IS THE ROBUST FIX ---
#     # 1. Get the absolute path to the directory containing this script (main.py).
#     current_dir = os.path.dirname(os.path.abspath(__file__))
    
#     # 2. Join that directory path with the filename 'style.css'.
#     # This creates a full, unambiguous path to your CSS file.
#     style_path = os.path.join(current_dir, "style.css")
    
#     # 3. Pass the full path to the function.
#     local_css(style_path)
#     # --- END FIX ---

#     initialize_session_state()

#     with st.sidebar:
#         st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
#         conv_id_to_title_map = {conv_id: data.get("title", "Chat...") for conv_id, data in st.session_state.conversations.items()}
#         title_to_conv_id_map = {v: k for k, v in conv_id_to_title_map.items()}
#         ordered_titles = [conv_id_to_title_map[cid] for cid in reversed(list(st.session_state.conversations.keys()))]
#         active_title = conv_id_to_title_map.get(st.session_state.active_conversation_id)
#         try:
#             default_index = ordered_titles.index(active_title) + 1 if active_title else 0
#         except ValueError:
#             default_index = 0
#         selected_option = option_menu(
#             menu_title=None, options=["➕ New Analysis"] + ordered_titles,
#             icons=['plus-square-dotted'] + ['journals'] * len(ordered_titles),
#             default_index=default_index,
#             styles={
#                 "container": {"padding": "0!important", "background-color": "transparent"},
#                 "icon": {"color": "#007bff", "font-size": "20px"},
#                 "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e9ecef"},
#                 "nav-link-selected": {"background-color": "#cce5ff", "color": "#0056b3", "font-weight": "600"},
#             })
#         intended_conv_id = title_to_conv_id_map.get(selected_option) if selected_option != "➕ New Analysis" else None
#         if st.session_state.active_conversation_id != intended_conv_id:
#             st.session_state.active_conversation_id = intended_conv_id
#             if intended_conv_id is None:
#                 st.session_state.selected_keywords = []
#             st.rerun()
#         st.markdown("---")
#         with st.form(key="new_analysis_form"):
#             st.subheader("Start a New Analysis")
#             selected_keywords = st.multiselect("Select keywords (up to 3)", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []), max_selections=3)
#             time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
#             selected_year, selected_month = None, None
#             if time_filter_type == "Year":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 years = pd.to_datetime(dates, errors='coerce').dropna().year.unique()
#                 selected_year = st.selectbox("Select year", sorted(years, reverse=True)) if len(years) > 0 else st.write("No papers with years found.")
#             elif time_filter_type == "Month":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 months = pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique()
#                 selected_month = st.selectbox("Select month", sorted(months, reverse=True)) if len(months) > 0 else st.write("No papers with months found.")
            
#             if st.form_submit_button("Search & Analyze"):
#                 analysis_result, retrieved_papers = process_keyword_search(selected_keywords, time_filter_type, selected_year, selected_month)
#                 if analysis_result:
#                     conv_id = f"conv_{time.time()}"
#                     initial_message = {"role": "assistant", "content": f"**Analysis for: {', '.join(selected_keywords)}**\n\n{analysis_result}"}
#                     title = generate_conversation_title(analysis_result)
#                     st.session_state.conversations[conv_id] = {
#                         "title": title, 
#                         "messages": [initial_message], 
#                         "keywords": selected_keywords,
#                         "retrieved_papers": retrieved_papers
#                     }
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

#         st.markdown("---")
#         with st.expander("Paper Management"):
#             display_paper_management()

#     st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

#     if st.session_state.active_conversation_id is None:
#         st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
#     else:
#         active_id = st.session_state.active_conversation_id
#         active_conv = st.session_state.conversations[active_id]
        
#         for message in active_conv["messages"]:
#             avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
#             with st.expander("View Retrieved Papers for this Analysis"):
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'N/A')
#                     paper_id = paper.get('paper_id')

#                     col1, col2 = st.columns([4, 1])
#                     with col1:
#                         st.markdown(f"**{i+1}. {title}**")
#                         if link != 'N/A':
#                             st.markdown(f"   - Link: [{link}]({link})")
#                     with col2:
#                         if paper_id:
#                             pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
#                             if pdf_bytes:
#                                 st.download_button(
#                                     label="Download PDF",
#                                     data=pdf_bytes,
#                                     file_name=paper_id,
#                                     mime="application/pdf",
#                                     key=f"download_{paper_id}_{i}"
#                                 )

#         if prompt := st.chat_input("Ask a follow-up question..."):
#             active_conv["messages"].append({"role": "user", "content": prompt})
#             st.rerun()

#     if st.session_state.active_conversation_id and st.session_state.conversations[st.session_state.active_conversation_id]["messages"][-1]["role"] == "user":
#         active_conv = st.session_state.conversations[st.session_state.active_conversation_id]
#         with st.spinner("Thinking..."):
#             chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in active_conv["messages"]])
#             full_context = ""
#             if active_conv.get("retrieved_papers"):
#                 full_context += "Here is the full context of every paper found in the initial analysis:\n\n"
#                 for paper in active_conv["retrieved_papers"]:
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#                     content_preview = (meta.get('abstract') or paper.get('content') or '')[:1000]
#                     full_context += f"Title: {title}\nLink: {link}\nPreview: {content_preview}...\n---\n"
#             full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
# Your task is to answer the user's follow-up question based on the chat history and the full context of the papers provided below.
# When the user asks you to list the papers, you MUST list ALL papers provided in the context below. Do not omit, summarize, or change any.
# Format the response as a numbered list. For each paper, provide its full title and a clickable markdown link if the link is available in the context.
# --- CHAT HISTORY ---
# {chat_history}
# --- END CHAT HISTORY ---
# --- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
# {full_context}
# --- END FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
# Assistant Response:"""
            
#             response_text = post_message_vertexai(full_prompt)
#             if response_text:
#                 active_conv["messages"].append({"role": "assistant", "content": response_text})
#                 st.rerun()

# if __name__ == "__main__":
#     main()
































# # app/main.py

# import streamlit as st
# import platform
# import requests
# import time
# import json
# import PyPDF2
# import io
# import yaml
# import os
# import sys
# from typing import List, Dict, Any
# import datetime
# from dateutil import parser as date_parser
# from streamlit_option_menu import option_menu
# import vertexai
# from vertexai.generative_models import GenerativeModel
# from google.cloud import storage
# from google.api_core.exceptions import NotFound

# # SQLite3 Patch for Linux environments
# if platform.system() == "Linux":
#     try:
#         __import__("pysqlite3")
#         import sys
#         sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
#     except ImportError:
#         st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

# try:
#     from elasticsearch_utils import get_es_manager
#     from vector_db import get_vector_db
# except ImportError as e:
#     st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
#     st.stop()

# # --- App Configuration & Constants ---
# # (This section remains the same)
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# try:
#     config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
#     with open(config_path, 'r') as file:
#         config = yaml.safe_load(file)
# except FileNotFoundError:
#     st.error("Configuration file 'config/config.yaml' not found.")
#     st.stop()
# except Exception as e:
#     st.error(f"Error loading config.yaml: {e}")
#     st.stop()

# # --- Configuration from Streamlit Secrets ---
# try:
#     # --- Elastic Cloud Configuration ---
#     ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
#     ELASTIC_USER = st.secrets["elasticsearch"]["username"]
#     ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

#     # --- Vertex AI Configurations ---
#     # Reading lowercase keys to match secrets.toml best practice
#     VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
#     VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
#     VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

#     # --- GCS Configuration ---
#     GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

#     # --- Google Service Account Credentials ---
#     # 1. Read the secret, which is a Streamlit AttrDict object.
#     gcp_service_account_secret = st.secrets["gcp_service_account"]
    
#     # 2. Convert the AttrDict to a standard Python dictionary.
#     #    THIS IS THE FIX for the "not JSON serializable" error.
#     GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
#     # 3. Write the standard dictionary to a temporary file.
#     with open("gcp_credentials.json", "w") as f:
#         json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
#     # 4. Set the environment variable for Google Cloud libraries to find the file.
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

# except KeyError as e:
#     st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
#     st.stop()

# # --- Interface Constants (no changes) ---
# GENETICS_KEYWORDS = [
#     "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
# ]
# USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
# BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# # --- API and Helper Functions (no changes) ---
# def post_message_vertexai(input_text: str) -> str | None:
#     try:
#         vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
#         model = GenerativeModel(VERTEXAI_MODEL_ID)
#         generation_config = {"temperature": 0.25, "max_output_tokens": 8192} # Increased for longer summaries
#         response = model.generate_content([input_text], generation_config=generation_config)
#         return response.text
#     except Exception as e:
#         st.error(f"An error occurred with the Vertex AI API: {e}")
#         import traceback
#         st.error(f"Traceback: {traceback.format_exc()}")
#         return None

# @st.cache_data
# def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
#     # ... (function is correct, no changes)
#     try:
#         storage_client = storage.Client()
#         bucket = storage_client.bucket(bucket_name)
#         blob = bucket.blob(blob_name)
#         return blob.download_as_bytes()
#     except NotFound:
#         st.warning(f"File not found in GCS: {blob_name}")
#         return None
#     except Exception as e:
#         st.error(f"Failed to download from GCS: {e}")
#         return None

# def initialize_session_state():
#     # ... (function is correct, no changes)
#     if 'es_manager' not in st.session_state:
#         st.session_state.es_manager = get_es_manager(cloud_id=ELASTIC_CLOUD_ID, username=ELASTIC_USER, password=ELASTIC_PASSWORD)
#     if 'vector_db' not in st.session_state:
#         st.session_state.vector_db = get_vector_db(_es_manager=st.session_state.es_manager)
#     if 'conversations' not in st.session_state:
#         st.session_state.conversations = {}
#     if 'active_conversation_id' not in st.session_state:
#         st.session_state.active_conversation_id = None
#     if 'selected_keywords' not in st.session_state:
#         st.session_state.selected_keywords = []

# def local_css(file_name):
#     # ... (function is correct, no changes)
#     try:
#         with open(file_name) as f:
#             st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#     except FileNotFoundError:
#         st.warning(f"CSS file '{file_name}' not found. Using default styles.")

# def read_pdf_content(pdf_file: io.BytesIO) -> str | None:
#     # ... (function is correct, no changes)
#     try:
#         pdf_reader = PyPDF2.PdfReader(pdf_file)
#         return "".join(page.extract_text() for page in pdf_reader.pages)
#     except Exception as e:
#         st.error(f"Error reading PDF: {e}")
#         return None

# def generate_conversation_title(conversation_history: str) -> str:
#     # ... (function is correct, no changes)
#     prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
#     title = post_message_vertexai(prompt)
#     if title:
#         return title.strip().replace('"', '')
#     return "New Chat"

# def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 10) -> list:
#     # ... (function is correct, no changes)
#     vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
#     es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results)
#     fused_scores = {}
#     k = 60
#     for i, doc in enumerate(vector_results):
#         rank = i + 1
#         paper_id = doc.get('paper_id')
#         if paper_id and paper_id not in fused_scores:
#             fused_scores[paper_id] = {'score': 0, 'doc': doc}
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     for i, hit in enumerate(es_results):
#         rank = i + 1
#         paper_id = hit['_id']
#         if paper_id not in fused_scores:
#             doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
#             fused_scores[paper_id] = {'score': 0, 'doc': doc_content}
#         if paper_id in fused_scores:
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     sorted_fused_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
#     return [item['doc'] for item in sorted_fused_results[:n_results]]

# # <<< --- MAJOR CHANGES TO THIS FUNCTION --- >>>
# def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
#     if not keywords:
#         st.error("Please select at least one keyword.")
#         return None, []
#     with st.spinner("Searching papers and generating a detailed, multi-part report..."):
#         time_filter_dict = None
#         now = datetime.datetime.now()
#         if time_filter_type == "Year" and selected_year:
#             time_filter_dict = {"gte": f"{selected_year}-01-01", "lte": f"{selected_year}-12-31"}
#         elif time_filter_type == "Month" and selected_month:
#             year, month = map(int, selected_month.split('-'))
#             time_filter_dict = {"gte": f"{year}-{month:02d}-01", "lt": f"{year}-{(month % 12) + 1:02d}-01" if month < 12 else f"{year+1}-01-01"}
#         elif time_filter_type == "Last week":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}
#         elif time_filter_type == "Last month":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}
        
#         search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict)
#         if not search_results:
#             st.error("No papers found for the selected keywords and time window.")
#             return None, []

#         context = "You are a meticulous and expert research assistant. Analyze the following scientific paper excerpts.\n\n"
#         # CHANGE: Give each paper a unique reference tag for citation
#         for i, result in enumerate(search_results):
#             meta = result.get('metadata', {})
#             title = meta.get('title', 'N/A')
#             link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
            
#             # CHANGE: Increase content preview size for deeper analysis
#             content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
            
#             # Use a structured format the AI can easily parse for citations
#             context += f"SOURCE [{i+1}]:\n"
#             context += f"Title: {title}\n"
#             context += f"Link: {link}\n"
#             context += f"Content: {content_preview}\n---\n\n"
        
#         # CHANGE: A new, much more detailed prompt to implement all high-priority features
#         prompt = f"""{context}
# ---
# **TASK:**

# Based *only* on the provided paper sources above, generate a detailed, multi-part report. You must follow these instructions exactly:

# **Part 1: Thematic Analysis**
# Generate the following sections. For "Key Methodological Advances," "Emerging Trends," and "Overall Summary," you MUST provide a detailed, extended analysis of at least two paragraphs or a comprehensive bulleted list. Go beyond a simple list; explain the significance and synthesize information across multiple sources.

#    ### Diseases: List the specific diseases, conditions, or traits studied.
#    ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries.
#    ### Key Methodological Advances: Describe significant methods, pipelines, or statistical approaches. Explain *why* they are important advances.
#    ### Emerging Trends: Identify future directions and new research areas. Synthesize repeated themes to explain what trends are emerging in the field.
#    ### Overall Summary: Provide a comprehensive textual summary of the key findings and clinical implications.

# **CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].`

# **Part 2: Key Paper Summaries**
# Create a new section titled ### Key Paper Summaries. Under this heading, identify the top 3 most relevant papers from the sources and provide a concise, one-paragraph summary for each. After each summary, you **MUST** include a direct link to the paper on a new line, formatted as: `[Source Link](the_actual_link)`.

# **Part 3: References**
# Create a final section titled ### References. Under this heading, you **MUST** list all the paper sources provided above. The number for each reference must correspond to the citation markers used in Part 1. Format each entry as a numbered list item: `1. [Paper Title](Paper Link)`.
# """

#         analysis = post_message_vertexai(prompt)
#         return analysis, search_results

# # --- Main App Logic and UI (No changes needed below this line) ---
# def display_paper_management():
#     # ... (This function is correct)
#     st.subheader("Add Papers to Database")
#     uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
#     uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
#     json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
#     if uploaded_pdfs and st.button("Add to Database"):
#         with st.spinner("Adding papers to databases..."):
#             for uploaded_file in uploaded_pdfs:
#                 base_name = os.path.splitext(uploaded_file.name)[0]
#                 metadata = json_map.get(base_name, {'title': base_name})
#                 metadata['paper_id'] = uploaded_file.name
#                 pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
#                 paper_content = read_pdf_content(pdf_content_bytes)
#                 if paper_content:
#                     st.session_state.vector_db.add_paper(paper_id=uploaded_file.name, content=paper_content, metadata=metadata)
#                     st.success(f"Successfully added '{uploaded_file.name}' to the database.")
#         st.rerun()

# def main():
#     st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     style_path = os.path.join(current_dir, "style.css")
#     local_css(style_path)
#     initialize_session_state()

#     with st.sidebar:
#         st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
#         conv_id_to_title_map = {conv_id: data.get("title", "Chat...") for conv_id, data in st.session_state.conversations.items()}
#         title_to_conv_id_map = {v: k for k, v in conv_id_to_title_map.items()}
#         ordered_titles = [conv_id_to_title_map[cid] for cid in reversed(list(st.session_state.conversations.keys()))]
#         active_title = conv_id_to_title_map.get(st.session_state.active_conversation_id)
#         try:
#             default_index = ordered_titles.index(active_title) + 1 if active_title else 0
#         except ValueError:
#             default_index = 0
#         selected_option = option_menu(
#             menu_title=None, options=["➕ New Analysis"] + ordered_titles,
#             icons=['plus-square-dotted'] + ['journals'] * len(ordered_titles),
#             default_index=default_index,
#             styles={
#                 "container": {"padding": "0!important", "background-color": "transparent"},
#                 "icon": {"color": "#007bff", "font-size": "20px"},
#                 "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e9ecef"},
#                 "nav-link-selected": {"background-color": "#cce5ff", "color": "#0056b3", "font-weight": "600"},
#             })
#         intended_conv_id = title_to_conv_id_map.get(selected_option) if selected_option != "➕ New Analysis" else None
#         if st.session_state.active_conversation_id != intended_conv_id:
#             st.session_state.active_conversation_id = intended_conv_id
#             if intended_conv_id is None:
#                 st.session_state.selected_keywords = []
#             st.rerun()
#         st.markdown("---")
#         with st.form(key="new_analysis_form"):
#             st.subheader("Start a New Analysis")
#             selected_keywords = st.multiselect("Select keywords (up to 3)", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []), max_selections=3)
#             time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
#             selected_year, selected_month = None, None
#             if time_filter_type == "Year":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 years = pd.to_datetime(dates, errors='coerce').dropna().year.unique()
#                 selected_year = st.selectbox("Select year", sorted(years, reverse=True)) if len(years) > 0 else st.write("No papers with years found.")
#             elif time_filter_type == "Month":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 months = pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique()
#                 selected_month = st.selectbox("Select month", sorted(months, reverse=True)) if len(months) > 0 else st.write("No papers with months found.")
            
#             if st.form_submit_button("Search & Analyze"):
#                 analysis_result, retrieved_papers = process_keyword_search(selected_keywords, time_filter_type, selected_year, selected_month)
#                 if analysis_result:
#                     conv_id = f"conv_{time.time()}"
#                     initial_message = {"role": "assistant", "content": f"**Analysis for: {', '.join(selected_keywords)}**\n\n{analysis_result}"}
#                     title = generate_conversation_title(analysis_result)
#                     st.session_state.conversations[conv_id] = {
#                         "title": title, 
#                         "messages": [initial_message], 
#                         "keywords": selected_keywords,
#                         "retrieved_papers": retrieved_papers
#                     }
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

#         st.markdown("---")
#         with st.expander("Paper Management"):
#             display_paper_management()

#     st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

#     if st.session_state.active_conversation_id is None:
#         st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
#     else:
#         active_id = st.session_state.active_conversation_id
#         active_conv = st.session_state.conversations[active_id]
        
#         for message in active_conv["messages"]:
#             avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
#             with st.expander("View Retrieved Papers for this Analysis"):
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'N/A')
#                     paper_id = paper.get('paper_id')

#                     col1, col2 = st.columns([4, 1])
#                     with col1:
#                         st.markdown(f"**{i+1}. {title}**")
#                         if link != 'N/A':
#                             st.markdown(f"   - Link: [{link}]({link})")
#                     with col2:
#                         if paper_id:
#                             pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
#                             if pdf_bytes:
#                                 st.download_button(
#                                     label="Download PDF",
#                                     data=pdf_bytes,
#                                     file_name=paper_id,
#                                     mime="application/pdf",
#                                     key=f"download_{paper_id}_{i}"
#                                 )

#         if prompt := st.chat_input("Ask a follow-up question..."):
#             active_conv["messages"].append({"role": "user", "content": prompt})
#             st.rerun()

#     if st.session_state.active_conversation_id and st.session_state.conversations[st.session_state.active_conversation_id]["messages"][-1]["role"] == "user":
#         active_conv = st.session_state.conversations[st.session_state.active_conversation_id]
#         with st.spinner("Thinking..."):
#             chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in active_conv["messages"]])
#             full_context = ""
#             if active_conv.get("retrieved_papers"):
#                 full_context += "Here is the full context of every paper found in the initial analysis:\n\n"
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#                     content_preview = (meta.get('abstract') or paper.get('content') or '')[:4000] # Use larger preview here too
#                     full_context += f"SOURCE [{i+1}]:\nTitle: {title}\nLink: {link}\nContent: {content_preview}\n---\n\n"
            
#             full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
# Your task is to answer the user's last message based on the chat history and the full context from the paper sources provided below.
# When the user asks you to list the papers or for references, you MUST format the response as a numbered list with clickable markdown links: `1. [Paper Title](Paper Link)`.

# --- CHAT HISTORY ---
# {chat_history}
# --- END CHAT HISTORY ---

# --- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
# {full_context}
# --- END FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---

# Assistant Response:"""
            
#             response_text = post_message_vertexai(full_prompt)
#             if response_text:
#                 active_conv["messages"].append({"role": "assistant", "content": response_text})
#                 st.rerun()

# if __name__ == "__main__":
#     main()
































# # app/main.py MOST IMPORTANT ONE
# # This code piece part of only with inline clickable links

# import streamlit as st
# import platform
# import requests
# import time
# import json
# import PyPDF2
# import io
# import yaml
# import os
# import sys
# from typing import List, Dict, Any
# import datetime
# from dateutil import parser as date_parser
# from streamlit_option_menu import option_menu
# import vertexai
# from vertexai.generative_models import GenerativeModel
# from google.cloud import storage
# from google.api_core.exceptions import NotFound

# # SQLite3 Patch for Linux environments
# if platform.system() == "Linux":
#     try:
#         __import__("pysqlite3")
#         import sys
#         sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
#     except ImportError:
#         st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

# try:
#     from elasticsearch_utils import get_es_manager
#     from vector_db import get_vector_db
# except ImportError as e:
#     st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
#     st.stop()

# # --- App Configuration & Constants ---
# # (This section remains the same)
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# try:
#     config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
#     with open(config_path, 'r') as file:
#         config = yaml.safe_load(file)
# except FileNotFoundError:
#     st.error("Configuration file 'config/config.yaml' not found.")
#     st.stop()
# except Exception as e:
#     st.error(f"Error loading config.yaml: {e}")
#     st.stop()

# # --- Configuration from Streamlit Secrets ---
# try:
#     # --- Elastic Cloud Configuration ---
#     ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
#     ELASTIC_USER = st.secrets["elasticsearch"]["username"]
#     ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

#     # --- Vertex AI Configurations ---
#     # Reading lowercase keys to match secrets.toml best practice
#     VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
#     VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
#     VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

#     # --- GCS Configuration ---
#     GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

#     # --- Google Service Account Credentials ---
#     # 1. Read the secret, which is a Streamlit AttrDict object.
#     gcp_service_account_secret = st.secrets["gcp_service_account"]
    
#     # 2. Convert the AttrDict to a standard Python dictionary.
#     #    THIS IS THE FIX for the "not JSON serializable" error.
#     GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
#     # 3. Write the standard dictionary to a temporary file.
#     with open("gcp_credentials.json", "w") as f:
#         json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
#     # 4. Set the environment variable for Google Cloud libraries to find the file.
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

# except KeyError as e:
#     st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
#     st.stop()

# # --- Interface Constants (no changes) ---
# GENETICS_KEYWORDS = [
#     "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
# ]
# USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
# BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# # --- API and Helper Functions (no changes) ---
# def post_message_vertexai(input_text: str) -> str | None:
#     try:
#         vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
#         model = GenerativeModel(VERTEXAI_MODEL_ID)
#         generation_config = {"temperature": 0.25, "max_output_tokens": 8192} # Increased for longer summaries
#         response = model.generate_content([input_text], generation_config=generation_config)
#         return response.text
#     except Exception as e:
#         st.error(f"An error occurred with the Vertex AI API: {e}")
#         import traceback
#         st.error(f"Traceback: {traceback.format_exc()}")
#         return None

# @st.cache_data
# def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
#     # ... (function is correct, no changes)
#     try:
#         storage_client = storage.Client()
#         bucket = storage_client.bucket(bucket_name)
#         blob = bucket.blob(blob_name)
#         return blob.download_as_bytes()
#     except NotFound:
#         st.warning(f"File not found in GCS: {blob_name}")
#         return None
#     except Exception as e:
#         st.error(f"Failed to download from GCS: {e}")
#         return None

# def initialize_session_state():
#     # ... (function is correct, no changes)
#     if 'es_manager' not in st.session_state:
#         st.session_state.es_manager = get_es_manager(cloud_id=ELASTIC_CLOUD_ID, username=ELASTIC_USER, password=ELASTIC_PASSWORD)
#     if 'vector_db' not in st.session_state:
#         st.session_state.vector_db = get_vector_db(_es_manager=st.session_state.es_manager)
#     if 'conversations' not in st.session_state:
#         st.session_state.conversations = {}
#     if 'active_conversation_id' not in st.session_state:
#         st.session_state.active_conversation_id = None
#     if 'selected_keywords' not in st.session_state:
#         st.session_state.selected_keywords = []

# def local_css(file_name):
#     # ... (function is correct, no changes)
#     try:
#         with open(file_name) as f:
#             st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#     except FileNotFoundError:
#         st.warning(f"CSS file '{file_name}' not found. Using default styles.")

# def read_pdf_content(pdf_file: io.BytesIO) -> str | None:
#     # ... (function is correct, no changes)
#     try:
#         pdf_reader = PyPDF2.PdfReader(pdf_file)
#         return "".join(page.extract_text() for page in pdf_reader.pages)
#     except Exception as e:
#         st.error(f"Error reading PDF: {e}")
#         return None

# def generate_conversation_title(conversation_history: str) -> str:
#     # ... (function is correct, no changes)
#     prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
#     title = post_message_vertexai(prompt)
#     if title:
#         return title.strip().replace('"', '')
#     return "New Chat"

# def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 10) -> list:
#     # ... (function is correct, no changes)
#     vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
#     es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results)
#     fused_scores = {}
#     k = 60
#     for i, doc in enumerate(vector_results):
#         rank = i + 1
#         paper_id = doc.get('paper_id')
#         if paper_id and paper_id not in fused_scores:
#             fused_scores[paper_id] = {'score': 0, 'doc': doc}
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     for i, hit in enumerate(es_results):
#         rank = i + 1
#         paper_id = hit['_id']
#         if paper_id not in fused_scores:
#             doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
#             fused_scores[paper_id] = {'score': 0, 'doc': doc_content}
#         if paper_id in fused_scores:
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     sorted_fused_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
#     return [item['doc'] for item in sorted_fused_results[:n_results]]

# # <<< --- MAJOR CHANGES TO THIS FUNCTION --- >>>
# def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
#     if not keywords:
#         st.error("Please select at least one keyword.")
#         return None, []
#     with st.spinner("Searching papers and generating a detailed, multi-part report..."):
#         time_filter_dict = None
#         now = datetime.datetime.now()
#         if time_filter_type == "Year" and selected_year:
#             time_filter_dict = {"gte": f"{selected_year}-01-01", "lte": f"{selected_year}-12-31"}
#         elif time_filter_type == "Month" and selected_month:
#             year, month = map(int, selected_month.split('-'))
#             time_filter_dict = {"gte": f"{year}-{month:02d}-01", "lt": f"{year}-{(month % 12) + 1:02d}-01" if month < 12 else f"{year+1}-01-01"}
#         elif time_filter_type == "Last week":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}
#         elif time_filter_type == "Last month":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}
        
#         search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict)
#         if not search_results:
#             st.error("No papers found for the selected keywords and time window.")
#             return None, []

#         context = "You are a meticulous and expert research assistant. Analyze the following scientific paper excerpts.\n\n"
#         # CHANGE: Give each paper a unique reference tag for citation
#         for i, result in enumerate(search_results):
#             meta = result.get('metadata', {})
#             title = meta.get('title', 'N/A')
#             link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
            
#             # CHANGE: Increase content preview size for deeper analysis
#             content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
            
#             # Use a structured format the AI can easily parse for citations
#             context += f"SOURCE [{i+1}]:\n"
#             context += f"Title: {title}\n"
#             context += f"Link: {link}\n"
#             context += f"Content: {content_preview}\n---\n\n"
        
#         # CHANGE: A new, much more detailed prompt to implement all high-priority features
#         prompt = f"""{context}
# ---
# **TASK:**

# Based *only* on the provided paper sources above, generate a detailed, multi-part report. You must follow these instructions exactly:

# **Part 1: Thematic Analysis**
# Generate the following sections. For "Key Methodological Advances," "Emerging Trends," and "Overall Summary," you MUST provide a detailed, extended analysis of at least two paragraphs or a comprehensive bulleted list. Go beyond a simple list; explain the significance and synthesize information across multiple sources.

#    ### Diseases: List the specific diseases, conditions, or traits studied.
#    ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries.
#    ### Key Methodological Advances: Describe significant methods, pipelines, or statistical approaches. Explain *why* they are important advances.
#    ### Emerging Trends: Identify future directions and new research areas. Synthesize repeated themes to explain what trends are emerging in the field.
#    ### Overall Summary: Provide a comprehensive textual summary of the key findings and clinical implications.

# **CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].`

# **Part 2: Key Paper Summaries**
# Create a new section titled ### Key Paper Summaries. Under this heading, identify the top 3 most relevant papers from the sources and provide a concise, one-paragraph summary for each. After each summary, you **MUST** include a direct link to the paper on a new line, formatted as: `[Source Link](the_actual_link)`.

# **Part 3: References**
# Create a final section titled ### References. Under this heading, you **MUST** list all the paper sources provided above. The number for each reference must correspond to the citation markers used in Part 1. Format each entry as a numbered list item: `1. [Paper Title](Paper Link)`.
# """

#         analysis = post_message_vertexai(prompt)
#         return analysis, search_results

# # --- Main App Logic and UI (No changes needed below this line) ---
# def display_paper_management():
#     # ... (This function is correct)
#     st.subheader("Add Papers to Database")
#     uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
#     uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
#     json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
#     if uploaded_pdfs and st.button("Add to Database"):
#         with st.spinner("Adding papers to databases..."):
#             for uploaded_file in uploaded_pdfs:
#                 base_name = os.path.splitext(uploaded_file.name)[0]
#                 metadata = json_map.get(base_name, {'title': base_name})
#                 metadata['paper_id'] = uploaded_file.name
#                 pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
#                 paper_content = read_pdf_content(pdf_content_bytes)
#                 if paper_content:
#                     st.session_state.vector_db.add_paper(paper_id=uploaded_file.name, content=paper_content, metadata=metadata)
#                     st.success(f"Successfully added '{uploaded_file.name}' to the database.")
#         st.rerun()

# def main():
#     st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     style_path = os.path.join(current_dir, "style.css")
#     local_css(style_path)
#     initialize_session_state()

#     with st.sidebar:
#         st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
#         conv_id_to_title_map = {conv_id: data.get("title", "Chat...") for conv_id, data in st.session_state.conversations.items()}
#         title_to_conv_id_map = {v: k for k, v in conv_id_to_title_map.items()}
#         ordered_titles = [conv_id_to_title_map[cid] for cid in reversed(list(st.session_state.conversations.keys()))]
#         active_title = conv_id_to_title_map.get(st.session_state.active_conversation_id)
#         try:
#             default_index = ordered_titles.index(active_title) + 1 if active_title else 0
#         except ValueError:
#             default_index = 0
#         selected_option = option_menu(
#             menu_title=None, options=["➕ New Analysis"] + ordered_titles,
#             icons=['plus-square-dotted'] + ['journals'] * len(ordered_titles),
#             default_index=default_index,
#             styles={
#                 "container": {"padding": "0!important", "background-color": "transparent"},
#                 "icon": {"color": "#007bff", "font-size": "20px"},
#                 "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e9ecef"},
#                 "nav-link-selected": {"background-color": "#cce5ff", "color": "#0056b3", "font-weight": "600"},
#             })
#         intended_conv_id = title_to_conv_id_map.get(selected_option) if selected_option != "➕ New Analysis" else None
#         if st.session_state.active_conversation_id != intended_conv_id:
#             st.session_state.active_conversation_id = intended_conv_id
#             if intended_conv_id is None:
#                 st.session_state.selected_keywords = []
#             st.rerun()
#         st.markdown("---")
#         with st.form(key="new_analysis_form"):
#             st.subheader("Start a New Analysis")
#             selected_keywords = st.multiselect("Select keywords (up to 3)", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []), max_selections=3)
#             time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
#             selected_year, selected_month = None, None
#             if time_filter_type == "Year":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 years = pd.to_datetime(dates, errors='coerce').dropna().year.unique()
#                 selected_year = st.selectbox("Select year", sorted(years, reverse=True)) if len(years) > 0 else st.write("No papers with years found.")
#             elif time_filter_type == "Month":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 months = pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique()
#                 selected_month = st.selectbox("Select month", sorted(months, reverse=True)) if len(months) > 0 else st.write("No papers with months found.")
            
#             if st.form_submit_button("Search & Analyze"):
#                 analysis_result, retrieved_papers = process_keyword_search(selected_keywords, time_filter_type, selected_year, selected_month)
#                 if analysis_result:
#                     conv_id = f"conv_{time.time()}"
#                     initial_message = {"role": "assistant", "content": f"**Analysis for: {', '.join(selected_keywords)}**\n\n{analysis_result}"}
#                     title = generate_conversation_title(analysis_result)
#                     st.session_state.conversations[conv_id] = {
#                         "title": title, 
#                         "messages": [initial_message], 
#                         "keywords": selected_keywords,
#                         "retrieved_papers": retrieved_papers
#                     }
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

#         st.markdown("---")
#         with st.expander("Paper Management"):
#             display_paper_management()

#     st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

#     if st.session_state.active_conversation_id is None:
#         st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
#     else:
#         active_id = st.session_state.active_conversation_id
#         active_conv = st.session_state.conversations[active_id]
        
#         for message in active_conv["messages"]:
#             avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
#             with st.expander("View Retrieved Papers for this Analysis"):
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'N/A')
#                     paper_id = paper.get('paper_id')

#                     col1, col2 = st.columns([4, 1])
#                     with col1:
#                         st.markdown(f"**{i+1}. {title}**")
#                         if link != 'N/A':
#                             st.markdown(f"   - Link: [{link}]({link})")
#                     with col2:
#                         if paper_id:
#                             pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
#                             if pdf_bytes:
#                                 st.download_button(
#                                     label="Download PDF",
#                                     data=pdf_bytes,
#                                     file_name=paper_id,
#                                     mime="application/pdf",
#                                     key=f"download_{paper_id}_{i}"
#                                 )

#         if prompt := st.chat_input("Ask a follow-up question..."):
#             active_conv["messages"].append({"role": "user", "content": prompt})
#             st.rerun()

#     if st.session_state.active_conversation_id and st.session_state.conversations[st.session_state.active_conversation_id]["messages"][-1]["role"] == "user":
#         active_conv = st.session_state.conversations[st.session_state.active_conversation_id]
#         with st.spinner("Thinking..."):
#             chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in active_conv["messages"]])
#             full_context = ""
#             if active_conv.get("retrieved_papers"):
#                 full_context += "Here is the full context of every paper found in the initial analysis:\n\n"
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#                     content_preview = (meta.get('abstract') or paper.get('content') or '')[:4000] # Use larger preview here too
#                     full_context += f"SOURCE [{i+1}]:\nTitle: {title}\nLink: {link}\nContent: {content_preview}\n---\n\n"
            
#             full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
# Your task is to answer the user's last message based on the chat history and the full context from the paper sources provided below.
# When the user asks you to list the papers or for references, you MUST format the response as a numbered list with clickable markdown links: `1. [Paper Title](Paper Link)`.

# --- CHAT HISTORY ---
# {chat_history}
# --- END CHAT HISTORY ---

# --- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
# {full_context}
# --- END FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---

# Assistant Response:"""
            
#             response_text = post_message_vertexai(full_prompt)
#             if response_text:
#                 active_conv["messages"].append({"role": "assistant", "content": response_text})
#                 st.rerun()

# if __name__ == "__main__":
#     main()



























































# # app/main.py

# import streamlit as st
# import platform
# import requests
# import time
# import json
# import PyPDF2
# import io
# import yaml
# import os
# import sys
# from typing import List, Dict, Any
# import datetime
# from dateutil import parser as date_parser
# from collections import defaultdict

# import vertexai
# from vertexai.generative_models import GenerativeModel
# from google.cloud import storage
# from google.api_core.exceptions import NotFound

# # SQLite3 Patch for Linux environments
# if platform.system() == "Linux":
#     try:
#         __import__("pysqlite3")
#         import sys
#         sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
#     except ImportError:
#         st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

# try:
#     from elasticsearch_utils import get_es_manager
#     from vector_db import get_vector_db
# except ImportError as e:
#     st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
#     st.stop()

# # --- App Configuration & Constants ---
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# try:
#     config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
#     with open(config_path, 'r') as file:
#         config = yaml.safe_load(file)
# except FileNotFoundError:
#     st.error("Configuration file 'config/config.yaml' not found.")
#     st.stop()
# except Exception as e:
#     st.error(f"Error loading config.yaml: {e}")
#     st.stop()

# # --- Configuration from Streamlit Secrets ---
# try:
#     # --- Elastic Cloud Configuration ---
#     ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
#     ELASTIC_USER = st.secrets["elasticsearch"]["username"]
#     ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

#     # --- Vertex AI Configurations ---
#     # Reading lowercase keys to match secrets.toml best practice
#     VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
#     VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
#     VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

#     # --- GCS Configuration ---
#     GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

#     # --- Google Service Account Credentials ---
#     # 1. Read the secret, which is a Streamlit AttrDict object.
#     gcp_service_account_secret = st.secrets["gcp_service_account"]
    
#     # 2. Convert the AttrDict to a standard Python dictionary.
#     #    THIS IS THE FIX for the "not JSON serializable" error.
#     GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
#     # 3. Write the standard dictionary to a temporary file.
#     with open("gcp_credentials.json", "w") as f:
#         json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
#     # 4. Set the environment variable for Google Cloud libraries to find the file.
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

# except KeyError as e:
#     st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
#     st.stop()

# # --- Interface Constants ---
# GENETICS_KEYWORDS = [
#     "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
# ]
# USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
# BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# # --- API and Helper Functions ---
# def post_message_vertexai(input_text: str) -> str | None:
#     try:
#         vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
#         model = GenerativeModel(VERTEXAI_MODEL_ID)
#         generation_config = {"temperature": 0.25, "max_output_tokens": 8192}
#         response = model.generate_content([input_text], generation_config=generation_config)
#         return response.text
#     except Exception as e:
#         st.error(f"An error occurred with the Vertex AI API: {e}")
#         import traceback
#         st.error(f"Traceback: {traceback.format_exc()}")
#         return None

# @st.cache_data
# def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
#     try:
#         storage_client = storage.Client()
#         bucket = storage_client.bucket(bucket_name)
#         blob = bucket.blob(blob_name)
#         return blob.download_as_bytes()
#     except NotFound:
#         st.warning(f"File not found in GCS: {blob_name}")
#         return None
#     except Exception as e:
#         st.error(f"Failed to download from GCS: {e}")
#         return None

# def initialize_session_state():
#     if 'es_manager' not in st.session_state:
#         st.session_state.es_manager = get_es_manager(cloud_id=ELASTIC_CLOUD_ID, username=ELASTIC_USER, password=ELASTIC_PASSWORD)
#     if 'vector_db' not in st.session_state:
#         st.session_state.vector_db = get_vector_db(_es_manager=st.session_state.es_manager)
#     if 'conversations' not in st.session_state:
#         st.session_state.conversations = {}
#     if 'active_conversation_id' not in st.session_state:
#         st.session_state.active_conversation_id = None
#     if 'selected_keywords' not in st.session_state:
#         st.session_state.selected_keywords = []

# def local_css(file_name):
#     try:
#         with open(file_name) as f:
#             st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#     except FileNotFoundError:
#         st.warning(f"CSS file '{file_name}' not found. Using default styles.")

# def read_pdf_content(pdf_file: io.BytesIO) -> str | None:
#     try:
#         pdf_reader = PyPDF2.PdfReader(pdf_file)
#         return "".join(page.extract_text() for page in pdf_reader.pages)
#     except Exception as e:
#         st.error(f"Error reading PDF: {e}")
#         return None

# def generate_conversation_title(conversation_history: str) -> str:
#     prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
#     title = post_message_vertexai(prompt)
#     if title:
#         return title.strip().replace('"', '')
#     return "New Chat"

# def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 10) -> list:
#     vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
#     es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results)
#     fused_scores = {}
#     k = 60
#     for i, doc in enumerate(vector_results):
#         rank = i + 1
#         paper_id = doc.get('paper_id')
#         if paper_id and paper_id not in fused_scores:
#             fused_scores[paper_id] = {'score': 0, 'doc': doc}
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     for i, hit in enumerate(es_results):
#         rank = i + 1
#         paper_id = hit['_id']
#         if paper_id not in fused_scores:
#             doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
#             fused_scores[paper_id] = {'score': 0, 'doc': doc_content}
#         if paper_id in fused_scores:
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#     sorted_fused_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
#     return [item['doc'] for item in sorted_fused_results[:n_results]]

# def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
#     if not keywords:
#         st.error("Please select at least one keyword.")
#         return None, []
#     with st.spinner("Searching papers and generating a detailed, multi-part report..."):
#         time_filter_dict = None
#         now = datetime.datetime.now()
#         if time_filter_type == "Year" and selected_year:
#             time_filter_dict = {"gte": f"{selected_year}-01-01", "lte": f"{selected_year}-12-31"}
#         elif time_filter_type == "Month" and selected_month:
#             year, month = map(int, selected_month.split('-'))
#             time_filter_dict = {"gte": f"{year}-{month:02d}-01", "lt": f"{year}-{(month % 12) + 1:02d}-01" if month < 12 else f"{year+1}-01-01"}
#         elif time_filter_type == "Last week":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}
#         elif time_filter_type == "Last month":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}
        
#         search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict)
#         if not search_results:
#             st.error("No papers found for the selected keywords and time window.")
#             return None, []

#         context = "You are a meticulous and expert research assistant. Analyze the following scientific paper excerpts.\n\n"
#         for i, result in enumerate(search_results):
#             meta = result.get('metadata', {})
#             title = meta.get('title', 'N/A')
#             link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#             content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
#             context += f"SOURCE [{i+1}]:\n"
#             context += f"Title: {title}\n"
#             context += f"Link: {link}\n"
#             context += f"Content: {content_preview}\n---\n\n"
        
#         prompt = f"""{context}
# ---
# **TASK:**

# Based *only* on the provided paper sources above, generate a detailed, multi-part report. You must follow these instructions exactly:

# **Part 1: Thematic Analysis**
# Generate the following sections. For "Key Methodological Advances," "Emerging Trends," and "Overall Summary," you MUST provide a detailed, extended analysis of at least two paragraphs or a comprehensive bulleted list. Go beyond a simple list; explain the significance and synthesize information across multiple sources.

#    ### Diseases: List the specific diseases, conditions, or traits studied.
#    ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries.
#    ### Key Methodological Advances: Describe significant methods, pipelines, or statistical approaches. Explain *why* they are important advances.
#    ### Emerging Trends: Identify future directions and new research areas. Synthesize repeated themes to explain what trends are emerging in the field.
#    ### Overall Summary: Provide a comprehensive textual summary of the key findings and clinical implications.

# **CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].`

# **Part 2: Key Paper Summaries**
# Create a new section titled ### Key Paper Summaries. Under this heading, identify the top 3 most relevant papers from the sources and provide a concise, one-paragraph summary for each. After each summary, you **MUST** include a direct link to the paper on a new line, formatted as: `[Source Link](the_actual_link)`.

# **Part 3: References**
# Create a final section titled ### References. Under this heading, you **MUST** list all the paper sources provided above. The number for each reference must correspond to the citation markers used in Part 1. Format each entry as a numbered list item: `1. [Paper Title](Paper Link)`.
# """
#         analysis = post_message_vertexai(prompt)
#         return analysis, search_results

# def display_paper_management():
#     st.subheader("Add Papers to Database")
#     uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
#     uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
#     json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
#     if uploaded_pdfs and st.button("Add to Database"):
#         with st.spinner("Adding papers to databases..."):
#             for uploaded_file in uploaded_pdfs:
#                 base_name = os.path.splitext(uploaded_file.name)[0]
#                 metadata = json_map.get(base_name, {'title': base_name})
#                 metadata['paper_id'] = uploaded_file.name
#                 pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
#                 paper_content = read_pdf_content(pdf_content_bytes)
#                 if paper_content:
#                     st.session_state.vector_db.add_paper(paper_id=uploaded_file.name, content=paper_content, metadata=metadata)
#                     st.success(f"Successfully added '{uploaded_file.name}' to the database.")
#         st.rerun()

# def display_chat_history():
#     st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
#     if not st.session_state.conversations:
#         st.caption("No past analyses found.")
#         return

#     grouped_convs = defaultdict(list)
#     sorted_conv_ids = sorted(st.session_state.conversations.keys(), reverse=True)
#     for conv_id in sorted_conv_ids:
#         try:
#             timestamp_str = conv_id.split('_')[1]
#             ts = float(timestamp_str)
#             conv_date = datetime.datetime.fromtimestamp(ts)
#             month_key = conv_date.strftime("%Y-%m")
#             title = st.session_state.conversations[conv_id].get("title", "Chat...")
#             grouped_convs[month_key].append((conv_id, title))
#         except (IndexError, ValueError):
#             continue
    
#     now = datetime.datetime.now()
#     current_month_key = now.strftime("%Y-%m")
    
#     for month_key in sorted(grouped_convs.keys(), reverse=True):
#         if month_key == current_month_key:
#             st.markdown("<h5>Recent</h5>", unsafe_allow_html=True)
#         else:
#             display_date = datetime.datetime.strptime(month_key, "%Y-%m")
#             st.markdown(f"<h5>{display_date.strftime('%B %Y')}</h5>", unsafe_allow_html=True)

#         for conv_id, title in grouped_convs[month_key]:
#             if st.button(title, key=f"btn_{conv_id}", use_container_width=True):
#                 if st.session_state.active_conversation_id != conv_id:
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

# def main():
#     st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     style_path = os.path.join(current_dir, "style.css")
#     local_css(style_path)
#     initialize_session_state()

#     with st.sidebar:
#         if st.button("➕ New Analysis", use_container_width=True):
#             st.session_state.active_conversation_id = None
#             st.session_state.selected_keywords = []
#             st.rerun()

#         display_chat_history()

#         st.markdown("---")
#         with st.form(key="new_analysis_form"):
#             st.subheader("Start a New Analysis")
#             selected_keywords = st.multiselect("Select keywords (up to 3)", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []), max_selections=3)
#             time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
#             selected_year, selected_month = None, None
#             if time_filter_type == "Year":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 years = pd.to_datetime(dates, errors='coerce').dropna().year.unique()
#                 selected_year = st.selectbox("Select year", sorted(years, reverse=True)) if len(years) > 0 else st.write("No papers with years found.")
#             elif time_filter_type == "Month":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 months = pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique()
#                 selected_month = st.selectbox("Select month", sorted(months, reverse=True)) if len(months) > 0 else st.write("No papers with months found.")
            
#             if st.form_submit_button("Search & Analyze"):
#                 analysis_result, retrieved_papers = process_keyword_search(selected_keywords, time_filter_type, selected_year, selected_month)
#                 if analysis_result:
#                     conv_id = f"conv_{time.time()}"
#                     initial_message = {"role": "assistant", "content": f"**Analysis for: {', '.join(selected_keywords)}**\n\n{analysis_result}"}
#                     title = generate_conversation_title(analysis_result)
#                     st.session_state.conversations[conv_id] = {
#                         "title": title, 
#                         "messages": [initial_message], 
#                         "keywords": selected_keywords,
#                         "retrieved_papers": retrieved_papers
#                     }
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

#         st.markdown("---")
#         with st.expander("Paper Management"):
#             display_paper_management()

#     st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

#     if st.session_state.active_conversation_id is None:
#         st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
#     else:
#         active_id = st.session_state.active_conversation_id
#         active_conv = st.session_state.conversations[active_id]
        
#         # <<< FIX: REVERTING TO THE ORIGINAL, WORKING DISPLAY LOGIC >>>
        
#         # 1. First, loop through and display all chat messages.
#         for message in active_conv["messages"]:
#             avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         # 2. THEN, display the expander with retrieved papers.
#         # This simpler, sequential structure avoids rendering conflicts.
#         if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
#             with st.expander("Download Retrieved Papers for this Analysis"):
#                 for paper_index, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'N/A')
#                     paper_id = paper.get('paper_id')

#                     col1, col2 = st.columns([4, 1])
#                     with col1:
#                         st.markdown(f"**{paper_index+1}. {title}**")
#                         if link != 'N/A':
#                             st.markdown(f"   - Link: [{link}]({link})")
#                     with col2:
#                         if paper_id:
#                             pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
#                             if pdf_bytes:
#                                 st.download_button(
#                                     label="Download PDF",
#                                     data=pdf_bytes,
#                                     file_name=paper_id,
#                                     mime="application/pdf",
#                                     key=f"download_{active_id}_{paper_id}"
#                                 )

#         if prompt := st.chat_input("Ask a follow-up question..."):
#             active_conv["messages"].append({"role": "user", "content": prompt})
#             st.rerun()

#     if st.session_state.active_conversation_id and st.session_state.conversations[st.session_state.active_conversation_id]["messages"][-1]["role"] == "user":
#         active_conv = st.session_state.conversations[st.session_state.active_conversation_id]
#         with st.spinner("Thinking..."):
#             chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in active_conv["messages"]])
#             full_context = ""
#             if active_conv.get("retrieved_papers"):
#                 full_context += "Here is the full context of every paper found in the initial analysis:\n\n"
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#                     content_preview = (meta.get('abstract') or paper.get('content') or '')[:4000]
#                     full_context += f"SOURCE [{i+1}]:\nTitle: {title}\nLink: {link}\nContent: {content_preview}\n---\n\n"
            
#             full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
# Your task is to answer the user's last message based on the chat history and the full context from the paper sources provided below.
# When the user asks you to list the papers or for references, you MUST format the response as a numbered list with clickable markdown links: `1. [Paper Title](Paper Link)`.

# --- CHAT HISTORY ---
# {chat_history}
# --- END CHAT HISTORY ---

# --- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
# {full_context}
# --- END FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---

# Assistant Response:"""
            
#             response_text = post_message_vertexai(full_prompt)
#             if response_text:
#                 active_conv["messages"].append({"role": "assistant", "content": response_text})
#                 st.rerun()

# if __name__ == "__main__":
#     main()
















































# # 01/09 Bir onceki app.py yukaridaki yenilenmis chat history be cliklable link ozellikleri var ayrica paragraflar genisledi ve daha detayli analiz yapiliyor.
# # Simdi keyword search ve daha cok paper getirip analiz yapmaya calisacagim herhangi bir kisitlama olmayacak onu arka tarafta halldecegiz.

# # app/main.py

# import streamlit as st
# import platform
# import requests
# import time
# import json
# import PyPDF2
# import io
# import yaml
# import os
# import sys
# from typing import List, Dict, Any
# import datetime
# from dateutil import parser as date_parser
# from collections import defaultdict

# import vertexai
# from vertexai.generative_models import GenerativeModel
# from google.cloud import storage
# from google.api_core.exceptions import NotFound

# # SQLite3 Patch for Linux environments
# if platform.system() == "Linux":
#     try:
#         __import__("pysqlite3")
#         import sys
#         sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
#     except ImportError:
#         st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

# try:
#     from elasticsearch_utils import get_es_manager
#     from vector_db import get_vector_db
# except ImportError as e:
#     st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
#     st.stop()

# # --- App Configuration & Constants ---
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# try:
#     config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
#     with open(config_path, 'r') as file:
#         config = yaml.safe_load(file)
# except FileNotFoundError:
#     st.error("Configuration file 'config/config.yaml' not found.")
#     st.stop()
# except Exception as e:
#     st.error(f"Error loading config.yaml: {e}")
#     st.stop()

# # --- Configuration from Streamlit Secrets ---
# try:
#     # --- Elastic Cloud Configuration ---
#     ELASTIC_CLOUD_ID = st.secrets["elasticsearch"]["cloud_id"]
#     ELASTIC_USER = st.secrets["elasticsearch"]["username"]
#     ELASTIC_PASSWORD = st.secrets["elasticsearch"]["password"]

#     # --- Vertex AI Configurations ---
#     # Reading lowercase keys to match secrets.toml best practice
#     VERTEXAI_PROJECT = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]
#     VERTEXAI_LOCATION = st.secrets["vertex_ai"]["VERTEXAI_LOCATION"]
#     VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

#     # --- GCS Configuration ---
#     GCS_BUCKET_NAME = st.secrets["app_config"]["gcs_bucket_name"]

#     # --- Google Service Account Credentials ---
#     # 1. Read the secret, which is a Streamlit AttrDict object.
#     gcp_service_account_secret = st.secrets["gcp_service_account"]
    
#     # 2. Convert the AttrDict to a standard Python dictionary.
#     #    THIS IS THE FIX for the "not JSON serializable" error.
#     GOOGLE_CREDENTIALS_DICT = dict(gcp_service_account_secret)
    
#     # 3. Write the standard dictionary to a temporary file.
#     with open("gcp_credentials.json", "w") as f:
#         json.dump(GOOGLE_CREDENTIALS_DICT, f)
        
#     # 4. Set the environment variable for Google Cloud libraries to find the file.
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

# except KeyError as e:
#     st.error(f"Missing secret configuration for key: '{e}'. Please check that your .streamlit/secrets.toml file (for local development) or your Streamlit Cloud secrets match the required structure.")
#     st.stop()

# # --- Interface Constants ---
# GENETICS_KEYWORDS = [
#     "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
# ]
# USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
# BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjQgMjQifCBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVM McDonaldsIDUgMTIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"

# # --- API and Helper Functions ---
# def post_message_vertexai(input_text: str) -> str | None:
#     try:
#         vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
#         model = GenerativeModel(VERTEXAI_MODEL_ID)
#         generation_config = {"temperature": 0.25, "max_output_tokens": 8192}
#         response = model.generate_content([input_text], generation_config=generation_config)
#         return response.text
#     except Exception as e:
#         st.error(f"An error occurred with the Vertex AI API: {e}")
#         import traceback
#         st.error(f"Traceback: {traceback.format_exc()}")
#         return None

# @st.cache_data
# def get_pdf_bytes_from_gcs(bucket_name: str, blob_name: str) -> bytes | None:
#     try:
#         storage_client = storage.Client()
#         bucket = storage_client.bucket(bucket_name)
#         blob = bucket.blob(blob_name)
#         return blob.download_as_bytes()
#     except NotFound:
#         st.warning(f"File not found in GCS: {blob_name}")
#         return None
#     except Exception as e:
#         st.error(f"Failed to download from GCS: {e}")
#         return None

# def initialize_session_state():
#     if 'es_manager' not in st.session_state:
#         st.session_state.es_manager = get_es_manager(cloud_id=ELASTIC_CLOUD_ID, username=ELASTIC_USER, password=ELASTIC_PASSWORD)
#     if 'vector_db' not in st.session_state:
#         st.session_state.vector_db = get_vector_db(_es_manager=st.session_state.es_manager)
#     if 'conversations' not in st.session_state:
#         st.session_state.conversations = {}
#     if 'active_conversation_id' not in st.session_state:
#         st.session_state.active_conversation_id = None
#     if 'selected_keywords' not in st.session_state:
#         st.session_state.selected_keywords = []

# def local_css(file_name):
#     try:
#         with open(file_name) as f:
#             st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#     except FileNotFoundError:
#         st.warning(f"CSS file '{file_name}' not found. Using default styles.")

# def read_pdf_content(pdf_file: io.BytesIO) -> str | None:
#     try:
#         pdf_reader = PyPDF2.PdfReader(pdf_file)
#         return "".join(page.extract_text() for page in pdf_reader.pages)
#     except Exception as e:
#         st.error(f"Error reading PDF: {e}")
#         return None

# def generate_conversation_title(conversation_history: str) -> str:
#     prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
#     title = post_message_vertexai(prompt)
#     if title:
#         return title.strip().replace('"', '')
#     return "New Chat"

# def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 50, score_threshold: float = 0.005) -> list:
#     """
#     Performs a hybrid search combining vector and Elasticsearch results.
#     Filters results based on a relevance score threshold.
#     """
#     vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
#     es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results)
    
#     fused_scores = {}
#     k = 60 # A constant for reciprocal rank fusion

#     # Process vector database results
#     for i, doc in enumerate(vector_results):
#         rank = i + 1
#         paper_id = doc.get('paper_id')
#         if paper_id:
#             if paper_id not in fused_scores:
#                 fused_scores[paper_id] = {'score': 0, 'doc': doc}
#             fused_scores[paper_id]['score'] += 1 / (k + rank)

#     # Process Elasticsearch results
#     for i, hit in enumerate(es_results):
#         rank = i + 1
#         paper_id = hit['_id']
#         doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
        
#         if paper_id not in fused_scores:
#             fused_scores[paper_id] = {'score': 0, 'doc': doc_content}
#         fused_scores[paper_id]['score'] += 1 / (k + rank)

#     # Sort and filter by threshold
#     sorted_fused_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
    
#     # Apply score threshold and limit to a reasonable number for model processing
#     # The aim is to get high-quality papers. Max 15-20 papers for detailed analysis in LLM.
#     filtered_results = [
#         item['doc'] for item in sorted_fused_results 
#         if item['score'] >= score_threshold
#     ][:20] # Limiting to 20 for robust LLM processing, but the threshold is primary.

#     return filtered_results


# def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
#     if not keywords:
#         st.error("Please select at least one keyword.")
#         return None, []
#     with st.spinner("Searching papers and generating a detailed, multi-part report..."):
#         time_filter_dict = None
#         now = datetime.datetime.now()
#         if time_filter_type == "Year" and selected_year:
#             time_filter_dict = {"gte": f"{selected_year}-01-01", "lte": f"{selected_year}-12-31"}
#         elif time_filter_type == "Month" and selected_month:
#             year, month = map(int, selected_month.split('-'))
#             time_filter_dict = {"gte": f"{year}-{month:02d}-01", "lt": f"{year}-{(month % 12) + 1:02d}-01" if month < 12 else f"{year+1}-01-01"}
#         elif time_filter_type == "Last week":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d')}
#         elif time_filter_type == "Last month":
#             time_filter_dict = {"gte": (now - datetime.timedelta(days=31)).strftime('%Y-%m-%d')}
        
#         # Increase n_results to allow more initial papers to be considered before filtering
#         # The score_threshold will then refine this to the most relevant ones.
#         search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict, n_results=100) 
        
#         if not search_results:
#             st.error("No highly relevant papers found for the selected keywords and time window after applying the relevance threshold. Try broadening your keywords or adjusting the time filter.")
#             return None, []

#         context = "You are a meticulous and expert research assistant. Analyze the following scientific paper excerpts.\n\n"
#         for i, result in enumerate(search_results):
#             meta = result.get('metadata', {})
#             title = meta.get('title', 'N/A')
#             link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#             content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
#             context += f"SOURCE [{i+1}]:\n"
#             context += f"Title: {title}\n"
#             context += f"Link: {link}\n"
#             context += f"Content: {content_preview}\n---\n\n"
        
#         prompt = f"""{context}
# ---
# **TASK:**

# Based *only* on the provided paper sources above, generate a detailed, multi-part report. You must follow these instructions exactly:

# **Part 1: Thematic Analysis**
# Generate the following sections. For "Key Methodological Advances," "Emerging Trends," and "Overall Summary," you MUST provide a detailed, extended analysis of at least two paragraphs or a comprehensive bulleted list. Go beyond a simple list; explain the significance and synthesize information across multiple sources. Strive to make these sections as long and comprehensive as possible, leveraging all relevant information from the provided papers to create a rich narrative.

#    ### Diseases: List the specific diseases, conditions, or traits studied.
#    ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries.
#    ### Key Methodological Advances: Describe significant methods, pipelines, or statistical approaches. Explain *why* they are important advances.
#    ### Emerging Trends: Identify future directions and new research areas. Synthesize repeated themes to explain what trends are emerging in the field.
#    ### Overall Summary: Provide a comprehensive textual summary of the key findings and clinical implications.

# **CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].`

# **Part 2: Key Paper Summaries**
# Create a new section titled ### Key Paper Summaries. Under this heading, identify the top 3 most relevant papers from the sources and provide a concise, one-paragraph summary for each. After each summary, you **MUST** include a direct link to the paper on a new line, formatted as: `[Source Link](the_actual_link)`.

# **Part 3: References**
# Create a final section titled ### References. Under this heading, you **MUST** list all the paper sources provided above. The number for each reference must correspond to the citation markers used in Part 1. Format each entry as a numbered list item: `1. [Paper Title](Paper Link)`.
# """
#         analysis = post_message_vertexai(prompt)
#         return analysis, search_results

# def display_paper_management():
#     st.subheader("Add Papers to Database")
#     uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
#     uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
#     json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
#     if uploaded_pdfs and st.button("Add to Database"):
#         with st.spinner("Adding papers to databases..."):
#             for uploaded_file in uploaded_pdfs:
#                 base_name = os.path.splitext(uploaded_file.name)[0]
#                 metadata = json_map.get(base_name, {'title': base_name})
#                 metadata['paper_id'] = uploaded_file.name
#                 pdf_content_bytes = io.BytesIO(uploaded_file.getvalue())
#                 paper_content = read_pdf_content(pdf_content_bytes)
#                 if paper_content:
#                     st.session_state.vector_db.add_paper(paper_id=uploaded_file.name, content=paper_content, metadata=metadata)
#                     st.success(f"Successfully added '{uploaded_file.name}' to the database.")
#         st.rerun()

# def display_chat_history():
#     st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
#     if not st.session_state.conversations:
#         st.caption("No past analyses found.")
#         return

#     grouped_convs = defaultdict(list)
#     sorted_conv_ids = sorted(st.session_state.conversations.keys(), reverse=True)
#     for conv_id in sorted_conv_ids:
#         try:
#             timestamp_str = conv_id.split('_')[1]
#             ts = float(timestamp_str)
#             conv_date = datetime.datetime.fromtimestamp(ts)
#             month_key = conv_date.strftime("%Y-%m")
#             title = st.session_state.conversations[conv_id].get("title", "Chat...")
#             grouped_convs[month_key].append((conv_id, title))
#         except (IndexError, ValueError):
#             continue
    
#     now = datetime.datetime.now()
#     current_month_key = now.strftime("%Y-%m")
    
#     for month_key in sorted(grouped_convs.keys(), reverse=True):
#         if month_key == current_month_key:
#             st.markdown("<h5>Recent</h5>", unsafe_allow_html=True)
#         else:
#             display_date = datetime.datetime.strptime(month_key, "%Y-%m")
#             st.markdown(f"<h5>{display_date.strftime('%B %Y')}</h5>", unsafe_allow_html=True)

#         for conv_id, title in grouped_convs[month_key]:
#             if st.button(title, key=f"btn_{conv_id}", use_container_width=True):
#                 if st.session_state.active_conversation_id != conv_id:
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

# def main():
#     st.set_page_config(layout="wide", page_title="Polo GGB Research Assistant")
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     style_path = os.path.join(current_dir, "style.css")
#     local_css(style_path)
#     initialize_session_state()

#     with st.sidebar:
#         if st.button("➕ New Analysis", use_container_width=True):
#             st.session_state.active_conversation_id = None
#             st.session_state.selected_keywords = []
#             st.rerun()

#         display_chat_history()

#         st.markdown("---")
#         with st.form(key="new_analysis_form"):
#             st.subheader("Start a New Analysis")
#             # Removed max_selections to allow unlimited keywords
#             selected_keywords = st.multiselect("Select keywords", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []))
#             time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
#             selected_year, selected_month = None, None
#             if time_filter_type == "Year":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 years = pd.to_datetime(dates, errors='coerce').dropna().year.unique()
#                 selected_year = st.selectbox("Select year", sorted(years, reverse=True)) if len(years) > 0 else st.write("No papers with years found.")
#             elif time_filter_type == "Month":
#                 import pandas as pd
#                 all_papers = st.session_state.vector_db.get_all_papers()
#                 dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
#                 months = pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique()
#                 selected_month = st.selectbox("Select month", sorted(months, reverse=True)) if len(months) > 0 else st.write("No papers with months found.")
            
#             if st.form_submit_button("Search & Analyze"):
#                 analysis_result, retrieved_papers = process_keyword_search(selected_keywords, time_filter_type, selected_year, selected_month)
#                 if analysis_result:
#                     conv_id = f"conv_{time.time()}"
#                     initial_message = {"role": "assistant", "content": f"**Analysis for: {', '.join(selected_keywords)}**\n\n{analysis_result}"}
#                     title = generate_conversation_title(analysis_result)
#                     st.session_state.conversations[conv_id] = {
#                         "title": title, 
#                         "messages": [initial_message], 
#                         "keywords": selected_keywords,
#                         "retrieved_papers": retrieved_papers
#                     }
#                     st.session_state.active_conversation_id = conv_id
#                     st.rerun()

#         st.markdown("---")
#         with st.expander("Paper Management"):
#             display_paper_management()

#     st.markdown("<h1>🧬 Polo GGB Research Assistant</h1>", unsafe_allow_html=True)

#     if st.session_state.active_conversation_id is None:
#         st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
#     else:
#         active_id = st.session_state.active_conversation_id
#         active_conv = st.session_state.conversations[active_id]
        
#         # <<< FIX: REVERTING TO THE ORIGINAL, WORKING DISPLAY LOGIC >>>
        
#         # 1. First, loop through and display all chat messages.
#         for message in active_conv["messages"]:
#             avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         # 2. THEN, display the expander with retrieved papers.
#         # This simpler, sequential structure avoids rendering conflicts.
#         if "retrieved_papers" in active_conv and active_conv["retrieved_papers"]:
#             with st.expander("Download Retrieved Papers for this Analysis"):
#                 # Display the count of papers retrieved
#                 st.write(f"Retrieved {len(active_conv['retrieved_papers'])} highly relevant papers.")
#                 for paper_index, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'N/A')
#                     paper_id = paper.get('paper_id')

#                     col1, col2 = st.columns([4, 1])
#                     with col1:
#                         st.markdown(f"**{paper_index+1}. {title}**")
#                         if link != 'N/A':
#                             st.markdown(f"   - Link: [{link}]({link})")
#                     with col2:
#                         if paper_id:
#                             pdf_bytes = get_pdf_bytes_from_gcs(GCS_BUCKET_NAME, paper_id)
#                             if pdf_bytes:
#                                 st.download_button(
#                                     label="Download PDF",
#                                     data=pdf_bytes,
#                                     file_name=paper_id,
#                                     mime="application/pdf",
#                                     key=f"download_{active_id}_{paper_id}"
#                                 )

#         if prompt := st.chat_input("Ask a follow-up question..."):
#             active_conv["messages"].append({"role": "user", "content": prompt})
#             st.rerun()

#     if st.session_state.active_conversation_id and st.session_state.conversations[st.session_state.active_conversation_id]["messages"][-1]["role"] == "user":
#         active_conv = st.session_state.conversations[st.session_state.active_conversation_id]
#         with st.spinner("Thinking..."):
#             chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in active_conv["messages"]])
#             full_context = ""
#             if active_conv.get("retrieved_papers"):
#                 full_context += "Here is the full context of every paper found in the initial analysis:\n\n"
#                 for i, paper in enumerate(active_conv["retrieved_papers"]):
#                     meta = paper.get('metadata', {})
#                     title = meta.get('title', 'N/A')
#                     link = meta.get('url') or meta.get('link') or meta.get('doi_url', 'Not available')
#                     content_preview = (meta.get('abstract') or paper.get('content') or '')[:4000]
#                     full_context += f"SOURCE [{i+1}]:\nTitle: {title}\nLink: {link}\nContent: {content_preview}\n---\n\n"
            
#             full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
# Your task is to answer the user's last message based on the chat history and the full context from the paper sources provided below.
# When the user asks you to list the papers or for references, you MUST format the response as a numbered list with clickable markdown links: `1. [Paper Title](Paper Link)`.

# --- CHAT HISTORY ---
# {chat_history}
# --- END CHAT HISTORY ---

# --- FULL LITERATURE CONTEXT FOR THIS ANALYSIS ---
# {full_context}
# --- END LITERATURE CONTEXT FOR THIS ANALYSIS ---

# Assistant Response:"""
            
#             response_text = post_message_vertexai(full_prompt)
#             if response_text:
#                 active_conv["messages"].append({"role": "assistant", "content": response_text})
#                 st.rerun()

# if __name__ == "__main__":
#     main()














































# 01/09 Ikinci deneme

# app/main.py

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

# SQLite3 Patch for Linux environments
if platform.system() == "Linux":
    try:
        # Import the module
        import pysqlite3
        import sys
        # Directly assign the imported module to the 'sqlite3' key
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        # This part remains the same, for when the package isn't installed
        st.warning("pysqlite3-binary not found. ChromaDB may fail on this environment.")

try:
    from elasticsearch_utils import get_es_manager
    from vector_db import get_vector_db
except ImportError as e:
    st.error(f"Failed to import a local module: {e}. Ensure all .py files are in the 'app/' directory.")
    st.stop()

# --- App Configuration & Constants ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
# <<< FIX: Restored the correct BOT_AVATAR SVG string >>>
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

# <<< NEW: Robust link retrieval helper function >>>
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

# def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 50, score_threshold: float = 0.005) -> list:
#     vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
#     # <<< MODIFIED: Pass 'operator="AND"' to enforce all keywords are present >>>
#     es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="AND")
    
#     fused_scores = defaultdict(lambda: {'score': 0, 'doc': None})
#     k = 60 

#     for i, doc in enumerate(vector_results):
#         rank = i + 1
#         paper_id = doc.get('paper_id')
#         if paper_id:
#             fused_scores[paper_id]['score'] += 1 / (k + rank)
#             if fused_scores[paper_id]['doc'] is None:
#                  fused_scores[paper_id]['doc'] = doc

#     for i, hit in enumerate(es_results):
#         rank = i + 1
#         paper_id = hit['_id']
#         fused_scores[paper_id]['score'] += 1 / (k + rank)
#         if fused_scores[paper_id]['doc'] is None:
#             doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
#             fused_scores[paper_id]['doc'] = doc_content

#     # Filter out any entries that didn't get a doc object assigned (unlikely but safe)
#     valid_fused_results = [item for item in fused_scores.values() if item['doc'] is not None]

#     sorted_fused_results = sorted(valid_fused_results, key=lambda x: x['score'], reverse=True)
    
#     filtered_results = [
#         item['doc'] for item in sorted_fused_results 
#         if item['score'] >= score_threshold
#     ][:20]

#     return filtered_results







def perform_hybrid_search(keywords: list, time_filter_dict: dict | None = None, n_results: int = 50, score_threshold: float = 0.005, max_final_results: int = 20) -> list:
    # <<< MODIFICATION: The Elasticsearch 'AND' search is now the first and most critical step. >>>
    # This search acts as our definitive filter. Only papers found here are eligible for the final list.
    es_results = st.session_state.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="AND")

    # <<< MODIFICATION: Create a set of valid paper IDs from the strict 'AND' search. >>>
    # This is extremely efficient for checking if a paper meets our mandatory criteria.
    valid_paper_ids = {hit['_id'] for hit in es_results}

    # <<< MODIFICATION: If the strict 'AND' search returns no results, we stop immediately. >>>
    # This is more efficient and provides a clearer message to the user.
    if not valid_paper_ids:
        return []

    # The vector search now primarily helps in re-ranking the already-validated papers.
    vector_results = st.session_state.vector_db.search_by_keywords(keywords, n_results=n_results)
    
    fused_scores = defaultdict(lambda: {'score': 0, 'doc': None})
    k = 60 

    # Process vector results, but only consider papers that are in our valid_paper_ids set.
    for i, doc in enumerate(vector_results):
        rank = i + 1
        paper_id = doc.get('paper_id')
        # <<< MODIFICATION: Crucial check to ensure the paper contains all keywords. >>>
        if paper_id and paper_id in valid_paper_ids:
            fused_scores[paper_id]['score'] += 1 / (k + rank)
            if fused_scores[paper_id]['doc'] is None:
                 fused_scores[paper_id]['doc'] = doc

    # Process Elasticsearch results (all of which are guaranteed to be valid).
    for i, hit in enumerate(es_results):
        rank = i + 1
        paper_id = hit['_id']
        # The check 'paper_id in valid_paper_ids' is redundant here but safe.
        fused_scores[paper_id]['score'] += 1 / (k + rank)
        if fused_scores[paper_id]['doc'] is None:
            doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
            fused_scores[paper_id]['doc'] = doc_content

    # Filter out any entries that didn't get a doc object assigned.
    valid_fused_results = [item for item in fused_scores.values() if item['doc'] is not None]

    # Sort the combined results by the fused score.
    sorted_fused_results = sorted(valid_fused_results, key=lambda x: x['score'], reverse=True)
    
    # <<< MODIFICATION: The final list is now filtered by the score threshold and limited by max_final_results. >>>
    # This makes the '20' limit a configurable parameter and not a hardcoded value.
    # The number of results will now correctly reflect how many papers matched ALL criteria.
    filtered_results = [
        item['doc'] for item in sorted_fused_results 
        if item['score'] >= score_threshold
    ][:max_final_results]

    return filtered_results






def process_keyword_search(keywords: list, time_filter_type: str | None, selected_year: int | None, selected_month: str | None) -> tuple[str | None, list]:
    if not keywords:
        st.error("Please select at least one keyword.")
        return None, []
    with st.spinner("Searching for highly relevant papers and generating a comprehensive, in-depth report..."):
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
        
        search_results = perform_hybrid_search(keywords, time_filter_dict=time_filter_dict, n_results=100) 
        
        if not search_results:
            st.error("No papers found that contain ALL of the selected keywords within the specified time window. Please try a different combination of keywords.")
            return None, []

        context = "You are a world-class scientific analyst and expert research assistant. Your primary objective is to generate the most detailed and extensive report possible based on the following scientific paper excerpts.\n\n"
        for i, result in enumerate(search_results):
            meta = result.get('metadata', {})
            title = meta.get('title', 'N/A')
            link = get_paper_link(meta)
            content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
            context += f"SOURCE [{i+1}]:\n"
            context += f"Title: {title}\n"
            context += f"Link: {link}\n"
            context += f"Content: {content_preview}\n---\n\n"
        
        # <<< MODIFIED: Heavily enhanced prompt to demand a very long and detailed output >>>
        prompt = f"""{context}
---
**CRITICAL TASK:**

You are a world-class scientific analyst. Your task is to generate an exceptionally detailed and extensive multi-part report based *only* on the provided paper sources. The final report should be substantial in length, reflecting a deep synthesis of information from all provided papers.

**Part 1: Thematic Analysis**
For the sections "Key Methodological Advances," "Emerging Trends," and "Overall Summary," your analysis **MUST** be exhaustive. Generate at least **three long and detailed paragraphs** or a comprehensive multi-level bulleted list for each of these sections. Do not just list findings; you must deeply synthesize information across multiple sources, explain the significance, compare and contrast approaches, and build a compelling narrative about the state of the research.

   ### Diseases: List the specific diseases, conditions, or traits studied.
   ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries mentioned across the papers.
   ### Key Methodological Advances: Provide an in-depth description of significant methods, pipelines, or statistical approaches. Explain *why* they are important advances, how they differ from previous methods, and what new possibilities they unlock.
   ### Emerging Trends: Identify future directions and new research areas. Synthesize recurring themes to explain what trends are emerging in the field. Discuss the implications of these trends for science and medicine.
   ### Overall Summary: Provide a comprehensive, multi-paragraph textual summary of the key findings and clinical implications. This should be a full executive summary, not a brief conclusion.

**CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].`

**Part 2: Key Paper Summaries**
Create a new section titled ### Key Paper Summaries. Under this heading, identify the top 3-5 most impactful papers from the sources and provide a detailed, one-paragraph summary for each. After each summary, you **MUST** include a direct link to the paper on a new line, formatted as: `[Source Link](the_actual_link)`.

**Part 3: References**
Create a final section titled ### References. Under this heading, you **MUST** list all the paper sources provided above. The number for each reference must correspond to the citation markers used in Part 1. Format each entry as a numbered list item: `1. [Paper Title](Paper Link)`.
"""
        analysis = post_message_vertexai(prompt)
        return analysis, search_results

def display_paper_management():
    st.subheader("Add Papers to Database")
    uploaded_pdfs = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=['pdf'], key="db_pdf_uploader")
    uploaded_jsons = st.file_uploader("Upload corresponding metadata JSON files", accept_multiple_files=True, type=['json'], key="db_json_uploader")
    json_map = {os.path.splitext(json_file.name)[0]: json.load(io.BytesIO(json_file.getvalue())) for json_file in uploaded_jsons or []}
    if uploaded_pdfs and st.button("Add to Database"):
        with st.spinner("Adding papers to databases..."):
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(current_dir, "style.css")
    local_css(style_path)
    initialize_session_state()

    with st.sidebar:
        if st.button("➕ New Analysis", use_container_width=True):
            st.session_state.active_conversation_id = None
            st.session_state.selected_keywords = []
            st.rerun()

        display_chat_history()

        st.markdown("---")
        with st.form(key="new_analysis_form"):
            st.subheader("Start a New Analysis")
            selected_keywords = st.multiselect("Select keywords", GENETICS_KEYWORDS, default=st.session_state.get('selected_keywords', []))
            time_filter_type = st.selectbox("Filter by Time Window", ["All time", "Year", "Month", "Last week", "Last month"])
            selected_year, selected_month = None, None
            if time_filter_type == "Year":
                import pandas as pd
                all_papers = st.session_state.vector_db.get_all_papers()
                dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
                years = sorted(pd.to_datetime(dates, errors='coerce').dropna().year.unique(), reverse=True)
                selected_year = st.selectbox("Select year", years) if years else st.write("No papers with years found.")
            elif time_filter_type == "Month":
                import pandas as pd
                all_papers = st.session_state.vector_db.get_all_papers()
                dates = [p['metadata'].get('publication_date') for p in all_papers if p['metadata'].get('publication_date')]
                months = sorted(pd.to_datetime(dates, errors='coerce').dropna().strftime('%Y-%m').unique(), reverse=True)
                selected_month = st.selectbox("Select month", months) if months else st.write("No papers with months found.")
            
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
            with st.expander("Download Retrieved Papers for this Analysis"):
                st.write(f"Retrieved {len(active_conv['retrieved_papers'])} highly relevant papers.")
                for paper_index, paper in enumerate(active_conv["retrieved_papers"]):
                    meta = paper.get('metadata', {})
                    title = meta.get('title', 'N/A')
                    # <<< MODIFIED: Using the robust get_paper_link function >>>
                    link = get_paper_link(meta)
                    paper_id = paper.get('paper_id')

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{paper_index+1}. {title}**")
                        if link != 'Not available':
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
                    # <<< MODIFIED: Using the robust get_paper_link function >>>
                    link = get_paper_link(meta)
                    content_preview = (meta.get('abstract') or paper.get('content') or '')[:4000]
                    full_context += f"SOURCE [{i+1}]:\nTitle: {title}\nLink: {link}\nContent: {content_preview}\n---\n\n"
            
            full_prompt = f"""Continue our conversation. You are the Polo-GGB Research Assistant.
Your task is to answer the user's last message based on the chat history and the full context from the paper sources provided below.
When the user asks you to list the papers or for references, you MUST format the response as a numbered list with clickable markdown links: `1. [Paper Title](Paper Link)`.

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

















