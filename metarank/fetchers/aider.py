"""Aider polyglot coding leaderboard (225 Exercism tasks, 6 languages)."""
import re, requests
from html.parser import HTMLParser

SOURCE = {"id": "aider", "name": "Aider", "url": "https://aider.chat/docs/leaderboards/",
          "what": "225 real coding exercises across 6 languages, % passing",
          "category": "coding"}
URL = "https://aider.chat/docs/leaderboards/"

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_td=False; self.in_tr=False
        self.cell=""; self.row=[]; self.rows=[]
    def handle_starttag(self, tag, attrs):
        if tag=="tr": self.in_tr=True; self.row=[]
        if tag in ("td","th"): self.in_td=True; self.cell=""
    def handle_endtag(self, tag):
        if tag in ("td","th"): self.in_td=False; self.row.append(self.cell.strip())
        if tag=="tr": self.in_tr=False; self.rows.append(self.row)
    def handle_data(self, d):
        if self.in_td: self.cell+=d

def fetch():
    html = requests.get(URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=60).text
    p = TableParser(); p.feed(html)
    entries = []
    for row in p.rows:
        if len(row) >= 3 and re.match(r"^[A-Za-z0-9]", row[1] or ""):
            m = re.match(r"([\d.]+)%", row[2] or "")
            if m:
                entries.append({"raw_name": row[1], "org": None,
                                "score": float(m.group(1))})
    # dedupe, keep best score per raw name
    best = {}
    for e in entries:
        if e["raw_name"] not in best or e["score"] > best[e["raw_name"]]["score"]:
            best[e["raw_name"]] = e
    entries = sorted(best.values(), key=lambda e: -e["score"])
    return {"entries": entries, "data_date": None}
