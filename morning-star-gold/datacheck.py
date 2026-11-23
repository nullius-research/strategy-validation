"""Test Q datacheck: metadata only (dates, bars per day, usable start, spread, session hours). No signals."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from morning_star import load, usable_start
d = load(sys.argv[1])
t = d["TIME"]
print(f"rows {len(d)}, first {t.iloc[0]}, last {t.iloc[-1]}")
print(f"duplicate timestamps {int(t.duplicated().sum())}, non-30-min-aligned {int(((t.dt.minute % 30) != 0).sum())}")
st = usable_start(d)
print(f"usable start (first month with >=40 M30 bars on every trading day onward? -> first such month): {st.date()}")
per_day = d.groupby(t.dt.date).size()
per_day.index = pd.to_datetime(per_day.index)
after = per_day[per_day.index >= st]
print(f"trading days from usable start {len(after)}; bars per day min {after.min()}, median {after.median():.0f}, max {after.max()}")
print("days with < 40 bars after usable start:", int((after < 40).sum()))
for y, g in after.groupby(after.index.year):
    print(f"  {y}: days {len(g)}, min bars {g.min()}, median {g.median():.0f}, days<40 {int((g<40).sum())}")
bd = pd.bdate_range(st, t.iloc[-1].normalize())
missing = bd.difference(after.index)
print(f"weekdays without data after usable start: {len(missing)}")
print("  " + ", ".join(str(x.date()) for x in missing))
x = d[t >= st]
print(f"median SPREAD (points) from usable start {x['SPREAD'].median():.0f}; per year:")
for y, g in x.groupby(x['TIME'].dt.year):
    print(f"  {y}: median {g['SPREAD'].median():.0f}, p90 {g['SPREAD'].quantile(.9):.0f}")
print("price digits check (sample closes):", x['CLOSE'].iloc[:3].tolist())
x2 = x[x['TIME'] >= '2021-11-06']
first = x2.groupby(x2['TIME'].dt.date)['TIME'].min().dt.strftime('%H:%M').value_counts().head(5)
last = x2.groupby(x2['TIME'].dt.date)['TIME'].max().dt.strftime('%H:%M').value_counts().head(5)
print("P1 first bar of day (top 5):", dict(first)); print("P1 last bar of day (top 5):", dict(last))
print("P1 weekday counts:", dict(x2.groupby(x2['TIME'].dt.date).size().index.map(lambda z: pd.Timestamp(z).day_name()).value_counts()))
print("P1 days", x2['TIME'].dt.date.nunique(), "first", x2['TIME'].iloc[0], "last", x2['TIME'].iloc[-1])
