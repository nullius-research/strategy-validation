# MA 9/21 crossover + 200 MA on gold: results

The rules come from a trading video with an article (November 2025). Gold, long only. On the daily chart, price must be above a 9-period moving average. On the 30-minute chart, go long when the 9 crosses above the 21, with the whole candle above both averages, and price and both averages above the 200. Target 1.5 times the stop. The source reports a win rate of about 58% over 100 trades, taken only in what it calls a good market. It does not give a stop rule or a test period.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` and `hypothesis-v1.1-dutch.md` (in Dutch, with the source details removed). Version 1.1 changes only the control group, after version 1.0 failed the check on random data (see below). Rules, periods and pass/fail criteria are the same in both.

## What the claim implies

At a 1.5R target, 58 wins and 42 losses add up to +45R, about +0.45R per trade before costs. Break-even at 1.5R is 40%. On a random walk with no drift, a 1.5R target also wins about 40% of the time.

## Setup

| | |
|---|---|
| Script | `ma-9-21-gold/ma921_control.py` in the repository root |
| Bars | MT5 XAUUSD M30 export from one broker, 1998 to 5 November 2026. Complete 30-minute data only from 1 May 2017 (first month where every trading day has at least 40 bars); the test starts there |
| Averages | EMA 9, 21 and 200 on the 30-minute close. Daily filter: the previous completed day closed above its daily EMA 9 |
| Signal | EMA 9 crosses above EMA 21 on this bar; the bar's low is above both; close, EMA 9 and EMA 21 above EMA 200; daily filter true |
| Entry | Close of the signal bar |
| Stop | Lowest low of the last 10 bars including the signal bar. The source gives no stop; this is our fixed translation, the same as in our MACD + 200 EMA and Bollinger + 200 EMA tests. No trade if the stop is under 1.00 USD |
| Target | 1.5R, as in the source |
| Positions | One at a time; held overnight and over weekends |
| Costs | 0.40 USD per ounce round trip, assumed. Sensitivity at 0 and 0.80. The median spread in the export is 0.02 USD, so 0.40 is on the generous side |
| Path rule | Bar by bar. A bar that touches both stop and target counts as a stop. A bar that opens beyond the stop exits at its open |
| Decisive period | P1: May 2017 to December 2023, plus January to November 2026. The years 2024 and 2025, when gold rose strongly and the source most likely tested, are reported separately as P0 |
| Run | Variant 1 of 1 |

The hand-drawn "bad market" boxes in the source cannot be reproduced. This test measures the mechanical part of the rule only. A lower win rate can therefore also come from leaving out that hand selection.

## Result, P1 (decisive)

402 signals, none dropped by the minimum stop, 310 trades after the one-at-a-time rule.

| | Measured | Claimed |
|---|---|---|
| Win rate | 42.3% (95%: 36.9% to 47.8%) | about 58% |
| Mean net R per trade | −0.017 (95% day bootstrap: −0.157 to +0.125) | about +0.45 before costs |
| Profit factor | 0.97 | |
| Mean R at 0 / 0.40 / 0.80 USD costs | +0.050 / −0.017 / −0.085 | |
| Median stop | 7.01 USD | |
| Best 5% of trades | +23.8R, against a total of −5.3R | |
| Longest losing streak | 7 | |

## Control group

A long-only rule on a market that rose over the period gets a tailwind from the trend alone. A coin flip is the wrong control here, because it is half short. The control is long, in the same trend context, without the crossover.

It is a random process that moves through time like the rule, one position at a time. After each exit it waits a number of bars drawn from the rule's own waiting times, then goes long on the next allowed bar. The stop distance is drawn from the rule's own stops, with the same 1.5R target, the same costs and the same path rules. 10,000 runs.

| Control | 5th / 50th / 95th percentile, mean net R | Rule's percentile |
|---|---|---|
| Null A: allowed bars have the same trend context (daily filter, close and both averages above the 200), no crossover, no candle rule (decisive) | −0.174 / −0.046 / +0.085 | **64.8** |
| Null B: all bars allowed (extra) | −0.170 / −0.053 / +0.067 | 68.9 |

The crossover adds nothing measurable on top of the trend filter it sits in.

## 2024 to mid-November 2025 (P0, not decisive)

105 trades, win rate 45.7% (95%: 36.5% to 55.2%), mean net R +0.108 (−0.125 to +0.352), profit factor 1.19, median stop 15.05 USD. Against Null A: percentile 27.7. Random long entries in the same trend did better than the rule in this period: the trend carried the result, not the crossover.

## By year (P1 and P0 together)

| Year | Trades | Win rate | Mean net R |
|---|---|---|---|
| 2017 (from Jun) | 20 | 40.0% | −0.098 |
| 2018 | 43 | 41.9% | −0.060 |
| 2019 | 53 | 35.8% | −0.204 |
| 2020 | 32 | 53.1% | +0.280 |
| 2021 | 33 | 24.2% | −0.447 |
| 2022 | 44 | 45.5% | +0.081 |
| 2023 | 49 | 53.1% | +0.267 |
| 2024 | 52 | 48.1% | +0.158 |
| 2025 (to 14 Nov) | 53 | 43.4% | +0.060 |
| 2026 (to 19 Oct) | 36 | 41.7% | −0.022 |

No year has 100 trades, so no single year can be read on its own.

## Script check on noise, and why the control group changed

Before the real run, the script was run on 24 synthetic random walks (10 years of 30-minute bars, 15% yearly volatility, drift 0% and 8%). On random data the rule should not beat its control.

Version 1.0 used a different control: random non-overlapping trades drawn from the trend bars, each with its own 10-bar stop. On noise the rule scored above the 95th percentile in 13 of 24 sets (mean percentile 88.0). The check failed. Two causes were measured: the rule's stops were larger than the random trades' stops, so costs weighed less per R, and drawing trades without overlap favoured short trades, which lose more often. Output in `noise_24sets_v1.0_failed.txt`.

Version 1.1 uses the sequential control described above. On the same 24 sets: mean percentile 46.0, above 95 in 0 of 24, below 5 in 1 of 24, mean win rate 40.4%. Output in `noise_24sets_v1.1.txt`. Only then was the real data opened.

## A note on reproducibility

The script that produced the first real run on 9 November 2026 was not saved. It was rebuilt the next day from the version 1.0 script and the saved version 1.1 check. The rebuilt script reproduces the noise check byte for byte, and on the real data it gives identical rule results and identical trade lists. Only the control in P1 differs slightly: the first run placed the rule at percentile 63.9 against Null A, the rebuilt script at 64.8. The difference comes from how a waiting time across the excluded 2024-2025 period is handled, which could not be recovered. Every variant tried gave 64.1 to 64.8. The numbers above are from the rebuilt script, so they can be reproduced with the code in this repository.

## Verdict

Rejected on the win-rate claim (the upper bound 47.8% is below 58%) and on the control (percentile 64.8, an edge needs above 95). The profit claim of about +0.45R per trade is far outside the measured range, but a mean of zero cannot be excluded either, so on that criterion the result is not rejected by the pre-set rule. No parameter variants will be tested.

## Limitations

- The source selected its trades partly by hand. That selection cannot be reproduced, so this is a test of the mechanical rule, not of the source's full method.
- The stop is our translation. The source gives none. A different stop would give different numbers; it was fixed before the data was seen.
- The source does not say which period it tested. 2024-2025 is our assumption for its period.
- One broker, one data source, 30-minute bars from May 2017 only.
- Costs are a fixed assumption, not the historical spread per trade.
- The raw price export is not published. Run the script on your own MT5 export to reproduce the method; exact numbers will differ by broker.

## Files

| File | Contents |
|---|---|
| `trades_P1_decisive.csv` | One row per decisive trade: entry and exit time (broker time), entry, stop, stop distance in USD, gross R, net R at 0.40 USD, open at end |
| `trades_P0_2024_2025.csv` | Same columns, 2024 to 14 November 2025 |
| `run01.txt` | Full output of the run with the rebuilt script |
| `noise_24sets_v1.1.txt` | Script check on 24 random-walk sets, version 1.1 control |
| `noise_24sets_v1.0_failed.txt` | The failed check with the version 1.0 control |
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.1-dutch.md` | Rules and pass/fail criteria, fixed before the run (Dutch) |

Usage: `python ma921_control.py XAUUSD_M30.csv` for the real run, `python ma921_control.py --synthetic 24` for the noise check.

Nothing here is financial advice. It is a measurement of one rule in one period. Test it yourself and make your own judgment.
