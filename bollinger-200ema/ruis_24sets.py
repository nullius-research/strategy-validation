"""ruis_24sets.py . Runs bb200_control on random-walk sets (EURUSD) and logs trades, win rate, net R, Null A and Null B.
Usage: python ruis_24sets.py --from 1 --to 12 --work DIR"""
import argparse, subprocess, sys, re
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="a", type=int); ap.add_argument("--to", dest="b", type=int)
ap.add_argument("--work", required=True); a = ap.parse_args()
here = Path(__file__).parent
for seed in range(a.a, a.b + 1):
    d = Path(a.work) / f"s{seed}"
    subprocess.run([sys.executable, str(here / "make_synthetic.py"), "--out", str(d), "--seed", str(seed), "--pairs", "EURUSD"], check=True, capture_output=True)
    out = subprocess.run([sys.executable, str(here / "bb200_control.py"), "--dir", str(d), "--pairs", "EURUSD", "--broker-offset", "0",
                          "--runs", "2000", "--out", str(d / "t.csv")], check=True, capture_output=True, text=True).stdout
    n = re.search(r"Trades (\d+)", out).group(1)
    wr = re.search(r"Win rate ([\d.]+)%", out).group(1)
    m = re.search(r"Mean net R at 1\.2 pip\s+([+-][\d.]+)", out).group(1)
    pa = re.search(r"Null A.*percentile ([\d.]+)", out).group(1)
    pb = re.search(r"Null B.*percentile ([\d.]+)", out).group(1)
    st = re.search(r"Median stop ([\d.]+)", out).group(1)
    print(f"{seed}\t{n}\t{wr}\t{m}\t{pa}\t{pb}\t{st}", flush=True)
