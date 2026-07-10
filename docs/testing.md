---
title: "Testing and Quality Assurance"
description: "Reference for manual validation workflows, visual analysis verification, and automated testing setups."
audience: "QA Teams, Backend Developers, Release Engineers"
last_updated: "2026-07-10"
related_documents: "[Modules](modules.md), [Developer Guide](developer-guide.md), [Security](security.md)"
---

# Documentation

[Home](../README.md) | [Architecture](architecture.md) | [Modules](modules.md) | [AI Pipelines](ai-pipelines.md) | [Database](database.md) | [API](api.md) | [Deployment](deployment.md) | [Roadmap](roadmap.md) | [Developer Guide](developer-guide.md) | [Security](security.md) | [Testing](testing.md) | [Performance](performance.md)

---

## Table of Contents

- [Overview](#overview)
- [Manual Verification Procedures](#manual-verification-procedures)
  - [1. Pincode and Location AJAX Validation](#1-pincode-and-location-ajax-validation)
  - [2. Leaf Disease Vision Verification](#2-leaf-disease-vision-verification)
  - [3. Chatbot Interaction Verification](#3-chatbot-interaction-verification)
- [Edge Cases & Verification Matrix](#edge-cases--verification-matrix)
- [Proposed Automated Testing (Future Improvements)](#proposed-automated-testing-future-improvements)
  - [1. Unit Testing Configuration](#1-unit-testing-configuration)
  - [2. AI API Response Mocking](#2-ai-api-response-mocking)

---

## Overview

This guide details the QA and testing procedures for the Smart Farming AI platform. We focus on manual verification workflows for local testing and outline the configuration for future automated tests.

---

## Manual Verification Procedures

The following manual test scripts can be run to verify the application is working correctly:

### 1. Pincode and Location AJAX Validation
Verify the registration page dynamically loads location lists using the local pincode database:

```
[Enter 6-digit Pincode] ──> [AJAX request triggers] ──> [Dropdown populates local areas]
```

#### Test Steps:
1. Navigate to `/auth/register`.
2. Locate the **Pincode** field (verify it restricts input to a 6-digit string).
3. Input `201301`.
4. Press Tab or click outside the field.
5. Verify the **Location** dropdown updates to display matching locations (e.g., "Noida SEC-62, Gautam Buddha Nagar").
6. Enter an invalid pincode (e.g., `000000`) and verify the dropdown displays: "No locations found."

---

### 2. Leaf Disease Vision Verification
Verify the vision pipeline correctly processes leaf images and handles API errors:

#### Test Steps:
1. Log in as a **Farmer** and navigate to the **Disease Detection** section.
2. Upload a valid leaf image (e.g., `leaf_rust.jpg`).
3. Click **Analyze Image**.
4. Verify the UI displays:
   - Predicted disease name and confidence score.
   - Identified symptoms.
   - Separate organic and chemical treatments.
5. Repeat the test using a non-image file (e.g., a PDF document). Verify the standardizer catches the error and displays a validation warning: "Invalid image file."

---

### 3. Chatbot Interaction Verification
Verify that FarmBot AI references the user's soil profile when answering queries:

#### Test Steps:
1. Log in as a **Farmer** with a configured soil profile.
2. Open the chatbot panel and ask: "What is my current soil pH level?"
3. Verify the chatbot replies with your profile pH value (e.g., `6.8`).
4. Ask a general agronomy question: "What is crop rotation?"
5. Verify the chatbot provides a clear, general answer.
6. Click **Clear History** and verify the chat log is reset.

---

## Edge Cases & Verification Matrix

The following test cases check how the application handles incorrect inputs or missing data:

| Test Target | Input | Expected Output | Status |
| :--- | :--- | :--- | :--- |
| **User ID Check** | Existing ID on registration | Displays: "This user ID is already registered" | Passed |
| **Phone Number Formatter** | `09876543210` (11 digits) | Standardizes the number to: `+919876543210` | Passed |
| **Phone Number Checker**| `12345` (Short input) | Displays: "Invalid phone number" | Passed |
| **Profile Validation** | Missing soil parameters | Displays: "Please complete your soil details first" | Passed |
| **Session Inactivity** | No user activity for 30 min | User is logged out and redirected to the login screen. | Passed |

---

## Proposed Automated Testing (Future Improvements)

To automate verification in production environments, we recommend configuring unit tests and AI mocks:

### 1. Unit Testing Configuration
We recommend setting up automated unit tests using pytest:

```python
# test_app.py
import pytest
from app import create_app, db
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use an in-memory database for speed

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_health_check(client):
    """Verify health endpoint returns a successful database connection status"""
    response = client.get('/government/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
```

---

### 2. AI API Response Mocking
Mock the Google Generative AI API during testing to prevent rate limit issues and run tests offline:

```python
# mock_gemini.py
from unittest.mock import patch
import pytest

@pytest.fixture
def mock_gemini_recommendation():
    with patch('app.ai_services.crop_recommendation.model.generate_content') as mock_call:
        # Configure a mock response that matches the expected Gemini API format
        mock_response = mock_call.return_value
        mock_response.text = "Wheat, Rice, Barley, Maize"
        yield mock_call
```

---

Previous: [Security Details](security.md) | Next: [Performance Details](performance.md)
