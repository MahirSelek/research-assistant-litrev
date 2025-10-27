# app/frontend/html_ui.py
"""
HTML/CSS/JS Frontend - Clean separation from backend logic
This handles all UI components using HTML/CSS/JavaScript instead of Streamlit components
"""

import streamlit as st
import time
import os
from typing import Dict, List, Any, Optional
import datetime
import json
import base64

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import ResearchAssistantAPI
from auth import show_login_page, show_logout_button
from utils.static_assets import StaticAssetsManager

class HTMLResearchAssistantUI:
    def __init__(self, api: ResearchAssistantAPI):
        """Initialize HTML-based UI with backend API"""
        self.api = api
        
        # Initialize static assets manager
        self.assets_manager = StaticAssetsManager()
        
        # Clean user and assistant avatars (bigger sizes)
        # User avatar: Simple person icon (bigger)
        self.USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIiBmaWxsPSJub25lIj48cGF0aCBkPSJNMjAgMjBjLTUuNSAwLTEwIDQuNS0xMCAxMHY1aDIwdi01YzAtNS41LTQuNS0xMC0xMC0xMHoiIGZpbGw9IiM2NjdlZWEiLz48Y2lyY2xlIGN4PSIyMCIgY3k9IjEyIiByPSI3IiBmaWxsPSIjNjY3ZWVhIi8+PC9zdmc+"
        
        # Assistant avatar: Simple DNA double-helix in Polo-GGB color (no circle)
        assistant_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40" fill="none">'
            '<g stroke="#667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M12 8c8 0 8 24 16 24"/>'
            '<path d="M28 8c-8 0-8 24-16 24"/>'
            '<line x1="14" y1="13" x2="26" y2="13"/>'
            '<line x1="14" y1="20" x2="26" y2="20"/>'
            '<line x1="14" y1="27" x2="26" y2="27"/>'
            '</g>'
            '</svg>'
        )
        self.ASSISTANT_AVATAR = "data:image/svg+xml;base64," + base64.b64encode(assistant_svg.encode("utf-8")).decode("utf-8")
        
        # UI Constants
        self.GENETICS_KEYWORDS = [
            "Polygenic risk score", "Complex disease", "Multifactorial disease", "PRS", "Risk", "Risk prediction", "Genetic risk prediction", "GWAS", "Genome-wide association study", "GWAS summary statistics", "Relative risk", "Absolute risk", "clinical polygenic risk score", "disease prevention", "disease management", "personalized medicine", "precision medicine", "UK biobank", "biobank", "All of US biobank", "PRS pipeline", "PRS workflow", "PRS tool", "PRS conversion", "Binary trait", "Continuous trait", "Meta-analysis", "Genome-wide association", "Genetic susceptibility", "PRSs Clinical utility", "Genomic risk prediction", "clinical implementation", "PGS", "SNP hereditability", "Risk estimation", "Machine learning in genetic prediction", "PRSs clinical application", "Risk stratification", "Multiancestry PRS", "Integrative PRS model", "Longitudinal PRS analysis", "Genetic screening", "Ethical implication of PRS", "human genetics", "human genome variation", "genetics of common multifactorial diseases", "genetics of common traits", "pharmacogenetics", "pharmacogenomics"
        ]
    
    def initialize_session_state(self):
        """Initialize user session state"""
        current_user = st.session_state.get('username', 'default')
        
        # Check if this is a new login (user data not loaded yet)
        user_data_loaded_key = f"user_data_loaded_{current_user}"
        
        if current_user != 'default' and not st.session_state.get(user_data_loaded_key, False):
            # Load user data from backend
            try:
                print(f"Loading user data for: {current_user}")
                user_data = self.api.get_user_data(current_user)
                if user_data:
                    print(f"Loaded user data: {list(user_data.keys())}")
                    # Set persistent user data from backend (conversations only)
                    self.set_user_session('conversations', user_data.get('conversations', {}))
                    
                    # Clear session-specific data on each login (like in old implementation)
                    # This includes clearing active_conversation_id to show new analysis page
                    self.set_user_session('active_conversation_id', None)
                    self.set_user_session('selected_keywords', [])
                    self.set_user_session('search_mode', 'all_keywords')
                    self.set_user_session('uploaded_papers', [])
                    self.set_user_session('custom_summary_chat', [])
                    
                    # Mark user data as loaded
                    st.session_state[user_data_loaded_key] = True
                    print(f"Successfully loaded data for {current_user}")
                else:
                    # Initialize empty user data if none exists
                    print(f"No data found for {current_user}, initializing empty data")
                    self._initialize_empty_user_data()
                    st.session_state[user_data_loaded_key] = True
            except Exception as e:
                print(f"Failed to load user data for {current_user}: {e}")
                self._initialize_empty_user_data()
                st.session_state[user_data_loaded_key] = True
        
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
        if self.get_user_key('analysis_locked') not in st.session_state:
            self.set_user_session('analysis_locked', False)
    
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
        if key in ['conversations', 'selected_keywords', 'search_mode', 'uploaded_papers', 'custom_summary_chat', 'active_conversation_id', 'time_filter']:
            username = st.session_state.get('username')
            if username and username != 'default':
                try:
                    # Simple rate limiting to avoid GCS 429 errors
                    rate_key = f"last_backend_sync_{username}"
                    now_ts = time.time()
                    last_sync = st.session_state.get(rate_key, 0)
                    # Always allow immediate syncs for conversations; throttle others to once per 5s
                    must_sync = key == 'conversations' or (now_ts - last_sync) >= 5.0
                    if must_sync:
                        user_data = {
                            'selected_keywords': self.get_user_session('selected_keywords', []),
                            'search_mode': self.get_user_session('search_mode', 'all_keywords'),
                            'uploaded_papers': self.get_user_session('uploaded_papers', []),
                            'custom_summary_chat': self.get_user_session('custom_summary_chat', []),
                            'active_conversation_id': self.get_user_session('active_conversation_id')
                        }
                        self.api.save_user_data(username, user_data)
                        st.session_state[rate_key] = now_ts
                except Exception as e:
                    print(f"Failed to sync to backend: {e}")
    
    def inject_css_and_js(self):
        """Inject CSS and JavaScript using external files"""
        # Load core assets (main.css and main.js)
        success = self.assets_manager.load_core_assets()
        
        if not success:
            st.warning("Some static assets could not be loaded. Using fallback styling.")
            # Fallback minimal styling if assets fail to load
            st.markdown("""
            <style>
            .stApp { background: #0e1117 !important; }
            .stSidebar { background: #1e1e1e !important; }
            </style>
            """, unsafe_allow_html=True)
    
    def render_main_interface(self):
        """Render the main interface using Streamlit components"""
        
        # Show full-screen loading overlay if loading (do NOT return; allow processing to continue)
        if st.session_state.get('is_loading', False):
            loading_message = st.session_state.get('loading_message', 'Processing...')
            loading_subtext = st.session_state.get('loading_subtext', 'Please wait while we work on your request')
            loading_progress = st.session_state.get('loading_progress', '')
            
            st.markdown(f"""
            <div class="loading-overlay show">
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">{loading_message}</div>
                    <div class="loading-subtext">{loading_subtext}</div>
                    {f'<div class="loading-progress">{loading_progress}</div>' if loading_progress else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            # IMPORTANT: don't return; keep running so background task can execute during this run
        
        # Main content area
        st.markdown("# 🧬 POLO-GGB RESEARCH ASSISTANT")
        
        # Get current state
        active_conversation_id = self.get_user_session('active_conversation_id')
        conversations = self.get_user_session('conversations', {})

        # If a keyword search was scheduled on previous click, run it now while overlay is visible
        if st.session_state.get('do_keyword_search'):
            try:
                pending_keywords = st.session_state.get('pending_keywords', [])
                pending_time = st.session_state.get('pending_time_filter', 'Current year')
                pending_mode = st.session_state.get('pending_search_mode', 'all_keywords')

                success = self.process_keyword_search(pending_keywords, pending_time, pending_mode)

                # Clear loading and flags
                st.session_state['is_loading'] = False
                st.session_state['do_keyword_search'] = False
                st.session_state.pop('pending_keywords', None)
                st.session_state.pop('pending_time_filter', None)
                st.session_state.pop('pending_search_mode', None)

                if success:
                    st.rerun()
                else:
                    self.set_user_session('analysis_locked', False)
                    st.error("Analysis failed. Please try again.")
                    st.rerun()
            except Exception as e:
                st.session_state['is_loading'] = False
                st.session_state['do_keyword_search'] = False
                self.set_user_session('analysis_locked', False)
                st.error(f"An error occurred: {e}")
                st.rerun()
        
        # If a custom summary was scheduled on previous click, run it now while overlay is visible
        if st.session_state.get('do_custom_summary'):
            try:
                uploaded_papers = self.get_user_session('uploaded_papers', [])
                
                success = self.generate_custom_summary(uploaded_papers)
                
                # Clear loading and flags
                st.session_state['is_loading'] = False
                st.session_state['do_custom_summary'] = False
                
                if success:
                    # Clear uploaded papers IMMEDIATELY after successful generation (before rerun)
                    self.set_user_session('uploaded_papers', [])
                    # Also clear from session state directly to ensure it's gone
                    user_key = self.get_user_key('uploaded_papers')
                    if user_key in st.session_state:
                        st.session_state[user_key] = []
                    st.rerun()
                else:
                    self.set_user_session('analysis_locked', False)
                    st.error("Custom summary generation failed. Please try again.")
                    st.rerun()
            except Exception as e:
                st.session_state['is_loading'] = False
                st.session_state['do_custom_summary'] = False
                self.set_user_session('analysis_locked', False)
                st.error(f"An error occurred: {e}")
                st.rerun()
        
        # Show default message if no active conversation
        if active_conversation_id is None:
            st.info("Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.")
        elif active_conversation_id is not None and active_conversation_id in conversations:
            active_conv = conversations[active_conversation_id]
            
            # Display all messages in the conversation
            for message_index, message in enumerate(active_conv.get("messages", [])):
                # Use custom avatars based on message role
                avatar = self.ASSISTANT_AVATAR if message["role"] == "assistant" else self.USER_AVATAR
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
                        
                        # For follow-up responses, use all retrieved papers to make citations clickable but don't include references section
                        response_text = self.api._display_citations_separately(response_text, retrieved_papers, retrieved_papers, search_mode, include_references=False)
                        active_conv["messages"].append({"role": "assistant", "content": response_text})
                        active_conv['last_interaction_time'] = time.time()
                        self.set_user_session('conversations', conversations)
                        
                        # Save conversation to backend
                        username = st.session_state.get('username')
                        if username:
                            self.api.save_conversation(username, active_conversation_id, active_conv)
                        
                        st.rerun()
    
    def render_sidebar(self):
        """Sidebar is now part of the main HTML interface"""
        pass
    
    def improve_conversation_title(self, conv_data: Dict, conv_id: str) -> str:
        """Improve existing conversation titles that are too generic"""
        current_title = conv_data.get("title", "Untitled")
        
        # Check if title needs improvement
        if (current_title in ["Research Analysis", "Analysis", "Research", "Chat..."] or 
            len(current_title.split()) < 3 or 
            "Genetics via" in current_title or 
            ("Medical" in current_title and len(current_title.split()) < 4)):
            
            # Try to extract better title from conversation content
            messages = conv_data.get("messages", [])
            if messages:
                # Get the first assistant message (analysis content)
                for msg in messages:
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "")
                        
                        # Extract keywords from conversation
                        keywords = conv_data.get("keywords", [])
                        if keywords:
                            keyword_str = ", ".join(keywords[:3])
                            
                            # Look for disease mentions in content
                            content_lower = content.lower()
                            diseases = []
                            if 'lung cancer' in content_lower or 'nsclc' in content_lower:
                                diseases.append('Lung Cancer')
                            elif 'breast cancer' in content_lower:
                                diseases.append('Breast Cancer')
                            elif 'coronary' in content_lower or 'cad' in content_lower:
                                diseases.append('CAD')
                            elif 'diabetes' in content_lower:
                                diseases.append('Diabetes')
                            elif 'alzheimer' in content_lower:
                                diseases.append('Alzheimer\'s')
                            
                            if diseases:
                                return f"{keyword_str}: {diseases[0]} Analysis"
                            else:
                                return f"{keyword_str} Analysis"
            
            # Fallback: use conversation ID timestamp for uniqueness
            try:
                if conv_id.startswith('custom_summary_'):
                    # Try to extract more info from custom summary
                    retrieved_papers = conv_data.get("retrieved_papers", [])
                    if retrieved_papers:
                        # Use the enhanced title generation for custom summaries
                        summary_text = ""
                        for msg in messages:
                            if msg.get("role") == "assistant":
                                summary_text = msg.get("content", "")
                                break
                        
                        if summary_text:
                            # Use the same logic as generate_custom_summary_title
                            summary_lower = summary_text.lower()
                            
                            # Quick disease detection
                            if 'lung cancer' in summary_lower or 'nsclc' in summary_lower:
                                return f"Custom Summary: Lung Cancer Analysis"
                            elif 'breast cancer' in summary_lower:
                                return f"Custom Summary: Breast Cancer Analysis"
                            elif 'coronary' in summary_lower or 'cad' in summary_lower:
                                return f"Custom Summary: CAD Analysis"
                            elif 'diabetes' in summary_lower:
                                return f"Custom Summary: Diabetes Analysis"
                            elif 'alzheimer' in summary_lower:
                                return f"Custom Summary: Alzheimer's Analysis"
                            elif 'kras' in summary_lower:
                                return f"Custom Summary: KRAS Analysis"
                            elif 'prs' in summary_lower or 'polygenic' in summary_lower:
                                return f"Custom Summary: PRS Analysis"
                            elif 'biomarker' in summary_lower:
                                return f"Custom Summary: Biomarker Analysis"
                    
                    return f"Custom Summary Analysis"
                elif conv_id.startswith('conv_'):
                    return f"Research Analysis"
            except:
                pass
        
        return current_title  # Return original if no improvement needed

    def process_keyword_search(self, keywords: List[str], time_filter_type: str, search_mode: str = "all_keywords"):
        """Process keyword search via backend"""
        try:
            print(f"Processing keyword search with {len(keywords)} keywords: {keywords}")
            analysis_result, retrieved_papers, total_found = self.api.search_papers(keywords, time_filter_type, search_mode)
            print(f"API returned: analysis_result={bool(analysis_result)}, papers={len(retrieved_papers)}, total_found={total_found}")
            
            if analysis_result:
                conv_id = f"conv_{time.time()}"
                search_mode_display = search_mode
                selected_keywords = keywords  # Use the actual keywords passed to the function
                search_mode_text = "ALL keywords" if search_mode_display == "all_keywords" else "AT LEAST ONE keyword"
                
                initial_message = {"role": "assistant", "content": f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    <h2 style="color: white; margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">Analysis Report</h2>
    <div style="color: #f0f0f0; font-size: 16px; margin-bottom: 8px;">
        <strong>Keywords:</strong> {', '.join(selected_keywords) if selected_keywords else 'None selected'}
    </div>
    <div style="color: #e0e0e0; font-size: 14px;">
        <strong>Search Mode:</strong> {search_mode_text}
    </div>
    <div style="color: #f0f0f0; font-size: 16px;">
        <strong>Time Window:</strong> {time_filter_type}
    </div>
</div>

{analysis_result}
"""}
                
                # Generate better title using keywords and analysis content
                title = self.api.generate_conversation_title(analysis_result)
                
                # If AI title is too generic, create a better one from keywords
                if title in ["Research Analysis", "Analysis", "Research"] or len(title.split()) < 3:
                    # Create title from keywords and paper topics
                    keyword_str = ", ".join(selected_keywords[:3])  # First 3 keywords
                    
                    # Extract disease/topic from retrieved papers
                    if retrieved_papers:
                        paper_titles = [paper.get('metadata', {}).get('title', '') for paper in retrieved_papers[:3]]
                        # Look for common disease terms
                        diseases = []
                        for title_text in paper_titles:
                            title_lower = title_text.lower()
                            if 'lung cancer' in title_lower or 'nsclc' in title_lower:
                                diseases.append('Lung Cancer')
                            elif 'breast cancer' in title_lower:
                                diseases.append('Breast Cancer')
                            elif 'coronary' in title_lower or 'cad' in title_lower:
                                diseases.append('CAD')
                            elif 'diabetes' in title_lower:
                                diseases.append('Diabetes')
                            elif 'alzheimer' in title_lower:
                                diseases.append('Alzheimer\'s')
                        
                        if diseases:
                            # Use most common disease
                            from collections import Counter
                            disease_counts = Counter(diseases)
                            main_disease = disease_counts.most_common(1)[0][0]
                            title = f"{keyword_str}: {main_disease} Analysis"
                        else:
                            title = f"{keyword_str} Analysis"
                    else:
                        title = f"{keyword_str} Analysis"
                
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
                print(f"Created conversation {conv_id} with message: {initial_message['content'][:100]}...")
                
                # Save conversation to backend
                username = st.session_state.get('username')
                if username:
                    self.api.save_conversation(username, conv_id, conversations[conv_id])
                
                self.set_user_session('active_conversation_id', conv_id)
                self.set_user_session('custom_summary_chat', [])
                print(f"Successfully created conversation: {conv_id}")
                return True
            else:
                search_mode_text = "ALL of the selected keywords" if search_mode == "all_keywords" else "AT LEAST ONE of the selected keywords"
                st.error(f"No papers found that contain {search_mode_text} within the specified time window. Please try a different combination of keywords.")
                return False
        except Exception as e:
            print(f"Error in process_keyword_search: {e}")
            st.error(f"An error occurred while processing the search: {str(e)}")
            return False
    
    def handle_form_submissions(self):
        """Handle form submissions using Streamlit components"""
        # Use regular Streamlit components instead of complex form handling
        
        # Create a sidebar for controls
        with st.sidebar:
            # Get analysis lock status
            analysis_locked = self.get_user_session('analysis_locked', False)
            
            # Show analysis status
            if analysis_locked:
                st.info("🔒 Analysis Active - Controls Locked")
            else:
                st.success("🔓 Ready for New Analysis")
            
            st.markdown("---")
            
            # Get is_loading status to disable buttons during any operation
            is_loading = st.session_state.get('is_loading', False)
            is_any_blocked = analysis_locked or is_loading
            
            # New Analysis button
            if st.button("➕ New Analysis", type="primary", use_container_width=True, disabled=is_any_blocked):
                # Clear ALL session state for fresh start
                self.set_user_session('active_conversation_id', None)
                self.set_user_session('selected_keywords', [])
                self.set_user_session('search_mode', "all_keywords")
                self.set_user_session('time_filter', "Current year")
                self.set_user_session('custom_summary_chat', [])
                self.set_user_session('analysis_locked', False)  # Unlock for new analysis
                
                # Force clear the multiselect by updating session state
                if 'html_keywords' in st.session_state:
                    st.session_state['html_keywords'] = []
                if 'html_search_mode' in st.session_state:
                    st.session_state['html_search_mode'] = "all_keywords"
                if 'html_time_filter' in st.session_state:
                    st.session_state['html_time_filter'] = "Current year"
                
                st.rerun()
            
            # Keyword selection
            # Initialize keywords in session state if not exists
            if 'html_keywords' not in st.session_state:
                st.session_state['html_keywords'] = self.get_user_session('selected_keywords', [])
            
            selected_keywords = st.multiselect(
                "Select Keywords",
                self.GENETICS_KEYWORDS,
                key="html_keywords",
                help="Select keywords for your research analysis" if not is_any_blocked else "Keywords are locked for current analysis.",
                disabled=is_any_blocked
            )
            
            # Update session state with selected keywords
            self.set_user_session('selected_keywords', selected_keywords)
            
            # Search mode
            # Initialize search mode in session state if not exists
            if 'html_search_mode' not in st.session_state:
                st.session_state['html_search_mode'] = self.get_user_session('search_mode', 'all_keywords')
            
            search_mode = st.selectbox(
                "Search Mode",
                ["all_keywords", "any_keyword"],
                format_func=lambda x: "Find papers containing ALL keywords" if x == "all_keywords" else "Find papers containing AT LEAST ONE keyword",
                key="html_search_mode",
                disabled=is_any_blocked
            )
            
            # Update session state with search mode
            self.set_user_session('search_mode', search_mode)
            
            # Time filter
            # Initialize time filter in session state if not exists
            if 'html_time_filter' not in st.session_state:
                st.session_state['html_time_filter'] = self.get_user_session('time_filter', 'Current year')
            
            time_filter = st.selectbox(
                "Filter by Time Window",
                ["Current year", "Last 3 months", "Last 6 months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
                key="html_time_filter",
                disabled=is_any_blocked
            )
            
            # Update session state with time filter
            self.set_user_session('time_filter', time_filter)
            
            # Search button
            if st.button("Search & Analyze", type="primary", use_container_width=True, disabled=is_any_blocked):
                if selected_keywords:
                    # Set loading state and lock immediately, then schedule analysis and rerun
                    st.session_state['is_loading'] = True
                    st.session_state['loading_message'] = "Analyzing Research Papers"
                    st.session_state['loading_subtext'] = "Searching for highly relevant papers and generating comprehensive report..."
                    st.session_state['loading_progress'] = "This may take a few moments..."
                    self.set_user_session('analysis_locked', True)

                    # Stash pending action parameters to run on next script run
                    st.session_state['do_keyword_search'] = True
                    st.session_state['pending_keywords'] = list(selected_keywords)
                    st.session_state['pending_time_filter'] = time_filter
                    st.session_state['pending_search_mode'] = search_mode

                    st.rerun()
                else:
                    st.error("Please select at least one keyword.")
            
            # Chat history
            st.markdown("### Chat History")
            conversations = self.get_user_session('conversations', {})
            if conversations:
                # Sort conversations by creation time (most recent first) - like ChatGPT
                def get_creation_time(conv_id, conv_data):
                    # Use last_interaction_time if available, otherwise fall back to creation time
                    if 'last_interaction_time' in conv_data:
                        return conv_data['last_interaction_time']
                    
                    # Extract timestamp from conversation ID
                    try:
                        if conv_id.startswith('custom_summary_'):
                            timestamp_str = conv_id.split('_', 2)[2]
                        else:
                            timestamp_str = conv_id.split('_')[1]
                        return float(timestamp_str)
                    except (IndexError, ValueError):
                        return 0
                
                sorted_conversations = sorted(
                    conversations.items(), 
                    key=lambda x: get_creation_time(x[0], x[1]), 
                    reverse=True
                )
                
                for conv_id, conv_data in sorted_conversations:
                    # Get and potentially improve the title
                    title = conv_data.get("title", "Chat...")
                    
                    # Check if title needs improvement (too generic)
                    if (title in ["Research Analysis", "Analysis", "Research", "Chat..."] or 
                        len(title.split()) < 3 or 
                        "Genetics via" in title or 
                        ("Medical" in title and len(title.split()) < 4)):
                        
                        # Try to improve the title
                        improved_title = self.improve_conversation_title(conv_data, conv_id)
                        if improved_title != title:
                            # Update the conversation with improved title
                            conversations = self.get_user_session('conversations', {})
                            if conv_id in conversations:
                                conversations[conv_id]['title'] = improved_title
                                self.set_user_session('conversations', conversations)
                                
                                # Save to backend
                                username = st.session_state.get('username')
                                if username:
                                    self.api.save_conversation(username, conv_id, conversations[conv_id])
                                
                                title = improved_title
                    
                    # Extract and format the date from conversation ID
                    try:
                        if conv_id.startswith('custom_summary_'):
                            timestamp_str = conv_id.split('_', 2)[2]
                        else:
                            timestamp_str = conv_id.split('_')[1]
                        timestamp = float(timestamp_str)
                        date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%b %d, %Y")
                    except (IndexError, ValueError):
                        date_str = "Unknown date"
                    
                    # Create columns for chat title and delete button
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        # Display title and date in a more compact format
                        display_text = f"{title}\n{date_str}"
                        if st.button(display_text, key=f"chat_{conv_id}", use_container_width=True, disabled=is_any_blocked):
                            self.set_user_session('active_conversation_id', conv_id)
                            self.set_user_session('analysis_locked', True)  # Lock when viewing past analysis
                            st.rerun()
                    
                    with col2:
                        if st.button("×", key=f"delete_{conv_id}", help="Delete this analysis", type="secondary", disabled=is_any_blocked):
                            # Delete conversation from session
                            del conversations[conv_id]
                            self.set_user_session('conversations', conversations)
                            
                            # Delete from GCS
                            username = st.session_state.get('username')
                            if username:
                                try:
                                    self.api.delete_conversation(username, conv_id)
                                    st.success("Analysis deleted!")
                                except Exception as e:
                                    st.error(f"Failed to delete from storage: {e}")
                            
                            # Clear active conversation if it was deleted
                            if self.get_user_session('active_conversation_id') == conv_id:
                                self.set_user_session('active_conversation_id', None)
                            
                            st.rerun()
            else:
                st.caption("No past analyses found.")
            
            # Uploaded papers section
            st.markdown("### Uploaded Papers")
            uploaded_papers = self.get_user_session('uploaded_papers', [])
            
            if uploaded_papers:
                st.info(f"{len(uploaded_papers)} papers uploaded")
                with st.expander("View uploaded papers"):
                    for i, paper in enumerate(uploaded_papers):
                        title = paper['metadata'].get('title', 'Unknown title')
                        st.write(f"{i+1}. {title}")
                
                # Get analysis lock status for button disable state
                analysis_locked = self.get_user_session('analysis_locked', False)
                is_loading = st.session_state.get('is_loading', False)
                is_blocked = analysis_locked or is_loading
                
                # Custom summary button
                if st.button("Generate Custom Summary", type="primary", use_container_width=True, disabled=is_blocked):
                    # Set loading state and lock immediately, then schedule custom summary generation
                    st.session_state['is_loading'] = True
                    st.session_state['loading_message'] = "Generating Custom Summary"
                    st.session_state['loading_subtext'] = "Analyzing your uploaded papers and creating comprehensive summary..."
                    st.session_state['loading_progress'] = "Processing PDF content and generating AI summary..."
                    self.set_user_session('analysis_locked', True)
                    
                    # Stash pending action parameter to run on next script run
                    st.session_state['do_custom_summary'] = True
                    
                    st.rerun()
                
                # Clear uploaded papers button
                if st.button("Clear uploaded papers", type="secondary", use_container_width=True, disabled=is_blocked):
                    self.set_user_session('uploaded_papers', [])
                    st.rerun()
            else:
                st.caption("No papers uploaded yet")
            
            # PDF upload section
            with st.expander("Upload PDF Files"):
                st.info("Upload PDF files to generate custom summary of your documents.")
                
                # Check if blocked for file uploader (need to get the status from parent scope)
                is_blocked_upload = st.session_state.get('is_loading', False) or self.get_user_session('analysis_locked', False)
                
                uploaded_pdfs = st.file_uploader(
                    "Choose PDF files", 
                    accept_multiple_files=True, 
                    type=['pdf'], 
                    key="pdf_uploader_html",
                    disabled=is_blocked_upload
                )
                
                if uploaded_pdfs and st.button("Add PDFs", type="primary", disabled=is_blocked_upload):
                    # Show full-screen loading overlay for PDF processing
                    st.markdown("""
                    <script>
                    showLoadingOverlay("📄 Processing PDF Files", "Extracting text and metadata from uploaded papers...", "Reading PDF content and generating summaries...");
                    </script>
                    """, unsafe_allow_html=True)
                    
                    for uploaded_file in uploaded_pdfs:
                        # Process PDF using backend API
                        paper_data = self.api.process_uploaded_pdf(uploaded_file, uploaded_file.name)
                        
                        if paper_data:
                            # Store in user-specific session state
                            uploaded_papers = self.get_user_session('uploaded_papers', [])
                            uploaded_papers.append(paper_data)
                            self.set_user_session('uploaded_papers', uploaded_papers)
                            st.success(f"Successfully processed '{uploaded_file.name}' (Content length: {len(paper_data['content'])} chars)")
                        else:
                            st.error(f"Could not read content from '{uploaded_file.name}'. The PDF might be corrupted or password-protected.")
                    
                    # Hide loading overlay
                    st.markdown("""
                    <script>
                    hideLoadingOverlay();
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.rerun()
            
            # Logout
            if st.button("Logout", type="secondary", use_container_width=True):
                # Clear session state
                for key in list(st.session_state.keys()):
                    if not key.startswith('_'):
                        del st.session_state[key]
                st.rerun()
        
        # Handle chat input
        active_conversation_id = self.get_user_session('active_conversation_id')
        if active_conversation_id:
            if prompt := st.chat_input("Ask a follow-up question..."):
                # Fast path: just append user message and rerun; the "Handle follow-up responses"
                # section above will generate the assistant reply with a lightweight spinner.
                conversations = self.get_user_session('conversations', {})
                if active_conversation_id in conversations:
                    active_conv = conversations[active_conversation_id]
                    active_conv["messages"].append({"role": "user", "content": prompt})
                    active_conv['last_interaction_time'] = time.time()
                    self.set_user_session('conversations', conversations)

                    # Save conversation to backend (no overlay)
                    username = st.session_state.get('username')
                    if username:
                        self.api.save_conversation(username, active_conversation_id, active_conv)

                    st.rerun()
    
    def generate_custom_summary(self, uploaded_papers: List[Dict]):
        """Generate custom summary via backend"""
        try:
            print(f"Generating custom summary for {len(uploaded_papers)} papers")
            summary = self.api.generate_custom_summary(uploaded_papers)
            
            if summary:
                conv_id = f"custom_summary_{time.time()}"
                
                def generate_custom_summary_title(papers, summary_text):
                    """Generate detailed custom summary title with specific information"""
                    paper_count = len(papers)
                    summary_lower = summary_text.lower()
                    
                    # Extract detailed information from papers and summary
                    diseases = []
                    methodologies = []
                    specific_topics = []
                    drug_names = []
                    gene_names = []
                    
                    # Enhanced disease detection
                    if any(word in summary_lower for word in ['lung cancer', 'nsclc', 'non-small cell lung cancer']):
                        diseases.append('Lung Cancer')
                    elif any(word in summary_lower for word in ['breast cancer', 'mammary carcinoma']):
                        diseases.append('Breast Cancer')
                    elif any(word in summary_lower for word in ['prostate cancer', 'prostate carcinoma']):
                        diseases.append('Prostate Cancer')
                    elif any(word in summary_lower for word in ['colorectal cancer', 'colon cancer', 'rectal cancer']):
                        diseases.append('Colorectal Cancer')
                    elif any(word in summary_lower for word in ['coronary artery disease', 'cad', 'heart disease', 'myocardial infarction']):
                        diseases.append('Coronary Artery Disease')
                    elif any(word in summary_lower for word in ['diabetes', 'diabetic', 'type 2 diabetes', 't2d']):
                        diseases.append('Diabetes')
                    elif any(word in summary_lower for word in ['alzheimer', 'dementia', 'alzheimer\'s disease']):
                        diseases.append('Alzheimer\'s Disease')
                    elif any(word in summary_lower for word in ['cancer', 'oncology', 'tumor', 'carcinoma']):
                        diseases.append('Cancer')
                    elif any(word in summary_lower for word in ['cardiovascular', 'heart', 'cardiac', 'cvd']):
                        diseases.append('Cardiovascular Disease')
                    elif any(word in summary_lower for word in ['obesity', 'obese']):
                        diseases.append('Obesity')
                    
                    # Enhanced methodology and topic detection
                    if any(word in summary_lower for word in ['kras', 'krasg12c', 'sotorasib']):
                        specific_topics.append('KRAS Inhibition')
                        drug_names.append('Sotorasib')
                    elif any(word in summary_lower for word in ['polygenic risk score', 'prs', 'polygenic score']):
                        specific_topics.append('Polygenic Risk Scoring')
                    elif any(word in summary_lower for word in ['gwas', 'genome-wide association study']):
                        specific_topics.append('GWAS Analysis')
                    elif any(word in summary_lower for word in ['machine learning', 'ai', 'artificial intelligence', 'ml', 'deep learning']):
                        methodologies.append('AI/ML')
                    elif any(word in summary_lower for word in ['ctdna', 'circulating tumor dna', 'liquid biopsy']):
                        specific_topics.append('ctDNA Analysis')
                    elif any(word in summary_lower for word in ['biomarker', 'biomarkers', 'biomarker discovery']):
                        specific_topics.append('Biomarker Discovery')
                    elif any(word in summary_lower for word in ['transcriptomic', 'transcriptome', 'rna-seq']):
                        specific_topics.append('Transcriptomics')
                    elif any(word in summary_lower for word in ['genomic', 'genome', 'genomics']):
                        specific_topics.append('Genomics')
                    elif any(word in summary_lower for word in ['pharmacogenomics', 'drug response', 'pharmacogenetics']):
                        specific_topics.append('Pharmacogenomics')
                    elif any(word in summary_lower for word in ['clinical trial', 'clinical study']):
                        methodologies.append('Clinical Trial')
                    elif any(word in summary_lower for word in ['therapeutic', 'therapy', 'treatment']):
                        methodologies.append('Therapeutic')
                    
                    # Extract gene names
                    import re
                    gene_patterns = [r'\b[A-Z]{2,}\d*\b', r'\b[A-Z]{1,2}[a-z]+\d*\b']
                    for pattern in gene_patterns:
                        genes = re.findall(pattern, summary_text)
                        gene_names.extend([g for g in genes if len(g) > 2 and g not in ['DNA', 'RNA', 'PCR', 'GWAS', 'PRS']])
                    
                    # Create detailed title
                    title_parts = []
                    
                    # Priority 1: Specific topic + Disease + Drug/Gene
                    if specific_topics and diseases:
                        base_title = f"{specific_topics[0]}: {diseases[0]}"
                        if drug_names:
                            base_title += f" ({drug_names[0]})"
                        elif gene_names[:2]:  # Take first 2 genes
                            base_title += f" ({', '.join(gene_names[:2])})"
                        title = base_title
                    # Priority 2: Disease + Methodology
                    elif diseases and methodologies:
                        title = f"{diseases[0]}: {methodologies[0]} Analysis"
                    # Priority 3: Specific topic only
                    elif specific_topics:
                        title = specific_topics[0]
                    # Priority 4: Disease only
                    elif diseases:
                        title = diseases[0]
                    # Priority 5: Methodology only
                    elif methodologies:
                        title = f"{methodologies[0]} Analysis"
                    # Fallback: Extract from paper titles
                    else:
                        paper_titles = [paper.get('metadata', {}).get('title', '') for paper in papers]
                        if paper_titles and paper_titles[0]:
                            # Extract meaningful words from paper title
                            words = paper_titles[0].split()
                            meaningful_words = [w for w in words[:5] if len(w) > 3 and w.lower() not in 
                                             ['the', 'and', 'for', 'with', 'this', 'that', 'analysis', 'study', 'research', 'investigation']]
                            title = ' '.join(meaningful_words[:4]) if meaningful_words else "Research Analysis"
                        else:
                            title = "Research Analysis"
                    
                    # Add paper count
                    return f"{title} ({paper_count} papers)"
                
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
                print(f"Created custom summary conversation {conv_id} with message: {initial_message['content'][:100]}...")
                
                # Save conversation to backend
                username = st.session_state.get('username')
                if username:
                    self.api.save_conversation(username, conv_id, conversations[conv_id])
                
                self.set_user_session('active_conversation_id', conv_id)
                print(f"Successfully generated custom summary: {conv_id}")
                return True
            else:
                st.error("Failed to generate summary. Please try again.")
                return False
        except Exception as e:
            print(f"Error in generate_custom_summary: {e}")
            st.error(f"An error occurred while generating the summary: {str(e)}")
            return False
    
    def local_css(self, file_name):
        """Load local CSS file"""
        try:
            with open(file_name) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning(f"CSS file '{file_name}' not found. Using default styles.")
