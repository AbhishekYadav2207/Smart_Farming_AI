# Smart Farming Application

## Overview

The **Smart Farming Application** is an AI-driven, IoT-enabled, and data-driven platform designed to empower Indian farmers by providing **personalized, localized, and sustainable crop recommendations**. It integrates **soil sensors, satellite data, weather APIs, and government datasets** to ensure reliable guidance. The platform also includes **security, role-based access, multilingual support, offline access, and government monitoring capabilities**.

---

## Features

### Core Features
- **AI Crop Recommendation System**
  - Uses soil nutrients (NPK, pH), past fertilizers, previous crops, weather, and location.
  - Tiered constraints:
    1. Single prioritized state with full production & yield data.
    2. Single prioritized state with partial/missing data.
    3. Hybrid sorting: fewest farmers, highest total production, highest yield.
  - Dataset fallback ensures recommendations if AI fails.

- **Soil & Fertilizer Management**
  - Real-time IoT sensors measure NPK, pH, and moisture.
  - Satellite data fallback using SoilGrids and Bhuvan APIs.
  - Smart fertilizer recommendations based on crop type, soil nutrients, and past history.
  - Future upgrade: Recommended pH & NPK values per crop.

- **Weather & Location Awareness**
  - Weather API integration for rainfall, temperature, humidity.
  - Hyper-local recommendations using **1.65 lakh+ pincode dataset**.

- **Pest & Disease Detection**
  - Farmers upload crop images; AI detects pests/diseases.
  - Natural remedies recommended first, then chemical treatments if needed.
  - Early warning alerts based on nearby farm data.

- **Chatbot & Multilingual Support**
  - AI chatbot answers crop, soil, and fertilizer queries.
  - Supports multiple Indian languages for inclusive access.

- **Offline & Voice-Assisted Access**
  - Toll-free IVR for farmers without smartphones.
  - Provides advice in local languages for low-connectivity regions.

---

### Advanced Features
- Dynamic crop rotation planner to maintain soil fertility.
- Historical crop performance analytics for yield, fertilizer, and environmental tracking.
- Fertilizer efficiency and cost calculator.
- Climate adaptation guidance (drought/flood-tolerant crops).
- Sustainability scoring for soil health, water usage, and environmental impact.
- Personal dashboards for farmers and government analytics dashboards.

---

### Security & Access
- **Role-Based Access Control**
  - Farmers: Access only personal data and recommendations.
  - Government Users: Access farmers within assigned pincodes only.
  - Admins: Full control over all users, crops, and datasets.
- **Session Timeout:** Automatic logout for inactive users.
- Strong data privacy and security mechanisms.

---

### Datasets
- **Crop Dataset:** Scientific name, season, yield, total production, prioritized states, farmer count, and recommended pH/NPK values.
- **Location Dataset:** 1.65 lakh+ pincodes from *data.gov.in*.
- Hybrid combination of AI + dataset + fallback ensures **accurate, hyper-local recommendations**.

---

### Future Scope
- Web-first approach, mobile app in later phases.
- Integration with government seed/fertilizer subsidy schemes.
- Profit & yield forecasting for decision-making before planting.
- Direct farmer-to-market connections for better transparency.
- Sustainability & environmental impact insights.

---

### Unique Features / Showstoppers
- Hybrid AI + IoT + Satellite + Dataset system ensures reliability.
- Robust fallback system guarantees recommendations even if AI fails.
- Hyper-local precision for 1.65 lakh+ locations.
- Inclusive: Web, mobile, IVR, multilingual support.
- Predictive pest/disease alerts and early warnings.
- Dynamic crop rotation and sustainability scoring.
- Historical analytics for farmers and government planning.
- Scalable architecture for new regions, crops, and datasets.

---

### Expected Impact
- **Farmers:** Better yields, improved soil health, data-backed decisions, reduced risks.
- **Government:** Efficient monitoring and policy implementation at pincode level.
- **Society:** Sustainable agriculture, inclusive technology adoption, improved food security.

---

### Technology Stack
- Backend: Python (Flask), SQLAlchemy (Database ORM)
- AI/ML: Google Gemini API for crop recommendation, pest/disease detection
- IoT: NPK, pH, moisture sensors
- Frontend: HTML/CSS, JavaScript
- APIs: Weather API, Satellite (SoilGrids, Bhuvan), government datasets

---

### Usage
1. Farmers register with their farm location and unique ID.
2. IoT sensors and/or satellite data feed soil information.
3. AI recommends crops based on soil, weather, and historical datasets.
4. Farmers receive crop, fertilizer, and pest/disease guidance via web, chatbot, or IVR.
5. Government users monitor farmers in their assigned pincodes; admins manage the system globally.

---

### License
This project is open-source and available for academic, research, and non-commercial use.
