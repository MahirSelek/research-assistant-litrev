# app/user_management.py
import streamlit as st
import json
import time
from auth import get_auth_manager

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
    
    # Show user count
    auth_mgr = get_auth_manager()
    total_users = len(auth_mgr.load_users())
    st.info(f"📊 Total registered users: **{total_users}**")
    
    # Load current users
    users = auth_mgr.load_users()
    
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
                auth_mgr = get_auth_manager()
                success, message = auth_mgr.create_user(new_username, new_password)
                if success:
                    st.success(f"User '{new_username}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {message}")
            else:
                st.error("Please enter both username and password")
    
    st.markdown("---")
    
    # Display existing users
    st.subheader("📋 Current Users")
    
    if not users:
        st.info("No users found.")
        return
    
    # Create a table of users
    user_data = []
    for username, user_info in users.items():
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
        
        role = user_info.get('role', 'user')
        user_data.append({
            "Username": username,
            "Role": role,
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
                st.write(f"**Role:** {user['Role'].title()}")
                st.write(f"**Created:** {user['Created']}")
                st.write(f"**Last Login:** {user['Last Login']}")
            
            with col2:
                st.write(f"**Failed Attempts:** {user['Failed Attempts']}")
                st.write(f"**Status:** {user['Status']}")
            
            with col3:
                if user['Username'] != 'admin':  # Don't allow deleting admin
                    if st.button(f"🗑️ Delete User", key=f"delete_{user['Username']}"):
                        auth_mgr = get_auth_manager()
                        users = auth_mgr.load_users()
                        if user['Username'] in users:
                            del users[user['Username']]
                            auth_mgr.save_users(users)
                            st.success(f"User '{user['Username']}' deleted successfully!")
                            st.rerun()
                
                # Reset login attempts
                if user['Failed Attempts'] > 0:
                    if st.button(f"🔄 Reset Attempts", key=f"reset_{user['Username']}"):
                        auth_mgr = get_auth_manager()
                        users = auth_mgr.load_users()
                        if user['Username'] in users:
                            users[user['Username']]['login_attempts'] = 0
                            users[user['Username']]['locked_until'] = None
                            auth_mgr.save_users(users)
                            st.success(f"Login attempts reset for '{user['Username']}'!")
                            st.rerun()
    
    # System statistics
    st.markdown("---")
    st.subheader("📊 System Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(users))
    
    with col2:
        active_users = len([u for u in users.values() if u.get('last_login', 0) > time.time() - 86400])  # Last 24 hours
        st.metric("Active (24h)", active_users)
    
    with col3:
        locked_users = len([u for u in users.values() if u.get('locked_until', 0) > time.time()])
        st.metric("Locked Users", locked_users)
    
    with col4:
        total_attempts = sum(u.get('login_attempts', 0) for u in users.values())
        st.metric("Failed Attempts", total_attempts)
    
    # Recent registrations
    st.markdown("---")
    st.subheader("🆕 Recent Registrations")
    
    recent_users = []
    for username, user_info in users.items():
        created_time = user_info.get('created_at', 0)
        if created_time > time.time() - 7 * 86400:  # Last 7 days
            recent_users.append((username, created_time))
    
    recent_users.sort(key=lambda x: x[1], reverse=True)
    
    if recent_users:
        for username, created_time in recent_users[:5]:  # Show last 5
            created_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(created_time))
            st.write(f"• **{username}** - {created_date}")
    else:
        st.info("No new registrations in the last 7 days")
    
    # Security settings
    st.markdown("---")
    st.subheader("🔒 Security Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auth_mgr = get_auth_manager()
        st.write(f"**Max Login Attempts:** {auth_mgr.max_login_attempts}")
        st.write(f"**Lockout Duration:** {auth_mgr.lockout_duration // 60} minutes")
    
    with col2:
        st.write(f"**Session Timeout:** {auth_mgr.session_timeout // 3600} hours")
        st.write(f"**Password Hashing:** PBKDF2 with Salt")

if __name__ == "__main__":
    # Check authentication
    auth_mgr = get_auth_manager()
    if not auth_mgr.require_auth():
        from auth import show_login_page
        show_login_page()
    else:
        show_user_management()
