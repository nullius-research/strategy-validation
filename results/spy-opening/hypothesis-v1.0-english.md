# Hypothesis: buying SPY at the open (test G2, side claim of test G)

Date: 13 November 2026 · Origin: side claim in source 3 of test G · Status: **version 1.0, 13 November 2026. Data source A chosen (13 Nov). Approved on 13 Nov 2026. No price data opened.**

This is the English version. The Dutch original (`hypothese-spy-opening.md`, same date) is binding; its SHA-256 is in the measurement log.

Legend: **[verified]** = checked or calculated ourselves · **[assumption]** = not checked ourselves, or a choice in the measurement

Rule: everything below is fixed before the first run. After the first real run nothing changes; a new version gets a new date.

## 1. The claim

[verified, transcript read on 11 Nov 2026, timecode 23:20-23:54] A trading video from 19 September 2026 says: "over the last 15 years, if you just bought the SPY" at the open and sold, you were in profit 51% of the time after one hour, 53% after two hours, and 54% at the end of the day.

[verified, 13 Nov 2026] The video and the whole channel can no longer be viewed: YouTube reports that the account was terminated. The quote above can therefore no longer be checked at the source. Only the words in quotation marks were noted verbatim; the rest is our summary of 11 Nov.

## 2. Testable claims

| # | Claim | Testable as |
|---|---|---|
| C1 | After 1 hour SPY is above the open on 51% of days | Share of days higher, with 95% interval |
| C2 | After 2 hours: 53% | Same |
| C3 | At the close: 54% | Same |
| C4 | The open is a good moment to buy (implied: "if you just bought the SPY") | Mean net return of the window, against the same window from a random time on the same day (Null A) |
| C5 | Buying at the open wins more often than it loses | Lower bound of the 95% interval above 50% (coin flip) |

C4 and C5 are not stated literally in the video. They are our translation of what the claim suggests [assumption]. In the publication they are kept separate from C1 to C3.

## 3. Weak points, named in advance

1. [verified] The source is offline; the exact wording and the maker's calculation can no longer be checked.
2. [assumption] "In profit" can mean: price above the open (without costs), or above it after costs. We measure the first as the claim, the second as a supplement.
3. [assumption] A rising market gives slightly more than half rising days by itself. A number above 50% therefore says little about the open itself; hence C4.
4. [assumption] "15 years" counted back from the video: 19 Sep 2011 to 18 Sep 2026 inclusive. The maker may have used a slightly different period.
5. Depending on the data source (section 5): with option A, C1, C2 and C4 are measured on a CFD on the S&P 500, not on SPY, and only from 2017.

## 4. Mechanical translation (fixed)

**4.1 Open.** The first minute of the exchange session, 9:30 New York time. With minute data from MT5 (server time): detected as in test G, from the largest jump in tick volume around 16:30 server time, allowing 60 minutes earlier or later for weeks with a daylight saving difference. A day only counts if the session has at least 90% of its 390 minute bars. Opening price = the open of that first minute bar.

**4.2 Measurement points.** Price after 1 hour = close of the 60th minute bar of the session (10:30). After 2 hours = close of the 120th (11:30). Close = close of the last session bar (16:00), or with daily data the official close. On shortened sessions (13:00) that day's close counts; 1 and 2 hours stay the same.

**4.3 Higher.** Price at the measurement point strictly above the opening price. Equal counts as not higher; the share of equal days is reported separately.

**4.4 Return.** (price at measurement point / opening price) minus 1. Net: minus the costs from 6.

## 5. Data (fixed: option A, chosen on 13 Nov 2026)

| | A. Yahoo SPY daily + MT5 US500 M1 | B. Paid SPY minute data | C. Close only |
|---|---|---|---|
| C3 (close) | SPY daily data Yahoo, 19 Sep 2011 to 18 Sep 2026, exactly the claim period | SPY, 15 years | SPY daily data Yahoo, 15 years |
| C1, C2, C4 | US500 M1 (IC Markets, already on file), real minute data from 21 Mar 2017. CFD, not SPY | SPY, 15 years | Not tested, reported as not testable |
| Cost | Free, data partly on file | Purchase, source and price still to find | Free |
| Proposal | **Yes**: quick, with the limitation stated in every publication | Only if the CFD measurement leaves doubt | |

With option A also a check on the CFD as a stand-in: on the days both series have (2017 to 2026), the share higher at the close on US500 next to that on SPY. If they differ by more than 2 percentage points, this is reported with C1 and C2 [assumption: threshold chosen before the data].

Data check before the run, on prices and metadata only, not on outcomes:
- SPY: trading days per year (expected about 252), days with open equal to the previous close, open outside the day's range. If more than 2% of days have open = previous close, report it.
- US500: share of days where the open was found, share of valid sessions, distribution of the detected opening minute (16:30, 15:30, 17:30 server time).

## 6. The three fixed rules

**Costs.** SPY: 2 basis points per round trip [assumption: spread of about 1 cent plus some slippage]. US500: the spread from the SPREAD column on the opening bar, plus 1 basis point slippage [assumption]. Sensitivity 0, 2 and 4 bp. C1 to C3 are measured without costs, as the claim is; the share after costs is reported next to it.

**Path.** No stop and no target: the position runs from the open to the measurement point. Per day also the deepest interim drop within that window (minute data only), for information.

**Control group.**
- C4, Null A (decisive): for each window (1 hour, 2 hours), on the same days, a random start minute within the session, with the same window and the same costs, such that the window stays within the session (start between 9:30 and 15:00 for 1 hour, between 9:30 and 14:00 for 2 hours). The open itself may also be drawn. 10,000 runs, seed 29. Measured: mean net return per day. Percentile of the real value within the distribution.
- C5: coin flip, 50%.
- For the close there is no meaningful Null A within the day (the window always starts at the open). The close is therefore only set against 50% (C5), and the claimed value against the measurement (C3).

## 7. Noise check before the real data (fixed)

24 synthetic series of 2,300 days with 390 minute bars, without trend and without an opening effect, volatility per minute chosen so that the daily move is about 1.1% [assumption]. Seed 7.

Limits, as in the audit of 10 Nov: percentile of C4 against Null A between 35 and 65 on average, at most 3 of 24 above 95. Share higher at 1 hour, 2 hours and the close between 49 and 51% on average.

Extra sensitivity check (reported, not decisive): the same 24 series with an artificial rise of 0.05% in the first hour. Expected: percentile above 95 in most sets. If the check reaches that in fewer than 20 of 24, the publication states that the test can miss small opening effects.

## 8. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | 19 Sep 2011 to 18 Sep 2026 inclusive (claim period); with minute data from the first full day after 21 Mar 2017 | **Decisive** |
| P2 | per year within P1 | Distribution, not decisive |
| P3 | 19 Sep 2026 to the last day | After the claim. Fewer than 100 days: reported as insufficient |

## 9. When is the claim falsified (in advance)

| Claim | Falsified if |
|---|---|
| C1, C2, C3 | The claimed value (51, 53, 54%) lies outside the 95% interval (Wilson) of the measured share. The direction is reported: a higher measured share also contradicts the claim, but with a different message |
| C4 | The mean net return of the window is not above percentile 95 of Null A |
| C5 | The lower bound of the 95% interval is at or below 50% |

After the run: no other times, windows or cost levels are tried. If a claim stands, it is reported as "not falsified in this measurement", not as "works".

## 10. What I report, whatever the outcome

Per measurement point: number of days, share higher (95% interval), share equal, mean return gross and net, percentile against Null A (1 and 2 hours). The year table. With option A the comparison US500 against SPY at the close. The noise check and the sensitivity check. The note that the source is offline.

## 11. Next step

1. Data source chosen (A, B or C) and hypothesis approved. SHA-256 in the measurement log.
2. Script `spy_open_control.py`, first the noise check from 7.
3. SPY daily data fetched via the browser pane (Yahoo chart API, as in test E), data check from 5, then the run.
4. Code and data on GitHub before publication.
