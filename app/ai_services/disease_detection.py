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

        disease_prompt = """Analyze the uploaded plant image and provide a detailed disease report formatted in HTML div structure. 
Use the following format exactly:

<div class="disease-report">
  <div class="report-section">
    <h3 class="section-title">DISEASE IDENTIFICATION</h3>
    <div class="report-item">
      <span class="item-label">Name:</span>
      <span class="item-value"><i>[Scientific name]</i></span>
    </div>
    <div class="report-item">
      <span class="item-label">Confidence Level:</span>
      <span class="item-value"><i>[High/Moderate/Low]</i></span>
    </div>
  </div>

  <div class="report-section">
    <h3 class="section-title">SYMPTOMS OBSERVED</h3>
    <div class="report-item">
      <span class="item-label">Visible Signs:</span>
      <span class="item-value"><i>[Description]</i></span>
    </div>
    <div class="report-item">
      <span class="item-label">Affected Areas:</span>
      <span class="item-value"><i>[Plant parts]</i></span>
    </div>
  </div>

  <div class="report-section">
    <h3 class="section-title">TREATMENT RECOMMENDATIONS</h3>
    <div class="treatment-item">
      <span class="treatment-type">Organic Solutions:</span>
      <ul class="treatment-list">
        <li><i>[Remedy 1 with instructions]</i></li>
        <li><i>[Remedy 2 with instructions]</i></li>
        .
        .
        .
        <li><i>[Remedy N with instructions]</i></li>
      </ul>
    </div>
    <div class="treatment-item">
      <span class="treatment-type">Chemical Solutions:</span>
      <ul class="treatment-list">
        <li><i>[Product 1 with notes]</i></li>
        <li><i>[Product 2 with notes]</i></li>
        .
        .
        .
        <li><i>[Product N with notes]</i></li>
      </ul>
    </div>
  </div>

  <div class="report-section">
    <h3 class="section-title">PREVENTION MEASURES</h3>
    <div class="prevention-item">
      <span class="prevention-type">Immediate Actions:</span>
      <span class="prevention-detail"><i>[Steps]</i></span>
    </div>
    <div class="prevention-item">
      <span class="prevention-type">Long-Term Practices:</span>
      <span class="prevention-detail"><i>[Strategies]</i></span>
    </div>
  </div>
</div>

Formatting Rules:
1. Use div-based structure for responsive layout
2. Maintain consistent class names as shown
3. Use semantic HTML elements
4. Keep content concise but informative
5. No tables or complex formatting
6. Remove all unnecessary whitespace
7. Only include the HTML structure, no markdown"""


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