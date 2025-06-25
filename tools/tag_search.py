import streamlit as st
import os
from tools.tag_search_util import find_notes_with_tags

def render(vault_path_default):
    st.write("Search for notes containing any of the specified tags in your Obsidian vault.")
    vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default, key="vault_path_tag_search")
    tags_input = st.text_input("Tags to search for (comma or space separated, with or without #)", value="")
    search_btn = st.button("Search for Tags")
    tags = []
    if tags_input:
        if ',' in tags_input:
            tags = [t.strip() for t in tags_input.split(',') if t.strip()]
        else:
            tags = [t.strip() for t in tags_input.split() if t.strip()]
    results = []
    if search_btn and tags:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
        else:
            with st.spinner("Counting notes in vault..."):
                total_files = 0
                for root, _, files in os.walk(vault_path):
                    for file in files:
                        if file.endswith('.md'):
                            total_files += 1
            progress_bar = st.progress(0)
            status_text = st.empty()
            found = []
            scanned = 0
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if file.endswith('.md'):
                        scanned += 1
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        has_tag = False
                        yaml_end = -1
                        if content.startswith('---'):
                            yaml_end = content.find('---', 3)
                            if yaml_end != -1:
                                yaml_block = content[3:yaml_end].strip()
                                from tools.tag_search_util import parse_yaml_tags
                                tags_found = parse_yaml_tags(yaml_block)
                                if set(t.lstrip('#') for t in tags).intersection(t.lstrip('#') for t in tags_found):
                                    has_tag = True
                        if not has_tag:
                            body = content[yaml_end+3:] if yaml_end != -1 else content
                            from tools.tag_search_util import remove_code_blocks
                            body_no_code = remove_code_blocks(body)
                            for tag in tags:
                                import re
                                tag_pattern = r'(?<!\\w)#' + re.escape(tag.lstrip('#')) + r'(?![\\w/])'
                                if re.search(tag_pattern, body_no_code):
                                    has_tag = True
                                    break
                        if has_tag:
                            rel_path = os.path.relpath(file_path, vault_path)
                            title = os.path.splitext(os.path.basename(file))[0]
                            found.append({"title": title, "path": rel_path, "full_path": os.path.abspath(file_path)})
                        progress = scanned / total_files if total_files else 1
                        progress_bar.progress(progress)
                        status_text.text(f"Scanned {scanned} of {total_files} notes...")
            st.session_state['tag_search_results'] = found
            st.session_state['tag_search_params'] = {'vault_path': vault_path, 'tags': tags}
            progress_bar.empty()
            status_text.empty()
    # Display results
    results = st.session_state.get('tag_search_results', [])
    params = st.session_state.get('tag_search_params', {'vault_path': vault_path, 'tags': tags})
    if results:
        st.success(f"Found {len(results)} notes with tags: {', '.join(params['tags'])}")
        import pandas as pd
        table_data = [{"Note Name": r["title"], "Full Path": r["full_path"]} for r in results]
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    elif search_btn and not results:
        st.info("No notes found matching the specified tags.")