from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import Farmer, GovtUser
from app.ai_services import crop_recommendation
from app.utils.decorators import govt_required
from app import db
from sqlalchemy import or_

govt_bp = Blueprint('government', __name__)

@govt_bp.route('/govt_dashboard', methods=['GET', 'POST'])
@govt_required
def dashboard():
    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    if not govt_user:
        flash('Government user not found', 'error')
        return redirect(url_for('auth.login'))

    selected_option = session.get('selected_option')
    farmer_data = None
    crop_options = None
    farmer_details_incomplete = False
    farmers = None

    farmer_count = Farmer.query.filter_by(location=govt_user.location).count()
    active_farmer_count = Farmer.query.filter(
        Farmer.location == govt_user.location,
        Farmer.crop_selected.isnot(None)
    ).count()

    if request.method == 'POST':
        if 'option' in request.form:
            session['selected_option'] = request.form['option']
            return redirect(url_for('government.dashboard', option=request.form['option']))
        
        elif 'farmer_id' in request.form and selected_option == 'analyze':
            farmer_id = request.form['farmer_id']
            farmer_data = Farmer.query.filter_by(id=farmer_id, location=govt_user.location).first()
            
            if not farmer_data:
                flash('Farmer not found in your area', 'error')
            else:
                required_fields = ['soil_type', 'pH_level', 'nitrogen', 'phosphorus', 'potassium']
                farmer_details_incomplete = any(not getattr(farmer_data, field) for field in required_fields)
                
                if not farmer_details_incomplete:
                    analysis_result = crop_recommendation.analyze(
                        farmer_data.soil_type,
                        farmer_data.pH_level,
                        farmer_data.annual_rainfall or govt_user.annual_rainfall,
                        farmer_data.average_temperature or govt_user.average_temperature,
                        farmer_data.location,
                        farmer_data.nitrogen,
                        farmer_data.phosphorus,
                        farmer_data.potassium,
                        farmer_data.area_of_land,
                        farmer_data.crop_selected
                    )
                    if analysis_result:
                        all_crops = [crop.strip() for crop in analysis_result.split(',') if crop.strip()]
                        current_crop = farmer_data.crop_selected
                        
                        if current_crop and current_crop in all_crops:
                            all_crops.remove(current_crop)
                        all_crops.append('__NONE__')
                        crop_options = all_crops

        elif 'save_crop' in request.form:
            farmer_id = request.form['farmer_id']
            selected_crop = request.form['selected_crop']
            
            if selected_crop == '__NONE__':
                selected_crop = None
            
            farmer = Farmer.query.filter_by(id=farmer_id, location=govt_user.location).first()
            if not farmer:
                flash('Farmer not found', 'error')
                return redirect(url_for('government.dashboard', option='analyze'))
            
            if farmer.crop_selected != selected_crop:
                farmer.previous_crop = farmer.crop_selected
                farmer.crop_selected = selected_crop
                farmer.fertilizer_needed = None
                db.session.commit()
                flash('Crop updated successfully', 'success')
            else:
                flash('No changes made', 'info')
            
            return redirect(url_for('government.dashboard', option='view_farmers'))
        
        elif 'farmer_id' in request.form and selected_option == 'view_farmer':
            farmer_id = request.form['farmer_id']
            farmer_data = Farmer.query.filter_by(id=farmer_id).first()
            if farmer_data.location != govt_user.location:
                flash('You do not have access to this farmer\'s data', 'error')
                return redirect(url_for('government.dashboard', option='view_farmers'))
            else:
                farmer_details_incomplete = any(
                    not getattr(farmer_data, field) for field in ['soil_type', 'pH_level', 'nitrogen', 'phosphorus', 'potassium']
                )
                if farmer_details_incomplete:
                    flash('Farmer details are incomplete', 'warning')
                    return render_template('government/dashboard.html', farmer_data=farmer_data, govt_user=govt_user, selected_option=selected_option, crop_options=crop_options, farmer_details_incomplete=farmer_details_incomplete)
            if not farmer_data:
                flash('Farmer not found', 'error')

        elif 'register_farmer' in request.form and selected_option == 'register_farmer':
            new_farmer_name = request.form['new_farmer_name']
            new_farmer_id = request.form['new_farmer_id']
            area_of_land = request.form.get('area_of_land')
            
            if Farmer.query.filter_by(id=new_farmer_id).first():
                flash('Farmer ID already exists', 'error')
            else:
                new_farmer = Farmer(
                    name=new_farmer_name,
                    id=new_farmer_id,
                    location=govt_user.location,
                    annual_rainfall=govt_user.annual_rainfall,
                    average_temperature=govt_user.average_temperature,
                    area_of_land=area_of_land if area_of_land else None
                )
                db.session.add(new_farmer)
                db.session.commit()
                
                flash(f'Farmer {new_farmer_id} registered successfully', 'success')
                return redirect(url_for('government.dashboard', option='view_farmers'))
        
        elif 'save_area_details' in request.form:
            govt_user.annual_rainfall = request.form['annual_rainfall']
            govt_user.average_temperature = request.form['average_temperature']
            
            Farmer.query.filter_by(location=govt_user.location).update({
                'annual_rainfall': govt_user.annual_rainfall,
                'average_temperature': govt_user.average_temperature
            })
            
            db.session.commit()
            flash('Area details updated successfully', 'success')
            return redirect(url_for('government.dashboard'))
        
        elif 'go_back' in request.form:
            session['selected_option'] = None
            return redirect(url_for('government.dashboard'))

    if request.method == 'GET' and selected_option == 'view_farmers':
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        
        farmers_query = Farmer.query.filter_by(location=govt_user.location)
        
        if search_query:
            farmers_query = farmers_query.filter(
                or_(
                    Farmer.id.ilike(f'%{search_query}%'),
                    Farmer.crop_selected.ilike(f'%{search_query}%')
                )
            )
        
        if status_filter == 'active':
            farmers_query = farmers_query.filter(
                Farmer.soil_type.isnot(None),
                Farmer.crop_selected.isnot(None)
            )
        elif status_filter == 'incomplete':
            farmers_query = farmers_query.filter(
                or_(
                    Farmer.soil_type.is_(None),
                    Farmer.crop_selected.is_(None)
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

@govt_bp.route('/edit_farmer/<farmer_id>', methods=['GET', 'POST'])
@govt_required
def edit_farmer(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    
    if farmer.location != govt_user.location:
        flash('You can only edit farmers in your area', 'error')
        return redirect(url_for('government.dashboard'))

    if request.method == 'POST':
        farmer.name = request.form.get('farmer_name', farmer.name)
        farmer.soil_type = request.form.get('soil_type')
        farmer.pH_level = request.form.get('pH_level')
        farmer.nitrogen = request.form.get('nitrogen')
        farmer.phosphorus = request.form.get('phosphorus')
        farmer.potassium = request.form.get('potassium')
        farmer.area_of_land = request.form.get('area_of_land')
        farmer.previous_crop = request.form.get('previous_crop')
        
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
        db.session.commit()
        flash(f'Farmer {farmer_id} removed successfully', 'success')

    return redirect(url_for('government.dashboard', option='view_farmers'))

@govt_bp.route('/save_crop', methods=['POST'])
@govt_required
def save_crop():
    farmer_id = request.form.get('farmer_id')
    selected_crop = request.form.get('selected_crop')
    govt_user = GovtUser.query.filter_by(id=session['govt_id']).first()
    
    if selected_crop == '__NONE__':
        selected_crop = None
    
    farmer = Farmer.query.filter_by(id=farmer_id, location=govt_user.location).first()
    if not farmer:
        flash('Farmer not found', 'error')
        return redirect(url_for('government.dashboard', option='analyze'))
    
    if farmer.crop_selected != selected_crop:
        farmer.previous_crop = farmer.crop_selected
        farmer.crop_selected = selected_crop
        farmer.fertilizer_needed = None
        db.session.commit()
        flash('Crop updated successfully', 'success')
    else:
        flash('No changes made', 'info')
    
    return redirect(url_for('government.dashboard', option='view_farmers'))