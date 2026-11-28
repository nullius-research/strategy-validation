#!/usr/bin/env python3
"""Supplementary, descriptive (not in the hypothesis): the source's baseline, every RSI(3) < 22 day without the EMA and
VWAP filters, same entry, exit and handling as the rule. Run from the repository root:
python results/qqq-rsi3-vwap/rsi3_alone.py QQQ_yahoo_D1.csv"""
import sys, numpy as np
sys.path.insert(0, "qqq-rsi3-vwap")
import qqq_rsi3_vwap_control as q
d, o, h, l, c, v = q.load(sys.argv[1])
for end, label in [(None, "P1"), ("2026-09-30", "P0")]:
    hi = len(d) - 1 if end is None else int(np.searchsorted(d, end, side="right")) - 1
    for kind in ["wilder", "cutler"]:
        ind = q.indicators(h, l, c, v, kind)
        pool = ind["low_rsi"].copy(); pool[:q.WARMUP] = False
        t = q.seq_trades(pool, ind["rsi"], 0, hi, 1.0, np.random.default_rng(0))
        for cost in [0, 0.0002]:
            r = q.rets(o, c, t, cost)
            print(label, kind, "cost", cost, "RSI3<22 alone: trades", len(t), "win %.1f" % (100 * (r > 0).mean()),
                  "mean %+.3f%%" % (100 * r.mean()), "PF %.2f" % q.pf(r))
