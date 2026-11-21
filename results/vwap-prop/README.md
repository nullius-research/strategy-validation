# 9 EMA + VWAP and a prop firm challenge, Nasdaq 100 5 minutes: results

The rule comes from a viral Instagram reel (16 November 2026). The caption claims "an 85% prop firm pass rate". The reel shows a backtest screen of a strategy platform for the 5-minute chart: win rate 56.6%, profit factor 1.84, 396 trades. A post by the same maker a day later speaks of "backtest results over the last 3 years" and a prop firm pass rate of 84%. The rule, as spoken in the reel: long when the EMA 9 crosses above the VWAP, enter when a candle closes above the EMA, exit when a candle closes back below the EMA.

## Note added 21 November 2026: opening time

The script took the opening minute (9:30 New York) from the largest jump in tick volume at 15:30, 16:30 or 17:30 server time. The server runs on New York time + 7 all year, so the opening is always 16:30. On days with economic releases at 8:30 New York the script picked 15:30, one hour too early. We reran the test with the opening fixed at 16:30, same data and seed. The original script reproduces the published numbers exactly. The verdict does not change. With the fixed opening, regular session: 797 trades (was 799), win rate 32.2% (95%: 29.1 to 35.6; was 32.5%) against 56.6% claimed, PF 0.91 (was 0.89), −1.68 point per trade (was −2.03), percentile 71.0 against random entries (was 65.0). Challenge attempts in sequence: 9 of 92 passed, 9.8% (95%: 5.2 to 17.6; was 9 of 95, 9.5%) against 85% claimed; random entries 9.4%. The full-session variant does not depend on the opening and is unchanged. Old and new output: [`results/audit-opening-2026-11-21/`](../audit-opening-2026-11-21/). This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgement.

The reel does not name the prop firm or its rules. The platform's own changelog lists the challenge rules of five well-known firms. This test uses the 50K evaluation of one large futures prop firm (firm A) as decisive and a 25K evaluation of a second firm (firm B) as supplementary. The firms are not named here; their rules are in the hypothesis, as published in their help centres in September and October 2026.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (binding), with an English version written at the same time. The noise check of v1.0 failed for one claim (C5, see below), so version 1.1 was written before the real data was opened: C5 became descriptive. Nothing else changed. The published files differ from the internal ones only in the names of the two firms (replaced by firm A and firm B), the links to their help centres, one removed first name and one removed reference to a private source file.

## Rule

| | |
|---|---|
| Script | `vwap-prop/vwap_prop.py` in the repository root. Needs pandas and numpy |
| Data | USTEC (Nasdaq 100) CFD, M1, one broker (MT5 export, server time New York + 7). Tick volume, not exchange volume. Same file as the earlier Nasdaq tests |
| Session | Regular hours, 9:30 to 16:00 New York (decisive). Full futures day 18:00 to 17:00 as a supplementary run. A day counts with at least 90% of its minutes |
| Candles | 5 minutes from 9:30: 78 per day |
| EMA | 9 on the 5-minute close, continuing across days |
| VWAP | Restarts every day at the first candle. Price per minute (open + high + low + close) / 4, weighted by tick volume |
| Signal | Long only. The EMA 9 crosses above the VWAP on a closed candle. Confirmation: a later candle closes above the EMA 9 while the EMA 9 is still above the VWAP. If the EMA 9 falls back to or below the VWAP first, the signal is cancelled |
| Entry | Open of the candle after the confirmation, at the latest on the third-to-last candle of the day. One position at a time |
| Exit | First candle that closes below the EMA 9, out at the next open. Everything closed at the end of the session |
| Costs | Spread at the entry minute plus 1 point slippage per side. Sensitivity 0 and 2 times the slippage. In dollars: points × $20 (one NQ contract) |
| Challenge, firm A 50K | Target +$3,000. Maximum loss $2,000 below the highest end-of-day balance, rising only, stopping at the start balance. The open loss inside a trade counts (lowest price per minute). Consistency: best day at most 55% of the target, otherwise the target rises to best day / 0.55. At least 2 trading days. Attempts one after another: a new attempt starts the day after the previous one ends |
| Decisive period | 17 November 2023 to 5 November 2026 ("the last 3 years", counted from the maker's post, up to the end of the data) |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M1 export in the format described in the main README works.

## Self-test and noise check first

Self-test (`selftest.txt`): EMA equal to pandas `ewm(adjust=False)`, VWAP equal to a recomputation, the rule equal to a second implementation (65 against 65 trades), seven hand-calculated challenge cases correct, the fast challenge equal to the loop on 50 random runs. Passed.

24 fake markets (1,500 days of minute bars each, random walk without drift, 60 sub-steps per minute, fixed spread 1 point), 2,000 control runs per set (`noise_24sets.txt`). Threshold: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95.

| | Result |
|---|---|
| Mean net result per trade against Null A | mean percentile 55.6, 2 of 24 above 95: passed |
| Pass rate against Null A in the challenge | mean percentile 69.9, 3 of 24 above 95: outside the limit, failed |
| Pass rate of the rule on the fake markets | 10.1% on average (5.5% to 13.8% per set); Null A 8.6% |

On markets without any edge, the rule passes about one in ten challenges, and more often than random entries with the same exit. Two other control groups were tried on fake data only and did not remove this difference. So a comparison of pass rates with chance cannot show an edge of the rule: in version 1.1 that claim (C5) is descriptive only. The check for the mean result per trade (C3) passed and stayed decisive.

## Data check

`data_check_ustec_rth.txt`: valid sessions 2023 to 2026: 247, 249, 247, 210. Spread empty in 0.0% to 0.5% of session minutes, zero tick volume 0.00%. 734 valid sessions in the decisive period. `data_check_ustec_full.txt` for the full futures day.

## Result, Nasdaq 100, 17 November 2023 to 5 November 2026 (decisive)

| | Measured | Claimed |
|---|---|---|
| Trades | 799 on 552 days | 396 |
| Win rate after costs | 32.5% (95% Wilson: 29.4% to 35.9%); before costs 33.9% | 56.6% |
| Mean net result per trade | **-2.03 points** (95% bootstrap per trading day: -6.44 to +3.36) = -$40.56 per contract | |
| Profit factor | 0.89 (0.68 to 1.18) | 1.84 |
| Without costs | -0.03 point, profit factor 1.00 | |
| Median holding time | 25 minutes | |
| Average win and loss per contract | +$1,051.66 and -$567.43 | +$292.78 and -$206.97 |

## Control (10,000 runs, seed 43)

Null A: the same days and session, the same exit and the same costs, long only. On every candle without an open position where the close is above the EMA 9, chance opens a long with probability p. p is set so that the mean number of trades equals the rule's (p = 0.0314, 799 trades on average).

| | Mean net result per trade |
|---|---|
| The rule | -2.03 points |
| Null A, mean of the runs | -2.66 points |
| Rule's percentile | **65.0** |

## The challenge, firm A 50K, one contract

| | Measured |
|---|---|
| Attempts one after another | 95 completed: **9 passed, 86 failed** |
| Pass rate | **9.5%** (95% Wilson: 5.1% to 17.0%). Claimed: 85% |
| Median length of an attempt | 6 trading days |
| Null A in the same challenge (descriptive) | 9.4% on average (5 to 95: 4.3% to 15.0%), percentile 53.9 |
| The same rule on the fake markets without edge (noise check) | 10.1% on average |

All 95 attempts with their dates are in `run01_ustec.txt`.

## Verdict by the pre-set criteria

| Claim | Criterion | Result |
|---|---|---|
| C1: win rate 56.6% | upper end of the 95% range of the win rate below 56.6% | 35.9%: falsified |
| C2: the rule makes a profit, profit factor 1.84 | upper end of the 95% range of the mean result below 0, or of the profit factor below 1.84 | profit factor at most 1.18: falsified |
| C3: the rule picks better moments than chance | not above percentile 95 of Null A | 65.0: falsified |
| C4: 85% of the challenges are passed | upper end of the 95% range of the pass rate below 85% | 17.0%: falsified |
| C5: the pass rate comes from the rule | descriptive since v1.1 | Null A 9.4%, fake markets 10.1% |

## Supplementary (not decisive, same script)

| Variant | Result |
|---|---|
| Per year | 2024: -5.53 points per trade (276 trades); 2025: -1.41 (266); 2026: +1.43 (224); 2023: 33 trades, insufficient. Only 2024 has a 95% range entirely below 0 |
| Slippage 0 / 1 / 2 times | -0.03 / -2.03 / -4.03 points per trade |
| Overlapping attempts (a new attempt on every session) | 52 of 731 passed: 7.1% |
| Firm B 25K, one contract | 6 of 161 passed: 3.7% (1.7% to 7.9%) |
| Firm A 50K, two contracts | 13 of 173 passed: 7.5% (4.4% to 12.4%) |
| Crossing candle counts as confirmation | 887 trades, -2.42 points (-6.55 to +2.33), profit factor 0.88 |
| VWAP without volume | 809 trades, -2.36 points (-6.71 to +2.85), profit factor 0.88 |
| 2019 to 16 November 2023 | 1,312 trades, -1.85 points (-3.82 to +0.19), profit factor 0.86, percentile Null A 67.3; challenge 9 of 96 (9.4%), Null A 8.9% |
| Full futures day, 18:00 to 17:00 | 2,009 trades, win rate 28.4%, -3.11 points (-4.76 to -1.47), profit factor 0.75, percentile Null A 28.1; challenge 4 of 101 (4.0%) |

The largest single gain, +1,416.85 points after costs, is on 9 April 2025, a day with an unusually large rise of the index. It is in the data and in the trade file; it is not a data error in the trade itself.

## What this does and does not say

It measures one mechanical reading of the rule on the Nasdaq 100 index CFD, with costs, against chance and under the published rules of one prop firm. It does not measure the platform's backtest. Possible reasons for a difference between the two: a different market or contract, a different session, different costs, a smaller position size (the claimed average win and loss are about a quarter to a third of ours per contract), different challenge rules, or a different way of counting attempts. The pass rate of a rule without an edge depends mostly on the challenge: on fake markets without any edge, this rule passed about one in ten.

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.0-english.md` | Fixed before the data was opened |
| `hypothesis-v1.1-dutch.md`, `hypothesis-v1.1-english.md` | After the noise check, before the data was opened: C5 descriptive |
| `selftest.txt` | Self-test |
| `noise_24sets.txt` | Noise check |
| `data_check_ustec_rth.txt`, `data_check_ustec_full.txt` | Data checks |
| `run01_ustec.txt`, `trades_ustec.csv` | Decisive run with all attempts and the supplementary variants, all trades |
| `run01_ustec_full.txt`, `trades_ustec_full.csv` | Full futures day |

## Reproduce

```
pip install pandas numpy
python vwap-prop/vwap_prop.py --selftest
python vwap-prop/vwap_prop.py --noise
python vwap-prop/vwap_prop.py USTEC_M1.csv --datacheck --session rth
python vwap-prop/vwap_prop.py USTEC_M1.csv --datacheck --session full
python vwap-prop/vwap_prop.py USTEC_M1.csv --session rth --firm firm_a --out ./out
python vwap-prop/vwap_prop.py USTEC_M1.csv --session full --firm firm_a --n 2000 --nprop 500 --out ./out
```

The published script was run again from a clean folder: self-test passed, the noise check, the data checks, both runs and both trade files identical to the internal run (only the firm label differs).

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
