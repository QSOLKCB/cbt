#!/usr/bin/env python3
"""Build the deterministic human-facing site projection from canonical JSON."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    ("cbt_context", ROOT / "profiles" / "cbt-context.json"),
    ("cognitive_work_addendum", ROOT / "profiles" / "cognitive-work-addendum.json"),
    ("learning_accessibility", ROOT / "profiles" / "learning-accessibility.json"),
    ("exercises", ROOT / "exercises" / "index.json"),
    ("examples", ROOT / "examples" / "index.json"),
    ("public_sources", ROOT / "sources" / "public-sources.json"),
    ("medical_claim_boundary", ROOT / "ai" / "medical-claim-boundary.json"),
]
OUTPUT = ROOT / "site" / "data" / "context.bundle.js"

def build() -> str:
    payload = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in INPUTS}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "window.CBT95_CONTEXT=" + canonical + ";\n"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build()
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if actual != expected:
            print("site projection is stale; run python3 tools/build_site_data.py")
            return 1
        print("site projection: ok")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")
    print(OUTPUT.relative_to(ROOT))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
