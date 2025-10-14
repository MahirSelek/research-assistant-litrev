# app/persistent_storage.py
import streamlit as st
import json
import time
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Tuple
from google.cloud import storage
from google.api_core.exceptions import NotFound
import os

class PersistentStorageManager:
    """
    Manages persistent storage of user data using Google Cloud Storage.
    This ensures data persists across deployments and sessions.
    """
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        
        # Ensure required folders exist
        self._ensure_folders_exist()
    
    def _ensure_folders_exist(self):
        """Ensure required folder structure exists in GCS"""
        folders = [
            "user-data/",
            "user-data/users/",
            "user-data/conversations/",
            "user-data/sessions/"
        ]
        
        for folder in folders:
            try:
                # Create a placeholder file to ensure folder exists
                blob = self.bucket.blob(f"{folder}.gitkeep")
                if not blob.exists():
                    blob.upload_from_string("")
            except Exception as e:
                st.error(f"Failed to create folder {folder}: {e}")
    
    def _get_user_blob_path(self, username: str) -> str:
        """Get the blob path for user data"""
        return f"user-data/users/{username}.json"
    
    def _get_conversation_blob_path(self, username: str, conversation_id: str) -> str:
        """Get the blob path for a specific conversation"""
        return f"user-data/conversations/{username}/{conversation_id}.json"
    
    def _get_user_conversations_index_path(self, username: str) -> str:
        """Get the blob path for user's conversations index"""
        return f"user-data/conversations/{username}/index.json"
    
    def _get_session_blob_path(self, username: str) -> str:
        """Get the blob path for user session data"""
        return f"user-data/sessions/{username}.json"
    
    def _upload_json(self, blob_path: str, data: Dict) -> bool:
        """Upload JSON data to GCS"""
        try:
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            return True
        except Exception as e:
            st.error(f"Failed to upload {blob_path}: {e}")
            return False
    
    def _download_json(self, blob_path: str) -> Optional[Dict]:
        """Download JSON data from GCS"""
        try:
            blob = self.bucket.blob(blob_path)
            if not blob.exists():
                return None
            
            content = blob.download_as_string()
            return json.loads(content)
        except NotFound:
            return None
        except Exception as e:
            st.error(f"Failed to download {blob_path}: {e}")
            return None
    
    def _delete_blob(self, blob_path: str) -> bool:
        """Delete a blob from GCS"""
        try:
            blob = self.bucket.blob(blob_path)
            if blob.exists():
                blob.delete()
            return True
        except Exception as e:
            st.error(f"Failed to delete {blob_path}: {e}")
            return False
    
    # User Management Methods
    def create_user(self, username: str, password: str) -> bool:
        """Create a new user with persistent storage"""
        # Check if user already exists
        if self.get_user_data(username) is not None:
            return False
        
        # Hash password with salt
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        user_data = {
            'username': username,
            'password_hash': password_hash,
            'salt': salt,
            'created_at': time.time(),
            'last_login': None,
            'login_attempts': 0,
            'locked_until': None,
            'profile': {
                'display_name': username,
                'email': None,
                'role': 'user'
            }
        }
        
        # Upload user data
        blob_path = self._get_user_blob_path(username)
        success = self._upload_json(blob_path, user_data)
        
        if success:
            # Initialize user's conversations index
            self._initialize_user_conversations(username)
            # Initialize user's session data
            self._initialize_user_session(username)
        
        return success
    
    def get_user_data(self, username: str) -> Optional[Dict]:
        """Get user data from persistent storage"""
        blob_path = self._get_user_blob_path(username)
        return self._download_json(blob_path)
    
    def update_user_data(self, username: str, user_data: Dict) -> bool:
        """Update user data in persistent storage"""
        blob_path = self._get_user_blob_path(username)
        return self._upload_json(blob_path, user_data)
    
    def verify_password(self, username: str, password: str) -> Tuple[bool, str]:
        """Verify user password"""
        user_data = self.get_user_data(username)
        if not user_data:
            return False, "User not found"
        
        # Check if account is locked
        current_time = time.time()
        if user_data.get('locked_until') and current_time < user_data['locked_until']:
            remaining_time = int(user_data['locked_until'] - current_time)
            return False, f"Account locked. Try again in {remaining_time} seconds."
        
        # Verify password
        salt = user_data['salt']
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        if password_hash != user_data['password_hash']:
            # Increment login attempts
            user_data['login_attempts'] = user_data.get('login_attempts', 0) + 1
            
            # Lock account if too many attempts
            max_attempts = 5
            lockout_duration = 300  # 5 minutes
            if user_data['login_attempts'] >= max_attempts:
                user_data['locked_until'] = current_time + lockout_duration
                self.update_user_data(username, user_data)
                return False, f"Too many failed attempts. Account locked for {lockout_duration // 60} minutes."
            
            self.update_user_data(username, user_data)
            return False, "Invalid password"
        
        # Successful login - reset attempts and update last login
        user_data['login_attempts'] = 0
        user_data['locked_until'] = None
        user_data['last_login'] = current_time
        self.update_user_data(username, user_data)
        
        return True, "Login successful"
    
    def delete_user(self, username: str) -> bool:
        """Delete user and all associated data"""
        try:
            # Delete user data
            user_blob_path = self._get_user_blob_path(username)
            self._delete_blob(user_blob_path)
            
            # Delete user's conversations
            self._delete_user_conversations(username)
            
            # Delete user's session data
            session_blob_path = self._get_session_blob_path(username)
            self._delete_blob(session_blob_path)
            
            return True
        except Exception as e:
            st.error(f"Failed to delete user {username}: {e}")
            return False
    
    # Conversation Management Methods
    def _initialize_user_conversations(self, username: str):
        """Initialize user's conversations index"""
        conversations_index = {
            'conversations': {},
            'last_updated': time.time()
        }
        blob_path = self._get_user_conversations_index_path(username)
        self._upload_json(blob_path, conversations_index)
    
    def save_conversation(self, username: str, conversation_id: str, conversation_data: Dict) -> bool:
        """Save a conversation to persistent storage"""
        # Save the conversation
        blob_path = self._get_conversation_blob_path(username, conversation_id)
        success = self._upload_json(blob_path, conversation_data)
        
        if success:
            # Update conversations index
            self._update_conversations_index(username, conversation_id, conversation_data)
        
        return success
    
    def get_conversation(self, username: str, conversation_id: str) -> Optional[Dict]:
        """Get a specific conversation from persistent storage"""
        blob_path = self._get_conversation_blob_path(username, conversation_id)
        return self._download_json(blob_path)
    
    def get_user_conversations(self, username: str) -> Dict:
        """Get all conversations for a user"""
        blob_path = self._get_user_conversations_index_path(username)
        conversations_index = self._download_json(blob_path)
        
        if not conversations_index:
            return {}
        
        return conversations_index.get('conversations', {})
    
    def _update_conversations_index(self, username: str, conversation_id: str, conversation_data: Dict):
        """Update the conversations index for a user"""
        blob_path = self._get_user_conversations_index_path(username)
        conversations_index = self._download_json(blob_path)
        
        if not conversations_index:
            conversations_index = {'conversations': {}, 'last_updated': time.time()}
        
        # Update the conversation entry
        conversations_index['conversations'][conversation_id] = {
            'title': conversation_data.get('title', 'Untitled'),
            'created_at': conversation_data.get('created_at', time.time()),
            'last_interaction_time': conversation_data.get('last_interaction_time', time.time()),
            'message_count': len(conversation_data.get('messages', [])),
            'keywords': conversation_data.get('keywords', []),
            'search_mode': conversation_data.get('search_mode', 'all_keywords')
        }
        conversations_index['last_updated'] = time.time()
        
        self._upload_json(blob_path, conversations_index)
    
    def delete_conversation(self, username: str, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            # Delete the conversation file
            blob_path = self._get_conversation_blob_path(username, conversation_id)
            self._delete_blob(blob_path)
            
            # Update conversations index
            blob_path = self._get_user_conversations_index_path(username)
            conversations_index = self._download_json(blob_path)
            
            if conversations_index and conversation_id in conversations_index.get('conversations', {}):
                del conversations_index['conversations'][conversation_id]
                conversations_index['last_updated'] = time.time()
                self._upload_json(blob_path, conversations_index)
            
            return True
        except Exception as e:
            st.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    def _delete_user_conversations(self, username: str):
        """Delete all conversations for a user"""
        try:
            # Get all conversations
            conversations = self.get_user_conversations(username)
            
            # Delete each conversation
            for conversation_id in conversations.keys():
                blob_path = self._get_conversation_blob_path(username, conversation_id)
                self._delete_blob(blob_path)
            
            # Delete conversations index
            index_blob_path = self._get_user_conversations_index_path(username)
            self._delete_blob(index_blob_path)
            
        except Exception as e:
            st.error(f"Failed to delete conversations for user {username}: {e}")
    
    # Session Management Methods
    def _initialize_user_session(self, username: str):
        """Initialize user's session data"""
        session_data = {
            'active_conversation_id': None,
            'selected_keywords': [],
            'search_mode': 'all_keywords',
            'uploaded_papers': [],
            'custom_summary_chat': [],
            'last_updated': time.time()
        }
        blob_path = self._get_session_blob_path(username)
        self._upload_json(blob_path, session_data)
    
    def save_user_session(self, username: str, session_data: Dict) -> bool:
        """Save user session data"""
        session_data['last_updated'] = time.time()
        blob_path = self._get_session_blob_path(username)
        return self._upload_json(blob_path, session_data)
    
    def get_user_session(self, username: str) -> Optional[Dict]:
        """Get user session data"""
        blob_path = self._get_session_blob_path(username)
        return self._download_json(blob_path)
    
    def update_user_session_key(self, username: str, key: str, value: Any) -> bool:
        """Update a specific key in user session data"""
        session_data = self.get_user_session(username)
        if not session_data:
            session_data = {}
        
        session_data[key] = value
        return self.save_user_session(username, session_data)
    
    # Utility Methods
    def get_all_users(self) -> List[Dict]:
        """Get all users (for admin purposes)"""
        try:
            blobs = self.bucket.list_blobs(prefix="user-data/users/")
            users = []
            
            for blob in blobs:
                if blob.name.endswith('.json'):
                    username = blob.name.split('/')[-1].replace('.json', '')
                    user_data = self.get_user_data(username)
                    if user_data:
                        users.append(user_data)
            
            return users
        except Exception as e:
            st.error(f"Failed to get all users: {e}")
            return []
    
    def get_user_stats(self, username: str) -> Dict:
        """Get user statistics"""
        user_data = self.get_user_data(username)
        conversations = self.get_user_conversations(username)
        session_data = self.get_user_session(username)
        
        stats = {
            'username': username,
            'created_at': user_data.get('created_at', 0) if user_data else 0,
            'last_login': user_data.get('last_login', 0) if user_data else 0,
            'total_conversations': len(conversations),
            'uploaded_papers': len(session_data.get('uploaded_papers', [])) if session_data else 0,
            'login_attempts': user_data.get('login_attempts', 0) if user_data else 0,
            'is_locked': bool(user_data.get('locked_until', 0) > time.time()) if user_data else False
        }
        
        return stats
    
    def backup_user_data(self, username: str) -> Optional[Dict]:
        """Create a backup of all user data"""
        try:
            user_data = self.get_user_data(username)
            conversations = self.get_user_conversations(username)
            session_data = self.get_user_session(username)
            
            # Get all conversation details
            conversation_details = {}
            for conv_id in conversations.keys():
                conv_data = self.get_conversation(username, conv_id)
                if conv_data:
                    conversation_details[conv_id] = conv_data
            
            backup = {
                'user_data': user_data,
                'conversations_index': conversations,
                'conversation_details': conversation_details,
                'session_data': session_data,
                'backup_created_at': time.time()
            }
            
            return backup
        except Exception as e:
            st.error(f"Failed to create backup for user {username}: {e}")
            return None
    
    def restore_user_data(self, username: str, backup_data: Dict) -> bool:
        """Restore user data from backup"""
        try:
            # Restore user data
            if 'user_data' in backup_data:
                self.update_user_data(username, backup_data['user_data'])
            
            # Restore conversations
            if 'conversation_details' in backup_data:
                for conv_id, conv_data in backup_data['conversation_details'].items():
                    self.save_conversation(username, conv_id, conv_data)
            
            # Restore session data
            if 'session_data' in backup_data:
                self.save_user_session(username, backup_data['session_data'])
            
            return True
        except Exception as e:
            st.error(f"Failed to restore data for user {username}: {e}")
            return False
