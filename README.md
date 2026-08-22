# CBT

**CBT 95** is an evidence-bounded Cognitive Behavioural Therapy (CBT) reference, exercise lab, and AI context substrate.

The project has two layers:

1. a machine-readable substrate that teaches an AI how to reason about CBT without crossing medical claim boundaries; and
2. an Encarta-95-style human layer where people can learn what CBT is by trying small, low-risk exercises and seeing what each exercise is doing.

## Core boundary

CBT is a structured psychological intervention and is an evidence-based treatment for some conditions when supported by applicable clinical guidance. This repository does **not** represent CBT as a cure, universal remedy, guaranteed outcome, diagnosis engine, or replacement for appropriate professional care.

Machine guards:

- `CBT != CURE`
- `CBT != UNIVERSAL_REMEDY`
- `SELF_HELP_CBT != CLINICIAN_DELIVERED_CBT`
- `AI_CONTEXT != DIAGNOSIS`
- `AI_CONTEXT != CLINICAL_AUTHORITY`
- `SYMPTOM_IMPROVEMENT != DISEASE_ERADICATION`
- `GUIDELINE_RECOMMENDATION != INDIVIDUAL_MEDICAL_ADVICE`
- `CONFIDENCE != EVIDENCE`

## What the exercise layer is for

The exercises are educational demonstrations of CBT mechanisms. They help a person observe links among:

**situation → thought → emotion/body → behaviour → consequence**

and experiment with changing one part of that loop.

Every exercise includes a **What CBT is doing here** explanation. Exercises are not scored as “right” or “wrong”, and the site does not diagnose users from their answers.

Initial exercises include:

- the 7-step thought record
- Catch → Check → Change
- behaviour-loop mapping
- tiny-step activity planning
- structured problem solving
- a cognitive-work exercise for coding, study, writing, debugging, and research

## Cognitive-work addendum

The project deliberately avoids the cartoon claim that emotions are literally “moved into the prefrontal cortex”.

A more defensible description is that skills such as affect labelling, cognitive reappraisal, and task decomposition can sometimes help **channel emotional arousal into reflective and executive processing**. That may make it easier to re-engage attention and choose a next action during cognitively demanding work.

This is a possible mechanism and practical framing, not a deterministic brain switch or productivity guarantee.

## Ethical baseline

The policy layer is grounded in public, authoritative sources from:

- Medical Board of Australia
- Australian Commission on Safety and Quality in Health Care
- NHS and the NHS Constitution for England
- NICE
- NHS Every Mind Matters
- peer-reviewed neuroimaging literature used only for the cognitive-work mechanism addendum

See `sources/public-sources.json`.

## Architecture

```text
ai/
  bootstrap.json
  epistemic-contract.json
  medical-claim-boundary.json
  safety-escalation-policy.json
  source-policy.json
profiles/
  cbt-context.json
  cognitive-work-addendum.json
exercises/
  index.json
sources/
  public-sources.json
site/
  index.html
  styles.css
  app.js
  data/context.bundle.js   # generated projection
tools/
  build_site_data.py
  validate_context.py
tests/
  test_context.py
```

`ai/bootstrap.json` is the entry point for AI systems.

## Validation

```bash
python3 tools/validate_context.py
python3 tools/build_site_data.py --check
python3 -m unittest discover -s tests -v
```

## Scope

This is educational and research infrastructure. Passing its tests does not certify an AI system as clinically safe, medically approved, or suitable for autonomous healthcare delivery.
