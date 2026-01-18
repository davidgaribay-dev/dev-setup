# Rewind Viewer

A modern web application for browsing and visualizing your Claude Code conversation history with Neo4j graph database, real-time hook ingestion, Monaco code editor, statistics dashboards, and dark mode support.

## Screenshots & Demo

<div align="center">

### Light Mode

![Light Mode Demo](assets/light-mode.mp4)

![Statistics Dashboard - View detailed token usage, model distribution, and activity timelines](assets/stats.png)

### Dark Mode

![Dark Mode Demo](assets/dark-mode.mp4)

![Navigation Interface - Browse projects, conversations, and search with Monaco code editor](assets/raw-nav-bar.png)

</div>

---

## Architecture

This is a **pnpm monorepo** with four packages:

- **@rewind/api** - Hono API server with Neo4j graph database (TypeScript)
- **@rewind/web** - React SPA built with React Router v7 + TanStack Query
- **@rewind/marketing** - Astro-based marketing and documentation site
- **@rewind/shared** - Shared TypeScript types

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REAL-TIME INGESTION                             │
│                                                                      │
│  Claude Code Response → Stop Hook (Python) → API → Neo4j            │
│                              │                                       │
│                              ▼                                       │
│              ~/.claude/hooks/rewind_hook.py                         │
│              (stdlib only - no dependencies)                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   ┌──────────────────┐                                              │
│   │  Real-time Hook  │                                              │
│   │  (Stop Event)    │                                              │
│   └────────┬─────────┘                                              │
│            │                                                         │
│            │  POST /api/ingest                                       │
│            ▼                                                         │
│   ┌────────────────────────────────────────────────────────────────┐│
│   │               Hono API Server (port 8429)                      ││
│   │   /api/projects  /api/conversations  /api/ingest  /api/stats   ││
│   └────────────────────────────┬───────────────────────────────────┘│
│                                │                                     │
│                                │ Neo4j Driver                        │
│                                ▼                                     │
│   ┌────────────────────────────────────────────────────────────────┐│
│   │                   Neo4j (port 7474/7687)                       ││
│   │   :Project, :Conversation, :Message, :ContentBlock             ││
│   │   Graph relationships for natural data modeling                ││
│   └────────────────────────────────────────────────────────────────┘│
│                                                                      │
│   ┌────────────────────────────────────────────────────────────────┐│
│   │                    React Web (port 8430)                       ││
│   │   Projects | Conversations | Statistics                        ││
│   └────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Real-Time Hook Setup

Enable automatic real-time ingestion of Claude Code conversations:

### 1. Copy Hook File

```bash
# Create hooks directory and copy the hook
mkdir -p ~/.claude/hooks
cp .claude/hooks/rewind_hook.py ~/.claude/hooks/
```

### 2. Configure Claude Code

Add to your `~/.claude/settings.json`:

```json
{
  "env": {
    "REWIND_HOOK_ENABLED": "true",
    "REWIND_API_URL": "http://localhost:8429"
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/rewind_hook.py"
          }
        ]
      }
    ]
  }
}
```

Now every Claude Code response will automatically be sent to the API and stored in Neo4j!

### Hook Features

- **Pure Python 3 stdlib** - No external dependencies required
- **Incremental processing** - Only sends new messages since last run (tracks state per transcript file)
- **Batch ingestion** - Sends multiple messages in a single API call for efficiency
- **Non-blocking** - Always returns 0 to never block Claude Code, even on errors
- **Debug logging** - Optional verbose logging for troubleshooting

### Hook Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `REWIND_HOOK_ENABLED` | `true` | Enable/disable the hook |
| `REWIND_API_URL` | `http://localhost:8429` | API endpoint URL |
| `REWIND_HOOK_DEBUG` | `false` | Enable debug logging to `~/.claude/state/rewind/hook.log` |

### Troubleshooting the Hook

```bash
# View hook logs
tail -f ~/.claude/state/rewind/hook.log

# Enable debug mode (add to ~/.claude/settings.json env section)
"REWIND_HOOK_DEBUG": "true"

# Verify API is running
curl http://localhost:8429/health

# Check hook state (tracks processed lines per transcript)
cat ~/.claude/state/rewind/state.json
```

---

## Quick Start (Production)

**One command to rule them all:**

```bash
# 1. Clone and configure
git clone https://github.com/davidgaribay-dev/rewind.git
cd rewind

# 2. Set Neo4j password (optional, defaults to rewind_password)
export NEO4J_PASSWORD=your_secure_password

# 3. Start everything
docker-compose up -d
```

That's it!

- **Web UI**: http://localhost:8430
- **API**: http://localhost:8429
- **Neo4j Browser**: http://localhost:7474 (username: neo4j)

The first run will take a few minutes to build. Subsequent starts are instant.

---

## Development Setup

For local development with hot reload:

### Prerequisites

- Node.js 20+
- pnpm (`npm install -g pnpm`)
- Docker & Docker Compose

### Steps

```bash
# 1. Clone and install
git clone https://github.com/davidgaribay-dev/rewind.git
cd rewind
pnpm install

# 2. Start all services with Docker
pnpm docker:dev
```

### Available Scripts

**Development:**
- `pnpm docker:dev` - Start all services (Neo4j, API, Web)
- `pnpm docker:dev:down` - Stop all services
- `pnpm docker:dev:logs` - View all logs
- `pnpm docker:dev:logs:api` - View API logs
- `pnpm docker:dev:logs:web` - View web logs
- `pnpm docker:dev:rebuild` - Rebuild and restart all services

**Building:**
- `pnpm build` - Build all packages
- `pnpm build:api` - Build API package only
- `pnpm build:web` - Build Web package only
- `pnpm build:marketing` - Build marketing site only

**Type Checking:**
- `pnpm typecheck` - Run TypeScript type checking on Web package

**Production:**
- `pnpm docker:prod` - Start production containers
- `pnpm docker:prod:down` - Stop production containers
- `pnpm docker:prod:logs` - View production logs

## Project Structure

```
rewind/
├── .claude/
│   └── hooks/
│       └── rewind_hook.py    # Hook source (copy to ~/.claude/hooks/)
│
├── packages/
│   ├── api/                  # Hono API server (TypeScript)
│   │   ├── src/
│   │   │   ├── db/           # Neo4j driver & queries
│   │   │   ├── routes/       # API routes
│   │   │   └── index.ts      # Server entry
│   │   ├── tsup.config.ts    # tsup bundler config
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   ├── web/                  # React web app
│   │   ├── app/
│   │   │   ├── components/   # UI components
│   │   │   ├── hooks/        # React hooks
│   │   │   ├── lib/          # Utilities & API client
│   │   │   └── routes/       # React Router routes
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   ├── marketing/            # Astro marketing site
│   │   └── ...
│   │
│   └── shared/               # Shared TypeScript types
│       └── src/types.ts
│
├── docker-compose.yml        # Production config
├── docker-compose.dev.yml    # Development config
└── pnpm-workspace.yaml

# After installation, hook is at:
~/.claude/hooks/rewind_hook.py
```

## Features

### Core Features
- **Project Management**: Browse all your Claude Code projects with statistics
- **Conversation Viewer**: View conversations with rich formatting, syntax highlighting, and Monaco code editor
- **Content Blocks**: Display thinking blocks, tool use, and tool results separately
- **Search**: Full-text search across conversations with project filtering
- **Statistics Dashboard**: Visualize token usage, model distribution, and activity timelines
- **Dark Mode**: System-aware dark/light theme with manual toggle
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS v4

### Graph Database Benefits
- **Natural Data Model**: Conversations are graphs - messages have relationships, tool uses connect to results
- **Flexible Schema**: Easy to evolve as Claude Code's data format changes
- **Efficient Traversals**: O(1) per hop for finding related data
- **Built-in Visualization**: Neo4j Browser at http://localhost:7474

## API Endpoints

**Projects:**
- `GET /api/projects` - List all projects with stats
- `GET /api/projects/:id` - Get single project
- `GET /api/projects/:id/conversations` - Get project conversations

**Conversations:**
- `GET /api/conversations/:id` - Get conversation with messages and content blocks
- `GET /api/conversations/search?q=query&projectId=id` - Search conversations

**Stats:**
- `GET /api/stats` - Get overall statistics

**Ingest:**
- `POST /api/ingest` - Ingest a message from hook

**Health:**
- `GET /health` - Health check with Neo4j status

## Tech Stack

### API (@rewind/api)
- [Hono](https://hono.dev/) - Ultra-fast web framework
- [neo4j-driver](https://neo4j.com/docs/javascript-manual/current/) - Official Neo4j JavaScript driver
- [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- [tsup](https://tsup.egoist.dev/) - Fast TypeScript bundler (esbuild-based)

### Database
- [Neo4j 5](https://neo4j.com/) - Graph database (Community Edition)
- [APOC](https://neo4j.com/labs/apoc/) - Neo4j procedures library

### Web (@rewind/web)
- [React 19](https://react.dev/) - Latest React with concurrent features
- [React Router v7](https://reactrouter.com/) - File-based routing in SPA mode
- [TanStack Query v5](https://tanstack.com/query) - Server state management
- [TanStack Table v8](https://tanstack.com/table) - Data tables
- [Tailwind CSS v4](https://tailwindcss.com/) - Utility-first styling
- [Radix UI](https://www.radix-ui.com/) - Accessible components
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) - Code editor
- [Vite](https://vitejs.dev/) - Build tool

### Hook
- Python 3 (stdlib only - no external dependencies)
- Uses `urllib` for HTTP requests

## Troubleshooting

**Neo4j connection issues:**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# View Neo4j logs
docker logs rewind-neo4j-dev

# Access Neo4j Browser
open http://localhost:7474
```

**Hook not sending data:**
- Check hook logs: `tail -f ~/.claude/state/rewind/hook.log`
- Verify API is running: `curl http://localhost:8429/health`
- Check environment variables in `~/.claude/settings.json`

**Web app can't connect to API:**
- Verify API is running: `docker ps | grep api`
- Check `VITE_API_URL` (should be `http://localhost:8429`)
- View API logs: `pnpm docker:dev:logs:api`

**Docker-specific issues:**
- Check container status: `docker ps`
- View all logs: `pnpm docker:dev:logs`
- Rebuild containers: `pnpm docker:dev:rebuild`
- Clean restart: `pnpm docker:dev:clean && pnpm docker:dev`

## Environment Variables

Copy `.env.example` to `.env` to customize configuration:

```bash
cp .env.example .env
```

**Neo4j Configuration:**
- `NEO4J_PASSWORD` - Neo4j password (default: `rewind_password`)

**API Configuration:**
- `LOG_LEVEL` - Logging level: error, warn, info, debug (default: `info`)

**Web Configuration:**
- `VITE_API_URL` - API base URL (default: `http://localhost:8429`)

**Hook Configuration (in `~/.claude/settings.json`):**
- `REWIND_HOOK_ENABLED` - Enable/disable hook (default: `true`)
- `REWIND_API_URL` - API endpoint (default: `http://localhost:8429`)
- `REWIND_HOOK_DEBUG` - Enable debug logging (default: `false`)

## License

MIT
