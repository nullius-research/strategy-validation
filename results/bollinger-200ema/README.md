# Bollinger Bands + 200 EMA: results

The rules come from a video by a trading channel that tests the strategy 100 times by hand on 15-minute EURUSD at a 1.5 reward-to-risk ratio, and reports a 52% win rate and a $1,000 account growing to $1,622.60. An open-source chart script by a third party turns the entry into exact code (Bollinger 20, 2.0 and EMA 200). The test follows that script where the two differ.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (in Dutch, with the source details removed). The script was then checked on 24 sets of synthetic random-walk data before the real run.

## What the claim implies

At a 1.5R target, 52 wins and 48 losses add up to +30R, about +0.30R per trade. That fits the reported $622.60 profit at roughly 2% risk per trade. Without any predictive power, a 1.5R target wins about 40% of the time. The chance of 52 or more winners in 100 trades at a true 40% is about 1%.

## Setup

| | |
|---|---|
| Script | `bollinger-200ema/bb200_control.py` in the repository root |
| Bars | MT5 M15 exports; trade paths walked bar by bar on M15 |
| Indicators | SMA 20 of the close with bands at 2.0 population standard deviations; EMA 200 of the close |
| Long | Low above the EMA 200, low below the lower band, and the previous bar's low was not below the lower band |
| Short | Mirror image |
| Entry | Open of the next bar |
| Stop | Lowest low (long) or highest high (short) of the last 10 bars including the signal bar. The source sets the stop by hand; this is our fixed translation, the same as in the MACD + 200 EMA test. No trade if the stop is closer than 5 pips |
| Target | 1.5R, as in the source. No break-even, no time limit |
| Positions | One open trade per pair at a time |
| Costs | 1.2 pips round trip, assumed. Sensitivity at 0 and 2.0 pips |
| Path rule | A bar that touches both stop and target counts as a stop |
| Data | MT5 M15 exports from one broker. EURUSD (decisive), August 2022 to August 2026, plus nine more pairs |
| Run | 7 November 2026, variant 1 of 1 |

## Result, EURUSD (decisive)

2,893 signals by the script rule. 638 had a stop of at least 5 pips. 573 trades over 418 trading days after the one-at-a-time rule.

| | Measured | Claimed |
|---|---|---|
| Win rate | 37.5% (95%: 33.6% to 41.5%) | 52% |
| Mean net R per trade | −0.214 (95% day bootstrap: −0.316 to −0.111) | about +0.30 |
| Profit factor | 0.703 | |
| Mean R at 0 / 1.2 / 2.0 pip costs | −0.062 / −0.214 / −0.315 | |
| Median stop | 7.7 pips | |
| Longest losing streak | 9 | 5 |

The result is negative even before costs.

## Controls

| Control | 5th to 95th percentile | Rule's percentile |
|---|---|---|
| Null A, coin flip: same entries, random direction, same stop and target, 10,000 runs (decisive) | −0.236 to −0.083 | **11.1** |
| Null B, random bar in the same pair and month on the same side of the EMA 200, trend direction (extra) | −0.229 to −0.059 | 8.6 |

Null B does not count in either direction here. On the 24 synthetic data sets the rule ranked below the 50th percentile of Null B in 22 of 24, so in this test Null B is skewed against the rule. A likely reason is that a band touch sits close to the 10-bar extreme, so the stop is tight and costs weigh more per R than for a random bar. That reason was not tested.

## By year, EURUSD

| Year | Trades | Win rate | Mean net R |
|---|---|---|---|
| 2022 (from Aug) | 86 | 25.6% | −0.498 |
| 2023 | 145 | 35.9% | −0.259 |
| 2024 | 92 | 51.1% | +0.114 |
| 2025 | 178 | 39.3% | −0.161 |
| 2026 (to Aug) | 72 | 33.3% | −0.331 |

2024 alone came close to the claimed 52%. It has 92 trades, below the 100 needed to read a year on its own. On synthetic random walks, where there is nothing to find, one set also produced a single year at 51.5% over 97 trades.

## Other pairs (not decisive)

| Pair | Trades | Win rate | Mean net R | Null A percentile |
|---|---|---|---|---|
| GBPUSD | 762 | 37.5% | −0.208 | 28.7 |
| USDJPY | 1,194 | 38.6% | −0.167 | 21.0 |
| EURJPY | 1,316 | 39.9% | −0.131 | 45.0 |
| USDCHF | 584 | 44.0% | −0.047 | 96.8 |
| USDCAD (from 2025) | 239 | 46.0% | −0.000 | 98.2 |
| NZDUSD | 494 | 41.5% | −0.118 | 90.4 |
| EURGBP | 312 | 38.8% | −0.181 | 52.7 |
| GBPJPY | 1,480 | 38.6% | −0.154 | 75.9 |
| AUDUSD | 515 | 39.2% | −0.177 | 68.2 |

None reaches 52% or a positive result after costs. Two of nine rank above the 95th percentile of the coin flip, both with a net result at or below zero. With nine extra measurements and a 5% threshold, about half a false signal is expected; two is on the high side. Full output in `run01_extra.txt`.

## Script check on noise

On 24 synthetic random walks (M15, four years, EURUSD) the rule averaged a 40.5% win rate (range 36.8% to 44.6%), which is what a 1.5R target gives with no predictive power. Against the coin flip it reported "not dead" in 1 of 24 sets, in line with the 5% error built into a 95th-percentile threshold. Per-set output in `noise_24sets.txt`. Run `make_synthetic.py` and `ruis_24sets.py` to reproduce.

## Verdict

Rejected on all three claims: the 52% win rate, the +0.30R per trade, and beating a coin flip. No parameter variants will be tested.

## Limitations

- The stop is our translation. The source places it by hand per trade. With the fixed 10-bar stop and the 5-pip minimum, 78% of the script's signals were not traded. A different stop rule would give different numbers; it was fixed before the data was seen.
- The entry rule follows a third-party script, not the video directly. The video says "as soon as the price hits" the band; the script also requires that the previous bar did not.
- One broker, one data source, four years. The source tested a different, shorter period.
- Costs are a fixed assumption, not the historical spread per trade. With a median stop of 7.7 pips, 1.2 pips is about 0.16R per trade.
- The raw price exports are not published. Run the script on your own MT5 exports to reproduce the method; exact numbers will differ by broker.

## Files

| File | Contents |
|---|---|
| `bb200_trades_eurusd.csv` | One row per EURUSD trade: pair, entry time (UTC), direction, entry, stop distance, gross R, gross R of the mirrored trade, net R at 0, 1.2 and 2.0 pips |
| `run01_eurusd.txt` | Full output of the decisive run |
| `run01_extra.txt` | Full output for the nine other pairs |
| `noise_24sets.txt` | Script check on 24 random-walk sets |
| `hypothesis-v1.0-dutch.md` | The rules and pass/fail criteria, fixed before the run (Dutch) |

Nothing here is financial advice. It is a measurement of one rule in one period. Test it yourself and make your own judgment.
