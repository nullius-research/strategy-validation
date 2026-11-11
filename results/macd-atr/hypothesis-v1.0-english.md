# Hypothesis: MACD signals with ATR stop (1.5 ATR) and ATR target (1 ATR)

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.0-dutch.md`, approved on 6 November 2026 before the first run on real data (SHA-256 of the published Dutch file: ee6b6675a318ae7853890afa06fe6060d1e3e2de98d17ff5232e306795cba950). If the two differ, the Dutch text applies. Quotes from the source are in the original English, spelling included.

Date: 5 November 2026, revised 6 November 2026 (21 pairs) · Status: **version 1.0, approved on 6 November 2026 (ATR fixed from the signal bar, swap not included), before the first run on real data**

Source: an open-source strategy script on a charting platform (August 2020), the video in which the maker presents the outcome, and a public spreadsheet by the maker with win rates per pair and signal. Name and links are kept in the private project files (decision of 2 Nov 2026: no names in publications).

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing changes. If a choice turns out to be untenable, a new version with a new date follows, and this result stays.

## 1. What the source promises

[verified, video and script page] "we've hit the 90% WinRAte mark on the Euro New Zealand Dollar chart". Daily chart, "3 year period", "28 different graphs", five MACD signals. Stop 1.5 x ATR, target 1 x ATR.

[verified, transcript] "if it is over 60 [%] i am convinced that the strategy i am testing can be really profitable". Average win rate over 28 pairs: Reversal 59.57%, MACD Line zero cross 62.54%, Signal Line zero cross 64.25% ("our winner").

[verified, spreadsheet] EURNZD, MACD Line zero cross: 94.12%. Highest cell of 140 (28 pairs x 5 signals). Lowest cell 23.08%. The averages in the sheet are unweighted averages of the 28 win rates per pair.

[verified, arithmetic] 94.12% = 16/17. That the cell rests on 17 trades is [assumption]: 32/34 gives the same, but 34 zero crossings of the MACD line in 2.6 years of daily data is unlikely.

Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | EURNZD, MACD Line ZC: win rate 94.12% ("90%") | Win rate with 95% interval, same period and after |
| C2 | MACD Line ZC over 28 pairs: 62.54% | Win rate over all trades, with interval |
| C3 | Signal Line ZC over 28 pairs: 64.25%, the best | Same |
| C4 | Above 60% is "really profitable": the signals pick better moments than chance | Mean net R against a coin flip (Null A) |

## 2. Weak spots visible before the test

1. [verified, arithmetic] Target 1 ATR, stop 1.5 ATR. Break-even win rate before costs: 1.5 / (1 + 1.5) = **60%**. The source's threshold ("over 60 = convinced") is exactly break-even without costs.
2. [verified, mathematical: the chance of +a before -b in a driftless random walk is b/(a+b)] Without any predictive value, this stop and target already reach about **60%** win rate. The 62.54% and 64.25% are therefore just above it. Discrete daily bars, gaps and the rule "stop and target in one bar counts as stop" can lower that base level [assumption, measured on noise data].
3. [verified, binomial] With a true chance of 60%, the chance of 16 or more wins in 17 trades is 0.21%. But 94.12% is the maximum of 140 cells, often with fewer than 30 trades per cell [assumption about the counts]. The highest number from many small samples is high by itself. This is measured by repeating the 140 cells on noise data.
4. [verified, source code] The description says that 50% is taken at the target and the stop moves to break-even. **The code does not do that**: `strategy.exit` closes the whole position at the target or the stop. The win rates in the sheet therefore come from the code without scaling out [assumption: the sheet was made with this code; the video says so].
5. [verified, source code] `timeFilter = year > 2020 - 3`: trades only from 1 January 2018. The "3 years" up to publication (Aug 2020) is about 2.6 years.
6. [verified, source code] No commission, spread or slippage set. [assumption] By default the charting platform then charges zero costs.
7. [verified, source code] `strategy.entry` in the opposite direction reverses an open position. An opposite signal therefore also closes a trade. On the charting platform a trade counts as a win if it closes with a profit [assumption about the definition of "percent profitable"].
8. [assumption] What the charting platform does when target and stop fall in one daily bar depends on its assumption about the path within the bar. Here that counts as a stop (fixed rule), and the path is followed on H1.

## 3. Mechanical translation (fixed)

Everything below is **[assumption]**: choices made to turn the code into a measurement. Where the code fixes something, I follow the code.

**3.1 Instrument and timeframe.** Daily bars (D1) of 21 of the 28 pairs from the spreadsheet: EURGBP, EURAUD, EURNZD, EURUSD, EURCAD, EURCHF, GBPAUD, GBPNZD, GBPUSD, GBPCAD, GBPCHF, AUDUSD, NZDUSD, NZDCAD, NZDCHF, USDCHF, NZDJPY, CHFJPY, EURJPY, USDJPY, GBPJPY. Source: MT5 export (IC Markets EU, demo account).

Not included: AUDNZD, AUDCAD, AUDCHF, USDCAD, CADCHF, CADJPY, AUDJPY. On this server they only have data from 2 Jan 2025, also after a second export [verified, data check 5 and 6 Nov]. Decision of 6 Nov 2026, before the first run: continue with 21 pairs (option B). Every report names this as a limitation.

**3.2 Periods.**
- Period R (replication, not decisive): 1 Jan 2018 through 14 Aug 2020, the source's period according to the code.
- Period T (test, decisive): 15 Aug 2020 through the end of the export. The source has not seen this data.
- Indicators may warm up on data before the period.

**3.3 Indicators** (as in the code): MACD 12, 26, 9 with EMA on the close. ATR 14 according to Wilder (RMA of the true range), as `atr()` in the script.

**3.4 Signals** (as in the code, at the close of daily bar t):
- MACD Line ZC: long when MACD goes from ≤ 0 to > 0, short when MACD goes from ≥ 0 to < 0.
- Signal Line ZC: the same with the signal line.
- Continuation, Reversal, Histogram: as in the code, reported additionally, not decisive.
- `crossover(a, b)` = a(t) > b(t) and a(t-1) ≤ b(t-1). `crossunder` mirrored.

**3.5 Entry.** Open of daily bar t+1. [assumption: that is what the charting platform does by default with `strategy.entry` without `process_orders_on_close`]

**3.6 Stop and target.** ATR(14) on signal bar t, fixed for the whole trade. Stop 1.5 ATR, target 1 ATR from the entry price. Deviation from the code: in the script `strategy.exit` is called again on every bar with that bar's ATR, so the levels can shift [assumption about the script's behaviour]. A fixed ATR is unambiguous and common; the difference shows up in period R as a deviation from the sheet.

**3.7 Exit.** Target, stop, or an opposite signal (closes at the open of the next daily bar and opens the reverse trade, as in the code). A signal in the same direction as an open trade does nothing. No time limit. Open at the end of the data: close at the last close.

**3.8 One position per pair.**

**3.9 Win.** A trade counts as a win if the net outcome in R is greater than 0. R = the stop distance (1.5 ATR). A trade at the target is +0.667R minus costs.

## 4. The three fixed rules

**Costs.** 1.2 pips round trip per trade [verified, fixed assumption from earlier tests]. Sensitivity: 0, 1.2 and 3.0 pips (crosses such as GBPNZD have wider spreads [assumption]). Swap (overnight financing) is not included [assumption, a limitation stated in every report; trades often run several days].

**Order of events.** The path is followed bar by bar on H1, where H1 data exists. If one H1 bar hits both stop and target, it counts as a stop. Where only D1 exists: the same rule per daily bar. The share of trades without an H1 path is reported.

**Control groups.** 10,000 runs per control, seed 23. Bootstrap per trading day.
- **Null A, decisive (coin flip):** the same entry moments and ATR distances as the real trades, random direction, same stop, target and costs, same path. For FX the right null [verified, method].
- **Noise check in advance:** the script first on synthetic random-walk data (D1 and H1, 28 pairs, 9 years, 24 sets). There "dead" should come out, and there it is measured (a) which win rate this stop and target reach on noise and (b) how high the highest of 140 cells gets on noise.

## 5. Data

[verified, `datacontrole-export-1.md`] Export with `ExportFX_D1_H1.mq5`. The 21 pairs have D1 from Jan 2010 (GBPNZD from May 2010) and H1 from Jan 2015 (EURCHF from 19 Jan 2015). No duplicate or invalid bars; gaps longer than 4 days only before 2018.

## 6. When is the idea dead (in advance)

Decisive is period T, all 21 pairs together, per signal (MACD Line ZC and Signal Line ZC). The thresholds of C2 and C3 remain the source's averages over 28 pairs.

| Claim | Falsified if |
|---|---|
| C1 | The upper bound of the 95% interval of the win rate on EURNZD (MACD Line ZC, period T) is below 90%. Fewer than 100 trades: "insufficient", but reported |
| C2 | The upper bound of the 95% interval of the win rate (MACD Line ZC, period T, all pairs) is below 62.54% |
| C3 | Same for Signal Line ZC, below 64.25% |
| C4 | The mean net R (period T, all pairs) is not above percentile 95 of Null A. Tested per signal; dead if it holds for both signals |

C1 uses 90%, the number from the headline, not 94.12%, so the test is not stricter than the source.

If C4 falls, the system is dead: no repairs, no optimisation, no other ATR factors, signals or filters. The scaling out from the description is not added afterwards either; it was not in the code that produced the numbers.

## 7. What I report, whatever the outcome

Per signal and period: trades per pair, win rate with interval, mean net R with day bootstrap (95%), profit factor, percentile against Null A. The source's spreadsheet next to our period R per cell (105 cells: 21 pairs x 5 signals). Win rate on noise data next to the real one. The highest cell on noise next to 94.12%. The three cost levels. Share of trades without an H1 path. Result per year.

## 8. Next step

1. The document is approved or adjusted. After that it is fixed (SHA-256 in the measurement log).
2. Export done (5 and 6 Nov 2026).
3. Measurement script `macdatr_control.py` on noise data (28 synthetic pairs, so that the highest cell of 140 is comparable with the spreadsheet), only then the real data.
