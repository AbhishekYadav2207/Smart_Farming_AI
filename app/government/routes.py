# app/routes/govt_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from app.models import Farmer, GovtUser, Crop, Location, Recommendation, DiseaseReport
from app.ai_services import crop_recommendation
from app.utils.decorators import govt_required, session_required
from app import db
from sqlalchemy import or_, func, and_
from sqlalchemy.exc import SQLAlchemyError
from app.utils.helpers import update_farmer_counts, update_govt_user_counts
from app.utils.validation import validate_and_format_phone
import logging

govt_bp = Blueprint('government', __name__)
logger = logging.getLogger(__name__)

def normalize_name(name):
    """Safely normalize crop names"""
    if not name:
        return ""
    return name.replace(" ", "").lower()

def safe_float_conversion(value, default=None):
    """Safely convert to float with error handling"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

@govt_bp.route('/govt_dashboard', methods=['GET', 'POST'])
@govt_required
@session_required
def dashboard():
<<<<<<< HEAD
    try:
        # Clear selected_option if coming from browser back/forward navigation
        if request.referrer and url_for('government.dashboard') in request.referrer:
=======
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
                            
                        total_farmers = Farmer.query.filter_by(location_id=location.id).count() or 1  # avoid divide by zero
                        crop_opts = []
                        for crop_name in all_crops:
                            crop_obj = Crop.query.filter_by(name=crop_name).first()
                            if crop_obj:
                                farmers_growing = Farmer.query.filter_by(location_id=location.id, current_crop_id=crop_obj.id).count()
                                percentage = (farmers_growing / total_farmers) * 100
                                if percentage >= 40:
                                    crop_opts.append(f"{crop_name} ⚠️")
                                else:
                                    crop_opts.append(crop_name)
                            
                        crop_opts.append('__NONE__')  # Just the value, no tuple
                        crop_options = crop_opts

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
>>>>>>> f2acce8f400823c83627d4b473d40ee52deddfce
            session.pop('selected_option', None)

        # Clear selected_option if coming from external page
        if not request.referrer or url_for('farmer.dashboard') not in request.referrer:
            session.pop('selected_option', None)

        # Get government user safely
        govt_user = GovtUser.query.filter_by(id=session.get('govt_id')).first()
        if not govt_user:
            flash('Government user not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get all locations and location IDs under this pincode safely
        govt_locations = []
        govt_location_ids = []
        try:
            govt_locations = Location.query.filter_by(pincode=govt_user.pincode).all()
            govt_location_ids = [loc.id for loc in govt_locations]
        except SQLAlchemyError as e:
            logger.error(f"Error fetching locations: {e}")
            flash('Error loading location data', 'error')
        
        if not govt_locations:
            flash('No locations found for your pincode', 'error')
            return redirect(url_for('auth.login'))
        
        # Update counts safely
        total_farmers = 0
        active_farmers = 0
        try:
            total_farmers = Farmer.query.filter(Farmer.location_id.in_(govt_location_ids)).count()
            active_farmers = Farmer.query.filter(
                Farmer.location_id.in_(govt_location_ids),
                Farmer.current_crop_id.isnot(None)
            ).count()
            
            govt_user.no_farmers_assigned = total_farmers
            govt_user.no_farmers_active = active_farmers
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error updating counts: {e}")
            db.session.rollback()
        
        selected_option = request.args.get('option', session.get('selected_option'))
        session['selected_option'] = selected_option
        farmer_data = None
        crop_options = None
        farmer_details_incomplete = False
        farmers = None
        analysis_warning = None
        analysis_error = None
        crop_metadata = {}
        low_coverage_crops = []

        if request.method == 'POST':
            if 'option' in request.form:
                selected_option = request.form['option']
                session['selected_option'] = selected_option
                return redirect(url_for('government.dashboard', option=selected_option))
            
            if 'farmer_id' in request.form and selected_option == 'analyze':
                farmer_id = request.form['farmer_id']
                try:
                    # Check if farmer is in any location under this pincode
                    farmer_data = Farmer.query.filter(
                        Farmer.id == farmer_id,
                        Farmer.location_id.in_(govt_location_ids)
                    ).first()
                    
                    if not farmer_data:
                        flash('Farmer not found in your area', 'error')
                    else:
                        # Check if farmer has required details
                        required_fields = ['soil_type', 'ph_level', 'nitrogen', 'phosphorus', 'potassium']
                        farmer_details_incomplete = any(
                            not getattr(farmer_data, field) for field in required_fields
                            if getattr(farmer_data, field) is not None
                        )
                        
                        if not farmer_details_incomplete:
                            try:
                                # Use the farmer's specific location for analysis
                                location = farmer_data.location
                                
                                # Safely get all parameters with defaults
                                soil_type = farmer_data.soil_type or "Unknown"
                                ph_level = safe_float_conversion(farmer_data.ph_level, 7.0)
                                rainfall = safe_float_conversion(
                                    location.annual_rainfall if location else None, 
                                    1000.0
                                )
                                temperature = safe_float_conversion(
                                    location.average_temperature if location else None, 
                                    25.0
                                )
                                location_name = location.name if location else "Unknown"
                                state = location.state if location else "Unknown"
                                state = state.title()
                                crops_loc = Crop.query.filter(Crop.states.ilike(f"%{state}%")).all()
                                crops_pri = Crop.query.filter(Crop.prioritized_states.ilike(f"%{state}%")).all()
                                
                                nitrogen = safe_float_conversion(farmer_data.nitrogen, 0)
                                phosphorus = safe_float_conversion(farmer_data.phosphorus, 0)
                                potassium = safe_float_conversion(farmer_data.potassium, 0)
                                land_area = safe_float_conversion(farmer_data.land_area, 1.0)
                                
                                current_crop = farmer_data.current_crop.name if farmer_data.current_crop else None
                                
                                # Get crop recommendations
                                analysis_result = crop_recommendation.analyze(
                                    soil_type, ph_level, rainfall, temperature, 
                                    location_name, nitrogen, phosphorus, potassium, 
                                    land_area, current_crop, crops_loc, crops_pri
                                )
                                
                                if analysis_result:
                                    all_crops = []
                                    existing_crops = {}
                                    
                                    try:
                                        existing_crops = {normalize_name(crop.name): crop for crop in Crop.query.all()}
                                    except SQLAlchemyError:
                                        # If DB query fails, continue with empty dict
                                        pass
                                    
                                    for crop_raw in [crop.strip() for crop in analysis_result.split(',') if crop.strip()]:
                                        normalized_input = normalize_name(crop_raw)
                                        if normalized_input in existing_crops:
                                            crop = existing_crops[normalized_input]
                                        else:
                                            try:
                                                # Create new crop with basic metadata
                                                formatted_name = crop_raw.replace("_", " ").title()
                                                new_crop = Crop(
                                                    name=formatted_name,
                                                    being_grown=False,
                                                    no_of_farmers=0,
                                                    states=[state],
                                                    seasons=["Whole Year"],
                                                    priority=0,
                                                    prioritized_states=[state],
                                                    prioritized_seasons=["Whole Year"],
                                                    total_production=0,
                                                    avg_area=0,
                                                    avg_yield=0
                                                )
                                                db.session.add(new_crop)
                                                db.session.flush()
                                                db.session.commit()
                                                existing_crops[normalized_input] = new_crop
                                            except SQLAlchemyError as e:
                                                logger.error(f"Error creating crop: {e}")
                                                continue
                                        
                                        all_crops.append(existing_crops[normalized_input].name)
                                    
                                    # Remove current crop if present
                                    if current_crop and current_crop in all_crops:
                                        all_crops.remove(current_crop)
                                    
                                    # Add none option and set crop options
                                    all_crops.append('__NONE__')
                                    crop_options = all_crops
                                    
                                    # Get crop metadata for display
                                    try:
                                        for crop_name in all_crops:
                                            if crop_name != '__NONE__':
                                                crop = Crop.query.filter_by(name=crop_name).first()
                                                if crop:
                                                    crop_metadata[crop_name] = {
                                                        'states': crop.prioritized_states or [],
                                                        'seasons': crop.prioritized_seasons or [],
                                                        'avg_yield': crop.avg_yield or 0
                                                    }
                                    except SQLAlchemyError:
                                        # Metadata fetch is optional
                                        pass
                                    
                                else:
                                    analysis_error = "Could not generate crop recommendations"
                                    
                            except Exception as e:
                                logger.error(f"Error in crop analysis: {e}")
                                analysis_error = "Error analyzing farmer data. Please try again."
                                flash('Analysis failed', 'error')
                        else:
                            analysis_warning = "Farmer profile is incomplete. Please ensure all soil details are filled."
                            
                except Exception as e:
                    logger.error(f"Error processing farmer analysis: {e}")
                    flash('Error processing farmer data', 'error')

            elif 'save_crop' in request.form:
                return handle_crop_save(request, govt_user, govt_location_ids)
            
            elif 'register_farmer' in request.form and selected_option == 'register_farmer':
                return handle_farmer_registration(request, govt_user, govt_location_ids)
            
            elif 'save_area_details' in request.form:
                return handle_area_details_save(request, govt_user)
            
            elif 'go_back' in request.form:
                session.pop('selected_option', None)
                return redirect(url_for('government.dashboard'))

        # Handle GET requests for view_farmers
        if request.method == 'GET' and selected_option == 'view_farmers':
            farmers = handle_farmer_list_view(request, govt_location_ids)

        return render_template(
            'government/dashboard.html',
            govt_user=govt_user,
            selected_option=selected_option,
            farmer_data=farmer_data,
            crop_options=crop_options,
            farmer_details_incomplete=farmer_details_incomplete,
            farmers=farmers,
            farmer_count=total_farmers,
            active_farmer_count=active_farmers,
            search_query=request.args.get('search', ''),
            current_status=request.args.get('status', ''),
            locations=govt_locations,
            analysis_warning=analysis_warning,
            analysis_error=analysis_error,
            crop_metadata=crop_metadata,
            low_coverage_crops=low_coverage_crops
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in dashboard: {e}")
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('auth.login'))

def handle_crop_save(request, govt_user, govt_location_ids):
    """Handle crop save operation safely"""
    try:
        farmer_id = request.form.get('farmer_id')
        selected_crop = request.form.get('selected_crop')
        
        if not farmer_id or not selected_crop:
            flash('Missing required fields', 'error')
            return redirect(url_for('government.dashboard', option='analyze'))
        
        # Check if farmer is in any location under this pincode
        farmer = Farmer.query.filter(
            Farmer.id == farmer_id,
            Farmer.location_id.in_(govt_location_ids)
        ).first()
        
        if not farmer:
            flash('Farmer not found in your area', 'error')
            return redirect(url_for('government.dashboard', option='analyze'))
        
        # Handle crop selection
        selected_crop_id = None
        if selected_crop and selected_crop != '__NONE__':
            crop = Crop.query.filter_by(name=selected_crop).first()
            if crop:
                selected_crop_id = crop.id
            else:
                flash('Selected crop not found in database', 'error')
                return redirect(url_for('government.dashboard', option='analyze'))
        
        # Update farmer crop
        prev_crop_id = farmer.current_crop_id
        if prev_crop_id == selected_crop_id:
            flash('No changes made', 'info')
            return redirect(url_for('government.dashboard', option='view_farmers'))
        
        # Update farmer
        farmer.previous_crop_id = prev_crop_id
        farmer.current_crop_id = selected_crop_id
        farmer.fertilizer_needed = None
        
        # Delete related reports
        try:
            DiseaseReport.query.filter_by(farmer_id=farmer.id).delete(synchronize_session=False)
            Recommendation.query.filter_by(farmer_id=farmer.id).delete(synchronize_session=False)
        except SQLAlchemyError:
            # Non-critical if deletion fails
            pass
        
        # Update crop counts
        try:
            if prev_crop_id:
                prev_crop = Crop.query.get(prev_crop_id)
                if prev_crop and prev_crop.no_of_farmers:
                    prev_crop.no_of_farmers = max(prev_crop.no_of_farmers - 1, 0)
                    prev_crop.being_grown = prev_crop.no_of_farmers > 0
            
            if selected_crop_id:
                new_crop = Crop.query.get(selected_crop_id)
                if new_crop:
                    new_crop.no_of_farmers = (new_crop.no_of_farmers or 0) + 1
                    new_crop.being_grown = True
            
            # Update government user counts
            if prev_crop_id and not selected_crop_id:
                govt_user.no_farmers_active = max(govt_user.no_farmers_active - 1, 0)
            elif not prev_crop_id and selected_crop_id:
                govt_user.no_farmers_active = (govt_user.no_farmers_active or 0) + 1
            
            db.session.commit()
            flash('Crop updated successfully', 'success')
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating crop counts: {e}")
            flash('Error updating crop information', 'error')
        
        return redirect(url_for('government.dashboard', option='view_farmers'))
        
    except Exception as e:
        logger.error(f"Error in crop save: {e}")
        flash('Error saving crop selection', 'error')
        return redirect(url_for('government.dashboard', option='analyze'))

def handle_farmer_registration(request, govt_user, govt_location_ids):
    """Handle farmer registration safely"""
    try:
        new_farmer_name = request.form.get('new_farmer_name')
        new_farmer_id = request.form.get('new_farmer_id')
        new_farmer_phone = request.form.get('new_farmer_phone')
        new_farmer_email = request.form.get('new_farmer_email')
        area_of_land = request.form.get('area_of_land')
        selected_location_id = request.form.get('location_id')
        
        if not new_farmer_name or not new_farmer_id:
            flash('Name and ID are required', 'error')
            return redirect(url_for('government.dashboard', option='register_farmer'))
        
        # Validate location
        if selected_location_id:
            try:
                selected_location_id = int(selected_location_id)
                if selected_location_id not in govt_location_ids:
                    flash('Invalid location selected', 'error')
                    return redirect(url_for('government.dashboard', option='register_farmer'))
            except (ValueError, TypeError):
                flash('Invalid location', 'error')
                return redirect(url_for('government.dashboard', option='register_farmer'))
        else:
            selected_location_id = govt_location_ids[0] if govt_location_ids else None
        
        # Check if farmer ID already exists
        if Farmer.query.filter_by(id=new_farmer_id).first():
            flash('Farmer ID already exists', 'error')
            return redirect(url_for('government.dashboard', option='register_farmer'))
        
        # Validate phone
        phone = new_farmer_phone
        if phone:
            phone, error = validate_and_format_phone(phone)
            if not phone:
                flash(error, 'error')
                phone = None
        
        # Get location
        location = Location.query.get(selected_location_id) if selected_location_id else None
        
        # Create new farmer
        new_farmer = Farmer(
            name=new_farmer_name,
            id=new_farmer_id,
            phone=phone,
            email=new_farmer_email,
            location_id=selected_location_id,
            location=location,
            land_area=safe_float_conversion(area_of_land),
            type='farmer'
        )
        
        db.session.add(new_farmer)
        
        # Update counts
        try:
            total_farmers = Farmer.query.filter(Farmer.location_id.in_(govt_location_ids)).count()
            govt_user.no_farmers_assigned = total_farmers
            
            if location:
                location.no_of_farmers = Farmer.query.filter_by(location_id=selected_location_id).count()
            
            db.session.commit()
            flash(f'Farmer {new_farmer_id} registered successfully', 'success')
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating counts: {e}")
            flash('Farmer registered but count update failed', 'warning')
        
        return redirect(url_for('government.dashboard', option='view_farmers'))
        
    except Exception as e:
        logger.error(f"Error in farmer registration: {e}")
        flash('Error registering farmer', 'error')
        return redirect(url_for('government.dashboard', option='register_farmer'))

def handle_area_details_save(request, govt_user):
    """Handle area details save safely"""
    try:
        annual_rainfall = request.form.get('annual_rainfall')
        average_temperature = request.form.get('average_temperature')
        
        if not annual_rainfall or not average_temperature:
            flash('Please provide both annual rainfall and average temperature', 'error')
            return redirect(url_for('government.dashboard'))
        
        try:
            rainfall_val = float(annual_rainfall)
            temp_val = float(average_temperature)
            
            # Update all locations under this pincode
            Location.query.filter_by(pincode=govt_user.pincode).update({
                'annual_rainfall': rainfall_val,
                'average_temperature': temp_val
            })
            
            db.session.commit()
            flash('Area details updated for all locations in your pincode', 'success')
            
        except (ValueError, TypeError):
            flash('Please enter valid numeric values', 'error')
        
        return redirect(url_for('government.dashboard'))
        
    except Exception as e:
        logger.error(f"Error saving area details: {e}")
        flash('Error updating area details', 'error')
        return redirect(url_for('government.dashboard'))

def handle_farmer_list_view(request, govt_location_ids):
    """Handle farmer list view with filtering"""
    try:
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        
        # Query farmers across all locations under this pincode
        farmers_query = Farmer.query.filter(Farmer.location_id.in_(govt_location_ids))
        
        if search_query:
            farmers_query = farmers_query.filter(
                or_(
                    Farmer.name.ilike(f'%{search_query}%'),
                    Farmer.id.ilike(f'%{search_query}%'),
                    Farmer.phone.ilike(f'%{search_query}%'),
                    Farmer.current_crop.has(Crop.name.ilike(f'%{search_query}%'))
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
                    Farmer.current_crop_id.is_(None)
                )
            )
        
        return farmers_query.order_by(Farmer.id.asc()).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching farmers list: {e}")
        flash('Error loading farmers list', 'error')
        return []

@govt_bp.route('/government/edit_farmer/<farmer_id>', methods=['GET', 'POST'])
@govt_required
def edit_farmer(farmer_id):
    try:
        farmer = Farmer.query.get_or_404(farmer_id)
        govt_user = GovtUser.query.filter_by(id=session.get('govt_id')).first()
        
        if not govt_user:
            flash('Government user not found', 'error')
            return redirect(url_for('government.dashboard'))
        
        # Get all location IDs under this pincode
        govt_location_ids = []
        try:
            govt_location_ids = [loc.id for loc in Location.query.filter_by(pincode=govt_user.pincode).all()]
        except SQLAlchemyError:
            pass
        
        # Check if farmer is in any location under this pincode
        if farmer.location_id not in govt_location_ids:
            flash('You can only edit farmers in your area', 'error')
            return redirect(url_for('government.dashboard'))

        if request.method == 'POST':
            try:
                phone = request.form.get('phone', farmer.phone)
                if phone:
                    phone, error = validate_and_format_phone(phone)
                    if not phone:
                        flash('Invalid phone number format', 'error')
                        phone = farmer.phone
                
                farmer.name = request.form.get('farmer_name', farmer.name)
                farmer.phone = phone
                farmer.email = request.form.get('email', farmer.email)
                farmer.soil_type = request.form.get('soil_type', farmer.soil_type)
                farmer.ph_level = safe_float_conversion(request.form.get('ph_level'), farmer.ph_level)
                farmer.land_area = safe_float_conversion(request.form.get('area_of_land'), farmer.land_area)
                
                # Handle numeric fields safely
                farmer.nitrogen = safe_float_conversion(request.form.get('nitrogen'), farmer.nitrogen)
                farmer.phosphorus = safe_float_conversion(request.form.get('phosphorus'), farmer.phosphorus)
                farmer.potassium = safe_float_conversion(request.form.get('potassium'), farmer.potassium)
                
                db.session.commit()
                flash('Farmer details updated successfully', 'success')
                return redirect(url_for('government.dashboard', option='view_farmers'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating farmer: {e}")
                flash('Error updating farmer details', 'error')

        return render_template('admin/edit_farmer.html', farmer=farmer)
        
    except Exception as e:
        logger.error(f"Error in edit_farmer: {e}")
        flash('Error loading farmer details', 'error')
        return redirect(url_for('government.dashboard'))

@govt_bp.route('/remove_farmer', methods=['POST'])
@govt_required
def remove_farmer():
    try:
        farmer_id = request.form.get('farmer_id')
        if not farmer_id:
            flash('Farmer ID required', 'error')
            return redirect(url_for('government.dashboard', option='view_farmers'))
        
        farmer = Farmer.query.filter_by(id=farmer_id).first()
        govt_user = GovtUser.query.filter_by(id=session.get('govt_id')).first()
        
        if not farmer:
            flash('Farmer not found', 'error')
        elif not govt_user:
            flash('Government user not found', 'error')
        else:
            # Get all location IDs under this pincode
            govt_location_ids = []
            try:
                govt_location_ids = [loc.id for loc in Location.query.filter_by(pincode=govt_user.pincode).all()]
            except SQLAlchemyError:
                pass
            
            if farmer.location_id not in govt_location_ids:
                flash('You can only remove farmers in your area', 'error')
            else:
                location_id = farmer.location_id
                db.session.delete(farmer)
                
                try:
                    # Update counts
                    total_farmers = Farmer.query.filter(Farmer.location_id.in_(govt_location_ids)).count()
                    active_farmers = Farmer.query.filter(
                        Farmer.location_id.in_(govt_location_ids),
                        Farmer.current_crop_id.isnot(None)
                    ).count()
                    govt_user.no_farmers_assigned = total_farmers
                    govt_user.no_farmers_active = active_farmers
                    
                    # Update location count
                    location = Location.query.get(location_id)
                    if location:
                        location.no_of_farmers = Farmer.query.filter_by(location_id=location_id).count()
                    
                    db.session.commit()
                    flash(f'Farmer {farmer_id} removed successfully', 'success')
                    
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Error updating counts after removal: {e}")
                    flash('Farmer removed but count update failed', 'warning')
        
        return redirect(url_for('government.dashboard', option='view_farmers'))
        
    except Exception as e:
        logger.error(f"Error removing farmer: {e}")
        flash('Error removing farmer', 'error')
        return redirect(url_for('government.dashboard', option='view_farmers'))

@govt_bp.route('/get_user_details', methods=['GET'])
@govt_required
def get_user_details():
    try:
        user_type = request.args.get('user_type', 'farmer')
        user_id = request.args.get('user_id')
        
        if not user_id:
            return "User ID required", 400
        
        if user_type == 'farmer':
            user = Farmer.query.get_or_404(user_id)
            return render_template('government/_farmer_details.html', farmer=user)
        else:
            return "Invalid user type", 400
            
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return "Error loading user details", 500

# Health check endpoint
@govt_bp.route('/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except SQLAlchemyError:
        return jsonify({'status': 'degraded', 'database': 'disconnected'}), 500
    
<<<<<<< HEAD
@govt_bp.route('/govt_dashboard/save_crop', methods=['POST'])
@govt_required
@session_required
def save_crop():
    govt_user = GovtUser.query.filter_by(id=session.get('govt_id')).first()
    if not govt_user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))

    # Get location IDs under this user
    govt_location_ids = [loc.id for loc in Location.query.filter_by(pincode=govt_user.pincode).all()]
    
    return handle_crop_save(request, govt_user, govt_location_ids)
=======
    if user_type == 'farmer':
        user = Farmer.query.get_or_404(user_id)
        return render_template('admin/_farmer_details.html', farmer=user)
    else:

        return "Invalid user type", 400
>>>>>>> f2acce8f400823c83627d4b473d40ee52deddfce
