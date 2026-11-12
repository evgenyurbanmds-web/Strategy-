"""BTCUSDT trend-pullback v1, research only; no orders.
CSV columns: time (UTC),open,high,low,close,volume; contiguous 5m candles.
Run: python -m backtests.trend_pullback --csv data/btc_5m.csv
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd

def prepare(d):
    d=d.sort_values('time').reset_index(drop=True).copy()
    d['time']=pd.to_datetime(d.time,utc=True)
    if d.time.duplicated().any() or not (d.time.diff().dropna()==pd.Timedelta(minutes=5)).all(): raise ValueError('5m data gaps or duplicates')
    for n in (20,50):d['ema'+str(n)]=d.close.ewm(span=n,adjust=False,min_periods=n).mean()
    prev=d.close.shift()
    tr=pd.concat([d.high-d.low,(d.high-prev).abs(),(d.low-prev).abs()],axis=1).max(axis=1)
    d['atr']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h=d.set_index('time').resample('1h',closed='left',label='right').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    for n in (50,200):h['ema'+str(n)]=h.close.ewm(span=n,adjust=False,min_periods=n).mean()
    up=h.high.diff();dn=-h.low.diff();prev=h.close.shift()
    trh=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    atrh=trh.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    pdi=100*up.where((up>dn)&(up>0),0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atrh
    mdi=100*dn.where((dn>up)&(dn>0),0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atrh
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    adx=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h['trend']=np.select([(h.ema50>h.ema200)&(h.close>h.ema50)&(adx>25)&(pdi>mdi),(h.ema50<h.ema200)&(h.close<h.ema50)&(adx>25)&(mdi>pdi)],[1,-1],0)
    times=d[['time']].copy();times['known_at']=times.time+pd.Timedelta(minutes=5)
    d['trend']=pd.merge_asof(times,h[['trend']].reset_index(),left_on='known_at',right_on='time',direction='backward').trend.fillna(0).astype(int).values
    return d

def run(d,period,capital=10000):
    cash=capital;pos=None;pending=None;trades=[];curve=[]
    for i in range(len(d)):
        b=d.iloc[i];side=int(b.trend)
        if pending:
            s,stop,signal=pending;pending=None
            if i==signal+1:
                entry=float(b.open)*(1+s*.0005);dist=s*(entry-stop)
                if dist>0 and cash>0:
                    qty=min(cash*.01/dist,cash/entry)
                    if qty>0:
                        cash-=qty*entry*.001
                        pos=dict(side=s,stop=stop,entry=entry,qty=qty,target=entry+s*2*dist,at=i,when=b.time)
        if pos:
            p=pos;s=p['side'];stop=p['stop'];target=p['target']
            sh=(b.low<=stop if s==1 else b.high>=stop)
            th=(b.high>=target if s==1 else b.low<=target)
            reason=None
            if sh:price=min(b.open,stop) if s==1 else max(b.open,stop);reason='stop'
            elif th:price=target;reason='target'
            elif i-p['at']>=48:price=b.close;reason='timeout'
            elif i==len(d)-1:price=b.close;reason='end'
            if reason:
                exit=float(price)*(1-s*.0005)
                pnl=s*(exit-p['entry'])*p['qty']-p['qty']*(p['entry']+exit)*.001
                cash+=s*(exit-p['entry'])*p['qty']-p['qty']*exit*.001
                trades.append(dict(entry_time=str(p['when']),exit_time=str(b.time),side=s,net_pnl=pnl,reason=reason))
                pos=None
        eq=cash if pos is None else cash+pos['side']*(b.close-pos['entry'])*pos['qty']-pos['qty']*b.close*.001
        curve.append((b.time,eq))
        if pos or pending or i<2500 or i>=len(d)-1 or side==0 or not np.isfinite(b.atr):continue
        prev=d.iloc[i-1];window=d.iloc[i-3:i]; ema='ema'+str(period)
        if side==1:
            touch=(window.low<=window[ema]).any()
            confirm=b.close>b.ema20 and b.close>prev.high and b.close>b[ema]
            stop=float(d.iloc[i-3:i+1].low.min()-.2*b.atr)
        else:
            touch=(window.high>=window[ema]).any()
            confirm=b.close<b.ema20 and b.close<prev.low and b.close<b[ema]
            stop=float(d.iloc[i-3:i+1].high.max()+.2*b.atr)
        if touch and confirm:pending=(side,stop,i)
    e=pd.DataFrame(curve,columns=['time','equity']);t=pd.DataFrame(trades)
    dd=float((e.equity/e.equity.cummax()-1).min()*100)
    annual=[]
    for year,g in e.groupby(e.time.dt.year):
        previous=e[e.time.dt.year<year]
        base=capital if previous.empty else float(previous.equity.iloc[-1])
        x=d[d.time.dt.year==year]
        subset=t[pd.to_datetime(t.exit_time,utc=True).dt.year==year] if not t.empty else t
        annual.append(dict(year=int(year),trades=len(subset),strategy_pct=100*(float(g.equity.iloc[-1])/base-1),buy_hold_pct=100*(x.close.iloc[-1]/x.close.iloc[0]-1),realized_pnl=float(subset.net_pnl.sum()) if not subset.empty else 0))
    return dict(ema=period,trades=len(t),net_profit=cash-capital,return_pct=100*(cash/capital-1),max_dd_pct=dd,buy_hold_pct=100*(d.close.iloc[-1]/d.close.iloc[0]-1),annual=annual),t,e

def main():
    p=argparse.ArgumentParser();p.add_argument('--csv',required=True);p.add_argument('--out',default='reports/trend_pullback');a=p.parse_args()
    d=pd.read_csv(a.csv);d=prepare(d);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    for period in (20,50):
        report,trades,equity=run(d,period)
        (out/f'ema{period}.json').write_text(json.dumps(report,indent=2))
        trades.to_csv(out/f'ema{period}_trades.csv',index=False)
        equity.to_csv(out/f'ema{period}_equity.csv',index=False)
        print(json.dumps(report,indent=2))
if __name__=='__main__':main()
