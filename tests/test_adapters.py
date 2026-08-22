import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_model_adapters.py"

class AdapterProjectionTests(unittest.TestCase):
    def run_builder(self, *args, check=True):
        return subprocess.run([sys.executable, str(BUILDER), *args], check=check, capture_output=True, text=True)

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

    def test_retrieval_bundle_carries_canonical_paths_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out))
            bundle = (out / "retrieval-bundle.txt").read_text(encoding="utf-8")
            for path in (
                "ai/bootstrap.json",
                "claims/index.json",
                "claims/conflicts.json",
                "sources/snapshots/manifest.json",
                "exercises/index.json",
            ):
                self.assertIn(f"canonical_path: {path}", bundle)
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

    def test_manifest_hashes_generated_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.run_builder("--output-dir", str(out), "--verify")
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["projection_only"])
            self.assertFalse(manifest["canonical_evidence"])
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
