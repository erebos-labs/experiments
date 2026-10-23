"""Bounded local numerical, cross-language, certificate and parity checks."""
from pathlib import Path
import json,subprocess,sys
from fractions import Fraction as F
p=Path(__file__).resolve().parent
subprocess.run([sys.executable,'-B','-m','unittest','-v','test_model.py','test_gated.py'],cwd=p,check=True)
subprocess.run(['node','test_js.js'],cwd=p,check=True)
sys.path.insert(0,str(p))
from test_model import dense_mean,exact_survival
c=json.loads((p/'data/exact-certificate.json').read_text())
assert str(dense_mean(10,5,F(1,32)))==c['reset_mean_fraction']
a=exact_survival(10,5,F(0),51);b=exact_survival(10,5,F(1,32),51)
for key,value in [('baseline_t48',a[48]),('baseline_t49',a[49]),('reset_t50',b[50]),('reset_t51',b[51])]:assert str(value)==c['witness_survivals'][key]
html=(p/'page.template.html').read_text().replace('/* CORE_JS */',(p/'core.js').read_text())
assert html==(p/'index.html').read_text()
assert html==(p.parents[1]/'docs/restart-bargain/index.html').read_text()
print('PASS 19 Python tests, 640 cross-language comparisons, exact certificate and source/generated parity')
