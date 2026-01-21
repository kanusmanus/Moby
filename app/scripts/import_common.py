from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError(f"{filename} must contain a JSON array (list of objects).")
    return data


@dataclass
class ImportContext:
    user_id_map: Dict[Any, int]
    vehicle_id_map: Dict[Any, int]
    lot_id_map: Dict[Any, int]
    reservation_id_map: Dict[Any, int]
    payment_id_map: Dict[Any, int]

    @staticmethod
    def empty() -> "ImportContext":
        return ImportContext({}, {}, {}, {}, {})


def pick(item: dict, *keys: str, default=None):
    """Return first existing non-None value from item for given keys."""
    for k in keys:
        if k in item and item[k] is not None:
            return item[k]
    return default


def parse_dt(value: Any) -> Optional[datetime]:
    """
    Accepts:
    - ISO strings: "2025-01-01T10:00:00Z" / "+01:00"
    - unix timestamps (seconds)
    - datetime objects
    Returns datetime or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if isinstance(value, str):
        s = value.strip()
        # handle trailing Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            # fallback: common formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
    raise ValueError(f"Unsupported datetime value: {value!r}")


def commit_every(db: Session, i: int, chunk: int = 500) -> None:
    if i % chunk == 0:
        db.commit()
