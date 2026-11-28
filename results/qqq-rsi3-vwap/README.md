# RSI(3) + EMA(100) + rolling VWAP on QQQ: results

A strategy research website published this rule in a video (9 October 2026), a newsletter post (12 November 2026, edited 19 November) and a social media post. On QQQ from 1999 to September 2026 it reports 215 trades, a 78.6% win rate and a profit factor of 3.94 (video), or 215 trades and a profit factor of 3.54 "before costs" (newsletter). The video adds a maximum drawdown of about $10,943 at a fixed $100,000 per trade, a profit factor above 3 in each of three sub-periods, and that the EMA and VWAP filters raised the profit factor of RSI(3) alone (2.27 in the video, 2.19 in the newsletter). The results exclude commissions and slippage.

The hypothesis was written and fixed before any QQQ price data was opened: `hypothesis-v1.0-dutch.md` (binding; the reference to a private source file is removed, nothing else changed) and `hypothesis-v1.0-english.md`. One correction followed, before the run on real data: v1.1 changed only Null B, because the noise check showed it was biased. The binding version is v1.1 (`hypothesis-v1.1-dutch.md`; the English files are translations).

Two results matter more than any single number:

- The rule beat **every percentile** of random entry days in the same trend (Null A, percentile 100.0). Its profit factor and win rate are close to the claim.
- The two filters did **not** beat the same number of RSI(3) days picked at random (Null B, percentile 49.2). Random picks averaged +0.913% per trade, the rule +0.909%.

## Rule

| | |
|---|---|
| Script | `qqq-rsi3-vwap/qqq_rsi3_vwap_control.py` in the repository root. Needs numpy |
| Market | QQQ daily bars (open, high, low, close, volume) without dividend adjustment, Yahoo Finance. Sensitivity: dividend-adjusted prices |
| Signal, on the close of day t | RSI(3) below 22, the 100-day EMA higher than five trading days earlier, and the close at least 1% below the 10-day rolling VWAP |
| RSI | Wilder's RSI, period 3. The source does not say which RSI it used; Cutler's RSI as sensitivity |
| EMA | 100 days, alpha 2/101, seeded with the simple mean of the first 100 closes |
| Rolling VWAP | Sum of typical price (high + low + close) / 3 times volume over the last 10 days, divided by the sum of volume |
| Entry | Open of day t+1 |
| Exit | Close of the first day from the day after the entry day on which RSI(3) is above 55 ("Starting the session after entry"). No stop, no target, no time limit. Exit already on the entry day as sensitivity |
| Positions | One at a time; a signal during an open trade is dropped; a signal on the exit day counts |
| Costs | 2 basis points round trip, assumed. Sensitivity at 0, 4 and 10 bp |
| Warm-up | Signals from trading day 105 (6 August 1999) |
| Run | Run 1 of 1, 28 November 2026 |

The prices are not in this repository. Series used: QQQ from Yahoo Finance, 10 March 1999 to 27 November 2026, 6,974 days; SPY from Yahoo Finance, 29 January 1993 to 27 November 2026, 8,516 days. `make_csv.py` converts the Yahoo chart response and checks the series without printing prices (`data_check_qqq.txt`, `data_check_spy.txt`: no missing values, no zero volume, one gap in September 2001, a 2:1 split in March 2000).

## Self-test and noise check first

Self-test (`selftest.txt`, passed): EMA, Wilder and Cutler RSI, rolling VWAP on a constant price and on a hand-weighted case, no exit on the entry day, a trade still open at the end, a signal on the exit day counts and a signal inside a trade is dropped.

24 fake markets (6,950 days each, random walk with drift 0.04% and volatility 1.8% a day, random open, high, low and volume), 2,000 control runs per set. Threshold: mean percentile between 35 and 65, at most 3 of 24 above 95, for both controls.

| | v1.0 (`noise_24sets_v1.0.txt`) | v1.1 (`noise_24sets_v1.1.txt`) |
|---|---|---|
| Against Null A | 59.3, 1 of 24 above 95: passed | 61.5, 2 of 24: passed |
| Against Null B | 0.0: **failed** | 51.8, 2 of 24: passed |

Why Null B failed in v1.0: it drew random RSI days in random order and refused a trade that overlapped one already drawn. Long trades overlap more often, and without a stop long trades are often losers. So the control kept mostly short winners, and the rule would always have looked worse than it. v1.1 makes Null B a sequential process like the rule itself: each RSI(3) < 22 day becomes a fake signal with probability p, then the rule's own handling and exit; p is set so the mean number of trades equals the rule's. On noise, Null A leans slightly towards the rule (61.5 instead of 50), within the threshold.

## Control first (10,000 runs, seed 38)

Null A (decisive for "better than chance in the same trend"): random signal days among the days on which the EMA is higher than five days earlier, entry at the next open, as many trades as the rule, one at a time, each with the duration of a real trade (shuffled).
Null B (decisive for "the filters improve RSI(3)"): the sequential process above, over the days with RSI(3) < 22, without the EMA and VWAP filters.

| | Mean net return per trade, 5 / 50 / 95 | Rule's percentile |
|---|---|---|
| The rule | +0.909% | |
| Null A | −0.078% / +0.175% / +0.420% | **100.0** |
| Null B | +0.683% / +0.913% / +1.144% (214.8 trades per run) | **49.2** |

## Result, QQQ, 10 March 1999 to 27 November 2026 (decisive)

| | Measured | Claimed |
|---|---|---|
| Trades | 216 (215 up to 30 September 2026) | 215 |
| Win rate | 79.2% (95% Wilson: 73.3% to 84.0%) | 78.6% |
| Profit factor after costs | **3.43** (95% bootstrap: 2.26 to 5.74); before costs 3.51; up to 30 September 2026 before costs 3.50 | 3.94 (video), 3.54 before costs (newsletter) |
| Mean net return per trade | +0.909% (95%: +0.646% to +1.171%) | |
| Drawdown at $100,000 per trade | $9,155 | about $10,943 |
| Worst trade | −9.15% | |
| Lowest daily low during a trade | −19.73% below the entry price | |
| Mean duration | 3.57 days after the entry day; 14.4% of days in the market | |
| Funnel | 6,869 days, 925 with RSI(3) < 22, 503 with the EMA filter, 441 signals, 225 dropped during a trade | |
| Buy and hold, same period | +1,174.9% (price only) | |

## Checks set in advance

| Claim | Falsified if | Measured | Verdict |
|---|---|---|---|
| C1 profit factor 3.94 (or 3.54) | upper bound of the 95% interval below the claim | 3.43 (2.26 to 5.74) | Not falsified |
| C2 win rate 78.6% | upper bound of the 95% interval below 78.6% | 79.2% (73.3 to 84.0) | Not falsified |
| C3 drawdown about $10,943 | descriptive | $9,155 | |
| C4 profit factor above 3 in each sub-period | descriptive, every period below 100 trades | 4.09 (66 trades), 3.68 (82), 2.62 (67) | Insufficient |
| C5 better than chance in the same trend | not above percentile 95 of Null A | 100.0 | Not falsified |
| C6 the filters improve RSI(3) alone | not above percentile 95 of Null B | 49.2 | **Falsified** |

## Periods and sensitivity

| Run | Trades | Win rate | Mean net | PF net | Null A | Null B |
|---|---|---|---|---|---|---|
| P1 1999 to 27 Nov 2026 (`run01_P1.txt`) | 216 | 79.2% | +0.909% | 3.43 | 100.0 | 49.2 |
| P0 to 30 Sep 2026 (`run01_P0.txt`) | 215 | 79.1% | +0.909% | 3.42 | 100.0 | 47.6 |
| P2 1999 to 2008 (`run01_P2a.txt`) | 66 | 74.2% | +1.148% | 4.09 | 99.9 | 38.5 |
| P2 2009 to 2017 (`run01_P2b.txt`) | 82 | 85.4% | +0.877% | 3.68 | 100.0 | 64.6 |
| P2 2018 to Sep 2026 (`run01_P2c.txt`) | 67 | 76.1% | +0.713% | 2.62 | 96.1 | 59.9 |
| P4 Oct to 27 Nov 2026, after the source (`run01_P4.txt`) | 1 | 1 of 1 | +0.905% | | | |
| P3 SPY 1993 to 27 Nov 2026, same rules (`run01_P3_spy.txt`) | 238 | 76.5% | +0.659% | 2.97 | 100.0 | 78.6 |
| P1, 4 bp (`sens_P1_cost4.txt`) | 216 | 78.7% | +0.889% | 3.35 | 100.0 | 49.2 |
| P1, 10 bp (`sens_P1_cost10.txt`) | 216 | 77.8% | +0.829% | 3.12 | 100.0 | 49.2 |
| P1, dividend-adjusted (`sens_P1_adjclose.txt`) | 220 | 78.2% | +0.862% | 3.16 | 100.0 | 37.1 |
| P0, 0 bp, Cutler RSI (`sens_P0_cutler_gross.txt`) | 231 | 73.2% | +0.666% | 2.51 | 100.0 | 72.1 |
| P0, 0 bp, exit possible on the entry day (`sens_P0_fc0_gross.txt`) | 218 | 79.8% | +0.937% | 3.63 | 100.0 | 50.7 |

No variant puts the rule above percentile 95 of Null B.

Supplementary, descriptive, not in the hypothesis (`rsi3_alone.py`, `rsi3_alone.txt`): RSI(3) < 22 alone, every signal, same entry and exit, up to 30 September 2026: 334 trades, +0.70% per trade, profit factor 2.03 before costs (the source reports 2.27 and 2.19). Picking about 215 of these days at random already gives about +0.92% per trade (Null B median). Why fewer trades helps was not measured; one possibility is that a thinned set enters later in a decline on average.

## What this does and does not say

- It measures one reading of the published rule on one data source. The trade count up to September 2026 matches the source exactly (215), which suggests the reading is close.
- The source tested on the same history it published. There is no QQQ period it could not see apart from October and November 2026 (1 trade).
- Without a stop, the risk sits in the open trades: one trade fell almost 20% below its entry at the lowest point before it was closed.
- This is the fourth long-only mean-reversion rule on a US index in this project, after Buy the Dip, RSI(2) pullback and Triple RSI. The results are not independent.
- Null A leans slightly towards the rule on noise; C5 may be slightly lenient.

This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgment.
