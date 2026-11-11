# RSI(2) pullback on the S&P 500: results

The rule comes from a 2007 article by a trading author. It reports that the rule was right on 84.31% of 102 trades in the S&P 500 index from January 1995 to December 2006, for 1,013.90 index points. The article gives no stop and says nothing about costs.

The hypothesis was written and fixed before any price data was opened: `hypothesis-v1.0-dutch.md` (in Dutch; the source name and private file paths are removed, nothing else changed). The script was then checked on 24 sets of synthetic random-walk data before the real run.

What makes this test different from the earlier ones: the source's test period has a fixed end date. Everything from 2007 on is data the source could not have seen. That period decides.

## Rule

| | |
|---|---|
| Script | `rsi2-pullback/rsi2_control.py` in the repository root |
| Market | S&P 500 price index (^GSPC), daily closes, Yahoo Finance |
| Filter | Close above its 200-day simple moving average |
| Signal | 2-period RSI below 65 two days ago, lower the day before, lower again today |
| Entry | Close of the signal day |
| Exit | Close of the first later day on which the 2-period RSI closes above 75. No stop, no time limit |
| RSI | Wilder's RSI, period 2. The source does not say which RSI it used |
| Positions | One at a time; a signal during an open trade is skipped |
| Costs | 2 basis points round trip, assumed. Sensitivity at 0 and 4 bp |

The prices are not in this repository. The S&P 500 series used is ^GSPC from Yahoo Finance, 4 January 1993 to 30 October 2026, 8,516 days.

## Step 1: can the calculation reproduce the source? (1995 to 2006)

| | Measured | Source |
|---|---|---|
| Trades | 101 | 102 |
| Winners | 85 | 86 |
| Win rate | 84.16% | 84.31% |
| Index points | 998.68 | 1,013.90 |

Close enough to say the rule is coded as the source meant it. This step does not decide anything.

## Step 2: the decisive period, 3 January 2007 to 30 October 2026

| | Measured |
|---|---|
| Trades | 166 |
| Win rate | 80.72% (95%: 74.1% to 86.0%) |
| Mean net return per trade | +0.548% (95% bootstrap: +0.130% to +0.863%) |
| Profit factor | 2.19 |
| Mean holding time | 4.8 trading days (longest 22) |
| Worst trade | −23.28% (24 Feb to 25 Mar 2020) |
| Deepest drop inside a trade | −30.64% (same trade) |
| Best 5% of trades (8) | +25.8% of the +91.0% summed return |
| Rule, compounded | +134.9% |
| Buy and hold, same period | +435.1% |

The rule is in the market on roughly one day in six. Buy and hold is shown for context, not as a control.

## Controls (10,000 runs, seed 23)

| Control | 5th / 50th / 95th percentile | Rule's percentile |
|---|---|---|
| Null A: random entry day among days above the 200-day average, same exit rule, same number of trades, one at a time (decisive) | +0.060% / +0.256% / +0.420% | **99.9** |
| Null B: random entry day, no filter, same exit rule (extra; this is the control used in the buy-the-dip test) | +0.116% / +0.362% / +0.593% | 90.5 |

At 0 and 4 bp the percentile against Null A stays at 99.9.

**A known skew, recorded before the real run.** On 48 synthetic random walks (no edge by construction), the rule ranked on average at the 32nd and 42nd percentile of Null A in two rounds of 24, never above 95. So Null A is skewed against the rule: it does not create false edges, but it can hide a small real one. A version with matched holding times (Null C) was tried and rejected because it was skewed the other way: on noise it averaged the 63rd percentile and put 2 of 24 above 95. The reading rule was fixed before the real run: above 95 not falsified, 80 to 95 "not shown", below 80 dead. See `noise_24sets.txt`.

## Verdict against the pre-registered criteria

| Claim | Falsified if | Result |
|---|---|---|
| C1: 84.31% correct | upper bound of the win-rate interval below 84.31% | Not falsified (upper bound 86.0%) |
| C2: the rule makes money | upper bound of the mean net return below 0 | Not falsified (lower bound +0.130%) |
| C3: the entry beats random | mean net return not above the 95th percentile of Null A | Not falsified (99.9) |

Not falsified is not the same as "works". It means this test, in this period, did not find the claim to be false.

## By year

| Year | Trades | Win rate | Mean net return |
|---|---|---|---|
| 2007 | 8 | 87.5% | +1.080% |
| 2009 | 5 | 100.0% | +1.081% |
| 2010 | 5 | 80.0% | +0.517% |
| 2011 | 11 | 72.7% | +0.090% |
| 2012 | 13 | 76.9% | +0.864% |
| 2013 | 9 | 77.8% | +0.836% |
| 2014 | 8 | 75.0% | +0.243% |
| 2015 | 11 | 72.7% | +0.475% |
| 2016 | 8 | 87.5% | +0.952% |
| 2017 | 10 | 90.0% | +0.537% |
| 2018 | 11 | 54.5% | −0.203% |
| 2019 | 7 | 71.4% | +0.325% |
| 2020 | 7 | 71.4% | −2.369% |
| 2021 | 8 | 87.5% | +1.778% |
| 2022 | 2 | 50.0% | −0.606% |
| 2023 | 9 | 77.8% | +0.852% |
| 2024 | 12 | 100.0% | +1.214% |
| 2025 | 10 | 90.0% | +0.298% |
| 2026 (to 30 Oct) | 12 | 91.7% | +1.067% |

No trades in 2008: the index closed below its 200-day average on all 253 trading days that year.

## Extra: Nasdaq 100, same period and rules

172 trades, win rate 78.5%, mean net return +0.830% per trade, percentile 100.0 against Null A and 98.0 against Null B, worst trade −10.18%. Reported for context; it does not decide.

## Follow-up: executed at the next open (added 11 November 2026)

A reader pointed out that buying and selling at the exact close is hard to do in practice, since the signal is only known once the market has closed. So the same rule was run again with fills a reader can actually get: buy at the open of the day after the signal, sell at the open of the day after the RSI closes above 75. The random-entry control was moved to the same fills. Signals, exit rule, filter, period, costs and pass/fail criteria are unchanged. The hypothesis was written and fixed before the opening prices were looked at: `next-open/hypothesis-next-open-v1.0-dutch.md` (Dutch). The close-to-close results above stay as they are.

| 3 Jan 2007 to 30 Oct 2026, 2 bp | At the close (above) | At the next open |
|---|---|---|
| Trades | 166 | 166 (same signals) |
| Win rate | 80.72% (74.1 to 86.0) | 78.92% (72.1 to 84.4) |
| Mean net return per trade | +0.548% | +0.551% (95% +0.133 to +0.870) |
| Profit factor | 2.19 | 2.20 |
| Percentile vs Null A | 99.9 | 100.0 |
| Worst trade | −23.28% | −22.79% |
| Rule compounded / buy and hold | +134.9% / +435.1% | +136.0% / +435.1% |

On the rule's own trades, the overnight move from the signal close to the next open averaged +0.029% on entry nights and +0.031% on exit nights. The two roughly cancel, which is why the result barely moves.

Verdict against the same criteria: not falsified on C1 (upper bound 84.4% is above the claimed 84.31%, just), C2 and C3.

Checks before the real run:
- With every open set equal to the previous close, the next-open script reproduces the 166 close-to-close trades and returns exactly.
- Noise check on 24 synthetic random walks with a separate overnight part (30% of the variance), 5,000 days each: mean percentile against Null A 39.1, 0 of 24 above 95. The control does not favour the rule.
- Data check: closes identical to the series used above on all 5,492 shared days. In 2007 to 2026, 4.1% of opens equal the previous close (mostly 2007 and 2011 to 2013), none outside the day's range.
- Five random trades recomputed by hand from the prices: 5 of 5 equal.

Opening prices of an index are not tradable prices; an index fund or future opens at a slightly different level. This is closer to what a reader can do, not identical to it.

Script `rsi2-pullback/rsi2_next_open.py`. Output, trades and checks in `next-open/`. The price data is not in this repository; the same Yahoo chart URL with `period1=1104537600&period2=1793491200` returns it.

## Limitations

- One index, one data source, price index without dividends.
- Costs are an assumption, not measured fills. Entry and exit at the exact close are an idealisation; see the next-open follow-up above.
- No stop: the worst trade lost 23% and was down 31% before it closed. The average hides that.
- The rule is similar to the buy-the-dip rule tested earlier (buying short declines in an index). The two results are not independent evidence.
- Null A is skewed against the rule (see above).

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md` | Pre-registered hypothesis, fixed before any price data was opened |
| `noise_24sets.txt` | Check on 24 synthetic random walks |
| `run_P0_sp500_1995_2006.txt` | Reproduction of the source period |
| `run_P1_sp500_2007_2026.txt` | Decisive run |
| `run_P1_nasdaq100_2007_2026.txt` | Extra run |
| `trades_*.csv` | Every trade: entry and exit date, closes, net return, deepest drop inside the trade |

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade. Test it yourself and make your own judgment.
