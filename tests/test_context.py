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

    def test_self_help_route_loads_source_registry(self):
        bootstrap = load("ai/bootstrap.json")
        self.assertIn("sources/public-sources.json", bootstrap["routed_records"]["cbt_self_help"])

    def test_cognitive_work_caveat(self):
        work = load("profiles/cognitive-work-addendum.json")
        self.assertIn("move emotion into the prefrontal cortex", work["avoid_framing"])
        self.assertTrue(any("productivity guarantee" in x for x in work["mechanism_summary"]))
        self.assertTrue(work["evidence_scope"])
        self.assertTrue(any("do not generalise laboratory neuroimaging findings" in x for x in work["guardrails"]))

    def test_neuroscience_sources_preserve_scope(self):
        sources = load("sources/public-sources.json")
        neuro = [s for s in sources["sources"] if s["class"] == "peer_reviewed_pubmed"]
        self.assertGreaterEqual(len(neuro), 2)
        for source in neuro:
            self.assertTrue(source["population"])
            self.assertTrue(source["design"])
            self.assertTrue(source["scope_limitations"])

    def test_every_exercise_explains_mechanism_and_safety(self):
        data = load("exercises/index.json")
        for ex in data["exercises"]:
            self.assertTrue(ex["mechanism"])
            self.assertTrue(ex["not_established"])
            self.assertTrue(ex["pause_or_support"])

    def test_site_has_missing_bundle_and_clear_guards(self):
        app = (ROOT/"site"/"app.js").read_text(encoding="utf-8")
        self.assertIn("if (!ctx)", app)
        self.assertIn("#exerciseForm textarea", app)
        self.assertIn("When to pause or seek support", app)

if __name__ == "__main__":
    unittest.main()
