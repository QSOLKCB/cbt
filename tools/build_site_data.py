#!/usr/bin/env python3
"""Build deterministic human-facing CBT 95 projections from canonical JSON."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_OUTPUT = ROOT / "site" / "data" / "context.bundle.js"
SEARCH_OUTPUT = ROOT / "site" / "data" / "search-index.json"

INPUTS = [
    ("cbt_context", ROOT / "profiles" / "cbt-context.json"),
    ("cbt_glossary", ROOT / "profiles" / "cbt-glossary.json"),
    ("cognitive_work_addendum", ROOT / "profiles" / "cognitive-work-addendum.json"),
    ("learning_accessibility", ROOT / "profiles" / "learning-accessibility.json"),
    ("exercises", ROOT / "exercises" / "index.json"),
    ("examples", ROOT / "examples" / "index.json"),
    ("public_sources", ROOT / "sources" / "public-sources.json"),
    ("evidence_sources", ROOT / "sources" / "evidence-sources.json"),
    ("source_snapshots", ROOT / "sources" / "snapshots" / "manifest.json"),
    ("evidence_classes", ROOT / "claims" / "evidence-classes.json"),
    ("claim_ledger", ROOT / "claims" / "index.json"),
    ("claim_conflicts", ROOT / "claims" / "conflicts.json"),
    ("medical_claim_boundary", ROOT / "ai" / "medical-claim-boundary.json"),
]


def load_payload() -> dict:
    return {key: json.loads(path.read_text(encoding="utf-8")) for key, path in INPUTS}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"[^0-9a-z]+", " ", text)
    return " ".join(text.split())


def tokens(*values: object) -> list[str]:
    merged = normalize_text(" ".join(str(v or "") for v in values))
    return sorted(set(merged.split()))


def build_context(payload: dict | None = None) -> str:
    payload = payload or load_payload()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "window.CBT95_CONTEXT=" + canonical + ";\n"


def build_search(payload: dict | None = None) -> str:
    payload = payload or load_payload()
    entries: list[dict] = []

    for ex in payload["exercises"]["exercises"]:
        entries.append({
            "id": ex["id"],
            "kind": "exercise",
            "title": ex["title"],
            "tokens": tokens(ex["id"], ex["title"], ex["purpose"], ex["mechanism"], " ".join(ex["teaching_loop_nodes"])),
        })

    for row in payload["cbt_glossary"]["terms"]:
        entries.append({
            "id": row["id"],
            "kind": "glossary",
            "title": row["term"],
            "tokens": tokens(row["id"], row["term"], row["definition"]),
        })

    source_rows = payload["public_sources"]["sources"] + payload["evidence_sources"]["sources"]
    for source in source_rows:
        entries.append({
            "id": source["id"],
            "kind": "source",
            "title": source["title"],
            "tokens": tokens(
                source["id"], source["title"], source.get("class"), source.get("jurisdiction"),
                source.get("population"), source.get("design"), source.get("scope_limitations"),
                " ".join(source.get("supports", [])),
            ),
        })

    for claim in payload["claim_ledger"]["claims"]:
        # Intentionally do not project claim_text. Search stores tokens + canonical ID only;
        # the UI reconstructs substantive wording and scope from the canonical claim ledger.
        entries.append({
            "id": claim["id"],
            "kind": "claim",
            "title": f"{claim['condition']} · {claim['evidence_class'].replace('_', ' ')}",
            "tokens": tokens(
                claim["id"], claim["condition"], claim["claim_text"], claim["population"],
                claim["intervention"], claim["comparator"], claim["outcome"], claim["evidence_class"],
                claim["jurisdiction"], " ".join(claim["not_established"]),
            ),
        })

    entries.sort(key=lambda row: (row["kind"], row["id"]))
    projection = {
        "type": "cbt95-search-index",
        "schema_version": "1.0.0",
        "projection_only": True,
        "canonical_evidence": False,
        "ranking_contract": "NFKC + lowercase + ASCII-alphanumeric tokens; exact > prefix > substring; integer score; stable type then canonical-id tie-break",
        "rules": [
            "SEARCH_RANK != EVIDENCE_STRENGTH",
            "SEARCH_RESULT != DE-SCOPED_MEDICAL_CLAIM",
            "claim entries contain normalized search tokens and canonical IDs, not standalone claim_text",
        ],
        "entries": entries,
    }
    return json.dumps(projection, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def expected_outputs() -> dict[Path, str]:
    payload = load_payload()
    return {CONTEXT_OUTPUT: build_context(payload), SEARCH_OUTPUT: build_search(payload)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = expected_outputs()
    if args.check:
        stale = []
        for path, expected in outputs.items():
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != expected:
                stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            print("site projection is stale: " + ", ".join(stale))
            return 1
        print("site projections: ok")
        return 0

    for path, expected in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
