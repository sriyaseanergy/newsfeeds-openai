# Editorial Intelligence Platform

## 1. Vision

The Editorial Intelligence Platform automatically discovers, evaluates, enriches, and publishes high-quality technology intelligence from trusted sources.

The platform is organized around **Technology Domains**, allowing content to be managed by subject area rather than individual feeds. This enables the platform to scale naturally as new technologies emerge while keeping the architecture simple and maintainable.

The platform follows a single, linear editorial pipeline where each stage has one responsibility and produces a clearly defined output for the next stage.

---

# 2. Goals

The platform is designed to:

- Collect articles from trusted technology sources
- Organize sources into Technology Domains
- Normalize articles into a canonical format
- Select editorial candidates
- Classify articles using OpenAI
- Enrich selected articles with editorial intelligence
- Build professional publications
- Deliver publications through Microsoft Graph
- Provide a clean API for the existing frontend

---

# 3. Non Goals

The platform intentionally avoids:

- Multiple execution modes
- Legacy compatibility layers
- V1 / V2 implementations
- Business logic inside rendering
- Duplicate processing pipelines
- Hardcoded publication logic

---

# 4. Technology Domains

Technology Domains organize the platform's knowledge.

Examples include:

- Artificial Intelligence
- Machine Learning
- Security
- Engineering
- Quality Assurance

Domains own one or more feeds and allow Publication Profiles to define editorial scope without referencing individual feeds.

---

# 5. Publication Types

The platform supports multiple publication schedules.

## Daily

Examples

- Daily AI Brief
- Daily Security Brief

Purpose

Deliver time-sensitive intelligence.

---

## Weekly

Example

Weekly Engineering Digest

Purpose

Summarize engineering developments across Engineering and QA domains.

---

## Monthly

Example

Technology Magazine

Purpose

Provide curated editorial content and long-form industry insights across all domains.

---

# 6. High Level Architecture

Technology Domains
        │
        ▼
Feeds
        │
        ▼
Ingestion
        │
        ▼
Articles
        │
        ▼
Editorial Pipeline
        │
        ▼
Publications
        │
        ▼
HTML Rendering
        │
        ▼
Microsoft Graph Email

---

# 7. Architectural Principles

- Single Responsibility
- Linear Data Flow
- Configuration over Hardcoding
- Domain Driven Design
- Deterministic Processing before AI
- Separation of Concerns
- Observable Pipeline
- PostgreSQL as the System of Record

---

# 8. Architectural Constraints

## Frontend

The existing React frontend remains unchanged.

The backend is responsible for maintaining compatible APIs.

---

## Database

PostgreSQL is the system of record.

pgAdmin is used for administration and inspection.

---

## AI

OpenAI is responsible only for editorial reasoning.

AI never performs rendering, persistence, or scheduling.

---

# 9. Architect's Rules

1. One module = one responsibility.
2. Data always flows forward.
3. The renderer never performs business logic.
4. AI services never generate HTML.
5. Email services never build newsletters.
6. Business rules belong to services.
7. Configuration belongs in the database.
8. Simplicity is preferred over cleverness.
9. Every component should be independently testable.
10. The architecture should be understandable without reading the implementation.