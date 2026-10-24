"""Bounded optics checks; optional full deterministic parameter studies."""
from pathlib import Path
import argparse,subprocess,sys,json,math
p=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args()
def run(cmd):subprocess.run(cmd,cwd=p,check=True)
run([sys.executable,'-B','-m','unittest','-v','test_model'])
run(['node','test_js.js']);run(['node','test_scaling.js'])
run([sys.executable,'-B','loss_control.py']);run([sys.executable,'-B','delay_control.py'])
if args.full:
    for name in ['run_study.py','followups.py','matched_correlation.py']:run([sys.executable,'-B',name])
html=(p/'page.template.html').read_text().replace('/*CORE*/',(p/'core.js').read_text()).replace('/*UI*/',(p/'ui.js').read_text())
assert html==(p/'index.html').read_text()
assert html==(p.parents[1]/'docs/mirror-window/index.html').read_text()
print('PASS 28 Python groups, 9102 JS checks, loss/delay controls and generated-page parity')
