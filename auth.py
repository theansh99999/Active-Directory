"""
Authentication utilities and decorators.
"""
from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role for access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        if current_user.role != 'Admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def login_required_with_message(f):
    """Decorator to require login with custom message."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_client_ip():
    """Get client IP address for audit logging."""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']