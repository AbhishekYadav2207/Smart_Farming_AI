import google.generativeai as genai
from config import Config
from app.models import Farmer, Crop, Recommendation, DiseaseReport, Location
import json
import html

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_farmer_data_for_ai(farmer_id):
    """Fetches relevant farmer data from the database."""
    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return None

    data = {
        "name": farmer.name,
        "id": farmer.id,
        "phone": farmer.phone,
        "email": farmer.email,
        "location": {
            "pincode": farmer.location.id if farmer.location else None,
            "name": farmer.location.name if farmer.location else "N/A",
            "district": farmer.location.district if farmer.location else "N/A",
            "state": farmer.location.state if farmer.location else "N/A",
            "annual_rainfall": farmer.location.annual_rainfall if farmer.location else "N/A",
            "average_temperature": farmer.location.average_temperature if farmer.location else "N/A",
            "latitude": farmer.location.latitude if farmer.location else "N/A",
            "longitude": farmer.location.longitude if farmer.location else "N/A"
        },
        "land_area": farmer.land_area,
        "soil_type": farmer.soil_type,
        "ph_level": farmer.ph_level,
        "nitrogen": farmer.nitrogen,
        "phosphorus": farmer.phosphorus,
        "potassium": farmer.potassium,
        "current_crop": farmer.current_crop.name if farmer.current_crop else "None",
        "previous_crop": farmer.previous_crop.name if farmer.previous_crop else "None",
        "profile_complete": farmer.profile_complete,
        "latest_fertilizer_recommendation": None,
        "latest_disease_report": None
    }

    latest_rec = Recommendation.query.filter_by(farmer_id=farmer.id).order_by(Recommendation.date.desc()).first()
    if latest_rec:
        data["latest_fertilizer_recommendation"] = {
            "crop": latest_rec.crop.name if latest_rec.crop else "N/A",
            "date": latest_rec.date.strftime('%Y-%m-%d'),
            "recommendation": latest_rec.fertilizer_recommendation,
            "water_requirement": latest_rec.water_requirement,
            "notes": latest_rec.notes
        }

    latest_disease = DiseaseReport.query.filter_by(farmer_id=farmer.id).order_by(DiseaseReport.detection_date.desc()).first()
    if latest_disease:
        data["latest_disease_report"] = {
            "disease_name": latest_disease.disease_name,
            "confidence": latest_disease.confidence,
            "symptoms": latest_disease.symptoms,
            "treatment": latest_disease.treatment, # This is already JSON string
            "prevention": latest_disease.prevention # This is already JSON string
        }
        try:
            data["latest_disease_report"]["treatment"] = json.loads(data["latest_disease_report"]["treatment"])
        except json.JSONDecodeError:
            pass # Keep as string if not valid JSON
        try:
            data["latest_disease_report"]["prevention"] = json.loads(data["latest_disease_report"]["prevention"])
        except json.JSONDecodeError:
            pass # Keep as string if not valid JSON

    return data


def generate_chatbot_response(user_query, farmer_id):
    """Generates a response from the Gemini AI model based on user query and farmer data."""
    farmer_data = get_farmer_data_for_ai(farmer_id)

    if not farmer_data:
        return "I cannot access your data at the moment. Please ensure your profile is complete."

    # Construct a detailed prompt for the AI
    prompt = f"""You are FarmBot AI, an intelligent assistant for farmers. Your goal is to provide helpful and concise answers based on the farmer's provided data and general agricultural knowledge.
    The farmer's current data is:
    {json.dumps(farmer_data, indent=2)}

    Based on this data and your knowledge, answer the following query from the farmer:
    "{user_query}"

    If the query is about personal data, refer to the provided farmer data. If it's a general farming question, use your general knowledge.
    Keep your answers clear, direct, and helpful. If you don't have enough information to answer a specific question about the farmer's data, state that clearly.
    """

    try:
        response = model.generate_content([prompt], safety_settings={
            'HARASSMENT': 'BLOCK_NONE',
            'HATE': 'BLOCK_NONE',
            'SEXUAL': 'BLOCK_NONE',
            'DANGEROUS': 'BLOCK_NONE'
        })
        # Escape special characters in the response
        return html.escape(response.text.strip())
    except Exception as e:
        print(f"Error generating chatbot response: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."
