"""
compare.py - decides, in plain code, what the evidence says.

WHAT THIS FILE DOES, IN ONE SENTENCE
  It takes the checked evidence from evidence.py, puts every value into
  one standard form, compares the issuer's source with the market's
  source and with both vendors, gives the row one label, and drafts the
  ticket note.

WHY IT EXISTS
  The decision must be explainable line by line and must never change
  from one run to the next. So no model is used anywhere in this file:
  only fixed rules that a person can read.

WHY VALUES ARE "NORMALIZED" FIRST
  Two sources often print the same fact differently:
    "68270C 202"          and  "68270C202"            (same CUSIP)
    "one-for-ten (1-10)"  and  "1-for-10"             (same ratio)
    "Tuesday, September 29, 2026" and "2026-09-29"    (same date)
  Normalizing means turning each into one standard form, so a simple
  equality test (==) gives the right answer.

HOW ONE ROW FLOWS THROUGH THIS FILE
  judge(result)
    1. compare_sources   field by field: agree, differ, one side only
    2. row_label         one label for the whole row, with the reason
    3. vendor_check      which vendor matches the evidence
    4. draft_ticket_note the resolution note, with the links
  <- one dictionary for the screen

THE LABELS
  CORROBORATED    two independent sources agree
  SAME_ISSUER     both agree, but the "market" copy is an SEC filing of
                  the issuer's own release, so it is not independent
  SINGLE_ISSUER   only the issuer's own announcement is usable
  SINGLE_MARKET   only the exchange's or SEC's notice is usable
  CONFLICT        the two sources disagree on a key field
  STALE_REPAIRED  the only source is a re-fetched stale page
  NOT_CONFIRMED   nothing usable: route to the analyst, with the reason

WHY THE LABEL IS DECIDED BY CODE AND NOT BY A MODEL
  A model can give a different answer to the same input on another run,
  and it cannot show its working. A reconciliation desk needs the same
  answer every time and a reason an auditor can read. So the model only
  fetches and fills fields upstream; every judgement is made here.
"""

# ---------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------

# re is Python's regular expressions module, for finding patterns such
# as dates and ratios inside free text.
import re

# datetime.date checks that a date really exists (no February 30th)
# and prints it in the standard YYYY-MM-DD form.
from datetime import date

# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------

# The fields that decide the row. Each feeds one rule below.
# A list in square brackets keeps its order, so the table always shows
# the fields in this same order.
KEY_FIELDS = ["terms", "market_effective_date", "new_cusip"]

# The fields shown in the comparison table: the key fields plus two for
# context (the effective time as written, and the date on the notice).
# Adding two lists with + makes one new, longer list.
SHOWN_FIELDS = KEY_FIELDS + ["effective_as_stated", "source_notice_date"]

# Month names and short forms, mapped to their number. "sept" is here
# because press releases often write "Sept. 25".
# Curly brackets with key: value pairs make a dictionary, a lookup
# table: MONTHS["oct"] gives 10.
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Number words that appear in split ratios, such as "one-for-ten".
# Only the words we have actually seen in notices are listed. A word
# that is not here simply finds no match, which is the safe outcome.
WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
    "fifteen": 15, "twenty": 20, "twenty-five": 25, "twenty five": 25, "thirty": 30,
    "forty": 40, "fifty": 50, "one hundred": 100, "one hundred fifty": 150,
    "two hundred": 200,
}

# Words that mean "no value". Same list as in evidence.py.
# Curly brackets with no colons make a set: a bag of values with no
# order, built for a fast "is this word in the bag?" test.
MISSING_WORDS = {"", "not stated", "none", "n/a", "na", "null", "unknown", "not available"}

# The plain-English label and screen colour for each label code.
# Each value is a tuple: two items in round brackets that travel
# together, here (the words shown, the colour of the box).
# The code (left) is what the rules below use; the words (right) are
# only for people, so the wording can change without breaking a rule.
LABELS = {
    "CORROBORATED": ("Corroborated by two independent sources", "green"),
    "SAME_ISSUER": ("Same-issuer confirmation (the SEC copy is the issuer's own release)", "amber"),
    "SINGLE_ISSUER": ("Single source, issuer only", "amber"),
    "SINGLE_MARKET": ("Single source, exchange or SEC only", "amber"),
    "CONFLICT": ("Conflict between sources, escalate", "red"),
    "STALE_REPAIRED": ("Stale source repaired, one source, analyst confirms", "amber"),
    "NOT_CONFIRMED": ("Not confirmed, route to analyst", "red"),
}


# ---------------------------------------------------------------------
# NORMALIZING VALUES
# ---------------------------------------------------------------------

def _missing(text):
    """True if the value means "not given"."""
    # The leading underscore in the name says "used only inside this
    # file". Python does not enforce it; it is a note to other people.
    # Three tests joined by "or": the value is None (nothing at all), or
    # its tidied text is one of the missing words, or it starts with
    # "not stated" (the model sometimes adds more, such as "not stated
    # in the release"). str() turns any value into text, .strip() drops
    # spaces at both ends, .lower() makes it lower case.
    # This check ignores Exa's confidence on purpose: a "not stated"
    # value once came back with confidence "high", and a confident
    # "nothing" is still nothing.
    return text is None or str(text).strip().lower() in MISSING_WORDS or str(text).strip().lower().startswith("not stated")


def normalize_cusip(text):
    """Any printed CUSIP to 9 capital characters with no spaces, or None."""
    # A CUSIP is the 9-character ID for a US or Canadian security.
    # No value: say so with None, so a blank never "matches" a blank.
    if _missing(text):
        return None
    # Remove whitespace and dashes, use capitals: "68270c 202" -> "68270C202".
    # Why: one source prints "68270C 202" and the other "68270C202". They
    # are the same CUSIP, but == on the raw text would say they differ
    # and raise a false conflict.
    # re.sub(pattern, "", text) replaces every match with nothing.
    # The pattern [\s\-] means "one character that is whitespace (\s) or
    # a dash (\-)". The r before the quotes makes a "raw string", so the
    # backslashes reach the regex engine untouched.
    cleaned = re.sub(r"[\s\-]", "", str(text)).upper()
    # The whole thing is exactly 9 letters or digits: done.
    # re.fullmatch only succeeds if the pattern covers the WHOLE text.
    # [0-9A-Z] is one digit or capital letter; {9} means exactly nine.
    if re.fullmatch(r"[0-9A-Z]{9}", cleaned):
        return cleaned
    # Otherwise look for a CUSIP inside longer text, such as
    # "CUSIP No. 06051GLX5". The two groups in ( ) allow one space in
    # the middle, as in "316773 DD9".
    # Piece by piece:
    #   ([0-9]{3}[0-9A-Z]{3})   group 1: 3 digits, then 3 letters or digits
    #                           (the issuer part of the CUSIP)
    #   \s?                     one optional space (? means "0 or 1 of")
    #   ([0-9A-Z]{2}[0-9])      group 2: 2 letters or digits, then the
    #                           final check digit
    # re.search finds the first match anywhere in the text.
    found = re.search(r"([0-9]{3}[0-9A-Z]{3})\s?([0-9A-Z]{2}[0-9])", str(text).upper())
    # A failed search returns None, which counts as false in an if.
    if found:
        # .group(1) and .group(2) are the two captured parts.
        return found.group(1) + found.group(2)
    # No CUSIP anywhere in the text.
    return None


def _make_date(year, month, day):
    """Return YYYY-MM-DD, or None if the date does not exist."""
    # try / except: run the code under try; if it raises the named error,
    # jump to the except block instead of crashing the whole screen.
    try:
        # date() raises ValueError for impossible dates like Sep 31.
        # .isoformat() prints the standard form, 2026-09-29.
        # int() turns text like "09" into the number 9.
        return date(int(year), int(month), int(day)).isoformat()
    # An impossible date is treated as "no date", never guessed at.
    except ValueError:
        return None


def normalize_date(text):
    """
    Find the first date in some text and return it as YYYY-MM-DD.
    Handles "2026-09-29", "September 29, 2026", "Sept. 25, 2026" and
    "12:01 a.m. Eastern Time on September 29, 2026". Returns None if
    there is no date.
    """
    # No value: nothing to find.
    if _missing(text):
        return None
    # Make sure we are working with text, whatever came in.
    text = str(text)
    # Form 1: 2026-09-29. (\d{4}) captures 4 digits, (\d{2}) captures 2.
    # \d means "one digit". The dashes between the groups are literal.
    found = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if found:
        # Groups 1, 2, 3 are year, month, day in this form.
        return _make_date(found.group(1), found.group(2), found.group(3))
    # Form 2: a month name, a day and a year. Piece by piece:
    #   ([A-Za-z]{3,9})   a word of 3 to 9 letters (the month)
    #   \.?               an optional dot, as in "Sept."
    #   \s+               one or more spaces
    #   (\d{1,2})         the day, 1 or 2 digits
    #   ,?\s+             an optional comma, then spaces
    #   (\d{4})           the year
    # re.finditer walks through EVERY match in order, not just the first,
    # so a non-month word that looks like one can be skipped.
    for found in re.finditer(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})", text):
        # Look up the month by its first 4 letters, then its first 3,
        # so "September", "Sept" and "Sep" all work. Words that are not
        # months, such as "Friday", find nothing and are skipped.
        word = found.group(1).lower()
        # word[:4] is a "slice": the first 4 characters. MONTHS.get(key)
        # returns None instead of crashing when the key is not there.
        # "a or b" gives a if it has a value, otherwise b.
        month = MONTHS.get(word[:4]) or MONTHS.get(word[:3])
        # Only a real month name gets this far.
        if month:
            # Here group 3 is the year and group 2 is the day.
            return _make_date(found.group(3), month, found.group(2))
    # Form 3: 9/29/2026, the US order of month, day, year.
    found = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if found:
        # Reorder to year, month, day for _make_date.
        return _make_date(found.group(3), found.group(1), found.group(2))
    # None of the three forms was found.
    return None


# A pattern that finds a ratio written in words, such as "one-for-ten".
# "|".join(...) builds "two hundred|one hundred|...|one": any of the
# number words. They are sorted longest first so "one hundred fifty"
# is tried before "one". [\s-]+ allows a space or a dash around "for".
# sorted(WORD_NUMBERS, key=len, reverse=True) sorts the dictionary's
# keys by their length (key=len says "sort by len() of each word"),
# and reverse=True puts the longest first. In a regex, | means "or",
# and the first alternative that fits wins, hence longest first.
_WORD = "|".join(sorted(WORD_NUMBERS, key=len, reverse=True))
# re.compile turns the pattern into a ready-made object once, when the
# file loads, instead of rebuilding it on every call.
# \b is a "word boundary", so "one" does not match inside "someone".
# re.IGNORECASE makes "One-For-Ten" match as well.
WORD_RATIO = re.compile(r"\b(" + _WORD + r")[\s-]+for[\s-]+(" + _WORD + r")\b", re.IGNORECASE)


def normalize_terms(text):
    """
    Put split terms into one form, "1-for-10".
    "1-for-10", "1 for 10", "one-for-ten (1-10)" and "1:10" all become
    "1-for-10". Redemption terms become "100% of principal". Anything
    else is lower-cased with single spaces.
    """
    # No value: nothing to normalize.
    if _missing(text):
        return None
    # Lower case once, so every pattern below can be written in lower case.
    lowered = str(text).lower()
    # An ADS ratio, such as "one (1) ADS representing two hundred (200)
    # ordinary shares" or "1 ADS = 200 ordinary shares". Piece by piece:
    #   (\d+)\)?               a number, maybe followed by ")" as in "(1)"
    #   \s*ads\s*              the word ADS
    #   (?:=|representing)\s*  "=" or "representing"
    #   (?:[a-z\- ]+\()?       optionally the number in words and "(",
    #                          as in "two hundred ("
    #   (\d+)\)?               the number of shares
    # (?: ... ) is a group that does NOT capture, so only the two numbers
    # come back as group 1 and group 2.
    # (An ADS, American Depositary Share, is a US-traded share that stands
    # for some number of a foreign company's ordinary shares.)
    # finditer finds every match; a ratio CHANGE prints the old ratio
    # first and the new one last, so the last match is the new ratio.
    # list(...) turns the matches into a list so we can count and index it.
    ads = list(re.finditer(r"(\d+)\)?\s*ads\s*(?:=|representing)\s*(?:[a-z\- ]+\()?(\d+)\)?", lowered))
    # An empty list counts as false, so this runs only if there was a match.
    if ads:
        # [-1] is the last item of a list.
        last = ads[-1]
        # An f-string: the f before the quotes lets {expression} drop a
        # value straight into the text. int() drops leading zeros.
        return f"{int(last.group(1))} ADS = {int(last.group(2))} shares"
    # Digits with "for": "1-for-10" or "1 for 10".
    # \s*-?\s* means "any spaces, an optional dash, any spaces".
    found = re.search(r"(\d+)\s*-?\s*for\s*-?\s*(\d+)", lowered)
    if found:
        return f"{int(found.group(1))}-for-{int(found.group(2))}"
    # Nasdaq's style: words, then the digits in brackets, as in
    # "one-for-twenty five (1-25)". The digits in brackets win, because a
    # spaced number word ("twenty five") could be read as just "twenty".
    # Found live on 2026-10-02 in alert 2026-683, which read as 1-for-20
    # before this rule. The pattern needs "for", then words, then "(a-b)",
    # so a date range such as "1-15" on its own still does not match.
    found = re.search(r"for[\s-]+[a-z\s-]*\((\d+)\s*-\s*(\d+)\)", lowered)
    if found:
        return f"{int(found.group(1))}-for-{int(found.group(2))}"
    # Words with "for": "one-for-ten".
    found = WORD_RATIO.search(lowered)
    if found:
        # Replace any dash inside a number word with a space before the
        # lookup, except the one key that keeps its dash (twenty-five).
        # So first try the word exactly as found; if that is not a key,
        # try it again with dashes turned into spaces.
        first = WORD_NUMBERS.get(found.group(1)) or WORD_NUMBERS.get(found.group(1).replace("-", " "))
        second = WORD_NUMBERS.get(found.group(2)) or WORD_NUMBERS.get(found.group(2).replace("-", " "))
        # Both numbers must be known, or we do not claim a ratio.
        if first and second:
            return f"{first}-for-{second}"
    # Digits with a colon, "1:10". A dash alone ("1-10") is not trusted
    # here, because it could be part of a date range.
    found = re.search(r"\b(\d+)\s*:\s*(\d+)\b", lowered)
    if found:
        return f"{int(found.group(1))}-for-{int(found.group(2))}"
    # A redemption price, such as "100% of the principal amount".
    # (\d+(?:\.\d+)?) is a whole number with an optional decimal part,
    # and \s*% is the percent sign after any spaces.
    # (A redemption is when a bond issuer pays the bond back early.)
    found = re.search(r"(\d+(?:\.\d+)?)\s*%", lowered)
    if found:
        return f"{found.group(1)}% of principal"
    # Fallback: lower case, single spaces. .split() breaks on any run
    # of spaces, and " ".join puts single spaces back.
    # This way two sources that differ only in spacing still agree.
    return " ".join(lowered.split())


def normalize_field(field, value):
    """Normalize one value according to which field it is."""
    # Each kind of field has its own rule, so pick the rule by name.
    if field == "new_cusip":
        return normalize_cusip(value)
    # "in" with a tuple tests "is field any one of these three names?"
    if field in ("market_effective_date", "source_notice_date", "effective_as_stated"):
        return normalize_date(value)
    if field == "terms":
        return normalize_terms(value)
    # Any other field: None if missing, else lower case, single spaces.
    if _missing(value):
        return None
    return " ".join(str(value).lower().split())


# ---------------------------------------------------------------------
# COMPARING THE TWO SOURCES
# ---------------------------------------------------------------------

def usable(check, field):
    """The normalized value of a field, but only if code verified it."""
    # "missing" and "unverified" fields are never used as evidence.
    # "verified" was set by evidence.py: the value has a citation to an
    # approved page that also passed the identity guard. Anything less
    # could be about a different company, so it counts for nothing here.
    if check["status"] != "verified":
        return None
    # Verified: put it in standard form so it can be compared with ==.
    return normalize_field(field, check["value"])


def compare_field(field, issuer_check, market_check):
    """Compare one field across the two channels."""
    # i and m are the usable, normalized values, or None.
    i = usable(issuer_check, field)
    m = usable(market_check, field)
    # Four cases: both sides have it, only issuer, only market, neither.
    if i and m:
        # A conditional expression: "A if test else B" picks one of two
        # values in a single line.
        verdict = "agree" if i == m else "differ"
    elif i:
        verdict = "issuer only"
    elif m:
        verdict = "market only"
    else:
        verdict = "neither"
    # The settled value: both agree, or only one side has it.
    # Two conditional expressions nested: take i when both agree or only
    # the issuer has it; otherwise take m when only the market has it;
    # otherwise None (they differ, or neither has it, so nothing is settled).
    resolved = i if verdict in ("agree", "issuer only") else (m if verdict == "market only" else None)
    # Return everything the table and the note need, raw and normalized,
    # so the screen can show what the source printed next to what code
    # compared.
    return {
        "field": field,
        "issuer_raw": issuer_check["value"],
        "market_raw": market_check["value"],
        "issuer_status": issuer_check["status"],
        "market_status": market_check["status"],
        "issuer": i,
        "market": m,
        "verdict": verdict,
        "resolved": resolved,
    }


def compare_sources(result):
    """Compare every shown field. Returns a list, one entry per field."""
    # The checked fields for each channel, as a dictionary field -> check.
    issuer = result["channels"]["issuer"]["fields"]
    market = result["channels"]["market"]["fields"]
    # A list comprehension: one compare_field result per shown field.
    # [expression for f in list] is a one-line way to build a new list by
    # running the expression once for every item.
    return [compare_field(f, issuer[f], market[f]) for f in SHOWN_FIELDS]


def in_window(notice_date, window_start):
    """True unless the notice is dated before the ticket's window."""
    # Why a window: an old notice about the same company (last year's
    # split, say) must not be used as evidence for today's break.
    # No printed date: we cannot say it is outside, so it stays in.
    if not notice_date:
        return True
    # Dates in YYYY-MM-DD form sort correctly as plain text, so the
    # ordinary >= test works without converting them.
    return notice_date >= window_start


def channel_usable(channel, row):
    """
    Can this channel's evidence be used? Returns (True or False, reason).
    Usable means: at least one key field verified in code, and the date
    printed on the notice is inside the ticket's evidence window.
    """
    # The envelope is the package exa_client returned for this call.
    envelope = channel["envelope"]
    # The code-checked fields for this channel.
    fields = channel["fields"]
    # No answer at all (not live and no saved run): unusable.
    if not envelope["ok"]:
        # "return a, b" returns a tuple of two values. The caller unpacks
        # it with "ok, why = channel_usable(...)".
        # "x or 'no saved run'" shows the error, or the fallback words
        # when the error is blank.
        return False, f"no result ({envelope['error'] or 'no saved run'})"
    # Exa's stored page is a "Page Not Available" placeholder: its fields
    # describe nothing, so it cannot be evidence.
    if channel["stale_url"]:
        return False, f"Exa's stored copy of {channel['stale_url']} is a 'Page Not Available' placeholder"
    # The date printed on the notice, only if code verified it.
    notice = usable(fields["source_notice_date"], "source_notice_date")
    # Too old for this ticket: unusable, and say the two dates.
    if not in_window(notice, row["window_start"]):
        return False, f"notice dated {notice}, before the window start {row['window_start']}"
    # A list comprehension with a filter: keep only the key fields whose
    # status is "verified".
    verified = [f for f in KEY_FIELDS if fields[f]["status"] == "verified"]
    # At least one key field verified: usable, and name the fields.
    if verified:
        # ", ".join(list) glues the names into one text with commas.
        return True, "verified: " + ", ".join(verified)
    # Count why nothing was verified, to say it plainly.
    # sum(1 for ...) counts the items that pass the test: it adds a 1
    # for each one.
    missing = sum(1 for f in KEY_FIELDS if fields[f]["status"] == "missing")
    # Every key field that is not missing must be unverified here.
    unverified = len(KEY_FIELDS) - missing
    # How many result pages passed the identity guard, for context.
    kept = len(channel["guard"]["kept"])
    # Two f-strings side by side inside brackets are joined into one
    # text by Python, which lets a long message span two lines.
    return False, (
        f"no key field could be verified ({missing} not stated, {unverified} failed the "
        f"citation check; {kept} page(s) passed the identity guard)"
    )


def date_notes(result):
    """Notes when a source's legal effective date differs from its first trading day."""
    # Why: a split can be legally effective at 12:01 a.m. on one day
    # while the stock first trades on the new terms on another. Two
    # vendors that picked different ones can both be right, so we
    # explain the gap instead of calling it a conflict.
    notes = []
    # Check each channel in turn.
    for name in ("issuer", "market"):
        fields = result["channels"][name]["fields"]
        # The legal date and the first trading day, both verified only.
        legal = usable(fields["effective_as_stated"], "effective_as_stated")
        trading = usable(fields["market_effective_date"], "market_effective_date")
        # Both present and different: add a note that explains it.
        if legal and trading and legal != trading:
            # \" inside a string is a literal double quote character.
            notes.append(
                f"Explained difference ({name} channel): legal effective date {legal} "
                f"(\"{fields['effective_as_stated']['value']}\") and first trading day on the "
                f"new terms {trading} differ. Both vendor dates can be right; they mean different things."
            )
    return notes


def _is_sec(channel):
    """True if the market channel is sec.gov (an issuer filing, not an exchange)."""
    # Why: an SEC filing is usually the issuer's own release filed again,
    # so it repeats the issuer rather than confirming it independently.
    return "sec.gov" in channel["allowlist"]


def row_label(result, comparisons):
    """Give the row one label code, with the reason in words."""
    row = result["row"]
    # Tuple unpacking: channel_usable returns two values, and this line
    # puts the first in issuer_ok and the second in issuer_why.
    issuer_ok, issuer_why = channel_usable(result["channels"]["issuer"], row)
    market_ok, market_why = channel_usable(result["channels"]["market"], row)
    # dict.get("repair") returns None when there was no repair, instead
    # of crashing on a missing key.
    repair = result.get("repair")
    # Only key fields decide the label.
    key = [c for c in comparisons if c["field"] in KEY_FIELDS]
    # The names of the key fields where the two sides differ, and agree.
    differ = [c["field"] for c in key if c["verdict"] == "differ"]
    agree = [c["field"] for c in key if c["verdict"] == "agree"]

    # The rules run top to bottom and the first one that fits wins, so
    # their order is the priority: a conflict beats an agreement, and
    # two sources beat one.
    if issuer_ok and market_ok and differ:
        # Two usable sources that disagree on any key field: escalate.
        code, reason = "CONFLICT", "sources disagree on " + ", ".join(differ)
    elif issuer_ok and market_ok and agree:
        # An SEC copy is usually the issuer's own release filed again.
        code = "SAME_ISSUER" if _is_sec(result["channels"]["market"]) else "CORROBORATED"
        reason = "issuer and market sources agree on " + ", ".join(agree)
    elif issuer_ok and not market_ok:
        # Only the issuer is usable; the reason says why the market is not.
        code, reason = "SINGLE_ISSUER", "market channel: " + market_why
    elif market_ok and not issuer_ok:
        # Only the market is usable; the reason says why the issuer is not.
        code, reason = "SINGLE_MARKET", "issuer channel: " + issuer_why
    elif issuer_ok and market_ok:
        # Both usable, but they verified different fields, so there is no
        # shared field to compare.
        code, reason = "NOT_CONFIRMED", "both sources usable but they give different fields, so nothing can be compared"
    elif repair and repair["ok"]:
        # Neither search was usable, but the live re-fetch of a stale page
        # worked. It is one source, so the analyst confirms.
        code, reason = "STALE_REPAIRED", f"only source is the re-fetched page {repair['url']}"
    else:
        # Nothing usable. Collect every reason so the analyst sees them all.
        parts = ["issuer channel: " + issuer_why, "market channel: " + market_why]
        if repair:
            parts.append(f"live re-fetch of {repair['url']}: {repair['reason']}")
        # "; ".join puts a semicolon and a space between the reasons.
        code, reason = "NOT_CONFIRMED", "; ".join(parts)

    # Look up the words and colour for the chosen code (tuple unpacking).
    text, colour = LABELS[code]
    return {"code": code, "label": text, "colour": colour, "reason": reason, "notes": date_notes(result)}


# ---------------------------------------------------------------------
# CHECKING THE VENDORS AGAINST THE EVIDENCE
# ---------------------------------------------------------------------

def _vendor_status(raw, field, resolved, legal_date):
    """Say how one vendor's value compares with the evidence."""
    # The vendor sent nothing for this field.
    if _missing(raw):
        return "no value on file"
    # Normalize the vendor value with the same rule as the evidence, so
    # a difference in spacing or format is not called a mismatch.
    value = normalize_field(field, raw)
    # The evidence did not settle the field, so we cannot grade a vendor.
    if resolved is None:
        return "cannot judge: the evidence did not settle this field"
    if value == resolved:
        return "matches the evidence"
    # A vendor date that equals the LEGAL effective date is a valid
    # meaning of "effective", just not the first trading day. That is a
    # field-mapping question for us, not a vendor error.
    if field == "market_effective_date" and legal_date and value == legal_date:
        return "matches the legal effective date, not the first trading day: check our field mapping"
    # A real mismatch.
    return "does not match the evidence"


def vendor_check(result, comparisons):
    """Compare Vendor A and Vendor B with the settled value."""
    row = result["row"]
    # The field the two vendors disagree on, such as new_cusip.
    field = row["field_in_dispute"]
    # next(...) returns the first matching item, or None if there is none.
    # The part in brackets is a "generator": like a list comprehension,
    # but it hands out items one at a time, so next() can stop early.
    comp = next((c for c in comparisons if c["field"] == field), None)
    # The settled value for that field, or None if there is no comparison.
    resolved = comp["resolved"] if comp else None
    # Words that say where the settled value came from, used in the note.
    basis = "the evidence"
    # When the only source is a repaired stale page, its CUSIP (read by
    # code from the page text) may settle a CUSIP dispute, but it is one
    # source, so the wording says the analyst must confirm it.
    repair = result.get("repair")
    # All five must hold: nothing settled yet, the dispute is a CUSIP, a
    # repair ran, it worked, and code found a CUSIP on the page.
    if resolved is None and field == "new_cusip" and repair and repair["ok"] and repair.get("cusip"):
        resolved = repair["cusip"]
        basis = "the repaired page (one source; analyst confirms)"
    # The issuer's verified legal effective date, used by _vendor_status
    # to spot the "legal date versus first trading day" case.
    legal = usable(result["channels"]["issuer"]["fields"]["effective_as_stated"], "effective_as_stated")

    def status(raw):
        # A function inside a function: it can read field, resolved,
        # legal and basis from vendor_check, so each vendor is one line.
        # .replace swaps the generic words for the actual basis.
        return _vendor_status(raw, field, resolved, legal).replace("the evidence", basis)

    # One dictionary for the screen and the note: each vendor's raw
    # value next to its status.
    return {
        "field": field,
        "resolved": resolved,
        "basis": basis,
        "vendor_a": {"raw": row["vendor_a"], "status": status(row["vendor_a"])},
        "vendor_b": {"raw": row["vendor_b"], "status": status(row["vendor_b"])},
    }


# ---------------------------------------------------------------------
# THE TICKET NOTE
# ---------------------------------------------------------------------

def _first_citation(channel):
    """The first verified citation URL in a channel, or ""."""
    # Key fields first, so the link shown is the most important one.
    for field in KEY_FIELDS + ["effective_as_stated", "source_notice_date"]:
        # cited_url is "" unless the field was verified, and "" is false.
        if channel["fields"][field]["cited_url"]:
            return channel["fields"][field]["cited_url"]
    # No verified citation at all.
    return ""


def draft_ticket_note(result, label, comparisons, vendors):
    """Write the resolution note. Only verified fields and their links go in."""
    row = result["row"]
    # Start the note as a list of lines; each line is one f-string.
    # Inside an f-string that uses double quotes, the keys use single
    # quotes, as in row['id'], so the quotes do not clash.
    lines = [
        f"Break Check: {row['id']} ({row['issuer_display']}), ticket opened {row['opened_at']}",
        f"Result: {label['label']}. {label['reason']}.",
    ]
    # Any explained date differences go right under the result.
    for note in label["notes"]:
        lines.append(note)
    # The disputed field and its settled value, with where it came from.
    lines.append(
        f"Field in dispute: {vendors['field']}. Settled value: {vendors['resolved'] or 'not settled'} "
        f"(from {vendors['basis']})."
    )
    # Each vendor's value, or "blank" if it sent none, and its status.
    lines.append(f"Vendor A ({vendors['vendor_a']['raw'] or 'blank'}): {vendors['vendor_a']['status']}.")
    lines.append(f"Vendor B ({vendors['vendor_b']['raw'] or 'blank'}): {vendors['vendor_b']['status']}.")
    # Only channels that are usable as evidence go into the note. A
    # channel whose only verified field is a date on an unrelated
    # release must not appear as a source.
    usable_sides = []
    for side in ("issuer", "market"):
        # "_" takes the reason we do not need here; only ok matters.
        ok, _ = channel_usable(result["channels"][side], row)
        if ok:
            usable_sides.append(side)
    lines.append("Verified fields:")
    # For every field and every usable side, list the verified values
    # with the page that proves each one.
    for comp in comparisons:
        for side in usable_sides:
            # f"{side}_status" builds the key name, "issuer_status" or
            # "market_status".
            if comp[f"{side}_status"] == "verified":
                url = result["channels"][side]["fields"][comp["field"]]["cited_url"]
                lines.append(f"  - {comp['field']} = {comp[f'{side}_raw']} ({side} source: {url})")
    # Say so plainly when there is nothing to list.
    if not usable_sides:
        lines.append("  - none from the two searches")
    # One source link per channel, or "none usable".
    for side in ("issuer", "market"):
        url = _first_citation(result["channels"][side]) if side in usable_sides else ""
        # .capitalize() makes the first letter a capital: "Issuer".
        lines.append(f"{side.capitalize()} source: {url or 'none usable'}")
    # If a stale page was re-fetched, record whether that worked.
    if result.get("repair"):
        repair = result["repair"]
        lines.append(f"Stale page {repair['url']}: live re-fetch {'worked' if repair['ok'] else 'failed'} ({repair['reason']}).")
    # The honesty line: vendors are mocked and a person approves.
    lines.append("Vendor values in this demo are mocked. Nothing is loaded until an analyst approves.")
    # "\n".join puts each line on its own line.
    return "\n".join(lines)


# ---------------------------------------------------------------------
# ONE CALL FOR THE SCREEN
# ---------------------------------------------------------------------

def judge(result):
    """Run every step for one checked row and return it all together."""
    # Step 1: field by field, issuer against market.
    comparisons = compare_sources(result)
    # Step 2: one label for the row, with its reason.
    label = row_label(result, comparisons)
    # Step 3: grade each vendor against the settled value.
    vendors = vendor_check(result, comparisons)
    # Step 4: write the ticket note from the three results above.
    note = draft_ticket_note(result, label, comparisons, vendors)
    # One dictionary, so the screen gets everything in a single call.
    return {"comparisons": comparisons, "label": label, "vendors": vendors, "note": note}
