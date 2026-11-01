# MACD + 200 EMA (Trading Rush): results

Null Test 04. The rules come from Trading Rush, "I risked MACD Trading Strategy 100 TIMES" (tradingrush.net), which reports 62 winners out of 100 trades at a 1.5 reward-to-risk ratio on 30-minute EURUSD and EURJPY charts.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (in Dutch). The script was then checked on 24 sets of synthetic random-walk data before the real run.

## Setup

| | |
|---|---|
| Script | `macd-200ema/macd_control.py` in the repository root |
| Bars | M30 built from MT5 M15 exports; trade paths walked on M15 |
| Indicators | MACD(12, 26, 9) and EMA 200 on close. The source gives no MACD settings, so the default is used |
| Long | MACD crosses above its signal line, both below zero, close above EMA 200 |
| Short | Mirror image |
| Entry | Open of the next M30 bar |
| Stop | Lowest low (long) or highest high (short) of the last 10 M30 bars. The source says "below the pullback"; this is the fixed translation. No trade if the stop is closer than 5 pips |
| Target | 1.5R, as in the source's backtest. No break-even, no time limit |
| Positions | One open trade per pair at a time |
| Costs | 1.2 pips round trip, assumed. Sensitivity at 0 and 2.0 pips |
| Path rule | Bar by bar on M15. A bar that touches both stop and target counts as a stop |
| Data | MT5 M15 exports from one broker, EURUSD and EURJPY, August 2022 to August 2026 |
| Run | 1 November 2026, variant 1 of 1 |

## Result

1,050 trades (EURUSD 528, EURJPY 522) over 677 trading days.

| | Measured | Claimed |
|---|---|---|
| Win rate | 40.9% (95%: 37.9% to 43.8%) | 62% |
| Mean net R per trade | −0.035 (95%: −0.109 to +0.040) | about +0.5 |
| Profit factor | 0.944 | |
| Mean R at 0 / 1.2 / 2.0 pip costs | +0.021 / −0.035 / −0.073 | |
| Median stop | 26.3 pips | |

At a 1.5R target, the break-even win rate is 40% before costs. The rule lands at 40.9%.

## Controls

| Control | 5th to 95th percentile | Rule's percentile |
|---|---|---|
| Null A, coin flip: same entries, random direction, same stop and target, 10,000 runs (decisive) | −0.121 to −0.006 | **79.2** |
| Null B, random bar in the same pair and month on the same side of the EMA 200, trend direction (extra) | −0.161 to −0.038 | 95.5 |

Null B is not evidence that the MACD cross adds anything. On the synthetic data, where there is nothing to find, the Null B band also sat below the coin-flip band in every set; random bars more often get tight stops and so pay more costs in R. The rule's own result is negative after costs.

## By year

| Year | Trades | Win rate | Mean net R |
|---|---|---|---|
| 2022 (from Aug) | 78 | 44.9% | +0.081 |
| 2023 | 258 | 39.9% | −0.055 |
| 2024 | 262 | 43.9% | +0.032 |
| 2025 | 286 | 40.6% | −0.039 |
| 2026 (to Aug) | 166 | 36.1% | −0.158 |

## Script check on noise

On 24 synthetic random walks (M15, four years, two pairs), the script reported "not dead" against the coin flip in 2 of 24 sets (8%), with percentiles spread evenly between 0 and 100. That matches the 5% error built into a 95th-percentile threshold. Run `make_synthetic.py` and `macd_control.py --broker-offset 0` to reproduce.

## Verdict

Rejected on all three claims: the 62% win rate, the +0.5R per trade, and beating a coin flip. No parameter variants will be tested.

## Limitations

- One broker, one data source, four years.
- Costs are a fixed assumption, not the historical spread per trade.
- The stop rule is a translation of "below the pullback". A different translation would give different numbers; it was fixed before the data was seen.
- The source skipped three trades it called unclear. Here every signal counts.
- The raw price exports are not published. Run the script on your own MT5 exports to reproduce the method; exact numbers will differ by broker.

## Files

| File | Contents |
|---|---|
| `macd_trades.csv` | One row per trade: pair, entry time (UTC), direction, entry, stop distance, gross R, gross R of the mirrored trade, net R at 0, 1.2 and 2.0 pips |
| `run01.txt` | Full output of the run |
| `hypothesis-v1.0-dutch.md` | The rules and pass/fail criteria, fixed before the run (Dutch) |

Research only. Not financial advice. No recommendation to trade anything.
