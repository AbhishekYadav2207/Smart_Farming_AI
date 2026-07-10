---
title: "ADR 0003: Flask-SQLAlchemy ORM with Single-Table Inheritance"
description: "Architecture Decision Record for using Flask-SQLAlchemy and Single-Table Inheritance to model users."
audience: "Developers, Database Administrators, Architects"
last_updated: "2026-07-10"
related_documents: "[Database](../database.md), [Developer Guide](../developer-guide.md)"
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

The application requires an Object-Relational Mapper (ORM) to manage SQL queries and database relationships. We need to:
1.  **Map Complex User Roles:** Model different user roles (such as Farmers and Government Users) that share base columns (like name, email, and phone) but require separate fields (soil parameters for Farmers, regional pincodes for Government Users).
2.  **Ensure Schema Safety:** Enforce validation rules and foreign key constraints at the application level.
3.  **Support Migration Management:** Track database schema modifications across development and production environments.

---

## Decision

We chose **Flask-SQLAlchemy** as our database mapper and implemented **Single-Table Inheritance (STI)** to model user roles:
- Base class `User` holds shared credentials.
- Inherited child classes `Farmer` and `GovtUser` map to the same `users` table, utilizing a polymorphic discriminator column (`type`).
- Database schema changes are tracked using **Flask-Migrate** (Alembic).

---

## Consequences

### Positive:
- **Simplified DB Model:** Storing all user profiles in a single table avoids complex JOIN operations, keeping query performance high.
- **Parametrized Queries:** SQLAlchemy parameterizes all queries automatically, protecting the application against SQL injection attacks.
- **Relational Constraints:** Cascades (`all, delete-orphan`) ensure child records are removed when profiles are deleted, preventing orphaned data records.

### Negative:
- **Null Fields:** Since child models share the same table, columns unique to `Farmer` (such as soil properties) must be nullable to support `GovtUser` records.
- **Table Density:** As more user roles are added, the shared `users` table will grow in width, requiring us to monitor table indexing and query performance closely.

---

Previous: [ADR 0002: Google Gemini AI Integration](0002-gemini.md) | Next: [ADR 0004: Custom RBAC Decorators](0004-role-based-auth.md)
