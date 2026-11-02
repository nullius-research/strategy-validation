# Buy the dip after 3 red days: results

The rule comes from a backtest report that tested dozens of popular strategies and passed only this one. For its newer-data check, 2024 to 2026, it reports a profit factor of 3.98 on 98 trades across three US indices, and that the rule beat 1,999 of 2,000 random-timing runs.

## Rule

| | |
|---|---|
| Red day | Close below the previous close |
| Entry | After 3 red days in a row, buy at the close of the third |
| Exit | Close of the first day that closes higher, or after a maximum of N days. N is blurred in the report, so N = 1, 2, 3, 4, 5, 7, 10 and no maximum are all tested |
| Stop, target | None |
| Mirror test | Short after 3 green days |
| Costs | 2 basis points per round trip (4 bp as stress test) |
| Controls | Null A: random entry day, same exit rule. Null B: random entry, same holding times. 2,000 runs each, seed 42 |

Script: `buy-the-dip/buy_the_dip_test.py`. It reads any CSV with columns `date` and `close`.

## Data

Daily closes of the S&P 500 (`^GSPC`) and Nasdaq 100 (`^NDX`) price indices, 3 January 2000 to 30 October 2026, 6,748 trading days each, from Yahoo Finance. The prices are not in this repository. You can get them in a browser from
`https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=946684800&period2=1793577600&interval=1d`
(and the same with `%5ENDX`); the `close` series in that JSON is what was used.

Periods were fixed before the run: 2000-2007, 2008-2009, 2010-2018, and 2019 to September 2026 for comparison with the report.

## Result (no maximum hold, 2 bp)

| Index | Period | Trades | Win | PF | Rule return | Buy & hold | Beat Null A |
|---|---|---|---|---|---|---|---|
| S&P 500 | 2000-2007 | 113 | 75.2% | 2.84 | +62.1% | +0.9% | 1995/2000 |
| S&P 500 | 2008-2009 | 24 | 83.3% | 2.08 | +18.1% | −22.9% | 1466/2000 |
| S&P 500 | 2010-2018 | 113 | 67.3% | 1.49 | +20.5% | +121.3% | 1485/2000 |
| S&P 500 | 2019-Sep 2026 | 99 | 77.8% | 3.57 | +74.8% | +204.8% | 1981/2000 |
| Nasdaq 100 | 2000-2007 | 114 | 71.9% | 2.63 | +185.2% | −45.0% | 1993/2000 |
| Nasdaq 100 | 2008-2009 | 26 | 76.9% | 1.97 | +20.6% | −9.2% | 1398/2000 |
| Nasdaq 100 | 2010-2018 | 117 | 74.4% | 1.66 | +37.2% | +235.5% | 1633/2000 |
| Nasdaq 100 | 2019-Sep 2026 | 89 | 75.3% | 2.98 | +79.8% | +378.1% | 1948/2000 |

Newer-data window of the report, 2024 to September 2026, no maximum hold: S&P 500 36 trades, PF 8.89, beat 1982/2000 random entries; Nasdaq 100 29 trades, PF 6.38, beat 1941/2000; both together 65 trades, PF 7.49. The report's S&P-only version gives PF 8.75 on about 30 trades in that window. Fewer than 100 trades.

Median profit factor of random entry with the same exit: 1.10 to 1.55 in the four periods, up to 1.85 in 2024 to 2026. The exit rule alone makes almost any entry look profitable; the comparison that matters is against that.

- 2000-2007: the rule beat 99.7% or more of random entries on both indices.
- 2008-2009: too few trades (24 and 26) for a verdict.
- 2010-2018: profitable, but inside the random range.
- Worst single trade: −15.7% (Nasdaq 100, December 2000), −8.7% (S&P 500, October 2008). There is no stop.
- Short after 3 green days lost or stayed flat from 2010 on, as the report says, but was profitable on the S&P 500 in 2000-2009. Upward drift alone does not explain that; short-term mean reversion might.

`trades.csv` holds all 695 trades (no maximum hold) with entry date, exit date, days held and return. `run_GSPC.txt` and `run_NDX.txt` hold every holding limit, both cost levels and the mirror test.

## Limitations

Price indices without dividends; not directly tradable. No financing costs for leveraged products. Eight holding limits times four periods per index were tested, so single high numbers can be luck. Two of the three indices in the report were tested.

This is a measurement, not a recommendation. Test it yourself and make your own judgment.
