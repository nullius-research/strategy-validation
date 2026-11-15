import numpy as np, pandas as pd
df=pd.read_csv('USTEC_M1_201208060000_202611052200.csv',sep='\t'); df.columns=[c.strip('<>').lower() for c in df.columns]
df.index=pd.to_datetime(df.date+' '+df.time,format='%Y.%m.%d %H:%M:%S'); df=df[~df.index.duplicated()].sort_index()
b=df.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','spread':'last'}).dropna(subset=['open'])
o,h,l,c=b.open.values,b.high.values,b.low.values,b.close.values
tr=np.maximum(h-l,np.maximum(abs(h-np.r_[np.nan,c[:-1]]),abs(l-np.r_[np.nan,c[:-1]]))); tr[0]=h[0]-l[0]
ts=np.zeros(len(c)); p=0.0
for i in range(len(c)):
    q=c[i-1] if i else 0.0; nl=2*tr[i]
    ts[i]=max(p,c[i]-nl) if (c[i]>p and q>p) else (min(p,c[i]+nl) if (c[i]<p and q<p) else (c[i]-nl if c[i]>p else c[i]+nl)); p=ts[i]
lr=pd.Series(c).rolling(11).apply(lambda y:np.polyval(np.polyfit(np.arange(11),y,1),10),raw=True).values
sig=pd.Series(lr).rolling(7).mean().values
t=pd.read_csv('trades_P1.csv'); rng=np.random.default_rng(9)
for k in sorted(rng.choice(len(t),5,replace=False)):
    i=int(t.signal_bar[k]); d=int(t.dir[k])
    buy=c[i]>ts[i] and c[i-1]<=ts[i-1]; sell=c[i]<ts[i] and c[i-1]>=ts[i-1]
    filt=(c[i]>o[i] and c[i]>sig[i]) if d==1 else (c[i]<o[i] and c[i]<sig[i])
    e=c[i]; stop=l[i-9:i+1].min() if d==1 else h[i-9:i+1].max(); R=(e-stop)*d
    j=i+1
    while True:
        if d==1:
            if o[j]<=stop: px=o[j];break
            if l[j]<=stop: px=stop;break
            if c[j]<sig[j] and c[j]>e: px=c[j];break
        else:
            if o[j]>=stop: px=o[j];break
            if h[j]>=stop: px=stop;break
            if c[j]>sig[j] and c[j]<e: px=c[j];break
        j+=1
    net=d*(px-e)/R-(b.spread.values[i]*0.01+2)/R
    print(b.index[i],'dir',d,'UT signal',buy if d==1 else sell,'filter',filt,'exit',j,'vs',t.exit_bar[k],'netR %.4f vs %.4f'%(net,t.net_R[k]))
