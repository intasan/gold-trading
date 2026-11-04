"""Integration assertions against the actual PostgreSQL service, never sample prices."""
import csv,json,os
from pathlib import Path
from goldtrading.storage import Store,ROOT
from goldtrading.sources import Observation
s=Store(os.environ['DATABASE_URL'])
assert s.postgres
with (ROOT/'data/published/observations.csv').open(newline='') as f: rows=[Observation(**{**r,'value':float(r['value'])}) for r in csv.DictReader(f)]
with s.transaction(): first=s.upsert(rows)
with s.transaction(): second=s.upsert(rows)
assert second==(0,len(rows)),second
n=s.query('SELECT COUNT(*) AS n FROM observations')[0]['n'];assert n>=len(rows)
s.close();s=Store(os.environ['DATABASE_URL']);assert s.query('SELECT COUNT(*) AS n FROM observations')[0]['n']==n
print(json.dumps({'postgres_version':s.query('SELECT version() AS version')[0]['version'],'real_recorded_rows':len(rows),'database_rows':n,'second_replay':second,'reopen_persistent':True}))
s.close()
