from functools import wraps
from flask import redirect, url_for, flash, session
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

def farmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'farmer':
            flash('Farmer reqired', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def govt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'govt':
            flash('Govenment User Required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin':
            flash('Admin Required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session:
            flash('Your session has expired. Please log in again.', 'error')
            return redirect(url_for('auth.login'))
            
        # Check session expiration (30 minutes inactivity)
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(str(session['last_activity']))
            # Ensure both are timezone-aware
            now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
            if (now_ist - last_activity).total_seconds() > 10*60:  # 10 minutes for testing, change to 30*60 for production
                session.clear()
                flash('Session timed out due to inactivity', 'error')
                return redirect(url_for('auth.login'))
        
        # Update last activity time on each request
        session['last_activity'] = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        return f(*args, **kwargs)
    return decorated_function