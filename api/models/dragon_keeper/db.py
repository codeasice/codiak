"""SQLite connection manager and query helpers for Dragon Keeper."""
import json
import os
import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger("dragon_keeper.db")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
DB_PATH = os.path.join(DB_DIR, "dragon_keeper.db")


def get_db() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_migrations():
    """Run all pending migrations using fastmigrate."""
    from fastmigrate import create_db, run_migrations as fm_run
    os.makedirs(DB_DIR, exist_ok=True)
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "migrations", "dragon_keeper"
    )
    create_db(DB_PATH)
    fm_run(DB_PATH, migrations_dir)
    logger.info("Dragon Keeper migrations complete")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upsert_accounts(conn: sqlite3.Connection, accounts: list[dict]):
    for a in accounts:
        conn.execute("""
            INSERT INTO accounts (id, budget_id, name, type, on_budget, closed,
                balance, cleared_balance, uncleared_balance, note, deleted, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, type=excluded.type, on_budget=excluded.on_budget,
                closed=excluded.closed, balance=excluded.balance,
                cleared_balance=excluded.cleared_balance, uncleared_balance=excluded.uncleared_balance,
                note=excluded.note, deleted=excluded.deleted, updated_at=excluded.updated_at
        """, (a["id"], a["budget_id"], a["name"], a["type"], a["on_budget"], a["closed"],
              a["balance"], a["cleared_balance"], a["uncleared_balance"],
              a.get("note"), a.get("deleted", 0), _now_utc()))


def upsert_category_groups(conn: sqlite3.Connection, groups: list[dict]):
    for g in groups:
        conn.execute("""
            INSERT INTO category_groups (id, name, hidden, deleted, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, hidden=excluded.hidden,
                deleted=excluded.deleted, updated_at=excluded.updated_at
        """, (g["id"], g["name"], g.get("hidden", 0), g.get("deleted", 0), _now_utc()))


def upsert_categories(conn: sqlite3.Connection, categories: list[dict]):
    for c in categories:
        conn.execute("""
            INSERT INTO categories (id, category_group_id, name, hidden, budgeted, activity,
                balance, goal_type, goal_target, goal_target_month, goal_percentage_complete,
                note, deleted, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                category_group_id=excluded.category_group_id, name=excluded.name,
                hidden=excluded.hidden, budgeted=excluded.budgeted, activity=excluded.activity,
                balance=excluded.balance, goal_type=excluded.goal_type,
                goal_target=excluded.goal_target, goal_target_month=excluded.goal_target_month,
                goal_percentage_complete=excluded.goal_percentage_complete,
                note=excluded.note, deleted=excluded.deleted, updated_at=excluded.updated_at
        """, (c["id"], c["category_group_id"], c["name"], c.get("hidden", 0),
              c.get("budgeted", 0), c.get("activity", 0), c.get("balance", 0),
              c.get("goal_type"), c.get("goal_target"), c.get("goal_target_month"),
              c.get("goal_percentage_complete"), c.get("note"),
              c.get("deleted", 0), _now_utc()))


def upsert_payees(conn: sqlite3.Connection, payees: list[dict]):
    for p in payees:
        conn.execute("""
            INSERT INTO payees (id, name, deleted, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, deleted=excluded.deleted, updated_at=excluded.updated_at
        """, (p["id"], p["name"], p.get("deleted", 0), _now_utc()))


def upsert_transactions(conn: sqlite3.Connection, transactions: list[dict]):
    for t in transactions:
        conn.execute("""
            INSERT INTO transactions (id, account_id, date, amount, payee_id, payee_name,
                category_id, category_name, memo, cleared, approved, transfer_account_id,
                deleted, imported_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                account_id=excluded.account_id, date=excluded.date, amount=excluded.amount,
                payee_id=excluded.payee_id, payee_name=excluded.payee_name,
                category_id=excluded.category_id, category_name=excluded.category_name,
                memo=excluded.memo, cleared=excluded.cleared, approved=excluded.approved,
                transfer_account_id=excluded.transfer_account_id,
                deleted=excluded.deleted, updated_at=excluded.updated_at
        """, (t["id"], t["account_id"], t["date"], t["amount"],
              t.get("payee_id"), t.get("payee_name"),
              t.get("category_id"), t.get("category_name"),
              t.get("memo"), t["cleared"], t.get("approved", 0),
              t.get("transfer_account_id"), t.get("deleted", 0),
              _now_utc(), _now_utc()))


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str):
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def update_sync_state(
    conn: sqlite3.Connection,
    account_id: str,
    status: str,
    transactions_synced: int = 0,
    error: str | None = None,
):
    conn.execute("""
        INSERT INTO sync_state (account_id, server_knowledge, last_sync_at, last_sync_status, last_error, transactions_synced)
        VALUES (?, 0, ?, ?, ?, ?)
        ON CONFLICT(account_id) DO UPDATE SET
            last_sync_at=excluded.last_sync_at, last_sync_status=excluded.last_sync_status,
            last_error=excluded.last_error, transactions_synced=excluded.transactions_synced
    """, (account_id, _now_utc(), status, error, transactions_synced))


def log_sync_event(conn: sqlite3.Connection, account_id: str | None, event_type: str, details: str | None = None):
    conn.execute(
        "INSERT INTO sync_log (account_id, event_type, details, created_at) VALUES (?, ?, ?, ?)",
        (account_id, event_type, details, _now_utc()),
    )


def get_all_sync_states(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT ss.account_id, a.name as account_name, ss.last_sync_at,
               ss.last_sync_status, ss.last_error, ss.transactions_synced
        FROM sync_state ss
        JOIN accounts a ON ss.account_id = a.id
        ORDER BY a.name
    """).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Categorization helpers
# ---------------------------------------------------------------------------

def get_uncategorized_transactions(conn: sqlite3.Connection) -> list[dict]:
    """Get transactions that need categorization (no category_id, not transfers, not deleted)."""
    rows = conn.execute("""
        SELECT id, account_id, date, amount, payee_id, payee_name, memo,
               category_id, categorization_status
        FROM transactions
        WHERE (category_id IS NULL OR category_id = '')
        AND transfer_account_id IS NULL
        AND deleted = 0
        AND (categorization_status IS NULL OR categorization_status NOT IN ('approved', 'skipped'))
    """).fetchall()
    return [dict(r) for r in rows]


def get_categorization_rules(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT id, payee_pattern, match_type, category_id, min_amount, max_amount,
               confidence, source, times_applied
        FROM categorization_rules
        ORDER BY times_applied DESC, id
    """).fetchall()
    return [dict(r) for r in rows]


def apply_rule_to_transaction(conn: sqlite3.Connection, transaction_id: str, category_id: str, rule_id: int):
    conn.execute("""
        UPDATE transactions
        SET category_id = ?, categorization_status = 'rule_applied',
            suggested_category_id = ?, suggestion_confidence = 1.0,
            suggestion_source = 'rule', updated_at = ?
        WHERE id = ?
    """, (category_id, category_id, _now_utc(), transaction_id))
    conn.execute("""
        UPDATE categorization_rules SET times_applied = times_applied + 1, updated_at = ?
        WHERE id = ?
    """, (_now_utc(), rule_id))


def mark_pending_review(conn: sqlite3.Connection, transaction_id: str):
    conn.execute("""
        UPDATE transactions SET categorization_status = 'pending_review', updated_at = ?
        WHERE id = ?
    """, (_now_utc(), transaction_id))


def set_llm_suggestion(conn: sqlite3.Connection, transaction_id: str, category_id: str, confidence: float):
    conn.execute("""
        UPDATE transactions
        SET suggested_category_id = ?, suggestion_confidence = ?,
            suggestion_source = 'llm', categorization_status = 'pending_review',
            updated_at = ?
        WHERE id = ?
    """, (category_id, confidence, _now_utc(), transaction_id))


def get_pending_review_transactions(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT t.id, t.date, t.amount, t.payee_name, t.memo,
               t.category_id, t.category_name,
               t.suggested_category_id, t.suggestion_confidence, t.suggestion_source,
               t.categorization_status,
               c.name as suggested_category_name
        FROM transactions t
        LEFT JOIN categories c ON t.suggested_category_id = c.id
        WHERE t.categorization_status = 'pending_review'
        AND t.deleted = 0
        ORDER BY t.date DESC
    """).fetchall()
    return [dict(r) for r in rows]


def approve_categorization(conn: sqlite3.Connection, transaction_id: str, category_id: str):
    conn.execute("""
        UPDATE transactions
        SET category_id = ?, categorization_status = 'approved', updated_at = ?
        WHERE id = ?
    """, (category_id, _now_utc(), transaction_id))


def skip_categorization(conn: sqlite3.Connection, transaction_id: str):
    conn.execute("""
        UPDATE transactions SET categorization_status = 'skipped', updated_at = ?
        WHERE id = ?
    """, (_now_utc(), transaction_id))


def enqueue_write_back(conn: sqlite3.Connection, transaction_id: str, category_id: str):
    conn.execute("""
        INSERT INTO write_back_queue (transaction_id, category_id, status, created_at)
        VALUES (?, ?, 'pending', ?)
    """, (transaction_id, category_id, _now_utc()))


def get_queue_stats(conn: sqlite3.Connection) -> dict:
    row = conn.execute("""
        SELECT
            SUM(CASE WHEN categorization_status = 'pending_review' THEN 1 ELSE 0 END) as pending_count,
            SUM(CASE WHEN categorization_status = 'approved' THEN 1 ELSE 0 END) as approved_count,
            SUM(CASE WHEN categorization_status = 'rule_applied' THEN 1 ELSE 0 END) as rule_applied_count,
            SUM(CASE WHEN categorization_status = 'skipped' THEN 1 ELSE 0 END) as skipped_count,
            SUM(CASE WHEN category_id IS NOT NULL AND deleted = 0 AND transfer_account_id IS NULL THEN 1 ELSE 0 END) as categorized_count,
            COUNT(*) as total_count
        FROM transactions
        WHERE deleted = 0 AND transfer_account_id IS NULL
    """).fetchone()
    return dict(row) if row else {}


def get_correction_count(conn: sqlite3.Connection, payee_name: str, category_id: str) -> int:
    """Count how many times this payee was manually corrected to this category."""
    row = conn.execute("""
        SELECT COUNT(*) as cnt
        FROM transactions
        WHERE payee_name = ? AND category_id = ? AND categorization_status = 'approved'
        AND suggestion_source IN ('llm', 'manual')
    """, (payee_name, category_id)).fetchone()
    return row["cnt"] if row else 0


def rule_exists(conn: sqlite3.Connection, payee_pattern: str, category_id: str) -> bool:
    row = conn.execute("""
        SELECT COUNT(*) as cnt FROM categorization_rules
        WHERE payee_pattern = ? AND category_id = ? AND match_type = 'exact'
    """, (payee_pattern, category_id)).fetchone()
    return (row["cnt"] or 0) > 0


def create_learned_rule(conn: sqlite3.Connection, payee_name: str, category_id: str) -> int:
    cursor = conn.execute("""
        INSERT INTO categorization_rules (payee_pattern, match_type, category_id, confidence, source, times_applied, created_at, updated_at)
        VALUES (?, 'exact', ?, 1.0, 'learned', 0, ?, ?)
    """, (payee_name, category_id, _now_utc(), _now_utc()))
    return cursor.lastrowid


def apply_rule_retroactively(conn: sqlite3.Connection, rule_id: int, payee_pattern: str, category_id: str) -> int:
    """Apply a rule to all pending_review transactions matching the payee. Returns count updated."""
    now = _now_utc()
    cursor = conn.execute("""
        UPDATE transactions
        SET category_id = ?, categorization_status = 'rule_applied',
            suggested_category_id = ?, suggestion_confidence = 1.0,
            suggestion_source = 'rule', updated_at = ?
        WHERE payee_name = ? AND categorization_status = 'pending_review' AND deleted = 0
    """, (category_id, category_id, now, payee_pattern))
    affected = cursor.rowcount
    if affected > 0:
        conn.execute("""
            UPDATE categorization_rules SET times_applied = times_applied + ?, updated_at = ?
            WHERE id = ?
        """, (affected, now, rule_id))
    return affected


def get_manual_review_payees(conn: sqlite3.Connection) -> list[str]:
    """Get payees flagged for always-manual review (stored in settings as JSON)."""
    raw = conn.execute("SELECT value FROM settings WHERE key = 'manual_review_payees'").fetchone()
    if raw:
        return json.loads(raw["value"])
    return []


def set_manual_review_payees(conn: sqlite3.Connection, payees: list[str]):
    val = json.dumps(payees)
    conn.execute(
        "INSERT INTO settings (key, value) VALUES ('manual_review_payees', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (val,),
    )


# ---------------------------------------------------------------------------
# Rules CRUD helpers (Epic 4)
# ---------------------------------------------------------------------------

def get_rule_by_id(conn: sqlite3.Connection, rule_id: int) -> dict | None:
    row = conn.execute("""
        SELECT r.id, r.payee_pattern, r.match_type, r.category_id,
               r.min_amount, r.max_amount, r.confidence, r.source,
               r.times_applied, r.created_at, r.updated_at,
               c.name as category_name, cg.name as group_name
        FROM categorization_rules r
        LEFT JOIN categories c ON r.category_id = c.id
        LEFT JOIN category_groups cg ON c.category_group_id = cg.id
        WHERE r.id = ?
    """, (rule_id,)).fetchone()
    return dict(row) if row else None


def get_all_rules_with_categories(conn: sqlite3.Connection) -> list[dict]:
    """Get all rules with joined category/group names."""
    rows = conn.execute("""
        SELECT r.id, r.payee_pattern, r.match_type, r.category_id,
               r.min_amount, r.max_amount, r.confidence, r.source,
               r.times_applied, r.created_at, r.updated_at,
               c.name as category_name, cg.name as group_name
        FROM categorization_rules r
        LEFT JOIN categories c ON r.category_id = c.id
        LEFT JOIN category_groups cg ON c.category_group_id = cg.id
        ORDER BY r.times_applied DESC, r.id
    """).fetchall()
    return [dict(r) for r in rows]


def create_rule(conn: sqlite3.Connection, payee_pattern: str, match_type: str,
                category_id: str, min_amount: float | None = None,
                max_amount: float | None = None, confidence: float = 1.0,
                source: str = 'manual') -> int:
    now = _now_utc()
    cursor = conn.execute("""
        INSERT INTO categorization_rules
            (payee_pattern, match_type, category_id, min_amount, max_amount,
             confidence, source, times_applied, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (payee_pattern, match_type, category_id, min_amount, max_amount,
          confidence, source, now, now))
    return cursor.lastrowid


def update_rule(conn: sqlite3.Connection, rule_id: int, payee_pattern: str,
                match_type: str, category_id: str,
                min_amount: float | None = None, max_amount: float | None = None,
                confidence: float = 1.0):
    conn.execute("""
        UPDATE categorization_rules
        SET payee_pattern = ?, match_type = ?, category_id = ?,
            min_amount = ?, max_amount = ?, confidence = ?, updated_at = ?
        WHERE id = ?
    """, (payee_pattern, match_type, category_id, min_amount, max_amount,
          confidence, _now_utc(), rule_id))


def delete_rule(conn: sqlite3.Connection, rule_id: int):
    conn.execute("DELETE FROM categorization_rules WHERE id = ?", (rule_id,))


def preview_rule_matches(conn: sqlite3.Connection, payee_pattern: str, match_type: str,
                         min_amount: float | None = None, max_amount: float | None = None,
                         limit: int = 20) -> dict:
    """Preview which transactions would match a rule pattern. Returns {count, samples}."""
    if match_type == 'exact':
        where = "t.payee_name = ?"
        params: list = [payee_pattern]
    elif match_type == 'starts_with':
        where = "t.payee_name LIKE ?"
        params = [payee_pattern + '%']
    else:  # contains
        where = "t.payee_name LIKE ?"
        params = ['%' + payee_pattern + '%']

    amount_clauses = []
    if min_amount is not None:
        amount_clauses.append("ABS(t.amount) >= ?")
        params.append(min_amount)
    if max_amount is not None:
        amount_clauses.append("ABS(t.amount) <= ?")
        params.append(max_amount)

    full_where = f"{where} AND t.deleted = 0 AND t.transfer_account_id IS NULL"
    if amount_clauses:
        full_where += " AND " + " AND ".join(amount_clauses)

    count_row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM transactions t WHERE {full_where}", params
    ).fetchone()
    total = count_row["cnt"] if count_row else 0

    sample_rows = conn.execute(f"""
        SELECT t.id, t.date, t.amount, t.payee_name, t.memo,
               t.category_id, c.name as category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE {full_where}
        ORDER BY t.date DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    return {"count": total, "samples": [dict(r) for r in sample_rows]}


def bulk_reclassify(conn: sqlite3.Connection, payee_pattern: str, match_type: str,
                    category_id: str, min_amount: float | None = None,
                    max_amount: float | None = None) -> int:
    """Bulk-update transactions matching a pattern to a new category. Returns count updated."""
    if match_type == 'exact':
        where = "payee_name = ?"
        params: list = [payee_pattern]
    elif match_type == 'starts_with':
        where = "payee_name LIKE ?"
        params = [payee_pattern + '%']
    else:
        where = "payee_name LIKE ?"
        params = ['%' + payee_pattern + '%']

    amount_clauses = []
    if min_amount is not None:
        amount_clauses.append("ABS(amount) >= ?")
        params.append(min_amount)
    if max_amount is not None:
        amount_clauses.append("ABS(amount) <= ?")
        params.append(max_amount)

    full_where = f"{where} AND deleted = 0 AND transfer_account_id IS NULL"
    if amount_clauses:
        full_where += " AND " + " AND ".join(amount_clauses)

    now = _now_utc()
    cursor = conn.execute(f"""
        UPDATE transactions
        SET category_id = ?, categorization_status = 'rule_applied',
            suggested_category_id = ?, suggestion_confidence = 1.0,
            suggestion_source = 'rule', updated_at = ?
        WHERE {full_where}
    """, [category_id, category_id, now] + params)
    return cursor.rowcount


# ---------------------------------------------------------------------------
# Engagement / streak helpers (Epic 3)
# ---------------------------------------------------------------------------

def log_engagement_visit(conn: sqlite3.Connection) -> dict:
    """Log a visit for today. Returns the engagement record."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = _now_utc()
    conn.execute("""
        INSERT INTO engagement_log (date, visit_count, actions_count, first_visit_at, last_visit_at)
        VALUES (?, 1, 0, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            visit_count = visit_count + 1,
            last_visit_at = excluded.last_visit_at
    """, (today, now, now))
    conn.commit()
    row = conn.execute("SELECT * FROM engagement_log WHERE date = ?", (today,)).fetchone()
    return dict(row) if row else {}


def increment_engagement_actions(conn: sqlite3.Connection, count: int = 1):
    """Increment the action count for today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = _now_utc()
    conn.execute("""
        INSERT INTO engagement_log (date, visit_count, actions_count, first_visit_at, last_visit_at)
        VALUES (?, 1, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            actions_count = actions_count + ?,
            last_visit_at = excluded.last_visit_at
    """, (today, count, now, now, count))


def get_engagement_history(conn: sqlite3.Connection, days: int = 90) -> list[dict]:
    """Get engagement log for the last N days."""
    rows = conn.execute("""
        SELECT date, visit_count, actions_count
        FROM engagement_log
        WHERE date >= date('now', ?)
        ORDER BY date ASC
    """, (f"-{days} days",)).fetchall()
    return [dict(r) for r in rows]


def get_current_streak(conn: sqlite3.Connection) -> dict:
    """Calculate current consecutive-day streak and days since last visit."""
    rows = conn.execute("""
        SELECT date FROM engagement_log ORDER BY date DESC
    """).fetchall()
    if not rows:
        return {"streak": 0, "last_visit": None, "days_away": None}

    from datetime import timedelta
    dates = [datetime.strptime(r["date"], "%Y-%m-%d").date() for r in rows]
    today = datetime.now(timezone.utc).date()

    last_visit = dates[0]
    days_away = (today - last_visit).days

    streak = 0
    check = today
    for d in dates:
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        elif d < check:
            break

    return {"streak": streak, "last_visit": last_visit.isoformat(), "days_away": days_away}


# ---------------------------------------------------------------------------
# Spending trends helpers (Epic 3)
# ---------------------------------------------------------------------------

def get_spending_by_category_periods(conn: sqlite3.Connection, periods: int = 8) -> list[dict]:
    """Get spending per category per week for the last N weeks.
    Returns rows of {category_id, category_name, group_name, period_start, total}."""
    rows = conn.execute("""
        SELECT c.id as category_id, c.name as category_name, cg.name as group_name,
               date(t.date, 'weekday 0', '-6 days') as period_start,
               SUM(ABS(t.amount)) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        JOIN category_groups cg ON c.category_group_id = cg.id
        WHERE t.deleted = 0 AND t.transfer_account_id IS NULL
        AND t.amount < 0
        AND t.date >= date('now', ?)
        AND c.hidden = 0 AND cg.hidden = 0
        GROUP BY c.id, period_start
        ORDER BY c.id, period_start
    """, (f"-{periods * 7} days",)).fetchall()
    return [dict(r) for r in rows]


def get_category_transactions(conn: sqlite3.Connection, category_id: str, limit: int = 100) -> list[dict]:
    """Get transactions for a specific category, most recent first."""
    rows = conn.execute("""
        SELECT t.id, t.date, t.amount, t.payee_name, t.memo, t.account_id,
               a.name as account_name
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        WHERE t.category_id = ? AND t.deleted = 0
        ORDER BY t.date DESC
        LIMIT ?
    """, (category_id, limit)).fetchall()
    return [dict(r) for r in rows]


def get_category_spending_over_time(conn: sqlite3.Connection, category_id: str, periods: int = 12) -> list[dict]:
    """Get weekly spending totals for a single category."""
    rows = conn.execute("""
        SELECT date(t.date, 'weekday 0', '-6 days') as period_start,
               SUM(ABS(t.amount)) as total,
               COUNT(*) as txn_count
        FROM transactions t
        WHERE t.category_id = ? AND t.deleted = 0 AND t.amount < 0
        AND t.date >= date('now', ?)
        GROUP BY period_start
        ORDER BY period_start
    """, (category_id, f"-{periods * 7} days")).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Dragon state helpers (Epic 3)
# ---------------------------------------------------------------------------

def get_dragon_state_inputs(conn: sqlite3.Connection) -> dict:
    """Gather all inputs needed to compute dragon state: balances, queue, streak, sync health."""
    checking = conn.execute("""
        SELECT COALESCE(SUM(balance), 0) as total
        FROM accounts WHERE type = 'checking' AND closed = 0 AND deleted = 0
    """).fetchone()["total"]

    pending_queue = conn.execute("""
        SELECT COUNT(*) as cnt FROM transactions
        WHERE categorization_status = 'pending_review' AND deleted = 0
    """).fetchone()["cnt"]

    total_txns = conn.execute("""
        SELECT COUNT(*) as cnt FROM transactions
        WHERE deleted = 0 AND transfer_account_id IS NULL
    """).fetchone()["cnt"]

    categorized_txns = conn.execute("""
        SELECT COUNT(*) as cnt FROM transactions
        WHERE category_id IS NOT NULL AND deleted = 0 AND transfer_account_id IS NULL
    """).fetchone()["cnt"]

    sync_states = conn.execute("""
        SELECT last_sync_at, last_sync_status FROM sync_state
    """).fetchall()

    return {
        "checking_balance": checking,
        "pending_queue": pending_queue,
        "total_transactions": total_txns,
        "categorized_transactions": categorized_txns,
        "sync_states": [dict(r) for r in sync_states],
    }


# ---------------------------------------------------------------------------
# Chat history helpers (Epic 5)
# ---------------------------------------------------------------------------

def save_chat_message(conn: sqlite3.Connection, role: str, content: str,
                      tool_calls: str | None = None) -> int:
    cursor = conn.execute("""
        INSERT INTO chat_messages (role, content, tool_calls, created_at)
        VALUES (?, ?, ?, ?)
    """, (role, content, tool_calls, _now_utc()))
    return cursor.lastrowid


def get_chat_history(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    rows = conn.execute("""
        SELECT id, role, content, tool_calls, created_at
        FROM chat_messages
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in reversed(rows)]


def clear_chat_history(conn: sqlite3.Connection):
    conn.execute("DELETE FROM chat_messages")


def get_spending_summary(conn: sqlite3.Connection, payee_pattern: str | None = None,
                         category_name: str | None = None,
                         days: int | None = 30) -> dict:
    """Flexible spending query for the agent to answer financial questions.
    Pass days=0 or days=None for all-time."""
    where_parts = ["t.deleted = 0", "t.transfer_account_id IS NULL", "t.amount < 0"]
    if days:
        where_parts.append(f"t.date >= date('now', '-{days} days')")
    params: list = []

    if payee_pattern:
        where_parts.append("t.payee_name LIKE ?")
        params.append(f"%{payee_pattern}%")
    if category_name:
        where_parts.append("c.name LIKE ?")
        params.append(f"%{category_name}%")

    where = " AND ".join(where_parts)

    row = conn.execute(f"""
        SELECT COALESCE(SUM(ABS(t.amount)), 0) as total,
               COUNT(*) as txn_count
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE {where}
    """, params).fetchone()

    samples = conn.execute(f"""
        SELECT t.date, t.payee_name, t.amount, c.name as category_name,
               a.name as account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts a ON t.account_id = a.id
        WHERE {where}
        ORDER BY t.date DESC LIMIT 5
    """, params).fetchall()

    return {
        "total": round(row["total"], 2) if row else 0,
        "transaction_count": row["txn_count"] if row else 0,
        "days": days,
        "recent_samples": [dict(s) for s in samples],
    }


def get_account_balances(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT name, type, balance, cleared_balance
        FROM accounts
        WHERE closed = 0 AND deleted = 0
        ORDER BY type, name
    """).fetchall()
    return [dict(r) for r in rows]


def get_recent_spending_by_category(conn: sqlite3.Connection, days: int = 30) -> list[dict]:
    rows = conn.execute("""
        SELECT c.name as category_name, SUM(ABS(t.amount)) as total, COUNT(*) as txn_count
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.deleted = 0 AND t.transfer_account_id IS NULL AND t.amount < 0
        AND t.date >= date('now', ?)
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 15
    """, (f"-{days} days",)).fetchall()
    return [dict(r) for r in rows]
