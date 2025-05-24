from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import Farmer
from app.ai_services import fertilizer_analysis
from app.ai_services import disease_detection as disease_detection_module
from app.utils.decorators import farmer_required,session_required
from app import db

farmer_bp = Blueprint('farmer', __name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/disease_detection', methods=['GET', 'POST'])
def detect_disease():
    disease_result = None
    
    if request.method == 'POST' and 'analyze_disease' in request.form:
        if 'image' in request.files:
            image = request.files['image']
            disease_result = disease_detection_module.analyze(image)
        else:
            flash('Please upload an image.', 'error')
    
    return render_template('features/disease_detection.html', disease_result=disease_result)

@farmer_bp.route('/farmer_dashboard', methods=['GET', 'POST'])
@farmer_required
@session_required
def dashboard():
    # Clear selected_option if coming from browser back/forward navigation
    if request.referrer and url_for('farmer.dashboard') in request.referrer:
        session.pop('selected_option', None)

    farmer = Farmer.query.filter_by(id=session['farmer_id']).first()
    selected_option = session.get('selected_option')
    fertilizer_recommendations = None
    disease_result = None

    if request.method == 'POST':
        if 'option' in request.form:
            if request.form['option'] == 'disease':
                return redirect(url_for('main.detect_disease'))
            session['selected_option'] = request.form['option']
            selected_option = session.get('selected_option')
            return redirect(url_for('farmer.dashboard', option=selected_option))

        elif 'save_details' in request.form:
            farmer.soil_type = request.form.get('soil_type')
            farmer.pH_level = request.form.get('pH_level')  
            farmer.nitrogen = request.form.get('nitrogen')
            farmer.phosphorus = request.form.get('phosphorus')
            farmer.potassium = request.form.get('potassium')
            db.session.commit()
            flash('Details saved successfully!', 'success')
        elif 'edit_details' in request.form:
            session['selected_option'] = 'details'
            selected_option = 'details'
        elif 'save_crop' in request.form:
            farmer.crop_selected = request.form.get('selected_crop')
            db.session.commit()
            flash('Crop saved successfully!', 'success')
        elif 'analyze_fertilizer' in request.form:
            if farmer.crop_selected:
                if farmer.fertilizer_needed:
                    farmer.previous_fertilizer_used = farmer.fertilizer_needed
                fertilizer_recommendations = fertilizer_analysis.analyze(
                    farmer.crop_selected, 
                    farmer.nitrogen, 
                    farmer.phosphorus, 
                    farmer.potassium, 
                    farmer.area_of_land
                )
                if fertilizer_recommendations:
                    farmer.fertilizer_needed = fertilizer_recommendations
                    db.session.commit()
                    flash('Fertilizer recommendations updated!', 'success')
            else:
                flash('Please select a crop first.', 'error')
            
        elif 'go_back' in request.form:
            session.pop('selected_option', None)
            selected_option = None

    return render_template(
        'farmer/dashboard.html', 
        farmer=farmer, 
        selected_option=selected_option,
        fertilizer_recommendations=fertilizer_recommendations, 
        disease_result=disease_result
    )