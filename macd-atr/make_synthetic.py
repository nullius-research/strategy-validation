"""Synthetic driftless random-walk FX data in the MT5 export format (H1 and D1), for checking
macdatr_control.py. No edge exists in this data by construction."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

PAIRS = ["EURGBP","EURAUD","EURNZD","EURUSD","EURCAD","EURCHF","GBPAUD","GBPNZD","GBPUSD","GBPCAD",
         "GBPCHF","AUDNZD","AUDUSD","AUDCAD","AUDCHF","NZDUSD","NZDCAD","NZDCHF","USDCAD","USDCHF",
         "CADCHF","NZDJPY","CADJPY","CHFJPY","EURJPY","USDJPY","AUDJPY","GBPJPY"]
SUB = 12           # sub-steps per hour for high and low
DAILY_VOL = 0.006

def write(df, path, digits):
    out = pd.DataFrame({
        "<DATE>": df.index.strftime("%Y.%m.%d"), "<TIME>": df.index.strftime("%H:%M:%S"),
        "<OPEN>": df.o.round(digits), "<HIGH>": df.h.round(digits), "<LOW>": df.l.round(digits),
        "<CLOSE>": df.c.round(digits), "<TICKVOL>": 1000, "<VOL>": 0, "<SPREAD>": 0})
    out.to_csv(path, sep="\t", index=False, float_format=f"%.{digits}f")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--pairs", default=",".join(PAIRS))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    hours = pd.date_range("2010-01-04", "2026-11-05 23:00", freq="h")
    hours = hours[hours.dayofweek < 5]
    n = len(hours)
    sd = DAILY_VOL / np.sqrt(24 * SUB)
    for p in a.pairs.split(","):
        jpy = p.endswith("JPY")
        p0 = 100.0 if jpy else 1.2
        digits = 3 if jpy else 5
        steps = rng.normal(0, sd, size=(n, SUB))
        logp = np.cumsum(steps.ravel()).reshape(n, SUB)
        start = np.concatenate([[0.0], logp[:-1, -1]])
        path = np.concatenate([start[:, None], logp], axis=1)
        px = p0 * np.exp(path)
        h1 = pd.DataFrame({"o": px[:, 0], "h": px.max(axis=1), "l": px.min(axis=1), "c": px[:, -1]}, index=hours)
        g = h1.groupby(h1.index.normalize())
        d1 = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last()})
        write(h1[h1.index >= "2015-01-01"], out / f"{p}_H1.csv", digits)
        write(d1, out / f"{p}_D1.csv", digits)

if __name__ == "__main__":
    main()
