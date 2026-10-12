#!/usr/bin/env python3
"""#15 original-model reproducibility harness. Never fabricates historical data.

Input CSV: month,us_stock,long_treasury,gold,commodities, 1 row per month.
All return columns are decimal monthly *total* returns in USD, e.g. .0125 for 1.25%.
A provenance JSON must identify every upstream series. Historical completeness is enforced.
This tool does not certify that proxies reproduce the video/book unless the inputs do.
"""
import argparse
import calendar
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ASSETS = ['us_stock','long_treasury','gold','commodities']
PORTFOLIOS = {'video_26_34_20_20':[.26,.34,.20,.20], 'stock60_same_long_treasury40':[.60,.40,0.,0.]}

def months_inclusive(start,end):
    sy,sm=map(int,start.split('-'));ey,em=map(int,end.split('-'))
    if not(1<=sm<=12 and 1<=em<=12) or (sy,sm)>(ey,em):
        raise ValueError('Invalid inclusive dates')
    return [f'{y:04d}-{m:02d}' for y in range(sy,ey+1) for m in range(1,13) if (y,m)>=(sy,sm) and (y,m)<=(ey,em)]

def read_csv(path,start,end):
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or list(reader.fieldnames)!=['month',*ASSETS]:
            raise ValueError('CSV header must be exactly month,us_stock,long_treasury,gold,commodities')
        rows=list(reader)
    requested=months_inclusive(start,end)
    dates=[r['month'] for r in rows]
    if dates != requested:
        raise ValueError(f'Incomplete/nonmonotonic input: expected {len(requested)} monthly rows {start}..{end}, got {len(rows)}; first/last {dates[:1]}, {dates[-1:]}')
    returns=[]
    for r in rows:
        ret=[]
        for name in ASSETS:
            value=float(r[name])
            if not math.isfinite(value) or value <= -1:
                raise ValueError(f'Invalid monthly total return in {r["month"]} {name}: {value}')
            ret.append(value)
        returns.append(ret)
    return requested,returns

def validate_provenance(p):
    obj=json.loads(p.read_text(encoding='utf-8'))
    if obj.get('return_unit')!='decimal' or obj.get('currency')!='USD' or obj.get('return_basis')!='monthly_total_return_including_income':
        raise ValueError('Provenance needs currency=USD, return_unit=decimal, return_basis=monthly_total_return_including_income')
    src=obj.get('series',{})
    for key in ASSETS:
        s=src.get(key,{})
        if not all(s.get(k) for k in ['index_name','publisher','source_url','series_start','series_end','treatment']):
            raise ValueError(f'Provenance incomplete for {key}: identify all source/return conventions')
    return obj

def measure(returns, weights, dates, rebalance='annual'):
    positions=list(weights)
    equity=[1.]
    for month,rets in zip(dates,returns):
        if (rebalance=='monthly' and len(equity)>1) or (rebalance=='annual' and month.endswith('-01') and len(equity)>1):
            total=sum(positions)
            positions=[total*w for w in weights]
        positions=[a*(1+r) for a,r in zip(positions,rets)]
        equity.append(sum(positions))
    end=equity[-1]
    n=len(returns)
    mr=[equity[i+1]/equity[i]-1 for i in range(n)]
    avg=sum(mr)/n
    std=math.sqrt(sum((x-avg)**2 for x in mr)/(n-1))*math.sqrt(12) if n>1 else 0.
    peak=1.;mdd=0.
    for e in equity[1:]:
        peak=max(peak,e)
        mdd=min(mdd,e/peak-1)
    return {'months':n,'years':n/12,'cagr':end**(12/n)-1,'annualized_volatility':std,
            'maximum_drawdown':mdd,'growth_of_1_usd':end,'rebalance':rebalance}

def self_test():
    assert abs(sum(PORTFOLIOS['video_26_34_20_20'])-1)<1e-12
    assert abs(sum(PORTFOLIOS['stock60_same_long_treasury40'])-1)<1e-12
    d=months_inclusive('2020-01','2021-12')
    assert len(d)==24 and d[0]=='2020-01' and d[-1]=='2021-12'
    r=[[.0,.0,.0,.0] for _ in d]
    z=measure(r,PORTFOLIOS['video_26_34_20_20'],d)
    assert z['cagr']==0.0 and z['maximum_drawdown']==0. and z['growth_of_1_usd']==1.
    r=[[.01,.01,.01,.01] for _ in d]
    z=measure(r,PORTFOLIOS['video_26_34_20_20'],d)
    assert abs(z['growth_of_1_usd']-1.01**24)<1e-12
    assert abs(z['cagr']-1.01**12+1)<1e-12
    try:
        months_inclusive('2021-14','2022-02')
    except ValueError: pass
    else: raise AssertionError('Invalid month accepted')
    return {'self_test':'PASS','checks':7,'original_backtest_reproduced':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--csv',type=Path)
    ap.add_argument('--provenance',type=Path)
    ap.add_argument('--start',default='1972-01')
    ap.add_argument('--end',default='2022-12')
    ap.add_argument('--rebalance',choices=['annual','monthly','buy-and-hold'],default='annual')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),ensure_ascii=False,indent=2));return 0
    if not args.csv or not args.csv.is_file() or not args.provenance or not args.provenance.is_file():
        print(json.dumps({'status':'BLOCKED_MISSING_SOURCE_RETURNS','expected':'Actual identified total-return historical monthly CSV plus verifiable provenance metadata; no historical performance has been fabricated','original_backtest_reproduced':False},ensure_ascii=False,indent=2));return 2
    try:
        manifest=validate_provenance(args.provenance)
        dates,returns=read_csv(args.csv,args.start,args.end)
        out={'status':'COMPUTED_NOT_ORIGINAL_BOOK_CERTIFIED','source_manifest':str(args.provenance),
             'date_range':[dates[0],dates[-1]],'return_basis':manifest['return_basis'],
             'requires_independent_book_alignment':True,
             'portfolios':{name:measure(returns,weights,dates,args.rebalance) for name,weights in PORTFOLIOS.items()}}
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0
    except (ValueError,KeyError,ZeroDivisionError) as e:
        print(json.dumps({'status':'BLOCKED_INPUT_VALIDATION','error':str(e),'original_backtest_reproduced':False},ensure_ascii=False,indent=2));return 2

if __name__=='__main__':sys.exit(main())