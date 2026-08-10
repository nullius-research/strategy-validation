"""
asian_range_study.py

Measures the ASSUMPTION, not the strategy.

Question it answers: after the Asian session range breaks during the London
window, what actually happens next? And does a narrow (compressed) overnight
range lead to a better outcome than a wide one?

It places no trades and applies no entry rules. It reports the distribution of
MFE and MAE in R-multiples, split by compression, so you can see whether the
edge exists before writing a single line of EA code.

If the compressed tercile does not clearly beat the wide tercile, the idea is
dead and you have lost one afternoon instead of three months.

--- Getting the data out of MT5 ---
  View > Symbols (Ctrl+U) > select EURUSD > Bars tab
  Set timeframe M15, pick your date range, click Export
  Save as a .csv

The export is tab separated with a header like:
  <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>

--- Usage ---
  python asian_range_study.py --file EURUSD_M15.csv --broker-offset 2

--broker-offset is your server's WINTER offset from UTC in hours.
IC Markets and most EU brokers run EET, so that is 2. The script applies the
US daylight saving schedule on top, which is what FX brokers follow.

Always read the "hourly volatility profile" diagnostic it prints. If the London
open does not show up as a volatility jump around 07:00-08:00 UTC, your offset
is wrong and every number below it is meaningless.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

# --- Study windows, all in UTC -----------------------------------------
ASIA_START, ASIA_END = 0, 7        # range built from 00:00 up to 07:00
BREAK_START, BREAK_END = 7, 11     # only breaks inside this window count
DAY_END = 16                       # everything measured up to 16:00

ATR_PERIOD = 14
MIN_BARS_PER_DAY = 60              # M15 sanity floor, a full day is 96


# --- Time handling ------------------------------------------------------
def _us_dst_bounds(year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Second Sunday in March to first Sunday in November."""
    march = pd.date_range(f"{year}-03-01", f"{year}-03-31", freq="D")
    nov = pd.date_range(f"{year}-11-01", f"{year}-11-30", freq="D")
    start = march[march.dayofweek == 6][1]          # 2nd Sunday
    end = nov[nov.dayofweek == 6][0]                # 1st Sunday
    return start, end


def broker_to_utc(idx: pd.DatetimeIndex, winter_offset: int) -> pd.DatetimeIndex:
    """Convert broker server time to UTC, honouring the US DST schedule.

    Getting this wrong shifts every session boundary by an hour for eight
    months of the year, which quietly destroys any session-based study.
    """
    offsets = np.full(len(idx), winter_offset, dtype=float)
    for year in np.unique(idx.year):
        s, e = _us_dst_bounds(int(year))
        in_dst = (idx >= s) & (idx < e)
        offsets[in_dst] = winter_offset + 1
    return idx - pd.to_timedelta(offsets, unit="h")


# --- Loading ------------------------------------------------------------
def load_mt5_csv(path: str, winter_offset: int) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=None, engine="python")
    raw.columns = [c.strip().strip("<>").upper() for c in raw.columns]

    if "DATE" not in raw.columns:
        raise ValueError(f"No DATE column. Found: {list(raw.columns)}")

    if "TIME" in raw.columns:
        stamp = raw["DATE"].astype(str) + " " + raw["TIME"].astype(str)
    else:
        stamp = raw["DATE"].astype(str)

    df = pd.DataFrame(index=pd.to_datetime(stamp, format="mixed"))
    for src, dst in [("OPEN", "Open"), ("HIGH", "High"),
                     ("LOW", "Low"), ("CLOSE", "Close")]:
        if src not in raw.columns:
            raise ValueError(f"Missing {src} column")
        df[dst] = pd.to_numeric(raw[src].values, errors="coerce")

    df["Spread"] = pd.to_numeric(raw.get("SPREAD", 0), errors="coerce").fillna(0).values
    df["TickVol"] = pd.to_numeric(raw.get("TICKVOL", 0), errors="coerce").fillna(0).values

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    if df.index.has_duplicates:
        df = df[~df.index.duplicated(keep="first")]

    df.index = broker_to_utc(df.index, winter_offset)
    df.index.name = "utc"
    return df


def hourly_profile(df: pd.DataFrame) -> pd.Series:
    """Mean bar range per UTC hour. Used to verify the time offset."""
    rng = (df["High"] - df["Low"]) * 1e4          # pips for a 5-digit major
    return rng.groupby(df.index.hour).mean()


# --- The measurement ----------------------------------------------------
def build_daily(df: pd.DataFrame) -> pd.DataFrame:
    """One row per session day with range, break and outcome fields."""
    hours = df.index.hour
    days = df.index.normalize()

    # Daily true range for the compression yardstick.
    daily = df.groupby(days).agg(High=("High", "max"), Low=("Low", "min"),
                                 Close=("Close", "last"), Bars=("Close", "size"))
    prev_close = daily["Close"].shift(1)
    tr = pd.concat([daily["High"] - daily["Low"],
                    (daily["High"] - prev_close).abs(),
                    (daily["Low"] - prev_close).abs()], axis=1).max(axis=1)
    daily["ATR"] = tr.rolling(ATR_PERIOD).mean()

    asia = df[(hours >= ASIA_START) & (hours < ASIA_END)]
    a = asia.groupby(asia.index.normalize()).agg(
        RangeHigh=("High", "max"), RangeLow=("Low", "min"),
        AsiaBars=("Close", "size"), Spread=("Spread", "median"))

    out = daily.join(a, how="inner")
    out["Width"] = out["RangeHigh"] - out["RangeLow"]
    out = out[(out["Bars"] >= MIN_BARS_PER_DAY) & (out["AsiaBars"] >= 20)]
    out = out[out["Width"] > 0]
    out["Compression"] = out["Width"] / out["ATR"]
    return out.dropna(subset=["ATR"])


def measure_breaks(df: pd.DataFrame, daily: pd.DataFrame,
                   point: float, buffer_frac: float) -> pd.DataFrame:
    """For each day, find the first break in the London window and record what
    the price did afterwards, in R where R = the range width."""
    hours = df.index.hour
    win = df[(hours >= BREAK_START) & (hours < DAY_END)]
    grouped = dict(list(win.groupby(win.index.normalize())))

    rows = []
    for day, d in daily.iterrows():
        bars = grouped.get(day)
        if bars is None or len(bars) < 4:
            continue

        width = d["Width"]
        buf = max(buffer_frac * width, 3.0 * d["Spread"] * point)
        up_lvl = d["RangeHigh"] + buf
        dn_lvl = d["RangeLow"] - buf

        # Only bars inside the break window can trigger the entry.
        bh = bars.index.hour
        trig = bars[(bh >= BREAK_START) & (bh < BREAK_END)]

        up = trig.index[trig["High"] >= up_lvl]
        dn = trig.index[trig["Low"] <= dn_lvl]
        t_up = up[0] if len(up) else None
        t_dn = dn[0] if len(dn) else None

        if t_up is None and t_dn is None:
            rows.append({"Date": day, "Width": width, "Compression": d["Compression"],
                         "Broke": False, "Dir": 0, "MFE_R": np.nan, "MAE_R": np.nan,
                         "Close_R": np.nan, "Spread": d["Spread"], "BothSides": False})
            continue

        if t_dn is None or (t_up is not None and t_up <= t_dn):
            direction, entry, t0 = 1, up_lvl, t_up
        else:
            direction, entry, t0 = -1, dn_lvl, t_dn

        after = bars[bars.index >= t0]
        if after.empty:
            continue

        if direction == 1:
            mfe = (after["High"].max() - entry) / width
            mae = (entry - after["Low"].min()) / width
        else:
            mfe = (entry - after["Low"].min()) / width
            mae = (after["High"].max() - entry) / width

        close_r = direction * (after["Close"].iloc[-1] - entry) / width

        rows.append({"Date": day, "Width": width, "Compression": d["Compression"],
                     "Broke": True, "Dir": direction,
                     "MFE_R": mfe, "MAE_R": mae, "Close_R": close_r,
                     "Spread": d["Spread"],
                     "BothSides": (t_up is not None and t_dn is not None)})

    return pd.DataFrame(rows).set_index("Date")


# --- Reporting ----------------------------------------------------------
def describe(g: pd.DataFrame) -> dict:
    b = g[g["Broke"]]
    if len(b) == 0:
        return {}
    return {
        "days": len(g),
        "break%": 100 * len(b) / len(g),
        "MFE_med": b["MFE_R"].median(),
        "MFE_p75": b["MFE_R"].quantile(0.75),
        "MFE_p90": b["MFE_R"].quantile(0.90),
        "MAE_med": b["MAE_R"].median(),
        "P(MFE>1R)": 100 * (b["MFE_R"] > 1.0).mean(),
        "P(MAE>1R)": 100 * (b["MAE_R"] > 1.0).mean(),
        "Close_med": b["Close_R"].median(),
        "whipsaw%": 100 * b["BothSides"].mean(),
        "pips_R": 1e4 * b["Width"].median(),
        "spread": b["Spread"].median(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="MT5 M15 export CSV")
    ap.add_argument("--broker-offset", type=int, default=2,
                    help="Server winter offset from UTC in hours")
    ap.add_argument("--point", type=float, default=0.00001,
                    help="Point size, 0.00001 for 5-digit majors")
    ap.add_argument("--buffer", type=float, default=0.15,
                    help="Break buffer as a fraction of range width")
    ap.add_argument("--out", default="asian_range_results.csv")
    a = ap.parse_args()

    df = load_mt5_csv(a.file, a.broker_offset)
    print(f"Loaded {len(df):,} bars, {df.index.min()} to {df.index.max()} UTC\n")

    print("Hourly volatility profile, mean bar range in pips per UTC hour.")
    print("Sanity check: the jump should sit at 07:00-08:00 (London) and")
    print("13:00-15:00 (New York). If not, --broker-offset is wrong.\n")
    prof = hourly_profile(df)
    peak = prof.idxmax()
    for h, v in prof.items():
        bar = "#" * int(round(v / max(prof.max(), 1e-9) * 44))
        print(f"  {h:02d}:00 {v:6.2f} {bar}")
    print(f"\n  peak hour: {peak:02d}:00 UTC")
    if not (6 <= peak <= 15):
        print("  WARNING: peak is outside the London/NY window. Check the offset.")

    daily = build_daily(df)
    res = measure_breaks(df, daily, a.point, a.buffer)
    if res.empty:
        print("\nNo usable days. Check the export range.")
        sys.exit(1)

    print(f"\n{'='*68}\nSessions analysed: {len(res)}   "
          f"broke in window: {int(res['Broke'].sum())} "
          f"({100*res['Broke'].mean():.1f}%)\n{'='*68}")

    # The whole point: does compression matter?
    res["Tercile"] = pd.qcut(res["Compression"], 3,
                             labels=["narrow", "middle", "wide"])

    stats = {}
    for name, g in res.groupby("Tercile", observed=True):
        stats[name] = describe(g)
    stats["ALL"] = describe(res)

    table = pd.DataFrame(stats).T
    pd.set_option("display.width", 200)
    print("\nOutcome by overnight-range compression (R = range width)\n")
    print(table.round(2).to_string())

    n = stats.get("narrow", {})
    w = stats.get("wide", {})
    if n and w:
        edge = n["MFE_med"] - w["MFE_med"]
        print(f"\n{'='*68}")
        print(f"Median MFE, narrow {n['MFE_med']:.2f}R vs wide {w['MFE_med']:.2f}R "
              f"(difference {edge:+.2f}R)")
        print(f"Median R in pips, narrow {n['pips_R']:.1f}  wide {w['pips_R']:.1f}")
        print(f"Median spread {n['spread']:.1f} points")
        if edge < 0.05:
            print("\nVERDICT: compression buys you nothing. The filter is not")
            print("the edge you hoped for. Do not build the EA on this premise.")
        else:
            print("\nVERDICT: compression separates the outcomes. Worth pursuing,")
            print("but check the cost column before celebrating.")
        print("="*68)

    res.to_csv(a.out)
    print(f"\nPer-session detail written to {a.out}")
    print("Columns: Width, Compression, Broke, Dir, MFE_R, MAE_R, Close_R, BothSides")


if __name__ == "__main__":
    main()
