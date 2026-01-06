---
title: "Building a Resilient AI Medical Assistant: Architecture & Status"
date: "2026-01-05"
summary: "An overview of the Doctors Assistant stack, featuring a robust FastAPI backend, a multi-provider AI fallback system, and a secure, layered architecture."
tags: [Architecture, FastAPI, PydanticAI, AI Agents, Healthcare]
---

## The Mission

The **Doctors Assistant** project aims to solve a critical problem in modern healthcare: administrative burnout. By providing an intelligent, AI-powered system that handles patient visit summarization, Q&A, and data management, we empower doctors to focus less on paperwork and more on their patients. This isn't just a CRUD app; it's a context-aware assistant that understands medical data.

## The Tech Stack

We chose a stack that prioritizes **type safety**, **speed**, and **reliability**.

- **Backend:** **FastAPI**. We needed the speed of Starlette and the developer experience of automatic Pydantic validation. The auto-generated OpenAPI docs are indispensable for our frontend team.
- **AI & Logic:** **PydanticAI**. We needed structured output from our LLMs, not just raw text. PydanticAI gives us validation loops that ensure the AI speaks our schema's language.
- **AI Providers:** A multi-tiered implementation using **X.AI (Grok-3)** for speed/cost, falling back to **GPT-4** and **Claude 3.5 Sonnet** for complex reasoning.
- **Database:** **PostgreSQL** with **SQLAlchemy (Async)**. We require ACID transactions and reliable relational data storage, especially for HIPAA compliance.
- **Frontend:** **React** with **ReactMarkdown**. We render complex medical data (tables, lists) server-side into Markdown to ensure consistency across web and mobile clients.

## Core Architecture

Our architecture is built on the "Separation of Concerns" principle, ensuring that our AI logic doesn't bleed into our HTTP handlers.

### 1. The Fallback Agent Pattern

One of our most interesting architectural decisions is the `FallbackAgent`. In healthcare, downtime isn't an option. We implemented a system that attempts to generate a response using our primary, cost-effective model (Grok-3). If that fails or times out, it seamlessly retries with GPT-4, and finally Claude. This gives us the best of both worlds: low average latency/cost and high reliability.

### 2. Server-Side Data Formatting

Instead of sending raw JSON to the frontend and forcing them to figure out how to display a "High Stage 2" blood pressure, we use a `MedicalDataFormatter` service. This service takes raw values and returns standardized, GitHub-Flavored Markdown (GFM) tables with status indicators (e.g., "🔴 High"). This ensures that an AI summarizing a chart and a doctor viewing a dashboard see the _exact same_ representation of the data.

### 3. Async-First Service Layer

We use a dedicated Service Layer that handles all business logic. It's fully async, allowing our API to handle concurrent requests efficiently—crucial when waiting on external LLM APIs.

## Current Challenges

**Dockerizing the Persistence Layer**
Our biggest recent hurdle was moving from a local "it works on my machine" setup to a production-ready Docker environment. We faced two main issues:

1.  **Migration Amnesia:** Our initial Alembic migrations worked locally but failed in Docker because they relied on a pre-existing state. We had to rewrite our migration history to ensure a deterministic path from an empty DB to the current schema.
2.  **Environment Variable Wars:** Docker Compose and local `.env` files fought for control over the `DATABASE_URL`. We solved this by refactoring our config loader to build connection strings dynamically from individual components (`POSTGRES_USER`, `HOST`, etc.), ensuring the container always respects its isolated environment.

---

_Next up: Integrating the voice-to-text pipeline for real-time consultation transcription._
