"""Keeper Agent — conversational financial assistant powered by OpenAI function calling."""
import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from api.models.dragon_keeper.db import (
    get_db,
    get_chat_history,
    save_chat_message,
    clear_chat_history,
)
from api.services.dragon_keeper import keeper_tools as kt

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
    "category name from this list when calling tools. "
    "IMPORTANT: Never state that a category exists or doesn't exist based on memory. "
    "Always call search_categories first when the user asks about a specific category.\n\n"
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
    {
        "type": "function",
        "function": {
            "name": "search_categories",
            "description": "Search for categories by name. ALWAYS use this when the user asks whether a specific category exists — never answer category existence questions from memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The category name or partial name to search for"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sync",
            "description": "Pull fresh transaction and account data from YNAB, then push any approved categorizations back. Use when the user asks to sync, refresh, or update data from YNAB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flush_queue": {
                        "type": "boolean",
                        "description": "Also push approved categorizations back to YNAB (default true).",
                    },
                },
                "required": [],
            },
        },
    },
]


def _run_tool(name: str, args: dict) -> str:
    """Synchronous tool dispatch — called in a thread pool to avoid blocking the event loop."""
    try:
        if name == "query_spending":
            days = args.get("days", 30)
            result = kt.tool_query_spending(args.get("payee"), args.get("category"), days or 30)
        elif name == "get_balances":
            result = kt.tool_get_balances()
        elif name == "get_spending_breakdown":
            result = kt.tool_get_spending_breakdown(args.get("days", 30))
        elif name == "get_pending_categorizations":
            result = kt.tool_get_pending_categorizations()
        elif name == "approve_transactions":
            result = kt.tool_approve_transactions(args["transaction_ids"])
        elif name == "correct_transaction":
            result = kt.tool_correct_transaction(args["transaction_id"], args["category_name"])
        elif name == "recategorize_by_payee":
            result = kt.tool_recategorize_by_payee(
                args["payee"], args["new_category"], args.get("current_category")
            )
        elif name == "search_categories":
            result = kt.tool_search_categories(args["query"])
        elif name == "generate_debrief":
            result = kt.tool_generate_debrief()
        elif name == "sync":
            result = kt.tool_sync(args.get("flush_queue", True))
        else:
            result = {"error": f"Unknown tool: {name}"}
        return json.dumps(result, default=str)
    except Exception as e:
        logger.exception("Tool execution error for %s", name)
        return json.dumps({"error": str(e)})


async def _execute_tool(name: str, args: dict) -> str:
    """Run a tool in a thread pool so blocking I/O doesn't freeze the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_tool, name, args)


HISTORY_WINDOW = 20  # max prior messages to include (keeps token count bounded)


def _build_openai_messages(history: list[dict], user_message: str) -> list[dict]:
    """Convert DB chat history + new user message into OpenAI messages format.

    Only user and assistant text messages are included — tool call/response
    details are not replayed since the final assistant text captures the result.
    """
    messages = [{"role": "system", "content": _build_system_prompt()}]
    recent = [m for m in history if m["role"] in ("user", "assistant")][-HISTORY_WINDOW:]
    for msg in recent:
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
            model="gpt-4o",
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
                result = await _execute_tool(fn_name, fn_args)
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
