# Dragon Keeper — Ideas & Backlog

## Recurring Transactions

**Status:** Idea

Detect, visualize, and manage recurring transactions (subscriptions, bills, memberships, etc.).

### Detection
- Identify recurring patterns automatically from transaction history (same payee, similar amount, regular cadence — weekly, monthly, annual)
- Flag near-matches (e.g. amount changes slightly, payee name varies like "Netflix" vs "Netflix.com")
- Surface newly detected recurring transactions for confirmation

### Visualization
- Dashboard widget showing upcoming recurring charges with next expected date and amount
- Calendar or timeline view of recurring transactions across the month
- Monthly recurring total (committed spend) vs discretionary spend breakdown
- Trend view: track how subscriptions/bills change over time (new ones added, old ones dropped, price changes)

### Management
- Manually mark a transaction/payee as recurring with cadence (weekly, biweekly, monthly, annual)
- Set expected amount and tolerance (flag if actual deviates by more than X%)
- Pause/archive recurring items that are cancelled but might reappear
- Feed recurring data into safe-to-spend calculation (pending bills already partially does this)

### Integration Points
- Safe-to-spend: subtract upcoming recurring charges from available balance
- Keeper greeting: "You have 3 bills due this week totaling $X"
- Keeper agent: "What subscriptions am I paying for?" / "How much do I spend on recurring?"
- Categorization: auto-categorize known recurring transactions with high confidence
