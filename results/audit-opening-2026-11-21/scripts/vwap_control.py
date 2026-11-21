#!/usr/bin/env python3
"""
vwap_control.py · Nullius Research
Measurement script for test N (9 EMA + VWAP on 3 minutes).
Hypothesis: hypothese-vwap-9ema.md, version 1.0, approved 18 Nov 2026 (K1 A, K2 A, K3 A).
Built on orb_control.py (test H): same reading, opening detection and fake market.

Usage:
    python vwap_control.py --selftest                          (EMA, VWAP and rule against a second implementation)
    python vwap_control.py --noise [--sets 24] [--seed 7] [--n 2000]      (noise check, hypothesis section 6)
    python vwap_control.py <M1.csv> --datacheck [--point 0.01]            (metadata only, section 7)
    python vwap_control.py <M1.csv> [--point 0.01] [--slip 0.25] [--from 2019-01-01] [--to 2026-10-30]
                           [--fillspread X] [--n 10000] [--seed 43] [--out dir] [--label US500]

Input: MT5 M1 export, tab separated, <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE>
<TICKVOL> <VOL> <SPREAD>, server time (New York + 7).

All fixed choices come 1-to-1 from the hypothesis and are constants below.
Nothing here changes after the first run on real data.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

# ------------------------------------------------------------ fixed choices (hypothesis sections 4 to 6)
RTH_START = 16 * 60 + 30    # 9:30 New York in server time (NY + 7)
RTH_LEN = 390               # 9:30-16:00
BAR = 3                     # 3-minute candles
NBARS = RTH_LEN // BAR      # 130 candles a day
EMA_LEN = 9
OPEN_OFFSETS = (0,)  # AUDIT 21 nov 2026: fixed opening 16:30 server time (9:30 New York), no detection
MIN_SESSION_FRAC = 0.9
MIN_TRADES = 100
SLIP_MULT = (0, 1, 2)
SEED_NULL = 43
NOISE_SUBSTEPS = 60
NOISE_DAYS = 1500
NOISE_SPREAD = 0.5
NOISE_START = 4000.0        # [implementation choice, as test H] start price of the fake market
NOISE_VOL = 0.20            # [implementation choice, as test H] yearly volatility of the fake market
NOISE_TICKVOL_RTH = 100     # [implementation choice] Poisson mean of tick volume per minute in the session
NOISE_TICKVOL_OUT = 20      # [implementation choice] same, outside the session (lower, so the opening is found)


# ------------------------------------------------------------ reading (as test H)
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


# ------------------------------------------------------------ candles and indicators (section 4.1-4.3)
def make_bars(d, equal_weight=False, fillspread=None):
    """3-minute candles of the regular session, VWAP per candle close.
    Returns None for an invalid day (opening not found, <90% of minutes, or a candle without minutes)."""
    k_open = detect_open(d)
    if k_open is None:
        return None
    m = d["min"]
    sel = (m >= k_open) & (m < k_open + RTH_LEN)
    if sel.sum() < MIN_SESSION_FRAC * RTH_LEN:
        return None
    idx = np.flatnonzero(sel)
    b = (m[idx] - k_open) // BAR
    if len(np.unique(b)) < NBARS:          # [implementation choice] every candle needs at least one minute
        return None
    o, h, l, c, v, sp = (d[k][idx] for k in ("o", "h", "l", "c", "v", "sp"))
    if fillspread is not None:
        sp = np.where(sp > 0, sp, fillspread)
    first = np.searchsorted(b, np.arange(NBARS), "left")
    last = np.searchsorted(b, np.arange(NBARS), "right") - 1
    px = (o + h + l + c) / 4.0
    w = np.ones_like(v) if equal_weight else v
    cpw, cw = np.cumsum(px * w), np.cumsum(w)
    cpe, ce = np.cumsum(px), np.arange(1, len(px) + 1)
    vw = np.where(cw[last] > 0, cpw[last] / np.where(cw[last] > 0, cw[last], 1), cpe[last] / ce[last])
    return {"day": d["day"], "k_open": k_open, "O": o[first], "H": np.maximum.reduceat(h, first),
            "L": np.minimum.reduceat(l, first), "C": c[last], "SP": sp[first], "VW": vw,
            "mo": o, "mh": h, "ml": l, "mb": b}


def ema_series(x, n=EMA_LEN):
    """Pine ta.ema: first value = first source, then alpha * src + (1 - alpha) * previous."""
    a = 2.0 / (n + 1)
    out = np.empty(len(x))
    s = x[0]
    for i, xi in enumerate(x):
        s = xi if i == 0 else a * xi + (1 - a) * s
        out[i] = s
    return out


def prepare(days, equal_weight=False, fillspread=None):
    bars = [b for b in (make_bars(d, equal_weight, fillspread) for d in days) if b is not None]
    if not bars:
        return bars
    e = ema_series(np.concatenate([b["C"] for b in bars]))
    for i, b in enumerate(bars):
        b["E"] = e[i * NBARS:(i + 1) * NBARS]
    return bars


def signals(E, VW):
    s = np.zeros(NBARS, dtype=int)
    up = (E[:-1] <= VW[:-1]) & (E[1:] > VW[1:])
    dn = (E[:-1] >= VW[:-1]) & (E[1:] < VW[1:])
    s[1:][up] = 1
    s[1:][dn] = -1
    s[0] = 0              # no signal on the first candle (VWAP restarts)
    s[NBARS - 1] = 0      # no signal on the last candle
    return s


# ------------------------------------------------------------ the rule (sections 4.4-4.8)
def touch_exit(bar, k, side):
    """K1-B: first minute in candle k that touches EMA9(k-1). Returns price or None."""
    lvl = bar["E"][k - 1]
    sel = np.flatnonzero(bar["mb"] == k)
    for j in sel:
        if side > 0 and bar["ml"][j] <= lvl:
            return min(lvl, bar["mo"][j])
        if side < 0 and bar["mh"][j] >= lvl:
            return max(lvl, bar["mo"][j])
    return None


def rule_day(bar, touch=False):
    O, C, E, SP = bar["O"], bar["C"], bar["E"], bar["SP"]
    s = signals(E, bar["VW"])
    out = []
    pos, eb, ep, esp = 0, 0, 0.0, 0.0

    def close(xp, xk, why):
        out.append((pos, eb, xk, ep, xp, esp, why))

    for t in range(NBARS):
        st = s[t]
        if pos != 0:
            if touch and t >= eb:
                xp = touch_exit(bar, t, pos)
                if xp is not None:
                    close(xp, t, "touch")
                    if st == pos:
                        st = 0      # same-direction cross while the position was open: ignored (4.7)
                    pos = 0
            if pos != 0:
                if t == NBARS - 1:
                    close(C[t], t, "eod")
                    pos = 0
                    continue
                ema_out = t >= eb and ((pos > 0 and C[t] < E[t]) or (pos < 0 and C[t] > E[t]))
                rev = st == -pos
                if ema_out or rev:
                    old = pos
                    close(O[t + 1], t, "rev" if (rev and not ema_out) else "ema")
                    pos = 0
                    if st == -old:
                        pos, eb, ep, esp = st, t + 1, O[t + 1], SP[t + 1]
                    continue
                continue
        if pos == 0 and st != 0 and t <= NBARS - 2:
            pos, eb, ep, esp = st, t + 1, O[t + 1], SP[t + 1]
    return out


def run_rule(bars, touch=False, d_from=None, d_to=None):
    rows = []
    for b in bars:
        if d_from is not None and b["day"] < d_from:
            continue
        if d_to is not None and b["day"] > d_to:
            continue
        for side, eb, xk, ep, xp, esp, why in rule_day(b, touch):
            rows.append({"day": b["day"], "side": side, "entry_bar": eb, "exit_bar": xk, "entry": ep,
                         "exit": xp, "spread": esp, "gross": side * (xp - ep), "why": why})
    return pd.DataFrame(rows)


def net_pts(df, slip):
    return df["gross"] - df["spread"] - 2 * slip


# ------------------------------------------------------------ Null A (section 5)
def null_tables(bar, slip):
    """For every decision candle t (1..128): direction (side of close vs EMA9), net result,
    next decision candle after the trade. Exit as the rule with K1-A, no reversal signal."""
    O, C, E, SP = bar["O"], bar["C"], bar["E"], bar["SP"]
    dirn = np.sign(C - E).astype(int)
    net = np.zeros(NBARS)
    nxt = np.arange(1, NBARS + 1)
    for t in range(1, NBARS - 1):
        dd = dirn[t]
        if dd == 0:
            continue
        ep, k = O[t + 1], t + 1
        while k < NBARS - 1 and not ((dd > 0 and C[k] < E[k]) or (dd < 0 and C[k] > E[k])):
            k += 1
        if k == NBARS - 1 and not ((dd > 0 and C[k] < E[k]) or (dd < 0 and C[k] > E[k])):
            xp = C[k]
        elif k == NBARS - 1:
            xp = C[k]
        else:
            xp = O[k + 1]
        net[t] = dd * (xp - ep) - SP[t + 1] - 2 * slip
        nxt[t] = k + 1
    dirn[0] = 0
    dirn[NBARS - 1] = 0
    return dirn, net, nxt


def expected_trades(tables, p):
    """Exact expected number of Null A trades for probability p (dynamic programming, all days at once)."""
    D = np.array([t[0] for t in tables]) != 0
    NX = np.minimum(np.array([t[2] for t in tables]), NBARS)
    rows = np.arange(len(tables))
    f = np.zeros((len(tables), NBARS + 2))
    for t in range(NBARS - 1, 0, -1):
        q = np.where(D[:, t], p, 0.0)
        f[:, t] = q * (1 + f[rows, NX[:, t]]) + (1 - q) * f[:, t + 1]
    return f[:, 1].sum()


def calibrate_p(tables, n_target):
    lo, hi = 1e-6, 1.0
    if expected_trades(tables, hi) < n_target:
        return hi
    for _ in range(40):
        mid = (lo + hi) / 2
        if expected_trades(tables, mid) < n_target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def null_a(tables, p, rng, n):
    S, N = np.zeros(n), np.zeros(n)
    for dirn, net, nxt in tables:
        cur = np.ones(n, dtype=int)
        for t in range(1, NBARS - 1):
            act = cur == t
            if not act.any():
                continue
            if dirn[t] == 0:
                cur[act] = t + 1
                continue
            take = act & (rng.random(n) < p)
            S[take] += net[t]
            N[take] += 1
            cur[take] = nxt[t]
            cur[act & ~take] = t + 1
    return np.where(N > 0, S / np.maximum(N, 1), np.nan), N


# ------------------------------------------------------------ statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    hw = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return c - hw, c + hw


def day_boot(df, col, rng, B=10000):
    g = df.groupby("day")[col].agg(["sum", "count"])
    s, c = g["sum"].values, g["count"].values
    D = len(s)
    out = np.empty(B)
    for a in range(0, B, 500):
        bb = min(500, B - a)
        idx = rng.integers(0, D, (bb, D))
        out[a:a + bb] = s[idx].sum(1) / c[idx].sum(1)
    return np.percentile(out, [2.5, 97.5])


def pf(x):
    g, l = x[x > 0].sum(), -x[x < 0].sum()
    return np.inf if l == 0 else g / l


# ------------------------------------------------------------ selftest
def second_rule(bar):
    """Independent re-implementation of the rule (K1-A) with pandas, for the selftest."""
    f = pd.DataFrame({"O": bar["O"], "C": bar["C"], "E": bar["E"], "V": bar["VW"]})
    f["above"] = f["E"] > f["V"]
    f["sig"] = 0
    for i in range(1, NBARS - 1):
        if f.at[i, "above"] and f.at[i - 1, "E"] <= f.at[i - 1, "V"]:
            f.at[i, "sig"] = 1
        if (f.at[i, "E"] < f.at[i, "V"]) and f.at[i - 1, "E"] >= f.at[i - 1, "V"]:
            f.at[i, "sig"] = -1
    trades, side, start = [], 0, None
    i = 0
    while i < NBARS:
        if side == 0:
            if f.at[i, "sig"] != 0:
                side, start = int(f.at[i, "sig"]), i + 1
            i += 1
            continue
        if i == NBARS - 1:
            trades.append((side, start, i))
            side = 0
            i += 1
            continue
        out = (side > 0 and f.at[i, "C"] < f.at[i, "E"]) or (side < 0 and f.at[i, "C"] > f.at[i, "E"])
        rev = f.at[i, "sig"] == -side
        if out or rev:
            trades.append((side, start, i))
            side = -side if rev else 0
            start = i + 1 if rev else None
        i += 1
    return trades


def selftest():
    rng = np.random.default_rng(5)
    days = synth_days(rng, ndays=60)
    bars = prepare(days)
    ok = True
    allc = np.concatenate([b["C"] for b in bars])
    e2 = pd.Series(allc).ewm(span=EMA_LEN, adjust=False).mean().values
    e1 = np.concatenate([b["E"] for b in bars])
    d_ema = np.abs(e1 - e2).max()
    print(f"EMA9 vs pandas ewm(adjust=False): max diff {d_ema:.2e}")
    ok &= d_ema < 1e-9
    worst = 0.0
    for d, b in zip([dd for dd in days if make_bars(dd) is not None], bars):
        k = b["k_open"]
        sel = (d["min"] >= k) & (d["min"] < k + RTH_LEN)
        mm, oo, hh, ll, cc, vv = (d[x][sel] for x in ("min", "o", "h", "l", "c", "v"))
        for j in range(NBARS):
            upto = mm < k + BAR * (j + 1)
            p = (oo[upto] + hh[upto] + ll[upto] + cc[upto]) / 4
            worst = max(worst, abs((p * vv[upto]).sum() / vv[upto].sum() - b["VW"][j]))
    print(f"VWAP vs per-candle recomputation: max diff {worst:.2e}")
    ok &= worst < 1e-9
    n1 = n2 = mism = 0
    for b in bars:
        a = [(s, eb, xk) for s, eb, xk, *_ in rule_day(b)]
        c = second_rule(b)
        n1 += len(a)
        n2 += len(c)
        mism += a != c
    print(f"rule vs second implementation: trades {n1} vs {n2}, days with a difference {mism} of {len(bars)}")
    ok &= mism == 0 and n1 > 0
    tables = [null_tables(b, 0.0) for b in bars]
    p = calibrate_p(tables, n1)
    m, N = null_a(tables, p, rng, 4000)
    print(f"Null A: calibrated p {p:.4f}, expected trades {expected_trades(tables, p):.1f}, "
          f"simulated mean {N.mean():.1f}, target {n1}")
    ok &= abs(N.mean() - n1) / n1 < 0.03
    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    return ok


# ------------------------------------------------------------ noise check (section 6)
def synth_days(rng, ndays=NOISE_DAYS):
    """Random walk without drift and without opening effect, 1380 M1 bars per weekday,
    NOISE_SUBSTEPS sub-steps per minute, fixed spread, random tick volume (higher in the session
    only so that the opening is found). As test H plus random tick volume."""
    var_day = (NOISE_VOL ** 2) / 252
    mins = np.arange(60, 1440)
    in_rth = (mins >= RTH_START) & (mins < RTH_START + RTH_LEN)
    var_min = np.where(in_rth, 0.7 * var_day / RTH_LEN, 0.3 * var_day / (len(mins) - RTH_LEN))
    K = NOISE_SUBSTEPS
    sd_sub = np.sqrt(var_min / K)
    days = []
    logp = np.log(NOISE_START)
    lam = np.where(in_rth, NOISE_TICKVOL_RTH, NOISE_TICKVOL_OUT)
    for day in pd.bdate_range("2010-01-04", periods=ndays):
        steps = rng.standard_normal((len(mins), K)) * sd_sub[:, None]
        path = logp + np.cumsum(steps.ravel()).reshape(len(mins), K)
        prev_close = np.r_[logp, path[:-1, -1]]
        days.append({"day": day, "min": mins, "o": np.exp(prev_close), "c": np.exp(path[:, -1]),
                     "h": np.exp(np.maximum(path.max(1), prev_close)),
                     "l": np.exp(np.minimum(path.min(1), prev_close)),
                     "v": rng.poisson(lam).astype(float) + 1.0, "sp": np.full(len(mins), NOISE_SPREAD)})
        logp = path[-1, -1]
    return days


def noise_check(sets, seed, slip, n):
    rng = np.random.default_rng(seed)
    pcts, wrs, ntr = [], [], []
    print(f"noise check: {sets} sets of {NOISE_DAYS} days, seed {seed}, slip {slip}, Null A runs {n}, "
          f"start {NOISE_START}, vol {NOISE_VOL}, spread {NOISE_SPREAD}, sub-steps {NOISE_SUBSTEPS}", flush=True)
    for s in range(sets):
        bars = prepare(synth_days(rng))
        df = run_rule(bars)
        x = net_pts(df, slip)
        tables = [null_tables(b, slip) for b in bars]
        p = calibrate_p(tables, len(df))
        m, _ = null_a(tables, p, rng, n)
        pct = 100 * (m < x.mean()).mean()
        g = (df["gross"] > 0).mean()
        pcts.append(pct); wrs.append(100 * g); ntr.append(len(df))
        print(f"set {s+1:2d}: trades {len(df):6d}  per day {len(df)/len(bars):4.2f}  gross win rate {100*g:5.1f}%  "
              f"mean net {x.mean():+.4f} pt  p {p:.4f}  percentile vs Null A {pct:5.1f}", flush=True)
    pcts = np.array(pcts)
    print(f"mean percentile {pcts.mean():.1f}  above 95: {(pcts > 95).sum()} of {len(pcts)}  "
          f"mean gross win rate {np.mean(wrs):.1f}%  mean trades {np.mean(ntr):.0f}")
    ok = 35 <= pcts.mean() <= 65 and (pcts > 95).sum() <= 3
    print("NOISE CHECK " + ("PASSED" if ok else "FAILED") + " (bounds: mean 35-65, at most 3 of 24 above 95)")
    return ok


# ------------------------------------------------------------ data check (section 7, metadata only)
def datacheck(days):
    rows = []
    for d in days:
        k = detect_open(d)
        m = d["min"]
        sel = (m >= k) & (m < k + RTH_LEN) if k is not None else np.zeros(len(m), bool)
        b = make_bars(d)
        rows.append({"year": d["day"].year, "valid": b is not None, "open_min": k,
                     "rth_minutes": int(sel.sum()),
                     "spread_empty": float((d["sp"][sel] <= 0).mean()) if sel.any() else np.nan,
                     "zero_vol": float((d["v"][sel] <= 0).mean()) if sel.any() else np.nan})
    f = pd.DataFrame(rows)
    print("year | days | valid sessions | opening 15:30 / 16:30 / 17:30 server (valid) | "
          "RTH minutes median | spread empty % | tick volume zero %")
    for y, g in f.groupby("year"):
        v = g[g["valid"]]
        oc = v["open_min"].value_counts()
        print(f"{y} | {len(g)} | {len(v)} | {oc.get(RTH_START-60,0)} / {oc.get(RTH_START,0)} / {oc.get(RTH_START+60,0)} | "
              f"{v['rth_minutes'].median() if len(v) else float('nan'):.0f} | "
              f"{100*v['spread_empty'].mean() if len(v) else float('nan'):.1f} | "
              f"{100*v['zero_vol'].mean() if len(v) else float('nan'):.2f}")


# ------------------------------------------------------------ report
def summary(df, slip, rng, label, tables=None, n=0, out=None):
    x = net_pts(df, slip)
    df = df.assign(net=x, bps=x / df["entry"] * 1e4)
    nd = df["day"].nunique()
    k = int((df["net"] > 0).sum())
    lo, hi = wilson(k, len(df))
    ci = day_boot(df, "net", rng)
    cib = day_boot(df, "bps", rng)
    line = (f"{label}: trades {len(df)}, days with trades {nd}, per day {len(df)/max(nd,1):.2f} | "
            f"win rate net {100*k/len(df):.1f}% ({100*lo:.1f}-{100*hi:.1f}) | "
            f"mean net {x.mean():+.3f} pt ({ci[0]:+.3f} to {ci[1]:+.3f}) | "
            f"mean net {df['bps'].mean():+.2f} bp ({cib[0]:+.2f} to {cib[1]:+.2f}) | PF {pf(x.values):.2f} | "
            f"gross {df['gross'].mean():+.3f} pt")
    if len(df) < MIN_TRADES:
        line += " | INSUFFICIENT TRADES"
    pct = None
    if tables is not None and n > 0:
        p = calibrate_p(tables, len(df))
        m, N = null_a(tables, p, rng, n)
        pct = 100 * (m < x.mean()).mean()
        ties = int((m == x.mean()).sum())
        line += (f" | Null A: p {p:.4f}, mean trades {N.mean():.0f}, mean net {np.nanmean(m):+.3f} pt, "
                 f"percentile {pct:.1f} (ties {ties})")
    print(line, flush=True)
    if out is not None:
        out.write(line + "\n")
    return df, ci, pct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--datacheck", action="store_true")
    ap.add_argument("--sets", type=int, default=24)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--slip", type=float, default=0.25)
    ap.add_argument("--point", type=float, default=0.01)
    ap.add_argument("--from", dest="d_from", default="2019-01-01")
    ap.add_argument("--to", dest="d_to", default="2026-10-30")
    ap.add_argument("--fillspread", type=float, default=None)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default="US500")
    ap.add_argument("--short", action="store_true", help="main measurement only, no variants")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.noise:
        noise_check(a.sets, 7 if a.seed is None else a.seed, a.slip, 2000 if a.n is None else a.n)
        return
    m1 = load_mt5(a.csv)
    days = build_days(m1, a.point)
    if a.datacheck:
        datacheck(days)
        return

    seed = SEED_NULL if a.seed is None else a.seed
    n = 10000 if a.n is None else a.n
    rng = np.random.default_rng(seed)
    d_from, d_to = pd.Timestamp(a.d_from), pd.Timestamp(a.d_to)
    os.makedirs(a.out or ".", exist_ok=True)
    fo = open(os.path.join(a.out or ".", f"run01_{a.label}.txt"), "w", encoding="utf-8")
    hdr = (f"vwap_control.py run on {a.label}: {os.path.basename(a.csv)}, point {a.point}, slip {a.slip}, "
           f"P1 {a.d_from} to {a.d_to}, fillspread {a.fillspread}, Null A runs {n}, seed {seed}")
    print(hdr); fo.write(hdr + "\n")

    bars = prepare(days, fillspread=a.fillspread)
    inper = [b for b in bars if d_from <= b["day"] <= d_to]
    msg = f"valid sessions in P1: {len(inper)} (all valid sessions in the file: {len(bars)})"
    print(msg); fo.write(msg + "\n")

    df = run_rule(bars, d_from=d_from, d_to=d_to)
    tables = [null_tables(b, a.slip) for b in inper]
    fo.write("\n== P1, deciding for C1 and C2 ==\n")
    full, ci, pct = summary(df, a.slip, rng, "P1", tables, n, fo)
    full.to_csv(os.path.join(a.out or ".", f"trades_{a.label}.csv"), index=False)

    oct0, oct1 = pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-30")
    fo.write("\n== P0, October 2026, deciding for C3 ==\n")
    p0 = df[(df["day"] >= oct0) & (df["day"] <= oct1)]
    t0 = [null_tables(b, a.slip) for b in inper if oct0 <= b["day"] <= oct1]
    if len(p0):
        summary(p0, a.slip, rng, "P0 Oct 2026", t0, n, fo)

    verdict = (f"\nC1 {'FALSIFIED' if ci[1] < 0 else 'not falsified'} (upper bound {ci[1]:+.3f} pt) | "
               f"C2 {'FALSIFIED' if pct is not None and pct <= 95 else 'not falsified'} (percentile {pct:.1f})")
    print(verdict); fo.write(verdict + "\n")
    if len(p0):
        ci0 = day_boot(p0.assign(net=net_pts(p0, a.slip)), "net", rng)
        v0 = f"C3 {'FALSIFIED' if ci0[1] < 0 else 'not falsified'} (upper bound {ci0[1]:+.3f} pt)"
        print(v0); fo.write(v0 + "\n")

    if a.short:
        fo.close()
        return

    fo.write("\n== Descriptive (section 9) ==\n")
    x = net_pts(df, a.slip)
    dur = (df["exit_bar"] - df["entry_bar"] + 1) * BAR
    lines = [f"median duration {dur.median():.0f} min, mean {dur.mean():.1f} min",
             f"largest loss per trade {x.min():+.2f} pt on {df.loc[x.idxmin(), 'day'].date()}, "
             f"largest gain {x.max():+.2f} pt",
             f"exit reasons: {df['why'].value_counts().to_dict()}",
             f"mean spread at entry {df['spread'].mean():.3f} pt, cost per trade at slip x1 "
             f"{(df['spread'] + 2*a.slip).mean():.3f} pt"]
    for L in lines:
        print(L); fo.write(L + "\n")
    for mult in SLIP_MULT:
        xx = df["gross"] - df["spread"] - 2 * a.slip * mult
        L = f"costs: spread + slip x{mult}: mean net {xx.mean():+.3f} pt, PF {pf(xx.values):.2f}"
        print(L); fo.write(L + "\n")
    L = f"no costs at all: mean gross {df['gross'].mean():+.3f} pt, gross win rate {100*(df['gross']>0).mean():.1f}%"
    print(L); fo.write(L + "\n")
    for side, nm in ((1, "long"), (-1, "short")):
        summary(df[df["side"] == side], a.slip, rng, f"{nm}", None, 0, fo)
    for y, g in df.groupby(df["day"].dt.year):
        summary(g, a.slip, rng, f"year {y}", None, 0, fo)

    fo.write("\n== Variant K1-B (touch), not deciding ==\n")
    dfb = run_rule(bars, touch=True, d_from=d_from, d_to=d_to)
    summary(dfb, a.slip, rng, "K1-B touch", None, 0, fo)

    fo.write("\n== VWAP without volume, not deciding ==\n")
    bars_ew = prepare(days, equal_weight=True, fillspread=a.fillspread)
    dfe = run_rule(bars_ew, d_from=d_from, d_to=d_to)
    te = [null_tables(b, a.slip) for b in bars_ew if d_from <= b["day"] <= d_to]
    summary(dfe, a.slip, rng, "VWAP equal weight", te, n, fo)
    fo.close()


if __name__ == "__main__":
    main()
