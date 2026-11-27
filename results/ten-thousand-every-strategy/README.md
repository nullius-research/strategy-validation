# $10,000 test account in every strategy tested

Null Test 24 · 27 November 2026 · Nullius Research

A recalculation, not a new test. The published trades of 22 earlier tests are turned into dollars in one equal way, to show what would be left of a $10,000 **test account** per strategy. Hypothetical accounts, not real money and not a return.

## Plan (fixed before the calculation)

The binding plan is in Dutch: `rekenplan-10k-v1.0.md` (fixed before any dollar amount was calculated) and `rekenplan-10k-v1.1.md`.

| Item | Rule |
|---|---|
| Start | $10,000 per strategy, a separate account for each |
| Tests with a stop (results in R) | Fixed $100 risk per trade (1% of the start), no compounding. End = $10,000 + $100 × sum of net R |
| Tests without a stop (results in % or points) | A $10,000 position per trade, no compounding. Profit = $10,000 × net return of the trade |
| Period | Each test's own decisive period, as published |
| Costs | As in each test's published decisive result |
| Opening-time audit | Tests G, H, K, N and O use the corrected trades from `results/audit-opening-2026-11-21/new/` |
| **v1.1, added after run 01** | An account that reaches $0 or less stops: end $0, later trades do not count. Added because five accounts in run 01 traded on below zero. Run 01 stays here unchanged |

Files, columns and selections per test: section 3 of the plan.

## Reproduction first

`repro.py` recomputes, per test, the number of trades and the average in its own unit, and prints them next to the published numbers. All 22 match (`repro.txt`).

## Result (run 02, plan v1.1)

22 accounts, $220,000 in. **$229,782 left.** Six accounts reached zero, ten ended above $10,000 (`run02_v1.1.txt`).

The largest account, volume breakout ($44,004), scored a percentile of 27 against random entry dates on the same stocks: random dates did better most of the time. Its money came from stocks going up, not from the rule. Without it, the other 21 accounts turn $210,000 into $185,778.

Five of the 22 strategies beat their own control at 95 or higher. Two of those have fewer than 100 trades. **Making money and beating chance are not the same thing.**

Run 01 (plan v1.0, no stop at zero): $173,604, with five accounts below zero (`run01.txt`).

## Run it

From `results/`: `python3 ten-thousand-every-strategy/repro.py` and `python3 ten-thousand-every-strategy/ten_thousand.py out.csv`. Needs pandas and numpy; reads only trade files that are already in this repository.

## Limitations

Different tests cover different periods and markets, so the dollar amounts are not fully comparable. Fixed $100 risk without compounding is one choice of many; other sizing gives other amounts. The amounts say nothing about beating chance; only the percentiles in each test's README do.

Research only. Not financial advice. This is a measurement, not a recommendation. Test it yourself and make your own judgment.
