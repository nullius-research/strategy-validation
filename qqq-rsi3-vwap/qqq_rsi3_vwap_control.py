#!/usr/bin/env python3
"""
Nullius Research, test T: RSI(3) + EMA(100) + rolling VWAP(10) on QQQ, against two control groups.
Hypothesis: hypothese-qqq-rsi3-vwap.md v1.1 (v1.0 approved 28 Nov 2026, K1-K5 all A; v1.1 Null B as a sequential process). Nothing in here may change after the first real run.

Rule (long only, daily bars):
  signal    on the close of day t: RSI3(t) < 22 and EMA100(t) > EMA100(t-5) and close(t) <= 0.99 * VWAP10(t)
  entry     open of day t+1
  exit      close of the first check day with RSI3 > 55 (a level, not a cross); first check day = entry day + 1 (K2 A)
            no stop, no target, no time limit; a trade still open at the end of the period is closed on its last close and flagged
  one position at a time; a signal during an open trade is dropped; a signal on the exit day itself counts
RSI3:   Wilder RSI, period 3 (smoothing alpha 1/3) (K1 A); --rsi cutler for the sensitivity
EMA100: alpha 2/101, seeded with the simple mean of the first 100 closes
VWAP10: sum(TP * volume) / sum(volume) over the last 10 days up to and including t, TP = (high + low + close) / 3
Warm-up: signals from the first day on which EMA100(t-5) exists (index 104, trading day 105)
Costs: round trip in basis points, subtracted from each trade's return (open to close).

Controls (same number of trades, one position at a time, entry at the next open after a random signal day):
  Null A (decisive for C5): signal days drawn from days with EMA100(t) > EMA100(t-5) (K3 A); each fake trade gets
                            the duration of a real trade (real durations, shuffled)
  Null B (decisive for C6, v1.1): a sequential process over the days with RSI3 < 22 only: each such day becomes a fake
                            signal with probability p (p set so the mean number of trades equals the rule's), then
                            the rule's own handling and exit. v1.0 (greedy random draw) failed the noise check:
                            it favoured short, winning trades.

Usage:
  python qqq_rsi3_vwap_control.py prices.csv [--start 1999-03-10] [--end 2026-09-30] [--col close|adjclose]
         [--rsi wilder|cutler] [--first-check 1|0] [--cost-bps 2] [--runs 10000] [--seed 38] [--trades out.csv]
  python qqq_rsi3_vwap_control.py --selftest
  python qqq_rsi3_vwap_control.py --synthetic 24          (random walks, check before real data; seed 7)
CSV columns: date,open,high,low,close,adjclose,volume (date as YYYY-MM-DD).
"""
import argparse, csv
import numpy as np

WARMUP = 104
N_RSI, RSI_IN, RSI_OUT = 3, 22.0, 55.0
N_EMA, EMA_LAG = 100, 5
N_VWAP, VWAP_DISC = 10, 0.99


def load(path, col="close"):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if any(row.get(k) in (None, "", "null", "None") for k in ("open", "high", "low", "close", "volume", col)):
                continue
            rows.append(row)
    d = np.array([r["date"][:10] for r in rows])
    o, h, l, c = (np.array([float(r[k]) for r in rows]) for k in ("open", "high", "low", "close"))
    v = np.array([float(r["volume"]) for r in rows])
    if col != "close":
        f = np.array([float(r[col]) for r in rows]) / c
        o, h, l, c = o * f, h * f, l * f, c * f
    return d, o, h, l, c, v


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


def rsi_cutler(c, n=N_RSI):
    delta = np.diff(c, prepend=np.nan)
    up = np.where(delta > 0, delta, 0.0); dn = np.where(delta < 0, -delta, 0.0)
    r = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        au = up[i - n + 1:i + 1].mean(); ad = dn[i - n + 1:i + 1].mean()
        r[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return r


def ema(c, n=N_EMA):
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    a = 2.0 / (n + 1); out[n - 1] = c[:n].mean()
    for i in range(n, len(c)):
        out[i] = a * c[i] + (1 - a) * out[i - 1]
    return out


def vwap(h, l, c, v, n=N_VWAP):
    tpv = np.cumsum(np.insert((h + l + c) / 3 * v, 0, 0.0)); vv = np.cumsum(np.insert(v, 0, 0.0))
    out = np.full(len(c), np.nan)
    num = tpv[n:] - tpv[:-n]; den = vv[n:] - vv[:-n]
    out[n - 1:] = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
    return out


def indicators(h, l, c, v, kind="wilder"):
    rsi = rsi_wilder(c) if kind == "wilder" else rsi_cutler(c)
    e = ema(c)
    trend = np.zeros(len(c), bool); trend[EMA_LAG:] = e[EMA_LAG:] > e[:-EMA_LAG]
    vw = vwap(h, l, c, v)
    disc = np.zeros(len(c), bool); ok = ~np.isnan(vw); disc[ok] = c[ok] <= VWAP_DISC * vw[ok]
    low_rsi = np.zeros(len(c), bool); okr = ~np.isnan(rsi); low_rsi[okr] = rsi[okr] < RSI_IN
    return dict(rsi=rsi, trend=trend, disc=disc, low_rsi=low_rsi, sig=low_rsi & trend & disc, ema=e, vwap=vw)


def find_exit(rsi, e, hi, first_check=1):
    """First day k >= e + first_check with rsi[k] > 55, within the period; else hi (open trade)."""
    k = e + first_check
    while k <= hi and not rsi[k] > RSI_OUT:
        k += 1
    return (k, False) if k <= hi else (hi, True)


def rule_trades(ind, lo, hi, first_check=1):
    sig, rsi = ind["sig"], ind["rsi"]
    tr, skipped, i = [], 0, max(lo, WARMUP)
    while i <= hi - 1:
        if sig[i]:
            e = i + 1; j, open_ = find_exit(rsi, e, hi, first_check)
            tr.append((e, j, open_))
            skipped += int(sig[e:j].sum())          # signals strictly inside the trade (the exit day itself counts)
            i = j                                   # j > i always, so the loop advances
        else:
            i += 1
    return tr, skipped


def rets(o, c, tr, cost):
    return np.array([c[j] / o[e] - 1 - cost for e, j, _ in tr])


def low_excursion(o, l, tr):
    return np.array([min(0.0, l[e:j + 1].min() / o[e] - 1) for e, j, _ in tr])


def dd_100k(r):
    eq = np.concatenate([[0.0], np.cumsum(r * 100000)])
    return float(np.max(np.maximum.accumulate(eq) - eq))


def random_trades_dur(pool, durs, hi, rng, n_days):
    """Null A: greedy random non-overlapping trades; signal day s, entry s+1, exit entry + duration."""
    dq = list(rng.permutation(durs)); taken, busy = [], np.zeros(n_days, bool)
    for s in rng.permutation(pool):
        if not dq:
            break
        e = s + 1; j = e + dq[0]
        if j > hi or busy[e:j + 1].any():
            continue
        busy[e:j + 1] = True; taken.append((e, j, False)); dq.pop(0)
    return taken


def seq_trades(pool_mask, rsi, lo, hi, prob, rng, first_check=1):
    """Null B (v1.1): a sequential process like the rule itself. Each day in the pool becomes a fake signal with
    probability prob; then the rule's own handling (entry next open, own exit, one position, signals inside a trade dropped)."""
    sel = pool_mask & (rng.random(len(rsi)) < prob)
    tr, i = [], max(lo, WARMUP)
    while i <= hi - 1:
        if sel[i]:
            e = i + 1; j, open_ = find_exit(rsi, e, hi, first_check); tr.append((e, j, open_)); i = j
        else:
            i += 1
    return tr


def calibrate(pool_mask, rsi, lo, hi, n, rng, first_check=1):
    """Probability at which the sequential process gives on average n trades (bisection, 40 runs per step)."""
    a, b = 0.0, 1.0
    for _ in range(18):
        m = (a + b) / 2
        k = np.mean([len(seq_trades(pool_mask, rsi, lo, hi, m, rng, first_check)) for _ in range(40)])
        a, b = (m, b) if k < n else (a, m)
    return (a + b) / 2


def null_means(kind, o, c, ind, pool, n, durs, lo, hi, cost, runs, rng, first_check=1):
    """Null A: returns (means, runs with fewer trades). Null B: returns (means, mean number of trades)."""
    m = np.empty(runs); short = 0; counts = []
    if kind == "B":
        prob = calibrate(pool, ind["rsi"], lo, hi, n, rng, first_check)
    for k in range(runs):
        if kind == "A":
            t = random_trades_dur(pool, durs, hi, rng, len(c)); short += len(t) < n
        else:
            t = seq_trades(pool, ind["rsi"], lo, hi, prob, rng, first_check); counts.append(len(t))
        m[k] = rets(o, c, t, cost).mean() if t else np.nan
    return m, (short if kind == "A" else float(np.mean(counts)))


def pct(x, dist):
    dist = dist[~np.isnan(dist)]
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


def funnel(ind, lo, hi):
    days = np.arange(max(lo, WARMUP), hi)
    a = ind["low_rsi"][days]; b = a & ind["trend"][days]; s = b & ind["disc"][days]
    return dict(days=len(days), rsi_below_22=int(a.sum()), plus_ema=int(b.sum()), plus_vwap_signals=int(s.sum()))


def evaluate(o, h, l, c, v, lo, hi, cost, runs, rng, kind="wilder", first_check=1, with_nulls=True):
    ind = indicators(h, l, c, v, kind)
    tr, skipped = rule_trades(ind, lo, hi, first_check)
    n = len(tr)
    if n == 0:
        return None
    r = rets(o, c, tr, cost); g = rets(o, c, tr, 0.0)
    durs = np.array([j - e for e, j, _ in tr])
    res = dict(n=n, skipped=skipped, win=int((r > 0).sum()), wr=(r > 0).mean(), wr_gross=(g > 0).mean(),
               mean=r.mean(), pf=pf(r), pf_gross=pf(g), dd=dd_100k(r), trades=tr, r=r, durs=durs, ind=ind,
               funnel=funnel(ind, lo, hi), open_end=sum(1 for t in tr if t[2]))
    res["wr_ci"] = wilson(res["win"], n)
    res["mean_ci"], res["pf_ci"] = boot(r, rng)
    if with_nulls:
        days = np.arange(max(lo, WARMUP), hi)
        poolA = days[ind["trend"][days]]
        poolB = ind["low_rsi"].copy(); poolB[:max(lo, WARMUP)] = False; poolB[hi:] = False
        mA, sA = null_means("A", o, c, ind, poolA, n, durs, lo, hi, cost, runs, rng, first_check)
        mB, sB = null_means("B", o, c, ind, poolB, n, durs, lo, hi, cost, runs, rng, first_check)
        res.update(pctA=pct(r.mean(), mA), nullA=np.nanpercentile(mA, [5, 50, 95]), shortA=sA,
                   pctB=pct(r.mean(), mB), nullB=np.nanpercentile(mB, [5, 50, 95]), shortB=sB)
    return res


def fake_market(rng, ndays, mu=0.0004, sig=0.018):
    c = 100 * np.exp(np.cumsum(rng.normal(mu - sig * sig / 2, sig, ndays)))
    prev = np.concatenate([[100.0], c[:-1]])
    o = prev * (1 + rng.normal(0, 0.004, ndays))
    hi_ = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.006, ndays)))
    lo_ = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.006, ndays)))
    v = np.exp(rng.normal(17, 0.5, ndays))
    return o, hi_, lo_, c, v


def synthetic(nsets, runs, seed):
    rng = np.random.default_rng(seed)
    ndays = 6950
    pa, pb, wr, nn = [], [], [], []
    for k in range(nsets):
        o, h, l, c, v = fake_market(rng, ndays)
        res = evaluate(o, h, l, c, v, 0, ndays - 1, 0.0002, runs, rng)
        pa.append(res["pctA"]); pb.append(res["pctB"]); wr.append(res["wr"]); nn.append(res["n"])
        print(f"set {k+1:2d}: trades {res['n']:4d}  win {100*res['wr']:5.1f}%  PF {res['pf']:5.2f}  mean {100*res['mean']:+.3f}%  "
              f"NullA med {100*res['nullA'][1]:+.3f}%  pctA {res['pctA']:5.1f}  NullB med {100*res['nullB'][1]:+.3f}%  pctB {res['pctB']:5.1f}")
    pa, pb = np.array(pa), np.array(pb)
    print(f"\nmean trades {np.mean(nn):.0f}  mean win rate {100*np.mean(wr):.1f}% (range {100*min(wr):.1f}-{100*max(wr):.1f})")
    print(f"pctA mean {pa.mean():.1f}  above 95: {np.sum(pa > 95)} of {nsets}   (threshold: mean 35-65, at most 3 above 95)")
    print(f"pctB mean {pb.mean():.1f}  above 95: {np.sum(pb > 95)} of {nsets}   (same threshold)")
    ok = all(35 <= x.mean() <= 65 and np.sum(x > 95) <= 3 for x in (pa, pb))
    print("NOISE CHECK", "PASSED" if ok else "FAILED")


def selftest():
    rng = np.random.default_rng(1)
    c = 100 + np.cumsum(rng.normal(0, 1, 400))
    # EMA: compare with an independent recursion written differently
    e = ema(c); a = 2 / 101; ref = c[:100].mean()
    for i in range(100, 400):
        ref = ref + a * (c[i] - ref)
    assert abs(e[-1] - ref) < 1e-9, "EMA"
    # Wilder RSI: compare with exponential form, alpha 1/3, seeded with the first 3-day mean
    d = np.diff(c); up = np.clip(d, 0, None); dn = np.clip(-d, 0, None)
    au, ad = up[:3].mean(), dn[:3].mean()
    for x, y in zip(up[3:], dn[3:]):
        au += (x - au) / 3; ad += (y - ad) / 3
    assert abs(rsi_wilder(c)[-1] - (100 - 100 / (1 + au / ad))) < 1e-9, "RSI Wilder"
    # Cutler RSI on a known series: gains 1,1, loss 2 over the last three days -> 100 - 100/(1+ (2/3)/(2/3)) = 50
    assert abs(rsi_cutler(np.array([10, 11, 12, 10.0]))[-1] - 50) < 1e-9, "RSI Cutler"
    # VWAP: constant price -> VWAP equals price; volume weighting on a hand case
    h = l = cc = np.full(20, 50.0); v = np.arange(1, 21, dtype=float)
    assert np.allclose(vwap(h, l, cc, v)[9:], 50), "VWAP constant"
    h2 = np.array([12.0] * 9 + [24.0]); l2 = np.array([6.0] * 9 + [12.0]); c2 = np.array([9.0] * 9 + [18.0]); v2 = np.array([1.0] * 9 + [9.0])
    assert abs(vwap(h2, l2, c2, v2)[9] - (9 * 9 + 18 * 9) / 18) < 1e-9, "VWAP weights"
    # Exit: RSI above 55 on the entry day must NOT exit (first check = entry + 1)
    rsi = np.array([10, 60, 40, 60, 40.0])
    assert find_exit(rsi, 1, 4, 1) == (3, False) and find_exit(rsi, 1, 4, 0) == (1, False), "exit day"
    assert find_exit(np.array([10, 10, 10.0]), 1, 2, 1) == (2, True), "open trade"
    # Rule trades: a signal on the exit day counts, a signal inside the trade is dropped
    n = 12
    sig = np.zeros(n, bool); sig[[2, 3, 6]] = True; rsi = np.full(n, 30.0); rsi[6] = 60; rsi[9] = 60
    global WARMUP
    w = WARMUP; WARMUP = 0
    tr, sk = rule_trades(dict(sig=sig, rsi=rsi), 0, n - 1, 1)
    WARMUP = w
    assert tr == [(3, 6, False), (7, 9, False)] and sk == 1, f"rule trades {tr} {sk}"
    print("SELFTEST PASSED")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--start", default="1999-03-10"); ap.add_argument("--end", default=None)
    ap.add_argument("--col", default="close"); ap.add_argument("--rsi", default="wilder")
    ap.add_argument("--first-check", type=int, default=1)
    ap.add_argument("--cost-bps", type=float, default=2.0); ap.add_argument("--runs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=38); ap.add_argument("--synthetic", type=int, default=0)
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--trades", default=None)
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    if a.synthetic:
        synthetic(a.synthetic, min(a.runs, 2000), 7 if a.seed == 38 else a.seed); return
    d, o, h, l, c, v = load(a.csv, a.col)
    lo = int(np.searchsorted(d, a.start)); hi = len(d) - 1 if a.end is None else int(np.searchsorted(d, a.end, side="right")) - 1
    rng = np.random.default_rng(a.seed)
    res = evaluate(o, h, l, c, v, lo, hi, a.cost_bps / 1e4, a.runs, rng, a.rsi, a.first_check)
    print(f"data {d[0]} to {d[-1]} ({len(d)} days, {a.col}); period {d[lo]} to {d[hi]}; signals from {d[max(lo, WARMUP)]}; "
          f"RSI {a.rsi}; first check entry+{a.first_check}; costs {a.cost_bps} bp; runs {a.runs}; seed {a.seed}")
    if res is None:
        print("no trades"); return
    f = res["funnel"]
    print(f"funnel: days {f['days']}  RSI3<22 {f['rsi_below_22']}  +EMA {f['plus_ema']}  +VWAP (signals) {f['plus_vwap_signals']}  "
          f"dropped in trade {res['skipped']}  trades {res['n']}  open at end {res['open_end']}")
    print(f"win rate {100*res['wr']:.1f}% ({100*res['wr_ci'][0]:.1f}-{100*res['wr_ci'][1]:.1f}), gross {100*res['wr_gross']:.1f}%")
    print(f"mean net {100*res['mean']:+.3f}% ({100*res['mean_ci'][0]:+.3f} to {100*res['mean_ci'][1]:+.3f})")
    print(f"PF net {res['pf']:.2f} ({res['pf_ci'][0]:.2f}-{res['pf_ci'][1]:.2f}), gross {res['pf_gross']:.2f}")
    le = low_excursion(o, l, res["trades"])
    print(f"worst trade {100*res['r'].min():+.2f}%  lowest daily low {100*le.min():+.2f}%  mean duration {res['durs'].mean():.2f} days  "
          f"time in market {100*(res['durs'].sum()+len(res['durs']))/max(1, f['days']):.1f}%  drawdown at $100k {res['dd']:,.0f}")
    print(f"buy and hold {d[lo]} to {d[hi]}: {100*(c[hi]/c[lo]-1):+.1f}%")
    print(f"Null A 5/50/95: {100*res['nullA'][0]:+.3f} / {100*res['nullA'][1]:+.3f} / {100*res['nullA'][2]:+.3f}%  -> percentile {res['pctA']:.1f}  (runs with fewer trades: {res['shortA']})")
    print(f"Null B 5/50/95: {100*res['nullB'][0]:+.3f} / {100*res['nullB'][1]:+.3f} / {100*res['nullB'][2]:+.3f}%  -> percentile {res['pctB']:.1f}  (mean trades per run: {res['shortB']:.1f})")
    if a.trades:
        with open(a.trades, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["entry_date", "entry_open", "exit_date", "exit_close", "days", "net_return", "open_at_end"])
            for (e, j, op), r in zip(res["trades"], res["r"]):
                w.writerow([d[e], f"{o[e]:.4f}", d[j], f"{c[j]:.4f}", j - e, f"{r:.6f}", int(op)])


if __name__ == "__main__":
    main()
