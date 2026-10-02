"""
test_evidence.py - tests for the identity guard, citation check, stale
detector and repair check. Uses saved responses from cache_golden\\
(read only) and a few made-up pages. No network.
"""

import unittest

# helpers must be imported first: it puts the app folder on the path.
from helpers import block_network

import evidence
import exa_client

ROWS = evidence.load_rows()
CHANNELS = evidence.load_channels()

# The two re-fetch bodies used on the morning of Sep 29, whose saved
# answers are "success" with an empty page.
EMPTY_HIGHLIGHTS_BODY = {
    "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
    "highlights": True,
    "maxAgeHours": 0,
    "livecrawlTimeout": 12000,
}
EMPTY_TEXT_BODY = {
    "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
    "maxAgeHours": 0,
    "livecrawlTimeout": 12000,
    "text": {"maxCharacters": 1500},
}


def saved(row_id, channel):
    """The saved envelope for one fixed row and channel."""
    row = evidence.find_row(ROWS, row_id)
    body = evidence.build_search_body(row, channel, CHANNELS)
    return row, exa_client.search(body, cache_only=True)


class IdentityGuardTests(unittest.TestCase):

    def setUp(self):
        block_network(self)
        self.cdt = evidence.find_row(ROWS, "CDT")

    def test_time_zone_cdt_is_not_kept(self):
        # Another company's release that mentions Central Daylight Time.
        page = {
            "url": "https://www.globenewswire.com/news-release/other.html",
            "title": "Acme Widgets to Host Third Quarter Conference Call",
            "highlights": ["The call will begin at 10:00 a.m. CDT on October 8."],
        }
        guard = evidence.identity_guard([page], self.cdt)
        self.assertEqual(guard["kept"], [])
        # A bare ticker is amber: shown, never used as evidence.
        self.assertEqual(len(guard["amber"]), 1)

    def test_exchange_prefixed_ticker_is_kept(self):
        page = {"url": "https://x.com/a", "title": "Release", "highlights": ["CDT Holdings (NASDAQ:CDT) said"]}
        level, _ = evidence.match_identity(evidence.page_text(page), self.cdt)
        self.assertEqual(level, "strong")

    def test_real_cdt_release_is_kept(self):
        row, env = saved("CDT", "issuer")
        guard = evidence.identity_guard(env["data"]["results"], row)
        kept = [p["url"] for p in guard["kept"]]
        self.assertTrue(any("cdt-equity-inc-announces-reverse-stock-split" in u for u in kept))

    def test_bac_other_series_is_dropped(self):
        row, env = saved("BAC", "issuer")
        guard = evidence.identity_guard(env["data"]["results"], row)
        dropped_cad = [p for p in guard["dropped"] if "cad425" in p["url"]]
        self.assertTrue(dropped_cad)
        self.assertIn("different series", dropped_cad[0]["reason"])


class GroundingTests(unittest.TestCase):

    def setUp(self):
        block_network(self)

    def test_not_stated_with_high_confidence_is_missing(self):
        row, env = saved("CTNT", "issuer")
        guard = evidence.identity_guard(env["data"]["results"], row)
        checks = evidence.check_grounding(env["data"], guard, evidence.domains_for(row, "issuer", CHANNELS))
        # Exa said "high" confidence, but the value is "not stated".
        self.assertEqual(checks["terms"]["confidence"], "high")
        self.assertEqual(checks["terms"]["value"], "not stated")
        self.assertEqual(checks["terms"]["status"], "missing")

    def test_empty_value_is_missing(self):
        self.assertTrue(evidence.is_missing(""))
        self.assertTrue(evidence.is_missing("Not stated"))
        self.assertFalse(evidence.is_missing("1-for-10"))

    def test_citation_outside_allowlist_is_unverified(self):
        data = {
            "results": [{"url": "https://evil.example.com/p", "title": "OneMedNet Corp news", "highlights": []}],
            "output": {
                "content": {"terms": "1-for-10"},
                "grounding": [{"field": "terms", "citations": [{"url": "https://evil.example.com/p"}], "confidence": "high"}],
            },
        }
        row = evidence.find_row(ROWS, "ONMD")
        guard = evidence.identity_guard(data["results"], row)
        checks = evidence.check_grounding(data, guard, ["globenewswire.com"])
        self.assertEqual(checks["terms"]["status"], "unverified")
        self.assertIn("outside the approved domains", checks["terms"]["reason"])

    def test_onmd_fields_verified(self):
        row, env = saved("ONMD", "market")
        guard = evidence.identity_guard(env["data"]["results"], row)
        checks = evidence.check_grounding(env["data"], guard, evidence.domains_for(row, "market", CHANNELS))
        self.assertEqual(checks["new_cusip"]["status"], "verified")
        self.assertIn("ECA2026-688", checks["new_cusip"]["cited_url"])


class StaleAndRepairTests(unittest.TestCase):

    def setUp(self):
        block_network(self)

    def test_stale_detector_sees_placeholder_that_guard_drops(self):
        row, env = saved("CTNT", "market")
        checked = evidence.check_channel(row, "market", env, CHANNELS)
        self.assertEqual(checked["stale_url"], "https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677")
        # The guard dropped the same page, so the detector must run on raw results.
        dropped = [p["url"] for p in checked["guard"]["dropped"]]
        self.assertIn(checked["stale_url"], dropped)

    def test_stale_detector_quiet_on_good_row(self):
        row, env = saved("ONMD", "market")
        checked = evidence.check_channel(row, "market", env, CHANNELS)
        self.assertIsNone(checked["stale_url"])

    def test_success_with_empty_page_is_failure(self):
        # Saved on Sep 29: status "success", source "crawled", no highlights.
        env = exa_client.contents(EMPTY_HIGHLIGHTS_BODY, cache_only=True)
        self.assertEqual(env["data"]["statuses"][0]["status"], "success")
        ok, reason, _ = evidence.repair_outcome(env)
        self.assertFalse(ok)
        self.assertIn("empty", reason)

    def test_success_with_whitespace_text_is_failure(self):
        env = exa_client.contents(EMPTY_TEXT_BODY, cache_only=True)
        ok, reason, _ = evidence.repair_outcome(env)
        self.assertFalse(ok)

    def test_repaired_page_naming_another_issuer_is_discarded(self):
        row = evidence.find_row(ROWS, "CTNT")
        other = {
            "ok": True, "error": "",
            "data": {
                "statuses": [{"status": "success", "source": "crawled"}],
                "results": [{"title": "Alert for Some Other Co (SOCO)", "highlights": ["Some Other Co (SOCO) will effect a split"]}],
            },
        }
        ok, _, text = evidence.repair_outcome(other)
        self.assertTrue(ok)
        level, _ = evidence.match_identity(text, row)
        self.assertNotEqual(level, "strong")

    def test_cusip_read_from_repaired_text(self):
        text = "In conjunction with the reverse split, the CUSIP number will change to 16307X400."
        self.assertEqual(evidence.cusip_after_word(text), "16307X400")


class BodyTests(unittest.TestCase):

    def test_free_form_onmd_builds_the_same_bodies(self):
        # Typing ONMD by hand must produce the fixed row's bodies, so its
        # saved run is found too.
        fixed = evidence.find_row(ROWS, "ONMD")
        typed = evidence.make_free_form_row("onmd", "OneMedNet Corp", "reverse stock split", "nasdaq_equity", CHANNELS)
        for channel in ("issuer", "market"):
            self.assertEqual(
                evidence.build_search_body(fixed, channel, CHANNELS),
                evidence.build_search_body(typed, channel, CHANNELS),
            )

    def test_search_body_follows_exa_guidance(self):
        row = evidence.find_row(ROWS, "CDT")
        body = evidence.build_search_body(row, "issuer", CHANNELS)
        for banned in ("numResults", "category", "additionalQueries"):
            self.assertNotIn(banned, body)
        self.assertEqual(body["type"], "auto")
        self.assertEqual(body["contents"], {"highlights": True})

    def test_bac_issuer_channel_adds_newsroom(self):
        row = evidence.find_row(ROWS, "BAC")
        self.assertIn("newsroom.bankofamerica.com", evidence.domains_for(row, "issuer", CHANNELS))
        self.assertEqual(evidence.domains_for(row, "market", CHANNELS), ["sec.gov"])


if __name__ == "__main__":
    unittest.main()
