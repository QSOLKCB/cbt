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
    source_policy = load(root, "ai/source-policy.json")

    class_ids = set(classes["classes"])
    if not classes.get("no_global_rank"):
        errors.append("evidence classes must not define a global rank")

    allowed_source_classes = set(source_policy.get("allowed_source_classes", []))
    source_records = public_sources["sources"] + evidence_sources["sources"]
    source_ids = {s["id"] for s in source_records}
    source_map = {s["id"]: s for s in source_records}
    if len(source_ids) != len(source_records):
        errors.append("duplicate source id across source registries")
    for source in source_records:
        if source.get("class") not in allowed_source_classes:
            errors.append(f"{source['id']} has unregistered source class {source.get('class')}")

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
        except (ValueError, KeyError):
            errors.append(f"{snap.get('id')} has invalid verification date")

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

        claim_source_ids = set(claim.get("source_ids", []))
        for source_id in claim_source_ids:
            if source_id not in source_ids:
                errors.append(f"{cid} references unknown source {source_id}")

        represented_source_ids: set[str] = set()
        claim_snapshots = []
        for snapshot_id in claim.get("snapshot_ids", []):
            snap = snapshot_map.get(snapshot_id)
            if not snap:
                errors.append(f"{cid} references unknown snapshot {snapshot_id}")
                continue
            claim_snapshots.append(snap)
            represented_source_ids.add(snap["source_id"])
            if snap["source_id"] not in claim_source_ids:
                errors.append(f"{cid} snapshot {snapshot_id} does not match a claim source")
        missing_snapshot_sources = sorted(claim_source_ids - represented_source_ids)
        if missing_snapshot_sources:
            errors.append(f"{cid} missing snapshots for claim sources: {', '.join(missing_snapshot_sources)}")

        try:
            reviewed = date.fromisoformat(claim["last_reviewed"])
            due = date.fromisoformat(claim["review_due"])
            if due < reviewed:
                errors.append(f"{cid} review_due precedes last_reviewed")
        except (ValueError, KeyError):
            errors.append(f"{cid} has invalid review dates")

        authority_statuses = {
            source_map[source_id].get("authority_status")
            for source_id in claim_source_ids
            if source_id in source_map
        }
        authority_statuses.update(
            snap.get("observed_metadata", {}).get("authority_status")
            for snap in claim_snapshots
        )
        authority_statuses.discard(None)
        derives_historical_only = "reference_only" in authority_statuses
        if derives_historical_only:
            if claim.get("status") != "historical_reference_only":
                errors.append(f"{cid} uses reference_only evidence and must remain historical_reference_only")
            if claim.get("evidence_class") != "archived_guideline":
                errors.append(f"{cid} uses reference_only guidance and must use archived_guideline evidence class")
        if claim.get("evidence_class") == "archived_guideline":
            if claim.get("status") != "historical_reference_only":
                errors.append(f"{cid} archived guideline must remain historical_reference_only")
            if not derives_historical_only:
                errors.append(f"{cid} archived guideline lacks reference_only source authority metadata")

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
    ledger = load(root, "claims/index.json")
    rows = []

    for snap in sorted(snapshots["records"], key=lambda x: x["id"]):
        verified = date.fromisoformat(snap["verified_on"])
        due = date.fromisoformat(snap["verification_expires_on"])
        authority = snap["observed_metadata"].get("authority_status", "unspecified")
        if as_of < verified:
            status = "not_yet_verified"
        elif authority == "reference_only":
            status = "historical_reference_review_due" if as_of > due else "historical_reference_only"
        else:
            status = "review_due" if as_of > due else "current_verification"
        rows.append({
            "record_type": "source_snapshot",
            "snapshot_id": snap["id"],
            "source_id": snap["source_id"],
            "authority_status": authority,
            "verified_on": snap["verified_on"],
            "review_due_on": snap["verification_expires_on"],
            "freshness_status": status,
        })

    for claim in sorted(ledger["claims"], key=lambda x: x["id"]):
        reviewed = date.fromisoformat(claim["last_reviewed"])
        due = date.fromisoformat(claim["review_due"])
        if as_of < reviewed:
            status = "not_yet_reviewed"
        elif claim.get("status") == "historical_reference_only":
            status = "historical_claim_review_due" if as_of > due else "historical_claim_review_current"
        else:
            status = "claim_review_due" if as_of > due else "claim_review_current"
        rows.append({
            "record_type": "claim",
            "claim_id": claim["id"],
            "claim_status": claim["status"],
            "last_reviewed": claim["last_reviewed"],
            "review_due_on": claim["review_due"],
            "freshness_status": status,
        })

    return rows


def _freshness_blocks(row: dict) -> bool:
    status = row["freshness_status"]
    return status.endswith("review_due") or status in {"not_yet_verified", "not_yet_reviewed"}


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
    blocking = [r for r in rows if _freshness_blocks(r)]
    if args.json:
        print(json.dumps({"as_of": as_of.isoformat(), "records": rows}, sort_keys=True, separators=(",", ":")))
    else:
        print(f"CBT claim ledger freshness as of {as_of.isoformat()}")
        for row in rows:
            if row["record_type"] == "source_snapshot":
                print(f"{row['freshness_status']}: source {row['source_id']} (review by {row['review_due_on']})")
            else:
                print(f"{row['freshness_status']}: claim {row['claim_id']} (review by {row['review_due_on']})")
    return 1 if args.fail_on_stale and blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
