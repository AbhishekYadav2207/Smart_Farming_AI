---
title: "ADR 0002: Google Gemini AI Integration"
description: "Architecture Decision Record for selecting Google Gemini 2.5 Flash as the primary AI service engine."
audience: "Developers, Architects, Data Scientists"
last_updated: "2026-07-10"
related_documents: "[AI Pipelines](../ai-pipelines.md), [Developer Guide](../developer-guide.md)"
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

The Smart Farming AI application requires an AI service to power three core features:
1.  **Text Classification and Recommendation:** Analyzing nitrogen, phosphorus, potassium, and soil pH levels to suggest crops.
2.  **Computer Vision Diagnostics:** Analyzing leaf photos to predict crop diseases, symptoms, and treatments.
3.  **Conversational Chatbot:** Powering the conversational FarmBot AI assistant to answer user questions contextually.

Running models locally would require expensive server-side GPU hardware, which is not viable for our lightweight deployment target.

---

## Decision

We chose the **Google Gemini 2.5 Flash** model via the `google-generativeai` SDK.

### Why this decision was made:
- **Multimodal Capabilities:** Gemini supports text and image inputs natively, allowing us to use a single model for both crop recommendations and image diagnostics.
- **Low Latency:** The Flash variant is optimized for fast response times, keeping recommendations and chatbot interactions responsive.
- **Developer-Friendly SDK:** Provides native Python bindings, simplifying prompt engineering and image processing setups.

---

## Consequences

### Positive:
- **Simplified Backend:** Offloads heavy GPU processing to Google's cloud infrastructure, keeping container build sizes small.
- **Unified API:** A single external API key configuration (`GEMINI_API_KEY`) supports all AI features.
- **Dynamic Updates:** The model receives continuous updates from Google, improving classification accuracy over time.

### Negative:
- **Network Dependency:** Requires an active internet connection to communicate with Google's API. If the connection fails, the application must fall back to local database lookups.
- **Cost Controls:** High query volumes will incur API usage costs, requiring us to monitor usage patterns and manage rate limits.

---

Previous: [ADR 0001: Flask Core](0001-flask.md) | Next: [ADR 0003: Database ORM](0003-sqlalchemy.md)
