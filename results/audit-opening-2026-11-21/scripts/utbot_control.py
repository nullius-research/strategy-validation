"""Test K: UT Bot Alerts on Nasdaq 5 minutes against a control group.

Implements hypothesis v1.1 (15 Nov 2026), Dutch original binding.
v1.1: Null A uses the same colour and signal-line filter as the rule (direction from the filter);
the coin-flip control of v1.0 becomes Null B (supplementary).
Signals are deterministic code.

Usage:
  python utbot_control.py selftest
  python utbot_control.py noise
  python utbot_control.py run USTEC_M1.csv
"""
import sys
import math
import numpy as np
import pandas as pd
from numba import njit

POINT = 0.01            # SPREAD column unit (as test G)
RTH_START = 16 * 60 + 30  # 9:30 New York in server time (NY + 7), shifted per day
OPEN_OFFSETS = (0,)  # AUDIT 21 nov 2026: fixed opening 16:30 server time (9:30 New York), no detection
SESS_FROM = 8 * 60      # 08:00 New York
SESS_TO = 17 * 60       # 17:00 New York
KEY = 2.0
ATR_PER = 1
LR_LEN = 11
SIG_LEN = 7
SWING_N = 10
MIN_R = 1.0             # points
MAX_SIGNALS_DAY = 3
SLIP = 1.0              # points per side
N_NULL = 10000
SEED_NULL = 37
SEED_NOISE = 7
NOISE_SUBSTEPS = 60

# ------------------------------------------------------------------ data

def load_mt5(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        head = f.readline()
    sep = "\t" if "\t" in head else (";" if ";" in head else ",")
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    ts = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str), format="%Y.%m.%d %H:%M:%S")
    out = pd.DataFrame({"open": df["open"].astype(float).values, "high": df["high"].astype(float).values,
                        "low": df["low"].astype(float).values, "close": df["close"].astype(float).values,
                        "vol": df["tickvol"].astype(float).values, "spread": df["spread"].astype(float).values * POINT},
                       index=pd.DatetimeIndex(ts, name="ts"))
    return out[~out.index.duplicated(keep="first")].sort_index()

def detect_open_minutes(m1):
    """Per server date the opening minute (9:30 NY) from the largest tick-volume jump (as test G)."""
    res = {}
    for day, g in m1.groupby(m1.index.normalize()):
        mins = g.index.hour * 60 + g.index.minute
        full = pd.Series(g["vol"].values, index=mins).reindex(range(1440)).fillna(0).values
        best, bk = -np.inf, None
        for off in OPEN_OFFSETS:
            k = RTH_START + off
            jump = full[k:k + 15].mean() - full[k - 15:k].mean()
            if jump > best:
                best, bk = jump, k
        n_rth = ((mins >= bk) & (mins < bk + 390)).sum()
        res[day] = bk if n_rth >= 0.9 * 390 else None
    return res

def to_5m(m1):
    agg = m1.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "vol": "sum", "spread": "last"}).dropna(subset=["open"])
    return agg

def session_flags(b5, opens):
    """NY minute of each 5m bar's close and the session flag (bar closes inside 08:00-17:00 NY)."""
    day = b5.index.normalize()
    smin = b5.index.hour * 60 + b5.index.minute
    ny_close = np.full(len(b5), -1, np.int64)
    for i, (d, m) in enumerate(zip(day, smin)):
        k = opens.get(d)
        if k is not None:
            ny_close[i] = m + 5 - (k - 570)
    sess = (ny_close > SESS_FROM) & (ny_close <= SESS_TO)
    dayid = pd.factorize(day)[0].astype(np.int64)
    return ny_close, sess, dayid

# ------------------------------------------------------------------ indicators

def linreg_last(x, n):
    out = np.full(len(x), np.nan)
    t = np.arange(n, dtype=float); tm = t.mean(); den = ((t - tm) ** 2).sum()
    v = np.lib.stride_tricks.sliding_window_view(x, n)
    ym = v.mean(axis=1)
    slope = ((v - ym[:, None]) * (t - tm)).sum(axis=1) / den
    out[n - 1:] = ym - slope * tm + slope * (n - 1)
    return out

@njit(cache=True)
def ut_bot(src, h, l, c, key):
    n = len(src)
    tr = np.empty(n)
    tr[0] = h[0] - l[0]
    for i in range(1, n):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    nloss = key * tr          # ATR period 1: rma(tr, 1) = tr
    ts = np.zeros(n)
    prev = 0.0
    for i in range(n):
        p1 = src[i - 1] if i > 0 else 0.0
        if src[i] > prev and p1 > prev:
            ts[i] = max(prev, src[i] - nloss[i])
        elif src[i] < prev and p1 < prev:
            ts[i] = min(prev, src[i] + nloss[i])
        elif src[i] > prev:
            ts[i] = src[i] - nloss[i]
        else:
            ts[i] = src[i] + nloss[i]
        prev = ts[i]
    buy = np.zeros(n, np.bool_)
    sell = np.zeros(n, np.bool_)
    for i in range(1, n):
        above = src[i] > ts[i] and src[i - 1] <= ts[i - 1]
        below = ts[i] > src[i] and ts[i - 1] <= src[i - 1]
        buy[i] = src[i] > ts[i] and above
        sell[i] = src[i] < ts[i] and below
    return ts, buy, sell

def indicators(b5):
    o, h, l, c = (b5[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ts, buy, sell = ut_bot(c, h, l, c, KEY)
    bclose = linreg_last(c, LR_LEN)
    bopen = linreg_last(o, LR_LEN)
    sig = pd.Series(bclose).rolling(SIG_LEN).mean().to_numpy()
    lo10 = pd.Series(l).rolling(SWING_N).min().to_numpy()
    hi10 = pd.Series(h).rolling(SWING_N).max().to_numpy()
    return dict(o=o, h=h, l=l, c=c, ts=ts, buy=buy, sell=sell, sig=sig, lrgreen=bopen < bclose,
                lo10=lo10, hi10=hi10, spread=b5["spread"].to_numpy(float))

# ------------------------------------------------------------------ trades

@njit(cache=True)
def trade_from(i, d, o, h, l, c, sig, lo10, hi10, spread, slip, forced, ny_close, dayid):
    """Entry at close of bar i in direction d. Returns status, exit index, net R, gross R, R points.
    status 0 trade, 1 R below MIN_R, 2 no data."""
    n = len(c)
    if np.isnan(sig[i]) or np.isnan(lo10[i]):
        return 2, -1, 0.0, 0.0, 0.0
    e = c[i]
    stop = lo10[i] if d == 1 else hi10[i]
    R = (e - stop) * d
    if R < MIN_R:
        return 1, -1, 0.0, 0.0, R
    costR = (spread[i] + 2.0 * slip) / R
    for j in range(i + 1, n):
        if d == 1:
            if o[j] <= stop:
                g = (o[j] - e) / R
                return 0, j, g - costR, g, R
            if l[j] <= stop:
                g = -1.0
                return 0, j, g - costR, g, R
            if c[j] < sig[j] and c[j] > e:
                g = (c[j] - e) / R
                return 0, j, g - costR, g, R
        else:
            if o[j] >= stop:
                g = (e - o[j]) / R
                return 0, j, g - costR, g, R
            if h[j] >= stop:
                g = -1.0
                return 0, j, g - costR, g, R
            if c[j] > sig[j] and c[j] < e:
                g = (e - c[j]) / R
                return 0, j, g - costR, g, R
        if forced and (dayid[j] != dayid[i] or ny_close[j] >= SESS_TO):
            g = d * (c[j] - e) / R
            return 0, j, g - costR, g, R
    g = d * (c[n - 1] - e) / R
    return 0, -(n - 1) - 10, g - costR, g, R

def run_rule(ind, ny_close, sess, dayid, lo, hi, slip=SLIP, color="candle", forced=False):
    o, h, l, c, sig = ind["o"], ind["h"], ind["l"], ind["c"], ind["sig"]
    fun = dict(days=int(len(np.unique(dayid[lo:hi][sess[lo:hi]]))), ut_signals_in_session=0, within_first_three=0,
               color_ok=0, signal_line_ok=0, lapsed_open_trade=0, dropped_R_below_1=0, trades=0)
    trades = []
    busy = -1
    cnt_day = {}
    for i in range(max(lo, 30), hi):
        if not sess[i] or not (ind["buy"][i] or ind["sell"][i]):
            continue
        fun["ut_signals_in_session"] += 1
        k = cnt_day.get(dayid[i], 0)
        if k >= MAX_SIGNALS_DAY:
            continue
        cnt_day[dayid[i]] = k + 1
        fun["within_first_three"] += 1
        d = 1 if ind["buy"][i] else -1
        green = ind["lrgreen"][i] if color == "linreg" else c[i] > o[i]
        red = (not ind["lrgreen"][i]) if color == "linreg" else c[i] < o[i]
        if not ((d == 1 and green) or (d == -1 and red)):
            continue
        fun["color_ok"] += 1
        if not ((d == 1 and c[i] > sig[i]) or (d == -1 and c[i] < sig[i])):
            continue
        fun["signal_line_ok"] += 1
        if i < busy:
            fun["lapsed_open_trade"] += 1
            continue
        st, ex, r, g, R = trade_from(i, d, o, h, l, c, sig, ind["lo10"], ind["hi10"], ind["spread"], slip, forced, ny_close, dayid)
        if st == 1:
            fun["dropped_R_below_1"] += 1
            continue
        if st != 0:
            continue
        open_end = ex < 0
        exi = (-ex - 10) if open_end else ex
        trades.append((i, d, exi, r, g, R, open_end, dayid[i], dayid[exi] != dayid[i]))
        busy = exi
    fun["trades"] = len(trades)
    return trades, fun

# ------------------------------------------------------------------ control group

@njit(cache=True)
def precompute(cand, o, h, l, c, sig, lo10, hi10, spread, slip, ny_close, dayid):
    m = len(cand)
    st = np.empty((2, m), np.int64); ex = np.empty((2, m), np.int64); rr = np.empty((2, m))
    for k in range(m):
        i = cand[k]
        for di in range(2):
            d = 1 if di == 0 else -1
            s, e, r, g, R = trade_from(i, d, o, h, l, c, sig, lo10, hi10, spread, slip, False, ny_close, dayid)
            st[di, k] = s
            ex[di, k] = e if e >= 0 else (-e - 10)
            rr[di, k] = r
    return st, ex, rr

@njit(cache=True)
def null_runs(cand, cday, st, ex, rr, ntr, nrun, seed, trend_dir, use_trend):
    """Sequential process over session bars: geometric wait, then entry; after the exit continue
    from the first session bar at or after the exit bar; at most 3 entries per day."""
    np.random.seed(seed)
    m = len(cand)
    out = np.full(nrun, np.nan)
    hold = 0.0; cntv = 0
    for k in range(m):
        if st[0, k] == 0:
            e = ex[0, k]
            q = np.searchsorted(cand, e)
            hold += q - k; cntv += 1
    hold /= max(cntv, 1)
    mean_gap = max(1.0, (m - ntr * hold) / max(ntr, 1))
    p = 1.0 / mean_gap
    for run in range(nrun):
        k = 0; tot = 0.0; cnt = 0; curday = -1; nday = 0
        while True:
            k += np.random.geometric(p) - 1
            if k >= m:
                break
            if cday[k] != curday:
                curday = cday[k]; nday = 0
            if nday >= MAX_SIGNALS_DAY:
                while k < m and cday[k] == curday:
                    k += 1
                continue
            if use_trend:
                dd = trend_dir[k]
                if dd == 0:
                    k += 1
                    continue
                di = 0 if dd == 1 else 1
            else:
                di = 0 if np.random.random() < 0.5 else 1
            if st[di, k] != 0:
                k += 1
                continue
            tot += rr[di, k]; cnt += 1; nday += 1
            k = np.searchsorted(cand, ex[di, k])
        if cnt > 0:
            out[run] = tot / cnt
    return out

def null_compare(ind, ny_close, sess, dayid, lo, hi, trades, slip=SLIP, nrun=N_NULL, seed=SEED_NULL):
    idx = np.arange(len(sess))
    cand = idx[(idx >= max(lo, 30)) & (idx < hi) & sess].astype(np.int64)
    st, ex, rr = precompute(cand, ind["o"], ind["h"], ind["l"], ind["c"], ind["sig"],
                            ind["lo10"], ind["hi10"], ind["spread"], slip, ny_close, dayid)
    # v1.1: Null A takes the same colour and signal-line filter as the rule; the filter fixes the direction
    cc, oo, ss = ind["c"][cand], ind["o"][cand], ind["sig"][cand]
    trend = np.where((cc > oo) & (cc > ss), 1, np.where((cc < oo) & (cc < ss), -1, 0)).astype(np.int64)
    real = float(np.mean([t[3] for t in trades]))
    res = {}
    for name, use, sd in (("A", True, seed), ("B", False, seed + 1)):
        mvals = null_runs(cand, dayid[cand], st, ex, rr, len(trades), nrun, sd, trend, use)
        mvals = mvals[~np.isnan(mvals)]
        pct = 100.0 * ((mvals < real).sum() + 0.5 * (mvals == real).sum()) / len(mvals)
        res[name] = dict(p5=float(np.percentile(mvals, 5)), p50=float(np.percentile(mvals, 50)),
                         p95=float(np.percentile(mvals, 95)), percentile=float(pct))
    return real, res

# ------------------------------------------------------------------ statistics

def wilson(k, n, z=1.96):
    p = k / n
    cc = (p + z * z / (2 * n)) / (1 + z * z / n)
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (cc - hw), 100 * (cc + hw)

def day_boot(r, days, nb=10000, seed=11):
    rng = np.random.default_rng(seed)
    u = np.unique(days)
    groups = [r[days == x] for x in u]
    sums = np.array([g.sum() for g in groups]); cnts = np.array([len(g) for g in groups])
    vals = []
    for _ in range(nb):
        pick = rng.integers(0, len(u), len(u))
        vals.append(sums[pick].sum() / cnts[pick].sum())
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

def summary(trades):
    r = np.array([t[3] for t in trades]); g = np.array([t[4] for t in trades]); R = np.array([t[5] for t in trades])
    days = np.array([t[7] for t in trades])
    wins = int((r > 0).sum())
    pos = r[r > 0].sum(); neg = -r[r < 0].sum()
    streak = best = 0
    for x in r:
        streak = streak + 1 if x <= 0 else 0
        best = max(best, streak)
    return dict(trades=len(r), winrate=100 * wins / len(r), winrate_95=wilson(wins, len(r)),
                mean_R=float(r.mean()), mean_R_95=day_boot(r, days), pf_R=float(pos / neg) if neg > 0 else float("inf"),
                gross_mean_R=float(g.mean()), median_R_points=float(np.median(R)),
                best_R=float(r.max()), worst_R=float(r.min()), longest_losing_streak=best,
                mean_bars_held=float(np.mean([t[2] - t[0] for t in trades])),
                overnight_share=float(np.mean([t[8] for t in trades])),
                long=int(sum(1 for t in trades if t[1] == 1)), short=int(sum(1 for t in trades if t[1] == -1)),
                open_at_end=int(sum(1 for t in trades if t[6])))

# ------------------------------------------------------------------ pipeline

def prepare(m1):
    opens = detect_open_minutes(m1)
    b5 = to_5m(m1)
    ny_close, sess, dayid = session_flags(b5, opens)
    ind = indicators(b5)
    return b5, ind, ny_close, sess, dayid

def synth_m1(rng, years=5, start_price=15000.0, vol_year=0.20):
    """Generator of test G v1.1: random walk without drift, 1380 M1 bars per weekday (01:00-24:00 server),
    70% of daily variance in the session, more tick volume in the session, 60 sub-steps per minute."""
    n_days = years * 252
    var_day = vol_year ** 2 / 252
    mins = np.arange(60, 1440)
    in_rth = (mins >= RTH_START) & (mins < RTH_START + 390)
    var_min = np.where(in_rth, 0.7 * var_day / 390, 0.3 * var_day / (len(mins) - 390))
    sd_sub = np.sqrt(var_min / NOISE_SUBSTEPS)
    logp = np.log(start_price)
    frames = []
    for day in pd.bdate_range("2010-01-04", periods=n_days):
        steps = rng.standard_normal((len(mins), NOISE_SUBSTEPS)) * sd_sub[:, None]
        path = logp + np.cumsum(steps.ravel()).reshape(len(mins), NOISE_SUBSTEPS)
        prev = np.r_[logp, path[:-1, -1]]
        frames.append(pd.DataFrame({"open": np.exp(prev), "high": np.exp(np.maximum(path.max(1), prev)),
                                    "low": np.exp(np.minimum(path.min(1), prev)), "close": np.exp(path[:, -1]),
                                    "vol": np.where(in_rth, 100.0, 20.0), "spread": np.full(len(mins), 1.0)},
                                   index=day + pd.to_timedelta(mins, unit="m")))
        logp = path[-1, -1]
    return pd.concat(frames)

def noise(sets=24, nrun=2000):
    rng = np.random.default_rng(SEED_NOISE)
    pcts = []
    for s in range(sets):
        m1 = synth_m1(rng)
        b5, ind, nyc, sess, dayid = prepare(m1)
        trades, fun = run_rule(ind, nyc, sess, dayid, 0, len(b5))
        real, res = null_compare(ind, nyc, sess, dayid, 0, len(b5), trades, nrun=nrun, seed=SEED_NULL + s)
        wr = 100 * np.mean([t[3] > 0 for t in trades])
        pcts.append(res["A"]["percentile"])
        print("set %2d  trades %5d  winrate %5.1f  mean net R %+.4f  percentile Null A %5.1f" % (s, len(trades), wr, real, res["A"]["percentile"]), flush=True)
    pcts = np.array(pcts)
    print("mean percentile %.1f, above 95: %d of %d" % (pcts.mean(), (pcts > 95).sum(), len(pcts)))
    print("NOISE CHECK", "PASSED" if 35 <= pcts.mean() <= 65 and (pcts > 95).sum() <= 3 else "FAILED")

def selftest():
    rng = np.random.default_rng(3)
    m1 = synth_m1(rng, years=1)
    b5 = to_5m(m1)
    ind = indicators(b5)
    c, h, l = ind["c"], ind["h"], ind["l"]
    # UT Bot by hand, straight from the Pine logic, plain python
    ts_prev = 0.0; ts_hand = []
    for i in range(len(c)):
        tr = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        nl = 2 * tr; p1 = c[i - 1] if i > 0 else 0.0
        if c[i] > ts_prev and p1 > ts_prev: t = max(ts_prev, c[i] - nl)
        elif c[i] < ts_prev and p1 < ts_prev: t = min(ts_prev, c[i] + nl)
        elif c[i] > ts_prev: t = c[i] - nl
        else: t = c[i] + nl
        ts_hand.append(t); ts_prev = t
    print("UT trailing stop max abs diff", float(np.max(np.abs(np.array(ts_hand) - ind["ts"]))))
    print("buy signals", int(ind["buy"].sum()), "sell signals", int(ind["sell"].sum()))
    i = 500
    y = c[i - 10:i + 1]
    b, a = np.polyfit(np.arange(11), y, 1)
    print("linreg close code %.4f hand %.4f" % (linreg_last(c, 11)[i], a + b * 10))
    lr = linreg_last(c, 11)
    print("signal code %.4f hand %.4f" % (ind["sig"][i], np.mean(lr[i - 6:i + 1])))

PERIODS = {"P1": ("2018-01-01", "2026-11-06"), "P0": ("2023-10-01", "2023-11-01"), "P2": ("2023-11-06", "2026-11-06")}

def run(path):
    m1 = load_mt5(path)
    b5, ind, nyc, sess, dayid = prepare(m1)
    times = b5.index
    def rng_idx(a, b):
        return int(times.searchsorted(pd.Timestamp(a))), int(times.searchsorted(pd.Timestamp(b)))
    variants = [("", dict()), (" slip0", dict(slip=0.0)), (" slip2", dict(slip=2.0)),
                (" linreg-colour", dict(color="linreg")), (" forced17", dict(forced=True))]
    for tag, kw in variants:
        for name, (a, b) in PERIODS.items():
            if tag and name != "P1":
                continue
            lo, hi = rng_idx(a, b)
            trades, fun = run_rule(ind, nyc, sess, dayid, lo, hi, **kw)
            print("\n=== %s%s  %s to %s" % (name, tag, times[lo], times[hi - 1]), flush=True)
            print("funnel", fun)
            if len(trades) < 5:
                print("too few trades"); continue
            s = summary(trades)
            print("summary", s)
            if name == "P0" and not tag:
                print("Null: skipped for P0 (one month)")
            else:
                real, res = null_compare(ind, nyc, sess, dayid, lo, hi, trades, slip=kw.get("slip", SLIP))
                print("Null", res, flush=True)
            if not tag:
                pd.DataFrame(trades, columns=["signal_bar", "dir", "exit_bar", "net_R", "gross_R", "R_points", "open_at_end", "day", "overnight"]).assign(
                    signal_time=lambda x: times[x["signal_bar"]], exit_time=lambda x: times[x["exit_bar"]]).to_csv("trades_%s.csv" % name, index=False)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    {"selftest": selftest, "noise": noise}.get(mode, lambda: run(sys.argv[2]))()
