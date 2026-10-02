# Break Check

A small Streamlit app for a security master analyst. Two licensed data
vendors disagree about a security (a split date, a new CUSIP, whether a
bond was redeemed). Break Check makes one Exa search per source type, gets
structured fields back with a citation per field, and then plain code
(never a model) compares the sources and the vendor values and labels the
row. The analyst approves; a ticket note is drafted with the links.

Vendor A and Vendor B values are MOCKED. Every source page is retrieved
by Exa, live or from a labeled saved run.

## Watchlist scan: "Find what our feeds missed"

The first tab. A mocked watchlist (`data\portfolio.json`: 10 securities,
holdings, open orders, and a mocked Vendor A and Vendor B record for
each) is scanned with one Exa search per security. The query asks for
any recent corporate action by that issuer and never names the event.
Code then matches each event to a holding (identity guard reused from
`evidence.py`), compares it with both vendor records and gives one of
four statuses: "Absent from both vendor records", "Present at one vendor
only", "Both vendors have it", "Nothing found (not proof nothing
happened)". Each finding shows the source passage, the extracted fields
and the proposed action side by side, and a mocked "What the analyst
sees next" panel. Holdings never go to Exa. Domain setting: the approved
list (wires, nasdaqtrader.com, sec.gov, issuer newsrooms), chosen by a
probe on 2026-10-02; see the Under the hood tab.

## Run it

```
cd C:\Users\ajwal\Documents\exa-demo
streamlit run app\app.py
```

The Exa key must be in `.env` as `EXA_API_KEY=...`. It is read on the
server only and is never shown, logged or written anywhere else.

## Saved runs (no network)

In the sidebar, switch on **Saved runs only**. Every call then replays
the saved answer for that exact request body, reading `cache_golden\`
first and `cache\` second, and makes no network call. Each column says
"Saved run from <date> (golden folder)" so nobody mistakes it for live.

The same fallback happens automatically when a live call fails or runs
past the timebox, with the reason shown on screen.

- `cache_golden\` holds the frozen, known-good runs. The app never
  writes to it.
- `cache\` is the working folder. Every live success is saved there.

## Sidebar controls

- **Saved runs only**: replay saved runs, no network.
- **Simulate timeout**: holds the market channel back 20 seconds inside
  its worker thread, so the real timebox path runs. The screen returns
  at the timebox with the saved run and the reason.
- **Timebox seconds**: how long to wait for the pair of searches
  (default 8).

## Screens

1. **Break queue**: the rows, then one break in detail: presenter notes
   (hypothesis, action, expected result, what I check next), the label,
   the issuer and market channels side by side (status badge, ops line,
   Show request, top page, fields with status and citation, identity
   guard panel), the stale-page repair if one ran, the comparison table,
   the vendor check and the drafted ticket note with Approve.
2. **Free-form row**: type a ticker or CUSIP, issuer name, event type and
   asset class. The bodies are built from `data\channels.json` and run
   through the same path.
3. **Under the hood**: auto versus deep-lite from the saved runs, the
   session call log, the Exa Monitor body for production early warning
   (shown, never run) and the honest limits.

## Files

| File | What it does |
|---|---|
| `app\exa_client.py` | The only file that talks to Exa. Plain HTTP, one envelope shape for every call, retries on 429 and 503, golden-then-working cache fallback, safe writes to `cache\` only, a shared limiter (at most 4 calls in flight, starts 0.25 s apart), a timeout override, and /contents pricing. `python app\exa_client.py` checks the key. |
| `app\evidence.py` | Builds the request bodies from the two JSON files, runs both channels in parallel under the timebox, and checks the results in code: stale-page detector, identity guard, citation check, and the live re-fetch of a stale page. |
| `app\scan.py` | The watchlist scan: request bodies, the parallel run under the limiter and timebox, the portfolio matcher, the vendor comparison, the independent-source count and the downstream impact panel. |
| `data\portfolio.json` | The mocked watchlist, holdings, open orders and vendor records, plus the scan's query, systemPrompt, schema and approved domains. |
| `app\compare.py` | Normalizes values (CUSIP spacing, dates, split terms), compares issuer against market and both vendors against the evidence, gives the row one label, and drafts the ticket note. No model. |
| `app\app.py` | The Streamlit screens. |
| `data\rows.json` | The break queue: fixed query text, mocked vendor values, evidence window, and the four presenter notes per row. Live rows: ONMD, CDT, BAC, CTNT. Backups: AGRZ, NFE, JAGX, TRUG, IMMP. |
| `data\channels.json` | Approved domain lists per asset class, the issuer newsroom for BAC, the systemPrompt template, the output schema, and the templates for free-form rows. |
| `tests\` | Unit tests. No network: they read saved runs from `cache_golden\` and block any HTTP call. |
| `tools\probe.py` | The script used for the first live calls on 2026-09-29. |

## Tests

```
python -m unittest discover tests
```

`python -m pytest tests` also works.

## Labels

| Code | On screen |
|---|---|
| CORROBORATED | Corroborated by two independent sources |
| SAME_ISSUER | Same-issuer confirmation (the SEC copy is the issuer's own release) |
| SINGLE_ISSUER | Single source, issuer only |
| SINGLE_MARKET | Single source, exchange or SEC only |
| CONFLICT | Conflict between sources, escalate |
| STALE_REPAIRED | Stale source repaired, one source, analyst confirms |
| NOT_CONFIRMED | Not confirmed, route to analyst |
