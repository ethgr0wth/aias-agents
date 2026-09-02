---
title: Memory Architecture
icon: Database
category: Memory
order: 2
description: Technical specs for vector-based long-term memory.
---

# Memory Architecture

> Lightweight, Production-Safe Context Management for Multi-Provider AI

**Status:** Design Specification  
**Last Updated:** December 2024  
**Author:** AiAssist Secure Engineering

---

## Executive Summary

This document describes a conversation-aware memory system that enhances AI response quality without adding significant complexity or cost. The system uses a **two-lane architecture**:

1. **Short-Term Buffer** — Last N turns injected directly (no embeddings)
2. **Session Memory** — Extracted facts/constraints stored per session

**Net result:** Higher quality answers, fewer clarification loops, lower operational cost.

---

## Core Architecture

### Two Memory Lanes

```
┌─────────────────────────────────────────────────────────────┐
│                    CONVERSATION MEMORY                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────────────┐    ┌──────────────────────────┐  │
│   │   SHORT-TERM BUFFER  │    │    SESSION MEMORY        │  │
│   │   (Lane 1)           │    │    (Lane 2)              │  │
│   ├──────────────────────┤    ├──────────────────────────┤  │
│   │ • Last N turns       │    │ • Extracted facts        │  │
│   │ • Verbatim messages  │    │ • User preferences       │  │
│   │ • No embeddings      │    │ • Constraints/decisions  │  │
│   │ • Always injected    │    │ • Embedded (optional)    │  │
│   │ • Fast, cheap        │    │ • Retrieved when relevant│  │
│   └──────────────────────┘    └──────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Lane 1: Short-Term Buffer

**Purpose:** Immediate conversational context

| Property | Value |
|----------|-------|
| Storage | Redis sorted set (existing) |
| Retention | Last 10-20 turns |
| Format | Verbatim messages |
| Injection | Always, directly into prompt |
| Cost | Zero additional API calls |

### Lane 2: Session Memory

**Purpose:** Accumulated knowledge that transcends individual turns

| Property | Value |
|----------|-------|
| Storage | Redis hash per session |
| Retention | Session lifetime (configurable TTL) |
| Format | Structured facts list |
| Injection | Prepended to system prompt |
| Cost | One cheap extraction call per AI response |

---

## Memory Visibility Contract

> **Assistant must not enumerate or expose memory unless explicitly asked.**

**Rules:**
1. Never proactively mention what facts are stored
2. Never reveal confidence scores to users
3. Never expose metadata (turn numbers, timestamps)
4. Only reference stored facts when contextually relevant

**System Prompt Guard:**
```
MEMORY VISIBILITY RULES:
- Do not mention "I remember that..." or "Based on our previous conversation..."
- Do not list stored preferences or constraints unless the user asks
- Reference context naturally without citing the memory system
- Never reveal confidence levels or extraction metadata
```

---

## Feature Toggle

> **ConversationMemory is opt-in, not opt-out.** Clients decide whether to enable this feature.

### Design Principles

1. **Non-mandatory dependency** — Disabled by default, zero impact when off
2. **Workspace-level control** — Each workspace independently enables/disables
3. **Organization defaults** — Organizations can set default for new workspaces
4. **Graceful degradation** — When disabled, all memory operations are skipped silently

---

## Prompt Assembly Order

> **Critical:** The order of context injection directly affects hallucination rate, instruction-following, and cross-provider consistency.

### Assembly Sequence

1. **SYSTEM DIRECTIVES** (persona, constraints, guards)
2. **SESSION MEMORY** (extracted context, decisions)
3. **SHORT-TERM BUFFER** (last N turns, verbatim)
4. **USER QUESTION** (newest message)

### Source-of-Truth Invariant

> **Critical Policy:** This invariant MUST be preserved in all future extensions (RAG, tools, agents).

- **System Directives** are the highest authority
- **Session Memory** may inform responses but may **never override** system constraints or safety rules
- If a conflict exists between session memory and system directives, the system directive **silently wins**
