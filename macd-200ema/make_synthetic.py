"""make_synthetic.py . Random-walk M15 data in MT5 export format, no edge by construction.
Usage: python make_synthetic.py --out ./synthetic --seed 1"""
import argparse, numpy as np, pandas as pd
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--years", type=float, default=4)
a = ap.parse_args(); rng = np.random.default_rng(a.seed); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
idx = pd.date_range("2022-08-01", periods=int(a.years * 365 * 96), freq="15min"); idx = idx[idx.dayofweek < 5]
for sym, p0, dvol, dec in [("EURUSD", 1.08, 0.005, 5), ("EURJPY", 160.0, 0.006, 3)]:
    sub = 15; s = dvol / np.sqrt(1440)
    steps = rng.normal(0, s, (len(idx), sub))
    path = p0 * np.exp(np.cumsum(steps.ravel())).reshape(len(idx), sub)
    op = np.concatenate([[p0], path[:-1, -1]])
    hi = np.maximum(path.max(1), op); lo = np.minimum(path.min(1), op); cl = path[:, -1]
    df = pd.DataFrame({"<DATE>": idx.strftime("%Y.%m.%d"), "<TIME>": idx.strftime("%H:%M:%S"),
        "<OPEN>": op.round(dec), "<HIGH>": hi.round(dec), "<LOW>": lo.round(dec), "<CLOSE>": cl.round(dec),
        "<TICKVOL>": 100, "<VOL>": 0, "<SPREAD>": 0})
    df.to_csv(out / f"{sym}_M15_synthetic.csv", sep="\t", index=False)
    print(sym, len(df))
