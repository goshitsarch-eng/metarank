"""LiveBench: contamination-free benchmark with fresh monthly questions."""
import csv, io, requests

SOURCE = {"id": "livebench", "name": "LiveBench", "url": "https://livebench.ai/",
          "what": "Fresh monthly questions, contamination-resistant average score",
          "category": "general"}
LISTING = "https://api.github.com/repos/livebench/livebench.github.io/contents/public"
RAW = "https://raw.githubusercontent.com/livebench/livebench.github.io/main/public/"

def fetch():
    files = requests.get(LISTING, timeout=30).json()
    tables = sorted(f["name"] for f in files
                    if f["name"].startswith("table_") and f["name"].endswith(".csv"))
    latest = tables[-1]
    text = None
    for attempt in range(4):
        try:
            text = requests.get(RAW + latest, timeout=90).text
            break
        except requests.RequestException:
            if attempt == 3: raise
    entries = []
    for row in csv.DictReader(io.StringIO(text)):
        name = row.pop("model")
        scores = []
        for v in row.values():
            try: scores.append(float(v))
            except (ValueError, TypeError): pass
        if scores:
            entries.append({"raw_name": name, "org": None,
                            "score": round(sum(scores)/len(scores), 2)})
    entries.sort(key=lambda e: -e["score"])
    date = latest[len("table_"):].rsplit(".",1)[0].replace("_","-")
    return {"entries": entries, "data_date": date}
