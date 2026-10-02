"""
scan.py - the watchlist scan: "Find what our feeds missed".

WHAT THIS FILE DOES, IN ONE SENTENCE
  For every security on a (mocked) watchlist, it asks Exa one open
  question, "has this issuer announced a corporate action lately?",
  without naming the event, and then plain code matches what Exa found
  to the portfolio, compares it with the two (mocked) vendor records,
  and works out what the analyst has to do next.

WHY IT EXISTS
  The break queue starts from a break the vendors already disagree on.
  The scan starts earlier: it can DISCOVER an event that neither vendor
  record has. That is the moment the demo is built around.

HOW ONE SCAN FLOWS THROUGH THIS FILE
  run_scan(securities)
    1. build_scan_body for each security (no event named in the query)
    2. send them all at once through the shared thread pool and the
       shared limiter in exa_client, and stop waiting at the timebox
    3. for each answer, check_security:
         a. identity guard (reused from evidence.py) on every page
         b. check_fields: every field gets verified, missing or unverified
         c. match_event_to_portfolio: which holding is this event about?
         d. compare_vendors: is it in Vendor A, Vendor B, both, neither?
         e. originating_statements: how many independent sources?
         f. downstream_impact: what the analyst sees next (local only)
    <- one "finding" dictionary per security

WHAT NEVER LEAVES THIS LAPTOP
  Holdings, open orders and vendor records are read only by code in this
  file. The only things sent to Exa are the issuer's name, its ticker or
  CUSIP, and the fixed rules in data\\portfolio.json.

WORDS USED HERE
  finding     the result for one security: the event (or none), the
              finding status, the evidence and the impact
  originating statement
              one announcement by one party. An issuer's release copied
              by three wires is still ONE originating statement.
"""

# ---------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------

# json reads data\portfolio.json into a dictionary.
import json

# re is Python's pattern-matching module ("regular expressions").
import re

# time gives us a stopwatch for the whole scan.
import time

# date is Python's calendar-date type; two dates can be subtracted.
from datetime import date

# Path builds file paths that work on any operating system.
from pathlib import Path

# Our own files. compare has the normalizers (dates, ratios, CUSIPs).
# evidence has the identity guard, the thread pool and the timebox code.
# exa_client makes (or replays) every Exa call.
import compare
import evidence
import exa_client

# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------

# The data folder: one level up from this file's folder, then "data".
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# How long the screen waits for the whole scan, in seconds. Ten searches
# share 4 slots in the limiter, and one search took 3 to 9 seconds when
# probed on 2026-10-02, so the whole scan needs about 15 to 25 seconds.
SCAN_TIMEBOX_S = 30

# The "Simulate timeout" drill holds one security back this long, which
# is longer than the timebox, so the real timebox path runs.
SCAN_SIMULATED_DELAY_S = 40

# The security the drill holds back. A bond, so the equities still show.
SIMULATED_SECURITY = "BAC 06051GLX5"

# The seven fields the scan asks Exa to fill (see portfolio.json).
SCAN_FIELDS = [
    "event_type",
    "terms",
    "effective_as_stated",
    "effective_date",
    "new_identifier",
    "identifier_in_source",
    "source_notice_date",
]

# The fields that must be verified before the evidence counts as
# complete. A bond redemption keeps its CUSIP, so new_identifier is not
# required for it (see required_fields below).
CORE_FIELDS = ["event_type", "terms", "effective_date"]

# The four finding statuses, exactly as the screen shows them.
ABSENT_BOTH = "Absent from both vendor records"
ONE_VENDOR = "Present at one vendor only"
BOTH_VENDORS = "Both vendors have it"
NOTHING_FOUND = "Nothing found (not proof nothing happened)"
# A typed name on the Free-form tab has no vendor records to compare.
NO_VENDOR_RECORDS = "Found (typed name, no vendor records to compare)"

# The order the screen sorts findings in: the payoff first.
STATUS_ORDER = [ABSENT_BOTH, ONE_VENDOR, BOTH_VENDORS, NO_VENDOR_RECORDS, NOTHING_FOUND]

# The independence rule, shown on screen next to every finding.
INDEPENDENCE_RULE = (
    "An issuer release and a syndicated copy of it count as ONE originating "
    "statement, not two. Two independent sources means the issuer plus the "
    "exchange or the SEC."
)


# ---------------------------------------------------------------------
# LOADING THE PORTFOLIO
# ---------------------------------------------------------------------

def load_portfolio():
    """Return data\\portfolio.json as a dictionary."""
    # read_text loads the file; json.loads turns the text into a dictionary.
    return json.loads((DATA_DIR / "portfolio.json").read_text(encoding="utf-8"))


def find_security(portfolio, security_id):
    """Return the security whose id matches, or None."""
    # next(..., None) returns the first item the generator produces, or
    # None when it produces nothing. A compact form of a search loop.
    return next((s for s in portfolio["securities"] if s["id"] == security_id), None)


# ---------------------------------------------------------------------
# BUILDING THE REQUEST BODY
# ---------------------------------------------------------------------

def allowlist(portfolio):
    """The approved domains, or [] when the scan runs on the open web."""
    # domain_mode was chosen by the probe on 2026-10-02: "approved".
    if portfolio["domain_mode"] == "approved":
        return portfolio["approved_domains"]
    return []


def build_scan_body(security, portfolio):
    """
    Return the /search body for one security.

    The query asks for corporate actions in general and never names the
    event. That is what lets the scan find an event nobody told it about.
    Every piece is fixed text, so the same security always produces the
    same body and its saved run keeps matching.
    """
    subject = security["subject"]
    # Start with the two fields Exa recommends on every search.
    body = {
        # Retrieval intent only: what the pages we want are about.
        "query": portfolio["query_template"].format(subject=subject),
        # Exa's default type. auto filled every field on 2026-09-29.
        "type": "auto",
    }
    # The customer's approved list, a hard filter, when the mode says so.
    # On the open web we leave the field out entirely.
    domains = allowlist(portfolio)
    if domains:
        body["includeDomains"] = domains
    # The rest is added in a fixed order so the screen shows it neatly.
    # The window is a stated, bounded window (about 60 days), which is
    # the case where Exa's guidance says a date filter belongs.
    body["startPublishedDate"] = portfolio["scan_start_published"]
    # The keep and drop rules live in systemPrompt, not in the query.
    body["systemPrompt"] = portfolio["system_prompt_template"].format(subject=subject)
    # The fields we want back, with Exa's per-field citations.
    body["outputSchema"] = portfolio["output_schema"]
    # The most relevant passages per page. Code reads them for identity,
    # and the screen shows them as the supporting passage.
    body["contents"] = {"highlights": True}
    return body


def as_row(security):
    """
    Return the security in the shape evidence.py's identity guard reads.

    The guard looks at four keys: ticker, cusip, legal_names and bond.
    Reusing it means the scan uses exactly the same identity rules as
    the break queue, including "CDT alone could be Central Daylight Time".
    """
    return {
        "ticker": security["ticker"],
        "cusip": security["cusip"],
        "legal_names": security["legal_names"],
        "bond": security["bond"],
    }


# ---------------------------------------------------------------------
# RUNNING THE SCAN UNDER THE TIMEBOX
# ---------------------------------------------------------------------

def run_scan(securities, portfolio, cache_only=False, simulate_timeout=False,
             timebox_s=SCAN_TIMEBOX_S, on_tick=None):
    """
    Send one search per security, all at once, and wait at most timebox_s.

    on_tick   called every half second with (seconds waited, {id: done?})
              so the screen can show a per-security progress line.
    Returns a list of findings, one per security, in watchlist order.
    """
    started = time.perf_counter()
    # Build every body first, so the screen can show them either way.
    # A dictionary comprehension: {key: value for item in list}.
    bodies = {s["id"]: build_scan_body(s, portfolio) for s in securities}
    # Hand each search to the app's one shared thread pool. submit()
    # returns at once with a "future", a handle to the running job.
    # Every search still passes through exa_client's shared limiter, so
    # no more than 4 calls are ever in flight.
    futures = {}
    for security in securities:
        # The drill delays one security only, so the rest still show live.
        held = simulate_timeout and security["id"] == SIMULATED_SECURITY
        delay = SCAN_SIMULATED_DELAY_S if held else 0
        futures[security["id"]] = evidence.EXECUTOR.submit(
            evidence._search_job, bodies[security["id"]], cache_only, delay
        )
    # Wait, waking every half second to update the progress line, until
    # every search is back or the timebox runs out. Reused from evidence.py.
    evidence._wait_with_ticks(futures, timebox_s, on_tick)

    findings = []
    for security in securities:
        sid = security["id"]

        # The saved run for this body, used if the live call is late.
        # "body=bodies[sid]" fixes the value now, inside the loop.
        def fallback(body=bodies[sid]):
            return exa_client.search(body, cache_only=True)

        envelope = evidence._collect(futures[sid], fallback, timebox_s, "live call")
        findings.append(check_security(security, envelope, portfolio))
    # Attach the total wall time to every finding, for the summary line.
    total_ms = int((time.perf_counter() - started) * 1000)
    for finding in findings:
        finding["scan_wall_ms"] = total_ms
    return findings


# ---------------------------------------------------------------------
# CHECKING ONE SECURITY'S ANSWER
# ---------------------------------------------------------------------

def check_fields(data, guard, domains):
    """
    Give every scan field a status, checked in code (same rules as the
    break queue):
      verified    has a value, and a cited page passed the identity guard
                  (and is on the approved list, when there is one)
      missing     "not stated", "none found" or empty. Exa's confidence is
                  ignored on purpose.
      unverified  has a value, but no cited page passes the checks
    """
    fields = evidence.read_fields(data)
    output = data.get("output") or {}
    # Index Exa's grounding list by field name for quick lookup.
    grounding = {entry.get("field"): entry for entry in output.get("grounding") or []}
    # The URLs of the pages that passed the identity guard, as a set.
    kept_urls = {item["url"] for item in guard["kept"]}
    checks = {}
    for field in SCAN_FIELDS:
        value = fields.get(field)
        entry = grounding.get(field) or {}
        # Every cited URL for this field, skipping blanks.
        citations = [c.get("url") for c in entry.get("citations") or [] if c.get("url")]
        # A citation is good if its page passed the guard, and, when an
        # approved list exists, sits on that list.
        good = [u for u in citations if u in kept_urls and (not domains or evidence.in_allowlist(u, domains))]
        # "none found" is the systemPrompt's word for "no event".
        if evidence.is_missing(value) or str(value).strip().lower() == "none found":
            status, reason = "missing", "the source does not give it"
        elif good:
            status, reason = "verified", "cited page names this security"
        elif not citations:
            status, reason = "unverified", "no citation for this field"
        else:
            status, reason = "unverified", "cited page failed the identity check"
        checks[field] = {
            "value": "" if value is None else str(value),
            "status": status,
            "confidence": entry.get("confidence", ""),
            "citations": citations,
            "cited_url": good[0] if good else "",
            # Every citation that passed, used to count independent sources.
            "good_citations": good,
            "reason": reason,
        }
    return checks


def required_fields(event_type):
    """The fields that must be verified for this kind of event."""
    # A split or identifier change must also give the new identifier.
    # A redemption does not change the bond's CUSIP.
    if "redemption" in event_type or "tender" in event_type:
        return CORE_FIELDS
    return CORE_FIELDS + ["new_identifier"]


def match_event_to_portfolio(identifier, page_text, securities):
    """
    Decide, in code, which holding an event is about. Returns its id or None.

    identifier  identifier_in_source as Exa read it, such as "ONMD" or
                "06051GLX5" (may be "not stated")
    page_text   the title and highlights of the cited pages
    securities  the watchlist

    Rule 1: the printed identifier equals a holding's ticker or CUSIP,
            once spaces and dashes are removed. Exactly one must match.
    Rule 2: otherwise the identity guard (evidence.match_identity) must
            give a "strong" match on the page text for exactly one holding.
    Anything else is None: the event is not matched to a holding.
    """
    # squash removes spaces and dashes and uses capitals.
    printed = evidence.squash(identifier or "")
    if printed and not evidence.is_missing(identifier):
        hits = [s["id"] for s in securities
                if printed in {evidence.squash(s["ticker"]), evidence.squash(s["cusip"])} - {""}]
        # len(hits) == 1 means one and only one holding matched.
        if len(hits) == 1:
            return hits[0]
    # Rule 2: run the identity guard's matcher for each holding.
    strong = [s["id"] for s in securities
              if evidence.match_identity(page_text, as_row(s))[0] == "strong"]
    if len(strong) == 1:
        return strong[0]
    return None


def event_family(event_type):
    """Group event names so "Reverse Stock Split" and "reverse split" match."""
    text = (event_type or "").lower()
    # Order matters: "reverse" must be checked before plain "split".
    if "reverse" in text:
        return "reverse split"
    if "split" in text:
        return "forward split"
    if "redemption" in text or "redeem" in text:
        return "redemption"
    if "cusip" in text:
        return "identifier change"
    if "ticker" in text or "symbol" in text:
        return "ticker change"
    if "ads" in text:
        return "ADS ratio change"
    # Anything else keeps its own lower-case name.
    return text.strip()


def _vendor_differences(name, record, event):
    """List the fields where one vendor's record disagrees with the source."""
    notes = []
    # The terms, put into one form ("1-for-10") on both sides.
    source_terms = compare.normalize_terms(event["terms"])
    vendor_terms = compare.normalize_terms(record.get("terms"))
    if source_terms and vendor_terms != source_terms:
        notes.append(f"{name} terms {record.get('terms') or '(blank)'}; source says {source_terms}")
    # The new identifier, with spaces removed on both sides.
    source_id = evidence.squash(event["new_identifier"]) if not evidence.is_missing(event["new_identifier"]) else ""
    vendor_id = evidence.squash(record.get("new_identifier") or "")
    if source_id and vendor_id != source_id:
        notes.append(f"{name} new identifier {record.get('new_identifier') or '(blank)'}; source says {source_id}")
    # The date. A vendor that loaded the legal effective date instead of
    # the first trading day gets its own wording, because that is a
    # mapping question, not a wrong date.
    source_date = compare.normalize_date(event["effective_date"])
    legal_date = compare.normalize_date(event["effective_as_stated"])
    vendor_date = compare.normalize_date(record.get("effective_date"))
    if source_date and vendor_date != source_date:
        if vendor_date and vendor_date == legal_date:
            notes.append(f"{name} date {vendor_date} is the legal effective date as stated; the first trading day is {source_date}")
        else:
            notes.append(f"{name} date {record.get('effective_date') or '(blank)'}; source says {source_date}")
    return notes


def compare_vendors(event, vendor_a, vendor_b, typed=False):
    """
    Compare what the source says with the two mocked vendor records.

    event     the event found, as {"event_type", "terms", ...}, or None
    vendor_a  Vendor A's record for this security, or None if it has none
    vendor_b  the same for Vendor B
    typed     True for a name typed on the Free-form tab (no records)
    Returns {"status", "has_a", "has_b", "differences", "note"}.
    """
    result = {"status": "", "has_a": False, "has_b": False, "differences": [], "note": ""}
    if event is None:
        result["status"] = NOTHING_FOUND
        # Say so if a vendor shows an event the scan could not confirm.
        shown = [name for name, rec in (("Vendor A", vendor_a), ("Vendor B", vendor_b)) if rec]
        if shown:
            result["note"] = " and ".join(shown) + " show an event that this scan did not find in public sources. Ask the vendor for its source."
        return result
    if typed:
        result["status"] = NO_VENDOR_RECORDS
        return result
    family = event_family(event["event_type"])
    # A vendor "has it" when its record is the same kind of event.
    # bool(...) turns "a record exists and matches" into True or False.
    result["has_a"] = bool(vendor_a) and event_family(vendor_a.get("event_type")) == family
    result["has_b"] = bool(vendor_b) and event_family(vendor_b.get("event_type")) == family
    if result["has_a"] and result["has_b"]:
        result["status"] = BOTH_VENDORS
    elif result["has_a"] or result["has_b"]:
        result["status"] = ONE_VENDOR
        missing = "Vendor B" if result["has_a"] else "Vendor A"
        result["note"] = f"{missing} has no record of this event."
    else:
        result["status"] = ABSENT_BOTH
        result["note"] = "Neither vendor record shows this event. Exa found it in a public announcement."
    # For each vendor that has it, list where its fields disagree.
    if result["has_a"]:
        result["differences"] += _vendor_differences("Vendor A", vendor_a, event)
    if result["has_b"]:
        result["differences"] += _vendor_differences("Vendor B", vendor_b, event)
    return result


def source_kind(url):
    """Sort a page into the issuer's side, or the exchange or SEC side."""
    host = evidence.host_of(url)
    if host == "nasdaqtrader.com" or host.endswith(".nasdaqtrader.com"):
        return "exchange"
    if host == "sec.gov" or host.endswith(".sec.gov"):
        return "SEC"
    # Wires, issuer newsrooms and anything that republishes them.
    return "issuer"


def originating_statements(checks):
    """
    Count the independent sources behind the verified fields.

    All issuer-side pages (the release on several wires, the newsroom
    copy) are ONE originating statement. The exchange or SEC notice is a
    second, independent one.
    """
    # Every citation that passed the checks on a field that has a value,
    # once each, in a stable order. A set comprehension {x for ...}
    # removes duplicates; sorted() turns it into an ordered list.
    urls = sorted({u for c in checks.values() if c["status"] == "verified"
                   for u in c.get("good_citations") or []})
    # Group the URLs by side. setdefault adds an empty list on first use.
    groups = {}
    for url in urls:
        groups.setdefault(source_kind(url), []).append(url)
    issuer = groups.get("issuer", [])
    official = groups.get("exchange", []) + groups.get("SEC", [])
    if issuer and official:
        label = "Two independent sources: the issuer plus the exchange or SEC"
    elif issuer:
        # len(issuer) copies of one statement still count as one.
        label = f"One originating statement: the issuer ({len(issuer)} cited cop{'y' if len(issuer) == 1 else 'ies'})"
    elif official:
        label = "One originating statement: the exchange or SEC"
    else:
        label = "No verified source"
    return {"label": label, "issuer": issuer, "official": official,
            "independent": bool(issuer and official)}


def check_security(security, envelope, portfolio, typed=False):
    """Turn one security's envelope into a finding."""
    data = envelope.get("data") or {}
    results = data.get("results") or []
    domains = allowlist(portfolio)
    row = as_row(security)
    # a. The identity guard, reused from evidence.py.
    guard = evidence.identity_guard(results, row)
    # b. Every field gets a status.
    checks = check_fields(data, guard, domains)
    event_type = checks["event_type"]["value"]
    # Was an event found at all? The event type must have a value.
    found = checks["event_type"]["status"] != "missing"
    # c. Which holding is it about? Only the cited, kept pages count.
    cited = {c["cited_url"] for c in checks.values() if c["cited_url"]}
    cited_text = "\n".join(evidence.page_text(r) for r in results if r.get("url") in cited)
    candidates = portfolio["securities"] if not typed else [security]
    matched = match_event_to_portfolio(checks["identifier_in_source"]["value"], cited_text, candidates) if found else None
    # The event only counts for this security if it matched THIS security.
    event = None
    off_target = ""
    if found and matched == security["id"]:
        # A dictionary comprehension: the plain value of every field.
        event = {f: checks[f]["value"] for f in SCAN_FIELDS}
    elif found:
        off_target = "Exa returned an event, but code could not tie it to this holding, so it is not counted."
    # The evidence is complete when every required field is verified.
    unresolved = []
    if event:
        for field in required_fields(event_family(event_type)):
            if checks[field]["status"] != "verified":
                unresolved.append(field)
        # The notice must be inside the scan window, read from the page.
        notice = compare.normalize_date(event["source_notice_date"])
        if notice and notice < portfolio["scan_start_published"][:10]:
            unresolved.append("source_notice_date (before the scan window)")
    # d. Compare with the two mocked vendor records.
    vendors = compare_vendors(event, security.get("vendor_a"), security.get("vendor_b"), typed=typed)
    # e. How many independent sources stand behind it.
    sources = originating_statements(checks) if event else originating_statements({})
    finding = {
        "security": security,
        "envelope": envelope,
        "body": envelope.get("body") or build_scan_body(security, portfolio),
        "guard": guard,
        "checks": checks,
        "event": event,
        "event_family": event_family(event_type) if event else "",
        "matched_to": matched or "",
        "off_target": off_target,
        "unresolved": unresolved,
        "vendors": vendors,
        "status": vendors["status"],
        "sources": sources,
        "wall_ms": envelope.get("elapsed_ms", 0),
        "cost_live": envelope["cost_dollars"] if envelope.get("source") == "live" and envelope.get("cost_dollars") else 0.0,
    }
    # f. What the analyst sees next. Local only: holdings never go to Exa.
    finding["impact"] = downstream_impact(finding)
    return finding


# ---------------------------------------------------------------------
# DOWNSTREAM IMPACT: what the analyst sees next (all local, all mocked)
# ---------------------------------------------------------------------

def split_ratio(terms):
    """Return (old, new) from split terms such as "1-for-10", or None."""
    # normalize_terms turns "one-for-ten (1-10)" into "1-for-10".
    norm = compare.normalize_terms(terms) or ""
    found = re.fullmatch(r"(\d+)-for-(\d+)", norm)
    # int() turns the captured text into numbers.
    return (int(found.group(1)), int(found.group(2))) if found else None


def downstream_impact(finding):
    """
    Build the mocked "what happens next" panel for one finding.

    Returns {"kind", "headline", "lines", "action", "warning"}. Only plain
    local code runs here: holdings and orders never go to Exa.
    """
    security = finding["security"]
    event = finding["event"]
    holding = security.get("holding") or {}
    impact = {"kind": "", "headline": "", "lines": [], "action": "", "warning": ""}

    # Nothing found: say what that does and does not mean.
    if event is None:
        impact["kind"] = "nothing"
        impact["headline"] = "Nothing found. Not proof nothing happened."
        impact["lines"].append("No public announcement in the approved sources inside the scan window.")
        if finding["vendors"]["note"]:
            impact["lines"].append(finding["vendors"]["note"])
        impact["action"] = "No change proposed. The vendor feeds remain the record."
        return impact

    family = finding["event_family"]
    # A reverse or forward split: shares before and after, orders, identifier.
    ratio = split_ratio(event["terms"])
    if family in ("reverse split", "forward split") and ratio and "shares" in holding:
        old, new = ratio
        shares = holding["shares"]
        # A 1-for-10 reverse split turns 10 shares into 1: multiply by
        # old and divide by new. // is whole-number division (it drops
        # the fraction); % gives what is left over.
        after = shares * old // new
        leftover = shares * old % new
        impact["kind"] = "split"
        impact["headline"] = f"{old}-for-{new} {family}: the share count changes, the value does not"
        # :, puts thousands separators in a number, as in 10,000.
        impact["lines"].append(f"Held: {shares:,} shares before. {after:,} shares after, before fractional-share handling.")
        if leftover:
            impact["lines"].append(f"A fraction of {leftover}/{new} of a share is left over; it is handled under the issuer's fractional-share terms.")
        impact["lines"].append("The price adjusts by the same ratio, so the position's value is unchanged by the split itself.")
        # Each open order is flagged, never changed.
        for order in security.get("open_orders") or []:
            impact["lines"].append(
                f"Open order {order['order_id']} ({order['side']} {order['quantity']:,} at {order['limit_price']}) "
                "flagged for review: quantity and limit price are on pre-split terms."
            )
        if not security.get("open_orders"):
            impact["lines"].append("No open orders on this security.")
        new_id = event["new_identifier"]
        if not evidence.is_missing(new_id):
            impact["lines"].append(f"Identifier update proposed: new CUSIP {evidence.squash(new_id)}, effective {event['effective_date']}.")
        impact["action"] = "Propose the split and identifier update for analyst approval. Nothing is booked automatically."
    # A bond redemption: par, the expected cash event, verify, never mark.
    elif family == "redemption" and "par" in holding:
        par = holding["par"]
        impact["kind"] = "redemption"
        impact["headline"] = "Announced redemption: an expected cash event to verify"
        impact["lines"].append(f"Held: {par:,} par.")
        impact["lines"].append(f"Expected cash event date: {event['effective_date']}. Terms as stated: {event['terms']}.")
        price = compare.normalize_terms(event["terms"]) or ""
        found = re.match(r"(\d+(?:\.\d+)?)% of principal", price)
        if found:
            # float() turns "100" into 100.0; / 100 turns a percent into a share.
            amount = par * float(found.group(1)) / 100
            impact["lines"].append(f"Amount to verify: {amount:,.0f} principal plus accrued interest, on the date above.")
        impact["action"] = "Propose status update for analyst verification."
        impact["warning"] = (
            "Do not mark the notes redeemed. An announcement of a future redemption does not prove it completed. "
            "Confirm the payment with the custodian or the paying agent on or after the date."
        )
    else:
        impact["kind"] = "other"
        impact["headline"] = f"{event['event_type']}: review the terms"
        impact["action"] = "Propose the change for analyst approval."

    # Legal date versus trading date: which date does the master map?
    legal = compare.normalize_date(event["effective_as_stated"])
    trading = compare.normalize_date(event["effective_date"])
    # date.fromisoformat turns "2026-09-28" into a date, so two dates can
    # be subtracted; .days is the gap in whole days.
    gap = (date.fromisoformat(trading) - date.fromisoformat(legal)).days if legal and trading else 0
    # A legal effective time one to three days before the first trading
    # day is the classic "evening before" pattern (CDT: 5:00 pm Sep 28,
    # trading Sep 29). A bigger gap is more likely a different date in
    # the notice (a meeting, a filing), so it is an open question instead.
    if family != "redemption" and 1 <= gap <= 3:
        impact["lines"].append(
            f"Date mapping needs review: the legal effective date as stated is {legal} "
            f"({event['effective_as_stated']}), the first split-adjusted trading day is {trading}. "
            "Decide which one the security master's effective-date field holds."
        )
        impact["date_mapping"] = {"legal": legal, "trading": trading}

    elif family != "redemption" and gap:
        finding["unresolved"].append(
            f"effective_as_stated ({event['effective_as_stated']}) is {abs(gap)} days from effective_date"
        )
    # Evidence incomplete: name the open question and the next action.
    if finding["unresolved"]:
        names = ", ".join(finding["unresolved"])
        impact["incomplete"] = (
            f"Evidence incomplete. Unresolved: {names}. "
            "Next action: open the cited page and confirm these fields, or look for the exchange notice, before approving."
        )
    return impact


# ---------------------------------------------------------------------
# A NAME TYPED ON THE FREE-FORM TAB
# ---------------------------------------------------------------------

def typed_security(text, portfolio):
    """
    Turn what someone typed into a security to scan.

    A watchlist id or ticker returns that holding. A CUSIP, a ticker or a
    company name builds a new security with no holdings and no vendor
    records. No event is ever asked for.
    """
    cleaned = text.strip()
    # A watchlist match first: by id or by ticker, ignoring case.
    for security in portfolio["securities"]:
        if cleaned.upper() in {security["id"].upper(), security["ticker"].upper()} - {""}:
            return security, False
    base = {"id": cleaned, "kind": "equity", "exchange": "", "bond": None,
            "holding": {}, "open_orders": [], "vendor_a": None, "vendor_b": None}
    # A CUSIP: 9 letters and digits.
    if evidence.looks_like_cusip(cleaned):
        cusip = evidence.squash(cleaned)
        base.update({"ticker": "", "cusip": cusip, "issuer": cusip, "legal_names": [],
                     "subject": f"the security with CUSIP {cusip}"})
    # A ticker: one to five letters with no spaces.
    elif re.fullmatch(r"[A-Za-z]{1,5}", cleaned):
        ticker = cleaned.upper()
        base.update({"id": ticker, "ticker": ticker, "cusip": "", "issuer": ticker, "legal_names": [],
                     "subject": f"the company listed under ticker {ticker}"})
    # Anything else is a company name.
    else:
        names = list(dict.fromkeys([cleaned, evidence.short_name(cleaned)]))
        base.update({"ticker": "", "cusip": "", "issuer": cleaned, "legal_names": names,
                     "subject": cleaned})
    return base, True


def scan_one(security, portfolio, cache_only=False, typed=False):
    """Scan a single security (the Free-form tab), under the same timebox."""
    body = build_scan_body(security, portfolio)
    future = evidence.EXECUTOR.submit(evidence._search_job, body, cache_only, 0)
    evidence._wait_with_ticks({"one": future}, SCAN_TIMEBOX_S, None)

    def fallback():
        return exa_client.search(body, cache_only=True)

    envelope = evidence._collect(future, fallback, SCAN_TIMEBOX_S, "live call")
    return check_security(security, envelope, portfolio, typed=typed)


# ---------------------------------------------------------------------
# SHOWING THE EVIDENCE: the passage behind one field
# ---------------------------------------------------------------------

# Month names, for turning "2026-09-29" into "September 29, 2026".
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def value_variants(value):
    """The ways a value may be printed on a page, most exact first."""
    value = (value or "").strip()
    variants = [value]
    # A CUSIP may be printed with a space, as in "68270C 202".
    squashed = evidence.squash(value)
    if len(squashed) == 9:
        variants += [squashed, squashed[:6] + " " + squashed[6:]]
    # A date may be printed in words.
    found = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    if found:
        year, month, day = int(found.group(1)), int(found.group(2)), int(found.group(3))
        name = MONTH_NAMES[month - 1]
        variants += [f"{name} {day}, {year}", f"{name[:3]}. {day}, {year}", f"{name} {day}"]
    # A ratio may be printed in its normalized form, as in "1-for-20".
    terms = compare.normalize_terms(value)
    if terms and terms != value:
        variants.append(terms)
    # Drop empties and duplicates, keep the order.
    return [v for v in dict.fromkeys(variants) if v and not evidence.is_missing(v)]


def supporting_passage(finding, field):
    """
    Find the passage that supports one field.

    Returns {"url", "title", "passage", "match"}: the cited page, the
    highlight that contains the value (or the first highlight), and the
    exact text of the value as printed, so the screen can mark it.
    """
    check = finding["checks"][field]
    # Prefer the verified citation, then any citation for this field.
    urls = [check["cited_url"]] if check["cited_url"] else check["citations"]
    results = (finding["envelope"].get("data") or {}).get("results") or []
    variants = value_variants(check["value"])
    for url in urls:
        for result in results:
            if result.get("url") != url:
                continue
            for highlight in result.get("highlights") or []:
                lowered = highlight.lower()
                for variant in variants:
                    at = lowered.find(variant.lower())
                    # find() returns -1 when the text is not there.
                    if at >= 0:
                        # Keep about 300 characters either side of the value.
                        start = max(0, at - 300)
                        end = min(len(highlight), at + len(variant) + 300)
                        return {"url": url, "title": result.get("title") or "",
                                "passage": highlight[start:end],
                                "match": highlight[at:at + len(variant)]}
            # The page is cited but the value is not printed word for word.
            first = (result.get("highlights") or [""])[0]
            return {"url": url, "title": result.get("title") or "", "passage": first[:700], "match": ""}
    return {"url": urls[0] if urls else "", "title": "", "passage": "", "match": ""}


def proposed_action_line(finding):
    """One sentence: what code proposes, for the third stage on screen."""
    event = finding["event"]
    if event is None:
        return "No change proposed."
    impact = finding["impact"]
    # The normalized terms read better than the raw text ("1-for-20").
    terms = compare.normalize_terms(event["terms"]) or event["terms"]
    parts = [f"{event_family(event['event_type'])}, {terms}, effective {event['effective_date']}"]
    if not evidence.is_missing(event["new_identifier"]):
        parts.append(f"new identifier {evidence.squash(event['new_identifier'])}")
    return f"{impact['action']} ({'; '.join(parts)}.)"
