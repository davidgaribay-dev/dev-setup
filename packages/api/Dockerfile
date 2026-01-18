FROM node:20-alpine AS base

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10 --activate

# Build stage
FROM base AS builder
WORKDIR /app

# Copy workspace files
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/api/package.json ./packages/api/
COPY packages/shared/package.json ./packages/shared/

# Install dependencies (including devDependencies for build)
RUN pnpm install --frozen-lockfile

# Copy source code
COPY packages/api ./packages/api
COPY packages/shared ./packages/shared

# Build with tsup (bundles local code, externalizes node_modules)
RUN pnpm --filter @rewind/api build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10 --activate

# Copy workspace files for production install
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/api/package.json ./packages/api/
COPY packages/shared/package.json ./packages/shared/

# Install production dependencies only
RUN pnpm install --frozen-lockfile --prod

# Copy built files
COPY --from=builder /app/packages/api/dist ./packages/api/dist

WORKDIR /app/packages/api

EXPOSE 8429

CMD ["node", "dist/index.js"]
