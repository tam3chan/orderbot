"""Order item model for order state."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class OrderItem:
    """Represents an item in an order."""
    code: str
    name: str
    qty: float
    unit: str
    ncc: str = ""
    order_date: Optional[date] = None

    @classmethod
    def from_dict(cls, data: dict) -> "OrderItem":
        """Create OrderItem from dict."""
        order_date = data.get("order_date")
        if isinstance(order_date, str):
            order_date = date.fromisoformat(order_date) if order_date else None
        return cls(
            code=str(data.get("code", "")),
            name=str(data.get("name", "")),
            qty=float(data.get("qty", 0)),
            unit=str(data.get("unit", "kg")),
            ncc=str(data.get("ncc", "")),
            order_date=order_date,
        )

    def to_dict(self) -> dict:
        """Convert to dict for storage."""
        return {
            "code": self.code,
            "name": self.name,
            "qty": self.qty,
            "unit": self.unit,
            "ncc": self.ncc,
            "order_date": self.order_date.isoformat() if self.order_date else None,
        }
