import streamlit as st
import os
import re
from datetime import datetime, timedelta, date

# Helper: get all dates between two dates (inclusive)
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

# Helper: get all (year, week) tuples between two dates (inclusive)
def weekrange(start_date, end_date):
    weeks = set()
    for d in daterange(start_date, end_date):
        iso = d.isocalendar()
        weeks.add((iso[0], iso[1]))
    return sorted(list(weeks))

# Helper: find notes by date or week prefix
def find_notes_in_range(vault_path, date_prefixes, week_prefixes):
    notes = []
    for root, _, files in os.walk(vault_path):
        for file in files:
            if not file.endswith('.md'):
                continue
            title = os.path.splitext(file)[0]
            if any(title.startswith(p) for p in date_prefixes) or any(title.startswith(w) for w in week_prefixes):
                notes.append({
                    'title': title,
                    'full_path': os.path.join(root, file),
                    'rel_path': os.path.relpath(os.path.join(root, file), vault_path)
                })
    return notes

# Helper: find completed tasks in notes within range
def find_completed_tasks(notes, start_date, end_date):
    completed = []
    date_re = re.compile(r'- \[x\].*?✅ (\d{4}-\d{2}-\d{2})')
    for note in notes:
        # DEBUG: Show note rel_path
        print(f"DEBUG: find_completed_tasks note rel_path: {note.get('rel_path', '')}")
        try:
            with open(note['full_path'], 'r', encoding='utf-8') as f:
                for line in f:
                    m = date_re.search(line)
                    if m:
                        task_date = datetime.strptime(m.group(1), '%Y-%m-%d').date()
                        if start_date <= task_date <= end_date:
                            completed.append({
                                'task': line.strip(),
                                'note': note['title'],
                                'rel_path': note['rel_path'],
                                'date': task_date
                            })
        except Exception as e:
            continue
    return completed

def render(vault_path_default):
    # Do NOT include st.header or st.write for the tool title/description here!
    vault_path = st.text_input('Obsidian Vault Path', value=vault_path_default, key='vault_path_changes_in_range')
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input('Start Date', value=date.today() - timedelta(days=7), key='start_date_changes')
    with col2:
        end_date = st.date_input('End Date (optional)', value=date.today(), key='end_date_changes')
    segregate = st.checkbox('Segregate by prefix', value=True, key='segregate_by_prefix')
    prefix = st.text_input('Prefix to segregate by', value='2 Work', key='segregate_prefix')
    if start_date > end_date:
        st.error('Start date must be before end date.')
        return
    search_btn = st.button('Find Notes & Tasks')
    if search_btn:
        if not os.path.isdir(vault_path):
            st.error(f"Vault path '{vault_path}' does not exist.")
            return
        # Prepare prefixes
        date_prefixes = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_date - start_date).days + 1)]
        week_tuples = weekrange(start_date, end_date)
        week_prefixes = [f"{y}-{str(w).zfill(2)}" for y, w in week_tuples]
        notes = find_notes_in_range(vault_path, date_prefixes, week_prefixes)
        st.session_state['changes_in_range_notes'] = notes
        st.session_state['changes_in_range_selected'] = set()
        st.session_state['changes_in_range_start'] = start_date
        st.session_state['changes_in_range_end'] = end_date
        # Find completed tasks in all notes in vault (could optimize to just notes in range)
        all_notes = []
        for root, _, files in os.walk(vault_path):
            for file in files:
                if file.endswith('.md'):
                    rel_path = os.path.relpath(os.path.join(root, file), vault_path)
                    # DEBUG: Show rel_path for each note
                    print(f"DEBUG: all_notes rel_path: {rel_path}")
                    all_notes.append({'title': os.path.splitext(file)[0], 'full_path': os.path.join(root, file), 'rel_path': rel_path})
        completed = find_completed_tasks(all_notes, start_date, end_date)
        st.session_state['changes_in_range_tasks'] = completed
    notes = st.session_state.get('changes_in_range_notes', [])
    selected = st.session_state.get('changes_in_range_selected', set())
    tasks = st.session_state.get('changes_in_range_tasks', [])
    # Sort notes by title
    notes = sorted(notes, key=lambda n: n['title'].lower())
    tab_notes, tab_tasks = st.tabs(["Notes", "Tasks"])
    with tab_notes:
        if notes:
            if segregate:
                work_notes = [n for n in notes if n['rel_path'].startswith(prefix)]
                nonwork_notes = [n for n in notes if not n['rel_path'].startswith(prefix)]
                st.write(f"### Work Notes ({len(work_notes)})")
                for note in work_notes:
                    checked = st.checkbox(note['title'], key=f"note_work_{note['rel_path']}", value=note['rel_path'] in selected)
                    if checked:
                        selected.add(note['rel_path'])
                    else:
                        selected.discard(note['rel_path'])
                st.write(f"### Non-Work Notes ({len(nonwork_notes)})")
                for note in nonwork_notes:
                    checked = st.checkbox(note['title'], key=f"note_nonwork_{note['rel_path']}", value=note['rel_path'] in selected)
                    if checked:
                        selected.add(note['rel_path'])
                    else:
                        selected.discard(note['rel_path'])
            else:
                st.write(f"### Notes in Range ({len(notes)})")
                for note in notes:
                    checked = st.checkbox(note['title'], key=f"note_{note['rel_path']}", value=note['rel_path'] in selected)
                    if checked:
                        selected.add(note['rel_path'])
                    else:
                        selected.discard(note['rel_path'])
            st.session_state['changes_in_range_selected'] = selected
            if st.button('Compile Selected Notes'):
                compiled = ''
                for note in notes:
                    if note['rel_path'] in selected:
                        try:
                            with open(note['full_path'], 'r', encoding='utf-8') as f:
                                compiled += f"\n---\n# {note['title']}\n" + f.read()
                        except Exception as e:
                            compiled += f"\n---\n# {note['title']}\nERROR reading note: {e}\n"
                st.session_state['changes_in_range_compiled'] = compiled
        compiled = st.session_state.get('changes_in_range_compiled', '')
        if compiled:
            st.write('### Compiled Notes')
            st.text_area('Compiled Notes', value=compiled, height=300)
    with tab_tasks:
        if tasks:
            # Prepare table data
            def parse_task_line(task_line):
                # Remove checkbox and date from '- [x] Task Name ✅ YYYY-MM-DD'
                import re
                m = re.match(r'- \[x\] (.*?)(?: ✅ (\d{4}-\d{2}-\d{2}))?$', task_line)
                if m:
                    return m.group(1)
                return task_line
            if segregate:
                work_tasks = [t for t in tasks if t.get('rel_path', '').startswith(prefix)]
                nonwork_tasks = [t for t in tasks if t not in work_tasks]
                for label, group in [("Work Tasks", work_tasks), ("Non-Work Tasks", nonwork_tasks)]:
                    st.write(f"### {label} ({len(group)})")
                    if group:
                        # Sort by note, then date completed
                        group = sorted(group, key=lambda t: (t['note'].lower(), t['date']))
                        table_data = [{
                            "Task Name": parse_task_line(t['task']),
                            "Date Completed": t['date'].strftime('%Y-%m-%d') if t.get('date') else '',
                            "Note": t['note']
                        } for t in group]
                        st.dataframe(table_data, hide_index=True)
            else:
                st.write(f"### Completed Tasks in Range ({len(tasks)})")
                # Sort by note, then date completed
                tasks = sorted(tasks, key=lambda t: (t['note'].lower(), t['date']))
                table_data = [{
                    "Task Name": parse_task_line(t['task']),
                    "Date Completed": t['date'].strftime('%Y-%m-%d') if t.get('date') else '',
                    "Note": t['note']
                } for t in tasks]
                st.dataframe(table_data, hide_index=True)