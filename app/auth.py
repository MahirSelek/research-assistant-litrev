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

# Default admin user creation (only if no users exist)
def initialize_default_admin():
    """Create default admin user if no users exist"""
    users = auth_manager.load_users()
    if not users:
        # Create default admin user
        auth_manager.create_user("admin", "pologgb2024")
        # Don't show success message to avoid confusion

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
    </style>
    """, unsafe_allow_html=True)
    
    # Logo and company name
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Try to display logo
        try:
            st.image("polo-ggb-logo.png", width=120)
        except:
            st.markdown("🧬 **Polo GGB**")
        
        st.markdown("**Polo d'Innovazione di Genomica, Genetica e Biologia**")
        st.markdown("---")
    # Login/Register tabs
    tab1, tab2 = st.tabs(["Log in", "Sign in"])
    
    with tab1:
        st.markdown("### Research Assistant Log in")
        st.info("Please log in to access the Polo GGB Research Assistant")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            submitted = st.form_submit_button("Login", use_container_width=True)
    
    with tab2:
        st.markdown("### Create New Account")
        st.info("Register for access to the Polo GGB Research Assistant")
        
        with st.form("register_form"):
            new_username = st.text_input("New Username", placeholder="Choose a username", key="register_username")
            new_password = st.text_input("New Password", type="password", placeholder="Choose a password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="confirm_password")
            
            # Password requirements
            st.markdown("**Password Requirements:**")
            st.markdown("- At least 8 characters long")
            st.markdown("- Contains letters and numbers")
            
            register_submitted = st.form_submit_button("Create Account", use_container_width=True)
        
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
        
        if register_submitted:
            if new_username and new_password and confirm_password:
                # Validate password
                if len(new_password) < 8:
                    st.markdown('<div class="error-message">❌ Password must be at least 8 characters long</div>', unsafe_allow_html=True)
                elif not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
                    st.markdown('<div class="error-message">❌ Password must contain both letters and numbers</div>', unsafe_allow_html=True)
                elif new_password != confirm_password:
                    st.markdown('<div class="error-message">❌ Passwords do not match</div>', unsafe_allow_html=True)
                else:
                    # Create new user
                    success = auth_manager.create_user(new_username, new_password)
                    if success:
                        st.markdown('<div class="success-message">✅ Account created successfully! You can now login.</div>', unsafe_allow_html=True)
                        # Auto-login the new user
                        auth_manager.login(new_username, new_password)
                        st.rerun()
                    else:
                        st.markdown('<div class="error-message">❌ Username already exists. Please choose a different username.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-message">❌ Please fill in all fields</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>© 2024 Polo GGB - Research and Services that create value</p>
        <p>Genomics, Genetics, Biology</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize default admin on first run
    initialize_default_admin()

def show_logout_button():
    """Show logout button in sidebar"""
    if st.session_state.get('authenticated', False):
        with st.sidebar:
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"👤 **{st.session_state.username}**")
            with col2:
                if st.button("🚪", help="Logout", key="logout_btn"):
                    auth_manager.logout()
                    st.rerun()
