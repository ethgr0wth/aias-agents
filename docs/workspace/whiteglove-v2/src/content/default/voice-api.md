---
title: Voice API
icon: Mic
category: Developers
order: 6
description: API reference for TTS and speech-related endpoints.
---

# Voice API Reference

**Version:** 1.0  
**Base URL:** `https://your-domain.com/api`  
**Authentication:** API Key (Bearer token)

## Overview

The Voice API provides text-to-speech synthesis and intelligent content processing through voice action endpoints. All endpoints require an active subscription and API key authentication.

## Authentication

Include your API key in the Authorization header:

```
Authorization: Bearer aai_your_api_key_here
```

API keys can be generated from the Dashboard under "API Keys". Both standard (`aai_`) and extended (`aai_pub_`, `aai_srv_`) keys are supported.

---

## Text-to-Speech Endpoints

### Synthesize Speech

Convert text to audio using Google Cloud TTS.

**Endpoint:** `POST /api/tts/synthesize`

**Request Body:**
```json
{
  "text": "Hello, this is a test message.",
  "voice_id": "en-US-Chirp3-HD-Puck",
  "speaking_rate": 1.0,
  "pitch": 0.0
}
```

### List Available Voices

Get all available TTS voices.

**Endpoint:** `GET /api/tts/voices`

---

## Voice Action Endpoints

Intelligent content processing with optional TTS response.

### Common Request Structure

```json
{
  "content": "The main content to process",
  "context": ["Optional array of previous messages for context"],
  "include_audio": true,
  "voice_id": "en-US-Chirp3-HD-Puck"
}
```

### Explain Content

Transform raw input into clear, understandable explanation.

**Endpoint:** `POST /api/voice/actions/explain`

### Summarize Content

Reduce content to key points and essential information.

**Endpoint:** `POST /api/voice/actions/summarize`

### Extract Action Items

Identify tasks, to-dos, and actionable items from content.

**Endpoint:** `POST /api/voice/actions/extract-actions`

### Decision Recommendation

Analyze content and provide structured decision guidance.

**Endpoint:** `POST /api/voice/actions/decision`

---

## BYOK Credentials Endpoints

Manage your own Google Cloud TTS credentials.

### Add Google TTS Credentials

**Endpoint:** `POST /api/user/provider-keys/google-tts`

### Check Credentials Status

**Endpoint:** `GET /api/user/provider-keys/google-tts`

### Remove Credentials

**Endpoint:** `DELETE /api/user/provider-keys/google-tts`
