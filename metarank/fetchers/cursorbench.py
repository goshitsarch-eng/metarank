"""CursorBench leaderboard: IDE-integrated coding benchmark by Cursor.

cursor.com/cursorbench is a Next.js page whose leaderboard is a
server-rendered HTML table (rank, model, score %, cost/task, tokens/task,
steps/task) -- no JS needed. Each effort variant (Max/Extra High/High/
Medium/Low) stays its own row per the no-rollup policy; vendor prefixes
(Fable/Opus/Sonnet) are expanded by normalize.py.
"""
import re, requests

SOURCE = {"id": "cursorbench", "name": "CursorBench",
          "url": "https://cursor.com/cursorbench",
          "what": "Ambiguous multi-file coding tasks from real Cursor sessions, score %",
          "category": "coding"}
URL = "https://cursor.com/cursorbench"
HEADERS = {"User-Agent": "metarank/1.0"}


def fetch():
    r = requests.get(URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    tables = re.findall(
        r'<table class="w-full table-fixed border-collapse">(.*?)</table>',
        r.text, re.S)
    if not tables:
        raise RuntimeError("no leaderboard table found on cursor.com/cursorbench")
    # the page renders the table twice (desktop/mobile); they are identical
    rows = []
    for m in re.findall(r"<tr[^>]*>(.*?)</tr>", tables[0], re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m, re.S)
        rows.append([re.sub(r"<[^>]+>", "", c).strip() for c in cells])

    entries = []
    for cells in rows:
        if len(cells) < 3:
            continue
        name = cells[1]
        score_txt = cells[2].rstrip("%").strip()
        if not name or name == "Model":
            continue
        try:
            score = float(score_txt)
        except ValueError:
            continue
        entries.append({"raw_name": name, "score": score})
    if not entries:
        raise RuntimeError("parsed zero model rows from CursorBench table")
    entries.sort(key=lambda e: -e["score"])
    return {"entries": entries, "data_date": "2026-09-12"}
