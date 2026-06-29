# Subscription Payee Linking — Feature Spec

**Status:** Draft  
**Scope:** Dragon Keeper → Subscriptions (`recurring-items`)  
**Author:** Spec session (Jun 2026)

---

## Problem

Recurring detection creates one `recurring_items` row per **exact transaction payee string**. The same real-world subscription often appears multiple times when YNAB uses variant names (e.g. `NETFLIX.COM`, `Netflix`, `Netflix Inc`).

Today this causes:

- Duplicate rows in Subscriptions
- Fragmented charge-history sparklines
- Double-counting risk in Safe-to-Spend if both rows are STS-enabled
- Cancelled-charge alerts that miss charges under alias names
- Re-detection recreating split items after manual cleanup

---

## Goals

1. Let the user **explicitly combine** two or more recurring items that represent the same subscription/bill.
2. Let the user **unlink (separate)** a previously linked payee name.
3. Keep merges **reversible** and **user-initiated** — no auto-merge in v1.
4. Wire aliases through all backend consumers so numbers stay correct.

## Non-Goals (v1)

- Auto-suggesting merges (fuzzy matching, ML, “did you mean…”)
- Regex / wildcard payee patterns (reuse of `payee_pattern` as a LIKE pattern)
- Renaming payees in YNAB or rewriting transaction `payee_name` values
- Combining **income** items (paychecks) — expenses/subscriptions only
- Merging a subscription with an ad hoc recurring bill unless user confirms via preview

---

## Core Concept: Canonical Item + Aliases

Each logical subscription is represented by:

| Piece | Description |
|-------|-------------|
| **Canonical recurring item** | One row in `recurring_items` — display name, cadence, amount, STS, cancel state |
| **Primary payee** | `recurring_items.payee_name` — the canonical transaction name |
| **Linked aliases** | Additional exact payee strings stored in a new table, all rolling up to the canonical item |

The canonical row’s `payee_name` is never silently changed on merge; the user picks which item survives as canonical (or renames display separately in a future iteration).

---

## Data Model

### New table: `recurring_item_aliases`

```sql
CREATE TABLE IF NOT EXISTS recurring_item_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recurring_id INTEGER NOT NULL REFERENCES recurring_items(id) ON DELETE CASCADE,
    payee_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(payee_name COLLATE NOCASE)
);

CREATE INDEX IF NOT EXISTS idx_recurring_aliases_recurring_id
    ON recurring_item_aliases(recurring_id);
```

**Constraints:**

- `payee_name` is globally unique (case-insensitive) across aliases **and** canonical `recurring_items.payee_name`.
- One alias cannot belong to two canonical items.
- Deleting a canonical recurring item cascades aliases.

### Helper: resolve all payee names for an item

```python
def get_payee_names_for_item(conn, item: dict) -> list[str]:
    """Return [canonical payee_name, ...aliases] for queries."""
```

Used everywhere we currently filter on a single `payee_name`.

### Optional: `payee_pattern` field

Leave unchanged in v1. Future v2 could store a human-readable pattern summary (e.g. joined alias list) but matching stays exact-name via alias table.

---

## API

Base path: `/api/dragon-keeper/recurring` (existing router).

### Response changes

Extend `RecurringItem` in list response:

```typescript
interface RecurringItem {
  // ...existing fields...
  linked_payees: string[]   // aliases only (excludes canonical payee_name)
  all_payee_names: string[]   // canonical + aliases, for sparkline/tooltips
}
```

### `POST /recurring/{id}/link`

Link another recurring item (or a raw payee name) to this canonical item.

**Request:**

```json
{
  "source_recurring_id": 42   // preferred: merge another row
}
```

Alternative v1.1 (link by name without a row):

```json
{
  "payee_name": "NETFLIX.COM"
}
```

**Behavior:**

1. Validate canonical item exists, is `active`, type `expense`.
2. Validate source item exists, is `active`, type `expense`, not already canonical of another group.
3. Run merge preview checks (see Preview Rules).
4. Insert alias row(s): source’s `payee_name` → canonical `recurring_id`.
5. If source was a separate `recurring_items` row: **delete** source row (or archive — see Open Questions).
6. Recompute canonical metadata from combined transaction history (see Recompute).
7. Return updated canonical item.

**Errors:**

- `409` — payee already linked elsewhere
- `422` — type mismatch (income vs expense), cancelled/archived source, STS conflict without confirmation
- `400` — linking item to itself

### `DELETE /recurring/{id}/link/{payee_name}`

Unlink one alias from a canonical item.

**Behavior:**

1. Remove alias row (cannot unlink canonical `payee_name` — must use “Change primary” in v2 or re-link flow).
2. Trigger `detect_recurring_transactions()` for that payee only (or insert fresh unconfirmed row from history).
3. Return `{ unlinked_payee, new_recurring_id? }`.

### `GET /recurring/{id}/link/preview?source_recurring_id=42`

Returns merge preview without committing:

```json
{
  "canonical": { "id": 1, "payee_name": "Netflix", "expected_amount": 15.99, ... },
  "source": { "id": 42, "payee_name": "NETFLIX.COM", "expected_amount": 15.99, ... },
  "warnings": [
    { "code": "amount_mismatch", "message": "Amounts differ by 18%", "severity": "warning" },
    { "code": "cadence_mismatch", "message": "Monthly vs biweekly", "severity": "error" }
  ],
  "combined_charge_history": [{ "date": "2025-01-15", "amount": 15.99 }, ...],
  "combined_occurrence_count": 24,
  "combined_last_seen": "2026-05-12"
}
```

---

## Recompute After Merge

After linking, update the **canonical row only**:

| Field | Rule |
|-------|------|
| `expected_amount` | Weighted average of recent charges across all payee names (same logic as detection’s last N sample), or max if user chose “use canonical amount” in preview |
| `avg_amount` | Same as detection |
| `occurrence_count` | Sum of distinct charge dates across all payees |
| `last_seen_date` | Max date across all payees |
| `next_expected_date` | Re-run cadence math on combined date series |
| `is_subscription` | `true` if any source was subscription; user override preserved |
| `confirmed` | `true` if both were confirmed; else stays unconfirmed |
| `include_in_sts` | Canonical value wins; preview warns if source had different STS setting |

---

## Backend Touch Points

Every place that queries by single `payee_name` must use `get_payee_names_for_item()` or a batch equivalent.

| Module | File | Change |
|--------|------|--------|
| List + charge history | `api/routers/dragon_keeper/recurring.py` | `_get_charge_histories` accepts all names per item; attach `linked_payees` |
| Detection | `api/services/dragon_keeper/recurring_detection.py` | Skip payees that are aliases; update canonical row when alias payee detected; block `_insert_new` for aliased names |
| Cancelled charges | `recurring.py` | Alert queries all payee names |
| Safe-to-Spend projection | `api/services/dragon_keeper/projection.py` | No change if duplicate rows deleted on merge; add guard: alias payees must not have their own `recurring_items` row |
| Paycheck tracer | `api/services/dragon_keeper/paycheck_tracer.py` | Out of scope (income excluded) |
| Transaction explorer “recurring?” heuristic | `transaction_explorer.py` | Optional: check aliases table |

### Detection rules (critical)

```text
On detect:
  IF payee_name matches an alias (case-insensitive)
    → update parent canonical item stats only; do NOT insert new row
  ELIF payee_name matches canonical payee_name
    → existing behavior
  ELSE
    → existing behavior (maybe new row)
```

Also extend `_get_cancelled_payees` / existing-payee checks to include alias names so a cancelled canonical blocks re-split aliases.

---

## UI / UX

### Entry points

1. **Row action menu** on each expense row: `Link payee…`
2. **Multi-select** (stretch): select 2+ rows → `Combine selected`

Start with (1).

### Link flow

```text
[Link payee…] on canonical row
  → Modal: searchable dropdown of other active expense recurring items
  → [Preview] shows:
      - Both names
      - Combined sparkline (last 12 charges)
      - Warnings (amount/cadence mismatch)
      - Which row is canonical (radio: keep this row / keep other row)
  → [Combine] (disabled if blocking error)
  → Toast: "Linked NETFLIX.COM to Netflix"
```

### Display on merged row

Under payee name (subtitle area):

```text
Netflix
Monthly · 18 occurrences
Also: NETFLIX.COM, Netflix Inc   [manage ▾]
```

“Manage” dropdown:

- Unlink `NETFLIX.COM`
- Unlink `Netflix Inc`

### Unlink flow

```text
[Unlink NETFLIX.COM]
  → Confirm: "This will create a separate subscription entry for NETFLIX.COM"
  → On confirm: DELETE alias, run detection for that payee
  → New row appears in "Needs Confirmation" if pattern detected
```

### Sorting / sparklines

- Sort by name uses **canonical** `payee_name` only.
- Sparkline uses **combined** `charge_history` (already planned in API).
- Last Seen shows max date across all linked payees.

---

## Preview Rules

| Condition | Severity | Behavior |
|-----------|----------|----------|
| Amount differs > 10% | Warning | Show in preview; user can proceed |
| Amount differs > 50% | Error | Block unless user checks “These are the same subscription” |
| Cadence differs | Error | Block combine |
| Type differs (income vs expense) | Error | Block |
| One row cancelled/archived | Error | Block |
| Source already has aliases | Warning | Merge alias trees: all aliases move to canonical |
| Both STS-enabled | Info | After merge, one row — no double count |

---

## Edge Cases

| Case | Handling |
|------|----------|
| Link A→B, then link C→A | Allowed; C’s payee becomes alias on A |
| Unlink middle alias | Only that payee separates; others stay linked |
| Detect runs after merge | Alias payees update canonical; no duplicate rows |
| User deletes canonical item | CASCADE deletes aliases; orphaned payees may reappear on next detect |
| Same payee on two cards (rare) | Globally unique alias constraint prevents |
| Cancel subscription with aliases | Cancel applies to canonical item; post-cancel alerts check **all** payee names |
| Charge after cancel on alias name | Surfaces in existing “Unexpected Charges” alert |

---

## Phased Delivery

### Phase 1 — MVP (ship this)

- Migration `0014-recurring-item-aliases.sql`
- `POST link`, `DELETE unlink`, preview endpoint
- Update charge history + cancelled alerts + detection
- UI: link modal, alias display, unlink
- Expense items only

### Phase 2 — Polish

- Link by raw payee name (no existing recurring row)
- “Suggest duplicates” read-only panel (same amount ±5%, Levenshtein on name) — **suggestions only**
- Bulk combine

### Phase 3 — Optional

- Change canonical primary name
- `payee_pattern` display field
- Income/paycheck linking (separate spec)

---

## Test Plan

### Unit / service

- [ ] `get_payee_names_for_item` returns canonical + aliases
- [ ] Merge recomputes `last_seen_date`, `occurrence_count`, `expected_amount`
- [ ] Detection skips alias payees for insert; updates canonical
- [ ] Unlink + detect recreates row for unlinked payee
- [ ] Unique constraint rejects duplicate alias
- [ ] Cancelled charge alert finds charges on alias names

### Integration

- [ ] `GET /recurring` returns `linked_payees` and combined `charge_history`
- [ ] `POST link` deletes source row; STS total unchanged
- [ ] `DELETE link` restores separate detection

### Manual

- [ ] Combine two Netflix variants; sparkline shows full history
- [ ] Safe-to-Spend doesn’t double-count after merge
- [ ] Re-run Detect Recurring doesn’t split them again
- [ ] Unlink restores separate row in Needs Confirmation
- [ ] Cancel merged subscription; charge on alias triggers alert

---

## Open Questions

1. **Delete vs archive source row on merge?**  
   Recommend **delete** to avoid STS double-count; aliases preserve payee association. Audit trail via `created_at` on alias rows.

2. **Can user unlink the canonical payee name?**  
   v1: No — only aliases unlink. v2: “Promote alias to primary” swaps rows.

3. **Rename display without changing payee_name?**  
   Defer; could use `payees.display_name` later for UI only.

4. **Maximum aliases per item?**  
   No hard limit v1; soft warn at 5+.

---

## Files to Create / Modify

| Action | Path |
|--------|------|
| Create | `api/migrations/dragon_keeper/0014-recurring-item-aliases.sql` |
| Create | `api/services/dragon_keeper/recurring_linking.py` |
| Modify | `api/routers/dragon_keeper/recurring.py` |
| Modify | `api/services/dragon_keeper/recurring_detection.py` |
| Modify | `web/src/hooks/dragon-keeper/use-recurring.ts` |
| Modify | `web/src/components/dragon-keeper/recurring-items.tsx` |
| Create | `web/src/components/dragon-keeper/link-payee-modal.tsx` |

---

## Success Criteria

- User can combine two duplicate subscription rows in < 30 seconds.
- Combined row shows unified sparkline and correct Last Seen.
- Safe-to-Spend monthly expenses unchanged after merge (no double count).
- Detect Recurring does not recreate split rows for linked payees.
- User can unlink and get a separate entry back within one detect cycle.
