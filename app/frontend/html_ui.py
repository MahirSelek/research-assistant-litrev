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
                    # Set persistent user data from backend (conversations, active conversation)
                    self.set_user_session('conversations', user_data.get('conversations', {}))
                    self.set_user_session('active_conversation_id', user_data.get('active_conversation_id'))
                    
                    # Clear session-specific data on each login (like in old implementation)
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
        """Inject CSS and JavaScript for the HTML frontend"""
        st.markdown("""
        <style>
        /* Hide Streamlit default elements */
        .main .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        .stApp {
            background: #0e1117 !important;
        }
        
        /* Custom CSS Variables */
        :root {
            --primary-color: #2E8B57;
            --secondary-color: #3CB371;
            --accent-color: #667eea;
            --text-color: #ffffff;
            --bg-color: #0e1117;
            --sidebar-bg: #1e1e1e;
            --card-bg: #2d2d2d;
            --border-color: #404040;
        }
        
        /* Main Layout */
        .app-container {
            display: flex;
            height: 100vh;
            background: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Sidebar */
        .sidebar {
            width: 350px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            overflow-y: auto;
            position: fixed;
            height: 100vh;
            left: 0;
            top: 0;
        }
        
        .main-content {
            margin-left: 350px;
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            height: 100vh;
        }
        
        /* User Info */
        .user-info {
            background: var(--card-bg);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }
        
        .user-info h3 {
            margin: 0 0 10px 0;
            color: var(--primary-color);
        }
        
        /* Buttons */
        .btn {
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            width: 100%;
            margin-bottom: 10px;
        }
        
        .btn:hover {
            background: linear-gradient(90deg, #228B22, #32CD32);
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: var(--text-color);
        }
        
        .form-group select,
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--card-bg);
            color: var(--text-color);
            font-size: 14px;
        }
        
        .form-group select:focus,
        .form-group input:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        /* Keywords */
        .keywords-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }
        
        .keyword-tag {
            background: var(--accent-color);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .keyword-tag .remove {
            cursor: pointer;
            font-weight: bold;
        }
        
        .keyword-tag .remove:hover {
            color: #ff6b6b;
        }
        
        /* Chat Interface */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 40px);
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: var(--bg-color);
        }
        
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            max-width: 80%;
        }
        
        .message.user {
            background: var(--primary-color);
            margin-left: auto;
            text-align: right;
        }
        
        .message.assistant {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
        }
        
        .message-header {
            font-weight: bold;
            margin-bottom: 8px;
            color: var(--accent-color);
        }
        
        .message-content {
            line-height: 1.6;
        }
        
        /* Chat Input */
        .chat-input-container {
            padding: 20px;
            background: var(--sidebar-bg);
            border-top: 1px solid var(--border-color);
        }
        
        .chat-input {
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--card-bg);
            color: var(--text-color);
            font-size: 14px;
        }
        
        .chat-input input:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .chat-input button {
            padding: 12px 20px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .chat-input button:hover {
            background: var(--secondary-color);
        }
        
        /* Loading Overlay */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            color: white;
            font-size: 18px;
        }
        
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 2s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Chat History */
        .chat-history {
            margin-bottom: 20px;
        }
        
        .chat-history h3 {
            color: var(--primary-color);
            margin-bottom: 15px;
        }
        
        .chat-item {
            background: var(--card-bg);
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            cursor: pointer;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        
        .chat-item:hover {
            background: var(--primary-color);
            transform: translateX(5px);
        }
        
        .chat-item.active {
            background: var(--primary-color);
            border-color: var(--secondary-color);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                width: 100%;
                position: relative;
                height: auto;
            }
            
            .main-content {
                margin-left: 0;
            }
            
            .app-container {
                flex-direction: column;
            }
        }
        
        /* Hide Streamlit elements */
        .stApp > header {
            display: none !important;
        }
        
        .stApp > div:first-child {
            display: none !important;
        }
        </style>
        
        <script>
        // JavaScript for interactive functionality
        function addKeyword(keyword) {
            const container = document.getElementById('keywords-container');
            const tag = document.createElement('div');
            tag.className = 'keyword-tag';
            tag.innerHTML = `
                ${keyword}
                <span class="remove" onclick="removeKeyword(this)">×</span>
            `;
            container.appendChild(tag);
            updateKeywords();
        }
        
        function removeKeyword(element) {
            element.parentElement.remove();
            updateKeywords();
        }
        
        function updateKeywords() {
            const tags = document.querySelectorAll('.keyword-tag');
            const keywords = Array.from(tags).map(tag => tag.textContent.replace('×', '').trim());
            
            // Send to Streamlit
            const keywordInput = document.getElementById('selected-keywords');
            if (keywordInput) {
                keywordInput.value = JSON.stringify(keywords);
            }
        }
        
        function startAnalysis() {
            const keywords = Array.from(document.querySelectorAll('.keyword-tag'))
                .map(tag => tag.textContent.replace('×', '').trim());
            
            if (keywords.length === 0) {
                alert('Please select at least one keyword');
                return;
            }
            
            // Show loading
            showLoading('Searching for highly relevant papers and generating a comprehensive, in-depth report...');
            
            // Send to Streamlit
            const form = document.getElementById('analysis-form');
            if (form) {
                form.submit();
            }
        }
        
        function showLoading(message) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div style="text-align: center;">
                    <div class="loading-spinner"></div>
                    <p>${message}</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        
        function hideLoading() {
            const overlay = document.querySelector('.loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
        
        function loadChatHistory() {
            // This will be populated by Streamlit
            const container = document.getElementById('chat-history-container');
            return container ? container.innerHTML : '';
        }
        
        function selectChat(chatId) {
            // Remove active class from all items
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Add active class to selected item
            event.target.closest('.chat-item').classList.add('active');
            
            // Send to Streamlit
            const input = document.getElementById('selected-chat');
            if (input) {
                input.value = chatId;
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (message) {
                // Add message to chat
                addMessage('user', message);
                input.value = '';
                
                // Send to Streamlit
                const form = document.getElementById('chat-form');
                if (form) {
                    form.submit();
                }
            }
        }
        
        function addMessage(role, content) {
            const container = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const header = role === 'user' ? 'You' : 'Assistant';
            messageDiv.innerHTML = `
                <div class="message-header">${header}</div>
                <div class="message-content">${content}</div>
            `;
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Hide loading if it exists
            hideLoading();
            
            // Set up keyword selection
            const keywordSelect = document.getElementById('keyword-select');
            if (keywordSelect) {
                keywordSelect.addEventListener('change', function() {
                    if (this.value) {
                        addKeyword(this.value);
                        this.value = '';
                    }
                });
            }
            
            // Set up chat input
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)
    
    def render_main_interface(self):
        """Render the main HTML interface"""
        # Inject CSS and JavaScript
        self.inject_css_and_js()
        
        # Get current state
        active_conversation_id = self.get_user_session('active_conversation_id')
        conversations = self.get_user_session('conversations', {})
        
        # Show loading overlay if analysis is in progress
        if st.session_state.get('is_loading_analysis', False):
            st.markdown(f"""
            <div class="loading-overlay">
                <div style="text-align: center;">
                    <div class="loading-spinner"></div>
                    <p>{st.session_state.loading_message}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Main HTML Interface
        st.markdown("""
        <div class="app-container">
            <div class="sidebar">
                <div class="user-info">
                    <h3>Research Assistant</h3>
                    <p>Logged in as: """ + st.session_state.get('username', 'User') + """</p>
                    <p>Role: """ + ('Administrator' if st.session_state.get('username') == 'admin' else 'User') + """</p>
                </div>
                
                <button class="btn" onclick="window.location.reload()">➕ New Analysis</button>
                
                <div class="chat-history">
                    <h3>Chat History</h3>
                    <div id="chat-history-container">
        """, unsafe_allow_html=True)
        
        # Render chat history
        if conversations:
            for conv_id, conv_data in conversations.items():
                title = conv_data.get("title", "Chat...")
                is_active = conv_id == active_conversation_id
                active_class = "active" if is_active else ""
                
                st.markdown(f"""
                <div class="chat-item {active_class}" onclick="selectChat('{conv_id}')">
                    {title}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color: #666;">No past analyses found.</p>', unsafe_allow_html=True)
        
        st.markdown("""
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Start a New Analysis</label>
                    <p style="color: #4CAF50; font-size: 12px; margin: 5px 0;">Data available until: end of September 2025</p>
                </div>
                
                <div class="form-group">
                    <label>Select Keywords</label>
                    <select id="keyword-select">
                        <option value="">Choose a keyword...</option>
        """, unsafe_allow_html=True)
        
        # Add keyword options
        for keyword in self.GENETICS_KEYWORDS:
            st.markdown(f'<option value="{keyword}">{keyword}</option>', unsafe_allow_html=True)
        
        st.markdown("""
                    </select>
                    <div id="keywords-container" class="keywords-container">
        """, unsafe_allow_html=True)
        
        # Show selected keywords
        selected_keywords = self.get_user_session('selected_keywords', [])
        for keyword in selected_keywords:
            st.markdown(f"""
            <div class="keyword-tag">
                {keyword}
                <span class="remove" onclick="removeKeyword(this)">×</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Search Mode</label>
                    <select id="search-mode">
                        <option value="all_keywords">Find papers containing ALL keywords</option>
                        <option value="any_keyword">Find papers containing AT LEAST ONE keyword</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Filter by Time Window</label>
                    <select id="time-filter">
                        <option value="Current year">Current year</option>
                        <option value="Last 3 months">Last 3 months</option>
                        <option value="Last 6 months">Last 6 months</option>
                        <option value="January">January</option>
                        <option value="February">February</option>
                        <option value="March">March</option>
                        <option value="April">April</option>
                        <option value="May">May</option>
                        <option value="June">June</option>
                        <option value="July">July</option>
                        <option value="August">August</option>
                        <option value="September">September</option>
                        <option value="October">October</option>
                        <option value="November">November</option>
                        <option value="December">December</option>
                    </select>
                </div>
                
                <button class="btn" onclick="startAnalysis()">Search & Analyze</button>
                
                <div class="form-group">
                    <label>Uploaded Papers</label>
                    <p id="uploaded-count">No papers uploaded yet</p>
                    <button class="btn btn-secondary" onclick="uploadPapers()">Upload PDF Files</button>
                </div>
                
                <button class="btn" onclick="generateCustomSummary()">Generate Custom Summary</button>
                
                <button class="btn btn-secondary" onclick="logout()">Logout</button>
            </div>
            
            <div class="main-content">
                <div class="chat-container">
                    <div class="chat-messages" id="chat-messages">
        """, unsafe_allow_html=True)
        
        # Render active conversation
        if active_conversation_id and active_conversation_id in conversations:
            active_conv = conversations[active_conversation_id]
            
            for message in active_conv.get("messages", []):
                role = message["role"]
                content = message["content"]
                
                st.markdown(f"""
                <div class="message {role}">
                    <div class="message-header">{'You' if role == 'user' else 'Assistant'}</div>
                    <div class="message-content">{content}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="message assistant">
                <div class="message-header">Assistant</div>
                <div class="message-content">
                    Select keywords and click 'Search & Analyze' to start a new report, or choose a past report from the sidebar.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
                    </div>
                    
                    <div class="chat-input-container">
                        <div class="chat-input">
                            <input type="text" id="chat-input" placeholder="Ask a follow-up question...">
                            <button onclick="sendMessage()">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Hidden form for Streamlit communication -->
        <form id="analysis-form" style="display: none;">
            <input type="hidden" id="selected-keywords" name="keywords">
            <input type="hidden" id="search-mode-value" name="search_mode">
            <input type="hidden" id="time-filter-value" name="time_filter">
        </form>
        
        <form id="chat-form" style="display: none;">
            <input type="hidden" id="chat-message" name="message">
        </form>
        
        <form id="chat-select-form" style="display: none;">
            <input type="hidden" id="selected-chat" name="chat_id">
        </form>
        """, unsafe_allow_html=True)
    
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
        """Handle form submissions from the HTML interface"""
        # Handle keyword search form
        if st.form_submit_button("Search & Analyze", key="html_search_form"):
            keywords_str = st.session_state.get('html_keywords', '[]')
            search_mode = st.session_state.get('html_search_mode', 'all_keywords')
            time_filter = st.session_state.get('html_time_filter', 'Current year')
            
            try:
                keywords = json.loads(keywords_str) if keywords_str else []
                if keywords:
                    st.session_state.is_loading_analysis = True
                    st.session_state.loading_message = "Searching for highly relevant papers and generating a comprehensive, in-depth report..."
                    
                    success = self.process_keyword_search(keywords, time_filter, search_mode)
                    st.session_state.is_loading_analysis = False
                    
                    if success:
                        st.rerun()
                    else:
                        st.error("Analysis failed. Please try again.")
                else:
                    st.error("Please select at least one keyword.")
            except Exception as e:
                st.error(f"Error processing form: {e}")
        
        # Handle chat message form
        if st.form_submit_button("Send Message", key="html_chat_form"):
            message = st.session_state.get('html_chat_message', '')
            if message:
                active_conversation_id = self.get_user_session('active_conversation_id')
                if active_conversation_id:
                    conversations = self.get_user_session('conversations', {})
                    if active_conversation_id in conversations:
                        active_conv = conversations[active_conversation_id]
                        active_conv["messages"].append({"role": "user", "content": message})
                        active_conv['last_interaction_time'] = time.time()
                        self.set_user_session('conversations', conversations)
                        
                        # Save conversation to backend
                        username = st.session_state.get('username')
                        if username:
                            self.api.save_conversation(username, active_conversation_id, active_conv)
                        
                        st.rerun()
        
        # Handle chat selection form
        if st.form_submit_button("Select Chat", key="html_chat_select_form"):
            chat_id = st.session_state.get('html_selected_chat', '')
            if chat_id:
                self.set_user_session('active_conversation_id', chat_id)
                st.rerun()
    
    def generate_custom_summary(self, uploaded_papers: List[Dict]):
        """Generate custom summary via backend"""
        try:
            print(f"Generating custom summary for {len(uploaded_papers)} papers")
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
