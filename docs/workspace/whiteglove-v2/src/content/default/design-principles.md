---
title: Design Principles
icon: PenTool
category: Design
order: 1
description: Core philosophy behind the AiAssist user experience.
---

# AiAssist - Design Documentation

## Overview

AiAssist is an AI-as-a-Service platform that enables businesses and developers to integrate AI consulting capabilities into their applications. Users can sign up, manage their AI knowledge base, generate API keys, and access AI through both the web interface and programmatic API.

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│                  Port 5000 (via Express)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Express Proxy Server (Port 5000)               │
│         - Serves static files                               │
│         - Proxies /api/* and /socket.io to FastAPI          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
│         - Authentication & Authorization                    │
│         - Business Logic                                    │
│         - AI Orchestration                                  │
│         - WebSocket (Socket.IO)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│     Redis       │     │    Groq API     │
│  (All Data)     │     │   (LLM Calls)   │
└─────────────────┘     └─────────────────┘
```
