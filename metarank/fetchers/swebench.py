"""SWE-bench Verified leaderboard: real GitHub issues, % resolved.

Raw data: SWE-bench/swe-bench.github.io data/leaderboards.json (the same
file that renders swebench.com). Entries are per agent-run; we keep the
best resolved % per displayed model.
"""
import requests

SOURCE = {"id": "swebench", "name": "SWE-bench Verified",
          "url": "https://www.swebench.com/",
          "what": "Real GitHub issue fixes, % resolved (Verified split)",
          "category": "coding"}
URL = ("https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/"
       "master/data/leaderboards.json")


def fetch():
    d = requests.get(URL, timeout=120).json()
    boards = d.get("leaderboards", [])
    lb = next((b for b in boards if b.get("name") == "Verified"), None)
    if lb is None:
        raise RuntimeError("Verified leaderboard not found in payload")
    best = {}
    for r in lb.get("results", []):
        name = (r.get("model_display") or "").strip()
        if not name:
            continue
        try:
            score = float(r["resolved"])
        except (KeyError, TypeError, ValueError):
            continue
        date = r.get("date") or ""
        cur = best.get(name)
        if cur is None or score > cur["score"] or (
                score == cur["score"] and date > cur.get("date", "")):
            best[name] = {"raw_name": name, "org": r.get("model_org"),
                          "score": score, "date": date}
    entries = sorted(best.values(), key=lambda e: -e["score"])
    dates = [e["date"] for e in entries if e.get("date")]
    return {"entries": entries,
            "data_date": max(dates) if dates else None}
