# Hypothesis: RSI(3) + EMA(100) + rolling VWAP on QQQ (test T)

Date: 28 November 2026 · Source: a Substack post, a video and an Instagram post by a strategy research website (name kept private) · Status: **version 1.1, approved by Nullius Research on 28 November 2026. Version 1.0 (approved 28 Nov, choices K1 to K5 all A) failed the noise check on Null B; only Null B changed (see 11). No QQQ price data opened yet.**

Legend: **[verified]** = checked or calculated ourselves · **[assumption]** = not checked ourselves, or a choice in the measurement

Rule of play: everything below is fixed before the first run. After the first real run nothing changes; a new version gets a new date. The Dutch version (`hypothesis-v1.1-dutch.md`) is the original; this is a translation.

## 1. The claim

[verified, sources read 28 Nov 2026] Rules, on the daily close of QQQ, all three at once:
- RSI(3) below 22;
- the 100-day EMA higher than five trading days earlier (the EMA compared with itself; the close may be below the EMA);
- the close at least 1% below the 10-day rolling VWAP, computed on "daily typical price and volume" (video).

Buy at the next session's open. Substack: "Starting the session after entry, sell at the close when RSI(3) is above 55." Video: "exit after RSI recovers above 55". One position at a time. No stop, no target. Period in both sources: 1999 to September 2026. The video states the results exclude commissions and slippage.

There are two versions of the result:

| Version | Source | Trades | Win rate | Profit factor | RSI(3) alone | Max. drawdown |
|---|---|---|---|---|---|---|
| A | video, 9 Oct 2026 | 215 | 78.6% | 3.94 | PF 2.27 | about $10,943 at a fixed $100,000 per trade |
| B | Substack, 12 Nov 2026 (edited 19 Nov) | 215 | not stated | 3.54 "before costs" | PF 2.19 | not stated |

Video, sub-periods: PF 5.62 (1999-2008), 3.29 (2009-2017), 3.47 (2018 to Sep 2026). Video: RSI + EMA without VWAP PF 3.08 [verified, transcript].

## 2. Testable claims

| # | Claim | Testable as |
|---|---|---|
| C1 | Profit factor 3.94 (A) or 3.54 (B) | Net profit factor, with 95% interval (bootstrap per trade) |
| C2 | Win rate 78.6% (A) | Win rate with 95% interval (Wilson) |
| C3 | Max. drawdown about $10,943 at a fixed $100,000 per trade (A) | Descriptive: largest decline of the sum of closed trades, $100,000 per trade |
| C4 | All three sub-periods PF above 3 (A) | Descriptive: each period has fewer than 100 trades |
| C5 | The three conditions pick better entry days than chance in the same trend (implicit: "a temporary pullback inside a stronger backdrop") | Mean net return per trade against Null A |
| C6 | EMA and VWAP make RSI(3) better than RSI(3) alone ("the filters did what we wanted them to do") | Mean net return per trade against Null B: the same number of trades, drawn at random from the unfiltered RSI(3) signals |

## 3. Weak points, named in advance

1. [verified] The source shows the full QQQ history up to Sep 2026. There is no QQQ period the source could not see, apart from Oct and Nov 2026 (too short). Reproduction therefore proves little; C5 and C6 (against the control groups) decide.
2. [verified] Two profit factors (3.94 and 3.54) and two RSI baselines (2.27 and 2.19) at the same number of trades. Possibly a different RSI variant or exit day between the versions [assumption]. We test both numbers; the rules are the same.
3. [verified, arithmetic] At 215 trades the 95% interval around 78.6% runs from about 72.6% to 83.6%. C2 only fails if the measured win rate is below about 73.2%.
4. [assumption, reasoned] An exit without a stop on an index with upward drift also gives a high win rate with random entries. A high win rate alone says little.
5. [verified, our log] Fourth long-only mean-reversion test on a US index, after Buy the Dip, E (RSI(2) pullback) and I (Triple RSI), none of which was falsified. The results are not independent; QQQ and SPY largely move together.
6. [assumption] Each sub-period has about 70 trades: insufficient for its own verdict, descriptive only.
7. [verified, description] Another channel already re-ran the rules (PF 4.00 without costs, from 2016 PF 2.20 on 85 trades). That is a reproduction, not a control against chance.

## 4. Mechanical translation (fixed)

All points below are **[assumption]**: choices made to turn the text into rules.

**4.1 Market and data.** QQQ daily prices (open, high, low, close, volume) from Yahoo Finance, from the first trading day (10 March 1999) to the last closed day before the run. Signals and returns on the close without dividend adjustment ("close"); adjusted close as sensitivity only (K5). Splits are applied in the Yahoo series, volume included. Raw download with SHA-256 in the test folder.

**4.2 RSI(3).** Wilder RSI with period 3 on the close (smoothing alpha 1/3), the Amibroker default (K1).

**4.3 EMA(100).** Exponential average of the close, alpha 2/101, seeded with the simple average of the first 100 closes. Condition: EMA(t) > EMA(t-5).

**4.4 Rolling VWAP(10).** Typical price TP = (high + low + close) / 3. VWAP(t) = sum of TP × volume over the last 10 trading days up to and including t, divided by the sum of volume over those days. Condition: close(t) ≤ 0.99 × VWAP(t).

**4.5 Warm-up.** A signal is possible from the first day on which EMA(t-5) exists (trading day 105). This keeps most of 1999 in the test, as in the source.

**4.6 Signal on day t.** RSI(t) < 22, EMA(t) > EMA(t-5) and close(t) ≤ 0.99 × VWAP(t).

**4.7 Entry.** At the open of day t+1.

**4.8 Exit.** At the close of the first check day on which RSI(3) is above 55 (a level, not a cross). The first check day is the day after the entry day (K2, literal reading of "Starting the session after entry"). No stop, no target, no time limit. Open at the end of the data: closed at the last close and reported separately.

**4.9 One position at a time.** A signal during an open trade is dropped. A signal on the exit day itself counts (entry the next day).

## 5. The three fixed rules

**Costs.** 2 basis points round trip per trade, as in Buy the Dip, E and I. Sensitivity: 0, 2, 4 and 10 bp. The source has no costs; at an average of more than 1% per trade [assumption] 2 bp hardly moves the PF.

**Order.** Entry at the open, exit at the close. The rule has no intraday stop or target, so the intraday path decides nothing [verified, rules]. Measured per trade anyway: the lowest daily low against the entry price, because without a stop that is where the risk is.

**Control groups.** 10,000 runs, seed 38. Look at the control first, then the rule.
- **Null A, decisive for C5:** random signal days from the days on which the EMA condition holds (K3), entry at the next open, as many trades as the rule, one position at a time. Each fake trade gets the duration of a real trade (the real durations, shuffled). Tests whether RSI and VWAP pick better days than a random day in the same trend, with the same time in the market.
- **Null B, decisive for C6 (v1.1):** a sequential process, like the rule itself. Each day with RSI(3) < 22 (without the EMA and VWAP filters) becomes a fake signal with probability p; then the same handling as the rule: entry at the next open, own exit rule (4.8), one position at a time, a signal during an open trade is dropped. p is set so the mean number of trades equals the rule's (bisection, 18 steps of 40 runs). Tests whether the two filters do more than reduce the number of trades.

## 6. Noise check before the real data (fixed)

24 fake markets of 6,950 trading days (about 27.6 years), a random walk with memoryless daily returns, drift 0.04% and volatility 1.8% per day [assumption: roughly QQQ]. Open = previous close × (1 + N(0; 0.4%)); high and low = highest and lowest of open and close, × (1 ± |N(0; 0.6%)|); volume lognormal and independent of price. Seed 7.

Limit, as in earlier tests: percentile against Null A and against Null B each on average between 35 and 65, at most 3 of 24 above 95. If the check fails, the script is fixed first, before the real data.

Result (2,000 runs per set) [verified]: v1.0 Null A mean 59.3, 1 of 24 above 95; Null B mean 0.0: **failed**. v1.1 Null A 61.5, 2 of 24 above 95; Null B 51.8, 2 of 24 above 95: **passed** (`noise_24sets_v1.0.txt`, `noise_24sets_v1.1.txt`).

## 7. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | 10 Mar 1999 to the last closed day | **Decisive** for C1, C2, C5, C6 |
| P0 | 10 Mar 1999 to 30 Sep 2026 | Reproduction: 215 trades, 78.6%, PF 3.94 or 3.54, drawdown about $10,943? Not decisive |
| P2 | 1999-2008, 2009-2017, 2018 to 30 Sep 2026 | C4 and distribution. Below 100 trades: insufficient |
| P4 | 1 Oct 2026 to the last day | After the source. Descriptive, very few trades |
| P3 | SPY, 29 Jan 1993 to the last day (K4) | Other market, same rules. Supplementary, not decisive |

## 8. When the idea is dead (in advance)

| Claim | Falsified in P1 if |
|---|---|
| C1 | The upper bound of the 95% interval of the net PF is below 3.94 (A); reported separately against 3.54 (B) |
| C2 | The upper bound of the 95% interval of the win rate is below 78.6% |
| C3, C4 | Not falsifiable in this measurement; only shown next to the claim |
| C5 | The mean net return per trade is not above percentile 95 of Null A |
| C6 | The mean net return per trade is not above percentile 95 of Null B |

After the run: no other RSI periods, thresholds, EMA or VWAP lengths, filters or exits. If a claim stands, it is "not falsified in this measurement", not "works".

## 9. Choices (fixed 28 Nov 2026: all five A)

| Choice | A (chosen) | B |
|---|---|---|
| K1 RSI variant | Wilder (smoothing 1/3), the Amibroker default; the source names Cutler only for another strategy [assumption] | Cutler (simple average of gains and losses over 3 days) |
| K2 First check day for the exit | Close of the day after the entry day (literal "Starting the session after entry") | Already the close of the entry day |
| K3 Pool for Null A | Days on which the EMA condition holds: tests RSI and VWAP within the same trend (as in test I) | All trading days: tests the whole package, trend filter included |
| K4 SPY as extra market (P3) | Yes, supplementary | No |
| K5 Price series | Close without dividends, adjusted close as sensitivity (as in E and I) | Adjusted close decisive |

The other variant of K1 and K2 is reported as a sensitivity next to P0, to show which variant comes closest to the source. The chosen variant in P1 stays decisive.

## 10. What we report, whatever the result

The funnel: trading days, days with RSI(3) < 22, with the EMA condition, with the VWAP condition, signals, dropped during an open trade, trades. Per period: trades, win rate (95%), mean net return (95%), PF (95%), worst trade, lowest daily low, mean duration, time in the market, drawdown at $100,000 per trade, and buy and hold over the same period. Percentiles against Null A and Null B. Cost sensitivity, adjusted close, the variants of K1 and K2. The noise check.

## 11. Change in version 1.1 (28 Nov 2026, before the real data)

[verified] On fake markets, Null B of v1.0 (drawing random days in random order and refusing a trade that overlaps) averaged about +1.1% per trade, against about +0.2% for the rule itself. Long trades overlap more often and are dropped more often, and without a stop long trades are often losers. So Null B mostly kept short winners, and the rule would always end up below Null B on real data. The same problem was solved earlier in test J with a control group as a sequential process.

Tested and rejected: Null B with shuffled durations (as Null A, but from the RSI days): mean percentile 13.2 on noise, also biased [verified].

Not changed: rules, claims, Null A, periods, costs, limits. On noise, Null A leans slightly towards the rule (mean 61.5 instead of 50) [verified]: a possible explanation is that the rule's own exit only comes after a rise, while the fake trades have a fixed duration [assumption]. Within the limit; it makes C5 slightly lenient rather than strict.

This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgment.
