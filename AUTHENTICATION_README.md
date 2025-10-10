# Polo GGB Research Assistant - Authentication System

## 🔐 Overview

This application now includes a professional authentication system designed for enterprise use. The system provides secure user management, session handling, and access control for the Polo GGB Research Assistant.

## 🏢 Company Information

**Polo d'Innovazione di Genomica, Genetica e Biologia (Polo GGB)**
- Website: https://www.pologgb.com/
- Focus: Genomics, Genetics, Biology
- Services: Research and Services that create value

## 🚀 Features

### Security Features
- **Password Hashing**: SHA-256 with salt for secure password storage
- **Session Management**: 1-hour session timeout with automatic logout
- **Login Attempt Tracking**: Maximum 5 failed attempts before account lockout
- **Account Lockout**: 5-minute lockout period after failed attempts
- **Session Validation**: Continuous session validation for security

### User Management
- **Admin Panel**: Complete user management interface
- **User Registration**: Self-service user registration with password validation
- **User Creation**: Secure user account creation (admin + self-registration)
- **User Deletion**: Remove users (except admin)
- **Login Monitoring**: Track failed login attempts and reset locks
- **System Statistics**: Monitor active users, registrations, and security metrics

### Professional UI
- **Polo GGB Branding**: Company logo and colors
- **Responsive Design**: Professional login interface
- **Error Handling**: Clear error messages and feedback
- **Session Indicators**: User information and logout functionality

## 🔑 Default Credentials

**Admin Account (Created Automatically)**
- Username: `admin`
- Password: `pologgb2024`

⚠️ **Important**: Change the default admin password immediately after first login!

## 📁 File Structure

```
app/
├── auth.py                 # Authentication system
├── user_management.py      # Admin user management interface
├── main.py                 # Main application (with auth integration)
└── polo-ggb-logo.png       # Company logo
```

## 🛠️ Usage

### For Users
1. **Registration**: Create new account with username and password
2. **Login**: Enter username and password
3. **Session**: Automatically logged out after 1 hour of inactivity
4. **Logout**: Click the logout button in the sidebar

### For Administrators
1. **Login**: Use admin credentials
2. **User Management**: Click "👥 User Management" in sidebar
3. **Create Users**: Add new users with secure passwords
4. **Monitor**: View user activity, registrations, and security statistics
5. **Manage**: Reset failed attempts or delete users
6. **Track**: Monitor recent registrations and user growth

## 🔒 Security Implementation

### Password Security
- **Hashing**: SHA-256 with random salt
- **Storage**: Passwords never stored in plain text
- **Validation**: Secure password verification

### Session Security
- **Tokens**: Unique session tokens for each login
- **Timeout**: Automatic session expiration
- **Validation**: Continuous session validation
- **Logout**: Secure session termination

### Access Control
- **Authentication**: Required for all application access
- **Authorization**: Role-based access (admin vs regular users)
- **Protection**: Failed attempt tracking and lockout

## 📊 User Data Storage

User data is stored in `users.json` with the following structure:

```json
{
  "username": {
    "password_hash": "hashed_password",
    "salt": "random_salt",
    "created_at": 1234567890,
    "last_login": 1234567890,
    "login_attempts": 0,
    "locked_until": null
  }
}
```

## 🚨 Security Best Practices

1. **Change Default Password**: Immediately change admin password
2. **Strong Passwords**: Use complex passwords for all users
3. **Regular Monitoring**: Check user activity and failed attempts
4. **Access Control**: Limit admin access to trusted personnel
5. **Session Management**: Logout when finished using the application

## 🔧 Configuration

### Security Settings (in auth.py)
- `session_timeout`: 3600 seconds (1 hour)
- `max_login_attempts`: 5 attempts
- `lockout_duration`: 300 seconds (5 minutes)

### Customization
- Logo: Replace `polo-ggb-logo.png` with your company logo
- Colors: Modify CSS in `auth.py` for brand colors
- Timeouts: Adjust security settings as needed

## 📞 Support

For technical support or questions about the authentication system, contact the Polo GGB development team.

---

**© 2024 Polo GGB - Research and Services that create value**
