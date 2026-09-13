"""LMArena WebDev Arena leaderboard via the public
lmarena-ai/leaderboard-dataset (CC-BY-4.0). Human votes on web-app builds,
Bradley-Terry rating. Same dataset as the text arena, 'webdev' category.
"""
import io, requests, pandas as pd

SOURCE = {"id": "webdev", "name": "LMArena WebDev",
          "url": "https://lmarena.ai/leaderboard",
          "what": "Blind human votes on web-app builds, Bradley-Terry rating",
          "category": "coding"}
URL = ("https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/"
       "resolve/main/webdev/latest-00000-of-00001.parquet")


def fetch():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    df = pd.read_parquet(io.BytesIO(r.content))
    df = df[df["category"] == "webdev"]
    latest = df["leaderboard_publish_date"].max()
    df = df[df["leaderboard_publish_date"] == latest]
    df = df.sort_values("rank")
    entries = [{"raw_name": row.model_name, "org": row.organization,
                "score": float(row.rating)} for row in df.itertuples()]
    return {"entries": entries, "data_date": str(latest)}
