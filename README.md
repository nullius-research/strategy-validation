# strategy-validation
Control-group testing for trading strategy ideas. Python.

Four Python scripts that answer one question: **does this signal beat a null version of itself?**

Not "is it profitable". A strategy can be profitable in a sample and still contain no information. The relevant test is whether it outperforms a control taken at the same moments, with the same stop, the same target and the same costs. If it does not, any profit in the sample is a fortunate draw.

These were written to test three specific ideas. All three failed. The scripts are published because the method generalises even though the results did not.

## Why bother

Three things go wrong in most retail backtests, and each of them is enough on its own to produce a system that looks profitable and is not.

**No costs.** Spread and commission are a fixed tax on every trade. A strategy with a 20 pip stop and a 1.2 pip round-trip cost gives up 6% of every position before it starts.

**Extremes instead of order.** Maximum favourable and adverse excursion tell you how far price moved in each direction, not which came first. A trade that reached 2.0R of profit and 1.2R of loss is a winner or a loser depending entirely on sequence. Every script here walks the bars forward and records the first touch. Where a single bar spans both stop and target, it is scored as a stop. That bias is deliberate and works against the strategy.

**No control.** This is the big one. There are thousands of possible rules and millions of moments to apply them to, so some rule always looks good in hindsight. Without a null comparison you cannot tell a signal from a lucky sample.

## The scripts

| File | What it tests | Control used |
|---|---|---|
| `asian_range_study.py` | Overnight range breakout. Reports MFE and MAE distributions split by range compression. | None. Superseded by v2, kept because the MFE/MAE split is still a useful first look. |
| `asian_range_study2.py` | Same idea, with first-touch path simulation and costs. | Direction assigned by coin flip at the same moment, resampled 2,000 times. |
| `bb_reversion_study.py` | Bollinger band mean reversion on one instrument. Signals on H1, paths walked on M15. | The momentum version. Same moment, same stop, same target distance, opposite direction. |
| `bb_reversion_multi.py` | Same, pooled across a basket of pairs. | Same, plus a cluster bootstrap that resamples whole trading days. |

### On the cluster bootstrap

FX majors share a common dollar factor. Three pairs breaking their bands on the same day is one bet, not three. Resampling individual trades would produce a narrow and dishonest confidence interval, so `bb_reversion_multi.py` resamples entire trading days with every symbol kept together. This is why it reports the number of distinct trading days alongside the number of trades. The day count is the one that tells you how much you actually know.

## Requirements

```
pip install pandas numpy
```

Python 3.10 or later. Nothing else, and no network access at runtime.

## Data

MT5 M15 exports. In MetaTrader 5: `View > Symbols (Ctrl+U) > select symbol > Bars tab > set timeframe and range > Request > Export`.

The expected format is tab separated with an MT5-style header:

```
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>
```

For the multi-symbol script, put one CSV per pair in a single folder. The symbol is read from the start of the filename, and JPY crosses are detected automatically for pip sizing.

## Usage

```
python asian_range_study2.py --file EURUSD_M15.csv --broker-offset 2
python bb_reversion_multi.py --dir ./data --cost-pips 1.2
```

`--broker-offset` is your server's **winter** offset from UTC in hours. Most EU brokers run EET, so that is 2. The scripts apply the US daylight saving schedule on top, which is the convention FX brokers follow.

**Check the hourly volatility profile that `asian_range_study.py` prints before trusting anything else.** It shows mean bar range per UTC hour. For EURUSD you should see a dip during the Asian afternoon around 03:00 to 04:00, a step up at the London open around 07:00, and the largest values during the New York overlap at 13:00 to 15:00. If your profile does not look like that, the offset is wrong and every number below it is meaningless.

Getting session boundaries wrong by an hour for eight months of the year is the quietest way to destroy a session-based study, which is why the check is printed first.

## Reading the output

Look at the control before anything else. If the real result sits inside the control band, stop reading. The table above it does not matter.

Then check the sample size. Below roughly 100 observations per subgroup, differences between subgroups are not interpretable regardless of how large they look.

Then check the cost column against the median stop distance in pips. A filter that steers you toward tighter stops is also steering you toward worse cost ratios, and that trade-off is easy to miss.

## Limitations

Single broker, single data source, and the tests these were built for covered four years, which is one to two regimes rather than a full cycle. Costs are a fixed assumption rather than modelled from historical spread, because MT5 bar exports report minimum spread per bar, which is frequently zero.

The scripts test whether a signal carries information. They do not simulate a portfolio, position sizing, correlation limits, or execution. A signal that passes here still needs all of that before it becomes a system.

## Results

Trade logs and summaries per test, so every number we publish can be checked.

| Test | Folder |
|---|---|
| Bollinger band reversion, 9 FX majors, 790 trades | [`results/bollinger-reversion`](results/bollinger-reversion/) |

## Licence

MIT. Use it, change it, no attribution required.

If you find an error in the method, open an issue. Corrections are more useful than stars.

## Not financial advice!

Nothing here is financial advice or a recommendation to trade. These are measurement tools, and the measurements they produced were negative!
