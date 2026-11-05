"""
srm_control.py . Null test of the "Stochastic + RSI + MACD" strategy.

Fixed in advance in hypothese-stoch-rsi-macd.md, version 1.0 (approved 5 Nov 2026,
SHA-256 18a7d430...). Nothing in this script may change after the first run on real data.

Rules (section 3 of the hypothesis):
  bars       M30 built from MT5 M15 exports, paths walked on M15
  stochastic %K 14, smoothing 1, %D 3. Oversold: K<20 and D<20 on one bar. Overbought: K>80 and D>80
  RSI        14 (Wilder), level 50.   MACD 12, 26, 9.   All on close, through the signal bar
  setup      long armed on an oversold bar s, re-armed by each new oversold bar, cancelled by an
             overbought bar (which arms the short), expires after 48 M30 bars (t <= s+47),
             consumed by its first trigger even if a position is open
  trigger    long: MACD crosses above signal on bar t, RSI(t) > 50. Short: mirror image
  entry      open of the next M30 bar
  stop       most recent 5-bar fractal swing low below entry, confirmed (j+2 <= t), j >= t-49.
             Short: swing high above entry. No swing or stop < 5 pips: no trade
  target     1.5R, no break-even, no time limit, open at end of data closed at last close
  one open trade per pair at a time
  variant    stop capped at 0.15% of entry, target 1.5x that (reported, not decisive)
Costs: 1.2 pip round trip (sensitivity 0, 1.2, 2.0). Stop and target in one M15 bar = stop.
Controls (10,000 runs, seed 19), decisive pair EURUSD:
  Null A  coin flip: same entries, random direction, same stop distance, same 1.5R   (decisive)
  Null B  random bar, same pair and month, direction = side of RSI 50, same stop rule  (extra)

Usage:
  python srm_control.py --dir ./data --pairs EURUSD,EURJPY,...
  python srm_control.py --dir ./synthetic --pairs EURUSD --broker-offset 0
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_R = 1.5
MIN_STOP_PIPS = 5.0
SETUP_BARS = 48
SWING_LOOKBACK = 50
STOP_CAP = 0.0015
N_RUNS = 10_000
SEED = 19
DECISIVE = "EURUSD"


# --- Data (same loader as macd_control.py) ----------------------------
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


# --- Indicators --------------------------------------------------------
def to_m30(m15: pd.DataFrame) -> pd.DataFrame:
    return m15.resample("30min", label="left", closed="left").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()


def add_indicators(m30: pd.DataFrame) -> pd.DataFrame:
    c, h, l = m30["Close"], m30["High"], m30["Low"]
    out = m30.copy()
    ll, hh = l.rolling(14).min(), h.rolling(14).max()
    k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)          # %K 14, smoothing 1
    out["K"], out["D"] = k, k.rolling(3).mean()                  # %D 3
    diff = c.diff()
    up = diff.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    dn = (-diff.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    out["RSI"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    out["MACD"], out["SIG"] = macd, macd.ewm(span=9, adjust=False).mean()
    out["NEXT_OPEN"] = m30["Open"].shift(-1)
    out["NEXT_TIME"] = pd.Series(m30.index, index=m30.index).shift(-1)
    return out.iloc[100:]  # warm-up for MACD and RSI


# --- Setup state machine and triggers ---------------------------------
def triggers(ind: pd.DataFrame) -> np.ndarray:
    """Direction per bar (+1, -1, 0) of a valid trigger per section 3.3 to 3.5."""
    K, D, R = ind["K"].to_numpy(), ind["D"].to_numpy(), ind["RSI"].to_numpy()
    M, S = ind["MACD"].to_numpy(), ind["SIG"].to_numpy()
    n = len(ind)
    out = np.zeros(n, dtype=int)
    side, start = 0, -10**9
    for t in range(1, n):
        os_ = K[t] < 20 and D[t] < 20
        ob_ = K[t] > 80 and D[t] > 80
        if os_:
            side, start = 1, t
        elif ob_:
            side, start = -1, t
        if side != 0 and t > start + SETUP_BARS - 1:
            side = 0
        if side == 1 and M[t - 1] <= S[t - 1] and M[t] > S[t] and R[t] > 50:
            out[t] = 1; side = 0
        elif side == -1 and M[t - 1] >= S[t - 1] and M[t] < S[t] and R[t] < 50:
            out[t] = -1; side = 0
    return out


def swing_stops(ind: pd.DataFrame, bars: np.ndarray, dirs: np.ndarray, entries: np.ndarray) -> np.ndarray:
    """Stop price per section 3.7, NaN if no swing in range."""
    lo, hi = ind["Low"].to_numpy(), ind["High"].to_numpy()
    n = len(lo)
    sl = np.zeros(n, bool); sh = np.zeros(n, bool)
    sl[2:n - 2] = ((lo[2:n-2] < lo[1:n-3]) & (lo[2:n-2] < lo[:n-4]) & (lo[2:n-2] < lo[3:n-1]) & (lo[2:n-2] < lo[4:]))
    sh[2:n - 2] = ((hi[2:n-2] > hi[1:n-3]) & (hi[2:n-2] > hi[:n-4]) & (hi[2:n-2] > hi[3:n-1]) & (hi[2:n-2] > hi[4:]))
    idx_l, idx_h = np.flatnonzero(sl), np.flatnonzero(sh)
    res = np.full(len(bars), np.nan)
    for i, (t, d, e) in enumerate(zip(bars, dirs, entries)):
        arr, price = (idx_l, lo) if d > 0 else (idx_h, hi)
        p = np.searchsorted(arr, t - 2, side="right") - 1
        while p >= 0 and arr[p] >= t - SWING_LOOKBACK + 1:
            v = price[arr[p]]
            if (d > 0 and v < e) or (d < 0 and v > e):
                res[i] = v; break
            p -= 1
    return res


# --- Path walk on M15 (same as macd_control.py) -----------------------
def walk(m15_hi, m15_lo, m15_cl, starts, dirs, entries, stops_dist, target_r):
    n = len(starts)
    res = np.full(n, np.nan)
    end = np.full(n, len(m15_cl) - 1)
    for b0 in range(0, n, 1000):
        sl = slice(b0, min(n, b0 + 1000))
        st, dr, en, sd = starts[sl], dirs[sl], entries[sl], stops_dist[sl]
        pending = np.arange(len(st))
        look = 400
        while len(pending):
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
            res[b0 + gp] = np.where(fs[done] <= ft[done], -1.0, target_r)
            end[b0 + gp] = st[gp] + np.minimum(fs[done], ft[done])
            eod = ~done & ~valid[:, -1]
            ge = pending[eod]
            res[b0 + ge] = (m15_cl[-1] - en[ge]) * dr[ge] / sd[ge]
            end[b0 + ge] = len(m15_cl) - 1
            pending = pending[~done & ~eod]
            look *= 4
    return res, end


def candidates(ind, bars, dirs, pip, tt):
    entries = ind["NEXT_OPEN"].to_numpy()[bars]
    stop = swing_stops(ind, bars, dirs, entries)
    sd = np.where(dirs > 0, entries - stop, stop - entries)
    ok = np.isfinite(sd) & (sd >= MIN_STOP_PIPS * pip) & np.isfinite(entries)
    starts = np.searchsorted(tt, ind["NEXT_TIME"].to_numpy()[bars], side="left")
    return entries, sd, ok, starts


# --- Per pair ----------------------------------------------------------
def build_pair(sym, m15):
    pip = pip_size(sym, m15)
    ind = add_indicators(to_m30(m15))
    hi, lo, cl = m15["High"].to_numpy(), m15["Low"].to_numpy(), m15["Close"].to_numpy()
    tt = m15.index.to_numpy()
    trig = triggers(ind)
    bars = np.flatnonzero(trig != 0)
    bars = bars[bars < len(ind) - 1]
    dirs = trig[bars]
    entries, sd, ok, starts = candidates(ind, bars, dirs, pip, tt)
    n_trig, n_noswing = len(bars), int((~np.isfinite(sd)).sum())
    n_small = int((np.isfinite(sd) & (sd < MIN_STOP_PIPS * pip)).sum())
    bars, dirs, entries, sd, starts = bars[ok], dirs[ok], entries[ok], sd[ok], starts[ok]
    r, end = walk(hi, lo, cl, starts, dirs, entries, sd, TARGET_R)
    keep, busy = [], -1
    for i, (s, e) in enumerate(zip(starts, end)):
        if s > busy:
            keep.append(i); busy = e
    keep = np.array(keep, dtype=int)
    t = pd.DataFrame({"PAIR": sym, "ENTRY_TIME": ind["NEXT_TIME"].to_numpy()[bars[keep]], "DIR": dirs[keep],
                      "ENTRY": entries[keep], "STOP_D": sd[keep], "R_GROSS": r[keep], "PIP": pip})
    st = starts[keep]
    t["R_MIRROR"], _ = walk(hi, lo, cl, st, -t["DIR"].to_numpy(), t["ENTRY"].to_numpy(), t["STOP_D"].to_numpy(), TARGET_R)
    # variant: stop capped at 0.15% of entry, same moments and direction (own one-position filter)
    sdc = np.minimum(sd, STOP_CAP * entries)
    okc = sdc >= MIN_STOP_PIPS * pip
    rc, endc = walk(hi, lo, cl, starts[okc], dirs[okc], entries[okc], sdc[okc], TARGET_R)
    kc, busy = [], -1
    for i, (s, e) in enumerate(zip(starts[okc], endc)):
        if s > busy:
            kc.append(i); busy = e
    var = pd.DataFrame({"R_GROSS": rc[kc], "STOP_D": sdc[okc][kc], "PIP": pip})
    # Null B pool: every bar, direction = side of RSI 50, same stop rule
    rsi = ind["RSI"].to_numpy()
    pb = np.flatnonzero((rsi != 50) & np.isfinite(rsi))
    pb = pb[pb < len(ind) - 1]
    pdir = np.where(rsi[pb] > 50, 1, -1)
    pe, psd, pok, pst = candidates(ind, pb, pdir, pip, tt)
    pr, _ = walk(hi, lo, cl, pst[pok], pdir[pok], pe[pok], psd[pok], TARGET_R)
    pool = pd.DataFrame({"MONTH": pd.DatetimeIndex(ind.index[pb[pok]]).to_period("M"), "R_GROSS": pr, "STOP_D": psd[pok]})
    months = max(1, pd.DatetimeIndex(t["ENTRY_TIME"]).to_period("M").nunique()) if len(t) else 1
    info = dict(pair=sym, first=str(m15.index[0].date()), last=str(m15.index[-1].date()), m30=len(ind),
                triggers=n_trig, no_swing=n_noswing, small_stop=n_small, trades=len(t), per_month=len(t) / months)
    return t, pool, var, info


def net(r, sd, pip, cost):
    return r - cost * pip / sd


def day_bootstrap(df, col, n, rng):
    days = df.groupby(df["ENTRY_TIME"].dt.date)[col].apply(np.array).to_list()
    k = len(days)
    return np.array([np.concatenate([days[j] for j in rng.integers(0, k, k)]).mean() for _ in range(n)])


def report(T, pools, runs, rng, label, decisive):
    n = len(T)
    wins = (T["R_GROSS"] >= TARGET_R - 1e-9).sum()
    wr = wins / n
    se = np.sqrt(wr * (1 - wr) / n)
    for cp in (0.0, 1.2, 2.0):
        T[f"NET_{cp}"] = net(T["R_GROSS"], T["STOP_D"], T["PIP"], cp)
    g = T["NET_1.2"]
    boot = day_bootstrap(T.assign(NET=g), "NET", runs, rng)
    b_lo, b_hi = np.percentile(boot, [2.5, 97.5])
    pf = g[g > 0].sum() / -g[g < 0].sum() if (g < 0).any() else np.inf
    top5 = g.sort_values(ascending=False).iloc[:max(1, int(round(0.05 * n)))].sum()
    cost = 1.2 * T["PIP"].to_numpy() / T["STOP_D"].to_numpy()
    flips = rng.random((runs, n)) < 0.5
    nullA = (np.where(flips, T["R_MIRROR"].to_numpy(), T["R_GROSS"].to_numpy()) - cost).mean(1)
    pA = (nullA < g.mean()).mean() * 100
    samp = []
    for pair, et, pip in zip(T["PAIR"], T["ENTRY_TIME"], T["PIP"]):
        pool = pools[pair]
        cand = pool[pool["MONTH"] == et.to_period("M")]
        if len(cand) == 0:
            cand = pool
        samp.append((cand["R_GROSS"] - 1.2 * pip / cand["STOP_D"]).to_numpy())
    nullB = np.array([np.mean([s[rng.integers(0, len(s))] for s in samp]) for _ in range(min(runs, 2000))])
    pB = (nullB < g.mean()).mean() * 100
    print("-" * 78)
    print(f"  {label}{'  (INSUFFICIENT <100)' if n < 100 else ''}")
    print(f"  Trades {n}   win rate {wr:.1%} (95% {wr - 1.96*se:.1%} to {wr + 1.96*se:.1%})   claim 56%")
    print("  Mean net R   " + "   ".join(f"{cp} pip {T[f'NET_{cp}'].mean():+.4f}" for cp in (0.0, 1.2, 2.0)))
    print(f"  95% range (day bootstrap, 1.2 pip) {b_lo:+.4f} to {b_hi:+.4f}   claim about +0.14R")
    print(f"  Profit factor {pf:.3f}   best 5% {top5:+.1f} R of total {g.sum():+.1f} R   median stop {np.median(T['STOP_D']/T['PIP']):.1f} pip")
    a5, a95 = np.percentile(nullA, [5, 95]); b5, b95 = np.percentile(nullB, [5, 95])
    print(f"  Null A coin flip{' (decisive)' if decisive else ''}  {a5:+.4f} to {a95:+.4f}   percentile {pA:.1f}")
    print(f"  Null B RSI side                {b5:+.4f} to {b95:+.4f}   percentile {pB:.1f}")
    return dict(n=n, wr_hi=wr + 1.96 * se, b_hi=b_hi, pA=pA, pB=pB, mean=g.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pairs", default="EURUSD")
    ap.add_argument("--broker-offset", type=int, default=2)
    ap.add_argument("--out", default="srm_trades.csv")
    ap.add_argument("--runs", type=int, default=N_RUNS)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    trades, pools, vars_, infos = {}, {}, {}, []
    for sym in [s.strip().upper() for s in a.pairs.split(",")]:
        m15 = load_mt5_csv(find_file(Path(a.dir), sym), a.broker_offset)
        t, pool, var, info = build_pair(sym, m15)
        trades[sym], pools[sym], vars_[sym] = t, pool, var
        infos.append(info)
    print("\n" + "=" * 78)
    print("  Stochastic + RSI + MACD · hypothesis v1.0 · target 1.5R · stop at swing")
    print("=" * 78)
    for i in infos:
        print(f"  {i['pair']} {i['first']} to {i['last']}  M30 {i['m30']:,}  triggers {i['triggers']}  "
              f"no swing {i['no_swing']}  stop<5pip {i['small_stop']}  trades {i['trades']}  ({i['per_month']:.1f}/month)")
    res = {}
    if DECISIVE in trades and len(trades[DECISIVE]):
        T = trades[DECISIVE]
        res = report(T, pools, a.runs, rng, f"{DECISIVE} (decisive)", True)
        T["YEAR"] = T["ENTRY_TIME"].dt.year
        for y, gy in T.groupby("YEAR"):
            print(f"    {y}  n={len(gy):4d}  win {(gy['R_GROSS'] >= TARGET_R - 1e-9).mean():.1%}  mean net {gy['NET_1.2'].mean():+.4f} R")
        v = vars_[DECISIVE]
        vn = net(v["R_GROSS"], v["STOP_D"], v["PIP"], 1.2)
        print(f"  Variant stop cap 0.15%: trades {len(v)}  win {(v['R_GROSS'] >= TARGET_R - 1e-9).mean():.1%}  mean net {vn.mean():+.4f} R  (not decisive)")
    for sym, t in trades.items():
        if sym != DECISIVE and len(t):
            report(t, pools, a.runs, rng, f"{sym} (extra, not decisive)", False)
    others = [t for s, t in trades.items() if s != DECISIVE and len(t)]
    if others:
        report(pd.concat(others, ignore_index=True), pools, a.runs, rng, "Other pairs together (extra)", False)
    print("-" * 78)
    if res:
        if res["n"] < 100:
            print("  EURUSD under 100 trades: INSUFFICIENT, no verdict")
        else:
            print(f"  C1 win rate 56%:     {'FALSIFIED' if res['wr_hi'] < 0.56 else 'not falsified'}")
            print(f"  C2 about +0.14R:     {'FALSIFIED' if res['b_hi'] < 0.14 else 'not falsified'}")
            print(f"  C3 beats coin flip:  {'FALSIFIED (dead)' if res['pA'] <= 95 else 'not falsified'}")
    print("=" * 78)
    pd.concat(trades.values(), ignore_index=True).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
