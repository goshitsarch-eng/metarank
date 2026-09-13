"""Fetch all sources, rank within each, and aggregate placements across
sources into per-category tabs: Overall, Chat, Coding, Agents."""
import json, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from metarank import normalize as N
from metarank.fetchers import lmarena, epoch, livebench, aider, artificialanalysis

FETCHERS = [lmarena, epoch, livebench, aider, artificialanalysis]
MAX_MODELS = 60

# (tab_id, label, blurb, min_sources, source categories counted in this tab)
TABS = [
    ("overall", "Overall", "Consensus across every source", 2,
     ("chat", "coding", "agents", "general")),
    ("chat", "Chat", "Everyday chat / general use", 1, ("chat",)),
    ("coding", "Coding", "Real-world coding ability", 1, ("coding",)),
    ("agents", "Agents", "Hard benchmarks & agentic capability", 1, ("agents",)),
]

def fetch_all():
    sources, per_source = [], {}
    for f in FETCHERS:
        try:
            data = f.fetch()
        except Exception as e:
            # AA is key-gated; others may fail too. Skip cleanly.
            print(f"SKIP {f.SOURCE['id']}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        src = dict(f.SOURCE)
        src["data_date"] = data.get("data_date")
        src["n_models"] = len(data["entries"])
        sources.append(src)
        # rank within source, collapse variants to canonical key (best rank wins)
        best = {}
        for i, e in enumerate(data["entries"], start=1):
            key = N.canonical(e["raw_name"])
            if key not in best or i < best[key]["rank"]:
                best[key] = {"rank": i, "score": e["score"],
                             "raw": e["raw_name"], "org": e.get("org")}
        per_source[src["id"]] = best
        print(f"OK {src['id']}: {len(data['entries'])} entries -> {len(best)} models",
              file=sys.stderr)
    return sources, per_source

def build_rows(per_source, tab_sources, min_sources):
    models = {}
    for sid in tab_sources:
        for key, r in per_source.get(sid, {}).items():
            m = models.setdefault(key, {"key": key, "raw_names": {},
                                        "orgs": {}, "ranks": {}})
            m["raw_names"][r["raw"]] = m["raw_names"].get(r["raw"], 0) + 1
            if r.get("org"):
                m["orgs"][r["org"]] = m["orgs"].get(r["org"], 0) + 1
            m["ranks"][sid] = r["rank"]

    rows = []
    for key, m in models.items():
        if len(m["ranks"]) < min_sources:
            continue
        ranks = m["ranks"]
        avg = sum(ranks.values()) / len(ranks)
        placements = {str(p): sum(1 for r in ranks.values() if r == p)
                      for p in (1, 2, 3, 4)}
        # prettiest raw name: prefer one with spaces/caps (human name)
        raw = max(m["raw_names"], key=lambda n: ((" " in n), len(n)))
        org = max(m["orgs"], key=m["orgs"].get) if m["orgs"] else None
        rows.append({
            "key": key,
            "name": N.display_name(key, raw),
            "org": N.org_for(key, org),
            "avg_rank": round(avg, 2),
            "n_sources": len(ranks),
            "placements": placements,
            "ranks": {sid: ranks.get(sid) for sid in tab_sources},
        })
    rows.sort(key=lambda r: (r["avg_rank"], -int(r["placements"]["1"]),
                             -r["n_sources"]))
    return rows

def run():
    sources, per_source = fetch_all()
    tabs = {}
    for tab_id, label, blurb, min_sources, cats in TABS:
        tab_sources = [s["id"] for s in sources if s.get("category") in cats]
        models = build_rows(per_source, tab_sources, min_sources)
        tabs[tab_id] = {
            "label": label,
            "blurb": blurb,
            "min_sources": min_sources,
            "source_ids": tab_sources,
            "models": models[:MAX_MODELS],
        }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": sources,
        "tabs": tabs,
        # legacy flat list = overall tab
        "models": tabs["overall"]["models"],
    }

if __name__ == "__main__":
    out = run()
    with open(sys.argv[1], "w") as fh:
        json.dump(out, fh, indent=1)
    counts = {t: len(v["models"]) for t, v in out["tabs"].items()}
    print(f"wrote {sys.argv[1]}: {len(out['sources'])} sources, "
          f"tab counts {counts}", file=sys.stderr)
