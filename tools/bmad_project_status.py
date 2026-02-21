import os
import yaml
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import date, datetime


def json_serialize(obj: Any) -> Any:
    """Convert non-serializable objects to JSON-serializable format."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: json_serialize(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [json_serialize(item) for item in obj]
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


def find_bmad_files(project_path: str) -> Dict[str, Any]:
    """Find and locate key BMAD project files."""
    project_path = Path(project_path)
    bmad_info = {
        "project_path": str(project_path),
        "config_file": None,
        "status_file": None,
        "sprint_status_file": None,
        "output_folder": None,
        "bmad_folder": None,
        "errors": []
    }

    # Check if path exists
    if not project_path.exists():
        bmad_info["errors"].append(f"Project path does not exist: {project_path}")
        return bmad_info

    # Look for .bmad or bmad folder (try both)
    bmad_folder = None
    for folder_name in [".bmad", "bmad"]:
        test_folder = project_path / folder_name
        if test_folder.exists():
            bmad_folder = test_folder
            bmad_info["bmad_folder"] = str(bmad_folder)
            break

    if bmad_folder:
        # Look for config.yaml
        config_file = bmad_folder / "bmm" / "config.yaml"
        if config_file.exists():
            bmad_info["config_file"] = str(config_file)

            # Read config to find output_folder
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if config and isinstance(config, dict):
                        output_folder = config.get("output_folder", "")
                        if output_folder:
                            # Resolve relative paths
                            if not os.path.isabs(output_folder):
                                output_folder = str(project_path / output_folder)
                            bmad_info["output_folder"] = output_folder

                            # Look for status file in output folder
                            status_file = Path(output_folder) / "bmm-workflow-status.yaml"
                            if status_file.exists():
                                bmad_info["status_file"] = str(status_file)
            except Exception as e:
                bmad_info["errors"].append(f"Error reading config file: {str(e)}")

        # Also try to find status file in common locations
        if not bmad_info["status_file"]:
            common_locations = [
                project_path / "bmm-workflow-status.yaml",
                project_path / "output" / "bmm-workflow-status.yaml",
                project_path / "docs" / "bmm-workflow-status.yaml",
            ]

            for location in common_locations:
                if location.exists():
                    bmad_info["status_file"] = str(location)
                    if not bmad_info["output_folder"]:
                        bmad_info["output_folder"] = str(location.parent)
                    break

    # Look for sprint-status.yaml in docs folder
    sprint_status_file = project_path / "docs" / "sprint-status.yaml"
    if sprint_status_file.exists():
        bmad_info["sprint_status_file"] = str(sprint_status_file)

    # Also check other common locations for sprint status
    if not bmad_info["sprint_status_file"]:
        sprint_locations = [
            project_path / "sprint-status.yaml",
            project_path / "output" / "sprint-status.yaml",
        ]
        for location in sprint_locations:
            if location.exists():
                bmad_info["sprint_status_file"] = str(location)
                break

    if not bmad_folder:
        bmad_info["errors"].append("No .bmad or bmad folder found. This may not be a BMAD project.")

    return bmad_info


def read_status_file(status_file_path: str) -> Optional[Dict[str, Any]]:
    """Read and parse the bmm-workflow-status.yaml file."""
    try:
        with open(status_file_path, 'r', encoding='utf-8') as f:
            status_data = yaml.safe_load(f)
            # Validate that we got a dictionary
            if status_data is None:
                return {}
            if not isinstance(status_data, dict):
                st.warning(f"Status file does not contain a dictionary. Got type: {type(status_data).__name__}")
                return None
            return status_data
    except yaml.YAMLError as e:
        st.error(f"Error parsing YAML file: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error reading status file: {str(e)}")
        return None


def summarize_status(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key insights from the status data."""
    # Validate input
    if not isinstance(status_data, dict):
        return {
            "project_name": "Unknown",
            "current_phase": "Unknown",
            "active_workflows": [],
            "completed_workflows": [],
            "pending_workflows": [],
            "epics": [],
            "stories": [],
            "key_metrics": {},
            "recent_updates": [],
            "next_actions": []
        }

    summary = {
        "project_name": status_data.get("project", {}).get("name", "Unknown") if isinstance(status_data.get("project"), dict) else "Unknown",
        "current_phase": status_data.get("workflow", {}).get("current_phase", "Unknown") if isinstance(status_data.get("workflow"), dict) else "Unknown",
        "active_workflows": [],
        "completed_workflows": [],
        "pending_workflows": [],
        "epics": [],
        "stories": [],
        "key_metrics": {},
        "recent_updates": [],
        "next_actions": []
    }

    # Extract workflow information
    workflows = status_data.get("workflows", {})
    for workflow_name, workflow_info in workflows.items():
        if isinstance(workflow_info, dict):
            status = workflow_info.get("status", "unknown")
            if status == "active":
                summary["active_workflows"].append({
                    "name": workflow_name,
                    "info": workflow_info
                })
            elif status == "completed":
                summary["completed_workflows"].append({
                    "name": workflow_name,
                    "info": workflow_info
                })
            else:
                summary["pending_workflows"].append({
                    "name": workflow_name,
                    "info": workflow_info
                })

    # Extract epic and story information
    epics = status_data.get("epics", {})
    for epic_name, epic_info in epics.items():
        if isinstance(epic_info, dict):
            summary["epics"].append({
                "name": epic_name,
                "status": epic_info.get("status", "unknown"),
                "stories": epic_info.get("stories", [])
            })

    stories = status_data.get("stories", {})
    for story_name, story_info in stories.items():
        if isinstance(story_info, dict):
            summary["stories"].append({
                "name": story_name,
                "status": story_info.get("status", "unknown"),
                "epic": story_info.get("epic", "Unknown")
            })

    # Extract metrics
    metrics = status_data.get("metrics", {})
    if metrics:
        summary["key_metrics"] = metrics

    # Extract recent updates or notes
    updates = status_data.get("updates", [])
    if updates:
        summary["recent_updates"] = updates[-5:]  # Last 5 updates

    # Extract next actions
    next_actions = status_data.get("next_actions", [])
    if next_actions:
        summary["next_actions"] = next_actions

    return summary


def summarize_sprint_status(sprint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key insights from the sprint status data."""
    # Validate input
    if not isinstance(sprint_data, dict):
        return {
            "sprint_name": "Unknown",
            "sprint_dates": "Unknown",
            "sprint_goals": [],
            "completed_stories": [],
            "in_progress_stories": [],
            "blocked_stories": [],
            "metrics": {},
            "notes": []
        }

    # Try to get sprint info from various possible structures
    sprint_name = "Unknown"
    sprint_dates = "Unknown"

    # Check for traditional sprint structure
    if "sprint" in sprint_data and isinstance(sprint_data.get("sprint"), dict):
        sprint_name = sprint_data["sprint"].get("name", sprint_data.get("project", "Unknown"))
        sprint_dates = sprint_data["sprint"].get("dates", "Unknown")
    elif "name" in sprint_data:
        sprint_name = sprint_data.get("name", "Unknown")
        sprint_dates = sprint_data.get("dates", "Unknown")
    elif "project" in sprint_data:
        sprint_name = sprint_data.get("project", "Unknown")
        if "generated" in sprint_data:
            generated = sprint_data.get("generated", "")
            if isinstance(generated, (date, datetime)):
                sprint_dates = generated.isoformat()
            else:
                sprint_dates = str(generated)

    summary = {
        "sprint_name": sprint_name,
        "sprint_dates": sprint_dates,
        "sprint_goals": sprint_data.get("sprint", {}).get("goals", []) if isinstance(sprint_data.get("sprint"), dict) else sprint_data.get("goals", []),
        "completed_stories": [],
        "in_progress_stories": [],
        "blocked_stories": [],
        "metrics": sprint_data.get("metrics", {}),
        "notes": sprint_data.get("notes", [])
    }

    # Extract story information from traditional structure
    stories = sprint_data.get("stories", {})
    if isinstance(stories, dict):
        for story_name, story_info in stories.items():
            if isinstance(story_info, dict):
                status = story_info.get("status", "unknown").lower()
                story_entry = {
                    "name": story_name,
                    "info": story_info
                }
                if status in ["completed", "done"]:
                    summary["completed_stories"].append(story_entry)
                elif status in ["blocked", "block"]:
                    summary["blocked_stories"].append(story_entry)
                else:
                    summary["in_progress_stories"].append(story_entry)

    # Extract story information from development_status structure (alternative format)
    development_status = sprint_data.get("development_status", {})
    if isinstance(development_status, dict) and not stories:
        for story_id, status in development_status.items():
            if story_id.startswith("epic-") or story_id.endswith("-retrospective"):
                # Skip epic entries and retrospectives
                continue

            status_lower = str(status).lower() if status else "unknown"
            story_entry = {
                "name": story_id,
                "info": {
                    "status": status,
                    "description": ""
                }
            }

            if status_lower in ["completed", "done"]:
                summary["completed_stories"].append(story_entry)
            elif status_lower in ["blocked", "block"]:
                summary["blocked_stories"].append(story_entry)
            elif status_lower in ["in-progress", "in_progress", "review", "contexted"]:
                summary["in_progress_stories"].append(story_entry)
            elif status_lower == "backlog":
                # Backlog items could be considered pending, but let's show them separately
                # For now, we'll add them to in_progress to show them in the table
                summary["in_progress_stories"].append(story_entry)
            else:
                summary["in_progress_stories"].append(story_entry)

    return summary


def create_sprint_table(sprint_summary: Dict[str, Any]) -> pd.DataFrame:
    """Create a pandas DataFrame table from sprint summary data."""
    table_data = []

    # Add all stories in one table
    all_stories = []

    # Add completed stories
    completed = sprint_summary.get("completed_stories", [])
    for story in completed:
        story_info = story.get("info", {})
        status_text = story_info.get("status", "done")
        # Map status to emoji
        if status_text.lower() in ["done", "completed"]:
            status_display = "✅ Done"
        else:
            status_display = f"✅ {status_text.title()}"

        all_stories.append({
            "Story": story.get("name", ""),
            "Status": status_display,
            "Description": story_info.get("description", story_info.get("notes", "")),
            "Epic": story_info.get("epic", ""),
            "Assignee": story_info.get("assignee", "")
        })

    # Add in-progress stories
    in_progress = sprint_summary.get("in_progress_stories", [])
    for story in in_progress:
        story_info = story.get("info", {})
        status_text = story_info.get("status", "in-progress")
        status_lower = str(status_text).lower()

        # Map status to emoji
        if status_lower in ["in-progress", "in_progress"]:
            status_display = "🔄 In Progress"
        elif status_lower == "review":
            status_display = "👀 Review"
        elif status_lower == "backlog":
            status_display = "📋 Backlog"
        elif status_lower == "contexted":
            status_display = "📝 Contexted"
        else:
            status_display = f"🔄 {status_text.title()}"

        all_stories.append({
            "Story": story.get("name", ""),
            "Status": status_display,
            "Description": story_info.get("description", story_info.get("notes", "")),
            "Epic": story_info.get("epic", ""),
            "Assignee": story_info.get("assignee", "")
        })

    # Add blocked stories
    blocked = sprint_summary.get("blocked_stories", [])
    for story in blocked:
        story_info = story.get("info", {})
        all_stories.append({
            "Story": story.get("name", ""),
            "Status": "🚫 Blocked",
            "Description": story_info.get("description", story_info.get("notes", "")),
            "Epic": story_info.get("epic", ""),
            "Assignee": story_info.get("assignee", "")
        })

    if all_stories:
        return pd.DataFrame(all_stories)
    else:
        # If no stories, return empty DataFrame
        return pd.DataFrame(columns=["Story", "Status", "Description", "Epic", "Assignee"])


def format_sprint_summary(summary: Dict[str, Any]) -> str:
    """Format the sprint status summary as a readable text."""
    lines = []

    lines.append(f"## Sprint: {summary['sprint_name']}")
    if summary['sprint_dates'] != "Unknown":
        lines.append(f"**Dates:** {summary['sprint_dates']}")
    lines.append("")

    # Goals
    if summary['sprint_goals']:
        lines.append("### Sprint Goals:")
        for goal in summary['sprint_goals']:
            lines.append(f"- {goal}")
        lines.append("")

    # Stories by status
    if summary['completed_stories']:
        lines.append(f"### Completed Stories ({len(summary['completed_stories'])}):")
        for story in summary['completed_stories']:
            lines.append(f"✅ {story['name']}")
        lines.append("")

    if summary['in_progress_stories']:
        lines.append(f"### In Progress Stories ({len(summary['in_progress_stories'])}):")
        for story in summary['in_progress_stories']:
            lines.append(f"🔄 {story['name']}")
        lines.append("")

    if summary['blocked_stories']:
        lines.append(f"### Blocked Stories ({len(summary['blocked_stories'])}):")
        for story in summary['blocked_stories']:
            lines.append(f"🚫 {story['name']}")
        lines.append("")

    # Metrics
    if summary['metrics']:
        lines.append("### Sprint Metrics:")
        for key, value in summary['metrics'].items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    # Notes
    if summary['notes']:
        lines.append("### Notes:")
        for note in summary['notes']:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


def format_status_summary(summary: Dict[str, Any]) -> str:
    """Format the status summary as a readable text."""
    lines = []

    lines.append(f"## Project: {summary['project_name']}")
    lines.append(f"**Current Phase:** {summary['current_phase']}")
    lines.append("")

    # Workflows
    if summary['active_workflows']:
        lines.append("### Active Workflows:")
        for wf in summary['active_workflows']:
            lines.append(f"- {wf['name']}")
    lines.append("")

    if summary['completed_workflows']:
        lines.append(f"### Completed Workflows ({len(summary['completed_workflows'])}):")
        for wf in summary['completed_workflows']:
            lines.append(f"- {wf['name']}")
        lines.append("")

    # Epics and Stories
    if summary['epics']:
        lines.append(f"### Epics ({len(summary['epics'])}):")
        for epic in summary['epics']:
            status_emoji = "✅" if epic['status'] == "completed" else "🔄" if epic['status'] == "active" else "⏳"
            lines.append(f"{status_emoji} {epic['name']} ({epic['status']})")
        lines.append("")

    if summary['stories']:
        active_stories = [s for s in summary['stories'] if s['status'] == 'active']
        if active_stories:
            lines.append(f"### Active Stories ({len(active_stories)}):")
            for story in active_stories:
                lines.append(f"- {story['name']} (Epic: {story['epic']})")
            lines.append("")

    # Next Actions
    if summary['next_actions']:
        lines.append("### Next Actions:")
        for action in summary['next_actions']:
            lines.append(f"- {action}")
        lines.append("")

    # Metrics
    if summary['key_metrics']:
        lines.append("### Key Metrics:")
        for key, value in summary['key_metrics'].items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    return "\n".join(lines)


def render():
    """Render the BMAD Project Status Analyzer UI."""
    st.write("Enter the folder path of a local BMAD project to analyze its status and get key insights.")

    # Initialize session state
    if 'bmad_analysis' not in st.session_state:
        st.session_state.bmad_analysis = None
    if 'bmad_project_path' not in st.session_state:
        st.session_state.bmad_project_path = ""

    # Input section
    st.subheader("📁 Project Path")
    project_path = st.text_input(
        "BMAD Project Folder Path",
        value=st.session_state.bmad_project_path,
        placeholder="e.g., C:\\Users\\live\\dev\\my-bmad-project"
    )

    analyze_btn = st.button("🔍 Analyze Project", type="primary")

    if analyze_btn:
        if not project_path:
            st.error("Please enter a project folder path.")
        else:
            st.session_state.bmad_project_path = project_path
            with st.spinner("Analyzing BMAD project..."):
                # Find BMAD files
                bmad_info = find_bmad_files(project_path)

                if bmad_info["errors"]:
                    for error in bmad_info["errors"]:
                        st.warning(error)

                # Read status file if found
                status_data = None
                if bmad_info["status_file"]:
                    status_data = read_status_file(bmad_info["status_file"])

                # Read sprint status file if found
                sprint_status_data = None
                if bmad_info["sprint_status_file"]:
                    sprint_status_data = read_status_file(bmad_info["sprint_status_file"])

                # Store analysis results
                st.session_state.bmad_analysis = {
                    "bmad_info": bmad_info,
                    "status_data": status_data,
                    "sprint_status_data": sprint_status_data
                }

    # Display results
    if st.session_state.bmad_analysis:
        analysis = st.session_state.bmad_analysis
        bmad_info = analysis["bmad_info"]
        status_data = analysis.get("status_data")
        sprint_status_data = analysis.get("sprint_status_data")

        # Project Status Summary - At the top, expandable
        if status_data and isinstance(status_data, dict):
            with st.expander("📊 Project Status Summary", expanded=True):
                # Create summary
                summary = summarize_status(status_data)

                # Display formatted summary
                st.markdown(format_status_summary(summary))

                # Download option
                st.subheader("💾 Export")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 Download Status JSON",
                        data=json.dumps(json_serialize(status_data), indent=2),
                        file_name="bmm-workflow-status.json",
                        mime="application/json"
                    )
                with col2:
                    st.download_button(
                        label="📝 Download Summary",
                        data=format_status_summary(summary),
                        file_name="bmm-project-summary.md",
                        mime="text/markdown"
                    )

                # Detailed view as collapsible section (not nested expander)
                st.subheader("📋 Detailed Status Data")
                st.json(status_data)
        elif bmad_info["status_file"]:
            if status_data is not None:
                st.error(f"Status file exists but contains invalid data (expected dict, got {type(status_data).__name__}). Check the file format.")
            else:
                st.error("Could not read status file. Check the file format.")
        else:
            st.info("No status file found. This project may need to be initialized with the workflow-init workflow.")

        # Sprint Status Summary - Display as table
        if sprint_status_data and isinstance(sprint_status_data, dict):
            st.subheader("🏃 Sprint Status")

            # Create sprint summary
            sprint_summary = summarize_sprint_status(sprint_status_data)

            # Display sprint header info
            sprint_name = sprint_summary.get("sprint_name", "Unknown")
            sprint_dates = sprint_summary.get("sprint_dates", "Unknown")
            sprint_goals = sprint_summary.get("sprint_goals", [])

            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Sprint:** {sprint_name}")
                if sprint_dates != "Unknown":
                    st.write(f"**Dates:** {sprint_dates}")
            with col2:
                if sprint_goals:
                    with st.expander("Sprint Goals", expanded=False):
                        for goal in sprint_goals:
                            st.write(f"• {goal}")

            # Create and display table
            sprint_df = create_sprint_table(sprint_summary)
            if not sprint_df.empty:
                st.dataframe(sprint_df, use_container_width=True, hide_index=True)

            # Detailed view and export in expander
            with st.expander("📋 Sprint Details & Export", expanded=False):
                st.markdown(format_sprint_summary(sprint_summary))

                # Detailed data section (not nested expander)
                st.subheader("📋 Detailed Sprint Status Data")
                st.json(sprint_status_data)

                # Download option for sprint status
                st.subheader("💾 Sprint Export")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 Download Sprint Status JSON",
                        data=json.dumps(json_serialize(sprint_status_data), indent=2),
                        file_name="sprint-status.json",
                        mime="application/json"
                    )
                with col2:
                    st.download_button(
                        label="📝 Download Sprint Summary",
                        data=format_sprint_summary(sprint_summary),
                        file_name="sprint-summary.md",
                        mime="text/markdown"
                    )
        elif bmad_info["sprint_status_file"]:
            if sprint_status_data is not None:
                st.error(f"Sprint status file exists but contains invalid data (expected dict, got {type(sprint_status_data).__name__}). Check the file format.")
            else:
                st.error("Could not read sprint status file. Check the file format.")

        # Project Structure - At the bottom, minimized
        with st.expander("📂 Project Structure", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Project Path:**")
                st.code(bmad_info["project_path"], language="text")

                if bmad_info["bmad_folder"]:
                    st.success(f"✅ BMAD folder found: {bmad_info['bmad_folder']}")
                else:
                    st.warning("⚠️ BMAD folder not found")

            with col2:
                if bmad_info["config_file"]:
                    st.write(f"**Config File:**")
                    st.code(bmad_info["config_file"], language="text")

                if bmad_info["output_folder"]:
                    st.write(f"**Output Folder:**")
                    st.code(bmad_info["output_folder"], language="text")

            # Status File Information
            col1, col2 = st.columns(2)
            with col1:
                if bmad_info["status_file"]:
                    st.success(f"✅ Workflow status file found: {bmad_info['status_file']}")
                else:
                    st.warning("⚠️ Workflow status file (bmm-workflow-status.yaml) not found")

            with col2:
                if bmad_info["sprint_status_file"]:
                    st.success(f"✅ Sprint status file found: {bmad_info['sprint_status_file']}")
                else:
                    st.info("ℹ️ Sprint status file (docs/sprint-status.yaml) not found")

            # Show raw file info (as a section, not nested expander)
            st.subheader("🔧 Debug Information")
            st.json(bmad_info)

