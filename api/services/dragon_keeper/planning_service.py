"""Planning service — aggregates purchases, savings opportunities, and selling items."""
from api.services.dragon_keeper.purchases_service import get_purchases
from api.services.dragon_keeper.savings_opportunities_service import get_savings_opportunities
from api.services.dragon_keeper.selling_service import get_selling_items

ACTIVE_STATUSES = {"considering", "approved"}


def _is_active(status: str) -> bool:
    return status in ACTIVE_STATUSES


def _purchase_item(p: dict) -> dict:
    return {
        "type": "purchase",
        "filename": p["filename"],
        "filepath": p["filepath"],
        "title": p["item"],
        "status": p["status"],
        "order": p["order"],
        "added": p["added"] or "",
        "category": p["category"] or "",
        "direction": "out",
        "impact": p.get("cost"),
        "true_impact": p.get("true_cost_1yr"),
        "impact_detail": "one-time",
        "url": p.get("url"),
        "cost": p.get("cost"),
        "purchase_date": p.get("purchase_date"),
    }


def _savings_item(s: dict) -> dict:
    return {
        "type": "savings",
        "filename": s["filename"],
        "filepath": s["filepath"],
        "title": s["action"],
        "status": s["status"],
        "order": s["order"],
        "added": s["added"] or "",
        "category": s["category"] or "",
        "direction": "in",
        "impact": s.get("annual_savings"),
        "true_impact": s.get("true_savings_1yr"),
        "impact_detail": s.get("period"),
        "url": s.get("url"),
        "savings": s.get("savings"),
        "period": s.get("period"),
        "completed_date": s.get("completed_date"),
        "actual_savings": s.get("actual_savings"),
    }


def _selling_item(s: dict) -> dict:
    return {
        "type": "selling",
        "filename": s["filename"],
        "filepath": s["filepath"],
        "title": s["item"],
        "status": s["status"],
        "order": s["order"],
        "added": s["added"] or "",
        "category": s.get("possession_category") or "",
        "direction": "in",
        "impact": s.get("current_value"),
        "true_impact": s.get("true_value"),
        "impact_detail": "one-time",
        "url": None,
        "current_value": s.get("current_value"),
        "sold_date": s.get("sold_date"),
        "brand": s.get("brand"),
        "model": s.get("model"),
    }


def get_planning() -> dict:
    purchases = get_purchases()
    savings = get_savings_opportunities()
    selling = get_selling_items()

    items = (
        [_purchase_item(p) for p in purchases["purchases"]]
        + [_savings_item(s) for s in savings["opportunities"]]
        + [_selling_item(s) for s in selling["items"]]
    )

    max_cc_rate = purchases["max_cc_rate"] or savings["max_cc_rate"] or selling["max_cc_rate"]
    active = [i for i in items if _is_active(i["status"])]

    true_cost_out = sum(
        i["true_impact"] or 0 for i in active
        if i["type"] == "purchase" and i["true_impact"] is not None
    )
    true_savings_in = sum(
        i["true_impact"] or 0 for i in active
        if i["type"] == "savings" and i["true_impact"] is not None
    )
    sale_proceeds = sum(
        i["impact"] or 0 for i in active
        if i["type"] == "selling" and i["impact"] is not None
    )
    true_sale_proceeds = sum(
        i["true_impact"] or 0 for i in active
        if i["type"] == "selling" and i["true_impact"] is not None
    )

    return {
        "items": items,
        "summary": {
            "true_cost_out": round(true_cost_out, 2),
            "true_savings_in": round(true_savings_in, 2),
            "sale_proceeds": round(sale_proceeds, 2),
            "true_sale_proceeds": round(true_sale_proceeds, 2),
            "net_true_impact": round(true_savings_in + true_sale_proceeds - true_cost_out, 2),
        },
        "max_cc_rate": max_cc_rate,
        "counts": {
            "purchase": len([i for i in items if i["type"] == "purchase"]),
            "savings": len([i for i in items if i["type"] == "savings"]),
            "selling": len([i for i in items if i["type"] == "selling"]),
        },
    }
