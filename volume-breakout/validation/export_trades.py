"""
export_trades.py . Writes the per-trade results behind the control.py summary.

Uses the scoring functions of control.py unchanged: same path walk, same costs,
same 'stop and target in one bar counts as stop' rule. Adds nothing to the test.

    python validation/export_trades.py --signals briefs/signals.csv --bars data/history.csv --out trades.csv
"""
import argparse
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("control", Path(__file__).with_name("control.py"))
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)

p = argparse.ArgumentParser()
p.add_argument("--signals", required=True)
p.add_argument("--bars", required=True)
p.add_argument("--target-r", type=float, default=2.0)
p.add_argument("--max-hold", type=int, default=20)
p.add_argument("--cost-bps", type=float, default=10.0)
p.add_argument("--out", default="trades.csv")
a = p.parse_args()

bars = control.load_bars(a.bars)
signals = control.load_signals(a.signals)
by_ticker = {t: g.reset_index(drop=True) for t, g in bars.groupby("ticker")}
res = control.score_real(signals, by_ticker, a.target_r, a.max_hold, a.cost_bps)

# score_real keeps signal order and skips nothing on this data; check before joining.
assert len(res) == len(signals), "some signals were skipped, join would be wrong"
out = signals.copy()
out["r"] = res["r"].round(6).to_numpy()
out.to_csv(a.out, index=False, date_format="%Y-%m-%d")

s = control.summarise(res)
print(f"{s['n']} trades, expectancy {s['expectancy']:+.4f} R, PF {s['profit_factor']:.3f}, win {s['win_rate']:.1%}")
out["year"] = out["date"].dt.year
for y, g in out.groupby("year"):
    r = g["r"]; w, l = r[r > 0].sum(), -r[r < 0].sum()
    print(f"{y}  n={len(g):4d}  mean {r.mean():+.4f} R  win {(r > 0).mean():.1%}  PF {w / l:.2f}")
