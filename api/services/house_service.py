"""House service — reads room notes from the Obsidian vault."""
import os
import re
from pathlib import Path
import yaml


ROOMS_FOLDER = "1 Personal/3 Resources/Property/Rooms"
ROOM_TAG = "room"


def _vault_path() -> str:
    return os.getenv("OB_VAULT_PATH", "")


def _rooms_dir() -> Path:
    folder = os.getenv("VIZ_ROOM_FOLDER", ROOMS_FOLDER)
    return Path(_vault_path()) / folder


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _coerce_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_room_file(filepath: Path) -> dict | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    fm_str = content[3:end]
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
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

    return {
        "id": room_id,
        "name": name,
        "note": note,
        "x": x,
        "z": z,
        "w": w,
        "d": d,
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

    # Sort so emoji-prefixed files (higher Unicode) come last and win over slug duplicates
    seen_ids: set[str] = set()
    rooms: list[dict] = []
    for f in sorted(folder.glob("*.md")):
        if f.name.startswith("_"):
            continue
        room = _parse_room_file(f)
        if room is not None:
            if room["id"] in seen_ids:
                # Replace the earlier (slug-named) entry with this one
                rooms = [r for r in rooms if r["id"] != room["id"]]
            rooms.append(room)
            seen_ids.add(room["id"])

    links = _compute_links(rooms)
    for room in rooms:
        room["links"] = links.get(room["id"], {})

    return {"rooms": rooms, "source": "vault", "count": len(rooms)}
