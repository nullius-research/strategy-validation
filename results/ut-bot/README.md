# UT Bot Alerts on Nasdaq 5 minutes: results

The rule comes from a trading channel's video (November 2023) about UT Bot Alerts, one of the most popular indicators on TradingView. The video tests it by hand for one month, October 2023, on the Nasdaq 5-minute chart, and reports 66 trades, 44 winners and 22 losers ("just over a 66% win rate", 66.7%) and "123% profit on the account". Position size is not stated. All three indicators in the video are public scripts, so the rule could be rebuilt exactly; only the swing used for the stop is undefined.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` and `hypothesis-v1.1-dutch.md` (binding), with English versions written at the same time. Version 1.1 changes only the control group, after version 1.0 failed the noise check (see below). Rule, data, periods, costs and pass/fail criteria are the same in both. The published Dutch files differ from the internal ones only in one removed first name and one removed reference to a private source file.

## Rule

| | |
|---|---|
| Script | `ut-bot/utbot_control.py` in the repository root. Needs `numba` besides pandas and numpy |
| Bars | MT5 Nasdaq 100 CFD (USTEC) M1 export from one broker, server time, combined into 5-minute bars. The same export as the Box Theory test (`results/box-theory/data_check_ustec.txt`) |
| Session | New York 08:00 to 17:00 America/New_York. A signal counts if its bar closes inside that window |
| UT Bot | The public code, key value 2, ATR period 1, no Heikin Ashi. Signal: close crosses the trailing stop |
| Linear Regression Candles | The public code, regression length 11; signal line = 7-bar SMA of the regression close |
| Count | The first three UT Bot signals per day in the session. A signal that fails the filter or comes during an open trade still counts as one of the three |
| Filter | Buy: close above the open and above the signal line. Sell: mirrored |
| Entry | Close of the signal bar. One position at a time |
| Stop | Lowest low (buy) or highest high (sell) of the last 10 bars, signal bar included. No trade if under 1 point |
| Exit | Stop; or the first close on the other side of the signal line, but only if the trade is in profit at that close. No time limit |
| Path rule | Bar by bar on 5 minutes. A stop inside the bar comes before an exit at the close. A bar that opens beyond the stop exits at its open |
| Costs | Spread from the export at the entry bar, plus 1 point slippage per side. Sensitivity 0 and 2 points |
| Decisive period | P1: 1 January 2018 to 5 November 2026 |
| Run | Variant 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M1 export of a Nasdaq 100 CFD in the format described in the main README works.

## Noise check first

24 fake markets of 5 years of M1 with a session structure, random walk without drift, 2,000 control runs per set. Threshold: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95.

| Version | Mean percentile | Above 95 | Outcome |
|---|---|---|---|
| v1.0: control group with random entry and a coin flip for direction | 99.1 | 23 of 24 | Failed (`noise_24sets_v1.0_failed.txt`) |
| v1.1: control group with random entry that passes the same colour and signal-line filter | 44.9 | 1 of 24 | Passed (`noise_24sets_v1.1.txt`) |

Cause, measured on two fake markets (`diag_k.py`): random entries on the wrong side of the signal line exit at once or lose more, and have smaller stops, so costs weigh more. Random entries that pass the same filter do about as well as the rule. On markets with no pattern at all, the rule therefore beats a coin flip. The coin-flip control (Null B) is reported for comparison only and is never read as "better than chance".

## Result, P1 (decisive)

| | Measured |
|---|---|
| Trading days | 2,198 |
| UT Bot signals in the session | 15,723 |
| ... within the first three of the day | 6,570 |
| ... through the candle colour | 6,565 |
| ... through the signal line | 6,490 |
| Skipped during an open trade | 1,143 |
| Dropped for a stop under 1 point | 0 |
| Trades | 5,347 (2,738 long, 2,609 short) |
| Win rate | 46.0% (95% Wilson: 44.7% to 47.4%) |
| Mean net R per trade | -0.101 (95% bootstrap per trading day: -0.139 to -0.064) |
| Mean R before costs | +0.027 |
| Profit factor (R) | 0.81 |
| Median stop | 38.4 points |
| Best and worst trade | +17.28 R and -3.04 R |
| Longest losing streak | 10 |
| Mean holding time | 11.7 bars of 5 minutes |
| Trades held overnight | 0.9% |

## Controls (10,000 runs, seed 37)

| Control | 5th / 50th / 95th percentile of mean net R | Rule's percentile |
|---|---|---|
| Null A: after each exit a random wait inside the session, then entry on the first bar that passes the same filter; same stop, exit, costs, at most three per day (decisive) | -0.134 / -0.100 / -0.064 | **47.2** |
| Null B: the same without the filter, coin flip for direction (supplementary, see the noise check) | -0.316 / -0.271 / -0.222 | 100.0 |

## Verdict by the pre-set criteria (P1)

| Claim | Criterion | Result |
|---|---|---|
| C1: 66.7% winners | upper end of the 95% range below 66.7% | 47.4%: falsified |
| C2: profitable | upper end of the 95% range of mean net R below 0 | -0.064 R: falsified |
| C3: the rule picks better moments than chance | not above percentile 95 of Null A | 47.2: falsified |

In this measurement the UT Bot signal added nothing on top of the colour and signal-line filter.

## The month of the video (P0, not decisive)

October 2023: 66 UT Bot signals within the first three per day, the same number as the trades in the video. Under these rules 59 of them became trades (2 failed the signal line, 5 came during an open trade). Win rate 49.2% (95%: 36.8% to 61.6%), mean net R +0.050 (-0.288 to +0.377), profit factor 1.10. One month of 66 trades can land far from the long-run result; the 95% range around 66.7% at 66 trades runs from about 54.7% to 76.8%.

## After the video (P2, supplementary)

6 November 2023 to 5 November 2026: 1,797 trades, win rate 49.5% (47.2% to 51.8%), mean net R -0.035 (-0.099 to +0.031), profit factor 0.93, percentile 62.4 against Null A (97.9 against Null B).

## Sensitivity (P1, not decisive)

| Variant | Win rate | Mean net R | Percentile Null A |
|---|---|---|---|
| Slippage 0 points | 50.7% | -0.028 | 39.6 |
| Slippage 2 points per side | 42.5% | -0.175 | 54.2 |
| Colour of the regression candle instead of the ordinary candle | 46.2% | -0.099 | 50.9 |
| Forced exit at 17:00 New York | 45.8% | -0.101 | 47.3 |

## Independent check

Five random P1 trades recomputed with separate code for UT Bot, the signal line, the stop and the path (`check5.py`): 5 of 5 identical in signal, filter, exit bar and net R (`check5_trades.txt`). The session window and the count of the first three were not recomputed separately in that check.

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.0-english.md` | Fixed before the data was opened |
| `hypothesis-v1.1-dutch.md`, `hypothesis-v1.1-english.md` | Control group changed after the failed noise check, before the data was opened |
| `noise_24sets_v1.0_failed.txt`, `noise_24sets_v1.1.txt`, `diag_k.py` | Noise checks and the diagnosis |
| `run01.txt` | P1, P0, P2 and the sensitivities |
| `trades_P1.csv`, `trades_P0.csv`, `trades_P2.csv` | All trades |
| `check5.py`, `check5_trades.txt` | Independent check |

## Reproduce

```
pip install pandas numpy numba
python ut-bot/utbot_control.py selftest
python ut-bot/utbot_control.py noise
python ut-bot/utbot_control.py run USTEC_M1.csv
```

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
