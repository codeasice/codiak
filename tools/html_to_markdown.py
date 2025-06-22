import streamlit as st

def render():
    st.write("Paste your rich HTML (formatted content) below. The tool will convert it to Markdown using markdownify.")
    st.info("You can paste formatted content (e.g., from a web page) directly into the editor below.")

    try:
        from markdownify import markdownify as md
    except ImportError:
        st.error("The markdownify package is required. Please install it with 'pip install markdownify'.")
        st.stop()

    from streamlit_quill import st_quill
    html_input = st_quill(
        value="",
        placeholder="Paste rich HTML or formatted content here...",
        html=True,
        key='html_to_md_editor',
    )
    markdown = ""
    if html_input:
        markdown = md(html_input)
        # Remove all blank lines
        markdown = "\n".join([line for line in markdown.splitlines() if line.strip()])
    st.text_area("Markdown Output:", value=markdown or "", height=200, key="markdown_output")