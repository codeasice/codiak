import streamlit as st
import re

def strip_markdown(text, options):
    # Remove H1, H2, H3
    if options.get('h1'):
        text = re.sub(r'^# .+$', lambda m: m.group(0)[2:], text, flags=re.MULTILINE)
    if options.get('h2'):
        text = re.sub(r'^## .+$', lambda m: m.group(0)[3:], text, flags=re.MULTILINE)
    if options.get('h3'):
        text = re.sub(r'^### .+$', lambda m: m.group(0)[4:], text, flags=re.MULTILINE)
    # Remove bullets
    if options.get('bullets'):
        text = re.sub(r'^(\s*)[-*+]\s+', r'\1', text, flags=re.MULTILINE)
    # Remove checkboxes
    if options.get('checkboxes'):
        text = re.sub(r'^(\s*)[-*+] \[.\] ', r'\1', text, flags=re.MULTILINE)
    # Remove bold
    if options.get('bold'):
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    # Remove italic
    if options.get('italic'):
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove inline code
    if options.get('inline_code'):
        text = re.sub(r'`([^`]*)`', r'\1', text)
    # Remove code blocks
    if options.get('code_block'):
        text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove blockquotes
    if options.get('blockquote'):
        text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    if options.get('hr'):
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    return text

def render():
    st.write("Paste your markdown below. Select which markdown elements to remove, then click the button.")
    st.info("Useful for cleaning up markdown by removing specific formatting elements.")

    input_text = st.text_area(
        "Markdown Input:",
        value="",
        height=200,
        key="markdown_stripper_input",
    )

    st.write("**Select markdown elements to remove:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        h1 = st.checkbox("H1 (#)", value=True, key="strip_h1")
        h2 = st.checkbox("H2 (##)", value=True, key="strip_h2")
        h3 = st.checkbox("H3 (###)", value=True, key="strip_h3")
        bullets = st.checkbox("Bullets (-, *, +)", value=True, key="strip_bullets")
    with col2:
        checkboxes = st.checkbox("Checkboxes [ ] [x]", value=True, key="strip_checkboxes")
        bold = st.checkbox("Bold (**text**)", value=True, key="strip_bold")
        italic = st.checkbox("Italic (*text*)", value=True, key="strip_italic")
    with col3:
        inline_code = st.checkbox("Inline Code (`code`)", value=True, key="strip_inline_code")
        code_block = st.checkbox("Code Block (```)", value=True, key="strip_code_block")
        blockquote = st.checkbox("Blockquote (>)", value=True, key="strip_blockquote")
        hr = st.checkbox("Horizontal Rule (---)", value=True, key="strip_hr")

    options = {
        'h1': h1,
        'h2': h2,
        'h3': h3,
        'bullets': bullets,
        'checkboxes': checkboxes,
        'bold': bold,
        'italic': italic,
        'inline_code': inline_code,
        'code_block': code_block,
        'blockquote': blockquote,
        'hr': hr,
    }

    strip_btn = st.button("Remove Selected Formatting", key="strip_markdown_btn")
    output = ""
    if strip_btn:
        output = strip_markdown(input_text, options)

    if strip_btn:
        st.text_area(
            "Output:",
            value=output or "",
            height=200,
            key="markdown_stripper_output",
        )