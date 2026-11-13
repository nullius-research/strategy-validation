#!/usr/bin/env python3
"""
spy_open_control.py · Nullius Research
Measurement script for test G2 (buying SPY at the open, side claim of test G).
Hypothesis: hypothese-spy-opening.md v1.0, 13 Nov 2026, data source A.

Usage:
    python spy_open_control.py --noise [--sets 24] [--seed 7] [--n 10000]      (section 7)
    python spy_open_control.py --spy SPY_daily.csv [--from 2011-09-19] [--to 2026-09-18]
    python spy_open_control.py --us500 US500_M1.csv [--from 2017-03-22] [--to 2026-09-18]
                               [--point 0.01] [--n 10000] [--seed 29]
    python spy_open_control.py --compare SPY_daily.csv US500_M1.csv            (section 5)

SPY daily csv: columns date, open, high, low, close (Yahoo chart API, as test E).
US500 M1: MT5 export, tab separated, <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE>
<TICKVOL> <VOL> <SPREAD>, server time.

All fixed choices come from the hypothesis and are constants below.
Nothing here changes after the first run on real data.
"""
import argparse
import sys

import numpy as np
import pandas as pd

# ------------------------------------------------------------ fixed choices
RTH_START = 16 * 60 + 30     # 9:30 New York in server time (as test G)
RTH_LEN = 390                # 9:30-16:00
OPEN_OFFSETS = (-60, 0, 60)  # DST weeks, detected from tick volume (as test G)
MIN_SESSION_FRAC = 0.9       # session counts with >= 90% of its M1 bars
WINDOWS = (60, 120)          # 1 hour, 2 hours
CLAIM = {60: 0.51, 120: 0.53, "close": 0.54}
SPY_COST_BP = 2.0            # round trip
US500_SLIP_BP = 1.0          # on top of the spread of the entry bar
COST_SENS_BP = (0, 2, 4)
NOISE_DAYS = 2300
NOISE_DAY_VOL = 0.011        # daily move about 1.1%
NOISE_BUMP = 0.0005          # sensitivity check: +0.05% in the first hour
MIN_OBS = 100


# ------------------------------------------------------------ statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return mid - half, mid + half


def share_line(label, up, eq, n, claim=None):
    lo, hi = wilson(up, n)
    s = f"{label:<8} n={n:>5}  higher {up / n * 100:6.2f}%  (95%: {lo * 100:5.2f} to {hi * 100:5.2f})  equal {eq / n * 100:5.2f}%"
    if claim is not None:
        inside = lo <= claim <= hi
        s += f"  claim {claim * 100:.0f}%: {'inside' if inside else 'OUTSIDE'}"
        if not inside:
            s += f" (measured {'higher' if lo > claim else 'lower'})"
    s += f"  C5 lower bound > 50%: {'yes' if lo > 0.5 else 'no'}"
    if n < MIN_OBS:
        s += "  INSUFFICIENT (<100)"
    return s


def null_a(R, C, real_mean, w, rng, n, chunk=500):
    """R[d, s]: return of window w started at session minute s on day d (gross).
    C[d, s]: cost (fraction) for a start at minute s. Random start per day, uniform
    over 0..RTH_LEN-w (open included). Returns (percentile of real_mean, null means)."""
    D, S = R.shape
    means = np.empty(n)
    rows = np.arange(D)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        s = rng.integers(0, S, size=(b - a, D))
        means[a:b] = (R[rows, s] - C[rows, s]).mean(axis=1)
    pct = ((means < real_mean).sum() + 0.5 * (means == real_mean).sum()) / n * 100
    return pct, means


# ------------------------------------------------------------ session matrices
def session_matrix(days_open, days_close, days_spread):
    """Inputs per valid day: arrays of length RTH_LEN with bar open, bar close (forward filled)
    and spread fraction. Returns dict with open/close matrices."""
    return {"o": np.vstack(days_open), "c": np.vstack(days_close), "sp": np.vstack(days_spread)}


def window_returns(M, w):
    """Gross return from open of bar s to close of bar s+w-1, for s = 0..RTH_LEN-w."""
    S = RTH_LEN - w + 1
    o = M["o"][:, :S]
    c = M["c"][:, w - 1:w - 1 + S]
    return c / o - 1.0, M["sp"][:, :S]


def analyse_session(M, rng, n, slip_bp, label=""):
    out = {}
    lines = []
    D = M["o"].shape[0]
    for w in WINDOWS:
        R, SP = window_returns(M, w)
        cost = SP + slip_bp / 1e4
        r0 = R[:, 0]
        up, eq = int((r0 > 0).sum()), int((r0 == 0).sum())
        lines.append(share_line(f"{w // 60}h", up, eq, D, CLAIM[w]))
        net = r0 - cost[:, 0]
        lines.append(f"         mean gross {r0.mean() * 1e4:+.2f} bp, net {net.mean() * 1e4:+.2f} bp, "
                     f"higher after costs {(net > 0).mean() * 100:.2f}%")
        pct, means = null_a(R, cost, net.mean(), w, rng, n)
        lines.append(f"         Null A (random start, same window): percentile {pct:.1f}, "
                     f"null median {np.median(means) * 1e4:+.2f} bp, 95th {np.percentile(means, 95) * 1e4:+.2f} bp"
                     f"  C4 {'not falsified' if pct > 95 else 'FALSIFIED'}")
        out[w] = {"share": up / D, "pct": pct}
    rc = M["c"][:, -1] / M["o"][:, 0] - 1.0
    up, eq = int((rc > 0).sum()), int((rc == 0).sum())
    lines.append(share_line("close", up, eq, D, CLAIM["close"]))
    out["close"] = {"share": up / D}
    return out, lines


# ------------------------------------------------------------ noise check (section 7)
def synth_matrix(rng, days, bump=0.0):
    sig = NOISE_DAY_VOL / np.sqrt(RTH_LEN)
    steps = rng.normal(0.0, sig, size=(days, RTH_LEN))
    if bump:
        steps[:, :60] += bump / 60.0
    logp = np.cumsum(steps, axis=1)
    close = 100.0 * np.exp(logp)
    open_ = np.empty_like(close)
    open_[:, 0] = 100.0
    open_[:, 1:] = close[:, :-1]
    sp = np.full_like(close, 0.5 / 1e4)  # constant cost, irrelevant for the percentile
    return {"o": open_, "c": close, "sp": sp}


def noise_check(sets, seed, n):
    rng = np.random.default_rng(seed)
    print(f"noise check: {sets} sets x {NOISE_DAYS} days x {RTH_LEN} minute bars, no trend, "
          f"daily vol {NOISE_DAY_VOL}, seed {seed}, Null A runs {n}")
    res = {"base": {60: [], 120: [], "s60": [], "s120": [], "sc": []}, "bump": {60: [], 120: []}}
    for i in range(sets):
        M = synth_matrix(rng, NOISE_DAYS)
        o, _ = analyse_session(M, rng, n, 0.0)
        Mb = synth_matrix(rng, NOISE_DAYS, NOISE_BUMP)
        ob, _ = analyse_session(Mb, rng, n, 0.0)
        for w in WINDOWS:
            res["base"][w].append(o[w]["pct"])
            res["base"]["s" + str(w)].append(o[w]["share"])
            res["bump"][w].append(ob[w]["pct"])
        res["base"]["sc"].append(o["close"]["share"])
        print(f"set {i + 1:>2}: pct 1h {o[60]['pct']:5.1f} 2h {o[120]['pct']:5.1f} | "
              f"share 1h {o[60]['share'] * 100:5.2f} 2h {o[120]['share'] * 100:5.2f} close {o['close']['share'] * 100:5.2f} | "
              f"bump pct 1h {ob[60]['pct']:5.1f} 2h {ob[120]['pct']:5.1f}")
        sys.stdout.flush()
    ok = True
    print()
    for w in WINDOWS:
        p = np.array(res["base"][w])
        good = 35 <= p.mean() <= 65 and (p > 95).sum() <= 3
        ok &= good
        print(f"{w // 60}h: mean percentile {p.mean():.1f}, above 95 in {(p > 95).sum()} of {sets}, "
              f"below 5 in {(p < 5).sum()}: {'PASS' if good else 'FAIL'}")
    for key, lab in (("s60", "1h"), ("s120", "2h"), ("sc", "close")):
        s = np.array(res["base"][key]) * 100
        good = 49 <= s.mean() <= 51
        ok &= good
        print(f"share higher {lab}: mean {s.mean():.2f}%: {'PASS' if good else 'FAIL'}")
    for w in WINDOWS:
        p = np.array(res["bump"][w])
        print(f"sensitivity +{NOISE_BUMP * 100:.2f}% first hour, {w // 60}h: above 95 in {(p > 95).sum()} of {sets}"
              f" ({'enough' if (p > 95).sum() >= 20 else 'TOO FEW: test can miss small opening effects'}, reported, not decisive)")
    print(f"\nnoise check overall: {'PASS' if ok else 'FAIL'}")
    return ok


# ------------------------------------------------------------ real data
def load_spy(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()[["open", "high", "low", "close"]].dropna()


def run_spy(path, d_from, d_to):
    df = load_spy(path).loc[d_from:d_to]
    r = df["close"] / df["open"] - 1.0
    n, up, eq = len(r), int((r > 0).sum()), int((r == 0).sum())
    print(f"SPY daily {df.index[0].date()} to {df.index[-1].date()}")
    print(share_line("close", up, eq, n, CLAIM["close"]))
    for c in COST_SENS_BP:
        net = r - c / 1e4
        print(f"         cost {c} bp: mean net {net.mean() * 1e4:+.2f} bp, higher after costs {(net > 0).mean() * 100:.2f}%")
    print("per year:")
    for y, g in r.groupby(r.index.year):
        print(f"  {y}: n={len(g):>3}  higher {(g > 0).mean() * 100:5.1f}%  mean {g.mean() * 1e4:+.2f} bp")
    return r


def load_mt5(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        head = f.readline()
    sep = "\t" if "\t" in head else (";" if ";" in head else ",")
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    raw = df["date"].astype(str) + " " + df["time"].astype(str)
    ts = pd.to_datetime(raw, format="%Y.%m.%d %H:%M:%S", errors="coerce")
    if ts.isna().mean() > 0.5:
        ts = pd.to_datetime(raw, format="%Y.%m.%d %H:%M", errors="coerce")
    out = pd.DataFrame({k: df[k].astype(float).values for k in ("open", "high", "low", "close", "tickvol", "spread")},
                       index=pd.DatetimeIndex(ts, name="ts"))
    out = out[~out.index.isna()]
    return out[~out.index.duplicated(keep="first")].sort_index()


def detect_open(minutes, vol):
    best, best_k = -np.inf, None
    full = pd.Series(vol, index=minutes).reindex(range(0, 1440)).fillna(0).values
    for off in OPEN_OFFSETS:
        k = RTH_START + off
        if k - 15 < 0 or k + 15 > 1440:
            continue
        jump = full[k:k + 15].mean() - full[k - 15:k].mean()
        if jump > best:
            best, best_k = jump, k
    return best_k


def us500_matrix(path, point, d_from, d_to):
    m1 = load_mt5(path).loc[d_from:d_to]
    minute = (m1.index.hour * 60 + m1.index.minute).values
    date = m1.index.normalize()
    bounds = np.flatnonzero(np.r_[True, date[1:] != date[:-1], True])
    O, C, SP, dates, offs = [], [], [], [], []
    stats = {"days": 0, "open_found": 0, "valid": 0}
    for a, b in zip(bounds[:-1], bounds[1:]):
        stats["days"] += 1
        mins = minute[a:b]
        k = detect_open(mins, m1["tickvol"].values[a:b])
        if k is None:
            continue
        stats["open_found"] += 1
        sel = (mins >= k) & (mins < k + RTH_LEN)
        if sel.sum() < MIN_SESSION_FRAC * RTH_LEN:
            continue
        idx = mins[sel] - k
        g = pd.DataFrame({"o": m1["open"].values[a:b][sel], "c": m1["close"].values[a:b][sel],
                          "sp": m1["spread"].values[a:b][sel] * point}, index=idx).reindex(range(RTH_LEN))
        if np.isnan(g["o"].iloc[0]):
            continue  # no bar in the opening minute: no opening price
        g["c"] = g["c"].ffill()
        g["o"] = g["o"].fillna(g["c"].shift(1))  # missing bar: open = previous close
        g["sp"] = g["sp"].ffill()
        stats["valid"] += 1
        O.append(g["o"].values)
        C.append(g["c"].values)
        SP.append(g["sp"].values / g["o"].values)
        dates.append(date[a])
        offs.append(k - RTH_START)
    M = {"o": np.vstack(O), "c": np.vstack(C), "sp": np.vstack(SP)}
    return M, pd.DatetimeIndex(dates), stats, pd.Series(offs).value_counts().to_dict()


def run_us500(path, point, d_from, d_to, n, seed):
    M, dates, stats, offs = us500_matrix(path, point, d_from, d_to)
    rng = np.random.default_rng(seed)
    print(f"US500 M1 {dates[0].date()} to {dates[-1].date()}: days {stats['days']}, open found "
          f"{stats['open_found']}, valid sessions {stats['valid']}, opening offsets {offs}")
    _, lines = analyse_session(M, rng, n, US500_SLIP_BP)
    print("\n".join(lines))
    print("per year (share higher 1h / 2h / close):")
    for y in sorted(set(dates.year)):
        s = dates.year == y
        r1 = M["c"][s, 59] / M["o"][s, 0] - 1
        r2 = M["c"][s, 119] / M["o"][s, 0] - 1
        rc = M["c"][s, -1] / M["o"][s, 0] - 1
        print(f"  {y}: n={s.sum():>3}  {(r1 > 0).mean() * 100:5.1f}  {(r2 > 0).mean() * 100:5.1f}  {(rc > 0).mean() * 100:5.1f}")


def compare(spy_path, us_path, point, d_from, d_to):
    spy = load_spy(spy_path)
    M, dates, _, _ = us500_matrix(us_path, point, d_from, d_to)
    us = pd.Series(M["c"][:, -1] / M["o"][:, 0] - 1, index=dates)
    sp = (spy["close"] / spy["open"] - 1).reindex(us.index).dropna()
    us = us.reindex(sp.index)
    a, b = (sp > 0).mean() * 100, (us > 0).mean() * 100
    print(f"common days {len(sp)}: share higher at close SPY {a:.2f}%, US500 {b:.2f}%, "
          f"difference {b - a:+.2f} pp ({'report with C1 and C2' if abs(b - a) > 2 else 'within 2 pp'}), "
          f"same sign {(np.sign(sp) == np.sign(us)).mean() * 100:.1f}% of days")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--sets", type=int, default=24)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--spy")
    ap.add_argument("--us500")
    ap.add_argument("--compare", nargs=2)
    ap.add_argument("--point", type=float, default=0.01)
    ap.add_argument("--from", dest="d_from", default=None)
    ap.add_argument("--to", dest="d_to", default="2026-09-18")
    a = ap.parse_args()
    if a.noise:
        noise_check(a.sets, 7 if a.seed is None else a.seed, a.n)
    elif a.spy:
        run_spy(a.spy, a.d_from or "2011-09-19", a.d_to)
    elif a.us500:
        run_us500(a.us500, a.point, a.d_from or "2017-03-22", a.d_to, a.n, 29 if a.seed is None else a.seed)
    elif a.compare:
        compare(a.compare[0], a.compare[1], a.point, a.d_from or "2017-03-22", a.d_to)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
