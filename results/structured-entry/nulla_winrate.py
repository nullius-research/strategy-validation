"""Test L, added after run 01 (descriptive, not decisive): win rate of Null A runs
with exactly the rules of run 01 (P1, seed 41, 10,000 runs). Uses null_runs with col=4."""
import numpy as np, pandas as pd
import structured_control as sc
df = pd.read_csv("BTCUSDT_30m_binance.csv")
ms, o, h, l, c, stopv, eldir, sig, aux = sc.build(df)
lo = sc.first_valid(stopv, aux)
hi = int(np.searchsorted(ms, pd.Timestamp("2026-11-15", tz="UTC").value // 10**6))
p = (sig[lo:hi] != 0).sum() / (eldir[lo:hi] != 0).sum()
for structured, m in ((1, 0.5), (0, 0.5), (0, 0.25)):
    w, cn = sc.null_runs(o, h, l, c, stopv, sig, eldir, p, lo, hi, structured, m, sc.MIN_STOP, sc.SPACING, sc.COST_SIDE, 10000, sc.SEED_NULL, 4)
    w = 100 * w[~np.isnan(w)]
    print("%s  Null A winrate p5 %.1f  p50 %.1f  p95 %.1f  mean setups %.0f" % ("G" if structured else "Z m=%.2f" % m, *np.percentile(w, [5, 50, 95]), cn.mean()))
