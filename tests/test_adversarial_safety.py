import importlib.util
import json
import shutil
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


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


class AdversarialSafetyTests(unittest.TestCase):
    def run_runner(self, *args, check=True):
        return subprocess.run([sys.executable, str(RUNNER), *args], check=check, capture_output=True, text=True)

    def temp_repo(self):
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name) / "repo"
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "generated", "__pycache__"))
        return tmp, repo

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

    def test_prompt_pack_is_deterministic_and_hides_all_rubric_labels(self):
        suite = json.loads((ROOT / "evals" / "adversarial-safety" / "cases.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "prompts.jsonl"
            self.run_runner("render", "--output", str(out))
            first = out.read_bytes()
            self.run_runner("render", "--output", str(out), "--check")
            self.assertEqual(first, out.read_bytes())
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(set(row), {"case_id", "prompt", "instruction"})
                self.assertTrue(row["case_id"].startswith("case-"))
            rendered_ids = {row["case_id"] for row in rows}
            semantic_ids = {case["id"] for case in suite["cases"]}
            self.assertTrue(rendered_ids.isdisjoint(semantic_ids))
            text = out.read_text(encoding="utf-8")
            for hidden_key in ("must_true", "must_false", "required_invariants", "category", "attack_style", "subcontext"):
                self.assertNotIn(f'"{hidden_key}"', text)

    def test_self_test_detects_one_failure_per_category(self):
        self.assertIn("self-test: ok", self.run_runner("self-test").stdout)

    def test_structured_scorer_accepts_reference_conformance(self):
        module = load_module()
        rows = module.synthetic_pass_rows(ROOT)
        self.assertEqual(module.score_rows(rows, ROOT), [])

    def test_structured_scorer_rejects_cure_violation(self):
        module = load_module()
        rows = module.synthetic_pass_rows(ROOT)
        target = module.opaque_case_id("cure.direct")
        row = next(item for item in rows if item["case_id"] == target)
        row["observations"]["cure_claim"] = True
        errors = module.score_rows([row], ROOT, require_all=False)
        self.assertTrue(any("cure_claim=false" in error for error in errors))

    def test_scorer_rejects_unlisted_global_hard_guard_violations(self):
        module = load_module()
        rows = module.synthetic_pass_rows(ROOT)
        target = module.opaque_case_id("medication.stop-now")
        row = next(item for item in rows if item["case_id"] == target)
        row["observations"]["diagnosis_asserted"] = True
        row["observations"]["hidden_profile_inference"] = True
        errors = module.score_rows([row], ROOT, require_all=False)
        self.assertTrue(any("diagnosis_asserted=false" in error for error in errors))
        self.assertTrue(any("hidden_profile_inference=false" in error for error in errors))

    def test_acute_risk_has_dedicated_risk_clearance_observation(self):
        module = load_module()
        suite = json.loads((ROOT / "evals" / "adversarial-safety" / "cases.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "evals" / "adversarial-safety" / "response-envelope.schema.json").read_text(encoding="utf-8"))
        self.assertIn("risk_clearance_asserted", suite["observation_flags"])
        self.assertIn("risk_clearance_asserted", schema["properties"]["observations"]["required"])
        acute = [case for case in suite["cases"] if case["category"] == "acute_risk_interruption"]
        self.assertTrue(all("risk_clearance_asserted" in case["expected"]["must_false"] for case in acute))
        rows = module.synthetic_pass_rows(ROOT)
        target = module.opaque_case_id("acute.risk-clearance")
        row = next(item for item in rows if item["case_id"] == target)
        row["observations"]["risk_clearance_asserted"] = True
        self.assertTrue(any("risk_clearance_asserted=false" in error for error in module.score_rows([row], ROOT, require_all=False)))

    def test_invariant_registry_cannot_authorize_itself(self):
        module = load_module()
        tmp, repo = self.temp_repo()
        try:
            path = repo / "evals" / "adversarial-safety" / "invariants.json"
            registry = json.loads(path.read_text(encoding="utf-8"))
            registry["invariants"]["no_cure"] = {
                "source": "evals/adversarial-safety/cases.json",
                "path": ["type"],
                "equals": "cbt-adversarial-safety-suite",
            }
            write_json(path, registry)
            errors = module.validate_suite(repo)
            self.assertTrue(any("not an approved canonical" in error for error in errors))
        finally:
            tmp.cleanup()

    def test_bootstrap_loads_high_risk_policy_before_context(self):
        bootstrap = json.loads((ROOT / "ai" / "bootstrap.json").read_text(encoding="utf-8"))
        order = bootstrap["load_order"]
        self.assertIn("ai/high-risk-boundary-policy.json", order)
        self.assertLess(order.index("ai/high-risk-boundary-policy.json"), order.index("profiles/cbt-context.json"))
        self.assertFalse(bootstrap["evaluation_interfaces"]["adversarial_safety"]["canonical"])

    def test_model_adapters_carry_complete_high_risk_policy(self):
        policy = json.loads((ROOT / "ai" / "high-risk-boundary-policy.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            subprocess.run([sys.executable, str(ADAPTER_BUILDER), "--output-dir", str(out), "--verify"], check=True, capture_output=True, text=True)
            generic = (out / "generic-system-prompt.txt").read_text(encoding="utf-8")
            compact = (out / "local-compact.txt").read_text(encoding="utf-8")
            openai = json.loads((out / "openai-responses.json").read_text(encoding="utf-8"))
            all_rules = policy["hard_guards"] + policy["general_rules"] + policy["privacy_rules"] + policy["productivity_rules"]
            for rules in policy["condition_boundaries"].values():
                all_rules.extend(rules)
            for rule in all_rules:
                self.assertIn(rule, generic)
                self.assertIn(rule, compact)
                self.assertIn(rule, openai["instructions"])

    def test_eval_fixtures_never_become_canonical_evidence(self):
        bootstrap = json.loads((ROOT / "ai" / "bootstrap.json").read_text(encoding="utf-8"))
        routed = list(bootstrap["load_order"])
        for paths in bootstrap["routed_records"].values():
            routed.extend(paths)
        self.assertFalse(any(path.startswith("evals/") for path in routed))
        ledger = json.loads((ROOT / "claims" / "index.json").read_text(encoding="utf-8"))
        for claim in ledger["claims"]:
            refs = claim["source_ids"] + claim["snapshot_ids"]
            self.assertFalse(any(str(ref).startswith("evals/") for ref in refs))

    def test_acute_risk_fixtures_are_non_method_specific(self):
        suite = json.loads((ROOT / "evals" / "adversarial-safety" / "cases.json").read_text(encoding="utf-8"))
        acute = [case["prompt"].lower() for case in suite["cases"] if case["category"] == "acute_risk_interruption"]
        for prompt in acute:
            for marker in ["dosage", "weapon", "ligature", "lethal dose", "method steps"]:
                self.assertNotIn(marker, prompt)


if __name__ == "__main__":
    unittest.main()
