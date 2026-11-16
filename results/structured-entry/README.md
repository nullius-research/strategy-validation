# Structured entry with MACD and a 4-hour colour EMA on Bitcoin 30 minutes: results

The rule comes from a trading channel's video (September 2024) presented as an "87% win rate" strategy. The video tests it by hand on "the last four years of Bitcoin USD price movement" on the 30-minute chart, with a 4-hour 200 EMA for the trend. Two variants, 100 trades each: a single entry with a 0.5R target ("approximately 73%" winners, "around 28% profit"), and a structured entry of up to three positions in the same setup with targets of 0.25R, 0.25R and 0.5R measured from the average entry price (87% winners, "slightly lower total profit"). The trend filter is the channel's own 200 EMA that "disappears" in a sideways market; its code is public, so the rule could be rebuilt exactly. Undefined in the video, and fixed in advance: the distance an added entry must improve on the previous one, a minimum stop distance, and the exact place of the stop.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (binding), with an English version written at the same time. The published Dutch file differs from the internal one only in one removed first name, one removed reference to a private source file, and the indicator's short name replaced by "kleur-EMA" (colour EMA). All numbers are identical.

## Rule

| | |
|---|---|
| Script | `structured-entry/structured_control.py` in the repository root. Needs `numba` besides pandas and numpy |
| Bars | Binance spot BTCUSDT, 30 minutes, 1 January 2019 to 15 November 2026 08:30 UTC (`structured-entry/fetch_binance.py`, data check in `data_check_btcusdt.txt`) |
| 4-hour bars | Eight 30-minute bars, starting 00:00, 04:00, ... UTC. A 30-minute bar only uses the last closed 4-hour bar |
| Colour EMA | EMA(200) of the 4-hour close (first value the SMA of the first 200). Green if the close now and 5, 10, 15, 20, 30, 40 and 50 bars back each was above the EMA of that bar; red if each was below; otherwise no colour |
| MACD | 12, 26, 9 on the 30-minute close |
| Long signal | MACD crosses above its signal line, both below zero, colour EMA green, close above the 4-hour EMA. Short mirrored |
| Variant Z, single entry | Entry at the close. Stop at the 4-hour EMA at entry, fixed. Target 0.5R. One position at a time |
| Variant G, structured | Entry 1 at the close, stop S at the 4-hour EMA, fixed for the setup. While open, a new signal in the same direction adds entry 2 and then 3 if it is at least 10% of (entry 1 to S) better than the previous entry and still on the right side of S. Each entry risks 1% of the account to S. Target after 1 or 2 entries: average + 0.25 x (average - S); after 3: 0.5 x |
| Minimum stop | No trade if entry 1 is less than 0.5% of the price from the stop |
| Path rule | Bar by bar on 30 minutes. Stop before target; a bar that hits both counts as a stop. A bar that opens beyond a level exits at its open. No new setup on the bar where one ends |
| Costs | 0.06% per side (taker fee plus slippage) on every entry and every exit. Sensitivity 0 and 0.20% per round trip. No leverage |
| Decisive period | P1: 11 February 2019 (first bar with a valid colour EMA) to 14 November 2026 |
| Run | Run 1 of 1 |

## Noise check first

24 fake markets of 6 years on 30 minutes, random walk without drift at 60% volatility per year, built from 1-minute steps, 2,000 control runs per set. Threshold per variant: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95.

| Variant | Mean percentile | Above 95 | Win rate on noise | Outcome |
|---|---|---|---|---|
| G, structured | 38.9 | 1 of 24 | 79.6% to 85.7% | Passed |
| Z, single entry | 42.8 | 0 of 24 | 60.0% to 73.3% | Passed |

On markets with no pattern at all, the structured rule already wins 80 to 86% of its setups (`noise_24sets.txt`).

## Result, P1 (decisive)

Funnel: 135,870 bars after warm-up, 86,410 with a green or red colour EMA, 85,832 also with the close on the right side of the EMA, 3,320 MACD crosses in the filter direction, 1,935 on the right side of the zero line.

| | G, structured | Z, single entry |
|---|---|---|
| Setups or trades | 448 (one, two, three entries: 280, 91, 77) | 211 |
| Dropped for the minimum stop | 25 | 9 |
| Win rate | 85.7% (95% Wilson: 82.2% to 88.7%) | 71.1% (64.6% to 76.8%) |
| Mean net result | +0.059% of the account per setup (95% bootstrap by week: -0.038% to +0.151%) | +0.035 R per trade (-0.064 to +0.129) |
| Profit factor | 1.19 | 1.12 |
| Median stop distance | 6.7% of the price | 7.2% |
| Best and worst | +1.49% and -3.27% | +0.50 R and -1.24 R |
| Longest losing streak | 3 | 4 |
| Long and short | 260 and 188 | 122 and 89 |

R is the risk of one trade, from entry to stop. In variant G each entry risks 1% of the account, so a setup with three entries risks 3%.

## Control (10,000 runs, seed 41)

Null A replaces the MACD cross with a random signal: on every 30-minute bar where the colour filter holds, a signal fires with a probability chosen so that the number of signals equals the rule's. Everything else is identical: the same stop, minimum stop, add rules, targets and costs, run as a sequential process through time.

| | 5th / 50th / 95th percentile of the mean | The rule | Percentile |
|---|---|---|---|
| G, % of the account per setup | -0.019 / +0.025 / +0.068 | +0.059 | **90.4** |
| Z, net R per trade | +0.022 / +0.061 / +0.098 | +0.035 | **13.6** |

Win rate of the same control runs, added after the run as a description (`nulla_winrate.py`, not part of the pre-set criteria): G 84.2% / **85.8%** / 87.4%, Z 69.9% / **72.5%** / 74.9% (5th / 50th / 95th percentile).

## Verdict by the pre-set criteria (P1)

| Claim | Criterion | Result |
|---|---|---|
| C1: structured 87% | upper end of the 95% range below 87% | 88.7%: not falsified |
| C2: single entry 73% | upper end of the 95% range below 73% | 76.8%: not falsified |
| C3: single entry profitable | upper end of the 95% range of mean net R below 0 | +0.129 R: not falsified, and not shown either (the range includes 0) |
| C4: structured profitable | upper end of the 95% range of the mean below 0 | +0.151%: not falsified, and not shown either (the range includes 0) |
| C5a: structured beats chance | not above percentile 95 of Null A | 90.4: falsified |
| C5b: single entry beats chance | not above percentile 95 of Null A | 13.6: falsified |

In this measurement the win rates of the video are reproduced, and random entries with the same filter, stop, targets and add rules reach them too.

## The four years of the video (P0, not decisive)

28 September 2020 to 27 September 2024: G 229 setups, 86.5% (81.4% to 90.3%), +0.078% per setup, percentile 88.3. Z 98 trades (under 100: insufficient), 70.4% (60.7% to 78.5%), +0.027 R, percentile 14.5. The video took 100 trades per variant; which signals it took is not stated.

## After the video (P2, supplementary)

28 September 2024 to 14 November 2026: G 116 setups, 82.8%, +0.039%, percentile 76.3. Z 60 trades (insufficient), 66.7%, -0.039 R, percentile 9.7.

## Same entries, one position, target 0.25R (not tested, for comparison)

392 trades, 82.9% (78.9% to 86.3%), +0.006 R, percentile 29.9 (2,000 runs).

## Per year and direction (P3)

Every single year is under 100 setups and therefore insufficient on its own; see `run01.txt`. Long and short: G 260 long 87.7% +0.111%, 188 short 83.0% -0.013%; Z 122 long 75.4% +0.102 R, 89 short (insufficient) 65.2% -0.057 R.

## Sensitivity (P1, 2,000 control runs, not decisive)

| Variant | G win rate | G mean | G percentile | Z win rate | Z mean R | Z percentile |
|---|---|---|---|---|---|---|
| Add distance 0% | 83.3% | +0.049% | 53.5 | | | |
| Add distance 25% | 85.7% | +0.007% | 53.3 | | | |
| No minimum stop | 84.9% | -0.138% | 0.95 | 70.5% | +0.007 | 20.0 |
| Minimum stop 1.0% | 86.2% | +0.075% | 94.7 | 71.4% | +0.047 | 16.1 |
| Costs 0 | 85.7% | +0.105% | 93.6 | 71.1% | +0.066 | 19.0 |
| Costs 0.20% per round trip | 85.7% | +0.028% | 86.6 | 71.1% | +0.014 | 11.6 |
| Plain 4-hour 200 EMA, no colour | 85.6% | +0.015% | 50.2 | 72.5% | +0.037 | 15.0 |

Without a minimum stop, one setup with a very small stop lost 79.96% of the account in a single price jump. No variant comes above percentile 95.

## Independent check

Five setups of G (with one, two and three entries, two losses with three entries, one short) and two trades of Z recomputed with separate code (`check5.py`, pandas resampling and plain loops): 7 of 7 identical in entries, exit bar, win or loss and net result (`check5_trades.txt`).

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.0-english.md` | Fixed before the data was opened |
| `data_check_btcusdt.txt` | Bars, gaps, consistency of the data file |
| `noise_24sets.txt` | Noise check |
| `run01.txt` | P1, P0, P2, P3 and the sensitivities |
| `trades_G_P1.csv`, `trades_Z_P1.csv`, `trades_Z025_P1.csv`, `trades_G_P0.csv`, `trades_Z_P0.csv`, `trades_G_P2.csv`, `trades_Z_P2.csv` | All setups and trades |
| `nulla_winrate.py`, `nulla_winrate.txt` | Win rate of the control runs (descriptive, added after the run) |
| `check5.py`, `check5_trades.txt` | Independent check |

## Reproduce

```
pip install pandas numpy numba
python structured-entry/fetch_binance.py
python structured-entry/structured_control.py selftest
python structured-entry/structured_control.py noise
python structured-entry/structured_control.py run BTCUSDT_30m_binance.csv
```

A new download ends later than ours, so its SHA-256 differs from 8ed44f29...; the periods are cut at 15 November 2026, so the same bars give the same numbers.

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
