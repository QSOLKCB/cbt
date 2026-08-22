#!/usr/bin/env python3
"""Build deterministic, non-canonical model-adapter projections for CBT 95."""
from __future__ import annotations
import argparse, hashlib, json, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PROJECTION_SPEC_PATH="adapters/projection-spec.json"
REQUIRED_OUTPUT_KEYS={"generic_system_prompt","local_compact","manifest","openai_responses","retrieval_bundle"}
def read_text(rel): return (ROOT/rel).read_text(encoding="utf-8")
def load_json(rel): return json.loads(read_text(rel))
def sha256_bytes(data): return "sha256:"+hashlib.sha256(data).hexdigest()
def sha256_text(text): return sha256_bytes(text.encode("utf-8"))
def projection_spec():
 spec=load_json(PROJECTION_SPEC_PATH); outputs=spec.get("outputs")
 if spec.get("type")!="cbt-model-adapter-projection-spec": raise ValueError("projection spec has unexpected type")
 if spec.get("canonical_evidence") is not False: raise ValueError("projection spec must remain noncanonical")
 if not isinstance(outputs,dict) or set(outputs)!=REQUIRED_OUTPUT_KEYS: raise ValueError("projection spec output keys do not match required adapter interface")
 names=[x.get("filename") for x in outputs.values()]
 if any(not isinstance(x,str) or not x for x in names) or len(names)!=len(set(names)): raise ValueError("projection spec output filenames invalid")
 if spec.get("builder")!="tools/build_model_adapters.py": raise ValueError("projection spec builder mismatch")
 return spec
def output_names(spec=None): spec=spec or projection_spec(); return tuple(sorted(x["filename"] for x in spec["outputs"].values()))
def output_filename(key,spec=None): spec=spec or projection_spec(); return spec["outputs"][key]["filename"]
def default_output_dir(spec=None): spec=spec or projection_spec(); return ROOT/spec["generated_output_dir"]
def canonical_inputs(bootstrap=None):
 bootstrap=bootstrap or load_json("ai/bootstrap.json"); paths={"ai/bootstrap.json",*bootstrap.get("load_order",[])}
 for routed in bootstrap.get("routed_records",{}).values(): paths.update(routed)
 return tuple(sorted(paths))
def route_map(bootstrap,inputs=None):
 inputs=inputs or canonical_inputs(bootstrap); mapping={p:[] for p in inputs}; mapping.setdefault("ai/bootstrap.json",[]).append("bootstrap")
 for p in bootstrap.get("load_order",[]): mapping.setdefault(p,[]).append("mandatory_policy")
 for route,paths in bootstrap.get("routed_records",{}).items():
  for p in paths: mapping.setdefault(p,[]).append(route)
 return {p:sorted(set(r)) for p,r in mapping.items()}
def projection_banner(kind,spec=None):
 spec=spec or projection_spec(); return f"{spec['projection_protocol']}\nKIND: {kind}\nPROJECTION_ONLY: true\nCANONICAL_EVIDENCE: false\nSOURCE_OF_TRUTH: ai/bootstrap.json + canonical routed records\nRULE: PROJECTION != CANONICAL_SOURCE\n"
def merged_guards(boundary,epi,high):
 out=[]
 for g in boundary.get("hard_guards",[])+epi.get("guards",[])+high.get("hard_guards",[]):
  if g not in out: out.append(g)
 return out
def append_high(lines,policy,compact=False):
 lines += ["","High-risk clinical boundaries",f"- {policy['principle']}."]; lines.extend(f"- {r}" for r in policy.get("general_rules",[]))
 for context,rules in policy.get("condition_boundaries",{}).items():
  if compact: lines.append(f"- {context}: "+" | ".join(rules))
  else:
   lines.append(f"- {context}:"); lines.extend(f"  - {r}" for r in rules)
 if not compact:
  lines += ["- Privacy boundaries:"]; lines.extend(f"  - {r}" for r in policy.get("privacy_rules",[])); lines += ["- Productivity boundaries:"]; lines.extend(f"  - {r}" for r in policy.get("productivity_rules",[]))
def build_system_prompt(spec=None):
 spec=spec or projection_spec(); b=load_json("ai/bootstrap.json"); m=load_json("ai/medical-claim-boundary.json"); e=load_json("ai/epistemic-contract.json"); s=load_json("ai/safety-escalation-policy.json"); h=load_json("ai/high-risk-boundary-policy.json"); p=load_json("profiles/cbt-context.json")
 lines=[projection_banner("generic-system-prompt",spec).rstrip(),"","You are using the CBT 95 evidence-bounded context substrate.","","Core role",f"- {p['definition']}","- This projection is transport guidance only. For substantive claims, retrieve and use the canonical repository records named by ai/bootstrap.json.","","Non-negotiable guards"]
 lines.extend(f"- {g}" for g in merged_guards(m,e,h)); lines += ["","Medical and evidence rules"]; lines.extend(f"- {r}" for r in b.get("instructions",[])); lines += ["","Urgent-safety override",f"- {s['principle']}.","- Pause routine CBT exercise when:"]; lines.extend(f"  - {r}" for r in s.get("pause_routine_exercise_when",[])); lines += ["- Safety response rules:"]; lines.extend(f"  - {r}" for r in s.get("response_rules",[])); lines += ["- Non-urgent assessment boundary:"]; lines.extend(f"  - {r}" for r in s.get("non_urgent_boundary",[])); append_high(lines,h); lines += ["","Response discipline",f"- Epistemic fallback state: {e.get('fallback_state','unknown')}.","- Distinguish authoritative guidance, evidence-supported claims, educational summaries, inference, user reports, unknowns, conflicts, and out-of-scope requests.","- Do not cite this projection or an adversarial fixture as evidence. Identify the underlying canonical policy, claim, or source record.","- If exact claim scope or freshness matters, retrieve claims/index.json, claims/conflicts.json, and sources/snapshots/manifest.json as routed by the bootstrap.",""]; return "\n".join(lines)
def build_local_compact(spec=None):
 spec=spec or projection_spec(); m=load_json("ai/medical-claim-boundary.json"); e=load_json("ai/epistemic-contract.json"); s=load_json("ai/safety-escalation-policy.json"); h=load_json("ai/high-risk-boundary-policy.json"); b=load_json("ai/bootstrap.json")
 lines=[projection_banner("compact-local-model",spec).rstrip(),"","CBT95 compact operating context:","CBT is a structured psychological intervention/tool and an evidence-based treatment for some indications. It is not a cure, diagnosis, universal remedy, guarantee, or substitute for appropriate care.","","GUARDS:"]; lines.extend(f"- {g}" for g in merged_guards(m,e,h)); lines += ["","CLAIMS:","- For substantive medical claims, retrieve canonical claims/index.json and preserve population, intervention, comparator, outcome, evidence class, jurisdiction, source IDs, snapshot IDs, limitations, and review dates.","- Never inherit evidence across condition, population, protocol, comparator, outcome, or delivery format.","- Preserve conflicts. Do not average incompatible claims.","- Archived guidance is historical only. Stale verification means review is due, not that the claim is false.","","SAFETY:",f"- {s['principle']}.","- Pause routine CBT exercise when:"]; lines.extend(f"  - {r}" for r in s.get("pause_routine_exercise_when",[])); lines += ["- Safety response rules:"]; lines.extend(f"  - {r}" for r in s.get("response_rules",[])); lines += ["- Non-urgent assessment boundary:"]; lines.extend(f"  - {r}" for r in s.get("non_urgent_boundary",[])); append_high(lines,h,True); lines += ["","SELF-HELP:","- Educational exercises are not automatically equivalent to clinician-delivered CBT.","- Do not force positive thinking, dismiss real danger/abuse/grief/material problems, or score answers diagnostically.","","ROUTING:"]
 for route,paths in b.get("routed_records",{}).items(): lines.append(f"- {route}: {', '.join(paths)}")
 lines += ["","This compact projection is not evidence. Retrieve canonical records for claim support.",""]; return "\n".join(lines)
def build_retrieval_bundle(spec=None):
 spec=spec or projection_spec(); b=load_json("ai/bootstrap.json"); inputs=canonical_inputs(b); mapping=route_map(b,inputs); parts=[projection_banner("retrieval-bundle",spec).rstrip(),""]
 for rel in inputs:
  content=read_text(rel).rstrip()+"\n"; parts += ["=== CBT95 CANONICAL RECORD PROJECTION ===",f"canonical_path: {rel}",f"canonical_sha256: {sha256_bytes((ROOT/rel).read_bytes())}",f"routes: {','.join(mapping.get(rel,[])) if mapping.get(rel,[]) else 'none'}","projection_only: true","canonical_evidence: false","content_follows:",content.rstrip(),"=== END CBT95 RECORD ===",""]
 return "\n".join(parts)
def build_openai(prompt,spec=None):
 spec=spec or projection_spec(); d=spec["generated_output_dir"].rstrip("/"); payload={"type":"cbt-openai-responses-adapter","schema_version":"1.0.0","projection_protocol":spec["projection_protocol"],"projection_only":True,"canonical_evidence":False,"transport":{"provider":"OpenAI","api_family":"Responses API","verified_pattern_date":"2026-08-22","model":"<choose a currently supported model>"},"instructions":prompt,"retrieval":{"recommended_tool":"file_search","source_projection":f"{d}/{output_filename('retrieval_bundle',spec)}","vector_store_id":"<vector_store_id>","rule":"Use retrieval to locate canonical record content; do not treat retrieval scores or this adapter as medical evidence."},"request_template":{"model":"<choose a currently supported model>","instructions":"<copy the instructions field from this adapter>","input":"<user request>","tools":[{"type":"file_search","vector_store_ids":["<vector_store_id>"]}]},"noncanonical_rule":"PROJECTION != CANONICAL_SOURCE"}; return json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
def input_manifest(bootstrap=None): bootstrap=bootstrap or load_json("ai/bootstrap.json"); return [{"path":r,"sha256":sha256_bytes((ROOT/r).read_bytes())} for r in canonical_inputs(bootstrap)]
def build_outputs():
 spec=projection_spec(); prompt=build_system_prompt(spec); names={"generic":output_filename("generic_system_prompt",spec),"openai":output_filename("openai_responses",spec),"retrieval":output_filename("retrieval_bundle",spec),"local":output_filename("local_compact",spec),"manifest":output_filename("manifest",spec)}; outputs={names["generic"]:prompt,names["openai"]:build_openai(prompt,spec),names["retrieval"]:build_retrieval_bundle(spec),names["local"]:build_local_compact(spec)}; d=spec["generated_output_dir"].rstrip("/"); manifest={"type":"cbt-model-adapter-projection-manifest","schema_version":"1.0.0","projection_protocol":spec["projection_protocol"],"projection_only":True,"canonical_evidence":False,"projection_spec":{"path":PROJECTION_SPEC_PATH,"sha256":sha256_bytes((ROOT/PROJECTION_SPEC_PATH).read_bytes())},"canonical_inputs":input_manifest(),"outputs":[{"path":f"{d}/{n}","sha256":sha256_text(outputs[n])} for n in sorted(outputs)],"rules":["PROJECTION != CANONICAL_SOURCE","adapter outputs must never appear in ai/bootstrap.json load_order or routed_records","adapter outputs must never be used as claim source_ids or snapshot_ids","deterministic byte identity does not create medical authority"]}; outputs[names["manifest"]]=json.dumps(manifest,indent=2,ensure_ascii=False,sort_keys=True)+"\n"; return outputs
def write_outputs(out): out.mkdir(parents=True,exist_ok=True); outputs=build_outputs(); [(out/n).write_text(outputs[n],encoding="utf-8") for n in output_names()]
def _is_generated_reference(value,prefix): return isinstance(value,str) and value.replace("\\","/").lstrip("./").startswith(prefix)
def verify_noncanonical_boundaries():
 errors=[]; spec=projection_spec(); b=load_json("ai/bootstrap.json"); claims=load_json("claims/index.json"); ps=load_json("sources/public-sources.json"); es=load_json("sources/evidence-sources.json"); snaps=load_json("sources/snapshots/manifest.json"); prefix=spec["generated_output_dir"].rstrip("/")+"/"; routed=list(b.get("load_order",[])); [routed.extend(x) for x in b.get("routed_records",{}).values()]
 if any(_is_generated_reference(x,prefix) for x in routed): errors.append("generated adapter projection appears in canonical bootstrap routing")
 for c in claims.get("claims",[]):
  if any(_is_generated_reference(x,prefix) for x in list(c.get("source_ids",[]))+list(c.get("snapshot_ids",[]))): errors.append(f"{c.get('id')} depends on generated adapter projection")
 for s in ps.get("sources",[])+es.get("sources",[]):
  if _is_generated_reference(s.get("url",""),prefix): errors.append(f"{s.get('id')} uses generated adapter projection as source")
 for snap in snaps.get("records",[]):
  if _is_generated_reference(snap.get("source_registry",""),prefix): errors.append(f"{snap.get('id')} depends on generated adapter projection")
  if _is_generated_reference(snap.get("observed_metadata",{}).get("url",""),prefix): errors.append(f"{snap.get('id')} uses generated adapter projection as observed metadata URL")
 if any(_is_generated_reference(x,prefix) for x in canonical_inputs(b)): errors.append("generated adapter projection included as canonical builder input")
 return errors
def verify_output_dir(out):
 errors=verify_noncanonical_boundaries(); expected=build_outputs()
 for n in output_names():
  p=out/n
  if not p.exists(): errors.append(f"missing generated projection {n}")
  elif p.read_text(encoding="utf-8")!=expected[n]: errors.append(f"stale or non-deterministic generated projection {n}")
 try:
  o=json.loads((out/output_filename("openai_responses")).read_text(encoding="utf-8"))
  if o.get("projection_only") is not True or o.get("canonical_evidence") is not False: errors.append("OpenAI adapter projection boundary weakened")
 except (FileNotFoundError,json.JSONDecodeError): errors.append("OpenAI adapter is missing or invalid JSON")
 return errors
def determinism_check():
 errors=[]
 with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
  pa,pb=Path(a),Path(b); write_outputs(pa); write_outputs(pb)
  for n in output_names():
   if (pa/n).read_bytes()!=(pb/n).read_bytes(): errors.append(f"non-deterministic output {n}")
 return errors
def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--output-dir"); parser.add_argument("--check",action="store_true"); parser.add_argument("--verify",action="store_true"); parser.add_argument("--determinism-check",action="store_true"); args=parser.parse_args()
 try: spec=projection_spec()
 except (KeyError,TypeError,ValueError,json.JSONDecodeError) as exc: print(f"adapter projection spec invalid: {exc}"); return 1
 out=Path(args.output_dir) if args.output_dir else default_output_dir(spec)
 if args.determinism_check:
  errors=determinism_check()
  if errors: [print(f"adapter determinism failed: {e}") for e in errors]; return 1
  print("CBT model adapter determinism: ok"); return 0
 if args.check:
  errors=verify_output_dir(out)
  if errors: [print(f"adapter projection check failed: {e}") for e in errors]; return 1
  print("CBT model adapter projections: ok"); return 0
 write_outputs(out)
 if args.verify:
  errors=verify_output_dir(out)
  if errors: [print(f"adapter projection verification failed: {e}") for e in errors]; return 1
  print("CBT model adapter projections built and verified")
 else: print(out)
 return 0
if __name__=="__main__": raise SystemExit(main())
