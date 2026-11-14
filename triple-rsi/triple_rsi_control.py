#!/usr/bin/env python3
"""
Nullius Research, test I: Triple RSI on SPY, against a control group.
Hypothesis: hypothese-triple-rsi.md v1.0 (approved 14 Nov 2026). Nothing in here may change after the first real run.

Rule (long only, daily closes):
  signal    RSI5(t) < 30 and RSI5(t) < RSI5(t-1) < RSI5(t-2) < RSI5(t-3) and RSI5(t-3) < 60 and close(t) > SMA200(t)
  entry     close of day t
  exit      close of the first later day on which RSI5 crosses above 50 (RSI5 of the day before <= 50, RSI5 of that day > 50)
            no stop, no target, no time limit; a trade still open at the end is closed on the last close and flagged
  one position at a time; a new signal during an open trade is ignored
RSI5: Wilder RSI, period 5 (smoothing alpha 1/5). SMA200: simple mean of the last 200 closes. First 250 days: warm-up.
Costs: round trip in basis points, subtracted from each trade's return.

Controls (same number of trades, one position at a time, entry days among days with close > SMA200):
  Null A (decisive):   each fake trade gets the duration of a real trade (real durations, shuffled)
  Null B (supplementary): the rule's own exit (RSI5 crosses above 50)

Usage:
  python triple_rsi_control.py prices.csv --start 1993-01-29 [--end 2026-02-20] [--col close] [--cost-bps 2] [--runs 10000] [--seed 37]
  python triple_rsi_control.py --synthetic 24          (random walks, check before real data; seed 7)
CSV needs columns date,close (date as YYYY-MM-DD); --col adjclose uses that column instead.
"""
import argparse, csv
import numpy as np

WARMUP = 250
N_RSI = 5


def load(path, col="close"):
    d, c = [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get(col) in (None, "", "null", "None"):
                continue
            d.append(row["date"][:10]); c.append(float(row[col]))
    return np.array(d), np.array(c)


def rsi_wilder(c, n=N_RSI):
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


def cross_exit(rsi, i):
    """First day j > i with rsi[j-1] <= 50 and rsi[j] > 50, or the last day (open trade)."""
    j = i + 1
    while j < len(rsi) and not (rsi[j - 1] <= 50 and rsi[j] > 50):
        j += 1
    return (j, False) if j < len(rsi) else (len(rsi) - 1, True)


def signal(c, rsi, ma, i):
    return (rsi[i] < 30 and rsi[i] < rsi[i - 1] < rsi[i - 2] < rsi[i - 3] and rsi[i - 3] < 60 and c[i] > ma[i])


def funnel(c, rsi, ma, lo, hi):
    f = dict(days=0, above_ma=0, rsi_below_30=0, three_declines=0, rsi_t3_below_60=0)
    for i in range(max(lo, WARMUP), hi + 1):
        f["days"] += 1
        if not c[i] > ma[i]:
            continue
        f["above_ma"] += 1
        if not rsi[i] < 30:
            continue
        f["rsi_below_30"] += 1
        if not rsi[i] < rsi[i - 1] < rsi[i - 2] < rsi[i - 3]:
            continue
        f["three_declines"] += 1
        if rsi[i - 3] < 60:
            f["rsi_t3_below_60"] += 1
    return f


def rule_trades(c, rsi, ma, lo, hi):
    tr, i, skipped = [], max(lo, WARMUP), 0
    while i <= hi:
        if signal(c, rsi, ma, i):
            j, open_ = cross_exit(rsi, i)
            tr.append((i, j, open_))
            skipped += sum(1 for k in range(i + 1, min(j, hi) + 1) if signal(c, rsi, ma, k))
            i = j + 1
        else:
            i += 1
    return tr, skipped


def rets(c, tr, cost):
    return np.array([c[j] / c[i] - 1 - cost for i, j, _ in tr])


def mae(c, tr):
    """Deepest close-to-close drawdown from entry while the trade was open."""
    return np.array([min(0.0, c[i + 1:j + 1].min() / c[i] - 1) if j > i else 0.0 for i, j, _ in tr])


def random_trades_exit(c, rsi, eligible, n, rng):
    """Null B: greedy random non-overlapping trades with the rule's own exit."""
    taken, busy = [], np.zeros(len(c), bool)
    for i in rng.permutation(eligible):
        if busy[i]:
            continue
        j, open_ = cross_exit(rsi, i)
        if busy[i:j + 1].any():
            continue
        busy[i:j + 1] = True; taken.append((i, j, open_))
        if len(taken) == n:
            break
    return taken


def random_trades_dur(c, eligible, durs, rng):
    """Null A: greedy random non-overlapping trades, each with the next duration from the shuffled real durations."""
    dq = list(rng.permutation(durs)); taken, busy = [], np.zeros(len(c), bool); last = len(c) - 1
    for i in rng.permutation(eligible):
        if not dq:
            break
        dd = dq[0]; j = i + dd
        if j > last or busy[i:j + 1].any():
            continue
        busy[i:j + 1] = True; taken.append((i, j, False)); dq.pop(0)
    return taken


def null_means(kind, c, rsi, eligible, n, durs, cost, runs, rng):
    m = np.empty(runs); short = 0
    for k in range(runs):
        t = random_trades_dur(c, eligible, durs, rng) if kind == "A" else random_trades_exit(c, rsi, eligible, n, rng)
        short += len(t) < n
        m[k] = rets(c, t, cost).mean()
    return m, short


def pct(x, dist):
    return 100.0 * (np.sum(dist < x) + 0.5 * np.sum(dist == x)) / len(dist)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; m = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return m - h, m + h


def pf(r):
    return r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else np.inf


def boot(r, rng, B=10000):
    idx = rng.integers(0, len(r), (B, len(r)))
    s = r[idx]
    m = s.mean(1)
    pos = np.where(s > 0, s, 0).sum(1); neg = -np.where(s < 0, s, 0).sum(1)
    p = np.where(neg > 0, pos / np.where(neg > 0, neg, 1), np.inf)
    return (np.percentile(m, 2.5), np.percentile(m, 97.5)), (np.percentile(p, 2.5), np.percentile(p, 97.5))


def evaluate(c, lo, hi, cost, runs, rng, with_b=True):
    rsi, ma = rsi_wilder(c), sma(c)
    tr, skipped = rule_trades(c, rsi, ma, lo, hi)
    n = len(tr)
    if n == 0:
        return None
    r = rets(c, tr, cost); g = rets(c, tr, 0.0)
    durs = np.array([j - i for i, j, _ in tr])
    days = np.arange(max(lo, WARMUP), hi + 1)
    el = days[c[days] > ma[days]]
    mA, sA = null_means("A", c, rsi, el, n, durs, cost, runs, rng)
    o = dict(n=n, skipped=skipped, win=int((r > 0).sum()), wr=(r > 0).mean(), wr_gross=(g > 0).mean(), mean=r.mean(), pf=pf(r),
             pctA=pct(r.mean(), mA), nullA=np.percentile(mA, [5, 50, 95]), shortA=sA, trades=tr, r=r, durs=durs, rsi=rsi, ma=ma)
    o["wr_ci"] = wilson(o["win"], n)
    o["mean_ci"], o["pf_ci"] = boot(r, rng)
    if with_b:
        mB, sB = null_means("B", c, rsi, el, n, durs, cost, runs, rng)
        o.update(pctB=pct(r.mean(), mB), nullB=np.percentile(mB, [5, 50, 95]), shortB=sB)
    return o


def synthetic(nsets, runs, seed):
    rng = np.random.default_rng(seed)
    mu, sig, ndays = 0.0003, 0.012, 8400
    pa, pb, wr, nn = [], [], [], []
    for k in range(nsets):
        c = 100 * np.exp(np.cumsum(rng.normal(mu - sig * sig / 2, sig, ndays)))
        o = evaluate(c, WARMUP, ndays - 1, 0.0002, runs, rng)
        pa.append(o["pctA"]); pb.append(o["pctB"]); wr.append(o["wr"]); nn.append(o["n"])
        print(f"set {k+1:2d}: trades {o['n']:4d}  win {100*o['wr']:5.1f}%  mean {100*o['mean']:+.3f}%  "
              f"NullA median {100*o['nullA'][1]:+.3f}%  pctA {o['pctA']:5.1f}  pctB {o['pctB']:5.1f}")
    pa, pb = np.array(pa), np.array(pb)
    print(f"\nmean trades {np.mean(nn):.0f}  mean win rate {100*np.mean(wr):.1f}% (range {100*min(wr):.1f}-{100*max(wr):.1f})")
    print(f"pctA mean {pa.mean():.1f}  above 95: {np.sum(pa > 95)} of {nsets}   (threshold: mean 35-65, at most 3 above 95)")
    print(f"pctB mean {pb.mean():.1f}  above 95: {np.sum(pb > 95)} of {nsets}")
    ok = 35 <= pa.mean() <= 65 and np.sum(pa > 95) <= 3
    print("NOISE CHECK", "PASSED" if ok else "FAILED")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--start"); ap.add_argument("--end")
    ap.add_argument("--col", default="close")
    ap.add_argument("--cost-bps", type=float, default=2.0)
    ap.add_argument("--runs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=37)
    ap.add_argument("--synthetic", type=int, default=0)
    ap.add_argument("--trades-out")
    a = ap.parse_args()
    if a.synthetic:
        synthetic(a.synthetic, min(a.runs, 2000), 7 if a.seed == 37 else a.seed); return
    d, c = load(a.csv, a.col)
    lo = int(np.searchsorted(d, a.start)) if a.start else 0
    hi = int(np.searchsorted(d, a.end, side="right")) - 1 if a.end else len(d) - 1
    rng = np.random.default_rng(a.seed)
    print(f"data {d[0]} to {d[-1]} ({len(d)} days, column {a.col}); entries {d[max(lo,WARMUP)]} to {d[hi]}; costs {a.cost_bps} bp; runs {a.runs}; seed {a.seed}")
    for mult in (1, 0, 2):
        cost = a.cost_bps * mult / 1e4
        o = evaluate(c, lo, hi, cost, a.runs if mult == 1 else min(a.runs, 2000), rng)
        if o is None:
            print("no trades"); return
        print(f"\n== costs {a.cost_bps*mult:.0f} bp ==")
        print(f"trades {o['n']}  wins {o['win']}  win rate {100*o['wr']:.2f}% (95% {100*o['wr_ci'][0]:.1f}-{100*o['wr_ci'][1]:.1f})  gross win rate {100*o['wr_gross']:.2f}%")
        print(f"mean net return per trade {100*o['mean']:+.3f}% (95% {100*o['mean_ci'][0]:+.3f} to {100*o['mean_ci'][1]:+.3f})")
        print(f"profit factor {o['pf']:.2f} (95% {o['pf_ci'][0]:.2f} to {o['pf_ci'][1]:.2f})")
        print(f"Null A 5/50/95: {100*o['nullA'][0]:+.3f} / {100*o['nullA'][1]:+.3f} / {100*o['nullA'][2]:+.3f}%  -> percentile {o['pctA']:.1f}  (runs with fewer trades: {o['shortA']})")
        print(f"Null B 5/50/95: {100*o['nullB'][0]:+.3f} / {100*o['nullB'][1]:+.3f} / {100*o['nullB'][2]:+.3f}%  -> percentile {o['pctB']:.1f}  (runs with fewer trades: {o['shortB']})")
        if mult == 1:
            tr, r, durs = o["trades"], o["r"], o["durs"]
            m = mae(c, tr)
            f = funnel(c, o["rsi"], o["ma"], lo, hi)
            print("funnel: " + "  ".join(f"{k} {v}" for k, v in f.items()) + f"  ignored during open trade {o['skipped']}  trades {o['n']}")
            top = np.sort(r)[::-1][:max(1, int(round(0.05 * len(r))))]
            s0 = max(lo, WARMUP); dend = max(hi, tr[-1][1])
            print(f"holding days mean {durs.mean():.1f}  median {np.median(durs):.0f}  max {durs.max()}  days in market {durs.sum()} of {dend - s0}")
            print(f"worst trade {100*r.min():+.2f}%  deepest drawdown in a trade {100*m.min():+.2f}%  last trade open at end: {tr[-1][2]}")
            print(f"sum of all {100*r.sum():+.1f}%  sum of best 5% ({len(top)}) {100*top.sum():+.1f}%")
            print(f"rule compounded {100*(np.prod(1+r)-1):+.1f}% (100,000 -> {100000*np.prod(1+r):,.0f})  buy and hold {d[s0]} to {d[dend]} {100*(c[dend]/c[s0]-1):+.1f}%")
            dec = {}
            for (i, j, _), x in zip(tr, r):
                dec.setdefault(d[i][:3] + "0s", []).append(x)
            print("decade  trades  win%   mean%")
            for y in sorted(dec):
                v = np.array(dec[y]); print(f"{y}  {len(v):6d}  {100*(v>0).mean():5.1f}  {100*v.mean():+.3f}" + ("  (insufficient, <100)" if len(v) < 100 else ""))
            if a.trades_out:
                with open(a.trades_out, "w", newline="") as fh:
                    w = csv.writer(fh); w.writerow(["entry_date", "exit_date", "days", "entry_close", "exit_close", "rsi5_entry", "rsi5_exit", "net_return", "max_drawdown", "open_at_end"])
                    for (i, j, op), x, mm in zip(tr, r, m):
                        w.writerow([d[i], d[j], j - i, f"{c[i]:.4f}", f"{c[j]:.4f}", f"{o['rsi'][i]:.2f}", f"{o['rsi'][j]:.2f}", f"{x:.6f}", f"{mm:.6f}", op])


if __name__ == "__main__":
    main()
