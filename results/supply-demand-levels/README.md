# Supply-demand levels on a volume profile: results

The rules come from a public document by a seller of a trading course. It describes entries at "supply and demand levels" taken from a volume profile, filtered by trend, structure and momentum, and claims a win rate of 60 to 80% with that filter and 5 to 10R per month.

The document is discretionary in places (which moving averages form the "cloud", what counts as "rejection on both sides"). Every translation to fixed rules is mine and is listed in `hypothesis-v1.3-dutch.md` (in Dutch), written and fixed before any real data was opened. The script was first checked on synthetic random-walk data, where it found two errors in my own setup (no minimum stop, and a coin flip with a different number of trades). Both were fixed in version 1.2, before the real run.

## Setup

| | |
|---|---|
| Script | `supply-demand-levels/levels_control.py` in the repository root |
| Instrument | US500 CFD, M1 export from one broker (MT5), 2 January 2019 to 30 October 2026 |
| Session | Regular US session only, 16:30 to 23:00 server time. The script checks this against the tick-volume jump at the open: 83.4% of days open on the expected minute, most others 1 or 2 minutes earlier |
| Levels | High-volume nodes in a 20-session volume profile (200 rows) that line up with a session point of control (100 rows), touched and rejected from both sides. Zone 8 points wide |
| Filters | EMA 34/50 cloud on 5 minutes and 1 hour, swing structure on 5 minutes, momentum back through the 5-minute cloud |
| Stop and target | Stop halfway to the next level behind the trade, target at the next level in front. Break-even at 50% of the way. No trade if the stop is closer than 4 points |
| Day rules | Stop after 1 win or 2 losses |
| Costs | Spread per bar from the export (median 0.50 point) plus 1 tick (0.25 point) slippage per side. Sensitivity at 0 and 2 ticks. No commission (the broker lists none for this CFD) |
| Path rule | Bar by bar on M1. A bar that touches both stop and target counts as a stop |
| Period | 2019 onwards only. Before March 2017 the export holds no minute data, and in 2017 and 2018 the spread column is empty, which would make trades almost free |
| Run | 2 November 2026, variant 1 of 1 |

The script reads the full export; the period was cut to 2019-2026 in a separate step before the run.

## Result

**73 trades in 1,929 test days.** That is below the 100 trades this method treats as enough for a firm verdict, so read everything below as a measurement with wide margins.

| | Measured | Claimed |
|---|---|---|
| Win rate | 31.5% | 60 to 80% |
| Mean net R per trade | −0.194 (90%: −0.340 to −0.046) | |
| Net R per month | median 0.0; 15 of 94 months positive | 5 to 10R |
| Mean R at 0 / 1 / 2 ticks slippage | −0.160 / −0.194 / −0.228 | |
| Exits | 24 stop, 19 target, 17 break-even, 13 session close | |
| Best 4 trades (top 5%) | +6.7R of a total of −14.1R | |

## Controls

| Control | Rule's percentile |
|---|---|
| Null A: same number of trades per day, picked at random from the valid level touches that day, random direction | 21.2 |
| Null B: fake levels shifted 5 to 15 points, same rules | 16.0 |
| Null C: same days and filter state, random time without a level | 0.0 |
| Null A0 ("the floor"): coin flip on every level touch | 0.0 (band −0.087 to +0.037) |

Against random picks among its own levels (Null A) and against fake levels (Null B), the system ranks below the middle, inside the range that chance produces. Against entering at a random time with the same filters but no level (Null C), it ranks below every run. The levels did not add anything measurable; if anything, they made it worse.

## By year

| Year | Trades | Win rate | Mean net R |
|---|---|---|---|
| 2019 | 3 | 33.3% | −0.312 |
| 2020 | 8 | 37.5% | −0.114 |
| 2021 | 8 | 37.5% | +0.072 |
| 2022 | 17 | 23.5% | −0.413 |
| 2023 | 10 | 20.0% | −0.270 |
| 2024 | 10 | 40.0% | −0.073 |
| 2025 | 7 | 28.6% | −0.519 |
| 2026 (to Oct) | 10 | 40.0% | +0.121 |

## Limitations

Fewer than 100 trades. A CFD volume profile measures tick volume, not traded futures volume, so the claim that these levels "must react" is tested on a proxy. The rules are my translation of a discretionary text; a different translation can give a different result. One broker, one instrument, one period, variant one of one.

This is a measurement, not a recommendation. Test it yourself and make your own judgment.
