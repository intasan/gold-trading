from pathlib import Path
import csv,json,hashlib,math
r=Path(__file__).resolve().parents[1];d=json.loads((r/'data/published/snapshot.json').read_text());m=json.loads((r/'data/published/manifest.json').read_text())
with (r/'data/published/observations.csv').open(newline='') as f:rows=list(csv.DictReader(f))
assert len(rows)==d['quality']['rows']==m['row_count']
assert len({(x['source'],x['series'],x['frequency'],x['observed_at']) for x in rows})==len(rows)
assert all(math.isfinite(float(x['value'])) and float(x['value'])>0 for x in rows)
assert m['csv_sha256']==hashlib.sha256((r/'data/published/observations.csv').read_bytes()).hexdigest()
assert m['snapshot_sha256']==hashlib.sha256((r/'data/published/snapshot.json').read_bytes()).hexdigest()
for series,hist in d['history'].items():
 expected=[x for x in rows if x['source']=='worldbank' and x['series']==series]
 assert len(hist)==len(expected)
 assert all(float(a['value'])==float(b['value']) and a['period']==b['observed_at'] for a,b in zip(hist,expected))
if d['model']['status']=='evaluated':
 assert len(d['model']['predictions'])==d['model']['holdout_rows']
 assert all(x['train_last_period']<x['period'] for x in d['model']['predictions'])
 if not d['model']['beats_naive_mae']:assert d['model']['forecast'] is None
print('Published JSON/CSV/hash/chronology checks passed:',len(rows),'real observations')
