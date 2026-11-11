# Hypothesis: Bollinger Bands + 200 EMA (test D)

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.0-dutch.md`, fixed on 7 November 2026 before any real data was opened (SHA-256 of the published Dutch file: 17d5ebed1166f829a3fb9dc1f318470f7d49d340b2448e715be2b3e00d94933d). If the two differ, the Dutch text applies.

Date: 7 November 2026 · Source: a video from a testing channel (2020) and an open-source script by a third party that works out that strategy (2020); the source with its name is kept in the private project files · Status: **version 1.0, fixed and approved on 7 November 2026, no real data looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, transcript and script] The rules as the sources give them:
- Trend filter: 200 EMA. Above the 200 EMA only buy, below it only sell.
- Bollinger Bands: 20 periods, 2 standard deviations around an SMA (length 20 only in the script).
- Long: price above the 200 EMA, price touches the lower band.
- Short: price below the 200 EMA, price touches the upper band.
- Stop: not given, set by hand in the video.
- Target: 1.5 times the risk.
- Tested on EURUSD, 15 minutes, 100 trades, by hand.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | Win rate 52% at 1.5R | Win rate with 95% interval |
| C2 | $1,000 became $1,622.60 after 100 trades; together with 52% at 1.5R that is about +30R, so about +0.30R per trade [verified, calculation: 52 x 1.5R - 48 x 1R = +30R] | Mean net R per trade |
| C3 | The combination Bollinger + 200 EMA picks better moments than chance | Real result against the control group |

[verified] Not testable and outside this measurement: the advice to combine the strategy with price action, support and resistance, or supply and demand zones. That is discretionary.

## 2. Weak spots visible before the test

1. [verified, arithmetic] With a 1.5R target, break-even is a win rate of 40% before costs. On a random walk without drift, 40% is also the expected win rate. The claim of 52% is 12 percentage points higher.
2. [verified, binomial] With a true win rate of 40%, the chance of 52 or more winners in 100 trades is 1.0%. With a true win rate of 52%, the 95% interval over 100 trades is about 42% to 62%.
3. [verified] In the source, the stop is a manual choice per trade. Any fixed stop is my translation. The same goes for the entry moment. Both are fixed below.
4. [verified] The script and the video come from different makers. The script is a third party's interpretation of the video [verified, script description]. Where they differ, this test follows the script, because it is the only mechanical version.
5. [assumption] The source's period is unknown; the screen probably shows May 2020. This test measures a different period.

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules. Chosen before opening the data, on 7 November 2026: stop A (swing) and entry X (close of the signal bar).

**3.1 Instruments and timeframe.** Main test: EURUSD on 15 minutes, the pair and timeframe of the source. Period: everything the export contains. Additional, reported separately and not decisive: the same rules on the other pairs from the same M15 exports.

**3.2 Indicators.** On the close, calculated up to and including the signal bar:
- EMA 200.
- Middle line SMA 20; bands at plus and minus 2.0 times the standard deviation of the last 20 closes (population standard deviation, as in the source script) [assumption about the definition in the source script].

**3.3 Signal on bar t, exactly as in the script code.**
- Long: low(t) > EMA200(t) and low(t) < lowerband(t) and not low(t-1) < lowerband(t-1).
- Short: high(t) < EMA200(t) and high(t) > upperband(t) and not high(t-1) > upperband(t-1).

**3.4 Entry (X).** At the first price after the close of the signal bar, so the open of bar t+1. The signal is only fixed once bar t has closed.

**3.5 Stop (A).** Long: lowest low of the last 10 bars up to and including t. Short: highest high of the last 10 bars up to and including t. The same rule as in test A (MACD + 200 EMA), so the series stays comparable. On 15 minutes that is 2.5 hours. If the stop is less than 5 pips from the entry (JPY pairs 0.05), no trade.

**3.6 Target.** 1.5 times the distance from entry to stop. No break-even, no partial profit, no time limit. Anything still open at the end of the data is closed at the last close.

**3.7 One position at a time per pair.** If a trade is open, new signals on that pair are dropped [verified, script description].

## 4. The three fixed rules

**Costs.** 1.2 pips round trip per trade, the fixed assumption from earlier tests [verified, project handover document]. Sensitivity: 0, 1.2 and 2.0 pips.

**Order of events.** The path is followed bar by bar on M15. If one bar hits both stop and target, it counts as a stop. The entry bar t+1 itself also counts.

**Control group.** 10,000 runs, seed 19. Bootstrap per trading day.
- **Null A, decisive (coin flip):** the same entry moments as the real trades, random direction, same stop distance mirrored, same 1.5R, same costs. For FX this is the right null [verified, method].
- **Null B, additional (timing within the trend):** per real trade a random bar on the same pair and in the same month on which the low was above (long) or the high below (short) the EMA200, direction according to the trend, same stop rule as 3.5. Tests whether the band touch adds anything on top of the trend filter. Known from tests A and B: on noise, Null B is skewed in favour of the rule [verified, measurement logs A and B]. A high percentile against Null B therefore does not count as evidence.

## 5. Data

[verified, measurement logs A and B] The M15 exports contain EURUSD from August 2022 to August 2026, from one broker, broker offset 2. Nothing has been opened for this test yet.

[verified, arithmetic] Four years is about 100,000 M15 bars. How many signals that gives is unknown until the synthetic check [assumption].

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate on EURUSD is below 52% |
| C2 | The upper bound of the 95% interval of the mean net R on EURUSD is below +0.30R |
| C3 | The real result on EURUSD (mean net R) is not above percentile 95 of Null A |

If C3 falls, the idea is dead according to step 5: no repairs, no optimisation, no other band settings, stop rules or timeframes. Below 100 trades the report says "insufficient trades".

## 7. What I report, whatever the outcome

Number of trades, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A and Null B, result per year, sum of the best 5% of trades next to the total, the three cost levels, the median stop distance in pips against the costs, and the longest losing streak (the source mentions five).

## 8. Next step

1. Approved on 7 November 2026, before the first run.
2. Write the measurement script `bb200_control.py` and first run it on 24 synthetic random-walk sets (M15, 4 years). There a win rate around 40% and an even spread of the Null A percentiles should come out. Only then the real data.
