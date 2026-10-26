"""Offline package and numerical checks; does not run a browser."""
from pathlib import Path
from html.parser import HTMLParser
import json,subprocess,sys,re,math
HERE=Path(__file__).resolve().parent
class Page(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.labels=[];self.sources=[];self.scripts=[];self.active=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='label' and 'for' in a:self.labels.append(a['for'])
        if tag in ('script','img','iframe','link','audio','video','source'):
            for k in ('src','href'):
                if k in a:self.sources.append(a[k])
        if tag=='script':self.active=True;self.scripts.append('')
    def handle_endtag(self,tag):
        if tag=='script':self.active=False
    def handle_data(self,data):
        if self.active:self.scripts[-1]+=data
subprocess.run([sys.executable,'-B','build.py'],cwd=HERE,check=True)
s=(HERE/'index.html').read_text();p=Page();p.feed(s)
assert len(p.ids)==len(set(p.ids)) and set(p.labels)<=set(p.ids)
assert not p.sources and len(p.scripts)==3
assert p.scripts[0]==(HERE/'core.js').read_text() and p.scripts[2]==(HERE/'ui.js').read_text()
assert set(re.findall(r"\$\('([^']+)'\)",(HERE/'ui.js').read_text()))<=set(p.ids)
assert not any(t in s for t in ('/* CORE */','/* UI */','/* STUDY */','/* EXACT */'))
assert not re.search(r'\b(fetch|XMLHttpRequest|WebSocket|sendBeacon|eval)\s*\(',s)
subprocess.run([sys.executable,'-B','-m','unittest','-v','test_model'],cwd=HERE,check=True)
subprocess.run(['node','test_js.js'],cwd=HERE,check=True)
subprocess.run(['node','test_ui_wiring.js'],cwd=HERE,check=True)
from model import theory,ensemble,detection
study=json.loads((HERE/'data/study.json').read_text());ref=next(r for r in study['rows'] if r['sigma']==.8)
assert ref['theory']==theory(.25,1,.8,256)
assert ref['batches']==ensemble(.25,1,.8,20261025,256,128)
controls=json.loads((HERE/'data/controls.json').read_text());ref=next(r for r in controls['rows'] if r['sigma']==.8)
assert ref['calibrated_projection']==detection(.25,1,.8,20261025,256,512,512)
print('PASS static packaging and saved numerical references; browser rendering unverified')
