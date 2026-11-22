# Hypothesis: noise-area intraday momentum (test R)

Translation of the Dutch original `hypothese-noise-area-momentum.md`, version 1.2. The Dutch file is binding (file name, SHA-256 and date in the measurement log).

Date: 21 November 2026 · Source: a YouTube video of 14 November 2026 (a testing channel), based on a 2024 research paper · Status: **version 1.2, 21 November 2026, fixed in advance, choices K1 A, K2 A, K3 A, K4 C, K5 A made on 21 November 2026, no real price data opened for this test yet**

Change from v1.0 (21 November 2026, SHA-256 1eda21bb...): section 4.5 only. In v1.0 a position could exit at a check time and immediately reopen in the same direction; the position did not change, but the costs were paid twice. That followed from my wording, not from the source. The self-test showed it (day 18). v1.1 follows the public replication: at the same moment only a reversal to the other direction (Erwin's choice A, 21 November 2026). Changed before any run on real data.

Change from v1.1 (21 November 2026, SHA-256 e3e45657...): section 4.1 and the data check in section 7 only. The data check (metadata only) showed that detecting the open from tick volume chose 8:30 New York time on 156 days in 2021 to 2026: mostly days with jobs and inflation releases, when volume jumps harder at 8:30 than at the open. On those days the real open is at 16:30 server time, and the server is at New York + 7 all year, also in the weeks when Europe and the US are on different daylight saving time [verified, tick volume]. v1.2 therefore uses a fixed open (Erwin's choice K6 A, 21 November 2026). Changed before any run on real data.

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule: everything below is fixed before the first run. Nothing is changed after the run. If a choice turns out untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, video description and transcript] The rule, taken by the video from the paper:
- Noise band: for each time of day, the average absolute move from the open over the last 14 days. The band sits around the open and shifts on a gap: "If there was a gap overnight, the band starts at yesterday's close on that side."
- Every 30 minutes from 10:00 New York time: long above the upper band, short below the lower band.
- Exit "when the price falls back into the band or when it crosses the VWAP". Always flat at the close.
- The video's test: CME futures, minute bars, January 2020 to October 2026, one contract, commission and one tick of slippage on every entry and every exit.

[verified, video description] The results the video reports:
- Nasdaq futures: "1,564 trades, +6.8 points per trade after costs, t-statistic 2.6, 41% winners, every year 2020-2026 positive."
- "Random direction: 4 of 1,000 reached the real result."
- S&P 500 futures: "+0.5 points per trade, t-statistic about 1."
- After the paper appeared (May 2024): 8.4 points per trade on 549 trades (transcript).

[verified, SSRN abstract] The paper itself reports on SPY, 2007 to early 2024: 1,985% total after costs, 19.6% a year, Sharpe 1.33. That number is not tested as decisive (see K1).

[verified] Testable claims (decisive on the Nasdaq 100, choice K1 A):

| # | Claim | Testable as |
|---|---|---|
| C1 | "+6.8 points per trade after costs" | Mean net result per trade in points over P1 |
| C2 | The rule picks better moments and directions than chance ("unlikely that this is just luck") | Real result against the control group with random entry moment and random direction (Null B) |
| C3 | "every year 2020-2026 positive" | Net sum per calendar year in P1 |

Descriptive, not decisive: win rate 41%, number of trades 1,564, the coin test on direction (4 of 1,000), the S&P 500, the period after the paper.

## 2. Weak spots visible before the test

1. [verified] This rule has been tested in public several times already: an independent replication on SPY and ES, a second paper outside the original sample, the testing channel itself and a TradingView script. Our data largely overlaps with the video's (2020 to October 2026). This is a replication on data from another source, not a test on new data.
2. [verified, earlier tests] Our data is a CFD on the Nasdaq 100 (USTEC) with tick volume, not a future with exchange volume. The VWAP is weighted with tick volume [assumption that this approximates the real VWAP]. Sensitivity: VWAP without volume (all minutes equal weight).
3. [assumption] CFD points are close to NQ points but not exactly equal (the future carries an interest premium). For a per-trade comparison the difference is small.
4. [verified, earlier tests N and O] Our fixed costs on USTEC (spread plus 1 point slippage per side) are higher than the video's (one tick of 0.25 point per side plus commission). C1 can therefore fail on costs alone. That is why we also report the video's cost level (K5 B) and the result without costs, and every publication states which level is decisive.
5. [verified, transcript] According to the video the profit comes from a few big days ("If you take out the 10 best days ... drop to about $7,300"). The result is therefore sensitive to a few days. We report the result without the 10 best days.
6. [verified] The video does not say which price the VWAP uses, whether the check uses the minute's close, or where the order fills. Those choices are fixed in section 4.

## 3. Choices (made on 21 November 2026: K1 A, K2 A, K3 A, K4 C, K5 A, the options in bold)

| Choice | A | B | C |
|---|---|---|---|
| K1 · Decisive claim and market | **Nasdaq 100 (USTEC), the video's claim** | S&P 500 (US500), the paper's claim, measurable only from 2017 | Both decisive |
| K2 · Entry | **Outside the band only, as the video describes it** | Outside the band and on the same side of the VWAP, as the TradingView script and the second paper read it | |
| K3 · Period | **2 January 2020 to 5 November 2026 inclusive (end of our data)** | 2017 to 2026 | |
| K4 · Control group | Same trades, coin flip on direction (the video's test) | Random entry moment, coin flip on direction, holding time from the real trades | **Both, B decisive** |
| K5 · Costs | **Our fixed method: spread from the data plus slippage per side (1 point on USTEC, 0.25 point on US500), sensitivity 0, 1 and 2 times** | The video's cost level: 0.25 point slippage plus 0.125 point commission per side, 0.75 point per trade in total [assumption: commission of about $2.50 per side on one NQ at $20 per point] | |

The unchosen variants of K1, K2 and K5 are reported as supplementary, not decisive.

## 4. Mechanical translation (fixed after approval)

All points below are **[assumption]**: choices to translate the text into rules.

**4.1 Session.** Regular trading hours only, 9:30 to 16:00 New York time, 390 minute bars, fixed from 16:30 to 23:00 server time (New York + 7). A day is valid with at least 90% of the 390 minute bars in that window. The report gives the number of valid days without a clear volume jump at 16:30 (mean tick volume 16:30-16:59 not at least 1.3 times that of 16:00-16:29), without excluding them. Half trading days therefore drop out by themselves (as the script also skips them). A minute bar is named after its start time: the 9:59 bar closes at 10:00.

**4.2 Noise band.** For session minute t (t = 0 for the 9:30 bar) and valid day d:
- O_d = open of the 9:30 bar.
- C_d = close of the 15:59 bar.
- move(d, t) = |close of bar t / O_d − 1|.
- σ_t on day D = mean of move(d, t) over the 14 preceding valid days (day D itself is excluded).
- Upper band_t = max(O_D, C_previous) × (1 + σ_t); lower band_t = min(O_D, C_previous) × (1 − σ_t). C_previous is the close of the preceding valid day.
- Width factor 1, lookback 14 days (fixed, as paper, video and script). The first 14 valid days of the data do not trade (warm-up); P1 only starts after those 14 days, the warm-up falls in December 2019.

**4.3 VWAP.** Restarts every day at the 9:30 bar. Price per minute = (high + low + close) / 3, weight = tick volume of that minute. VWAP at a check time = sum(price × volume) / sum(volume) over all minute bars closed before that time.

**4.4 Check times.** 10:00, 10:30, ..., 15:30 (12 a day). At each time the close P of the minute bar that closes at that time applies (bar t = 29 at 10:00, and so on), with σ_t of the same bar.

**4.5 Signal and exit at a check time, in this order.**
- Long open: exit if P < max(upper band, VWAP).
- Short open: exit if P > min(lower band, VWAP).
- If there was no position at the start of the check time: long if P > upper band, short if P < lower band (K2 A). Under K2 B (supplementary) P must also be above (long) or below (short) the VWAP.
- If a position has just been closed at this check time, only a position in the other direction may open at the same moment (reversal): after a long a short if P < lower band, after a short a long if P > upper band (under K2 B also on the right side of the VWAP). A new entry in the same direction can only come at the next check time.
- A position that still qualifies simply stays open.

**4.6 Fills.** Entry and exit at the open of the minute bar directly after the check time (at 10:00 that is the open of the 10:00 bar). Never at the close on which the signal was determined.

**4.7 Close.** A position still open at 16:00 is closed at the close of the 15:59 bar. An entry at 15:30 is allowed; it closes at 16:00 at the latest.

**4.8 Position size.** One unit per trade, result in index points, as in the video (one contract). The paper's volatility target and leverage are outside this test; the paper's yearly percentage is therefore not measured.

**4.9 Result.** Per trade in points and in basis points of the entry price, net of costs. There is no fixed stop, so no R.

## 5. The three fixed rules

**Costs.** K5 A: the spread from the SPREAD column at the entry minute (in points), plus slippage per side (entry and exit): 1 point on USTEC, 0.25 point on US500, as in tests N and O [verified, README test N]. Sensitivity: slippage 0, 1 and 2 times. Supplementary K5 B: 0.75 point per trade, without spread.

**Order.** The path is followed minute by minute. All decisions fall on check times and all fills on the open of the next minute; there are no stops or targets inside a bar, so the order within a minute does not matter.

**Control group.** 10,000 runs, seed 43. Percentile of the real mean net result per trade against the distribution of the runs. Confidence intervals by bootstrap per trading day, also 10,000 times.
- **Null B, decisive for C2:** the same valid days in P1, the same check times, the same costs. A sequential process: at every check time without an open position, chance opens a position with probability p, direction by a fair coin. The holding time in check intervals (1, 2, ...) is drawn per trade from the distribution of the real trades in P1; the exit falls on the open after that check time, or on the close at 16:00 if that comes first. p is set so that the expected number of trades equals the rule's. Tests whether the noise band picks better moments and directions than chance with the same exposure.
- **Null A, supplementary (the video's test):** every real trade with the same entry and exit, direction by a fair coin.

## 6. Noise check before the real data (fixed)

24 fake markets of 1,500 trading days with minute bars (only 9:30 to 16:00 and a small overnight jump), built from 60 sub-steps per minute as in tests G, H and N, without trend, without opening effect and without momentum, with a fixed spread of 1 point and random tick volume. Seed 7. Start price and yearly volatility as in test N [assumption].

Threshold, equal to the audit of 10 November: mean percentile against Null B between 35 and 65, at most 3 of 24 above 95. Null A is also measured on noise and must meet the same threshold. If the script fails, first find the cause and write a new version of this document, before the real data.

In addition, before the noise check, a self-test: noise band, VWAP and the decision rule against a second, simple implementation on a few hand-made days (gap up, gap down, reversal, close at 16:00).

## 7. Data

[verified, file names and data checks of tests G and N] USTEC M1, IC Markets, `Test\box-theory\USTEC_M1_201208060000_202611052200.csv`, runs to 5 November 2026. US500 M1, `Test\lce-supply-demand\US500_M1_201208060000_202611021049.csv`, real minute data from 21 March 2017, spread column filled from 2019, runs to 2 November 2026. Nothing has been opened for this test yet.

Periods:
- **P1, decisive for C1, C2 and C3:** USTEC, all valid sessions from 2 January 2020 to 5 November 2026 inclusive.
- Supplementary: US500 over the same period (to 2 November 2026); USTEC 2017 to 2019 inclusive (K3 B); USTEC from 14 May 2024 (the paper has been online since that day [verified, SSRN]).

Data check before the run, metadata only: number of valid sessions per year, number of days without a clear volume jump at 16:30, share of minutes with an empty spread, minutes with zero tick volume, unit of the spread column on USTEC.

## 8. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval (day bootstrap) of the mean net result per trade in P1 lies below 6.8 points |
| C2 | The real mean net result in P1 does not lie above percentile 95 of Null B |
| C3 | At least one calendar year 2020 to 2026 inclusive (2026 to 5 November) has a negative net sum |

If C2 fails, the idea is dead: no repair, no optimisation, no filters, no other lookback or check interval. Below 100 trades in a period or year the report says "insufficient trades".

## 9. What I report, whatever the outcome

Number of trades and trades per day, win rate (descriptive, against 41%), mean net result in points and basis points with 95% interval, profit factor, percentile against Null B and Null A, the result without costs, the three slippage levels and K5 B, median holding time, average win and average loss, long and short separately, per year, the period after the paper, the result without the 10 best days, the largest drop in cumulative points, K2 B, the VWAP without volume, US500 (K1 B) and USTEC 2017 to 2019.

Title by the fixed rule: no percentage in the claim, so the main number: "+6.8 points per trade claimed", with our measurement next to it. No names of the paper, the video or the script in publications.

## 10. Next step

1. Approved: v1.0 by Erwin on 21 November 2026, v1.1 (section 4.5 only) and v1.2 (section 4.1 and the data check in section 7 only) by Erwin on 21 November 2026. SHA-256 in `meetlog-noise-area-momentum.md`. English version alongside.
2. Script `noise_area.py`: self-test from section 6, then the noise check.
3. Data check from section 7, then run 01, control group first.
