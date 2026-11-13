# Buying SPY at the open: results

The claim comes from a side remark in a trading channel's video (September 2026), the same source as the Box Theory test. Over the last 15 years, if you bought SPY at the open, you were up after one hour on 51% of days, after two hours on 53%, and at the close on 54%. The video is no longer online; the claim was recorded from its transcript on 11 November 2026.

The hypothesis was written and fixed before any price data was opened: `hypothesis-v1.0-dutch.md`, with an English version written at the same time. The Dutch file is binding. The published Dutch file differs from the internal one only in a removed first name and one rephrased line in the last section.

## What the claim implies

A rising market has more up days than down days at any hour. So the percentages alone say little about the open. The test therefore has two parts: are the claimed numbers right (C1 to C3, C5), and is the open a better moment to buy than a random moment on the same day (C4)?

## Setup

| | |
|---|---|
| Script | `spy-opening/spy_open_control.py` in the repository root |
| Close (C3, C5) | SPY daily bars, Yahoo Finance chart API, raw prices, 19 Sep 2011 to 18 Sep 2026 (the 15 years before the video). Converted with `spy-opening/spy_json_to_csv.py`. Prices are not redistributed here; the source is `query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d`. Closed days 3 Jan 2011 to 12 Nov 2026: 3,990 rows, canonical SHA-256 3f7d5229... (see `datacheck_g2.txt`) |
| 1 and 2 hours (C1, C2, C4) | MT5 S&P 500 CFD (US500) M1 export from one broker, server time. Real minute data from 21 March 2017. Not SPY |
| Session | 9:30 to 16:00 New York. The opening minute is taken per day from the jump in tick volume at 16:30 server time, or one hour earlier or later in weeks where daylight saving differs. A session counts with at least 90% of its 390 minute bars |
| Up | Price at the check strictly above the opening price. Equal days reported separately |
| Costs | SPY: 2 basis points per round trip. US500: spread at the opening bar plus 1 bp. Sensitivity 0, 2 and 4 bp. C1 to C3 are measured without costs, as the claim |
| Control (C4) | On the same days, the same window (1 or 2 hours) from a random start minute in the session, same costs. 10,000 runs, seed 29 |
| Decisive period | P1: 19 Sep 2011 to 18 Sep 2026 (SPY); 22 Mar 2017 to 18 Sep 2026 (US500) |
| Run | Variant 1 of 1 |

## Noise check (before real data)

24 synthetic markets of 2,300 days, no trend, no opening effect. The open should sit in the middle of its control.

| | 1 hour | 2 hours |
|---|---|---|
| Average percentile | 50.4 | 57.3 |
| Above the 95th | 0 of 24 | 0 of 24 |
| Planted +0.05% in the first hour, found above the 95th | 24 of 24 | 23 of 24 |

Output: `noise_24sets.txt`.

## Data check (before the run, metadata only)

SPY 250 to 253 trading days per full year, open equal to the previous close on 0.88% of days, no open outside the day range, no duplicate dates. US500: opening found on 100% of server days, valid sessions 92.9%. Only 124 valid sessions in 2017. On 7 days the opening was found at 17:30 server time, probably a misdetection; effect on 2,278 days small. Output: `datacheck_g2.txt`.

## Result, P1 (decisive)

| Check | Measured | 95% range | Claim | Verdict |
|---|---|---|---|---|
| Up at the close (SPY), 3,772 days | 54.11% | 52.52-55.69% | 54% | Not rejected |
| Up after 1 hour (US500), 2,278 days | 52.24% | 50.19-54.28% | 51% | Not rejected |
| Up after 2 hours (US500) | 53.69% | 51.64-55.73% | 53% | Not rejected |
| Up more often than down | lower bounds above 50% | | | Not rejected |
| 1 hour, open vs random start, net | -0.46 bp, percentile 88.6 | | above 95 needed | **Rejected** |
| 2 hours, open vs random start, net | +0.07 bp, percentile 89.9 | | above 95 needed | **Rejected** |

SPY open to close, net of costs: +0.21 bp per day at 2 bp, -1.79 bp at 4 bp. On the 2,278 days both series share, the share of up closes was 53.20% for SPY and 54.13% for US500 (difference +0.92 percentage points, same sign on 96.6% of days).

After the video (from 19 Sep 2026): 39 SPY days, 30 US500 sessions. Insufficient.

Full output: `run01_spy.txt`, `run01_us500.txt`.

## Limitations

One and two hours are measured on a CFD from one broker, not on SPY, and only from 2017. The exact period of the claim is unknown. Costs are assumptions. The share of up days depends on the period.

This is a measurement of one claim in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
