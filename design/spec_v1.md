# Break Check: build and demo spec

Demo: Fri 2026-10-02, 6:30 PM ET, Exa FDE demo round with Ryan Ahern. 30 minutes.

Nothing in this spec has been run with an API key yet. Every expected result below comes from the Sep 29 research: keyless MCP probes plus WebFetch checks on primary pages. Re-verify each row on its primary page on Wednesday before saying it out loud.

---

## 1. The customer, the end user, and the problem

1. **The customer.** A mid-size US asset manager (assume $100B to $200B under management, equities plus investment-grade bonds) buys security data from two licensed vendors and merges it into one "golden copy". The golden copy is the master record of every instrument its order system trades. The buyer is the Head of Investment Operations, who owns the data-vendor budget.
2. **The end user.** The security master analyst starts around 7 AM on a queue of "breaks". A break is a row where the two vendors disagree about something: a split ratio, an effective date, a new CUSIP (the 9-character US security identifier), or whether a bond has been redeemed.
3. **The job today.** Every break must be settled before the 9:30 AM open. The only real tiebreaker is the issuer's own announcement plus the exchange's or SEC's notice, which the analyst finds by hand. That takes an assumed 15 to 25 minutes per break.
4. **The cost of getting it wrong.** A wrong or late fix is expensive:
   - Load a 1-for-25 reverse split one day early, and that day's position is misstated by a factor of 25 in NAV (net asset value) and risk reports.
   - An order on a retired CUSIP rejects at the broker.
   - A redeemed bond stays "live" on the books.
5. **What Break Check does.** It puts both primary sources side by side in seconds, with a citation on every field. Plain code, not an AI model, decides whether they agree, and the analyst still approves every change.

## 2. The workflow today, and the step the applet replaces

1. **Overnight.** The golden-copy build merges Vendor A, Vendor B and the custodian file. Mismatches become exception tickets. *(Unchanged.)*
2. **7:00 AM.** The analyst opens the queue and sorts by impact: held positions first, then pending orders. *(Unchanged.)*
3. **Read the ticket.** The analyst reads both vendor values and the field in dispute. *(Unchanged.)*
4. **Search by hand.** Google, EDGAR and Nasdaq Trader, looking for the issuer's release and the exchange's alert while skipping re-posts and aggregators. **REPLACED:** two Exa calls, one per source type, with domains and a date window set in code.
5. **Read and reconcile.** The analyst reads both documents and works out what each "effective date" means (legal effective time vs first trading day on new terms). **MOSTLY REPLACED:** fields are extracted with a citation each, code compares them field by field and labels known patterns, and the analyst reads the two highlighted sentences to confirm.
6. **Write up.** The analyst pastes links into the ticket and writes a resolution note. **REPLACED:** code drafts the note from the grounded fields and their URLs.
7. **Fix and escalate.** The analyst loads the fix and escalates to whichever vendor was wrong. **Stays human.** The escalation note is drafted, with the evidence attached.
8. **Weeks later.** Audit asks what the firm knew when it loaded the fix. **NEW, optional:** an Exa Snapshot copy of each source as of the ticket's open time.
9. **The case no one catches.** Announced-but-not-yet-effective events (a bond call next month) are found only when a feed changes. **NEW, in production:** a daily early-warning job on held issuers (section 11).

The one step to name on the call: step 4, the manual search, is where the 15 to 25 minutes go. Steps 5 and 6 fall out of it.

## 3. The applet: screens and panels

It is a single Streamlit app.

**Sidebar (the presenter's controls)**
- **"Saved runs only"** toggle. It replays the frozen golden cache and makes no network calls.
- **"Simulate timeout"** toggle. It forces the timebox to fire on the next call.
- **Timebox seconds.** Default 12 for deep-lite, 8 for auto.
- **Free-form box.** Ticker or CUSIP, issuer name and event hint, for a live row that Ryan names.
- A permanent line: "Vendor records are mocked. Every page retrieved is live from Exa."

**Screen 1: Exception queue**

A table with columns: row, identifier, issuer, field in dispute, Vendor A value, Vendor B value, opened at. It holds five rows, all real September 2026 events with mocked vendor values:

| Row | Break | Why it is here |
|---|---|---|
| CDT (CDT Equity, Nasdaq) | 1-for-25 reverse split. Vendor A effective 2026-09-28, Vendor B 2026-09-29, both CUSIP 20678X700 | Hero row: legal vs market effective date |
| CTNT (Cheetah Net, Nasdaq) | 1-for-150. Vendor B has no new CUSIP; the exchange side came back stale | Stale-page repair with maxAgeHours 0 |
| IMMP (Immutep ADS, Nasdaq) | ADS ratio change from 1:10 to 1:200. Vendor B booked it as a 1-for-20 split of the ordinary shares | Booked on the wrong security line; new CUSIP 45257L207 is single-source. Re-verify before showing |
| BAC 06051GLX5 (Bank of America floating-rate senior notes due Sep 2027) | Redeemed Sep 15, 2026 per the issuer's Sep 4 newsroom release. Still outstanding in Vendor B | Fixed income: a bond that no longer exists |
| FITB 316773 DD9 (Fifth Third notes) | Redemption announced Sep 24 (8-K and release), redemption date Nov 1, 2026. Vendor A flags the call, Vendor B does not | Early warning: announced, not yet effective |

Backups for the free-form moment:
- New Fortress Energy, 1-for-50, effective Sep 14, Nasdaq alert #2026-654.
- VerifyMe (VRME), new CUSIP 92346X305.

Buttons: **Check** (one row) and **Run all** (batch).

**Screen 2: Break detail (the core screen)**

- **Top: the hypothesis panel.** The text is stored in rows.json so AJ can read it aloud. Example: "Both vendors agree on ratio and CUSIP but not the date. I expect the issuer's GlobeNewswire release and Nasdaq alert 683, both published in the 30 days before the break."
- **Two columns: "Issuer channel" and "Market channel"** (the exchange alert for listed stocks, the SEC filing for bonds). Each column shows:
  - A status badge: Live or Saved (with saved-at time), latency, costDollars and requestId.
  - The top result that passed the identity guard: title, domain, a source-class tag (issuer wire, issuer IR site, syndication mirror, exchange, SEC), Exa's publishedDate next to the date printed on the notice, and the highlighted sentences.
  - The extracted fields, each with a confidence chip (low, medium or high) and a clickable citation from output.grounding.
  - Expanders: "Request JSON" (the exact body sent) and "Filtered out by identity guard (n)" (other issuers' pages that came back and were dropped).
- **Comparison table:** field, issuer value, market value, Vendor A, Vendor B, verdict. The verdict comes from rules in compare.py. It is never a model judgment.
- **Ticket note:** a plain-code template with both citations and a Copy button.
- **Conditional buttons:**
  - "Re-fetch this page live" appears when a source reads as stale.
  - "Replay as of ticket open" re-runs with endPublishedDate set to the ticket's open time.

**Screen 3: Run all**

All five rows run in a thread pool of 4. Each row gets a status chip:
- Corroborated
- Explained difference
- Single-source field
- Stale source repaired
- Conflict, escalate

Totals at the bottom: calls, dollars, median and max latency.

**Screen 4: Under the hood**

- A call log (requestId, endpoint, type, latency, costDollars, live or cache).
- The Wednesday bake-off table: auto vs deep-lite on the same rows, with field accuracy, latency and cost.
- A Snapshot audit panel, cached and optional.
- The Monitor JSON for FITB, and a static production diagram.

## 4. Every Exa call

All calls go through the existing C:\Users\ajwal\Documents\exa-demo\app\exa_client.py, using raw HTTP (`requests`) with the `x-api-key` header.

Why raw HTTP and not exa-py (say this if asked): exa-py silently adds 10,000 characters of full text to `search()`, and adds text to `get_contents()` even when you ask for highlights. That bills a second content type on /contents and hides what was sent. exa-py also drops the per-URL error tags in `statuses`. With raw HTTP, the body on screen is exactly what went over the wire.

### Call 1: Issuer-channel evidence (live; runs in parallel with Call 2)

`POST https://api.exa.ai/search`

```json
{
  "query": "Press release from CDT Equity Inc. (Nasdaq: CDT) announcing a reverse stock split, with the split ratio, the effective date and time, the first day of split-adjusted trading, and the new CUSIP",
  "type": "deep-lite",
  "numResults": 10,
  "includeDomains": ["globenewswire.com", "prnewswire.com", "businesswire.com", "accessnewswire.com", "nasdaq.com/press-release", "finance.yahoo.com"],
  "startPublishedDate": "2026-08-29T00:00:00Z",
  "additionalQueries": ["CDT Equity reverse stock split new CUSIP 20678X700"],
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only announcements from CDT Equity Inc. (ticker CDT); ignore every other company. Copy dates and times exactly as the source writes them. If a later notice from the issuer updates an earlier one, use the later one. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": {
    "type": "object",
    "required": ["identifier_in_source", "event_type", "terms", "effective_as_stated", "market_effective_date", "new_cusip", "new_symbol", "source_notice_date"],
    "properties": {
      "identifier_in_source": {"type": "string", "description": "Ticker or CUSIP of the affected security, exactly as the source prints it"},
      "event_type": {"type": "string", "description": "One of: reverse split, forward split, ticker change, name change, ADS ratio change, redemption, tender offer, other"},
      "terms": {"type": "string", "description": "Split or ratio terms, or redemption price and amount, as stated"},
      "effective_as_stated": {"type": "string", "description": "Effective date and time exactly as the source writes it"},
      "market_effective_date": {"type": "string", "description": "YYYY-MM-DD of the first trading day on the new terms, or the redemption date for a bond, or not stated"},
      "new_cusip": {"type": "string", "description": "New CUSIP as stated, or not stated"},
      "new_symbol": {"type": "string", "description": "New ticker as stated, or not stated"},
      "source_notice_date": {"type": "string", "description": "YYYY-MM-DD printed on the notice itself"}
    }
  },
  "contents": {"highlights": {"query": "split ratio, effective date and time, first split-adjusted trading day, new CUSIP, redemption date, redemption price", "maxCharacters": 1000}}
}
```

**Bond variant (BAC, FITB).**
- The query becomes: "Press release from Fifth Third Bancorp announcing the redemption of its notes with CUSIP 316773 DD9, with the redemption date and redemption price".
- `includeDomains` adds the issuer IR site taken from the security master's issuer record (for example `newsroom.bankofamerica.com`).
- The event hint becomes "redemption".

Every body lives in rows.json with fixed dates (see the cache gotcha in section 5).

**Response fields used.**
- `results[].url, title, publishedDate, highlights`, shown and passed through the identity guard.
- `output.content`, the 8 fields.
- `output.grounding[{field, citations[{url,title}], confidence}]`, the per-field citation and confidence chip.
- `costDollars.total`, `searchTime` and `requestId`, for the ops panel.

**Expected latency and cost.**
- About 4 s for deep-lite plus about 2 s for outputSchema synthesis, so about 6 s. This is untested with a key.
- $0.012 at list. 10 results are included in the base price. costDollars is an estimate, and the first live call will show whether outputSchema adds anything.

**Why each parameter (what Ryan will probe).**
- **`type: deep-lite`.** The docs recommend deep types when outputSchema has 3 or more fields, and warn against using deep only because the output is JSON. This call has 8 fields and has to reconcile an announcement against a completion notice, so the recommendation applies. deep-lite is the lightest deep type, about 4 s, vs 4 to 15 s for deep.
- **The auto vs deep-lite question.** On Wednesday AJ runs auto and deep-lite on the same five rows and shows the measured table: field accuracy, latency and cost. That is the answer to "why not auto?". If auto matches deep-lite on every field, keep deep-lite for the live demo anyway and say the POC would test auto at production volume, because it is cheaper ($0.007).
- **`numResults: 10`.** Probes with 5 results missed CDT's alert. 10 is also the most the base price covers.
- **`includeDomains`, set in code from config.** The model and the user can never widen it. That is Ryan's own Pydantic AI fix. It holds issuer wires only. `finance.yahoo.com` is there only because Business Wire originals did not surface in the probes, and code tags it "syndication mirror", so a field sourced only from a mirror is flagged. sec.gov is deliberately not in the issuer channel, so the two channels stay independent.
- **`startPublishedDate`.** The break date minus 30 days. An older split at the same issuer cannot win.
- **No `endPublishedDate`** on the live path, because publishedDate is Exa's estimate and a mis-dated page could be cut. It is used only in the replay (Call 4).
- **`additionalQueries`.** A second search angle built from the row's identifiers. The spec says this field is for deep types only; confirm on Wednesday that deep-lite accepts it, and drop it if the call returns a 400.
- **`systemPrompt`.** Names the one issuer, says to copy dates verbatim, and says a later notice wins. The "later notice wins" rule matters for amended events.
- **`outputSchema`.** 8 properties at one level, inside the 10-property and 2-level limits. It has no citation or confidence fields, because Exa's docs say not to add them: grounding supplies them. Descriptions are used instead of enums, because enum support is untested.
- **`identifier_in_source`.** Lets code reject a record built from another company's page.
- **`source_notice_date`.** Exists because publishedDate is an estimate. In the probes, a Verizon release whose text says Aug 20 came back dated Sep 21, and Nasdaq OTU #2026-9, printed Aug 4, came back dated Aug 31.
- **`contents.highlights` with a query.** A model (the synthesis) and then a person both read excerpts, not whole pages. That is Ryan's default. There is no full text here.
- **No `maxAgeHours`.** A press release does not change after publication, so forcing a live crawl only adds latency. Freshness is used only in Call 3.
- **No `category`.** Not needed with a domain allowlist.

### Call 2: Market-channel evidence (live; in parallel with Call 1)

`POST https://api.exa.ai/search`

```json
{
  "query": "Nasdaq Equity Corporate Actions Alert for CDT Equity Inc. (CDT) announcing a reverse stock split and a CUSIP change, with the effective date",
  "type": "deep-lite",
  "numResults": 10,
  "includeDomains": ["nasdaqtrader.com"],
  "startPublishedDate": "2026-08-29T00:00:00Z",
  "additionalQueries": ["Nasdaq corporate actions alert CDT Equity CUSIP 20678X700"],
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only the exchange's corporate actions alert for CDT Equity Inc. (ticker CDT); ignore alerts for every other company. Copy dates exactly as written. Write not stated for any field the alert does not give. Never infer.",
  "outputSchema": "<identical to Call 1>",
  "contents": {"highlights": {"query": "effective date, split ratio, new CUSIP, new symbol", "maxCharacters": 1000}}
}
```

**Channel config by asset class** (channels.json):

| Asset class | Issuer channel | Market channel |
|---|---|---|
| Nasdaq-listed equity | issuer wires | `["nasdaqtrader.com"]` |
| NYSE-listed equity (no per-issuer alert source was found) | issuer wires | `["sec.gov"]` (8-K) |
| Corporate bonds | wires plus IR site | `["sec.gov"]` |

Expected results: FITB should show its Sep 24 8-K. BAC may find no 8-K, in which case it honestly shows "single source, issuer only".

**What code does next (evidence.py), before anything is shown as agreed:**
1. **Identity guard.** Keep a result only if its title or highlights contain the row's ticker as a whole word, or a CUSIP (spaces removed, uppercased), or the issuer's legal name. A name-only match gets an amber tag.
2. **Identifier check.** If `output.content.identifier_in_source` does not match the row's identifiers, the whole record is marked "wrong security" and not used.
3. **Citation check.** Every `output.grounding` citation URL must be inside that call's `includeDomains` and among the results that passed the guard. Otherwise that field is amber, "unverified", and left out of the ticket.

**Expected result** (per Sep 29 research; the alert text was checked with WebFetch): alert #2026-683, 1-for-25, effective Tuesday Sep 29, 2026, CUSIP 20678X700.

**Latency and cost:** about 6 s and $0.012, as for Call 1. It runs in parallel, so the wall time for the pair is roughly the slower of the two.

### Call 3: Stale-page repair (live; only when triggered)

**Trigger:** a market-channel highlight contains "Page Not Available", or every field comes back "not stated".

`POST https://api.exa.ai/contents`

```json
{
  "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
  "maxAgeHours": 0,
  "livecrawlTimeout": 12000,
  "highlights": {"query": "effective date, split ratio, new CUSIP, new symbol", "maxCharacters": 1000},
  "summary": {"query": "What corporate action does this alert announce, for which security, effective when, with what new CUSIP and symbol?", "schema": "<the same 8-property object as Call 1>"}
}
```

**Why.**
- Options sit at the top level on /contents, with no `contents` wrapper.
- `maxAgeHours: 0` forces a live fetch of this one page, instead of paying live-crawl latency on every search result. It controls how fresh the returned text is, not which pages exist.
- `livecrawlTimeout: 12000` follows the docs' advice of 12 to 15 s for slow sites.
- `summary` with `schema` re-extracts the fields from the repaired page. It comes back as a JSON string to parse, and the citation is the page itself.
- No `text` is requested, and raw HTTP means none gets added silently.

**Response fields used:**
- `results[0].highlights` and `results[0].summary`, parsed as JSON.
- `statuses[]` with `{status, source: cached|crawled, error.tag}`. The screen shows `source: crawled`. On failure it shows CRAWL_TIMEOUT or CRAWL_LIVECRAWL_TIMEOUT, keeps the stale copy flagged, and escalates.

**Measured on Sep 29 through the keyless MCP:** the default cache returned "Page Not Available" in 1.6 s. With maxAgeHours 0 and livecrawlTimeout 12000, the real alert came back in 3.1 s: 1-for-150, effective Monday Sep 28, new CUSIP 16307X400.

**Cost:** $0.001 for highlights plus $0.001 for the summary = $0.002. The summary part is untested with maxAgeHours 0; fall back to highlights only.

### Call 4: No-hindsight replay (pre-cached; live optional)

This is the Call 1 and Call 2 bodies plus `"endPublishedDate": "2026-09-28T11:30:00Z"` (7:30 AM ET on Sep 28, when the CDT ticket opened).

**Why:** it shows the evidence was knowable before the load. It is also exactly how the POC eval replays closed tickets with no hindsight.

**Caveat to say:** publishedDate is an estimate, so a mis-dated page can drop out. That is why this is the eval method and not the live default.

**Cost:** $0.024 for the pair.

### Call 5: Audit copy with Exa Snapshot (pre-run, cached, never live)

`POST https://api.exa.ai/contents`

```json
{
  "urls": ["<CDT GlobeNewswire release URL from Call 1>", "https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-683"],
  "snapshotAsOf": "2026-09-28T11:30:00Z",
  "highlights": {"query": "effective date, split ratio, new CUSIP"}
}
```

**Why:** this is the auditor's question, "what did each source say when we loaded it?".

**Rules and limits:**
- Snapshot is a research preview.
- It covers a rolling 5-month window.
- After 100 requests you have to talk to sales.
- It cannot be combined with `maxAgeHours`, `livecrawlTimeout`, `livecrawl` or `subpages`.
- It rejects deep types and `category`.
- A URL Exa had not stored by then returns `CONTENT_NOT_CACHED`. If either URL returns that, drop the panel.

**Cost:** $0.002. Budget about 5 Snapshot calls in total.

### Call 6: Production early warning (shown as JSON, not run live)

`POST https://api.exa.ai/monitors`

```json
{
  "name": "held-issuer watch: Fifth Third Bancorp",
  "search": {
    "query": "Fifth Third Bancorp press release or filing announcing a redemption, tender offer, exchange offer or other corporate action on its notes or preferred shares",
    "numResults": 10,
    "includeDomains": ["prnewswire.com", "businesswire.com", "globenewswire.com", "sec.gov"],
    "contents": {"highlights": true}
  },
  "trigger": {"type": "interval", "period": "1d"},
  "outputSchema": "<the Call 1 schema>",
  "metadata": {"team": "security-master", "issuer": "FITB"},
  "webhook": {"url": "https://<customer ticket bridge>/exa-monitor", "events": ["monitor.run.completed"]}
}
```

**Why:**
- It catches the FITB case (announced Sep 24, effective Nov 1) before any feed changes.
- The webhook must be public HTTPS, never localhost, so it cannot run inside a local demo.
- `webhookSecret` is returned only once.
- Runs can be up to 30 minutes late, which is fine for a daily watch.
- $0.015 per run.

**ZDR caveat.** The docs list zero data retention for Search, Contents and Agent only. Monitor queries name held issuers, so ask Exa whether Monitors are covered. If they are not, run the same body as a scheduled /search from the customer's own scheduler, which is ZDR-covered.

### Deliberately not used (say it)

- **/answer:** not covered by ZDR, and these queries reveal holdings. It also has no per-field grounding.
- **findSimilar:** deprecated.
- **livecrawl:** replaced by maxAgeHours.
- **neural and keyword types:** not in the current API.
- **Websets:** a separate paid plan, and the docs steer new work to Agent.
- **Agent API:** asynchronous, with no documented run time for the fixed efforts. It is reserved for an offline backfill (section 11).
- **category:** not needed with an allowlist, and Snapshot rejects it.

### Per-exception cost and latency summary

| Call | When | Latency | List cost |
|---|---|---|---|
| 1 + 2 in parallel | every exception | about 6 s wall time (untested) | $0.024 |
| 3 repair | only when stale | about 3 s (measured analog) | $0.002 |
| 4 replay | POC eval only | about 6 s | $0.024 |
| 5 Snapshot | audit, on demand | unknown | $0.002 |
| 6 Monitor | daily per watched issuer | async | $0.015 per run |

## 5. Reliability design

**Timebox, visible on screen.**
- Calls 1 and 2 run in a `ThreadPoolExecutor`, and the app waits with `concurrent.futures.wait(futures, timeout=12)`: 12 s for deep-lite, 8 s if the bake-off picks auto.
- A channel not back in time shows its golden cached run, badged "Saved run from Wed 9/30 14:02, reason: live call still running past 12 s". The other channel renders live. Partial results beat a spinner.
- A late live response is still written to the working cache when it lands.
- Timer text counts up next to each column, so the audience sees the timebox, not a hang.

**Hard timeouts under the timebox.**
- exa_client's `TIMEOUT_BY_TYPE`: auto 15 s, deep-lite 30 s, deep 45 s. Add an optional `timeout=` override to `call()`, `search()` and `contents()`.
- Call 3 uses 20 s (a 12 s live crawl plus overhead).
- Note: the requests timeout covers connect time and gaps between reads, not total elapsed time. That is why the executor wait is the real timebox.

**Retries.**
- 429 and 503 retry at most twice, honoring `Retry-After`, capped at 5 s. This already exists in exa_client.
- A 503 SERVICE_OVERLOADED is not billed.

**Error states shown to the user.** The envelope `source` drives a badge:
- **Green:** Live, with seconds, dollars and requestId.
- **Amber:** Saved run, with saved-at time and reason. Reasons: timeout, network, 429 after retries, 402 NO_MORE_CREDITS or API_KEY_BUDGET_EXCEEDED, and the like.
- **Red:** no live result and no saved run, with the reason.
- **/contents:** per-URL `statuses` tags are shown verbatim.
- **Identity guard:** fields it drops are amber, not hidden.

**Cached fallback: a frozen golden cache.**
- exa_client caches the last successful response by a hash of the exact body.
- Two gotchas follow:
  1. Every date in a body must be fixed in rows.json, never computed from `now()`, or Friday's bodies will not match Wednesday's cache.
  2. A Friday warm-up call that returns worse results would overwrite the good copy.
- So on Wednesday night, copy `cache/` to `cache_golden/`. "Saved runs only" and every timeout fallback read `cache_golden/`, and live calls write to `cache/`.

**How the presenter switches.**
- Sidebar toggle **"Saved runs only"** (keyboard: click it; it is at the top of the sidebar).
- The spoken line: "Exa is slower than my 12-second timebox right now, so I'm switching to Wednesday's saved run, labeled with its time. In production I'd check status.exa.ai and send Exa support this requestId."
- The **"Simulate timeout"** toggle runs the same path on purpose, for the 30-second failure drill.

**Pre-flight, Friday 5:45 PM.**
- Check https://status.exa.ai/summary.json.
- Run every row once live to warm the caches (not golden).
- Confirm credits and the per-key budget in the dashboard.
- Close the network-heavy apps.

**Security of the key.**
- It lives in `.env`, is read server-side only, and never goes into the browser. CORS would allow a direct browser call, which is exactly why the key stays server-side.
- Set a per-key budget (`budgetCents`) of $5 in the dashboard.

## 6. The three slides

**Slide 1. "7:40 AM: two vendors, one security, who is right?"**
- **Customer and user:** a US asset manager ($100B to $200B, equities and investment-grade credit). The buyer is the Head of Investment Operations; the user is the security master analyst, clearing the overnight exception queue before the 9:30 open.
- **Today:** each break where licensed feeds disagree needs primary-source evidence found by hand on Google, EDGAR and Nasdaq Trader. That is an assumed 15 to 25 minutes each, with links pasted into the ticket.
- **This week, for real:** CDT Equity's 1-for-25 reverse split. The issuer says effective Sep 28 at 5:00 PM ET, with split-adjusted trading from the Sep 29 open. Nasdaq alert #2026-683 says effective Tuesday Sep 29. Same CUSIP, two meanings of "effective".
- **What a wrong fix breaks:**
  - the position is misstated by the split factor in that day's NAV and risk reports;
  - orders on a retired CUSIP reject;
  - ownership-limit compliance rules divide by the wrong share count;
  - a redeemed bond (BAC 06051GLX5, redeemed Sep 15) stays open.

**Slide 2. "The tiebreaker is on the public web. Exa makes it a two-call step."**
- **Licensed feeds stay the system of record.** Bloomberg, LSEG, ICE and DTCC remain the source of truth. The exception exists because they disagree or lag, so neither feed can settle it.
- **The tiebreaker is the issuer's own words plus the exchange or SEC notice.** Break Check makes one Exa call per source type, with a domain allowlist and date window set in code, and gets fields back with a citation and confidence each.
- **Code compares, not a model.** It applies fixed rules (for example "legal effective after the close vs market effective at the open"). The analyst approves, and the ticket note is drafted with both links.
- **Enterprise fit:** these queries reveal holdings, so production runs under Zero Data Retention (available for Search and Contents, the only two endpoints used). Exa states SOC 2 Type II, with reports at trust.exa.ai. /answer is not used because ZDR does not cover it.

**Slide 3. "Impact, cost, and a two-week proof of concept"**
- **Analyst time** (assumptions to confirm): a $45K a year floor (12 breaks a day, 12 minutes saved each) to $126K base (20 breaks a day, 20 minutes saved each), at $75 an hour loaded. The larger value is avoided NAV errors and failed trades, priced from your own incident log.
- **Exa spend at list price:** about $0.025 per exception, so $76 to $126 a year. A daily early-warning watch on 300 held issuers is about $530 (scheduled search) to $1,640 (Monitors) a year.
- **POC:** replay 150 closed tickets as of each ticket's open time. Pass means all of these:
  - issuer source found for 90% or more
  - effective date and new identifier match the analyst's resolution for 95% or more
  - zero wrong-issuer citations
  - at most 1 high-confidence wrong field
  - median under 8 s
  - handling time halved in a one-week shadow
- **Questions for you:** how many corporate-action breaks a day need an outside check, and which NAV correction or failed trade last year traced back to one?

Everything on the slides is either a verified public fact (re-check on Wednesday), an Exa documented fact, or a number labeled as an assumption. There are no client names and no AJ volume claims.

## 7. Demo script, minute by minute

Every step follows the pattern: hypothesis, then action, then result, then the user's next step.

**0:00 to 1:00. Open.**
"I'll spend about six minutes on the customer, eleven on the live demo, five on impact and a POC plan, and leave the rest for questions. Interrupt me anywhere."

**1:00 to 4:00. Slide 1.**
Tell it as the analyst's morning: the queue, the 9:30 deadline, the CDT dates, the downstream breaks.
Credibility line: "At Charles River I supported the ops teams on the other side of this. When reference data was wrong, it busted trades, and the first question was always which provider caused it."
Say "the ops teams I supported". Never name clients.

**4:00 to 6:00. Slide 2.**
Deliver the thesis in one sentence: "Licensed feeds stay the record; Exa supplies the primary-source evidence for the exceptions they produce."
Say plainly: "The vendor records are mocked because I don't have a customer's security master. Everything retrieved is live."

**6:00 to 7:00. Screen 1, the queue.**
- **Hypothesis:** "For every row, the issuer has already said which value is right. The job is to find that sentence fast and prove it."
- **Action:** point at the five rows and the field in dispute.
- **Next user step:** the analyst picks the row with the most trading impact, CDT.

**7:00 to 10:30. Screen 2, CDT.**
- **Hypothesis (read from the panel):** "The analyst needs two independent sources, the company's words and the exchange's notice. So I send Exa two searches in parallel. Domains are fixed in code, the window starts 30 days back, highlights are aimed at ratio, date and CUSIP, and there's an eight-field schema. I'm using deep-lite because the docs recommend a deep type for schemas with three or more fields. On Wednesday I measured auto against it (open the bake-off table later). If Exa is doing its job, the left column shows the GlobeNewswire release and the right column shows Nasdaq alert 683 in about six seconds."
- **Action:** open "Request JSON" and walk through it in 30 seconds, then press Check.
- **Result:**
  - Ratio: corroborated.
  - CUSIP 20678X700: corroborated.
  - Effective date: issuer "September 28, 2026, at 5:00 pm, Eastern Time" vs Nasdaq "Tuesday, September 29, 2026". The verdict chip reads "Explained difference: legal effective after the close vs market effective at the open. Adjust positions for the Sep 29 open." Say: "That label is a fixed rule in compare.py, not the model."
  - Click both grounding links live so the room reads the sentences on globenewswire.com and nasdaqtrader.com.
  - Point at the confidence chips, the latency, $0.024 and the requestId.
- **Next user step:** "The analyst loads the split for Sep 29. Vendor A had Sep 28, so the drafted escalation goes to Vendor A with the Nasdaq link." Click Copy on the ticket note.
- **Optional 30 s:** toggle "Replay as of ticket open". "Same calls, with endPublishedDate set to 7:30 AM on Sep 28. Both sources were already public. In my paper-trading research system, the hardest rule was using only what was knowable on the date. Ops has the same question in an audit, and it's also how I'd run the POC eval."

**10:30 to 12:00. CTNT, the stale-page repair.**
- **Hypothesis:** "The exchange column should give me the 1-for-150 terms."
- **Action and result:** the saved run, labeled "recorded Sep 29", shows Exa's cached copy reading "Page Not Available". "Exa crawled this alert before Nasdaq filled it in. The app detected an empty page, so instead of paying for live crawls on every search, it re-fetches just this URL with maxAgeHours 0 and a 12-second crawl timeout." Click "Re-fetch this page live". statuses shows `source: crawled`, and the fields fill in: 1-for-150, effective Monday Sep 28, new CUSIP 16307X400.
- If the page is already fresh on Friday, say so. The re-fetch still runs live and proves the parameter.
- **Next user step:** load the new CUSIP and close the break.

**12:00 to 13:30. FITB, fixed income and early warning.**
- **Hypothesis:** "For a bond there's no exchange alert, so the market channel is SEC filings. I expect Fifth Third's Sep 24 8-K and release, with a Nov 1 redemption date."
- **Action:** press Check.
- **Result:** event type redemption, market_effective_date 2026-11-01, Vendor A matches.
- "This break exists five weeks before it would have caused a problem. That's the production case: a daily watch on held issuers (Call 6 JSON on the last screen)."
- **Next user step:** set the pending redemption in the golden copy and tell the PM.
- Mention the BAC row in one line: a floating-rate note redeemed Sep 15 that is still open in Vendor B.

**13:30 to 15:00. Ryan picks.**
"Name any recent Nasdaq split or ticker change." Type it into the free-form box and run it live.
- If the guard honestly returns "not found", say what you'd check next: widen the window, confirm the listing venue, look for the 8-K.
- Fallback suggestion: New Fortress Energy, 1-for-50, Sep 14, alert #2026-654.

**15:00 to 16:00. Run all and the failure drill.**
- Run all: five chips, total dollars and latency. The pool of 4 keeps deep calls well under 5 QPS.
- Toggle "Simulate timeout" and rerun CDT. One column goes amber with "Saved run from Wed, reason: past 12 s timebox", and the other renders live.
- Say: "Timebox, announce, fall back, and keep the requestId for support."

**16:00 to 17:00. Under the hood.**
- Show the bake-off table.
- Open evidence.py and point at the identity guard and the grounding-domain check: "Search finds, code verifies identity, the analyst decides."
- One line on raw HTTP vs exa-py.
- Show the known-limit line: publishedDate vs date printed on the notice, the Verizon and OTU examples.

**17:00 to 22:00. Slide 3.**
Walk through the arithmetic (section 8), the POC (section 9) and production (section 11) in three sentences.
Packaging line: "The same two calls can be one tool in your ops copilot or an MCP tool, with the domain list fixed in code and the model passing only the identifier."
Then ask the two discovery questions.

**22:00 to 30:00. Questions.**
AJ's questions for Ryan:
- "Do integrations like your Pydantic AI one start from a specific customer ask?"
- "Which verticals is NYC going after first?"
- "When an enterprise demo lands, what's usually the moment that does it?"

## 8. Business impact arithmetic

Every input is an assumption to confirm in discovery.

**Shared assumptions**
- 252 trading days a year.
- Loaded analyst cost $150K a year over 2,000 hours, which is $75 an hour.
- Review of the Break Check card takes 3 to 5 minutes.

**Floor case**
- 12 breaks a day need outside evidence, at 15 minutes each by hand vs 3 minutes to review, saving 12 minutes each.
- 12 x 12 = 144 minutes a day, which is 2.4 hours.
- 2.4 x 252 = 605 hours a year, about 0.3 of an analyst.
- 605 x $75 = **about $45K a year**.

**Base case (adds bond calls, tenders and ticker changes)**
- 20 breaks a day at 25 minutes by hand vs 5 minutes to review, saving 20 minutes each.
- 20 x 20 = 400 minutes a day, which is 6.7 hours.
- 6.7 x 252 = 1,680 hours a year, about 0.84 of an analyst.
- 1,680 x $75 = **about $126K a year**.

**Volume sanity check from the public web:** Nasdaq's equity corporate-action alert numbering reached #688 by Sep 25, 2026. That is about 3.7 alerts per trading day on one exchange alone, before NYSE, bonds and non-US lines.

**Error avoided (not in the totals):** a split loaded a day early misstates the position by the full split factor (25x for CDT) in that day's NAV and risk. The customer prices this from its own log. Illustration only: if one NAV or failed-trade investigation a quarter takes 40 staff hours, that is 160 hours, or $12K a year, before any reimbursement to the fund.

**Exa spend at list price**
- **Per exception:** two deep-lite searches ($0.024), plus an occasional $0.002 repair, is about $0.025.
- **Floor:** 3,024 exceptions a year is about $76.
- **Base:** 5,040 exceptions a year is about $126.
- **If the POC shows auto is as accurate:** $0.014 per exception.
- **Early-warning watch on 300 held issuers, daily:**
  - As scheduled auto searches: 300 x 252 x $0.007 is about $530 a year.
  - As Monitors: 300 x 365 x $0.015 is about $1,640 a year.
- **Total:** under $2K a year at list.

**The honest commercial read (say it if Ryan asks about revenue):** per-call spend is small by design. The account value is the Enterprise contract that ZDR requires, because the queries reveal holdings. After that, it grows through expansion:
- fund administrators and middle-office outsourcers running the same queue for many clients;
- fixed-income voluntary events (tenders, conditional calls);
- the onboarding backfill for a new fund's whole book.

## 9. Proof-of-concept plan

**Scope.**
- 2 weeks of offline eval plus a 1-week shadow run.
- US-listed equities and US corporate bonds only.
- Two channels per asset class, exactly as in the demo.

**Eval set.**
- 150 exception tickets closed in the last 90 days, where the analyst's final resolution is the ground truth.
- Each is replayed with `endPublishedDate` set to the moment the ticket opened, so the eval measures what was knowable then, with no hindsight.
- Run auto and deep-lite on the same set, and pick the type on accuracy per dollar.

**Success criteria.** All must pass:
1. An issuer-channel primary source passes the identity guard for 90% or more of tickets. A market-channel source (exchange alert or SEC filing) passes for 85% or more where one exists.
2. Event type, market effective date and new identifier match the final resolution for 95% or more of tickets with evidence.
3. Zero fields cited to the wrong issuer, enforced in code and audited by hand on a 30-ticket sample.
4. At most 1 high-confidence wrong field across the whole set.
5. Median wall time under 8 s per exception, p95 under 15 s.
6. Under 3 cents per exception at list price.
7. **Shadow week:** analyst handling time on live exceptions falls by 50% or more, measured from ticket timestamps with and without the card.

**Timeline.**
- Week 1: channel config from their security master (issuer IR sites), eval harness, first run.
- Week 2: tuning (queries, allowlists, rules), second run, readout.
- Week 3: shadow run and sign-off.

**Who signs off.**
- Head of Investment Operations (the business case).
- Security master team lead (accuracy judgments on disputed rows).
- CISO or InfoSec (vendor review).
- Procurement.
- On Exa's side: the AE for the contract and the FDE for the technical win.

**Security and data-retention answers.**
- **Zero Data Retention.** Enterprise-only, enabled per team. It covers Search and Contents, the only endpoints on the live path. It does not cover /answer (not used) or Websets (not used).
- **Monitors.** ZDR coverage is not stated in the docs. "I'll find out." Until then, production early warning uses scheduled /search.
- **What the queries contain.** Only public identifiers (ticker, CUSIP, issuer name), no client names or position sizes. The set of identifiers queried still reveals holdings, which is why ZDR is required and the POC should run on an Enterprise trial with ZDR, or on closed tickets the customer is comfortable sending.
- **Compliance.** Exa states SOC 2 Type II, with the report and DPA (data processing agreement) at trust.exa.ai.
- **Default retention for non-ZDR accounts** is not stated in the pages reviewed. Say "I'll find out" rather than guess.
- **Keys.** Server-side only, with a per-key `budgetCents` cap and rate limit set via the dashboard or the Team Management API.
- **Audit trail.** Every call logs requestId, costDollars and searchTime.

## 10. Honest limits

**What Exa does not replace**
- The licensed corporate-actions feeds or the golden-copy precedence rules.
- Custodian notices (SWIFT MT564 corporate-action messages), DTCC corporate-action data, and broker-only notices.
- Anything behind a login or paywall. Exa's crawler respects robots.txt and does not log in.
- The analyst's approval. Nothing auto-loads.

**What could go wrong**
- **Mis-estimated dates.** publishedDate is an estimate. Verizon's release (text: Aug 20) was dated Sep 21, and Nasdaq OTU #2026-9 (printed Aug 4) was dated Aug 31. Mitigation: `source_notice_date` is extracted and shown next to it, and the live path has no `endPublishedDate`. The exa-py comment that undated pages are excluded by date filters is unconfirmed.
- **Unstable ranking for per-issuer exchange alerts.** With 5 results, CDT's alert #683 was missed. Mitigation: numResults 10, additionalQueries, the identity guard, and every demo row in the golden cache.
- **Stale caches.** Exa's copy can be stale (CTNT). The repair fixes the text, but maxAgeHours does not make an unindexed page appear.
- **Coverage gaps.**
  - NYSE-listed names have no per-issuer alert source; the 8-K fallback applies.
  - Non-US issuers, municipal bonds (MSRB EMMA) and structured products were not checked.
  - Business Wire originals did not surface in the probes; the syndication mirror is tagged.
- **Extraction mistakes.** Model extraction can be wrong or merge two notices. Mitigation: grounding confidence, the identity and citation checks, the code comparison and the human review.
- **Untested until AJ has a key:**
  - deep-lite with an 8-field outputSchema;
  - additionalQueries on deep-lite;
  - summary with a schema on /contents together with maxAgeHours 0;
  - real latency.
  Each has a named fallback: auto, drop the field, highlights only, cache.
- **Snapshot** is a preview: 5-month window, 100 requests before sales, CONTENT_NOT_CACHED possible. It stays off the live path.
- **Competitors.** Parallel (Task, Extract) could approximate this, so the POC should allow a head-to-head. Never claim Exa is the only option.
- **Mocked rows.** The vendor disagreements are mocked and are labeled as such everywhere.
- **Small spend.** Per-customer Exa spend is small. The commercial case rests on the ZDR Enterprise contract and on expansion.

## 11. How this runs in production

**Pipeline**
1. The nightly golden-copy build writes exceptions to the customer's queue.
2. A small Break Check service (Python, server-side, inside their network) picks up each exception.
3. It reads the channel config for the asset class, runs Calls 1 and 2 under the ZDR team key, applies the identity guard and the comparison rules, and writes the evidence card, verdict and drafted note back to the ticket (ServiceNow or Jira) with the citation URLs.
4. The analyst approves; the golden copy is updated; the escalation goes to the wrong vendor.

**Early warning**
- For each held issuer, a daily job watches for announced-but-not-effective actions (Call 6). It uses Exa Monitors with a webhook to their ticket bridge (public HTTPS, verified with `webhookSecret`) once ZDR coverage is confirmed, or otherwise a scheduled /search from their own scheduler.
- New events open tickets weeks ahead, as in the FITB case.

**Agent and MCP packaging**
- Expose `break_check(identifier, event_hint)` as one tool in the customer's ops copilot. It can be a Pydantic AI tool or a tool on an internal MCP server.
- The domain allowlist, date window and schema are fixed in code from config. The model passes only the identifier.
- Highlights are the default output to the model.

**Bulk jobs**
- When a new fund is onboarded, check its whole book for pending events by running Exa Agent at a fixed effort (for example `low`, $0.025 per run) asynchronously, off the live path.
- Under ZDR, run data lasts only 10 minutes after a run ends, and `previousRunId` is unavailable. Persist `output.grounding` immediately.
- At higher volume, the Batch API (Enterprise beta) runs nightly bulk /search.

**Operations**
- Log requestId, costDollars and searchTime per call.
- Set per-key budgets and rate limits.
- Alert on the status.exa.ai components.
- Honor the rate limits: deep types at 5 QPS, /search at 10 QPS.
- Keep a weekly re-run of the eval set as a regression test.

## 12. Four-hour build plan and file layout

**Before the clock starts (AJ does this himself, about 10 minutes)**
- Create the Exa account and key at dashboard.exa.ai/api-keys.
- Put `EXA_API_KEY` in `C:\Users\ajwal\Documents\exa-demo\.env`.
- Set a $5 per-key budget.
- Complete onboarding for the $10 bonus.

**Timeboxed steps**

| Time | Step | Done when |
|---|---|---|
| 0:00 to 0:30 | `rows.json` (5 rows plus 2 backups, fixed dates, mocked vendor values, hypothesis text, identifiers) and `channels.json` (allowlists by asset class, source-class tags including the mirror). Add a `timeout=` override to exa_client `call/search/contents` | Bodies print and match section 4 exactly |
| 0:30 to 1:15 | `evidence.py`: build the bodies, run both channels in a thread pool with the timebox, identity guard, grounding-domain check, stale detector, repair call | CDT returns two guarded records live |
| 1:15 to 1:45 | `compare.py`: date, CUSIP and ratio normalizers; rules (corroborated, explained difference with the after-close rule, single-source, stale repaired, conflict, which vendor matches); `ticket.py` note template | Unit tests pass on cached CDT, CTNT and FITB responses |
| 1:45 to 2:45 | `app.py`: sidebar controls, queue, break detail, run-all, under-the-hood screens | The full click-path works in "Saved runs only" mode |
| 2:45 to 3:15 | Wednesday live bake-off: all rows with auto and with deep-lite (about 20 calls, under $0.30), the CTNT repair, the CDT replay, the Snapshot pre-run (2 calls). Fill the bake-off table, pick the type, then copy `cache/` to `cache_golden/` | Golden cache frozen; every row has a saved run |
| 3:15 to 3:45 | `slides/build_slides.py` with python-pptx: 3 slides from section 6, plain layout | Break_Check.pptx opens in PowerPoint |
| 3:45 to 4:00 | One full timed rehearsal, out loud, using the section 7 script; note any overrun | Under 17 minutes to the end of the demo |

**Cut list if time runs short (in this order)**
1. Snapshot panel.
2. Replay toggle (keep it as a POC slide line).
3. IMMP row.
4. Run-all screen (keep the failure drill on CDT).

**File layout**

```
C:\Users\ajwal\Documents\exa-demo\
  .env                      EXA_API_KEY (never committed, never shown)
  requirements.txt          streamlit, pandas, requests, python-dotenv, python-pptx (plotly optional)
  app\
    exa_client.py           existing: envelope, cache, retries; add timeout override and CACHE_DIR switch for golden
    app.py                  Streamlit entry: streamlit run app\app.py
    evidence.py             body builders, parallel channels, timebox, identity guard, grounding check, repair
    compare.py              normalizers and fixed comparison rules (no model)
    ticket.py               resolution and escalation note templates
    config\
      rows.json             exception rows with fixed dates, identifiers, mocked vendor values, hypothesis text
      channels.json         allowlists per asset class and channel, source-class tags (mirror flagged)
      monitor_fitb.json     Call 6 body, shown on the under-the-hood screen
  cache\                    working cache written by live calls
  cache_golden\             frozen Wednesday runs used by fallback and "Saved runs only"
  tests\
    test_compare.py         offline tests on golden responses (VCR-style replay, no API calls)
  slides\
    build_slides.py         python-pptx builder
    Break_Check.pptx
```
