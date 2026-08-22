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
- `CHAT_CONTEXT != DIAGNOSIS`
- `SELF_HELP_CBT != INTENSIVE_TRAUMA_PROCESSING`
- `SELF_HELP_CBT != PSYCHOSIS_ASSESSMENT`
- `SELF_HELP_CBT != MANIA_ASSESSMENT`
- `SELF_HELP_CBT != EATING_DISORDER_ASSESSMENT`
- `SELF_HELP_CBT != SUBSTANCE_WITHDRAWAL_MANAGEMENT`
- `USER_DISCLOSURE != HIDDEN_CLINICAL_PROFILE`
- `PRODUCTIVITY != SAFETY_PRIORITY`
- `DISTRESS_OR_NONRESPONSE != PERSONAL_FAILURE`

Do not weaken these to make an answer smoother.

## Clinical language rule

Do not “correct” the project into saying CBT is never a treatment. NHS/NICE guidance does recommend CBT as a treatment for multiple indications. The boundary is that **treatment does not mean cure**, and a population-level recommendation does not become individualized medical advice.

## Claim ledger

Substantive medical claims belong in `claims/index.json`. Preserve population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, snapshots, review dates, and limitations. Do not inherit evidence across condition, population, protocol, comparator, outcome, or delivery format. Preserve conflicts instead of averaging them. Stale verification means review is due, not automatic falsehood. Archived guidance remains historical only.

## Source snapshots

`sources/snapshots/manifest.json` stores identifiers, bibliographic/status metadata, repository-authored summaries, dates, and metadata fingerprints only. Do not copy restricted full text.

## Model adapter projections

`adapters/projection-spec.json` and `tools/build_model_adapters.py` define noncanonical transport projections. Generated outputs live under `adapters/generated/` and never satisfy evidence provenance or canonical routing. `PROJECTION != CANONICAL_SOURCE`.

## High-risk boundary policy

`ai/high-risk-boundary-policy.json` is mandatory policy and is loaded before `profiles/cbt-context.json`.

It defines boundary handling for trauma, possible psychosis, possible mania, eating-disorder, and substance-use contexts without turning this repository into a diagnostic or condition-specific treatment system.

Rules include no chat diagnosis; no intensive trauma reliving/exposure as generic self-help; no medication change/taper instructions; no detoxification or withdrawal-management instructions; no victim blaming or coercive reframing; no hidden clinical profiling; no productivity-over-safety framing; professional assessment when symptoms are severe, worsening, unclear, or substantially impairing; and urgent safety precedence.

## Phase 5 adversarial safety evaluation

`evals/adversarial-safety/**` and `tools/adversarial_safety.py` define synthetic conformance tests.

The evaluation layer is **noncanonical**. It tests policy conformance; it does not create medical evidence, treatment rules, or clinical certification.

Every case must map to a Phase 5 category, bind expected behavior to stable invariant IDs, resolve those IDs to canonical policy/profile records, avoid exact-response wording as the acceptance criterion, keep acute-risk prompts non-method-specific, and avoid real user records or sensitive personal data.

The deterministic scorer consumes a structured **judge observation envelope**. It does not claim to infer arbitrary model prose by itself. A human or semantic judge maps model output to the envelope before scoring.

CI validates the suite, renders the hidden-rubric-free prompt pack, checks determinism, and runs the evaluator self-test. Do not add `evals/**` paths to claim provenance or canonical bootstrap routing.

## Exercise design

Each exercise must state educational purpose, steps, mechanism, limitations, and when to pause or seek support. Do not score responses diagnostically.

## Cognitive-work addendum

Never claim emotion is literally transferred into the prefrontal cortex. Affect labelling, reappraisal, and task decomposition are mechanistic/probabilistic framings, not productivity guarantees.

## Safety

Urgent safety needs override routine exercises. Do not hardcode crisis phone numbers into canonical policy. Runtime systems resolve current local resources. Do not add autonomous diagnosis, medication changes, involuntary-treatment decisions, or risk clearance.

## Privacy

Generic exercises should not require sensitive personal data. The human site stores exercise state only in the browser session and offers clear/reset controls. Do not build hidden clinical profiles.

## Evidence discipline

Every new substantive medical or neuroscience claim must identify a source, preserve population/jurisdiction/scope, avoid stronger wording than the source, expose uncertainty, use the correct evidence class, bind to a versioned snapshot, preserve conflicts, and pass validation/tests.
