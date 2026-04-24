from __future__ import annotations

from typing import Any

from data.mongodb_repository import get_db


VALID_KINDS = {"food", "nonfood"}


def normalize_kind(kind: str | None) -> str:
    """Return a supported dashboard order type."""
    value = (kind or "food").strip().lower()
    if value not in VALID_KINDS:
        raise ValueError("type must be 'food' or 'nonfood'")
    return value


def normalize_limit(raw_limit: str | int | None, default: int = 30, max_limit: int = 100) -> int:
    """Clamp dashboard list limits so accidental large queries stay bounded."""
    try:
        limit = int(raw_limit) if raw_limit is not None else default
    except (TypeError, ValueError):
        raise ValueError("limit must be a number") from None
    if limit < 1:
        raise ValueError("limit must be at least 1")
    return min(limit, max_limit)


def _collection(kind: str, suffix: str):
    db = get_db()
    collection_names = {
        ("food", "orders"): "orders",
        ("food", "templates"): "templates",
        ("nonfood", "orders"): "nonfood_orders",
        ("nonfood", "templates"): "nonfood_templates",
    }
    return db[collection_names[(normalize_kind(kind), suffix)]]


def _summary(doc: dict[str, Any]) -> dict[str, Any]:
    items = doc.get("items") or []
    return {
        "date": doc.get("date"),
        "item_count": len(items),
        "updated_at": doc.get("updated_at"),
    }


def list_orders(kind: str, limit: int) -> list[dict[str, Any]]:
    col = _collection(kind, "orders")
    cursor = col.find({}, {"_id": 0, "date": 1, "items": 1, "updated_at": 1}).sort("date", -1).limit(limit)
    return [_summary(doc) for doc in cursor]


def get_order_detail(kind: str, date: str) -> dict[str, Any] | None:
    col = _collection(kind, "orders")
    doc = col.find_one({"date": date}, {"_id": 0})
    if not doc:
        return None
    return {
        "type": kind,
        "date": doc.get("date"),
        "items": doc.get("items", []),
        "updated_at": doc.get("updated_at"),
    }


def list_templates(kind: str) -> list[dict[str, Any]]:
    col = _collection(kind, "templates")
    cursor = col.find({}, {"_id": 0, "name": 1, "items": 1, "updated_at": 1})
    out: list[dict[str, Any]] = []
    for doc in cursor:
        items = doc.get("items") or []
        row = {"name": doc.get("name")}
        if "items" in doc:
            row["item_count"] = len(items)
        if doc.get("updated_at") is not None:
            row["updated_at"] = doc.get("updated_at")
        out.append(row)
    return out
