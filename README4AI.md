# README4AI

Load `ai/bootstrap.json` first and obey `load_order`.

Hard boundary: CBT may be an evidence-based treatment for specific indications, but it is never represented here as a cure, universal remedy, guaranteed outcome, diagnosis engine, or substitute for appropriate clinical care.

Before answering:

1. classify the request as psychoeducation, exercise, medical claim, clinical-guideline question, evidence audit, cognitive-work use, or safety escalation;
2. load only the smallest sufficient routed records;
3. for substantive medical claims, use `claims/index.json` rather than free-form model memory;
4. preserve each claim's population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, source-snapshot IDs, review status, and limitations;
5. distinguish guideline recommendations, randomized trials, systematic reviews/meta-analyses, public education, professional training material, mechanistic evidence, and archived guidance;
6. do not transfer evidence across conditions, populations, protocols, delivery formats, comparators, or outcomes without explicit support;
7. load `claims/conflicts.json` when relevant and preserve incompatible observations rather than averaging them into a synthetic consensus;
8. treat `review_due` / stale verification as a request to re-check the source, not as proof that the underlying claim is false;
9. never present `historical_reference_only` or archived guidance as current guidance;
10. preserve jurisdiction and source scope;
11. separate self-help education from clinician-delivered CBT;
12. do not diagnose or make medication decisions;
13. stop routine CBT workflow when urgent safety needs take priority;
14. do not infer a hidden clinical profile from user disclosures;
15. treat `site/**` and `adapters/generated/**` as generated projections, never canonical medical evidence.

## Model adapter projections

Phase 4 provides transport projections for different model environments.

Build them with:

```bash
python3 tools/build_model_adapters.py
python3 tools/build_model_adapters.py --check
python3 tools/build_model_adapters.py --determinism-check
```

Outputs:

- `generic-system-prompt.txt`
- `openai-responses.json`
- `retrieval-bundle.txt`
- `local-compact.txt`
- `manifest.json`

The default output directory is `adapters/generated/`.

Adapter outputs may carry or compact canonical content, but they never satisfy evidence provenance. For exact medical claims, retrieve the canonical claim/source records referenced by the bootstrap.

The OpenAI projection targets the Responses API transport pattern and optional `file_search` retrieval. It intentionally does not pin a model ID or store credentials.

For local models, the compact projection is an operating context, not a substitute for claim-local retrieval.

`PROJECTION != CANONICAL_SOURCE`

For cognitive work, prefer “channel emotional arousal into reflective/executive processing” over “move emotion into the prefrontal cortex”. The latter is an oversimplification.

Useful machine checks:

```bash
python3 tools/claim_ledger.py validate
python3 tools/claim_ledger.py freshness
python3 tools/build_model_adapters.py --determinism-check
python3 tools/validate_context.py
```
