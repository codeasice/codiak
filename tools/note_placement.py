import os
import json
import streamlit as st

from . import llm_utils


def _build_tree(root_path: str, max_depth: int, current_depth: int = 0):
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
            child = _build_tree(full_path, max_depth, current_depth + 1)
            nodes.append({
                "name": entry,
                "path": full_path,
                "children": child.get("children", []) if isinstance(child, dict) else []
            })
        else:
            nodes.append({"name": entry, "path": full_path})

    return {"children": nodes}


def _render_tree(tree, max_rows: int = 1500):
    lines = []

    def add_line(prefix, name):
        if len(lines) < max_rows:
            lines.append(f"{prefix}{name}")

    def walk(node, level):
        if not node:
            return
        for child in node.get("children", []):
            name = child.get("name", os.path.basename(child.get("path", "")))
            add_line("  " * level + ("- " if level else ""), name)
            if "children" in child:
                walk(child, level + 1)

    walk(tree, 0)
    return "\n".join(lines)


def _find_note_path(vault_path: str, note_query: str):
    """Find a note path by name or relative path. Returns the first match (case-insensitive)."""
    if not note_query:
        return None

    # If an exact file path was provided
    candidate = os.path.join(vault_path, note_query)
    if os.path.isfile(candidate):
        return os.path.abspath(candidate)
    if os.path.isfile(candidate + ".md"):
        return os.path.abspath(candidate + ".md")

    # Search by base name
    target_lower = note_query.lower().rstrip(".md")
    for dirpath, dirnames, filenames in os.walk(vault_path):
        if ".obsidian" in dirnames:
            dirnames.remove(".obsidian")
        if ".trash" in dirnames:
            dirnames.remove(".trash")
        for fname in filenames:
            base = os.path.splitext(fname)[0].lower()
            if base == target_lower:
                return os.path.join(dirpath, fname)
    return None


def _parent_folder_from_note(note_path: str):
    if not note_path:
        return None
    return os.path.dirname(note_path)


def _build_llm_prompt(vault_path: str,
                      root_scanned: str,
                      page_name: str,
                      page_description: str,
                      depth: int,
                      tree_preview: str) -> str:
    return (
        "You are an expert Obsidian vault information architect.\n\n"
        f"Vault root: {vault_path}\n"
        f"Scan start: {root_scanned}\n"
        f"Scan depth: {depth}\n\n"
        f"New note name: {page_name}\n"
        f"New note description: {page_description or '(none provided)'}\n\n"
        "Given the scanned folder structure below (truncated), recommend the best target folder(s) within the scanned scope to place this note.\n"
        "Return a concise JSON object with up to 3 ranked suggestions. Each suggestion must include: 'path' (absolute path within vault), 'reason', and 'confidence' (0-1).\n\n"
        "Scanned structure (truncated):\n"
        f"{tree_preview}\n\n"
        "Output strictly as JSON with this schema: {\"suggestions\": [ {\"path\": string, \"reason\": string, \"confidence\": number } ] }"
    )


def render(vault_path_default):
    st.write("Scan your Obsidian vault (top X levels) and get LLM-recommended placement for a new note.")

    vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default)
    col_a, col_b = st.columns(2)
    with col_a:
        page_name = st.text_input("New Note Name", value="")
    with col_b:
        parent_note_query = st.text_input("Optional: Start from Parent Note (name or path)", value="")

    page_description = st.text_area("Optional: Note Description / Context", value="", height=120)
    depth = st.number_input("Scan Depth (levels)", min_value=0, max_value=12, value=3, step=1)

    st.divider()
    st.caption("LLM Configuration")
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], index=0)
    max_tokens = st.slider("Max tokens", min_value=128, max_value=2000, value=500, step=32)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

    run_btn = st.button("Scan and Recommend")

    if run_btn:
        if not page_name.strip():
            st.error("Please provide a note name.")
            return
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
            return

        # Resolve scan root
        scan_root = vault_path
        if parent_note_query.strip():
            note_path = _find_note_path(vault_path, parent_note_query.strip())
            if not note_path:
                st.warning("Parent note not found; scanning from vault root instead.")
            else:
                parent_folder = _parent_folder_from_note(note_path)
                if parent_folder and os.path.isdir(parent_folder):
                    scan_root = parent_folder

        with st.spinner("Scanning folders..."):
            tree = _build_tree(scan_root, depth)

        if not tree:
            st.error("Could not scan folders. Check permissions or path.")
            return

        preview = _render_tree(tree)
        st.subheader("Structure Preview (truncated)")
        st.code(preview)

        if not llm_utils.llm_client.is_available():
            st.error("LLM not available or API key not configured. Set OPENAI_API_KEY.")
            return

        prompt = _build_llm_prompt(
            vault_path=vault_path,
            root_scanned=scan_root,
            page_name=page_name.strip(),
            page_description=page_description.strip(),
            depth=depth,
            tree_preview=preview,
        )

        messages = [
            {"role": "system", "content": "Be practical and specific. Prefer existing topic folders. Return strict JSON."},
            {"role": "user", "content": prompt},
        ]

        response_text, error = llm_utils.llm_client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            tool_name="ObsidianNotePlacement",
            function_name="recommend_note_location",
        )

        if error:
            st.error(error)
            return

        st.subheader("LLM Suggestions")

        parsed = None
        try:
            parsed = json.loads(response_text)
        except Exception:
            # Try to extract JSON substring if the model wrapped it with text
            try:
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    parsed = json.loads(response_text[start:end+1])
            except Exception:
                parsed = None

        if parsed and isinstance(parsed, dict) and "suggestions" in parsed:
            for i, s in enumerate(parsed.get("suggestions", [])[:3], start=1):
                path = s.get("path", "(missing)")
                reason = s.get("reason", "")
                conf = s.get("confidence", None)
                cols = st.columns([3, 1])
                with cols[0]:
                    st.write(f"{i}. {path}")
                    if reason:
                        st.caption(reason)
                with cols[1]:
                    if isinstance(conf, (int, float)):
                        st.metric("Confidence", f"{conf:.2f}")
        else:
            st.caption("Could not parse JSON. Raw response:")
            st.code(response_text, language="text")




