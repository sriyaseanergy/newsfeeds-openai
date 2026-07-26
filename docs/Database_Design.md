## Purpose

The database serves as the persistent memory of the Editorial Intelligence Platform.

It stores business information, editorial decisions, publications, and configuration.

The database is not responsible for business logic.

---

# Database Principles

The database remembers.

Services think.

Pipelines process.

The database should never become the pipeline.

---

# Data Layers

## Configuration Layer

Stores administrator-managed data.

Includes

- Technology Domains
- Feeds
- Publication Profiles
- Scheduler Configuration

---

## Content Layer

Stores externally collected information.

Includes

- Articles
- Raw RSS Content
- Full Article Content
- Metadata

---

## Editorial Layer

Stores platform-generated intelligence.

Includes

- Editorial Evaluations
- OpenAI Enrichment
- Publication Decisions

---

## Publishing Layer

Stores generated publications.

Includes

- Publications
- Publication Sections
- Publication Articles

---

# Persistence Strategy

Every important business entity is persisted.

Pipeline execution occurs in memory.

Each stage loads data, transforms it, and persists the result.

---

# Entity Ownership

Technology Domain

Owns

Feeds

---

Feed

Owns

Articles

---

Article

Owns

Editorial Evaluations

---

Publication Profile

Owns

Publication Rules

---

Publication

Owns

Publication Sections

Publication Articles

---

# Lifecycle of an Article

Feed
        ↓
Discovered
        ↓
Stored
        ↓
Normalized
        ↓
Editorial Evaluation
        ↓
Publication
        ↓
Archived

---

# Immutable Data

Articles

Publication Editions

Published Editorial Decisions

---

# Mutable Data

Technology Domains

Feeds

Publication Profiles

Scheduler Settings

---

# Historical Data

The platform keeps historical publications.

Previous publications are never modified.

Future editorial improvements do not change previously published editions.

---

# Database Constraints

PostgreSQL is the system of record.

The frontend accesses the platform through APIs.

Business logic never lives inside SQL.

The schema should support future expansion without breaking existing data.