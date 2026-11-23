# Hypothesis: morning star with a trend filter on gold, with a prop firm challenge (test Q), version 1.0

English translation. The Dutch original `hypothese-morning-star-goud.md` (version 1.0, 21 November 2026, SHA-256 in the measurement log) is binding. Names of the source and of the prop firm are kept in private files; the firm is called "firm A" here.

Date: 21 November 2026 · Source: a short social media video of 7 November 2026 · Status: **version 1.0, 21 November 2026. Choices K1-A, K2-A, K3-A and K4-A approved on 21 Nov; text approved on 21 Nov. Firm A's rules checked on its own website on 21 Nov (section 6). No price data looked at for this test yet.**

Legend: **[verified]** = checked or calculated myself · **[assumption]** = not checked myself, or a choice in the measurement

Rule of play: everything below is fixed before the first run. Nothing changes after the run. If a choice turns out to be untenable, a new version with a new date follows, and this result stays as it is.

## 0. Not blind to this market

[verified, log] The same gold export (XAUUSD M30) was used in test F (MA 9/21 + 200 MA, rejected, percentile 63.9) and test P (support and resistance breakout, C2 rejected, percentile 91.2). So I know the rough path of gold in this period, including the strong rise in 2025. New here: the candle pattern (morning star and evening star), MA 14 and MA 200 as a filter, a fixed 2R target, and the prop firm challenge with risk as a percentage of the account. I have not seen those numbers. Every publication says this.

## 1. What the source claims

[verified, caption read on 21 Nov 2026] Rules in words:
- gold (XAUUSD), 1 hour;
- long: price is above the 14 and the 200 "moving average";
- the candles form a morning star: "a falling candle, a small candle, then a strong rising candle";
- buy "when the price goes higher than the third candle";
- stop at the lowest point of the three candles, target 2 × the risk;
- short: everything mirrored (evening star below both MAs);
- 1% risk per trade, "$1,000 on a $100K account".

[verified, caption] The source's numbers: "In 5 years of gold, it took 512 trades and 43% won", average win about 2 × average loss, worst day -3.6%, maximum drawdown 7.5%. 81% of 1,000 simulated challenges of firm A passed, about 1 in 8 failed, the rest did not finish within a year, median 155 days to pass, longest run 7 targets in a row.

[verified] Not stated: type of MA (simple or exponential), when a candle is "small" or "strong", how long the buy order stays valid, costs, whether "passed" means one phase or both, and how the 1,000 challenges were drawn.

Testable claims:

| # | Claim | Testable as |
|---|---|---|
| C1 | The rule makes money after costs | Average net R per trade with 95% interval |
| C2 | The pattern picks better moments than chance within the same trend | Real result against Null A (same trend filter, no pattern) |
| C3 | 512 trades in 5 years, 43% won, max drawdown 7.5% | Descriptive only, next to our measurement (rebuild, see 2.1) |
| C4 | 81% of challenges passed | Pass rate in our simulation (section 6), with 95% interval |
| C5 | That pass rate comes from the rule, not from the challenge itself | Descriptive only: the same simulation with the trades of Null A (as in test O v1.1) |

## 2. Weak points, named in advance

1. [verified] We test a public translation of the caption, fixed in advance, not the source's code (available only with an account, which we chose not to create). A result different from 43% or 512 trades can come from our translation. That is why C3 is descriptive only, and every publication says it is a rebuild (as in tests J and P).
2. [assumption] A fixed 2R target with 43% wins gives +0.29R per trade before costs. Small differences in win rate matter a lot here: at 2R break-even is about 33% before costs [verified, arithmetic].
3. [assumption] A pass rate depends strongly on the challenge rules and the position size. Hence C5.
4. [verified, own simulation 21 Nov] For independent trades with 43% wins and 2R/-1R, the median longest winning run over 512 trades is 7 (consistent with the claim), and the median maximum drawdown is about 13.5R. A drawdown of 7.5% at 1% risk is possible if the dollar risk stays fixed while the account grows [assumption about how the source calculates]. No verdict in advance.
5. [assumption] Broker time is probably GMT+2 or GMT+3. H1 bars and trading days are in broker time. Firm A's daily limit is in its own time zone (CE(S)T); I ignore the difference of 1 to 2 hours.

## 3. Mechanical translation

All points below are **[assumption]**: choices to turn the text into rules.

**3.1 Data.** The same MT5 export of XAUUSD M30 as tests F and P, SHA-256 c7d40c32a3d53f7ccfcc199b51d910daccaeafc2e6f996a0a9e1925aa684d7d2 (checked again before the run). H1 bars are built from the M30 bars per broker hour. Each trade's path is walked on M30.

**3.2 Usable data.** Same completeness check as tests F and P: the measurement starts in the first calendar month in which every trading day has at least 40 M30 bars. Warm-up: the first 200 H1 bars after that start do not count (MA 200).

**3.3 MAs (K1).** On H1 closes, value of the closed bar.

**3.4 Pattern on H1 bars t−2, t−1, t (K2).** Body = |close − open|.
- Morning star: candle t−2 falling (close < open); body t−1 ≤ 1/3 of body t−2; candle t rising (close > open) and close(t) > middle of the body of t−2. No gap required (gold trades almost continuously).
- Evening star: mirrored (t−2 rising, t−1 small, t falling with close below the middle of the body of t−2).
- Trend filter on the close of t: long only if close(t) > MA14 and close(t) > MA200; short only if close(t) < MA14 and close(t) < MA200.

**3.5 Entry (K3).** Long: buy stop at the high of candle t. Short: sell stop at the low of candle t. The order is valid only in H1 bar t+1 (walked on M30). If an M30 bar already opens beyond the level, entry at that open. Not reached: no trade.

**3.6 Stop and target.** Long: stop at the lowest low of t−2, t−1 and t; target at entry + 2 × (entry − stop). Short mirrored. Minimum stop 1.00 USD, as in tests F and P; a smaller stop means no trade. No time limit and no end-of-day exit: the trade runs to stop or target (the source names no other exit).

**3.7 One position at a time.** A signal during an open trade is dropped.

**3.8 Win rate** = share of trades with net R > 0 (after costs). R = net result in USD per ounce divided by the stop distance from the actual entry.

**3.9 Details for the script (21 Nov, after approval, before looking at data).**
- In the M30 bar of entry only the stop counts (if that bar touches the stop after entry, it is a loss); the target counts from the next M30 bar. This works against the rule, like "stop and target in one bar = stop".
- ATR(14) by Wilder on H1, value of the closed bar; used only for the control group's stop distance.
- Trading day and "start of day" in the challenge: broker date (see 2.5).
- Maximum drawdown in % (C3): over P1 with a fixed risk of $1,000 on $100,000 without compounding, measured on closed balance against the highest level before.
- If a trade is held over a weekend or holiday, the first open after it applies (rule "opens beyond the stop or target").

### Choices made (21 Nov 2026)

| | Chosen (decisive) | Not chosen (reported as a supplement only, never tried as a repair after the run) | Why |
|---|---|---|---|
| K1 type of MA | A. Simple (SMA 14 and SMA 200) | B. Exponential (EMA 14 and EMA 200) | "Moving average" without a qualifier usually means simple; SMA is the default in MT5 and TradingView [assumption] |
| K2 pattern | A. Classic: middle body ≤ 1/3 of candle 1, candle 3 closes above the middle of candle 1 | B. Loose: middle body < body of candle 1, candle 3 closes above the open of candle 2 | Common textbook definition [assumption] |
| K3 order validity | A. Next H1 bar only | B. Until the stop is hit first, at most 5 H1 bars | "When the price goes higher than the third candle" reads as immediate [assumption] |
| K4 what counts as passed | A. Both phases (10%, then 5%), as firm A means "passed" | B. Phase 1 only (10%) | Only after phase 2 do you get an account [assumption about what the source means] |

## 4. The three fixed rules

**Costs.** 0.40 USD per ounce round trip (spread plus slippage), as in tests F and P [assumption]. Sensitivity: 0, 0.40 and 0.80 USD. The median spread from the SPREAD column is reported only.

**Order.** The path runs per M30 bar from entry. If a bar touches stop and target together, it counts as a stop. If a bar opens beyond the stop or target, exit at that open. In the entry bar, see 3.9.

**Control group.** 10,000 runs, seed 31. A random sequential process, one position at a time, as in tests F and P:
- after each exit (or at the start) a waiting time in H1 bars, drawn from the rule's own waiting times in the same period;
- then entry at the open of the first H1 bar whose previous bar meets the null's filter;
- stop distance drawn from the rule's stop distances (20 quantiles, as a multiple of ATR(14) H1 on the entry bar), target 2R; stop smaller than 1.00 USD: no trade;
- the same costs and path rules.

Compared: average net R per trade.
- **Null A, decisive:** the trend filter of 3.4 only, without the pattern. Close above both MAs: long; below both: short; otherwise no entry. Tests whether the pattern adds anything on top of the trend.
- **Null B, supplementary:** coin flip, long and short 50% each, no filter.

Order of looking: control group first, then the rule.

## 5. Periods

| Run | Period | Role |
|---|---|---|
| P1 | 6 Nov 2021 to the last bar (5 Nov 2026) | **Decisive**. The source's "5 years of gold" [assumption: the source ends around the reel of 7 Nov 2026] |
| P0 | Start of usable data (3.2) to 5 Nov 2021 | Supplementary: the same rule before the claim's period |
| P3 | per year | Spread over the years, not decisive |

## 6. The prop firm simulation (fixed)

[verified, firm A's own website, 21 Nov 2026] Rules of the standard two-phase challenge, $100,000 account: target phase 1 10%, phase 2 5%, reached with all positions closed; maximum daily loss 5% of initial capital below the balance at the start of the day (day 1: initial capital), on equity including open loss; maximum loss fixed at $90,000, on equity; at least 4 trading days per phase, a trading day being a day (CE(S)T) on which at least one position is opened. The page names no time limit [verified]; other pages of the firm say "unlimited" [verified].

[assumption, translation into code]
- **Position:** risk 1% of the starting balance ($1,000) per trade, as the source says. Ounces = 1,000 / stop distance. Costs per trade = ounces × 0.40 USD.
- **Daily loss:** failed as soon as the balance including open loss (lowest price per M30 bar for longs, highest for shorts) falls $5,000 below the balance at the start of the trading day.
- **Maximum loss:** failed as soon as the balance including open loss falls below $90,000.
- **Target:** a phase is passed at the first moment the closed balance reaches the target and there are at least 4 trading days with an entry in that phase. Phase 2 then starts with a new $100,000 account on the next trading day (K4-A).
- **Draw:** 1,000 challenges, start day drawn at random from the trading days of P1 (seed 31), with the rule's trades from that day. A challenge still running after 1 year (365 calendar days) or at the end of the data counts as "not finished", as in the source. Start days in the last year of P1 are excluded.
- **Pass rate** = passed / 1,000, with 95% interval (Wilson, noting that overlapping draws are not independent). Also: failed, not finished, median time to pass.
- **C5 (descriptive):** the same simulation with trades of Null A, 2,000 runs.
- No entry fee, no payout rules.

## 7. When is the idea dead (in advance)

| Claim | Rejected if |
|---|---|
| C1 | The upper bound of the 95% interval (day bootstrap) of the average net R per trade in P1 is below 0 |
| C2 | The average net R per trade in P1 is not above percentile 95 of Null A |
| C3 | No verdict; shown side by side only |
| C4 | The upper bound of the 95% interval of the pass rate is below 81% |
| C5 | No verdict; descriptive only |

If C2 falls, the idea is dead: no repair, no optimisation, no other MAs, pattern definitions, filters or targets. This also applies to the variants not chosen at K1 to K4. Fewer than 100 trades in P1: "insufficient trades".

If C1 and C2 stand, I report "not rejected", with the limitations, and not "works".

## 8. What I report, whatever the outcome

- Number of patterns, how many inside the trend filter, how many orders filled, how many dropped by the minimum stop, number of trades, share long.
- Win rate with interval, average net R with day bootstrap (95%), profit factor.
- Percentile against Null A and Null B.
- Result per year, the three cost levels, median stop distance in USD against the costs.
- Longest winning and losing run; maximum drawdown in R and in % at 1% fixed risk.
- Pass rate, failed, not finished, median time, next to 81%, 1 in 8 and 155 days.
- P0 next to P1; C3 next to 512 trades, 43% and 7.5%.

## 9. Noise check before the real data (fixed)

24 synthetic series: random walk with gold's volatility (15% per year), drift 0 and 8% per year, with 60 steps per M30 bar (as in test P) [assumption, chosen before seeing the data]. Required: average percentile against Null A between 35 and 65, at most 3 of 24 above 95. If the script fails this, first find the cause and write a new version of this document, before the real data.

## 10. Next step

1. Approved on 21 Nov (K1 to K4 = A). SHA-256 of the Dutch and English versions in the measurement log.
2. Firm A's rules checked on 21 Nov (see 6).
3. Script: self-test (pattern against a second implementation, challenge against a hand calculation), noise check, data check, then run 01.
