import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze(crop_selected, nitrogen, phosphorus, potassium, area_of_land):
    fertilizer_prompt = f"""Analyze the crop selected and suggest the fertilizer needed:
        - Crop Selected: {crop_selected}
        - nitrogen, phosphorus, potassium levels in the soil : {nitrogen}, {phosphorus}, {potassium}
        - Area of land: {area_of_land} hectares
        - analyze the crop and suggest the type of fertilizer needed for best yield
        Provide:
        a Python string in the form of value1, value2, ..., containing the type of fertilizer needed for the crop selected. Do not include any additional text, explanations, or code formatting. The output should be directly assignable to a Python variable as a string."""
    try:
        response = model.generate_content([fertilizer_prompt], safety_settings={
            'HARASSMENT': 'BLOCK_NONE',
            'HATE': 'BLOCK_NONE',
            'SEXUAL': 'BLOCK_NONE',
            'DANGEROUS': 'BLOCK_NONE'
        })
        return response.text
    except Exception as e:
        print(f"Error generating fertilizer analysis: {e}")
        return ""