from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit
import json
from .storage import Store,ROOT
from .export import snapshot

def serve(database,host='127.0.0.1',port=8000):
 class Handler(SimpleHTTPRequestHandler):
  def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
  def do_GET(self):
   path=urlsplit(self.path).path
   if path.startswith('/api/'):
    if path not in ['/api/health','/api/snapshot']:return self.send_error(404)
    store=Store(database)
    try:
     data,_=snapshot(store);obj={'ok':True,'rows':data['quality']['rows'],'pipeline_status':data['pipeline']['status']} if path=='/api/health' else data
    finally:store.close()
    body=json.dumps(obj,allow_nan=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
   if path not in ['/','/index.html'] and not path.startswith(('/web/','/data/published/')):return self.send_error(404)
   if '..' in path or '%' in path:return self.send_error(400)
   return super().do_GET()
  def list_directory(self,path):return self.send_error(403)
  def end_headers(self):
   self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','strict-origin-when-cross-origin');super().end_headers()
 print(f'Gold Trading Dashboard: http://{host}:{port}/',flush=True);ThreadingHTTPServer((host,port),Handler).serve_forever()
