# Breakout of support and resistance, gold 1 hour: results

The idea comes from a strategy book by a seller of automated trading systems (September 2026). The book calls the breakout of support and resistance "the G.O.A.T. of trading systems" and says "it works". It describes the method in words: important levels across several timeframes where price turned before, entry when a candle closes beyond the level, a stop just back inside it, a stop that moves with volatility, "let winners run", intraday on gold. The book also shows backtest figures of the seller's own gold system (2004-2024): win rate 69%, profit factor 2.13, at most 3 losses in a row. The rules of that system are not public.

**This is a reconstruction.** I tested a public translation of the described method, fixed in advance, not the seller's system. A different result can come from my translation. That is why the seller's figures are only shown next to mine, without a verdict.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (binding), with an English version. The published Dutch file differs from the internal one (SHA-256 f39bf6af...) only in a removed first name, a removed reference to a private source file and a removed local path.

## Rule

| | |
|---|---|
| Script | `sr-breakout/sr_breakout.py` in the repository root. Needs pandas, numpy and numba |
| Data | XAUUSD (gold) CFD, M30, one broker, MT5 export, broker time. Same file as the gold test `ma-9-21-gold`. H1, H4 and D1 bars are built from M30 |
| Usable data | From the first month in which every trading day has at least 40 M30 bars: **May 2017**. 30 trading days warm-up |
| Levels | 5-bar turning points on H4 and D1: a high strictly above the two highs before and after (resistance), a low strictly below (support). Active only after the confirming bars have closed. A level expires at its first breakout or after 20 trading days |
| Signal | H1 close above a resistance after a close at or below it (long), mirrored for support (short). Not on the last H1 bar of the day |
| Entry and stop | Close of the signal bar. Stop at the level minus 0.5 ATR(14, H1) for longs, plus for shorts. Minimum stop 1.00 USD |
| Exit | No target. Trailing stop: 2 ATR from the best M30 close since entry, never moving back. Everything closed at the end of the broker day |
| Costs | 0.40 USD per ounce round trip. Sensitivity 0 and 0.80 |
| Path | M30 bar by bar. A bar that opens beyond the stop exits at its open |
| Decisive period | P1: June 2017 to 31 December 2024 |
| Supplement | P2: 1 January 2025 to 5 November 2026. Time filter 09:00-21:00 broker time |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M30 export in the format described in the main README works.

## Noise check first

24 fake markets (10 years of M30 bars, random walk, 15% volatility a year, drift 0 and 8%), 1,000 control runs per set.

| Fake prices | Mean percentile against Null A | Above 95 | Below 5 | Result |
|---|---|---|---|---|
| 6 price steps per M30 bar (`noise_24sets_6steps_failed.txt`) | 38.1 | 0 of 24 | 1 | Failed (uniformity test p = 0.046) |
| 60 price steps per M30 bar (`noise_24sets_60steps.txt`) | 56.4 | 0 of 24 | 0 | Passed (p = 0.147) |

Why the first one failed: with only 6 steps per bar, the fake price jumps over the stop, and an exit exactly at the stop gives that jump away for free. Rule and control both earned about +0.11R per trade on pure noise without costs, which should be 0. The rule's stops sit slightly wider (its ATR at entry is 1.029 times the average), so it got that gift a little less often, which pushed its percentile down. With 60 steps the path is close to continuous and the gift disappears. The rules of the test did not change, only the fake prices. The diagnosis is in `sr-breakout/noise_diagnosis.py`.

## Control (10,000 runs, seed 23)

A random process that walks through time like the rule, one position at a time: after each exit a waiting time drawn from the rule's own waiting times, entry at the close of the next H1 bar, a stop distance drawn from the rule's own stops (as a multiple of ATR), the same trailing stop, day close and costs.

- Null A (decisive): long with the same probability as the rule (52.6% in P1).
- Null B: coin flip.

## Result, P1, June 2017 to 2024 (decisive)

| | Control (Null A) | The rule |
|---|---|---|
| Mean net R per trade | 5% / 50% / 95% of the runs: -0.182 / **-0.108** / -0.026 | **-0.041** (95% bootstrap per trading day: -0.132 to +0.052) |
| Trades | 1,509 per run (median) | 1,569 (2,014 signals, 20 dropped on the minimum stop, the rest fell inside an open trade) |
| Rule's percentile | | **91.2** (Null B: 91.2) |

| | Measured | Seller's own system (shown only for comparison) |
|---|---|---|
| Win rate after costs | 31.7% (95% Wilson: 29.5% to 34.1%) | 69% |
| Profit factor | 0.94 | 2.13 |
| Longest losing streak | 21 (81.4% of the control runs had an equal or shorter one) | 3 |
| Costs 0 / 0.40 / 0.80 USD | +0.096 / -0.041 / -0.178 R | |
| Median stop | 3.31 USD (0.85 ATR) | |
| Best 5% of trades | +474.7R, against a total of -64.8R | |

**Reading, as fixed in advance:**
- C1, the rule makes money: not falsified. The interval includes 0. Profit is not shown either: the mean is negative after costs.
- C2, the breakout picks better moments than chance: **falsified**. The rule did better than 91.2% of the random runs, but the threshold set in advance was 95.

## Supplements (not decisive)

| | Trades | Win rate | Mean net R (95%) | Percentile Null A |
|---|---|---|---|---|
| P2, 2025 to 5 Nov 2026 | 374 | 35.3% | +0.170 (-0.021 to +0.379) | 95.0 |
| P1 with time filter 09:00-21:00 | 1,159 | 32.7% | -0.045 (-0.149 to +0.063) | 87.9 |

P2 looks better. It was fixed in advance as a supplement, because gold rose strongly in 2025 and two good years can come from the market rather than from the rule. It does not change the verdict.

Per year (rule, no time filter):

| Year | Trades | Long % | Win % | Mean R | Sum R |
|---|---|---|---|---|---|
| 2017 | 109 | 50.5 | 30.3 | +0.032 | +3.5 |
| 2018 | 201 | 46.8 | 32.3 | -0.080 | -16.1 |
| 2019 | 203 | 56.2 | 33.5 | +0.079 | +16.0 |
| 2020 | 194 | 57.7 | 33.0 | +0.021 | +4.1 |
| 2021 | 210 | 51.0 | 31.9 | +0.021 | +4.5 |
| 2022 | 218 | 48.2 | 27.5 | -0.263 | -57.4 |
| 2023 | 229 | 49.8 | 30.1 | -0.184 | -42.0 |
| 2024 | 205 | 60.5 | 35.1 | +0.111 | +22.7 |
| 2025 | 199 | 59.8 | 34.7 | +0.248 | +49.4 |
| 2026 | 175 | 45.7 | 36.0 | +0.082 | +14.3 |

## Spot check

Five random trades rebuilt with separate, plain code (`sr-breakout/verify.py`, output `spot_check_5_trades.txt`): entry equals the H1 close, the level is a real H4 turning point known before the entry, the close crosses it, and the replayed exit equals the script's. 5 of 5.

## Limitations

- A reconstruction of a method described in words, not the seller's system. Volume filters were left out (the export has tick volume only).
- One broker, CFD prices, broker time. Usable data starts in May 2017, not 2004.
- Costs are a fixed assumption, not historical spreads.
- The exit at exactly the stop price is slightly optimistic in fast markets.

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md` / `-english.md` | The hypothesis, fixed before the data |
| `noise_24sets_6steps_failed.txt`, `noise_24sets_60steps.txt` | Noise checks |
| `run01.txt` | Full output of the single run |
| `trades_P1_decisive.csv`, `trades_P2_2025_2026.csv` | Every trade (the script writes them as `trades_P1.csv` and `trades_P2.csv`) |
| `spot_check_5_trades.txt` | Output of the spot check |

This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgment and decision. Nothing here is financial advice.
