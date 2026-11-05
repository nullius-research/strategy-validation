"""ruis_24sets.py . Runs srm_control on 24 random-walk sets (EURUSD) and logs Null A, Null B and net R.
Usage: python ruis_24sets.py --from 1 --to 12 --work DIR"""
import argparse, io, contextlib, subprocess, sys, re
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="a", type=int); ap.add_argument("--to", dest="b", type=int)
ap.add_argument("--work", required=True); a = ap.parse_args()
here = Path(__file__).parent
for seed in range(a.a, a.b + 1):
    d = Path(a.work) / f"s{seed}"
    subprocess.run([sys.executable, str(here / "make_synthetic.py"), "--out", str(d), "--seed", str(seed), "--pairs", "EURUSD"], check=True, capture_output=True)
    out = subprocess.run([sys.executable, str(here / "srm_control.py"), "--dir", str(d), "--pairs", "EURUSD", "--broker-offset", "0",
                          "--runs", "2000", "--out", str(d / "t.csv")], check=True, capture_output=True, text=True).stdout
    n = re.search(r"Trades (\d+)", out).group(1)
    wr = re.search(r"win rate ([\d.]+)%", out).group(1)
    m = re.search(r"1\.2 pip ([+-][\d.]+)", out).group(1)
    pa = re.search(r"Null A.*percentile ([\d.]+)", out).group(1)
    pb = re.search(r"Null B.*percentile ([\d.]+)", out).group(1)
    print(f"{seed}\t{n}\t{wr}\t{m}\t{pa}\t{pb}", flush=True)
