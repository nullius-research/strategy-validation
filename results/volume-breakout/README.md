# Volume breakout on US large caps: results

Null Test 03. The test behind the video and the article *The Control Group That Was Missing*.

A six-agent AI trading system built in Claude Code circulates on Instagram. Its Scanner agent is told to flag "momentum, volume surges, and key-level tests". This test turns that instruction into a fixed rule and measures it. It tests the rule, not the agents. No language model touched the price history: signals and scoring are deterministic Python.

## Setup

| | |
|---|---|
| Scripts | `volume-breakout/validation/` (`signals.py`, `control.py`) |
| Signal | Daily close above the highest high of the previous 20 bars, and volume above 1.5x the 20-bar average |
| Direction | Long only |
| Entry | Open of the next bar |
| Stop | Entry minus 2x ATR14, ATR computed through the signal bar only |
| Target | 2R, or exit at the close after 20 bars |
| Cooldown | 5 bars between two signals on the same ticker |
| Costs | 10 bps per trade, assumed |
| Universe | 60 US large caps, listed in `volume-breakout/config/watchlist.md` |
| Data | yfinance adjusted daily bars, 15 August 2016 to 12 August 2026 |
| Path rule | Bar by bar. A bar that touches both stop and target counts as a stop |
| Run | 13 August 2026, variant 1 of 1. Re-run 31 October 2026 with identical output |

## Result

2,097 trades over 1,135 trading days, 14 September 2016 to 5 August 2026.

| | |
|---|---|
| Expectancy | +0.1622 R per trade |
| Profit factor | 1.332 |
| Win rate | 47.6% |
| Bootstrap 95% interval | +0.0967 to +0.2261 R (2,000 draws of whole trading days, all tickers together, seed 7) |

## Controls

Same 2,097 signals, same stop, target and costs. Both controls share one random generator, seed 42.

| Control | 5th to 95th percentile | Rule's percentile |
|---|---|---|
| Coin flip: same moment, random direction, 400 draws | −0.0236 to +0.0544 R | 100.0 |
| Random entry dates: same ticker, direction and stop in ATR, 400 draws | +0.1366 to +0.2204 R | **27.0** |

The coin flip is the wrong null here. On long-only stocks it is half short in a market that rose, so it loses by construction and the rule looks strong next to it. The random-date control keeps direction, market drift and survivorship bias on both sides and varies only the timing. That is the one that counts, and the rule sits below its middle.

## By year, next to random entries

The rule is positive in 9 of 11 years. That looks robust until you put a random long entry next to it.

| Year | Trades | Rule, mean R | Win rate | PF | Random entry, mean R |
|---|---|---|---|---|---|
| 2016 (from Sep) | 75 | +0.237 | 50.7% | 1.53 | +0.245 |
| 2017 | 296 | +0.335 | 55.1% | 1.83 | +0.417 |
| 2018 | 216 | −0.184 | 35.2% | 0.72 | −0.020 |
| 2019 | 227 | +0.217 | 54.6% | 1.50 | +0.344 |
| 2020 | 234 | +0.326 | 53.0% | 1.72 | +0.208 |
| 2021 | 203 | +0.111 | 43.3% | 1.21 | +0.160 |
| 2022 | 151 | +0.051 | 43.0% | 1.10 | −0.070 |
| 2023 | 211 | −0.008 | 39.3% | 0.99 | +0.176 |
| 2024 | 190 | +0.250 | 51.6% | 1.56 | +0.187 |
| 2025 | 180 | +0.155 | 48.3% | 1.33 | +0.176 |
| 2026 (to Aug) | 114 | +0.293 | 46.5% | 1.60 | +0.105 |

Random entry: `random_by_year.py`, 50 draws per signal, seed 11, grouped by the year of the random entry. Over all years it averages +0.1733 R, the middle of the control band above. The rule beats it in 5 years and trails it in 6. Descriptive only; the verdict comes from the control table.

## Verdict

Rejected. The rule picks no better moments than a random date. The positive expectancy is the market's drift over these ten years plus a list made of survivors, not information in the signal.

## Limitations

- One data source. yfinance adjusted bars are split- and dividend-adjusted and do not reflect what was tradeable at the time.
- Survivorship bias: the 60 tickers are companies that exist today. The random-date control carries the same bias, which is why it is the decisive one, but it inflates both absolute numbers.
- Costs are a fixed assumption, not measured at a broker. Gaps are not modelled, so real stops fill worse than scored.
- The random-date control matches the ATR multiple, not the volatility regime.
- One rule, one universe, one decade.
- The price history is not published. `volume-breakout/data/fetch.py history --years 10` downloads it again, but yfinance revises adjusted prices, so a fresh download can give slightly different numbers.

## Files

| File | Contents |
|---|---|
| `signals.csv` | The 2,097 signals: `date` (signal bar), `ticker`, `direction` (1 = long), `entry` (next open), `stop` |
| `trades.csv` | Same rows plus `r`: net result in R after costs, from `export_trades.py` |
| `run01.txt` | Original output of `control.py`, in Dutch. RESULTAAT = result, muntworp = coin flip, willekeurige datums = random dates, VERWORPEN = rejected |

## Reproduce

```
cd volume-breakout
pip install pandas numpy yfinance
python data/fetch.py history --years 10
python validation/signals.py
python validation/control.py --signals briefs/signals.csv --bars data/history.csv
python validation/export_trades.py --signals briefs/signals.csv --bars data/history.csv --out trades.csv
python validation/random_by_year.py --signals briefs/signals.csv --bars data/history.csv --draws 50 --seed 11
```

Research only. Not financial advice. No recommendation to trade anything.
