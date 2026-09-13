"""Epoch AI capabilities index (CC-BY-4.0). Independent re-runs of frontier benchmarks."""
import io, zipfile, requests, pandas as pd

SOURCE = {"id": "epoch", "name": "Epoch AI", "url": "https://epoch.ai/benchmarks",
          "what": "Independent re-runs of hard benchmarks, combined capability index",
          "category": "agents"}
URL = "https://epoch.ai/data/benchmark_data.zip"

def fetch():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    df = pd.read_csv(z.open("epoch_capabilities_index/eci_scores.csv"))
    df = df.dropna(subset=["eci"]).sort_values("eci", ascending=False)
    entries = []
    for row in df.itertuples():
        d = row._asdict()
        raw = d.get("Display name") or d.get("Model")
        entries.append({"raw_name": raw, "org": d.get("Organization"),
                        "score": float(d["eci"])})
    return {"entries": entries, "data_date": None}
