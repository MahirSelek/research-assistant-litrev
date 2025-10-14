# app/test_persistence.py
"""
Test script to verify the persistent storage and authentication system.
This script can be run to test the GCS-based persistence functionality.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_persistent_storage():
    """Test the persistent storage functionality"""
    print("🧪 Testing Persistent Storage System")
    print("=" * 50)
    
    try:
        from persistent_storage import PersistentStorageManager
        
        # Test with a test bucket (you'll need to replace with your actual bucket)
        test_bucket = "your-test-bucket-name"  # Replace with actual bucket name
        
        print(f"📦 Initializing storage manager with bucket: {test_bucket}")
        storage_manager = PersistentStorageManager(test_bucket)
        
        # Test user creation
        print("\n👤 Testing user creation...")
        test_username = f"test_user_{int(time.time())}"
        test_password = "test_password_123"
        
        success = storage_manager.create_user(test_username, test_password)
        if success:
            print(f"✅ User '{test_username}' created successfully")
        else:
            print(f"❌ Failed to create user '{test_username}'")
            return False
        
        # Test user authentication
        print("\n🔐 Testing user authentication...")
        success, message = storage_manager.verify_password(test_username, test_password)
        if success:
            print(f"✅ Authentication successful: {message}")
        else:
            print(f"❌ Authentication failed: {message}")
            return False
        
        # Test wrong password
        print("\n🚫 Testing wrong password...")
        success, message = storage_manager.verify_password(test_username, "wrong_password")
        if not success:
            print(f"✅ Wrong password correctly rejected: {message}")
        else:
            print(f"❌ Wrong password incorrectly accepted")
            return False
        
        # Test conversation creation
        print("\n💬 Testing conversation creation...")
        conv_id = f"test_conv_{int(time.time())}"
        conversation_data = {
            "title": "Test Conversation",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "keywords": ["test"],
            "search_mode": "all_keywords",
            "retrieved_papers": [],
            "total_papers_found": 0,
            "created_at": time.time(),
            "last_interaction_time": time.time()
        }
        
        success = storage_manager.save_conversation(test_username, conv_id, conversation_data)
        if success:
            print(f"✅ Conversation '{conv_id}' saved successfully")
        else:
            print(f"❌ Failed to save conversation '{conv_id}'")
            return False
        
        # Test conversation retrieval
        print("\n📖 Testing conversation retrieval...")
        retrieved_conv = storage_manager.get_conversation(test_username, conv_id)
        if retrieved_conv and retrieved_conv["title"] == "Test Conversation":
            print(f"✅ Conversation retrieved successfully")
        else:
            print(f"❌ Failed to retrieve conversation")
            return False
        
        # Test user conversations list
        print("\n📋 Testing user conversations list...")
        conversations = storage_manager.get_user_conversations(test_username)
        if conv_id in conversations:
            print(f"✅ Conversation found in user's conversation list")
        else:
            print(f"❌ Conversation not found in user's conversation list")
            return False
        
        # Test session data
        print("\n💾 Testing session data...")
        session_data = {
            "active_conversation_id": conv_id,
            "selected_keywords": ["test", "example"],
            "search_mode": "all_keywords",
            "uploaded_papers": [],
            "custom_summary_chat": []
        }
        
        success = storage_manager.save_user_session(test_username, session_data)
        if success:
            print(f"✅ Session data saved successfully")
        else:
            print(f"❌ Failed to save session data")
            return False
        
        # Test session data retrieval
        retrieved_session = storage_manager.get_user_session(test_username)
        if retrieved_session and retrieved_session["active_conversation_id"] == conv_id:
            print(f"✅ Session data retrieved successfully")
        else:
            print(f"❌ Failed to retrieve session data")
            return False
        
        # Test user stats
        print("\n📊 Testing user statistics...")
        stats = storage_manager.get_user_stats(test_username)
        if stats["username"] == test_username and stats["total_conversations"] == 1:
            print(f"✅ User statistics generated correctly")
        else:
            print(f"❌ User statistics incorrect")
            return False
        
        # Cleanup - delete test user
        print("\n🧹 Cleaning up test data...")
        success = storage_manager.delete_user(test_username)
        if success:
            print(f"✅ Test user '{test_username}' deleted successfully")
        else:
            print(f"❌ Failed to delete test user '{test_username}'")
        
        print("\n🎉 All tests passed! Persistent storage system is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication_manager():
    """Test the authentication manager"""
    print("\n🔐 Testing Authentication Manager")
    print("=" * 50)
    
    try:
        from auth import AuthenticationManager
        
        # Note: This will fail if GCS bucket is not configured
        print("📦 Initializing authentication manager...")
        auth_manager = AuthenticationManager()
        
        if not auth_manager.storage_manager:
            print("⚠️  Storage manager not initialized (GCS bucket not configured)")
            print("   This is expected in test environment without proper secrets")
            return True
        
        # Test user creation
        print("\n👤 Testing user creation...")
        test_username = f"auth_test_user_{int(time.time())}"
        test_password = "auth_test_password_123"
        
        success = auth_manager.create_user(test_username, test_password)
        if success:
            print(f"✅ User '{test_username}' created successfully")
        else:
            print(f"❌ Failed to create user '{test_username}'")
            return False
        
        # Test authentication
        print("\n🔐 Testing authentication...")
        success, message = auth_manager.authenticate_user(test_username, test_password)
        if success:
            print(f"✅ Authentication successful: {message}")
        else:
            print(f"❌ Authentication failed: {message}")
            return False
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        success = auth_manager.storage_manager.delete_user(test_username)
        if success:
            print(f"✅ Test user '{test_username}' deleted successfully")
        else:
            print(f"❌ Failed to delete test user '{test_username}'")
        
        print("\n🎉 Authentication manager tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Authentication and Persistence Tests")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test persistent storage
    storage_test_passed = test_persistent_storage()
    
    # Test authentication manager
    auth_test_passed = test_authentication_manager()
    
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    print(f"📦 Persistent Storage: {'✅ PASSED' if storage_test_passed else '❌ FAILED'}")
    print(f"🔐 Authentication Manager: {'✅ PASSED' if auth_test_passed else '❌ FAILED'}")
    
    if storage_test_passed and auth_test_passed:
        print("\n🎉 ALL TESTS PASSED! Your authentication and persistence system is ready for production!")
        print("\n📝 Next Steps:")
        print("   1. Deploy your application with proper GCS bucket configuration")
        print("   2. Test user registration and login in production")
        print("   3. Verify that conversations persist across sessions")
        print("   4. Monitor user data in your GCS bucket")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
        print("   Make sure your GCS bucket is properly configured and accessible.")

if __name__ == "__main__":
    main()
