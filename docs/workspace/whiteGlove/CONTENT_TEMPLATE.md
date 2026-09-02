# WhiteGlove Content Template

Copy this template to create new content pages.

## File Location

Save your `.md` files to: `whiteGlove/src/content/`

---

## Template

```markdown
---
title: Page Title Here
icon: Sparkles
description: Brief description for the card (keep under 60 chars)
category: Category Name
order: 1
---

## First Section

Your content starts here. Use standard Markdown formatting.

### Subsection

- Bullet points work
- As do numbered lists

1. First item
2. Second item

### Tables

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data | Data | Data |

### Code Blocks

```javascript
const example = "syntax highlighted"
```

### Blockquotes

> Important callouts render nicely

### Links

[Link text](https://example.com)

---

## Another Section

Content continues...
```

---

## Available Icons

Use any of these Lucide icon names:

| Icon | Use Case |
|------|----------|
| `Sparkles` | Features, highlights |
| `Layers` | Architecture, structure |
| `Blocks` | Components, building |
| `DollarSign` | Pricing, money |
| `HelpCircle` | FAQ, help |
| `Wrench` | Setup, configuration |
| `LayoutList` | Plans, lists |
| `Zap` | Performance, speed |
| `Shield` | Security, protection |
| `Code` | Developer, technical |
| `Users` | Team, community |
| `Settings` | Configuration |
| `Globe` | Global, web |
| `Lock` | Privacy, auth |
| `Rocket` | Launch, deploy |
| `BookOpen` | Docs, learning |
| `MessageSquare` | Chat, communication |
| `Terminal` | CLI, commands |
| `Database` | Data, storage |
| `Key` | API keys, secrets |
| `Cpu` | Processing, compute |
| `Cloud` | Cloud, hosting |

---

## Categories

Group related content by category. Current categories:

- `Getting Started` - Onboarding, setup, basics
- `Technical` - Architecture, deep dives
- `Business` - Pricing, plans, FAQ

Create new categories as needed - they auto-group in the directory.

---

## Order

The `order` field determines sort position within a category.
Lower numbers appear first (1, 2, 3...).
