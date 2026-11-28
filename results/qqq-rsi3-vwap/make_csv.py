#!/usr/bin/env python3
"""
Nullius Research, test T: Yahoo chart JSON (v8, interval 1d) to CSV, plus a metadata-only data check.
Usage: python make_csv.py qqq_raw.json QQQ_yahoo_D1.csv
Prints only metadata (rows, first and last date, missing values, gaps, splits, zero volume). No prices, no indicators.
"""
import json, sys, csv
from datetime import datetime, timezone, timedelta

src, dst = sys.argv[1], sys.argv[2]
r = json.load(open(src))["chart"]["result"][0]
meta = r["meta"]; ts = r["timestamp"]; q = r["indicators"]["quote"][0]
adj = r["indicators"].get("adjclose", [{}])[0].get("adjclose")
off = timedelta(seconds=meta.get("gmtoffset", -18000))
rows, missing = [], 0
for k, t in enumerate(ts):
    d = (datetime.fromtimestamp(t, timezone.utc) + off).strftime("%Y-%m-%d")
    vals = [q[f][k] for f in ("open", "high", "low", "close")] + [adj[k] if adj else None, q["volume"][k]]
    if any(v is None for v in vals):
        missing += 1; continue
    rows.append([d] + vals)
seen = set(); dup = 0; out = []
for row in rows:
    if row[0] in seen:
        dup += 1; continue
    seen.add(row[0]); out.append(row)
with open(dst, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "adjclose", "volume"])
    w.writerows(out)
dates = [datetime.strptime(x[0], "%Y-%m-%d") for x in out]
gaps = [(a.date(), b.date()) for a, b in zip(dates, dates[1:]) if (b - a).days > 5]
bad = sum(1 for x in out if not (x[3] <= min(x[1], x[4]) + 1e-9 and x[2] >= max(x[1], x[4]) - 1e-9))
print(f"symbol {meta.get('symbol')}  timezone {meta.get('exchangeTimezoneName')}  rows {len(out)}  first {out[0][0]}  last {out[-1][0]}")
print(f"rows with a missing value dropped: {missing}  duplicate dates dropped: {dup}  zero volume: {sum(1 for x in out if x[6] == 0)}")
print(f"gaps over 5 calendar days: {len(gaps)} {gaps[:5]}")
print(f"rows where low/high do not enclose open and close: {bad}")
ev = r.get("events", {})
print(f"splits: {[(datetime.fromtimestamp(int(k), timezone.utc).date().isoformat(), v.get('splitRatio')) for k, v in ev.get('splits', {}).items()]}")
print(f"dividends in file: {len(ev.get('dividends', {}))}")
