# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies. Also contains the **Ms. Sunny** Python Flask multi-agent AI education system.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Python version**: 3.11
- **Package manager**: pnpm (Node), uv/pip (Python)
- **TypeScript version**: 5.9
- **API framework**: Express 5 (TS) + Flask (Python)
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)
- **AI**: LangGraph multi-agent + NVIDIA Nemotron (`nvidia/nemotron-nano-9b-v2`)

## Structure

```text
artifacts-monorepo/
├── artifacts/              # Deployable applications
│   ├── api-server/         # Express API server (TypeScript)
│   └── ms-sunny/           # React + Vite frontend for Ms. Sunny
├── lib/                    # Shared libraries
│   ├── api-spec/           # OpenAPI spec + Orval codegen config
│   ├── api-client-react/   # Generated React Query hooks
│   ├── api-zod/            # Generated Zod schemas from OpenAPI
│   └── db/                 # Drizzle ORM schema + DB connection
├── scripts/                # Utility scripts
├── app.py                  # Flask app entry point (serves GET /, POST /answer)
├── agents.py               # LangGraph multi-agent workflow
├── nemotron.py             # NVIDIA Nemotron model client
├── rag.py                  # RAG retrieval from curriculum.json
├── curriculum.json         # Phonics/reading knowledge base (26 letters, blends, sight words)
├── templates/index.html    # Flask HTML template (fallback)
├── static/style.css        # Flask static CSS (fallback)
├── static/script.js        # Flask static JS (fallback)
├── pnpm-workspace.yaml     # pnpm workspace
├── tsconfig.base.json      # Shared TS options
├── tsconfig.json           # Root TS project references
└── package.json            # Root package with hoisted devDeps
```

## Ms. Sunny AI System

### Architecture
- **Frontend**: React + Vite at `artifacts/ms-sunny/` (served at `/`)
- **Backend**: Flask API at `app.py` (port 8000, `Ms. Sunny Flask Backend` workflow)
- **Proxy**: Vite dev server proxies `/answer` → Flask port 8000

### Agents (LangGraph)
1. **Assessment Agent** — Evaluates student's answer with Nemotron model
2. **Retrieval Agent (RAG)** — Searches `curriculum.json` for relevant phonics concept
3. **Lesson Generator Agent** — Generates kid-friendly explanation using Nemotron
4. **Reinforcement Agent** — Creates new practice question if student struggles

### Reasoning Loop
`THOUGHT → ACTION → OBSERVATION → PLAN`

### API Endpoints
- `GET /` — Returns Flask HTML template (fallback)
- `POST /answer` — Receives student answer, runs LangGraph workflow, returns:
  - `is_correct` (bool)
  - `explanation` (str)
  - `next_question` (str)
  - `learning_gaps` (list)
  - `reasoning_logs` (list of THOUGHT/ACTION/OBSERVATION/PLAN dicts)

### Environment Variables
- `NVIDIA_API_KEY` — Required for NVIDIA Nemotron model API calls. Get from https://build.nvidia.com/

### Running
- Frontend: `artifacts/ms-sunny: web` workflow (pnpm dev, port 24596)
- Backend: `Ms. Sunny Flask Backend` workflow (`PORT=8000 python app.py`)

## TypeScript & Composite Projects

Every package extends `tsconfig.base.json` which sets `composite: true`. The root `tsconfig.json` lists all packages as project references.

## Packages

### `artifacts/ms-sunny` (`@workspace/ms-sunny`)
React + Vite frontend for Ms. Sunny. Proxies `/answer` to Flask on port 8000.

### `artifacts/api-server` (`@workspace/api-server`)
Express 5 API server (not used by Ms. Sunny).

### `lib/db` (`@workspace/db`)
Database layer using Drizzle ORM with PostgreSQL.

### `lib/api-spec` (`@workspace/api-spec`)
OpenAPI 3.1 spec and Orval codegen config.
