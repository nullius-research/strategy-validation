# 9 EMA + VWAP on 3 minutes, S&P 500: results

The rule comes from a viral Instagram reel (30 October 2026). The reel claims "$255,000 in the month of October" with options, using two indicators on the 3-minute chart: an EMA 9 on the close and a session VWAP on OHLC4. Calls when the EMA 9 crosses above the VWAP, puts when it crosses below, exit when a candle breaches the EMA 9. The reel does not name the underlying, the session times, the number of trades or a win rate.

## Note added 21 November 2026: opening time

The script took the opening minute (9:30 New York) from the largest jump in tick volume at 15:30, 16:30 or 17:30 server time. The server runs on New York time + 7 all year, so the opening is always 16:30. On days with economic releases at 8:30 New York the script picked 15:30, one hour too early. We reran the test with the opening fixed at 16:30, same data and seed. The original script reproduces the published numbers exactly. The verdict does not change. With the fixed opening, S&P 500 2019 to October 2026: 5,797 trades (was 5,850), −0.711 point per trade after costs (95%: −0.939 to −0.475; was −0.689), PF 0.78, percentile 70.9 against random entries (was 82.2). October 2026 alone: 59 trades, +0.483 point per trade (95%: −1.069 to +2.870; was 65 trades, −0.360). That is still too few trades to say anything, but the October result is now slightly positive instead of negative. Nasdaq 100: −2.671 point, percentile 70.8 (was −2.695, 71.5). Old and new output: [`results/audit-opening-2026-11-21/`](../audit-opening-2026-11-21/). This is a measurement of one rule in one period, not a recommendation. Test it yourself and make your own judgement.

The amount itself cannot be tested: it is the personal result of one account with options, with unknown position size and unknown choices per trade. This test measures the rule on the underlying index, not the account.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (binding), with an English version written at the same time. Three readings of the reel were chosen in advance: a candle "breaches" the EMA 9 when it closes on the other side (exit at the next open); no extra stop (the reel's -25% to -30% emergency exit is a percentage of an option premium); the S&P 500 as the decisive market, the Nasdaq 100 supplementary. The published Dutch file differs from the internal one only in one removed first name and one removed reference to a private source file.

## Rule

| | |
|---|---|
| Script | `vwap-9ema/vwap_control.py` in the repository root. Needs pandas and numpy |
| Data | US500 CFD, M1, one broker (MT5 export, server time New York + 7). Spread column filled from 2019. Tick volume, not exchange volume |
| Session | Regular hours only, 9:30 to 16:00 New York. Opening found per day from the jump in tick volume, as in the 5-minute opening range test. A day counts with at least 90% of its 390 minutes |
| Candles | 3 minutes from 9:30: 130 per day |
| EMA | 9 on the 3-minute close, regular hours only, continuing across days. Pine `ta.ema` |
| VWAP | Restarts at 9:30 every day. Price per minute (open + high + low + close) / 4, weighted by tick volume |
| Long signal | EMA 9 crosses above the VWAP on a closed candle. Short mirrored. Not on the first or last candle of the day |
| Entry | Open of the next candle. One position at a time; an opposite cross closes and reverses |
| Exit | First candle that closes on the wrong side of the EMA 9 (checked from the entry candle on), out at the next open. Everything closed at 16:00 |
| Result | Points and basis points per trade, net of costs. No fixed stop, so no R |
| Costs | Spread at the entry minute plus 0.25 point slippage per side. Sensitivity 0 and 2 times the slippage |
| Decisive | S&P 500, 2019 to 30 October 2026 (C1, C2); October 2026 alone (C3) |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M1 export in the format described in the main README works.

## Self-test and noise check first

Self-test on 60 fake days: EMA equal to pandas `ewm(adjust=False)`, VWAP equal to a per-candle recomputation, and the rule equal to a second implementation (207 against 207 trades, no differences).

24 fake markets (1,500 days of minute bars each, random walk without drift, 60 sub-steps per minute, fixed spread 0.5 point, random tick volume), 2,000 control runs per set (`noise_24sets.txt`). Threshold: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95.

| | Result |
|---|---|
| Mean percentile against Null A | 55.4 |
| Sets above 95 | 0 of 24 |
| Mean net result on noise | about -1.0 point per trade, equal to the costs |
| Outcome | Passed |

## Data check

`data_check_us500.txt`: valid sessions per year 2019 to 2026: 247, 245, 245, 249, 244, 249, 247, 207 (1,933 in the decisive period). Spread empty in 0.0% of session minutes (2025: 0.1%), zero tick volume 0.00%. 2017 and 2018 have an empty spread column for most days and are reported separately.

## Result, S&P 500, 2019 to October 2026 (decisive)

| | Measured |
|---|---|
| Trades | 5,850 on 1,779 days (3.29 per day with trades; 3,063 long, 2,787 short) |
| Median holding time | 15 minutes |
| Win rate after costs | 30.1% (95% Wilson: 29.0% to 31.3%); before costs 34.1% |
| Mean result per trade before costs | +0.104 point |
| Costs per trade | 0.793 point (spread 0.293 + 2 × 0.25 slippage) |
| Mean net result per trade | **-0.689 point** (95% bootstrap per trading day: -0.920 to -0.454); -1.75 basis points |
| Net at slippage 0 / 1 / 2 times | -0.189 / -0.689 / -1.189 point |
| Profit factor | 0.78 |
| Largest loss and gain per trade | -46.20 and +167.20 points |

Every year from 2019 to 2026 is negative after costs (per trade: -1.08, -0.74, -0.72, -0.88, -0.55, -0.40, -0.51, -0.62 point). Long -0.508 point, short -0.889 point. Every signal in the period arrived with no position open: 5,850 signals, 5,850 trades.

## Control (10,000 runs, seed 43)

Null A, decisive: the same days and session, the same EMA exit and the same costs. On every candle without an open position, chance opens a position with probability p, in the direction of the close relative to the EMA 9, so the exit works exactly as for the real trades. p is set so that the expected number of trades equals the rule's (p = 0.0276, 5,850 trades on average).

| | Mean net result per trade |
|---|---|
| The rule | -0.689 point |
| Null A, mean of the runs | -0.771 point |
| Rule's percentile | **82.2** |

The cross of the EMA 9 and the VWAP ended above 82.2% of the random-entry runs. The threshold set in advance was 95. The entry adds no measurable value over random entries with the same exit.

## October 2026, the month of the claim

| | Measured |
|---|---|
| Trades | 65 on 22 days: below the usual threshold of 100, insufficient |
| Mean net result per trade | -0.360 point (95%: -1.894 to +1.822); before costs +0.446 |
| Win rate after costs | 33.8% (23.5% to 46.0%) |
| Percentile against Null A | 67.1 |

## Verdict by the pre-set criteria

| Claim | Criterion | Result |
|---|---|---|
| C1: the rule makes money | upper end of the 95% range of the mean net result in 2019-2026 below 0 | -0.454 point: falsified |
| C2: the cross picks better moments than chance | not above percentile 95 of Null A | 82.2: falsified |
| C3: October 2026 was profitable with this rule | upper end of the 95% range in October 2026 below 0 | +1.771 point: not falsified, on 65 trades (insufficient) |

## Supplementary (not decisive, same script)

| Variant | Trades | Mean net per trade (95%) | Profit factor | Percentile Null A |
|---|---|---|---|---|
| Exit when a candle touches the EMA 9 (exit at the EMA level) | 5,850 | -0.590 point (-0.765 to -0.399) | 0.76 | not run |
| VWAP without volume (all minutes equal weight) | 6,285 | -0.677 point (-0.892 to -0.457) | 0.78 | 87.3 |
| S&P 500 2017-2018, spread filled with the 2019 median (0.4 point) | 1,051 | -0.808 point (-1.066 to -0.538) | 0.57 | 77.3 |
| Nasdaq 100 (USTEC) 2019 to October 2026, slippage 1 point per side | 5,987 | -2.695 points (-3.698 to -1.682); -2.03 basis points | 0.81 | 71.5 |
| Nasdaq 100, October 2026 | 62 | -8.545 points (-17.759 to +6.624) | 0.64 | 23.3 |

None of the variants is profitable after costs or above percentile 95 of Null A.

## Independent check

Five random trades from the decisive run (seed 11, not chosen on outcome) recomputed with separate code: own 3-minute candles via pandas resampling, own VWAP and own EMA via `ewm` (`check5.py`). Signal, entry, exit and the absence of an earlier exit: 5 of 5 identical (`check5_trades.txt`). The published script was run again from a clean folder: self-test passed, run and trade file identical.

## What this does and does not say

It measures one mechanical reading of the rule on the S&P 500 index CFD, with costs, against chance. It does not measure the account in the reel. Possible reasons for a difference between the two: the leverage and shape of options, choices per trade on top of the rule, position size, or a month that happened to be favourable. Before costs the rule is close to flat (+0.10 point per trade); costs of about 0.8 point per trade decide the outcome.

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.0-english.md` | Fixed before the data was opened |
| `noise_24sets.txt` | Noise check |
| `data_check_us500.txt`, `data_check_ustec.txt` | Data checks |
| `run01_us500.txt`, `trades_us500.csv` | Decisive run, October 2026 and the supplementary variants, all trades |
| `run01_us500_2017-2018.txt`, `trades_us500_2017-2018.csv` | 2017-2018 |
| `run01_ustec.txt`, `trades_ustec.csv` | Nasdaq 100 |
| `check5.py`, `check5_trades.txt` | Independent check |

## Reproduce

```
pip install pandas numpy
python vwap-9ema/vwap_control.py --selftest
python vwap-9ema/vwap_control.py --noise
python vwap-9ema/vwap_control.py US500_M1.csv --datacheck
python vwap-9ema/vwap_control.py US500_M1.csv --out ./out --label US500
python vwap-9ema/vwap_control.py US500_M1.csv --from 2017-03-21 --to 2018-12-31 --fillspread 0.4 --label US500_2017-2018 --out ./out --short
python vwap-9ema/vwap_control.py USTEC_M1.csv --slip 1.0 --label USTEC --out ./out --short
python results/vwap-9ema/check5.py US500_M1.csv ./out/trades_US500.csv
```

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
