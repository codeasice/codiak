"""
Pure business logic for Obsidian tools.
No Streamlit imports — callable from FastAPI or any other context.
"""
import os
import json
from typing import Optional

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------------------
# Vault scanning helpers
# ---------------------------------------------------------------------------

def build_tree(root_path: str, max_depth: int, current_depth: int = 0) -> Optional[dict]:
    if current_depth > max_depth:
        return None
    try:
        entries = sorted(os.listdir(root_path))
    except (FileNotFoundError, PermissionError, NotADirectoryError):
        return None

    nodes = []
    for entry in entries:
        if entry in (".obsidian", ".trash"):
            continue
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path):
            child = build_tree(full_path, max_depth, current_depth + 1)
            nodes.append({
                "name": entry,
                "path": full_path,
                "children": child.get("children", []) if isinstance(child, dict) else [],
            })
        else:
            nodes.append({"name": entry, "path": full_path})

    return {"children": nodes}


def render_tree(tree: dict, max_rows: int = 1500) -> str:
    lines: list[str] = []

    def walk(node: dict, level: int):
        if not node:
            return
        for child in node.get("children", []):
            if len(lines) >= max_rows:
                return
            name = child.get("name", os.path.basename(child.get("path", "")))
            lines.append("  " * level + ("- " if level else "") + name)
            if "children" in child:
                walk(child, level + 1)

    walk(tree, 0)
    return "\n".join(lines)


def find_note_path(vault_path: str, note_query: str) -> Optional[str]:
    """Find a note by name or relative path (case-insensitive)."""
    if not note_query:
        return None

    candidate = os.path.join(vault_path, note_query)
    if os.path.isfile(candidate):
        return os.path.abspath(candidate)
    if os.path.isfile(candidate + ".md"):
        return os.path.abspath(candidate + ".md")

    target_lower = note_query.lower().removesuffix(".md")
    for dirpath, dirnames, filenames in os.walk(vault_path):
        dirnames[:] = [d for d in dirnames if d not in (".obsidian", ".trash")]
        for fname in filenames:
            if os.path.splitext(fname)[0].lower() == target_lower:
                return os.path.join(dirpath, fname)
    return None


# ---------------------------------------------------------------------------
# LLM recommendation
# ---------------------------------------------------------------------------

def _build_prompt(vault_path: str, root_scanned: str, page_name: str,
                  page_description: str, depth: int, tree_preview: str) -> str:
    return (
        "You are an expert Obsidian vault information architect.\n\n"
        f"Vault root: {vault_path}\n"
        f"Scan start: {root_scanned}\n"
        f"Scan depth: {depth}\n\n"
        f"New note name: {page_name}\n"
        f"New note description: {page_description or '(none provided)'}\n\n"
        "Given the scanned folder structure below (truncated), recommend the best target folder(s) "
        "within the scanned scope to place this note.\n"
        "Return a concise JSON object with up to 3 ranked suggestions. "
        "Each suggestion must include: 'path' (absolute path within vault), 'reason', "
        "and 'confidence' (0-1).\n\n"
        "Scanned structure (truncated):\n"
        f"{tree_preview}\n\n"
        'Output strictly as JSON with this schema: {"suggestions": [{"path": string, "reason": string, "confidence": number}]}'
    )


def recommend_note_placement(
    vault_path: str,
    page_name: str,
    page_description: str = "",
    depth: int = 3,
    parent_note_query: str = "",
    model: str = "gpt-4o",
    max_tokens: int = 500,
    temperature: float = 0.2,
) -> dict:
    """
    Scan the vault and return LLM-ranked folder suggestions for a new note.

    Returns dict with keys:
      - tree_preview: str
      - suggestions: list[{path, reason, confidence}]
      - error: str (only on failure)
    """
    if not os.path.isdir(vault_path):
        return {"error": f"Vault path '{vault_path}' does not exist or is not a directory."}

    # Resolve scan root
    scan_root = vault_path
    parent_note_resolved = None
    if parent_note_query.strip():
        note_path = find_note_path(vault_path, parent_note_query.strip())
        if note_path:
            parent_folder = os.path.dirname(note_path)
            if parent_folder and os.path.isdir(parent_folder):
                scan_root = parent_folder
                parent_note_resolved = note_path

    tree = build_tree(scan_root, depth)
    if not tree:
        return {"error": "Could not scan folders. Check path or permissions."}

    preview = render_tree(tree)

    if not OPENAI_AVAILABLE:
        return {"error": "openai package not installed. Run: pip install openai"}

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY environment variable not set."}

    client = OpenAI(api_key=api_key)

    prompt = _build_prompt(
        vault_path=vault_path,
        root_scanned=scan_root,
        page_name=page_name,
        page_description=page_description,
        depth=depth,
        tree_preview=preview,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Be practical and specific. Prefer existing topic folders. Return strict JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response_text = response.choices[0].message.content.strip()
    except Exception as e:
        return {"tree_preview": preview, "error": f"OpenAI error: {str(e)}"}

    # Parse JSON
    suggestions = []
    raw = response_text
    try:
        parsed = json.loads(raw)
        suggestions = parsed.get("suggestions", [])
    except Exception:
        # Try to extract JSON substring
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end > start:
                parsed = json.loads(raw[start:end + 1])
                suggestions = parsed.get("suggestions", [])
        except Exception:
            return {"tree_preview": preview, "error": "Could not parse LLM response as JSON.", "raw": raw}

    return {
        "tree_preview": preview,
        "suggestions": suggestions[:3],
        "scan_root": scan_root,
        "parent_note": parent_note_resolved,
    }
