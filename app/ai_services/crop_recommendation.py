# app/ai_services/crop_recommendation.py
import google.generativeai as genai
from config import Config
from app.models import Crop
from sqlalchemy import func

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')


def analyze(soil_type, pH_level, rainfall, temperature, location_name,
            nitrogen, phosphorus, potassium, area_of_land, current_crop=None, crops_loc=None, crops_pri=None):
    try:
        # Build detailed state-specific crop data
        crops_info = []
        if crops_loc:
            for crop in crops_loc:
                name = crop.name or "Unknown Crop"
                states = ", ".join(crop.states) if crop.states else "Not specified"
                prioritized_states = ", ".join(crop.prioritized_states) if crop.prioritized_states else "Not specified"
                seasons = ", ".join(crop.seasons) if crop.seasons else "Not specified"
                priority = crop.priority if crop.priority is not None else 0
                ph_min = crop.ideal_ph_min if crop.ideal_ph_min is not None else "Not specified"
                ph_max = crop.ideal_ph_max if crop.ideal_ph_max is not None else "Not specified"
                water = f"{crop.water_requirements} mm" if crop.water_requirements is not None else "Not specified"
                production = crop.total_production if crop.total_production is not None else "Data not available"
                yield_val = crop.avg_yield if crop.avg_yield is not None else "Data not available"

                crop_str = (
                    f"{name} | "
                    f"States: {states} | "
                    f"Prioritized States: {prioritized_states} | "
                    f"Seasons: {seasons} | "
                    f"Priority: {priority} | "
                    f"pH: {ph_min}-{ph_max} | "
                    f"Water: {water} | "
                    f"Total Production: {production} | "
                    f"Average Yield: {yield_val}"
                )
                crops_info.append(crop_str)

        crops_text = "\n".join(crops_info) if crops_info else "Not specified"
        soil_prompt = f"""
You are an agricultural crop recommendation engine.
Your ONLY task is to recommend suitable crops.
Follow every instruction exactly.
Do NOT provide explanations, sentences, or any output other than crop names.

=====================
INPUT CONDITIONS
=====================
- Soil Type: {soil_type or 'Not specified'}
- pH Level: {pH_level or 'Not specified'}
- Annual Rainfall: {rainfall or 'Not specified'} mm
- Average Temperature: {temperature or 'Not specified'}°C
- Location: {location_name or 'Unknown'}
- Nitrogen: {nitrogen or 'Not specified'} kg/ha
- Phosphorus: {phosphorus or 'Not specified'} kg/ha
- Potassium: {potassium or 'Not specified'} kg/ha
- Area of Land: {area_of_land or 'Not specified'} hectares
- Current Crop: {current_crop or 'None'}

=====================
AVAILABLE CROPS FOR THIS LOCATION
=====================
{crops_text}

=====================
RULES FOR MISSING DATA
=====================
- If a field is marked "Not specified" or "Data not available", simply ignore that field.
- Do not reject a crop just because some information is missing.

=====================
PRIORITIZATION RULES
=====================
Rank crops using a combination of the provided data and real-world agricultural principles.
1.  **HIGH PRIORITY TIER:** Crops with exactly one prioritized state which was the state of the farmer and both `total_production` and `avg_yield` data available.
2.  **MEDIUM PRIORITY TIER:** Crops with exactly one prioritized state but without `total_production` or `avg_yield` data.
3.  **GENERAL PRIORITY TIER:** All other crops, sorted by:
    a. **Least** number of farmers (`no_of_farmers`).
    b. **Highest** `total_production`.
    c. **Highest** `avg_yield`.
    d. **Highest** `priority` (if available).

=====================
SUITABILITY RULES & EXTERNAL KNOWLEDGE
=====================
- Match crops with soil type, pH range, rainfall, and temperature.
- Ensure `water_requirements` are compatible with rainfall, considering **real-world climate patterns like monsoon, drought, or floods**.
- Prefer crops with low adoption in this region (`being_grown = False`) to promote crop diversity and sustainability.
- Avoid crops that severely deplete soil or require excessive irrigation.
- **If the provided list is small or not enough crops are suitable, consider crops known to thrive in similar Indian climates and soil types.** For example, Millets for arid regions, flood-tolerant Rice varieties for high rainfall areas, or legumes for nitrogen-deficient soil.
- **Reference knowledge of crop cycles (Kharif, Rabi, Zaid) and common agricultural practices in India to make informed choices.**

=====================
OUTPUT RULES
=====================
- Return ONLY a comma-separated list of **4–6 crop names**.
- The list must be sorted according to the "PRIORITIZATION RULES".
- Use **Title Case** for all crop names (e.g., Wheat, Maize, Chickpea).
- Do NOT output numbering, bullet points, or explanations.
- Do NOT include duplicate crops.
- Do NOT return fewer than 4 crops or more than 6 crops.
- Exclude the current crop ({current_crop or 'None'}) from the list.

=====================
FINAL REQUIREMENT
=====================
Output must be ONLY a single line:
- A comma-separated list
- Between 4 and 6 crop names
- Title Case
- No extra text, no explanations"""


        #return get_fallback_crops(crops_pri)
        response = model.generate_content(
            [soil_prompt],
            safety_settings={
                'HARASSMENT': 'BLOCK_NONE',
                'HATE': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            }
        )

        return process_crop_recommendations(response.text, current_crop)

    except Exception:
        return get_fallback_crops(crops_pri)


def process_crop_recommendations(raw_response, current_crop):
    try:
        crops = []
        if raw_response:
            crops = [format_crop_name(c) for c in raw_response.split(',') if c.strip()]

        crops = list(dict.fromkeys(crops))  # remove duplicates

        if current_crop and current_crop in crops:
            crops.remove(current_crop)

        if not crops or len(crops) < 3:
            crops = get_fallback_crops().split(', ')

        return ', '.join(crops[:6])

    except Exception:
        return get_fallback_crops()


def format_crop_name(crop_name):
    try:
        formatted = crop_name.replace('_', ' ').title().strip()
        existing = Crop.query.filter(
            func.lower(Crop.name) == func.lower(formatted)
        ).first()
        return existing.name if existing else formatted
    except Exception:
        return crop_name or "Crop"


from sqlalchemy import func

def get_fallback_crops(crops_pri=None):
    """
    Retrieves the top 6 fallback crops from a given list, sorted by
    a multi-tiered prioritization logic.
    
    Args:
        crops_pri (list, optional): A list of Crop objects. Defaults to None.
    
    Returns:
        str: A comma-separated string of crop names.
    """
    try:
        if crops_pri:
            # Step 1: Filter and sort crops based on a precise hierarchy of rules.
            # We'll use a lambda function to define the sorting keys for each crop.
            sorted_crops = sorted(
                crops_pri,
                key=lambda crop: (
                    # Tier 1: Is the crop in a single prioritized state?
                    # `len(crop.prioritized_states) == 1` is true (1) or false (0).
                    # `(crop.total_production is not None and crop.avg_yield is not None)`
                    # is true (1) or false (0).
                    # We negate both (using `not`) to give the highest priority (0)
                    # to crops that meet both conditions.
                    not (len(crop.prioritized_states) == 1 and
                         crop.total_production is not None and
                         crop.avg_yield is not None),
                         
                    # Tier 2: Is the crop in a single prioritized state but has no production/yield data?
                    # This comes next. A true condition (0) will be prioritized over a false one (1).
                    not (len(crop.prioritized_states) == 1 and
                         (crop.total_production is None or crop.avg_yield is None)),

                    # Tier 3 (Hybrid Constraint): Sort remaining crops.
                    # Sort by the least number of farmers. `no_of_farmers` is positive, so we negate it.
                    crop.no_of_farmers if crop.no_of_farmers is not None else float('inf'),
                    
                    # Then by highest total production.
                    -(crop.total_production or 0),
                    
                    # Then by highest average yield.
                    -(crop.avg_yield or 0),

                    # Fallback to the original priority if all else is equal.
                    crop.priority
                )
            )
            
            # Step 2: Select the top 6 crops from the sorted list.
            fallback_crops = sorted_crops[:]
            
            if fallback_crops:
                return ', '.join([crop.name for crop in fallback_crops])

    except Exception:
        # Gracefully handle any errors during the process.
        pass

    # Final fallback if the initial list is empty or the process fails.
    return "Wheat, Rice, Maize, Soybean, Cotton, Sugarcane"