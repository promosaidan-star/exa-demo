"""
test_exa_client.py - tests for the cache folders, pricing and timeouts.

Every test points the two cache folders at a temporary folder, so the
real cache\\ and cache_golden\\ are never touched, and no test uses the
network.
"""

# tempfile makes a throwaway folder that is deleted after the test.
import tempfile

# json writes the pretend saved runs.
import json

# unittest is Python's built-in test framework. pytest can run it too.
import unittest

from pathlib import Path

# helpers must be imported first: it puts the app folder on the path.
from helpers import FakeResponse, block_network  # noqa: F401

import exa_client

# A small request body used by several tests.
BODY = {"query": "test query", "type": "auto", "contents": {"highlights": True}}


class CacheFolderTests(unittest.TestCase):
    """Fallback reads golden first; live writes go to the working folder only."""

    def setUp(self):
        # setUp runs before every test in this class.
        block_network(self)
        # A throwaway folder with a golden and a working folder inside.
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.golden = root / "golden"
        self.working = root / "working"
        self.golden.mkdir()
        self.working.mkdir()
        # Point exa_client at them, and put the real folders back after.
        for name, value in (("GOLDEN_DIR", self.golden), ("CACHE_DIR", self.working)):
            self.addCleanup(setattr, exa_client, name, getattr(exa_client, name))
            setattr(exa_client, name, value)

    def _save(self, folder, marker):
        """Write a pretend saved run for BODY into a folder."""
        path = exa_client.cache_path("/search", BODY, folder)
        record = {"saved_at": marker, "endpoint": "/search", "body": BODY, "elapsed_ms": 1, "data": {"requestId": marker}}
        path.write_text(json.dumps(record), encoding="utf-8")

    def test_fallback_reads_golden_before_working(self):
        self._save(self.golden, "golden-run")
        self._save(self.working, "working-run")
        env = exa_client.search(BODY, cache_only=True)
        self.assertEqual(env["source"], "cache")
        self.assertEqual(env["saved_from"], "golden")
        self.assertEqual(env["request_id"], "golden-run")

    def test_fallback_uses_working_when_no_golden(self):
        self._save(self.working, "working-run")
        env = exa_client.search(BODY, cache_only=True)
        self.assertEqual(env["saved_from"], "working")

    def test_live_write_goes_to_working_folder_only(self):
        # Pretend there is a key and that Exa answers at once.
        self.addCleanup(setattr, exa_client, "api_key", exa_client.api_key)
        exa_client.api_key = lambda: "test-key"
        self.addCleanup(setattr, exa_client.requests, "post", exa_client.requests.post)
        exa_client.requests.post = lambda *a, **k: FakeResponse(200, {"requestId": "live-1", "results": []})
        env = exa_client.search(BODY)
        self.assertEqual(env["source"], "live")
        self.assertTrue(exa_client.cache_path("/search", BODY, self.working).exists())
        self.assertFalse(exa_client.cache_path("/search", BODY, self.golden).exists())

    def test_failed_cache_write_still_returns_live_envelope(self):
        # Make the working "folder" a plain FILE, so saving into it fails.
        blocker = Path(self.tmp.name) / "not_a_folder"
        blocker.write_text("x", encoding="utf-8")
        exa_client.CACHE_DIR = blocker
        self.addCleanup(setattr, exa_client, "api_key", exa_client.api_key)
        exa_client.api_key = lambda: "test-key"
        self.addCleanup(setattr, exa_client.requests, "post", exa_client.requests.post)
        exa_client.requests.post = lambda *a, **k: FakeResponse(200, {"requestId": "live-2"})
        env = exa_client.search(BODY)
        self.assertEqual(env["source"], "live")
        self.assertTrue(env["cache_write_error"])

    def test_timeout_override_is_passed_through(self):
        seen = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            # Record the timeout the client used.
            seen["timeout"] = timeout
            return FakeResponse(200, {"requestId": "t"})

        self.addCleanup(setattr, exa_client, "api_key", exa_client.api_key)
        exa_client.api_key = lambda: "test-key"
        self.addCleanup(setattr, exa_client.requests, "post", exa_client.requests.post)
        exa_client.requests.post = fake_post
        exa_client.contents({"urls": ["https://example.com"], "highlights": True}, timeout=20)
        self.assertEqual(seen["timeout"], 20)
        # With no override, a body with no type gets 15 seconds.
        exa_client.contents({"urls": ["https://example.com/b"], "highlights": True})
        self.assertEqual(seen["timeout"], 15)


class PricingTests(unittest.TestCase):
    """/contents is priced as pages times content types, minimum one."""

    def test_contents_price_when_exa_sends_none(self):
        body = {"urls": ["https://a.com", "https://b.com"], "highlights": True, "text": True}
        env = exa_client._envelope(True, {"requestId": "x"}, body, "/contents", "live", 5)
        self.assertAlmostEqual(env["cost_dollars"], 0.004)

    def test_contents_default_counts_as_one_type(self):
        body = {"urls": ["https://a.com"]}
        env = exa_client._envelope(True, {"requestId": "x"}, body, "/contents", "live", 5)
        self.assertAlmostEqual(env["cost_dollars"], 0.001)

    def test_exa_cost_wins_when_present(self):
        data = {"requestId": "x", "costDollars": {"total": 0}}
        env = exa_client._envelope(True, data, {"urls": ["https://a.com"], "highlights": True}, "/contents", "live", 5)
        self.assertEqual(env["cost_dollars"], 0)

    def test_search_keeps_type_price(self):
        env = exa_client._envelope(True, {"requestId": "x"}, {"type": "deep-lite"}, "/search", "live", 5)
        self.assertAlmostEqual(env["cost_dollars"], 0.012)


if __name__ == "__main__":
    unittest.main()
