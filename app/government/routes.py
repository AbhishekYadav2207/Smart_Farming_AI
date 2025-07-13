from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import Farmer, GovtUser, Crop, Location, Recommendation, DiseaseReport
from app.ai_services import crop_recommendation
from app.utils.decorators import govt_required, session_required
from app import db
from sqlalchemy import or_, func
from app.utils.helpers import update_farmer_counts, update_govt_user_counts
from app.utils.validation import validate_and_format_phone

govt_bp = Blueprint('government', __name__)

def normalize_name(name):
    return name.replace(" ", "").lower()

@govt_bp.route('/govt_dashboard', methods=['GET', 'POST'])
@govt_required
@session_required
def dashboard():
    # Clear selected_option if coming from browser back/forward navigation
    if request.referrer and url_for('government.dashboard') in request.referrer:
        session.pop('selected_option', None)

    # Clear selected_option if coming from external page
    if not request.referrer or url_for('farmer.dashboard') not in request.referrer:
        session.pop('selected_option', None)

    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    if not govt_user:
        flash('Government user not found', 'error')
        return redirect(url_for('auth.login'))
    
    update_govt_user_counts(govt_user)
    
    selected_option = request.args.get('option', session.get('selected_option'))
    session['selected_option'] = selected_option
    farmer_data = None
    crop_options = None
    farmer_details_incomplete = False
    farmers = None
    location = Location.query.get(govt_user.location_id)
    farmer_count = govt_user.no_farmers_assigned or 0
    active_farmer_count = govt_user.no_farmers_active or 0

    if request.method == 'POST':
        if 'option' in request.form:
            selected_option = request.form['option']
            session['selected_option'] = selected_option
            return redirect(url_for('government.dashboard', option=selected_option))
        
        if 'farmer_id' in request.form and selected_option == 'analyze':
            farmer_id = request.form['farmer_id']
            farmer_data = Farmer.query.filter_by(id=farmer_id, location=govt_user.location).first()
            
            if not farmer_data:
                flash('Farmer not found in your area', 'error')
            else:
                required_fields = ['soil_type', 'ph_level', 'nitrogen', 'phosphorus', 'potassium']
                farmer_details_incomplete = any(not getattr(farmer_data, field) for field in required_fields)
                
                if not farmer_details_incomplete:
                    analysis_result = crop_recommendation.analyze(
                        farmer_data.soil_type,
                        farmer_data.ph_level,
                        location.annual_rainfall,
                        location.average_temperature,
                        location.name,
                        farmer_data.nitrogen,
                        farmer_data.phosphorus,
                        farmer_data.potassium,
                        farmer_data.land_area,
                        farmer_data.current_crop.name if farmer_data.current_crop else None
                    )
                    if analysis_result:
                        all_crops = []
                        if Crop.query.count() == 0:
                            crop_id = 0
                        else:
                            crop_id = Crop.query.order_by(Crop.id.desc()).first().id
                        existing_crops = {normalize_name(crop.name): crop for crop in Crop.query.all()}  # normalize db names once

                        for crop_raw in [crop.strip() for crop in analysis_result.split(',') if crop.strip()]:
                            normalized_input = normalize_name(crop_raw)
                            if normalized_input in existing_crops:
                                crop = existing_crops[normalized_input]
                            else:
                                crop_id += 1
                                formatted_name = crop_raw.replace("_", " ").title()  # title-case with proper spacing
                                new_crop = Crop(name=formatted_name, id=crop_id)
                                db.session.add(new_crop)
                                db.session.commit()
                                existing_crops[normalized_input] = new_crop
                            all_crops.append(existing_crops[normalized_input].name)

                        current_crop = farmer_data.current_crop
                        if current_crop and current_crop.name in all_crops:
                            all_crops.remove(current_crop.name)
                            
                        all_crops.append('__NONE__')  # Just the value, no tuple
                        crop_options = all_crops

        elif 'save_crop' in request.form:
            farmer_id = request.form['farmer_id']
            selected_crop = request.form['selected_crop']
            
            if selected_crop == '__NONE__':
                selected_crop = None
                selected_crop_id = None
            else:
                crop = Crop.query.filter_by(name=selected_crop).first()
                selected_crop_id = crop.id if crop else None
            
            farmer = Farmer.query.filter_by(id=farmer_id, location=govt_user.location).first()
            if not farmer:
                flash('Farmer not found', 'error')
                return redirect(url_for('government.dashboard', option='analyze'))
            
            # Update farmer counts
            was_active = farmer.current_crop_id is not None
            will_be_active = selected_crop_id is not None
            
            if farmer.current_crop_id != selected_crop_id:
                farmer.previous_crop = farmer.current_crop
                farmer.current_crop_id = selected_crop_id if selected_crop_id else None
                farmer.current_crop = Crop.query.filter_by(id=selected_crop_id).first() if selected_crop_id else None
                farmer.fertilizer_needed = None
                # Delete previous fertilizer and disease reports for this farmer
                Recommendation.query.filter_by(farmer_id=farmer.id).delete()
                DiseaseReport.query.filter_by(farmer_id=farmer.id).delete()
                db.session.flush()  # Ensure deletions are staged before counting

                # Optionally, update any related counts if you track them elsewhere
                db.session.commit()
                
                # Update counts if activity status changed
                if was_active != will_be_active:
                    # Ensure no_farmers_active is not None
                    if govt_user.no_farmers_active is None:
                        govt_user.no_farmers_active = 0

                    if will_be_active:
                        govt_user.no_farmers_active += 1
                    else:
                        govt_user.no_farmers_active = max(0, govt_user.no_farmers_active - 1)
                        # Remove farmer's data if they become inactive
                        DiseaseReport.query.filter_by(farmer_id=farmer.id).delete()
                        Recommendation.query.filter_by(farmer_id=farmer.id).delete()

                    db.session.commit()
                
                flash('Crop updated successfully', 'success')
            else:
                flash('No changes made', 'info')
            
            return redirect(url_for('government.dashboard', option='view_farmers'))

        elif 'register_farmer' in request.form and selected_option == 'register_farmer':
            new_farmer_name = request.form['new_farmer_name']
            new_farmer_id = request.form['new_farmer_id']
            new_farmer_phone = request.form.get('new_farmer_phone')
            new_farmer_email = request.form.get('new_farmer_email')
            area_of_land = request.form.get('area_of_land')
            
            if Farmer.query.filter_by(id=new_farmer_id).first():
                flash('Farmer ID already exists', 'error')
            else:
                phone = new_farmer_phone
                phone,error = validate_and_format_phone(phone)
                if not phone:
                    flash(error, 'error')
                    phone = None               
                
                new_farmer = Farmer(
                    name=new_farmer_name,
                    id=new_farmer_id,
                    phone=phone,
                    email=new_farmer_email,
                    location_id=govt_user.location_id,
                    location=govt_user.location,
                    land_area=area_of_land if area_of_land else None,
                    type='farmer'  # Set type automatically
                )
                db.session.add(new_farmer)
                
                # Update farmer count
                govt_user.no_farmers_assigned = (govt_user.no_farmers_assigned or 0) + 1
                location.no_of_farmers = (location.no_of_farmers or 0) + 1
                db.session.commit()

                update_farmer_counts(govt_user.location_id)
                
                flash(f'Farmer {new_farmer_id} registered successfully', 'success')
                return redirect(url_for('government.dashboard', option='view_farmers'))
        
        elif 'save_area_details' in request.form:
    # Update location details instead of govt_user details
            if location:
                location.annual_rainfall = request.form['annual_rainfall']
                location.average_temperature = request.form['average_temperature']
                
                # # Update all farmers in this location
                # Farmer.query.filter_by(location_id=location.id).update({
                #     'annual_rainfall': location.annual_rainfall,
                #     'average_temperature': location.average_temperature
                # })
                
                db.session.commit()
                flash('Area details updated successfully', 'success')
            else:
                flash('Location not found', 'error')
            return redirect(url_for('government.dashboard'))
        
        elif 'go_back' in request.form:
            session.pop('selected_option', None)
            return redirect(url_for('government.dashboard'))

    if request.method == 'GET' and selected_option == 'view_farmers':
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        
        farmers_query = Farmer.query.filter_by(location=govt_user.location)
        
        if search_query:
            farmers_query = farmers_query.filter(
                or_(
                    Farmer.name.like(f'%{search_query}%'),
                    Farmer.id.ilike(f'%{search_query}%'),
                    Farmer.phone.ilike(f'%{search_query}%'),
                    Farmer.current_crop.name.ilike(f'%{search_query}%')
                )
            )
        
        if status_filter == 'active':
            farmers_query = farmers_query.filter(
                Farmer.soil_type.isnot(None),
                Farmer.current_crop_id.isnot(None)
            )
        elif status_filter == 'incomplete':
            farmers_query = farmers_query.filter(
                or_(
                    Farmer.soil_type.is_(None),
                    Farmer.current_crop.is_(None)
                )
            )
        
        farmers = farmers_query.order_by(Farmer.id.asc()).all()

    return render_template(
        'government/dashboard.html',
        govt_user=govt_user,
        selected_option=selected_option,
        farmer_data=farmer_data,
        crop_options=crop_options,
        farmer_details_incomplete=farmer_details_incomplete,
        farmers=farmers,
        farmer_count=farmer_count,
        active_farmer_count=active_farmer_count,
        search_query=request.args.get('search', ''),
        current_status=request.args.get('status', '')
    )

@govt_bp.route('/government/edit_farmer/<farmer_id>', methods=['GET', 'POST'])
@govt_required
def edit_farmer(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    
    if farmer.location != govt_user.location:
        flash('You can only edit farmers in your area', 'error')
        return redirect(url_for('government.dashboard'))

    if request.method == 'POST':
        phone = request.form.get('phone', farmer.phone)
        phone = validate_and_format_phone(phone)
        if not phone:
            flash('Invalid phone number format', 'error')
            phone = None
        
        farmer.name = request.form.get('farmer_name', farmer.name)
        farmer.phone = phone
        farmer.email = request.form.get('email', farmer.email)
        farmer.soil_type = request.form.get('soil_type')
        farmer.ph_level = request.form.get('ph_level')
        farmer.area_of_land = request.form.get('area_of_land')
        
        db.session.commit()
        flash('Farmer details updated successfully', 'success')
        return redirect(url_for('government.dashboard', option='view_farmers'))

    return render_template('admin/edit_farmer.html', farmer=farmer)

@govt_bp.route('/remove_farmer', methods=['POST'])
@govt_required
def remove_farmer():
    farmer_id = request.form.get('farmer_id')
    farmer = Farmer.query.filter_by(id=farmer_id).first()
    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    
    if not farmer:
        flash('Farmer not found', 'error')
    elif farmer.location != govt_user.location:
        flash('You can only remove farmers in your area', 'error')
    else:
        db.session.delete(farmer)
        # Safely decrement the count
        if govt_user.no_farmers_assigned:
            govt_user.no_farmers_assigned = max(0, govt_user.no_farmers_assigned - 1)

        if farmer.current_crop_id:
            crop = Crop.query.get(farmer.current_crop_id)
            if crop:
                crop.no_of_farmers = max(0, crop.no_of_farmers - 1)
            govt_user.no_farmers_active = max(0, govt_user.no_farmers_active - 1)

        if farmer.location.no_of_farmers:
            farmer.location.no_of_farmers = max(0, farmer.location.no_of_farmers - 1)

        db.session.commit()
        flash(f'Farmer {farmer_id} removed successfully', 'success')

    return redirect(url_for('government.dashboard', option='view_farmers'))

@govt_bp.route('government/save_crop', methods=['POST'])
@govt_required
def save_crop():
    farmer_id = request.form.get('farmer_id')
    selected_crop = request.form.get('selected_crop')
    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    
    # Get crop ID (None if __NONE__ is selected)
    selected_crop_id = None
    if selected_crop and selected_crop != '__NONE__':
        crop = Crop.query.filter_by(name=selected_crop).first()
        if crop:
            selected_crop_id = crop.id
    
    farmer = Farmer.query.filter_by(id=farmer_id, location=govt_user.location).first()
    if not farmer:
        flash('Farmer not found', 'error')
        return redirect(url_for('government.dashboard', option='analyze'))
    
    # Track previous state
    previous_crop_id = farmer.current_crop_id
    was_active = previous_crop_id is not None
    will_be_active = selected_crop_id is not None
    
    if farmer.current_crop_id != selected_crop_id:
        # Update previous crop's count if it exists
        if previous_crop_id:
            previous_crop = Crop.query.get(previous_crop_id)
            if previous_crop:
                # Count farmers for previous crop excluding the current farmer
                previous_crop.no_of_farmers = Farmer.query.filter(
                    Farmer.current_crop_id == previous_crop_id,
                    Farmer.id != farmer.id
                ).count()
                if previous_crop.no_of_farmers <= 0:
                    previous_crop.being_grown = False
                    previous_crop.no_of_farmers = 0
        
        # Update farmer's crop first
        farmer.previous_crop_id = previous_crop_id
        farmer.current_crop_id = selected_crop_id
        farmer.fertilizer_needed = None
        
        # Delete related records
        DiseaseReport.query.filter_by(farmer_id=farmer.id).delete()
        Recommendation.query.filter_by(farmer_id=farmer.id).delete()
        
        # Update new crop's count if it exists
        if selected_crop_id:
            new_crop = Crop.query.get(selected_crop_id)
            # Count farmers for new crop including this farmer
            new_crop.no_of_farmers = Farmer.query.filter_by(
                current_crop_id=selected_crop_id
            ).count()
            new_crop.being_grown = new_crop.no_of_farmers > 0
        
        db.session.commit()

        update_farmer_counts(farmer.location_id)
        
        # Update government user's active farmer count
        current_active_count = Farmer.query.filter(
            Farmer.location_id == govt_user.location_id,
            Farmer.current_crop_id.isnot(None)
        ).count()
        govt_user.no_farmers_active = current_active_count
        db.session.commit()
        
        flash('Crop updated successfully', 'success')
    else:
        flash('No changes made', 'info')
    
    return redirect(url_for('government.dashboard', option='view_farmers'))

@govt_bp.route('/get_user_details', methods=['GET'])
@govt_required
def get_user_details():
    user_type = 'farmer'
    user_id = request.args.get('user_id')
    
    if user_type == 'farmer':
        user = Farmer.query.get_or_404(user_id)
        return render_template('admin/_farmer_details.html', farmer=user)
    else:
        return "Invalid user type", 400