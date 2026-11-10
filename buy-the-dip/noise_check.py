"""Noise check for the Null A control in buy_the_dip_test.py (added 10 Nov 2026).
24 synthetic daily random walks, 2,000 days each, 16% yearly volatility, drift 0% and 8%, seed 7.
Rule: no maximum hold, long, 2 bp. Null A as in buy_the_dip_test.py, 2,000 runs, seed 42 + set.
On data with no edge the rule should land evenly across the percentiles of its control.
Usage: python noise_check.py   (run from this folder)"""
import numpy as np, importlib.util, time
spec=importlib.util.spec_from_file_location("b","buy_the_dip_test.py"); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
rng=np.random.default_rng(7); out=[]
t0=time.time()
for s in range(24):
    drift=0.0 if s%2==0 else 0.08; sig=0.16/np.sqrt(252); mu=drift/252
    c=100*np.exp(np.cumsum(rng.normal(mu-sig**2/2,sig,2000)))
    t=b.run_rule(c,None,1); st=b.stats(c,t,1,2/1e4)
    pa=b.null_a(c,st["trades"],None,1,2/1e4,2000,np.random.default_rng(42+s))
    k,n=b.beat(st["pf"],pa); pct=100*k/n; out.append(pct)
    print(f"set {s:2d} drift {drift:.2f}: trades {st['trades']:4d} win {100*st['win']:5.1f}% PF {st['pf']:.2f}  NullA median {np.nanmedian(pa):.2f}  beat {k}/{n}  pct {pct:5.1f}",flush=True)
out=np.array(out)
print(f"\nmean percentile {out.mean():.1f}; above 95: {(out>95).sum()} of 24; below 5: {(out<5).sum()}; {time.time()-t0:.0f}s")
