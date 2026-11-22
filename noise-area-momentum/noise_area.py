#!/usr/bin/env python3
"""
noise_area.py · Nullius Research
Measurement script for test R (noise-area intraday momentum).
Hypothesis: hypothese-noise-area-momentum.md, version 1.2 (4.5 changed in v1.1, 4.1 in v1.2), approved 21 Nov 2026
(K1 A, K2 A, K3 A, K4 C, K5 A).

Usage:
    python noise_area.py --selftest                                   (rule against a second implementation, section 6)
    python noise_area.py --noise [--sets 24] [--seed 7] [--n 2000]    (noise check, section 6)
    python noise_area.py <M1.csv> --datacheck [--point 0.01]          (metadata only, section 7)
    python noise_area.py --real --ustec <USTEC_M1.csv> --us500 <US500_M1.csv>
                         [--point-ustec 0.01] [--point-us500 0.01] [--n 10000] [--out dir]

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
from numba import njit

# ------------------------------------------------------------ fixed choices (hypothesis sections 4 to 7)
RTH_START = 16 * 60 + 30     # 9:30 New York in server time (NY + 7), fixed all year (v1.2, section 4.1)
JUMP_MIN = 1.3              # section 4.1: report days whose tick volume 16:30-16:59 is not 1.3x that of 16:00-16:29
RTH_LEN = 390                # 9:30-16:00, minute bars
MIN_SESSION_FRAC = 0.9       # section 4.1
LOOKBACK = 14                # section 4.2
BAND_MULT = 1.0              # section 4.2
NCHK = 12                    # checks 10:00 ... 15:30 (section 4.4)
CHK = np.array([29 + 30 * k for k in range(NCHK)])   # bar that closes at the check time
EOD = NCHK                   # holding index meaning "closed at 16:00"
SLIP_USTEC = 1.0             # section 5, K5 A
SLIP_US500 = 0.25
SLIP_MULT = (0, 1, 2)
K5B_COST = 0.75              # section 3, K5 B: points per trade, no spread
MIN_TRADES = 100
SEED_NULL = 43
N_NULL = 10000
CLAIM_C1 = 6.8
P1_FROM, P1_TO = "2020-01-02", "2026-11-05"
AFTER_PAPER = "2024-05-14"
EARLY_FROM, EARLY_TO = "2017-01-01", "2019-12-31"
NOISE_SUBSTEPS = 60
NOISE_DAYS = 1500
NOISE_SPREAD = 1.0
NOISE_START = 4000.0         # as test N
NOISE_VOL = 0.20             # as test N
NOISE_OVERNIGHT = 0.3        # [implementation choice] overnight jump sd as a fraction of the daily sd ("small")
NOISE_TICKVOL = 100          # [implementation choice] Poisson mean of tick volume per minute


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
    out = pd.DataFrame({"open": df["open"].astype(float).values,
                        "high": df["high"].astype(float).values,
                        "low": df["low"].astype(float).values,
                        "close": df["close"].astype(float).values,
                        "vol": df["tickvol"].astype(float).values,
                        "spread": df["spread"].astype(float).values},
                       index=pd.DatetimeIndex(ts, name="ts"))
    out = out[~out.index.isna()]
    return out[~out.index.duplicated(keep="first")].sort_index()


def split_days(m1, point):
    minute = (m1.index.hour * 60 + m1.index.minute).values
    date = m1.index.normalize()
    o, h, l, c = (m1[k].values for k in ("open", "high", "low", "close"))
    v, sp = m1["vol"].values, m1["spread"].values * point
    bounds = np.flatnonzero(np.r_[True, date[1:] != date[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        yield {"day": date[a], "min": minute[a:b], "o": o[a:b], "h": h[a:b],
               "l": l[a:b], "c": c[a:b], "v": v[a:b], "sp": sp[a:b]}


def open_jump(d):
    """Ratio of mean tick volume 16:30-16:59 to 16:00-16:29 server time (reported only, section 4.1)."""
    full = np.zeros(1440)
    full[d["min"]] = d["v"]
    pre = full[RTH_START - 30:RTH_START].mean()
    post = full[RTH_START:RTH_START + 30].mean()
    return post / pre if pre > 0 else np.inf


def session_arrays(d):
    """390 minute bars of the regular session, or None (section 4.1).
    [implementation choice] a missing minute gets o=h=l=c = previous close, volume 0, previous spread;
    a missing first minute takes the first available open."""
    k_open = RTH_START                     # v1.2: fixed opening, no detection
    m = d["min"]
    sel = (m >= k_open) & (m < k_open + RTH_LEN)
    if sel.sum() < MIN_SESSION_FRAC * RTH_LEN:
        return None
    idx = np.flatnonzero(sel)
    pos = m[idx] - k_open
    arr = {k: np.full(RTH_LEN, np.nan) for k in ("o", "h", "l", "c", "v", "sp")}
    for k in arr:
        arr[k][pos] = d[k][idx]
    first = idx[0]
    if np.isnan(arr["o"][0]):
        arr["o"][0] = d["o"][first]
        arr["h"][0] = arr["l"][0] = arr["c"][0] = d["o"][first]
        arr["v"][0] = 0.0
        arr["sp"][0] = d["sp"][first]
    for t in range(1, RTH_LEN):
        if np.isnan(arr["c"][t]):
            p = arr["c"][t - 1]
            arr["o"][t] = arr["h"][t] = arr["l"][t] = arr["c"][t] = p
            arr["v"][t] = 0.0
            arr["sp"][t] = arr["sp"][t - 1]
    arr["day"] = d["day"]
    arr["k_open"] = k_open
    arr["jump"] = open_jump(d)
    return arr


# ------------------------------------------------------------ per-day check values (sections 4.2-4.4)
def day_tables(sess, equal_weight=False):
    """Stack valid sessions into check-level tables.
    Returns dict with, per day i and check k: P (close at check), VW (VWAP at check), MOVE (|P/O-1|),
    FILL (open of the bar after the check), SPF (spread at that bar), plus O, CL (16:00 close)."""
    n = len(sess)
    P = np.empty((n, NCHK)); VW = np.empty((n, NCHK)); FILL = np.empty((n, NCHK)); SPF = np.empty((n, NCHK))
    O = np.empty(n); CL = np.empty(n)
    for i, s in enumerate(sess):
        o, h, l, c, v = s["o"], s["h"], s["l"], s["c"], s["v"]
        px = (h + l + c) / 3.0
        w = np.ones(RTH_LEN) if equal_weight else v
        cpw, cw = np.cumsum(px * w), np.cumsum(w)
        cpe, ce = np.cumsum(px), np.arange(1, RTH_LEN + 1)
        t = CHK
        vw = np.where(cw[t] > 0, cpw[t] / np.where(cw[t] > 0, cw[t], 1.0), cpe[t] / ce[t])
        P[i], VW[i] = c[t], vw
        FILL[i], SPF[i] = o[t + 1], s["sp"][t + 1]
        O[i], CL[i] = o[0], c[RTH_LEN - 1]
    MOVE = np.abs(P / O[:, None] - 1.0)
    SIG = np.full((n, NCHK), np.nan)
    for i in range(LOOKBACK, n):
        SIG[i] = MOVE[i - LOOKBACK:i].mean(axis=0)
    CPREV = np.r_[np.nan, CL[:-1]]
    UB = np.maximum(O, CPREV)[:, None] * (1.0 + BAND_MULT * SIG)
    LB = np.minimum(O, CPREV)[:, None] * (1.0 - BAND_MULT * SIG)
    days = pd.DatetimeIndex([s["day"] for s in sess])
    return {"days": days, "P": P, "VW": VW, "FILL": FILL, "SPF": SPF, "O": O, "CL": CL,
            "UB": UB, "LB": LB, "SIG": SIG}


# ------------------------------------------------------------ the rule (sections 4.5-4.7)
@njit(cache=True)
def _put(out, m, a, b, c, d, e, f, g):
    out[m, 0] = a; out[m, 1] = b; out[m, 2] = c; out[m, 3] = d
    out[m, 4] = e; out[m, 5] = f; out[m, 6] = g


@njit(cache=True)
def _rule(P, VW, UB, LB, FILL, SPF, CL, active, vwap_entry):
    n = P.shape[0]
    out = np.zeros((n * NCHK + n, 7))   # day, side, k_in, k_out, entry, exit, spread
    m = 0
    for i in range(n):
        if not active[i]:
            continue
        pos = 0
        kin = 0
        ep = 0.0
        esp = 0.0
        for k in range(NCHK):
            p = P[i, k]
            closed = 0                      # direction closed at this check (v1.1, section 4.5)
            if pos > 0 and p < max(UB[i, k], VW[i, k]):
                _put(out, m, i, pos, kin, k, ep, FILL[i, k], esp); m += 1; closed = 1; pos = 0
            elif pos < 0 and p > min(LB[i, k], VW[i, k]):
                _put(out, m, i, pos, kin, k, ep, FILL[i, k], esp); m += 1; closed = -1; pos = 0
            if pos == 0:
                if closed != 1 and p > UB[i, k] and (not vwap_entry or p > VW[i, k]):
                    pos = 1
                elif closed != -1 and p < LB[i, k] and (not vwap_entry or p < VW[i, k]):
                    pos = -1
                if pos != 0:
                    kin = k; ep = FILL[i, k]; esp = SPF[i, k]
        if pos != 0:
            _put(out, m, i, pos, kin, EOD, ep, CL[i], esp); m += 1
    return out[:m]


def run_rule(T, mask, vwap_entry=False):
    active = mask & ~np.isnan(T["SIG"][:, 0]) & ~np.isnan(T["UB"][:, 0])
    r = _rule(T["P"], T["VW"], T["UB"], T["LB"], T["FILL"], T["SPF"], T["CL"], active, vwap_entry)
    df = pd.DataFrame(r, columns=["i", "side", "k_in", "k_out", "entry", "exit", "spread"])
    for c in ("i", "side", "k_in", "k_out"):
        df[c] = df[c].astype(int)
    df["day"] = T["days"][df["i"].values]
    df["gross"] = df["side"] * (df["exit"] - df["entry"])
    df["hold"] = df["k_out"] - df["k_in"]
    return df, active


def net_of(df, slip, spread=True, flat=None):
    if flat is not None:
        return df["gross"].values - flat
    return df["gross"].values - (df["spread"].values if spread else 0.0) - 2.0 * slip


# ------------------------------------------------------------ control groups (section 5)
@njit(cache=True)
def _null_b(FILL, SPF, CL, act_idx, holds, p, slip, nruns, seed, flat):
    """Sequential random process. Returns mean net per trade and trade count per run."""
    np.random.seed(seed)
    means = np.empty(nruns)
    counts = np.empty(nruns)
    nh = holds.shape[0]
    for r in range(nruns):
        tot = 0.0
        cnt = 0
        for ii in range(act_idx.shape[0]):
            i = act_idx[ii]
            pos = 0
            kout = 0
            ep = 0.0
            esp = 0.0
            for k in range(NCHK):
                if pos != 0 and k == kout:
                    g = pos * (FILL[i, k] - ep)
                    tot += g - (flat if flat >= 0 else esp + 2.0 * slip)
                    cnt += 1
                    pos = 0
                if pos == 0 and np.random.random() < p:
                    pos = 1 if np.random.random() < 0.5 else -1
                    h = holds[np.random.randint(nh)]
                    kout = k + h
                    ep = FILL[i, k]
                    esp = SPF[i, k]
            if pos != 0:
                g = pos * (CL[i] - ep)
                tot += g - (flat if flat >= 0 else esp + 2.0 * slip)
                cnt += 1
        means[r] = tot / cnt if cnt > 0 else 0.0
        counts[r] = cnt
    return means, counts


def null_b(T, active, real, slip, nruns, seed=SEED_NULL, flat=None):
    holds = real["hold"].values.astype(np.int64)
    act_idx = np.flatnonzero(active).astype(np.int64)
    target = len(real)
    fl = -1.0 if flat is None else float(flat)
    lo, hi = 1e-4, 0.999
    for _ in range(40):           # [implementation choice] bisection on p with 200 calibration runs
        mid = 0.5 * (lo + hi)
        _, c = _null_b(T["FILL"], T["SPF"], T["CL"], act_idx, holds, mid, slip, 200, seed + 1, fl)
        if c.mean() < target:
            lo = mid
        else:
            hi = mid
    p = 0.5 * (lo + hi)
    means, counts = _null_b(T["FILL"], T["SPF"], T["CL"], act_idx, holds, p, slip, nruns, seed, fl)
    return means, counts, p


def null_a(real, net, nruns, seed=SEED_NULL):
    rng = np.random.default_rng(seed)
    g = real["gross"].values
    cost = g - net
    out = np.empty(nruns)
    for r in range(nruns):
        s = rng.choice((-1.0, 1.0), size=len(g))
        out[r] = (s * g - cost).mean()
    return out


def pct(real_mean, null):
    lt = (null < real_mean).mean() * 100
    eq = (null == real_mean).mean() * 100
    return lt + 0.5 * eq, lt, lt + eq


def day_boot_ci(real, net, active_days, nruns=N_NULL, seed=SEED_NULL):
    """95% interval of the mean net per trade, bootstrap over trading days (incl. days without trades)."""
    rng = np.random.default_rng(seed)
    dsum = pd.Series(net).groupby(real["i"].values).sum()
    dcnt = real.groupby("i").size()
    s = np.zeros(len(active_days)); c = np.zeros(len(active_days))
    pos = {d: j for j, d in enumerate(active_days)}
    for d, v in dsum.items():
        s[pos[d]] = v
    for d, v in dcnt.items():
        c[pos[d]] = v
    idx = rng.integers(0, len(active_days), size=(nruns, len(active_days)))
    ss, cc = s[idx].sum(axis=1), c[idx].sum(axis=1)
    m = ss / np.where(cc > 0, cc, 1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


# ------------------------------------------------------------ report (section 9)
def describe(label, T, mask, slip, nruns, vwap_entry=False, flat=None, with_null=True, top_trades=False):
    real, active = run_rule(T, mask, vwap_entry)
    lines = [f"== {label}"]
    nd = int(active.sum())
    if len(real) == 0:
        return lines + ["no trades"], real
    net = net_of(real, slip, flat=flat)
    gross = real["gross"].values
    m = net.mean()
    lo, hi = day_boot_ci(real, net, np.flatnonzero(active), nruns)
    win = (net > 0).mean() * 100
    pf = net[net > 0].sum() / -net[net < 0].sum() if (net < 0).any() else np.inf
    bp = (net / real["entry"].values * 1e4).mean()
    cum = np.cumsum(net)
    dd = (cum - np.maximum.accumulate(np.r_[0.0, cum])[1:]).min()
    lines.append(f"valid days {nd}, trades {len(real)} ({len(real) / nd:.2f} per day)"
                 + ("  INSUFFICIENT TRADES" if len(real) < MIN_TRADES else ""))
    lines.append(f"mean net per trade {m:.3f} pt (95% day bootstrap {lo:.3f} to {hi:.3f}); {bp:.3f} bp; "
                 f"gross {gross.mean():.3f} pt; sum net {net.sum():.1f} pt")
    lines.append(f"win rate {win:.1f}%; profit factor {pf:.3f}; avg win {net[net > 0].mean():.3f}; "
                 f"avg loss {net[net <= 0].mean():.3f}; median hold {np.median(real['hold']):.0f} checks; "
                 f"max drawdown cum. points {dd:.1f}")
    for sd, nm in ((1, "long"), (-1, "short")):
        sel = real["side"].values == sd
        if sel.any():
            lines.append(f"  {nm}: {sel.sum()} trades, mean net {net[sel].mean():.3f}, win {(net[sel] > 0).mean() * 100:.1f}%")
    yr = pd.Series(net).groupby(real["day"].dt.year.values)
    for y, g in yr:
        lines.append(f"  year {y}: {len(g)} trades, sum net {g.sum():.1f}, mean {g.mean():.3f}"
                     + ("  (insufficient)" if len(g) < MIN_TRADES else ""))
    dnet = pd.Series(net).groupby(real["day"].values).sum().sort_values()
    lines.append(f"without the 10 best days: sum net {dnet.iloc[:-10].sum():.1f} pt "
                 f"(10 best days {dnet.iloc[-10:].sum():.1f} pt)")
    if with_null:
        nb, cb, p = null_b(T, active, real, slip, nruns, flat=flat)
        pb = pct(m, nb)
        na = null_a(real, net, nruns)
        pa = pct(m, na)
        lines.append(f"Null B (random moment and direction, p={p:.4f}, mean trades {cb.mean():.0f}): "
                     f"mean {nb.mean():.3f}, percentile {pb[0]:.1f} (strict {pb[1]:.1f}, with ties {pb[2]:.1f}), "
                     f"{int((nb >= m).sum())} of {nruns} runs at or above")
        lines.append(f"Null A (same trades, coin on direction): mean {na.mean():.3f}, percentile {pa[0]:.1f} "
                     f"(strict {pa[1]:.1f}, with ties {pa[2]:.1f}), {int((na >= m).sum())} of {nruns} runs at or above")
    return lines, real


# ------------------------------------------------------------ fake market (section 6)
def fake_sessions(rng, ndays):
    sd_sub = NOISE_VOL / np.sqrt(252 * RTH_LEN * NOISE_SUBSTEPS)
    sd_night = NOISE_VOL / np.sqrt(252) * NOISE_OVERNIGHT
    px = NOISE_START
    out = []
    for dd in range(ndays):
        px *= np.exp(rng.normal(0, sd_night))
        steps = rng.normal(0, sd_sub, size=(RTH_LEN, NOISE_SUBSTEPS))
        path = px * np.exp(np.cumsum(steps.ravel())).reshape(RTH_LEN, NOISE_SUBSTEPS)
        prev = np.r_[px, path[:-1, -1]]
        o = prev
        h = np.maximum(path.max(axis=1), o)
        l = np.minimum(path.min(axis=1), o)
        c = path[:, -1]
        out.append({"o": o, "h": h, "l": l, "c": c,
                    "v": rng.poisson(NOISE_TICKVOL, RTH_LEN).astype(float) + 1.0,
                    "sp": np.full(RTH_LEN, NOISE_SPREAD),
                    "day": pd.Timestamp("2000-01-03") + pd.Timedelta(days=dd)})
        px = c[-1]
    return out


def noise_check(sets, seed, n):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(sets):
        sess = fake_sessions(rng, NOISE_DAYS)
        T = day_tables(sess)
        mask = np.ones(len(sess), dtype=bool)
        real, active = run_rule(T, mask)
        net = net_of(real, SLIP_USTEC)
        m = net.mean()
        nb, cb, p = null_b(T, active, real, SLIP_USTEC, n, seed=SEED_NULL + s)
        na = null_a(real, net, n, seed=SEED_NULL + s)
        rows.append((s, len(real), m, real["gross"].mean(), pct(m, nb)[0], pct(m, na)[0], cb.mean()))
        print(f"set {s:2d}: trades {len(real)}, net {m:.3f}, gross {real['gross'].mean():.3f}, "
              f"Null B pct {rows[-1][4]:.1f} (trades {cb.mean():.0f}), Null A pct {rows[-1][5]:.1f}", flush=True)
    a = np.array(rows)
    mb, ma = a[:, 4].mean(), a[:, 5].mean()
    ob, oa = int((a[:, 4] > 95).sum()), int((a[:, 5] > 95).sum())
    ok = (35 <= mb <= 65) and ob <= 3 and (35 <= ma <= 65) and oa <= 3
    print(f"\nNull B: mean percentile {mb:.1f}, {ob} of {sets} above 95")
    print(f"Null A: mean percentile {ma:.1f}, {oa} of {sets} above 95")
    print(f"mean gross per trade on noise {a[:, 3].mean():.3f} pt; mean net {a[:, 2].mean():.3f} pt")
    print("NOISE CHECK PASSED" if ok else "NOISE CHECK FAILED")
    return ok


# ------------------------------------------------------------ self-test (section 6)
def reference_trades(sess, vwap_entry=False):
    """Second, plain implementation: explicit loops, no shared code with day_tables/_rule."""
    out = []
    for i in range(LOOKBACK, len(sess)):
        s = sess[i]
        O = s["o"][0]
        cprev = sess[i - 1]["c"][RTH_LEN - 1]
        pos, kin, ep, esp = 0, 0, 0.0, 0.0
        for k in range(NCHK):
            t = 29 + 30 * k
            sig = 0.0
            for j in range(i - LOOKBACK, i):
                sig += abs(sess[j]["c"][t] / sess[j]["o"][0] - 1.0)
            sig /= LOOKBACK
            ub = max(O, cprev) * (1 + sig)
            lb = min(O, cprev) * (1 - sig)
            num = den = 0.0
            for u in range(t + 1):
                tp = (s["h"][u] + s["l"][u] + s["c"][u]) / 3.0
                num += tp * s["v"][u]
                den += s["v"][u]
            vw = num / den if den > 0 else np.mean((s["h"][:t + 1] + s["l"][:t + 1] + s["c"][:t + 1]) / 3.0)
            p = s["c"][t]
            fill = s["o"][t + 1]
            was = pos
            if pos == 1 and p < max(ub, vw):
                out.append((i, 1, kin, k, ep, fill)); pos = 0
            if pos == -1 and p > min(lb, vw):
                out.append((i, -1, kin, k, ep, fill)); pos = 0
            if pos == 0:
                want = 1 if (p > ub and (not vwap_entry or p > vw)) else (
                    -1 if (p < lb and (not vwap_entry or p < vw)) else 0)
                if want != 0 and want != was:      # same moment: only a reversal after an exit
                    pos, kin, ep = want, k, fill
        if pos != 0:
            out.append((i, pos, kin, EOD, ep, s["c"][RTH_LEN - 1]))
    return out


def handmade(rng):
    """16 quiet days, then: gap up without move, gap down with fall, rise then crash (reversal), late rise."""
    days = []
    px = 1000.0
    def day(path, open_px):
        o = np.r_[open_px, path[:-1]]
        return {"o": o, "h": np.maximum(o, path) + 0.01, "l": np.minimum(o, path) - 0.01, "c": path,
                "v": np.full(RTH_LEN, 10.0), "sp": np.full(RTH_LEN, 0.1), "day": pd.Timestamp("2001-01-01")}
    for _ in range(16):
        path = px + np.cumsum(rng.normal(0, 0.3, RTH_LEN))
        days.append(day(path, px)); px = path[-1]
    # A: gap up 10, then flat: no trade expected
    o = px + 10; path = o + np.zeros(RTH_LEN); days.append(day(path, o)); px = path[-1]
    # B: gap down 10, then steady fall: short from 10:00 to 16:00 expected
    o = px - 10; path = o - np.linspace(0, 30, RTH_LEN); days.append(day(path, o)); px = path[-1]
    # C: flat open, rise to +20 by 11:00, crash to -25 by 13:00: long, then exit and short (reversal)
    o = px; t = np.arange(RTH_LEN)
    path = o + np.interp(t, [0, 90, 210, 389], [0, 20, -25, -25]); days.append(day(path, o)); px = path[-1]
    # D: flat until 15:00, then rise: long at 15:30, closed at 16:00
    o = px; path = o + np.interp(t, [0, 330, 389], [0, 0, 15]); days.append(day(path, o)); px = path[-1]
    for k, d in enumerate(days):
        d["day"] = pd.Timestamp("2001-01-01") + pd.Timedelta(days=k)
    return days


def selftest():
    rng = np.random.default_rng(1)
    ok = True
    # 1) hand-made days with expected behaviour
    sess = handmade(rng)
    T = day_tables(sess)
    real, _ = run_rule(T, np.ones(len(sess), dtype=bool))
    last = real[real["i"] >= 16]
    exp = {16: [], 17: [(-1, 0, EOD)], 18: "rev", 19: [(1, 11, EOD)]}
    got = {i: [(r.side, r.k_in, r.k_out) for r in last[last["i"] == i].itertuples()] for i in range(16, 20)}
    print("hand-made days:", got)
    c1 = got[16] == exp[16] and got[17] == exp[17] and got[19] == exp[19]
    c2 = len(got[18]) >= 2 and got[18][0][0] == 1 and got[18][-1][0] == -1 and got[18][-1][2] == EOD \
        and got[18][0][2] <= got[18][-1][1]
    print(" gap up no trade, gap down short all day, late long:", "OK" if c1 else "FAIL")
    print(" rise then crash gives long then reversal to short:", "OK" if c2 else "FAIL")
    same_dir = 0
    for i, g in real.groupby("i"):
        r = list(g.itertuples())
        same_dir += sum(1 for x, y in zip(r[:-1], r[1:]) if x.k_out == y.k_in and x.side == y.side)
    c3 = same_dir == 0
    print(f" same-direction re-entry at the exit moment (v1.1 forbids): {same_dir}", "OK" if c3 else "FAIL")
    ok &= c1 and c2 and c3
    # 2) both implementations on a fake market, both entry variants and both VWAP weightings
    sess = fake_sessions(np.random.default_rng(3), 300)
    for ve in (False, True):
        T = day_tables(sess)
        real, _ = run_rule(T, np.ones(len(sess), dtype=bool), ve)
        ref = reference_trades(sess, ve)
        a = real[["i", "side", "k_in", "k_out", "entry", "exit"]].values
        b = np.array(ref)
        same = a.shape == b.shape and np.allclose(a, b)
        print(f" fake market 300 days, vwap_entry={ve}: {len(a)} vs {len(b)} trades,", "OK" if same else "FAIL")
        ok &= same
    # 3) Null A and Null B mechanics: zero-cost random-walk mean near zero
    T = day_tables(sess)
    real, active = run_rule(T, np.ones(len(sess), dtype=bool))
    nb, cb, p = null_b(T, active, real, 0.0, 500, flat=0.0)
    print(f" Null B on 300 fake days, no costs: mean {nb.mean():.4f}, trades {cb.mean():.1f} vs real {len(real)}")
    ok &= abs(cb.mean() - len(real)) < 0.05 * len(real)
    print("SELFTEST PASSED" if ok else "SELFTEST FAILED")
    return ok


# ------------------------------------------------------------ data check and real run (sections 7-9)
def datacheck(path, point):
    m1 = load_mt5(path)
    print(f"file {os.path.basename(path)}: {len(m1)} rows, {m1.index[0]} to {m1.index[-1]}")
    rows, opens = [], []
    for d in split_days(m1, point):
        s = session_arrays(d)
        y = d["day"].year
        rows.append((y, s is not None, len(d["min"]), np.median(d["sp"]) if len(d["sp"]) else np.nan,
                     (d["sp"] == 0).mean(), (d["v"] == 0).mean()))
        if s is not None:
            opens.append((y, s["jump"] < JUMP_MIN))
    df = pd.DataFrame(rows, columns=["year", "valid", "bars", "med_spread_pts", "zero_spread", "zero_vol"])
    op = pd.DataFrame(opens, columns=["year", "nojump"])
    print("year | days | valid | median bars/day | median spread (pt) | zero spread share | zero tickvol share | valid days without clear jump at 16:30")
    for y, g in df.groupby("year"):
        print(f"{y} | {len(g)} | {int(g['valid'].sum())} | {g['bars'].median():.0f} | {g['med_spread_pts'].median():.2f} | "
              f"{g['zero_spread'].mean():.3f} | {g['zero_vol'].mean():.4f} | "
              f"{int(op[op['year'] == y]['nojump'].sum())}")


def load_sessions(path, point):
    m1 = load_mt5(path)
    return [s for s in (session_arrays(d) for d in split_days(m1, point)) if s is not None]


def real_run(a):
    out = []
    def emit(lines):
        for x in lines:
            print(x, flush=True)
            out.append(x)
    us = load_sessions(a.ustec, a.point_ustec)
    T = day_tables(us)
    Teq = day_tables(us, equal_weight=True)
    d = T["days"]
    p1 = (d >= P1_FROM) & (d <= P1_TO)
    nj = sum(1 for s, dd in zip(us, d) if P1_FROM <= str(dd.date()) <= P1_TO and s["jump"] < JUMP_MIN)
    emit([f"USTEC valid sessions {len(us)}, {d[0].date()} to {d[-1].date()}; P1 sessions {int(p1.sum())}; "
          f"P1 days without clear volume jump at 16:30: {nj}"])
    # control group first (section 5): the decisive run prints Null B before the rule summary in the log file
    lines, real = describe("USTEC P1, K2 A, K5 A slippage 1 pt (DECISIVE: C1, C2, C3)", T, p1, SLIP_USTEC, a.n)
    nb_line = [x for x in lines if x.startswith("Null")]
    emit(["-- control groups --"] + nb_line + ["-- rule --"] + [x for x in lines if not x.startswith("Null")])
    real.to_csv(os.path.join(a.out, "trades_ustec_p1.csv"), index=False)
    net = net_of(real, SLIP_USTEC)
    lo, hi = day_boot_ci(real, net, np.flatnonzero(run_rule(T, p1)[1]), a.n)
    yrs = pd.Series(net).groupby(real["day"].dt.year.values).sum()
    nb = [x for x in lines if x.startswith("Null B")][0]
    pB = float(nb.split("percentile ")[1].split(" ")[0])
    emit(["", "VERDICT (section 8)",
          f"C1 (+{CLAIM_C1} pt): upper bound {hi:.3f} -> " + ("FALSIFIED" if hi < CLAIM_C1 else "not falsified"),
          f"C2 (beats Null B): percentile {pB:.1f} -> " + ("not falsified" if pB > 95 else "FALSIFIED"),
          f"C3 (every year positive): " + ", ".join(f"{y} {v:.1f}" for y, v in yrs.items()) + " -> "
          + ("FALSIFIED" if (yrs < 0).any() else "not falsified"), ""])
    for mult in SLIP_MULT:
        if mult == 1:
            continue
        emit(describe(f"USTEC P1, slippage {mult}x", T, p1, SLIP_USTEC * mult, a.n)[0] + [""])
    emit(describe("USTEC P1, K5 B video cost level 0.75 pt per trade", T, p1, 0, a.n, flat=K5B_COST)[0] + [""])
    emit(describe("USTEC P1, K2 B (entry also on the VWAP side)", T, p1, SLIP_USTEC, a.n, vwap_entry=True)[0] + [""])
    emit(describe("USTEC P1, VWAP without volume", Teq, p1, SLIP_USTEC, a.n)[0] + [""])
    emit(describe("USTEC after the paper (from 2024-05-14)", T, (d >= AFTER_PAPER) & (d <= P1_TO), SLIP_USTEC, a.n)[0] + [""])
    emit(describe("USTEC 2017-2019 (K3 B)", T, (d >= EARLY_FROM) & (d <= EARLY_TO), SLIP_USTEC, a.n)[0] + [""])
    s5 = load_sessions(a.us500, a.point_us500)
    T5 = day_tables(s5)
    d5 = T5["days"]
    emit([f"US500 valid sessions {len(s5)}, {d5[0].date()} to {d5[-1].date()}"])
    emit(describe("US500 P1 (K1 B), slippage 0.25 pt", T5, (d5 >= P1_FROM) & (d5 <= P1_TO), SLIP_US500, a.n)[0] + [""])
    with open(os.path.join(a.out, "run01.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--datacheck", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--ustec"); ap.add_argument("--us500")
    ap.add_argument("--point", type=float, default=0.01)
    ap.add_argument("--point-ustec", type=float, default=0.01)
    ap.add_argument("--point-us500", type=float, default=0.01)
    ap.add_argument("--sets", type=int, default=24)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.noise:
        sys.exit(0 if noise_check(a.sets, a.seed, a.n or 2000) else 1)
    if a.datacheck:
        datacheck(a.csv, a.point)
        return
    if a.real:
        a.n = a.n or N_NULL
        os.makedirs(a.out, exist_ok=True)
        real_run(a)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
