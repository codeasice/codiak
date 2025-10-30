import os
import json
import streamlit as st
from . import llm_utils


def _build_tree(root_path: str, max_depth: int, current_depth: int = 0, include_files: bool = True):
    if current_depth > max_depth:
        return None
    try:
        entries = sorted(os.listdir(root_path))
    except (FileNotFoundError, PermissionError, NotADirectoryError):
        return None

    folders = []
    files = []
    for entry in entries:
        if entry in (".obsidian", ".trash"):
            continue
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path):
            child = _build_tree(full_path, max_depth, current_depth + 1, include_files)
            folders.append({
                "name": entry,
                "path": full_path,
                "children": child.get("children", []) if isinstance(child, dict) else []
            })
        else:
            if include_files:
                files.append({"name": entry, "path": full_path})

    return {"children": folders + files}


def _collect_stats(root_path: str, max_depth: int):
    stats = {
        "total_files": 0,
        "total_folders": 0,
        "empty_folders": [],
        "shallow_files": [],
        "deeply_nested_folders": [],
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prevent descending into .obsidian and .trash
        for skip in (".obsidian", ".trash"):
            if skip in dirnames:
                dirnames.remove(skip)
        depth = os.path.relpath(dirpath, root_path).count(os.sep)
        stats["total_files"] += len(filenames)
        stats["total_folders"] += 1
        if not dirnames and not filenames:
            stats["empty_folders"].append(dirpath)
        if depth >= max_depth and dirnames:
            stats["deeply_nested_folders"].append(dirpath)
        for fname in filenames:
            if depth <= 1:
                stats["shallow_files"].append(os.path.join(dirpath, fname))

    return stats


def _recommendations(stats, root_path: str):
    recs = []
    if stats["empty_folders"]:
        recs.append(f"Remove or consolidate {len(stats['empty_folders'])} empty folder(s).")
    if stats["deeply_nested_folders"]:
        recs.append("Flatten deeply nested folders to simplify navigation.")
    shallow = [p for p in stats["shallow_files"] if os.path.dirname(p) == root_path]
    if shallow:
        recs.append(f"Move {len(shallow)} file(s) out of the vault root into topic folders.")
    if not recs:
        recs.append("Structure looks good. No obvious cleanup needed.")
    return recs


def _render_tree(tree, indent: int = 0, max_rows: int = 3000):
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

    walk(tree, indent)
    return "\n".join(lines)


def render(vault_path_default):
    st.write("Scan your Obsidian vault's folder structure up to a specified depth and get cleanup suggestions.")

    vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default)
    max_depth = st.number_input("Depth (levels)", min_value=0, max_value=12, value=3, step=1)
    show_files = st.checkbox("Include files in listing", value=True)
    run_btn = st.button("Analyze Structure")

    # Run analysis on demand and persist results
    if run_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
        else:
            with st.spinner("Scanning folders..."):
                tree = _build_tree(vault_path, max_depth, include_files=show_files)
                stats = _collect_stats(vault_path, max_depth)
            st.session_state["osa_tree"] = tree
            st.session_state["osa_stats"] = stats
            st.session_state["osa_params"] = {
                "vault_path": vault_path,
                "max_depth": max_depth,
                "include_files": show_files,
            }

    # Load last results (if any)
    tree = st.session_state.get("osa_tree")
    stats = st.session_state.get("osa_stats")
    # Ensure params are present for future use
    if "osa_params" not in st.session_state:
        st.session_state["osa_params"] = {"vault_path": vault_path, "max_depth": max_depth, "include_files": show_files}

    st.subheader("Structure Preview")
    if tree:
        preview = _render_tree(tree)
        st.code(preview)
    else:
        st.info("No analysis yet. Click 'Analyze Structure' to generate a preview.")

    st.subheader("Stats")
    col1, col2, col3 = st.columns(3)
    if stats:
        with col1:
            st.metric("Files", stats["total_files"])
        with col2:
            st.metric("Folders", stats["total_folders"])
        with col3:
            st.metric("Empty Folders", len(stats["empty_folders"]))
    else:
        st.caption("Run an analysis to see stats.")

    st.subheader("Recommendations")
    if stats:
        for rec in _recommendations(stats, vault_path):
            st.write(f"- {rec}")
    else:
        st.caption("Run an analysis to see recommendations.")

    with st.expander("Details"):
        if stats:
            st.write("Empty folders:")
            for p in stats["empty_folders"][:200]:
                st.text(p)
            st.write("Deeply nested folders (at or beyond depth):")
            for p in stats["deeply_nested_folders"][:200]:
                st.text(p)
            st.write("Shallow files (near root):")
            for p in stats["shallow_files"][:200]:
                st.text(p)
        else:
            st.caption("Run an analysis to see details.")

    st.download_button(
        label="Download JSON report",
        data=json.dumps({"stats": stats or {}}, indent=2),
        file_name="obsidian_structure_report.json",
        mime="application/json",
        disabled=not bool(stats),
    )

    st.subheader("LLM Analysis")

    # Debug section
    with st.expander("Debug LLM Configuration", expanded=False):
        st.write(f"OpenAI Available: {llm_utils.OPENAI_AVAILABLE}")
        st.write(f"LLM Client Available: {llm_utils.llm_client.is_available()}")
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            st.write(f"API Key Found: {api_key[:10]}...{api_key[-4:]}")
        else:
            st.write("No API Key Found")

    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], index=0)
    max_tokens = st.slider("Max tokens", min_value=128, max_value=2000, value=600, step=32)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    include_tree_in_prompt = st.checkbox("Include tree preview in prompt", value=True)

    # Custom prompt editor
    default_prompt = """You are an expert in knowledge base information architecture and Obsidian vault organization.

I use the PARA methodology (Projects, Areas, Resources, Archive) and want to maintain separate PARA structures for work and personal content.

Given the following summary stats and an optional tree preview, produce a concise set of recommendations to clean up the structure.

Focus on:
- PARA compliance (Projects, Areas, Resources, Archive folders)
- Work vs Personal separation
- Redundant folders and deep nesting
- Files at root that should be grouped
- Naming inconsistencies
- Suggested target structure

IMPORTANT: When suggesting moves or reorganizations, always show:
- Current location: [exact path]
- Destination: [exact path]

Output in bullet points with clear, actionable steps."""

    custom_prompt = st.text_area(
        "Custom Prompt",
        value=default_prompt,
        height=200,
        help="Edit the prompt sent to the LLM for analysis"
    )

    run_llm = st.button("Analyze with LLM")

    if run_llm:
        if not llm_utils.llm_client.is_available():
            st.error("LLM not available or API key not configured. Set OPENAI_API_KEY.")
        elif not (tree and stats):
            st.error("Please run 'Analyze Structure' first to generate data for the LLM.")
        else:
            # Build a concise prompt using the custom prompt
            preview_text = _render_tree(tree)
            preview_lines = preview_text.splitlines() if preview_text else []
            preview_snippet = "\n".join(preview_lines[:400]) if include_tree_in_prompt else "(omitted)"

            prompt = (
                custom_prompt + "\n\n"
                f"Vault: {vault_path}\n"
                f"Depth analyzed: {max_depth}\n"
                f"Stats: files={stats['total_files']}, folders={stats['total_folders']}, empty_folders={len(stats['empty_folders'])}, "
                f"deeply_nested_folders={len(stats['deeply_nested_folders'])}, shallow_files_near_root={len([p for p in stats['shallow_files'] if os.path.dirname(p)==vault_path])}\n\n"
                "Tree preview (truncated):\n" + preview_snippet
            )

            messages = [
                {"role": "system", "content": "Be precise, pragmatic, and opinionated. Optimize for ease of navigation and future scalability."},
                {"role": "user", "content": prompt},
            ]

            response, error = llm_utils.llm_client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                tool_name="ObsidianStructureAnalyzer",
                function_name="llm_structure_review",
            )

            if error:
                st.error(error)
            else:
                st.session_state["osa_llm_response"] = response

    if st.session_state.get("osa_llm_response"):
        st.markdown("**LLM Recommendations**")
        st.code(st.session_state["osa_llm_response"], language="text")


