"""check5_trades.py: recompute 5 random P1 trades of test H from the raw M1 export, without orb_control.py."""
import sys, numpy as np, pandas as pd
raw = pd.read_csv(sys.argv[1], sep="\t")
raw.columns = [c.strip("<>").lower() for c in raw.columns]
raw["ts"] = pd.to_datetime(raw["date"] + " " + raw["time"], format="%Y.%m.%d %H:%M:%S")
raw = raw.set_index("ts")
tr = pd.read_csv(sys.argv[2], parse_dates=["day"])
pick = tr.sample(5, random_state=5)
for t in pick.itertuples():
    d = raw.loc[str(t.day.date())]
    # opening: biggest jump in mean tick volume (15 min after vs before) at 15:30, 16:30, 17:30
    best = None
    for hh in (15, 16, 17):
        k = pd.Timestamp(f"{t.day.date()} {hh}:30")
        after = d.loc[k:k + pd.Timedelta(minutes=14), "tickvol"].reindex(pd.date_range(k, periods=15, freq="min")).fillna(0).mean()
        before = d.loc[k - pd.Timedelta(minutes=15):k - pd.Timedelta(minutes=1), "tickvol"].reindex(pd.date_range(k - pd.Timedelta(minutes=15), periods=15, freq="min")).fillna(0).mean()
        if best is None or after - before > best[0]:
            best = (after - before, k)
    k = best[1]
    first5 = d.loc[k:k + pd.Timedelta(minutes=4)]
    hi, lo = first5["high"].max(), first5["low"].min(); R = hi - lo
    sess = d.loc[k + pd.Timedelta(minutes=5):k + pd.Timedelta(minutes=389)]
    for ts, b in sess.iterrows():
        if b.high > hi or b.low < lo:
            break
    side = 1 if b.high > hi else -1
    lvl = hi if side > 0 else lo
    entry = max(lvl, b.open) if side > 0 else min(lvl, b.open)
    stop_d = min(abs(entry - (lo if side > 0 else hi)), 14.0)
    stop, tgt = entry - side * stop_d, lvl + side * 0.5 * R
    after = sess.loc[ts:]
    res = None
    for j, (ts2, c) in enumerate(after.iterrows()):
        hit_s = (c.low <= stop) if side > 0 else (c.high >= stop)
        hit_t = (c.high >= tgt) if side > 0 else (c.low <= tgt)
        if hit_s:
            px = stop if j == 0 else (min(stop, c.open) if side > 0 else max(stop, c.open)); res = ("stop", px); break
        if j > 0 and hit_t:
            res = ("target", tgt); break
    if res is None:
        res = ("close", after.iloc[-1].close)
    g = side * (res[1] - entry)
    ok = abs(g - t.gross) < 1e-6 and abs(entry - t.entry) < 1e-6 and res[0] == t.kind and side == t.side
    print(f"{t.day.date()} side {side:+d} range {R:.2f} entry {entry:.2f} stop {stop_d:.2f} exit {res[0]} gross {g:+.2f}  "
          f"script: {t.side:+d} {t.entry:.2f} {t.kind} {t.gross:+.2f}  {'MATCH' if ok else 'DIFF'}")
