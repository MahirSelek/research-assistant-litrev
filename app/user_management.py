# app/user_management.py
import streamlit as st
import json
import time
from auth import auth_manager

def show_user_management():
    """Show user management interface for admin users"""
    
    # Check if user is admin
    if st.session_state.get('username') != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    # Back button
    if st.button("← Back to Research Assistant"):
        st.session_state.show_user_management = False
        st.rerun()
    
    st.title("👥 User Management")
    st.markdown("Manage users and access to the Polo GGB Research Assistant")
    
    # Check if storage manager is available
    if not auth_manager.storage_manager:
        st.error("Storage manager not initialized. Cannot manage users.")
        return
    
    # Show user count
    all_users = auth_manager.storage_manager.get_all_users()
    total_users = len(all_users)
    st.info(f"📊 Total registered users: **{total_users}**")
    
    # Create new user section
    st.subheader("➕ Add New User")
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username", placeholder="Enter username")
        with col2:
            new_password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.form_submit_button("Create User"):
            if new_username and new_password:
                if auth_manager.create_user(new_username, new_password):
                    st.success(f"User '{new_username}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"User '{new_username}' already exists!")
            else:
                st.error("Please enter both username and password")
    
    st.markdown("---")
    
    # Display existing users
    st.subheader("📋 Current Users")
    
    if not all_users:
        st.info("No users found.")
        return
    
    # Create a table of users
    user_data = []
    for user_info in all_users:
        username = user_info['username']
        created_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(user_info.get('created_at', 0)))
        last_login = user_info.get('last_login')
        if last_login:
            last_login_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(last_login))
        else:
            last_login_date = "Never"
        
        login_attempts = user_info.get('login_attempts', 0)
        locked_until = user_info.get('locked_until')
        if locked_until and time.time() < locked_until:
            status = f"🔒 Locked ({int(locked_until - time.time())}s)"
        else:
            status = "✅ Active"
        
        user_data.append({
            "Username": username,
            "Created": created_date,
            "Last Login": last_login_date,
            "Failed Attempts": login_attempts,
            "Status": status
        })
    
    # Display users table
    for i, user in enumerate(user_data):
        with st.expander(f"👤 {user['Username']} - {user['Status']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Created:** {user['Created']}")
                st.write(f"**Last Login:** {user['Last Login']}")
            
            with col2:
                st.write(f"**Failed Attempts:** {user['Failed Attempts']}")
                st.write(f"**Status:** {user['Status']}")
            
            with col3:
                if user['Username'] != 'admin':  # Don't allow deleting admin
                    if st.button(f"🗑️ Delete User", key=f"delete_{user['Username']}"):
                        if auth_manager.storage_manager.delete_user(user['Username']):
                            st.success(f"User '{user['Username']}' deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete user '{user['Username']}'")
                
                # Reset login attempts
                if user['Failed Attempts'] > 0:
                    if st.button(f"🔄 Reset Attempts", key=f"reset_{user['Username']}"):
                        user_data = auth_manager.storage_manager.get_user_data(user['Username'])
                        if user_data:
                            user_data['login_attempts'] = 0
                            user_data['locked_until'] = None
                            if auth_manager.storage_manager.update_user_data(user['Username'], user_data):
                                st.success(f"Login attempts reset for '{user['Username']}'!")
                                st.rerun()
                            else:
                                st.error(f"Failed to reset attempts for '{user['Username']}'")
    
    # System statistics
    st.markdown("---")
    st.subheader("📊 System Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(all_users))
    
    with col2:
        active_users = len([u for u in all_users if u.get('last_login', 0) > time.time() - 86400])  # Last 24 hours
        st.metric("Active (24h)", active_users)
    
    with col3:
        locked_users = len([u for u in all_users if u.get('locked_until', 0) > time.time()])
        st.metric("Locked Users", locked_users)
    
    with col4:
        total_attempts = sum(u.get('login_attempts', 0) for u in all_users)
        st.metric("Failed Attempts", total_attempts)
    
    # Recent registrations
    st.markdown("---")
    st.subheader("🆕 Recent Registrations")
    
    recent_users = []
    for user_info in all_users:
        created_time = user_info.get('created_at', 0)
        if created_time > time.time() - 7 * 86400:  # Last 7 days
            recent_users.append((user_info['username'], created_time))
    
    recent_users.sort(key=lambda x: x[1], reverse=True)
    
    if recent_users:
        for username, created_time in recent_users[:5]:  # Show last 5
            created_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(created_time))
            st.write(f"• **{username}** - {created_date}")
    else:
        st.info("No new registrations in the last 7 days")
    
    # Password change section
    st.markdown("---")
    st.subheader("🔐 Change Admin Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password", placeholder="Enter current password")
        new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
        confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
        
        if st.form_submit_button("Change Password"):
            if current_password and new_password and confirm_password:
                # Verify current password
                success, message = auth_manager.authenticate_user("admin", current_password)
                if success:
                    if new_password == confirm_password:
                        if len(new_password) >= 8 and any(c.isalpha() for c in new_password) and any(c.isdigit() for c in new_password):
                            # Update password
                            user_data = auth_manager.storage_manager.get_user_data("admin")
                            if user_data:
                                # Generate new salt and hash
                                import hashlib
                                import secrets
                                new_salt = secrets.token_hex(16)
                                new_hash = hashlib.sha256((new_password + new_salt).encode()).hexdigest()
                                
                                user_data['password_hash'] = new_hash
                                user_data['salt'] = new_salt
                                
                                if auth_manager.storage_manager.update_user_data("admin", user_data):
                                    st.success("✅ Password changed successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update password")
                            else:
                                st.error("❌ Admin user not found")
                        else:
                            st.error("❌ New password must be at least 8 characters with letters and numbers")
                    else:
                        st.error("❌ New passwords do not match")
                else:
                    st.error("❌ Current password is incorrect")
            else:
                st.error("❌ Please fill in all fields")
    
    # Security settings
    st.markdown("---")
    st.subheader("🔒 Security Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Max Login Attempts:** {auth_manager.max_login_attempts}")
        st.write(f"**Lockout Duration:** {auth_manager.lockout_duration // 60} minutes")
    
    with col2:
        st.write(f"**Session Timeout:** {auth_manager.session_timeout // 3600} hours")
        st.write(f"**Password Hashing:** SHA-256 with Salt")
        st.write(f"**Storage:** Google Cloud Storage (Persistent)")

if __name__ == "__main__":
    # Check authentication
    if not auth_manager.require_auth():
        from auth import show_login_page
        show_login_page()
    else:
        show_user_management()
