#!/usr/bin/env python3
"""
box_control.py · Nullius Research
Measurement script for test G (Box Theory, traded blindly).
Hypothesis: hypothese-box-theory-v1.1.md, approved 11 Nov 2026 (SHA-256 2f4a8c27...).
v1.1 changes only the fake market of the noise check: 60 sub-steps per minute (v1.0: 5).

Usage:
    python box_control.py <M1.csv> --minstop 10 --slip 1.0 [--point 0.01]
                          [--from 2019-01-01] [--to 2026-10-30] [--n 10000] [--seed 23]
                          [--nullb] [--out results_dir]
    python box_control.py --noise [--sets 24] [--seed 7]    (noise check, section 5)

Input: MT5 M1 export (Symbols > Bars > Export), tab separated,
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>, server time.

All fixed choices come 1-to-1 from the hypothesis and are constants below.
Nothing here changes after the first run on real data.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

# ------------------------------------------------------------ fixed choices
RTH_START = 16 * 60 + 30   # 9:30 New York in server time (NY + 7)
RTH_LEN = 390              # 9:30-16:00
BOX_FIX = 15               # box widens once at 9:45, then fixed
ENTRY_END = 360            # no new entries from 15:30
STOP_FRAC = 0.2            # stop 0.2 box heights beyond the edge
TGT_FRAC = 0.5             # target = middle line = 0.5 box heights from the edge
OPEN_OFFSETS = (-60, 0, 60)  # allowed opening shifts (DST weeks), detected from tick volume
MIN_SESSION_FRAC = 0.9     # session counts with >= 90% of the expected M1 bars
MIN_TRADES = 100
SLIP_MULT = (0, 1, 2)
NOISE_SUBSTEPS = 60        # v1.1 (v1.0: 5)


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


# ------------------------------------------------------------ days
def build_days(m1, point):
    """Per server date: arrays of minute-of-day, OHLC, volume, spread (points)."""
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
    """Opening minute: largest tick-volume jump among RTH_START + OPEN_OFFSETS (15-min means)."""
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


# ------------------------------------------------------------ path
def simulate(o, h, l, c, i0, side, entry, stop, target, last):
    """Returns (exit_price, exit_index, kind) with kind 'stop', 'target' or 'close'."""
    # entry bar: stop only
    if side < 0:
        if h[i0] >= stop:
            return stop, i0, "stop"
    else:
        if l[i0] <= stop:
            return stop, i0, "stop"
    for i in range(i0 + 1, last + 1):
        if side < 0:
            hit_s = h[i] >= stop
            hit_t = l[i] <= target
            if hit_s:
                px = max(stop, o[i])  # gap beyond the stop: exit at the open
                return px, i, "stop"
            if hit_t:
                return target, i, "target"
        else:
            hit_s = l[i] <= stop
            hit_t = h[i] >= target
            if hit_s:
                px = min(stop, o[i])
                return px, i, "stop"
            if hit_t:
                return target, i, "target"
    return c[last], last, "close"


# ------------------------------------------------------------ the rule
def day_trades(prev, d, minstop):
    """Box, entries and both-direction outcomes for one day. Returns (info, trades)."""
    info = {"open_found": False, "valid": False, "top_touch": False, "bot_touch": False,
            "minstop_ok": False}
    k_open = detect_open(d)
    if k_open is None:
        return info, []
    info["open_found"] = True
    m = d["min"]
    rth = (m >= k_open) & (m < k_open + RTH_LEN)
    if rth.sum() < MIN_SESSION_FRAC * RTH_LEN:
        return info, []
    info["valid"] = True
    top, bot = prev["h"].max(), prev["l"].min()
    pre = m < k_open
    if pre.any():
        top, bot = max(top, d["h"][pre].max()), min(bot, d["l"][pre].min())
    upto = m < k_open + BOX_FIX
    top, bot = max(top, d["h"][upto].max()), min(bot, d["l"][upto].min())
    H = top - bot
    mid = (top + bot) / 2
    info["H"] = H
    if STOP_FRAC * H < minstop:
        return info, []
    info["minstop_ok"] = True
    o, h, l, c, sp = d["o"], d["h"], d["l"], d["c"], d["sp"]
    idx = np.flatnonzero(rth)
    last = idx[-1]
    win = idx[(m[idx] >= k_open + BOX_FIX) & (m[idx] < k_open + ENTRY_END)]
    trades = []
    taken = {+1: False, -1: False}
    flat_from = win[0] if len(win) else None
    for i in win:
        if flat_from is None or i < flat_from:
            continue
        t_top = h[i] >= top
        t_bot = l[i] <= bot
        info["top_touch"] |= bool(t_top)
        info["bot_touch"] |= bool(t_bot)
        if t_top and t_bot:
            continue
        side = -1 if t_top else (+1 if t_bot else 0)
        if side == 0 or taken[side]:
            continue
        entry = top if side < 0 else bot
        risk = STOP_FRAC * H
        res = {}
        for s in (side, -side):
            stop = entry - s * risk
            target = entry + s * TGT_FRAC * H
            px, j, kind = simulate(o, h, l, c, i, s, entry, stop, target, last)
            res[s] = (s * (px - entry), j, kind)
        g, j, kind = res[side]
        trades.append({"day": d["day"], "i": int(i), "minute": int(m[i]), "side": side,
                       "entry": entry, "risk": risk, "H": H, "spread": float(sp[i]),
                       "gross": g, "kind": kind, "exit_minute": int(m[j]),
                       "gross_opp": res[-side][0], "kind_opp": res[-side][2]})
        taken[side] = True
        flat_from = j + 1
        if taken[+1] and taken[-1]:
            break
    return info, trades


def run_rule(days, minstop, d_from=None, d_to=None):
    trades, funnel = [], {"days": 0, "open_found": 0, "valid": 0, "minstop_ok": 0,
                          "top_touch": 0, "bot_touch": 0}
    for k in range(1, len(days)):
        d = days[k]
        if d_from is not None and d["day"] < d_from:
            continue
        if d_to is not None and d["day"] > d_to:
            continue
        funnel["days"] += 1
        info, tr = day_trades(days[k - 1], d, minstop)
        for key in ("open_found", "valid", "minstop_ok", "top_touch", "bot_touch"):
            funnel[key] += int(bool(info.get(key)))
        trades += tr
    return pd.DataFrame(trades), funnel


# ------------------------------------------------------------ Null B (additional)
def day_pool(prev, d, minstop):
    """All bars between 9:45 and 15:30 as random entries at the bar's open, both directions,
    stop 0.2H and target 0.5H of that day's box. Returns (gross_long, gross_short, risk, spread)."""
    k_open = detect_open(d)
    if k_open is None:
        return None
    m = d["min"]
    rth = (m >= k_open) & (m < k_open + RTH_LEN)
    if rth.sum() < MIN_SESSION_FRAC * RTH_LEN:
        return None
    top, bot = prev["h"].max(), prev["l"].min()
    upto = m < k_open + BOX_FIX
    top, bot = max(top, d["h"][upto].max()), min(bot, d["l"][upto].min())
    H = top - bot
    risk = STOP_FRAC * H
    if risk < minstop:
        return None
    idx = np.flatnonzero(rth)
    last = idx[-1]
    win = idx[(m[idx] >= k_open + BOX_FIX) & (m[idx] < k_open + ENTRY_END)]
    o, h, l, c = d["o"], d["h"], d["l"], d["c"]
    seg = np.arange(win[0], last + 1)
    hs, ls, os_ = h[seg], l[seg], o[seg]
    out = {}
    for s in (+1, -1):
        g = np.empty(len(win))
        for n_, i in enumerate(win):
            e = o[i]
            stop, tgt = e - s * risk, e + s * TGT_FRAC * H
            k0 = i - seg[0]
            if s > 0:
                st = ls[k0:] <= stop
                tg = hs[k0 + 1:] >= tgt
            else:
                st = hs[k0:] >= stop
                tg = ls[k0 + 1:] <= tgt
            js = np.argmax(st) if st.any() else 10 ** 9
            jt = (np.argmax(tg) + 1) if tg.any() else 10 ** 9
            if js == 10 ** 9 and jt == 10 ** 9:
                g[n_] = s * (c[last] - e)
            elif js <= jt:
                px = stop if js == 0 else (min(stop, os_[k0 + js]) if s > 0 else max(stop, os_[k0 + js]))
                g[n_] = s * (px - e)
            else:
                g[n_] = s * (tgt - e)
        out[s] = g
    return out[+1], out[-1], risk, d["sp"][win]


def null_b(days, df, minstop, slip, rng, n, d_from=None, d_to=None):
    pools = {}
    for k in range(1, len(days)):
        d = days[k]
        if d_from is not None and d["day"] < d_from:
            continue
        if d_to is not None and d["day"] > d_to:
            continue
        p = day_pool(days[k - 1], d, minstop)
        if p is None:
            continue
        gl, gs, risk, sp = p
        key = (d["day"].year, d["day"].month)
        rl = (gl - sp - 2 * slip) / risk
        rs = (gs - sp - 2 * slip) / risk
        pools.setdefault(key, []).append(np.concatenate([rl, rs]))
    pools = {k: np.concatenate(v) for k, v in pools.items()}
    keys = [(pd.Timestamp(x).year, pd.Timestamp(x).month) for x in df["day"].values]
    sums = np.zeros(n)
    for key, cnt in pd.Series(keys).value_counts().items():
        pool = pools.get(key)
        if pool is None:
            continue
        pick = rng.integers(0, len(pool), size=(n, cnt))
        sums += pool[pick].sum(1)
    means = sums / len(df)
    real = net_r(df, slip).mean()
    pct = 100.0 * (means < real).mean() + 50.0 * (means == real).mean()
    return means, pct


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


def day_boot(df, r, rng, B=10000):
    days = df["day"].values
    u, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=r, minlength=len(u))
    n = np.bincount(inv, minlength=len(u)).astype(float)
    pick = rng.integers(0, len(u), size=(B, len(u)))
    means = s[pick].sum(1) / n[pick].sum(1)
    return np.percentile(means, [2.5, 97.5])


def null_a(df, slip, rng, n):
    a = net_r(df, slip)
    b = net_r(df, slip, opp=True)
    means = np.empty(n)
    for k in range(0, n, 500):
        m = min(500, n - k)
        flip = rng.random((m, len(a))) < 0.5
        means[k:k + m] = np.where(flip, b, a).mean(1)
    real = a.mean()
    pct = 100.0 * (means < real).mean() + 50.0 * (means == real).mean()
    return means, pct


def summary(df, slip, rng, n, label):
    lines = [f"== {label} =="]
    if len(df) == 0:
        return lines + ["no trades"], None
    r = net_r(df, slip)
    wins = int((r > 0).sum())
    lo, hi = wilson(wins, len(r))
    blo, bhi = day_boot(df, r, rng)
    pos = r[r > 0].sum(); neg = -r[r < 0].sum()
    means, pct = null_a(df, slip, rng, n)
    q = np.percentile(means, [5, 50, 95])
    srt = np.sort(r)[::-1]
    top5 = srt[:max(1, int(round(0.05 * len(r))))].sum()
    streak = mx = 0
    for x in r:
        streak = streak + 1 if x <= 0 else 0
        mx = max(mx, streak)
    lines += [
        f"trades {len(r)}  wins {wins}  win rate {100*wins/len(r):.2f}% (95% {100*lo:.1f}-{100*hi:.1f})"
        + ("  INSUFFICIENT TRADES" if len(r) < MIN_TRADES else ""),
        f"mean net R {r.mean():+.4f} (95% day bootstrap {blo:+.4f} to {bhi:+.4f})  PF {pos/neg if neg else np.inf:.2f}",
        f"Null A 5/50/95: {q[0]:+.4f} / {q[1]:+.4f} / {q[2]:+.4f}  -> percentile {pct:.1f}",
        f"longs {int((df['side']>0).sum())}  shorts {int((df['side']<0).sum())}  "
        f"exits target {int((df['kind']=='target').sum())} stop {int((df['kind']=='stop').sum())} "
        f"close {int((df['kind']=='close').sum())}",
        f"median stop {np.median(df['risk']):.2f} pts  median spread {np.median(df['spread']):.2f} pts  "
        f"longest losing streak {mx}  best 5% sum {top5:+.2f}R of total {r.sum():+.2f}R",
    ]
    return lines, pct


# ------------------------------------------------------------ noise data
def synth_days(rng, years=5, start_price=15000.0, vol_year=0.20):
    """Random walk without drift, 1380 M1 bars per weekday (01:00-24:00 server),
    70% of the daily variance in the session, tick volume higher in the session,
    NOISE_SUBSTEPS sub-steps per minute for high and low."""
    n_days = years * 252
    var_day = (vol_year ** 2) / 252
    mins = np.arange(60, 1440)
    in_rth = (mins >= RTH_START) & (mins < RTH_START + RTH_LEN)
    var_min = np.where(in_rth, 0.7 * var_day / RTH_LEN, 0.3 * var_day / (len(mins) - RTH_LEN))
    K = NOISE_SUBSTEPS
    sd_sub = np.sqrt(var_min / K)
    days = []
    logp = np.log(start_price)
    d0 = pd.Timestamp("2010-01-04")
    bdays = pd.bdate_range(d0, periods=n_days)
    for day in bdays:
        steps = rng.standard_normal((len(mins), K)) * sd_sub[:, None]
        path = logp + np.cumsum(steps.ravel()).reshape(len(mins), K)
        prev_close = np.r_[logp, path[:-1, -1]]
        o = np.exp(prev_close)
        c = np.exp(path[:, -1])
        h = np.exp(np.maximum(path.max(1), prev_close))
        l = np.exp(np.minimum(path.min(1), prev_close))
        logp = path[-1, -1]
        v = np.where(in_rth, 100.0, 20.0)
        days.append({"day": day, "min": mins, "o": o, "h": h, "l": l, "c": c,
                     "v": v, "sp": np.full(len(mins), 1.0)})
    return days


def noise_check(sets, seed, minstop, slip, n):
    rng = np.random.default_rng(seed)
    pcts, wrs, ntr = [], [], []
    print(f"noise check: {sets} sets, seed {seed}, minstop {minstop}, slip {slip}, Null A runs {n}")
    for s in range(sets):
        days = synth_days(rng)
        df, fun = run_rule(days, minstop)
        if len(df) == 0:
            print(f"set {s+1:2d}: no trades"); continue
        r = net_r(df, slip)
        _, pct = null_a(df, slip, rng, n)
        g = ((df["gross"]) > 0).mean()
        pcts.append(pct); wrs.append(100 * g); ntr.append(len(df))
        print(f"set {s+1:2d}: trades {len(df):4d}  gross win rate {100*g:5.1f}%  "
              f"mean net R {r.mean():+.4f}  percentile vs Null A {pct:5.1f}")
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
    ap.add_argument("--minstop", type=float, default=10.0)
    ap.add_argument("--slip", type=float, default=1.0)
    ap.add_argument("--point", type=float, default=0.01)
    ap.add_argument("--from", dest="d_from", default=None)
    ap.add_argument("--to", dest="d_to", default=None)
    ap.add_argument("--after", default=None, help="extra report from this date (P2)")
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--nullb", action="store_true")
    a = ap.parse_args()

    if a.noise:
        noise_check(a.sets, 7 if a.seed is None else a.seed, a.minstop, a.slip, a.n)
        return

    seed = 23 if a.seed is None else a.seed
    rng = np.random.default_rng(seed)
    m1 = load_mt5(a.csv)
    days = build_days(m1, a.point)
    d_from = pd.Timestamp(a.d_from) if a.d_from else None
    d_to = pd.Timestamp(a.d_to) if a.d_to else None
    df, fun = run_rule(days, a.minstop, d_from, d_to)
    print(f"file {os.path.basename(a.csv)}  minstop {a.minstop}  slip/side {a.slip}  seed {seed}")
    print("funnel: " + "  ".join(f"{k} {v}" for k, v in fun.items()) + f"  trades {len(df)}")
    for mult in SLIP_MULT:
        lines, _ = summary(df, a.slip * mult, rng, a.n, f"slippage {mult} x {a.slip} per side")
        print("\n".join(lines))
    if len(df):
        r = net_r(df, a.slip)
        df = df.assign(net_r=r, year=pd.DatetimeIndex(df["day"]).year)
        print("year  trades  win%   meanR")
        for y, g in df.groupby("year"):
            print(f"{y}  {len(g):6d}  {100*(g['net_r']>0).mean():5.1f}  {g['net_r'].mean():+.4f}")
        if a.after:
            sub = df[df["day"] >= pd.Timestamp(a.after)]
            print("\n".join(summary(sub, a.slip, rng, a.n, f"from {a.after}")[0]))
        if a.nullb:
            means, pct = null_b(days, df, a.minstop, a.slip, rng, a.n, d_from, d_to)
            q = np.percentile(means, [5, 50, 95])
            print(f"Null B (random place, same month) 5/50/95: {q[0]:+.4f} / {q[1]:+.4f} / {q[2]:+.4f}"
                  f"  -> percentile {pct:.1f}")
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            df.to_csv(os.path.join(a.out, "trades.csv"), index=False)


if __name__ == "__main__":
    main()
