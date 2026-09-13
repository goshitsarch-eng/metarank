"""Fetch all sources, rank within each, and aggregate placements across
sources into tabs: Overall, Chat, Coding, Agents, Pricing (OpenRouter
prices), Open Weights and Self-Hosted (curated open-weights list).
Every row is also tagged with its lab's region (curated origins map)."""
import json, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from metarank import normalize as N
from metarank.fetchers import lmarena, epoch, livebench, aider, artificialanalysis
from metarank.fetchers import pricing as pricing_fetcher

FETCHERS = [lmarena, epoch, livebench, aider, artificialanalysis]
MAX_MODELS = 60

OPEN_MODELS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "data", "open_models.json")
ORIGINS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "model_origins.json")

def load_open_models():
    """Curated open-weights map: canonical key -> {params_b, self_hostable}."""
    try:
        with open(OPEN_MODELS_PATH) as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"WARN open_models: {e}", file=sys.stderr)
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}

def load_origins():
    """Curated region map: (prefixes, exact models). Longest prefix wins."""
    try:
        with open(ORIGINS_PATH) as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"WARN model_origins: {e}", file=sys.stderr)
        return {}, {}
    prefixes = {k: v for k, v in data.get("prefixes", {}).items()}
    models = {k: v for k, v in data.get("models", {}).items()
              if not k.startswith("_")}
    return prefixes, models

def region_for(key, prefixes, models):
    if key in models:
        return models[key]
    for pre in sorted(prefixes, key=len, reverse=True):
        if key.startswith(pre):
            return prefixes[pre]
    return "Other"

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

def build_rows(per_source, tab_sources, min_sources, open_map, origins):
    models = {}
    for sid in tab_sources:
        for key, r in per_source.get(sid, {}).items():
            m = models.setdefault(key, {"key": key, "raw_names": {},
                                        "orgs": {}, "ranks": {}})
            m["raw_names"][r["raw"]] = m["raw_names"].get(r["raw"], 0) + 1
            if r.get("org"):
                m["orgs"][r["org"]] = m["orgs"].get(r["org"], 0) + 1
            m["ranks"][sid] = r["rank"]

    prefixes, origin_models = origins
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
        om = open_map.get(key, {})
        rows.append({
            "key": key,
            "name": N.display_name(key, raw),
            "org": N.org_for(key, org),
            "avg_rank": round(avg, 2),
            "n_sources": len(ranks),
            "placements": placements,
            "ranks": {sid: ranks.get(sid) for sid in tab_sources},
            "open_weights": key in open_map,
            "self_hostable": bool(om.get("self_hostable")),
            "params_b": om.get("params_b"),
            "region": region_for(key, prefixes, origin_models),
        })
    rows.sort(key=lambda r: (r["avg_rank"], -int(r["placements"]["1"]),
                             -r["n_sources"]))
    return rows

def fetch_pricing():
    try:
        data = pricing_fetcher.fetch()
    except Exception as e:
        print(f"SKIP pricing: {type(e).__name__}: {e}", file=sys.stderr)
        return {}
    print(f"OK pricing: {data['n_models']} models priced", file=sys.stderr)
    return data["pricing"]

def build_pricing_rows(overall_models, pricing_map, source_ids):
    rows = []
    for m in overall_models:
        p = pricing_map.get(m["key"])
        rows.append({
            "key": m["key"], "name": m["name"], "org": m["org"],
            "avg_rank": m["avg_rank"], "n_sources": m["n_sources"],
            "placements": m["placements"], "ranks": m["ranks"],
            "input_1m": p["input_per_1m_usd"] if p else None,
            "output_1m": p["output_per_1m_usd"] if p else None,
        })
    return rows

def run():
    sources, per_source = fetch_all()
    pricing_map = fetch_pricing()
    open_map = load_open_models()
    print(f"OK open_models: {len(open_map)} curated entries", file=sys.stderr)
    origins = load_origins()
    print(f"OK model_origins: {len(origins[0])} prefixes, "
          f"{len(origins[1])} overrides", file=sys.stderr)
    tabs = {}
    for tab_id, label, blurb, min_sources, cats in TABS:
        tab_sources = [s["id"] for s in sources if s.get("category") in cats]
        models = build_rows(per_source, tab_sources, min_sources, open_map,
                            origins)
        tabs[tab_id] = {
            "label": label,
            "blurb": blurb,
            "min_sources": min_sources,
            "source_ids": tab_sources,
            "models": models[:MAX_MODELS],
        }
    overall_sources = [s["id"] for s in sources
                       if s.get("category") in ("chat", "coding", "agents", "general")]
    tabs["pricing"] = {
        "label": "Pricing",
        "blurb": "What the top models cost to run — $ per 1M tokens via OpenRouter",
        "min_sources": 2,
        "source_ids": overall_sources,
        "models": build_pricing_rows(tabs["overall"]["models"], pricing_map,
                                     overall_sources)[:MAX_MODELS],
    }
    overall_models = tabs["overall"]["models"]
    tabs["open"] = {
        "label": "Open Weights",
        "blurb": "Top models with publicly released weights",
        "min_sources": 2,
        "source_ids": overall_sources,
        "models": [m for m in overall_models if m["open_weights"]][:MAX_MODELS],
    }
    tabs["selfhosted"] = {
        "label": "Self-Hosted",
        "blurb": "Open models you can actually run yourself via Ollama or vLLM",
        "min_sources": 2,
        "source_ids": overall_sources,
        "models": [m for m in overall_models if m["self_hostable"]][:MAX_MODELS],
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": sources,
        "pricing": pricing_map,
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
