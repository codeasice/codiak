"""Payee investigation — Tavily web search + GPT-4o summary."""
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("dragon_keeper.investigate")


def investigate_payee(payee_name: str, amount: float | None = None, memo: str | None = None) -> dict:
    tavily_key = os.getenv("TAVILY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not tavily_key:
        return {"error": "TAVILY_API_KEY not configured."}
    if not openai_key:
        return {"error": "OPENAI_API_KEY not configured."}

    from tavily import TavilyClient
    from openai import OpenAI

    try:
        client = TavilyClient(api_key=tavily_key)
        results = client.search(
            query=f'"{payee_name}" business merchant what is this company',
            max_results=4,
            search_depth="basic",
        )
        snippets = "\n\n".join(
            f"- {r.get('title', '')}: {r.get('content', '')}"
            for r in results.get("results", [])
        )
    except Exception as e:
        logger.warning("Tavily search failed for '%s': %s", payee_name, e)
        snippets = ""

    context_parts = [f'Payee name: "{payee_name}"']
    if amount is not None:
        context_parts.append(f"Amount: ${abs(amount):.2f}")
    if memo:
        context_parts.append(f"Memo: {memo}")
    if snippets:
        context_parts.append(f"\nWeb search results:\n{snippets}")

    prompt = (
        "You are a financial assistant helping identify an unclear bank transaction. "
        "Based on the information below, explain in 2-3 sentences what this business is "
        "and what this charge most likely represents. Be specific and practical — the user "
        "needs to decide which budget category to assign it to.\n\n"
        + "\n".join(context_parts)
    )

    try:
        oai = OpenAI(api_key=openai_key)
        resp = oai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2,
        )
        summary = resp.choices[0].message.content or ""
    except Exception as e:
        logger.error("OpenAI summary failed for '%s': %s", payee_name, e)
        return {"error": f"Failed to generate summary: {e}"}

    return {
        "payee": payee_name,
        "summary": summary,
        "sources": [r.get("url") for r in results.get("results", [])] if snippets else [],
    }
