# app/gcs_user_storage.py
import json
import os
import time
from typing import Dict, List, Any, Optional
from google.cloud import storage
from google.api_core.exceptions import NotFound
import streamlit as st

class GCSUserStorage:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        
    def _get_user_path(self, username: str, data_type: str) -> str:
        """Get GCS path for user-specific data"""
        return f"user-data/users/{username}/{data_type}.json"
    
    def _get_conversation_path(self, username: str, conversation_id: str) -> str:
        """Get GCS path for specific conversation"""
        return f"user-data/users/{username}/conversations/{conversation_id}.json"
    
    def _get_session_path(self, username: str, session_id: str) -> str:
        """Get GCS path for specific session"""
        return f"user-data/users/{username}/sessions/{session_id}.json"
    
    def save_user_data(self, username: str, data_type: str, data: Dict[str, Any]) -> bool:
        """Save user-specific data to GCS"""
        try:
            path = self._get_user_path(username, data_type)
            blob = self.bucket.blob(path)
            
            # Add metadata
            data_with_metadata = {
                "username": username,
                "data_type": data_type,
                "last_updated": time.time(),
                "data": data
            }
            
            blob.upload_from_string(
                json.dumps(data_with_metadata, indent=2),
                content_type='application/json'
            )
            return True
        except Exception as e:
            st.error(f"Failed to save user data to GCS: {e}")
            return False
    
    def load_user_data(self, username: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Load user-specific data from GCS"""
        try:
            path = self._get_user_path(username, data_type)
            blob = self.bucket.blob(path)
            
            if not blob.exists():
                return None
            
            content = blob.download_as_string()
            data_with_metadata = json.loads(content)
            return data_with_metadata.get("data", {})
        except Exception as e:
            st.error(f"Failed to load user data from GCS: {e}")
            return None
    
    def save_conversation(self, username: str, conversation_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation to GCS"""
        try:
            path = self._get_conversation_path(username, conversation_id)
            blob = self.bucket.blob(path)
            
            # Add metadata
            data_with_metadata = {
                "username": username,
                "conversation_id": conversation_id,
                "last_updated": time.time(),
                "conversation": conversation_data
            }
            
            blob.upload_from_string(
                json.dumps(data_with_metadata, indent=2),
                content_type='application/json'
            )
            return True
        except Exception as e:
            st.error(f"Failed to save conversation to GCS: {e}")
            return False
    
    def load_conversation(self, username: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation from GCS"""
        try:
            path = self._get_conversation_path(username, conversation_id)
            blob = self.bucket.blob(path)
            
            if not blob.exists():
                return None
            
            content = blob.download_as_string()
            data_with_metadata = json.loads(content)
            return data_with_metadata.get("conversation", {})
        except Exception as e:
            st.error(f"Failed to load conversation from GCS: {e}")
            return None
    
    def list_user_conversations(self, username: str) -> List[str]:
        """List all conversation IDs for a user"""
        try:
            prefix = f"user-data/users/{username}/conversations/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            conversation_ids = []
            for blob in blobs:
                # Extract conversation ID from blob name
                filename = os.path.basename(blob.name)
                if filename.endswith('.json'):
                    conversation_id = filename[:-5]  # Remove .json extension
                    conversation_ids.append(conversation_id)
            
            return conversation_ids
        except Exception as e:
            st.error(f"Failed to list user conversations: {e}")
            return []
    
    def save_user_session(self, username: str, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save user session to GCS"""
        try:
            path = self._get_session_path(username, session_id)
            blob = self.bucket.blob(path)
            
            # Add metadata
            data_with_metadata = {
                "username": username,
                "session_id": session_id,
                "last_updated": time.time(),
                "session": session_data
            }
            
            blob.upload_from_string(
                json.dumps(data_with_metadata, indent=2),
                content_type='application/json'
            )
            return True
        except Exception as e:
            st.error(f"Failed to save user session to GCS: {e}")
            return False
    
    def load_user_session(self, username: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Load user session from GCS"""
        try:
            path = self._get_session_path(username, session_id)
            blob = self.bucket.blob(path)
            
            if not blob.exists():
                return None
            
            content = blob.download_as_string()
            data_with_metadata = json.loads(content)
            return data_with_metadata.get("session", {})
        except Exception as e:
            st.error(f"Failed to load user session from GCS: {e}")
            return None
    
    def delete_user_data(self, username: str, data_type: str) -> bool:
        """Delete user-specific data from GCS"""
        try:
            path = self._get_user_path(username, data_type)
            blob = self.bucket.blob(path)
            
            if blob.exists():
                blob.delete()
            return True
        except Exception as e:
            st.error(f"Failed to delete user data from GCS: {e}")
            return False
    
    def delete_conversation(self, username: str, conversation_id: str) -> bool:
        """Delete conversation from GCS"""
        try:
            path = self._get_conversation_path(username, conversation_id)
            blob = self.bucket.blob(path)
            
            if blob.exists():
                blob.delete()
            return True
        except Exception as e:
            st.error(f"Failed to delete conversation from GCS: {e}")
            return False
    
    def sync_user_data_to_gcs(self, username: str, local_data: Dict[str, Any]) -> bool:
        """Sync all user data from local session state to GCS"""
        try:
            # Save conversations
            conversations = local_data.get('conversations', {})
            for conv_id, conv_data in conversations.items():
                self.save_conversation(username, conv_id, conv_data)
            
            # Save other user data
            user_data = {
                'selected_keywords': local_data.get('selected_keywords', []),
                'search_mode': local_data.get('search_mode', 'all_keywords'),
                'uploaded_papers': local_data.get('uploaded_papers', []),
                'custom_summary_chat': local_data.get('custom_summary_chat', []),
                'active_conversation_id': local_data.get('active_conversation_id')
            }
            
            self.save_user_data(username, 'user_preferences', user_data)
            return True
        except Exception as e:
            st.error(f"Failed to sync user data to GCS: {e}")
            return False
    
    def load_user_data_from_gcs(self, username: str) -> Dict[str, Any]:
        """Load all user data from GCS"""
        try:
            # Load user preferences
            user_preferences = self.load_user_data(username, 'user_preferences') or {}
            
            # Load conversations
            conversation_ids = self.list_user_conversations(username)
            conversations = {}
            for conv_id in conversation_ids:
                conv_data = self.load_conversation(username, conv_id)
                if conv_data:
                    conversations[conv_id] = conv_data
            
            return {
                'conversations': conversations,
                'selected_keywords': user_preferences.get('selected_keywords', []),
                'search_mode': user_preferences.get('search_mode', 'all_keywords'),
                'uploaded_papers': user_preferences.get('uploaded_papers', []),
                'custom_summary_chat': user_preferences.get('custom_summary_chat', []),
                'active_conversation_id': user_preferences.get('active_conversation_id')
            }
        except Exception as e:
            st.error(f"Failed to load user data from GCS: {e}")
            return {}
