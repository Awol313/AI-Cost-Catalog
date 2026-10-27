import csv
import io
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import (
    BASE_DIR,
    CONFIDENCE_BLURBS,
    CONFIDENCE_LABELS,
    KIND_LABELS,
    STALE_AFTER_DAYS,
    STATUS_LABELS,
)
from app.db import get_db, init_db
from app.models import Offering
from app.seed import load_catalog, seed

app = FastAPI(title="LLM Model & Cost Catalog")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
templates.env.filters["kind_label"] = lambda k: KIND_LABELS.get(k, k)
templates.env.filters["status_label"] = lambda s: STATUS_LABELS.get(s, s)
templates.env.filters["confidence_label"] = lambda c: CONFIDENCE_LABELS.get(c, c)


def _money(value, places=2):
    """Format a price without trailing noise: $0.10, $2, $12.50, $0.0006."""
    if value is None:
        return "—"
    if value == 0:
        return "$0"
    text = "{:.{p}f}".format(value, p=places).rstrip("0").rstrip(".")
    return "${}".format(text)


def _tokens(value):
    if value is None:
        return "—"
    if value >= 1_000_000:
        return "{:g}M".format(value / 1_000_000)
    if value >= 1_000:
        return "{:g}K".format(value / 1_000)
    return str(value)


templates.env.filters["money"] = _money
templates.env.filters["tokens"] = _tokens


@app.on_event("startup")
def _startup():
    init_db()
    db = next(get_db())
    try:
        empty = db.query(Offering).count() == 0
    finally:
        db.close()
    # First run on a fresh checkout should just work, with no seed step to forget.
    if empty:
        seed(verbose=False)


# Sort keys map to (column, label). Token-priced sorts put NULLs last so that
# non-token rows never crowd the top of a price-sorted view.
SORTS = {
    "provider": "Provider",
    "name": "Name",
    "input": "Input price",
    "output": "Output price",
    "context": "Context window",
    "as_of": "Last checked",
}


def _filtered(db, provider, kind, status, confidence, q):
    query = db.query(Offering)
    if provider:
        query = query.filter(Offering.provider == provider)
    if kind:
        query = query.filter(Offering.kind == kind)
    if status:
        query = query.filter(Offering.status == status)
    if confidence:
        query = query.filter(Offering.confidence == confidence)
    if q:
        needle = "%{}%".format(q.strip().lower())
        query = query.filter(
            Offering.name.ilike(needle)
            | Offering.provider.ilike(needle)
            | Offering.model_id.ilike(needle)
            | Offering.notes.ilike(needle)
        )
    return query.all()


def _sorted(rows, sort, direction):
    reverse = direction == "desc"

    def key(row):
        if sort == "input":
            return (row.price_input is None, row.price_input or 0.0)
        if sort == "output":
            return (row.price_output is None, row.price_output or 0.0)
        if sort == "context":
            return (row.context_window is None, row.context_window or 0)
        if sort == "as_of":
            return (row.as_of is None, row.as_of or date.min)
        if sort == "name":
            return (False, row.name.lower())
        return (False, (row.provider.lower(), row.name.lower()))

    # A descending sort must still keep missing values at the bottom, so the
    # "is None" half of the key is never reversed.
    rows = sorted(rows, key=lambda r: key(r)[1], reverse=reverse)
    return sorted(rows, key=lambda r: key(r)[0])


@app.get("/")
def index(
    request: Request,
    provider: str = Query(""),
    kind: str = Query(""),
    status: str = Query(""),
    confidence: str = Query(""),
    q: str = Query(""),
    sort: str = Query("provider"),
    direction: str = Query("asc"),
    db: Session = Depends(get_db),
):
    if sort not in SORTS:
        sort = "provider"
    if direction not in ("asc", "desc"):
        direction = "asc"

    rows = _sorted(_filtered(db, provider, kind, status, confidence, q), sort, direction)

    all_rows = db.query(Offering).all()
    stale_cutoff = date.today() - timedelta(days=STALE_AFTER_DAYS)
    counts = {"verified": 0, "unverified": 0, "disputed": 0}
    for row in all_rows:
        if row.confidence in counts:
            counts[row.confidence] += 1

    catalog = load_catalog()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rows": rows,
            "total": len(all_rows),
            "providers": sorted({r.provider for r in all_rows}),
            "kinds": sorted({r.kind for r in all_rows}),
            "statuses": sorted({r.status for r in all_rows}),
            "confidences": ["verified", "unverified", "disputed"],
            "counts": counts,
            "confidence_blurbs": CONFIDENCE_BLURBS,
            "selected": {
                "provider": provider,
                "kind": kind,
                "status": status,
                "confidence": confidence,
                "q": q,
                "sort": sort,
                "direction": direction,
            },
            "sorts": SORTS,
            "stale_cutoff": stale_cutoff,
            "stale_after_days": STALE_AFTER_DAYS,
            "catalog_updated": catalog.get("catalog_updated", "unknown"),
        },
    )


@app.get("/export.csv")
def export_csv(
    provider: str = Query(""),
    kind: str = Query(""),
    status: str = Query(""),
    confidence: str = Query(""),
    q: str = Query(""),
    sort: str = Query("provider"),
    direction: str = Query("asc"),
    db: Session = Depends(get_db),
):
    """CSV of the current view. Carries source_url and as_of on every line so a
    price never leaves the app without its provenance attached."""
    rows = _sorted(_filtered(db, provider, kind, status, confidence, q), sort, direction)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "provider",
            "name",
            "model_id",
            "kind",
            "status",
            "context_window",
            "max_output",
            "input_per_mtok_usd",
            "output_per_mtok_usd",
            "cache_write_5m_per_mtok_usd",
            "cache_write_1h_per_mtok_usd",
            "cache_read_per_mtok_usd",
            "unit_price_usd",
            "unit_label",
            "free_tier",
            "confidence",
            "last_checked",
            "source_url",
            "notes",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.provider,
                r.name,
                r.model_id or "",
                KIND_LABELS.get(r.kind, r.kind),
                STATUS_LABELS.get(r.status, r.status),
                r.context_window if r.context_window is not None else "",
                r.max_output if r.max_output is not None else "",
                r.price_input if r.price_input is not None else "",
                r.price_output if r.price_output is not None else "",
                r.price_cache_write_5m if r.price_cache_write_5m is not None else "",
                r.price_cache_write_1h if r.price_cache_write_1h is not None else "",
                r.price_cache_read if r.price_cache_read is not None else "",
                r.unit_price if r.unit_price is not None else "",
                r.unit_label or "",
                r.free_tier or "",
                r.confidence,
                r.as_of.isoformat() if r.as_of else "",
                r.source_url or "",
                (r.notes or "").replace("\n", " "),
            ]
        )

    buffer.seek(0)
    filename = "llm-cost-catalog-{}.csv".format(date.today().isoformat())
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
    )
