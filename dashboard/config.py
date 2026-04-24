from __future__ import annotations

import os


class DashboardConfig:
    DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "")
    DASHBOARD_ALLOW_INSECURE = os.environ.get("DASHBOARD_ALLOW_INSECURE", "false").lower() == "true"
