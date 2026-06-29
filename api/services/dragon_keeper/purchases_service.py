"""Purchases service — reads/writes purchase .md files from the Obsidian vault."""
import os
from pathlib import Path
import yaml
from api.models.dragon_keeper.db import get_db

VAULT_PATH = os.getenv("OB_VAULT_PATH", "")
PURCHASES_FOLDER = "1 Personal/3 Resources/Shopping"


def _purchases_dir() -> Path:
    return Path(VAULT_PATH) / PURCHASES_FOLDER


def _parse_file(filepath: Path) -> dict | None:
    """Return a purchase dict from a vault .md file, or None if not a purchase note."""
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
    body = content[end + 3:].strip()
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        return None
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if "shopping/purchase" not in tags:
        return None
    return {
        "filename": filepath.stem,
        "filepath": str(filepath),
        "item": fm.get("item") or filepath.stem,
        "cost": fm.get("cost"),
        "order": fm.get("order"),
        "priority": fm.get("priority", ""),
        "category": fm.get("category", ""),
        "status": fm.get("status", "considering"),
        "added": fm.get("added", ""),
        "purchase_date": fm.get("purchase_date"),
        "url": fm.get("url"),
        "notes": body or None,
    }


def _get_filepath(filename: str) -> str | None:
    p = _purchases_dir() / f"{filename}.md"
    return str(p) if p.exists() else None


def get_max_cc_rate() -> float | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT MAX(interest_rate) AS rate FROM accounts "
            "WHERE type='creditCard' AND interest_rate IS NOT NULL AND deleted=0"
        ).fetchone()
        return row["rate"] if row else None
    finally:
        conn.close()


def get_purchases() -> dict:
    """Return all purchase notes sorted by order, with true 1-year cost appended."""
    folder = _purchases_dir()
    items: list[dict] = []
    if folder.exists():
        for f in sorted(folder.glob("*.md")):
            if f.name.startswith("_"):
                continue
            p = _parse_file(f)
            if p is not None:
                items.append(p)

    ordered = sorted([i for i in items if i["order"] is not None], key=lambda x: x["order"])
    unordered = sorted([i for i in items if i["order"] is None], key=lambda x: x["added"] or "")
    items = ordered + unordered

    max_rate = get_max_cc_rate()
    for item in items:
        cost = item.get("cost")
        if cost is not None and max_rate is not None:
            item["true_cost_1yr"] = round(cost * (1 + max_rate / 100), 2)
        else:
            item["true_cost_1yr"] = None

    return {"purchases": items, "max_cc_rate": max_rate}


def _rewrite_frontmatter(filepath: str, updates: dict) -> bool:
    """Merge updates into the frontmatter of an existing .md file."""
    p = Path(filepath)
    if not p.exists():
        return False
    content = p.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False
    end = content.find("---", 3)
    if end == -1:
        return False
    fm_str = content[3:end]
    body = content[end + 3:]
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        return False
    fm.update(updates)
    new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    p.write_text(f"---\n{new_fm}---{body}", encoding="utf-8")
    return True


def update_cost(filename: str, cost: float) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"cost": cost}) if fp else False


def update_purchase_date(filename: str, date: str | None) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"purchase_date": date}) if fp else False


def move_purchase(filename: str, direction: str) -> bool:
    """Swap order values with the adjacent item (direction: 'up' or 'down')."""
    data = get_purchases()
    items = data["purchases"]

    # Assign orders to any unordered items so swapping works uniformly
    for idx, item in enumerate(items):
        if item["order"] is None:
            item["order"] = idx + 1
            _rewrite_frontmatter(item["filepath"], {"order": idx + 1})

    idx = next((i for i, item in enumerate(items) if item["filename"] == filename), None)
    if idx is None:
        return False

    if direction == "up" and idx > 0:
        a, b = items[idx], items[idx - 1]
    elif direction == "down" and idx < len(items) - 1:
        a, b = items[idx], items[idx + 1]
    else:
        return False

    _rewrite_frontmatter(a["filepath"], {"order": b["order"]})
    _rewrite_frontmatter(b["filepath"], {"order": a["order"]})
    return True
