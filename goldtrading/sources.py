from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib, io, json, math, re, time
import pandas as pd

WORLD_BANK_URL = 'https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx'
URLS = {'worldbank': WORLD_BANK_URL, 'gold_api_xau': 'https://api.gold-api.com/price/XAU', 'gold_api_xag': 'https://api.gold-api.com/price/XAG', 'frankfurter': 'https://api.frankfurter.dev/v2/rate/USD/THB'}

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')

@dataclass(frozen=True)
class Observation:
    source: str
    series: str
    frequency: str
    observed_at: str
    value: float
    unit: str
    retrieved_at: str
    raw_sha256: str

ALLOWED = {('worldbank','GOLD','monthly'): 'USD/troy oz (monthly average)', ('worldbank','SILVER','monthly'): 'USD/troy oz (monthly average)', ('worldbank','PLATINUM','monthly'): 'USD/troy oz (monthly average)', ('gold_api','XAU','quote'): 'USD/troy oz (spot quote)', ('gold_api','XAG','quote'): 'USD/troy oz (spot quote)', ('frankfurter','USDTHB','daily'): 'THB per USD (reference rate)'}

def validate(row):
    expected = ALLOWED.get((row.source, row.series, row.frequency))
    if row.unit != expected:
        raise ValueError('Unexpected source/series/frequency/unit combination')
    if not math.isfinite(row.value) or row.value <= 0:
        raise ValueError('Price must be positive and finite')
    observed = datetime.fromisoformat(row.observed_at.replace('Z', '+00:00'))
    retrieved = datetime.fromisoformat(row.retrieved_at.replace('Z', '+00:00'))
    observed = observed.replace(tzinfo=timezone.utc) if observed.tzinfo is None else observed
    if retrieved.tzinfo is None or observed > retrieved + timedelta(minutes=5):
        raise ValueError('Invalid or future-dated observation')
    if not re.fullmatch('[a-f0-9]{64}', row.raw_sha256):
        raise ValueError('Missing raw response hash')
    return row

class Downloader:
    def __init__(self, directory: Path, force=False):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.force = force

    def get(self, name):
        url = URLS[name]
        index = self.directory / (name + '-latest.json')
        ttl = 6*3600 if name == 'worldbank' else (3600 if name == 'frankfurter' else 30)
        if index.exists() and not self.force:
            meta = json.loads(index.read_text())
            when = datetime.fromisoformat(meta['retrieved_at'].replace('Z','+00:00'))
            file = self.directory / meta['file']
            if file.exists() and (datetime.now(timezone.utc)-when).total_seconds() < ttl:
                body=file.read_bytes()
                if hashlib.sha256(body).hexdigest()==meta['sha256']:
                    return body, {**meta, 'cached': True}
        last = None
        for attempt in range(2):
            try:
                with urlopen(Request(url, headers={'User-Agent':'GoldTradingAnalytics/1.0 (research portfolio; cached requests)'}), timeout=25) as response:
                    body = response.read(10*1024*1024+1)
                    if len(body)>10*1024*1024: raise ValueError('Response exceeds 10 MB')
                    meta={'url':url, 'final_url':response.url, 'http_status':response.status, 'retrieved_at':utcnow(), 'sha256':hashlib.sha256(body).hexdigest(), 'cached':False}
                suffix='xlsx' if name=='worldbank' else 'json'
                file=self.directory/(name+'-'+meta['sha256']+'.'+suffix)
                file.write_bytes(body)
                meta['file']=file.name
                index.write_text(json.dumps(meta,indent=2))
                return body,meta
            except Exception as exc:
                last=exc
                if attempt==0: time.sleep(1)
        raise RuntimeError(f'{name}: {type(last).__name__}: {last}')

def parse_worldbank(body, meta):
    sheet=pd.read_excel(io.BytesIO(body), sheet_name='Monthly Prices', header=None)
    header=next((i for i in range(min(20,len(sheet))) if 'Gold' in sheet.iloc[i].tolist() and 'Silver' in sheet.iloc[i].tolist()),None)
    if header is None: raise ValueError('World Bank schema changed: Gold/Silver headers missing')
    selected={'Gold':'GOLD','Silver':'SILVER','Platinum':'PLATINUM'}
    columns={str(v).strip():i for i,v in enumerate(sheet.iloc[header])}
    rows=[]
    for name,series in selected.items():
        if name not in columns: raise ValueError('Missing World Bank column '+name)
        col=columns[name]
        if str(sheet.iloc[header+1,col]).strip() != '($/troy oz)':
            raise ValueError('World Bank unit changed: '+name+' '+str(sheet.iloc[header+1,col]))
        for _, raw in sheet.iloc[header+2:].iterrows():
            period=str(raw.iloc[0]).strip()
            if not re.fullmatch(r'\d{4}M\d{2}',period): continue
            value=pd.to_numeric(raw.iloc[col],errors='coerce')
            if pd.isna(value): continue  # missing periods stay missing; never impute a price
            observed=f'{period[:4]}-{period[5:]}-01'
            if date.fromisoformat(observed)>=date.today().replace(day=1):
                raise ValueError('Uncompleted monthly period in historical source')
            rows.append(validate(Observation('worldbank',series,'monthly',observed,float(value),ALLOWED[('worldbank',series,'monthly')],meta['retrieved_at'],meta['sha256'])))
    keys=[(r.source,r.series,r.frequency,r.observed_at) for r in rows]
    if not rows or len(keys)!=len(set(keys)): raise ValueError('Empty or duplicate World Bank dataset')
    meta['release_label']=str(sheet.iloc[header-1,0])
    return rows

def parse_quote(body,meta,symbol):
    d=json.loads(body)
    if d.get('symbol')!=symbol or d.get('currency','USD')!='USD': raise ValueError('Unexpected quote instrument/currency')
    stamp=datetime.fromisoformat(str(d['updatedAt']).replace('Z','+00:00'))
    if stamp.tzinfo is None: raise ValueError('Quote timestamp must include timezone')
    when=stamp.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    return [validate(Observation('gold_api',symbol,'quote',when,float(d['price']),ALLOWED[('gold_api',symbol,'quote')],meta['retrieved_at'],meta['sha256']))]

def parse_fx(body,meta):
    d=json.loads(body)
    if d.get('base')!='USD' or d.get('quote')!='THB': raise ValueError('Unexpected currency pair')
    when=date.fromisoformat(d['date']).isoformat()
    return [validate(Observation('frankfurter','USDTHB','daily',when,float(d['rate']),ALLOWED[('frankfurter','USDTHB','daily')],meta['retrieved_at'],meta['sha256']))]

def collect(name, downloader):
    body,meta=downloader.get(name)
    if name=='worldbank': rows=parse_worldbank(body,meta)
    elif name=='frankfurter': rows=parse_fx(body,meta)
    else: rows=parse_quote(body,meta,'XAU' if name.endswith('xau') else 'XAG')
    return rows,meta
