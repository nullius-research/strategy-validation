"""Option for v1.1 test H: Null A measured from the open of the bar after the breakout bar,
both directions, same stop and target distances. Fake market unchanged (60 sub-steps), 24 sets, seed 7."""
import numpy as np, orb_control as oc
rng = np.random.default_rng(7)
pcts = []
for s in range(24):
    days = oc.synth_days(rng)
    df, _ = oc.run_rule(days)
    byday = {d["day"]: d for d in days}
    a, b = [], []
    for t in df.itertuples():
        d = byday[t.day]; k_open, idx, _ = oc.session(d); last = idx[-1]
        j = t.i + 1
        if j > last:
            continue
        e = d["o"][j]
        r = {}
        for s_ in (t.side, -t.side):
            px, _, _ = oc.simulate(d["o"], d["h"], d["l"], d["c"], j, s_, e - s_ * t.risk, e + s_ * t.tgt_d, last)
            r[s_] = (s_ * (px - e) - d["sp"][j] - 0.5) / t.risk
        a.append(r[t.side]); b.append(r[-t.side])
    a, b = np.array(a), np.array(b)
    flip = rng.random((10000, len(a))) < 0.5
    means = np.where(flip, b, a).mean(1)
    p = 100 * (means < a.mean()).mean() + 50 * (means == a.mean()).mean()
    pcts.append(p)
    print(f"set {s+1:2d}: trades {len(a)}  real {a.mean():+.4f}  mirrored {b.mean():+.4f}  percentile {p:5.1f}", flush=True)
pcts = np.array(pcts)
ok = 35 <= pcts.mean() <= 65 and (pcts > 95).sum() <= 3
print(f"mean percentile {pcts.mean():.1f}  above 95: {(pcts>95).sum()} of 24  -> {'PASSED' if ok else 'FAILED'}")
