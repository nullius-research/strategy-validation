# Hypothesis: breakout of support and resistance on gold (test P), version 1.0

English translation. The Dutch original `hypothese-sr-breakout.md` (20 November 2026, SHA-256 in `meetlog-sr-breakout.md`) is binding; on any difference the Dutch text applies.

Date: 20 November 2026 · Source: a strategy book by an EA vendor (Sep 2026), details kept private · Status: **version 1.0, 20 November 2026. Choices K1-B, K2-A, K3-B and K4-B made by the researcher on 20 Nov; text approved on 20 Nov. After that, before looking at any data, the clarifications in 3.9 were added. No price data looked at for this test yet.**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule of play: everything below is fixed before the first run. Nothing is changed after the run. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the source promises

[verified, PDF p. 62-65 and 76-77] The source calls the breakout of support and resistance "the G.O.A.T. of trading systems" and writes "it works". The method in words:
- important levels, looked for across several timeframes, where price turned before;
- entry when price breaks the level, confirmed by a close beyond the level ("touching the level is not breaking it");
- stop just back inside the broken level;
- stop and target that move with market volatility, "let winners run";
- intraday on gold (XAUUSD), H1;
- further filters on volume, time of day and volatility, without exact rules.

[verified, PDF p. 12] Figures of the source's own EA (backtest 2004-2024, fixed 0.1 lot on 100K): win rate 69%, profit factor 2.13, at most 3 losses in a row, about 500 trades per year. The rules of that EA are not public [verified].

Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | A breakout of S/R on gold makes money | Mean net R per trade with 95% interval |
| C2 | The breakout picks better moments than chance ("captures big moves") | Real result against the control group |
| C3 | Win rate 69%, PF 2.13, at most 3 losses in a row | Descriptive only, next to our measurement, no verdict (see 2.1) |

## 2. Weak points, named in advance

1. [verified] We test a public translation of the described method, fixed in advance, not the source's EA. A result other than 69% or PF 2.13 may therefore come from our translation. That is why C3 is descriptive only, and every publication says it is a reconstruction (as in test J).
2. [verified] Volume is left out: the M30 export only has tick volume, and the source gives no rule.
3. [verified, log] Breakout rules have been measured three times without an edge: Donchian (article 1), volume breakout (Null Test 03) and the 5-minute opening range breakout (test H, percentile 18.7). New here: gold, levels from earlier turning points on H4 and D1, intraday.
4. [assumption] Gold rose strongly in 2025. A breakout rule goes long more often in a rising market and gets a tailwind without the timing adding anything. That is why the decisive period lies before 2025 (5), and why the decisive control group keeps the same share of longs and shorts as the rule (4).
5. [assumption] Broker time is probably GMT+2 or GMT+3. The day close and the supplementary time filter are therefore in broker time.

## 3. Mechanical translation

All points below are **[assumption]**: choices made to turn the text into rules.

**3.1 Data.** `XAUUSD_M30_199804220000_202611052200.csv`, the same MT5 export as test F, SHA-256 c7d40c32a3d53f7ccfcc199b51d910daccaeafc2e6f996a0a9e1925aa684d7d2 (checked again before the run). H1, H4 and D1 bars are built from the M30 bars per broker hour, 4-hour block from midnight, and broker date. The path of every trade is walked on M30.

**3.2 Usable data.** Same completeness check as test F: the measurement starts in the first calendar month in which every trading day has at least 40 M30 bars. Warm-up: the first 30 trading days after that start do not count.

**3.3 ATR.** Wilder ATR(14) on H1, value of the closed bar.

**3.4 Levels (K1-B).** Turning points on H4 and on D1. A resistance is the high of a bar j that is higher than the highs of the two bars before and the two bars after (strictly higher). A support is the low of a bar j that is lower than the lows of the two bars before and the two bars after (strictly lower). The level is active from the first H1 bar that starts after bar j+2 has closed. A level is only known once the bars that confirm it have closed, so there is no look-ahead. A level expires at its first breakout (used) or after 20 trading days.

**3.5 Signal on H1 bar t.**
- Long: close(t) > resistance and close(t−1) ≤ resistance (first close above).
- Short: close(t) < support and close(t−1) ≥ support.
- If several levels break at once, it counts once.
- No signal on the last H1 bar of the broker day.
- No time filter (K2-A). Reported as a supplement: only signal bars opening between 09:00 and 21:00 broker time.

**3.6 Entry and stop.** Entry on the close of bar t. Stop just back inside the level: long at resistance − 0.5 × ATR, short at support + 0.5 × ATR. Minimum stop 1.00 USD, as in test F; if the stop is smaller, no trade.

**3.7 Exit (K3-B, trailing stop).** No target. A = ATR(14) H1 at bar t, fixed for the whole trade. After the close of every M30 bar from the entry on: long, stop = max(stop, highest M30 close since entry − 2 × A); short, stop = min(stop, lowest M30 close since entry + 2 × A). The stop never moves back. The new stop applies from the next M30 bar. At the latest, exit on the close of the last M30 bar of the broker day (intraday, as in the source). R = net result in USD divided by the initial stop distance (entry to the stop from 3.6).

**3.8 One position at a time.** A signal during an open trade lapses. A level that breaks during an open trade also expires.

**3.9 Clarifications for the script (20 Nov, after approval, before looking at any data).**
- If several levels in the same direction break at once, the stop belongs to the level nearest to the close (long: the highest broken resistance, short: the lowest broken support). If a resistance and a support break in the same bar, no trade.
- The trailing stop is also updated after the close of the entry bar itself (the highest close since entry starts at the entry price).
- Waiting times in the control group are counted in H1 bars, from the H1 bar in which the previous trade closed to the H1 bar of the entry.
- Stop distance in the control group: drawn as a multiple of ATR (the rule's stop distance divided by its ATR at entry, 20 quantiles) and applied with the ATR on the control trade's entry bar. Reason: gold rose from about 400 to over 2,000 USD during the measurement period, so a stop distance in dollars from one year does not fit another [assumption, choice]. If that stop is smaller than 1.00 USD, no trade, as for the rule.
- Win rate = share of trades with net R > 0 (after costs).

### Choices made (20 Nov 2026)

| | Choice | Not chosen (will not be tried after the run either) |
|---|---|---|
| K1 level | B. Turning points H4 and D1 | A. High and low of the previous day · C. High and low of 5 days |
| K2 time filter | A. No filter (09:00-21:00 only as a supplement) | B. Filter decisive |
| K3 exit | B. Trailing stop 2 × ATR | A. Fixed target 2R |
| K4 direction of the control group | B. Same share of longs and shorts as the rule (decisive) | A. Coin flip 50/50 (supplement) |

## 4. The three fixed rules

**Costs.** 0.40 USD per ounce round trip (spread plus slippage), same as test F [assumption]. Sensitivity: 0, 0.40 and 0.80 USD. The median spread from the SPREAD column is reported only.

**Order.** The path runs per M30 bar from the bar after the entry. Within a bar the stop is the one set after the close of the previous bar; it only moves after the close of the bar. If the bar reaches the stop, exit at the stop. If a bar opens beyond the stop, exit at the open of that bar. There is no target, so the rule "stop and target in one bar counts as stop" does not occur.

**Control group.** 10,000 runs, seed 23. A random process that walks through time like the rule, one position at a time, as in test F v1.1:
- after every exit (or at the start) a waiting time, drawn from the rule's own waiting times in the same period;
- then entry on the close of the next H1 bar that is not the last of the broker day;
- stop distance drawn from the rule's own stop distances (20 quantiles, as a multiple of ATR, see 3.9);
- direction according to the null below;
- the same trailing stop (3.7, with the ATR on its own entry bar), day close, costs and path rules.

Compared is the mean net R per trade.
- **Null A, decisive:** every trade long with probability p, short with probability 1 − p, where p is the rule's share of longs in the same period. Tests the timing only.
- **Null B, supplement:** coin flip, long and short 50% each.

Order of looking: first the control group, then the rule.

## 5. Periods

| Run | Period | Role |
|---|---|---|
| P1 | Start of usable data (3.2) to 31 Dec 2024 | **Decisive**. Matches the source's backtest period (2004-2024) |
| P2 | 1 Jan 2025 to the last bar (5 Nov 2026) | Supplement: the period of the live claim (+105% in 2025) |
| P3 | per year | Distribution over the years, not decisive |

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the mean net R per trade in P1 is below 0 |
| C2 | The mean net R per trade in P1 is not above percentile 95 of Null A |
| C3 | No verdict; shown side by side only |

If C2 falls, the idea is dead: no repair, no optimisation, no other levels, filters, stops or exits. This also holds for the variants not chosen at K1 to K4. Fewer than 100 trades in P1: "insufficient trades".

If C1 and C2 stand, I report "not falsified", with the limitations, and not "works".

## 7. What I report, whatever the outcome

- Number of signals, how many drop out on the minimum stop, number of trades, share of longs.
- Win rate with interval, mean net R with day bootstrap (95%), profit factor.
- Percentile against Null A and Null B.
- Result per year, the three cost levels, median stop distance in USD against the costs.
- Longest losing streak, with how often the control group has an equally short or shorter one.
- Sum of the best 5% of trades next to the total.
- P2 next to the live claim; C3 next to 69%, 2.13 and 3.

## 8. Next step

1. Approved on 20 Nov. SHA-256 of the Dutch and English versions in `meetlog-sr-breakout.md`.
2. Measurement script `sr_breakout.py` first on 24 synthetic series: random walk with gold's volatility (15% per year), drift 0 and 8% per year, as in test F [assumption, chosen before seeing the data]. There, the rule must on average not come out better than Null A, and the percentiles must be roughly evenly spread. Only then the real data.
