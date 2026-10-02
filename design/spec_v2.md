# Break Check: build and demo spec (version 2)

Demo: Fri 2026-10-02, 6:30 PM ET, Exa FDE demo round with Ryan Ahern (technical go-to-market). 30 minutes. Expect him to open the code and ask why each parameter is set.

**Status of every result in this spec: UNVERIFIED.** Nothing has been run with an API key yet. Every expected result, latency and cost below comes from the Sep 29 research (keyless MCP probes, WebFetch checks on primary pages, and the red-team panel's own checks). Each one stays labeled "unverified until Wednesday" until AJ's keyed test on Wed 9/30 confirms it. Re-verify each row fact on its primary page before saying it out loud.

**What changed from version 1, in one paragraph.** Both search calls now default to `type: "auto"`, with deep-lite as a measured challenger, because Exa's own guidance says to use a deep type only when one search cannot fill the schema. The request bodies were trimmed to what Exa's build guidance (the build-with-exa skill, version 0.2.0) allows: no restated defaults except `type: "auto"`, sent only so the bake-off bodies differ by one line (Exa's pages differ on whether to send it), bare highlights, retrieval intent only in the query, rules in the systemPrompt, a 5-field flat schema (inside the 1 to 5 root fields Exa's patterns page prefers; the reason is in section 4). The customer is now an asset manager whose index and total-market products really do hold small caps, with a 3 to 4 person team. Value leads with "breaks still open at 9:30". The live demo is three scenes, each narrated as hypothesis, action, result and "if it comes back different, I check X next". The replay is renamed and its leaks are named. The bond channel is labeled honestly. The timebox, limiter and cache folders are fixed so the reliability story actually holds.

---

## 1. The customer, the end user, and the problem

1. **The customer.** A US asset manager that runs index and total-market equity products alongside investment-grade credit (assume $100B to $200B under management; an assumption to confirm). Because its total-market products can hold nearly every listed US name, small-cap reverse splits like CDT's land in its book, and because it runs credit, bond calls do too. It buys security data from two licensed vendors and merges them into one "golden copy", the firm's master record of every instrument its order system trades.
2. **Who decides and who pays.**
   - **Economic champion:** the Head of Investment Operations, who owns the pre-open deadline and feels the cost of a late or wrong fix.
   - **Contract owner:** the market data or vendor management team, which holds data-vendor contracts.
   - **The gate:** InfoSec (information security), because the identifiers the firm looks up reveal what it holds.
   - **Expansion path, not the primary customer:** fund administrators and middle-office outsourcers that run the same queue for many clients.
3. **The end user.** A security master analyst on a team of 3 to 4 who share one queue of "breaks". A break is a row where the two vendors disagree about something: a split ratio, an effective date, a new CUSIP (the 9-character US security identifier), or whether a bond has been redeemed.
4. **The job today.** The team starts around 7:00 AM and must settle every break before the 9:30 AM open. The only real tiebreaker is the issuer's own announcement plus the exchange's or SEC's notice, which an analyst finds by hand. That takes an assumed 15 to 25 minutes per break (to be checked against AJ's own measured baseline, section 8).
5. **The cost of a late or wrong fix.**
   - Load a 1-for-25 reverse split one day early, and price and quantity fall out of step by the split factor. That trips the NAV tolerance check (NAV is the fund's daily net asset value; the check flags big day-over-day moves) and costs an investigation on deadline, and possibly a late NAV.
   - An order on a retired CUSIP rejects at the broker.
   - A redeemed bond stays "live" on the books.
   - A break still open at 9:30 means the name is either held back from trading or traded on an unconfirmed record.
6. **What Break Check does.** It puts both primary sources side by side in seconds, with a citation on every field. Plain code, not an AI model, decides whether they agree, and the analyst still approves every change.

## 2. The workflow today, and the step the applet replaces

1. **Overnight.** The golden-copy build merges Vendor A, Vendor B and the custodian file. Mismatches become exception tickets. *(Unchanged.)*
2. **7:00 AM.** The team opens the shared queue and sorts by impact: held positions first, then pending orders. *(Unchanged.)*
3. **Read the ticket.** The analyst reads both vendor values and the field in dispute. *(Unchanged.)*
4. **Search by hand.** Google, EDGAR (the SEC's filing database) and Nasdaq Trader (Nasdaq's site for market notices), looking for the issuer's release and the exchange's alert while skipping re-posts and aggregators. **REPLACED:** two Exa searches, one per source type. The approved domain list is fixed in code, the evidence window is stated in the systemPrompt, and code checks the date printed on each notice.
5. **Read and reconcile.** The analyst reads both documents and works out what each "effective date" means (legal effective time vs first trading day on new terms). **MOSTLY REPLACED:** fields come back with a citation each, code compares them field by field and labels known patterns, and the analyst reads the two highlighted sentences to confirm.
6. **Write up.** The analyst pastes links into the ticket and writes a resolution note. **REPLACED:** code drafts the note from the grounded fields and their URLs.
7. **Fix, then decide who is wrong.** The analyst loads the fix, then decides whether the disagreement is a vendor error (escalate to that vendor) or the firm's own field mapping (fix the precedence rule). **Stays human.** The note is drafted with the evidence attached.
8. **Weeks later.** Audit asks what the firm knew when it loaded the fix. **NEW, optional:** an Exa Snapshot copy of each cited source as Exa had stored it at the ticket's open time.
9. **The case no one catches.** An announced-but-not-yet-effective event (a bond call next month) that neither vendor has picked up yet is found only when a feed finally changes. **NEW, in production:** a daily early-warning search on held issuers (section 11).

The one step to name on the call: step 4, the manual search, is where the 15 to 25 minutes go. Steps 5 and 6 fall out of it.

## 3. The applet: screens and panels

It is a single Streamlit app (`streamlit run app\app.py`).

**Sidebar (the presenter's controls)**
- **"Saved runs only"** toggle. It reads the frozen Wednesday runs in `cache_golden\` and makes no network calls.
- **"Simulate timeout"** toggle. It delays the next market-channel call by 20 seconds inside the worker thread, so the real timebox path runs (not a shortcut).
- **Timebox seconds.** Default 8 on auto, reset on Wednesday to about twice the measured 95th-percentile wall time for the pair (unverified until then); 12 only if deep-lite wins.
- **Free-form box.** Ticker or CUSIP, issuer name, listing venue and event hint, for a live row Ryan names.
- A permanent line: "Vendor records are mocked. Every source page is retrieved by Exa, live or from a labeled saved run."

**Screen 1: Exception queue**

Columns: row, identifier, issuer, field in dispute, Vendor A value, Vendor B value, opened at. Five rows, all real September 2026 events with mocked vendor values. Only CDT and FITB are on the spoken path; CTNT is conditional; BAC and IMMP are on screen only.

| Row | Break | Role in the demo |
|---|---|---|
| CDT (CDT Equity, Nasdaq) | 1-for-25 reverse split. Vendor A market-effective 2026-09-28, Vendor B 2026-09-29, both CUSIP 20678X700 | **Scene 1 (hero):** legal vs market effective date |
| FITB 316773 DD9 (Fifth Third Bancorp senior notes; coupon and maturity filled from the verified release on Wednesday) | Redemption announced Sep 24 (8-K and release), redemption date Nov 1, 2026. Vendor A shows the call, Vendor B does not | **Scene 2:** an ordinary break that happens to carry a future date, in fixed income |
| CTNT (Cheetah Net, Nasdaq) | 1-for-150. Vendor B has no new CUSIP | **Conditional:** stale-page repair, only if the stale detector actually fires live |
| BAC 06051GLX5 (Bank of America floating-rate senior notes due Sep 2027) | Redeemed Sep 15, 2026 per the issuer's Sep 4 release. Still outstanding in Vendor B | On screen only. Also the identity-guard test: the release covers two series |
| IMMP (Immutep ADS, Nasdaq) | ADS ratio change from 1:10 to 1:200. Vendor B booked it as a 1-for-20 split of the ordinary shares | On screen only. Keep or swap per decisions_for_aj |

Backups for Ryan's row (scene 3), if he has none in mind:
- New Fortress Energy, 1-for-50, effective Sep 14, Nasdaq alert #2026-654.
- VerifyMe (VRME), new CUSIP 92346X305.

Button: **Check** (one row).

**Screen 2: Break detail (the core screen)**

- **Top: the beat panel.** Four short texts stored per row in rows.json, so AJ reads his reasoning aloud instead of skipping it: hypothesis, action, expected result, and "if it comes back different, I check X next".
- **Two columns: "Issuer channel" and "Market channel".** For bonds the market column is labeled "SEC filing (issuer, legally filed)"; for NYSE names, "SEC filing, 8-K (issuer, legally filed)". For both, code shows "Same-issuer confirmation" when both citations carry the issuer's own text. Each column shows:
  - A status badge: Live (green), or Saved run (amber, with saved-at time and reason), latency, costDollars and requestId.
  - The top result that passed the identity guard: title, domain, a source-class tag (issuer wire, issuer IR site, syndication mirror, exchange, SEC filing), Exa's publishedDate next to the date printed on the notice, and the highlighted sentences.
  - The extracted fields, each with a confidence chip (low, medium or high) and a clickable citation from `output.grounding`.
  - Expanders: "Request JSON" (the exact body sent) and "Filtered out by identity guard (n)" (other issuers' pages that came back and were dropped, plus amber bare-ticker matches).
- **Comparison table:** field, issuer value, market value, Vendor A, Vendor B, verdict. The verdict comes from fixed rules in compare.py, never from a model.
- **Ticket note:** a plain-code template with both citations and a Copy button.
- **Conditional button:** "Re-fetch this page live" appears only when the stale detector fires.

**Screen 3: Under the hood (the 60-second tour and a place to answer questions)**

- **Call log:** requestId, endpoint, type, latency, costDollars, live or saved, and the `x-exa-queued` / `x-exa-queue-ms` headers (whether the request waited in Exa's rate-limit queue, and for how long).
- **Bake-off table** (from Wednesday): auto vs deep-lite on the same rows, identical bodies except `type`, with fields correct, fields "not stated", fields wrong, latency and cost. Next to it, the **manual baseline**: AJ's own minutes per row by hand (n=3, one person).
- **Run all** button: calls `run_row()` for one row at a time (never all rows submitted at once), so each row's two calls start together and its timebox measures real call time; every request still passes the shared limiter. Status chips (Corroborated, Same-issuer confirmation, Explained difference, Single-source field, Stale source repaired, Conflict, escalate) and totals (calls, live dollars, median and max latency).
- **Snapshot audit panel** (cached, pre-run on Wednesday, never live).
- **Early-warning JSON:** the scheduled /search body (the zero-data-retention path) and the Monitor body (the option for teams that accept non-ZDR), plus a static production diagram.

## 4. Every Exa call

All calls go through the existing `C:\Users\ajwal\Documents\exa-demo\app\exa_client.py`, as raw HTTP POST (`requests`) with the `x-api-key` header. exa_client passes the body through untouched, so the bodies below are exactly what goes over the wire. Nothing below has been run with a key: every latency, cost and result is unverified until Wednesday's keyed test.

**Why raw HTTP and not exa-py (say this if asked):** "exa-py's get_contents adds 10,000 characters of text whenever I don't pass text, summary or extras, even when I ask only for highlights. That bills two content types, and it drops the per-URL error tags. search() adds text only when you pass no contents. With raw HTTP, the body on screen is exactly what was sent." Exa's own build guidance treats raw HTTP as a first-class route and accepts either `x-api-key` or `Authorization: Bearer`.

**Rule for rows.json:** put an identifier in the query only when both vendors agree on it, so the query never leans toward one vendor's disputed value. Recency goes in the query as words ("September 2026"). Every date is fixed text in rows.json, never computed from `now()` (see the cache note in section 5).

### Shared schema (Calls 1 and 2; the Call 3 summary schema swaps one field, see Call 3)

Five flat fields. For a ticker-change row, code swaps `new_cusip` for `new_symbol` ("New ticker as stated, or not stated"). No citation, confidence or identifier fields: `output.grounding` already returns citations and confidence, and identity is checked by code against the cited page's own text.

```json
{
  "type": "object",
  "required": ["terms", "effective_as_stated", "market_effective_date", "new_cusip", "source_notice_date"],
  "properties": {
    "terms": {"type": "string", "description": "Split or ADS ratio, or redemption price and the series redeemed, as stated"},
    "effective_as_stated": {"type": "string", "description": "Effective date and time exactly as the source writes it"},
    "market_effective_date": {"type": "string", "description": "YYYY-MM-DD of the first trading day on the new terms, or the redemption date for a bond, or not stated"},
    "new_cusip": {"type": "string", "description": "New CUSIP as stated, or not stated"},
    "source_notice_date": {"type": "string", "description": "YYYY-MM-DD printed on the notice itself"}
  }
}
```

**Why five fields (the line):** "Five flat fields, and each one feeds exactly one rule in compare.py. Your guidance says prefer one to five root fields, so I cut three from my first draft: event_type, because the row already carries the event hint; new_symbol, because code swaps it in only on ticker-change rows; and identifier_in_source, because a model can echo the name I put in the prompt, so identity is checked by code against the cited page's text instead."

### Call 1: issuer channel, CDT (live; runs in parallel with Call 2)

`POST https://api.exa.ai/search`

```json
{
  "query": "CDT Equity Inc. (Nasdaq: CDT) reverse stock split press release, September 2026, new CUSIP 20678X700",
  "type": "auto",
  "includeDomains": ["globenewswire.com", "prnewswire.com", "businesswire.com", "accessnewswire.com", "nasdaq.com/press-release", "www.nasdaq.com/press-release", "finance.yahoo.com"],
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only announcements issued by CDT Equity Inc. (Nasdaq: CDT) about its reverse stock split, dated on or after 2026-08-29; ignore every other company and any earlier corporate action. Prefer the issuer's original release over a syndicated copy of it. If a later notice from the issuer updates an earlier one, use the later one. Copy dates and times exactly as the source writes them. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<shared 5-field schema above>",
  "contents": {"highlights": true}
}
```

Code tags `nasdaq.com/press-release`, `www.nasdaq.com/press-release` and `finance.yahoo.com` as syndication mirrors (sites that re-post the original release). Unverified until Wednesday: whether the bare `nasdaq.com/press-release` entry also matches the www host (both are listed until that is known).

**Bake-off arm (Wednesday only):** the identical body with only `"type": "deep-lite"`. Nothing else changes, so the table isolates the type.

**Why each parameter (what Ryan will probe):**
- **`query`: retrieval intent only.** It names the issuer, the event, the month and the CUSIP both vendors agree on. The field list lives in the schema and the rules live in the systemPrompt, as Exa's guidance says.
- **`type: "auto"`.** "Auto is Exa's default, and each call fills its fields from one page, so I started there. I ran the identical body on deep-lite and I only switch on measured field accuracy." (Say the second sentence only after Wednesday's bake-off has actually run. Until then say: "I'm testing the identical body on deep-lite and will switch only on measured field accuracy.") If deep-lite wins: "deep-lite filled N fields that auto left not stated on these rows, which is the more-than-one-search case your guidance names." `auto` is the default, so sending it is optional: "It's the default. I show it so the bake-off comparison is readable."
- **No `numResults`.** The server default is already 10. If asked: "I left it at the default of 10. My probes at 5 missed CDT's exchange alert, so I deliberately did not lower it."
- **`includeDomains`, fixed in code from channels.json.** "The allowlist is a compliance control the customer supplies and approves: primary wires, plus the issuer's IR site when their security master has one (FITB and BAC do; the CDT row has none), plus two tagged mirrors. It is fixed in code so neither the model nor the user can widen it. That's the point you raised in Pydantic AI issue 6082 about models putting domain filters into the query. The mirror entries are there because originals did not always surface in my probes, and code tags anything from a mirror, so a mirror-only field never counts as corroborated." sec.gov is deliberately not in the issuer channel, so the two channels stay separate.
- **No date filter on the live path.** "I don't use the date filter on the live path, because publishedDate is estimated and the filter drops undated pages. The window is in the systemPrompt, and code enforces it on the date printed on the notice." The probes showed why: a Verizon release whose text says Aug 20 came back dated Sep 21, and Nasdaq OTU #2026-9, printed Aug 4, came back dated Aug 31. Exchange alert pages are the likeliest to be undated. **Fallback:** if Wednesday shows an older CDT event crowding the results, restore `"startPublishedDate": "2026-08-29T00:00:00Z"` and say: "The ticket names one event, so a 30-day evidence window is a product rule, and I accept that it can drop an undated page because code also checks the printed date."
- **No `additionalQueries`.** Exa's API spec says it only works with the deep types, so on auto it would at best do nothing. The agreed CUSIP moved into the query. If deep-lite wins, `additionalQueries` gets tested later as its own arm, never in the same run as the type change.
- **`systemPrompt`.** Names the one issuer, holds the date rule, prefers the original release over a syndicated copy, lets a later notice win (this matters for amended events), copies dates verbatim, and writes "not stated" rather than guessing. Exa's guidance puts keep/drop rules and "what to do when a field cannot be verified" here, not in the query.
- **`outputSchema`.** The five fields above. Descriptions instead of enums, because enum support is untested.
- **`contents: {"highlights": true}`.** "On search, highlights anchor to my query already, and I have no token budget that needs a cap, so I didn't tune them." A model (the synthesis) and then a person both read excerpts, not whole pages.
- **No `maxAgeHours`.** A press release does not change after publication, so forcing a live crawl only adds latency. Freshness is used only in Call 3.
- **No `category`.** "Exa's guidance says category is only for explicit category-constrained retrieval, and the query already says what I want."

**Response fields used:** `results[].url, title, publishedDate, highlights` (shown and passed through the identity guard); `output.content` (the five fields); `output.grounding[{field, citations[{url,title}], confidence}]` (citation and confidence chip); `costDollars.total`, `searchTime`, `requestId`. Latency on screen is exa_client's `elapsed_ms` (end to end); `searchTime` is logged but can exclude the synthesis phase, per Exa's API spec.

### Call 1: issuer channel, FITB bond variant (live)

```json
{
  "query": "Fifth Third Bancorp press release announcing redemption of its senior notes, CUSIP 316773 DD9, September 2026",
  "type": "auto",
  "includeDomains": ["globenewswire.com", "prnewswire.com", "businesswire.com", "accessnewswire.com", "finance.yahoo.com", "ir.53.com"],
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only announcements issued by Fifth Third Bancorp about the notes with CUSIP 316773 DD9 (<coupon> due <maturity>, from rows.json), dated on or after <break date minus 30 days, from rows.json>. If a release covers several series, report only this series and ignore the others. Prefer the issuer's original release over a syndicated copy. If a later notice updates an earlier one, use the later one. Copy dates exactly as written. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<shared 5-field schema above>",
  "contents": {"highlights": true}
}
```

- `ir.53.com` comes from the security master's issuer record. For BAC, the same slot holds `newsroom.bankofamerica.com`. Both live in channels.json.
- **Bond identity key:** issuer, coupon, maturity, and the CUSIP when printed. Issuer redemption releases often name notes by coupon and maturity and leave out the CUSIP, and "FITB" is the stock ticker, not the bond's.
- Do not invent the coupon or maturity: fill them from the verified release on Wednesday.
- The series rule is in the systemPrompt because BAC's Sep 4 release covers two series (06051GLX5 floating and 06051GLV9 fixed/floating), and a separate BAC CAD-notes release uses the same "Due September 2027" wording. Code also rejects any record whose identifier is a different series.

### Call 2: market channel, CDT (live; in parallel with Call 1)

```json
{
  "query": "Nasdaq Trader equity corporate actions alert for CDT Equity Inc. (CDT) reverse stock split and CUSIP change, September 2026",
  "type": "auto",
  "includeDomains": ["nasdaqtrader.com"],
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only the exchange's corporate actions alert for CDT Equity Inc. (CDT), dated on or after 2026-08-29; ignore alerts for every other company. Copy dates exactly as written. Write not stated for any field the alert does not give. Never infer.",
  "outputSchema": "<shared 5-field schema above>",
  "contents": {"highlights": true}
}
```

Line: "The market channel is defined as the exchange's or the SEC's own notice, so the customer's channel config locks it to nasdaqtrader.com for Nasdaq names and sec.gov for bonds and NYSE names." Unverified until Wednesday: that bare host entries (`nasdaqtrader.com`, `sec.gov` and the wire domains) match their `www.` hosts. If one does not, add the www entry for that host.

### Call 2: market channel, FITB bond variant (live)

The channel label on screen is "SEC filing (issuer, legally filed)". For bonds, the 8-K exhibit is usually the issuer's own release filed again (FITB's 8-K Exhibit 99.1 is the same Sep 24 news release). So when both citations carry the issuer's own text, code shows **"Same-issuer confirmation"**, not "Corroborated".

```json
{
  "query": "Fifth Third Bancorp Form 8-K announcing redemption of senior notes, September 2026",
  "type": "auto",
  "includeDomains": ["sec.gov"],
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only SEC filings by Fifth Third Bancorp about the notes with CUSIP 316773 DD9 (<coupon> due <maturity>, from rows.json), dated on or after <break date minus 30 days, from rows.json>. If a filing covers several series, report only this series. Copy dates exactly as written. Write not stated for any field the filing does not give. Never infer.",
  "outputSchema": "<shared 5-field schema above>",
  "contents": {"highlights": true}
}
```

Say plainly: the truly independent sources for bonds (trustee or DTC notices) sit behind logins, which is exactly where the licensed feeds stay the source of truth.

**Channel config by asset class** (data\channels.json):

| Asset class | Issuer channel | Market channel (label) |
|---|---|---|
| Nasdaq-listed equity | issuer wires, mirrors tagged | `["nasdaqtrader.com"]` (Exchange alert) |
| NYSE-listed equity (no per-issuer alert source was found) | issuer wires, mirrors tagged | `["sec.gov"]` (SEC filing, 8-K (issuer, legally filed)) |
| Corporate bonds | wires plus the issuer's IR site from the security master, mirrors tagged | `["sec.gov"]` (SEC filing: issuer, legally filed) |

**Expected for the Call 1 plus Call 2 pair on auto (unverified):** about 1 s search plus about 2 s synthesis per call, so roughly 3 s of wall time in parallel. Cost $0.007 per call at list, $0.014 for the pair (unverified). Exa's API spec prices /search dynamically between $0.007 and $0.015 and has a costDollars.summary line for synthesized output, so the first live `costDollars` shows whether outputSchema adds to it. The timebox is 8 s.

**Expected results (unverified until Wednesday; the text of each was checked with WebFetch on Sep 29):**
- CDT market: Nasdaq alert #2026-683 (issued Fri Sep 25): 1-for-25, effective Tuesday Sep 29, 2026, CUSIP 20678X700.
- CDT issuer: the release says effective "September 28, 2026, at 5:00 pm, Eastern Time", with split-adjusted trading from Sep 29.
- FITB: the Sep 24 8-K and release, CUSIP 316773 DD9, redemption Nov 1, 2026. Nov 1, 2026 is a Sunday, so expect business-day wording; compare.py flags a weekend date rather than guessing the payment convention.
- BAC may find no 8-K, in which case it honestly shows "Single-source field, issuer only".

**What code does next (evidence.py), before anything is shown as agreed. Order matters:**
1. **Stale detector, on the raw results, before the identity guard.** A "Page Not Available" placeholder contains no ticker, so the guard would otherwise drop it before the detector sees it. It fires when a market-channel result URL matches `nasdaqtrader.com/TraderNews.aspx?id=ECA` and its highlights contain "Page Not Available" or are empty. The URL it passes to Call 3 comes from these raw results, which also gives a free-form row a URL to repair.
2. **Identity guard on results.** Keep a result only if its title or highlights contain an exchange-prefixed ticker ("Nasdaq: CDT", "NASDAQ:CDT", "Symbol: CDT"), a CUSIP (spaces removed, uppercased), or the issuer's legal name. For a bond: the issuer's name plus either the CUSIP or the coupon and maturity. A bare ticker match is amber only, because "CDT" is also Central Daylight Time and appears in many wire releases ("10:00 a.m. CDT").
3. **Grounding check: the primary identity guard.** For every field, each `output.grounding` citation URL must be inside that call's `includeDomains`, must be among the results that passed step 2, and the cited page's own title or highlights must contain the identifier, checked by code against the retrieved text. A field that fails goes amber, "unverified", and stays out of the ticket note. Unverified until Wednesday: whether bare highlights on nasdaqtrader alert pages include the issuer's name or CUSIP. If CDT's correct citations fail this check, the fallback is one /contents call on the cited URL with highlights `{"query": "<legal name> <CUSIP>"}` ($0.001, inside the timebox), and the check reads that text.
4. **Window check.** compare.py drops any record whose `source_notice_date` (the date printed on the notice) is before the row's window start.
5. **Repaired fields.** A Call 3 record has no grounding and no highlights. Code checks that the URL is the one the stale detector took from this row's raw results, runs the identity check on the repair (below, under Call 3), and checks that the parsed `new_cusip`, if stated, is a valid 9-character CUSIP. The chip reads "Stale source repaired, one source: fields from Exa's page summary, page link is the citation, analyst confirms", and the fields never count as corroborated until the analyst opens the link.

### Call 3: stale-page repair (live, only when the stale detector fires)

`POST https://api.exa.ai/contents`. Code takes the URL from Call 2's raw results, before the identity guard runs.

```json
{
  "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
  "maxAgeHours": 0,
  "livecrawlTimeout": 12000,
  "summary": {
    "query": "What corporate action does this alert announce, for which security, effective when, and with what new CUSIP?",
    "schema": "<repair schema: the shared 5 fields with identifier_in_source in place of effective_as_stated>"
  }
}
```

**Why each parameter:**
- **Top-level options, no `contents` wrapper.** On /contents, text, highlights and summary are top-level fields; on /search they sit inside `contents`. A good 10-second talking point on the shape difference.
- **`maxAgeHours: 0`.** "Code fires this only when Exa's stored copy is a placeholder, so I pay for a live crawl on one known URL instead of on every search result. That's the content-must-be-current case in your freshness guidance." It controls how fresh the returned text is, not which pages exist.
- **`livecrawlTimeout: 12000`.** Exa's guidance says to set it whenever live crawling matters so a slow page cannot block the request. exa_client's timeout override is 20 s for this call, because the default for a body with no `type` is 15 s.
- **`summary` with the schema, and nothing stacked on it.** "On a known URL, /contents has no outputSchema, so a per-page summary with my schema is the one content type I buy, to get the same fields compare.py needs. Nothing is stacked on it, and the page link is the citation." The summary comes back as a JSON string that code parses.

**Response fields used:** `results[0].summary` (parsed as JSON), and `statuses[]` with `{status, source: cached|crawled, error.tag}` read verbatim. The screen shows `source: crawled`, or on failure CRAWL_TIMEOUT or CRAWL_LIVECRAWL_TIMEOUT, keeps the stale copy flagged, and escalates to the analyst.

**The repair schema.** Still five root fields. Code swaps `effective_as_stated` for `identifier_in_source` ("Ticker, CUSIP, or issuer name exactly as the alert prints them"). The repair only ever serves the market channel, where compare.py uses `market_effective_date`; the verbatim effective time is used only on the issuer side. (A design choice made while merging the red-team fixes: AJ to confirm.)

**Identity check on the repair.** Code compares the parsed summary's identifier_in_source with the row's CUSIP, exchange-prefixed ticker and legal name. The check means something here because the summary query names no issuer, so the model has nothing to echo. If they do not match, the repair is discarded and the break goes to the analyst with the link. Repaired fields get the chip "Stale source repaired, one source" and never count as corroborated until the analyst opens the link.

**Fallback body if summary plus `maxAgeHours: 0` fails on Wednesday** (still one content type, no maxCharacters; the object form with a query is the recommended form on /contents, where there is no search query to anchor to):

```json
{
  "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
  "maxAgeHours": 0,
  "livecrawlTimeout": 12000,
  "highlights": {"query": "effective date, split ratio, new CUSIP, new symbol"}
}
```

**What was seen on Sep 29, through the keyless MCP only (not through this app, not recorded by exa_client):** Exa's stored copy of CTNT alert #2026-677 was a "Page Not Available" placeholder (1.6 s). With maxAgeHours 0 and livecrawlTimeout 12000 the real alert came back in 3.1 s: 1-for-150, effective Monday Sep 28, new CUSIP 16307X400. Say "Exa's stored copy was a placeholder page", never "Exa crawled this before Nasdaq filled it in". WebFetch already returns the full alert text, so Exa may have refreshed its copy by Wednesday.

**Cost:** $0.001 to $0.002 at list for the one page (Exa lists a per-content-type contents price and a separate AI page summary price; which applies is unverified), plus any live-crawl charge, shown by the first live `costDollars`.

### Call 4: publication-date-bounded replay (pre-cached; live optional; used in answers and in the POC)

This is the corrected Call 1 or Call 2 body plus one field. Example for Call 2:

```json
{
  "query": "Nasdaq Trader equity corporate actions alert for CDT Equity Inc. (CDT) reverse stock split and CUSIP change, September 2026",
  "type": "auto",
  "includeDomains": ["nasdaqtrader.com"],
  "endPublishedDate": "2026-09-28T11:30:00Z",
  "systemPrompt": "<same as Call 2>",
  "outputSchema": "<shared 5-field schema above>",
  "contents": {"highlights": true}
}
```

`2026-09-28T11:30:00Z` is 7:30 AM ET on Sep 28, when the CDT ticket opened (a mocked time, fixed in rows.json).

**The line:** "The replay's whole question is what was published before the ticket opened, so it's a bounded window that must be enforced. I call it a publication-date-bounded replay, not no-hindsight, because page content and ranking are still today's. Snapshot is the stricter check."

Optional add-on (AJ decides): "In my paper-trading research system, the hardest rule was using only what was knowable on the date. This replay only partly meets that rule, which is why I name its leaks." Say "paper-trading research system", never "production", and skip feed and test counts.

**Its leaks, named out loud:**
1. The page text, highlights and synthesis come from Exa's current stored copy, not the copy that existed at 7:30 AM.
2. Ranking uses today's signals.
3. publishedDate is an estimate, so a mis-dated page can drop out or slip in, and an undated page drops out.

**The strict point-in-time check** is a Snapshot arm: the same body on type auto with `"contents": {"highlights": true, "snapshotAsOf": "<ticket open time>"}`. Snapshot pins the text to Exa's stored version at or before that time; it bounds content, not ranking. It supports auto, fast and instant only, never with `maxAgeHours`, `livecrawl`, `livecrawlTimeout`, `subpages` or `category`. It is unverified whether it combines with `outputSchema` and `includeDomains`, and it falls under the 100-request Snapshot limit, so beyond a demo it is part of the enterprise trial ask (section 9).

Before ever saying "both sources were already public at 7:30 AM Sep 28", check the date printed on alert #683 (reported issued Fri Sep 25) and on the CDT release, on Wednesday.

**Cost:** $0.014 for the pair on auto.

### Call 5: Snapshot audit copy (pre-run on Wednesday, cached, never live)

```json
{
  "urls": ["<CDT GlobeNewswire release URL from Call 1>", "https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-683"],
  "snapshotAsOf": "2026-09-28T11:30:00Z",
  "highlights": {"query": "effective date, split ratio, new CUSIP"}
}
```

- This is the auditor's question: "what did each source say when we loaded it?"
- `snapshotAsOf` is top level on /contents and is never sent with `maxAgeHours` or `livecrawl`.
- Check `statuses` for `CONTENT_NOT_CACHED` (Exa had no stored copy by then). If either URL returns it, the panel says so.
- If the stored nasdaqtrader copy is the placeholder, keep it and show it as the honest reason Snapshot exists, never as proof the alert was knowable.
- Limits to quote: a rolling 5-month window, 10 QPS (queries per second) on pay-as-you-go, and 100 Snapshot requests before a sales conversation. Do not call it a "research preview" unless Wednesday's re-check of Exa's docs finds that label.
- **Cost:** $0.002 at list (2 pages, one content type). Budget about 5 Snapshot calls in total.

### Call 6: early warning (shown as JSON on Screen 3, never run live)

**Production early warning under ZDR: a scheduled /search from the customer's own scheduler.** Exa's build guidance says Monitors are not ZDR, and these queries reveal holdings, so this is the default production path.

```json
{
  "query": "Fifth Third Bancorp announces redemption, tender offer or exchange offer for its notes or preferred shares",
  "type": "auto",
  "includeDomains": ["prnewswire.com", "businesswire.com", "globenewswire.com", "ir.53.com", "sec.gov"],
  "startPublishedDate": "<last successful run time minus 7 days>",
  "systemPrompt": "Report only actions announced by Fifth Third Bancorp on its own notes or preferred shares. Ignore every other issuer. Copy dates exactly as written. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<the Call 6 events schema below>",
  "contents": {"highlights": true}
}
```

`startPublishedDate` is justified here because the job's stated window is "new since the last run", and the 7-day overlap absorbs mis-dated pages. Code also dedupes by URL against tickets already opened.

**Monitor body: the option for teams that accept non-ZDR** (valid per Exa's OpenAPI spec, not created live):

```json
{
  "name": "held-issuer watch: Fifth Third Bancorp",
  "search": {
    "query": "Fifth Third Bancorp announces redemption, tender offer or exchange offer for its notes or preferred shares",
    "includeDomains": ["prnewswire.com", "businesswire.com", "globenewswire.com", "ir.53.com", "sec.gov"],
    "contents": {"highlights": true}
  },
  "trigger": {"type": "interval", "period": "1d"},
  "outputSchema": {
    "type": "object",
    "required": ["events"],
    "properties": {
      "events": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["identifier_in_source", "event_type", "terms", "market_effective_date", "source_notice_date"],
          "properties": {
            "identifier_in_source": {"type": "string", "description": "CUSIP, or coupon plus maturity, or ticker, as printed"},
            "event_type": {"type": "string", "description": "redemption, tender offer, exchange offer, or other"},
            "terms": {"type": "string", "description": "Price, amount and series, as stated"},
            "market_effective_date": {"type": "string", "description": "YYYY-MM-DD the action takes effect, or not stated"},
            "source_notice_date": {"type": "string", "description": "YYYY-MM-DD printed on the notice"}
          }
        }
      }
    }
  },
  "metadata": {"team": "security-master", "issuer": "FITB"},
  "webhook": {"url": "https://<customer ticket bridge>/exa-monitor", "events": ["monitor.run.completed"]}
}
```

**Why:**
- The line on ZDR: "Exa's own guidance says Monitors aren't covered by ZDR, and these queries reveal holdings, so under ZDR the daily watch runs as a scheduled search from the customer's scheduler."
- The allowlist gets the same compliance line as Call 1, including the issuer's IR site. Monitor search accepts no systemPrompt, type or date filters, so the issuer and series constraints go in the query, and the identity guard runs on the webhook payload.
- The schema is an events array of 5 fields (6 properties in total, inside the 10-property cap): "The webhook opens tickets, so it needs fields, and one daily run can find more than one event, so it's a short events array."
- No `numResults` (the default of 10 is not restated). `search`, not searchParams; `trigger`, not a schedule string.
- `metadata`: "Exa echoes it back in every webhook delivery, so the ticket bridge routes the run to the security-master queue and the right issuer without parsing the query."
- `webhook.events: ["monitor.run.completed"]`: "The bridge opens tickets only from finished runs, so it subscribes to nothing else; the default is all events."
- "Per Exa's API spec, a Monitor fetches only content since its last run and dedupes semantically on its own; the scheduled search does both in code, with the 7-day overlap and URL dedupe."
- The webhook must be public HTTPS, never localhost, so it cannot run in a local demo. `webhookSecret` is returned only once, at creation, and must be stored immediately. Runs can be up to 30 minutes late. $0.015 per run.

### Deliberately not used (say it)

- **Exa's answer endpoint (/answer):** "I need the result list itself so code can run the identity guard, and per-field grounding with confidence. /answer gives one answer with a citation list, and your guidance says to prefer search when the app needs the results." Never give "no ZDR" as the reason: Exa's pages disagree on whether it is covered.
- **findSimilar:** deprecated.
- **livecrawl:** replaced by maxAgeHours.
- **neural and keyword types:** not in the current API.
- **Websets:** for existing integrations only; Exa steers new work to the Agent API.
- **Agent API:** asynchronous (runs in the background), with no documented run time for the fixed efforts. Reserved for an offline backfill (section 11).
- **category:** "Exa's guidance says category is only for explicit category-constrained retrieval, and the query already says what I want." Snapshot also rejects it.
- **additionalQueries, numResults, highlight options, date filters on the live path:** covered under Call 1.

### Per-exception cost and latency summary (all unverified until Wednesday)

| Call | When | Latency | List cost |
|---|---|---|---|
| 1 + 2 in parallel (auto) | every exception | about 3 s wall time | $0.014 |
| 1 + 2 in parallel (deep-lite, only if it wins the bake-off) | every exception | about 6 s wall time | $0.024 |
| 3 repair | only when the stale detector fires | about 3 s (Sep 29 MCP analog) | $0.001 to $0.002 plus any live-crawl charge |
| 4 replay | answers and the POC eval | about 3 s | $0.014 |
| 5 Snapshot | audit, on demand | unknown | $0.002 |
| 6 scheduled search (ZDR path) | daily per watched issuer | about 3 s, off the live path | $0.007 per run |
| 6 Monitor (non-ZDR option) | daily per watched issuer | async | $0.015 per run |

## 5. Reliability design

**Timebox, visible on screen, that cannot block.**
- **One module-level thread pool, never a with-block.** `EXECUTOR = ThreadPoolExecutor(max_workers=4)` is created once at the top of evidence.py. Streamlit imports the module once per server process, so reruns reuse it. A `with ThreadPoolExecutor() as ex:` block is banned, because leaving the block waits for every thread to finish, which would silently turn the 8-second timebox into exa_client's 15-second request timeout plus retries.
- **A polling loop, not one long wait.** `run_row()` loops `concurrent.futures.wait(pending, timeout=0.5)` and calls an `on_tick` callback every half second, which updates `st.empty()` placeholders: a counting timer next to each column. The audience sees the timebox, not a hang.
- **At the deadline** (8 s on auto; 12 s only if deep-lite wins), for each channel not back, `run_row()` calls `exa_client.search(body, cache_only=True)` and sets `envelope["error"] = f"live call still running past {timebox_s} s"` on the envelope it gets back. That envelope's `source` ("cache" or "none") and `saved_from` ("golden" or "working") drive the badge, for example "Saved run from Wed 9/30 14:02, reason: live call still running past 8 s". The other channel renders live. Partial results beat a spinner.
- **The late thread is left alone.** Python cannot stop a running thread. It finishes when Exa answers or its own request timeout fires, writes its answer to `cache\` (never `cache_golden\`), and frees its limiter slot.
- **Shared limiter.** One `threading.BoundedSemaphore(4)` in exa_client wraps every live request, across rows and channels, and request starts are spaced at least 250 ms apart. So at most 4 calls are in flight and at most 4 start in any second. That keeps a Run all under the 5 QPS limit for deep types if deep-lite wins, and well under the 10 QPS limit for /search on auto. Spoken line: "A shared limiter keeps us under Exa's rate limits." Run all sends rows one at a time through run_row (each row's two calls in parallel), so no call waits on the limiter inside its own timebox.
- **Simulate timeout** delays the market-channel worker by 20 s before its real call, so the drill runs the same code as a real slow call. Wednesday's test also runs one genuinely slow call, not just the flag.

**Hard timeouts under the timebox.**
- exa_client's `TIMEOUT_BY_TYPE`: auto 15 s, deep-lite 30 s. The new `timeout=` override is used for Call 3 (20 s: a 12 s live crawl plus overhead).
- The `requests` timeout covers connect time and each gap between reads, not total elapsed time. That is why the polling loop, not the request timeout, is the real timebox.

**Retries.**
- 429 and 503 retry at most twice, honoring `Retry-After`, capped at 5 s. This already exists in exa_client.
- A 503 SERVICE_OVERLOADED is not billed.

**Error states shown to the user.** The envelope `source` drives a badge:
- **Green:** Live, with seconds, dollars and requestId.
- **Amber:** Saved run, with saved-at time, which folder it came from, and the reason: timebox, network, 429 after retries, 402 NO_MORE_CREDITS or API_KEY_BUDGET_EXCEEDED, and the like.
- **Red:** no live result and no saved run, with the reason.
- **/contents:** per-URL `statuses` tags are shown verbatim.
- **Identity guard:** dropped results and amber fields are shown, not hidden.

**Two cache folders.**
- `cache_golden\` is read-only: Wednesday's frozen known-good runs. Nothing in the app ever writes to it. "Saved runs only" and every fallback read it first.
- `cache\` is the working folder: every live success is written there. Fallback reads it second (useful for a row with no golden copy, such as a free-form row run earlier in the session).
- The cache key is a hash of the exact request body, so two gotchas follow:
  1. Every date and every piece of recency wording in a body is fixed text in rows.json, never computed from `now()`, or Friday's bodies will not match Wednesday's saved runs.
  2. A Friday warm-up that returns worse results can never overwrite the golden copy, because live calls write only to `cache\`.
- On Wednesday night, after the bake-off, copy `cache\` to `cache_golden\` once, then leave it alone.

**Exact changes to app\exa_client.py** (it keeps its envelope, retries and plain-HTTP design; these are additions):
1. **Folders.** Add `GOLDEN_DIR = PROJECT_DIR / "cache_golden"` next to `CACHE_DIR`. Give `cache_path(endpoint, body, folder=CACHE_DIR)` a folder argument (the hash is unchanged, so Wednesday's files keep their names).
2. **Read order.** In `call()`, load the fallback from `GOLDEN_DIR` first, then `CACHE_DIR`, and record which one in a new envelope key, `saved_from` ("golden" or "working"). `from_cache()` uses that record.
3. **Write target.** `_write_cache()` writes only to `CACHE_DIR`. It writes to a temp file named per thread, `path.with_name(f"{path.stem}.{os.getpid()}.{threading.get_ident()}.tmp")`, then calls `os.replace()` to move it into place, so a late thread never leaves a half-written file. The whole write is wrapped in `try/except OSError`. On failure the temp file is removed and the live envelope is still returned, with `cache_write_error` set, because a failed save must never turn a live success into a crash.
4. **Timeout override.** Add `timeout=None` to `call()`, `search()` and `contents()`. When it is None, keep today's `TIMEOUT_BY_TYPE` lookup (15 s for a body with no `type`).
5. **Shared limiter.** Add `import threading`, a module-level `_LIMIT = threading.BoundedSemaphore(4)`, and a start-spacing lock (at least 250 ms between request starts). Every attempt, including each retry, acquires `_LIMIT` and passes the spacing lock immediately before its own `requests.post()`, and releases `_LIMIT` as soon as that post returns or raises. No slot is held during a retry's `time.sleep()`.
6. **/contents pricing.** In `_envelope()`, when `costDollars` is missing and the endpoint is `/contents`, price it as `len(body.get("urls") or body.get("ids") or []) * max(1, sum(1 for k in ("text", "highlights", "summary") if body.get(k))) * 0.001`. The max(1, ...) covers Exa's default of full text when no content type is named. Today it wrongly falls back to the /search price of $0.007. /search keeps `PRICE_BY_TYPE`. Run all totals and the call log's dollar column sum `cost_dollars` only where `source == "live"`.
7. **Queue headers.** Copy `x-request-id`, `x-exa-queued` and `x-exa-queue-ms` from `resp.headers` into plain values: `queued = resp.headers.get("x-exa-queued") == "true"`, `queue_ms = int(resp.headers.get("x-exa-queue-ms") or 0)`. Store them in the cache record and pass them to `_envelope()` as new keyword arguments, so every envelope carries `queued`, `queue_ms` and `saved_from` (empty for live). The call log shows whether a request waited in Exa's rate-limit queue.
8. **Docstring.** Correct the module docstring's SDK sentence to the reworded exa-py reason in section 4 (search() adds text only when you pass no contents; get_contents adds text even with highlights). Update 'HOW ONE CALL FLOWS' to say the fallback reads cache_golden then cache, and add `saved_from`, `queued` and `queue_ms` to 'WHAT AN ENVELOPE LOOKS LIKE'.

**Pre-flight, Friday 5:45 PM.**
- Check https://status.exa.ai/summary.json.
- Run CDT and FITB once live to warm `cache\` (never golden).
- Run CTNT's Call 2 only, to see whether the stale detector fires. Never press the repair in pre-flight: it is unverified whether a live crawl refreshes Exa's stored copy for later searches, and that would erase the state the scene needs.
- Confirm credits and the per-key budget in the dashboard.
- Close the network-heavy apps.

**Security of the key.**
- It lives in `.env`, is read server-side only, and never goes into the browser. Exa's CORS settings (the browser rule for cross-site calls) would allow a direct browser call, which is exactly why the key stays server-side.
- Set a per-key budget (`budgetCents`) of $5 in the dashboard.

## 6. The three slides

**Slide 1. "7:40 AM: two vendors, one security, who is right?"**
- **Customer and user:** a US asset manager running index and total-market equity products alongside investment-grade credit (size is an assumption). A team of 3 to 4 security master analysts clears one shared queue of breaks (rows where the two licensed data vendors disagree) before the 9:30 open. The golden copy is the firm's master security record.
- **Today:** each break where the licensed feeds disagree needs primary-source evidence found by hand on Google, EDGAR (the SEC's filing database) and Nasdaq Trader (Nasdaq's notice site). That is an assumed 15 to 25 minutes each, with links pasted into the ticket. On a heavy day some breaks are still open at 9:30.
- **This week, for real:** CDT Equity's 1-for-25 reverse split (every 25 old shares become 1 new share). The issuer says effective Sep 28 at 5:00 PM ET, with split-adjusted trading from the Sep 29 open. Nasdaq alert #2026-683 says effective Tuesday Sep 29. Same CUSIP (the 9-character US security ID), two meanings of "effective".
- **What a wrong or late fix breaks:**
  - price and quantity fall out of step by the split factor, which trips the NAV check (NAV is the fund's daily net asset value) and costs an investigation on deadline, and possibly a late NAV;
  - orders on a retired CUSIP reject at the broker;
  - ownership-limit compliance rules divide by the wrong share count;
  - a redeemed bond (BAC 06051GLX5, redeemed Sep 15) stays open.

**Slide 2. "The tiebreaker is on the public web. Exa makes it a two-call step."**
- **Licensed feeds stay the system of record (the official source the firm books from).** Bloomberg, LSEG, ICE and DTCC (the US settlement and depository utility) remain the source of truth. The exception exists because they disagree or lag, so neither feed can settle it.
- **The tiebreaker is the issuer's own words plus the exchange or SEC notice.** Break Check makes one Exa search per source type, limited to a domain list the customer approves, and gets each field back with a citation and a confidence level.
- **Why Exa and not a scraper:** "For Nasdaq names you could scrape the alert page. The long tail of issuer investor-relations sites, bond redemptions and 8-K filings (a company's SEC report of a major event) is where one plain-language search beats a scraper per site." One call, answered while you wait, returns the page, the highlighted sentences and per-field citations with confidence.
- **Code compares, not a model.** It applies fixed rules (for example "legal effective after the close vs market effective at the open"). The analyst approves, and the ticket note is drafted with both links.
- **Enterprise fit:** these lookups reveal holdings, so production runs under Zero Data Retention (ZDR: Exa keeps nothing from the request). Search, which carries every routine lookup, is ZDR-covered in both Exa sources I read. The occasional one-page repair uses Contents, which one of those sources does not list, so I'd confirm it. Exa states SOC 2 Type II (an independently audited report on security controls), with reports at trust.exa.ai.

**Slide 3. "Impact, cost, and a proof of concept"**
- **First: breaks still open at 9:30.** Today, evidence-gathering can fill most of the team's pre-open window on a heavy day (section 8). With a 3 to 5 minute review per break (an assumption), the same team would clear the queue before the open on a base-case day; the POC shadow week measures it. The customer prices a late or wrong fix from its own incident log. Illustration only: one 40-hour NAV investigation a quarter is about $12K a year in staff time, before any reimbursement to the fund.
- **Second: analyst time** (assumptions to confirm): about $45K a year (floor) to $126K (base), at $75 an hour loaded cost (salary plus benefits and overhead). Next to it, AJ's measured manual baseline: n=3 rows, one person.
- **Exa spend at list price:** about $0.015 per exception on auto at list price (whether structured output adds to that is confirmed Wednesday), so under $100 a year for the queue. A daily early-warning watch on 300 held credit issuers is about $530 a year as scheduled searches. The point is not the spend: Break Check is the workload that takes Exa through security review and ZDR at an asset manager.
- **Proof of concept (POC: a trial to prove value before purchase):** a week-0 security review, a public-data eval that needs no holdings, then 150 of the customer's closed tickets once ZDR is on, then a shadow week (analysts use the card alongside today's process). Pass means all of these:
  - issuer source found for 90% or more
  - terms, market effective date and new identifier match the analyst's resolution for 95% or more
  - zero wrong-issuer citations
  - at most 1 high-confidence wrong field
  - median under 8 s
  - fewer breaks still open at 9:30, and handling time halved, in the shadow week
- **Questions for you:** how many breaks a day need an outside check, how many are still open at 9:30, and which NAV correction or failed trade last year traced back to one?

Every slide statement is a verified public fact (re-checked Wednesday), an Exa documented fact, or a number labeled as an assumption. No client names and no AJ volume claims.

## 7. Demo script, minute by minute

**Every beat has four parts, spoken out loud: hypothesis, action, result, and "if it comes back different, I check X next".** The hypothesis and the "if different" line are stored in rows.json and shown on the beat panel, so AJ reads his reasoning instead of jumping to the answer. Every expected result below is unverified until Wednesday.

**0:00 to 1:00. Open.**
"I'll spend about six minutes on the customer, eight on the live demo, five on impact and a POC plan, and leave the rest for questions. Interrupt me anywhere."

**1:00 to 4:00. Slide 1: the analyst's morning.**
Tell it as the team's morning: the shared queue, the 9:30 deadline, the CDT dates, what a wrong or late fix breaks.
Credibility line, exact scope: "At Charles River I was a FIX connectivity analyst for buy-side clients. When security reference data was wrong, trades busted, and I worked with our data services team to figure out which provider caused it. I didn't own the security master, but I saw what a bad record does downstream." Never name a client. Never say "always".

**4:00 to 6:00. Slide 2: the thesis.**
One sentence: "Licensed feeds stay the record; Exa supplies the primary-source evidence for the exceptions they produce."
The scraper answer, before he asks: the long tail of IR sites, bond redemptions and 8-Ks.
Say plainly: "The vendor records are mocked because I don't have a customer's security master. Every source page is retrieved by Exa, live or from a labeled saved run."

**6:00 to 6:45. Screen 1, the queue.**
- **Hypothesis:** "For every row, the issuer has already said which value is right. The job is to find that sentence fast and prove it."
- **Action:** point at the rows and the field in dispute; say BAC and IMMP are there to show the range, and we'll take CDT first because it has the most trading impact.
- **Result:** the analyst picks CDT.
- **If different:** if Ryan wants another row first, take FITB and come back to CDT.

**6:45 to 10:15. Scene 1: CDT (hero), with the failure drill as a second run.**
- **Hypothesis:** "The analyst needs two separate sources, the company's words and the exchange's notice, so I send Exa two searches in parallel. I'm on auto, Exa's default, because each call fills its fields from one page. I expect the GlobeNewswire release on the left and Nasdaq alert 683 on the right in about three seconds. If a field comes back not stated, I check the bake-off to see whether deep-lite filled it."
- **Action:** open "Request JSON" and walk it in 30 seconds: the query is intent only, the domain list is the customer's and fixed in code, the rules and the evidence window are in the systemPrompt, five schema fields, bare highlights. Press Check.
- **Result (expected, unverified):**
  - Ratio: corroborated. CUSIP 20678X700: corroborated.
  - Effective date: issuer "September 28, 2026, at 5:00 pm, Eastern Time" vs Nasdaq "Tuesday, September 29, 2026". The chip reads "Explained difference: legal effective after the close vs market effective at the open. Adjust positions for the Sep 29 open." Say: "That label is a fixed rule in compare.py, not the model."
  - Click both grounding links live so the room reads the sentences on the issuer's release and on nasdaqtrader.com.
  - Point at the confidence chips, the latency, about $0.014 and the requestId.
- **Next user step:** "Load the split for the Sep 29 open. Then check whether Vendor A's Sep 28 is their legal-effective date being mapped into our market-effective field. If so, it's our precedence rule to fix, not a vendor ticket." (Optional, true: "That's the same unmapped-field problem I built a pre-go-live harness for at Adroit.") Click Copy on the ticket note.
- **If different:**
  - One column empty or a field "not stated": open "Filtered out by identity guard" to see whether the right page came back and was dropped, then check the bake-off row for CDT.
  - A wrong-company page in a column: that means the guard failed; show the amber tag and say the citation check keeps it out of the note.
  - Slower than 8 s: the timebox fires on its own, which is the drill below, live.
- **Second run, the failure drill (45 s):**
  - **Hypothesis:** "If Exa is slow, the screen should switch that column to Wednesday's saved run at eight seconds and keep the other column live."
  - **Action:** toggle "Simulate timeout" and press Check again.
  - **Result (expected, unverified until Wednesday's timebox test):** the market column goes amber, "Saved run from Wed 9/30, reason: live call still running past 8 s"; the issuer column renders live. "Timebox, announce, fall back, and keep the requestId for support."
  - **If different:** if the page hangs past 8 s, the thread pool is blocking; I check that nothing waits on the executor with a with-block, and switch the sidebar to "Saved runs only" while I say so.

**10:15 to 12:15. Scene 2: FITB, the bond row.**
- **Hypothesis:** "For a bond there's no exchange alert, so the second channel is the SEC filing. For a redemption that filing is usually the issuer's own release filed again, so I expect the screen to say 'same-issuer confirmation', not 'corroborated'. I expect Fifth Third's Sep 24 release and 8-K, CUSIP 316773 DD9, redemption Nov 1."
- **Action:** press Check. Point at the bond identity key: issuer, coupon, maturity, and the CUSIP when printed.
- **Result (expected, unverified):** market_effective_date 2026-11-01, Vendor A matches, chip "Same-issuer confirmation". compare.py flags that Nov 1, 2026 is a Sunday, so the payment-date convention goes to the analyst. Say: "The truly independent bond sources, trustee and DTC notices, are behind logins, which is where the licensed feeds stay the source of truth."
- **Next user step:** set the pending redemption in the golden copy and tell the portfolio manager. "This one Vendor A already had. The production case is the one neither vendor has yet: a daily search on held issuers, which is on the last screen."
- **If different:**
  - The issuer channel finds only the Yahoo mirror: the chip says mirror-only, not corroborated, and I check whether ir.53.com is being matched.
  - The record names another series: the series rule and the identity check should reject it; I open the filtered list to confirm.
  - No 8-K: it shows "Single-source field, issuer only", which is the honest result.

**12:15 to 13:45. Scene 3: a row Ryan names.**
"Name any recent Nasdaq split, ticker change or bond redemption." Type it into the free-form box and run it live.
- **Hypothesis:** say it before pressing Check, in the same shape: "I expect the issuer's release on a wire and, for a Nasdaq name, the exchange alert, dated in the last month."
- **The Exa point, before pressing Check:** "This is the scraper question answered live. I have written no rule for this issuer's site. The same plain-language query and the same approved domain list find its release wherever it was posted." After the result, point at the source-class tag to show which wire or IR site it came from.
- **Action:** press Check.
- **Result:** whatever comes back, read the chips out loud.
- **If different:** if the guard honestly returns "not found", say what I'd check next: confirm the listing venue (an NYSE name uses the 8-K channel), widen the evidence window, look for the 8-K. Fallback suggestion: New Fortress Energy, 1-for-50, Sep 14, alert #2026-654.
- **Free-form row mechanics:** a free-form row's evidence window is computed from today's date. It has no saved run to match, so the cache-key rule does not apply. If different, a timeout: the column shows red, "no saved run", with the reason. Say: "That's the timebox doing its job; I'd rerun it once and otherwise hand the link search to the analyst."

**Conditional, 60 seconds taken from Slide 3 (which drops from five minutes to four): CTNT stale-page repair.** Only if the stale detector actually fires on Friday. If it does not fire, describe it in one sentence during the tour and do not stage it.
- **Hypothesis:** "The exchange column should give me the 1-for-150 terms. If Exa's stored copy is a placeholder, the app should notice and re-fetch just that one page live."
- **Action:** press "Re-fetch this page live".
- **Result (unverified):** `statuses` shows `source: crawled`, and the fields fill in: 1-for-150, effective Monday Sep 28, new CUSIP 16307X400.
- **If different:** a CRAWL_LIVECRAWL_TIMEOUT tag means Nasdaq was slow; the stale copy stays flagged and the break goes to the analyst with the link.

**13:45 to 14:45. Under the hood, 60 seconds.**
- **Hypothesis:** "If the design is sound, you should be able to see every call's cost and timing, the measured reason I'm on auto, and the code that decides identity."
- **Action:** open the call log, the bake-off table with the manual baseline beside it, one line of evidence.py ("Search finds, code verifies identity, the analyst decides") and the early-warning JSON ("Scheduled search under ZDR; Monitors for teams that accept non-ZDR"). Run all, the Snapshot panel and the replay stay here for questions.
- **Result (expected, unverified until Wednesday):** two calls per exception at about $0.007 each and about 3 s wall time, queue headers showing no wait, and the bake-off row that shows why the default is auto.
- **If different:** if the bake-off showed deep-lite winning, say so with the measured numbers and that the live default was switched on Wednesday.

**14:45 to 19:45. Slide 3.**
Walk through breaks open at 9:30 first, then the time arithmetic (section 8), the wedge framing, the POC (section 9) and production (section 11) in three sentences.
Packaging line: "The same two calls can be one tool in your ops copilot or on an MCP server. Your tool guidance says don't hardcode filters the user never asked for; here the customer did ask for them, so the model passes only the identifier and the approved list stays in code."
Then ask the discovery questions on the slide.

**19:45 to 30:00. Questions, both ways.** AJ's questions for Ryan are in section 13; the first three are the ones to ask if time is short.

## 8. Business impact arithmetic

Every input is an assumption to confirm in discovery, except the manual baseline, which is measured (and small).

**Shared assumptions**
- 252 trading days a year.
- A team of 3 to 4 analysts, each with the 150 minutes from 7:00 to 9:30, so 450 to 600 analyst-minutes before the open, shared with other queue work.
- Loaded analyst cost (salary plus benefits and overhead) of $150K a year over 2,000 hours, which is $75 an hour.
- Reviewing a Break Check card takes 3 to 5 minutes.

**First: breaks still open at 9:30 (the value that matches the deadline)**
- **Floor:** 12 breaks a day need outside evidence, at 15 minutes each by hand, which is 180 analyst-minutes: 30% to 40% of the team's pre-open window. With the card: 36 minutes.
- **Base:** 20 breaks at 25 minutes, which is 500 analyst-minutes: 83% to 111% of the window. On a base-case day, evidence-gathering alone can fill the window, so some breaks are still open at 9:30. With the card: 100 minutes.
- **What a break open at 9:30 costs:** the name is held back from trading or traded on an unconfirmed record, and a wrong load trips the NAV tolerance check and costs an investigation on deadline, possibly a late NAV. The customer prices this from its own incident log.
- **Illustration only:** if one NAV or failed-trade investigation a quarter takes 40 staff hours, that is 160 hours, or $12K a year, before any reimbursement to the fund.
- **How to measure it:** the POC shadow week counts breaks still open at 9:30 with and without the card.

**Second: analyst time**
- **Floor:** 12 breaks a day, 15 minutes by hand vs 3 to review, saving 12 each. 12 x 12 = 144 minutes a day, which is 2.4 hours. 2.4 x 252 = 605 hours a year, about 0.3 of an analyst. 605 x $75 = **about $45K a year**.
- **Base (adds bond calls, tenders and ticker changes):** 20 breaks at 25 minutes vs 5 to review, saving 20 each. 20 x 20 = 400 minutes a day, which is 6.7 hours. 6.7 x 252 = 1,680 hours a year, about 0.84 of an analyst. 1,680 x $75 = **about $126K a year**.

**Measured manual baseline (Wednesday; n=3, one person, not the customer's analysts)**
AJ times himself resolving CDT, CTNT and FITB by hand with Google, EDGAR and Nasdaq Trader, before looking at Break Check's answer for that row. He already knows the answers from research, so this likely understates real manual time.

| Row | Manual, AJ (min) | Break Check wall time (s) | Break Check cost |
|---|---|---|---|
| CDT | to fill Wednesday | to fill Wednesday | to fill Wednesday |
| CTNT | to fill Wednesday | to fill Wednesday | to fill Wednesday |
| FITB | to fill Wednesday | to fill Wednesday | to fill Wednesday |

**Volume sanity check, rewritten to support the count honestly:** Nasdaq's equity corporate-action alert numbering reached #688 by Sep 25, 2026, about 3.7 alerts per trading day on one exchange. For a firm whose total-market products hold most listed US names, many of those touch the book (some alerts cover warrants, units and delistings it would not hold). Add NYSE names, plus calls, tenders and redemptions across the credit issuers it holds, and name or ticker changes. Only the events where the vendors disagree or lag become breaks, so 12 to 20 breaks a day needing outside evidence is plausible for the floor-to-base range but unproven. It is the first discovery question, and the value framing still holds at a few breaks a day, because it rests on the ones still open at 9:30.

**Exa spend at list price (unverified whether outputSchema adds to it)**
- **Per exception on auto:** two searches ($0.014), plus an occasional $0.001 repair, is about $0.015.
- **Floor:** 3,024 exceptions a year is about $45. **Base:** 5,040 a year is about $76.
- **If deep-lite wins the bake-off:** about $0.025 per exception, $76 to $126 a year.
- **Early-warning watch on 300 held credit issuers, daily:**
  - As scheduled auto searches (the ZDR path): 300 x 252 x $0.007 is about $530 a year.
  - As Monitors (non-ZDR option): 300 x 365 x $0.015 is about $1,640 a year.
- **Total for this customer:** under $2K a year at list.

**The commercial read: Break Check is the wedge (say it if Ryan asks about revenue)**
- Per-call spend is small by design. The commercial event is getting Exa through InfoSec and onto a zero-data-retention Enterprise agreement at an asset manager. Once Exa is approved there, other workloads can run on the same approval: a research copilot, credit monitoring, onboarding checks.
- **Expansion sized at list prices (all assumptions):**
  - A fund administrator or middle-office outsourcer running a daily watch across 5,000 issuers for its clients: 5,000 x 365 x $0.015 = about $27K a year as Monitors, or 5,000 x 252 x $0.007 = about $8.8K a year as scheduled searches under ZDR.
  - Onboarding backfills: low-effort Agent runs at $0.025 each, with the new fund's book in input.data. How many securities one run handles well is a POC question, so the cost per onboarding ranges from under $1 (100 securities a run) to about $75 (one a run) for a 3,000-security fund.
- **No contract size is guessed.** Exa's enterprise page lists committed-use plans and volume discounts; how they are sized is Ryan's world, so it becomes a question (section 13, question 2).

## 9. Proof-of-concept plan

**Scope.**
- US-listed equities and US corporate bonds only.
- Two channels per asset class, exactly as in the demo.

**Timeline.**
- **Week 0: security review.** InfoSec questionnaire, Exa's SOC 2 report and DPA (data processing agreement) from trust.exa.ai, and ZDR enabled for the team. Ask the Exa account executive whether a ZDR trial exists rather than assuming one. The public-data eval below starts in parallel, because it sends no holdings.
- **Week 1: public-universe eval.** Every Nasdaq corporate-action alert from the last 90 days (roughly 230 at the current rate of about 3.7 a trading day) plus a sample of bond-redemption 8-Ks, with public ground truth: the printed notice. Run auto and deep-lite on the same set; pick the type on accuracy per dollar. Optional: a head-to-head with Parallel (Task, Extract) on the same set.
- **Week 2: customer replay, after ZDR is on.** 150 exception tickets closed in the last 90 days, where the analyst's final resolution is the ground truth.
  - Each is run as a **publication-date-bounded replay** (`endPublishedDate` = the moment the ticket opened). Its leaks are named in the readout: content and ranking are today's, and mis-dated pages can drop or slip in.
  - The strict point-in-time arm is **Snapshot on type auto** (`contents.snapshotAsOf` = ticket open time, with outputSchema, no category, no maxAgeHours), for tickets inside Snapshot's 5-month window. 150 tickets x 2 channels is 300 Snapshot requests, beyond the 100-request pay-as-you-go limit, so Snapshot capacity is part of the enterprise trial ask.
  - Tuning (queries, allowlists, rules), second run, readout.
- **Week 3: shadow week and sign-off.** Analysts use the card alongside today's process.

**Success criteria. All must pass:**
1. An issuer-channel primary source passes the identity guard for 90% or more of tickets. A market-channel source (exchange alert or SEC filing) passes for 85% or more where one exists.
2. Terms, market effective date and new identifier match the final resolution for 95% or more of tickets with evidence.
3. Zero fields cited to the wrong issuer or the wrong bond series, enforced in code and audited by hand on a 30-ticket sample.
4. At most 1 high-confidence wrong field across the whole set.
5. Median wall time under 8 s per exception, 95th percentile under 15 s.
6. Under 3 cents per exception at list price.
7. **Shadow week:** fewer breaks still open at 9:30 than the prior four weeks' average, and analyst handling time on live exceptions down 50% or more, measured from ticket timestamps with and without the card.
8. **Reported, not a pass condition:** how often the Snapshot arm and the replay arm agree on fields, with each disagreement explained. This measures how much the replay leaks.

**Who signs off.**
- Head of Investment Operations (the business case).
- Security master team lead (accuracy judgments on disputed rows).
- Market data or vendor management (the contract).
- CISO or InfoSec (vendor review, the gate).
- Procurement.
- On Exa's side: the account executive for the contract and the FDE for the technical win.

**Security and data-retention answers (the safe phrasing).**
- **ZDR:** "Search, which carries every routine query, is covered by ZDR in both Exa sources I read. The one-URL repair uses Contents, and I'd confirm its coverage with you because two Exa pages list it differently. Monitors are not ZDR, so under ZDR the watch runs as scheduled searches." Agent is ZDR-covered in both Exa sources. Batch coverage is not stated: confirm. If Contents turns out not to be covered, the repair is switched off under ZDR and a stale page goes to the analyst with its link.
- **What the queries contain.** Only public identifiers (ticker, CUSIP, issuer name), no client names or position sizes. The set of identifiers still reveals holdings, which is why ZDR comes first and the customer replay waits for it.
- **Compliance.** Exa states SOC 2 Type II, with the report and DPA at trust.exa.ai.
- **Default retention for non-ZDR accounts** is not stated in the pages reviewed. Say "I don't know, I'll find out" rather than guess.
- **Keys.** Server-side only, with a per-key `budgetCents` cap and rate limit set in the dashboard or through the Team Management API.
- **Audit trail.** Every call logs requestId, costDollars and searchTime.

## 10. Honest limits

**What Exa does not replace**
- The licensed corporate-actions feeds or the golden-copy precedence rules.
- Custodian notices (SWIFT MT564 corporate-action messages), DTCC corporate-action data, trustee notices and broker-only notices.
- Anything behind a login or paywall. Exa's crawler respects robots.txt and does not log in.
- The analyst's approval. Nothing auto-loads.

**Where a scraper would do as well**
- For Nasdaq names you could scrape the alert page, and EDGAR has full-text search for 8-Ks. The case for Exa is the long tail: issuer IR sites, wires and bond redemptions found from one plain-language query with no per-site rules, returned with highlights and per-field citations in one synchronous call. Parallel (Task, Extract) could approximate this, so the POC allows a head-to-head. Never claim Exa is the only option.

**What could go wrong**
- **Mis-estimated dates.** publishedDate is an estimate: Verizon's release (text: Aug 20) was dated Sep 21, and Nasdaq OTU #2026-9 (printed Aug 4) was dated Aug 31. Mitigation: no date filter on the live path; the window is in the systemPrompt and code checks `source_notice_date`, the date printed on the notice.
- **Unstable ranking for per-issuer exchange alerts.** With 5 results, CDT's alert #683 was missed in the probes. Mitigation: the default of 10 results is kept on purpose, the stale detector and identity guard run on raw results, and every demo row is in the golden cache.
- **Identity.** "CDT" is also a time zone abbreviation, so bare tickers are amber only. Bond releases can cover several series (BAC's does), so the series rule sits in the systemPrompt and code rejects other series. The model can echo the issuer named in the prompt, so the grounding check against the cited page's own text is the primary guard.
- **Stale stored copies.** Exa's stored copy can be a placeholder (CTNT on Sep 29, seen through the keyless MCP). The repair fixes the text; maxAgeHours does not make an unindexed page appear.
- **Bonds are not truly two-source.** The SEC filing is usually the issuer's own release filed again, so the chip says "Same-issuer confirmation".
- **The replay leaks.** It bounds publication date, not content or ranking; Snapshot is the stricter check.
- **Coverage gaps.**
  - NYSE-listed names have no per-issuer alert source; the 8-K channel applies.
  - Non-US issuers, municipal bonds (MSRB EMMA) and structured products were not checked.
  - Business Wire originals did not surface in the probes; mirrors are tagged and never count as corroboration alone.
- **Extraction mistakes.** Model extraction can be wrong or merge two notices. Mitigation: grounding confidence, the identity and citation checks, the code comparison and the human review.
- **Untested until AJ has a key (Wednesday):**
  - auto with the 5-field outputSchema, and whether deep-lite beats it;
  - summary with a schema on /contents together with maxAgeHours 0;
  - whether the bare `nasdaq.com/press-release`, `nasdaqtrader.com`, `sec.gov` and wire-domain entries match their www hosts;
  - Snapshot on /search with outputSchema and includeDomains;
  - real latency and whether outputSchema adds to `costDollars`.
  Each has a named fallback: the deep-lite arm, highlights-only repair, the www entries, the /contents Snapshot audit, and the golden cache.
- **Snapshot limits:** a rolling 5-month window, 100 requests before a sales conversation, and CONTENT_NOT_CACHED possible. It stays off the live path.
- **Mocked rows.** The vendor disagreements are mocked and labeled as such everywhere.
- **Small spend.** Per-customer Exa usage is small. The commercial case rests on the ZDR Enterprise agreement and on expansion, and AJ does not know how Exa sizes those.

## 11. How this runs in production

**Pipeline**
1. The nightly golden-copy build writes exceptions to the customer's queue.
2. A small Break Check service (Python, server-side, inside their network) picks up each exception.
3. It reads the channel config for the asset class, runs Calls 1 and 2 on /search under the ZDR team key, applies the stale detector, identity guard, grounding check and comparison rules, and writes the evidence card, verdict and drafted note back to the ticket (ServiceNow or Jira) with the citation URLs.
4. The analyst approves; the golden copy is updated; the note goes either to the vendor that was wrong or to the team that owns the field mapping.

**Early warning**
- **Under ZDR (the default):** for each held issuer, a daily scheduled /search from the customer's own scheduler (the Call 6 scheduled body), with `startPublishedDate` set to the last successful run minus 7 days and URL dedupe against open tickets.
- **For teams that accept non-ZDR:** Exa Monitors with a webhook to their ticket bridge (public HTTPS, verified with `webhookSecret`).
- New events open tickets weeks ahead, before either vendor has them.

**Agent and MCP packaging**
- Expose `break_check(identifier, event_hint)` as one tool in the customer's ops copilot: a Pydantic AI tool or a tool on an internal MCP server (Model Context Protocol, the standard way to plug tools into AI agents).
- The domain allowlist, evidence window and schema come from the customer's approved config, fixed in code. The model passes only the identifier. Line: "Your tool guidance says don't hardcode filters the user never asked for. Here the customer did ask for them, so the model passes only the identifier and the approved list stays in code."
- Highlights are the default output to the model.

**Bulk jobs**
- **Onboarding backfill:** when a new fund is onboarded, check its whole book for pending events with Exa Agent, run asynchronously off the live path.
  - `effort: "low"` set explicitly ($0.025 per run), for a fixed, predictable cost.
  - The book goes in `input.data`, not the query. How many rows one low-effort run handles well is a POC question.
  - The output array gets `maxItems`, so output size and cost are bounded.
  - Code waits for a terminal status and reads `output` only when status is `completed`; `failed` and `cancelled` are logged and retried.
  - `output.grounding` is persisted at once. Exa's zero-data-retention docs page says that under ZDR, run data lasts only 10 minutes after a run ends and `previousRunId` is unavailable.
- **At higher volume:** the Batch API (Enterprise beta) runs nightly bulk /search. Its ZDR coverage is not stated; confirm first.

**Operations**
- Log requestId, costDollars, searchTime and the queue headers per call.
- Set per-key budgets and rate limits.
- Alert on the status.exa.ai components.
- Honor the rate limits: /search on auto at 10 QPS; the 5 QPS deep-type limit and the shared limiter matter only if deep-lite wins.
- Keep a weekly re-run of the eval set as a regression test.

## 12. Build plan, rehearsal, file layout and prepared answers

**Before the clock starts (AJ does this himself, about 10 minutes)**
- Create the Exa account and key at dashboard.exa.ai/api-keys.
- Put `EXA_API_KEY` in `C:\Users\ajwal\Documents\exa-demo\.env`.
- Set a $5 per-key budget.
- Complete onboarding for the $10 bonus.
- If the key exists before Wednesday, run CTNT's Call 2 at once and keep the file. Every day of delay is another chance that Exa refreshes the page.

**Timeboxed steps (about four hours in total, including rehearsal)**

| Time | Step | Done when |
|---|---|---|
| 0:00 to 0:25 | `data\rows.json` (5 rows plus 2 backups: fixed dates, identifiers, bond identity key, mocked vendor values, per-channel query and systemPrompt text, and the four beat texts) and `data\channels.json`. Apply the eight exa_client changes from section 5 | Bodies print and match section 4, with every `<placeholder>` replaced: `outputSchema` and `summary.schema` are the schema object (never a string), and the FITB coupon, maturity and window dates come from rows.json |
| 0:25 to 1:05 | `app\evidence.py`: body builders, module-level executor, polling timebox, stale detector, identity guard, grounding check, repair | CDT returns two guarded records in "Saved runs only" mode and live |
| 1:05 to 1:30 | `app\compare.py`: normalizers, rules, note templates; `tests\` | Unit tests pass on saved CDT, CTNT, FITB and BAC responses |
| 1:30 to 2:20 | `app\app.py`: sidebar, queue, break detail, under the hood | The full click-path works in "Saved runs only" mode |
| 2:20 to 2:50 | Wednesday live run: the bake-off (all rows plus backups, auto and deep-lite, identical bodies except type: about 28 calls, under $0.30), the CTNT capture: run CTNT's Call 2 only and save it. Never run Call 3 on Wednesday, because a live crawl may refresh Exa's stored copy and erase Friday's state. If Friday's repair fails, the stale copy stays flagged and the break goes to the analyst with its link. If the detector does not fire on Wednesday, cut the scene and describe CTNT in one sentence, using the Sep 29 MCP observation labeled as such. Then the CDT replay, the Snapshot pre-run (2 calls), and one genuinely slow call: the CDT Call 2 body with type deep-reasoning (Exa lists 12 to 40 s, $0.015) under the 8 s timebox; pass = the screen returns in about 8 s. Fill the bake-off table, pick the type, copy `cache\` to `cache_golden\` | Golden cache frozen; every demo row has a saved run |
| 2:50 to 3:05 | `slides\build_slides.py`: 3 slides from section 6, plain layout | Break_Check.pptx opens in PowerPoint |
| 3:05 to 3:40 | **Rehearsal, at least 35 minutes:** one full timed run out loud using section 7, then a second run where someone interrupts at least three times; fix overruns | Demo block ends by 14:45 with every beat's four parts spoken |
| 3:40 to 4:00 | **"Explain the code out loud", 20 minutes:** walk exa_client.py and evidence.py line by line, then say each prepared answer below without notes | Every answer below said once, cleanly |

**Separately on Wednesday, outside the four hours:** the manual baseline (AJ times himself on CDT, CTNT and FITB by hand; likely 45 to 75 minutes) and re-verifying every row fact on its primary page.

**Cut list if time runs short (in this order)**
1. Snapshot panel (describe it in answers).
2. Run all button (keep the failure drill on CDT).
3. IMMP row.
4. Early-warning JSON on screen (keep it on slide 3 as one line).

**File layout, with every function**

```
C:\Users\ajwal\Documents\exa-demo\
  .env                      EXA_API_KEY (never committed, never shown)
  requirements.txt          streamlit, pandas, requests, python-dotenv, python-pptx
  app\
    exa_client.py
    evidence.py
    compare.py
    app.py
  data\
    rows.json
    channels.json
  cache\                    working cache, written by live calls
  cache_golden\             frozen Wednesday runs, read-only
  tests\
    test_exa_client.py
    test_evidence.py
    test_compare.py
    test_timebox.py
    fixtures\               saved responses copied from cache_golden (no API calls in tests)
  slides\
    build_slides.py
    Break_Check.pptx
```

**app\exa_client.py** (exists; add the eight changes in section 5)
- `api_key()`: return the key from .env, or empty text.
- `cache_path(endpoint, body, folder)`: the file a request is saved under, from a hash of the endpoint plus the sorted body.
- `_read_cache(path)`: load a saved response, or None.
- `_write_cache(path, endpoint, body, data, elapsed_ms, headers)`: save a good response to `cache\` only, via a per-thread temp file and `os.replace()`, wrapped in `try/except OSError` so a failed save sets `cache_write_error` and still returns the live envelope.
- `_envelope(...)`: build the one package every call returns, pricing /contents as pages times content types (minimum one), and carrying `queued`, `queue_ms` and `saved_from`.
- `_explain(status, payload)`: turn an HTTP failure into a sentence a presenter can read out.
- `_retry_wait(resp, attempt)`: seconds to pause before a retry, honoring Retry-After, capped at 5.
- `call(endpoint, body, cache_only, max_retries, timeout)`: send one request inside the shared limiter; fall back to golden, then working cache; always return an envelope.
- `search(body, cache_only, timeout)`: POST /search.
- `contents(body, cache_only, timeout)`: POST /contents.

**app\evidence.py** (keep it short and flat, one function per step)
- `load_rows()`: read data\rows.json.
- `load_channels()`: read data\channels.json.
- `build_search_body(row, channel, type_override=None, end_published=None)`: the Call 1 or 2 body for a row, from rows.json text and the channel allowlist.
- `build_repair_body(url)`: the Call 3 /contents body with summary and the repair schema (the shared five fields with identifier_in_source in place of effective_as_stated).
- `build_repair_fallback_body(url)`: the highlights-only Call 3 body.
- `build_snapshot_body(urls, as_of)`: the Call 5 audit body.
- `build_watch_body(issuer)`: the scheduled /search early-warning body.
- `build_monitor_body(issuer)`: the Monitor body, for display only.
- `EXECUTOR`: the one module-level `ThreadPoolExecutor(max_workers=4)`.
- `run_row(row, timebox_s, on_tick, simulate_timeout=False)`: submit both channels, loop `wait(timeout=0.5)` calling `on_tick`, and at the deadline, for any unfinished channel, call `exa_client.search(body, cache_only=True)` and set `envelope["error"] = f"live call still running past {timebox_s} s"`.
- `detect_stale(raw_results, channel)`: return the URL to repair, or None; runs before the identity guard.
- `source_class(url, channels)`: tag a URL as issuer wire, issuer IR site, syndication mirror, exchange or SEC filing.
- `identity_guard(results, row)`: split results into kept, amber (bare ticker or name only) and dropped.
- `check_grounding(output, kept, allowlist, row)`: per-field status; the primary guard (cited URL in the allowlist, among kept results, and the cited page's own text contains the identifier).
- `repair(url, timebox_s=15, on_tick=None)`: submit Call 3 to `EXECUTOR`, loop `wait(timeout=0.5)` calling `on_tick` so the timer counts on screen, and at the deadline stop waiting and show the stale copy flagged with reason "live re-fetch still running past 15 s". Only if Call 3 returns an error inside the timebox, submit the highlights-only fallback body under the same remaining deadline. Parse the summary.
- `parse_summary(summary_text)`: turn the summary's JSON string into a dict, or None.

**app\compare.py** (no model anywhere)
- `normalize_date(text)`: any printed date to YYYY-MM-DD, or None.
- `parse_time_et(text)`: the clock time in a stated effective time, or None.
- `normalize_cusip(text)`: 9 characters, uppercase, no spaces, or None.
- `normalize_ratio(text)`: "1-for-25" or "1:200" to a (new, old) pair.
- `next_trading_day(date)`: the next NYSE trading day, from a fixed 2026 holiday list.
- `weekend_flag(date)`: True when a stated date falls on a Saturday or Sunday (FITB's Nov 1).
- `in_window(source_notice_date, window_start)`: enforce the evidence window on the printed date.
- `is_after_close_rule(issuer_rec, market_rec)`: True when the issuer's effective time is at or after 4:00 PM ET on day D and the market date is `next_trading_day(D)`.
- `field_verdict(field, issuer_val, market_val, source_classes)`: Corroborated, Same-issuer confirmation, Explained difference, Single-source field or Conflict for one field; a mirror-only value never counts as corroborated.
- `vendor_match(field, resolved, vendor_a, vendor_b)`: which vendor matches the resolved value.
- `row_verdict(row, issuer_rec, market_rec, repaired)`: the one status chip for the row, including Stale source repaired.
- `draft_ticket_note(row, verdicts, citations)`: the resolution note with both links.
- `draft_followup_note(row, verdicts)`: either a vendor escalation or a "check our field mapping" note, depending on whether the vendor value matches a valid meaning in the source.

**app\app.py** (Streamlit)
- `sidebar()`: the toggles, timebox, free-form box and the permanent mocked-data line.
- `render_queue(rows)`: Screen 1.
- `render_beat_panel(row)`: the four beat texts from rows.json.
- `render_channel_column(label, envelope, checks)`: status badge, top guarded result, fields with confidence and citation, expanders.
- `render_comparison(row, verdicts)`: the comparison table and chip.
- `render_ticket_note(note)`: the note with a Copy button.
- `render_break_detail(row)`: Screen 2, wiring `run_row` to `st.empty()` timer placeholders through `on_tick`.
- `render_under_the_hood()`: Screen 3: call log, bake-off plus manual baseline, Run all, Snapshot panel, early-warning JSON.
- `main()`: page routing.

**data\rows.json**: per row: id, asset class, listing venue, ticker, exchange-prefixed ticker forms, CUSIP, legal name, bond identity key (issuer, coupon, maturity, CUSIP when printed), field in dispute, Vendor A and B values, opened_at, window_start, the query and systemPrompt text per channel (fixed dates and month words), the four beat texts, and a demo_path flag.

**data\channels.json**: per asset class: issuer-channel allowlist, mirror list, market-channel allowlist and on-screen label; per issuer: IR site (ir.53.com, newsroom.bankofamerica.com); source-class tags; the early-warning query per watched issuer.

**slides\build_slides.py**
- `slide_customer(prs)`: slide 1.
- `slide_thesis(prs)`: slide 2.
- `slide_impact(prs)`: slide 3.
- `main()`: write slides\Break_Check.pptx.

**tests\** (saved responses only, no API calls, in the spirit of recorded-response tests)
- `test_exa_client.py`: monkeypatch `CACHE_DIR` and `GOLDEN_DIR` to pytest `tmp_path` folders; fallback reads golden before working cache; live writes go only to the working folder; /contents pricing is pages times content types with a minimum of one; the timeout override is passed through; a failed cache write still returns a live envelope.
- `test_evidence.py`: "10:00 a.m. CDT" does not pass the guard, and a bare ticker is amber; the stale detector sees a placeholder page before the guard drops it; a citation outside the allowlist fails the grounding check; BAC's second series is rejected; a repaired summary naming another issuer is discarded.
- `test_compare.py`: CDT gets "Explained difference"; FITB gets "Same-issuer confirmation" and a weekend flag; a mirror-only field is not corroborated; a notice printed before the window is dropped.
- `test_timebox.py`: with both cache folders monkeypatched to `tmp_path`, a mocked 3-second call under a 1-second timebox returns control in about 1 second with the saved run and the reason text, and after the late thread finishes its file exists in the working folder only.

**Prepared one-sentence answers (say each out loud in the 20-minute pass)**
- **Why POST?** "The request carries a JSON body with the query, filters and schema, and Exa defines search and contents as POST endpoints; GET reads something at a URL with no body, POST sends a body for the server to act on, and PUT replaces a resource at a known address."
- **What does the x-api-key header do?** "It tells Exa which team is calling, for authorization, billing and rate limits; it's read from .env on the server and never reaches the browser, and Exa also accepts it as an Authorization Bearer header."
- **What happens to a running thread when the timebox fires?** "Nothing stops it, because Python can't kill a running thread: the screen stops waiting and shows the saved run, and the thread finishes when Exa answers or its own request timeout fires, then writes to the working cache for next time."
- **Why is the cache keyed by a hash of the request body?** "So the same request always maps to the same file and any change to the query, type or dates maps to a new one, which means a saved answer can never be shown for a different question; sorting the keys first makes key order irrelevant."
- **How long did the build take?** "About four hours of build and rehearsal, plus research beforehand and about an hour timing myself on the manual baseline; I used AI tools for research and code, as your posting says is expected, and I reviewed every call myself." (The last clause is true only once the 20-minute explain-the-code pass is done.)
- **Why a thread pool at module level?** "A with-block waits for every thread on exit, which would turn my 8-second timebox into the full request timeout."
- **Why not exa-py?** The reworded line in section 4.

## 13. Questions for Ryan

Drawn from `research\interviewer.md`. Credit his work accurately: the Pydantic AI PR was closed, and in the harness integration that shipped he was one contributor among several, so say "the Exa capability in the Pydantic AI harness you worked on".

**Ask these three first if time is short**
1. "In Pydantic AI issue 6082 you described a customer whose model was putting domain filters into the query text. How common are setup mistakes like that, and is catching them part of an FDE's first weeks on an account?"
2. "A workload like Break Check spends very little, but it's the one that gets Exa through InfoSec and zero data retention at an asset manager. How does Exa size an enterprise commitment when the first workload is small but opens the door?"
3. "Which verticals is the NYC FDE team going after first? Is financial services where the early pipeline is?"

**About his work**
4. "Do partner integrations like the Exa capability in the Pydantic AI harness start from a specific customer ask, or are they a way to meet developers inside the frameworks they already use?"
5. "You pushed highlights as the default for agents because they use fewer tokens. In a POC, how do you show a customer the tradeoff between answer quality and token cost in numbers they trust?"
6. "Your agent_run change in the MCP server handles runs that outlast the call window. For enterprise Agent customers, what causes the most production pain: latency, cost control, or structured-output quality?"
7. "You added the x-exa-integration attribution header. How does the go-to-market side use usage signals like that, for example to spot expansion or churn risk?"
8. "Your post about joining Exa described years of manual research feeding executive and architecture decisions. What convinced you to move from doing that research to building the tool for it?"

**About the product, from building this demo**
9. "Two Exa pages list zero-data-retention coverage for Contents and Answer differently. Which is current, and how do FDEs handle a security questionnaire when the docs disagree?"
10. "Snapshot is the strict point-in-time tool. What do customers use it for most, and how is the 100-request limit usually handled in a trial?"
11. "In discovery, how do FDEs decide between Search, the Agent API and Monitors? Is there a rule of thumb?"

**About how FDE work is judged**
12. "When an enterprise demo lands, what's usually the moment that does it: results they couldn't get elsewhere, structured output, or speed?"
13. "How do you set POC success criteria with an enterprise team, and who on their side usually signs off?"
14. "After a strong demo, where do deals most often stall: security review and data retention, procurement, or proving return on investment?"
15. "What separates the FDEs who ramp fastest here from the ones who struggle?"

**About the NYC FDE team**
16. "How will NYC FDEs split time between new logos and existing accounts, and does each FDE pair with a specific account executive?"
17. "How do SF and NYC FDEs share demos and integration patterns? Is there a shared demo library, or will the new Technical Enablement role own that?"
18. "The posting says ship code in the morning and close a deal in the afternoon. How literal is that? Roughly what share of the week is building versus calls?"
19. "When an FDE finds a product gap, how does it get back to product? Can FDEs ship fixes into core repos directly, the way you did with the MCP server?"
20. "What would you want a new NYC FDE to have shipped or owned by day 90?"
