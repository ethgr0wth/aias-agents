# Rock Shield Construction Website

## Overview

Rock Shield Construction is a marketing and lead generation website for a construction company specializing in exterior home services. The site is designed to convert visitors into leads through quote forms, chat functionality, and phone calls. It features a modern dark theme with a "storm mode" emergency feature, customer reviews system, and an admin dashboard for content moderation and analytics.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Routing**: Wouter (lightweight React router)
- **Styling**: Tailwind CSS v4 with custom dark theme, CSS variables for theming
- **UI Components**: shadcn/ui component library (Radix UI primitives)
- **State Management**: React Query (TanStack Query) for server state, React Context for app state (storm mode)
- **Animations**: Framer Motion for transitions and micro-interactions
- **Build Tool**: Vite with custom plugins for meta images and Replit integration

### Backend Architecture
- **Runtime**: Node.js with Express
- **Language**: TypeScript compiled with tsx (development) and esbuild (production)
- **API Design**: RESTful endpoints under `/api/*` prefix
- **Authentication**: Simple token-based admin auth with environment variable password

### Data Storage
- **Primary**: Redis for reviews, analytics, and session data
- **Fallback**: In-memory storage when Redis is unavailable
- **Schema Validation**: Zod for runtime type checking, shared between client and server
- **ORM**: Drizzle ORM configured for PostgreSQL (database not yet provisioned)

### Key Features
- **Review System**: Customer-submitted reviews with admin moderation workflow
- **Analytics Tracking**: Page views, click events, and session tracking
- **AI Chat**: Integration with AiAssist SDK for automated customer support
- **Storm Mode**: Emergency UI state with priority contact information
- **Exit Intent Modal**: Lead capture on page exit
- **Multi-step Quote Form**: Guided form with file uploads and service selection
- **Blog System**: AI-powered content generation with admin CRUD, SEO fields, publish/draft workflow
  - Uses AiAS (@aiassist-secure/core) for LLM content generation
  - Categories: roofing, siding, gutters, storm-damage, maintenance, tips, news
  - SEO fields: meta title, meta description, keywords
  - Public routes: /blog (list), /blog/:slug (individual post)

### Build & Deployment
- **Development**: Vite dev server with HMR, tsx for server
- **Production**: Single-file CJS bundle via esbuild, static assets via Vite
- **Output**: `dist/` folder with `index.cjs` server and `public/` static files

## External Dependencies

### Third-Party Services
- **Redis**: Session and data storage (via `REDIS_URL` environment variable)
- **PostgreSQL**: Database (via `DATABASE_URL`, configured in Drizzle but not actively used)
- **AiAssist**: AI chat functionality (via `VITE_AIAS_API_KEY`)

### Key NPM Packages
- `@tanstack/react-query`: Server state management
- `drizzle-orm` / `drizzle-kit`: Database ORM and migrations
- `ioredis`: Redis client
- `framer-motion`: Animation library
- `react-hook-form` / `zod`: Form handling and validation
- `embla-carousel-react`: Carousel component
- `vaul`: Drawer component

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (required for Drizzle)
- `REDIS_URL`: Redis connection string (falls back to localhost)
- `ADMIN_PASSWORD`: Admin dashboard password (defaults to "rockshield2024")
- `VITE_AIAS_API_KEY`: AiAssist API key for chat functionality
- `AIAS_API_KEY`: AiAssist API key for blog content generation (server-side)
- `PORT`: Server port (defaults to 5000)