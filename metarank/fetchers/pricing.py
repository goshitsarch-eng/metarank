"""Model pricing from OpenRouter's public no-key endpoint.

https://openrouter.ai/api/v1/models -> id, name, pricing.prompt,
pricing.completion ($/token as strings). Converted to $ per 1M tokens and
keyed by the same canonical normalizer used for the rankings, so prices
join cleanly onto ranked models. Not a rank source: aggregate.py treats
this separately as enrichment.
"""
import requests

from metarank import normalize as N

SOURCE = {"id": "pricing", "name": "OpenRouter pricing",
          "url": "https://openrouter.ai/models",
          "what": "Live per-token pricing, $ per 1M tokens (input/output)",
          "category": "pricing"}
URL = "https://openrouter.ai/api/v1/models"


def _candidate_keys(model: dict):
    keys = []
    mid = (model.get("id") or "")
    if "/" in mid:
        mid = mid.split("/", 1)[1]
    # strip provider routing suffixes like :online, :nitro
    mid = mid.split(":")[0]
    keys.append(N.canonical(mid))
    name = (model.get("name") or "").split(":")[-1]
    keys.append(N.canonical(name))
    # de-dup, drop empties
    seen, out = set(), []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def fetch():
    r = requests.get(URL, headers={"User-Agent": "metarank/1.0"}, timeout=60)
    r.raise_for_status()
    pricing = {}
    for m in r.json().get("data", []):
        p = m.get("pricing") or {}
        try:
            inp = float(p["prompt"]) * 1_000_000
            outp = float(p["completion"]) * 1_000_000
        except (KeyError, TypeError, ValueError):
            continue
        entry = {"input_per_1m_usd": round(inp, 4),
                 "output_per_1m_usd": round(outp, 4)}
        for key in _candidate_keys(m):
            # same model via multiple routes: keep the cheapest listing
            cur = pricing.get(key)
            if cur is None or (inp + outp) < (
                    cur["input_per_1m_usd"] + cur["output_per_1m_usd"]):
                pricing[key] = entry
    return {"pricing": pricing, "n_models": len(pricing)}
