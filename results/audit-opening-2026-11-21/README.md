# Audit of the opening time, 21 November 2026

## What was wrong

Six scripts took the opening minute of the US stock session (9:30 New York) from the data itself: the largest jump in tick volume at 15:30, 16:30 or 17:30 server time. The idea was to follow the weeks in which US and European daylight saving time differ. But the server of this broker runs on New York time + 7 all year, so the opening is always 16:30 server time. On days with economic releases at 8:30 New York (jobs, inflation) the volume jumps harder at 15:30, and the script took that as the opening, one hour too early.

Affected tests: Box Theory (`box-theory`), SPY at the open (`spy-opening`), 5-minute opening range breakout (`orb-5min`), UT Bot Alerts (`ut-bot`), 9 EMA + VWAP (`vwap-9ema`) and 9 EMA + VWAP with a prop firm challenge (`vwap-prop`).

## What was done

- In each script one line was changed: `OPEN_OFFSETS = (-60, 0, 60)` became `OPEN_OFFSETS = (0,)`, so the opening is fixed at 16:30 server time. Nothing else changed: same data, same seed, same settings. The changed copies are in `scripts/`.
- First the original scripts were run again on the same data. They reproduce the published numbers exactly (`old/`). The difference between `old/` and `new/` therefore comes only from the opening time.
- About 8% of the sessions moved (`shifted_days.txt`, from `count_shift.py`).
- On days where the opening did not move, the trades of Box Theory and the opening range breakout are identical before and after (`check_unshifted.txt`). In the two 9 EMA + VWAP tests some trades also change on the day after a moved day, because the EMA runs on from one session into the next.

## Result

No published verdict changes. Some numbers do.

| Test | Published | Fixed opening at 16:30 |
|---|---|---|
| Box Theory, Nasdaq 100, 2019 to Nov 2026 | 1,316 trades, 32.8%, −0.134R, percentile 0.2 | 1,293 trades, 32.3%, −0.157R, percentile 0.0 |
| Box Theory, from 22 May 2025 | 244 trades, −0.023R, percentile 77.0 | 236 trades, −0.062R, percentile 53.8 |
| Box Theory, S&P 500 | 1,337 trades, 36.7%, −0.103R, percentile 7.8 | 1,323 trades, 36.4%, −0.110R, percentile 4.7 |
| SPY at the open, share higher after 1 h / 2 h / close | 52.24% / 53.69% / 54.13% | 52.74% / 54.06% / 54.15% |
| SPY at the open, percentile against a random start, 1 h / 2 h | 88.6 / 89.9 | 93.9 / 84.6 |
| Opening range breakout, 2019 to Oct 2025 | 1,250 trades, 65.92%, −0.121R, percentile 18.7 | 1,290 trades, 66.28%, −0.118R, percentile 30.7 |
| Opening range breakout, after the post | 107 trades, 57.01%, −0.179R, percentile 4.2 | 108 trades, 61.11%, −0.122R, percentile 25.8 |
| UT Bot Alerts | 5,347 trades, 46.0%, −0.101R, percentile 47.2 | 5,349 trades, 46.5%, −0.096R, percentile 56.4 |
| 9 EMA + VWAP, S&P 500 | 5,850 trades, −0.689 point, percentile 82.2 | 5,797 trades, −0.711 point, percentile 70.9 |
| 9 EMA + VWAP, October 2026 (too few trades) | 65 trades, −0.360 point | 59 trades, +0.483 point |
| 9 EMA + VWAP, prop firm challenge | 799 trades, 32.5%, percentile 65.0; 9 of 95 passed (9.5%) | 797 trades, 32.2%, percentile 71.0; 9 of 92 passed (9.8%) |

Percentiles are against each test's own control group, as in the test's README. Full output in `old/` and `new/`. Each test's README has a note with its own numbers.

Tests that start later in this repository fix the opening at 16:30 from the start.

These are measurements of one rule in one period with one broker's data, not recommendations. Test it yourself and make your own judgement.
