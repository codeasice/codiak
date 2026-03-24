"""Dragon state computation and keeper greeting service."""
import logging
from datetime import datetime, timezone

from api.models.dragon_keeper.db import get_db, get_dragon_state_inputs, get_current_streak, get_queue_stats
from api.services.dragon_keeper.safe_to_spend import calculate_safe_to_spend

logger = logging.getLogger("dragon_keeper.dragon_state")

BALANCE_CRITICAL = 100
BALANCE_ATTENTION = 500
QUEUE_ATTENTION = 50
QUEUE_CRITICAL = 200
CAT_PCT_ATTENTION = 50
CAT_PCT_CRITICAL = 25
SYNC_STALE_ATTENTION_HOURS = 24
SYNC_STALE_CRITICAL_DAYS = 7

STATE_CONFIG = {
    "sleeping": {"color": "var(--success)", "label": "Sleeping"},
    "stirring": {"color": "var(--warning)", "label": "Stirring"},
    "raging":   {"color": "var(--danger)",  "label": "Raging"},
}

SECONDS_PER_ITEM = 20


def _status_for(value: float, attention_threshold: float, critical_threshold: float, *, lower_is_worse: bool = True) -> str:
    if lower_is_worse:
        if value < critical_threshold:
            return "critical"
        if value < attention_threshold:
            return "attention"
    else:
        if value > critical_threshold:
            return "critical"
        if value > attention_threshold:
            return "attention"
    return "healthy"


def _sync_staleness_status(sync_states: list[dict]) -> tuple[str, str]:
    if not sync_states:
        return "healthy", "No sync data"

    now = datetime.now(timezone.utc)
    worst = "healthy"
    detail = "All syncs recent"

    for ss in sync_states:
        last = ss.get("last_sync_at")
        if not last:
            worst = "critical"
            detail = "Never synced"
            break
        try:
            ts = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            worst = "critical"
            detail = "Invalid sync timestamp"
            break

        hours_ago = (now - ts).total_seconds() / 3600
        if hours_ago > SYNC_STALE_CRITICAL_DAYS * 24:
            return "critical", f"Sync {hours_ago / 24:.0f}d ago"
        if hours_ago > SYNC_STALE_ATTENTION_HOURS:
            worst = "attention"
            detail = f"Sync {hours_ago:.0f}h ago"

    return worst, detail


def _resolve_state(statuses: list[str]) -> str:
    if "critical" in statuses:
        return "raging"
    if "attention" in statuses:
        return "stirring"
    return "sleeping"


def compute_dragon_state() -> dict:
    conn = get_db()
    try:
        inputs = get_dragon_state_inputs(conn)

        checking = inputs["checking_balance"]
        pending = inputs["pending_queue"]
        total = inputs["total_transactions"]
        categorized = inputs["categorized_transactions"]
        cat_pct = (categorized / total * 100) if total > 0 else 100.0

        balance_status = _status_for(checking, BALANCE_ATTENTION, BALANCE_CRITICAL)
        queue_status = _status_for(pending, QUEUE_ATTENTION, QUEUE_CRITICAL, lower_is_worse=False)
        cat_status = _status_for(cat_pct, CAT_PCT_ATTENTION, CAT_PCT_CRITICAL)
        sync_status, sync_detail = _sync_staleness_status(inputs["sync_states"])

        state = _resolve_state([balance_status, queue_status, cat_status, sync_status])
        cfg = STATE_CONFIG[state]

        components = [
            {"name": "Checking Balance", "status": balance_status,
             "detail": f"${checking:,.2f}"},
            {"name": "Review Queue", "status": queue_status,
             "detail": f"{pending} pending"},
            {"name": "Categorization", "status": cat_status,
             "detail": f"{cat_pct:.0f}% categorized"},
            {"name": "Sync Health", "status": sync_status,
             "detail": sync_detail},
        ]

        return {
            "state": state,
            "color": cfg["color"],
            "label": cfg["label"],
            "components": components,
        }
    finally:
        conn.close()


def generate_greeting() -> dict:
    conn = get_db()
    try:
        streak_data = get_current_streak(conn)
        queue = get_queue_stats(conn)
    finally:
        conn.close()

    sts = calculate_safe_to_spend()

    streak = streak_data.get("streak", 0)
    days_away = streak_data.get("days_away")
    pending = queue.get("pending_count", 0) or 0
    safe_amount = sts.get("amount", 0)

    recovery = False

    if days_away is not None and days_away > 1:
        recovery = True
        if pending == 0:
            greeting = "Welcome back! All caught up while you were away."
        else:
            est = pending * SECONDS_PER_ITEM
            time_label = f"~{est}s" if est < 60 else f"~{est // 60} min"
            greeting = f"Welcome back! {pending} to review, should take about {time_label}."
            if days_away > 7:
                greeting = f"Good to see you — it's been {days_away} days. {pending} items queued up ({time_label})."
    elif streak > 5:
        ctx = f"Safe to spend: ${safe_amount:,.2f}" if pending == 0 else f"{pending} items to review"
        greeting = f"{streak}-day streak! {ctx}"
    elif pending > 0:
        est = pending * SECONDS_PER_ITEM
        time_label = f"~{est}s" if est < 60 else f"~{est // 60} min"
        greeting = f"You have {pending} items to review ({time_label})"
    else:
        greeting = f"Everything looks good. Safe to spend: ${safe_amount:,.2f}"

    return {
        "greeting": greeting,
        "streak": streak,
        "days_away": days_away,
        "pending_count": pending,
        "safe_to_spend": safe_amount,
        "recovery": recovery,
    }
