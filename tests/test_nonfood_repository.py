"""Tests for isolated non-food MongoDB persistence APIs."""
from __future__ import annotations

from datetime import date
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import data
from data import (
    get_nonfood_order,
    get_nonfood_order_by_iso,
    get_nonfood_template,
    get_recent_nonfood_dates,
    list_nonfood_templates,
    save_nonfood_order,
    save_nonfood_template,
)
from data import mongodb_repository as repo


class _FakeCursor:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def sort(self, key: str, direction: int):
        reverse = direction < 0
        self._docs = sorted(self._docs, key=lambda doc: doc[key], reverse=reverse)
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class _FakeCollection:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[tuple] = []
        self.docs: dict[str, dict] = {}

    def create_index(self, *args, **kwargs):
        self.calls.append(("create_index", args, kwargs))

    def update_one(self, filter_doc: dict, update_doc: dict, upsert: bool = False):
        self.calls.append(("update_one", filter_doc, update_doc, upsert))
        payload = update_doc["$set"].copy()
        key = payload.get("date") or payload.get("_id")
        self.docs[key] = payload

    def find_one(self, query: dict):
        self.calls.append(("find_one", query))
        key = query.get("date") or query.get("_id")
        return self.docs.get(key)

    def find(self, query: dict, projection: dict):
        self.calls.append(("find", query, projection))
        docs = []
        for doc in self.docs.values():
            if projection == {"date": 1, "_id": 0}:
                docs.append({"date": doc["date"]})
            elif projection == {"_id": 1, "name": 1}:
                docs.append({"_id": doc["_id"], "name": doc["name"]})
            else:
                docs.append(doc.copy())
        return _FakeCursor(docs)


class _FakeDb:
    def __init__(self):
        self.collections = {
            "orders": _FakeCollection("orders"),
            "templates": _FakeCollection("templates"),
            "nonfood_orders": _FakeCollection("nonfood_orders"),
            "nonfood_templates": _FakeCollection("nonfood_templates"),
        }

    def __getitem__(self, name: str):
        return self.collections[name]


def test_nonfood_order_apis_use_isolated_collections(monkeypatch):
    fake_db = _FakeDb()
    monkeypatch.setattr(repo, "_get_db", lambda: fake_db)

    order_date = date(2026, 4, 21)
    items = [{"code": "NF01", "name": "Khan trang", "qty": 3}]

    save_nonfood_order(order_date, items)

    assert get_nonfood_order(order_date) == items
    assert get_nonfood_order_by_iso("2026-04-21") == items
    assert get_recent_nonfood_dates() == ["2026-04-21"]

    assert fake_db.collections["orders"].calls == []
    assert fake_db.collections["templates"].calls == []
    assert fake_db.collections["nonfood_orders"].calls[0][0] == "create_index"
    assert any(call[0] == "update_one" for call in fake_db.collections["nonfood_orders"].calls)
    assert any(call[0] == "find_one" for call in fake_db.collections["nonfood_orders"].calls)
    assert any(call[0] == "find" for call in fake_db.collections["nonfood_orders"].calls)


def test_nonfood_template_apis_use_isolated_collections(monkeypatch):
    fake_db = _FakeDb()
    monkeypatch.setattr(repo, "_get_db", lambda: fake_db)

    items = [{"code": "NF02", "name": "Bao tay", "qty": 1}]

    save_nonfood_template("van-phong", items)

    assert get_nonfood_template("van-phong") == items
    assert list_nonfood_templates() == [{"_id": "van-phong", "name": "van-phong"}]

    assert fake_db.collections["orders"].calls == []
    assert fake_db.collections["templates"].calls == []
    assert any(call[0] == "update_one" for call in fake_db.collections["nonfood_templates"].calls)
    assert any(call[0] == "find_one" for call in fake_db.collections["nonfood_templates"].calls)
    assert any(call[0] == "find" for call in fake_db.collections["nonfood_templates"].calls)


def test_data_package_exports_nonfood_apis():
    assert data.save_nonfood_order is save_nonfood_order
    assert data.get_nonfood_order is get_nonfood_order
    assert data.get_recent_nonfood_dates is get_recent_nonfood_dates
    assert data.get_nonfood_order_by_iso is get_nonfood_order_by_iso
    assert data.save_nonfood_template is save_nonfood_template
    assert data.get_nonfood_template is get_nonfood_template
    assert data.list_nonfood_templates is list_nonfood_templates
