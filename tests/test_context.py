import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class ContextTests(unittest.TestCase):
    def test_validator(self):
        subprocess.run([sys.executable, str(ROOT/"tools"/"validate_context.py")], check=True)

    def test_projection_is_deterministic(self):
        subprocess.run([sys.executable, str(ROOT/"tools"/"build_site_data.py")], check=True)
        first = (ROOT/"site"/"data"/"context.bundle.js").read_bytes()
        subprocess.run([sys.executable, str(ROOT/"tools"/"build_site_data.py")], check=True)
        second = (ROOT/"site"/"data"/"context.bundle.js").read_bytes()
        self.assertEqual(first, second)
        subprocess.run([sys.executable, str(ROOT/"tools"/"build_site_data.py"), "--check"], check=True)

    def test_no_cure_language_in_core_position(self):
        boundary = load("ai/medical-claim-boundary.json")
        self.assertIn("a cure", boundary["core_position"]["cbt_is_not"])
        self.assertNotIn("a cure", boundary["core_position"]["cbt_is"])

    def test_self_help_is_not_clinical_equivalence(self):
        profile = load("profiles/cbt-context.json")
        self.assertIn("not automatically equivalent", profile["clinical_boundary"]["not_equivalent"])

    def test_cognitive_work_caveat(self):
        work = load("profiles/cognitive-work-addendum.json")
        self.assertIn("move emotion into the prefrontal cortex", work["avoid_framing"])
        self.assertTrue(any("productivity guarantee" in x for x in work["mechanism_summary"]))

    def test_every_exercise_explains_mechanism(self):
        data = load("exercises/index.json")
        for ex in data["exercises"]:
            self.assertTrue(ex["mechanism"])
            self.assertTrue(ex["not_established"])

if __name__ == "__main__":
    unittest.main()
