"""
fetch.py . Gratis, VERTRAAGDE marktdata via yfinance. Analyse only, plaatst nooit orders.

Twee modi:
  scan     Korte tabel voor de dagelijkse pipeline (60 dagen).
  history  Volledige OHLCV export naar data/history.csv voor validation/control.py.

Gebruik:
    python data/fetch.py scan
    python data/fetch.py history --years 10

Let op: yfinance levert aangepaste koersen (splits en dividend). Voor
validatie is dat acceptabel, voor live uitvoering niet. De data is vertraagd.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    sys.exit("yfinance ontbreekt. Installeer met: pip install yfinance pandas")

ROOT = Path(__file__).resolve().parent.parent


def read_watchlist():
    path = ROOT / "config" / "watchlist.md"
    if not path.exists():
        sys.exit("config/watchlist.md niet gevonden.")
    tickers = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("-"):
            tickers.append(line.lstrip("- ").split()[0].upper())
    if not tickers:
        sys.exit("Geen tickers gevonden in config/watchlist.md.")
    return tickers


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def download(ticker, period):
    df = yf.download(ticker, period=period, interval="1d",
                     auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()


def do_scan(tickers):
    rows = []
    for t in tickers:
        df = download(t, "6mo")
        if len(df) < 60:
            print(f"  overgeslagen: {t} (te weinig bars)")
            continue
        df["RSI"] = rsi(df["Close"])
        df["ATR"] = atr(df)
        last = df.iloc[-1]
        rows.append({
            "ticker": t,
            "close": round(float(last["Close"]), 2),
            "chg%": round(float(df["Close"].pct_change().iloc[-1] * 100), 2),
            "vol_x20d": round(float(last["Volume"] / df["Volume"].tail(20).mean()), 2),
            "ma20": round(float(df["Close"].tail(20).mean()), 2),
            "ma50": round(float(df["Close"].tail(50).mean()), 2),
            "rsi14": round(float(last["RSI"]), 1),
            "atr14": round(float(last["ATR"]), 2),
            "atr%": round(float(last["ATR"] / last["Close"] * 100), 2),
        })
    out = pd.DataFrame(rows)
    print("\nVERTRAAGDE GRATIS DATA. Alleen analyse, geen orders.\n")
    print(out.to_string(index=False))
    return out


def do_history(tickers, years):
    frames = []
    for t in tickers:
        df = download(t, f"{years}y")
        if df.empty:
            print(f"  overgeslagen: {t}")
            continue
        df = df.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df.columns = ["date", "open", "high", "low", "close", "volume"]
        df["ticker"] = t
        frames.append(df)
        print(f"  {t}: {len(df)} bars")
    if not frames:
        sys.exit("Niets opgehaald.")
    out = pd.concat(frames)[["date", "ticker", "open", "high", "low", "close", "volume"]]
    dest = ROOT / "data" / "history.csv"
    out.to_csv(dest, index=False)
    print(f"\nOpgeslagen: {dest} ({len(out)} rijen)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["scan", "history"])
    p.add_argument("--years", type=int, default=10)
    args = p.parse_args()

    tickers = read_watchlist()
    if args.mode == "scan":
        do_scan(tickers)
    else:
        do_history(tickers, args.years)


if __name__ == "__main__":
    main()
