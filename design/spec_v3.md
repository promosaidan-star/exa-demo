# Break Check: build and demo spec (version 3)

Demo: Fri 2026-10-02, 6:30 PM ET, Exa FDE demo round with Ryan Ahern (technical go-to-market). 30 minutes. Expect him to open the code and ask why each parameter is set.

**Status of results in this spec: measured 2026-09-29 where marked.** AJ's Exa key exists and works. On Sep 29 about 35 keyed calls went through `app\exa_client.py` (script: `tools\probe.py`), costing roughly $0.25 of the $10 free credit, and every response is saved in `cache\` and copied to `cache_golden\` (the full record is `design\live_findings_2026-09-29.md`). Anything marked "measured 2026-09-29" comes from those saved responses. Anything still marked "unverified" was truly not tested. Re-check each row fact on its primary page before saying it out loud.

**What changed from version 2, in one paragraph.** The live demo is now five scenes (ONMD, CDT, BAC, CTNT with the timeout drill, and a security Ryan names); FITB is dropped from the live path because it failed on both channels. Every "expected" result is replaced by the measured one. The request bodies are now the exact bodies that were measured, because the saved-run cache is keyed by a hash of the body (section 4 explains the two differences from version 2: an 8-field schema and a `startPublishedDate` window). Auto is the default on measured evidence. The stale-page repair is shown honestly: on nasdaqtrader.com a forced live fetch comes back "success" with an empty page, so code treats empty text as a failure. Code reads the value of every field and never trusts the confidence label alone. The credibility line states what AJ did at Charles River, plainly.

**Earlier versions.** The version 1 to version 2 changes are recorded at the top of `design\spec_v2.md`.

---

## 1. The customer, the end user, and the problem

1. **The customer.** A US asset manager that runs index and total-market equity products alongside investment-grade credit (assume $100B to $200B under management; an assumption to confirm). Because its total-market products can hold nearly every listed US name, small-cap reverse splits like ONMD's and CDT's land in its book, and because it runs credit, bond calls do too. It buys security data from two licensed vendors and merges them into one "golden copy", the firm's master record of every instrument its order system trades.
2. **Who decides and who pays.**
   - **Economic champion:** the Head of Investment Operations, who owns the pre-open deadline and feels the cost of a late or wrong fix.
   - **Contract owner:** the market data or vendor management team, which holds data-vendor contracts.
   - **The gate:** InfoSec (information security), because the identifiers the firm looks up reveal what it holds.
   - **Expansion path, not the primary customer:** fund administrators and middle-office outsourcers that run the same queue for many clients.
3. **The end user.** A security master analyst on a team of 3 to 4 who share one queue of "breaks". A break is a row where the two vendors disagree about something: a split ratio, an effective date, a new CUSIP (the 9-character US security identifier), or whether a bond has been redeemed.
4. **The job today.** The team starts around 7:00 AM and must settle every break before the 9:30 AM open. The only real tiebreaker is the issuer's own announcement plus the exchange's or SEC's notice, which an analyst finds by hand. That takes an assumed 15 to 25 minutes per break (to be checked against AJ's own timed manual baseline, section 8).
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
4. **Search by hand.** Google, EDGAR (the SEC's filing database) and Nasdaq Trader (Nasdaq's site for market notices), looking for the issuer's release and the exchange's alert while skipping re-posts and aggregators. **REPLACED:** two Exa searches, one per source type. The approved domain list is fixed in code, the evidence window is a fixed start date in the request, and code checks the date printed on each notice.
5. **Read and reconcile.** The analyst reads both documents and works out what each "effective date" means (legal effective time vs first trading day on new terms). **MOSTLY REPLACED:** fields come back with a citation each, code compares them field by field and labels known patterns, and the analyst reads the two highlighted sentences to confirm.
6. **Write up.** The analyst pastes links into the ticket and writes a resolution note. **REPLACED:** code drafts the note from the grounded fields and their URLs. When only one source can be found, or a source page is stale or empty, the note says so and the break stays with the analyst.
7. **Fix, then decide who is wrong.** The analyst loads the fix, then decides whether the disagreement is a vendor error (escalate to that vendor) or the firm's own field mapping (fix the precedence rule). **Stays human.** The note is drafted with the evidence attached.
8. **Weeks later.** Audit asks what the firm knew when it loaded the fix. **NEW, optional:** an Exa Snapshot copy of each cited source as Exa had stored it at the ticket's open time.
9. **The case no one catches.** An announced-but-not-yet-effective event (a bond call next month) that neither vendor has picked up yet is found only when a feed finally changes. **NEW, in production:** a daily early-warning search on held issuers (section 11).

The one step to name on the call: step 4, the manual search, is where the 15 to 25 minutes go. Steps 5 and 6 fall out of it.

## 3. The applet: screens and panels

It is a single Streamlit app (`streamlit run app\app.py`).

**Sidebar (the presenter's controls)**
- **"Saved runs only"** toggle. It reads the frozen Sep 29 runs in `cache_golden\` and makes no network calls.
- **"Simulate timeout"** toggle. It delays the next market-channel call by 20 seconds inside the worker thread, so the real timebox path runs (not a shortcut).
- **Timebox seconds.** Default 8 on auto. Measured 2026-09-29: 20 auto calls with the schema took 1.9 to 4.1 seconds each (median about 3.1 s), so 8 s is about twice the slowest call seen.
- **Free-form box.** Ticker or CUSIP, issuer name, listing venue and event hint, for a live row Ryan names.
- A permanent line: "Vendor records are mocked. Every source page is retrieved by Exa, live or from a labeled saved run."

**Screen 1: Exception queue**

Columns: row, identifier, issuer, field in dispute, Vendor A value, Vendor B value, opened at, status. All rows are real September 2026 events with mocked vendor values. Four rows are on the spoken path, in this order; the fifth scene is a row Ryan names in the free-form box. The backups sit below a divider on the same screen.

| Row | Break (vendor values mocked) | What Exa returned (measured 2026-09-29) | Role in the demo |
|---|---|---|---|
| ONMD (OneMedNet Corp, Nasdaq: ONMD) | 1-for-10 reverse split effective 2026-09-29. Vendor A has the new CUSIP 68270C202; Vendor B shows no CUSIP change | Issuer: GlobeNewswire, Sep 25, 1-for-10, effective 12:01 a.m. ET Sep 29, CUSIP printed "68270C 202". Market: Nasdaq alert 2026-688, one-for-ten, effective Tue Sep 29, CUSIP "68270C202". All fields high confidence | **Scene 1:** the normal path. Code strips the space from the CUSIP and marks the row corroborated by two independent sources |
| CDT (CDT Equity Inc., Nasdaq: CDT) | 1-for-25 reverse split. Vendor A market-effective 2026-09-28, Vendor B 2026-09-29, both CUSIP 20678X700 | Issuer: GlobeNewswire, Sep 25, effective "September 28, 2026, at 5:00 pm, Eastern Time", split-adjusted trading from Sep 29, CUSIP 20678X700. Market: Nasdaq alert 2026-683 is not in Exa's index (alerts 682 and 688 from the same day are) | **Scene 2:** two meanings of "effective", shown honestly as single source, issuer only |
| BAC 06051GLX5 (Bank of America Floating Rate Senior Notes due September 2027) | Redeemed Sep 15, 2026. Vendor A shows it redeemed; Vendor B still shows it outstanding | Issuer: Bank of America newsroom release of Sep 4 (also on PR Newswire): redemption at 100% of principal plus accrued and unpaid interest on Sep 15, 2026, identifier 06051GLX5. Market: nothing relevant on sec.gov | **Scene 3:** fixed income. A bond that no longer exists but is still live at one vendor. Single source, issuer only |
| CTNT (Cheetah Net, Nasdaq: CTNT) | 1-for-150 reverse split. Vendor A has new CUSIP 16307X400; Vendor B has no new CUSIP (row facts from a WebFetch of the alert on Sep 29; re-check before Friday) | Issuer: no reverse-split release on the wires. Market: Exa's stored copy of alert 2026-677 reads "Page Not Available"; a forced live fetch returns "success" with empty text | **Scene 4:** when it goes wrong. Code refuses to confirm and routes the row to the analyst with the reason. The timeout drill is the second half of this scene |

**Backups below the divider** (in rows.json, all measured 2026-09-29, none on the spoken path):

| Row | Measured state | Use |
|---|---|---|
| AGRZ (Agroz Inc.) | Corroborated by two independent sources: PR Newswire and Nasdaq alert 2026-682, 1-for-20, effective Sep 29, CUSIP G0136M119 | Swap for ONMD if ONMD misbehaves on Friday |
| NFE (New Fortress Energy) | Exchange only: alert 2026-654, 1-for-50, effective Mon Sep 14, CUSIP 644393308. The issuer search's top result was a law firm's shareholder-lawsuit advertisement, so fields came back "not stated" | Suggested row if Ryan has none in mind; also the best live example of why the identity guard exists |
| JAGX (Jaguar Health) | Exchange only: alert 2026-662, 1-for-15, effective Thu Sep 17, CUSIP 47010C854 | Backup for Ryan's pick |
| IMMP (Immutep ADS) | Issuer only: GlobeNewswire Sep 21, ratio from 1 ADS = 10 shares to 1 ADS = 200 shares | Backup; shows a depositary-share ratio change |
| TRUG (TruGolf) | Issuer only: GlobeNewswire Sep 25, 1-for-10, CUSIP 243733607, trading Sep 29 | Backup |

FITB is not in rows.json: it failed on both channels on Sep 29 (not found on the wires or ir.53.com; sec.gov returned a prospectus, not the redemption 8-K).

Button: **Check** (one row).

**Screen 2: Break detail (the core screen)**

- **Top: the beat panel.** Four short texts stored per row in rows.json, so AJ reads his reasoning aloud: hypothesis, action, expected result, and "if it comes back different, I check X next".
- **Two columns: "Issuer channel" and "Market channel".** For bonds the market column is labeled "SEC filing (issuer, legally filed)". For both, code shows "Same-issuer confirmation" when both citations carry the issuer's own text. Each column shows:
  - A status badge: Live (green), or Saved run (amber, with saved-at time and reason), latency, costDollars and requestId.
  - The top result that passed the identity guard: title, domain, a source-class tag (issuer wire, issuer newsroom, syndication mirror, exchange, SEC filing), Exa's publishedDate next to the date printed on the notice, and the highlighted sentences.
  - The extracted fields, each with a confidence chip (low, medium or high) and a clickable citation from `output.grounding`. A field whose value is "not stated" is shown grey as "missing" whatever its confidence chip says.
  - Expanders: "Request JSON" (the exact body sent) and "Filtered out by identity guard (n)" (other issuers' pages that came back and were dropped, plus amber bare-ticker matches).
- **Comparison table:** field, issuer value, market value, Vendor A, Vendor B, verdict. The verdict comes from fixed rules in compare.py, never from a model.
- **Row chip:** Corroborated (two independent sources), Same-issuer confirmation, Explained difference, Single source (issuer only, or exchange only), Stale source, not confirmed, or Conflict, escalate.
- **Ticket note:** a plain-code template with the citations, the chip and, for a single-source or stale row, the reason, plus a Copy button.
- **Conditional button:** "Re-fetch this page live" appears only when the stale detector fires.

**Screen 3: Under the hood (the 60-second tour and a place to answer questions)**

- **Call log:** requestId, endpoint, type, latency, costDollars, live or saved, and the `x-exa-queued` / `x-exa-queue-ms` headers (whether the request waited in Exa's rate-limit queue, and for how long).
- **Type comparison** (measured 2026-09-29): the CDT market call on auto ($0.007, 4.1 s) and on deep-lite ($0.012, 5.0 s), identical bodies except `type`; deep-lite found nothing extra. One call pair, so it is labeled as a single comparison, not a benchmark. Next to it, the **manual baseline**: AJ's own minutes per row by hand, if timed before Friday (section 8).
- **Measured summary:** 20 auto calls with the schema, 1.9 to 4.1 s each, $0.007 each; no ratio, date or CUSIP invented in 22 search calls (section 5 gives the exact wording).
- **Run all** button: calls `run_row()` for one row at a time (never all rows submitted at once), so each row's two calls start together and its timebox measures real call time; every request still passes the shared limiter. Totals: calls, live dollars, median and max latency.
- **Snapshot audit panel** (cached, pre-run before Friday, never live).
- **Early-warning JSON:** the scheduled /search body (the zero-data-retention path) and the Monitor body (the option for teams that accept non-ZDR), plus a static production diagram.

## 4. Every Exa call

All calls go through the existing `C:\Users\ajwal\Documents\exa-demo\app\exa_client.py`, as raw HTTP POST (`requests`) with the `x-api-key` header. exa_client passes the body through untouched, so the bodies below are exactly what goes over the wire. Calls 1, 2 and 3 were run with AJ's key on 2026-09-29 and their responses are saved in `cache_golden\`; Calls 4, 5 and 6 have not been run yet and are marked unverified.

**Why raw HTTP and not exa-py (say this if asked):** "exa-py's get_contents adds 10,000 characters of text whenever I don't pass text, summary or extras, even when I ask only for highlights. That bills two content types, and it drops the per-URL error tags. search() adds text only when you pass no contents. With raw HTTP, the body on screen is exactly what was sent." Exa's own build guidance treats raw HTTP as a first-class route and accepts either `x-api-key` or `Authorization: Bearer`.

**Rule for rows.json:** the query, systemPrompt, `startPublishedDate` and schema for every demo row are copied verbatim from the saved request bodies in `cache_golden\` (written by `tools\probe.py`). The cache key is a hash of the exact body, so a single changed character means "Saved runs only" and every fallback find nothing. Put an identifier in the query only when both vendors agree on it, so the query never leans toward one vendor's disputed value. Every date is fixed text in rows.json, never computed from `now()` (see the cache note in section 5).

**Two differences from version 2, both because the measured bodies differ:**
1. **The schema has 8 flat fields, not 5.** That is the schema every Sep 29 call used.
2. **The live bodies carry `startPublishedDate`** (a fixed date about 30 days before the event, from rows.json). Version 2 had planned no date filter on the live path. The window still gets a second check in code against the date printed on the notice.
Trimming to 5 fields or dropping the date filter are untested alternatives. Either would need a fresh keyed run and a new golden copy before Friday, so neither is planned.

### Shared schema (Calls 1 and 2, as measured)

```json
{
  "type": "object",
  "required": ["identifier_in_source", "event_type", "terms", "effective_as_stated",
               "market_effective_date", "new_cusip", "new_symbol", "source_notice_date"],
  "properties": {
    "identifier_in_source": {"type": "string", "description": "Ticker or CUSIP of the affected security, exactly as the source prints it. For a bond with no CUSIP printed, the coupon and maturity as printed"},
    "event_type": {"type": "string", "description": "One of: reverse split, forward split, ticker change, name change, ADS ratio change, redemption, tender offer, other"},
    "terms": {"type": "string", "description": "Split or ratio terms, or redemption price and amount, as stated"},
    "effective_as_stated": {"type": "string", "description": "Effective date and time exactly as the source writes it"},
    "market_effective_date": {"type": "string", "description": "YYYY-MM-DD of the first trading day on the new terms, or the redemption date for a bond, or not stated"},
    "new_cusip": {"type": "string", "description": "New CUSIP as stated, or not stated"},
    "new_symbol": {"type": "string", "description": "New ticker as stated, or not stated"},
    "source_notice_date": {"type": "string", "description": "YYYY-MM-DD printed on the notice itself"}
  }
}
```

**Why eight fields (the line):** "Your patterns page prefers one to five root fields. I measured eight flat fields, and on every call where the right page was in the index all eight came back filled, so I kept the shape I measured. Six of them feed a rule in compare.py. The other two, identifier_in_source and event_type, are display only. Identity is decided by code against the cited page's own text, because on the CDT exchange call the model returned 'CDT' as the identifier at low confidence while citing another company's alert. That is the prompt being echoed, and it is exactly what the grounding check catches."

### Call 1: issuer channel, ONMD (live; runs in parallel with Call 2; measured 2026-09-29)

`POST https://api.exa.ai/search`

```json
{
  "query": "Press release from OneMedNet Corp (Nasdaq: ONMD) announcing a reverse stock split, with the ratio, the effective date and time, the first day of split-adjusted trading, and the new CUSIP",
  "type": "auto",
  "includeDomains": ["globenewswire.com", "prnewswire.com", "businesswire.com", "accessnewswire.com"],
  "startPublishedDate": "2026-08-20T00:00:00Z",
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only the issuer's own announcements about OneMedNet Corp (Nasdaq: ONMD); ignore every other company and every other security. Copy dates and times exactly as the source writes them. If a later notice updates an earlier one, use the later one. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<shared 8-field schema above>",
  "contents": {"highlights": true}
}
```

The CDT, CTNT and backup rows use the same body with their own issuer name, query wording and start date, all copied from `cache_golden\`.

**Why each parameter (what Ryan will probe):**
- **`query`: retrieval intent only.** It names the document type, the issuer and the facts wanted. The field list lives in the schema and the rules live in the systemPrompt, as Exa's guidance says.
- **`type: "auto"`, on measured evidence.** "Auto filled every field in about two to four seconds for seven-tenths of a cent whenever the page was in the index. I ran the identical body on deep-lite for the CDT exchange call: 1.2 cents, five seconds, and it found nothing extra, because the page isn't in the index. That's one comparison, not a benchmark, but it matches your guidance to use a deep type only when one search can't fill the schema." `auto` is the default, so sending it is optional: "It's the default. I show it so the comparison is readable."
- **No `numResults`.** The server default is already 10. If asked: "I left it at the default of 10."
- **`includeDomains`, fixed in code from channels.json.** "The allowlist is a compliance control the customer supplies and approves: the four primary wires, plus the issuer's own newsroom when their security master has one (Bank of America does). It is fixed in code so neither the model nor the user can widen it. That's the point you raised in Pydantic AI issue 6082 about models putting domain filters into the query." sec.gov is deliberately not in the issuer channel, so the two channels stay separate. The measured bodies hold no syndication mirrors (sites that re-post a release), so none are in the demo; channels.json can still tag a mirror so a mirror-only field never counts as corroborated.
- **`startPublishedDate`: a fixed evidence window.** "The ticket names one event, so a 30-day window is a product rule. publishedDate is Exa's estimate, so code also checks the date printed on the notice." Measured 2026-09-29: one undated page (the stale CTNT alert) still came back with the filter on, so code does not rely on the filter either dropping or keeping undated pages.
- **No `additionalQueries`.** Exa's API spec says it only works with the deep types, so on auto it would at best do nothing.
- **`systemPrompt`.** Names the one issuer (for a bond, the one series and its CUSIP), says which kind of source to use, lets a later notice win (this matters for amended events), copies dates verbatim, and writes "not stated" rather than guessing. Exa's guidance puts keep/drop rules and "what to do when a field cannot be verified" here, not in the query.
- **`outputSchema`.** The eight fields above. Descriptions instead of enums, because enum support is untested.
- **`contents: {"highlights": true}`.** "On search, highlights anchor to my query already, and I have no token budget that needs a cap, so I didn't tune them." A model (the synthesis) and then a person both read excerpts, not whole pages.
- **No `maxAgeHours`.** A press release does not change after publication, so forcing a live crawl only adds latency. Freshness is used only in Call 3.
- **No `category`.** "Exa's guidance says category is only for explicit category-constrained retrieval, and the query already says what I want."

**Response fields used:** `results[].url, title, publishedDate, highlights` (shown and passed through the stale detector and identity guard); `output.content` (the eight fields); `output.grounding[{field, citations[{url,title}], confidence}]` (citation and confidence chip; measured: present on every successful call); `costDollars.total`, `searchTime`, `requestId`. Latency on screen is exa_client's `elapsed_ms` (end to end); `searchTime` is logged but excludes the synthesis phase (measured: about 1.2 to 1.5 s of searchTime inside 3 to 4 s of wall time).

### Call 2: market channel, ONMD (live; in parallel with Call 1; measured 2026-09-29)

```json
{
  "query": "Nasdaq Equity Corporate Actions Alert for OneMedNet Corp (ONMD) reverse stock split and CUSIP change, with the effective date",
  "type": "auto",
  "includeDomains": ["nasdaqtrader.com"],
  "startPublishedDate": "2026-08-20T00:00:00Z",
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only the exchange's or the SEC's official notices about OneMedNet Corp (Nasdaq: ONMD); ignore every other company and every other security. Copy dates and times exactly as the source writes them. If a later notice updates an earlier one, use the later one. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<shared 8-field schema above>",
  "contents": {"highlights": true}
}
```

Line: "The market channel is defined as the exchange's or the SEC's own notice, so the customer's channel config locks it to nasdaqtrader.com for Nasdaq names and sec.gov for bonds and NYSE names." Measured 2026-09-29: the bare host entries matched their `www.` pages (every nasdaqtrader, sec.gov and wire result came back on a `www.` URL).

### Calls 1 and 2: bond variant, BAC (live; measured 2026-09-29)

Issuer channel:

```json
{
  "query": "Press release from Bank of America announcing the redemption of its Floating Rate Senior Notes due September 2027, CUSIP 06051GLX5, with the redemption date and redemption price",
  "type": "auto",
  "includeDomains": ["globenewswire.com", "prnewswire.com", "businesswire.com", "accessnewswire.com", "newsroom.bankofamerica.com"],
  "startPublishedDate": "2026-08-05T00:00:00Z",
  "systemPrompt": "You are checking a security master exception for an investment operations team. Use only the issuer's own announcements about Bank of America Floating Rate Senior Notes due September 2027, CUSIP 06051GLX5; ignore every other company and every other security. Copy dates and times exactly as the source writes them. If a later notice updates an earlier one, use the later one. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<shared 8-field schema above>",
  "contents": {"highlights": true}
}
```

Market channel: the same shape with `"includeDomains": ["sec.gov"]`, the query "Bank of America SEC filing about the redemption of Floating Rate Senior Notes due September 2027, CUSIP 06051GLX5", and "the exchange's or the SEC's official notices" in the systemPrompt. The channel label on screen is "SEC filing (issuer, legally filed)".

- `newsroom.bankofamerica.com` comes from the security master's issuer record and lives in channels.json.
- **The CUSIP goes in the systemPrompt** because BAC's Sep 4 release covers two series: $500,000,000 Floating Rate Senior Notes (06051GLX5) and $1,500,000,000 5.933% Fixed/Floating Rate Senior Notes (06051GLV9), both due September 2027. A separate BAC CAD-notes release uses the same "Due September 2027" wording. Code also rejects any record whose identifier is a different series.
- **Bond identity key:** issuer, coupon, maturity, and the CUSIP when printed. Issuer redemption releases often name notes by coupon and maturity, and "BAC" is the stock ticker, not the bond's. Measured: the model returned identifier_in_source "06051GLX5" with high confidence, cited to the newsroom release.
- Say plainly: the truly independent sources for bonds (trustee or DTC notices) sit behind logins, which is exactly where the licensed feeds stay the source of truth. When the SEC channel does return the redemption, it is usually the issuer's own release filed again as an 8-K exhibit, so code would show "Same-issuer confirmation", not "Corroborated".

**Channel config by asset class** (data\channels.json):

| Asset class | Issuer channel | Market channel (label) |
|---|---|---|
| Nasdaq-listed equity | the four issuer wires | `["nasdaqtrader.com"]` (Exchange alert) |
| NYSE-listed equity (no per-issuer alert source was found) | the four issuer wires | `["sec.gov"]` (SEC filing, 8-K (issuer, legally filed)) |
| Corporate bonds | the four wires plus the issuer's newsroom from the security master | `["sec.gov"]` (SEC filing: issuer, legally filed) |

**Measured for a Call 1 plus Call 2 pair on auto (2026-09-29):** 20 calls took 1.9 to 4.1 s each (median about 3.1 s), so a parallel pair takes about 3 to 4 s of wall time. Every call cost $0.007 (costDollars broke it down as search only, so the outputSchema added nothing), so $0.014 a pair. The timebox is 8 s.

**Measured results for the demo rows (2026-09-29):**

| Row | Issuer channel | Market channel | Row chip |
|---|---|---|---|
| ONMD | GlobeNewswire Sep 25. terms 1-for-10; effective "12:01 a.m. Eastern Time on September 29, 2026"; market_effective_date 2026-09-29; new_cusip "68270C 202"; all 8 fields high | Alert 2026-688, printed Fri Sep 25. terms "one-for-ten (1-10)"; effective "Tuesday, September 29, 2026"; new_cusip "68270C202"; all 8 fields high | Corroborated, two independent sources (after code strips the space from the CUSIP and normalizes both ratios to 1-for-10) |
| CDT | GlobeNewswire Sep 25. terms 1-for-25; effective "September 28, 2026, at 5:00 pm, Eastern Time"; market_effective_date 2026-09-29; new_cusip 20678X700; all 8 fields high | Alert 2026-683 not returned on auto or deep-lite. Top results were alerts 654 (NFE), 665 and 651. Seven fields "not stated"; identifier "CDT" at low confidence cited to alert 654, which the grounding check rejects | Single source, issuer only, with the explained difference inside the issuer's own release |
| BAC | Bank of America newsroom Sep 4 (PR Newswire copy also returned). terms "100% of the principal amount of such series, plus accrued and unpaid interest to, but excluding, the redemption date of September 15, 2026"; market_effective_date 2026-09-15; identifier 06051GLX5; all fields high | sec.gov returned unrelated filings from other companies; all fields "not stated", no grounding | Single source, issuer only |
| CTNT | No reverse-split release on the wires. Top result was an unrelated CTNT release of Sep 15; split fields "not stated" | Result 1 is alert 2026-677, title correct, highlights "Page Not Available", no publishedDate. All 8 fields "not stated" at HIGH confidence, cited to that placeholder | Stale source, not confirmed |

Why CDT's alert counts as "not in Exa's index" rather than "filtered out": a /contents call on alert 683 with no freshness setting came back with source "crawled", not "cached", which means Exa had no stored copy, and the crawl returned empty text.

**What code does next (evidence.py), before anything is shown as agreed. Order matters:**
1. **Stale detector, on the raw results, before the identity guard.** A "Page Not Available" placeholder contains no ticker in its text, so the guard would otherwise drop it before the detector sees it. It fires when a market-channel result URL matches `nasdaqtrader.com/TraderNews.aspx?id=ECA` and its highlights contain "Page Not Available" or are empty. Measured: it would fire on CTNT's alert 677. The URL it passes to Call 3 comes from these raw results, which also gives a free-form row a URL to try.
2. **Identity guard on results.** Keep a result only if its title or highlights contain an exchange-prefixed ticker ("Nasdaq: CDT", "NASDAQ:CDT", "Symbol: CDT"), a CUSIP (spaces removed, uppercased), or the issuer's legal name. For a bond: the issuer's name plus either the CUSIP or the coupon and maturity. A bare ticker match is amber only, because "CDT" is also Central Daylight Time and appears in many wire releases ("10:00 a.m. CDT"). Measured: nasdaqtrader alert titles carry the issuer's legal name and ticker (for example "Information Regarding the Reverse Stock Split and CUSIP Number Change for OneMedNet Corp (ONMD)").
3. **Value check: code reads the value, never the confidence label alone.** Any field whose value is "not stated" (any case) or empty is treated as missing, whatever its confidence reads. Measured: on CTNT's exchange call all eight fields read "not stated" with HIGH confidence, cited to the placeholder page. Confidence alone would have passed them.
4. **Grounding check: the primary identity guard.** For every field that has a value, each `output.grounding` citation URL must be inside that call's `includeDomains`, must be among the results that passed step 2, and the cited page's own title or highlights must contain the identifier, checked by code against the retrieved text. A field that fails goes amber, "unverified", and stays out of the ticket note. Measured: this is what rejects CDT's identifier "CDT" cited to NFE's alert 654.
5. **Window check.** compare.py drops any record whose `source_notice_date` (the date printed on the notice) is before the row's window start.
6. **Normalization.** CUSIPs lose spaces and are uppercased before comparing ("68270C 202" becomes "68270C202"); ratios like "one-for-ten (1-10)" and "1-for-10" become the same (new, old) pair.
7. **Corroboration rule.** A row is "Corroborated" only when two independent sources each give the value, each passes steps 3 and 4, and neither page is stale or empty. Otherwise the chip says exactly which source is missing.

### Call 3: stale-page repair, attempted (live, only when the stale detector fires; measured 2026-09-29)

`POST https://api.exa.ai/contents`. Code takes the URL from Call 2's raw results, before the identity guard runs.

```json
{
  "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
  "highlights": true,
  "maxAgeHours": 0,
  "livecrawlTimeout": 12000
}
```

**Why each parameter:**
- **Top-level options, no `contents` wrapper.** On /contents, text, highlights and summary are top-level fields; on /search they sit inside `contents`. A good 10-second talking point on the shape difference.
- **`maxAgeHours: 0`.** "Code fires this only when Exa's stored copy is a placeholder, so I pay for a live crawl on one known URL instead of on every search result. That's the content-must-be-current case in your freshness guidance." It controls how fresh the returned text is, not which pages exist.
- **`livecrawlTimeout: 12000`.** Exa's guidance says to set it whenever live crawling matters so a slow page cannot block the request. exa_client's timeout override is 20 s for this call, because the default for a body with no `type` is 15 s.
- **`highlights: true`, one content type.** It is the body that was measured, so it is in the golden cache.

**What actually happened (measured 2026-09-29):**
- /contents on alert 677 with no freshness setting: source "cached", title and highlights "Page Not Available", 0.5 s, $0.001.
- The body above: status "success", source "crawled", but the title is the bare file name ("TraderNews.aspx?id=ECA2026-677") and the text and highlights are EMPTY. 1.3 s, billed $0.
- The same with `"text": {"maxCharacters": 1500}` instead of highlights: whitespace only, 1.2 s, $0.001. With a highlights query: empty, $0.
- The same results for alert 683 (CDT).
- So a forced live fetch of nasdaqtrader.com through the API returns an empty page. The keyless MCP probe on Sep 29 that seemed to repair the page does not reproduce through the API; never cite it as working.
- Version 2's summary-with-schema body was not tested. With an empty page there is nothing to summarize, so it is dropped.

**The empty-text check (the reason this call stays in the spec).** Code treats a /contents result as a failure when `status` is "success" but the text and highlights are empty after stripping whitespace, or the title is just the file name. The column then shows "Live re-fetch returned an empty page (source: crawled, 1.3 s)", the row stays "Stale source, not confirmed", and the ticket note routes it to the analyst with the link and that reason. Code never marks a row corroborated from a stale or empty page. The screen also shows the per-URL `statuses` verbatim, including CRAWL_TIMEOUT or CRAWL_LIVECRAWL_TIMEOUT if they occur.

**What AJ says it means (the FDE line):** "This is a coverage gap on one source the customer can't do without. Of four Nasdaq alerts I checked from the same week, 682 and 688 are indexed, 683 is missing, and 677 is stored as a placeholder, and a forced live fetch comes back empty. What I'd ask Exa for is a recrawl of those alert pages, or, for a customer on an enterprise plan, a custom index for the must-have sources. Your enterprise pricing lists custom indexes, and I'd want to know from you how that's scoped." (Custom indexes appear on Exa's enterprise pricing card; how they are scoped is a question, not a claim.)

**Cost:** $0 to $0.001 per attempt (measured).

### Call 4: publication-date-bounded replay (not yet run; used in answers and in the POC)

This is the measured Call 1 or Call 2 body plus one field. Example for ONMD's Call 2, whose alert Exa does hold:

```json
{
  "query": "Nasdaq Equity Corporate Actions Alert for OneMedNet Corp (ONMD) reverse stock split and CUSIP change, with the effective date",
  "type": "auto",
  "includeDomains": ["nasdaqtrader.com"],
  "startPublishedDate": "2026-08-20T00:00:00Z",
  "endPublishedDate": "2026-09-28T11:30:00Z",
  "systemPrompt": "<same as Call 2>",
  "outputSchema": "<shared 8-field schema above>",
  "contents": {"highlights": true}
}
```

`2026-09-28T11:30:00Z` is 7:30 AM ET on Sep 28, when the ONMD ticket opened (a mocked time, fixed in rows.json).

**The line:** "The replay's whole question is what was published before the ticket opened, so it's a bounded window that must be enforced. I call it a publication-date-bounded replay, not no-hindsight, because page content and ranking are still today's. Snapshot is the stricter check."

Optional add-on (AJ decides): "In my paper-trading research system, the hardest rule was using only what was knowable on the date. This replay only partly meets that rule, which is why I name its leaks." Say "paper-trading research system", never "production", and skip feed and test counts.

**Its leaks, named out loud:**
1. The page text, highlights and synthesis come from Exa's current stored copy, not the copy that existed at 7:30 AM.
2. Ranking uses today's signals.
3. publishedDate is an estimate, so a mis-dated page can drop out or slip in.

**The strict point-in-time check** is a Snapshot arm: the same body on type auto with `"contents": {"highlights": true, "snapshotAsOf": "<ticket open time>"}`. Snapshot pins the text to Exa's stored version at or before that time; it bounds content, not ranking. It supports auto, fast and instant only, never with `maxAgeHours`, `livecrawl`, `livecrawlTimeout`, `subpages` or `category`. It is unverified whether it combines with `outputSchema` and `includeDomains`, and it falls under the 100-request Snapshot limit, so beyond a demo it is part of the enterprise trial ask (section 9).

Measured 2026-09-29: the ONMD release and alert 688 both print Friday Sep 25, so both were public before a Sep 28 7:30 AM ticket. Say that only after the replay itself has run.

**Cost:** $0.014 for the pair on auto (the measured per-call price).

### Call 5: Snapshot audit copy (to pre-run before Friday, cached, never live; unverified)

```json
{
  "urls": ["<ONMD GlobeNewswire release URL from Call 1>", "https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-688"],
  "snapshotAsOf": "2026-09-28T11:30:00Z",
  "highlights": {"query": "effective date, split ratio, new CUSIP"}
}
```

- This is the auditor's question: "what did each source say when we loaded it?"
- `snapshotAsOf` is top level on /contents and is never sent with `maxAgeHours` or `livecrawl`.
- Check `statuses` for `CONTENT_NOT_CACHED` (Exa had no stored copy by then). If either URL returns it, the panel says so.
- A second pre-run on CTNT's alert 677 would show what Exa had stored for it at ticket time; if that is the placeholder, show it as the honest reason Snapshot exists, never as proof the alert was knowable.
- Limits to quote: a rolling 5-month window, 10 QPS (queries per second) on pay-as-you-go, and 100 Snapshot requests before a sales conversation. Do not call it a "research preview" unless a re-check of Exa's docs finds that label.
- **Cost:** $0.002 at list (2 pages, one content type). Budget about 5 Snapshot calls in total.

### Call 6: early warning (shown as JSON on Screen 3, never run live)

**Production early warning under ZDR: a scheduled /search from the customer's own scheduler.** Exa's build guidance says Monitors are not ZDR, and these queries reveal holdings, so this is the default production path.

```json
{
  "query": "Bank of America announces redemption, tender offer or exchange offer for its notes or preferred shares",
  "type": "auto",
  "includeDomains": ["prnewswire.com", "businesswire.com", "globenewswire.com", "newsroom.bankofamerica.com", "sec.gov"],
  "startPublishedDate": "<last successful run time minus 7 days>",
  "systemPrompt": "Report only actions announced by Bank of America on its own notes or preferred shares. Ignore every other issuer. Copy dates exactly as written. Write not stated for any field the source does not give. Never infer.",
  "outputSchema": "<the Call 6 events schema below>",
  "contents": {"highlights": true}
}
```

`startPublishedDate` is justified here because the job's stated window is "new since the last run", and the 7-day overlap absorbs mis-dated pages. Code also dedupes by URL against tickets already opened.

**Monitor body: the option for teams that accept non-ZDR** (valid per Exa's OpenAPI spec, not created live):

```json
{
  "name": "held-issuer watch: Bank of America",
  "search": {
    "query": "Bank of America announces redemption, tender offer or exchange offer for its notes or preferred shares",
    "includeDomains": ["prnewswire.com", "businesswire.com", "globenewswire.com", "newsroom.bankofamerica.com", "sec.gov"],
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
  "metadata": {"team": "security-master", "issuer": "BAC"},
  "webhook": {"url": "https://<customer ticket bridge>/exa-monitor", "events": ["monitor.run.completed"]}
}
```

**Why:**
- The line on ZDR: "Exa's own guidance says Monitors aren't covered by ZDR, and these queries reveal holdings, so under ZDR the daily watch runs as a scheduled search from the customer's scheduler."
- The allowlist gets the same compliance line as Call 1, including the issuer's newsroom. Monitor search accepts no systemPrompt, type or date filters, so the issuer and series constraints go in the query, and the identity guard runs on the webhook payload.
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
- **additionalQueries, numResults, highlight options:** covered under Call 1.
- **A summary schema on /contents for the repair:** dropped, because the live fetch of nasdaqtrader.com returns an empty page (Call 3).

### Per-exception cost and latency summary

| Call | When | Latency | Cost | Status |
|---|---|---|---|---|
| 1 + 2 in parallel (auto) | every exception | 1.9 to 4.1 s per call, median about 3.1 s; about 3 to 4 s for the pair | $0.007 per call, $0.014 per pair | measured 2026-09-29 (20 calls) |
| 1 or 2 on deep-lite | not used; comparison only | 5.0 s | $0.012 | measured 2026-09-29 (1 call) |
| 3 attempted repair | only when the stale detector fires | 0.5 to 1.3 s | $0 to $0.001 | measured 2026-09-29; returns an empty page on nasdaqtrader.com |
| 4 replay | answers and the POC eval | about 3 s (same body plus one field) | $0.014 | unverified, not yet run |
| 5 Snapshot | audit, on demand | unknown | $0.002 | unverified, not yet run |
| 6 scheduled search (ZDR path) | daily per watched issuer | about 3 s, off the live path | $0.007 per run | unverified |
| 6 Monitor (non-ZDR option) | daily per watched issuer | async | $0.015 per run | list price, not run |

## 5. Reliability design

**Timebox, visible on screen, that cannot block.**
- **One module-level thread pool, never a with-block.** `EXECUTOR = ThreadPoolExecutor(max_workers=4)` is created once at the top of evidence.py. Streamlit imports the module once per server process, so reruns reuse it. A `with ThreadPoolExecutor() as ex:` block is banned, because leaving the block waits for every thread to finish, which would silently turn the 8-second timebox into exa_client's 15-second request timeout plus retries.
- **A polling loop, not one long wait.** `run_row()` loops `concurrent.futures.wait(pending, timeout=0.5)` and calls an `on_tick` callback every half second, which updates `st.empty()` placeholders: a counting timer next to each column. The audience sees the timebox, not a hang.
- **At the deadline** (8 s on auto, about twice the slowest measured call), for each channel not back, `run_row()` calls `exa_client.search(body, cache_only=True)` and sets `envelope["error"] = f"live call still running past {timebox_s} s"` on the envelope it gets back. That envelope's `source` ("cache" or "none") and `saved_from` ("golden" or "working") drive the badge, for example "Saved run from Tue 9/29 09:19, reason: live call still running past 8 s". The other channel renders live. Partial results beat a spinner.
- **The late thread is left alone.** Python cannot stop a running thread. It finishes when Exa answers or its own request timeout fires, writes its answer to `cache\` (never `cache_golden\`), and frees its limiter slot.
- **Shared limiter.** One `threading.BoundedSemaphore(4)` in exa_client wraps every live request, across rows and channels, and request starts are spaced at least 250 ms apart. So at most 4 calls are in flight and at most 4 start in any second. That keeps a Run all well under the 10 QPS limit for /search on auto. Spoken line: "A shared limiter keeps us under Exa's rate limits." Run all sends rows one at a time through run_row (each row's two calls in parallel), so no call waits on the limiter inside its own timebox.
- **Simulate timeout** delays the market-channel worker by 20 s before its real call, so the drill runs the same code as a real slow call. Before Friday, one genuinely slow call is also run under the timebox, not just the flag (unverified until then).

**Hard timeouts under the timebox.**
- exa_client's `TIMEOUT_BY_TYPE`: auto 15 s. The new `timeout=` override is used for Call 3 (20 s: a 12 s live crawl plus overhead).
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

**Checks on what comes back, from what was measured on 2026-09-29 (to be built into evidence.py and compare.py).**
- **Values, not confidence labels.** Grounding confidence can read "high" on a field whose value is "not stated" (all eight CTNT exchange fields did, cited to the placeholder page). So code treats "not stated" or an empty value as missing whatever the confidence says, and a confidence chip is shown only next to a real value.
- **Empty "success" is a failure.** A /contents result with status "success" and empty text and highlights (the forced live fetch of nasdaqtrader.com) is shown as "live re-fetch returned an empty page" and never fills a field.
- **No row is corroborated from a stale or empty page.** The corroboration rule needs two independent sources with real values that each pass the grounding check.
- **What the model did with missing pages, as a measured observation, not a guarantee:** across the 22 search calls in the Sep 29 record (21 of them with the schema), when the right page was not in the results the fields came back "not stated". No split ratio, date or CUSIP was invented. The one echo seen was the CDT exchange call returning the prompted ticker "CDT" as the identifier at low confidence, cited to another company's alert, which the grounding check rejects. Twenty-two calls is a small sample, so the checks above stay in code regardless.

**Two cache folders.**
- `cache_golden\` is read-only: the frozen known-good runs from Sep 29 (30 saved responses: 22 searches and 8 /contents calls), plus anything added before Friday by one deliberate copy. Nothing in the app ever writes to it. "Saved runs only" and every fallback read it first.
- `cache\` is the working folder: every live success is written there. Fallback reads it second (useful for a row with no golden copy, such as a free-form row run earlier in the session).
- The cache key is a hash of the exact request body, so two gotchas follow:
  1. Every date and every piece of recency wording in a body is fixed text in rows.json, never computed from `now()`, or Friday's bodies will not match the saved runs.
  2. A Friday warm-up that returns worse results can never overwrite the golden copy, because live calls write only to `cache\`.
- The Sep 29 copy into `cache_golden\` is done. If the Snapshot pre-run or the replay is added before Friday, copy only those new files in once, then leave the folder alone.

**Exact changes to app\exa_client.py** (it keeps its envelope, retries and plain-HTTP design; these are additions):
1. **Folders.** Add `GOLDEN_DIR = PROJECT_DIR / "cache_golden"` next to `CACHE_DIR`. Give `cache_path(endpoint, body, folder=CACHE_DIR)` a folder argument (the hash is unchanged, so the Sep 29 files keep their names).
2. **Read order.** In `call()`, load the fallback from `GOLDEN_DIR` first, then `CACHE_DIR`, and record which one in a new envelope key, `saved_from` ("golden" or "working"). `from_cache()` uses that record.
3. **Write target.** `_write_cache()` writes only to `CACHE_DIR`. It writes to a temp file named per thread, `path.with_name(f"{path.stem}.{os.getpid()}.{threading.get_ident()}.tmp")`, then calls `os.replace()` to move it into place, so a late thread never leaves a half-written file. The whole write is wrapped in `try/except OSError`. On failure the temp file is removed and the live envelope is still returned, with `cache_write_error` set, because a failed save must never turn a live success into a crash.
4. **Timeout override.** Add `timeout=None` to `call()`, `search()` and `contents()`. When it is None, keep today's `TIMEOUT_BY_TYPE` lookup (15 s for a body with no `type`).
5. **Shared limiter.** Add `import threading`, a module-level `_LIMIT = threading.BoundedSemaphore(4)`, and a start-spacing lock (at least 250 ms between request starts). Every attempt, including each retry, acquires `_LIMIT` and passes the spacing lock immediately before its own `requests.post()`, and releases `_LIMIT` as soon as that post returns or raises. No slot is held during a retry's `time.sleep()`.
6. **/contents pricing.** In `_envelope()`, when `costDollars` is missing and the endpoint is `/contents`, price it as `len(body.get("urls") or body.get("ids") or []) * max(1, sum(1 for k in ("text", "highlights", "summary") if body.get(k))) * 0.001`. The max(1, ...) covers Exa's default of full text when no content type is named. Today it wrongly falls back to the /search price of $0.007. /search keeps `PRICE_BY_TYPE`. Run all totals and the call log's dollar column sum `cost_dollars` only where `source == "live"`.
7. **Queue headers.** Copy `x-request-id`, `x-exa-queued` and `x-exa-queue-ms` from `resp.headers` into plain values: `queued = resp.headers.get("x-exa-queued") == "true"`, `queue_ms = int(resp.headers.get("x-exa-queue-ms") or 0)`. Store them in the cache record and pass them to `_envelope()` as new keyword arguments, so every envelope carries `queued`, `queue_ms` and `saved_from` (empty for live). The call log shows whether a request waited in Exa's rate-limit queue.
8. **Docstring.** Correct the module docstring's SDK sentence to the reworded exa-py reason in section 4 (search() adds text only when you pass no contents; get_contents adds text even with highlights). Update 'HOW ONE CALL FLOWS' to say the fallback reads cache_golden then cache, and add `saved_from`, `queued` and `queue_ms` to 'WHAT AN ENVELOPE LOOKS LIKE'.

**Pre-flight, Friday 5:45 PM.**
- Check https://status.exa.ai/summary.json.
- Run ONMD, CDT and BAC once live to warm `cache\` (never golden), and check each matches the measured results in section 4.
- Run CTNT's Call 2 only, to see whether the stale detector still fires live. If Exa has refreshed alert 677 since Sep 29, the scene runs from the saved run and AJ says so. Do not press the repair in pre-flight; it was already measured on Sep 29.
- Confirm credits and the per-key budget in the dashboard.
- Close the network-heavy apps.

**Security of the key.**
- It lives in `.env`, is read server-side only, and never goes into the browser. Exa's CORS settings (the browser rule for cross-site calls) would allow a direct browser call, which is exactly why the key stays server-side.
- Set a per-key budget (`budgetCents`) of $5 in the dashboard, if it is not set already (not confirmed in the Sep 29 record).

## 6. The three slides

**Slide 1. "7:40 AM: two vendors, one security, who is right?"**
- **Customer and user:** a US asset manager running index and total-market equity products alongside investment-grade credit (size is an assumption). A team of 3 to 4 security master analysts clears one shared queue of breaks (rows where the two licensed data vendors disagree) before the 9:30 open. The golden copy is the firm's master security record.
- **Today:** each break where the licensed feeds disagree needs primary-source evidence found by hand on Google, EDGAR (the SEC's filing database) and Nasdaq Trader (Nasdaq's notice site). That is an assumed 15 to 25 minutes each, with links pasted into the ticket. On a heavy day some breaks are still open at 9:30.
- **This month, for real:**
  - OneMedNet (ONMD), 1-for-10 reverse split (every 10 old shares become 1 new share), new CUSIP (the 9-character US security ID) from Sep 29.
  - CDT Equity (CDT), 1-for-25. The issuer says effective Sep 28 at 5:00 PM ET, with split-adjusted trading from the Sep 29 open. Two meanings of "effective".
  - A Bank of America floating-rate note (CUSIP 06051GLX5), redeemed Sep 15.
- **What a wrong or late fix breaks:**
  - price and quantity fall out of step by the split factor, which trips the NAV check (NAV is the fund's daily net asset value) and costs an investigation on deadline, and possibly a late NAV;
  - orders on a retired CUSIP reject at the broker;
  - ownership-limit compliance rules divide by the wrong share count;
  - a redeemed bond stays open on the books.

**Slide 2. "The tiebreaker is on the public web. Exa makes it a two-call step."**
- **Licensed feeds stay the system of record (the official source the firm books from).** Bloomberg, LSEG, ICE and DTCC (the US settlement and depository utility) remain the source of truth. The exception exists because they disagree or lag, so neither feed can settle it.
- **The tiebreaker is the issuer's own words plus the exchange or SEC notice.** Break Check makes one Exa search per source type, limited to a domain list the customer approves, and gets each field back with a citation and a confidence level.
- **Why Exa and not a scraper:** "For Nasdaq names you could scrape the alert page. The long tail of issuer newsrooms, wires, bond redemptions and 8-K filings (a company's SEC report of a major event) is where one plain-language search beats a scraper per site." One call, answered while you wait, returns the page, the highlighted sentences and per-field citations with confidence.
- **Code compares, not a model.** It applies fixed rules (for example "legal effective after the close vs market effective at the open"), reads every value rather than trusting a confidence label, and never calls a row confirmed from one source or from a stale page. The analyst approves, and the ticket note is drafted with the links.
- **Enterprise fit:** these lookups reveal holdings, so production runs under Zero Data Retention (ZDR: Exa keeps nothing from the request). Search, which carries every routine lookup, is ZDR-covered in both Exa sources I read. The occasional one-page re-fetch uses Contents, which one of those sources does not list, so I'd confirm it. Exa states SOC 2 Type II (an independently audited report on security controls), with reports at trust.exa.ai.

**Slide 3. "Impact, cost, and a proof of concept"**
- **First: breaks still open at 9:30.** Today, evidence-gathering can fill most of the team's pre-open window on a heavy day (section 8). With a 3 to 5 minute review per break (an assumption), the same team would clear the queue before the open on a base-case day; the POC shadow week measures it. The customer prices a late or wrong fix from its own incident log. Illustration only: one 40-hour NAV investigation a quarter is about $12K a year in staff time, before any reimbursement to the fund.
- **Second: analyst time** (assumptions to confirm): about $45K a year (floor) to $126K (base), at $75 an hour loaded cost (salary plus benefits and overhead). Next to it, AJ's timed manual baseline if it has been run (section 8).
- **Exa spend, measured on Sep 29:** $0.007 per search, so $0.014 per exception on auto, in about 3 to 4 seconds. That is under $100 a year for the queue. A daily early-warning watch on 300 held credit issuers is about $530 a year as scheduled searches. The point is not the spend: Break Check is the workload that takes Exa through security review and ZDR at an asset manager.
- **Proof of concept (POC: a trial to prove value before purchase):** a week-0 security review, a public-data eval that needs no holdings, then 150 of the customer's closed tickets once ZDR is on, then a shadow week (analysts use the card alongside today's process). Pass means all of these:
  - issuer source found for 90% or more
  - terms, market effective date and new identifier match the analyst's resolution for 95% or more
  - zero wrong-issuer citations
  - at most 1 high-confidence wrong field
  - median under 8 s
  - fewer breaks still open at 9:30, and handling time halved, in the shadow week
  - a coverage report on the customer's must-have sources (for example, which exchange alerts are indexed), with a fix agreed for any gap
- **Questions for you:** how many breaks a day need an outside check, how many are still open at 9:30, and which NAV correction or failed trade last year traced back to one?

Every slide statement is a verified public fact (re-checked before Friday), an Exa documented fact, a number measured on Sep 29, or a number labeled as an assumption. No client names.

## 7. Demo script, minute by minute

**Every scene has four parts, spoken out loud: hypothesis, action, result, and "if it comes back different, I check X next".** The hypothesis and the "if different" line are stored in rows.json and shown in the "Presenter notes" panel. Results below are what was measured on 2026-09-29; if Friday's live call differs, say so and use the "if different" line.

**Timing at a glance**

| Clock | Block | Minutes |
|---|---|---|
| 0:00 to 0:30 | Open | 0.5 |
| 0:30 to 3:00 | Slide 1: the analyst's morning, plus the credibility line | 2.5 |
| 3:00 to 5:00 | Slide 2: the thesis | 2 |
| 5:00 to 7:30 | Scene 1: ONMD, the clean path (includes 20 s on the queue) | 2.5 |
| 7:30 to 11:00 | Scene 2: CDT, two meanings of "effective" | 3.5 |
| 11:00 to 13:30 | Scene 3: BAC bond, redeemed but still live at one vendor | 2.5 |
| 13:30 to 16:30 | Scene 4: CTNT, when it goes wrong, plus the timeout drill | 3 |
| 16:30 to 19:00 | Scene 5: a security Ryan names | 2.5 |
| 19:00 to 20:00 | Under the hood | 1 |
| 20:00 to 24:00 | Slide 3: impact, cost and the POC plan | 4 |
| 24:00 to 30:00 | Questions, both ways | 6 |

**If running long:** cut the under-the-hood minute first (its content is there for questions), then shorten Scene 5 to one run with no second attempt. Never cut the CTNT scene.

**0:00 to 0:30. Open.**
"I'll spend about five minutes on the customer, fourteen on five live scenes, a few on impact and a POC plan, and leave the rest for questions. Interrupt me anywhere."

**0:30 to 3:00. Slide 1: the analyst's morning.**
Tell it as the team's morning: the shared queue, the 9:30 deadline, the three real events from September, what a wrong or late fix breaks.
Credibility line, word for word: "I spent two and a half years at Charles River as the primary FIX analyst for five buy-side clients. When security reference data was wrong, trades busted, and I was the one working out with the trader and the data team which provider caused it." Never name a client.

**3:00 to 5:00. Slide 2: the thesis.**
One sentence: "Licensed feeds stay the record; Exa supplies the primary-source evidence for the exceptions they produce."
The scraper answer, before he asks: the long tail of issuer newsrooms, wires, bond redemptions and 8-Ks.
Say plainly: "The vendor records are mocked, since this is a demo and not a customer's security master. Every source page is retrieved by Exa, live or from a labeled saved run."

**5:00 to 7:30. Scene 1: ONMD, the clean path.**
- **Queue (20 s):** "Four real breaks from September. I'll start with the one that should just work, then show you the harder ones." Point at the field in dispute on each row.
- **Hypothesis:** "OneMedNet did a 1-for-10 reverse split. Vendor A has a new CUSIP from Sep 29; Vendor B shows no change. The analyst needs two independent sources, the company's words and the exchange's notice, so I send Exa two searches in parallel on auto. I expect the GlobeNewswire release on the left and Nasdaq alert 688 on the right in about three to four seconds, and both should give 68270C202."
- **Action:** open "Show request" and walk it in 30 seconds: the query is intent only, the domain list is the customer's and fixed in code, the rules are in the systemPrompt, a fixed 30-day start date, eight schema fields, bare highlights. Press Check.
- **Result (measured 2026-09-29):**
  - Issuer: 1-for-10, effective "12:01 a.m. Eastern Time on September 29, 2026", CUSIP printed "68270C 202".
  - Exchange: alert 688, "one-for-ten (1-10)", effective "Tuesday, September 29, 2026", CUSIP "68270C202".
  - "The issuer prints the CUSIP with a space and Nasdaq doesn't. Code strips the space, so the CUSIP, ratio and date all match. That's corroborated by two independent sources, and it's code saying so, not the model."
  - Click one grounding link so the room reads the sentence on nasdaqtrader.com. Point at latency, $0.014 for the pair and the requestId.
- **Next user step:** "Load the new CUSIP for the Sep 29 open, and send Vendor B a correction with both links. Vendor B is lagging here, so that one really is a vendor ticket." Press Approve under the ticket note.
- **If different:** if one column is empty, open the "Identity guard" panel to see whether the right page came back and was dropped; if the live call is slow, the timebox takes over (that's Scene 4). If ONMD misbehaves, switch to AGRZ, which was also corroborated on Sep 29.

**7:30 to 11:00. Scene 2: CDT, two meanings of "effective".**
- **Hypothesis:** "CDT Equity did a 1-for-25. Vendor A says market-effective Sep 28, Vendor B says Sep 29. I expect the issuer release to say effective Sep 28 at 5 PM, after the close, with trading on new terms from Sep 29, and I expect Nasdaq alert 683 to say Sep 29. If the alert doesn't come back, the row has to say single source, not corroborated."
- **Action:** press Check.
- **Result (measured 2026-09-29):**
  - Issuer: 1-for-25, CUSIP 20678X700, effective "September 28, 2026, at 5:00 pm, Eastern Time", market_effective_date 2026-09-29, all fields high confidence.
  - The row shows "Explained difference: legal effective after the close vs market effective at the open. Adjust positions for the Sep 29 open." "That label is a fixed rule in compare.py, applied to the two dates inside the issuer's own release."
  - Exchange: alert 683 is not in Exa's index. Alerts 682 and 688 from the same day are. The column shows other companies' alerts filtered out by the identity guard, and the one field the model filled, identifier "CDT" at low confidence, rejected by the grounding check because it cites New Fortress Energy's alert.
  - The row label says "Single source, issuer only". "I'd rather show you one honest source than two sources where one is the wrong company."
- **Next user step:** "Load the split for the Sep 29 open. Then check whether Vendor A's Sep 28 is the legal effective date landing in a field our golden copy reads as the market date. That's a mapping or precedence question on our side, not necessarily a vendor error. The analyst opens alert 683 in a browser to add the second source." (Optional, true: "That's the same unmapped-field problem I built a pre-go-live harness for at Adroit.") Press Approve.
- **If different:** if alert 683 does come back live on Friday, Exa has indexed it since Tuesday: read the dates, and the row becomes corroborated with the explained difference. If the issuer column is empty, check the "Identity guard" panel, then the start date in the body.

**11:00 to 13:30. Scene 3: BAC, a bond that no longer exists.**
- **Hypothesis:** "Fixed income now. Bank of America redeemed its Floating Rate Senior Notes due September 2027 on Sep 15. Vendor A shows it redeemed; Vendor B still shows it outstanding. There's no exchange alert for a bond, so the second channel is SEC filings. The release covers two series, so the CUSIP 06051GLX5 is in the systemPrompt, and I expect Exa to report only this series."
- **Action:** press Check. Point at the bond identity key: issuer, coupon, maturity, and the CUSIP when printed.
- **Result (measured 2026-09-29):**
  - Issuer: Bank of America's newsroom release of Sep 4: redemption at 100% of principal plus accrued and unpaid interest, redemption date Sep 15, 2026, identifier 06051GLX5, all high confidence. The identity check confirms 06051GLX5 is on the cited page and the second series is not the one reported.
  - SEC channel: unrelated filings from other companies, every field "not stated", all filtered out.
  - Row label: "Single source, issuer only". "For bonds the truly independent sources, trustee and DTC notices, sit behind logins. That's exactly where the licensed feeds stay the source of truth."
- **Next user step:** "Mark the note redeemed as of Sep 15 in the golden copy, and send Vendor B a correction with the issuer link. The bigger production case is the redemption neither vendor has yet: a daily search on held issuers, which is on the last screen."
- **If different:** if the result names the other series (the 5.933% fixed/floating notes), the series rule and identity check should reject it; open the "Identity guard" panel to confirm. If only the PR Newswire copy comes back, it is still the issuer's own release.

**13:30 to 16:30. Scene 4: CTNT, when it goes wrong, plus the timeout drill.**
- **Hypothesis:** "Cheetah Net did a 1-for-150. This is the row where I expect Exa's stored copy to let me down, and I want to show you what the app does about it. If the stored copy of the exchange alert is a placeholder, code should notice, make one live re-fetch, and only trust the result if real text comes back."
- **Action:** press Check. The re-fetch runs by itself when the stale detector fires; there is no extra button.
- **Result (measured 2026-09-29, afternoon):**
  - Issuer channel: it finds a real Cheetah Net release, but it is about an acquisition, not the split. "Right company, wrong event. Code does not count it as evidence, and the ticket note does not cite it."
  - Market channel: Exa's stored copy of alert 677 reads "Page Not Available". All eight fields come back "not stated", and the Exa confidence column reads high. "This is why code reads the value, never the confidence label alone. High confidence here means the model is sure the page says nothing."
  - The stale detector fires and the panel "Stale-page repair: one live re-fetch through /contents" appears: one call with maxAgeHours 0, about 1 second, $0.001. It returns the real alert: 1-for-150, effective Monday Sep 28, CUSIP 16307X400.
  - Row label: "Stale source repaired, one source, analyst confirms". "Code will not call this corroborated. It is one source, and it came through a repair, so a person signs off."
  - **The honest part, say it plainly:** "On Tuesday morning this same re-fetch came back with status success and an empty page. Code treats an empty success as a failure, and the row read 'Not confirmed, route to analyst'. By the afternoon the same call returned the real page. So that failure was temporary, but I kept the check and the test for it, because a customer will hit it again."
- **What I'd ask Exa to fix (the FDE line):** "Of four Nasdaq alerts from that week, 682 and 688 are indexed, 683 is missing, and 677 is stored as a placeholder. The live re-fetch fixes 677 for a tenth of a cent, but it failed once on Tuesday morning. For this customer those alerts are a must-have source. I'd ask for a recrawl of those pages, or, on an enterprise plan, a custom index for the customer's must-have sources. I'd want to know from you how that gets scoped."
- **Second half, the timeout drill (about 45 s):**
  - **Hypothesis:** "The other way this goes wrong is Exa being slow. If a call runs past eight seconds, the screen should stop waiting, show the saved run, and say why."
  - **Action:** switch to CDT, turn on "Simulate timeout" in the sidebar and press Check.
  - **Result (tested 2026-09-29):** the progress line counts up to the 8 second timebox, then the row returns at 8.0 s. The market channel reads "Saved run from 2026-09-29 09:19:10 (golden folder). Reason: live call still running past 8 s." The label is unchanged: "Single source, issuer only". "Timebox, announce, fall back, and keep the requestId for support."
  - **Cost note:** with "Saved runs only" off, the drill makes one real $0.007 call after its delay. With it on, the drill is free.
  - **If different:** if the page hangs past 8 s, the thread pool is blocking; I check that nothing waits on the executor with a with-block, and switch the sidebar to "Saved runs only" while I say so.
- **If different (first half):** if Friday's re-fetch comes back empty again, the row reads "Not confirmed, route to analyst". Say: "That is the Tuesday morning failure happening live, and this is the app refusing to guess." If the stored copy has been refreshed and alert 677 comes back in the search itself, the row reads "Single source, exchange or SEC only": say Exa has recrawled it since Tuesday, and show the Tuesday state with "Saved runs only".

**16:30 to 19:00. Scene 5: a security Ryan names.**
"Name any recent Nasdaq split, ticker change or bond redemption." Type it into the free-form box: ticker or CUSIP, issuer name, venue, event hint.
- **Hypothesis (say it before pressing Check):** "I expect the issuer's release on one of the four wires and, for a Nasdaq name, the exchange alert, both dated in the last month. If both come back and agree, it's corroborated. If only one does, the row should say which one, not pretend."
- **The Exa point, before pressing Check:** "This is the scraper question answered live. I have written no rule for this issuer's site. The same plain-language query and the same approved domain list find its release wherever it was posted."
- **Action:** press Check.
- **Result:** read the row label and the field table out loud, then point at the source type next to the link (issuer wire, exchange, and so on) to show which wire the release came from.
- **If it comes back empty (the line):** "Nothing passed the identity guard, so the app says not found rather than guessing. Next I'd check three things: the listing venue, because an NYSE name uses the 8-K channel; the window, because the free-form row starts 30 days back; and whether the release went out on a wire outside the approved list. That last one is a conversation with the customer, since the list is theirs." If Ryan has no name in mind, suggest NFE (exchange only on Sep 29, and its issuer search is a good identity-guard example) or JAGX.
- **Free-form row mechanics:** a free-form row's evidence window is computed from today's date. It has no saved run to match, so the cache-key rule does not apply. If it times out, the column shows red, "no saved run", with the reason. Say: "That's the timebox doing its job; I'd rerun it once and otherwise hand the search to the analyst."

**19:00 to 20:00. Under the hood.**
- **Hypothesis:** "If the design is sound, you should be able to see every call's cost and timing, the measured reason I'm on auto, and the code that decides identity."
- **Action:** open the call log, the auto vs deep-lite comparison, one line of evidence.py ("Search finds, code verifies identity, the analyst decides") and the early-warning JSON ("Scheduled search under ZDR; Monitors for teams that accept non-ZDR"). Snapshot and the dated replay are not built into the app; describe them in words if asked.
- **Result (measured 2026-09-29):** $0.007 per search and 1.9 to 4.1 s per call across 20 calls; deep-lite on the same CDT call at $0.012 and 5 s with nothing extra; across 22 search calls no invented ratio, date or CUSIP.
- **If different:** if the queue headers show a wait, say so and read the queue milliseconds.

**20:00 to 24:00. Slide 3.**
Walk through breaks open at 9:30 first, then the time arithmetic (section 8), the measured spend, the wedge framing, the POC (section 9) including the source-coverage check CTNT showed is needed, and production (section 11) in three sentences.
Packaging line: "The same two calls can be one tool in your ops copilot or on an MCP server. Your tool guidance says don't hardcode filters the user never asked for; here the customer did ask for them, so the model passes only the identifier and the approved list stays in code."
Then ask the discovery questions on the slide.

**24:00 to 30:00. Questions, both ways.** AJ's questions for Ryan are in section 13; the first three are the ones to ask if time is short.

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

**Manual baseline (to time before Friday; n=4 rows, one person, not the customer's analysts)**
AJ times himself resolving ONMD, CDT, BAC and CTNT by hand with Google, EDGAR, the issuers' newsrooms and Nasdaq Trader, before looking at Break Check's answer for that row. He already knows the answers from research, so this likely understates real manual time. The Break Check columns are already measured (2026-09-29, the slower of the two calls in each pair).

| Row | Manual, AJ (min) | Break Check wall time (s) | Break Check cost |
|---|---|---|---|
| ONMD | to time | about 3.6 | $0.014 |
| CDT | to time | about 4.1 | $0.014 |
| BAC | to time | about 3.0 | $0.014 |
| CTNT | to time | about 3.5, plus about 1.3 for the attempted re-fetch | $0.014 plus $0 to $0.001 |

If the baseline is not timed before Friday, drop the column and say "assumed 15 to 25 minutes" only.

**Volume sanity check, rewritten to support the count honestly:** Nasdaq's equity corporate-action alert numbering reached #688 by Sep 25, 2026, about 3.7 alerts per trading day on one exchange. For a firm whose total-market products hold most listed US names, many of those touch the book (some alerts cover warrants, units and delistings it would not hold). Add NYSE names, plus calls, tenders and redemptions across the credit issuers it holds, and name or ticker changes. Only the events where the vendors disagree or lag become breaks, so 12 to 20 breaks a day needing outside evidence is plausible for the floor-to-base range but unproven. It is the first discovery question, and the value framing still holds at a few breaks a day, because it rests on the ones still open at 9:30.

**Exa spend (per-call price measured 2026-09-29: $0.007 per search including the outputSchema; costDollars showed no separate charge for it)**
- **Per exception on auto:** two searches ($0.014), plus an occasional $0 to $0.001 re-fetch, is about $0.015.
- **Floor:** 3,024 exceptions a year is about $45. **Base:** 5,040 a year is about $76.
- **If a later eval ever favored deep-lite** ($0.012 per call measured on one call): about $0.025 per exception, $76 to $126 a year.
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
- **Week 1: public-universe eval.** Every Nasdaq corporate-action alert from the last 90 days (roughly 230 at the current rate of about 3.7 a trading day) plus a sample of bond-redemption 8-Ks, with public ground truth: the printed notice. Run auto and deep-lite on the same set; pick the type on accuracy per dollar (the demo's one measured comparison favored auto). The same run produces a coverage report: which of the customer's must-have source pages Exa holds, which are stale placeholders, and which a live fetch cannot read (on Sep 29, Nasdaq alert 683 was missing and 677 was a placeholder). Optional: a head-to-head with Parallel (Task, Extract) on the same set.
- **Week 2: customer replay, after ZDR is on.** 150 exception tickets closed in the last 90 days, where the analyst's final resolution is the ground truth.
  - Each is run as a **publication-date-bounded replay** (`endPublishedDate` = the moment the ticket opened). Its leaks are named in the readout: content and ranking are today's, and mis-dated pages can drop or slip in.
  - The strict point-in-time arm is **Snapshot on type auto** (`contents.snapshotAsOf` = ticket open time, with outputSchema, no category, no maxAgeHours), for tickets inside Snapshot's 5-month window. 150 tickets x 2 channels is 300 Snapshot requests, beyond the 100-request pay-as-you-go limit, so Snapshot capacity is part of the enterprise trial ask.
  - Tuning (queries, allowlists, rules), second run, readout.
  - Any coverage gap on a must-have source goes to Exa as a named request (a recrawl, or a custom index on an enterprise plan) with the list of URLs.
- **Week 3: shadow week and sign-off.** Analysts use the card alongside today's process.

**Success criteria. All must pass:**
1. An issuer-channel primary source passes the identity guard for 90% or more of tickets. A market-channel source (exchange alert or SEC filing) passes for 85% or more where one exists.
2. Terms, market effective date and new identifier match the final resolution for 95% or more of tickets with evidence.
3. Zero fields cited to the wrong issuer or the wrong bond series, enforced in code and audited by hand on a 30-ticket sample.
4. At most 1 high-confidence wrong field across the whole set.
5. Median wall time under 8 s per exception, 95th percentile under 15 s.
6. Under 3 cents per exception at list price.
7. **Shadow week:** fewer breaks still open at 9:30 than the prior four weeks' average, and analyst handling time on live exceptions down 50% or more, measured from ticket timestamps with and without the card.
8. **Coverage:** every must-have source the customer names is either indexed and readable, or has an agreed fix with Exa and a dated plan.
9. **Reported, not a pass condition:** how often the Snapshot arm and the replay arm agree on fields, with each disagreement explained. This measures how much the replay leaks.

**Who signs off.**
- Head of Investment Operations (the business case).
- Security master team lead (accuracy judgments on disputed rows).
- Market data or vendor management (the contract).
- CISO or InfoSec (vendor review, the gate).
- Procurement.
- On Exa's side: the account executive for the contract and the FDE for the technical win.

**Security and data-retention answers (the safe phrasing).**
- **ZDR:** "Search, which carries every routine query, is covered by ZDR in both Exa sources I read. The one-URL re-fetch uses Contents, and I'd confirm its coverage with you because two Exa pages list it differently. Monitors are not ZDR, so under ZDR the watch runs as scheduled searches." Agent is ZDR-covered in both Exa sources. Batch coverage is not stated: confirm. If Contents turns out not to be covered, the re-fetch is switched off under ZDR and a stale page goes to the analyst with its link, which is what happens on nasdaqtrader.com today anyway.
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

**What could go wrong (measured examples from 2026-09-29 where they exist)**
- **Coverage gaps on a must-have source.** Nasdaq alert 683 (CDT) is not in Exa's index, while alerts 682 and 688 from the same day are. Mitigation: the row says "single source" honestly, the analyst opens the alert, and the POC produces a coverage report and a named request to Exa.
- **Stale stored copies, and a live fetch that cannot read the page.** Exa's stored copy of alert 677 (CTNT) is a "Page Not Available" placeholder. A /contents call with maxAgeHours 0 returns status "success", source "crawled", with empty text; the same for 683. Mitigation: the stale detector, the empty-text check, and never marking a row confirmed from a stale or empty page. maxAgeHours controls freshness; it does not make an unindexed or unreadable page appear.
- **Confidence labels can mislead.** Grounding confidence read "high" on eight "not stated" fields cited to the placeholder page. Mitigation: code checks the value, never the confidence label alone.
- **Invented values: not seen, not ruled out.** Across the 22 search calls in the Sep 29 record, missing pages produced "not stated" and no ratio, date or CUSIP was invented. That is a measured observation on a small sample, not a guarantee, so the grounding, value and identity checks stay in code. The one prompt echo seen (identifier "CDT" at low confidence, cited to NFE's alert) is rejected by the grounding check.
- **Identity.** "CDT" is also a time zone abbreviation, so bare tickers are amber only. Bond releases can cover several series (BAC's does), so the CUSIP sits in the systemPrompt and code rejects other series. For NFE the issuer search's top result was a law firm's shareholder-lawsuit advertisement, which the identity guard is there to drop.
- **Mis-estimated dates.** publishedDate is an estimate: Verizon's release (text: Aug 20) was dated Sep 21, and Nasdaq OTU #2026-9 (printed Aug 4) was dated Aug 31. Mitigation: code checks `source_notice_date`, the date printed on the notice, as well as the `startPublishedDate` window. One undated page (alert 677) still came back with the window on, so code does not assume the filter drops or keeps undated pages.
- **Bonds are not truly two-source.** On Sep 29 the SEC channel found nothing relevant for BAC and returned a prospectus, not the redemption 8-K, for FITB. When a filing does match it is usually the issuer's own release filed again, so the chip would say "Same-issuer confirmation".
- **The replay leaks.** It bounds publication date, not content or ranking; Snapshot is the stricter check.
- **Other coverage not checked.**
  - NYSE-listed names have no per-issuer alert source; the 8-K channel applies.
  - Non-US issuers, municipal bonds (MSRB EMMA) and structured products were not checked.
  - Business Wire returned one result in the Sep 29 record, so its coverage is thin evidence either way.
- **Extraction mistakes.** Model extraction can be wrong or merge two notices. Mitigation: the value, identity and citation checks, the code comparison and the human review.
- **Still untested (unverified):**
  - a 5-field schema or a body with no date filter (the measured bodies use 8 fields and `startPublishedDate`);
  - the timebox under a genuinely slow call, and the Simulate timeout drill end to end;
  - Snapshot on /search with outputSchema and includeDomains, and the /contents Snapshot audit;
  - the publication-date-bounded replay;
  - whether a live fetch works on sources other than nasdaqtrader.com;
  - deep-lite beyond the one CDT comparison.
  Each has a named fallback: the golden cache, the /contents Snapshot audit, or the analyst with the link.
- **Snapshot limits:** a rolling 5-month window, 100 requests before a sales conversation, and CONTENT_NOT_CACHED possible. It stays off the live path.
- **Mocked rows.** The vendor disagreements are mocked and labeled as such everywhere.
- **Small spend.** Per-customer Exa usage is small. The commercial case rests on the ZDR Enterprise agreement and on expansion; how Exa sizes those is a question for Ryan (section 13, question 2).

## 11. How this runs in production

**Pipeline**
1. The nightly golden-copy build writes exceptions to the customer's queue.
2. A small Break Check service (Python, server-side, inside their network) picks up each exception.
3. It reads the channel config for the asset class, runs Calls 1 and 2 on /search under the ZDR team key, applies the stale detector, identity guard, value check, grounding check, empty-page check and comparison rules, and writes the evidence card, verdict and drafted note back to the ticket (ServiceNow or Jira) with the citation URLs.
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
- Honor the rate limits: /search on auto at 10 QPS, enforced by the shared limiter.
- Re-run the source coverage check weekly on the must-have sources, and send any new gap to Exa with the URLs.
- Keep a weekly re-run of the eval set as a regression test.

## 12. Build plan, rehearsal, file layout and prepared answers

**Already done (2026-09-29)**
- Exa account and key created; `EXA_API_KEY` is in `C:\Users\ajwal\Documents\exa-demo\.env` and works.
- `tools\probe.py` ran every demo row and backup on auto (about 35 calls, roughly $0.25 of the $10 credit), plus the one deep-lite comparison on CDT's exchange call and the /contents re-fetch attempts on alerts 677 and 683.
- The CTNT stale state is captured: the search that returns the placeholder and the empty live fetch are both saved.
- `cache\` has been copied to `cache_golden\` (30 saved responses). The live findings are written up in `design\live_findings_2026-09-29.md`.
- FITB was tested and dropped.

**Still to do before the clock starts (AJ, about 5 minutes)**
- Set a $5 per-key budget in the dashboard if it is not already set, and complete onboarding for the $10 bonus if not already done (neither is confirmed in the Sep 29 record).

**Timeboxed steps (about three and a half hours in total, including rehearsal)**

| Time | Step | Done when |
|---|---|---|
| 0:00 to 0:25 | `data\rows.json`: the five live rows (ONMD, CDT, BAC, CTNT, plus the free-form template for Ryan's pick) and the five backups (AGRZ, NFE, JAGX, IMMP, TRUG). Each row holds fixed dates, identifiers, bond identity key, mocked vendor values, the four beat texts, and the query, systemPrompt, `startPublishedDate` and schema copied verbatim from its saved body in `cache_golden\`. Also `data\channels.json`. Apply the eight exa_client changes from section 5 | For every row, the body built from rows.json hashes to an existing file in `cache_golden\` (a one-line check script prints OK per row) |
| 0:25 to 1:05 | `app\evidence.py`: body builders, module-level executor, polling timebox, stale detector, identity guard, value check, grounding check, attempted re-fetch with the empty-page check | ONMD returns two guarded records, CDT returns issuer-only, CTNT flags stale, all in "Saved runs only" mode |
| 1:05 to 1:30 | `app\compare.py`: normalizers, rules, note templates; `tests\` | Unit tests pass on the saved ONMD, CDT, BAC and CTNT responses |
| 1:30 to 2:20 | `app\app.py`: sidebar, queue, break detail, under the hood | The full five-scene click-path works in "Saved runs only" mode |
| 2:20 to 2:40 | Remaining keyed tests, about 10 calls and under $0.10: the ONMD replay (Call 4), the Snapshot pre-run (Call 5, 2 calls), and one genuinely slow call (the ONMD Call 2 body with type deep-reasoning, which Exa lists at 12 to 40 s and $0.015) under the 8 s timebox; pass = the screen returns in about 8 s with the saved run. Copy only these new files into `cache_golden\`. Do not re-run the CTNT re-fetch | Every demo row and every panel has a saved run |
| 2:40 to 2:55 | `slides\build_slides.py`: 3 slides from section 6, plain layout | Break_Check.pptx opens in PowerPoint |
| 2:55 to 3:30 | **Rehearsal, at least 35 minutes:** one full timed run out loud using section 7, then a second run where someone interrupts at least three times; fix overruns | The five scenes end by 19:00 with every scene's four parts spoken |
| 3:30 to 3:50 | **"Explain the code out loud", 20 minutes:** walk exa_client.py and evidence.py line by line, then say each prepared answer below without notes | Every answer below said once, cleanly |

**Separately, outside the timed steps:** the manual baseline (AJ times himself on ONMD, CDT, BAC and CTNT by hand; likely 60 to 90 minutes) and re-verifying every row fact on its primary page, including CTNT's 1-for-150 terms and CUSIP 16307X400, which come from a WebFetch of the alert, not from Exa.

**Cut list if time runs short (in this order)**
1. Snapshot panel (describe it in answers).
2. The replay (describe it in answers).
3. Run all button (keep the timeout drill in the CTNT scene).
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
  cache_golden\             frozen Sep 29 runs (30 responses), read-only
  tools\
    probe.py                the Sep 29 keyed probe; source of every measured body
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
- `build_repair_body(url)`: the Call 3 /contents body as measured: highlights true, maxAgeHours 0, livecrawlTimeout 12000.
- `build_snapshot_body(urls, as_of)`: the Call 5 audit body.
- `build_watch_body(issuer)`: the scheduled /search early-warning body.
- `build_monitor_body(issuer)`: the Monitor body, for display only.
- `EXECUTOR`: the one module-level `ThreadPoolExecutor(max_workers=4)`.
- `run_row(row, timebox_s, on_tick, simulate_timeout=False)`: submit both channels, loop `wait(timeout=0.5)` calling `on_tick`, and at the deadline, for any unfinished channel, call `exa_client.search(body, cache_only=True)` and set `envelope["error"] = f"live call still running past {timebox_s} s"`.
- `detect_stale(raw_results, channel)`: return the URL to re-fetch, or None; runs before the identity guard.
- `source_class(url, channels)`: tag a URL as issuer wire, issuer newsroom, syndication mirror, exchange or SEC filing.
- `identity_guard(results, row)`: split results into kept, amber (bare ticker or name only) and dropped.
- `check_values(output)`: mark every field whose value is "not stated" (any case) or empty as missing, whatever its confidence label says.
- `check_grounding(output, kept, allowlist, row)`: per-field status; the primary guard (cited URL in the allowlist, among kept results, and the cited page's own text contains the identifier).
- `repair(url, timebox_s=15, on_tick=None)`: submit Call 3 to `EXECUTOR`, loop `wait(timeout=0.5)` calling `on_tick` so the timer counts on screen, and at the deadline stop waiting and show the stale copy flagged with reason "live re-fetch still running past 15 s". Return the envelope plus the result of `is_empty_page`.
- `is_empty_page(result, status)`: True when status is "success" but the text and highlights are empty after stripping whitespace, or the title is only the file name (what nasdaqtrader.com returned on Sep 29).

**app\compare.py** (no model anywhere)
- `normalize_date(text)`: any printed date to YYYY-MM-DD, or None.
- `parse_time_et(text)`: the clock time in a stated effective time, or None.
- `normalize_cusip(text)`: 9 characters, uppercase, no spaces ("68270C 202" becomes "68270C202"), or None.
- `normalize_ratio(text)`: "1-for-25", "one-for-ten (1-10)" or "1:200" to a (new, old) pair.
- `next_trading_day(date)`: the next NYSE trading day, from a fixed 2026 holiday list.
- `weekend_flag(date)`: True when a stated date falls on a Saturday or Sunday, so the payment convention goes to the analyst.
- `in_window(source_notice_date, window_start)`: enforce the evidence window on the printed date.
- `is_after_close_rule(effective_as_stated, market_effective_date)`: True when the effective time is at or after 4:00 PM ET on day D and the market date is `next_trading_day(D)`. It runs on the two dates inside one source (CDT's issuer release) or across the two sources.
- `field_verdict(field, issuer_val, market_val, source_classes)`: Corroborated, Same-issuer confirmation, Explained difference, Single source or Conflict for one field; a missing value never counts, and a mirror-only value never counts as corroborated.
- `vendor_match(field, resolved, vendor_a, vendor_b)`: which vendor matches the resolved value.
- `row_verdict(row, issuer_rec, market_rec, stale, empty_refetch)`: the one status chip for the row: Corroborated, Same-issuer confirmation, Explained difference, Single source (issuer only or exchange only), Stale source, not confirmed, or Conflict, escalate. A stale or empty page never contributes to Corroborated.
- `draft_ticket_note(row, verdicts, citations)`: the resolution note with the links, and for a single-source or stale row the reason and the next step for the analyst.
- `draft_followup_note(row, verdicts)`: either a vendor escalation or a "check our field mapping" note, depending on whether the vendor value matches a valid meaning in the source.

**app\app.py** (Streamlit)
- `sidebar()`: the toggles, timebox, free-form box and the permanent mocked-data line.
- `render_queue(rows)`: Screen 1.
- `render_beat_panel(row)`: the four beat texts from rows.json.
- `render_channel_column(label, envelope, checks)`: status badge, top guarded result, fields with confidence and citation, expanders.
- `render_comparison(row, verdicts)`: the comparison table and chip.
- `render_ticket_note(note)`: the note with a Copy button.
- `render_break_detail(row)`: Screen 2, wiring `run_row` to `st.empty()` timer placeholders through `on_tick`.
- `render_under_the_hood()`: Screen 3: call log, the auto vs deep-lite comparison, measured summary, manual baseline, Run all, Snapshot panel, early-warning JSON.
- `main()`: page routing.

**data\rows.json**: per row: id, asset class, listing venue, ticker, exchange-prefixed ticker forms, CUSIP, legal name, bond identity key (issuer, coupon, maturity, CUSIP when printed), field in dispute, Vendor A and B values, opened_at, window_start, the query, systemPrompt and `startPublishedDate` per channel copied verbatim from `cache_golden\`, the four beat texts, and a demo_path flag (live scene number, or backup). Rows: ONMD, CDT, BAC, CTNT (live), AGRZ, NFE, JAGX, IMMP, TRUG (backups), and a free-form template.

**data\channels.json**: per asset class: issuer-channel allowlist, mirror list, market-channel allowlist and on-screen label; per issuer: newsroom site (newsroom.bankofamerica.com); source-class tags; the early-warning query per watched issuer.

**slides\build_slides.py**
- `slide_customer(prs)`: slide 1.
- `slide_thesis(prs)`: slide 2.
- `slide_impact(prs)`: slide 3.
- `main()`: write slides\Break_Check.pptx.

**tests\** (saved responses only, no API calls, in the spirit of recorded-response tests)
- `test_exa_client.py`: monkeypatch `CACHE_DIR` and `GOLDEN_DIR` to pytest `tmp_path` folders; fallback reads golden before working cache; live writes go only to the working folder; /contents pricing is pages times content types with a minimum of one; the timeout override is passed through; a failed cache write still returns a live envelope.
- `test_evidence.py`: "10:00 a.m. CDT" does not pass the guard, and a bare ticker is amber; the stale detector sees CTNT's saved placeholder page before the guard drops it; CTNT's eight "not stated" fields at high confidence are all marked missing; CDT's identifier "CDT" cited to alert 654 fails the grounding check; a citation outside the allowlist fails; BAC's second series is rejected; the saved empty re-fetch of alert 677 is detected as an empty page.
- `test_compare.py`: ONMD's "68270C 202" and "68270C202" match and the row is Corroborated; CDT gets "Explained difference" inside the issuer release and "Single source, issuer only" as the row chip; BAC gets "Single source, issuer only"; CTNT gets "Stale source, not confirmed"; a mirror-only field is not corroborated; a notice printed before the window is dropped.
- `test_timebox.py`: with both cache folders monkeypatched to `tmp_path`, a mocked 3-second call under a 1-second timebox returns control in about 1 second with the saved run and the reason text, and after the late thread finishes its file exists in the working folder only.

**Prepared one-sentence answers (say each out loud in the 20-minute pass)**
- **Why POST?** "The request carries a JSON body with the query, filters and schema, and Exa defines search and contents as POST endpoints; GET reads something at a URL with no body, POST sends a body for the server to act on, and PUT replaces a resource at a known address."
- **What does the x-api-key header do?** "It tells Exa which team is calling, for authorization, billing and rate limits; it's read from .env on the server and never reaches the browser, and Exa also accepts it as an Authorization Bearer header."
- **What happens to a running thread when the timebox fires?** "Nothing stops it, because Python can't kill a running thread: the screen stops waiting and shows the saved run, and the thread finishes when Exa answers or its own request timeout fires, then writes to the working cache for next time."
- **Why is the cache keyed by a hash of the request body?** "So the same request always maps to the same file and any change to the query, type or dates maps to a new one, which means a saved answer can never be shown for a different question; sorting the keys first makes key order irrelevant."
- **How long did the build take?** "About four hours of build and rehearsal, plus research and a morning of keyed testing beforehand, and about an hour timing myself on the manual baseline; I used AI tools for research and code, as your posting says is expected, and I reviewed every call myself." (The last clause is true only once the 20-minute explain-the-code pass is done.)
- **Why a thread pool at module level?** "A with-block waits for every thread on exit, which would turn my 8-second timebox into the full request timeout."
- **Why not exa-py?** The reworded line in section 4.
- **Why eight schema fields when Exa prefers five?** The line in section 4: measured, all eight filled when the page was indexed, and identity is decided by code.
- **What if the live re-fetch fails?** "It did once, on Tuesday morning: status success with an empty page. Code treats an empty success as a failure and hands the row to the analyst as not confirmed. A few hours later the same call returned the real page, so the row now reads repaired. Either way a person signs off, and the failure is the evidence I'd bring to Exa for a recrawl or a custom index."
- **Why does the app keep things in st.session_state?** "Streamlit runs the whole script again from the top every time someone clicks anything, so ordinary variables are wiped on each click. I keep the check results, the call log and the approvals in session_state, which Streamlit keeps for each browser tab across those reruns."
- **Why save the result as soon as Check is clicked?** "A button is True only on the one rerun that its click causes. So I save the result right away, and later clicks like Approve redraw from the saved result without calling Exa again."
- **What is on_tick?** "It is a small function defined inside run_check that I hand to evidence.py, which calls it back every half second while it waits. It redraws one placeholder on screen, so a timer counts up and evidence.py never needs to know about Streamlit."
- **Why strip spaces from a CUSIP before comparing?** "One source prints 68270C 202 and another prints 68270C202. A plain text comparison would call that a conflict when it is the same security."
- **How does the row get its label?** "The rules in row_label run top to bottom and the first one that fits wins, so a conflict always beats an agreement. It is plain code, so the same evidence gets the same label every time, with a reason an auditor can read."
- **Why is a field missing when Exa says confidence is high?** "High confidence on a value of not stated means the model is sure the page says nothing. A confident nothing is still nothing, so code reads the value and ignores the label."
- **Why the approved domain list and not the open web for the scan?** "I tried both today. With no domain list the same events came back, but through syndicators, and one quiet name, Procter and Gamble, came back as a redemption because of a Form 25 on a syndicator page. That is a debt delisting, not an action on the shares we hold. With the approved list every event came back from the issuer or the exchange and both quiet names stayed quiet. For a security master the list is the customer's and the false positive is the thing to avoid."
- **Why does the scan not name the event?** "Because the point is to find what we do not know. The query asks for any recent corporate action by that issuer; the system prompt says which kinds count and which to ignore, like dividends. Code matches whatever comes back to the holdings and the vendor records."
- **How would this run in production?** "One Exa Monitor per held issuer: a recurring search with the same body, deduplication, webhook delivery and structured findings. Tonight the scan is on demand because Monitors need a public webhook and are not covered by zero data retention; under ZDR it runs as a daily scheduled search."

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
12. "In the CTNT scene, Exa's stored copy of a Nasdaq alert was a placeholder, another alert from the same week wasn't indexed, and the live re-fetch failed once and worked a few hours later. When a customer has a source they can't do without, what's the usual fix: a recrawl request, a custom index, or something else, and who on Exa's side owns it?"

**About how FDE work is judged**
13. "When an enterprise demo lands, what's usually the moment that does it: results they couldn't get elsewhere, structured output, or speed?"
14. "How do you set POC success criteria with an enterprise team, and who on their side usually signs off?"
15. "After a strong demo, where do deals most often stall: security review and data retention, procurement, or proving return on investment?"
16. "What separates the FDEs who ramp fastest here from the ones who struggle?"

**About the NYC FDE team**
17. "How will NYC FDEs split time between new logos and existing accounts, and does each FDE pair with a specific account executive?"
18. "How do SF and NYC FDEs share demos and integration patterns? Is there a shared demo library, or will the new Technical Enablement role own that?"
19. "The posting says ship code in the morning and close a deal in the afternoon. How literal is that? Roughly what share of the week is building versus calls?"
20. "When an FDE finds a product gap, how does it get back to product? Can FDEs ship fixes into core repos directly, the way you did with the MCP server?"
21. "What would you want a new NYC FDE to have shipped or owned by day 90?"
