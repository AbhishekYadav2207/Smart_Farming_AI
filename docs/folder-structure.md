---
Title: Repository Folder Structure
Description: File-by-file directory structure, import mappings, and class responsibilities.
Audience: Contributors, Developers, System Engineers
Last Updated: 2026-07-10
Related Documents: [Modules](modules.md), [Database](database.md), [Developer Guide](developer-guide.md)
---

# Documentation

[Home](../README.md) | [Architecture](architecture.md) | [Modules](modules.md) | [AI Pipelines](ai-pipelines.md) | [Database](database.md) | [API](api.md) | [Deployment](deployment.md) | [Roadmap](roadmap.md) | [Developer Guide](developer-guide.md) | [Security](security.md) | [Testing](testing.md) | [Performance](performance.md)

---

## Table of Contents

- [Overview](#overview)
- [Directory Tree Diagram](#directory-tree-diagram)
- [Root Directory Configuration Files](#root-directory-configuration-files)
- [Application Package (app/)](#application-package-app)
- [Module Blueprint Directories](#module-blueprint-directories)
  - [1. Authentication Blueprint (app/auth/)](#1-authentication-blueprint-appauth)
  - [2. Farmer Blueprint (app/farmer/)](#2-farmer-blueprint-appfarmer)
  - [3. Government Blueprint (app/government/)](#3-government-blueprint-appgovernment)
  - [4. Administrative Blueprint (app/admin/)](#4-administrative-blueprint-appadmin)
- [Core Application Support Folders](#core-application-support-folders)
  - [AI Services (app/ai_services/)](#ai-services-appai_services)
  - [Utility Scripts (app/utils/)](#utility-scripts-apputils)
  - [Assets Directory (assets/)](#assets-directory-assets)

---

## Overview

The Smart Farming AI project follows standard Flask configurations, separating routes and controllers into distinct, self-contained blueprint folders.

---

## Directory Tree Diagram

The diagram below maps all files and directories in the repository:

```
smart_farming_AI/
├── app/                              # Main Application Module Package
│   ├── admin/                        # Admin Control Blueprint
│   │   ├── __init__.py               # Package marker
│   │   ├── forms.py                  # Admin WTF validation classes
│   │   └── routes.py                 # Admin dashboard and lookup controller
│   ├── ai_services/                  # Gemini 2.5 Flash Wrapper Classes
│   │   ├── __init__.py               # Package marker
│   │   ├── chatbot_ai.py             # FarmBot AI controller
│   │   ├── crop_recommendation.py    # Crop recommendations script
│   │   ├── disease_detection.py      # Vision-based leaf diagnostic handler
│   │   └── fertilizer_analysis.py    # Soil NPK advisory script
│   ├── auth/                         # Authentication and AJAX Blueprint
│   │   ├── __init__.py               # Package marker
│   │   ├── forms.py                  # Login and Registration forms
│   │   └── routes.py                 # Authorization controller routes
│   ├── farmer/                       # Farmer Features Blueprint
│   │   ├── __init__.py               # Package marker
│   │   └── routes.py                 # Farmer dashboard and FarmBot API routes
│   ├── government/                   # Government User Blueprint
│   │   ├── __init__.py               # Package marker
│   │   └── routes.py                 # Regional planning controller
│   ├── static/                       # Static Asset Repository
│   │   ├── images/                   # Dynamic login and role-specific backgrounds
│   │   └── styles.css                # Base application style sheet
│   ├── templates/                    # Jinja2 Layout Templates
│   │   ├── admin/                    # Admin panels and modal overlays
│   │   ├── auth/                     # Authentication interface screens
│   │   ├── errors/                   # HTTP Error layouts (404, 500)
│   │   ├── farmer/                   # Farmer dashboard view screen
│   │   ├── features/                 # Disease upload interfaces
│   │   ├── government/               # Government user regional dashboards
│   │   ├── base.html                 # Parent framework document
│   │   └── index.html                # Public landing page
│   ├── utils/                        # Application Utilities
│   │   ├── __init__.py               # Package marker
│   │   ├── decorators.py             # Security checks and inactivity guards
│   │   ├── helpers.py                # Database sync helpers
│   │   └── validation.py             # Phone number format validation checks
│   ├── __init__.py                   # Core Application Factory configuration
│   ├── extensions.py                 # Extensions definitions file
│   └── models.py                     # SQLAlchemy database models schema
├── assets/                           # Documentation Media Assets
│   ├── banners/                      # Banners and social previews
│   ├── diagrams/                     # Architecture flowcharts and schemas
│   └── screenshots/                  # User interface screenshots
├── docs/                             # Project Documentation Suite
│   ├── adr/                          # Architectural Decision Records
│   └── ...                           # Markdown documentation files
├── Dockerfile                        # Docker container configurations
├── app.py                            # Development environment bootstrapper
├── run.py                            # Production environment entry point
├── config.py                         # App configuration and environment loading
└── requirements.txt                  # Python dependencies index
```

---

## Root Directory Configuration Files

---

### `run.py` & `app.py`
- **Purpose:** Entry points to boot the Flask application.
- **Responsibilities:** Import and execute the Flask application factory.
- **Dependencies:** Imports `create_app` from the `app` package.

---

### `config.py`
- **Purpose:** Manages application settings, environment configurations, and session options.
- **Responsibilities:** Loads configuration variables from `.env` and exports the `Config` settings class.
- **Dependencies:** Uses `os`, `dotenv`, and `datetime.timedelta`.

---

### `Dockerfile`
- **Purpose:** Automates building the application container.
- **Responsibilities:** Sets up the Python runtime environment, installs dependencies, and runs Gunicorn.
- **Dependencies:** Uses the `python:3.9-slim` base image.

---

### `requirements.txt`
- **Purpose:** Lists python package dependencies.
- **Responsibilities:** Ensures consistent dependency versions across local and production environments.
- **Dependencies:** Includes `flask`, `flask-sqlalchemy`, `flask-migrate`, `google-generativeai`, and `gunicorn`.

---

## Application Package (app/)

---

### `app/__init__.py`
- **Purpose:** Application factory that configures and initializes the Flask app.
- **Responsibilities:** Registers blueprints, templates, custom filters, database hooks, and configures SQLite.
- **Dependencies:** Imports `Flask` and registers routes from the blueprint folders.

---

### `app/extensions.py`
- **Purpose:** Defines database and security extension instances.
- **Responsibilities:** Declares database (`db`), migrations (`migrate`), security (`csrf`, `limiter`), and session (`login_manager`) managers.
- **Dependencies:** Imports `flask_sqlalchemy`, `flask_migrate`, `flask_wtf.csrf`, and `flask_limiter`.

---

### `app/models.py`
- **Purpose:** Declares the database schema models.
- **Responsibilities:** Maps Python classes to database tables and handles database-level events.
- **Dependencies:** Imports `SQLAlchemy` from `app` and hashing utilities from `werkzeug.security`.

---

## Module Blueprint Directories

---

### 1. Authentication Blueprint (app/auth/)
- **`app/auth/forms.py`:** Defines login and registration forms using WTForms.
- **`app/auth/routes.py`:** Manages user login, registration, and logout flows.

---

### 2. Farmer Blueprint (app/farmer/)
- **`app/farmer/routes.py`:** Manages Farmer dashboards, crop updates, diagnostics, and FarmBot chatbot endpoints.

---

### 3. Government Blueprint (app/government/)
- **`app/government/routes.py`:** Handles regional analytics, rainfall metrics updates, and farmer registration workflows.

---

### 4. Administrative Blueprint (app/admin/)
- **`app/admin/forms.py`:** Defines registration forms for locations and Government Users.
- **`app/admin/routes.py`:** Handles administrative user management, crop catalog updates, and location records.

---

## Core Application Support Folders

---

### AI Services (app/ai_services/)
- **`app/ai_services/crop_recommendation.py`:** Standardizes parameters and calls Gemini for crop recommendations.
- **`app/ai_services/disease_detection.py`:** Processes images and submits them to Gemini Vision.
- **`app/ai_services/fertilizer_analysis.py`:** Recommends soil fertilizer application volumes.
- **`app/ai_services/chatbot_ai.py`:** Implements the conversational FarmBot interface.

---

### Utility Scripts (app/utils/)
- **`app/utils/decorators.py`:** Defines access-control decorators (`@farmer_required`, `@govt_required`, `@admin_required`) and `@session_required` to enforce inactivity timeouts.
- **`app/utils/helpers.py`:** Syncs count statistics across `Farmer` and `Location` tables.
- **`app/utils/validation.py`:** Standardizes contact number formats.

---

### Assets Directory (assets/)
- **`assets/banners/`:** Images used for banners and previews.
- **`assets/diagrams/`:** System flowcharts, database ERDs, and network layouts.
- **`assets/screenshots/`:** User interface screenshots.

---

Previous: [Production Deployment](deployment.md) | Next: [Contributing Guide](contributing.md)
