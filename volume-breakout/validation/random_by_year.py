"""
random_by_year.py . Random-entry baseline per calendar year.

Same construction as the 'random entry dates' control in control.py (same ticker,
same direction, same stop distance in ATR, same target, costs and max hold), but
each random trade is kept with its own entry year, so a year of the real rule can
be read next to what a random long entry earned in that year.
Descriptive only. It does not change the verdict of control.py.

    python validation/random_by_year.py --signals briefs/signals.csv --bars data/history.csv --draws 50 --seed 11
"""
import argparse, importlib.util
from pathlib import Path
import numpy as np, pandas as pd

spec = importlib.util.spec_from_file_location("control", Path(__file__).with_name("control.py"))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

p = argparse.ArgumentParser()
p.add_argument("--signals", required=True); p.add_argument("--bars", required=True)
p.add_argument("--target-r", type=float, default=2.0); p.add_argument("--max-hold", type=int, default=20)
p.add_argument("--cost-bps", type=float, default=10.0); p.add_argument("--draws", type=int, default=50)
p.add_argument("--seed", type=int, default=11)
a = p.parse_args()

bars = c.load_bars(a.bars); sig = c.load_signals(a.signals)
by = {t: g.reset_index(drop=True) for t, g in bars.groupby("ticker")}
rng = np.random.default_rng(a.seed)
rows = []
for _ in range(a.draws):
    for row in sig.itertuples(index=False):
        g = by.get(row.ticker)
        if g is None or len(g) < c.ATR_PERIOD + a.max_hold + 5: continue
        idx = min(int(g["date"].searchsorted(row.date, side="right")), len(g) - 1)
        ra = float(g["atr"].to_numpy()[idx])
        if not np.isfinite(ra) or ra <= 0: continue
        m = abs(row.entry - row.stop) / ra
        pos = int(rng.integers(c.ATR_PERIOD + 1, len(g) - a.max_hold - 1))
        e = float(g["open"].to_numpy()[pos]); sd = m * float(g["atr"].to_numpy()[pos - 1])
        if sd <= 0 or not np.isfinite(sd): continue
        r = c.walk_trade(g.iloc[pos:pos + a.max_hold], int(row.direction), e, sd, a.target_r, (e * a.cost_bps / 1e4) / sd)
        if r is not None: rows.append((g["date"].iloc[pos].year, r))
d = pd.DataFrame(rows, columns=["year", "r"])
print(f"random entries: {len(d)} trades, mean {d.r.mean():+.4f} R")
for y, g in d.groupby("year"): print(f"{y}  n={len(g):6d}  mean {g.r.mean():+.4f} R")
