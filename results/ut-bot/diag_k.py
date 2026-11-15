import numpy as np
from utbot_control import *
rng=np.random.default_rng(SEED_NOISE)
for s in range(2):
    m1=synth_m1(rng); b5,ind,nyc,sess,dayid=prepare(m1)
    tr,_=run_rule(ind,nyc,sess,dayid,0,len(b5))
    r=np.array([t[3] for t in tr]); g=np.array([t[4] for t in tr]); R=np.array([t[5] for t in tr])
    idx=np.arange(len(sess)); cand=idx[(idx>=30)&sess].astype(np.int64)
    st,ex,rr=precompute(cand,ind['o'],ind['h'],ind['l'],ind['c'],ind['sig'],ind['lo10'],ind['hi10'],ind['spread'],SLIP,nyc,dayid)
    c,o,sig=ind['c'][cand],ind['o'][cand],ind['sig'][cand]
    Rl=c-ind['lo10'][cand]; Rs=ind['hi10'][cand]-c
    ok=st==0
    print('set',s,'RULE: net %+.3f gross %+.3f medR %.1f pts | coin: net long %+.3f short %+.3f, medR %.1f'%(r.mean(),g.mean(),np.median(R),rr[0][ok[0]].mean(),rr[1][ok[1]].mean(),np.median(np.r_[Rl[ok[0]],Rs[ok[1]]])))
    fl=(c>o)&(c>sig)&ok[0]; fs=(c<o)&(c<sig)&ok[1]
    print('      filtered (colour+line): net long %+.3f short %+.3f medR %.1f | wrong side of line: net long %+.3f'%(rr[0][fl].mean(),rr[1][fs].mean(),np.median(np.r_[Rl[fl],Rs[fs]]),rr[0][ok[0]&(c<sig)].mean()))
