import io
from PIL import Image
import google.generativeai as genai
from config import Config
from flask import flash

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze(image_file):
    try:
        # Show loading immediately when called
        image = Image.open(image_file.stream)
        image = image.resize((224, 224))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_bytes.seek(0)
        image_for_gemini = Image.open(image_bytes)

        disease_prompt = """Analyze the uploaded plant image and provide a detailed disease report formatted as a two-column HTML table. 
Use the following structure exactly:

<div class="disease-report">
<table>
<tr><td colspan="2"><b>PLANT DISEASE REPORT</b></td></tr>

<tr><td><b><u>1. DISEASE IDENTIFICATION</u></b></td><td></td></tr>
<tr><td>Name:</td><td><i>[Scientific name]</i></td></tr>
<tr><td>Confidence Level:</td><td><i>[High/Moderate/Low]</i></td></tr>

<tr><td><b><u>2. SYMPTOMS OBSERVED</u></b></td><td></td></tr>
<tr><td>Visible Signs:</td><td><i>[Description]</i></td></tr>
<tr><td>Color:</td><td><i>[Colors]</i></td></tr>
<tr><td>Shape/Pattern:</td><td><i>[Description]</i></td></tr>
<tr><td>Affected Areas:</td><td><i>[Plant parts]</i></td></tr>
<tr><td>Severity:</td><td><i>[Mild/Moderate/Severe]</i></td></tr>

<tr><td><b><u>3. ROOT CAUSES</u></b></td><td></td></tr>
<tr><td>Primary Type:</td><td><i>[Fungal/Bacterial/Viral]</i></td></tr>
<tr><td>Contributing Factors:</td><td></td></tr>
<tr><td>- Environmental:</td><td><i>[Factors]</i></td></tr>
<tr><td>- Cultural:</td><td><i>[Factors]</i></td></tr>

<tr><td><b><u>4. TREATMENT RECOMMENDATIONS</u></b></td><td></td></tr>
<tr><td>Organic Solutions:</td><td></td></tr>
<tr><td>→</td><td><i>[Remedy 1 with instructions]</i></td></tr>
<tr><td>→</td><td><i>[Remedy 2 with instructions]</i></td></tr>
<tr><td>Chemical Solutions:</td><td></td></tr>
<tr><td>→</td><td><i>[Product 1 with notes]</i></td></tr>
<tr><td>→</td><td><i>[Product 2 with notes]</i></td></tr>

<tr><td><b><u>5. PREVENTION MEASURES</u></b></td><td></td></tr>
<tr><td>Immediate Actions:</td><td><i>[Steps]</i></td></tr>
<tr><td>Long-Term Practices:</td><td><i>[Strategies]</i></td></tr>

<tr><td><b>ADDITIONAL NOTES:</b></td><td><i>[Any relevant information]</i></td></tr>
</table>
</div>

Formatting Rules:
1. Use HTML table structure for perfect two-column layout
2. First column contains all headings and labels
3. Second column contains all data values
4. Maintain HTML formatting (<b>, <i>) but NO underlines
5. Use arrow symbols (→) for treatment items
6. Section headings span both columns
7. No markdown symbols, only HTML tags
8. Remove all <u> underline tags
strip all teh white space and new lines from the response
9. No extra spaces between HTML tags and content"""


        response = model.generate_content([disease_prompt, image_for_gemini], safety_settings={
            'HARASSMENT': 'BLOCK_NONE',
            'HATE': 'BLOCK_NONE',
            'SEXUAL': 'BLOCK_NONE',
            'DANGEROUS': 'BLOCK_NONE'
        })

        if response.text:
            formatted_result = response.text.replace("**", "<strong>").replace("**", "</strong>")
            formatted_result = formatted_result.replace("*", "<em>").replace("*", "</em>")
            formatted_result = formatted_result.replace("\n", "<br>")
            return formatted_result
        else:
            return None
    except Exception as e:
        flash(f"Error processing image: {e}", 'error')
        return None