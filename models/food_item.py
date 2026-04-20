"""Food item model loaded from Excel."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FoodItem:
    """Represents a food item from the supplier Excel."""
    code: str
    name: str
    unit: str
    cat: str
    sub: str = ""
    ncc: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "FoodItem":
        """Create FoodItem from dict (e.g., from Excel row or DB)."""
        return cls(
            code=str(data.get("code", "")),
            name=str(data.get("name", "")),
            unit=str(data.get("unit", "kg")),
            cat=str(data.get("cat", "Khác")),
            sub=str(data.get("sub", "")),
            ncc=str(data.get("ncc", "")),
        )

    def to_dict(self) -> dict:
        """Convert to dict for storage."""
        return {
            "code": self.code,
            "name": self.name,
            "unit": self.unit,
            "cat": self.cat,
            "sub": self.sub,
            "ncc": self.ncc,
        }
