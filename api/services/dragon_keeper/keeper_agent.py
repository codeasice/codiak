"""Keeper Agent — conversational financial assistant powered by OpenAI function calling.

Tools are discovered dynamically from the MCP server (ynab_mcp.ynab_server) so that
adding a new @mcp.tool() there automatically makes it available here — no manual
TOOLS list or _run_tool dispatch needed.
"""
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
    "Always call get_categories_tool first when the user asks about a specific category.\n\n"
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


# ---------------------------------------------------------------------------
# MCP-backed tool discovery and execution
# ---------------------------------------------------------------------------

_mcp_tools_cache: dict | None = None


async def _get_mcp_tools() -> dict:
    """Return the FastMCP FunctionTool dict, loading once and caching."""
    global _mcp_tools_cache
    if _mcp_tools_cache is None:
        from ynab_mcp.ynab_server import mcp
        _mcp_tools_cache = await mcp.get_tools()
    return _mcp_tools_cache


async def _get_openai_tools() -> list[dict]:
    """Convert MCP tool schemas to OpenAI function-calling format."""
    tools = await _get_mcp_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.parameters,
            },
        }
        for t in tools.values()
    ]


async def _execute_tool(name: str, args: dict) -> str:
    """Call a tool via FastMCP in-process and return the result as a JSON string."""
    tools = await _get_mcp_tools()
    tool = tools.get(name)
    if not tool:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = await tool.run(args)
        if result.content:
            return result.content[0].text
        return json.dumps({"error": "No content returned"})
    except Exception as e:
        logger.exception("Tool execution error for %s", name)
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Chat history helpers
# ---------------------------------------------------------------------------

HISTORY_WINDOW = 20


def _build_openai_messages(history: list[dict], user_message: str) -> list[dict]:
    """Convert DB chat history + new user message into OpenAI messages format.

    Only user and assistant text messages are replayed — tool call details are
    not included since the final assistant text captures the result.
    """
    messages = [{"role": "system", "content": _build_system_prompt()}]
    recent = [m for m in history if m["role"] in ("user", "assistant")][-HISTORY_WINDOW:]
    for msg in recent:
        messages.append({"role": msg["role"], "content": msg["content"] or ""})
    messages.append({"role": "user", "content": user_message})
    return messages


# ---------------------------------------------------------------------------
# Main chat entry point
# ---------------------------------------------------------------------------

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
    openai_tools = await _get_openai_tools()
    tool_calls_made: list[str] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools,
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

        content = choice.message.content or ""
        conn = get_db()
        try:
            tc_json = json.dumps(tool_calls_made) if tool_calls_made else None
            save_chat_message(conn, "assistant", content, tool_calls=tc_json)
            conn.commit()
        finally:
            conn.close()

        return {"role": "assistant", "content": content, "tool_calls_made": tool_calls_made}

    fallback = "I needed more steps to answer that. Could you try a simpler question?"
    conn = get_db()
    try:
        save_chat_message(conn, "assistant", fallback)
        conn.commit()
    finally:
        conn.close()
    return {"role": "assistant", "content": fallback, "tool_calls_made": tool_calls_made}


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------

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
