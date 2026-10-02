"""
app.py - the Break Check screens, built with Streamlit.

WHAT THIS FILE DOES, IN ONE SENTENCE
  It draws the screens: the break queue, the evidence for one break side
  by side, the comparison and the drafted ticket note, a free-form row,
  and an "Under the hood" tab.

WHY IT EXISTS
  All the thinking lives in evidence.py (gather and check the evidence)
  and compare.py (decide). This file only shows things and passes the
  presenter's choices from the sidebar down to those two files. Keeping
  the screen separate means every decision can be tested without it.

HOW STREAMLIT WORKS, IN SHORT
  Streamlit runs this whole file from top to bottom every time someone
  clicks something. Anything that must survive between runs, such as
  the results of a check, is kept in st.session_state, a dictionary that
  Streamlit keeps for each browser tab.
  Why it works this way: the screen is just the result of running the
  script. There is no separate "update the screen" code to keep in step,
  which keeps the page simple. The price is that ordinary variables are
  wiped on every click, which is exactly what session_state is for.

HOW ONE CLICK FLOWS THROUGH THIS FILE
  main()
    sidebar()                 read the presenter's toggles
    tab 0: render_watchlist() the watchlist scan, "Find what our feeds
                              missed": one open search per holding, then
                              the finding, its evidence and its impact
    tab 1: render_queue()     the break queue, pick a row
           render_break_detail(row)
             button "Check"  -> run_check(): evidence.check_row, which
                                calls on_tick every half second so the
                                timer on screen counts up
                             -> compare.judge: label, vendors, note
             then draw: label, two channel columns, repair, comparison,
             ticket note
    tab 2: the live challenge (scan one name, no event named), then
           the original free-form row (same path, row built from typed input)
    tab 3: render_under_the_hood()

RUN IT
  streamlit run app\\app.py
"""

# ---------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------

# html.escape makes text from a web page safe to show inside HTML.
import html

# sys lets us add this file's folder to Python's search path, so the
# imports below work however the app is started.
import sys

# time gives the clock time for the call log.
import time

# Path builds file paths that work on any operating system.
from pathlib import Path

# sys.path is the list of folders Python searches for imports. Putting
# this file's own folder first means "import evidence" finds our file.
# Path(__file__) is this file; .resolve() makes the path complete;
# .parent is the folder it sits in (the app folder).
sys.path.insert(0, str(Path(__file__).resolve().parent))

# pandas builds the tables shown on screen.
# "# noqa: E402" tells the style checker that importing below other code
# is on purpose here: the sys.path line above has to run first.
import pandas as pd  # noqa: E402

# streamlit draws the web page. "st" is the usual short name.
import streamlit as st  # noqa: E402

# Our own three files.
# compare decides the label, evidence gathers and checks the sources,
# exa_client makes (or replays) every Exa call.
import compare  # noqa: E402
import evidence  # noqa: E402
import exa_client  # noqa: E402
# scan runs the watchlist scan: one open search per holding.
import scan  # noqa: E402

# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------

# The permanent honesty line, shown in the sidebar and on every break.
# Two texts inside round brackets, side by side, are joined into one
# by Python. That lets a long sentence span two lines of code.
MOCK_LINE = (
    "Vendor A and Vendor B values are MOCKED for this demo. "
    "Every source page is retrieved by Exa, live or from a labeled saved run."
)

# Streamlit reads text between two dollar signs as a math formula, so a line
# with two prices in it comes out garbled. Putting a backslash in front of
# the dollar sign tells Streamlit "this is a plain dollar sign, print it".
# DOLLAR holds that two-character text so the code below can reuse it.
# In Python, "\\" inside quotes is ONE backslash character.
DOLLAR = "\\$"


def money(amount):
    """Turn a number like 0.007 into the text $0.007, safe to show on screen."""
    # An f-string: the f before the quotes lets {expression} drop a value
    # straight into the text.
    # :.3f means "show three digits after the decimal point".
    return f"{DOLLAR}{amount:.3f}"


# The measured comparison from the live findings of 2026-09-29. Shown on
# the Under the hood tab next to the numbers read from the saved runs.
# The + signs glue the fixed text to the two money() results.
MEASURED_BAKEOFF_TEXT = (
    "Measured on 2026-09-29 with the real key: type auto filled every field whenever "
    "the right page was in Exa's index, in about 2 to 4 seconds wall time and " + money(0.007) + " "
    "per call. deep-lite on the same body cost " + money(0.012) + ", took about 5 seconds, and found "
    "nothing extra (CDT's alert 2026-683 was missing from the index on both that day). So auto is "
    "the default, on measured evidence."
)

# The honest limits, shown as a list on the Under the hood tab.
# Saying the limits out loud, on screen, is part of the demo: it shows
# what Exa does and does not replace.
HONEST_LIMITS = [
    "Vendor records are mocked. The sources are real and retrieved by Exa.",
    "Exa does not replace the licensed corporate-actions feeds, custodian or DTC notices, or anything behind a login.",
    "Coverage has gaps: Nasdaq alert 2026-683 (CDT) was not in Exa's index on Sep 29 (it was by Oct 2), and Exa's stored copy of 2026-677 (CTNT) is a placeholder. A forced live re-fetch of nasdaqtrader.com was flaky on Sep 29: status success with an empty page at 09:19 ET, the real alert at 09:40 ET. Code treats success with no text as a failure.",
    "For bonds, the SEC copy is usually the issuer's own release filed again, so it is same-issuer confirmation, not independent.",
    "Exa's publishedDate is an estimate. Code checks the date printed on the notice against the ticket window.",
    "Grounding confidence alone is not trusted: a 'not stated' field came back with confidence 'high'. Code treats it as missing.",
    "The model can be wrong or echo the name in the prompt, so identity is checked in code on the retrieved titles and highlights.",
    "Nothing is loaded automatically. The analyst approves every change.",
]


# ---------------------------------------------------------------------
# LOADING THE CONFIG ONCE
# ---------------------------------------------------------------------

# @st.cache_data is a "decorator": a line starting with @ placed above a
# function that wraps it with extra behaviour. This one remembers the
# function's return value, so the two JSON files are read once, not on
# every click.
# Why it matters: Streamlit reruns this whole file on every click, so
# without the cache the files would be read again each time.
@st.cache_data
def load_config():
    """Return (rows, channels, portfolio) from the data folder."""
    # Returning two values with a comma makes a tuple; main() unpacks it
    # with "rows, channels, portfolio = load_config()".
    return evidence.load_rows(), evidence.load_channels(), scan.load_portfolio()


def init_state():
    """Create the session_state entries this app uses, if missing."""
    # st.session_state is Streamlit's memory for this browser tab. Normal
    # variables are wiped on every rerun; values stored here are not.
    # setdefault adds a key only if it is not there yet, so results
    # survive from one click to the next.
    # results: each checked row's evidence and verdict, by store key.
    st.session_state.setdefault("results", {})
    # call_log: one entry per Exa call, for the Under the hood tab.
    st.session_state.setdefault("call_log", [])
    # approved: which ticket notes the analyst has approved.
    st.session_state.setdefault("approved", {})
    # free_row: the row built on the free-form tab, or None until built.
    st.session_state.setdefault("free_row", None)
    # scan_results: the watchlist scan's findings, by mode (live or saved).
    st.session_state.setdefault("scan_results", {})
    # one_scan: the finding from the live challenge, or None.
    st.session_state.setdefault("one_scan", None)


# ---------------------------------------------------------------------
# SIDEBAR: the presenter's controls
# ---------------------------------------------------------------------

def sidebar():
    """Draw the sidebar and return the presenter's settings."""
    # st.sidebar.X draws X in the panel on the left instead of the page.
    st.sidebar.header("Presenter controls")
    # A toggle is an on/off switch. key= names it in session_state.
    # It returns True or False, and because it has a key its position is
    # remembered across reruns. help= is the tooltip text.
    cache_only = st.sidebar.toggle(
        "Saved runs only", key="saved_only",
        help="Replays saved runs (cache_golden first, then cache). No network calls.",
    )
    # The drill switch: delay the market channel so the timebox is seen
    # to work for real, not faked.
    simulate = st.sidebar.toggle(
        "Simulate timeout", key="simulate",
        help=(
            "Break queue: holds the market channel back 20 seconds inside its worker thread. "
            "Watchlist scan: holds the BAC note back 40 seconds. Either way the real timebox path runs."
        ),
    )
    # A number box with up and down arrows, limited to 2 to 30 seconds,
    # starting at the default from evidence.py.
    timebox = st.sidebar.number_input(
        "Timebox seconds", min_value=2, max_value=30,
        value=evidence.DEFAULT_TIMEBOX_S, step=1, key="timebox",
    )
    # Say whether a key exists, never what it is.
    # A conditional expression: "A if test else B" picks one of two
    # values in one line.
    st.sidebar.caption("Exa key found in .env: " + ("yes" if exa_client.api_key() else "no"))
    st.sidebar.caption(MOCK_LINE)
    # Hand the three settings back as one dictionary. int() makes sure
    # the timebox is a whole number.
    return {"cache_only": cache_only, "simulate": simulate, "timebox": int(timebox)}


# ---------------------------------------------------------------------
# SCREEN 1: the break queue
# ---------------------------------------------------------------------

def render_queue(rows):
    """Draw the queue table and return the row the presenter picked."""
    # st.caption draws small grey text.
    st.caption(MOCK_LINE)
    # A tick box; it returns True when ticked.
    show_backups = st.checkbox("Show backup rows", key="show_backups")
    # Keep live-path rows, plus backups only when asked for.
    # A list comprehension with a filter: [item for item in list if test]
    # builds a new list of only the items that pass the test.
    shown = [r for r in rows if r["live_path"] or show_backups]
    # pd.DataFrame builds a table from a list of dictionaries: each
    # dictionary is one row, and its keys become the column headings.
    # The list inside is another list comprehension, one dictionary per
    # shown row.
    table = pd.DataFrame(
        [
            {
                "row": r["id"],
                # Bonds have no ticker, so fall back to the CUSIP. "a or b"
                # gives a if it has a value, otherwise b.
                "identifier": r["ticker"] or r["cusip"],
                "issuer": r["issuer_display"],
                "break": r["break_summary"],
                "field in dispute": r["field_in_dispute"],
                # Show "(blank)" rather than an empty cell, so a missing
                # vendor value is visible.
                "Vendor A (mocked)": r["vendor_a"] or "(blank)",
                "Vendor B (mocked)": r["vendor_b"] or "(blank)",
                "opened at": r["opened_at"],
            }
            for r in shown
        ]
    )
    # st.dataframe draws a pandas table as a scrollable, sortable grid.
    # hide_index=True hides pandas' row numbers, which mean nothing here.
    # width="stretch" makes it fill the page width.
    st.dataframe(table, hide_index=True, width="stretch")
    # A row of round buttons, one per row id.
    # It returns the id the presenter picked; key= keeps the pick across
    # reruns.
    picked = st.radio("Break to check", [r["id"] for r in shown], horizontal=True, key="row_pick")
    # Turn the picked id back into the full row dictionary.
    return evidence.find_row(shown, picked)


# ---------------------------------------------------------------------
# SCREEN 2: one break, in detail
# ---------------------------------------------------------------------

def render_presenter_notes(row):
    """The four things to say out loud, before and after pressing Check."""
    # The notes for this row come from data\rows.json.
    notes = row["presenter"]
    # st.expander is a fold-out box: a heading you click to open or close.
    # "with" is a with-block: everything indented under it is drawn
    # inside that box, and Streamlit closes the box when the block ends.
    # expanded=True opens it by default; the presenter can still fold it.
    # expanded=False: folded by default, so the screen leads with the
    # evidence, not with notes about coverage gaps.
    with st.expander("Presenter notes: say all four out loud", expanded=False):
        # st.markdown reads **text** as bold.
        st.markdown(f"**1. Hypothesis.** {notes['hypothesis']}")
        st.markdown(f"**2. Action.** {notes['action']}")
        st.markdown(f"**3. Expected result.** {notes['expected']}")
        st.markdown(f"**4. If it comes back different, I check next:** {notes['if_different']}")


def log_calls(row, result):
    """Add this row's calls to the call log on the Under the hood tab."""
    # all_envelopes gives every call's envelope (the package exa_client
    # returns): both searches, plus the repair if one ran.
    for env in evidence.all_envelopes(result):
        # The raw answer Exa sent back.
        data = env["data"]
        # .append adds one entry to the end of the list kept in
        # session_state, so the log grows across clicks instead of
        # being wiped on the next rerun.
        st.session_state.call_log.append(
            {
                # The clock time now, as hours:minutes:seconds.
                "time": time.strftime("%H:%M:%S"),
                "row": row["id"],
                "endpoint": env["endpoint"],
                # .get("type", "") gives the value for "type", or "" when
                # the body has no such key (the /contents call has none).
                "type": env["body"].get("type", ""),
                # "live" or "cache", plus the saved folder name in brackets
                # when it came from a saved run. The inner conditional gives
                # "" for a live call, so nothing is added.
                "source": env["source"] + (f" ({env['saved_from']})" if env["saved_from"] else ""),
                "wall ms": env["elapsed_ms"],
                # Exa's own timing. "or 0" covers a missing value, and
                # round() drops the decimals.
                "Exa searchTime ms": round(data.get("searchTime") or 0),
                # Only live calls cost money today.
                "live cost $": env["cost_dollars"] if env["source"] == "live" else 0.0,
                # Whether the call had to wait for the shared limiter.
                "queued": env["queued"],
                # Exa's id for the call, useful if support needs to look.
                "requestId": env["request_id"],
                "error": env["error"],
            }
        )


def run_check(row, settings, channels):
    """Run one row with a counting timer on screen, then judge it."""
    # st.empty() makes a placeholder: a spot on the page we can redraw.
    # Why: the timer must count up in the same spot, not print a new line
    # every half second. Each call like timer.info(...) replaces what
    # was in that spot.
    timer = st.empty()
    # A second spot, for the repair timer if a stale page is found.
    repair_timer = st.empty()

    # A function inside a function. evidence.py calls it every half
    # second; it can see "timer" and "settings" from run_check.
    # This is a "callback": we hand the function to evidence.py, and
    # evidence.py calls it back while it waits. That way evidence.py
    # never needs to know anything about Streamlit.
    def on_tick(elapsed, status):
        # A conditional expression picks the word for each channel.
        # status is a dictionary like {"issuer": True, "market": False};
        # .get returns None (counted as false) if a name is missing.
        issuer = "back" if status.get("issuer") else "waiting"
        market = "back" if status.get("market") else "waiting"
        # Redraw the placeholder as a blue info box with the new time.
        # :.1f shows one digit after the decimal point.
        timer.info(
            f"Searching: {elapsed:.1f} s of the {settings['timebox']} s timebox. "
            f"Issuer channel: {issuer}. Market channel: {market}."
        )

    # The same idea for the live re-fetch of a stale page.
    def on_repair_tick(elapsed, status):
        repair_timer.info(f"Stale page found. Live re-fetch: {elapsed:.1f} s of {evidence.REPAIR_TIMEBOX_S} s.")

    # Gather and check the evidence for this row. Named arguments
    # (name=value) make each setting clear. The two callbacks are passed
    # in by name, without brackets, so evidence.py can call them later.
    result = evidence.check_row(
        row, channels,
        timebox_s=settings["timebox"],
        on_tick=on_tick,
        cache_only=settings["cache_only"],
        simulate_timeout=settings["simulate"],
        on_repair_tick=on_repair_tick,
    )
    # Clear the timers once the answer is in.
    # .empty() on a placeholder removes whatever it was showing.
    timer.empty()
    repair_timer.empty()
    # Record the calls for the Under the hood tab.
    log_calls(row, result)
    # Keep the evidence and the code's decision together, so the caller
    # can store both in session_state in one go.
    return {"result": result, "verdict": compare.judge(result)}


def render_ops(env):
    """The badge, the ops line and the Show request panel for one call."""
    data = env["data"]
    # A coloured badge that says where the result came from: green for
    # live, amber for a saved run, red for nothing at all.
    if env["source"] == "live":
        # elapsed_ms / 1000 turns milliseconds into seconds.
        st.success(f"Live. {env['elapsed_ms'] / 1000:.1f} s")
    elif env["source"] == "cache":
        # Say why the saved run was used, if there was an error.
        reason = f" Reason: {env['error']}." if env["error"] else ""
        st.warning(f"Saved run from {env['saved_at']} ({env['saved_from']} folder).{reason}")
    else:
        st.error(f"No live result and no saved run. Reason: {env['error']}")
    # Cost: a saved run costs nothing now; show what the original cost.
    cost = env["cost_dollars"]
    # "n/a" when Exa sent no cost figure. "is not None" is used rather
    # than a plain truth test so that a real cost of 0 still prints.
    cost_text = money(cost) if cost is not None else "n/a"
    if env["source"] != "live":
        cost_text = f"{DOLLAR}0 now (original call {cost_text})"
    source_text = "live" if env["source"] == "live" else f"saved {env['saved_at']}"
    # One small grey line with every operational number, so the
    # presenter can point at timing, cost and the request id.
    st.caption(
        f"source: {source_text} | wall time: {env['elapsed_ms']} ms | "
        f"Exa searchTime: {round(data.get('searchTime') or 0)} ms | cost: {cost_text} | "
        f"requestId: {env['request_id'] or 'none'} | queued: {env['queued']} ({env['queue_ms']} ms)"
    )
    # If saving the run to disk failed, say so rather than hide it.
    if env["cache_write_error"]:
        st.caption(f"Note: {env['cache_write_error']}")
    # A fold-out box with the exact request body that was sent, so anyone
    # can see the domain list came from config and not from a model.
    with st.expander("Show request"):
        st.caption(f"POST {exa_client.BASE_URL}{env['endpoint']}")
        # st.json draws a dictionary as neat, foldable JSON.
        st.json(env["body"], expanded=True)


def _top_page(channel):
    """The page to feature: the one the verified fields cite, else the first kept."""
    # The pages that passed the identity guard.
    kept = channel["guard"]["kept"]
    # Find the first field that has a verified citation.
    cited = ""
    # .values() gives the dictionary's values (the checks), not its keys.
    for check in channel["fields"].values():
        if check["cited_url"]:
            cited = check["cited_url"]
            # break leaves the loop at once: the first one is enough.
            break
    # Prefer the kept page that the verified fields actually cite.
    for page in kept:
        if page["url"] == cited:
            return page
    # kept[0] if the list has anything, else None.
    # An empty list counts as false, so kept[0] is never tried on it.
    return kept[0] if kept else None


def render_channel_column(channel, channels):
    """One channel: badge, ops line, top page, fields, identity guard."""
    # "####" in markdown is a small heading.
    st.markdown(f"#### {channel['label']}")
    # The approved domains, joined with commas, so the audience sees the
    # search was fenced to the customer's list.
    st.caption("Approved domains: " + ", ".join(channel["allowlist"]))
    render_ops(channel["envelope"])
    # A red box if Exa's stored copy of the page is a placeholder.
    if channel["stale_url"]:
        st.error(f"Stale page: Exa's stored copy of {channel['stale_url']} is a 'Page Not Available' placeholder.")

    # The one page to feature for this channel, or None.
    page = _top_page(channel)
    if page:
        st.markdown(f"**{page['title']}**")
        # Where the page lives, what kind of source it is, and both dates.
        # Exa's publishedDate is an estimate, so the date printed on the
        # notice is shown next to it.
        st.caption(
            f"{page['url']} | {evidence.source_class(page['url'], channels)} | "
            f"Exa publishedDate (estimated): {page['published'] or 'none'} | "
            f"date printed on notice: {channel['fields']['source_notice_date']['value'] or 'none'}"
        )
        # The first highlight, capped at 700 characters. st.text shows it
        # as plain text, so stray symbols are not read as formatting.
        # [0] is the first highlight; [:700] is a slice, the first 700
        # characters.
        if page["highlights"]:
            st.text(page["highlights"][0][:700])
    else:
        st.info("No page passed the identity guard.")

    # The field table: one row per field, with its value, the code's
    # status, Exa's confidence, the citation and the reason.
    # .items() gives (key, value) pairs; "for name, check in ..." is
    # tuple unpacking, putting the key in name and the value in check.
    table = pd.DataFrame(
        [
            {
                "field": name,
                "value": check["value"],
                # The status set by code: verified, missing or unverified.
                "status": check["status"],
                # Shown for honesty, but never trusted on its own: a
                # "not stated" value once came back with confidence "high",
                # so code marks it missing whatever the confidence says.
                "Exa confidence": check["confidence"],
                # The verified link, or else every cited link, cut to 120
                # characters so the table stays readable.
                "citation": check["cited_url"] or ", ".join(check["citations"])[:120],
                "why": check["reason"],
            }
            for name, check in channel["fields"].items()
        ]
    )
    st.dataframe(table, hide_index=True, width="stretch")

    # The identity guard's three piles, with counts in the heading.
    # len() gives the number of items in a list.
    guard = channel["guard"]
    title = f"Identity guard: {len(guard['kept'])} kept, {len(guard['amber'])} amber, {len(guard['dropped'])} dropped"
    with st.expander(title):
        # One grey line per page, pile by pile, with the reason code gave.
        for group in ("kept", "amber", "dropped"):
            for item in guard[group]:
                # .upper() gives "KEPT"; [:90] cuts long titles.
                st.caption(f"{group.upper()}: {item['title'][:90]} | {item['url']} | {item['reason']}")


def render_repair(repair):
    """The stale-page repair: its call, and whether it worked."""
    st.markdown("#### Stale-page repair: one live re-fetch through /contents")
    # The same badge and ops line as a search.
    render_ops(repair["envelope"])
    if repair["ok"]:
        # It worked, but it is still one source, so the analyst confirms.
        st.success(f"Re-fetch worked: {repair['reason']}. One repaired source; the analyst confirms.")
        # The start of the fresh page text, as plain text.
        st.text(repair["text"][:700])
    else:
        st.error(f"Re-fetch did not repair the page: {repair['reason']}")


def render_label(verdict):
    """The one label for the row, its reason and any notes."""
    # The label chosen by compare.py: code, words, colour and reason.
    label = verdict["label"]
    text = f"{label['label']}"
    # Pick the coloured box that matches the label's colour.
    # success is green, warning is amber, error is red.
    if label["colour"] == "green":
        st.success(text)
    elif label["colour"] == "amber":
        st.warning(text)
    else:
        st.error(text)
    # st.write shows plain text (or almost anything else) on the page.
    st.write("Why: " + label["reason"])
    # Any "legal date versus first trading day" notes, each in a blue box.
    for note in label["notes"]:
        st.info(note)


def render_comparison(verdict, row):
    """The comparison table: issuer, market, verdict, and the vendors."""
    st.markdown("#### Comparison (plain code, no model)")
    # One table row per compared field. When a side has no usable value,
    # show its status in brackets instead, such as "(missing)", so the
    # audience sees why that cell is empty.
    table = pd.DataFrame(
        [
            {
                "field": c["field"],
                "issuer (normalized)": c["issuer"] or f"({c['issuer_status']})",
                "market (normalized)": c["market"] or f"({c['market_status']})",
                "verdict": c["verdict"],
            }
            for c in verdict["comparisons"]
        ]
    )
    st.dataframe(table, hide_index=True, width="stretch")
    # The vendor check from compare.py.
    vendors = verdict["vendors"]
    # The disputed field, in bold, and its settled value.
    st.markdown(
        f"**Field in dispute: {vendors['field']}.** Settled value: {vendors['resolved'] or 'not settled'} "
        f"(from {vendors['basis']})."
    )
    # Each vendor's value and whether it matches the evidence.
    st.write(f"Vendor A (mocked) {vendors['vendor_a']['raw'] or '(blank)'}: {vendors['vendor_a']['status']}.")
    st.write(f"Vendor B (mocked) {vendors['vendor_b']['raw'] or '(blank)'}: {vendors['vendor_b']['status']}.")


def render_ticket_note(note, store_key):
    """The drafted note, with a copy button and an Approve button."""
    st.markdown("#### Ticket note (drafted by code)")
    # st.code shows text in a box with a built-in copy button.
    # language=None means no colour highlighting, since it is not code.
    st.code(note, language=None)
    # st.button draws a button and returns True only on the one rerun
    # that the click causes; on every other run it returns False. So the
    # approval is saved in session_state, where it outlives that run.
    # key= must be unique on the page, so it includes the store key.
    if st.button("Approve", key=f"approve_{store_key}"):
        st.session_state.approved[store_key] = True
    # .get returns None (false) until this note has been approved.
    if st.session_state.approved.get(store_key):
        st.success("Approved by the analyst. In production this writes the note to the ticket; in this demo nothing is sent.")


def render_queue_trace(result, verdict, store_key):
    """The break queue's evidence, as three stages: passage, fields, action."""
    st.markdown("#### Evidence: source passage, extracted fields, proposed action")
    channels_checked = result["channels"]
    # Pick which source to trace. format_func shows the channel's heading.
    channel_key = st.radio(
        "Source to trace", ["issuer", "market"], horizontal=True,
        format_func=lambda c: channels_checked[c]["label"], key=f"qtrace_ch_{store_key}",
    )
    channel = channels_checked[channel_key]
    # Only fields with a value can be traced to a passage.
    fields = [f for f, c in channel["fields"].items() if c["status"] != "missing"]
    if not fields:
        st.info("This source gave no fields to trace.")
        return
    field = st.radio("Field to trace", fields, horizontal=True, key=f"qtrace_f_{store_key}_{channel_key}")
    # scan.supporting_passage reads "checks" and "envelope", so hand it
    # this channel's field checks and envelope under those names.
    support = scan.supporting_passage({"checks": channel["fields"], "envelope": channel["envelope"]}, field)
    left, middle, right = st.columns([5, 4, 3])
    with left:
        st.markdown("**1. Source passage**")
        if support["passage"]:
            st.markdown(marked_passage(support["passage"], support["match"]), unsafe_allow_html=True)
        else:
            st.info("No passage for this field.")
        if support["url"]:
            st.markdown(f"Citation: [{support['url'][:90]}]({support['url']})")
    with middle:
        st.markdown("**2. Extracted fields**")
        st.dataframe(
            pd.DataFrame(
                [{"traced": "->" if n == field else "", "field": n, "value": c["value"], "status (code)": c["status"]}
                 for n, c in channel["fields"].items()]
            ),
            hide_index=True, width="stretch",
        )
    with right:
        st.markdown("**3. Proposed action**")
        st.write(verdict["label"]["label"] + ".")
        vendors = verdict["vendors"]
        st.write(f"{vendors['field']}: settled value {vendors['resolved'] or 'not settled'}. The analyst approves the ticket note below.")
        st.caption(scan.INDEPENDENCE_RULE)


def render_break_detail(row, settings, channels, key_prefix):
    """Screen 2: everything about one break."""
    # The heading, the one-line break summary and the honesty line.
    st.subheader(f"{row['id']}: {row['issuer_display']}")
    st.write(row["break_summary"])
    st.caption(MOCK_LINE)
    render_presenter_notes(row)

    # One stored result per row and per mode, so live and saved runs of
    # the same row do not overwrite each other.
    mode = "saved" if settings["cache_only"] else "live"
    # key_prefix is "queue" or "free", so the two tabs never share a
    # result either. Example key: "queue:CDT:live".
    store_key = f"{key_prefix}:{row['id']}:{mode}"
    # The Check button. The click makes Streamlit rerun the whole file;
    # on that one run st.button returns True, so the check runs and its
    # result is saved in session_state. type="primary" colours it.
    if st.button(f"Check {row['id']}", key=f"check_{key_prefix}_{row['id']}", type="primary"):
        st.session_state.results[store_key] = run_check(row, settings, channels)

    # Read the saved result back. On later reruns (for example after
    # clicking Approve) the button returns False, but the result is still
    # here, so the screen does not go blank and no money is spent again.
    checked = st.session_state.results.get(store_key)
    # Not checked yet: show a hint and stop drawing this screen.
    if checked is None:
        st.info("Press Check to search both channels.")
        return
    result = checked["result"]
    verdict = checked["verdict"]

    render_label(verdict)
    # The evidence as a visible transformation, before the raw columns.
    render_queue_trace(result, verdict, store_key)
    # Timing and spend for the whole row.
    st.caption(
        f"Row wall time: {result['wall_ms']} ms (searches {result['search_wall_ms']} ms). "
        f"Live spend for this row: {money(result['cost_live'])}"
    )
    # Two columns side by side. "with" puts what follows inside a column.
    # st.columns(2) returns two column objects; tuple unpacking names
    # them left and right.
    left, right = st.columns(2)
    # Issuer on the left, market on the right, so the two sources can be
    # read side by side.
    with left:
        render_channel_column(result["channels"]["issuer"], channels)
    with right:
        render_channel_column(result["channels"]["market"], channels)
    # The repair section only appears when a stale page was re-fetched.
    if result["repair"]:
        render_repair(result["repair"])
    render_comparison(verdict, row)
    render_ticket_note(verdict["note"], store_key)


# ---------------------------------------------------------------------
# SCREEN 0: the watchlist scan, "Find what our feeds missed"
# ---------------------------------------------------------------------

# The honesty line for the scan, shown above every scan result.
SCAN_NOTE = (
    "Vendor records, holdings and open orders are simulated. "
    "The announcements are real and retrieved by Exa."
)

# Friendly names for the seven scan fields, used on the field picker.
FIELD_NAMES = {
    "event_type": "Event type",
    "terms": "Terms",
    "effective_as_stated": "Effective date as stated",
    "effective_date": "Effective date (first trading day)",
    "new_identifier": "New identifier",
    "identifier_in_source": "Identifier in source",
    "source_notice_date": "Notice date",
}


def describe_vendor(record):
    """One short line for a mocked vendor record, or "(no record)"."""
    # None, or an empty dictionary, both count as "no record".
    if not record:
        return "(no record)"
    # Only the parts that have a value, joined with commas.
    parts = [record.get("event_type"), record.get("terms"), record.get("effective_date"), record.get("new_identifier")]
    return ", ".join(p for p in parts if p)


def describe_holding(security):
    """The holding as text: shares for a stock, par for a bond."""
    holding = security.get("holding") or {}
    # :, adds thousands separators, as in 10,000.
    if "shares" in holding:
        return f"{holding['shares']:,} shares"
    if "par" in holding:
        return f"{holding['par']:,} par"
    return "not held"


def show_status(status, note=""):
    """Draw a finding status in a coloured box that fits its meaning."""
    text = status + (f". {note}" if note else "")
    # The payoff, an event neither feed has, is red: it needs work today.
    if status == scan.ABSENT_BOTH:
        st.error(text)
    # One vendor only: amber, the other feed needs a fix.
    elif status == scan.ONE_VENDOR:
        st.warning(text)
    # Both vendors have it: green, at most a field to reconcile.
    elif status == scan.BOTH_VENDORS:
        st.success(text)
    # Nothing found, or a typed name: blue, for information.
    else:
        st.info(text)


def marked_passage(passage, match):
    """
    Return the passage as safe HTML, with the supporting value marked.

    html.escape turns characters like < and & into codes, so text from a
    web page can never be read as HTML or script by the browser.
    """
    safe = html.escape(passage)
    if match:
        target = html.escape(match)
        # Replace only the first time the value appears (the 1 at the end).
        safe = safe.replace(target, f"<mark>{target}</mark>", 1)
    # Streamlit reads text between two dollar signs as math, so each
    # dollar sign becomes its HTML code, which still shows as a dollar.
    safe = safe.replace("$", "&#36;")
    # A box with a line on the left, keeping the page's line breaks.
    return (
        "<div style='border-left:4px solid #f0b429;padding:8px 12px;"
        "white-space:pre-wrap;font-size:0.9rem;max-height:340px;overflow-y:auto'>"
        f"{safe}</div>"
    )


def log_scan_calls(findings):
    """Add the scan's calls to the call log on the Under the hood tab."""
    for finding in findings:
        env = finding["envelope"]
        # The same columns as log_calls above, so one table holds both.
        st.session_state.call_log.append(
            {
                "time": time.strftime("%H:%M:%S"),
                "row": "scan " + finding["security"]["id"],
                "endpoint": env["endpoint"],
                "type": env["body"].get("type", ""),
                "source": env["source"] + (f" ({env['saved_from']})" if env["saved_from"] else ""),
                "wall ms": env["elapsed_ms"],
                "Exa searchTime ms": round(env["data"].get("searchTime") or 0),
                "live cost $": finding["cost_live"],
                "queued": env["queued"],
                "requestId": env["request_id"],
                "error": env["error"],
            }
        )


def run_watchlist_scan(portfolio, settings):
    """Run the scan with a per-security progress line, then return findings."""
    securities = portfolio["securities"]
    # One placeholder that is redrawn every half second.
    progress = st.empty()

    # A callback: scan.py calls it every half second while it waits.
    def on_tick(elapsed, status):
        # One line per security: "back" once its answer is in.
        # A list comprehension builds one markdown bullet per security.
        lines = [f"- {sid}: {'back' if done else 'searching'}" for sid, done in status.items()]
        # Count the securities that are back. True counts as 1.
        done_count = sum(1 for done in status.values() if done)
        progress.markdown(
            f"**Scanning {len(status)} securities: {done_count} back, {elapsed:.1f} s.**\n" + "\n".join(lines)
        )

    findings = scan.run_scan(
        securities, portfolio,
        cache_only=settings["cache_only"],
        simulate_timeout=settings["simulate"],
        on_tick=on_tick,
    )
    # Clear the progress line once every answer is in.
    progress.empty()
    log_scan_calls(findings)
    return findings


def rank_findings(findings):
    """The findings sorted payoff first, then in watchlist order."""
    # enumerate gives (position, item) pairs; we keep each id's position.
    order = {f["security"]["id"]: i for i, f in enumerate(findings)}
    # The sort key is a pair: the status's place in STATUS_ORDER, then
    # the watchlist position. Pairs sort by the first item, then the second.
    return sorted(findings, key=lambda f: (scan.STATUS_ORDER.index(f["status"]), order[f["security"]["id"]]))


def render_findings_table(ranked):
    """The scan results, one line per security, the payoff first."""
    lines = []
    for f in ranked:
        event = f["event"]
        # The first verified citation is the link to show.
        link = next((c["cited_url"] for c in f["checks"].values() if c["cited_url"]), "")
        lines.append(
            {
                "Security": f["security"]["id"],
                "Holding (mocked)": describe_holding(f["security"]),
                # The event in one short phrase, or "none" when not found.
                "Event found": (
                    f"{f['event_family']} {compare.normalize_terms(event['terms']) or event['terms']}, effective {event['effective_date']}"
                    if event else "none"
                ),
                "Finding status": f["status"],
                "Sources": f["sources"]["label"] if event else "",
                "Link": link,
                "Wall time s": round(f["wall_ms"] / 1000, 1),
                # A saved run costs nothing now.
                "Live cost $": f["cost_live"],
            }
        )
    # column_config tells Streamlit how to draw a column. LinkColumn
    # makes each web address clickable.
    st.dataframe(
        pd.DataFrame(lines), hide_index=True, width="stretch",
        column_config={"Link": st.column_config.LinkColumn("Link")},
    )


def render_impact(finding):
    """What the analyst sees next. Mocked, local, never sent to Exa."""
    impact = finding["impact"]
    st.markdown("#### What the analyst sees next")
    # A bordered box groups the panel visually.
    with st.container(border=True):
        st.markdown(f"**{impact['headline']}**")
        for line in impact["lines"]:
            st.markdown(f"- {line}")
        # A bond redemption carries a firm warning: never mark redeemed.
        if impact["warning"]:
            st.warning(impact["warning"])
        # The named open question, if the evidence is incomplete.
        if impact.get("incomplete"):
            st.warning(impact["incomplete"])
        st.markdown(f"**Proposed action:** {impact['action']}")
        st.caption("Holdings and orders are mocked and stay on this laptop. Only the issuer and identifier go to Exa.")


def render_evidence_stages(finding, key):
    """The three stages side by side: passage, fields, proposed action."""
    st.markdown("#### Evidence: source passage, extracted fields, proposed action")
    # Only fields with a value can be traced to a passage.
    traceable = [f for f in scan.SCAN_FIELDS if finding["checks"][f]["status"] != "missing"] or scan.SCAN_FIELDS
    # A horizontal radio: one round button per field. format_func shows
    # the friendly name while the code keeps the field's key.
    field = st.radio(
        "Field to trace", traceable, horizontal=True,
        format_func=lambda f: FIELD_NAMES[f], key=f"trace_{key}",
    )
    check = finding["checks"][field]
    support = scan.supporting_passage(finding, field)
    # Three columns; the numbers are their relative widths.
    left, middle, right = st.columns([5, 4, 3])
    with left:
        st.markdown("**1. Source passage**")
        if support["passage"]:
            st.caption(support["title"][:120])
            # unsafe_allow_html=True lets our own HTML through. Safe here
            # because marked_passage escaped the page text first.
            st.markdown(marked_passage(support["passage"], support["match"]), unsafe_allow_html=True)
            if not support["match"]:
                st.caption("The value is not printed word for word in this passage; open the link to confirm.")
        else:
            st.info("No passage for this field.")
        if support["url"]:
            st.markdown(f"Citation: [{support['url'][:90]}]({support['url']})")
            st.caption(
                f"Source kind: {scan.source_kind(support['url'])} | "
                f"Exa confidence: {check['confidence'] or 'n/a'} (shown, not trusted on its own)"
            )
    with middle:
        st.markdown("**2. Extracted fields**")
        table = pd.DataFrame(
            [
                {
                    # An arrow marks the field being traced.
                    "traced": "->" if name == field else "",
                    "field": FIELD_NAMES[name],
                    "value": c["value"],
                    "status (code)": c["status"],
                }
                for name, c in finding["checks"].items()
            ]
        )
        st.dataframe(table, hide_index=True, width="stretch")
    with right:
        st.markdown("**3. Proposed action**")
        st.write(scan.proposed_action_line(finding))
        st.markdown(f"**Sources:** {finding['sources']['label']}.")
        st.caption(scan.INDEPENDENCE_RULE)


def render_finding(finding, key):
    """Everything about one finding."""
    security = finding["security"]
    st.subheader(f"{security['id']}: {security['issuer']}")
    show_status(finding["status"], finding["vendors"]["note"])
    # Where a vendor has the event but a field disagrees, list it.
    for difference in finding["vendors"]["differences"]:
        st.markdown(f"- {difference}")
    if finding["off_target"]:
        st.caption(finding["off_target"])
    # A short line on where the answer came from: live or a saved run.
    env = finding["envelope"]
    if env["source"] == "live":
        st.caption(f"Live from Exa. {env['elapsed_ms'] / 1000:.1f} s, {money(finding['cost_live'])}.")
    elif env["source"] == "cache":
        st.caption(f"Saved run from {env['saved_at']} ({env['saved_from']} folder). {env['error']}")
    else:
        st.error(f"No live result and no saved run. {env['error']}")
    # The evidence stages only make sense when an event was found.
    if finding["event"]:
        render_evidence_stages(finding, key)
    render_impact(finding)
    # The raw request stays available, folded away.
    with st.expander("Show request"):
        st.caption(f"POST {exa_client.BASE_URL}/search")
        st.json(finding["body"], expanded=True)
    guard = finding["guard"]
    with st.expander(f"Identity guard: {len(guard['kept'])} kept, {len(guard['amber'])} amber, {len(guard['dropped'])} dropped"):
        for group in ("kept", "amber", "dropped"):
            for item in guard[group]:
                st.caption(f"{group.upper()}: {item['title'][:90]} | {item['url']} | {item['reason']}")


def render_watchlist(settings, portfolio):
    """Screen 0: scan the watchlist and open one finding."""
    st.subheader("Find what our feeds missed")
    st.info(SCAN_NOTE)
    st.caption(
        "One Exa search per security. The query never names the event: it asks for any recent "
        f"corporate action by that issuer. {portfolio['scan_window_note']}"
    )
    # The watchlist, with both mocked vendor records, before the scan.
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Security": s["id"],
                    "Issuer": s["issuer"],
                    "Holding (mocked)": describe_holding(s),
                    "Vendor A record (mocked)": describe_vendor(s.get("vendor_a")),
                    "Vendor B record (mocked)": describe_vendor(s.get("vendor_b")),
                }
                for s in portfolio["securities"]
            ]
        ),
        hide_index=True, width="stretch",
    )
    # One stored scan per mode, so live and saved runs do not mix.
    mode = "saved" if settings["cache_only"] else "live"
    if st.button("Scan watchlist", key="scan_watchlist", type="primary"):
        st.session_state.scan_results[mode] = run_watchlist_scan(portfolio, settings)
    findings = st.session_state.scan_results.get(mode)
    if not findings:
        st.caption("Press Scan watchlist to search every security at once.")
        return
    # A row of counters, one per status. st.metric draws a big number.
    statuses = [scan.ABSENT_BOTH, scan.ONE_VENDOR, scan.BOTH_VENDORS, scan.NOTHING_FOUND]
    # zip pairs each column with one status.
    for column, status in zip(st.columns(4), statuses):
        column.metric(status, sum(1 for f in findings if f["status"] == status))
    total_cost = sum(f["cost_live"] for f in findings)
    st.caption(f"Scan wall time: {findings[0]['scan_wall_ms'] / 1000:.1f} s. Live spend: {money(total_cost)}.")
    ranked = rank_findings(findings)
    render_findings_table(ranked)
    # Pick one finding to open; the payoff is first in the list.
    ids = [f["security"]["id"] for f in ranked]
    statuses_by_id = {f["security"]["id"]: f["status"] for f in ranked}
    picked = st.selectbox(
        "Open a finding", ids, key="finding_pick",
        format_func=lambda i: f"{i}: {statuses_by_id[i]}",
    )
    finding = next(f for f in ranked if f["security"]["id"] == picked)
    render_finding(finding, f"watch_{mode}_{picked}")


# ---------------------------------------------------------------------
# THE LIVE CHALLENGE: scan one name, no event named
# ---------------------------------------------------------------------

def render_live_challenge(settings, portfolio):
    """Scan one issuer picked from the watchlist or typed in."""
    st.subheader("Live challenge: scan one name")
    st.caption("Pick an issuer or type a name or ticker. No event is named; the same scan runs for that one name.")
    how = st.radio("Choose the name", ["Pick from the watchlist", "Type an issuer name or ticker"],
                   horizontal=True, key="challenge_how")
    if how == "Pick from the watchlist":
        picked = st.selectbox("Watchlist security", [s["id"] for s in portfolio["securities"]], key="challenge_pick")
        typed_text = ""
    else:
        picked = ""
        typed_text = st.text_input("Issuer name or ticker", key="challenge_text")
    if st.button("Scan this name", key="challenge_scan", type="primary"):
        security, typed = None, False
        if picked:
            security = scan.find_security(portfolio, picked)
        elif typed_text.strip():
            # A watchlist ticker typed by hand still gets its vendor records.
            security, typed = scan.typed_security(typed_text, portfolio)
        else:
            st.error("Type an issuer name or ticker first.")
        if security:
            # st.spinner shows a turning wheel while the block runs.
            with st.spinner(f"Scanning {security['id']}..."):
                finding = scan.scan_one(security, portfolio, cache_only=settings["cache_only"], typed=typed)
            log_scan_calls([finding])
            st.session_state.one_scan = finding
    finding = st.session_state.one_scan
    if finding:
        if finding["event"] is None:
            st.info("Nothing found. Not proof nothing happened.")
        render_finding(finding, "challenge")


# ---------------------------------------------------------------------
# THE FREE-FORM ROW
# ---------------------------------------------------------------------

def render_free_form(settings, channels):
    """A row built from typed input, run through the same path."""
    st.caption("Type a security. The app builds both request bodies from channels.json and runs the same checks.")
    # The asset class settings, such as nasdaq_equity.
    classes = channels["asset_classes"]
    # st.form groups inputs so nothing runs until the submit button.
    # Without a form, every keystroke in a text box would rerun the file.
    with st.form("free_form"):
        # Text boxes; each returns what was typed, as text.
        identifier = st.text_input("Ticker or CUSIP", key="ff_id")
        issuer = st.text_input("Issuer name, as it appears in releases", key="ff_issuer")
        # A drop-down list of the event types from channels.json.
        event = st.selectbox("Event type", channels["event_choices"], key="ff_event")
        # format_func shows the friendly label while keeping the key.
        # list(classes) is the dictionary's keys. "lambda k: ..." is a
        # tiny unnamed function: given a key k, return its label. It is
        # a callback that Streamlit calls once per option to get the
        # words to show.
        asset_class = st.selectbox(
            "Asset class", list(classes), format_func=lambda k: classes[k]["label"], key="ff_class"
        )
        # Only the key fields can be disputed. index=1 starts on the
        # second one, market_effective_date (counting starts at 0).
        field = st.selectbox("Field in dispute", compare.KEY_FIELDS, index=1, key="ff_field")
        vendor_a = st.text_input("Vendor A value (optional, mocked)", key="ff_va")
        vendor_b = st.text_input("Vendor B value (optional, mocked)", key="ff_vb")
        # The form's own button; True on the run after it is clicked.
        submitted = st.form_submit_button("Build row")
    if submitted:
        # .strip() removes spaces, so a box with only spaces counts as
        # empty. Both boxes are required.
        if not identifier.strip() or not issuer.strip():
            st.error("Type both a ticker or CUSIP and an issuer name.")
        else:
            # Build the row in evidence.py, from the approved config, and
            # keep it in session_state so it survives the next click
            # (such as pressing Check).
            st.session_state.free_row = evidence.make_free_form_row(
                identifier, issuer, event, asset_class, channels, field, vendor_a, vendor_b
            )
    # Once a row exists, show it with the same detail screen as the queue.
    if st.session_state.free_row:
        render_break_detail(st.session_state.free_row, settings, channels, "free")


# ---------------------------------------------------------------------
# SCREEN 3: under the hood
# ---------------------------------------------------------------------

def render_bakeoff(rows, channels):
    """auto versus deep-lite on the identical CDT market body."""
    st.markdown("#### auto versus deep-lite (identical body except type)")
    st.write(MEASURED_BAKEOFF_TEXT)
    # The CDT row is the one both types were measured on.
    row = evidence.find_row(rows, "CDT")
    # One dictionary per search type goes into this list.
    lines = []
    for search_type in ("auto", "deep-lite"):
        # The same market body, with only "type" changed.
        body = evidence.build_search_body(row, "market", channels, type_override=search_type)
        # Read the saved run only. This table never spends money.
        env = exa_client.search(body, cache_only=True)
        # The eight fields Exa filled in that saved run.
        fields = evidence.read_fields(env["data"])
        # Count the fields that have a real value.
        filled = sum(1 for v in fields.values() if not evidence.is_missing(v))
        lines.append(
            {
                "type": search_type,
                "saved run": env["saved_at"] or "none",
                "wall ms": env["elapsed_ms"],
                "Exa searchTime ms": round(env["data"].get("searchTime") or 0),
                "cost $": env["cost_dollars"],
                "fields filled (of 8)": filled,
            }
        )
    # Turn the list into a table and draw it.
    st.dataframe(pd.DataFrame(lines), hide_index=True, width="stretch")


def render_call_log():
    """Every call made in this browser session."""
    st.markdown("#### Call log (this session)")
    # The log kept in session_state, so it holds every click's calls.
    log = st.session_state.call_log
    # An empty list is false: nothing to show yet.
    if not log:
        st.caption("No calls yet.")
        return
    table = pd.DataFrame(log)
    st.dataframe(table, hide_index=True, width="stretch")
    # table['live cost $'] is one column; .sum() adds it up.
    st.caption(f"Calls: {len(log)}. Live spend: {money(table['live cost $'].sum())}.")


# The probe behind the watchlist scan's domain setting, 2026-10-02.
SCAN_PROBE_TEXT = (
    "Watchlist scan, probed on 2026-10-02 (17 calls, about " + money(0.12) + "). With the approved list "
    "(the four wires, nasdaqtrader.com, sec.gov and the issuer newsrooms), all 8 event names came back "
    "with the right event, and Microsoft and Procter & Gamble came back 'none found'. With no domain "
    "list, the same events came back, but mostly through syndicators (stocktitan, finviz, Yahoo, "
    "publicnow), and Procter & Gamble came back as a 'redemption' of its 3.250% notes from a Form 25 "
    "on stocktitan: a debt delisting, not an action on the held shares. So the scan uses the approved list."
)


def render_under_the_hood(rows, channels):
    """Screen 3: the bake-off, call log, Monitor body and limits."""
    st.markdown("#### Watchlist scan: approved domain list or open web")
    st.write(SCAN_PROBE_TEXT)
    render_bakeoff(rows, channels)
    render_call_log()
    # A Monitor is Exa's feature for watching the web on a schedule.
    # Its body is built and shown, but never sent.
    st.markdown("#### Production early warning: Exa Monitor body (shown, never run)")
    st.caption(
        "Never sent from this app. Monitors are not covered by zero data retention and need a public "
        "HTTPS webhook. Under zero data retention the same watch runs as a daily scheduled /search."
    )
    # expanded=False starts the JSON folded up.
    st.json(evidence.build_monitor_body(evidence.find_row(rows, "BAC"), channels), expanded=False)
    st.markdown("#### Honest limits")
    # One markdown bullet ("- ") per limit.
    for limit in HONEST_LIMITS:
        st.markdown(f"- {limit}")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    """Draw the whole page."""
    # Page title in the browser tab, and a wide layout so two columns
    # fit side by side. It runs first, before anything is drawn.
    st.set_page_config(page_title="Break Check", layout="wide")
    # Make sure the session_state entries exist before anything uses them.
    init_state()
    # Tuple unpacking: load_config returns two values; name them both.
    rows, channels, portfolio = load_config()
    # Draw the sidebar and get the presenter's settings.
    settings = sidebar()
    st.title("Break Check")
    st.caption("Exa finds the corporate actions our vendor feeds missed. Code checks every field against its source and proposes the work.")
    # Four tabs. Everything inside "with tab:" is drawn on that tab.
    # st.tabs returns one object per tab name, unpacked into four names.
    # Note: Streamlit draws all four tabs on every run; clicking a tab
    # only changes which one is visible.
    watch_tab, queue_tab, free_tab, hood_tab = st.tabs(["Watchlist scan", "Break queue", "Free-form row", "Under the hood"])
    with watch_tab:
        render_watchlist(settings, portfolio)
    with queue_tab:
        row = render_queue(rows)
        # find_row returns None if nothing is picked, so check first.
        if row:
            render_break_detail(row, settings, channels, "queue")
    with free_tab:
        render_live_challenge(settings, portfolio)
        st.divider()
        # The original free-form row, where an event IS named, is kept
        # behind a toggle so the tab leads with the open scan.
        if st.toggle("Check a named event (the original free-form row)", key="show_old_free"):
            render_free_form(settings, channels)
    with hood_tab:
        render_under_the_hood(rows, channels)


# Streamlit runs this file as a script, so call main() at the bottom.
# That is also why it reruns everything on each click: it simply runs
# the file again, and this line starts the drawing each time.
main()
