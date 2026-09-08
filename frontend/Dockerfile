# Multi-stage build for Next.js frontend
# Pinned to node 22: on node 24, `next build` fails deserializing next.config.ts
# with "Missing field `turbopackMemoryEviction`".
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# next.config.ts resolves BACKEND_URL for rewrites() at build time, since
# Next.js bakes the rewrite destination into routes-manifest.json — a
# runtime-only env var on the production stage has no effect.
ARG BACKEND_URL=http://api:8000
ENV BACKEND_URL=$BACKEND_URL

# Build
RUN npm run build

# Production stage
FROM node:22-alpine

WORKDIR /app

ARG BACKEND_URL=http://api:8000

ENV NODE_ENV=production
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_API_URL=""

# Copy built app from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
