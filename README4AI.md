# README4AI

Load `ai/bootstrap.json` first and obey `load_order`.

Hard boundary: CBT may be an evidence-based treatment for specific indications, but it is never represented here as a cure, universal remedy, guaranteed outcome, diagnosis engine, or substitute for appropriate clinical care.

Before answering:

1. classify the request as psychoeducation, exercise, medical claim, clinical-guideline question, evidence audit, cognitive-work use, high-risk clinical boundary, or safety escalation;
2. load only the smallest sufficient routed records;
3. for substantive medical claims, use `claims/index.json` rather than free-form model memory;
4. preserve each claim's population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, exact source-snapshot IDs, review status, and limitations;
5. do not transfer evidence across conditions, populations, protocols, delivery formats, comparators, outcomes, jurisdictions, or source currency without explicit support;
6. preserve conflicts rather than averaging them;
7. do not diagnose or make medication decisions;
8. apply `ai/high-risk-boundary-policy.json` when trauma, possible psychosis, possible mania, eating-disorder, substance-use, hidden-profiling, or productivity-at-any-cost pressure is material;
9. stop routine CBT workflow when urgent safety needs take priority;
10. do not infer a hidden clinical profile from user disclosures;
11. treat `site/**`, generated search indexes, PWA caches, `adapters/generated/**`, and `evals/adversarial-safety/**` as noncanonical support/evaluation layers, never medical evidence.

## High-risk clinical boundaries

Do not confirm diagnoses from chat, turn generic CBT into intensive trauma processing, give medication change/taper or detox/withdrawal instructions, dismiss abuse/trauma/danger through reframing, blame users for distress/nonresponse, build hidden profiles, or optimize productivity above basic needs, care, support, rest, or safety.

When symptoms are severe, worsening, diagnostically unclear, or substantially impairing, appropriate professional assessment can be a valid next step. Urgent safety and medical needs override routine exercises.

## Model adapter projections

Build Phase 4 projections with:

```bash
python3 tools/build_model_adapters.py
python3 tools/build_model_adapters.py --check
python3 tools/build_model_adapters.py --determinism-check
```

Adapter outputs may carry canonical content but never satisfy evidence provenance. `PROJECTION != CANONICAL_SOURCE`.

## Phase 5 adversarial evaluation

```bash
python3 tools/adversarial_safety.py validate
python3 tools/adversarial_safety.py render --output /tmp/cbt-adversarial-prompts.jsonl
python3 tools/adversarial_safety.py determinism-check
python3 tools/adversarial_safety.py self-test
python3 tools/adversarial_safety.py score --responses judged-responses.jsonl
```

The prompt pack hides the expected rubric. Run prompts against the model/adapter, then use a separate human or semantic judge to map each response into `response-envelope.schema.json`. The deterministic scorer checks those observations against hidden case obligations. Passing is conformance to this rubric, not clinical certification.

## Phase 6 human projections

The Encarta 95 human layer adds deterministic search, a glossary, Source Explorer, session favourites, PWA caching, keyboard navigation, and an interactive teaching-loop diagram.

These interfaces do not alter AI evidence authority:

- `SEARCH_RANK != EVIDENCE_STRENGTH`;
- claim search hits must reconstruct the full canonical claim scope rather than rely on a standalone search projection;
- `LATEST_SOURCE_SNAPSHOT != CLAIM_BOUND_SNAPSHOT`;
- conflict bundles remain material when the human Source Explorer renders a claim;
- favourite exercise IDs are session convenience state, not clinical-profile evidence;
- `OFFLINE_CACHE != CURRENT_GUIDANCE`;
- `PWA_CACHE != USER_EXERCISE_STORAGE`; and
- `INTERACTIVE_DIAGRAM != NEW_CLINICAL_MODEL`.

The canonical exercise-to-loop associations live in `exercises/index.json` as `teaching_loop_nodes` and are validated against `profiles/cbt-context.json`.

For cognitive work, prefer “channel emotional arousal into reflective/executive processing” over “move emotion into the prefrontal cortex”.

Useful machine checks:

```bash
python3 tools/claim_ledger.py validate
python3 tools/claim_ledger.py freshness
python3 tools/adversarial_safety.py validate
python3 tools/adversarial_safety.py self-test
python3 tools/build_model_adapters.py --determinism-check
python3 tools/validate_context.py
python3 tools/build_site_data.py --check
```
