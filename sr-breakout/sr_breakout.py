"""Test P: breakout of support and resistance on gold (XAUUSD), intraday, both directions.

Hypothesis v1.0 (20 Nov 2026), fixed before looking at price data. Rules:
  data      : MT5 M30 export, broker time. H1, H4 and D1 bars built from M30 (broker hour, 4-hour block
              from midnight, broker date). The trade path is walked on M30.
  ATR       : Wilder ATR(14) on H1, value of the closed bar.
  levels    : 5-bar fractals on H4 and on D1. Resistance = high of bar j strictly above the highs of the two
              bars before and the two after; support mirrored on lows. Active from the first H1 bar that
              starts after bar j+2 has closed. A level expires at its first breakout (used, also during an
              open trade) or after 20 trading days.
  signal    : H1 bar t. Long if close(t) > resistance and close(t-1) <= resistance; short mirrored on support.
              Several levels in one direction count once; the stop uses the level nearest to the close.
              Resistance and support broken in the same bar: no trade. No signal on the last H1 bar of the
              broker day. No time filter (09:00-21:00 broker time reported as a supplement).
  entry     : close of H1 bar t. Stop just back inside the level: long level - 0.5 ATR, short level + 0.5 ATR.
              No trade if the stop distance is below 1.00 USD.
  exit      : no target. Trailing stop: A = ATR at t, fixed. After the close of every M30 bar from the entry
              bar on, long stop = max(stop, highest M30 close since entry - 2A), short mirrored. The new stop
              applies from the next M30 bar. A bar that opens beyond the stop exits at its open. At the latest
              exit on the close of the last M30 bar of the broker day.
  costs     : 0.40 USD per ounce round trip (sensitivity 0 and 0.80). R = net USD / initial stop distance.
  one position at a time.
Controls: a random process that walks through time like the rule, one position at a time. After each exit
  (or the start) a wait in H1 bars drawn from the rule's own waits, then entry on the close of the next H1
  bar that is not the last of the broker day. Stop distance drawn as a multiple of ATR from the rule's own
  stops (20 quantiles), applied with the ATR on the control's entry bar; below 1.00 USD no trade. Same
  trailing stop, day close, costs and path rules.
  Null A (decisive): long with probability p = share of long trades of the rule in the same period.
  Null B (supplement): coin flip, 50/50.
Usage: python sr_breakout.py data.csv           real data
       python sr_breakout.py --synthetic 24 [sub] noise check (sub = price steps per M30 bar, default 60)
"""
import sys
import numpy as np
import pandas as pd
from numba import njit

COST, COSTS = 0.40, (0.0, 0.40, 0.80)
MIN_STOP, BUF, TRAIL, ATR_N, EXPIRE_DAYS = 1.00, 0.5, 2.0, 14, 20
RUNS, SEED, K = 10000, 23, 20


# ---------- data ----------
def load(path):
    d = pd.read_csv(path, sep="\t")
    d.columns = [c.strip("<>").upper() for c in d.columns]
    d["TIME"] = pd.to_datetime(d["DATE"] + " " + d["TIME"], format="%Y.%m.%d %H:%M:%S")
    return d[["TIME", "OPEN", "HIGH", "LOW", "CLOSE", "SPREAD"]].sort_values("TIME").reset_index(drop=True)


def usable_start(d, min_bars=40):
    """First calendar month in which every trading day has at least min_bars M30 bars (same as test F)."""
    per_day = d.groupby(d["TIME"].dt.date).size()
    per_day.index = pd.to_datetime(per_day.index)
    ok = per_day.groupby(per_day.index.to_period("M")).min() >= min_bars
    return ok[ok].index[0].to_timestamp()


def bars(d, key):
    """Aggregate M30 rows into bars by key. Returns dataframe with first/last M30 index, OHLC, start, end."""
    g = d.assign(IDX=np.arange(len(d))).groupby(key, sort=False)
    out = pd.DataFrame({
        "i0": g["IDX"].first(), "i1": g["IDX"].last(),
        "OPEN": g["OPEN"].first(), "HIGH": g["HIGH"].max(), "LOW": g["LOW"].min(), "CLOSE": g["CLOSE"].last(),
        "START": g["TIME"].first(), "END": g["TIME"].last() + pd.Timedelta(minutes=30)}).reset_index(drop=True)
    return out


def wilder_atr(h, l, c, n=ATR_N):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr = np.full(len(c), np.nan)
    if len(c) > n:
        atr[n - 1] = tr[:n].mean()
        for i in range(n, len(c)):
            atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
    return atr


def fractal_levels(b, kind):
    """Return (price, activation time) for 5-bar fractal highs or lows of bar frame b."""
    x = b["HIGH" if kind == "res" else "LOW"].to_numpy()
    n = len(x); out = []
    for j in range(2, n - 2):
        if kind == "res":
            ok = x[j] > x[j - 1] and x[j] > x[j - 2] and x[j] > x[j + 1] and x[j] > x[j + 2]
        else:
            ok = x[j] < x[j - 1] and x[j] < x[j - 2] and x[j] < x[j + 1] and x[j] < x[j + 2]
        if ok:
            out.append((x[j], b["END"].iloc[j + 2]))
    return out


def prepare(d):
    """Build H1 frame, levels, signals and per-H1 metadata."""
    t = d["TIME"]
    date = t.dt.normalize()
    h1 = bars(d, [date, t.dt.hour])
    h4 = bars(d, [date, t.dt.hour // 4])
    d1 = bars(d, date)
    h1["DATE"] = h1["START"].dt.normalize()
    dates = np.sort(h1["DATE"].unique())
    h1["DIDX"] = np.searchsorted(dates, h1["DATE"].to_numpy())
    h1["LASTOFDAY"] = h1["DIDX"].ne(h1["DIDX"].shift(-1)).to_numpy()
    h1["ATR"] = wilder_atr(h1["HIGH"].to_numpy(), h1["LOW"].to_numpy(), h1["CLOSE"].to_numpy())
    # levels with activation index (first H1 bar starting at or after activation time)
    starts = h1["START"].to_numpy()
    levels = []
    for frame in (h4, d1):
        for kind, sgn in (("res", 1), ("sup", -1)):
            for px, act in fractal_levels(frame, kind):
                ai = int(np.searchsorted(starts, np.datetime64(act), side="left"))
                if ai < len(h1):
                    levels.append((ai, sgn, px))
    levels.sort()
    close = h1["CLOSE"].to_numpy(); didx = h1["DIDX"].to_numpy()
    n = len(h1)
    sig_dir = np.zeros(n, np.int8); sig_lvl = np.full(n, np.nan); conflict = 0
    act_res, act_sup = [], []     # lists of [price, expire_didx]
    li = 0
    for i in range(1, n):
        while li < len(levels) and levels[li][0] <= i:
            ai, sgn, px = levels[li]
            (act_res if sgn == 1 else act_sup).append([px, didx[ai] + EXPIRE_DAYS])
            li += 1
        act_res = [v for v in act_res if didx[i] < v[1]]
        act_sup = [v for v in act_sup if didx[i] < v[1]]
        up = [v[0] for v in act_res if close[i] > v[0] and close[i - 1] <= v[0]]
        dn = [v[0] for v in act_sup if close[i] < v[0] and close[i - 1] >= v[0]]
        if up:
            act_res = [v for v in act_res if not (close[i] > v[0] and close[i - 1] <= v[0])]
        if dn:
            act_sup = [v for v in act_sup if not (close[i] < v[0] and close[i - 1] >= v[0])]
        if up and dn:
            conflict += 1
            continue
        if up:
            sig_dir[i] = 1; sig_lvl[i] = max(up)
        elif dn:
            sig_dir[i] = -1; sig_lvl[i] = min(dn)
    sig_dir[h1["LASTOFDAY"].to_numpy()] = 0
    sig_dir[np.isnan(h1["ATR"].to_numpy())] = 0
    # last M30 index of each broker day, per H1 bar
    day_last = d.assign(IDX=np.arange(len(d))).groupby(date, sort=False)["IDX"].last().to_numpy()
    h1_daylast = day_last[didx]
    m30_h1 = np.zeros(len(d), np.int64)
    for k, (a, b_) in enumerate(zip(h1["i0"].to_numpy(), h1["i1"].to_numpy())):
        m30_h1[a:b_ + 1] = k
    return dict(h1=h1, sig_dir=sig_dir, sig_lvl=sig_lvl, conflict=conflict, h1_daylast=h1_daylast,
                m30_h1=m30_h1, nlevels=len(levels))


# ---------- path ----------
@njit
def walk(o, h, l, c, i_entry_m30, i_last_m30, entry, dirn, stop0, A):
    """Trailing-stop path on M30. Returns (exit index, exit price)."""
    stop = stop0
    ext = entry
    # update after the close of the entry bar itself
    if dirn == 1:
        stop = max(stop, ext - TRAIL * A)
    else:
        stop = min(stop, ext + TRAIL * A)
    for k in range(i_entry_m30 + 1, i_last_m30 + 1):
        if dirn == 1:
            if o[k] <= stop:
                return k, o[k]
            if l[k] <= stop:
                return k, stop
            if c[k] > ext:
                ext = c[k]
            stop = max(stop, ext - TRAIL * A)
        else:
            if o[k] >= stop:
                return k, o[k]
            if h[k] >= stop:
                return k, stop
            if c[k] < ext:
                ext = c[k]
            stop = min(stop, ext + TRAIL * A)
    return i_last_m30, c[i_last_m30]


@njit
def null_table(o, h, l, c, elig, i1, daylast, close_h1, atr, mults, cost, min_stop):
    """Outcome of a control trade from every eligible H1 bar, both directions, every stop multiple."""
    nq = len(mults); n = len(close_h1)
    EX = np.full((2, nq, n), -1, np.int64); RN = np.full((2, nq, n), np.nan)
    for e in range(n):
        if not elig[e]:
            continue
        entry = close_h1[e]
        for q in range(nq):
            dist = mults[q] * atr[e]
            if dist < min_stop:
                continue
            for di in range(2):
                dirn = 1 if di == 0 else -1
                stop0 = entry - dirn * dist
                k, px = walk(o, h, l, c, i1[e], daylast[e], entry, dirn, stop0, atr[e])
                EX[di, q, e] = k
                RN[di, q, e] = ((px - entry) * dirn - cost) / dist
    return EX, RN


@njit
def run_null(EX, RN, m30_h1, elig_idx, start_ptr, end_h1, waits, p_long, runs, seed, rule_streak):
    np.random.seed(seed)
    nq = EX.shape[1]
    means = np.empty(runs); counts = np.empty(runs, np.int64); shorter = 0
    for t in range(runs):
        ptr = start_ptr; s = 0.0; cnt = 0; streak = 0; mx = 0; skipped = False
        while True:
            w = waits[np.random.randint(0, len(waits))]
            if skipped and w < 1:
                w = 1
            want = ptr + w
            skipped = False
            k = np.searchsorted(elig_idx, want)
            if k >= len(elig_idx):
                break
            e = elig_idx[k]
            if e > end_h1:
                break
            q = np.random.randint(0, nq)
            di = 0 if np.random.random() < p_long else 1
            if EX[di, q, e] < 0:          # stop below minimum: no trade, wait again from here
                ptr = e
                skipped = True
                continue
            r = RN[di, q, e]
            s += r; cnt += 1
            if r <= 0:
                streak += 1
                if streak > mx:
                    mx = streak
            else:
                streak = 0
            ptr = m30_h1[EX[di, q, e]]
        means[t] = s / cnt if cnt > 0 else np.nan
        counts[t] = cnt
        if mx <= rule_streak:
            shorter += 1
    return means, counts, shorter


# ---------- statistics ----------
def pct(x, dist):
    dist = dist[~np.isnan(dist)]
    return 100.0 * (np.sum(dist < x) + 0.5 * np.sum(dist == x)) / len(dist)


def wilson(k, n, z=1.96):
    p = k / n; dd = 1 + z * z / n; mid = (p + z * z / (2 * n)) / dd
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return mid - hw, mid + hw


def day_boot(r, days, rng, B=10000):
    groups = [r[days == u] for u in np.unique(days)]
    k = len(groups); out = np.empty(B)
    for b in range(B):
        out[b] = np.concatenate([groups[j] for j in rng.integers(0, k, k)]).mean()
    return np.percentile(out, [2.5, 97.5])


def max_streak(r):
    s = m = 0
    for x in r:
        s = s + 1 if x <= 0 else 0; m = max(m, s)
    return m


# ---------- evaluation ----------
def rule_trades(d, P, mask_h1, hour_filter=False):
    """Walk the rule through the H1 bars in mask_h1, one position at a time."""
    h1 = P["h1"]; o, hh, ll, cc = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    i1 = h1["i1"].to_numpy(); close = h1["CLOSE"].to_numpy(); atr = h1["ATR"].to_numpy()
    hours = h1["START"].dt.hour.to_numpy()
    rows = []; busy_until = -1; signals = dropped = 0
    for i in np.where(mask_h1 & (P["sig_dir"] != 0))[0]:
        if hour_filter and not (9 <= hours[i] <= 20):
            continue
        signals += 1
        if i1[i] <= busy_until:
            continue
        dirn = int(P["sig_dir"][i]); lvl = P["sig_lvl"][i]; A = atr[i]; entry = close[i]
        stop0 = lvl - dirn * BUF * A
        dist = (entry - stop0) * dirn
        if dist < MIN_STOP:
            dropped += 1
            continue
        k, px = walk(o, hh, ll, cc, i1[i], P["h1_daylast"][i], entry, dirn, stop0, A)
        gross = (px - entry) * dirn
        rows.append((i, k, dirn, entry, stop0, dist, A, px, gross))
        busy_until = k
    t = pd.DataFrame(rows, columns=["H1", "EXIT_M30", "DIR", "ENTRY", "STOP0", "DIST", "ATR", "EXIT", "GROSS_USD"])
    for cst in COSTS:
        t[f"R_{cst:.2f}"] = (t["GROSS_USD"] - cst) / t["DIST"]
    t["R_NET"] = t[f"R_{COST:.2f}"]
    return t, signals, dropped


def evaluate(d, P, mask_h1, rng, runs=RUNS, label="", verbose=True, hour_filter=False, seed=SEED):
    h1 = P["h1"]
    t, signals, dropped = rule_trades(d, P, mask_h1, hour_filter)
    out = dict(label=label, signals=signals, dropped=dropped, n=len(t))
    if len(t) < 2:
        if verbose:
            print(f"\n== {label}: {len(t)} trades")
        return out
    r = t["R_NET"].to_numpy()
    wins = int((r > 0).sum())
    out.update(win=wins / len(t), wil=wilson(wins, len(t)), mean=r.mean(), long_share=float((t["DIR"] == 1).mean()),
               pf=r[r > 0].sum() / -r[r < 0].sum(), cost_means={c: t[f"R_{c:.2f}"].mean() for c in COSTS},
               med_dist=float(t["DIST"].median()), med_mult=float((t["DIST"] / t["ATR"]).median()),
               streak=max_streak(r))
    days = h1["DIDX"].to_numpy()[t["H1"].to_numpy()]
    out["boot"] = day_boot(r, days, rng)
    # controls
    o, hh, ll, cc = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    i1 = h1["i1"].to_numpy(); close = h1["CLOSE"].to_numpy(); atr = h1["ATR"].to_numpy()
    hours = h1["START"].dt.hour.to_numpy()
    elig = mask_h1 & ~h1["LASTOFDAY"].to_numpy() & ~np.isnan(atr)
    if hour_filter:
        elig &= (hours >= 9) & (hours <= 20)
    mults = np.quantile((t["DIST"] / t["ATR"]).to_numpy(), (np.arange(K) + 0.5) / K)
    EX, RN = null_table(o, hh, ll, cc, elig, i1, P["h1_daylast"], close, atr, mults, COST, MIN_STOP)
    m30_h1 = P["m30_h1"]
    exit_h1 = m30_h1[t["EXIT_M30"].to_numpy()]
    start_ptr = int(np.where(mask_h1)[0][0]) - 1; end_h1 = int(np.where(mask_h1)[0][-1])
    prev = np.concatenate([[start_ptr], exit_h1[:-1]])
    waits = (t["H1"].to_numpy() - prev).astype(np.int64)
    elig_idx = np.where(elig)[0].astype(np.int64)
    res = {}
    for name, p in (("A", out["long_share"]), ("B", 0.5)):
        m, cnt, sh = run_null(EX, RN, m30_h1, elig_idx, start_ptr, end_h1, waits, p, runs, seed, out["streak"])
        res[name] = (m, cnt, sh)
    out.update(pctA=pct(r.mean(), res["A"][0]), pctB=pct(r.mean(), res["B"][0]),
               nullA=np.nanpercentile(res["A"][0], [5, 50, 95]), nullB=np.nanpercentile(res["B"][0], [5, 50, 95]),
               cntA=float(np.median(res["A"][1])), cntB=float(np.median(res["B"][1])),
               streak_null_share=res["A"][2] / runs)
    srt = np.sort(r)[::-1]; top = max(1, int(round(0.05 * len(r))))
    out.update(top5=srt[:top].sum(), total=r.sum())
    tt = t.copy()
    tt.insert(0, "ENTRY_TIME", h1["END"].to_numpy()[t["H1"].to_numpy()])
    tt.insert(1, "EXIT_TIME", d["TIME"].to_numpy()[t["EXIT_M30"].to_numpy()] + np.timedelta64(30, "m"))
    out["trades"] = tt
    if verbose:
        report(out)
    return out


def report(o):
    print(f"\n== {o['label']}")
    print(f"  signals {o['signals']}, dropped by min stop {o['dropped']}, trades {o['n']}{'  INSUFFICIENT (<100)' if o['n'] < 100 else ''}, long share {100*o['long_share']:.1f}%")
    print(f"  win rate (net R > 0) {100*o['win']:.1f}%  (95% {100*o['wil'][0]:.1f} to {100*o['wil'][1]:.1f})")
    print(f"  mean net R {o['mean']:+.3f}  (day bootstrap 95% {o['boot'][0]:+.3f} to {o['boot'][1]:+.3f})   PF {o['pf']:.2f}")
    print("  costs 0 / 0.40 / 0.80 USD: " + " / ".join(f"{v:+.3f}" for v in o["cost_means"].values())
          + f"   median stop {o['med_dist']:.2f} USD ({o['med_mult']:.2f} ATR)")
    print(f"  Null A 5/50/95 {o['nullA'][0]:+.3f} / {o['nullA'][1]:+.3f} / {o['nullA'][2]:+.3f} -> percentile {o['pctA']:.1f} (null trades median {o['cntA']:.0f})")
    print(f"  Null B 5/50/95 {o['nullB'][0]:+.3f} / {o['nullB'][1]:+.3f} / {o['nullB'][2]:+.3f} -> percentile {o['pctB']:.1f} (null trades median {o['cntB']:.0f})")
    print(f"  best 5% of trades {o['top5']:+.1f}R of total {o['total']:+.1f}R")
    print(f"  longest losing streak {o['streak']}; Null A runs with an equal or shorter longest streak: {100*o['streak_null_share']:.1f}%")


def synthetic(nsets, seed=7, runs=1000, sub=60):
    rng = np.random.default_rng(seed)
    pcts = []
    for s in range(nsets):
        drift = 0.0 if s % 2 == 0 else 0.08
        days = pd.bdate_range("2014-01-01", periods=260 * 10)
        times = (days.values[:, None] + (np.arange(48) * np.timedelta64(30, "m"))[None, :]).ravel()
        nb = len(times)
        sig = 0.15 / np.sqrt(260 * 48 * sub); mu = drift / (260 * 48 * sub)
        steps = rng.normal(mu - sig ** 2 / 2, sig, nb * sub)
        p = 1000 * np.exp(np.cumsum(steps)).reshape(nb, sub)
        op = np.concatenate([[1000], p[:-1, -1]])
        d = pd.DataFrame({"TIME": pd.to_datetime(times), "OPEN": op, "HIGH": np.maximum(p.max(1), op),
                          "LOW": np.minimum(p.min(1), op), "CLOSE": p[:, -1], "SPREAD": 0})
        del p, steps
        P = prepare(d)
        mask = np.zeros(len(P["h1"]), bool); mask[1000:] = True
        o = evaluate(d, P, mask, np.random.default_rng(SEED + s), runs=runs, verbose=False, label=f"set {s}", seed=SEED + s)
        pcts.append(o.get("pctA", np.nan))
        print(f"set {s:2d} drift {drift:.2f}: trades {o['n']:5d} (Null A median {o.get('cntA', 0):.0f})  long {100*o.get('long_share', np.nan):5.1f}%  "
              f"win {100*o.get('win', np.nan):5.1f}%  mean {o.get('mean', np.nan):+.3f}R  pct vs Null A {o.get('pctA', np.nan):5.1f}  vs Null B {o.get('pctB', np.nan):5.1f}", flush=True)
    pcts = np.array(pcts)
    print(f"\nmean percentile vs Null A {np.nanmean(pcts):.1f}; above 95: {int(np.sum(pcts > 95))} of {nsets}; below 5: {int(np.sum(pcts < 5))}")


if __name__ == "__main__":
    if sys.argv[1] == "--synthetic":
        synthetic(int(sys.argv[2]), sub=int(sys.argv[3]) if len(sys.argv) > 3 else 60)
        sys.exit()
    d = load(sys.argv[1])
    start = usable_start(d)
    print(f"M30 bars {len(d)}, first {d['TIME'].iloc[0]}, last {d['TIME'].iloc[-1]}, usable from {start.date()}")
    d = d[d["TIME"] >= start].reset_index(drop=True)
    P = prepare(d)
    h1 = P["h1"]
    print(f"H1 bars {len(h1)}, levels {P['nlevels']}, raw signals {int((P['sig_dir'] != 0).sum())}, conflicts {P['conflict']}")
    print(f"median spread column (points): {d['SPREAD'].median():.0f}")
    warm = (h1["DIDX"] >= 30).to_numpy()
    st = h1["START"]
    P1 = warm & (st < "2025-01-01").to_numpy()
    P2 = warm & (st >= "2025-01-01").to_numpy()
    rng = np.random.default_rng(SEED)
    res = {}
    for name, m in (("P1 decisive (start to 2024)", P1), ("P2 supplement (2025 to end)", P2)):
        res[name] = evaluate(d, P, m, rng, label=name)
    evaluate(d, P, P1, rng, label="P1 supplement: time filter 09:00-21:00 broker time", hour_filter=True)
    res["P1 decisive (start to 2024)"]["trades"].to_csv("trades_P1.csv", index=False)
    res["P2 supplement (2025 to end)"]["trades"].to_csv("trades_P2.csv", index=False)
    print("\n== P3 per year (rule only, no time filter)")
    allt = pd.concat([res[k]["trades"] for k in res]).sort_values("ENTRY_TIME")
    g = allt.groupby(pd.to_datetime(allt["ENTRY_TIME"]).dt.year)
    print(pd.DataFrame({"trades": g.size(), "long%": (g["DIR"].apply(lambda x: (x == 1).mean()) * 100).round(1),
                        "win%": (g["R_NET"].apply(lambda x: (x > 0).mean()) * 100).round(1),
                        "meanR": g["R_NET"].mean().round(3), "sumR": g["R_NET"].sum().round(1)}).to_string())
