# Active Directory Clone - Implementation Plan

## Core Application Files
1. **app.py** - Main Flask application with routes and configuration
2. **models.py** - SQLAlchemy database models (User, Group, Computer, OU, AuditLog, UserGroup)
3. **forms.py** - WTForms for form handling and validation
4. **auth.py** - Authentication utilities and decorators
5. **config.py** - Application configuration settings
6. **requirements.txt** - Python dependencies
7. **init_db.py** - Database initialization with demo data

## Template Files (Jinja2 + Bootstrap 5)
1. **templates/base.html** - Base template with dark mode, sidebar navigation
2. **templates/login.html** - Login page
3. **templates/dashboard.html** - Main dashboard
4. **templates/users.html** - User management page
5. **templates/groups.html** - Group management page
6. **templates/computers.html** - Computer management page
7. **templates/ous.html** - Organizational Units page
8. **templates/logs.html** - Audit logs page

## Static Files
1. **static/css/custom.css** - Custom CSS for dark mode and styling
2. **static/js/app.js** - JavaScript for modals, search, and theme toggle

## Key Features Implementation:
- User Management: CRUD operations with role assignment
- Group Management: Create groups, assign users, manage permissions
- Computer Management: Add/edit/delete computers with status control
- OU Management: Nested hierarchy for departments
- Authentication: Flask-Login with session management
- Policy Enforcement: Password rules, account lockout
- Audit Logging: Track all system actions
- Dark Mode UI: Bootstrap 5 with custom dark theme

## Database Schema:
- Users (id, username, email, password_hash, role, is_active, failed_attempts, locked_until)
- Groups (id, name, description, permissions)
- Computers (id, name, description, status, ou_id)
- OrganizationalUnits (id, name, description, parent_id)
- AuditLogs (id, user_id, action, target, timestamp)
- UserGroups (user_id, group_id) - Many-to-many relationship

Total Files: ~15 files
Complexity: Medium - Flask web application with authentication and CRUD operations