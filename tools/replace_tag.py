import streamlit as st
import os
import re

def render(vault_path):
    st.warning("This tool will modify your notes. Make sure you have a backup.")

    vault_path = st.text_input("Obsidian Vault Path", value=vault_path, key="vault_path_replace_tag")
    old_tag = st.text_input("Tag to replace (include #)", value="#oldtag", key="old_tag")
    new_tag = st.text_input("Replace with (include #)", value="#newtag", key="new_tag")
    ignore_string = st.text_input("Ignore files containing this string in filename", value="template", key="ignore_replace_tag")
    max_replacements = st.number_input("Max number of tag replacements to process", min_value=1, value=10, step=1)
    do_replace = st.checkbox("Replace tags now", value=False)
    search_btn = st.button("Search and Replace Tag")

    if search_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
        elif not old_tag or not new_tag:
            st.error("Both old and new tags must be specified.")
        else:
            total_files = 0
            files_with_replacements = {}
            replacements_done = [0]
            progress_bar = st.progress(0)
            status_text = st.empty()
            # Count total files
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if file.endswith(".md") and not (ignore_string and ignore_string in file):
                        total_files += 1
            # Scan and replace
            current_file = 0
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if ignore_string and ignore_string in file:
                        continue
                    if file.endswith(".md"):
                        current_file += 1
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, vault_path)
                        progress = current_file / total_files if total_files else 1
                        progress_bar.progress(progress)
                        status_text.write(f"Scanning {current_file} of {total_files}: {rel_path}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # Find all occurrences of the old tag
                        tag_pattern = re.escape(old_tag)
                        matches = list(re.finditer(tag_pattern, content))
                        if matches:
                            files_with_replacements[rel_path] = len(matches)
                            if do_replace and replacements_done[0] < max_replacements:
                                # Replace only up to the max_replacements limit
                                def limited_sub(match):
                                    if replacements_done[0] < max_replacements:
                                        replacements_done[0] += 1
                                        return new_tag
                                    else:
                                        return match.group(0)
                                new_content, n = re.subn(tag_pattern, limited_sub, content)
                                if new_content != content:
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(new_content)
                        if replacements_done[0] >= max_replacements:
                            break
                if replacements_done[0] >= max_replacements:
                    break
            progress_bar.empty()
            status_text.empty()
            if files_with_replacements:
                st.write(f"Found {len(files_with_replacements)} files containing '{old_tag}'")
                if do_replace:
                    st.success(f"Replaced {replacements_done[0]} occurrences of '{old_tag}' with '{new_tag}' (max {max_replacements})")
                for file_path, count in files_with_replacements.items():
                    with st.expander(f"{file_path} ({count} matches)"):
                        st.write(f"{count} occurrence(s) of '{old_tag}' found.")
            else:
                st.info(f"No files found containing the tag '{old_tag}'.")