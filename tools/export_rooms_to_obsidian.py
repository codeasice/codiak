"""
Migration script: adds viz-* properties to existing Obsidian room notes.

Matches each app room to an existing note by comparing the slugified filename
stem to the room ID. For matched notes, adds title, note, viz-x, viz-z, viz-w,
viz-d to the frontmatter if those properties are absent. Existing properties
and body content are never overwritten.

Run once:
  python tools/export_rooms_to_obsidian.py
"""
import io
import os
import re
import sys
from pathlib import Path
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOMS_FOLDER = "1 Personal/3 Resources/Property/Rooms"

ROOMS = [
    {"id": "master_bedroom",           "name": "Master Bedroom",           "note": "Large upstairs bedroom on the west side of the house.",                        "x": 12,   "z": 0,     "w": 9,   "d": 6},
    {"id": "master_bathroom",          "name": "Master Bathroom",          "note": "Bathroom suite between the master bedroom and dining room.",                    "x": 21,   "z": 0,     "w": 7,   "d": 2},
    {"id": "hallway_closet_upper_a",   "name": "Hallway Closet (Upper A)", "note": "Compact upstairs hallway closet below the master bathroom.",                   "x": 21,   "z": 2,     "w": 3,   "d": 2},
    {"id": "main_bathroom",            "name": "Main Bathroom",            "note": "Shared upstairs bathroom beside the central closets.",                         "x": 24,   "z": 2,     "w": 4,   "d": 4},
    {"id": "hallway_closet_upper_b",   "name": "Hallway Closet (Upper B)", "note": "Second small closet in the upstairs bath cluster.",                            "x": 21,   "z": 4,     "w": 3,   "d": 2},
    {"id": "dining_room",              "name": "Dining Room",              "note": "Tall central upstairs room between bathrooms, kitchen, and stairs.",            "x": 28,   "z": 0,     "w": 7.5, "d": 9},
    {"id": "kitchen",                  "name": "Kitchen",                  "note": "Upstairs kitchen connected to the dining and living spaces.",                  "x": 35.5, "z": 0,     "w": 8,   "d": 6.5},
    {"id": "glass_room",               "name": "Glass Room",               "note": "Long eastern upstairs room with exterior exposure.",                           "x": 43.5, "z": 0,     "w": 6,   "d": 13},
    {"id": "office_closet",            "name": "Office Closet",            "note": "Small closet above Cody Office.",                                              "x": 12,   "z": 6,     "w": 4,   "d": 2},
    {"id": "hallway_closet_upper_c",   "name": "Hallway Closet (Upper C)", "note": "Closet segment west of the upstairs hallway.",                                 "x": 16,   "z": 6,     "w": 4,   "d": 2},
    {"id": "upstairs_hallway",         "name": "Upstairs Hallway",         "note": "Central upstairs connector for bedrooms, closets, bathrooms, and dining.",     "x": 20,   "z": 6,     "w": 8,   "d": 2},
    {"id": "cody_office",              "name": "Cody Office",              "note": "Upstairs office at the southwest part of the occupied layout.",                "x": 12,   "z": 8,     "w": 8,   "d": 5},
    {"id": "george_bedroom",           "name": "George Bedroom",           "note": "Large bedroom below the upstairs hallway.",                                    "x": 20,   "z": 8,     "w": 8,   "d": 5},
    {"id": "hallway_closet_dining_a",  "name": "Hallway Closet (Dining A)","note": "Closet stack below the dining room.",                                         "x": 28,   "z": 9,     "w": 3,   "d": 1.75},
    {"id": "hallway_closet_dining_b",  "name": "Hallway Closet (Dining B)","note": "Lower closet beside the upstairs stairs.",                                    "x": 28,   "z": 10.75, "w": 3,   "d": 2.25},
    {"id": "upstairs_stairs",          "name": "Upstairs Stairs",          "note": "Stairwell linking the upstairs and downstairs floor plans.",                   "x": 31,   "z": 9,     "w": 4.5, "d": 4},
    {"id": "living_room",              "name": "Living Room",              "note": "Upstairs living room below the kitchen.",                                      "x": 35.5, "z": 6.5,   "w": 8,   "d": 6.5},
    {"id": "garage",                   "name": "Garage",                   "note": "Large downstairs garage at the west side.",                                    "x": 0,    "z": 18,    "w": 12,  "d": 12},
    {"id": "music_room",               "name": "Music Room",               "note": "Downstairs music room above the workout room.",                                "x": 12,   "z": 18,    "w": 10,  "d": 7},
    {"id": "workout_room",             "name": "Workout Room",             "note": "Downstairs room below the music room.",                                        "x": 12,   "z": 25,    "w": 10,  "d": 5},
    {"id": "harris_bathroom",          "name": "Harris Bathroom",          "note": "Downstairs bathroom west of Harris Bedroom.",                                  "x": 22,   "z": 18,    "w": 4.5, "d": 6},
    {"id": "harris_bedroom",           "name": "Harris Bedroom",           "note": "Large downstairs bedroom between bathroom and laundry.",                       "x": 26.5, "z": 18,    "w": 8.5, "d": 6},
    {"id": "laundry_room",             "name": "Laundry Room",             "note": "Downstairs utility room beside the cellar and playroom.",                      "x": 35,   "z": 18,    "w": 7.5, "d": 6},
    {"id": "creepy_cellar",            "name": "Creepy Cellar",            "note": "Long eastern downstairs cellar area.",                                         "x": 42.5, "z": 18,    "w": 5.5, "d": 12},
    {"id": "downstairs_hallway",       "name": "Downstairs Hallway",       "note": "Downstairs hallway segment connecting bedrooms, offices, and stairs.",         "x": 22,   "z": 24,    "w": 13,  "d": 2},
    {"id": "amanda_office",            "name": "Amanda Office",            "note": "Downstairs office near the stairwell.",                                        "x": 22,   "z": 26,    "w": 6,   "d": 4},
    {"id": "hallway_closet_downstairs","name": "Hallway Closet (Downstairs)","note": "Small downstairs closet beside Amanda Office.",                              "x": 28,   "z": 26,    "w": 2.5, "d": 2},
    {"id": "amanda_office_closet",     "name": "Amanda Office Closet",     "note": "Closet below Amanda Office hallway closet.",                                   "x": 28,   "z": 28,    "w": 2.5, "d": 2},
    {"id": "downstairs_stairs",        "name": "Downstairs Stairs",        "note": "Lower stairwell linking back to the upstairs stairs.",                         "x": 30.5, "z": 26,    "w": 4.5, "d": 4},
    {"id": "playroom",                 "name": "Playroom",                 "note": "Large downstairs playroom below the laundry room.",                            "x": 35,   "z": 24,    "w": 7.5, "d": 6},
]


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _add_props_to_existing(filepath: Path, props: dict) -> bool:
    """Add missing YAML frontmatter properties; never overwrites existing values."""
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        fm = props.copy()
        new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        filepath.write_text(f"---\n{new_fm}---\n\n{content}", encoding="utf-8")
        return True

    end = content.find("---", 3)
    if end == -1:
        return False
    fm_str = content[3:end]
    body = content[end + 3:]
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        return False

    changed = False
    for key, value in props.items():
        if key not in fm:
            fm[key] = value
            changed = True

    if not changed:
        return False

    new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    filepath.write_text(f"---\n{new_fm}---{body}", encoding="utf-8")
    return True


def main():
    vault = os.getenv("OB_VAULT_PATH", "")
    if not vault:
        print("ERROR: OB_VAULT_PATH is not set.")
        sys.exit(1)

    folder_rel = os.getenv("VIZ_ROOM_FOLDER", ROOMS_FOLDER)
    folder = Path(vault) / folder_rel
    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}")
        sys.exit(1)

    # Build map: slugified stem → filepath for all existing notes
    existing: dict[str, Path] = {}
    for f in folder.glob("*.md"):
        slug = _slugify(f.stem)
        existing[slug] = f

    updated = 0
    skipped = 0
    unmatched = []

    for room in ROOMS:
        filepath = existing.get(room["id"])
        if filepath is None:
            unmatched.append(room["id"])
            continue

        props = {
            "title": room["name"],
            "note": room["note"],
            "viz-x": room["x"],
            "viz-z": room["z"],
            "viz-w": room["w"],
            "viz-d": room["d"],
        }
        changed = _add_props_to_existing(filepath, props)
        if changed:
            print(f"  updated  {filepath.name}")
            updated += 1
        else:
            print(f"  skipped  {filepath.name} (already complete)")
            skipped += 1

    print(f"\nDone: {updated} updated, {skipped} skipped")
    if unmatched:
        print(f"\nNo matching note found for {len(unmatched)} rooms (will use hardcoded fallback):")
        for rid in unmatched:
            print(f"  - {rid}")


if __name__ == "__main__":
    main()
