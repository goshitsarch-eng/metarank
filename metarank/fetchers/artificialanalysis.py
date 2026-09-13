"""Artificial Analysis Intelligence Index. Requires a free API key (100 req/day)."""
import os, requests

SOURCE = {"id": "aa", "name": "Artificial Analysis", "url": "https://artificialanalysis.ai/",
          "what": "Independent Intelligence Index over ~10 evals",
          "category": "chat"}
URL = "https://artificialanalysis.ai/api/v2/data/llms/models"

def fetch():
    key = os.environ.get("ARTIFICIALANALYSIS_API_KEY")
    if not key:
        raise RuntimeError("ARTIFICIALANALYSIS_API_KEY not set; skipping")
    r = requests.get(URL, headers={"x-api-key": key}, timeout=60)
    r.raise_for_status()
    entries = []
    for m in r.json()["data"]:
        ev = m.get("evaluations") or {}
        idx = ev.get("artificial_analysis_intelligence_index")
        if idx is not None:
            entries.append({"raw_name": m.get("name") or m["slug"],
                            "org": (m.get("model_creator") or {}).get("name"),
                            "score": float(idx)})
    entries.sort(key=lambda e: -e["score"])
    return {"entries": entries, "data_date": None}
