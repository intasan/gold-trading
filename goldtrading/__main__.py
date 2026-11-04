import argparse,csv,json,os,sys
from pathlib import Path
from .sources import Observation
from .storage import Store
from .pipeline import ingest
from .model import run_model
from .export import export

def main():
 p=argparse.ArgumentParser(description='Source-traceable gold research pipeline');p.add_argument('--db',default=os.environ.get('DATABASE_URL','data/gold.db'),help='SQLite path or PostgreSQL URL; use environment for secrets');sub=p.add_subparsers(dest='command',required=True)
 for name in ['refresh','ingest']:
  q=sub.add_parser(name);q.add_argument('--sources',default='worldbank,gold_api_xau,gold_api_xag,frankfurter');q.add_argument('--force',action='store_true');q.add_argument('--raw-dir',default='data/raw')
 for name in ['model','export','inspect']:sub.add_parser(name)
 q=sub.add_parser('replay');q.add_argument('--input',default='data/published/observations.csv')
 q=sub.add_parser('serve');q.add_argument('--host',default='127.0.0.1');q.add_argument('--port',type=int,default=8000)
 a=p.parse_args()
 if a.command=='serve':
  from .server import serve
  return serve(a.db,a.host,a.port)
 store=Store(a.db)
 try:
  if a.command in ['refresh','ingest']:
   report=ingest(store,Path(a.raw_dir),a.sources.split(','),a.force);print(json.dumps(report,indent=2))
   if a.command=='refresh':
    try:model=run_model(store)
    except Exception as exc:
     from .sources import utcnow
     import uuid
     model={'status':'failed','reason':f'{type(exc).__name__}: {exc}','evaluated_at':utcnow()}
     with store.transaction():store.execute('INSERT INTO model_runs VALUES(?,?,?,?)',(str(uuid.uuid4()),utcnow(),'failed',json.dumps(model)))
    data=export(store);print(json.dumps({'database_rows':data['quality']['rows'],'model_status':model['status'],'reason':model.get('reason'),'model_metrics':model.get('model_metrics'),'naive_metrics':model.get('naive_metrics'),'beats_naive_mae':model.get('beats_naive_mae')},indent=2))
   return int(report['status']=='failed')
  if a.command=='model':print(json.dumps(run_model(store),indent=2))
  elif a.command=='export':print(json.dumps({'quality':export(store)['quality']},indent=2))
  elif a.command=='inspect':print(json.dumps({'coverage':store.query('SELECT source,series,frequency,unit,COUNT(*) AS rows,MIN(observed_at) AS first,MAX(observed_at) AS last FROM observations GROUP BY source,series,frequency,unit'),'runs':store.query('SELECT id,status,started_at,finished_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 10')},indent=2))
  elif a.command=='replay':
   with open(a.input,newline='') as f:rows=[Observation(**{**r,'value':float(r['value'])}) for r in csv.DictReader(f)]
   with store.transaction():inserted,existing=store.upsert(rows)
   print(json.dumps({'mode':'replay_recorded_observations_not_live_fetch','inserted_rows':inserted,'existing_rows':existing}))
  return 0
 finally:store.close()
if __name__=='__main__':sys.exit(main())
