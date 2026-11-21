"""Independent check: on days where the old detection chose 16:30, old and new trades must be identical.
All differences must sit on days the old detection moved (15:30 or 17:30)."""
import sys, pandas as pd, numpy as np
sys.argv = [sys.argv[0]] + sys.argv[1:]
exec(open("count_shift.py").read().split("path = sys.argv[1]")[0])
def shifted_days(path):
    m = load(path); out = {}
    for day, g in m.groupby("day"):
        out[pd.Timestamp(day).strftime("%Y-%m-%d")] = detect(g["min"].values, g["v"].values)
    return out
for data, test, f in [("us500.csv", "H_P1", "trades.csv"), ("ustec.csv", "G_P1", "trades.csv"),
                      ("ustec.csv", "O_rth", "trades_USTEC_rth_firm_a.csv"), ("us500.csv", "N_us500", "trades_US500.csv")]:
    sd = shifted_days(data)
    o = pd.read_csv(f"old/{test}/{f}"); n = pd.read_csv(f"new/{test}/{f}")
    dcol = "day" if "day" in o.columns else [c for c in o.columns if "date" in c or "day" in c][0]
    o["d"] = o[dcol].astype(str).str[:10]; n["d"] = n[dcol].astype(str).str[:10]
    keep = [c for c in o.columns if c in n.columns and c not in ("i",)]
    same_days = {d for d, off in sd.items() if off == 0}
    oa = o[o.d.isin(same_days)][keep].round(6).reset_index(drop=True); na = n[n.d.isin(same_days)][keep].round(6).reset_index(drop=True)
    eq = oa.shape == na.shape and (oa.astype(str).values == na.astype(str).values).all()
    print(f"{test}: col {dcol}; trades old {len(o)} new {len(n)}; on unshifted days old {len(oa)} new {len(na)} identical={eq}; "
          f"on shifted days old {(~o.d.isin(same_days)).sum()} new {(~n.d.isin(same_days)).sum()}")
print("--- where do differences on unshifted days sit?")
for data, test, f in [("ustec.csv", "O_rth", "trades_USTEC_rth_firm_a.csv"), ("us500.csv", "N_us500", "trades_US500.csv")]:
    sd = shifted_days(data); days = sorted(sd); prev = {days[i]: days[i-1] for i in range(1, len(days))}
    o = pd.read_csv(f"old/{test}/{f}"); n = pd.read_csv(f"new/{test}/{f}")
    keep = [c for c in o.columns if c != "i"]
    so = set(map(tuple, o[keep].round(6).astype(str).values)); sn = set(map(tuple, n[keep].round(6).astype(str).values))
    di = keep.index("day"); diff_days = {r[di][:10] for r in so ^ sn}
    uns = [d for d in diff_days if sd.get(d, 0) == 0]
    after = [d for d in uns if sd.get(prev.get(d), 0) != 0]
    print(f"{test}: days with a different trade {len(diff_days)}, of which unshifted {len(uns)}, of which the day after a shifted day {len(after)}")
