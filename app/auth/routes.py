from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import Farmer, GovtUser
from app.auth.forms import LoginForm
from datetime import datetime
from zoneinfo import ZoneInfo
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' or form.validate_on_submit():
        if form.user_type.data == 'govt':
            govt_user = GovtUser.query.filter_by(id=form.id.data).first()
            if govt_user:
                if govt_user.verify_password(form.password.data):
                    session['user_type'] = 'govt'
                    session['govt_id'] = govt_user.id
                    session.permanent = True  # Enable permanent sessions
                    
                    # Update last login time
                    session['last_activity'] = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
                    govt_user.last_login = datetime.now(ZoneInfo("Asia/Kolkata"))
                    db.session.commit()
                    return redirect(url_for('government.dashboard'))
                else:
                    flash('Invalid password', 'error')
            else:
                flash('Invalid Username', 'error')
        elif form.user_type.data == 'farmer':
            farmer = Farmer.query.filter_by(id=form.id.data).first()
            if farmer:
                session['user_type'] = 'farmer'
                session['farmer_id'] = farmer.id
                session.permanent = True  # Enable permanent sessions # Track activity
                
                # Update last login time
                session['last_activity'] = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
                farmer.last_login = datetime.now(ZoneInfo("Asia/Kolkata"))
                db.session.commit()
                return redirect(url_for('farmer.dashboard'))
            else:
                flash('Invalid credentials', 'error')
        elif form.user_type.data == 'admin':
            from config import Config
            from werkzeug.security import check_password_hash
            if (form.id.data == Config.ADMIN_USERNAME):
                if (Config.ADMIN_PASSWORD_HASH and 
                check_password_hash(Config.ADMIN_PASSWORD_HASH, form.password.data)):
                    session['user_type'] = 'admin'
                    session.permanent = True  # Enable permanent sessions
                    session['last_activity'] = datetime.utcnow()  # Track activity
                    return redirect(url_for('admin.dashboard'))
                else:
                    flash('Invalid password', 'error')
            else:
                flash('Invalid Username', 'error')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    # Create redirect response with security headers
    response = redirect(url_for('auth.login'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.delete_cookie('remember_token')
    return response