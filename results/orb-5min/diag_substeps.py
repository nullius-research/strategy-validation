"""Diagnosis test H: does the Null A bias shrink with finer fake markets (overshoot at the level)?
Same seed 7, 6 sets, mean gross R real minus mirrored, and percentile vs Null A."""
import sys, numpy as np, orb_control as oc
for K in (15, 60, 600):
    oc.NOISE_SUBSTEPS = K
    rng = np.random.default_rng(7)
    diffs, pcts = [], []
    for s in range(6):
        df, _ = oc.run_rule(oc.synth_days(rng))
        diffs.append(((df.gross - df.gross_opp) / df.risk).mean() / 2)
        pcts.append(oc.null_a(df, 0.25, rng, 10000)[1])
    print(f"substeps {K:4d}: half gap real vs mirrored {np.mean(diffs):+.4f} R  "
          f"mean percentile {np.mean(pcts):.1f}  per set {' '.join(f'{p:.0f}' for p in pcts)}", flush=True)
