"""
Pure business logic for the BMAD Project Status tool.
No Streamlit imports — callable from FastAPI or any other context.
"""
import os
import re
import yaml
import json
from typing import Any, Optional
from pathlib import Path
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_serialize(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _json_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_serialize(i) for i in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _read_yaml(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_bmad_files(project_path: str) -> dict:
    p = Path(project_path)
    info = {
        "project_path": str(p),
        "config_file": None,
        "status_file": None,
        "sprint_status_files": [],
        "epics_files": [],
        "output_folder": None,
        "bmad_folder": None,
        "errors": [],
    }

    if not p.exists():
        info["errors"].append(f"Project path does not exist: {project_path}")
        return info

    bmad_folder = None
    for name in (".bmad", "bmad", "_bmad"):
        candidate = p / name
        if candidate.exists():
            bmad_folder = candidate
            info["bmad_folder"] = str(candidate)
            break

    if bmad_folder:
        config_file = bmad_folder / "bmm" / "config.yaml"
        if config_file.exists():
            info["config_file"] = str(config_file)
            try:
                config = _read_yaml(str(config_file))
                if config:
                    output_folder = config.get("output_folder", "")
                    if isinstance(output_folder, str):
                        output_folder = output_folder.replace("{project-root}", str(p))
                    if output_folder:
                        if not os.path.isabs(output_folder):
                            output_folder = str(p / output_folder)
                        info["output_folder"] = output_folder
                        status_file = Path(output_folder) / "planning-artifacts" / "bmm-workflow-status.yaml"
                        if not status_file.exists():
                            status_file = Path(output_folder) / "bmm-workflow-status.yaml"
                        if status_file.exists():
                            info["status_file"] = str(status_file)
            except Exception as e:
                info["errors"].append(f"Error reading config: {str(e)}")

    # Fallback workflow status locations
    if not info["status_file"]:
        for loc in [
            p / "_bmad-output" / "planning-artifacts" / "bmm-workflow-status.yaml",
            p / "bmm-workflow-status.yaml",
            p / "output" / "bmm-workflow-status.yaml",
            p / "docs" / "bmm-workflow-status.yaml",
        ]:
            if loc.exists():
                info["status_file"] = str(loc)
                if not info["output_folder"]:
                    info["output_folder"] = str(loc.parent)
                break

    # Sprint status files — collect all matches
    sprint_candidates = [
        p / "docs" / "sprint-status.yaml",
        p / "sprint-status.yaml",
        p / "output" / "sprint-status.yaml",
        p / "_bmad-output" / "sprint-status.yaml",
        p / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml",
    ]
    for loc in sprint_candidates:
        if loc.exists():
            info["sprint_status_files"].append(str(loc))

    # Epics files — collect all epics*.md from docs/ and _bmad-output/
    epics_search_dirs = [p / "docs", p / "_bmad-output" / "planning-artifacts"]
    for search_dir in epics_search_dirs:
        if search_dir.exists():
            for f in sorted(search_dir.iterdir()):
                if f.is_file() and f.name.startswith("epics") and f.suffix == ".md":
                    info["epics_files"].append(str(f))

    if not bmad_folder:
        info["errors"].append("No .bmad / bmad / _bmad folder found. This may not be a BMAD project.")

    return info


# ---------------------------------------------------------------------------
# Sprint status — parse development_status into epic groups
# ---------------------------------------------------------------------------

def parse_sprint_epics(sprint_data: dict) -> dict:
    """
    Parse a sprint-status.yaml into structured epic groups.

    Returns:
        {
            "project": str,
            "generated": str,
            "epics": [
                {
                    "id": "epic-1",
                    "num": 1,
                    "status": "contexted",
                    "retrospective": "done" | "optional" | None,
                    "stories": [{"id": "1-1-slug", "status": "done"}, ...],
                    "counts": {"done": N, "in-progress": N, ...}
                }
            ],
            "totals": {"done": N, "in-progress": N, ...}
        }
    """
    if not isinstance(sprint_data, dict):
        return {"project": "Unknown", "generated": "", "epics": [], "totals": {}}

    project = sprint_data.get("project", "Unknown")
    generated = sprint_data.get("generated", "")
    if isinstance(generated, (date, datetime)):
        generated = generated.isoformat()

    dev_status = sprint_data.get("development_status", {})
    if not isinstance(dev_status, dict):
        return {"project": project, "generated": str(generated), "epics": [], "totals": {}}

    # Group entries by epic
    epic_map: dict[str, dict] = {}  # epic_id -> {status, stories, retrospective}
    epic_order: list[str] = []

    for key, val in dev_status.items():
        status = str(val) if val is not None else "unknown"

        # Epic header: epic-N
        m = re.match(r'^(epic-\d+)$', key)
        if m:
            eid = m.group(1)
            if eid not in epic_map:
                epic_map[eid] = {"status": status, "stories": [], "retrospective": None}
                epic_order.append(eid)
            else:
                epic_map[eid]["status"] = status
            continue

        # Retrospective: epic-N-retrospective
        m = re.match(r'^(epic-\d+)-retrospective$', key)
        if m:
            eid = m.group(1)
            if eid not in epic_map:
                epic_map[eid] = {"status": "unknown", "stories": [], "retrospective": status}
                epic_order.append(eid)
            else:
                epic_map[eid]["retrospective"] = status
            continue

        # Story: N-M-slug (starts with digit)
        if re.match(r'^\d', key):
            # Determine parent epic from story prefix (e.g. "11-8-foo" -> "epic-11")
            epic_num = key.split("-")[0]
            eid = f"epic-{epic_num}"
            if eid not in epic_map:
                epic_map[eid] = {"status": "unknown", "stories": [], "retrospective": None}
                epic_order.append(eid)
            epic_map[eid]["stories"].append({"id": key, "status": status})

    # Build sorted epic list + compute counts
    STATUS_ORDER = ["done", "in-progress", "review", "ready-for-dev", "drafted", "in_progress",
                    "contexted", "backlog", "unknown", "optional", "completed"]

    def _sort_key(eid: str) -> int:
        m = re.match(r'epic-(\d+)', eid)
        return int(m.group(1)) if m else 9999

    totals: dict[str, int] = {}
    epics_out = []
    for eid in sorted(set(epic_order), key=_sort_key):
        ep = epic_map[eid]
        counts: dict[str, int] = {}
        for s in ep["stories"]:
            sl = s["status"].lower()
            counts[sl] = counts.get(sl, 0) + 1
            totals[sl] = totals.get(sl, 0) + 1
        m = re.match(r'epic-(\d+)', eid)
        epics_out.append({
            "id": eid,
            "num": int(m.group(1)) if m else 0,
            "status": ep["status"],
            "retrospective": ep["retrospective"],
            "stories": ep["stories"],
            "counts": counts,
        })

    return {
        "project": project,
        "generated": str(generated),
        "epics": epics_out,
        "totals": totals,
    }


# ---------------------------------------------------------------------------
# Epics.md — extract headings only (file can be very large)
# ---------------------------------------------------------------------------

def parse_epics_headings(epics_path: str) -> list[dict]:
    """
    Read epics.md and extract ## Epic N: Title headings with story counts.
    Returns list of {num, title, story_count}.
    Reads file line-by-line to avoid loading everything into memory.
    """
    results = []
    current_epic = None
    story_count = 0

    try:
        with open(epics_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                # H2 epic heading: ## Epic N: Title  or  ## Epic N - Title
                m = re.match(r'^##\s+Epic\s+(\d+)[:\-\s]+(.+)', line)
                if m:
                    if current_epic is not None:
                        results.append({**current_epic, "story_count": story_count})
                    current_epic = {"num": int(m.group(1)), "title": m.group(2).strip()}
                    story_count = 0
                    continue
                # Count story headings: ### Story N.M or ### N.M
                if current_epic and re.match(r'^###\s+', line):
                    story_count += 1
        if current_epic is not None:
            results.append({**current_epic, "story_count": story_count})
    except Exception:
        pass

    return results


# ---------------------------------------------------------------------------
# Workflow status summary (bmm-workflow-status.yaml)
# ---------------------------------------------------------------------------

def summarize_status(status_data: dict) -> dict:
    if not isinstance(status_data, dict):
        return {
            "project_name": "Unknown", "current_phase": "Unknown",
            "active_workflows": [], "completed_workflows": [], "pending_workflows": [],
            "key_metrics": {}, "next_actions": [],
        }

    project = status_data.get("project", {})
    workflow_meta = status_data.get("workflow", {})

    summary = {
        "project_name": project.get("name", "Unknown") if isinstance(project, dict) else "Unknown",
        "current_phase": workflow_meta.get("current_phase", "Unknown") if isinstance(workflow_meta, dict) else "Unknown",
        "active_workflows": [],
        "completed_workflows": [],
        "pending_workflows": [],
        "key_metrics": {},
        "next_actions": [],
    }

    for wf_name, wf_info in status_data.get("workflows", {}).items():
        if isinstance(wf_info, dict):
            status = wf_info.get("status", "unknown")
            entry = {"name": wf_name, "info": wf_info}
            if status == "active":
                summary["active_workflows"].append(entry)
            elif status == "completed":
                summary["completed_workflows"].append(entry)
            else:
                summary["pending_workflows"].append(entry)

    summary["key_metrics"] = status_data.get("metrics", {}) or {}
    summary["next_actions"] = status_data.get("next_actions", []) or []

    return summary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_bmad_project(project_path: str) -> dict:
    """Analyze a BMAD project folder and return structured status data."""
    info = find_bmad_files(project_path)

    # Workflow status (bmm-workflow-status.yaml)
    status_data = None
    status_summary = None
    if info["status_file"]:
        status_data = _read_yaml(info["status_file"])
        if isinstance(status_data, dict):
            status_data = _json_serialize(status_data)
            status_summary = summarize_status(status_data)

    # Sprint status files
    sprint_files = []
    for path in info["sprint_status_files"]:
        data = _read_yaml(path)
        if isinstance(data, dict):
            data = _json_serialize(data)
            sprint_files.append({
                "path": path,
                "filename": os.path.basename(path),
                "data": data,
                "epics": parse_sprint_epics(data),
            })

    # Epics files — headings only
    epics_files = []
    for path in info["epics_files"]:
        headings = parse_epics_headings(path)
        epics_files.append({
            "path": path,
            "filename": os.path.basename(path),
            "epics": headings,
        })

    return {
        "bmad_info": info,
        "status_data": status_data,
        "status_summary": status_summary,
        "sprint_files": sprint_files,
        "epics_files": epics_files,
    }
