# Morning star with a trend filter, gold 1 hour, with a prop firm challenge: results

The idea comes from a short social media video (7 November 2026). It describes a candle pattern on gold, 1 hour: when price is above the 14 and the 200 moving average and the candles form a morning star ("a falling candle, a small candle, then a strong rising candle"), buy "when the price goes higher than the third candle", stop at the lowest point of the three candles, target 2 times the risk; shorts mirrored. Risk 1% per trade. The video reports: "In 5 years of gold, it took 512 trades and 43% won", worst day -3.6%, maximum drawdown 7.5%, and "81% of 1,000 simulated [firm A] challenges passed" (a two-phase prop firm evaluation), with a median of 155 days to pass.

**This is a reconstruction.** I tested a public translation of the words in the video, fixed in advance, not the source's own code (available only with an account, which I chose not to create). A different result can come from my translation. That is why the source's 512 trades, 43% and 7.5% are only shown next to mine, without a verdict.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md`, with an English version. The noise check of v1.0 failed (see below); v1.1 changed only the fake prices of the noise check, not the rules. The binding version is v1.1 (`hypothesis-v1.1-dutch.md`; the Dutch files are binding, the English ones are translations). The published files differ from the internal ones (v1.1 SHA-256 46ff91c2..., v1.0 df2d64a2...) only in removed names of the source and the firm, a removed first name, a removed private file reference and a removed local path.

## Rule

| | |
|---|---|
| Script | `morning-star-gold/morning_star.py` (rules, controls, challenge, self-test, noise check) and `morning-star-gold/run_real.py` (periods and report) in the repository root. Needs pandas, numpy and numba |
| Data | XAUUSD (gold) CFD, M30, one broker, MT5 export, broker time. Same file as the gold tests `ma-9-21-gold` and `sr-breakout`. H1 bars are built from M30; every trade path is walked on M30 |
| Usable data | From the first month in which every trading day has at least 40 M30 bars: **May 2017**. The first 200 H1 bars are warm-up |
| Moving averages | Simple, 14 and 200, on H1 closes (choice K1-A; the video does not say which kind) |
| Pattern | On H1 bars t-2, t-1, t. Morning star: t-2 falling; body of t-1 at most 1/3 of the body of t-2; t rising and closing above the middle of the body of t-2. Evening star mirrored (choice K2-A) |
| Filter | Long only if the close of t is above both averages; short only if below both |
| Entry | Buy stop at the high of t (sell stop at the low), valid only during the next H1 bar (choice K3-A). An M30 bar that opens beyond the level enters at its open |
| Stop and target | Stop at the lowest low of the three candles (short: highest high). Target 2 × the risk. No trade if the stop is below 1.00 USD. No time exit. One position at a time |
| Costs | 0.40 USD per ounce round trip. Sensitivity 0 and 0.80. The broker's median spread in the data is 0.00 to 0.05 USD |
| Path | M30 bar by bar. In the entry bar only the stop counts. A bar that touches stop and target counts as stop. A bar that opens beyond the stop or the target exits at its open |
| Decisive period | P1: 6 November 2021 to 5 November 2026 (the "5 years of gold") |
| Supplement | P0: May 2017 to 5 November 2021. Per year. The non-chosen alternatives K1-B to K4-B |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M30 export in the format described in the main README works.

## Prop firm challenge (fixed in advance)

Two phases on a $100,000 account, rules as published by the firm on 21 November 2026: phase 1 target 10%, phase 2 target 5% (on closed balance), at least 4 trading days with an entry per phase, maximum daily loss $5,000 below the balance at the start of the day (on equity including open loss), maximum loss: equity below $90,000. Risk $1,000 per trade, as in the video, costs included. 1,000 challenges, each starting on a random trading day of P1 (not in the last year); still running after 365 days = not finished, as in the video. "Passed" means both phases (choice K4-A).

## Self-test and noise check first

Self-test (`selftest.txt`): the pattern equals a second implementation on 12,480 bars; SMA 14 equals a plain mean; stop, target, stop and target in one bar, and a buy stop opening above the level behave as the rule says; a hand-made challenge passes and fails where it should.

24 fake markets (10 years of M30 bars, random walk, 15% volatility a year, drift 0 and 8%), 1,000 control runs per set. Threshold: mean percentile between 35 and 65, at most 3 of 24 above 95.

| | Result |
|---|---|
| v1.0, 60 price steps per M30 bar (`noise_24sets_v1.0_60steps_failed.txt`) | mean percentile 66.3, 6 of 24 above 95: **failed**. The fake price jumped over the buy stop level in steps of about 0.16 USD, and the fill exactly at the level gave the rule about +0.03R per trade for free |
| v1.1, 600 price steps per M30 bar (`noise_24sets_v1.1_600steps.txt`) | mean percentile 46.2, 0 of 24 above 95: passed |

Filling exactly at the level stays a limitation on real data (slightly in favour of the rule).

## Data check

`datacheck.txt` (metadata only, before the run): 125,452 M30 bars, 22 April 1998 to 5 November 2026; usable from May 2017; 2,458 trading days after that, median 46 bars a day; 26 weekdays without data (Christmas, New Year, Good Friday). P1 has 1,290 trading days.

## Control first (10,000 runs, seed 31)

A random sequential process, one position at a time, with the rule's own waiting times, its own stop distances (as a multiple of the 1-hour ATR), target 2R and the same costs and path rules.
Null A (decisive): entry only when the previous H1 bar meets the same trend filter (close above both averages: long; below both: short), no pattern. This asks whether the pattern adds anything on top of the trend.
Null B (supplement): coin flip on direction, no filter.

| P1 | Mean net result per trade | Rule's percentile |
|---|---|---|
| The rule | +0.132R | |
| Null A, 5 / 50 / 95% of the runs | -0.063 / +0.050 / +0.166R | **87.8** |
| Null B, 5 / 50 / 95% of the runs | -0.169 / -0.049 / +0.074R | 99.2 |

Chance with the same trend filter already made about +0.05R per trade in this period: gold rose strongly.

## Result, gold, 6 November 2021 to 5 November 2026 (decisive)

| | Measured | Claimed (descriptive only) |
|---|---|---|
| Trades | 369 (59.6% long) | 512 |
| Win rate after costs | 39.8% (95%: 35.0 to 44.9) | 43% |
| Mean net result per trade | **+0.132R** (95% bootstrap per trading day: -0.017 to +0.276); before costs +0.195R | |
| Profit factor | 1.20 | |
| Average win and loss | +1.96R and -1.08R | about 2 × |
| Largest drawdown, $1,000 fixed risk on $100,000 | 13.9% (14.3R) | 7.5% |
| Worst day | -3.71% | -3.6% |
| Longest run of wins and of losses | 6 and 8 | 7 wins |
| Median stop distance | 8.17 USD | |

| Year | 2021 (from 8 Nov) | 2022 | 2023 | 2024 | 2025 | 2026 (to 5 Nov) |
|---|---|---|---|---|---|---|
| Trades | 9 | 79 | 74 | 79 | 73 | 55 |
| Mean net R | -0.419 | +0.212 | -0.025 | +0.071 | +0.199 | +0.318 |

| Challenge (1,000 random start days) | Measured | Claimed |
|---|---|---|
| Passed both phases | **41.8%** (95%: 38.8 to 44.9) | 81% |
| Failed | 17.0% | about 1 in 8 |
| Not finished within a year | 41.2% | the rest |
| Median days to pass | 173 | 155 |
| Same challenge with Null A trades (2,000 runs) | 24.8% passed | |

## Verdict by the pre-set criteria

| Claim | Criterion | Result |
|---|---|---|
| C1: the rule makes money after costs | upper end of the 95% range below 0 | +0.276: not falsified (the range includes 0) |
| C2: the pattern picks better moments than chance within the same trend | not above percentile 95 of Null A | 87.8: **falsified** |
| C3: 512 trades, 43% won, drawdown 7.5% | descriptive only | 369 trades, 39.8%, 13.9% |
| C4: 81% of the challenges passed | upper end of the 95% range below 81% | 44.9%: **falsified** |
| C5: the pass rate comes from the rule | descriptive only | Null A trades pass 24.8% |

By the rule fixed in advance, the idea is dead when C2 falls: the pattern did not beat chance with the same trend filter.

## Read this before you draw a conclusion

- **The average is positive.** +0.132R per trade after costs; 2022, 2024, 2025 and 2026 positive, 2023 and the 9 trades of late 2021 negative. It was not better than chance within the same trend filter at the pre-set level: about 12% of the random runs did as well or better.
- **Before the claim's period it lost.** P0 (May 2017 to 5 November 2021): 292 trades, 32.9% winners, -0.133R per trade (-0.289 to +0.027), Null A percentile 39.8.
- **One non-chosen variant crosses the line.** The order valid up to 5 H1 bars (K3-B, cancelled once the stop level is touched): 387 trades, +0.182R (+0.032 to +0.330), Null A percentile 96.6. The other alternatives: EMA instead of SMA (K1-B) percentile 70.2; a looser pattern (K2-B) 79.3. These variants were listed before the run as supplementary, not as a second chance. Three extra tries make one result above 95 less surprising. A new test of K3-B would need a new hypothesis and a new period.
- **Phase 1 only (K4-B).** 58.6% passed phase 1 (55.5 to 61.6); with Null A trades 49.2%.
- **Costs.** 0 / 0.40 / 0.80 USD: +0.195 / +0.132 / +0.070R per trade.

All runs are in `run01.txt` (the input path in its first line is shortened to the file name); every decisive trade with time, direction, entry, stop, target and exit is in `trades_P1_decisive.csv`, P0 in `trades_P0_2017_2021.csv`.

## Limits

One broker's CFD data and broker time, not the firm's time zone. A reconstruction of words, not the source's code. Stop orders fill exactly at the level, which slightly favours the rule. Overlapping challenge start days are not independent, so the interval for the pass rate is too narrow if anything. No fees, no payout rules. A different period may give a different result.

This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgement.
