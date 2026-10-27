from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CATALOG_PATH = BASE_DIR / "data" / "catalog.json"
DATABASE_PATH = BASE_DIR / "data" / "catalog.db"

# A row older than this many days is flagged stale in the UI. LLM pricing moves
# fast enough that month-old figures should not go into a client quote unchecked.
STALE_AFTER_DAYS = 45

KIND_LABELS = {
    "llm_model": "LLM model",
    "grounding": "Search grounding",
    "data_api": "Data / SERP API",
    "subscription": "Subscription",
    "tool": "Tool",
    "discount": "Discount",
    "surcharge": "Surcharge",
}

CONFIDENCE_LABELS = {
    "verified": "Verified",
    "unverified": "Unverified",
    "disputed": "Disputed",
}

# Why each confidence level exists, shown in the UI legend so the distinction
# survives contact with a client conversation.
CONFIDENCE_BLURBS = {
    "verified": "Read directly from the vendor's own pricing page.",
    "unverified": "Best available third-party reporting. Vendor page was not reachable when captured.",
    "disputed": "Sources materially disagree. Do not quote without checking the vendor page.",
}

STATUS_LABELS = {
    "current": "Current",
    "preview": "Preview",
    "legacy": "Legacy",
    "deprecated": "Deprecated",
    "retired": "Retired",
    "limited": "Limited access",
}
