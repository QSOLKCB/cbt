#!/usr/bin/env python3
"""Fail-closed structural validation for CBT 95."""
from __future__ import annotations
import json
from pathlib import Path
from adversarial_safety import validate_suite
from build_model_adapters import verify_noncanonical_boundaries
from claim_ledger import validate_repository
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def require(condition,message):
 if not condition: raise SystemExit(f"validation failed: {message}")
def main():
 b=load("ai/bootstrap.json"); boundary=load("ai/medical-claim-boundary.json"); epi=load("ai/epistemic-contract.json"); safety=load("ai/safety-escalation-policy.json"); high=load("ai/high-risk-boundary-policy.json"); sources=load("sources/public-sources.json"); evidence=load("sources/evidence-sources.json"); exercises=load("exercises/index.json"); examples=load("examples/index.json"); access=load("profiles/learning-accessibility.json"); work=load("profiles/cognitive-work-addendum.json")
 required=["ai/source-policy.json","ai/epistemic-contract.json","ai/medical-claim-boundary.json","ai/safety-escalation-policy.json","ai/high-risk-boundary-policy.json","profiles/cbt-context.json"]; require(b["load_order"]==required,"policy load order changed")
 for needed in ("sources/public-sources.json","profiles/learning-accessibility.json","examples/index.json"): require(needed in b["routed_records"]["cbt_self_help"],f"self-help route missing {needed}")
 for route in ("medical_claim","clinical_guideline","evidence_audit"):
  for needed in ("claims/evidence-classes.json","claims/index.json","claims/conflicts.json","sources/evidence-sources.json","sources/snapshots/manifest.json"): require(needed in b["routed_records"][route],f"{route} route missing {needed}")
 for route in ("high_risk_boundary","urgent_safety"):
  require("ai/high-risk-boundary-policy.json" in b["routed_records"][route],f"{route} route missing high-risk boundary policy"); require("ai/safety-escalation-policy.json" in b["routed_records"][route],f"{route} route missing safety escalation policy")
 for guard in {"CBT != CURE","CBT != UNIVERSAL_REMEDY","SELF_HELP_CBT != CLINICIAN_DELIVERED_CBT","AI_CONTEXT != DIAGNOSIS","AI_CONTEXT != CLINICAL_AUTHORITY"}: require(guard in set(boundary["hard_guards"]),f"missing guard {guard}")
 for guard in {"CHAT_CONTEXT != DIAGNOSIS","SELF_HELP_CBT != INTENSIVE_TRAUMA_PROCESSING","SELF_HELP_CBT != PSYCHOSIS_ASSESSMENT","SELF_HELP_CBT != MANIA_ASSESSMENT","SELF_HELP_CBT != EATING_DISORDER_ASSESSMENT","SELF_HELP_CBT != SUBSTANCE_WITHDRAWAL_MANAGEMENT","USER_DISCLOSURE != HIDDEN_CLINICAL_PROFILE","PRODUCTIVITY != SAFETY_PRIORITY","DISTRESS_OR_NONRESPONSE != PERSONAL_FAILURE"}: require(guard in set(high["hard_guards"]),f"missing high-risk guard {guard}")
 require(set(high["contexts"])=={"trauma","possible_psychosis","possible_mania","eating_disorder","substance_use"},"high-risk context set changed"); require(high["urgent_safety_precedence"]=="ai/safety-escalation-policy.json","high-risk policy must defer to urgent safety policy"); require(epi["fallback_state"]=="unknown","epistemic contract must fail to unknown"); require(safety["principle"]=="urgent safety needs override routine CBT exercises","safety override weakened"); require("move emotion into the prefrontal cortex" in work["avoid_framing"],"neuroscience cartoon guard missing"); require(work.get("evidence_scope") and work.get("mechanism_summary") and work.get("guardrails"),"cognitive-work guardrails incomplete")
 records=sources["sources"]+evidence["sources"]; source_ids={s["id"] for s in records}; require(len(source_ids)==len(records),"duplicate source id across registries")
 ids=set(); require(len(exercises["exercises"])>=10,"phase-2 exercise baseline shrank")
 for ex in exercises["exercises"]:
  require(ex["id"] not in ids,f"duplicate exercise {ex['id']}"); ids.add(ex["id"])
  for field in ("purpose","prompts","mechanism","not_established","pause_or_support","source_ids"): require(ex.get(field),f"{ex['id']} missing {field}")
  for sid in ex["source_ids"]: require(sid in source_ids,f"{ex['id']} references unknown source {sid}")
 require({"worry-time","graded-task-ladder","behavioural-experiment","setback-plan"}.issubset(ids),"phase-2 exercise missing"); require("affect-to-action" in ids,"cognitive-work route dependency affect-to-action missing"); require(ids==set(access["plain_language_exercises"]),"plain-language variants must cover every exercise"); require(ids==set(examples["examples"]),"synthetic examples must cover every exercise"); require(any("never reads user-entered answers" in x for x in examples["rules"]),"example privacy guard missing"); require(any("must not print user-entered answers" in x for x in access["principles"]),"blank-print privacy guard missing")
 claim_errors=validate_repository(ROOT); require(not claim_errors,"claim ledger invalid: "+"; ".join(claim_errors)); adapter_errors=verify_noncanonical_boundaries(); require(not adapter_errors,"model adapter boundary invalid: "+"; ".join(adapter_errors)); eval_errors=validate_suite(ROOT); require(not eval_errors,"adversarial safety suite invalid: "+"; ".join(eval_errors)); interface=b.get("evaluation_interfaces",{}).get("adversarial_safety",{}); require(interface.get("canonical") is False,"adversarial evaluation interface must remain noncanonical"); require(interface.get("runner")=="tools/adversarial_safety.py","adversarial evaluator runner mismatch"); print("CBT context validation: ok"); return 0
if __name__=="__main__": raise SystemExit(main())
