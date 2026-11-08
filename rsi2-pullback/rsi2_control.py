#!/usr/bin/env python3
"""
Nullius Research, test E: RSI(2) pullback on a stock index, against a control group.
Hypothesis: hypothese-rsi2-pullback.md v1.0 (approved 8 Nov 2026). Nothing in here may change after the first real run.

Rule (long only, daily closes):
  filter    close(t) > SMA200(t)
  signal    RSI2(t-2) < 65 and RSI2(t-1) < RSI2(t-2) and RSI2(t) < RSI2(t-1)
  entry     close of day t
  exit      close of the first later day with RSI2 > 75 (no stop, no time limit)
  one position at a time; a trade still open at the end is closed on the last close and flagged
RSI2: Wilder RSI, period 2 (smoothing alpha 1/2). SMA200: simple mean of the last 200 closes.
Costs: round trip in basis points, subtracted from each trade's return.

Controls (same number of trades, same exit rule, one position at a time):
  Null A (decisive): random entry days among days with close > SMA200
  Null B (context):  random entry days, no filter

Usage:
  python rsi2_control.py prices.csv --start 2007-01-01 [--end 2026-12-31] [--cost-bps 2] [--runs 10000] [--seed 23]
  python rsi2_control.py --synthetic 24          (random walks, check before real data)
CSV needs columns date,close (date as YYYY-MM-DD).
"""
import argparse, csv, sys
import numpy as np

WARMUP = 250


def load(path):
    d, c = [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["close"] in ("", "null", "None"):
                continue
            d.append(row["date"][:10]); c.append(float(row["close"]))
    return np.array(d), np.array(c)


def rsi_wilder(c, n=2):
    delta = np.diff(c, prepend=np.nan)
    up = np.where(delta > 0, delta, 0.0); dn = np.where(delta < 0, -delta, 0.0)
    r = np.full(len(c), np.nan)
    if len(c) <= n:
        return r
    au = up[1:n + 1].mean(); ad = dn[1:n + 1].mean()
    for i in range(n, len(c)):
        if i > n:
            au = (au * (n - 1) + up[i]) / n; ad = (ad * (n - 1) + dn[i]) / n
        r[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return r


def sma(c, n=200):
    out = np.full(len(c), np.nan)
    cs = np.cumsum(np.insert(c, 0, 0.0))
    out[n - 1:] = (cs[n:] - cs[:-n]) / n
    return out


def exit_index(rsi, i):
    """First day after i with RSI2 > 75, or the last day (open trade)."""
    j = i + 1
    while j < len(rsi) and not rsi[j] > 75:
        j += 1
    return (j, False) if j < len(rsi) else (len(rsi) - 1, True)


def rule_trades(c, rsi, ma, lo, hi):
    tr, i = [], max(lo, WARMUP)
    while i <= hi:
        if c[i] > ma[i] and rsi[i - 2] < 65 and rsi[i - 1] < rsi[i - 2] and rsi[i] < rsi[i - 1]:
            j, open_ = exit_index(rsi, i)
            tr.append((i, j, open_)); i = j + 1
        else:
            i += 1
    return tr


def rets(c, tr, cost):
    return np.array([c[j] / c[i] - 1 - cost for i, j, _ in tr])


def mae(c, tr):
    """Deepest close-to-close drawdown from entry while the trade was open."""
    return np.array([min(0.0, c[i + 1:j + 1].min() / c[i] - 1) if j > i else 0.0 for i, j, _ in tr])


def random_trades(c, rsi, eligible, n, rng):
    """Greedy random non-overlapping trades: shuffle eligible days, accept a day if its trade does not overlap."""
    taken, busy = [], np.zeros(len(c), bool)
    for i in rng.permutation(eligible):
        if busy[i]:
            continue
        j, open_ = exit_index(rsi, i)
        if busy[i:j + 1].any():
            continue
        busy[i:j + 1] = True; taken.append((i, j, open_))
        if len(taken) == n:
            break
    return taken


def null_means(c, rsi, eligible, n, cost, runs, rng):
    m = np.empty(runs); short = 0
    for k in range(runs):
        t = random_trades(c, rsi, eligible, n, rng)
        short += len(t) < n
        m[k] = rets(c, t, cost).mean()
    return m, short


def pct(x, dist):
    return 100.0 * (np.sum(dist < x) + 0.5 * np.sum(dist == x)) / len(dist)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; m = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return m - h, m + h


def boot_mean(r, rng, B=10000):
    idx = rng.integers(0, len(r), (B, len(r)))
    m = r[idx].mean(1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def evaluate(d, c, lo, hi, cost, runs, rng, verbose=True):
    rsi, ma = rsi_wilder(c), sma(c)
    tr = rule_trades(c, rsi, ma, lo, hi)
    n = len(tr)
    if n == 0:
        return None
    r = rets(c, tr, cost); g = rets(c, tr, 0.0)
    win = int((r > 0).sum()); wg = int((g > 0).sum())
    days = np.arange(max(lo, WARMUP), hi + 1)
    elA = days[c[days] > ma[days]]; elB = days
    mA, sA = null_means(c, rsi, elA, n, cost, runs, rng)
    mB, sB = null_means(c, rsi, elB, n, cost, runs, rng)
    out = dict(n=n, win=win, wr=win / n, wr_ci=wilson(win, n), wr_gross=wg / n, mean=r.mean(), mean_ci=boot_mean(r, rng),
               pf=r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else np.inf, pctA=pct(r.mean(), mA), pctB=pct(r.mean(), mB),
               nullA=(np.percentile(mA, 5), np.percentile(mA, 50), np.percentile(mA, 95)), nullB=(np.percentile(mB, 5), np.percentile(mB, 50), np.percentile(mB, 95)),
               shortA=sA, shortB=sB, open_last=tr[-1][2], trades=tr, r=r, mae=mae(c, tr))
    return out


def synthetic(nsets, runs, seed):
    rng = np.random.default_rng(seed)
    mu, sig, ndays = 0.07 / 252, 0.18 / np.sqrt(252), 252 * 21  # ~20 years after a 1-year warmup
    rows = []
    for k in range(nsets):
        lr = rng.normal(mu - sig * sig / 2, sig, ndays)
        c = 1000 * np.exp(np.cumsum(lr))
        d = np.array([str(i) for i in range(ndays)])
        o = evaluate(d, c, WARMUP, ndays - 1, 0.0002, runs, rng, False)
        rows.append(o)
        print(f"set {k+1:2d}: trades {o['n']:4d}  win {100*o['wr']:5.1f}%  mean {100*o['mean']:+.3f}%  "
              f"NullA median {100*o['nullA'][1]:+.3f}%  pctA {o['pctA']:5.1f}  pctB {o['pctB']:5.1f}")
    pa = np.array([o["pctA"] for o in rows]); wr = np.array([o["wr"] for o in rows]); n = np.array([o["n"] for o in rows])
    print(f"\nmean trades {n.mean():.0f}  mean win rate {100*wr.mean():.1f}% (range {100*wr.min():.1f}-{100*wr.max():.1f})")
    print(f"pctA mean {pa.mean():.1f} (uniform: 50)  above 95: {np.sum(pa > 95)} of {nsets} (expected about {0.05*nsets:.1f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--start"); ap.add_argument("--end")
    ap.add_argument("--cost-bps", type=float, default=2.0)
    ap.add_argument("--runs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--synthetic", type=int, default=0)
    ap.add_argument("--trades-out")
    a = ap.parse_args()
    if a.synthetic:
        synthetic(a.synthetic, min(a.runs, 2000), a.seed); return
    d, c = load(a.csv)
    lo = int(np.searchsorted(d, a.start)) if a.start else 0
    hi = int(np.searchsorted(d, a.end, side="right")) - 1 if a.end else len(d) - 1
    rng = np.random.default_rng(a.seed)
    print(f"data {d[0]} to {d[-1]} ({len(d)} days); period {d[lo]} to {d[hi]}; costs {a.cost_bps} bp; runs {a.runs}; seed {a.seed}")
    for mult in (0, 1, 2):
        cost = a.cost_bps * mult / 1e4
        o = evaluate(d, c, lo, hi, cost, a.runs if mult == 1 else min(a.runs, 2000), rng)
        if o is None:
            print("no trades"); return
        print(f"\n== costs {a.cost_bps*mult:.0f} bp ==")
        print(f"trades {o['n']}  wins {o['win']}  win rate {100*o['wr']:.2f}% (95% {100*o['wr_ci'][0]:.1f}-{100*o['wr_ci'][1]:.1f})  gross win rate {100*o['wr_gross']:.2f}%")
        print(f"mean net return per trade {100*o['mean']:+.3f}% (95% {100*o['mean_ci'][0]:+.3f} to {100*o['mean_ci'][1]:+.3f})  PF {o['pf']:.2f}")
        print(f"Null A 5/50/95: {100*o['nullA'][0]:+.3f} / {100*o['nullA'][1]:+.3f} / {100*o['nullA'][2]:+.3f}%  -> percentile {o['pctA']:.1f}  (runs with fewer trades: {o['shortA']})")
        print(f"Null B 5/50/95: {100*o['nullB'][0]:+.3f} / {100*o['nullB'][1]:+.3f} / {100*o['nullB'][2]:+.3f}%  -> percentile {o['pctB']:.1f}  (runs with fewer trades: {o['shortB']})")
        if mult == 1:
            tr, r, m = o["trades"], o["r"], o["mae"]
            dur = np.array([j - i for i, j, _ in tr])
            top = np.sort(r)[::-1][:max(1, int(round(0.05 * len(r))))]
            print(f"holding days mean {dur.mean():.1f}  max {dur.max()}  worst trade {100*r.min():+.2f}%  deepest drawdown in a trade {100*m.min():+.2f}%")
            print(f"sum of all {100*r.sum():+.1f}%  sum of best 5% ({len(top)}) {100*top.sum():+.1f}%  last trade open at end: {o['open_last']}")
            print(f"buy and hold same period {100*(c[hi]/c[max(lo,WARMUP)]-1):+.1f}%  rule compounded {100*(np.prod(1+r)-1):+.1f}%")
            yrs = {}
            for (i, j, _), x in zip(tr, r):
                yrs.setdefault(d[i][:4], []).append(x)
            print("year  trades  win%   mean%")
            for y in sorted(yrs):
                v = np.array(yrs[y]); print(f"{y}  {len(v):6d}  {100*(v>0).mean():5.1f}  {100*v.mean():+.3f}")
            if a.trades_out:
                with open(a.trades_out, "w", newline="") as f:
                    w = csv.writer(f); w.writerow(["entry_date", "exit_date", "days", "entry_close", "exit_close", "net_return", "max_drawdown", "open_at_end"])
                    for (i, j, op), x, mm in zip(tr, r, m):
                        w.writerow([d[i], d[j], j - i, f"{c[i]:.2f}", f"{c[j]:.2f}", f"{x:.6f}", f"{mm:.6f}", op])


if __name__ == "__main__":
    main()
