"""
helpers.py - shared setup for the tests.

WHAT THIS FILE DOES
  1. Puts the app folder on Python's search path, so the tests can
     "import exa_client", "import evidence" and "import compare".
  2. Offers block_network(), which makes any real HTTP call fail loudly,
     so no test can ever reach Exa or spend money by accident.
  3. Offers FakeResponse, a stand-in for a real HTTP response.

The tests read saved responses from cache_golden\\ only. They never
write to it.
"""

# sys and Path let us add the app folder to the import search path.
import sys
from pathlib import Path

# The project folder is one level above this tests folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Put the app folder first on the search path.
sys.path.insert(0, str(PROJECT_DIR / "app"))

# Now these imports find our own files.
import exa_client  # noqa: E402


def _no_network(*args, **kwargs):
    """Stand-in for requests.post that refuses to run."""
    raise AssertionError("a test tried to use the network")


def block_network(test_case):
    """Replace requests.post for one test, and restore it afterwards."""
    # Keep the real function so it can be put back.
    original = exa_client.requests.post
    exa_client.requests.post = _no_network
    # addCleanup runs the given function when the test finishes, pass or
    # fail. setattr(obj, "name", value) is the same as obj.name = value.
    test_case.addCleanup(setattr, exa_client.requests, "post", original)


class FakeResponse:
    """A pretend HTTP response with just the parts exa_client reads."""

    def __init__(self, status_code, payload, headers=None):
        # __init__ runs when a FakeResponse is created. "self" is the new
        # object; we store the values on it.
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = str(payload)

    def json(self):
        """Return the payload, as requests' .json() would."""
        return self._payload
