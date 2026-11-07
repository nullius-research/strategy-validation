"""make_synthetic.py . Random-walk M15 data in MT5 export format, no edge by construction.
Usage: python make_synthetic.py --out ./synthetic --seed 1 [--pairs EURUSD,GBPUSD,USDJPY]"""
import argparse, numpy as np, pandas as pd
from pathlib import Path
SPEC = {"EURUSD": (1.08, 0.005, 5), "GBPUSD": (1.27, 0.006, 5), "USDJPY": (145.0, 0.006, 3),
        "EURJPY": (160.0, 0.006, 3), "USDCHF": (0.88, 0.005, 5), "USDCAD": (1.36, 0.004, 5),
        "NZDUSD": (0.60, 0.006, 5), "EURGBP": (0.86, 0.003, 5), "GBPJPY": (190.0, 0.007, 3)}
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--years", type=float, default=4); ap.add_argument("--pairs", default="EURUSD")
a = ap.parse_args(); rng = np.random.default_rng(a.seed); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
idx = pd.date_range("2022-08-01", periods=int(a.years * 365 * 96), freq="15min"); idx = idx[idx.dayofweek < 5]
for sym in a.pairs.split(","):
    p0, dvol, dec = SPEC[sym]
    sub = 15; s = dvol / np.sqrt(1440)
    path = p0 * np.exp(np.cumsum(rng.normal(0, s, (len(idx), sub)).ravel())).reshape(len(idx), sub)
    op = np.concatenate([[p0], path[:-1, -1]])
    hi = np.maximum(path.max(1), op); lo = np.minimum(path.min(1), op); cl = path[:, -1]
    pd.DataFrame({"<DATE>": idx.strftime("%Y.%m.%d"), "<TIME>": idx.strftime("%H:%M:%S"),
        "<OPEN>": op.round(dec), "<HIGH>": hi.round(dec), "<LOW>": lo.round(dec), "<CLOSE>": cl.round(dec),
        "<TICKVOL>": 100, "<VOL>": 0, "<SPREAD>": 0}).to_csv(out / f"{sym}_M15_synthetic.csv", sep="\t", index=False)
    print(sym, len(idx))
