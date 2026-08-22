# Phase 6 — Encarta 95 polish design contract

Status: **scaffolding / review target only**. This file exists so Phase 6 architecture can be reviewed before the remaining implementation lands.

## Goal

Complete the human-facing CBT 95 layer without weakening the canonical medical, safety, privacy, evidence, or projection boundaries established in Phases 1–5.

Phase 6 remains a presentation / navigation layer. It does not create new medical claims, clinical authority, source authority, evidence strength, or personalized formulation.

## Planned completion PR

The follow-up implementation PR will complete:

1. deterministic search index and CBT glossary;
2. Source Explorer;
3. exercise favourites;
4. offline PWA packaging;
5. keyboard-first navigation;
6. interactive “How this maps to the CBT model” diagram.

## Non-negotiable invariants

- `PROJECTION != CANONICAL_SOURCE`
- `SEARCH_RANK != EVIDENCE_STRENGTH`
- `FAVOURITE_ID != CLINICAL_PROFILE`
- `OFFLINE_CACHE != CURRENT_GUIDANCE`
- `INTERACTIVE_DIAGRAM != NEW_CLINICAL_MODEL`
- `PWA_CACHE != USER_EXERCISE_STORAGE`
- `LATEST_SOURCE_SNAPSHOT != CLAIM_BOUND_SNAPSHOT`
- `SEARCH_RESULT != DE-SCOPED_MEDICAL_CLAIM`

## Search and glossary

Search is navigation only.

The generated search projection may index:

- exercise titles, purposes, mechanisms and IDs;
- glossary terms and educational definitions;
- source titles, classes, jurisdictions and scope metadata;
- claim identifiers plus deterministic search tokens derived from claim-local records.

### Claim-scope rule

A substantive claim must never be displayed or exported as claim text detached from its claim-local scope.

If a search result displays substantive claim wording, the same result must visibly carry, or immediately render from the canonical claim record:

- population;
- intervention;
- comparator;
- outcome;
- evidence class;
- jurisdiction;
- source IDs;
- the claim's exact `snapshot_ids`;
- `last_reviewed` and `review_due`;
- `not_established` limitations;
- conflict-bundle membership when applicable.

A compact search index may store only claim ID + normalized search tokens and reconstruct the displayed result from the canonical claim record. It must not publish a standalone de-scoped `claim_text` projection.

### Deterministic query ranking

Phase 6 search is deliberately lexical. The baseline implementation must not depend on approximate vector search, an external embedding model, browser-specific locale ranking, wall-clock state, or nondeterministic relevance APIs.

The follow-up PR must define and test one reproducible query pipeline. Baseline contract:

1. Unicode-normalize indexed text and query with NFKC;
2. lowercase using locale-independent semantics;
3. replace non-alphanumeric runs with a single space;
4. split on spaces and remove empty tokens;
5. score exact token matches above prefix matches, and prefix matches above substring matches;
6. sum integer scores only;
7. use a fixed type-order only as a documented presentation tie-break, never as evidence priority;
8. resolve all remaining ties by stable canonical identifier in ascending code-point order.

The same repository bytes and same query must therefore produce the same result order.

Search scoring, result order, keyword frequency, or any future vector similarity must never be interpreted as evidence quality, treatment priority, clinical relevance to a particular person, or source authority.

The search index and query algorithm must both be deterministic and generated from canonical repository records.

## Source Explorer

The human Source Explorer should expose, where available:

- source title and ID;
- registry;
- source class;
- jurisdiction;
- population;
- study/design metadata;
- scope limitations;
- source-level snapshot verification status and dates;
- related claim-local records.

### Claim-bound snapshot rule

For every displayed related claim, the Explorer must show that claim's own:

- `snapshot_ids`;
- `last_reviewed`;
- `review_due`;
- evidence class and jurisdiction;
- PICO scope and `not_established` limits.

The UI may also show the latest snapshot known for a source, but it must label that separately. A newer source snapshot must never make an older claim-bound snapshot appear reverified without a claim-ledger update.

`LATEST_SOURCE_SNAPSHOT != CLAIM_BOUND_SNAPSHOT`

### Conflict preservation

If a displayed claim belongs to a bundle in `claims/conflicts.json`, the Explorer must visibly surface:

- the conflict-bundle ID;
- bundle status;
- `resolution_rule`;
- all linked claim observations / claim IDs;
- the scope distinction that prevents silent averaging.

The Explorer must not display one member of a known material conflict as though the other observations do not exist.

It must preserve evidence-class and jurisdiction differences. It must not flatten sources into a single confidence score or synthetic consensus.

## Exercise favourites

Favourites are convenience state only.

To preserve the existing privacy contract, Phase 6 favourites are **session-scoped** by default.

Allowed session persistence:

- exercise IDs;
- optional UI-only ordering/preferences.

Storage requirements:

- use session-scoped browser state, not cross-session `localStorage` or IndexedDB, unless a future change explicitly revises the privacy contract and UI disclosure;
- the existing global Clear/reset control must remove favourite IDs/preferences as well as exercise answers;
- no favourite state may be inferred from worksheet text;
- favourites must not be synchronized, exported, cached by the service worker, or interpreted as symptom/condition interest.

Forbidden persistence:

- worksheet answers outside the existing session behavior;
- synthetic example content merged with answers;
- inferred diagnoses;
- inferred trauma/substance/risk histories;
- hidden clinical profiles.

Exercise answers remain governed by the existing browser-session behavior.

## Offline PWA

The PWA may cache public application and reference assets for offline reading.

It must not place browser-entered exercise answers, favourite state, form values, or other user-entered data into the service-worker cache.

### Online freshness and cache strategy

Evidence/reference projections must not be cache-first while the browser is online.

The follow-up implementation must:

- use network-first revalidation for the generated context/search/reference bundles when online;
- fall back to cached reference data only when the network request fails;
- visibly label a cached fallback as cached/offline-derived content;
- use versioned cache names tied to an explicit application/projection version;
- evict superseded cache versions during service-worker activation;
- never cache external journal/guideline pages as if they were part of CBT 95;
- keep static application-shell caching logically separate from evidence/reference freshness.

### Display-time freshness

The UI must calculate freshness from canonical dates against the browser's current date whenever source/claim status is displayed.

For source snapshots, compare the current date with `verified_on` and `verification_expires_on`.

For claims, compare the current date with `last_reviewed` and `review_due`.

Do not rely on a cached precomputed label such as `current_verification` after its date window has expired.

When offline or when an online revalidation fails, the UI must visibly communicate that cached medical/reference content may be stale and that time-sensitive guidance should be rechecked online before being treated as current.

`OFFLINE_CACHE != CURRENT_GUIDANCE`

The service worker must not convert cached site projections into canonical evidence.

## Keyboard-first navigation

The finished site should support:

- visible focus states;
- skip navigation;
- keyboard-operable route controls;
- Enter/Space activation where custom controls are used;
- arrow-key movement for grouped navigation where appropriate;
- a search-focus shortcut that does not interfere with typing in form controls;
- keyboard traversal of the interactive CBT model.

### Route-change focus contract

After client-side route activation replaces the contents of `#app`, focus must move to the newly rendered route content, preferably the page heading or the existing focusable `#app` container.

Focus movement must:

- avoid forcing the user to tab through the remaining menu/toolbar/sidebar to reach the new content;
- provide a programmatic route-change announcement for assistive technology;
- use `preventScroll` or equivalent care when focus movement would otherwise create an unwanted viewport jump;
- preserve sensible focus when an in-page control updates content without changing route.

Keyboard support must not rely on color alone for state.

## Interactive CBT model

The diagram must derive from the existing canonical teaching loop:

`situation -> thought_or_interpretation -> emotion_and_body -> behaviour -> consequence_or_feedback`

The interaction may explain each canonical node, but it must not invent a new clinical model, diagnosis path, severity score, or personalized formulation.

### Canonical exercise-to-node associations

The site must not heuristically infer which exercises belong to which loop nodes.

If Phase 6 displays exercise-to-node relationships, the follow-up PR must first add an explicit validated field such as `teaching_loop_nodes` to each applicable canonical exercise record in `exercises/index.json`.

Validation must require every associated node to exist in `profiles/cbt-context.json` → `teaching_model.loop`.

The human site then projects those canonical associations. It must not author them independently in `site/app.js` or a generated search file.

### Diagram accessibility

The interactive diagram must have a complete non-visual equivalent.

Requirements:

- each node is a semantic control with an accessible name;
- selected/current state is programmatically exposed (`aria-pressed`, `aria-selected`, or an equivalent appropriate pattern);
- arrow relationships are represented in text, not only visually;
- the complete canonical node sequence is available as ordinary text/list content;
- each node's explanation is available without requiring pointer interaction;
- any canonical exercise associations are also exposed as ordinary text links/list items;
- keyboard focus order follows the canonical loop order.

A screen-reader user must be able to understand the same loop, node explanations, and exercise associations without perceiving the graphical arrows.

## Documentation cleanup

The follow-up PR should also update README onboarding examples so the documented mandatory policy order includes the Phase 5 high-risk boundary policy and matches `ai/bootstrap.json` exactly.

## Required Phase 6 regression targets

The completion PR must add tests that fail if:

- a claim search result loses PICO/evidence/jurisdiction/snapshot/review/limitation scope;
- lexical search ordering changes for a fixed query and fixed repository;
- a conflict-member claim is shown without its bundle context;
- a claim is presented with a source's newest snapshot instead of its own bound snapshot;
- favourites survive the site's global Clear/reset or escape session-scoped storage;
- the service worker stores user-entered state;
- online evidence/reference requests become cache-first;
- old cache versions are not evicted;
- freshness labels ignore current date vs snapshot/claim review dates;
- route changes leave keyboard focus trapped in navigation chrome;
- diagram nodes lack semantic names/state/textual equivalents;
- exercise-to-node mappings are created outside canonical exercise records.

## Review question for Codex

Please review this design primarily for:

- accidental weakening of Phase 1–5 invariants;
- privacy leakage through favourites/PWA storage;
- PWA cache semantics that could imply stale guidance is current;
- search/source-explorer semantics that could accidentally become evidence ranking or de-scoped medical claims;
- conflict/snapshot provenance loss in the Source Explorer;
- accessibility/keyboard traps;
- any place the human projection could be mistaken for canonical medical evidence.

The actual Phase 6 implementation will land in a separate follow-up PR after this architecture review.
