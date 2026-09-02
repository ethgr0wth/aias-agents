# whoami

whoami is a portable identity-profile registry for people, companies,
projects, publications, and autonomous agents. Profiles are human-readable in
the React interface and exportable as JSON, Markdown, Schema.org data, and
`llms.txt`.

## Features

- Browse and search structured profiles
- Create, update, and remove profiles
- Type-aware profile pages and relationship metadata
- Machine-readable JSON and Schema.org exports
- Markdown and `llms.txt` exports for AI systems
- Redis persistence with automatic demo seeding on an empty database

## Requirements

- Node.js 22+
- npm
- Redis

## Quick start

```bash
cp .env.example .env
npm install
./start.sh
```

The web app runs on `http://localhost:3000` and the API on
`http://localhost:3001`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `API_PORT` | `3001` | Express API port |
| `WEB_PORT` | `3000` | Vite preview port |
| `PUBLIC_BASE_URL` | `http://localhost:3000` | Canonical public URL used in exports |

Never commit `.env` or a Redis data dump.

## Scripts

```bash
npm run dev          # Vite development server
npm run dev:api      # API server
npm run build        # TypeScript and production frontend build
npm run lint         # ESLint
npm run start:web    # Serve the production frontend build
```

## Project layout

```text
whoami/
├── src/              # React frontend
├── server/           # Express API, Redis storage, and demo seed data
├── public/           # Static browser assets
├── start.sh          # Starts API and frontend preview
├── Dockerfile
└── .env.example
```

## Docker

```bash
docker build -t whoami .
docker run --rm --env-file .env -p 3000:3000 -p 3001:3001 whoami
```

## License

MIT. See [LICENSE](./LICENSE).