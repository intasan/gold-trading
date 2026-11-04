"""Start the real read-only API against an isolated DB replayed from actual observations."""
from pathlib import Path
import csv,json,socket,subprocess,sys,tempfile,time
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from goldtrading.storage import Store,ROOT
from goldtrading.sources import Observation
with tempfile.TemporaryDirectory() as temp:
 path=str(Path(temp)/'api.db');store=Store(path)
 with (ROOT/'data/published/observations.csv').open(newline='') as f:rows=[Observation(**{**r,'value':float(r['value'])}) for r in csv.DictReader(f)]
 with store.transaction():store.upsert(rows)
 store.close()
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 process=subprocess.Popen([sys.executable,'-m','goldtrading','--db',path,'serve','--port',str(port)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 results=[]
 try:
  base=f'http://127.0.0.1:{port}'
  for _ in range(50):
   try:
    with urlopen(base+'/api/health',timeout=1) as response:health=json.load(response)
    break
   except OSError:time.sleep(.1)
  else:raise RuntimeError('API did not start')
  assert health['ok'] and health['rows']==len(rows)
  for endpoint,expected in [('/api/health',200),('/api/snapshot',200),('/',200),('/.env',404),('/data/gold.db',404),('/sql/schema.sql',404),('/api/unknown',404),('/web/../data/gold.db',400)]:
   try:
    with urlopen(base+endpoint,timeout=5) as response:
     status=response.status
     if endpoint=='/api/snapshot':assert json.load(response)['quality']['rows']==len(rows)
   except HTTPError as e:status=e.code
   assert status==expected,(endpoint,status,expected);results.append({'path':endpoint,'status':status,'expected':expected})
 finally:
  process.terminate();out,err=process.communicate(timeout=5)
report={'scope':'Actual Python HTTP server with real recorded observations replayed in a temporary SQLite DB; no provider network call in this test','rows':len(rows),'checks':results}
(ROOT/'evidence/api-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
