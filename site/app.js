(() => {
const ctx = window.CBT95_CONTEXT;
const app = document.getElementById("app");
const status = document.getElementById("status");
const exerciseData = ctx.index.exercises;
const sourceMap = Object.fromEntries(ctx.public_sources.sources.map(s => [s.id,s]));
const esc = s => String(s ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const setStatus = s => status.textContent=s;

function home(){
 app.innerHTML=`<section class="card hero"><h1>CBT 95</h1><p><b>Learn CBT by watching the mechanism.</b> This desk combines a small evidence-bounded reference with exercises you can try privately in this browser session.</p><p class="warning"><b>Boundary:</b> CBT can be an evidence-based treatment for some conditions. It is not a cure, diagnosis, universal remedy, or guarantee. These exercises are educational self-help, not clinician-delivered therapy or emergency care.</p></section>
 <section class="card"><h2>The working model</h2><p><b>Situation → Thought/interpretation → Emotion &amp; body → Behaviour → Consequence</b></p><p>CBT asks whether one part of that loop can be observed, tested, reframed, or changed. It does not require pretending difficult facts or emotions are unreal.</p></section>
 <section class="card"><h2>Try the desk</h2><p>Start with <b>The 7-Step Thought Record</b> to see cognitive restructuring, or open <b>CBT for Cognitive Work</b> for the coding/study addendum.</p></section>`;
}
function learn(){
 const p=ctx.cbt_context;
 app.innerHTML=`<section class="card hero"><h1>What is CBT?</h1><p>${esc(p.definition)}</p></section>
 <section class="card"><h2>What CBT looks for</h2><p>${p.teaching_model.loop.map(x=>`<span class="tag">${esc(x)}</span>`).join(" → ")}</p><p>${esc(p.teaching_model.principle)}</p></section>
 <section class="card"><h2>Important: not forced positivity</h2><ul>${p.exercise_rules.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></section>`;
}
function exercises(){
 app.innerHTML=`<section class="card hero"><h1>Exercise Lab</h1><p>Pick an exercise. Each one shows <b>what CBT is doing here</b> and what the result does <b>not</b> prove.</p></section><div class="exercise-list">${exerciseData.map(ex=>`<article class="card exercise-card" data-ex="${esc(ex.id)}"><span class="tag">${esc(ex.level)}</span><span class="tag">${esc(ex.time)}</span><h2>${esc(ex.title)}</h2><p>${esc(ex.purpose)}</p></article>`).join("")}</div>`;
 document.querySelectorAll("[data-ex]").forEach(el=>el.addEventListener("click",()=>exercise(el.dataset.ex)));
}
function exercise(id){
 const ex=exerciseData.find(x=>x.id===id); if(!ex)return exercises();
 const key=`cbt95:${id}`;
 const saved=JSON.parse(sessionStorage.getItem(key)||"[]");
 app.innerHTML=`<section class="card hero"><button id="backEx">← Exercises</button><h1>${esc(ex.title)}</h1><p>${esc(ex.purpose)}</p><span class="tag">${esc(ex.time)}</span></section>
 <form class="card" id="exerciseForm">${ex.prompts.map((p,i)=>`<label for="p${i}">${i+1}. ${esc(p)}</label><textarea id="p${i}" data-i="${i}">${esc(saved[i]||"")}</textarea>`).join("")}<div class="actions"><button type="button" id="saveExercise">Save this session</button><button type="button" id="clearExercise">Clear</button></div></form>
 <section class="card mechanism"><h2>What CBT is doing here</h2><p>${esc(ex.mechanism)}</p></section>
 <section class="card limit"><h2>What this does not establish</h2><p>${esc(ex.not_established)}</p></section>
 <section class="card"><h2>Sources</h2>${ex.source_ids.map(sourceLine).join("")}</section>`;
 document.getElementById("backEx").onclick=exercises;
 document.getElementById("saveExercise").onclick=()=>{const vals=[...document.querySelectorAll("textarea[data-i]")].map(x=>x.value);sessionStorage.setItem(key,JSON.stringify(vals));setStatus("Saved in this browser session");};
 document.getElementById("clearExercise").onclick=()=>{sessionStorage.removeItem(key);document.querySelectorAll("textarea[data-i]").forEach(x=>x.value="");setStatus("Exercise cleared");};
 app.focus();
}
function work(){
 const w=ctx.cognitive_work_addendum;
 const ex=exerciseData.find(x=>x.id==="affect-to-action");
 app.innerHTML=`<section class="card hero"><h1>CBT for Cognitive Work</h1><p>For coding, study, debugging, research and writing.</p><p class="warning"><b>Better brain language:</b> ${esc(w.preferred_framing)}. We avoid saying emotion is literally “moved into the prefrontal cortex”.</p></section>
 <section class="card"><h2>Why this might help</h2><ul>${w.mechanism_summary.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></section>
 <section class="card"><h2>Five moves</h2><ol>${w.workflow.map(x=>`<li><b>${esc(x.step)}</b>: ${esc(x.prompt)}</li>`).join("")}</ol><button id="tryWork">Try the exercise</button></section>
 <section class="card"><h2>Examples</h2>${Object.entries(w.examples).map(([k,v])=>`<h3>${esc(k)}</h3><p>${esc(v)}</p>`).join("")}</section>
 <section class="card limit"><h2>Guardrails</h2><ul>${w.guardrails.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></section>
 <section class="card"><h2>Mechanism sources</h2>${ex.source_ids.map(sourceLine).join("")}</section>`;
 document.getElementById("tryWork").onclick=()=>exercise("affect-to-action");
}
function sourceLine(id){const s=sourceMap[id];return s?`<p class="source"><b>${esc(s.title)}</b><br><span class="tag">${esc(s.jurisdiction)}</span> <a href="${esc(s.url)}" target="_blank" rel="noreferrer">${esc(s.url)}</a></p>`:`<p>${esc(id)}</p>`}
function sources(){
 app.innerHTML=`<section class="card hero"><h1>Evidence &amp; Ethics</h1><p>The substrate uses Australian medical/safety standards, NHS/NICE guidance, and a small peer-reviewed neuroscience addendum. Sources retain jurisdiction and scope.</p></section>${ctx.public_sources.sources.map(s=>`<section class="card">${sourceLine(s.id)}<p>${s.supports.map(x=>`<span class="tag">${esc(x)}</span>`).join(" ")}</p></section>`).join("")}`;
}
function about(){
 app.innerHTML=`<section class="card hero"><h1>About CBT 95</h1><p>This is an educational reference and exercise lab, not a healthcare service.</p></section><section class="card"><h2>Privacy</h2><p>Exercise answers are not sent anywhere by this static site. “Save this session” uses browser <code>sessionStorage</code>, which is cleared when the session ends or when you press the clear button.</p></section><section class="card"><h2>When the exercise should stop</h2><p>Urgent safety or medical needs take priority over routine CBT exercises. A runtime AI should resolve current local emergency/crisis resources rather than rely on stale hardcoded numbers.</p></section>`;
}
const routes={home,learn,exercises,work,sources,about};
document.querySelectorAll("[data-route]").forEach(b=>b.addEventListener("click",()=>{routes[b.dataset.route]();setStatus(b.textContent.trim())}));
document.getElementById("clearData").onclick=()=>{Object.keys(sessionStorage).filter(k=>k.startsWith("cbt95:")).forEach(k=>sessionStorage.removeItem(k));setStatus("All exercise session data cleared");};
home();
})();