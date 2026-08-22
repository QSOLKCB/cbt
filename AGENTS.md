# AGENTS.md

## Mission

Maintain a public, evidence-bounded CBT teaching resource and AI substrate.

## Non-negotiable invariants

- `CBT != CURE`
- `CBT != UNIVERSAL_REMEDY`
- `SELF_HELP_CBT != CLINICIAN_DELIVERED_CBT`
- `AI_CONTEXT != DIAGNOSIS`
- `AI_CONTEXT != CLINICAL_AUTHORITY`
- `GUIDELINE_RECOMMENDATION != INDIVIDUAL_MEDICAL_ADVICE`
- `CONFIDENCE != EVIDENCE`
- `PROJECTION != CANONICAL_SOURCE`
- `ADJACENT_CLAIM != CLAIM_LOCAL_EVIDENCE`
- `STALE_VERIFICATION != FALSE_CLAIM`
- `ARCHIVED_GUIDANCE != CURRENT_GUIDANCE`
- `CONFLICT_BUNDLE != AVERAGED_CONSENSUS`

Do not weaken these to make an answer smoother.

## Clinical language rule

Do not “correct” the project into saying CBT is never a treatment. NHS/NICE guidance does recommend CBT as a treatment for multiple indications. The boundary is that **treatment does not mean cure**, and a population-level recommendation does not become individualized medical advice.

## Claim ledger

Substantive medical claims belong in `claims/index.json`.

Each claim must preserve:

- population
- intervention
- comparator
- outcome
- evidence class
- jurisdiction
- source IDs
- source-snapshot IDs
- review dates
- material limitations / what is not established

Do not inherit a positive result from one condition, population, protocol, comparator, outcome, or delivery format into another.

Evidence classes are not a single ranking ladder. Guidelines, trials, systematic reviews, public education, mechanistic evidence, professional training material, and archived guidance answer different questions.

`claims/conflicts.json` preserves material differences. Do not average incompatible findings into a synthetic “consensus”. Resolve apparent conflicts only by explicit scope, jurisdiction, intervention, comparator, outcome, authority, or currency rules.

A stale source snapshot means repository verification is due. It does **not** mean the underlying claim is automatically false.

Archived guidance remains available for provenance but must never be presented as current guidance.

## Source snapshots

`sources/snapshots/manifest.json` stores identifiers, bibliographic/status metadata, repository-authored summaries, dates, and metadata fingerprints only.

Do not copy restricted full text into source snapshots. A metadata fingerprint is not a hash of the remote article or guideline body.

## Exercise design

Each exercise must state:

- educational purpose
- steps
- “What CBT is doing here”
- what the exercise does not establish
- when to pause or seek appropriate support

Do not score a person’s responses as diagnostic.

## Cognitive-work addendum

Never claim emotion is literally transferred into the prefrontal cortex.

Permitted framing: affect labelling, reappraisal, and task decomposition may help regulate emotional responding and support reflective/executive processing. The evidence is mechanistic and probabilistic, not a productivity guarantee.

## Safety

Urgent safety needs override routine exercises.

Do not hardcode crisis phone numbers into canonical machine policy. Runtime systems should resolve current local emergency and crisis resources for the user’s jurisdiction.

Do not add autonomous diagnosis, medication initiation/discontinuation/dose changes, involuntary-treatment decisions, or risk clearance.

## Privacy

Generic exercises should not require sensitive personal data. The human site stores exercise state only in the browser session and offers a clear/reset control. Do not build hidden clinical profiles.

## Evidence discipline

Every new substantive medical or neuroscience claim must:

1. identify a source;
2. preserve population, jurisdiction, and scope;
3. avoid stronger wording than the source;
4. expose material uncertainty;
5. use the correct evidence class;
6. bind to a versioned source snapshot;
7. preserve conflicts instead of smoothing them away;
8. pass validation and tests.
