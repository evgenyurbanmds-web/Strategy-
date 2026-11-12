"""Download BTCUSDT 5m OHLCV into CSV. Public market data; no orders."""
import argparse,time
from pathlib import Path
import pandas as pd
import requests

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start',default='2022-01-01')
    p.add_argument('--end',default='2026-11-01')
    p.add_argument('--market',choices=['spot','futures'],default='spot')
    p.add_argument('--out',default='data/btc_5m.csv')
    a=p.parse_args()
    url='https://api.binance.com/api/v3/klines' if a.market=='spot' else 'https://fapi.binance.com/fapi/v1/klines'
    start=int(pd.Timestamp(a.start,tz='UTC').timestamp()*1000)
    end=int(pd.Timestamp(a.end,tz='UTC').timestamp()*1000)
    step=300000;rows=[]
    while start<end:
        r=requests.get(url,params={'symbol':'BTCUSDT','interval':'5m','startTime':start,'endTime':end-1,'limit':1000},timeout=30)
        r.raise_for_status();batch=r.json()
        if not batch:break
        rows.extend(batch)
        next_start=int(batch[-1][0])+step
        if next_start<=start:raise RuntimeError('Pagination stalled')
        start=next_start
        time.sleep(.15)
    if not rows:raise RuntimeError('No data returned')
    d=pd.DataFrame([{'time':pd.to_datetime(int(x[0]),unit='ms',utc=True),'open':float(x[1]),'high':float(x[2]),'low':float(x[3]),'close':float(x[4]),'volume':float(x[5])} for x in rows])
    d=d.drop_duplicates('time').sort_values('time')
    if not (d.time.diff().dropna()==pd.Timedelta(minutes=5)).all():raise RuntimeError('Missing 5m candles')
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(path,index=False)
    print(f'Saved {len(d)} contiguous candles: {d.time.iloc[0]} through {d.time.iloc[-1]} to {path}')
if __name__=='__main__':main()
