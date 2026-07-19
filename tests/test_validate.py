import json
import unittest
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from validate import validate_batch

def good(**overrides):
    q = {
        "id": "3f2c9b1e-8a41-4a5e-9c11-2f6d0e7b5a10",
        "date": "2026-07-20",
        "format": "two",
        "question": "Which is closer to the Sun on average?",
        "choices": ["Mercury", "The corona's outer edge"],
        "correctIndex": 1,
        "articleTitle": "Solar corona",
        "articleURL": "https://en.wikipedia.org/wiki/Stellar_corona",
        "anchorText": "extends millions of kilometres into outer space",
        "thumbnailURL": "https://upload.wikimedia.org/example.jpg",
        "attribution": "Text from Wikipedia, CC BY-SA 4.0",
    }
    q.update(overrides)
    return q

class ValidateTests(unittest.TestCase):
    def test_valid_batch_passes(self):
        self.assertEqual(validate_batch([good()], set()), [])

    def test_missing_field_fails(self):
        q = good()
        del q["anchorText"]
        self.assertTrue(validate_batch([q], set()))

    def test_bad_format_fails(self):
        self.assertTrue(validate_batch([good(format="five")], set()))

    def test_choice_count_must_match_format(self):
        self.assertTrue(validate_batch([good(format="four")], set()))  # only 2 choices
        self.assertEqual(validate_batch([good(format="four",
            choices=["A", "B", "C", "D"], correctIndex=3)], set()), [])

    def test_tf_requires_true_false_labels(self):
        self.assertTrue(validate_batch([good(format="tf", choices=["Yes", "No"])], set()))
        self.assertEqual(validate_batch([good(format="tf",
            choices=["True", "False"], correctIndex=0)], set()), [])

    def test_correct_index_bounds(self):
        self.assertTrue(validate_batch([good(correctIndex=2)], set()))

    def test_article_url_must_be_enwiki(self):
        self.assertTrue(validate_batch([good(articleURL="https://example.com/x")], set()))

    def test_anchor_word_count(self):
        self.assertTrue(validate_batch([good(anchorText="too short")], set()))
        self.assertTrue(validate_batch([good(anchorText=" ".join(["w"] * 21))], set()))

    def test_duplicate_id_within_batch_fails(self):
        self.assertTrue(validate_batch([good(), good()], set()))

    def test_id_collision_with_existing_fails(self):
        self.assertTrue(validate_batch([good()], {"3f2c9b1e-8a41-4a5e-9c11-2f6d0e7b5a10"}))

    def test_bad_date_fails(self):
        self.assertTrue(validate_batch([good(date="20-07-2026")], set()))

if __name__ == "__main__":
    unittest.main()
