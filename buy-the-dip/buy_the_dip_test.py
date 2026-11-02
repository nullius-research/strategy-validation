"""
Nullius Research - "Buy the Dip after 3 red days", as published in a backtest report

Regels zoals het rapport ze publiceert:
  1. Een rode dag = slot lager dan het slot van de dag ervoor.
  2. Na 3 rode dagen op rij: koop op het slot van de derde.
  3. Verkoop op het slot van de eerste dag die hoger sluit, of na maximaal N dagen (N is geblurd).
  4. Geen stop, geen target.

Wat dit script doet:
  - draait de regel voor N = 1..10 en zonder maximum (de geblurde parameter als bereik, niet als gok)
  - rekent kosten per round trip mee (in basispunten, instelbaar)
  - vergelijkt elk resultaat met twee controlegroepen (2.000 runs elk):
      Null A: willekeurige instapdag, ZELFDE exitregel  -> test of de instap (3 rode dagen) iets toevoegt
      Null B: willekeurige instapdag, ZELFDE houdduren  -> test hetzelfde, maar los van de exitregel
  - vergelijkt met buy-and-hold over dezelfde periode
  - test de spiegelversie (short na 3 groene dagen), die volgens het rapport faalde

Gebruik:
  python buy_the_dip_test.py pad/naar/koersen.csv [--cost-bps 2] [--runs 2000] [--seed 42]
CSV-kolommen nodig: date, close  (dagdata, oplopend of aflopend)
"""
import argparse
import sys

import numpy as np
import pandas as pd

PERIODS = {
    "2000-2007 (vooraf, dotcom)": ("2000-01-01", "2007-12-31"),
    "2008-2009 (vooraf, krediet)": ("2008-01-01", "2009-12-31"),
    "2010-2018 (vooraf)": ("2010-01-01", "2018-12-31"),
    "2019-sep2026 (report)": ("2019-01-01", "2026-09-30"),
}
MAX_DAYS = [1, 2, 3, 4, 5, 7, 10, None]


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.lower().strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").dropna(subset=["close"]).reset_index(drop=True)
    return df[["date", "close"]]


def run_rule(close, max_days, side=1, streak=3, entries=None):
    """Bar voor bar. side=1 long na rode reeks, side=-1 short na groene reeks.
    entries: optioneel vaste lijst instap-indexen (voor Null A). Geeft lijst (in, uit)."""
    n = len(close)
    trades = []
    i = streak
    entry_set = None if entries is None else set(entries)
    while i < n - 1:
        if entry_set is None:
            ok = all((close[i - k] - close[i - k - 1]) * side < 0 for k in range(streak))
        else:
            ok = i in entry_set
        if not ok:
            i += 1
            continue
        j = i + 1
        while j < n:
            favourable = (close[j] - close[j - 1]) * side > 0
            if favourable or (max_days is not None and j - i >= max_days):
                break
            j += 1
        if j >= n:
            break  # open positie aan het eind van de data telt niet mee
        trades.append((i, j))
        i = j + 1  # geen overlap; nieuwe instap pas na de uitstap
    return trades


def stats(close, trades, side, cost):
    if not trades:
        return dict(trades=0, win=np.nan, pf=np.nan, ret=0.0, dd=0.0, expo=0.0)
    r = np.array([side * (close[j] / close[i] - 1) - cost for i, j in trades])
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    pf = gains / losses if losses > 0 else np.inf
    eq = np.cumprod(1 + r)
    dd = (1 - eq / np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:]).max()
    days = sum(j - i for i, j in trades)
    return dict(trades=len(r), win=(r > 0).mean(), pf=pf, ret=eq[-1] - 1, dd=dd,
                expo=days / len(close))


def random_entries(n, k, rng, lo=3):
    return np.sort(rng.choice(np.arange(lo, n - 1), size=min(k, n - 1 - lo), replace=False))


def null_a(close, n_trades, max_days, side, cost, runs, rng):
    """Willekeurige instap, zelfde exitregel. Trekt ruim kandidaten en houdt de eerste n_trades niet-overlappende."""
    pfs = np.empty(runs)
    n = len(close)
    for r in range(runs):
        cand = random_entries(n, min(n - 5, n_trades * 4), rng)
        t = run_rule(close, max_days, side, entries=cand)
        if len(t) > n_trades:
            t = [t[x] for x in np.sort(rng.choice(len(t), n_trades, replace=False))]
        pfs[r] = stats(close, t, side, cost)["pf"]
    return pfs


def null_b(close, durations, side, cost, runs, rng):
    """Willekeurige instap, zelfde houdduren (geschud), geen overlap."""
    pfs = np.empty(runs)
    n = len(close)
    total = sum(durations) + len(durations)
    for r in range(runs):
        d = rng.permutation(durations)
        slack = n - 1 - total
        if slack <= 0:
            pfs[r] = np.nan
            continue
        gaps = np.diff(np.sort(np.concatenate([[0], rng.choice(slack + 1, len(d), replace=True)])))
        t, pos = [], 0
        for g, dur in zip(gaps, d):
            pos += g
            t.append((pos, pos + dur))
            pos += dur + 1
        pfs[r] = stats(close, t, side, cost)["pf"]
    return pfs


def beat(pf, pfs):
    pfs = pfs[~np.isnan(pfs)]
    return int((pfs < pf).sum()), len(pfs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--name", default=None)
    ap.add_argument("--cost-bps", type=float, default=2.0, help="kosten per round trip in bp (1x)")
    ap.add_argument("--runs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    df = load(a.csv)
    name = a.name or a.csv
    rng = np.random.default_rng(a.seed)
    rows = []
    for pname, (s, e) in PERIODS.items():
        sub = df[(df.date >= s) & (df.date <= e)].reset_index(drop=True)
        if len(sub) < 20:
            continue
        c = sub.close.to_numpy()
        bh = c[-1] / c[0] - 1
        for side, label in [(1, "long na 3 rood"), (-1, "short na 3 groen")]:
            for md in MAX_DAYS:
                if side == -1 and md not in (3, None):
                    continue
                t = run_rule(c, md, side)
                for mult in (1, 2):
                    cost = a.cost_bps * mult / 1e4
                    st = stats(c, t, side, cost)
                    row = dict(markt=name, periode=pname, variant=label,
                               max_dagen=md if md else "geen", kosten=f"{mult}x", **st,
                               buy_hold=bh)
                    if mult == 1 and st["trades"] >= 5:
                        pa = null_a(c, st["trades"], md, side, cost, a.runs, rng)
                        pb = null_b(c, [j - i for i, j in t], side, cost, a.runs, rng)
                        row["nullA_beat"] = "%d/%d" % beat(st["pf"], pa)
                        row["nullB_beat"] = "%d/%d" % beat(st["pf"], pb)
                        row["nullA_pf_med"] = float(np.nanmedian(pa))
                    rows.append(row)
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_columns", 30)
    fmt = out.copy()
    for col in ["win", "ret", "dd", "expo", "buy_hold"]:
        fmt[col] = (fmt[col] * 100).round(1)
    for col in ["pf", "nullA_pf_med"]:
        fmt[col] = fmt[col].round(2)
    print(fmt.to_string(index=False))
    return out


if __name__ == "__main__":
    res = main()
    if len(sys.argv) > 1:
        res.to_csv(sys.argv[1].rsplit("/", 1)[-1].replace(".csv", "") + "_btd_results.csv", index=False)
