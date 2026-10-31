"""
control.py v2 . Falsificatielaag.

Doel: bepalen of een signaalset informatie bevat, of dat het resultaat volledig
verklaard wordt door marktdrift, toeval en kosten.

Scoringsregels:
  1. Elke trade wordt bar voor bar vooruit gelopen, niet beoordeeld op extremen.
  2. Als een bar zowel stop als target raakt, telt het als stop. Bewust
     conservatief, en de bias werkt tegen de strategie.
  3. Kosten worden altijd in rekening gebracht, uitgedrukt in R.
  4. Betrouwbaarheidsinterval via cluster bootstrap op hele handelsdagen, niet
     op losse trades. Aandelen delen een marktfactor, dus vijf tickers die op
     dezelfde dag een signaal geven zijn een weddenschap.

TWEE CONTROLEGROEPEN, en het verschil is essentieel.

  flip   Zelfde momenten, richting door een muntworp.
         Toetst: bevat het signaal RICHTINGSinformatie?
         Waarschuwing: bij een long only strategie op aandelen is dit GEEN
         eerlijke null. Aandelen hebben opwaartse drift en een watchlist van
         vandaag heeft survivorship bias. De muntworp is half short en verliest
         daardoor systematisch. Long only verslaat deze controle bijna altijd,
         zonder dat er enige edge is.

  dates  Zelfde ticker, zelfde richting, zelfde stopafstand in ATR, maar een
         willekeurige instapdatum uit dezelfde historie.
         Toetst: kiest het signaal BETERE MOMENTEN dan willekeurige momenten?
         Drift en survivorship bias zitten in beide kanten en vallen weg.
         Dit is de juiste controle voor een long only aandelenstrategie.

Draai altijd beide. Verslaat de strategie flip maar niet dates, dan meet je
marktdrift en niets anders.

Gebruik:
    python validation/control.py --signals briefs/signals.csv \
        --bars data/history.csv --target-r 2.0 --max-hold 20 --control both

signals.csv moet bevatten: date, ticker, direction, entry, stop
"""

import argparse
import sys

import numpy as np
import pandas as pd

BOTH_HIT_IS_STOP = True
ATR_PERIOD = 14


def load_bars(path):
    bars = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "ticker", "open", "high", "low", "close"}
    missing = required - set(bars.columns)
    if missing:
        sys.exit(f"history.csv mist kolommen: {sorted(missing)}")
    bars = bars.sort_values(["ticker", "date"]).reset_index(drop=True)

    frames = []
    for t, g in bars.groupby("ticker"):
        g = g.copy()
        prev = g["close"].shift(1)
        tr = pd.concat([g["high"] - g["low"],
                        (g["high"] - prev).abs(),
                        (g["low"] - prev).abs()], axis=1).max(axis=1)
        g["atr"] = tr.ewm(alpha=1 / ATR_PERIOD, adjust=False).mean()
        frames.append(g)
    return pd.concat(frames).reset_index(drop=True)


def load_signals(path):
    sig = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "ticker", "direction", "entry", "stop"}
    missing = required - set(sig.columns)
    if missing:
        sys.exit(f"signals.csv mist kolommen: {sorted(missing)}")
    sig = sig[sig["direction"].isin([1, -1])].copy()
    return sig.sort_values("date").reset_index(drop=True)


def walk_trade(path_bars, direction, entry, stop_dist, target_r, cost_r):
    """Loopt de trade bar voor bar vooruit. Resultaat in R."""
    if stop_dist <= 0 or not np.isfinite(stop_dist):
        return None

    if direction == 1:
        stop_level, target_level = entry - stop_dist, entry + target_r * stop_dist
    else:
        stop_level, target_level = entry + stop_dist, entry - target_r * stop_dist

    highs = path_bars["high"].to_numpy()
    lows = path_bars["low"].to_numpy()

    for hi, lo in zip(highs, lows):
        if direction == 1:
            hit_stop, hit_target = lo <= stop_level, hi >= target_level
        else:
            hit_stop, hit_target = hi >= stop_level, lo <= target_level

        if hit_stop and hit_target:
            return -1.0 - cost_r if BOTH_HIT_IS_STOP else target_r - cost_r
        if hit_stop:
            return -1.0 - cost_r
        if hit_target:
            return target_r - cost_r

    last = path_bars["close"].to_numpy()[-1]
    raw = (last - entry) / stop_dist * direction
    return float(np.clip(raw, -1.0, target_r)) - cost_r


def score_real(signals, by_ticker, target_r, max_hold, cost_bps, directions=None):
    """Scoort de echte signalen. directions overschrijft de richting (flip control)."""
    results, dates = [], []
    dirs = signals["direction"].to_numpy() if directions is None else directions

    for i, row in enumerate(signals.itertuples(index=False)):
        g = by_ticker.get(row.ticker)
        if g is None:
            continue
        pos = int(g["date"].searchsorted(row.date, side="right"))
        path = g.iloc[pos: pos + max_hold]
        if path.empty:
            continue

        stop_dist = abs(row.entry - row.stop)
        if stop_dist <= 0:
            continue
        cost_r = (row.entry * cost_bps / 10_000.0) / stop_dist

        r = walk_trade(path, int(dirs[i]), row.entry, stop_dist, target_r, cost_r)
        if r is not None:
            results.append(r)
            dates.append(row.date)

    return pd.DataFrame({"date": dates, "r": results})


def score_random_dates(signals, by_ticker, target_r, max_hold, cost_bps, rng):
    """
    Zelfde ticker, zelfde richting, zelfde stopafstand uitgedrukt in ATR,
    maar een willekeurige instapdatum uit dezelfde historie.
    """
    out = []
    for row in signals.itertuples(index=False):
        g = by_ticker.get(row.ticker)
        if g is None or len(g) < ATR_PERIOD + max_hold + 5:
            continue

        idx = min(int(g["date"].searchsorted(row.date, side="right")), len(g) - 1)
        real_atr = float(g["atr"].to_numpy()[idx])
        if not np.isfinite(real_atr) or real_atr <= 0:
            continue
        atr_mult = abs(row.entry - row.stop) / real_atr

        pos = int(rng.integers(ATR_PERIOD + 1, len(g) - max_hold - 1))
        entry = float(g["open"].to_numpy()[pos])
        atr_here = float(g["atr"].to_numpy()[pos - 1])
        stop_dist = atr_mult * atr_here
        if stop_dist <= 0 or not np.isfinite(stop_dist):
            continue

        cost_r = (entry * cost_bps / 10_000.0) / stop_dist
        r = walk_trade(g.iloc[pos: pos + max_hold], int(row.direction),
                       entry, stop_dist, target_r, cost_r)
        if r is not None:
            out.append(r)
    return float(np.mean(out)) if out else np.nan


def summarise(trades):
    r = trades["r"].to_numpy()
    if len(r) == 0:
        return dict(n=0, expectancy=np.nan, profit_factor=np.nan, win_rate=np.nan)
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    return dict(n=len(r), expectancy=r.mean(),
                profit_factor=wins / losses if losses > 0 else float("inf"),
                win_rate=(r > 0).mean())


def cluster_bootstrap(trades, n=2000, seed=7):
    rng = np.random.default_rng(seed)
    days = [g["r"].to_numpy() for _, g in trades.groupby(trades["date"].dt.date)]
    if not days:
        return np.array([])
    return np.array([
        np.concatenate([days[i] for i in rng.integers(0, len(days), len(days))]).mean()
        for _ in range(n)
    ])


def report_control(name, dist, real_exp):
    dist = dist[np.isfinite(dist)]
    if len(dist) == 0:
        print(f"  {name:<24} niet berekenbaar")
        return None
    lo, hi = np.percentile(dist, [5, 95])
    pct = float((dist < real_exp).mean() * 100)
    print(f"  {name:<24} {lo:+.4f} tot {hi:+.4f} R    percentiel {pct:.1f}")
    return pct


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--signals", required=True)
    p.add_argument("--bars", required=True)
    p.add_argument("--target-r", type=float, default=2.0)
    p.add_argument("--max-hold", type=int, default=20)
    p.add_argument("--cost-bps", type=float, default=10.0)
    p.add_argument("--control", choices=["flip", "dates", "both"], default="both")
    p.add_argument("--n-control", type=int, default=400)
    args = p.parse_args()

    bars = load_bars(args.bars)
    signals = load_signals(args.signals)
    by_ticker = {t: g.reset_index(drop=True) for t, g in bars.groupby("ticker")}

    real = score_real(signals, by_ticker, args.target_r, args.max_hold, args.cost_bps)
    s = summarise(real)
    if s["n"] == 0:
        sys.exit("Geen enkele trade kon gescoord worden. Controleer datums en tickers.")

    boot = cluster_bootstrap(real)
    b_lo, b_hi = np.percentile(boot, [2.5, 97.5]) if len(boot) else (np.nan, np.nan)
    n_days = real["date"].dt.date.nunique()
    long_share = float((signals["direction"] == 1).mean())

    print("\n" + "=" * 72)
    print(f"  RESULTAAT   target {args.target_r}R, max hold {args.max_hold} bars,"
          f" kosten {args.cost_bps} bps")
    print("=" * 72)
    print(f"  Trades                   {s['n']}, verdeeld over {n_days} handelsdagen")
    print(f"  Waarvan long             {long_share:.0%}")
    print(f"  Expectancy               {s['expectancy']:+.4f} R")
    print(f"  Profit factor            {s['profit_factor']:.3f}")
    print(f"  Win rate                 {s['win_rate']:.1%}")
    print(f"  Bootstrap 95% CI         {b_lo:+.4f} tot {b_hi:+.4f} R (cluster op dagen)")
    print("-" * 72)
    print("  CONTROLEGROEPEN                       5e tot 95e percentiel")

    rng = np.random.default_rng(42)
    pct_flip = pct_dates = None

    if args.control in ("flip", "both"):
        dist = np.array([
            score_real(signals, by_ticker, args.target_r, args.max_hold,
                       args.cost_bps,
                       directions=rng.choice([1, -1], size=len(signals)))["r"].mean()
            for _ in range(args.n_control)
        ])
        pct_flip = report_control("muntworp (richting)", dist, s["expectancy"])

    if args.control in ("dates", "both"):
        dist = np.array([
            score_random_dates(signals, by_ticker, args.target_r, args.max_hold,
                               args.cost_bps, rng)
            for _ in range(args.n_control)
        ])
        pct_dates = report_control("willekeurige datums", dist, s["expectancy"])

    print("-" * 72)

    if long_share > 0.9 and pct_flip is not None:
        print("  LET OP: bijna alles long. De muntworpcontrole is dan te makkelijk,")
        print("          want die is half short in een markt met opwaartse drift.")
        print("          Alleen 'willekeurige datums' telt hier.")
        print("-" * 72)

    beslissend = pct_dates if pct_dates is not None else pct_flip
    if beslissend is None:
        print("  OORDEEL: geen controle berekend.")
    elif beslissend < 95:
        print("  OORDEEL: VERWORPEN. Valt binnen de controleband.")
        print("           Het signaal kiest geen betere momenten dan willekeur.")
    elif b_lo <= 0:
        print("  OORDEEL: ONVOLDOENDE. Verslaat de controle, maar het")
        print("           betrouwbaarheidsinterval bevat nul. Meer data nodig.")
    else:
        print("  OORDEEL: KANDIDAAT. Herhaal op een periode en een universum")
        print("           die nog niet gebruikt zijn, voordat je iets bouwt.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
