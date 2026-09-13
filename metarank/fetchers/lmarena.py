"""LMArena text-arena leaderboard via the public lmarena-ai/leaderboard-dataset (CC-BY-4.0)."""
import io, requests, pandas as pd

SOURCE = {"id": "lmarena", "name": "LMArena", "url": "https://lmarena.ai/leaderboard",
          "what": "Millions of blind human votes, Bradley-Terry rating",
          "category": "chat"}
URL = ("https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/"
       "resolve/main/text/latest-00000-of-00001.parquet")

def fetch():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    df = pd.read_parquet(io.BytesIO(r.content))
    df = df[df["category"] == "overall"]
    latest = df["leaderboard_publish_date"].max()
    df = df[df["leaderboard_publish_date"] == latest]
    df = df.sort_values("rank")
    entries = [{"raw_name": row.model_name, "org": row.organization,
                "score": float(row.rating)} for row in df.itertuples()]
    return {"entries": entries, "data_date": str(latest)}
