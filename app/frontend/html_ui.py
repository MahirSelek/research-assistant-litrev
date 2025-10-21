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

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import ResearchAssistantAPI
from auth import show_login_page, show_logout_button

class HTMLResearchAssistantUI:
    def __init__(self, api: ResearchAssistantAPI):
        """Initialize HTML-based UI with backend API"""
        self.api = api
        
        # Clean user and assistant avatars (bigger sizes)
        # User avatar: Simple person icon (bigger)
        self.USER_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIiBmaWxsPSJub25lIj48cGF0aCBkPSJNMjAgMjBjLTUuNSAwLTEwIDQuNS0xMCAxMHY1aDIwdi01YzAtNS41LTQuNS0xMC0xMC0xMHoiIGZpbGw9IiM2NjdlZWEiLz48Y2lyY2xlIGN4PSIyMCIgY3k9IjEyIiByPSI3IiBmaWxsPSIjNjY3ZWVhIi8+PC9zdmc+"
        
        # Assistant avatar: Very basic robot/assistant icon
        self.ASSISTANT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIiBmaWxsPSJub25lIj48cmVjdCB4PSI4IiB5PSIxMCIgd2lkdGg9IjI0IiBoZWlnaHQ9IjIwIiBmaWxsPSIjMTA5OTgxIiByeD0iNCIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTgiIHI9IjIiIGZpbGw9IndoaXRlIi8+PGNpcmNsZSBjeD0iMjQiIGN5PSIxOCIgcj0iMiIgZmlsbD0id2hpdGUiLz48cmVjdCB4PSIxNiIgeT0iMjQiIHdpZHRoPSI4IiBoZWlnaHQ9IjMiIGZpbGw9IndoaXRlIiByeD0iMSIvPjwvc3ZnPg=="
        
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
        if 'is_loading' not in st.session_state:
            st.session_state.is_loading = False
        if 'loading_message' not in st.session_state:
            st.session_state.loading_message = ""
        if 'loading_subtext' not in st.session_state:
            st.session_state.loading_subtext = ""
        if 'loading_progress' not in st.session_state:
            st.session_state.loading_progress = ""
    
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
    
    def inject_css_and_js(self):
        """Inject minimal CSS for styling"""
        st.markdown("""
        <style>
        /* Custom styling for better appearance */
        .stApp {
            background: #0e1117 !important;
        }
        
        .stSidebar {
            background: #1e1e1e !important;
        }
        
        /* Primary buttons - Modern blue gradient with enhanced styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 14px 28px !important;
            font-size: 15px !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 14px rgba(102, 126, 234, 0.25) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .stButton > button::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
            transition: left 0.5s !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
        }
        
        .stButton > button:hover::before {
            left: 100% !important;
        }
        
        .stButton > button:active {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 14px rgba(102, 126, 234, 0.25) !important;
        }
        
        /* Secondary buttons - Subtle gray */
        [data-testid="stSecondaryButton"] > button {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #e2e8f0 !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 6px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease !important;
        }
        
        [data-testid="stSecondaryButton"] > button:hover {
            background: rgba(255, 255, 255, 0.15) !important;
            color: #f1f5f9 !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Delete buttons in chat history - Red accent */
        div[data-testid="stButton"]:has(button:contains("×")) button {
            background: rgba(239, 68, 68, 0.1) !important;
            color: #f87171 !important;
            border: 1px solid rgba(239, 68, 68, 0.3) !important;
            border-radius: 6px !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            min-height: 28px !important;
            padding: 4px 8px !important;
            transition: all 0.2s ease !important;
        }
        
        div[data-testid="stButton"]:has(button:contains("×")) button:hover {
            background: rgba(239, 68, 68, 0.2) !important;
            color: #ef4444 !important;
            border-color: rgba(239, 68, 68, 0.5) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Special button types with enhanced styling */
        button:contains("New Analysis") {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
        }
        
        button:contains("New Analysis"):hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
        }
        
        button:contains("Logout") {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3) !important;
        }
        
        button:contains("Logout"):hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
            box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4) !important;
        }
        
        /* Search & Analyze button - Special styling */
        button:contains("Search & Analyze") {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3) !important;
        }
        
        button:contains("Search & Analyze"):hover {
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4) !important;
        }
        
        /* Full-Screen Dark Loading Overlay - Covers Entire Page */
        .loading-overlay {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(0, 0, 0, 0.35) !important;
            backdrop-filter: blur(10px) !important;
            z-index: 999999 !important;
            display: none !important;
            justify-content: center !important;
            align-items: center !important;
            flex-direction: column !important;
            pointer-events: all !important;
            cursor: not-allowed !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .loading-overlay.show {
            display: flex !important;
        }
        
        .loading-content {
            background: rgba(20, 20, 20, 0.85) !important;
            border-radius: 20px !important;
            padding: 50px 60px !important;
            text-align: center !important;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4) !important;
            border: 2px solid rgba(102, 126, 234, 0.4) !important;
            max-width: 600px !important;
            width: 90% !important;
            position: relative !important;
            z-index: 1000000 !important;
        }
        
        .loading-spinner {
            width: 100px !important;
            height: 100px !important;
            border: 8px solid rgba(102, 126, 234, 0.2) !important;
            border-top: 8px solid #667eea !important;
            border-radius: 50% !important;
            animation: spin 1s linear infinite !important;
            margin: 0 auto 40px !important;
        }
        
        .loading-text {
            color: white !important;
            font-size: 28px !important;
            font-weight: 700 !important;
            text-align: center !important;
            margin-bottom: 20px !important;
            animation: pulse 2s ease-in-out infinite !important;
        }
        
        .loading-subtext {
            color: rgba(255, 255, 255, 0.9) !important;
            font-size: 18px !important;
            text-align: center !important;
            line-height: 1.6 !important;
            margin-bottom: 25px !important;
        }
        
        .loading-progress {
            color: rgba(255, 255, 255, 0.7) !important;
            font-size: 16px !important;
            font-style: italic !important;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        /* Ensure overlay covers everything */
        body.loading-active {
            overflow: hidden !important;
        }
        
        /* Block all interactions */
        .loading-overlay * {
            pointer-events: none !important;
        }
        
        .loading-overlay .loading-content {
            pointer-events: auto !important;
        }
        
        /* Hide Streamlit toolbar/menu/icons (top-right) and footer badges */
        [data-testid="stToolbar"],
        [data-testid="stMainMenu"],
        [data-testid="stStatusWidget"],
        [data-testid="stActionButton"],
        header [data-testid^="baseButton"],
        .stDeployButton,
        .viewerBadge_link,
        .viewerBadge_container__,
        footer,
        #MainMenu {
            display: none !important;
            visibility: hidden !important;
        }

        /* Fallback selectors for older/newer Streamlit/classnames */
        header .stActionButton,
        a[class*="viewerBadge"],
        div[class*="viewerBadge"],
        button[title="View source on GitHub"],
        button[title="Share"],
        button[title="Settings"],
        button[aria-label="Settings"],
        button[aria-label="Share"],
        button[aria-label="View source on GitHub"] {
            display: none !important;
        }
        
        </style>
        <script>
        // Button styling is now handled by CSS above
        
        // Full-Screen Loading Overlay Functions - Enhanced
        function showLoadingOverlay(message = "Processing...", subtext = "Please wait while we work on your request", progress = "") {
            // Remove any existing overlay first
            let existingOverlay = document.getElementById('loading-overlay');
            if (existingOverlay) {
                existingOverlay.remove();
            }
            
            // Create new overlay
            let overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            
            // Set overlay content
            overlay.innerHTML = `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">${message}</div>
                    <div class="loading-subtext">${subtext}</div>
                    ${progress ? `<div class="loading-progress">${progress}</div>` : ''}
                </div>
            `;
            
            // Add to body
            document.body.appendChild(overlay);
            
            // Force show overlay immediately
            setTimeout(() => {
                overlay.classList.add('show');
                document.body.classList.add('loading-active');
            }, 10);
            
            // Block all interactions
            overlay.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            });
            
            overlay.addEventListener('keydown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            });
            
            // Block scrolling
            document.body.style.overflow = 'hidden';
            document.documentElement.style.overflow = 'hidden';
        }
        
        function hideLoadingOverlay() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.remove('show');
                setTimeout(() => {
                    if (overlay.parentNode) {
                        overlay.parentNode.removeChild(overlay);
                    }
                }, 300);
                
                // Restore scrolling
                document.body.classList.remove('loading-active');
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
            }
        }
        
        // Force overlay to show immediately when called
        window.showLoadingOverlay = showLoadingOverlay;
        window.hideLoadingOverlay = hideLoadingOverlay;
        
        // Handle Return key for keyword deletion in multiselect
        setTimeout(function() {
            const multiselectInputs = document.querySelectorAll('input[aria-label*="Select Keywords"]');
            multiselectInputs.forEach(input => {
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === 'Return') {
                        e.preventDefault();
                        // Find the closest selected keyword chip and remove it
                        const container = input.closest('[data-testid="stMultiSelect"]');
                        if (container) {
                            const chips = container.querySelectorAll('[data-testid="stMultiSelect"] > div > div > div > div > div');
                            if (chips.length > 0) {
                                const lastChip = chips[chips.length - 1];
                                const removeButton = lastChip.querySelector('button');
                                if (removeButton) {
                                    removeButton.click();
                                }
                            }
                        }
                    }
                });
            });
        }, 1500);
        </script>
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
        
        # Main content area
        st.markdown("# 🧬 POLO-GGB RESEARCH ASSISTANT")
        
        # Get current state
        active_conversation_id = self.get_user_session('active_conversation_id')
        conversations = self.get_user_session('conversations', {})
        
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
            
            # New Analysis button
            if st.button("➕ New Analysis", type="primary", use_container_width=True):
                self.set_user_session('active_conversation_id', None)
                self.set_user_session('selected_keywords', [])
                self.set_user_session('search_mode', "all_keywords")
                self.set_user_session('custom_summary_chat', [])
                self.set_user_session('analysis_locked', False)  # Unlock for new analysis
                st.rerun()
            
            # Keyword selection
            selected_keywords = st.multiselect(
                "Select Keywords",
                self.GENETICS_KEYWORDS,
                default=self.get_user_session('selected_keywords', []),
                key="html_keywords",
                help="Select keywords for your research analysis" if not analysis_locked else "Keywords are locked for current analysis. Click 'New Analysis' to modify.",
                disabled=analysis_locked
            )
            
            # Search mode
            search_mode = st.selectbox(
                "Search Mode",
                ["all_keywords", "any_keyword"],
                format_func=lambda x: "Find papers containing ALL keywords" if x == "all_keywords" else "Find papers containing AT LEAST ONE keyword",
                index=0 if self.get_user_session('search_mode', 'all_keywords') == 'all_keywords' else 1,
                key="html_search_mode",
                disabled=analysis_locked
            )
            
            # Time filter
            time_filter = st.selectbox(
                "Filter by Time Window",
                ["Current year", "Last 3 months", "Last 6 months", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
                key="html_time_filter",
                disabled=analysis_locked
            )
            
            # Search button
            if st.button("Search & Analyze", type="primary", use_container_width=True, disabled=analysis_locked):
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
                    title = conv_data.get("title", "Chat...")
                    
                    # Create columns for chat title and delete button
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        if st.button(title, key=f"chat_{conv_id}", use_container_width=True):
                            self.set_user_session('active_conversation_id', conv_id)
                            self.set_user_session('analysis_locked', True)  # Lock when viewing past analysis
                            st.rerun()
                    
                    with col2:
                        if st.button("×", key=f"delete_{conv_id}", help="Delete this analysis", type="secondary"):
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
                
                # Custom summary button
                if st.button("Generate Custom Summary", type="primary", use_container_width=True):
                    # Show full-screen overlay immediately via JS (no pre-rerun)
                    st.markdown(
                        """
                        <script>
                        showLoadingOverlay("📄 Generating Custom Summary", "Analyzing your uploaded papers and creating comprehensive summary...", "Processing PDF content and generating AI summary...");
                        </script>
                        """,
                        unsafe_allow_html=True,
                    )

                    success = self.generate_custom_summary(uploaded_papers)

                    # Hide overlay and refresh UI
                    st.markdown(
                        """
                        <script>
                        hideLoadingOverlay();
                        </script>
                        """,
                        unsafe_allow_html=True,
                    )

                    if success:
                        st.rerun()
                    else:
                        st.error("Custom summary generation failed. Please try again.")
                
                # Clear uploaded papers button
                if st.button("Clear uploaded papers", type="secondary", use_container_width=True):
                    self.set_user_session('uploaded_papers', [])
                    st.rerun()
            else:
                st.caption("No papers uploaded yet")
            
            # PDF upload section
            with st.expander("Upload PDF Files"):
                st.info("Upload PDF files to generate custom summary of your documents.")
                
                uploaded_pdfs = st.file_uploader(
                    "Choose PDF files", 
                    accept_multiple_files=True, 
                    type=['pdf'], 
                    key="pdf_uploader_html"
                )
                
                if uploaded_pdfs and st.button("Add PDFs", type="primary"):
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
                conversations = self.get_user_session('conversations', {})
                if active_conversation_id in conversations:
                    active_conv = conversations[active_conversation_id]
                    active_conv["messages"].append({"role": "user", "content": prompt})
                    active_conv['last_interaction_time'] = time.time()
                    self.set_user_session('conversations', conversations)
                    
                    # Save conversation to backend
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
                    """Generate descriptive title like ChatGPT - unique and specific"""
                    paper_count = len(papers)
                    summary_lower = summary_text.lower()
                    
                    # Extract key topics and methodologies
                    topics = []
                    methodologies = []
                    applications = []
                    
                    # Topic detection
                    if any(word in summary_lower for word in ['polygenic risk', 'prs', 'genetic risk']):
                        topics.append('Polygenic Risk')
                    if any(word in summary_lower for word in ['gwas', 'genome-wide association']):
                        topics.append('GWAS')
                    if any(word in summary_lower for word in ['machine learning', 'ai', 'artificial intelligence', 'ml']):
                        methodologies.append('AI/ML')
                    if any(word in summary_lower for word in ['genetics', 'genetic', 'dna', 'genome']):
                        topics.append('Genetics')
                    if any(word in summary_lower for word in ['disease', 'medical', 'health', 'clinical']):
                        applications.append('Medical')
                    if any(word in summary_lower for word in ['prediction', 'predictive', 'modeling']):
                        methodologies.append('Prediction')
                    if any(word in summary_lower for word in ['risk', 'risk assessment']):
                        applications.append('Risk Analysis')
                    if any(word in summary_lower for word in ['ancestry', 'population', 'ethnic']):
                        topics.append('Ancestry')
                    if any(word in summary_lower for word in ['pharmacogenomics', 'drug', 'therapy']):
                        applications.append('Pharmacogenomics')
                    if any(word in summary_lower for word in ['cancer', 'oncology']):
                        applications.append('Cancer Research')
                    if any(word in summary_lower for word in ['cardiovascular', 'heart', 'cardiac']):
                        applications.append('Cardiovascular')
                    
                    # Create descriptive title
                    title_parts = []
                    
                    # Add main topic
                    if topics:
                        title_parts.append(topics[0])
                    
                    # Add methodology if available
                    if methodologies:
                        title_parts.append(f"via {methodologies[0]}")
                    
                    # Add application if available
                    if applications:
                        title_parts.append(f"for {applications[0]}")
                    
                    # Add paper count
                    title_parts.append(f"({paper_count} papers)")
                    
                    if title_parts:
                        return " ".join(title_parts)
                    else:
                        # Fallback: use first meaningful words from summary
                        words = summary_text.split()
                        meaningful_words = [w for w in words[:6] if len(w) > 3 and w.lower() not in ['the', 'and', 'for', 'with', 'this', 'that']]
                        return f"{' '.join(meaningful_words[:4])}... ({paper_count} papers)"
                
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
