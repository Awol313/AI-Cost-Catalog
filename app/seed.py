"""Load data/catalog.json into SQLite.

The JSON file is the source of truth and the thing to edit or regenerate; the
database is a disposable projection of it. Reseeding replaces every row, so a
refresh never leaves half-old data behind.
"""
import json
from datetime import datetime

from app.config import CATALOG_PATH
from app.db import SessionLocal, init_db
from app.models import Offering

FLOAT_FIELDS = (
    "price_input",
    "price_output",
    "price_cache_write_5m",
    "price_cache_write_1h",
    "price_cache_read",
    "unit_price",
)
INT_FIELDS = ("context_window", "max_output")
STR_FIELDS = (
    "provider",
    "name",
    "model_id",
    "kind",
    "status",
    "unit_label",
    "free_tier",
    "notes",
    "confidence",
    "source_url",
)


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_catalog():
    with open(str(CATALOG_PATH), "r", encoding="utf-8") as fh:
        return json.load(fh)


def seed(verbose=True):
    init_db()
    payload = load_catalog()
    rows = payload.get("offerings", [])

    db = SessionLocal()
    try:
        db.query(Offering).delete()
        for raw in rows:
            kwargs = {}
            for field in STR_FIELDS:
                kwargs[field] = raw.get(field)
            for field in FLOAT_FIELDS:
                value = raw.get(field)
                kwargs[field] = None if value is None else float(value)
            for field in INT_FIELDS:
                value = raw.get(field)
                kwargs[field] = None if value is None else int(value)
            kwargs["status"] = raw.get("status") or "current"
            kwargs["confidence"] = raw.get("confidence") or "unverified"
            kwargs["as_of"] = _parse_date(raw.get("as_of"))
            db.add(Offering(**kwargs))
        db.commit()
    finally:
        db.close()

    if verbose:
        print("Seeded {} offerings from {}".format(len(rows), CATALOG_PATH.name))
        print("Catalog updated: {}".format(payload.get("catalog_updated", "unknown")))
    return len(rows)


if __name__ == "__main__":
    seed()
