import io
import json
from PIL import Image
import google.generativeai as genai
from config import Config
from flask import flash

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze(image_file):
    try:
        # Validate and process image
        if not image_file or image_file.filename == '':
            raise ValueError("No image selected")
            
        # Open and convert image
        try:
            image = Image.open(image_file.stream)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image = image.resize((512, 512))
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")

        # Prepare for Gemini API
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_data = img_byte_arr.getvalue()

        # Structured prompt
        disease_prompt = """Analyze this plant image and return strict JSON:
        {
            "disease": "string",
            "confidence": "High/Medium/Low",
            "symptoms": "string",
            "treatments": {
                "organic": ["string"],
                "chemical": ["string"]
            },
            "prevention": ["string"]
        }"""

        # Get analysis
        response = model.generate_content(
            [disease_prompt, {'mime_type': 'image/jpeg', 'data': img_data}],
            safety_settings={
                'HARASSMENT': 'BLOCK_NONE',
                'HATE': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            }
        )

        # Parse and validate response
        if not response.text:
            raise ValueError("No response from analysis API")
            
        try:
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(json_str)
            
            # Validate structure
            if not all(key in result for key in ['disease', 'confidence', 'symptoms', 'treatments', 'prevention']):
                raise ValueError("Invalid response format")
                
            return {
                'disease': result['disease'],
                'confidence': result['confidence'],
                'symptoms': result['symptoms'],
                'treatments': {
                    'organic': result['treatments'].get('organic', []),
                    'chemical': result['treatments'].get('chemical', [])
                },
                'prevention': result.get('prevention', [])
            }
            
        except json.JSONDecodeError:
            raise ValueError("Could not parse analysis results")

    except Exception as e:
        flash(str(e), 'error')
        return {
            'disease': 'Analysis Error',
            'confidence': 'Low',
            'symptoms': str(e),
            'treatments': {
                'organic': ['Please try again with a clearer image'],
                'chemical': ['Consult an agricultural expert if problem persists']
            },
            'prevention': ['Ensure proper plant care practices']
        }