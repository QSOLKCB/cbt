import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "adversarial_safety.py"
ADAPTER_BUILDER = ROOT / "tools" / "build_model_adapters.py"


def load_module():
    spec = importlib.util.spec_from_file_location("cbt_adversarial_safety", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AdversarialSafetyTests(unittest.TestCase):
    def run_runner(self, *args, check=True):
        return subprocess.run([sys.executable, str(RUNNER), *args], check=check, capture_output=True, text=True)

    def test_suite_validates_and_covers_all_phase5_categories(self):
        proc = self.run_runner("validate")
        self.assertIn("suite: ok", proc.stdout)
        suite = json.loads((ROOT / "evals" / "adversarial-safety" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(set(suite["categories"]), {"cure_language_pressure","diagnostic_certainty_pressure","medication_change_requests","coercive_reframing_victim_blaming","high_risk_clinical_boundaries","acute_risk_interruption","privacy_hidden_profiling","productivity_at_any_cost"})
        self.assertGreaterEqual(len(suite["cases"]), 20)

    def test_high_risk_subcontexts_are_complete(self):
        suite = json.loads((ROOT / "evals" / "adversarial-safety" / "cases.json").read_text(encoding="utf-8"))
        subcontexts = {case["subcontext"] for case in suite["cases"] if case["category"] == "high_risk_clinical_boundaries"}
        self.assertEqual(subcontexts, {"trauma","possible_psychosis","possible_mania","eating_disorder","substance_use"})

    def test_prompt_pack_is_deterministic_and_hides_expected_rubric(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "prompts.jsonl"
            self.run_runner("render", "--output", str(out)); first = out.read_bytes()
            self.run_runner("render", "--output", str(out), "--check"); second = out.read_bytes()
            self.assertEqual(first, second)
            text = out.read_text(encoding="utf-8")
            self.assertNotIn('"must_true"', text); self.assertNotIn('"must_false"', text); self.assertNotIn('"required_invariants"', text)

    def test_self_test_detects_one_failure_per_category(self):
        self.assertIn("self-test: ok", self.run_runner("self-test").stdout)

    def test_structured_scorer_accepts_reference_conformance(self):
        module = load_module(); rows = module.synthetic_pass_rows(ROOT)
        self.assertEqual(module.score_rows(rows, ROOT), [])

    def test_structured_scorer_rejects_cure_violation(self):
        module = load_module(); rows = module.synthetic_pass_rows(ROOT)
        row = next(item for item in rows if item["case_id"] == "cure.direct"); row["observations"]["cure_claim"] = True
        errors = module.score_rows([row], ROOT, require_all=False)
        self.assertTrue(any("cure_claim=false" in error for error in errors))

    def test_bootstrap_loads_high_risk_policy_before_context(self):
        bootstrap = json.loads((ROOT / "ai" / "bootstrap.json").read_text(encoding="utf-8")); order = bootstrap["load_order"]
        self.assertIn("ai/high-risk-boundary-policy.json", order)
        self.assertLess(order.index("ai/high-risk-boundary-policy.json"), order.index("profiles/cbt-context.json"))
        self.assertFalse(bootstrap["evaluation_interfaces"]["adversarial_safety"]["canonical"])

    def test_model_adapters_carry_high_risk_guards_and_rules(self):
        policy = json.loads((ROOT / "ai" / "high-risk-boundary-policy.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            subprocess.run([sys.executable, str(ADAPTER_BUILDER), "--output-dir", str(out), "--verify"], check=True, capture_output=True, text=True)
            generic = (out / "generic-system-prompt.txt").read_text(encoding="utf-8"); compact = (out / "local-compact.txt").read_text(encoding="utf-8")
            openai = json.loads((out / "openai-responses.json").read_text(encoding="utf-8"))
            for guard in policy["hard_guards"]:
                self.assertIn(guard, generic); self.assertIn(guard, compact); self.assertIn(guard, openai["instructions"])
            for rule in policy["general_rules"]:
                self.assertIn(rule, generic); self.assertIn(rule, compact); self.assertIn(rule, openai["instructions"])

    def test_eval_fixtures_never_become_canonical_evidence(self):
        bootstrap = json.loads((ROOT / "ai" / "bootstrap.json").read_text(encoding="utf-8")); routed = list(bootstrap["load_order"])
        for paths in bootstrap["routed_records"].values(): routed.extend(paths)
        self.assertFalse(any(path.startswith("evals/") for path in routed))
        ledger = json.loads((ROOT / "claims" / "index.json").read_text(encoding="utf-8"))
        for claim in ledger["claims"]:
            refs = claim["source_ids"] + claim["snapshot_ids"]
            self.assertFalse(any(str(ref).startswith("evals/") for ref in refs))

    def test_acute_risk_fixtures_are_non_method_specific(self):
        suite = json.loads((ROOT / "evals" / "adversarial-safety" / "cases.json").read_text(encoding="utf-8"))
        acute = [case["prompt"].lower() for case in suite["cases"] if case["category"] == "acute_risk_interruption"]
        for prompt in acute:
            for marker in ["dosage","weapon","ligature","lethal dose","method steps"]: self.assertNotIn(marker, prompt)


if __name__ == "__main__": unittest.main()
