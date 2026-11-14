#!/usr/bin/env python3
"""Data check test I: metadata only (counts, gaps, empty or non-positive values). No prices printed."""
import csv, sys, datetime as dt, collections
for f in sys.argv[1:]:
    rows = list(csv.DictReader(open(f)))
    d = [dt.date.fromisoformat(r["date"]) for r in rows]
    yrs = collections.Counter(x.year for x in d)
    gaps = [(d[i-1], d[i]) for i in range(1, len(d)) if (d[i] - d[i-1]).days > 5]
    bad = sum(1 for r in rows for k in ("close", "adjclose") if not r[k] or float(r[k]) <= 0)
    order = all(d[i] > d[i-1] for i in range(1, len(d)))
    print(f"{f}: {len(d)} days, {d[0]} to {d[-1]}, ascending {order}, empty/non-positive {bad}, gaps > 5 calendar days {len(gaps)}")
    for a, b in gaps: print(f"   gap {a} -> {b}")
    full = {y: n for y, n in yrs.items() if y not in (d[0].year, d[-1].year)}
    print(f"   days per full year: min {min(full.values())} ({min(full, key=full.get)}), max {max(full.values())} ({max(full, key=full.get)})")
