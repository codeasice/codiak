"""Selling service — reads/writes possession selling .md files from the Obsidian vault."""
import os
from datetime import date, datetime
from pathlib import Path
import yaml
from api.services.dragon_keeper.purchases_service import get_max_cc_rate

SELLING_FOLDER = "1 Personal/3 Resources/Possessions (Thing and Stuff I own) Resource/Selling"


def _vault_path() -> str:
    return os.getenv("OB_VAULT_PATH", "")


def _selling_dir() -> Path:
    return Path(_vault_path()) / SELLING_FOLDER


def _coerce_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _as_str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return str(val)


def _as_str_or_none(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    s = str(val).strip()
    return s or None


def _parse_file(filepath: Path) -> dict | None:
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
    if "possession/selling" not in tags:
        return None
    current_value = _coerce_float(fm.get("current_value"))
    return {
        "filename": filepath.stem,
        "filepath": str(filepath),
        "item": fm.get("item") or filepath.stem,
        "current_value": current_value,
        "purchase_price": _coerce_float(fm.get("purchase_price")),
        "brand": fm.get("brand") or "",
        "model": fm.get("model") or "",
        "condition": fm.get("condition") or "",
        "possession_category": fm.get("possession_category") or "",
        "order": fm.get("order"),
        "status": fm.get("status") or "considering",
        "added": _as_str(fm.get("added")),
        "sold_date": _as_str_or_none(fm.get("sold_date")),
        "notes": body or None,
    }


def _get_filepath(filename: str) -> str | None:
    p = _selling_dir() / f"{filename}.md"
    return str(p) if p.exists() else None


def get_selling_items() -> dict:
    folder = _selling_dir()
    items: list[dict] = []
    if folder.exists():
        for f in sorted(folder.glob("*.md")):
            if f.name.startswith("_"):
                continue
            item = _parse_file(f)
            if item is not None:
                items.append(item)

    ordered = sorted([i for i in items if i["order"] is not None], key=lambda x: x["order"])
    unordered = sorted([i for i in items if i["order"] is None], key=lambda x: x["added"] or "")
    items = ordered + unordered

    max_rate = get_max_cc_rate()
    for item in items:
        value = item.get("current_value")
        if value is not None and max_rate is not None:
            item["true_value"] = round(value * (1 + max_rate / 100), 2)
        else:
            item["true_value"] = value

    active = [i for i in items if i["status"] in ("considering", "approved")]
    total = sum(i["current_value"] or 0 for i in active if i["current_value"] is not None)
    total_true = sum(i["true_value"] or 0 for i in active if i["true_value"] is not None)

    return {
        "items": items,
        "total_sale_value": round(total, 2),
        "total_true_sale_value": round(total_true, 2),
        "max_cc_rate": max_rate,
    }


def _rewrite_frontmatter(filepath: str, updates: dict) -> bool:
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


def update_current_value(filename: str, current_value: float) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"current_value": current_value}) if fp else False


def update_sold_date(filename: str, date: str | None) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"sold_date": date}) if fp else False


def move_selling_item(filename: str, direction: str) -> bool:
    data = get_selling_items()
    items = data["items"]

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
