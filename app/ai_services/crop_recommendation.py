import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze(soil_type, pH_level, rainfall, temperature, location, nitrogen, phosphorus, potassium, area_of_land, current_crop=None):
    soil_prompt = f"""Analyze the soil conditions for crop suitability:
        - Soil Type: {soil_type}
        - pH Level: {pH_level}
        - Annual Rainfall: {rainfall} mm
        - Average Temperature: {temperature}°C
        - Location: {location}
        - Nitrogen: {nitrogen} kg/ha
        - Phosphorus: {phosphorus} kg/ha
        - Potassium: {potassium} kg/ha
        - Area of Land: {area_of_land} hectares
        - Current Crop: {current_crop} (if any)
        
        Provide a list of 4-6 suitable crops (excluding the current crop if specified) 
        in a comma-separated format like: crop1, crop2, crop3
        
        Only include crops that:
        1. Are different from any current cultivation
        2. Are suitable for the given conditions
        3. Would provide good yield in the specified area
        
        Return ONLY the comma-separated list with no additional text or explanations."""
    
    try:
        response = model.generate_content([soil_prompt], safety_settings={
            'HARASSMENT': 'BLOCK_NONE',
            'HATE': 'BLOCK_NONE',
            'SEXUAL': 'BLOCK_NONE',
            'DANGEROUS': 'BLOCK_NONE'
        })
        return response.text.strip('"').strip("'").strip()
    except Exception as e:
        print(f"Error generating crop recommendations: {e}")
        return None