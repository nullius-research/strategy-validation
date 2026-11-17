# Supertrend + 200 EMA on EURUSD and EURJPY 30 minutes: results

The rule comes from a strategy-testing channel's video (August 2020). The video tests a Supertrend strategy by hand, 100 trades, first on EURJPY and then on EURUSD: buy when the Supertrend line turns green and flips below the candles while price is above the 200-period EMA, sell on the mirror image, stop "at or below the supertrend line", fixed target of 1.5 times the risk. It reports a win rate of "approximately 46 percent" and a profit. The video does not state the timeframe, the Supertrend settings or the period.

The hypothesis was written and fixed before any real data was opened: `hypothesis-v1.0-dutch.md` (binding), with an English version written at the same time. Undefined in the video, and fixed in advance: 30 minutes as the decisive timeframe (15 minutes and 1 hour supplementary), Supertrend (10, 3) as in TradingView's built-in default, the stop on the Supertrend value of the signal bar, and a minimum stop of 5 pips. After approval and before any run, one sentence in the Dutch text was corrected so that the band rule matches TradingView's published `pine_supertrend` code exactly. The published Dutch file differs from the internal one only in one removed first name and one removed reference to a private source file.

## Rule

| | |
|---|---|
| Script | `supertrend-200ema/supertrend_control.py` in the repository root. Needs pandas and numpy |
| Bars | MT5 M15 exports from one broker (EURUSD and EURJPY, August 2022 to August 2026), broker time converted to UTC, combined into 30-minute bars. The same exports as the MACD + 200 EMA and Bollinger + 200 EMA tests |
| Supertrend | Factor 3, ATR 10 (Wilder), on (high + low) / 2. A literal port of `pine_supertrend` from TradingView's Pine reference |
| EMA | 200 on the 30-minute close |
| Long signal | Supertrend direction flips from down to up on the closed bar, close above the EMA. Short mirrored |
| Entry | Open of the next 30-minute bar. One position at a time per pair |
| Stop | The Supertrend line on the signal bar (lower band for a long, upper band for a short), fixed. No trade if under 5 pips (EURJPY 0.05) |
| Target | 1.5R. No break-even, no trailing, no time limit |
| Path rule | Bar by bar on 15 minutes. A bar that touches stop and target counts as a stop. The entry bar counts |
| Costs | 1.2 pips round trip. Sensitivity 0 and 2.0 pips |
| Decisive | EURUSD and EURJPY together, 30 minutes, the whole export |
| Run | Run 1 of 1 |

The prices are not in this repository (broker data). Any MT5 M15 export in the format described in the main README works.

## Noise check first

24 fake markets (EURUSD and EURJPY, 4 years of M15, random walk without drift), 2,000 control runs per set (`noise_24sets.txt`). Threshold: mean percentile against Null A between 35 and 65, at most 3 of 24 above 95, and a win rate near the 40% break-even.

| | Result |
|---|---|
| Mean percentile against Null A | 52.2 |
| Sets above 95 | 2 of 24 |
| Mean win rate on noise | 40.3% |
| Outcome | Passed |

Null B (a random bar in the same trend state) gave a mean percentile of 71.9 and 6 of 24 sets above 95 on noise. It leans towards the rule even on markets with no pattern, so it is reported for comparison only.

## Data check

`data_check_eurusd_eurjpy.txt`: 100,037 and 99,993 rows, no duplicate times, no empty or negative prices, no impossible bars. 7 and 10 weekday gaps, the largest 2 hours. Opens more than 1% away from the previous close: 1 and 3, all at a Monday open.

## Result, 30 minutes (decisive)

| | Measured |
|---|---|
| Period of the trades | 9 August 2022 to 7 August 2026 |
| Supertrend flips through the EMA filter | EURUSD 748, EURJPY 704 |
| Dropped for a stop under 5 pips | 0 and 1 |
| Trades (one at a time) | 805 (EURUSD 404, EURJPY 401; 439 long, 366 short) |
| Win rate | 37.3% (300 of 805; 95% Wilson: 34.0% to 40.7%) |
| Mean net R per trade | -0.095 (95% bootstrap per trading day: -0.179 to -0.011) |
| Mean R at 0 / 1.2 / 2.0 pips | -0.065 / -0.095 / -0.114 |
| Profit factor (R) | 0.85 |
| Best 5% of trades | +59.5 R, against a total of -76.1 R |
| Median stop | 47.0 pips (cost 0.026 R at the median) |
| Longest winning and losing streak | 5 and 15 (the video: 7 and 7) |
| Median holding time | 16.8 hours |

Per pair: EURUSD 37.6% (33.0% to 42.4%), -0.092 R; EURJPY 36.9% (32.3% to 41.7%), -0.097 R. Per year: 2022 33.3%, 2023 44.0%, 2024 39.3%, 2025 34.4%, 2026 32.6%.

## Controls (10,000 runs, seed 19)

| Control | 5th to 95th percentile of mean net R | Rule's percentile |
|---|---|---|
| Null A: the same entries, direction by coin flip, same stop distance, same 1.5R, same costs (decisive) | -0.093 to +0.037 | **4.4** |
| Null B: per trade a random bar in the same pair, month and trend state, stop on that bar's Supertrend line (supplementary, see the noise check) | -0.161 to -0.021 | 48.1 |

A percentile of 4.4 means that 95.6% of the coin-flip runs ended with a higher mean net R than the rule.

## Verdict by the pre-set criteria

| Claim | Criterion | Result |
|---|---|---|
| C1: about 46% winners | upper end of the 95% range below 46% | 40.7%: falsified |
| C2: profitable | upper end of the 95% range of mean net R below 0 | -0.011 R: falsified |
| C3: the rule picks better moments than chance | not above percentile 95 of Null A | 4.4: falsified |

## Supplementary (not decisive, same script and settings)

| Variant | Trades | Win rate (95% Wilson) | Mean net R (95%) | Percentile Null A |
|---|---|---|---|---|
| 15 minutes, EURUSD + EURJPY | 1,600 | 40.4% (38.0% to 42.8%) | -0.035 (-0.098 to +0.027) | 50.5 |
| 1 hour, EURUSD + EURJPY | 434 | 37.6% (33.1% to 42.2%) | -0.076 (-0.188 to +0.040) | 37.0 |
| 30 minutes, eight other pairs | 3,195 | 38.1% (36.4% to 39.8%) | -0.084 (-0.132 to -0.035) | 0.4 |

USDCAD in the eight other pairs only has data from January 2025 (158 trades). None of the variants reaches 46% or lies above percentile 95 of Null A.

## Independent check

Five random trades from the decisive run (seed 5, not chosen on outcome) recomputed with separate code: own 30-minute bars, a second Supertrend implementation in plain Python, own EMA loop and own 15-minute path (`check5.py`). Direction, entry, stop distance, exit time, gross and net R: 5 of 5 identical (`check5_trades.txt`). The script's self-test compares the two Supertrend implementations on 3,000 bars: identical.

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.0-english.md` | Fixed before the data was opened |
| `noise_24sets.txt` | Noise check |
| `data_check_eurusd_eurjpy.txt` | Data check |
| `run01.txt`, `trades_m30.csv` | Decisive run and all trades |
| `run01_extra_timeframes.txt`, `trades_m15.csv`, `trades_h1.csv` | 15 minutes and 1 hour |
| `run01_extra_pairs.txt`, `trades_extra_pairs.csv` | Eight other pairs |
| `check5.py`, `check5_trades.txt` | Independent check |

## Reproduce

```
pip install pandas numpy
python supertrend-200ema/supertrend_control.py --selftest
python supertrend-200ema/ruis_24sets.py --from 1 --to 24 --work ./noise
python supertrend-200ema/datacontrole.py EURUSD_M15.csv EURJPY_M15.csv
python supertrend-200ema/supertrend_control.py --dir ./data --pairs EURUSD,EURJPY --tf 30
python results/supertrend-200ema/check5.py supertrend_trades.csv EURUSD_M15.csv EURJPY_M15.csv
```

This is a measurement of one rule in one period. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
