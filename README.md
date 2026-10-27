# AI Cost Catalog

A private reference app: every model version, grounding surcharge, data/SERP API,
and subscription tier that's out there, with what each one costs — and, on every
row, where that price came from and when it was last checked.

Built for AEO/GEO work at Onomaris: deciding which model to use, and quoting
what a client engagement will actually cost to run.

## Running it

FastAPI + SQLite + Jinja2. Python 3.9, no Node, no build step.

```bash
git clone https://github.com/Awol313/AI-Cost-Catalog.git
cd AI-Cost-Catalog
pip install -r requirements.txt
python run.py
```

Then open <http://127.0.0.1:8001>.

Port 8001, not 8000 — so it runs alongside the LLM Brand Visibility Tracker
without a clash.

The database builds itself from `data/catalog.json` the first time you start it.
There's no setup step to forget.

## What's in it

65 rows at last update, across:

- **LLM models** — input, output, and cache prices per million tokens, plus context window
- **Search grounding** — the per-search surcharges that are charged *on top of* tokens
- **Data / SERP APIs** — DataForSEO, Serper, SerpApi, Perplexity's standalone search
- **Subscriptions** — ChatGPT, Claude, Google AI, Perplexity seat pricing
- **Discounts and surcharges** — batch processing, regional endpoints, inference geography

Click any row's name to see its notes — the caveats that decide whether a number
is safe to put in front of a client.

## The confidence system

This is the part that matters, and it exists because of a real problem: most
vendor pricing pages could not be read directly when this catalog was built, and
the third-party sites that report pricing **contradict each other** — on prices,
and even on which models exist.

So no row claims more certainty than it has:

| Badge | Means |
|---|---|
| **Verified** | Read directly from the vendor's own pricing page. |
| **Unverified** | Best available third-party reporting. The vendor page wasn't reachable when captured. |
| **Disputed** | Sources materially disagree. Don't quote without checking the vendor page. |

Rows older than 45 days get a **stale** flag regardless of confidence.

Right now: **27 verified** (all Anthropic, read first-hand from
`platform.claude.com`), **29 unverified**, **9 disputed**.

The CSV export carries `confidence`, `last_checked` and `source_url` on every
line, so a price can't leave this app and land in a client document with its
provenance stripped off.

## Updating it

`data/catalog.json` is the source of truth. The SQLite database is a disposable
projection of it — reseeding replaces every row, so a refresh never leaves half-old
data behind.

To re-verify prices and flip rows from unverified to verified, see **[REFRESH.md](REFRESH.md)**.

After editing the JSON:

```bash
python -m app.seed
```

## Files

```
.
├── run.py                  # launcher (port 8001)
├── data/catalog.json       # the catalog — source of truth, edit this
├── data/catalog.db         # generated, gitignored
├── REFRESH.md              # how to re-verify prices
└── app/
    ├── main.py             # routes: browse, filter, sort, CSV export
    ├── models.py           # one flat Offering table
    ├── seed.py             # JSON -> SQLite
    ├── config.py           # labels, staleness threshold
    ├── templates/
    └── static/
```
