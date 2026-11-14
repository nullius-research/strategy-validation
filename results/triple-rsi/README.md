# Triple RSI on SPY: results

A strategy research website published this rule in an article, a newsletter post, a video and a social media post. On SPY "since 1993" it reports a 90% win rate: 103 trades, 1.2% average gain per trade and a profit factor of 4 (article, February 2026), or 83 trades and almost 1.4% per trade (video, September 2026). No stop. Costs are not mentioned.

The hypothesis was written and fixed before any price data was opened: `hypothesis-v1.0-dutch.md` (binding; the reference to a private source file is removed, nothing else changed) and `hypothesis-v1.0-english.md`. The script was checked on 24 synthetic random walks before the real run.

Two results matter more than any single number:

- On SPY, January 1994 to November 2026, the rule passed all four pre-set checks. But on **89 trades**, below the threshold of about 100 that this project normally requires.
- On the S&P 500 index from 1950 to January 1993, before SPY existed, the same rules averaged **-0.03% per trade** and landed at **percentile 4.2** against the control. This period was supplementary in the hypothesis, so it does not change the verdict, but it belongs next to it.

## Rule

| | |
|---|---|
| Script | `triple-rsi/triple_rsi_control.py` in the repository root |
| Market | SPY daily closes without dividend adjustment, Yahoo Finance. Sensitivity: dividend-adjusted closes |
| Filter | Close above its 200-day simple moving average |
| Signal | 5-day RSI below 30, lower than the day before for three days in a row, and below 60 three days ago |
| Entry | Close of the signal day |
| Exit | Close of the first later day on which the 5-day RSI crosses above 50. No stop, no target, no time limit |
| RSI | Wilder's RSI, period 5. The source does not say which RSI it used |
| Positions | One at a time; a signal during an open trade is skipped |
| Costs | 2 basis points round trip, assumed. Sensitivity at 0 and 4 bp |
| Warm-up | First 250 trading days, so entries start 25 January 1994 |

The prices are not in this repository. Series used: SPY from Yahoo Finance, 29 January 1993 to 13 November 2026, 8,507 days; ^GSPC from Yahoo Finance, 2 January 1948 to 28 January 1993, 11,334 days. `json_to_csv.py` converts the Yahoo chart response; `datacheck_i.py` checks the series without reading prices.

## Noise check first

24 random walks of 8,400 days, drift 0.03% and volatility 1.2% per day, 2 bp (`noise_24sets.txt`):

| | |
|---|---|
| Average trades per set | 92 |
| Average win rate | 67.3% (60.6% to 76.2%) |
| Percentile against Null A, average | 47.0 |
| Sets above 95 | 0 of 24 |
| Threshold | average 35 to 65, at most 3 above 95: passed |

Two out of three winners is what no edge looks like for this rule.

## Decisive: SPY, 25 January 1994 to 13 November 2026

| | Measured |
|---|---|
| Days above the 200-day average | 6,186 |
| ... with RSI below 30 | 490 |
| ... down three days in a row | 192 |
| ... below 60 three days ago | 119 |
| Skipped during an open trade | 30 |
| Trades | 89 |
| Win rate | 89.89% (95%: 81.9% to 94.6%) |
| Mean net return per trade | +1.286% (95% bootstrap: +0.891% to +1.658%) |
| Profit factor | 6.08 (95% bootstrap: 2.89 to 22.83) |
| Mean holding time | 4.9 trading days (median 4, longest 15) |
| Days in the market | 433 of 8,256 |
| Worst trade | -7.39% |
| Deepest drop inside a trade | -13.79% |
| Rule, compounded | +207.4% |
| Buy and hold, same period, without dividends | +1,498.7% |

## Controls (10,000 runs, seed 37)

| Control | 5th / 50th / 95th percentile | Rule's percentile |
|---|---|---|
| Null A: random entry days above the 200-day average, the real holding times shuffled, same number of trades, one at a time (decisive) | -0.141% / +0.174% / +0.475% | **100.0** |
| Null B: same days, the rule's own exit (supplementary) | +0.119% / +0.430% / +0.731% | 100.0 |

At 0 and 4 bp: +1.306% and +1.266% per trade, percentile 100.0. With dividend-adjusted closes: 91 trades, 90.11%, +1.376%, profit factor 7.28, percentile 100.0.

## Verdict by the pre-set criteria (SPY)

| Claim | Criterion | Result |
|---|---|---|
| C1: 90% winners | upper end of the 95% range below 90% | 94.6%: not falsified |
| C2: 1.2% per trade (1.4% in the video) | upper end below 1.2% | +1.658%: not falsified |
| C3: profit factor 4 | upper end below 4 | 22.83: not falsified |
| C4: the RSI conditions pick better days than chance in the same trend | not above percentile 95 of Null A | 100.0: not falsified |

Not falsified in this measurement, on 89 trades. Not "works".

## Reproducing the source (not decisive)

| | Measured | Source |
|---|---|---|
| Up to 20 Feb 2026 (article) | 87 trades, 90.80%, +1.336%, PF 6.77 | 103 trades, 90%, 1.2%, PF 4 |
| Up to 18 Sep 2026 (video) | 89 trades, 89.89%, +1.286% | 83 trades, about 90%, almost 1.4% |

## By decade (all below 100 trades: insufficient)

| Decade | Trades | Win rate | Mean |
|---|---|---|---|
| 1990s | 18 | 94.4% | +2.014% |
| 2000s | 18 | 94.4% | +1.579% |
| 2010s | 33 | 90.9% | +1.016% |
| 2020s | 20 | 80.0% | +0.814% |

## Supplementary: S&P 500 index, 3 January 1950 to 28 January 1993

Every SPY day is a day the source could see. The years before are not. Same script, ^GSPC (`run01_P3_gspc.txt`, `trades_P3_gspc.csv`):

| | Measured |
|---|---|
| Trades | 143 |
| Win rate | 70.63% (95%: 62.7% to 77.5%) |
| Mean net return per trade | -0.026% (95%: -0.466% to +0.354%) |
| Profit factor | 0.97 (95%: 0.58 to 1.78) |
| Null A 5th / 50th / 95th | -0.011% / +0.281% / +0.560% |
| Percentile against Null A | **4.2** (Null B: 16.0) |
| Worst trade | -19.08% |
| Deepest drop inside a trade | -27.72% |
| Rule, compounded | -8.2% |

By decade: 1950s 37 trades +0.290%, 1960s 31 trades -0.702%, 1970s 30 trades -0.262%, 1980s 36 trades +0.177%, 1990 to 1993 9 trades +0.984%.

## Independent check

Five random SPY trades recomputed with a separate RSI (pandas ewm), moving average, signal and exit (`check5_trades.py`): 5 of 5 identical (`check5_trades.txt`).

## Files

| File | Content |
|---|---|
| `hypothesis-v1.0-dutch.md`, `hypothesis-v1.0-english.md` | Fixed before the data was opened |
| `noise_24sets.txt` | Noise check |
| `datacheck_i.py`, `datacheck_i.txt`, `json_to_csv.py` | Data conversion and check |
| `run01_P1.txt` | Decisive run, SPY, with 0, 2 and 4 bp |
| `run01_P0a.txt`, `run01_P0b.txt` | Reproduction up to the article and the video |
| `run01_P1_adjclose.txt` | Dividend-adjusted closes |
| `run01_P3_gspc.txt` | S&P 500 index, 1950 to 1993 |
| `trades_P1.csv`, `trades_P3_gspc.csv` | All trades |
| `check5_trades.py`, `check5_trades.txt` | Independent check |
| `chart_trsi.py`, `triple-rsi-vs-random-1200x630.png` | Chart |

## Reproduce

```
python triple-rsi/triple_rsi_control.py --synthetic 24 --runs 2000
python triple-rsi/triple_rsi_control.py SPY_yahoo_D1_1993_2026.csv --trades-out trades_P1.csv
python triple-rsi/triple_rsi_control.py GSPC_yahoo_D1_1948_1993.csv --start 1950-01-03
```

This is a measurement of one rule in two periods. It is not financial advice or a recommendation to trade or not trade any approach. Test it yourself and judge for yourself.
