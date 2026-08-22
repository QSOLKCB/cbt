#!/usr/bin/env python3
"""Fail-closed structural validation for CBT 95."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def require(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"validation failed: {message}")

def main() -> int:
    bootstrap = load("ai/bootstrap.json")
    boundary = load("ai/medical-claim-boundary.json")
    epi = load("ai/epistemic-contract.json")
    safety = load("ai/safety-escalation-policy.json")
    sources = load("sources/public-sources.json")
    exercises = load("exercises/index.json")
    work = load("profiles/cognitive-work-addendum.json")

    required_order = [
        "ai/source-policy.json",
        "ai/epistemic-contract.json",
        "ai/medical-claim-boundary.json",
        "ai/safety-escalation-policy.json",
        "profiles/cbt-context.json",
    ]
    require(bootstrap["load_order"] == required_order, "policy load order changed")
    require(
        "sources/public-sources.json" in bootstrap["routed_records"]["cbt_self_help"],
        "self-help route must load source metadata",
    )

    guards = set(boundary["hard_guards"])
    for guard in {
        "CBT != CURE",
        "CBT != UNIVERSAL_REMEDY",
        "SELF_HELP_CBT != CLINICIAN_DELIVERED_CBT",
        "AI_CONTEXT != DIAGNOSIS",
        "AI_CONTEXT != CLINICAL_AUTHORITY",
    }:
        require(guard in guards, f"missing guard {guard}")

    require(epi["fallback_state"] == "unknown", "epistemic contract must fail to unknown")
    require("urgent safety needs override routine CBT exercises" == safety["principle"], "safety override weakened")
    require("move emotion into the prefrontal cortex" in work["avoid_framing"], "neuroscience cartoon guard missing")
    require(work.get("evidence_scope"), "cognitive-work evidence scope missing")
    require(
        any("do not generalise laboratory neuroimaging findings" in x for x in work["guardrails"]),
        "cognitive-work generalisation guard missing",
    )

    source_ids = {s["id"] for s in sources["sources"]}
    require(len(source_ids) == len(sources["sources"]), "duplicate source id")
    for needed in {
        "au.medicalboard.good-medical-practice",
        "au.acsqhc.digital-mental-health",
        "uk.nhs.cbt",
        "uk.nice.depression.ng222",
        "uk.nice.gad.cg113",
        "pubmed.lieberman.2007.affect-labeling",
        "pubmed.buhle.2014.reappraisal-meta",
    }:
        require(needed in source_ids, f"missing critical source {needed}")

    for source in sources["sources"]:
        if source["class"] == "peer_reviewed_pubmed":
            for field in ("population", "design", "scope_limitations"):
                require(source.get(field), f"{source['id']} missing {field}")

    require(len(exercises["exercises"]) >= 6, "exercise baseline shrank")
    ids = set()
    for exercise in exercises["exercises"]:
        require(exercise["id"] not in ids, f"duplicate exercise {exercise['id']}")
        ids.add(exercise["id"])
        for field in ("purpose","prompts","mechanism","not_established","pause_or_support","source_ids"):
            require(exercise.get(field), f"{exercise['id']} missing {field}")
        for source_id in exercise["source_ids"]:
            require(source_id in source_ids, f"{exercise['id']} references unknown source {source_id}")

    require("affect-to-action" in ids, "cognitive-work exercise missing")
    print("CBT context validation: ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
