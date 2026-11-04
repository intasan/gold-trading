from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parents[1];d=r/'dist';d.mkdir(exist_ok=True)
for p in ['index.html','web','data/published']:
 f=r/p;to=d/p
 if f.is_dir():shutil.copytree(f,to,dirs_exist_ok=True)
 else:shutil.copy2(f,to)
shutil.copy2(r/'tools/browser-qa.html',d/'qa.html')
(r/'.openai').mkdir(exist_ok=True);(r/'.openai/hosting.json').write_text(json.dumps({'static':{'directory':'dist'}}))
