"""Fetch Binance spot BTCUSDT 30-minute bars from 1 Jan 2019 (UTC) to the last closed bar.
Run on the laptop (the public Binance API is not reachable from the cloud).
Writes BTCUSDT_30m_binance.csv and prints metadata only (no prices)."""
import csv, hashlib, json, time, urllib.request

URL = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=30m&limit=1000&startTime=%d"
START = 1546300800000          # 2019-01-01 00:00 UTC
STEP = 30 * 60 * 1000
OUT = "BTCUSDT_30m_binance.csv"

now = int(time.time() * 1000)
rows, t = [], START
while True:
    with urllib.request.urlopen(URL % t, timeout=30) as r:
        batch = json.loads(r.read())
    if not batch:
        break
    for k in batch:
        if k[6] < now:                         # only closed bars
            rows.append([k[0], k[1], k[2], k[3], k[4], k[5]])
    t = batch[-1][0] + STEP
    if len(batch) < 1000 or t >= now:
        break
    time.sleep(0.2)

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["open_time_ms", "open", "high", "low", "close", "volume"])
    w.writerows(rows)

times = [r[0] for r in rows]
gaps = [(a, b) for a, b in zip(times, times[1:]) if b - a != STEP]
fmt = lambda ms: time.strftime("%Y-%m-%d %H:%M", time.gmtime(ms / 1000))
print("bars", len(rows))
print("first", fmt(times[0]), "UTC")
print("last ", fmt(times[-1]), "UTC")
print("gaps ", len(gaps), "missing bars", sum((b - a) // STEP - 1 for a, b in gaps))
for a, b in gaps[:10]:
    print("  gap after", fmt(a), "to", fmt(b))
print("sha256", hashlib.sha256(open(OUT, "rb").read()).hexdigest())
