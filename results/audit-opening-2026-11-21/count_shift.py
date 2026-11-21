"""Count per period the days where the old detection (OPEN_OFFSETS -60,0,60; largest 15-min tick-volume jump)
chose another opening than 16:30 server time. Same logic as detect_open in the published scripts."""
import sys, numpy as np, pandas as pd
def load(path):
    df = pd.read_csv(path, sep="\t")
    df.columns = [c.strip("<>").lower() for c in df.columns]
    t = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")
    return pd.DataFrame({"min": (t.dt.hour*60 + t.dt.minute).values, "v": df["tickvol"].values, "day": t.dt.normalize().values})
def detect(mins, vol):
    full = pd.Series(vol, index=mins).groupby(level=0).sum().reindex(range(1440)).fillna(0).values
    best, bk = -np.inf, None
    for off in (-60, 0, 60):
        k = 990 + off
        j = full[k:k+15].mean() - full[k-15:k].mean()
        if j > best: best, bk = j, k
    return bk - 990
path = sys.argv[1]; periods = [p.split(":") for p in sys.argv[2:]]
m = load(path)
res = {}
for day, g in m.groupby("day"):
    mins = g["min"].values
    if ((mins >= 990) & (mins < 1380)).sum() < 0.9*390: continue   # only days with a full session at 16:30
    res[pd.Timestamp(day)] = detect(mins, g["v"].values)
s = pd.Series(res)
for a, b in periods:
    x = s.loc[a:b]
    print(f"{path.split('/')[-1]} {a} to {b}: sessions {len(x)}, at 16:30 {int((x==0).sum())}, at 15:30 {int((x==-60).sum())}, at 17:30 {int((x==60).sum())}")
