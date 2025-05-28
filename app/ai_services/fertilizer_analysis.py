import google.generativeai as genai
from config import Config
import json

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze(crop, nitrogen, phosphorus, potassium, ph_level):
    if not crop:
        return {
            "recommendation": "Please select a crop first",
            "water_requirement": "Not available",
            "notes": "Crop selection is required for analysis"
        }

    fertilizer_prompt = f"""Analyze the following crop and soil conditions to provide fertilizer recommendations:
    
    Crop: {crop}
    Soil Conditions:
    - Nitrogen: {nitrogen} ppm
    - Phosphorus: {phosphorus} ppm
    - Potassium: {potassium} ppm
    - pH Level: {ph_level}
    
    Provide recommendations in JSON format with the following structure:
    {{
        "recommendation": "Specific fertilizer recommendations",
        "water_requirement": "Watering requirements for optimal growth",
        "notes": "Additional important notes for crop management"
    }}
    
    Guidelines:
    1. Be specific with fertilizer types and ratios
    2. Consider the soil pH in recommendations
    3. Provide practical, actionable advice
    4. Include any warnings about nutrient imbalances
    5. Keep recommendations concise but comprehensive
    6. Give the watering requirements in float format
    7. The fertilizer recommendation should be givven with a specific fertilizer name only and additional details in notes"""

    try:
        response = model.generate_content([fertilizer_prompt], safety_settings={
            'HARASSMENT': 'BLOCK_NONE',
            'HATE': 'BLOCK_NONE',
            'SEXUAL': 'BLOCK_NONE',
            'DANGEROUS': 'BLOCK_NONE'
        })
        
        if response.text:
            try:
                # Clean the response text to ensure valid JSON
                cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
                result = json.loads(cleaned_text)
                
                # Ensure all required fields are present
                if not all(key in result for key in ["recommendation", "water_requirement", "notes"]):
                    raise ValueError("Missing required fields in response")
                    
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return the text with default structure
                return {
                    "recommendation": response.text,
                    "water_requirement": 0,
                    "notes": "AI-generated recommendation - verify with local expert"
                }
            except Exception as e:
                print(f"Error processing response: {e}")
                return {
                    "recommendation": "Error processing analysis",
                    "water_requirement": 0,
                    "notes": "Technical error occurred"
                }
                
        return {
            "recommendation": "Unable to generate recommendation",
            "water_requirement": 0,
            "notes": "No response from analysis service"
        }
    except Exception as e:
        print(f"Error generating fertilizer analysis: {e}")
        return {
            "recommendation": "System error - please try again later",
            "water_requirement": "Standard watering for crop type",
            "notes": "Technical difficulty in analysis"
        }