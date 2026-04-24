from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .auth import api_auth_required
from .config import DashboardConfig
from .services.order_queries import (
    get_order_detail,
    list_orders,
    list_templates,
    normalize_kind,
    normalize_limit,
)


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(DashboardConfig)

    @app.get("/")
    def index():
        return send_from_directory(Path(app.static_folder), "index.html")

    @app.get("/api/health")
    @api_auth_required
    def health():
        from data.mongodb_repository import ping_db

        return jsonify({"ok": True, "mongo_ok": ping_db(), "auth_configured": bool(app.config.get("DASHBOARD_TOKEN"))})

    @app.get("/api/orders")
    @api_auth_required
    def orders():
        try:
            kind = normalize_kind(request.args.get("type", "food"))
            limit = normalize_limit(request.args.get("limit", 30))
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "orders": list_orders(kind, limit)})

    @app.get("/api/orders/<date>")
    @api_auth_required
    def order_detail(date: str):
        try:
            kind = normalize_kind(request.args.get("type", "food"))
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        doc = get_order_detail(kind, date)
        if not doc:
            return jsonify({"ok": False, "error": "Not found"}), 404
        return jsonify({"ok": True, "order": doc})

    @app.get("/api/templates")
    @api_auth_required
    def templates():
        try:
            kind = normalize_kind(request.args.get("type", "food"))
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "templates": list_templates(kind)})

    return app


if __name__ == "__main__":
    debug = os.environ.get("DASHBOARD_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("DASHBOARD_PORT", "5000"))
    create_app().run(host="127.0.0.1", port=port, debug=debug)
