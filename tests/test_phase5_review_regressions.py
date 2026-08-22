import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


class Phase5ReviewRegressionTests(unittest.TestCase):
    def temp_repo(self):
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name) / "repo"
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "generated", "__pycache__"))
        return tmp, repo

    def run_validator(self, repo: Path):
        return subprocess.run(
            [sys.executable, str(repo / "tools" / "validate_context.py")],
            capture_output=True,
            text=True,
        )

    def test_context_validator_rejects_missing_peer_reviewed_scope_metadata(self):
        tmp, repo = self.temp_repo()
        try:
            source_path = repo / "sources" / "public-sources.json"
            sources = json.loads(source_path.read_text(encoding="utf-8"))
            source = next(item for item in sources["sources"] if item["class"] == "peer_reviewed_pubmed")
            source.pop("population")
            write_json(source_path, sources)
            proc = self.run_validator(repo)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("missing population", proc.stdout + proc.stderr)
        finally:
            tmp.cleanup()

    def test_context_validator_rejects_drifted_evaluation_interface_paths(self):
        tmp, repo = self.temp_repo()
        try:
            original = repo / "evals" / "adversarial-safety" / "cases.json"
            renamed = repo / "evals" / "adversarial-safety" / "cases-renamed.json"
            shutil.copy2(original, renamed)
            bootstrap_path = repo / "ai" / "bootstrap.json"
            bootstrap = json.loads(bootstrap_path.read_text(encoding="utf-8"))
            bootstrap["evaluation_interfaces"]["adversarial_safety"]["suite"] = "evals/adversarial-safety/cases-renamed.json"
            write_json(bootstrap_path, bootstrap)
            proc = self.run_validator(repo)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("evaluation interface paths", proc.stdout + proc.stderr)
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
