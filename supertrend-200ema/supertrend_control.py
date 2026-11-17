"""
supertrend_control.py . Null test of the "Supertrend + 200 EMA" strategy (test M).

Fixed in advance in hypothese-supertrend-200ema.md, version 1.0 (17 Nov 2026). Nothing in this
script may change after the first run on real data.

Rules (section 3 of the hypothesis):
  bars       signal bars built from MT5 M15 exports (decisive: 30 min), paths walked on M15
  Supertrend factor 3, ATR 10 (Wilder), on hl2, exactly TradingView's pine_supertrend
  EMA        200 on close; everything through the signal bar
  long       direction flips from down to up on bar t, close(t) > EMA200(t)
  short      mirror image
  entry      open of the next signal bar
  stop       Supertrend line on bar t (lower band long, upper band short), fixed
             no trade if entry to stop < 5 pips (or entry already beyond the stop)
  target     1.5R, no break-even, no time limit, open at end of data closed at last close
  one open trade per pair at a time
Costs: 1.2 pip round trip (sensitivity 0, 1.2, 2.0). Stop and target in one M15 bar = stop.
Controls (10,000 runs, seed 19):
  Null A  coin flip: same entries, random direction, same stop distance, same 1.5R   (decisive)
  Null B  random bar, same pair, month and direction, Supertrend in that direction and
          close on that side of EMA200, stop on that bar's Supertrend line          (extra)
Win-rate interval: Wilson 95%.

Usage:
  python supertrend_control.py --dir ./data --pairs EURUSD,EURJPY
  python supertrend_control.py --dir ./synthetic --pairs EURUSD,EURJPY --broker-offset 0
  python supertrend_control.py --selftest
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_R = 1.5
ST_FACTOR = 3.0
ST_ATR = 10
MIN_STOP_PIPS = 5.0
N_RUNS = 10_000
SEED = 19
CLAIM_WR = 0.46


# --- Data (same loader as tests A to D) -------------------------------
def _us_dst_bounds(year: int):
    mar = pd.date_range(f"{year}-03-01", f"{year}-03-31", freq="D")
    nov = pd.date_range(f"{year}-11-01", f"{year}-11-30", freq="D")
    return mar[mar.dayofweek == 6][1], nov[nov.dayofweek == 6][0]


def broker_to_utc(idx: pd.DatetimeIndex, winter_offset: int) -> pd.DatetimeIndex:
    off = np.full(len(idx), float(winter_offset))
    for y in np.unique(idx.year):
        s, e = _us_dst_bounds(int(y))
        off[(idx >= s) & (idx < e)] = winter_offset + 1
    return idx - pd.to_timedelta(off, unit="h")


def load_mt5_csv(path: Path, winter_offset: int) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=None, engine="python")
    raw.columns = [c.strip().strip("<>").upper() for c in raw.columns]
    stamp = raw["DATE"].astype(str)
    if "TIME" in raw.columns:
        stamp = stamp + " " + raw["TIME"].astype(str)
    df = pd.DataFrame(index=pd.to_datetime(stamp, format="mixed"))
    for s, d in [("OPEN", "Open"), ("HIGH", "High"), ("LOW", "Low"), ("CLOSE", "Close")]:
        df[d] = pd.to_numeric(raw[s].values, errors="coerce")
    df = df.dropna().sort_index()
    df = df[~df.index.duplicated(keep="first")]
    if winter_offset:
        df.index = broker_to_utc(df.index, winter_offset)
    return df


def pip_size(symbol: str, df: pd.DataFrame) -> float:
    if "JPY" in symbol:
        return 0.01
    return 0.01 if df["Close"].median() > 20 else 0.0001


def find_file(d: Path, sym: str) -> Path:
    for p in sorted(d.iterdir()):
        m = re.match(r"([A-Za-z]{6,8})", p.stem)
        if m and m.group(1).upper() == sym and p.suffix.lower() in (".csv", ".txt") and "M15" in p.stem.upper():
            return p
    sys.exit(f"no M15 file for {sym} in {d}")


# --- Indicators -------------------------------------------------------
def resample(m15: pd.DataFrame, tf: int) -> pd.DataFrame:
    if tf == 15:
        return m15.copy()
    return m15.resample(f"{tf}min", label="left", closed="left").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()


def rma(x: np.ndarray, n: int) -> np.ndarray:
    """Pine ta.rma: SMA of the first n values as seed, then alpha = 1/n."""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    a = 1.0 / n
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def supertrend(h: np.ndarray, l: np.ndarray, c: np.ndarray, factor=ST_FACTOR, period=ST_ATR):
    """Literal port of pine_supertrend (TradingView Pine reference, checked 17 Nov 2026).
    Returns line, direction (-1 up/green, 1 down/red)."""
    n = len(c)
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.where(np.isnan(pc), h - l, np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc))))
    atr = rma(tr, period)
    src = (h + l) / 2
    ub0, lb0 = src + factor * atr, src - factor * atr
    ub, lb = np.full(n, np.nan), np.full(n, np.nan)
    st, dr = np.full(n, np.nan), np.zeros(n, dtype=int)
    for i in range(n):
        p_lb = lb[i - 1] if i > 0 and not np.isnan(lb[i - 1]) else 0.0   # nz()
        p_ub = ub[i - 1] if i > 0 and not np.isnan(ub[i - 1]) else 0.0
        c1 = c[i - 1] if i > 0 else np.nan
        lb[i] = lb0[i] if (lb0[i] > p_lb or c1 < p_lb) else p_lb
        ub[i] = ub0[i] if (ub0[i] < p_ub or c1 > p_ub) else p_ub
        if i == 0 or np.isnan(atr[i - 1]):
            d = 1
        elif st[i - 1] == p_ub:
            d = -1 if c[i] > ub[i] else 1
        else:
            d = 1 if c[i] < lb[i] else -1
        dr[i] = d
        st[i] = lb[i] if d == -1 else ub[i]
    return st, dr


def add_indicators(bars: pd.DataFrame) -> pd.DataFrame:
    out = bars.copy()
    st, dr = supertrend(bars["High"].to_numpy(), bars["Low"].to_numpy(), bars["Close"].to_numpy())
    out["ST"], out["STDIR"] = st, dr
    out["EMA200"] = bars["Close"].ewm(span=200, adjust=False).mean()
    out["NEXT_OPEN"] = bars["Open"].shift(-1)
    out["NEXT_TIME"] = pd.Series(bars.index, index=bars.index).shift(-1)
    return out.iloc[200:]  # EMA200 warm-up


def raw_signals(ind: pd.DataFrame) -> pd.Series:
    d, c, e = ind["STDIR"], ind["Close"], ind["EMA200"]
    up = (d.shift(1) == 1) & (d == -1) & (c > e)
    dn = (d.shift(1) == -1) & (d == 1) & (c < e)
    s = pd.Series(0, index=ind.index)
    s[up], s[dn] = 1, -1
    return s


# --- Path walk on M15 (same as tests A to D) ---------------------------
def walk(m15_hi, m15_lo, m15_cl, starts, dirs, entries, stops_dist, target_r, max_look=4000):
    n = len(starts)
    res = np.full(n, np.nan)
    end = np.full(n, len(m15_cl) - 1)
    for b0 in range(0, n, 1000):
        sl = slice(b0, min(n, b0 + 1000))
        st, dr, en, sd = starts[sl], dirs[sl], entries[sl], stops_dist[sl]
        pending = np.arange(len(st))
        look = 400
        while len(pending) and look <= max_look * 64:
            idx = st[pending, None] + np.arange(look)[None, :]
            valid = idx < len(m15_cl)
            idx = np.minimum(idx, len(m15_cl) - 1)
            hi, lo = m15_hi[idx], m15_lo[idx]
            d = dr[pending, None]
            stop_lvl = en[pending, None] - d * sd[pending, None]
            tgt_lvl = en[pending, None] + d * target_r * sd[pending, None]
            hit_s = np.where(d > 0, lo <= stop_lvl, hi >= stop_lvl) & valid
            hit_t = np.where(d > 0, hi >= tgt_lvl, lo <= tgt_lvl) & valid
            fs = np.where(hit_s.any(1), hit_s.argmax(1), 10**9)
            ft = np.where(hit_t.any(1), hit_t.argmax(1), 10**9)
            done = (fs < 10**9) | (ft < 10**9)
            gp = pending[done]
            r = np.where(fs[done] <= ft[done], -1.0, target_r)
            res[b0 + gp] = r
            end[b0 + gp] = st[gp] + np.minimum(fs[done], ft[done])
            eod = ~done & ~valid[:, -1]
            ge = pending[eod]
            res[b0 + ge] = (m15_cl[-1] - en[ge]) * dr[ge] / sd[ge]
            end[b0 + ge] = len(m15_cl) - 1
            pending = pending[~done & ~eod]
            look *= 4
    return res, end


# --- Per pair ---------------------------------------------------------
def build_pair(sym, m15, tf):
    pip = pip_size(sym, m15)
    ind = add_indicators(resample(m15, tf))
    s = raw_signals(ind)
    hi, lo, cl = m15["High"].to_numpy(), m15["Low"].to_numpy(), m15["Close"].to_numpy()
    tt = m15.index.to_numpy()
    c = ind[s != 0].copy()
    c["DIR"] = s[s != 0]
    c = c.dropna(subset=["NEXT_OPEN"])
    c["ENTRY"] = c["NEXT_OPEN"]
    c["STOP_D"] = np.where(c["DIR"] > 0, c["ENTRY"] - c["ST"], c["ST"] - c["ENTRY"])
    c = c[c["STOP_D"] >= MIN_STOP_PIPS * pip]
    starts = np.searchsorted(tt, c["NEXT_TIME"].to_numpy(), side="left")
    r, end = walk(hi, lo, cl, starts, c["DIR"].to_numpy(), c["ENTRY"].to_numpy(), c["STOP_D"].to_numpy(), TARGET_R)
    c["R_GROSS"], c["END"], c["START"] = r, end, starts
    keep, busy_until = [], -1
    for i, (st_, en_) in enumerate(zip(c["START"].to_numpy(), c["END"].to_numpy())):
        if st_ > busy_until:
            keep.append(i); busy_until = en_
    t = c.iloc[keep].copy()
    rm, _ = walk(hi, lo, cl, t["START"].to_numpy(), -t["DIR"].to_numpy(), t["ENTRY"].to_numpy(), t["STOP_D"].to_numpy(), TARGET_R)
    t["R_MIRROR"] = rm
    t["PAIR"], t["PIP"] = sym, pip
    t["ENTRY_TIME"] = t["NEXT_TIME"]
    t["EXIT_TIME"] = tt[t["END"].to_numpy()]
    # Null B pool: every bar in a trend state, direction = Supertrend, same side of EMA200
    p = ind.dropna(subset=["NEXT_OPEN"]).copy()
    up = (p["STDIR"] == -1) & (p["Close"] > p["EMA200"])
    dn = (p["STDIR"] == 1) & (p["Close"] < p["EMA200"])
    p = p[up | dn].copy()
    p["DIR"] = np.where(p["STDIR"] == -1, 1, -1)
    p["ENTRY"] = p["NEXT_OPEN"]
    p["STOP_D"] = np.where(p["DIR"] > 0, p["ENTRY"] - p["ST"], p["ST"] - p["ENTRY"])
    p = p[p["STOP_D"] >= MIN_STOP_PIPS * pip]
    ps = np.searchsorted(tt, p["NEXT_TIME"].to_numpy(), side="left")
    pr, _ = walk(hi, lo, cl, ps, p["DIR"].to_numpy(), p["ENTRY"].to_numpy(), p["STOP_D"].to_numpy(), TARGET_R)
    pool = pd.DataFrame({"MONTH": p.index.to_period("M"), "DIR": p["DIR"].to_numpy(), "R_GROSS": pr,
                         "STOP_D": p["STOP_D"].to_numpy()})
    info = dict(pair=sym, pip=pip, m15_bars=len(m15), sig_bars=len(ind), raw_signals=int((s != 0).sum()),
                after_min_stop=len(c), trades=len(t), first=str(m15.index[0].date()), last=str(m15.index[-1].date()))
    return t, pool, info


def net(r_gross, stop_d, pip, cost_pips):
    return r_gross - cost_pips * pip / stop_d


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def day_bootstrap(df, col, n, rng):
    days = df.groupby(df["ENTRY_TIME"].dt.date)[col].apply(np.array).to_list()
    k = len(days)
    out = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, k, k)
        out[i] = np.concatenate([days[j] for j in pick]).mean()
    return out


def streaks(win: np.ndarray):
    bw = bl = cw = cl = 0
    for w in win:
        if w:
            cw += 1; cl = 0
        else:
            cl += 1; cw = 0
        bw, bl = max(bw, cw), max(bl, cl)
    return bw, bl


# --- Self-test: independent second implementation and a hand check ------
def supertrend_reference(h, l, c, factor=ST_FACTOR, period=ST_ATR):
    """Second, independent implementation in plain Python (lists, no numpy), for the self-test."""
    n = len(c)
    tr = []
    for i in range(n):
        if i == 0:
            tr.append(h[i] - l[i])
        else:
            tr.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    atr = [None] * n
    for i in range(period - 1, n):
        atr[i] = sum(tr[:period]) / period if i == period - 1 else (atr[i - 1] * (period - 1) + tr[i]) / period
    lines, dirs = [], []
    plb = pub = 0.0
    prev_st = None
    for i in range(n):
        if atr[i] is None:
            lbi = ubi = None
        else:
            mid = (h[i] + l[i]) / 2
            lbi, ubi = mid - factor * atr[i], mid + factor * atr[i]
        cprev = c[i - 1] if i > 0 else None
        lb_new = lbi if (lbi is not None and lbi > plb) or (cprev is not None and cprev < plb) else plb
        ub_new = ubi if (ubi is not None and ubi < pub) or (cprev is not None and cprev > pub) else pub
        if i == 0 or atr[i - 1] is None:
            d = 1
        elif prev_st == pub:
            d = -1 if c[i] > ub_new else 1
        else:
            d = 1 if c[i] < lb_new else -1
        stv = lb_new if d == -1 else ub_new
        lines.append(stv); dirs.append(d)
        prev_st = stv
        plb = lb_new if lb_new is not None else 0.0
        pub = ub_new if ub_new is not None else 0.0
    return lines, dirs


def selftest():
    rng = np.random.default_rng(7)
    n = 3000
    c = 1.08 * np.exp(np.cumsum(rng.normal(0, 0.0012, n)))
    o = np.concatenate([[1.08], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0006, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0006, n)))
    st, dr = supertrend(h, l, c)
    st2, dr2 = supertrend_reference(list(h), list(l), list(c))
    a = np.array(st2, dtype=float)
    ok_dir = bool((dr[20:] == np.array(dr2)[20:]).all())
    ok_line = bool(np.allclose(st[20:], a[20:], rtol=0, atol=1e-12))
    flips = int((np.diff(dr[20:]) != 0).sum())
    print(f"selftest Supertrend vs independent implementation: direction equal {ok_dir}, line equal {ok_line}, flips {flips}")
    # hand check of one band step (bar 50)
    i = 50
    pc = c[i - 1]
    tr_i = max(h[i] - l[i], abs(h[i] - pc), abs(l[i] - pc))
    print(f"hand check bar {i}: TR {tr_i:.6f}, hl2 {(h[i] + l[i]) / 2:.6f}, line {st[i]:.6f}, direction {dr[i]}")
    # EMA200 against a manual loop
    e = pd.Series(c).ewm(span=200, adjust=False).mean().to_numpy()
    m = c[0]; k = 2 / 201
    for x in c[1:]:
        m = k * x + (1 - k) * m
    print(f"selftest EMA200 last value pandas {e[-1]:.10f} manual {m:.10f} equal {abs(e[-1] - m) < 1e-12}")
    return ok_dir and ok_line and abs(e[-1] - m) < 1e-12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir")
    ap.add_argument("--pairs", default="EURUSD,EURJPY")
    ap.add_argument("--tf", type=int, default=30, choices=[15, 30, 60])
    ap.add_argument("--broker-offset", type=int, default=2)
    ap.add_argument("--out", default="supertrend_trades.csv")
    ap.add_argument("--runs", type=int, default=N_RUNS)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    rng = np.random.default_rng(SEED)
    trades, pools, infos = [], {}, []
    for sym in [s.strip().upper() for s in a.pairs.split(",")]:
        m15 = load_mt5_csv(find_file(Path(a.dir), sym), a.broker_offset)
        t, pool, info = build_pair(sym, m15, a.tf)
        trades.append(t); pools[sym] = pool; infos.append(info)
    T = pd.concat(trades).sort_values("ENTRY_TIME")
    print("\n" + "=" * 78)
    print(f"  Supertrend(10, 3) + 200 EMA · hypothesis v1.0 · {a.tf} min · target 1.5R · stop on the line")
    print("=" * 78)
    for i in infos:
        print(f"  {i['pair']}  {i['first']} to {i['last']}  bars {i['sig_bars']:,}  signals {i['raw_signals']}  "
              f"stop>=5pip {i['after_min_stop']}  trades {i['trades']}{'  (INSUFFICIENT <100)' if i['trades'] < 100 else ''}")
    for cp in (0.0, 1.2, 2.0):
        T[f"NET_{cp}"] = net(T["R_GROSS"], T["STOP_D"], T["PIP"], cp)
    T["NET"] = T["NET_1.2"]
    T["WIN"] = T["R_GROSS"] >= TARGET_R - 1e-9
    n = len(T)
    wins = int(T["WIN"].sum())
    wr = wins / n
    wr_lo, wr_hi = wilson(wins, n)
    boot = day_bootstrap(T, "NET", a.runs, rng)
    b_lo, b_hi = np.percentile(boot, [2.5, 97.5])
    g = T["NET"]
    pf = g[g > 0].sum() / -g[g < 0].sum() if (g < 0).any() else np.inf
    top = g.sort_values(ascending=False)
    top5 = top.iloc[:max(1, int(round(0.05 * n)))].sum()
    bw, bl = streaks(T["WIN"].to_numpy())
    med_stop = np.median(T["STOP_D"] / T["PIP"])
    print("-" * 78)
    print(f"  Trades {n}  over {T['ENTRY_TIME'].dt.date.nunique()} days{'  (INSUFFICIENT <100)' if n < 100 else ''}")
    print(f"  Win rate {wr:.1%}  ({wins}/{n}, Wilson 95% {wr_lo:.1%} to {wr_hi:.1%})   claim 46%")
    for cp in (0.0, 1.2, 2.0):
        print(f"  Mean net R at {cp} pip   {T[f'NET_{cp}'].mean():+.4f}")
    print(f"  95% range (day bootstrap, 1.2 pip)  {b_lo:+.4f} to {b_hi:+.4f}   claim: profitable (> 0)")
    print(f"  Profit factor {pf:.3f}   best 5% of trades {top5:+.1f} R of total {g.sum():+.1f} R")
    print(f"  Median stop {med_stop:.1f} pip vs cost 1.2 pip ({1.2 / med_stop:.3f} R at the median)")
    print(f"  Longest run of wins {bw}, of losses {bl}   (source: 7 and 7)")
    print(f"  Median holding time {((T['EXIT_TIME'] - T['ENTRY_TIME']).dt.total_seconds() / 3600).median():.1f} h")
    for sym, gp in T.groupby("PAIR"):
        k = int(gp["WIN"].sum()); lo_, hi_ = wilson(k, len(gp))
        print(f"  {sym}  n={len(gp)}  win {k / len(gp):.1%} ({lo_:.1%} to {hi_:.1%})  mean net {gp['NET'].mean():+.4f} R"
              f"{'  (INSUFFICIENT <100)' if len(gp) < 100 else ''}")
    cost = 1.2 * T["PIP"].to_numpy() / T["STOP_D"].to_numpy()
    rg, rm = T["R_GROSS"].to_numpy(), T["R_MIRROR"].to_numpy()
    flips = rng.random((a.runs, n)) < 0.5
    nullA = (np.where(flips, rm, rg) - cost).mean(1)
    pA = (nullA < g.mean()).mean() * 100
    samp = []
    for _, r in T.iterrows():
        pool = pools[r["PAIR"]]
        cand = pool[(pool["MONTH"] == r["ENTRY_TIME"].to_period("M")) & (pool["DIR"] == r["DIR"])]
        if len(cand) == 0:
            cand = pool[pool["DIR"] == r["DIR"]]
        samp.append((cand["R_GROSS"] - 1.2 * r["PIP"] / cand["STOP_D"]).to_numpy())
    nullB = np.array([np.mean([s[rng.integers(0, len(s))] for s in samp]) for _ in range(min(a.runs, 2000))])
    pB = (nullB < g.mean()).mean() * 100
    print("-" * 78)
    print("  CONTROLS                         5th to 95th          percentile")
    a5, a95 = np.percentile(nullA, [5, 95]); b5, b95 = np.percentile(nullB, [5, 95])
    print(f"  Null A  coin flip (decisive)     {a5:+.4f} to {a95:+.4f}   percentile {pA:.1f}")
    print(f"  Null B  random bar in trend      {b5:+.4f} to {b95:+.4f}   percentile {pB:.1f}")
    print("-" * 78)
    T["YEAR"] = T["ENTRY_TIME"].dt.year
    for y, gy in T.groupby("YEAR"):
        print(f"  {y}  n={len(gy):4d}  win {gy['WIN'].mean():.1%}  mean net {gy['NET'].mean():+.4f} R")
    print("-" * 78)
    c1 = wr_hi < CLAIM_WR; c2 = b_hi < 0; c3 = pA <= 95
    print(f"  C1 win rate 46%:      {'FALSIFIED' if c1 else 'not falsified'}")
    print(f"  C2 profitable:        {'FALSIFIED' if c2 else 'not falsified'}")
    print(f"  C3 beats coin flip:   {'FALSIFIED (dead)' if c3 else 'not falsified'}")
    print("=" * 78)
    cols = ["PAIR", "ENTRY_TIME", "EXIT_TIME", "DIR", "ENTRY", "STOP_D", "R_GROSS", "R_MIRROR", "NET_0.0", "NET_1.2", "NET_2.0"]
    T[cols].to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
