from __future__ import annotations

import hmac
from functools import wraps

from flask import Response, current_app, jsonify, request


def _token_from_request() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.headers.get("X-Dashboard-Token", "").strip()


def api_auth_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = current_app.config.get("DASHBOARD_TOKEN", "")
        insecure = bool(current_app.config.get("DASHBOARD_ALLOW_INSECURE", False))
        if not token:
            if insecure:
                return view(*args, **kwargs)
            return jsonify({"ok": False, "error": "DASHBOARD_TOKEN is not configured"}), 503
        if not hmac.compare_digest(_token_from_request(), token):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapper
