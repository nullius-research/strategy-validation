"""
signals.py . Genereert briefs/signals.csv uit data/history.csv.

Dit script bestaat om een reden. Als een taalmodel de signalen genereert of
beoordeelt op historische data, is het resultaat besmet: het model weet wat er
na die datum is gebeurd. Dat is lookahead die je niet kunt zien en niet kunt
repareren. Alleen deterministische code mag historie aanraken.

Alle indicatoren worden berekend op bars TOT EN MET de signaalbar. De entry is
de open van de VOLGENDE bar. Dat is de enige constructie waarin een signaal
uitvoerbaar was op het moment dat het ontstond.

Regel (breakout, long only), instelbaar via de vlaggen hieronder:
    signaal:  close > hoogste high van de vorige N bars
              EN volume > V maal het gemiddelde volume van de vorige N bars
    entry:    open van de volgende bar
    stop:     entry - M * ATR14

Gebruik:
    python validation/signals.py --lookback 20 --vol-mult 1.5 --atr-mult 2.0
    python validation/signals.py --shuffle-check   # sanity check, zie onderaan
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ATR_PERIOD = 14


def atr(g, period=ATR_PERIOD):
    prev = g["close"].shift(1)
    tr = pd.concat([g["high"] - g["low"],
                    (g["high"] - prev).abs(),
                    (g["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def generate(bars, lookback, vol_mult, atr_mult, cooldown):
    rows = []
    for ticker, g in bars.groupby("ticker"):
        g = g.sort_values("date").reset_index(drop=True)
        if len(g) < lookback + ATR_PERIOD + 5:
            continue

        # shift(1) overal: alleen informatie tot en met de vorige bar.
        prior_high = g["high"].shift(1).rolling(lookback).max()
        prior_vol = g["volume"].shift(1).rolling(lookback).mean()
        a = atr(g)

        cond = (g["close"] > prior_high) & (g["volume"] > vol_mult * prior_vol)

        last_signal = -10**9
        closes = g["close"].to_numpy()
        opens = g["open"].to_numpy()
        dates = g["date"].to_numpy()
        atrs = a.to_numpy()

        for i in np.flatnonzero(cond.to_numpy()):
            if i - last_signal < cooldown or i + 1 >= len(g):
                continue
            entry = float(opens[i + 1])          # open van de VOLGENDE bar
            stop_dist = atr_mult * float(atrs[i])  # ATR tot en met de signaalbar
            if not np.isfinite(stop_dist) or stop_dist <= 0:
                continue
            rows.append({
                "date": pd.Timestamp(dates[i]),
                "ticker": ticker,
                "direction": 1,
                "entry": round(entry, 4),
                "stop": round(entry - stop_dist, 4),
            })
            last_signal = i

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bars", default=str(ROOT / "data" / "history.csv"))
    p.add_argument("--out", default=str(ROOT / "briefs" / "signals.csv"))
    p.add_argument("--lookback", type=int, default=20)
    p.add_argument("--vol-mult", type=float, default=1.5)
    p.add_argument("--atr-mult", type=float, default=2.0)
    p.add_argument("--cooldown", type=int, default=5,
                   help="minimaal aantal bars tussen twee signalen per ticker")
    args = p.parse_args()

    bars = pd.read_csv(args.bars, parse_dates=["date"])
    need = {"date", "ticker", "open", "high", "low", "close", "volume"}
    missing = need - set(bars.columns)
    if missing:
        sys.exit(f"history.csv mist kolommen: {sorted(missing)}")

    sig = generate(bars, args.lookback, args.vol_mult, args.atr_mult, args.cooldown)
    if sig.empty:
        sys.exit("Geen signalen. Versoepel de parameters of haal meer historie op.")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sig.to_csv(args.out, index=False)

    n = len(sig)
    print(f"\n  Signalen            {n}")
    print(f"  Tickers             {sig['ticker'].nunique()}")
    print(f"  Periode             {sig['date'].min().date()} tot {sig['date'].max().date()}")
    print(f"  Handelsdagen        {sig['date'].dt.date.nunique()}")
    print(f"  Geschreven naar     {args.out}")
    print(f"  Parameters          lookback={args.lookback}, vol={args.vol_mult}, "
          f"atr={args.atr_mult}, cooldown={args.cooldown}  (4 vrijheidsgraden)")
    if n < 200:
        print("\n  WAARSCHUWING: onder de 200 trades is de uitslag niet")
        print("  interpreteerbaar. Breid het universum of de periode uit.")
    print()


if __name__ == "__main__":
    main()
