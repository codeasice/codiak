# Cursor Rule: For any new UI tool:
# 1. The filename must be snake_case and match the tool's id in lower_snake_case (e.g., ItemsToLinks -> items_to_links.py).
# 2. The file must define a top-level function named 'render' (no arguments, or with optional arguments for vault_path if needed).
# 3. The tool's id in ui_tools_metadata.py must match the CamelCase or PascalCase version of the filename.
# 4. The tool must be added to RENDER_FUNC_MAP in app.py, mapping the tool's id to the module's render function (e.g., 'ItemsToLinks': tools.items_to_links.render).
# This ensures the UI loader can dynamically import and call the render function without errors.

import streamlit as st
import re

def items_to_links(input_text: str, exclude_numbers: bool = False) -> str:
    """
    Converts each line in the input text to a link in the format [[item]].
    Optionally excludes leading numbers and punctuation from each line.
    Blank lines are ignored in the output.
    Args:
        input_text (str): Multiline string with one item per line.
        exclude_numbers (bool): If True, remove leading numbers and punctuation.
    Returns:
        str: Multiline string with each item converted to [[item]].
    """
    lines = input_text.strip().splitlines()
    processed_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if exclude_numbers:
            # Remove leading numbers, dots, parentheses, and whitespace (e.g., '1. ', '2) ', '3 - ')
            stripped = re.sub(r'^\s*\d+[.)\-:]*\s*', '', stripped)
        processed_lines.append(f'[[{stripped}]]')
    return '\n'.join(processed_lines)

def items_to_links_bold_only(input_text: str, exclude_numbers: bool = False) -> str:
    """
    Converts only the bolded portions of each line to Obsidian links.
    Looks for **text** or __text__ patterns and converts them to [[text]].

    Args:
        input_text (str): Multiline string with one item per line.
        exclude_numbers (bool): If True, remove leading numbers and punctuation.
    Returns:
        str: Multiline string with only bolded portions converted to links.
    """
    lines = input_text.strip().splitlines()
    processed_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if exclude_numbers:
            # Remove leading numbers, dots, parentheses, and whitespace (e.g., '1. ', '2) ', '3 - ')
            stripped = re.sub(r'^\s*\d+[.)\-:]*\s*', '', stripped)

        # Find bolded text patterns and convert them to links
        # Pattern matches **text** or __text__
        bold_pattern = r'\*\*(.*?)\*\*|__(.*?)__'

        def replace_bold_with_link(match):
            # Get the text from either ** or __ pattern
            text = match.group(1) if match.group(1) else match.group(2)
            return f'[[{text}]]'

        # Replace bolded text with links
        converted = re.sub(bold_pattern, replace_bold_with_link, stripped)
        processed_lines.append(converted)

    return '\n'.join(processed_lines)

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
        help="For 'Bold Only' mode: Use **text** or __text__ to mark portions for linking"
    )

    col1, col2 = st.columns(2)
    with col1:
        exclude_numbers = st.checkbox(
            "Exclude leading numbers from each line (e.g., '1. Item' → 'Item')",
            value=False,
            key="exclude_numbers_checkbox",
        )
    with col2:
        bold_only = st.checkbox(
            "Only link bolded portions (**text** → [[text]])",
            value=False,
            key="bold_only_checkbox",
            help="Convert only **bold** or __bold__ text to [[links]]"
        )

    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        add_links = st.button("Add Links", key="add_links_btn")
    with col3:
        remove_links = st.button("Remove Links", key="remove_links_btn")

    output = ""
    if add_links:
        if bold_only:
            output = items_to_links_bold_only(input_text, exclude_numbers=exclude_numbers)
        else:
            output = items_to_links(input_text, exclude_numbers=exclude_numbers)
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