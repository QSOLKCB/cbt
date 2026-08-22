#!/usr/bin/env python3
"""Build deterministic, non-canonical model-adapter projections for CBT 95."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "adapters" / "generated"
PROJECTION_PROTOCOL = "CBT-MODEL-ADAPTER-PROJECTION/1"

CANONICAL_INPUTS = (
    "ai/bootstrap.json",
    "ai/source-policy.json",
    "ai/epistemic-contract.json",
    "ai/medical-claim-boundary.json",
    "ai/safety-escalation-policy.json",
    "profiles/cbt-context.json",
    "profiles/cognitive-work-addendum.json",
    "profiles/learning-accessibility.json",
    "exercises/index.json",
    "examples/index.json",
    "claims/evidence-classes.json",
    "claims/index.json",
    "claims/conflicts.json",
    "sources/public-sources.json",
    "sources/evidence-sources.json",
    "sources/snapshots/manifest.json",
)

OUTPUT_NAMES = (
    "generic-system-prompt.txt",
    "openai-responses.json",
    "retrieval-bundle.txt",
    "local-compact.txt",
    "manifest.json",
)

def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def load_json(rel: str):
    return json.loads(read_text(rel))

def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))

def route_map(bootstrap: dict) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {path: [] for path in CANONICAL_INPUTS}
    for path in bootstrap.get("load_order", []):
        mapping.setdefault(path, []).append("mandatory_policy")
    for route, paths in bootstrap.get("routed_records", {}).items():
        for path in paths:
            mapping.setdefault(path, []).append(route)
    return {path: sorted(set(routes)) for path, routes in mapping.items()}

def projection_banner(kind: str) -> str:
    return (
        f"{PROJECTION_PROTOCOL}\n"
        f"KIND: {kind}\n"
        "PROJECTION_ONLY: true\n"
        "CANONICAL_EVIDENCE: false\n"
        "SOURCE_OF_TRUTH: ai/bootstrap.json + canonical routed records\n"
        "RULE: PROJECTION != CANONICAL_SOURCE\n"
    )

def build_system_prompt() -> str:
    bootstrap = load_json("ai/bootstrap.json")
    boundary = load_json("ai/medical-claim-boundary.json")
    epi = load_json("ai/epistemic-contract.json")
    safety = load_json("ai/safety-escalation-policy.json")
    profile = load_json("profiles/cbt-context.json")
    guards = boundary.get("hard_guards", []) + [
        g for g in epi.get("guards", []) if g not in boundary.get("hard_guards", [])
    ]
    lines = [
        projection_banner("generic-system-prompt").rstrip(),
        "",
        "You are using the CBT 95 evidence-bounded context substrate.",
        "",
        "Core role",
        f"- {profile['definition']}",
        "- This projection is transport guidance only. For substantive claims, retrieve and use the canonical repository records named by ai/bootstrap.json.",
        "",
        "Non-negotiable guards",
    ]
    lines.extend(f"- {guard}" for guard in guards)
    lines += ["", "Medical and evidence rules"]
    lines.extend(f"- {rule}" for rule in bootstrap.get("instructions", []))
    lines += ["", "Urgent-safety override", f"- {safety['principle']}." ]
    lines.extend(f"- {rule}" for rule in safety.get("response_rules", []))
    lines += [
        "",
        "Response discipline",
        f"- Epistemic fallback state: {epi.get('fallback_state', 'unknown')}.",
        "- Distinguish authoritative guidance, evidence-supported claims, educational summaries, inference, user reports, unknowns, conflicts, and out-of-scope requests.",
        "- Do not cite this projection as evidence. Cite or identify the underlying canonical claim/source records instead.",
        "- If exact claim scope or freshness matters, retrieve claims/index.json, claims/conflicts.json, and sources/snapshots/manifest.json as routed by the bootstrap.",
        "",
    ]
    return "\n".join(lines)

def build_local_compact() -> str:
    boundary = load_json("ai/medical-claim-boundary.json")
    epi = load_json("ai/epistemic-contract.json")
    safety = load_json("ai/safety-escalation-policy.json")
    bootstrap = load_json("ai/bootstrap.json")
    lines = [
        projection_banner("compact-local-model").rstrip(),
        "",
        "CBT95 compact operating context:",
        "CBT is a structured psychological intervention/tool and an evidence-based treatment for some indications. It is not a cure, diagnosis, universal remedy, guarantee, or substitute for appropriate care.",
        "",
        "GUARDS:",
    ]
    lines.extend(f"- {g}" for g in boundary.get("hard_guards", []))
    lines.extend(f"- {g}" for g in epi.get("guards", []) if g not in boundary.get("hard_guards", []))
    lines += [
        "",
        "CLAIMS:",
        "- For substantive medical claims, retrieve canonical claims/index.json and preserve population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, snapshot IDs, limitations, and review dates.",
        "- Never inherit evidence across condition, population, protocol, comparator, outcome, or delivery format.",
        "- Preserve conflicts. Do not average incompatible claims.",
        "- Archived guidance is historical only. Stale verification means review is due, not that the claim is false.",
        "",
        "SAFETY:",
        f"- {safety['principle']}.",
        "- Do not diagnose, prescribe, change medication, perform risk clearance, or tell a person to stop professional care.",
        "- Resolve current local urgent-support information at runtime when needed.",
        "",
        "SELF-HELP:",
        "- Educational exercises are not automatically equivalent to clinician-delivered CBT.",
        "- Do not force positive thinking, dismiss real danger/abuse/grief/material problems, or score answers diagnostically.",
        "",
        "ROUTING:",
    ]
    for route, paths in bootstrap.get("routed_records", {}).items():
        lines.append(f"- {route}: {', '.join(paths)}")
    lines += ["", "This compact projection is not evidence. Retrieve canonical records for claim support.", ""]
    return "\n".join(lines)

def build_retrieval_bundle() -> str:
    bootstrap = load_json("ai/bootstrap.json")
    mapping = route_map(bootstrap)
    parts = [projection_banner("retrieval-bundle").rstrip(), ""]
    for rel in CANONICAL_INPUTS:
        content = read_text(rel).rstrip() + "\n"
        routes = mapping.get(rel, [])
        parts.extend([
            "=== CBT95 CANONICAL RECORD PROJECTION ===",
            f"canonical_path: {rel}",
            f"canonical_sha256: {sha256_bytes((ROOT / rel).read_bytes())}",
            f"routes: {','.join(routes) if routes else 'none'}",
            "projection_only: true",
            "canonical_evidence: false",
            "content_follows:",
            content.rstrip(),
            "=== END CBT95 RECORD ===",
            "",
        ])
    return "\n".join(parts)

def build_openai(system_prompt: str) -> str:
    payload = {
        "type": "cbt-openai-responses-adapter",
        "schema_version": "1.0.0",
        "projection_protocol": PROJECTION_PROTOCOL,
        "projection_only": True,
        "canonical_evidence": False,
        "transport": {
            "provider": "OpenAI",
            "api_family": "Responses API",
            "verified_pattern_date": "2026-08-22",
            "model": "<choose a currently supported model>",
        },
        "instructions": system_prompt,
        "retrieval": {
            "recommended_tool": "file_search",
            "source_projection": "adapters/generated/retrieval-bundle.txt",
            "vector_store_id": "<vector_store_id>",
            "rule": "Use retrieval to locate canonical record content; do not treat retrieval scores or this adapter as medical evidence.",
        },
        "request_template": {
            "model": "<choose a currently supported model>",
            "instructions": "<copy the instructions field from this adapter>",
            "input": "<user request>",
            "tools": [{"type": "file_search", "vector_store_ids": ["<vector_store_id>"]}],
        },
        "noncanonical_rule": "PROJECTION != CANONICAL_SOURCE",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

def input_manifest() -> list[dict]:
    return [{"path": rel, "sha256": sha256_bytes((ROOT / rel).read_bytes())} for rel in CANONICAL_INPUTS]

def build_outputs() -> dict[str, str]:
    system_prompt = build_system_prompt()
    outputs = {
        "generic-system-prompt.txt": system_prompt,
        "openai-responses.json": build_openai(system_prompt),
        "retrieval-bundle.txt": build_retrieval_bundle(),
        "local-compact.txt": build_local_compact(),
    }
    manifest = {
        "type": "cbt-model-adapter-projection-manifest",
        "schema_version": "1.0.0",
        "projection_protocol": PROJECTION_PROTOCOL,
        "projection_only": True,
        "canonical_evidence": False,
        "canonical_inputs": input_manifest(),
        "outputs": [
            {"path": f"adapters/generated/{name}", "sha256": sha256_text(outputs[name])}
            for name in sorted(outputs)
        ],
        "rules": [
            "PROJECTION != CANONICAL_SOURCE",
            "adapter outputs must never appear in ai/bootstrap.json load_order or routed_records",
            "adapter outputs must never be used as claim source_ids or snapshot_ids",
            "deterministic byte identity does not create medical authority",
        ],
    }
    outputs["manifest.json"] = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return outputs

def write_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_outputs()
    for name in OUTPUT_NAMES:
        (output_dir / name).write_text(outputs[name], encoding="utf-8")

def verify_noncanonical_boundaries() -> list[str]:
    errors: list[str] = []
    bootstrap = load_json("ai/bootstrap.json")
    claims = load_json("claims/index.json")
    public_sources = load_json("sources/public-sources.json")
    evidence_sources = load_json("sources/evidence-sources.json")
    snapshots = load_json("sources/snapshots/manifest.json")
    generated_prefix = "adapters/generated/"
    routed = list(bootstrap.get("load_order", []))
    for paths in bootstrap.get("routed_records", {}).values():
        routed.extend(paths)
    if any(path.startswith(generated_prefix) for path in routed):
        errors.append("generated adapter projection appears in canonical bootstrap routing")
    for claim in claims.get("claims", []):
        refs = list(claim.get("source_ids", [])) + list(claim.get("snapshot_ids", []))
        if any(str(ref).startswith(generated_prefix) for ref in refs):
            errors.append(f"{claim.get('id')} depends on generated adapter projection")
    for source in public_sources.get("sources", []) + evidence_sources.get("sources", []):
        if str(source.get("url", "")).startswith(generated_prefix):
            errors.append(f"{source.get('id')} uses generated adapter projection as source")
    for snap in snapshots.get("records", []):
        if str(snap.get("source_registry", "")).startswith(generated_prefix):
            errors.append(f"{snap.get('id')} depends on generated adapter projection")
    if any(path.startswith(generated_prefix) for path in CANONICAL_INPUTS):
        errors.append("generated adapter projection included as canonical builder input")
    return errors

def verify_output_dir(output_dir: Path) -> list[str]:
    errors = verify_noncanonical_boundaries()
    expected = build_outputs()
    for name in OUTPUT_NAMES:
        path = output_dir / name
        if not path.exists():
            errors.append(f"missing generated projection {name}")
            continue
        if path.read_text(encoding="utf-8") != expected[name]:
            errors.append(f"stale or non-deterministic generated projection {name}")
    try:
        openai = json.loads((output_dir / "openai-responses.json").read_text(encoding="utf-8"))
        if openai.get("projection_only") is not True or openai.get("canonical_evidence") is not False:
            errors.append("OpenAI adapter projection boundary weakened")
    except (FileNotFoundError, json.JSONDecodeError):
        errors.append("OpenAI adapter is missing or invalid JSON")
    return errors

def determinism_check() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        pa, pb = Path(a), Path(b)
        write_outputs(pa)
        write_outputs(pb)
        for name in OUTPUT_NAMES:
            if (pa / name).read_bytes() != (pb / name).read_bytes():
                errors.append(f"non-deterministic output {name}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--check", action="store_true", help="compare output directory with a fresh deterministic build")
    parser.add_argument("--verify", action="store_true", help="verify projection boundaries and output structure")
    parser.add_argument("--determinism-check", action="store_true")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if args.determinism_check:
        errors = determinism_check()
        if errors:
            for error in errors: print(f"adapter determinism failed: {error}")
            return 1
        print("CBT model adapter determinism: ok")
        return 0
    if args.check:
        errors = verify_output_dir(output_dir)
        if errors:
            for error in errors: print(f"adapter projection check failed: {error}")
            return 1
        print("CBT model adapter projections: ok")
        return 0
    write_outputs(output_dir)
    if args.verify:
        errors = verify_output_dir(output_dir)
        if errors:
            for error in errors: print(f"adapter projection verification failed: {error}")
            return 1
        print("CBT model adapter projections built and verified")
    else:
        print(output_dir)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
