"""Read-only checks against the database populated by a real ingest run."""
from pathlib import Path
import csv,json,math,sqlite3
from goldtrading.storage import Store
from goldtrading.sources import Observation
from goldtrading.export import snapshot
store=Store('data/gold.db')
data,obs=snapshot(store)
assert data['quality']['rows']>0 and data['quality']['invalid_prices']==0 and data['quality']['duplicate_keys']==0
with open('data/published/observations.csv',newline='') as f:published=list(csv.DictReader(f))
assert len(published)==len(obs)
# Replay the exact recorded real rows into an isolated temporary DB, twice, then reopen.
import tempfile
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'replay.db';isolated=Store(str(path))
 rows=[Observation(**{**r,'value':float(r['value'])}) for r in published]
 with isolated.transaction():first=isolated.upsert(rows)
 with isolated.transaction():second=isolated.upsert(rows)
 assert first==(len(rows),0) and second==(0,len(rows))
 isolated.close();isolated=Store(str(path));assert isolated.query('SELECT COUNT(*) AS n FROM observations')[0]['n']==len(rows);isolated.close()
report={'validation':'actual collected/exported rows only; replay in isolated temporary SQLite database','quality':data['quality'],'csv_rows_equal_database':True,'first_load_inserted':first[0],'second_load_inserted':second[0],'second_load_existing':second[1],'persistence_after_reopen':True,'coverage':data['coverage'],'model_status':data['model']['status'],'model_beats_naive_mae':data['model'].get('beats_naive_mae'),'model_metrics':data['model'].get('model_metrics'),'naive_metrics':data['model'].get('naive_metrics')}
Path('evidence/runtime-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));store.close()
