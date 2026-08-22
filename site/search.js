(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports) module.exports=api;
  else root.CBT95_SEARCH=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const TYPE_ORDER={exercise:0,glossary:1,source:2,claim:3};

  function normalize(value){
    return String(value??"").normalize("NFKC").toLowerCase().replace(/[^0-9a-z]+/g," ").trim().replace(/\s+/g," ");
  }

  function queryTokens(query){
    const text=normalize(query);
    return text?text.split(" "):[];
  }

  function tokenScore(queryToken,indexToken){
    if(indexToken===queryToken) return 100;
    if(indexToken.startsWith(queryToken)) return 20;
    if(indexToken.includes(queryToken)) return 5;
    return 0;
  }

  function scoreEntry(entry,query){
    const qs=queryTokens(query);
    if(!qs.length) return 0;
    const indexed=Array.isArray(entry.tokens)?entry.tokens:[];
    let total=0;
    for(const q of qs){
      let best=0;
      for(const token of indexed) best=Math.max(best,tokenScore(q,token));
      total+=best;
    }
    return total;
  }

  function compareIds(a,b){ return a<b?-1:a>b?1:0; }

  function rank(entries,query){
    return (entries||[])
      .map(entry=>({entry,score:scoreEntry(entry,query)}))
      .filter(row=>row.score>0)
      .sort((a,b)=>{
        if(a.score!==b.score) return b.score-a.score;
        const at=TYPE_ORDER[a.entry.kind]??99,bt=TYPE_ORDER[b.entry.kind]??99;
        if(at!==bt) return at-bt;
        return compareIds(String(a.entry.id),String(b.entry.id));
      });
  }

  return {TYPE_ORDER,normalize,queryTokens,tokenScore,scoreEntry,rank};
});
