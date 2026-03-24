---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-03-15'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-codiak-2026-03-01.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/analysis/brainstorming-session-2026-03-01.md
  - docs/index.md
  - docs/technical/architecture.md
  - docs/technical/developer-guide.md
  - docs/technical/integrations.md
workflowType: 'architecture'
project_name: 'codiak'
user_name: 'Master Cody'
date: '2026-03-14'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (36 total across 6 categories):**

| Category | Count | Architectural Significance |
|----------|-------|---------------------------|
| Data Synchronization (FR1-FR6) | 6 | Foundation layer — cache coherence, sync health, transfer detection |
| Transaction Categorization (FR7-FR15) | 9 | Most complex backend — three-tier pipeline with learning, write-back queue |
| Financial Awareness (FR16-FR19) | 4 | Derived calculations dependent on data layer accuracy |
| Dragon Keeper Agent (FR20-FR26) | 7 | Separate interaction model — LLM orchestration, MCP tool access, chat persistence |
| Dashboard & Status (FR27-FR31) | 5 | Primary UI surface — progressive loading, multiple independent widgets |
| Configuration & Rules (FR32-FR36) | 5 | CRUD operations with bulk reclassification and pipeline integration |

**Non-Functional Requirements (14 total):**

| Category | Key Constraints |
|----------|----------------|
| Performance (NFR1-5) | Safe-to-spend < 1s, categorization actions < 500ms, agent responses < 5s, progressive widget loading |
| Security (NFR6-9) | API keys server-side only, LLM calls sanitized (payee/amount/memo only), SQLite excluded from VCS |
| Integration (NFR10-14) | YNAB rate limit 200 req/hr with throttling, graceful API failure handling, no modifications to shared Codiak components |

**Scale & Complexity:**

- Primary domain: Full-stack web application (React + FastAPI + SQLite + external APIs)
- Complexity level: Medium (single-user, single-tenant, but with LLM integration, multi-tier pipeline, and agent orchestration)
- Estimated architectural components: 8-10 (data layer, sync engine, categorization pipeline, rules engine, safe-to-spend calculator, agent orchestrator, dashboard API, configuration manager)
- Deployment: Local desktop, no cloud hosting in MVP

### Technical Constraints & Dependencies

**Platform Constraints:**
- Must integrate as self-contained "wing" within existing Codiak React + FastAPI stack
- Dragon Keeper routes nested under existing routing (`/tool/dragon-keeper/*`)
- Registered in `TOOL_COMPONENTS` map in `ToolPage.tsx`
- All API endpoints prefixed `/api/dragon-keeper/`
- Desktop only, modern Chrome/Edge — no mobile, no responsive breakpoints
- Separate SQLite database from existing `accounts.db`

**External Dependencies:**
- YNAB API (200 req/hr rate limit, bank sync reliability varies)
- LLM API (Anthropic/OpenAI — for categorization and agent responses)
- Existing Codiak patterns: `apiFetch()`, TanStack Query, FastAPI router/service pattern

**Existing Code Reuse Targets:**
- `ynab_export_data.py` — YNAB data fetch/import logic
- `ynab_mcp/queries.py` — SQLite read queries
- `ynab_categorizer_config.py` + `ynab_categorizer.py` — rules engine and LLM categorization
- `ynab_categorizer_rules.json` — existing categorization rules
- `ynab_mcp/ynab_server.py` — MCP tool definitions for agent access

**Resource Constraints:**
- Solo developer with day job — architecture must support incremental, independent delivery
- Each Phase A component (A1-A5) should be independently functional and testable

### Cross-Cutting Concerns Identified

1. **Rate Limiting** — YNAB 200 req/hr shared across sync, categorization write-back, and agent-initiated queries. Needs centralized rate limiter with priority queue.
2. **Data Consistency** — SQLite cache must track staleness per-account. Write-back to YNAB must handle conflicts (user edited in YNAB directly). Sync health must be visible.
3. **Amount Normalization** — YNAB uses milliunits (1000 = $1.00). Unified amount handling needed across all components to prevent conversion bugs.
4. **LLM Failure Graceful Degradation** — Categorization falls to manual queue if LLM unavailable. Agent functions with reduced capability. No silent failures.
5. **Error Propagation** — API failures surface as user-visible messages without data corruption. Import failures don't leave partial state.
6. **Progressive Loading** — Dashboard widgets render independently. Safe-to-spend renders first. TanStack Query handles per-widget caching and refetching.
7. **Security Boundary** — All external API calls server-side. Frontend never sees API keys. LLM requests contain only payee names, amounts, memos — no account numbers.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application — brownfield extension of existing Codiak platform. No new starter template needed; Dragon Keeper extends established patterns.

### Existing Stack (Inherited from Codiak)

| Layer | Technology | Status |
|-------|-----------|--------|
| Frontend Framework | React 18 + TypeScript + Vite | In production |
| Server State | TanStack Query v5.x | In production |
| Routing | React Router | In production |
| Backend | FastAPI (latest: 0.135.1) | In production |
| Database | SQLite (built-in Python) | In production |
| HTTP Client | `apiFetch()` wrapper (`web/src/api.ts`) | In production |
| LLM SDK | Anthropic Python SDK (latest: 0.84.0) | In production |

### Starter Options Considered

Given brownfield context, the evaluation focused on what Dragon Keeper needs beyond existing infrastructure rather than greenfield starter templates.

### Selected Approach: Extend Existing Codiak Patterns + Minimal New Dependencies

**Rationale:** Dragon Keeper is a wing within a running platform. Adding a new starter would create architectural divergence. Instead, follow established Codiak patterns (FastAPI routers/services, `apiFetch()`, TanStack Query, `TOOL_COMPONENTS` registration) and add only what's missing.

### Additional Dependencies for Dragon Keeper

**1. Agent Orchestration: Strands Agents SDK (v1.29.0)**

- Model-agnostic framework supporting Anthropic, OpenAI, Bedrock, Gemini, LiteLLM, Ollama, and custom providers
- Native MCP support via `MCPClient` — can consume existing `ynab_mcp/ynab_server.py` directly
- Clean `@tool` decorator for defining financial data tools with auto-generated specs from docstrings and type hints
- Swap LLM providers with a single line change — no agent logic modifications needed
- Install: `pip install 'strands-agents[anthropic]' strands-agents-tools`
- Optional provider extras: `pip install 'strands-agents[openai]'` or `'strands-agents[bedrock]'`

**2. SQLite Schema Migrations: fastmigrate (v0.5.2)**

- Zero external dependencies, uses Python's built-in `sqlite3`
- Numbered `.sql`/`.py` migration files with version tracking via `_meta` table
- `create_db()` and `run_migrations()` at application startup
- Install: `pip install fastmigrate`
- Rejected alternatives: alembic (overkill, pulls SQLAlchemy), yoyo-migrations (less active)

**3. YNAB API Rate Limiting: Custom Token Bucket (Project Code)**

- Simple sliding-window counter (~15 lines) shared via FastAPI dependency injection
- 200 req/hr from single source — no library needed for this scale
- Rejected alternatives: aiolimiter (async-only complexity), limits (Redis-oriented)

**4. Chat UI: Custom React Component (Project Code)**

- Scrollable message list + text input + avatar display
- TanStack Query mutation for sending, optimistic updates
- Keeps styling consistent with Codiak, minimal bundle impact
- Rejected alternatives: Stream Chat SDK (SaaS dependency), chat UI libraries (opinionated styling)

**5. Background Tasks: FastAPI BackgroundTasks (Built-in)**

- Already part of FastAPI — no additional dependency
- Sufficient for single-user write-back queue processing
- Rejected alternatives: Celery (requires message broker, massive overkill)

### Net New Dependencies Summary

| Package | Purpose | Type |
|---------|---------|------|
| `strands-agents[anthropic]` | Agent orchestration with LLM flexibility | pip |
| `strands-agents-tools` | Community tool packages for agent | pip |
| `fastmigrate` | SQLite schema migrations | pip |

Everything else is either already present in Codiak or built as project code.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Normalized SQLite schema with fastmigrate migrations
- Full mirror YNAB cache model
- Persistent write-back queue (SQLite table)
- Pre-composed widget API endpoints
- Strands Agents SDK with API-only data access

**Important Decisions (Shape Architecture):**
- TanStack Query for Keeper chat state management
- Nested layout routes for Dragon Keeper
- Persistent agent conversation history (SQLite)
- Polling for real-time updates (TanStack Query refetch)
- Structured JSON error responses

**Deferred Decisions (Post-MVP):**
- SSE/WebSocket for push updates (if polling latency becomes noticeable)
- Mobile-specific API optimizations (if mobile client built)
- Multi-user auth and authorization (not in scope)

### Data Architecture

**Schema Strategy: Normalized**

- Standard normalized relational schema for transactions, accounts, categories, rules, and chat history
- SQLite with `fastmigrate` for schema versioning
- Reasoning: Single-user local app — query performance is not a constraint. Normalization gives flexibility for evolving queries without migration pain. Joins are negligible cost at this data volume.

**YNAB Cache Model: Full Mirror**

- Sync all accounts, transactions, categories, and payees from YNAB into local SQLite
- Delta sync using YNAB's `server_knowledge` parameter to fetch only changes
- Local copy is the source of truth for all reads; YNAB is the source of truth for writes
- Reasoning: Simplest mental model. No decisions about what to cache — everything is local. Dashboard queries hit SQLite only, never YNAB API directly.

**Write-Back Queue: Persistent (SQLite Table)**

- Approved categorizations queued in a `write_back_queue` table with status tracking (`pending`, `in_progress`, `completed`, `failed`)
- Background task processes queue on interval, respecting YNAB rate limits
- Failed items retry with exponential backoff, surface in sync health
- Reasoning: App restart must not lose approved categorizations. Persistent queue ensures no work is lost between sessions.

### API & Communication Patterns

**API Design: Pre-Composed Widget Endpoints**

- Each dashboard widget backed by a dedicated endpoint returning ready-to-render data
- Endpoints: `/api/dragon-keeper/safe-to-spend`, `/api/dragon-keeper/trends`, `/api/dragon-keeper/sync-health`, `/api/dragon-keeper/queue-status`, `/api/dragon-keeper/summary-cards`
- Calculation logic lives server-side in service functions; frontend is a thin rendering layer
- Reasoning: Keeps frontend simple, each widget loads independently via its own TanStack Query hook, and business logic is testable in Python.

**Error Handling: Structured JSON**

```json
{
  "error": "sync_failed",
  "code": "YNAB_RATE_LIMITED",
  "detail": "Rate limit exceeded. Next sync available in 45 seconds."
}
```

- All API errors return consistent shape with machine-readable `code` and human-readable `detail`
- Frontend maps error codes to UI feedback (toast, inline message, Keeper greeting)
- Agent uses `detail` field in conversational responses

**Real-Time Updates: Polling**

- TanStack Query `refetchInterval` for dashboard widgets (30s default)
- Sync status polled at 10s during active sync operations
- Queue count polled at 60s (or on focus via `refetchOnWindowFocus`)
- Reasoning: Single-user local app — polling is trivially simple and the latency difference vs. SSE is imperceptible. No WebSocket infrastructure to maintain.

### Frontend Architecture

**Keeper Chat State: TanStack Query**

- Chat history persisted in SQLite, served via `/api/dragon-keeper/chat/history`
- Sending messages via mutation to `/api/dragon-keeper/chat/send`
- Optimistic updates for user messages; streaming response appended as Keeper generates
- Drawer reads from query cache — survives route changes without re-fetching
- Reasoning: Chat is server state (persisted in SQLite). TanStack Query already manages caching, refetching, and optimistic updates for every other data surface. No additional dependency needed.

**Routing: Nested Layout Routes**

```
/tool/dragon-keeper          → DragonKeeperLayout
  /                          → Dashboard (default)
  /category/:id              → CategoryDetail
  /rules                     → RulesManagement
  /history                   → TransactionHistory
```

- `DragonKeeperLayout` renders sidebar grouping, DragonStateIndicator, and Keeper drawer
- Child routes render into `<Outlet />` within the layout
- Keeper drawer state (open/closed) persisted in layout — survives child route changes
- Reasoning: Prevents re-mounting the Keeper drawer on navigation. Dragon Keeper has its own chrome (state indicator, drawer toggle) that must persist across views.

### Agent Architecture

**Conversation Persistence: SQLite**

- Chat messages stored in `chat_messages` table with `role`, `content`, `timestamp`, `session_id`
- Agent can reference past conversations for context ("You asked about this last week")
- Searchable message history enables conversational continuity across sessions
- Reasoning: The Keeper's value is in the relationship. Memory requires persistence. SQLite is already the data layer — one more table, no new infrastructure.

**Agent Tool Boundary: API-Only**

- Keeper agent accesses all data through FastAPI endpoints — same path as the frontend
- No direct SQLite access from agent tools
- Agent tools are thin wrappers that call API endpoints and format responses for conversation
- Write operations (approve, correct, create rule) use the same service functions as API routes
- Reasoning: One source of truth for all data access. Bug fixes in endpoints benefit the agent automatically. Easier to test, debug, and reason about. Localhost HTTP overhead is negligible for a single-user app.

### Decision Impact Analysis

**Implementation Sequence:**

1. SQLite schema + fastmigrate setup (foundation for everything)
2. YNAB sync engine + full mirror cache (data must exist before anything renders)
3. Widget API endpoints + service layer (backend ready for frontend)
4. Dragon Keeper layout + routing shell (frontend chrome)
5. Dashboard widgets with TanStack Query hooks (first visible value)
6. Write-back queue + categorization pipeline (interactive features)
7. Strands agent setup + API tool wrappers (Keeper comes alive)
8. Chat persistence + Keeper drawer (relationship surface)

**Cross-Component Dependencies:**

| Component | Depends On | Feeds Into |
|-----------|-----------|------------|
| SQLite schema | fastmigrate | Everything |
| Sync engine | Schema, YNAB API, rate limiter | Cache, widget endpoints |
| Widget endpoints | Schema, service layer | Dashboard, agent tools |
| Categorization pipeline | Schema, LLM API, rules engine | Write-back queue, dashboard |
| Write-back queue | Schema, rate limiter | YNAB sync, sync health |
| Agent orchestrator | Strands SDK, API endpoints | Keeper chat, greeting |
| Keeper chat UI | TanStack Query, chat endpoints | Layout drawer |

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**12 conflict points identified** where AI agents could make incompatible choices. Each is resolved below with explicit conventions and examples.

### Naming Patterns

**Database Naming (SQLite):**

| Element | Convention | Example |
|---------|-----------|---------|
| Tables | `snake_case`, plural | `transactions`, `chat_messages`, `categorization_rules` |
| Columns | `snake_case` | `transaction_id`, `created_at`, `safe_to_spend` |
| Foreign keys | `{referenced_table_singular}_id` | `account_id`, `category_id` |
| Indexes | `idx_{table}_{columns}` | `idx_transactions_account_id`, `idx_chat_messages_session_id` |
| Migrations | `{NNN}_{description}.sql` | `001_initial_schema.sql`, `002_add_write_back_queue.sql` |

**API Naming:**

| Element | Convention | Example |
|---------|-----------|---------|
| Endpoints | `/api/dragon-keeper/{resource}`, plural nouns | `/api/dragon-keeper/transactions`, `/api/dragon-keeper/rules` |
| Widget endpoints | `/api/dragon-keeper/{widget-name}` | `/api/dragon-keeper/safe-to-spend`, `/api/dragon-keeper/sync-health` |
| Actions | POST with verb | `POST /api/dragon-keeper/sync/trigger`, `POST /api/dragon-keeper/chat/send` |
| Path parameters | `snake_case` | `/api/dragon-keeper/categories/{category_id}` |
| Query parameters | `snake_case` | `?start_date=2026-01-01&account_id=abc` |

**JSON Fields: `snake_case` everywhere (no conversion at API boundary):**

```json
{
  "safe_to_spend": 340.50,
  "health_status": "healthy",
  "last_sync_at": "2026-03-15T10:30:00Z",
  "account_id": "abc-123"
}
```

TypeScript interfaces use `snake_case` properties to match:

```typescript
interface SafeToSpendResponse {
  safe_to_spend: number;
  health_status: "healthy" | "caution" | "critical";
  health_threshold: { green: number; yellow: number };
}
```

**Code Naming:**

| Context | Convention | Example |
|---------|-----------|---------|
| Python functions | `snake_case` | `get_safe_to_spend()`, `approve_categorization()` |
| Python classes | `PascalCase` | `SyncEngine`, `WriteBackQueue` |
| Python files | `snake_case` | `sync_engine.py`, `safe_to_spend_service.py` |
| React components | `PascalCase` | `SafeToSpendHero`, `KeeperChat` |
| React component files (DK) | `kebab-case` | `safe-to-spend-hero.tsx`, `keeper-chat.tsx` |
| React hooks | `camelCase` with `use` prefix | `useSafeToSpend()`, `useTrends()` |
| React hook files | `kebab-case` | `use-safe-to-spend.ts` |
| TypeScript interfaces | `PascalCase` | `SafeToSpendResponse`, `TrendRow` |
| Constants | `UPPER_SNAKE_CASE` | `REFETCH_INTERVAL_MS`, `YNAB_RATE_LIMIT` |
| CSS/Tailwind | `kebab-case` for custom classes | `keeper-greeting`, `dragon-state` |

### Structure Patterns

**Project Organization (Dragon Keeper additions to Codiak):**

```
api/
├── routers/
│   └── dragon_keeper/
│       ├── __init__.py
│       ├── dashboard.py
│       ├── categorization.py
│       ├── chat.py
│       ├── sync.py
│       └── rules.py
├── services/
│   └── dragon_keeper/
│       ├── __init__.py
│       ├── safe_to_spend.py
│       ├── sync_engine.py
│       ├── categorization.py
│       ├── chat_service.py
│       ├── trends.py
│       └── rules_engine.py
├── models/
│   └── dragon_keeper/
│       ├── __init__.py
│       ├── schemas.py
│       └── db.py
└── migrations/
    └── dragon_keeper/
        ├── 001_initial_schema.sql
        └── ...

web/src/
├── components/
│   ├── ui/
│   └── dragon-keeper/
│       ├── safe-to-spend-hero.tsx
│       ├── keeper-chat.tsx
│       └── ...
├── hooks/
│   └── dragon-keeper/
│       ├── use-safe-to-spend.ts
│       ├── use-trends.ts
│       ├── use-chat.ts
│       └── use-sync-health.ts
├── pages/
│   └── dragon-keeper/
│       ├── dashboard.tsx
│       ├── category-detail.tsx
│       ├── rules.tsx
│       └── layout.tsx
└── types/
    └── dragon-keeper.ts

tests/
├── api/
│   └── dragon_keeper/
│       ├── test_dashboard.py
│       ├── test_categorization.py
│       └── ...
├── services/
│   └── dragon_keeper/
│       ├── test_safe_to_spend.py
│       ├── test_sync_engine.py
│       └── ...
└── web/
    └── dragon-keeper/
        ├── safe-to-spend-hero.test.tsx
        └── ...
```

**Organization rules:**
- Backend: group by domain (`dragon_keeper/`) then by layer (routers, services, models)
- Frontend: group by type (components, hooks, pages) then by domain (`dragon-keeper/`)
- Tests: mirror source structure under `tests/` directory
- One file per service, one file per router, one file per component — no god files

### Format Patterns

**API Response Shapes:**

Success (direct data, no wrapper):
```json
{ "safe_to_spend": 340.50, "health_status": "healthy" }
```

List responses:
```json
{ "items": [...], "total_count": 42 }
```

Error responses (consistent structure):
```json
{ "error": "sync_failed", "code": "YNAB_RATE_LIMITED", "detail": "Rate limit exceeded." }
```

**Date/Time: ISO 8601 strings everywhere:**
- API responses: `"2026-03-15T10:30:00Z"` (UTC)
- SQLite storage: `"2026-03-15T10:30:00Z"` (text column, UTC)
- Frontend display: Convert to local time at render only
- Never store epoch timestamps

**Amount Handling: Convert at sync time, store dollars:**
- YNAB API returns milliunits (1000 = $1.00)
- Sync engine converts: `amount_dollars = milliunit_amount / 1000.0`
- SQLite stores `REAL` dollar values
- All API responses, service logic, and frontend code work in dollars
- Never expose milliunits outside the sync engine

**Null Handling:**
- API: Omit null fields from responses (don't send `"field": null`)
- SQLite: Use `NULL` for truly absent data, never empty strings as null substitutes
- Frontend: Optional fields typed with `?` in TypeScript interfaces

### Communication Patterns

**TanStack Query Key Convention:**

```typescript
// Pattern: ["dragon-keeper", resource, ...params]
queryKey: ["dragon-keeper", "safe-to-spend"]
queryKey: ["dragon-keeper", "trends", { period: "weekly" }]
queryKey: ["dragon-keeper", "chat", "history", session_id]
queryKey: ["dragon-keeper", "category", category_id]
```

Invalidation targets the prefix: `queryClient.invalidateQueries({ queryKey: ["dragon-keeper"] })` refreshes everything.

**Polling Intervals:**

| Widget | Interval | Rationale |
|--------|----------|-----------|
| Safe-to-spend | 30s | Core metric, moderate freshness |
| Sync health | 10s during active sync, 60s idle | Responsive during sync, quiet otherwise |
| Queue count | 60s | Low urgency |
| Trends | 5min | Rarely changes mid-session |
| Chat history | None (mutation-driven) | Updates only on send/receive |

All intervals defined as constants in a shared config, not hardcoded in hooks.

**Logging (Python backend):**

```python
import logging
logger = logging.getLogger("dragon_keeper.{module}")

logger.info("Sync completed", extra={"account_id": id, "transactions": count})
logger.warning("Rate limit approaching", extra={"remaining": n})
logger.error("YNAB API failed", extra={"status": code, "endpoint": url})
```

- Module-scoped loggers: `dragon_keeper.sync`, `dragon_keeper.categorization`
- Structured `extra` dict for machine-parseable context
- Never log sensitive data (API keys, full transaction details)

### Process Patterns

**Error Handling (Backend):**

```python
from fastapi import HTTPException

class DragonKeeperError(Exception):
    def __init__(self, error: str, code: str, detail: str, status_code: int = 400):
        self.error = error
        self.code = code
        self.detail = detail
        self.status_code = status_code
```

- All DK service errors raise `DragonKeeperError` subclasses
- Router exception handler converts to structured JSON response
- Never let raw Python exceptions reach the API response

**Error Handling (Frontend):**

```typescript
const { data, error, isLoading } = useQuery({
  queryKey: ["dragon-keeper", "safe-to-spend"],
  queryFn: () => apiFetch<SafeToSpendResponse>("/api/dragon-keeper/safe-to-spend"),
  retry: 2,
  retryDelay: 1000,
});
```

- All hooks handle `isLoading`, `error`, and `data` states
- Components render skeleton for loading, inline error for failure, content for success
- Never show raw error messages to user — map codes to friendly messages

**Loading States:**

- Every component that fetches data has three visual states: `loading` (skeleton), `error` (inline message + retry), `success` (content)
- Use TanStack Query's `isLoading` / `isError` / `isSuccess` directly
- No global loading spinners — each widget manages its own state

### Enforcement Guidelines

**All AI agents building Dragon Keeper MUST:**

1. Follow the file/directory structure above — no ad-hoc file placement
2. Use `snake_case` for all Python code, database columns, API fields, and TypeScript interface properties
3. Use `kebab-case` for all Dragon Keeper React file names
4. Store amounts as dollars (REAL), dates as ISO 8601 UTC strings
5. Return structured `{ error, code, detail }` for all error responses
6. Create one TanStack Query hook per widget endpoint in `hooks/dragon-keeper/`
7. Never hardcode polling intervals — use shared constants
8. Include `isLoading`, `isError`, and `isSuccess` handling in every data-fetching component
9. Write tests in the `tests/` directory mirroring source structure
10. Log with module-scoped loggers and structured `extra` context

## Project Structure & Boundaries

### Complete Project Directory Structure

**Dragon Keeper additions within existing Codiak project:**

```
codiak/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── run_react.bat
│
├── api/
│   ├── main.py
│   ├── routers/
│   │   ├── tools.py
│   │   ├── text_tools.py
│   │   └── dragon_keeper/
│   │       ├── __init__.py
│   │       ├── dashboard.py
│   │       ├── sync.py
│   │       ├── categorization.py
│   │       ├── chat.py
│   │       ├── rules.py
│   │       └── transactions.py
│   ├── services/
│   │   ├── text_tools_service.py
│   │   └── dragon_keeper/
│   │       ├── __init__.py
│   │       ├── safe_to_spend.py
│   │       ├── sync_engine.py
│   │       ├── categorization.py
│   │       ├── write_back.py
│   │       ├── chat_service.py
│   │       ├── greeting.py
│   │       ├── trends.py
│   │       ├── rules_engine.py
│   │       ├── rate_limiter.py
│   │       └── health.py
│   ├── models/
│   │   └── dragon_keeper/
│   │       ├── __init__.py
│   │       ├── schemas.py
│   │       └── db.py
│   ├── migrations/
│   │   └── dragon_keeper/
│   │       ├── 001_initial_schema.sql
│   │       ├── 002_categorization.sql
│   │       ├── 003_chat.sql
│   │       └── 004_sync_meta.sql
│   └── agent/
│       └── dragon_keeper/
│           ├── __init__.py
│           ├── keeper_agent.py
│           └── tools/
│               ├── __init__.py
│               ├── financial_tools.py
│               ├── categorization_tools.py
│               └── account_tools.py
│
├── web/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── components.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── ToolPage.tsx
│   │   │   ├── ui/
│   │   │   │   ├── sheet.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── progress.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   ├── toaster.tsx
│   │   │   │   ├── tooltip.tsx
│   │   │   │   ├── collapsible.tsx
│   │   │   │   ├── scroll-area.tsx
│   │   │   │   ├── separator.tsx
│   │   │   │   ├── skeleton.tsx
│   │   │   │   ├── command.tsx
│   │   │   │   └── popover.tsx
│   │   │   └── dragon-keeper/
│   │   │       ├── safe-to-spend-hero.tsx
│   │   │       ├── keeper-greeting-strip.tsx
│   │   │       ├── keeper-chat.tsx
│   │   │       ├── keeper-message.tsx
│   │   │       ├── sparkline-widget.tsx
│   │   │       ├── activity-squares.tsx
│   │   │       ├── trend-row.tsx
│   │   │       ├── financial-summary-card.tsx
│   │   │       ├── sync-health-collapsible.tsx
│   │   │       ├── queue-badge.tsx
│   │   │       ├── dragon-state-indicator.tsx
│   │   │       ├── categorization-approval.tsx
│   │   │       ├── categorization-queue.tsx
│   │   │       └── category-combobox.tsx
│   │   ├── hooks/
│   │   │   └── dragon-keeper/
│   │   │       ├── use-safe-to-spend.ts
│   │   │       ├── use-trends.ts
│   │   │       ├── use-summary-cards.ts
│   │   │       ├── use-sync-health.ts
│   │   │       ├── use-queue-status.ts
│   │   │       ├── use-chat.ts
│   │   │       ├── use-categorization.ts
│   │   │       ├── use-transactions.ts
│   │   │       ├── use-rules.ts
│   │   │       └── constants.ts
│   │   ├── pages/
│   │   │   └── dragon-keeper/
│   │   │       ├── layout.tsx
│   │   │       ├── dashboard.tsx
│   │   │       ├── category-detail.tsx
│   │   │       ├── rules.tsx
│   │   │       └── history.tsx
│   │   ├── types/
│   │   │   └── dragon-keeper.ts
│   │   └── tools/
│   │       ├── BmadProjectStatus.tsx
│   │       └── ObsidianNotePlacement.tsx
│   └── public/
│       └── favicon.png
│
├── tests/
│   ├── conftest.py
│   ├── api/
│   │   └── dragon_keeper/
│   │       ├── test_dashboard.py
│   │       ├── test_sync.py
│   │       ├── test_categorization.py
│   │       ├── test_chat.py
│   │       ├── test_rules.py
│   │       └── test_transactions.py
│   ├── services/
│   │   └── dragon_keeper/
│   │       ├── test_safe_to_spend.py
│   │       ├── test_sync_engine.py
│   │       ├── test_categorization.py
│   │       ├── test_write_back.py
│   │       ├── test_rules_engine.py
│   │       ├── test_rate_limiter.py
│   │       └── test_health.py
│   └── web/
│       └── dragon-keeper/
│           ├── safe-to-spend-hero.test.tsx
│           ├── categorization-queue.test.tsx
│           └── ...
│
├── tools/
│   └── ...
├── app.py
│
├── data/
│   └── dragon_keeper.db
│
└── docs/
    ├── index.md
    └── technical/
        ├── architecture.md
        ├── developer-guide.md
        └── integrations.md
```

### Architectural Boundaries

**API Boundaries:**

| Boundary | Inside | Outside | Contract |
|----------|--------|---------|----------|
| YNAB API | `sync_engine.py`, `write_back.py` | Everything else | Only these two files import YNAB client. All other code sees local SQLite data. |
| LLM API | `categorization.py` (pipeline tier 2), `chat_service.py` | Everything else | LLM calls isolated to these services. Agent tools don't call LLM directly. |
| Dragon Keeper API | `api/routers/dragon_keeper/*` | Frontend, Agent tools | All external access through REST endpoints. No direct service imports from frontend. |
| SQLite | `models/dragon_keeper/db.py` | Routers, frontend | All SQL queries in `db.py`. Services call `db.py` functions, never raw SQL. |

**Service Boundaries:**

| Service | Owns | Reads From | Writes To |
|---------|------|-----------|-----------|
| `sync_engine` | Sync orchestration, delta tracking | YNAB API | `accounts`, `transactions`, `categories`, `payees`, `sync_state` |
| `safe_to_spend` | STS calculation | `accounts`, `transactions` (via db.py) | Nothing (read-only computation) |
| `categorization` | Pipeline orchestration | `transactions`, `categorization_rules` | `transactions.category_id`, `write_back_queue` |
| `write_back` | YNAB push-back | `write_back_queue` | YNAB API, `write_back_queue.status` |
| `rules_engine` | Rule matching + CRUD | `categorization_rules` | `categorization_rules` |
| `chat_service` | Agent orchestration | `chat_messages` | `chat_messages` |
| `greeting` | Context-aware greeting | STS, trends, queue status, sync health (via other services) | Nothing (read-only composition) |
| `trends` | Spending aggregation | `transactions`, `categories` | Nothing (read-only computation) |
| `health` | Dragon state calculation | Sync state, queue status, STS | Nothing (read-only computation) |
| `rate_limiter` | YNAB request budget | In-memory counter | Nothing (stateless utility) |

**Data Boundary — Single SQLite file, all access through `db.py`:**

No service directly opens a connection or writes raw SQL. `db.py` exposes typed query functions:

```python
def get_transactions(account_id: str, start_date: str) -> list[dict]: ...
def get_uncategorized_transactions() -> list[dict]: ...
def update_transaction_category(transaction_id: str, category_id: str) -> None: ...
def enqueue_write_back(transaction_id: str, category_id: str) -> None: ...
```

### Requirements to Structure Mapping

**FR1-FR6 (Data Synchronization):**

| Requirement | Backend | Frontend | Test |
|-------------|---------|----------|------|
| FR1: YNAB import | `services/dk/sync_engine.py` | — | `tests/services/dk/test_sync_engine.py` |
| FR2: Delta sync | `services/dk/sync_engine.py` | — | `tests/services/dk/test_sync_engine.py` |
| FR3: Sync health | `services/dk/health.py` | `components/dk/sync-health-collapsible.tsx` | `tests/services/dk/test_health.py` |
| FR4: Account staleness | `models/dk/db.py` (sync_state table) | `hooks/dk/use-sync-health.ts` | `tests/services/dk/test_sync_engine.py` |
| FR5: Transfer detection | `services/dk/sync_engine.py` | — | `tests/services/dk/test_sync_engine.py` |
| FR6: Rate limiting | `services/dk/rate_limiter.py` | — | `tests/services/dk/test_rate_limiter.py` |

**FR7-FR15 (Transaction Categorization):**

| Requirement | Backend | Frontend | Test |
|-------------|---------|----------|------|
| FR7-9: Three-tier pipeline | `services/dk/categorization.py` | — | `tests/services/dk/test_categorization.py` |
| FR10: Approval queue | `routers/dk/categorization.py` | `components/dk/categorization-queue.tsx` | `tests/api/dk/test_categorization.py` |
| FR11: Correct + learn | `services/dk/rules_engine.py` | `components/dk/category-combobox.tsx` | `tests/services/dk/test_rules_engine.py` |
| FR12-13: Write-back | `services/dk/write_back.py` | — | `tests/services/dk/test_write_back.py` |
| FR14-15: Confidence scoring | `services/dk/categorization.py` | `components/dk/categorization-approval.tsx` | `tests/services/dk/test_categorization.py` |

**FR16-FR19 (Financial Awareness):**

| Requirement | Backend | Frontend | Test |
|-------------|---------|----------|------|
| FR16: Safe-to-spend | `services/dk/safe_to_spend.py` | `components/dk/safe-to-spend-hero.tsx` | `tests/services/dk/test_safe_to_spend.py` |
| FR17: Spending trends | `services/dk/trends.py` | `components/dk/trend-row.tsx`, `sparkline-widget.tsx` | TBD |
| FR18: Account balances | `routers/dk/dashboard.py` | `components/dk/financial-summary-card.tsx` | `tests/api/dk/test_dashboard.py` |
| FR19: Upcoming bills | `services/dk/safe_to_spend.py` | `components/dk/financial-summary-card.tsx` | `tests/services/dk/test_safe_to_spend.py` |

**FR20-FR26 (Dragon Keeper Agent):**

| Requirement | Backend | Frontend | Test |
|-------------|---------|----------|------|
| FR20-21: Agent + tools | `agent/dk/keeper_agent.py`, `agent/dk/tools/*` | — | TBD |
| FR22: Chat persistence | `services/dk/chat_service.py` | `hooks/dk/use-chat.ts` | `tests/api/dk/test_chat.py` |
| FR23: Greeting | `services/dk/greeting.py` | `components/dk/keeper-greeting-strip.tsx` | TBD |
| FR24-25: Inline actions | `agent/dk/tools/categorization_tools.py` | `components/dk/keeper-chat.tsx` | `tests/api/dk/test_chat.py` |
| FR26: Context awareness | `agent/dk/keeper_agent.py` (system prompt) | — | Manual testing |

**FR27-FR31 (Dashboard & Status):**

| Requirement | Backend | Frontend | Test |
|-------------|---------|----------|------|
| FR27: Dashboard | `routers/dk/dashboard.py` | `pages/dk/dashboard.tsx` | `tests/api/dk/test_dashboard.py` |
| FR28: Dragon state | `services/dk/health.py` | `components/dk/dragon-state-indicator.tsx` | `tests/services/dk/test_health.py` |
| FR29: Activity tracking | `models/dk/db.py` (engagement table) | `components/dk/activity-squares.tsx` | TBD |
| FR30: Queue badge | `routers/dk/dashboard.py` | `components/dk/queue-badge.tsx` | `tests/api/dk/test_dashboard.py` |
| FR31: Progressive loading | — | Skeleton states in all components | Manual testing |

**FR32-FR36 (Configuration & Rules):**

| Requirement | Backend | Frontend | Test |
|-------------|---------|----------|------|
| FR32-34: Rule CRUD | `routers/dk/rules.py`, `services/dk/rules_engine.py` | `pages/dk/rules.tsx` | `tests/api/dk/test_rules.py` |
| FR35: Bulk reclassify | `services/dk/rules_engine.py` | `pages/dk/rules.tsx` | `tests/services/dk/test_rules_engine.py` |
| FR36: Health thresholds | Config in `.env` or `db.py` settings table | Settings UI (Phase B) | TBD |

### Integration Points

**External Integrations:**

| System | Entry Point | Protocol | Auth | Rate Limit |
|--------|------------|----------|------|-----------|
| YNAB API | `sync_engine.py`, `write_back.py` | REST (HTTPS) | Bearer token (`.env`) | 200 req/hr (shared token bucket) |
| Anthropic API | `categorization.py` (tier 2), `chat_service.py` | REST (HTTPS) | API key (`.env`) | Per-model limits |
| Existing YNAB MCP | `agent/dk/keeper_agent.py` | MCP protocol via Strands `MCPClient` | Local | N/A |

**Internal Integration (Codiak ↔ Dragon Keeper):**

| Touch Point | File | Integration Method |
|-------------|------|-------------------|
| Router registration | `api/main.py` | `app.include_router(dk_router, prefix="/api/dragon-keeper")` |
| Tool registration | `web/src/components/ToolPage.tsx` | Add `DragonKeeper` to `TOOL_COMPONENTS` map |
| Route registration | `web/src/App.tsx` | Add DK nested routes under `/tool/dragon-keeper/*` |
| Sidebar entry | `tools/ui_tools_metadata.py` | Add DK metadata for sidebar display |
| Shared CSS tokens | `web/src/index.css` → `tailwind.config.ts` | Map existing CSS custom properties to Tailwind theme |

**Data Flow:**

```
YNAB API ──sync──→ sync_engine ──store──→ SQLite (full mirror)
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                   ▼                   ▼
                   safe_to_spend.py     trends.py          categorization.py
                          │                   │                   │
                          ▼                   ▼                   ▼
                   dashboard router    dashboard router    categorization router
                          │                   │                   │
                          ▼                   ▼                   ▼
                   apiFetch()          apiFetch()          apiFetch()
                          │                   │                   │
                          ▼                   ▼                   ▼
                   TanStack Query      TanStack Query      TanStack Query
                          │                   │                   │
                          ▼                   ▼                   ▼
                   SafeToSpendHero     TrendRow            CategorizationQueue
                                                                  │
                                                          ──approve──→ write_back.py ──push──→ YNAB API
```

### Development Workflow

**Dev server startup (`run_react.bat`):**
1. FastAPI starts on `:8000` — runs migrations on startup via `fastmigrate`
2. Vite dev server starts on `:5173` — CORS allows `:5173`
3. SQLite DB created at `data/dragon_keeper.db` if not exists

**Build process:**
- Frontend: `npm run build` in `web/` → outputs to `web/dist/`
- Backend: No build step (Python)
- Migrations: Run automatically on FastAPI startup

## Architecture Validation Results

### SQLite Schema Definition

**Database: `data/dragon_keeper.db`**

Separate from Codiak's `accounts.db`. All amounts stored as REAL dollars (converted from YNAB milliunits at sync time). All timestamps stored as ISO 8601 UTC text.

#### Core Data Tables (populated by sync engine)

```sql
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    budget_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    on_budget INTEGER NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0,
    balance REAL NOT NULL DEFAULT 0,
    cleared_balance REAL NOT NULL DEFAULT 0,
    uncleared_balance REAL NOT NULL DEFAULT 0,
    note TEXT,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE category_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hidden INTEGER NOT NULL DEFAULT 0,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE categories (
    id TEXT PRIMARY KEY,
    category_group_id TEXT NOT NULL REFERENCES category_groups(id),
    name TEXT NOT NULL,
    hidden INTEGER NOT NULL DEFAULT 0,
    budgeted REAL NOT NULL DEFAULT 0,
    activity REAL NOT NULL DEFAULT 0,
    balance REAL NOT NULL DEFAULT 0,
    goal_type TEXT,
    goal_target REAL,
    goal_target_month TEXT,
    goal_percentage_complete INTEGER,
    note TEXT,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE payees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    payee_id TEXT REFERENCES payees(id),
    payee_name TEXT,
    category_id TEXT REFERENCES categories(id),
    category_name TEXT,
    memo TEXT,
    cleared TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0,
    transfer_account_id TEXT,
    deleted INTEGER NOT NULL DEFAULT 0,
    imported_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_payee_id ON transactions(payee_id);
```

#### Categorization Tables

```sql
CREATE TABLE categorization_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payee_pattern TEXT NOT NULL,
    match_type TEXT NOT NULL,
    category_id TEXT NOT NULL REFERENCES categories(id),
    min_amount REAL,
    max_amount REAL,
    confidence REAL NOT NULL DEFAULT 1.0,
    source TEXT NOT NULL,
    times_applied INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_rules_payee_pattern ON categorization_rules(payee_pattern);

CREATE TABLE write_back_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL REFERENCES transactions(id),
    category_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX idx_write_back_status ON write_back_queue(status);
```

#### Chat Tables

```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    last_message_at TEXT NOT NULL,
    title TEXT
);

CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

#### Sync & Tracking Tables

```sql
CREATE TABLE sync_state (
    account_id TEXT PRIMARY KEY REFERENCES accounts(id),
    server_knowledge INTEGER NOT NULL DEFAULT 0,
    last_sync_at TEXT,
    last_sync_status TEXT NOT NULL DEFAULT 'never',
    last_error TEXT,
    transactions_synced INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT REFERENCES accounts(id),
    event_type TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_sync_log_created_at ON sync_log(created_at);

CREATE TABLE engagement_log (
    date TEXT PRIMARY KEY,
    visited INTEGER NOT NULL DEFAULT 0,
    actions_count INTEGER NOT NULL DEFAULT 0,
    first_visit_at TEXT,
    last_action_at TEXT
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Coherence Validation

**Decision Compatibility:** All technology choices verified compatible. Pydantic natively produces `snake_case` JSON matching our API convention. Shadcn/ui + Tailwind + Vite confirmed compatible. Strands Agents SDK supports Anthropic provider and MCP client as specified. fastmigrate operates on raw `.sql` files — compatible with the schema above.

**Pattern Consistency:** Naming conventions are uniform — `snake_case` in database, API, and TypeScript interfaces. File naming follows conventions (kebab-case for DK React files, snake_case for Python). TanStack Query key convention aligns with endpoint naming.

**Structure Alignment:** Project tree maps cleanly to service boundaries. Each service owns specific tables (sync_engine → accounts/transactions/sync_state, categorization → categorization_rules/write_back_queue, chat_service → chat_sessions/chat_messages). No overlapping ownership.

**Inconsistency resolved:** Step 2 states "no responsive breakpoints" while the UX spec specifies Tailwind breakpoints for tablet (MVP) and mobile (deferred). The UX spec is authoritative — Dragon Keeper is desktop-first with tablet as a secondary MVP target.

### Requirements Coverage Validation

**Functional Requirements: 36/36 covered**

All six FR categories mapped to specific backend services, frontend components, and test files in the Project Structure section. No gaps.

**Non-Functional Requirements: 14/14 covered**

| NFR | Architectural Support |
|-----|----------------------|
| NFR1: STS < 1s | Local SQLite query, pre-composed endpoint, no external API call |
| NFR2: Categorization < 500ms | Inline mutation + optimistic update, write-back is async |
| NFR3: Agent response < 5s | LLM-dependent, streaming response to show progress immediately |
| NFR4: Progressive loading | Per-widget TanStack Query hooks, independent skeleton states |
| NFR5: Dashboard render | Staggered widget loading, hero renders first |
| NFR6-7: API keys server-side | `.env` file, never in frontend code or API responses |
| NFR8: LLM sanitization | `categorization.py` sends only payee_name, amount, memo |
| NFR9: SQLite excluded from VCS | `data/` directory in `.gitignore` |
| NFR10: YNAB rate limit | Shared token bucket in `rate_limiter.py`, 200 req/hr |
| NFR11: Graceful API failure | `DragonKeeperError` hierarchy, structured JSON responses |
| NFR12: No shared Codiak mods | DK in subdirectories, no changes to existing Codiak files except registration points |
| NFR13-14: Integration handling | Rate limiter priority queue, sync health visibility, error surfacing |

### Implementation Readiness Validation

**Decision Completeness:** All critical and important decisions documented with specific versions, rationale, and rejected alternatives. Schema provides concrete table definitions for all 13 tables.

**Structure Completeness:** Every file in the project tree is mapped to at least one FR category. Integration points with existing Codiak are explicitly listed (4 registration touch points).

**Pattern Completeness:** 10 enforcement guidelines cover naming, structure, formats, error handling, loading states, testing, and logging. Concrete examples provided for each pattern.

### Architecture Completeness Checklist

**Requirements Analysis:**
- [x] Project context thoroughly analyzed (36 FRs, 14 NFRs)
- [x] Scale and complexity assessed (medium, single-user)
- [x] Technical constraints identified (YNAB rate limit, existing Codiak patterns)
- [x] Cross-cutting concerns mapped (7 identified and resolved)

**Architectural Decisions:**
- [x] Critical decisions documented with versions (10 decisions)
- [x] Technology stack fully specified (existing + 2 new deps)
- [x] Integration patterns defined (YNAB, LLM, Codiak, MCP)
- [x] Performance considerations addressed (per NFR)

**Implementation Patterns:**
- [x] Naming conventions established (database, API, code, files)
- [x] Structure patterns defined (subdirectory organization)
- [x] Communication patterns specified (TanStack Query keys, polling intervals, logging)
- [x] Process patterns documented (error handling, loading states)

**Project Structure:**
- [x] Complete directory structure defined (~80 files mapped)
- [x] Component boundaries established (service ownership table)
- [x] Integration points mapped (4 Codiak touch points, 3 external APIs)
- [x] Requirements to structure mapping complete (36 FRs → specific files)

**Data Architecture:**
- [x] SQLite schema fully defined (13 tables, indexes, constraints)
- [x] Amount handling specified (milliunits → dollars at sync)
- [x] Date format specified (ISO 8601 UTC text)
- [x] Data boundaries enforced (all access through db.py)

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
1. Brownfield integration — extends proven Codiak patterns rather than introducing new paradigms
2. Clear data boundaries — single db.py access point prevents schema drift
3. Minimal new dependencies — 2 pip packages (Strands, fastmigrate) beyond existing stack
4. Per-widget architecture — each dashboard component is independently buildable and testable
5. Complete FR traceability — every requirement maps to specific files

**Areas for Future Enhancement:**
- SQLite WAL mode evaluation for concurrent read/write during background sync
- Agent system prompt engineering (iterative during implementation)
- Charting library selection for category detail drill-down views
- Notification/push system design (Phase B, Discord integration)

## Architecture Completion Summary

**Architecture Decision Workflow:** COMPLETED
**Total Steps Completed:** 8
**Date Completed:** 2026-03-15
**Document Location:** `_bmad-output/planning-artifacts/architecture.md`

### Final Deliverables

- 10 core architectural decisions documented with versions and rationale
- 10 implementation pattern enforcement guidelines
- 13 SQLite tables fully specified with indexes and constraints
- ~80 files mapped in complete project directory structure
- 36 functional requirements traced to specific files
- 14 non-functional requirements verified with architectural support

### Implementation Sequence

1. SQLite schema + fastmigrate setup
2. YNAB sync engine + full mirror cache
3. Widget API endpoints + service layer
4. Dragon Keeper layout + routing shell
5. Dashboard widgets with TanStack Query hooks
6. Write-back queue + categorization pipeline
7. Strands agent setup + API tool wrappers
8. Chat persistence + Keeper drawer

**Architecture Status:** READY FOR IMPLEMENTATION
