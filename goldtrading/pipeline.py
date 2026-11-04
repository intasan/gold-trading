from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json,uuid
from .sources import URLS, Downloader, collect, utcnow

def ingest(store, raw_dir=Path('data/raw'), sources=None, force=False, collector=None):
    names=list(sources or URLS)
    if not names or any(n not in URLS for n in names): raise ValueError('Unknown source')
    started=utcnow();run_id=str(uuid.uuid4());results={}
    downloader=Downloader(Path(raw_dir),force=force)
    fetch=collector or (lambda name:collect(name,downloader))
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,name):name for name in names}
        for future in as_completed(futures):
            name=futures[future]
            try:
                rows,meta=future.result()
                # Source-level atomicity: invalid or failed sources never replace prior records.
                with store.transaction(): inserted,existing=store.upsert(rows)
                results[name]={'status':'success','extracted_rows':len(rows),'inserted_rows':inserted,'existing_rows':existing,'error':None,'provenance':meta}
            except Exception as exc:
                results[name]={'status':'failed','extracted_rows':0,'inserted_rows':0,'existing_rows':0,'error':f'{type(exc).__name__}: {exc}','provenance':{'url':URLS[name]}}
    success=sum(r['status']=='success' for r in results.values())
    status='success' if success==len(names) else ('partial' if success else 'failed')
    report={'id':run_id,'started_at':started,'finished_at':utcnow(),'status':status,'sources':results}
    with store.transaction():
        store.execute('INSERT INTO pipeline_runs VALUES(?,?,?,?,?)',(run_id,started,report['finished_at'],status,json.dumps(report,allow_nan=False)))
        for name,r in results.items():
            store.execute('INSERT INTO source_runs VALUES(?,?,?,?,?,?,?,?)',(run_id,name,r['status'],r['extracted_rows'],r['inserted_rows'],r['existing_rows'],r['error'],json.dumps(r['provenance'])))
    return report
