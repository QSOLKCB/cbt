# OpenAI Responses API adapter

This adapter is a **transport projection**, not an OpenAI-supplied medical configuration and not a source of medical evidence.

The current projection targets the OpenAI **Responses API** pattern verified on 2026-08-22:

- use the request-level `instructions` field for the CBT 95 operating contract;
- use `input` for the user's request;
- optionally use the built-in `file_search` tool backed by a vector store for retrieval;
- do not pin a model ID in the repository because supported model choices change over time.

Official references:

- https://developers.openai.com/api/reference/resources/responses/methods/create
- https://developers.openai.com/api/reference/typescript/resources/vector_stores/methods/search

## Build

```bash
python3 tools/build_model_adapters.py
```

Then inspect:

```text
adapters/generated/openai-responses.json
adapters/generated/retrieval-bundle.txt
```

## Retrieval workflow

A deployment can ingest `retrieval-bundle.txt` into its retrieval system or upload the underlying canonical files individually.

For OpenAI file search:

1. create or choose a vector store;
2. upload the retrieval material;
3. put the vector-store ID into the runtime request;
4. send the generated `instructions` string as the Responses API instructions;
5. let file search retrieve task-relevant records;
6. cite/identify the underlying canonical claim/source records, not the adapter projection.

The generated JSON contains placeholders rather than credentials or a hard-coded vector-store ID.

## Important boundary

Retrieval similarity is not evidence strength. A high search score cannot upgrade a public-education record into a clinical recommendation or turn an adjacent claim into claim-local evidence.

The adapter must preserve:

`PROJECTION != CANONICAL_SOURCE`

`ADJACENT_CLAIM != CLAIM_LOCAL_EVIDENCE`

`GUIDELINE_RECOMMENDATION != INDIVIDUAL_MEDICAL_ADVICE`

`CBT != CURE`
