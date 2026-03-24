---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - _bmad-output/analysis/brainstorming-session-2026-03-01.md
  - docs/index.md
  - docs/technical/architecture.md
  - docs/technical/developer-guide.md
  - docs/technical/integrations.md
date: 2026-03-01
author: Master Cody
---

# Product Brief: Codiak — Dragon Keeper

## Executive Summary

Dragon Keeper is a custom financial management module within the Codiak platform that replaces the friction-heavy YNAB interface with an agent-first, narrative-driven tool tailored to one household's real financial life. Built on React + FastAPI with YNAB as the data backend, Dragon Keeper addresses a specific behavioral problem: good income undermined by low spending awareness, a credit card safety-net cycle, and tool friction that prevents financial habits from forming.

The centerpiece is The Keeper — an agentic AI character who pushes daily financial awareness to the user through conversational check-ins, auto-categorizes transactions to eliminate the backlog death spiral, and presents one critical number: what's safe to spend from checking right now. For the family, Dragon Keeper reframes finances as a shared narrative — debt is a dragon to slay together, progress is visible, and the answer to "why don't we have money?" is finally clear.

Dragon Keeper is not a budgeting tool — it's a **financial relationship**. The budgeting happens inside it, but the core value is the ongoing, trust-based relationship with The Keeper. This distinction drives every design decision: agent-first over dashboard-first, narrative over spreadsheet, push over pull.

The product operates within an 18-month transformation window: a second household income arriving (~18 months), a major expense ending (private school, ~12 months), and a son approaching independence. Building now means the tool, data, habits, and family alignment are ready to deploy that second income with strategic precision against debt.

Dragon Keeper consolidates 14 existing fragmented YNAB Streamlit tools into a unified experience with a phased roadmap: Foundation (trust the data) → Engagement (use it daily) → Family (share the story) → Intelligence (plan the future) → Expansion (grow with life changes).

---

## Core Vision

### Problem Statement

A household with good income but no real-time visibility into spending has fallen into a credit card debt cycle: uncertain checking balance → credit card used as safety net → debt accumulates → minimum payments reduce next month's checking → cycle deepens. YNAB exists to solve this but creates its own friction death spiral: manual categorization is too time-consuming → user stops categorizing → data becomes untrustworthy → tool gets abandoned → financial blindness returns. The family cannot see or understand the financial picture, creating tension and misaligned spending behavior. Meanwhile, interest compounds invisibly, retirement readiness erodes, and financial dependence on current employment deepens.

### Problem Impact

- **Daily:** Spending decisions made without data; credit card used reflexively to avoid overdrafts
- **Monthly:** No trustworthy view of where money went; categorization backlog grows
- **Annually:** Thousands lost to invisible credit card interest; no progress on debt
- **Long-term:** Retirement trajectory worsening; financial freedom index near zero; family tension around money; job lock due to financial instability
- **Family:** Wife and kids (Harris, 17; George, 13) cannot understand why good income doesn't translate to financial comfort; no evidence-based way to communicate the picture or align on priorities

### Why Existing Solutions Fall Short

| Solution | Strength | Critical Gap |
|----------|----------|-------------|
| **YNAB** | Comprehensive budgeting engine, bank sync, envelope method | UI friction creates abandonment cycle; poor AI categorization; pull model demands user come to it; no agentic layer; categories don't match user's mental model |
| **Mint / similar** | Automatic categorization, read-only dashboards | No behavioral nudging; no customization; no write-back; no family narrative; passive |
| **Spreadsheets** | Maximum flexibility | Maximum effort; no automation; no push; no intelligence |
| **Existing Codiak YNAB tools** | 14 specialized tools covering transactions, categorization, visualization, export | Fragmented (no unified experience); ~7,500 lines with massive duplication; manual export; no auto-categorization pipeline; no agent; Streamlit-only |

### Proposed Solution

Dragon Keeper is a self-contained module ("wing") within Codiak's React + FastAPI architecture that treats YNAB as a backend data engine while providing a radically different user experience built around five principles:

1. **Trust before features** — Accurate, transparent data with visible quality indicators (sync health, categorization %, confidence scores) before adding capabilities
2. **Push, don't pull** — The Keeper agent comes to you daily via Slack or notifications rather than waiting for you to open a dashboard
3. **Honesty over false precision** — Opaque transactions (Amazon, PayPal) and incomplete data are flagged honestly rather than guessed at incorrectly
4. **Reduce friction ruthlessly** — Auto-categorization (rules → LLM → user validation) eliminates the backlog death spiral; every interaction takes seconds, not minutes
5. **Relationship, not dashboard** — The Dragon Keeper persona transforms financial management from sterile data entry into a narrative quest the whole family can participate in

Core capabilities by phase:
- **Phase A (Foundation):** YNAB data cache, auto-categorization pipeline, safe-to-spend number, daily Keeper push via Slack, three-second dashboard with sync health and static dragon avatar
- **Phase B (Engagement):** Interactive Keeper chat in React, subscription detection with renewal warnings, streak gamification, paycheck tracer, conversational categorization
- **Phase C (Family):** Family narrative view with emotional onramp and privacy shields, dragon visualization with states, balance trends, Dollar River spending flow, family quest board
- **Phase D (Intelligence):** Lifetime financial projections, scenario simulator, debt archaeology, Freedom Index, vacation projector
- **Phase E (Expansion):** Voice interface, Amazon/PayPal decoding, Obsidian bridge, multi-channel agent, two-income battle plan

### Key Differentiators

1. **Agent-first engagement architecture** — No other personal finance tool leads with a conversational AI agent that pushes awareness daily. The dashboard exists but is secondary to the relationship. This addresses the fundamental engagement problem that killed Mint and limits YNAB to the ultra-disciplined minority.
2. **The Dragon Keeper narrative** — Debt as a dragon, progress as a quest, family members as co-adventurers. Transforms an emotionally charged topic into an engaging shared experience. Gamification (streaks, quests, countdowns) sustains daily engagement. Daily messages must feel varied and personal — never templated.
3. **Obsidian knowledge bridge** — Connects personal knowledge management (project priorities, anticipated costs, kid activities) to financial tracking. No budgeting tool in existence has access to the user's thinking and planning context. This is the true competitive moat — unfair advantage that no VC-funded fintech can replicate.
4. **Trust-first transparency** — Surfaces data quality metrics (sync health, categorization %, confidence scores) rather than hiding uncertainty. The user always knows what they can trust and what needs attention.
5. **Life-tailored categories** — "The Farm," "The Amazon Vortex," "Harris's Flying," "George's School" — categories built around this household's actual life, not generic financial templates.
6. **18-month transformation window** — Second income arriving, major expenses ending, kids approaching independence. Building now means data, habits, and family alignment are ready to strategically deploy these changes.

### Party Mode Insights (Agent Review)

- **PM (John):** Daily Slack push pulled into Phase A — more important for habit formation than interactive chat. Ship Phase A fast; don't let future phases delay it.
- **UX (Sally):** Daily Keeper messages must feel varied and personal, not templated. Family View needs an emotional onramp before hard numbers. Static dragon avatar in Phase A for emotional anchoring.
- **Strategy (Victor):** Dragon Keeper is a *financial relationship*, not a budgeting tool — this is a category distinction, not just positioning. Obsidian bridge is the true moat. The 18-month window is the strategic narrative.

## Target Users

### Primary User

**Master Cody — The Household Financial Manager**

- **Context:** Software developer, sole income earner (for now), manages all household finances. Lives on a farm with wife and two sons. Good income but credit card debt cycle driven by low spending visibility and tool friction.
- **Current behavior:** Spends and hopes for the best. Uses credit cards as a checking account safety net. Installed YNAB but abandoned it because categorization friction created a data-trust death spiral. Has 14 fragmented YNAB Streamlit tools he built but none that solve the core problem.
- **Emotional state:** Knows things aren't right but can't see clearly enough to act. Feels pressure from family questions ("why don't we have money?"). Wants control but is overwhelmed by the effort current tools demand.
- **Goals:** (1) Know what's safe to spend at any moment. (2) Break the credit card safety-net cycle. (3) Understand where every dollar goes. (4) Show the family the financial picture clearly. (5) Build toward retirement and financial freedom from job dependency.
- **Success looks like:** Opens a Slack message from The Keeper each morning, spends 30 seconds reviewing, feels informed and in control. Hasn't used a credit card in weeks because he trusts his checking balance. Can show Amanda and the kids exactly where money goes and why.
- **What makes him say "this is exactly what I needed":** The safe-to-spend number is accurate and he believes it. Categorization happens without him. The Keeper notices things he'd miss and brings them up. His family finally understands the picture.

### Secondary Users

**Amanda — The Financial Partner (Not a Tool User)**

- **Context:** Wife, currently in nursing school (~18 months from earning). Not engaged with finances day-to-day because the picture is unclear, not because she doesn't care. Willing to help maintain budgets and plan if given clarity.
- **Interaction model:** Does NOT use Dragon Keeper directly. Sees the Family View when Cody shares it. Participates in budget-setting conversations informed by Keeper data. Helps maintain agreed-upon budgets in daily life (e.g., sticking to dining-out targets).
- **Core need:** Clarity. "Show me where the money goes so I can help." Needs the paycheck tracer ("every dollar from income to destination") and the debt story told with context, not just numbers.
- **Success looks like:** Understands why good income doesn't mean disposable cash. Can participate in financial decisions ("can we afford this?") with real data instead of guesswork. Sees the dragon shrinking and feels like a co-adventurer, not a bystander.

**Harris (17) — The Soon-to-Be-Independent Son**

- **Context:** Taking flight lessons (expensive investment in his future). Approaching independence. Does not understand the value of money — hasn't had to.
- **Interaction model:** Sees the Family View occasionally. May participate in family quests. Primary exposure is through family conversations informed by Keeper data, not direct tool use.
- **Core need:** Understanding that things cost real money, that Dad's income is finite, and that the flight lessons he's receiving are a significant family investment. Needs this understanding before he's managing his own finances at 18+.
- **Success looks like:** When he asks for something, he has context for what it means to the family budget. Understands the concept of trade-offs ("flight lessons OR eating out more, not both"). Leaves home with basic financial awareness rather than the "spend and hope" pattern.

**George (13) — The Curious Kid**

- **Context:** In private school (expensive, 1 more year). Younger, less financially aware. Asks "why can't we just buy it?"
- **Interaction model:** Sees simplified Family View elements — particularly the dragon (engaging, visual, age-appropriate). May participate in family quests at a basic level.
- **Core need:** Understands where the money goes. Not full financial literacy — just "Dad works hard, money goes to school and house and food and animals, and we're working together to get rid of the dragon."
- **Success looks like:** Stops asking "why don't we have money?" because he can see the answer. Gets excited about the dragon shrinking. Understands that when the family says no, it's not arbitrary — it's a choice within a real system.

### User Journey

**Cody's Journey:**

| Stage | Experience |
|-------|-----------|
| **Day 1 (Setup)** | Imports YNAB data. Sees sync health go green. Auto-categorization runs — 70% handled automatically, 15 transactions queued for review. Reviews them in 2 minutes. Sees safe-to-spend number for the first time. Feels a mix of anxiety and relief — the number is real. |
| **Day 2-7 (Trust Building)** | Daily Keeper message via Slack: spending summary, streak count, one insight. Categorization queue is 3-5 items per day. Takes 30 seconds. Safe-to-spend number becomes the thing he checks before purchases. First time he puts something on debit instead of credit card because he trusts the number. |
| **Week 2-4 (Habit Formation)** | Streak counter grows. Categorization progress bar passes 90%. The Keeper's daily messages feel varied — sometimes a warning, sometimes a celebration, sometimes a strategic observation. Cody starts to feel the data is trustworthy. Decides not to renew an annual subscription the Keeper flagged. Saves $200. |
| **Month 2 (Aha Moment)** | Cody shows Amanda the paycheck tracer. For the first time, she sees exactly where every dollar goes. "Oh — THAT's why we don't have money." They set dining-out and Amazon budgets together. The dragon has a name now. The kids see it on the Family View and ask about it. |
| **Month 3+ (New Normal)** | Daily Keeper check is as automatic as checking the weather. Credit card hasn't been used in weeks. Cushion quest is at 60%. Amanda participates in monthly budget reviews. Harris sees the cost of flight lessons in context and starts appreciating it. George checks the dragon at dinner. The family is aligned. |

**Amanda's Journey:**

| Stage | Experience |
|-------|-----------|
| **First exposure** | Cody shows her the Family View with the paycheck tracer. Emotional onramp: "Here's our plan, here's the dragon, here's how we win." Not "look how bad things are." |
| **Ongoing** | Monthly check-ins using Keeper data. Helps set and maintain budgets. Sees progress. Feels like a partner, not a spectator. |
| **Transformation** | When her income arrives, the Scenario Simulator shows exactly how to deploy it. They pick a strategy together. |

**Kids' Journey:**

| Stage | Experience |
|-------|-----------|
| **First exposure** | See the dragon on the Family View. It's cool. They want to know what it is. |
| **Ongoing** | Occasional family quests ("no Amazon requests for a week"). See the dragon shrink. Understand trade-offs when they ask for things. |
| **Growth** | Harris leaves home understanding that money is finite and choices matter. George develops financial awareness years earlier than most kids. |

## Success Metrics

### User Success Metrics (Behavioral Change)

| Metric | Measurement | Phase A Target | 6-Month Target | 12-Month Target |
|--------|------------|----------------|----------------|-----------------|
| **Daily Engagement** | Days Keeper message is read/acknowledged | 5 of 7 days/week | 6 of 7 days/week | Habitual (daily) |
| **Credit Card Non-Use Streak** | Consecutive days without a credit card purchase | 3 days | 14 days | 30+ days |
| **Categorization Rate** | % of transactions auto- or manually categorized | 80% | 90% | 95% |
| **Categorization Friction** | Time spent on daily categorization validation | < 2 minutes | < 1 minute | < 30 seconds |
| **Safe-to-Spend Trust** | User checks safe-to-spend before purchases (self-reported) | Occasionally | Usually | Reflexive |
| **Tool Retention** | Consecutive weeks of active use without abandonment | 4 weeks (Phase A) | 26 weeks | 52 weeks |

### Financial Outcome Metrics (The Dragon Shrinks)

| Metric | Measurement | Phase A Target | 6-Month Target | 12-Month Target |
|--------|------------|----------------|----------------|-----------------|
| **Checking Cushion** | Checking account buffer above zero | $0 → tracking starts | $1,000 | $2,000 |
| **Credit Card Debt** | Total credit card balance across all cards | Baseline established | 15% reduction | 30% reduction |
| **Interest Paid** | Monthly interest charges across all credit accounts | Baseline established | Decreasing trend | Measurably lower |
| **Subscription Spend** | Monthly recurring subscription total | Audit completed | 2+ cancelled | Ongoing optimization |
| **Dining Out Ratio** | Dining out as % of food spend (dining + groceries) | Baseline measured | Trending down | At agreed target |
| **Financial Freedom Index** | Months of expenses coverable without income | Baseline (likely < 1) | 1+ month | 2+ months |

### Family Alignment Metrics

| Metric | Measurement | Target |
|--------|------------|--------|
| **Amanda Engagement** | Monthly budget conversation using Keeper data | At least 1x/month by Month 2 |
| **Family View Shared** | Paycheck tracer and dragon shown to family | First share by Month 2 |
| **Budget Co-Ownership** | Budgets set collaboratively with Amanda | At least 2 categories co-managed by Month 3 |
| **Kids Awareness** | Harris and George can explain the dragon concept | By Month 3 |

### Business Objectives (Personal Life Goals)

Since Dragon Keeper is a personal tool, "business objectives" are life objectives measured in financial freedom and family alignment:

- **3-month objective:** Trust the data. Use the tool daily. Know safe-to-spend reflexively. First family conversation with real data.
- **6-month objective:** Credit card usage rare. Cushion at $1,000+. Amanda is a financial partner with visibility. Subscriptions audited and trimmed. Dining out at agreed target.
- **12-month objective:** Credit card debt reduced 30%. Cushion at $2,000. Freedom Index above 2 months. Family aligned on finances. Tool is as habitual as checking the weather. Ready for Amanda's income with a deployment plan.
- **18-month objective (transformation window):** Amanda's income arrives. George finishes private school. Two-income battle plan executes against remaining debt. Dragon visibly wounded. Retirement projection improves meaningfully.

### Key Performance Indicators (Leading Indicators)

These predict whether you're on track before the outcomes arrive:

| KPI | Why It Matters | Warning Threshold |
|-----|---------------|-------------------|
| **Days since last Keeper check-in** | If you stop reading, you stop caring | > 3 days = re-engagement needed |
| **Categorization queue depth** | Backlog growing = friction returning | > 20 uncategorized = pipeline needs tuning |
| **Sync staleness** | Stale data = untrustworthy data | Any account > 7 days = investigate |
| **Credit card transaction count** | Leading indicator of CC reliance | Increasing trend over 2 weeks = alert |
| **Safe-to-spend trend** | Is the cushion growing or shrinking? | 3 consecutive weeks declining = strategic review |

## MVP Scope

### Core Features (Phase A — "I Can Trust This")

**A1. Data Layer (YNAB Shadow Database)**
- Manual YNAB import triggerable from the UI
- Clean SQLite cache as single source of truth for all reads
- Schema migration scripts for reliable, versioned database structure
- Transfer detection and flagging (separate from real spending)
- Sync health indicators: last sync time, per-account green/yellow/red status, staleness warnings

**A2. Auto-Categorization Pipeline**
- Three-tier categorization on import: rules engine → LLM with confidence scoring → user validation queue
- High-confidence matches (>90%) auto-applied; low-confidence queued for user
- Pending categorization approval UI — minimal friction, fast approval
- Rules learning engine: auto-creates rules from repeated user corrections
- Write-back queue: approved categories batched and pushed to YNAB with rate limiting
- Categorization progress bar (% categorized this month)

**A3. Safe-to-Spend Number**
- Prominent, single number: checking balance minus pending bills minus budget commitments
- Green/yellow/red color coding
- One sentence from The Keeper contextualizing the number
- Upcoming bills detection based on recurring transaction patterns

**A4. Dragon Keeper Chat Agent (In-App)**
- Chat interface within the React app with Dragon Keeper persona
- Static Keeper avatar for emotional anchoring
- LLM-powered agent with MCP tool access to all financial data
- Conversational categorization approval ("I categorized 5 transactions today — look right?")
- Daily debrief generation: spending summary, streak, one insight, safe-to-spend
- Agent can answer questions about spending, balances, and trends

**A5. Three-Second Dashboard**
- Landing page: safe-to-spend (big, bold), dragon state (basic: sleeping/stirring/raging), streak counter, categorization %, sync health
- One click deeper for transaction details, category breakdown, balance view
- Basic account balance view (current balances, all accounts)

### Technical Foundation (MVP)
- Self-contained "Dragon Keeper wing" within Codiak (React + FastAPI)
- Unified DB module merging existing `ynab_mcp/queries.py` and Streamlit export code
- Rate-limited YNAB API client with retry logic
- Unified amount handling (milliunits/cents → dollars)
- No Streamlit — React + FastAPI only

### Out of Scope for MVP

| Feature | Rationale | Target Phase |
|---------|-----------|-------------|
| Discord / OpenClaw integration | In-app chat establishes the core relationship first | Phase B |
| Subscription detection & renewal warnings | Requires recurring transaction analysis; build on solid categorization first | Phase B |
| Streak gamification beyond basic counter | Streaks tracked in MVP, but full gamification (flames, dragon state changes, quests) in Phase B | Phase B |
| Paycheck tracer | Requires income detection and full category mapping; needs 1+ months of trusted categorized data | Phase B |
| Family View / privacy shields | Needs trusted, well-categorized data before sharing with family | Phase C |
| Dragon visualization (animated/interactive) | Static avatar in MVP; animated dragon states after core is proven | Phase C |
| Balance trend charts over time | Requires multiple sync snapshots accumulated over weeks | Phase C |
| Dollar River (Sankey diagram) | Migration of existing alluvial code; needs categorized data | Phase C |
| Lifetime projections / Scenario Simulator | Complex modeling; build after data foundation is solid | Phase D |
| Debt archaeology / Interest vampire | Historical analysis needs deep data; build after trust established | Phase D |
| Freedom Index / Vacation projector | Derived metrics; meaningful only after months of tracked data | Phase D |
| Voice interface | Technically complex; defer until agent relationship is proven | Phase E |
| Amazon/PayPal transaction decoding | API integration complexity; honesty-first flagging in MVP instead | Phase E |
| Obsidian bridge | Valuable moat but not essential for core financial management | Phase E |
| Auto-sync on schedule | Manual import first; scheduled sync after confidence is built | Phase E |
| Direct bank connections (Plaid) | Adds complexity; YNAB handles bank sync for now | Deferred indefinitely |
| Auto-cancelling subscriptions | Legally/technically impractical | Not planned |
| Email integration | Massive security surface, scope creep | Not planned |

### MVP Success Criteria

The MVP is successful when:

1. **Data trust achieved:** Categorization rate ≥ 80%, sync health green for all accounts, safe-to-spend number calculated and believed
2. **Daily habit forming:** Cody engages with the Keeper chat or dashboard ≥ 5 of 7 days per week for 4 consecutive weeks
3. **Behavioral shift started:** At least one instance of choosing debit over credit card because the safe-to-spend number was trusted
4. **Friction eliminated:** Daily categorization validation takes < 2 minutes
5. **Tool not abandoned:** Active use sustained through 4 full weeks (the YNAB death spiral broken)

**Go/No-Go for Phase B:** If all 5 criteria are met after 4 weeks of use, proceed to Phase B. If criteria 5 fails (tool abandoned), diagnose why before adding features — the problem is friction, not missing features.

### Future Vision

If Dragon Keeper succeeds through all phases, it becomes:

- A **living financial relationship** that has known Cody's money for years, with deep context and memory
- A **family financial operating system** where Amanda co-manages budgets, Harris leaves home financially literate, and George grows up understanding money
- A **life projection engine** that models retirement, major purchases, and life transitions with real data
- A **knowledge-connected financial tool** that bridges Obsidian notes (projects, priorities, plans) with spending reality — something no commercial fintech can replicate
- A **multi-channel companion** reachable via web, Discord, and voice — The Keeper is always on watch

The 18-month transformation window (Amanda's income + George's school ending + Harris's independence) is the proving ground. If Dragon Keeper can help the family navigate that transition strategically, it will have justified every hour of development.
