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
def assert_reference(actual, expected, path='reference'):
    """Retain exact structure/counts; allow bounded libm rounding in finite floats."""
    if isinstance(expected, dict):
        assert type(actual) is dict and actual.keys()==expected.keys(), path
        for key in expected: assert_reference(actual[key], expected[key], path+'.'+key)
    elif isinstance(expected, list):
        assert type(actual) is list and len(actual)==len(expected), path
        for index,(left,right) in enumerate(zip(actual,expected)):
            assert_reference(left,right,path+'['+str(index)+']')
    elif type(expected) is float:
        assert type(actual) in (int,float) and math.isfinite(actual) and math.isfinite(expected), path
        assert math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12), (path,actual,expected)
    else:
        assert type(actual) is type(expected) and actual==expected, path

# Negative controls keep numerical tolerance from admitting changed results/schema.
assert_reference({'x':[.5+1e-14],'count':2},{'x':[.5],'count':2})
for actual,expected in [({'x':.5+1e-7},{'x':.5}),({'x':float('nan')},{'x':.5}),
                        ({'x':.5,'extra':0},{'x':.5}),({'count':3},{'count':2})]:
    try: assert_reference(actual,expected)
    except AssertionError: pass
    else: raise AssertionError('Reference comparator accepted an invalid control')

study=json.loads((HERE/'data/study.json').read_text());ref=next(r for r in study['rows'] if r['sigma']==.8)
computed_theory=theory(.25,1,.8,256)
assert_reference(computed_theory,ref['theory'],'theory')
print('Theory reference maximum absolute difference:',max(abs(computed_theory[k]-ref['theory'][k]) for k in computed_theory))
assert_reference(ensemble(.25,1,.8,20261025,256,128),ref['batches'],'batches')
controls=json.loads((HERE/'data/controls.json').read_text());ref=next(r for r in controls['rows'] if r['sigma']==.8)
assert_reference(detection(.25,1,.8,20261025,256,512,512),ref['calibrated_projection'],'calibrated_projection')
print('PASS static packaging and saved numerical references; browser rendering unverified')
