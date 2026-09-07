<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Frontend guidance

Next.js (App Router) UI for the RAG project. See the root `AGENTS.md` for the overall
architecture, GPU/VRAM constraints, and git conventions — those apply here too.

## Commands

```bash
npm run dev      # next dev
npm run build    # next build
npm run start    # next start
npm run lint     # eslint
```

## Structure

- `src/app/` — routes (App Router)
- `src/components/` — grouped by feature: `documents/`, `search/`, `chat/`, `upload/`,
  `layout/`, `shared/`
- `src/contexts/` — `documents`, `health`, `upload-modal` (avoids prop-drilling through
  `AppShell`)
- `src/lib/api/` — one typed module per backend resource (`chat`, `documents`, `health`,
  `ingest`, `search`), all built on the shared fetch wrapper in `client.ts` for
  consistent error handling
- `src/types/` — shared types
- Calls the backend through the `/api/*` rewrite proxy to `BACKEND_URL`
  (`next.config.ts`)

## Code Style

- TypeScript strict mode plus `noUncheckedIndexedAccess`, `noImplicitReturns`,
  `noUnusedLocals`/`noUnusedParameters` (see `tsconfig.json`) — no implicit `any`, no
  unused code
- ESLint: `eslint-config-next` + `typescript-eslint` recommended/stylistic
  type-checked, `no-floating-promises`, `no-misused-promises`,
  `consistent-type-imports` (see `eslint.config.mjs`) — fix violations, don't disable
  rules
- New API calls go through `src/lib/api/<resource>.ts` using the shared `client.ts`
  wrapper, not ad hoc `fetch`
