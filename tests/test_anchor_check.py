import json
import unittest
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from anchor_check import anchor_present, fetch_plaintext

class AnchorPresentTests(unittest.TestCase):
    def test_verbatim_match(self):
        self.assertTrue(anchor_present("deadliest animal family",
                                       "the deadliest animal family in the world"))

    def test_whitespace_normalized(self):
        self.assertTrue(anchor_present("deadliest  animal family",
                                       "the deadliest\nanimal   family in the world"))

    def test_case_sensitive_miss(self):
        self.assertFalse(anchor_present("Deadliest Animal Family",
                                        "the deadliest animal family in the world"))

    def test_absent(self):
        self.assertFalse(anchor_present("flying turtles", "no such thing here"))

class FetchPlaintextTests(unittest.TestCase):
    def test_parses_mediawiki_extract(self):
        payload = json.dumps({"query": {"pages": [{"extract": "Full article text."}]}})
        def fake_fetch(url):
            self.assertIn("en.wikipedia.org/w/api.php", url)
            self.assertIn("explaintext", url)
            return payload
        self.assertEqual(fetch_plaintext("Mosquito", fetch=fake_fetch),
                         "Full article text.")

    def test_missing_page_returns_empty(self):
        payload = json.dumps({"query": {"pages": []}})
        self.assertEqual(fetch_plaintext("Nope", fetch=lambda url: payload), "")

if __name__ == "__main__":
    unittest.main()
