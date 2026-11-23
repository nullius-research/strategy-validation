"""Test Q: morning star / evening star with a trend filter on gold (XAUUSD H1), fixed 2R target,
plus a two-phase prop firm challenge simulation.

Hypothesis v1.0 (21 Nov 2026, Dutch original binding), fixed before looking at price data. Rules:
  data     : MT5 M30 export, broker time. H1 bars built per broker hour. Trade paths walked on M30.
  MAs (K1A): SMA 14 and SMA 200 on H1 closes, value of the closed bar.
  pattern (K2A) on H1 bars t-2, t-1, t, body = |close - open|:
             morning star: t-2 falling; body(t-1) <= 1/3 body(t-2); t rising and close(t) > middle of body(t-2).
             evening star mirrored.
  filter   : long only if close(t) > SMA14 and > SMA200; short only if below both.
  entry(K3A): buy stop at high(t) (sell stop at low(t)), valid only in H1 bar t+1, walked on M30.
             An M30 bar that opens beyond the level enters at its open.
  stop     : lowest low of t-2..t (short: highest high); target entry + 2 x (entry - stop).
             No trade if the stop distance from the actual entry is below 1.00 USD. No time exit.
  path     : in the entry M30 bar only the stop counts; from the next bar: open beyond stop or target exits
             at the open; stop and target in one bar = stop.
  costs    : 0.40 USD per ounce round trip (sensitivity 0 and 0.80). R = net USD per oz / stop distance.
  one position at a time.
Controls: random sequential process, one position at a time. After each exit (or the start) a wait in H1
  bars drawn from the rule's own waits, then entry at the open of the first H1 bar whose previous bar meets
  the null's filter. Stop distance = multiple of ATR(14, Wilder, H1, previous closed bar) drawn from the
  rule's own stops (20 quantiles); target 2R; below 1.00 USD no trade. Same costs and path rules.
  Null A (decisive): trend filter only (close above both SMAs: long; below both: short).
  Null B (supplement): coin flip on every bar.
Prop firm (firm A, two phases, K4A): $100,000; risk $1,000 per trade; daily loss $5,000 below the balance at
  the start of the broker day, on equity incl. open loss; max loss: equity below $90,000; target 10% then
  5% on closed balance with at least 4 trading days with an entry per phase; phase 2 starts the next trading
  day. 1,000 random start days in P1 (excluding the last 365 days); unfinished after 365 calendar days or at
  the end of the data = not finished.
Usage: python morning_star.py data.csv              real data
       python morning_star.py --selftest            self-test on synthetic data
       python morning_star.py --synthetic 24 [sub] noise check (sub = price steps per M30 bar, default 60)
"""
import sys
import numpy as np
import pandas as pd
from numba import njit

COST, COSTS = 0.40, (0.0, 0.40, 0.80)
MIN_STOP, TGT_R, ATR_N = 1.00, 2.0, 14
RUNS, SEED, K = 10000, 31, 20
ACC, RISK, DAILY, MAXLOSS, TGT1, TGT2, MINDAYS = 100000.0, 1000.0, 5000.0, 90000.0, 10000.0, 5000.0, 4
NCHAL, NCHAL_NULL, HORIZON = 1000, 2000, 365


# ---------- data ----------
def load(path):
    d = pd.read_csv(path, sep="\t")
    d.columns = [c.strip("<>").upper() for c in d.columns]
    d["TIME"] = pd.to_datetime(d["DATE"] + " " + d["TIME"], format="%Y.%m.%d %H:%M:%S")
    return d[["TIME", "OPEN", "HIGH", "LOW", "CLOSE", "SPREAD"]].sort_values("TIME").reset_index(drop=True)


def usable_start(d, min_bars=40):
    per_day = d.groupby(d["TIME"].dt.date).size()
    per_day.index = pd.to_datetime(per_day.index)
    ok = per_day.groupby(per_day.index.to_period("M")).min() >= min_bars
    return ok[ok].index[0].to_timestamp()


def bars(d, key):
    g = d.assign(IDX=np.arange(len(d))).groupby(key, sort=False)
    return pd.DataFrame({
        "i0": g["IDX"].first(), "i1": g["IDX"].last(),
        "OPEN": g["OPEN"].first(), "HIGH": g["HIGH"].max(), "LOW": g["LOW"].min(), "CLOSE": g["CLOSE"].last(),
        "START": g["TIME"].first(), "END": g["TIME"].last() + pd.Timedelta(minutes=30)}).reset_index(drop=True)


def wilder_atr(h, l, c, n=ATR_N):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr = np.full(len(c), np.nan)
    if len(c) > n:
        atr[n - 1] = tr[:n].mean()
        for i in range(n, len(c)):
            atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
    return atr


def sma(x, n):
    return pd.Series(x).rolling(n).mean().to_numpy()


def pattern(o, h, l, c):
    """Vectorised pattern on bar t (uses t-2, t-1, t). +1 morning star, -1 evening star, 0 none."""
    b = np.abs(c - o)
    out = np.zeros(len(c), np.int8)
    o2, c2, b2 = o[:-2], c[:-2], b[:-2]          # t-2
    b1 = b[1:-1]                                  # t-1
    o0, c0 = o[2:], c[2:]                         # t
    mid = (o2 + c2) / 2.0
    ms = (c2 < o2) & (b1 <= b2 / 3.0) & (c0 > o0) & (c0 > mid)
    es = (c2 > o2) & (b1 <= b2 / 3.0) & (c0 < o0) & (c0 < mid)
    out[2:][ms] = 1
    out[2:][es] = -1
    return out


def pattern_loop(o, h, l, c):
    """Second, independent implementation for the self-test."""
    out = []
    for t in range(len(c)):
        v = 0
        if t >= 2:
            body2 = abs(c[t - 2] - o[t - 2]); body1 = abs(c[t - 1] - o[t - 1])
            middle = o[t - 2] + (c[t - 2] - o[t - 2]) / 2
            small = body1 * 3 <= body2 + 1e-12
            if c[t - 2] < o[t - 2] and small and c[t] > o[t] and c[t] > middle:
                v = 1
            elif c[t - 2] > o[t - 2] and small and c[t] < o[t] and c[t] < middle:
                v = -1
        out.append(v)
    return np.array(out, np.int8)


def prepare(d):
    t = d["TIME"]
    date = t.dt.normalize()
    h1 = bars(d, [date, t.dt.hour])
    h1["DATE"] = h1["START"].dt.normalize()
    dates = np.sort(h1["DATE"].unique())
    h1["DIDX"] = np.searchsorted(dates, h1["DATE"].to_numpy())
    o, h, l, c = (h1[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    h1["ATR"] = wilder_atr(h, l, c)
    s14, s200 = sma(c, 14), sma(c, 200)
    trend = np.zeros(len(c), np.int8)
    ok = ~np.isnan(s200)
    trend[ok & (c > s14) & (c > s200)] = 1
    trend[ok & (c < s14) & (c < s200)] = -1
    pat = pattern(o, h, l, c)
    sig = np.where(pat == trend, pat, 0).astype(np.int8)
    sig[~ok] = 0
    m30_h1 = np.zeros(len(d), np.int64)
    for k, (a, b_) in enumerate(zip(h1["i0"].to_numpy(), h1["i1"].to_numpy())):
        m30_h1[a:b_ + 1] = k
    mdate = d["TIME"].dt.normalize().to_numpy()
    return dict(h1=h1, trend=trend, pat=pat, sig=sig, m30_h1=m30_h1, mdate=mdate)


# ---------- path ----------
@njit
def walk(o, h, l, c, k0, entry, dirn, stop, tgt):
    """Path from entry M30 bar k0. Returns (exit index, exit price, finished flag)."""
    n = len(c)
    if dirn == 1:
        if l[k0] <= stop:
            return k0, stop, 1
    else:
        if h[k0] >= stop:
            return k0, stop, 1
    for k in range(k0 + 1, n):
        if dirn == 1:
            if o[k] <= stop:
                return k, o[k], 1
            if o[k] >= tgt:
                return k, o[k], 1
            if l[k] <= stop:
                return k, stop, 1
            if h[k] >= tgt:
                return k, tgt, 1
        else:
            if o[k] >= stop:
                return k, o[k], 1
            if o[k] <= tgt:
                return k, o[k], 1
            if h[k] >= stop:
                return k, stop, 1
            if l[k] <= tgt:
                return k, tgt, 1
    return n - 1, c[n - 1], 0


@njit
def fill(o, h, l, i0, i1, lvl, dirn):
    """Stop order at lvl in the M30 bars i0..i1. Returns (bar, price) or (-1, nan)."""
    for k in range(i0, i1 + 1):
        if dirn == 1:
            if o[k] >= lvl:
                return k, o[k]
            if h[k] >= lvl:
                return k, lvl
        else:
            if o[k] <= lvl:
                return k, o[k]
            if l[k] <= lvl:
                return k, lvl
    return -1, np.nan


def rule_trades(d, P, mask_h1):
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
        k0, entry = fill(o, hh, ll, i0[t + 1], i1[t + 1], lvl, dirn)
        if k0 < 0:
            stats["unfilled"] += 1
            continue
        dist = (entry - stop) * dirn
        if dist < MIN_STOP:
            stats["dropped"] += 1
            continue
        tgt = entry + dirn * TGT_R * dist
        k, px, fin = walk(o, hh, ll, cc, k0, entry, dirn, stop, tgt)
        rows.append((t, k0, k, dirn, entry, stop, tgt, dist, atr[t], px, (px - entry) * dirn, fin))
        busy_until = k
    tr = pd.DataFrame(rows, columns=["SIG_H1", "ENTRY_M30", "EXIT_M30", "DIR", "ENTRY", "STOP", "TARGET", "DIST",
                                     "ATR", "EXIT", "GROSS_USD", "FINISHED"])
    for cst in COSTS:
        tr[f"R_{cst:.2f}"] = (tr["GROSS_USD"] - cst) / tr["DIST"]
    tr["R_NET"] = tr[f"R_{COST:.2f}"]
    return tr, stats


# ---------- controls ----------
@njit
def null_table(o, h, l, c, elig, i0h, atr_prev, mults, cost, min_stop):
    nq = len(mults); n = len(elig)
    EX = np.full((2, nq, n), -1, np.int64); RN = np.full((2, nq, n), np.nan)
    for e in range(n):
        if not elig[e]:
            continue
        k0 = i0h[e]; entry = o[k0]
        for q in range(nq):
            dist = mults[q] * atr_prev[e]
            if dist < min_stop:
                continue
            for di in range(2):
                dirn = 1 if di == 0 else -1
                stop = entry - dirn * dist; tgt = entry + dirn * TGT_R * dist
                k, px, fin = walk(o, h, l, c, k0, entry, dirn, stop, tgt)
                EX[di, q, e] = k
                RN[di, q, e] = ((px - entry) * dirn - cost) / dist
    return EX, RN


@njit
def null_seq(EX, RN, m30_h1, elig_idx, fixdir, start_ptr, end_h1, waits, use_fixed, seed, out_e, out_q, out_d):
    """One sequential control run. Fills out_* arrays with chosen (bar, quantile, dir index); returns count."""
    nq = EX.shape[1]
    ptr = start_ptr; cnt = 0; skipped = False
    while True:
        w = waits[np.random.randint(0, len(waits))]
        if skipped and w < 1:
            w = 1
        skipped = False
        k = np.searchsorted(elig_idx, ptr + w)
        if k >= len(elig_idx):
            break
        e = elig_idx[k]
        if e > end_h1:
            break
        q = np.random.randint(0, nq)
        if use_fixed:
            di = 0 if fixdir[e] == 1 else 1
        else:
            di = 0 if np.random.random() < 0.5 else 1
        if EX[di, q, e] < 0:
            ptr = e; skipped = True
            continue
        out_e[cnt] = e; out_q[cnt] = q; out_d[cnt] = di; cnt += 1
        ptr = m30_h1[EX[di, q, e]]
    return cnt


@njit
def run_null(EX, RN, m30_h1, elig_idx, fixdir, start_ptr, end_h1, waits, use_fixed, runs, seed):
    np.random.seed(seed)
    means = np.empty(runs); counts = np.empty(runs, np.int64)
    n = len(m30_h1)
    oe = np.empty(n, np.int64); oq = np.empty(n, np.int64); od = np.empty(n, np.int64)
    for t in range(runs):
        cnt = null_seq(EX, RN, m30_h1, elig_idx, fixdir, start_ptr, end_h1, waits, use_fixed, seed, oe, oq, od)
        s = 0.0
        for j in range(cnt):
            s += RN[od[j], oq[j], oe[j]]
        means[t] = s / cnt if cnt > 0 else np.nan
        counts[t] = cnt
    return means, counts


@njit
def seed_nb(s):
    np.random.seed(s)


# ---------- prop firm ----------
@njit
def challenge(o, h, l, mday, t_k0, t_k1, t_dir, t_entry, t_dist, t_exit, start_day, horizon_day, cost):
    """Two-phase challenge. Trades given in time order (entry M30, exit M30, ...), all with entry day >= start_day.
    Returns (status, end_day, day_of_pass) with status 1 passed, -1 failed, 0 not finished."""
    phase = 1; bal = ACC; daystart = ACC; cur_day = -1; ndays = 0; last_entry_day = -1
    min_phase_day = start_day
    for j in range(len(t_k0)):
        k0 = t_k0[j]; k1 = t_k1[j]
        eday = mday[k0]
        if eday < min_phase_day:
            continue
        if eday > horizon_day:
            return 0, eday, -1
        size = RISK / t_dist[j]; c = size * cost
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
            if eq <= daystart - DAILY or eq <= MAXLOSS:
                return -1, mday[k], -1
        bal += size * (t_exit[j] - t_entry[j]) * t_dir[j] - c
        tgt = TGT1 if phase == 1 else TGT2
        if bal >= ACC + tgt and ndays >= MINDAYS:
            if phase == 1:
                phase = 2; bal = ACC; daystart = ACC; ndays = 0; last_entry_day = -1
                min_phase_day = mday[k1] + 1
            else:
                return 1, mday[k1], mday[k1]
    return 0, -1, -1




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


def streak(r, win):
    s = m = 0
    for x in r:
        hit = x > 0 if win else x <= 0
        s = s + 1 if hit else 0; m = max(m, s)
    return m


def drawdown_pct(r):
    bal = ACC + RISK * np.cumsum(r)
    bal = np.concatenate([[ACC], bal])
    peak = np.maximum.accumulate(bal)
    return 100 * ((peak - bal) / peak).max(), ((peak - bal) / RISK).max()


# ---------- evaluation ----------
def evaluate(d, P, mask_h1, rng, runs=RUNS, label="", verbose=True, seed=SEED, prop=False, period_days=None):
    h1 = P["h1"]
    t, st = rule_trades(d, P, mask_h1)
    out = dict(label=label, n=len(t), **st)
    if len(t) < 2:
        if verbose:
            print(f"\n== {label}: {len(t)} trades")
        return out
    r = t["R_NET"].to_numpy()
    wins = int((r > 0).sum())
    out.update(win=wins / len(t), wil=wilson(wins, len(t)), mean=r.mean(), long_share=float((t["DIR"] == 1).mean()),
               pf=r[r > 0].sum() / -r[r < 0].sum(), cost_means={c: t[f"R_{c:.2f}"].mean() for c in COSTS},
               med_dist=float(t["DIST"].median()), lstreak=streak(r, False), wstreak=streak(r, True),
               open_trades=int((t["FINISHED"] == 0).sum()))
    out["dd_pct"], out["dd_R"] = drawdown_pct(r)
    exitday = P["mdate"][t["EXIT_M30"].to_numpy()]
    daily = pd.Series(r * RISK).groupby(exitday).sum()
    out["worst_day_pct"] = 100 * daily.min() / ACC
    days = h1["DIDX"].to_numpy()[t["SIG_H1"].to_numpy()]
    out["boot"] = day_boot(r, days, rng)
    # controls
    o, hh, ll, cc = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    i0h = h1["i0"].to_numpy(); atr = h1["ATR"].to_numpy()
    atr_prev = np.concatenate([[np.nan], atr[:-1]])
    trend_prev = np.concatenate([[0], P["trend"][:-1]]).astype(np.int8)
    base = mask_h1 & ~np.isnan(atr_prev)
    mults = np.quantile((t["DIST"] / t["ATR"]).to_numpy(), (np.arange(K) + 0.5) / K)
    EX, RN = null_table(o, hh, ll, cc, base, i0h, atr_prev, mults, COST, MIN_STOP)
    out["_mults"] = mults
    m30_h1 = P["m30_h1"]
    entry_h1 = m30_h1[t["ENTRY_M30"].to_numpy()]; exit_h1 = m30_h1[t["EXIT_M30"].to_numpy()]
    start_ptr = int(np.where(mask_h1)[0][0]) - 1; end_h1 = int(np.where(mask_h1)[0][-1])
    prev = np.concatenate([[start_ptr], exit_h1[:-1]])
    waits = (entry_h1 - prev).astype(np.int64)
    eligA = np.where(base & (trend_prev != 0))[0].astype(np.int64)
    eligB = np.where(base)[0].astype(np.int64)
    mA, cA = run_null(EX, RN, m30_h1, eligA, trend_prev, start_ptr, end_h1, waits, True, runs, seed)
    mB, cB = run_null(EX, RN, m30_h1, eligB, trend_prev, start_ptr, end_h1, waits, False, runs, seed + 1)
    out.update(pctA=pct(r.mean(), mA), pctB=pct(r.mean(), mB),
               nullA=np.nanpercentile(mA, [5, 50, 95]), nullB=np.nanpercentile(mB, [5, 50, 95]),
               cntA=float(np.median(cA)), cntB=float(np.median(cB)))
    tt = t.copy()
    tt.insert(0, "ENTRY_TIME", d["TIME"].to_numpy()[t["ENTRY_M30"].to_numpy()])
    tt.insert(1, "EXIT_TIME", d["TIME"].to_numpy()[t["EXIT_M30"].to_numpy()] + np.timedelta64(30, "m"))
    out["trades"] = tt
    if prop:
        prop_sim(d, P, mask_h1, t, out, EX, RN, eligA, trend_prev, start_ptr, end_h1, waits, seed)
    if verbose:
        report(out)
    return out


def prop_sim(d, P, mask_h1, t, out, EX, RN, eligA, trend_prev, start_ptr, end_h1, waits, seed):
    mdate = P["mdate"]
    udays, mday_idx = np.unique(mdate, return_inverse=True)
    mday_idx = mday_idx.astype(np.int64)
    h1 = P["h1"]
    pdays = np.unique(mday_idx[h1["i0"].to_numpy()[mask_h1]])
    last_cal = pd.Timestamp(udays[pdays[-1]])
    ok = np.array([pd.Timestamp(udays[x]) <= last_cal - pd.Timedelta(days=HORIZON) for x in pdays])
    cand = pdays[ok]
    # horizon in day-index units: per start day, the last day index within 365 calendar days
    cal = pd.to_datetime(udays)
    def horizon_idx(sd):
        return int(np.searchsorted(cal, cal[sd] + pd.Timedelta(days=HORIZON), side="right") - 1)
    rng = np.random.default_rng(seed)
    starts = rng.choice(cand, NCHAL, replace=True)
    o, h, l = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW"))
    def run_one(trades_df, sd):
        k0 = trades_df["ENTRY_M30"].to_numpy().astype(np.int64)
        j0 = np.searchsorted(mday_idx[k0], sd)
        tdf = trades_df.iloc[j0:]
        return challenge(o, h, l, mday_idx, tdf["ENTRY_M30"].to_numpy().astype(np.int64),
                         tdf["EXIT_M30"].to_numpy().astype(np.int64), tdf["DIR"].to_numpy().astype(np.int64),
                         tdf["ENTRY"].to_numpy(), tdf["DIST"].to_numpy(), tdf["EXIT"].to_numpy(), sd,
                         horizon_idx(sd), COST)
    res = [run_one(t, sd) for sd in starts]
    stt = np.array([x[0] for x in res])
    dur = np.array([(cal[x[2]] - cal[sd]).days for x, sd in zip(res, starts) if x[0] == 1])
    npass = int((stt == 1).sum())
    out.update(ch_pass=npass / NCHAL, ch_wil=wilson(npass, NCHAL), ch_fail=float((stt == -1).mean()),
               ch_open=float((stt == 0).mean()), ch_med_days=float(np.median(dur)) if len(dur) else np.nan)
    # C5: Null A trades in the same challenge, one random start day per control run
    seed_nb(seed + 7)
    o_, hh, ll, cc = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    i0h = h1["i0"].to_numpy(); atr_prev = np.concatenate([[np.nan], h1["ATR"].to_numpy()[:-1]])
    n = len(P["m30_h1"]); oe = np.empty(n, np.int64); oq = np.empty(n, np.int64); od = np.empty(n, np.int64)
    stn = []
    starts_n = rng.choice(cand, NCHAL_NULL, replace=True)
    for r_ in range(NCHAL_NULL):
        cnt = null_seq(EX, RN, P["m30_h1"], eligA, trend_prev, start_ptr, end_h1, waits, True, seed, oe, oq, od)
        e = oe[:cnt]; q = oq[:cnt]; di = od[:cnt]
        k0 = i0h[e]; dirn = np.where(di == 0, 1, -1)
        entry = o_[k0]
        dist = out["_mults"][q] * atr_prev[e]
        tdf = pd.DataFrame({"ENTRY_M30": k0, "EXIT_M30": EX[di, q, e], "DIR": dirn, "ENTRY": entry, "DIST": dist})
        tdf["EXIT"] = tdf["ENTRY"] + tdf["DIR"] * (RN[di, q, e] * tdf["DIST"] + COST)
        stn.append(run_one(tdf, starts_n[r_])[0])
    stn = np.array(stn)
    out.update(c5_pass=float((stn == 1).mean()), c5_fail=float((stn == -1).mean()), c5_open=float((stn == 0).mean()))


def report(o):
    print(f"\n== {o['label']}")
    print(f"  patterns {o['patterns']}, in trend filter {o['in_filter']}, during open trade {o['busy']}, order not filled {o['unfilled']}, "
          f"stop under 1.00 USD {o['dropped']}")
    print(f"  trades {o['n']}{'  INSUFFICIENT (<100)' if o['n'] < 100 else ''}, long share {100*o['long_share']:.1f}%, still open at end {o['open_trades']}")
    print(f"  win rate (net R > 0) {100*o['win']:.1f}%  (95% {100*o['wil'][0]:.1f} to {100*o['wil'][1]:.1f})")
    print(f"  mean net R {o['mean']:+.3f}  (day bootstrap 95% {o['boot'][0]:+.3f} to {o['boot'][1]:+.3f})   PF {o['pf']:.2f}")
    print("  costs 0 / 0.40 / 0.80 USD: " + " / ".join(f"{v:+.3f}" for v in o["cost_means"].values())
          + f"   median stop {o['med_dist']:.2f} USD")
    print(f"  longest losing run {o['lstreak']}, longest winning run {o['wstreak']}; max drawdown {o['dd_pct']:.1f}% ({o['dd_R']:.1f}R) "
          f"at fixed $1,000 on $100,000; worst day {o['worst_day_pct']:+.2f}%")
    print(f"  Null A 5/50/95 {o['nullA'][0]:+.3f} / {o['nullA'][1]:+.3f} / {o['nullA'][2]:+.3f} -> percentile {o['pctA']:.1f} (null trades median {o['cntA']:.0f})")
    print(f"  Null B 5/50/95 {o['nullB'][0]:+.3f} / {o['nullB'][1]:+.3f} / {o['nullB'][2]:+.3f} -> percentile {o['pctB']:.1f} (null trades median {o['cntB']:.0f})")
    if "ch_pass" in o:
        print(f"  challenge (both phases): passed {100*o['ch_pass']:.1f}% (95% {100*o['ch_wil'][0]:.1f} to {100*o['ch_wil'][1]:.1f}), "
              f"failed {100*o['ch_fail']:.1f}%, not finished {100*o['ch_open']:.1f}%, median days to pass {o['ch_med_days']:.0f}")
        print(f"  C5 Null A in the same challenge: passed {100*o['c5_pass']:.1f}%, failed {100*o['c5_fail']:.1f}%, not finished {100*o['c5_open']:.1f}%")


def make_synth(rng, drift, sub, years=10):
    days = pd.bdate_range("2014-01-01", periods=260 * years)
    times = (days.values[:, None] + (np.arange(48) * np.timedelta64(30, "m"))[None, :]).ravel()
    nb = len(times)
    sig = 0.15 / np.sqrt(260 * 48 * sub); mu = drift / (260 * 48 * sub)
    p = np.empty((nb, sub)); last = 1000.0
    for a in range(0, nb, 20000):
        b = min(nb, a + 20000)
        steps = rng.normal(mu - sig ** 2 / 2, sig, (b - a) * sub)
        blk = last * np.exp(np.cumsum(steps)).reshape(b - a, sub)
        p[a:b] = blk; last = blk[-1, -1]
    op = np.concatenate([[1000.0], p[:-1, -1]])
    return pd.DataFrame({"TIME": pd.to_datetime(times), "OPEN": op, "HIGH": np.maximum(p.max(1), op),
                         "LOW": np.minimum(p.min(1), op), "CLOSE": p[:, -1], "SPREAD": 0})


def synthetic(nsets, seed=7, runs=1000, sub=60):
    rng = np.random.default_rng(seed)
    pcts = []
    for s in range(nsets):
        drift = 0.0 if s % 2 == 0 else 0.08
        d = make_synth(rng, drift, sub)
        P = prepare(d)
        mask = np.zeros(len(P["h1"]), bool); mask[1000:] = True
        o = evaluate(d, P, mask, np.random.default_rng(SEED + s), runs=runs, verbose=False, label=f"set {s}", seed=SEED + s)
        pcts.append(o.get("pctA", np.nan))
        print(f"set {s:2d} drift {drift:.2f}: trades {o['n']:5d} (Null A median {o.get('cntA', 0):.0f})  long {100*o.get('long_share', np.nan):5.1f}%  "
              f"win {100*o.get('win', np.nan):5.1f}%  mean {o.get('mean', np.nan):+.3f}R  pct vs Null A {o.get('pctA', np.nan):5.1f}  vs Null B {o.get('pctB', np.nan):5.1f}", flush=True)
    pcts = np.array(pcts)
    print(f"\nmean percentile vs Null A {np.nanmean(pcts):.1f}; above 95: {int(np.sum(pcts > 95))} of {nsets}; below 5: {int(np.sum(pcts < 5))}")


def selftest():
    rng = np.random.default_rng(1)
    d = make_synth(rng, 0.0, 6, years=2)
    P = prepare(d); h1 = P["h1"]
    o, h, l, c = (h1[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    a, b = pattern(o, h, l, c), pattern_loop(o, h, l, c)
    print(f"pattern: vectorised vs loop equal on {len(a)} bars: {bool((a == b).all())}; morning {int((a == 1).sum())}, evening {int((a == -1).sum())}")
    # SMA check against a plain loop on a few bars
    cs = h1["CLOSE"].to_numpy()
    s = sma(cs, 14); ok = all(abs(s[i] - cs[i - 13:i + 1].mean()) < 1e-9 for i in (13, 500, 2000))
    print(f"SMA14 equals a plain mean: {ok}")
    # walk on a hand-made path
    O = np.array([100, 100, 100.5, 101, 103.0]); H = np.array([101, 101, 102, 104, 103.5]); L = np.array([99.5, 99, 100, 100.8, 102.5]); C = O
    print("walk, long, entry 100.5 stop 99 target 103.5 from bar 0 (stop not hit in bar 0? low 99.5): ",
          walk(O, H, L, C, 0, 100.5, 1, 99.0, 103.5), " expected bar 1 at 99.0 (low 99 touches stop)")
    print("walk, same but stop 98.0: ", walk(O, H, L, C, 0, 100.5, 1, 98.0, 103.5), " expected bar 3 at 103.5 (high 104)")
    print("walk, stop and target in one bar: ", walk(np.array([100, 100.]), np.array([100, 104.]), np.array([100, 97.]),
                                                    np.array([100, 100.]), 0, 100.0, 1, 98.0, 104.0), " expected bar 1 at 98.0")
    print("fill, buy stop 101 opens above at 101.5: ", fill(np.array([101.5]), np.array([102.]), np.array([101.]), 0, 0, 101.0, 1), " expected (0, 101.5)")
    # challenge by hand: 12 winning trades of +2R ($2,000) on 12 different days -> phase 1 after 5 wins ($10,000) and
    # at least 4 days: passes at trade 5; phase 2 from the next day needs $5,000: 3 wins -> pass at trade 8.
    n = 12
    days = np.repeat(np.arange(n), 2)
    Oa = np.full(2 * n, 100.0); Ha = np.full(2 * n, 102.1); La = np.full(2 * n, 99.5)
    k0 = np.arange(0, 2 * n, 2); k1 = k0 + 1
    st = challenge(Oa, Ha, La, days.astype(np.int64), k0, k1, np.ones(n, np.int64), np.full(n, 100.0),
                   np.full(n, 1.0), np.full(n, 102.0), 0, 10 ** 6, 0.0)
    print(f"challenge 12 x +2R: {st}  expected (1, 8, 8): phase 1 at trade 5 (day 4); phase 2 has $6,000 after day 7 but only 3 days, so day 8")
    # daily loss: 6 losses of -1R on one day -> -$6,000 on the day -> fail at the 5th? equity hits -5,000 at 5th loss
    Ld = np.full(12, 98.9); Hd = np.full(12, 100.0); Od = np.full(12, 100.0)
    k0 = np.arange(0, 12, 2); k1 = k0 + 1
    st = challenge(Od, Hd, Ld, np.zeros(12, np.int64), k0, k1, np.ones(6, np.int64), np.full(6, 100.0),
                   np.full(6, 1.0), np.full(6, 99.0), 0, 10 ** 6, 0.0)
    print(f"challenge 6 x -1R same day (low 98.9 = -1.1R floating): {st}  expected (-1, 0, -1): equity -$5,000 reached in trade 5")


if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        selftest(); sys.exit()
    if sys.argv[1] == "--synthetic":
        synthetic(int(sys.argv[2]), sub=int(sys.argv[3]) if len(sys.argv) > 3 else 60)
        sys.exit()
    raise SystemExit("real-data run: see run_real() (added after the noise check)")
