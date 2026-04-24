from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dashboard.app import create_app
import dashboard.services.order_queries as order_queries


class _FakeCursor:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def sort(self, key: str, direction: int):
        self._docs = sorted(self._docs, key=lambda doc: doc[key], reverse=direction < 0)
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class _FakeCollection:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.calls: list[tuple] = []

    def find(self, query: dict, projection: dict):
        self.calls.append((query, projection))
        return _FakeCursor([doc.copy() for doc in self.docs])

    def find_one(self, query: dict, projection: dict):
        self.calls.append((query, projection))
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return doc.copy()
        return None


class _FakeDb:
    def __init__(self):
        self.collections = {
            "orders": _FakeCollection([
                {"date": "2026-04-24", "items": [{"name": "Rau", "qty": 2}], "updated_at": "a"},
            ]),
            "nonfood_orders": _FakeCollection([
                {"date": "2026-04-23", "items": [{"name": "Giấy", "qty": 1}], "updated_at": "b"},
            ]),
            "templates": _FakeCollection([
                {"name": "food-template", "items": [1, 2, 3], "updated_at": "c"},
            ]),
            "nonfood_templates": _FakeCollection([
                {"name": "nonfood-template", "items": [1], "updated_at": "d"},
            ]),
        }

    def __getitem__(self, name: str):
        return self.collections[name]


def _make_client(monkeypatch):
    app = create_app()
    app.config.update(DASHBOARD_TOKEN="", DASHBOARD_ALLOW_INSECURE=True)
    return app.test_client()


def _make_token_client(token: str = "secret"):
    app = create_app()
    app.config.update(DASHBOARD_TOKEN=token, DASHBOARD_ALLOW_INSECURE=False)
    return app.test_client()


def test_health_returns_503_without_token_and_no_insecure(monkeypatch):
    app = create_app()
    app.config.update(DASHBOARD_TOKEN="", DASHBOARD_ALLOW_INSECURE=False)

    client = app.test_client()
    resp = client.get("/api/health")

    assert resp.status_code == 503
    assert resp.get_json() == {"ok": False, "error": "DASHBOARD_TOKEN is not configured"}


def test_health_allows_insecure_and_uses_ping_db(monkeypatch):
    app = create_app()
    app.config.update(DASHBOARD_TOKEN="", DASHBOARD_ALLOW_INSECURE=True)
    monkeypatch.setattr("data.mongodb_repository.ping_db", lambda: True)

    resp = app.test_client().get("/api/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True, "mongo_ok": True, "auth_configured": False}


def test_configured_token_auth_accepts_bearer_and_rejects_missing(monkeypatch):
    monkeypatch.setattr("data.mongodb_repository.ping_db", lambda: True)
    client = _make_token_client("secret")

    missing = client.get("/api/health")
    valid = client.get("/api/health", headers={"Authorization": "Bearer secret"})

    assert missing.status_code == 401
    assert missing.get_json() == {"ok": False, "error": "Unauthorized"}
    assert valid.status_code == 200
    assert valid.get_json()["auth_configured"] is True


def test_configured_token_auth_accepts_dashboard_header(monkeypatch):
    monkeypatch.setattr("data.mongodb_repository.ping_db", lambda: True)
    client = _make_token_client("secret")

    resp = client.get("/api/health", headers={"X-Dashboard-Token": "secret"})

    assert resp.status_code == 200


def test_orders_and_templates_use_expected_collections(monkeypatch):
    fake_db = _FakeDb()
    monkeypatch.setattr(order_queries, "get_db", lambda: fake_db)

    client = _make_client(monkeypatch)

    food_orders = client.get("/api/orders?type=food")
    nonfood_orders = client.get("/api/orders?type=nonfood")
    food_templates = client.get("/api/templates?type=food")
    nonfood_templates = client.get("/api/templates?type=nonfood")

    assert food_orders.status_code == 200
    assert food_orders.get_json()["orders"] == [{"date": "2026-04-24", "item_count": 1, "updated_at": "a"}]
    assert nonfood_orders.get_json()["orders"] == [{"date": "2026-04-23", "item_count": 1, "updated_at": "b"}]
    assert food_templates.get_json()["templates"] == [{"name": "food-template", "item_count": 3, "updated_at": "c"}]
    assert nonfood_templates.get_json()["templates"] == [{"name": "nonfood-template", "item_count": 1, "updated_at": "d"}]

    assert fake_db.collections["orders"].calls
    assert fake_db.collections["nonfood_orders"].calls
    assert fake_db.collections["templates"].calls
    assert fake_db.collections["nonfood_templates"].calls


def test_order_detail_and_not_found(monkeypatch):
    fake_db = _FakeDb()
    monkeypatch.setattr(order_queries, "get_db", lambda: fake_db)
    client = _make_client(monkeypatch)

    found = client.get("/api/orders/2026-04-24?type=food")
    missing = client.get("/api/orders/1999-01-01?type=food")

    assert found.status_code == 200
    assert found.get_json()["order"] == {
        "type": "food",
        "date": "2026-04-24",
        "items": [{"name": "Rau", "qty": 2}],
        "updated_at": "a",
    }
    assert missing.status_code == 404


def test_invalid_type_returns_400(monkeypatch):
    client = _make_client(monkeypatch)

    resp = client.get("/api/orders?type=bad")

    assert resp.status_code == 400
    assert resp.get_json() == {"ok": False, "error": "type must be 'food' or 'nonfood'"}
