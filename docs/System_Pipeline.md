## Purpose

The Editorial Intelligence Platform processes information through a single,
linear pipeline.

Each stage has one responsibility.

Each stage consumes a defined input and produces a defined output.

The output of one stage becomes the input of the next.

No stage skips another stage.

---

# Pipeline Overview

Scheduler
        │
        ▼
Publication Profile
        │
        ▼
Enabled Technology Domains
        │
        ▼
Enabled Feeds
        │
        ▼
RSS Discovery
        │
        ▼
Article Normalization
        │
        ▼
Article Persistence
        │
        ▼
Candidate Selection
        │
        ▼
Editorial Classification
        │
        ▼
Editorial Decision
        │
        ▼
Content Fetch
        │
        ▼
Editorial Enrichment
        │
        ▼
Publication Builder
        │
        ▼
HTML Rendering
        │
        ▼
Email Delivery

---

# Stage 1 — Scheduler

Purpose

Determine which Publication Profile should run.

Input

System Time

Output

Publication Profile

Responsibilities

- Execute scheduled publications
- Trigger the pipeline
- Prevent duplicate executions

Must Never

- Read RSS
- Call OpenAI
- Build publications

---

# Stage 2 — Publication Profile

Purpose

Load the publication configuration.

Input

Publication Name

Output

Publication Profile

Responsibilities

- Determine schedule
- Determine Technology Domains
- Determine article limits
- Determine editorial style

Must Never

- Fetch articles

---

# Stage 3 — Feed Discovery

Purpose

Identify every enabled feed that belongs to the selected domains.

Input

Publication Profile

Output

Feed List

Responsibilities

- Load enabled domains
- Load enabled feeds
- Ignore disabled feeds

Must Never

- Download articles

---

# Stage 4 — RSS Discovery

Purpose

Collect articles from external feeds.

Input

Feed List

Output

Raw Articles

Responsibilities

- Download RSS
- Parse RSS
- Validate entries

Must Never

- Call OpenAI

---

# Stage 5 — Normalization

Purpose

Convert all RSS entries into a canonical Article.

Input

Raw Articles

Output

Normalized Articles

Responsibilities

- Normalize dates
- Normalize URLs
- Normalize metadata

Must Never

- Filter articles

---

# Stage 6 — Article Persistence

Purpose

Store newly discovered articles.

Input

Normalized Articles

Output

Stored Articles

Responsibilities

- Insert new articles
- Update metadata
- Ignore duplicates

Must Never

- Make editorial decisions

---

# Stage 7 — Candidate Selection

Purpose

Determine which articles deserve editorial evaluation.

Input

Stored Articles

Output

Candidate Articles

Responsibilities

- Remove duplicates
- Apply recency rules
- Apply publication profile rules

Must Never

- Call OpenAI

---

# Stage 8 — Editorial Classification

Purpose

Understand the editorial characteristics of an article.

Input

Candidate Articles

Output

Editorial Classifications

Responsibilities

- Categorization
- Severity
- Audience
- Editorial relevance

Must Never

- Build newsletters

---

# Stage 9 — Editorial Decision

Purpose

Determine whether an article belongs in the publication.

Input

Editorial Classification

Output

Editorial Decision

Possible Decisions

- Include
- Review
- Reject

Must Never

- Generate summaries

---

# Stage 10 — Content Fetch

Purpose

Download complete article content.

Input

Approved Articles

Output

Full Article Content

Responsibilities

- Download webpage
- Extract clean text

Must Never

- Generate AI summaries

---

# Stage 11 — Editorial Enrichment

Purpose

Generate high-quality editorial content.

Input

Full Article Content

Output

Editorial Intelligence

Examples

- Executive Summary
- Why It Matters
- Recommended Action
- Key Takeaways

Must Never

- Render HTML

---

# Stage 12 — Publication Builder

Purpose

Construct the complete publication.

Input

Editorial Intelligence

Output

Publication

Responsibilities

- Create sections
- Order articles
- Generate statistics

Must Never

- Send email

---

# Stage 13 — HTML Renderer

Purpose

Transform the publication into HTML.

Input

Publication

Output

HTML

Responsibilities

- Render templates
- Replace placeholders

Must Never

- Call OpenAI
- Read RSS
- Query PostgreSQL

---

# Stage 14 — Email Delivery

Purpose

Deliver the publication.

Input

Rendered HTML

Output

Email

Responsibilities

- Send through Microsoft Graph
- Log delivery

Must Never

- Modify publications

---

# Error Handling

Each stage is responsible for reporting failures.

Failures should be isolated whenever possible.

Examples

RSS Failure

Continue with remaining feeds.

OpenAI Failure

Retry according to policy.

Rendering Failure

Abort publication.

Email Failure

Record failure for retry.

---

# Observability

Every stage records

- Start Time
- End Time
- Duration
- Input Count
- Output Count
- Success Count
- Failure Count

These metrics allow complete visibility into the editorial pipeline.

---

# Pipeline Principles

- One direction only.
- One responsibility per stage.
- Every stage is independently testable.
- Every stage has defined contracts.
- Business logic never crosses stage boundaries.