# Hypothesis: RSI(2) pullback, executed at the open (test E2)

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-next-open-v1.0-dutch.md`, fixed on 11 November 2026 before any opening prices were looked at (SHA-256 of the published Dutch file: d7a62db7b7a89fa8c686ac0d16e8d624ce6d16d9970a555836ae5f57490b1d86). If the two differ, the Dutch text applies.

Date: 11 November 2026 · Reason: a reader's comment under article 9 (8 Nov 2026) · Basis: test E, `hypothese-rsi2-pullback.md` v1.0 (8 Nov 2026), published here as `../hypothesis-v1.0-dutch.md` · Status: **version 1.0, 11 November 2026, approved (control group A: drawn the same way as in test E), no opening prices looked at yet**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. Test E (v1.0) stays as published; this is a separate test, not a replacement.

## 1. Why this test

[verified, article 9] Test E buys and sells exactly at the close of the signal day. In practice a reader can hardly do that: the signal is only known once the market has closed. Article 9 itself already calls this an idealisation.

[verified, reader's comment of 8 Nov] The reader suggests: execute the same rule at the open of the next day, let the control group trade the same way, and put the result next to the frozen replication instead of replacing it.

So this test measures one thing: **does the rule survive when you execute it the way a reader can?** It is not a parameter variant: rules, thresholds, filter and period are the same as in test E. Only the moment of buying and selling shifts.

## 2. Testable claims (same as test E)

| # | Claim | Testable as |
|---|---|---|
| C1 | 84.31% of trades are profitable | Win rate with 95% interval |
| C2 | The rule makes money | Mean net return per trade with interval |
| C3 | The entry picks better days than chance within the trend filter | Real result against Null A, both executed at the open |

## 3. Weak spots, named in advance

1. [assumption] A large part of a short rebound after a drop can already happen overnight, between the close and the open. Then execution at the open misses part of the gain. That is exactly what this test measures; the direction of the outcome is unknown.
2. [assumption] The exit shifts too: the rule only sells on the morning after the day on which RSI(2) closed above 75. A gap up or down overnight counts.
3. [assumption] Opening prices of an index are not tradable prices: an index ETF or future opens at a slightly different price. This remains an approximation, but one a reader can reproduce.
4. [assumption] Yahoo opening prices from older years are sometimes equal to the previous day's close (not a real open). See the data check in 5.

## 4. Mechanical translation (fixed)

Everything from test E v1.0, section 3, stays the same (Wilder RSI(2), SMA 200 on closes, signal on day t with the filter on day t, one position at a time, warm-up of 250 days), with these changes **[assumption]**:

**4.1 Entry.** At the opening price of day t+1, the first trading day after the signal.

**4.2 Exit.** RSI(2) closes above 75 on day j (first day after the signal day t). Sell at the opening price of day j+1. No stop, no time limit. Still open at the end of the data: close at the last close and report separately.

**4.3 Next signal.** A new signal only counts from the day after the selling day j+1 (day j+1 itself has a sale at the open; a signal at the close of j+1 is allowed, because the position is then closed) [assumption].

## 5. Data (fixed)

- ^GSPC daily data with opening and closing prices, Yahoo Finance, the same source as test E. If the current series only has closes, fetch it again via the same route (browser) [assumption: the Yahoo series contains an open column].
- Data check before the run, on the prices only, not on outcomes: share of days with the open exactly equal to the previous close, and opens outside the day's range (below the low or above the high). If in P1 more than 5% of days have open = previous close, this is reported and the test still runs, with that caveat.
- The closes must be equal to the series of test E. If they differ, investigate first [check].

## 6. The three fixed rules

**Costs.** 2 basis points round trip, sensitivity 0, 2 and 4 bp. Same as test E.

**Order of events.** Entry and exit at opening prices; no stop or target within the day. The deepest interim drop per trade is also measured, on closes, from the entry price.

**Control group.** 10,000 runs, seed 23. Null A decisive, Null B additional, with the same definitions as test E, but **with the same execution**: random signal day, entry at the open of the next day, exit at the open after the day on which RSI(2) closes above 75.

Drawing of the control group: **option A chosen** (11 Nov 2026). For the record, the trade-off:

| | A. Same as test E | B. Sequential, as in test F v1.1 |
|---|---|---|
| What | Random order, without overlap ("greedy"), exactly as in test E | Waiting time and order like the rule itself |
| Advantage | Only the execution differs from test E: the comparison is clean | Methodically the newest control |
| Disadvantage | Leaned against the rule in test E (noise mean 31.7) | Two things differ from test E at once |
| Proposal | **Yes**: the reader's question is only about the execution | |

## 7. Noise check before the real data (fixed)

24 synthetic series of 5,000 trading days, 7% rise per year and 18% volatility (same as test E), each day split into an overnight part (close to open) and a day part (open to close). The overnight part gets 30% of the variance [assumption, chosen before seeing opening prices]. Seed 7.

Bounds, same as the audit of 10 Nov: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95. If the mean is below 35 (as in test E, 31.7), the control leans against the rule: a positive outcome then stays valid, a negative one is reported with that caveat.

## 8. Periods (fixed)

| Run | Period | Role |
|---|---|---|
| P1 | 1 Jan 2007 through the last day | **Decisive**, same as test E |
| P2 | per year within P1 | Spread, not decisive |

No P0 (1995-2006): the opening prices of those years are less reliable [assumption], and the replication of the source was already done in test E.

## 9. When is the idea dead (in advance, same as test E)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate in P1 is below 84.31% |
| C2 | The upper bound of the 95% interval of the mean net return per trade is below 0 |
| C3 | The mean net return per trade is not above percentile 95 of Null A |

If C3 falls: publish as "the published rule survived at the close, the version a reader can execute did not". Both outcomes stay side by side. No other execution times (for example the next day's close) will be tried.

If C3 stands: report as "not falsified, also at the open", with the limitations, not as "works".

## 10. What I report, whatever the outcome

Everything from test E section 7, plus side by side: test E (close) and E2 (open) for number of trades, win rate, mean net return, percentile against Null A. And the mean overnight return on the rule's entry and exit days, so it is visible where the difference comes from.

## 11. Next step

1. Approved on 11 November 2026 (option A). SHA-256 in the measurement log.
2. Script `rsi2_next_open.py` based on `rsi2_control.py`; first the noise check from 7.
3. Data check from 5 on the real series, then the run.
4. Code and data on GitHub before publication; reply under the reader's comment with the outcome, whichever way it goes.
