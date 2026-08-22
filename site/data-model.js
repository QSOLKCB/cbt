(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports) module.exports=api;
  else root.CBT95_DATA_MODEL=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";

  function isoToday(date){
    const d=date||new Date();
    const y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,"0"),day=String(d.getDate()).padStart(2,"0");
    return `${y}-${m}-${day}`;
  }

  function snapshotFreshness(snapshot,today){
    const now=today||isoToday();
    if(!snapshot) return "unknown";
    if(snapshot.verified_on&&now<snapshot.verified_on) return "not_yet_verified";
    if(snapshot.verification_expires_on&&now>snapshot.verification_expires_on) return "review_due";
    return "current_verification";
  }

  function claimFreshness(claim,today){
    const now=today||isoToday();
    if(!claim) return "unknown";
    if(claim.last_reviewed&&now<claim.last_reviewed) return "not_yet_reviewed";
    if(claim.review_due&&now>claim.review_due) return "claim_review_due";
    return "claim_review_current";
  }

  function sourceRecords(ctx){
    return [...(ctx.public_sources?.sources||[]),...(ctx.evidence_sources?.sources||[])];
  }

  function sourceById(ctx,id){ return sourceRecords(ctx).find(row=>row.id===id)||null; }
  function claimById(ctx,id){ return (ctx.claim_ledger?.claims||[]).find(row=>row.id===id)||null; }
  function snapshotById(ctx,id){ return (ctx.source_snapshots?.records||[]).find(row=>row.id===id)||null; }

  function conflictsForClaim(ctx,claimId){
    return (ctx.claim_conflicts?.bundles||[]).filter(bundle=>(bundle.claim_ids||[]).includes(claimId));
  }

  function sourceView(ctx,sourceId,today){
    const source=sourceById(ctx,sourceId);
    if(!source) return null;
    const snapshots=(ctx.source_snapshots?.records||[])
      .filter(row=>row.source_id===sourceId)
      .slice()
      .sort((a,b)=>a.verified_on===b.verified_on?(a.id<b.id?-1:a.id>b.id?1:0):(a.verified_on>b.verified_on?-1:1));
    const latestSnapshot=snapshots[0]||null;
    const relatedClaims=(ctx.claim_ledger?.claims||[])
      .filter(claim=>(claim.source_ids||[]).includes(sourceId))
      .map(claim=>({
        claim,
        freshness:claimFreshness(claim,today),
        boundSnapshots:(claim.snapshot_ids||[]).map(id=>snapshotById(ctx,id)).filter(Boolean),
        conflicts:conflictsForClaim(ctx,claim.id),
      }));
    return {
      source,
      snapshots,
      latestSnapshot,
      latestSnapshotFreshness:snapshotFreshness(latestSnapshot,today),
      relatedClaims,
    };
  }

  return {isoToday,snapshotFreshness,claimFreshness,sourceRecords,sourceById,claimById,snapshotById,conflictsForClaim,sourceView};
});
