# Hypothesis: "MACD + 200 EMA"

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.0-dutch.md`, fixed on 1 November 2026 before any real data was looked at (SHA-256 of the published Dutch file: 167ae120ab2d29346cfebc747b1f1efed61abf998685d4d55edae6a1820207d3). If the two differ, the Dutch text applies.

Date: 1 November 2026 · Source: video from a trading channel in which the strategy is traded 100 times (transcript) · Status: **fixed in advance, version 1.0, no real data looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, source] The rules as the source gives them:
- Trend filter: 200 EMA. Above the 200 EMA only buy, below it only sell.
- Long: the MACD line crosses above the signal line, and that crossover happens below the zero line.
- Short: the mirror image. MACD line crosses below the signal line, above the zero line, price below the 200 EMA.
- Stop: "below the pullback of the trend".
- Target: in the backtest 1.5 times the risk. Elsewhere in the same source: 25% off at 1R, stop to break-even, the rest at 2R. The source does not reconcile the two.
- Tested on 30-minute charts, first EURUSD, then EURJPY. 1% risk per trade.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | 62 of the 100 trades won, so a win rate of 62% at 1.5R | Win rate with confidence interval |
| C2 | After 100 trades about 50% gain on the account at 1% risk, so about +0.5R per trade | Mean net R per trade |
| C3 | The combination MACD + 200 EMA picks better moments than chance | Real result against the control groups |

[verified] Not testable and outside this measurement: "works on any timeframe and in any market". The source skipped 3 trades with an "unclear" entry. That is a discretionary choice that cannot be reproduced; here every trade counts.

## 2. Weak spots visible before the test

1. [verified, arithmetic] With a 1.5R target, break-even is a win rate of 40% (0.4 × 1.5 = 0.6 × 1), before costs. A claim of 62% means +0.55R per trade, an exceptionally high number for one indicator combination on the most traded currency pairs [assumption that this is exceptional].
2. [verified] With a true win rate of 50%, one hundred trades give a 95% interval of about 40% to 60% [arithmetic, binomial]. A measured 62% over 100 trades therefore does not rule out a true win rate around 50%.
3. [verified] The stop ("below the pullback") is not defined mechanically. Any translation is my choice. That is why it is fixed below, with the reason.
4. [verified] Two different target rules in one source. Here the backtest rule is tested (1.5R), because the 62% belongs to it.

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules.

**3.1 Instruments and timeframe.** Main test: EURUSD and EURJPY on 30 minutes, the pairs from the source. M30 bars are built from the M15 exports (two bars per half hour, starting at :00 and :30 server time). Period: everything the exports contain. Additional, reported separately and not decisive: the same rules on the other seven pairs from the Bollinger test.

**3.2 Indicators.** MACD(12, 26, 9) on the close, the standard setting, because the source gives no numbers. EMA 200 on the close. Everything calculated up to and including the signal bar.

**3.3 Signal (at the close of bar t).**
- Long: MACD(t-1) ≤ signal(t-1) and MACD(t) > signal(t), MACD(t) < 0 and signal(t) < 0, close(t) > EMA200(t).
- Short: MACD(t-1) ≥ signal(t-1) and MACD(t) < signal(t), MACD(t) > 0 and signal(t) > 0, close(t) < EMA200(t).

**3.4 Entry.** Open of bar t+1. Never at the close of the signal bar itself, because the crossover is only fixed once the bar has closed.

**3.5 Stop ("below the pullback").** Long: lowest low of the last 10 bars up to and including t. Short: highest high of the last 10 bars up to and including t. Ten bars on 30 minutes is 5 hours, about the length of a pullback in the source's examples [assumption, not measured]. If the stop is less than 5 pips from the entry (EURJPY 0.05), no trade. Lesson from the supply-demand test: stops that are too tight get eaten by costs [verified in that test].

**3.6 Target.** 1.5 times the distance from entry to stop. No break-even, no partial profit. No time limit. Anything still open at the end of the data is closed at the last close.

**3.7 One position at a time per pair.** If a trade is open, new signals on that pair are dropped. As the source describes it: one trade after the other [assumption that the source worked this way].

## 4. The three fixed rules

**Costs.** 1.2 pips round trip per trade, the fixed assumption from earlier tests [verified, project handover document]. Sensitivity: 0, 1.2 and 2.0 pips.

**Order of events.** The path is followed bar by bar on M15, so finer than the signal. If one M15 bar hits both stop and target, it counts as a stop.

**Control groups.** 10,000 runs per control, seed 19. Bootstrap per trading day, both pairs together.
- **Null A, decisive (coin flip):** the same entry moments as the real trades, random direction, same stop distance mirrored, same 1.5R, same costs. For FX this is the right null, because long and short are symmetrical [verified, method].
- **Null B, additional (timing within the trend):** per real trade a random bar on the same pair and in the same month on which the close was on the same side of the EMA200, direction according to the trend, same stop rule as 3.5. Tests whether the MACD crossover adds anything on top of the trend filter.

## 5. Data

[verified, README on GitHub] The M15 exports of the Bollinger test contain nine pairs, including EURUSD and EURJPY, from August 2022 to August 2026, from one broker. [assumption] The raw files are still in a local folder. That folder is not connected yet; nothing has been opened yet.

[verified, arithmetic] Four years is about 50,000 M30 bars per pair (48 per trading day, about 260 trading days per year). How many signals that gives is unknown until the synthetic check [assumption].

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate is below 62% |
| C2 | The upper bound of the 95% interval of the mean net R is below +0.5R |
| C3 | The real result (mean net R) is not above percentile 95 of Null A |

If C3 falls, the system is dead according to step 5: no repairs, no optimisation, no other MACD settings or stop rules. Below 100 trades per pair, the report says "insufficient trades" for that pair; the two pairs together are then decisive.

## 7. What I report, whatever the outcome

Number of trades per pair, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A and Null B, result per year, share of the best 5% of trades in the total, the three cost levels, and the median stop distance in pips against the costs.

## 8. Next step

1. The document is approved or adjusted. After that it is fixed.
2. Write the measurement script `macd_control.py` and first run it on synthetic random-walk data (M15, 4 years, two pairs). There the verdict "dead" should come out. Only then the real data.
3. Connect the folder `Documents\trading` for the M15 exports.
