---
stepsCompleted: [1, 2, 3, 4]
status: 'complete'
completedAt: '2026-03-15'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# Dragon Keeper - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Dragon Keeper, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**Data Synchronization:**
- FR1: Cody can trigger a manual YNAB data import from the UI
- FR2: System imports accounts, transactions, categories, and budgets from YNAB API into local SQLite cache
- FR3: System uses SQLite cache as single source of truth for all read operations
- FR4: Cody can view sync health status per YNAB account (green/yellow/red based on staleness)
- FR5: System detects and flags transfer transactions separately from real spending
- FR6: System tracks last sync time per account and warns when any account exceeds 7 days without sync

**Transaction Categorization:**
- FR7: System auto-categorizes transactions using a rules engine for known payee patterns
- FR8: System auto-categorizes unmatched transactions using LLM with confidence scoring
- FR9: System auto-applies high-confidence categorizations (above threshold) without user intervention
- FR10: System queues low-confidence categorizations for user validation
- FR11: Cody can review and approve or reject pending categorizations individually
- FR12: System writes approved categorizations back to YNAB with rate limiting
- FR13: Cody can view categorization progress as a percentage of transactions categorized this month
- FR14: System auto-creates categorization rules from repeated user corrections
- FR15: Cody can flag specific payees or patterns to always require manual review

**Financial Awareness:**
- FR16: Cody can view a safe-to-spend number calculated as checking balance minus pending bills minus budget commitments
- FR17: System color-codes the safe-to-spend number based on financial health thresholds
- FR18: System detects upcoming bills based on recurring transaction patterns
- FR19: Cody can view current balances for all accounts

**Dragon Keeper Agent:**
- FR20: Cody can chat with the Dragon Keeper agent through a React chat interface
- FR21: Keeper agent can query financial data through tool access to answer questions
- FR22: Keeper agent can present pending categorizations conversationally for approval
- FR23: Keeper agent can generate a daily debrief summarizing spending, streak, one insight, and safe-to-spend
- FR24: Keeper agent can answer natural language questions about spending, balances, and trends
- FR25: Keeper agent contextualizes the safe-to-spend number with a relevant observation
- FR26: Keeper agent displays with a static avatar for persona anchoring

**Dashboard & Status:**
- FR27: Cody can view a dashboard showing safe-to-spend, dragon state, streak count, categorization percentage, and sync health at a glance
- FR28: Cody can navigate from the dashboard to detailed views for transactions, category breakdowns, and account balances
- FR29: System tracks a daily engagement streak based on consecutive days of interaction
- FR30: System displays a dragon state indicator reflecting overall financial health
- FR31: System handles streak breaks with non-judgmental re-engagement messaging and quick recovery flow

**Configuration & Rules Management:**
- FR32: Cody can create categorization rules mapping payee patterns to categories
- FR33: Cody can edit and delete existing categorization rules
- FR34: Cody can preview which existing transactions match a rule before applying it
- FR35: Cody can bulk-reclassify past transactions when a new rule is created or modified
- FR36: System applies categorization in priority order: rules engine, then LLM, then manual queue

### NonFunctional Requirements

**Performance:**
- NFR1: Safe-to-spend number renders within 1 second from cached SQLite data
- NFR2: Dashboard widgets load progressively -- safe-to-spend first, other widgets independently
- NFR3: Categorization queue interactions (approve/reject) complete within 500ms per item
- NFR4: YNAB import displays a progress indicator and does not block UI interaction
- NFR5: Keeper agent responses return within 5 seconds for typical financial queries

**Security:**
- NFR6: YNAB API key stored in environment variables, never in version control or frontend code
- NFR7: All YNAB API communication occurs server-side through FastAPI
- NFR8: SQLite database file excluded from version control
- NFR9: LLM API calls send only payee names, amounts, and memos -- no account numbers or sensitive identifiers

**Integration:**
- NFR10: YNAB API calls respect the 200 requests/hour rate limit with automatic throttling
- NFR11: YNAB API failures handled gracefully with user-visible messages and no data corruption
- NFR12: YNAB write-back operations batched and rate-limited separately from reads
- NFR13: LLM API failures fall back gracefully -- transactions queue for manual review
- NFR14: Dragon Keeper integrates with existing Codiak infrastructure without modifying shared components

### Additional Requirements

**From Architecture:**
- AR1: SQLite schema with 13 tables managed by fastmigrate migrations
- AR2: Strands Agents SDK (v1.29.0) for agent orchestration with API-only data access
- AR3: Custom token bucket rate limiter shared via FastAPI dependency injection
- AR4: Pre-composed widget API endpoints (one endpoint per dashboard widget)
- AR5: Nested layout routes with DragonKeeperLayout wrapping child routes via Outlet
- AR6: Persistent write-back queue (SQLite table) with retry and exponential backoff
- AR7: Persistent chat history in SQLite (survives restart, searchable)
- AR8: Structured JSON error responses ({ error, code, detail }) across all endpoints
- AR9: All amounts stored as dollars (converted from YNAB milliunits at sync time)
- AR10: All dates stored as ISO 8601 UTC text
- AR11: TanStack Query for all server state including Keeper chat
- AR12: Polling via TanStack Query refetchInterval (no WebSocket/SSE)
- AR13: Dragon Keeper code in subdirectories (api/routers/dragon_keeper/, api/services/dragon_keeper/, etc.)
- AR14: All SQL access through models/dragon_keeper/db.py -- no raw SQL in services or routers

**From UX Design:**
- UX1: Shadcn/ui + Tailwind CSS component library with Codiak token mapping
- UX2: Desktop-first layout with Tailwind breakpoints; tablet as secondary MVP target
- UX3: Skeleton loading states for every data-fetching component
- UX4: Toast-based undo pattern for destructive actions (6-second window)
- UX5: Keeper drawer as persistent right-side Sheet (360px), overlay on tablet
- UX6: Three-tier button hierarchy (primary/secondary/tertiary) with categorization-specific variants
- UX7: Inline editing and approval patterns for categorization (approve/correct/skip)
- UX8: Category combobox (searchable select) for corrections with recent categories first
- UX9: KeeperGreetingStrip above dashboard with contextual daily message
- UX10: DragonStateIndicator in sidebar with hover tooltip detail
- UX11: ActivitySquares (GitHub-style contribution graph) for engagement tracking
- UX12: SparklineWidget for inline category trend visualization
- UX13: SyncHealthCollapsible with auto-expand on warning/error state
- UX14: QueueBadge with time estimate ("~20 sec") for pending categorizations

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | 1 | Manual YNAB import trigger |
| FR2 | 1 | Import accounts, transactions, categories into SQLite |
| FR3 | 1 | SQLite as source of truth for reads |
| FR4 | 1 | Sync health status per account |
| FR5 | 1 | Transfer transaction detection |
| FR6 | 1 | Staleness tracking and warning |
| FR7 | 2 | Rules engine auto-categorization |
| FR8 | 2 | LLM auto-categorization with confidence |
| FR9 | 2 | High-confidence auto-apply |
| FR10 | 2 | Low-confidence queue for validation |
| FR11 | 2 | Approve/reject pending categorizations |
| FR12 | 2 | Write-back to YNAB with rate limiting |
| FR13 | 2 | Categorization progress percentage |
| FR14 | 2 | Auto-create rules from corrections |
| FR15 | 2 | Flag payees for always-manual review |
| FR16 | 1 | Safe-to-spend calculation |
| FR17 | 1 | Health-based color coding |
| FR18 | 1 | Upcoming bill detection |
| FR19 | 1 | Account balance display |
| FR20 | 5 | Chat interface |
| FR21 | 5 | Agent financial data tool access |
| FR22 | 5 | Conversational categorization approval |
| FR23 | 5 | Daily debrief generation |
| FR24 | 5 | Natural language financial queries |
| FR25 | 5 | Contextual safe-to-spend observation |
| FR26 | 5 | Avatar for persona anchoring |
| FR27 | 3 | Full dashboard (STS + dragon + streak + cat% + sync) |
| FR28 | 3 | Dashboard to detail navigation |
| FR29 | 3 | Engagement streak tracking |
| FR30 | 3 | Dragon state indicator |
| FR31 | 3 | Non-judgmental streak break recovery |
| FR32 | 4 | Create categorization rules |
| FR33 | 4 | Edit and delete rules |
| FR34 | 4 | Preview matching transactions |
| FR35 | 4 | Bulk reclassify past transactions |
| FR36 | 2 | Categorization priority order |
| FR37 | 3 | All-time transaction list (paginated, sortable, filterable) |
| FR38 | 3 | Composable filters (payee, category, date range, amount range) |
| FR39 | 3 | Payee summary header (count, total, date span, category breakdown, recurring indicator) |
| FR40 | 3 | Inline and bulk re-categorization from search results |
| FR41 | 3 | Clickable payee names throughout Dragon Keeper |
| FR42 | 5 | Keeper agent payee names as clickable verification links |

## Epic List

### Epic 1: "I Can See Where I Stand"
Import YNAB data and see your financial position — safe-to-spend, account balances, and sync health — on a real dashboard. Includes project scaffolding (schema, migrations, routing, Shadcn/ui setup), YNAB sync engine, rate limiter, safe-to-spend calculation, and dashboard shell with hero + summary cards + sync health.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR16, FR17, FR18, FR19

### Epic 2: "I Can Trust the Numbers"
Auto-categorize transactions, review and approve them, and watch categorizations write back to YNAB. Includes three-tier categorization pipeline, approval queue UI (approve/correct/skip), write-back queue, inline category combobox, auto-rule creation from corrections, and queue badge with time estimate.
**FRs covered:** FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR36

### Epic 3: "My Daily Financial Habit"
Complete the dashboard with engagement tracking, spending trends, dragon state, and non-judgmental recovery — everything needed for the 30-second daily check-in. Includes TrendRow + SparklineWidget, ActivitySquares, DragonStateIndicator, KeeperGreetingStrip (static initially), streak tracking, category drill-down, Transaction Explorer with payee deep dive, and engagement logging.
**FRs covered:** FR27, FR28, FR29, FR30, FR31, FR37, FR38, FR39, FR40, FR41

### Epic 4: "Teaching the Machine My Life"
Create and manage categorization rules, preview matches, and bulk-reclassify past transactions. Includes rules management page, rule CRUD UI, match preview, bulk reclassification, and pipeline priority integration.
**FRs covered:** FR32, FR33, FR34, FR35

### Epic 5: "Talking to the Keeper"
Chat with the Dragon Keeper agent — ask about spending, get daily debriefs, approve categorizations conversationally. Includes Strands agent setup, API tool wrappers, Keeper drawer, chat UI with history, streaming responses, contextual greeting generation, conversational categorization approval, and clickable payee verification links in agent responses.
**FRs covered:** FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR42

## Epic 1: "I Can See Where I Stand"

Import YNAB data and see your financial position — safe-to-spend, account balances, and sync health — on a real dashboard.

### Story 1.1: Dragon Keeper App Shell

As a user,
I want Dragon Keeper to appear in the Codiak sidebar and open to its own dashboard page,
So that I have a dedicated space for my financial management tool.

**Acceptance Criteria:**

**Given** Codiak is running
**When** I click "Dragon Keeper" in the sidebar
**Then** I navigate to `/tool/dragon-keeper` and see an empty dashboard page with the Dragon Keeper layout
**And** the page uses Shadcn/ui components with Tailwind CSS matching Codiak's dark theme
**And** nested routes are configured (`/tool/dragon-keeper/*`) with a DragonKeeperLayout wrapping an Outlet
**And** the Dragon Keeper SQLite database is created at `data/dragon_keeper.db` on first startup with fastmigrate

### Story 1.2: YNAB Data Import

As Cody,
I want to import my YNAB data into Dragon Keeper with one click,
So that my accounts, transactions, and categories are available locally.

**Acceptance Criteria:**

**Given** I am on the Dragon Keeper dashboard
**When** I click the "Import" button
**Then** the system fetches accounts, transactions, categories, and payees from the YNAB API
**And** all data is stored in the local SQLite cache with amounts converted from milliunits to dollars
**And** transfer transactions are flagged via `transfer_account_id` (FR5)
**And** a progress indicator shows import status without blocking UI interaction (NFR4)
**And** YNAB API calls respect the 200 req/hr rate limit via the token bucket (NFR10)
**And** sync state is recorded per account with `server_knowledge` for future delta syncs
**And** if YNAB API fails, a structured error message is shown and no partial data is left (NFR11)

**Given** data has been previously imported
**When** I click "Import" again
**Then** the system performs a delta sync using `server_knowledge`, fetching only changes
**And** existing records are updated, new records inserted, deleted records marked

### Story 1.3: Safe-to-Spend Number

As Cody,
I want to see my safe-to-spend number prominently on the dashboard,
So that I know at a glance whether I can afford discretionary spending today.

**Acceptance Criteria:**

**Given** YNAB data has been imported
**When** I view the Dragon Keeper dashboard
**Then** I see a SafeToSpendHero component showing the dollar amount in large bold text
**And** the amount is calculated as: checking balance minus pending bills minus budget commitments
**And** the number is color-coded: green (healthy), yellow (caution), red (critical) based on configurable thresholds (FR17)
**And** a health status label appears below ("Healthy" / "Caution" / "Critical")
**And** the component renders within 1 second from cached SQLite data (NFR1)
**And** a skeleton placeholder shows while data is loading

### Story 1.4: Account Balances & Upcoming Bills

As Cody,
I want to see my account balances and pending bills on the dashboard,
So that I understand the components behind my safe-to-spend number.

**Acceptance Criteria:**

**Given** YNAB data has been imported
**When** I view the Dragon Keeper dashboard
**Then** I see FinancialSummaryCard components for checking balance, credit card debt, and pending bills
**And** checking balance shows in default text color with account name
**And** credit card debt shows in danger red
**And** pending bills shows the total with timeframe subtitle (FR18)
**And** each card shows a skeleton while loading and renders independently (NFR2)

### Story 1.5: Sync Health Monitor

As Cody,
I want to see the health of my YNAB data sync per account,
So that I know whether my financial data is current and trustworthy.

**Acceptance Criteria:**

**Given** YNAB data has been imported
**When** I view the Dragon Keeper dashboard
**Then** I see a SyncHealthCollapsible showing colored status dots (green/yellow/red) per account (FR4)
**And** collapsed view shows a row of dots with "Sync Health" label
**And** expanded view shows per-account name, status dot, and last sync timestamp
**And** the component auto-expands when any account enters warning (>24h stale) or error (>7 days) state (FR6)
**And** clicking toggles expand/collapse and the state is remembered

## Epic 2: "I Can Trust the Numbers"

Auto-categorize transactions, review and approve them, and watch categorizations write back to YNAB.

### Story 2.1: Rules Engine Categorization

As Cody,
I want my known transactions to be automatically categorized by matching rules,
So that most of my spending is categorized without any effort from me.

**Acceptance Criteria:**

**Given** YNAB data has been imported with uncategorized transactions
**When** the categorization pipeline runs after import
**Then** the rules engine matches transactions against `categorization_rules` by payee pattern (exact, contains, starts_with)
**And** matched transactions have their `category_id` updated in local SQLite
**And** rules with `min_amount`/`max_amount` thresholds only match within range
**And** the pipeline processes rules as the first tier before LLM or manual queue (FR36)
**And** the `times_applied` counter increments for each matched rule

### Story 2.2: LLM Categorization

As Cody,
I want transactions that don't match any rule to be categorized by AI with confidence scoring,
So that even unfamiliar payees get reasonable category suggestions.

**Acceptance Criteria:**

**Given** transactions remain uncategorized after the rules engine pass
**When** the LLM categorization tier runs
**Then** the system sends payee name, amount, and memo to the LLM API (NFR9)
**And** the LLM returns a suggested category with a confidence score (0.0-1.0)
**And** transactions above the confidence threshold are auto-applied without user intervention (FR9)
**And** transactions below the threshold are queued for user validation (FR10)
**And** if the LLM API fails, all remaining transactions queue for manual review gracefully (NFR13)

### Story 2.3: Categorization Approval Queue

As Cody,
I want to review pending categorizations and approve, correct, or skip them in seconds,
So that my categorization percentage climbs and my safe-to-spend becomes trustworthy.

**Acceptance Criteria:**

**Given** transactions are queued for user validation
**When** I view the categorization queue
**Then** I see a list of transactions with date, merchant, amount, and suggested category with confidence indicator
**And** each row has Approve (primary), Correct (secondary), and Skip (tertiary) buttons (FR11)
**And** clicking Approve confirms the suggestion and removes the item from the queue
**And** clicking Correct opens an inline searchable category combobox showing recent categories first
**And** selecting a category auto-confirms the correction
**And** clicking Skip dims the row and defers it to the next session
**And** a "Approve All" button appears when 3+ items have high confidence
**And** each action completes within 500ms (NFR3)
**And** a QueueBadge on the dashboard shows pending count with time estimate ("~20 sec")

**Given** all items are approved or skipped
**When** the queue is empty
**Then** I see "All caught up — nothing to review"
**And** the categorization progress percentage updates on the dashboard (FR13)

### Story 2.4: YNAB Write-Back

As Cody,
I want my approved categorizations to be written back to YNAB automatically,
So that my YNAB budget reflects the same categories as Dragon Keeper.

**Acceptance Criteria:**

**Given** categorizations have been approved or corrected
**When** the write-back processor runs
**Then** approved items are queued in `write_back_queue` with status `pending`
**And** a background task processes the queue, calling YNAB API to update each transaction's category
**And** write-back API calls respect the rate limit separately from sync reads (NFR12)
**And** successful items are marked `completed` with timestamp
**And** failed items are marked `failed` with error message and retry with exponential backoff
**And** write-back status is reflected in sync health

### Story 2.5: Learning from Corrections

As Cody,
I want the system to learn from my corrections and create rules automatically,
So that the same payee gets categorized correctly next time without my help.

**Acceptance Criteria:**

**Given** I have corrected a categorization for a payee
**When** I have corrected the same payee-to-category mapping 2+ times
**Then** the system auto-creates a categorization rule with source `learned` (FR14)
**And** a toast notification confirms: "Rule created: [payee] → [category]" with Undo option
**And** the new rule applies to future imports automatically

**Given** I want a payee to always require my manual review
**When** I flag a payee for manual review (FR15)
**Then** that payee bypasses rules engine and LLM categorization
**And** transactions from that payee always appear in the validation queue

## Epic 3: "My Daily Financial Habit"

Complete the dashboard with engagement tracking, spending trends, dragon state, and non-judgmental recovery.

### Story 3.1: Spending Trends & Sparklines

As Cody,
I want to see how my spending categories trend over time at a glance,
So that I can spot patterns without digging into transaction lists.

**Acceptance Criteria:**

**Given** I have imported transaction data spanning multiple periods
**When** I view the Dragon Keeper dashboard
**Then** I see TrendRow components for my top spending categories
**And** each row shows category name, sparkline chart (7-8 bars), delta percentage with arrow, and period total
**And** hovering a sparkline bar shows a tooltip with period and amount
**And** rows are sorted by total spending descending
**And** clicking a trend row navigates to the category detail view (FR28)

### Story 3.2: Engagement Streak & Activity Tracking

As Cody,
I want to see my daily engagement streak and activity history,
So that I'm motivated to maintain my financial check-in habit.

**Acceptance Criteria:**

**Given** I visit Dragon Keeper on a given day
**When** the dashboard loads
**Then** the system logs my visit in `engagement_log` with timestamp (FR29)
**And** actions (approvals, corrections, chat messages) increment the `actions_count`
**And** I see an ActivitySquares component showing a GitHub-style grid of daily visits
**And** visited days show light accent fill; days with actions show full accent fill
**And** my current streak count is displayed alongside the grid
**And** the streak counts consecutive days with visits

### Story 3.3: Dragon State & Keeper Greeting

As Cody,
I want to see an ambient health indicator and a contextual greeting when I open the dashboard,
So that I immediately know whether everything is fine or something needs attention.

**Acceptance Criteria:**

**Given** I navigate to Dragon Keeper
**When** the dashboard loads
**Then** I see a DragonStateIndicator in the sidebar next to "Dragon Keeper" (FR30)
**And** the indicator is green (sleeping/healthy), amber (stirring/attention needed), or red (raging/critical)
**And** hovering shows a tooltip with state name, component breakdown, and trend direction
**And** a KeeperGreetingStrip appears above the dashboard with a contextual message
**And** the greeting references safe-to-spend, notable trends, pending queue count, and upcoming bills
**And** the greeting strip can be collapsed for the session

**Given** the dashboard shows all widgets (STS, summary cards, trends, sync health, activity, queue badge, dragon state, greeting)
**When** I view the complete dashboard (FR27)
**Then** all widgets load progressively with skeletons, safe-to-spend first (NFR2)

### Story 3.4: Category Drill-Down

As Cody,
I want to click into a spending category and see its full transaction history and chart,
So that I can investigate unexpected spending patterns.

**Acceptance Criteria:**

**Given** I am viewing spending trends on the dashboard
**When** I click a trend row for a specific category
**Then** I navigate to `/tool/dragon-keeper/category/:id` (FR28)
**And** I see a chart showing spending over time for that category
**And** I see a sortable transaction table with date, payee, amount, and memo
**And** a "← Dashboard" breadcrumb link returns me to the dashboard
**And** my dashboard scroll position and widget states are preserved on return

### Story 3.5: Recovery & Re-engagement

As Cody,
I want to return after missing days without feeling punished or overwhelmed,
So that a break doesn't turn into permanent abandonment.

**Acceptance Criteria:**

**Given** I have not visited Dragon Keeper for 2+ days
**When** I return to the dashboard
**Then** the KeeperGreetingStrip acknowledges the gap without judgment (FR31)
**And** the greeting includes queue count and time estimate ("11 to review, should take about a minute")
**And** the streak resets to 0 but activity squares still show my past history
**And** the categorization queue shows accumulated items with batch approve option
**And** if all items are auto-categorized with high confidence, greeting says "All caught up while you were away"

### Story 3.6: Transaction Explorer & Payee Deep Dive

As Cody,
I want to browse all my transactions with filtering and see payee-level summaries,
So that I can audit categorization consistency, verify Keeper answers against raw data, and identify recurring vs. one-off spending patterns.

**Acceptance Criteria:**

**Given** I navigate to `/tool/dragon-keeper/transactions`
**When** the Transaction Explorer loads
**Then** I see a paginated, sortable table of all transactions (all time by default) showing date, payee, category, amount, and memo
**And** the table supports sorting by any column
**And** a "← Dashboard" breadcrumb link returns me to the dashboard

**Given** I am on the Transaction Explorer
**When** I type in the payee search field
**Then** the transaction list filters in real-time to transactions whose payee name matches my search (case-insensitive, substring match)
**And** I can additionally filter by category (combobox), date range (start/end pickers), and amount range (min/max)
**And** filters are composable (payee + category + date range simultaneously)

**Given** the list is filtered to a single payee (or payee substring match)
**When** results are displayed
**Then** a PayeeSummaryHeader appears showing: payee name, total transaction count, total dollar amount, and date range of first-to-last transaction
**And** if transactions span multiple categories, a category breakdown is shown (e.g., "42 The Farm, 3 Shopping, 2 Uncategorized") with inconsistent categories visually flagged
**And** if transactions appear at regular intervals (monthly +/- 3 days), a "Likely recurring" indicator is displayed

**Given** I see a transaction with the wrong category
**When** I click the category cell on that row
**Then** an inline searchable category combobox opens (same pattern as Story 2.3) showing recent categories first
**And** selecting a new category updates the transaction locally and queues a YNAB write-back
**And** the PayeeSummaryHeader totals and category breakdown update immediately

**Given** I want to fix multiple transactions at once
**When** I select multiple rows via checkboxes and click "Re-categorize Selected"
**Then** a category combobox appears and my selection applies to all checked transactions
**And** a toast confirms: "[N] transactions re-categorized to [category]" with Undo (6-second window)
**And** all changes queue for YNAB write-back

**Given** a payee name appears anywhere in Dragon Keeper (dashboard trend rows, category drill-down, categorization queue, rules page, Keeper chat messages)
**When** I click the payee name
**Then** I navigate to `/tool/dragon-keeper/transactions?payee=[name]` with the Transaction Explorer pre-filtered
**And** the PayeeSummaryHeader is visible immediately

**Given** the Keeper agent references payee spending in a response (e.g., "You spent $340 at Amazon this month")
**When** the response renders in the chat
**Then** the payee name is rendered as a clickable link that opens the Transaction Explorer pre-filtered to that payee
**And** clicking preserves the Keeper drawer open state

## Epic 4: "Teaching the Machine My Life"

Create and manage categorization rules, preview matches, and bulk-reclassify past transactions.

### Story 4.1: Rules Management Page

As Cody,
I want a dedicated page to create categorization rules,
So that I can teach the system which categories my regular payees belong to.

**Acceptance Criteria:**

**Given** I navigate to `/tool/dragon-keeper/rules`
**When** the rules page loads
**Then** I see a list of all existing categorization rules showing payee pattern, match type, category, confidence, source, and times applied
**And** a "Create Rule" button opens an inline form
**And** the form has fields for: payee pattern (text), match type (exact/contains/starts_with), category (combobox), optional min/max amount
**And** submitting creates the rule and shows a toast confirmation (FR32)
**And** rules are sorted by times_applied descending (most used first)

### Story 4.2: Edit & Delete Rules

As Cody,
I want to edit or delete rules that aren't working correctly,
So that I can refine my categorization over time.

**Acceptance Criteria:**

**Given** I am on the rules management page
**When** I click edit on a rule
**Then** the rule row transforms into an inline edit form with current values populated (FR33)
**And** I can modify any field and save
**And** saving shows a toast confirmation

**Given** I want to delete a rule
**When** I click delete
**Then** the rule is removed and a toast with "Undo" appears (6-second window)
**And** clicking Undo restores the rule

### Story 4.3: Rule Preview & Bulk Reclassify

As Cody,
I want to preview which transactions match a rule before applying it and reclassify past transactions in bulk,
So that I can confidently create rules knowing exactly what they affect.

**Acceptance Criteria:**

**Given** I am creating or editing a rule
**When** I enter a payee pattern and match type
**Then** I see a live preview of matching transactions with count and sample rows (FR34)
**And** the preview updates as I change the pattern

**Given** I save a new or modified rule
**When** matching transactions exist that have a different category
**Then** I am prompted: "Reclassify [N] past transactions to [category]?" with Yes/No
**And** clicking Yes bulk-updates all matching transactions and queues write-backs to YNAB (FR35)
**And** a toast confirms: "[N] transactions reclassified" with Undo option

## Epic 5: "Talking to the Keeper"

Chat with the Dragon Keeper agent — ask about spending, get daily debriefs, approve categorizations conversationally.

### Story 5.1: Keeper Agent & Chat Shell

As Cody,
I want to open a chat drawer and send messages to the Dragon Keeper,
So that I can interact with my financial data conversationally.

**Acceptance Criteria:**

**Given** I am on any Dragon Keeper page
**When** I click the Keeper icon in the sidebar or press Ctrl+K
**Then** a Sheet drawer opens on the right side (360px width) with a chat interface (FR20)
**And** the chat shows a message list with Keeper messages (indigo left border, avatar) and user messages (right-aligned)
**And** I can type a message and press Enter to send
**And** the Keeper responds with a typing indicator followed by a streamed response
**And** the drawer persists across route changes within Dragon Keeper
**And** the Keeper displays with a static avatar for persona anchoring (FR26)
**And** chat history is persisted in SQLite and survives app restart
**And** on first visit, the Keeper sends an opening message establishing the relationship

### Story 5.2: Financial Data Queries

As Cody,
I want to ask the Keeper questions about my spending and get answers grounded in real data,
So that I can make informed financial decisions through conversation.

**Acceptance Criteria:**

**Given** the Keeper chat is open
**When** I ask "What did I spend on Amazon this month?"
**Then** the Keeper queries financial data via API tool wrappers and returns a specific dollar amount with transaction count (FR21, FR24)

**Given** I ask "Can we afford takeout tonight?"
**When** the Keeper processes the question
**Then** it references the safe-to-spend amount, relevant upcoming bills, and days until payday to provide contextual advice (FR25)

**Given** I ask about trends or balances
**When** the Keeper responds
**Then** responses include specific numbers from the local data cache, not hallucinated figures
**And** responses return within 5 seconds for typical queries (NFR5)

### Story 5.3: Contextual Greeting & Daily Debrief

As Cody,
I want the Keeper to greet me with relevant context and generate a daily debrief on request,
So that I'm informed the moment I open the app and can get a structured summary when I want one.

**Acceptance Criteria:**

**Given** I open Dragon Keeper
**When** the dashboard loads
**Then** the KeeperGreetingStrip shows a dynamically generated greeting based on: safe-to-spend, notable trends, pending queue count, upcoming bills, and days since last visit (FR23)
**And** the greeting varies in content and tone (not repetitive)

**Given** I ask the Keeper for a daily debrief
**When** the Keeper generates the response
**Then** it includes: safe-to-spend with context, spending since last visit, streak status, one insight or observation, and any items needing attention (FR25)

### Story 5.4: Conversational Categorization Approval

As Cody,
I want the Keeper to present pending categorizations in conversation for quick approval,
So that I can handle my queue without leaving the chat.

**Acceptance Criteria:**

**Given** there are pending categorizations and I'm chatting with the Keeper
**When** the Keeper presents pending items
**Then** it shows them in natural language: "I filed 3 new transactions — $47 Amazon as Household Supplies, $12 Spotify as Subscriptions, $85 Rural King as The Farm. Sound right?" (FR22)
**And** I can approve all with "yep" or similar affirmative
**And** I can correct specific items: "Rural King should be Farm Equipment"
**And** approvals and corrections are processed through the same categorization service as the queue UI
**And** a confirmation message summarizes what was done
