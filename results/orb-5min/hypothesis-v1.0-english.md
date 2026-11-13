# Hypothesis: 5-minute opening range breakout on the S&P 500 (test H)

Date: 13 November 2026 · Source: blog post by a provider of trading data, 18 April 2026 · Status: **draft 1.0, 13 November 2026, not yet approved. No price data opened for this test.**

This is the English version. The Dutch original (`hypothese-orb-5min.md`, same date) is binding; its SHA-256 is in the measurement log.

Legend: **[verified]** = checked or calculated ourselves · **[assumption]** = not checked ourselves, or a choice in the measurement

Rule: everything below is fixed before the first run. After the first real run nothing changes; a new version gets a new date.

## 1. The claim

[verified, source read 13 Nov 2026] On the S&P 500 future (ES), 1 contract, over "6 months": 115 trades, win rate 72.17%, profit factor 1.623, net 10,825 dollars. The source itself says the settings are optimized and that the default settings "won't perform like this". Costs and slippage are not mentioned.

## 2. Testable claims

| # | Claim | Testable as |
|---|---|---|
| C1 | 72.17% of trades win | Win rate with 95% interval (Wilson) |
| C2 | The rule makes money (profit factor 1.623) | Mean net result per trade in R, with 95% interval (bootstrap by day); profit factor for information |
| C3 | The direction of the break carries information (implied: "trade in the direction of the break") | Mean net R against Null A: same entry, direction by coin flip |

## 3. Weak points, named in advance

1. [verified] The source does not state the exact period, nor: touch or close as the break, trades per day, exit time, costs. We fill these in (section 4) and report it with every outcome.
2. [verified, arithmetic] Target 0.5 range against stop 1.0 range: without costs, 66.7% wins are needed to break even. Small costs weigh heavily, because a target of half a range is often only a few points.
3. [assumption] We measure on a CFD on the S&P 500 (US500, IC Markets), not on the ES future. Points are comparable, the price not exactly (basis, spread).
4. [verified, source] The filters (range at most 0.55%, no Tuesday, at most 14 points loss) were chosen on the same period as the claim. The claim period itself is therefore not decisive.

## 4. Mechanical translation (fixed)

**4.1 Session.** Open 9:30 New York time, detected as in test G (tick volume jump around 16:30 server time, 60 minutes leeway for daylight saving weeks). A day only counts with at least 90% of its 390 minute bars.

**4.2 Range.** Highest high and lowest low of the first 5 minute bars (9:30 to 9:35). Range = high minus low. Range 0: no trade.

**4.3 Filters.** No trade if the range is larger than 0.55% of the opening price. No trade on Tuesday (both directions) [assumption: the source contradicts itself; the heading says all Tuesdays].

**4.4 Entry.** From 9:35, the first minute bar with a high above the range high (long) or a low below the range low (short): entry at the range level, as a stop order. If that bar already opens beyond the level, entry at the open of that bar. If the same bar touches both sides, no trade (order unknown), but counted. At most one trade per day [assumption]. No break before 15:55: no trade.

**4.5 Stop.** The other side of the range, but never further than 14 points from the entry (the maximum loss from the source) [assumption: 1 ES point = 1 US500 point].

**4.6 Target.** The range level plus (long) or minus (short) 0.5 times the range [verified, source: measured from the breakout level].

**4.7 Exit.** Stop, target, or else at the close of the last session bar (16:00) [assumption: the source gives no exit time].

**4.8 R.** 1 R = distance from entry to stop. Result per trade in R, net of costs.

## 5. Data (fixed)

US500 M1, IC Markets, export already on file (`US500_M1_201208060000_202611021049.csv`). Real minute data from 21 March 2017; spread column filled only from 2019 [verified, data check 2 Nov]. A fresh export to the last trading day is allowed if it arrives before the run.

Data check before the run, metadata only: valid sessions per year, distribution of the detected opening minute, share of days with an empty spread.

## 6. The three fixed rules

**Costs.** The spread from the SPREAD column on the entry bar, plus 0.25 point slippage per side (entry and exit) [assumption: one ES tick]. Sensitivity: slippage 0, 1 and 2 times.

**Path.** Minute by minute. In the entry bar only the stop counts. If a later bar touches both stop and target, the stop counts.

**Control group.**
- Null A (decisive): the same days, the same entry minute and entry price, but the direction by coin flip; stop and target at the same distance, mirrored. 10,000 runs, seed 31. Measured: mean net R. Percentile of the real value.
- Null B (supplementary): the same days, a random entry minute between 9:35 and 15:30, direction by coin flip, the same range distances. 10,000 runs.

## 7. Noise check before the real data (fixed)

24 fake markets of 1,500 trading days with minute bars, built from 60 steps per minute (as test G v1.1), without trend and without an opening effect, with a fixed spread of 0.5 point. Seed 7.

Limits, as in the audit of 10 Nov: percentile against Null A between 35 and 65 on average, at most 3 of 24 above 95.

## 8. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | 1 Jan 2019 to 17 Oct 2025 inclusive | **Decisive**: before the window the source optimized on |
| P0 | 18 Oct 2025 to 17 Apr 2026 inclusive | Rebuilt claim period [assumption: the 6 months before the post]. Compared with 115 trades and 72.17%. Not decisive |
| P2 | 18 Apr 2026 to the last day | After the post. Fewer than 100 trades: reported as insufficient |
| P3 | per year within P1 | Distribution, not decisive |

## 9. When is the idea dead (in advance)

| Claim | Falsified in P1 if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate is below 72.17% |
| C2 | The upper bound of the 95% interval of the mean net R is below 0 |
| C3 | The mean net R is not above percentile 95 of Null A |

After the run: no other ranges, targets, filters or exit times. If a claim stands: "not falsified in this measurement", not "works".

## 10. What I report, whatever the outcome

The funnel: valid days, after the range filter, after the Tuesday filter, with a break, both sides in one bar, trades. Per period: trades, win rate (95%), mean net R (95%), profit factor, share of stop, target and close exits. Percentiles against Null A and Null B. Cost sensitivity. The year table. The noise check.

## 11. Next step

1. Approval (or changes). SHA-256 in the measurement log.
2. Script `orb_control.py` based on test G, first the noise check from 7.
3. Data check from 5, then the run.
4. Code and data on GitHub before publication.
