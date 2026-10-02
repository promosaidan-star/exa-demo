"""
test_scan.py - tests for the watchlist scan: the portfolio matcher, the
vendor comparison, the source count, the impact panel and the request
body. Uses saved responses from cache_golden\\ (read only) and a few
made-up values. No network: block_network makes any HTTP call fail.
"""

import unittest

# helpers must be imported first: it puts the app folder on the path.
from helpers import block_network

import scan

# The watchlist, loaded once for every test in this file.
PORTFOLIO = scan.load_portfolio()
SECURITIES = PORTFOLIO["securities"]


def event(**fields):
    """A made-up event with every scan field, "not stated" by default."""
    # A dictionary comprehension gives every field "not stated" first;
    # .update then overwrites the ones this test cares about.
    base = {f: "not stated" for f in scan.SCAN_FIELDS}
    base.update(fields)
    return base


class PortfolioMatcherTests(unittest.TestCase):

    def test_printed_ticker_matches_its_holding(self):
        self.assertEqual(scan.match_event_to_portfolio("ONMD", "", SECURITIES), "ONMD")

    def test_cusip_with_a_space_matches_the_bond(self):
        # The CUSIP printed with a space still matches after squashing.
        self.assertEqual(scan.match_event_to_portfolio("06051G LX5", "", SECURITIES), "BAC 06051GLX5")

    def test_legal_name_on_the_page_matches_when_identifier_missing(self):
        text = "Agroz Inc. today announced a reverse stock split."
        self.assertEqual(scan.match_event_to_portfolio("not stated", text, SECURITIES), "AGRZ")

    def test_time_zone_cdt_matches_nothing(self):
        # "CDT" as Central Daylight Time is not CDT Equity.
        text = "The call will begin at 10:00 a.m. CDT on October 8."
        self.assertIsNone(scan.match_event_to_portfolio("not stated", text, SECURITIES))

    def test_unknown_identifier_and_unknown_page_match_nothing(self):
        self.assertIsNone(scan.match_event_to_portfolio("ZZZZ", "Some other company", SECURITIES))


class VendorComparisonTests(unittest.TestCase):

    def test_event_absent_from_both_vendors(self):
        found = event(event_type="reverse split", terms="1-for-50", effective_date="2026-09-14")
        result = scan.compare_vendors(found, None, None)
        self.assertEqual(result["status"], scan.ABSENT_BOTH)

    def test_event_at_one_vendor_only(self):
        found = event(event_type="redemption", terms="100%", effective_date="2026-09-15")
        record = {"event_type": "redemption", "terms": "100% of principal", "effective_date": "2026-09-15"}
        result = scan.compare_vendors(found, record, None)
        self.assertEqual(result["status"], scan.ONE_VENDOR)
        self.assertIn("Vendor B", result["note"])

    def test_vendor_with_a_different_event_does_not_count(self):
        found = event(event_type="reverse split", terms="1-for-10")
        record = {"event_type": "ticker change"}
        self.assertEqual(scan.compare_vendors(found, record, None)["status"], scan.ABSENT_BOTH)

    def test_both_vendors_with_a_wrong_ratio_is_listed(self):
        found = event(event_type="reverse split", terms="1-for-15", effective_date="2026-09-17", new_identifier="47010C854")
        a = {"event_type": "reverse split", "terms": "1-for-15", "effective_date": "2026-09-17", "new_identifier": "47010C854"}
        b = {"event_type": "reverse split", "terms": "1-for-5", "effective_date": "2026-09-17", "new_identifier": "47010C854"}
        result = scan.compare_vendors(found, a, b)
        self.assertEqual(result["status"], scan.BOTH_VENDORS)
        self.assertEqual(len(result["differences"]), 1)
        self.assertIn("Vendor B terms 1-for-5", result["differences"][0])

    def test_vendor_holding_the_legal_date_is_named_as_such(self):
        found = event(event_type="reverse split", terms="1-for-25", effective_date="2026-09-29",
                      effective_as_stated="September 28, 2026, at 5:00 pm, Eastern Time", new_identifier="20678X700")
        a = {"event_type": "reverse split", "terms": "1-for-25", "effective_date": "2026-09-28", "new_identifier": "20678X700"}
        result = scan.compare_vendors(found, a, a)
        self.assertIn("legal effective date", result["differences"][0])

    def test_nothing_found_says_which_vendor_shows_an_event(self):
        record = {"event_type": "reverse split"}
        result = scan.compare_vendors(None, record, None)
        self.assertEqual(result["status"], scan.NOTHING_FOUND)
        self.assertIn("Vendor A", result["note"])

    def test_typed_name_has_no_vendor_records(self):
        found = event(event_type="reverse split")
        self.assertEqual(scan.compare_vendors(found, None, None, typed=True)["status"], scan.NO_VENDOR_RECORDS)


class SourceCountTests(unittest.TestCase):

    def test_two_wire_copies_are_one_statement(self):
        checks = {
            "terms": {"status": "verified", "good_citations": ["https://www.prnewswire.com/a", "https://www.globenewswire.com/b"]},
        }
        sources = scan.originating_statements(checks)
        self.assertFalse(sources["independent"])
        self.assertIn("One originating statement", sources["label"])

    def test_issuer_plus_exchange_is_two_independent_sources(self):
        checks = {
            "terms": {"status": "verified", "good_citations": ["https://www.prnewswire.com/a"]},
            "effective_date": {"status": "verified", "good_citations": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-682"]},
        }
        self.assertTrue(scan.originating_statements(checks)["independent"])


class RequestBodyTests(unittest.TestCase):

    def test_body_never_names_the_event_and_follows_exa_guidance(self):
        body = scan.build_scan_body(scan.find_security(PORTFOLIO, "NFE"), PORTFOLIO)
        # No ratio and no "1-for" in the query: the event is not named.
        self.assertNotIn("1-for", body["query"])
        self.assertNotIn("50", body["query"])
        # Exa's guidance: no numResults, no category, type auto, highlights.
        self.assertNotIn("numResults", body)
        self.assertNotIn("category", body)
        self.assertEqual(body["type"], "auto")
        self.assertEqual(body["contents"], {"highlights": True})
        # Holdings never go to Exa.
        self.assertNotIn("15000", str(body))


class SavedScanTests(unittest.TestCase):
    """The whole scan, replayed from cache_golden with the network blocked."""

    @classmethod
    def setUpClass(cls):
        # setUpClass runs once for the class, so the scan replays once.
        findings = scan.run_scan(SECURITIES, PORTFOLIO, cache_only=True)
        cls.by_id = {f["security"]["id"]: f for f in findings}

    def setUp(self):
        block_network(self)

    def test_every_security_came_from_a_saved_run(self):
        for finding in self.by_id.values():
            self.assertEqual(finding["envelope"]["source"], "cache")

    def test_nfe_and_agrz_are_absent_from_both(self):
        self.assertEqual(self.by_id["NFE"]["status"], scan.ABSENT_BOTH)
        self.assertEqual(self.by_id["AGRZ"]["status"], scan.ABSENT_BOTH)

    def test_quiet_names_find_nothing(self):
        self.assertEqual(self.by_id["MSFT"]["status"], scan.NOTHING_FOUND)
        self.assertEqual(self.by_id["PG"]["status"], scan.NOTHING_FOUND)

    def test_split_impact_shows_shares_before_and_after(self):
        lines = " ".join(self.by_id["ONMD"]["impact"]["lines"])
        self.assertIn("10,000 shares before. 1,000 shares after", lines)

    def test_bond_redemption_is_never_marked_redeemed(self):
        impact = self.by_id["BAC 06051GLX5"]["impact"]
        self.assertEqual(impact["action"], "Propose status update for analyst verification.")
        self.assertIn("Do not mark the notes redeemed", impact["warning"])

    def test_cdt_needs_a_date_mapping_review(self):
        self.assertEqual(self.by_id["CDT"]["impact"]["date_mapping"], {"legal": "2026-09-28", "trading": "2026-09-29"})


if __name__ == "__main__":
    unittest.main()
