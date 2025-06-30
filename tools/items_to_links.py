# Cursor Rule: For any new UI tool:
# 1. The filename must be snake_case and match the tool's id in lower_snake_case (e.g., ItemsToLinks -> items_to_links.py).
# 2. The file must define a top-level function named 'render' (no arguments, or with optional arguments for vault_path if needed).
# 3. The tool's id in ui_tools_metadata.py must match the CamelCase or PascalCase version of the filename.
# 4. The tool must be added to RENDER_FUNC_MAP in app.py, mapping the tool's id to the module's render function (e.g., 'ItemsToLinks': tools.items_to_links.render).
# This ensures the UI loader can dynamically import and call the render function without errors.

import streamlit as st
import re

def items_to_links(input_text: str) -> str:
    """
    Converts each line in the input text to a link in the format [[item]].
    Blank lines are ignored in the output.
    Args:
        input_text (str): Multiline string with one item per line.
    Returns:
        str: Multiline string with each item converted to [[item]].
    """
    lines = input_text.strip().splitlines()
    return '\n'.join(f'[[{line.strip()}]]' for line in lines if line.strip())

def links_to_items(input_text: str) -> str:
    """
    Converts each line in the input text from [[item]] to item (removes surrounding brackets if present).
    Blank lines are ignored in the output.
    Args:
        input_text (str): Multiline string with one link per line.
    Returns:
        str: Multiline string with each link converted to item.
    """
    lines = input_text.strip().splitlines()
    return '\n'.join(re.sub(r'^\[\[(.*)\]\]$', r'\1', line.strip()) for line in lines if line.strip())

def render():
    st.write("Paste your list of items (one per line) below. Use the buttons to add or remove Obsidian-style links.")
    st.info("Blank lines will be ignored. Output is suitable for Obsidian or similar markdown apps.")

    input_text = st.text_area(
        "Items (one per line or as links):",
        value="",
        height=200,
        key="items_to_links_input",
    )

    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        add_links = st.button("Add Links", key="add_links_btn")
    with col3:
        remove_links = st.button("Remove Links", key="remove_links_btn")

    output = ""
    if add_links:
        output = items_to_links(input_text)
    elif remove_links:
        output = links_to_items(input_text)

    if add_links or remove_links:
        st.text_area(
            "Output:",
            value=output or "",
            height=200,
            key="items_to_links_output",
        )

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # If a filename is provided as an argument, read from file
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            input_text = f.read()
    else:
        # Otherwise, read from stdin
        print("Paste your list of items (Ctrl+D to end):")
        input_text = sys.stdin.read()
    output = items_to_links(input_text)
    print("\nConverted links:\n")
    print(output)