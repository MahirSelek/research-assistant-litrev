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
        
        # Custom avatars for chat messages - Professional Icons8 genetics icons
        # User avatar: Magnifying glass with DNA helix (for researcher/user)
        self.USER_AVATAR = "data:image/png;base64,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"
        
        # Assistant avatar: DNA helix icon (for AI assistant)
        self.ASSISTANT_AVATAR = "data:image/png;base64,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"
        
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
        
        </style>
        <script>
        // Button styling is now handled by CSS above
        
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
        # Show loading overlay if analysis is in progress
        if st.session_state.get('is_loading_analysis', False):
            loading_message = st.session_state.loading_message
            st.markdown(f"""
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.8); display: flex; justify-content: center; align-items: center; z-index: 9999; color: white; font-size: 18px;">
                <div style="text-align: center;">
                    <div style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 2s linear infinite; margin: 0 auto 20px;"></div>
                    <p>{loading_message}</p>
                </div>
            </div>
            <style>
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
            """, unsafe_allow_html=True)
            return
        
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
                    st.session_state.is_loading_analysis = True
                    st.session_state.loading_message = "Searching for highly relevant papers and generating a comprehensive, in-depth report..."
                    
                    success = self.process_keyword_search(selected_keywords, time_filter, search_mode)
                    st.session_state.is_loading_analysis = False
                    
                    if success:
                        # Lock the analysis after successful search
                        self.set_user_session('analysis_locked', True)
                        st.rerun()
                    else:
                        st.error("Analysis failed. Please try again.")
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
                    st.session_state.is_loading_analysis = True
                    st.session_state.loading_message = "Generating summary of your uploaded papers..."
                    
                    success = self.generate_custom_summary(uploaded_papers)
                    st.session_state.is_loading_analysis = False
                    
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
                    with st.spinner("Processing PDF files..."):
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
