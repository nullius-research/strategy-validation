# Hypothesis: Supertrend + 200 EMA

Translation of the Dutch original `hypothese-supertrend-200ema.md` (here `hypothesis-v1.0-dutch.md`). The Dutch original, with its own date and SHA-256, is binding.

Date: 17 November 2026 · Source: a strategy-testing channel video, 11 August 2020, transcript with manual subtitles (source file kept private) · Status: **version 1.0, fixed in advance and approved on 17 November 2026 (30 minutes, Supertrend 10, 3, otherwise unchanged), no real data looked at**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule: everything below is fixed before the first run. Nothing is changed after the run. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, transcript] The rules as the source gives them:
- Trend filter: 200-period exponential moving average (EMA). Above the EMA only buy, below it only sell.
- Long: the Supertrend line turns green and flips below the candles while price is still above the 200 EMA.
- Short: the mirror image. The line turns red and flips above the candles, price below the 200 EMA.
- Stop: "at or below the supertrend line" (short: above it).
- Target: fixed, 1.5 times the risk, as in the source's other tests.
- Tested with 100 trades, first on EURJPY, then on EURUSD because the data ran out.
- Result: a win rate of "approximately 46 percent", and a profit with it. Seven wins in a row and seven losses in a row.

[verified, transcript] Not stated in the source: the timeframe, the Supertrend settings, the period, and the number of trades per pair.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | Win rate about 46% at 1.5R | Win rate with confidence interval |
| C2 | The strategy makes a profit ("still a profitable strategy") | Mean net R per trade above zero |
| C3 | The Supertrend flip with the 200 EMA filter picks better moments than chance | Real result against the control group |

## 2. Weak points visible before the test

1. [verified, arithmetic] With a 1.5R target the break-even win rate is 40% (0.4 × 1.5 = 0.6 × 1), before costs. 46% means +0.15R per trade before costs. That is a thin margin: costs of 0.15R per trade use it up.
2. [verified, arithmetic] With 46 wins out of 100 trades the 95% interval (Wilson) is about 36.6% to 55.7%. The lower bound is below the 40% break-even. With 100 trades the source cannot show that the win rate is above break-even.
3. [verified, transcript] The source itself says the stop on the Supertrend line was sometimes too far away. A far stop also puts the 1.5R target far away, which lowers the win rate.
4. [verified, transcript] Timeframe and settings are missing. Every choice below is therefore my translation, with the reason given.

## 3. Mechanical translation (fixed)

Everything below is **[assumption]**: choices to turn the text into rules.

**3.1 Instruments and time.** Main test: EURUSD and EURJPY together, the pairs from the source, on 30 minutes. Reason for 30 minutes: the same source used 30 minutes in its MACD test from the same period, and 30 minutes as the entry timeframe in a later Supertrend video [verified, sources of test A and an article by the source from November 2025]; that the 2020 video also used 30 minutes is not checked [assumption]. M30 bars are built from the M15 exports (two bars per half hour, starting at :00 and :30 server time). Period: everything the exports contain. Additional, reported separately and not decisive: 15 minutes and 1 hour on the same two pairs, and 30 minutes on the other pairs in the same M15 exports.

**3.2 Indicators.**
- Supertrend(10, 3): ATR period 10 with Wilder smoothing, factor 3, on (high + low) / 2. This is the default of TradingView's built-in Supertrend, because the source gives no numbers.
- Bands as usual: lower band = mid − 3 × ATR, upper band = mid + 3 × ATR. The lower band may only rise while the previous close was above it, the upper band only fall while the previous close was below it. Direction turns up when the close ends above the upper band of the same bar (after that adjustment), down when it ends below the lower band of the same bar. Exactly the `pine_supertrend` rule in TradingView's Pine reference [verified, 17 Nov 2026]. The Supertrend line is the lower band in an up direction (green) and the upper band in a down direction (red).
- EMA 200 on the close.
- Everything calculated up to and including the signal bar.

**3.3 Signal (on the close of bar t).**
- Long: direction(t-1) down, direction(t) up, close(t) > EMA200(t).
- Short: direction(t-1) up, direction(t) down, close(t) < EMA200(t).

**3.4 Entry.** Open of bar t+1. Never on the close of the signal bar itself, because the flip is only fixed once the bar has closed.

**3.5 Stop.** Long: the value of the Supertrend line on bar t (the lower band). Short: the value of the line on bar t (the upper band). Fixed, not trailing. If the entry is already beyond the stop (gap at the open), no trade. If the stop is less than 5 pips from the entry (EURJPY 0.05), no trade, as in tests A to D.

**3.6 Target.** 1.5 times the distance from entry to stop. No break-even, no partial profit, no trailing stop, no time limit. Anything still open at the end of the data is closed at the last close.

**3.7 One position at a time per pair.** While a trade is open, new signals on that pair are skipped.

## 4. The three fixed rules

**Costs.** 1.2 pips round trip per trade, the fixed assumption from earlier FX tests [verified, tests A to D]. Sensitivity: 0, 1.2 and 2.0 pips.

**Order.** The path is walked bar by bar on M15, finer than the signal. If one M15 bar touches both stop and target, it counts as a stop. The entry bar itself counts too.

**Control groups.** 10,000 runs per control, seed 19. Bootstrap per trading day, both pairs together.
- **Null A, decisive (coin flip):** the same entry moments as the real trades, random direction, same stop distance mirrored, same 1.5R, same costs. For FX this is the fixed null, because long and short are symmetric [verified, method and control-group audit of 10 November].
- **Null B, additional (timing within the trend):** for each real trade a random bar on the same pair and in the same month on which the Supertrend had the same direction as the trade and the close was on the same side of the EMA200, direction with the trend, stop on that bar's Supertrend line. Tests whether the moment of the flip adds anything on top of the trend state. Known from tests A, B and D: this kind of control can be skewed in favour of the rule on noise [verified, measurement logs]. A high percentile against Null B therefore does not count as evidence.

## 5. Noise check before the real data (fixed)

The script first runs on 24 synthetic random-walk sets (M15, 4 years, EURUSD daily vol 0.5%, EURJPY daily vol 0.6%, seeds 1 to 24, 2,000 runs per set), with no predictability by construction. Limit: mean percentile against Null A between 35 and 65, at most 3 of 24 sets above 95, and a gross win rate around 40%. If the script fails this, first find the cause and write a new version of this document, before the real data.

## 6. Data

[verified, measurement logs A, B and D] The M15 exports contain EURUSD and EURJPY from August 2022 to August 2026, from one broker, broker offset 2. Nothing has been opened for this test. Data check before the run: missing bars, duplicate times, zero or negative prices, jumps.

[verified] The claim is from August 2020. The whole data period therefore lies after the claim.

## 7. When is the idea dead (fixed in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate (both pairs together) is below 46% |
| C2 | The upper bound of the 95% interval of the mean net R (both pairs together) is below 0 |
| C3 | The real result (mean net R) is not above the 95th percentile of Null A |

If C3 falls, the idea is dead: no repair, no optimisation, no other Supertrend settings, stop rules or timeframes. Below 100 trades the report says "insufficient trades".

## 8. What I report, whatever the outcome

Number of trades per pair and together, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A and Null B, result per year, sum of the best 5% of trades next to the total, the three cost levels, the median stop distance in pips against the costs, the longest run of wins and of losses (the source mentions seven and seven), and the additional timeframes and pairs from 3.1.

## 9. Next step

1. Dutch original approved on 17 November 2026. Its SHA-256 is in the measurement log.
2. Measurement script `supertrend_control.py`: first check Supertrend and EMA against a hand calculation, then the noise check from 5.
3. Load the M15 exports, data check, run 01.
