#!/usr/bin/env python3
"""
orb_control.py · Nullius Research
Measurement script for test H (5-minute opening range breakout).
Hypothesis: hypothese-orb-5min-v1.1.md (13 Nov 2026 evening). v1.0 (SHA-256 e927e873...) approved 13 Nov;
v1.1 changes only Null A (C3): both directions measured from the open of the bar after the breakout bar.
Script v1.0 SHA-256 207f6511... is kept in the meetlog.
Built on box_control.py (test G v1.1): same reading, opening detection and fake market.

Usage:
    python orb_control.py <US500_M1.csv> [--point 0.01] [--slip 0.25]
                          [--from 2019-01-01] [--to 2025-10-17] [--n 10000] [--seed 31]
                          [--nullb] [--out results_dir]
    python orb_control.py --noise [--sets 24] [--seed 7]      (noise check, section 7)

Input: MT5 M1 export, tab separated, <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE>
<TICKVOL> <VOL> <SPREAD>, server time.

All fixed choices come 1-to-1 from the hypothesis and are constants below.
Nothing here changes after the first run on real data.
"""
import argparse
import os

import numpy as np
import pandas as pd

# ------------------------------------------------------------ fixed choices (hypothesis section 4 and 6)
RTH_START = 16 * 60 + 30    # 9:30 New York in server time (NY + 7)
RTH_LEN = 390               # 9:30-16:00
RANGE_BARS = 5              # 9:30-9:35
LAST_ENTRY = 385            # no breakout before 15:55 -> no trade
MAX_RANGE_FRAC = 0.0055     # no trade if range > 0.55% of the opening price
SKIP_WEEKDAY = 1            # Tuesday (Monday = 0)
MAX_STOP_PTS = 14.0         # stop never further than 14 points from the entry
TGT_FRAC = 0.5              # target = breakout level +/- 0.5 range
NULLB_LAST = 360            # Null B: random entry minute 9:35-15:30
OPEN_OFFSETS = (-60, 0, 60)
MIN_SESSION_FRAC = 0.9
MIN_TRADES = 100
SLIP_MULT = (0, 1, 2)
NOISE_SUBSTEPS = 60
NOISE_DAYS = 1500
NOISE_SPREAD = 0.5          # fixed spread in the fake market (points)
NOISE_START = 4000.0        # [implementation choice] start price of the fake market
NOISE_VOL = 0.20            # [implementation choice] yearly volatility of the fake market


# ------------------------------------------------------------ reading
def load_mt5(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        head = f.readline()
    sep = "\t" if "\t" in head else (";" if ";" in head else ",")
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    raw = df["date"].astype(str) + " " + df["time"].astype(str)
    ts = pd.to_datetime(raw, format="%Y.%m.%d %H:%M:%S", errors="coerce")
    if ts.isna().mean() > 0.5:
        ts = pd.to_datetime(raw, format="%Y.%m.%d %H:%M", errors="coerce")
    out = pd.DataFrame({"open": df["open"].astype(float).values,
                        "high": df["high"].astype(float).values,
                        "low": df["low"].astype(float).values,
                        "close": df["close"].astype(float).values,
                        "vol": df["tickvol"].astype(float).values,
                        "spread": df["spread"].astype(float).values},
                       index=pd.DatetimeIndex(ts, name="ts"))
    out = out[~out.index.isna()]
    return out[~out.index.duplicated(keep="first")].sort_index()


def build_days(m1, point):
    days = []
    minute = (m1.index.hour * 60 + m1.index.minute).values
    date = m1.index.normalize()
    o, h, l, c = (m1[k].values for k in ("open", "high", "low", "close"))
    v, sp = m1["vol"].values, m1["spread"].values * point
    bounds = np.flatnonzero(np.r_[True, date[1:] != date[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        days.append({"day": date[a], "min": minute[a:b], "o": o[a:b], "h": h[a:b],
                     "l": l[a:b], "c": c[a:b], "v": v[a:b], "sp": sp[a:b]})
    return days


def detect_open(d):
    best, best_k = -np.inf, None
    vol = pd.Series(d["v"], index=d["min"])
    full = vol.reindex(range(0, 1440)).fillna(0).values
    for off in OPEN_OFFSETS:
        k = RTH_START + off
        if k - 15 < 0 or k + 15 > 1440:
            continue
        jump = full[k:k + 15].mean() - full[k - 15:k].mean()
        if jump > best:
            best, best_k = jump, k
    return best_k


# ------------------------------------------------------------ path (section 6, order)
def simulate(o, h, l, c, i0, side, stop, target, last):
    """Bar by bar. Entry bar: stop only. Later bar with stop and target: stop.
    Gap beyond the stop: exit at the open. Otherwise close of the last session bar."""
    if (side > 0 and l[i0] <= stop) or (side < 0 and h[i0] >= stop):
        return stop, i0, "stop"
    for i in range(i0 + 1, last + 1):
        if side > 0:
            if l[i] <= stop:
                return min(stop, o[i]), i, "stop"
            if h[i] >= target:
                return target, i, "target"
        else:
            if h[i] >= stop:
                return max(stop, o[i]), i, "stop"
            if l[i] <= target:
                return target, i, "target"
    return c[last], last, "close"


# ------------------------------------------------------------ the rule (section 4)
def session(d):
    k_open = detect_open(d)
    if k_open is None:
        return None
    m = d["min"]
    rth = (m >= k_open) & (m < k_open + RTH_LEN)
    if rth.sum() < MIN_SESSION_FRAC * RTH_LEN:
        return None
    idx = np.flatnonzero(rth)
    rng_idx = idx[m[idx] < k_open + RANGE_BARS]
    if len(rng_idx) < RANGE_BARS:
        return None
    return k_open, idx, rng_idx


FUNNEL_KEYS = ("days", "valid", "range_ok", "not_tuesday", "breakout", "both_sides", "trades",
               "entry_beyond_target")


def day_trade(d, fun):
    """At most one trade per day. Fills the funnel. Returns a dict or None."""
    s = session(d)
    if s is None:
        return None
    fun["valid"] += 1
    k_open, idx, rng_idx = s
    o, h, l, c, sp, m = d["o"], d["h"], d["l"], d["c"], d["sp"], d["min"]
    top, bot = h[rng_idx].max(), l[rng_idx].min()
    R = top - bot
    open_px = o[rng_idx[0]]
    if R <= 0 or R > MAX_RANGE_FRAC * open_px:
        return None
    fun["range_ok"] += 1
    if d["day"].dayofweek == SKIP_WEEKDAY:
        return None
    fun["not_tuesday"] += 1
    last = idx[-1]
    win = idx[(m[idx] >= k_open + RANGE_BARS) & (m[idx] < k_open + LAST_ENTRY)]
    for i in win:
        up, dn = h[i] > top, l[i] < bot
        if not (up or dn):
            continue
        fun["breakout"] += 1
        if up and dn:
            fun["both_sides"] += 1
            return None
        side = 1 if up else -1
        level = top if up else bot
        entry = max(level, o[i]) if up else min(level, o[i])
        # stop: other side of the range, never further than 14 points from the entry
        far = bot if up else top
        stop_d = min(abs(entry - far), MAX_STOP_PTS)
        target = level + side * TGT_FRAC * R
        tgt_d = (target - entry) * side
        if tgt_d <= 0:
            fun["entry_beyond_target"] += 1
        res = {}
        for s_ in (side, -side):
            stop = entry - s_ * stop_d
            tgt = entry + s_ * tgt_d
            px, j, kind = simulate(o, h, l, c, i, s_, stop, tgt, last)
            res[s_] = (s_ * (px - entry), j, kind)
        # v1.1 Null A (C3): both directions from the open of the next bar, same distances
        nx = {}
        if i + 1 <= last:
            e2 = o[i + 1]
            for s_ in (side, -side):
                px2, _, _ = simulate(o, h, l, c, i + 1, s_, e2 - s_ * stop_d, e2 + s_ * tgt_d, last)
                nx[s_] = s_ * (px2 - e2)
        fun["trades"] += 1
        g, j, kind = res[side]
        return {"day": d["day"], "i": int(i), "minute": int(m[i] - k_open), "side": side,
                "range": R, "entry": entry, "risk": stop_d, "tgt_d": tgt_d,
                "spread": float(sp[i]), "gross": g, "kind": kind, "exit_minute": int(m[j] - k_open),
                "gross_opp": res[-side][0], "kind_opp": res[-side][2],
                "nx_ok": bool(nx), "nx_spread": float(sp[i + 1]) if nx else np.nan,
                "nx_gross": nx.get(side, np.nan), "nx_gross_opp": nx.get(-side, np.nan)}
    return None


def run_rule(days, d_from=None, d_to=None):
    fun = {k: 0 for k in FUNNEL_KEYS}
    trades = []
    for d in days:
        if d_from is not None and d["day"] < d_from:
            continue
        if d_to is not None and d["day"] > d_to:
            continue
        fun["days"] += 1
        t = day_trade(d, fun)
        if t is not None:
            trades.append(t)
    return pd.DataFrame(trades), fun


# ------------------------------------------------------------ statistics
def net_r(df, slip, opp=False):
    g = df["gross_opp"] if opp else df["gross"]
    return ((g - df["spread"] - 2 * slip) / df["risk"]).values


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def day_boot(r, rng, B=10000):
    # one trade per day: the day bootstrap is a bootstrap over trades
    pick = rng.integers(0, len(r), size=(B, len(r)))
    return np.percentile(r[pick].mean(1), [2.5, 97.5])


def null_a(df, slip, rng, n):
    """v1.1: C3 on trades with a next bar; real = break direction from the next open."""
    d = df[df["nx_ok"]]
    a = ((d["nx_gross"] - d["nx_spread"] - 2 * slip) / d["risk"]).values
    b = ((d["nx_gross_opp"] - d["nx_spread"] - 2 * slip) / d["risk"]).values
    means = np.empty(n)
    for k in range(0, n, 500):
        mm = min(500, n - k)
        flip = rng.random((mm, len(a))) < 0.5
        means[k:k + mm] = np.where(flip, b, a).mean(1)
    real = a.mean()
    pct = 100.0 * (means < real).mean() + 50.0 * (means == real).mean()
    return means, pct


def null_b(days, df, slip, rng, n):
    """Same days, random entry minute 9:35-15:30 at the bar's open, coin direction,
    stop and target at the same distances as that day's trade."""
    byday = {d["day"]: d for d in days}
    pools = []
    for t in df.itertuples():
        d = byday[t.day]
        k_open, idx, _ = session(d)
        m = d["min"]
        last = idx[-1]
        win = idx[(m[idx] >= k_open + RANGE_BARS) & (m[idx] < k_open + NULLB_LAST)]
        o, h, l, c, sp = d["o"], d["h"], d["l"], d["c"], d["sp"]
        vals = []
        for i in win:
            e = o[i]
            for s_ in (1, -1):
                px, _, _ = simulate(o, h, l, c, i, s_, e - s_ * t.risk, e + s_ * t.tgt_d, last)
                vals.append((s_ * (px - e) - sp[i] - 2 * slip) / t.risk)
        pools.append(np.array(vals))
    sums = np.zeros(n)
    for p in pools:
        sums += p[rng.integers(0, len(p), size=n)]
    means = sums / len(pools)
    real = net_r(df, slip).mean()
    pct = 100.0 * (means < real).mean() + 50.0 * (means == real).mean()
    return means, pct


def c3_real(df, slip):
    d = df[df["nx_ok"]]
    return ((d["nx_gross"] - d["nx_spread"] - 2 * slip) / d["risk"]).mean()


def summary(df, slip, rng, n, label):
    lines = [f"== {label} =="]
    if len(df) == 0:
        return lines + ["no trades"], None
    r = net_r(df, slip)
    wins = int((r > 0).sum())
    lo, hi = wilson(wins, len(r))
    blo, bhi = day_boot(r, rng)
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    means, pct = null_a(df, slip, rng, n)
    q = np.percentile(means, [5, 50, 95])
    lines += [
        f"trades {len(r)}  wins {wins}  win rate {100*wins/len(r):.2f}% (95% {100*lo:.1f}-{100*hi:.1f})"
        + ("  INSUFFICIENT TRADES" if len(r) < MIN_TRADES else ""),
        f"mean net R {r.mean():+.4f} (95% bootstrap {blo:+.4f} to {bhi:+.4f})  PF {pos/neg if neg else np.inf:.3f}",
        f"C3 (from next open, {int(df['nx_ok'].sum())} trades, {int((~df['nx_ok']).sum())} left out): "
        f"break direction {c3_real(df, slip):+.4f}  Null A 5/50/95: {q[0]:+.4f} / {q[1]:+.4f} / {q[2]:+.4f}  -> percentile {pct:.1f}",
        f"longs {int((df['side']>0).sum())}  shorts {int((df['side']<0).sum())}  "
        f"exits target {int((df['kind']=='target').sum())} stop {int((df['kind']=='stop').sum())} "
        f"close {int((df['kind']=='close').sum())}",
        f"median range {np.median(df['range']):.2f}  median stop {np.median(df['risk']):.2f}  "
        f"median target {np.median(df['tgt_d']):.2f}  median spread {np.median(df['spread']):.2f} pts",
    ]
    return lines, pct


# ------------------------------------------------------------ noise data (section 7)
def synth_days(rng):
    """Random walk without drift and without opening effect, 1380 M1 bars per weekday,
    NOISE_SUBSTEPS sub-steps per minute, fixed spread. Tick volume is higher in the
    session only so that the opening is found."""
    var_day = (NOISE_VOL ** 2) / 252
    mins = np.arange(60, 1440)
    in_rth = (mins >= RTH_START) & (mins < RTH_START + RTH_LEN)
    var_min = np.where(in_rth, 0.7 * var_day / RTH_LEN, 0.3 * var_day / (len(mins) - RTH_LEN))
    K = NOISE_SUBSTEPS
    sd_sub = np.sqrt(var_min / K)
    days = []
    logp = np.log(NOISE_START)
    for day in pd.bdate_range("2010-01-04", periods=NOISE_DAYS):
        steps = rng.standard_normal((len(mins), K)) * sd_sub[:, None]
        path = logp + np.cumsum(steps.ravel()).reshape(len(mins), K)
        prev_close = np.r_[logp, path[:-1, -1]]
        days.append({"day": day, "min": mins, "o": np.exp(prev_close), "c": np.exp(path[:, -1]),
                     "h": np.exp(np.maximum(path.max(1), prev_close)),
                     "l": np.exp(np.minimum(path.min(1), prev_close)),
                     "v": np.where(in_rth, 100.0, 20.0), "sp": np.full(len(mins), NOISE_SPREAD)})
        logp = path[-1, -1]
    return days


def noise_check(sets, seed, slip, n):
    rng = np.random.default_rng(seed)
    pcts, wrs, ntr = [], [], []
    print(f"noise check: {sets} sets of {NOISE_DAYS} days, seed {seed}, slip {slip}, Null A runs {n}, "
          f"start {NOISE_START}, vol {NOISE_VOL}, spread {NOISE_SPREAD}, sub-steps {NOISE_SUBSTEPS}")
    for s in range(sets):
        days = synth_days(rng)
        df, fun = run_rule(days)
        if len(df) == 0:
            print(f"set {s+1:2d}: no trades", flush=True)
            continue
        r = net_r(df, slip)
        _, pct = null_a(df, slip, rng, n)
        g = (df["gross"] > 0).mean()
        pcts.append(pct); wrs.append(100 * g); ntr.append(len(df))
        print(f"set {s+1:2d}: trades {len(df):4d}  gross win rate {100*g:5.1f}%  mean net R {r.mean():+.4f}  "
              f"percentile vs Null A {pct:5.1f}  both-sides {fun['both_sides']}  "
              f"beyond-target {fun['entry_beyond_target']}", flush=True)
    pcts = np.array(pcts)
    print(f"mean percentile {pcts.mean():.1f}  above 95: {(pcts > 95).sum()} of {len(pcts)}  "
          f"mean gross win rate {np.mean(wrs):.1f}%  mean trades {np.mean(ntr):.0f}")
    ok = 35 <= pcts.mean() <= 65 and (pcts > 95).sum() <= 3
    print("NOISE CHECK " + ("PASSED" if ok else "FAILED") + " (bounds: mean 35-65, at most 3 of 24 above 95)")


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--sets", type=int, default=24)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--slip", type=float, default=0.25)
    ap.add_argument("--point", type=float, default=0.01)
    ap.add_argument("--from", dest="d_from", default=None)
    ap.add_argument("--to", dest="d_to", default=None)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--nullb", action="store_true")
    a = ap.parse_args()

    if a.noise:
        noise_check(a.sets, 7 if a.seed is None else a.seed, a.slip, a.n)
        return

    seed = 31 if a.seed is None else a.seed
    rng = np.random.default_rng(seed)
    days = build_days(load_mt5(a.csv), a.point)
    d_from = pd.Timestamp(a.d_from) if a.d_from else None
    d_to = pd.Timestamp(a.d_to) if a.d_to else None
    df, fun = run_rule(days, d_from, d_to)
    print(f"file {os.path.basename(a.csv)}  from {a.d_from}  to {a.d_to}  slip/side {a.slip}  seed {seed}")
    print("funnel: " + "  ".join(f"{k} {v}" for k, v in fun.items()))
    for mult in SLIP_MULT:
        print("\n".join(summary(df, a.slip * mult, rng, a.n, f"slippage {mult} x {a.slip} per side")[0]))
    if len(df):
        r0 = (df["gross"] / df["risk"]).values
        print(f"gross (no spread, no slippage): win rate {100*(r0>0).mean():.2f}%  mean R {r0.mean():+.4f}")
        r = net_r(df, a.slip)
        df = df.assign(net_r=r, year=pd.DatetimeIndex(df["day"]).year)
        print("year  trades  win%   meanR")
        for y, g in df.groupby("year"):
            print(f"{y}  {len(g):6d}  {100*(g['net_r']>0).mean():5.1f}  {g['net_r'].mean():+.4f}")
        if a.nullb:
            means, pct = null_b(days, df, a.slip, rng, a.n)
            q = np.percentile(means, [5, 50, 95])
            print(f"Null B (random minute, same day) 5/50/95: {q[0]:+.4f} / {q[1]:+.4f} / {q[2]:+.4f}"
                  f"  -> percentile {pct:.1f}")
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            df.to_csv(os.path.join(a.out, "trades.csv"), index=False)


if __name__ == "__main__":
    main()
