"""Data layer - MongoDB repository and R2 storage."""
from data.mongodb_repository import (
    get_client,
    set_client,
    get_db,
    ping_db,
    save_order,
    get_order,
    get_recent_dates,
    get_order_by_iso,
    save_template,
    get_template,
    list_templates,
)
from data.r2_storage import download_excel

__all__ = [
    "get_client",
    "set_client",
    "get_db",
    "ping_db",
    "save_order",
    "get_order",
    "get_recent_dates",
    "get_order_by_iso",
    "save_template",
    "get_template",
    "list_templates",
    "download_excel",
]
