# Video B: $10.000 per geteste strategie. Rekenplan v1.1 (regel 2a: rekening stopt bij $0). Eerder: v1.0. Draai vanuit strategy-validation/results.
import pandas as pd, numpy as np, json, sys
A='audit-opening-2026-11-21/new/'; rd=pd.read_csv
def tcol(d,c): return pd.to_datetime(d[c].astype(str).str[:19],errors='coerce')
T={}
def add(key,label,period,df,tc,dollars,kind):
    d=pd.DataFrame({'t':tcol(df,tc).values,'usd':np.asarray(dollars,float)}).sort_values('t',kind='stable')
    T[key]=(label,period,d,kind)
R=lambda x: 100*np.asarray(x,float)          # $100 per R
P=lambda x: 10000*np.asarray(x,float)        # $10.000 positie x rendement (fractie)
a=rd('macd-200ema/macd_trades.csv'); add('A','MACD + 200 EMA','Aug 2022 - Aug 2026',a,'ENTRY_TIME',R(a['NET_1.2']),'R')
b=rd('stoch-rsi-macd/srm_trades.csv'); b=b[b.PAIR=='EURUSD']; add('B','Stochastic + RSI + MACD','Aug 2022 - Aug 2026',b,'ENTRY_TIME',R(b['NET_1.2']),'R')
c=rd('macd-atr/macdatr_trades.csv'); c=c[(c.period=='T')&(c.signal=='MACD Line ZC')]; add('C','MACD + ATR','Aug 2020 - Nov 2026',c,'entry_date',R(c.R),'R')
d=rd('bollinger-200ema/bb200_trades_eurusd.csv'); add('D','Bollinger + 200 EMA','Aug 2022 - Aug 2026',d,'ENTRY_TIME',R(d['NET_1.2']),'R')
e=rd('rsi2-pullback/trades_P1_sp500.csv'); add('E','RSI(2) pullback','2007 - Oct 2026',e,'entry_date',P(e.net_return),'pos')
f=rd('ma-9-21-gold/trades_P1_decisive.csv'); add('F','MA 9/21 + 200 MA gold','2017 - 2026 (P1)',f,'ENTRY_TIME',R(f.R_NET),'R')
g=rd(A+'G_P1/trades.csv'); add('G','Box Theory','2019 - Nov 2026',g,'day',R(g.net_r),'R')
h=rd(A+'H_P1/trades.csv'); add('H','5-min opening range breakout','2019 - Oct 2025',h,'day',R(h.net_r),'R')
i=rd('triple-rsi/trades_P1.csv'); add('I','Triple RSI','1994 - Sep 2026',i,'entry_date',P(i.net_return),'pos')
k=rd(A+'K/trades_P1.csv'); add('K','UT Bot Alerts','2018 - Nov 2026',k,'signal_time',R(k.net_R),'R')
l=rd('structured-entry/trades_G_P1.csv'); add('L','Structured entry (Bitcoin)','Feb 2019 - Nov 2026',l,'start_time',P(l.result_pct/100),'pos')
m=rd('supertrend-200ema/trades_m30.csv'); add('M','Supertrend + 200 EMA','Aug 2022 - Aug 2026',m,'ENTRY_TIME',R(m['NET_1.2']),'R')
n=rd(A+'N_us500/trades_US500.csv'); add('N','9 EMA + VWAP','2019 - Oct 2026',n,'day',P(n.net/n.entry),'pos')
o=rd(A+'O_rth/trades_USTEC_rth_firm_a.csv'); add('O','9 EMA + VWAP, prop firm','Nov 2023 - Nov 2026',o,'day',P(o.net/o.entry),'pos')
p=rd('sr-breakout/trades_P1_decisive.csv'); add('P','Support & resistance breakout','Jun 2017 - 2024',p,'ENTRY_TIME',R(p.R_NET),'R')
q=rd('morning-star-gold/trades_P1_decisive.csv'); add('Q','Morning star gold','Nov 2021 - Nov 2026',q,'ENTRY_TIME',R(q.R_NET),'R')
r=rd('noise-area-momentum/trades_ustec.csv'); add('R','Noise-area momentum','2020 - Nov 2026',r,'day',P((r.gross-r.spread-2)/r.entry),'pos')
s=rd('prev-day-sweep/trades_ustec_p1.csv'); add('S','Previous-day sweep','2020 - Oct 2026',s,'entry_time_server',R(s.R),'R')
lc=rd('supply-demand-levels/trades.csv'); add('LCE','Supply-demand levels','2019 - Oct 2026',lc,'day',R(lc.netto_R),'R')
bb=rd('bollinger-reversion/bb_multi_trades.csv'); add('BB','Bollinger reversion','Aug 2022 - Aug 2026',bb,'Date',R(bb.real_R),'R')
vb=rd('volume-breakout/trades.csv'); add('VB','Volume breakout','2016 - Aug 2026',vb,'date',R(vb.r),'R')
bd=rd('buy-the-dip/trades.csv'); bd=bd[bd.entry_date>='2024-01-01']; add('BTD','Buy the dip','Jan 2024 - Sep 2026',bd,'entry_date',P(bd.net_return_2bp),'pos')
rows=[]
for key,(label,per,d,kind) in T.items():
    assert d.t.notna().all(), key
    bal=10000+d.usd.cumsum().values
    hit=np.where(bal<=0)[0]
    if len(hit):
        j=hit[0]; blown=str(d.t.iloc[j].date()); blown_n=int(j+1); bal=bal[:j+1]; bal[-1]=0.0
    else: blown=''; blown_n=0
    low=min(10000,bal.min()); end=bal[-1]
    rows.append(dict(key=key,label=label,period=per,trades=len(d),kind=kind,end=round(end,0),low=round(low,0),blown=blown,blown_trade=blown_n,
        best_trade=round(d.usd.max(),0),worst_trade=round(d.usd.min(),0),too_few=len(d)<100))
out=pd.DataFrame(rows)
tot=out.end.sum(); n=len(out)
print(out.to_string(index=False)); print(f'\n{n} rekeningen, ingelegd ${n*10000:,.0f}, over ${tot:,.0f}; boven 10.000: {(out.end>10000).sum()}')
out.to_csv(sys.argv[1] if len(sys.argv)>1 else 'b10k_result.csv',index=False)
