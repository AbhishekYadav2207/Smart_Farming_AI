---
title: "API Specifications and Endpoints"
description: "Structured API specs for AJAX endpoints, auth endpoints, disease detection uploaders, and chatbot routes."
audience: "Frontend Engineers, Integration Developers, QA Teams"
last_updated: "2026-07-10"
related_documents: "[Modules](modules.md), [Database](database.md), [Security](security.md)"
---

# Documentation

[Home](../README.md) | [Architecture](architecture.md) | [Modules](modules.md) | [AI Pipelines](ai-pipelines.md) | [Database](database.md) | [API](api.md) | [Deployment](deployment.md) | [Roadmap](roadmap.md) | [Developer Guide](developer-guide.md) | [Security](security.md) | [Testing](testing.md) | [Performance](performance.md)

---

## Table of Contents

- [Overview](#overview)
- [Endpoints Directory](#endpoints-directory)
- [1. Location Query Service](#1-location-query-service)
- [2. Leaf Disease Vision Diagnostic Service](#2-leaf-disease-vision-diagnostic-service)
- [3. FarmBot Chatbot Session Services](#3-farmbot-chatbot-session-services)
  - [A. Submit Chatbot Query](#a-submit-chatbot-query)
  - [B. Get Chatbot History](#b-get-chatbot-history)
  - [C. Clear Chatbot History](#c-clear-chatbot-history)
- [4. Health Status Monitor](#4-health-status-monitor)
- [Error Codes & Common Structures](#error-codes--common-structures)

---

## Overview

The Smart Farming AI application uses API endpoints to handle location updates, vision-based leaf diagnostics, and natural language chatbot queries.

---

## Endpoints Directory

```
smart_farming_AI/
├── API Endpoints
│   ├── GET  /api/locations                  # Location query by pincode
│   ├── POST /disease_detection              # Visual leaf disease diagnostics
│   ├── POST /farmer/chatbot_query           # Conversational AI client
│   ├── GET  /farmer/chatbot_history         # Chat history logger
│   ├── POST /farmer/chatbot_clear           # Chat logger cleanup
│   └── GET  /government/health              # System health metrics
```

---

## 1. Location Query Service

- **Endpoint:** `/api/locations`
- **Method:** `GET`
- **Authentication:** None (Public endpoint used to populate registration fields)
- **Description:** Returns locations associated with a 6-digit pincode.

### Query Parameters

| Parameter | Data Type | Requirement | Description |
| :--- | :--- | :--- | :--- |
| `pincode` | `String` | Required | 6-digit postal pincode. |

### Response Headers
- `Content-Type: application/json`

### HTTP Status Codes

| Code | Reason | Description |
| :--- | :--- | :--- |
| **200 OK** | Success | Returns the list of locations matching the pincode. |
| **400 Bad Request**| Validation Failed | The pincode was missing, not numeric, or not exactly 6 digits. |

### Request Example
```http
GET /api/locations?pincode=201301 HTTP/1.1
Host: localhost:5000
Accept: application/json
```

### Response Example (200 OK)
```json
{
  "locations": [
    {
      "id": 1,
      "name": "Noida SEC-62",
      "district": "Gautam Buddha Nagar",
      "state": "Uttar Pradesh"
    },
    {
      "id": 2,
      "name": "Noida SEC-63",
      "district": "Gautam Buddha Nagar",
      "state": "Uttar Pradesh"
    }
  ]
}
```

### Response Example (400 Bad Request)
```json
{
  "error": "Invalid pincode format"
}
```

---

## 2. Leaf Disease Vision Diagnostic Service

- **Endpoint:** `/disease_detection`
- **Method:** `POST`
- **Authentication:** Optional (Saves reports to user history if a Farmer session is active; processes anonymously if not logged in).
- **Description:** Standardizes leaf images and analyzes them using Gemini AI Vision.

### Multipart Form Parameters

| Field Name | Type | Requirement | Description |
| :--- | :--- | :--- | :--- |
| `image` | `File (Binary)`| Required | Leaf image (JPEG, JPG, or PNG). |

### HTTP Status Codes

| Code | Reason | Description |
| :--- | :--- | :--- |
| **200 OK** | Success | Image analyzed successfully. Returns diagnostic details. |
| **400 Bad Request**| Missing File | No image was uploaded or the selected file was empty. |
| **500 Server Error**| Processing Failure| Image standardizer failed or Gemini returned an invalid structure. |

### Request Example
```http
POST /disease_detection HTTP/1.1
Host: localhost:5000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="image"; filename="leaf_blight.jpg"
Content-Type: image/jpeg

[RAW IMAGE BINARY DATA]
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

### Response Example (200 OK)
```json
{
  "disease": "Leaf Blight",
  "confidence": "High",
  "symptoms": "Large, oval-shaped brown lesions with concentric rings appearing on the lower leaves.",
  "treatments": {
    "organic": [
      "Spray copper sulfate solution",
      "Remove infected crop residues"
    ],
    "chemical": [
      "Apply Mancozeb 75% WP",
      "Use Chlorothalonil fungicide"
    ]
  },
  "prevention": [
    "Rotate crops with non-host varieties",
    "Ensure proper spacing to promote airflow"
  ],
  "saved": true
}
```

---

## 3. FarmBot Chatbot Session Services

---

### A. Submit Chatbot Query
- **Endpoint:** `/farmer/chatbot_query`
- **Method:** `POST`
- **Authentication:** Enforced (`@farmer_required`, `@session_required`)
- **Description:** Submits a query to FarmBot, which evaluates the question using the Farmer's logged soil profile.

### Request Body (JSON)

| Key | Data Type | Requirement | Description |
| :--- | :--- | :--- | :--- |
| `query` | `String` | Required | The user's query or message. |

### HTTP Status Codes

| Code | Reason | Description |
| :--- | :--- | :--- |
| **200 OK** | Success | Query processed successfully. Returns the chatbot's response. |
| **400 Bad Request**| Missing Fields | The query parameter was missing or the user ID could not be verified. |
| **401 Unauthorized**| Session Expired | The session cookie is missing or has expired. |

### Request Example
```http
POST /farmer/chatbot_query HTTP/1.1
Host: localhost:5000
Content-Type: application/json
Cookie: session=.eJyrV...

{
  "query": "Should I apply more nitrogen to my crop?"
}
```

### Response Example (200 OK)
```json
{
  "response": "Based on your current soil profile, your nitrogen level is 42.0 ppm, which is within the optimal range for Wheat. You do not need to add more nitrogen at this stage, as over-application can lead to excessive leaf growth and lower yields."
}
```

---

### B. Get Chatbot History
- **Endpoint:** `/farmer/chatbot_history`
- **Method:** `GET`
- **Authentication:** Enforced (`@farmer_required`, `@session_required`)
- **Description:** Returns the active chatbot message history for the current session.

### HTTP Status Codes

| Code | Reason | Description |
| :--- | :--- | :--- |
| **200 OK** | Success | Returns the chat history array. |
| **401 Unauthorized**| Session Expired | The session cookie is missing or has expired. |

### Request Example
```http
GET /farmer/chatbot_history HTTP/1.1
Host: localhost:5000
Cookie: session=.eJyrV...
```

### Response Example (200 OK)
```json
{
  "history": [
    {
      "role": "user",
      "content": "Should I apply more nitrogen to my crop?"
    },
    {
      "role": "bot",
      "content": "Based on your current soil profile, your nitrogen level is 42.0 ppm, which is within the optimal range for Wheat. You do not need to add more nitrogen at this stage, as over-application can lead to excessive leaf growth and lower yields."
    }
  ]
}
```

---

### C. Clear Chatbot History
- **Endpoint:** `/farmer/chatbot_clear`
- **Method:** `POST`
- **Authentication:** Enforced (`@farmer_required`, `@session_required`)
- **Description:** Clears the chat history cached in the active session.

### HTTP Status Codes

| Code | Reason | Description |
| :--- | :--- | :--- |
| **200 OK** | Success | Chat history cleared successfully. |
| **401 Unauthorized**| Session Expired | The session cookie is missing or has expired. |

### Request Example
```http
POST /farmer/chatbot_clear HTTP/1.1
Host: localhost:5000
Cookie: session=.eJyrV...
```

### Response Example (200 OK)
```json
{
  "success": true
}
```

---

## 4. Health Status Monitor

- **Endpoint:** `/government/health`
- **Method:** `GET`
- **Authentication:** None
- **Description:** Performs a database connection check to monitor application health.

### HTTP Status Codes

| Code | Reason | Description |
| :--- | :--- | :--- |
| **200 OK** | Database Connected | The system is healthy and connected to the database. |
| **500 Server Error**| Database Disconnected| Database connection failed or timed out. |

### Request Example
```http
GET /government/health HTTP/1.1
Host: localhost:5000
```

### Response Example (200 OK)
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Response Example (500 Server Error)
```json
{
  "status": "degraded",
  "database": "disconnected"
}
```

---

## Error Codes & Common Structures

The API uses standardized error formats to handle validation and processing issues:

```json
{
  "error": "Error details, describing validation failures or processing errors."
}
```

Common response statuses:
- **400 Bad Request:** Returned when inputs are formatted incorrectly (such as invalid phone numbers or missing fields).
- **401 Unauthorized:** Returned when role checks or session validations fail, redirecting the user to the login screen.
- **500 Internal Server Error:** Returned when background processes fail, such as API timeouts or database connection losses.

---

Previous: [Database Schema](database.md) | Next: [Deployment Configurations](deployment.md)
