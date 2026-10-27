# Refreshing the catalog

## Why this file exists

When this catalog was built, the machine it was built on could not reach the
pricing pages for OpenAI, Google, xAI, Perplexity, DataForSEO, Serper, SerpApi,
or anyone else. Only Anthropic's own documentation was reachable.

So everything non-Anthropic was filled in from third-party reporting — and those
sources **contradict each other**. Some list models that others don't mention at
all. That's why those rows are marked `unverified` or `disputed` rather than
quietly presented as fact.

**Your Mac can reach those pages.** A refresh run from there is what turns the
yellow and red badges green.

## The quickest way: hand it to Claude

Open Claude Code in this folder and paste this:

> Refresh `data/catalog.json` for **<provider name>**. Fetch their official
> pricing page, compare it against the rows currently in the file for that
> provider, and update them: prices, context windows, model status, and any
> models that are new or now retired. For every row you touch, set
> `confidence` to `verified`, set `as_of` to today's date, and set `source_url`
> to the exact page you read. If the page disagrees with what's in the file,
> tell me what changed rather than silently overwriting it. Don't touch rows
> for other providers. When you're done, run `python -m app.seed`.

Do one provider at a time. It keeps the diff readable and makes it obvious when
something has genuinely moved.

### Priority order

Work down this list — it's ordered by how wrong the data is likely to be and how
much it matters to your work:

1. **OpenAI** — all 5 model rows are `disputed`. The current lineup could not be
   established at all; sources disagree on both names and prices. Treat every
   OpenAI number in there as a placeholder.
2. **Perplexity** — `disputed`. One source reports Sonar moved into an "Agent API"
   on 2026-09-27 and the old model names are gone. If true, several rows need
   replacing, not editing. Directly relevant: the tracker queries Perplexity.
3. **Google** — the Gemini 3 grounding rate ($14 per 1,000 after 5,000 free/month)
   is well-attributed but unread. The 2.5-era rate is `disputed`. Grounding is the
   thing that drives your per-run cost, so it's worth getting exact.
4. **xAI** — best-supported of the unverified set, but Live Search pricing is
   `disputed` and billed *per source*, not per request.
5. **Data/SERP vendors** — all `unverified`, and mostly sourced from blogs written
   by competing vendors. Check the vendors' own pages before committing spend.
6. **Subscriptions** — lowest stakes, easy to confirm.

## Re-verifying Anthropic

Anthropic rows came from
<https://platform.claude.com/docs/en/about-claude/pricing> on 2026-10-26 and are
`verified`. Re-read that page when the 45-day stale flag appears.

## Editing by hand

Each row in `data/catalog.json` looks like this:

```json
{
  "provider": "Anthropic",
  "name": "Claude Opus 5.5",
  "model_id": "claude-opus-5-5",
  "kind": "llm_model",
  "status": "current",
  "context_window": 1000000,
  "max_output": 128000,
  "price_input": 4.0,
  "price_output": 20.0,
  "price_cache_write_5m": 5.0,
  "price_cache_write_1h": 8.0,
  "price_cache_read": 0.2,
  "confidence": "verified",
  "source_url": "https://platform.claude.com/docs/en/about-claude/pricing",
  "as_of": "2026-10-26",
  "notes": "..."
}
```

Field rules:

- **Token prices** (`price_input`, `price_output`, `price_cache_*`) are USD per
  **million** tokens. Use them for `kind: "llm_model"`.
- **Everything else** uses `unit_price` + `unit_label` — a number and its unit in
  words, e.g. `10.0` and `"per 1,000 searches"`, or `19.99` and `"per month"`.
  Percentages go in as plain numbers with `"percent"` in the label.
- `kind` is one of: `llm_model`, `grounding`, `data_api`, `subscription`, `tool`,
  `discount`, `surcharge`.
- `status` is one of: `current`, `preview`, `legacy`, `deprecated`, `retired`,
  `limited`.
- `confidence` is one of: `verified`, `unverified`, `disputed`.
- Anything not applicable should be `null`, not `0` — `0` means genuinely free
  (as with Anthropic's web fetch tool), and the app shows those differently.

Then reload the database:

```bash
python -m app.seed
```

## Three things worth remembering when you refresh

These cost more money than headline token prices do, and they're easy to miss:

1. **Grounding surcharges stack on top of tokens, twice.** The per-search fee is
   the small part. The retrieved page content is billed as input tokens — in that
   turn *and* in every later turn of the conversation. This is the mechanism
   behind the tracker's jump from ~$0.16 to ~$1–1.20 per run.
2. **Tokenizers change between model generations.** Anthropic's 4.7-and-later
   models produce roughly 30% more tokens for the same text than 4.6 and earlier.
   A model with an identical headline rate can cost 30% more per actual page of
   text. Same-price is not same-cost.
3. **Prompt-size tiers flip silently.** Claude Haiku 5.5 jumps 5x above 100K
   tokens; Grok 4.7 doubles at 200K; Gemini 3.1 Pro nearly doubles above 200K.
   The model ID doesn't change, so nothing warns you — the bill just goes up.
