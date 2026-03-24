"""Engagement streak and activity tracking service."""
import logging
from api.models.dragon_keeper.db import (
    get_db,
    log_engagement_visit,
    increment_engagement_actions,
    get_engagement_history,
    get_current_streak,
)

logger = logging.getLogger("dragon_keeper.engagement")


def record_visit() -> dict:
    conn = get_db()
    try:
        today_record = log_engagement_visit(conn)
        streak = get_current_streak(conn)
        return {"today": today_record, "streak": streak}
    finally:
        conn.close()


def record_actions(count: int = 1) -> dict:
    conn = get_db()
    try:
        increment_engagement_actions(conn, count)
        conn.commit()
        return {"recorded": count}
    finally:
        conn.close()


def get_engagement_data() -> dict:
    conn = get_db()
    try:
        history = get_engagement_history(conn)
        streak = get_current_streak(conn)
        return {"history": history, "streak": streak}
    finally:
        conn.close()
