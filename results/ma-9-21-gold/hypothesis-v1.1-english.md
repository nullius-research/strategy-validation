# Hypothesis: MA 9/21 crossover with 200 MA on gold (test F), version 1.1

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.1-dutch.md`, fixed on 9 November 2026 before any price data was looked at (SHA-256 of the published Dutch file: 19a44d985408a42450efe3b5029c3d53a638dd262f124b129aad47125445bd89). If the two differ, the Dutch text applies.

Date: 9 November 2026 · Source: a trading video with article (15 Nov 2025); the source with its name is kept in the private project files · Status: **version 1.1, 9 November 2026, approved (option A). Replaces v1.0 only in the control group (4), because v1.0 failed the noise check (see measurement log, not published; outcome in noise_24sets_v1.0_failed.txt). Rules, periods and thresholds unchanged. No price data looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, article] Gold (XAUUSD). Daily filter: price above the 9 EMA on the daily chart, plus hand-drawn boxes around slow markets. Entry on 30 minutes: long when the 9 MA crosses above the 21 MA, at the close of that candle; the candle is above both MAs; price and both MAs above the 200 MA. Target 1.5 times the stop distance. No stop given. Long only.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | Win rate around 58% over 100 trades in the "good market" | Win rate with 95% interval |
| C2 | The rule makes money: around +45% at 1% risk, so about +0.45R per trade before costs | Mean net R per trade with interval |
| C3 | The entry (crossover with the candle above the MAs) picks better moments than chance within the same trend | Real result against the control group |

## 2. Weak spots, named in advance

1. [verified] The 58% belongs to trades picked by hand (outside the drawn boxes). Those boxes cannot be reproduced. This test measures only the mechanical part: daily filter, crossover, 200 MA and stop. A lower win rate can therefore also come from leaving out the manual selection. This is stated in every publication.
2. [verified] The source gives no stop. The stop is our choice (3.6), the same as in tests A and D. A different stop gives a different result; we do not try another.
3. [verified, arithmetic] Break-even at 1.5R is 40% before costs. On a random walk without drift, 40% is also the expected win rate.
4. [assumption] Gold rose strongly in 2024 and 2025. A long-only rule gets a tailwind there. That is why the decisive period is the time outside 2024-2025, and why the control group is long within the same filter.
5. [verified, Wilson interval] Even if 58% is the true win rate, the 95% interval over 100 trades runs from 48.2% to 67.2%.

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules. Chosen on 9 November 2026.

**3.1 Data.** `XAUUSD_M30_199804220000_202611052200.csv`, MT5 export, 9 Nov 2026, SHA-256 c7d40c32a3d53f7ccfcc199b51d910daccaeafc2e6f996a0a9e1925aa684d7d2. Broker time. Daily bars are built from the M30 bars per broker date.

**3.2 Usable data.** The export runs from 1998, but old M30 data is often sparse. The measurement starts in the first calendar month in which every trading day has at least 40 M30 bars. This is a completeness check, not a choice based on prices. Warm-up: the first 300 M30 bars and 30 days after that start do not count.

**3.3 MAs.** EMA 9, EMA 21 and EMA 200 on the M30 close. Daily filter: EMA 9 on the daily close.

**3.4 Daily filter.** On M30 bar t: the close of the previous completed day is above that day's EMA 9. The current day does not count, otherwise the filter looks ahead.

**3.5 Signal on M30 bar t.** All five at once:
- EMA9(t) > EMA21(t) and EMA9(t-1) ≤ EMA21(t-1) (the crossover happens on bar t);
- low(t) > max(EMA9(t), EMA21(t)) (the whole candle is above both MAs, "not crossing them");
- close(t) > EMA200(t);
- EMA9(t) > EMA200(t) and EMA21(t) > EMA200(t);
- daily filter true.

**3.6 Entry, stop and target.** Entry at the close of bar t. Stop A: lowest low of the last 10 M30 bars up to and including t (5 hours), the same as tests A and D. Target: entry + 1.5 × (entry − stop). Minimum stop 1.00 USD; if the stop is smaller, no trade (at 0.40 USD costs, more than 40% of the stop would otherwise go to costs).

**3.7 Exit.** The path is followed bar by bar from bar t+1. If one bar hits both stop and target, it counts as a stop. If a bar opens beyond the stop (a gap, for example after the weekend), exit at that bar's open. If it opens beyond the target, exit at the target. Positions run through nights and weekends. Still open at the end of the data: close at the last close and report separately.

**3.8 One position at a time.** A signal during an open trade is dropped.

## 4. The three fixed rules

**Costs.** 0.40 USD per ounce round trip (spread plus slippage) [assumption: a common spread on XAUUSD is around 0.20 to 0.35 USD]. Sensitivity: 0, 0.40 and 0.80 USD. Additional: the median spread from the SPREAD column of the export, reported only, not decisive.

**Order of events.** See 3.7. The entry bar t+1 itself also counts.

**Control group (v1.1).** 10,000 runs, seed 23. A random process that, like the rule, walks through time, one position at a time: after each exit (or at the start) a waiting time, drawn from the rule's own waiting times in the same period; then long on the next allowed bar. Stop distance drawn from the rule's stop distances (20 quantiles), target 1.5R, same costs, same path rules (3.7). The number of trades follows from the process and is lower than for the rule; what is compared is the mean net R per trade.
- **Null A, decisive:** allowed bars = the same trend context (daily filter true, close, EMA9 and EMA21 above EMA200), without the crossover and without the candle rule. Tests whether the crossover adds anything on top of the trend.
- **Null B, additional:** allowed bars = all bars. Shows how much the trend itself delivers.

Why not as in v1.0 [verified, noise check 9 Nov]: with random trades without overlap and stop A per bar, the rule scored above percentile 95 on 24 noise series in 13 cases. Causes: larger stops for the rule (costs weigh less in R) and a preference for short, more often losing trades in the drawing without overlap. With the control group of v1.1: mean percentile 46.0, above 95 in 0 of 24.

A coin flip is not the right null here: the rule is long only, on a market with upward drift [verified, method].

## 5. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P0 | 1 Jan 2024 to 14 Nov 2025 | Probable period of the source [assumption: the source gives no dates]. For comparison, not decisive |
| P1 | Start of usable data (3.2) to 31 Dec 2023, plus 1 Jan 2026 to the last bar | **Decisive**: outside 2024-2025 |
| P2 | per year | Spread over the years, not decisive |

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate in P1 is below 58% |
| C2 | The upper bound of the 95% interval of the mean net R per trade in P1 is below 0 |
| C3 | The mean net R per trade in P1 is not above percentile 95 of Null A |

If C3 falls, the idea is dead: no repairs, no optimisation, no other MAs, stops or filters. Fewer than 100 trades in P1: "insufficient trades".

If C3 stands, I report it as "not falsified", with the limitations, and not as "works".

## 7. What I report, whatever the outcome

Number of signals and how many drop out because of the minimum stop, number of trades, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A and Null B, result per year, the three cost levels, median stop distance in USD against the costs, longest losing streak, sum of the best 5% of trades next to the total, and P0 next to the claim.

## 8. Next step

1. SHA-256 of this version in `meetlog-ma-9-21-goud.md`.
2. Run the measurement script `ma921_control.py` first on 24 synthetic series (random walk with the volatility of gold, 15% per year, and drift 0 and 8% per year [assumption, chosen before seeing the data]). There the rule should on average not do better than Null A, and the percentiles should be roughly evenly spread. Only then the real data.
