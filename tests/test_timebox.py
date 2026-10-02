"""
test_timebox.py - the screen must get control back at the timebox.

A mocked Exa call that would take 20 seconds must hand control back in
about the timebox, show the saved run with the reason, and let the late
thread finish in the background and save to the working folder only.
Both cache folders point at a temporary folder. No network.
"""

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

# helpers must be imported first: it puts the app folder on the path.
from helpers import FakeResponse, block_network

import evidence
import exa_client

ROWS = evidence.load_rows()
CHANNELS = evidence.load_channels()


class TimeboxTests(unittest.TestCase):

    def setUp(self):
        block_network(self)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.golden = root / "golden"
        self.working = root / "working"
        self.golden.mkdir()
        self.working.mkdir()
        self.row = evidence.find_row(ROWS, "ONMD")
        # Copy the real saved runs for ONMD into the temporary golden folder
        # BEFORE pointing exa_client at it.
        for channel in ("issuer", "market"):
            body = evidence.build_search_body(self.row, channel, CHANNELS)
            real = exa_client.cache_path("/search", body, exa_client.GOLDEN_DIR)
            (self.golden / real.name).write_text(real.read_text(encoding="utf-8"), encoding="utf-8")
        for name, value in (("GOLDEN_DIR", self.golden), ("CACHE_DIR", self.working)):
            self.addCleanup(setattr, exa_client, name, getattr(exa_client, name))
            setattr(exa_client, name, value)
        self.addCleanup(setattr, exa_client, "api_key", exa_client.api_key)
        exa_client.api_key = lambda: "test-key"

    def test_slow_call_returns_at_timebox_with_saved_run(self):
        # An Event is a flag threads can wait on. The fake market call
        # waits on it for up to 20 seconds, like a stuck request.
        release = threading.Event()
        # Make sure the stuck thread is always let go, pass or fail.
        self.addCleanup(release.set)

        def fake_post(url, headers=None, json=None, timeout=None):
            if "Corporate Actions Alert" in json["query"]:
                release.wait(20)
            return FakeResponse(200, {"requestId": "late-or-fast", "results": []})

        self.addCleanup(setattr, exa_client.requests, "post", exa_client.requests.post)
        exa_client.requests.post = fake_post

        ticks = []
        started = time.perf_counter()
        run = evidence.run_row(self.row, CHANNELS, timebox_s=1, on_tick=lambda s, st: ticks.append(s))
        took = time.perf_counter() - started

        # Control came back in about the timebox, not 20 seconds.
        self.assertLess(took, 2.5)
        # The screen was updated while waiting.
        self.assertTrue(ticks)
        market = run["envelopes"]["market"]
        self.assertEqual(market["source"], "cache")
        self.assertEqual(market["saved_from"], "golden")
        self.assertIn("still running past 1 s", market["error"])
        # The fast channel came back live.
        self.assertEqual(run["envelopes"]["issuer"]["source"], "live")

        # Let the late thread finish; it saves to the working folder only.
        market_body = run["bodies"]["market"]
        golden_file = exa_client.cache_path("/search", market_body, self.golden)
        golden_before = golden_file.read_text(encoding="utf-8")
        release.set()
        working_file = exa_client.cache_path("/search", market_body, self.working)
        deadline = time.time() + 5
        while not working_file.exists() and time.time() < deadline:
            time.sleep(0.05)
        self.assertTrue(working_file.exists())
        self.assertEqual(json.loads(working_file.read_text(encoding="utf-8"))["data"]["requestId"], "late-or-fast")
        # The golden copy is untouched.
        self.assertEqual(golden_file.read_text(encoding="utf-8"), golden_before)

    def test_simulate_timeout_drill_in_saved_mode(self):
        # Shorten the drill's delay so the test process does not wait 20 s
        # at exit for the sleeping thread.
        self.addCleanup(setattr, evidence, "SIMULATED_DELAY_S", evidence.SIMULATED_DELAY_S)
        evidence.SIMULATED_DELAY_S = 3
        started = time.perf_counter()
        run = evidence.run_row(self.row, CHANNELS, timebox_s=1, cache_only=True, simulate_timeout=True)
        self.assertLess(time.perf_counter() - started, 2.5)
        self.assertIn("still running past", run["envelopes"]["market"]["error"])
        self.assertEqual(run["envelopes"]["issuer"]["error"], "")


if __name__ == "__main__":
    unittest.main()
