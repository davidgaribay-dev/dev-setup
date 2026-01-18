# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Rewind Viewer is a web application for browsing and visualizing Claude Code conversation history. It's a **pnpm monorepo** with four packages:

- **@rewind/api** - Hono API server with Neo4j graph database
- **@rewind/web** - React SPA built with React Router v7 + TanStack Query
- **@rewind/marketing** - Astro-based marketing and documentation site
- **@rewind/shared** - Shared TypeScript types used by API and Web packages

Data is ingested in real-time via a Claude Code hook that posts to the API, which stores everything in Neo4j.

## Essential Scripts Quick Reference

### Building
```bash
pnpm build          # Build all packages
pnpm build:api      # Build API package only
pnpm build:web      # Build Web package only
pnpm build:marketing # Build marketing site only
```

### Type Checking
```bash
pnpm typecheck      # Run TypeScript type checking on Web package
pnpm typecheck:web  # Run TypeScript type checking on Web package (alias)
```

### Development
```bash
pnpm dev            # Start API (port 8429) and Web (port 8430) in parallel
pnpm dev:api        # API server only
pnpm dev:web        # Web app only
pnpm dev:marketing  # Marketing site only
```

### Production
```bash
pnpm start:api      # Start production API server (requires prior build)
pnpm start:web      # Serve production Web build
```

## Development Commands

### Environment Setup

#### Option 1: Docker Development (Recommended)
```bash
# Copy environment template
cp .env.example .env

# Start all services (Neo4j + API + Web) with hot reload
pnpm docker:dev

# Or rebuild and start (when dependencies change)
pnpm docker:dev:build

# Stop all services
pnpm docker:dev:down

# Stop and remove volumes (clean slate)
pnpm docker:dev:clean

# View logs
pnpm docker:dev:logs

# Rebuild specific service
pnpm docker:dev:rebuild:api
pnpm docker:dev:rebuild:web

# View service-specific logs
pnpm docker:dev:logs:api
pnpm docker:dev:logs:web
```

#### Option 2: Local Development
```bash
# Copy environment template
cp .env.example .env

# Install dependencies
pnpm install

# Start Neo4j via Docker
docker-compose up -d neo4j

# Wait for Neo4j to be healthy, then start dev servers
pnpm dev
```

**Development Docker Features:**
- **Hot reload**: Source code changes are reflected immediately without rebuilding
- **Volume mounts**: `packages/api/src`, `packages/web/app`, and `packages/shared/src` are mounted as read-only volumes
- **Node modules isolation**: Uses named volumes for `node_modules` to avoid host conflicts
- **Separate networks**: Uses `rewind-network-dev` to avoid conflicts with production setup

### Package-Specific Commands
```bash
# Run commands in specific packages
pnpm --filter @rewind/api <command>
pnpm --filter @rewind/web <command>
pnpm --filter @rewind/marketing <command>

# Examples
pnpm --filter @rewind/web typecheck
pnpm --filter @rewind/api build
```

## Architecture

### Data Flow
1. **Claude Code Hook**: A Python hook (`~/.claude/hooks/rewind/hook.py`) runs after each Claude Code response
2. **API Ingest**: Hook sends messages to `POST /api/ingest` endpoint
3. **Neo4j Storage**: API stores data as a graph in Neo4j with nodes for Projects, Conversations, Messages, and ContentBlocks
4. **Query API**: Hono server exposes REST endpoints for reading data
5. **Frontend**: React SPA fetches data via TanStack Query and displays conversations

### Graph Schema (Neo4j)

**Nodes:**
- **Project**: `{id, name, displayName, path, createdAt, updatedAt}`
- **Conversation**: `{sessionId, uuid, timestamp, createdAt}`
- **Message**: `{uuid, type, timestamp, parentUuid, isSidechain, cwd, sessionId, version, gitBranch, agentId, model, inputTokens, outputTokens, messageData, preview}`
- **ContentBlock**: `{index, type, data}`

**Relationships:**
- `(Project)-[:HAS_CONVERSATION]->(Conversation)`
- `(Conversation)-[:CONTAINS]->(Message)`
- `(Message)-[:HAS_BLOCK]->(ContentBlock)`

### API Endpoints

Located in `packages/api/src/routes/`:

- **Projects** ([routes/projects.ts](packages/api/src/routes/projects.ts)):
  - `GET /api/projects` - List all projects with stats
  - `GET /api/projects/:id` - Get single project
  - `GET /api/projects/:id/conversations` - Get project conversations

- **Conversations** ([routes/conversations.ts](packages/api/src/routes/conversations.ts)):
  - `GET /api/conversations/:id` - Get conversation with messages and content blocks
  - `GET /api/conversations/search?q=query&projectId=id` - Search conversations

- **Stats** ([routes/stats.ts](packages/api/src/routes/stats.ts)):
  - `GET /api/stats` - Get overall statistics

- **Ingest** ([routes/ingest.ts](packages/api/src/routes/ingest.ts)):
  - `POST /api/ingest` - Ingest a message from hook

- **Health Check**:
  - `GET /health` - Returns health status and Neo4j connection state

### Frontend Architecture

Located in `packages/web/app/`:

- **Routing**: File-based routing via React Router v7 (SPA mode)
  - [routes/home.tsx](packages/web/app/routes/home.tsx) - Projects landing page
  - [routes/project.$projectId.tsx](packages/web/app/routes/project.$projectId.tsx) - Single project view with conversations
  - [routes/project.$projectId.conversation.$conversationId.tsx](packages/web/app/routes/project.$projectId.conversation.$conversationId.tsx) - Conversation viewer

- **Data Fetching**: TanStack Query configured in [lib/queryClient.tsx](packages/web/app/lib/queryClient.tsx)

- **UI Components**: Radix UI primitives + custom components in [components/](packages/web/app/components/)

- **Styling**: Tailwind CSS v4 with dark mode support

### Hook Architecture

The Claude Code hook source is at `.claude/hooks/rewind_hook.py` in this repo. Users copy it to `~/.claude/hooks/rewind_hook.py`.

**Hook Features:**
- **No dependencies**: Uses only Python stdlib (urllib, json)
- **State tracking**: Tracks processed lines per transcript file in `~/.claude/state/rewind/state.json`
- **Incremental updates**: Only sends new messages since last run
- **Batch ingestion**: Uses `POST /api/ingest/batch` for efficiency
- **Error handling**: Never blocks Claude Code (returns 0 on any error)
- **Logging**: Writes to `~/.claude/state/rewind/hook.log`

**Configuration via environment variables (set in `~/.claude/settings.json` env section):**
- `REWIND_API_URL` - API endpoint (default: `http://localhost:8429`)
- `REWIND_HOOK_ENABLED` - Enable/disable hook (default: `true`)
- `REWIND_HOOK_DEBUG` - Enable debug logging (default: `false`)

**Hook Installation:**
```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/rewind_hook.py ~/.claude/hooks/
```

**settings.json configuration:**
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

## Environment Variables

Copy `.env.example` to `.env` and customize as needed:
```bash
cp .env.example .env
```

**Neo4j Configuration:**
- **NEO4J_PASSWORD**: Neo4j password (default: `rewind_password`)

**API Configuration:**
- **LOG_LEVEL**: Logging level - error, warn, info, debug (default: `info`)

**Web Configuration:**
- **VITE_API_URL**: API base URL for frontend (default: `http://localhost:8429`)

Note: `NEO4J_URI` and `NEO4J_USER` are set automatically in Docker Compose and don't need to be configured manually.

## Technology Stack

### API (@rewind/api)
- **Hono**: Ultra-fast web framework with Node.js server adapter
- **neo4j-driver**: Official Neo4j JavaScript driver
- **tsup**: Fast TypeScript bundler (esbuild-based) for production builds
- **tsx**: TypeScript execution for development

### Web (@rewind/web)
- **React 19**: Latest React with concurrent features
- **React Router v7**: File-based routing in SPA mode
- **TanStack Query v5**: Server state management and caching
- **TanStack Table v8**: Data table components
- **Radix UI**: Accessible component primitives
- **Tailwind CSS v4**: Utility-first styling
- **Monaco Editor**: Code editor with syntax highlighting
- **Recharts**: Data visualization
- **Vite**: Build tool and dev server

### Database
- **Neo4j 5**: Graph database (Community Edition)
- **APOC**: Neo4j procedures library

### Shared (@rewind/shared)
- **TypeScript types**: Shared type definitions
- No runtime dependencies

## Common Development Workflows

### Working with Shared Types
1. Define types in `packages/shared/src/types.ts`
2. Export from `packages/shared/src/index.ts`
3. Import in API or Web: `import { TypeName } from '@rewind/shared'`

### Adding New API Endpoints
1. Create route handler in `packages/api/src/routes/`
2. Add Cypher queries in `packages/api/src/db/queries.ts`
3. Register route in `packages/api/src/index.ts`

### Adding Frontend Features
1. Create route file in `packages/web/app/routes/` (auto-registered)
2. Use TanStack Query hooks for data fetching
3. Reuse UI components from `components/`

### Debugging
1. Check Neo4j Browser at http://localhost:7474
2. View API logs: `pnpm docker:dev:logs:api`
3. View hook logs: `tail -f ~/.claude/state/rewind/hook.log`
4. Set `LOG_LEVEL=debug` for verbose output

## API Build System

The API uses **tsup** (esbuild-based bundler) instead of plain `tsc` for production builds:

**Why tsup:**
- **Fast builds**: ~16ms vs ~1.5s with tsc
- **No .js extensions**: Uses `moduleResolution: "bundler"` so imports don't need `.js` extensions
- **Bundles shared package**: The `@rewind/shared` package is bundled inline
- **External dependencies**: npm packages (hono, neo4j-driver) are kept external

**Configuration files:**
- [tsup.config.ts](packages/api/tsup.config.ts) - tsup bundler configuration
- [tsconfig.json](packages/api/tsconfig.json) - TypeScript config with `moduleResolution: "bundler"`

**Build output:**
- Single `dist/index.js` file with sourcemap
- External dependencies resolved from `node_modules` at runtime

## Neo4j Best Practices

The API uses the official Neo4j JavaScript driver with these patterns:

- **Single driver instance**: One driver per application for connection pooling
- **Managed transactions**: `executeRead`/`executeWrite` for auto-retry on transient errors
- **Session per request**: Create session, use it, close it
- **Integer handling**: Use `neo4j.int()` for writes, `.toNumber()` for reads
