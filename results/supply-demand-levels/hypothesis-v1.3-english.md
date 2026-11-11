# Hypothesis: supply-demand levels on a volume profile

> **English translation, made on 11 November 2026, after the run.** The binding version is the Dutch original in this folder, `hypothesis-v1.3-dutch.md`, version 1.3 of 2 November 2026, fixed before any real outcomes were looked at (SHA-256 of the published Dutch file: 68471fb24c01ccf578abacdc0c27cef980073bba4d7d3683c693373635be899c). If the two differ, the Dutch text applies.

Date: 29 October 2026 · Source: public document from a provider of a trading course · Status: **fixed in advance, version 1.3, no real outcomes looked at yet** (changes in section 9)

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice made in the measurement

Ground rule: everything below is fixed before the first run. After the run nothing is changed. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 1. What the document promises

[verified] The document makes these testable claims (summarised in my own words):

| # | Claim | Testable as |
|---|---|---|
| C1 | Random long or short at every level, 1:1, gives about 50% wins and therefore break-even. It calls this the "floor". | Coin flip on the same levels, with costs |
| C2 | With the A+ filter (trend, structure, momentum) the win rate rises to 60–80%. | Win rate filtered against unfiltered |
| C3 | Return of 5–10R per month. | Net R per calendar month |
| C4 | At these volume levels price *must* react; they do not expire. | Reaction at real levels against fake levels with the same spacing |
| C5 | The two-strike rule (stop after 1 win or 2 losses) improves the result. | Same system with and without the daily rule |

[verified] Not testable and therefore outside this measurement: "600+ traders make money with it", "used myself for 3+ years", the testimonials and screenshots of payouts.

## 2. Weak spots visible before the test

1. [verified, arithmetic] C1 ignores costs. At 50% wins and 1:1 the result is not 0 but minus the costs per trade. The "floor" is below zero.
2. [verified] The document is internally inconsistent about the risk-reward. It calculates with 1:1, but the described stop ("roughly in the middle of your two surrounding levels") with the next level as target gives something closer to 2:1. With an entry *at* a level, "the middle of the two surrounding levels" is moreover the level itself. See choice 3.6.
3. [verified] Core concepts are not defined mechanically: which "cloud" (periods missing), when structure is "softer", what counts as "rejection on both sides". Every translation into rules is therefore my choice. The maker can always say "that is not what I mean". That is why all choices are explicit below, and they count as fixed.
4. [assumption] A volume profile on a CFD measures tick volume, not real traded volume. The argument "that is where the institutional money sits" only holds with real futures volume. See the data choice in section 5.

## 3. Mechanical translation (fixed)

All points below are **[assumption]**: they are my choices to translate discretionary text into rules. Where the document gives a number, it is stated.

**3.1 Instrument and time.** ES (S&P 500 future), the example from the document. Regular session only, 9:30–16:00 ET. Signals on 5-minute bars. Anything still open at 16:00 is closed at the close.

**3.2 Levels.**
- VRVP: volume profile over the 20 preceding sessions, 200 rows (number from the document).
- SVP: a profile of 100 rows per session (number from the document), giving the Point of Control.
- A level is a high-volume node (local maximum in the VRVP, in the top 20% of all rows) with a POC of one of the 20 preceding sessions within 5 points.
- Rejection on both sides: within those 20 sessions the zone was touched at least once from above and once from below, each time followed by a move of at least 10 points away from the zone within 12 bars.
- Zone = 8 points wide, centred on the node (document: 7–10).
- Levels are set before 9:30 using only data from earlier sessions. No look-ahead.

**3.3 Trend ("cloud").** EMA 34/50 cloud on 5 minutes and 1 hour (the document names both timeframes, not the periods). Bullish if on both timeframes EMA34 > EMA50 and EMA50 is higher than 6 bars earlier. Bearish the other way round. Otherwise "flat": no trading.

**3.4 Structure.** Swing points with a fractal of 2 bars left and right on 5 minutes. Bullish if the last two swing highs and swing lows are both higher. Bearish the other way round. Otherwise no trade.

**3.5 Momentum.** In the last 6 bars price touched the 5m cloud and the last bar closed back on the trend side of the cloud.

**3.6 Entry, stop, target.**
- Long: price comes into a zone from above, trend and structure bullish, momentum confirmed. Short: mirror image at a zone touched from below.
- Entry at the close of the first 5m bar in the zone on which all filters hold.
- Stop: halfway between this level and the next level *behind* the trade.
- Target: the next level *ahead of* the trade.
- Stop to break-even once price has covered 50% of the distance to the target (from the document).
- If there is no next level (off the map), no trade.

**3.7 Daily rules.** Stop after 1 win or after 2 losses (A+ checklist). Base variant without an extra limit. The variant "1 trade per day" (the "week 5+" phase from the document) is reported separately, not as a replacement.

## 4. The three fixed rules

**Costs.** [assumption] 1 tick of slippage per side (0.25 point = $12.50) plus $4.50 commission per round trip per contract. [verified, arithmetic] With a stop of 12.5 points ($625) that is about 0.05R per trade. Sensitivity: 0, 1 and 2 ticks per side.

**Order of events.** Bar by bar on 1-minute data where available. If one bar hits both stop and target, it counts as a stop. The break-even shift only applies from the bar *after* the bar in which 50% was reached.

**Control groups.** 10,000 runs per control, seed 19.
- **Null A, decisive for C2:** the same level touches, *without* the filter, direction by coin flip, same stop, target and break-even rules, same daily rules, same costs. This is exactly the "floor" from the document, so it is also the test of C1.
- **Null B, decisive for C4:** fake levels. That day's real level map is shifted as a whole by a random amount between 5 and 15 points (up or down). Same spacing, same filters, same rules. Tests whether the volume levels add anything compared with random lines with the same rhythm.
- **Null C, additional:** same days and filter state, entry at a random moment at which the filters also held but without a level, same stop distance in points. Tests whether "being at the level" matters.

## 5. Data: the choice is yours

| | A. MT5 broker data US500 (CFD) | B. ES futures 1m with real volume (paid source) | C. SPY 5m via Yahoo |
|---|---|---|---|
| Costs | Free [assumption] | Paid, price not checked [assumption] | Free [verified, TSLA test] |
| Period | Several years of M1 [assumption, differs per broker] | Several years [assumption] | About 60 days [verified, TSLA test: 59 sessions] |
| Volume | Tick volume, not the "institutional" volume [assumption] | Real traded volume, fits the claim | Real volume of the ETF, but a different instrument |
| Faithful to the document | Weak on levels, good on price | Highest | Moderate (SPY, not ES; rescale points) |
| Enough trades (≥100)? | Yes with ≥2 years [assumption] | Yes with ≥2 years [assumption] | No, at most ~60 with 1 trade/day [verified, arithmetic] |
| Usable as | Full test, with a caveat on C4 | Full test, strongest publication | Only a pilot to test the script |

[assumption] My estimate: C as a pilot for the script, then B as the publishable measurement. A is a reasonable alternative if B turns out too expensive, but then C4 cannot be established firmly.

Minimum: 2 full years, all years reported, not a single parameter chosen on the basis of the outcome.

## 6. When is the idea dead (in advance)

| Claim | Falsified if |
|---|---|
| C1 | Null A mean net R clearly below 0 (90% bootstrap interval entirely negative). Then the "floor" is not break-even. |
| C2 | Real result (mean net R) not above percentile 95 of Null A, *or* filtered win rate below 60%. |
| C3 | Median net R per month below 5. |
| C4 | Real result not above percentile 95 of Null B. |
| C5 | The variant without the daily rule has an equal or higher mean net R per trade. |

If C2 and C4 both fall, the system is dead according to step 5: no repairs, no optimisation.

## 7. What I report, whatever the outcome

Number of trades, win rate, mean net R with day bootstrap (90%), percentile against Null A, B and C, net R per month (distribution, not only the mean), result per year, share of the best 5% of trades in the total, and the three cost levels.

## 8. Next step

Measurement script `levels_control.py` (levels, filters, Null A/B/C, costs, bar by bar), first run on the pilot data (option C) to check the script, not yet to draw conclusions.

## 9. Changes before the first real run

The text above stays as it was fixed. What follows replaces the points concerned. No real market data was looked at for any of these changes.

### Version 1.1 · 29-10-2026 · data choice

- Chosen: **option A, MT5 broker data US500, M1**. With that, C4 cannot be established firmly from the start: the profile measures tick volume, not real traded volume [assumption, see section 2 point 4]. A C4 outcome is reported that way too.
- The pilot (option C) is dropped. Instead the script was checked on synthetic data, see 1.2.
- Costs: the spread comes per bar from the SPREAD column of the export [verified that the script uses that column], plus 1 tick (0.25 point) of slippage per side. Sensitivity 0, 1 and 2 ticks. No commission [assumption: CFD broker without commission; if your broker does charge one, it must be added].
- Session: 16:30–23:00 server time [assumption: broker with server time equal to New York + 7 hours]. The script checks this itself against the jump in tick volume at the open and reports how many days match.
- Prices are bid. The spread is deducted once per trade as costs, also for shorts. The path of a short is checked on bid, not on ask [assumption, a small optimistic deviation for shorts].

Details that were not explicit in version 1, now fixed:
- The volume of an M1 bar is spread evenly over the rows the bar touches. VRVP and POC from RTH bars only.
- Local maximum = greater than or equal to all rows within ±2.
- EMA cloud and swing points on all hours (as a chart shows them), hourly trend from the last completed hourly bar.
- Rejection window: the 12 bars *after* the touch bar, within the same session.
- The daily rule counts wins and losses on the gross result. A break-even exit counts as neither.
- One candidate per zone visit. If a position is still open, that visit is dropped.
- Null B: shifts in steps of 0.25 point (5.00 to 15.00, up or down).
- Null C: per real trade a random replacement on the same day, without daily rules.

### Version 1.2 · 29-10-2026 · errors found on synthetic data

The script was run on four sets of artificial random-walk data of 2 years (no predictability at all, so every "result" is noise). Two errors in my design came to light:

1. [verified] **No minimum stop distance.** The entry at the close could be just above the stop. Trades with less than 1 point of risk lost 4.2R on average, purely through costs. New rule: no trade if entry to stop is smaller than 4 points. Basis in the document: the stop must not be so tight that ordinary noise takes you out. Applies to the real trades and all control groups.
2. [verified] **Null A did not have the same number of trades.** The real system (16 trades) was compared with a band of coin-flip runs with hundreds of trades. On pure noise that gave percentile 96.7, so a false "edge". Null A has therefore been split:
   - **Null A0 (the floor, for C1):** coin flip on all level touches, with daily rules, as in version 1.
   - **Null A (decisive for C2):** per day exactly as many trades as the real system took that day, chosen at random from that day's valid level touches, random direction.
3. Extra reporting rule: below 100 trades the report says "insufficient trades". The criteria from section 6 are still applied, but the outcome counts as not decisive.

[verified] Check after the changes: on all four noise sets the script judged "dead", with percentiles against Null A between 8 and 90. The gross result of the coin flip was -0.01 point per trade (standard error 0.28), so the stop-first rule gives no noticeable skew. The floor fell below zero only because of costs.

[verified] Warning in advance: on noise data the filter gave only 13 to 21 trades in 2 years. Whether the real market gives many more is unknown [assumption]. If the real run comes out below 100, the agreement now is: as many extra years of data as the broker provides, with the same rules, and not a single rule change.

### Version 1.3 · 02-11-2026 · period and costs after the data check

Only the metadata of the export was looked at (bars per day, SPREAD column), not a single outcome of the system or the control groups. See `datacontrole-us500-m1.md`.

- Data: export US500 M1 from IC Markets EU (demo account), made on 2 November 2026 (`US500_M1_201208060000_202611021049.csv`).
- **Period: 1 January 2019 through 30 October 2026** (chosen before the run, option A). Reason: before 21 March 2017 the file contains only daily bars, and in 2017 and 2018 the SPREAD column is (almost) empty [verified]. With those years included, the system would trade there almost without costs. 2 November 2026 is a running day and drops out.
- **Commission: 0.** [verified] The IC Markets (CySEC) indices product sheet gives no commission for US500, only an average spread of 0.36 point. [assumption] The commission of $3.50 per lot per side on the IC Markets site applies to forex on a Raw account, not to index CFDs. For comparison: the median spread in the export is 0.50 point [verified], so the costs from the column are higher rather than lower than the average the broker states.
- **Method:** the script stays unchanged. The file is filtered in advance to the period above (`US500_M1_2019-2026.csv`), then it goes through `levels_control.py` with the same arguments.
