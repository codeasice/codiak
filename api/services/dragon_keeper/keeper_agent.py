"""Keeper Agent — conversational financial assistant powered by OpenAI function calling."""
import json
import logging
import os
import re

from dotenv import load_dotenv
from openai import AsyncOpenAI

from api.models.dragon_keeper.db import (
    get_db,
    get_chat_history,
    save_chat_message,
    clear_chat_history,
    get_spending_summary,
    get_account_balances,
    get_recent_spending_by_category,
    get_queue_stats,
    get_pending_review_transactions,
    approve_categorization,
    enqueue_write_back,
)
from api.services.dragon_keeper.safe_to_spend import calculate_safe_to_spend
from api.services.dragon_keeper.learning import check_and_create_rule
from api.models.dragon_keeper.db import get_current_streak

load_dotenv()

logger = logging.getLogger("dragon_keeper.keeper_agent")

MAX_TOOL_ITERATIONS = 5

_SYSTEM_PROMPT_BASE = (
    "You are the Keeper — a friendly, concise financial assistant for Dragon Keeper. "
    "You have a warm but professional tone. You answer with specific numbers from the "
    "data and never guess. Keep responses under 3 sentences unless the user asks for "
    "detail. You can look up spending, balances, pending categorizations, approve or "
    "correct transactions, and generate daily debriefs. "
    "All monetary amounts in tool results are already in US dollars. "
    "Never mention milliunits, units, or any conversion — just say the dollar amount "
    "like a normal person (e.g. '$2,168.95'). "
    "When the user asks about a spending category using everyday language, map it to "
    "the closest matching category name from the list below. For example 'eating out' "
    "maps to 'Dining', 'groceries' maps to 'Groceries', etc. Always use the exact "
    "category name from this list when calling tools.\n\n"
)


def _build_system_prompt() -> str:
    """Build system prompt with the actual category names from the DB."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT cg.name as group_name, c.name as category_name
            FROM categories c
            JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE c.hidden = 0 AND c.deleted = 0 AND cg.hidden = 0 AND cg.deleted = 0
            ORDER BY cg.name, c.name
        """).fetchall()
    finally:
        conn.close()

    if not rows:
        return _SYSTEM_PROMPT_BASE + "Available categories: (none loaded yet — data not imported)"

    groups: dict[str, list[str]] = {}
    for r in rows:
        groups.setdefault(r["group_name"], []).append(r["category_name"])

    lines = ["Available categories:"]
    for group, cats in sorted(groups.items()):
        lines.append(f"  {group}: {', '.join(cats)}")

    return _SYSTEM_PROMPT_BASE + "\n".join(lines)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_spending",
            "description": "Look up spending totals and recent transactions, optionally filtered by payee name, category, or time range. Results include account name, payee, amount, and category for each transaction. Use days=0 for all-time totals. When the user asks for a 'total' without specifying a time period, use days=0.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payee": {"type": "string", "description": "Partial payee name to filter by"},
                    "category": {"type": "string", "description": "Partial category name to filter by"},
                    "days": {"type": "integer", "description": "Number of days to look back. Default 30. Use 0 for all time."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balances",
            "description": "Get all account balances and the safe-to-spend amount.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_breakdown",
            "description": "Get the top spending categories for a time period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to look back (default 30)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_categorizations",
            "description": "Get transactions waiting for categorization review.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_transactions",
            "description": "Approve one or more pending transactions using their suggested categories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of transaction IDs to approve",
                    },
                },
                "required": ["transaction_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "correct_transaction",
            "description": "Correct a transaction's category to a different one by category name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string", "description": "The transaction ID to correct"},
                    "category_name": {"type": "string", "description": "The correct category name"},
                },
                "required": ["transaction_id", "category_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recategorize_by_payee",
            "description": "Bulk re-categorize all transactions matching a payee pattern to a new category. Use this when the user wants to change multiple transactions from one payee to a different category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payee": {"type": "string", "description": "Payee name or partial match"},
                    "new_category": {"type": "string", "description": "The target category name to assign"},
                    "current_category": {"type": "string", "description": "Optional: only change transactions currently in this category"},
                },
                "required": ["payee", "new_category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_debrief",
            "description": "Generate a daily financial debrief with balances, spending, streak, and queue status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


_EMOJI_RE = re.compile(
    r"[\U00002600-\U000027BF\U0001F300-\U0001FAFF\U0000FE00-\U0000FE0F\U0000200D]+",
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def _find_category(conn, name: str) -> dict | None:
    """Fuzzy category lookup: tries exact LIKE, then emoji-stripped comparison."""
    row = conn.execute(
        "SELECT id, name FROM categories WHERE name LIKE ? AND deleted = 0",
        (f"%{name}%",),
    ).fetchone()
    if row:
        return dict(row)

    stripped = _strip_emoji(name)
    if stripped != name:
        row = conn.execute(
            "SELECT id, name FROM categories WHERE name LIKE ? AND deleted = 0",
            (f"%{stripped}%",),
        ).fetchone()
        if row:
            return dict(row)

    all_cats = conn.execute(
        "SELECT id, name FROM categories WHERE deleted = 0"
    ).fetchall()
    name_lower = stripped.lower()
    for cat in all_cats:
        if name_lower in _strip_emoji(cat["name"]).lower():
            return dict(cat)
    return None


def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool call and return the JSON result string."""
    try:
        if name == "query_spending":
            conn = get_db()
            try:
                days_val = args.get("days", 30)
                result = get_spending_summary(
                    conn,
                    payee_pattern=args.get("payee"),
                    category_name=args.get("category"),
                    days=days_val if days_val else None,
                )
            finally:
                conn.close()
            return json.dumps(result, default=str)

        if name == "get_balances":
            conn = get_db()
            try:
                balances = get_account_balances(conn)
            finally:
                conn.close()
            sts = calculate_safe_to_spend()
            return json.dumps({"accounts": balances, "safe_to_spend": sts}, default=str)

        if name == "get_spending_breakdown":
            conn = get_db()
            try:
                cats = get_recent_spending_by_category(conn, days=args.get("days", 30))
            finally:
                conn.close()
            return json.dumps({"categories": cats, "days": args.get("days", 30)}, default=str)

        if name == "get_pending_categorizations":
            conn = get_db()
            try:
                items = get_pending_review_transactions(conn)
            finally:
                conn.close()
            return json.dumps({"pending": items, "count": len(items)}, default=str)

        if name == "approve_transactions":
            conn = get_db()
            try:
                pending = get_pending_review_transactions(conn)
                pending_map = {item["id"]: item for item in pending}
                approved = 0
                for tid in args["transaction_ids"]:
                    item = pending_map.get(tid)
                    if item and item.get("suggested_category_id"):
                        cid = item["suggested_category_id"]
                        approve_categorization(conn, tid, cid)
                        enqueue_write_back(conn, tid, cid)
                        approved += 1
                        if item.get("payee_name"):
                            check_and_create_rule(item["payee_name"], cid)
                conn.commit()
            finally:
                conn.close()
            return json.dumps({"approved_count": approved, "requested": len(args["transaction_ids"])})

        if name == "correct_transaction":
            conn = get_db()
            try:
                cat = _find_category(conn, args["category_name"])
                if not cat:
                    return json.dumps({"error": f"Category '{args['category_name']}' not found"})
                cid = cat["id"]
                cat_name = cat["name"]
                tid = args["transaction_id"]
                approve_categorization(conn, tid, cid)
                enqueue_write_back(conn, tid, cid)
                conn.commit()
                txn = conn.execute("SELECT payee_name FROM transactions WHERE id = ?", (tid,)).fetchone()
                if txn and txn["payee_name"]:
                    check_and_create_rule(txn["payee_name"], cid)
            finally:
                conn.close()
            return json.dumps({"status": "corrected", "transaction_id": tid, "category": cat_name})

        if name == "recategorize_by_payee":
            conn = get_db()
            try:
                cat = _find_category(conn, args["new_category"])
                if not cat:
                    return json.dumps({"error": f"Category '{args['new_category']}' not found"})
                new_cid = cat["id"]
                new_cat_name = cat["name"]

                where = "t.payee_name LIKE ? AND t.deleted = 0 AND t.transfer_account_id IS NULL"
                params: list = [f"%{args['payee']}%"]

                if args.get("current_category"):
                    cur_cat = _find_category(conn, args["current_category"])
                    if cur_cat:
                        where += " AND t.category_id = ?"
                        params.append(cur_cat["id"])
                    else:
                        where += " AND c.name LIKE ?"
                        params.append(f"%{args['current_category']}%")

                rows = conn.execute(f"""
                    SELECT t.id, t.payee_name
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE {where}
                """, params).fetchall()

                updated = 0
                for r in rows:
                    conn.execute("""
                        UPDATE transactions
                        SET category_id = ?, categorization_status = 'approved',
                            suggested_category_id = ?, suggestion_confidence = 1.0,
                            suggestion_source = 'manual', updated_at = datetime('now')
                        WHERE id = ?
                    """, (new_cid, new_cid, r["id"]))
                    enqueue_write_back(conn, r["id"], new_cid)
                    updated += 1
                conn.commit()
            finally:
                conn.close()
            return json.dumps({
                "updated": updated,
                "payee_filter": args["payee"],
                "new_category": new_cat_name,
            })

        if name == "generate_debrief":
            sts = calculate_safe_to_spend()
            conn = get_db()
            try:
                breakdown = get_recent_spending_by_category(conn, days=7)
                streak = get_current_streak(conn)
                queue = get_queue_stats(conn)
            finally:
                conn.close()
            return json.dumps({
                "safe_to_spend": sts,
                "week_spending": breakdown[:10],
                "streak": streak,
                "queue": queue,
            }, default=str)

        return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        logger.exception("Tool execution error for %s", name)
        return json.dumps({"error": str(e)})


def _build_openai_messages(history: list[dict], user_message: str) -> list[dict]:
    """Convert DB chat history + new user message into OpenAI messages format.

    Only user and assistant text messages are included — tool call/response
    details are not replayed since the final assistant text captures the result.
    """
    messages = [{"role": "system", "content": _build_system_prompt()}]
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"] or ""})
    messages.append({"role": "user", "content": user_message})
    return messages


async def chat(user_message: str) -> dict:
    """Send a user message and get the Keeper's response, executing tool calls as needed."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "role": "assistant",
            "content": "I can't respond right now — the OpenAI API key is not configured. "
                       "Please set the OPENAI_API_KEY environment variable and restart.",
            "tool_calls_made": [],
        }

    client = AsyncOpenAI(api_key=api_key)

    conn = get_db()
    try:
        history = get_chat_history(conn)
        save_chat_message(conn, "user", user_message)
        conn.commit()
    finally:
        conn.close()

    messages = _build_openai_messages(history, user_message)
    tool_calls_made: list[str] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
            assistant_msg: dict = {"role": "assistant", "content": choice.message.content or ""}
            if choice.message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.message.tool_calls
                ]
            messages.append(assistant_msg)

            for tc in choice.message.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls_made.append(fn_name)
                result = _execute_tool(fn_name, fn_args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

            continue

        # Final text response
        content = choice.message.content or ""
        conn = get_db()
        try:
            tc_json = json.dumps(tool_calls_made) if tool_calls_made else None
            save_chat_message(conn, "assistant", content, tool_calls=tc_json)
            conn.commit()
        finally:
            conn.close()

        return {"role": "assistant", "content": content, "tool_calls_made": tool_calls_made}

    # Exhausted iterations — return whatever we have
    fallback = "I needed more steps to answer that. Could you try a simpler question?"
    conn = get_db()
    try:
        save_chat_message(conn, "assistant", fallback)
        conn.commit()
    finally:
        conn.close()
    return {"role": "assistant", "content": fallback, "tool_calls_made": tool_calls_made}


def get_history() -> list[dict]:
    """Return the full chat history."""
    conn = get_db()
    try:
        return get_chat_history(conn)
    finally:
        conn.close()


def reset_chat() -> None:
    """Clear all chat history."""
    conn = get_db()
    try:
        clear_chat_history(conn)
        conn.commit()
    finally:
        conn.close()
