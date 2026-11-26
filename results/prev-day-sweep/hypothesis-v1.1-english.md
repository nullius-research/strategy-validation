# Hypothesis: previous-day sweep with 1-hour trend on the Nasdaq 100 (test S)

Translation of `hypothese-prev-day-sweep.md` (Dutch, binding). Date: 23 November 2026 · Source: YouTube video of 17 November 2026 by a trading channel, with a free session indicator (open source code) · Status: **version 1.1, 23 November 2026, registered in advance by the daily task, no real price data opened for this test yet**

Change from v1.0 (23 November 2026, SHA-256 1f70d61a...): only the definition of Null T in 5 (supplementary, not decisive). In v1.0 Null T picked a random moment on the same day and in the same kill zone, also before the sweep, with the trend as direction. Because the trend almost always gives the same direction as the real trade, that control saw the sweep itself in the path: a long entering before the dip is often stopped by the dip. On the noise check this gave a false advantage to the rule (mean percentile 85.1, 10 of 24 above 95). Null B (coin flip on direction) and Null A met the threshold (47.7 and 50.6). v1.1: Null T picks a random valid day from the same period, so the control knows nothing about the sweep. Repair round 1 of at most 2, before any run on real data.

Choices: all choices in section 3 are "daily-task choice (recommended option), approved in advance by Erwin on 22 Nov 2026" (instruction `opdracht-dagelijkse-test.md` v2). Nothing changes after run 01.

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a measurement choice

Rule of play: everything below is fixed before the first run. Nothing is changed after the run. If a choice proves untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, video description and transcript, script description] The rule:
- Times in New York time. The trading day starts at 20:00. London kill zone 02:00 to 05:00, New York kill zone 07:00 to 11:00.
- Setup "previous-day sweep": "inside the London or New York kill zone price trades through yesterday's high/low and closes back inside." Through yesterday's high and back inside: short. Through the low and back inside: long.
- Confirmation "higher-timeframe trend": "close vs an EMA on a higher timeframe (default 1h EMA 200), using the last completed higher-timeframe bar". Long only above, short only below.
- "Every signal enters at the next candle's open." Stop "past the sweep extreme, with a minimum of 0.5 × ATR 14". Exit: "hold to 16:00 New York".
- "One signal per setup per weekday. If both sides of a range are taken before a close back inside, that day is skipped."
- Costs in the video: "Nasdaq / S&P CFD 0.01 % per side".

[verified, video description] The result the video reports:
- "Nasdaq 100 · previous-day sweep + 1 hour trend · 5 min · hold to 16:00 New York — profit factor 1.95 (290 trades; 1.95 on 2021–24, 1.96 on 2025–26). On 15 min: 2.20."
- "about 70 % of the trades lose", in the transcript "71% of these trades lost".
- "without the 5 best days the Nasdaq setup is close to break even" (transcript: profit factor "about 1.1"), "the longest losing streak was 18 trades".
- Transcript: without the trend filter profit factor 1.11 on the old data and 0.84 on the new; 2024 as a whole a losing year; January to September 2026 33 trades, 5 winners, -23 R.
- The settings were chosen from 26,825 backtests on 2021-2024 and checked once on 2025-2026.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | "profit factor 1.95" after costs | Net profit factor in R over P1 |
| C2 | The sweep with trend filter is an edge ("The edge is real") | Mean net R per trade against the control group with a random entry moment in the same kill zone and a random direction (Null B) |
| C3 | "1.95 on 2021–24, 1.96 on 2025–26": it holds on the years it was chosen on and on the new years | Net profit factor per sub-period |

Descriptive, not decisive: number of trades (290 in 2021-2026), share of losers (about 70%), profit factor without the 5 best days (about 1.1), longest losing streak (18), 2024 negative, January to September 2026, the 15-minute variant (2.20), the video's cost level, the control group with the trend as direction (Null T, see 5).

## 2. Weak spots visible before the test

1. [verified, transcript] The setting was chosen from 26,825 combinations. Even though 2025-2026 was checked separately, the choice of market, setup, confirmation, timeframe and exit was made on the same years. Part of the result may come from that choice. Our test on data from another source, with a control group, is therefore the core.
2. [verified, transcript] The maker says the profit comes from a few big trend days. The result is therefore sensitive to a few days. We report it without the 5 best days.
3. [verified] The Pine source code was not read for this test; the rules come from the script description and the transcript. Where these are not unambiguous (which "yesterday", when a level is "taken", what happens if the trend does not agree on the close-back candle), section 4 fixes a choice. A difference with the script can come from that.
4. [verified, earlier tests N, O, R] Our data is a CFD on the Nasdaq 100 (USTEC, IC Markets) with tick volume. According to its description the video also used a Nasdaq CFD, from another provider [assumption, the provider is not named].
5. [assumption] Our costs (spread from the data plus 1 point slippage per side) are close to the video's level (0.01% per side is about 2 points per side at a price of 20,000). We report both.
6. [verified, test R] The data server is on New York time + 7 hours all year. This was checked for the 9:30 open; for the night hours we assume the same [assumption].

## 3. Choices (daily-task choice, recommended option in bold, approved in advance by Erwin on 22 Nov 2026)

| Choice | A | B |
|---|---|---|
| K1 · Decisive claim, market and timeframe | **The maker's claim: Nasdaq 100 (USTEC), 5 minutes, previous-day sweep + 1-hour trend, hold to 16:00** | Also the 15-minute variant (2.20) decisive |
| K2 · Period | **P1 = 2 January 2020 to 5 November 2026 (end of our data); P0 = 2013 to 2019, supplementary** | P1 = 2021 to 2026, exactly the claim's window |
| K3 · Costs | **Our fixed method: spread from the data at the entry minute plus 1 point slippage per side** | The video's cost level: 0.01% of price per side, no spread |
| K4 · Control group | **Null B decisive (random entry moment in the same kill zone of the same day, coin flip on direction, same stop distance); Null A and Null T supplementary** | Null A decisive |
| K5 · Session times | **Fixed clock times (server = New York + 7), no detection from tick volume (audit 21 Nov)** | |

The variants not chosen for K1, K2 and K3 are reported as supplementary, not decisive. The 2021-2026 window (K2 B) is always reported separately, because the claim's 290 trades refer to it.

## 4. Mechanical translation (fixed)

All points below are **[assumption]**: choices to turn the text into rules.

**4.1 Time.** Server time = New York time + 7 hours, all year (see 2.6). A bar is named after its start time. New York 20:00 = server 03:00; 02:00 = 09:00; 07:00 = 14:00; 11:00 = 18:00; 16:00 = 23:00.

**4.2 Bars.** Five-minute bars from the data's minute bars, aligned to the clock (:00, :05, ...). Hour bars the same way, aligned to the full hour. A bar exists if at least one minute bar falls in it.

**4.3 Trading day.** Trading day D runs from 20:00 New York time on the calendar day before D to 20:00 on day D (server 03:00 to 03:00). Only trading days D from Monday to Friday can give a trade (Monday's day starts Sunday 20:00). A trading day is valid if at least 90% of the minutes from 02:00 to 16:00 New York time (840 minutes) have a minute bar. Invalid days (holidays, half days) give no trade.

**4.4 Yesterday.** Yesterday's high and low (PDH, PDL) = highest high and lowest low of all minute bars of the last earlier trading day with at least 600 minute bars in its 20:00 to 20:00 window. For Monday that is usually Friday.

**4.5 Taken.** A level is taken at the first five-minute bar of day D (from 20:00) with high > PDH (for the high) or low < PDL (for the low). After that the level no longer exists that day. A sweep only counts if that first time falls inside a kill zone: a bar starting 02:00 to 04:55 (London) or 07:00 to 10:55 (New York). If the level was taken earlier (in Asia, between the zones), that side gives no sweep that day.

**4.6 Back inside.** After the take (the take bar itself counts), the trigger bar is the first five-minute bar in the same kill zone with close < PDH (after a sweep of the high) or close > PDL (after a sweep of the low). If there is no close back inside within that kill zone, this sweep gives no trade. Only this first return counts: if the trend does not agree there, this sweep gives no trade.

**4.7 Both sides.** If at the trigger bar (at its close) PDH and PDL have both been taken on day D, wherever and whenever, the day is skipped for this setup: no trade and no later trade.

**4.8 Trend.** EMA 200 on the closes of the hour bars (all hours, including the night), alpha 2/201, started with the average of the first 200 closes. At the trigger bar the EMA of the last hour that is fully closed at the close of the trigger bar applies. Long only if the trigger bar's close is above that EMA, short only if below.

**4.9 One per day.** At most one trade per trading day for this setup: the first trigger bar that meets 4.6 to 4.8.

**4.10 Entry.** At the open of the five-minute bar directly after the trigger bar (the open of its first minute bar).

**4.11 Stop.** ATR 14 = Wilder average of the true range of the five-minute bars (continuous across days), value at the trigger bar. Sweep extreme = lowest low (long) or highest high (short) of the bars from the take bar to the trigger bar. Stop distance d = max(|entry − sweep extreme|, 0.5 × ATR) with the stop on the losing side: long stop = entry − d, short stop = entry + d. No extra tick.

**4.12 Path and exit.** The path is followed minute by minute from the entry minute. If a minute bar touches the stop (low ≤ stop for long, high ≥ stop for short), exit at the stop, or at that minute's open if it is already beyond the stop. Otherwise exit at the close of the last minute bar before 16:00 New York time. No target, so "stop and target in one bar" does not occur.

**4.13 Result.** R per trade = (exit − entry) × direction − costs, divided by d. Profit factor = sum of positive net R divided by the absolute sum of negative net R (one R risk per trade). Also in points.

## 5. The three fixed rules

**Costs.** K3 A: the spread from the SPREAD column at the entry minute (unit 0.01, in points, as in test R), plus 1 point slippage per side. Sensitivity: slippage 0, 1 and 2 times, and without costs. Supplementary K3 B: 0.01% of the entry price per side, no spread. If the spread at the entry minute is 0 or empty (mostly before 2019), the median spread of that calendar year applies; P1 almost never has this [assumption, checked in the data check].

**Order.** Path minute by minute (4.12). Signals only on closed five-minute bars.

**Control group.** 10,000 runs, seed 43. Percentile of the real mean net R per trade against the distribution of the runs; confidence intervals with a bootstrap by trading day, also 10,000 times.
- **Null B, decisive for C2:** for each real trade in P1 one random trade on the same day and in the same kill zone: entry at the open of a random five-minute bar from 02:05 to 05:00 (London, 36 options) or from 07:05 to 11:00 (New York, 48 options), direction by a fair coin, the same stop distance d in points, the same exit at 16:00, the same costs. Tests whether the sweep with trend filter picks better moments and directions than chance with the same exposure.
- **Null A, supplementary:** each real trade with the same entry, stop and exit, the direction by a fair coin.
- **Null T, supplementary (v1.1):** for each real trade one random trade on a random valid trading day from the same period (not necessarily the same day), in the same kill zone, entry at the open of a random five-minute bar as in Null B, direction by the trend (close of the previous five-minute bar against the EMA 200 of the last completed hour; no option on a tie), stop distance = the real trade's stop distance in ATR units (d / ATR of the trigger bar) times the ATR of the previous five-minute bar, exit at 16:00, the same costs. Tests whether the sweep adds anything to just following the trend in the same kill zone.

## 6. Noise check before the real data (fixed)

24 fake markets of 1,500 trading days (weekdays only, 24 hours a day, no break), minute bars built from 60 steps per minute, no trend, no session effect, a fixed spread of 1 point. Start price 15,000, volatility similar to the Nasdaq 100 (about 1.2% per day) [assumption]. Seed 7. 2,000 runs per set.

Threshold, as in earlier tests: percentile against Null B on average between 35 and 65, at most 2 of 24 above 95 (instruction v2). Null A and Null T are also measured on noise and must meet the same threshold. If the script fails, first find the cause and write a new version of this document (at most two repair rounds), before the real data.

Before the noise check, a self-test: handmade days (sweep of the low with trend up, same with trend down, level taken earlier, both sides taken, no return inside the zone, stop hit, minimum stop 0.5 ATR, exit at 16:00) and a second, simple implementation that must give exactly the same trades on fake days.

## 7. Data

[verified, `data/README.md` and earlier tests] USTEC M1, IC Markets, `USTEC_M1_201208060000_202611052200.csv` (SHA-256 starts with 714b4cc0), server time, runs to 5 November 2026. Nothing has been opened for this test yet.

Periods:
- **P1, decisive for C1, C2 and C3:** trading days from 2 January 2020 to 5 November 2026.
- C3 uses the claim's sub-periods: 2021 to 2024, and 1 January 2025 to 5 November 2026.
- Supplementary: the window 2021 to 5 November 2026 (number of trades against 290), P0 2013 to 2019, the 15-minute variant (same rules on fifteen-minute bars) in P1.

Data check before the run, metadata only: number of valid trading days per year, minute bars per day, missing night hours, share of minutes with spread 0, median spread per year, and whether the quiet period around the daily break falls at server 00:00 to 01:00 (New York 17:00 to 18:00).

## 8. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval (day bootstrap) of the net profit factor in P1 lies below 1.95 |
| C2 | The real mean net R per trade in P1 is not above percentile 95 of Null B |
| C3 | The net profit factor in 2021-2024 or in 2025-2026 is 1.0 or lower |

If C2 falls, the idea is dead: no repair, no optimisation, no other confirmation, kill zone, exit or timeframe. Below 100 trades in a period, sub-period or group the report says "insufficient trades".

## 9. What I report, whatever the outcome

Number of trades (P1, 2021-2026 against 290, per year, London and New York separately, long and short separately), share of losers (against about 70%), mean net R with 95% interval, profit factor with 95% interval, percentile against Null B, Null A and Null T, without costs, slippage 0, 1 and 2 times, K3 B, profit factor without the 5 best days, longest losing streak, largest drawdown in R, mean stop distance in points, January to September 2026, the 15-minute variant, P0.

Title by the fixed rule: "profit factor 1.95 claimed" with our measurement next to it. No names of the channel, the video or the indicator in publications.

## 10. Next step

1. Save, SHA-256 in `meetlog-prev-day-sweep.md`, commit before the data. English version alongside.
2. Script `sweep_test.py`: self-test, noise check.
3. Data check from section 7, then run 01, control group first.
