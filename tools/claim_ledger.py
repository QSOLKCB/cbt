#!/usr/bin/env python3
"""Validate and inspect the deterministic CBT medical claim ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(root: Path, rel: str):
    return json.loads((root / rel).read_text(encoding="utf-8"))

def canonical_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()

def _contains_forbidden_snapshot_key(value) -> bool:
    forbidden = {"full_text", "article_text", "body", "content", "transcript"}
    if isinstance(value, dict):
        return any(k in forbidden or _contains_forbidden_snapshot_key(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_snapshot_key(v) for v in value)
    return False

def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    ledger = load(root, "claims/index.json")
    classes = load(root, "claims/evidence-classes.json")
    conflicts = load(root, "claims/conflicts.json")
    snapshots = load(root, "sources/snapshots/manifest.json")
    public_sources = load(root, "sources/public-sources.json")
    evidence_sources = load(root, "sources/evidence-sources.json")

    class_ids = set(classes["classes"])
    if not classes.get("no_global_rank"):
        errors.append("evidence classes must not define a global rank")

    source_records = public_sources["sources"] + evidence_sources["sources"]
    source_ids = {s["id"] for s in source_records}
    if len(source_ids) != len(source_records):
        errors.append("duplicate source id across source registries")

    snapshot_map = {s["id"]: s for s in snapshots["records"]}
    if len(snapshot_map) != len(snapshots["records"]):
        errors.append("duplicate source snapshot id")

    if _contains_forbidden_snapshot_key(snapshots):
        errors.append("source snapshots must not contain copied full-text/content fields")

    for snap in snapshots["records"]:
        if snap["source_id"] not in source_ids:
            errors.append(f"{snap['id']} references unknown source {snap['source_id']}")
        if canonical_sha256(snap["observed_metadata"]) != snap.get("metadata_sha256"):
            errors.append(f"{snap['id']} metadata fingerprint mismatch")
        try:
            verified = date.fromisoformat(snap["verified_on"])
            expires = date.fromisoformat(snap["verification_expires_on"])
            if expires < verified:
                errors.append(f"{snap['id']} expires before verification")
        except ValueError:
            errors.append(f"{snap['id']} has invalid verification date")

    claim_map = {}
    required = (
        "id", "condition", "population", "intervention", "comparator", "outcome",
        "evidence_class", "claim_text", "jurisdiction", "source_ids",
        "snapshot_ids", "status", "last_reviewed", "review_due", "not_established"
    )
    for claim in ledger["claims"]:
        cid = claim.get("id")
        if cid in claim_map:
            errors.append(f"duplicate claim id {cid}")
        claim_map[cid] = claim
        for field in required:
            if field not in claim or (claim[field] in ("", [], None) and field not in {"quantitative_result"}):
                errors.append(f"{cid} missing {field}")
        if claim.get("evidence_class") not in class_ids:
            errors.append(f"{cid} has unknown evidence class {claim.get('evidence_class')}")
        for source_id in claim.get("source_ids", []):
            if source_id not in source_ids:
                errors.append(f"{cid} references unknown source {source_id}")
        for snapshot_id in claim.get("snapshot_ids", []):
            snap = snapshot_map.get(snapshot_id)
            if not snap:
                errors.append(f"{cid} references unknown snapshot {snapshot_id}")
            elif snap["source_id"] not in claim.get("source_ids", []):
                errors.append(f"{cid} snapshot {snapshot_id} does not match a claim source")
        try:
            reviewed = date.fromisoformat(claim["last_reviewed"])
            due = date.fromisoformat(claim["review_due"])
            if due < reviewed:
                errors.append(f"{cid} review_due precedes last_reviewed")
        except (ValueError, KeyError):
            errors.append(f"{cid} has invalid review dates")

        if claim.get("evidence_class") == "archived_guideline" and claim.get("status") != "historical_reference_only":
            errors.append(f"{cid} archived guideline must remain historical_reference_only")

    for bundle in conflicts["bundles"]:
        if len(bundle.get("claim_ids", [])) < 2:
            errors.append(f"{bundle.get('id')} must preserve at least two claims")
        for cid in bundle.get("claim_ids", []):
            if cid not in claim_map:
                errors.append(f"{bundle.get('id')} references unknown claim {cid}")
        if bundle.get("preserve_all_observations") is not True:
            errors.append(f"{bundle.get('id')} must preserve all observations")
        if bundle.get("do_not_average") is not True:
            errors.append(f"{bundle.get('id')} must forbid averaging")
        if not bundle.get("resolution_rule"):
            errors.append(f"{bundle.get('id')} missing resolution_rule")

    return errors

def freshness_report(root: Path = ROOT, as_of: date | None = None):
    if as_of is None:
        as_of = date.today()
    snapshots = load(root, "sources/snapshots/manifest.json")
    rows = []
    for snap in sorted(snapshots["records"], key=lambda x: x["id"]):
        due = date.fromisoformat(snap["verification_expires_on"])
        authority = snap["observed_metadata"].get("authority_status", "unspecified")
        status = "review_due" if as_of > due else "current_verification"
        if authority == "reference_only":
            status = "historical_reference_only" if as_of <= due else "historical_reference_review_due"
        rows.append({
            "snapshot_id": snap["id"],
            "source_id": snap["source_id"],
            "authority_status": authority,
            "verified_on": snap["verified_on"],
            "verification_expires_on": snap["verification_expires_on"],
            "freshness_status": status,
        })
    return rows

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    freshness = sub.add_parser("freshness")
    freshness.add_argument("--as-of")
    freshness.add_argument("--json", action="store_true")
    freshness.add_argument("--fail-on-stale", action="store_true")
    args = parser.parse_args()

    if args.command == "validate":
        errors = validate_repository()
        if errors:
            for error in errors:
                print(f"claim ledger validation failed: {error}")
            return 1
        print("CBT claim ledger validation: ok")
        return 0

    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    rows = freshness_report(as_of=as_of)
    stale = [r for r in rows if r["freshness_status"].endswith("review_due")]
    if args.json:
        print(json.dumps({"as_of": as_of.isoformat(), "records": rows}, sort_keys=True, separators=(",", ":")))
    else:
        print(f"CBT claim ledger freshness as of {as_of.isoformat()}")
        for row in rows:
            print(f"{row['freshness_status']}: {row['source_id']} (review by {row['verification_expires_on']})")
    return 1 if args.fail_on_stale and stale else 0

if __name__ == "__main__":
    raise SystemExit(main())
