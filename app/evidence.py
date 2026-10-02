"""
evidence.py - gathers the evidence for one break, and checks it in code.

WHAT THIS FILE DOES, IN ONE SENTENCE
  For one row of the break queue, it runs one Exa search per source type
  at the same time, stops waiting at a fixed deadline, and then checks in
  plain code that every page and every field really is about this
  security before anything is shown as evidence.

WHY IT EXISTS
  1. The request bodies are built here, from data\\rows.json and
     data\\channels.json, so the domain lists come from the customer's
     approved config and never from a model or a user.
  2. The screen must never hang. A "timebox" (a fixed deadline, 8 seconds
     by default) decides how long we wait. Anything still running after
     it is replaced by the saved run, and the late call finishes quietly
     in the background.
  3. A model can be wrong, or can echo back the company name we put in
     the prompt. So code, not the model, checks identity: it reads the
     page titles and highlights Exa returned and looks for the ticker
     with its exchange, the CUSIP, or the legal name.

THE TWO CHANNELS
  issuer   press-release wires, plus the issuer's own newsroom if any
  market   the exchange's alert (nasdaqtrader.com) or the SEC (sec.gov)

HOW ONE ROW FLOWS THROUGH THIS FILE
  check_row(row)
    1. run_row: build both bodies, send both at once, poll every 0.5 s
       until both are back or the timebox runs out
    2. for each channel, check_channel:
         a. detect_stale     is the exchange page a "Page Not Available"
                             placeholder? (runs BEFORE the identity guard,
                             because a placeholder names no company and
                             the guard would throw it away unseen)
         b. identity_guard   keep, amber or drop each result page
         c. check_grounding  each field: verified, missing or unverified
    3. if a stale page was found: repair, one live re-fetch of that URL
    <- one dictionary with everything compare.py and the screen need

WORDS USED HERE
  envelope   the package exa_client returns for every call
  grounding  Exa's list of which page supports which field, with a
             confidence of low, medium or high
  kept       a result page that passed the identity guard
  amber      a result page that only weakly matches, such as a bare
             ticker; shown, never used as evidence
"""

# ---------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------

# json reads our two config files, and the model's answer, which Exa
# sometimes sends as JSON text inside the response.
import json

# re is Python's "regular expressions" module: a small language for
# describing patterns in text, such as "Nasdaq, a colon, then CDT".
import re

# time gives us a stopwatch and a way to pause (for the timeout drill).
import time

# A ThreadPoolExecutor runs functions on background threads, so two
# searches can wait on the network at the same time. wait() lets the
# main thread check on them with a short timeout.
from concurrent.futures import ThreadPoolExecutor, wait

# Path builds file paths that work on any operating system.
from pathlib import Path

# urlparse splits a web address into parts, so we can read its host
# name (for example www.globenewswire.com).
from urllib.parse import urlparse

# Our own file that talks to Exa. Every call goes through it.
import exa_client

# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------

# The data folder: one level up from this file's folder, then "data".
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# How long the screen waits for the pair of searches, in seconds.
# Measured today: a search on type auto took 2.6 to 4.1 seconds.
DEFAULT_TIMEBOX_S = 8

# How long the screen waits for the live re-fetch of a stale page.
REPAIR_TIMEBOX_S = 15

# The network timeout for that re-fetch. Exa may take up to 12 seconds
# to crawl the page (livecrawlTimeout), so 20 leaves room for overhead.
REPAIR_HTTP_TIMEOUT_S = 20

# How long the "Simulate timeout" drill holds back the market channel.
SIMULATED_DELAY_S = 20

# How often the waiting loop wakes up to update the screen, in seconds.
TICK_S = 0.5

# The eight fields every search asks Exa to fill (see channels.json).
SCHEMA_FIELDS = [
    "identifier_in_source",
    "event_type",
    "terms",
    "effective_as_stated",
    "market_effective_date",
    "new_cusip",
    "new_symbol",
    "source_notice_date",
]

# Words that mean "the source did not give this value". We compare in
# lower case, so "Not Stated" and "not stated" both count.
MISSING_WORDS = {"", "not stated", "none", "n/a", "na", "null", "unknown", "not available"}

# Text that shows a page is a placeholder, not the real notice.
STALE_MARKERS = ["page not available", "page may have been moved"]

# ONE thread pool for the whole app, created once when this file is
# first imported. Streamlit re-runs the screen script on every click but
# imports this file only once, so every run shares this pool.
#
# We never write "with ThreadPoolExecutor() as pool:". Leaving a
# with-block like that waits for EVERY thread to finish, which would
# quietly turn the 8-second timebox into the full network timeout.
#
# 8 workers, while exa_client's shared limiter still allows only 4 Exa
# calls at once. The extra workers exist so threads that are asleep in
# the timeout drill can never block a real search from starting.
EXECUTOR = ThreadPoolExecutor(max_workers=8)


# ---------------------------------------------------------------------
# LOADING THE CONFIG FILES
# ---------------------------------------------------------------------

def _load_json(name):
    """Read one JSON file from the data folder into a dictionary."""
    # DATA_DIR / name joins the folder and the file name into one path.
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def load_rows():
    """Return the list of rows in data\\rows.json, in demo order."""
    rows = _load_json("rows.json")["rows"]
    # sorted() returns a new list in order. key= says what to sort by: a
    # small function, written with "lambda", that returns each row's
    # demo_order number.
    return sorted(rows, key=lambda row: row["demo_order"])


def load_channels():
    """Return the channel config in data\\channels.json."""
    return _load_json("channels.json")


def find_row(rows, row_id):
    """Return the row whose id matches, or None."""
    # A plain loop: look at each row until one matches.
    for row in rows:
        if row["id"] == row_id:
            return row
    return None


# ---------------------------------------------------------------------
# BUILDING THE REQUEST BODIES
# ---------------------------------------------------------------------

def domains_for(row, channel, channels):
    """Return the approved domain list for this row and channel."""
    # The settings for this row's asset class, such as nasdaq_equity.
    asset = channels["asset_classes"][row["asset_class"]]
    if channel == "issuer":
        # The wires, plus this issuer's own newsroom when the security
        # master has one. Adding two lists with + makes a new list.
        # .get(row["id"], []) returns [] when this issuer has no site.
        return channels["wires"] + channels["ir_sites"].get(row["id"], [])
    # The market channel: the exchange or the SEC.
    return asset["market_domains"]


def channel_label(row, channel, channels):
    """Return the heading shown above a channel on screen."""
    asset = channels["asset_classes"][row["asset_class"]]
    # An f-string builds the key name, "issuer_label" or "market_label".
    return asset[f"{channel}_label"]


def build_system_prompt(row, channel, channels):
    """Return the systemPrompt: the keep or drop rules for the model."""
    # .format() fills each {name} in the template with the value given.
    return channels["system_prompt_template"].format(
        kind=channels["channel_kinds"][channel],
        subject=row["subject"],
    )


def build_search_body(row, channel, channels, type_override=None):
    """
    Return the /search body for one row and one channel.

    Every piece is fixed text from the two config files, so the same row
    always produces the same body, and its saved run keeps matching.
    """
    return {
        # Retrieval intent only: what the page we want looks like.
        "query": row[f"{channel}_query"],
        # Exa's default type. Sent anyway so the auto versus deep-lite
        # comparison differs by exactly this one line. "or" picks the
        # override when one is given, and "auto" when it is None.
        "type": type_override or "auto",
        # The customer's approved list. A hard filter, fixed in code.
        "includeDomains": domains_for(row, channel, channels),
        # The ticket's evidence window, fixed per row. A bounded window
        # that must be enforced is the case where Exa's guidance says a
        # date filter belongs in the request.
        "startPublishedDate": row["start_published"],
        # The keep or drop rules live here, not in the query.
        "systemPrompt": build_system_prompt(row, channel, channels),
        # The fields we want back, with Exa's per-field citations.
        "outputSchema": channels["output_schema"],
        # The most relevant passages from each page. Code reads these for
        # the identity guard, and a person reads them to confirm.
        "contents": {"highlights": True},
    }


def build_repair_body(url, row, channels):
    """Return the /contents body that re-fetches one stale page live."""
    # The highlights query names what we want from the page. This is the
    # recommended form on /contents, where no search query exists to
    # anchor the highlights to.
    query = channels["repair_query_template"].format(
        issuer=row["issuer_display"],
        # A bond row has no ticker, so fall back to its CUSIP.
        ticker=row["ticker"] or row["cusip"],
        event=row["event_type"],
    )
    return {
        # The one page to fetch. On /contents, options sit at the top
        # level, not inside a "contents" object as on /search.
        "urls": [url],
        # 0 means "do not use your stored copy, crawl the page now".
        "maxAgeHours": channels["repair_max_age_hours"],
        # Give up on the crawl after 12 seconds so one slow page cannot
        # block the request.
        "livecrawlTimeout": channels["repair_livecrawl_timeout_ms"],
        # One content type only: highlights, anchored to our query.
        "highlights": {"query": query},
    }


def build_monitor_body(row, channels):
    """
    Return an Exa Monitor body for the production early-warning job.

    SHOWN ON SCREEN ONLY. The app never sends it: Monitors are not
    covered by zero data retention, and the webhook must be a public
    HTTPS address, which a laptop demo does not have.
    """
    return {
        "name": f"held-issuer watch: {row['issuer_display']}",
        "search": {
            "query": f"{row['legal_names'][0]} announces a redemption, tender offer or exchange offer for its notes",
            "includeDomains": domains_for(row, "issuer", channels) + ["sec.gov"],
            "contents": {"highlights": True},
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
                            "source_notice_date": {"type": "string", "description": "YYYY-MM-DD printed on the notice"},
                        },
                    },
                },
            },
        },
        "metadata": {"team": "security-master", "issuer": row["id"]},
        "webhook": {"url": "https://<customer ticket bridge>/exa-monitor", "events": ["monitor.run.completed"]},
    }


# ---------------------------------------------------------------------
# THE FREE-FORM ROW: a row built from what the user types
# ---------------------------------------------------------------------

# Company-name endings to trim, so "Acme Corp." also matches "Acme
# Corporation" on a page.
NAME_ENDINGS = [", Inc.", " Inc.", ", Inc", " Inc", " Corporation", " Corp.", " Corp", " Limited", " Ltd.", " Ltd", " plc", " PLC"]


def short_name(name):
    """Trim one company ending, for example "Acme Corp." to "Acme"."""
    for ending in NAME_ENDINGS:
        # .endswith checks the last characters of the text.
        if name.endswith(ending):
            # name[: -len(ending)] keeps everything except the ending.
            return name[: -len(ending)].strip()
    return name.strip()


def looks_like_cusip(text):
    """True if the text is 9 letters and digits once spaces are removed."""
    # re.sub(pattern, replacement, text) replaces every match.
    # r"\s" means any whitespace character; the r before the quotes
    # makes a "raw string", so the backslash reaches re unchanged.
    cleaned = re.sub(r"\s", "", text).upper()
    # re.fullmatch requires the WHOLE text to fit the pattern.
    # [0-9A-Z] is any digit or capital letter, and {9} means exactly 9.
    # A ticker is at most 5 characters, so it can never fit.
    return re.fullmatch(r"[0-9A-Z]{9}", cleaned) is not None


def make_free_form_row(identifier, issuer, event, asset_class, channels,
                       field_in_dispute="market_effective_date", vendor_a="", vendor_b=""):
    """Build a row, in the same shape as rows.json, from typed input."""
    # Tidy the typed text: remove spaces at the ends, capital letters.
    identifier = identifier.strip().upper()
    issuer = issuer.strip()
    # A CUSIP or a ticker? A conditional expression: "A if test else B".
    cusip = re.sub(r"\s", "", identifier) if looks_like_cusip(identifier) else ""
    ticker = "" if cusip else identifier
    # The template values shared by the subject and the two queries.
    values = {"issuer": issuer, "ticker": ticker, "cusip": cusip, "event": event}
    # The settings for the chosen asset class.
    asset = channels["asset_classes"][asset_class]
    # A bond has no ticker, so its identity key is issuer plus CUSIP.
    bond = {"issuer": short_name(issuer), "coupon": "", "maturity": ""} if asset_class == "corporate_bond" else None
    # The fixed evidence window from channels.json, never today's date.
    start = channels["free_form_start_published"]
    return {
        "id": ticker or cusip,
        "live_path": True,
        "demo_order": 99,
        "asset_class": asset_class,
        "ticker": ticker,
        "cusip": cusip,
        # Both the full and the trimmed name count as the legal name.
        # A list comprehension, [x for x in ... if ...], builds a list;
        # dict.fromkeys then removes duplicates while keeping the order.
        "legal_names": list(dict.fromkeys([n for n in [issuer, short_name(issuer)] if n])),
        "bond": bond,
        "issuer_display": issuer,
        "event_type": event,
        "break_summary": "Free-form row typed by the user. Vendor values as typed (mocked).",
        "field_in_dispute": field_in_dispute,
        "vendor_a": vendor_a.strip(),
        "vendor_b": vendor_b.strip(),
        "opened_at": "typed now",
        # The first 10 characters of "2026-08-20T00:00:00Z" are the date.
        "window_start": start[:10],
        "start_published": start,
        # **values unpacks the dictionary into name=value arguments, so
        # .format(**values) fills {issuer}, {ticker}, {cusip}, {event}.
        "subject": asset["subject_template"].format(**values),
        "issuer_query": asset["issuer_query_template"].format(**values),
        "market_query": asset["market_query_template"].format(**values),
        "expected_label": "",
        "presenter": {
            "hypothesis": "If this event is real, the issuer's own release and the exchange's or SEC's notice should both describe it, with the same terms.",
            "action": "The app builds the two request bodies from channels.json, the same way as for the fixed rows, and runs the same checks.",
            "expected": "I do not know yet. That is the point of a live row: I say what comes back, field by field.",
            "if_different": "If a channel is empty, I open Show request to check the query and domain list, then the identity guard panel to see what was found and dropped.",
        },
    }


# ---------------------------------------------------------------------
# RUNNING THE TWO SEARCHES UNDER THE TIMEBOX
# ---------------------------------------------------------------------

def _search_job(body, cache_only, delay_s):
    """The work one background thread does: optional pause, then search."""
    # The timeout drill: hold the call back before sending it, so the
    # real timebox code runs, not a shortcut.
    if delay_s:
        time.sleep(delay_s)
    return exa_client.search(body, cache_only=cache_only)


def _wait_with_ticks(futures, timebox_s, on_tick):
    """
    Wait for background jobs, but never past the timebox.

    futures   a dictionary of name -> future. A "future" is a handle to
              a job running on another thread: .done() says whether it
              has finished, .result() gives its return value.
    on_tick   a function to call every half second so the screen can
              show a counting timer, or None for no screen.
    Returns the seconds spent waiting.
    """
    started = time.perf_counter()
    # A set of the jobs still running. .values() gives the futures.
    pending = set(futures.values())
    # Keep going while any job is still running.
    while pending:
        # How much of the timebox is left.
        remaining = timebox_s - (time.perf_counter() - started)
        # Out of time: stop waiting. The jobs keep running on their own.
        if remaining <= 0:
            break
        # Wait up to half a second (or what is left, if less). wait()
        # returns two sets: the jobs now done, and the ones still going.
        # We only need the second, so the first goes into "_", Python's
        # name for "a value I do not need".
        _, pending = wait(pending, timeout=min(TICK_S, remaining))
        # Tell the screen how long we have waited and which jobs are done.
        if on_tick is not None:
            # A dictionary comprehension: {key: value for ... in ...}
            # builds a dictionary, here name -> True or False.
            status = {name: future.done() for name, future in futures.items()}
            on_tick(time.perf_counter() - started, status)
    return time.perf_counter() - started


def _collect(future, fallback_call, timebox_s, what):
    """Take a finished job's envelope, or the saved run if it is late."""
    if future.done():
        try:
            # The job finished in time: its return value is the envelope.
            return future.result()
        except Exception as exc:  # noqa: BLE001, any crash in the thread
            # exa_client is written never to raise, but if something did,
            # show the saved run with the reason instead of crashing.
            envelope = fallback_call()
            envelope["error"] = f"{what} failed: {type(exc).__name__}"
            return envelope
    # Still running at the deadline. Show the saved run instead, and say
    # why. The late thread is left alone: Python cannot stop a running
    # thread. It finishes when Exa answers or its own timeout fires, and
    # saves its answer to cache\ for next time.
    envelope = fallback_call()
    envelope["error"] = f"{what} still running past {timebox_s} s"
    envelope["timed_out"] = True
    return envelope


def run_row(row, channels, timebox_s=DEFAULT_TIMEBOX_S, on_tick=None,
            cache_only=False, simulate_timeout=False):
    """
    Send both searches at once and wait at most timebox_s seconds.

    Returns {"envelopes": {"issuer": ..., "market": ...},
             "bodies": {...}, "wall_ms": ...}
    """
    # Build both bodies first, so the screen can show them either way.
    bodies = {
        "issuer": build_search_body(row, "issuer", channels),
        "market": build_search_body(row, "market", channels),
    }
    # Hand each search to the thread pool. submit() returns at once with
    # a future; the search itself runs on a background thread.
    futures = {}
    for channel, body in bodies.items():
        # The drill delays only the market channel, so the screen shows
        # one live column and one saved column side by side.
        delay = SIMULATED_DELAY_S if (simulate_timeout and channel == "market") else 0
        futures[channel] = EXECUTOR.submit(_search_job, body, cache_only, delay)

    # Poll every half second until both are back or time is up.
    waited = _wait_with_ticks(futures, timebox_s, on_tick)

    # Collect an envelope for each channel, live or saved.
    envelopes = {}
    for channel, future in futures.items():
        # A function inside a loop that remembers this channel's body.
        # "body=bodies[channel]" fixes the value now; without it, every
        # function made in the loop would see the last channel's body.
        def fallback(body=bodies[channel]):
            return exa_client.search(body, cache_only=True)
        envelopes[channel] = _collect(future, fallback, timebox_s, "live call")

    return {"envelopes": envelopes, "bodies": bodies, "wall_ms": int(waited * 1000)}


# ---------------------------------------------------------------------
# READING THE RESULT PAGES
# ---------------------------------------------------------------------

def page_text(result):
    """Return a result's title and highlights as one piece of text."""
    # "or" swaps a missing title (None) for empty text.
    title = result.get("title") or ""
    # Highlights are a list of passages. "\n".join glues them together
    # with a line break between each.
    highlights = "\n".join(result.get("highlights") or [])
    return title + "\n" + highlights


def host_of(url):
    """Return the host of a URL, lower case, without a leading www."""
    # urlparse(url).hostname is the part between "https://" and the
    # first "/", for example "www.globenewswire.com".
    host = (urlparse(url).hostname or "").lower()
    # Drop "www." so "www.sec.gov" and "sec.gov" compare equal.
    if host.startswith("www."):
        host = host[4:]
    return host


def in_allowlist(url, allowlist):
    """True if the URL's host is one of the approved domains."""
    host = host_of(url)
    for domain in allowlist:
        # An exact match, or a sub-domain such as ir.example.com under
        # example.com. The "." in front stops "notsec.gov" matching.
        if host == domain or host.endswith("." + domain):
            return True
    return False


def source_class(url, channels):
    """Tag a URL as issuer wire, issuer IR site, exchange or SEC filing."""
    host = host_of(url)
    # .items() gives each (domain, tag) pair in the config.
    for domain, tag in channels["source_classes"].items():
        if host == domain or host.endswith("." + domain):
            return tag
    return "other"


# ---------------------------------------------------------------------
# STEP A: THE STALE-PAGE DETECTOR (runs before the identity guard)
# ---------------------------------------------------------------------

# A regular expression for a Nasdaq Trader corporate actions alert URL.
# Piece by piece:
#   nasdaqtrader\.com   the site name; "\." is a literal dot, because a
#                       bare "." in a pattern means "any character"
#   /TraderNews\.aspx   the page that shows one notice
#   \?id=ECA            "?" must be escaped too; ECA = Equity Corporate
#                       Actions alert
# re.IGNORECASE makes capital and small letters match each other.
ALERT_URL = re.compile(r"nasdaqtrader\.com/TraderNews\.aspx\?id=ECA", re.IGNORECASE)


def is_stale_page(result):
    """True if a result is an exchange alert whose stored copy is empty
    or a "Page Not Available" placeholder."""
    # Only exchange alert pages are checked.
    if not ALERT_URL.search(result.get("url") or ""):
        return False
    # The highlights on their own, lower case, spaces trimmed.
    text = "\n".join(result.get("highlights") or []).strip().lower()
    # No text at all counts as stale.
    if not text:
        return True
    # any(...) is True if at least one marker appears in the text.
    return any(marker in text for marker in STALE_MARKERS)


def cited_urls(output):
    """Return every URL that Exa's grounding cites, as a set."""
    urls = set()
    # "or []" guards against a missing grounding list.
    for entry in (output or {}).get("grounding") or []:
        for citation in entry.get("citations") or []:
            if citation.get("url"):
                urls.add(citation["url"])
    return urls


def detect_stale(results, output, channel, kept_count):
    """
    Return the URL of a stale exchange page to repair, or None.

    It fires only on the market channel, and only when the stale page is
    the one Exa's answer cites, or when no page at all passed the guard.
    That way a stale page about some other company, sitting further down
    the list, does not trigger a repair on a row that is fine.
    """
    if channel != "market":
        return None
    # Every stale candidate among the raw results, in Exa's order.
    stale = [r["url"] for r in results if is_stale_page(r)]
    if not stale:
        return None
    # First choice: a stale page the model actually leaned on.
    cited = cited_urls(output)
    for url in stale:
        if url in cited:
            return url
    # Second choice: nothing usable came back, so try the stale page.
    if kept_count == 0:
        return stale[0]
    return None


# ---------------------------------------------------------------------
# STEP B: THE IDENTITY GUARD, run by code on the text Exa retrieved
# ---------------------------------------------------------------------

def squash(text):
    """Remove spaces and dashes and use capitals: "68270C 202" -> "68270C202"."""
    # [\s\-] is a "character class": any whitespace or a dash.
    return re.sub(r"[\s\-]", "", text).upper()


def exchange_ticker_regex(ticker):
    """
    Build a pattern for a ticker written with its exchange, such as
    "Nasdaq: CDT", "NASDAQ:CDT", "Nasdaq CM: CTNT" or "Symbol: CDT".

    Piece by piece:
      \\b                         a word boundary, so "XNasdaq" cannot match
      (?:NASDAQ|NYSE AMERICAN|NYSE|SYMBOL)
                                  one of these words; (?: ) groups them
                                  without saving the match
      (?:\\s+(?:CM|GM|GS))?       optionally a Nasdaq tier, such as " CM";
                                  the final ? means "zero or one time"
      \\s*:\\s*                   a colon, with any spaces around it
      re.escape(ticker)           the ticker itself, with any special
                                  characters made literal
      \\b                         a word boundary, so "CDTX" cannot match
    """
    pattern = (
        r"\b(?:NASDAQ|NYSE AMERICAN|NYSE|SYMBOL)(?:\s+(?:CM|GM|GS))?\s*:\s*"
        + re.escape(ticker)
        + r"\b"
    )
    return re.compile(pattern, re.IGNORECASE)


# A CUSIP printed after the word CUSIP, as on "CUSIP No. 06051GLX5".
# Piece by piece:
#   CUSIP                     the word itself
#   (?:\s*(?:NO\.?|NUMBER|#))?  optionally "No.", "Number" or "#"
#   \s*:?\s*                  an optional colon, with spaces
#   ( ... )                   a "capture group": the part we keep
#   [0-9]{3}[0-9A-Z]{3}       6 characters: 3 digits, then 3 digits or letters
#   \s?                       an optional space, as in "68270C 202"
#   [0-9A-Z]{2}[0-9]          2 more characters, then the check digit
PRINTED_CUSIP = re.compile(
    r"CUSIP(?:\s*(?:NO\.?|NUMBER|#))?\s*:?\s*([0-9]{3}[0-9A-Z]{3}\s?[0-9A-Z]{2}[0-9])",
    re.IGNORECASE,
)


def printed_cusips(text):
    """Return every CUSIP printed after the word CUSIP, squashed."""
    # findall returns the captured part of every match, as a list.
    return {squash(found) for found in PRINTED_CUSIP.findall(text)}


def _names_on_page(text, row):
    """Return the first legal name of this row found in the text, or ""."""
    lowered = text.lower()
    for name in row["legal_names"]:
        if name and name.lower() in lowered:
            return name
    return ""


def _match_bond(text, row):
    """Identity for a bond: issuer name plus CUSIP, or coupon plus maturity."""
    bond = row["bond"]
    # The issuer's name must be on the page, or it is not this bond.
    if not _names_on_page(text, row) and bond["issuer"].lower() not in text.lower():
        return "none", "issuer name not on the page"
    # Our CUSIP on the page: the strongest match.
    if row["cusip"] and row["cusip"] in squash(text):
        return "strong", f"issuer name and CUSIP {row['cusip']}"
    # The page prints CUSIPs, but not ours: it is about another series.
    others = printed_cusips(text)
    if others:
        # sorted() makes the order stable; ", ".join lists them.
        return "none", "a different series: CUSIP " + ", ".join(sorted(others))
    # No CUSIP printed: coupon and maturity must both appear.
    coupon = bond.get("coupon", "")
    maturity = bond.get("maturity", "")
    if coupon and maturity and coupon.lower() in text.lower() and maturity.lower() in text.lower():
        return "strong", f"issuer, coupon ({coupon}) and maturity ({maturity}); no CUSIP printed"
    return "amber", "issuer name only; no CUSIP, coupon or maturity to confirm the series"


def match_identity(text, row):
    """
    Decide how strongly a page's own text names this security.

    Returns a pair: a level and a reason.
      "strong"  exchange-prefixed ticker, CUSIP or legal name
      "amber"   a bare ticker only. "CDT" alone is also Central Daylight
                Time, so a bare ticker is never enough on its own.
      "none"    not about this security
    """
    # Bonds have their own rule.
    if row.get("bond"):
        return _match_bond(text, row)
    # 1. The CUSIP, once spaces are removed on both sides.
    if row["cusip"] and row["cusip"] in squash(text):
        return "strong", f"CUSIP {row['cusip']}"
    # 2. The ticker with its exchange, such as "Nasdaq: CDT".
    if row["ticker"]:
        found = exchange_ticker_regex(row["ticker"]).search(text)
        # .group(0) is the exact text that matched.
        if found:
            return "strong", f"exchange-prefixed ticker '{found.group(0)}'"
    # 3. The legal name.
    name = _names_on_page(text, row)
    if name:
        return "strong", f"legal name '{name}'"
    # 4. The bare ticker as a whole word, capitals only: amber.
    if row["ticker"] and re.search(r"\b" + re.escape(row["ticker"]) + r"\b", text):
        return "amber", f"bare ticker '{row['ticker']}' only (could be another meaning)"
    return "none", "no exchange-prefixed ticker, CUSIP or legal name on the page"


def identity_guard(results, row):
    """Split result pages into kept, amber and dropped, with reasons."""
    guard = {"kept": [], "amber": [], "dropped": []}
    for result in results:
        level, reason = match_identity(page_text(result), row)
        # A small summary of the page, enough for the screen.
        item = {
            "url": result.get("url") or "",
            "title": result.get("title") or "",
            "published": (result.get("publishedDate") or "")[:10],
            "highlights": result.get("highlights") or [],
            "reason": reason,
        }
        # Map the level to the list it belongs in.
        if level == "strong":
            guard["kept"].append(item)
        elif level == "amber":
            guard["amber"].append(item)
        else:
            guard["dropped"].append(item)
    return guard


# ---------------------------------------------------------------------
# STEP C: THE CITATION CHECK, field by field
# ---------------------------------------------------------------------

def read_fields(data):
    """Return the model's fields as a dictionary, or {} if there are none."""
    content = (data.get("output") or {}).get("content")
    # Exa may send the fields as JSON text. Turn text into a dictionary.
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except ValueError:
            return {}
    # Anything that is still not a dictionary means no usable fields.
    return content if isinstance(content, dict) else {}


def is_missing(value):
    """True if a field value means "the source does not give this"."""
    if value is None:
        return True
    # str() turns any value into text; .strip().lower() tidies it.
    text = str(value).strip().lower()
    return text in MISSING_WORDS or text.startswith("not stated")


def check_grounding(data, guard, allowlist):
    """
    Give every field a status, checked in code:
      verified    has a value, and a cited page is on the approved list
                  AND passed the identity guard
      missing     the value is "not stated" or empty. Exa's confidence is
                  ignored here on purpose: today a "not stated" field
                  came back with confidence "high".
      unverified  has a value, but no cited page passes both checks
    """
    fields = read_fields(data)
    output = data.get("output") or {}
    # Index the grounding list by field name for quick lookup.
    grounding = {}
    for entry in output.get("grounding") or []:
        grounding[entry.get("field")] = entry
    # The URLs of the pages that passed the identity guard.
    kept_urls = {item["url"] for item in guard["kept"]}

    checks = {}
    for field in SCHEMA_FIELDS:
        value = fields.get(field)
        entry = grounding.get(field) or {}
        # Every cited URL for this field, skipping blanks.
        citations = [c.get("url") for c in entry.get("citations") or [] if c.get("url")]
        # The citations that pass both code checks.
        good = [u for u in citations if in_allowlist(u, allowlist) and u in kept_urls]

        if is_missing(value):
            status, reason = "missing", "the source does not give it (confidence ignored)"
        elif good:
            status, reason = "verified", "cited page is approved and names this security"
        elif not citations:
            status, reason = "unverified", "no citation for this field"
        elif not any(in_allowlist(u, allowlist) for u in citations):
            status, reason = "unverified", "citation is outside the approved domains"
        else:
            status, reason = "unverified", "cited page failed the identity check"

        checks[field] = {
            "value": "" if value is None else str(value),
            "status": status,
            "confidence": entry.get("confidence", ""),
            "citations": citations,
            # The first good citation, or "" if none.
            "cited_url": good[0] if good else "",
            "reason": reason,
        }
    return checks


def check_channel(row, channel, envelope, channels):
    """Run steps A, B and C on one channel's envelope."""
    data = envelope.get("data") or {}
    results = data.get("results") or []
    allowlist = domains_for(row, channel, channels)
    # Step B first in code order, because step A needs the kept count;
    # step A still reads the RAW results, so the guard cannot hide a
    # placeholder page from it.
    guard = identity_guard(results, row)
    stale_url = detect_stale(results, data.get("output"), channel, len(guard["kept"]))
    fields = check_grounding(data, guard, allowlist)
    return {
        "channel": channel,
        "label": channel_label(row, channel, channels),
        "envelope": envelope,
        "allowlist": allowlist,
        "guard": guard,
        "stale_url": stale_url,
        "fields": fields,
    }


# ---------------------------------------------------------------------
# THE REPAIR: one live re-fetch of a stale exchange page
# ---------------------------------------------------------------------

def repair_outcome(envelope):
    """
    Decide whether a /contents re-fetch really worked.

    Returns (ok, reason, text). Exa can answer HTTP 200 with status
    "success" and still hand back an empty page. Today it did exactly
    that for nasdaqtrader.com, so "success" with no text is a FAILURE.
    """
    if not envelope["ok"]:
        # "or" supplies a reason when the error text is empty, which
        # happens in saved-runs mode when no saved run exists.
        return False, f"re-fetch failed: {envelope['error'] or 'no saved run for this request'}", ""
    data = envelope["data"]
    # /contents reports each URL's own status in a "statuses" list.
    statuses = data.get("statuses") or []
    status = statuses[0] if statuses else {}
    if status.get("status") != "success":
        # The error tag, such as CRAWL_TIMEOUT, read out word for word.
        tag = (status.get("error") or {}).get("tag", "") if isinstance(status.get("error"), dict) else str(status.get("error") or "")
        return False, f"Exa status '{status.get('status', 'none')}' {tag}".strip(), ""
    results = data.get("results") or []
    page = results[0] if results else {}
    # Everything readable on the page: text plus highlights.
    text = (page.get("text") or "") + "\n".join(page.get("highlights") or [])
    if not text.strip():
        return False, (
            f"Exa reported status 'success' (source: {status.get('source', '?')}) "
            f"but the page came back empty; title '{page.get('title', '')}'. "
            "Treated as a failure."
        ), ""
    if any(marker in text.lower() for marker in STALE_MARKERS):
        return False, "the live copy is still the 'Page Not Available' placeholder", text
    return True, "live copy has text", text


def repair(url, row, channels, cache_only=False, timebox_s=REPAIR_TIMEBOX_S, on_tick=None):
    """Re-fetch one stale page live, under its own timebox."""
    body = build_repair_body(url, row, channels)
    # submit() also passes name=value arguments through to the function.
    future = EXECUTOR.submit(
        exa_client.contents, body, cache_only=cache_only, timeout=REPAIR_HTTP_TIMEOUT_S
    )
    _wait_with_ticks({"repair": future}, timebox_s, on_tick)

    # A small function that returns the saved run for this body.
    def fallback():
        return exa_client.contents(body, cache_only=True)

    envelope = _collect(future, fallback, timebox_s, "live re-fetch")
    ok, reason, text = repair_outcome(envelope)
    # The page's title counts as its text too, for the identity check.
    results = envelope["data"].get("results") or []
    title = results[0].get("title", "") if results else ""
    # Even a page with text must name this security before it counts.
    if ok:
        level, why = match_identity(title + "\n" + text, row)
        if level != "strong":
            ok, reason = False, f"re-fetched page does not name this security ({why})"
    return {
        "url": url,
        "body": body,
        "envelope": envelope,
        "ok": ok,
        "reason": reason,
        "text": text,
        # The new CUSIP, read by code from the repaired text, or "".
        "cusip": cusip_after_word(text) if ok else "",
    }


# A CUSIP that follows the word CUSIP within a short phrase, as in
# "the CUSIP number will change to 16307X400". Piece by piece:
#   CUSIP\b            the word CUSIP
#   [^.]{0,40}?        up to 40 characters that are not a full stop; the
#                      ? makes it "as few as possible", so the nearest
#                      CUSIP wins
#   \b([0-9]{3}[0-9A-Z]{5}[0-9])\b
#                      a whole 9-character CUSIP: 3 digits, 5 digits or
#                      letters, and a final check digit
CUSIP_PHRASE = re.compile(r"CUSIP\b[^.]{0,40}?\b([0-9]{3}[0-9A-Z]{5}[0-9])\b")


def cusip_after_word(text):
    """Return the first CUSIP printed shortly after the word CUSIP, or ""."""
    found = CUSIP_PHRASE.search(text)
    return found.group(1) if found else ""


# ---------------------------------------------------------------------
# THE WHOLE ROW
# ---------------------------------------------------------------------

def check_row(row, channels, timebox_s=DEFAULT_TIMEBOX_S, on_tick=None,
              cache_only=False, simulate_timeout=False, on_repair_tick=None):
    """Gather and check all the evidence for one row."""
    started = time.perf_counter()
    run = run_row(row, channels, timebox_s, on_tick, cache_only, simulate_timeout)
    # Check each channel with steps A, B and C.
    checked = {}
    for channel in ("issuer", "market"):
        checked[channel] = check_channel(row, channel, run["envelopes"][channel], channels)
    # Step 3: repair a stale exchange page, if one was found.
    repaired = None
    if checked["market"]["stale_url"]:
        repaired = repair(checked["market"]["stale_url"], row, channels,
                          cache_only=cache_only, on_tick=on_repair_tick)
    result = {
        "row": row,
        "channels": checked,
        "repair": repaired,
        "search_wall_ms": run["wall_ms"],
        "wall_ms": int((time.perf_counter() - started) * 1000),
    }
    result["cost_live"] = live_cost(result)
    return result


def all_envelopes(result):
    """Every envelope in a checked row: two searches, plus any repair."""
    envelopes = [result["channels"]["issuer"]["envelope"], result["channels"]["market"]["envelope"]]
    if result.get("repair"):
        envelopes.append(result["repair"]["envelope"])
    return envelopes


def live_cost(result):
    """Dollars actually spent on this row: live calls only, not replays."""
    total = 0.0
    for envelope in all_envelopes(result):
        # A saved run costs nothing today, so only "live" is counted.
        if envelope["source"] == "live" and envelope["cost_dollars"] is not None:
            total += envelope["cost_dollars"]
    # round() keeps the number tidy on screen.
    return round(total, 4)
