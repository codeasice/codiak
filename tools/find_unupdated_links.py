import streamlit as st
import os
import re

def render(vault_path_default):
    st.write("Identify all #person notes that begin with the emoji, and find files that link to them without the emoji in the link.")

    vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default, key="vault_path_links")
    tag = st.text_input("Tag to search for (include #)", value="#person", key="tag_links")
    emoji = st.text_input("Emoji at start of filename", value="🧍", key="emoji_links")
    ignore_string = st.text_input("Ignore files containing this string in filename", value="template", key="ignore_links")
    fix_links = st.checkbox("Fix invalid links automatically", value=False)
    max_fixes = st.number_input("Max number of links to fix", min_value=1, value=5, step=1)
    search_btn = st.button("Search for unupdated links")

    if search_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
        else:
            # Count total number of markdown notes in the vault
            total_md_notes = 0
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if file.endswith(".md") and not (ignore_string and ignore_string in file):
                        total_md_notes += 1
            st.write(f"There are {total_md_notes} total markdown notes in the vault.")
            # Step 1: Find all #person notes that begin with the emoji
            person_notes = []
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if ignore_string and ignore_string in file:
                        continue
                    if file.endswith(".md") and file.startswith(emoji):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # Check for tag in YAML frontmatter or body (reuse logic)
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
                                        if '[' in line and ']' in line:
                                            tag_list = line.split('[',1)[1].split(']',1)[0]
                                            tags_found = [t.strip().strip('"\'') for t in tag_list.split(',')]
                                            in_tags = False
                                        elif line.endswith(':'):
                                            in_tags = True
                                        else:
                                            tag_val = line.split(':',1)[1].strip()
                                            if tag_val:
                                                tags_found = [tag_val.strip('"\'')]
                                            in_tags = False
                                    elif in_tags:
                                        if line.startswith('- '):
                                            tags_found.append(line[2:].strip('"\''))
                                        else:
                                            in_tags = False
                                tag_clean = tag.lstrip('#')
                                if tag_clean in tags_found:
                                    has_tag = True
                        if not has_tag:
                            body = content[yaml_end+3:] if yaml_end != -1 else content
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
                            person_notes.append((file, rel_path))
            st.write(f"Found {len(person_notes)} #person notes starting with '{emoji}' to validate for links.")

            # Step 2: For each, search all files for links to the note without the emoji
            total_notes = len(person_notes)
            progress_bar = st.progress(0)
            status_text = st.empty()
            realtime_container = st.container()
            total_valid_links = 0
            total_invalid_links = 0
            unupdated_links = {}
            summary_text = st.empty()
            links_list_text = st.empty()
            fixes_done = 0
            for idx, (note_file, rel_path) in enumerate(person_notes):
                status_text.write(f"Validating {idx+1} of {total_notes}: {note_file}")
                st.toast(f"Checking links for: {note_file}")
                progress_bar.progress((idx+1)/total_notes)
                # The note name without the emoji
                base_name = note_file[len(emoji):].rsplit('.md', 1)[0]
                # Possible link forms: [[Name]] or [[Name|...]]
                pattern_invalid = re.compile(rf'\[\[({re.escape(base_name)})(\||\]\])')
                pattern_valid = re.compile(rf'\[\[({re.escape(emoji + base_name)})(\||\]\])')
                found_in = []
                valid_count = 0
                for root, _, files in os.walk(vault_path):
                    for file in files:
                        if ignore_string and ignore_string in file:
                            continue
                        if file.endswith(".md"):
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if pattern_invalid.search(content):
                                rel_link_path = os.path.relpath(file_path, vault_path)
                                found_in.append(rel_link_path)
                            if pattern_valid.search(content):
                                valid_count += 1
                total_valid_links += valid_count
                total_invalid_links += len(found_in)
                status_text.write(f"Validating {idx+1} of {total_notes}: {note_file} — {valid_count} valid links found")
                if found_in:
                    unupdated_links[rel_path] = found_in
                # If fixing is enabled and we haven't reached the max, fix links
                if fix_links and fixes_done < max_fixes:
                    for f in found_in:
                        if fixes_done >= max_fixes:
                            break
                        file_path = os.path.join(vault_path, f)
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        # Replace [[Name]] or [[Name|...]] with [[emojiName]] or [[emojiName|...]]
                        base_name = note_file[len(emoji):].rsplit('.md', 1)[0]
                        pattern = re.compile(rf'\[\[({re.escape(base_name)})(\||\]\])')
                        # Replace only up to max_fixes
                        new_content, n = pattern.subn(lambda m: f'[[{emoji}{base_name}{m.group(2)}', content, count=max_fixes-fixes_done)
                        if n > 0:
                            with open(file_path, 'w', encoding='utf-8') as file:
                                file.write(new_content)
                            fixes_done += n
                # Update the realtime list
                with realtime_container:
                    summary_text.markdown(f"**Total valid links found:** {total_valid_links}\n\n**Total invalid links found:** {total_invalid_links}")
                    if unupdated_links:
                        links_list_text.markdown("### Files with unupdated links (so far):")
                        for note, files in unupdated_links.items():
                            with links_list_text.expander(f"{note}"):
                                correct_note_name = note
                                base_name = note[len(emoji):].rsplit('.md', 1)[0]
                                correct_link = f"[[{emoji}{base_name}]]"
                                for f in files:
                                    st.write(f"{f} has an invalid link to {base_name} that should be {correct_link}")
                    else:
                        links_list_text.empty()
            progress_bar.empty()
            status_text.empty()
            # Final summary (in case nothing found)
            with realtime_container:
                summary_text.markdown(f"**Total valid links found:** {total_valid_links}\n\n**Total invalid links found:** {total_invalid_links}")
                if unupdated_links:
                    links_list_text.markdown("### Files with unupdated links:")
                    for note, files in unupdated_links.items():
                        with links_list_text.expander(f"{note}"):
                            correct_note_name = note
                            base_name = note[len(emoji):].rsplit('.md', 1)[0]
                            correct_link = f"[[{emoji}{base_name}]]"
                            for f in files:
                                st.write(f"{f} has an invalid link to {base_name} that should be {correct_link}")
                else:
                    links_list_text.empty()
                    st.success("No unupdated links found!")
            if fix_links:
                st.success(f"Fixed {fixes_done} invalid links (max {max_fixes})")