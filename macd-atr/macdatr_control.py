"""
macdatr_control.py . Null test of MACD signals with an ATR stop (1.5 ATR) and an ATR target (1 ATR).

Fixed in advance in hypothese-macd-atr.md (version recorded in the meetlog). Nothing in this
script may change after the first run on real data.

Rules (section 3 of the hypothesis):
  bars       D1 signals, path walked on H1 of the same broker
  MACD       12, 26, 9, EMA on close.  ATR 14, Wilder (RMA of true range), as Pine atr()
  signals    MACD Line ZC: MACD crosses 0. Signal Line ZC: signal line crosses 0.
             Continuation, Reversal, Histogram as in the source code (extra, not decisive)
             crossover(a,b): a(t) > b(t) and a(t-1) <= b(t-1)
  entry      open of the next D1 bar
  stop       1.5 x ATR(signal bar), target 1 x ATR(signal bar), fixed for the trade
  exit       stop, target, or an opposite signal (exit and reverse at the next D1 open)
             a signal in the direction of an open trade does nothing; one position per pair
  win        net R > 0, R = stop distance (1.5 ATR)
Costs: 1.2 pip round trip (sensitivity 0, 1.2, 3.0). Stop and target in one H1 bar = stop.
Control (10,000 runs, seed 23): Null A coin flip. Same entries and horizon, random direction.

Usage:
  python macdatr_control.py --dir ./data --out run01.txt --trades trades.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SL_ATR = 1.5
TP_ATR = 1.0
COSTS = (0.0, 1.2, 3.0)
COST_MAIN = 1.2
N_RUNS = 10_000
SEED = 23
SIGNALS = ["Continuation", "Reversal", "Histogram", "MACD Line ZC", "Signal Line ZC"]
DECISIVE = ["MACD Line ZC", "Signal Line ZC"]
PERIOD_R = ("2018-01-01", "2020-08-14")
PERIOD_T = ("2020-08-15", "2100-01-01")


# ---------------------------------------------------------------- data
def load(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, sep="\t")
    d.columns = [c.strip("<>").upper() for c in d.columns]
    idx = pd.to_datetime(d["DATE"] + " " + d["TIME"], format="%Y.%m.%d %H:%M:%S")
    out = pd.DataFrame({"o": d["OPEN"].values, "h": d["HIGH"].values,
                        "l": d["LOW"].values, "c": d["CLOSE"].values}, index=idx)
    out = out[~out.index.duplicated(keep="first")].sort_index()
    return out


def pip_size(pair: str) -> float:
    return 0.01 if pair.endswith("JPY") else 0.0001


# ---------------------------------------------------------------- indicators
def ema(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(span=n, adjust=False).mean()


def rma(x: pd.Series, n: int) -> pd.Series:
    # Pine rma: first value is the SMA of the first n values, then alpha = 1/n
    v = x.values.astype(float)
    out = np.full(len(v), np.nan)
    if len(v) < n:
        return pd.Series(out, index=x.index)
    out[n - 1] = np.nanmean(v[:n])
    a = 1.0 / n
    for i in range(n, len(v)):
        out[i] = a * v[i] + (1 - a) * out[i - 1]
    return pd.Series(out, index=x.index)


def indicators(d1: pd.DataFrame) -> pd.DataFrame:
    c = d1["c"]
    macd = ema(c, 12) - ema(c, 26)
    sig = ema(macd, 9)
    hist = macd - sig
    pc = c.shift(1)
    tr = pd.concat([d1["h"] - d1["l"], (d1["h"] - pc).abs(), (d1["l"] - pc).abs()], axis=1).max(axis=1)
    tr.iloc[0] = d1["h"].iloc[0] - d1["l"].iloc[0]
    atr = rma(tr, 14)
    return pd.DataFrame({"macd": macd, "sig": sig, "hist": hist, "atr": atr})


def cross_over(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


def signals(ind: pd.DataFrame, kind: str) -> np.ndarray:
    m, s, h = ind["macd"], ind["sig"], ind["hist"]
    z = pd.Series(0.0, index=ind.index)
    if kind == "Continuation":
        lo = cross_over(m, s) & (m > 0)
        sh = cross_over(s, m) & (m < 0)
    elif kind == "Reversal":
        lo = cross_over(m, s) & (m < 0)
        sh = cross_over(s, m) & (m > 0)
    elif kind == "Histogram":
        lo, sh = cross_over(h, z), cross_over(z, h)
    elif kind == "MACD Line ZC":
        lo, sh = cross_over(m, z), cross_over(z, m)
    elif kind == "Signal Line ZC":
        lo, sh = cross_over(s, z), cross_over(z, s)
    else:
        raise ValueError(kind)
    out = np.zeros(len(ind), dtype=int)
    out[lo.fillna(False).values] = 1
    out[sh.fillna(False).values] = -1
    return out


# ---------------------------------------------------------------- path
def h1_day_slices(d1: pd.DataFrame, h1: pd.DataFrame):
    """For each D1 bar, the [start, end) row range of H1 bars on that calendar date."""
    hd = h1.index.normalize().values
    dd = d1.index.normalize().values
    start = np.searchsorted(hd, dd, side="left")
    end = np.searchsorted(hd, dd, side="right")
    return start, end


def walk(direction: int, entry: float, stop_d: float, tgt_d: float, hh, ll, cost: float,
         exit_px: float):
    """Walk H1 highs/lows in order. Return (R, kind, bar offset). Stop first if both in one bar."""
    if direction == 1:
        sl, tp = entry - stop_d, entry + tgt_d
        hit_sl = ll <= sl
        hit_tp = hh >= tp
    else:
        sl, tp = entry + stop_d, entry - tgt_d
        hit_sl = hh >= sl
        hit_tp = ll <= tp
    any_hit = hit_sl | hit_tp
    if any_hit.any():
        k = int(np.argmax(any_hit))
        if hit_sl[k]:
            return (-stop_d - cost) / stop_d, "stop", k
        return (tgt_d - cost) / stop_d, "target", k
    return (direction * (exit_px - entry) - cost) / stop_d, "signal_or_end", -1


def run_pair(pair: str, d1: pd.DataFrame, h1: pd.DataFrame, kind: str, period, cost_pips: float):
    ind = indicators(d1)
    sig = signals(ind, kind)
    hs, he = h1_day_slices(d1, h1)
    H, L = h1["h"].values, h1["l"].values
    O, C = d1["o"].values, d1["c"].values
    atr = ind["atr"].values
    dates = d1.index
    n = len(d1)
    cost = cost_pips * pip_size(pair)
    p0, p1 = pd.Timestamp(period[0]), pd.Timestamp(period[1])
    in_period = (dates >= p0) & (dates <= p1)
    trades = []
    t = 0
    pending = None  # (signal day, direction) waiting to enter at next open
    while t < n - 1:
        if pending is None:
            if sig[t] != 0 and in_period[t] and not np.isnan(atr[t]):
                pending = (t, sig[t])
            t += 1
            continue
        s_day, dirn = pending
        pending = None
        e = s_day + 1                       # entry day
        entry = O[e]
        stop_d, tgt_d = SL_ATR * atr[s_day], TP_ATR * atr[s_day]
        # next opposite signal at or after the entry day
        f = None
        for j in range(e, n):
            if sig[j] == -dirn:
                f = j
                break
        last_day = f if f is not None else n - 1
        a, b = hs[e], he[last_day]
        hh, ll = H[a:b], L[a:b]
        if f is not None and f + 1 < n:
            exit_px = O[f + 1]
        else:
            exit_px = C[n - 1]
        # outcome for both directions on the same horizon (for Null A)
        res = {}
        for dd_ in (1, -1):
            res[dd_] = walk(dd_, entry, stop_d, tgt_d, hh, ll, cost, exit_px)
        r, how, k = res[dirn]
        no_path = (b - a) == 0
        if how == "signal_or_end":
            exit_day = f + 1 if (f is not None and f + 1 < n) else n - 1
            how = "signal" if f is not None and f + 1 < n else "end"
        else:
            hit_time = h1.index[a + k]
            exit_day = int(np.searchsorted(dates.normalize().values, hit_time.normalize().to_datetime64(), side="left"))
        trades.append(dict(pair=pair, signal=kind, signal_date=dates[s_day].date(), entry_date=dates[e].date(),
                           dir=dirn, entry=entry, atr=atr[s_day], exit_how=how, R=r,
                           R_long=res[1][0], R_short=res[-1][0], no_h1=no_path))
        if how == "signal":
            # reversal: the opposite signal on day f opens the next trade at open f+1
            if in_period[f]:
                pending = (f, -dirn)
                t = f + 1
            else:
                t = f + 1
        else:
            # free from the exit day on; a signal at the close of that day may open a trade
            t = max(exit_day, e)
    return trades


# ---------------------------------------------------------------- stats
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - hw, c + hw


def day_boot(df: pd.DataFrame, rng, n=10_000):
    g = df.groupby("entry_date")["R"].agg(["sum", "count"])
    s, c = g["sum"].values, g["count"].values
    idx = rng.integers(0, len(g), size=(n, len(g)))
    means = s[idx].sum(axis=1) / c[idx].sum(axis=1)
    return np.percentile(means, [2.5, 97.5])


def null_a(df: pd.DataFrame, rng, n=N_RUNS):
    rl, rs = df["R_long"].values, df["R_short"].values
    coin = rng.integers(0, 2, size=(n, len(df))).astype(bool)
    means = np.where(coin, rl, rs).mean(axis=1)
    return means


def summary(df: pd.DataFrame, rng) -> dict:
    n = len(df)
    if n == 0:
        return dict(n=0)
    wins = int((df["R"] > 0).sum())
    lo, hi = wilson(wins, n)
    gp = df.loc[df["R"] > 0, "R"].sum()
    gl = -df.loc[df["R"] < 0, "R"].sum()
    ci = day_boot(df, rng)
    nm = null_a(df, rng)
    pct = float((nm < df["R"].mean()).mean() * 100)
    return dict(n=n, wins=wins, winrate=wins / n * 100, wr_lo=lo * 100, wr_hi=hi * 100,
                meanR=df["R"].mean(), ci_lo=ci[0], ci_hi=ci[1], pf=gp / gl if gl > 0 else np.inf,
                null_med=float(np.median(nm)), null_p95=float(np.percentile(nm, 95)), pct=pct,
                no_h1=int(df["no_h1"].sum()))


def fmt(s: dict) -> str:
    if s.get("n", 0) == 0:
        return "n=0"
    return (f"n={s['n']:5d}  winrate {s['winrate']:5.1f}% [{s['wr_lo']:5.1f}-{s['wr_hi']:5.1f}]  "
            f"meanR {s['meanR']:+.4f} [{s['ci_lo']:+.4f} {s['ci_hi']:+.4f}]  PF {s['pf']:.2f}  "
            f"NullA med {s['null_med']:+.4f} p95 {s['null_p95']:+.4f}  pct {s['pct']:5.1f}  noH1 {s['no_h1']}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pairs", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--trades", default="")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    root = Path(a.dir)
    pairs = [p for p in a.pairs.split(",") if p] or sorted({f.stem.split("_")[0] for f in root.glob("*_D1.csv")})
    rng = np.random.default_rng(SEED)
    lines = [f"macdatr_control.py  dir={root}  pairs={len(pairs)}  seed={SEED}  runs={N_RUNS}"]
    data = {}
    for p in pairs:
        data[p] = (load(root / f"{p}_D1.csv"), load(root / f"{p}_H1.csv"))
    all_tr = []
    for cost in COSTS:
        for per_name, per in (("R", PERIOD_R), ("T", PERIOD_T)):
            for kind in SIGNALS:
                tr = []
                for p in pairs:
                    tr += run_pair(p, data[p][0], data[p][1], kind, per, cost)
                df = pd.DataFrame(tr)
                if cost == COST_MAIN:
                    df["period"] = per_name
                    all_tr.append(df)
                if cost != COST_MAIN and kind not in DECISIVE:
                    continue
                s = summary(df, rng)
                tag = "DECISIVE" if (per_name == "T" and kind in DECISIVE and cost == COST_MAIN) else ""
                lines.append(f"cost {cost:.1f}  period {per_name}  {kind:15s} {fmt(s)} {tag}")
    trades = pd.concat(all_tr, ignore_index=True)
    # per pair x signal cells, period R, main cost
    lines.append("")
    lines.append("cells period R (winrate %, n), main cost")
    cells = trades[trades.period == "R"].groupby(["pair", "signal"])["R"].agg(
        n="count", wr=lambda x: (x > 0).mean() * 100)
    for (p, k), row in cells.iterrows():
        lines.append(f"  {p} {k:15s} {row['wr']:6.2f}  n={int(row['n'])}")
    lines.append(f"max cell period R: {cells['wr'].max():.2f}")
    # per year, decisive signals, period T
    lines.append("")
    lines.append("per year period T, main cost")
    tt = trades[(trades.period == "T") & (trades.signal.isin(DECISIVE))].copy()
    tt["year"] = pd.to_datetime(tt["entry_date"]).dt.year
    for (k, y), g in tt.groupby(["signal", "year"]):
        lines.append(f"  {k:15s} {y}  n={len(g):4d}  winrate {(g.R > 0).mean() * 100:5.1f}%  meanR {g.R.mean():+.4f}")
    # EURNZD MACD Line ZC
    for per_name in ("R", "T"):
        g = trades[(trades.pair == "EURNZD") & (trades.signal == "MACD Line ZC") & (trades.period == per_name)]
        if len(g):
            k = int((g.R > 0).sum())
            lo, hi = wilson(k, len(g))
            lines.append(f"EURNZD MACD Line ZC period {per_name}: {k}/{len(g)} = {k / len(g) * 100:.1f}% [{lo * 100:.1f}-{hi * 100:.1f}]")
    txt = "\n".join(lines)
    if not a.quiet:
        print(txt)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    if a.trades:
        trades.to_csv(a.trades, index=False)


if __name__ == "__main__":
    main()
