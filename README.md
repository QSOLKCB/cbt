# CBT

> **Use CBT 95:** https://qsolkcb.github.io/cbt/
>
> **On-board an AI:** start with [`README4AI.md`](README4AI.md), then load [`ai/bootstrap.json`](ai/bootstrap.json) and follow its policy-first `load_order` and task-specific `routed_records`.

**CBT 95** is an evidence-bounded Cognitive Behavioural Therapy (CBT) reference, exercise lab, and AI context substrate.

The project has two layers:

1. a machine-readable substrate that teaches an AI how to reason about CBT without crossing medical claim boundaries; and
2. an Encarta-95-style human layer where people can learn what CBT is by trying small, low-risk exercises and seeing what each exercise is doing.

## Use CBT 95 as a person

Open the live educational desk:

**https://qsolkcb.github.io/cbt/**

The site is the human-facing learning layer. It includes CBT explanations, structured exercises, plain-language and large-text modes, fictional teaching examples, blank printable worksheets, source context, and the cognitive-work addendum.

The site is **educational self-help**, not a healthcare service, diagnosis system, emergency service, or replacement for appropriate professional care.

## On-board an AI with the CBT substrate

The repository itself is the AI-facing layer. Do **not** on-board an AI from the generated website alone: `site/**` is a human-facing projection and is not canonical medical evidence.

### AI with GitHub or repository access

Give the AI this repository:

`https://github.com/QSOLKCB/cbt`

Then instruct it to:

1. read `README4AI.md`;
2. load `ai/bootstrap.json` as the machine entry point;
3. obey the bootstrap `load_order` **before** loading task-specific CBT material;
4. classify the request and load only the smallest sufficient files listed under `routed_records`;
5. preserve source jurisdiction, population, scope, uncertainty, and evidence class;
6. keep self-help education separate from clinician-delivered CBT;
7. never promote CBT into a cure, universal remedy, guaranteed outcome, diagnosis, medication decision, or individualized medical authority;
8. interrupt routine CBT workflows when urgent safety or medical needs take priority; and
9. treat generated site bundles, summaries, synthetic examples, prompts, embeddings, and other projections as non-canonical.

The mandatory policy layer is currently loaded in this order:

```text
ai/source-policy.json
ai/epistemic-contract.json
ai/medical-claim-boundary.json
ai/safety-escalation-policy.json
profiles/cbt-context.json
```

After that, `ai/bootstrap.json` routes the task to the smallest sufficient context. For example:

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

Medical claim or clinical guideline question
  sources/public-sources.json
  ai/medical-claim-boundary.json

CBT for cognitive work
  profiles/cognitive-work-addendum.json
  exercises/index.json
  sources/public-sources.json

Urgent safety
  ai/safety-escalation-policy.json
```

### Copy/paste AI onboarding instruction

```text
Use https://github.com/QSOLKCB/cbt as the CBT context substrate for this conversation.

Read README4AI.md first, then load ai/bootstrap.json. Obey its load_order before answering any CBT-related request. Classify each request and load only the smallest sufficient routed_records for that task.

Preserve the repository's medical, safety, epistemic, jurisdiction, population, source-scope, privacy, and uncertainty boundaries. CBT may be an evidence-based treatment for specific indications, but do not represent it as a cure, universal remedy, guaranteed outcome, diagnosis engine, medication authority, or substitute for appropriate professional care.

Separate educational self-help from clinician-delivered CBT. Urgent safety or medical needs override routine exercises. Treat site/** and other generated projections as non-canonical. If the available evidence does not support a claim, say that it is unknown or insufficiently supported rather than filling the gap from model memory.
```

### AI without GitHub access

Provide the AI with the files directly. At minimum, give it:

```text
README4AI.md
ai/bootstrap.json
ai/source-policy.json
ai/epistemic-contract.json
ai/medical-claim-boundary.json
ai/safety-escalation-policy.json
profiles/cbt-context.json
```

Then add the task-specific files named in `routed_records`. For example, an exercise-capable assistant also needs `exercises/index.json`, `profiles/learning-accessibility.json`, `examples/index.json`, and `sources/public-sources.json`.

If context space is limited, prefer the bootstrap's **smallest-sufficient routing** rather than loading the entire repository and hoping the model sorts it out.

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
  learning-accessibility.json
exercises/
  index.json
examples/
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

## Build and validation

The site data is generated from canonical JSON and is intentionally not committed as medical evidence.

```bash
python3 tools/validate_context.py
python3 tools/build_site_data.py
python3 tools/build_site_data.py --check
python3 -m unittest discover -s tests -v
```

For a local preview after building:

```bash
python3 -m http.server 8000 -d site
```

GitHub Pages performs the same build from canonical records when `main` is deployed.

## Scope

This is educational and research infrastructure. Passing its tests does not certify an AI system as clinically safe, medically approved, or suitable for autonomous healthcare delivery.
