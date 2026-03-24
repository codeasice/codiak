---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Custom YNAB-powered financial management tool with agentic chat coach for Codiak'
session_goals: 'Feature ideation, behavioral nudging, reducing YNAB friction via custom UI, agentic financial coach, API architecture (caching/sync/write-back), data structure, UX design'
selected_approach: 'progressive-flow'
techniques_used: ['First Principles Thinking', 'Six Thinking Hats', 'Dream Fusion Laboratory', 'Solution Matrix']
ideas_generated: []
context_file: '_bmad/bmm/data/project-context-template.md'
---

# Brainstorming Session Results

**Facilitator:** Master Cody
**Date:** 2026-03-01

## Session Overview

**Topic:** Custom YNAB-powered financial management tool with agentic chat coach for Codiak

**Goals:**
1. Feature ideas for a unified YNAB tool (consolidating 14 existing Streamlit tools)
2. Behavioral nudging strategies to reduce credit card spending
3. Exploring why YNAB itself creates friction and how a custom tool can eliminate it
4. Agentic financial coach — conversational AI for daily money management
5. YNAB API architecture — caching, sync, rate limiting, write-back
6. Data structure — persistent local cache, smart refresh strategy
7. UI/UX — React frontend that's engaging and reduces friction

### Context Guidance

_Existing codebase has 14 YNAB Streamlit tools covering: transaction browsing, categorization (manual + AI-assisted + rules-based), spending graphs, alluvial diagrams, payee management, data export, and transaction creation. Code has significant duplication, inconsistent caching, minimal rate limiting, and manual export-to-DB workflow. An MCP server exists for read-only SQLite access. Migration target is React + FastAPI stack._

### Session Setup

_Master Cody wants to move beyond YNAB's native UX friction and build a personalized financial tool that comes to him rather than demanding he go to it. Key innovation: an agentic chat interface layered on top of structured financial tools._

## Technique Selection

**Approach:** Progressive Technique Flow
**Journey Design:** Systematic development from exploration to action

**Progressive Techniques:**

- **Phase 1 - Exploration:** First Principles Thinking — strip assumptions, rebuild from fundamental truths
- **Phase 2 - Pattern Recognition:** Six Thinking Hats — multi-perspective analysis of generated ideas
- **Phase 3 - Development:** Dream Fusion Laboratory — dream impossible, reverse-engineer to reality
- **Phase 4 - Action Planning:** Solution Matrix — systematic grid of features vs. implementation approaches

**Journey Rationale:** User has friction with YNAB but can't pinpoint why. First Principles uncovers root causes. Six Hats analyzes emotional/practical dimensions (critical for behavioral nudging). Dream Fusion develops the agentic coach concept from vision to feasibility. Solution Matrix produces actionable implementation plan.

## Phase 1: First Principles Thinking — Exploration Results

### Fundamental Truths Uncovered

1. Credit cards are a safety net, not a choice — used to avoid checking overdrafts
2. Charges accumulate because payoff never happens — death by a thousand cuts
3. Low financial awareness — "spend and hope for the best"
4. YNAB's friction creates a death spiral — categorization backlog → untrustworthy data → tool abandonment
5. NOT an income problem — it's a behavior and visibility problem
6. Doesn't understand spending implications — compounding effects, retirement impact invisible
7. Wants guardrails, not just dashboards
8. Family doesn't understand the financial picture — wife and kids need evidence
9. Need to communicate the financial story, not just numbers
10. Wants to understand the history — how did we get into debt? Was it worth it?
11. Interest paid is invisible waste — wants to see actual dollars lost
12. Bank transaction sync is unreliable — another friction layer
13. Second income coming in 1.5–2 years (wife in nursing school) — need a two-income plan
14. Dragon theme resonates — kept as core identity
15. Would stop using credit card with a checking cushion — that's the exit condition
16. YNAB's AI categorization is bad — manual work compounds over time
17. Push model > pull model — daily agent pings beat opening YNAB
18. Categories themselves might be wrong — need to match user's mental model
19. Eating out is driven by convenience + picky family (2–3 meals to cook) — not laziness
20. Amazon purchases are a black hole — inconsistent, hard to track, hard to categorize
21. Farm animals are a real spending category unique to this household
22. Many anticipated future costs (roof, pool, flooring, painting, bathrooms)
23. Obsidian vault has project notes, priorities, kid activities — potential integration point
24. Subscriptions (AI tools, internet) are a recurring bleed — needs audit/prioritization
25. Manual import/export initially is fine — auto-sync is a confidence-building progression

### The Core Feedback Loop (Root Cause)
Budget is off → unsure what's safe to spend → use credit card → CC balance grows → minimum payments eat checking → budget is MORE off → repeat

### Ideas Generated (67)

**Behavioral Nudging:**
1. The Dragon Slayer Dashboard — debt as a literal dragon, shrinks as you pay
2. The Spending Ghost — show compounding/retirement cost of each purchase
3. The Cushion Quest — gamified checking buffer goal
13. The Streak Flame — chain mechanics for daily financial behaviors
19. The Categorization Progress Bar — gamify categorization completion %
29. The Subscription Audit Agent — active challenger with real dollar impact
31. The Countdown Collection — visual countdowns for expenses that end (school, flight lessons)
33. The Dining Out Reality Check — realistic targets, not shaming
34. The Meal Cost Tracker — eat-out ratio tracking
38. The Impulse Buffer — 48-hour cooling off nudge for purchases over threshold

**Agent / Dragon Keeper:**
4. The Daily Dragon Keeper — agent pings for daily categorization (push model)
5. Smart Auto-Categories — rules + LLM auto-categorize 80%+ automatically
15. Conversational Validation — agent auto-categorizes, you validate in 10 seconds
20. The Strategic Advisor — agent answers big questions ("can we afford flight lessons?")
35. The Obsidian-Aware Financial Agent — reads Obsidian notes for financial context
36. The Proactive Advisor — agent notices patterns and brings them up
40. The Agent Memory Layer — remembers past commitments, follows up
43. The "Can We Afford It?" Quick Check — family members can ask
44. The Dragon Keeper Persona — weathered, wise guardian character
47. The Keeper's Journal — daily summary as narrative journal entry
48. The Keeper's Warnings — alerts in character voice
50. The Keeper's Wisdom — strategic advice in character with real data

**Family & Communication:**
6. The Family Financial Story — narrative read-only view
16. Privacy Shields — mark transactions/categories as private in family view
37. The Family Money Education Module — age-appropriate views for kids
42. The Dragon Slayer Family Quest — cooperative family quests
49. The Family Quest Board — RPG-style quest board

**Visualization:**
11. The Dollar River — Sankey/alluvial showing every dollar's flow
21. The Debt Archaeology Timeline — historical reconstruction of how debt accumulated
32. The Spending Weather Report — financial status as weather metaphor
39. The Interest Vampire — dedicated interest-paid visualization
45. The Keeper's Avatar — visual character with states
46. Dragon State Visualization — dragon moods based on financial health
67. Account Balance Trends — line charts showing all account balances over time

**Tools:**
7. The Debt Archaeology Report — categorize historical debt (intentional vs. bleed vs. waste)
12. The Retirement Oracle — current trajectory to retirement, with levers
14. The Subscription Slayer — detect, prioritize, challenge recurring charges
22. Smart Category Suggestions — analyze spending patterns, suggest natural categories
24. The Utility Tracker — utility trend lines and optimization suggestions
25. The Crystal Ball — anticipated future costs tracker
27. The Amazon Decoder — split and categorize Amazon orders
30. The Cody Household Spending Map — custom categories matching your life
41. The "What Did Amazon Charge Me For?" Decoder — cross-reference charges with orders

**Architecture:**
8. The YNAB Shadow Database — persistent SQLite cache, all reads local
9. The Two-Income Battle Plan — projection tool for debt payoff with two incomes
17. Sync Health Monitor — visual indicator for account sync status
18. The Scenario Simulator — interactive what-if engine with sliders
23. The Daily Debrief — morning/evening summary with green/red indicators
26. The Obsidian Bridge — connect Obsidian notes to financial tracking
28. Direct Bank Connection (Plaid) — optional direct transaction pull
54. Shared YNAB Service Layer — unified API client, DB, caching
55. The Wing Structure — self-contained module within Codiak
56. Schema Migration System — proper versioned DB migrations
57. Unified Cache Architecture — single read path, batched write path
58. The Write-Back Queue — rate-limited async pushes to YNAB
59. Agent as MCP Consumer — compose agent from existing MCP tools
60. Auto-Categorization Pipeline — three-tier: rules → LLM → user
61. Real-Time Balance Check — "safe to spend" number
62. Rules Learning Engine — auto-create rules from user corrections
63. Unified Amount Handling — single money type for milliunits/cents
64. Transaction Deduplication — detect double-posts during sync
65. API Health Dashboard — sync status, queue depth, categorization stats
66. Scheduled Sync via Background Worker — auto-sync on interval

**UX:**
51. Mobile-First Notifications — Telegram/SMS/PWA push
52. The Three-Second Glance — one number, one color, one sentence
53. The Swipe-to-Categorize Interface — Tinder-style transaction categorization

## Phase 2: Six Thinking Hats — Pattern Recognition Results

### Red Hat (Emotions)
- **Excited by:** Personalization, safe-to-spend, subscription pruning, auto-categorization, Obsidian integration, MCP/agentic
- **Nervous about:** Security, complexity → friction → abandonment, inaccurate data, YNAB limitations, confusing transfers, opaque Amazon/PayPal
- **Core need:** Honest mirror — truth about spending, trajectory, and prioritized opportunities

### White Hat (Facts)
- 3+ credit cards, multiple credit accounts, significant balances
- ~7,500 lines existing YNAB Streamlit code (heavy duplication)
- MCP server + Obsidian MCP already exist
- Auto-categorization partially built (rules + LLM)
- YNAB API rate limited (~200 req/hr), sync unreliable
- Wife's income ~18 months out. George's school ~12 months. Harris is 17.
- Amazon/PayPal transactions obscure actual purchases
- Account transfers create confusing ghost transactions
- Data gaps: exact account count, historical interest paid, categorization coverage

### Yellow Hat (Benefits)
- **Tier 1 (Life-changing):** Break credit card spiral, catch cancellable subscriptions, family alignment
- **Tier 2 (Quality of life):** Daily awareness without effort, trust in data, knowing trajectory
- **Tier 3 (Strategic):** Two-income battle plan, kids learning money, Obsidian bridge
- **Tier 4 (Long-term):** Retirement planning, financial freedom from job dependency, life-long scenario modeling

### Black Hat (Risks)
1. Complexity creep → tool abandonment (the YNAB trap)
2. Inaccurate data = worse than no data
3. Security exposure (API keys, transaction data)
4. Amazon/PayPal black hole (genuinely hard problem)
5. Transfer confusion (ghost transactions)
6. Building too much, using too little

### Green Hat (Creative Breakthroughs)
1. Agent-first, dashboard-second (tool comes to you)
2. Obsidian as financial context (no other tool does this)
3. Trust architecture (surface data quality rather than hiding it)
4. Family narrative (story, not spreadsheet — answers "why don't we have money?")
5. Honesty-first approach to opaque transactions

### Blue Hat (Process)
- **Design filter:** Does it increase trust? Add clarity? Reduce effort?
- **Three tiers:** Foundation → Engagement → Growth
- **Build trust first, then engagement, then growth**

### Key Corrections & Additions from Phase 2
- Tool is React + FastAPI ONLY — no Streamlit going forward
- Son is Harris (not Jake)
- Long-term goal: retirement satisfaction, financial freedom, less job dependency
- Lifetime scenario modeling — project finances through end of life, keep updated
- Family narrative must answer: "You make a lot of money, why don't we have any?" — trace every dollar from paycheck to destination
- Amazon/PayPal direct API integration is worth exploring
- Debt archaeology must show WHERE each CC balance came from

## Phase 3: Dream Fusion Laboratory — Idea Development Results

### The Dream Vision
An omniscient Dragon Keeper agent that knows every transaction, every account, every subscription. Talks through voice, Slack, chat. Auto-manages finances. Generates visualizations on demand. Projects your entire financial life through retirement and beyond.

### Dream → Reality Bridge (5-Phase Roadmap)

**Phase A — Foundation (weeks 1–4): "I can trust this"**
- Manual YNAB import → clean SQLite cache
- Auto-categorization: rules + LLM, auto-apply high-confidence, queue low for daily validation
- Safe-to-spend number (checking balance minus pending bills minus uncommitted budget)
- Dragon Keeper text agent via MCP tools in React chat
- Trust indicators: sync health, categorization %, last-updated

**Phase B — Engagement (weeks 5–8): "I actually use this daily"**
- Daily debrief pushed via Slack bot
- Subscription detection with upcoming renewal warnings
- Streaks & gamification, dragon state changes
- Paycheck tracer ("where does Dad's money go")
- Conversational categorization via Slack or React chat

**Phase C — Family & Visualization (weeks 9–12): "Others can see this too"**
- Family narrative view with privacy shields
- Dragon Slayer dashboard with visual dragon
- Balance trends, Dollar River (Sankey), Spending Weather Report
- Family quest board

**Phase D — Intelligence (months 3–6): "It makes me smarter"**
- Lifetime projections through retirement/end of life (living, updated model)
- Scenario simulator with interactive sliders
- Debt archaeology, Interest vampire, Freedom Index
- Vacation projector based on historical costs

**Phase E — Expansion (months 6+): "It grows with me"**
- Voice interface (Whisper/browser speech APIs)
- Amazon/PayPal transaction decoding
- Obsidian bridge for project/priority context
- Multi-channel (Slack, Discord, SMS, PWA push)
- Two-income battle plan

**Explicitly deferred:** Auto-cancelling subscriptions, email integration, holistic life management, direct bank connections (Plaid)

### Additional Ideas from Phase 3 (68–74)
68. Lifetime Projection Engine — living financial model through end of life
69. Paycheck Tracer — trace every dollar from gross pay to destination
70. Financial Freedom Index — "months you could survive without working"
71. Amazon Order History API Integration — decode opaque charges
72. Vacation Projector — plan fun based on historical costs
73. Multi-Channel Keeper — Slack, voice, mobile
74. On-Demand Visualization — agent generates charts in conversation

## Phase 4: Solution Matrix — Action Planning Results

### Phase A Solution Matrix: "I Can Trust This" (Weeks 1–4)

#### A1. Data Layer (Week 1)
- **Purpose:** Clean SQLite cache of all YNAB data, single source of truth
- **Endpoints:** `POST /api/dragon-keeper/sync`, `GET /api/dragon-keeper/sync-status`
- **Reuse:** `ynab_export_data.py` (fetch/import), `ynab_mcp/queries.py` (reads)
- **New:** Schema migrations, unified DB module, transfer detection/flagging, sync status table
- **UI:** Import button, sync health indicators (green/yellow/red per account)

#### A2. Auto-Categorization Pipeline (Week 2)
- **Purpose:** Rules → LLM → user queue. Auto-apply high-confidence, queue low-confidence.
- **Endpoints:** `POST /api/dragon-keeper/categorize`, `GET /api/dragon-keeper/pending-categorizations`, `POST /api/dragon-keeper/approve-categorization`
- **Reuse:** `ynab_categorizer_config.py` (rules), `ynab_categorizer.py` (LLM + rate limiting), `ynab_categorizer_rules.json`
- **New:** Confidence scoring, pipeline orchestration, rules learning, write-back queue
- **UI:** Categorization progress bar, pending approval queue

#### A3. Safe-to-Spend Number (Week 3)
- **Purpose:** Checking balance - pending bills - budget commitments = safe to spend
- **Endpoints:** `GET /api/dragon-keeper/safe-to-spend`
- **Reuse:** `ynab_mcp/queries.py` balances, `ynab_categories` budget data
- **New:** Upcoming bills detection, budget-aware calculation
- **UI:** Big bold number, green/yellow/red, one Keeper sentence

#### A4. Dragon Keeper Chat Agent (Week 4)
- **Purpose:** Conversational agent with Keeper persona, MCP tool access, categorization approval
- **Endpoints:** `POST /api/dragon-keeper/chat`
- **Reuse:** `ynab_mcp/ynab_server.py` tools, `llm_utils.py`
- **New:** Agent orchestration, Keeper persona prompt, chat persistence, write-action tools
- **UI:** Chat window with dragon avatar, message history, text input

#### A5. Three-Second Dashboard (Week 3, alongside A3)
- **Purpose:** Landing page: safe-to-spend, dragon state, streak, categorization %, sync health
- **Endpoints:** `GET /api/dragon-keeper/dashboard-summary`
- **UI:** `DragonDashboard.tsx` — the home view

### File Structure

```
api/services/dragon_keeper/
  db.py                  # Unified DB
  ynab_client.py         # YNAB API wrapper (rate-limited)
  sync_service.py        # Import/export, sync status
  categorization.py      # Rules + LLM pipeline
  safe_to_spend.py       # Core calculation
  agent.py               # Keeper chat orchestration

api/routers/dragon_keeper.py

web/src/tools/dragon-keeper/
  DragonDashboard.tsx
  KeeperChat.tsx
  SyncHealth.tsx
  components/
    SafeToSpend.tsx
    DragonState.tsx
    CategorizationBar.tsx
    StreakCounter.tsx
```

### Full Phased Roadmap Summary

| Phase | Timeline | Theme | Key Deliverables |
|-------|----------|-------|-----------------|
| A | Weeks 1–4 | "I can trust this" | Data layer, auto-categorization, safe-to-spend, Keeper chat, dashboard |
| B | Weeks 5–8 | "I use this daily" | Slack bot, subscription detection, streaks, paycheck tracer, conversational categorization |
| C | Weeks 9–12 | "Others can see this" | Family view, dragon visualization, balance trends, Dollar River, privacy shields |
| D | Months 3–6 | "It makes me smarter" | Lifetime projections, scenario simulator, debt archaeology, Freedom Index, vacation projector |
| E | Months 6+ | "It grows with me" | Voice, Amazon/PayPal decode, Obsidian bridge, multi-channel, two-income plan |

### Design Principles (from Six Thinking Hats)
1. **Trust before features** — accurate data > more features
2. **Push, don't pull** — the tool comes to you
3. **Honesty over false precision** — flag what's uncertain rather than guess wrong
4. **Reduce friction ruthlessly** — every interaction should take seconds, not minutes
5. **The Dragon Keeper is a relationship, not a dashboard**
