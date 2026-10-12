"""Check static packaging, local links, and dependency-free page structure."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re
root=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=[];self.labels=[];self.lang=None;self.viewport=False;self.external=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='html':self.lang=a.get('lang')
  if tag=='meta' and a.get('name')=='viewport':self.viewport=True
  if 'id' in a:self.ids.append(a['id'])
  if tag=='label' and 'for' in a:self.labels.append(a['for'])
  for key in ['src','href']:
   if key in a:
    self.refs.append((tag,key,a[key]))
    if key=='src' and urlsplit(a[key]).scheme in ['http','https']:self.external.append(a[key])
for filename in sorted((root/'docs').rglob('*.html')):
 text=filename.read_text();p=Page();p.feed(text)
 assert p.lang=='en' and p.viewport,filename
 assert len(p.ids)==len(set(p.ids)),('duplicate IDs',filename)
 assert all(label in p.ids for label in p.labels),('broken label',filename)
 assert p.external==[],('remote asset',filename)
 assert not re.search(r'\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket|serviceWorker|localStorage|sessionStorage)\b',text),('network/persistence API',filename)
 for tag,key,ref in p.refs:
  split=urlsplit(ref)
  if split.scheme or split.netloc or not split.path:continue
  target=(filename.parent/unquote(split.path)).resolve()
  assert target.is_relative_to((root/'docs').resolve()),('outside docs link',ref)
  assert target.is_file(),('broken link',filename,ref)
  if split.fragment:
   targetp=Page();targetp.feed(target.read_text());assert split.fragment in targetp.ids
 print('PASS',filename.relative_to(root),'valid page, labels, local links, inline assets')
assert not list(root.rglob('*.mp3'))
assert not list(root.rglob('*.xml'))
assert not list(root.rglob('*.pdf'))
print('PASS original executable pages only; no third-party assets or recordings bundled')
