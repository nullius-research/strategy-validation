# 5-minute opening range breakout: results

The claim comes from a blog post by a company that sells trading data (18 April 2026). On the S&P 500 future, one contract, over "6 months": 115 trades, a win rate of 72.17%, a profit factor of 1.623. The post calls its settings "optimized" and says the default settings "won't perform like this". Costs are not mentioned.

The hypothesis was written and fixed before any price data was opened: `hypothesis-v1.0-dutch.md` and `hypothesis-v1.1-dutch.md`, with English versions written at the same time. The Dutch files are binding. Version 1.1 changes only the control group for C3, after version 1.0 failed the noise check (see below). Rule, costs, periods and pass/fail criteria are the same. The published Dutch files differ from the internal ones only in a removed first name and a shortened file path.

## What the claim implies

Target 0.5 range against a stop of 1 range: break-even before costs is 1 / 1.5 = 66.7%. On a random walk the target is reached first in about two of three trades. So a win rate near 67% says nothing about the breakout, and with a target of a few points, costs decide.

## Setup

| | |
|---|---|
| Script | `orb-5min/orb_control.py` in the repository root. The diagnosis scripts in this folder import it |
| Bars | MT5 S&P 500 CFD (US500) M1 export from one broker, server time. Real minute data from March 2017, spread column filled from 2019 (`datacheck_h.txt`) |
| Session | 9:30 to 16:00 New York. Opening minute per day from the jump in tick volume at 16:30 server time, or one hour earlier or later in weeks where daylight saving differs. A session counts with at least 90% of its 390 bars |
| Range | High and low of the first 5 minute bars (9:30 to 9:35) |
| Filters | No trade if the range is wider than 0.55% of the opening price. No trade on Tuesdays |
| Entry | From 9:35, the first minute bar with a high above the range (long) or a low below it (short). Entry at the range edge, or at the bar's open if it opens beyond the edge. A bar that breaks both sides: no trade (counted). One trade per day. No break before 15:55: no trade |
| Stop | The other side of the range, never more than 14 points from the entry |
| Target | The range edge plus or minus 0.5 range |
| Exit | Stop, target, or the close of the last session bar |
| Path rule | Bar by bar on M1. In the entry bar only the stop counts. A bar that touches both counts as a stop. A bar that opens beyond the stop exits at its open |
| Costs | Spread from the export at the entry bar, plus 0.25 point slippage per side. Sensitivity 0 and 2 x |
| Control, C3 (v1.1, decisive) | Per trade, both directions measured from the open of the bar after the breakout bar, with that trade's stop and target distance and the same costs. The break direction against a coin flip, 10,000 runs, seed 31 |
| Control, Null B (additional) | Same days, a random entry minute between 9:35 and 15:30, coin flip direction, same distances |
| Decisive period | P1: 1 January 2019 to 17 October 2025, before the six months of the post (our reading) |
| Run | Variant 1 of 1 |

## Noise check (before real data)

24 synthetic markets of 1,500 days, no trend, no opening effect, 60 sub-steps per minute, spread 0.5 point.

| | v1.0 (failed) | v1.1 |
|---|---|---|
| Average percentile | 78.3 | 41.7 |
| Above the 95th | 5 of 24 | 2 of 24 |
| Needed | 35-65, at most 3 | 35-65, at most 3 |

Why v1.0 failed: the entry is booked exactly at the range edge, while the price has already moved a fraction past it. That favours the break direction and penalises the flipped trade at the same price. On finer fake markets the gap shrinks (`diag_substeps.txt`: percentile 99.7 at 15 sub-steps, 70.8 at 60, 35.2 at 600). Real markets have the same effect, about one tick, so version 1.1 measures both directions from the next bar's open instead (`diag_nexto.txt`). Stops inside the entry bar were not the cause (`diag_entrybar.txt`).

On the fake markets the rule wins 67.0% of trades before costs, as the arithmetic says.

## Result, P1 (decisive)

| | |
|---|---|
| Days, valid, range filter passed, not Tuesday | 1,756 / 1,687 / 1,588 / 1,255 |
| Breaks, both sides in one bar, trades | 1,255 / 5 / 1,250 |
| Win rate | 65.92% (95%: 63.2 to 68.5) |
| Mean net R | -0.121 (95% bootstrap: -0.161 to -0.081) |
| Profit factor | 0.68 |
| Before costs | 66.24% winners, +0.004R |
| Median range, target, spread | 7.70, 3.85, 0.30 points |
| Stop set by the 14-point cap | 161 of 1,250 trades |
| C3: break direction from the next open | -0.164R, percentile 18.7 against a coin flip |
| Null B | percentile 72.4 |

Cost sensitivity: slippage 0: 66.24%, -0.044R; slippage 2 x: 64.08%, -0.198R. C3 percentile 18.2 and 18.4.

| Claim | Falsified if (fixed in advance) | Result |
|---|---|---|
| C1: 72.17% win | upper bound of the 95% interval below 72.17% | **Falsified** (68.5) |
| C2: makes money | upper bound of mean net R below 0 | **Falsified** (-0.081) |
| C3: the break direction matters | not above percentile 95 | **Falsified** (18.7) |

By year, the win rate ran from 62.3% (2025) to 70.2% (2019); no year had a positive mean net R.

Five trades were recomputed from the raw export with separate code (`check5_trades.py`): 5 of 5 identical.

## Other periods (not decisive)

| Period | Trades | Win rate | Mean net R | C3 percentile |
|---|---|---|---|---|
| P0: 18 Oct 2025 to 17 Apr 2026 (our reading of the claim's six months) | 93 (insufficient) | 68.82% | +0.008 | 82.0 |
| P2: 18 Apr 2026 to 2 Nov 2026 (after the post) | 107 | 57.01% | -0.179 | 4.2 |

## Limitations

A CFD from one broker, not the ES future. The 14-point cap comes from the post's dollar limit on one ES contract (1 ES point = 1 US500 point assumed). Slippage is an assumption. The break rule, one trade per day and the close exit are our translation; the post does not specify them. The claim's six months are our reading.

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
