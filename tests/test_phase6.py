import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class Phase6Tests(unittest.TestCase):
    def test_search_projection_is_deterministic_and_claims_are_not_descoped(self):
        builder = ROOT / "tools" / "build_site_data.py"
        subprocess.run([sys.executable, str(builder)], check=True)
        first = (ROOT / "site" / "data" / "search-index.json").read_bytes()
        subprocess.run([sys.executable, str(builder)], check=True)
        second = (ROOT / "site" / "data" / "search-index.json").read_bytes()
        self.assertEqual(first, second)
        data = json.loads(first)
        self.assertTrue(data["projection_only"])
        self.assertFalse(data["canonical_evidence"])
        for entry in [e for e in data["entries"] if e["kind"] == "claim"]:
            self.assertEqual(set(entry), {"id", "kind", "title", "tokens"})
            self.assertNotIn("claim_text", entry)
            self.assertIn(entry["id"], {c["id"] for c in load("claims/index.json")["claims"]})

    @unittest.skipUnless(NODE, "Node.js is required for Phase 6 JS determinism tests")
    def test_lexical_ranking_is_reproducible_with_stable_tiebreaks(self):
        script = r'''
const S=require('./site/search.js');
const rows=[
 {id:'source.b',kind:'source',tokens:['cbt','guide']},
 {id:'exercise.z',kind:'exercise',tokens:['cbt','guide']},
 {id:'exercise.a',kind:'exercise',tokens:['cbt','guide']},
 {id:'claim.x',kind:'claim',tokens:['cbtx']}
];
const a=S.rank(rows,'cbt').map(x=>x.entry.id);
const b=S.rank(rows,'cbt').map(x=>x.entry.id);
console.log(JSON.stringify({a,b,exact:S.tokenScore('cbt','cbt'),prefix:S.tokenScore('cb','cbt'),substring:S.tokenScore('bt','cbt')}));
'''
        proc = subprocess.run([NODE, "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
        result = json.loads(proc.stdout)
        self.assertEqual(result["a"], result["b"])
        self.assertEqual(result["a"][:3], ["exercise.a", "exercise.z", "source.b"])
        self.assertGreater(result["exact"], result["prefix"])
        self.assertGreater(result["prefix"], result["substring"])

    def test_exercise_loop_mappings_are_canonical(self):
        profile = load("profiles/cbt-context.json")
        loop = profile["teaching_model"]["loop"]
        self.assertEqual(set(profile["teaching_model"]["node_definitions"]), set(loop))
        for ex in load("exercises/index.json")["exercises"]:
            self.assertTrue(ex["teaching_loop_nodes"])
            self.assertTrue(set(ex["teaching_loop_nodes"]).issubset(set(loop)))

    @unittest.skipUnless(NODE, "Node.js is required for Phase 6 provenance tests")
    def test_source_view_preserves_conflict_and_exact_claim_bound_snapshot(self):
        script = r'''
const fs=require('fs'),M=require('./site/data-model.js');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const ctx={
 public_sources:load('sources/public-sources.json'),
 evidence_sources:load('sources/evidence-sources.json'),
 source_snapshots:load('sources/snapshots/manifest.json'),
 claim_ledger:load('claims/index.json'),
 claim_conflicts:load('claims/conflicts.json')
};
const view=M.sourceView(ctx,'pubmed.papola.2024.gad-network-meta','2026-08-23');
const row=view.relatedClaims.find(x=>x.claim.id==='claim.gad.meta.papola2024.cbt-vs-tau');
console.log(JSON.stringify({
 latest:view.latestSnapshot.id,
 bound:row.boundSnapshots.map(x=>x.id),
 conflicts:row.conflicts.map(x=>x.id),
 claimFresh:row.freshness,
 future:M.snapshotFreshness(view.latestSnapshot,'2028-01-01'),
 historical:M.snapshotFreshness(view.latestSnapshot,'2020-01-01')
}));
'''
        proc = subprocess.run([NODE, "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
        result = json.loads(proc.stdout)
        self.assertEqual(result["bound"], ["snapshot.pubmed.papola.2024.gad-network-meta.2026-08-22"])
        self.assertIn("conflict.gad.aggregate-vs-delivery-format", result["conflicts"])
        self.assertEqual(result["future"], "review_due")
        self.assertEqual(result["historical"], "not_yet_verified")

    def test_source_explorer_renders_claim_scope_conflicts_bound_snapshots_and_registry_filter(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        for marker in (
            "Claim-bound snapshot IDs",
            "Population",
            "Intervention",
            "Comparator",
            "Outcome",
            "Evidence class",
            "Jurisdiction",
            "What this does not establish",
            "Model.conflictsForClaim",
            "Exact snapshots bound to this claim",
            "not automatically the snapshot a claim is bound to",
            'id="sourceRegistryFilter"',
            "All registries",
            "sourceRegistry(s.id)===reg.value",
            "reg.onchange=render",
        ):
            self.assertIn(marker, app)

    def test_favourites_are_session_only_and_global_clear_removes_them_and_refreshes_open_exercise(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn('FAV_KEY="cbt95:favourites"', app)
        self.assertIn("sessionStorage.getItem(FAV_KEY)", app)
        self.assertIn("sessionStorage.setItem(FAV_KEY", app)
        self.assertNotIn("localStorage", app)
        self.assertNotIn("indexedDB", app)
        self.assertIn("Object.keys(sessionStorage).filter(k=>k.startsWith(\"cbt95:\"))", app)
        self.assertIn("favourites=new Set()", app)
        self.assertIn("if(currentExerciseId)exercise(currentExerciseId,[]);else exercises()", app)

    def test_service_worker_is_network_first_for_reference_and_evicts_old_versions(self):
        sw = (ROOT / "site" / "service-worker.js").read_text(encoding="utf-8")
        start = sw.index("async function referenceNetworkFirst")
        end = sw.index("async function shellCacheFirst")
        section = sw[start:end]
        self.assertGreater(start, -1)
        self.assertLess(section.index('fetch(request,{cache:"no-store"})'), section.index("cache.match(request)"))
        self.assertIn('key.startsWith("cbt95-")', sw)
        self.assertIn("caches.delete(key)", sw)
        self.assertIn("CBT95_CACHE_FALLBACK", sw)
        for forbidden in ("sessionStorage", "localStorage", "indexedDB"):
            self.assertNotIn(forbidden, sw)

    def test_keyboard_route_focus_and_diagram_accessibility_contract(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("focus({preventScroll:true})", app)
        self.assertIn("routeAnnouncer", index)
        self.assertIn('e.key==="/"', app)
        self.assertIn('e.key==="ArrowRight"', app)
        self.assertIn('aria-label="Interactive CBT teaching loop"', app)
        self.assertIn('aria-pressed="false"', app)
        self.assertIn("Full textual version of the CBT loop", app)
        self.assertIn("Text sequence:", app)
        self.assertIn("data-ex-link", app)

    def test_pwa_manifest_and_offline_warning_are_present(self):
        manifest = load("site/manifest.webmanifest")
        self.assertEqual(manifest["display"], "standalone")
        self.assertTrue(manifest["icons"])
        index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn('rel="manifest"', index)
        self.assertIn("OFFLINE_CACHE != CURRENT_GUIDANCE", app)
        self.assertIn("cached medical/reference content may be stale", app.lower())

    def test_readme4ai_builds_site_projections_before_checking_them(self):
        text = (ROOT / "README4AI.md").read_text(encoding="utf-8")
        build = text.index("python3 tools/build_site_data.py\n")
        check = text.index("python3 tools/build_site_data.py --check")
        self.assertLess(build, check)


if __name__ == "__main__":
    unittest.main()
