# Noise-area intraday momentum, Nasdaq 100: results

The rule comes from a 2024 research paper. A testing channel's video (14 November 2026) ran it on CME futures from January 2020 to October 2026 and reports for the Nasdaq: "1,564 trades, +6.8 points per trade after costs", "41% winners", "every year 2020-2026 positive", and on a coin flip for the direction: "4 of 1,000 reached the real result". For the S&P 500 the video reports "+0.5 points per trade". This test measures the rule on another data source (a CFD with the broker's real spread) and adds a control group with random entry moments.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md`, with an English version written at the same time. Two corrections followed, both before the run on real data: v1.1 (the self-test showed that an exit and a re-entry in the same direction at the same moment paid costs twice; now only a reversal is allowed, as in a public replication) and v1.2 (a data check showed that detecting the opening minute from tick volume picked 8:30 New York on days with economic releases; the opening is now fixed at 16:30 server time). The binding version is v1.2 (`hypothesis-v1.2-dutch.md`; the Dutch files are binding, the English ones are translations).

## Rule

| | |
|---|---|
| Script | `noise-area-momentum/noise_area.py` in the repository root. Needs pandas, numpy and numba |
| Data | USTEC (Nasdaq 100) CFD, M1, one broker (MT5 export, server time New York + 7 all year). Tick volume, not exchange volume. Same file as the earlier Nasdaq tests. US500 (S&P 500) supplementary |
| Session | Regular hours, 9:30 to 16:00 New York, fixed at 16:30 to 23:00 server time. A day counts with at least 90% of its 390 minutes |
| Noise band | For each minute of the session: the average absolute move from the open at that minute over the last 14 days. Upper band = max(open, previous close) × (1 + band), lower band = min(open, previous close) × (1 − band) |
| VWAP | Restarts every day at 9:30. Price per minute (high + low + close) / 3, weighted by tick volume |
| Checks | Every 30 minutes, 10:00 to 15:30 New York (12 a day), on the close of the minute that ends at that time |
| Entry | Long above the upper band, short below the lower band. One position at a time |
| Exit | Long: when the price is below the higher of the upper band and the VWAP. Short: when the price is above the lower of the lower band and the VWAP. At the same check only a reversal is allowed. Everything closed at 16:00 |
| Fills | Open of the minute after the check time, never the close that gave the signal |
| Costs | Spread at the fill minute plus 1 point slippage per side on USTEC (0.25 point on US500). Sensitivity 0 and 2 times the slippage, and the video's cost level (0.75 point per trade) |
| Decisive period | 2 January 2020 to 5 November 2026 |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M1 export in the format described in the main README works.

## Self-test and noise check first

Self-test (`selftest.txt`): four hand-made days behave as the rule says (gap up without a move: no trade; gap down with a fall: short all day; rise then crash: long, then a reversal to short; late rise: long), no re-entry in the same direction, and the rule equals a second implementation on 300 fake days (401 against 401 trades, and 391 against 391 with the VWAP entry variant).

24 fake markets (1,500 days of minute bars each, random walk without trend or opening effect, 60 sub-steps per minute, fixed spread 1 point), 2,000 control runs per set (`noise_24sets.txt`). Threshold: mean percentile between 35 and 65, at most 3 of 24 above 95.

| | Result |
|---|---|
| Against Null B | mean percentile 40.4, 1 of 24 above 95: passed |
| Against Null A | mean percentile 41.0, 1 of 24 above 95: passed |
| The rule on noise | −0.12 point per trade before costs, −3.12 after costs |

## Data check

`data_check_ustec.txt`: valid sessions 2020 to 2026: 250, 250, 250, 247, 249, 247, 211. Median spread 2.00 points up to 2023, 0.81 in 2024, 1.00 in 2025 and 2026. From April 2026 the tick volume of this broker is much flatter; the timing of the session still shows (jump at 16:30, drop at 23:00), but 193 days in the decisive period have no clear volume jump at 16:30, most of them in 2026. `data_check_us500.txt` for the S&P 500.

## Control first (10,000 runs, seed 43)

Null B (decisive): the same valid days, the same check times and the same costs. At every check time without an open position, chance opens a position with probability p and a random direction. The holding time is drawn from the real trades. p is set so that the number of trades matches the rule's.
Null A (the video's test): the same trades with the same entry and exit, direction by a coin flip.

| | Mean net result per trade | Rule's percentile |
|---|---|---|
| The rule | +4.85 points | |
| Null B, mean of the runs | −2.95 points | **100.0** (0 of 10,000 runs at or above) |
| Null A, mean of the runs | −2.91 points | 99.8 (22 of 10,000 runs at or above) |

## Result, Nasdaq 100, 2 January 2020 to 5 November 2026 (decisive)

| | Measured | Claimed |
|---|---|---|
| Trades | 1,537 (0.90 a day) | 1,564 |
| Mean net result per trade | **+4.85 points** (95% bootstrap per trading day: +0.05 to +9.90); before costs +7.79 | +6.8 |
| Win rate after costs | 40.5% | 41% |
| Profit factor | 1.17 | |
| Average win and loss | +82.96 and −48.39 points | |
| Long and short | 782 long, +6.30; 755 short, +3.35 | |
| Largest drawdown | −2,329 points | |

| Year | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to 5 Nov) |
|---|---|---|---|---|---|---|---|
| Trades | 213 | 221 | 259 | 217 | 218 | 217 | 192 |
| Net points | +241 | +789 | +1,490 | +1,325 | +1,588 | +1,226 | +794 |

## Verdict by the pre-set criteria

| Claim | Criterion | Result |
|---|---|---|
| C1: +6.8 points per trade after costs | upper end of the 95% range below 6.8 | +9.90: not falsified |
| C2: the rule beats chance | not above percentile 95 of Null B | 100.0: not falsified |
| C3: every year 2020-2026 positive | any year negative | all seven positive: not falsified |

## Read this before you draw a conclusion

The result holds on the pre-set criteria, but it is fragile:

- **Ten days made most of it.** The ten best days together: +6,054 points. All 1,537 trades together: +7,453 points. Without those ten days: +1,399 points.
- **Costs matter.** With twice the slippage (2 points per side): +2.85 points per trade, 95% range −1.95 to +7.90, and 2020 turns negative. Without slippage: +6.85. At the video's cost level: +7.04 (+2.24 to +12.09), 41.5% winners.
- **After the paper.** From 14 May 2024 (the paper online): 550 trades, +6.05 points (95% range −4.18 to +17.33), Null B percentile 98.1. Without the ten best days in that period: −2,688 points.
- **Before 2020.** USTEC 2017 to 2019: 582 trades, +1.73 points (−1.07 to +4.72).
- **The S&P 500.** Same rule, same period: 1,557 trades, +0.05 point per trade (−0.96 to +1.09), profit factor 1.01, Null B percentile 96.1; 2020, 2025 and 2026 negative.
- **Variants.** Entry also on the VWAP side: +5.04. VWAP without volume: +4.73.

All runs are in `run01.txt`; every decisive trade with date, direction, entry and exit is in `trades_ustec.csv`.

## Limits

One broker's CFD data, not exchange futures. Tick volume for the VWAP. CFD points are close to Nasdaq futures points but not equal. One unit per trade; the paper's volatility targeting and leverage are not part of this test. The result rests on a few days; a different period may give a different result.

This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgement.
