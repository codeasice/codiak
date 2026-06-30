"""
Match Obsidian smart light notes to Home Assistant light entities by name normalization.

Reads light notes from the vault Smart Lights folder, fetches live HA light entities,
normalizes both names, and writes ha_entity_id to notes where a confident match is found.

Usage:
    python tools/match_lights_to_ha.py [--dry-run]
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import yaml
from api.services.home_assistant_service import get_grouped_entities
from api.services.house_service import LIGHTS_FOLDER, _vault_path, _parse_frontmatter

DRY_RUN = "--dry-run" in sys.argv


def _normalize(name: str) -> str:
    name = re.sub(r'[^\x00-\x7F]+', '', name)
    name = re.sub(r'^[Ll]\d+\s*[-–]\s*', '', name)
    name = re.sub(r'\s*(smart light|light|lamp|bulb)\s*$', '', name, flags=re.IGNORECASE)
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', name.lower()).split())


def _word_overlap(a: str, b: str) -> float:
    wa, wb = set(a.split()), set(b.split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _update_frontmatter(filepath: Path, key: str, value: str) -> bool:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return False
    if not content.startswith("---"):
        return False
    end = content.find("---", 3)
    if end == -1:
        return False
    try:
        fm = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return False
    if fm.get(key):
        return False
    new_fm = content[3:end].rstrip() + f"\n{key}: {value}\n"
    filepath.write_text("---" + new_fm + content[end:], encoding="utf-8")
    return True


def main():
    vault = _vault_path()
    if not vault:
        print("OB_VAULT_PATH is not set.")
        sys.exit(1)

    lights_dir = Path(vault) / LIGHTS_FOLDER
    if not lights_dir.exists():
        print(f"Smart Lights folder not found: {lights_dir}")
        sys.exit(1)

    print("Fetching HA light entities...")
    try:
        data = get_grouped_entities()
    except Exception as e:
        print(f"Failed to fetch HA entities: {e}")
        sys.exit(1)

    ha_lights = data.get("lights", [])
    print(f"Found {len(ha_lights)} HA lights.\n")

    ha_by_norm: dict[str, dict] = {}
    for light in ha_lights:
        norm = _normalize(light.get("friendly_name", light["entity_id"]))
        ha_by_norm[norm] = light

    light_files = sorted(lights_dir.glob("*.md"))
    print(f"{'Light Note':<42} {'HA Entity':<48} {'Conf':<6} {'Action'}")
    print("-" * 115)

    written = 0
    for f in light_files:
        fm = _parse_frontmatter(f)
        if fm is None:
            continue
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if "smart-light" not in tags:
            continue

        stem = f.stem
        existing_entity_id = fm.get("ha_entity_id", "")
        norm_stem = _normalize(stem)

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
        elif best_entity and confidence == "HIGH":
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

        print(f"{stem:<42} {entity_str:<48} {confidence:<6} {action}")

    print()
    if not DRY_RUN:
        print(f"Wrote ha_entity_id to {written} light note(s).")
        print("Review LOW/NONE confidence rows and add ha_entity_id manually.")
    else:
        print("Dry-run complete. Run without --dry-run to write changes.")

    matched_eids: set[str] = set()
    for f in light_files:
        fm = _parse_frontmatter(f)
        if fm and fm.get("ha_entity_id"):
            matched_eids.add(fm["ha_entity_id"])

    unmatched = [l for l in ha_lights if l["entity_id"] not in matched_eids]
    if unmatched:
        print(f"\nUnmatched HA lights (not linked to any light note):")
        for l in unmatched:
            print(f"  {l['entity_id']:<48} friendly_name: {l.get('friendly_name', '')}")


if __name__ == "__main__":
    main()
