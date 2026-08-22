import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_model_adapters.py"


def load_builder_module():
    spec = importlib.util.spec_from_file_location("cbt_model_adapter_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AdapterProjectionTests(unittest.TestCase):
    def run_builder(self, *args, check=True):
        return subprocess.run([sys.executable, str(BUILDER), *args], check=check, capture_output=True, text=True)

    def temp_repo(self):
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name) / "repo"
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "generated", "__pycache__"))
        return tmp, repo

    def test_adapter_projection_determinism(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            pa, pb = Path(a), Path(b)
            self.run_builder("--output-dir", str(pa), "--verify")
            self.run_builder("--output-dir", str(pb), "--verify")
            names = sorted(p.name for p in pa.iterdir())
            self.assertEqual(names, sorted(p.name for p in pb.iterdir()))
            for name in names:
                self.assertEqual((pa / name).read_bytes(), (pb / name).read_bytes(), name)

    def test_builder_self_determinism_check(self):
        proc = self.run_builder("--determinism-check")
        self.assertIn("determinism: ok", proc.stdout)

    def test_projection_spec_controls_output_interface(self):
        module = load_builder_module()
        tmp, repo = self.temp_repo()
        try:
            module.ROOT = repo
            spec_path = repo / "adapters" / "projection-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["outputs"]["generic_system_prompt"]["filename"] = "renamed-generic.txt"
            spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            out = repo / "tmp-adapters"
            module.write_outputs(out)
            self.assertTrue((out / "renamed-generic.txt").exists())
            self.assertFalse((out / "generic-system-prompt.txt").exists())
            self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(module.output_names()))
        finally:
            tmp.cleanup()

    def test_retrieval_inputs_derive_from_bootstrap_routes(self):
        module = load_builder_module()
        tmp, repo = self.temp_repo()
        try:
            module.ROOT = repo
            bootstrap_path = repo / "ai" / "bootstrap.json"
            bootstrap = json.loads(bootstrap_path.read_text(encoding="utf-8"))
            bootstrap["routed_records"]["cbt_overview"].append("README4AI.md")
            bootstrap_path.write_text(json.dumps(bootstrap, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            inputs = set(module.canonical_inputs())
            self.assertIn("README4AI.md", inputs)
            bundle = module.build_retrieval_bundle()
            self.assertIn("canonical_path: README4AI.md", bundle)
        finally:
            tmp.cleanup()

    def test_openai_responses_adapter_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out), "--verify")
            data = json.loads((out / "openai-responses.json").read_text(encoding="utf-8"))
            self.assertTrue(data["projection_only"])
            self.assertFalse(data["canonical_evidence"])
            self.assertEqual(data["transport"]["api_family"], "Responses API")
            self.assertEqual(data["request_template"]["tools"][0]["type"], "file_search")
            self.assertIn("instructions", data["request_template"])
            self.assertNotIn("api_key", json.dumps(data).lower())

    def test_generic_and_local_prompts_preserve_complete_safety_policy(self):
        safety = json.loads((ROOT / "ai" / "safety-escalation-policy.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out), "--verify")
            generic = (out / "generic-system-prompt.txt").read_text(encoding="utf-8")
            compact = (out / "local-compact.txt").read_text(encoding="utf-8")
            openai = json.loads((out / "openai-responses.json").read_text(encoding="utf-8"))
            for rule in safety["pause_routine_exercise_when"] + safety["response_rules"] + safety["non_urgent_boundary"]:
                self.assertIn(rule, generic)
                self.assertIn(rule, compact)
                self.assertIn(rule, openai["instructions"])

    def test_generic_prompt_preserves_core_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out))
            prompt = (out / "generic-system-prompt.txt").read_text(encoding="utf-8")
            for marker in (
                "PROJECTION_ONLY: true",
                "CANONICAL_EVIDENCE: false",
                "CBT != CURE",
                "AI_CONTEXT != DIAGNOSIS",
                "PROJECTION != CANONICAL_SOURCE",
                "urgent safety needs override routine CBT exercises",
            ):
                self.assertIn(marker, prompt)

    def test_retrieval_bundle_carries_all_bootstrap_paths_and_hashes(self):
        bootstrap = json.loads((ROOT / "ai" / "bootstrap.json").read_text(encoding="utf-8"))
        expected = {"ai/bootstrap.json", *bootstrap["load_order"]}
        for paths in bootstrap["routed_records"].values():
            expected.update(paths)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out))
            bundle = (out / "retrieval-bundle.txt").read_text(encoding="utf-8")
            for path in expected:
                self.assertIn(f"canonical_path: {path}", bundle)
            self.assertEqual(bundle.count("canonical_path: "), len(expected))
            self.assertIn("canonical_sha256: sha256:", bundle)
            self.assertIn("projection_only: true", bundle)

    def test_local_projection_is_compact_and_requires_canonical_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out))
            compact = (out / "local-compact.txt").read_text(encoding="utf-8")
            self.assertLess(len(compact.encode("utf-8")), 12000)
            self.assertIn("retrieve canonical claims/index.json", compact)
            self.assertIn("This compact projection is not evidence.", compact)

    def test_manifest_hashes_generated_outputs_and_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out), "--verify")
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["projection_only"])
            self.assertFalse(manifest["canonical_evidence"])
            self.assertEqual(manifest["projection_spec"]["path"], "adapters/projection-spec.json")
            self.assertTrue(manifest["projection_spec"]["sha256"].startswith("sha256:"))
            output_paths = {row["path"] for row in manifest["outputs"]}
            self.assertEqual(
                output_paths,
                {
                    "adapters/generated/generic-system-prompt.txt",
                    "adapters/generated/openai-responses.json",
                    "adapters/generated/retrieval-bundle.txt",
                    "adapters/generated/local-compact.txt",
                },
            )

    def test_snapshot_metadata_url_cannot_reference_generated_projection(self):
        module = load_builder_module()
        tmp, repo = self.temp_repo()
        try:
            module.ROOT = repo
            snap_path = repo / "sources" / "snapshots" / "manifest.json"
            snaps = json.loads(snap_path.read_text(encoding="utf-8"))
            snaps["records"][0]["observed_metadata"]["url"] = "adapters/generated/retrieval-bundle.txt"
            snap_path.write_text(json.dumps(snaps, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            errors = module.verify_noncanonical_boundaries()
            self.assertTrue(any("observed metadata URL" in error for error in errors))
        finally:
            tmp.cleanup()

    def test_generated_adapters_are_not_canonical_dependencies(self):
        bootstrap = json.loads((ROOT / "ai" / "bootstrap.json").read_text(encoding="utf-8"))
        routed = list(bootstrap["load_order"])
        for paths in bootstrap["routed_records"].values():
            routed.extend(paths)
        self.assertFalse(any(path.startswith("adapters/generated/") for path in routed))
        ledger = json.loads((ROOT / "claims" / "index.json").read_text(encoding="utf-8"))
        for claim in ledger["claims"]:
            refs = claim["source_ids"] + claim["snapshot_ids"]
            self.assertFalse(any(str(ref).startswith("adapters/generated/") for ref in refs))
        proc = self.run_builder("--determinism-check")
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
