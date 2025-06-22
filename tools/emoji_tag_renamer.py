import streamlit as st
import os
import re

def render(vault_path_default):
    st.write("Identify notes with a specific tag that do not start with a specified emoji.")

    vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default)
    tag = st.text_input("Tag to search for (include #)", value="#person")
    emoji = st.text_input("Emoji to check for at start of filename", value="🧍")
    ignore_string = st.text_input("Ignore files containing this string", value="template")
    # Set update_limit before it is used
    if 'update_limit' in st.session_state:
        update_limit = st.session_state['update_limit']
    else:
        update_limit = 5
    search_btn = st.button("Search")

    if search_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
        else:
            notes = []
            notes_with_emoji = []
            with st.spinner("Searching for notes..."):
                for root, _, files in os.walk(vault_path):
                    for file in files:
                        # Ignore files whose filename contains the ignore_string
                        if ignore_string and ignore_string in file:
                            continue
                        if file.endswith(".md"):
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            # Check for tag in YAML frontmatter or body
                            has_tag = False
                            yaml_end = -1
                            if content.startswith('---'):
                                yaml_end = content.find('---', 3)
                                if yaml_end != -1:
                                    yaml_block = content[3:yaml_end].strip()
                                    lines = yaml_block.splitlines()
                                    in_tags = False
                                    tags_found = []
                                    for line in lines:
                                        line = line.strip()
                                        if line.startswith('tags:'):
                                            # tags: [person, friend] or tags:
                                            if '[' in line and ']' in line:
                                                # Inline list
                                                tag_list = line.split('[',1)[1].split(']',1)[0]
                                                tags_found = [t.strip().strip('"\'') for t in tag_list.split(',')]
                                                in_tags = False
                                            elif line.endswith(':'):
                                                in_tags = True
                                            else:
                                                # Single tag
                                                tag_val = line.split(':',1)[1].strip()
                                                if tag_val:
                                                    tags_found = [tag_val.strip('"\'')]
                                                in_tags = False
                                        elif in_tags:
                                            if line.startswith('- '):
                                                tags_found.append(line[2:].strip('"\''))
                                            else:
                                                in_tags = False
                                    # Remove # if present in tag input
                                    tag_clean = tag.lstrip('#')
                                    if tag_clean in tags_found:
                                        has_tag = True
                            # Check for tag in body (excluding code blocks)
                            if not has_tag:
                                # Get body after YAML frontmatter
                                body = content[yaml_end+3:] if yaml_end != -1 else content
                                # Remove code blocks (```...```)
                                def remove_code_blocks(text):
                                    result = []
                                    in_code = False
                                    for line in text.splitlines():
                                        if line.strip().startswith('```'):
                                            in_code = not in_code
                                            continue
                                        if not in_code:
                                            result.append(line)
                                    return '\n'.join(result)
                                body_no_code = remove_code_blocks(body)
                                if tag in body_no_code:
                                    has_tag = True
                            if has_tag:
                                rel_path = os.path.relpath(file_path, vault_path)
                                if file.startswith(emoji):
                                    notes_with_emoji.append(rel_path)
                                else:
                                    notes.append(rel_path)
            # Store results and params in session_state
            st.session_state['notes'] = notes
            st.session_state['notes_with_emoji'] = notes_with_emoji
            st.session_state['search_params'] = {
                'vault_path': vault_path,
                'tag': tag,
                'emoji': emoji,
                'ignore_string': ignore_string,
                'update_limit': update_limit
            }

    # Use session_state to display results and handle renaming
    notes = st.session_state.get('notes', [])
    notes_with_emoji = st.session_state.get('notes_with_emoji', [])
    params = st.session_state.get('search_params', {
        'vault_path': vault_path,
        'tag': tag,
        'emoji': emoji,
        'ignore_string': ignore_string,
        'update_limit': update_limit
    })
    if notes or notes_with_emoji:
        st.write(f"Found {len(notes_with_emoji)} notes with tag '{params['tag']}' that already start with '{params['emoji']}'")
        total = len(notes) + len(notes_with_emoji)
        st.write(f"Total notes with tag '{params['tag']}': {total}")
        if notes:
            st.success(f"Found {len(notes)} notes with tag '{params['tag']}' not starting with '{params['emoji']}'")
            with st.expander("Notes:"):
                for note in notes:
                    st.write(note)
            update_limit = st.number_input("Limit number of files to update", min_value=1, value=params['update_limit'], step=1, key="update_limit_input")
            params['update_limit'] = update_limit
            button_label = f"Prepend emoji to up to {update_limit} filenames"
            if st.button(button_label):
                renamed_count = 0
                for rel_path in notes[:params['update_limit']]:
                    old_path = os.path.join(params['vault_path'], rel_path)
                    dir_name, file_name = os.path.split(old_path)
                    if not file_name.startswith(params['emoji']):
                        new_file_name = params['emoji'] + file_name
                        new_path = os.path.join(dir_name, new_file_name)
                        os.rename(old_path, new_path)
                        renamed_count += 1
                st.session_state['success_message'] = f"Renamed {renamed_count} files by prepending '{params['emoji']}' to the filename."
                # After renaming, clear session_state to force a new search
                st.session_state.pop('notes', None)
                st.session_state.pop('notes_with_emoji', None)
                st.session_state.pop('search_params', None)
                st.rerun()
        else:
            st.info("No notes found matching the criteria.")