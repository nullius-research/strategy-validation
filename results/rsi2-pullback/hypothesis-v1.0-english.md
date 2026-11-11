# Hypothesis: RSI(2) pullback on the S&P 500 (test E)

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.0-dutch.md`, fixed on 8 November 2026 before any price data was opened (SHA-256 of the published Dutch file: 1923f4bfe0685de781de08b261d0697dd9d2cade784dbf0baadc10f3797c91b1). If the two differ, the Dutch text applies.

Date: 8 November 2026 · Source: an article by a trading author (21 Feb 2007); the source with its name is kept in the private project files · Status: **version 1.0, fixed and approved on 8 November 2026 (Null A decisive, P0 via the browser pane, Wilder RSI), no price data looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, article] Rules: S&P 500 above its 200-day SMA; RSI(2) below 65 on day 1, lower than day 1 on day 2, lower than day 2 on day 3; buy at the close of day 3; sell when RSI(2) closes above 75. Long only. No stop.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | 84.31% of trades are profitable (86 of 102, 1995 through 2006) | Win rate with 95% interval |
| C2 | The rule makes money: 1,013.90 points in 12 years | Mean net return per trade in percent, with interval |
| C3 | The entry (three falling RSI days in a rising market) picks better days than chance | Real result against the control group |

## 2. What makes this design strong, and weak spots in advance

1. [verified] The claim has a fixed end date: 31 December 2006. The source could not see anything after that. The decisive measurement is therefore 1 January 2007 through the last available day: a real out-of-sample test.
2. [verified, Wilson interval] Even if 84.31% is the true win rate, the 95% interval over 102 trades runs from 76.0% to 90.1%. A lower win rate in another period only means something if it drops below 76%.
3. [assumption] An exit without a stop on an index with upward drift often gives a high win rate, even with random entries: wait long enough and you usually see a rising day. A high win rate alone therefore says little; C3 decides.
4. [assumption] The rule resembles Buy the Dip (test of 2 Nov, not falsified): both buy a short dip in an index. The results are not independent of each other.
5. [verified] The source says nothing about costs. On an index ETF or future, the cost per round trip is small compared with an average trade [assumption, measured].

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules.

**3.1 Market and data.** S&P 500 price index (^GSPC), daily closes from Yahoo Finance, the same source as Buy the Dip (3 Jan 2000 to 30 Oct 2026, not yet opened for this test). The replication of 1995 to 2006 needs a longer series, from 1994 (see 5).

**3.2 RSI(2).** Wilder RSI with period 2 on the close (smoothing with alpha 1/2, the standard calculation on most platforms). Warm-up: the first 250 days do not count.

**3.3 SMA 200.** Simple average of the last 200 closes, up to and including the signal day.

**3.4 Signal on day t (= day 3).** close(t) > SMA200(t), and RSI(t-2) < 65, and RSI(t-1) < RSI(t-2), and RSI(t) < RSI(t-1). The filter applies on day 3, the day of entry [assumption: the source does not say on which day].

**3.5 Entry.** At the close of day t.

**3.6 Exit.** At the close of the first day after entry on which RSI(2) closes above 75. No stop, no time limit. Still open at the end of the data: close at the last close and report separately.

**3.7 One position at a time.** A new signal during an open trade is ignored.

## 4. The three fixed rules

**Costs.** 2 basis points round trip per trade, the same as Buy the Dip [verified, buy-the-dip README]. Sensitivity: 0, 2 and 4 bp.

**Order of events.** Entry and exit at closes; the rule has no stop or target within the day, so the intraday path plays no part [verified, rules]. The deepest interim drop per trade (on closes) is also measured, because without a stop that is where the risk is.

**Control group.** 10,000 runs, seed 23.
- **Null A, decisive:** random entry day from the days on which the close is above the SMA200 (same filter as the rule), same exit rule (RSI(2) above 75), same number of trades, one position at a time. Tests whether the three falling RSI days add anything on top of the trend filter.
- **Null B, additional:** random entry day without the filter, same exit rule. Equal to Null A of Buy the Dip, so the two tests are comparable.

[assumption, chosen on 8 Nov] Null A with the filter is stricter than the null of Buy the Dip. With Null B as decisive, the rule would also get credit for the trend filter, which has been known for decades.

## 5. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P0 | 1 Jan 1995 to 31 Dec 2006 | Replication: do we get close to 102 trades and 84.31%? A check of the calculation, not decisive |
| P1 | 1 Jan 2007 through the last day | **Decisive**: outside the source's period |
| P2 | per year within P1 | Spread over the years, not decisive |

Additional and not decisive: the same rules on the Nasdaq 100 (^NDX) in P1.

[verified, buy-the-dip README] The existing Yahoo series starts on 3 January 2000. P0 needs ^GSPC from January 1994 (200 days of warm-up plus RSI); I fetch it the same way as for Buy the Dip. If that fails, P0 is dropped and P1 remains decisive.

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate in P1 is below 84.31% |
| C2 | The upper bound of the 95% interval of the mean net return per trade in P1 is below 0 |
| C3 | The mean net return per trade in P1 is not above percentile 95 of Null A |

If C3 falls, the idea is dead: no repairs, no optimisation, no other RSI thresholds, filters or exit rules. Fewer than 100 trades in P1: "insufficient trades".

If C3 stands, I report it as "not falsified", with the limitations, and not as "works".

## 7. What I report, whatever the outcome

Number of trades, win rate with interval, mean net return per trade with bootstrap interval, profit factor, percentile against Null A and Null B, result per year, mean and longest duration, largest loser, deepest interim drop per trade, sum of the best 5% of trades next to the total, the three cost levels, and the return of buy and hold over the same period for comparison (not a control group).

## 8. Next step

1. Approved on 8 November 2026. The SHA-256 of the original is in the private measurement log.
2. Write the measurement script `rsi2_control.py` and first run it on 24 synthetic series (random walk with the drift and volatility of an index, chosen before seeing ^GSPC: 7% per year, 18% volatility [assumption]). There the rule should on average not do better than Null A, and the percentiles should be evenly spread. Only then the real data.
