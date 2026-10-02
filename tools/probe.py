"""
probe.py - run the demo rows against Exa with a real key and print what comes back.

Used to find out, before building screens, which rows work live, how long
each search type takes, and what each call costs. Every response is saved
to cache/ by exa_client, so nothing here has to be run twice.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import exa_client  # noqa: E402

WIRES = ["globenewswire.com", "prnewswire.com", "businesswire.com", "accessnewswire.com"]

SCHEMA = {
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
        "source_notice_date": {"type": "string", "description": "YYYY-MM-DD printed on the notice itself"},
    },
}

def system_prompt(issuer, kind):
    return (f"You are checking a security master exception for an investment operations team. "
            f"Use only {kind} about {issuer}; ignore every other company and every other security. "
            f"Copy dates and times exactly as the source writes them. If a later notice updates an "
            f"earlier one, use the later one. Write not stated for any field the source does not give. Never infer.")

ROWS = {
    "CDT": {
        "issuer": "CDT Equity Inc. (Nasdaq: CDT)",
        "issuer_q": "Press release from CDT Equity Inc. (Nasdaq: CDT) announcing a reverse stock split, with the split ratio, the effective date and time, the first day of split-adjusted trading, and the new CUSIP",
        "issuer_domains": WIRES,
        "market_q": "Nasdaq Equity Corporate Actions Alert for CDT Equity Inc. (CDT) announcing a reverse stock split and a CUSIP change, with the effective date",
        "market_domains": ["nasdaqtrader.com"],
        "start": "2026-08-29T00:00:00Z",
    },
    "CTNT": {
        "issuer": "Cheetah Net Supply Chain Service Inc. (Nasdaq: CTNT)",
        "issuer_q": "Press release from Cheetah Net Supply Chain Service Inc. (Nasdaq: CTNT) announcing a reverse stock split, with the split ratio, the effective date, and the new CUSIP",
        "issuer_domains": WIRES,
        "market_q": "Nasdaq Equity Corporate Actions Alert for Cheetah Net Supply Chain Service Inc. (CTNT) announcing a reverse stock split and a CUSIP change, with the effective date",
        "market_domains": ["nasdaqtrader.com"],
        "start": "2026-08-29T00:00:00Z",
    },
    "FITB": {
        "issuer": "Fifth Third Bancorp notes with CUSIP 316773 DD9",
        "issuer_q": "Press release from Fifth Third Bancorp announcing the redemption of its notes with CUSIP 316773 DD9, with the redemption date and redemption price",
        "issuer_domains": WIRES + ["ir.53.com"],
        "market_q": "Fifth Third Bancorp Form 8-K announcing the redemption of notes with CUSIP 316773 DD9, with the redemption date and redemption price",
        "market_domains": ["sec.gov"],
        "start": "2026-08-25T00:00:00Z",
    },
    "BAC": {
        "issuer": "Bank of America Floating Rate Senior Notes due September 2027, CUSIP 06051GLX5",
        "issuer_q": "Press release from Bank of America announcing the redemption of its Floating Rate Senior Notes due September 2027, CUSIP 06051GLX5, with the redemption date and redemption price",
        "issuer_domains": WIRES + ["newsroom.bankofamerica.com"],
        "market_q": "Bank of America SEC filing about the redemption of Floating Rate Senior Notes due September 2027, CUSIP 06051GLX5",
        "market_domains": ["sec.gov"],
        "start": "2026-08-05T00:00:00Z",
    },
    "IMMP": {
        "issuer": "Immutep Limited American Depositary Shares (Nasdaq: IMMP)",
        "issuer_q": "Press release from Immutep Limited (Nasdaq: IMMP) announcing a change to the ratio of its American Depositary Shares to ordinary shares, with the effective date and the new CUSIP",
        "issuer_domains": WIRES,
        "market_q": "Nasdaq Equity Corporate Actions Alert for Immutep Limited (IMMP) American Depositary Shares ratio change, with the effective date and new CUSIP",
        "market_domains": ["nasdaqtrader.com"],
        "start": "2026-08-01T00:00:00Z",
    },
}

def body(row, channel, search_type):
    r = ROWS[row]
    kind = "the issuer's own announcements" if channel == "issuer" else "the exchange's or the SEC's official notices"
    return {
        "query": r[f"{channel}_q"],
        "type": search_type,
        "includeDomains": r[f"{channel}_domains"],
        "startPublishedDate": r["start"],
        "systemPrompt": system_prompt(r["issuer"], kind),
        "outputSchema": SCHEMA,
        "contents": {"highlights": True},
    }

def show(row, channel, search_type):
    t0 = time.perf_counter()
    env = exa_client.search(body(row, channel, search_type))
    wall = int((time.perf_counter() - t0) * 1000)
    d = env["data"]
    print(f"\n=== {row} | {channel} | {search_type} | ok={env['ok']} src={env['source']} "
          f"wall={wall}ms searchTime={d.get('searchTime')} cost=${env['cost_dollars']} {env['error']}")
    out = (d.get("output") or {})
    content = out.get("content")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except ValueError:
            pass
    print("  FIELDS:", json.dumps(content, ensure_ascii=True)[:700])
    for g in (out.get("grounding") or [])[:8]:
        cites = [c.get("url", "")[:90] for c in (g.get("citations") or [])][:2]
        print(f"  GROUND {g.get('field')}: {g.get('confidence')} {cites}")
    for x in (d.get("results") or [])[:6]:
        hl = " ".join(x.get("highlights") or [])[:160].replace("\n", " ")
        print(f"  RESULT {str(x.get('publishedDate'))[:10]} {x.get('url','')[:95]} | {x.get('title','')[:60]!r} | {hl.encode('ascii','replace').decode()}")

if __name__ == "__main__":
    rows = sys.argv[1].split(",") if len(sys.argv) > 1 else list(ROWS)
    types = sys.argv[2].split(",") if len(sys.argv) > 2 else ["auto"]
    for row in rows:
        for channel in ("issuer", "market"):
            for t in types:
                show(row, channel, t)
