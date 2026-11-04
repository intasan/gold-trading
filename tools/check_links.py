from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.refs=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if 'id' in d:self.ids.append(d['id'])
  for k in ['href','src']:
   if k in d:self.refs.append(d[k])
p=Page();p.feed((R/'index.html').read_text());assert len(p.ids)==len(set(p.ids))
count=0
for ref in p.refs:
 u=urlsplit(ref)
 if u.scheme or u.netloc:continue
 if not u.path:assert u.fragment in p.ids,ref
 else:assert (R/unquote(u.path)).exists(),ref
 count+=1
print('HTML local links/fragments and unique IDs passed:',count)
