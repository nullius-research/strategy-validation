"""
asian_range_study2.py

Version 2. Fixes the flaw in v1: MFE and MAE gave you the extremes but not
which came first, so they could not tell you whether the idea makes money.

This version walks the bars forward after the break and records which level was
touched first, the stop or the target. It charges a round-trip cost. And it
runs a control: the same entries with the direction flipped at random.

The control is the point of the whole script. If the real breakout direction
does not beat a coin flip taken at the same moment with the same stop and the
same target, then the break carries no directional information and the idea is
finished. Everything else is decoration.

Usage:
  python asian_range_study2.py --file EURUSD_M15_xxx.csv --broker-offset 2
  python asian_range_study2.py --file ... --cost-pips 1.2 --min-R-pips 12
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

ASIA_START, ASIA_END = 0, 7
BREAK_START, BREAK_END = 7, 11
DAY_END = 16
ATR_PERIOD = 14
MIN_BARS_PER_DAY = 60
TARGETS = [0.5, 1.0, 1.5, 2.0]
N_CONTROL = 2000


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


# --- Sessions ---------------------------------------------------------
def build_daily(df: pd.DataFrame) -> pd.DataFrame:
    h, days = df.index.hour, df.index.normalize()
    daily = df.groupby(days).agg(High=("High", "max"), Low=("Low", "min"),
                                 Close=("Close", "last"), Bars=("Close", "size"))
    pc = daily["Close"].shift(1)
    tr = pd.concat([daily["High"] - daily["Low"],
                    (daily["High"] - pc).abs(),
                    (daily["Low"] - pc).abs()], axis=1).max(axis=1)
    daily["ATR"] = tr.rolling(ATR_PERIOD).mean()

    asia = df[(h >= ASIA_START) & (h < ASIA_END)]
    a = asia.groupby(asia.index.normalize()).agg(
        RangeHigh=("High", "max"), RangeLow=("Low", "min"), AsiaBars=("Close", "size"))

    out = daily.join(a, how="inner")
    out["Width"] = out["RangeHigh"] - out["RangeLow"]
    out = out[(out["Bars"] >= MIN_BARS_PER_DAY) & (out["AsiaBars"] >= 20) & (out["Width"] > 0)]
    out["Compression"] = out["Width"] / out["ATR"]
    return out.dropna(subset=["ATR"])


def _first_touch(highs, lows, closes, direction, entry, stop, target, cost, width):
    """Net R for one path. When a bar spans both levels the stop is assumed to
    hit first. That bias is deliberate, it stops the study flattering itself."""
    if direction == 1:
        s_hit = np.flatnonzero(lows <= stop)
        t_hit = np.flatnonzero(highs >= target)
    else:
        s_hit = np.flatnonzero(highs >= stop)
        t_hit = np.flatnonzero(lows <= target)

    i_s = s_hit[0] if s_hit.size else np.inf
    i_t = t_hit[0] if t_hit.size else np.inf

    if i_s <= i_t and np.isfinite(i_s):
        px = stop
    elif np.isfinite(i_t):
        px = target
    else:
        px = closes[-1]

    return (direction * (px - entry) - cost) / width


def simulate(df: pd.DataFrame, daily: pd.DataFrame, buffer_frac: float,
             cost_pips: float, pip: float) -> pd.DataFrame:
    """One row per break. Records the outcome for BOTH directions, so the
    control can be resampled instantly without re-walking the bars."""
    h = df.index.hour
    win = df[(h >= BREAK_START) & (h < DAY_END)]
    groups = dict(list(win.groupby(win.index.normalize())))
    cost = cost_pips * pip

    rows = []
    for day, d in daily.iterrows():
        bars = groups.get(day)
        if bars is None or len(bars) < 4:
            continue

        width = d["Width"]
        buf = buffer_frac * width
        up, dn = d["RangeHigh"] + buf, d["RangeLow"] - buf

        bh = bars.index.hour
        trig = bars[(bh >= BREAK_START) & (bh < BREAK_END)]
        iu = trig.index[trig["High"] >= up]
        idn = trig.index[trig["Low"] <= dn]
        t_up = iu[0] if len(iu) else None
        t_dn = idn[0] if len(idn) else None
        if t_up is None and t_dn is None:
            continue

        if t_dn is None or (t_up is not None and t_up <= t_dn):
            real_dir, entry, t0 = 1, up, t_up
        else:
            real_dir, entry, t0 = -1, dn, t_dn

        after = bars[bars.index >= t0]
        if after.empty:
            continue
        hi = after["High"].to_numpy()
        lo = after["Low"].to_numpy()
        cl = after["Close"].to_numpy()

        row = {"Date": day, "Compression": d["Compression"],
               "R_pips": width / pip, "Dir": real_dir,
               "BothSides": (t_up is not None and t_dn is not None)}

        for tgt in TARGETS:
            for lbl, dd in (("real", real_dir), ("anti", -real_dir)):
                stop = entry - dd * width
                target = entry + dd * width * tgt
                row[f"{lbl}@{tgt}"] = _first_touch(hi, lo, cl, dd, entry,
                                                   stop, target, cost, width)
        rows.append(row)

    return pd.DataFrame(rows).set_index("Date")


def summarise(res: pd.DataFrame) -> pd.DataFrame:
    out = {}
    for t in TARGETS:
        v = res[f"real@{t}"].dropna()
        if v.empty:
            continue
        w, l = v[v > 0], v[v <= 0]
        out[f"{t:.1f}R"] = {
            "n": len(v),
            "win%": 100 * len(w) / len(v),
            "expectancy_R": v.mean(),
            "total_R": v.sum(),
            "PF": (w.sum() / abs(l.sum())) if l.sum() != 0 else np.inf,
        }
    d = pd.DataFrame(out).T
    d.index.name = "target"
    return d


def control(res: pd.DataFrame, target: float, n: int, rng) -> tuple:
    """Resample direction as a coin flip per session."""
    real = res[f"real@{target}"].to_numpy()
    anti = res[f"anti@{target}"].to_numpy()
    picks = rng.random((n, len(real))) < 0.5
    sims = np.where(picks, real, anti).mean(axis=1)
    return sims, real.mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--broker-offset", type=int, default=2)
    ap.add_argument("--pip", type=float, default=0.0001)
    ap.add_argument("--buffer", type=float, default=0.15)
    ap.add_argument("--cost-pips", type=float, default=1.2,
                    help="Round trip cost: spread plus commission plus slippage")
    ap.add_argument("--min-R-pips", type=float, default=12.0,
                    help="Skip sessions whose range sits in the noise floor")
    ap.add_argument("--out", default="asian_range_paths.csv")
    a = ap.parse_args()

    df = load_mt5_csv(a.file, a.broker_offset)
    print(f"Loaded {len(df):,} bars, {df.index.min()} to {df.index.max()} UTC")
    print(f"Cost assumption: {a.cost_pips} pips round trip\n")

    daily = build_daily(df)
    res = simulate(df, daily, a.buffer, a.cost_pips, a.pip)
    if res.empty:
        print("No breaks found. Check the export range.")
        sys.exit(1)

    before = len(res)
    res = res[res["R_pips"] >= a.min_R_pips]
    print(f"Breaks: {before}, kept after the {a.min_R_pips} pip floor: {len(res)}")
    if len(res) < 50:
        print("Too few sessions to say anything. Export a longer history.")
        sys.exit(1)
    print(f"Median R: {res['R_pips'].median():.1f} pips   "
          f"both sides broke: {100*res['BothSides'].mean():.1f}%\n")

    pd.set_option("display.width", 200)
    print("=" * 74)
    print("ALL BREAKS, net of costs. Stop is 1R, the far side of the range.")
    print("=" * 74)
    print(summarise(res).round(3).to_string(), "\n")

    try:
        res["Tercile"] = pd.qcut(res["Compression"], 3,
                                 labels=["narrow", "middle", "wide"])
        for name, g in res.groupby("Tercile", observed=True):
            print(f"--- {name} range ({len(g)} sessions, median R "
                  f"{g['R_pips'].median():.1f} pips) ---")
            print(summarise(g).round(3).to_string(), "\n")
    except ValueError:
        print("(compression terciles skipped, not enough distinct values)\n")

    rng = np.random.default_rng(42)
    print("=" * 74)
    print(f"CONTROL: identical entries, direction flipped at random, {N_CONTROL} runs.")
    print("If the real number sits inside the control band, the break tells you")
    print("nothing about direction and the premise is dead.")
    print("=" * 74)
    for t in TARGETS:
        sims, real = control(res, t, N_CONTROL, rng)
        pct = 100 * (sims < real).mean()
        verdict = "BEATS CONTROL" if pct >= 95 else "inside noise"
        print(f"  target {t:.1f}R   real {real:+.4f}R   "
              f"control p5..p95 [{np.percentile(sims,5):+.4f}, "
              f"{np.percentile(sims,95):+.4f}]   pctile {pct:5.1f}   {verdict}")

    res.to_csv(a.out)
    print(f"\nPer-session detail written to {a.out}")


if __name__ == "__main__":
    main()
