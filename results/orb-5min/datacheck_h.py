#!/usr/bin/env python3
"""datacheck_h.py · Nullius Research · test H, hypothesis section 5.
Metadata only, no outcomes: valid sessions per year, opening minute found, share of days with empty spread.
Usage: python datacheck_h.py US500_M1.csv"""
import sys
import numpy as np, pandas as pd
import orb_control as oc
days = oc.build_days(oc.load_mt5(sys.argv[1]), 0.01)
rows = []
for d in days:
    if d["day"] < pd.Timestamp("2017-03-21"):
        continue
    s = oc.session(d)
    k = oc.detect_open(d)
    sp_empty = None
    if s is not None:
        idx = s[1]
        sp_empty = bool((d["sp"][idx] == 0).all())
    rows.append({"year": d["day"].year, "valid": s is not None, "offset": (k - oc.RTH_START) if k is not None else None,
                 "spread_empty": sp_empty})
df = pd.DataFrame(rows)
print(f"server days from 2017-03-21: {len(df)}  last day {days[-1]['day'].date()}")
g = df.groupby("year")
print("year  server_days  valid_sessions  spread_empty_share_of_valid")
for y, x in g:
    v = x[x.valid]
    print(f"{y}  {len(x):11d}  {len(v):14d}  {v.spread_empty.mean()*100 if len(v) else float('nan'):6.1f}%")
v = df[df.valid]
print("opening offset among valid sessions (min vs 16:30 server): " + str(v.offset.value_counts().sort_index().to_dict()))
