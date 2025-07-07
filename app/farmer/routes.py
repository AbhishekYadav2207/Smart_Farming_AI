from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from app.models import Farmer, Crop, Recommendation, DiseaseReport
from app.ai_services import fertilizer_analysis, disease_detection as disease_detection_module
from app.utils.decorators import farmer_required, session_required
from werkzeug.utils import secure_filename
from app import db
from datetime import datetime
import json
from app.ai_services import chatbot_ai

farmer_bp = Blueprint('farmer', __name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/disease_detection', methods=['GET', 'POST'])
def detect_disease():
    if request.method == 'GET':
        return render_template('features/disease_detection.html')
        
    if request.method == 'POST':
        try:
            # Validate request
            if 'image' not in request.files:
                return jsonify({'error': 'No image uploaded'}), 400
                
            image = request.files['image']
            if image.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            # Get analysis results
            result = disease_detection_module.analyze(image)
            
            # Save to database for farmers
            if 'farmer_id' in session:
                try:
                    report = DiseaseReport(
                        farmer_id=session['farmer_id'],
                        image_path=secure_filename(image.filename),
                        disease_name=result['disease'],
                        confidence=result['confidence'],
                        treatment=json.dumps(result['treatments']),
                        prevention=json.dumps(result['prevention']),
                        symptoms=result['symptoms'],
                    )
                    db.session.add(report)
                    db.session.commit()
                    result['saved'] = True
                except Exception as e:
                    print(f"Error saving report: {e}")
                    result['saved'] = False
            else:
                result['saved'] = False
                
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'disease': 'Analysis Error',
                'confidence': 'Low',
                'symptoms': 'Failed to process image',
                'treatments': {
                    'organic': ['Please try again'],
                    'chemical': ['Consult an expert']
                },
                'prevention': ['Check image quality'],
                'saved': False
            }), 500

@farmer_bp.route('/farmer_dashboard', methods=['GET', 'POST'])
@farmer_required
@session_required
def dashboard():
    # Clear selected_option if coming from browser back/forward navigation
    if request.referrer and url_for('farmer.dashboard') in request.referrer:
        session.pop('selected_option', None)

    # Clear selected_option if coming from external page
    if not request.referrer or url_for('farmer.dashboard') not in request.referrer:
        session.pop('selected_option', None)

    farmer = Farmer.query.filter_by(id=session['farmer_id']).first()
    selected_option = request.args.get('option', session.get('selected_option'))
    session['selected_option'] = selected_option
    fertilizer_recommendations = None
    disease_result = None
    disease_reports_count = db.session.query(DiseaseReport).filter_by(farmer_id=farmer.id).count()
    fertilizer_reports_count = db.session.query(Recommendation).filter_by(farmer_id=farmer.id).count()

    if request.method == 'POST':
        if 'option' in request.form:
            if request.form['option'] == 'disease':
                return redirect(url_for('main.detect_disease'))
            selected_option = request.form['option']
            session['selected_option'] = selected_option
            return redirect(url_for('farmer.dashboard', option=selected_option))

        elif 'save_details' in request.form:
            farmer.soil_type = request.form.get('soil_type')
            farmer.ph_level = float(request.form.get('ph_level'))
            farmer.nitrogen = float(request.form.get('nitrogen'))
            farmer.phosphorus = float(request.form.get('phosphorus'))
            farmer.potassium = float(request.form.get('potassium'))
            db.session.commit()
            flash('Soil details saved successfully!', 'success')
        
        elif 'edit_details' in request.form:
            session['selected_option'] = 'details'
            selected_option = 'details'
        
        elif 'save_crop' in request.form:
            crop_id = request.form.get('selected_crop')
            if crop_id:
                crop = Crop.query.get(crop_id)
                if crop and farmer.current_crop_id != crop.id:
                    # Clear existing disease reports and recommendations
                    DiseaseReport.query.filter_by(farmer_id=farmer.id).delete()
                    Recommendation.query.filter_by(farmer_id=farmer.id).delete()
                    
                    # Update the crop
                    farmer.current_crop = crop
                    db.session.commit()
                    flash('Crop updated successfully! Previous reports cleared.', 'success')
                else:
                    flash('No changes made to crop selection', 'info')
        
        elif 'analyze_fertilizer' in request.form:
            if not farmer.profile_complete:
                flash('Please complete your soil details first.', 'error')
            elif not farmer.current_crop:
                flash('Please select a crop first.', 'error')
            else:
                try:
                    # Create a new recommendation record
                    recommendation = Recommendation(
                        farmer_id=farmer.id,
                        crop_id=farmer.current_crop.id,
                        date=datetime.utcnow()
                    )
                    
                    # Get fertilizer analysis
                    analysis = fertilizer_analysis.analyze(
                        crop=farmer.current_crop.name,
                        nitrogen=farmer.nitrogen,
                        phosphorus=farmer.phosphorus,
                        potassium=farmer.potassium,
                        ph_level=farmer.ph_level
                    )
                    
                    # Save the analysis results
                    recommendation.fertilizer_recommendation = analysis.get('recommendation', 'No specific recommendation')
                    recommendation.water_requirement = analysis.get('water_requirement', 'Standard watering for crop type')
                    recommendation.notes = analysis.get('notes', 'Generated by AI analysis')
                    
                    db.session.add(recommendation)
                    db.session.commit()
                    flash('Fertilizer recommendations generated!', 'success')
                    fertilizer_recommendations = recommendation
                except Exception as e:
                    print(f"Error in fertilizer analysis: {e}")
                    flash('Error generating fertilizer recommendations. Please try again.', 'error')
            
        elif 'go_back' in request.form:
            session.pop('selected_option', None)
            selected_option = None

    # Get latest recommendation
    latest_recommendation = Recommendation.query.filter_by(farmer_id=farmer.id)\
        .order_by(Recommendation.date.desc()).first()

    # Get all available crops for selection
    available_crops = Crop.query.all()

    return render_template(
        'farmer/dashboard.html', 
        farmer=farmer, 
        selected_option=selected_option,
        fertilizer_recommendations=fertilizer_recommendations or latest_recommendation,
        disease_result=disease_result,
        crops=available_crops,
        profile_complete=farmer.profile_complete,
        disease_reports_count=disease_reports_count,
        fertilizer_reports_count=fertilizer_reports_count
    )

@farmer_bp.route('/chatbot_query', methods=['POST'])
@farmer_required
@session_required
def chatbot_query():
    data = request.get_json()
    user_query = data.get('query')
    farmer_id = session.get('farmer_id')

    if not user_query or not farmer_id:
        return jsonify({'response': 'Invalid request.'}), 400

    # Initialize chat history in session if not exists
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Store user message in history
    session['chat_history'].append({'role': 'user', 'content': user_query})

    response_text = chatbot_ai.generate_chatbot_response(user_query, farmer_id)
    
    # Store bot response in history
    session['chat_history'].append({'role': 'bot', 'content': response_text})
    
    # Save the session
    session.modified = True

    return jsonify({'response': response_text})

@farmer_bp.route('/chatbot_history', methods=['GET'])
@farmer_required
@session_required
def get_chat_history():
    chat_history = session.get('chat_history', [])
    return jsonify({'history': chat_history})

@farmer_bp.route('/chatbot_clear', methods=['POST'])
@farmer_required
@session_required
def clear_chat_history():
    session['chat_history'] = []
    session.modified = True
    return jsonify({'success': True})
