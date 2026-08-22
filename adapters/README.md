# CBT 95 model adapters

Phase 4 turns the canonical CBT substrate into transport-specific **projections**.

These files are not a second medical knowledge base.

> `PROJECTION != CANONICAL_SOURCE`

The source of truth remains `ai/bootstrap.json` plus the canonical records it routes to. Adapter outputs are generated from those records for easier use with different model families and retrieval stacks.

## Build all projections

```bash
python3 tools/build_model_adapters.py
python3 tools/build_model_adapters.py --check
python3 tools/build_model_adapters.py --determinism-check
```

The default output directory is `adapters/generated/` and is intentionally git-ignored. The generated artifacts are:

- `generic-system-prompt.txt` — model-family-neutral operating instructions.
- `openai-responses.json` — OpenAI Responses API transport projection.
- `retrieval-bundle.txt` — deterministic text bundle for vector/RAG ingestion.
- `local-compact.txt` — smaller projection for local models with limited context.
- `manifest.json` — canonical-input and output fingerprints.

Use `--output-dir <path>` to build elsewhere.

## Canonicality boundary

Adapter outputs may summarize, duplicate, reorder, or compact canonical records, but they never become claim evidence.

The validator enforces that generated adapter paths do not appear in:

- bootstrap `load_order`;
- bootstrap `routed_records`;
- claim `source_ids`;
- claim `snapshot_ids`;
- source/snapshot authority links; or
- the adapter compiler's own canonical input set.

Byte-for-byte reproducibility proves only that a projection is deterministic. It does not confer medical authority.

## Recommended use

1. Load or build the adapter projection suitable for the target model.
2. Preserve the projection's `PROJECTION_ONLY` / `CANONICAL_EVIDENCE: false` markers.
3. For exact medical claims, retrieve the underlying canonical `claims/**`, `sources/**`, and policy files named by the bootstrap.
4. Resolve current safety resources at runtime when needed.
5. Rebuild projections whenever canonical inputs change.

See `adapters/openai/README.md` for OpenAI-specific transport guidance.
