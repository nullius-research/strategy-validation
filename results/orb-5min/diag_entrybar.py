"""Diagnosis noise-check failure test H: is the mirrored trade stopped more often in the entry bar?"""
import numpy as np, orb_control as oc
rng = np.random.default_rng(7)
rows = []
for s in range(6):
    days = oc.synth_days(rng)
    df, _ = oc.run_rule(days)
    byday = {d["day"]: d for d in days}
    ent_real = ent_opp = 0
    for t in df.itertuples():
        d = byday[t.day]; i = t.i
        if t.side > 0:
            ent_real += d["l"][i] <= t.entry - t.risk
            ent_opp += d["h"][i] >= t.entry + t.risk
        else:
            ent_real += d["h"][i] >= t.entry + t.risk
            ent_opp += d["l"][i] <= t.entry - t.risk
    gr = (df.gross > 0).mean(); go = (df.gross_opp > 0).mean()
    print(f"set {s+1}: trades {len(df)}  stopped in entry bar real {ent_real} mirrored {ent_opp}  "
          f"gross win real {100*gr:.1f}% mirrored {100*go:.1f}%  "
          f"mean gross R real {(df.gross/df.risk).mean():+.4f} mirrored {(df.gross_opp/df.risk).mean():+.4f}")
