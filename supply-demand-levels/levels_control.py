#!/usr/bin/env python3
"""
levels_control.py · Nullius Research
Meetscript bij hypothesis-v1.3-dutch.md (versie 1.1, 29-10-2026).

Gebruik:
    python levels_control.py <US500_M1.csv> [--rth 16:30-23:00] [--point 0.01]
                          [--n 10000] [--seed 19] [--out resultaten]

Invoer: M1-export uit MetaTrader 5 (Symbolen > Bars > Exporteren), tab-gescheiden,
kolommen <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>.
Ook een export via het Python-pakket MetaTrader5 (time, open, high, low, close,
tick_volume, spread) wordt gelezen.

Alle vaste keuzes staan bovenaan als constanten en komen 1-op-1 uit de hypothese.
Na de eerste run op echte data wordt hier niets meer aangepast.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- vaste keuzes
LOOKBACK = 20          # sessies voor VRVP en POC's
VRVP_ROWS = 200        # document
SVP_ROWS = 100         # document
HVN_PCT = 80           # high-volume node: bovenste 20 % van de rijen
LOCAL = 2              # lokaal maximum: >= alle rijen binnen ±2
POC_TOL = 5.0          # POC binnen 5 punten van de node
REJ_MOVE = 10.0        # rejection: minstens 10 punten weg van de zone
REJ_BARS = 12          # ... binnen 12 bars (5m)
ZONE_HALF = 4.0        # zone 8 punten breed
MERGE = 8.0            # levels dichter dan 8 punten: alleen de sterkste blijft
EMA_F, EMA_S = 34, 50  # cloud
SLOPE_BARS = 6         # EMA50 hoger/lager dan 6 bars eerder
FRACTAL = 2            # swingpunten: 2 bars links en rechts
MOM_BARS = 6           # cloud geraakt in de laatste 6 bars
BE_FRAC = 0.5          # stop naar break-even na 50 % van de afstand naar target
MIN_RISK = 4.0         # v1.2: geen trade als entry-stop < 4 punten (document: stop niet zo krap dat ruis je eruit haalt)
MIN_TRADES = 100       # vuistregel; minder = rapporteren als onvoldoende power
TICK = 0.25            # slippage-eenheid (punten)
SLIPS = (0, 1, 2)      # ticks slippage per kant
BASE_SLIP = 1
MIN_SESSION_FRAC = 0.9 # sessie telt mee bij >= 90 % van de verwachte M1-bars
SHIFTS = np.round(np.concatenate([np.arange(5.0, 15.0001, 0.25),
                                  -np.arange(5.0, 15.0001, 0.25)]), 2)


# ---------------------------------------------------------------- inlezen
def load_mt5(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        head = f.readline()
    sep = "\t" if "\t" in head else (";" if ";" in head else ",")
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    if "date" in df.columns:
        raw = df["date"].astype(str) + " " + df["time"].astype(str)
        ts = pd.to_datetime(raw, format="%Y.%m.%d %H:%M:%S", errors="coerce")
        if ts.isna().mean() > 0.5:
            ts = pd.to_datetime(raw, format="%Y.%m.%d %H:%M", errors="coerce")
    else:
        t = df["time"]
        ts = pd.to_datetime(t, unit="s") if np.issubdtype(t.dtype, np.number) else pd.to_datetime(t)
    vol = df["tickvol"] if "tickvol" in df.columns else df["tick_volume"]
    spread = df["spread"] if "spread" in df.columns else pd.Series(0, index=df.index)
    out = pd.DataFrame({"open": df["open"].astype(float).values,
                        "high": df["high"].astype(float).values,
                        "low": df["low"].astype(float).values,
                        "close": df["close"].astype(float).values,
                        "vol": vol.astype(float).values,
                        "spread": spread.astype(float).values},
                       index=pd.DatetimeIndex(ts, name="ts"))
    out = out[~out.index.isna()]
    out = out[~out.index.duplicated(keep="first")].sort_index()
    return out


# ---------------------------------------------------------------- datacontrole
def data_check(m1, rth_start, rth_end, point):
    rep = {}
    rep["rijen"] = int(len(m1))
    rep["van"] = str(m1.index[0])
    rep["tot"] = str(m1.index[-1])
    bad = ((m1["high"] < m1[["open", "close"]].max(axis=1)) |
           (m1["low"] > m1[["open", "close"]].min(axis=1))).sum()
    rep["bars_met_onmogelijke_ohlc"] = int(bad)
    ret = m1["close"].diff().abs()
    rep["grootste_m1_sprong_punten"] = float(ret.max())
    rep["moment_grootste_sprong"] = str(ret.idxmax())
    rep["spread_mediaan_punten"] = float(m1["spread"].median() * point)
    rep["spread_p95_punten"] = float(m1["spread"].quantile(0.95) * point)
    # Openingscontrole: minuut met de grootste tickvolume-sprong rond de verwachte opening
    minute = m1.index.hour * 60 + m1.index.minute
    win = (minute >= rth_start - 120) & (minute < rth_start + 120)
    sub = m1.loc[win, ["vol"]].copy()
    sub["min"] = minute[win]
    sub["day"] = sub.index.normalize()
    hits, total = 0, 0
    offsets = {}
    for _, g in sub.groupby("day"):
        v = g.set_index("min")["vol"].reindex(range(rth_start - 120, rth_start + 120)).fillna(0).values
        if v.sum() == 0:
            continue
        before = pd.Series(v).rolling(15).mean().shift(1).values
        after = pd.Series(v[::-1]).rolling(15).mean().values[::-1]
        jump = after - before
        k = int(np.nanargmax(jump)) + (rth_start - 120)
        total += 1
        d = k - rth_start
        offsets[d] = offsets.get(d, 0) + 1
        if abs(d) <= 2:
            hits += 1
    rep["opening_dagen_getoetst"] = total
    rep["opening_op_verwachte_minuut_pct"] = round(100 * hits / total, 1) if total else None
    top = sorted(offsets.items(), key=lambda x: -x[1])[:3]
    rep["opening_meest_voorkomende_afwijking_min"] = [{"afwijking": int(a), "dagen": int(b)} for a, b in top]
    return rep


# ---------------------------------------------------------------- hulpfuncties
def first_idx(mask):
    """Eerste index waar mask waar is, anders len(mask)."""
    if mask.size == 0:
        return 0
    i = int(np.argmax(mask))
    return i if mask[i] else mask.size


def profile(lo, hi, vol, rows):
    L, H = float(lo.min()), float(hi.max())
    if H <= L:
        return None
    rs = (H - L) / rows
    a = np.clip(((lo - L) / rs).astype(int), 0, rows - 1)
    b = np.clip(((hi - L) / rs).astype(int), 0, rows - 1)
    per = vol / (b - a + 1)
    diff = np.zeros(rows + 1)
    np.add.at(diff, a, per)
    np.add.at(diff, b + 1, -per)
    prof = np.cumsum(diff)[:rows]
    centers = L + (np.arange(rows) + 0.5) * rs
    return centers, prof


# ---------------------------------------------------------------- voorbereiding
class Market:
    def __init__(self, m1, rth_start, rth_end, point):
        self.point = point
        minute = m1.index.hour * 60 + m1.index.minute
        is_rth = (minute >= rth_start) & (minute < rth_end)
        expected = rth_end - rth_start

        # 5m en 1h over alle uren (zo staat de cloud op een grafiek)
        agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
        f5 = m1.resample("5min", label="left", closed="left").agg(agg).dropna()
        h1 = m1.resample("60min", label="left", closed="left").agg(agg).dropna()
        self.f5 = f5
        o5, hh5, ll5, c5 = (f5[c].values for c in ("open", "high", "low", "close"))
        e34 = f5["close"].ewm(span=EMA_F, adjust=False).mean().values
        e50 = f5["close"].ewm(span=EMA_S, adjust=False).mean().values
        bull5 = (e34 > e50) & (e50 > np.r_[np.full(SLOPE_BARS, np.nan), e50[:-SLOPE_BARS]])
        bear5 = (e34 < e50) & (e50 < np.r_[np.full(SLOPE_BARS, np.nan), e50[:-SLOPE_BARS]])

        h34 = h1["close"].ewm(span=EMA_F, adjust=False).mean().values
        h50 = h1["close"].ewm(span=EMA_S, adjust=False).mean().values
        hb = (h34 > h50) & (h50 > np.r_[np.full(SLOPE_BARS, np.nan), h50[:-SLOPE_BARS]])
        hs = (h34 < h50) & (h50 < np.r_[np.full(SLOPE_BARS, np.nan), h50[:-SLOPE_BARS]])
        h_close_t = h1.index + pd.Timedelta(minutes=60)
        f_close_t = f5.index + pd.Timedelta(minutes=5)
        # laatste afgesloten uurbar op het moment dat de 5m-bar sluit
        pos = np.searchsorted(h_close_t.values, f_close_t.values, side="right") - 1
        ok = pos >= 0
        bull1h = np.zeros(len(f5), bool)
        bear1h = np.zeros(len(f5), bool)
        bull1h[ok] = hb[pos[ok]]
        bear1h[ok] = hs[pos[ok]]

        # structuur: bevestigde fractals
        n5 = len(f5)
        last_sh = np.full(n5, np.nan); prev_sh = np.full(n5, np.nan)
        last_sl = np.full(n5, np.nan); prev_sl = np.full(n5, np.nan)
        a_sh = [np.nan, np.nan]; a_sl = [np.nan, np.nan]
        F = FRACTAL
        for i in range(n5):
            j = i - F
            if j - F >= 0:
                hj = hh5[j]
                if hj > hh5[j - F:j].max() and hj > hh5[j + 1:j + F + 1].max():
                    a_sh = [a_sh[1], hj]
                lj = ll5[j]
                if lj < ll5[j - F:j].min() and lj < ll5[j + 1:j + F + 1].min():
                    a_sl = [a_sl[1], lj]
            prev_sh[i], last_sh[i] = a_sh
            prev_sl[i], last_sl[i] = a_sl
        bull_st = (last_sh > prev_sh) & (last_sl > prev_sl)
        bear_st = (last_sh < prev_sh) & (last_sl < prev_sl)

        top = np.maximum(e34, e50); bot = np.minimum(e34, e50)
        touch_b = pd.Series(ll5 <= top).rolling(MOM_BARS, min_periods=1).max().values.astype(bool)
        touch_s = pd.Series(hh5 >= bot).rolling(MOM_BARS, min_periods=1).max().values.astype(bool)
        bull_mom = touch_b & (c5 > top)
        bear_mom = touch_s & (c5 < bot)

        warm = np.arange(n5) >= EMA_S * 3
        self.bull_ok = bull5 & bull1h & bull_st & bull_mom & warm
        self.bear_ok = bear5 & bear1h & bear_st & bear_mom & warm
        self.prev_close5 = np.r_[np.nan, c5[:-1]]
        self.h5, self.l5, self.c5 = hh5, ll5, c5
        self.filter_share = (float(self.bull_ok.mean()), float(self.bear_ok.mean()))

        # sessies (RTH)
        r = m1[is_rth]
        days = r.index.normalize()
        self.sessions = []
        f5_start = f5.index.values
        for d, g in r.groupby(days):
            if len(g) < MIN_SESSION_FRAC * expected:
                continue
            t = g.index.values
            i0 = np.searchsorted(f5_start, t[0], side="left")
            i1 = np.searchsorted(f5_start, t[-1], side="right")
            self.sessions.append({
                "day": pd.Timestamp(d),
                "t": t,
                "o": g["open"].values, "h": g["high"].values,
                "l": g["low"].values, "c": g["close"].values,
                "v": g["vol"].values, "sp": g["spread"].values * point,
                "i5": np.arange(i0, i1),
            })
        self.n_sessions = len(self.sessions)

    # -- levelkaart voor sessie k, alleen uit eerdere sessies
    def levels(self, k):
        prev = self.sessions[k - LOOKBACK:k]
        lo = np.concatenate([s["l"] for s in prev])
        hi = np.concatenate([s["h"] for s in prev])
        vo = np.concatenate([s["v"] for s in prev])
        res = profile(lo, hi, vo, VRVP_ROWS)
        if res is None:
            return np.array([])
        cen, prof = res
        thr = np.percentile(prof, HVN_PCT)
        cand = []
        for r in range(VRVP_ROWS):
            a, b = max(0, r - LOCAL), min(VRVP_ROWS, r + LOCAL + 1)
            if prof[r] >= thr and prof[r] >= prof[a:b].max() and prof[r] > 0:
                cand.append((cen[r], prof[r]))
        pocs = []
        for s in prev:
            p = profile(s["l"], s["h"], s["v"], SVP_ROWS)
            if p is not None:
                pocs.append(p[0][int(np.argmax(p[1]))])
        pocs = np.array(pocs)
        cand = [(c, v) for c, v in cand if pocs.size and np.min(np.abs(pocs - c)) <= POC_TOL]
        # rejection aan beide kanten, binnen elke sessie
        keep = []
        for c, v in cand:
            zt, zb = c + ZONE_HALF, c - ZONE_HALF
            up = dn = False
            for s in prev:
                idx = s["i5"]
                if idx.size < 2:
                    continue
                H, Lw, C = self.h5[idx], self.l5[idx], self.c5[idx]
                n = idx.size
                for b in range(1, n - 1):
                    if not up and C[b - 1] > zt and Lw[b] <= zt:
                        if H[b + 1:b + 1 + REJ_BARS].max() >= zt + REJ_MOVE:
                            up = True
                    if not dn and C[b - 1] < zb and H[b] >= zb:
                        if Lw[b + 1:b + 1 + REJ_BARS].min() <= zb - REJ_MOVE:
                            dn = True
                    if up and dn:
                        break
                if up and dn:
                    break
            if up and dn:
                keep.append((c, v))
        keep.sort(key=lambda x: -x[1])
        final = []
        for c, v in keep:
            if all(abs(c - f) >= MERGE for f in final):
                final.append(c)
        return np.array(sorted(final))

    # -- pad op M1 vanaf index k0
    def sim(self, s, k0, d, entry, stop, target):
        h, l, c = s["h"][k0:], s["l"][k0:], s["c"][k0:]
        n = h.size
        if n == 0:
            return None
        trig = entry + d * BE_FRAC * abs(target - entry)
        if d == 1:
            si, ti, bi = first_idx(l <= stop), first_idx(h >= target), first_idx(h >= trig)
        else:
            si, ti, bi = first_idx(h >= stop), first_idx(l <= target), first_idx(l <= trig)
        if si < n and si <= bi:
            x, px, kind = si, stop, "stop"
        elif bi < n:
            if ti == bi:
                x, px, kind = ti, target, "target"
            else:
                rest_h, rest_l = h[bi + 1:], l[bi + 1:]
                e = first_idx(rest_l <= entry) if d == 1 else first_idx(rest_h >= entry)
                e = bi + 1 + e
                if e < n and e <= ti:
                    x, px, kind = e, entry, "breakeven"
                elif ti < n:
                    x, px, kind = ti, target, "target"
                else:
                    x, px, kind = n - 1, c[-1], "slot"
        else:
            x, px, kind = n - 1, c[-1], "slot"
        return {"gross": (px - entry) * d, "risk": abs(entry - stop),
                "exit_k": k0 + x, "kind": kind, "exit_px": px}

    # -- kandidaten op een levelkaart
    def candidates(self, s, centers, mode):
        """mode 'real': eerste bar in de zone waarop het filter klopt.
           mode 'touch': eerste bar van elk bezoek, zonder filter (voor Null A)."""
        out = []
        if centers.size < 3:
            return out
        idx = s["i5"]
        H, Lw, C, PC = self.h5[idx], self.l5[idx], self.c5[idx], self.prev_close5[idx]
        BU, BE = self.bull_ok[idx], self.bear_ok[idx]
        t5 = self.f5.index.values[idx]
        for li in range(1, centers.size - 1):
            c = centers[li]
            zt, zb = c + ZONE_HALF, c - ZONE_HALF
            inz = (H >= zb) & (Lw <= zt)
            if not inz.any():
                continue
            starts = np.flatnonzero(inz & ~np.r_[False, inz[:-1]])
            for st in starts:
                en = st
                while en < inz.size and inz[en]:
                    en += 1
                if PC[st] > zt:
                    appr = 1
                elif PC[st] < zb:
                    appr = -1
                else:
                    continue
                if mode == "real":
                    okv = BU if appr == 1 else BE
                    hit = np.flatnonzero(okv[st:en])
                    if hit.size == 0:
                        continue
                    j = st + int(hit[0])
                    dirs = [appr]
                else:
                    j = st
                    dirs = [1, -1]
                close_t = t5[j] + np.timedelta64(5, "m")
                k0 = int(np.searchsorted(s["t"], close_t, side="left"))
                if k0 >= s["t"].size or k0 == 0:
                    continue
                entry = C[j]
                spread = s["sp"][k0 - 1]
                legs = {}
                for d in dirs:
                    if d == 1:
                        stop, target = (c + centers[li - 1]) / 2, centers[li + 1]
                        valid = stop < entry < target
                    else:
                        stop, target = (c + centers[li + 1]) / 2, centers[li - 1]
                        valid = target < entry < stop
                    if not valid or abs(entry - stop) < MIN_RISK:
                        continue
                    r = self.sim(s, k0, d, entry, stop, target)
                    if r is None:
                        continue
                    r.update(dir=d, entry=entry, stop=stop, target=target, level=c,
                             k0=k0, spread=spread, t_entry=close_t)
                    legs[d] = r
                if legs:
                    out.append({"k0": k0, "legs": legs})
        out.sort(key=lambda x: x["k0"])
        return out


def take_sequence(cands, rule="basis"):
    """Eén positie tegelijk; basis: stop na 1 winst of 2 verliezen (op bruto)."""
    busy, w, l, taken = -1, 0, 0, []
    for cd in cands:
        r = next(iter(cd["legs"].values()))
        if cd["k0"] <= busy:
            continue
        if rule == "basis" and (w >= 1 or l >= 2):
            break
        if rule == "een_per_dag" and taken:
            break
        taken.append(r)
        busy = r["exit_k"]
        if r["gross"] > 0:
            w += 1
        elif r["gross"] < 0:
            l += 1
    return taken


def net_r(t, slip_ticks):
    return (t["gross"] - t["spread"] - 2 * slip_ticks * TICK) / t["risk"]


def stats(trades, slip):
    if not trades:
        return {"n": 0}
    r = np.array([net_r(t, slip) for t in trades])
    return {"n": int(r.size), "winrate_pct": round(100 * float((r > 0).mean()), 1),
            "gem_netto_R": round(float(r.mean()), 4), "totaal_R": round(float(r.sum()), 2)}


def day_bootstrap(per_day_sum, per_day_n, rng, B=10000):
    D = per_day_sum.size
    idx = rng.integers(0, D, (B, D))
    s = per_day_sum[idx].sum(1)
    n = per_day_n[idx].sum(1)
    m = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    return float(np.nanpercentile(m, 5)), float(np.nanpercentile(m, 95))


# ---------------------------------------------------------------- hoofdprogramma
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--rth", default="16:30-23:00", help="reguliere sessie in servertijd")
    ap.add_argument("--point", type=float, default=0.01, help="puntgrootte voor de SPREAD-kolom")
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=19)
    ap.add_argument("--out", default="resultaten")
    a = ap.parse_args()
    hs, he = a.rth.split("-")
    rs = int(hs[:2]) * 60 + int(hs[3:5])
    re_ = int(he[:2]) * 60 + int(he[3:5])
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)

    m1 = load_mt5(a.csv)
    check = data_check(m1, rs, re_, a.point)
    print("== Datacontrole ==")
    for k, v in check.items():
        print(f"  {k}: {v}")

    mk = Market(m1, rs, re_, a.point)
    print(f"  sessies (RTH, >=90% compleet): {mk.n_sessions}")
    print(f"  aandeel 5m-bars met filter long/short: {mk.filter_share[0]:.3f} / {mk.filter_share[1]:.3f}")
    if mk.n_sessions <= LOOKBACK + 5:
        sys.exit("Te weinig sessies.")

    days = list(range(LOOKBACK, mk.n_sessions))
    D = len(days)
    real = {"basis": [], "geen_dagregel": [], "een_per_dag": []}
    real_by_day = []
    touch_by_day = []
    nb_A = np.zeros((D, SHIFTS.size)); nb_B = np.zeros((D, SHIFTS.size)); nb_N = np.zeros((D, SHIFTS.size))
    maps = []
    n_levels = []
    for di, k in enumerate(days):
        s = mk.sessions[k]
        cen = mk.levels(k)
        maps.append(cen)
        n_levels.append(cen.size)
        cands = mk.candidates(s, cen, "real")
        for rule in real:
            tk = take_sequence(cands, rule)
            for t in tk:
                t["day"] = s["day"]
                t["k"] = k
            real[rule].extend(tk)
            if rule == "basis":
                real_by_day.append(tk)
        touch_by_day.append(mk.candidates(s, cen, "touch"))
        for si, sh in enumerate(SHIFTS):
            tk = take_sequence(mk.candidates(s, cen + sh, "real"), "basis")
            for t in tk:
                nb_A[di, si] += (t["gross"] - t["spread"]) / t["risk"]
                nb_B[di, si] += 1.0 / t["risk"]
                nb_N[di, si] += 1
        if (di + 1) % 50 == 0:
            print(f"  ... {di + 1}/{D} dagen verwerkt")

    report = {"hypothese_versie": "1.1", "datacontrole": check, "sessies": mk.n_sessions,
              "testdagen": D, "min_risk_punten": MIN_RISK, "levels_per_dag_mediaan": float(np.median(n_levels)),
              "eerste_testdag": str(mk.sessions[days[0]]["day"].date()),
              "laatste_testdag": str(mk.sessions[days[-1]]["day"].date())}

    # ---------------- Null A: muntworp op dezelfde level-aanrakingen
    R = a.n
    A_A = np.zeros(R); B_A = np.zeros(R); N_A = np.zeros(R)
    dayA = np.zeros(D); dayB = np.zeros(D); dayN = np.zeros(D)
    for di, cands in enumerate(touch_by_day):
        busy = np.full(R, -1); w = np.zeros(R, int); l = np.zeros(R, int)
        a0 = A_A.copy(); b0 = B_A.copy(); n0 = N_A.copy()
        for cd in cands:
            coin = rng.integers(0, 2, R) * 2 - 1
            for d in (1, -1):
                if d not in cd["legs"]:
                    continue
                t = cd["legs"][d]
                take = (coin == d) & (cd["k0"] > busy) & (w < 1) & (l < 2)
                busy = np.where(take, t["exit_k"], busy)
                if t["gross"] > 0:
                    w += take
                elif t["gross"] < 0:
                    l += take
                A_A += take * ((t["gross"] - t["spread"]) / t["risk"])
                B_A += take * (1.0 / t["risk"])
                N_A += take
        dayA[di] = (A_A - a0).mean(); dayB[di] = (B_A - b0).mean(); dayN[di] = (N_A - n0).mean()

    # ---------------- Null A (v1.2, beslissend voor C2): zelfde aantal trades per dag als echt,
    # willekeurig gekozen uit de geldige level-aanrakingen van die dag, richting willekeurig
    A_M = np.zeros(R); B_M = np.zeros(R); N_M = np.zeros(R)
    for di, cands in enumerate(touch_by_day):
        kd = len(real_by_day[di])
        if kd == 0:
            continue
        pool = [((t["gross"] - t["spread"]) / t["risk"], 1.0 / t["risk"])
                for cd in cands for t in cd["legs"].values()]
        if not pool:
            continue
        pool = np.array(pool)
        p = rng.integers(0, len(pool), (R, kd))
        A_M += pool[p, 0].sum(1); B_M += pool[p, 1].sum(1); N_M += kd

    # ---------------- Null B: nep-levels (hele kaart verschoven)
    pick = rng.integers(0, SHIFTS.size, (R, D))
    rows = np.arange(D)[None, :]
    A_B = nb_A[rows, pick].sum(1); B_B = nb_B[rows, pick].sum(1); N_B = nb_N[rows, pick].sum(1)

    # ---------------- Null C: zelfde dag en richting, filter klopt, geen level
    base = real["basis"]
    tables = []
    for t in base:
        k = t["k"]
        s = mk.sessions[k]
        cen = maps[k - LOOKBACK]
        idx = s["i5"]
        okv = mk.bull_ok[idx] if t["dir"] == 1 else mk.bear_ok[idx]
        H, Lw, C = mk.h5[idx], mk.l5[idx], mk.c5[idx]
        free = np.ones(idx.size, bool)
        for c in cen:
            free &= ~((H >= c - ZONE_HALF) & (Lw <= c + ZONE_HALF))
        tab = []
        for j in np.flatnonzero(okv & free):
            close_t = mk.f5.index.values[idx[j]] + np.timedelta64(5, "m")
            k0 = int(np.searchsorted(s["t"], close_t, side="left"))
            if k0 >= s["t"].size or k0 == 0:
                continue
            e = C[j]
            r = mk.sim(s, k0, t["dir"], e, e - t["dir"] * t["risk"],
                       e + t["dir"] * abs(t["target"] - t["entry"]))
            if r:
                tab.append(((r["gross"] - s["sp"][k0 - 1]) / r["risk"], 1.0 / r["risk"]))
        tables.append(np.array(tab) if tab else None)
    A_C = np.zeros(R); B_C = np.zeros(R); N_C = np.zeros(R)
    for tab in tables:
        if tab is None:
            continue
        p = rng.integers(0, len(tab), R)
        A_C += tab[p, 0]; B_C += tab[p, 1]; N_C += 1

    # ---------------- uitkomst per kostenniveau
    def null_means(Ax, Bx, Nx, slip):
        return (Ax - 2 * slip * TICK * Bx) / np.maximum(Nx, 1)

    res_cost = []
    for slip in SLIPS:
        st = stats(base, slip)
        mean_real = st.get("gem_netto_R", np.nan)
        per_s = np.array([sum(net_r(t, slip) for t in tk) for tk in real_by_day])
        per_n = np.array([len(tk) for tk in real_by_day], float)
        lo, hi = day_bootstrap(per_s, per_n, rng)
        row = {"slippage_ticks_per_kant": slip, **st, "bootstrap90": [round(lo, 3), round(hi, 3)]}
        for name, (Ax, Bx, Nx) in {"A0": (A_A, B_A, N_A), "A": (A_M, B_M, N_M), "B": (A_B, B_B, N_B), "C": (A_C, B_C, N_C)}.items():
            m = null_means(Ax, Bx, Nx, slip)
            row[f"null{name}_mediaan"] = round(float(np.median(m)), 4)
            row[f"null{name}_band90"] = [round(float(np.percentile(m, 5)), 3), round(float(np.percentile(m, 95)), 3)]
            row[f"null{name}_p95"] = round(float(np.percentile(m, 95)), 4)
            row[f"percentiel_tegen_null{name}"] = round(100 * float((m < mean_real).mean()), 1)
        # C1: Null A over dagen, verwachte waarde
        dA = dayA - 2 * slip * TICK * dayB
        lo1, hi1 = day_bootstrap(dA, dayN, rng)
        row["nullA_dagbootstrap90"] = [round(lo1, 3), round(hi1, 3)]
        res_cost.append(row)
    report["per_kostenniveau"] = res_cost

    b = next(r for r in res_cost if r["slippage_ticks_per_kant"] == BASE_SLIP)
    report["varianten_basiskosten"] = {k: stats(v, BASE_SLIP) for k, v in real.items()}

    # maanden, jaren, verdeling (basiskosten)
    tr = pd.DataFrame([{**{k: v for k, v in t.items() if k not in ("legs",)},
                        "netto_R": net_r(t, BASE_SLIP)} for t in base])
    all_months = pd.period_range(mk.sessions[days[0]]["day"], mk.sessions[days[-1]]["day"], freq="M")
    if len(tr):
        tr["maand"] = pd.to_datetime(tr["day"]).dt.to_period("M")
        tr["jaar"] = pd.to_datetime(tr["day"]).dt.year
        per_m = tr.groupby("maand")["netto_R"].sum().reindex(all_months, fill_value=0.0)
        per_y = tr.groupby("jaar").agg(n=("netto_R", "size"), gem_netto_R=("netto_R", "mean"),
                                       winrate=("netto_R", lambda x: 100 * (x > 0).mean()))
        r = np.sort(tr["netto_R"].values)[::-1]
        k5 = max(1, int(np.ceil(0.05 * r.size)))
        report["netto_R_per_maand"] = {str(k): round(float(v), 2) for k, v in per_m.items()}
        report["maand_mediaan_R"] = round(float(per_m.median()), 2)
        report["per_jaar"] = {str(k): {"n": int(v.n), "gem_netto_R": round(float(v.gem_netto_R), 4),
                                       "winrate_pct": round(float(v.winrate), 1)} for k, v in per_y.iterrows()}
        report["beste_5pct_trades"] = {"aantal": k5, "som_R": round(float(r[:k5].sum()), 2),
                                       "totaal_R": round(float(r.sum()), 2),
                                       "totaal_zonder_beste_5pct": round(float(r[k5:].sum()), 2)}
        report["exit_soorten"] = tr["kind"].value_counts().to_dict()
        tr.drop(columns=["maand"]).to_csv(os.path.join(a.out, "trades_basis.csv"), index=False)
    else:
        report["maand_mediaan_R"] = 0.0

    # ---------------- oordeel per claim (basiskosten), volgens sectie 6
    v = {}
    v["C1_muntworp_break_even"] = ("GEFALSIFIEERD" if b["nullA_dagbootstrap90"][1] < 0 else "niet gefalsifieerd")
    c2_fail = (b.get("gem_netto_R", -9) <= b["nullA_p95"]) or (b.get("winrate_pct", 0) < 60)
    v["C2_filter_60_80pct"] = "GEFALSIFIEERD" if c2_fail else "niet gefalsifieerd"
    v["C3_5_10R_per_maand"] = "GEFALSIFIEERD" if report["maand_mediaan_R"] < 5 else "niet gefalsifieerd"
    c4_fail = b.get("gem_netto_R", -9) <= b["nullB_p95"]
    v["C4_levels_moeten_reageren"] = "GEFALSIFIEERD" if c4_fail else "niet gefalsifieerd"
    nr = report["varianten_basiskosten"]["geen_dagregel"].get("gem_netto_R", -9)
    v["C5_dagregel_helpt"] = ("GEFALSIFIEERD" if nr >= b.get("gem_netto_R", -9) else "niet gefalsifieerd")
    v["systeem_dood_volgens_stap5"] = c2_fail and c4_fail
    v["voldoende_trades"] = b.get("n", 0) >= MIN_TRADES
    report["oordeel"] = v

    with open(os.path.join(a.out, "rapport.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n== Uitkomst (basis: 1 tick slippage per kant + spread uit de data) ==")
    for r in res_cost:
        print(f"  slip {r['slippage_ticks_per_kant']}: n={r.get('n')} winrate={r.get('winrate_pct')}% "
              f"gem={r.get('gem_netto_R')}R boot90={r['bootstrap90']} | "
              f"pct A={r['percentiel_tegen_nullA']} B={r['percentiel_tegen_nullB']} C={r['percentiel_tegen_nullC']} | "
              f"NullA dag90={r['nullA_dagbootstrap90']}")
    print("  varianten:", report["varianten_basiskosten"])
    print("  maand-mediaan R:", report.get("maand_mediaan_R"))
    print("\n== Oordeel ==")
    for k, x in v.items():
        print(f"  {k}: {x}")
    print(f"\nRapport: {os.path.join(a.out, 'rapport.json')}")


if __name__ == "__main__":
    main()
