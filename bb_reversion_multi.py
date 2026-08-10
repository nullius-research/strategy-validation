"""
bb_reversion_multi.py

Same Bollinger reversion test, run across a basket of pairs and pooled.

Why this exists: on one pair you had 89 trades and a confidence interval half an
R wide. A real edge of +0.05R is invisible at that sample size. Pooling ten
pairs gets you the observations you need.

One honest complication. FX majors are not independent, they share a common
dollar factor, so 900 trades across ten pairs is worth far less than 900 trades
on ten unrelated instruments. The bootstrap here therefore resamples whole
DAYS, keeping every symbol's trades from that day together. That is a cluster
bootstrap and it gives an interval that is wider, and honest, rather than
narrow and flattering.

Data prep in MT5: export M15 for each pair via Ctrl+U > Bars > Export.
Put every CSV in one folder. Filenames keep the MT5 default, the symbol is read
from the start of the filename.

Usage:
  python bb_reversion_multi.py --dir ./data
  python bb_reversion_multi.py --dir ./data --sl-mult 1.5 --cost-pips 1.5
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# --- Time -------------------------------------------------------------
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


def symbol_from_name(path: Path) -> str:
    m = re.match(r"([A-Za-z]{6,8})", path.stem)
    return (m.group(1) if m else path.stem).upper()


def load_mt5_csv(path: Path, winter_offset: int) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=None, engine="python")
    raw.columns = [c.strip().strip("<>").upper() for c in raw.columns]
    if "DATE" not in raw.columns:
        raise ValueError(f"{path.name}: no DATE column")

    stamp = raw["DATE"].astype(str)
    if "TIME" in raw.columns:
        stamp = stamp + " " + raw["TIME"].astype(str)

    df = pd.DataFrame(index=pd.to_datetime(stamp, format="mixed"))
    for s, d in [("OPEN", "Open"), ("HIGH", "High"), ("LOW", "Low"), ("CLOSE", "Close")]:
        if s not in raw.columns:
            raise ValueError(f"{path.name}: missing {s}")
        df[d] = pd.to_numeric(raw[s].values, errors="coerce")

    df = df.dropna().sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df.index = broker_to_utc(df.index, winter_offset)
    return df


def pip_size(df: pd.DataFrame, symbol: str) -> float:
    """JPY crosses quote to 3 decimals, everything else to 5."""
    if "JPY" in symbol:
        return 0.01
    return 0.01 if df["Close"].median() > 20 else 0.0001


# --- Signals ----------------------------------------------------------
def bollinger(h1: pd.DataFrame, period: int, sd: float) -> pd.DataFrame:
    x = h1.copy()
    x["MID"] = x["Close"].rolling(period).mean()
    s = x["Close"].rolling(period).std(ddof=0)
    x["SIGMA"] = s
    x["UPPER"] = x["MID"] + sd * s
    x["LOWER"] = x["MID"] - sd * s
    x["SLOPE"] = (x["MID"] - x["MID"].shift(50)).abs() / s.replace(0, np.nan)
    return x.dropna()


def find_signals(bb: pd.DataFrame) -> pd.DataFrame:
    up = bb["Close"] > bb["UPPER"]
    dn = bb["Close"] < bb["LOWER"]
    outside = up | dn
    fresh = outside & ~outside.shift(1, fill_value=False)
    sig = bb[fresh].copy()
    sig["Side"] = np.where(up[fresh], -1, 1)
    sig["ActFrom"] = sig.index + pd.Timedelta(hours=1)
    return sig


def _first_touch(hi, lo, cl, direction, entry, stop, target, cost, R):
    if direction == 1:
        s = np.flatnonzero(lo <= stop)
        t = np.flatnonzero(hi >= target)
    else:
        s = np.flatnonzero(hi >= stop)
        t = np.flatnonzero(lo <= target)
    i_s = s[0] if s.size else np.inf
    i_t = t[0] if t.size else np.inf
    if i_s <= i_t and np.isfinite(i_s):
        px, kind, bars = stop, "stop", i_s
    elif np.isfinite(i_t):
        px, kind, bars = target, "target", i_t
    else:
        px, kind, bars = cl[-1], "time", len(cl) - 1
    return (direction * (px - entry) - cost) / R, kind, int(bars)


def simulate(m15, sig, sl_mult, cost_pips, pip, max_bars, symbol):
    rows = []
    cost = cost_pips * pip
    idx = m15.index
    hi_a, lo_a = m15["High"].to_numpy(), m15["Low"].to_numpy()
    cl_a, op_a = m15["Close"].to_numpy(), m15["Open"].to_numpy()
    busy = pd.Timestamp.min

    for ts, s in sig.iterrows():
        if s["ActFrom"] <= busy:
            continue
        i0 = idx.searchsorted(s["ActFrom"])
        if i0 >= len(idx):
            continue
        i1 = min(i0 + max_bars, len(idx))
        if i1 - i0 < 4:
            continue

        entry, direction = op_a[i0], int(s["Side"])
        reward = abs(entry - s["MID"])
        if reward <= 0:
            continue
        R = sl_mult * reward
        hi, lo, cl = hi_a[i0:i1], lo_a[i0:i1], cl_a[i0:i1]

        r_r, r_k, r_b = _first_touch(hi, lo, cl, direction, entry,
                                     entry - direction * R,
                                     entry + direction * reward, cost, R)
        a_r, a_k, _ = _first_touch(hi, lo, cl, -direction, entry,
                                   entry + direction * R,
                                   entry - direction * reward, cost, R)

        rows.append({"Date": ts, "Symbol": symbol, "Dir": direction,
                     "Slope": s["SLOPE"], "R_pips": R / pip,
                     "real_R": r_r, "real_exit": r_k, "bars": r_b,
                     "anti_R": a_r, "anti_exit": a_k})
        busy = idx[min(i0 + r_b, len(idx) - 1)]

    return pd.DataFrame(rows)


def summarise(g: pd.DataFrame, col="real_R") -> dict:
    v = g[col].dropna()
    if v.empty:
        return {}
    w, l = v[v > 0], v[v <= 0]
    ex = g[col.replace("_R", "_exit")]
    return {"n": len(v), "win%": round(100 * len(w) / len(v), 1),
            "exp_R": round(v.mean(), 4), "total_R": round(v.sum(), 1),
            "PF": round(w.sum() / abs(l.sum()), 3) if l.sum() != 0 else np.inf,
            "target%": round(100 * (ex == "target").mean(), 1),
            "stop%": round(100 * (ex == "stop").mean(), 1),
            "time%": round(100 * (ex == "time").mean(), 1)}


def cluster_bootstrap(res: pd.DataFrame, col: str, n: int, rng) -> np.ndarray:
    """Resample whole days, not individual trades.

    Trades opened on the same day across correlated pairs are one bet, not ten.
    Resampling them independently would understate the interval badly.
    """
    days = res["Date"].dt.normalize()
    groups = [g[col].to_numpy() for _, g in res.groupby(days)]
    k = len(groups)
    out = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, k, k)
        out[i] = np.concatenate([groups[j] for j in pick]).mean()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Folder with one M15 CSV per pair")
    ap.add_argument("--broker-offset", type=int, default=2)
    ap.add_argument("--bb-period", type=int, default=200)
    ap.add_argument("--bb-sd", type=float, default=2.5)
    ap.add_argument("--sl-mult", type=float, default=2.0)
    ap.add_argument("--cost-pips", type=float, default=1.2)
    ap.add_argument("--max-bars", type=int, default=960)
    ap.add_argument("--out", default="bb_multi_trades.csv")
    a = ap.parse_args()

    files = sorted(Path(a.dir).glob("*.csv"))
    files = [f for f in files if not f.name.startswith(("bb_", "asian_"))]
    if not files:
        print(f"No CSV files in {a.dir}")
        sys.exit(1)

    all_res, skipped = [], []
    print(f"{'symbol':10}{'bars':>10}{'signals':>9}{'traded':>8}{'pip':>9}")
    for f in files:
        sym = symbol_from_name(f)
        try:
            m15 = load_mt5_csv(f, a.broker_offset)
        except Exception as e:
            skipped.append(f"{f.name}: {e}")
            continue
        pip = pip_size(m15, sym)
        h1 = m15.resample("1h").agg(Open=("Open", "first"), High=("High", "max"),
                                    Low=("Low", "min"), Close=("Close", "last")).dropna()
        if len(h1) < a.bb_period + 100:
            skipped.append(f"{f.name}: only {len(h1)} H1 bars")
            continue
        sig = find_signals(bollinger(h1, a.bb_period, a.bb_sd))
        r = simulate(m15, sig, a.sl_mult, a.cost_pips, pip, a.max_bars, sym)
        print(f"{sym:10}{len(m15):>10,}{len(sig):>9}{len(r):>8}{pip:>9}")
        if len(r):
            all_res.append(r)

    if skipped:
        print(f"\nSkipped {len(skipped)}: {skipped[:3]}")
    if not all_res:
        print("Nothing tradeable.")
        sys.exit(1)

    res = pd.concat(all_res, ignore_index=True)
    res["Date"] = pd.to_datetime(res["Date"])
    pd.set_option("display.width", 220)

    print(f"\nPooled trades: {len(res)} across {res['Symbol'].nunique()} symbols")
    print(f"Distinct trading days: {res['Date'].dt.normalize().nunique()}\n")

    print("=" * 84)
    print("FADE the break   vs   FOLLOW the break, pooled")
    print("=" * 84)
    print(pd.DataFrame({"fade": summarise(res, "real_R"),
                        "follow": summarise(res, "anti_R")}).T.to_string(), "\n")

    print("Per symbol (fade):")
    per = pd.DataFrame({s: summarise(g) for s, g in res.groupby("Symbol")}).T
    print(per.sort_values("exp_R", ascending=False).to_string(), "\n")

    print("By middle-band slope:")
    try:
        res["Regime"] = pd.qcut(res["Slope"], 3, labels=["flat", "medium", "steep"])
        print(pd.DataFrame({str(k): summarise(g)
                            for k, g in res.groupby("Regime", observed=True)}).T.to_string(), "\n")
    except ValueError:
        print("  skipped\n")

    print("By year:")
    print(pd.DataFrame({str(y): summarise(g)
                        for y, g in res.groupby(res["Date"].dt.year)}).T.to_string())

    rng = np.random.default_rng(42)
    print("\n" + "=" * 84)
    print("CLUSTER BOOTSTRAP, resampling whole days so correlated pairs stay together")
    print("=" * 84)
    for col, name in (("real_R", "fade"), ("anti_R", "follow")):
        b = cluster_bootstrap(res, col, 4000, rng)
        lo, hi = np.percentile(b, [2.5, 97.5])
        print(f"  {name:7} mean {res[col].mean():+.4f}R   "
              f"95% CI [{lo:+.4f}, {hi:+.4f}]   "
              f"P(edge>0) {100*(b>0).mean():5.1f}%")

    res["diff"] = res["real_R"] - res["anti_R"]
    b = cluster_bootstrap(res, "diff", 4000, rng)
    lo, hi = np.percentile(b, [2.5, 97.5])
    print(f"\n  fade minus follow: {res['diff'].mean():+.4f}R   "
          f"95% CI [{lo:+.4f}, {hi:+.4f}]")
    if lo > 0:
        print("  VERDICT: fading beats following and the interval clears zero.")
    elif hi < 0:
        print("  VERDICT: following beats fading. The premise is backwards.")
    else:
        print("  VERDICT: interval straddles zero. Even pooled, the band break")
        print("  carries no directional information.")

    per_pos = (per["exp_R"] > 0).sum()
    print(f"\n  Symbols with positive expectancy: {per_pos} of {len(per)}. "
          f"Coin flip would give about {len(per)/2:.0f}.")
    print("=" * 84)

    res.to_csv(a.out, index=False)
    print(f"\nPer-trade detail written to {a.out}")


if __name__ == "__main__":
    main()
