import streamlit as st
import os
import re
from dotenv import load_dotenv
import sys

load_dotenv()
DEFAULT_VAULT_PATH = os.getenv('OB_VAULT_PATH', './vault')

st.set_page_config(
    page_title="Codiak",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Sidebar for tool selection (expandable later)
st.sidebar.title("Tools")
tool = st.sidebar.radio("Select a tool:", ["Emoji Tag Renamer", "Find Unupdated Links", "Remove Emoji Links", "Replace Tag", "HTML to Markdown"])

# Show success message if present
if 'success_message' in st.session_state:
    st.success(st.session_state['success_message'])
    del st.session_state['success_message']

if tool == "Emoji Tag Renamer":
    st.title("Obsidian Emoji Tag Renamer")
    st.write("Identify notes with a specific tag that do not start with a specified emoji.")

    vault_path = st.text_input("Obsidian Vault Path", value=DEFAULT_VAULT_PATH)
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
                st.experimental_rerun()
        else:
            st.info("No notes found matching the criteria.")

elif tool == "Find Unupdated Links":
    st.title("Find Unupdated Links to #person Notes")
    st.write("Identify all #person notes that begin with the emoji, and find files that link to them without the emoji in the link.")

    vault_path = st.text_input("Obsidian Vault Path", value=DEFAULT_VAULT_PATH, key="vault_path_links")
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

elif tool == "Remove Emoji Links":
    st.title("Remove Emoji Links")
    st.write("Scan all markdown files for links that start with a specified emoji and optionally remove them.")

    vault_path = st.text_input("Obsidian Vault Path", value=DEFAULT_VAULT_PATH, key="vault_path_remove")
    emoji = st.text_input("Emoji to look for at start of links", value="🧍", key="emoji_remove")
    ignore_string = st.text_input("Ignore files containing this string in filename", value="template", key="ignore_remove")
    remove_links = st.checkbox("Remove emoji-prefixed links", value=False)
    max_process = st.number_input("Max number of links to process", min_value=1, value=5, step=1)
    search_btn = st.button("Search for emoji-prefixed links")

    if search_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
        else:
            # Initialize counters and storage
            total_files = 0
            files_with_emoji_links = {}
            links_processed = 0

            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # First pass: count total files
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if file.endswith(".md") and not (ignore_string and ignore_string in file):
                        total_files += 1

            # Second pass: scan files
            current_file = 0
            for root, _, files in os.walk(vault_path):
                for file in files:
                    if ignore_string and ignore_string in file:
                        continue
                    if file.endswith(".md"):
                        current_file += 1
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, vault_path)

                        # Update progress
                        progress = current_file / total_files if total_files else 1
                        progress_bar.progress(progress)
                        status_text.write(f"Scanning {current_file} of {total_files}: {rel_path}")

                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Find all wiki-style links
                        pattern = re.compile(r'\[\[([^\]]+)\]\]')
                        matches = list(pattern.finditer(content))

                        emoji_links = []
                        for match in matches:
                            link_text = match.group(1)
                            if link_text.startswith(emoji):
                                if links_processed < max_process:
                                    emoji_links.append((match.start(), match.end(), link_text))
                                    links_processed += 1
                                if links_processed >= max_process:
                                    break

                        if emoji_links:
                            files_with_emoji_links[rel_path] = emoji_links

                            # If removal is enabled
                            if remove_links:
                                # Sort matches in reverse order to maintain correct indices
                                emoji_links_sorted = sorted(emoji_links, reverse=True)
                                new_content = content
                                for start, end, link_text in emoji_links_sorted:
                                    # Remove the emoji from the link
                                    new_link = f"[[{link_text[len(emoji):]}]]"
                                    new_content = new_content[:start] + new_link + new_content[end:]
                                # Write changes if any were made
                                if new_content != content:
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(new_content)
                        if links_processed >= max_process:
                            break
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Display results
            if files_with_emoji_links:
                st.write(f"Found {len(files_with_emoji_links)} files containing emoji-prefixed links")
                if remove_links:
                    st.success(f"Processed {links_processed} links (max {max_process})")
                for file_path, links in files_with_emoji_links.items():
                    with st.expander(f"{file_path} ({len(links)} links)"):
                        for _, _, link_text in links:
                            st.write(f"`{link_text}`")
            else:
                st.info("No emoji-prefixed links found in any files.")

elif tool == "Replace Tag":
    st.title("Replace Tag in Notes")
    st.write("Scan all markdown files and replace a specified tag with another.")

    vault_path = st.text_input("Obsidian Vault Path", value=DEFAULT_VAULT_PATH, key="vault_path_replace_tag")
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

elif tool == "HTML to Markdown":
    st.title("HTML to Markdown Converter (Rich Paste Supported)")
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