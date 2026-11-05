# Stochastic + RSI + MACD: results

The rules come from a video by a trading channel that tests the strategy 100 times and reports a 56% win rate at a 1.5 reward-to-risk ratio on 30-minute EURUSD, with a profit of about 28% at 2% risk per trade.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (in Dutch). The script was then checked on 24 sets of synthetic random-walk data before the real run.

## Two numbers that do not fit together

This was visible before the test. At a 1.5R target, 56 wins and 44 losses add up to +40R. At 2% risk per trade that is roughly +80% without compounding, not 28%. A gain of 28% is +14R, which at 1.5R corresponds to a win rate of about 45.6%. The video does not say which of the two numbers is off. Possible explanations include costs, a different risk per trade, or exits that differed from the stated rule. To stay no stricter than the source, the test uses the lower claim (+0.14R per trade) for C2.

## Setup

| | |
|---|---|
| Script | `stoch-rsi-macd/srm_control.py` in the repository root |
| Bars | M30 built from MT5 M15 exports; trade paths walked on M15 |
| Indicators | Stochastic %K 14, smoothing 1, %D 3, levels 20 and 80. RSI 14 at level 50. MACD 12, 26, 9. The source gives no settings, so the TradingView defaults are used |
| Setup | Long setup when %K and %D are both below 20 on the same bar. Cancelled when both go above 80 (that arms the short). Expires after 48 M30 bars (one trading day) |
| Long | Within the setup, MACD crosses above its signal line and RSI is above 50 |
| Short | Mirror image |
| Entry | Open of the next M30 bar |
| Stop | The most recent confirmed 5-bar swing low below entry (swing high for shorts), within the last 50 bars. The source says "nearest swing low"; this is the fixed translation. No trade if the stop is closer than 5 pips |
| Target | 1.5R, as in the source. No break-even, no time limit |
| Positions | One open trade per pair at a time |
| Costs | 1.2 pips round trip, assumed. Sensitivity at 0 and 2.0 pips |
| Path rule | Bar by bar on M15. A bar that touches both stop and target counts as a stop |
| Data | MT5 M15 exports from one broker. EURUSD (decisive) plus eight more pairs, August 2022 to August 2026. USDCAD only from January 2025 |
| Run | 5 November 2026, variant 1 of 1 |

## Result, EURUSD (decisive)

583 trades over 492 trading days, 12.1 per month.

| | Measured | Claimed |
|---|---|---|
| Win rate | 41.7% (95%: 37.7% to 45.7%) | 56% |
| Mean net R per trade | −0.019 (95%: −0.118 to +0.081) | about +0.14 |
| Profit factor | 0.970 | |
| Mean R at 0 / 1.2 / 2.0 pip costs | +0.042 / −0.019 / −0.059 | |
| Median stop | 22.1 pips | |

At a 1.5R target, the break-even win rate is 40% before costs. The rule lands at 41.7%.

## Controls

| Control | 5th to 95th percentile | Rule's percentile |
|---|---|---|
| Null A, coin flip: same entries, random direction, same stop and target, 10,000 runs (decisive) | −0.126 to +0.024 | **74.4** |
| Null B, random bar in the same pair and month on the same side of RSI 50, RSI direction (extra) | −0.195 to −0.036 | 97.5 |

Null B is not evidence that the stochastic and MACD add anything. On the 24 synthetic data sets, where there is nothing to find, the rule ranked above the 95th percentile of Null B in 4 of 24 sets and higher against Null B than against the coin flip in 19 of 24. Null B is skewed in favour of the rule, as it was in the MACD + 200 EMA test. The rule's own result is negative after costs.

## By year, EURUSD

| Year | Trades | Win rate | Mean net R |
|---|---|---|---|
| 2022 (from Aug) | 53 | 45.3% | +0.094 |
| 2023 | 157 | 35.0% | −0.188 |
| 2024 | 142 | 43.7% | +0.020 |
| 2025 | 148 | 44.6% | +0.061 |
| 2026 (to Aug) | 83 | 43.4% | +0.021 |

2022 and 2026 are below 100 trades each and should not be read on their own.

## Stop capped at 0.15%

After its backtest the source suggests capping the stop at 0.15%. That variant was fixed in the hypothesis before the run and is not decisive: 850 trades, win rate 39.5%, −0.094R per trade. Worse than without the cap.

## Other pairs (not decisive)

| Pair | Trades | Win rate | Mean net R | Null A percentile |
|---|---|---|---|---|
| EURJPY | 517 | 40.6% | −0.018 | 50.5 |
| GBPUSD | 576 | 40.8% | −0.023 | 56.2 |
| GBPJPY | 599 | 39.4% | −0.041 | 28.6 |
| USDJPY | 533 | 37.0% | −0.114 | 4.1 |
| USDCHF | 591 | 36.5% | −0.152 | 10.8 |
| USDCAD (from 2025) | 254 | 35.4% | −0.179 | 1.7 |
| NZDUSD | 596 | 37.6% | −0.126 | 16.3 |
| EURGBP | 574 | 37.5% | −0.159 | 46.6 |
| Together | 4,240 | 38.3% | −0.097 | 1.7 |

All eight are negative after costs. On EURGBP the median stop is 13.8 pips, so the 1.2 pip cost takes a larger share of each trade.

## Script check on noise

On 24 synthetic random walks (M15, four years, EURUSD) the rule averaged a 40.3% win rate (range 37.2% to 43.8%), which is what a 1.5R target gives with no predictive power. Against the coin flip it reported "not dead" in 1 of 24 sets, in line with the 5% error built into a 95th-percentile threshold. Per-set output in `noise_24sets.txt`. Run `make_synthetic.py` and `ruis_24sets.py` to reproduce.

## Verdict

Rejected on all three claims: the 56% win rate, the +0.14R per trade, and beating a coin flip. No parameter variants will be tested.

## Limitations

- One broker, one data source, four years. The source tested a different period of 134 days.
- Costs are a fixed assumption, not the historical spread per trade.
- Settings, levels, the swing definition and the one-day setup window are translations of a verbal rule. Different choices would give different numbers; they were fixed before the data was seen.
- The raw price exports are not published. Run the script on your own MT5 exports to reproduce the method; exact numbers will differ by broker.

## Files

| File | Contents |
|---|---|
| `srm_trades.csv` | One row per trade, all nine pairs: pair, entry time (UTC), direction, entry, stop distance, gross R, gross R of the mirrored trade, net R at 0, 1.2 and 2.0 pips |
| `run01.txt` | Full output of the run |
| `noise_24sets.txt` | Script check on 24 random-walk sets |
| `hypothesis-v1.0-dutch.md` | The rules and pass/fail criteria, fixed before the run (Dutch) |

Nothing here is financial advice. It is a measurement of one rule in one period.
