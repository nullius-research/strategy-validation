#!/bin/sh
# Script check on noise: 24 synthetic random-walk sets, 28 pairs each.
mkdir -p noise
for i in $(seq 1 24); do
  python3 make_synthetic.py --out syn --seed $((100+i))
  python3 macdatr_control.py --dir syn --out noise/run_$i.txt --quiet
done
