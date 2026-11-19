# Hypothesis: 9 EMA + VWAP on 3 minutes (test N)

English translation. The Dutch original `hypothese-vwap-9ema.md` is binding; its file name, SHA-256 and date are in the measurement log.

Date: 18 November 2026 · Source: an Instagram reel of 30 October 2026, rules taken from the spoken text · Status: **version 1.0, fixed in advance and approved on 18 November 2026 (K1 A, K2 A, K3 A), no real price data opened for this test**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule: everything below is fixed before the first run. Nothing is changed after the run. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, transcript and caption] The rules as the source gives them:
- Timeframe 3 minutes.
- EMA 9 on the close.
- VWAP with anchor period "session" on OHLC4 ((open + high + low + close) / 4).
- Long ("calls"): the EMA 9 crosses above the VWAP. Short ("puts"): the EMA 9 crosses below the VWAP.
- Exit: "If candle breaches the EMA 9 on the 3-minute time frame, exit your position."
- Emergency exit: "If it's a fake out, exit at -25% to -30%" (of the option premium [assumption]).
- Result: "I made over $255,000 in ONE MONTH" (October 2026), with options.

[verified] Not mentioned: the underlying, session times, number of trades, win rate, position size.

[verified] Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | The rule makes money ("insane trading strategy", "$255,000 in one month") | Mean net result per trade on the underlying above zero, over all data |
| C2 | The cross of EMA 9 and VWAP picks better moments than chance | Real result against the control group with the same exit rule |
| C3 | October 2026, the month of the claim, was profitable with this rule | Mean net result per trade in October 2026 above zero |

[verified] Not testable: the amount of $255,000. That is the personal result of one account with options, with unknown position size and unknown choices per trade. We measure the rule, not the account. Every publication says so.

## 2. Weak spots visible before the test

1. [verified] One month is one sample. A strong month says little about the rule itself; that holds for any month picked afterwards.
2. [assumption] A cross of two lines on 3 minutes probably gives several signals a day, with short trades. With short trades, spread and slippage weigh heavily.
3. [verified, transcript] The exit rule can be read in two ways: a candle that closes through the EMA 9, or a candle that only touches it. See choice K1.
4. [verified] The emergency exit is in percent of an option premium. On the underlying that limit does not exist without assumptions about expiry, strike and volatility. See choice K2.
5. [verified, earlier tests] Our data is a CFD on the S&P 500 with tick volume, not real traded volume. The VWAP is therefore weighted with tick volume [assumption that this approximates the real VWAP]. Sensitivity: VWAP without volume (all minutes equal weight).

## 3. Choices (made on 18 November 2026: K1 A, K2 A, K3 A, the options in bold)

| Choice | A | B |
|---|---|---|
| K1 · Exit "candle breaches the EMA 9" | **Close of the 3-minute candle on the other side of the EMA 9, exit at the open of the next candle.** The only other test I found (another testing channel) read it this way too [verified, transcript] | Candle touches the EMA 9 (long: low below the EMA 9), exit at the EMA 9 itself. Gives earlier exits and more small losses |
| K2 · Emergency exit of -25 to -30% | **No extra stop. Only the EMA exit and closing at the end of the session.** The limit only exists for options; any translation into points is our own number. The largest loss per trade is reported | Fixed stop of 0.3% of the price [assumption: rough translation of -25% premium at a delta around 0.5 and a premium of about 0.6% of the price] |
| K3 · Deciding instrument | **US500 (S&P 500).** The other testing channel tested on the ES future; the source names no instrument | USTEC (Nasdaq 100). "75 point uptrend" fits the Nasdaq just as well [assumption] |

The instrument not chosen in K3 is reported as supplementary, not deciding. So is the K1 variant not chosen.

## 4. Mechanical translation (fixed)

All points below are **[assumption]**: choices to turn the text into rules.

**4.1 Session.** Regular trading hours only, 9:30 to 16:00 New York time, as the other testing channel read it ("RTH"). The opening per day as in tests G and H: the jump in tick volume around 16:30 server time. A day only counts with at least 90% of the 390 minute bars.

**4.2 Bars.** 3-minute candles from the M1 data, starting at 9:30: 9:30, 9:33, ... 15:57. 130 candles a day.

**4.3 Indicators.**
- EMA 9 on the close of the 3-minute candles, regular session only, continuing across days (as a chart with trading hours only does).
- VWAP: starts again every day at the 9:30 candle. Price per minute is the OHLC4 of that minute, weight is the tick volume of that minute. Value at the close of the 3-minute candle = sum(price × volume) / sum(volume) from 9:30 up to and including the last minute of that candle.
- Everything calculated up to and including the signal candle.

**4.4 Signal (at the close of 3-minute candle t).**
- Long: EMA9(t-1) ≤ VWAP(t-1) and EMA9(t) > VWAP(t).
- Short: EMA9(t-1) ≥ VWAP(t-1) and EMA9(t) < VWAP(t).
- Only from the second candle of the day (the VWAP restarts at 9:30; a comparison with the previous day means nothing). No signals on the last candle of the day.

**4.5 Entry.** Open of candle t+1 (the open of its first minute). Never at the close of the signal candle.

**4.6 Exit.** According to K1. With A: long out when close(k) < EMA9(k), short out when close(k) > EMA9(k), checked from the close of the entry candle on, out at the open of candle k+1. Further: everything closed at the close of the last candle (16:00). No target in points, no trailing stop. Emergency exit according to K2.

**4.7 One position at a time.** A new cross in the same direction while the position is open is ignored. A cross in the other direction while the position is open: the position closes and the new one opens, both at the open of the next candle.

**4.8 Result.** Per trade in points and in basis points of the entry price, net of costs. There is no fixed stop, so no R.

## 5. The three fixed rules

**Costs.** The spread from the SPREAD column at the entry minute, plus 0.25 point slippage per side (entry and exit), as in test H [verified, hypothesis test H]. Sensitivity: slippage 0, 1 and 2 times. For USTEC the same set-up with 1 point slippage per side [assumption].

**Order.** The path is run minute by minute. With K1-A and K2-A all exits fall on a candle open, so the order within a minute plays no role. With K1-B or K2-B: if one minute hits both the exit and the emergency stop, the worst outcome counts.

**Control group.** 10,000 runs, seed 43, bootstrap per trading day.
- **Null A, deciding for C2:** the same days, the same session, the same exit rule and the same costs. A sequential process: on every 3-minute candle with no open position (except the first and last of the day), chance opens a position with probability p. The direction is the side where the close lies relative to the EMA 9 (above: long, below: short), so the exit rule works exactly as with the real trades. p is chosen so that the mean number of trades equals that of the rule. Tests whether the cross with the VWAP adds anything on top of random entries with the same EMA exit. Set up after the lessons of tests J and K: same structure as the rule from the start [verified, handover 25].
- Percentile of the real mean net result per trade.

## 6. Noise check before the real data (fixed)

24 fake markets of 1,500 trading days with minute bars, built from 60 sub-steps per minute (as tests G and H), without trend and without opening effect, with a fixed spread of 0.5 point and random tick volume. Seed 7.

Bounds, equal to the audit of 10 November: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95. If the script fails, the cause is found first and a new version of this document follows, before the real data.

## 7. Data

[verified, hypothesis and data check test H] US500 M1 from one broker, real minute data from 21 March 2017, spread column filled from 2019. Runs to 2 November 2026, so October 2026 is included. USTEC M1 from test G. Nothing opened yet for this test.

Periods:
- **P1, deciding for C1 and C2:** all valid sessions from 2019 (spread column filled) up to and including 30 October 2026.
- **P0, deciding for C3:** October 2026.
- Supplementary: 2017 and 2018 with the median spread of 2019 [assumption].

Data check before the run, metadata only: number of valid sessions per year, distribution of the opening minute found, share of days with an empty spread, minutes with zero tick volume.

## 8. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval (day bootstrap) of the mean net result per trade in P1 is below 0 |
| C2 | The real mean net result in P1 is not above percentile 95 of Null A |
| C3 | The upper bound of the 95% interval of the mean net result per trade in October 2026 is below 0 |

If C2 falls, the idea is dead: no repair, no optimisation, no filters, other lengths or timeframes. Below 100 trades in a period, the report says "insufficient trades".

## 9. What I report, whatever the outcome

Number of trades and trades per day, win rate (descriptive, the source names none), mean net result in points and basis points with 95% interval, profit factor, percentile against Null A, the result without costs, the three cost levels, median duration of a trade, largest loss per trade (because of K2), long and short apart, per year, October 2026 apart, the K1 variant not chosen, the VWAP without volume, and the instrument not chosen in K3.

Title by the fixed rule: no percentage in the claim, so the main number: "$255,000 claimed", with our measurement next to it.

## 10. Next step

1. Approved on 18 November 2026 (K1 A, K2 A, K3 A). SHA-256 in the measurement log. English version alongside.
2. Script `vwap_control.py`: first check EMA and VWAP against a hand calculation, then the noise check from 6.
3. Data check from 7, then run 01.
