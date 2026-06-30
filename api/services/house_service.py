"""House service — reads room notes from the Obsidian vault."""
import os
import re
from pathlib import Path
import yaml


ROOMS_FOLDER = "1 Personal/3 Resources/Property/Rooms"
SENSORS_FOLDER = "1 Personal/3 Resources/Possessions (Thing and Stuff I own) Resource/Electronic Devices and Accessories/Sensors"
LIGHTS_FOLDER = "1 Personal/3 Resources/Possessions (Thing and Stuff I own) Resource/Electronic Devices and Accessories/Smart Lights"
ROOM_TAG = "room"


def _vault_path() -> str:
    return os.getenv("OB_VAULT_PATH", "")


def _rooms_dir() -> Path:
    folder = os.getenv("VIZ_ROOM_FOLDER", ROOMS_FOLDER)
    return Path(_vault_path()) / folder


def _sensors_dir() -> Path:
    return Path(_vault_path()) / SENSORS_FOLDER

def _lights_dir() -> Path:
    return Path(_vault_path()) / LIGHTS_FOLDER


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _coerce_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_frontmatter(filepath: Path) -> dict | None:
    """Parse YAML frontmatter from any vault note. Returns None on error."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return None


def _strip_wikilink(val) -> str:
    """Strip Obsidian [[...]] syntax, returning the inner title."""
    if not isinstance(val, str):
        return ""
    return re.sub(r'^\[\[(.+)\]\]$', r'\1', val.strip())


def _build_sensor_map() -> dict[str, str]:
    """Returns {slugified_sensor_stem: ha_entity_id} for sensor notes that have ha_entity_id."""
    sensors_dir = _sensors_dir()
    result: dict[str, str] = {}
    if not sensors_dir.exists():
        return result
    for f in sensors_dir.glob("*.md"):
        fm = _parse_frontmatter(f)
        if fm is None:
            continue
        ha_entity_id = fm.get("ha_entity_id")
        if ha_entity_id:
            result[_slugify(f.stem)] = str(ha_entity_id).strip()
    return result


def _build_lights_map() -> dict[str, list[str]]:
    """Returns {room_id: [ha_entity_id, ...]} for light notes that have ha_entity_id and a location."""
    lights_dir = _lights_dir()
    result: dict[str, list[str]] = {}
    if not lights_dir.exists():
        return result
    for f in lights_dir.glob("*.md"):
        fm = _parse_frontmatter(f)
        if fm is None:
            continue
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if "smart-light" not in tags:
            continue
        ha_entity_id = fm.get("ha_entity_id")
        location_raw = _strip_wikilink(fm.get("location", ""))
        if not ha_entity_id or not location_raw:
            continue
        room_id = _slugify(location_raw)
        result.setdefault(room_id, []).append(str(ha_entity_id).strip())
    return result


def _parse_room_file(filepath: Path) -> dict | None:
    fm = _parse_frontmatter(filepath)
    if fm is None:
        return None

    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if ROOM_TAG not in tags:
        return None

    x = _coerce_float(fm.get("viz-x"))
    z = _coerce_float(fm.get("viz-z"))
    w = _coerce_float(fm.get("viz-w"))
    d = _coerce_float(fm.get("viz-d"))
    if any(v is None for v in [x, z, w, d]):
        return None

    room_id = _slugify(filepath.stem)
    name = str(fm.get("title") or filepath.stem.replace("_", " ").title())
    note = str(fm.get("note") or "")

    motion_raw = _strip_wikilink(fm.get("motion_sensor", ""))
    motion_sensor_ref = _slugify(motion_raw) if motion_raw else None

    return {
        "id": room_id,
        "name": name,
        "note": note,
        "x": x,
        "z": z,
        "w": w,
        "d": d,
        "_motion_sensor_ref": motion_sensor_ref,
    }


def _compute_links(rooms: list[dict]) -> dict[str, dict[str, str]]:
    """Derive directional nav links from wall adjacency.

    When multiple rooms share a wall in the same direction, prefer the one
    whose shared wall segment starts earliest (lowest coordinate value).
    """
    TOLERANCE = 0.05
    MIN_OVERLAP = 0.5

    # best[room_id][direction] = (target_id, overlap_start)
    best: dict[str, dict[str, tuple[str, float]]] = {r["id"]: {} for r in rooms}

    def try_update(room_id: str, direction: str, target_id: str, overlap_start: float) -> None:
        existing = best[room_id].get(direction)
        if existing is None or overlap_start < existing[1]:
            best[room_id][direction] = (target_id, overlap_start)

    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            ax0, ax1 = a["x"], a["x"] + a["w"]
            az0, az1 = a["z"], a["z"] + a["d"]
            bx0, bx1 = b["x"], b["x"] + b["w"]
            bz0, bz1 = b["z"], b["z"] + b["d"]

            # East-west adjacency
            if abs(ax1 - bx0) < TOLERANCE:
                z_overlap = min(az1, bz1) - max(az0, bz0)
                if z_overlap >= MIN_OVERLAP:
                    start = max(az0, bz0)
                    try_update(a["id"], "east", b["id"], start)
                    try_update(b["id"], "west", a["id"], start)
            elif abs(bx1 - ax0) < TOLERANCE:
                z_overlap = min(az1, bz1) - max(az0, bz0)
                if z_overlap >= MIN_OVERLAP:
                    start = max(az0, bz0)
                    try_update(b["id"], "east", a["id"], start)
                    try_update(a["id"], "west", b["id"], start)

            # North-south adjacency (south = increasing z)
            if abs(az1 - bz0) < TOLERANCE:
                x_overlap = min(ax1, bx1) - max(ax0, bx0)
                if x_overlap >= MIN_OVERLAP:
                    start = max(ax0, bx0)
                    try_update(a["id"], "south", b["id"], start)
                    try_update(b["id"], "north", a["id"], start)
            elif abs(bz1 - az0) < TOLERANCE:
                x_overlap = min(ax1, bx1) - max(ax0, bx0)
                if x_overlap >= MIN_OVERLAP:
                    start = max(ax0, bx0)
                    try_update(b["id"], "south", a["id"], start)
                    try_update(a["id"], "north", b["id"], start)

    return {
        room_id: {dir_: target for dir_, (target, _) in dirs.items()}
        for room_id, dirs in best.items()
    }


def get_rooms() -> dict:
    vault = _vault_path()
    if not vault:
        return {"rooms": [], "source": "unconfigured", "count": 0}

    folder = _rooms_dir()
    if not folder.exists():
        return {"rooms": [], "source": "folder_missing", "count": 0}

    sensor_map = _build_sensor_map()
    lights_map = _build_lights_map()

    # Sort so emoji-prefixed files (higher Unicode) come last and win over slug duplicates
    seen_ids: set[str] = set()
    rooms: list[dict] = []
    for f in sorted(folder.glob("*.md")):
        if f.name.startswith("_"):
            continue
        room = _parse_room_file(f)
        if room is not None:
            if room["id"] in seen_ids:
                rooms = [r for r in rooms if r["id"] != room["id"]]
            rooms.append(room)
            seen_ids.add(room["id"])

    links = _compute_links(rooms)
    for room in rooms:
        room["links"] = links.get(room["id"], {})
        ref = room.pop("_motion_sensor_ref", None)
        room["motion_entity_id"] = sensor_map.get(ref) if ref else None
        room["light_entity_ids"] = lights_map.get(room["id"], [])

    return {"rooms": rooms, "source": "vault", "count": len(rooms)}
