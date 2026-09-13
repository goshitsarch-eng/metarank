"""Terminal-Bench 2.1 leaderboard: agentic coding in real containers.

tbench.ai is a Next.js app; the leaderboard rows are embedded in its
React-Flight (RSC) payload as a plain JSON "rows" array. We fetch with the
same RSC headers a browser sends and parse the first well-formed rows
array belonging to the 2.1 board. Entries are per agent+model run; we keep
the best accuracy per displayed model.
"""
import json, re, requests

SOURCE = {"id": "terminalbench", "name": "Terminal-Bench",
          "url": "https://www.tbench.ai/leaderboard/terminal-bench/2.1",
          "what": "89 hard terminal tasks run by an agent, accuracy %",
          "category": "coding"}
PATH = "/leaderboard/terminal-bench/2.1"
BASE = "https://www.tbench.ai"
HEADERS = {"RSC": "1", "Next-Url": PATH,
           "User-Agent": "metarank/1.0"}


def _rows_arrays(text):
    """Yield (context, rows) for every well-formed "rows":[...] in payload."""
    dec = json.JSONDecoder()
    for m in re.finditer(r'"rows":\[', text):
        try:
            arr, _ = dec.raw_decode(text, m.end() - 1)
        except Exception:
            continue
        if isinstance(arr, list) and arr:
            yield text[max(0, m.start() - 1500):m.start()], arr


def fetch():
    r = requests.get(BASE + PATH, headers=HEADERS, timeout=90)
    r.raise_for_status()
    cands = list(_rows_arrays(r.text))
    if not cands:
        raise RuntimeError("no leaderboard rows found in tbench payload")
    # prefer the 2.1 board's rows; fall back to the largest array
    rows = None
    for ctx, arr in cands:
        if "2.1" in ctx or "terminal-bench-2-1" in ctx:
            rows = arr
            break
    if rows is None:
        rows = max(cands, key=lambda c: len(c[1]))[1]

    best = {}
    for row in rows:
        meta = row.get("metadata", {}) or {}
        metrics = row.get("metrics", {}) or {}
        md = meta.get("model_display", {}) or {}
        name = (md.get("label") or "").strip()
        if not name:
            # fall back to modelNames list
            names = meta.get("modelNames") or row.get("modelNames") or []
            name = (names[0] if names else "").strip()
        if not name:
            continue
        try:
            acc = float(metrics["accuracy"])
        except (KeyError, TypeError, ValueError):
            continue
        date = meta.get("date") or row.get("date") or ""
        mo = meta.get("model_org", {}) or {}
        org = mo.get("label")
        cur = best.get(name)
        if cur is None or acc > cur["score"] or (
                acc == cur["score"] and date > cur.get("date", "")):
            best[name] = {"raw_name": name, "org": org, "score": acc,
                          "date": date}
    entries = sorted(best.values(), key=lambda e: -e["score"])
    dates = [e["date"] for e in entries if e.get("date")]
    return {"entries": entries,
            "data_date": max(dates) if dates else None}
