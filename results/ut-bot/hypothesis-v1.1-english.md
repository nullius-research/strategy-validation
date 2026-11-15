# Hypothesis: UT Bot Alerts on Nasdaq 5 minutes (test K)

Date: 15 November 2026 · Source: video by a trading channel about one of the most popular indicators on TradingView (source file kept private) · Status: **version 1.1, approved on 15 November 2026, after a failed noise check of version 1.0. Only the control group changes (section 5, see 11). Version 1.0 (SHA-256 of the Dutch original 3ec64d8c...) is kept. The rule has not been run on price data yet. The Nasdaq data is the same export as in test G; there it was used for a different rule.**

This is the English version, made at the same time as the Dutch original. The Dutch original is binding.

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule of play: everything below is fixed before the first run. After the first real run nothing changes; a new version gets a new date.

## 1. The claim

[verified, transcript read 15 Nov 2026] Nasdaq on 5 minutes, one month (October 2023), tested by hand. UT Bot Alerts (key value 2, ATR period 1) gives the signal. Only in the New York session, the first three signals per day. A buy only on a green candle that closes above the signal line of the Linear Regression Candles (length 11, signal 7); a sell mirrored. Entry at the close. Stop behind the latest swing. Exit at the first close on the other side of the signal line, but only if the trade is in profit then; otherwise the trade runs until the stop.

| Number | In the video |
|---|---|
| Trades | 66 (44 wins, 22 losses) |
| Win rate | "just over a 66%" (44 of 66 is 66.7%) |
| Account | +123% in one month (sizing not stated) |
| Best trade | 10.59R |

## 2. Testable claims

| # | Claim | Testable as |
|---|---|---|
| C1 | Win rate 66.7% | Win rate with 95% interval (Wilson) |
| C2 | Profitable ("123% profit", "will make you rich") | Mean net result per trade in R, with 95% interval (bootstrap per trading day) |
| C3 | The rule picks better moments than chance | Mean net R against Null A |

Not tested, but reported: the return on the account (sizing unknown) and the best trade.

## 3. Weak points, named in advance

1. [verified] The claim rests on one month and 66 trades, done by hand. At 66 trades the 95% interval around 66.7% runs from about 54.7% to 76.8%. The video may therefore have been lucky without the maker doing anything wrong.
2. [assumption] "Recent swing high" and "swing low" are not defined. Our choice is in 4.6; another choice gives another stop and so other R values.
3. [assumption] "Candle is red ... green": in the video UT Bot colours the candles itself (green above the trailing stop). On a buy signal that colour is always green, so the rule would filter nothing. We use the ordinary candle (close above or below the open). The colour of the Linear Regression Candles is measured as a sensitivity.
4. [verified] The source trades "the NASDAQ" without brand or broker. We use the Nasdaq 100 CFD from test G (USTEC). Price movement almost the same, costs and times not.
5. [assumption, reasoned] With a fixed stop and an exit only in profit, many small wins and fewer, larger losses are to be expected. A high win rate therefore says little; the mean net R decides.

## 4. Mechanical translation (fixed)

All points below are **[assumption]**: choices to turn the video into rules.

**4.1 Market and data.** USTEC M1 from MT5 (server time), combined into 5-minute bars on server time. From 1 January 2018 (first full year with a filled SPREAD column). For each day the opening of the regular session (9:30 New York) is found from the jump in tick volume, as in test G.

**4.2 Session.** New York 08:00 to 17:00 America/New_York, the default of the session indicator with exactly the four sessions from the video. A signal counts if the signal bar closes inside that window.

**4.3 UT Bot.** Exactly the public code, key value 2, ATR period 1, no Heikin Ashi. ATR(1) is the true range of that bar. Buy and sell signals as in the code (close crosses the trailing stop).

**4.4 Linear Regression Candles.** Exactly the public code: linear regression (length 11, offset 0) of open, high, low and close; signal line = SMA with length 7 of the regression close.

**4.5 Filter and count.** Per day the first three UT Bot signals inside the session, in order of time. A signal becomes a trade if:
- buy: close above the open of the signal bar and close above the signal line; sell: close below the open and close below the signal line;
- no trade is open.
A signal that fails the filter or falls during an open trade still counts as one of the three.

**4.6 Entry and stop.** Entry at the close of the signal bar. Buy stop: the lowest low of the last 10 bars of 5 minutes, signal bar included. Sell stop: the highest high of those 10 bars. R = distance from entry to stop. If R is smaller than 1 point, no trade (costs would decide everything).

**4.7 Exit.** For each 5-minute bar after the entry:
- if the bar touches the stop, exit at the stop (if the bar already opens beyond the stop, at the open);
- otherwise: if the bar closes on the other side of the signal line (buy: close below the line) and the trade is in profit at that close, exit at that close;
- no time limit and no forced exit at the end of the session; open at the end of the data: exit at the last close, reported separately.

**4.8 One position at a time.**

## 5. The three fixed rules

**Costs.** Spread from the SPREAD column on the entry bar plus 1 point slippage per side, charged in R, as in test G. Sensitivity: slippage 0, 1 and 2 points per side.

**Order.** Bar by bar on 5 minutes. A stop inside the bar comes before an exit at the close. Entry at the close of the signal bar, so the first bar that counts is the next one.

**Control group.** 10,000 runs, seed 37. Sequential process through time, as in test J v1.1.
- **Null A, decisive:** after each exit (and from the start) a random wait in bars inside the session (geometric, on average such that the number of trades is around that of the rule), then entry at the close of the first bar from there that passes the same filter as the rule: buy on a green candle closing above the signal line, sell on a red candle closing below it. The filter therefore fixes the direction. Same stop, same exit, same costs, at most three entries per day, only inside the session. Tests what the UT Bot signal adds on top of the filter.
- **Null B, supplementary:** like Null A, but without the filter and with a coin flip for the direction (the control group of version 1.0). Note: the rule also beats Null B on markets without a pattern (see 11); Null B is therefore for comparison only.

## 6. Noise check before the real data (fixed)

24 fake markets of 5 years of M1 with session structure, the generator from test G v1.1 (random walk without drift, 20% per year, 60 sub-steps per minute, 70% of the daily movement in the session), seed 7, 2,000 runs per set.

Threshold: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95.

## 7. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | 1 Jan 2018 up to and including the last full day (5 Nov 2026) | **Decisive** for C1 to C3 |
| P0 | October 2023 | Reproduction of the month in the video: do we get about 66 trades and 66.7%? Not decisive |
| P2 | 6 Nov 2023 up to and including the last full day | After the video. Supplementary |
| P3 | Per year within P1, and long and short separately | Distribution. Under 100 trades: insufficient |

## 8. When is the idea dead (in advance)

| Claim | Falsified in P1 if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate is below 66.7% |
| C2 | The upper bound of the 95% interval of the mean net R is below 0 |
| C3 | The mean net R is not above percentile 95 of Null A |

After the run: no other settings, swings, sessions or exits. If a claim stands, then "not falsified in this measurement", not "works".

Sensitivity, fixed in advance and not decisive: candle colour of the Linear Regression Candles instead of the ordinary candle; forced exit at 17:00 New York; slippage 0 and 2 points.

## 9. What I report, whatever the outcome

The funnel: trading days, UT Bot signals in the session, within the first three, through the colour filter, through the signal line, dropped during an open trade, dropped for R under 1 point, trades. Per period: trades, win rate (95%), mean net R (95%), profit factor, median stop in points against the costs, best and worst trade in R, longest losing streak, mean holding time, share of trades held overnight. Percentiles against Null A and Null B. The sensitivities. The noise check.

## 10. Next step

1. Approval (or adjustment). SHA-256 in the measurement log.
2. Script `utbot_control.py`: first check UT Bot and the signal line against a hand calculation, then the noise check from 6.
3. Run in the cloud on the USTEC export from test G (only metadata checked for this test).
4. Code and data on GitHub before publication.

## 11. Change to version 1.1 (before the real data)

[verified] The noise check of version 1.0 failed: mean percentile 99.1, 23 of 24 above 95 (`noise_24sets_v1.0.txt`). Cause measured (`diag_k.py`, two fake markets): random entries on the wrong side of the signal line exit at once or lose more (on average -0.49 R for long), and have a smaller stop (median 18.3 against 25.7 points for the rule), so costs weigh more. Random entries that pass the same colour and line filter do about as well as the rule (-0.13 and -0.11 R against -0.12 R). The filter therefore changes the shape of the trade, apart from any prediction. The control group gets the same filter; C3 now tests what the UT Bot signal adds.

Noise check with version 1.1: mean percentile 44.9, 1 of 24 above 95 (`noise_24sets.txt`). Passed. Rule, data, periods, criteria and costs stay the same as in version 1.0.
