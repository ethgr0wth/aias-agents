---
title: Conversation Memory
icon: CircuitBoard
category: Memory
order: 1
description: How AiAssist remembers context across conversations.
---

# How AiAssist Remembers Your Conversations

> A Simple Guide to Understanding AI Memory

**Written for:** Anyone curious about how our AI remembers things  
**No programming experience required**

---

## Table of Contents

1. [The Problem: Why AI Forgets](#the-problem-why-ai-forgets)
2. [Our Solution: Two-Lane Memory](#our-solution-two-lane-memory)
3. [Lane 1: Short-Term Buffer (Recent Chat)](#lane-1-short-term-buffer-recent-chat)
4. [Lane 2: Session Memory (Important Facts)](#lane-2-session-memory-important-facts)
5. [How It All Works Together](#how-it-all-works-together)
6. [Who Gets Their Own Memory?](#who-gets-their-own-memory)
7. [Privacy & Safety Features](#privacy--safety-features)
8. [For Developers: Code Examples](#for-developers-code-examples)
9. [Frequently Asked Questions](#frequently-asked-questions)

---

## The Problem: Why AI Forgets

Imagine you're talking to someone who forgets everything you said after each sentence. That would be frustrating, right?

**Traditional AI chatbots have this exact problem.** When you say:

> "I'm a vegetarian, and I need dinner ideas"

A forgetful AI might later suggest:

> "How about a nice steak dinner?"

That's not helpful! The AI forgot you're vegetarian.

### The Challenge

AI models like GPT-4 or Llama don't have permanent memory built in. Each time they respond, they only see what's directly in front of them—like reading a single page of a book without knowing what came before.

Our job is to give them the right "pages" so they can respond intelligently.

---

## Our Solution: Two-Lane Memory

Think of our memory system like a person's brain:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI'S MEMORY SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   🧠 LANE 1: Short-Term Buffer    🗃️ LANE 2: Session Memory  │
│   ─────────────────────────────   ───────────────────────── │
│                                                              │
│   Like working memory:            Like a notebook:           │
│   • What we just talked about     • Important facts saved    │
│   • Last 10-20 messages           • "User is vegetarian"     │
│   • Exact words you used          • "Prefers Python"         │
│   • Always included               • Decisions you've made    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Two Lanes?

**Lane 1 (Short-Term)** is fast and cheap. We just show the AI your recent messages—no processing needed.

**Lane 2 (Session Memory)** is smarter. We extract the *important stuff* from conversations and save it separately, so even if your recent messages scroll away, the AI still knows key facts about you.

---

## Lane 1: Short-Term Buffer (Recent Chat)

### What Is It?

The short-term buffer is simply **your last 10-20 messages**, shown directly to the AI.

### How It Works

```
You: "I'm planning a trip to Japan"
AI: "That sounds exciting! When are you thinking of going?"
You: "Probably next spring"
AI: "Spring in Japan is beautiful—cherry blossom season!"
You: "What cities should I visit?"

↓ AI sees all of this ↓

AI: "Since you're going in spring, I'd recommend Tokyo for the 
     cherry blossoms in Shinjuku Gyoen, then Kyoto for..."
```

The AI remembers you said "Japan" and "spring" because those messages are right there in the conversation.

### Real-Life Analogy

Imagine you're having a phone call. You naturally remember what was said in the last few minutes. You don't need to write it down—it's fresh in your mind.

That's what the short-term buffer does for the AI.

### Technical Details (for the curious)

- **Storage:** Messages are stored in Redis (a fast database)
- **Limit:** Typically 10-20 recent turns
- **Cost:** Free! No extra AI calls needed
- **Speed:** Instant—just loads the messages

---

## Lane 2: Session Memory (Important Facts)

### What Is It?

Session memory is like a **smart notebook** that automatically writes down important things you mention.

### How It Works

After each conversation turn, a small helper AI reads through what was said and picks out facts worth remembering:

```
┌────────────────────────────────────────────────────────────┐
│                     FACT EXTRACTION                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Conversation:                                              │
│  You: "I'm a Python developer working on machine learning  │
│        projects. I prefer VS Code and usually work on Mac." │
│                                                             │
│  AI: "Great! Let me help with your ML setup..."            │
│                                                             │
│  ↓ Extracted Facts ↓                                        │
│                                                             │
│  📝 "User is a Python developer"                            │
│  📝 "User works on machine learning projects"               │
│  📝 "User prefers VS Code as their editor"                  │
│  📝 "User works on Mac"                                     │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Types of Facts We Remember

| Category | Examples | Priority |
|----------|----------|----------|
| **Decisions** | "User chose React for their project" | Highest |
| **Constraints** | "Budget is under $500" | High |
| **Preferences** | "Prefers dark mode" | Medium |
| **Context** | "User is planning a wedding" | Lower |

We prioritize decisions and constraints because they directly affect advice we give.

### Real-Life Analogy

Imagine a helpful assistant who takes notes during your meetings. They don't write down every word—just the important stuff:

- "Client wants blue, not green"
- "Deadline is Friday"
- "Budget approved for $10,000"

Later, even if you forget what was discussed, your assistant has the key points.

---

## How It All Works Together

Here's what happens when you send a message:

```
┌─────────────────────────────────────────────────────────────┐
│                    MESSAGE FLOW                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Step 1: You send a message                                 │
│   ─────────────────────────                                  │
│   "What Python library should I use for data analysis?"      │
│                                                              │
│   Step 2: We prepare the AI's context                        │
│   ─────────────────────────────────                          │
│   ┌──────────────────────────────────────────────────────┐   │
│   │ System Instructions:                                  │   │
│   │ "You are a helpful coding assistant..."               │   │
│   │                                                       │   │
│   │ [Session Memory]                                      │   │
│   │ - User is a Python developer                          │   │
│   │ - User works on machine learning projects             │   │
│   │ - User prefers VS Code on Mac                         │   │
│   │                                                       │   │
│   │ [Recent Conversation]                                 │   │
│   │ User: "I'm starting a new data project"               │   │
│   │ AI: "Great! What kind of data will you work with?"    │   │
│   │ User: "What Python library should I use for..."       │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                              │
│   Step 3: AI generates a personalized response               │
│   ────────────────────────────────────────────               │
│   "For a Python ML developer like yourself, I'd recommend    │
│    Pandas for data analysis. It integrates well with your    │
│    existing ML workflow..."                                  │
│                                                              │
│   Step 4: We extract new facts (in background)               │
│   ────────────────────────────────────────────               │
│   📝 New fact: "User is starting a new data project"         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### The Magic: Prompt Assembly

Before the AI responds, we assemble everything in a specific order:

1. **System instructions** (who the AI should be)
2. **Session memory** (important facts about you)
3. **Recent messages** (what we just discussed)
4. **Your current question**

This order matters! The AI pays most attention to what comes last, but the context from session memory helps it give personalized answers.

---

## Who Gets Their Own Memory?

Different people get different memory spaces. We don't mix up one person's facts with another's!

### Memory Scopes

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY SCOPES                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   👤 USER SCOPE (Default)                                    │
│   ───────────────────────                                    │
│   Each logged-in user has their own private memory.          │
│   Your preferences stay yours.                               │
│                                                              │
│   🏢 WORKSPACE SCOPE                                         │
│   ───────────────────                                        │
│   Team members share facts in a workspace.                   │
│   Good for: "Our company uses PostgreSQL"                    │
│                                                              │
│   💬 CONVERSATION SCOPE                                      │
│   ──────────────────────                                     │
│   Memory only lasts for one chat session.                    │
│   When you close the chat, facts are cleared.                │
│                                                              │
│   📧 LEAD SCOPE (Anonymous + Email)                          │
│   ────────────────────────────────                           │
│   Website visitor who gave their email.                      │
│   Memory persists so they get a consistent experience.       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### How We Decide Your Scope

```
If you're logged in:
   → You get USER scope (private memory)

Else if you gave your email (lead capture):
   → You get LEAD scope (persistent across visits)

Else (anonymous visitor):
   → You get CONVERSATION scope (temporary)
```

---

## Privacy & Safety Features

We take privacy seriously. Here's how we protect you:

### 1. PII Filtering

We automatically filter out personal identifiable information before saving facts:

| Blocked | Example |
|---------|---------|
| Email addresses | `john@email.com` |
| Phone numbers | `555-123-4567` |
| Credit cards | `4111-1111-1111-1111` |
| Social Security | `123-45-6789` |

### 2. Confidence Threshold

We only save facts the AI is confident about (75%+ confidence). Uncertain guesses are discarded.

### 3. Memory Limits

Each session stores a maximum of 15 facts. When you hit the limit, oldest and least important facts are removed.

### 4. Kill Switch

We can instantly disable fact extraction globally if something goes wrong—no restart needed.

### 5. Memory Is Invisible

The AI never says things like "I remember you told me..." or lists what it knows about you. It uses the information naturally, just like a person would.

---

## For Developers: Code Examples

### How Fact Extraction Works

When a conversation turn happens, we call a small helper AI to extract facts:

```python
# The prompt we send to extract facts
EXTRACTION_PROMPT = """
You are a context extraction system. Analyze the conversation turn 
and extract factual information that should be remembered.

Extract ONLY concrete facts, preferences, constraints, or decisions.

PRIVACY RULES:
- Do NOT extract email addresses, phone numbers, or URLs
- Do NOT extract names of individuals
- Extract preferences abstractly

Output format (one per line):
CATEGORY|CONFIDENCE|FACT

Categories:
- preference: User's stated preferences
- constraint: Limitations or requirements
- decision: Choices that have been made
- context: Background information

Example output:
preference|0.9|User prefers Python for backend development
constraint|0.95|Budget is limited to $5,000
decision|0.85|Will use PostgreSQL instead of MongoDB

If no extractable facts, output: NONE
"""
```

The AI returns simple pipe-delimited lines that we parse:

```
preference|0.92|User is a vegetarian
context|0.88|User is planning a trip to Japan
decision|0.95|User chose React over Vue
```

### Session Fact Data Structure

```python
@dataclass
class SessionFact:
    content: str           # "User prefers Python"
    category: str          # preference, constraint, decision, context
    confidence: float      # 0.0 to 1.0
    turn_number: int       # When this was learned
    created_at: datetime   # Timestamp
```

### How Facts Are Stored in Redis

```python
# Session key format
session_key = f"aai:session:{workspace_id}:{user_id}"

# Facts stored as hash
{
    "fact_abc123": {
        "content": "User is a Python developer",
        "category": "context",
        "confidence": 0.95,
        "turn_number": 3
    },
    "fact_def456": {
        "content": "User prefers dark mode",
        "category": "preference", 
        "confidence": 0.88,
        "turn_number": 7
    }
}

# TTL: 7 days by default
```

### How Session Memory Is Injected

```python
async def generate_response(workspace_id: str, message: str):
    # 1. Check if memory is enabled for this workspace
    workspace = storage.get_workspace(workspace_id)
    memory_enabled = workspace.conversation_memory_enabled
    
    # 2. Get session facts if memory is enabled
    session_facts = []
    if memory_enabled:
        session_id = get_session_id(workspace_id, user_id)
        session_facts = await memory.get_session_facts(session_id)
    
    # 3. Build the prompt
    system_prompt = get_base_prompt(workspace)
    
    if session_facts:
        # Add facts to the prompt
        memory_block = memory.format_session_memory(session_facts)
        system_prompt += f"\n\n{memory_block}"
    
    # 4. Get recent messages (short-term buffer)
    recent_messages = storage.get_messages(workspace_id, limit=20)
    
    # 5. Call the AI
    response = await ai.chat(
        system=system_prompt,
        messages=recent_messages + [{"role": "user", "content": message}]
    )
    
    # 6. Extract new facts in background (doesn't slow down response)
    if memory_enabled:
        asyncio.create_task(
            memory.extract_and_store_facts(session_id, message, response)
        )
    
    return response
```

### Enabling Memory for a Workspace

```python
# Via API
PATCH /api/workspaces/{workspace_id}/settings
{
    "conversation_memory_enabled": true
}

# In Python
workspace.conversation_memory_enabled = True
storage.save_workspace(workspace)
```

### Buffer Compression (For Long Conversations)

When conversations get long, we compress older messages into a summary:

```python
# Before compression:
messages = [
    {"role": "user", "content": "Hello, I need help with Python"},
    {"role": "assistant", "content": "Hi! I'd be happy to help..."},
    # ... 20 more messages ...
    {"role": "user", "content": "What about async functions?"},
]

# After compression:
messages = [
    {"role": "system", "content": "[Earlier: User asked about Python basics, we covered variables, functions, and loops]"},
    {"role": "user", "content": "What about async functions?"},  # Recent messages preserved
]
```

This keeps the conversation within token limits while preserving important context.

---

## Frequently Asked Questions

### Q: Does the AI remember me forever?

**A:** No. Session memory typically expires after 7 days of inactivity. Your recent chat (short-term buffer) only includes the last 10-20 messages.

### Q: Can I delete my memory?

**A:** Yes! You can clear your session memory at any time. Contact support or (if you're a developer) call the API endpoint to purge your session.

### Q: Does everyone see my facts?

**A:** No. By default, your facts are private to you (USER scope). Only you can see them. Workspace-scoped memory is an opt-in feature for teams.

### Q: Will the AI say "I remember you..."?

**A:** No. The AI is instructed to never explicitly mention the memory system. It uses the information naturally without calling attention to it.

### Q: Does memory work with all AI providers?

**A:** Yes! We support Groq, OpenAI, Anthropic, Google Gemini, and Mistral. Each uses slightly different models for fact extraction, but the result is the same.

### Q: Does memory slow down responses?

**A:** No. Fact extraction happens *after* you receive your response, in the background. Loading existing facts takes only a few milliseconds.

### Q: Can I turn memory off?

**A:** Yes. Memory is opt-in per workspace. You or your admin can disable it anytime.

---

## Summary

Our conversation memory system helps AI give better, more personalized responses by:

1. **Short-Term Buffer** - Keeping your recent messages visible to the AI
2. **Session Memory** - Saving important facts you mention

This two-lane approach is:
- **Fast** - No slowdown in responses
- **Cheap** - Uses small, efficient AI models for extraction
- **Private** - Your facts are yours alone
- **Smart** - Prioritizes decisions and constraints over casual context

The result? An AI that feels like it actually *knows* you, without being creepy about it.
