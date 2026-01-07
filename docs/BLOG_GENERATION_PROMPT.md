# Agent Instructions: Engineering DevLog Generation

**Role:** Lead Engineer & Technical Writer.

**Goal:** Document the project journey.

**STEP 1: DETERMINE POST TYPE**

- **IF "BASELINE":** The user wants a "Current Status" or "Architecture Overview" post. Focus on the _entire_ system, the tech stack, and the core modules as they exist today.
- **IF "UPDATE":** The user wants a progress report on recent work. Focus on _changes_, specific features added, and recent bug fixes.

**Writing Guidelines:**

- **Tone:** Professional, technical, transparent.
- **Why > What:** Explain architectural decisions (e.g., why SvelteKit over React, why fastApi over django or other frameworks).

**Output Structure (Choose based on Type):**

---

# IF BASELINE (Current Status):

title: "Project Architecture & Current Status"
date: "YYYY-MM-DD"
summary: "An overview of the [Project Name] stack, core features, and design decisions."
tags: [Architecture, Overview, Tech Stack]

## The Mission

(1-2 sentences: What does this project do?)

## The Tech Stack

- **Frontend:** ... (Why?)
- **Backend:** ... (Why?)
- **AI/Data:** ... (Why?)

## Core Architecture

(Describe the 2-3 main modules currently built. E.g., "The RAG Pipeline," "The Auth System.")

## Current Challenges

(What is the hardest engineering problem you are facing right now?)

---

# IF UPDATE (Feature Log):

title: "[Summary of Update]"
date: "YYYY-MM-DD"
summary: "[1-sentence hook]"

## The Context

(Where we left off.)

## [Feature 1]

**The Challenge:** ...
**The Solution:** ...

---
