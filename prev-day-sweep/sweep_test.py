"""Test S: previous-day sweep with 1-hour EMA 200 trend, Nasdaq 100 (USTEC) 5 min, hold to 16:00 New York.

Follows hypothesis v1.1 (hypothese-prev-day-sweep.md, 23 Nov 2026; v1.1 changed only Null T). Deterministic, no LLM on price data.

Usage:
    python sweep_test.py --selftest                                   (self-test, section 6)
    python sweep_test.py --noise [--sets 24] [--seed 7] [--n 2000]   (noise check, section 6)
    python sweep_test.py <M1.csv> --datacheck                         (metadata only, section 7)
    python sweep_test.py <M1.csv> --run [--n 10000] [--out dir]       (run 01, section 8 and 9)

Input: MT5 export with <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>, server time = New York + 7.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

SERVER_MINUS_NY = 7 * 60      # section 4.1
DAY_START_NY = 20 * 60        # trading day starts 20:00 New York (section 4.3)
KZ = ((2 * 60, 5 * 60), (7 * 60, 11 * 60))   # London, New York kill zones, NY minutes of day (section 1)
EXIT_NY = 16 * 60             # flat at 16:00 New York
VALID_FROM, VALID_TO = 2 * 60, 16 * 60       # validity window, section 4.3
VALID_SHARE = 0.90
PREV_MIN_BARS = 600           # section 4.4
EMA_LEN = 200
ATR_LEN = 14
ATR_MIN = 0.5
SLIP = 1.0                    # points per side (K3 A)
VIDEO_COST = 0.0001           # 0.01% per side (K3 B)
POINT = 0.01                  # spread column unit (as test R)
SEED_NULL = 43
N_NULL = 10000


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
    keep = ~ts.isna()
    df, ts = df[keep.values], ts[keep]
    tmin = (ts.values.astype("datetime64[m]").astype(np.int64))
    order = np.argsort(tmin, kind="stable")
    tmin = tmin[order]
    u = np.r_[True, tmin[1:] != tmin[:-1]]
    g = lambda k: df[k].astype(float).values[order][u]
    return {"t": tmin[u], "o": g("open"), "h": g("high"), "l": g("low"), "c": g("close"),
            "sp": g("spread") * POINT}


# ------------------------------------------------------------ preparation (sections 4.1 to 4.4, 4.8, 4.11)
def prepare(m1, bar=5):
    t = m1["t"]
    ny = t - SERVER_MINUS_NY
    tod = ny % 1440
    td = (ny + (1440 - DAY_START_NY)) // 1440          # trading-day number (days since epoch of day D)
    # bars of `bar` minutes, aligned to the clock
    bk = t // bar
    bstart = np.flatnonzero(np.r_[True, bk[1:] != bk[:-1]])
    bend = np.r_[bstart[1:], len(t)]
    B = {"key": bk[bstart], "i0": bstart, "i1": bend,
         "o": m1["o"][bstart], "c": m1["c"][bend - 1],
         "h": np.maximum.reduceat(m1["h"], bstart), "l": np.minimum.reduceat(m1["l"], bstart)}
    B["ny"] = B["key"] * bar - SERVER_MINUS_NY
    B["tod"] = B["ny"] % 1440
    B["td"] = (B["ny"] + (1440 - DAY_START_NY)) // 1440
    # ATR 14 Wilder on bars
    pc = np.r_[B["c"][0], B["c"][:-1]]
    tr = np.maximum(B["h"] - B["l"], np.maximum(np.abs(B["h"] - pc), np.abs(B["l"] - pc)))
    tr[0] = B["h"][0] - B["l"][0]
    B["atr"] = wilder(tr, ATR_LEN)
    # hour bars, EMA 200 of closes
    hk = t // 60
    hs = np.flatnonzero(np.r_[True, hk[1:] != hk[:-1]])
    he = np.r_[hs[1:], len(t)]
    hkey, hclose = hk[hs], m1["c"][he - 1]
    hema = ema(hclose, EMA_LEN)
    # EMA of the last hour fully closed at the close of each bar (section 4.8)
    bclose_t = (B["key"] + 1) * bar                     # server minute at bar close
    last_hour = bclose_t // 60 - 1                      # hour key whose end <= bar close
    j = np.searchsorted(hkey, last_hour, side="right") - 1
    B["ema"] = np.where(j >= 0, hema[np.maximum(j, 0)], np.nan)
    # day table
    tdu, first = np.unique(td, return_index=True)
    last = np.r_[first[1:], len(td)]
    D = {"td": tdu, "a": first, "b": last, "n": last - first}
    valid = np.zeros(len(tdu), bool)
    for k in range(len(tdu)):
        a, b = first[k], last[k]
        x = tod[a:b]
        nwin = np.count_nonzero((x >= VALID_FROM) & (x < VALID_TO) & (ny[a:b] // 1440 == tdu[k]))
        wd = (tdu[k] + 3) % 7                           # 0 = Monday (1970-01-01 was a Thursday)
        valid[k] = nwin >= VALID_SHARE * (VALID_TO - VALID_FROM) and wd < 5
    D["valid"] = valid
    D["wd"] = (tdu + 3) % 7
    D["pdh"] = np.full(len(tdu), np.nan)
    D["pdl"] = np.full(len(tdu), np.nan)
    prev = -1
    for k in range(len(tdu)):
        if prev >= 0:
            D["pdh"][k] = m1["h"][first[prev]:last[prev]].max()
            D["pdl"][k] = m1["l"][first[prev]:last[prev]].min()
        if D["n"][k] >= PREV_MIN_BARS:
            prev = k
    # bar ranges per day
    ba = np.searchsorted(B["td"], tdu, side="left")
    bb = np.searchsorted(B["td"], tdu, side="right")
    D["ba"], D["bb"] = ba, bb
    # median spread per calendar year (fallback, section 5)
    yr = (pd.to_datetime(t * 60, unit="s").year).values
    med = {}
    for y in np.unique(yr):
        s = m1["sp"][yr == y]
        s = s[s > 0]
        med[y] = float(np.median(s)) if len(s) else 0.0
    return {"m1": m1, "ny": ny, "tod": tod, "td": td, "yr": yr, "B": B, "D": D, "bar": bar, "medsp": med}


def wilder(x, n):
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    for i in range(n, len(x)):
        out[i] = out[i - 1] + (x[i] - out[i - 1]) / n
    return out


def ema(x, n):
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    a = 2.0 / (n + 1)
    out[n - 1] = x[:n].mean()
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def kz_of(tod):
    for z, (s, e) in enumerate(KZ):
        if s <= tod < e:
            return z
    return -1


# ------------------------------------------------------------ signal (sections 4.5 to 4.11)
def day_signal(bo, bh, bl, bc, btod, bema, batr, pdh, pdl):
    """Pure function on the bars of one trading day (chronological, from 20:00). Returns None or a dict with
    trigger bar index (in this day's bars), side, sweep extreme, kill zone. Used by the main run and the self-test."""
    n = len(bh)
    takeH = takeL = -1
    for k in range(n):
        if takeH < 0 and bh[k] > pdh:
            takeH = k
        if takeL < 0 and bl[k] < pdl:
            takeL = k
    cands = []
    for side, take in ((-1, takeH), (1, takeL)):
        if take < 0:
            continue
        z = kz_of(btod[take])
        if z < 0:
            continue
        for k in range(take, n):
            if kz_of(btod[k]) != z:
                break
            back = bc[k] < pdh if side == -1 else bc[k] > pdl
            if back:
                ext = bh[take:k + 1].max() if side == -1 else bl[take:k + 1].min()
                cands.append((k, side, take, ext, z))
                break
    for k, side, take, ext, z in sorted(cands):
        if takeH >= 0 and takeL >= 0 and takeH <= k and takeL <= k:
            return {"skip": True, "k": k}
        e = bema[k]
        if np.isnan(e) or np.isnan(batr[k]):
            continue
        if (side == 1 and bc[k] > e) or (side == -1 and bc[k] < e):
            return {"skip": False, "k": k, "side": side, "take": take, "ext": ext, "z": z}
    return None


@njit(cache=True)
def walk(o, h, l, c, e, last, side, stop):
    """Minute-by-minute path from minute index e (entry at o[e]) to minute `last` (inclusive). Section 4.12."""
    for i in range(e, last + 1):
        if side == 1:
            if o[i] <= stop and i > e:
                return o[i], i, 1
            if l[i] <= stop:
                return min(stop, o[i]) if i > e else stop, i, 1
        else:
            if o[i] >= stop and i > e:
                return o[i], i, 1
            if h[i] >= stop:
                return max(stop, o[i]) if i > e else stop, i, 1
    return c[last], last, 0


def last_minute_before_exit(P, k_day, e):
    """Index of the last minute bar of day D before 16:00 New York, from entry minute e."""
    m = P["m1"]
    td = P["D"]["td"][k_day]
    b = P["D"]["b"][k_day]
    lim = td * 1440 + EXIT_NY                           # NY minute of 16:00 on day D
    hi = np.searchsorted(P["ny"][e:b], lim, side="left") + e - 1
    return hi


def spread_at(P, i):
    s = P["m1"]["sp"][i]
    if not s > 0:
        s = P["medsp"][P["yr"][i]]
    return s


def trade_result(P, k_day, e, side, d, slip=SLIP, cost_mode="ours"):
    m = P["m1"]
    last = last_minute_before_exit(P, k_day, e)
    if last < e:
        return None
    entry = m["o"][e]
    stop = entry - d if side == 1 else entry + d
    px, xi, hit = walk(m["o"], m["h"], m["l"], m["c"], e, last, side, stop)
    gross = (px - entry) * side
    if cost_mode == "ours":
        cost = spread_at(P, e) + 2 * slip
    elif cost_mode == "video":
        cost = VIDEO_COST * (entry + px)
    else:
        cost = 0.0
    return {"entry": entry, "exit": px, "xi": xi, "hit": hit, "gross": gross, "cost": cost,
            "net": gross - cost, "R": (gross - cost) / d, "Rg": gross / d}


def find_trades(P):
    B, D, m = P["B"], P["D"], P["m1"]
    rows = []
    for k in range(len(D["td"])):
        if not D["valid"][k] or np.isnan(D["pdh"][k]):
            continue
        a, b = D["ba"][k], D["bb"][k]
        if b - a < 2:
            continue
        s = day_signal(B["o"][a:b], B["h"][a:b], B["l"][a:b], B["c"][a:b], B["tod"][a:b],
                       B["ema"][a:b], B["atr"][a:b], D["pdh"][k], D["pdl"][k])
        if s is None or s["skip"]:
            continue
        kt = a + s["k"]
        if kt + 1 >= b:
            continue
        nb = kt + 1
        if B["tod"][nb] >= EXIT_NY and B["td"][nb] == D["td"][k]:
            continue
        e = B["i0"][nb]
        entry = m["o"][e]
        d = max(abs(entry - s["ext"]), ATR_MIN * B["atr"][kt])
        r = trade_result(P, k, e, s["side"], d)
        if r is None:
            continue
        r.update({"kday": k, "td": D["td"][k], "kz": s["z"], "side": s["side"], "e": e, "d": d,
                  "trig": kt, "atr": B["atr"][kt], "ext": s["ext"], "pdh": D["pdh"][k], "pdl": D["pdl"][k]})
        rows.append(r)
    df = pd.DataFrame(rows)
    if len(df):
        df["date"] = pd.to_datetime(df["td"] * 86400, unit="s").dt.date
        df["year"] = pd.to_datetime(df["td"] * 86400, unit="s").dt.year
    return df


# ------------------------------------------------------------ control groups (section 5)
def option_table(P, T):
    """For each real trade: R for each random entry option in the same kill zone (both sides) and the trend side."""
    B, D, m = P["B"], P["D"], P["m1"]
    bar = P["bar"]
    out = []
    for _, r in T.iterrows():
        k = int(r["kday"])
        zs, ze = KZ[int(r["kz"])]
        a, b = D["ba"][k], D["bb"][k]
        tods = B["tod"][a:b]
        opts = np.flatnonzero((tods > zs) & (tods <= ze)) + a     # bar opens 02:05..05:00 / 07:05..11:00
        Rl, Rs, tside = [], [], []
        for nb in opts:
            e = B["i0"][nb]
            rl = trade_result(P, k, e, 1, r["d"])
            rs = trade_result(P, k, e, -1, r["d"])
            if rl is None or rs is None:
                continue
            Rl.append(rl["R"]); Rs.append(rs["R"])
            pb = nb - 1
            em = B["ema"][pb]
            tside.append(1 if B["c"][pb] > em else (-1 if B["c"][pb] < em else 0))
        opp = trade_result(P, k, int(r["e"]), -int(r["side"]), r["d"])
        out.append({"Rl": np.array(Rl), "Rs": np.array(Rs), "ts": np.array(tside), "Ropp": opp["R"]})
    return out


def run_nulls(T, opt, nruns, seed):
    """Null B (decisive) and Null A. Null T (v1.1) is in null_t()."""
    rng = np.random.default_rng(seed)
    n = len(T)
    realR = T["R"].values
    nb = np.zeros(nruns); na = np.zeros(nruns)
    for i in range(n):
        Rl, Rs = opt[i]["Rl"], opt[i]["Rs"]
        m = len(Rl)
        j = rng.integers(0, m, nruns)
        coin = rng.integers(0, 2, nruns)
        nb += np.where(coin == 1, Rl[j], Rs[j])
        coin2 = rng.integers(0, 2, nruns)
        na += np.where(coin2 == 1, realR[i], opt[i]["Ropp"])
    return nb / n, na / n


def null_t_pool(P, day_mask):
    """All entry options on valid days in `day_mask` (section 5, Null T v1.1): entry minute, last minute before
    16:00, trend side from the previous bar, ATR of the previous bar, spread at entry, kill zone."""
    B, D = P["B"], P["D"]
    E, L, S, A, SP, Z = [], [], [], [], [], []
    for k in np.flatnonzero(day_mask & D["valid"] & ~np.isnan(D["pdh"])):
        a, b = D["ba"][k], D["bb"][k]
        tods = B["tod"][a:b]
        for z, (zs, ze) in enumerate(KZ):
            for nb in np.flatnonzero((tods > zs) & (tods <= ze)) + a:
                pb = nb - 1
                em, at = B["ema"][pb], B["atr"][pb]
                if np.isnan(em) or np.isnan(at) or B["c"][pb] == em:
                    continue
                e = B["i0"][nb]
                last = last_minute_before_exit(P, k, e)
                if last < e:
                    continue
                E.append(e); L.append(last); S.append(1 if B["c"][pb] > em else -1); A.append(at)
                SP.append(spread_at(P, e)); Z.append(z)
    return {k: np.array(v) for k, v in zip("ELSAPZ", (E, L, S, A, SP, Z))}


@njit(cache=True)
def _null_t(o, h, l, c, pe, pl, ps, pa, psp, idx_by_z, nz, kk, zz, slip, nruns, seed):
    np.random.seed(seed)
    n = len(kk)
    out = np.zeros(nruns)
    for r in range(nruns):
        tot = 0.0
        for i in range(n):
            z = zz[i]
            j = idx_by_z[z, np.random.randint(0, nz[z])]
            e = pe[j]; side = ps[j]; d = kk[i] * pa[j]
            entry = o[e]
            stop = entry - d if side == 1 else entry + d
            px, xi, hit = walk(o, h, l, c, e, pl[j], side, stop)
            tot += ((px - entry) * side - psp[j] - 2.0 * slip) / d
        out[r] = tot / n
    return out


def null_t(P, T, day_mask, nruns, seed):
    pool = null_t_pool(P, day_mask)
    m = P["m1"]
    nz = np.array([np.sum(pool["Z"] == z) for z in range(len(KZ))])
    idx = np.full((len(KZ), max(nz.max(), 1)), -1, np.int64)
    for z in range(len(KZ)):
        w = np.flatnonzero(pool["Z"] == z); idx[z, :len(w)] = w
    kk = (T["d"] / T["atr"]).values.astype(float)
    zz = T["kz"].values.astype(np.int64)
    return _null_t(m["o"], m["h"], m["l"], m["c"], pool["E"].astype(np.int64), pool["L"].astype(np.int64),
                   pool["S"].astype(np.int64), pool["A"].astype(float), pool["P"].astype(float), idx, nz.astype(np.int64),
                   kk, zz, SLIP, nruns, seed)


def pct(real, null):
    lt = (null < real).mean() * 100
    eq = (null == real).mean() * 100
    return lt + 0.5 * eq


def pf(x):
    g = x[x > 0].sum(); l = -x[x < 0].sum()
    return g / l if l > 0 else np.inf


def boot(T, days, nruns, seed):
    """95% intervals of mean R and PF, bootstrap over valid trading days (incl. days without trade)."""
    rng = np.random.default_rng(seed)
    pos = {d: j for j, d in enumerate(days)}
    R = np.zeros(len(days)); has = np.zeros(len(days))
    for d, v in zip(T["td"].values, T["R"].values):
        R[pos[d]] += v; has[pos[d]] += 1
    means = np.empty(nruns); pfs = np.empty(nruns)
    for r in range(nruns):
        idx = rng.integers(0, len(days), len(days))
        x = R[idx]; c = has[idx]
        means[r] = x.sum() / max(c.sum(), 1)
        g = x[x > 0].sum(); l = -x[x < 0].sum()
        pfs[r] = g / l if l > 0 else np.inf
    return np.percentile(means, [2.5, 97.5]), np.percentile(pfs, [2.5, 97.5])


def streak(x):
    best = cur = 0
    for v in x:
        cur = cur + 1 if v < 0 else 0
        best = max(best, cur)
    return best


def max_dd(x):
    cum = np.cumsum(x)
    return float((cum - np.maximum.accumulate(np.r_[0, cum])[1:]).min()) if len(x) else 0.0


# ------------------------------------------------------------ noise (section 6)
@njit(cache=True)
def _fake(n_min, start, step_sd, seed, o, h, l, c):
    np.random.seed(seed)
    p = start
    for i in range(n_min):
        o[i] = p; hi = p; lo = p
        for s in range(60):
            p += np.random.normal() * step_sd
            if p > hi: hi = p
            if p < lo: lo = p
        h[i] = hi; l[i] = lo; c[i] = p


def fake_market(ndays, seed, start=15000.0, daily_sd_frac=0.012):
    """Weekdays only, 24 h a day, 1-point spread. Trading day 0 starts on a Monday 20:00 NY - 1 day."""
    n = ndays * 1440
    o = np.empty(n); h = np.empty(n); l = np.empty(n); c = np.empty(n)
    step = start * daily_sd_frac / np.sqrt(1440 * 60)
    _fake(n, start, step, seed, o, h, l, c)
    # server minutes: day j of trading days -> calendar weekdays, starting Monday 2001-01-01 (td 11323)
    td0 = 11323
    tds = []
    d = td0
    while len(tds) < ndays:
        if (d + 3) % 7 < 5:
            tds.append(d)
        d += 1
    tds = np.array(tds)
    base = (tds - 1) * 1440 + DAY_START_NY + SERVER_MINUS_NY      # server minute of 20:00 NY on day before
    t = (base[:, None] + np.arange(1440)[None, :]).ravel()
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "sp": np.full(n, 1.0)}


def noise_check(sets, seed, n, ndays=1500):
    res = []
    lines = []
    for s in range(sets):
        m1 = fake_market(ndays, seed * 1000 + s)
        P = prepare(m1, 5)
        T = find_trades(P)
        opt = option_table(P, T)
        nb, na = run_nulls(T, opt, n, SEED_NULL + s)
        nt = null_t(P, T, np.ones(len(P["D"]["td"]), bool), n, SEED_NULL + s)
        real = T["R"].mean()
        r = (len(T), real, pct(real, nb), pct(real, na), pct(real, nt), pf(T["R"].values), (T["R"] < 0).mean())
        res.append(r)
        line = (f"set {s:2d}: trades {r[0]:4d}  mean net R {r[1]:+.3f}  PF {r[5]:.2f}  losers {r[6]*100:.1f}%  "
                f"pct Null B {r[2]:5.1f}  Null A {r[3]:5.1f}  Null T {r[4]:5.1f}")
        print(line, flush=True); lines.append(line)
    a = np.array(res)
    ok = True
    summ = []
    for name, col in (("Null B", 2), ("Null A", 3), ("Null T", 4)):
        mean = a[:, col].mean(); hi = int((a[:, col] > 95).sum())
        good = 35 <= mean <= 65 and hi <= 2
        ok &= good
        summ.append(f"{name}: mean percentile {mean:.1f}, above 95: {hi} of {sets} -> {'PASS' if good else 'FAIL'}")
    summ.append(f"mean trades per set {a[:,0].mean():.1f}, mean net R {a[:,1].mean():+.3f}, mean PF {a[:,5].mean():.2f}")
    summ.append("NOISE CHECK " + ("PASSED" if ok else "FAILED"))
    for x in summ:
        print(x)
    return ok


# ------------------------------------------------------------ reference implementation (self-test)
def reference_trades(m1):
    """Second, plain implementation straight from minute bars (loops, dicts), section 6."""
    t, o, h, l, c, sp = m1["t"], m1["o"], m1["h"], m1["l"], m1["c"], m1["sp"]
    bars = {}
    order = []
    for i in range(len(t)):
        k = t[i] // 5
        if k not in bars:
            bars[k] = [o[i], h[i], l[i], c[i], i, i]; order.append(k)
        else:
            b = bars[k]; b[1] = max(b[1], h[i]); b[2] = min(b[2], l[i]); b[3] = c[i]; b[5] = i
    hours = {}
    horder = []
    for i in range(len(t)):
        k = t[i] // 60
        if k not in hours:
            horder.append(k)
        hours[k] = c[i]
    hc = [hours[k] for k in horder]
    he = {}
    e = None
    for j, k in enumerate(horder):
        if j == EMA_LEN - 1:
            e = sum(hc[:EMA_LEN]) / EMA_LEN
        elif j >= EMA_LEN:
            e = 2 / (EMA_LEN + 1) * hc[j] + (1 - 2 / (EMA_LEN + 1)) * e
        he[k] = e
    atr = {}
    trs = []
    pc = None
    a = None
    for j, k in enumerate(order):
        b = bars[k]
        tr = b[1] - b[2] if pc is None else max(b[1] - b[2], abs(b[1] - pc), abs(b[2] - pc))
        trs.append(tr)
        if j == ATR_LEN - 1:
            a = sum(trs) / ATR_LEN
        elif j >= ATR_LEN:
            a = a + (tr - a) / ATR_LEN
        atr[k] = a
        pc = b[3]
    def ema_at(bk):
        hk = (bk + 1) * 5 // 60 - 1
        cand = [x for x in horder if x <= hk]
        return he[cand[-1]] if cand else None
    # days
    byday = {}
    for i in range(len(t)):
        ny = t[i] - SERVER_MINUS_NY
        d = (ny + 240) // 1440
        byday.setdefault(d, []).append(i)
    dkeys = sorted(byday)
    out = []
    prevd = None
    for d in dkeys:
        idx = byday[d]
        pd_ok = prevd is not None
        if pd_ok:
            ph = max(h[i] for i in byday[prevd]); pl = min(l[i] for i in byday[prevd])
        if len(idx) >= PREV_MIN_BARS:
            nxt = d
        else:
            nxt = prevd
        cnt = sum(1 for i in idx if VALID_FROM <= (t[i] - SERVER_MINUS_NY) % 1440 < VALID_TO
                  and (t[i] - SERVER_MINUS_NY) // 1440 == d)
        if not pd_ok or (d + 3) % 7 >= 5 or cnt < VALID_SHARE * (VALID_TO - VALID_FROM):
            prevd = nxt; continue
        bk = sorted(set(t[i] // 5 for i in idx))
        tH = tL = None
        for j, k in enumerate(bk):
            if tH is None and bars[k][1] > ph: tH = j
            if tL is None and bars[k][2] < pl: tL = j
        def zone(k):
            x = (k * 5 - SERVER_MINUS_NY) % 1440
            if 120 <= x < 300: return 0
            if 420 <= x < 660: return 1
            return -1
        cands = []
        for side, tk in ((-1, tH), (1, tL)):
            if tk is None or zone(bk[tk]) < 0: continue
            z = zone(bk[tk])
            for j in range(tk, len(bk)):
                if zone(bk[j]) != z: break
                cl = bars[bk[j]][3]
                if (side == -1 and cl < ph) or (side == 1 and cl > pl):
                    ext = max(bars[bk[q]][1] for q in range(tk, j + 1)) if side == -1 else min(bars[bk[q]][2] for q in range(tk, j + 1))
                    cands.append((j, side, ext, z)); break
        trade = None
        for j, side, ext, z in sorted(cands):
            if tH is not None and tL is not None and tH <= j and tL <= j:
                break
            em = ema_at(bk[j]); at = atr[bk[j]]
            if em is None or at is None: continue
            cl = bars[bk[j]][3]
            if (side == 1 and cl > em) or (side == -1 and cl < em):
                trade = (j, side, ext, z); break
        prevd = nxt
        if trade is None or trade[0] + 1 >= len(bk): continue
        j, side, ext, z = trade
        nk = bk[j + 1]
        if (nk * 5 - SERVER_MINUS_NY) % 1440 >= EXIT_NY and (nk * 5 - SERVER_MINUS_NY + 240) // 1440 == d:
            continue
        ei = bars[nk][4]
        entry = o[ei]
        dd = max(abs(entry - ext), ATR_MIN * atr[bk[j]])
        stop = entry - dd if side == 1 else entry + dd
        lim = d * 1440 + EXIT_NY
        last = max(i for i in idx if t[i] - SERVER_MINUS_NY < lim)
        px = None
        for i in range(ei, last + 1):
            if side == 1:
                if i > ei and o[i] <= stop: px = o[i]; break
                if l[i] <= stop: px = min(stop, o[i]) if i > ei else stop; break
            else:
                if i > ei and o[i] >= stop: px = o[i]; break
                if h[i] >= stop: px = max(stop, o[i]) if i > ei else stop; break
        if px is None: px = c[last]
        net = (px - entry) * side - (sp[ei] + 2 * SLIP)
        out.append((d, side, round(entry, 6), round(px, 6), round(net / dd, 9)))
    return out


def make_day_bars(spec):
    """Handmade day: list of (tod_ny_minutes, o, h, l, c). Returns arrays."""
    a = np.array(spec, float)
    return a[:, 1], a[:, 2], a[:, 3], a[:, 4], a[:, 0].astype(int)


def selftest():
    ok = True
    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'OK  ' if cond else 'FAIL'} {name}")
    # day bars: 20:00 .. 15:55 every 5 min, flat at 100 unless changed; PDH 105, PDL 95
    tods = [(20 * 60 + 5 * i) % 1440 for i in range(240)]
    def base():
        return [[x, 100, 101, 99, 100] for x in tods]
    def idx(hh, mm):
        return tods.index(hh * 60 + mm)
    def sig(bars, ema_val, atr_val=2.0):
        o, h, l, c, td = make_day_bars(bars)
        n = len(o)
        return day_signal(o, h, l, c, td, np.full(n, ema_val), np.full(n, atr_val), 105.0, 95.0)
    # 1: low swept at 02:30 London, close back inside same bar, trend up (ema 90) -> long
    b = base(); k = idx(2, 30); b[k] = [b[k][0], 100, 100, 94, 96]
    s = sig(b, 90.0)
    check("1 low sweep in London + trend up -> long at trigger 02:30, extreme 94", s and not s["skip"] and s["side"] == 1 and s["k"] == k and s["ext"] == 94 and s["z"] == 0)
    # 2: same with trend down -> no trade
    s = sig(b, 110.0)
    check("2 same sweep, trend down -> no trade", s is None)
    # 3: low taken at 23:00 (Asia) first -> no sweep later
    b = base(); k0 = idx(23, 0); b[k0] = [b[k0][0], 100, 100, 94, 96]; k = idx(2, 30); b[k] = [b[k][0], 100, 100, 93, 96]
    check("3 level taken in Asia -> no trade", sig(b, 90.0) is None)
    # 4: high taken at 01:00 (outside), then low sweep in London -> both taken -> skip
    b = base(); k0 = idx(1, 0); b[k0] = [b[k0][0], 100, 106, 99, 100]; k = idx(2, 30); b[k] = [b[k][0], 100, 100, 94, 96]
    s = sig(b, 90.0)
    check("4 both sides taken before close back inside -> skip", s is not None and s["skip"])
    # 5: low taken at 04:50, closes below; 04:55 closes below; 05:00 closes inside (outside zone) -> no trade
    b = base(); k = idx(4, 50); b[k] = [b[k][0], 100, 100, 94, 94.5]; b[k + 1] = [b[k + 1][0], 94.5, 95, 93, 94]; b[k + 2] = [b[k + 2][0], 94, 97, 94, 96]
    check("5 no close back inside within the kill zone -> no trade", sig(b, 90.0) is None)
    # 6: high swept at 07:10 NY zone, closes back inside at 07:20, trend down -> short, extreme = max high 107
    b = base(); k = idx(7, 10); b[k] = [b[k][0], 100, 106, 100, 105.5]; b[k + 1] = [b[k + 1][0], 105.5, 107, 105, 106]; b[k + 2] = [b[k + 2][0], 106, 106.5, 103, 104]
    s = sig(b, 110.0)
    check("6 high sweep NY zone, close back two bars later, trend down -> short, extreme 107", s and not s["skip"] and s["side"] == -1 and s["k"] == k + 2 and s["ext"] == 107 and s["z"] == 1)
    # 7: trend at trigger disagrees, later bar would agree -> still no trade (only first return counts)
    b2 = [r[:] for r in b]
    o, h, l, c, td = make_day_bars(b2)
    em = np.full(len(o), 103.0); em[k + 3:] = 110.0
    s = day_signal(o, h, l, c, td, em, np.full(len(o), 2.0), 105.0, 95.0)
    check("7 trend disagrees on first return -> no trade", s is None)
    # 8: sweep in London at 05:00 boundary is outside (London ends 05:00) -> no trade
    b = base(); k = idx(5, 0); b[k] = [b[k][0], 100, 100, 94, 96]
    check("8 take at 05:00 (outside zones) -> no trade", sig(b, 90.0) is None)
    # path tests on minute bars
    o = np.array([100, 100, 100, 100, 100.]); h = np.array([101, 101, 101, 101, 101.]); l = np.array([99.5, 99, 97, 99, 99.]); c = o.copy()
    px, xi, hit = walk(o, h, l, c, 0, 4, 1, 98.0)
    check("9 long stop 98 hit at minute 2 -> exit 98", hit == 1 and xi == 2 and px == 98.0)
    o2 = np.array([100, 100, 96, 100.]); h2 = np.array([101, 101, 97, 101.]); l2 = np.array([99, 99, 95, 99.]); c2 = o2.copy()
    px, xi, hit = walk(o2, h2, l2, c2, 0, 3, 1, 98.0)
    check("10 gap past the stop -> exit at that minute's open 96", hit == 1 and xi == 2 and px == 96.0)
    px, xi, hit = walk(o, h, l, c, 0, 4, 1, 90.0)
    check("11 stop not hit -> exit at close of the last minute before 16:00", hit == 0 and xi == 4 and px == c[4])
    px, xi, hit = walk(o, h, l, c, 0, 4, -1, 101.0)
    check("12 short stop 101 hit at minute 0 (high = stop) -> exit 101", hit == 1 and xi == 0 and px == 101.0)
    # 13: minimum stop 0.5 ATR and full pipeline vs reference on fake days
    m1 = fake_market(1000, 99)
    P = prepare(m1, 5)
    T = find_trades(P)
    ref = reference_trades(m1)
    mine = [(int(r.td), int(r.side), round(r.entry, 6), round(r.exit, 6), round(r.R, 9)) for r in T.itertuples()]
    check(f"13 main and reference implementation identical on 1000 fake days ({len(mine)} and {len(ref)} trades)", mine == ref and len(mine) > 10)
    mind = (T["d"] >= ATR_MIN * T["atr"] - 1e-9).all()
    check("14 every stop distance >= 0.5 ATR", mind)
    usedmin = (np.abs(T["d"] - ATR_MIN * T["atr"]) < 1e-9).sum()
    check(f"15 minimum stop used on part of the trades ({usedmin} of {len(T)})", 0 < usedmin < len(T))
    check("16 all exits at or before 16:00 New York", ((P["ny"][T["xi"].values] % 1440) < EXIT_NY).all())
    check("17 entries inside or right after the kill zones", T.apply(lambda r: kz_of((P["ny"][r.e] - 5) % 1440) >= 0, axis=1).all())
    print("SELF-TEST " + ("PASSED" if ok else "FAILED"))
    return ok


# ------------------------------------------------------------ data check (section 7, metadata only)
def datacheck(path):
    m1 = load_mt5(path)
    P = prepare(m1, 5)
    D = P["D"]
    yrs = pd.to_datetime(D["td"] * 86400, unit="s").year.values
    print(f"file {os.path.basename(path)}: {len(m1['t'])} minute bars, "
          f"{pd.to_datetime(m1['t'][0]*60, unit='s')} to {pd.to_datetime(m1['t'][-1]*60, unit='s')} (server time)")
    print("year | weekday trading days | valid | median minute bars per day | zero-spread share | median spread (pt) | share of valid days with bars at NY 20:00-02:00 >= 90%")
    tod = P["tod"]
    for y in np.unique(yrs):
        sel = (yrs == y) & (D["wd"] < 5)
        ks = np.flatnonzero(sel)
        sp = m1["sp"][P["yr"] == y]
        night = []
        for k in ks:
            if not D["valid"][k]:
                continue
            a, b = D["a"][k], D["b"][k]
            x = tod[a:b]
            night.append(np.count_nonzero((x >= 20 * 60) | (x < 2 * 60)) >= 0.9 * 360)
        print(f"{y} | {len(ks)} | {int(D['valid'][ks].sum())} | {np.median(D['n'][ks]):.0f} | "
              f"{(sp <= 0).mean():.3f} | {np.median(sp[sp > 0]) if (sp > 0).any() else float('nan'):.2f} | "
              f"{np.mean(night) if night else float('nan'):.3f}")
    # daily break location: minutes of NY day with fewest bars, 2020 onwards
    sel = P["yr"] >= 2020
    cnt = np.bincount(tod[sel], minlength=1440)
    q = np.argsort(cnt)[:90]
    print("NY minutes of day with the fewest bars (2020+), as hours:", sorted(set((q // 60).tolist())))
    print(f"bars per NY hour 2020+ (min of 24): {[int(cnt[h*60:(h+1)*60].sum()) for h in range(24)]}")


# ------------------------------------------------------------ run 01 (sections 8 and 9)
def describe(T, label, emit):
    if len(T) == 0:
        emit(f"{label}: 0 trades"); return
    R = T["R"].values
    note = "  (insufficient trades)" if len(T) < 100 else ""
    emit(f"{label}: {len(T)} trades{note}, losers {np.mean(R < 0)*100:.1f}%, mean net R {R.mean():+.3f}, "
         f"sum {R.sum():+.1f} R, PF {pf(R):.2f}")


def real_run(a):
    out = []
    def emit(s=""):
        print(s, flush=True); out.append(s)
    m1 = load_mt5(a.csv)
    P = prepare(m1, 5)
    Tall = find_trades(P)
    D = P["D"]
    dyear = pd.to_datetime(D["td"] * 86400, unit="s")
    p1 = lambda T: T[(T["date"] >= pd.Timestamp("2020-01-02").date()) & (T["date"] <= pd.Timestamp("2026-11-05").date())]
    T = p1(Tall).reset_index(drop=True)
    days = D["td"][D["valid"] & (dyear >= "2020-01-02") & (dyear <= "2026-11-05") & ~np.isnan(D["pdh"])]
    emit("RUN 01 test S, script sweep_test.py, hypothesis v1.0")
    emit(f"P1: valid trading days {len(days)}, trades {len(T)}")
    emit("")
    # control group first
    opt = option_table(P, T)
    nb, na = run_nulls(T, opt, a.n, SEED_NULL)
    p1days = np.isin(D["td"], days)
    nt = null_t(P, T, p1days, a.n, SEED_NULL)
    real = T["R"].mean()
    emit("CONTROL GROUPS (first)")
    emit(f"Null B (random moment in same kill zone, coin flip, same stop): mean net R {nb.mean():+.3f} "
         f"(2.5-97.5%: {np.percentile(nb,2.5):+.3f} to {np.percentile(nb,97.5):+.3f}), 95th pct {np.percentile(nb,95):+.3f}")
    emit(f"Null A (same trades, coin flip): mean {na.mean():+.3f}, 95th pct {np.percentile(na,95):+.3f}")
    emit(f"Null T v1.1 (random valid day, same kill zone, direction = 1h trend, same stop in ATR units): mean {nt.mean():+.3f}, 95th pct {np.percentile(nt,95):+.3f}")
    emit("")
    emit("RULE")
    ci_m, ci_pf = boot(T, days, a.n, SEED_NULL)
    R = T["R"].values
    emit(f"P1 trades {len(T)}, losers {np.mean(R<0)*100:.1f}%, mean net R {real:+.3f} (95%: {ci_m[0]:+.3f} to {ci_m[1]:+.3f}), "
         f"PF {pf(R):.2f} (95%: {ci_pf[0]:.2f} to {ci_pf[1]:.2f}), sum {R.sum():+.1f} R")
    emit(f"percentile Null B {pct(real, nb):.1f} | Null A {pct(real, na):.1f} | Null T {pct(real, nt):.1f}")
    emit(f"gross (no costs) mean R {T['Rg'].mean():+.3f}, PF {pf(T['Rg'].values):.2f}; mean net points {T['net'].mean():+.2f}, "
         f"mean stop distance {T['d'].mean():.1f} pt (median {T['d'].median():.1f}), mean cost {T['cost'].mean():.2f} pt "
         f"= {(T['cost']/T['d']).mean():.3f} R")
    emit(f"stopped out {T['hit'].mean()*100:.1f}%, longest losing streak {streak(R)}, max drawdown {max_dd(R):.1f} R")
    top5 = T.sort_values("R", ascending=False).head(5)
    rest = T.drop(top5.index)["R"].values
    emit(f"5 best days: {', '.join(f'{d} {r:+.1f}R' for d, r in zip(top5['date'], top5['R']))}; PF without them {pf(rest):.2f}, "
         f"sum without them {rest.sum():+.1f} R")
    emit("")
    emit("VERDICT (section 8)")
    c1 = ci_pf[1] < 1.95
    emit(f"C1 PF 1.95: upper bound {ci_pf[1]:.2f} -> {'FALSIFIED' if c1 else 'not falsified'}")
    c2 = not (real > np.percentile(nb, 95))
    emit(f"C2 beats Null B: percentile {pct(real, nb):.1f} -> {'FALSIFIED' if c2 else 'not falsified'}")
    s1 = T[(T["year"] >= 2021) & (T["year"] <= 2024)]["R"].values
    s2 = T[(T["year"] >= 2025)]["R"].values
    c3 = pf(s1) <= 1.0 or pf(s2) <= 1.0
    emit(f"C3 2021-2024 PF {pf(s1):.2f} ({len(s1)} trades), 2025-2026 PF {pf(s2):.2f} ({len(s2)} trades) -> "
         f"{'FALSIFIED' if c3 else 'not falsified'}")
    emit("")
    emit("DESCRIPTIVE")
    describe(T[T["year"] >= 2021], "window 2021-2026 (claim: 290 trades)", emit)
    for y, g in T.groupby("year"):
        describe(g, f"year {y}", emit)
    describe(T[T["kz"] == 0], "London kill zone", emit)
    describe(T[T["kz"] == 1], "New York kill zone", emit)
    describe(T[T["side"] == 1], "long", emit)
    describe(T[T["side"] == -1], "short", emit)
    describe(T[(T["date"] >= pd.Timestamp("2026-01-01").date()) & (T["date"] <= pd.Timestamp("2026-09-30").date())],
             "Jan-Sep 2026 (claim: 33 trades, 5 winners, -23 R)", emit)
    # cost sensitivity
    for slip in (0.0, 1.0, 2.0):
        rr = np.array([trade_result(P, int(r.kday), int(r.e), int(r.side), r.d, slip=slip)["R"] for r in T.itertuples()])
        emit(f"slippage {slip:.0f} pt per side: mean R {rr.mean():+.3f}, PF {pf(rr):.2f}")
    rv = np.array([trade_result(P, int(r.kday), int(r.e), int(r.side), r.d, cost_mode="video")["R"] for r in T.itertuples()])
    emit(f"video cost level (0.01% per side, no spread): mean R {rv.mean():+.3f}, PF {pf(rv):.2f}; "
         f"2021-2026 PF {pf(rv[T['year'].values >= 2021]):.2f}")
    emit("")
    # P0
    T0 = Tall[(Tall["year"] >= 2013) & (Tall["year"] <= 2019)].reset_index(drop=True)
    emit("SUPPLEMENTARY P0 2013-2019")
    describe(T0, "P0", emit)
    if len(T0):
        d0 = D["td"][D["valid"] & (dyear.year >= 2013) & (dyear.year <= 2019) & ~np.isnan(D["pdh"])]
        o0 = option_table(P, T0)
        nb0, _ = run_nulls(T0, o0, a.n, SEED_NULL)
        nt0 = null_t(P, T0, np.isin(D["td"], d0), a.n, SEED_NULL)
        emit(f"P0 percentile Null B {pct(T0['R'].mean(), nb0):.1f}, Null T {pct(T0['R'].mean(), nt0):.1f}")
    # 15 min
    emit("")
    emit("SUPPLEMENTARY 15-minute bars, P1 (claim: PF 2.20)")
    P15 = prepare(m1, 15)
    T15 = p1(find_trades(P15)).reset_index(drop=True)
    describe(T15, "15 min P1", emit)
    if len(T15):
        o15 = option_table(P15, T15)
        nb15, _ = run_nulls(T15, o15, a.n, SEED_NULL)
        D15 = P15["D"]; y15 = pd.to_datetime(D15["td"] * 86400, unit="s")
        nt15 = null_t(P15, T15, (y15 >= "2020-01-02") & (y15 <= "2026-11-05"), a.n, SEED_NULL)
        emit(f"15 min percentile Null B {pct(T15['R'].mean(), nb15):.1f}, Null T {pct(T15['R'].mean(), nt15):.1f}")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "run01.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    cols = ["date", "kz", "side", "entry", "exit", "hit", "d", "atr", "pdh", "pdl", "ext", "gross", "cost", "net", "R", "Rg"]
    Tw = T.copy()
    Tw["entry_time_server"] = pd.to_datetime(m1["t"][Tw["e"].values] * 60, unit="s")
    Tw["exit_time_server"] = pd.to_datetime(m1["t"][Tw["xi"].values] * 60, unit="s")
    Tw["kz"] = Tw["kz"].map({0: "London", 1: "NewYork"})
    Tw[["date", "entry_time_server", "exit_time_server"] + cols[1:]].round(4).to_csv(
        os.path.join(a.out, "trades_p1.csv"), index=False)
    np.save(os.path.join(a.out, "null_b_means.npy"), nb)
    np.save(os.path.join(a.out, "null_t_means.npy"), nt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--datacheck", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--sets", type=int, default=24)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.noise:
        sys.exit(0 if noise_check(a.sets, a.seed, a.n or 2000) else 1)
    if a.datacheck:
        datacheck(a.csv); return
    if a.run:
        a.n = a.n or N_NULL
        real_run(a); return
    ap.print_help()


if __name__ == "__main__":
    main()
