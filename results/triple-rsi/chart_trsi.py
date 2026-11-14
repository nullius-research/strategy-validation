import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import triple_rsi_control as t
plt.rcParams["font.family"] = "Inter"
BG, FG, MUTED, GREEN, RED, GRID, NUL, IN = "#12161C", "#F2F0EB", "#8A8F98", "#39FF7A", "#FF2B2B", "#2A3038", "#4A515C", "#9B7BFF"

def nullA(csvf, start, seed=37, runs=10000):
    d, c = t.load(csvf); lo = int(np.searchsorted(d, start)) if start else 0; hi = len(d) - 1
    rng = np.random.default_rng(seed); rsi, ma = t.rsi_wilder(c), t.sma(c)
    tr, _ = t.rule_trades(c, rsi, ma, lo, hi); r = t.rets(c, tr, 0.0002)
    durs = np.array([j - i for i, j, _ in tr]); days = np.arange(max(lo, t.WARMUP), hi + 1); el = days[c[days] > ma[days]]
    m, _ = t.null_means("A", c, rsi, el, len(tr), durs, 0.0002, runs, rng)
    return m * 100, r.mean() * 100, len(tr), t.pct(r.mean(), m)

panels = [("SPY, 1994-2026", *nullA("SPY_yahoo_D1_1993_2026.csv", None), GREEN),
          ("S&P 500 index, 1950-1993", *nullA("GSPC_yahoo_D1_1948_1993.csv", "1950-01-03"), RED)]
for p in panels: print(p[0], p[3], round(p[2], 3), round(p[4], 1), np.round(np.percentile(p[1], [5, 50, 95]), 3))
fig, axes = plt.subplots(1, 2, figsize=(12, 6.3), dpi=100); fig.patch.set_facecolor(BG)
bins = np.linspace(-0.6, 1.5, 43)
for ax, (title, m, rule, n, pc, col) in zip(axes, panels):
    ax.set_facecolor(BG); h, e = np.histogram(m, bins=bins); p5, p95 = np.percentile(m, [5, 95])
    for i in range(len(h)):
        mid = (e[i] + e[i+1]) / 2
        ax.bar(mid, h[i], width=(e[1]-e[0])*0.9, color=IN if p5 <= mid <= p95 else NUL, zorder=3)
    ax.axvline(rule, color=col, lw=4, zorder=4)
    right = rule > 0.7
    ax.text(rule - 0.04 if right else 0.84, h.max()*1.12, f"The rule\n{rule:+.2f}% per trade\npercentile {pc:.1f}", color=col, fontsize=15, fontweight="bold", ha="right" if right else "left", va="top")
    ax.set_ylim(0, h.max()*1.15)
    ax.set_xlim(-0.6, 1.5)
    ax.set_xticks([-0.5, 0, 0.5, 1.0, 1.5]); ax.set_xticklabels(["-0.5%", "0%", "+0.5%", "+1.0%", "+1.5%"], color=MUTED, fontsize=12)
    ax.set_yticks([]); ax.grid(axis="x", color=GRID, lw=0.8, zorder=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(f"{title}, {n} trades", color=FG, fontsize=15, loc="left", pad=8)
fig.text(0.04, 0.93, "Triple RSI: rule vs 10,000 random entries", color=FG, fontsize=22, fontweight="bold")
fig.text(0.04, 0.875, "Random entries: days above the 200-day average, same holding times, same number of trades. Purple: middle 90%.", color=MUTED, fontsize=12)
fig.text(0.5, 0.05, "Mean net return per trade, 2 bp costs in", color=MUTED, fontsize=12, ha="center")
fig.text(0.97, 0.02, "Nullius Research", color=MUTED, fontsize=11, ha="right")
plt.subplots_adjust(left=0.03, right=0.97, top=0.76, bottom=0.14, wspace=0.08)
fig.savefig("triple-rsi-vs-random-1200x630.png", facecolor=BG)
