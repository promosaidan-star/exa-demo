"""
test_compare.py - tests for normalizing, labels, vendor checks and the
note. Runs the fixed rows from saved runs in cache_golden\\. No network.
"""

import unittest

# helpers must be imported first: it puts the app folder on the path.
from helpers import block_network

import compare
import evidence
import exa_client

ROWS = evidence.load_rows()
CHANNELS = evidence.load_channels()


def judged(row_id):
    """Run one fixed row from saved runs and judge it."""
    row = evidence.find_row(ROWS, row_id)
    result = evidence.check_row(row, CHANNELS, cache_only=True)
    return result, compare.judge(result)


class NormalizeTests(unittest.TestCase):

    def test_cusip(self):
        self.assertEqual(compare.normalize_cusip("68270C 202"), "68270C202")
        self.assertEqual(compare.normalize_cusip("68270c202"), "68270C202")
        self.assertEqual(compare.normalize_cusip("CUSIP No. 06051GLX5"), "06051GLX5")
        self.assertEqual(compare.normalize_cusip("316773 DD9"), "316773DD9")
        self.assertIsNone(compare.normalize_cusip("not stated"))

    def test_dates(self):
        self.assertEqual(compare.normalize_date("2026-09-29"), "2026-09-29")
        self.assertEqual(compare.normalize_date("Tuesday, September 29, 2026"), "2026-09-29")
        self.assertEqual(compare.normalize_date("12:01 a.m. Eastern Time on September 29, 2026"), "2026-09-29")
        self.assertEqual(compare.normalize_date("September 28, 2026, at 5:00 pm, Eastern Time"), "2026-09-28")
        self.assertEqual(compare.normalize_date("Sept. 25, 2026"), "2026-09-25")
        self.assertEqual(compare.normalize_date("9/15/2026"), "2026-09-15")
        self.assertIsNone(compare.normalize_date("not stated"))
        self.assertIsNone(compare.normalize_date("September 31, 2026"))

    def test_terms(self):
        self.assertEqual(compare.normalize_terms("one-for-ten (1-10)"), "1-for-10")
        self.assertEqual(compare.normalize_terms("1-for-10"), "1-for-10")
        self.assertEqual(compare.normalize_terms("1 for 10"), "1-for-10")
        self.assertEqual(compare.normalize_terms("1:10"), "1-for-10")
        self.assertEqual(compare.normalize_terms("one-for-twenty-five"), "1-for-25")
        self.assertEqual(
            compare.normalize_terms("from one (1) ADS representing ten (10) ordinary shares to one (1) ADS representing two hundred (200) ordinary shares"),
            "1 ADS = 200 shares",
        )
        self.assertEqual(compare.normalize_terms("100% of the principal amount"), "100% of principal")

    def test_window(self):
        self.assertTrue(compare.in_window("2026-09-25", "2026-08-29"))
        self.assertFalse(compare.in_window("2026-08-01", "2026-08-29"))
        self.assertTrue(compare.in_window(None, "2026-08-29"))


class LabelTests(unittest.TestCase):

    def setUp(self):
        block_network(self)

    def test_onmd_corroborated_after_cusip_space_removed(self):
        result, verdict = judged("ONMD")
        self.assertEqual(verdict["label"]["code"], "CORROBORATED")
        issuer_raw = result["channels"]["issuer"]["fields"]["new_cusip"]["value"]
        market_raw = result["channels"]["market"]["fields"]["new_cusip"]["value"]
        # The raw values differ; normalized they agree.
        self.assertNotEqual(issuer_raw, market_raw)
        cusip = next(c for c in verdict["comparisons"] if c["field"] == "new_cusip")
        self.assertEqual(cusip["verdict"], "agree")

    def test_cdt_single_issuer_with_date_note(self):
        _, verdict = judged("CDT")
        self.assertEqual(verdict["label"]["code"], "SINGLE_ISSUER")
        self.assertTrue(any("2026-09-28" in n and "2026-09-29" in n for n in verdict["label"]["notes"]))
        self.assertIn("field mapping", verdict["vendors"]["vendor_a"]["status"])
        self.assertEqual(verdict["vendors"]["vendor_b"]["status"], "matches the evidence")

    def test_bac_single_issuer(self):
        _, verdict = judged("BAC")
        self.assertEqual(verdict["label"]["code"], "SINGLE_ISSUER")
        self.assertEqual(verdict["vendors"]["resolved"], "2026-09-15")

    def test_ctnt_saved_run_is_repaired_one_source(self):
        _, verdict = judged("CTNT")
        self.assertEqual(verdict["label"]["code"], "STALE_REPAIRED")
        self.assertIn("analyst confirms", verdict["vendors"]["vendor_a"]["status"])

    def test_ctnt_with_empty_refetch_routes_to_analyst(self):
        # Replay the morning's empty "success" as the repair result.
        row = evidence.find_row(ROWS, "CTNT")
        result = evidence.check_row(row, CHANNELS, cache_only=True)
        body = {
            "urls": ["https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-677"],
            "highlights": True, "maxAgeHours": 0, "livecrawlTimeout": 12000,
        }
        env = exa_client.contents(body, cache_only=True)
        ok, reason, text = evidence.repair_outcome(env)
        result["repair"] = {"url": body["urls"][0], "body": body, "envelope": env, "ok": ok, "reason": reason, "text": text, "cusip": ""}
        verdict = compare.judge(result)
        self.assertEqual(verdict["label"]["code"], "NOT_CONFIRMED")
        self.assertIn("empty", verdict["label"]["reason"])

    def test_note_has_links_and_mock_line(self):
        _, verdict = judged("ONMD")
        self.assertIn("globenewswire.com", verdict["note"])
        self.assertIn("nasdaqtrader.com", verdict["note"])
        self.assertIn("mocked", verdict["note"])



class SpacedNumberWordTests(unittest.TestCase):
    """Nasdaq alert 2026-683 prints "one-for-twenty five (1-25)"."""

    def test_digits_in_brackets_win_over_a_spaced_word(self):
        # Before the fix this read as 1-for-20 and caused a false conflict.
        self.assertEqual(compare.normalize_terms("one-for-twenty five (1-25) reverse split"), "1-for-25")

    def test_a_bare_date_range_is_still_not_a_ratio(self):
        self.assertNotEqual(compare.normalize_terms("from 1-15 September"), "1-for-15")


if __name__ == "__main__":
    unittest.main()
