---
title: "ADR 0004: Role-Based Access Control and Session Decorators"
description: "Architecture Decision Record for implementing custom route-level decorators to manage sessions and roles."
audience: "Developers, Security Engineers, Architects"
last_updated: "2026-07-10"
related_documents: "[Authentication](../authentication.md), [Security](../security.md)"
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

The application requires a secure authentication framework to:
1.  **Enforce Multi-Role Access:** Restrict dashboard access to specific user roles (Farmer, Admin, or Government User).
2.  **Enforce Inactivity Timeouts:** Monitor user activity and automatically log out idle users after 30 minutes to secure sensitive data.
3.  **Ensure Easy Routing Integration:** Protect specific endpoints manually at the route level.

---

## Decision

We chose to implement **custom route decorators** using Flask's built-in session cookie interface, rather than integrating external authentication libraries (such as Flask-Login or Flask-Security):
- Access controls are enforced using `@farmer_required`, `@govt_required`, and `@admin_required` decorators in `app/utils/decorators.py`.
- Session lifetimes are monitored and updated on each request using the `@session_required` wrapper.

---

## Consequences

### Positive:
- **Zero External Dependencies:** Custom wrappers keep the code simple and eliminate dependencies on external security packages.
- **Explicit Access Controls:** Placing decorators directly above route handlers makes it easy to audit permissions:
  ```python
  @farmer_bp.route('/farmer_dashboard')
  @farmer_required
  @session_required
  def dashboard():
      # Dashboard logic
  ```
- **Custom Timeout Handling:** Allows us to log out inactive users and display custom flash warnings on redirect.

### Negative:
- **No Automatic Session Tracking:** Logging user details (such as current active sessions) requires manually mapping database fields, whereas external packages like Flask-Login handle this out of the box.
- **Requires Strict Developer Discipline:** Developers must remember to add the security decorators to all new routes manually. If a decorator is missed, the route will be accessible to unauthorized users.

---

Previous: [ADR 0003: Database ORM](0003-sqlalchemy.md) | Next: [Verification Plan Guide](../testing.md)
