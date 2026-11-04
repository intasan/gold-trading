from pathlib import Path
import csv,hashlib,json,os,tempfile
from .sources import utcnow
from .storage import FIELDS
SOURCE_DOCS={'worldbank':{'name':'World Bank · Pink Sheet','url':'https://www.worldbank.org/en/research/commodity-markets','license':'CC BY 4.0 (World Bank dataset catalogue)','scope':'Monthly nominal USD averages; not daily or spot quotes'},'gold_api':{'name':'Gold API','url':'https://gold-api.com/docs','license':'Provider terms apply','scope':'Timestamped spot quotes in USD per troy ounce'},'frankfurter':{'name':'Frankfurter','url':'https://frankfurter.dev/','license':'Provider terms apply','scope':'Daily USD/THB reference rate; not a dealer quote'}}
def atomic_json(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def snapshot(store):
 obs=store.query('SELECT * FROM observations ORDER BY source,series,observed_at')
 coverage=store.query('SELECT source,series,frequency,unit,COUNT(*) AS rows,MIN(observed_at) AS first_period,MAX(observed_at) AS last_period FROM observations GROUP BY source,series,frequency,unit ORDER BY source,series')
 runs=store.query('SELECT details_json FROM pipeline_runs ORDER BY started_at DESC, id DESC LIMIT 1');pipeline=json.loads(runs[0]['details_json']) if runs else {'status':'not_run','sources':{}}
 models=store.query('SELECT result_json FROM model_runs ORDER BY created_at DESC,id DESC LIMIT 1');model=json.loads(models[0]['result_json']) if models else {'status':'not_run','reason':'Run evaluation after ingesting sufficient history.'}
 quotes=[]
 for c in coverage:
  if c['frequency']!='monthly':quotes+=store.query('SELECT * FROM observations WHERE source=? AND series=? AND frequency=? ORDER BY observed_at DESC LIMIT 1',(c['source'],c['series'],c['frequency']))
 history={s:[{'period':r['observed_at'],'value':r['value']} for r in obs if r['source']=='worldbank' and r['series']==s] for s in ['GOLD','SILVER','PLATINUM']}
 quality={'duplicate_keys':store.query('SELECT COUNT(*) AS n FROM (SELECT source,series,frequency,observed_at FROM observations GROUP BY source,series,frequency,observed_at HAVING COUNT(*)>1) AS d')[0]['n'],'invalid_prices':store.query('SELECT COUNT(*) AS n FROM observations WHERE value<=0 OR value IS NULL')[0]['n'],'rows':len(obs),'monthly_average_and_spot_are_separate':True}
 return {'schema_version':1,'exported_at':utcnow(),'delivery':'Recorded pipeline export; browser does not query data providers','sources':SOURCE_DOCS,'coverage':coverage,'quotes':quotes,'history':history,'quality':quality,'pipeline':pipeline,'model':model},obs
def export(store,directory=Path('data/published')):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);data,obs=snapshot(store);path=directory/'observations.csv';tmp=directory/'observations.csv.tmp'
 with tmp.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n");w.writeheader();w.writerows(obs)
 os.replace(tmp,path);atomic_json(directory/'snapshot.json',data)
 atomic_json(directory/'manifest.json',{'exported_at':data['exported_at'],'row_count':len(obs),'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256((directory/'snapshot.json').read_bytes()).hexdigest(),'source_urls':SOURCE_DOCS,'provenance_note':'Real normalized observations. raw_sha256 identifies the original provider response. Raw response cache is local and ignored by Git.'})
 return data
