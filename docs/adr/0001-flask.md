---
title: "ADR 0001: Flask Web Framework"
description: "Architecture Decision Record for selecting Flask as the core framework."
audience: "Developers, Architects"
last_updated: "2026-07-10"
related_documents: "[Architecture](../architecture.md), [Developer Guide](../developer-guide.md)"
---

# Documentation

[Home](../../README.md) | [Architecture](../architecture.md) | [Modules](../modules.md) | [AI Pipelines](../ai-pipelines.md) | [Database](../database.md) | [API](../api.md) | [Deployment](../deployment.md) | [Roadmap](../roadmap.md) | [Developer Guide](../developer-guide.md) | [Security](../security.md) | [Testing](../testing.md) | [Performance](../performance.md)

---

## Table of Contents

- [Status](#status)
- [Context](#context)
- [Decision](#decision)
- [Consequences](#consequences)

---

## Status

**Accepted**

---

## Context

The Smart Farming AI application requires a web framework that satisfies the following requirements:
1.  **Lightweight Core:** Simple core routing that minimizes resource usage.
2.  **Flexible Blueprinting:** Supports separating roles (such as Farmer, Admin, and Government User portals) into modular blueprint folders.
3.  **Low Boilerplate:** Allows rapid deployment without the overhead of heavy frameworks like Django.
4.  **Compatibility:** Full compatibility with the Google Generative AI SDK, Pillow, and SQLAlchemy.

---

## Decision

We chose **Flask 2.3.2** as the core web framework. 

### Why this decision was made:
- **Modular Routing:** Flask's blueprint system allows us to organize the application into self-contained modules (`auth`, `farmer`, `government`, `admin`, `api`, and `main`).
- **Jinja2 Rendering:** The built-in template engine enables rendering server-side HTML and displaying data tables efficiently.
- **Custom Security:** Integrates easily with custom security decorators to enforce Role-Based Access Control (RBAC).

---

## Consequences

### Positive:
- **Simplified codebase:** Clear separations of views, templates, and static styles.
- **Flexibility:** Allows us to select extensions (like Flask-Migrate and Flask-SQLAlchemy) manually, keeping the project lightweight.
- **Ease of Containerization:** Flask's micro-framework core is lightweight, making it easy to package into a single Docker container.

### Negative:
- **No Built-in Admin Panel:** We had to implement a custom admin panel from scratch, which would have been included out of the box in a framework like Django.
- **Manual Security Setup:** Enforcing CSRF protection and role-based checks requires manually importing and configuring extensions like Flask-WTF.

---

Previous: [Performance Details](../performance.md) | Next: [ADR 0002: Google Gemini SDK](0002-gemini.md)
