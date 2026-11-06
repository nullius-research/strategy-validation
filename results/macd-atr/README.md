# MACD + ATR stop and target: results

The rules come from an open-source strategy script published in August 2020, together with a video and a public spreadsheet by the same maker. The script tests five MACD signals on daily charts of 28 forex pairs, with a stop at 1.5 x ATR and a target at 1 x ATR. The headline of the video: "we've hit the 90% WinRAte mark" on one pair. The spreadsheet gives average win rates over the 28 pairs of 62.54% (MACD line crossing zero) and 64.25% (signal line crossing zero, called the winner). The maker says that above 60% he is convinced a strategy "can be really profitable".

The hypothesis was written and fixed before any signal was computed on real data: `hypothesis-v1.0-dutch.md` (in Dutch, names of the source removed). The script was then checked on 24 sets of synthetic random-walk data before the real run.

## What was visible before the test

- **60% is break-even, and 60% is what chance gives.** With a target of 1 ATR and a stop of 1.5 ATR, the break-even win rate before costs is 1.5 / (1 + 1.5) = 60%. For a random walk without drift, the chance of moving +1 before -1.5 is also 1.5 / 2.5 = 60%. The threshold the maker uses is the result you get with no predictive power at all.
- **The 90% is the best of 140 small samples.** The spreadsheet has 28 pairs x 5 signals = 140 cells. The 90% headline is the highest cell, 94.12%, which is 16 of 17 trades. If a coin wins 60% of the time, 16 or more wins in 17 has a 0.21% chance on its own. Among 140 cells the best one is high by construction.
- **The description and the code differ.** The description says half the position is closed at the target and the stop moves to break-even. The script closes the whole position at the target or the stop. The spreadsheet was made with the script, according to the video. The script also sets no costs.

## Setup

| | |
|---|---|
| Script | `macd-atr/macdatr_control.py` in the repository root |
| Bars | Daily (D1) signals. Trade paths walked hour by hour (H1) from the same broker |
| Indicators | MACD 12, 26, 9 (EMA on close). ATR 14, Wilder smoothing, as in the source script |
| Signals | MACD line crosses zero; signal line crosses zero (both decisive). Continuation, reversal and histogram as in the source script (reported, not decisive) |
| Entry | Open of the next daily bar |
| Stop and target | Stop 1.5 x ATR, target 1 x ATR, ATR taken on the signal bar and fixed for the trade |
| Exit | Stop, target, or an opposite signal (exit and reverse at the next open), as in the source script. One position per pair |
| Win | Net result above zero. R = the stop distance (1.5 ATR), so a target hit is +0.667R before costs |
| Costs | 1.2 pips round trip, assumed. Sensitivity at 0 and 3.0 pips. Overnight financing (swap) not included |
| Path rule | Hour by hour. An hour that touches both stop and target counts as a stop |
| Period R | 1 Jan 2018 to 14 Aug 2020: the source's own period according to its code. Replication, not decisive |
| Period T | 15 Aug 2020 to 5 Nov 2026: data the source had not seen. Decisive |
| Data | MT5 D1 and H1 exports from one broker. 21 of the 28 pairs; the other 7 (AUDNZD, AUDCAD, AUDCHF, USDCAD, CADCHF, CADJPY, AUDJPY) only had data from January 2025 on this server and were dropped before the run |
| Run | 6 November 2026, variant 1 of 1 |

## Replication of the source (period R, not decisive)

The script reproduces the spreadsheet closely.

| | Measured | Source |
|---|---|---|
| Correlation of the 105 cells (21 pairs x 5 signals) | 0.87 | |
| Average win rate MACD line zero cross, same 21 pairs | 63.34% | 63.38% |
| Average win rate signal line zero cross, same 21 pairs | 63.18% | 62.83% |
| The 90% cell (one pair, MACD line zero cross) | 15 of 17 = 88.2% | 16 of 17 = 94.12% |

In this period the MACD line signal ranked at the 97.2nd percentile of the coin flip and the signal line at 95.2 (1.2 pip costs). The hypothesis treats this period as replication only, because it is the period the source chose and published.

## Result (period T, decisive)

1.2 pip costs.

| Signal | Trades | Win rate (95%) | Mean net R (95%, day bootstrap) | Profit factor | Coin flip percentile |
|---|---|---|---|---|---|
| MACD line crosses zero | 1,281 | 58.5% (55.7 to 61.1) | +0.018 (-0.029 to +0.064) | 1.05 | **88.8** |
| Signal line crosses zero | 914 | 59.8% (56.6 to 63.0) | +0.002 (-0.053 to +0.057) | 1.01 | **84.7** |

The coin flip (Null A, 10,000 runs): same entry days, same ATR stop and target, same horizon, random direction.

| Costs | MACD line: mean R / percentile | Signal line: mean R / percentile |
|---|---|---|
| 0 pips | +0.028 / 89.4 | +0.013 / 84.5 |
| 1.2 pips | +0.018 / 88.8 | +0.002 / 84.7 |
| 3.0 pips | +0.002 / 88.4 | -0.013 / 84.6 |

The 90% pair, MACD line zero cross: 32 of 59 = 54.2% (95%: 41.7% to 66.3%). Fewer than 100 trades, so by the fixed rules this is reported but not judged on its own.

## By year (period T)

| Year | MACD line: trades / win rate / mean R | Signal line: trades / win rate / mean R |
|---|---|---|
| 2020 (from Aug) | 87 / 54.0% / -0.036 | 63 / 52.4% / -0.113 |
| 2021 | 228 / 54.8% / -0.026 | 134 / 62.7% / +0.047 |
| 2022 | 186 / 59.1% / +0.018 | 142 / 57.0% / -0.034 |
| 2023 | 191 / 62.3% / +0.063 | 156 / 65.4% / +0.087 |
| 2024 | 195 / 68.7% / +0.175 | 145 / 67.6% / +0.115 |
| 2025 | 208 / 49.5% / -0.134 | 145 / 46.2% / -0.211 |
| 2026 (to Nov) | 186 / 59.7% / +0.055 | 129 / 63.6% / +0.064 |

## Other signals (period T, not decisive)

| Signal | Trades | Win rate | Mean net R | Coin flip percentile |
|---|---|---|---|---|
| Continuation | 915 | 59.0% | -0.018 | 29.2 |
| Reversal | 1,657 | 62.0% | +0.029 | 90.1 |
| Histogram | 2,805 | 53.5% | -0.003 | 52.0 |

## Script check on noise

24 synthetic random walks, 28 pairs each, D1 from 2010 and H1 from 2015, no edge by construction. Per-set results in `noise_24sets.txt`.

| On noise | Median | Range |
|---|---|---|
| Win rate, MACD line, a period as long as period R | 58.0% | 53.8% to 65.8% |
| Win rate, signal line, same | 59.9% | 55.2% to 64.7% |
| Win rate, MACD line, period T | 57.8% | 55.8% to 59.4% |
| Win rate, signal line, period T | 58.5% | 56.2% to 61.4% |
| Best of 140 cells (28 pairs x 5 signals), period R | 87.7% | 82.6% to 100% |

On pure noise the best of 140 cells reached 90% or more in 8 of 24 sets, and 94.12% or more in 4 of 24. The script reported "not dead" against the coin flip in 1 of 24 sets, in line with a 95th-percentile threshold on two signals. On noise the signal line's percentile had a median of 40.3, so for that signal the test may lean strict rather than lenient; 24 sets are too few to tell.

One difference with the source: the source averages 28 per-pair win rates, the script pools all trades. On the 21 pairs both ways of averaging give similar numbers (see the replication table).

## Verdict

- 62.54% (MACD line) and 64.25% (signal line): rejected. The upper ends of the 95% intervals in period T are 61.1% and 63.0%.
- Beating a coin flip: rejected for both signals (88.8 and 84.7, threshold 95).
- 90% on one pair: 54.2% on 59 trades in period T. Below 100 trades, reported, not judged.

No parameter variants will be tested.

## Limitations

- One broker, one data source. 21 of the 28 pairs.
- Costs are a fixed assumption. Overnight financing (swap) is not included; trades often last several days.
- The ATR is fixed at the signal bar. The source script may update it every bar.
- Per pair, period T has 31 to 85 trades: too few to judge any single pair.
- The raw price exports are not published. Run the script on your own MT5 exports to reproduce the method; exact numbers will differ by broker.

## Files

| File | Contents |
|---|---|
| `macdatr_trades.csv` | One row per trade, both periods, all five signals, 1.2 pip costs: pair, signal, signal date, entry date, direction, entry price, ATR, exit type, net R, net R if long, net R if short (same horizon, used by the coin flip), period |
| `run01.txt` | Full output of the run, including all 105 cells of period R and the years of period T |
| `noise_24sets.txt` | Script check on 24 random-walk sets |
| `hypothesis-v1.0-dutch.md` | The rules and pass/fail criteria, fixed before the run (Dutch, names of the source removed) |

Nothing here is financial advice. It is a measurement of one rule in one period. Test it yourself and make your own judgment.
