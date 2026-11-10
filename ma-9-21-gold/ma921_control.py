"""Test F: MA 9/21 crossover with 200 MA on gold (XAUUSD M30), long only.

Hypothesis v1.1 (9 Nov 2026), fixed before looking at price data. Only the control group differs from v1.0. Rules (all from the hypothesis document):
  daily filter   : previous completed broker day closed above its daily EMA 9
  signal at bar t: EMA9 crosses above EMA21 on bar t; low(t) > max(EMA9, EMA21);
                   close(t) > EMA200; EMA9 and EMA21 > EMA200; daily filter true
  entry          : close of bar t
  stop A         : lowest low of the last 10 M30 bars up to t; no trade if entry - stop < 1.00 USD
  target         : entry + 1.5 x (entry - stop)
  path           : bar by bar from t+1; stop and target in one bar = stop; a bar that opens beyond
                   the stop exits at its open, a bar that opens beyond the target exits at the target
  costs          : 0.40 USD per ounce round trip (sensitivity 0 and 0.80)
  one position at a time; a trade still open at the end is closed on the last close and flagged
Controls (v1.1, sequential): a random process that walks through time like the rule, one position at a time.
  After each exit, wait a number of bars drawn from the rule's own waiting times, then go long on the next
  allowed bar. Stop distance drawn from the rule's own stops (20 quantiles), 1.5R, same costs, same path rules.
  A wait never spans the excluded 2024-2025 period.
  Null A (decisive): allowed bars have the same trend context (daily filter, close, EMA9, EMA21 above EMA200)
  Null B           : all bars allowed
Usage: python ma921_control.py data.csv          real data, all periods
       python ma921_control.py --synthetic 24     noise check
"""
import sys
import numpy as np
import pandas as pd

COST, COSTS = 0.40, (0.0, 0.40, 0.80)
MIN_STOP, RR, LOOKBACK = 1.00, 1.5, 10
RUNS, SEED = 10000, 23
K = 20


def load(path):
    d = pd.read_csv(path, sep="\t")
    d.columns = [c.strip("<>").upper() for c in d.columns]
    d["TIME"] = pd.to_datetime(d["DATE"] + " " + d["TIME"], format="%Y.%m.%d %H:%M:%S")
    return d[["TIME", "OPEN", "HIGH", "LOW", "CLOSE", "SPREAD"]].sort_values("TIME").reset_index(drop=True)


def usable_start(d, min_bars=40):
    """First calendar month in which every trading day has at least min_bars M30 bars."""
    per_day = d.groupby(d["TIME"].dt.date).size()
    per_day.index = pd.to_datetime(per_day.index)
    ok = per_day.groupby(per_day.index.to_period("M")).min() >= min_bars
    return ok[ok].index[0].to_timestamp()


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def features(d):
    c = d["CLOSE"].to_numpy()
    e9, e21, e200 = ema(c, 9), ema(c, 21), ema(c, 200)
    date = d["TIME"].dt.normalize()
    daily = d.groupby(date)["CLOSE"].last()
    dfilt = (daily > pd.Series(ema(daily.to_numpy(), 9), index=daily.index)).shift(1)  # previous completed day
    day_ok = date.map(dfilt).fillna(False).to_numpy(bool)
    lo = d["LOW"].to_numpy()
    stop = pd.Series(lo).rolling(LOOKBACK).min().to_numpy()
    risk = c - stop
    context = day_ok & (c > e200) & (e9 > e200) & (e21 > e200)
    cross = (e9 > e21) & (np.roll(e9, 1) <= np.roll(e21, 1))
    cross[0] = False
    signal = context & cross & (lo > np.maximum(e9, e21))
    sized = np.nan_to_num(risk, nan=0) >= MIN_STOP
    return dict(c=c, signal=signal, context=context, risk=risk, stop=stop, sized=sized)


def outcomes(d, f, idx):
    """Simulate a long trade from each bar in idx. Returns exit bar, gross R before costs, exit price, open flag."""
    o, h, l, c = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE"))
    n = len(c)
    idx = np.asarray(idx)
    entry, stop = c[idx], f["stop"][idx]
    risk = entry - stop
    tgt = entry + RR * risk
    exit_i = np.full(len(idx), n - 1); exit_p = c[-1] * np.ones(len(idx)); open_ = np.ones(len(idx), bool)
    active = np.ones(len(idx), bool); k = 1
    while active.any():
        a = np.where(active)[0]
        j = idx[a] + k
        done_end = j >= n
        if done_end.any():
            active[a[done_end]] = False
        a, j = a[~done_end], j[~done_end]
        if len(a) == 0:
            break
        gap_s = o[j] <= stop[a]; gap_t = (o[j] >= tgt[a]) & ~gap_s
        hit_s = ~gap_s & ~gap_t & (l[j] <= stop[a]); hit_t = ~gap_s & ~gap_t & ~hit_s & (h[j] >= tgt[a])
        px = np.where(gap_s, o[j], np.where(gap_t | hit_t, tgt[a], stop[a]))
        fin = gap_s | gap_t | hit_s | hit_t
        exit_i[a[fin]] = j[fin]; exit_p[a[fin]] = px[fin]; open_[a[fin]] = False; active[a[fin]] = False
        k += 1
    return exit_i, (exit_p - entry) / risk, risk, open_


def rule_trades(sig_idx, exit_of):
    taken, free_from = [], -1
    for i in sig_idx:
        if i > free_from:
            taken.append(i); free_from = exit_of[i]
    return np.array(taken, int)


def sim_fixed_risk(d, idx, risk):
    """Long trades from bars idx with a given stop distance in USD. Returns exit bar and net R at COST."""
    o, h, l, c = (d[k].to_numpy() for k in ("OPEN", "HIGH", "LOW", "CLOSE")); n = len(c)
    entry = c[idx]; stop = entry - risk; tgt = entry + RR * risk
    ex = np.full(len(idx), n - 1); px = c[-1] * np.ones(len(idx)); act = np.ones(len(idx), bool); k = 1
    while act.any():
        a = np.where(act)[0]; j = idx[a] + k; e = j >= n
        act[a[e]] = False; a, j = a[~e], j[~e]
        if len(a) == 0:
            break
        gs = o[j] <= stop[a]; gt = (o[j] >= tgt[a]) & ~gs
        hs = ~gs & ~gt & (l[j] <= stop[a]); ht = ~gs & ~gt & ~hs & (h[j] >= tgt[a])
        p = np.where(gs, o[j], np.where(gt | ht, tgt[a], stop[a])); fin = gs | gt | hs | ht
        ex[a[fin]] = j[fin]; px[a[fin]] = p[fin]; act[a[fin]] = False; k += 1
    return ex, (px - entry - COST) / risk


def seq_null(d, pool, start, end, tr, ex_rule, rule_risk, runs, rng, mask=None):
    """Null as a sequential random process (hypothesis v1.1): walk through time like the rule, one position
    at a time. After each exit (or the start) wait a number of bars drawn from the rule's own waiting times,
    then go long on the next allowed bar. Stop distance drawn from the rule's own stops (20 quantiles),
    target 1.5R, same costs, same path rules. Returns mean net R per run and number of trades per run."""
    qs = np.quantile(rule_risk, (np.arange(K) + 0.5) / K)
    EX = np.zeros((K, len(d)), int); RN = np.zeros((K, len(d)))
    for q in range(K):
        e, r = sim_fixed_risk(d, pool, np.full(len(pool), qs[q])); EX[q, pool] = e; RN[q, pool] = r
    prev_exit = np.concatenate([[start - 1], ex_rule[tr][:-1]])
    if mask is not None:                                    # a wait never spans the excluded period
        mi = np.where(mask)[0]; gaps = np.where(np.diff(mi) > 1)[0]
        for g in gaps:
            hi = mi[g + 1]
            prev_exit[(prev_exit < hi) & (tr >= hi)] = hi - 1
    waits = tr - prev_exit
    means = np.empty(runs); counts = np.empty(runs, int)
    for t in range(runs):
        ptr = start - 1; got = []
        while True:
            want = ptr + waits[rng.integers(0, len(waits))]
            k = np.searchsorted(pool, want)
            if k >= len(pool) or pool[k] > end:
                break
            i = pool[k]; q = rng.integers(0, K)
            got.append(RN[q, i]); ptr = EX[q, i]
        means[t] = np.mean(got); counts[t] = len(got)
    return means, counts


def pct(x, dist):
    return 100.0 * (np.sum(dist < x) + 0.5 * np.sum(dist == x)) / len(dist)


def wilson(k, n, z=1.96):
    p = k / n; dd = 1 + z * z / n; mid = (p + z * z / (2 * n)) / dd
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / dd
    return mid - h, mid + h


def day_boot(r, days, rng, B=10000):
    groups = [r[days == u] for u in np.unique(days)]
    k = len(groups); out = np.empty(B)
    for b in range(B):
        out[b] = np.concatenate([groups[j] for j in rng.integers(0, k, k)]).mean()
    return np.percentile(out, [2.5, 97.5])


def prepare(d):
    f = features(d)
    n = len(d)
    allbars = np.where(f["sized"])[0]
    allbars = allbars[allbars < n - 1]
    ex, rg, risk, op = outcomes(d, f, allbars)
    exit_of = np.full(n, n - 1); R = np.full(n, np.nan); RK = np.full(n, np.nan); OPEN = np.zeros(n, bool)
    exit_of[allbars] = ex; R[allbars] = rg; RK[allbars] = risk; OPEN[allbars] = op
    return f, exit_of, R, RK, OPEN


def evaluate(d, prep, mask, rng, runs=RUNS, verbose=True, label=""):
    f, exit_of, R, RK, OPEN = prep
    valid = mask & f["sized"] & ~np.isnan(R)
    sig_all = np.where(mask & f["signal"])[0]
    sig = np.where(valid & f["signal"])[0]
    tr = rule_trades(sig, exit_of)
    out = dict(label=label, signals=len(sig_all), dropped_minstop=len(sig_all) - len(sig), n=len(tr))
    if len(tr) == 0:
        return out
    rnet = {c: R - c / RK for c in COSTS}
    r = rnet[COST][tr]
    wins = int((R[tr] > 0).sum())
    out.update(win=wins / len(tr), wil=wilson(wins, len(tr)), mean=r.mean(), open=int(OPEN[tr].sum()),
               pf=r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else np.inf,
               cost_means={c: rnet[c][tr].mean() for c in COSTS}, med_risk=float(np.median(RK[tr])))
    days = d["TIME"].dt.date.to_numpy()[tr]
    out["boot"] = day_boot(r, days, rng) if len(tr) > 1 else (np.nan, np.nan)
    poolA = np.where(valid & f["context"])[0]; poolB = np.where(valid)[0]
    start, end = int(np.where(mask)[0][0]), int(np.where(mask)[0][-1])
    mA, cA = seq_null(d, poolA, start, end, tr, exit_of, RK[tr], runs, rng, mask)
    mB, cB = seq_null(d, poolB, start, end, tr, exit_of, RK[tr], runs, rng, mask)
    out.update(pctA=pct(r.mean(), mA), pctB=pct(r.mean(), mB), nullA=np.percentile(mA, [5, 50, 95]), nullB=np.percentile(mB, [5, 50, 95]), cntA=float(np.median(cA)), cntB=float(np.median(cB)))
    srt = np.sort(r)[::-1]; top = max(1, int(round(0.05 * len(r))))
    out.update(top5=srt[:top].sum(), total=r.sum())
    streak = mx = 0
    for x in R[tr]:
        streak = streak + 1 if x <= 0 else 0; mx = max(mx, streak)
    out["max_loss_streak"] = mx
    out["trades"] = pd.DataFrame({"ENTRY_TIME": d["TIME"].to_numpy()[tr], "EXIT_TIME": d["TIME"].to_numpy()[exit_of[tr]],
                                  "ENTRY": f["c"][tr], "STOP": f["stop"][tr], "RISK_USD": RK[tr], "R_GROSS": R[tr], "R_NET": r, "OPEN_AT_END": OPEN[tr]})
    if verbose:
        report(out)
    return out


def report(o):
    print(f"\n== {o['label']}")
    print(f"  signals {o['signals']}, dropped by min stop {o['dropped_minstop']}, trades {o['n']}{'  INSUFFICIENT (<100)' if o['n'] < 100 else ''}, open at end {o.get('open', 0)}")
    if o["n"] == 0:
        return
    print(f"  win rate {100*o['win']:.1f}%  (95% {100*o['wil'][0]:.1f} to {100*o['wil'][1]:.1f})   claim 58%, break-even 40% before costs")
    print(f"  mean net R {o['mean']:+.3f}  (day bootstrap 95% {o['boot'][0]:+.3f} to {o['boot'][1]:+.3f})   PF {o['pf']:.2f}")
    print("  costs 0 / 0.40 / 0.80 USD: " + " / ".join(f"{v:+.3f}" for v in o["cost_means"].values()) + f"   median stop {o['med_risk']:.2f} USD")
    print(f"  Null A 5/50/95 {o['nullA'][0]:+.3f} / {o['nullA'][1]:+.3f} / {o['nullA'][2]:+.3f} -> percentile {o['pctA']:.1f} (null trades median {o['cntA']:.0f})")
    print(f"  Null B 5/50/95 {o['nullB'][0]:+.3f} / {o['nullB'][1]:+.3f} / {o['nullB'][2]:+.3f} -> percentile {o['pctB']:.1f} (null trades median {o['cntB']:.0f})")
    print(f"  best 5% of trades {o['top5']:+.1f}R of total {o['total']:+.1f}R   longest losing streak {o['max_loss_streak']}")


def synthetic(nsets, seed=7):
    rng = np.random.default_rng(seed)
    pcts = []; wins = []
    for s in range(nsets):
        drift = 0.0 if s % 2 == 0 else 0.08
        days = pd.bdate_range("2014-01-01", periods=260 * 10)
        times = (days.values[:, None] + (np.arange(48) * np.timedelta64(30, "m"))[None, :]).ravel()
        nb = len(times); sub = 6
        sig = 0.15 / np.sqrt(260 * 48 * sub); mu = drift / (260 * 48 * sub)
        steps = rng.normal(mu - sig ** 2 / 2, sig, nb * sub)
        p = 1000 * np.exp(np.cumsum(steps)).reshape(nb, sub)
        op = np.concatenate([[1000], p[:-1, -1]])
        d = pd.DataFrame({"TIME": pd.to_datetime(times), "OPEN": op, "HIGH": np.maximum(p.max(1), op), "LOW": np.minimum(p.min(1), op), "CLOSE": p[:, -1], "SPREAD": 0})
        prep = prepare(d)
        mask = np.zeros(len(d), bool); mask[2000:] = True
        o = evaluate(d, prep, mask, np.random.default_rng(SEED + s), runs=1000, verbose=False, label=f"set {s}")
        pcts.append(o.get("pctA", np.nan)); wins.append(o.get("win", np.nan))
        print(f"set {s:2d} drift {drift:.2f}: trades {o['n']:4d} (Null A median {o.get('cntA', 0):.0f})  win {100*o.get('win', np.nan):5.1f}%  mean {o.get('mean', np.nan):+.3f}R  pct vs Null A {o.get('pctA', np.nan):5.1f}  vs Null B {o.get('pctB', np.nan):5.1f}")
    pcts = np.array(pcts)
    print(f"\nmean percentile vs Null A {np.nanmean(pcts):.1f}; above 95: {int(np.sum(pcts > 95))} of {nsets}; below 5: {int(np.sum(pcts < 5))}; mean win rate {100*np.nanmean(wins):.1f}%")


if __name__ == "__main__":
    if sys.argv[1] == "--synthetic":
        synthetic(int(sys.argv[2]))
        sys.exit()
    d = load(sys.argv[1])
    start = usable_start(d)
    print(f"bars {len(d)}, first {d['TIME'].iloc[0]}, last {d['TIME'].iloc[-1]}, usable from {start.date()}")
    d = d[d["TIME"] >= start].reset_index(drop=True)
    prep = prepare(d)
    t = d["TIME"]
    warm = (np.arange(len(d)) >= 300) & (t >= start + pd.Timedelta(days=30)).to_numpy()
    print(f"median spread column (points): {d['SPREAD'].median():.0f}")
    rng = np.random.default_rng(SEED)
    P0 = warm & ((t >= "2024-01-01") & (t < "2025-11-15")).to_numpy()
    P1 = warm & (((t < "2024-01-01") | (t >= "2026-01-01"))).to_numpy()
    res = {}
    for name, m in (("P1 decisive", P1), ("P0 2024 to 14 Nov 2025", P0)):
        res[name] = evaluate(d, prep, m, rng, label=name)
    res["P1 decisive"]["trades"].to_csv("trades_P1.csv", index=False)
    res["P0 2024 to 14 Nov 2025"]["trades"].to_csv("trades_P0.csv", index=False)
    print("\n== P2 per year (decisive trades P1 plus P0, rule only)")
    allt = pd.concat([res["P1 decisive"]["trades"], res["P0 2024 to 14 Nov 2025"]["trades"]]).sort_values("ENTRY_TIME")
    g = allt.groupby(allt["ENTRY_TIME"].dt.year)
    print(pd.DataFrame({"trades": g.size(), "win%": (g["R_GROSS"].apply(lambda x: (x > 0).mean()) * 100).round(1), "meanR": g["R_NET"].mean().round(3), "sumR": g["R_NET"].sum().round(1)}).to_string())
