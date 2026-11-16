"""Test L: independent recalculation of five setups from trades_G_P1.csv and two from
trades_Z_P1.csv. Written separately from structured_control.py (pandas resample,
plain Python loops), to catch errors in the main script."""
import pandas as pd
import numpy as np

df = pd.read_csv("BTCUSDT_30m_binance.csv")
df["t"] = pd.to_datetime(df.open_time_ms, unit="ms", utc=True)
df = df.set_index("t")

# 4h bars, labelled by their start, closes = last 30m close in the window
c4 = df["close"].resample("4h", origin="epoch").last().dropna()

def ema_sma_seed(x, n):
    x = list(x)
    out = [np.nan] * len(x)
    v = sum(x[:n]) / n
    out[n - 1] = v
    for i in range(n, len(x)):
        v = v + 2 / (n + 1) * (x[i] - v)
        out[i] = v
    return out

e4 = pd.Series(ema_sma_seed(c4.values, 200), index=c4.index)
lags = [0, 5, 10, 15, 20, 30, 40, 50]
pos = {t: i for i, t in enumerate(c4.index)}

def filt_at(ts_close):
    """Colour and EMA of the last 4h bar that ended at or before ts_close."""
    start = ts_close.floor("4h") - pd.Timedelta(hours=4)
    i = pos[start]
    up = all(c4.iloc[i - k] > e4.iloc[i - k] for k in lags)
    dn = all(c4.iloc[i - k] < e4.iloc[i - k] for k in lags)
    return (1 if up else -1 if dn else 0), e4.iloc[i]

cl = df["close"].values
ema12 = ema_sma_seed(cl, 12)
ema26 = ema_sma_seed(cl, 26)
mac = np.array(ema12) - np.array(ema26)
sigl = np.full(len(cl), np.nan)
sigl[25:] = ema_sma_seed(mac[25:], 9)

def is_signal(j, d):
    ts_close = df.index[j] + pd.Timedelta(minutes=30)
    col, e = filt_at(ts_close)
    c = cl[j]
    if d == 1:
        ok = mac[j - 1] <= sigl[j - 1] and mac[j] > sigl[j] and mac[j] < 0 and sigl[j] < 0 and col == 1 and c > e
    else:
        ok = mac[j - 1] >= sigl[j - 1] and mac[j] < sigl[j] and mac[j] > 0 and sigl[j] > 0 and col == -1 and c < e
    return ok, e

O, H, L = df["open"].values, df["high"].values, df["low"].values

def replay(start, d, structured):
    ok, S = is_signal(start, d)
    assert ok, "no signal at start"
    entries = [cl[start]]
    r1 = d * (cl[start] - S)
    size = [(0.01 if structured else 0.03) / r1]
    tgt = cl[start] + d * (0.25 if structured else 0.5) * r1
    j = start + 1
    while True:
        if (d == 1 and L[j] <= S) or (d == -1 and H[j] >= S):
            px = min(O[j], S) if d == 1 else max(O[j], S); win = 0; break
        if (d == 1 and H[j] >= tgt) or (d == -1 and L[j] <= tgt):
            px = max(O[j], tgt) if d == 1 else min(O[j], tgt); win = 1; break
        if structured and len(entries) < 3:
            sok, _ = is_signal(j, d)
            if sok and d * (entries[-1] - cl[j]) >= 0.10 * r1 and d * (cl[j] - S) > 0:
                entries.append(cl[j]); size.append(0.01 / (d * (cl[j] - S)))
                avg = sum(s * e for s, e in zip(size, entries)) / sum(size)
                tgt = avg + d * (0.5 if len(entries) == 3 else 0.25) * d * (avg - S)
        j += 1
    res = sum(s * (d * (px - e) - 0.0006 * (e + px)) for s, e in zip(size, entries))
    return len(entries), j, win, 100 * res, S, entries, px

out = []
for fn, structured in (("trades_G_P1.csv", True), ("trades_Z_P1.csv", False)):
    t = pd.read_csv(fn)
    if structured:
        pick = [t[t.entries == 1].iloc[10], t[t.entries == 2].iloc[20], t[t.entries == 3].iloc[5],
                t[(t.entries == 3) & (t.win == 0)].iloc[0], t[t.dir == -1].iloc[-1]]
    else:
        pick = [t[t.win == 0].iloc[3], t[t.dir == -1].iloc[7]]
    for row in pick:
        n, ex, win, res, S, ents, px = replay(int(row.start_bar), int(row.dir), structured)
        code = row.result_pct if structured else row.result_R * 3
        line = "%s %s dir %+d  entries code %d hand %d  exit code %s hand %s  win %d/%d  result%% code %.5f hand %.5f  stop %.2f  entries %s  exit px %.2f" % (
            "G" if structured else "Z", row.start_time, row.dir, row.entries, n, row.exit_time[:16],
            str(df.index[ex])[:16], row.win, win, code, res, S, [round(x, 2) for x in ents], px)
        print(line)
        out.append(abs(code - res) < 1e-6 and int(row.entries) == n and int(row.exit_bar) == ex and int(row.win) == win)
print("ALL EQUAL" if all(out) else "DIFFERENCE FOUND", sum(out), "of", len(out))
