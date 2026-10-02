"""
exa_client.py - the only file in the app that talks to Exa.

WHAT THIS FILE DOES, IN ONE SENTENCE
  It sends a request to Exa, and no matter what happens (success, slow
  network, bad key, no credits) it hands back the same small package of
  information, so the screen code never crashes and never has to guess.

WHY IT EXISTS
  1. One place for the API key, the timeout and the retry rules.
  2. Every good response is saved to disk, so the demo still works if
     the network or the API has a bad minute. That saved copy is the
     "cache", and using it when a live call fails is the "fallback".
  3. Every call returns the same package, called the "envelope" here.
     An envelope is a dictionary (a set of labelled values) that wraps
     Exa's answer together with facts about the call: did it work, was
     it live or saved, how long it took, what it cost.
  4. One shared "limiter" makes sure no more than 4 calls are in flight
     at once, across every row and every channel, so the app stays well
     under Exa's rate limits even when several things run together.

WHY PLAIN HTTP INSTEAD OF EXA'S PYTHON SDK
  An SDK is a helper library a vendor publishes for its own API.
  Exa's SDK (exa-py) adds full page text to a contents request whenever
  you do not ask for text, a summary or extras, even when you ask only
  for highlights, so it bills two content types. Its search() adds text
  only when you pass no contents at all. With plain HTTP, the JSON body
  we build is exactly what goes over the wire, so it matches Exa's API
  reference field for field and the screen can show it honestly.

TWO CACHE FOLDERS
  cache_golden\\  Known-good saved runs, frozen on purpose. This file
                 READS it but NEVER writes to it.
  cache\\         The working folder. Every live success is written here.
  When a live call cannot be used, the fallback reads cache_golden\\
  first and cache\\ second, and records which one it used.

HOW ONE CALL FLOWS THROUGH THIS FILE
  search(body)
    -> call("/search", body)
         1. work out the cache file name for this exact request
         2. load the saved answer for it: golden folder first, then
            working folder. May find nothing.
         3. "saved run" mode on?      -> return the saved answer
         4. no API key?               -> return the saved answer
         5. wait for a free slot in the shared limiter, then send
              timeout or network down -> return the saved answer
              HTTP 200 (success)      -> save it to cache\\, return "live"
              HTTP 429 or 503         -> wait briefly, try again
              any other error         -> return the saved answer
    <- an envelope, every time

WHAT AN ENVELOPE LOOKS LIKE
  {
    "ok": True,                  there is something to show
    "data": {...},               Exa's response, untouched
    "source": "live",            "live", "cache" or "none"
    "saved_from": "",            "golden" or "working" for a saved answer
    "error": "",                 why the live call failed, if it did
    "elapsed_ms": 812,           how long the live call took
    "saved_at": "",              when a cached answer was first fetched
    "cost_dollars": 0.007,       estimated spend for this call
    "request_id": "abc123",      the ID to quote to Exa support
    "queued": False,             did Exa hold the call in its rate queue
    "queue_ms": 0,               and for how long, in milliseconds
    "cache_write_error": "",     why saving to cache\\ failed, if it did
    "endpoint": "/search",       which Exa endpoint was called
    "body": {...},               the exact request that was sent
  }

NAMING NOTE
  A function whose name starts with an underscore, like _read_cache, is
  a helper meant for use inside this file only. The rest of the app
  should only ever call search() and contents().
"""

# ---------------------------------------------------------------------
# IMPORTS: tools this file borrows from Python and from installed packages
# ---------------------------------------------------------------------

# hashlib makes a "hash": a short fingerprint of a piece of text.
# We use it to turn a request into a file name.
import hashlib

# json converts between Python dictionaries and JSON text.
# Exa speaks JSON, and our cache files are JSON.
import json

# os lets us read environment variables, which is where the key lives.
# It also gives us os.replace, used to save files safely.
import os

# threading gives us locks and semaphores: tools that stop two threads
# (two jobs running at the same time) from stepping on each other.
import threading

# time gives us a stopwatch and the ability to pause between retries.
import time

# Path builds file and folder paths that work on Windows, Mac and Linux.
from pathlib import Path

# requests is the library that actually sends the HTTP request.
import requests

# load_dotenv reads a .env file and puts its values into the environment.
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# SETTINGS: values fixed for the whole app. Capital letters are the
# Python convention for "this is a constant, do not change it in code".
# ---------------------------------------------------------------------

# __file__ is the path of this file (.../exa-demo/app/exa_client.py).
# resolve() makes it a full path. parent is the folder holding it (app).
# parent.parent is one level higher again: the project folder, exa-demo.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# The working cache folder sits inside the project folder. Live calls
# write here. With Path objects, the / sign means "join these into one path".
CACHE_DIR = PROJECT_DIR / "cache"

# The frozen folder of known-good runs. Read first, never written.
GOLDEN_DIR = PROJECT_DIR / "cache_golden"

# Exa's web address. Each endpoint path ("/search") is added to the end.
BASE_URL = "https://api.exa.ai"

# How many seconds to wait for Exa before giving up, by search type.
# "type" is Exa's setting for how hard it works on a search.
# The fast types answer in under a second, so 10 seconds is generous.
# The deep types run several searches and then write a summary, so they
# need longer. The numbers are about three times Exa's stated latency,
# so a slow-but-working call is not cut off early.
TIMEOUT_BY_TYPE = {
    "instant": 10,  # Exa says about 0.25 seconds
    "fast": 10,  # about 0.45 seconds
    "auto": 15,  # about 1 second. This is Exa's default type.
    "deep-lite": 30,  # about 4 seconds
    "deep": 45,  # 4 to 15 seconds
    "deep-reasoning": 90,  # 12 to 40 seconds
}

# Exa's list price for one call of each type, in dollars.
# Exa prices per 1,000 calls, so $7 per 1,000 is $0.007 per call.
# Used only as a backup when Exa's response carries no cost figure.
PRICE_BY_TYPE = {
    "instant": 0.004,  # $4 per 1,000
    "fast": 0.007,  # $7 per 1,000
    "auto": 0.007,  # $7 per 1,000
    "deep-lite": 0.012,  # $12 per 1,000
    "deep": 0.012,  # $12 per 1,000
    "deep-reasoning": 0.015,  # $15 per 1,000
}

# The list price of one content type for one page on /contents: $1 per
# 1,000 pages. Used only when a /contents response carries no cost.
PRICE_PER_PAGE_CONTENT = 0.001

# The longest we will ever pause before a retry, in seconds.
# A live demo cannot sit silent for longer than this.
MAX_RETRY_WAIT = 5.0

# The most Exa calls allowed in flight at the same moment, app-wide.
MAX_CALLS_IN_FLIGHT = 4

# The shortest gap between two request starts, in seconds. With at most
# 4 in flight and starts 0.25 s apart, no more than 4 calls start in any
# one second, which keeps us well under Exa's 10 per second for /search.
MIN_START_GAP = 0.25

# A BoundedSemaphore is a counter of free slots. acquire() takes a slot
# and waits if none is free; release() gives it back. "Bounded" means
# releasing more slots than were taken raises an error, which catches
# bugs. It is created once, here, so every thread shares the same one.
_LIMIT = threading.BoundedSemaphore(MAX_CALLS_IN_FLIGHT)

# A Lock lets only one thread at a time run the code it guards. We use
# it so two threads cannot both decide "it has been 0.25 s" at once.
_START_LOCK = threading.Lock()

# The time of the most recent request start. It sits in a dictionary so
# functions can change it without Python's "global" keyword.
_LAST_START = {"at": 0.0}

# Read the .env file now, once, when this file is first imported.
# After this line, the key is available through os.environ.
# The key lives in .env and not in the code so it never ends up in a
# shared file, a screenshot of the code, or a git repository.
load_dotenv(PROJECT_DIR / ".env")


# ---------------------------------------------------------------------
# THE API KEY
# ---------------------------------------------------------------------

def api_key():
    """Return the Exa key, or an empty string if none is set."""
    # os.environ is a dictionary of environment variables.
    # .get("EXA_API_KEY", "") means: give me that value, and if it does
    # not exist give me "" (empty text) instead of raising an error.
    # .strip() removes any space or line break that was pasted along
    # with the key. A trailing space would make Exa reject the key.
    return os.environ.get("EXA_API_KEY", "").strip()


# ---------------------------------------------------------------------
# THE CACHE: saving good answers and loading them back
# ---------------------------------------------------------------------

def cache_path(endpoint, body, folder=None):
    """Return the file that a given request is saved under."""
    # folder=None means "the caller did not choose a folder". We look up
    # CACHE_DIR here, at call time, rather than writing folder=CACHE_DIR
    # in the line above, because a default in the def line is fixed once
    # at import time and tests need to point CACHE_DIR somewhere else.
    if folder is None:
        folder = CACHE_DIR

    # Goal: the same request must always map to the same file name, and
    # two different requests must never share one.
    #
    # Step 1. Turn the request into text.
    # json.dumps converts a dictionary to JSON text.
    # sort_keys=True puts the keys in alphabetical order, so
    # {"a": 1, "b": 2} and {"b": 2, "a": 1} produce identical text.
    # Without it, the same request could get two different file names.
    canonical = json.dumps({"endpoint": endpoint, "body": body}, sort_keys=True)

    # Step 2. Fingerprint that text.
    # .encode("utf-8") turns text into raw bytes, which sha256 needs.
    # sha256 is a standard hash: same input, same output, every time.
    # .hexdigest() gives the fingerprint as letters and digits.
    # [:16] keeps the first 16 characters. The full 64 are not needed
    # for a handful of files and would make long file names.
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    # Step 3. Build the path, for example cache/3fa91c0b7e2d4a18.json
    # The f before the quotes makes this an f-string: anything inside
    # curly braces is replaced by that variable's value.
    return folder / f"{digest}.json"


def _read_cache(path):
    """Load a saved response, or return None if there is not one."""
    # If the file is not there, nothing was ever saved for this request.
    # None is Python's word for "no value".
    if not path.exists():
        return None
    # try / except means: attempt this, and if it raises one of the
    # named errors, run the except block instead of crashing.
    try:
        # read_text loads the file as text. json.loads turns that text
        # back into a dictionary.
        return json.loads(path.read_text(encoding="utf-8"))
    # OSError covers "could not read the file" (locked, no permission).
    # JSONDecodeError covers "the file is not valid JSON", which happens
    # if the app was closed halfway through writing it.
    except (OSError, json.JSONDecodeError):
        # Treat a broken cache file the same as no cache file.
        return None


def _read_fallback(endpoint, body):
    """Find a saved answer: golden folder first, then working folder."""
    # The same file name is used in both folders, because the name comes
    # only from the request. So we try the golden copy first.
    golden = _read_cache(cache_path(endpoint, body, GOLDEN_DIR))
    # "is not None" means a record was found and loaded.
    if golden is not None:
        # Return two values at once: the record and where it came from.
        # Python packs them into a "tuple" (a fixed pair of values).
        return golden, "golden"
    # No golden copy. Try the working folder, which holds whatever the
    # app saved from earlier live calls, such as a free-form row.
    working = _read_cache(cache_path(endpoint, body, CACHE_DIR))
    if working is not None:
        return working, "working"
    # Nothing saved anywhere.
    return None, ""


def _write_cache(path, endpoint, body, data, elapsed_ms, queued=False, queue_ms=0):
    """
    Save a good response to the working folder, safely.

    Returns "" on success, or a short reason if the save failed. A failed
    save must never turn a live success into a crash, so it never raises.
    """
    # Bundle the response with the facts we want to show on replay.
    record = {
        # The date and time of the live call, e.g. 2026-10-02 18:41:07.
        # Shown on screen so nobody mistakes a saved answer for a live one.
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        # Which Exa endpoint answered.
        "endpoint": endpoint,
        # The exact request, so the "show request" panel works on replay.
        "body": body,
        # How long the live call took, so replay shows a real timing.
        "elapsed_ms": elapsed_ms,
        # Whether Exa held the call in its rate-limit queue, and how long.
        "queued": queued,
        "queue_ms": queue_ms,
        # Exa's full response, untouched.
        "data": data,
    }

    # Write to a temporary file first, then move it into place. The name
    # includes the process id and the thread id, so two threads saving
    # at the same time never share a temp file. os.replace swaps the
    # finished file in one step, so a reader never sees half a file.
    temp = path.with_name(f"{path.stem}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        # Create the cache folder if it does not exist yet.
        # parents=True also creates any missing folders above it.
        # exist_ok=True means "do not complain if it is already there".
        path.parent.mkdir(parents=True, exist_ok=True)
        # json.dumps turns the record into text. indent=1 puts each field
        # on its own line so the file is readable if opened in an editor.
        temp.write_text(json.dumps(record, indent=1), encoding="utf-8")
        # Move the finished temp file over the real name.
        os.replace(temp, path)
        # Empty text means "no error".
        return ""
    except OSError as exc:
        # The disk was full, the folder was locked, and so on. Tidy up
        # the temp file if it was created. missing_ok=True means "do not
        # complain if it is not there".
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            # Even the tidy-up failed. Nothing more we can do; carry on.
            pass
        # Report the problem as text instead of crashing.
        return f"could not save to cache: {type(exc).__name__}"


# ---------------------------------------------------------------------
# THE ENVELOPE: the one shape every call returns
# ---------------------------------------------------------------------

def _list_price(endpoint, body):
    """Estimate the cost of a call when Exa's response carries none."""
    # /contents is priced per page and per content type. A request for
    # highlights on 1 page is $0.001. Text plus highlights is $0.002.
    if endpoint == "/contents":
        # How many pages were asked for. "or []" swaps a missing list for
        # an empty one so len() is safe.
        pages = len(body.get("urls") or body.get("ids") or [])
        # Count the content types that were asked for. A generator like
        # (1 for k in ... if ...) produces a 1 for each match, and sum()
        # adds them up.
        types = sum(1 for k in ("text", "highlights", "summary") if body.get(k))
        # If no content type was named, Exa returns full text by default,
        # which still counts as one. max(1, types) enforces that minimum.
        return pages * max(1, types) * PRICE_PER_PAGE_CONTENT
    # /search is priced per call by type. Exa's default type is "auto".
    return PRICE_BY_TYPE.get(body.get("type", "auto"))


def _envelope(ok, data, body, endpoint, source, elapsed_ms, error="",
              saved_at="", saved_from="", queued=False, queue_ms=0,
              cache_write_error=""):
    """Build the package that every caller gets back."""
    # error="" and the other name=value parts are default values: a
    # caller that has nothing to say for them can leave them out.

    # Start with no cost figure. We fill it in below if we can.
    cost = None

    # isinstance checks that data really is a dictionary. On a failed
    # call data is None, and calling .get on None would crash.
    if isinstance(data, dict):
        # Exa reports an estimated cost on each response, like this:
        #   "costDollars": {"total": 0.007, ...}
        # data.get("costDollars") returns that inner dictionary, or None
        # if the field is missing. "or {}" swaps None for an empty
        # dictionary so the second .get is safe either way.
        cost = (data.get("costDollars") or {}).get("total")

    # If the call worked but Exa sent no cost, use the list price, so
    # the cost panel on screen is never blank.
    if cost is None and ok:
        cost = _list_price(endpoint, body)

    # Return the envelope. Every key is always present, so the screen
    # code can read any of them without checking first.
    return {
        # True when there is something to show, live or saved.
        "ok": ok,
        # Exa's response. "or {}" gives an empty dictionary on failure.
        "data": data or {},
        # "live" = fresh from Exa. "cache" = saved copy. "none" = nothing.
        "source": source,
        # For a saved copy: "golden" (frozen folder) or "working" (cache\).
        "saved_from": saved_from,
        # Plain-English reason the live call failed. Empty on success.
        # It is kept even when a saved answer is shown, so the presenter
        # can say out loud what went wrong.
        "error": error,
        # Time the live call took, in milliseconds (1000 = one second).
        "elapsed_ms": elapsed_ms,
        # When a saved answer was originally fetched. Empty for live.
        "saved_at": saved_at,
        # Estimated spend for this one call, in dollars.
        "cost_dollars": cost,
        # Exa's ID for this request. Exa support asks for it.
        "request_id": (data or {}).get("requestId", ""),
        # Did the request wait in Exa's rate-limit queue, and how long.
        "queued": queued,
        "queue_ms": queue_ms,
        # Why the save to cache\ failed, if it did. Empty otherwise.
        "cache_write_error": cache_write_error,
        # Kept so the screen can show exactly what was sent, and where.
        "endpoint": endpoint,
        "body": body,
    }


# ---------------------------------------------------------------------
# ERROR MESSAGES: turning status codes into sentences
# ---------------------------------------------------------------------

def _explain(status, payload):
    """Turn an HTTP failure into a sentence a presenter can read out."""
    # Every HTTP response carries a status code. 200 means success.
    # Codes from 400 to 499 mean the request was the problem.
    # Codes from 500 to 599 mean the server was the problem.
    #
    # Exa's error responses look like this:
    #   {"requestId": "...", "error": "Invalid API key", "tag": "INVALID_API_KEY"}
    # "tag" is a short machine-readable label. "error" is the detail.
    # The isinstance check guards against a response that is not a
    # dictionary at all, such as an HTML error page from a proxy.
    tag = payload.get("tag", "") if isinstance(payload, dict) else ""
    detail = payload.get("error", "") if isinstance(payload, dict) else ""

    # Our own plain-English wording for the codes Exa documents.
    reasons = {
        400: "Exa rejected the request as invalid",
        401: "the API key is missing or wrong",
        402: "the account is out of credits or over its budget",
        403: "this feature is not enabled for the account",
        429: "too many requests in a short time",
        500: "Exa had an internal error",
        503: "Exa is overloaded right now (this call is not billed)",
    }

    # Look up the code. If it is one we did not list, fall back to a
    # generic sentence that still shows the number.
    reason = reasons.get(status, f"Exa returned HTTP {status}")

    # Add Exa's own tag and detail after our sentence.
    # str(detail)[:200] caps the detail at 200 characters so a long
    # error cannot flood the screen.
    # "if x" drops any piece that is empty, and " ".join glues the rest
    # together with single spaces.
    extra = " ".join(x for x in [tag, str(detail)[:200]] if x)

    # .strip() removes the trailing space left when extra is empty.
    return f"{reason}. {extra}".strip()


def _retry_wait(resp, attempt):
    """Work out how many seconds to pause before trying again."""
    # When Exa is rate limiting, it may send a Retry-After header that
    # says how long to wait. Headers are labelled values sent alongside
    # the response body.
    header = resp.headers.get("Retry-After", "")
    try:
        # The usual form is a number of seconds, such as "2".
        wait = float(header)
    except ValueError:
        # The header was missing, or it held a date instead of a number
        # (the HTTP standard allows both). Wait 1 second on the first
        # retry and 2 on the second, so we back off a little more each
        # time.
        wait = float(attempt)
    # min() picks the smaller value, so we never pause longer than the
    # cap. max() with 0 guards against a negative number.
    return max(0.0, min(wait, MAX_RETRY_WAIT))


# ---------------------------------------------------------------------
# THE SHARED LIMITER: at most 4 calls in flight, starts spaced apart
# ---------------------------------------------------------------------

def _wait_for_start_turn():
    """Pause if the previous request started less than 0.25 s ago."""
    # "with _START_LOCK:" is a with-block. It takes the lock on the way
    # in and always gives it back on the way out, even if an error
    # happens inside. Only one thread at a time can be inside this block.
    with _START_LOCK:
        # time.monotonic() is a clock that never jumps backwards, which
        # makes it safe for measuring gaps.
        gap = _LAST_START["at"] + MIN_START_GAP - time.monotonic()
        # A positive gap means we are too early. Sleep the difference.
        if gap > 0:
            time.sleep(gap)
        # Record this start, so the next thread measures from it.
        _LAST_START["at"] = time.monotonic()


def _post(url, headers, body, timeout):
    """Send one POST inside the shared limiter, and free the slot after."""
    # Take one of the 4 slots. If all 4 are busy, this line waits until
    # another call finishes and gives its slot back.
    _LIMIT.acquire()
    # try / finally means: run the try part, and ALWAYS run the finally
    # part afterwards, whether the try part worked or raised an error.
    # That guarantees the slot is given back, so a failed call can never
    # leave a slot taken forever.
    try:
        # Keep request starts at least 0.25 s apart.
        _wait_for_start_turn()
        # Send the request. POST is the HTTP verb for "here is some
        # data, do something with it". Every Exa endpoint we use takes
        # POST. json=body converts the dictionary to JSON text for us.
        # timeout stops us waiting forever on a stalled connection.
        return requests.post(url, headers=headers, json=body, timeout=timeout)
    finally:
        # Give the slot back as soon as the post returns or fails. No
        # slot is held while a retry is sleeping.
        _LIMIT.release()


# ---------------------------------------------------------------------
# THE MAIN FUNCTION: send one request, always return an envelope
# ---------------------------------------------------------------------

def call(endpoint, body, cache_only=False, max_retries=2, timeout=None):
    """
    Send one request to Exa and always return an envelope.

    endpoint     the path, such as "/search" or "/contents"
    body         the JSON request body, exactly as Exa's reference shows it
    cache_only   True replays the saved answer and makes no network call
    max_retries  how many times to retry when Exa says "try again"
    timeout      seconds to wait for Exa. None means "use the table above"
    """
    # Load the saved answer now, before any network call. If the live
    # call fails later, the fallback is already in hand. May be None.
    cached, cached_from = _read_fallback(endpoint, body)

    # A function defined inside another function. It can see the
    # variables of the outer one (cached, body, endpoint), so each
    # failure branch below needs only one short line.
    def from_cache(reason):
        """Return the saved answer, keeping the failure reason visible."""
        # Nothing saved: report a failure. The screen shows the reason.
        if cached is None:
            return _envelope(False, None, body, endpoint, "none", 0, error=reason)
        # Something saved: return it, marked as "cache", along with why
        # the live call was not used and which folder it came from.
        return _envelope(
            True,  # ok: there is something to show
            cached["data"],  # Exa's response from the earlier live call
            body,
            endpoint,
            "cache",  # source: be honest that this is not live
            cached.get("elapsed_ms", 0),  # the timing of that live call
            error=reason,
            saved_at=cached.get("saved_at", ""),
            saved_from=cached_from,  # "golden" or "working"
            queued=cached.get("queued", False),
            queue_ms=cached.get("queue_ms", 0),
        )

    # Branch 1. The presenter switched on "saved run" mode. Skip the
    # network on purpose. There is no error, so the reason is empty.
    if cache_only:
        return from_cache("")

    # Branch 2. No key, so a live call cannot succeed. Do not even try.
    key = api_key()
    # "not key" is True when key is empty text.
    if not key:
        return from_cache("No EXA_API_KEY found in .env")

    # Headers sent with the request.
    headers = {
        # How Exa knows who is calling. This is Exa's documented header.
        "x-api-key": key,
        # Tells Exa the body is JSON.
        "Content-Type": "application/json",
    }

    # Pick the timeout. If the caller gave one, use it. Otherwise pick
    # the one that fits this search type, or 15 seconds for a type we
    # did not list (a /contents body has no type, so it gets 15).
    if timeout is None:
        timeout = TIMEOUT_BY_TYPE.get(body.get("type", "auto"), 15)

    # Where a live success will be saved: always the working folder.
    save_to = cache_path(endpoint, body, CACHE_DIR)

    # Count of retries used so far.
    attempt = 0

    # "while True" repeats until something inside returns. Each pass
    # through the loop is one attempt to reach Exa.
    while True:
        # Start a stopwatch. perf_counter is Python's most precise clock.
        started = time.perf_counter()

        try:
            # Send the request through the shared limiter.
            resp = _post(BASE_URL + endpoint, headers, body, timeout)
        # Branch 3. Exa did not answer in time.
        except requests.Timeout:
            return from_cache(f"Exa did not answer within {timeout} seconds")
        # Branch 4. Any other network failure: Wi-Fi dropped, the
        # address could not be looked up, the connection was reset.
        # RequestException is the parent of every error requests raises.
        # type(exc).__name__ is the error's name, e.g. ConnectionError.
        except requests.RequestException as exc:
            return from_cache(f"Network problem: {type(exc).__name__}")

        # Stop the stopwatch. The difference is in seconds, so multiply
        # by 1000 for milliseconds. int() drops the decimals.
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        try:
            # Turn the response text into a dictionary. Exa sends JSON
            # for errors as well as for successes.
            payload = resp.json()
        except ValueError:
            # The response was not JSON. Keep the first 200 characters
            # so the error message still has something to show.
            payload = {"error": resp.text[:200]}

        # Branch 5. Success.
        if resp.status_code == 200:
            # Exa's queue headers: did this call wait in the rate-limit
            # queue, and for how long. Header values are always text, so
            # compare with "true" and convert the number with int().
            queued = resp.headers.get("x-exa-queued") == "true"
            queue_ms = int(resp.headers.get("x-exa-queue-ms") or 0)
            # Save it first, so this answer becomes the new fallback.
            # A failed save comes back as text, never as a crash.
            write_error = _write_cache(
                save_to, endpoint, body, payload, elapsed_ms, queued, queue_ms
            )
            # Then hand it back, marked as "live".
            return _envelope(
                True, payload, body, endpoint, "live", elapsed_ms,
                queued=queued, queue_ms=queue_ms, cache_write_error=write_error,
            )

        # Branch 6. Two errors are worth trying again:
        #   429 = we sent too many requests too quickly
        #   503 = Exa is overloaded (Exa does not bill these)
        # Other errors, such as a wrong key, fail the same way every
        # time, so retrying them would only waste seconds.
        retryable = resp.status_code in (429, 503)
        if retryable and attempt < max_retries:
            # attempt += 1 is short for attempt = attempt + 1.
            attempt += 1
            # Pause, then go back to the top of the loop. The limiter
            # slot was already given back, so nobody waits on our sleep.
            time.sleep(_retry_wait(resp, attempt))
            # continue skips the rest of this pass and starts the next.
            continue

        # Branch 7. An error we cannot fix by retrying, or we ran out
        # of retries. Fall back to the saved answer and say why.
        return from_cache(_explain(resp.status_code, payload))


# ---------------------------------------------------------------------
# THE PUBLIC FUNCTIONS: what the rest of the app calls
# ---------------------------------------------------------------------

def search(body, cache_only=False, timeout=None):
    """
    POST /search: find pages on the web.

    One call can also return the page contents (text or highlights) and
    a written answer with citations, depending on what body asks for.

    Example body. This is the request Exa itself recommends: the query,
    the default type, and highlights (the most relevant passages from
    each page). Exa's own guidance is to add any other field only when
    the task needs it, and to be able to say why.
        {
            "query": "exchange notices about FIX session changes",
            "type": "auto",
            "contents": {"highlights": True},
        }
    """
    # All the real work is in call(). This wrapper exists so other code
    # reads as exa_client.search(...) and cannot mistype the path.
    return call("/search", body, cache_only=cache_only, timeout=timeout)


def contents(body, cache_only=False, timeout=None):
    """
    POST /contents: fetch text or highlights for URLs we already have.

    Note a difference from /search. On /search the options sit inside a
    "contents" object. On /contents they sit at the top level:
        {"urls": ["https://example.com/page"], "highlights": True}
    """
    return call("/contents", body, cache_only=cache_only, timeout=timeout)


# ---------------------------------------------------------------------
# SELF-CHECK: run "python exa_client.py" to test the key
# ---------------------------------------------------------------------

# __name__ equals "__main__" only when this file is run directly.
# When another file imports it, this block is skipped.
if __name__ == "__main__":
    # Say whether a key was found, without ever printing the key itself.
    print("Key found in .env:", "yes" if api_key() else "no")

    # One search, kept as cheap as possible because this is only a test
    # of the key. "instant" is the lowest-priced type, and numResults 1
    # asks for a single result. Cost: $0.004, less than half a cent.
    # A real search in the app would not set either of these.
    result = search({"query": "Exa search API", "type": "instant", "numResults": 1})

    # Print the facts that show whether the key and network work.
    print("Worked:", result["ok"])
    print("Source:", result["source"], result["saved_from"])
    print("Time  :", result["elapsed_ms"], "ms")
    print("Cost  : $", result["cost_dollars"])
    # Only print the error line when there is an error to show.
    if result["error"]:
        print("Error :", result["error"])
