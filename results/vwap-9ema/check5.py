#!/usr/bin/env python3
"""check5.py · test N · five random trades recomputed independently with pandas resampling
(own 3-minute candles, own VWAP, own EMA9 via ewm). Only the opening minute per day comes from
vwap_control.detect_open."""
import os, sys, importlib.util
import numpy as np, pandas as pd
spec = importlib.util.spec_from_file_location("v", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vwap-9ema", "vwap_control.py")); v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
csv, trades = sys.argv[1], sys.argv[2]
m1 = v.load_mt5(csv)
days = v.build_days(m1, 0.01)
valid = {}
for d in days:
    b = v.make_bars(d)
    if b is not None:
        valid[d["day"]] = b["k_open"]
rows = []
for day, k in valid.items():
    t0 = day + pd.Timedelta(minutes=int(k))
    seg = m1.loc[t0:t0 + pd.Timedelta(minutes=389)]
    g = seg.resample("3min", origin=t0)
    c3 = pd.DataFrame({"O": g["open"].first(), "C": g["close"].last()})
    px = (seg["open"] + seg["high"] + seg["low"] + seg["close"]) / 4
    vw = ((px * seg["vol"]).cumsum() / seg["vol"].cumsum()).resample("3min", origin=t0).last()
    c3["VW"] = vw
    c3["day"] = day
    c3["bar"] = range(len(c3))
    c3["spread_first"] = seg["spread"].resample("3min", origin=t0).first() * 0.01
    rows.append(c3)
allb = pd.concat(rows)
allb["E"] = allb["C"].ewm(span=9, adjust=False).mean()
tr = pd.read_csv(trades, parse_dates=["day"])
pick = tr.sample(5, random_state=11)
ok = 0
for _, t in pick.iterrows():
    f = allb[allb["day"] == t["day"]].set_index("bar")
    s = int(t["side"]); e = int(t["entry_bar"]); x = int(t["exit_bar"])
    sig = (f.at[e-1, "E"] > f.at[e-1, "VW"] and f.at[e-2, "E"] <= f.at[e-2, "VW"]) if s > 0 else \
          (f.at[e-1, "E"] < f.at[e-1, "VW"] and f.at[e-2, "E"] >= f.at[e-2, "VW"])
    entry_ok = abs(f.at[e, "O"] - t["entry"]) < 1e-9
    if x == 129 and t["why"] == "eod":
        exit_ok = abs(f.at[x, "C"] - t["exit"]) < 1e-9
    else:
        exit_ok = abs(f.at[x + 1, "O"] - t["exit"]) < 1e-9
    held = all(not ((s > 0 and f.at[k, "C"] < f.at[k, "E"]) or (s < 0 and f.at[k, "C"] > f.at[k, "E"])) for k in range(e, x))
    trig = t["why"] != "ema" or ((s > 0 and f.at[x, "C"] < f.at[x, "E"]) or (s < 0 and f.at[x, "C"] > f.at[x, "E"]))
    good = sig and entry_ok and exit_ok and held and trig
    ok += good
    print(f"{t['day'].date()} side {s:+d} candles {e}-{x} ({t['why']}): signal {sig}, entry {t['entry']:.2f} {entry_ok}, "
          f"exit {t['exit']:.2f} {exit_ok}, no earlier exit {held}, exit trigger {trig}, gross {t['gross']:+.2f} -> {'OK' if good else 'DIFFERENT'}")
print(f"{ok} of 5 equal")
