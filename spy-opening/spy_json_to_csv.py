#!/usr/bin/env python3
"""spy_json_to_csv.py · Nullius Research · test G2
Yahoo chart-API JSON -> SPY_daily.csv (date, open, high, low, close, volume), raw prices.
Only days before --cut (the day still in progress is left out). Deterministic, no LLM.
Usage: python spy_json_to_csv.py spy_raw.json SPY_daily.csv --cut 2026-11-13"""
import argparse, json
import pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("--cut", required=True)
a = ap.parse_args()
r = json.load(open(a.src, encoding="utf-8"))["chart"]["result"][0]
q = r["indicators"]["quote"][0]
d = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert(r["meta"]["exchangeTimezoneName"]).date
df = pd.DataFrame({"date": d, "open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"], "volume": q["volume"]})
df = df[pd.to_datetime(df["date"]) < pd.Timestamp(a.cut)]
df.to_csv(a.dst, index=False, float_format="%.6f")
print(f"rows {len(df)}  {df['date'].iloc[0]} to {df['date'].iloc[-1]}  missing values {int(df.isna().sum().sum())}")
