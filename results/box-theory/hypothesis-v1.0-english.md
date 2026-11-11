# Hypothesis: Box Theory, traded blindly (test G)

> **English version, written on 11 November 2026 together with the Dutch original, before any price data was looked at.** The binding version is the Dutch original `hypothese-box-theory.md` (published as `hypothesis-v1.0-dutch.md`). If the two differ, the Dutch text applies.

Date: 11 November 2026 · Source: a video from a trading channel (May 2025) and two follow-up videos (May and September 2026); the source with its name is kept in the private project files · Status: **version 1.0, approved on 11 November 2026, no price data looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. If a choice turns out to be untenable, a new version with a new date follows, and this result stays.

## 1. What the source promises

[verified, transcript] The rule as the source demonstrates it:
- Box: the previous day's high and low, with a line roughly in the middle.
- Sell at the top, buy at the bottom, do not trade in the middle.
- Stop: just above the high of the day (short), just below the low (long).
- Target: the middle or the other side of the box, "2:1 to 3:1".
- If price breaks the box in the first 15 to 20 minutes, widen the box to the new high or low. Also widen it to a higher pre-market high or lower pre-market low.
- Example on the Nasdaq, 5 minutes. According to the source, any timeframe works.
- Without candles or indicators: "blindly buy".

[verified, transcript] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | "three winners, one loser" when blindly buying and selling at the box, so 75% | Win rate with 95% interval |
| C2 | The rule makes money ("for like $4,000") | Mean net R per trade with interval |
| C3 | "that accurate by blindly buying and selling at premium levels": the edges of the box pick a better direction than chance | Real result against the control group |

[verified] Not testable and outside this measurement: "six-figure a month", "$10,000/month" (depends on position size), and adding candle patterns for an "elite" level. The source itself says it does not recommend trading blindly. This test measures the blind version the source demonstrates and calls "accurate". That is stated in every publication.

## 2. Weak spots, named in advance

1. [verified] The 75% claim rests on 4 trades in one video. With a true win rate of 30%, the chance of 3 or more winners in 4 trades is 8.4% [verified, binomial].
2. [verified, arithmetic] With the translation below (stop 0.2 and target 0.5 box heights), break-even is a win rate of 0.2 / 0.7 = 28.6% before costs. On a random walk without drift, the chance of reaching +0.5 before -0.2 is also 28.6%. A high win rate is therefore not to be expected at this ratio; 75% would be exceptional.
3. [assumption] "Just above the high of the day" gives a stop of almost zero at the moment of entry. A fixed minimum distance is needed, otherwise costs eat everything (lesson from the supply-demand test). That distance is our choice.
4. [assumption] The source ties widening the box after a break to an earlier level on the chart ("does it coincide with any value premium level in the past"). That is not mechanical. We widen once, at a fixed time.
5. [assumption] The source trades the Nasdaq future. We use a Nasdaq 100 CFD from one broker. Price movement is nearly the same, costs and times are not.

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules.

**3.1 Data.** Decisive: Nasdaq 100 CFD (NAS100 or USTEC), M1, MT5 export from the same broker as US500 (IC Markets EU, demo). Additional and not decisive: US500 M1, 1 Jan 2019 through 30 Oct 2026 (`US500_M1_2019-2026.csv`, already in hand). Times in server time; the script determines the regular session (9:30 to 16:00 New York) per day from the jump in tick volume at the open, as in the supply-demand test.

**3.2 Box.** Per trading day d:
- Base: the high and low of the previous broker day (the daily chart, as the source uses it).
- Pre-market: if the high or low of day d before 9:30 lies outside the base, that side moves with it.
- Open: at 9:45 (after 15 minutes of session), each side moves once more to the high or low of day d up to then.
- After that the box is fixed until the close. Middle line M = (top + bottom) / 2. Box height H = top − bottom.

**3.3 Entry.** Between 9:45 and 15:30 New York:
- Short: the first M1 bar whose high touches the top. Entry at the top (limit order).
- Long: the first M1 bar whose low touches the bottom. Entry at the bottom.
- At most one short and one long per day, and one position at a time. If both sides are touched in the same bar, no trade in that bar.

**3.4 Stop.** 0.2 × H beyond the edge: short stop = top + 0.2H, long stop = bottom − 0.2H. If 0.2H is smaller than 10 index points (Nasdaq) or 2.5 points (US500), no trade that day on that side.

**3.5 Target.** The middle line M. That is 0.5H from the entry, so 2.5R before costs, within the source's "2:1 to 3:1".

**3.6 Exit.** Stop, target, or the end of the session (16:00 New York) at the close of the last M1 bar.

## 4. The three fixed rules

**Costs.** Spread from the SPREAD column of the export, per entry bar, plus slippage of 1 point per side (Nasdaq) or 0.25 point per side (US500) [assumption]. No commission [assumption, as for US500 in the supply-demand test]. Sensitivity: slippage 0, 1 and 2 times.

**Order of events.** The path is followed bar by bar on M1. If one bar hits both stop and target, it counts as a stop. The entry bar itself also counts for the stop (not for the target).

**Control group.** 10,000 runs, seed 23. Bootstrap per trading day.
- **Null A, decisive (coin flip):** the same entry moments, prices and distances as the real trades, random direction. In the opposite direction, stop and target are mirrored (stop 0.2H on the other side, target 0.5H further). Tests whether trading against the edge is better than trading with it.
- **Null B, additional (place in the box):** per real trade a random M1 bar on a random trading day in the same month, between 9:45 and 15:30, random direction, the same stop and target distance in that day's box heights. Tests whether the edge adds anything compared with a random place.

[verified, method] A coin flip is the right null here: the rule trades long and short within one day, where the index's drift is small compared with the movement. The share of longs and shorts is reported.

## 5. Noise check before the real data (fixed)

24 synthetic series of 5 years of M1, random walk without drift with the volatility of an index (20% per year) and a session structure (trading days, pre-market, session), seed 7 [assumption, chosen before seeing the data].

Bounds, the same as the audit of 10 Nov: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95. Expected [verified, arithmetic]: a win rate around 28.6% before costs. If the noise check fails, the control is revised first (new version), only then the real data.

## 6. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | Nasdaq: 1 Jan 2019 (or the first month with a filled SPREAD column, if later) through the last full day | **Decisive** |
| P2 | Nasdaq: from 22 May 2025 (after the video) | After the claim, not decisive |
| P3 | US500, 2019-2026 | Second market, not decisive |
| P4 | per year | Spread, not decisive |

## 7. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate in P1 is below 75% |
| C2 | The upper bound of the 95% interval of the mean net R in P1 is below 0 |
| C3 | The mean net R in P1 is not above percentile 95 of Null A |

If C3 falls, the rule is dead: no repairs, no optimisation, no other stops, targets, times or box definitions. Fewer than 100 trades in P1: "insufficient trades".

If C3 stands, I report it as "not falsified", with the limitations, and not as "works".

## 8. What I report, whatever the outcome

The funnel (trading days, days with a touch of the top and of the bottom, trades after the minimum stop, trades after one position at a time), number of trades, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A and Null B, share of longs and shorts, result per year, share of trades closed at the session end, the three cost levels, median stop distance in points against the costs, longest losing streak, and the sum of the best 5% of trades next to the total.

## 9. Next step

1. Approved on 11 November 2026. The document is fixed (SHA-256 in the measurement log). The English version goes along.
2. Export of Nasdaq 100 M1 from MT5. Data check on the metadata only (bars per day, SPREAD column, times).
3. Measurement script `box_control.py`, first the noise check from 5, then the real data.
4. After that, separately: the side claim about SPY after the open (own hypothesis).
