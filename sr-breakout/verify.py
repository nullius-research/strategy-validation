"""Independent spot check of 5 random P1 trades (plain pandas, no numba, no shared helpers)."""
import numpy as np, pandas as pd, sys
d = pd.read_csv(sys.argv[1], sep="\t"); d.columns = [c.strip("<>") for c in d.columns]
d["T"] = pd.to_datetime(d["DATE"] + " " + d["TIME"], format="%Y.%m.%d %H:%M:%S")
d = d[d["T"] >= "2017-05-01"].reset_index(drop=True)
tr = pd.read_csv("trades_P1.csv", parse_dates=["ENTRY_TIME", "EXIT_TIME"])
rng = np.random.default_rng(99)
def agg(rule):
    g = d.groupby(rule)
    return pd.DataFrame({"H": g["HIGH"].max(), "L": g["LOW"].min(), "C": g["CLOSE"].last(), "S": g["T"].first(), "E": g["T"].last() + pd.Timedelta("30min")}).reset_index(drop=True)
day = d["T"].dt.normalize()
H4 = agg([day, d["T"].dt.hour // 4]); D1 = agg(day)
for k in rng.choice(len(tr), 5, replace=False):
    t = tr.iloc[k]; dirn = t["DIR"]
    entry_bar = d[d["T"] < t["ENTRY_TIME"]].iloc[-1]
    ok_entry = abs(entry_bar["CLOSE"] - t["ENTRY"]) < 1e-9
    L = t["STOP0"] + dirn * 0.5 * t["ATR"]
    found = []
    for name, F in (("H4", H4), ("D1", D1)):
        x = F["H"].to_numpy() if dirn == 1 else F["L"].to_numpy()
        for j in range(2, len(F) - 2):
            if abs(x[j] - L) < 1e-6:
                frac = all(x[j] > x[j + s] for s in (-2, -1, 1, 2)) if dirn == 1 else all(x[j] < x[j + s] for s in (-2, -1, 1, 2))
                act = F["E"].iloc[j + 2]
                found.append((name, F["S"].iloc[j], frac, act <= t["ENTRY_TIME"] - pd.Timedelta("1h")))
    # previous H1 close and current H1 close vs level
    h_end = t["ENTRY_TIME"]; prev = d[d["T"] < h_end - pd.Timedelta("1h")].iloc[-1]["CLOSE"]
    cross = (t["ENTRY"] > L >= prev) if dirn == 1 else (t["ENTRY"] < L <= prev)
    # replay trailing stop
    stop = t["STOP0"]; ext = t["ENTRY"]; A = t["ATR"]
    stop = max(stop, ext - 2 * A) if dirn == 1 else min(stop, ext + 2 * A)
    path = d[(d["T"] >= h_end) & (day == entry_bar["T"].normalize())]
    px = None
    for _, b in path.iterrows():
        if dirn == 1:
            if b["OPEN"] <= stop: px = b["OPEN"]; break
            if b["LOW"] <= stop: px = stop; break
            ext = max(ext, b["CLOSE"]); stop = max(stop, ext - 2 * A)
        else:
            if b["OPEN"] >= stop: px = b["OPEN"]; break
            if b["HIGH"] >= stop: px = stop; break
            ext = min(ext, b["CLOSE"]); stop = min(stop, ext + 2 * A)
    if px is None: px = path.iloc[-1]["CLOSE"]
    print(f"trade {k}: {t['ENTRY_TIME']} dir {dirn:+d} entry ok {ok_entry} level {L:.2f} fractal {found} cross ok {cross} exit script {t['EXIT']:.2f} replay {px:.2f} R {t['R_NET']:+.3f}")
