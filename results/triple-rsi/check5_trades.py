#!/usr/bin/env python3
"""Independent check of 5 random trades from trades_P1.csv: own RSI (pandas ewm), own SMA, own signal and exit."""
import pandas as pd, numpy as np
px = pd.read_csv("SPY_yahoo_D1_1993_2026.csv", parse_dates=["date"]).set_index("date")["close"]
dl = px.diff(); up = dl.clip(lower=0); dn = -dl.clip(upper=0)
rsi = 100 - 100 / (1 + up.ewm(alpha=1/5, adjust=False).mean() / dn.ewm(alpha=1/5, adjust=False).mean())
ma = px.rolling(200).mean()
tr = pd.read_csv("trades_P1.csv", parse_dates=["entry_date", "exit_date"])
pick = tr.sample(5, random_state=5)
for _, t in pick.iterrows():
    i = px.index.get_loc(t.entry_date); r = rsi.values
    sig = r[i] < 30 and r[i] < r[i-1] < r[i-2] < r[i-3] and r[i-3] < 60 and px.iloc[i] > ma.iloc[i]
    j = i + 1
    while not (r[j-1] <= 50 and r[j] > 50): j += 1
    ret = px.iloc[j] / px.iloc[i] - 1 - 0.0002
    print(f"{t.entry_date.date()} signal {sig}  rsi {r[i]:.2f} (script {t.rsi5_entry:.2f})  exit {px.index[j].date()} (script {t.exit_date.date()})  "
          f"net {100*ret:+.3f}% (script {100*t.net_return:+.3f}%)  match {abs(ret-t.net_return)<1e-6 and px.index[j]==t.exit_date}")
