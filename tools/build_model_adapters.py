#!/usr/bin/env python3
"""Build deterministic, non-canonical model-adapter projections for CBT 95."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTION_SPEC_PATH = "adapters/projection-spec.json"
REQUIRED_OUTPUT_KEYS = {
    "generic_system_prompt",
    "local_compact",
    "manifest",
    "openai_responses",
    "retrieval_bundle",
}


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def load_json(rel: str):
    return json.loads(read_text(rel))


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def projection_spec() -> dict:
    spec = load_json(PROJECTION_SPEC_PATH)
    outputs = spec.get("outputs")
    if spec.get("type") != "cbt-model-adapter-projection-spec":
        raise ValueError("projection spec has unexpected type")
    if spec.get("canonical_evidence") is not False:
        raise ValueError("projection spec must remain noncanonical")
    if not isinstance(outputs, dict) or set(outputs) != REQUIRED_OUTPUT_KEYS:
        raise ValueError("projection spec output keys do not match required adapter interface")
    names = [entry.get("filename") for entry in outputs.values()]
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("projection spec output filename missing")
    if len(names) != len(set(names)):
        raise ValueError("projection spec output filenames must be unique")
    if spec.get("builder") != "tools/build_model_adapters.py":
        raise ValueError("projection spec builder mismatch")
    if not isinstance(spec.get("generated_output_dir"), str) or not spec["generated_output_dir"]:
        raise ValueError("projection spec generated_output_dir missing")
    return spec


def output_names(spec: dict | None = None) -> tuple[str, ...]:
    spec = spec or projection_spec()
    return tuple(sorted(entry["filename"] for entry in spec["outputs"].values()))


def output_filename(key: str, spec: dict | None = None) -> str:
    spec = spec or projection_spec()
    return spec["outputs"][key]["filename"]


def default_output_dir(spec: dict | None = None) -> Path:
    spec = spec or projection_spec()
    return ROOT / spec["generated_output_dir"]


def canonical_inputs(bootstrap: dict | None = None) -> tuple[str, ...]:
    bootstrap = bootstrap or load_json("ai/bootstrap.json")
    paths = {"ai/bootstrap.json", *bootstrap.get("load_order", [])}
    for routed in bootstrap.get("routed_records", {}).values():
        paths.update(routed)
    return tuple(sorted(paths))


def route_map(bootstrap: dict, inputs: tuple[str, ...] | None = None) -> dict[str, list[str]]:
    inputs = inputs or canonical_inputs(bootstrap)
    mapping: dict[str, list[str]] = {path: [] for path in inputs}
    mapping.setdefault("ai/bootstrap.json", []).append("bootstrap")
    for path in bootstrap.get("load_order", []):
        mapping.setdefault(path, []).append("mandatory_policy")
    for route, paths in bootstrap.get("routed_records", {}).items():
        for path in paths:
            mapping.setdefault(path, []).append(route)
    return {path: sorted(set(routes)) for path, routes in mapping.items()}


def projection_banner(kind: str, spec: dict | None = None) -> str:
    spec = spec or projection_spec()
    return (
        f"{spec['projection_protocol']}\n"
        f"KIND: {kind}\n"
        "PROJECTION_ONLY: true\n"
        "CANONICAL_EVIDENCE: false\n"
        "SOURCE_OF_TRUTH: ai/bootstrap.json + canonical routed records\n"
        "RULE: PROJECTION != CANONICAL_SOURCE\n"
    )


def merged_guards(boundary: dict, epistemic: dict, high_risk: dict) -> list[str]:
    guards: list[str] = []
    for guard in boundary.get("hard_guards", []) + epistemic.get("guards", []) + high_risk.get("hard_guards", []):
        if guard not in guards:
            guards.append(guard)
    return guards


def append_high_risk_policy(lines: list[str], policy: dict, compact: bool = False) -> None:
    lines += ["", "High-risk clinical boundaries", f"- {policy['principle']}." ]
    lines.extend(f"- {rule}" for rule in policy.get("general_rules", []))
    for context, rules in policy.get("condition_boundaries", {}).items():
        if compact:
            lines.append(f"- {context}: " + " | ".join(rules))
        else:
            lines.append(f"- {context}:")
            lines.extend(f"  - {rule}" for rule in rules)
    if compact:
        lines.append("- Privacy boundaries: " + " | ".join(policy.get("privacy_rules", [])))
        lines.append("- Productivity boundaries: " + " | ".join(policy.get("productivity_rules", [])))
    else:
        lines.append("- Privacy boundaries:")
        lines.extend(f"  - {rule}" for rule in policy.get("privacy_rules", []))
        lines.append("- Productivity boundaries:")
        lines.extend(f"  - {rule}" for rule in policy.get("productivity_rules", []))


def append_safety_policy(lines: list[str], safety: dict) -> None:
    lines += ["", "Urgent-safety override", f"- {safety['principle']}.", "- Pause routine CBT exercise when:"]
    lines.extend(f"  - {rule}" for rule in safety.get("pause_routine_exercise_when", []))
    lines.append("- Safety response rules:")
    lines.extend(f"  - {rule}" for rule in safety.get("response_rules", []))
    lines.append("- Non-urgent assessment boundary:")
    lines.extend(f"  - {rule}" for rule in safety.get("non_urgent_boundary", []))


def build_system_prompt(spec: dict | None = None) -> str:
    spec = spec or projection_spec()
    bootstrap = load_json("ai/bootstrap.json")
    boundary = load_json("ai/medical-claim-boundary.json")
    epistemic = load_json("ai/epistemic-contract.json")
    safety = load_json("ai/safety-escalation-policy.json")
    high_risk = load_json("ai/high-risk-boundary-policy.json")
    profile = load_json("profiles/cbt-context.json")
    lines = [
        projection_banner("generic-system-prompt", spec).rstrip(),
        "",
        "You are using the CBT 95 evidence-bounded context substrate.",
        "",
        "Core role",
        f"- {profile['definition']}",
        "- This projection is transport guidance only. For substantive claims, retrieve and use the canonical repository records named by ai/bootstrap.json.",
        "",
        "Non-negotiable guards",
    ]
    lines.extend(f"- {guard}" for guard in merged_guards(boundary, epistemic, high_risk))
    lines += ["", "Medical and evidence rules"]
    lines.extend(f"- {rule}" for rule in bootstrap.get("instructions", []))
    append_safety_policy(lines, safety)
    append_high_risk_policy(lines, high_risk)
    lines += [
        "",
        "Response discipline",
        f"- Epistemic fallback state: {epistemic.get('fallback_state', 'unknown')}.",
        "- Distinguish authoritative guidance, evidence-supported claims, educational summaries, inference, user reports, unknowns, conflicts, and out-of-scope requests.",
        "- Do not cite this projection or an adversarial fixture as evidence. Identify the underlying canonical policy, claim, or source record.",
        "- If exact claim scope or freshness matters, retrieve claims/index.json, claims/conflicts.json, and sources/snapshots/manifest.json as routed by the bootstrap.",
        "",
    ]
    return "\n".join(lines)


def build_local_compact(spec: dict | None = None) -> str:
    spec = spec or projection_spec()
    boundary = load_json("ai/medical-claim-boundary.json")
    epistemic = load_json("ai/epistemic-contract.json")
    safety = load_json("ai/safety-escalation-policy.json")
    high_risk = load_json("ai/high-risk-boundary-policy.json")
    bootstrap = load_json("ai/bootstrap.json")
    lines = [
        projection_banner("compact-local-model", spec).rstrip(),
        "",
        "CBT95 compact operating context:",
        "CBT is a structured psychological intervention/tool and an evidence-based treatment for some indications. It is not a cure, diagnosis, universal remedy, guarantee, or substitute for appropriate care.",
        "",
        "GUARDS:",
    ]
    lines.extend(f"- {guard}" for guard in merged_guards(boundary, epistemic, high_risk))
    lines += [
        "",
        "CLAIMS:",
        "- For substantive medical claims, retrieve canonical claims/index.json and preserve population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, snapshot IDs, limitations, and review dates.",
        "- Never inherit evidence across condition, population, protocol, comparator, outcome, or delivery format.",
        "- Preserve conflicts. Do not average incompatible claims.",
        "- Archived guidance is historical only. Stale verification means review is due, not that the claim is false.",
    ]
    append_safety_policy(lines, safety)
    append_high_risk_policy(lines, high_risk, compact=True)
    lines += [
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


def build_retrieval_bundle(spec: dict | None = None) -> str:
    spec = spec or projection_spec()
    bootstrap = load_json("ai/bootstrap.json")
    inputs = canonical_inputs(bootstrap)
    mapping = route_map(bootstrap, inputs)
    parts = [projection_banner("retrieval-bundle", spec).rstrip(), ""]
    for rel in inputs:
        content = read_text(rel).rstrip() + "\n"
        routes = mapping.get(rel, [])
        parts += [
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
        ]
    return "\n".join(parts)


def build_openai(prompt: str, spec: dict | None = None) -> str:
    spec = spec or projection_spec()
    generated_dir = spec["generated_output_dir"].rstrip("/")
    payload = {
        "type": "cbt-openai-responses-adapter",
        "schema_version": "1.0.0",
        "projection_protocol": spec["projection_protocol"],
        "projection_only": True,
        "canonical_evidence": False,
        "transport": {
            "provider": "OpenAI",
            "api_family": "Responses API",
            "verified_pattern_date": "2026-08-22",
            "model": "<choose a currently supported model>",
        },
        "instructions": prompt,
        "retrieval": {
            "recommended_tool": "file_search",
            "source_projection": f"{generated_dir}/{output_filename('retrieval_bundle', spec)}",
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


def input_manifest(bootstrap: dict | None = None) -> list[dict]:
    bootstrap = bootstrap or load_json("ai/bootstrap.json")
    return [{"path": rel, "sha256": sha256_bytes((ROOT / rel).read_bytes())} for rel in canonical_inputs(bootstrap)]


def build_outputs() -> dict[str, str]:
    spec = projection_spec()
    prompt = build_system_prompt(spec)
    names = {
        "generic": output_filename("generic_system_prompt", spec),
        "openai": output_filename("openai_responses", spec),
        "retrieval": output_filename("retrieval_bundle", spec),
        "local": output_filename("local_compact", spec),
        "manifest": output_filename("manifest", spec),
    }
    outputs = {
        names["generic"]: prompt,
        names["openai"]: build_openai(prompt, spec),
        names["retrieval"]: build_retrieval_bundle(spec),
        names["local"]: build_local_compact(spec),
    }
    generated_dir = spec["generated_output_dir"].rstrip("/")
    manifest = {
        "type": "cbt-model-adapter-projection-manifest",
        "schema_version": "1.0.0",
        "projection_protocol": spec["projection_protocol"],
        "projection_only": True,
        "canonical_evidence": False,
        "projection_spec": {
            "path": PROJECTION_SPEC_PATH,
            "sha256": sha256_bytes((ROOT / PROJECTION_SPEC_PATH).read_bytes()),
        },
        "canonical_inputs": input_manifest(),
        "outputs": [
            {"path": f"{generated_dir}/{name}", "sha256": sha256_text(outputs[name])}
            for name in sorted(outputs)
        ],
        "rules": [
            "PROJECTION != CANONICAL_SOURCE",
            "adapter outputs must never appear in ai/bootstrap.json load_order or routed_records",
            "adapter outputs must never be used as claim source_ids or snapshot_ids",
            "deterministic byte identity does not create medical authority",
        ],
    }
    outputs[names["manifest"]] = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return outputs


def write_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_outputs()
    for name in output_names():
        (output_dir / name).write_text(outputs[name], encoding="utf-8")


def _is_generated_reference(value: object, prefix: str) -> bool:
    return isinstance(value, str) and value.replace("\\", "/").lstrip("./").startswith(prefix)


def verify_noncanonical_boundaries() -> list[str]:
    errors: list[str] = []
    spec = projection_spec()
    bootstrap = load_json("ai/bootstrap.json")
    claims = load_json("claims/index.json")
    public_sources = load_json("sources/public-sources.json")
    evidence_sources = load_json("sources/evidence-sources.json")
    snapshots = load_json("sources/snapshots/manifest.json")
    prefix = spec["generated_output_dir"].rstrip("/") + "/"
    routed = list(bootstrap.get("load_order", []))
    for paths in bootstrap.get("routed_records", {}).values():
        routed.extend(paths)
    if any(_is_generated_reference(path, prefix) for path in routed):
        errors.append("generated adapter projection appears in canonical bootstrap routing")
    for claim in claims.get("claims", []):
        refs = list(claim.get("source_ids", [])) + list(claim.get("snapshot_ids", []))
        if any(_is_generated_reference(ref, prefix) for ref in refs):
            errors.append(f"{claim.get('id')} depends on generated adapter projection")
    for source in public_sources.get("sources", []) + evidence_sources.get("sources", []):
        if _is_generated_reference(source.get("url", ""), prefix):
            errors.append(f"{source.get('id')} uses generated adapter projection as source")
    for snapshot in snapshots.get("records", []):
        if _is_generated_reference(snapshot.get("source_registry", ""), prefix):
            errors.append(f"{snapshot.get('id')} depends on generated adapter projection")
        if _is_generated_reference(snapshot.get("observed_metadata", {}).get("url", ""), prefix):
            errors.append(f"{snapshot.get('id')} uses generated adapter projection as observed metadata URL")
    if any(_is_generated_reference(path, prefix) for path in canonical_inputs(bootstrap)):
        errors.append("generated adapter projection included as canonical builder input")
    return errors


def verify_output_dir(output_dir: Path) -> list[str]:
    errors = verify_noncanonical_boundaries()
    expected = build_outputs()
    for name in output_names():
        path = output_dir / name
        if not path.exists():
            errors.append(f"missing generated projection {name}")
        elif path.read_text(encoding="utf-8") != expected[name]:
            errors.append(f"stale or non-deterministic generated projection {name}")
    try:
        openai = json.loads((output_dir / output_filename("openai_responses")).read_text(encoding="utf-8"))
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
        for name in output_names():
            if (pa / name).read_bytes() != (pb / name).read_bytes():
                errors.append(f"non-deterministic output {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--determinism-check", action="store_true")
    args = parser.parse_args()
    try:
        spec = projection_spec()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"adapter projection spec invalid: {exc}")
        return 1
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(spec)
    if args.determinism_check:
        errors = determinism_check()
        if errors:
            for error in errors:
                print(f"adapter determinism failed: {error}")
            return 1
        print("CBT model adapter determinism: ok")
        return 0
    if args.check:
        errors = verify_output_dir(output_dir)
        if errors:
            for error in errors:
                print(f"adapter projection check failed: {error}")
            return 1
        print("CBT model adapter projections: ok")
        return 0
    write_outputs(output_dir)
    if args.verify:
        errors = verify_output_dir(output_dir)
        if errors:
            for error in errors:
                print(f"adapter projection verification failed: {error}")
            return 1
        print("CBT model adapter projections built and verified")
    else:
        print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
