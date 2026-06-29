"""Link recurring items that share the same subscription under different payee names."""
import re
from collections import defaultdict
from difflib import SequenceMatcher
from fastapi import HTTPException
from api.models.dragon_keeper.db import get_db, _now_utc

CHARGE_HISTORY_LIMIT = 12
AMOUNT_MATCH_PCT = 5.0
NAME_SIMILARITY_THRESHOLD = 0.55
MANY_ALIASES_THRESHOLD = 5

def load_aliases_by_recurring_id(conn) -> dict[int, list[str]]:
    rows = conn.execute(
        "SELECT recurring_id, payee_name FROM recurring_item_aliases ORDER BY payee_name"
    ).fetchall()
    result: dict[int, list[str]] = defaultdict(list)
    for row in rows:
        result[row["recurring_id"]].append(row["payee_name"])
    return dict(result)


def get_payee_names_for_item(conn, item_id: int) -> list[str]:
    row = conn.execute(
        "SELECT payee_name FROM recurring_items WHERE id = ?", (item_id,)
    ).fetchone()
    if not row:
        return []
    aliases = conn.execute(
        "SELECT payee_name FROM recurring_item_aliases WHERE recurring_id = ? ORDER BY payee_name",
        (item_id,),
    ).fetchall()
    return [row["payee_name"]] + [a["payee_name"] for a in aliases]


def get_alias_owner_id(conn, payee_name: str) -> int | None:
    row = conn.execute(
        "SELECT recurring_id FROM recurring_item_aliases WHERE LOWER(payee_name) = LOWER(?)",
        (payee_name,),
    ).fetchone()
    return row["recurring_id"] if row else None


def get_all_alias_payees_lower(conn) -> dict[str, int]:
    rows = conn.execute(
        "SELECT recurring_id, payee_name FROM recurring_item_aliases"
    ).fetchall()
    return {row["payee_name"].lower(): row["recurring_id"] for row in rows}


def get_combined_charge_history(
    conn, payee_names: list[str], limit: int = CHARGE_HISTORY_LIMIT
) -> list[dict]:
    if not payee_names:
        return []
    lower_names = list({name.lower() for name in payee_names})
    placeholders = ",".join("?" * len(lower_names))
    rows = conn.execute(f"""
        SELECT date, amount FROM transactions
        WHERE deleted = 0 AND transfer_account_id IS NULL
          AND payee_name IS NOT NULL AND payee_name != ''
          AND LOWER(payee_name) IN ({placeholders})
        ORDER BY date DESC
        LIMIT ?
    """, (*lower_names, limit)).fetchall()
    history = [{"date": row["date"], "amount": round(abs(row["amount"]), 2)} for row in rows]
    history.reverse()
    return history


def _get_item(conn, item_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM recurring_items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def _item_summary(item: dict) -> dict:
    return {
        "id": item["id"],
        "payee_name": item["payee_name"],
        "type": item["type"],
        "cadence": item["cadence"],
        "expected_amount": item["expected_amount"],
        "confirmed": bool(item["confirmed"]),
        "is_subscription": bool(item["is_subscription"]),
        "status": item["status"],
        "include_in_sts": bool(item["include_in_sts"]),
    }


def _validate_merge(canonical: dict, source: dict, conn, force_amount: bool = False) -> tuple[list[dict], bool]:
    warnings: list[dict] = []
    blocking = False

    if canonical["id"] == source["id"]:
        raise HTTPException(status_code=400, detail="Cannot link an item to itself")

    if canonical["type"] != "expense" or source["type"] != "expense":
        warnings.append({
            "code": "type_mismatch",
            "message": "Only expense items can be linked",
            "severity": "error",
        })
        blocking = True

    if canonical["status"] != "active" or source["status"] != "active":
        warnings.append({
            "code": "inactive",
            "message": "Both items must be active",
            "severity": "error",
        })
        blocking = True

    if canonical["cadence"] != source["cadence"]:
        warnings.append({
            "code": "cadence_mismatch",
            "message": f"Cadence differs ({canonical['cadence']} vs {source['cadence']})",
            "severity": "error",
        })
        blocking = True

    a1, a2 = canonical["expected_amount"], source["expected_amount"]
    if a1 > 0 and a2 > 0:
        pct_diff = abs(a1 - a2) / max(a1, a2) * 100
        if pct_diff > 50 and not force_amount:
            warnings.append({
                "code": "amount_mismatch",
                "message": f"Amounts differ by {pct_diff:.0f}% (${a1:.2f} vs ${a2:.2f})",
                "severity": "error",
            })
            blocking = True
        elif pct_diff > 10:
            warnings.append({
                "code": "amount_mismatch",
                "message": f"Amounts differ by {pct_diff:.0f}% (${a1:.2f} vs ${a2:.2f})",
                "severity": "warning",
            })

    source_id = source.get("id")
    if source_id:
        source_alias_count = conn.execute(
            "SELECT COUNT(*) as c FROM recurring_item_aliases WHERE recurring_id = ?",
            (source_id,),
        ).fetchone()["c"]
        if source_alias_count > 0:
            warnings.append({
                "code": "source_has_aliases",
                "message": f"Source has {source_alias_count} linked payee(s); they will move to the combined item",
                "severity": "warning",
            })

    if canonical["include_in_sts"] != source["include_in_sts"]:
        warnings.append({
            "code": "sts_diff",
            "message": "Safe-to-Spend settings differ; the kept row's setting will be used",
            "severity": "info",
        })

    canonical_alias_count = conn.execute(
        "SELECT COUNT(*) as c FROM recurring_item_aliases WHERE recurring_id = ?",
        (canonical["id"],),
    ).fetchone()["c"]
    source_id = source.get("id")
    source_alias_count_extra = 0
    if source_id and source_id != canonical["id"]:
        source_alias_count_extra = conn.execute(
            "SELECT COUNT(*) as c FROM recurring_item_aliases WHERE recurring_id = ?",
            (source_id,),
        ).fetchone()["c"]
    new_alias_count = canonical_alias_count + 1 + source_alias_count_extra
    if new_alias_count >= MANY_ALIASES_THRESHOLD:
        warnings.append({
            "code": "many_aliases",
            "message": f"Combined item will have {new_alias_count} linked payee names",
            "severity": "warning",
        })

    for payee in (source["payee_name"],):
        owner = get_alias_owner_id(conn, payee)
        if owner and owner not in (canonical["id"], source_id):
            warnings.append({
                "code": "already_linked",
                "message": f"'{payee}' is already linked to another subscription",
                "severity": "error",
            })
            blocking = True

    return warnings, blocking


def recompute_recurring_item(conn, item_id: int) -> None:
    item = _get_item(conn, item_id)
    if not item:
        return

    payee_names = get_payee_names_for_item(conn, item_id)
    txns: list[dict] = []
    for payee_name in payee_names:
        rows = conn.execute("""
            SELECT date, amount FROM transactions
            WHERE deleted = 0 AND transfer_account_id IS NULL
              AND LOWER(payee_name) = LOWER(?)
            ORDER BY date
        """, (payee_name,)).fetchall()
        txns.extend({"date": row["date"], "amount": row["amount"]} for row in rows)

    if not txns:
        return

    txns.sort(key=lambda t: t["date"])
    distinct_dates = sorted({t["date"] for t in txns})
    from api.services.dragon_keeper.recurring_detection import _analyze_payee
    result = _analyze_payee(item["payee_name"], txns)

    confirmed = bool(item["confirmed"])
    include_in_sts = bool(item["include_in_sts"])
    is_subscription = bool(item["is_subscription"])

    if result:
        conn.execute("""
            UPDATE recurring_items SET
                expected_amount = ?, avg_amount = ?, occurrence_count = ?,
                last_seen_date = ?, next_expected_date = ?, expected_day = ?,
                expected_day_2 = ?, cadence = ?,
                confirmed = ?, is_subscription = ?, updated_at = ?
            WHERE id = ?
        """, (
            result["expected_amount"],
            result["avg_amount"],
            len(distinct_dates),
            result["last_seen_date"],
            result["next_expected_date"],
            result["expected_day"],
            result.get("expected_day_2"),
            result["cadence"],
            1 if confirmed else 0,
            1 if is_subscription else 0,
            _now_utc(),
            item_id,
        ))
    else:
        conn.execute("""
            UPDATE recurring_items SET
                occurrence_count = ?, last_seen_date = ?, updated_at = ?
            WHERE id = ?
        """, (len(distinct_dates), distinct_dates[-1], _now_utc(), item_id))


def preview_link(
    item_id: int,
    source_recurring_id: int,
    canonical_recurring_id: int | None = None,
) -> dict:
    conn = get_db()
    try:
        anchor = _get_item(conn, item_id)
        source = _get_item(conn, source_recurring_id)
        if not anchor or not source:
            raise HTTPException(status_code=404, detail="Recurring item not found")

        keep_id = canonical_recurring_id or item_id
        if keep_id not in (anchor["id"], source["id"]):
            raise HTTPException(status_code=400, detail="canonical_recurring_id must be one of the two items")

        canonical = _get_item(conn, keep_id)
        other = source if keep_id == anchor["id"] else anchor
        if keep_id == source["id"]:
            other = anchor

        warnings, blocking = _validate_merge(canonical, other, conn)
        all_names = list({
            *get_payee_names_for_item(conn, canonical["id"]),
            *get_payee_names_for_item(conn, other["id"]),
        })
        combined_history = get_combined_charge_history(conn, all_names)
        if all_names:
            placeholders = ",".join("?" * len(all_names))
            combined_occurrence = conn.execute(f"""
                SELECT COUNT(DISTINCT date) as c FROM transactions
                WHERE deleted = 0 AND transfer_account_id IS NULL
                  AND LOWER(payee_name) IN ({placeholders})
            """, [n.lower() for n in all_names]).fetchone()["c"]
        else:
            combined_occurrence = 0

        dates = [h["date"] for h in combined_history]
        combined_last_seen = max(dates) if dates else None

        return {
            "canonical": _item_summary(canonical),
            "source": _item_summary(other),
            "warnings": warnings,
            "blocking": blocking,
            "combined_charge_history": combined_history,
            "combined_occurrence_count": combined_occurrence,
            "combined_last_seen": combined_last_seen,
        }
    finally:
        conn.close()


def link_recurring_items(
    item_id: int,
    source_recurring_id: int,
    canonical_recurring_id: int,
    force_amount: bool = False,
) -> dict:
    conn = get_db()
    try:
        preview = preview_link(item_id, source_recurring_id, canonical_recurring_id)
        if preview["blocking"] and not force_amount:
            raise HTTPException(status_code=422, detail={
                "message": "Cannot combine these items",
                "warnings": preview["warnings"],
            })
        if preview["blocking"] and force_amount:
            errors = [w for w in preview["warnings"] if w["severity"] == "error" and w["code"] != "amount_mismatch"]
            if errors:
                raise HTTPException(status_code=422, detail={
                    "message": "Cannot combine these items",
                    "warnings": errors,
                })

        canonical_id = canonical_recurring_id
        other_id = source_recurring_id if canonical_id == item_id else item_id
        if canonical_id == source_recurring_id:
            other_id = item_id

        canonical = _get_item(conn, canonical_id)
        other = _get_item(conn, other_id)
        if not canonical or not other:
            raise HTTPException(status_code=404, detail="Recurring item not found")

        now = _now_utc()
        conn.execute(
            "UPDATE recurring_item_aliases SET recurring_id = ? WHERE recurring_id = ?",
            (canonical_id, other_id),
        )

        existing_alias = conn.execute(
            "SELECT id FROM recurring_item_aliases WHERE LOWER(payee_name) = LOWER(?)",
            (other["payee_name"],),
        ).fetchone()
        if not existing_alias and other["payee_name"].lower() != canonical["payee_name"].lower():
            conn.execute(
                "INSERT INTO recurring_item_aliases (recurring_id, payee_name, created_at) VALUES (?, ?, ?)",
                (canonical_id, other["payee_name"], now),
            )

        merged_confirmed = bool(canonical["confirmed"]) and bool(other["confirmed"])
        merged_subscription = bool(canonical["is_subscription"]) or bool(other["is_subscription"])
        conn.execute("""
            UPDATE recurring_items SET
                confirmed = ?, is_subscription = ?, updated_at = ?
            WHERE id = ?
        """, (
            1 if merged_confirmed else 0,
            1 if merged_subscription else 0,
            now,
            canonical_id,
        ))

        conn.execute("DELETE FROM recurring_items WHERE id = ?", (other_id,))
        recompute_recurring_item(conn, canonical_id)
        conn.commit()

        updated = _get_item(conn, canonical_id)
        aliases = load_aliases_by_recurring_id(conn).get(canonical_id, [])
        return {
            "status": "linked",
            "item": {
                **_item_summary(updated),
                "linked_payees": aliases,
                "all_payee_names": [updated["payee_name"], *aliases],
            },
        }
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


def unlink_payee(recurring_id: int, payee_name: str) -> dict:
    conn = get_db()
    try:
        item = _get_item(conn, recurring_id)
        if not item:
            raise HTTPException(status_code=404, detail="Recurring item not found")

        if item["payee_name"].lower() == payee_name.lower():
            raise HTTPException(status_code=400, detail="Cannot unlink the primary payee name")

        alias = conn.execute(
            "SELECT id, payee_name FROM recurring_item_aliases WHERE recurring_id = ? AND LOWER(payee_name) = LOWER(?)",
            (recurring_id, payee_name),
        ).fetchone()
        if not alias:
            raise HTTPException(status_code=404, detail="Linked payee not found")

        unlinked_name = alias["payee_name"]
        conn.execute("DELETE FROM recurring_item_aliases WHERE id = ?", (alias["id"],))
        recompute_recurring_item(conn, recurring_id)
        new_id = detect_payee_for_name(conn, unlinked_name)
        conn.commit()
        return {"unlinked_payee": unlinked_name, "new_recurring_id": new_id}
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


def detect_payee_for_name(conn, payee_name: str) -> int | None:
    """Detect and insert a recurring item for one payee. Returns new item id or None."""
    if get_alias_owner_id(conn, payee_name):
        return None

    existing = conn.execute(
        "SELECT id FROM recurring_items WHERE LOWER(payee_name) = LOWER(?)",
        (payee_name,),
    ).fetchone()
    if existing:
        return existing["id"]

    rows = conn.execute("""
        SELECT payee_name, date, amount FROM transactions
        WHERE deleted = 0 AND transfer_account_id IS NULL
          AND LOWER(payee_name) = LOWER(?)
        ORDER BY date
    """, (payee_name,)).fetchall()
    if not rows:
        return None

    actual_name = rows[0]["payee_name"]
    txns = [{"date": row["date"], "amount": row["amount"]} for row in rows]
    from api.services.dragon_keeper.recurring_detection import _analyze_payee, _insert_new
    result = _analyze_payee(actual_name, txns)
    if not result:
        return None

    _insert_new(conn, result)
    new_row = conn.execute(
        "SELECT id FROM recurring_items WHERE LOWER(payee_name) = LOWER(?)",
        (actual_name,),
    ).fetchone()
    return new_row["id"] if new_row else None


def _normalize_payee_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _name_similarity(a: str, b: str) -> float:
    na, nb = _normalize_payee_name(a), _normalize_payee_name(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 0.9
    return SequenceMatcher(None, na, nb).ratio()


def _amount_diff_pct(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 100.0
    return abs(a - b) / max(a, b) * 100


def find_duplicate_suggestions() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, payee_name, cadence, expected_amount, type, status
            FROM recurring_items
            WHERE type = 'expense' AND status = 'active'
            ORDER BY payee_name
        """).fetchall()
        items = [dict(r) for r in rows]
        suggestions: list[dict] = []
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a["cadence"] != b["cadence"]:
                    continue
                amount_diff = _amount_diff_pct(a["expected_amount"], b["expected_amount"])
                if amount_diff > AMOUNT_MATCH_PCT:
                    continue
                similarity = _name_similarity(a["payee_name"], b["payee_name"])
                if similarity < NAME_SIMILARITY_THRESHOLD:
                    continue
                suggestions.append({
                    "item_a_id": a["id"],
                    "item_b_id": b["id"],
                    "payee_a": a["payee_name"],
                    "payee_b": b["payee_name"],
                    "cadence": a["cadence"],
                    "amount_a": a["expected_amount"],
                    "amount_b": b["expected_amount"],
                    "amount_diff_pct": round(amount_diff, 1),
                    "name_similarity": round(similarity, 2),
                })
        suggestions.sort(key=lambda s: (-s["name_similarity"], s["amount_diff_pct"]))
        return suggestions
    finally:
        conn.close()


def _analyze_payee_transactions(conn, payee_name: str) -> tuple[str, dict] | None:
    rows = conn.execute("""
        SELECT payee_name, date, amount FROM transactions
        WHERE deleted = 0 AND transfer_account_id IS NULL
          AND LOWER(payee_name) = LOWER(?)
        ORDER BY date
    """, (payee_name,)).fetchall()
    if not rows:
        return None
    actual_name = rows[0]["payee_name"]
    txns = [{"date": row["date"], "amount": row["amount"]} for row in rows]
    from api.services.dragon_keeper.recurring_detection import _analyze_payee
    result = _analyze_payee(actual_name, txns)
    if not result:
        return None
    return actual_name, result


def _ensure_payee_linkable(conn, payee_name: str, canonical_id: int) -> str:
    owner = get_alias_owner_id(conn, payee_name)
    if owner:
        if owner == canonical_id:
            raise HTTPException(status_code=409, detail=f"'{payee_name}' is already linked to this subscription")
        raise HTTPException(status_code=409, detail=f"'{payee_name}' is already linked to another subscription")

    existing = conn.execute(
        "SELECT id, payee_name FROM recurring_items WHERE LOWER(payee_name) = LOWER(?)",
        (payee_name,),
    ).fetchone()
    if existing:
        if existing["id"] == canonical_id:
            raise HTTPException(status_code=400, detail="Cannot link a subscription to itself")
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"'{existing['payee_name']}' already has its own subscription row — combine via the subscription list instead",
                "existing_recurring_id": existing["id"],
            },
        )

    analyzed = _analyze_payee_transactions(conn, payee_name)
    if not analyzed:
        raise HTTPException(status_code=404, detail=f"No recurring pattern found for '{payee_name}'")

    return analyzed[0]


def _source_from_payee_analysis(actual_name: str, analysis: dict) -> dict:
    return {
        "id": None,
        "payee_name": actual_name,
        "type": analysis["type"],
        "cadence": analysis["cadence"],
        "expected_amount": analysis["expected_amount"],
        "confirmed": False,
        "is_subscription": analysis.get("is_subscription", True),
        "status": "active",
        "include_in_sts": True,
    }


def preview_link_by_payee_name(item_id: int, payee_name: str) -> dict:
    conn = get_db()
    try:
        canonical = _get_item(conn, item_id)
        if not canonical:
            raise HTTPException(status_code=404, detail="Recurring item not found")
        if canonical["type"] != "expense" or canonical["status"] != "active":
            raise HTTPException(status_code=422, detail="Can only link payees to active expense subscriptions")

        actual_name = _ensure_payee_linkable(conn, payee_name, item_id)
        _, analysis = _analyze_payee_transactions(conn, actual_name)
        source = _source_from_payee_analysis(actual_name, analysis)

        warnings, blocking = _validate_merge(canonical, source, conn)
        all_names = list({*get_payee_names_for_item(conn, item_id), actual_name})
        combined_history = get_combined_charge_history(conn, all_names)
        if all_names:
            placeholders = ",".join("?" * len(all_names))
            combined_occurrence = conn.execute(f"""
                SELECT COUNT(DISTINCT date) as c FROM transactions
                WHERE deleted = 0 AND transfer_account_id IS NULL
                  AND LOWER(payee_name) IN ({placeholders})
            """, [n.lower() for n in all_names]).fetchone()["c"]
        else:
            combined_occurrence = 0
        dates = [h["date"] for h in combined_history]

        return {
            "canonical": _item_summary(canonical),
            "source": {
                "id": None,
                "payee_name": actual_name,
                "type": source["type"],
                "cadence": source["cadence"],
                "expected_amount": source["expected_amount"],
                "confirmed": False,
                "is_subscription": bool(source["is_subscription"]),
                "status": "active",
                "include_in_sts": True,
            },
            "warnings": warnings,
            "blocking": blocking,
            "combined_charge_history": combined_history,
            "combined_occurrence_count": combined_occurrence,
            "combined_last_seen": max(dates) if dates else None,
            "link_mode": "payee_name",
        }
    finally:
        conn.close()


def link_by_payee_name(item_id: int, payee_name: str, force_amount: bool = False) -> dict:
    conn = get_db()
    try:
        preview = preview_link_by_payee_name(item_id, payee_name)
        if preview["blocking"] and not force_amount:
            raise HTTPException(status_code=422, detail={
                "message": "Cannot link this payee",
                "warnings": preview["warnings"],
            })
        if preview["blocking"] and force_amount:
            errors = [w for w in preview["warnings"] if w["severity"] == "error" and w["code"] != "amount_mismatch"]
            if errors:
                raise HTTPException(status_code=422, detail={
                    "message": "Cannot link this payee",
                    "warnings": errors,
                })

        canonical = _get_item(conn, item_id)
        if not canonical:
            raise HTTPException(status_code=404, detail="Recurring item not found")

        actual_name = _ensure_payee_linkable(conn, payee_name, item_id)
        now = _now_utc()
        conn.execute(
            "INSERT INTO recurring_item_aliases (recurring_id, payee_name, created_at) VALUES (?, ?, ?)",
            (item_id, actual_name, now),
        )
        recompute_recurring_item(conn, item_id)
        conn.commit()

        updated = _get_item(conn, item_id)
        aliases = load_aliases_by_recurring_id(conn).get(item_id, [])
        return {
            "status": "linked",
            "item": {
                **_item_summary(updated),
                "linked_payees": aliases,
                "all_payee_names": [updated["payee_name"], *aliases],
            },
        }
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()
