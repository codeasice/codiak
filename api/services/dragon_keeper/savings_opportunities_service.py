"""Savings opportunities service — reads/writes savings .md files from the Obsidian vault."""
import os
from datetime import date, datetime
from pathlib import Path
import yaml
from api.services.dragon_keeper.purchases_service import get_max_cc_rate

SAVINGS_FOLDER = "1 Personal/2 Areas/Personal Finance Area/Savings Opportunities"

VALID_PERIODS = {"one-time", "monthly", "yearly"}
VALID_STATUSES = {"considering", "approved", "done", "dropped"}


def _vault_path() -> str:
    return os.getenv("OB_VAULT_PATH", "")


def _savings_dir() -> Path:
    return Path(_vault_path()) / SAVINGS_FOLDER


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


def _annual_savings(amount: float | None, period: str) -> float | None:
    if amount is None:
        return None
    if period == "monthly":
        return round(amount * 12, 2)
    if period in ("one-time", "yearly"):
        return round(amount, 2)
    return None


def _parse_file(filepath: Path) -> dict | None:
    """Return a savings opportunity dict from a vault .md file, or None if not a savings note."""
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
    if "savings/opportunity" not in tags:
        return None
    period = fm.get("period") or "one-time"
    if period not in VALID_PERIODS:
        period = "one-time"
    savings = _coerce_float(fm.get("savings"))
    annual_savings = _annual_savings(savings, period)
    return {
        "filename": filepath.stem,
        "filepath": str(filepath),
        "action": fm.get("action") or filepath.stem,
        "savings": savings,
        "period": period,
        "order": fm.get("order"),
        "priority": fm.get("priority") or "",
        "category": fm.get("category") or "",
        "status": fm.get("status") or "considering",
        "added": _as_str(fm.get("added")),
        "completed_date": _as_str_or_none(fm.get("completed_date")),
        "actual_savings": _coerce_float(fm.get("actual_savings")),
        "url": fm.get("url") or None,
        "notes": body or None,
        "annual_savings": annual_savings,
    }


def _get_filepath(filename: str) -> str | None:
    p = _savings_dir() / f"{filename}.md"
    return str(p) if p.exists() else None


def _default_actual_savings(item: dict) -> float | None:
    """Default realized savings to true savings (1yr), falling back to annual savings."""
    return item.get("true_savings_1yr") or item.get("annual_savings")


def _completed_year(completed_date: str | None) -> int | None:
    if not completed_date:
        return None
    try:
        return int(completed_date[:4])
    except (TypeError, ValueError):
        return None


def get_savings_opportunities() -> dict:
    """Return all savings opportunity notes sorted by order, with annual totals."""
    folder = _savings_dir()
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
        annual = item.get("annual_savings")
        if annual is not None and max_rate is not None:
            item["true_savings_1yr"] = round(annual * (1 + max_rate / 100), 2)
        else:
            item["true_savings_1yr"] = None

    active = [i for i in items if i["status"] in ("considering", "approved")]
    total = sum(i["annual_savings"] or 0 for i in active if i["annual_savings"] is not None)
    total_true = sum(i["true_savings_1yr"] or 0 for i in active if i["true_savings_1yr"] is not None)

    done = [i for i in items if i["status"] == "done"]
    total_realized = sum(i["actual_savings"] or 0 for i in done if i["actual_savings"] is not None)

    by_year: dict[int, float] = {}
    for i in done:
        year = _completed_year(i.get("completed_date"))
        if year is None or i["actual_savings"] is None:
            continue
        by_year[year] = round(by_year.get(year, 0) + i["actual_savings"], 2)

    return {
        "opportunities": items,
        "total_annual_savings": round(total, 2),
        "total_true_savings_1yr": round(total_true, 2),
        "total_realized_savings": round(total_realized, 2),
        "realized_by_year": {str(y): v for y, v in sorted(by_year.items(), reverse=True)},
        "max_cc_rate": max_rate,
    }


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


def update_savings(filename: str, savings: float) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"savings": savings}) if fp else False


def update_period(filename: str, period: str) -> bool:
    if period not in VALID_PERIODS:
        return False
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"period": period}) if fp else False


def update_completed_date(filename: str, date: str | None) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"completed_date": date}) if fp else False


def update_status(filename: str, status: str) -> bool:
    if status not in VALID_STATUSES:
        return False
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"status": status}) if fp else False


def update_actual_savings(filename: str, actual_savings: float) -> bool:
    fp = _get_filepath(filename)
    return _rewrite_frontmatter(fp, {"actual_savings": actual_savings}) if fp else False


def mark_as_done(filename: str) -> bool:
    """Mark an opportunity done, set completed_date to today, and record actual savings."""
    data = get_savings_opportunities()
    item = next((i for i in data["opportunities"] if i["filename"] == filename), None)
    if item is None:
        return False
    actual = _default_actual_savings(item)
    if actual is None:
        return False
    fp = _get_filepath(filename)
    if not fp:
        return False
    return _rewrite_frontmatter(fp, {
        "status": "done",
        "completed_date": date.today().isoformat(),
        "actual_savings": round(actual, 2),
    })


def move_savings_opportunity(filename: str, direction: str) -> bool:
    """Swap order values with the adjacent item (direction: 'up' or 'down')."""
    data = get_savings_opportunities()
    items = data["opportunities"]

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
