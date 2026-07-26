## Purpose

This document defines the business language of the Editorial Intelligence Platform.

Every database table, service, API, and frontend screen should derive from these domain concepts.

---

# Core Business Flow

Discover
    ↓
Evaluate
    ↓
Enrich
    ↓
Publish

---

# Domain Overview

Technology Domain
        │
contains
        ▼
Feed
        │
discovers
        ▼
Article
        │
evaluated by
        ▼
Editorial Evaluation
        │
selected for
        ▼
Publication
        │
delivered to
        ▼
Reader

---

# Core Entities

## Technology Domain

Represents a logical technology area.

Examples

- AI
- Machine Learning
- Security
- Engineering
- QA

Responsibilities

- Organize feeds
- Group editorial knowledge
- Simplify publication configuration

Relationship

A Technology Domain owns many Feeds.

---

## Feed

Represents an external information source.

Examples

- OpenAI
- Anthropic
- React Blog
- Kubernetes Blog
- OWASP

Responsibilities

- Discover articles
- Store source configuration
- Enable or disable collection

Relationship

A Feed belongs to one Technology Domain.

A Feed discovers many Articles.

---

## Article

Represents externally published content.

Responsibilities

- Preserve original content
- Store metadata
- Act as the source of editorial processing

Relationship

Belongs to one Feed.

Can participate in multiple Editorial Evaluations.

Can appear in multiple Publications.

---

## Editorial Evaluation

Represents the platform's understanding of an article.

Includes

- Classification
- Decision
- Editorial Score
- AI Enrichment

Possible Decisions

- Include
- Review
- Reject

Relationship

Belongs to one Article.

Belongs to one Publication Profile.

---

## Publication Profile

Defines how a publication should be produced.

Examples

- Daily AI Brief
- Daily Security Brief
- Weekly Engineering Digest
- Monthly Technology Magazine

Defines

- Domains
- Schedule
- Audience
- Editorial Style
- Article Limits

---

## Publication

Represents a completed editorial product.

Examples

Daily AI Brief — July 28

Weekly Engineering Digest — Week 31

Technology Magazine — August Edition

Relationship

Generated from one Publication Profile.

Contains many Articles.

---

## Reader (Future)

Represents a consumer of publications.

Future capabilities

- Preferences
- Subscriptions
- Delivery schedules

---

# Domain Principles

Articles are immutable.

Editorial intelligence is additive.

Publications are snapshots.

Publication Profiles drive behavior.

Technology Domains organize knowledge.

---

# Ubiquitous Language

Technology Domain

Logical organization of knowledge.

Feed

External information source.

Article

Collected content.

Editorial Evaluation

The platform's editorial understanding of an article.

Publication Profile

Configuration describing how publications are generated.

Publication

Completed editorial product.