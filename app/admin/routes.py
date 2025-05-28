from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from sqlalchemy import or_
from app.models import Farmer, GovtUser, Location, Crop
from app.admin.forms import RegisterGovtUserForm, RegisterLocationForm
from app.utils.decorators import admin_required, session_required
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@admin_required
@session_required
def dashboard():
    # Clear selected_option if coming from browser back/forward navigation
    if request.referrer and url_for('admin.dashboard') in request.referrer:
        session.pop('selected_option', None)

    # Clear selected_option if coming from external page
    if not request.referrer or url_for('farmer.dashboard') not in request.referrer:
        session.pop('selected_option', None)

    selected_option = request.args.get('option', session.get('selected_option'))
    session['selected_option'] = selected_option
    farmer_data = None
    farmers = None
    govt_users = None
    form1 = RegisterGovtUserForm()
    form2 = RegisterLocationForm()
    form = form1 if selected_option == 'register_govt' else form2 if selected_option == 'register_location' else None

    farmer_count = Farmer.query.count()
    govt_user_count = GovtUser.query.count()
    location_count = Location.query.count()
    crop_count = Crop.query.count()
    print(f"Farmer Count: {farmer_count}, Govt User Count: {govt_user_count}, Location Count: {location_count}, Crop Count: {crop_count}")

    if request.method == 'POST':
        if 'option' in request.form:
            selected_option = request.form['option']
            session['selected_option'] = selected_option
            return redirect(url_for('admin.dashboard', option=selected_option))

        if 'register_govt' in request.form and selected_option == 'register_govt':
            form = RegisterGovtUserForm()
            if form.validate_on_submit():
                if GovtUser.query.filter_by(id=form.id.data).first():
                    flash('Government user ID already exists', 'error')
                else:
                    # Check if location exists
                    location = Location.query.get(form.location_id.data)
                    if not location:
                        flash('Location ID does not exist', 'error')
                    else:
                        phone = form.ph_no.data
                        if phone.startswith('0') and len(phone) == 11:
                            phone = phone[1:]
                        if not phone.isdigit() and len(phone) != 13:
                            flash('Invalid phone number', 'error')
                            phone = None
                        elif phone.startswith('+91') and len(phone) != 13:
                            flash('Phone number must be in +91XXXXXXXXXX format', 'error')
                            phone = None
                        elif len(phone) == 10 and not phone.startswith('+91'):
                            phone = '+91' + phone
                        new_govt_user = GovtUser(
                            id=form.id.data,
                            name=form.name.data,
                            phone=phone,
                            email=form.email.data,
                            password=form.password.data,
                            location_id=form.location_id.data,
                            type='govt_user'  # Set type automatically
                        )
                        db.session.add(new_govt_user)
                        db.session.commit()
                        flash('Government user registered successfully', 'success')
                        return redirect(url_for('admin.dashboard'))

        elif 'register_location' in request.form and selected_option == 'register_location':
            form = RegisterLocationForm()
            if form.validate_on_submit():
                if Location.query.filter_by(id=form.id.data).first():
                    flash('Location ID already exists', 'error')
                else:
                    new_location = Location(
                        id=form.id.data,
                        name=form.name.data,
                        state=form.state.data,
                        country='India'  # Default country
                    )
                    db.session.add(new_location)
                    db.session.commit()
                    flash('Location registered successfully', 'success')
                    return redirect(url_for('admin.dashboard'))
            else:
                flash('Please correct the errors in the form', 'error')

        elif 'farmer_id' in request.form and selected_option == 'view_farmer':
            farmer_id = request.form['farmer_id']
            farmer_data = Farmer.query.filter_by(id=farmer_id).first()
            if not farmer_data:
                flash('Farmer not found', 'error')
                
        elif 'go_back' in request.form:
            session.pop('selected_option', None)
            return redirect(url_for('admin.dashboard'))

    # Handle GET requests (search/filter/sort)
    if request.method == 'GET':
        if selected_option in ['view_farmers', 'view_govt_users']:
            search_query = request.args.get('search', '').strip()
            filter_option = request.args.get('filter', '')
            sort_option = request.args.get('sort', 'id_asc')

            if selected_option == 'view_farmers':
                farmers_query = Farmer.query
                
                if search_query:
                    farmers_query = farmers_query.filter(
                        or_(
                            Farmer.name.like(f'%{search_query}%'),
                            Farmer.id.ilike(f'%{search_query}%'),
                            Farmer.location.has(Location.name.ilike(f'%{search_query}%')),
                            Farmer.current_crop.has(Crop.name.ilike(f'%{search_query}%'))
                        )
                    )
                
                if filter_option == 'complete':
                    farmers_query = farmers_query.filter(Farmer.soil_type.isnot(None))
                elif filter_option == 'incomplete':
                    farmers_query = farmers_query.filter(Farmer.soil_type.is_(None))
                
                if sort_option == 'id_asc':
                    farmers_query = farmers_query.order_by(Farmer.id.asc())
                elif sort_option == 'id_desc':
                    farmers_query = farmers_query.order_by(Farmer.id.desc())
                elif sort_option == 'location_asc':
                    farmers_query = farmers_query.join(Location).order_by(Location.name.asc())
                elif sort_option == 'location_desc':
                    farmers_query = farmers_query.join(Location).order_by(Location.name.desc())
                elif sort_option == 'crop_asc':
                    farmers_query = farmers_query.join(Crop, Farmer.current_crop_id == Crop.id).order_by(Crop.name.asc())
                elif sort_option == 'crop_desc':
                    farmers_query = farmers_query.join(Crop, Farmer.current_crop_id == Crop.id).order_by(Crop.name.desc())
                
                farmers = farmers_query.all()

            elif selected_option == 'view_govt_users':
                govt_users_query = GovtUser.query
            
                if search_query:
                    govt_users_query = govt_users_query.filter(
                        or_(
                            GovtUser.id.ilike(f'%{search_query}%'),
                            GovtUser.name.ilike(f'%{search_query}%'),
                            GovtUser.location.has(Location.name.ilike(f'%{search_query}%'))
                    )
                )
                
                if sort_option == 'id_asc':
                    govt_users_query = govt_users_query.order_by(GovtUser.id.asc())
                elif sort_option == 'id_desc':
                    govt_users_query = govt_users_query.order_by(GovtUser.id.desc())
                elif sort_option == 'location_asc':
                    govt_users_query = govt_users_query.join(Location).order_by(Location.name.asc())
                elif sort_option == 'location_desc':
                    govt_users_query = govt_users_query.join(Location).order_by(Location.name.desc())
                
                govt_users = govt_users_query.all()

        # Load default data if no search/filter applied
        if selected_option == 'view_farmers' and farmers is None:
            farmers = Farmer.query.order_by(Farmer.id.asc()).all()
        elif selected_option == 'view_govt_users' and govt_users is None:
            govt_users = GovtUser.query.order_by(GovtUser.id.asc()).all()

    return render_template(
        'admin/dashboard.html',
        farmer_data=farmer_data,
        selected_option=selected_option,
        farmers=farmers,
        govt_users=govt_users,
        form=form,
        farmer_count=farmer_count,
        govt_user_count=govt_user_count,
        location_count=location_count,
        crop_count=crop_count,
        search_query=request.args.get('search', ''),
        current_filter=request.args.get('filter', ''),
        current_sort=request.args.get('sort', 'id_asc')
    )

@admin_bp.route('/edit_farmer/<farmer_id>', methods=['GET', 'POST'])
@admin_required
def edit_farmer(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    
    if request.method == 'POST':
        phone = request.form.get('ph_no', farmer.ph_no)
        if phone.startswith('0') and len(phone) == 11:
            phone = phone[1:]
        if not phone.isdigit() and len(phone) != 13:
            flash('Invalid phone number', 'error')
            phone = None
        elif phone.startswith('+91') and len(phone) != 13:
            flash('Phone number must be in +91XXXXXXXXXX format', 'error')
            phone = None
        elif len(phone) ==10 and not phone.startswith('+91'):
            phone = '+91' + phone
        farmer.name = request.form.get('name', farmer.name)
        farmer.phone = phone
        farmer.email = request.form.get('email', farmer.email)
        farmer.soil_type = request.form.get('soil_type', farmer.soil_type)
        farmer.ph_level = request.form.get('ph_level', farmer.ph_level)
        farmer.nitrogen = request.form.get('nitrogen', farmer.nitrogen)
        farmer.phosphorus = request.form.get('phosphorus', farmer.phosphorus)
        farmer.potassium = request.form.get('potassium', farmer.potassium)
        farmer.land_area = request.form.get('land_area', farmer.land_area)
        
        db.session.commit()
        flash('Farmer details updated successfully', 'success')
        return redirect(url_for('admin.dashboard', option='view_farmers'))

    return render_template('admin/edit_farmer.html', farmer=farmer)

@admin_bp.route('/edit_govt_user/<govt_user_id>', methods=['GET', 'POST'])
@admin_required
def edit_govt_user(govt_user_id):
    govt_user = GovtUser.query.get_or_404(govt_user_id)
    
    if request.method == 'POST':
        govt_user.name = request.form.get('name', govt_user.name)
        
        new_password = request.form.get('password')
        if new_password:
            govt_user.password = new_password
            
        phone = request.form.get('phone', govt_user.phone)
        if phone.startswith('0') and len(phone) == 11:
            phone = phone[1:]
        if not phone.isdigit() and len(phone) != 13:
            flash('Invalid phone number', 'error')
            phone = None
        elif phone.startswith('+91') and len(phone) != 13:
            flash('Phone number must be in +91XXXXXXXXXX format', 'error')
            phone = None
        elif len(phone) == 10 and not phone.startswith('+91'):
            phone = '+91' + phone
        govt_user.phone = phone
        govt_user.email = request.form.get('email', govt_user.email)
        govt_user.location_id = request.form.get('location_id', govt_user.location_id)
        
        db.session.commit()
        flash('Government user updated successfully', 'success')
        return redirect(url_for('admin.dashboard', option='view_govt_users'))
    
    return render_template('admin/edit_govt_user.html', govt_user=govt_user)

@admin_bp.route('/remove_farmer', methods=['POST'])
@admin_required
def remove_farmer():
    farmer_id = request.form.get('farmer_id')
    farmer = Farmer.query.filter_by(id=farmer_id).first()
    
    if not farmer:
        flash('Farmer not found', 'error')
    else:
        db.session.delete(farmer)
        db.session.commit()
        flash(f'Farmer {farmer_id} removed successfully', 'success')

    return redirect(url_for('admin.dashboard', option='view_farmers'))


@admin_bp.route('/remove_govt_user', methods=['POST'])
@admin_required
def remove_govt_user():
    govt_user_id = request.form.get('govt_user_id')
    govt_user = GovtUser.query.filter_by(id=govt_user_id).first()
    if govt_user:
        db.session.delete(govt_user)
        db.session.commit()
        flash(f'Government user {govt_user_id} removed successfully', 'success')
    else:
        flash('Government user not found', 'error')

    return redirect(url_for('admin.dashboard'))