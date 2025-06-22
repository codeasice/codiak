import streamlit as st
import os
import re

def render(vault_path_default):
    st.warning("This tool will modify your notes. Make sure you have a backup.")
    st.write("Scan all markdown files for links that start with a specified emoji and optionally remove them.")

    vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default, key="vault_path_remove")
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