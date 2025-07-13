from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from app.models import Farmer, GovtUser, Location
from app.auth.forms import LoginForm, RegisterForm
from datetime import datetime
from zoneinfo import ZoneInfo
from app import db

auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)

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
                    session.permanent = True
                    
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
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    return response

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'GET':
        # Initialize empty location choices
        form.location_id.choices = [('', 'Enter pincode first')]
    
    if request.method == 'POST' and 'pincode' in request.form:
        # Handle pincode change
        pincode = request.form['pincode']
        if len(pincode) == 6:
            locations = Location.query.filter_by(pincode=int(pincode)).all()
            form.location_id.choices = [(loc.id, f"{loc.name}, {loc.district}") for loc in locations] or [('', 'No locations found')]

    if form.validate_on_submit():
        try:
            # Create new farmer
            farmer = Farmer(
                id=form.user_id.data,
                name=form.name.data,
                phone=form.phone.data,
                email=form.email.data or None,
                location_id=form.location_id.data,
                land_area=str(form.land_area.data) if form.land_area.data else None,
                created_at=datetime.now(ZoneInfo("Asia/Kolkata"))
            )
            location = Location.query.filter_by(id = int(form.location_id.data)).first()
            if not location:
                flash('Invalid location selected', 'error')
                return render_template('auth/register.html', form=form)
            # govt_user.no_farmers_assigned = (govt_user.no_farmers_assigned or 0) + 1
            location.no_of_farmers = (location.no_of_farmers or 0) + 1
            db.session.add(farmer)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)


@api_bp.route('/locations')
def get_locations():
    pincode = request.args.get('pincode')
    if not pincode or not pincode.isdigit() or len(pincode) != 6:
        return jsonify({'error': 'Invalid pincode format'}), 400
    
    locations = Location.query.filter_by(pincode=int(pincode)).all()
    return jsonify({
        'locations': [{
            'id': loc.id,
            'name': loc.name,
            'district': loc.district,
            'state': loc.state
        } for loc in locations]
    })