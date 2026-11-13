#!/usr/bin/env python3
"""datacheck_g2.py · Nullius Research · test G2, hypothesis section 5.
Prices and metadata only, no outcomes (no returns, no shares higher).
Usage: python datacheck_g2.py SPY_daily.csv US500_M1.csv"""
import sys
import numpy as np, pandas as pd
import spy_open_control as g
spy = g.load_spy(sys.argv[1])
print(f"SPY {spy.index[0].date()} to {spy.index[-1].date()}, {len(spy)} days")
print("SPY trading days per year: " + ", ".join(f"{y}: {n}" for y, n in spy.groupby(spy.index.year).size().items()))
prev = spy["close"].shift(1)
eqp = (np.isclose(spy["open"], prev, atol=1e-6))[1:].mean() * 100
out = ((spy["open"] > spy["high"] + 1e-9) | (spy["open"] < spy["low"] - 1e-9)).sum()
dup = spy.index.duplicated().sum()
print(f"SPY open equal to previous close: {eqp:.2f}% of days ({'REPORT, above 2%' if eqp > 2 else 'below 2%'})  "
      f"open outside day range: {out}  duplicate dates: {dup}")
for lab, lo, hi in (("US500 P1", "2017-03-22", "2026-09-18"), ("US500 P3", "2026-09-19", None)):
    M, dates, st, offs = g.us500_matrix(sys.argv[2], 0.01, lo, hi)
    print(f"{lab}: {dates[0].date()} to {dates[-1].date()}  server days {st['days']}  opening found {st['open_found']} "
          f"({st['open_found']/st['days']*100:.1f}%)  valid sessions {st['valid']} ({st['valid']/st['days']*100:.1f}%)  "
          f"opening offset (min vs 16:30 server): {dict(sorted(offs.items()))}")
    print(f"  valid sessions per year: " + ", ".join(f"{y}: {n}" for y, n in pd.Series(dates.year).value_counts().sort_index().items()))
