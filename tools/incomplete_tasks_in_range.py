import streamlit as st
import os
import re
from datetime import datetime, timedelta, date

# Helper: get all dates between two dates (inclusive) - reused from changes_in_range.py
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

# Helper: find notes by date prefix - reused from changes_in_range.py
def find_notes_in_range(vault_path, date_prefixes):
    notes = []
    for root, _, files in os.walk(vault_path):
        for file in files:
            if not file.endswith('.md'):
                continue
            title = os.path.splitext(file)[0]
            if any(title.startswith(p) for p in date_prefixes):
                notes.append({
                    'title': title,
                    'full_path': os.path.join(root, file),
                    'rel_path': os.path.relpath(os.path.join(root, file), vault_path)
                })
    return notes

# Helper: find notes with sections starting with date prefixes
def find_notes_with_date_sections(vault_path, date_prefixes):
    notes = []
    for root, _, files in os.walk(vault_path):
        for file in files:
            if not file.endswith('.md'):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for sections starting with date prefixes
                    lines = content.split('\n')
                    has_date_section = False
                    for line in lines:
                        line = line.strip()
                        if line.startswith('#'):  # Section header
                            # Remove # symbols and check if it starts with a date prefix
                            header_text = line.lstrip('#').strip()

                            # Check if header starts with a date prefix
                            if any(header_text.startswith(p) for p in date_prefixes):
                                has_date_section = True
                                break

                            # Check if header contains a date prefix within wiki-style links [[YYYY-MM-DD]]
                            import re
                            wiki_links = re.findall(r'\[\[([^\]]+)\]\]', header_text)
                            for link in wiki_links:
                                if any(link.startswith(p) for p in date_prefixes):
                                    has_date_section = True
                                    break
                            if has_date_section:
                                break
                    if has_date_section:
                        notes.append({
                            'title': os.path.splitext(file)[0],
                            'full_path': file_path,
                            'rel_path': os.path.relpath(file_path, vault_path)
                        })
            except Exception as e:
                continue
    return notes

# Helper: find incomplete tasks in notes
def find_incomplete_tasks(notes, start_date, end_date):
    incomplete_tasks = []

    for note in notes:
        try:
            with open(note['full_path'], 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

                current_section = None
                in_relevant_section = False

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()

                    # Check if this is a section header
                    if line.startswith('#'):
                        header_text = line.lstrip('#').strip()
                        current_section = header_text

                        # Check if this section starts with a date in our range
                        in_relevant_section = False
                        for date_prefix in [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                                          for i in range((end_date - start_date).days + 1)]:
                            if header_text.startswith(date_prefix):
                                in_relevant_section = True
                                break

                        # Check if this section contains a date in our range within wiki-style links
                        if not in_relevant_section:
                            import re
                            wiki_links = re.findall(r'\[\[([^\]]+)\]\]', header_text)
                            for link in wiki_links:
                                if any(link.startswith(date_prefix) for date_prefix in [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                                                                                      for i in range((end_date - start_date).days + 1)]):
                                    in_relevant_section = True
                                    break

                    # Look for incomplete tasks (lines starting with "- [ ]")
                    if line.startswith('- [ ]'):
                        # If we're in a relevant section or the note title itself is in range
                        note_title_in_range = any(note['title'].startswith(
                            (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                        ) for i in range((end_date - start_date).days + 1))

                        if in_relevant_section or note_title_in_range:
                            # Extract task text (remove the checkbox)
                            task_text = line[4:].strip()

                            # Strip leading ']' if present
                            if task_text.startswith(']'):
                                task_text = task_text[1:].strip()

                            # Process wiki-style links [[link]] -> _link_
                            import re
                            task_text = re.sub(r'\[\[([^\]]+)\]\]', r'_\1_', task_text)

                            incomplete_tasks.append({
                                'task': task_text,
                                'note': note['title'],
                                'rel_path': note['rel_path'],
                                'section': current_section if in_relevant_section else 'Note Title',
                                'line_number': line_num
                            })

        except Exception as e:
            continue

    return incomplete_tasks

def render(vault_path_default):
    # Do NOT include st.header or st.write for the tool title/description here!
    vault_path = st.text_input('Obsidian Vault Path', value=vault_path_default, key='vault_path_incomplete_tasks')
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input('Start Date', value=date.today() - timedelta(days=7), key='start_date_incomplete_tasks')
    with col2:
        end_date = st.date_input('End Date', value=date.today(), key='end_date_incomplete_tasks')

    segregate = st.checkbox('Segregate by prefix', value=True, key='segregate_by_prefix_incomplete_tasks')
    prefix = st.text_input('Prefix to segregate by', value='2 Work', key='segregate_prefix_incomplete_tasks')

    if start_date > end_date:
        st.error('Start date must be before end date.')
        return

    search_btn = st.button('Find Incomplete Tasks')

    if search_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
            return

        # Prepare date prefixes
        date_prefixes = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                        for i in range((end_date - start_date).days + 1)]

        # Show progress container
        progress_container = st.container()
        with progress_container:
            st.info("🔍 Scanning vault for notes and tasks...")
            progress_bar = st.progress(0)
            status_text = st.empty()

        # Find notes with titles in range
        status_text.text("📝 Finding notes with date-prefixed titles...")
        title_notes = find_notes_in_range(vault_path, date_prefixes)
        progress_bar.progress(25)

        # Find notes with sections in range
        status_text.text("📋 Finding notes with date-prefixed sections...")
        section_notes = find_notes_with_date_sections(vault_path, date_prefixes)
        progress_bar.progress(50)

        # Combine and deduplicate notes
        status_text.text("🔄 Combining and deduplicating notes...")
        all_notes = title_notes + section_notes
        unique_notes = []
        seen_paths = set()
        for note in all_notes:
            if note['rel_path'] not in seen_paths:
                unique_notes.append(note)
                seen_paths.add(note['rel_path'])
        progress_bar.progress(75)

        # Find incomplete tasks
        status_text.text("✅ Scanning notes for incomplete tasks...")
        incomplete_tasks = find_incomplete_tasks(unique_notes, start_date, end_date)
        progress_bar.progress(100)

        # Clear progress indicators
        progress_container.empty()

        # Show summary
        st.success(f"✅ Found {len(unique_notes)} relevant notes and {len(incomplete_tasks)} incomplete tasks")

        st.session_state['incomplete_tasks_notes'] = unique_notes
        st.session_state['incomplete_tasks_tasks'] = incomplete_tasks
        st.session_state['incomplete_tasks_start'] = start_date
        st.session_state['incomplete_tasks_end'] = end_date

    notes = st.session_state.get('incomplete_tasks_notes', [])
    tasks = st.session_state.get('incomplete_tasks_tasks', [])

    # Sort notes by title
    notes = sorted(notes, key=lambda n: n['title'].lower())

    tab_notes, tab_tasks = st.tabs(["Notes", "Incomplete Tasks"])

    with tab_notes:
        if notes:
            if segregate:
                work_notes = [n for n in notes if n['rel_path'].startswith(prefix)]
                nonwork_notes = [n for n in notes if not n['rel_path'].startswith(prefix)]

                st.write(f"### Work Notes ({len(work_notes)})")
                if work_notes:
                    work_table_data = [{
                        "Title": note['title'],
                        "Path": note['rel_path']
                    } for note in work_notes]
                    st.dataframe(work_table_data, hide_index=True)

                st.write(f"### Non-Work Notes ({len(nonwork_notes)})")
                if nonwork_notes:
                    nonwork_table_data = [{
                        "Title": note['title'],
                        "Path": note['rel_path']
                    } for note in nonwork_notes]
                    st.dataframe(nonwork_table_data, hide_index=True)
            else:
                st.write(f"### Notes with Incomplete Tasks ({len(notes)})")
                table_data = [{
                    "Title": note['title'],
                    "Path": note['rel_path']
                } for note in notes]
                st.dataframe(table_data, hide_index=True)

    with tab_tasks:
        if tasks:
            if segregate:
                work_tasks = [t for t in tasks if t.get('rel_path', '').startswith(prefix)]
                nonwork_tasks = [t for t in tasks if t not in work_tasks]

                for label, group in [("Work Incomplete Tasks", work_tasks), ("Non-Work Incomplete Tasks", nonwork_tasks)]:
                    st.write(f"### {label} ({len(group)})")
                    if group:
                        # Sort by note, then section, then line number
                        group = sorted(group, key=lambda t: (t['note'].lower(), t['section'], t['line_number']))
                        table_data = [{
                            "Task": t['task'],
                            "Note": t['note'],
                            "Section": t['section'],
                            "Line": t['line_number']
                        } for t in group]
                        st.dataframe(table_data, hide_index=True)
            else:
                st.write(f"### Incomplete Tasks in Range ({len(tasks)})")
                # Sort by note, then section, then line number
                tasks = sorted(tasks, key=lambda t: (t['note'].lower(), t['section'], t['line_number']))
                table_data = [{
                    "Task": t['task'],
                    "Note": t['note'],
                    "Section": t['section'],
                    "Line": t['line_number']
                } for t in tasks]
                st.dataframe(table_data, hide_index=True)
        else:
            st.info("No incomplete tasks found in the specified date range.")