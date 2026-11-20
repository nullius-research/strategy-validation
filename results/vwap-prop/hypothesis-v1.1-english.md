# Hypothesis: 9 EMA + VWAP, long on the Nasdaq 100, 5 minutes, with a prop firm challenge (test O)

English translation. The Dutch original `hypothese-vwap-prop.md` (version 1.1, approved 20 November 2026, SHA-256 in the measurement log) is binding. Where the two differ, the Dutch text counts.

Date: 19 November 2026 · Source: an Instagram reel of 16 November 2026 and a post on X of 17 November 2026 by the same maker (source file kept private) · Status: **version 1.1, 20 November 2026, approved (choice A after the failed noise check of v1.0). Version 1.0 (K1 A, K2 A) is kept, SHA-256 7de9e9f5... No real price data opened for this test yet**

Change from 1.0: C5 is no longer a deciding claim. The noise check of v1.0 showed that on markets without an edge the rule reaches the target more often than random entries (mean percentile 69.9, limit 35 to 65), and that two other control groups do not solve this (percentile 99.9 and 91.1). See the measurement log. The pass rate of Null A is reported descriptively, together with the rule's pass rate on the fake markets of the noise check. Nothing else has changed.

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule of play: everything below is fixed before the first run. Nothing is changed after the run. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 0. What I already know before this test (stated up front)

[verified, measurement log test N] The same Nasdaq data (USTEC M1) was already used in test N, as a supplementary measurement: a related rule on 3 minutes, long and short, exit on a close through the EMA 9. Result: -2.695 points per trade, percentile 71.5 against chance. So this test is not blind to the market. New here: 5 minutes, long only, a confirmation candle, a different deciding period, and the prop firm challenge. I have not seen those new numbers. This is stated in every publication.

## 1. What the source promises

[verified, on-screen subtitles, 19 November 2026] The rules as the source gives them:
- "It uses two lines: the VWAP and the 9 EMA."
- Rule 1: "The 9 EMA crosses above the VWAP."
- Rule 2: "Wait for a candle to close above the EMA. That's your entry."
- Rule 3: "[Hold] the trade until a candle closes back below the EMA."

[verified, image in the reel] Chart with a 5-minute time frame, price around 21,000. Results screen of a backtesting platform: 396 trades, win rate 56.6%, profit factor 1.84, average R:R 1.41, net +$29,985.04 (+299.85%), max drawdown -22.0%, expectancy +$75.72 per trade, average win +$292.78, average loss -$206.97.

[verified, caption and X] "This strategy has an 85% prop firm pass rate" (reel). On X, a day later: "the backtest results over the last 3 years", and "the prop firm pass rate of 84%".

[verified] Not stated: the instrument by name, the session, the exact period, the position size, the costs, and which prop firm with which account size. [verified, the platform's website] The platform's simulator uses the rules of existing firms (five well-known firms) and since 5 November 2026 also checks open losses within a trade.

[assumption] Instrument: the Nasdaq 100 future (NQ). A price around 21,000 fits; the S&P 500 never stood that high.

Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | Win rate 56.6% | Net win rate per trade in P1 |
| C2 | The rule makes a profit, profit factor 1.84 | Mean net result per trade and profit factor in P1 |
| C3 | The rule picks better moments than chance | Real result against the control group with the same exit rule |
| C4 | 85% of prop firm challenges are passed | Share of challenges passed in P1, under the rules of K2 |
| C5 | That pass rate comes from the rule, not from the challenge itself | Since v1.1 not deciding, see the change at the top; descriptive only |

## 2. Weak spots visible before the test

1. [verified, measurement log test N] A related rule lost well over its costs on the same data. So I expect no profit [assumption]. That is no reason not to measure.
2. [assumption] A pass rate depends strongly on the rules of the challenge: profit target, maximum loss, position size. A rule without an edge can reach a high pass rate if the target is small compared with the loss limit. Hence C5: the same challenge with random entries.
3. [verified] The source names no firm. Any choice of firm is ours. See K2.
4. [verified, earlier tests] Our data is a CFD on the Nasdaq 100 with tick volume, not a real future with real volume. The VWAP is weighted with tick volume [assumption that this approximates the real VWAP]. Sensitivity: VWAP without volume.
5. [assumption] A CFD moves point for point with the index. The future has a basis (interest, dividends), which shifts all prices within a day by nearly the same amount. For crossings within a day this matters little.

## 3. Choices (chosen on 20 November 2026: K1 A, K2 A, the options in bold)

| Choice | A | B |
|---|---|---|
| K1 · Session | **Regular trading hours, 9:30 to 16:00 New York time.** VWAP starts at 9:30, everything closed at 16:00. Same setup as test N, so the results can be compared | Full futures day, 18:00 to 17:00 New York time (CME). VWAP starts at 18:00. The day of firm A also runs this way, with everything closed at 16:10 New York time |
| K2 · Prop firm challenge | **Firm A, 50K evaluation.** Profit target $3,000, maximum loss $2,000 trailing on the end-of-day balance, consistency 55%. No daily loss limit (it is optional). Source: the help centre of firm A, updated 18 and 24 September 2026 [verified] | Firm B, 25K evaluation. Profit target $1,250, maximum loss $1,000 trailing on the end-of-day balance, consistency 40%. Source: the help centre of firm B, 26 August and 18 October 2026 [verified]. The platform used a 25K account of firm B in another reel |

The non-chosen variant of K1 and K2 is reported as supplementary, not deciding.

## 4. Mechanical translation (fixed after approval)

All points below are **[assumption]**: choices to translate the text into rules.

**4.1 Session and days.** According to K1. With A: the open per day as in test N, the jump in tick volume around 16:30 server time; a day counts with at least 90% of the 390 minute bars. With B: from 1:00 to 23:59 server time (18:00 to 16:59 New York time); a day counts with at least 90% of the minutes the file normally has that day.

**4.2 Bars.** 5-minute candles from the M1 data, starting at the session open (with A: 9:30, 9:35, ... 15:55, 78 candles).

**4.3 Indicators.** As in test N, on 5 minutes:
- EMA 9 on the close of the 5-minute candles, continuous across days, only within the session.
- VWAP: restarts every day at the first candle. Price per minute OHLC4, weight tick volume. Value at the close of the candle over all minutes up to and including that candle.

**4.4 Signal.**
- Rule 1, the crossing, at the close of candle t: EMA9(t-1) ≤ VWAP(t-1) and EMA9(t) > VWAP(t). Only from the second candle of the day.
- Rule 2, the confirmation: the first candle k ≥ t+1 with close(k) > EMA9(k), as long as EMA9 stays above the VWAP. If the EMA 9 drops back below the VWAP first (on the close of a candle), the crossing lapses without a trade. I read "wait for" as: the crossing candle itself does not count as confirmation. The variant in which it does count is reported as supplementary.
- Entry at the open of candle k+1. Never at the close of the confirmation candle. No entry on the last candle of the day.

**4.5 Exit.** Rule 3: out when close(j) < EMA9(j), checked from the close of the entry candle, out at the open of candle j+1. Further: everything closed at the close of the last candle of the session. No target and no stop in points (the source names none).

**4.6 One position at a time, long only.** A new crossing while the position is open lapses. Shorts do not exist in this rule.

**4.7 Result.** Per trade in points and in dollars for 1 NQ contract ($20 per point), net after costs. 1 contract is an [assumption]: the source's average win ($292.78) comes to about 14.6 points at 1 contract, which fits 5-minute trades; at 1 micro contract it would be 146 points. Sensitivity: 2 contracts in the prop firm simulation.

## 5. The three fixed rules

**Costs.** The spread from the SPREAD column at the entry minute, plus 1 point of slippage per side, as for USTEC in test N [verified, hypothesis test N]. Sensitivity: slippage 0, 1 and 2 times. In dollars: points × $20. No separate commission; slippage of 1 point per side ($40 per round turn) is wider than the commission of an NQ contract [assumption].

**Order.** The path is run minute by minute. All exits fall on a candle open. In the prop firm simulation the open loss per minute counts (see 6): the lowest price of each minute against the entry, minus costs.

**Control group.** 10,000 runs, seed 43, bootstrap per trading day.
- **Null A, deciding for C3:** the same days, the same session, the same exit rule and the same costs, long only. A sequential process: on each 5-minute candle without an open position (except the first and last of the day) on which the close lies above the EMA 9, chance opens a long with probability p, at the open of the next candle. p is chosen so that the mean number of trades equals that of the rule. Tests whether the crossing with the VWAP adds anything on top of a random entry above the EMA 9 with the same exit.
- **Null A in the challenge, descriptive (since v1.1):** the same simulation of the challenge, with the trades of Null A. 2,000 runs, seed 43.

## 6. The prop firm simulation (fixed)

[assumption, translation of the firm's rules into code; sources in K2]
- **Account:** starting balance according to K2. 1 NQ contract per trade, the rule from 4.
- **Loss limit:** maximum loss below the highest end-of-day balance; the limit only rises and stops at the starting balance (firm A) or at starting balance + $100 (firm B). The challenge fails as soon as the balance including the open loss (lowest price per minute) touches the limit.
- **Target:** reached at the end of a trading day on which the net profit since the start is at least the target and the consistency rule holds. Firm A: best day at most 55% of the target; if the best day is larger, the target becomes best day / 0.55. Firm B: best day at most 40% of total profit. At least 2 trading days.
- **Attempts in sequence (deciding):** the first attempt starts on the first trading day of P1. After pass or fail the next attempt starts on the next trading day, with a new account. An attempt still running at the end of P1 does not count (it is reported).
- **Pass rate** = passed / completed, with 95% interval (Wilson).
- Supplementary: an attempt starting on every trading day (overlapping, descriptive), median duration of an attempt in days.
- No costs for the challenge itself (fee), no payout rules: only the question whether the target is reached.

## 7. Noise check before the real data (fixed)

24 fake markets of 1,500 trading days with minute bars, as in test N (60 sub-steps per minute, no trend, no opening effect, fixed spread, random tick volume), at the price level of the Nasdaq (start 15,000, spread 1 point). Seed 7.

Limits:
- Percentile of the mean net result against Null A on average between 35 and 65, at most 3 of 24 above 95.
- (v1.0, dropped in v1.1) Percentile of the pass rate against Null A in the challenge on average between 35 and 65, at most 3 of 24 above 95. Failed, see the top.

If the script fails this, first find the cause and write a new version of this document, before the real data.

## 8. Data

[verified, measurement log test N] USTEC M1, IC Markets, the same file as test G, SHA-256 714b4cc0..., runs to 5 November 2026, spread column filled from 2019.

Periods:
- **P1, deciding for C1 to C5:** the source's "last 3 years", counted from the post on X: 17 November 2023 to 5 November 2026 inclusive (end of the data).
- Supplementary: 2019 to 16 November 2023.

Data check before the run, metadata only: number of valid sessions per year, share of minutes with an empty spread or zero tick volume.

## 9. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval (Wilson) of the net win rate in P1 lies below 56.6% |
| C2 | The upper bound of the 95% interval (day bootstrap) of the mean net result per trade in P1 lies below 0, or the upper bound of the 95% interval of the profit factor lies below 1.84 |
| C3 | The real mean net result in P1 does not lie above percentile 95 of Null A |
| C4 | The upper bound of the 95% interval (Wilson) of the pass rate (attempts in sequence) lies below 85% |
| C5 | Dropped in v1.1: not deciding, descriptive only |

If C3 falls, the rule is dead: no repair, no optimisation. Below 100 trades the report says "insufficient trades". Below 20 completed attempts the pass rate says "insufficient attempts".

## 10. What I report, whatever the outcome

Number of trades and trades per day (the source: 396 in about 3 years), win rate net and gross, mean net result in points and dollars with 95% interval, profit factor with interval, average win and average loss in dollars (the source: +$292.78 and -$206.97), percentile against Null A, the result without costs, the three cost levels, median trade duration, per year, number of attempts, passed, failed and running, pass rate with interval, pass rate of Null A (descriptive), the rule's pass rate on the fake markets of the noise check, median duration of an attempt, the overlapping pass rate, the non-chosen variants of K1 and K2, the confirmation variant from 4.4, the VWAP without volume, 2 contracts, and 2019 to November 2023.

Title according to the fixed rule: the strategy with the percentage, claimed and measured, for example "9 EMA + VWAP: 85% prop pass rate claimed, X% measured".

## 11. Next step

1. Approved on 20 November 2026 (K1 A, K2 A). SHA-256 in the measurement log. English version alongside.
2. Script `vwap_prop.py`, built on `vwap_control.py`: first a self-test (EMA, VWAP, rule against a second implementation, the challenge against a hand calculation of a few days), then the noise check from 7.
3. Data check from 8, then run 01.
