# Hypothesis: Triple RSI on SPY (test I)

Date: 14 November 2026 · Source: article, Substack post, video and Instagram post by a strategy research website · Status: **draft 1.0, 14 November 2026, not yet approved. No price data opened for this test.**

This is the English version. The Dutch original (`hypothese-triple-rsi.md`, same date) is binding; its SHA-256 is in the measurement log.

Legend: **[verified]** = checked or calculated ourselves · **[assumption]** = not checked ourselves, or a choice in the measurement

Rule: everything below is fixed before the first run. After the first real run nothing changes; a new version gets a new date.

## 1. The claim

[verified, sources read 14 Nov 2026] Rules: 5-day RSI below 30; 5-day RSI down for the third day in a row; 5-day RSI below 60 three trading days ago; close above the 200-day moving average; buy at the close. Sell at the close when the 5-day RSI crosses above 50. Long only, SPY. No stop, no target, no costs mentioned.

There are two versions of the result:

| Version | Source | Period | Trades | Win rate | Average per trade | Profit factor |
|---|---|---|---|---|---|---|
| A | article and Substack post, Feb 2026 | "since 1993" | 103 | 90% | 1.2% | 4 |
| B | video, Sep 2026 | "from 1993 until today" | 83 | "approximately 90%" | "almost 1.4%" | not given |

## 2. Testable claims

| # | Claim | Testable as |
|---|---|---|
| C1 | 90% of trades win | Win rate with 95% interval (Wilson) |
| C2 | Average gain of 1.2% per trade (version A); almost 1.4% (version B) | Mean net return per trade in percent, with 95% interval (bootstrap by trade) |
| C3 | Profit factor 4 (version A) | Net profit factor, with 95% interval (bootstrap by trade) |
| C4 | The three RSI conditions pick better entry days than chance within the trend filter (implied: "high-probability entry points") | Mean net return per trade against Null A |

## 3. Weak points, named in advance

1. [verified] The source shows the full SPY history since 1993. So there is no SPY period the source could not see, except the days after its latest publication. Reproducing the numbers therefore proves little; C4 (against the control group) decides.
2. [verified, arithmetic] At about 100 trades, the 95% interval around 90% runs from about 83% to 95%. C1 only fails if the measured win rate is below about 83%.
3. [assumption, reasoned] An exit without a stop on an index with upward drift often gives a high win rate even with random entries. A high win rate alone says little.
4. [verified] The two versions contradict each other (103 against 83 trades, a longer period with fewer trades). We test both sets of numbers; the rules are the same for both.
5. [verified, log] Closely related to test E (RSI(2) pullback, not falsified). The results are not independent.
6. [assumption] About 100 trades sits exactly at our threshold. Every subgroup (per decade, after publication) has fewer: those are reported as insufficient.

## 4. Mechanical translation (fixed)

All points below are **[assumption]**: choices to translate the text into rules.

**4.1 Market and data.** SPY daily prices from Yahoo Finance via the browser pane, from the first trading day (29 January 1993) to the last closed day before the run. Signals and returns on the close without dividend adjustment ("close"). The dividend-adjusted close ("adjclose") only as a sensitivity check.

**4.2 RSI(5).** Wilder RSI with period 5 on the close (smoothing with alpha 1/5), the default in Amibroker. Warm-up: the first 250 trading days do not count.

**4.3 SMA 200.** Simple average of the last 200 closes, up to and including the signal day.

**4.4 Signal on day t.** All four at once:
- RSI(t) < 30
- RSI(t) < RSI(t-1) < RSI(t-2) < RSI(t-3) (three declines in a row)
- RSI(t-3) < 60
- close(t) > SMA200(t)

**4.5 Entry.** At the close of day t.

**4.6 Exit.** At the close of the first day after entry on which the 5-day RSI crosses above 50: RSI of the previous day at most 50, RSI of that day above 50. No stop, no target, no time limit. Still open at the end of the data: closed at the last close and reported separately.

**4.7 One position at a time.** A new signal during an open trade is ignored.

## 5. The three fixed rules

**Costs.** 2 basis points round trip per trade, the same as Buy the Dip and test E. Sensitivity: 0, 2 and 4 bp.

**Order.** Entry and exit on closes. The rule has no stop or target within the day, so the path within the day plays no part [verified, rules]. Measured per trade: the deepest interim decline on closes, because without a stop that is where the risk sits.

**Control group.** 10,000 runs, seed 37.
- **Null A, decisive:** random entry days from the days with the close above the SMA200, as many trades as the rule, one position at a time. Each fake trade gets the duration of a real trade (the real durations, shuffled). Tests whether the three RSI conditions pick better days than a random day in the same trend, with the same time in the market.
- **Null B, supplementary:** as Null A, but with the rule's own exit (5-day RSI crosses above 50), like Null A of test E. With an entry where the RSI is already above 50, that fake trade waits for a dip and a recovery; its duration can then differ a lot.

## 6. Noise check before the real data (fixed)

24 fake markets of 8,400 trading days (about 33 years, so each set can give around 100 trades), a random walk with memoryless daily returns, drift 0.03% and volatility 1.2% per day [assumption: roughly SPY]. Seed 7.

Threshold, the same as the audit of 10 Nov: percentile against Null A on average between 35 and 65, at most 3 of 24 above 95.

## 7. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | 29 Jan 1993 up to and including the last day | **Decisive** for C1 to C4 |
| P0a | 29 Jan 1993 up to and including 20 Feb 2026 (date of the Substack post) | Reproduction of version A: do we get near 103 trades, 90%, 1.2%, PF 4? Not decisive |
| P0b | 29 Jan 1993 up to and including 18 Sep 2026 (date of the video) | Reproduction of version B: 83 trades, about 90%, almost 1.4%. Not decisive |
| P2 | per decade within P1 | Distribution. Below 100 trades: insufficient |
| P3 | S&P 500 index (^GSPC), 3 Jan 1950 to 28 Jan 1993 | Outside the source: the same rules before SPY existed. Supplementary, not decisive |

## 8. When is the idea dead (in advance)

| Claim | Falsified in P1 if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate is below 90% |
| C2 | The upper bound of the 95% interval of the mean net return is below 1.2% (version A); reported separately against 1.4% (version B) |
| C3 | The upper bound of the 95% interval of the profit factor is below 4 |
| C4 | The mean net return per trade is not above percentile 95 of Null A |

After the run: no other RSI periods, thresholds, filters or exits. If a claim stands, it is "not falsified in this measurement", not "works".

## 9. What I report, whatever the outcome

The funnel: days above the SMA200, days with RSI below 30, with three declines, with RSI(t-3) below 60, signals, ignored during an open trade, trades. Per period: trades, win rate (95%), mean net return (95%), profit factor (95%), worst trade, deepest interim decline, average duration, time in the market, and buy and hold over the same period. Percentiles against Null A and Null B. Cost sensitivity and the dividend-adjusted version. The noise check.

## 10. Next step

1. Erwin approves (or adjusts). SHA-256 in the measurement log.
2. Script `triple_rsi_control.py` based on test E (`rsi2_control.py`), noise check from 6 first.
3. Fetch data via the browser pane, data check (metadata only), then the run.
4. Code and data on GitHub before publication.
