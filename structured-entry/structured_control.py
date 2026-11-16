"""Test L: structured entry with MACD and the 4-hour colour EMA on BTCUSDT 30 min,
against a control group.

Implements hypothesis v1.0 (15 Nov 2026), Dutch original binding.
Signals are deterministic code. No price data is used for any choice.

Usage:
  python structured_control.py selftest           # indicator and add-arithmetic check
  python structured_control.py noise              # noise check (section 6)
  python structured_control.py run data.csv       # real run, all periods (section 7)

CSV columns: open_time_ms,open,high,low,close,volume (UTC, 30-minute bars).
"""
import sys
import math
import numpy as np
import pandas as pd
from numba import njit

BAR_MS = 30 * 60 * 1000
H4_MS = 4 * 60 * 60 * 1000
EMA_LEN = 200
TR_LAGS = (0, 5, 10, 15, 20, 30, 40, 50)
MIN_STOP = 0.005        # 4.7: entry 1 to stop under 0.5% of price: no trade
SPACING = 0.10          # 4.6: add at least 10% of (entry 1 - stop) beyond the previous entry
COST_SIDE = 0.0006      # 0.06% per side
M_Z = 0.5               # 4.5 target single entry
N_NULL = 10000
SEED_NULL = 41
SEED_NOISE = 7

# ---------------------------------------------------------------- indicators

def pine_ema(x, n):
    """Pine ta.ema: alpha 2/(n+1), first value the SMA of the first n values."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    a = 2.0 / (n + 1)
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out

def macd(c, fast=12, slow=26, sig=9):
    m = pine_ema(c, fast) - pine_ema(c, slow)
    s = np.full(len(c), np.nan)
    first = np.where(~np.isnan(m))[0][0]
    s[first:] = pine_ema(m[first:], sig)
    return m, s

def four_hour(ms, c):
    """4-hour closes from 30-minute bars, grouped on 00:00/04:00/... UTC.
    Returns group start (ms) per 4h bar, 4h close, and for each 30m bar the index of
    the last CLOSED 4h bar at its close (-1 if none)."""
    g = ms // H4_MS
    starts, first_idx = np.unique(g, return_index=True)
    last_idx = np.r_[first_idx[1:] - 1, len(ms) - 1]
    c4 = c[last_idx]
    # at the close of 30m bar t (time ms+30min) the last closed 4h group is floor((ms+30m)/4h)-1
    closed_g = (ms + BAR_MS) // H4_MS - 1
    pos = np.searchsorted(starts, closed_g, side="right") - 1
    ok = (pos >= 0) & (starts[np.clip(pos, 0, None)] == closed_g)
    # a 4h group only counts as closed once its last 30m bar has closed; groups are
    # time-based, so a gap at the end of a group still closes it at the group end
    idx = np.where(ok, pos, -1)
    return starts, c4, idx

def colour_ema(c4, n=EMA_LEN):
    """Colour of the 200 EMA on the 4h bars: +1 green, -1 red, 0 none, exactly the public code."""
    e = pine_ema(c4, n)
    col = np.zeros(len(c4), np.int64)
    for i in range(len(c4)):
        if i < max(TR_LAGS) or np.isnan(e[i - max(TR_LAGS)]):
            continue
        up = all(c4[i - k] > e[i - k] for k in TR_LAGS)
        dn = all(c4[i - k] < e[i - k] for k in TR_LAGS)
        col[i] = 1 if up else (-1 if dn else 0)
    return e, col

def build(df, plain_ema=False):
    ms = df["open_time_ms"].to_numpy(np.int64)
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    starts, c4, idx = four_hour(ms, c)
    e4, col4 = colour_ema(c4)
    stopv = np.where(idx >= 0, e4[np.clip(idx, 0, None)], np.nan)
    colour = np.where(idx >= 0, col4[np.clip(idx, 0, None)], 0)
    if plain_ema:  # sensitivity: plain 4h 200 EMA without the colour condition
        colour = np.where(np.isnan(stopv), 0, np.where(c > stopv, 1, np.where(c < stopv, -1, 0)))
    m, s = macd(c)
    # filter of 4.4 without the MACD conditions
    eldir = np.where((colour == 1) & (c > stopv), 1, np.where((colour == -1) & (c < stopv), -1, 0)).astype(np.int64)
    eldir[np.isnan(stopv)] = 0
    cross_up = np.zeros(len(c), bool)
    cross_dn = np.zeros(len(c), bool)
    cross_up[1:] = (m[:-1] <= s[:-1]) & (m[1:] > s[1:])
    cross_dn[1:] = (m[:-1] >= s[:-1]) & (m[1:] < s[1:])
    below0 = (m < 0) & (s < 0)
    above0 = (m > 0) & (s > 0)
    sig = np.where(cross_up & below0 & (eldir == 1), 1, np.where(cross_dn & above0 & (eldir == -1), -1, 0)).astype(np.int64)
    aux = {"cross_up": cross_up, "cross_dn": cross_dn, "below0": below0, "above0": above0,
           "colour": colour, "e4": e4, "c4": c4, "starts4": starts, "idx4": idx, "macd": m, "signal": s}
    return ms, o, h, l, c, stopv, eldir, sig, aux

# ---------------------------------------------------------------- simulation

@njit(cache=True)
def sim(o, h, l, c, stopv, sig, eldir, p, use_random, lo, hi, structured, m_single,
        minstop, spacing, cost_side, rec):
    """One pass through bars lo..hi-1. structured=1: variant G, else single entry with
    target m_single R. Signals: sig (rule) or, if use_random, eldir with probability p.
    rec (n x 8 array) gets one row per setup: start, dir, n_entries, exit_bar, win,
    result_pct (account % at 1% risk per entry for G, 3% for single), result_R, open_end.
    Returns (n_setups, n_minstop_drop, n_lapsed, n_add_refused, n_signals)."""
    n_set = 0
    n_min = 0
    n_lap = 0
    n_ref = 0
    n_sig = 0
    inpos = False
    d = 0
    S = 0.0
    k = 0
    e = np.zeros(3)
    w = np.zeros(3)
    tgt = 0.0
    start = 0
    r1 = 0.0
    j = lo
    while j < hi:
        # signal at the close of bar j
        sd = 0
        if use_random:
            if eldir[j] != 0 and np.random.random() < p:
                sd = eldir[j]
        else:
            sd = sig[j]
        if sd != 0:
            n_sig += 1
        if inpos:
            # bar j: stop first, then target
            px = 0.0
            hit = 0
            if d == 1:
                if l[j] <= S:
                    px = min(o[j], S); hit = -1
                elif h[j] >= tgt:
                    px = max(o[j], tgt); hit = 1
            else:
                if h[j] >= S:
                    px = max(o[j], S); hit = -1
                elif l[j] <= tgt:
                    px = min(o[j], tgt); hit = 1
            if hit != 0:
                res = 0.0
                for i in range(k):
                    res += w[i] * (d * (px - e[i]) - cost_side * (e[i] + px))
                rec[n_set, 0] = start; rec[n_set, 1] = d; rec[n_set, 2] = k; rec[n_set, 3] = j
                rec[n_set, 4] = 1.0 if hit == 1 else 0.0
                rec[n_set, 5] = 100.0 * res
                rec[n_set, 6] = res / (k * (0.01 if structured == 1 else 0.03))
                rec[n_set, 7] = 0.0
                n_set += 1
                inpos = False
                j += 1          # no new setup on the exit bar
                continue
            # still open: add?
            if sd != 0:
                if structured == 1 and sd == d and k < 3:
                    pe = c[j]
                    if d * (e[k - 1] - pe) >= spacing * r1 and d * (pe - S) > 0:
                        e[k] = pe
                        w[k] = 0.01 / (d * (pe - S))
                        k += 1
                        sw = 0.0; se = 0.0
                        for i in range(k):
                            sw += w[i]; se += w[i] * e[i]
                        avg = se / sw
                        mk = 0.5 if k == 3 else 0.25
                        tgt = avg + mk * (avg - S)
                    else:
                        n_ref += 1
                else:
                    n_lap += 1
            j += 1
            continue
        # flat
        if sd != 0:
            pe = c[j]
            Sv = stopv[j]
            risk = sd * (pe - Sv)
            if risk <= 0 or risk / pe < minstop:
                n_min += 1
            else:
                inpos = True
                d = sd
                S = Sv
                k = 1
                e[0] = pe
                start = j
                r1 = risk
                if structured == 1:
                    w[0] = 0.01 / risk
                    tgt = pe + d * 0.25 * risk
                else:
                    w[0] = 0.03 / risk
                    tgt = pe + d * m_single * risk
        j += 1
    if inpos:  # open at the end of the data: close on the last close
        px = c[hi - 1]
        res = 0.0
        for i in range(k):
            res += w[i] * (d * (px - e[i]) - cost_side * (e[i] + px))
        rec[n_set, 0] = start; rec[n_set, 1] = d; rec[n_set, 2] = k; rec[n_set, 3] = hi - 1
        rec[n_set, 4] = 1.0 if res > 0 else 0.0
        rec[n_set, 5] = 100.0 * res
        rec[n_set, 6] = res / (k * (0.01 if structured == 1 else 0.03))
        rec[n_set, 7] = 1.0
        n_set += 1
    return n_set, n_min, n_lap, n_ref, n_sig

@njit(cache=True)
def null_runs(o, h, l, c, stopv, sig, eldir, p, lo, hi, structured, m_single, minstop,
              spacing, cost_side, nrun, seed, col):
    """Null A: random signal with probability p on every filter bar, same rules.
    Returns the per-run mean of rec[:, col] and the setup count per run."""
    np.random.seed(seed)
    out = np.full(nrun, np.nan)
    cnt = np.zeros(nrun, np.int64)
    rec = np.zeros((hi - lo + 1, 8))
    for r in range(nrun):
        ns, a, b, cc, dd = sim(o, h, l, c, stopv, sig, eldir, p, True, lo, hi, structured,
                               m_single, minstop, spacing, cost_side, rec)
        cnt[r] = ns
        if ns > 0:
            out[r] = rec[:ns, col].mean()
    return out, cnt

def run_variant(o, h, l, c, stopv, sig, eldir, lo, hi, structured, m_single=M_Z,
                minstop=MIN_STOP, spacing=SPACING, cost_side=COST_SIDE):
    rec = np.zeros((hi - lo + 1, 8))
    ns, nmin, nlap, nref, nsig = sim(o, h, l, c, stopv, sig, eldir, 0.0, False, lo, hi, structured,
                                     m_single, minstop, spacing, cost_side, rec)
    return rec[:ns].copy(), {"signals": nsig, "dropped_min_stop": nmin, "lapsed_open_position": nlap,
                             "adds_refused": nref, "setups": ns}

def null_compare(o, h, l, c, stopv, sig, eldir, lo, hi, structured, rec_real, nrun=N_NULL, seed=SEED_NULL,
                 m_single=M_Z, minstop=MIN_STOP, spacing=SPACING, cost_side=COST_SIDE):
    n_sig = int((sig[lo:hi] != 0).sum())
    n_el = int((eldir[lo:hi] != 0).sum())
    p = n_sig / max(n_el, 1)
    col = 5 if structured == 1 else 6
    real = float(rec_real[:, col].mean()) if len(rec_real) else float("nan")
    m, cn = null_runs(o, h, l, c, stopv, sig, eldir, p, lo, hi, structured, m_single, minstop,
                      spacing, cost_side, nrun, seed, col)
    m = m[~np.isnan(m)]
    pct = 100.0 * ((m < real).sum() + 0.5 * (m == real).sum()) / len(m) if len(m) else float("nan")
    return real, {"p": p, "filter_bars": n_el, "runs_complete": int(len(m)),
                  "p5": float(np.percentile(m, 5)), "p50": float(np.percentile(m, 50)),
                  "p95": float(np.percentile(m, 95)), "percentile": pct, "mean_setups_per_run": float(cn.mean())}

# ---------------------------------------------------------------- statistics

def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    cc = (p + z * z / (2 * n)) / (1 + z * z / n)
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return cc - hw, cc + hw

def pf(x):
    g = x[x > 0].sum()
    ls = -x[x < 0].sum()
    return g / ls if ls > 0 else float("inf")

def boot_week(x, weeks, nb=10000, seed=11):
    """Bootstrap of the mean, resampling whole weeks."""
    rng = np.random.default_rng(seed)
    uw, inv = np.unique(weeks, return_inverse=True)
    sums = np.bincount(inv, weights=x)
    cnts = np.bincount(inv)
    v = np.empty(nb)
    for b in range(nb):
        pick = rng.integers(0, len(uw), len(uw))
        v[b] = sums[pick].sum() / cnts[pick].sum()
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))

def summary(rec, ms, structured, c, stopv):
    if len(rec) == 0:
        return {"n": 0}
    col = 5 if structured == 1 else 6
    x = rec[:, col]
    win = rec[:, 4]
    n = len(x)
    lo, hi = wilson(int(win.sum()), n)
    weeks = ms[rec[:, 0].astype(int)] // (7 * 24 * 3600 * 1000)
    streak = best = 0
    for v in win:
        streak = streak + 1 if v == 0 else 0
        best = max(best, streak)
    st = rec[:, 0].astype(int)
    stop_pct = 100 * np.abs(c[st] - stopv[st]) / c[st]
    ne = rec[:, 2].astype(int)
    return {
        "n": n, "winrate": 100 * win.mean(), "winrate_95": (100 * lo, 100 * hi),
        "mean": float(x.mean()), "mean_95": boot_week(x, weeks), "unit": "account % per setup" if structured == 1 else "net R per trade",
        "mean_R_per_unit_risk": float(rec[:, 6].mean()),
        "pf": pf(x), "median_stop_pct": float(np.median(stop_pct)), "cost_rt_pct": 200 * COST_SIDE,
        "best": float(x.max()), "worst": float(x.min()), "longest_losing_streak": best,
        "mean_bars": float((rec[:, 3] - rec[:, 0]).mean()),
        "entries_1_2_3": [int((ne == 1).sum()), int((ne == 2).sum()), int((ne == 3).sum())],
        "long": int((rec[:, 1] == 1).sum()), "short": int((rec[:, 1] == -1).sum()),
        "open_at_end": int(rec[:, 7].sum()),
    }

# ---------------------------------------------------------------- noise check

def fake_market(nbars, rng, vol_year=0.60, sub=30):
    sig_min = vol_year / math.sqrt(365 * 24 * 60)
    steps = rng.normal(0.0, sig_min, size=(nbars, sub))
    path = np.cumsum(steps.ravel()).reshape(nbars, sub)
    start = np.r_[0.0, path[:-1, -1]]
    full = np.concatenate([start[:, None], path], axis=1)
    price = 30000.0 * np.exp(full)
    t0 = int(pd.Timestamp("2019-01-01", tz="UTC").value // 10**6)
    return pd.DataFrame({"open_time_ms": t0 + BAR_MS * np.arange(nbars, dtype=np.int64),
                         "open": price[:, 0], "high": price.max(axis=1),
                         "low": price.min(axis=1), "close": price[:, -1]})

def first_valid(stopv, aux):
    col_ok = np.where(aux["idx4"] >= 0)[0]
    e_ok = np.where(~np.isnan(stopv))[0]
    # first 30m bar whose closed 4h bar has 200 + 50 bars of history
    need = EMA_LEN - 1 + max(TR_LAGS)
    ok = np.where(aux["idx4"] >= need)[0]
    return int(ok[0])

def noise(nsets=24, nbars=6 * 365 * 48, nrun=2000):
    rng = np.random.default_rng(SEED_NOISE)
    res = {1: [], 0: []}
    for s in range(nsets):
        df = fake_market(nbars, rng)
        ms, o, h, l, c, stopv, eldir, sig, aux = build(df)
        lo = first_valid(stopv, aux)
        line = "set %2d" % s
        for structured in (1, 0):
            rec, fun = run_variant(o, h, l, c, stopv, sig, eldir, lo, len(c), structured)
            real, nr = null_compare(o, h, l, c, stopv, sig, eldir, lo, len(c), structured, rec,
                                    nrun=nrun, seed=SEED_NULL + s)
            res[structured].append(nr["percentile"])
            line += "  %s n %4d win %5.1f pct %5.1f" % ("G" if structured else "Z", len(rec), 100 * rec[:, 4].mean(), nr["percentile"])
        print(line, flush=True)
    for structured in (1, 0):
        pc = np.array(res[structured])
        ok = 35 <= pc.mean() <= 65 and (pc > 95).sum() <= 3
        print("variant %s: mean percentile %.1f, above 95: %d of %d -> %s" % (
            "G" if structured else "Z", pc.mean(), (pc > 95).sum(), len(pc), "PASSED" if ok else "FAILED"))

# ---------------------------------------------------------------- self test

def selftest():
    rng = np.random.default_rng(3)
    df = fake_market(20000, rng)
    ms, o, h, l, c, stopv, eldir, sig, aux = build(df)
    # 4h close by hand
    t = 15000
    g = ms[t] // H4_MS
    print("bar t closes at", pd.Timestamp(ms[t] + BAR_MS, unit="ms", tz="UTC"))
    i4 = aux["idx4"][t]
    grp = np.where(ms // H4_MS == aux["starts4"][i4])[0]
    print("last closed 4h group starts", pd.Timestamp(aux["starts4"][i4] * H4_MS, unit="ms", tz="UTC"),
          "ends", pd.Timestamp(ms[grp[-1]] + BAR_MS, unit="ms", tz="UTC"), "close4 code %.4f hand %.4f" % (aux["c4"][i4], c[grp[-1]]))
    # EMA by hand
    c4 = aux["c4"]
    e = c4[:200].mean()
    for k in range(200, i4 + 1):
        e = 2 / 201 * c4[k] + (1 - 2 / 201) * e
    print("EMA4h  code %.6f  hand %.6f  stopv[t] %.6f" % (aux["e4"][i4], e, stopv[t]))
    ee = aux["e4"]
    up = all(c4[i4 - k] > ee[i4 - k] for k in TR_LAGS)
    dn = all(c4[i4 - k] < ee[i4 - k] for k in TR_LAGS)
    print("colour code %d  hand %d" % (aux["colour"][t], 1 if up else (-1 if dn else 0)))
    # MACD by hand
    def ema_hand(x, n):
        v = np.mean(x[:n]); out = [np.nan] * (n - 1) + [v]
        for xx in x[n:]:
            v = 2 / (n + 1) * xx + (1 - 2 / (n + 1)) * v; out.append(v)
        return np.array(out)
    mh = ema_hand(c, 12) - ema_hand(c, 26)
    sh = np.full(len(c), np.nan); sh[25:] = ema_hand(mh[25:], 9)
    print("MACD   code %.6f hand %.6f  signal code %.6f hand %.6f" % (aux["macd"][t], mh[t], aux["signal"][t], sh[t]))
    # add arithmetic on a hand-made long setup: stop 90, entries 100, 98, 95
    o_ = np.array([100, 100, 99, 97, 95, 95, 96, 100.0])
    h_ = np.array([100, 100.5, 99, 97, 95, 96, 97.5, 101.0])
    l_ = np.array([100, 99, 97.5, 95, 94.5, 94.8, 95.5, 99.5])
    c_ = np.array([100, 99, 98, 96, 95, 95.5, 96, 100.5])
    sv = np.full(8, 90.0)
    sg = np.array([1, 0, 1, 0, 1, 0, 0, 0])
    el = np.ones(8, np.int64)
    rec = np.zeros((10, 8))
    ns = sim(o_, h_, l_, c_, sv, sg, el, 0.0, False, 0, 8, 1, 0.5, 0.0, 0.10, 0.0, rec)
    w = np.array([0.01 / 10, 0.01 / 8, 0.01 / 5])
    ent = np.array([100, 98, 95.0])
    avg = (w * ent).sum() / w.sum()
    tgt = avg + 0.5 * (avg - 90)
    print("G hand: avg %.4f target %.4f; result if target hit %.4f%%" % (avg, tgt, 100 * (w * (tgt - ent)).sum()))
    print("G code: setups %d, entries %d, exit bar %d, win %d, result %.4f%%" % (ns[0], rec[0, 2], rec[0, 3], rec[0, 4], rec[0, 5]))

# ---------------------------------------------------------------- real run

PERIODS = {  # UTC, end exclusive
    "P1": (None, "2026-11-15"),
    "P0": ("2020-09-28", "2024-09-28"),
    "P2": ("2024-09-28", "2026-11-15"),
}

def bounds(ms, lo0, a, b):
    lo = lo0 if a is None else max(lo0, int(np.searchsorted(ms, pd.Timestamp(a, tz="UTC").value // 10**6)))
    hi = int(np.searchsorted(ms, pd.Timestamp(b, tz="UTC").value // 10**6))
    return lo, hi

def report(tag, df, ms, o, h, l, c, stopv, eldir, sig, aux, lo, hi, structured, nrun=N_NULL, save=None, **kw):
    rec, fun = run_variant(o, h, l, c, stopv, sig, eldir, lo, hi, structured, **kw)
    s = summary(rec, ms, structured, c, stopv)
    real, nr = null_compare(o, h, l, c, stopv, sig, eldir, lo, hi, structured, rec, nrun=nrun, **kw) if len(rec) else (float("nan"), {})
    print("\n=== %s %s  %s to %s" % (tag, "G" if structured == 1 else ("Z" if kw.get("m_single", M_Z) == M_Z else "Z025"),
                                  df["time"].iloc[lo], df["time"].iloc[hi - 1]))
    print("funnel", fun)
    print("summary", s)
    print("NullA", nr)
    if save:
        out = pd.DataFrame(rec, columns=["start_bar", "dir", "entries", "exit_bar", "win", "result_pct", "result_R", "open_at_end"])
        out["start_time"] = df["time"].iloc[out["start_bar"].astype(int)].values
        out["exit_time"] = df["time"].iloc[out["exit_bar"].astype(int)].values
        out.to_csv(save, index=False)
    return rec, s, nr

def funnel_bars(sig, eldir, aux, lo, hi):
    a = aux
    sl = slice(lo, hi)
    return {"bars_after_warmup": hi - lo,
            "bars_colour_green_or_red": int((a["colour"][sl] != 0).sum()),
            "bars_filter_ok": int((eldir[sl] != 0).sum()),
            "macd_cross_in_filter_direction": int((((a["cross_up"]) & (eldir == 1)) | ((a["cross_dn"]) & (eldir == -1)))[sl].sum()),
            "and_right_side_of_zero": int((sig[sl] != 0).sum())}

def run(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["open_time_ms"], unit="ms", utc=True)
    ms, o, h, l, c, stopv, eldir, sig, aux = build(df)
    lo0 = first_valid(stopv, aux)
    print("first valid bar", df["time"].iloc[lo0])
    for name, (a, b) in PERIODS.items():
        lo, hi = bounds(ms, lo0, a, b)
        print("\n##### %s funnel" % name, funnel_bars(sig, eldir, aux, lo, hi))
        report(name, df, ms, o, h, l, c, stopv, eldir, sig, aux, lo, hi, 1, save="trades_G_%s.csv" % name)
        report(name, df, ms, o, h, l, c, stopv, eldir, sig, aux, lo, hi, 0, save="trades_Z_%s.csv" % name)
        if name == "P1":
            report(name, df, ms, o, h, l, c, stopv, eldir, sig, aux, lo, hi, 0, m_single=0.25, nrun=2000, save="trades_Z025_P1.csv")
    # P3: per year and long/short within P1
    lo, hi = bounds(ms, lo0, None, "2026-11-15")
    for structured in (1, 0):
        rec, _ = run_variant(o, h, l, c, stopv, sig, eldir, lo, hi, structured)
        yrs = df["time"].dt.year.to_numpy()[rec[:, 0].astype(int)]
        col = 5 if structured == 1 else 6
        print("\n=== P3 %s" % ("G" if structured == 1 else "Z"))
        for y in np.unique(yrs):
            r = rec[yrs == y]
            print("  %d  n %4d  win %5.1f  mean %+.4f%s" % (y, len(r), 100 * r[:, 4].mean(), r[:, col].mean(), "  (onder 100)" if len(r) < 100 else ""))
        for d, nm in ((1, "long"), (-1, "short")):
            r = rec[rec[:, 1] == d]
            if len(r):
                print("  %-5s n %4d  win %5.1f  mean %+.4f%s" % (nm, len(r), 100 * r[:, 4].mean(), r[:, col].mean(), "  (onder 100)" if len(r) < 100 else ""))
    # sensitivities (P1, not decisive)
    print("\n##### sensitivities P1 (not decisive), 2,000 null runs")
    for structured in (1, 0):
        for kw, tg in (({"spacing": 0.0}, "spacing 0%"), ({"spacing": 0.25}, "spacing 25%"),
                       ({"minstop": 0.0}, "no min stop"), ({"minstop": 0.01}, "min stop 1.0%"),
                       ({"cost_side": 0.0}, "cost 0"), ({"cost_side": 0.0010}, "cost 0.20% rt")):
            if structured == 0 and "spacing" in kw:
                continue
            print("\n-- %s" % tg)
            report("P1", df, ms, o, h, l, c, stopv, eldir, sig, aux, lo, hi, structured, nrun=2000, **kw)
    ms2, o2, h2, l2, c2, stopv2, eldir2, sig2, aux2 = build(df, plain_ema=True)
    print("\n-- plain 4h 200 EMA without colour")
    for structured in (1, 0):
        report("P1", df, ms2, o2, h2, l2, c2, stopv2, eldir2, sig2, aux2, lo, hi, structured, nrun=2000)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    if mode == "noise":
        noise()
    elif mode == "selftest":
        selftest()
    elif mode == "run":
        run(sys.argv[2])
