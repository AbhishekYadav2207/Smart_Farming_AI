---
Title: System Architecture
Description: C4 Model details, MVC implementation, and data flow topologies for Smart Farming AI.
Audience: System Architects, Core Developers, DevOps Engineers
Last Updated: 2026-07-10
Related Documents: [Home](../README.md), [Modules](modules.md), [Database](database.md), [Deployment](deployment.md)
---

# Documentation

[Home](../README.md) | [Architecture](architecture.md) | [Modules](modules.md) | [AI Pipelines](ai-pipelines.md) | [Database](database.md) | [API](api.md) | [Deployment](deployment.md) | [Roadmap](roadmap.md) | [Developer Guide](developer-guide.md) | [Security](security.md) | [Testing](testing.md) | [Performance](performance.md)

---

## Table of Contents

- [Overview](#overview)
- [C4 Architecture Model](#c4-architecture-model)
  - [Level 1: System Context Diagram](#level-1-system-context-diagram)
  - [Level 2: Container Diagram](#level-2-container-diagram)
  - [Level 3: Component Diagram](#level-3-component-diagram)
  - [Level 4: Code Design (Class Relations)](#level-4-code-design-class-relations)
- [Model-View-Controller (MVC) Pattern](#model-view-controller-mvc-pattern)
- [Data Flow Topologies](#data-flow-topologies)
  - [AI Inference Request Lifecycle](#ai-inference-request-lifecycle)
  - [Government User Analytical Updates](#government-user-analytical-updates)
- [Physical Deployment Architecture](#physical-deployment-architecture)
- [Current Implementation](#current-implementation)
- [Future Improvements](#future-improvements)

---

## Overview

The Smart Farming AI platform is engineered on a decoupled, modular design pattern utilizing the Model-View-Controller (MVC) blueprint. By combining local relational database records with remote Google Gemini Large Language Model reasoning, the system generates targeted crop recommendations, disease treatments, and interactive conversations while maintaining strict local access control boundaries.

> [!NOTE]
> All systems are designed for high fault tolerance. If remote AI calls fail, the system falls back to regional data structures compiled from official agricultural statistics.

---

## C4 Architecture Model

The following section maps the platform using the C4 software modeling framework.

### Level 1: System Context Diagram

The System Context diagram details how external actors interact with the boundary of the Smart Farming AI platform and how the platform relies on external services.

<!-- IMAGE: assets/diagrams/c4-context.png -->

```mermaid
flowchart LR
    Farmer[🌾 Farmer]
    GovUser[🏛 Government User]
    Admin[⚙ Admin]
    
    subgraph SystemBoundary [Smart Farming AI Platform]
        App[Smart Farming AI Application]
    end
    
    subgraph ExternalAPI [External Interfaces]
        GeminiAPI[Google Gemini 2.5 Flash API]
    end
    
    Farmer -->|Views soil profile, disease diagnostics, FarmBot chat| App
    GovUser -->|Registers farmers, tracks region crop counts| App
    Admin -->|Configures crop master and location pincodes| App
    App -->|Requests AI recommendations & visual diagnostics| GeminiAPI
```

---

### Level 2: Container Diagram

The Container diagram details the high-level technology choices, storage boundaries, and routing protocols within the system context.

<!-- IMAGE: assets/diagrams/c4-container.png -->

```mermaid
flowchart LR
    subgraph ClientLayer [Client Boundary]
        Browser[Web Browser - HTML5/CSS/JS]
    end

    subgraph ContainerBoundary [Application Container]
        WSGI[Gunicorn WSGI Server]
        Flask[Flask MVC App Engine]
        DB[(SQLite / PostgreSQL Database)]
    end

    subgraph ExternalLayer [AI API]
        Gemini[Google Gemini 2.5 Flash API]
    end

    Browser -->|HTTPS Request / AJAX| WSGI
    WSGI -->|Routing / WSGI Protocol| Flask
    Flask -->|SQLAlchemy ORM Read/Write| DB
    Flask -->|Google Generative AI SDK / JSON| Gemini
```

---

### Level 3: Component Diagram

The Component diagram details the internal modular structure of the Flask application container, highlighting Blueprints, Forms, and AI Service wrappers.

<!-- IMAGE: assets/diagrams/c4-component.png -->

```mermaid
flowchart LR
    subgraph HTTP [HTTP Routing]
        WSGI[Gunicorn HTTP Server]
    end

    subgraph Blueprints [Flask Blueprint Controllers]
        AuthBP[Auth Blueprint /auth]
        FarmerBP[Farmer Blueprint /farmer]
        GovBP[Gov Blueprint /government]
        AdminBP[Admin Blueprint /admin]
        MainBP[Main Blueprint /]
        API_BP[API Blueprint /api]
    end

    subgraph CoreEngine [Business Logic & Security]
        Dec[Auth & Timeout Decorators]
        Forms[WTForms Validators]
        Helpers[Counts Sync Helpers]
    end

    subgraph AISubsystem [AI Processing wrappers]
        CR[Crop Recommender]
        DD[Disease Vision Detector]
        FA[Fertilizer Analyzer]
        Chat[FarmBot Chat engine]
    end

    subgraph Data [Data Tier]
        ORM[SQLAlchemy ORM Model Mapper]
        Engine[(SQL Database Engine)]
    end

    WSGI -->|Dispatches| Blueprints
    Blueprints -->|Applies| Dec
    Blueprints -->|Parses| Forms
    
    FarmerBP & GovBP -->|Triggers| AISubsystem
    Blueprints -->|Queries| ORM
    
    GovBP & AdminBP -->|Updates Counts| Helpers
    ORM -->|Reads/Writes| Engine
```

---

### Level 4: Code Design (Class Relations)

The Code diagram maps the structural database model class relationships, inheritance, and foreign keys.

```mermaid
classDiagram
    direction LR
    class Location {
        +Integer id
        +Integer pincode
        +String name
        +String district
        +String state
        +String country
        +Float annual_rainfall
        +Float average_temperature
        +Integer no_of_farmers
        +Integer no_of_govt_users
    }
    class User {
        +String id
        +String name
        +String phone
        +String email
        +DateTime created_at
        +DateTime last_login
        +Boolean is_active
        +String type
    }
    class Farmer {
        +Integer location_id
        +String land_area
        +String soil_type
        +Float ph_level
        +Float nitrogen
        +Float phosphorus
        +Float potassium
        +Integer current_crop_id
        +Integer previous_crop_id
        +Float previous_yield
    }
    class GovtUser {
        +Integer no_farmers_assigned
        +Integer no_farmers_active
        +Integer pincode
        +String password_hash
        +verify_password(password)
    }
    class Crop {
        +Integer id
        +String name
        +String scientific_name
        +Float water_requirements
        +Float ideal_ph_min
        +Float ideal_ph_max
        +Float nitrogen_req
        +Float phosphorus_req
        +Float potassium_req
        +JSON states
        +JSON seasons
        +Integer priority
    }
    class Recommendation {
        +Integer id
        +String farmer_id
        +Integer crop_id
        +DateTime date
        +String fertilizer_recommendation
        +Float water_requirement
        +String notes
    }
    class DiseaseReport {
        +Integer id
        +String farmer_id
        +String image_path
        +DateTime detection_date
        +String disease_name
        +String confidence
        +String symptoms
        +String treatment
        +String prevention
    }

    User <|-- Farmer : Polymorphic Inheritance
    User <|-- GovtUser : Polymorphic Inheritance
    Location "1" --> "*" Farmer : Has Farmers
    Location "1" --> "*" GovtUser : Pincode Join
    Farmer "1" --> "*" Recommendation : Receives
    Farmer "1" --> "*" DiseaseReport : Reports
    Crop "1" --> "*" Recommendation : Referenced
```

---

## Model-View-Controller (MVC) Pattern

The system strictly adheres to Flask’s blueprint-driven MVC pattern:

| Component | Responsibility | Implementation Files |
| :--- | :--- | :--- |
| **Model** | Defines the data schema, relational constraints, security property setters, and validation hooks. | `app/models.py` |
| **View** | Renders HTML forms and data tables using Jinja2 templates, styled with static CSS layouts. | `app/templates/` and `app/static/` |
| **Controller** | Intercepts HTTP requests, runs security checks, executes business logic, queries database layers, and invokes AI scripts. | `app/auth/routes.py`, `app/farmer/routes.py`, `app/government/routes.py`, `app/admin/routes.py` |

---

## Data Flow Topologies

### AI Inference Request Lifecycle

The diagram below details the structural workflow when a Farmer requests an AI analysis:

```mermaid
sequenceDiagram
    autonumber
    actor Farmer as 🌾 Farmer
    participant Flask as Flask Controller
    participant Auth as Session Guard
    participant Gemini as Gemini AI Service
    participant DB as SQL Database

    Farmer->>Flask: POST /farmer_dashboard (analyze_fertilizer)
    Flask->>Auth: Verify user_type=='farmer' & last_activity is active
    alt Session Expired
        Auth-->>Farmer: Redirect to /auth/login (Flash Error)
    else Session Valid
        Auth-->>Flask: Permit transaction
    end
    
    Flask->>DB: Fetch Farmer details, location rainfall, and crop requirements
    DB-->>Flask: Return entity record
    
    Flask->>Gemini: Submit soil metrics, pH, location + structured instruction
    Note over Gemini: Evaluate NPK, pH ratios &<br/>generate JSON response structure
    Gemini-->>Flask: Return JSON recommendation output
    
    alt JSON Parsing Success
        Flask->>DB: Insert Recommendation record (crop_id, fertilizer, water)
        DB-->>Flask: Save confirmation
    else JSON Parsing Failure
        Flask->>Flask: Trigger database fallback calculations
        Flask->>DB: Insert fallback recommendation details
    end
    
    Flask-->>Farmer: Render dashboard page with updated recommendation card
```

---

### Government User Analytical Updates

The diagram below shows how farmer counts dynamically propagate up to the location and Government User statistics:

```mermaid
sequenceDiagram
    autonumber
    actor Govt as 🏛 Government User
    participant Flask as Flask Controller
    participant DB as SQL Database
    participant Helper as Helper: update_govt_user_counts

    Govt->>Flask: POST /government/govt_dashboard (register_farmer)
    Flask->>DB: Validate Farmer ID and insert new Farmer record
    DB-->>Flask: Commit transaction
    
    Flask->>Helper: Invoke update_govt_user_counts(govt_user)
    Helper->>DB: Execute query: COUNT(Farmer.id) WHERE location_id IN (govt_location_ids)
    DB-->>Helper: Return total farmer count
    Helper->>DB: Execute query: COUNT(Farmer.current_crop_id) WHERE location_id IN (govt_location_ids)
    DB-->>Helper: Return active farmer count
    
    Helper->>DB: Update GovtUser table: no_farmers_assigned and no_farmers_active
    DB-->>Helper: Save confirmation
    
    Flask-->>Govt: Redirect to /government/govt_dashboard?option=view_farmers
```

---

## Physical Deployment Architecture

The physical deployment topology routes client traffic through Nginx web servers into Docker containers hosting Gunicorn WSGI applications connected to PostgreSQL.

<!-- IMAGE: assets/diagrams/deployment-topology.png -->

```mermaid
flowchart TD
    Client[Client Web Browser]
    
    subgraph CloudServer [Cloud Production Instance]
        subgraph WebTier [Web Proxy Layer]
            Nginx[Nginx HTTP Proxy]
        end
        
        subgraph ContainerTier [Docker Containers]
            subgraph AppContainer [Application Container]
                Gunicorn[Gunicorn Server]
                FlaskInstance[Flask Application]
            end
        end
        
        subgraph DataTier [Storage Layer]
            Postgres[(PostgreSQL Database)]
        end
    end
    
    subgraph GoogleCloud [External AI Infrastructure]
        Gemini[Gemini 2.5 Flash API]
    end

    Client -->|HTTPS Traffic| Nginx
    Nginx -->|Proxy pass localhost:5000| Gunicorn
    Gunicorn -->|WSGI Dispatch| FlaskInstance
    FlaskInstance -->|SQLAlchemy connection| Postgres
    FlaskInstance -->|HTTPS egress over internet| Gemini
```

---

## Current Implementation

The existing implementation supports:
1.  **MVC Blueprinting:** Separation of admin, auth, farmer, government, main, and API modules.
2.  **Polymorphic Model Inheritance:** The `users` table utilizes single-table inheritance mapping to `Farmer` and `GovtUser` child classes.
3.  **Local SQLite Engine:** Local database queries are handled through `instance/farmers.db` using WAL-mode sync.
4.  **Google Gemini Services:** Visual diagnostics and fertilizer recommendation scripts query `gemini-2.5-flash` natively.

---

## Future Improvements

Planned architectural improvements include:
- **Nginx & SSL Configuration:** Adding an Nginx reverse proxy configuration and Let's Encrypt SSL layers for secure routing.
- **Background Task Workers:** Integrating Celery with Redis to execute AI vision processing out-of-band, mitigating web request timeouts.
- **Multi-Node Database Replication:** Migrating state data to distributed PostgreSQL instances to scale read operations across multiple locations.

---

Previous: [Home](../README.md) | Next: [Modules](modules.md)
