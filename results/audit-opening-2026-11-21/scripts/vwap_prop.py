#!/usr/bin/env python3
"""
vwap_prop.py · Nullius Research
Measurement script for test O (9 EMA + VWAP, long only, 5 minutes, with a prop firm challenge).
Hypothesis: hypothese-vwap-prop.md, version 1.1, approved 20 Nov 2026 (K1 A, K2 A; C5 descriptive since v1.1).
Built on vwap_control.py (test N): same reading, opening detection, VWAP, EMA and fake market.

Usage:
    python vwap_prop.py --selftest
    python vwap_prop.py --noise [--sets 24] [--seed 7] [--n 2000]                 (hypothesis section 7)
    python vwap_prop.py <M1.csv> --datacheck [--session rth|full]                  (section 8, metadata only)
    python vwap_prop.py <M1.csv> [--session rth] [--firm firm_a] [--slip 1.0] [--from 2023-11-17] [--to 2026-11-05]
                        [--n 10000] [--nprop 2000] [--seed 43] [--out dir] [--label USTEC] [--short]

Input: MT5 M1 export, tab separated, <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>,
server time (New York + 7).

All fixed choices come 1-to-1 from the hypothesis and are constants below.
Nothing here changes after the first run on real data.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

# ------------------------------------------------------------ fixed choices (hypothesis sections 3 to 7)
RTH_START = 16 * 60 + 30    # 9:30 New York in server time (NY + 7)
RTH_LEN = 390               # K1 A: 9:30-16:00
FULL_START = 60             # K1 B: 18:00 New York = 1:00 server
FULL_LEN = 23 * 60 + 10 - 60  # K1 B: until 16:10 New York = 23:10 server (firm A flat time)
BAR = 5                     # 5-minute candles
EMA_LEN = 9
OPEN_OFFSETS = (0,)  # AUDIT 21 nov 2026: fixed opening 16:30 server time (9:30 New York), no detection
MIN_SESSION_FRAC = 0.9
MIN_TRADES = 100
MIN_ATTEMPTS = 20
SLIP_MULT = (0, 1, 2)
SEED_NULL = 43
USD_PER_POINT = 20.0        # 1 NQ contract (section 4.7)
FIRMS = {                   # K2 (section 6); ratio = consistency (best day / target)
    "firm_a": {"start": 50000.0, "target": 3000.0, "mll": 2000.0, "lock_above_start": 0.0, "ratio": 0.55},
    "firm_b":   {"start": 25000.0, "target": 1250.0, "mll": 1000.0, "lock_above_start": 100.0, "ratio": 0.40},
}
MIN_DAYS_TRADED = 2
NOISE_SUBSTEPS = 60
NOISE_DAYS = 1500
NOISE_SPREAD = 1.0          # section 7
NOISE_START = 15000.0       # section 7
NOISE_VOL = 0.20            # [implementation choice, as test H/N]
NOISE_TICKVOL_RTH = 100     # [implementation choice, as test N]
NOISE_TICKVOL_OUT = 20


# ------------------------------------------------------------ reading (as test N)
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
    out = pd.DataFrame({"open": df["open"].astype(float).values, "high": df["high"].astype(float).values,
                        "low": df["low"].astype(float).values, "close": df["close"].astype(float).values,
                        "vol": df["tickvol"].astype(float).values, "spread": df["spread"].astype(float).values},
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


# ------------------------------------------------------------ candles and indicators (sections 4.1-4.3)
def session_window(d, session):
    if session == "rth":
        k = detect_open(d)
        return (None, None) if k is None else (k, RTH_LEN)
    return FULL_START, FULL_LEN


def make_bars(d, session="rth", equal_weight=False):
    """5-minute candles of the session, VWAP per candle close. None for an invalid day."""
    k_open, slen = session_window(d, session)
    if k_open is None:
        return None
    nb = slen // BAR
    m = d["min"]
    sel = (m >= k_open) & (m < k_open + slen)
    if sel.sum() < MIN_SESSION_FRAC * slen:
        return None
    idx = np.flatnonzero(sel)
    b = (m[idx] - k_open) // BAR
    if len(np.unique(b)) < nb:            # [implementation choice, as test N] every candle needs a minute
        return None
    o, h, l, c, v, sp = (d[k][idx] for k in ("o", "h", "l", "c", "v", "sp"))
    first = np.searchsorted(b, np.arange(nb), "left")
    last = np.searchsorted(b, np.arange(nb), "right") - 1
    px = (o + h + l + c) / 4.0
    w = np.ones_like(v) if equal_weight else v
    cpw, cw = np.cumsum(px * w), np.cumsum(w)
    cpe, ce = np.cumsum(px), np.arange(1, len(px) + 1)
    vw = np.where(cw[last] > 0, cpw[last] / np.where(cw[last] > 0, cw[last], 1), cpe[last] / ce[last])
    return {"day": d["day"], "k_open": k_open, "nb": nb, "O": o[first], "H": np.maximum.reduceat(h, first),
            "L": np.minimum.reduceat(l, first), "C": c[last], "SP": sp[first], "VW": vw}


def ema_series(x, n=EMA_LEN):
    a = 2.0 / (n + 1)
    out = np.empty(len(x))
    s = x[0]
    for i, xi in enumerate(x):
        s = xi if i == 0 else a * xi + (1 - a) * s
        out[i] = s
    return out


def prepare(days, session="rth", equal_weight=False):
    bars = [b for b in (make_bars(d, session, equal_weight) for d in days) if b is not None]
    if not bars:
        return bars
    e = ema_series(np.concatenate([b["C"] for b in bars]))
    i = 0
    for b in bars:
        b["E"] = e[i:i + b["nb"]]
        i += b["nb"]
    return bars


# ------------------------------------------------------------ the rule (sections 4.4-4.6)
def worst_low(bar, eb, xk):
    """Lowest price of candles eb..xk (the minutes the position is open)."""
    return bar["L"][eb:xk + 1].min()


def rule_day(bar, cross_counts=False):
    """Long only. Rule 1 cross arms, rule 2 confirmation candle k >= t+1 (or t itself with cross_counts),
    entry at open k+1 (k+1 <= nb-2), rule 3 exit at open j+1 after close(j) < EMA9(j), j >= entry candle,
    end of day at the close of the last candle. Returns (eb, xk, ep, xp, esp, worst, why)."""
    O, C, E, VW, SP, nb = bar["O"], bar["C"], bar["E"], bar["VW"], bar["SP"], bar["nb"]
    out = []
    pos, armed, eb, ep, esp = False, False, 0, 0.0, 0.0
    for t in range(nb):
        if pos:
            if t == nb - 1:
                out.append((eb, t, ep, C[t], esp, worst_low(bar, eb, t), "eod"))
                pos = False
            elif t >= eb and C[t] < E[t]:
                out.append((eb, t, ep, O[t + 1], esp, min(worst_low(bar, eb, t), O[t + 1]), "ema"))
                pos = False
            continue                       # a cross while the position is open lapses (4.6)
        cross = t >= 1 and E[t - 1] <= VW[t - 1] and E[t] > VW[t]
        if cross:
            armed = True
            if not cross_counts:
                continue
        if armed:
            if E[t] <= VW[t]:
                armed = False
            elif C[t] > E[t] and t <= nb - 3:
                pos, armed, eb, ep, esp = True, False, t + 1, O[t + 1], SP[t + 1]
    return out


def run_rule(bars, d_from=None, d_to=None, cross_counts=False):
    rows = []
    for b in bars:
        if (d_from is not None and b["day"] < d_from) or (d_to is not None and b["day"] > d_to):
            continue
        for eb, xk, ep, xp, esp, wl, why in rule_day(b, cross_counts):
            rows.append({"day": b["day"], "entry_bar": eb, "exit_bar": xk, "entry": ep, "exit": xp,
                         "spread": esp, "gross": xp - ep, "worst": wl - ep, "why": why})
    return pd.DataFrame(rows, columns=["day", "entry_bar", "exit_bar", "entry", "exit", "spread",
                                       "gross", "worst", "why"])


def net_pts(df, slip):
    return df["gross"] - df["spread"] - 2 * slip


# ------------------------------------------------------------ Null A (section 5)
def null_tables(bar, slip):
    """For every decision candle t (1..nb-3): eligible (close above EMA9), net result, worst open result
    (both after costs), next decision candle after the trade. Exit as the rule."""
    O, C, E, SP, nb = bar["O"], bar["C"], bar["E"], bar["SP"], bar["nb"]
    elig = np.zeros(nb, dtype=bool)
    net = np.zeros(nb)
    wst = np.zeros(nb)
    nxt = np.arange(1, nb + 1)
    for t in range(1, nb - 2):
        if not C[t] > E[t]:
            continue
        elig[t] = True
        ep, k = O[t + 1], t + 1
        while k < nb - 1 and not C[k] < E[k]:
            k += 1
        if k == nb - 1:
            xp, wl = C[k], worst_low(bar, t + 1, k)
        else:
            xp, wl = O[k + 1], min(worst_low(bar, t + 1, k), O[k + 1])
        cost = SP[t + 1] + 2 * slip
        net[t] = xp - ep - cost
        wst[t] = wl - ep - cost
        nxt[t] = k + 1
    return elig, net, wst, nxt


def expected_trades(tables, p):
    total = 0.0
    for elig, _, _, nxt in tables:
        nb = len(elig)
        f = np.zeros(nb + 2)
        for t in range(nb - 1, 0, -1):
            q = p if elig[t] else 0.0
            f[t] = q * (1 + f[min(nxt[t], nb)]) + (1 - q) * f[t + 1]
        total += f[1]
    return total


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


def null_a(tables, p, rng, n, daily=False):
    """n runs. Returns mean net per trade and trade count per run; with daily=True also per-day
    realized result R (points) and lowest intraday equity M (points, relative to the day start, <= 0)."""
    S, N = np.zeros(n), np.zeros(n)
    R = np.zeros((len(tables), n)) if daily else None
    M = np.zeros((len(tables), n)) if daily else None
    for di, (elig, net, wst, nxt) in enumerate(tables):
        nb = len(elig)
        cur = np.ones(n, dtype=int)
        real = np.zeros(n)
        low = np.zeros(n)
        for t in range(1, nb - 2):
            act = cur == t
            if not act.any():
                continue
            if not elig[t]:
                cur[act] = t + 1
                continue
            take = act & (rng.random(n) < p)
            S[take] += net[t]
            N[take] += 1
            if daily:
                low[take] = np.minimum(low[take], real[take] + wst[t])
                real[take] += net[t]
                low[take] = np.minimum(low[take], real[take])
            cur[take] = nxt[t]
            cur[act & ~take] = t + 1
        if daily:
            R[di], M[di] = real, low
    return np.where(N > 0, S / np.maximum(N, 1), np.nan), N, R, M


# ------------------------------------------------------------ prop firm challenge (section 6)
def day_series(df, slip, days, contracts=1):
    """Per valid session in `days`: realized result R and lowest equity M (dollars, M <= 0)."""
    R = np.zeros(len(days))
    M = np.zeros(len(days))
    pos = {d: i for i, d in enumerate(days)}
    mult = USD_PER_POINT * contracts
    for d, g in df.groupby("day"):
        i = pos[d]
        cost = g["spread"].values + 2 * slip
        real, low = 0.0, 0.0
        for net, w in zip(g["gross"].values - cost, g["worst"].values - cost):
            low = min(low, real + w * mult)
            real += net * mult
            low = min(low, real)
        R[i], M[i] = real, low
    return R, M


def challenge(R, M, start, firm):
    """One attempt starting at day index `start`. Returns ('pass'|'fail'|'open', end index, days used)."""
    f = FIRMS[firm]
    s0 = f["start"]
    bal, peak, mll = s0, s0, s0 - f["mll"]
    lock = s0 + f["lock_above_start"]
    best, traded = 0.0, 0
    for i in range(start, len(R)):
        if bal + M[i] <= mll:
            return "fail", i, i - start + 1
        bal += R[i]
        if R[i] != 0 or M[i] != 0:
            traded += 1
        best = max(best, R[i])
        target = max(f["target"], best / f["ratio"])
        if bal - s0 >= target and traded >= MIN_DAYS_TRADED:
            return "pass", i, i - start + 1
        peak = max(peak, bal)
        mll = max(mll, min(lock, peak - f["mll"]))
    return "open", len(R) - 1, len(R) - start


def sequential(R, M, firm):
    """Attempts in sequence (deciding, section 6)."""
    res, i = [], 0
    while i < len(R):
        out, end, used = challenge(R, M, i, firm)
        res.append((out, i, end, used))
        if out == "open":
            break
        i = end + 1
    return res


def seq_vectorized(R, M, firm):
    """Pass rate of attempts in sequence for many runs at once (columns of R and M). Returns passed, done."""
    f = FIRMS[firm]
    D, n = R.shape
    s0, lock = f["start"], f["start"] + f["lock_above_start"]
    bal = np.full(n, s0); peak = bal.copy(); mll = np.full(n, s0 - f["mll"])
    best = np.zeros(n); traded = np.zeros(n)
    passed = np.zeros(n); done = np.zeros(n)
    for i in range(D):
        r, m = R[i], M[i]
        fail = bal + m <= mll
        bal = bal + r
        traded = traded + ((r != 0) | (m != 0))
        best = np.maximum(best, r)
        target = np.maximum(f["target"], best / f["ratio"])
        ps = ~fail & (bal - s0 >= target) & (traded >= MIN_DAYS_TRADED)
        end = fail | ps
        passed += ps; done += end
        peak = np.maximum(peak, bal)
        mll = np.maximum(mll, np.minimum(lock, peak - f["mll"]))
        bal[end] = s0; peak[end] = s0; mll[end] = s0 - f["mll"]; best[end] = 0; traded[end] = 0
    return passed, done


# ------------------------------------------------------------ statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    hw = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return c - hw, c + hw


def day_boot(df, rng, B=10000):
    """95% interval of mean net per trade and of the profit factor, bootstrap per trading day."""
    g = df.groupby("day")["net"]
    s, c = g.sum().values, g.count().values
    gp = df.assign(p=df["net"].clip(lower=0), q=(-df["net"]).clip(lower=0)).groupby("day")[["p", "q"]].sum()
    P, Q = gp["p"].values, gp["q"].values
    D = len(s)
    mean, pfs = np.empty(B), np.empty(B)
    for a in range(0, B, 500):
        bb = min(500, B - a)
        idx = rng.integers(0, D, (bb, D))
        mean[a:a + bb] = s[idx].sum(1) / c[idx].sum(1)
        qq = Q[idx].sum(1)
        pfs[a:a + bb] = np.where(qq > 0, P[idx].sum(1) / np.where(qq > 0, qq, 1), np.inf)
    return np.percentile(mean, [2.5, 97.5]), np.percentile(pfs, [2.5, 97.5])


def pf(x):
    g, l = x[x > 0].sum(), -x[x < 0].sum()
    return np.inf if l == 0 else g / l


# ------------------------------------------------------------ selftest
def second_rule(bar):
    """Independent re-implementation of rules 1-3, driven by the list of crossings, for the selftest."""
    C, E, V, nb = bar["C"], bar["E"], bar["VW"], bar["nb"]
    crosses = [t for t in range(1, nb) if E[t - 1] <= V[t - 1] and E[t] > V[t]]
    trades, free_from = [], 1
    for t in crosses:
        if t < free_from:
            continue                       # crossing while a position was open: lapses
        entry = None
        for k in range(t + 1, nb):
            if E[k] <= V[k]:
                break                      # EMA back below VWAP before confirmation
            if C[k] > E[k]:
                if k <= nb - 3:
                    entry = k + 1
                break
        if entry is None:
            continue
        j = next((j for j in range(entry, nb - 1) if C[j] < E[j]), nb - 1)
        trades.append((entry, j))
        free_from = j + 1
    return trades


def selftest():
    rng = np.random.default_rng(5)
    days = synth_days(rng, ndays=60)
    bars = prepare(days)
    ok = True
    e2 = pd.Series(np.concatenate([b["C"] for b in bars])).ewm(span=EMA_LEN, adjust=False).mean().values
    d_ema = np.abs(np.concatenate([b["E"] for b in bars]) - e2).max()
    print(f"EMA9 vs pandas ewm(adjust=False): max diff {d_ema:.2e}")
    ok &= d_ema < 1e-9
    worst = 0.0
    for d in days:
        b = make_bars(d)
        if b is None:
            continue
        k = b["k_open"]
        sel = (d["min"] >= k) & (d["min"] < k + RTH_LEN)
        mm, oo, hh, ll, cc, vv = (d[x][sel] for x in ("min", "o", "h", "l", "c", "v"))
        for j in range(b["nb"]):
            upto = mm < k + BAR * (j + 1)
            p = (oo[upto] + hh[upto] + ll[upto] + cc[upto]) / 4
            worst = max(worst, abs((p * vv[upto]).sum() / vv[upto].sum() - b["VW"][j]))
    print(f"VWAP vs per-candle recomputation: max diff {worst:.2e}")
    ok &= worst < 1e-9
    n1 = n2 = mism = 0
    for b in bars:
        a = [(eb, xk) for eb, xk, *_ in rule_day(b)]
        c = second_rule(b)
        n1 += len(a); n2 += len(c); mism += a != c
    print(f"rule vs second implementation: trades {n1} vs {n2}, days with a difference {mism} of {len(bars)}")
    ok &= mism == 0 and n1 > 0
    # challenge against hand calculations (firm A 50K: target 3000, MLL 2000 trailing EOD, lock at 50000, 55%)
    cases = [
        ("three days of +1000/+1000/+1100", [1000, 1000, 1100], [0, 0, 0], ("pass", 2)),
        ("best day 2000 raises target to 3636.36", [2000, 1000, 600, 100], [0, 0, 0, 0], ("pass", 3)),
        ("-1500 then open loss 600 touches 48000", [-1500, 0], [-1500, -600], ("fail", 1)),
        ("trailing: +1500 then open loss 2100", [1500, 0], [0, -2100], ("fail", 1)),
        ("lock at start: +2500 then open loss 2400", [2500, -2400, 0], [0, -2400, -1], ("open", 2)),
        ("lock at start: +2500 then open loss 2500", [2500, 0], [0, -2500], ("fail", 1)),
        ("one day of +3000 is not enough", [3000], [0], ("open", 0)),
    ]
    for name, R, M, exp in cases:
        out, end, _ = challenge(np.array(R, float), np.array(M, float), 0, "firm_a")
        good = (out, end) == exp
        ok &= good
        print(f"challenge case '{name}': {out} at day {end}, expected {exp[0]} at day {exp[1]} -> {'OK' if good else 'WRONG'}")
    Rr = rng.normal(0, 800, (300, 50)); Mm = np.minimum(0, Rr - np.abs(rng.normal(0, 500, (300, 50))))
    pv, dv = seq_vectorized(Rr, Mm, "firm_a")
    same = all((sum(o == "pass" for o, *_ in sequential(Rr[:, j], Mm[:, j], "firm_a")),
                sum(o != "open" for o, *_ in sequential(Rr[:, j], Mm[:, j], "firm_a"))) == (pv[j], dv[j])
               for j in range(50))
    print(f"vectorized challenge vs loop on 50 random runs: {'equal' if same else 'DIFFERENT'}")
    ok &= same
    tables = [null_tables(b, 0.0) for b in bars]
    p = calibrate_p(tables, n1)
    m, N, _, _ = null_a(tables, p, rng, 4000)
    print(f"Null A: calibrated p {p:.4f}, expected trades {expected_trades(tables, p):.1f}, "
          f"simulated mean {N.mean():.1f}, target {n1}")
    ok &= abs(N.mean() - n1) / n1 < 0.03
    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    return ok


# ------------------------------------------------------------ noise check (section 7)
def synth_days(rng, ndays=NOISE_DAYS):
    var_day = (NOISE_VOL ** 2) / 252
    mins = np.arange(60, 1440)
    in_rth = (mins >= RTH_START) & (mins < RTH_START + RTH_LEN)
    var_min = np.where(in_rth, 0.7 * var_day / RTH_LEN, 0.3 * var_day / (len(mins) - RTH_LEN))
    sd_sub = np.sqrt(var_min / NOISE_SUBSTEPS)
    days, logp = [], np.log(NOISE_START)
    lam = np.where(in_rth, NOISE_TICKVOL_RTH, NOISE_TICKVOL_OUT)
    for day in pd.bdate_range("2010-01-04", periods=ndays):
        steps = rng.standard_normal((len(mins), NOISE_SUBSTEPS)) * sd_sub[:, None]
        path = logp + np.cumsum(steps.ravel()).reshape(len(mins), NOISE_SUBSTEPS)
        prev = np.r_[logp, path[:-1, -1]]
        days.append({"day": day, "min": mins, "o": np.exp(prev), "c": np.exp(path[:, -1]),
                     "h": np.exp(np.maximum(path.max(1), prev)), "l": np.exp(np.minimum(path.min(1), prev)),
                     "v": rng.poisson(lam).astype(float) + 1.0, "sp": np.full(len(mins), NOISE_SPREAD)})
        logp = path[-1, -1]
    return days


def measure(bars, slip, rng, n, nprop, firm, contracts=1):
    """Rule, Null A (mean net) and the challenge for the rule and for Null A. Returns a dict."""
    days = [b["day"] for b in bars]
    df = run_rule(bars)
    x = net_pts(df, slip)
    tables = [null_tables(b, slip) for b in bars]
    p = calibrate_p(tables, len(df))
    m, N, _, _ = null_a(tables, p, rng, n)
    R, M = day_series(df, slip, days, contracts)
    seq = sequential(R, M, firm)
    k = sum(o == "pass" for o, *_ in seq)
    done = sum(o != "open" for o, *_ in seq)
    _, _, Rn, Mn = null_a(tables, p, rng, nprop, daily=True)
    pv, dv = seq_vectorized(Rn * USD_PER_POINT * contracts, Mn * USD_PER_POINT * contracts, firm)
    nul_rate = np.where(dv > 0, pv / np.maximum(dv, 1), np.nan)
    rate = k / done if done else np.nan
    return {"df": df, "x": x, "p": p, "m": m, "N": N, "pct": 100 * (m < x.mean()).mean(),
            "ties": int((m == x.mean()).sum()), "seq": seq, "passed": k, "done": done, "rate": rate,
            "nul_rate": nul_rate, "pct_rate": 100 * np.nanmean(nul_rate < rate),
            "ties_rate": int(np.sum(nul_rate == rate)), "R": R, "M": M, "tables": tables}


def noise_check(sets, seed, slip, n):
    rng = np.random.default_rng(seed)
    p1, p2 = [], []
    print(f"noise check: {sets} sets of {NOISE_DAYS} days, seed {seed}, slip {slip}, Null A runs {n}, "
          f"start {NOISE_START}, vol {NOISE_VOL}, spread {NOISE_SPREAD}, sub-steps {NOISE_SUBSTEPS}, firm firm_a",
          flush=True)
    for s in range(sets):
        bars = prepare(synth_days(rng))
        r = measure(bars, slip, rng, n, n, "firm_a")
        p1.append(r["pct"]); p2.append(r["pct_rate"])
        print(f"set {s+1:2d}: trades {len(r['df']):5d} per day {len(r['df'])/len(bars):4.2f} | gross win rate "
              f"{100*(r['df']['gross']>0).mean():5.1f}% | mean net {r['x'].mean():+.3f} pt | percentile mean net "
              f"{r['pct']:5.1f} | challenges {r['done']} passed {r['passed']} rate {100*r['rate']:5.1f}% | "
              f"Null A rate {100*np.nanmean(r['nul_rate']):5.1f}% | percentile pass rate {r['pct_rate']:5.1f}",
              flush=True)
    p1, p2 = np.array(p1), np.array(p2)
    ok1 = 35 <= p1.mean() <= 65 and (p1 > 95).sum() <= 3
    ok2 = 35 <= p2.mean() <= 65 and (p2 > 95).sum() <= 3
    print(f"mean net: mean percentile {p1.mean():.1f}, above 95: {(p1 > 95).sum()} of {len(p1)} -> {'OK' if ok1 else 'NOT OK'}")
    print(f"pass rate: mean percentile {p2.mean():.1f}, above 95: {(p2 > 95).sum()} of {len(p2)} -> {'OK' if ok2 else 'NOT OK'}")
    print("NOISE CHECK " + ("PASSED" if ok1 and ok2 else "FAILED") + " (bounds: mean 35-65, at most 3 of 24 above 95)")
    return ok1 and ok2


# ------------------------------------------------------------ data check (section 8, metadata only)
def datacheck(days, session):
    rows = []
    for d in days:
        k, slen = session_window(d, session)
        m = d["min"]
        sel = (m >= k) & (m < k + slen) if k is not None else np.zeros(len(m), bool)
        rows.append({"year": d["day"].year, "valid": make_bars(d, session) is not None, "minutes": int(sel.sum()),
                     "spread_empty": float((d["sp"][sel] <= 0).mean()) if sel.any() else np.nan,
                     "zero_vol": float((d["v"][sel] <= 0).mean()) if sel.any() else np.nan})
    f = pd.DataFrame(rows)
    print(f"session {session} | year | days | valid sessions | minutes median | spread empty % | tick volume zero %")
    for y, g in f.groupby("year"):
        v = g[g["valid"]]
        print(f"{y} | {len(g)} | {len(v)} | {v['minutes'].median() if len(v) else float('nan'):.0f} | "
              f"{100*v['spread_empty'].mean() if len(v) else float('nan'):.1f} | "
              f"{100*v['zero_vol'].mean() if len(v) else float('nan'):.2f}")


# ------------------------------------------------------------ report
def trade_line(df, slip, rng, label):
    df = df.assign(net=net_pts(df, slip))
    k = int((df["net"] > 0).sum())
    lo, hi = wilson(k, len(df))
    ci, cpf = day_boot(df, rng)
    w, l = df.loc[df["net"] > 0, "net"], df.loc[df["net"] < 0, "net"]
    nd = df["day"].nunique()
    line = (f"{label}: trades {len(df)}, days with trades {nd}, per day {len(df)/max(nd,1):.2f} | win rate net "
            f"{100*k/len(df):.1f}% ({100*lo:.1f}-{100*hi:.1f}), gross {100*(df['gross']>0).mean():.1f}% | mean net "
            f"{df['net'].mean():+.3f} pt ({ci[0]:+.3f} to {ci[1]:+.3f}) = ${USD_PER_POINT*df['net'].mean():+.2f} | "
            f"PF {pf(df['net'].values):.2f} ({cpf[0]:.2f}-{cpf[1]:.2f}) | avg win ${USD_PER_POINT*w.mean():.2f}, "
            f"avg loss ${USD_PER_POINT*l.mean():.2f} | gross {df['gross'].mean():+.3f} pt")
    if len(df) < MIN_TRADES:
        line += " | INSUFFICIENT TRADES"
    return line, (lo, hi), ci, cpf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--datacheck", action="store_true")
    ap.add_argument("--sets", type=int, default=24)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--slip", type=float, default=1.0)
    ap.add_argument("--point", type=float, default=0.01)
    ap.add_argument("--session", default="rth", choices=["rth", "full"])
    ap.add_argument("--firm", default="firm_a", choices=list(FIRMS))
    ap.add_argument("--from", dest="d_from", default="2023-11-17")
    ap.add_argument("--to", dest="d_to", default="2026-11-05")
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--nprop", type=int, default=2000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default="USTEC")
    ap.add_argument("--short", action="store_true", help="main measurement only, no variants")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.noise:
        sys.exit(0 if noise_check(a.sets, 7 if a.seed is None else a.seed, a.slip,
                                  2000 if a.n is None else a.n) else 1)
    days = build_days(load_mt5(a.csv), a.point)
    if a.datacheck:
        datacheck(days, a.session)
        return

    seed = SEED_NULL if a.seed is None else a.seed
    n = 10000 if a.n is None else a.n
    rng = np.random.default_rng(seed)
    d_from, d_to = pd.Timestamp(a.d_from), pd.Timestamp(a.d_to)
    out = a.out or "."
    os.makedirs(out, exist_ok=True)
    tag = f"{a.label}_{a.session}_{a.firm}"
    fo = open(os.path.join(out, f"run01_{tag}.txt"), "w", encoding="utf-8")

    def say(s=""):
        print(s, flush=True); fo.write(s + "\n")

    say(f"vwap_prop.py run on {a.label}: {os.path.basename(a.csv)}, session {a.session}, firm {a.firm}, point {a.point}, "
        f"slip {a.slip}, P1 {a.d_from} to {a.d_to}, Null A runs {n}, challenge runs {a.nprop}, seed {seed}")
    bars = prepare(days, a.session)
    inper = [b for b in bars if d_from <= b["day"] <= d_to]
    say(f"valid sessions in P1: {len(inper)} (all valid sessions in the file: {len(bars)})")

    r = measure(inper, a.slip, rng, n, a.nprop, a.firm)
    df = r["df"]
    df.assign(net=r["x"]).to_csv(os.path.join(out, f"trades_{tag}.csv"), index=False)
    say("\n== P1, deciding for C1 to C4 (C5 descriptive since v1.1) ==")
    line, wr, ci, cpf = trade_line(df, a.slip, rng, "P1")
    say(line)
    say(f"Null A: p {r['p']:.4f}, mean trades {r['N'].mean():.0f}, mean net {np.nanmean(r['m']):+.3f} pt, "
        f"percentile {r['pct']:.1f} (ties {r['ties']})")
    lo, hi = wilson(r["passed"], r["done"])
    running = [s for s in r["seq"] if s[0] == "open"]
    used = [u for o, _, _, u in r["seq"] if o != "open"]
    say(f"challenge {a.firm}, attempts in sequence: completed {r['done']}, passed {r['passed']}, failed "
        f"{r['done']-r['passed']}, running at the end {len(running)} | pass rate {100*r['rate']:.1f}% "
        f"({100*lo:.1f}-{100*hi:.1f}) | median days per attempt {np.median(used) if used else float('nan'):.0f}"
        + (" | INSUFFICIENT ATTEMPTS" if r["done"] < MIN_ATTEMPTS else ""))
    say(f"Null A in the same challenge: mean pass rate {100*np.nanmean(r['nul_rate']):.1f}% (5-95: "
        f"{100*np.nanpercentile(r['nul_rate'],5):.1f}-{100*np.nanpercentile(r['nul_rate'],95):.1f}), "
        f"percentile of the real pass rate {r['pct_rate']:.1f} (ties {r['ties_rate']})")
    for o, s, e, u in r["seq"]:
        say(f"  attempt {inper[s]['day'].date()} to {inper[e]['day'].date()}: {o}, {u} sessions")
    verdict = [f"C1 {'FALSIFIED' if wr[1] < 0.566 else 'not falsified'} (upper bound win rate {100*wr[1]:.1f}% vs 56.6%)",
               f"C2 {'FALSIFIED' if ci[1] < 0 or cpf[1] < 1.84 else 'not falsified'} (upper bound mean net {ci[1]:+.3f} pt, "
               f"upper bound PF {cpf[1]:.2f} vs 1.84)",
               f"C3 {'FALSIFIED' if r['pct'] <= 95 else 'not falsified'} (percentile {r['pct']:.1f})",
               f"C4 {'FALSIFIED' if hi < 0.85 else 'not falsified'} (upper bound pass rate {100*hi:.1f}% vs 85%)",
               f"C5 descriptive since v1.1 (percentile of the pass rate vs Null A {r['pct_rate']:.1f})"]
    say("")
    for v in verdict:
        say(v)
    if a.short:
        fo.close()
        return

    say("\n== Descriptive (section 10) ==")
    x = r["x"]
    dur = (df["exit_bar"] - df["entry_bar"] + 1) * BAR
    say(f"median duration {dur.median():.0f} min, mean {dur.mean():.1f} min | exit reasons {df['why'].value_counts().to_dict()}")
    say(f"largest loss {x.min():+.2f} pt on {df.loc[x.idxmin(), 'day'].date()}, largest gain {x.max():+.2f} pt | "
        f"mean spread at entry {df['spread'].mean():.3f} pt, cost per trade {(df['spread'] + 2*a.slip).mean():.3f} pt")
    for mult in SLIP_MULT:
        xx = df["gross"] - df["spread"] - 2 * a.slip * mult
        say(f"costs: spread + slip x{mult}: mean net {xx.mean():+.3f} pt, PF {pf(xx.values):.2f}, win rate {100*(xx>0).mean():.1f}%")
    for y, g in df.groupby(df["day"].dt.year):
        say(trade_line(g, a.slip, rng, f"year {y}")[0])
    days_p = [b["day"] for b in inper]
    starts = [challenge(r["R"], r["M"], i, a.firm)[0] for i in range(len(days_p))]
    fin = [s for s in starts if s != "open"]
    say(f"overlapping attempts (one per session): completed {len(fin)}, passed {sum(s == 'pass' for s in fin)}, "
        f"rate {100*np.mean([s == 'pass' for s in fin]) if fin else float('nan'):.1f}%")
    other = "firm_b" if a.firm == "firm_a" else "firm_a"
    for firm_v, contracts in ((other, 1), (a.firm, 2)):
        R2, M2 = day_series(df, a.slip, days_p, contracts)
        seq = sequential(R2, M2, firm_v)
        k2, d2 = sum(o == "pass" for o, *_ in seq), sum(o != "open" for o, *_ in seq)
        l2, h2 = wilson(k2, d2)
        say(f"challenge {firm_v}, {contracts} contract(s): completed {d2}, passed {k2}, rate "
            f"{100*k2/max(d2,1):.1f}% ({100*l2:.1f}-{100*h2:.1f})")
    say("\n== Variants, not deciding ==")
    say(trade_line(run_rule(inper, cross_counts=True), a.slip, rng, "crossing candle counts as confirmation")[0])
    bars_ew = [b for b in prepare(days, a.session, equal_weight=True) if d_from <= b["day"] <= d_to]
    say(trade_line(run_rule(bars_ew), a.slip, rng, "VWAP without volume")[0])
    early = [b for b in bars if pd.Timestamp("2019-01-01") <= b["day"] < d_from]
    if early:
        re_ = measure(early, a.slip, rng, min(n, 2000), min(a.nprop, 500), a.firm)
        say(trade_line(re_["df"], a.slip, rng, "2019 to 16 Nov 2023")[0])
        say(f"  Null A percentile {re_['pct']:.1f} | challenge completed {re_['done']}, passed {re_['passed']}, "
            f"rate {100*re_['rate']:.1f}%, Null A rate {100*np.nanmean(re_['nul_rate']):.1f}%")
    fo.close()


if __name__ == "__main__":
    main()
