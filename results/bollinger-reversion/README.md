# Bollinger band reversion: results

Null Test 02. The trade log behind the numbers in the video and the article.

## Setup

| | |
|---|---|
| Script | `bb_reversion_multi.py` in the repository root |
| Signal | H1 close outside Bollinger(200, 2.5), paths walked on M15 |
| Pairs | EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY |
| Data | MT5 M15 exports from one broker, August 2022 to August 2026. USDCAD starts in January 2025 |
| Fade | Trade against the break, back toward the middle band (`real_R`) |
| Follow | Same moment, same stop, same target distance, with the break (`anti_R`) |
| Run | 10 August 2026 |

The exact command line of the run was not saved. The output matches the script defaults (cost 1.2 pips round trip, stop 2.0x, max 960 M15 bars), but that is an inference, not a record.

## Result

790 trades over 460 trading days, 17 August 2022 to 30 July 2026.

| | Mean R per trade | 95% interval | P(mean > 0) |
|---|---|---|---|
| Fade | +0.0092 | −0.0395 to +0.0575 | 65% |
| Follow | −0.0243 | −0.0768 to +0.0281 | 18% |

Intervals from a cluster bootstrap that resamples whole trading days, 4,000 draws, seed 42. Both intervals include zero.

## By year (fade)

| Year | Trades | Mean R | Win rate | Profit factor |
|---|---|---|---|---|
| 2022 (from Aug) | 75 | +0.039 | 60.0% | 1.17 |
| 2023 | 184 | +0.031 | 62.0% | 1.13 |
| 2024 | 186 | −0.118 | 55.9% | 0.67 |
| 2025 | 219 | +0.130 | 68.9% | 1.72 |
| 2026 (to Jul) | 126 | −0.063 | 55.6% | 0.79 |

Tested on 2025 alone, this looks like a discovery. Over the full sample it is one good year in a series that swings around zero.

## Verdict

No measurable directional information. Fading the band does not clearly beat following it, and neither clears zero.

## Limitations

- One broker, one data source, about four years.
- Costs are a fixed assumption, not the historical spread per trade.
- The raw price exports are not published. Run the script on your own MT5 exports to reproduce the method; exact numbers will differ by broker.

## Files

`bb_multi_trades.csv`, one row per trade:

| Column | Meaning |
|---|---|
| `Date` | Signal time (UTC) |
| `Symbol` | Pair |
| `Dir` | Fade direction, 1 = long, −1 = short |
| `Slope` | Band slope measure the script uses for the regime split |
| `R_pips` | Stop distance in pips (1R) |
| `real_R`, `real_exit` | Fade result in R and exit type |
| `bars` | M15 bars until exit |
| `anti_R`, `anti_exit` | Follow result in R and exit type |
| `Regime` | Slope tercile: flat, medium, steep |
| `diff` | `real_R` minus `anti_R` |

Research only. Not financial advice. No recommendation to trade anything.
