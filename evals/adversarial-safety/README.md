# Phase 5 adversarial safety evaluation

This directory contains **synthetic conformance tests**, not clinical examples and not medical evidence.

The suite pressures eight CBT 95 boundaries:

1. cure-language pressure
2. diagnostic-certainty pressure
3. medication-change requests
4. coercive reframing and victim blaming
5. trauma / possible psychosis / possible mania / eating-disorder / substance-use boundaries
6. acute-risk interruption of routine exercises
7. privacy leakage and hidden profiling
8. productivity-at-any-cost pressure

## Architecture

`cases.json` contains the user-side adversarial prompts and hidden expected response obligations.

`invariants.json` binds every expected obligation back to a canonical CBT 95 policy or profile record. The evaluation layer is not allowed to invent medical authority.

`response-envelope.schema.json` defines the structured observation envelope used for deterministic scoring.

`tools/adversarial_safety.py` provides:

```bash
python3 tools/adversarial_safety.py validate
python3 tools/adversarial_safety.py render --output /tmp/cbt-adversarial-prompts.jsonl
python3 tools/adversarial_safety.py render --output /tmp/cbt-adversarial-prompts.jsonl --check
python3 tools/adversarial_safety.py determinism-check
python3 tools/adversarial_safety.py self-test
python3 tools/adversarial_safety.py score --responses judged-responses.jsonl
```

## Important limitation

The repository does **not** pretend a lexical script can understand arbitrary model prose safely.

The intended evaluation flow is:

1. render the hidden-rubric-free prompt pack;
2. run those prompts against the model/adapter under test;
3. have a separate human or semantic judge map each response into the structured observation envelope;
4. use the deterministic scorer to check that envelope against the hidden case obligations.

The scorer therefore validates a structured judge result. It does not certify the semantic quality of the judge itself.

A passing run means the tested responses conformed to this rubric. It does **not** certify a model as clinically safe, medically approved, or suitable for autonomous care.

## Safety of the fixtures

Acute-risk prompts remain non-method-specific. The suite tests whether routine CBT is interrupted, whether urgent support takes priority, and whether the model refuses autonomous risk clearance. It is not a corpus of crisis methods or instructions.
