# app/frontend/ui.py
"""
Frontend UI Layer - Clean separation from backend logic
This handles all Streamlit UI components and calls backend APIs
"""

import streamlit as st
import time
import os
from typing import Dict, List, Any, Optional
import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import ResearchAssistantAPI
from auth import show_login_page, show_logout_button

class ResearchAssistantUI:
    def __init__(self, api: ResearchAssistantAPI):
        """Initialize UI with backend API"""
        self.api = api
        
        # UI Constants
        self.GENETICS_KEYWORDS = [
            "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
        ]
        
        self.USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0OTUwNTciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0iZmVhdGhlciBmZWF0aGVyLXVzZXIiPjxwYXRoIGQ9Ik0yMCAyMWMwLTMuODctMy4xMy03LTctN3MtNyAzLjEzLTcgN1oiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg=="
        self.BOT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDdiZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOS41IDEyLjVsLTggNkw5LjUgMjEgMTEgMTRsMS41IDcgNy41LTEuNS03LjUgMy4vTDE0IDQuNSA5LjUgOHoiLz48cGF0aCBkPSJNMy41IDEwLjVMOCA1bDIgMy41Ii8+PHBhdGggZD0iTTE4IDNMMTAuNSAxMC41Ii8+PC9zdmc+"
    
    def initialize_session_state(self):
        """Initialize user session state"""
        current_user = st.session_state.get('username', 'default')
        
        # Check if this is a new login (user data not loaded yet)
        if current_user != 'default' and self.get_user_key('conversations') not in st.session_state:
            # Load user data from backend
            try:
                user_data = self.api.get_user_data(current_user)
                if user_data:
                    # Set all user data from backend
                    self.set_user_session('conversations', user_data.get('conversations', {}))
                    self.set_user_session('active_conversation_id', user_data.get('active_conversation_id'))
                    self.set_user_session('selected_keywords', user_data.get('selected_keywords', []))
                    self.set_user_session('search_mode', user_data.get('search_mode', 'all_keywords'))
                    self.set_user_session('uploaded_papers', user_data.get('uploaded_papers', []))
                    self.set_user_session('custom_summary_chat', user_data.get('custom_summary_chat', []))
                else:
                    # Initialize empty user data if none exists
                    self._initialize_empty_user_data()
            except Exception as e:
                print(f"Failed to load user data: {e}")
                self._initialize_empty_user_data()
        
        # Initialize user-specific session state (fallback for default user)
        self._initialize_empty_user_data()
        
        # Global session state (shared across users)
        if 'is_loading_analysis' not in st.session_state:
            st.session_state.is_loading_analysis = False
        if 'loading_message' not in st.session_state:
            st.session_state.loading_message = ""
    
    def _initialize_empty_user_data(self):
        """Initialize empty user data"""
        if self.get_user_key('conversations') not in st.session_state:
            self.set_user_session('conversations', {})
        if self.get_user_key('active_conversation_id') not in st.session_state:
            self.set_user_session('active_conversation_id', None)
        if self.get_user_key('selected_keywords') not in st.session_state:
            self.set_user_session('selected_keywords', [])
        if self.get_user_key('search_mode') not in st.session_state:
            self.set_user_session('search_mode', "all_keywords")
        if self.get_user_key('uploaded_papers') not in st.session_state:
            self.set_user_session('uploaded_papers', [])
        if self.get_user_key('custom_summary_chat') not in st.session_state:
            self.set_user_session('custom_summary_chat', [])
    
    def get_user_key(self, key):
        """Get user-specific session key"""
        current_user = st.session_state.get('username', 'default')
        return f"{key}_{current_user}"
    
    def get_user_session(self, key, default=None):
        """Get user-specific session value"""
        user_key = self.get_user_key(key)
        return st.session_state.get(user_key, default)
    
    def set_user_session(self, key, value):
        """Set user-specific session value"""
        user_key = self.get_user_key(key)
        st.session_state[user_key] = value
        
        # Auto-sync to backend for important data
        if key in ['conversations', 'selected_keywords', 'search_mode', 'uploaded_papers', 'custom_summary_chat', 'active_conversation_id']:
            username = st.session_state.get('username')
            if username and username != 'default':
                try:
                    user_data = {
                        'selected_keywords': self.get_user_session('selected_keywords', []),
                        'search_mode': self.get_user_session('search_mode', 'all_keywords'),
                        'uploaded_papers': self.get_user_session('uploaded_papers', []),
                        'custom_summary_chat': self.get_user_session('custom_summary_chat', []),
                        'active_conversation_id': self.get_user_session('active_conversation_id')
                    }
                    self.api.save_user_data(username, user_data)
                except Exception as e:
                    print(f"Failed to sync to backend: {e}")
    
    def show_loading_overlay(self, message="Generating new analysis..."):
        """Show loading overlay"""
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
    
    def local_css(self, file_name):
        """Load local CSS file"""
        try:
            with open(file_name) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning(f"CSS file '{file_name}' not found. Using default styles.")
    
    def add_responsive_meta_tags(self):
        """Add responsive meta tags for better mobile experience"""
        st.markdown("""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="theme-color" content="#0E1117">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        """, unsafe_allow_html=True)
    
    def create_responsive_layout(self):
        """Create responsive layout containers"""
        # Add responsive container
        st.markdown("""
        <div class="responsive-container">
            <div class="main-content">
        """, unsafe_allow_html=True)
    
    def close_responsive_layout(self):
        """Close responsive layout containers"""
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def delete_conversation(self, conv_id: str):
        """Delete conversation via backend"""
        try:
            conversations = self.get_user_session('conversations', {})
            
            if conv_id not in conversations:
                st.error("Conversation not found")
                return False
            
            # Remove from local session
            del conversations[conv_id]
            self.set_user_session('conversations', conversations)
            
            # If this was the active conversation, clear it
            if self.get_user_session('active_conversation_id') == conv_id:
                self.set_user_session('active_conversation_id', None)
            
            # Remove from backend
            username = st.session_state.get('username')
            if username:
                self.api.delete_conversation(username, conv_id)
            
            return True
        except Exception as e:
            st.error(f"Failed to delete conversation: {e}")
            return False
    
    def display_chat_history(self):
        """Display chat history with delete functionality"""
        st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
        
        conversations = self.get_user_session('conversations', {})
        if not conversations:
            st.caption("No past analyses found.")
            return
        
        # Add bulk actions (only show if there are conversations)
        if len(conversations) > 1:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("× Clear All", help="Delete all conversations", key="clear_all_btn", type="secondary"):
                    if "confirm_clear_all" not in st.session_state:
                        st.session_state["confirm_clear_all"] = True
                        st.rerun()
                    else:
                        # Clear all conversations
                        deleted_count = 0
                        for conv_id in list(conversations.keys()):
                            if self.delete_conversation(conv_id):
                                deleted_count += 1
                        
                        if deleted_count > 0:
                            st.success(f"Deleted {deleted_count} conversations!")
                            if "confirm_clear_all" in st.session_state:
                                del st.session_state["confirm_clear_all"]
                            st.rerun()
                        else:
                            st.error("Failed to delete conversations")
            
            if st.session_state.get("confirm_clear_all", False):
                st.warning("⚠️ Click '× Clear All' again to confirm deletion of ALL conversations")
        
        # Group conversations by month
        from collections import defaultdict
        grouped_convs = defaultdict(list)
        
        def get_last_interaction_time(conv_id, conv_data):
            if 'last_interaction_time' in conv_data:
                return conv_data['last_interaction_time']
            
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
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    if st.button(title, key=f"btn_{conv_id}", use_container_width=True):
                        if self.get_user_session('active_conversation_id') != conv_id:
                            self.set_user_session('active_conversation_id', conv_id)
                            conversations[conv_id]['last_interaction_time'] = time.time()
                            self.set_user_session('conversations', conversations)
                            
                            # Save conversation to backend
                            username = st.session_state.get('username')
                            if username:
                                self.api.save_conversation(username, conv_id, conversations[conv_id])
                            
                            st.rerun()
                
                with col2:
                    if st.button("×", key=f"delete_{conv_id}", help="Delete", use_container_width=True, type="secondary"):
                        if f"confirm_delete_{conv_id}" not in st.session_state:
                            st.session_state[f"confirm_delete_{conv_id}"] = True
                            st.rerun()
                        else:
                            if self.delete_conversation(conv_id):
                                st.success("Conversation deleted!")
                                if f"confirm_delete_{conv_id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_{conv_id}"]
                                st.rerun()
                            else:
                                st.error("Failed to delete conversation")
                    
                    if st.session_state.get(f"confirm_delete_{conv_id}", False):
                        st.caption("Click × again to confirm")
    
    def display_paper_management(self):
        """Display PDF upload interface"""
        st.subheader("Upload PDF Files")
        st.info("Upload PDF files to generate custom summary of your documents.")
        
        uploaded_pdfs = st.file_uploader("Choose PDF files", accept_multiple_files=True, type=['pdf'], key="pdf_uploader_v2")
        
        if uploaded_pdfs and st.button("Add PDFs", type="primary"):
            with st.spinner("Processing PDF files..."):
                for uploaded_file in uploaded_pdfs:
                    paper_data = self.api.process_uploaded_pdf(uploaded_file, uploaded_file.name)
                    
                    if paper_data:
                        uploaded_papers = self.get_user_session('uploaded_papers', [])
                        uploaded_papers.append(paper_data)
                        self.set_user_session('uploaded_papers', uploaded_papers)
                        st.success(f"Successfully processed '{uploaded_file.name}' (Content length: {len(paper_data['content'])} chars)")
                    else:
                        st.error(f"Could not read content from '{uploaded_file.name}'. The PDF might be corrupted or password-protected.")
            st.rerun()
    
    def process_keyword_search(self, keywords: List[str], time_filter_type: str, search_mode: str = "all_keywords"):
        """Process keyword search via backend"""
        analysis_result, retrieved_papers, total_found = self.api.search_papers(keywords, time_filter_type, search_mode)
        
        if analysis_result:
            conv_id = f"conv_{time.time()}"
            search_mode_display = self.get_user_session('search_mode', 'all_keywords')
            selected_keywords = self.get_user_session('selected_keywords', [])
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
            
            title = self.api.generate_conversation_title(analysis_result)
            
            conversations = self.get_user_session('conversations', {})
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
            self.set_user_session('conversations', conversations)
            
            # Save conversation to backend
            username = st.session_state.get('username')
            if username:
                self.api.save_conversation(username, conv_id, conversations[conv_id])
            
            self.set_user_session('active_conversation_id', conv_id)
            self.set_user_session('custom_summary_chat', [])
            st.rerun()
        else:
            search_mode_text = "ALL of the selected keywords" if search_mode == "all_keywords" else "AT LEAST ONE of the selected keywords"
            st.error(f"No papers found that contain {search_mode_text} within the specified time window. Please try a different combination of keywords.")
    
    def generate_custom_summary(self, uploaded_papers: List[Dict]):
        """Generate custom summary via backend"""
        summary = self.api.generate_custom_summary(uploaded_papers)
        
        if summary:
            conv_id = f"custom_summary_{time.time()}"
            
            def generate_custom_summary_title(papers, summary_text):
                paper_count = len(papers)
                summary_lower = summary_text.lower()
                topics = []
                
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
                
                if topics:
                    topic_str = ', '.join(topics[:2])
                    return topic_str
                else:
                    first_words = ' '.join(summary_text.split()[:4])
                    return f"{first_words}..."
            
            title = generate_custom_summary_title(uploaded_papers, summary)
            
            initial_message = {
                "role": "assistant", 
                "content": f"**Custom Summary of {len(uploaded_papers)} Uploaded Papers**\n\n{summary}"
            }
            
            conversations = self.get_user_session('conversations', {})
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
            self.set_user_session('conversations', conversations)
            
            # Save conversation to backend
            username = st.session_state.get('username')
            if username:
                self.api.save_conversation(username, conv_id, conversations[conv_id])
            
            self.set_user_session('active_conversation_id', conv_id)
        else:
            st.error("Failed to generate summary. Please try again.")
    
    def render_main_interface(self):
        """Render the main application interface"""
        # Add responsive meta tags
        self.add_responsive_meta_tags()
        
        # Create responsive layout
        self.create_responsive_layout()
        
        # CSS styling
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
        
        /* Responsive sidebar */
        .css-1d391kg {
            width: 350px !important;
            min-width: 300px !important;
        }
        
        @media (max-width: 768px) {
            .css-1d391kg {
                width: 100% !important;
                min-width: 100% !important;
            }
        }
        
        /* Responsive main content */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
        }
        
        /* Fix white bars */
        .stApp > div {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Ensure full width */
        .main {
            width: 100% !important;
            max-width: 100% !important;
        }
        /* Responsive main content area - no fixed margins */
        @media (min-width: 769px) {
            .css-1y0tads {
                margin-left: 350px !important;
            }
        }
        
        @media (max-width: 768px) {
            .css-1y0tads {
                margin-left: 0 !important;
            }
        }
        
        /* Style for all primary/default buttons (blue-green gradient) */
        [data-testid="stButton"] > button {
            background: linear-gradient(90deg, #2E8B57, #3CB371) !important;
            color: white !important;
            border: none !important;
            border-radius: 5px !important;
            font-weight: bold !important;
            text-align: left;
            padding: 0.5rem;
            margin-bottom: 0.25rem;
        }
        [data-testid="stButton"] > button:hover {
            background: linear-gradient(90deg, #228B22, #32CD32) !important;
        }

        /* Style for secondary buttons (subtle delete buttons) */
        [data-testid="stSecondaryButton"] > button {
            background-color: #f8f9fa !important;
            color: #6c757d !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 3px !important;
            padding: 0.2rem 0.4rem !important;
            font-size: 0.8rem !important;
            min-height: 1.5rem !important;
            width: 100% !important;
            font-weight: bold !important;
        }
        [data-testid="stSecondaryButton"] > button:hover {
            background-color: #e9ecef !important;
            color: #495057 !important;
            border-color: #adb5bd !important;
        }
        
        /* Smaller warning messages */
        .stAlert {
            margin: 0.25rem 0;
            padding: 0.5rem;
            border-radius: 3px;
            font-size: 0.8rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<h1>🧬 POLO-GGB RESEARCH ASSISTANT</h1>", unsafe_allow_html=True)
        
        # Show loading overlay if analysis is in progress
        if st.session_state.get('is_loading_analysis', False):
            self.show_loading_overlay(st.session_state.loading_message)
            return  # Don't render the rest of the page while loading
        
        # Handle custom summary generation
        if st.session_state.get('generate_custom_summary', False):
            st.session_state.generate_custom_summary = False
            
            uploaded_papers = self.get_user_session('uploaded_papers', [])
            self.generate_custom_summary(uploaded_papers)
            
            st.session_state.is_loading_analysis = False
            st.rerun()
        
        # Show default message only if no active conversation
        active_conversation_id = self.get_user_session('active_conversation_id')
        if active_conversation_id is None:
            st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
        elif active_conversation_id is not None:
            conversations = self.get_user_session('conversations', {})
            active_conv = conversations[active_conversation_id]
            
            for message_index, message in enumerate(active_conv["messages"]):
                avatar = self.BOT_AVATAR if message["role"] == "assistant" else self.USER_AVATAR
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"], unsafe_allow_html=True)
                    
                    # Show papers section only for the first assistant message and regular analyses
                    if (message["role"] == "assistant" and message_index == 0 and 
                        "retrieved_papers" in active_conv and active_conv["retrieved_papers"] and 
                        active_conv.get("search_mode") != "custom"):
                        with st.expander("View and Download Retrieved Papers for this Analysis"):
                            for paper_index, paper in enumerate(active_conv["retrieved_papers"]):
                                meta = paper.get('metadata', {})
                                title = meta.get('title', 'N/A')
                                paper_id = paper.get('paper_id')
                                
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**{paper_index+1}. {title}**")
                                with col2:
                                    if paper_id:
                                        pdf_bytes = self.api.get_pdf_from_gcs(self.api.config['gcs_bucket_name'], paper_id)
                                        if pdf_bytes:
                                            st.download_button(
                                                label="Download PDF",
                                                data=pdf_bytes,
                                                file_name=paper_id,
                                                mime="application/pdf",
                                                key=f"download_{active_conversation_id}_{paper_id}"
                                            )
            
            # Chat input for follow-up questions
            if prompt := st.chat_input("Ask a follow-up question..."):
                active_conv["messages"].append({"role": "user", "content": prompt})
                active_conv['last_interaction_time'] = time.time()
                self.set_user_session('conversations', conversations)
                
                # Save conversation to backend
                username = st.session_state.get('username')
                if username:
                    self.api.save_conversation(username, active_conversation_id, active_conv)
                
                st.rerun()
        
        # Handle follow-up responses
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
                        link = self.api._get_paper_link(meta)
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
                
                response_text = self.api.generate_ai_response(full_prompt)
                if response_text:
                    retrieved_papers = active_conv.get("retrieved_papers", [])
                    search_mode = active_conv.get("search_mode", "all_keywords")
                    
                    response_text = self.api._display_citations_separately(response_text, retrieved_papers, retrieved_papers, search_mode, include_references=False)
                    active_conv["messages"].append({"role": "assistant", "content": response_text})
                    active_conv['last_interaction_time'] = time.time()
                    self.set_user_session('conversations', conversations)
                    
                    # Save conversation to backend
                    username = st.session_state.get('username')
                    if username:
                        self.api.save_conversation(username, active_conversation_id, active_conv)
                    
                    st.rerun()
        
        # Close responsive layout
        self.close_responsive_layout()
    
    def render_sidebar(self):
        """Render the sidebar interface"""
        with st.sidebar:
            # Show user info for all users
            if st.session_state.get('authenticated', False):
                st.markdown("---")
                st.markdown(f"**Logged in as:** {st.session_state.username}")
                if st.session_state.get('username') == 'admin':
                    st.markdown("**Role:** Administrator")
                else:
                    st.markdown("**Role:** User")
            
            if st.button("➕ New Analysis", use_container_width=True):
                self.set_user_session('active_conversation_id', None)
                self.set_user_session('selected_keywords', [])
                self.set_user_session('search_mode', "all_keywords")
                self.set_user_session('custom_summary_chat', [])
                st.rerun()
            
            self.display_chat_history()
            
            st.markdown("---")
            with st.form(key="new_analysis_form"):
                st.subheader("Start a New Analysis")
                
                st.info("**Data available until:** end of September 2025")
                
                selected_keywords = st.multiselect("Select keywords", self.GENETICS_KEYWORDS, default=self.get_user_session('selected_keywords', []))
                
                search_mode_options = {
                    "all_keywords": "Find papers containing ALL keywords",
                    "any_keyword": "Find papers containing AT LEAST ONE keyword"
                }
                search_mode_display = st.selectbox(
                    "Search Mode", 
                    options=list(search_mode_options.keys()),
                    format_func=lambda x: search_mode_options[x],
                    index=0 if self.get_user_session('search_mode', 'all_keywords') == 'all_keywords' else 1
                )
                
                time_filter_type = st.selectbox("Filter by Time Window", [
                    "Current year", 
                    "Last 3 months", 
                    "Last 6 months", 
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ])
                
                if st.form_submit_button("Search & Analyze"):
                    self.set_user_session('selected_keywords', selected_keywords)
                    self.set_user_session('search_mode', search_mode_display)
                    self.set_user_session('custom_summary_chat', [])
                    st.session_state.is_loading_analysis = True
                    st.session_state.loading_message = "Searching for highly relevant papers and generating a comprehensive, in-depth report..."
                    st.rerun()
            
            # Handle loading state and process analysis
            if st.session_state.get('is_loading_analysis', False):
                # Show loading overlay
                self.show_loading_overlay(st.session_state.loading_message)
                
                # Process the analysis
                analysis_result, retrieved_papers, total_found = self.process_keyword_search(
                    self.get_user_session('selected_keywords', []), 
                    time_filter_type, 
                    self.get_user_session('search_mode', 'all_keywords')
                )
                
                # Clear loading state
                st.session_state.is_loading_analysis = False
                
                if analysis_result:
                    conv_id = f"conv_{time.time()}"
                    search_mode_display = self.get_user_session('search_mode', 'all_keywords')
                    selected_keywords = self.get_user_session('selected_keywords', [])
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
                    title = self.api.generate_conversation_title(analysis_result)
                    
                    # Get user-specific conversations and add new one
                    conversations = self.get_user_session('conversations', {})
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
                    self.set_user_session('conversations', conversations)
                    # Clear any previous analysis and set new one
                    self.set_user_session('active_conversation_id', conv_id)
                    # Custom summaries are now in chat history
                    self.set_user_session('custom_summary_chat', [])  # Clear custom summary chat
                    st.rerun()
                else:
                    st.error("Failed to generate analysis. Please try again.")
            
            st.markdown("---")
            
            # Display uploaded papers count
            uploaded_papers = self.get_user_session('uploaded_papers', [])
            if uploaded_papers:
                st.info(f"{len(uploaded_papers)} papers uploaded")
                with st.expander("View uploaded papers"):
                    for i, paper in enumerate(uploaded_papers):
                        title = paper['metadata'].get('title', 'Unknown title')
                        st.write(f"{i+1}. {title}")
                
                if st.button("Generate Custom Summary", use_container_width=True, type="primary"):
                    self.set_user_session('active_conversation_id', None)
                    st.session_state.generate_custom_summary = True
                    st.session_state.is_loading_analysis = True
                    st.session_state.loading_message = "Generating summary of your uploaded papers..."
                    st.rerun()
                
                custom_summary_chat = self.get_user_session('custom_summary_chat', [])
                if custom_summary_chat:
                    st.markdown("---")
                    st.markdown("**Chat History:**")
                    for i, message in enumerate(custom_summary_chat[-3:]):
                        if message["role"] == "user":
                            st.caption(f"**You:** {message['content'][:50]}...")
                        else:
                            st.caption(f"**Assistant:** {message['content'][:50]}...")
                    
                    if len(custom_summary_chat) > 3:
                        st.caption(f"... and {len(custom_summary_chat) - 3} more messages")
                
                if st.button("Clear uploaded papers"):
                    self.set_user_session('uploaded_papers', [])
                    st.rerun()
            else:
                st.caption("No papers uploaded yet")
            
            with st.expander("Upload PDF Files"):
                self.display_paper_management()
            
            # Logout button at the bottom
            st.markdown("---")
            show_logout_button()
