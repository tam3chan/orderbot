"""
MongoDB data layer cho Order Bot.
Collections:
  - orders    : lưu đơn hàng theo ngày
  - templates : lưu đơn mẫu
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection


def _get_uri() -> str:
    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        raise RuntimeError("MONGODB_URI environment variable is not set!")
    return uri


# ─── Singleton client (tái sử dụng connection) ─────────────────────────
_client: MongoClient | None = None


def _get_db():
    global _client
    if _client is None:
        _client = MongoClient(_get_uri())
    db = _client["orderbot"]
    return db


def _orders() -> Collection:
    col = _get_db()["orders"]
    col.create_index("date", unique=True)
    return col


def _templates() -> Collection:
    return _get_db()["templates"]


# ─── Orders ────────────────────────────────────────────────────────────
def save_order(order_date: date, items: list[dict]) -> None:
    """Lưu/cập nhật đơn hàng (upsert theo ngày)."""
    _orders().update_one(
        {"date": order_date.isoformat()},
        {"$set": {
            "date": order_date.isoformat(),
            "items": items,
            "updated_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )


def get_order(order_date: date) -> list[dict] | None:
    """Trả về danh sách items của ngày đó, hoặc None nếu chưa có."""
    doc = _orders().find_one({"date": order_date.isoformat()})
    return doc["items"] if doc else None


def get_recent_dates(n: int = 7) -> list[str]:
    """Trả về list ngày ISO (YYYY-MM-DD) của n đơn gần nhất."""
    cursor = _orders().find({}, {"date": 1, "_id": 0}).sort("date", DESCENDING).limit(n)
    return [doc["date"] for doc in cursor]


def get_order_by_iso(iso_str: str) -> list[dict] | None:
    """Tìm đơn hàng theo chuỗi ngày ISO trực tiếp (YYYY-MM-DD)."""
    doc = _orders().find_one({"date": iso_str})
    return doc["items"] if doc else None




# ─── Templates ─────────────────────────────────────────────────────────
def save_template(name: str, items: list[dict]) -> None:
    """Lưu/cập nhật template."""
    _templates().update_one(
        {"_id": name},
        {"$set": {
            "_id": name,
            "name": name,
            "items": items,
            "updated_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )


def get_template(name: str) -> list[dict] | None:
    doc = _templates().find_one({"_id": name})
    return doc["items"] if doc else None

 
def list_templates() -> list[dict]:
    """Trả về list {"_id": ..., "name": ...} của tất cả templates."""
    return list(_templates().find({}, {"_id": 1, "name": 1}))
