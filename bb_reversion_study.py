"""
bb_reversion_study.py

Tests the premise: when price closes outside a wide Bollinger band, does fading
the move back toward the middle band make money?

Signals are computed on H1 bars, resampled from your M15 export. The path to
stop or target is then walked on the M15 bars, which is far more accurate than
checking H1 highs and lows.

The control here is the interesting one. Instead of a coin flip it runs the
MOMENTUM version: same moment, same stop, same target distance, but trading
with the break instead of against it. Reversion and continuation are the only
two stories you can tell about a band break, so this pits them directly against
each other. If fading does not clearly beat following, you have no edge, you
have a preference.

Usage:
  python bb_reversion_study.py --file EURUSD_M15_xxx.csv --broker-offset 2
  python bb_reversion_study.py --file ... --bb-period 200 --bb-sd 2.5 --sl-mult 2.0
"""

from __future__ import annotations

import argparse
import sys

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


def load_mt5_csv(path: str, winter_offset: int) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=None, engine="python")
    raw.columns = [c.strip().strip("<>").upper() for c in raw.columns]
    if "DATE" not in raw.columns:
        raise ValueError(f"No DATE column. Found: {list(raw.columns)}")

    stamp = raw["DATE"].astype(str)
    if "TIME" in raw.columns:
        stamp = stamp + " " + raw["TIME"].astype(str)

    df = pd.DataFrame(index=pd.to_datetime(stamp, format="mixed"))
    for s, d in [("OPEN", "Open"), ("HIGH", "High"), ("LOW", "Low"), ("CLOSE", "Close")]:
        df[d] = pd.to_numeric(raw[s].values, errors="coerce")

    df = df.dropna().sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df.index = broker_to_utc(df.index, winter_offset)
    return df


def to_h1(df: pd.DataFrame) -> pd.DataFrame:
    h = df.resample("1h").agg(Open=("Open", "first"), High=("High", "max"),
                              Low=("Low", "min"), Close=("Close", "last"))
    return h.dropna()


# --- Signals ----------------------------------------------------------
def bollinger(h1: pd.DataFrame, period: int, sd: float) -> pd.DataFrame:
    x = h1.copy()
    x["MID"] = x["Close"].rolling(period).mean()
    s = x["Close"].rolling(period).std(ddof=0)
    x["SIGMA"] = s
    x["UPPER"] = x["MID"] + sd * s
    x["LOWER"] = x["MID"] - sd * s
    # Slope of the middle band over 50 bars, scaled by sigma. Near zero means a
    # flat, ranging market. Large means a trend, where fading is dangerous.
    x["SLOPE"] = (x["MID"] - x["MID"].shift(50)).abs() / s.replace(0, np.nan)
    return x.dropna()


def find_signals(bb: pd.DataFrame) -> pd.DataFrame:
    """First close outside the band after being inside. Consecutive closes
    outside do not generate fresh entries."""
    out_up = bb["Close"] > bb["UPPER"]
    out_dn = bb["Close"] < bb["LOWER"]
    outside = out_up | out_dn
    fresh = outside & ~outside.shift(1, fill_value=False)

    sig = bb[fresh].copy()
    sig["Side"] = np.where(out_up[fresh], -1, 1)     # fade the break
    # Decision is made on the H1 close, so it can only be acted on afterwards.
    sig["ActFrom"] = sig.index + pd.Timedelta(hours=1)
    return sig


def _first_touch(hi, lo, cl, direction, entry, stop, target, cost, R):
    """Net R. A bar spanning both levels is scored as a stop. Deliberate bias."""
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


def simulate(m15: pd.DataFrame, sig: pd.DataFrame, sl_mult: float,
             cost_pips: float, pip: float, max_bars: int) -> pd.DataFrame:
    rows = []
    cost = cost_pips * pip
    idx = m15.index
    hi_all = m15["High"].to_numpy()
    lo_all = m15["Low"].to_numpy()
    cl_all = m15["Close"].to_numpy()
    op_all = m15["Open"].to_numpy()

    busy_until = pd.Timestamp.min.tz_localize(None)

    for ts, s in sig.iterrows():
        start = s["ActFrom"]
        if start <= busy_until:
            continue                       # one position at a time
        i0 = idx.searchsorted(start)
        if i0 >= len(idx):
            continue
        i1 = min(i0 + max_bars, len(idx))
        if i1 - i0 < 4:
            continue

        entry = op_all[i0]
        direction = int(s["Side"])
        # Distance back to the middle band is the natural target.
        reward = abs(entry - s["MID"])
        if reward <= 0:
            continue
        R = sl_mult * reward               # a deliberately wide stop

        hi, lo, cl = hi_all[i0:i1], lo_all[i0:i1], cl_all[i0:i1]

        real_r, real_k, real_b = _first_touch(
            hi, lo, cl, direction, entry,
            entry - direction * R, entry + direction * reward, cost, R)
        # Momentum control: same stop, same target distance, other way round.
        anti_r, anti_k, _ = _first_touch(
            hi, lo, cl, -direction, entry,
            entry + direction * R, entry - direction * reward, cost, R)

        rows.append({"Date": ts, "Dir": direction, "Slope": s["SLOPE"],
                     "R_pips": R / pip, "Target_pips": reward / pip,
                     "real_R": real_r, "real_exit": real_k, "bars": real_b,
                     "anti_R": anti_r, "anti_exit": anti_k})
        busy_until = idx[min(i0 + real_b, len(idx) - 1)]

    return pd.DataFrame(rows).set_index("Date")


def summarise(g: pd.DataFrame, col: str = "real_R") -> dict:
    v = g[col].dropna()
    if v.empty:
        return {}
    w, l = v[v > 0], v[v <= 0]
    ex = g[col.replace("_R", "_exit")]
    return {
        "n": len(v),
        "win%": round(100 * len(w) / len(v), 1),
        "expectancy_R": round(v.mean(), 4),
        "total_R": round(v.sum(), 1),
        "PF": round(w.sum() / abs(l.sum()), 3) if l.sum() != 0 else np.inf,
        "target%": round(100 * (ex == "target").mean(), 1),
        "stop%": round(100 * (ex == "stop").mean(), 1),
        "time%": round(100 * (ex == "time").mean(), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--broker-offset", type=int, default=2)
    ap.add_argument("--pip", type=float, default=0.0001)
    ap.add_argument("--bb-period", type=int, default=200)
    ap.add_argument("--bb-sd", type=float, default=2.5)
    ap.add_argument("--sl-mult", type=float, default=2.0,
                    help="Stop = this multiple of the distance back to the middle band")
    ap.add_argument("--cost-pips", type=float, default=1.2)
    ap.add_argument("--max-bars", type=int, default=960,
                    help="M15 bars before the trade is abandoned, 960 is 10 days")
    ap.add_argument("--out", default="bb_reversion_trades.csv")
    a = ap.parse_args()

    m15 = load_mt5_csv(a.file, a.broker_offset)
    h1 = to_h1(m15)
    print(f"Loaded {len(m15):,} M15 bars -> {len(h1):,} H1 bars")
    print(f"{h1.index.min()} to {h1.index.max()} UTC")
    print(f"BB({a.bb_period}, {a.bb_sd})   stop = {a.sl_mult}x the reward "
          f"distance   cost {a.cost_pips} pips\n")

    bb = bollinger(h1, a.bb_period, a.bb_sd)
    sig = find_signals(bb)
    print(f"Band breaks found: {len(sig)}")

    res = simulate(m15, sig, a.sl_mult, a.cost_pips, a.pip, a.max_bars)
    if len(res) < 40:
        print(f"Only {len(res)} tradeable signals. Too few to conclude anything.")
        sys.exit(1)

    print(f"Traded (one at a time): {len(res)}")
    print(f"Median stop {res['R_pips'].median():.1f} pips, "
          f"median target {res['Target_pips'].median():.1f} pips, "
          f"median hold {res['bars'].median():.0f} M15 bars\n")

    pd.set_option("display.width", 220)
    print("=" * 78)
    print("FADE the break (your idea)   vs   FOLLOW the break (control)")
    print("=" * 78)
    comp = pd.DataFrame({"fade": summarise(res, "real_R"),
                         "follow": summarise(res, "anti_R")}).T
    print(comp.to_string(), "\n")

    print("By direction:")
    for d, g in res.groupby("Dir"):
        print(f"  {'long (faded a low)' if d == 1 else 'short (faded a high)':22}",
              summarise(g))

    print("\nBy middle-band slope. Flat means ranging, steep means trending.")
    try:
        res["Regime"] = pd.qcut(res["Slope"], 3, labels=["flat", "medium", "steep"])
        for name, g in res.groupby("Regime", observed=True):
            print(f"  {name:7} n={len(g):4}", summarise(g))
    except ValueError:
        print("  (skipped, not enough distinct values)")

    print("\nBy year:")
    for y, g in res.groupby(res.index.year):
        print(f"  {y}  n={len(g):4}", summarise(g))

    print("\n" + "=" * 78)
    real, anti = res["real_R"].mean(), res["anti_R"].mean()
    diff = real - anti
    # Paired bootstrap on the per-trade difference.
    rng = np.random.default_rng(42)
    d = (res["real_R"] - res["anti_R"]).to_numpy()
    boot = rng.choice(d, size=(5000, len(d)), replace=True).mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"Fade {real:+.4f}R  vs follow {anti:+.4f}R   difference {diff:+.4f}R")
    print(f"95% bootstrap interval on the difference: [{lo:+.4f}, {hi:+.4f}]")
    if lo > 0:
        print("VERDICT: fading beats following, and the interval clears zero.")
    elif hi < 0:
        print("VERDICT: following beats fading. Your premise is backwards.")
    else:
        print("VERDICT: the interval straddles zero. Fading and following are")
        print("indistinguishable here. The band break carries no information.")
    print("=" * 78)

    res.to_csv(a.out)
    print(f"\nPer-trade detail written to {a.out}")


if __name__ == "__main__":
    main()
