---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain-skipped
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-codiak-2026-03-01.md
  - _bmad-output/analysis/brainstorming-session-2026-03-01.md
  - docs/index.md
  - docs/technical/architecture.md
  - docs/technical/developer-guide.md
  - docs/technical/integrations.md
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 1
  projectDocs: 4
classification:
  projectType: web_app
  domain: personal_finance
  complexity: medium
  projectContext: brownfield
workflowType: 'prd'
---

# Product Requirements Document: Dragon Keeper

**Author:** Master Cody
**Date:** 2026-03-14
**Project:** codiak
**Classification:** Web Application | Personal Finance | Medium Complexity | Brownfield

## Executive Summary

Dragon Keeper is a self-contained financial management module ("wing") within the Codiak platform that replaces the friction-heavy YNAB interface with an agent-first, narrative-driven tool for one household's financial life. Built on Codiak's existing React + FastAPI stack with YNAB as the data backend, Dragon Keeper addresses a specific behavioral loop: uncertain checking balance -> credit card used as safety net -> debt accumulates -> YNAB friction kills engagement -> cycle deepens.

**The core value proposition:** A trustworthy safe-to-spend number powered by automated categorization, delivered through a conversational AI agent (The Keeper) that pushes daily financial awareness rather than waiting for the user to open a dashboard.

**Key differentiators:**
- **Agent-first architecture** -- the Keeper is the primary interface; the dashboard is secondary
- **Trust-first transparency** -- data quality metrics surfaced, not hidden
- **Narrative gamification** -- debt as a dragon, family as co-adventurers
- **Obsidian knowledge bridge** (future) -- personal knowledge context no fintech can replicate

**Project context:** Brownfield. Codiak has 36+ existing tools, 14 of which are fragmented YNAB Streamlit modules with ~7,500 lines of duplicated code. Dragon Keeper consolidates these into a unified experience within the React + FastAPI migration target.

**Builder context:** Personal learning project for a solo developer. No market pressure, no investors, no deadline. The tool is the goal; learning is a bonus. Success = daily use that changes financial behavior.

## Success Criteria

### User Success

- Daily engagement with Keeper or dashboard 5 of 7 days/week within first month
- Credit card non-use streak reaches 14+ days within 6 months
- Transaction categorization rate >= 80% (auto + manual combined)
- Daily categorization validation takes < 2 minutes
- Safe-to-spend number trusted and checked before discretionary purchases
- Tool retention: active use sustained 4+ consecutive weeks (YNAB death spiral broken)

### Life Outcomes

- Checking account cushion grows from $0 baseline toward $1,000 at 6 months
- Credit card debt reduced 15% at 6 months, 30% at 12 months
- Monthly interest charges show decreasing trend
- 2+ unnecessary subscriptions identified and cancelled
- Amanda participates in monthly budget conversations using Keeper data by Month 2
- Tool still in active daily use at 6 months

### Technical Success

- Dragon Keeper wing self-contained within Codiak -- no regressions to existing tools
- YNAB API rate limits (200 req/hr) respected with no user-facing failures
- Auto-categorization pipeline runs reliably on each import
- Keeper agent responses contextually relevant and grounded in real financial data
- SQLite cache maintains consistency with YNAB as source of truth

### MVP Go/No-Go Gates

1. Categorization rate >= 80%
2. Daily engagement 5/7 days for 4 consecutive weeks
3. At least one instance of choosing debit over credit card because safe-to-spend was trusted
4. Categorization validation < 2 minutes/day
5. Active use sustained 4 full weeks without abandonment

All 5 met after 4 weeks -> proceed to Phase B. Gate #5 fails -> diagnose friction before adding features.

## Product Scope & Phased Development

### MVP Strategy

**Approach:** Problem-solving MVP -- deliver the minimum that changes daily financial behavior. The core bet: a trustworthy safe-to-spend number with low-friction categorization breaks the credit card safety-net cycle. The agent enhances engagement but isn't required for the behavioral shift.

**Resource reality:** Solo developer with a day job. Each component should be independently useful. The phased roadmap is a sequence, not a sprint plan.

### Phase A -- MVP ("I Can Trust This")

| Priority | Component | Rationale | Depends On |
|----------|-----------|-----------|------------|
| P0 | Data Layer (YNAB import, SQLite cache, sync health) | Foundation -- everything reads from this | Nothing |
| P0 | Auto-categorization pipeline (rules -> LLM -> user queue) | Safe-to-spend accuracy depends on categorization | Data Layer |
| P0 | Safe-to-spend number | The core behavior-changing value | Data Layer, Categorization |
| P0 | Three-second dashboard | Primary UI surface for daily use | Data Layer, Safe-to-spend |
| P1 | Keeper chat agent (LLM + MCP tools) | Engagement differentiator; can ship after P0 | Data Layer |

**Can be manual initially:** Streak tracking (simple counter), dragon state (static indicator), transfer detection (flag via rules).

### Phase B -- Engagement (after 4-week MVP validation)

- Daily Keeper push via Slack
- Subscription detection with renewal warnings
- Streak gamification and dragon state changes
- Paycheck tracer
- Conversational categorization via Slack

### Phase C -- Family (after daily habit proven)

- Family narrative view with privacy shields
- Interactive dragon visualization
- Balance trends and Dollar River (Sankey) spending flow
- Family quest board

### Phase D -- Intelligence (3-6 months)

- Lifetime financial projections through retirement
- Scenario simulator with interactive sliders
- Debt archaeology and interest tracking
- Financial Freedom Index

### Phase E -- Expansion (6+ months)

- Voice interface, Amazon/PayPal transaction decoding
- Obsidian knowledge bridge, multi-channel agent
- Two-income battle plan

### Risk Mitigation

**Technical Risks:**
- *Keeper agent complexity:* P0/P1 split -- ship data pipeline + dashboard first, add agent second
- *YNAB API rate limits:* All reads from local SQLite; API calls only on manual import
- *LLM categorization accuracy:* Three-tier design improves over time as rules learning captures corrections

**Resource Risks:**
- *Solo developer burnout:* Independent value at each phase; no all-or-nothing launch
- *Scope creep:* 5 explicit go/no-go gates before Phase B

## User Journeys

### Journey 1: Cody's First Day -- "Can I Trust This Thing?"

**Opening Scene:** Saturday morning. 14 fragmented YNAB Streamlit tools, a growing credit card balance, flying blind. Cody opens Dragon Keeper for the first time.

**Rising Action:** Import button. YNAB data flows into SQLite -- accounts, transactions, categories. Sync health lights up green. Auto-categorization runs: 70% by rules, 10% by LLM with high confidence. 15 transactions land in the validation queue. He taps through them in under 2 minutes.

**Climax:** The safe-to-spend number appears -- big, bold, lower than expected. The Keeper says: "You've got $340 safe to spend. Your phone bill hits in 3 days." For the first time in months, Cody knows exactly where he stands.

**Resolution:** He goes to lunch and pays with the debit card.

**Capabilities revealed:** Data import, sync health, auto-categorization pipeline, validation queue, safe-to-spend calculation, Keeper messaging, dashboard.

### Journey 2: Daily Check-in -- "30 Seconds and I'm Done"

**Opening Scene:** Tuesday morning, Week 3. Coffee brewing. Dragon Keeper is routine.

**Rising Action:** Dashboard loads: safe-to-spend $215 (yellow), categorization 94%, streak 18 days. Keeper chat: "3 new transactions, all auto-categorized. $47 Amazon charge filed under household supplies. Sound right?" Cody types "yep."

**Climax:** "Can we afford takeout tonight?" Keeper: "$215 safe to spend, groceries covered. $40 takeout leaves $175 with 4 days to payday. Tight but doable." Decision made with real data.

**Resolution:** 30-second interaction. No queue, no friction. He starts his day knowing the number.

**Capabilities revealed:** Dashboard summary, streaks, Keeper debrief, conversational approval, natural language Q&A, contextual advice.

### Journey 3: Configurator -- "Teaching the Machine"

**Opening Scene:** Week 2. "Tractor Supply" categorized as "Shopping" instead of "The Farm." Amazon charges dumped into a generic bucket.

**Rising Action:** Rules manager: payee contains "Tractor Supply" -> "The Farm." 12 past transactions reclassified instantly. Amazon flagged for always-manual-review.

**Climax:** Categorization rate jumps from 70% to 82% after rule tuning. The data gets more trustworthy.

**Resolution:** Next month, "Rural King" appears. LLM suggests "The Farm" at 85% confidence based on the farm supply pattern. One-tap approval. The system learns his life.

**Capabilities revealed:** Rules manager, rule CRUD, bulk reclassification, categorization progress, rules learning engine, manual review flagging.

### Journey 4: Recovery -- "The Streak Breaks"

**Opening Scene:** Sick kid, farm emergency, three days of chaos. Monday morning return.

**Rising Action:** Streak at 0. Queue has 11 items. Sync health still green -- data kept flowing. Keeper: "Welcome back. 11 to review, safe-to-spend is $180. Should take about a minute."

**Climax:** 7 of 11 auto-categorized correctly -- just confirm. 4 need decisions. 90 seconds total. Categorization rate barely dipped.

**Resolution:** Streak restarts at 1. No shame, no death spiral. The tool survived a gap without breaking trust.

**Capabilities revealed:** Streak reset, backlog management, graceful degradation, non-judgmental re-engagement, quick recovery flow.

### Journey Requirements Summary

| Journey | Key Capabilities |
|---------|-----------------|
| First Day | Data import, sync health, auto-categorization, validation queue, safe-to-spend, Keeper messaging, dashboard |
| Daily Check-in | Dashboard summary, streaks, Keeper debrief, conversational approval, NL Q&A, contextual advice |
| Configurator | Rules CRUD, bulk reclassification, categorization progress, rules learning, manual review flagging |
| Recovery | Graceful degradation, backlog management, non-judgmental re-engagement, streak reset, quick recovery |

**Deferred (Phase C+):** Amanda's Family View, Harris seeing costs in context, George and the dragon, family quests.

## Innovation & Novel Patterns

### Detected Innovation Areas

**Agent-First Architecture:** The Keeper agent is the primary interface; the dashboard is secondary. No personal finance tool leads with a conversational AI that pushes daily awareness. This inverts the standard interaction model.

**Narrative Gamification:** Debt as a dragon, family as co-adventurers, progress as a quest. Transforms an emotionally charged topic into an engaging shared experience.

**Trust-First Transparency:** Sync health, categorization %, confidence scores surfaced prominently. The system tells you what it knows and what it's unsure about.

**Obsidian Knowledge Bridge (Future):** Personal knowledge management connected to financial tracking -- project priorities, anticipated costs, activity schedules. Unique advantage unavailable to commercial fintech.

### Validation & Fallbacks

- Agent-first fails to engage -> fallback to dashboard-primary with optional chat
- Narrative feels gimmicky -> dragon theme tones down to simple progress indicators
- Transparency creates anxiety -> confidence scores collapse behind a details toggle

## Web Application Technical Requirements

### Architecture

**Frontend (Existing Codiak Patterns):**
- React 18 + TypeScript + Vite
- TanStack Query for server state
- React Router (`/tool/dragon-keeper/*` routes)
- `apiFetch()` wrapper from `web/src/api.ts`

**Backend (Existing Codiak Patterns):**
- FastAPI router at `api/routers/dragon_keeper.py`
- Service layer at `api/services/dragon_keeper/`
- SQLite for local data cache
- YNAB API client with rate limiting

**Data Flow:** Manual import trigger -> YNAB API fetch -> SQLite cache -> API endpoints -> React UI. Refresh-based updates, no WebSocket in MVP. TanStack Query handles caching and refetching.

### Constraints

- Desktop only, modern Chrome/Edge. No mobile, no SEO, no responsive breakpoints.
- Dragon Keeper routes nested under existing Codiak routing
- Registered in `TOOL_COMPONENTS` map in `ToolPage.tsx`
- All API endpoints prefixed `/api/dragon-keeper/`
- Separate SQLite database from existing `accounts.db`

## Functional Requirements

### Data Synchronization

- FR1: Cody can trigger a manual YNAB data import from the UI
- FR2: System imports accounts, transactions, categories, and budgets from YNAB API into local SQLite cache
- FR3: System uses SQLite cache as single source of truth for all read operations
- FR4: Cody can view sync health status per YNAB account (green/yellow/red based on staleness)
- FR5: System detects and flags transfer transactions separately from real spending
- FR6: System tracks last sync time per account and warns when any account exceeds 7 days without sync

### Transaction Categorization

- FR7: System auto-categorizes transactions using a rules engine for known payee patterns
- FR8: System auto-categorizes unmatched transactions using LLM with confidence scoring
- FR9: System auto-applies high-confidence categorizations (above threshold) without user intervention
- FR10: System queues low-confidence categorizations for user validation
- FR11: Cody can review and approve or reject pending categorizations individually
- FR12: System writes approved categorizations back to YNAB with rate limiting
- FR13: Cody can view categorization progress as a percentage of transactions categorized this month
- FR14: System auto-creates categorization rules from repeated user corrections
- FR15: Cody can flag specific payees or patterns to always require manual review

### Financial Awareness

- FR16: Cody can view a safe-to-spend number calculated as checking balance minus pending bills minus budget commitments
- FR17: System color-codes the safe-to-spend number based on financial health thresholds
- FR18: System detects upcoming bills based on recurring transaction patterns
- FR19: Cody can view current balances for all accounts

### Dragon Keeper Agent

- FR20: Cody can chat with the Dragon Keeper agent through a React chat interface
- FR21: Keeper agent can query financial data through tool access to answer questions
- FR22: Keeper agent can present pending categorizations conversationally for approval
- FR23: Keeper agent can generate a daily debrief summarizing spending, streak, one insight, and safe-to-spend
- FR24: Keeper agent can answer natural language questions about spending, balances, and trends
- FR25: Keeper agent contextualizes the safe-to-spend number with a relevant observation
- FR26: Keeper agent displays with a static avatar for persona anchoring

### Dashboard & Status

- FR27: Cody can view a dashboard showing safe-to-spend, dragon state, streak count, categorization percentage, and sync health at a glance
- FR28: Cody can navigate from the dashboard to detailed views for transactions, category breakdowns, and account balances
- FR29: System tracks a daily engagement streak based on consecutive days of interaction
- FR30: System displays a dragon state indicator reflecting overall financial health
- FR31: System handles streak breaks with non-judgmental re-engagement messaging and quick recovery flow

### Configuration & Rules Management

- FR32: Cody can create categorization rules mapping payee patterns to categories
- FR33: Cody can edit and delete existing categorization rules
- FR34: Cody can preview which existing transactions match a rule before applying it
- FR35: Cody can bulk-reclassify past transactions when a new rule is created or modified
- FR36: System applies categorization in priority order: rules engine, then LLM, then manual queue

### Transaction Explorer & Payee Investigation

- FR37: Cody can view all transactions in a paginated, sortable, filterable list (all time)
- FR38: Cody can filter transactions by payee name, category, date range, and amount range (composable filters)
- FR39: When filtered to a payee, system shows transaction count, total amount, date span, category consistency breakdown, and recurring indicator
- FR40: Cody can inline re-categorize individual or bulk-selected transactions from search results
- FR41: Payee names are clickable links throughout Dragon Keeper, opening Transaction Explorer pre-filtered to that payee
- FR42: Keeper agent responses render payee names as clickable verification links to Transaction Explorer

## Non-Functional Requirements

### Performance

- NFR1: Safe-to-spend number renders within 1 second from cached SQLite data
- NFR2: Dashboard widgets load progressively -- safe-to-spend first, other widgets independently
- NFR3: Categorization queue interactions (approve/reject) complete within 500ms per item
- NFR4: YNAB import displays a progress indicator and does not block UI interaction
- NFR5: Keeper agent responses return within 5 seconds for typical financial queries

### Security

- NFR6: YNAB API key stored in environment variables, never in version control or frontend code
- NFR7: All YNAB API communication occurs server-side through FastAPI
- NFR8: SQLite database file excluded from version control
- NFR9: LLM API calls send only payee names, amounts, and memos -- no account numbers or sensitive identifiers

### Integration

- NFR10: YNAB API calls respect the 200 requests/hour rate limit with automatic throttling
- NFR11: YNAB API failures handled gracefully with user-visible messages and no data corruption
- NFR12: YNAB write-back operations batched and rate-limited separately from reads
- NFR13: LLM API failures fall back gracefully -- transactions queue for manual review
- NFR14: Dragon Keeper integrates with existing Codiak infrastructure without modifying shared components
