import sys; sys.path.insert(0, '.')
import numpy as np, pandas as pd
import sr_breakout as s
s.COST = 0.0; s.COSTS = (0.0, 0.0, 0.0)
rng = np.random.default_rng(7); rows = []
for k in range(24):
    drift = 0.0 if k % 2 == 0 else 0.08
    days = pd.bdate_range("2014-01-01", periods=260 * 10)
    times = (days.values[:, None] + (np.arange(48) * np.timedelta64(30, "m"))[None, :]).ravel()
    nb = len(times); sub = 6
    sig = 0.15 / np.sqrt(260 * 48 * sub); mu = drift / (260 * 48 * sub)
    steps = rng.normal(mu - sig ** 2 / 2, sig, nb * sub)
    pp = 1000 * np.exp(np.cumsum(steps)).reshape(nb, sub)
    op = np.concatenate([[1000], pp[:-1, -1]])
    d = pd.DataFrame({"TIME": pd.to_datetime(times), "OPEN": op, "HIGH": np.maximum(pp.max(1), op), "LOW": np.minimum(pp.min(1), op), "CLOSE": pp[:, -1], "SPREAD": 0})
    P = s.prepare(d); mask = np.zeros(len(P["h1"]), bool); mask[1000:] = True
    o = s.evaluate(d, P, mask, np.random.default_rng(s.SEED + k), runs=500, verbose=False, seed=s.SEED + k)
    t = o["trades"]; r = t["R_NET"].to_numpy()
    h = P["h1"]["START"].dt.hour.to_numpy()[t["H1"].to_numpy()]
    rows.append((drift, o["mean"], o["nullA"][1], r.std(), np.mean(t["DIST"]/t["ATR"]), np.mean(h)))
df = pd.DataFrame(rows, columns=["drift", "rule_mean", "nullA_median", "rule_sd", "mult", "mean_hour"])
print(df.round(3).to_string())
print(df.groupby("drift").mean().round(4))
