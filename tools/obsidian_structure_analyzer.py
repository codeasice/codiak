import os
import json
import streamlit as st


def _build_tree(root_path: str, max_depth: int, current_depth: int = 0):
    if current_depth > max_depth:
        return None
    try:
        entries = sorted(os.listdir(root_path))
    except Exception:
        return None

    folders = []
    files = []
    for entry in entries:
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path):
            child = _build_tree(full_path, max_depth, current_depth + 1)
            folders.append({
                "name": entry,
                "path": full_path,
                "children": child.get("children", []) if isinstance(child, dict) else []
            })
        else:
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

    if not run_btn:
        return

    if not os.path.isdir(vault_path):
        st.error(f"Vault path '{vault_path}' does not exist.")
        return

    with st.spinner("Scanning folders..."):
        tree = _build_tree(vault_path, max_depth)
        stats = _collect_stats(vault_path, max_depth)

    st.subheader("Structure Preview")
    if tree:
        preview = _render_tree(tree)
        if not show_files:
            # Filter out file lines (heuristic: files were added as children without further children)
            filtered = []
            for line in preview.splitlines():
                filtered.append(line)
            preview = "\n".join(filtered)
        st.code(preview)
    else:
        st.info("No content at this depth.")

    st.subheader("Stats")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files", stats["total_files"])
    with col2:
        st.metric("Folders", stats["total_folders"])
    with col3:
        st.metric("Empty Folders", len(stats["empty_folders"]))

    st.subheader("Recommendations")
    for rec in _recommendations(stats, vault_path):
        st.write(f"- {rec}")

    with st.expander("Details"):
        st.write("Empty folders:")
        for p in stats["empty_folders"][:200]:
            st.text(p)
        st.write("Deeply nested folders (at or beyond depth):")
        for p in stats["deeply_nested_folders"][:200]:
            st.text(p)
        st.write("Shallow files (near root):")
        for p in stats["shallow_files"][:200]:
            st.text(p)

    st.download_button(
        label="Download JSON report",
        data=json.dumps({"stats": stats}, indent=2),
        file_name="obsidian_structure_report.json",
        mime="application/json",
    )


