"""
Match Obsidian sensor notes to Home Assistant motion entities by name normalization.

Reads sensor notes from the vault Sensors folder, fetches live HA motion entities,
normalizes both names, and writes ha_entity_id to sensor notes where a confident
match is found. Prints a table of all matches with HIGH/LOW confidence.

Usage:
    python tools/match_sensors_to_ha.py [--dry-run]
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Bootstrap env and project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import yaml
from api.services.home_assistant_service import get_grouped_entities
from api.services.house_service import SENSORS_FOLDER, _vault_path, _parse_frontmatter, _slugify

DRY_RUN = "--dry-run" in sys.argv


def _normalize(name: str) -> str:
    """Normalize a sensor name to comparable word tokens."""
    # Strip emoji / non-ASCII
    name = re.sub(r'[^\x00-\x7F]+', '', name)
    # Strip leading S-number prefix like "S7 - " or "S12-"
    name = re.sub(r'^[Ss]\d+\s*[-–]\s*', '', name)
    # Strip common HA suffixes
    name = re.sub(r'\s*(motion sensor|motion|sensor)\s*$', '', name, flags=re.IGNORECASE)
    # Lowercase alphanum words
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', name.lower()).split())


def _word_overlap(a: str, b: str) -> float:
    """Jaccard word overlap between two normalized strings."""
    wa, wb = set(a.split()), set(b.split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _update_frontmatter(filepath: Path, key: str, value: str) -> bool:
    """Add key: value to YAML frontmatter if not already present. Returns True if written."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return False
    if not content.startswith("---"):
        return False
    end = content.find("---", 3)
    if end == -1:
        return False
    fm_str = content[3:end]
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        return False
    if fm.get(key):
        return False  # already set
    # Insert before closing ---
    new_fm = fm_str.rstrip() + f"\n{key}: {value}\n"
    filepath.write_text("---" + new_fm + content[end:], encoding="utf-8")
    return True


def main():
    vault = _vault_path()
    if not vault:
        print("OB_VAULT_PATH is not set.")
        sys.exit(1)

    sensors_dir = Path(vault) / SENSORS_FOLDER
    if not sensors_dir.exists():
        print(f"Sensors folder not found: {sensors_dir}")
        sys.exit(1)

    # Fetch HA motion entities
    print("Fetching HA motion entities...")
    try:
        data = get_grouped_entities()
    except Exception as e:
        print(f"Failed to fetch HA entities: {e}")
        sys.exit(1)

    ha_sensors = data.get("motion_sensors", [])
    print(f"Found {len(ha_sensors)} HA motion sensors.\n")

    # Build (normalized_name → entity) map for HA sensors
    ha_by_norm: dict[str, dict] = {}
    for s in ha_sensors:
        norm = _normalize(s.get("friendly_name", s["entity_id"]))
        ha_by_norm[norm] = s

    # Scan sensor notes
    sensor_files = sorted(sensors_dir.glob("*.md"))
    print(f"{'Sensor Note':<38} {'HA Entity':<48} {'Conf':<6} {'Action'}")
    print("-" * 110)

    written = 0
    for f in sensor_files:
        fm = _parse_frontmatter(f)
        if fm is None:
            continue
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if "sensor" not in tags:
            continue

        stem = f.stem
        existing_entity_id = fm.get("ha_entity_id", "")
        norm_stem = _normalize(stem)

        # Find best match
        best_entity = None
        best_score = 0.0
        for norm_ha, entity in ha_by_norm.items():
            score = _word_overlap(norm_stem, norm_ha)
            if score > best_score:
                best_score = score
                best_entity = entity

        confidence = "HIGH" if best_score >= 0.5 else ("LOW" if best_score > 0 else "NONE")

        if existing_entity_id:
            action = f"already set: {existing_entity_id}"
            entity_str = best_entity["entity_id"] if best_entity else "-"
        elif best_entity and confidence in ("HIGH",):
            entity_str = best_entity["entity_id"]
            if DRY_RUN:
                action = "would write (dry-run)"
            else:
                ok = _update_frontmatter(f, "ha_entity_id", entity_str)
                action = "written" if ok else "skipped (already set)"
                if ok:
                    written += 1
        else:
            entity_str = best_entity["entity_id"] if best_entity else "-"
            action = "needs manual review"

        print(f"{stem:<38} {entity_str:<48} {confidence:<6} {action}")

    print()
    if not DRY_RUN:
        print(f"Wrote ha_entity_id to {written} sensor note(s).")
        print("Review LOW/NONE confidence rows and add ha_entity_id manually.")
    else:
        print("Dry-run complete. Run without --dry-run to write changes.")

    # Print HA entities not matched to any sensor note for reference
    matched_eids = set()
    for f in sensor_files:
        fm = _parse_frontmatter(f)
        if fm and fm.get("ha_entity_id"):
            matched_eids.add(fm["ha_entity_id"])

    unmatched = [s for s in ha_sensors if s["entity_id"] not in matched_eids]
    if unmatched:
        print(f"\nUnmatched HA motion sensors (not linked to any sensor note):")
        for s in unmatched:
            print(f"  {s['entity_id']:<48} friendly_name: {s.get('friendly_name', '')}")


if __name__ == "__main__":
    main()
