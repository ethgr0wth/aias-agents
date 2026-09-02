# AiAssist BYOK Blog Platform — Comprehensive Work Plan
**Version:** 1.0  
**Date:** December 20, 2025  
**Codename:** Project Lighthouse 🏠

---

## Executive Summary

Transform AiAssist from an AI chat tool into a **BYOK AI Content Infrastructure Platform** — enabling users to generate, publish, and distribute AI-powered blog content using their own AI keys, on their own domains, via embeddable widgets across any web platform.

**Vision:** Become the WordPress of AI-powered content — where anyone can spin up an AI blog in minutes, own their content, control their AI costs, and embed anywhere.

**Core Value Proposition:** AiAssist is not just an AI platform — it is the security and cost-control layer that makes AI safe to deploy in production. Billing-linked API keys are never exposed to client-side code under any circumstances.

---

## 1. Strategic Goals

| Goal | Success Metric | Target |
|------|---------------|--------|
| Multi-tenant adoption | Active tenants with blogs | 100 in 90 days |
| BYOK activation | % of blogs using own keys | 60%+ |
| Widget distribution | Embeds deployed | 500+ |
| Content velocity | Posts generated/month | 10,000+ |
| Platform stickiness | 30-day retention | 40%+ |

---

## 2. Platform Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ACCESS LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Custom Domain          │  Platform Subdomain    │  Widget Embeds       │
│  blog.company.com       │  company.aiassist.blog │  <script> / React    │
└───────────┬─────────────┴──────────┬─────────────┴──────────┬───────────┘
            │                        │                        │
            ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ROUTING LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Domain Router          │  Slug Resolver         │  Widget Gateway      │
│  (DNS + SSL)            │  (tenant/blog lookup)  │  (embed API)         │
└───────────┬─────────────┴──────────┬─────────────┴──────────┬───────────┘
            │                        │                        │
            ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONTENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Blog Engine            │  Post Manager          │  Asset Manager       │
│  (settings, SEO, theme) │  (draft/publish/sched) │  (images, media)     │
└───────────┬─────────────┴──────────┬─────────────┴──────────┬───────────┘
            │                        │                        │
            ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GENERATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  AI Orchestrator        │  Execution Gateway     │  Brand Voice Engine  │
│  (prompts, templates)   │  (policy + enforce)    │  (tone, style, mem)  │
└───────────┬─────────────┴──────────┬─────────────┴──────────┬───────────┘
            │                        │                        │
            ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PLATFORM LAYER (Existing)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Workspaces     │  Provider Settings   │  API Keys      │  Auth        │
│  (tenant scope) │  (Primary/Fallback)  │  (aai_ keys)   │  (sessions)  │
└─────────────────┴──────────────────────┴────────────────┴──────────────┘
```

### 2.2 Multi-Tenant Data Model

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Tenant      │       │      Blog       │       │      Post       │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │──┐    │ id (PK)         │
│ userId (FK)     │  │    │ tenantId (FK)   │◄─┘    │ blogId (FK)     │◄─┐
│ name            │  │    │ slug (unique)   │       │ slug (unique/bg)│  │
│ plan            │  │    │ title           │       │ title           │  │
│ createdAt       │  │    │ description     │       │ content (JSON)  │  │
└─────────────────┘  │    │ theme           │       │ status          │  │
                     │    │ seoConfig       │       │ seoMeta         │  │
                     │    │ brandVoice      │       │ generationMeta  │  │
                     │    │ settings        │       │ scheduledAt     │  │
                     └───►│ createdAt       │       │ publishedAt     │  │
                          └─────────────────┘       │ createdAt       │  │
                                   │                └─────────────────┘  │
                                   │                                     │
                          ┌────────┴────────┐                           │
                          ▼                 ▼                           │
                ┌─────────────────┐ ┌─────────────────┐                 │
                │  BlogDomain     │ │  WidgetConfig   │                 │
                ├─────────────────┤ ├─────────────────┤                 │
                │ id (PK)         │ │ id (PK)         │                 │
                │ blogId (FK)     │ │ blogId (FK)     │                 │
                │ hostname        │ │ embedToken      │                 │
                │ type (sub/cust) │ │ allowedOrigins  │                 │
                │ sslStatus       │ │ theme           │                 │
                │ verifiedAt      │ │ settings        │                 │
                └─────────────────┘ └─────────────────┘                 │
                                                                        │
                ┌───────────────────────────────────────────────────────┘
                ▼
        ┌─────────────────┐
        │  PostGeneration │
        ├─────────────────┤
        │ id (PK)         │
        │ postId (FK)     │
        │ provider        │
        │ model           │
        │ prompt          │
        │ tokensUsed      │
        │ latencyMs       │
        │ createdAt       │
        └─────────────────┘
```

### 2.3 Integration Points with Existing AiAssist

| Existing Feature | Blog Platform Integration |
|------------------|---------------------------|
| **Workspaces** | Each blog maps to a workspace for access control |
| **Provider Settings** | Blog generation uses tenant's Primary/Fallback providers |
| **API Keys** | Widget embeds use CLIENT-scoped keys (`aai_pub_`) with domain + feature restrictions |
| **User Roles** | Map to blog roles (Owner, Editor, Viewer) |
| **Directives** | Become "Brand Voice" templates for content |

### 2.4 Tenant Strategy: Reuse Workspaces

**Decision:** Rather than creating a separate `blogTenants` table, blogs will be owned by existing workspaces. This:
- Avoids authorization drift
- Leverages existing access control
- Simplifies the data model

```
Workspace (existing)
    │
    ├── blogs[]        # New: blogs owned by this workspace
    ├── contacts[]     # Existing
    ├── messages[]     # Existing
    └── directives[]   # Existing (reused as brand voice)
```

The `userId` field on blogs provides a quick lookup, but `workspaceId` is the authorization boundary.

### 2.5 Asset Storage Strategy

**Decision:** Use Replit's Object Storage for media assets.

### 2.6 API Key Security Model

AiAssist supports three distinct API key types with different security profiles:

| Key Type | Prefix | Usage Context | Security Model |
|----------|--------|---------------|----------------|
| **STANDARD** | `aai_` | Server-only | Full access, never expose to browsers |
| **CLIENT** | `aai_pub_` | Browser-safe | Domain-restricted + feature-scoped |
| **SERVER** | `aai_srv_` | Backend services | Explicit server context (future) |

**Why CLIENT Keys Are Safe in Browsers:**
- **Domain Restriction**: Keys are bound to specific allowed origins; requests from unauthorized domains are rejected server-side
- **Feature Scoping**: Keys are limited to specific capabilities (e.g., `blog.read`, `blog.embed`)
- **No Billing Access**: CLIENT keys cannot access billing, subscription, or account management features
- **Instant Revocation**: Keys can be revoked immediately with zero grace period
- **Server-Side Enforcement**: All validation happens on AiAssist's Execution Gateway, not in client code

**Feature Scopes for Blog Platform:**
```
blog.read        # Read published blog content
blog.generate    # Generate new blog posts (requires session)
blog.embed       # Embed widget capabilities
seo.generate     # Generate SEO metadata
```

**Widget Authentication Model:**
Widgets use a two-key authentication approach:
1. `embedToken` → Identifies the specific blog/content to display
2. `aai_pub_` key → Authorizes API capabilities for that embed

**Important:** BYOK Blog supports client-side usage via scoped public keys. BYOK Chat requires additional session constraints and is treated separately.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Asset Pipeline                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Upload                    Storage              Delivery        │
│  ┌──────────┐             ┌──────────┐         ┌──────────┐   │
│  │ Post     │────────────▶│ Replit   │────────▶│ CDN Edge │   │
│  │ Editor   │  resize/    │ Object   │  cache  │ Delivery │   │
│  └──────────┘  optimize   │ Storage  │         └──────────┘   │
│                           └──────────┘                         │
│                                                                 │
│  Supported: JPEG, PNG, WebP, GIF (max 5MB)                     │
│  Auto-optimization: WebP conversion, resize to max 1920px      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Storage Schema:**
- Path format: `blogs/{blogId}/posts/{postId}/{filename}`
- Cleanup: Delete assets when post is deleted
- CDN: Serve via platform CDN with cache headers

---

## 3. Phase 1 — Foundation MVP (Weeks 1-3)

### 3.1 Database Schema

**New Tables:**

```typescript
// shared/schema.ts additions

// NOTE: Blogs attach to existing workspaces - no separate tenant table needed
// The workspace provides: userId (owner), access control, and existing infra

export const blogs = pgTable("blogs", {
  id: text("id").primaryKey(),
  workspaceId: text("workspace_id").notNull(), // FK to workspace
  userId: text("user_id").notNull(), // Denormalized for quick lookup
  slug: text("slug").notNull(),
  title: text("title").notNull(),
  description: text("description"),
  theme: text("theme").default("default"),
  seoConfig: jsonb("seo_config").default({}),
  brandVoice: jsonb("brand_voice").default({}),
  settings: jsonb("settings").default({}),
  status: text("status").default("active"), // active, paused, archived
  createdAt: timestamp("created_at").defaultNow(),
});

export const blogPosts = pgTable("blog_posts", {
  id: text("id").primaryKey(),
  blogId: text("blog_id").references(() => blogs.id),
  slug: text("slug").notNull(),
  title: text("title").notNull(),
  excerpt: text("excerpt"),
  content: jsonb("content").notNull(), // structured content blocks
  contentHtml: text("content_html"), // rendered HTML for fast serving
  seoMeta: jsonb("seo_meta").default({}),
  featuredImage: text("featured_image"),
  tags: text("tags").array(),
  status: text("status").default("draft"), // draft, scheduled, published, archived
  generationMeta: jsonb("generation_meta").default({}),
  scheduledAt: timestamp("scheduled_at"),
  publishedAt: timestamp("published_at"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const blogDomains = pgTable("blog_domains", {
  id: text("id").primaryKey(),
  blogId: text("blog_id").references(() => blogs.id),
  hostname: text("hostname").unique().notNull(),
  type: text("type").default("subdomain"), // subdomain, custom
  sslStatus: text("ssl_status").default("pending"), // pending, active, failed
  verificationToken: text("verification_token"),
  verifiedAt: timestamp("verified_at"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const widgetConfigs = pgTable("widget_configs", {
  id: text("id").primaryKey(),
  blogId: text("blog_id").references(() => blogs.id),
  embedToken: text("embed_token").unique().notNull(),
  allowedOrigins: text("allowed_origins").array().default([]),
  theme: jsonb("theme").default({}),
  settings: jsonb("settings").default({}),
  createdAt: timestamp("created_at").defaultNow(),
});

export const postGenerations = pgTable("post_generations", {
  id: text("id").primaryKey(),
  postId: text("post_id").references(() => blogPosts.id),
  provider: text("provider").notNull(),
  model: text("model").notNull(),
  prompt: text("prompt"),
  systemPrompt: text("system_prompt"),
  tokensInput: integer("tokens_input"),
  tokensOutput: integer("tokens_output"),
  latencyMs: integer("latency_ms"),
  status: text("status").default("completed"), // completed, failed
  error: text("error"),
  createdAt: timestamp("created_at").defaultNow(),
});
```

### 3.2 Backend API Routes

**Blog Management:**
```
POST   /api/blog/tenants                    # Create tenant
GET    /api/blog/tenants/:id                # Get tenant
PUT    /api/blog/tenants/:id                # Update tenant
DELETE /api/blog/tenants/:id                # Delete tenant

POST   /api/blog/blogs                      # Create blog
GET    /api/blog/blogs                      # List user's blogs
GET    /api/blog/blogs/:id                  # Get blog
PUT    /api/blog/blogs/:id                  # Update blog
DELETE /api/blog/blogs/:id                  # Delete blog

POST   /api/blog/blogs/:blogId/posts        # Create post
GET    /api/blog/blogs/:blogId/posts        # List posts
GET    /api/blog/blogs/:blogId/posts/:id    # Get post
PUT    /api/blog/blogs/:blogId/posts/:id    # Update post
DELETE /api/blog/blogs/:blogId/posts/:id    # Delete post
POST   /api/blog/blogs/:blogId/posts/:id/publish   # Publish post
POST   /api/blog/blogs/:blogId/posts/:id/schedule  # Schedule post
```

**AI Generation:**
```
POST   /api/blog/generate/post              # Generate full post
POST   /api/blog/generate/outline           # Generate outline only
POST   /api/blog/generate/expand            # Expand section
POST   /api/blog/generate/rewrite           # Rewrite with instructions
POST   /api/blog/generate/seo               # Generate SEO metadata
```

**Public Content API (for widgets):**
```
GET    /api/embed/:embedToken/posts         # List published posts
GET    /api/embed/:embedToken/posts/:slug   # Get single post
GET    /api/embed/:embedToken/config        # Get widget config
```

### 3.3 Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/blog` | Blog Dashboard | List user's blogs, create new |
| `/blog/:blogId` | Blog Overview | Stats, recent posts, quick actions |
| `/blog/:blogId/posts` | Post Manager | List, filter, bulk actions |
| `/blog/:blogId/posts/new` | Post Editor | Create with AI generation |
| `/blog/:blogId/posts/:id` | Post Editor | Edit existing post |
| `/blog/:blogId/settings` | Blog Settings | SEO, theme, brand voice |
| `/blog/:blogId/widgets` | Widget Manager | Embed codes, config |
| `/blog/:blogId/domains` | Domain Manager | Custom domains (Phase 2) |

### 3.4 AI Generation Engine

**Core Generation Flow:**
```python
# backend/blog_generator.py

class BlogGenerator:
    """
    AI blog content generator using tenant's BYOK settings.
    """
    
    async def generate_post(
        self,
        tenant_id: str,
        prompt: str,
        brand_voice: dict,
        target_length: str = "medium",  # short, medium, long
        tone: str = "professional",
        include_outline: bool = True
    ) -> GeneratedPost:
        """
        Generate a complete blog post.
        
        Flow:
        1. Load tenant's provider settings (Primary/Fallback)
        2. Build system prompt with brand voice
        3. Generate outline first (if requested)
        4. Generate sections with continuity
        5. Generate SEO metadata
        6. Return structured content
        """
        
    async def generate_outline(
        self,
        tenant_id: str,
        topic: str,
        target_sections: int = 5
    ) -> PostOutline:
        """Generate structured outline for approval before full generation."""
        
    async def expand_section(
        self,
        tenant_id: str,
        section_title: str,
        context: str,
        brand_voice: dict
    ) -> str:
        """Expand a single section with more detail."""
        
    async def rewrite(
        self,
        tenant_id: str,
        content: str,
        instructions: str,
        brand_voice: dict
    ) -> str:
        """Rewrite content based on instructions while maintaining voice."""
```

**Brand Voice Configuration:**
```json
{
  "name": "TechStartup Voice",
  "tone": "friendly-professional",
  "personality": [
    "We're excited about technology but explain it simply",
    "We use 'you' and 'we' to feel personal",
    "We avoid jargon unless necessary, then explain it"
  ],
  "vocabulary": {
    "prefer": ["solution", "streamline", "empower"],
    "avoid": ["synergy", "leverage", "paradigm"]
  },
  "formatting": {
    "headings": "sentence-case",
    "lists": "prefer-bullets",
    "paragraphs": "short-2-3-sentences"
  },
  "examples": [
    {
      "bad": "Leverage our cutting-edge solution to synergize workflows.",
      "good": "Our tool helps your team work together more smoothly."
    }
  ]
}
```

### 3.5 Task Breakdown - Phase 1

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P1-01 | Add blog schema to shared/schema.ts | 2h | Critical |
| P1-02 | Create blog storage interface | 3h | Critical |
| P1-03 | Implement tenant CRUD endpoints | 2h | Critical |
| P1-04 | Implement blog CRUD endpoints | 3h | Critical |
| P1-05 | Implement post CRUD endpoints | 4h | Critical |
| P1-06 | Build BlogGenerator class | 6h | Critical |
| P1-07 | Integrate with existing ProviderSettings | 3h | Critical |
| P1-08 | Create Blog Dashboard page | 4h | Critical |
| P1-09 | Create Post Editor with AI generation | 8h | Critical |
| P1-10 | Create Blog Settings page | 3h | High |
| P1-11 | Build public embed API | 4h | High |
| P1-12 | Create basic embed widget (vanilla) | 6h | High |
| P1-13 | Platform subdomain routing | 4h | High |
| P1-14 | Add to main navigation | 1h | Medium |
| P1-15 | Knowledge Base documentation | 3h | Medium |

**Estimated Phase 1 Total: ~56 hours (2-3 weeks)**

---

## 4. Phase 2 — Widgets & Distribution (Weeks 4-6)

### 4.1 Widget SDK Architecture

```
packages/
├── @aiassist/blog-widget-core/     # Shared logic
│   ├── api.ts                      # Content fetching
│   ├── types.ts                    # Shared types
│   └── themes.ts                   # Theme system
│
├── @aiassist/blog-widget-vanilla/  # Vanilla JS
│   ├── index.ts                    # Entry point
│   ├── components/                 # Web Components
│   │   ├── blog-list.ts
│   │   ├── blog-post.ts
│   │   └── blog-card.ts
│   └── embed.ts                    # Script tag bootstrap
│
├── @aiassist/blog-widget-react/    # React wrapper
│   ├── index.tsx
│   ├── BlogList.tsx
│   ├── BlogPost.tsx
│   └── hooks/usePost.ts
│
└── @aiassist/blog-widget-next/     # Next.js optimized
    ├── index.tsx
    ├── components/
    └── server/                     # SSR helpers
```

### 4.2 Vanilla Widget Embed

```html
<!-- User adds this to their site -->
<div id="aiassist-blog"></div>
<script 
  src="https://cdn.aiassist.app/widgets/blog.js"
  data-embed-token="emb_abc123"
  data-api-key="aai_pub_xxx"
  data-theme="light"
  data-layout="list"
></script>
```

### 4.3 React Component

```tsx
import { BlogList, BlogPost } from '@aiassist/blog-widget-react';

function MyBlog() {
  return (
    <BlogList 
      embedToken="emb_abc123"
      apiKey="aai_pub_xxx"
      theme="light"
      postsPerPage={10}
      onPostClick={(post) => router.push(`/blog/${post.slug}`)}
    />
  );
}

function MyBlogPost({ slug }) {
  return (
    <BlogPost 
      embedToken="emb_abc123"
      apiKey="aai_pub_xxx"
      slug={slug}
      theme="light"
    />
  );
}
```

### 4.4 Task Breakdown - Phase 2

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P2-01 | Create widget core package | 4h | Critical |
| P2-02 | Build vanilla JS widget with Web Components | 8h | Critical |
| P2-03 | Build React widget package | 6h | Critical |
| P2-04 | Build Next.js optimized package | 6h | High |
| P2-05 | Widget theme system | 4h | High |
| P2-06 | CDN setup for widget hosting | 3h | High |
| P2-07 | Widget configuration UI | 4h | High |
| P2-08 | Hosted blog subdomain (*.aiassist.blog) | 6h | High |
| P2-09 | SEO optimization (sitemap, robots, meta) | 4h | Medium |
| P2-10 | Rate limiting for embed API | 2h | Medium |

**Estimated Phase 2 Total: ~47 hours (2-3 weeks)**

---

## 5. Phase 3 — Custom Domains & Analytics (Weeks 7-9)

### 5.1 Custom Domain Flow

```
User wants blog.company.com
         │
         ▼
┌─────────────────────┐
│ 1. Add domain in UI │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 2. Show CNAME/A     │
│    verification     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 3. User adds DNS    │
│    records          │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 4. System verifies  │
│    DNS propagation  │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 5. Auto-provision   │
│    SSL via ACME     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 6. Route traffic    │
│    to tenant blog   │
└─────────────────────┘
```

### 5.2 Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    Blog Analytics                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 This Month                    📈 Trending Posts          │
│  ┌─────────────────────┐          ┌───────────────────────┐ │
│  │ Views: 12,450       │          │ 1. "AI in 2025" - 3.2K│ │
│  │ Unique: 8,230       │          │ 2. "Getting Sta..." - │ │
│  │ Avg Read: 4.2m      │          │ 3. "Best Practi..." - │ │
│  └─────────────────────┘          └───────────────────────┘ │
│                                                             │
│  📍 Traffic Sources              🌍 Top Countries           │
│  ┌─────────────────────┐          ┌───────────────────────┐ │
│  │ ████████ Direct 45% │          │ 🇺🇸 USA     42%       │ │
│  │ █████ Widget 28%    │          │ 🇬🇧 UK      18%       │ │
│  │ ███ Search 15%      │          │ 🇩🇪 Germany 12%       │ │
│  │ ██ Social 12%       │          │ 🇨🇦 Canada   8%       │ │
│  └─────────────────────┘          └───────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Task Breakdown - Phase 3

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P3-01 | Domain verification system | 6h | Critical |
| P3-02 | SSL automation (Let's Encrypt/ACME) | 8h | Critical |
| P3-03 | Host-based tenant routing | 4h | Critical |
| P3-04 | Domain management UI | 4h | High |
| P3-05 | Basic analytics tracking | 6h | High |
| P3-06 | Analytics dashboard UI | 6h | High |
| P3-07 | View counting with privacy | 3h | Medium |
| P3-08 | Referrer tracking | 2h | Medium |
| P3-09 | Export analytics data | 2h | Low |

**Estimated Phase 3 Total: ~41 hours (2 weeks)**

---

## 6. Phase 4 — Example Apps & Developer Experience (Weeks 10-11)

### 6.1 Example Repository Structure

```
examples/
├── vanilla-js/
│   ├── index.html              # Simple HTML page
│   ├── blog-list.html          # Post listing
│   ├── blog-post.html          # Single post
│   └── README.md
│
├── react-tailwind/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BlogList.tsx
│   │   │   └── BlogPost.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── README.md
│
├── nextjs-blog/
│   ├── app/
│   │   ├── blog/
│   │   │   ├── page.tsx        # Blog listing (SSG)
│   │   │   └── [slug]/page.tsx # Post page (ISR)
│   │   └── layout.tsx
│   ├── package.json
│   └── README.md
│
├── wordpress-plugin/
│   ├── aiassist-blog.php       # WP plugin
│   ├── templates/
│   └── README.md
│
└── headless-api-demo/
    ├── fetch-posts.js          # Raw API usage
    └── README.md
```

### 6.2 Task Breakdown - Phase 4

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P4-01 | Vanilla JS example | 3h | Critical |
| P4-02 | React + Tailwind example | 4h | Critical |
| P4-03 | Next.js example with SSG/ISR | 6h | High |
| P4-04 | WordPress plugin | 8h | High |
| P4-05 | Headless API demo | 2h | Medium |
| P4-06 | Developer documentation | 6h | High |
| P4-07 | API reference docs | 4h | High |
| P4-08 | Video tutorials (scripts) | 4h | Medium |

**Estimated Phase 4 Total: ~37 hours (1.5 weeks)**

---

## 7. Phase 5 — Admin Control Plane (Week 12)

### 7.1 Admin Features

| Feature | Description |
|---------|-------------|
| Tenant Management | View, suspend, delete tenants |
| Feature Flags | Enable/disable features per tenant/plan |
| Model Availability | Control which models are available |
| Abuse Monitoring | Flag suspicious patterns |
| Usage Dashboard | Platform-wide metrics |
| Content Moderation | Review flagged content (metadata only) |

### 7.2 Task Breakdown - Phase 5

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P5-01 | Admin tenant management UI | 4h | High |
| P5-02 | Feature flag system | 4h | High |
| P5-03 | Platform usage dashboard | 4h | Medium |
| P5-04 | Abuse detection hooks | 3h | Medium |
| P5-05 | Model availability controls | 2h | Medium |

**Estimated Phase 5 Total: ~17 hours (1 week)**

---

## 8. Security & Compliance

### 8.1 Security Checklist

| Area | Requirement | Implementation |
|------|-------------|----------------|
| **BYOK Keys** | Encrypted at rest | AES-256 via existing provider encryption |
| **CLIENT Keys** | Domain + feature scoped | `aai_pub_` keys with server-side origin validation |
| **Key Revocation** | Instant, no grace period | Immediate invalidation, no session persistence after revoke |
| **Embed Tokens** | Scoped, revocable | Random tokens tied to blogId + origins |
| **Content API** | Rate limited | Per-token rate limiting |
| **Domains** | Verified ownership | DNS TXT record verification |
| **SSL** | Auto-provisioned | ACME (Let's Encrypt) |
| **AI Output** | Advisory only | No code execution, no auto-actions |
| **Audit Logs** | All mutations logged | Append-only log with user context |
| **Billing Keys** | Never client-exposed | Billing APIs require STANDARD keys only |

### 8.2 Compliance Notes

- **BYOK Only**: No shared inference = no PII in shared models
- **Content Ownership**: Users own all generated content
- **No Invasive Tracking**: Privacy-first analytics (no cookies required)
- **Stripe Safe**: No model direct billing complications

---

## 9. Monetization

### 9.1 Plan Matrix

| Feature | Free | Pro ($19) | Business ($49) | Enterprise |
|---------|------|-----------|----------------|------------|
| Blogs | 1 | 3 | 10 | Unlimited |
| Posts/month | 20 | 100 | 500 | Unlimited |
| Custom domain | ❌ | ✅ | ✅ | ✅ |
| Widget embeds | Watermark | ✅ | ✅ | ✅ |
| Team members | 1 | 3 | 10 | Unlimited |
| Analytics | Basic | Full | Full | Full + API |
| Brand voice | 1 | 3 | 10 | Unlimited |
| Scheduling | ❌ | ✅ | ✅ | ✅ |
| Priority support | ❌ | ❌ | ✅ | ✅ |
| White-label | ❌ | ❌ | ❌ | ✅ |

### 9.2 Usage-Based Add-ons

| Add-on | Price |
|--------|-------|
| Extra blog | $5/mo |
| Extra 100 posts | $10/mo |
| Additional domain | $3/mo |
| Analytics export | $5/mo |

---

## 10. V1 Ship Criteria

**Must Have:**
- [ ] Multi-tenant blog creation
- [ ] AI generation with BYOK integration
- [ ] Draft/publish lifecycle
- [ ] Public embed API
- [ ] At least 1 widget (vanilla JS)
- [ ] Platform subdomain hosting
- [ ] Basic admin controls

**Should Have:**
- [ ] React widget
- [ ] Brand voice configuration
- [ ] SEO metadata generation
- [ ] Post scheduling

**Nice to Have:**
- [ ] Custom domains
- [ ] Analytics
- [ ] WordPress integration

---

## 11. Timeline Summary

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 1** | Weeks 1-3 | Foundation MVP | Blog engine, AI gen, basic UI |
| **Phase 2** | Weeks 4-6 | Widgets | SDK, embeds, hosted blogs |
| **Phase 3** | Weeks 7-9 | Distribution | Custom domains, analytics |
| **Phase 4** | Weeks 10-11 | Developer DX | Examples, docs, WordPress |
| **Phase 5** | Week 12 | Admin | Control plane, monitoring |

**Total Estimated Effort: ~198 hours / 12 weeks**

---

## 12. Success Metrics

### Launch Metrics (30 days post-V1)
- 50+ tenants created
- 200+ blogs created
- 1,000+ posts generated
- 100+ widget embeds

### Growth Metrics (90 days)
- 30% week-over-week tenant growth
- 40%+ 30-day retention
- 60%+ BYOK adoption
- 10+ paying customers

---

## Appendix A: Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Content Storage | PostgreSQL JSONB | Flexible structure, existing infra |
| Widget Format | Web Components | Framework agnostic, encapsulated |
| CDN | Cloudflare/Platform | Edge caching, SSL |
| Domain SSL | Let's Encrypt | Free, automated |
| Analytics | Self-hosted | Privacy, no cookie consent |

---

## Appendix B: Related Files

- `shared/schema.ts` - Data model definitions
- `server/routes.ts` - API route definitions  
- `client/src/pages/KnowledgeBase.tsx` - Documentation
- `client/src/components/ProviderSettings.tsx` - BYOK config UI
- `backend/orchestrator.py` - AI orchestration (extend for blog)

---

**Document Status:** Ready for Review  
**Next Step:** Stakeholder approval → Begin Phase 1 implementation
