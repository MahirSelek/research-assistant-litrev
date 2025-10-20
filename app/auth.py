# app/auth.py
import streamlit as st
import hashlib
import secrets
import time
from typing import Dict, Optional, Tuple
import json
import os

class AuthenticationManager:
    def __init__(self):
        self.users_file = "users.json"
        self.session_timeout = 3600  # 1 hour in seconds
        self.max_login_attempts = 5
        self.lockout_duration = 300  # 5 minutes in seconds
        
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Combine password and salt
        password_salt = password + salt
        # Hash using SHA-256
        hashed = hashlib.sha256(password_salt.encode()).hexdigest()
        
        return hashed, salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against stored hash"""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == hashed
    
    def load_users(self) -> Dict:
        """Load users from file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_users(self, users: Dict):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def create_user(self, username: str, password: str) -> bool:
        """Create a new user"""
        users = self.load_users()
        
        if username in users:
            return False  # User already exists
        
        hashed_password, salt = self.hash_password(password)
        
        users[username] = {
            'password_hash': hashed_password,
            'salt': salt,
            'created_at': time.time(),
            'last_login': None,
            'login_attempts': 0,
            'locked_until': None
        }
        
        self.save_users(users)
        return True
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user with username and password"""
        users = self.load_users()
        
        if username not in users:
            return False, "Invalid username or password"
        
        user = users[username]
        current_time = time.time()
        
        # Check if account is locked
        if user.get('locked_until') and current_time < user['locked_until']:
            remaining_time = int(user['locked_until'] - current_time)
            return False, f"Account locked. Try again in {remaining_time} seconds."
        
        # Verify password
        if not self.verify_password(password, user['password_hash'], user['salt']):
            # Increment login attempts
            user['login_attempts'] = user.get('login_attempts', 0) + 1
            
            # Lock account if too many attempts
            if user['login_attempts'] >= self.max_login_attempts:
                user['locked_until'] = current_time + self.lockout_duration
                self.save_users(users)
                return False, f"Too many failed attempts. Account locked for {self.lockout_duration // 60} minutes."
            
            self.save_users(users)
            return False, "Invalid username or password"
        
        # Successful login - reset attempts and update last login
        user['login_attempts'] = 0
        user['locked_until'] = None
        user['last_login'] = current_time
        self.save_users(users)
        
        return True, "Login successful"
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            return False
        
        if 'login_time' not in st.session_state:
            return False
        
        current_time = time.time()
        session_age = current_time - st.session_state.login_time
        
        return session_age < self.session_timeout
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Perform login and set session"""
        success, message = self.authenticate_user(username, password)
        
        if success:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.login_time = time.time()
            st.session_state.session_id = secrets.token_hex(16)
        
        return success, message
    
    def logout(self):
        """Logout user and clear session"""
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        if 'username' in st.session_state:
            del st.session_state.username
        if 'login_time' in st.session_state:
            del st.session_state.login_time
        if 'session_id' in st.session_state:
            del st.session_state.session_id
    
    def require_auth(self) -> bool:
        """Require authentication - redirect to login if not authenticated"""
        # Debug: Check session state
        if 'authenticated' not in st.session_state:
            return False
        
        if not self.is_session_valid():
            self.logout()
            return False
        return True

# Initialize authentication manager
auth_manager = AuthenticationManager()

# Default users creation (only if no users exist)
def initialize_default_users():
    """Create default users if they don't exist"""
    users = auth_manager.load_users()
    
    # Create 4 strong user accounts with secure passwords
    user_credentials = [
        ("admin", "PoloGGB2024!Admin"),
        ("researcher1", "Genomics2024!Res1"),
        ("researcher2", "Genetics2024!Res2"),
        ("researcher3", "Biology2024!Res3"),
        ("researcher4", "Science2024!Res4")
    ]
    
    users_created = []
    for username, password in user_credentials:
        if username not in users:
            auth_manager.create_user(username, password)
            users_created.append(username)
    
    if users_created:
        print(f"Created new users: {', '.join(users_created)}")
        print("Users created successfully. Credentials should be shared securely.")

def show_login_page():
    """Display the login page"""
    st.set_page_config(
        page_title="Polo GGB Research Assistant - Login",
        page_icon="polo-ggb-logo.png",
        layout="centered"
    )
    
    # Simple CSS for login page
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #2E8B57, #3CB371);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .error-message {
        background: rgba(220, 53, 69, 0.1);
        border: 1px solid rgba(220, 53, 69, 0.3);
        border-radius: 5px;
        padding: 0.75rem;
        margin: 1rem 0;
        color: #dc3545;
    }
    
    .success-message {
        background: rgba(40, 167, 69, 0.1);
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-radius: 5px;
        padding: 0.75rem;
        margin: 1rem 0;
        color: #28a745;
    }

    /* Hide Streamlit top-right toolbar and bottom-right badges on login page */
    [data-testid="stToolbar"],
    [data-testid="stMainMenu"],
    [data-testid="stStatusWidget"],
    header [data-testid^="baseButton"],
    .stDeployButton,
    .viewerBadge_link,
    .viewerBadge_container__,
    footer,
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    /* Fallback selectors */
    button[title="View source on GitHub"],
    button[title="Share"],
    button[title="Settings"],
    button[aria-label="Settings"],
    button[aria-label="Share"],
    button[aria-label="View source on GitHub"],
    a[class*="viewerBadge"],
    div[class*="viewerBadge"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Defensive JS: hide Streamlit chrome on login using MutationObserver
    st.markdown(
        """
        <script>
        (function hideStreamlitChrome() {
          function hideNow() {
            const selectors = [
              '[data-testid="stToolbar"]',
              '[data-testid="stMainMenu"]',
              '[data-testid="stStatusWidget"]',
              'header [data-testid^="baseButton"]',
              '.stDeployButton',
              '.viewerBadge_link',
              '.viewerBadge_container__',
              'footer',
              '#MainMenu',
              'button[title="View source on GitHub"]',
              'button[title="Share"]',
              'button[title="Settings"]',
              'button[aria-label="Settings"]',
              'button[aria-label="Share"]',
              'button[aria-label="View source on GitHub"]',
              'a[class*="viewerBadge"]',
              'div[class*="viewerBadge"]'
            ];
            selectors.forEach(sel => {
              document.querySelectorAll(sel).forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
              });
            });
            // Also hide any header buttons with text like "Fork"
            document.querySelectorAll('header button, header a').forEach(el => {
              const t = (el.innerText || '').trim().toLowerCase();
              if (t === 'fork' || t === 'share') {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
              }
            });
          }
          function removeBottomBadges() {
            const nodes = Array.from(document.querySelectorAll('a,div,button'));
            nodes.forEach(el => {
              try {
                const cs = window.getComputedStyle(el);
                if (cs.position === 'fixed') {
                  const r = el.getBoundingClientRect();
                  const nearRight = (window.innerWidth - r.right) < 120;
                  const nearBottom = (window.innerHeight - r.bottom) < 120;
                  if (nearRight && nearBottom) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                  }
                }
                // Links to streamlit cloud
                if (el.tagName === 'A' && el.href && el.href.includes('streamlit')) {
                  el.style.display = 'none';
                  el.style.visibility = 'hidden';
                }
              } catch (e) {}
            });
          }
          // Run immediately and on DOM mutations
          const observer = new MutationObserver(() => { hideNow(); removeBottomBadges(); });
          observer.observe(document.documentElement, { childList: true, subtree: true });
          window.addEventListener('load', () => { hideNow(); removeBottomBadges(); });
          hideNow();
          removeBottomBadges();
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )
    
    # Simple header
    st.markdown("---")
    
    # Login form only
    st.markdown("### Research Assistant Login")
    st.info("Please log in to access the Polo GGB Research Assistant")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        
        submitted = st.form_submit_button("Login", use_container_width=True)
    
    if submitted:
        if username and password:
            success, message = auth_manager.login(username, password)
            
            if success:
                st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">❌ Please enter both username and password</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>© 2024 Polo GGB - Research and Services that create value</p>
        <p>Genomics, Genetics, Biology</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize default users on first run
    initialize_default_users()

def show_logout_button():
    """Show logout button in sidebar"""
    if st.session_state.get('authenticated', False):
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            auth_manager.logout()
            st.rerun()
