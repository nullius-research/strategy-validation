# Datacontrole test G: alleen metadata (bars per dag, SPREAD-kolom, tijden), geen uitkomsten.
import sys, numpy as np, pandas as pd
f = sys.argv[1]
df = pd.read_csv(f, sep="\t")
df.columns = [c.strip("<>").lower() for c in df.columns]
ts = pd.DatetimeIndex(pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S"))
df.index = ts
dec = df["open"].astype(str).str.split(".").str[1].str.len().value_counts().head(3).to_dict()
print("rijen", len(df), "van", ts.min(), "tot", ts.max(), "decimalen zoals tekst (nul aan het eind valt weg):", dec)
d = ts.normalize(); m = ts.hour * 60 + ts.minute
bars_day = df.groupby(d).size()
first_m1 = bars_day[bars_day > 300].index.min()
print("eerste dag met >300 bars (echte M1):", first_m1.date())
print("jaar | dagen | bars/dag mediaan | spread nul % | spread mediaan (in 0,01) | sessiebars 16:30-23:00 mediaan")
for y, g in df.groupby(ts.year):
    gd = g.index.normalize(); gm = g.index.hour * 60 + g.index.minute
    rth = g[(gm >= 990) & (gm < 1380)]
    print(y, "|", gd.nunique(), "|", int(g.groupby(gd).size().median()), "|",
          round(100 * (g["spread"] == 0).mean(), 1), "|", g["spread"].median(), "|",
          int(rth.groupby(rth.index.normalize()).size().median()) if len(rth) else 0)
# opening: tickvolume-sprong rond 16:30 servertijd, toegestane verschuivingen -60, 0, +60
sub = df[ts >= first_m1]
offs = {}
for day, g in sub.groupby(sub.index.normalize()):
    v = pd.Series(g["tickvol"].values, index=(g.index.hour * 60 + g.index.minute)).reindex(range(1440)).fillna(0).values
    best, bo = -1e18, None
    for off in (-60, 0, 60):
        k = 990 + off
        j = v[k:k + 15].mean() - v[k - 15:k].mean()
        if j > best: best, bo = j, off
    offs[bo] = offs.get(bo, 0) + 1
print("opening gedetecteerd op verschuiving (min: dagen):", offs)
