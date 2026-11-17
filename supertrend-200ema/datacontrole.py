"""datacontrole.py . Data check for test M: rows, period, duplicates, invalid prices, gaps, jumps. Broker time as exported."""
import sys, numpy as np, pandas as pd
from pathlib import Path
for f in sys.argv[1:]:
    raw = pd.read_csv(f, sep=None, engine="python"); raw.columns = [c.strip().strip("<>").upper() for c in raw.columns]
    t = pd.to_datetime(raw["DATE"].astype(str) + " " + raw["TIME"].astype(str), format="mixed")
    o, h, l, c = (pd.to_numeric(raw[k], errors="coerce") for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    dup = int(t.duplicated().sum()); nan = int(pd.concat([o, h, l, c], axis=1).isna().any(axis=1).sum())
    bad = int(((o <= 0) | (h <= 0) | (l <= 0) | (c <= 0)).sum())
    incons = int(((h < l) | (o > h + 1e-12) | (o < l - 1e-12) | (c > h + 1e-12) | (c < l - 1e-12)).sum())
    dt = t.diff().dt.total_seconds() / 60
    prev = t.shift(1)
    weekend = (prev.dt.dayofweek == 4) & (t.dt.dayofweek.isin([0, 1])) & (dt <= 4 * 1440)
    xmas_ny = ((prev.dt.month == 12) & (prev.dt.day >= 24)) | ((t.dt.month == 1) & (t.dt.day <= 2))
    daily_break = (t.dt.hour == 0) & (t.dt.minute == 0) & (dt <= 75)
    gaps = (dt > 15) & ~weekend & ~xmas_ny & ~daily_break
    missing = int((dt[gaps] / 15 - 1).sum())
    jump = (np.log(o / c.shift(1)).abs() > 0.01)
    unsorted = int((dt < 0).sum())
    print(f"{Path(f).name}: rows {len(raw):,}, {t.iloc[0]} to {t.iloc[-1]}, duplicates {dup}, NaN {nan}, <=0 {bad}, OHLC inconsistent {incons}, unsorted {unsorted}")
    print(f"   weekday gaps >15 min: {int(gaps.sum())} gaps, about {missing} missing bars; largest gaps:")
    for i in dt[gaps].sort_values(ascending=False).index[:5]:
        print(f"      {t.iloc[i-1]} -> {t.iloc[i]}  ({dt.iloc[i]:.0f} min)")
    print(f"   open vs previous close jumps >1%: {int(jump.sum())}" + "".join(f"\n      {t.iloc[i]}  {o.iloc[i]} vs {c.iloc[i-1]}" for i in jump[jump].index[:5]))
