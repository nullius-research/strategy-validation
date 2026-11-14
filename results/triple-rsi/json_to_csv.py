#!/usr/bin/env python3
"""Yahoo chart JSON -> CSV date,close,adjclose (NY trading date). Same canonical form as the in-page checksum."""
import json, sys, hashlib, datetime as dt
src, out = sys.argv[1], sys.argv[2]
cut = sys.argv[3] if len(sys.argv) > 3 else None   # drop dates >= cut (unfinished day)
r = json.load(open(src, encoding="utf-8"))["chart"]["result"][0]
gmt = r["meta"]["gmtoffset"]; q = r["indicators"]["quote"][0]; a = r["indicators"]["adjclose"][0]["adjclose"]
rows = []
for t, c, ac in zip(r["timestamp"], q["close"], a):
    if c is None: continue
    d = dt.datetime.fromtimestamp(t + gmt, dt.timezone.utc).strftime("%Y-%m-%d")
    if cut and d >= cut: continue
    def js(x):  # match JavaScript number-to-string
        s = repr(float(x)); return s[:-2] if s.endswith(".0") else s
    rows.append(f"{d},{js(c)},{js(ac)}")
txt = "date,close,adjclose\n" + "\n".join(rows) + "\n"
open(out, "w", newline="\n").write(txt)
print(out, len(rows), rows[0][:10], rows[-1][:10], hashlib.sha256(txt.encode()).hexdigest())
