---
title: "Performance Optimization Reference"
description: "Technical reference for database performance, WAL-mode configurations, AI latency, and caching strategies."
audience: "Database Administrators, Performance Engineers, System Architects"
last_updated: "2026-07-10"
related_documents: "[Database](database.md), [Developer Guide](developer-guide.md), [Deployment](deployment.md)"
---

# Documentation

[Home](../README.md) | [Architecture](architecture.md) | [Modules](modules.md) | [AI Pipelines](ai-pipelines.md) | [Database](database.md) | [API](api.md) | [Deployment](deployment.md) | [Roadmap](roadmap.md) | [Developer Guide](developer-guide.md) | [Security](security.md) | [Testing](testing.md) | [Performance](performance.md)

---

## Table of Contents

- [Overview](#overview)
- [Database Performance Optimizations](#database-performance-optimizations)
  - [SQLite Write-Ahead Logging (WAL) Configuration](#sqlite-write-ahead-logging-wal-configuration)
  - [Polymorphic Query Optimization](#polymorphic-query-optimization)
- [Managing AI Response Latency](#managing-ai-response-latency)
  - [Latency Breakdown Table](#latency-breakdown-table)
  - [Timeout and Fallback Strategies](#timeout-and-fallback-strategies)
- [Proposed Performance Enhancements (Future Improvements)](#proposed-performance-enhancements-future-improvements)
  - [1. Redis Cache Implementation](#1-redis-cache-implementation)
  - [2. Asynchronous Task Processing with Celery](#2-asynchronous-task-processing-with-celery)
- [Infrastructure Scaling Strategies](#infrastructure-scaling-strategies)

---

## Overview

This document details the performance optimization strategies implemented in the Smart Farming AI platform, focusing on database efficiency, response times, and scaling.

---

## Database Performance Optimizations

---

### SQLite Write-Ahead Logging (WAL) Configuration
To prevent database locks during concurrent write operations, the application configures the SQLite engine to run in **Write-Ahead Logging (WAL)** mode.

The SQLite parameters are set on initialization in `app/__init__.py`:

```python
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")        # Enables Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL;")      # Balances durability and speed
    cursor.execute("PRAGMA busy_timeout = 5000;")     # Wait 5 seconds before returning a lock error
    cursor.close()
```

#### Why these settings are used:
1.  **`journal_mode=WAL;`:** Allows readers to access the database while a writer is modifying it, increasing concurrency.
2.  **`synchronous=NORMAL;`:** Reduces the frequency of disk sync operations, speeding up writes while maintaining database integrity.
3.  **`busy_timeout = 5000;`:** Sets a wait limit to prevent concurrent transactions from failing immediately under load.

---

### Polymorphic Query Optimization
The application uses Single-Table Inheritance (STI) to map `User`, `Farmer`, and `GovtUser` records to a single `users` table:
- **Index Optimization:** Database queries join tables on primary keys (`users.id = farmers.id`), minimizing indexing overhead.
- **Single-Query Aggregates:** Dashboard calculations (such as counting active farmers) are calculated using a single aggregate query to reduce database hits:
  ```python
  # app/utils/helpers.py
  counts = db.session.query(
      func.count(Farmer.id).label('total'),
      func.count(Farmer.current_crop_id).label('active')
  ).filter(Farmer.location_id.in_(location_ids)).first()
  ```

---

## Managing AI Response Latency

The application calls the Google Gemini API to process agronomy suggestions and vision diagnostics. Since these remote requests introduce network latency, we manage response times as follows:

### Latency Breakdown Table

| Process Pipeline | External Service | Average Latency | Bottleneck Cause | Optimization Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Crop Recommendations**| `gemini-2.5-flash` | 1.8 seconds | Token generation time | Uses a structured prompt to return a comma-separated list of values without explanations. |
| **Leaf Disease Diagnostics**| `gemini-2.5-flash` (Vision) | 3.2 seconds | Image size upload time | Resizes images to 512x512 pixels before upload to minimize payload size. |
| **FarmBot AI Chatbot** | `gemini-2.5-flash` | 2.5 seconds | Context size size | Limits context size by including only the latest recommendation and diagnostic logs. |

### Timeout and Fallback Strategies
To prevent slow API requests from hanging, the application implements timeout limits:
- **API Mocks & Local Fallbacks:** If a request fails, the application falls back to local database lookups, returning suggestions without raising errors.
- **Gunicorn Workers:** Run Gunicorn with multi-threaded workers (`gthread`) in production to process slow AI requests in the background, keeping the main process responsive.

---

## Proposed Performance Enhancements (Future Improvements)

The following enhancements are planned to scale the application to handle high concurrent traffic volumes.

### 1. Redis Cache Implementation
We plan to introduce a Redis cache layer to store static data, such as location directories and crop catalogs:

```python
# Proposed caching helper
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})

@farmer_bp.route('/farmer_dashboard')
@cache.cached(timeout=600, query_string=True)  # Cache dashboard contents for 10 minutes
def dashboard():
    # Execute dashboard queries
```

---

### 2. Asynchronous Task Processing with Celery
We plan to run vision processing tasks in the background using Celery:

```python
# Proposed background task configuration
@celery.task
def process_leaf_image_async(image_bytes):
    # Call Gemini API Vision from background task workers
    return disease_detection.analyze(image_bytes)
```

---

## Infrastructure Scaling Strategies

- **Read/Write Database Splitting:** Route write operations to a primary PostgreSQL instance while routing analytical read requests to replica instances, reducing database load.
- **Rate-Limit Management:** Implement API key rotation to distribute requests across multiple Gemini API keys and prevent rate limit errors.

---

Previous: [Testing Suite](testing.md) | Next: [ADR 0001: Flask Core](adr/0001-flask.md)
