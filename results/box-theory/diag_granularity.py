# Diagnose 11 nov 2026: bias regel min spiegel op ruis bij K substappen per minuut. Gebruik: PYTHONPATH=. python3 diag_granularity.py K sets seed
import numpy as np, pandas as pd, sys, box_control as b
def synth(rng,K,years=5,start_price=15000.0,vol_year=0.20):
    n_days=years*252; var_day=vol_year**2/252
    mins=np.arange(60,1440); in_rth=(mins>=b.RTH_START)&(mins<b.RTH_START+b.RTH_LEN)
    var_min=np.where(in_rth,0.7*var_day/b.RTH_LEN,0.3*var_day/(len(mins)-b.RTH_LEN))
    sd=np.sqrt(var_min/K); logp=np.log(start_price); days=[]
    for day in pd.bdate_range("2010-01-04",periods=n_days):
        path=logp+np.cumsum((rng.standard_normal((len(mins),K))*sd[:,None]).ravel()).reshape(len(mins),K)
        pc=np.r_[logp,path[:-1,-1]]
        days.append({"day":day,"min":mins,"o":np.exp(pc),"c":np.exp(path[:,-1]),"h":np.exp(np.maximum(path.max(1),pc)),"l":np.exp(np.minimum(path.min(1),pc)),"v":np.where(in_rth,100.,20.),"sp":np.full(len(mins),1.)})
        logp=path[-1,-1]
    return days
K=int(sys.argv[1]); S=int(sys.argv[2]); rng=np.random.default_rng(int(sys.argv[3]))
d=[]
for s in range(S):
    df,_=b.run_rule(synth(rng,K),10.0); d.append(((df.gross-df.gross_opp)/df.risk).values)
d=np.concatenate(d); print(K,'n',len(d),'mean rule-opp',d.mean().round(4),'se',(d.std()/np.sqrt(len(d))).round(4))
