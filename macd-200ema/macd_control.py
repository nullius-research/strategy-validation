"""
macd_control.py . Null test of a published "MACD + 200 EMA" strategy.

Fixed in advance in hypothese-macd-200ema.md, version 1.0 (1 Nov 2026). Nothing in this
script may change after the first run on real data.

Rules (section 3 of the hypothesis):
  bars       M30 built from MT5 M15 exports, paths walked on M15
  MACD       12, 26, 9 on close; EMA 200 on close; all through the signal bar
  long       MACD crosses above signal, both below zero, close > EMA200
  short      mirror image
  entry      open of the next M30 bar
  stop       lowest low (long) / highest high (short) of the last 10 M30 bars incl. signal bar
             no trade if entry to stop < 5 pips
  target     1.5R, no break-even, no time limit, open at end of data closed at last close
  one open trade per pair at a time
Costs: 1.2 pip round trip (sensitivity 0, 1.2, 2.0). Stop and target in one M15 bar = stop.
Controls (10,000 runs, seed 19):
  Null A  coin flip: same entries, random direction, same stop distance, same 1.5R   (decisive)
  Null B  random bar, same pair and month, same side of EMA200, direction = trend,
          same stop rule                                                              (extra)

Usage:
  python macd_control.py --dir ./data --pairs EURUSD,EURJPY
  python macd_control.py --dir ./synthetic --pairs EURUSD,EURJPY --broker-offset 0
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_R = 1.5
STOP_LOOKBACK = 10
MIN_STOP_PIPS = 5.0
N_RUNS = 10_000
SEED = 19


# --- Data (same loader as bb_reversion_multi.py) ----------------------
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
        if m and m.group(1).upper() == sym and p.suffix.lower() in (".csv", ".txt"):
            return p
    sys.exit(f"no file for {sym} in {d}")


# --- Indicators and signals -------------------------------------------
def to_m30(m15: pd.DataFrame) -> pd.DataFrame:
    m30 = m15.resample("30min", label="left", closed="left").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    return m30


def add_indicators(m30: pd.DataFrame) -> pd.DataFrame:
    c = m30["Close"]
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    sig = macd.ewm(span=9, adjust=False).mean()
    out = m30.copy()
    out["MACD"], out["SIG"] = macd, sig
    out["EMA200"] = c.ewm(span=200, adjust=False).mean()
    out["LL"] = m30["Low"].rolling(STOP_LOOKBACK).min()
    out["HH"] = m30["High"].rolling(STOP_LOOKBACK).max()
    out["NEXT_OPEN"] = m30["Open"].shift(-1)
    out["NEXT_TIME"] = pd.Series(m30.index, index=m30.index).shift(-1)
    out = out.iloc[200:]  # EMA200 warm-up
    return out


def raw_signals(ind: pd.DataFrame) -> pd.DataFrame:
    m, s = ind["MACD"], ind["SIG"]
    up = (m.shift(1) <= s.shift(1)) & (m > s) & (m < 0) & (s < 0) & (ind["Close"] > ind["EMA200"])
    dn = (m.shift(1) >= s.shift(1)) & (m < s) & (m > 0) & (s > 0) & (ind["Close"] < ind["EMA200"])
    d = pd.Series(0, index=ind.index)
    d[up], d[dn] = 1, -1
    return d


# --- Path walk on M15 (vectorised in batches) --------------------------
def walk(m15_hi, m15_lo, m15_cl, m15_t, starts, dirs, entries, stops_dist, target_r, max_look=4000):
    """Returns gross R per trade and the M15 index where it closed. Stop first if both in one bar."""
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
            # trades reaching end of data without a hit: close at last close
            eod = ~done & ~valid[:, -1]
            ge = pending[eod]
            res[b0 + ge] = (m15_cl[-1] - en[ge]) * dr[ge] / sd[ge]
            end[b0 + ge] = len(m15_cl) - 1
            pending = pending[~done & ~eod]
            look *= 4
    return res, end


def m15_start_index(m15_t: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.searchsorted(m15_t, t, side="left")


# --- Per pair ---------------------------------------------------------
def build_pair(sym, m15, winter):
    pip = pip_size(sym, m15)
    ind = add_indicators(to_m30(m15))
    d = raw_signals(ind)
    hi, lo, cl = m15["High"].to_numpy(), m15["Low"].to_numpy(), m15["Close"].to_numpy()
    tt = m15.index.to_numpy()
    # candidate trades from signals
    c = ind[d != 0].copy()
    c["DIR"] = d[d != 0]
    c = c.dropna(subset=["NEXT_OPEN"])
    c["ENTRY"] = c["NEXT_OPEN"]
    c["STOP_D"] = np.where(c["DIR"] > 0, c["ENTRY"] - c["LL"], c["HH"] - c["ENTRY"])
    c = c[c["STOP_D"] >= MIN_STOP_PIPS * pip]
    starts = m15_start_index(tt, c["NEXT_TIME"].to_numpy())
    r, end = walk(hi, lo, cl, tt, starts, c["DIR"].to_numpy(), c["ENTRY"].to_numpy(), c["STOP_D"].to_numpy(), TARGET_R)
    c["R_GROSS"], c["END"], c["START"] = r, end, starts
    # one open trade at a time
    keep, busy_until = [], -1
    for i, (s, e) in enumerate(zip(c["START"].to_numpy(), c["END"].to_numpy())):
        if s > busy_until:
            keep.append(i); busy_until = e
    t = c.iloc[keep].copy()
    # mirror direction for Null A, same entry and stop distance
    rm, _ = walk(hi, lo, cl, tt, t["START"].to_numpy(), -t["DIR"].to_numpy(), t["ENTRY"].to_numpy(), t["STOP_D"].to_numpy(), TARGET_R)
    t["R_MIRROR"] = rm
    t["PAIR"], t["PIP"] = sym, pip
    t["ENTRY_TIME"] = t["NEXT_TIME"]
    # Null B pool: every bar, trend direction, same stop rule
    p = ind.dropna(subset=["NEXT_OPEN"]).copy()
    p["DIR"] = np.where(p["Close"] > p["EMA200"], 1, -1)
    p["ENTRY"] = p["NEXT_OPEN"]
    p["STOP_D"] = np.where(p["DIR"] > 0, p["ENTRY"] - p["LL"], p["HH"] - p["ENTRY"])
    p = p[p["STOP_D"] >= MIN_STOP_PIPS * pip]
    ps = m15_start_index(tt, p["NEXT_TIME"].to_numpy())
    pr, _ = walk(hi, lo, cl, tt, ps, p["DIR"].to_numpy(), p["ENTRY"].to_numpy(), p["STOP_D"].to_numpy(), TARGET_R)
    pool = pd.DataFrame({"MONTH": p.index.to_period("M"), "DIR": p["DIR"].to_numpy(), "R_GROSS": pr,
                         "STOP_D": p["STOP_D"].to_numpy()})
    info = dict(pair=sym, pip=pip, m15_bars=len(m15), m30_bars=len(ind), raw_signals=int((d != 0).sum()),
                after_min_stop=len(c), trades=len(t), first=str(m15.index[0].date()), last=str(m15.index[-1].date()))
    return t, pool, info


def net(r_gross, stop_d, pip, cost_pips):
    return r_gross - cost_pips * pip / stop_d


def day_bootstrap(df, col, n, rng):
    days = df.groupby(df["ENTRY_TIME"].dt.date)[col].apply(np.array).to_list()
    k = len(days)
    out = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, k, k)
        out[i] = np.concatenate([days[j] for j in pick]).mean()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pairs", default="EURUSD,EURJPY")
    ap.add_argument("--broker-offset", type=int, default=2)
    ap.add_argument("--out", default="macd_trades.csv")
    ap.add_argument("--runs", type=int, default=N_RUNS)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    trades, pools, infos = [], {}, []
    for sym in [s.strip().upper() for s in a.pairs.split(",")]:
        m15 = load_mt5_csv(find_file(Path(a.dir), sym), a.broker_offset)
        t, pool, info = build_pair(sym, m15, a.broker_offset)
        trades.append(t); pools[sym] = pool; infos.append(info)
    T = pd.concat(trades)
    print("\n" + "=" * 74)
    print("  MACD + 200 EMA · hypothesis v1.0 · target 1.5R · stop 10-bar extreme")
    print("=" * 74)
    for i in infos:
        print(f"  {i['pair']}  {i['first']} to {i['last']}  M30 {i['m30_bars']:,}  signals {i['raw_signals']}  "
              f"stop>=5pip {i['after_min_stop']}  trades {i['trades']}{'  (INSUFFICIENT <100)' if i['trades'] < 100 else ''}")
    for cp in (0.0, 1.2, 2.0):
        T[f"NET_{cp}"] = net(T["R_GROSS"], T["STOP_D"], T["PIP"], cp)
    T["NET"] = T["NET_1.2"]
    n = len(T)
    wins = (T["R_GROSS"] >= TARGET_R - 1e-9).sum()
    wr = wins / n
    wr_lo, wr_hi = wr - 1.96 * np.sqrt(wr * (1 - wr) / n), wr + 1.96 * np.sqrt(wr * (1 - wr) / n)
    boot = day_bootstrap(T, "NET", a.runs, rng)
    b_lo, b_hi = np.percentile(boot, [2.5, 97.5])
    g = T["NET"]
    pf = g[g > 0].sum() / -g[g < 0].sum() if (g < 0).any() else np.inf
    top = g.sort_values(ascending=False)
    top5 = top.iloc[:max(1, int(round(0.05 * n)))].sum()
    print("-" * 74)
    print(f"  Trades {n}  over {T['ENTRY_TIME'].dt.date.nunique()} days")
    print(f"  Win rate {wr:.1%}  (95% {wr_lo:.1%} to {wr_hi:.1%})   claim 62%")
    for cp in (0.0, 1.2, 2.0):
        print(f"  Mean net R at {cp} pip   {T[f'NET_{cp}'].mean():+.4f}")
    print(f"  95% range (day bootstrap, 1.2 pip)  {b_lo:+.4f} to {b_hi:+.4f}   claim about +0.5R")
    print(f"  Profit factor {pf:.3f}   best 5% of trades {top5:+.1f} R of total {g.sum():+.1f} R")
    print(f"  Median stop {np.median(T['STOP_D'] / T['PIP']):.1f} pip vs cost 1.2 pip")
    # Null A: coin flip, decisive
    cost = 1.2 * T["PIP"].to_numpy() / T["STOP_D"].to_numpy()
    rg, rm = T["R_GROSS"].to_numpy(), T["R_MIRROR"].to_numpy()
    flips = rng.random((a.runs, n)) < 0.5
    nullA = (np.where(flips, rm, rg) - cost).mean(1)
    pA = (nullA < g.mean()).mean() * 100
    # Null B: random bar, same pair and month, trend direction
    samp = []
    for _, r in T.iterrows():
        pool = pools[r["PAIR"]]
        cand = pool[pool["MONTH"] == r["ENTRY_TIME"].to_period("M")]
        if len(cand) == 0:
            cand = pool
        net_b = (cand["R_GROSS"] - 1.2 * r["PIP"] / cand["STOP_D"]).to_numpy()
        samp.append(net_b)
    nullB = np.array([np.mean([s[rng.integers(0, len(s))] for s in samp]) for _ in range(min(a.runs, 2000))])
    pB = (nullB < g.mean()).mean() * 100
    print("-" * 74)
    print("  CONTROLS                         5th to 95th          percentile")
    a5, a95 = np.percentile(nullA, [5, 95]); b5, b95 = np.percentile(nullB, [5, 95])
    print(f"  Null A  coin flip (decisive)     {a5:+.4f} to {a95:+.4f}   {pA:.1f}")
    print(f"  Null B  random bar in trend      {b5:+.4f} to {b95:+.4f}   {pB:.1f}")
    print("-" * 74)
    T["YEAR"] = T["ENTRY_TIME"].dt.year
    for y, gy in T.groupby("YEAR"):
        print(f"  {y}  n={len(gy):4d}  win {(gy['R_GROSS'] >= TARGET_R - 1e-9).mean():.1%}  mean net {gy['NET'].mean():+.4f} R")
    print("-" * 74)
    c1 = wr_hi < 0.62; c2 = b_hi < 0.5; c3 = pA <= 95
    print(f"  C1 win rate 62%:      {'FALSIFIED' if c1 else 'not falsified'}")
    print(f"  C2 about +0.5R:       {'FALSIFIED' if c2 else 'not falsified'}")
    print(f"  C3 beats coin flip:   {'FALSIFIED (dead)' if c3 else 'not falsified'}")
    print("=" * 74)
    cols = ["PAIR", "ENTRY_TIME", "DIR", "ENTRY", "STOP_D", "R_GROSS", "R_MIRROR", "NET_0.0", "NET_1.2", "NET_2.0"]
    T[cols].to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
