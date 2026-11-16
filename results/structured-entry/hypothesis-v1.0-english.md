# Hypothesis: structured entry with MACD and 200 EMA on Bitcoin 30 minutes (test L)

Translation of the Dutch original `hypothese-structured-entry.md`. The Dutch original, with its own date and SHA-256, is binding.

Date: 15 November 2026 · Source: a trading channel video about an "87% win rate" strategy (source file kept private) · Status: **version 1.0, approved on 15 November 2026 without changes (the default choices). The rule has not been run on price data. The Bitcoin data is the same export as in test J, where it was used for a different rule. For this test only the row count and the first and last time were inspected.**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule of the game: everything below is fixed before the first run. After the first real run nothing changes; a new version gets a new date.

## 1. The claim

[verified, transcript read 15 Nov 2026] Bitcoin on 30 minutes, "the last four years" before the video of 28 September 2024, tested by hand. Trend filter: the 4-hour 200 EMA, in the maker's version that "disappears" in a sideways market. Long: price above that EMA, the MACD line crosses above the signal line and the cross is below the zero line. Short mirrored. Stop beyond the 200 EMA. Two variants, 100 trades each:

| Variant | Rule | Numbers in the video |
|---|---|---|
| Single entry | One position, target 0.5R, 3% risk | Win rate "approximately 73%", "around 28% profit", breakeven "around 67%" |
| Structured | Up to three entries of 1% risk in the same setup, each lower (long), stop in the same place; target 0.25R after the first and second entry, 0.5R after the third, measured from the average entry price | Win rate 87%, breakeven "between 67% and 80%", edge "around 10%", total profit slightly lower than the single entry |

## 2. Testable claims

| # | Claim | Testable as |
|---|---|---|
| C1 | Structured: win rate 87% | Win rate per setup with 95% interval (Wilson) |
| C2 | Single entry: win rate 73% | Win rate per trade with 95% interval (Wilson) |
| C3 | Single entry is profitable | Mean net R per trade, 95% interval (bootstrap by week) |
| C4 | Structured is profitable | Mean net result per setup in percent of the account (1% per entry), 95% interval (bootstrap by week) |
| C5 | The rule picks better moments than chance | Mean net result against Null A, separately for structured (C5a) and single entry (C5b) |

Not tested, but reported: the account return of 28% (the order of his 100 trades is unknown) and the statement that structuring raises the win rate "not just because of the lower reward-risk ratio". The latter is measured (section 9: the same entries with one position and a 0.25R target).

## 3. Weak points, named in advance

1. [assumption, reasoned] With a 0.25R target and a 1R stop, random entries without costs already give a win rate around 80%; at 0.5R around 67%. A high win rate here mainly follows from the small target. The control group shows what chance gives with exactly the same targets.
2. [verified] Two times 100 trades in four years. At 100 trades the 95% interval around 87% runs from about 79% to 92%, around 73% from about 64% to 81%.
3. [assumption] Four years on 30 minutes probably gives far more than 100 signals with this rule. The maker may not have taken every signal; which ones he took is not in the source. We take every signal.
4. [assumption] "Too close to the previous entry" is not defined. Our choice is in 4.6, with alternatives as sensitivity.
5. [assumption] "Below the 200 EMA" gives no distance. We put the stop exactly at the EMA value at the first entry and keep it there.
6. [assumption] The 4-hour EMA on a 30-minute chart: TradingView can show the value of a 4-hour bar that has not closed yet on historical bars. We only use the last closed 4-hour bar. That is stricter than what the maker may have seen.
7. [verified] The source says "Bitcoin USD" without an exchange. We use BTCUSDT from Binance (test J). Price path nearly identical, costs and small price differences not.

## 4. Mechanical translation (fixed)

All points below are **[assumption]**: choices to translate the video into rules.

**4.1 Market and data.** BTCUSDT spot 30 minutes from Binance, `BTCUSDT_30m_binance.csv` from test J (137,887 bars, first bar 1 January 2019 00:00 UTC, last 15 November 2026 08:30 UTC, SHA-256 8ed44f29...). 4-hour bars are built from eight 30-minute bars, starting at 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 UTC, the Binance and TradingView layout.

**4.2 Trend filter (colour EMA on 4 hours).** EMA(200) on the close of the 4-hour bars. Exactly the maker's public code, on the 4-hour bars: green if the close now and 5, 10, 15, 20, 30, 40 and 50 bars back each was above the EMA of that bar; red if each was below; otherwise no colour. A 30-minute bar uses the colour and EMA value of the last closed 4-hour bar.

**4.3 MACD.** MACD(12, 26, 9) on the 30-minute close, the default, as in test A.

**4.4 Signal on bar t (30 minutes).**
- Long: MACD(t-1) ≤ signal(t-1) and MACD(t) > signal(t), MACD(t) < 0 and signal(t) < 0, colour EMA green, close(t) above the 4-hour EMA.
- Short: MACD(t-1) ≥ signal(t-1) and MACD(t) < signal(t), MACD(t) > 0 and signal(t) > 0, colour EMA red, close(t) below the 4-hour EMA.

**4.5 Variant Z, single entry.** Entry at the close of the signal bar. Stop: the 4-hour EMA at that moment (4.2), fixed until exit. R = distance from entry to stop. Target: entry plus 0.5R. One position at a time; signals during an open position lapse.

**4.6 Variant G, structured.** A setup starts at a signal when no position is open. Entry 1 at the close, stop S = the 4-hour EMA at that moment, fixed for the whole setup. While the position is open, a new signal in the same direction becomes entry 2, and then entry 3, if:
- the entry price is at least 10% of the distance (entry 1 to S) lower than the previous entry (short: higher);
- the entry price is still above S (short: below).
Each entry risks 1% of the account to S, so size_i = 1% / (entry_i - S). Average entry price = size-weighted mean. Target after k entries: average plus m_k times (average - S), with m_1 = m_2 = 0.25 and m_3 = 0.5 (short mirrored). After the third entry no more are added. The setup ends at the target or at S; a new setup may start from the next bar.

**4.7 Minimum stop.** If the distance from entry 1 to S is less than 0.5% of the entry price, no trade or setup (costs would decide everything). Signals with the close on the wrong side of S do not exist because of 4.4.

**4.8 Exit and end of data.** No time limit. Anything still open at the end of the data closes at the last close, reported separately.

## 5. The three fixed rules

**Costs.** 0.06% per side (0.05% taker fee plus 0.01% slippage), per entry and per exit of each part, as in test J. Charged in R (variant Z) and in percent of the account (variant G). Sensitivity: 0, 0.12% and 0.20% per round trip. No leverage, no funding.

**Order.** Bar by bar on 30 minutes. Per bar first the stop, then the target; if one bar hits both, it counts as a stop. If a bar opens beyond the stop or the target, exit at the open. An entry or add happens at the close; the new target applies from the next bar. On the bar where a setup ends, no new one starts.

**Control group.** 10,000 runs, seed 41. Sequential process through time, with the same filter from the start (lesson from tests J and K).
- **Null A, decisive:** the MACD cross is replaced by a random signal. On every 30-minute bar where the filter of 4.4 holds without the MACD conditions (colour EMA green and close above the EMA, or red and below), a signal fires with probability p in the direction of the filter. p is chosen per period so that the number of signals equals that of the rule. Then exactly the same rules: same stop, minimum stop, add rules, targets and costs. Separately for variant Z and variant G. Tests what the MACD cross below or above the zero line adds on top of the trend filter.

## 6. Noise check before the real data (fixed)

24 synthetic markets of 6 years on 30 minutes, random walk without drift at 60% volatility per year, built from 1-minute steps (open, high, low, close per 30 minutes), seed 7, 2,000 runs per set. For both variants.

Limit per variant: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95.

## 7. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | From the first bar with a valid colour EMA (200 plus 50 four-hour bars warm-up, around 11 February 2019) to the last full day in the data (14 November 2026) | **Decisive** for C1 to C5 |
| P0 | 28 September 2020 to 27 September 2024 | Reproduction of "the last four years". Do we get 73% and 87%? Not decisive |
| P2 | 28 September 2024 to 14 November 2026 | After the video. Supplementary |
| P3 | Per year within P1, and long and short separately | Distribution. Below 100 trades or setups: insufficient |

## 8. When is the idea dead (in advance)

| Claim | Falsified in P1 if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate (G) is below 87% |
| C2 | The upper bound of the 95% interval of the win rate (Z) is below 73% |
| C3 | The upper bound of the 95% interval of the mean net R (Z) is below 0 |
| C4 | The upper bound of the 95% interval of the mean net result per setup (G) is below 0 |
| C5a, C5b | The mean net result is not above percentile 95 of Null A |

After the run: no other settings, stops, targets, add rules or filters. If a claim stands, then "not falsified in this measurement", not "works".

Sensitivity, fixed in advance and not decisive:
- add distance: any lower price counts (0%), and 25% of the distance entry 1 to S;
- minimum stop: no minimum, and 1.0%;
- plain 4-hour 200 EMA without the colour condition;
- costs 0, 0.12% and 0.20% per round trip.

## 9. What I report, whatever the outcome

The funnel: bars after warm-up, bars with a green or red colour EMA, MACD crosses in the right direction, on the right side of the zero line, dropped by the minimum stop, dropped during an open position (Z), adds refused by the distance rule (G), trades and setups. Distribution of the number of entries per setup (1, 2 or 3).

Per period and variant: count, win rate (95%), mean net result (95%), profit factor, median stop distance in percent against costs, breakeven win rate after costs, best and worst outcome, longest losing streak, mean duration. Percentiles against Null A.

Extra comparison (not tested): the same first entries as variant G, but with one position and a 0.25R target. This shows how much of the win rate comes from the small target and how much from structuring. The sensitivities. The noise check.

## 10. Next step

1. Approval (or edits). SHA-256 in the measurement log.
2. Script `structured_control.py`: first check the colour EMA, MACD and the add arithmetic against hand calculation, then the noise check from 6.
3. Run in the cloud on the BTCUSDT export from test J.
4. Code and data on GitHub before publication.
