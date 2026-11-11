# Box Theory, traded blindly: results

The rule comes from a trading channel's video (May 2025) and two follow-up videos (2026). Draw a box from the previous day's high to its low, with a line in the middle. Sell at the top, buy at the bottom, stay out of the middle. Stop just beyond the high or low of the day, target the middle or the other side of the box ("2:1 to 3:1"). In the video the rule is traded on the Nasdaq "blindly", without candles or indicators. The video shows "three winners, one loser" and calls the blind rule "that accurate". It gives no win rate over more trades and no test period.

The source also says it does not recommend trading blindly, and that candle patterns and setups are needed for an "elite" level. This test measures the blind version that the video demonstrates.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` and `hypothesis-v1.1-dutch.md`, with English versions written at the same time. Version 1.1 changes only the fake market used for the noise check, after version 1.0 failed that check (see below). Rule, control group, costs, periods and pass/fail criteria are the same in both. The published Dutch files differ from the internal ones only in one removed first name.

## What the claim implies

With the translation below (stop 0.2 box heights beyond the edge, target the middle, 0.5 box heights away), break-even is 0.2 / 0.7 = 28.6% before costs. On a random walk with no drift, the chance of reaching the target before the stop is also 28.6%. Three wins out of four happens 8.4% of the time even at a true win rate of 30%.

## Setup

| | |
|---|---|
| Script | `box-theory/box_control.py` in the repository root |
| Bars | MT5 Nasdaq 100 CFD (USTEC) M1 export from one broker, server time. Real M1 data from April 2017, spread column filled from 2018 (`data_check_ustec.txt`) |
| Session | 9:30 to 16:00 New York. The opening minute is taken per day from the jump in tick volume at 16:30 server time, or one hour earlier or later in weeks where daylight saving differs |
| Box | High and low of the previous broker day. Moves out to a higher pre-market high or lower pre-market low, and once more at 9:45 to the day's high and low so far. Then fixed until the close. Middle = halfway |
| Entry | Between 9:45 and 15:30: short at the top on the first bar that touches it, long at the bottom on the first bar that touches it (limit fill at the edge). At most one long and one short per day, one position at a time |
| Stop | 0.2 box heights beyond the edge. No trade if that is under 10 index points |
| Target | The middle line, 0.5 box heights from the edge, so 2.5R before costs |
| Exit | Stop, target or the session close |
| Path rule | Bar by bar on M1. A bar that touches both stop and target counts as a stop. The entry bar counts for the stop, not for the target. A bar that opens beyond the stop exits at its open |
| Costs | Spread from the export at the entry bar, plus 1 point slippage per side. Sensitivity 0 and 2 points per side. No commission |
| Decisive period | P1: 1 January 2019 to 4 November 2026 |
| Run | Variant 1 of 1 |

## Result, P1 (decisive)

Funnel: 2,028 trading days, 1,952 with a complete session, 1,949 with a stop of at least 10 points. The top was touched on 738 days, the bottom on 578. 1,316 trades: 738 shorts, 578 longs. Exits: 184 at the target, 715 at the stop, 417 at the session close.

| | Measured | Claimed |
|---|---|---|
| Win rate | 32.8% (95%: 30.3% to 35.4%) | 3 of 4 (75%) |
| Mean net R per trade | −0.134 (95% day bootstrap: −0.202 to −0.064) | positive ("for like $4,000") |
| Profit factor | 0.79 | |
| Mean R at 0 / 1 / 2 points slippage per side | −0.093 / −0.134 / −0.175 | |
| Median stop | 59.0 points | |
| Median spread | 1.0 point | |
| Best 5% of trades | +162.8R, against a total of −176.2R | |
| Longest losing streak | 17 | |

## Control groups

The rule trades long and short within one day, so a coin flip on direction is the right control. 10,000 runs.

| Control | 5th / 50th / 95th percentile, mean net R | Rule's percentile |
|---|---|---|
| Null A: the same entry moments, prices and distances, random direction; the opposite direction gets the mirrored stop and target (decisive) | −0.098 / −0.046 / +0.006 | **0.2** |
| Null B: random minute between 9:45 and 15:30 on a random day in the same month, random direction, same stop and target in that day's box heights (extra) | −0.094 / −0.044 / +0.006 | 0.1 |

Fading the edges of the box did worse than a random direction at the same moments, and worse than random moments.

## After the video (P2, not decisive)

From 22 May 2025: 244 trades, win rate 38.5% (95%: 32.6% to 44.8%), mean net R −0.023 (−0.179 to +0.139), percentile 77.0 against Null A.

## Second market (P3, not decisive)

US500 CFD, same broker, 1 January 2019 to 30 October 2026, minimum stop 2.5 points, slippage 0.25 point per side: 1,337 trades, win rate 36.7% (95%: 34.1% to 39.3%), mean net R −0.103 (−0.172 to −0.036), percentile 7.8 against Null A and 5.8 against Null B. Output in `run01_P3_us500.txt`.

## By year (P1)

| Year | Trades | Win rate | Mean net R |
|---|---|---|---|
| 2019 | 150 | 30.7% | −0.259 |
| 2020 | 147 | 37.4% | −0.059 |
| 2021 | 175 | 29.7% | −0.232 |
| 2022 | 182 | 24.7% | −0.315 |
| 2023 | 178 | 33.1% | −0.123 |
| 2024 | 170 | 35.3% | +0.029 |
| 2025 | 166 | 33.7% | −0.030 |
| 2026 (to 4 Nov) | 148 | 39.9% | −0.059 |

## Script check on noise, and why the fake market changed

Before the real run, the script was run on 24 synthetic random walks: 5 years of M1 bars, 20% yearly volatility, no drift, with a session structure. On random data the rule should not differ from its control: mean percentile between 35 and 65, at most 3 of 24 above 95.

Version 1.0 failed: mean percentile 22.8 (`noise_24sets_v1.0_failed.txt`). The cause was the fake market, not the control. Its price moved in 5 steps per minute, so at the first touch it overshot the edge by a few points on average, while the entry is booked at the edge. That costs the rule (selling at the top) and gives the mirrored trade (buying at the top) the same amount. Measured, rule minus mirror in gross R per trade: −0.139 with 1 step per minute, −0.059 with 5, −0.002 with 60 (standard error 0.022). Output in `noise_granularity.txt`, script `diag_granularity.py`. In real data, prices move in ticks of a fraction of a point against a stop of at least 10 points.

Version 1.1 uses 60 steps per minute and nothing else changed. On 24 sets: mean percentile 37.0, above 95 in 0 of 24, mean gross win rate 35.7% (`noise_24sets_v1.1.txt`). It passed, at the low end: on noise the control leans slightly against the rule. Only then was the real data opened.

## Verdict

Rejected on all three pre-set criteria. Win rate: the upper bound 35.4% is far below the 75% shown. Profit: the upper bound of the mean is below zero. Control: percentile 0.2, an edge needs above 95. No parameter variants will be tested.

## Limitations

- This is the blind version of the rule. The source says better results need candle patterns and setups on top; those are not tested here.
- The stop distance (0.2 box heights), the minimum stop and the fixed widening at 9:45 are our translation. The source places the stop "just above the high of the day", which is almost zero at the moment of entry. They were fixed before the data was seen.
- The source widens the box after a break only when it lines up with an earlier level on the chart. That judgement cannot be coded; we widen once at a fixed time.
- A CFD from one broker, not the Nasdaq future the source trades. Costs and times differ.
- The raw price export is not published. Run the script on your own MT5 export to reproduce the method; exact numbers will differ by broker.

## Files

| File | Contents |
|---|---|
| `trades_P1_ustec.csv` | One row per decisive trade: day, minute (server time), side, entry, stop distance, box height, spread, gross points, exit kind, exit minute, the mirrored trade's gross points and exit kind, net R, year |
| `trades_P3_us500.csv` | Same columns, US500 |
| `run01_P1_ustec.txt`, `run01_P3_us500.txt` | Full output of the runs |
| `noise_24sets_v1.1.txt` | Script check on 24 random-walk sets, version 1.1 |
| `noise_24sets_v1.0_failed.txt` | The failed check with the version 1.0 fake market |
| `noise_granularity.txt`, `diag_granularity.py` | The measured cause of the failed check |
| `data_check_ustec.txt`, `data_check_ustec.py` | Data check on the export's metadata only, done before the run |
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.1-dutch.md` | Rules and pass/fail criteria, fixed before the run (Dutch, binding) |
| `hypothesis-v1.0-english.md`, `hypothesis-v1.1-english.md` | The same in English, written at the same time |

Usage: `python box_control.py USTEC_M1.csv --minstop 10 --slip 1.0 --from 2019-01-01 --after 2025-05-22 --nullb` for the real run, `python box_control.py --noise` for the noise check.

Nothing here is financial advice. It is a measurement of one rule in one period. Test it yourself and make your own judgment.
