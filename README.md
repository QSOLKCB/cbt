# CBT

> **Use CBT 95:** https://qsolkcb.github.io/cbt/
>
> **On-board an AI:** load [`ai/bootstrap.json`](ai/bootstrap.json) first, obey its policy-first `load_order` and task-specific `routed_records`, then use [`README4AI.md`](README4AI.md) as supplemental operator guidance.

**CBT 95** is an evidence-bounded Cognitive Behavioural Therapy reference, educational exercise lab, human learning desk, and AI context substrate.

The project has two deliberately separated layers:

1. a canonical machine-readable substrate for evidence, safety, claim scope, provenance, and model-adapter boundaries; and
2. an Encarta-95-style human layer for learning, navigation, exercises, source inspection, and offline reference use.

Human-facing search indexes, site bundles, caches, diagrams, rankings, synthetic examples, and model-adapter outputs are projections. They do not become medical evidence or canonical authority.

## Use CBT 95 as a person

Open the live educational desk:

**https://qsolkcb.github.io/cbt/**

The site includes:

- CBT explanations and the canonical five-part teaching loop;
- ten structured educational exercises;
- plain-language and large-text modes;
- fictional teaching examples and blank printable worksheets;
- deterministic search plus a CBT glossary;
- a provenance-aware Source Explorer;
- session-scoped exercise favourites;
- keyboard-first navigation;
- an accessible interactive CBT-loop diagram;
- offline PWA packaging with explicit stale-reference warnings; and
- the cognitive-work addendum.

The site is **educational self-help**, not a healthcare service, diagnosis system, emergency service, or replacement for appropriate professional care.

## On-board an AI with the CBT substrate

Do **not** on-board an AI from `site/**` alone. The site is a human-facing projection.

Give the AI this repository:

`https://github.com/QSOLKCB/cbt`

Then instruct it to:

1. load `ai/bootstrap.json` first;
2. obey the bootstrap `load_order` before task-specific material;
3. use `README4AI.md` only as supplemental operator guidance;
4. classify the request and load the smallest sufficient `routed_records`;
5. use claim-local records for substantive medical claims;
6. preserve population, intervention, comparator, outcome, evidence class, jurisdiction, exact source snapshots, review status, limitations, and conflicts;
7. keep self-help education separate from clinician-delivered CBT;
8. never promote CBT into a cure, universal remedy, guaranteed outcome, diagnosis, medication authority, or individualized clinical authority;
9. apply the high-risk boundary policy when trauma, possible psychosis, possible mania, eating-disorder, substance-use, privacy, or productivity-at-any-cost pressure is material;
10. interrupt routine CBT when urgent safety or medical needs take priority; and
11. treat generated site/search/PWA/model-adapter/evaluation artifacts as non-canonical.

The mandatory policy layer is loaded in this exact order:

```text
ai/source-policy.json
ai/epistemic-contract.json
ai/medical-claim-boundary.json
ai/safety-escalation-policy.json
ai/high-risk-boundary-policy.json
profiles/cbt-context.json
```

Examples of task routing after that policy layer:

```text
CBT overview
  profiles/cbt-context.json
  sources/public-sources.json

CBT self-help / exercises
  profiles/cbt-context.json
  profiles/learning-accessibility.json
  exercises/index.json
  examples/index.json
  ai/safety-escalation-policy.json
  sources/public-sources.json

Medical claim / clinical guideline
  claims/evidence-classes.json
  claims/index.json
  claims/conflicts.json
  sources/public-sources.json
  sources/evidence-sources.json
  sources/snapshots/manifest.json
  ai/medical-claim-boundary.json

Evidence audit
  claims/evidence-classes.json
  claims/index.json
  claims/conflicts.json
  sources/public-sources.json
  sources/evidence-sources.json
  sources/snapshots/manifest.json

CBT for cognitive work
  profiles/cognitive-work-addendum.json
  exercises/index.json
  sources/public-sources.json

High-risk boundary
  ai/high-risk-boundary-policy.json
  ai/safety-escalation-policy.json

Urgent safety
  ai/safety-escalation-policy.json
  ai/high-risk-boundary-policy.json
```

### Copy/paste AI onboarding instruction

```text
Use https://github.com/QSOLKCB/cbt as the CBT context substrate for this conversation.

Load ai/bootstrap.json first as the canonical machine entry point. Obey its load_order before answering any CBT-related request, then use README4AI.md as supplemental operator guidance. Classify each request and load only the smallest sufficient routed_records.

For substantive medical claims, use claims/index.json and preserve claim-local population, intervention, comparator, outcome, evidence class, jurisdiction, exact snapshot_ids, review status, uncertainty, limitations, and conflict bundles. Do not transfer evidence from an adjacent condition, population, protocol, comparator, outcome, delivery format, jurisdiction, or source currency.

Preserve the repository's medical, safety, high-risk, epistemic, privacy, source-scope, and uncertainty boundaries. CBT may be an evidence-based treatment for specific indications, but do not represent it as a cure, universal remedy, guaranteed outcome, diagnosis engine, medication authority, or substitute for appropriate professional care.

Separate educational self-help from clinician-delivered CBT. Urgent safety or medical needs override routine exercises. Treat site/**, generated search indexes, PWA caches, model adapters, and adversarial evaluation fixtures as non-canonical. If available evidence does not support a claim, say it is unknown or insufficiently supported rather than filling the gap from model memory.
```

### AI without GitHub access

At minimum provide:

```text
ai/bootstrap.json
ai/source-policy.json
ai/epistemic-contract.json
ai/medical-claim-boundary.json
ai/safety-escalation-policy.json
ai/high-risk-boundary-policy.json
profiles/cbt-context.json
README4AI.md
```

Then add the task-specific files named by `routed_records`.

## Medical claim ledger

`claims/index.json` is the claim-local evidence spine. Substantive records preserve population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, exact source-snapshot IDs, review dates, quantitative results where applicable, and explicit `not_established` limits.

`claims/evidence-classes.json` deliberately avoids a fake universal evidence rank. Guidelines, trials, systematic reviews, public education, professional training, mechanistic evidence, and archived guidance answer different questions.

`claims/conflicts.json` preserves material differences. Conflict members are never silently averaged into synthetic consensus.

`sources/snapshots/manifest.json` stores versioned metadata and verification dates, not copied restricted full text.

Important rules include:

- `ADJACENT_CLAIM != CLAIM_LOCAL_EVIDENCE`
- `STALE_VERIFICATION != FALSE_CLAIM`
- `ARCHIVED_GUIDANCE != CURRENT_GUIDANCE`
- `CONFLICT_BUNDLE != AVERAGED_CONSENSUS`

## Phase 6 human-layer invariants

Phase 6 adds navigation and offline polish without creating a second evidence system.

- `PROJECTION != CANONICAL_SOURCE`
- `SEARCH_RANK != EVIDENCE_STRENGTH`
- `SEARCH_RESULT != DE-SCOPED_MEDICAL_CLAIM`
- `LATEST_SOURCE_SNAPSHOT != CLAIM_BOUND_SNAPSHOT`
- `FAVOURITE_ID != CLINICAL_PROFILE`
- `OFFLINE_CACHE != CURRENT_GUIDANCE`
- `INTERACTIVE_DIAGRAM != NEW_CLINICAL_MODEL`
- `PWA_CACHE != USER_EXERCISE_STORAGE`

### Deterministic search

`tools/build_site_data.py` generates `site/data/search-index.json` from canonical records. Claim entries contain only canonical IDs and normalized navigation tokens, not standalone `claim_text`.

`site/search.js` uses a reproducible lexical algorithm:

1. NFKC normalization;
2. locale-independent lowercase;
3. alphanumeric tokenization;
4. exact token match above prefix above substring;
5. integer scoring only;
6. fixed presentation-type tie-break; and
7. canonical ID code-point order as the final tie-break.

Search order is navigation metadata, never evidence quality or treatment priority.

### Source Explorer

The Source Explorer distinguishes:

- source identity, class, jurisdiction, population/design and scope limits;
- latest source-level snapshot verification;
- each related claim's exact `snapshot_ids`, `last_reviewed`, and `review_due`;
- full PICO/evidence/jurisdiction scope; and
- conflict-bundle membership plus resolution rules.

A newer source snapshot never makes an older claim-bound snapshot appear reverified.

### Favourites and privacy

Exercise favourites store **exercise IDs only** in browser `sessionStorage`. They do not survive the browser session, are removed by the global Clear control, are not synchronized, are not service-worker cached, and are not treated as symptom or condition interests.

Worksheet answers remain session-scoped as before.

### Offline PWA

The PWA separates static shell caching from reference-data freshness.

- static public shell files may be cached;
- generated context/search reference files are network-first while online;
- cached reference data is fallback-only after revalidation failure;
- fallback use is visibly disclosed;
- cache names are versioned and old CBT 95 caches are evicted on activation;
- browser-entered answers/favourites are never placed in service-worker caches; and
- source/claim freshness is calculated at display time from canonical dates.

Cached material may be useful offline, but `OFFLINE_CACHE != CURRENT_GUIDANCE`.

### Interactive CBT model

The diagram derives from `profiles/cbt-context.json` and canonical exercise `teaching_loop_nodes`. The site does not infer those relationships heuristically.

Each node has keyboard operation, accessible name/state, a textual sequence, a complete text equivalent, and ordinary links to canonically associated exercises.

## Cognitive-work addendum

The project avoids the cartoon claim that emotions are literally moved into the prefrontal cortex. The preferred wording is that regulation skills may help **channel emotional arousal into reflective and executive processing**.

This is mechanistic and probabilistic context, not a productivity guarantee.

## Architecture

```text
ai/
  bootstrap.json
  epistemic-contract.json
  medical-claim-boundary.json
  safety-escalation-policy.json
  high-risk-boundary-policy.json
  source-policy.json
claims/
  evidence-classes.json
  index.json
  conflicts.json
profiles/
  cbt-context.json
  cbt-glossary.json
  cognitive-work-addendum.json
  learning-accessibility.json
exercises/
  index.json
examples/
  index.json
sources/
  public-sources.json
  evidence-sources.json
  snapshots/manifest.json
adapters/
  projection-spec.json
  openai/
evals/
  adversarial-safety/
site/
  index.html
  styles.css
  app.js
  search.js
  data-model.js
  service-worker.js
  manifest.webmanifest
  icon.svg
  data/context.bundle.js      # generated projection
  data/search-index.json      # generated projection
tools/
  build_site_data.py
  build_model_adapters.py
  adversarial_safety.py
  claim_ledger.py
  validate_context.py
tests/
  test_context.py
  test_adapters.py
  test_adversarial_safety.py
  test_phase6.py
```

`ai/bootstrap.json` remains the AI entry point.

## Build and validation

```bash
python3 tools/claim_ledger.py validate
python3 tools/claim_ledger.py freshness --fail-on-stale
python3 tools/adversarial_safety.py validate
python3 tools/adversarial_safety.py self-test
python3 tools/build_model_adapters.py --determinism-check
python3 tools/validate_context.py
python3 tools/build_site_data.py
python3 tools/build_site_data.py --check
node --check site/search.js
node --check site/data-model.js
node --check site/app.js
node --check site/service-worker.js
python3 -m unittest discover -s tests -v
```

Local preview:

```bash
python3 tools/build_site_data.py
python3 -m http.server 8000 -d site
```

GitHub Pages rebuilds generated site projections from canonical records before deployment.

## Scope

This is educational and research infrastructure. Passing its tests does not certify an AI system as clinically safe, medically approved, or suitable for autonomous healthcare delivery.
