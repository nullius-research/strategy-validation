# Previous-day sweep with a 1-hour trend filter, Nasdaq 100 5 minutes: results

A trading channel published a free session indicator and a video (17 November 2026) in which it tested 26,825 settings. For the Nasdaq 100 it reports one setup that held up: "previous-day sweep + 1 hour trend · 5 min · hold to 16:00 New York", with "profit factor 1.95 (290 trades; 1.95 on 2021–24, 1.96 on 2025–26)", after costs. The video also says that "about 70 % of the trades lose", that "without the 5 best days the Nasdaq setup is close to break even" and that the longest losing streak was 18 trades. This test rebuilds the rule from the public description, runs it on another data source and adds control groups with random entries.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md`, with an English version written at the same time. One correction followed, before the run on real data: v1.1 changed only one supplementary control group (Null T, see below), because the noise check showed it was biased. The binding version is v1.1 (`hypothesis-v1.1-dutch.md`; the Dutch files are binding, the English ones are translations).

## Rule

| | |
|---|---|
| Script | `prev-day-sweep/sweep_test.py` in the repository root. Needs pandas, numpy and numba |
| Data | USTEC (Nasdaq 100) CFD, M1, one broker (MT5 export, server time New York + 7 all year). Same file as the earlier Nasdaq tests |
| Trading day | 20:00 New York to 20:00 New York. Weekdays only. A day counts with at least 90% of the minutes from 02:00 to 16:00 New York |
| Yesterday | High and low of the previous trading day (20:00 to 20:00) |
| Kill zones | London 02:00 to 05:00 and New York 07:00 to 11:00, New York time |
| Sweep | The first 5-minute bar of the day that trades through yesterday's high (or low) must fall inside a kill zone. If the level was taken earlier, that side gives no sweep that day |
| Back inside | The first 5-minute bar in the same kill zone that closes back inside yesterday's range. Back below the high: short. Back above the low: long |
| Trend filter | Close of that bar against the EMA 200 of 1-hour closes (last completed hour). Long only above, short only below. If the trend does not agree on that first close back inside, no trade |
| Both sides | If yesterday's high and low have both been taken by then, the day is skipped |
| Entry | Open of the next 5-minute bar. At most one trade a day |
| Stop | Past the sweep extreme, at least 0.5 × ATR(14) of the 5-minute bars |
| Exit | Stop, followed minute by minute, or the close of the last minute before 16:00 New York. No target |
| Result | In R (one R = the stop distance), after costs. Profit factor = sum of winning R / sum of losing R |
| Costs | Spread at the entry minute plus 1 point slippage per side. Sensitivity 0 and 2 points, and the video's level (0.01% of price per side) |
| Decisive period | 2 January 2020 to 5 November 2026 |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M1 export in the format described in the main README works.

## Self-test and noise check first

Self-test (`selftest.txt`, 17 of 17 passed): eight hand-made days behave as the rule says (sweep of the low in London with the trend up gives a long; the same with the trend down gives nothing; a level taken earlier in the night gives nothing; both sides taken skips the day; no close back inside the zone gives nothing; a sweep of the high in New York with a close back two bars later gives a short with the right stop; a trend that disagrees on the first close back inside gives nothing; a take at 05:00 is outside the zone), four path checks (stop, gap past the stop, exit at 16:00, short stop on the high), and a second, plain implementation gives exactly the same 39 trades on 1,000 fake days.

24 fake markets (1,500 days of minute bars each, random walk without trend or session effect, 60 sub-steps per minute, fixed spread 1 point), 2,000 control runs per set. Threshold: mean percentile between 35 and 65, at most 2 of 24 above 95.

| | v1.0 (`noise_24sets_v1.0.txt`) | v1.1 (`noise_24sets_v1.1.txt`) |
|---|---|---|
| Against Null B (decisive) | 47.7, 1 of 24 above 95: passed | 47.5, 1 of 24: passed |
| Against Null A | 50.6, 0 of 24: passed | 50.8, 0 of 24: passed |
| Against Null T | 85.1, 10 of 24: **failed** | 56.7, 2 of 24: passed |
| The rule on noise | | 56 trades per set, −0.063 R per trade, profit factor 0.96, 87% losers |

Why Null T failed in v1.0: it took random moments on the same day, also before the sweep, with the trend as direction. The trend almost always points the same way as the real trade, so a random long that entered before the dip of the sweep was often stopped by that very dip. The control "knew" a sweep was coming. v1.1 takes Null T from random valid days instead.

## Data check

`data_check_ustec.txt`: real minute data starts in 2017 (before that the file has one bar per day). Valid trading days 2020 to 2026: 244, 249, 250, 248, 249, 247, 213. Night hours filled on 99.5 to 100% of the valid days. The daily break falls at 17:00 to 18:00 New York, which fits server time = New York + 7. Median spread 2.00 points up to 2023, 0.80 in 2024, 1.00 in 2025 and 2026.

## Control first (10,000 runs, seed 43)

Null B (decisive): for each real trade, one random trade on the same day in the same kill zone, at a random 5-minute open, direction by a coin flip, the same stop distance in points, exit at 16:00, the same costs.
Null A: the same trades, direction by a coin flip.
Null T (v1.1): random valid day in the same period, same kill zone, random 5-minute open, direction by the 1-hour trend, the same stop size in ATR units. Does the sweep add anything to just following the trend?

| | Mean net R per trade | Rule's percentile |
|---|---|---|
| The rule | +0.726 R | |
| Null B, mean of the runs | −0.117 R | **99.2** (81 of 10,000 runs at or above) |
| Null A, mean of the runs | +0.263 R | 93.7 |
| Null T, mean of the runs | −0.104 R | 96.5 (351 of 10,000 runs at or above) |

The header line of `run01.txt` says "hypothesis v1.0". That is a label left in a print line; the script follows v1.1 (see its docstring and Null T). It was not changed after the run.

## Result, Nasdaq 100, 2 January 2020 to 5 November 2026 (decisive)

| | Measured | Claimed |
|---|---|---|
| Trades | 139 (1,700 valid days); 124 in 2021 to 2026 | 290 in 2021 to 2026 |
| Profit factor after costs | **1.79** (95% bootstrap per trading day: 0.84 to 3.08); before costs 2.25 | 1.95 |
| Mean net R per trade | +0.726 R (95%: −0.159 to +1.771) | |
| Losing trades | 76.3% (2021 to 2026: 77.4%) | about 70% |
| Average win and loss | +6.91 R and −1.20 R | |
| Stopped out | 73.4% | |
| Longest losing streak | 11 | 18 |
| Largest drawdown | −39.5 R | |
| Mean stop distance | 40.2 points (median 22.8); costs 3.24 points = 0.20 R per trade | |
| London and New York | 41 trades, PF 1.28 (92.7% losers); 98 trades, PF 2.12 | |
| Long and short | 83, PF 1.63; 56, PF 2.02 | |

| Year | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to 5 Nov) |
|---|---|---|---|---|---|---|---|
| Trades | 15 | 21 | 27 | 20 | 24 | 26 | 6 |
| Net R | +29.2 | +5.3 | +55.1 | −0.2 | −16.3 | +34.6 | −6.7 |

Every year has fewer than 100 trades: insufficient for a judgement per year.

## Verdict by the pre-set criteria

| Claim | Criterion | Result |
|---|---|---|
| C1: profit factor 1.95 | upper end of the 95% range below 1.95 | 3.08: not falsified (measured 1.79) |
| C2: the sweep with trend filter beats chance | not above percentile 95 of Null B | 99.2: not falsified |
| C3: holds on 2021-2024 and on 2025-2026 | profit factor 1.0 or lower in either | 1.49 (92 trades) and 2.12 (32 trades): not falsified, but both below 100 trades, insufficient |

## Read this before you draw a conclusion

The result passes the pre-set criteria, but it is thin and fragile:

- **Five days made all of it.** The five best days: +135.3 R. All 139 trades together: +100.9 R. Without those five days: −34.3 R, profit factor 0.73. The video says "close to break even" without its five best days; here it is below.
- **The profit is not clearly above zero.** The 95% range of the mean is −0.16 to +1.77 R per trade, and the range of the profit factor runs from 0.84 to 3.08. The rule beat random entries on the same days (percentile 99.2), but with 139 trades the size of the profit is uncertain.
- **Fewer trades than claimed.** 124 trades in 2021 to 2026 against 290 claimed. The rule was rebuilt from the public description, not from the indicator's source code. Where the description is open (which "yesterday", when a level counts as taken, what happens if the trend does not agree on the first close back inside) the hypothesis fixes one reading. The indicator may read it differently and take more trades. This test measures our reading.
- **The video's own example days are in our trades.** The video shows a long on 9 December 2025 ("up 6 R" at 4 pm) and a losing short on 9 June 2026 ("minus 1.3 R"). Our reading took both: +5.69 R and −1.23 R after costs. On those two days the readings agree; on many other days they apparently do not.
- **2026 so far.** 6 trades, all losses, −6.7 R. The video reports 33 trades with 5 winners from January to September 2026; our reading took 5 trades in that period.
- **Before 2020.** 2017 to 2019 (the only earlier years with minute data): 49 trades, profit factor 0.66, Null B percentile 55.9.
- **Costs.** Without slippage: PF 2.04. With 2 points per side: PF 1.60. At the video's cost level: PF 1.80.
- **15-minute bars** (supplementary): 133 trades, PF 2.06 (claimed 2.20), Null B percentile 100.0, Null T 99.4.
- **The setting was chosen from 26,825 tests** on 2021 to 2024, by the video's own account. 2020 and 2017 to 2019 played no part in that choice: 2020 was positive (15 trades), 2017 to 2019 negative (49 trades).

All results are in `run01.txt`; every decisive trade with date, kill zone, direction, entry, exit, stop distance and costs is in `trades_ustec_p1.csv` (times in server time, New York + 7).

## Limits

One broker's CFD data, not exchange futures. Our reading of the rule, not the indicator's source code. 139 trades in the decisive period; every year and both sub-periods are below 100 trades. The result rests on a few days; a different period may give a different result.

This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgement.
