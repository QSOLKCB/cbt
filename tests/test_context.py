import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))

class ContextTests(unittest.TestCase):
    def test_validator(self):
        subprocess.run([sys.executable,str(ROOT/"tools"/"validate_context.py")],check=True)

    def test_claim_ledger_cli_validate(self):
        subprocess.run([sys.executable,str(ROOT/"tools"/"claim_ledger.py"),"validate"],check=True)

    def test_claim_freshness_gate_current_snapshot(self):
        subprocess.run([sys.executable,str(ROOT/"tools"/"claim_ledger.py"),"freshness","--as-of","2026-08-22","--fail-on-stale"],check=True)

    def test_claim_freshness_eventually_flags_review_due(self):
        proc=subprocess.run([sys.executable,str(ROOT/"tools"/"claim_ledger.py"),"freshness","--as-of","2028-12-31","--fail-on-stale"],capture_output=True,text=True)
        self.assertNotEqual(proc.returncode,0)
        self.assertIn("review_due",proc.stdout)

    def test_projection_is_deterministic_and_named(self):
        subprocess.run([sys.executable,str(ROOT/"tools"/"build_site_data.py")],check=True)
        out=ROOT/"site"/"data"/"context.bundle.js"; first=out.read_bytes()
        subprocess.run([sys.executable,str(ROOT/"tools"/"build_site_data.py")],check=True)
        self.assertEqual(first,out.read_bytes())
        text=out.read_text(encoding="utf-8")
        for key in ('"exercises":','"examples":','"claim_ledger":','"claim_conflicts":','"evidence_classes":','"source_snapshots":'):
            self.assertIn(key,text)
        subprocess.run([sys.executable,str(ROOT/"tools"/"build_site_data.py"),"--check"],check=True)

    def test_no_cure_language_in_core_position(self):
        b=load("ai/medical-claim-boundary.json")
        self.assertIn("a cure",b["core_position"]["cbt_is_not"])
        self.assertNotIn("a cure",b["core_position"]["cbt_is"])

    def test_phase2_exercises_present(self):
        self.assertTrue({"worry-time","graded-task-ladder","behavioural-experiment","setback-plan"}.issubset({x["id"] for x in load("exercises/index.json")["exercises"]}))

    def test_cognitive_work_route_dependency_present(self):
        ids={x["id"] for x in load("exercises/index.json")["exercises"]}
        self.assertIn("affect-to-action",ids)

    def test_every_exercise_has_mechanism_safety_plain_language_and_example(self):
        data=load("exercises/index.json"); plain=load("profiles/learning-accessibility.json")["plain_language_exercises"]; examples=load("examples/index.json")["examples"]
        for ex in data["exercises"]:
            for key in ("mechanism","not_established","pause_or_support"): self.assertTrue(ex[key])
            self.assertIn(ex["id"],plain); self.assertIn(ex["id"],examples)

    def test_example_mode_is_synthetic_and_separate(self):
        e=load("examples/index.json")
        self.assertIn("fictional",e["provenance"].lower())
        self.assertTrue(any("never reads user-entered answers" in x for x in e["rules"]))
        app=(ROOT/"site"/"app.js").read_text()
        self.assertIn("Synthetic example",app)
        self.assertIn("user answers untouched",app)

    def test_print_is_blank_accessible_and_keeps_safety_context(self):
        access=load("profiles/learning-accessibility.json")
        self.assertTrue(any("must not print user-entered answers" in x for x in access["principles"]))
        css=(ROOT/"site"/"styles.css").read_text(); app=(ROOT/"site"/"app.js").read_text()
        self.assertIn("@media print",css); self.assertIn("Print blank worksheet",app); self.assertIn('tabindex="0"',app)
        self.assertIn("Blank educational worksheet",app); self.assertIn("What this does not establish",app); self.assertIn("When to pause or seek support",app)

    def test_behavioural_experiment_is_low_risk_bounded(self):
        ex=next(x for x in load("exercises/index.json")["exercises"] if x["id"]=="behavioural-experiment")
        self.assertIn("low-stakes",ex["purpose"]); self.assertIn("dangerous exposure",ex["pause_or_support"])
        source=next(x for x in load("sources/public-sources.json")["sources"] if x["id"]=="uk.nhs.learninghub.behavioural-experiments")
        self.assertIn("Professional training material",source["scope_limitations"])

    def test_existing_privacy_and_neuroscience_guards_survive(self):
        app=(ROOT/"site"/"app.js").read_text(); self.assertIn("#exerciseForm textarea",app)
        work=load("profiles/cognitive-work-addendum.json")
        self.assertIn("move emotion into the prefrontal cortex",work["avoid_framing"])

    def test_cognitive_work_guardrails_are_rendered(self):
        app=(ROOT/"site"/"app.js").read_text()
        self.assertIn("w.mechanism_summary.map",app); self.assertIn("w.guardrails.map",app); self.assertIn("<h2>Guardrails</h2>",app)

    def test_about_restores_global_safety_guidance(self):
        app=(ROOT/"site"/"app.js").read_text()
        self.assertIn("Urgent safety or medical needs take priority over routine CBT exercises",app)

    def test_plain_language_toggle_rerenders_open_exercise_without_losing_draft(self):
        app=(ROOT/"site"/"app.js").read_text()
        self.assertIn("currentExerciseId",app); self.assertIn("exercise(currentExerciseId,draft)",app); self.assertIn("#exerciseForm textarea[data-i]",app)

    def test_phase3_claims_have_picoe_scope(self):
        ledger=load("claims/index.json")
        self.assertGreaterEqual(len(ledger["claims"]),8)
        classes={c["evidence_class"] for c in ledger["claims"]}
        self.assertTrue({"guideline_recommendation","systematic_review_meta_analysis","randomized_controlled_trial","public_education","archived_guideline"}.issubset(classes))
        for claim in ledger["claims"]:
            for field in ("population","intervention","comparator","outcome","evidence_class","jurisdiction","source_ids","snapshot_ids","not_established"):
                self.assertTrue(claim[field])

    def test_evidence_classes_are_not_a_fake_global_rank(self):
        data=load("claims/evidence-classes.json")
        self.assertTrue(data["no_global_rank"])
        self.assertIn("cannot_establish",data["classes"]["guideline_recommendation"])

    def test_conflict_bundles_preserve_evidence_instead_of_averaging(self):
        bundles=load("claims/conflicts.json")["bundles"]
        self.assertGreaterEqual(len(bundles),2)
        for bundle in bundles:
            self.assertTrue(bundle["preserve_all_observations"])
            self.assertTrue(bundle["do_not_average"])
            self.assertTrue(bundle["resolution_rule"])
        gad=next(b for b in bundles if b["id"]=="conflict.gad.aggregate-vs-delivery-format")
        self.assertEqual(gad["status"],"resolved_by_intervention_specificity")

    def test_archived_guidance_cannot_be_current(self):
        claim=next(c for c in load("claims/index.json")["claims"] if c["evidence_class"]=="archived_guideline")
        self.assertEqual(claim["status"],"historical_reference_only")
        self.assertIn("must not be represented as current", " ".join(claim["not_established"]))

    def test_snapshots_are_metadata_only_and_fingerprinted(self):
        snaps=load("sources/snapshots/manifest.json")
        raw=json.dumps(snaps).lower()
        for forbidden in ('"full_text"','"article_text"','"transcript"'):
            self.assertNotIn(forbidden,raw)
        for snap in snaps["records"]:
            self.assertTrue(snap["metadata_sha256"].startswith("sha256:"))
            self.assertIn("not a hash or copy of remote full text",snap["fingerprint_scope"])

if __name__=="__main__":
    unittest.main()
