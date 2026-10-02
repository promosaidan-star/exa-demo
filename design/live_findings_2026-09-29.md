# Live findings, run with AJ's real Exa key on 2026-09-29

These replace every "expected result" in spec_v1.md and spec_v2.md. All calls went through app/exa_client.py.
Request shape used for every search: query, type auto, includeDomains (per channel), startPublishedDate,
systemPrompt, the 8-field outputSchema, contents {highlights: true}. No numResults, no category, no maxAgeHours.
Script: tools/probe.py. Responses are saved in cache/ and copied to cache_golden/.

## What worked
- type auto with the 8-field outputSchema fills every field when the page is in the index. About 2 to 4 seconds
  wall time and $0.007 per call. deep-lite on the same call cost $0.012, took 5 seconds, and found nothing extra.
  So auto is the default, on measured evidence, which also matches Exa's own build-with-exa guidance.
- When the right page is NOT in the results, the fields come back "not stated". The model did not invent values
  in any of the 22 calls. But grounding confidence can still read "high" on a "not stated" field, so confidence
  alone is not a safe signal. Code must treat "not stated" as missing regardless of confidence.
- Per-field citations (output.grounding) came back on every successful call.

## Row by row

| Row | Issuer channel (wires) | Market channel | State to show |
|---|---|---|---|
| AGRZ Agroz Inc. | Found. PR Newswire. 1-for-20, effective 12:00 am ET Sep 29 2026, CUSIP G0136M119 | Found. Nasdaq alert 2026-682. 1-for-20, effective Tue Sep 29 2026, CUSIP G0136M119 | Corroborated, two independent sources |
| ONMD OneMedNet Corp | Found. GlobeNewswire. 1-for-10, effective 12:01 am ET Sep 29 2026, CUSIP printed as "68270C 202" | Found. Nasdaq alert 2026-688. 1-for-10, effective Tue Sep 29 2026, CUSIP "68270C202" | Corroborated after code strips the space from the CUSIP |
| CDT CDT Equity Inc. | Found. GlobeNewswire Sep 25. 1-for-25, effective "September 28, 2026, at 5:00 pm, Eastern Time", first split-adjusted trading day Sep 29, CUSIP 20678X700 | NOT in Exa's index. Alert 2026-683 is missing on auto and on deep-lite. Alerts 682 and 688 from the same day are indexed | Single source, issuer only. Legal effective date vs first trading day is visible inside the issuer release |
| BAC 06051GLX5 | Found. PR Newswire Sep 4. Redemption at 100% plus accrued interest, redemption date Sep 15 2026 | Nothing relevant on sec.gov | Single source, issuer only |
| IMMP Immutep ADS | Found. GlobeNewswire Sep 21. Ratio from 1 ADS = 10 shares to 1 ADS = 200 shares | Not found | Single source, issuer only |
| NFE New Fortress Energy | No issuer release found. Top result was a law firm's shareholder-lawsuit advertisement on PR Newswire. Fields came back "not stated" | Found. Alert 2026-654. 1-for-50, effective Mon Sep 14 2026, CUSIP 644393308 | Single source, exchange only. Good example of why the identity guard exists |
| JAGX Jaguar Health | No issuer release found | Found. Alert 2026-662. 1-for-15, effective Thu Sep 17 2026, CUSIP 47010C854 | Single source, exchange only |
| TRUG TruGolf | Found. GlobeNewswire Sep 25. 1-for-10, CUSIP 243733607, trading Sep 29 | Not found | Single source, issuer only |
| CTNT Cheetah Net | No reverse-split release found on the wires | Exa's stored copy of alert 2026-677 reads "Page Not Available" | Stale page, see below |
| FITB 316773 DD9 | Not found on the wires or ir.53.com | sec.gov returned a 424B5 prospectus, not the redemption 8-K | Does not work. Drop from the live path |

## The stale-page repair does NOT work on nasdaqtrader.com
- /contents on alert 2026-677 with no freshness setting: source "cached", text "Page Not Available". 0.5 s, $0.001.
- /contents on the same URL with maxAgeHours 0 and livecrawlTimeout 12000: status "success", source "crawled",
  but the title is the bare file name and the text and highlights are EMPTY. 1.3 s, billed $0 to $0.001.
- Same result for alert 2026-683 (CDT).
- So a forced live fetch of nasdaqtrader.com returns an empty page. The Sep 29 keyless MCP probe that seemed to
  repair the page does not reproduce through the API.
- Two things code must do: (1) treat "success" with empty text as a failure, and (2) never mark a row
  corroborated from a stale or empty page.
- This is a real coverage gap to raise with Ryan as an FDE would: which alerts are indexed (682 and 688 yes,
  683 no, 677 stale), and what the fix is on Exa's side (recrawl, or a custom index for the customer's
  must-have sources on an enterprise plan).

## /contents notes
- highlights: true with no query on a page with no text returns nothing, and the call is billed $0.
- costDollars is present on /contents responses, so the app can show real cost.

## Spend so far
About 35 calls, roughly $0.25 of the $10 free credit.


## Afternoon addendum (2026-09-29, during the applet build and my own click-through)

- **CTNT re-fetch now works.** Exa's stored copy of Nasdaq alert 2026-677 is still the "Page Not Available" placeholder in /search. The forced live re-fetch (/contents, maxAgeHours 0, livecrawlTimeout 12000, highlights with a query) returned the real alert: 1-for-150, effective Monday Sep 28 2026, CUSIP 16307X400. About 1.1 s, $0.001. The morning's empty "success" was temporary. The morning response is still in cache_golden and is what the empty-page test uses.
- **CDT alert 2026-683 is still not in the index.** The row still reads "Single source, issuer only".
- **All four demo rows ran live through the finished app** with the labels expected: ONMD corroborated (3.1 s, $0.014), CDT single source issuer only, BAC single source issuer only, CTNT stale source repaired (5.0 s, $0.015).
- **Timeout drill tested in the app:** with "Simulate timeout" on, the row returned at 8.0 s with the saved run and the reason "live call still running past 8 s".
- **Free-form row tested with VerifyMe (VRME):** exchange alert 2026-686 found, issuer release not found, label "Single source, exchange or SEC only".
- **Spend so far:** about $0.25 in the morning, about $0.11 during the build, about $0.03 in my click-through. Under $0.40 of the $10 credit.

## Friday 2026-10-02 addendum (demo day rebuild)

- Watchlist scan built (app\scan.py, data\portfolio.json): one search per security, event not named, approved domain list. Live run 1:20 PM: 11.0 s, $0.07 for 10 names. AGRZ and NFE absent from both mocked vendor records; CTNT, TRUG, BAC at one vendor only; ONMD, CDT, JAGX at both; MSFT and PG nothing found.
- Open web (no domain list) probe: same events via syndicators, plus a false positive on PG (Form 25 debt delisting read as a redemption). Approved list chosen.
- Nasdaq alert 2026-683 (CDT) is now indexed. CDT live reads corroborated with the explained date difference. A terms-parsing bug ("one-for-twenty five (1-25)" read as 1-for-20) was found and fixed in compare.py; digits in brackets win.
- Typed live challenge: "Nuwellis" returned a reverse split mentioned inside an Aug 13 earnings release, terms not stated, flagged as weak evidence.
- Spend today about $0.30. 61 tests pass.
