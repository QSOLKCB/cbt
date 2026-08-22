# Phase 6 — Encarta 95 polish design contract

Status: **scaffolding / review target only**. This file exists so Phase 6 architecture can be reviewed before the remaining implementation lands.

## Goal

Complete the human-facing CBT 95 layer without weakening the canonical medical, safety, privacy, evidence, or projection boundaries established in Phases 1–5.

Phase 6 remains a presentation / navigation layer. It does not create new medical claims, clinical authority, source authority, or evidence strength.

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

## Search and glossary

Search is navigation only.

The generated search projection may index:

- exercise titles, purposes, mechanisms and IDs;
- glossary terms and educational definitions;
- source titles, classes, jurisdictions and scope metadata;
- claim titles/text and identifiers for navigation back to claim-local records.

Search scoring, result order, keyword frequency, or vector similarity must never be interpreted as evidence quality, treatment priority, clinical relevance to a particular person, or source authority.

The search index must be deterministic and generated from canonical repository records.

## Source Explorer

The human Source Explorer should expose, where available:

- source title and ID;
- registry;
- source class;
- jurisdiction;
- population;
- study/design metadata;
- scope limitations;
- snapshot verification status and dates;
- related claim-local records.

It must preserve evidence-class and jurisdiction differences. It must not flatten sources into a single confidence score or synthetic consensus.

## Exercise favourites

Favourites are convenience state only.

Allowed persistence:

- exercise IDs;
- optional UI-only ordering/preferences.

Forbidden persistence:

- worksheet answers;
- synthetic example content merged with answers;
- inferred diagnoses;
- inferred trauma/substance/risk histories;
- hidden clinical profiles.

Exercise answers remain governed by the existing browser-session behavior.

## Offline PWA

The PWA may cache public application and reference assets for offline reading.

It must not place browser-entered exercise answers into the service-worker cache.

Offline mode must visibly communicate that cached medical/reference content may be stale and that time-sensitive guidance should be rechecked online before being treated as current.

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

Keyboard support must not rely on color alone for state.

## Interactive CBT model

The diagram must derive from the existing canonical teaching loop:

`situation -> thought_or_interpretation -> emotion_and_body -> behaviour -> consequence_or_feedback`

The interaction may explain each node and connect exercises to parts of the loop, but it must not invent a new clinical model, diagnosis path, severity score, or personalized formulation.

## Documentation cleanup

The follow-up PR should also update README onboarding examples so the documented mandatory policy order includes the Phase 5 high-risk boundary policy and matches `ai/bootstrap.json` exactly.

## Review question for Codex

Please review this design primarily for:

- accidental weakening of Phase 1–5 invariants;
- privacy leakage through favourites/PWA storage;
- PWA cache semantics that could imply stale guidance is current;
- search/source-explorer semantics that could accidentally become evidence ranking;
- accessibility/keyboard traps;
- any place the human projection could be mistaken for canonical medical evidence.

The actual Phase 6 implementation will land in a separate follow-up PR after this architecture review.
