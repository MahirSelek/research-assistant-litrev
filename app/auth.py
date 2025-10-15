# app/auth.py
import streamlit as st
import hashlib
import secrets
import time
import re
from typing import Dict, Optional, Tuple
import json
import os
from google.cloud import storage
from google.api_core.exceptions import NotFound
import base64
from cryptography.fernet import Fernet
import urllib.parse
import streamlit.components.v1 as components

class AuthenticationManager:
    def __init__(self):
        try:
            # GCS Configuration
            self.gcs_bucket_name = st.secrets["app_config"]["gcs_bucket_name"]
            self.gcs_project_id = st.secrets["vertex_ai"]["VERTEXAI_PROJECT"]  # Use same project as Vertex AI
            self.users_folder = "user-data/"
            self.session_timeout = 3600  # 1 hour in seconds
            self.max_login_attempts = 5
            self.lockout_duration = 300  # 5 minutes in seconds
            
            # Wait for credentials to be set up (same as main.py)
            import time
            max_retries = 10
            for i in range(max_retries):
                if os.path.exists("gcp_credentials.json"):
                    break
                time.sleep(0.5)
            
            # Test GCS connection
            try:
                self.storage_client = storage.Client(project=self.gcs_project_id)
                self.bucket = self.storage_client.bucket(self.gcs_bucket_name)
                
                # Test if bucket exists and is accessible
                if self.bucket.exists():
                    # Connection successful - no need to show message to users
                    pass
                else:
                    st.error(f"❌ GCS Bucket not found: {self.gcs_bucket_name}")
                    raise Exception("Bucket not accessible")
                    
            except Exception as e:
                st.error(f"❌ GCS Connection failed: {e}")
                raise
            
            # Generate encryption key for user data (this should be stored securely in production)
            self.encryption_key = self._get_or_create_encryption_key()
            self.cipher_suite = Fernet(self.encryption_key)
            
        except Exception as e:
            st.error(f"Failed to initialize authentication system: {e}")
            st.error("Please check your Google Cloud configuration and secrets.")
            raise
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for user data"""
        key_blob_name = f"{self.users_folder}encryption_key.key"
        key_blob = self.bucket.blob(key_blob_name)
        
        try:
            # Try to get existing key
            encrypted_key = key_blob.download_as_bytes()
            return encrypted_key
        except NotFound:
            # Create new key
            key = Fernet.generate_key()
            key_blob.upload_from_string(key)
            return key
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def encrypt_user_data(self, data: dict) -> str:
        """Encrypt user data before storing"""
        json_data = json.dumps(data)
        encrypted_data = self.cipher_suite.encrypt(json_data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_user_data(self, encrypted_data: str) -> dict:
        """Decrypt user data after retrieving"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception:
            return {}
        
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2 for better security"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 with 100,000 iterations for better security
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against stored hash"""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == hashed
    
    def load_users(self) -> Dict:
        """Load users from GCS"""
        try:
            users_blob_name = f"{self.users_folder}users.json"
            users_blob = self.bucket.blob(users_blob_name)
            
            if users_blob.exists():
                encrypted_data = users_blob.download_as_text()
                return self.decrypt_user_data(encrypted_data)
                return {}
        except Exception as e:
            st.error(f"Error loading users: {e}")
        return {}
    
    def save_users(self, users: Dict):
        """Save users to GCS"""
        try:
            users_blob_name = f"{self.users_folder}users.json"
            users_blob = self.bucket.blob(users_blob_name)
            
            encrypted_data = self.encrypt_user_data(users)
            users_blob.upload_from_string(encrypted_data)
        except Exception as e:
            st.error(f"Error saving users: {e}")
    
    def create_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Create a new user with password validation"""
        # Validate password strength
        is_valid, message = self.validate_password_strength(password)
        if not is_valid:
            return False, message
        
        users = self.load_users()
        
        if username in users:
            return False, "Username already exists"
        
        hashed_password, salt = self.hash_password(password)
        
        users[username] = {
            'password_hash': hashed_password,
            'salt': salt,
            'created_at': time.time(),
            'last_login': None,
            'login_attempts': 0,
            'locked_until': None,
            'role': 'user'  # Default role
        }
        
        self.save_users(users)
        return True, "User created successfully"
    
    def save_user_data(self, username: str, data: dict):
        """Save user-specific data (chat history, etc.) to GCS"""
        try:
            user_data_blob_name = f"{self.users_folder}{username}_data.json"
            user_data_blob = self.bucket.blob(user_data_blob_name)
            
            encrypted_data = self.encrypt_user_data(data)
            user_data_blob.upload_from_string(encrypted_data)
        except Exception as e:
            st.error(f"Error saving user data: {e}")
    
    def load_user_data(self, username: str) -> dict:
        """Load user-specific data (chat history, etc.) from GCS"""
        try:
            user_data_blob_name = f"{self.users_folder}{username}_data.json"
            user_data_blob = self.bucket.blob(user_data_blob_name)
            
            if user_data_blob.exists():
                encrypted_data = user_data_blob.download_as_text()
                return self.decrypt_user_data(encrypted_data)
            return {}
        except Exception as e:
            st.error(f"Error loading user data: {e}")
            return {}
    
    def delete_user_data(self, username: str):
        """Delete user-specific data from GCS"""
        try:
            user_data_blob_name = f"{self.users_folder}{username}_data.json"
            user_data_blob = self.bucket.blob(user_data_blob_name)
            
            if user_data_blob.exists():
                user_data_blob.delete()
        except Exception as e:
            st.error(f"Error deleting user data: {e}")
    
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
            
            # Load user-specific data from GCS
            user_data = self.load_user_data(username)
            if user_data:
                # Restore user's chat history and other data
                for key, value in user_data.items():
                    st.session_state[f"{key}_{username}"] = value
        
        return success, message
    
    def logout(self):
        """Logout user and save data before clearing session"""
        if 'authenticated' in st.session_state and 'username' in st.session_state:
            username = st.session_state.username
            
            # Save user-specific data to GCS before logout
            user_data = {}
            for key, value in st.session_state.items():
                if key.endswith(f"_{username}"):
                    # Extract the original key name
                    original_key = key[:-len(f"_{username}")]
                    user_data[original_key] = value
            
            if user_data:
                self.save_user_data(username, user_data)
        
        # Clear session state
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

# JavaScript functions for localStorage session management
SESSION_JS = """
<script>
function setSessionData(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (e) {
        console.error('Error setting session data:', e);
        return false;
    }
}

function getSessionData(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (e) {
        console.error('Error getting session data:', e);
        return null;
    }
}

function removeSessionData(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (e) {
        console.error('Error removing session data:', e);
        return false;
    }
}

function clearAllSessionData() {
    try {
        localStorage.clear();
        return true;
    } catch (e) {
        console.error('Error clearing session data:', e);
        return false;
    }
}

// Check for existing session on page load
window.addEventListener('load', function() {
    const sessionData = getSessionData('streamlit_session');
    if (sessionData && sessionData.username) {
        // Notify Streamlit that we have a session
        window.parent.postMessage({
            type: 'streamlit:session_restore',
            session: sessionData
        }, '*');
    }
});
</script>
"""

# Fallback AuthenticationManager with localStorage-based session persistence
class FallbackAuthenticationManager:
    def __init__(self):
        self.session_timeout = 1800  # 30 minutes
        self.max_login_attempts = 5
        self.lockout_duration = 300
        
        # Initialize persistent storage
        if 'persistent_users' not in st.session_state:
            st.session_state.persistent_users = {
                "admin": {
                    "password_hash": "fallback", 
                    "salt": "fallback", 
                    "role": "admin",
                    "created_at": time.time(),
                    "last_login": None,
                    "login_attempts": 0,
                    "locked_until": None
                }
            }
        
        if 'persistent_user_data' not in st.session_state:
            st.session_state.persistent_user_data = {}
            
        if 'persistent_sessions' not in st.session_state:
            st.session_state.persistent_sessions = {}
        
        # Inject JavaScript for localStorage management
        components.html(SESSION_JS, height=0)
        
        # Check for existing session in localStorage
        self._check_localStorage_session()
    
    def _check_localStorage_session(self):
        """Check for valid session in localStorage"""
        try:
            # Use JavaScript to check localStorage
            js_code = """
            <script>
            const sessionData = localStorage.getItem('streamlit_session');
            if (sessionData) {
                try {
                    const session = JSON.parse(sessionData);
                    const now = Date.now();
                    const sessionAge = now - session.login_time;
                    const timeoutMs = 30 * 60 * 1000; // 30 minutes
                    
                    if (sessionAge < timeoutMs && session.username) {
                        // Session is valid, notify Streamlit
                        window.parent.postMessage({
                            type: 'streamlit:session_restore',
                            session: session
                        }, '*');
                    } else {
                        // Session expired, remove it
                        localStorage.removeItem('streamlit_session');
                    }
                } catch (e) {
                    localStorage.removeItem('streamlit_session');
                }
            }
            </script>
            """
            
            components.html(js_code, height=0)
            
        except Exception as e:
            st.error(f"Error checking localStorage session: {e}")
        
        return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, "Password is valid"
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2 for better security"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 with 100,000 iterations for better security
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against stored hash"""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == hashed
    
    def create_user(self, username: str, password: str) -> Tuple[bool, str]:
        is_valid, message = self.validate_password_strength(password)
        if not is_valid:
            return False, message
        if username in self.users:
            return False, "Username already exists"
        
        hashed_password, salt = self.hash_password(password)
        self.users[username] = {
            "password_hash": hashed_password,
            "salt": salt,
            "role": "user",
            "created_at": time.time(),
            "last_login": None,
            "login_attempts": 0,
            "locked_until": None
        }
        self.save_users(self.users)
        return True, "User created successfully"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        if username not in self.users:
            return False, "Invalid username or password"
        
        user = self.users[username]
        current_time = time.time()
        
        # Check if account is locked
        if user.get('locked_until') and current_time < user['locked_until']:
            remaining_time = int(user['locked_until'] - current_time)
            return False, f"Account locked. Try again in {remaining_time} seconds."
        
        # Special case for admin fallback
        if username == "admin" and password == "PoloGGB2024!":
            # Update last login
            user['last_login'] = current_time
            user['login_attempts'] = 0
            user['locked_until'] = None
            self.save_users(self.users)
            return True, "Login successful"
        
        # Verify password for regular users
        if not self.verify_password(password, user['password_hash'], user['salt']):
            # Increment login attempts
            user['login_attempts'] = user.get('login_attempts', 0) + 1
            
            # Lock account if too many attempts
            if user['login_attempts'] >= self.max_login_attempts:
                user['locked_until'] = current_time + self.lockout_duration
                self.save_users(self.users)
                return False, f"Too many failed attempts. Account locked for {self.lockout_duration // 60} minutes."
            
            self.save_users(self.users)
            return False, "Invalid username or password"
        
        # Successful login - reset attempts and update last login
        user['login_attempts'] = 0
        user['locked_until'] = None
        user['last_login'] = current_time
        self.save_users(self.users)
        
        return True, "Login successful"
    
    def load_users(self) -> Dict:
        """Load users from persistent storage"""
        return st.session_state.persistent_users
    
    def save_users(self, users: Dict):
        """Save users to persistent storage"""
        st.session_state.persistent_users = users
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        success, message = self.authenticate_user(username, password)
        if success:
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            login_time = time.time()
            
            # Store session in persistent storage
            st.session_state.persistent_sessions[session_token] = {
                'username': username,
                'login_time': login_time,
                'session_id': session_token
            }
            
            # Set current session
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.login_time = login_time
            st.session_state.session_id = session_token
            
            # Store session in localStorage using JavaScript
            session_data = {
                'username': username,
                'login_time': login_time * 1000,  # Convert to milliseconds for JavaScript
                'session_id': session_token,
                'authenticated': True
            }
            
            js_code = f"""
            <script>
            localStorage.setItem('streamlit_session', JSON.stringify({json.dumps(session_data)}));
            console.log('Session stored in localStorage');
            </script>
            """
            components.html(js_code, height=0)
            
            # Load user-specific data
            user_data = self.load_user_data(username)
            if user_data:
                for key, value in user_data.items():
                    st.session_state[f"{key}_{username}"] = value
            
            st.success(f"✅ Logged in as {username}")
        
        return success, message
    
    def logout(self):
        """Logout user and save data before clearing session"""
        if 'authenticated' in st.session_state and 'username' in st.session_state:
            username = st.session_state.username
            session_id = st.session_state.get('session_id')
            
            # Save user-specific data before logout
            user_data = {}
            for key, value in st.session_state.items():
                if key.endswith(f"_{username}"):
                    # Extract the original key name
                    original_key = key[:-len(f"_{username}")]
                    user_data[original_key] = value
            
            if user_data:
                self.save_user_data(username, user_data)
            
            # Remove session from persistent storage
            if session_id and session_id in st.session_state.persistent_sessions:
                del st.session_state.persistent_sessions[session_id]
        
        # Clear localStorage session using JavaScript
        js_code = """
        <script>
        localStorage.removeItem('streamlit_session');
        console.log('Session cleared from localStorage');
        </script>
        """
        components.html(js_code, height=0)
        
        # Clear session state
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        if 'username' in st.session_state:
            del st.session_state.username
        if 'login_time' in st.session_state:
            del st.session_state.login_time
        if 'session_id' in st.session_state:
            del st.session_state.session_id
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        if 'authenticated' not in st.session_state or not st.session_state.get('authenticated', False):
            return False
        
        if 'login_time' not in st.session_state:
            return False
        
        current_time = time.time()
        session_age = current_time - st.session_state.login_time
        
        # Check if session has expired
        if session_age > self.session_timeout:
            return False
        
        # Check if session token exists in persistent storage
        session_id = st.session_state.get('session_id')
        if session_id and session_id not in st.session_state.persistent_sessions:
            return False
        
        return True
    
    def save_user_data(self, username: str, data: dict):
        """Save user-specific data to persistent storage"""
        try:
            st.session_state.persistent_user_data[username] = data
            st.info(f"💾 Data saved for {username} to persistent storage")
        except Exception as e:
            st.error(f"Error saving user data: {e}")
    
    def load_user_data(self, username: str) -> dict:
        """Load user-specific data from persistent storage"""
        try:
            data = st.session_state.persistent_user_data.get(username, {})
            if data:
                st.info(f"📂 Data loaded for {username} from persistent storage")
            else:
                st.info(f"📂 No data found for {username} in persistent storage")
            return data
        except Exception as e:
            st.error(f"Error loading user data: {e}")
            return {}
    
    def delete_user_data(self, username: str):
        """Delete user-specific data from persistent storage"""
        try:
            if username in st.session_state.persistent_user_data:
                del st.session_state.persistent_user_data[username]
                st.info(f"🗑️ Data deleted for {username}")
        except Exception as e:
            st.error(f"Error deleting user data: {e}")
    
    def restore_session_from_localStorage(self, session_data):
        """Restore session from localStorage data"""
        try:
            username = session_data.get('username')
            login_time = session_data.get('login_time', 0) / 1000  # Convert from milliseconds
            session_id = session_data.get('session_id')
            
            # Check if session is still valid
            current_time = time.time()
            if current_time - login_time < self.session_timeout:
                # Restore session
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.login_time = login_time
                st.session_state.session_id = session_id
                
                # Store session in persistent storage
                st.session_state.persistent_sessions[session_id] = {
                    'username': username,
                    'login_time': login_time,
                    'session_id': session_id
                }
                
                # Load user data
                user_data = self.load_user_data(username)
                if user_data:
                    for key, value in user_data.items():
                        st.session_state[f"{key}_{username}"] = value
                
                st.success(f"🔄 Session restored for {username}")
                return True
            else:
                # Session expired, clear localStorage
                js_code = """
                <script>
                localStorage.removeItem('streamlit_session');
                </script>
                """
                components.html(js_code, height=0)
                return False
        except Exception as e:
            st.error(f"Error restoring session: {e}")
            return False
    
    def require_auth(self) -> bool:
        """Require authentication - check session validity and restore if needed"""
        # Check if user is currently authenticated
        if 'authenticated' not in st.session_state or not st.session_state.get('authenticated', False):
            # Try to restore from localStorage
            js_code = """
            <script>
            const sessionData = localStorage.getItem('streamlit_session');
            if (sessionData) {
                try {
                    const session = JSON.parse(sessionData);
                    const now = Date.now();
                    const sessionAge = now - session.login_time;
                    const timeoutMs = 30 * 60 * 1000; // 30 minutes
                    
                    if (sessionAge < timeoutMs && session.username) {
                        // Session is valid, trigger restoration
                        window.parent.postMessage({
                            type: 'streamlit:session_restore',
                            session: session
                        }, '*');
                    } else {
                        // Session expired, remove it
                        localStorage.removeItem('streamlit_session');
                    }
                } catch (e) {
                    localStorage.removeItem('streamlit_session');
                }
            }
            </script>
            """
            components.html(js_code, height=0)
            return False
        
        # Check if current session is valid
        if not self.is_session_valid():
            self.logout()
            return False
        
        return True

# Initialize authentication manager lazily
auth_manager = None

def get_auth_manager():
    """Get the authentication manager, initializing it if needed"""
    global auth_manager
    if auth_manager is None:
        try:
            # Try to initialize cloud-based auth
            auth_manager = AuthenticationManager()
        except Exception as e:
            # Fall back to local auth if cloud fails
            st.warning(f"⚠️ Cloud auth failed: {e}")
            st.warning("🔄 Falling back to local storage (data won't be saved to cloud)")
            auth_manager = FallbackAuthenticationManager()
    return auth_manager

# Default admin user creation (only if no users exist)
def initialize_default_admin():
    """Create default admin user if no users exist"""
    auth_mgr = get_auth_manager()
    users = auth_mgr.load_users()
    if not users:
        # Create default admin user with strong password
        success, message = auth_mgr.create_user("admin", "PoloGGB2024!")
        if success:
            # Set admin role
            users = auth_mgr.load_users()
            users["admin"]["role"] = "admin"
            auth_mgr.save_users(users)
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
    
    # Simple login page - no logo
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
            st.markdown("- Contains uppercase and lowercase letters")
            st.markdown("- Contains at least one number")
            st.markdown("- Contains at least one special character (!@#$%^&* etc.)")
            
            register_submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            if username and password:
                auth_mgr = get_auth_manager()
                success, message = auth_mgr.login(username, password)
                
                if success:
                    st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-message">❌ Please enter both username and password</div>', unsafe_allow_html=True)
        
        if register_submitted:
            if new_username and new_password and confirm_password:
                auth_mgr = get_auth_manager()
                # Validate password strength
                is_valid, message = auth_mgr.validate_password_strength(new_password)
                if not is_valid:
                    st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
                elif new_password != confirm_password:
                    st.markdown('<div class="error-message">❌ Passwords do not match</div>', unsafe_allow_html=True)
                else:
                    # Create new user
                    success, message = auth_mgr.create_user(new_username, new_password)
                    if success:
                        st.markdown('<div class="success-message">✅ Account created successfully! You can now login.</div>', unsafe_allow_html=True)
                        # Auto-login the new user
                        auth_mgr.login(new_username, new_password)
                        st.rerun()
                    else:
                        st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
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
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            auth_mgr = get_auth_manager()
            auth_mgr.logout()
            st.rerun()
