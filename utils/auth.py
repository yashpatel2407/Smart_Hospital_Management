"""
Authentication Utilities - Smart Care Hospital Management System

Provides decorators for route protection:
- role_required: Ensures user has specific role(s) (internally checks login)

SESSION DICTIONARY USAGE:
Flask session is a dictionary data structure storing:
    session = {
        'user_id': int,       # Database user ID
        'full_name': str,     # Display name
        'email': str,         # User email
        'role': str,          # 'admin' | 'doctor' | 'patient'
        'profile_image': str  # Profile picture path
    }
This dictionary is checked on every protected route request.
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def role_required(*roles):
    """
    Decorator: Requires user to have one of the specified roles.
    Checks 'role' key in session dictionary against allowed roles.

    Usage:
        @app.route('/admin/dashboard')
        @role_required('admin')
        def admin_dashboard():
            ...

        @app.route('/staff-only')
        @role_required('admin', 'doctor')
        def staff_page():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check login first
            if 'user_id' not in session:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            # Check role from session dictionary
            user_role = session.get('role', '')
            if user_role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                # Redirect to their own dashboard based on role
                if user_role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user_role == 'doctor':
                    return redirect(url_for('doctor.dashboard'))
                elif user_role == 'patient':
                    return redirect(url_for('patient.dashboard'))
                else:
                    return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
