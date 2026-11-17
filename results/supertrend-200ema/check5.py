"""check5.py . Independent check of 5 randomly chosen trades from run 01 (seed 5).
Usage: python check5.py trades_m30.csv EURUSD_M15.csv EURJPY_M15.csv  (run from the repository root)
Own M30 build with plain loops, the plain-Python Supertrend (supertrend_reference), own EMA loop, own M15 walk."""
import csv, datetime as dt, random, sys
sys.path.insert(0, 'supertrend-200ema')
from supertrend_control import supertrend_reference, _us_dst_bounds
import pandas as pd

def load(path):
    rows = []
    with open(path) as f:
        r = csv.reader(f, delimiter='\t'); next(r)
        for x in r:
            t = dt.datetime.strptime(x[0] + ' ' + x[1], '%Y.%m.%d %H:%M:%S')
            s, e = _us_dst_bounds(t.year)
            off = 3 if s.to_pydatetime() <= t < e.to_pydatetime() else 2
            rows.append((t - dt.timedelta(hours=off), float(x[2]), float(x[3]), float(x[4]), float(x[5])))
    return rows

def m30(rows):
    out = {}
    for t, o, h, l, c in rows:
        k = t.replace(minute=0 if t.minute < 30 else 30, second=0)
        if k not in out: out[k] = [o, h, l, c]
        else:
            b = out[k]; b[1] = max(b[1], h); b[2] = min(b[2], l); b[3] = c
    keys = sorted(out); return keys, [out[k] for k in keys]

T = list(csv.DictReader(open(sys.argv[1])))
random.seed(5); pick = random.sample(range(len(T)), 5)
files = {'EURUSD': sys.argv[2], 'EURJPY': sys.argv[3]}
cache = {}
ok_all = True
for i in sorted(pick):
    tr = T[i]; sym = tr['PAIR']
    if sym not in cache:
        rows = load(files[sym]); keys, bars = m30(rows)
        st, d = supertrend_reference([b[1] for b in bars], [b[2] for b in bars], [b[3] for b in bars])
        ema = []; k = 2 / 201
        for j, b in enumerate(bars): ema.append(b[3] if j == 0 else k * b[3] + (1 - k) * ema[-1])
        cache[sym] = (rows, keys, bars, st, d, ema)
    rows, keys, bars, st, d, ema = cache[sym]
    et = dt.datetime.fromisoformat(tr['ENTRY_TIME'])
    j = keys.index(et) - 1                       # signal bar
    dirn = 1 if d[j - 1] == 1 and d[j] == -1 and bars[j][3] > ema[j] else (-1 if d[j - 1] == -1 and d[j] == 1 and bars[j][3] < ema[j] else 0)
    entry = bars[j + 1][0]; stop = st[j]; sd = (entry - stop) * dirn
    pip = 0.01 if 'JPY' in sym else 0.0001
    tgt = entry + dirn * 1.5 * sd; stp = entry - dirn * sd
    res = None; exit_t = None
    for t, o, h, l, c in rows:
        if t < et: continue
        hs = l <= stp if dirn > 0 else h >= stp; ht = h >= tgt if dirn > 0 else l <= tgt
        if hs or ht: res = -1.0 if hs else 1.5; exit_t = t; break
    net = res - 1.2 * pip / sd
    same = dirn == int(tr['DIR']) and abs(entry - float(tr['ENTRY'])) < 1e-9 and abs(sd - float(tr['STOP_D'])) < 1e-9 and res == float(tr['R_GROSS']) and abs(net - float(tr['NET_1.2'])) < 1e-9 and str(exit_t) == tr['EXIT_TIME']
    ok_all &= same
    print(f"{sym} signal {keys[j]} UTC  dir {dirn:+d}  close {bars[j][3]} EMA200 {ema[j]:.5f}  ST {d[j-1]}->{d[j]} line {stop:.5f}")
    print(f"   entry {et} at {entry}  stop {stp:.5f} ({sd/pip:.1f} pip)  target {tgt:.5f}  exit {exit_t}  R {res:+.1f}  net {net:+.4f}   script: R {float(tr['R_GROSS']):+.1f} net {float(tr['NET_1.2']):+.4f}  -> {'EQUAL' if same else 'DIFFERENT'}")
print('ALL EQUAL' if ok_all else 'DIFFERENCES FOUND')
