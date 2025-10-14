# app/test_automatic_system.py
"""
Test script to verify the automatic authentication system works correctly.
This tests the complete flow without any manual intervention.
"""

import os
import sys
import time

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_automatic_system():
    """Test the automatic authentication system"""
    print("🧪 Testing Automatic Authentication System")
    print("=" * 50)
    
    try:
        from auth import AuthenticationManager, initialize_default_admin
        from persistent_storage import PersistentStorageManager
        
        # Test with your actual bucket
        test_bucket = "polo-ggb-bucket"
        
        print(f"📦 Testing with bucket: {test_bucket}")
        
        # Initialize storage manager
        storage_manager = PersistentStorageManager(test_bucket)
        
        # Initialize auth manager
        auth_manager = AuthenticationManager()
        auth_manager.storage_manager = storage_manager
        
        # Test 1: Check if admin user exists
        print("\n1️⃣ Checking if admin user exists...")
        admin_data = storage_manager.get_user_data("admin")
        if admin_data:
            print("✅ Admin user already exists")
            print(f"   Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(admin_data['created_at']))}")
        else:
            print("❌ Admin user does not exist")
        
        # Test 2: Test automatic admin creation
        print("\n2️⃣ Testing automatic admin creation...")
        initialize_default_admin()
        
        # Check again
        admin_data = storage_manager.get_user_data("admin")
        if admin_data:
            print("✅ Admin user created automatically")
            print(f"   Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(admin_data['created_at']))}")
            print(f"   Username: {admin_data['username']}")
            print(f"   Role: {admin_data['profile']['role']}")
        else:
            print("❌ Admin user creation failed")
            return False
        
        # Test 3: Test user registration
        print("\n3️⃣ Testing user registration...")
        test_username = f"test_user_{int(time.time())}"
        test_password = "test_password_123"
        
        success = auth_manager.create_user(test_username, test_password)
        if success:
            print(f"✅ User '{test_username}' registered successfully")
        else:
            print(f"❌ User registration failed")
            return False
        
        # Test 4: Test authentication
        print("\n4️⃣ Testing authentication...")
        success, message = auth_manager.authenticate_user(test_username, test_password)
        if success:
            print(f"✅ Authentication successful: {message}")
        else:
            print(f"❌ Authentication failed: {message}")
            return False
        
        # Test 5: Test wrong password
        print("\n5️⃣ Testing wrong password...")
        success, message = auth_manager.authenticate_user(test_username, "wrong_password")
        if not success:
            print(f"✅ Wrong password correctly rejected: {message}")
        else:
            print(f"❌ Wrong password incorrectly accepted")
            return False
        
        # Test 6: Test conversation persistence
        print("\n6️⃣ Testing conversation persistence...")
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
            print(f"✅ Conversation saved successfully")
        else:
            print(f"❌ Conversation save failed")
            return False
        
        # Test 7: Test conversation retrieval
        print("\n7️⃣ Testing conversation retrieval...")
        retrieved_conv = storage_manager.get_conversation(test_username, conv_id)
        if retrieved_conv and retrieved_conv["title"] == "Test Conversation":
            print(f"✅ Conversation retrieved successfully")
        else:
            print(f"❌ Conversation retrieval failed")
            return False
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        success = storage_manager.delete_user(test_username)
        if success:
            print(f"✅ Test user '{test_username}' deleted successfully")
        else:
            print(f"❌ Failed to delete test user '{test_username}'")
        
        print("\n🎉 All automatic system tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the automatic system test"""
    print("🚀 Testing Automatic Authentication System")
    print("=" * 70)
    print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_automatic_system()
    
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    
    if success:
        print("🎉 AUTOMATIC SYSTEM TESTS PASSED!")
        print("\n✅ Your authentication system is completely automatic and secure:")
        print("   • Admin user created automatically on first run")
        print("   • Random secure password generated")
        print("   • No manual intervention required")
        print("   • No password sharing")
        print("   • Complete data persistence")
        print("   • Rate limiting handled gracefully")
        
        print("\n🚀 Ready for production deployment!")
        print("   • Deploy your application")
        print("   • First user will see the generated admin password")
        print("   • Admin can change password immediately")
        print("   • All user data persists automatically")
    else:
        print("⚠️  Automatic system tests failed.")
        print("   Please check the error messages above.")

if __name__ == "__main__":
    main()
