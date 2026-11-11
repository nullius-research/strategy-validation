# Hypothesis: Stochastic + RSI + MACD

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.0-dutch.md`, approved on 5 November 2026 before any real data was looked at. On 11 November 2026 two references were removed from that file and from the repository history: a local folder path and the name of a product. Rules, numbers and thresholds are unchanged. SHA-256 of the Dutch file as first published: f500665b6683e9741dd884c008d3f281155e43e84ec0a36327eddd7cf18f6a78; as published now: 2e01a27ff844fd1795d2036aab1da39b2d2e546ca91ec47f730e39938141f31b. If the two texts differ, the Dutch text applies.

Date: 5 November 2026 · Source: a YouTube video from a trading channel (uploaded March 2021) that tests the strategy 100 times. Read via the automatic English transcript (266 segments) · Status: **fixed in advance, version 1.0, approved on 5 November 2026, no real data looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing changes. If a choice turns out to be untenable, a new version with a new date follows, and this result stays.

Naming rule: this version names no channel or maker. Otherwise identical to the internal document fixed before the run.

## 1. What the source promises

[verified, transcript] The rules as the source gives them:
- Stochastic gives the main signal. Long: wait until the K and D lines are both oversold.
- RSI as trend filter: set the levels in the settings to 50. Above 50 only buy, below 50 only sell.
- MACD as confirmation: then wait until the MACD line crosses above the signal line.
- In addition, both stochastic lines must not have been overbought since the oversold moment.
- Short: the mirror image.
- Stop: long below the nearest swing low, short above the nearest swing high.
- Target: 1.5 times the stop.
- Backtest: EURUSD, 30 minutes, starting capital 1,000, 2% risk per trade, leverage 200.
- One position at a time; signals during an open trade are dropped.

[verified, transcript] Reported outcome: 100 trades in 134 days, win rate 56%, longest streak 5 wins and 3 losses, profit 280.41 dollars, about 28% on 1,000.

[verified, transcript] After the backtest the source names an improvement: limit the stop to 0.15%. That was not part of the 100 trades.

[verified] Not in the source: settings of stochastic, RSI and MACD, the levels for oversold and overbought, the definition of a swing low, the period of the 134 days, costs.

Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | Win rate 56% at a 1.5R target | Win rate with 95% interval |
| C2 | About 28% profit on 100 trades at 2% risk, so about +0.14R per trade | Mean net R per trade |
| C3 | The combination picks better moments than chance | Real result against the control groups |

## 2. Weak spots visible before the test

1. [verified, arithmetic] Break-even at 1.5R is a win rate of 40%, before costs. A win rate of 56% means +0.40R per trade.
2. [verified, arithmetic] The source's two numbers do not match. 56 wins of 1.5R and 44 losses of 1R is +40R. At 2% risk per trade that is about +80% without compounding, not 28%. A profit of 28% is +14R, which at 1.5R belongs to a win rate of about 45.6%. Possible explanations, none of them checked: costs or slippage, a risk per trade other than 2%, targets or stops that were placed differently in practice, or a calculation error. [assumption: which one it is cannot be determined from the video]
3. [verified, arithmetic, binomial] At 100 trades and 56%, the 95% interval runs from about 46% to 66%.
4. [verified] Settings, levels and the swing low are not defined mechanically. Every translation below is my choice, with a reason.
5. [verified] The source tested one period of 134 days in or before early 2021. This measurement uses 2022 to 2026. A difference can therefore also come from the period; that is stated in every report.
6. [assumption, not re-measured] A public TradingView implementation (2021) reports that the rules give hardly any signals, in crypto. Here the number of signals per month is reported.

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules.

**3.1 Instrument and timeframe.** Main test: EURUSD on 30 minutes, as in the source. M30 bars are built from the M15 exports (two bars per half hour, starting at :00 and :30 server time). Period: everything the export contains. Additional and not decisive: the same rules on the other eight pairs from the M15 set.

**3.2 Indicators, all on the close, up to and including the signal bar.**
- Stochastic: %K 14, %K smoothing 1, %D 3, levels 20 and 80. These are the TradingView defaults; the source gives no numbers.
- RSI 14 (Wilder), level 50, as in the source.
- MACD 12, 26, 9, the standard.

**3.3 Oversold and overbought.** Oversold on bar s: K(s) < 20 and D(s) < 20, on the same bar ("both the K and D lines"). Overbought on bar s: K(s) > 80 and D(s) > 80. The same definition on both sides, so that "not yet overbought" and "overbought" mean the same thing.

**3.4 Setup.**
- The long setup switches on at the first oversold bar s. A following oversold bar keeps it on.
- The long setup expires at the first overbought bar after s. On that bar the short setup switches on.
- Short setup: mirror image.
- Maximum waiting time: one trading day, so 48 M30 bars from and including bar s. A trigger on bar t only counts if t ≤ s + 47. Weekend bars do not exist and therefore do not count. The source gives no limit; this is a choice by the researcher (5 Nov 2026, before the first run), because a setup without a limit can stay open for days. A rolling window of 48 bars and not the end of the calendar day, so that every setup lives equally long. A new oversold bar resets the window to 48.
- A setup is used up at the first valid trigger, even if a position is already open at that moment (that trigger is then dropped).

**3.5 Trigger (at the close of bar t, with t ≥ s).**
- Long: long setup on, MACD(t-1) ≤ signal(t-1) and MACD(t) > signal(t), RSI(t) > 50.
- Short: short setup on, MACD(t-1) ≥ signal(t-1) and MACD(t) < signal(t), RSI(t) < 50.

**3.6 Entry.** Open of bar t+1. Never at the close of the signal bar, because the crossover is only fixed once that bar has closed.

**3.7 Stop ("nearest swing low").**
- Swing low: an M30 bar whose low is lower than the lows of the 2 bars before and the 2 bars after (5-bar fractal). A swing low on bar j is only known after bar j+2 closes, so only swings with j+2 ≤ t count.
- Long stop: the low of the most recent known swing low below the entry price, searched in the last 50 bars up to and including t. Short: mirror image with swing highs above the entry.
- No buffer beyond the swing; the costs are in the R.
- No swing found, or stop less than 5 pips from the entry: no trade. Lesson from the supply-demand test: stops that are too tight get eaten by costs [verified in that test].

**3.8 Target and exit.** Target 1.5 times the distance from entry to stop. No break-even, no partial profit, no time limit. Anything still open at the end of the data closes at the last close.

**3.9 One position at a time**, as in the source [verified, transcript].

**3.10 Variant with stop limit, fixed in advance and not decisive.** After the backtest the source recommends limiting the stop to 0.15%. Interpretation here: if the stop distance is larger than 0.15% of the entry price, the stop goes to 0.15% and the target to 1.5 times that distance. The timing and direction of the trades stay the same. Reported separately. This is not a repair afterwards: it is written here before the run.

## 4. The three fixed rules

**Costs.** 1.2 pips round trip per trade, the fixed assumption from earlier tests [verified, project handover document]. Sensitivity: 0, 1.2 and 2.0 pips.

**Order of events.** The path is followed bar by bar on M15, finer than the signal. If one M15 bar hits both stop and target, it counts as a stop.

**Control groups.** 10,000 runs per control, seed 19. Bootstrap per trading day.
- **Null A, decisive (coin flip):** the same entry moments as the real trades, random direction, same stop distance mirrored, same 1.5R, same costs. For FX the right null, because long and short are symmetrical [verified, method].
- **Null B, additional (stochastic and MACD on top of the RSI filter):** per real trade a random M30 bar on the same pair and in the same month on which the RSI was on the same side of 50, direction according to the RSI, same stop rule as 3.7. Note: in the MACD test, Null B was skewed in favour of the rule, also on noise data [verified, MACD measurement log]. That is why Null B is first run on the noise sets here, and the distribution on noise is put next to the real percentile.

## 5. Data

[verified, Bollinger test] The M15 set contains nine pairs: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY, USDCHF, USDCAD, NZDUSD, EURGBP, from August 2022 to August 2026, one broker.
[assumption] The raw files are in a local folder (`Documents\trading`), as for the MACD test. Not yet opened for this test.
[assumption] At the same frequency as the source (100 trades in 134 days), four years of EURUSD gives roughly 1,000 trades. The real number only shows in the run.

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate is below 56% |
| C2 | The upper bound of the 95% interval of the mean net R is below +0.14R |
| C3 | The real result (mean net R, EURUSD) is not above percentile 95 of Null A |

C2 uses the lower of the source's two numbers (+0.14R from the 28%, not +0.40R from the win rate), so the test is not stricter than the source itself.

If C3 falls, the system is dead: no repairs, no optimisation, no other settings, levels or stop rules. Fewer than 100 trades on EURUSD: the report says "insufficient trades" and no verdict follows. Per additional pair below 100 trades: "insufficient" for that pair.

## 7. What I report, whatever the outcome

Number of trades per pair and per month, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A and Null B (plus Null B on noise), result per year, share of the best 5% of trades, the three cost levels, the median stop distance in pips against the costs, the number of signals dropped for having no swing or a stop below 5 pips, and the variant with stop limit.

## 8. Next step

1. Approved on 5 November 2026, with the waiting time of one trading day. The document is fixed.
2. Write the measurement script `srm_control.py` (partly from `macd_control.py`) and first run it on synthetic random-walk data (M15, 4 years, nine pairs). There "dead" should come out, and Null B on noise is recorded. Only then the real data.
3. After that option C (MACD, stop 1.5 ATR, target 1 ATR); that needs an export of EURNZD M15.
