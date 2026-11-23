"""Test Q run 01 on real data (hypothesis v1.1). Uses morning_star.py (a30c8f29, unchanged, noise-checked) for all
decisive numbers. Supplementary only: the non-chosen alternatives K1-B, K2-B, K3-B, K4-B (hypothesis 3, table
"Gemaakte keuzes"); these are reported, never used as a repair.

Periods (hypothesis 5): data from the usable start (3.2); the first 200 H1 bars do not count (warm-up).
  P1 decisive: H1 bars starting 6 Nov 2021 to the last bar. P0 supplementary: usable start to 5 Nov 2021.
  P3: per year, descriptive.
Usage: python run_real.py XAUUSD_M30_199804220000_202611052200.csv outdir
Order of reporting: controls first, then the rule.
"""
import sys, os
import numpy as np
import pandas as pd
from numba import njit
import morning_star as ms

P1_START = pd.Timestamp("2021-11-06")
WARM = 200


# ---------- supplementary variants (not decisive) ----------
def prepare_variant(d, ma="sma", pat="classic"):
    """Same as ms.prepare, with K1-B (EMA) or K2-B (loose pattern) as options."""
    P = ms.prepare(d)
    h1 = P["h1"]
    o, h, l, c = (h1[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    if ma == "ema":
        s14 = pd.Series(c).ewm(span=14, adjust=False).mean().to_numpy()
        s200 = pd.Series(c).ewm(span=200, adjust=False).mean().to_numpy().copy()
        s200[:199] = np.nan           # same warm-up as the SMA
    else:
        s14, s200 = ms.sma(c, 14), ms.sma(c, 200)
    trend = np.zeros(len(c), np.int8)
    ok = ~np.isnan(s200)
    trend[ok & (c > s14) & (c > s200)] = 1
    trend[ok & (c < s14) & (c < s200)] = -1
    if pat == "loose":
        b = np.abs(c - o); pt = np.zeros(len(c), np.int8)
        o2, c2, b2 = o[:-2], c[:-2], b[:-2]; b1, o1 = b[1:-1], o[1:-1]; o0, c0 = o[2:], c[2:]
        msk = (c2 < o2) & (b1 < b2) & (c0 > o0) & (c0 > o1)
        esk = (c2 > o2) & (b1 < b2) & (c0 < o0) & (c0 < o1)
        pt[2:][msk] = 1; pt[2:][esk] = -1
    else:
        pt = ms.pattern(o, h, l, c)
    sig = np.where(pt == trend, pt, 0).astype(np.int8)
    sig[~ok] = 0
    P.update(trend=trend, pat=pt, sig=sig)
    return P


@njit
def fill_k3b(o, h, l, i0, i1, lvl, stop, dirn):
    """K3-B: stop order valid up to 5 H1 bars, cancelled once the protective stop level is touched first.
    A bar that touches the stop level and the entry level counts as cancelled unless it opens beyond the entry."""
    for k in range(i0, i1 + 1):
        if dirn == 1:
            if o[k] >= lvl:
                return k, o[k]
            if l[k] <= stop:
                return -1, np.nan
            if h[k] >= lvl:
                return k, lvl
        else:
            if o[k] <= lvl:
                return k, o[k]
            if h[k] >= stop:
                return -1, np.nan
            if l[k] <= lvl:
                return k, lvl
    return -1, np.nan


def rule_trades_k3b(d, P, mask_h1):
    """Copy of ms.rule_trades with the K3-B order validity. Everything else identical."""
    h1 = P["h1"]
    o, hh, ll, cc = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    i0 = h1["i0"].to_numpy(); i1 = h1["i1"].to_numpy()
    H, L = h1["HIGH"].to_numpy(), h1["LOW"].to_numpy(); atr = h1["ATR"].to_numpy()
    n = len(h1)
    stats = dict(patterns=int(((P["pat"] != 0) & mask_h1).sum()), in_filter=0, busy=0, unfilled=0, dropped=0)
    rows = []; busy_until = -1
    for t in np.where(mask_h1 & (P["sig"] != 0))[0]:
        stats["in_filter"] += 1
        if t + 1 >= n:
            continue
        if i1[t] <= busy_until:
            stats["busy"] += 1
            continue
        dirn = int(P["sig"][t])
        lvl = H[t] if dirn == 1 else L[t]
        stop = L[t - 2:t + 1].min() if dirn == 1 else H[t - 2:t + 1].max()
        k0, entry = fill_k3b(o, hh, ll, i0[t + 1], i1[min(t + 5, n - 1)], lvl, stop, dirn)
        if k0 < 0:
            stats["unfilled"] += 1
            continue
        dist = (entry - stop) * dirn
        if dist < ms.MIN_STOP:
            stats["dropped"] += 1
            continue
        tgt = entry + dirn * ms.TGT_R * dist
        k, px, fin = ms.walk(o, hh, ll, cc, k0, entry, dirn, stop, tgt)
        rows.append((t, k0, k, dirn, entry, stop, tgt, dist, atr[t], px, (px - entry) * dirn, fin))
        busy_until = k
    tr = pd.DataFrame(rows, columns=["SIG_H1", "ENTRY_M30", "EXIT_M30", "DIR", "ENTRY", "STOP", "TARGET", "DIST",
                                     "ATR", "EXIT", "GROSS_USD", "FINISHED"])
    for cst in ms.COSTS:
        tr[f"R_{cst:.2f}"] = (tr["GROSS_USD"] - cst) / tr["DIST"]
    tr["R_NET"] = tr[f"R_{ms.COST:.2f}"]
    return tr, stats


@njit
def challenge_p1only(o, h, l, mday, t_k0, t_k1, t_dir, t_entry, t_dist, t_exit, start_day, horizon_day, cost):
    """K4-B: as ms.challenge, but passed once phase 1 (10%) is reached with at least 4 trading days."""
    bal = 100000.0; daystart = 100000.0; cur_day = -1; ndays = 0; last_entry_day = -1
    for j in range(len(t_k0)):
        k0 = t_k0[j]; k1 = t_k1[j]
        eday = mday[k0]
        if eday < start_day:
            continue
        if eday > horizon_day:
            return 0, eday, -1
        size = 1000.0 / t_dist[j]; c = size * cost
        for k in range(k0, k1 + 1):
            if mday[k] != cur_day:
                cur_day = mday[k]; daystart = bal
            if k == k0 and eday != last_entry_day:
                ndays += 1; last_entry_day = eday
            if t_dir[j] == 1:
                adv = l[k]
                if k == k1 and t_exit[j] < t_entry[j]:
                    adv = t_exit[j]
            else:
                adv = h[k]
                if k == k1 and t_exit[j] > t_entry[j]:
                    adv = t_exit[j]
            eq = bal + size * (adv - t_entry[j]) * t_dir[j] - c
            if eq <= daystart - 5000.0 or eq <= 90000.0:
                return -1, mday[k], -1
        bal += size * (t_exit[j] - t_entry[j]) * t_dir[j] - c
        if bal >= 110000.0 and ndays >= 4:
            return 1, mday[k1], mday[k1]
    return 0, -1, -1


# ---------- reporting ----------
def line(o):
    return (f"trades {o['n']}, win {100*o['win']:.1f}% ({100*o['wil'][0]:.1f}-{100*o['wil'][1]:.1f}), mean {o['mean']:+.3f}R "
            f"({o['boot'][0]:+.3f} to {o['boot'][1]:+.3f}), PF {o['pf']:.2f}, pct Null A {o['pctA']:.1f}, pct Null B {o['pctB']:.1f}")


def report_controls_first(o):
    print(f"\n== {o['label']}")
    print("  CONTROLS (looked at first)")
    print(f"  Null A 5/50/95 {o['nullA'][0]:+.3f} / {o['nullA'][1]:+.3f} / {o['nullA'][2]:+.3f} R per trade (null trades median {o['cntA']:.0f})")
    print(f"  Null B 5/50/95 {o['nullB'][0]:+.3f} / {o['nullB'][1]:+.3f} / {o['nullB'][2]:+.3f} R per trade (null trades median {o['cntB']:.0f})")
    if "c5_pass" in o:
        print(f"  C5 Null A trades in the same challenge (2,000 runs): passed {100*o['c5_pass']:.1f}%, failed {100*o['c5_fail']:.1f}%, "
              f"not finished {100*o['c5_open']:.1f}%")
    print("  RULE")
    ms.report(o)


def per_year(t, label):
    print(f"\n== P3 per year ({label}), by entry year")
    y = pd.to_datetime(t["ENTRY_TIME"]).dt.year
    for yy, g in t.groupby(y):
        r = g["R_NET"].to_numpy()
        print(f"  {yy}: trades {len(g):4d}, win {100*(r>0).mean():5.1f}%, mean {r.mean():+.3f}R, sum {r.sum():+.1f}R")


def main(path, outdir):
    os.makedirs(outdir, exist_ok=True)
    d = ms.load(path)
    st = ms.usable_start(d)
    d = d[d["TIME"] >= st].reset_index(drop=True)
    print(f"data {path}\nusable start {st.date()}, M30 rows used {len(d)}, last bar {d['TIME'].iloc[-1]}")
    P = ms.prepare(d)
    h1 = P["h1"]; n = len(h1)
    warm = np.arange(n) >= WARM
    s = h1["START"]
    m1 = warm & (s >= P1_START).to_numpy()
    m0 = warm & (s < P1_START).to_numpy()
    print(f"H1 bars {n}; warm-up ends at {s.iloc[WARM]}; P0 H1 bars {int(m0.sum())} ({s[m0].iloc[0]} to {s[m0].iloc[-1]}); "
          f"P1 H1 bars {int(m1.sum())} ({s[m1].iloc[0]} to {s[m1].iloc[-1]})")
    # equality check of the variant builder with the decisive builder
    Pv = prepare_variant(d)
    assert (Pv["sig"] == P["sig"]).all() and (Pv["trend"] == P["trend"]).all()

    print("\n######## DECISIVE: P1 (hypothesis v1.1, K1-A K2-A K3-A K4-A) ########")
    o1 = ms.evaluate(d, P, m1, np.random.default_rng(ms.SEED), label="P1 decisive", verbose=False, prop=True)
    report_controls_first(o1)
    o1["trades"].to_csv(os.path.join(outdir, "trades_p1.csv"), index=False)
    per_year(o1["trades"], "P1")

    print("\n######## SUPPLEMENTARY: P0 (usable start to 5 Nov 2021) ########")
    o0 = ms.evaluate(d, P, m0, np.random.default_rng(ms.SEED), label="P0 supplementary", verbose=False)
    report_controls_first(o0)
    o0["trades"].to_csv(os.path.join(outdir, "trades_p0.csv"), index=False)
    per_year(o0["trades"], "P0")

    print("\n######## VERDICT P1 (hypothesis 7) ########")
    c1 = o1["boot"][1] < 0
    c2 = not (o1["pctA"] > 95)
    c4 = o1["ch_wil"][1] < 0.81
    enough = o1["n"] >= 100
    print(f"  trades {o1['n']} -> {'enough (>=100)' if enough else 'INSUFFICIENT'}")
    print(f"  C1 mean net R {o1['mean']:+.3f}, 95% upper {o1['boot'][1]:+.3f} -> {'FALSIFIED' if c1 else 'not falsified'}")
    print(f"  C2 percentile vs Null A {o1['pctA']:.1f} (needs > 95) -> {'FALSIFIED' if c2 else 'not falsified'}")
    print(f"  C3 descriptive: {o1['n']} trades vs 512, win {100*o1['win']:.1f}% vs 43%, max drawdown {o1['dd_pct']:.1f}% vs 7.5%, "
          f"worst day {o1['worst_day_pct']:+.2f}% vs -3.6%, longest winning run {o1['wstreak']} vs 7")
    print(f"  C4 pass rate {100*o1['ch_pass']:.1f}% (95% {100*o1['ch_wil'][0]:.1f} to {100*o1['ch_wil'][1]:.1f}), needs upper >= 81% -> "
          f"{'FALSIFIED' if c4 else 'not falsified'}; failed {100*o1['ch_fail']:.1f}% vs about 12.5% (1 in 8), median days {o1['ch_med_days']:.0f} vs 155")
    print(f"  C5 descriptive: Null A trades pass {100*o1['c5_pass']:.1f}%")

    print("\n######## SUPPLEMENTARY: non-chosen alternatives on P1 (not a repair, hypothesis 3 and 7) ########")
    for lab, Pk in (("K1-B EMA 14 / EMA 200", prepare_variant(d, ma="ema")),
                    ("K2-B loose pattern", prepare_variant(d, pat="loose"))):
        ok = ms.evaluate(d, Pk, m1, np.random.default_rng(ms.SEED), label=lab, verbose=False)
        print(f"  {lab}: " + line(ok))
    orig = ms.rule_trades
    ms.rule_trades = rule_trades_k3b
    try:
        ok = ms.evaluate(d, P, m1, np.random.default_rng(ms.SEED), label="K3-B", verbose=False)
        print(f"  K3-B order valid up to 5 H1 bars: " + line(ok))
    finally:
        ms.rule_trades = orig
    origc = ms.challenge
    ms.challenge = challenge_p1only
    try:
        ok = ms.evaluate(d, P, m1, np.random.default_rng(ms.SEED), label="K4-B", verbose=False, prop=True)
        print(f"  K4-B phase 1 only: passed {100*ok['ch_pass']:.1f}% (95% {100*ok['ch_wil'][0]:.1f} to {100*ok['ch_wil'][1]:.1f}), "
              f"failed {100*ok['ch_fail']:.1f}%, not finished {100*ok['ch_open']:.1f}%, median days {ok['ch_med_days']:.0f}; "
              f"Null A trades {100*ok['c5_pass']:.1f}%")
    finally:
        ms.challenge = origc
    print("\n(spread column: see datacheck.txt; costs used 0.40 USD per ounce round trip)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
