import json
import tempfile
import unittest
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from assemble import assemble
from test_validate import good

class AssembleTests(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        (self.dir / "content").mkdir()
        (self.dir / "work").mkdir()

    def write_survivors(self, questions):
        (self.dir / "work" / "survivors.json").write_text(json.dumps(questions))

    def test_publishes_batch_and_manifest(self):
        self.write_survivors([good()])
        self.assertEqual(assemble("2026-07-20.json", root=self.dir), 0)
        batch = json.loads((self.dir / "content" / "2026-07-20.json").read_text())
        self.assertEqual(len(batch), 1)
        manifest = json.loads((self.dir / "manifest.json").read_text())
        self.assertEqual(manifest, {"batches": ["2026-07-20.json"]})

    def test_appends_to_existing_manifest(self):
        (self.dir / "manifest.json").write_text(json.dumps({"batches": ["old.json"]}))
        self.write_survivors([good()])
        assemble("new.json", root=self.dir)
        manifest = json.loads((self.dir / "manifest.json").read_text())
        self.assertEqual(manifest["batches"], ["old.json", "new.json"])

    def test_zero_survivors_exits_3_publishes_nothing(self):
        self.write_survivors([])
        self.assertEqual(assemble("2026-07-20.json", root=self.dir), 3)
        self.assertFalse((self.dir / "content" / "2026-07-20.json").exists())
        self.assertFalse((self.dir / "manifest.json").exists())

    def test_id_collision_with_published_fails(self):
        (self.dir / "content" / "old.json").write_text(json.dumps([good()]))
        self.write_survivors([good()])  # same id
        self.assertEqual(assemble("new.json", root=self.dir), 1)
        self.assertFalse((self.dir / "content" / "new.json").exists())

if __name__ == "__main__":
    unittest.main()
